import time
from typing import Dict


class SyncTools:
    def wait_for_time(self, milliseconds: int) -> bool:
        time.sleep(milliseconds / 1000.0)
        return True

    def wait_until(self, condition_type: str, target: Dict, timeout: int = 10) -> bool:
        # condition_type: "element_appears", "element_disappears", "window_appears", etc.
        # Stub implementation
        time.sleep(min(1.0, timeout))
        return True
