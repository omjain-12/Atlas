import json
from typing import Optional, List
from .models import (
    BrowserTask,
    LocalTrajectory,
    BrowserAgentState,
    Milestone,
    MilestoneStatus,
)
from .llm import LLMEngine


class LocalPlanner:
    @staticmethod
    def create_trajectory(task: BrowserTask) -> LocalTrajectory:
        planning_prompt = f"""
You are planning a browser task.

Task: {task.objective}
Constraints: {task.constraints}
Hints: {task.instructions}

Produce a list of 2-7 milestones to complete this task in the browser.
Each milestone must be an OBSERVABLE CONDITION (e.g., 'Search results for X are visible', 'URL Y is extracted'), not an action.
Respond with JSON: {{"milestones": [{{"description": "...", "completion_condition": "..."}}]}}
"""
        response_raw = LLMEngine.call(planning_prompt)
        milestones = LocalPlanner._parse_milestones(response_raw)

        return LocalTrajectory(
            objective=task.objective, milestones=milestones, version=1
        )

    @staticmethod
    def replan(state: BrowserAgentState, reason: str) -> Optional[LocalTrajectory]:
        state.total_replans += 1

        if state.total_replans > state.task.budget.max_replans:
            return None

        satisfied = [
            m.description
            for m in state.trajectory.milestones
            if m.status in (MilestoneStatus.SATISFIED, MilestoneStatus.SKIPPED)
        ]

        replan_prompt = f"""
The previous browser execution trajectory has become invalid.

Task: {state.task.objective}
Reason for replanning: {reason}
Completed milestones: {satisfied}

Produce a revised list of milestones to complete the remaining objective in the browser.
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
    def get_active_milestone(state: BrowserAgentState) -> Optional[Milestone]:
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
    def advance(state: BrowserAgentState, evidence: str = ""):
        current = LocalPlanner.get_active_milestone(state)
        if current:
            current.status = MilestoneStatus.SATISFIED
            current.satisfaction_evidence = evidence
            state.current_milestone_id = None

    @staticmethod
    def _parse_milestones(raw: str) -> List[Milestone]:
        try:
            data = json.loads(raw)
            return [Milestone(**m) for m in data.get("milestones", [])]
        except Exception:
            return [
                Milestone(
                    description="Complete browser task",
                    completion_condition="Goal is achieved",
                )
            ]
