import unittest
import json
from desktop_agent.models import DesktopTask
from desktop_agent.agent import DesktopAgent
from desktop_agent.llm import LLMEngine
from desktop_agent.models import TaskStatus


class MockLLMEngineCall:
    def __init__(self):
        self.call_count = 0

    def __call__(self, prompt: str) -> str:
        self.call_count += 1

        # Planning phase
        if "Produce a list of 3-7 milestones" in prompt:
            return json.dumps(
                {
                    "milestones": [
                        {
                            "description": "App open",
                            "completion_condition": "Window visible",
                        },
                        {
                            "description": "Task done",
                            "completion_condition": "Goal achieved",
                        },
                    ]
                }
            )

        # Milestone Eval phase
        if "Is the milestone condition satisfied?" in prompt:
            # We'll say YES on the 4th LLM call
            if self.call_count > 3:
                return json.dumps(
                    {"milestone_satisfied": True, "evidence": "Observed it."}
                )
            return json.dumps({})

        # Execution phase
        return json.dumps(
            {
                "tool_call": {
                    "tool_name": "click_element",
                    "arguments": {"name": "Button"},
                },
                "intent": "Clicking button",
            }
        )


class TestDesktopAgentSmoke(unittest.TestCase):
    def test_end_to_end_execution(self):
        # Override LLM Engine call for testing
        original_call = LLMEngine.call
        LLMEngine.call = MockLLMEngineCall()

        try:
            result = DesktopAgent.execute_task("Open notepad and write hello")

            self.assertEqual(result.status, TaskStatus.COMPLETED)
            self.assertTrue(result.outcome.objective_achieved)
            self.assertGreater(result.execution_metadata.total_actions, 0)
        finally:
            LLMEngine.call = original_call


if __name__ == "__main__":
    unittest.main()
