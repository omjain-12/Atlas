from .models import DesktopAgentState, AgentStatus, ToolCall, ToolResult, ActionRecord
from .observation import ObservationManager
from .milestone import MilestoneEvaluator
from .context import ContextManager
from .llm import LLMEngine, LLMResponseType
from .loop_guard import LoopGuard
from .recovery import RecoveryManager
from .planner import LocalPlanner


class ToolExecutor:
    @staticmethod
    def execute(tool_call: ToolCall) -> ToolResult:
        # Mock tool executor bridging to Desktop Tools
        return ToolResult(
            success=True,
            output="Executed successfully",
            execution_method="MockExecutor",
        )


class ExecutionController:
    @staticmethod
    def run(state: DesktopAgentState):
        obs_manager = ObservationManager()

        while state.status == AgentStatus.EXECUTING:
            # 1. Budget Check
            if state.total_actions >= state.task.budget.max_actions:
                state.status = AgentStatus.FAILED
                break

            # 2. Observation
            scope = obs_manager.determine_required_scope(state)
            obs_manager.refresh_if_stale(state, scope)

            # 3. Milestone Evaluation
            current_milestone = LocalPlanner.get_current_milestone(state)
            if not current_milestone:
                state.status = AgentStatus.VERIFYING
                break

            is_satisfied, evidence = MilestoneEvaluator.is_satisfied(
                current_milestone, state.current_observation
            )
            if is_satisfied:
                LocalPlanner.advance_milestone(state, evidence)
                continue

            # 4. Context & LLM
            context_prompt = ContextManager.build(state)
            response = LLMEngine.decide(context_prompt)

            # 5. Handle LLM Response
            if response.type == LLMResponseType.TOOL_CALL:
                tool_call = response.tool_call
                result = ToolExecutor.execute(tool_call)

                record = ActionRecord(
                    milestone_id=current_milestone.milestone_id,
                    observation=state.current_observation,
                    llm_intent=response.intent or "No intent provided",
                    tool_call=tool_call,
                    tool_result=result,
                )

                state.action_history.append(record)
                state.total_actions += 1
                obs_manager.mark_stale()

                loop_warning = LoopGuard.detect_loop(state.action_history)
                if loop_warning:
                    state.status = AgentStatus.RECOVERING
                    RecoveryManager.attempt_recovery(state, loop_warning)
                    continue

                if not result.success:
                    state.consecutive_failures += 1
                    if (
                        state.consecutive_failures
                        > state.task.budget.max_consecutive_failures
                    ):
                        state.status = AgentStatus.RECOVERING
                        RecoveryManager.attempt_recovery(
                            state, "Repeated tool failures"
                        )
                else:
                    state.consecutive_failures = 0

            elif response.type == LLMResponseType.MILESTONE_SATISFIED:
                LocalPlanner.advance_milestone(state, response.evidence)

            elif response.type == LLMResponseType.NEEDS_HUMAN:
                state.status = AgentStatus.WAITING_FOR_HUMAN
                break

            else:  # PARSE_ERROR
                state.consecutive_failures += 1
                if state.consecutive_failures > 3:
                    state.status = AgentStatus.FAILED
                    break
