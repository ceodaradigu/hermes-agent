from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.approval_bridge import MissionApprovalBridgeDecision, MissionApprovalBridgePayload


class MissionApprovalHardeningDecision(str, Enum):
    ALLOWED_PREPARE_ONLY = "allowed_prepare_only"
    REQUIRES_REVIEW = "requires_review"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MissionApprovalHardeningResult:
    result_id: str
    payload_id: Optional[str]
    mission_id: Optional[str]
    decision: MissionApprovalHardeningDecision
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    audit_summary: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision", _coerce_enum(MissionApprovalHardeningDecision, self.decision, "decision"))
        object.__setattr__(self, "errors", _list_from(self.errors))
        object.__setattr__(self, "warnings", _list_from(self.warnings))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionApprovalHardeningResult":
        return cls(
            result_id=str(data.get("result_id", "")),
            payload_id=data.get("payload_id"),
            mission_id=data.get("mission_id"),
            decision=data.get("decision", ""),
            is_valid=bool(data.get("is_valid", False)),
            errors=_list_from(data.get("errors")),
            warnings=_list_from(data.get("warnings")),
            audit_summary=str(data.get("audit_summary", "")),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "payload_id": self.payload_id,
            "mission_id": self.mission_id,
            "decision": self.decision.value,
            "is_valid": self.is_valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "audit_summary": self.audit_summary,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


def harden_approval_bridge_payload(
    payload: MissionApprovalBridgePayload,
    *,
    evaluator: str = "jarvis",
) -> MissionApprovalHardeningResult:
    if not isinstance(payload, MissionApprovalBridgePayload):
        raise ValueError("payload must be a MissionApprovalBridgePayload")

    errors: List[str] = []
    warnings: List[str] = []
    text = _combined_text(payload)
    strong = payload.strong_approval_required or payload.decision == MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL

    if strong and not payload.challenge_required:
        errors.append("strong approval requires challenge_required=true")
    if strong and not payload.scope:
        errors.append("strong approval requires non-empty scope")
    if strong and not _is_non_empty_string(payload.expires_at):
        errors.append("strong approval requires expires_at")
    if strong and not _is_exact_action(payload.action):
        errors.append("strong approval requires an exact action")
    if _contains_any(text, _BLANKET_APPROVAL_PHRASES):
        errors.append("approve-all-forever or blanket approval language is blocked")
    if any(_contains_any(_normalize(item), _UNLIMITED_SCOPE_TERMS) for item in payload.scope):
        errors.append("unlimited scope is blocked")
    duration = _normalize(str(payload.metadata.get("duration", "")))
    if duration and _contains_any(duration, _UNLIMITED_DURATION_TERMS):
        errors.append("forever or unlimited duration is blocked")
    if _has_cost(payload) and payload.metadata.get("max_cost") is None and payload.metadata.get("cost_limit") is None:
        errors.append("payload with cost requires max_cost or cost_limit")
    if _contains_any(text, _PRODUCTION_PUBLICATION_TERMS) and not (
        _is_non_empty_string(str(payload.metadata.get("rollback_plan", ""))) or _is_non_empty_string(payload.blocked_reason)
    ):
        errors.append("deploy, production, or publication payload requires rollback_plan or blocked_reason")
    if payload.metadata.get("trusted_device") is True and not payload.metadata.get("trusted_device_id"):
        warnings.append("trusted_device requires explicit trusted_device_id before it can be trusted")

    decision = MissionApprovalHardeningDecision.ALLOWED_PREPARE_ONLY
    if errors:
        decision = MissionApprovalHardeningDecision.BLOCKED
    elif warnings:
        decision = MissionApprovalHardeningDecision.REQUIRES_REVIEW

    return MissionApprovalHardeningResult(
        result_id=str(uuid4()),
        payload_id=payload.payload_id,
        mission_id=payload.mission_id,
        decision=decision,
        is_valid=not errors,
        errors=errors,
        warnings=warnings,
        audit_summary=(
            f"Approval payload hardening checked payload {payload.payload_id}: decision={decision.value}; "
            "no approval, ApprovalGateway call, or execution occurred."
        ),
        created_at=_now_iso(),
        metadata={"evaluator": evaluator or "jarvis", "approval_gateway_called": False, "prepare_only": True},
    )


def _combined_text(payload: MissionApprovalBridgePayload) -> str:
    values = [
        payload.action,
        payload.reason,
        payload.scope,
        payload.blocked_reason,
        payload.policy_notes,
        payload.audit_summary,
        payload.metadata,
    ]
    return _normalize(" ".join(_flatten_text(values)))


def _flatten_text(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        items: List[str] = []
        for key, item in value.items():
            items.append(str(key))
            items.extend(_flatten_text(item))
        return items
    if isinstance(value, list):
        items: List[str] = []
        for item in value:
            items.extend(_flatten_text(item))
        return items
    return [str(value)]


def _has_cost(payload: MissionApprovalBridgePayload) -> bool:
    cost_keys = {"cost", "estimated_cost", "proposed_cost", "projected_cost", "confirmed_cost"}
    return any(key in payload.metadata and payload.metadata.get(key) is not None for key in cost_keys)


def _is_exact_action(action: Optional[str]) -> bool:
    normalized = _normalize(action)
    if not normalized:
        return False
    return not _contains_any(normalized, {"anything", "whatever", "all actions", "all_actions", "*"})


def _contains_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def _coerce_enum(enum_type, value: Any, field_name: str):
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid {enum_type.__name__}") from exc


def _list_from(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _is_non_empty_string(value: Optional[str]) -> bool:
    return bool((value or "").strip())


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_BLANKET_APPROVAL_PHRASES = {
    "approve_all_forever",
    "approve all forever",
    "do_anything",
    "unlimited",
    "no_limits",
    "whatever_it_takes",
    "haz_todo_lo_necesario_sin_limites",
}
_UNLIMITED_SCOPE_TERMS = {"*", "all", "everything", "unlimited", "global", "forever"}
_UNLIMITED_DURATION_TERMS = {"forever", "unlimited", "no expiry", "never expires", "permanent"}
_PRODUCTION_PUBLICATION_TERMS = {"deploy", "production", "publish", "publicacion", "publication", "release"}
