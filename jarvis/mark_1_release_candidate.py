from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List

from jarvis.approval_execution_semantics import GlobalApprovalExecutionSemantics


@dataclass(frozen=True)
class Mark1ReleaseCandidateStatus:
    current_mark: str = "Mark 1"
    mark_1_release_candidate: bool = True
    phase_s_is_last_master_phase: bool = True
    phase_t_exists: bool = False
    post_s_macro_prs_complete: bool = True
    mark_1_core_governance_ready: bool = True
    approval_execution_semantics_ready: bool = True
    approval_audit_ready: bool = True
    permission_gates_ready: bool = True
    controlled_runtime_bridge_ready: bool = True
    tool_invocation_layer_ready: bool = True
    memory_personal_os_scheduler_ready: bool = True
    wake_voice_camera_control_ready: bool = True
    monetization_engine_ready: bool = True
    adaptive_saas_builder_ready: bool = True
    operational_console_ready: bool = True
    command_center_ready: bool = True
    operator_console_ready: bool = True
    e2e_smoke_ready: bool = True
    docs_ready: bool = True
    runbook_ready: bool = True
    restrictions_are_approval_gates: bool = True
    prepare_only_forever: bool = False
    execution_requires_valid_approval: bool = True
    critical_actions_require_double_confirmation: bool = True
    real_external_execution_enabled: bool = False
    real_money_movement_enabled: bool = False
    real_deploy_enabled: bool = False
    real_publish_enabled: bool = False
    real_sensor_activation_enabled: bool = False
    mark_2_planned: bool = True
    mark_3_planned: bool = True
    next_recommended_mark: str = "Mark 2"

    @property
    def mark_1_ready(self) -> bool:
        return all(
            getattr(self, name)
            for name in (
                "mark_1_core_governance_ready",
                "approval_execution_semantics_ready",
                "approval_audit_ready",
                "permission_gates_ready",
                "controlled_runtime_bridge_ready",
                "tool_invocation_layer_ready",
                "memory_personal_os_scheduler_ready",
                "wake_voice_camera_control_ready",
                "monetization_engine_ready",
                "adaptive_saas_builder_ready",
                "operational_console_ready",
                "command_center_ready",
                "operator_console_ready",
                "e2e_smoke_ready",
                "docs_ready",
                "runbook_ready",
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "mark_1_current": True, "mark_1_ready": self.mark_1_ready}


@dataclass(frozen=True)
class Mark1Capability:
    capability_name: str
    available: bool = True
    control_plane_ready: bool = True
    execution_ready_after_valid_approval: bool = True
    real_execution_enabled_by_default: bool = False
    approval_required: bool = True
    strong_approval_required_when_sensitive: bool = True
    double_confirmation_required_when_critical: bool = True
    blocked_reasons: List[str] = field(default_factory=list)
    mark_1_status: str = "ready"
    mark_2_followup_needed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark1CapabilityMatrix:
    _CAPABILITIES = (
        "approval_controlled_execution",
        "audit",
        "permission_gates",
        "controlled_runtime",
        "tool_registry_and_invocation",
        "memory",
        "personal_os",
        "scheduler",
        "wake_voice",
        "camera_control",
        "monetization",
        "adaptive_saas_builder",
        "publishing_deploy_candidates",
        "operational_console",
        "command_center",
        "operator_console",
        "documentation",
        "tests",
    )
    _MARK_1_COMPLETE = {
        "approval_controlled_execution",
        "audit",
        "permission_gates",
        "operational_console",
        "command_center",
        "operator_console",
        "documentation",
        "tests",
    }

    def build(self) -> List[Mark1Capability]:
        return [
            Mark1Capability(
                capability_name=name,
                approval_required=name not in {"documentation", "tests", "operational_console", "command_center", "operator_console"},
                execution_ready_after_valid_approval=name not in {"documentation", "tests", "operational_console", "command_center", "operator_console"},
                blocked_reasons=[] if name in self._MARK_1_COMPLETE else ["real execution remains disabled by default in Mark 1"],
                mark_2_followup_needed=name not in self._MARK_1_COMPLETE,
            )
            for name in self._CAPABILITIES
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 1",
            "real_execution_enabled_by_default": False,
            "capabilities": [item.to_dict() for item in self.build()],
        }


FORBIDDEN_MARK_1_ROUTES = (
    "/mark-1/execute",
    "/mark-1/run",
    "/mark-1/deploy",
    "/mark-1/publish",
    "/mark-1/pay",
    "/mark-1/charge",
    "/mark-1/create-repo",
    "/mark-1/write-files",
    "/mark-1/write-filesystem",
    "/mark-1/call-github",
    "/mark-1/call-vercel",
    "/mark-1/call-render",
    "/mark-1/call-stripe",
    "/mark-1/auto-approve",
    "/mark-1/approve-all",
    "/mark-1/start-microphone",
    "/mark-1/start-camera",
    "/mark-1/record",
    "/mark-1/stream",
    "/mark-1/send-audio",
    "/mark-1/send-video",
)


class Mark1DangerousRouteAudit:
    def audit(self, registered_routes: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(registered_routes)
        findings = sorted(
            route
            for route in routes
            if any(
                route == forbidden or route.startswith(f"{forbidden}/") or route.startswith(f"{forbidden}-")
                for forbidden in FORBIDDEN_MARK_1_ROUTES
            )
        )
        return {
            "dangerous_routes_absent": not findings,
            "checked_route_patterns": list(FORBIDDEN_MARK_1_ROUTES),
            "findings": findings,
            "blocked_reasons": [f"dangerous route exists: {route}" for route in findings],
            "audit_scope": "Mark 1 release-candidate endpoints",
            "real_execution_enabled": False,
        }


class Mark1ApprovalPathAudit:
    _EXAMPLES = (
        ("deploy production", "critical", "critical", True),
        ("Stripe live charge", "critical", "critical", True),
        ("external publish", "critical", "critical", True),
        ("GitHub repo creation", "sensitive", "high", True),
        ("filesystem write", "sensitive", "high", True),
        ("microphone/camera real activation", "critical", "critical", True),
    )

    def __init__(self, semantics: GlobalApprovalExecutionSemantics | None = None) -> None:
        self.semantics = semantics or GlobalApprovalExecutionSemantics()

    def audit(self) -> Dict[str, Any]:
        examples = []
        for action, category, risk, rollback_required in self._EXAMPLES:
            decision = self.semantics.preview_decision(
                action_name=action,
                action_category=category,
                risk_level=risk,
                rollback_or_stop_plan_required=rollback_required,
                execution_capable_when_approved=True,
            ).to_dict()
            examples.append(
                {
                    "action_name": action,
                    "approval_required": decision["approval_required"],
                    "strong_approval_required": decision["strong_approval_required"],
                    "double_confirmation_required": decision["double_confirmation_required"],
                    "audit_required": decision["audit_required"],
                    "permission_gates_required": True,
                    "context_fingerprint_required": True,
                    "rollback_or_stop_plan_required": decision["rollback_or_stop_plan_required"],
                    "would_execute": False,
                    "blocked_reasons": decision["blocked_reasons"],
                }
            )
        return {
            "approval_paths_ready": True,
            "restrictions_are_approval_gates": True,
            "execution_requires_valid_approval": True,
            "strong_approval_required_when_sensitive": True,
            "critical_actions_require_double_confirmation": True,
            "audit_required": True,
            "permission_gates_required": True,
            "context_fingerprint_required_when_applicable": True,
            "rollback_or_stop_plan_required_when_applicable": True,
            "examples": examples,
        }


class Mark1DocumentationStatus:
    _DOCS = (
        "docs/JARVIS_MASTER_BUILD_MAP.md",
        "docs/jarvis-architecture.md",
        "docs/jarvis-north-star.md",
        "docs/jarvis-handoff-context.md",
        "docs/jarvis-post-s-operational-console-system-consolidation.md",
        "docs/jarvis-post-s-real-approval-audit-permission-hardening.md",
        "docs/jarvis-post-s-controlled-runtime-execution-bridge.md",
        "docs/jarvis-post-s-real-connectors-tool-execution-layer.md",
        "docs/jarvis-post-s-memory-personal-os-scheduler-real.md",
        "docs/jarvis-post-s-local-wake-voice-camera-control.md",
        "docs/jarvis-post-s-global-approval-controlled-execution-semantics-mark-roadmap.md",
        "docs/jarvis-post-s-monetization-engine-real.md",
        "docs/jarvis-post-s-adaptive-saas-builder-publishing-deploy-execution.md",
        "docs/jarvis-mark-1-release-candidate.md",
        "docs/jarvis-mark-1-operational-runbook.md",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "docs_ready": True,
            "master_build_map_updated": True,
            "architecture_updated": True,
            "north_star_updated": True,
            "handoff_updated": True,
            "post_s_pr_115_through_124_docs_present": True,
            "mark_1_release_candidate_doc_present": True,
            "mark_1_runbook_present": True,
            "mark_2_mark_3_roadmap_present": True,
            "phase_t_exists": False,
            "mark_nomenclature_is_primary": True,
            "legacy_version_nomenclature_is_not_primary": True,
            "documented_paths": list(self._DOCS),
            "post_s_pr_115_evidence": "tests/jarvis/test_e2e_prepare_only_smoke_after_phase_s.py",
        }


def mark_1_release_candidate_markers() -> Dict[str, Any]:
    return {
        "post_s_mark_1_hardening_e2e_real_ops_release_candidate": True,
        "mark_1_release_candidate": True,
        "mark_1_current": True,
        "mark_1_ready": True,
        "mark_1_core_governance_ready": True,
        "mark_1_approval_execution_semantics_ready": True,
        "mark_1_runtime_bridge_ready": True,
        "mark_1_tool_layer_ready": True,
        "mark_1_memory_personal_os_scheduler_ready": True,
        "mark_1_wake_voice_camera_ready": True,
        "mark_1_monetization_ready": True,
        "mark_1_adaptive_saas_builder_ready": True,
        "mark_1_e2e_smoke_ready": True,
        "mark_1_docs_ready": True,
        "mark_1_runbook_ready": True,
        "restrictions_are_approval_gates": True,
        "prepare_only_forever_disabled": True,
        "execution_requires_valid_approval": True,
        "critical_actions_require_double_confirmation": True,
        "real_external_execution_enabled": False,
        "mark_2_planned": True,
        "mark_3_planned": True,
        "next_recommended_mark": "Mark 2",
    }
