from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class Mark3ReleaseCandidateStatus:
    current_mark: str = "Mark 3"
    release_candidate_name: str = "Mark 3 Release Candidate + Pilot"
    release_candidate_status: str = "ready_as_controlled_release_candidate"
    ready_as_controlled_release_candidate: bool = True
    not_ready_for_free_autonomy: bool = True
    local_first: bool = True
    human_control_required: bool = True
    restrictions_are_approval_gates_not_permanent_bans: bool = True
    illegal_unsafe_unauthorized_deceptive_remain_denied: bool = True
    hermes_remains_execution_engine: bool = True
    jarvis_governs_classifies_approves_audits: bool = True
    no_duplicate_hermes_runtime: bool = True
    controlled_pilot_ready_to_prepare: bool = True
    real_pilot_executed: bool = False
    free_autonomy_enabled: bool = False
    real_scheduler_enabled: bool = False
    external_network_enabled: bool = False
    github_web_providers_connected: bool = False
    email_send_enabled: bool = False
    stripe_live_enabled: bool = False
    deploy_publish_domain_enabled: bool = False
    credentials_or_access_material_enabled: bool = False
    background_24_7_enabled: bool = False
    production_enabled: bool = False
    money_movement_enabled: bool = False
    no_fake_revenue: bool = True
    no_fake_costs: bool = True
    no_fake_results: bool = True
    no_fake_benchmarks: bool = True
    no_fake_capabilities: bool = True
    completed_mark_3_prs: List[str] = field(default_factory=lambda: [
        "PR #132 Mark 3 Master Planning",
        "PR #133 Autonomous Mission Loop",
        "PR #134 Governed Hermes Runtime read_file vertical slice",
        "PR #135 Outcome/Failure Memory, Learning Proposals, Growth Radar",
        "PR #136 Governed Research Execution Control Plane",
        "PR #137 Local Docs/Repo Research Adapter",
        "PR #138 Product/Revenue Factory",
        "PR #139 Local Routine Scheduler + Personal/Family Ops",
        "PR #140 Moonshot Lab + Research/Experiment Engine",
        "PR #141 Release Candidate + Pilot preparation",
        "PR #142 Pilot Findings Hardening",
    ])
    next_safe_step: str = "Run the local controlled pilot only after operator approval and within the RC pilot plan."
    safe_to_render: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Mark3Capability:
    capability_id: str
    name: str
    source_pr: str
    status: str
    execution_default: str = "disabled_or_gated"
    approval_required_for_side_effects: bool = True
    required_approval_level: str = "risk_scaled"
    real_execution_supported_now: bool = False
    real_execution_enabled_by_default: bool = False
    prepare_only_or_read_only_default: bool = True
    local_first: bool = True
    human_control_required: bool = True
    hermes_execution_engine: bool = True
    summary: str = ""
    limitations: List[str] = field(default_factory=list)
    next_safe_step: str = "Review the exact scope, risk, approval, evidence, and stop plan."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark3CapabilityMatrix:
    _CAPABILITIES = (
        Mark3Capability(
            "master_planning",
            "Master Planning",
            "PR #132",
            "ready",
            approval_required_for_side_effects=False,
            required_approval_level="direct",
            summary="Universal Governed Execution, risk model, macro-roadmap, guardrails, and local-first policy.",
            limitations=["Planning endpoints are read-only and do not execute tools."],
            next_safe_step="Use the roadmap to govern Mark 3 RC and pilot decisions.",
        ),
        Mark3Capability(
            "autonomous_mission_loop",
            "Autonomous Mission Loop",
            "PR #133",
            "ready_control_plane",
            required_approval_level="risk_scaled_per_step",
            summary="In-memory mission intake, classification, plans, approvals, candidates, outcomes, and post-mortem.",
            limitations=["Mission candidates do not grant free autonomy or inherited approval."],
        ),
        Mark3Capability(
            "governed_hermes_runtime_read_file",
            "Governed Hermes Runtime read_file",
            "PR #134",
            "ready_for_exact_gated_local_read",
            execution_default="gated_read_only_disabled_by_default",
            required_approval_level="valid_operator_authorization_and_step_approval",
            real_execution_supported_now=True,
            summary="The first governed Hermes vertical slice can perform one exact approved local read_file action.",
            limitations=[
                "Only read_file is supported.",
                "No terminal, browser, network, writes, money, providers, or broad filesystem access.",
                "Execution requires a valid mission candidate, approval, scope fingerprint, and operator authorization channel.",
            ],
            next_safe_step="Use only inside a bounded local pilot after approval; do not generalize it to arbitrary execution.",
        ),
        Mark3Capability(
            "outcome_failure_memory",
            "Outcome and Failure Memory",
            "PR #135",
            "ready_in_memory",
            approval_required_for_side_effects=False,
            required_approval_level="direct_for_recording_non_sensitive_outcomes",
            summary="Records evidence-linked outcomes and repeatable failures without storing secrets or inventing evidence.",
            limitations=["In-memory in this layer; memory never grants permission."],
        ),
        Mark3Capability(
            "learning_proposals",
            "Learning Proposals",
            "PR #135",
            "ready_reviewable",
            required_approval_level="simple_or_stronger_for_approval",
            summary="Creates reviewable, reversible learning proposals from evidence and failures.",
            limitations=["Approval of a proposal does not authorize task execution."],
        ),
        Mark3Capability(
            "growth_radar",
            "Autonomous Growth Radar",
            "PR #135",
            "ready_control_plane",
            required_approval_level="risk_scaled",
            summary="Plans research for GitHub, web, docs, and local repo without calling external sources by default.",
            limitations=["GitHub and web remain setup_required until real governed adapters exist."],
        ),
        Mark3Capability(
            "research_execution_control_plane",
            "Research Execution Control Plane",
            "PR #136",
            "ready_control_plane",
            required_approval_level="risk_scaled",
            summary="Normalizes research requests, checks policy, approval, capability, and prepares candidates.",
            limitations=["No research /execute route; missing capabilities return setup_required instead of fake research."],
        ),
        Mark3Capability(
            "local_docs_repo_research_adapter",
            "Local Docs/Repo Research Adapter",
            "PR #137",
            "ready_for_exact_read_only_scope",
            execution_default="gated_read_only_disabled_by_default",
            required_approval_level="direct_or_simple_depending_on_scope",
            real_execution_supported_now=True,
            summary="Can read one exact allowed local docs/repo file through the governed research candidate path.",
            limitations=[
                "No broad scans, multi-scope, symlinks, path traversal, .env, secrets, commands, web, GitHub, or providers.",
                "Candidate by id alone cannot rehydrate a previous preview into execution.",
            ],
        ),
        Mark3Capability(
            "product_revenue_factory",
            "Product/Revenue Factory",
            "PR #138",
            "ready_prepare_only",
            required_approval_level="direct_for_candidates_level_4_for_real_money_publication_or_identity",
            summary="Prepares opportunity, product, pricing, revenue, experiment, measurement, and kill/continue candidates.",
            limitations=["No publication, deploy, checkout, Stripe live, email, domains, money, credentials, fake revenue, or fake costs."],
        ),
        Mark3Capability(
            "local_routine_scheduler_personal_family_ops",
            "Local Routine Scheduler + Personal/Family Ops",
            "PR #139",
            "ready_prepare_only",
            required_approval_level="risk_scaled",
            summary="Prepares local routine, personal ops, family ops, account assistance, checklist, and health candidates.",
            limitations=[
                "No real scheduler, cron, worker, watcher, email, Gmail, Calendar, Contacts, account login, password storage, 2FA bypass, cookie/token/session use, or fake completion.",
            ],
        ),
        Mark3Capability(
            "moonshot_lab_research_experiment_engine",
            "Moonshot Lab + Research/Experiment Engine",
            "PR #140",
            "ready_prepare_only",
            required_approval_level="risk_scaled",
            summary="Prepares moonshot intake, hypotheses, experiment plans, prototypes, evidence scoring, stage gates, and decisions.",
            limitations=[
                "No experiment execution, network, GitHub/web, providers, installs, processes, publication, deploy, money, credentials, fake breakthrough, fake benchmark, fake result, or fake capability.",
            ],
        ),
    )

    def build(self) -> List[Mark3Capability]:
        return list(self._CAPABILITIES)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 3",
            "release_candidate_status": "ready_as_controlled_release_candidate",
            "ready_as_controlled_release_candidate": True,
            "not_ready_for_free_autonomy": True,
            "local_first": True,
            "human_control_required": True,
            "restrictions_are_approval_gates_not_permanent_bans": True,
            "hermes_remains_execution_engine": True,
            "no_duplicate_hermes_runtime": True,
            "capabilities": [item.to_dict() for item in self.build()],
            "safe_to_render": True,
        }


class Mark3ReadinessMatrix:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 3",
            "release_candidate_status": "ready_as_controlled_release_candidate",
            "ready_as_controlled_release_candidate": True,
            "not_ready_for_free_autonomy": True,
            "local_first": True,
            "human_control_required": True,
            "restrictions_are_approval_gates_not_permanent_bans": True,
            "readiness": {
                "master_planning": "ready",
                "mission_loop": "ready_control_plane",
                "governed_hermes_runtime_read_file": "ready_for_exact_gated_local_read",
                "outcome_failure_memory": "ready_in_memory",
                "learning_proposals": "ready_reviewable",
                "growth_radar": "ready_control_plane",
                "research_execution_control_plane": "ready_control_plane",
                "local_docs_repo_research_adapter": "ready_for_exact_read_only_scope",
                "product_revenue_factory": "ready_prepare_only",
                "local_routine_scheduler_personal_family_ops": "ready_prepare_only",
                "moonshot_lab": "ready_prepare_only",
                "dangerous_route_audit": "ready",
                "approval_path_audit": "ready",
                "e2e_prepare_only_gated_smoke": "ready",
                "pilot_plan": "ready_to_review",
                "operational_runbook": "ready",
                "docs": "ready",
                "tests": "ready",
                "free_autonomy": "not_ready",
                "real_scheduler": "not_ready",
                "external_web_github_providers": "not_connected_by_default",
                "production_money_email_deploy_domain": "not_ready_without_level_4_setup_and_approval",
            },
            "not_ready_for": [
                "free autonomy",
                "default real provider execution",
                "real scheduler or background 24/7 operation",
                "production, money, email, deploy, domain, account, credential, or publication operations without explicit setup and approvals",
            ],
            "pilot_readiness": "ready_to_prepare_local_controlled_pilot",
            "pilot_executed": False,
            "safe_to_render": True,
        }


def mark_3_release_candidate_markers() -> Dict[str, Any]:
    return {
        "mark_3_release_candidate_available": True,
        "mark_3_release_candidate_status": "ready_as_controlled_release_candidate",
        "mark_3_ready_as_controlled_release_candidate": True,
        "mark_3_not_ready_for_free_autonomy": True,
        "mark_3_local_first": True,
        "mark_3_human_control_required": True,
        "mark_3_restrictions_are_approval_gates_not_permanent_bans": True,
        "mark_3_hermes_remains_execution_engine": True,
        "mark_3_no_duplicate_hermes_runtime": True,
        "mark_3_real_scheduler_enabled": False,
        "mark_3_external_network_enabled": False,
        "mark_3_money_movement_enabled": False,
        "mark_3_email_send_enabled": False,
        "mark_3_production_enabled": False,
        "mark_3_no_fake_revenue": True,
        "mark_3_no_fake_costs": True,
        "mark_3_no_fake_results": True,
        "mark_3_no_fake_benchmarks": True,
        "mark_3_no_fake_capabilities": True,
        "mark_3_pilot_findings_hardened": True,
    }
