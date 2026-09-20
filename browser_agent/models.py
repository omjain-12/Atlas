from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class MilestoneStatus(str, Enum):
    PENDING = "PENDING"  # Not yet reached. Not being worked on.
    ACTIVE = "ACTIVE"  # Currently being worked toward.
    SATISFIED = "SATISFIED"  # Completion condition confirmed true.
    SKIPPED = "SKIPPED"  # Was already satisfied before it became active.
    BLOCKED = "BLOCKED"  # Cannot be satisfied; requires replanning or human.


class AgentStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    EVALUATING_MILESTONE = "EVALUATING_MILESTONE"
    RECOVERING = "RECOVERING"
    REPLANNING = "REPLANNING"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    WAITING_FOR_HUMAN = "WAITING_FOR_HUMAN"
    CANCELLED = "CANCELLED"


class ErrorType(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    ELEMENT_RESOLUTION_ERROR = "ELEMENT_RESOLUTION_ERROR"
    POLICY_DENIAL = "POLICY_DENIAL"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    LLM_ERROR = "LLM_ERROR"


class ExecutionError(BaseModel):
    type: ErrorType
    message: str
    is_retriable: bool = True


class TaskBudget(BaseModel):
    max_actions: int = 60
    max_time_seconds: int = 300
    max_consecutive_failures: int = 4
    max_replans: int = 2


class BrowserTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    objective: str
    instructions: List[str] = Field(default_factory=list)
    expected_outcome: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    budget: TaskBudget = Field(default_factory=TaskBudget)


class Milestone(BaseModel):
    milestone_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    completion_condition: str
    status: MilestoneStatus = MilestoneStatus.PENDING
    satisfaction_evidence: Optional[str] = None


class LocalTrajectory(BaseModel):
    trajectory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    objective: str
    milestones: List[Milestone]
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TabRef(BaseModel):
    tab_id: int
    title: str
    url: str


class ElementNode(BaseModel):
    element_ref: int
    tag_name: str
    text: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    is_interactive: bool = True
    is_visible: bool = True
    bounding_box: Optional[Dict[str, int]] = None


class BrowserObservation(BaseModel):
    observation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    url: str = ''
    title: str = ''
    tabs: List[TabRef] = Field(default_factory=list)
    active_tab_id: Optional[int] = None
    dom_elements: List[ElementNode] = Field(default_factory=list)
    screenshot_path: Optional[str] = None


class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ToolResult(BaseModel):
    success: bool
    output: Any = None
    error: Optional[ExecutionError] = None
    execution_method: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    milestone_id: str
    observation: BrowserObservation
    llm_intent: str
    tool_call: ToolCall
    tool_result: ToolResult
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumanInterventionState(BaseModel):
    reason: str
    prompt: str
    context: Dict[str, Any]


class BrowserAgentState(BaseModel):
    task: BrowserTask
    status: AgentStatus = AgentStatus.INITIALIZING
    trajectory: Optional[LocalTrajectory] = None
    current_milestone_id: Optional[str] = None
    current_observation: Optional[BrowserObservation] = None
    action_history: List[ActionRecord] = Field(default_factory=list)
    errors: List[ExecutionError] = Field(default_factory=list)
    consecutive_failures: int = 0
    total_actions: int = 0
    total_replans: int = 0
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    human_intervention: Optional[HumanInterventionState] = None


class Artifact(BaseModel):
    type: str
    path: str
    description: str


class ExecutionMetadata(BaseModel):
    total_actions: int = 0
    total_time_seconds: float = 0.0
    replans: int = 0
    human_interventions: int = 0


class OutcomeEvaluation(BaseModel):
    objective_achieved: bool
    evidence: List[str] = Field(default_factory=list)
    unmet_conditions: List[str] = Field(default_factory=list)


class BrowserTaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    summary: str
    outcome: OutcomeEvaluation
    artifacts: List[Artifact] = Field(default_factory=list)
    errors: List[ExecutionError] = Field(default_factory=list)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
