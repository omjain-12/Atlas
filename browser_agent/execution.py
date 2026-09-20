from .models import BrowserAgentState, AgentStatus, ToolCall, ToolResult, ActionRecord
from .observation import BrowserObservationManager
from .milestone import MilestoneEvaluator
from .context import ContextManager
from .llm import LLMEngine, LLMResponseType
from .loop_guard import LoopGuard
from .recovery import RecoveryManager
from .planner import LocalPlanner
from .tools.registry import BrowserToolRegistry


class ToolExecutor:
    @staticmethod
    def execute(registry: BrowserToolRegistry, tool_call: ToolCall) -> ToolResult:
        return registry.execute(tool_call)


class BrowserExecutionController:
    @staticmethod
    def run(state: BrowserAgentState, obs_manager: BrowserObservationManager, registry: BrowserToolRegistry):
        while state.status == AgentStatus.EXECUTING:
            if state.total_actions >= state.task.budget.max_actions:
                state.status = AgentStatus.FAILED
                break

            # 1. Automatic Internal Observation
            state.current_observation = obs_manager.observe()

            # 2. Milestone Evaluation
            current_milestone = LocalPlanner.get_active_milestone(state)
            if not current_milestone:
                # All milestones finished
                state.status = AgentStatus.VERIFYING
                break

            is_satisfied, evidence = MilestoneEvaluator.is_satisfied(
                current_milestone, state.current_observation
            )
            if is_satisfied:
                LocalPlanner.advance(state, evidence)
                continue

            # 3. Context & LLM
            context_prompt = ContextManager.build(state)
            response = LLMEngine.decide(context_prompt)

            # 4. Handle LLM Response
            if response.is_tool_call():
                tool_call = response.tool_call
                result = ToolExecutor.execute(registry, tool_call)

                record = ActionRecord(
                    milestone_id=current_milestone.milestone_id,
                    observation=state.current_observation,
                    llm_intent=response.intent or "No intent provided",
                    tool_call=tool_call,
                    tool_result=result,
                )

                state.action_history.append(record)
                state.total_actions += 1

                loop_warning = LoopGuard.detect_loop(state.action_history)
                if loop_warning:
                    state.status = AgentStatus.RECOVERING
                    RecoveryManager.attempt_recovery(state, loop_warning)
                    continue

                if not result.success:
                    state.consecutive_failures += 1
                    if state.consecutive_failures > state.task.budget.max_consecutive_failures:
                        state.status = AgentStatus.RECOVERING
                        RecoveryManager.attempt_recovery(
                            state, "Repeated tool failures"
                        )
                else:
                    state.consecutive_failures = 0

            elif response.is_milestone_satisfied():
                LocalPlanner.advance(state, response.evidence)

            elif response.needs_replanning():
                state.status = AgentStatus.REPLANNING
                new_trajectory = LocalPlanner.replan(state, response.reason)
                if new_trajectory:
                    state.trajectory = new_trajectory
                    state.status = AgentStatus.EXECUTING
                    state.consecutive_failures = 0
                else:
                    state.status = AgentStatus.FAILED

            elif response.type == LLMResponseType.NEEDS_HUMAN:
                state.status = AgentStatus.WAITING_FOR_HUMAN
                break

            else:  # PARSE_ERROR
                state.consecutive_failures += 1
                if state.consecutive_failures > 3:
                    state.status = AgentStatus.FAILED
                    break
