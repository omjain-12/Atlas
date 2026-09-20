import json
from typing import Optional, List
from .models import (
    DesktopTask,
    LocalTrajectory,
    DesktopAgentState,
    Milestone,
    MilestoneStatus,
)
from .llm import LLMEngine


class LocalPlanner:
    @staticmethod
    def create_trajectory(task: DesktopTask) -> LocalTrajectory:
        planning_prompt = f"""
You are planning a desktop task.

Task: {task.objective}
Constraints: {task.constraints}
Hints: {task.instructions}

Produce a list of 3-7 milestones.
Each milestone must be an OBSERVABLE CONDITION, not an action.
Respond with JSON: {{"milestones": [{{"description": "...", "completion_condition": "..."}}]}}
"""
        response_raw = LLMEngine.call(planning_prompt)
        milestones = LocalPlanner._parse_milestones(response_raw)

        return LocalTrajectory(
            objective=task.objective, milestones=milestones, version=1
        )

    @staticmethod
    def replan(state: DesktopAgentState, reason: str) -> Optional[LocalTrajectory]:
        state.total_replans += 1

        if state.total_replans > state.task.budget.max_replans:
            return None

        satisfied = [
            m.description
            for m in state.trajectory.milestones
            if m.status in (MilestoneStatus.SATISFIED, MilestoneStatus.SKIPPED)
        ]

        replan_prompt = f"""
The previous execution trajectory has become invalid.

Task: {state.task.objective}
Reason for replanning: {reason}
Completed milestones: {satisfied}

Produce a revised list of milestones to complete the remaining objective.
Respond with JSON: {{"milestones": [{{"description": "...", "completion_condition": "..."}}]}}
"""
        response_raw = LLMEngine.call(replan_prompt)
        new_milestones = LocalPlanner._parse_milestones(response_raw)

        old_milestones = [
            m
            for m in state.trajectory.milestones
            if m.status in (MilestoneStatus.SATISFIED, MilestoneStatus.SKIPPED)
        ]

        return LocalTrajectory(
            objective=state.task.objective,
            milestones=old_milestones + new_milestones,
            version=state.trajectory.version + 1,
        )

    @staticmethod
    def get_current_milestone(state: DesktopAgentState) -> Optional[Milestone]:
        if not state.trajectory:
            return None

        for milestone in state.trajectory.milestones:
            if milestone.status == MilestoneStatus.ACTIVE:
                return milestone
            if milestone.status == MilestoneStatus.PENDING:
                milestone.status = MilestoneStatus.ACTIVE
                state.current_milestone_id = milestone.milestone_id
                return milestone
        return None

    @staticmethod
    def advance_milestone(state: DesktopAgentState, evidence: str):
        current = LocalPlanner.get_current_milestone(state)
        if current:
            current.status = MilestoneStatus.SATISFIED
            current.satisfaction_evidence = evidence
            state.current_milestone_id = (
                None  # Cleared, so next get_current_milestone advances
            )

    @staticmethod
    def _parse_milestones(raw: str) -> List[Milestone]:
        try:
            data = json.loads(raw)
            return [Milestone(**m) for m in data.get("milestones", [])]
        except Exception:
            # Fallback mock for robustness
            return [
                Milestone(
                    description="Fallback milestone",
                    completion_condition="Fallback check",
                )
            ]
