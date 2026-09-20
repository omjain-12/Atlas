from .models import DesktopTask, DesktopTaskResult, TaskBudget
from .task_manager import TaskManager


class DesktopAgent:
    """
    Public entry point for the Desktop Agent.
    """

    @staticmethod
    def execute_task(objective: str, **kwargs) -> DesktopTaskResult:
        """
        Convenience method to create a task and run it.
        """
        budget = kwargs.pop("budget", TaskBudget())
        task = DesktopTask(objective=objective, budget=budget, **kwargs)
        return TaskManager.run(task)

    @staticmethod
    def run(task: DesktopTask) -> DesktopTaskResult:
        """
        Runs a fully formulated DesktopTask.
        """
        return TaskManager.run(task)
