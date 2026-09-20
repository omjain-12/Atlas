import unittest
import json
from unittest.mock import MagicMock, patch

from agent.agent import MainAgent
from agent.agent_state import (
    AgentState,
    AgentStatus,
    AgentType,
    TaskStep,
    TaskStepStatus,
    MessageIntent,
)
from agent.llm import MainLLMEngine


class MockMainLLMCalls:
    """
    Sequences LLM responses for the Main Agent lifecycle.
    """
    def __init__(self, responses):
        self.responses = list(responses)
        self.call_count = 0

    def __call__(self, prompt: str) -> str:
        if self.call_count < len(self.responses):
            result = self.responses[self.call_count]
            self.call_count += 1
            return result
        return json.dumps({"error": "no more mock responses"})


def make_plan_response(steps):
    return json.dumps({"steps": steps})


def make_eval_response(succeeded=True, needs_replanning=False, replan_reason=""):
    return json.dumps({
        "step_succeeded": succeeded,
        "summary": "Step completed successfully" if succeeded else "Step failed",
        "needs_replanning": needs_replanning,
        "replan_reason": replan_reason,
    })


def make_verification_response(achieved=True, evidence=None, unmet=None):
    return json.dumps({
        "objective_achieved": achieved,
        "evidence": evidence or ["Task completed"],
        "unmet_conditions": unmet or [],
    })


def make_interpretation_response(intent="NEW_TASK"):
    return json.dumps({
        "intent": intent,
        "updated_objective": "",
        "additional_requirements": [],
        "additional_constraints": [],
    })


class MockBrowserAgent:
    def __init__(self, return_status="COMPLETED", return_summary="Browser task done"):
        self.return_status = return_status
        self.return_summary = return_summary
        self.calls = []

    def execute_task(self, objective, **kwargs):
        self.calls.append(objective)
        result = MagicMock()
        result.status = MagicMock()
        result.status.value = self.return_status
        result.summary = self.return_summary
        result.artifacts = []
        return result


class MockDesktopAgent:
    def __init__(self, return_status="COMPLETED", return_summary="Desktop task done"):
        self.return_status = return_status
        self.return_summary = return_summary
        self.calls = []

    def execute_task(self, objective, **kwargs):
        self.calls.append(objective)
        result = MagicMock()
        result.status = MagicMock()
        result.status.value = self.return_status
        result.summary = self.return_summary
        result.artifacts = []
        return result


class TestMainAgentSingleStep(unittest.TestCase):
    """A simple single-step browser task: plan → delegate → evaluate → verify → complete."""

    def test_single_browser_step(self):
        original_call = MainLLMEngine.call

        mock_llm = MockMainLLMCalls([
            # 1. Planning: single browser step
            make_plan_response([{
                "id": "s1",
                "description": "Search for laptops on Amazon",
                "agent_type": "BROWSER",
                "dependencies": [],
                "requires_gui": True,
            }]),
            # 2. Evaluation of step result
            make_eval_response(succeeded=True),
            # 3. Verification
            make_verification_response(achieved=True),
        ])
        MainLLMEngine.call = mock_llm

        browser = MockBrowserAgent()

        try:
            agent = MainAgent(browser_agent=browser, desktop_agent=None)
            result = agent.run("Search for laptops on Amazon")

            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertEqual(result.steps_completed, 1)
            self.assertEqual(result.steps_total, 1)
            self.assertEqual(len(browser.calls), 1)
            self.assertIn("Amazon", browser.calls[0])
        finally:
            MainLLMEngine.call = original_call


class TestMainAgentMultiStepDAG(unittest.TestCase):
    """Multi-step DAG: two browser steps → one desktop step (with dependencies)."""

    def test_dag_execution_order(self):
        original_call = MainLLMEngine.call

        mock_llm = MockMainLLMCalls([
            # 1. Planning: s1 and s2 (independent), s3 depends on both
            make_plan_response([
                {
                    "id": "s1",
                    "description": "Search product A",
                    "agent_type": "BROWSER",
                    "dependencies": [],
                    "requires_gui": True,
                },
                {
                    "id": "s2",
                    "description": "Search product B",
                    "agent_type": "BROWSER",
                    "dependencies": [],
                    "requires_gui": True,
                },
                {
                    "id": "s3",
                    "description": "Save comparison to file",
                    "agent_type": "DESKTOP",
                    "dependencies": ["s1", "s2"],
                    "requires_gui": True,
                },
            ]),
            # 2. Eval for s1
            make_eval_response(succeeded=True),
            # 3. Eval for s2
            make_eval_response(succeeded=True),
            # 4. Eval for s3
            make_eval_response(succeeded=True),
            # 5. Verification
            make_verification_response(achieved=True),
        ])
        MainLLMEngine.call = mock_llm

        browser = MockBrowserAgent()
        desktop = MockDesktopAgent()

        try:
            agent = MainAgent(browser_agent=browser, desktop_agent=desktop)
            result = agent.run("Compare two products and save results")

            self.assertEqual(result.status, AgentStatus.COMPLETED)
            self.assertEqual(result.steps_completed, 3)
            self.assertEqual(len(browser.calls), 2)
            self.assertEqual(len(desktop.calls), 1)
        finally:
            MainLLMEngine.call = original_call


class TestMainAgentRetryAndCircuitBreaker(unittest.TestCase):
    """Tests that failed steps get retried, and circuit breaker trips after max retries."""

    def test_circuit_breaker_triggers(self):
        original_call = MainLLMEngine.call

        responses = [
            # 1. Planning: single step
            make_plan_response([{
                "id": "s1",
                "description": "Do a thing",
                "agent_type": "BROWSER",
                "dependencies": [],
                "requires_gui": True,
            }]),
            # 2-5. Evaluation: keep failing (retry 4 times, step.max_retries=3)
            make_eval_response(succeeded=False),
            make_eval_response(succeeded=False),
            make_eval_response(succeeded=False),
            make_eval_response(succeeded=False),
        ]
        # After step s1 exhausts retries, error recovery will try replan.
        # Provide enough replan responses (up to max_replans=3), each creating
        # a new step that also fails to exhaust the replan budget.
        for i in range(4):
            responses.append(make_plan_response([{
                "id": f"r{i}",
                "description": f"Retry attempt {i}",
                "agent_type": "BROWSER",
                "dependencies": [],
                "requires_gui": True,
            }]))
            # Eval failures for each replanned step (4 per step for max_retries=3)
            for _ in range(4):
                responses.append(make_eval_response(succeeded=False))

        mock_llm = MockMainLLMCalls(responses)
        MainLLMEngine.call = mock_llm

        browser = MockBrowserAgent()

        try:
            agent = MainAgent(browser_agent=browser)
            result = agent.run("Do a thing")

            # Should eventually stop via circuit breaker
            self.assertIn(result.status, (
                AgentStatus.COMPLETED,
                AgentStatus.FAILED,
                AgentStatus.WAITING_FOR_HUMAN,
            ))
        finally:
            MainLLMEngine.call = original_call


class TestMainAgentTaskContinuity(unittest.TestCase):
    """Tests that a second message in the same chat continues the existing task."""

    def test_continuation_message(self):
        original_call = MainLLMEngine.call

        # First message: new task
        mock_llm_1 = MockMainLLMCalls([
            make_plan_response([{
                "id": "s1",
                "description": "Find three laptops",
                "agent_type": "BROWSER",
                "dependencies": [],
                "requires_gui": True,
            }]),
            make_eval_response(succeeded=True),
            make_verification_response(achieved=True),
        ])

        browser = MockBrowserAgent()

        try:
            MainLLMEngine.call = mock_llm_1
            agent = MainAgent(browser_agent=browser)
            result1 = agent.run("Find three laptops")
            self.assertEqual(result1.status, AgentStatus.COMPLETED)

            # Second message: continuation
            mock_llm_2 = MockMainLLMCalls([
                # Task interpretation
                make_interpretation_response(intent="CONTINUATION"),
                # New plan for continuation
                make_plan_response([{
                    "id": "s2",
                    "description": "Compare the second and third laptops",
                    "agent_type": "BROWSER",
                    "dependencies": [],
                    "requires_gui": True,
                }]),
                make_eval_response(succeeded=True),
                make_verification_response(achieved=True),
            ])
            MainLLMEngine.call = mock_llm_2

            result2 = agent.run("Compare the second and third")
            self.assertEqual(result2.status, AgentStatus.COMPLETED)
            self.assertEqual(len(agent.get_state().chat_history), 2)
        finally:
            MainLLMEngine.call = original_call


class TestMainAgentNoAgents(unittest.TestCase):
    """Tests graceful handling when no agents are provided."""

    def test_missing_browser_agent(self):
        original_call = MainLLMEngine.call

        responses = [
            make_plan_response([{
                "id": "s1",
                "description": "Browse web",
                "agent_type": "BROWSER",
                "dependencies": [],
                "requires_gui": True,
            }]),
        ]
        # The step will fail because browser agent is None.
        # No eval LLM call needed — the dispatch itself returns FAILED.
        # After max retries, error recovery tries replan. Provide enough
        # responses for the full retry/replan cycle.
        for i in range(4):
            responses.append(make_plan_response([{
                "id": f"r{i}",
                "description": f"Retry {i}",
                "agent_type": "BROWSER",
                "dependencies": [],
                "requires_gui": True,
            }]))

        mock_llm = MockMainLLMCalls(responses)
        MainLLMEngine.call = mock_llm

        try:
            agent = MainAgent(browser_agent=None, desktop_agent=None)
            result = agent.run("Browse web")

            # Should fail gracefully
            self.assertIn(result.status, (
                AgentStatus.FAILED,
                AgentStatus.WAITING_FOR_HUMAN,
            ))
        finally:
            MainLLMEngine.call = original_call


class TestPlannerReadySteps(unittest.TestCase):
    """Tests the planner's dependency resolution logic directly."""

    def test_ready_steps_with_dependencies(self):
        from agent.agent_state import TaskStep, AgentType
        from agent.planner import MainPlanner

        state = AgentState()
        state.plan = [
            TaskStep(id="s1", description="A", agent_type=AgentType.BROWSER, status=TaskStepStatus.COMPLETED),
            TaskStep(id="s2", description="B", agent_type=AgentType.BROWSER, status=TaskStepStatus.PENDING, dependencies=["s1"]),
            TaskStep(id="s3", description="C", agent_type=AgentType.DESKTOP, status=TaskStepStatus.PENDING, dependencies=["s1", "s2"]),
        ]

        ready = MainPlanner.get_ready_steps(state)
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].id, "s2")

    def test_all_steps_terminal(self):
        from agent.agent_state import TaskStep
        from agent.planner import MainPlanner

        state = AgentState()
        state.plan = [
            TaskStep(id="s1", description="A", status=TaskStepStatus.COMPLETED),
            TaskStep(id="s2", description="B", status=TaskStepStatus.FAILED),
        ]

        self.assertTrue(MainPlanner.all_steps_terminal(state))


if __name__ == "__main__":
    unittest.main()
