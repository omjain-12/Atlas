from typing import Dict, List
import uiautomation as auto
import pyautogui


class InteractionTools:
    # --- Semantic Actions (Preferred) ---
    def click_element(self, element_ref: Dict) -> bool:
        try:
            ctrl = auto.Control(**element_ref)
            if not ctrl.Exists(0, 0):
                return False
            try:
                ctrl.GetInvokePattern().Invoke()
            except Exception:
                ctrl.Click()
            return True
        except Exception:
            return False

    def type_in_element(self, text: str, element_ref: Dict) -> bool:
        try:
            ctrl = auto.Control(**element_ref)
            if not ctrl.Exists(0, 0):
                return False
            ctrl.SetFocus()
            try:
                ctrl.GetValuePattern().SetValue(text)
            except Exception:
                ctrl.SendKeys(text)
            return True
        except Exception:
            return False

    def focus_element(self, element_ref: Dict) -> bool:
        try:
            ctrl = auto.Control(**element_ref)
            if ctrl.Exists(0, 0):
                ctrl.SetFocus()
                return True
            return False
        except Exception:
            return False

    def select_element(self, element_ref: Dict) -> bool:
        try:
            ctrl = auto.Control(**element_ref)
            if not ctrl.Exists(0, 0):
                return False
            try:
                ctrl.GetSelectionItemPattern().Select()
            except Exception:
                ctrl.Click()
            return True
        except Exception:
            return False

    # --- Physical Actions (Fallback) ---
    def mouse_click(
        self, x: int, y: int, button: str = "left", clicks: int = 1
    ) -> bool:
        try:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            return True
        except Exception:
            return False

    def mouse_drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        try:
            pyautogui.moveTo(start_x, start_y)
            pyautogui.dragTo(end_x, end_y, button="left")
            return True
        except Exception:
            return False

    def mouse_scroll(self, amount: int, direction: str = "down") -> bool:
        try:
            # PyAutoGUI scroll amount can vary by OS, but generally positive is up
            clicks = amount if direction == "up" else -amount
            pyautogui.scroll(clicks)
            return True
        except Exception:
            return False

    def keyboard_type(self, text: str) -> bool:
        try:
            pyautogui.write(text)
            return True
        except Exception:
            return False

    def keyboard_shortcut(self, keys: List[str]) -> bool:
        try:
            pyautogui.hotkey(*keys)
            return True
        except Exception:
            return False
