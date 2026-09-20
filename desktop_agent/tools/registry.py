from typing import Any, Dict, Callable
from ..models import ToolCall, ToolResult, ExecutionError, ErrorType
from .observation_tools import ObservationTools
from .interaction_tools import InteractionTools
from .application_tools import ApplicationTools
from .system_tools import SystemTools
from .sync_tools import SyncTools


class ToolRegistry:
    def __init__(self):
        self.obs_tools = ObservationTools()
        self.interact_tools = InteractionTools()
        self.app_tools = ApplicationTools()
        self.system_tools = SystemTools()
        self.sync_tools = SyncTools()

        self.tools: Dict[str, Callable] = {}
        self._register_tools(self.obs_tools)
        self._register_tools(self.interact_tools)
        self._register_tools(self.app_tools)
        self._register_tools(self.system_tools)
        self._register_tools(self.sync_tools)

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
            # Check policy here in a real implementation
            # Example: if tool_call.tool_name == "run_powershell": PolicyLayer.check(...)

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
