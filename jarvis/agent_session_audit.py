from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class AuditTimelineEvent:
    event_id: str
    timestamp: str
    actor: str
    channel: str
    event_type: str
    summary: str
    risk_level: str
    approval_state: str
    tool_or_agent: str
    redaction_applied: bool = True
    safe_to_render: bool = True
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "Inspect the safe summary and retain audit controls."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_audit_timeline() -> List[AuditTimelineEvent]:
    return [
        AuditTimelineEvent(
            event_id="macro-3-dashboard-ready",
            timestamp="not_recorded",
            actor="JARVIS",
            channel="system",
            event_type="control_plane_snapshot",
            summary="Mark 2 Macro 3 dashboard data model is available; no real agent or tool was invoked.",
            risk_level="low",
            approval_state="not_required",
            tool_or_agent="VisualCommandCenter",
        )
    ]

