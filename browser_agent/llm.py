import json
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from .models import ToolCall


class LLMResponseType(str, Enum):
    TOOL_CALL = "TOOL_CALL"
    MILESTONE_SATISFIED = "MILESTONE_SATISFIED"
    MILESTONE_FAILED = "MILESTONE_FAILED"
    NEEDS_REPLANNING = "NEEDS_REPLANNING"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    PARSE_ERROR = "PARSE_ERROR"


class LLMResponse(BaseModel):
    type: LLMResponseType
    raw: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    intent: Optional[str] = None
    evidence: Optional[str] = None
    reason: Optional[str] = None
    
    def is_tool_call(self):
        return self.type == LLMResponseType.TOOL_CALL
        
    def is_milestone_satisfied(self):
        return self.type == LLMResponseType.MILESTONE_SATISFIED
        
    def is_milestone_failed(self):
        return self.type == LLMResponseType.MILESTONE_FAILED
        
    def needs_replanning(self):
        return self.type in (LLMResponseType.NEEDS_REPLANNING, LLMResponseType.MILESTONE_FAILED)


class LLMEngine:
    @classmethod
    def decide(cls, context: str) -> LLMResponse:
        try:
            raw = cls.call(context)
            return cls.parse_response(raw)
        except Exception as e:
            return LLMResponse(type=LLMResponseType.PARSE_ERROR, raw=str(e))

    @classmethod
    def parse_response(cls, raw: str) -> LLMResponse:
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
            elif "needs_replanning" in data or "milestone_failed" in data:
                return LLMResponse(
                    type=LLMResponseType.NEEDS_REPLANNING,
                    reason=data.get("reason", "Unknown failure reason"),
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
        raise NotImplementedError("LLMEngine.call must be implemented or mocked.")
