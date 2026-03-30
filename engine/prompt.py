import json

from engine.interface import ToolDef

CUSTOM_TOOL_PROMPT = """## 추가 도구

아래 커스텀 도구가 필요하면, 텍스트 응답에 다음 JSON 블록을 포함하세요.
Claude 내장 도구(Read, Bash 등)와 자유롭게 조합해서 사용할 수 있습니다.

호출 형식 (반드시 이 형식을 지켜주세요):
```tool_call
{{"id": "고유ID", "name": "도구이름", "input": {{"param": "value"}}}}
```

### 사용 가능한 커스텀 도구

{tool_definitions}"""


def build_tool_prompt(tool_defs: list[ToolDef]) -> str | None:
    """도구 정의 리스트로 시스템 프롬프트를 생성. 비어있으면 None."""
    if not tool_defs:
        return None

    parts = []
    for d in tool_defs:
        params = json.dumps(d.input_schema, ensure_ascii=False, indent=2)
        parts.append(f"- {d.name}: {d.description}\n  파라미터: {params}")

    return CUSTOM_TOOL_PROMPT.format(tool_definitions="\n".join(parts))
