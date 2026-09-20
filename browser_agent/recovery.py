from .models import BrowserAgentState, AgentStatus
from .planner import LocalPlanner


class RecoveryManager:
    @staticmethod
    def attempt_recovery(state: BrowserAgentState, reason: str):
        """
        Decides which recovery level to apply.
        Currently simple: replan, if out of budget, wait for human.
        """
        new_trajectory = LocalPlanner.replan(state, reason)
        if new_trajectory:
            state.trajectory = new_trajectory
            state.status = AgentStatus.EXECUTING
            state.consecutive_failures = 0
        else:
            state.status = AgentStatus.FAILED
