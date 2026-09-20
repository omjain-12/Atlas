import json
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from pydantic import BaseModel
from .models import ToolCall, ExecutionError, ErrorType


class LLMResponseType(str, Enum):
    TOOL_CALL = "TOOL_CALL"
    MILESTONE_SATISFIED = "MILESTONE_SATISFIED"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    PARSE_ERROR = "PARSE_ERROR"


class LLMResponse(BaseModel):
    type: LLMResponseType
    raw: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    intent: Optional[str] = None
    evidence: Optional[str] = None
    reason: Optional[str] = None


class LLMEngine:
    """
    Interface for LLM calls. In a real system, this would wrap LangChain, OpenAI, etc.
    """

    @classmethod
    def decide(cls, context: str) -> LLMResponse:
        """
        Takes the constructed context prompt and returns a typed LLMResponse.
        """
        try:
            raw = cls.call(context)
            return cls.parse_response(raw)
        except Exception as e:
            return LLMResponse(type=LLMResponseType.PARSE_ERROR, raw=str(e))

    @classmethod
    def parse_response(cls, raw: str) -> LLMResponse:
        """
        Mock implementation of response parsing.
        Expects JSON string for simplicity in this implementation.
        """
        try:
            data = json.loads(raw)
            if "tool_call" in data:
                return LLMResponse(
                    type=LLMResponseType.TOOL_CALL,
                    tool_call=ToolCall(**data["tool_call"]),
                    intent=data.get("intent", ""),
                )
            elif "milestone_satisfied" in data:
                return LLMResponse(
                    type=LLMResponseType.MILESTONE_SATISFIED,
                    evidence=data.get("evidence", ""),
                )
            elif "needs_human" in data:
                return LLMResponse(
                    type=LLMResponseType.NEEDS_HUMAN, reason=data.get("reason", "")
                )
            else:
                return LLMResponse(type=LLMResponseType.PARSE_ERROR, raw=raw)
        except json.JSONDecodeError:
            return LLMResponse(type=LLMResponseType.PARSE_ERROR, raw=raw)

    @classmethod
    def call(cls, prompt: str) -> str:
        """
        Raw LLM call (placeholder).
        """
        raise NotImplementedError("LLMEngine.call must be implemented or mocked.")
