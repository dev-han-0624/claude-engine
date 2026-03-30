import subprocess
import threading
import json
from typing import Callable

from engine.interface import Engine, ToolDef, ParsedEvent
from engine.prompt import build_tool_prompt
from engine.event_parser import parse_stream_event

_BASE_CMD = [
    "claude", "-p",
    "--input-format", "stream-json",
    "--output-format", "stream-json",
    "--verbose",
]


class ClaudeProcess(Engine):
    """Engine 구현: claude CLI 프로세스의 생명주기를 관리."""

    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._on_event: Callable[[ParsedEvent], None] | None = None
        self._alive = False

    @property
    def alive(self) -> bool:
        return self._alive

    def start(self, tool_defs: list[ToolDef] | None = None,
              on_event: Callable[[ParsedEvent], None] = None,
              system_prompt: str | None = None):
        self._on_event = on_event

        cmd = list(_BASE_CMD)
        if system_prompt:
            cmd += ["--system-prompt", system_prompt]
        tool_prompt = build_tool_prompt(tool_defs) if tool_defs else None
        if tool_prompt:
            cmd += ["--append-system-prompt", tool_prompt]

        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._alive = True
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self):
        for line in self._process.stdout:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                raw = json.loads(line)
                if self._on_event:
                    for event in parse_stream_event(raw):
                        self._on_event(event)
            except json.JSONDecodeError:
                pass
        self._alive = False

    def _read_stderr(self):
        for line in self._process.stderr:
            pass  # stderr 무시

    def send(self, message: str):
        if self._process and self._process.poll() is None:
            msg = json.dumps({
                "type": "user",
                "message": {"role": "user", "content": message},
            })
            self._send_raw(msg)

    def send_tool_result(self, tool_use_id: str, content: str):
        """도구 실행 결과를 claude에게 전달."""
        feedback = json.dumps({
            "type": "user",
            "message": {
                "role": "user",
                "content": json.dumps({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content,
                }, ensure_ascii=False),
            },
        })
        self._send_raw(feedback)

    def _send_raw(self, json_str: str):
        if self._process and self._process.poll() is None:
            try:
                self._process.stdin.write(json_str + "\n")
                self._process.stdin.flush()
            except (OSError, ValueError):
                pass

    def stop(self):
        if self._process and self._process.poll() is None:
            try:
                self._process.stdin.close()
            except OSError:
                pass
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._alive = False
