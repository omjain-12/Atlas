import json
from typing import Optional
from enum import Enum
from pydantic import BaseModel
from .agent_state import TaskStep


class MainLLMResponseType(str, Enum):
    PLAN = "PLAN"
    EVALUATION = "EVALUATION"
    TASK_INTERPRETATION = "TASK_INTERPRETATION"
    VERIFICATION = "VERIFICATION"
    COMPRESSION = "COMPRESSION"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    PARSE_ERROR = "PARSE_ERROR"


class MainLLMResponse(BaseModel):
    type: MainLLMResponseType
    raw: Optional[str] = None
    data: Optional[dict] = None
    reason: Optional[str] = None

    def is_error(self) -> bool:
        return self.type == MainLLMResponseType.PARSE_ERROR


class MainLLMEngine:
    @classmethod
    def decide(cls, prompt: str, response_type: MainLLMResponseType) -> MainLLMResponse:
        try:
            raw = cls.call(prompt)
            return cls.parse_response(raw, response_type)
        except Exception as e:
            return MainLLMResponse(
                type=MainLLMResponseType.PARSE_ERROR, raw=str(e)
            )

    @classmethod
    def parse_response(cls, raw: str, expected_type: MainLLMResponseType) -> MainLLMResponse:
        try:
            data = json.loads(raw)
            return MainLLMResponse(type=expected_type, raw=raw, data=data)
        except json.JSONDecodeError:
            return MainLLMResponse(
                type=MainLLMResponseType.PARSE_ERROR, raw=raw
            )

    @classmethod
    def call(cls, prompt: str) -> str:
        raise NotImplementedError(
            "MainLLMEngine.call must be implemented or mocked."
        )
