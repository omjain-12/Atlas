from typing import Dict


class ApplicationTools:
    def launch_application(self, path_or_uri: str) -> bool:
        return True

    def focus_window(self, window_ref: Dict) -> bool:
        return True

    def close_window(self, window_ref: Dict) -> bool:
        return True

    def resize_window(self, window_ref: Dict, width: int, height: int) -> bool:
        return True

    def move_window(self, window_ref: Dict, x: int, y: int) -> bool:
        return True
