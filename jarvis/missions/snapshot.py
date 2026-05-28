from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from jarvis.missions.command_builder import MissionCommand
from jarvis.missions.dry_run import MissionDryRunEvaluation
from jarvis.missions.state_store import MissionState


SNAPSHOT_VERSION = "1"
SNAPSHOT_SOURCE = "mission_snapshot_serializer"


@dataclass(frozen=True)
class MissionSnapshotValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class MissionSnapshot:
    snapshot_id: str
    mission_id: str
    state: Dict[str, Any]
    commands: List[Dict[str, Any]] = field(default_factory=list)
    dry_run_evaluations: List[Dict[str, Any]] = field(default_factory=list)
    approval_requests: List[Dict[str, Any]] = field(default_factory=list)
    audit_events: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: _now_iso())
    redacted: bool = True
    redacted_fields: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = SNAPSHOT_VERSION
    source: str = SNAPSHOT_SOURCE
    summary: str = ""
    status: Optional[str] = None
    risk_summary: Dict[str, Any] = field(default_factory=dict)
    audit_summary: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.state = deepcopy(self.state)
        self.commands = _copy_list_value(self.commands)
        self.dry_run_evaluations = _copy_list_value(self.dry_run_evaluations)
        self.approval_requests = _copy_list_value(self.approval_requests)
        self.audit_events = _copy_list_value(self.audit_events)
        self.redacted_fields = _copy_list_value(self.redacted_fields)
        self.metadata = deepcopy(self.metadata or {})
        self.risk_summary = deepcopy(self.risk_summary or {})
        self.audit_summary = deepcopy(self.audit_summary or {})

        result = validate_mission_snapshot(self)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionSnapshot":
        return cls(
            snapshot_id=str(data.get("snapshot_id", "")),
            mission_id=str(data.get("mission_id", "")),
            state=deepcopy(data.get("state") or {}),
            commands=_copy_optional_list(data.get("commands")),
            dry_run_evaluations=_copy_optional_list(data.get("dry_run_evaluations")),
            approval_requests=_copy_optional_list(data.get("approval_requests")),
            audit_events=_copy_optional_list(data.get("audit_events")),
            created_at=str(data.get("created_at", "")),
            redacted=bool(data.get("redacted", True)),
            redacted_fields=_copy_optional_list(data.get("redacted_fields")),
            metadata=deepcopy(data.get("metadata") or {}),
            version=str(data.get("version", SNAPSHOT_VERSION)),
            source=str(data.get("source", SNAPSHOT_SOURCE)),
            summary=str(data.get("summary", "")),
            status=data.get("status"),
            risk_summary=deepcopy(data.get("risk_summary") or {}),
            audit_summary=deepcopy(data.get("audit_summary") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "mission_id": self.mission_id,
            "state": deepcopy(self.state),
            "commands": [deepcopy(item) for item in self.commands],
            "dry_run_evaluations": [deepcopy(item) for item in self.dry_run_evaluations],
            "approval_requests": [deepcopy(item) for item in self.approval_requests],
            "audit_events": [deepcopy(item) for item in self.audit_events],
            "created_at": self.created_at,
            "redacted": self.redacted,
            "redacted_fields": list(self.redacted_fields),
            "metadata": deepcopy(self.metadata),
            "version": self.version,
            "source": self.source,
            "summary": self.summary,
            "status": self.status,
            "risk_summary": deepcopy(self.risk_summary),
            "audit_summary": deepcopy(self.audit_summary),
        }


def build_mission_snapshot(
    state: MissionState,
    commands: Optional[List[Any]] = None,
    dry_run_evaluations: Optional[List[Any]] = None,
    *,
    redacted: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> MissionSnapshot:
    if not isinstance(state, MissionState):
        raise ValueError("state must be a MissionState")
    if commands is None:
        command_items: List[Any] = []
    elif isinstance(commands, list):
        command_items = commands
    else:
        raise ValueError("commands must be a list")

    if dry_run_evaluations is None:
        evaluation_items: List[Any] = []
    elif isinstance(dry_run_evaluations, list):
        evaluation_items = dry_run_evaluations
    else:
        raise ValueError("dry_run_evaluations must be a list")

    if metadata is None:
        snapshot_metadata: Dict[str, Any] = {}
    elif isinstance(metadata, dict):
        snapshot_metadata = deepcopy(metadata)
    else:
        raise ValueError("metadata must be a dict")

    state_dict = state.to_dict()
    mission_id = state.mission_id
    if not mission_id or state_dict.get("mission_id") != mission_id:
        raise ValueError("snapshot mission_id must match state.mission_id")

    command_dicts = [_serialize_command(item, mission_id) for item in command_items]
    evaluation_dicts = [_serialize_evaluation(item, mission_id) for item in evaluation_items]

    raw_snapshot = {
        "snapshot_id": str(uuid4()),
        "mission_id": mission_id,
        "state": state_dict,
        "commands": command_dicts,
        "dry_run_evaluations": evaluation_dicts,
        "approval_requests": deepcopy(state_dict.get("approval_requests", [])),
        "audit_events": deepcopy(state_dict.get("audit_events", [])),
        "created_at": _now_iso(),
        "redacted": redacted,
        "redacted_fields": [],
        "metadata": snapshot_metadata,
        "version": SNAPSHOT_VERSION,
        "source": SNAPSHOT_SOURCE,
        "summary": _build_summary(state_dict, command_dicts, evaluation_dicts),
        "status": state_dict.get("status"),
        "risk_summary": _build_risk_summary(evaluation_dicts),
        "audit_summary": _build_audit_summary(state_dict, command_dicts, evaluation_dicts),
    }

    if _blanket_approval_paths(raw_snapshot):
        raise ValueError("snapshot cannot contain vague blanket approval")

    if redacted:
        snapshot_dict, redacted_fields = redact_snapshot_dict(raw_snapshot)
        snapshot_dict["redacted_fields"] = redacted_fields
    else:
        secret_paths = _secret_like_key_paths(raw_snapshot)
        if secret_paths:
            raise ValueError("snapshot cannot expose secret-like keys: " + ", ".join(secret_paths))
        snapshot_dict = raw_snapshot

    return MissionSnapshot.from_dict(snapshot_dict)


def validate_mission_snapshot(snapshot: MissionSnapshot) -> MissionSnapshotValidationResult:
    errors: List[str] = []

    snapshot_dict = snapshot.to_dict() if isinstance(snapshot, MissionSnapshot) else {}
    if not _is_non_empty_string(getattr(snapshot, "snapshot_id", "")):
        errors.append("snapshot_id must be a non-empty string")
    if not _is_non_empty_string(getattr(snapshot, "mission_id", "")):
        errors.append("mission_id must be a non-empty string")

    state = getattr(snapshot, "state", None)
    if not isinstance(state, dict):
        errors.append("state must be a dict")
        state = {}
    elif state.get("mission_id") != getattr(snapshot, "mission_id", None):
        errors.append("snapshot mission_id must match state.mission_id")

    for field_name in ["commands", "dry_run_evaluations", "approval_requests", "audit_events", "redacted_fields"]:
        if not isinstance(getattr(snapshot, field_name, None), list):
            errors.append(f"{field_name} must be a list")

    metadata = getattr(snapshot, "metadata", None)
    if not isinstance(metadata, dict):
        errors.append("metadata must be a dict")
    elif not _is_simple_json_value(metadata):
        errors.append("metadata must be a simple JSON-compatible dict")

    if not isinstance(getattr(snapshot, "risk_summary", None), dict):
        errors.append("risk_summary must be a dict")
    if not isinstance(getattr(snapshot, "audit_summary", None), dict):
        errors.append("audit_summary must be a dict")

    mission_id = getattr(snapshot, "mission_id", None)
    errors.extend(_validate_item_mission_ids("commands", getattr(snapshot, "commands", []), mission_id))
    errors.extend(
        _validate_item_mission_ids(
            "dry_run_evaluations",
            getattr(snapshot, "dry_run_evaluations", []),
            mission_id,
        )
    )
    errors.extend(_validate_item_mission_ids("approval_requests", getattr(snapshot, "approval_requests", []), mission_id))
    errors.extend(_validate_item_mission_ids("audit_events", getattr(snapshot, "audit_events", []), mission_id))

    secret_paths = _secret_like_key_paths(snapshot_dict)
    if secret_paths:
        errors.append("snapshot cannot expose secret-like keys: " + ", ".join(secret_paths))

    summary_secret_paths = _secret_like_text_paths(
        {
            "summary": getattr(snapshot, "summary", ""),
            "audit_summary": getattr(snapshot, "audit_summary", {}),
        }
    )
    if summary_secret_paths:
        errors.append("summary and audit_summary cannot expose secret-like text: " + ", ".join(summary_secret_paths))

    blanket_paths = _blanket_approval_paths(
        {
            "summary": getattr(snapshot, "summary", ""),
            "audit_summary": getattr(snapshot, "audit_summary", {}),
            "metadata": metadata if isinstance(metadata, dict) else {},
        }
    )
    if blanket_paths:
        errors.append("snapshot cannot contain vague blanket approval: " + ", ".join(blanket_paths))

    try:
        json.dumps(snapshot_dict)
    except TypeError:
        errors.append("snapshot must be JSON-compatible")

    return MissionSnapshotValidationResult(errors=errors)


def redact_snapshot_dict(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    redacted_fields: List[str] = []
    redacted = _redact_secret_keys(deepcopy(data), "", redacted_fields)
    return redacted, sorted(redacted_fields)


def _serialize_command(item: Any, mission_id: str) -> Dict[str, Any]:
    if isinstance(item, MissionCommand):
        data = item.to_dict()
    elif isinstance(item, dict):
        data = deepcopy(item)
    else:
        raise ValueError("commands must contain MissionCommand or dict items")
    if data.get("mission_id") != mission_id:
        raise ValueError("commands must match mission_id")
    return data


def _serialize_evaluation(item: Any, mission_id: str) -> Dict[str, Any]:
    if isinstance(item, MissionDryRunEvaluation):
        data = item.to_dict()
    elif isinstance(item, dict):
        data = deepcopy(item)
    else:
        raise ValueError("dry_run_evaluations must contain MissionDryRunEvaluation or dict items")
    if data.get("mission_id") != mission_id:
        raise ValueError("dry_run_evaluations must match mission_id")
    return data


def _build_summary(
    state: Dict[str, Any],
    commands: List[Dict[str, Any]],
    dry_run_evaluations: List[Dict[str, Any]],
) -> str:
    return (
        f"Mission {state.get('mission_id')} snapshot captured with status {state.get('status')}; "
        f"{len(commands)} command(s), {len(dry_run_evaluations)} dry-run evaluation(s), "
        f"{len(state.get('approval_requests', []))} approval request(s), "
        f"{len(state.get('audit_events', []))} audit event(s)."
    )


def _build_risk_summary(dry_run_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    risk_counts: Dict[str, int] = {}
    decisions: Dict[str, int] = {}
    requires_approval_count = 0
    for evaluation in dry_run_evaluations:
        risk = str(evaluation.get("risk_level") or "unknown")
        decision = str(evaluation.get("decision") or "unknown")
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
        decisions[decision] = decisions.get(decision, 0) + 1
        if evaluation.get("requires_approval"):
            requires_approval_count += 1
    return {
        "dry_run_evaluation_count": len(dry_run_evaluations),
        "requires_approval_count": requires_approval_count,
        "risk_counts": risk_counts,
        "decision_counts": decisions,
    }


def _build_audit_summary(
    state: Dict[str, Any],
    commands: List[Dict[str, Any]],
    dry_run_evaluations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "approval_request_count": len(state.get("approval_requests", [])),
        "audit_event_count": len(state.get("audit_events", [])),
        "command_count": len(commands),
        "dry_run_evaluation_count": len(dry_run_evaluations),
    }


def _validate_item_mission_ids(field_name: str, values: Any, mission_id: str) -> List[str]:
    if not isinstance(values, list):
        return []
    errors: List[str] = []
    for item in values:
        if not isinstance(item, dict):
            errors.append(f"{field_name} must contain dict items")
            continue
        if item.get("mission_id") != mission_id:
            errors.append(f"{field_name} must match mission_id")
    return errors


def _redact_secret_keys(value: Any, prefix: str, redacted_fields: List[str]) -> Any:
    if isinstance(value, dict):
        redacted: Dict[str, Any] = {}
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if _is_secret_like_key(str(key)):
                redacted_fields.append(key_path)
                continue
            redacted[key] = _redact_secret_keys(item, key_path, redacted_fields)
        return redacted
    if isinstance(value, list):
        return [
            _redact_secret_keys(item, f"{prefix}[{index}]", redacted_fields)
            for index, item in enumerate(value)
        ]
    return value


def _secret_like_key_paths(value: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if _is_secret_like_key(str(key)):
                paths.append(key_path)
            paths.extend(_secret_like_key_paths(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_secret_like_key_paths(item, f"{prefix}[{index}]"))
    return sorted(paths)


def _secret_like_text_paths(value: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(_secret_like_text_paths(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_secret_like_text_paths(item, f"{prefix}[{index}]"))
    elif isinstance(value, str) and _contains_secret_like_text(value):
        paths.append(prefix or "value")
    return paths


def _blanket_approval_paths(value: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if _contains_blanket_approval(str(key)):
                paths.append(key_path)
            paths.extend(_blanket_approval_paths(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_blanket_approval_paths(item, f"{prefix}[{index}]"))
    elif isinstance(value, str) and _contains_blanket_approval(value):
        paths.append(prefix or "value")
    return paths


def _contains_secret_like_text(value: str) -> bool:
    normalized = _normalize(value)
    return any(key in normalized for key in _SECRET_LIKE_KEYS)


def _contains_blanket_approval(value: str) -> bool:
    normalized = _normalize(value)
    return any(phrase in normalized for phrase in _BLANKET_APPROVAL_PHRASES)


def _is_secret_like_key(value: str) -> bool:
    normalized = _normalize(value)
    return any(key == normalized or key in normalized for key in _SECRET_LIKE_KEYS)


def _is_simple_json_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_simple_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_simple_json_value(item) for key, item in value.items())
    return False


def _copy_optional_list(value: Any) -> Any:
    if value is None:
        return []
    return _copy_list_value(value)


def _copy_list_value(value: Any) -> Any:
    if isinstance(value, list):
        return [deepcopy(item) for item in value]
    return deepcopy(value)


def _is_non_empty_string(value: Optional[str]) -> bool:
    return bool((value or "").strip())


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_BLANKET_APPROVAL_PHRASES = {
    "approve_all_forever",
    "do_anything",
    "unlimited",
    "no_limits",
    "whatever_it_takes",
    "haz_todo_lo_necesario_sin_limites",
}

_SECRET_LIKE_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
    "private_key",
    "authorization",
    "cookie",
    ".env",
}
