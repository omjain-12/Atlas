from typing import List, Optional
from .models import (
    BrowserAgentState,
    ActionRecord,
    LocalTrajectory,
    BrowserObservation,
    MilestoneStatus,
)


class ContextManager:
    @staticmethod
    def build(state: BrowserAgentState) -> str:
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
            history=ContextManager.format_history(state.action_history),
            observation=ContextManager.format_observation(state.current_observation),
            errors=ContextManager.format_errors(state.errors)
        )

    @staticmethod
    def format_prompt(
        task_objective: str,
        expected_outcome: Optional[str],
        constraints: List[str],
        trajectory: str,
        current_milestone: str,
        milestone_condition: str,
        history: str,
        observation: str,
        errors: str,
    ) -> str:
        return f"""You are a Browser capability agent.

# Objective
{task_objective}
Expected: {expected_outcome or 'N/A'}
Constraints: {', '.join(constraints) if constraints else 'None'}

# Trajectory
{trajectory}

# Current Milestone
{current_milestone}
Condition to satisfy: {milestone_condition}

# Recent Errors
{errors}

# Action History
{history}

# Current Observation
{observation}

Decide the next action to achieve the current milestone. You can output a tool call, indicate the milestone is satisfied, or indicate the milestone failed and needs replanning.
Respond in JSON.
"""

    @staticmethod
    def format_trajectory(trajectory: Optional[LocalTrajectory]) -> str:
        if not trajectory:
            return "No trajectory"
        lines = []
        for m in trajectory.milestones:
            mark = "[x]" if m.status == MilestoneStatus.SATISFIED else "[ ]"
            if m.status == MilestoneStatus.ACTIVE:
                mark = "[>]"
            lines.append(f"{mark} {m.description}")
        return "\n".join(lines)

    @staticmethod
    def format_history(history: List[ActionRecord]) -> str:
        if not history:
            return "No history"
        lines = []
        for r in history[-5:]:
            lines.append(f"Intent: {r.llm_intent}")
            lines.append(f"Action: {r.tool_call.tool_name}({r.tool_call.arguments})")
            lines.append(f"Result: Success={r.tool_result.success}, Output={r.tool_result.output}")
            lines.append("---")
        return "\n".join(lines)

    @staticmethod
    def format_observation(obs: Optional[BrowserObservation]) -> str:
        if not obs:
            return "No observation available"
        lines = [
            f"URL: {obs.url}",
            f"Title: {obs.title}",
            f"Active Tab ID: {obs.active_tab_id}",
            "Interactive Elements:"
        ]
        for el in obs.dom_elements:
            lines.append(f"[{el.element_ref}] {el.tag_name} - {el.text} - {el.attributes}")
        return "\n".join(lines)

    @staticmethod
    def format_errors(errors: List[Any]) -> str:
        if not errors:
            return "None"
        return "\n".join(f"- {e.type}: {e.message}" for e in errors[-3:])
