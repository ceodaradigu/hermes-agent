from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_UNKNOWN = "unknown"
_REDACTED = "[redacted sensitive input]"
_SOURCE_TYPES = {"calendar", "email", "document", "local_files", "pc_state", "routine", "environment", "unknown"}
_CONSENT_STATUSES = {"missing", "pending", "approved", "denied", "unknown"}
_ROUTINE_TYPES = {"morning", "evening", "work", "family", "health", "learning", "unknown"}
_ENERGY_STATES = {"unknown", "low", "medium", "high"}
_SENSITIVE_SOURCE_TYPES = {"calendar", "email", "document", "local_files"}
_SENSITIVE_MARKERS = (
    ".env", "api key", "api-key", "api_key", "apikey", "authorization", "bearer",
    "credential", "credentials", "password", "private key", "private_key", "secret", "token",
)


@dataclass(frozen=True)
class PersonalOSEnvironmentStatus:
    prepare_only: bool = True
    personal_os_available: bool = False
    environment_intelligence_available: bool = False
    pc_state_awareness_enabled: bool = False
    calendar_reading_enabled: bool = False
    email_reading_enabled: bool = False
    document_reading_enabled: bool = False
    local_file_scanning_enabled: bool = False
    context_crossing_enabled: bool = False
    attention_notifications_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    sensitive_inference_enabled: bool = False
    surveillance_enabled: bool = False
    camera_enabled: bool = False
    microphone_enabled: bool = False
    screen_capture_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False
    persistence_enabled: bool = False

    def __post_init__(self) -> None:
        _force_safe(self)

    @classmethod
    def placeholder(cls) -> "PersonalOSEnvironmentStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "PersonalOSEnvironmentStatus":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PersonalOSPrivacyPolicy:
    prepare_only: bool = True
    consent_required_per_source: bool = True
    no_calendar_read_by_default: bool = True
    no_email_read_by_default: bool = True
    no_doc_read_by_default: bool = True
    no_local_file_scan_by_default: bool = True
    no_surveillance_by_default: bool = True
    no_sensitive_inference_by_default: bool = True
    no_cross_context_by_default: bool = True
    no_guest_mode_memory_by_default: bool = True
    visible_reasons_required: bool = True
    audit_explanation_required: bool = True
    strong_approval_required_for_sensitive_sources: bool = True
    strong_approval_required_for_cross_context: bool = True
    strong_approval_required_for_sending_or_acting: bool = True
    strong_approval_required_for_camera_microphone_screen: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in self.__dataclass_fields__:
            if name != "prepare_only":
                object.__setattr__(self, name, True)

    @classmethod
    def placeholder(cls) -> "PersonalOSPrivacyPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "PersonalOSPrivacyPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ContextSourceConsentPreview:
    prepare_only: bool = True
    source_name: str = _UNKNOWN
    source_type: str = _UNKNOWN
    access_requested: bool = False
    consent_status: str = "missing"
    scope_preview: List[str] = field(default_factory=list)
    would_read_source: bool = False
    would_store_data: bool = False
    would_cross_context: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False
    visible_reason: str = "Source access remains blocked until explicit consent and approval."
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _safe_common(self, choices={"source_type": _SOURCE_TYPES, "consent_status": _CONSENT_STATUSES})
        _force_true(self, "approval_required")
        object.__setattr__(
            self,
            "strong_approval_required",
            bool(self.strong_approval_required or self.source_type in _SENSITIVE_SOURCE_TYPES),
        )
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ContextSourceConsentPreview":
        source = dict(data or {})
        source_type = _choice(source.get("source_type"), _SOURCE_TYPES)
        crossing = bool(source.get("cross_context_requested"))
        return cls(
            source_name=source.get("source_name", _UNKNOWN),
            source_type=source_type,
            access_requested=bool(source.get("access_requested", False)),
            consent_status=source.get("consent_status", "missing"),
            scope_preview=_safe_list(source.get("scope_preview")),
            strong_approval_required=source_type in _SENSITIVE_SOURCE_TYPES or crossing or _strong_risk_requested(source),
            visible_reason=source.get("visible_reason") or "Source access remains blocked until explicit consent and approval.",
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class DailyStatePreview:
    prepare_only: bool = True
    date: str = _UNKNOWN
    timezone: str = _UNKNOWN
    mode: str = _UNKNOWN
    priorities: List[str] = field(default_factory=list)
    focus_state: str = _UNKNOWN
    open_loops: List[str] = field(default_factory=list)
    blocked_items: List[str] = field(default_factory=list)
    energy_hint: str = _UNKNOWN
    source_data: str = _UNKNOWN
    no_external_calendar_read: bool = True
    no_email_read: bool = True
    no_doc_read: bool = True
    would_notify: bool = False
    would_execute: bool = False
    sensitive_inference_made: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, choices={"source_data": {"provided", "unknown"}})
        _force_true(self, "no_external_calendar_read", "no_email_read", "no_doc_read")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DailyStatePreview":
        return cls(**_select(dict(data or {}), cls))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PCEnvironmentStatePreview:
    prepare_only: bool = True
    device_state_summary: str = _UNKNOWN
    active_context: str = _UNKNOWN
    environment_signals: List[str] = field(default_factory=list)
    interruption_risk: str = _UNKNOWN
    focus_mode_suggestion: str = _UNKNOWN
    no_screen_capture: bool = True
    no_process_scan: bool = True
    no_file_scan: bool = True
    no_camera_or_microphone: bool = True
    would_monitor: bool = False
    would_track: bool = False
    would_persist: bool = False

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "no_screen_capture", "no_process_scan", "no_file_scan", "no_camera_or_microphone")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PCEnvironmentStatePreview":
        return cls(**_select(dict(data or {}), cls))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class AwarenessSourcePreview:
    prepare_only: bool = True
    calendar_awareness_requested: bool = False
    email_awareness_requested: bool = False
    document_awareness_requested: bool = False
    local_file_awareness_requested: bool = False
    would_read_calendar: bool = False
    would_read_email: bool = False
    would_read_docs: bool = False
    would_scan_local_files: bool = False
    consent_required: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    data_minimization_required: bool = True

    def __post_init__(self) -> None:
        _force_true(self, "consent_required", "approval_required", "data_minimization_required")
        object.__setattr__(
            self,
            "strong_approval_required",
            bool(
                self.strong_approval_required
                or self.calendar_awareness_requested
                or self.email_awareness_requested
                or self.document_awareness_requested
                or self.local_file_awareness_requested
            ),
        )
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "AwarenessSourcePreview":
        source = dict(data or {})
        requested = any(bool(source.get(name)) for name in (
            "calendar_awareness_requested", "email_awareness_requested",
            "document_awareness_requested", "local_file_awareness_requested",
        ))
        return cls(
            calendar_awareness_requested=bool(source.get("calendar_awareness_requested")),
            email_awareness_requested=bool(source.get("email_awareness_requested")),
            document_awareness_requested=bool(source.get("document_awareness_requested")),
            local_file_awareness_requested=bool(source.get("local_file_awareness_requested")),
            strong_approval_required=requested or _strong_risk_requested(source),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class LocalFilesScopePreview:
    prepare_only: bool = True
    scope_name: str = _UNKNOWN
    allowed_paths_preview: List[str] = field(default_factory=list)
    denied_paths_preview: List[str] = field(default_factory=list)
    would_scan: bool = False
    would_index: bool = False
    would_store: bool = False
    secrets_blocked: bool = True
    private_paths_blocked: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "secrets_blocked", "private_paths_blocked", "approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "LocalFilesScopePreview":
        source = dict(data or {})
        return cls(
            scope_name=source.get("scope_name", _UNKNOWN),
            allowed_paths_preview=_safe_list(source.get("allowed_paths_preview")),
            denied_paths_preview=_safe_list(source.get("denied_paths_preview")),
            strong_approval_required=bool(source.get("broad_scope_requested") or source.get("private_scope_requested"))
            or _strong_risk_requested(source),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ContextSwitchingPreview:
    prepare_only: bool = True
    current_context: str = _UNKNOWN
    target_context: str = _UNKNOWN
    switch_reason: str = _UNKNOWN
    context_boundary_risk: str = _UNKNOWN
    would_switch: bool = False
    would_mix_contexts: bool = False
    professional_personal_separation_required: bool = True
    approval_required: bool = False
    visible_reason: str = "Context switch is a review-only preview."

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "professional_personal_separation_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ContextSwitchingPreview":
        source = dict(data or {})
        crossing = bool(source.get("cross_context_requested") or source.get("private_professional_boundary"))
        return cls(
            current_context=source.get("current_context", _UNKNOWN),
            target_context=source.get("target_context", _UNKNOWN),
            switch_reason=source.get("switch_reason", _UNKNOWN),
            context_boundary_risk=source.get("context_boundary_risk", _UNKNOWN),
            approval_required=crossing,
            visible_reason=source.get("visible_reason") or "Context switch is a review-only preview.",
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class AttentionProtectionPreview:
    prepare_only: bool = True
    focus_window: str = _UNKNOWN
    interruption_policy: str = _UNKNOWN
    allowed_interruptions: List[str] = field(default_factory=list)
    blocked_interruptions: List[str] = field(default_factory=list)
    would_send_notifications: bool = False
    would_mute_apps: bool = False
    would_modify_system_settings: bool = False
    would_contact_people: bool = False
    strong_approval_required: bool = False

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "AttentionProtectionPreview":
        source = dict(data or {})
        return cls(
            **_select(source, cls),
            strong_approval_required=bool(
                source.get("notification_requested") or source.get("system_change_requested")
                or source.get("contact_people_requested") or _strong_risk_requested(source)
            ),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PersonalRoutinePreview:
    prepare_only: bool = True
    routine_name: str = _UNKNOWN
    routine_type: str = _UNKNOWN
    steps_preview: List[str] = field(default_factory=list)
    triggers_preview: List[str] = field(default_factory=list)
    would_schedule: bool = False
    would_execute: bool = False
    would_notify: bool = False
    would_persist: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, choices={"routine_type": _ROUTINE_TYPES})
        _force_true(self, "approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PersonalRoutinePreview":
        return cls(**_select(dict(data or {}), cls))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class EnergyFocusSupportPreview:
    prepare_only: bool = True
    energy_state: str = _UNKNOWN
    focus_recommendation: str = _UNKNOWN
    workload_risk: str = _UNKNOWN
    break_suggestion: str = _UNKNOWN
    sensitive_health_inference_made: bool = False
    no_medical_conclusion: bool = True
    would_notify: bool = False
    would_execute: bool = False
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _safe_common(self, choices={"energy_state": _ENERGY_STATES})
        _force_true(self, "no_medical_conclusion")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "EnergyFocusSupportPreview":
        return cls(**_select(dict(data or {}), cls))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class GuestModeContextPreview:
    prepare_only: bool = True
    guest_mode_enabled_preview: bool = True
    memory_disabled: bool = True
    personal_context_hidden: bool = True
    sensitive_sources_blocked: bool = True
    cross_context_blocked: bool = True
    would_persist: bool = False
    would_use_private_context: bool = False

    def __post_init__(self) -> None:
        _force_true(
            self, "guest_mode_enabled_preview", "memory_disabled", "personal_context_hidden",
            "sensitive_sources_blocked", "cross_context_blocked",
        )
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "GuestModeContextPreview":
        return cls()

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class VisibleReasonAuditPreview:
    prepare_only: bool = True
    action_or_preview_name: str = _UNKNOWN
    visible_reason: str = "No action is taken; this preview explains the proposed context use."
    data_sources_used: List[str] = field(default_factory=list)
    data_sources_blocked: List[str] = field(default_factory=list)
    approvals_needed: List[str] = field(default_factory=list)
    uncertainty_notes: List[str] = field(default_factory=list)
    no_hidden_reasoning_claim: bool = True
    audit_required: bool = True
    would_persist_audit: bool = False

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "no_hidden_reasoning_claim", "audit_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "VisibleReasonAuditPreview":
        return cls(**_select(dict(data or {}), cls))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PersonalOSApprovalRequirements:
    prepare_only: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    approval_gateway_called: bool = False
    approval_created: bool = False
    approval_granted: bool = False
    approval_rejected: bool = False

    def __post_init__(self) -> None:
        _force_true(self, "approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PersonalOSApprovalRequirements":
        return cls(strong_approval_required=_strong_risk_requested(dict(data or {})))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


_FORCED_FALSE = {
    "personal_os_available", "environment_intelligence_available", "pc_state_awareness_enabled",
    "calendar_reading_enabled", "email_reading_enabled", "document_reading_enabled",
    "local_file_scanning_enabled", "context_crossing_enabled", "attention_notifications_enabled",
    "external_calls_enabled", "secrets_access_enabled", "sensitive_inference_enabled",
    "surveillance_enabled", "camera_enabled", "microphone_enabled", "screen_capture_enabled",
    "hermes_called", "approval_gateway_called", "execution_enabled", "persistence_enabled",
    "would_read_source", "would_store_data", "would_cross_context", "would_notify", "would_execute",
    "sensitive_inference_made", "would_monitor", "would_track", "would_persist",
    "would_read_calendar", "would_read_email", "would_read_docs", "would_scan_local_files",
    "would_scan", "would_index", "would_store", "would_switch", "would_mix_contexts",
    "would_send_notifications", "would_mute_apps", "would_modify_system_settings", "would_contact_people",
    "would_schedule", "sensitive_health_inference_made", "would_use_private_context",
    "would_persist_audit", "approval_created", "approval_granted", "approval_rejected",
}


def _force_safe(value: Any) -> None:
    object.__setattr__(value, "prepare_only", True)
    for name in _FORCED_FALSE:
        if name in value.__dataclass_fields__:
            object.__setattr__(value, name, False)


def _force_true(value: Any, *names: str) -> None:
    for name in names:
        object.__setattr__(value, name, True)


def _serialize(value: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        result[name] = list(item) if isinstance(item, list) else item
    result["prepare_only"] = True
    for name in _FORCED_FALSE:
        if name in result:
            result[name] = False
    return result


def _safe_common(value: Any, *, choices: Optional[Dict[str, set[str]]] = None) -> None:
    choices = choices or {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        if isinstance(item, list):
            object.__setattr__(value, name, _safe_list(item))
        elif isinstance(item, str):
            object.__setattr__(value, name, _choice(item, choices[name]) if name in choices else _safe_text(item, _UNKNOWN))


def _safe_text(value: Any, default: str = "") -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return default
    if any(marker in text.lower() for marker in _SENSITIVE_MARKERS):
        return _REDACTED
    return text[:500]


def _safe_list(value: Any) -> List[str]:
    items = value if isinstance(value, list) else []
    return [_safe_text(item) for item in items[:100] if _safe_text(item)]


def _choice(value: Any, choices: set[str]) -> str:
    text = str(value or "").strip().lower()
    return text if text in choices else _UNKNOWN


def _select(source: Dict[str, Any], cls: Any) -> Dict[str, Any]:
    return {
        name: source[name]
        for name in cls.__dataclass_fields__
        if name not in _FORCED_FALSE
        and name not in {"prepare_only", "approval_required", "strong_approval_required"}
        and name in source
        and source[name] is not None
    }


def _strong_risk_requested(source: Dict[str, Any]) -> bool:
    names = (
        "sensitive_source", "private_source", "cross_context", "sending", "acting", "camera",
        "microphone", "screen", "external_account", "private_files", "broad_scope", "secrets",
    )
    return any(bool(source.get(name) or source.get(f"{name}_requested")) for name in names)
