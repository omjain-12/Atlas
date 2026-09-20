from typing import List, Optional
from .agent_state import (
    AgentState,
    TaskStep,
    TaskStepStatus,
    UserMessage,
)


class MainContextManager:

    @staticmethod
    def build_planning_prompt(state: AgentState) -> str:
        completed_context = MainContextManager._format_completed_context(state)
        artifact_context = MainContextManager._format_artifact_registry(state)

        return f"""You are the Main Orchestrator for an autonomous computer-use agent.

# User Objective
{state.task.objective}

# Requirements
{MainContextManager._format_list(state.task.requirements)}

# Constraints
{MainContextManager._format_list(state.task.constraints)}

# Completed Work So Far
{completed_context}

# Available Artifacts
{artifact_context}

# Available Agents
- BROWSER: Can navigate websites, search, click, type, extract data, download files.
- DESKTOP: Can open applications, interact with Windows UI elements, type, click, manage files.
- MAIN: For pure reasoning or data synthesis steps that don't need a specific agent.

# Instructions
Create a plan of execution. Break the objective into sub-tasks.
For each task, specify:
- id: A short unique identifier (e.g., "s1", "s2")
- description: A detailed instruction for the sub-agent
- agent_type: "BROWSER", "DESKTOP", or "MAIN"
- dependencies: List of task IDs that must finish before this one starts (empty list if none)
- requires_gui: true if the task needs physical mouse/keyboard focus, false otherwise

Output as JSON: {{"steps": [...]}}"""

    @staticmethod
    def build_evaluation_prompt(
        state: AgentState,
        step: TaskStep,
        result_summary: str,
        result_status: str,
        artifacts: list,
    ) -> str:
        return f"""You are evaluating whether a delegated sub-task actually advanced the user's objective.

# Overall Objective
{state.task.objective}

# Sub-Task That Was Executed
Step ID: {step.id}
Description: {step.description}
Agent: {step.agent_type.value}

# Execution Result
Status: {result_status}
Summary: {result_summary}
Artifacts Produced: {artifacts}

# Question
Did this execution result actually advance the overall objective?
Consider:
- Did it produce the expected output?
- Is the result usable for subsequent steps?
- Does the remaining plan need to change?

Respond with JSON:
{{
    "step_succeeded": true/false,
    "summary": "concise description of what was achieved",
    "needs_replanning": true/false,
    "replan_reason": "why replanning is needed (if applicable)"
}}"""

    @staticmethod
    def build_task_interpretation_prompt(
        state: AgentState, new_message: str
    ) -> str:
        recent_history = ""
        for msg in state.chat_history[-5:]:
            recent_history += f"- {msg.content}\n"

        current_objective = state.task.objective or "None"
        plan_summary = MainContextManager._format_plan_status(state)

        return f"""You are determining how a new user message relates to the current task.

# Current Task Objective
{current_objective}

# Current Plan Status
{plan_summary}

# Recent Chat History
{recent_history}

# New User Message
{new_message}

# Question
What is the intent of this new message? Choose one:
- NEW_TASK: The user is starting a completely new, unrelated task.
- CONTINUATION: The user is continuing or following up on the existing task.
- MODIFICATION: The user is changing or refining the existing task requirements.
- PROGRESS_QUERY: The user is asking about the current task's progress.

Respond with JSON:
{{
    "intent": "NEW_TASK" | "CONTINUATION" | "MODIFICATION" | "PROGRESS_QUERY",
    "updated_objective": "the objective (new or updated), if applicable",
    "additional_requirements": ["any new requirements"],
    "additional_constraints": ["any new constraints"]
}}"""

    @staticmethod
    def build_verification_prompt(state: AgentState) -> str:
        completed_context = MainContextManager._format_completed_context(state)
        artifact_context = MainContextManager._format_artifact_registry(state)
        plan_summary = MainContextManager._format_plan_status(state)

        return f"""You are performing a final verification of the overall task completion.

# User Objective
{state.task.objective}

# Requirements
{MainContextManager._format_list(state.task.requirements)}

# Plan Status
{plan_summary}

# Completed Work
{completed_context}

# Available Artifacts
{artifact_context}

# Question
Were all necessary objectives achieved?
Consider whether the user's actual goal has been accomplished, not just whether individual steps ran.

Respond with JSON:
{{
    "objective_achieved": true/false,
    "evidence": ["list of evidence supporting completion"],
    "unmet_conditions": ["list of anything still missing"]
}}"""

    @staticmethod
    def build_compression_prompt(entries: List[str]) -> str:
        log_text = "\n".join(entries)
        return f"""Summarize the following completed task steps into a concise paragraph that preserves all important facts, data, file paths, and results.

Steps:
{log_text}

Respond with JSON: {{"summary": "your compressed summary"}}"""

    # --- Helpers ---

    @staticmethod
    def _format_completed_context(state: AgentState) -> str:
        parts = []
        if state.compressed_summary:
            parts.append(f"Previous summary: {state.compressed_summary}")
        if state.completed_steps_log:
            parts.append("Recent steps:")
            for entry in state.completed_steps_log:
                parts.append(f"  - {entry}")
        return "\n".join(parts) if parts else "No work completed yet."

    @staticmethod
    def _format_artifact_registry(state: AgentState) -> str:
        if not state.artifact_registry:
            return "No artifacts available."
        lines = []
        for alias, path in state.artifact_registry.items():
            lines.append(f"  {alias}: {path}")
        return "\n".join(lines)

    @staticmethod
    def _format_plan_status(state: AgentState) -> str:
        if not state.plan:
            return "No plan created yet."
        lines = []
        for step in state.plan:
            deps = f" (depends on: {', '.join(step.dependencies)})" if step.dependencies else ""
            lines.append(f"[{step.status.value}] {step.id}: {step.description}{deps}")
        return "\n".join(lines)

    @staticmethod
    def _format_list(items: List[str]) -> str:
        if not items:
            return "None"
        return "\n".join(f"- {item}" for item in items)
