import subprocess
import uiautomation as auto
from typing import Dict


class ApplicationTools:
    def launch_application(self, path_or_uri: str) -> bool:
        try:
            subprocess.Popen(path_or_uri, shell=True)
            return True
        except Exception:
            return False

    def focus_window(self, window_ref: Dict) -> bool:
        try:
            win = auto.WindowControl(searchDepth=1, **window_ref)
            if win.Exists(0, 0):
                win.SetFocus()
                return True
            return False
        except Exception:
            return False

    def close_window(self, window_ref: Dict) -> bool:
        try:
            win = auto.WindowControl(searchDepth=1, **window_ref)
            if win.Exists(0, 0):
                win.GetWindowPattern().Close()
                return True
            return False
        except Exception:
            return False

    def resize_window(self, window_ref: Dict, width: int, height: int) -> bool:
        try:
            win = auto.WindowControl(searchDepth=1, **window_ref)
            if win.Exists(0, 0):
                win.GetTransformPattern().Resize(width, height)
                return True
            return False
        except Exception:
            return False

    def move_window(self, window_ref: Dict, x: int, y: int) -> bool:
        try:
            win = auto.WindowControl(searchDepth=1, **window_ref)
            if win.Exists(0, 0):
                win.GetTransformPattern().Move(x, y)
                return True
            return False
        except Exception:
            return False
