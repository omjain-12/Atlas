from typing import Tuple
from .models import Milestone, BrowserObservation, BrowserAgentState, MilestoneStatus
from .llm import LLMEngine, LLMResponseType


class MilestoneEvaluator:
    @staticmethod
    def is_satisfied(
        milestone: Milestone, observation: BrowserObservation
    ) -> Tuple[bool, str]:
        eval_prompt = f"""
Milestone condition: {milestone.completion_condition}

Current browser state:
URL: {observation.url}
Title: {observation.title}

Is the milestone condition satisfied?
Answer with JSON containing 'milestone_satisfied' and 'evidence' if YES, or empty if NO.
"""
        response = LLMEngine.decide(eval_prompt)
        if response.type == LLMResponseType.MILESTONE_SATISFIED:
            return True, response.evidence or "Condition satisfied according to LLM."
        return False, ""

    @staticmethod
    def scan_and_skip_satisfied_milestones(state: BrowserAgentState):
        if not state.trajectory or not state.current_observation:
            return

        for milestone in state.trajectory.milestones:
            if milestone.status == MilestoneStatus.PENDING:
                satisfied, evidence = MilestoneEvaluator.is_satisfied(
                    milestone, state.current_observation
                )
                if satisfied:
                    milestone.status = MilestoneStatus.SKIPPED
                    milestone.satisfaction_evidence = evidence
                else:
                    break
