"""Generic stage-failure taxonomy (impl plan §3.4). Exactly these seven kinds; runtime-LLM
calls use their own transport_error/invalid_output taxonomy (§2.4), not this one."""
from __future__ import annotations

from enum import StrEnum


class FailureKind(StrEnum):
    TRANSIENT = "TRANSIENT"
    PERMANENT_INPUT = "PERMANENT_INPUT"
    PERMANENT_MODEL = "PERMANENT_MODEL"
    PERMANENT_VALIDATION = "PERMANENT_VALIDATION"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    BLOCKED_BY_DEPENDENCY = "BLOCKED_BY_DEPENDENCY"


class StageFailure(Exception):
    def __init__(self, kind: FailureKind, reason: str, detail: str = ""):
        self.kind, self.reason, self.detail = kind, reason, detail
        super().__init__(f"{kind}:{reason}" + (f" ({detail})" if detail else ""))


class BlockedBySpec(Exception):
    """A step that cannot be implemented without inventing something neither source document
    specifies. Deliberately NOT a FailureKind: it is a build-time stop-and-ask signal, never a
    runtime job outcome (README standing rule)."""
