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


class ObservationScope(str, Enum):
    WINDOW_LIST = "WINDOW_LIST"
    UI_TREE = "UI_TREE"
    SCREENSHOT = "SCREENSHOT"
    CLIPBOARD = "CLIPBOARD"
    FULL = "FULL"


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


class DesktopTask(BaseModel):
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


class WindowRef(BaseModel):
    hwnd: Optional[int] = None
    title: Optional[str] = None
    process_name: Optional[str] = None


class ElementRef(BaseModel):
    name: Optional[str] = None
    control_type: Optional[str] = None
    automation_id: Optional[str] = None
    window_ref: Optional[WindowRef] = None
    runtime_id: Optional[List[int]] = None
    bounding_box: Optional[Dict[str, int]] = None


class UIElement(BaseModel):
    ref: ElementRef
    is_enabled: bool = True
    is_focused: bool = False
    supported_patterns: List[str] = Field(default_factory=list)


class UIState(BaseModel):
    active_window: Optional[WindowRef] = None
    windows: List[WindowRef] = Field(default_factory=list)
    focused_element: Optional[ElementRef] = None
    tree: List[UIElement] = Field(default_factory=list)


class Observation(BaseModel):
    observation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scope: ObservationScope
    active_window: Optional[WindowRef] = None
    windows: Optional[List[WindowRef]] = None
    ui_tree: Optional[UIState] = None
    screenshot_path: Optional[str] = None
    clipboard: Optional[str] = None


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
    observation: Observation
    llm_intent: str
    tool_call: ToolCall
    tool_result: ToolResult
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HumanInterventionState(BaseModel):
    reason: str
    prompt: str
    context: Dict[str, Any]


class DesktopAgentState(BaseModel):
    task: DesktopTask
    status: AgentStatus = AgentStatus.INITIALIZING
    trajectory: Optional[LocalTrajectory] = None
    current_milestone_id: Optional[str] = None
    current_observation: Optional[Observation] = None
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


class DesktopTaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    summary: str
    outcome: OutcomeEvaluation
    artifacts: List[Artifact] = Field(default_factory=list)
    errors: List[ExecutionError] = Field(default_factory=list)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
