from .models import BrowserAgentState, BrowserTaskResult, TaskStatus, OutcomeEvaluation
from .planner import MilestoneStatus


class ResultManager:
    @staticmethod
    def build(state: BrowserAgentState) -> BrowserTaskResult:
        is_completed = (state.status == "COMPLETED" or state.status == "VERIFYING")
        
        status = TaskStatus.COMPLETED if is_completed else TaskStatus.FAILED
        if state.status == "CANCELLED":
            status = TaskStatus.CANCELLED
        elif state.status == "WAITING_FOR_HUMAN":
            status = TaskStatus.WAITING_FOR_HUMAN
            
        evidence = []
        unmet = []
        if state.trajectory:
            for m in state.trajectory.milestones:
                if m.status == MilestoneStatus.SATISFIED:
                    if m.satisfaction_evidence:
                        evidence.append(f"{m.description}: {m.satisfaction_evidence}")
                elif m.status == MilestoneStatus.SKIPPED:
                    evidence.append(f"{m.description}: (Skipped) {m.satisfaction_evidence}")
                else:
                    unmet.append(m.description)
                    
        # If execution stopped but some milestones were met, we still report failure 
        # for the overall task unless status says otherwise.
        if unmet and status == TaskStatus.COMPLETED:
            status = TaskStatus.FAILED

        outcome = OutcomeEvaluation(
            objective_achieved=(status == TaskStatus.COMPLETED),
            evidence=evidence,
            unmet_conditions=unmet,
        )

        # Build Execution Metadata
        duration = (state.action_history[-1].timestamp - state.start_time).total_seconds() if state.action_history else 0
        
        state.task.budget.max_time_seconds # used for typing maybe
        
        metadata = {
            "total_actions": state.total_actions,
            "total_time_seconds": duration,
            "replans": state.total_replans,
            "human_interventions": 1 if state.human_intervention else 0,
        }

        return BrowserTaskResult(
            task_id=state.task.task_id,
            status=status,
            summary=f"Task ended with status {status.value}.",
            outcome=outcome,
            artifacts=[],
            errors=state.errors,
            execution_metadata=metadata,
        )
