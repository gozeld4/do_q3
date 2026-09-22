from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

EvaluationReason = Literal["user_override", "global"]


@dataclass(frozen=True)
class EvaluationResult:
    enabled: bool
    reason: EvaluationReason


def evaluate_flag(
    *,
    global_enabled: bool,
    override_enabled: bool | None,
) -> EvaluationResult:
    if override_enabled is not None:
        return EvaluationResult(
            enabled=override_enabled,
            reason="user_override",
        )
    return EvaluationResult(enabled=global_enabled, reason="global")
