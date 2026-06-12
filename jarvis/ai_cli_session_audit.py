from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data


@dataclass(frozen=True)
class ExternalOperationAuditEvent:
    event_id: str
    timestamp: str
    actor: str
    channel: str
    operation_type: str
    provider: str
    target_summary_redacted: str
    risk_level: str
    approval_summary: str
    voice_approval_summary: str
    cost_summary: str
    access_material_summary: str
    network_summary: str
    production_impact_summary: str
    money_impact_summary: str
    rollback_or_stop_plan_summary: str
    adapter_used: str
    executed: bool = False
    external_call_made: bool = False
    money_moved: bool = False
    production_touched: bool = False
    secrets_redacted: bool = True
    audit_safe: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_external_operation_audit_event(**values: Any) -> ExternalOperationAuditEvent:
    safe, _ = redact_sensitive_data(values)
    return ExternalOperationAuditEvent(
        event_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        actor=str(safe.get("actor") or "David"),
        channel=str(safe.get("channel") or "local_api"),
        operation_type=str(safe.get("operation_type") or "preview"),
        provider=str(safe.get("provider") or "unknown"),
        target_summary_redacted=str(safe.get("target_summary") or "[redacted target summary]"),
        risk_level=str(safe.get("risk_level") or "medium"),
        approval_summary="valid approval present" if values.get("valid_approval_present") else "approval missing or invalid",
        voice_approval_summary="valid Voice Approval Channel state present" if values.get("valid_voice_approval_present") else "voice approval missing or invalid",
        cost_summary=str(safe.get("cost_summary") or "unknown; no billing queried"),
        access_material_summary="manual handoff required; none stored",
        network_summary="external call not made",
        production_impact_summary="production not touched",
        money_impact_summary="money not moved",
        rollback_or_stop_plan_summary=str(safe.get("rollback_or_stop_plan") or "stop before execution"),
        adapter_used=str(safe.get("adapter_used") or "Mark 2 Macro 4 preview"),
    )
