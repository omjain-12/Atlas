from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class WorkerStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class UIAElement(BaseModel):
    control_type: str
    name: str
    automation_id: str
    class_name: str
    bounding_rectangle: Optional[Dict[str, int]] = None  # left, top, right, bottom
    supported_patterns: List[str] = Field(
        default_factory=list
    )  # e.g., 'Invoke', 'Value', 'ScrollItem'
    is_keyboard_focusable: bool = False


class DesktopState(BaseModel):
    """
    Production-ready state for the Desktop Worker.
    Tracks the OS-level UI Automation (UIA) tree and window handles.
    """

    delegated_task: str = ""
    status: WorkerStatus = WorkerStatus.IDLE

    # Execution Tracking
    local_plan: List[str] = Field(default_factory=list)
    current_local_step: int = 0
    consecutive_failures: int = 0

    # Window Context
    active_window_title: str = ""
    active_window_handle: Optional[int] = None
    open_windows: List[Dict[str, Any]] = Field(
        default_factory=list
    )  # e.g., [{"hwnd": 123, "title": "Notepad"}]

    # Physical/Visual State
    screen_resolution: Dict[str, int] = Field(
        default_factory=lambda: {"width": 1920, "height": 1080}
    )
    screenshot_path: Optional[str] = None

    # The crucial mapping for the LLM: index -> UIAElement
    interactable_elements: Dict[int, UIAElement] = Field(default_factory=dict)

    # Current Focus
    focused_element_index: Optional[int] = None

    # Local memory/errors
    recent_events: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # Internal memory for the desktop agent across tasks
    domain_memory: Dict[str, Any] = Field(default_factory=dict)
