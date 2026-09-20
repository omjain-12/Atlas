from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    DELEGATING = "DELEGATING"
    WAITING_FOR_WORKERS = "WAITING_FOR_WORKERS"
    EVALUATING = "EVALUATING"
    ERROR_RECOVERY = "ERROR_RECOVERY"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskStepStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class AgentType(str, Enum):
    BROWSER = "BROWSER"
    DESKTOP = "DESKTOP"
    MAIN = "MAIN"


class MessageIntent(str, Enum):
    NEW_TASK = "NEW_TASK"
    CONTINUATION = "CONTINUATION"
    MODIFICATION = "MODIFICATION"
    PROGRESS_QUERY = "PROGRESS_QUERY"


class TaskStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str
    agent_type: AgentType = AgentType.BROWSER
    dependencies: List[str] = Field(default_factory=list)
    status: TaskStepStatus = TaskStepStatus.PENDING
    requires_gui: bool = True
    retry_count: int = 0
    max_retries: int = 3
    result_summary: str = ""
    produced_artifacts: Dict[str, str] = Field(default_factory=dict)


class UserMessage(BaseModel):
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    intent: Optional[MessageIntent] = None


class TaskState(BaseModel):
    objective: str = ""
    requirements: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class Artifact(BaseModel):
    alias: str
    path: str
    description: str = ""
    produced_by_step: Optional[str] = None


class OutcomeEvaluation(BaseModel):
    objective_achieved: bool
    evidence: List[str] = Field(default_factory=list)
    unmet_conditions: List[str] = Field(default_factory=list)


class MainTaskResult(BaseModel):
    session_id: str
    status: AgentStatus
    summary: str
    objective: str = ""
    outcome: Optional[OutcomeEvaluation] = None
    artifacts: List[Artifact] = Field(default_factory=list)
    steps_completed: int = 0
    steps_failed: int = 0
    steps_total: int = 0


class AgentState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    status: AgentStatus = AgentStatus.IDLE

    task: TaskState = Field(default_factory=TaskState)
    plan: List[TaskStep] = Field(default_factory=list)
    chat_history: List[UserMessage] = Field(default_factory=list)

    # Artifact registry for cross-agent data handoff
    artifact_registry: Dict[str, str] = Field(default_factory=dict)

    # Completed steps log for context compression
    completed_steps_log: List[str] = Field(default_factory=list)
    compressed_summary: str = ""

    # GUI mutex — tracks which step currently holds the lock
    gui_locked_by: Optional[str] = None

    # Circuit breakers
    replan_count: int = 0
    max_replans: int = 3

    # Shared workspace for cross-domain data handoff
    shared_workspace: Dict[str, Any] = Field(default_factory=dict)

    # Observability
    token_usage: TokenUsage = Field(default_factory=TokenUsage)

    # Human intervention
    human_intervention_reason: Optional[str] = None
