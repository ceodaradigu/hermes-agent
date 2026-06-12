from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Mark2ReleaseCandidateStatus:
    current_mark: str = "Mark 2"
    release_candidate: bool = True
    release_candidate_name: str = "Mark 2 Release Candidate"
    completed_macro_prs: List[str] = field(default_factory=lambda: [
        "Mark 2 Macro 1 Local Daemon / Wake / Voice Approval",
        "Mark 2 Macro 2 Real Tool Execution",
        "Mark 2 Macro 3 Visual Command Center / Human Approval / Agent Operations Dashboard",
        "Mark 2 Macro 4 Real Deploy / Stripe / Email / External Ops / AI CLI Adapters",
    ])
    mark_2_complete_as_release_candidate: bool = True
    mark_2_not_full_autonomy: bool = True
    mark_2_real_execution_default_enabled: bool = False
    control_plane_ready: bool = True
    approval_gates_ready: bool = True
    dashboard_ready: bool = True
    local_daemon_ready: bool = True
    voice_approval_ready: bool = True
    tool_execution_candidates_ready: bool = True
    external_ops_candidates_ready: bool = True
    ai_cli_adapters_preview_ready: bool = True
    cost_visibility_ready: bool = True
    audit_ready: bool = True
    runbook_ready: bool = True
    dangerous_route_audit_ready: bool = True
    e2e_prepare_only_smoke_ready: bool = True
    restrictions_are_approval_gates: bool = True
    wake_phrase_is_permission: bool = False
    voice_can_approve: bool = True
    production_requires_strong_double_and_rollback: bool = True
    money_requires_strong_double_or_triple: bool = True
    real_deploy_enabled: bool = False
    stripe_live_enabled: bool = False
    email_send_enabled: bool = False
    domain_publish_enabled: bool = False
    codex_cli_real_invocation_enabled: bool = False
    claude_code_real_invocation_enabled: bool = False
    claude_cowork_real_invocation_enabled: bool = False
    api_fallback_real_invocation_enabled: bool = False
    external_network_enabled: bool = False
    access_material_enabled: bool = False
    no_fake_costs: bool = True
    next_recommended_mark: str = "Mark 3"
    next_recommended_work: str = "Mark 3 planning or Mark 2 production pilot with explicit manual setup"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mark2Capability:
    capability_id: str
    status: str
    execution_default: str = "disabled"
    approval_required: bool = True
    strong_approval_required: bool = False
    double_confirmation_required: bool = False
    triple_confirmation_supported: bool = True
    real_side_effects_possible_after_valid_approval: bool = True
    real_side_effects_enabled_now: bool = False
    manual_setup_required: bool = False
    risk_level: str = "medium"
    summary: str = "Governed control-plane capability."
    limitations: List[str] = field(default_factory=lambda: ["Real side effects are disabled by default."])
    next_safe_step: str = "Review scope, approvals, audit, and stop or rollback plan."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark2CapabilityMatrix:
    _READ_ONLY = {
        "visual_command_center",
        "human_approval_console",
        "agent_operations_dashboard",
        "cost_usage_dashboard",
        "ai_cli_session_audit",
        "operational_runbook",
        "e2e_prepare_only_smoke",
    }
    _MANUAL_SETUP = {
        "local_daemon",
        "wake_listener",
        "deploy_candidate_operations",
        "stripe_candidate_operations",
        "email_candidate_operations",
        "domain_candidate_operations",
        "codex_cli_adapter_preview",
        "claude_code_adapter_preview",
        "claude_cowork_adapter_preview",
        "api_fallback_adapter_preview",
    }
    _HIGH = {
        "voice_approval_channel",
        "filesystem_candidate_execution",
        "github_candidate_execution",
        "browser_candidate_execution",
        "external_api_candidate_execution",
        "email_candidate_operations",
        "codex_cli_adapter_preview",
        "claude_code_adapter_preview",
        "claude_cowork_adapter_preview",
        "api_fallback_adapter_preview",
        "routine_execution_bridge",
    }
    _CRITICAL = {
        "deploy_candidate_operations",
        "stripe_candidate_operations",
        "domain_candidate_operations",
    }
    _CAPABILITIES = (
        "local_daemon",
        "desktop_runtime",
        "wake_listener",
        "voice_approval_channel",
        "filesystem_candidate_execution",
        "github_candidate_execution",
        "browser_candidate_execution",
        "external_api_candidate_execution",
        "visual_command_center",
        "human_approval_console",
        "agent_operations_dashboard",
        "cost_usage_dashboard",
        "deploy_candidate_operations",
        "stripe_candidate_operations",
        "email_candidate_operations",
        "domain_candidate_operations",
        "codex_cli_adapter_preview",
        "claude_code_adapter_preview",
        "claude_cowork_adapter_preview",
        "api_fallback_adapter_preview",
        "routine_execution_bridge",
        "ai_cli_session_audit",
        "operational_runbook",
        "e2e_prepare_only_smoke",
    )

    def build(self) -> List[Mark2Capability]:
        items = []
        for capability_id in self._CAPABILITIES:
            read_only = capability_id in self._READ_ONLY
            critical = capability_id in self._CRITICAL
            high = capability_id in self._HIGH
            manual = capability_id in self._MANUAL_SETUP
            status = "requires_manual_setup" if manual else "ready"
            items.append(Mark2Capability(
                capability_id=capability_id,
                status=status,
                approval_required=not read_only,
                strong_approval_required=critical or high,
                double_confirmation_required=critical,
                real_side_effects_possible_after_valid_approval=not read_only,
                manual_setup_required=manual,
                risk_level="critical" if critical else "high" if high else "low" if read_only else "medium",
                summary=f"{capability_id.replace('_', ' ')} is governed and available in Mark 2 RC.",
                limitations=["No real side effects are enabled now.", "Manual provider or local setup may still be required."] if manual else ["No real side effects are enabled now."],
            ))
        return items

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 2",
            "release_candidate": True,
            "real_side_effects_enabled_now": False,
            "capabilities": [item.to_dict() for item in self.build()],
        }


class Mark2ReadinessMatrix:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 2",
            "release_candidate_readiness": "ready_as_controlled_release_candidate",
            "full_autonomy_readiness": "blocked",
            "production_readiness": "pilot_ready_after_manual_setup_and_valid_approvals",
            "readiness": {
                "safety_readiness": "ready",
                "approval_readiness": "ready",
                "voice_readiness": "requires_manual_setup",
                "dashboard_readiness": "ready",
                "tool_execution_readiness": "partial",
                "external_ops_readiness": "requires_manual_setup",
                "ai_cli_readiness": "requires_manual_setup",
                "cost_readiness": "ready",
                "audit_readiness": "ready",
                "docs_readiness": "ready",
                "test_readiness": "ready",
                "production_readiness": "pilot_ready_after_manual_setup_and_valid_approvals",
            },
            "not_ready_for": ["free autonomy", "default real execution", "unapproved production or money operations"],
        }


def mark_2_release_candidate_markers() -> Dict[str, Any]:
    return {
        "mark_2_release_candidate_available": True,
        "mark_2_release_candidate": True,
        "mark_2_macro_1_complete": True,
        "mark_2_macro_2_complete": True,
        "mark_2_macro_3_complete": True,
        "mark_2_macro_4_complete": True,
        "mark_2_control_plane_ready": True,
        "mark_2_not_full_autonomy": True,
        "mark_2_real_execution_disabled_by_default": True,
        "mark_2_dangerous_route_audit_available": True,
        "mark_2_approval_path_audit_available": True,
        "mark_2_e2e_prepare_only_smoke_available": True,
        "mark_2_operational_runbook_available": True,
        "mark_2_capability_matrix_available": True,
        "mark_2_readiness_matrix_available": True,
        "production_pilot_requires_manual_setup_and_valid_approvals": True,
        "no_fake_costs": True,
        "access_material_disabled_by_default": True,
        "external_network_disabled_by_default": True,
        "wake_phrase_is_permission_false": True,
        "voice_can_approve": True,
        "restrictions_are_approval_gates": True,
        "mark_3_planned": True,
        "mark_2_next_recommended_mark": "Mark 3",
    }
