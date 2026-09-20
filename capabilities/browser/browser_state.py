from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class WorkerStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class DOMElement(BaseModel):
    node_id: int
    tag_name: str
    text_content: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    bounding_box: Optional[Dict[str, float]] = None  # x, y, width, height
    is_clickable: bool = False
    is_visible: bool = True


class ViewportInfo(BaseModel):
    width: int = 0
    height: int = 0
    scroll_x: int = 0
    scroll_y: int = 0


class BrowserState(BaseModel):
    """
    Production-ready state for the Browser Worker.
    Contains the rigorous technical details required for an LLM to accurately interact with a DOM.
    """

    delegated_task: str = ""
    status: WorkerStatus = WorkerStatus.IDLE

    # Execution Tracking
    local_plan: List[str] = Field(default_factory=list)
    current_local_step: int = 0
    consecutive_failures: int = 0

    # Page Context
    current_url: str = ""
    page_title: str = ""
    tabs: List[Dict[str, Any]] = Field(
        default_factory=list
    )  # e.g. [{"target_id": "...", "url": "..."}]

    # Physical/Visual State
    viewport: ViewportInfo = Field(default_factory=ViewportInfo)
    screenshot_path: Optional[str] = None

    # The crucial mapping for the LLM: index -> DOMElement
    # This allows the LLM to output "click 15" instead of writing a complex XPath
    interactable_elements: Dict[int, DOMElement] = Field(default_factory=dict)

    # Async loading state (Vital for browser automation)
    pending_network_requests: int = 0
    is_page_loading: bool = False

    # Local memory/errors
    recent_events: List[str] = Field(
        default_factory=list
    )  # e.g. "Clicked login button", "Navigation timeout"
    errors: List[str] = Field(default_factory=list)

    # Internal memory for the browser agent across tasks
    domain_memory: Dict[str, Any] = Field(default_factory=dict)
