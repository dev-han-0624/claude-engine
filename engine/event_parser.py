import json
import re
import uuid

from engine.interface import ParsedEvent, ToolCallRequest

_TOOL_CALL_PATTERN = re.compile(r"```tool_call\s*\n(.*?)\n```", re.DOTALL)


def parse_stream_event(data: dict) -> list[ParsedEvent]:
    """stream-json 이벤트 하나를 ParsedEvent 리스트로 변환."""
    msg_type = data.get("type", "")
    events = []

    if msg_type == "result":
        result_text = data.get("result", "")
        if result_text:
            events.extend(_parse_text(result_text))

        cost = data.get("total_cost_usd", 0)
        duration = data.get("duration_ms", 0)
        events.append(ParsedEvent(kind="meta", cost=cost, duration=duration))
        events.append(ParsedEvent(kind="done"))

    elif msg_type == "error":
        error = data.get("error", str(data))
        events.append(ParsedEvent(kind="error", text=error))
        events.append(ParsedEvent(kind="done"))

    return events


def _parse_text(text: str) -> list[ParsedEvent]:
    """텍스트에서 ```tool_call``` 블록을 추출. 일반 텍스트와 tool_calls로 분리."""
    parts = _TOOL_CALL_PATTERN.split(text)
    events = []
    tool_calls = []

    for i, part in enumerate(parts):
        if i % 2 == 0:
            cleaned = part.strip()
            if cleaned:
                events.append(ParsedEvent(kind="text", text=cleaned))
        else:
            try:
                data = json.loads(part)
                tool_calls.append(ToolCallRequest(
                    id=data.get("id", str(uuid.uuid4())),
                    name=data["name"],
                    arguments=data.get("input", {}),
                ))
            except (json.JSONDecodeError, KeyError):
                events.append(ParsedEvent(kind="text", text=part))

    if tool_calls:
        events.append(ParsedEvent(kind="tool_calls", tool_calls=tool_calls))

    return events
