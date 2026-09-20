from typing import Tuple
from .models import Milestone, Observation, DesktopAgentState, MilestoneStatus
from .llm import LLMEngine, LLMResponseType


class MilestoneEvaluator:
    @staticmethod
    def is_satisfied(
        milestone: Milestone, observation: Observation
    ) -> Tuple[bool, str]:
        """
        Ask LLM to evaluate the condition against the observation.
        """
        active_window_title = (
            observation.active_window.title if observation.active_window else "None"
        )

        eval_prompt = f"""
Milestone condition: {milestone.completion_condition}

Current desktop state:
Active window: {active_window_title}

Is the milestone condition satisfied?
Answer with JSON containing 'milestone_satisfied' and 'evidence' if YES, or empty if NO.
"""
        response = LLMEngine.decide(eval_prompt)
        if response.type == LLMResponseType.MILESTONE_SATISFIED:
            return True, response.evidence or "Condition satisfied according to LLM."
        return False, ""

    @staticmethod
    def scan_and_skip_satisfied_milestones(state: DesktopAgentState):
        """
        Called once at startup. If the environment is already ahead of the plan,
        mark those milestones SKIPPED rather than executing them.
        """
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
                    break  # Stop at first unsatisfied milestone
