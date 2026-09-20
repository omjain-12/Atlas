from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class AgentStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    DELEGATING = "delegating"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class PlanItemStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PlanItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str
    status: PlanItemStatus = PlanItemStatus.PENDING
    assigned_worker: Optional[str] = None
    result_summary: Optional[str] = None


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AgentState(BaseModel):
    """
    Production-ready state for the Main Orchestrator.
    Manages the lifecycle, complex planning, and execution metrics of the autonomous agent.
    """

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    goal: str = ""
    status: AgentStatus = AgentStatus.IDLE

    # Advanced Planning (Replacing the simple string list)
    plan: List[PlanItem] = Field(default_factory=list)
    current_plan_item_id: Optional[str] = None

    # Context & Handoff
    shared_workspace: Dict[str, Any] = Field(default_factory=dict)

    # State tracking
    active_worker: Optional[str] = None
    n_steps_taken: int = 0
    consecutive_failures: int = 0
    max_steps_allowed: int = 100

    # Observability
    token_usage: TokenUsage = Field(default_factory=TokenUsage)

    # Track conversation references without bloating the Pydantic state model
    conversation_id: Optional[str] = None
