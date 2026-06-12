from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from jarvis.agent_operations_dashboard import build_agent_operations_dashboard
from jarvis.agent_session_audit import build_audit_timeline
from jarvis.ai_coding_session_control import build_ai_coding_sessions
from jarvis.cost_usage_dashboard import build_cost_usage_dashboard
from jarvis.human_approval_console import build_human_approval_console
from jarvis.model_tool_router import build_model_tool_router_preview
from jarvis.worktree_execution_guard import DiffTestReviewPanel, WorktreeExecutionGuardPanel


NEXT_RECOMMENDED_MACRO_PR = "Mark 2 Macro 4 — Real Deploy, Stripe, Email, External Operations & AI CLI Adapters"


@dataclass(frozen=True)
class VisualCommandCenterStatus:
    current_mark: str = "Mark 2"
    mark_2_macro: str = "Mark 2 Macro 3"
    visual_command_center_available: bool = True
    human_approval_console_available: bool = True
    agent_operations_dashboard_available: bool = True
    ai_coding_session_control_available: bool = True
    cost_usage_dashboard_available: bool = True
    risk_panel_available: bool = True
    audit_timeline_available: bool = True
    worktree_guard_panel_available: bool = True
    diff_test_review_panel_available: bool = True
    kill_switch_visible: bool = True
    stop_control_visible: bool = True
    voice_approval_visible: bool = True
    text_approval_visible: bool = True
    real_frontend_enabled: bool = False
    dashboard_data_endpoints_available: bool = True
    control_plane_only: bool = True
    real_agent_execution_enabled: bool = False
    real_ai_cli_invocation_enabled: bool = False
    codex_cli_real_invocation_enabled: bool = False
    claude_code_real_invocation_enabled: bool = False
    claude_cowork_real_invocation_enabled: bool = False
    api_fallback_real_invocation_enabled: bool = False
    external_network_enabled: bool = False
    access_material_enabled: bool = False
    access_material_disabled_by_default: bool = True
    restrictions_are_approval_gates: bool = True
    wake_phrase_is_permission: bool = False
    voice_can_approve: bool = True
    no_fake_costs: bool = True
    next_recommended_macro_pr: str = NEXT_RECOMMENDED_MACRO_PR

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DashboardPanel:
    panel_id: str
    title: str
    status: str
    risk_level: str
    summary: str
    data_sources: List[str] = field(default_factory=list)
    actions_available: List[str] = field(default_factory=lambda: ["inspect"])
    actions_blocked: List[str] = field(default_factory=lambda: ["real execution"])
    requires_approval: bool = False
    refresh_mode: str = "preview"
    visible_to_human: bool = True
    safe_to_render: bool = True
    redaction_applied: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskPanel:
    risk_id: str
    risk_type: str
    severity: str
    summary: str
    affected_action: str
    approval_required: bool = True
    strong_approval_required: bool = False
    double_confirmation_required: bool = False
    triple_confirmation_required: bool = False
    mitigation: str = "Keep the action blocked until policy, approval, audit, and stop gates pass."
    rollback_or_stop_plan_required: bool = True
    current_gate_state: str = "blocked"
    blocked_reasons: List[str] = field(default_factory=lambda: ["real execution is disabled"])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def mark_2_visual_dashboard_markers() -> Dict[str, Any]:
    return {
        "mark_2_macro_3_visual_command_center_dashboard": True,
        "mark_2_macro_3_visual_command_center_dashboard_available": True,
        "visual_command_center_available": True,
        "human_approval_console_available": True,
        "agent_operations_dashboard_available": True,
        "ai_coding_session_control_available": True,
        "cost_usage_dashboard_available": True,
        "risk_panel_available": True,
        "audit_timeline_available": True,
        "worktree_guard_panel_available": True,
        "diff_test_review_panel_available": True,
        "codex_cli_adapter_preview_available": True,
        "claude_code_adapter_preview_available": True,
        "claude_cowork_adapter_preview_available": True,
        "api_fallback_adapter_preview_available": True,
        "real_ai_cli_invocation_enabled": False,
        "real_ai_cli_invocation_disabled_by_default": True,
        "real_agent_execution_enabled": False,
        "real_agent_execution_disabled_by_default": True,
        "dashboard_control_plane_only": True,
        "costs_are_estimated_or_unknown": True,
        "no_fake_costs": True,
        "human_approval_required_for_sensitive_actions": True,
        "voice_approval_visible": True,
        "wake_phrase_is_permission": False,
        "restrictions_are_approval_gates": True,
        "mark_2_macro_4_planned": True,
        "mark_2_macro_3_next_recommended_macro_pr": NEXT_RECOMMENDED_MACRO_PR,
    }


class VisualCommandCenter:
    PANEL_IDS = (
        "system_status", "agents", "sessions", "ai_coding_sessions", "costs_and_limits",
        "approvals", "risks", "tool_candidates", "diffs_tests_reviews", "audit_timeline",
        "kill_switch", "next_actions",
    )

    def status(self) -> Dict[str, Any]:
        return VisualCommandCenterStatus().to_dict()

    def panels(self) -> List[Dict[str, Any]]:
        return [
            DashboardPanel(
                panel_id=panel_id,
                title=panel_id.replace("_", " ").title(),
                status="ready",
                risk_level="high" if panel_id in {"approvals", "risks", "kill_switch"} else "medium",
                summary=f"Safe control-plane view for {panel_id.replace('_', ' ')}.",
                data_sources=["Mark 2 control-plane snapshot"],
                requires_approval=panel_id in {"approvals", "risks"},
                refresh_mode="manual",
            ).to_dict()
            for panel_id in self.PANEL_IDS
        ]

    def agents(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in build_agent_operations_dashboard()]

    def sessions(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in build_ai_coding_sessions()]

    def costs(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in build_cost_usage_dashboard()]

    def approvals(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in build_human_approval_console()]

    def risks(self) -> List[Dict[str, Any]]:
        types = ("production", "money", "access_material", "filesystem", "github", "browser", "external_api", "privacy", "legal", "unknown")
        return [
            RiskPanel(
                risk_id=f"risk-{risk_type}",
                risk_type=risk_type,
                severity="critical" if risk_type in {"production", "money"} else "high",
                summary=f"{risk_type.replace('_', ' ')} actions require explicit review.",
                affected_action=f"future {risk_type.replace('_', ' ')} action",
                strong_approval_required=risk_type in {"production", "money", "access_material", "privacy", "legal"},
                double_confirmation_required=risk_type in {"production", "money"},
                triple_confirmation_required=risk_type == "money",
            ).to_dict()
            for risk_type in types
        ]

    def worktree_guard(self) -> Dict[str, Any]:
        return WorktreeExecutionGuardPanel().to_dict()

    def diff_test_review(self) -> Dict[str, Any]:
        return DiffTestReviewPanel().to_dict()

    def audit(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in build_audit_timeline()]

    def next_actions(self) -> List[Dict[str, Any]]:
        return [
            {"action": "Review dashboard snapshot", "safe": True, "would_execute": False},
            {"action": "Provide manual worktree, diff, test, and cost evidence", "safe": True, "would_execute": False},
            {"action": NEXT_RECOMMENDED_MACRO_PR, "safe": True, "would_execute": False},
        ]

    def overview(self) -> Dict[str, Any]:
        return {
            "status": self.status(),
            "panels": self.panels(),
            "agents": self.agents(),
            "ai_coding_sessions": self.sessions(),
            "cost_usage": self.costs(),
            "approvals": self.approvals(),
            "risks": self.risks(),
            "tool_candidates": build_model_tool_router_preview(),
            "worktree_guard": self.worktree_guard(),
            "diff_test_review": self.diff_test_review(),
            "audit_timeline": self.audit(),
            "next_actions": self.next_actions(),
            "dashboard_health": "ready_control_plane_only",
            "safe_to_render": True,
        }
