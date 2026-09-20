from .agent_state import AgentState, MessageIntent, UserMessage
from .llm import MainLLMEngine, MainLLMResponseType
from .context import MainContextManager


class TaskInterpreter:

    @staticmethod
    def interpret(state: AgentState, message: str) -> MessageIntent:
        if not state.task.objective:
            return MessageIntent.NEW_TASK

        prompt = MainContextManager.build_task_interpretation_prompt(state, message)
        response = MainLLMEngine.decide(prompt, MainLLMResponseType.TASK_INTERPRETATION)

        if response.is_error() or not response.data:
            return MessageIntent.NEW_TASK

        intent_str = response.data.get("intent", "NEW_TASK").upper()
        try:
            intent = MessageIntent(intent_str)
        except ValueError:
            intent = MessageIntent.NEW_TASK

        # Apply any updates from the interpretation
        if intent == MessageIntent.MODIFICATION:
            updated_obj = response.data.get("updated_objective")
            if updated_obj:
                state.task.objective = updated_obj

            for req in response.data.get("additional_requirements", []):
                if req and req not in state.task.requirements:
                    state.task.requirements.append(req)

            for con in response.data.get("additional_constraints", []):
                if con and con not in state.task.constraints:
                    state.task.constraints.append(con)

        return intent
