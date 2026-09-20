from typing import Tuple, List, Dict, Optional
from ..models import WindowRef, UIState


class ObservationTools:
    def get_screenshot(self, target: str = "full") -> str:
        # returns path to screenshot
        return "/tmp/screenshot.png"

    def get_ui_tree(self) -> UIState:
        return UIState()

    def get_active_window_info(self) -> WindowRef:
        return WindowRef(title="Desktop")

    def list_all_windows(self) -> List[WindowRef]:
        return []

    def get_cursor_position(self) -> Tuple[int, int]:
        return (0, 0)

    def get_clipboard_content(self) -> str:
        return ""
