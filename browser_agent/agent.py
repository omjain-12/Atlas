from .models import BrowserTask, BrowserTaskResult, TaskBudget
from .task_manager import BrowserTaskManager
from .session import BrowserSessionManager


class BrowserAgent:
    """
    Public entry point for the Browser Agent.
    """

    @staticmethod
    def execute_task(objective: str, session_manager: BrowserSessionManager = None, **kwargs) -> BrowserTaskResult:
        """
        Convenience method to create a task and run it.
        """
        budget = kwargs.pop("budget", TaskBudget())
        task = BrowserTask(objective=objective, budget=budget, **kwargs)
        return BrowserTaskManager.run(task, session_manager=session_manager)

    @staticmethod
    def run(task: BrowserTask, session_manager: BrowserSessionManager = None) -> BrowserTaskResult:
        """
        Runs a fully formulated BrowserTask.
        """
        return BrowserTaskManager.run(task, session_manager=session_manager)
