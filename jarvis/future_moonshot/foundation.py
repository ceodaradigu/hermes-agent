from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_UNKNOWN = "unknown"
_REDACTED = "[redacted sensitive input]"
_CAPABILITY_TYPES = {
    "smart_glasses", "ar_overlay", "robotics", "drones", "simulation", "physical_automation", "unknown",
}
_SYSTEM_TYPES = {"robot", "drone", "actuator", "vehicle", "unknown"}
_RISK_LEVELS = {"none", "low", "medium", "high", "unknown"}
_SENSITIVE_MARKERS = (
    ".env", "api key", "api-key", "api_key", "apikey", "authorization", "bearer",
    "credential", "credentials", "password", "private key", "private_key", "secret", "token",
)


@dataclass(frozen=True)
class FutureMoonshotStatus:
    prepare_only: bool = True
    future_moonshot_available: bool = False
    smart_glasses_enabled: bool = False
    ar_overlay_enabled: bool = False
    robotics_enabled: bool = False
    drones_enabled: bool = False
    physical_world_automation_enabled: bool = False
    deep_simulation_enabled: bool = False
    camera_enabled: bool = False
    microphone_enabled: bool = False
    screen_capture_enabled: bool = False
    surveillance_enabled: bool = False
    identity_impersonation_enabled: bool = False
    illegal_action_enabled: bool = False
    implicit_permission_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False
    persistence_enabled: bool = False

    def __post_init__(self) -> None:
        _force_safe(self)

    placeholder = classmethod(lambda cls: cls())
    from_dict = classmethod(lambda cls, data: cls())

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MoonshotSafetyPolicy:
    prepare_only: bool = True
    no_physical_world_action_by_default: bool = True
    no_robotics_by_default: bool = True
    no_drones_by_default: bool = True
    no_smart_glasses_by_default: bool = True
    no_ar_overlay_by_default: bool = True
    no_camera_microphone_screen_by_default: bool = True
    no_surveillance_by_default: bool = True
    no_impersonation_by_default: bool = True
    no_illegal_actions_by_default: bool = True
    no_implicit_permissions: bool = True
    legal_review_required: bool = True
    safety_review_required: bool = True
    controlled_environment_required: bool = True
    immediate_stop_required: bool = True
    audit_required: bool = True
    rollback_required: bool = True
    strong_approval_required_for_physical: bool = True
    strong_approval_required_for_legal: bool = True
    strong_approval_required_for_identity: bool = True
    strong_approval_required_for_money: bool = True
    strong_approval_required_for_safety: bool = True

    def __post_init__(self) -> None:
        _force_all_true(self)

    placeholder = classmethod(lambda cls: cls())
    from_dict = classmethod(lambda cls, data: cls())

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MoonshotCapabilityPreview:
    prepare_only: bool = True
    capability_name: str = _UNKNOWN
    capability_type: str = _UNKNOWN
    concept_summary: str = _UNKNOWN
    intended_value: str = _UNKNOWN
    monetization_or_efficiency_hypothesis: str = _UNKNOWN
    spectacle_risk: str = _UNKNOWN
    safety_risk: str = _UNKNOWN
    legal_risk: str = _UNKNOWN
    identity_risk: str = _UNKNOWN
    privacy_risk: str = _UNKNOWN
    would_execute: bool = False
    would_connect_device: bool = False
    would_modify_physical_world: bool = False
    approval_required: bool = True
    strong_approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _safe_common(self, choices={"capability_type": _CAPABILITY_TYPES, **_risk_choices(self)})
        _force_true(self, "approval_required")
        object.__setattr__(self, "strong_approval_required", _has_material_risk(self))
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class SmartGlassesIntegrationPreview:
    prepare_only: bool = True
    device_name: str = _UNKNOWN
    integration_goal: str = _UNKNOWN
    data_inputs_preview: List[str] = field(default_factory=list)
    output_modes_preview: List[str] = field(default_factory=list)
    camera_required: bool = False
    microphone_required: bool = False
    always_on_risk: str = _UNKNOWN
    privacy_risk: str = _UNKNOWN
    bystander_privacy_risk: str = _UNKNOWN
    visible_indicator_required: bool = True
    immediate_stop_required: bool = True
    would_connect_device: bool = False
    would_activate_camera: bool = False
    would_activate_microphone: bool = False
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, choices=_risk_choices(self))
        _force_true(self, "visible_indicator_required", "immediate_stop_required", "strong_approval_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class AROverlayPreview:
    prepare_only: bool = True
    overlay_name: str = _UNKNOWN
    overlay_goal: str = _UNKNOWN
    display_context: str = _UNKNOWN
    data_sources_preview: List[str] = field(default_factory=list)
    safety_risk: str = _UNKNOWN
    distraction_risk: str = _UNKNOWN
    physical_world_dependency: str = _UNKNOWN
    would_render_overlay: bool = False
    would_capture_screen: bool = False
    would_use_camera: bool = False
    would_act_on_overlay: bool = False
    immediate_stop_required: bool = True
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, choices=_risk_choices(self))
        _force_true(self, "immediate_stop_required", "strong_approval_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class RoboticsDroneSafetyReviewPreview:
    prepare_only: bool = True
    system_name: str = _UNKNOWN
    system_type: str = _UNKNOWN
    intended_use: str = _UNKNOWN
    controlled_environment_required: bool = True
    human_supervision_required: bool = True
    geofence_required: bool = False
    emergency_stop_required: bool = True
    legal_review_required: bool = True
    bystander_safety_risk: str = _UNKNOWN
    property_damage_risk: str = _UNKNOWN
    prohibited_if_unsafe_or_illegal: bool = True
    would_send_command: bool = False
    would_connect_device: bool = False
    would_move_device: bool = False
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, choices={"system_type": _SYSTEM_TYPES, **_risk_choices(self)})
        _force_true(
            self, "controlled_environment_required", "human_supervision_required", "emergency_stop_required",
            "legal_review_required", "prohibited_if_unsafe_or_illegal", "strong_approval_required",
        )
        object.__setattr__(self, "geofence_required", self.system_type in {"drone", "vehicle"})
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class DeepSimulationPreview:
    prepare_only: bool = True
    simulation_name: str = _UNKNOWN
    simulation_goal: str = _UNKNOWN
    simulated_domain: str = _UNKNOWN
    assumptions: List[str] = field(default_factory=list)
    limits: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    no_real_world_action: bool = True
    no_production_decision_without_review: bool = True
    would_run_simulation: bool = False
    would_execute_real_action: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "no_real_world_action", "no_production_decision_without_review", "approval_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PhysicalWorldAutomationPreview:
    prepare_only: bool = True
    automation_name: str = _UNKNOWN
    target_environment: str = _UNKNOWN
    intended_action: str = _UNKNOWN
    physical_risk: str = _UNKNOWN
    legal_risk: str = _UNKNOWN
    safety_controls: List[str] = field(default_factory=list)
    stop_plan: str = _UNKNOWN
    rollback_plan: str = _UNKNOWN
    controlled_environment_required: bool = True
    would_control_device: bool = False
    would_send_command: bool = False
    would_modify_environment: bool = False
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, choices=_risk_choices(self))
        object.__setattr__(self, "rollback_plan", _safe_text(self.rollback_plan))
        _force_true(self, "controlled_environment_required", "strong_approval_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class LegalSafetyReviewPreview:
    prepare_only: bool = True
    review_subject: str = _UNKNOWN
    legal_questions: List[str] = field(default_factory=list)
    safety_questions: List[str] = field(default_factory=list)
    required_evidence: List[str] = field(default_factory=list)
    jurisdiction: str = _UNKNOWN
    blocked_until_review: bool = True
    jurisdiction_unknown: bool = True
    no_legal_conclusion: bool = True
    no_safety_clearance_without_evidence: bool = True
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(
            self, "blocked_until_review", "no_legal_conclusion", "no_safety_clearance_without_evidence",
            "strong_approval_required",
        )
        object.__setattr__(self, "jurisdiction_unknown", self.jurisdiction == _UNKNOWN)
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ControlledEnvironmentPreview:
    prepare_only: bool = True
    environment_name: str = _UNKNOWN
    isolation_level: str = _UNKNOWN
    allowed_capabilities: List[str] = field(default_factory=list)
    blocked_capabilities: List[str] = field(default_factory=list)
    human_supervision_required: bool = True
    emergency_stop_available: bool = True
    audit_enabled_preview: bool = True
    rollback_available: bool = True
    would_start_environment: bool = False
    would_execute: bool = False

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(
            self, "human_supervision_required", "emergency_stop_available", "audit_enabled_preview",
            "rollback_available",
        )
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ImmediateStopPreview:
    prepare_only: bool = True
    stop_name: str = _UNKNOWN
    stop_scope: List[str] = field(default_factory=list)
    stop_triggers: List[str] = field(default_factory=list)
    manual_stop_required: bool = True
    automatic_stop_preview: List[str] = field(default_factory=list)
    would_register_stop_hook: bool = False
    would_stop_real_device: bool = False
    would_execute: bool = False
    required_before_activation: bool = True

    def __post_init__(self) -> None:
        _safe_common(self)
        _force_true(self, "manual_stop_required", "required_before_activation")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MoonshotAuditRollbackPreview:
    prepare_only: bool = True
    subject: str = _UNKNOWN
    audit_events_preview: List[str] = field(default_factory=list)
    rollback_plan: List[str] = field(default_factory=list)
    evidence_required: List[str] = field(default_factory=list)
    would_write_audit: bool = False
    would_persist: bool = False
    would_rollback_real_system: bool = False
    audit_required: bool = True
    rollback_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self)
        if not isinstance(self.rollback_plan, list):
            object.__setattr__(self, "rollback_plan", [_safe_text(self.rollback_plan)])
        _force_true(self, "audit_required", "rollback_required")
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MonetizationAdvantageReviewPreview:
    prepare_only: bool = True
    idea_name: str = _UNKNOWN
    claimed_advantage: str = _UNKNOWN
    practical_value: str = _UNKNOWN
    spectacle_risk: str = _UNKNOWN
    revenue_or_efficiency_path: str = _UNKNOWN
    evidence_needed: List[str] = field(default_factory=list)
    no_fake_roi: bool = True
    reject_if_only_spectacle: bool = True
    rejected_as_only_spectacle: bool = False
    would_execute: bool = False
    would_spend_money: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, choices={"spectacle_risk": _RISK_LEVELS})
        _force_true(self, "no_fake_roi", "reject_if_only_spectacle")
        object.__setattr__(
            self,
            "rejected_as_only_spectacle",
            self.spectacle_risk == "high" and self.practical_value == _UNKNOWN and self.revenue_or_efficiency_path == _UNKNOWN,
        )
        _force_safe(self, preserve={"rejected_as_only_spectacle"})

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self, preserve={"rejected_as_only_spectacle"})


@dataclass(frozen=True)
class IdentityImpersonationGuardPreview:
    prepare_only: bool = True
    scenario_name: str = _UNKNOWN
    identity_risk: str = _UNKNOWN
    impersonation_risk: str = _UNKNOWN
    consent_required: bool = True
    prohibited_impersonation_actions: List[str] = field(default_factory=list)
    allowed_safe_summary: str = _UNKNOWN
    would_impersonate: bool = False
    would_create_identity_artifact: bool = False
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, choices={"identity_risk": _RISK_LEVELS, "impersonation_risk": _RISK_LEVELS})
        _force_true(self, "consent_required")
        object.__setattr__(
            self,
            "strong_approval_required",
            self.identity_risk != "none" or self.impersonation_risk != "none",
        )
        if not self.prohibited_impersonation_actions:
            object.__setattr__(self, "prohibited_impersonation_actions", ["Identity impersonation is prohibited."])
        _force_safe(self)

    from_request = classmethod(lambda cls, data: cls(**_select(data, cls)))
    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MoonshotApprovalRequirements:
    prepare_only: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    approval_gateway_called: bool = False
    approval_created: bool = False
    approval_granted: bool = False
    approval_rejected: bool = False
    action_authorized: bool = False
    device_authorized: bool = False

    def __post_init__(self) -> None:
        _force_true(self, "approval_required")
        _force_safe(self, preserve={"strong_approval_required"})

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "MoonshotApprovalRequirements":
        source = dict(data or {})
        risk_names = (
            "physical", "legal", "identity", "money", "safety", "camera", "microphone", "screen",
            "surveillance", "external_device", "robotics", "drones", "ar_overlay",
        )
        return cls(strong_approval_required=any(bool(source.get(name) or source.get(f"{name}_requested")) for name in risk_names))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self, preserve={"strong_approval_required"})


_FORCED_FALSE = {
    "future_moonshot_available", "smart_glasses_enabled", "ar_overlay_enabled", "robotics_enabled",
    "drones_enabled", "physical_world_automation_enabled", "deep_simulation_enabled", "camera_enabled",
    "microphone_enabled", "screen_capture_enabled", "surveillance_enabled", "identity_impersonation_enabled",
    "illegal_action_enabled", "implicit_permission_enabled", "external_calls_enabled", "secrets_access_enabled",
    "hermes_called", "approval_gateway_called", "execution_enabled", "persistence_enabled", "camera_required",
    "microphone_required", "would_execute", "would_connect_device", "would_modify_physical_world",
    "would_activate_camera", "would_activate_microphone", "would_render_overlay", "would_capture_screen",
    "would_use_camera", "would_act_on_overlay", "would_send_command", "would_move_device",
    "would_run_simulation", "would_execute_real_action", "would_control_device", "would_modify_environment",
    "would_start_environment", "would_register_stop_hook", "would_stop_real_device", "would_write_audit",
    "would_persist", "would_rollback_real_system", "would_spend_money", "would_impersonate",
    "would_create_identity_artifact", "approval_created", "approval_granted", "approval_rejected",
    "action_authorized", "device_authorized",
}


def _force_safe(value: Any, *, preserve: Optional[set[str]] = None) -> None:
    preserve = preserve or set()
    object.__setattr__(value, "prepare_only", True)
    for name in _FORCED_FALSE - preserve:
        if name in value.__dataclass_fields__:
            object.__setattr__(value, name, False)


def _force_all_true(value: Any) -> None:
    for name in value.__dataclass_fields__:
        object.__setattr__(value, name, True)


def _force_true(value: Any, *names: str) -> None:
    for name in names:
        object.__setattr__(value, name, True)


def _serialize(value: Any, *, preserve: Optional[set[str]] = None) -> Dict[str, Any]:
    preserve = preserve or set()
    result = {
        name: list(item) if isinstance(item := getattr(value, name), list) else item
        for name in value.__dataclass_fields__
    }
    result["prepare_only"] = True
    for name in _FORCED_FALSE - preserve:
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
            object.__setattr__(value, name, _choice(item, choices[name]) if name in choices else _safe_text(item))


def _safe_text(value: Any) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return _UNKNOWN
    if any(marker in text.lower() for marker in _SENSITIVE_MARKERS):
        return _REDACTED
    return text[:500]


def _safe_list(value: Any) -> List[str]:
    items = value if isinstance(value, list) else []
    return [_safe_text(item) for item in items[:100]]


def _choice(value: Any, choices: set[str]) -> str:
    text = str(value or "").strip().lower()
    return text if text in choices else _UNKNOWN


def _select(data: Optional[Dict[str, Any]], cls: Any) -> Dict[str, Any]:
    source = dict(data or {})
    blocked = _FORCED_FALSE | {"prepare_only", "approval_required", "strong_approval_required", "rejected_as_only_spectacle"}
    return {
        name: source[name]
        for name in cls.__dataclass_fields__
        if name not in blocked and name in source and source[name] is not None
    }


def _risk_choices(value: Any) -> Dict[str, set[str]]:
    return {name: _RISK_LEVELS for name in value.__dataclass_fields__ if name.endswith("_risk")}


def _has_material_risk(value: Any) -> bool:
    physical_types = {"smart_glasses", "ar_overlay", "robotics", "drones", "physical_automation"}
    return getattr(value, "capability_type", _UNKNOWN) in physical_types or any(
        getattr(value, name) != "none"
        for name in value.__dataclass_fields__
        if name in {"safety_risk", "legal_risk", "identity_risk"}
    )
