from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data


@dataclass(frozen=True)
class ToolExecutionAuditEvent:
    event_id: str
    timestamp: str
    actor: str
    channel: str
    request_id: str
    candidate_id: str
    adapter_name: str
    action_type: str
    target_type: str
    target_redacted: str
    risk_level: str
    approval_summary: str
    voice_approval_summary: str
    sandbox_scope: List[str] = field(default_factory=list)
    allowlist_result: bool = False
    denylist_result: bool = False
    rollback_or_stop_plan_summary: str = ""
    external_call_made: bool = False
    filesystem_changed: bool = False
    remote_changed: bool = False
    production_touched: bool = False
    money_moved: bool = False
    secrets_redacted: bool = True
    audit_safe: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_tool_execution_audit_event(**values: Any) -> ToolExecutionAuditEvent:
    safe, _ = redact_sensitive_data(values)
    return ToolExecutionAuditEvent(
        event_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        actor=str(safe.get("actor") or "David"),
        channel=str(safe.get("channel") or "local_api"),
        request_id=str(safe.get("request_id") or "preview-request"),
        candidate_id=str(safe.get("candidate_id") or "preview-candidate"),
        adapter_name=str(safe.get("adapter_name") or "mark_2_tool_execution"),
        action_type=str(safe.get("action_type") or "preview"),
        target_type=str(safe.get("target_type") or "unknown"),
        target_redacted=str(safe.get("target") or "[redacted target]"),
        risk_level=str(safe.get("risk_level") or "medium"),
        approval_summary="valid explicit approval present" if values.get("valid_approval_present") else "approval missing or invalid",
        voice_approval_summary="valid Voice Approval Channel state present" if values.get("valid_voice_approval_present") else "voice approval missing or invalid",
        sandbox_scope=list(safe.get("sandbox_scope") or []),
        allowlist_result=bool(values.get("allowlist_match")),
        denylist_result=bool(values.get("denylist_match")),
        rollback_or_stop_plan_summary=str(safe.get("rollback_or_stop_plan") or "missing"),
    )
