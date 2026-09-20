import time
from datetime import datetime, timezone
from .models import DesktopAgentState, DesktopTaskResult, TaskStatus, ExecutionMetadata
from .verification import VerificationManager


class ResultManager:
    @staticmethod
    def build(state: DesktopAgentState) -> DesktopTaskResult:
        outcome = None
        if state.status == "COMPLETED" or state.status == "VERIFYING":
            outcome = VerificationManager.verify(state)
            status = (
                TaskStatus.COMPLETED
                if outcome.objective_achieved
                else TaskStatus.FAILED
            )
        else:
            outcome = None  # Or mock failed outcome
            status = getattr(TaskStatus, state.status.value, TaskStatus.FAILED)

        execution_time = (datetime.now(timezone.utc) - state.start_time).total_seconds()

        return DesktopTaskResult(
            task_id=state.task.task_id,
            status=status,
            summary=f"Task ended with status {status.value}",
            outcome=outcome or getattr(VerificationManager, "verify")(state),
            artifacts=[],
            errors=state.errors,
            execution_metadata=ExecutionMetadata(
                total_actions=state.total_actions,
                total_time_seconds=execution_time,
                replans=state.total_replans,
                human_interventions=1 if state.human_intervention else 0,
            ),
        )
