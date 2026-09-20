from typing import List, Optional, Any
from .models import (
    DesktopAgentState,
    ActionRecord,
    LocalTrajectory,
    Observation,
    MilestoneStatus,
)


class ContextManager:
    @staticmethod
    def build(state: DesktopAgentState) -> str:
        current_milestone = None
        if state.trajectory:
            for m in state.trajectory.milestones:
                if m.milestone_id == state.current_milestone_id:
                    current_milestone = m
                    break

        return ContextManager.format_prompt(
            task_objective=state.task.objective,
            expected_outcome=state.task.expected_outcome,
            constraints=state.task.constraints,
            trajectory=ContextManager.format_trajectory(state.trajectory),
            current_milestone=(
                current_milestone.description if current_milestone else "None"
            ),
            milestone_condition=(
                current_milestone.completion_condition if current_milestone else "None"
            ),
            current_state=ContextManager.format_observation(state.current_observation),
            recent_actions=ContextManager.format_last_n_actions(
                state.action_history, n=5
            ),
            recent_errors=ContextManager.format_last_n_errors(state.errors, n=3),
            warnings=ContextManager.get_warnings(state),
            budget_remaining=state.task.budget.max_actions - state.total_actions,
        )

    @staticmethod
    def format_prompt(**kwargs) -> str:
        return f"""
[System Prompt]
You are a Desktop Agent.

[Task]
Objective: {kwargs.get('task_objective')}
Expected Outcome: {kwargs.get('expected_outcome')}
Constraints: {kwargs.get('constraints')}

[Trajectory Overview]
{kwargs.get('trajectory')}

[Current Phase]
Active Milestone: {kwargs.get('current_milestone')}
Completion Condition: {kwargs.get('milestone_condition')}

[Recent History]
{kwargs.get('recent_actions')}

[Errors]
{kwargs.get('recent_errors')}

[Current Observation]
{kwargs.get('current_state')}

[Warnings]
{kwargs.get('warnings')}

Budget Remaining: {kwargs.get('budget_remaining')} actions

[Your Turn]
Decide the next tool call, mark the milestone satisfied, or request human intervention.
Provide response in JSON.
"""

    @staticmethod
    def format_trajectory(trajectory: Optional[LocalTrajectory]) -> str:
        if not trajectory:
            return "No trajectory available."

        lines = []
        for i, m in enumerate(trajectory.milestones):
            prefix = (
                "[->]" if m.status == MilestoneStatus.ACTIVE else f"[{m.status.value}]"
            )
            lines.append(f"{prefix} {i+1}. {m.description}")
        return "\n".join(lines)

    @staticmethod
    def format_observation(obs: Optional[Observation]) -> str:
        if not obs:
            return "No observation available."

        res = f"Active Window: {obs.active_window.title if obs.active_window else 'None'}\n"
        if obs.ui_tree and obs.ui_tree.tree:
            res += "UI Tree:\n"
            for element in obs.ui_tree.tree:
                name = element.ref.name or ""
                ctype = element.ref.control_type or ""
                focused = "(focused)" if element.is_focused else ""
                res += f" - {ctype} '{name}' {focused}\n"
        return res

    @staticmethod
    def format_last_n_actions(history: List[ActionRecord], n: int) -> str:
        if not history:
            return "No recent actions."

        recent = history[-n:]
        lines = []
        for i, record in enumerate(reversed(recent)):
            status = "Success" if record.tool_result.success else "Failed"
            lines.append(
                f"Action -{i+1}: {record.tool_call.tool_name}({record.tool_call.arguments}) -> {status}"
            )
        return "\n".join(lines)

    @staticmethod
    def format_last_n_errors(errors: List[Any], n: int) -> str:
        if not errors:
            return "None"
        recent = errors[-n:]
        return "\n".join([f"- {e.type.value}: {e.message}" for e in recent])

    @staticmethod
    def get_warnings(state: DesktopAgentState) -> str:
        # LoopGuard integration point, simple for now
        return "None"
