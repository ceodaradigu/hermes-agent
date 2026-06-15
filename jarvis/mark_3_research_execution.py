from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4


SUPPORTED_SOURCE_TYPES = {"github", "web", "docs", "local_repo"}
EXTERNAL_SOURCE_TYPES = {"github", "web"}
APPROVAL_LEVELS = ("direct", "simple", "strong", "double", "triple")
CAPABILITY_BY_SOURCE = {
    "github": "github_research",
    "web": "web_research",
    "docs": "docs_research",
    "local_repo": "local_repo_research",
}
PUBLIC_REQUEST_FIELDS = ("source_type", "source", "query", "topic", "scope", "risk_level", "risk", "goal")
APPROVAL_INPUT_FIELDS = (
    "approval_valid",
    "approval_level",
    "authorized",
    "authorization_valid",
    "stronger_approval_channel_connected",
)


@dataclass(frozen=True)
class ResearchExecutionRecord:
    research_id: str
    created_at: str
    mode: str
    safe_snapshot: Dict[str, Any]
    policy: Dict[str, Any]
    full_request_stored: bool = False
    stored_snapshot_revalidatable: bool = False
    raw_request_stored: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchExecutionAuditEvent:
    event_id: str
    event_type: str
    created_at: str
    research_id: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    safe_to_execute: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def normalize_research_request(values: Optional[Mapping[str, Any]] = None, **overrides: Any) -> Dict[str, Any]:
    """Normalize only the request fields that are safe to classify and snapshot."""

    raw = _merge_values(values, overrides)
    source_type = _normalize_source_type(_first_present(raw.get("source_type"), raw.get("source")))
    query = _text(_first_present(raw.get("query"), raw.get("topic")))
    topic = query
    scope = _text(raw.get("scope"))
    goal = _text(raw.get("goal")) or "research"
    risk_seed_text = _risk_text({
        "source_type": source_type,
        "query": query,
        "topic": topic,
        "scope": scope,
        "goal": goal,
    })
    risk_level = _risk_level(_first_present(raw.get("risk_level"), raw.get("risk")), risk_seed_text)

    safe_query, query_redacted = _redact_text(query)
    safe_topic = safe_query
    safe_scope, scope_redacted = _redact_text(scope)
    safe_goal, goal_redacted = _redact_text(goal)
    redacted_fields = []
    if query_redacted:
        redacted_fields.extend(["query", "topic"])
    if scope_redacted:
        redacted_fields.append("scope")
    if goal_redacted:
        redacted_fields.append("goal")

    safe_fields = {
        "source_type": source_type,
        "source": source_type,
        "query": safe_query,
        "topic": safe_topic,
        "scope": safe_scope,
        "risk_level": risk_level,
        "risk": risk_level,
        "goal": safe_goal,
    }
    fingerprint = _fingerprint(safe_fields)
    safe_snapshot = {
        **safe_fields,
        "fingerprint": fingerprint,
        "redacted_fields": list(dict.fromkeys(redacted_fields)),
        "safe_to_revalidate_for_execution": False,
    }
    return {
        "source_type": source_type,
        "query": query,
        "topic": topic,
        "scope": scope,
        "risk_level": risk_level,
        "goal": goal,
        "fingerprint": fingerprint,
        "safe_snapshot": safe_snapshot,
        "risk_text": _risk_text({
            "source_type": source_type,
            "query": query,
            "topic": topic,
            "scope": scope,
            "risk_level": risk_level,
            "goal": goal,
        }),
        "risk_text_fields": ["source_type", "query", "topic", "scope", "risk_level", "goal"],
        "absent_fields": _absent_fields(raw),
        "redacted_fields": list(dict.fromkeys(redacted_fields)),
    }


def evaluate_research_policy(values: Optional[Mapping[str, Any]] = None, **overrides: Any) -> Dict[str, Any]:
    raw = _merge_values(values, overrides)
    normalized = normalize_research_request(raw)
    risk_text = normalized["risk_text"].lower()
    source_type = normalized["source_type"]
    source_supported = source_type in SUPPORTED_SOURCE_TYPES
    secret_requested = _has_marker(risk_text, SECRET_MARKERS) or _contains_sensitive_request_material(raw)
    illegal_requested = _has_marker(risk_text, ILLEGAL_MARKERS)
    unsafe_requested = _has_marker(risk_text, UNSAFE_MARKERS)
    authorized = _authorized(raw)
    sensitive_actions = _sensitive_actions(risk_text)
    risk_level = _promoted_risk(normalized["risk_level"], sensitive_actions)
    required_approval_level = _required_approval_level(source_type, risk_level, sensitive_actions)
    approval_required = required_approval_level != "direct"
    supplied_approval_level = _normalized_choice(raw.get("approval_level"), set(APPROVAL_LEVELS), "direct")
    stronger_channel_connected = _truthy(raw.get("stronger_approval_channel_connected", False))
    permanent_denial = bool(secret_requested or illegal_requested or unsafe_requested or not authorized or not source_supported)

    blocked_reasons: List[str] = []
    if secret_requested:
        blocked_reasons.append("secret_or_credential_request_blocked")
    if illegal_requested:
        blocked_reasons.append("illegal_request_blocked")
    if unsafe_requested:
        blocked_reasons.append("unsafe_request_blocked")
    if not authorized:
        blocked_reasons.append("authorization_missing")
    if not source_supported:
        blocked_reasons.append("source_type_unsupported")

    setup_reasons = ["capability_not_connected_yet", "setup_required"]
    if source_type in EXTERNAL_SOURCE_TYPES:
        blocked_reasons.append("external_network_requires_approval")
    if required_approval_level in {"double", "triple"} and not stronger_channel_connected:
        setup_reasons.append("stronger_approval_channel_not_connected")
    for action in sensitive_actions:
        blocked_reasons.append(f"{action}_requires_{required_approval_level}_approval")

    approval_valid = _approval_satisfied(
        approval_required=approval_required,
        required_level=required_approval_level,
        supplied_level=supplied_approval_level,
        approval_valid=_truthy(raw.get("approval_valid", False)),
        stronger_channel_connected=stronger_channel_connected,
    )

    if permanent_denial:
        candidate_state = "blocked"
        capability_status = "blocked_by_policy"
    else:
        candidate_state = "setup_required"
        capability_status = "capability_not_connected_yet"
        blocked_reasons.extend(setup_reasons)

    return {
        "source_type": source_type,
        "source": source_type,
        "query": normalized["safe_snapshot"]["query"],
        "topic": normalized["safe_snapshot"]["topic"],
        "scope": normalized["safe_snapshot"]["scope"],
        "risk_level": risk_level,
        "goal": normalized["safe_snapshot"]["goal"],
        "fingerprint": normalized["fingerprint"],
        "candidate_state": candidate_state,
        "execution_status": candidate_state,
        "approval_required": approval_required,
        "requires_approval": approval_required,
        "required_approval_level": required_approval_level,
        "approval_valid": approval_valid,
        "capability": CAPABILITY_BY_SOURCE.get(source_type, "unsupported_research_source"),
        "capability_status": capability_status,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "can_become_executable_candidate": not permanent_denial,
        "permanent_denial": permanent_denial,
        "source_supported": source_supported,
        "external_network_required": source_type in EXTERNAL_SOURCE_TYPES,
        "real_adapter_connected": False,
        "executes_now": False,
        "file_reads_enabled": False,
        "web_calls_enabled": False,
        "github_calls_enabled": False,
        "threads_enabled": False,
    }


class Mark3ResearchExecutionControlPlane:
    """Prepare-only research execution bridge; it never calls adapters or rehydrates raw requests."""

    def __init__(
        self,
        *,
        outcome_memory: Any = None,
        learning_proposals: Any = None,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.outcome_memory = outcome_memory
        self.learning_proposals = learning_proposals
        self.clock = clock or _now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._records: Dict[str, ResearchExecutionRecord] = {}
        self._audit: List[ResearchExecutionAuditEvent] = []

    def status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "mode": "prepare_only",
            "supported_sources": sorted(SUPPORTED_SOURCE_TYPES),
            "capabilities": {
                source: {
                    "capability": capability,
                    "capability_status": "capability_not_connected_yet",
                    "execution_status": "setup_required",
                }
                for source, capability in CAPABILITY_BY_SOURCE.items()
            },
            "real_research_execution_enabled": False,
            "adapters_connected": False,
            "execute_by_id_rehydrates_request": False,
            "redacted_snapshots_revalidatable": False,
            "raw_requests_stored": False,
            "file_reads_enabled": False,
            "local_scans_enabled": False,
            "threads_enabled": False,
            "github_calls_enabled": False,
            "web_calls_enabled": False,
            "stop_endpoint_available": False,
            "documentation": [
                "docs/jarvis-mark-3-governed-research-execution-bridge.md",
                "docs/JARVIS_MASTER_BUILD_MAP.md",
            ],
            "record_count": len(self._records),
            "audit_event_count": len(self._audit),
        }

    def preview(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        research_id = _text((values or {}).get("research_id")) or self.id_factory()
        normalized = normalize_research_request(values)
        policy = evaluate_research_policy(values)
        integration = self._register_safe_setup_requirement(research_id, normalized, policy, mode="preview")
        record = ResearchExecutionRecord(
            research_id=research_id,
            created_at=self.clock(),
            mode="preview",
            safe_snapshot=normalized["safe_snapshot"],
            policy=policy,
        )
        self._records[research_id] = record
        self._append_audit(
            "research_preview_created",
            research_id,
            "Research execution preview prepared without executing adapters.",
            {
                "source_type": policy["source_type"],
                "candidate_state": policy["candidate_state"],
                "capability_status": policy["capability_status"],
            },
        )
        return self._response(
            research_id=research_id,
            mode="preview",
            normalized=normalized,
            policy=policy,
            integration=integration,
            policy_recalculated=True,
        )

    def execute(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        values = dict(values or {})
        research_id = _text(values.get("research_id")) or self.id_factory()
        full_request = _extract_full_request(values)
        if full_request is None:
            self._append_audit(
                "research_execute_requires_full_request",
                research_id,
                "Execute rejected request-id-only flow; redacted snapshots are not revalidatable.",
                {"research_id_present": bool(values.get("research_id"))},
            )
            return {
                "research_id": research_id,
                "mode": "execute",
                "candidate_state": "setup_required",
                "execution_status": "setup_required",
                "approval_required": False,
                "requires_approval": False,
                "required_approval_level": "direct",
                "approval_valid": False,
                "capability_status": "capability_not_connected_yet",
                "blocked_reasons": [
                    "full_request_required_for_safe_policy_recalculation",
                    "redacted_snapshot_not_revalidatable",
                    "execute_by_id_rehydration_disabled",
                ],
                "can_become_executable_candidate": True,
                "permanent_denial": False,
                "policy_recalculated": False,
                "executed": False,
                "adapters_called": False,
                "file_reads_performed": False,
                "local_scans_performed": False,
                "threads_started": False,
                "github_calls_performed": False,
                "web_calls_performed": False,
                "full_request_stored": False,
                "stored_snapshot_revalidatable": False,
            }

        policy_input = dict(full_request)
        for key in APPROVAL_INPUT_FIELDS:
            if key in values and key not in policy_input:
                policy_input[key] = values[key]
        normalized = normalize_research_request(policy_input)
        policy = evaluate_research_policy(policy_input)
        integration = self._register_safe_setup_requirement(research_id, normalized, policy, mode="execute")
        record = ResearchExecutionRecord(
            research_id=research_id,
            created_at=self.clock(),
            mode="execute",
            safe_snapshot=normalized["safe_snapshot"],
            policy=policy,
        )
        self._records[research_id] = record
        self._append_audit(
            "research_execute_prepared_without_execution",
            research_id,
            "Execute recalculated policy from the full request but did not execute research.",
            {
                "source_type": policy["source_type"],
                "candidate_state": policy["candidate_state"],
                "capability_status": policy["capability_status"],
            },
        )
        return self._response(
            research_id=research_id,
            mode="execute",
            normalized=normalized,
            policy=policy,
            integration=integration,
            policy_recalculated=True,
        )

    def get(self, research_id: str) -> Dict[str, Any]:
        try:
            record = self._records[research_id]
        except KeyError as exc:
            raise KeyError(research_id) from exc
        return {
            **record.to_dict(),
            "can_execute_from_stored_snapshot": False,
            "execute_requires_full_request": True,
        }

    def audit(self) -> Dict[str, Any]:
        return {
            "append_only": True,
            "in_memory_only": True,
            "safe_to_execute": False,
            "events": [event.to_dict() for event in self._audit],
        }

    def _response(
        self,
        *,
        research_id: str,
        mode: str,
        normalized: Dict[str, Any],
        policy: Dict[str, Any],
        integration: Dict[str, Any],
        policy_recalculated: bool,
    ) -> Dict[str, Any]:
        return {
            "research_id": research_id,
            "mode": mode,
            "request_normalized": {
                "source_type": policy["source_type"],
                "query": policy["query"],
                "topic": policy["topic"],
                "scope": policy["scope"],
                "risk_level": policy["risk_level"],
                "goal": policy["goal"],
                "fingerprint": normalized["fingerprint"],
                "risk_text_fields": normalized["risk_text_fields"],
                "absent_fields": normalized["absent_fields"],
                "redacted_fields": normalized["redacted_fields"],
            },
            "safe_snapshot": normalized["safe_snapshot"],
            "policy": policy,
            "candidate_state": policy["candidate_state"],
            "execution_status": policy["execution_status"],
            "approval_required": policy["approval_required"],
            "requires_approval": policy["requires_approval"],
            "required_approval_level": policy["required_approval_level"],
            "approval_valid": policy["approval_valid"],
            "capability_status": policy["capability_status"],
            "blocked_reasons": policy["blocked_reasons"],
            "can_become_executable_candidate": policy["can_become_executable_candidate"],
            "permanent_denial": policy["permanent_denial"],
            "candidate": {
                "candidate_state": policy["candidate_state"],
                "capability": policy["capability"],
                "capability_status": policy["capability_status"],
                "can_become_executable_candidate": policy["can_become_executable_candidate"],
                "executes_now": False,
                "auto_execute": False,
            },
            "integration": integration,
            "policy_recalculated": policy_recalculated,
            "executed": False,
            "adapters_called": False,
            "file_reads_performed": False,
            "local_scans_performed": False,
            "threads_started": False,
            "github_calls_performed": False,
            "web_calls_performed": False,
            "full_request_stored": False,
            "stored_snapshot_revalidatable": False,
        }

    def _register_safe_setup_requirement(
        self,
        research_id: str,
        normalized: Dict[str, Any],
        policy: Dict[str, Any],
        *,
        mode: str,
    ) -> Dict[str, Any]:
        integration = {
            "setup_required_outcome_registered": False,
            "failure_memory_registered": False,
            "learning_proposal_candidate_registered": False,
            "adapter_proposal_created": False,
            "skipped_reason": "",
        }
        if policy["permanent_denial"]:
            integration["skipped_reason"] = "blocked_by_policy"
            return integration
        if policy["candidate_state"] != "setup_required":
            integration["skipped_reason"] = "not_setup_required"
            return integration

        failure = None
        if self.outcome_memory is not None:
            self.outcome_memory.record({
                "mission_id": "mark_3_research_execution",
                "step_id": mode,
                "candidate_id": research_id,
                "goal": policy["goal"],
                "tool_used": "none",
                "capability_used": policy["capability"],
                "result_status": "setup_required",
                "evidence_state": "not_applicable",
                "errors": ["capability_not_connected_yet"],
                "approval_level": policy["required_approval_level"],
                "what_worked": "safe research request normalized and policy classified",
                "what_failed": "research capability is not connected",
                "next_recommended_action": "connect governed research capability before execution",
            })
            integration["setup_required_outcome_registered"] = True
            if hasattr(self.outcome_memory, "record_failure"):
                failure = self.outcome_memory.record_failure({
                    "mission_id": "mark_3_research_execution",
                    "step_id": mode,
                    "candidate_id": research_id,
                    "category": "adapter_not_connected",
                    "error": "capability_not_connected_yet",
                    "affected_capability": policy["capability"],
                    "scope": policy["source_type"],
                    "suggested_avoidance": "return setup_required until a governed adapter is connected",
                })
                integration["failure_memory_registered"] = True

        if self.learning_proposals is not None:
            source_failure_ids = [failure["failure_id"]] if isinstance(failure, dict) and failure.get("failure_id") else []
            self.learning_proposals.create({
                "proposal": f"Connect governed {policy['source_type']} research capability before enabling execution.",
                "evidence": (
                    "Mark 3 research execution bridge returned setup_required for "
                    f"capability={policy['capability']} without executing adapters."
                ),
                "confidence": "high",
                "risk": "low",
                "requires_approval": True,
                "source_failure_ids": source_failure_ids,
            })
            integration["learning_proposal_candidate_registered"] = True
            integration["adapter_proposal_created"] = True

        integration["skipped_reason"] = "" if any(
            integration[key]
            for key in (
                "setup_required_outcome_registered",
                "failure_memory_registered",
                "learning_proposal_candidate_registered",
            )
        ) else "integration_stores_not_connected"
        return integration

    def _append_audit(self, event_type: str, research_id: str, summary: str, metadata: Dict[str, Any]) -> None:
        self._audit.append(ResearchExecutionAuditEvent(
            event_id=self.id_factory(),
            event_type=event_type,
            created_at=self.clock(),
            research_id=research_id,
            summary=summary,
            metadata=_safe_metadata(metadata),
        ))


def _extract_full_request(values: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    nested = values.get("request")
    if isinstance(nested, Mapping) and nested:
        return dict(nested)
    direct = {key: values[key] for key in PUBLIC_REQUEST_FIELDS if key in values}
    return direct or None


def _required_approval_level(source_type: str, risk_level: str, sensitive_actions: List[str]) -> str:
    if any(action in {"deploy", "money", "production"} for action in sensitive_actions):
        return "triple"
    if any(action in {"install", "commit", "push", "merge"} for action in sensitive_actions):
        return "double"
    if risk_level == "critical":
        return "double"
    if risk_level == "high":
        return "strong"
    if risk_level == "medium" or source_type in EXTERNAL_SOURCE_TYPES:
        return "simple"
    return "direct"


def _approval_satisfied(
    *,
    approval_required: bool,
    required_level: str,
    supplied_level: str,
    approval_valid: bool,
    stronger_channel_connected: bool,
) -> bool:
    if not approval_required:
        return True
    if required_level in {"double", "triple"} and not stronger_channel_connected:
        return False
    return approval_valid and _approval_rank(supplied_level) >= _approval_rank(required_level)


def _risk_level(value: Any, text: str) -> str:
    declared = _normalized_choice(value, {"low", "medium", "high", "critical"}, "")
    if declared:
        return declared
    lowered = text.lower()
    if _has_marker(lowered, ("deploy", "money", "production", "credential", "password", "token", ".env")):
        return "critical"
    if _has_marker(lowered, ("install", "commit", "push", "merge")):
        return "high"
    if _has_marker(lowered, ("github", "web", "external")):
        return "medium"
    return "low"


def _promoted_risk(current: str, sensitive_actions: List[str]) -> str:
    if any(action in {"deploy", "money", "production"} for action in sensitive_actions):
        return "critical"
    if sensitive_actions and _risk_rank(current) < _risk_rank("high"):
        return "high"
    return current


def _sensitive_actions(text: str) -> List[str]:
    return [marker for marker in ("install", "commit", "push", "merge", "deploy", "money", "production") if marker in text]


def _authorized(values: Mapping[str, Any]) -> bool:
    if "authorized" in values and not _truthy(values.get("authorized")):
        return False
    if "authorization_valid" in values and not _truthy(values.get("authorization_valid")):
        return False
    if "authorized" in values:
        return _truthy(values.get("authorized"))
    if "authorization_valid" in values:
        return _truthy(values.get("authorization_valid"))
    return True


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "valid", "approved"}
    return bool(value)


def _approval_rank(level: str) -> int:
    try:
        return APPROVAL_LEVELS.index(level)
    except ValueError:
        return 0


def _risk_rank(level: str) -> int:
    try:
        return ("low", "medium", "high", "critical").index(level)
    except ValueError:
        return 0


def _merge_values(values: Optional[Mapping[str, Any]], overrides: Mapping[str, Any]) -> Dict[str, Any]:
    raw = dict(values or {})
    raw.update({key: value for key, value in overrides.items() if value is not None})
    return raw


def _first_present(*values: Any) -> Any:
    for value in values:
        if _present(value):
            return value
    return None


def _present(value: Any) -> bool:
    if value is None:
        return False
    return bool(str(value).strip())


def _text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def _normalized_choice(value: Any, allowed: Iterable[str], fallback: str) -> str:
    text = _text(value).lower()
    return text if text in allowed else fallback


def _normalize_source_type(value: Any) -> str:
    text = _text(value).lower()
    return text or "local_repo"


def _risk_text(values: Mapping[str, Any]) -> str:
    return " ".join(_text(values.get(field)) for field in ("source_type", "query", "topic", "scope", "risk_level", "goal")).strip()


def _redact_text(value: str) -> tuple[str, bool]:
    text = _text(value)
    if not text:
        return "", False
    if _has_marker(text.lower(), SECRET_MARKERS):
        return "[redacted sensitive text]", True
    return text, False


def _fingerprint(values: Mapping[str, Any]) -> str:
    payload = json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _absent_fields(values: Mapping[str, Any]) -> List[str]:
    absent = []
    if not _present(_first_present(values.get("source_type"), values.get("source"))):
        absent.append("source_type")
    if not _present(_first_present(values.get("query"), values.get("topic"))):
        absent.extend(["query", "topic"])
    if not _present(values.get("scope")):
        absent.append("scope")
    if not _present(_first_present(values.get("risk_level"), values.get("risk"))):
        absent.append("risk_level")
    if not _present(values.get("goal")):
        absent.append("goal")
    return absent


def _has_marker(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def _safe_metadata(values: Mapping[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, str):
            safe[key], _ = _redact_text(value)
        else:
            safe[key] = value
    return safe


def _contains_sensitive_request_material(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _has_marker(str(key), SENSITIVE_KEY_MARKERS):
                return True
            if _contains_sensitive_request_material(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_sensitive_request_material(item) for item in value)
    if isinstance(value, str):
        return _has_marker(value, SECRET_MARKERS)
    return False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SECRET_MARKERS: Iterable[str] = (
    ".env",
    "api_key",
    "authorization:",
    "bearer ",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)
SENSITIVE_KEY_MARKERS: Iterable[str] = (
    ".env",
    "api_key",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)
ILLEGAL_MARKERS: Iterable[str] = (
    "steal",
    "exfiltrate",
    "bypass 2fa",
    "unauthorized access",
    "sin autorizacion",
    "sin autorización",
)
UNSAFE_MARKERS: Iterable[str] = (
    "malware",
    "phishing",
    "credential theft",
    "data theft",
)
