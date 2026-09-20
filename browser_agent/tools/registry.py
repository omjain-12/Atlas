from typing import Any, Dict, Callable
from .core_tools import CoreTools
from .interaction_tools import InteractionTools
from .tab_tools import TabTools
from .inspection_tools import InspectionTools
from .escape_tools import EscapeTools

# Note: Assuming ToolCall, ToolResult, ExecutionError, ErrorType are available in models
# For this scaffold, we'll mock them or import them if available
try:
    from ..models import ToolCall, ToolResult, ExecutionError, ErrorType
except ImportError:
    class ToolCall:
        tool_name: str
        arguments: dict

    class ToolResult:
        def __init__(self, success, output=None, error=None, execution_method=None):
            self.success = success
            self.output = output
            self.error = error
            self.execution_method = execution_method

    class ExecutionError:
        def __init__(self, type, message):
            self.type = type
            self.message = message
            
    class ErrorType:
        VALIDATION_ERROR = "VALIDATION_ERROR"
        SYSTEM_ERROR = "SYSTEM_ERROR"

class BrowserToolRegistry:
    def __init__(self):
        self.core_tools = CoreTools()
        self.interact_tools = InteractionTools()
        self.tab_tools = TabTools()
        self.inspect_tools = InspectionTools()
        self.escape_tools = EscapeTools()

        self.tools: Dict[str, Callable] = {}
        self._register_tools(self.core_tools)
        self._register_tools(self.interact_tools)
        self._register_tools(self.tab_tools)
        self._register_tools(self.inspect_tools)
        self._register_tools(self.escape_tools)

    def _register_tools(self, tool_group: Any):
        for attr_name in dir(tool_group):
            if not attr_name.startswith("_"):
                method = getattr(tool_group, attr_name)
                if callable(method):
                    self.tools[attr_name] = method

    def execute(self, tool_call: ToolCall) -> ToolResult:
        if tool_call.tool_name not in self.tools:
            return ToolResult(
                success=False,
                error=ExecutionError(
                    type=ErrorType.VALIDATION_ERROR,
                    message=f"Tool {tool_call.tool_name} not found in registry.",
                ),
            )

        tool_fn = self.tools[tool_call.tool_name]
        try:
            output = tool_fn(**tool_call.arguments)
            return ToolResult(
                success=True, output=output, execution_method=tool_call.tool_name
            )
        except TypeError as e:
            return ToolResult(
                success=False,
                error=ExecutionError(
                    type=ErrorType.VALIDATION_ERROR,
                    message=f"Invalid arguments for {tool_call.tool_name}: {str(e)}",
                ),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=ExecutionError(
                    type=ErrorType.SYSTEM_ERROR,
                    message=f"Error executing {tool_call.tool_name}: {str(e)}",
                ),
            )
