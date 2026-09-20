from .models import DesktopAgentState, OutcomeEvaluation
from .llm import LLMEngine


class VerificationManager:
    @staticmethod
    def verify(state: DesktopAgentState) -> OutcomeEvaluation:
        """
        Final objective-level verification before returning result.
        """
        prompt = f"""
Task Objective: {state.task.objective}
Expected Outcome: {state.task.expected_outcome}

Final Observation: {state.current_observation}

Did the agent achieve the objective? Provide JSON with 'objective_achieved' (bool), 'evidence' (list of str), and 'unmet_conditions' (list of str).
"""
        # Note: in real implementation we'd parse this from LLM
        # Mocking for now:
        return OutcomeEvaluation(
            objective_achieved=True,
            evidence=["Final milestone completed."],
            unmet_conditions=[],
        )
