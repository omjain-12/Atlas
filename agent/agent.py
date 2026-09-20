from typing import Optional
from .agent_state import (
    AgentState,
    AgentStatus,
    MainTaskResult,
    MessageIntent,
    OutcomeEvaluation,
    TaskState,
    TaskStepStatus,
    UserMessage,
    Artifact,
)
from .task_interpreter import TaskInterpreter
from .execution import MainExecutionController


class MainAgent:

    def __init__(self, browser_agent=None, desktop_agent=None):
        self._browser_agent = browser_agent
        self._desktop_agent = desktop_agent
        self._state = AgentState()

    def run(self, user_message: str) -> MainTaskResult:
        message = UserMessage(content=user_message)
        self._state.chat_history.append(message)

        intent = TaskInterpreter.interpret(self._state, user_message)
        message.intent = intent

        if intent == MessageIntent.NEW_TASK:
            self._start_new_task(user_message)
        elif intent == MessageIntent.MODIFICATION:
            # Task interpreter already applied modifications to state.task
            self._state.status = AgentStatus.PLANNING
            self._state.plan.clear()
            self._state.replan_count = 0
        elif intent == MessageIntent.CONTINUATION:
            if self._state.status in (
                AgentStatus.COMPLETED,
                AgentStatus.FAILED,
                AgentStatus.WAITING_FOR_HUMAN,
            ):
                self._state.status = AgentStatus.IDLE
        elif intent == MessageIntent.PROGRESS_QUERY:
            return self._build_progress_result()

        # Run the execution controller
        MainExecutionController.run(
            self._state,
            browser_agent=self._browser_agent,
            desktop_agent=self._desktop_agent,
        )

        return self._build_result()

    def get_state(self) -> AgentState:
        return self._state

    def _start_new_task(self, objective: str):
        # Preserve session_id and chat_history for continuity
        session_id = self._state.session_id
        chat_history = self._state.chat_history

        self._state = AgentState(
            session_id=session_id,
            chat_history=chat_history,
        )
        self._state.task = TaskState(objective=objective)

    def _build_result(self) -> MainTaskResult:
        steps_completed = sum(
            1 for s in self._state.plan
            if s.status == TaskStepStatus.COMPLETED
        )
        steps_failed = sum(
            1 for s in self._state.plan
            if s.status == TaskStepStatus.FAILED
        )

        outcome = None
        if self._state.status == AgentStatus.COMPLETED:
            evidence = [
                f"{s.id}: {s.result_summary}"
                for s in self._state.plan
                if s.status == TaskStepStatus.COMPLETED and s.result_summary
            ]
            outcome = OutcomeEvaluation(
                objective_achieved=True,
                evidence=evidence,
            )
        elif self._state.status == AgentStatus.FAILED:
            unmet = [
                s.description
                for s in self._state.plan
                if s.status not in (TaskStepStatus.COMPLETED, TaskStepStatus.SKIPPED)
            ]
            outcome = OutcomeEvaluation(
                objective_achieved=False,
                unmet_conditions=unmet,
            )

        # Collect all produced artifacts
        artifacts = [
            Artifact(alias=alias, path=path)
            for alias, path in self._state.artifact_registry.items()
        ]

        summary = self._build_summary()

        return MainTaskResult(
            session_id=self._state.session_id,
            status=self._state.status,
            summary=summary,
            objective=self._state.task.objective,
            outcome=outcome,
            artifacts=artifacts,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            steps_total=len(self._state.plan),
        )

    def _build_progress_result(self) -> MainTaskResult:
        steps_completed = sum(
            1 for s in self._state.plan
            if s.status == TaskStepStatus.COMPLETED
        )
        total = len(self._state.plan)

        summary_parts = [f"Task: {self._state.task.objective}"]
        summary_parts.append(f"Status: {self._state.status.value}")
        summary_parts.append(f"Progress: {steps_completed}/{total} steps completed")

        if self._state.completed_steps_log:
            summary_parts.append("Recent completions:")
            for entry in self._state.completed_steps_log[-3:]:
                summary_parts.append(f"  - {entry}")

        return MainTaskResult(
            session_id=self._state.session_id,
            status=self._state.status,
            summary="\n".join(summary_parts),
            objective=self._state.task.objective,
            steps_completed=steps_completed,
            steps_total=total,
        )

    def _build_summary(self) -> str:
        status = self._state.status.value
        objective = self._state.task.objective

        if self._state.status == AgentStatus.COMPLETED:
            return f"Task completed: {objective}"
        elif self._state.status == AgentStatus.FAILED:
            return f"Task failed: {objective}"
        elif self._state.status == AgentStatus.WAITING_FOR_HUMAN:
            reason = self._state.human_intervention_reason or "Unknown reason"
            return f"Waiting for user input: {reason}"
        else:
            return f"Task {status.lower()}: {objective}"
