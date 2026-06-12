from __future__ import annotations

from typing import Any, Dict

from jarvis.api_fallback_adapter import ApiFallbackAdapter
from jarvis.ai_cli_session_audit import build_external_operation_audit_event
from jarvis.claude_code_adapter import ClaudeCodeAdapter
from jarvis.claude_cowork_adapter import ClaudeCoworkAdapter
from jarvis.codex_cli_adapter import CodexCliAdapter
from jarvis.local_daemon import LocalDaemonControl
from jarvis.mark_2_deploy_adapter import Mark2DeployAdapter
from jarvis.mark_2_domain_publishing_adapter import Mark2DomainPublishingAdapter
from jarvis.mark_2_email_adapter import Mark2EmailAdapter
from jarvis.mark_2_release_candidate import Mark2ReleaseCandidateStatus
from jarvis.mark_2_stripe_adapter import Mark2StripeAdapter
from jarvis.routine_execution_bridge import RoutineExecutionBridge


class Mark2E2EReadinessSmoke:
    def run(self) -> Dict[str, Any]:
        deploy_without_rollback = Mark2DeployAdapter().preview(environment="production")
        deploy_without_approval = Mark2DeployAdapter().preview(environment="production", rollback_plan="restore prior release")
        stripe = Mark2StripeAdapter().preview(stripe_mode="live", operation="charge", money_movement=True)
        email = Mark2EmailAdapter().preview(operation="send")
        domain = Mark2DomainPublishingAdapter().preview(
            operation="dns_record", production_impact=True, rollback_or_unpublish_plan="restore prior record"
        )
        codex = CodexCliAdapter.preview()
        claude_code = ClaudeCodeAdapter.preview()
        cowork = ClaudeCoworkAdapter.preview(routine_type="browser_assist")
        api = ApiFallbackAdapter.preview()
        routine = RoutineExecutionBridge.preview(routine_type="external_api", use_case="worker")
        status = Mark2ReleaseCandidateStatus()
        local_daemon = LocalDaemonControl().status()
        audit_event = build_external_operation_audit_event()
        checks = {
            "deploy_candidate_cannot_deploy": not deploy_without_rollback.would_deploy and not deploy_without_approval.would_deploy,
            "production_deploy_requires_rollback": "required rollback or stop plan is missing" in deploy_without_rollback.blocked_reasons,
            "production_deploy_requires_approval": "valid explicit approval required" in deploy_without_approval.blocked_reasons,
            "stripe_cannot_move_money": not stripe.would_move_money and stripe.strong_approval_required and stripe.double_confirmation_required and stripe.triple_confirmation_required,
            "email_cannot_send": not email.would_send_email and email.approval_required,
            "domain_cannot_modify_dns": not domain.would_modify_dns and domain.strong_approval_required and domain.double_confirmation_required,
            "ai_cli_cannot_invoke_real_tool": not codex.would_invoke_real_cli and not claude_code.would_invoke_real_cli and not cowork.would_invoke_real_cowork,
            "api_fallback_cannot_call_real_api": not api.would_call_api,
            "routine_bridge_would_execute_false": not routine.would_execute,
            "no_fake_costs": not codex.cost_known and not claude_code.cost_known and not api.cost_known,
            "audit_safe": routine.audit_required and audit_event.audit_safe,
            "access_material_enabled_false": not status.access_material_enabled,
            "external_network_enabled_false": not status.external_network_enabled,
            "wake_phrase_is_permission_false": not status.wake_phrase_is_permission,
            "voice_can_approve": status.voice_can_approve,
            "kill_switch_stop_control_ready": local_daemon["kill_switch_available"] and local_daemon["stop_phrase_available"],
        }
        return {
            "passed": all(checks.values()),
            "prepare_only": True,
            "would_execute": False,
            "would_deploy": False,
            "would_move_money": False,
            "would_send_email": False,
            "would_modify_dns": False,
            "would_call_external": False,
            "access_material_enabled": False,
            "external_network_enabled": False,
            "wake_phrase_is_permission": False,
            "voice_can_approve": True,
            "kill_switch_stop_control_ready": True,
            "no_fake_costs": True,
            "audit_safe": True,
            "checks": checks,
        }
