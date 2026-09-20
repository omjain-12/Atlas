import os
import tempfile
import uiautomation as auto
import pyautogui
import pyperclip
from typing import Tuple, List, Dict, Optional
from ..models import WindowRef, UIState, UIElement, ElementRef


class ObservationTools:
    def get_screenshot(self, target: str = "full") -> str:
        path = os.path.join(tempfile.gettempdir(), "desktop_screenshot.png")
        try:
            if target == "full":
                pyautogui.screenshot(path)
            else:
                active = pyautogui.getActiveWindow()
                if active:
                    pyautogui.screenshot(
                        path,
                        region=(active.left, active.top, active.width, active.height),
                    )
                else:
                    pyautogui.screenshot(path)
        except Exception:
            pyautogui.screenshot(path)
        return path

    def get_ui_tree(self) -> UIState:
        try:
            win = auto.GetForegroundControl()
            active_win_ref = WindowRef(title=win.Name)
            ui_state = UIState(active_window=active_win_ref, windows=[active_win_ref])

            def traverse(ctrl, depth=0):
                # Limit depth to avoid massive UI trees freezing the agent
                if depth > 4:
                    return
                for child in ctrl.GetChildren():
                    ref = ElementRef(
                        name=child.Name, control_type=child.ControlTypeName
                    )
                    elem = UIElement(
                        ref=ref,
                        is_enabled=child.IsEnabled,
                        is_focused=child.HasKeyboardFocus,
                    )
                    ui_state.tree.append(elem)
                    traverse(child, depth + 1)

            traverse(win)
            return ui_state
        except Exception:
            return UIState()

    def get_active_window_info(self) -> WindowRef:
        try:
            win = auto.GetForegroundControl()
            return WindowRef(title=win.Name)
        except Exception:
            return WindowRef(title="Desktop")

    def list_all_windows(self) -> List[WindowRef]:
        try:
            windows = []
            for win in auto.GetRootControl().GetChildren():
                if win.ControlType == auto.ControlType.WindowControl:
                    windows.append(WindowRef(title=win.Name))
            return windows
        except Exception:
            return []

    def get_cursor_position(self) -> Tuple[int, int]:
        try:
            x, y = pyautogui.position()
            return (x, y)
        except Exception:
            return (0, 0)

    def get_clipboard_content(self) -> str:
        try:
            return pyperclip.paste()
        except Exception:
            return ""
