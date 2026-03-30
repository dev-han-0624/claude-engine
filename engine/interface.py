from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


# ── 입력: 엔진에 넣는 것 ──

@dataclass
class ToolDef:
    """엔진에 등록할 도구 정의."""
    name: str
    description: str
    input_schema: dict


# ── 출력: 엔진이 내보내는 것 ──

@dataclass
class ToolCallRequest:
    """엔진이 파싱한 도구 호출 요청."""
    id: str
    name: str
    arguments: dict


@dataclass
class ParsedEvent:
    """엔진이 내보내는 이벤트."""
    kind: str  # "text", "tool_calls", "meta", "error", "done"
    text: str | None = None
    tool_calls: list[ToolCallRequest] | None = None
    cost: float = 0
    duration: int = 0


# ── 엔진 인터페이스 ──

class Engine(ABC):
    """Claude CLI 엔진의 공개 인터페이스.

    사용 흐름:
        1. start(tool_defs, on_event) — 프로세스 시작 + 도구 등록
        2. send(message) — 메시지 전송
        3. on_event 콜백으로 ParsedEvent 수신
        4. stop() — 프로세스 종료
    """

    @abstractmethod
    def start(self, tool_defs: list[ToolDef] | None = None,
              on_event: Callable[[ParsedEvent], None] = None,
              system_prompt: str | None = None) -> None:
        pass

    @abstractmethod
    def send(self, message: str) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @property
    @abstractmethod
    def alive(self) -> bool:
        pass
