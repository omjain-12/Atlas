from typing import Dict, List, Optional
from ..models import ElementRef


class InteractionTools:
    # --- Semantic Actions (Preferred) ---
    def click_element(self, element_ref: Dict) -> bool:
        return True

    def type_in_element(self, text: str, element_ref: Dict) -> bool:
        return True

    def focus_element(self, element_ref: Dict) -> bool:
        return True

    def select_element(self, element_ref: Dict) -> bool:
        return True

    # --- Physical Actions (Fallback) ---
    def mouse_click(
        self, x: int, y: int, button: str = "left", clicks: int = 1
    ) -> bool:
        return True

    def mouse_drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        return True

    def mouse_scroll(self, amount: int, direction: str = "down") -> bool:
        return True

    def keyboard_type(self, text: str) -> bool:
        return True

    def keyboard_shortcut(self, keys: List[str]) -> bool:
        return True
