import json
from typing import List, Optional
from .agent_state import AgentState, TaskStep, TaskStepStatus, AgentType
from .llm import MainLLMEngine, MainLLMResponseType
from .context import MainContextManager


class MainPlanner:

    @staticmethod
    def create_plan(state: AgentState) -> List[TaskStep]:
        prompt = MainContextManager.build_planning_prompt(state)
        response = MainLLMEngine.decide(prompt, MainLLMResponseType.PLAN)

        if response.is_error() or not response.data:
            return [
                TaskStep(
                    id="s1",
                    description=state.task.objective,
                    agent_type=AgentType.BROWSER,
                )
            ]

        return MainPlanner._parse_steps(response.data)

    @staticmethod
    def replan(state: AgentState, reason: str) -> Optional[List[TaskStep]]:
        state.replan_count += 1
        if state.replan_count > state.max_replans:
            return None

        prompt = MainContextManager.build_planning_prompt(state)
        # Append replan context
        prompt += f"\n\n# Replanning Reason\n{reason}\n"
        prompt += "Generate a revised plan for the REMAINING work only. Do not repeat completed steps."

        response = MainLLMEngine.decide(prompt, MainLLMResponseType.PLAN)
        if response.is_error() or not response.data:
            return None

        new_steps = MainPlanner._parse_steps(response.data)

        # Preserve completed/skipped steps from the old plan
        preserved = [
            step for step in state.plan
            if step.status in (TaskStepStatus.COMPLETED, TaskStepStatus.SKIPPED)
        ]
        return preserved + new_steps

    @staticmethod
    def get_ready_steps(state: AgentState) -> List[TaskStep]:
        ready = []
        completed_ids = {
            step.id for step in state.plan
            if step.status in (TaskStepStatus.COMPLETED, TaskStepStatus.SKIPPED)
        }

        for step in state.plan:
            if step.status != TaskStepStatus.PENDING:
                continue
            if all(dep in completed_ids for dep in step.dependencies):
                ready.append(step)

        return ready

    @staticmethod
    def all_steps_terminal(state: AgentState) -> bool:
        if not state.plan:
            return False
        terminal = {
            TaskStepStatus.COMPLETED,
            TaskStepStatus.FAILED,
            TaskStepStatus.SKIPPED,
            TaskStepStatus.BLOCKED,
        }
        return all(step.status in terminal for step in state.plan)

    @staticmethod
    def has_failed_steps(state: AgentState) -> bool:
        return any(
            step.status == TaskStepStatus.FAILED for step in state.plan
        )

    @staticmethod
    def _parse_steps(data: dict) -> List[TaskStep]:
        try:
            raw_steps = data.get("steps", [])
            steps = []
            for s in raw_steps:
                agent_type = AgentType.BROWSER
                raw_agent = s.get("agent_type", "BROWSER").upper()
                if raw_agent in AgentType.__members__:
                    agent_type = AgentType(raw_agent)

                steps.append(TaskStep(
                    id=s.get("id", ""),
                    description=s.get("description", ""),
                    agent_type=agent_type,
                    dependencies=s.get("dependencies", []),
                    requires_gui=s.get("requires_gui", True),
                ))
            return steps if steps else [
                TaskStep(id="s1", description="Execute task", agent_type=AgentType.BROWSER)
            ]
        except Exception:
            return [
                TaskStep(id="s1", description="Execute task", agent_type=AgentType.BROWSER)
            ]
