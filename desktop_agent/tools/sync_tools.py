import time
import uiautomation as auto
from typing import Dict


class SyncTools:
    def wait_for_time(self, milliseconds: int) -> bool:
        time.sleep(milliseconds / 1000.0)
        return True

    def wait_until(self, condition_type: str, target: Dict, timeout: int = 10) -> bool:
        try:
            if "window" in condition_type:
                ctrl = auto.WindowControl(searchDepth=1, **target)
            else:
                ctrl = auto.Control(**target)

            if condition_type.endswith("appears"):
                return ctrl.Exists(timeout, 0.5)
            elif condition_type.endswith("disappears"):
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if not ctrl.Exists(0, 0):
                        return True
                    time.sleep(0.5)
                return False
            return False
        except Exception:
            return False
