from typing import Any, Dict, List, Optional, Tuple
from .agent_state import (
    AgentState,
    AgentStatus,
    AgentType,
    TaskStep,
    TaskStepStatus,
    OutcomeEvaluation,
)
from .planner import MainPlanner
from .llm import MainLLMEngine, MainLLMResponseType
from .context import MainContextManager


class MainExecutionController:

    MAX_ITERATIONS = 200

    @staticmethod
    def run(
        state: AgentState,
        browser_agent=None,
        desktop_agent=None,
    ):
        iterations = 0
        while True:
            iterations += 1
            if iterations > MainExecutionController.MAX_ITERATIONS:
                state.status = AgentStatus.FAILED
                break
            if state.status == AgentStatus.IDLE:
                state.status = AgentStatus.PLANNING

            elif state.status == AgentStatus.PLANNING:
                if state.plan and state.replan_count > 0:
                    # This is a replan — the plan was already replaced before entering this state
                    pass
                else:
                    state.plan = MainPlanner.create_plan(state)
                state.status = AgentStatus.DELEGATING

            elif state.status == AgentStatus.DELEGATING:
                ready_steps = MainPlanner.get_ready_steps(state)

                if not ready_steps and MainPlanner.all_steps_terminal(state):
                    if MainPlanner.has_failed_steps(state):
                        state.status = AgentStatus.ERROR_RECOVERY
                    else:
                        state.status = AgentStatus.VERIFYING
                    continue

                if not ready_steps:
                    # No steps are ready but plan isn't done — something is blocked
                    state.status = AgentStatus.ERROR_RECOVERY
                    state.human_intervention_reason = "No executable steps available and plan is not complete."
                    continue

                # Dispatch ready steps (sequential with GUI mutex)
                for step in ready_steps:
                    if step.requires_gui and state.gui_locked_by is not None:
                        continue  # Skip — GUI is busy

                    if step.requires_gui:
                        state.gui_locked_by = step.id

                    step.status = TaskStepStatus.RUNNING

                    # Inject artifact paths into description
                    description = MainExecutionController._inject_artifacts(
                        step.description, state.artifact_registry
                    )

                    # Dispatch to the appropriate agent
                    result = MainExecutionController._dispatch_step(
                        step, description, browser_agent, desktop_agent, state
                    )

                    # Evaluate the result
                    MainExecutionController._evaluate_result(
                        step, result, state
                    )

                    # Release GUI lock
                    if state.gui_locked_by == step.id:
                        state.gui_locked_by = None

                    # If evaluation triggered a state change, break out
                    if state.status != AgentStatus.DELEGATING:
                        break

                # Check if we should continue delegating or transition
                if state.status == AgentStatus.DELEGATING:
                    if MainPlanner.all_steps_terminal(state):
                        if MainPlanner.has_failed_steps(state):
                            state.status = AgentStatus.ERROR_RECOVERY
                        else:
                            state.status = AgentStatus.VERIFYING
                    elif not MainPlanner.get_ready_steps(state):
                        if MainPlanner.has_failed_steps(state):
                            state.status = AgentStatus.ERROR_RECOVERY

            elif state.status == AgentStatus.EVALUATING:
                # Triggered when a result needed deeper evaluation
                # After evaluation completes, go back to delegating
                state.status = AgentStatus.DELEGATING

            elif state.status == AgentStatus.ERROR_RECOVERY:
                MainExecutionController._handle_error_recovery(
                    state, browser_agent, desktop_agent
                )

            elif state.status == AgentStatus.VERIFYING:
                MainExecutionController._verify_completion(state)
                break

            elif state.status == AgentStatus.COMPLETED:
                break

            elif state.status == AgentStatus.FAILED:
                break

            elif state.status == AgentStatus.WAITING_FOR_HUMAN:
                break

            else:
                state.status = AgentStatus.FAILED
                break

    @staticmethod
    def _dispatch_step(
        step: TaskStep,
        description: str,
        browser_agent,
        desktop_agent,
        state: AgentState,
    ) -> Dict[str, Any]:
        try:
            if step.agent_type == AgentType.BROWSER:
                if browser_agent is None:
                    return {
                        "status": "FAILED",
                        "summary": "Browser agent not available.",
                        "artifacts": [],
                    }
                result = browser_agent.execute_task(
                    description,
                    context=state.shared_workspace,
                )
                return MainExecutionController._normalize_worker_result(result)

            elif step.agent_type == AgentType.DESKTOP:
                if desktop_agent is None:
                    return {
                        "status": "FAILED",
                        "summary": "Desktop agent not available.",
                        "artifacts": [],
                    }
                result = desktop_agent.execute_task(
                    description,
                    context=state.shared_workspace,
                )
                return MainExecutionController._normalize_worker_result(result)

            elif step.agent_type == AgentType.MAIN:
                # MAIN steps are pure reasoning — handled by evaluation prompt
                return {
                    "status": "COMPLETED",
                    "summary": f"Reasoning step completed: {description}",
                    "artifacts": [],
                }

            else:
                return {
                    "status": "FAILED",
                    "summary": f"Unknown agent type: {step.agent_type}",
                    "artifacts": [],
                }
        except Exception as e:
            return {
                "status": "FAILED",
                "summary": f"Execution error: {str(e)}",
                "artifacts": [],
            }

    @staticmethod
    def _normalize_worker_result(result) -> Dict[str, Any]:
        # Handle both BrowserTaskResult and DesktopTaskResult
        status = "COMPLETED"
        if hasattr(result, "status"):
            status_val = result.status
            if hasattr(status_val, "value"):
                status_val = status_val.value
            if status_val in ("FAILED", "BLOCKED", "CANCELLED"):
                status = "FAILED"
            elif status_val == "WAITING_FOR_HUMAN":
                status = "WAITING_FOR_HUMAN"
            else:
                status = "COMPLETED"

        summary = getattr(result, "summary", "No summary available.")

        artifacts = []
        if hasattr(result, "artifacts"):
            for a in result.artifacts:
                artifact_dict = {}
                if hasattr(a, "alias"):
                    artifact_dict["alias"] = a.alias
                elif hasattr(a, "description"):
                    artifact_dict["alias"] = a.description
                if hasattr(a, "path"):
                    artifact_dict["path"] = a.path
                if artifact_dict:
                    artifacts.append(artifact_dict)

        return {
            "status": status,
            "summary": summary,
            "artifacts": artifacts,
        }

    @staticmethod
    def _evaluate_result(
        step: TaskStep,
        result: Dict[str, Any],
        state: AgentState,
    ):
        result_status = result.get("status", "FAILED")
        result_summary = result.get("summary", "")
        result_artifacts = result.get("artifacts", [])

        if result_status == "WAITING_FOR_HUMAN":
            step.status = TaskStepStatus.BLOCKED
            state.status = AgentStatus.WAITING_FOR_HUMAN
            state.human_intervention_reason = result_summary
            return

        if result_status == "FAILED":
            step.retry_count += 1
            if step.retry_count > step.max_retries:
                step.status = TaskStepStatus.FAILED
                step.result_summary = f"Failed after {step.retry_count} attempts: {result_summary}"
                state.completed_steps_log.append(
                    f"FAILED {step.id}: {result_summary}"
                )
            else:
                # Return to PENDING for retry
                step.status = TaskStepStatus.PENDING
            return

        # Success — use LLM to evaluate if this actually advanced the objective
        eval_prompt = MainContextManager.build_evaluation_prompt(
            state, step, result_summary, result_status, result_artifacts
        )
        eval_response = MainLLMEngine.decide(
            eval_prompt, MainLLMResponseType.EVALUATION
        )

        if eval_response.is_error() or not eval_response.data:
            # If evaluation LLM fails, trust the worker's success status
            step.status = TaskStepStatus.COMPLETED
            step.result_summary = result_summary
        else:
            step_succeeded = eval_response.data.get("step_succeeded", True)
            eval_summary = eval_response.data.get("summary", result_summary)

            if step_succeeded:
                step.status = TaskStepStatus.COMPLETED
                step.result_summary = eval_summary
            else:
                step.retry_count += 1
                if step.retry_count > step.max_retries:
                    step.status = TaskStepStatus.FAILED
                    step.result_summary = f"Evaluation determined failure: {eval_summary}"
                else:
                    step.status = TaskStepStatus.PENDING

            needs_replanning = eval_response.data.get("needs_replanning", False)
            if needs_replanning:
                replan_reason = eval_response.data.get("replan_reason", "Evaluation triggered replan")
                new_plan = MainPlanner.replan(state, replan_reason)
                if new_plan is not None:
                    state.plan = new_plan
                    state.status = AgentStatus.PLANNING
                else:
                    state.status = AgentStatus.WAITING_FOR_HUMAN
                    state.human_intervention_reason = (
                        f"Replanning budget exhausted. Reason: {replan_reason}"
                    )
                return

        # Register artifacts
        for artifact in result_artifacts:
            alias = artifact.get("alias", "")
            path = artifact.get("path", "")
            if alias and path:
                state.artifact_registry[alias] = path
                step.produced_artifacts[alias] = path

        # Log completion
        if step.status == TaskStepStatus.COMPLETED:
            state.completed_steps_log.append(
                f"Step {step.id}: {step.result_summary}"
            )

        # Compress memory if log is growing
        MainExecutionController._maybe_compress(state)

    @staticmethod
    def _handle_error_recovery(state: AgentState, browser_agent, desktop_agent):
        failed_steps = [
            s for s in state.plan if s.status == TaskStepStatus.FAILED
        ]

        if not failed_steps:
            state.status = AgentStatus.DELEGATING
            return

        # Check if any failed steps can be retried
        retriable = [s for s in failed_steps if s.retry_count <= s.max_retries]
        if retriable:
            for s in retriable:
                s.status = TaskStepStatus.PENDING
            state.status = AgentStatus.DELEGATING
            return

        # All failed steps exhausted retries — try replanning
        reasons = [f"{s.id}: {s.result_summary}" for s in failed_steps]
        reason = "Failed steps: " + "; ".join(reasons)

        new_plan = MainPlanner.replan(state, reason)
        if new_plan is not None:
            state.plan = new_plan
            state.status = AgentStatus.PLANNING
        else:
            state.status = AgentStatus.WAITING_FOR_HUMAN
            state.human_intervention_reason = (
                f"Cannot recover. Replan budget exhausted. {reason}"
            )

    @staticmethod
    def _verify_completion(state: AgentState):
        prompt = MainContextManager.build_verification_prompt(state)
        response = MainLLMEngine.decide(prompt, MainLLMResponseType.VERIFICATION)

        if response.is_error() or not response.data:
            # If verification LLM fails, check plan status directly
            all_completed = all(
                s.status in (TaskStepStatus.COMPLETED, TaskStepStatus.SKIPPED)
                for s in state.plan
            )
            if all_completed:
                state.status = AgentStatus.COMPLETED
            else:
                state.status = AgentStatus.FAILED
            return

        achieved = response.data.get("objective_achieved", False)
        if achieved:
            state.status = AgentStatus.COMPLETED
        else:
            unmet = response.data.get("unmet_conditions", [])
            reason = f"Verification failed. Unmet: {', '.join(unmet)}" if unmet else "Verification failed."

            new_plan = MainPlanner.replan(state, reason)
            if new_plan is not None:
                state.plan = new_plan
                state.status = AgentStatus.PLANNING
            else:
                state.status = AgentStatus.FAILED

    @staticmethod
    def _maybe_compress(state: AgentState):
        if len(state.completed_steps_log) <= 5:
            return

        prompt = MainContextManager.build_compression_prompt(
            state.completed_steps_log
        )
        response = MainLLMEngine.decide(prompt, MainLLMResponseType.COMPRESSION)

        if not response.is_error() and response.data:
            summary = response.data.get("summary", "")
            if summary:
                state.compressed_summary = (
                    (state.compressed_summary + " " + summary).strip()
                    if state.compressed_summary
                    else summary
                )
                state.completed_steps_log.clear()

    @staticmethod
    def _inject_artifacts(description: str, registry: Dict[str, str]) -> str:
        result = description
        for alias, path in registry.items():
            result = result.replace(f"{{{alias}}}", path)
            result = result.replace(alias, path)
        return result
