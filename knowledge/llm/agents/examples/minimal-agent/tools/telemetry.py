# tools/telemetry.py

import json
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class EventSink(Protocol):
    def emit(self, event: Dict[str, Any]) -> None: ...


@dataclass
class StdoutJsonSink:
    """
    Default sink: print one-line JSON per event.
    """

    def emit(self, event: Dict[str, Any]) -> None:
        print(json.dumps(event, ensure_ascii=False))


class Telemetry:
    def __init__(
        self, sink: Optional[EventSink] = None, *, service_name: str = "minimal_agent"
    ):
        self.sink = sink or StdoutJsonSink()
        self.service_name = service_name

    def new_trace_id(self) -> str:
        return uuid.uuid4().hex

    def new_span_id(self) -> str:
        # span id 不需要是 uuid，短一点更适合日志
        return uuid.uuid4().hex[:16]

    def emit(self, event_type: str, payload: Dict[str, Any]) -> None:
        event = {
            "ts_ms": int(time.time() * 1000),
            "service": self.service_name,
            "type": event_type,
            **payload,
        }
        self.sink.emit(event)

    def start_span(
        self,
        span_type: str,
        *,
        trace_id: str,
        name: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> "Span":
        span_id = self.new_span_id()
        span = Span(
            telemetry=self,
            span_type=span_type,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            attributes=attributes or {},
        )
        span.start()
        return span


class Span:
    """
    Minimal tracing span:
    - emits <span_type>.start and <span_type>.end
    - records start time, computes latency
    - end() accepts outcome fields (ok/error_code/extra)
    """

    def __init__(
        self,
        telemetry: Telemetry,
        *,
        span_type: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str],
        name: str,
        attributes: Dict[str, Any],
    ):
        self.telemetry = telemetry
        self.span_type = span_type
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.name = name
        self.attributes = attributes
        self._t0: Optional[float] = None

    def start(self) -> None:
        self._t0 = time.time()
        self.telemetry.emit(
            f"{self.span_type}.start",
            {
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "parent_span_id": self.parent_span_id,
                "name": self.name,
                **self.attributes,
            },
        )

    def end(
        self,
        *,
        ok: bool,
        error_code: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        t1 = time.time()
        latency_ms = int(((t1 - (self._t0 or t1)) * 1000))
        payload = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "ok": ok,
            "error_code": error_code,
            "latency_ms": latency_ms,
            **self.attributes,
        }
        if extra:
            payload.update(extra)
        self.telemetry.emit(f"{self.span_type}.end", payload)

    # 让 Span 能用 with 语法（即使你不用也没事）
    def __enter__(self) -> "Span":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # 如果异常没被 end() 捕获，兜底记录
        if exc is not None:
            self.end(
                ok=False, error_code="SPAN_EXCEPTION", extra={"exception": str(exc)}
            )
        return False
