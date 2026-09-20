from .models import DesktopTask, DesktopTaskResult, DesktopAgentState, AgentStatus
from .planner import LocalPlanner
from .observation import ObservationManager
from .milestone import MilestoneEvaluator
from .execution import ExecutionController
from .result import ResultManager


class TaskManager:
    @staticmethod
    def run(task: DesktopTask) -> DesktopTaskResult:
        if not task.objective:
            raise ValueError("Task objective cannot be empty")

        state = DesktopAgentState(task=task)

        # Planning Phase
        state.status = AgentStatus.PLANNING
        trajectory = LocalPlanner.create_trajectory(task)
        state.trajectory = trajectory

        # Initial Environment Scan
        obs_manager = ObservationManager()
        state.current_observation = obs_manager.acquire()
        MilestoneEvaluator.scan_and_skip_satisfied_milestones(state)

        # Execution
        state.status = AgentStatus.EXECUTING
        ExecutionController.run(state)

        # Result
        return ResultManager.build(state)

    @staticmethod
    def cancel(state: DesktopAgentState) -> DesktopTaskResult:
        state.status = AgentStatus.CANCELLED
        return ResultManager.build(state)
