from __future__ import annotations

from typing import Any, Dict, List

from jarvis.adaptive_saas_builder import AdaptiveSaaSBuilder
from jarvis.monetization_engine import MonetizationEngine


class Mark1E2ERealOpsSmoke:
    """Deterministic control-plane smoke for a monetizable micro-SaaS request."""

    def __init__(
        self,
        builder: AdaptiveSaaSBuilder | None = None,
        monetization: MonetizationEngine | None = None,
    ) -> None:
        self.builder = builder or AdaptiveSaaSBuilder()
        self.monetization = monetization or MonetizationEngine()

    def run(self, *, simulated_valid_approval: bool = True) -> Dict[str, Any]:
        idea = {
            "idea_summary": "Help small agencies detect client churn risk before weekly reviews",
            "niche": "small digital agencies",
            "target_customer": "agency owners",
            "problem": "client-risk changes are hidden across weekly project updates",
            "monetization_goal": "monthly subscription",
            "budget_limit": 100,
            "timeline": "two-week MVP",
        }
        approval = {
            "valid_approval_present": simulated_valid_approval,
            "strong_approval_present": simulated_valid_approval,
            "double_confirmation_present": simulated_valid_approval,
            "context_fingerprint_matches": simulated_valid_approval,
            "permission_gates_passed": simulated_valid_approval,
            "audit_present": simulated_valid_approval,
            "rollback_or_stop_plan_present": simulated_valid_approval,
        }
        stages: List[Dict[str, Any]] = [
            {"stage": "idea_intake", "result": self.builder.preview_intake(idea)},
            {
                "stage": "validation_contrarian",
                "result": self.builder.preview_validation(
                    {
                        **idea,
                        "differentiation": "change-focused churn signals for weekly agency reviews",
                        "validation_evidence": ["operator-provided workflow pain"],
                        "validation_score": 75,
                    }
                ),
            },
            {
                "stage": "differentiation_review",
                "result": self.builder.preview_differentiation(
                    {
                        "unique_angle": "surfaces only client-risk changes since the prior review",
                        "unfair_advantage_or_edge": "agency-specific weekly review workflow",
                        "product_specific_decisions": ["change-first risk queue", "weekly owner digest"],
                        "differentiation_score": 85,
                    }
                ),
            },
            {
                "stage": "blueprint",
                "result": self.builder.preview_blueprint(
                    {
                        "product_name": "Agency Signal",
                        "problem": idea["problem"],
                        "target_customer": idea["target_customer"],
                        "differentiation": "change-focused churn signals for weekly agency reviews",
                        "reason_to_exist": "owners miss changes hidden in status updates",
                        "mvp_scope": ["capture weekly updates", "show changed risk signals"],
                        "pricing": {"name": "Starter", "price_amount": 19, "billing_period": "monthly"},
                        "risks": ["false positives"],
                        "assumptions": ["owners review weekly"],
                        "unknowns": ["preferred integrations"],
                    }
                ),
            },
            {
                "stage": "pricing_preview",
                "result": self.monetization.preview_pricing(
                    {"name": "Starter", "price_amount": 19, "billing_interval": "monthly"}
                ),
            },
            {
                "stage": "revenue_projection",
                "result": self.monetization.preview_revenue(
                    {
                        "expected_customers": 10,
                        "monthly_price": 19,
                        "conversion_rate": 0.05,
                        "churn_rate": 0.03,
                        "confidence_level": "low",
                    }
                ),
            },
            {
                "stage": "budget_guard",
                "result": self.monetization.preview_budget(
                    {
                        "monthly_budget_limit": 100,
                        "per_action_spend_limit": 25,
                        "current_spend_estimate": 0,
                        "proposed_spend": 20,
                        "valid_approval_present": simulated_valid_approval,
                    }
                ),
            },
            {
                "stage": "publishing_plan",
                "result": self.builder.preview_publishing(
                    {
                        **approval,
                        "environment": "production",
                        "target_platform": "vercel",
                        "rollback_or_unpublish_plan": ["restore previous release"],
                    }
                ),
            },
            {
                "stage": "deploy_plan",
                "result": self.builder.preview_deploy(
                    {
                        **approval,
                        "environment": "production",
                        "deploy_target": "vercel",
                        "artifact": "reviewed build candidate",
                        "rollback_plan": ["restore previous artifact"],
                    }
                ),
            },
            {
                "stage": "execution_candidate",
                "result": self.builder.preview_execution_candidate(
                    {
                        **approval,
                        "candidate_id": "mark-1-e2e-deploy-candidate",
                        "action_type": "deploy_backend",
                        "target": "Agency Signal production",
                        "environment": "production",
                    }
                ),
            },
            {
                "stage": "approval_decision",
                "result": self.builder.preview_action(
                    {**approval, "action_type": "plan_deploy", "environment": "production"}
                ),
            },
            {
                "stage": "critical_warning",
                "result": self.builder.semantics.preview_critical_warning(
                    action_name="deploy Agency Signal production",
                    affected_system="production deployment candidate",
                    possible_consequences=["public availability changes", "rollback may be required"],
                    estimated_cost="unknown; requires operator review",
                    rollback_available=True,
                ).to_dict(),
            },
            {
                "stage": "launch_readiness_review",
                "result": self.builder.preview_launch_readiness(
                    {
                        "environment": "production",
                        "product_ready": True,
                        "differentiation_ready": True,
                        "pricing_ready": True,
                        "legal_ready": True,
                        "privacy_ready": True,
                        "security_ready": True,
                        "analytics_ready": True,
                        "support_ready": True,
                        "deploy_ready": True,
                        "rollback_ready": True,
                        "approval_ready": simulated_valid_approval,
                    }
                ),
            },
        ]
        eligible = any(item["result"].get("eligible_after_valid_approval") is True for item in stages)
        required_stages = {
            "idea_intake",
            "validation_contrarian",
            "differentiation_review",
            "blueprint",
            "pricing_preview",
            "revenue_projection",
            "budget_guard",
            "publishing_plan",
            "deploy_plan",
            "execution_candidate",
            "approval_decision",
            "critical_warning",
            "launch_readiness_review",
        }
        observed_stages = {item["stage"] for item in stages}
        side_effect_flags_clear = not any(_contains_forbidden_true(item["result"]) for item in stages)
        validation_checks = {
            "all_required_stages_present": observed_stages == required_stages,
            "all_side_effect_flags_clear": side_effect_flags_clear,
            "execution_candidate_eligible_with_simulated_approval": eligible if simulated_valid_approval else not eligible,
        }
        return {
            "scenario": "David asks JARVIS to create a monetizable micro-SaaS.",
            "passed": all(validation_checks.values()),
            "control_plane_only": True,
            "simulated_valid_approval": simulated_valid_approval,
            "eligible_after_valid_approval": eligible,
            "would_execute": False,
            "would_create_repo": False,
            "would_write_external_filesystem": False,
            "would_call_external": False,
            "would_use_credentials": False,
            "would_move_money": False,
            "would_deploy": False,
            "would_publish": False,
            "validation_checks": validation_checks,
            "stages": stages,
        }


_FORBIDDEN_TRUE_KEYS = {
    "execution_allowed",
    "execution_enabled",
    "external_calls_enabled",
    "live_billing_enabled",
    "would_call_external",
    "would_charge_real_money",
    "would_create_repo",
    "would_deploy",
    "would_execute",
    "would_modify_filesystem",
    "would_move_money",
    "would_publish",
    "would_spend_real_money",
    "would_touch_production",
    "would_use_credentials",
    "would_write_files",
}


def _contains_forbidden_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            (key in _FORBIDDEN_TRUE_KEYS and item is True) or _contains_forbidden_true(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_true(item) for item in value)
    return False
