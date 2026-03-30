# claude-engine

Claude CLI(`claude -p`)를 상주 프로세스로 관리하는 독립 엔진 라이브러리.

## 설치

```bash
pip install git+https://github.com/dev-han-0624/claude-engine.git
```

## 전제 조건

- Python >= 3.11
- `claude` CLI가 PATH에 설치되어 있어야 함
- 외부 의존성 없음 (stdlib만 사용)

## 공개 인터페이스

`engine/interface.py`에 정의. 이 파일만 보면 사용법을 알 수 있다.

### 입력 (엔진에 넣는 것)

- `ToolDef(name, description, input_schema)` — 커스텀 도구 정의

### 출력 (엔진이 내보내는 것)

- `ToolCallRequest(id, name, arguments)` — 도구 호출 요청
- `ParsedEvent(kind, text, tool_calls, cost, duration)` — 이벤트 스트림
  - kind: `"text"`, `"tool_calls"`, `"meta"`, `"error"`, `"done"`

### Engine ABC

```python
class Engine(ABC):
    def start(tool_defs, on_event) -> None   # 프로세스 시작 + 도구 등록 + 콜백
    def send(message) -> None                # 메시지 전송
    def stop() -> None                       # 프로세스 종료
    alive: bool                              # 프로세스 상태
```

### ClaudeProcess (Engine 구현체)

추가 메서드:
- `send_tool_result(tool_use_id, content)` — 도구 실행 결과를 claude에게 전달

## 사용 예시

```python
from engine import ClaudeProcess, ToolDef, ParsedEvent

def on_event(event: ParsedEvent):
    if event.kind == "text":
        print(event.text)
    elif event.kind == "tool_calls":
        for tc in event.tool_calls:
            print(f"도구 호출: {tc.name}({tc.arguments})")
    elif event.kind == "done":
        print("응답 완료")

engine = ClaudeProcess()
engine.start(
    tool_defs=[
        ToolDef(
            name="get_time",
            description="현재 시간 반환",
            input_schema={"type": "object", "properties": {}, "required": []},
        )
    ],
    on_event=on_event,
)
engine.send("안녕")
# on_event 콜백으로 ParsedEvent 수신
engine.stop()
```

## 내부 구조

| 파일 | 역할 |
|------|------|
| `interface.py` | 공개 인터페이스 (Engine ABC, 데이터 타입) |
| `claude_process.py` | Engine 구현체 (subprocess 생명주기) |
| `event_parser.py` | stream-json 이벤트 파싱 + tool_call 블록 추출 |
| `prompt.py` | 커스텀 도구 프롬프트 생성 |

## 동작 방식

- `claude -p --input-format stream-json --output-format stream-json --verbose`로 프로세스 상주
- 커스텀 도구: `--append-system-prompt`로 도구 정의 주입 → 텍스트 내 ` ```tool_call``` ` 블록으로 호출 요청
- Claude 내장 도구(Read, Bash 등)도 동시 사용 가능 (LLM이 판단)
- stdout/stderr 각각 데몬 쓰레드에서 읽기 (blocking I/O 분리)
