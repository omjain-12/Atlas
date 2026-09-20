from typing import List, Optional
from .models import ActionRecord


class LoopGuard:
    @staticmethod
    def detect_loop(history: List[ActionRecord]) -> Optional[str]:
        if len(history) < 3:
            return None

        recent = history[-3:]
        # Simple loop detection: same tool call repeated 3 times
        if (
            recent[0].tool_call.tool_name
            == recent[1].tool_call.tool_name
            == recent[2].tool_call.tool_name
            and recent[0].tool_call.arguments
            == recent[1].tool_call.arguments
            == recent[2].tool_call.arguments
        ):
            return "Repeating exact same action"

        return None
