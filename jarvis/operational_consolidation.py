from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple


GLOBAL_READINESS = "foundation_complete_prepare_only"
NEXT_MACRO_PR = "Post-S Macro 5 - Memory, Personal OS & Scheduler Real"
NEXT_RECOMMENDED_MACRO_PR = "Post-S Macro 6 - Voice / Wake / Camera Controlled Runtime"


@dataclass(frozen=True)
class OperationalSystemStatus:
    prepare_only: bool = True
    phase_range: str = "A-S"
    last_master_phase: str = "Phase S"
    no_phase_t: bool = True
    runtime_execution_enabled: bool = False
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    persistence_enabled: bool = False
    operator_console_available: bool = True
    command_center_available: bool = True
    smoke_validation_available: bool = True
    approval_hardening_available: bool = True
    approval_audit_available: bool = True
    strong_approval_policy_available: bool = True
    permission_gates_available: bool = True
    controlled_runtime_bridge_available: bool = True
    dry_run_required: bool = True
    sandbox_required: bool = True
    rollback_required_for_side_effects: bool = True
    permission_gates_enforced: bool = True
    approval_gates_enforced: bool = True
    strong_approval_enforced: bool = True
    safe_to_execute_is_readiness_only: bool = True
    tool_registry_available: bool = True
    connector_contracts_available: bool = True
    tool_invocation_preview_available: bool = True
    real_connectors_control_plane_available: bool = True
    tool_execution_enabled: bool = False
    credentials_enabled: bool = False
    filesystem_writes_enabled: bool = False
    github_actions_enabled: bool = False
    browser_actions_enabled: bool = False
    api_calls_enabled: bool = False
    controlled_runtime_bridge_required: bool = True
    safe_to_invoke_is_readiness_only: bool = True
    approved_memory_records_available: bool = True
    personal_os_control_plane_available: bool = True
    scheduler_control_plane_available: bool = True
    daily_review_preview_available: bool = True
    weekly_review_preview_available: bool = True
    stop_controls_available: bool = True
    audit_summary_available: bool = True
    memory_autoload_enabled: bool = False
    memory_auto_activation_enabled: bool = False
    scheduler_worker_enabled: bool = False
    watcher_enabled: bool = False
    external_sources_enabled: bool = False
    private_sources_enabled: bool = False
    scheduler_execution_enabled: bool = False
    notifications_enabled: bool = False
    tool_invocation_from_scheduler_enabled: bool = False
    memory_is_not_permission: bool = True
    scheduler_due_is_not_execution: bool = True
    next_recommended_macro_pr: str = NEXT_RECOMMENDED_MACRO_PR
    global_readiness: str = GLOBAL_READINESS
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "phase_range", "A-S")
        object.__setattr__(self, "last_master_phase", "Phase S")
        object.__setattr__(self, "no_phase_t", True)
        for name in (
            "approval_hardening_available",
            "approval_audit_available",
            "strong_approval_policy_available",
            "permission_gates_available",
            "controlled_runtime_bridge_available",
            "dry_run_required",
            "sandbox_required",
            "rollback_required_for_side_effects",
            "permission_gates_enforced",
            "approval_gates_enforced",
            "strong_approval_enforced",
            "safe_to_execute_is_readiness_only",
            "tool_registry_available",
            "connector_contracts_available",
            "tool_invocation_preview_available",
            "real_connectors_control_plane_available",
            "controlled_runtime_bridge_required",
            "safe_to_invoke_is_readiness_only",
            "approved_memory_records_available",
            "personal_os_control_plane_available",
            "scheduler_control_plane_available",
            "daily_review_preview_available",
            "weekly_review_preview_available",
            "stop_controls_available",
            "audit_summary_available",
            "memory_is_not_permission",
            "scheduler_due_is_not_execution",
        ):
            object.__setattr__(self, name, True)
        for name in (
            "runtime_execution_enabled",
            "execution_enabled",
            "side_effects_enabled",
            "external_calls_enabled",
            "secrets_access_enabled",
            "hermes_called",
            "approval_gateway_called",
            "persistence_enabled",
            "tool_execution_enabled",
            "credentials_enabled",
            "filesystem_writes_enabled",
            "github_actions_enabled",
            "browser_actions_enabled",
            "api_calls_enabled",
            "memory_autoload_enabled",
            "memory_auto_activation_enabled",
            "scheduler_worker_enabled",
            "watcher_enabled",
            "external_sources_enabled",
            "private_sources_enabled",
            "scheduler_execution_enabled",
            "notifications_enabled",
            "tool_invocation_from_scheduler_enabled",
        ):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "next_recommended_macro_pr", NEXT_RECOMMENDED_MACRO_PR)
        object.__setattr__(self, "global_readiness", GLOBAL_READINESS)
        object.__setattr__(self, "warnings", list(self.warnings))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilitySummary:
    name: str
    category: str
    phase_or_source: str
    prepare_only: bool = True
    status: str = GLOBAL_READINESS
    blocked: bool = True
    approval_required: bool = False
    strong_approval_required: bool = False
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    external_calls_enabled: bool = False
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "status", GLOBAL_READINESS)
        object.__setattr__(self, "blocked", True)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "side_effects_enabled", False)
        object.__setattr__(self, "external_calls_enabled", False)
        object.__setattr__(self, "notes", list(self.notes))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityReadiness:
    name: str
    ready_for_preview: bool
    ready_for_dry_run: bool
    ready_for_real_execution: bool
    missing_requirements: List[str]
    approval_requirements: List[str]
    risk_level: str
    next_safe_step: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ready_for_real_execution", False)
        object.__setattr__(self, "missing_requirements", list(self.missing_requirements))
        object.__setattr__(self, "approval_requirements", list(self.approval_requirements))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SafetyBoundarySummary:
    prepare_only: bool = True
    no_execution: bool = True
    no_production: bool = True
    no_payments_movement: bool = True
    no_credential_access: bool = True
    no_external_calls_by_default: bool = True
    no_camera_by_default: bool = True
    no_microphone_by_default: bool = True
    no_screen_capture_by_default: bool = True
    no_camera_microphone_screen_by_default: bool = True
    no_physical_world_automation: bool = True
    no_memory_activation_unless_explicitly_approved: bool = True
    no_scheduler_execution_unless_approved: bool = True
    no_deployment_unless_strong_approval: bool = True
    blocked_actions: List[str] = field(
        default_factory=lambda: [
            "real execution",
            "production changes",
            "payments movement",
            "credential access",
            "external calls",
            "camera, microphone, or screen capture",
            "physical-world automation",
            "unapproved memory activation",
            "unapproved scheduler execution",
            "deployment without strong approval",
        ]
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in (
            "no_execution",
            "no_production",
            "no_payments_movement",
            "no_credential_access",
            "no_external_calls_by_default",
            "no_camera_by_default",
            "no_microphone_by_default",
            "no_screen_capture_by_default",
            "no_camera_microphone_screen_by_default",
            "no_physical_world_automation",
            "no_memory_activation_unless_explicitly_approved",
            "no_scheduler_execution_unless_approved",
            "no_deployment_unless_strong_approval",
        ):
            object.__setattr__(self, name, True)
        object.__setattr__(self, "blocked_actions", list(self.blocked_actions))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityRegistry:
    prepare_only: bool = True
    capabilities: List[CapabilitySummary] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "capabilities", list(self.capabilities))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "capabilities": [item.to_dict() for item in self.capabilities],
        }


@dataclass(frozen=True)
class ReadinessMatrix:
    prepare_only: bool = True
    readiness_matrix: List[CapabilityReadiness] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        object.__setattr__(self, "readiness_matrix", list(self.readiness_matrix))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "readiness_matrix": [item.to_dict() for item in self.readiness_matrix],
        }


_CAPABILITY_SPECS: Tuple[Tuple[str, str, str, bool, bool, str], ...] = (
    ("mission_core", "command_center", "Phase A", True, False, "Mission contracts exist; real mission creation and execution remain outside this view."),
    ("approvals_policy", "command_center", "Phases B-C", True, True, "Policy and approval contracts exist; no real approval is created here."),
    ("hermes_bridge", "command_center", "Phase C", True, False, "Hermes payloads can be prepared; Hermes is never called here."),
    ("command_center", "command_center", "Phase D", False, False, "Command Center is available as a prepare-only system map."),
    ("operator_console", "operator_console", "Phase G", False, False, "Operator Console is available as a read-only consolidated view."),
    ("voice", "operator_console", "Phases E-G", True, False, "Voice status and intent previews are visible; microphone and runtime activation remain disabled."),
    ("mobile", "operator_console", "Phase F", True, False, "Mobile companion previews are visible; push and execution remain disabled."),
    ("ambient_vision", "operator_console", "Phase G", True, True, "Vision policy is visible; camera, screen, and surveillance remain disabled."),
    ("multi_device", "operator_console", "Phase H", True, True, "Device topology previews are visible; pairing, sync, and notifications remain disabled."),
    ("sandbox_execution", "operator_console", "Phase I", True, True, "Sandbox command plans and dry runs are available; command execution remains disabled."),
    ("tool_adoption", "operator_console", "Phase J", True, True, "Tool evaluation is available; installation and adoption remain disabled."),
    ("asset_factory", "operator_console", "Phase K", True, False, "Asset plans and packages are previews only; no files are built or published."),
    ("deploy_publishing", "operator_console", "Phase L", True, True, "Publishing readiness is visible; production deployment requires strong approval and is disabled."),
    ("marketing_distribution", "operator_console", "Phase M", True, True, "Campaign plans are previews only; no distribution or budget spend occurs."),
    ("payments_revenue", "operator_console", "Phase N", True, True, "Revenue planning is visible; no payment, refund, or money movement occurs."),
    ("daily_operator", "operator_console", "Phase O", True, False, "Schedules and handoffs are previews only; no scheduler or background worker runs."),
    ("continuous_learning", "operator_console", "Phase P", True, True, "Learning proposals are visible; no code, prompt, dependency, or runtime modification occurs."),
    ("personal_os", "operator_console", "Phase Q", True, True, "Environment intelligence is preview-only; private sources and sensors remain inaccessible."),
    ("advanced_personalization", "operator_console", "Phase R", True, True, "Memory proposals are visible; no memory is persisted or activated."),
    ("future_moonshot", "future_not_activated", "Phase S", True, True, "Moonshot concepts remain future, controlled, and not activated."),
    ("smoke_validation", "system_validation", "Post-S validation", False, False, "End-to-end prepare-only smoke validation is available."),
)

_DRY_RUN_CAPABILITIES = {
    "mission_core",
    "approvals_policy",
    "hermes_bridge",
    "voice",
    "mobile",
    "ambient_vision",
    "multi_device",
    "sandbox_execution",
    "tool_adoption",
    "asset_factory",
    "deploy_publishing",
    "marketing_distribution",
    "payments_revenue",
    "daily_operator",
    "continuous_learning",
    "personal_os",
    "advanced_personalization",
    "future_moonshot",
    "smoke_validation",
}

_HIGH_RISK_CAPABILITIES = {
    "approvals_policy",
    "ambient_vision",
    "multi_device",
    "deploy_publishing",
    "payments_revenue",
    "personal_os",
    "advanced_personalization",
    "future_moonshot",
}


def build_operational_system_status() -> OperationalSystemStatus:
    return OperationalSystemStatus()


def build_capability_registry() -> List[CapabilitySummary]:
    return [
        CapabilitySummary(
            name=name,
            category=category,
            phase_or_source=phase,
            approval_required=approval_required,
            strong_approval_required=strong_approval_required,
            notes=[note, "Real execution is blocked by the post-S prepare-only boundary."],
        )
        for name, category, phase, approval_required, strong_approval_required, note in _CAPABILITY_SPECS
    ]


def build_capability_registry_view() -> CapabilityRegistry:
    return CapabilityRegistry(capabilities=build_capability_registry())


def build_readiness_matrix() -> List[CapabilityReadiness]:
    return [
        CapabilityReadiness(
            name=capability.name,
            ready_for_preview=True,
            ready_for_dry_run=capability.name in _DRY_RUN_CAPABILITIES,
            ready_for_real_execution=False,
            missing_requirements=_missing_requirements(capability),
            approval_requirements=_approval_requirements(capability),
            risk_level="high" if capability.name in _HIGH_RISK_CAPABILITIES else "medium",
            next_safe_step=_next_safe_step(capability),
        )
        for capability in build_capability_registry()
    ]


def build_readiness_matrix_view() -> ReadinessMatrix:
    return ReadinessMatrix(readiness_matrix=build_readiness_matrix())


def build_safety_boundary_summary() -> SafetyBoundarySummary:
    return SafetyBoundarySummary()


def build_command_center_system_map() -> Dict[str, Any]:
    return {
        "prepare_only": True,
        "post_s_operational_consolidation": True,
        "post_s_memory_personal_os_scheduler": "prepare_only",
        "approved_memory_records": "prepare_only",
        "personal_os_control_plane": "prepare_only",
        "scheduler_control_plane": "prepare_only",
        "daily_review_preview": "prepare_only",
        "weekly_review_preview": "prepare_only",
        "stop_controls": "prepare_only",
        "memory_autoload_disabled": "prepare_only",
        "memory_is_not_permission": "prepare_only",
        "scheduler_due_not_execution": "prepare_only",
        "scheduler_worker_disabled": "prepare_only",
        "watchers_disabled": "prepare_only",
        "external_sources_disabled": "prepare_only",
        "notifications_disabled": "prepare_only",
        "global_readiness": GLOBAL_READINESS,
        "system_map": {
            "phase_range": "A-S",
            "last_master_phase": "Phase S",
            "no_phase_t": True,
            "operator_console": "read_only_consolidated_view",
            "command_center": "prepare_only_system_map",
            "future_capabilities": "not_activated",
            "post_s_approval_hardening": "prepare_only",
            "strong_approval_policy": "prepare_only",
            "approval_audit": "prepare_only",
            "permission_gates": "prepare_only",
            "context_fingerprint": "prepare_only",
            "side_effect_gate_readiness": "prepare_only",
            "post_s_controlled_runtime_bridge": "prepare_only",
            "dry_run_bridge": "prepare_only",
            "sandbox_requirements": "prepare_only",
            "rollback_plan": "prepare_only",
            "runtime_permission_gate": "prepare_only",
            "runtime_approval_gate": "prepare_only",
            "safe_to_execute_readiness_only": "prepare_only",
            "runtime_execution_disabled": "prepare_only",
            "post_s_real_connectors_tool_layer": "prepare_only",
            "tool_registry": "prepare_only",
            "connector_contracts": "prepare_only",
            "tool_invocation_preview": "prepare_only",
            "connector_permission_gate": "prepare_only",
            "controlled_runtime_required": "prepare_only",
            "safe_to_invoke_readiness_only": "prepare_only",
            "tool_execution_disabled": "prepare_only",
            "external_calls_disabled": "prepare_only",
            "access_material_disabled": "prepare_only",
            "post_s_memory_personal_os_scheduler": "prepare_only",
            "approved_memory_records": "prepare_only",
            "personal_os_control_plane": "prepare_only",
            "scheduler_control_plane": "prepare_only",
            "daily_review_preview": "prepare_only",
            "weekly_review_preview": "prepare_only",
            "stop_controls": "prepare_only",
            "memory_autoload_disabled": "prepare_only",
            "memory_is_not_permission": "prepare_only",
            "scheduler_due_not_execution": "prepare_only",
            "scheduler_worker_disabled": "prepare_only",
            "watchers_disabled": "prepare_only",
            "external_sources_disabled": "prepare_only",
            "notifications_disabled": "prepare_only",
        },
        "safe_next_steps": [
            "review consolidated capability and readiness evidence",
            NEXT_RECOMMENDED_MACRO_PR,
            "retain prepare-only defaults until tool invocation is explicitly reviewed and enabled",
        ],
    }


def build_operational_console_summary() -> Dict[str, Any]:
    boundaries = build_safety_boundary_summary()
    return {
        "prepare_only": True,
        "operational_status": build_operational_system_status().to_dict(),
        "capabilities_summary": [item.to_dict() for item in build_capability_registry()],
        "readiness_matrix": [item.to_dict() for item in build_readiness_matrix()],
        "safety_boundaries": boundaries.to_dict(),
        "pending_macro_work": [
            NEXT_RECOMMENDED_MACRO_PR,
            "runtime execution bridge only after explicit approval and permission gate validation",
            "future opt-in voice, camera, external tools, and physical-world work",
        ],
        "next_recommended_macro_pr": NEXT_RECOMMENDED_MACRO_PR,
        "blocked_actions": list(boundaries.blocked_actions),
        "visible_reasons": [
            "Phase A-Phase S are foundation-complete, not runtime-enabled.",
            "No Phase T exists or is implied.",
            "Approval, audit, permission, sandbox, dry-run, and rollback gates precede real execution.",
            "Post-S Macro 4 provides connector and tool invocation readiness without enabling execution.",
            "Post-S Macro 5 provides approved-memory, Personal OS, scheduler, review, and stop-control previews without autoload or execution.",
        ],
        "command_center": build_command_center_system_map(),
    }


def _approval_requirements(capability: CapabilitySummary) -> List[str]:
    requirements = []
    if capability.approval_required:
        requirements.append("explicit operator approval")
    if capability.strong_approval_required:
        requirements.append("strong approval")
    return requirements or ["none for read-only preview"]


def _missing_requirements(capability: CapabilitySummary) -> List[str]:
    requirements = [
        "controlled runtime execution bridge security review",
        "explicit runtime enablement decision",
        "verified rollback and production safety evidence",
    ]
    if capability.strong_approval_required:
        requirements.append("strong approval challenge and verification")
    return requirements


def _next_safe_step(capability: CapabilitySummary) -> str:
    if capability.name == "smoke_validation":
        return "Keep running the post-S prepare-only smoke suite."
    if capability.category == "future_not_activated":
        return "Keep the capability unactivated and review it only in controlled previews."
    return f"Inspect {capability.name} through read-only previews and preserve prepare-only defaults."
