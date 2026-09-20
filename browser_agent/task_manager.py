from .models import BrowserTask, BrowserTaskResult, BrowserAgentState, AgentStatus
from .planner import LocalPlanner
from .observation import BrowserObservationManager
from .milestone import MilestoneEvaluator
from .execution import BrowserExecutionController
from .result import ResultManager
from .session import BrowserSessionManager
from .tools.registry import BrowserToolRegistry


class BrowserTaskManager:
    @staticmethod
    def run(task: BrowserTask, session_manager: BrowserSessionManager = None) -> BrowserTaskResult:
        if not task.objective:
            raise ValueError("Task objective cannot be empty")

        state = BrowserAgentState(task=task)
        
        # Start session if not provided
        owns_session = False
        if session_manager is None:
            session_manager = BrowserSessionManager()
            owns_session = True

        try:
            # Planning Phase
            state.status = AgentStatus.PLANNING
            trajectory = LocalPlanner.create_trajectory(task)
            state.trajectory = trajectory

            # Initial Environment Scan
            obs_manager = BrowserObservationManager(session_manager)
            registry = BrowserToolRegistry(session_manager)
            
            state.current_observation = obs_manager.observe()
            MilestoneEvaluator.scan_and_skip_satisfied_milestones(state)

            # Execution
            state.status = AgentStatus.EXECUTING
            BrowserExecutionController.run(state, obs_manager, registry)

            # Result
            return ResultManager.build(state)
            
        finally:
            if owns_session:
                session_manager.stop()

    @staticmethod
    def cancel(state: BrowserAgentState) -> BrowserTaskResult:
        state.status = AgentStatus.CANCELLED
        return ResultManager.build(state)
