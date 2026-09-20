import pytest
from unittest.mock import patch, MagicMock
from ..models import BrowserTask, TaskBudget, AgentStatus, MilestoneStatus
from ..agent import BrowserAgent
from ..session import BrowserSessionManager


@pytest.fixture
def mock_session():
    session = MagicMock(spec=BrowserSessionManager)
    session.get_active_page.return_value.url = "https://example.com"
    session.get_active_page.return_value.title.return_value = "Example Domain"
    session.get_pages.return_value = [session.get_active_page.return_value]
    return session


@patch("..planner.LLMEngine.call")
def test_browser_agent_flow(mock_llm_call, mock_session):
    # Setup mock LLM responses
    # 1. Planning response
    # 2. Evaluation response
    # 3. Decision response (tool call)
    # 4. Evaluation response
    mock_llm_call.side_effect = [
        # 1. Planning
        '{"milestones": [{"description": "Search something", "completion_condition": "Results visible"}]}',
        # 2. Evaluation (Not satisfied)
        '{"reason": "Not there yet"}',
        # 3. Decision (Tool Call)
        '{"tool_call": {"tool_name": "search", "arguments": {"query": "test"}}, "intent": "search"}',
        # 4. Evaluation (Satisfied)
        '{"milestone_satisfied": true, "evidence": "Search results are visible"}',
    ]

    task = BrowserTask(
        objective="Search for test",
        budget=TaskBudget(max_actions=5)
    )

    result = BrowserAgent.run(task, session_manager=mock_session)

    assert result.status.value == "COMPLETED"
    assert result.outcome.objective_achieved is True
    assert result.execution_metadata["total_actions"] > 0 or result.outcome.evidence
