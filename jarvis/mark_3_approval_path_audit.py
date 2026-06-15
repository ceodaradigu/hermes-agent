from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Mark3ApprovalPath:
    level: int
    name: str
    action_class: str
    examples: List[str]
    approval_required: bool
    required_approval_level: str
    strong_approval_required: bool = False
    double_confirmation_required: bool = False
    triple_confirmation_required: bool = False
    scope_required: bool = False
    budget_limit_required: bool = False
    rollback_or_stop_plan_required: bool = False
    audit_required: bool = True
    human_control_required: bool = True
    eligible_after_valid_approval_and_real_capability: bool = True
    permanent_denial: bool = False
    restrictions_are_approval_gates_not_permanent_bans: bool = True
    denial_reason: str = ""
    passed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark3ApprovalPathAudit:
    def audit(self) -> Dict[str, Any]:
        paths = [
            Mark3ApprovalPath(
                level=0,
                name="Level 0",
                action_class="innocuous_reasoning",
                examples=["summaries", "classification", "explanations", "questions", "draft plans without side effects"],
                approval_required=False,
                required_approval_level="none",
                scope_required=False,
                budget_limit_required=False,
                rollback_or_stop_plan_required=False,
            ),
            Mark3ApprovalPath(
                level=1,
                name="Level 1",
                action_class="low_risk_direct_or_contextual",
                examples=["local checklists", "document review", "candidate preparation", "operator-supplied metric review"],
                approval_required=False,
                required_approval_level="direct_or_contextual",
                scope_required=False,
                budget_limit_required=False,
                rollback_or_stop_plan_required=False,
            ),
            Mark3ApprovalPath(
                level=2,
                name="Level 2",
                action_class="scoped_local_read_repo_docs",
                examples=[
                    "scoped local repo inspection",
                    "exact docs/local_repo read",
                    "documentation edits in worktree",
                    "bounded local tests",
                ],
                approval_required=True,
                required_approval_level="simple",
                scope_required=True,
                budget_limit_required=True,
                rollback_or_stop_plan_required=True,
            ),
            Mark3ApprovalPath(
                level=3,
                name="Level 3",
                action_class="external_research_private_metrics_ai_cli_sensitive_authorized_data",
                examples=[
                    "external research",
                    "private metrics review",
                    "real AI CLI invocation",
                    "sensitive authorized data",
                    "provider setup candidate",
                ],
                approval_required=True,
                required_approval_level="strong",
                strong_approval_required=True,
                scope_required=True,
                budget_limit_required=True,
                rollback_or_stop_plan_required=True,
            ),
            Mark3ApprovalPath(
                level=4,
                name="Level 4",
                action_class="production_money_identity_credentials_publication_deploy_domain_email_real",
                examples=[
                    "production deploy",
                    "money movement",
                    "Stripe live or checkout",
                    "identity usage",
                    "credentials or access material",
                    "public publication",
                    "domain or DNS changes",
                    "real email send",
                    "real account recovery action",
                ],
                approval_required=True,
                required_approval_level="level_4_strong_double_or_triple",
                strong_approval_required=True,
                double_confirmation_required=True,
                triple_confirmation_required=True,
                scope_required=True,
                budget_limit_required=True,
                rollback_or_stop_plan_required=True,
            ),
            Mark3ApprovalPath(
                level=5,
                name="Level 5",
                action_class="illegal_unsafe_unauthorized_bypass_deception_fake_capability",
                examples=[
                    "illegal or unsafe action",
                    "unauthorized access",
                    "credential theft",
                    "2FA bypass",
                    "cookie/token/session theft",
                    "deception",
                    "fake execution",
                    "fake revenue, costs, benchmark, result, or capability",
                ],
                approval_required=False,
                required_approval_level="level_5_denied",
                eligible_after_valid_approval_and_real_capability=False,
                permanent_denial=True,
                restrictions_are_approval_gates_not_permanent_bans=False,
                denial_reason="Illegal, unsafe, unauthorized, bypass, deceptive, or fake-capability requests remain permanently denied.",
            ),
        ]
        return {
            "current_mark": "Mark 3",
            "release_candidate_status": "ready_as_controlled_release_candidate",
            "passed": all(item.passed for item in paths),
            "safe_to_render": True,
            "read_only_audit": True,
            "restrictions_are_approval_gates_not_permanent_bans": True,
            "level_5_is_permanent_denial": True,
            "approval_is_not_execution": True,
            "permission_does_not_create_capability": True,
            "human_control_required": True,
            "approval_paths": [item.to_dict() for item in paths],
            "coverage": {
                "level_0_1_low_risk": True,
                "level_2_scoped_local_read_repo_docs": True,
                "level_3_external_research_private_metrics_ai_cli_sensitive_authorized_data": True,
                "level_4_production_money_identity_credentials_publication_deploy_domain_email_real": True,
                "level_5_illegal_unsafe_unauthorized_bypass_deception_fake_capability": True,
            },
        }
