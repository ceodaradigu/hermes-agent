from __future__ import annotations

import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from jarvis.persistent_audit import PersistentAuditLedger


PHASE_9_SCHEMA_VERSION = "jarvis.phase_9_autonomous_product_operator.v1"
PRODUCT_MISSION_ENVELOPE_SCHEMA_VERSION = "jarvis.product_mission_envelope.v1"
PRODUCT_BUILDER_SCHEMA_VERSION = "jarvis.product_builder_candidate.v1"
MONEY_ROI_SCHEMA_VERSION = "jarvis.money_roi_decision.v1"
EXPERIMENT_PLANNER_SCHEMA_VERSION = "jarvis.product_experiment_plan.v1"
REVENUE_TRACKER_SCHEMA_VERSION = "jarvis.product_revenue_tracker.v1"
BUDGET_GUARD_V2_SCHEMA_VERSION = "jarvis.product_budget_guard.v2"
SELF_IMPROVEMENT_SCHEMA_VERSION = "jarvis.self_improvement_proposal.v1"
OPERATOR_REPORT_SCHEMA_VERSION = "jarvis.product_operator_report.v1"
OPERATING_LOOP_SCHEMA_VERSION = "jarvis.product_operating_loop.v1"

UNKNOWN = "unknown"

MISSION_STATUSES = {
    "draft",
    "prepared",
    "active",
    "paused",
    "blocked",
    "completed",
    "stopped",
    "expired",
}
RISK_LEVELS = {"low", "medium", "high", "critical", "denied"}
APPROVAL_LEVELS = {"direct", "normal", "strong", "double", "triple", "blocked", "denied"}
DECISION_STATES = {
    "reject",
    "watch",
    "prepare",
    "build candidate",
    "launch candidate",
    "needs approval",
    "blocked",
}
REVENUE_EVENT_TYPES = {"projected", "confirmed", "refund", "cost", "fee", "net_calculation"}
EXPERIMENT_STATUSES = {"planned", "prepared", "approval_required", "blocked", "running", "completed", "stopped"}
REPORT_TYPES = {
    "daily_operator_report",
    "weekly_product_report",
    "pending_approval_report",
    "budget_report",
    "revenue_report",
    "experiment_report",
    "blocker_report",
}

BLANKET_APPROVAL_MARKERS = {
    "approve_all_forever",
    "approve all forever",
    "do anything",
    "unlimited",
    "no limits",
    "without limits",
    "whatever it takes",
    "sin limites",
    "sin limites",
    "haz todo lo necesario sin limites",
}

DEFAULT_FORBIDDEN_ACTIONS = [
    "production deploy without approval",
    "DNS changes",
    "external publication",
    "real email send",
    "mass email",
    "Stripe live charge",
    "payment processing",
    "money movement",
    "payout",
    "refund",
    "credential or secret access",
    "commit, push, PR, merge without approval",
    "self-deploy",
    "self-merge",
    "approve-all-forever",
    "fake customers",
    "fake revenue",
    "fake launch",
]

HARD_DENIAL_MARKERS = (
    "fake revenue",
    "invent revenue",
    "fake customers",
    "invent customers",
    "fake launch",
    "pretend we launched",
    "bypass approval",
    "bypass policy",
    "hide from david",
    "hide this from",
    "exfiltrate",
    "steal",
)

CRITICAL_ACTION_KEYS = {
    "production_requested",
    "domain_requested",
    "dns_requested",
    "stripe_live_requested",
    "payment_requested",
    "charge_requested",
    "money_movement_requested",
    "refund_requested",
    "payout_requested",
    "identity_requested",
}
STRONG_ACTION_KEYS = {
    "deploy_requested",
    "publish_requested",
    "email_requested",
    "send_requested",
    "spend_requested",
    "budget_spend_requested",
    "provider_requested",
    "external_research_requested",
}
SELF_IMPROVEMENT_FORBIDDEN_MARKERS = (
    "remove approvalgateway",
    "remove approval gateway",
    "disable approvalgateway",
    "disable approval gateway",
    "bypass approval",
    "weaken policy",
    "remove policyengine",
    "remove policy engine",
    "disable audit",
    "remove audit",
    "skip tests",
    "bypass tests",
    "auto merge",
    "auto-merge",
    "self merge",
    "self-merge",
    "auto deploy",
    "auto-deploy",
    "self deploy",
    "self-deploy",
    "commit and push",
    "open pr by itself",
    "create pull request by itself",
)


class Phase9ProductOperatorControlPlane:
    """Autonomous product-operator control plane with governed prepare-only outputs.

    Phase 9 plans product/business work and creates local candidates. It does
    not execute Hermes, call providers, publish, deploy, email, charge money,
    spend money, commit, push, open PRs, merge, or run hidden schedules.
    """

    def __init__(
        self,
        *,
        phase_7_actions: Any = None,
        phase_8_external_ops: Any = None,
        product_revenue_factory: Any = None,
        audit_ledger: Optional[PersistentAuditLedger] = None,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.phase_7_actions = phase_7_actions
        self.phase_8_external_ops = phase_8_external_ops
        self.product_revenue_factory = product_revenue_factory
        self.audit_ledger = audit_ledger or PersistentAuditLedger.from_environment()
        self.clock = clock or _now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._missions: Dict[str, Dict[str, Any]] = {}
        self._builder_candidates: Dict[str, Dict[str, Any]] = {}
        self._roi_decisions: Dict[str, Dict[str, Any]] = {}
        self._experiments: Dict[str, Dict[str, Any]] = {}
        self._revenue_events: Dict[str, Dict[str, Any]] = {}
        self._budget_checks: Dict[str, Dict[str, Any]] = {}
        self._self_improvements: Dict[str, Dict[str, Any]] = {}
        self._reports: Dict[str, Dict[str, Any]] = {}
        self._operating_loops: Dict[str, Dict[str, Any]] = {}

    def status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        audit = self._audit(
            "phase_9_status_read",
            risk_level="low",
            approval_level="direct",
            metadata={"route_count": len(routes)},
        )
        revenue_summary = self.revenue_summary(audit_read=False)
        return {
            "schema_version": PHASE_9_SCHEMA_VERSION,
            "phase": "Phase 9",
            "title": "PR #174 -- Autonomous Product Operator, Money Engine and Self-Improvement",
            "status": "implemented_as_governed_product_operator_prepare_only",
            "prepare_only": True,
            "control_plane_only": True,
            "implemented_blocks": {
                "autonomous_product_mission_envelope_v1": True,
                "product_builder_v1": True,
                "money_roi_engine_v1": True,
                "experiment_planner_v1": True,
                "truthful_revenue_tracker_v1": True,
                "budget_guard_v2": True,
                "self_improvement_proposal_system_v1": True,
                "operator_scheduler_report_v1": True,
                "product_operating_loop_v1": True,
                "phase_7_phase_8_integration_contracts": True,
                "dashboard_event_stream_visibility": True,
            },
            "route_readiness": {
                "phase_9_status": "/mark-3/phase-9/status" in routes,
                "product_operator_status": "/mark-3/product-operator/status" in routes,
                "mission_envelope": "/mark-3/product-operator/missions" in routes,
                "product_builder": "/mark-3/product-operator/builder" in routes,
                "roi_decision": "/mark-3/product-operator/roi-decision" in routes,
                "experiment_planner": "/mark-3/product-operator/experiments" in routes,
                "revenue_tracker": "/mark-3/product-operator/revenue-events" in routes,
                "budget_guard": "/mark-3/product-operator/budget-guard" in routes,
                "self_improvement": "/mark-3/product-operator/self-improvement" in routes,
                "operator_report": "/mark-3/product-operator/reports" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "counts": {
                "active_product_missions": len([m for m in self._missions.values() if m.get("status") == "active"]),
                "mission_envelopes": len(self._missions),
                "builder_candidates": len(self._builder_candidates),
                "roi_decisions": len(self._roi_decisions),
                "experiments": len(self._experiments),
                "revenue_events": len(self._revenue_events),
                "budget_checks": len(self._budget_checks),
                "self_improvement_proposals": len(self._self_improvements),
                "operator_reports": len(self._reports),
            },
            "product_missions": _compact_items(self._missions.values(), fields=("mission_id", "title", "risk", "approval_level", "status", "budget_limit", "expires_at")),
            "builder_candidates": _compact_items(self._builder_candidates.values(), fields=("candidate_id", "product_name", "status", "risk", "approval_level", "files_written")),
            "roi_decisions": _compact_items(self._roi_decisions.values(), fields=("decision_id", "title", "decision_state", "opportunity_score", "confidence", "audit_id")),
            "experiments": _compact_items(self._experiments.values(), fields=("experiment_id", "hypothesis", "channel", "status", "approval_requirement")),
            "revenue_tracker": revenue_summary,
            "budget_guard": {
                "schema_version": BUDGET_GUARD_V2_SCHEMA_VERSION,
                "global_monthly_product_budget": UNKNOWN,
                "last_decision": next(reversed(self._budget_checks.values()), {}).get("decision", "not_evaluated") if self._budget_checks else "not_evaluated",
                "can_spend": False,
                "spending_requires_approval": True,
                "unknown_cost_blocks_or_requires_strong_approval": True,
                "memory_can_expand_budget": False,
            },
            "self_improvement": {
                "proposal_count": len(self._self_improvements),
                "can_prepare_patch_plans": True,
                "can_prepare_tests": True,
                "can_prepare_pr_description": True,
                "can_modify_policy_to_weaken_gates": False,
                "can_auto_merge": False,
                "can_auto_deploy": False,
                "can_commit_push_pr_merge_by_itself": False,
            },
            "scheduler_reports": {
                "manual_trigger_available": True,
                "hidden_background_scheduler": False,
                "daily_operator_report": True,
                "weekly_product_report": True,
                "pending_approval_report": True,
                "budget_report": True,
                "revenue_report": True,
                "experiment_report": True,
                "blocker_report": True,
                "future_automation_ready": True,
            },
            "operating_loop": self.operating_loop_status(),
            "phase_integrations": {
                "phase_7_filesystem_action": "filesystem.file.write_safe",
                "phase_7_previews_only": True,
                "phase_8_deploy_email_payment_candidates": True,
                "phase_8_provider_calls_enabled": False,
                "phase_5_voice_approval_contract": "trusted_device_active_session_exact_readback_challenge_scope_expiration_audit",
                "frontend_direct_hermes_allowed": False,
                "hermes_called_by_phase_9": False,
            },
            "security_gates": _phase_9_security_gates(),
            "real_vs_readiness": {
                "real": [
                    "deterministic mission envelope validation with budget/time/scope/stop-condition requirements",
                    "prepare-only product builder candidates and Markdown package previews",
                    "Money/ROI decisions that separate projected and confirmed revenue",
                    "truthful in-memory revenue ledger with evidence rules",
                    "budget checks that block unknown or over-limit spend",
                    "Phase 7 filesystem write previews when a local path is provided",
                    "Phase 8 deploy/email/payment candidate envelopes without provider calls",
                    "metadata-only persistent audit events",
                ],
                "readiness": [
                    "no hidden scheduler or autonomous background loop",
                    "no external posting, scraping, publication, deploy, email send, Stripe checkout or money movement",
                    "no commit, push, PR, merge, self-deploy or self-merge",
                    "no confirmed revenue or metrics without operator-provided evidence",
                ],
            },
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
            "source_endpoint": "/mark-3/product-operator/status",
        }

    def create_mission_envelope(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        envelope = self._mission_envelope_from_values(source)
        errors = self._validate_mission_envelope(envelope)
        if errors:
            raise ValueError("; ".join(errors))
        audit = self._audit(
            "product_mission_envelope_created",
            risk_level=envelope["risk"],
            approval_level=envelope["approval_level"],
            metadata={"mission_id": envelope["mission_id"], "status": envelope["status"]},
        )
        envelope["audit_id"] = audit.get("audit_id", "")
        self._missions[envelope["mission_id"]] = envelope
        return envelope

    def prepare_product_builder(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        product_name = _safe_text(_first_present(source, "product_name", "title", "idea"), "Product candidate", limit=120)
        candidate_id = _safe_id(_first_present(source, "candidate_id", "builder_id"), prefix="pb")
        blocked_reasons = _blocked_reasons(source)
        external_actions = _requested_external_actions(source)
        risk = _risk_for_values(source, blocked_reasons=blocked_reasons)
        approval_level = _approval_level_for_values(source, risk=risk)
        mission_id = _safe_text(source.get("mission_id"), "", limit=120)
        mission = self._missions.get(mission_id) if mission_id else None
        file_candidates = _product_file_candidates(source, product_name=product_name)
        governed_previews = self._governed_file_previews(file_candidates)
        phase_8_candidates = self._phase_8_candidates_for_product(source, product_name=product_name)
        audit = self._audit(
            "product_builder_candidate_prepared",
            risk_level=risk,
            approval_level=approval_level,
            metadata={"candidate_id": candidate_id, "mission_id": mission_id or "unlinked", "file_candidate_count": len(file_candidates)},
        )
        candidate = {
            "schema_version": PRODUCT_BUILDER_SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "product_name": product_name,
            "mission_id": mission_id or None,
            "mission_link_status": "linked_to_product_mission_envelope" if mission else "unlinked_preview_requires_mission_before_execution",
            "created_at": self.clock(),
            "status": "blocked" if blocked_reasons else "prepared_candidate",
            "risk": risk,
            "approval_level": approval_level,
            "approval_required": approval_level not in {"direct", "denied", "blocked"},
            "product_idea_brief": _safe_text(_first_present(source, "product_idea_brief", "idea", "goal"), UNKNOWN, limit=1000),
            "problem_statement": _safe_text(_first_present(source, "problem_statement", "problem"), UNKNOWN, limit=1000),
            "target_customer": _safe_text(_first_present(source, "target_customer", "target_user_customer", "audience"), UNKNOWN, limit=500),
            "value_proposition": _safe_text(_first_present(source, "value_proposition", "promise"), UNKNOWN, limit=1000),
            "competitor_alternative_notes": _safe_list(_first_present(source, "competitor_alternative_notes", "competitors", "alternatives")) or [
                "Manual research required before claiming differentiation."
            ],
            "landing_structure": _landing_structure(source),
            "feature_scope": {
                "mvp": _safe_list(_first_present(source, "mvp_scope", "feature_scope")) or [
                    "Single core workflow",
                    "Manual onboarding",
                    "Evidence capture",
                ],
                "out_of_scope": _safe_list(source.get("out_of_scope")) or [
                    "production deploy",
                    "live payments",
                    "mass email",
                    "automated customer claims",
                ],
            },
            "mvp_checklist": _mvp_checklist(source),
            "tech_stack_recommendation": _tech_stack_recommendation(source),
            "build_plan": _build_plan(source),
            "asset_package": _asset_package(source),
            "local_project_scaffold_plan": {
                "local_project_path": _safe_text(source.get("local_project_path"), UNKNOWN, limit=500),
                "candidate_files": _public_file_candidates(file_candidates),
                "files_written": False,
                "phase_7_filesystem_action_key": "filesystem.file.write_safe",
                "phase_7_governed_previews": governed_previews,
                "generated_files_go_through_governed_filesystem_or_remain_preview_only": True,
            },
            "deploy_candidate": phase_8_candidates.get("deploy_candidate", _deploy_candidate_stub(product_name)),
            "pricing_candidate": _pricing_candidate(source),
            "email_campaign_candidate": phase_8_candidates.get("email_candidate", _email_candidate_stub(source)),
            "stripe_payment_candidate": phase_8_candidates.get("payment_candidate", _payment_candidate_stub(source, product_name)),
            "launch_checklist": _launch_checklist(),
            "external_actions_requested": external_actions,
            "blocked_reasons": blocked_reasons,
            "readback_text": _readback("product builder", candidate_id, product_name, risk, approval_level),
            "challenge_phrase": _challenge(candidate_id),
            "audit_id": audit.get("audit_id", ""),
            "prepare_only": True,
            "files_written": False,
            "would_publish": False,
            "would_deploy": False,
            "would_send_email": False,
            "would_create_checkout": False,
            "would_charge": False,
            "would_call_provider": False,
            "would_call_hermes": False,
            "frontend_direct_hermes_allowed": False,
            "no_fake_launch": True,
            "no_fake_customers": True,
            "no_fake_revenue": True,
            "metadata_only": True,
        }
        self._builder_candidates[candidate_id] = candidate
        return candidate

    def evaluate_roi(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        decision_id = _safe_id(source.get("decision_id"), prefix="roi")
        title = _safe_text(_first_present(source, "title", "opportunity", "product_name"), "ROI decision", limit=160)
        evidence = _safe_list(_first_present(source, "evidence", "source"))
        blocked_reasons = _blocked_reasons(source)
        projected_revenue = _money(_first_present(source, "projected_revenue", "revenue_projection", "expected_upside"))
        confirmed_revenue = _money(source.get("confirmed_revenue"))
        gross_revenue = _money(_first_present(source, "gross_revenue", "gross"))
        fees = _money(source.get("fees")) or 0.0
        costs = _money(_first_present(source, "costs", "cost_estimate", "provider_cost_estimate"))
        effort_hours = _money(_first_present(source, "effort_estimate_hours", "human_time_required_hours")) or 0.0
        human_hours = _money(source.get("human_time_required_hours")) or effort_hours or 0.0
        confidence = _confidence_label(source.get("confidence"))
        confidence_score = _confidence_score(confidence)
        risks = _safe_list(source.get("risks"))
        dependencies = _safe_list(_first_present(source, "dependency_list", "dependencies"))
        unknown_cost = costs is None and bool(source.get("spending_requested") or source.get("spend_requested") or source.get("provider_requested"))
        if confirmed_revenue is not None and not evidence:
            blocked_reasons.append("confirmed revenue requires evidence/source")
            confirmed_revenue = None
        if gross_revenue is None and confirmed_revenue is not None:
            gross_revenue = confirmed_revenue
        net_revenue = gross_revenue - fees - (costs or 0.0) if gross_revenue is not None else None
        opportunity_score = _opportunity_score(
            expected_upside=projected_revenue,
            effort_hours=effort_hours,
            cost_estimate=costs,
            confidence_score=confidence_score,
            risk_count=len(risks),
            time_to_market_days=_money(source.get("time_to_market_days")),
        )
        decision_state = _roi_decision_state(
            opportunity_score=opportunity_score,
            blocked=bool(blocked_reasons),
            unknown_cost=unknown_cost,
            external_actions=bool(_requested_external_actions(source)),
        )
        net_benefit_per_hour = None
        if human_hours > 0 and projected_revenue is not None:
            net_benefit_per_hour = (projected_revenue - (costs or 0.0)) / human_hours
        audit = self._audit(
            "product_roi_decision_recorded",
            risk_level="high" if blocked_reasons or unknown_cost else "medium",
            approval_level="strong" if unknown_cost or _requested_external_actions(source) else "direct",
            metadata={"decision_id": decision_id, "decision_state": decision_state, "evidence_count": len(evidence)},
        )
        decision = {
            "schema_version": MONEY_ROI_SCHEMA_VERSION,
            "decision_id": decision_id,
            "title": title,
            "created_at": self.clock(),
            "decision_state": decision_state,
            "opportunity_score": opportunity_score,
            "expected_upside": _money_or_unknown(projected_revenue),
            "effort_estimate_hours": effort_hours,
            "cost_estimate": _money_or_unknown(costs),
            "time_to_market_days": _money_or_unknown(_money(source.get("time_to_market_days"))),
            "confidence": confidence,
            "confidence_score": confidence_score,
            "risks": risks,
            "dependency_list": dependencies,
            "human_time_required_hours": human_hours,
            "net_benefit_per_david_hour": _money_or_unknown(net_benefit_per_hour),
            "net_benefit_per_david_hour_is_projection": net_benefit_per_hour is not None,
            "financials": {
                "currency": _currency(source.get("currency")),
                "projected_revenue": _financial_amount(projected_revenue, projected=True, evidence=evidence, confidence=confidence),
                "confirmed_revenue": _financial_amount(confirmed_revenue, projected=False, evidence=evidence, confidence=confidence),
                "gross_revenue": _money_or_unknown(gross_revenue),
                "fees": fees,
                "costs": _money_or_unknown(costs),
                "net_revenue": _money_or_unknown(net_revenue),
                "projected_is_not_confirmed": True,
                "confirmed_revenue_requires_evidence": True,
                "unknown_cost_blocks_or_requires_strong_approval": unknown_cost,
            },
            "score_inputs": {
                "cost_included": True,
                "effort_included": True,
                "confidence_included": True,
                "risk_included": True,
                "time_to_market_included": True,
            },
            "blocked_reasons": _dedupe(blocked_reasons + (["unknown cost blocks or requires strong approval"] if unknown_cost else [])),
            "no_fake_revenue": True,
            "projections_labelled": True,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._roi_decisions[decision_id] = decision
        return decision

    def plan_experiment(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        experiment_id = _safe_id(source.get("experiment_id"), prefix="exp")
        blocked_reasons = _blocked_reasons(source)
        channel = _safe_text(_first_present(source, "channel", "experiment_channel"), "manual", limit=80).lower()
        external_requested = _requested_external_actions(source) or _channel_external_actions(channel)
        approval_requirement = "strong" if external_requested or _money(source.get("cost_cap")) not in (None, 0.0) else "direct"
        status = "blocked" if blocked_reasons else "approval_required" if approval_requirement != "direct" else "prepared"
        phase_8_candidate = None
        if self.phase_8_external_ops is not None and ("email" in channel or source.get("email_requested") or source.get("send_requested")):
            phase_8_response = self.phase_8_external_ops.prepare_email_candidate(
                provider=_safe_text(source.get("provider"), "unknown"),
                operation="draft",
                recipients=_safe_list(source.get("target_audience"))[:10],
                subject=_safe_text(source.get("subject"), "Experiment draft", limit=160),
                body=_safe_text(_first_present(source, "draft", "message", "action_plan"), "Experiment draft requires operator review.", limit=1200),
                send_requested=False,
                bulk_or_marketing=bool(source.get("bulk_or_marketing")),
            )
            phase_8_candidate = _phase_8_email_candidate_payload(phase_8_response)
        audit = self._audit(
            "product_experiment_plan_prepared",
            risk_level="high" if external_requested else "medium",
            approval_level=approval_requirement,
            metadata={"experiment_id": experiment_id, "channel": channel, "status": status},
        )
        experiment = {
            "schema_version": EXPERIMENT_PLANNER_SCHEMA_VERSION,
            "experiment_id": experiment_id,
            "created_at": self.clock(),
            "hypothesis": _safe_text(source.get("hypothesis"), UNKNOWN, limit=1000),
            "channel": channel,
            "target_audience": _safe_text(_first_present(source, "target_audience", "audience"), UNKNOWN, limit=500),
            "asset_needed": _safe_text(_first_present(source, "asset_needed", "asset"), "draft_or_local_asset_preview", limit=300),
            "cost_cap": _money_or_unknown(_money(source.get("cost_cap"))),
            "time_window": _safe_text(_first_present(source, "time_window", "time_limit"), UNKNOWN, limit=160),
            "success_metric": _safe_text(_first_present(source, "success_metric", "success_metrics"), UNKNOWN, limit=500),
            "expected_signal": _safe_text(source.get("expected_signal"), UNKNOWN, limit=500),
            "action_plan": _safe_list(source.get("action_plan")) or _default_experiment_action_plan(channel),
            "approval_requirement": approval_requirement,
            "status": status,
            "evidence": _safe_list(source.get("evidence")),
            "next_step": _safe_text(source.get("next_step"), "operator review; do not publish, post, email, scrape or spend by default", limit=500),
            "phase_8_candidate": phase_8_candidate,
            "blocked_reasons": blocked_reasons,
            "prepare_only": True,
            "would_post": False,
            "would_email": False,
            "would_scrape": False,
            "would_publish": False,
            "would_spend": False,
            "would_call_provider": False,
            "external_actions_go_through_phase_8": True,
            "readback_text": _readback("experiment", experiment_id, channel, "high" if external_requested else "medium", approval_requirement),
            "challenge_phrase": _challenge(experiment_id),
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._experiments[experiment_id] = experiment
        return experiment

    def record_revenue_event(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        event_id = _safe_id(source.get("revenue_event_id"), prefix="rev")
        event_type = _choice(source.get("type"), REVENUE_EVENT_TYPES, "projected")
        amount = _money(source.get("amount"))
        evidence = _safe_list(_first_present(source, "evidence", "source"))
        blocked_reasons = _blocked_reasons(source)
        confidence = _confidence_label(source.get("confidence"))
        status = "recorded_projected" if event_type == "projected" else "recorded"
        counts_as_confirmed = event_type == "confirmed"
        if event_type == "confirmed" and not evidence:
            status = "unconfirmed_missing_evidence"
            counts_as_confirmed = False
            blocked_reasons.append("confirmed revenue requires evidence/source")
        if "fake_revenue_request_blocked" in blocked_reasons:
            status = "rejected_fake_revenue"
            counts_as_confirmed = False
        audit = self._audit(
            "product_revenue_event_recorded",
            risk_level="high" if event_type in {"confirmed", "refund", "cost"} else "medium",
            approval_level="strong" if event_type in {"confirmed", "refund"} else "normal",
            metadata={"revenue_event_id": event_id, "type": event_type, "status": status, "evidence_count": len(evidence)},
        )
        event = {
            "schema_version": REVENUE_TRACKER_SCHEMA_VERSION,
            "revenue_event_id": event_id,
            "type": event_type,
            "status": status,
            "amount": _money_or_unknown(amount),
            "currency": _currency(source.get("currency")),
            "source": _safe_text(source.get("source"), "missing" if not evidence else "operator_provided", limit=300),
            "evidence": evidence,
            "timestamp": _safe_text(source.get("timestamp"), self.clock(), limit=80),
            "confidence": confidence,
            "linked_product": _safe_text(_first_present(source, "linked_product", "product_id", "product_name"), UNKNOWN, limit=160),
            "linked_mission": _safe_text(_first_present(source, "linked_mission", "mission_id"), UNKNOWN, limit=160),
            "linked_experiment": _safe_text(_first_present(source, "linked_experiment", "experiment_id"), UNKNOWN, limit=160),
            "counts_as_confirmed": counts_as_confirmed,
            "projected_revenue_counts_as_confirmed": False,
            "confirmed_revenue_requires_evidence": True,
            "net_formula": "net = gross - fees - costs - refunds",
            "blocked_reasons": _dedupe(blocked_reasons),
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._revenue_events[event_id] = event
        return event

    def revenue_summary(self, *, audit_read: bool = True) -> Dict[str, Any]:
        if audit_read:
            self._audit("product_revenue_summary_read", risk_level="low", approval_level="direct", metadata={"summary_read": True})
        projected = 0.0
        gross = 0.0
        fees = 0.0
        costs = 0.0
        refunds = 0.0
        currency = "USD"
        confirmed_events = 0
        for event in self._revenue_events.values():
            amount = event.get("amount")
            if not isinstance(amount, (int, float)):
                continue
            currency = event.get("currency") or currency
            if event.get("type") == "projected":
                projected += float(amount)
            elif event.get("type") == "confirmed" and event.get("counts_as_confirmed") is True:
                gross += float(amount)
                confirmed_events += 1
            elif event.get("type") == "fee":
                fees += float(amount)
            elif event.get("type") == "cost":
                costs += float(amount)
            elif event.get("type") == "refund":
                refunds += float(amount)
        return {
            "schema_version": REVENUE_TRACKER_SCHEMA_VERSION,
            "projected_revenue": projected,
            "confirmed_revenue": gross,
            "gross_revenue": gross,
            "fees": fees,
            "costs": costs,
            "refunds": refunds,
            "net_revenue": gross - fees - costs - refunds,
            "currency": currency,
            "confirmed_event_count": confirmed_events,
            "event_count": len(self._revenue_events),
            "projected_is_not_confirmed": True,
            "confirmed_revenue_requires_evidence": True,
            "no_fake_revenue": True,
            "evidence_required_for_confirmed": True,
            "metadata_only": True,
        }

    def evaluate_budget_guard(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        check_id = _safe_id(source.get("budget_check_id"), prefix="budget")
        global_budget = _money(_first_present(source, "global_monthly_product_budget", "monthly_budget"))
        mission_budget = _money(_first_present(source, "per_mission_budget", "mission_budget"))
        per_action_limit = _money(_first_present(source, "per_action_spending_limit", "per_action_max_cost"))
        provider_cost = _money(_first_present(source, "provider_cost_estimate", "estimated_cost", "proposed_cost"))
        confirmed_spend = _money(_first_present(source, "confirmed_spend_this_month", "confirmed_spend")) or 0.0
        evidence = _safe_list(_first_present(source, "confirmed_spend_evidence", "evidence"))
        spending_requested = bool(source.get("spending_requested", provider_cost is not None and provider_cost > 0))
        explicit_approval = bool(source.get("explicit_approval_present") or source.get("approval_present"))
        violations: List[str] = []
        decision = "allowed_prepare_only"
        if spending_requested and provider_cost is None:
            decision = "blocked_unknown_cost"
            violations.append("unknown provider cost blocks or requires strong approval")
        if provider_cost is not None and global_budget is not None and provider_cost + confirmed_spend > global_budget:
            decision = "blocked_over_global_monthly_product_budget"
            violations.append("provider cost estimate exceeds global monthly product budget")
        if provider_cost is not None and mission_budget is not None and provider_cost > mission_budget:
            decision = "blocked_over_per_mission_budget"
            violations.append("provider cost estimate exceeds per-mission budget")
        if provider_cost is not None and per_action_limit is not None and provider_cost > per_action_limit:
            decision = "blocked_over_per_action_limit"
            violations.append("provider cost estimate exceeds per-action spending limit")
        if spending_requested and not explicit_approval and not violations:
            decision = "requires_approval"
            violations.append("spending requires explicit approval")
        if confirmed_spend and not evidence:
            violations.append("confirmed spend requires evidence before consuming budget")
        phase_8_result = None
        if self.phase_8_external_ops is not None:
            phase_8_result = self.phase_8_external_ops.evaluate_budget_guard(
                audit_read=False,
                monthly_budget=global_budget,
                per_action_max_cost=per_action_limit,
                provider_cost_estimate=provider_cost,
                confirmed_spend_this_month=confirmed_spend,
                confirmed_spend_evidence=evidence,
                spending_requested=spending_requested,
                explicit_approval_present=explicit_approval,
            )
        audit = self._audit(
            "product_budget_guard_evaluated",
            risk_level="high" if violations else "medium",
            approval_level="strong" if spending_requested else "direct",
            metadata={"budget_check_id": check_id, "decision": decision, "violation_count": len(violations)},
        )
        result = {
            "schema_version": BUDGET_GUARD_V2_SCHEMA_VERSION,
            "budget_check_id": check_id,
            "decision": decision,
            "can_spend": False,
            "hard_stop": decision.startswith("blocked"),
            "global_monthly_product_budget": _money_or_unknown(global_budget),
            "per_mission_budget": _money_or_unknown(mission_budget),
            "per_action_spending_limit": _money_or_unknown(per_action_limit),
            "provider_cost_estimate": _money_or_unknown(provider_cost),
            "confirmed_spend_this_month": confirmed_spend,
            "confirmed_spend_evidence": evidence,
            "budget_consumed": confirmed_spend if evidence else 0.0,
            "budget_consumed_only_by_confirmed_evidence": True,
            "unknown_cost_handling": "blocked_or_requires_strong_approval",
            "approval_requirement": "strong" if spending_requested else "direct",
            "spending_requires_approval": True,
            "memory_preferences_can_expand_budget": False,
            "violations": _dedupe(violations),
            "phase_8_budget_guard": phase_8_result,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._budget_checks[check_id] = result
        return result

    def propose_self_improvement(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        proposal_id = _safe_id(source.get("proposal_id"), prefix="improve")
        blockers = _self_improvement_blockers(source)
        expected_value_score = _clamp_int(_money(source.get("expected_value_score")) or _money(source.get("expected_value")) or 50, 0, 100)
        risk = _choice(source.get("risk"), RISK_LEVELS, "medium")
        status = "blocked" if blockers else "prepared_candidate"
        audit = self._audit(
            "self_improvement_candidate_prepared",
            risk_level="critical" if blockers else risk,
            approval_level="blocked" if blockers else "strong",
            metadata={"proposal_id": proposal_id, "status": status, "blocker_count": len(blockers)},
        )
        proposal = {
            "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
            "proposal_id": proposal_id,
            "created_at": self.clock(),
            "status": status,
            "proposal_title": _safe_text(_first_present(source, "proposal_title", "title", "proposal"), "JARVIS improvement candidate", limit=180),
            "summary": _safe_text(_first_present(source, "summary", "proposal"), UNKNOWN, limit=1200),
            "expected_value_score": expected_value_score,
            "risks": _safe_list(source.get("risks")) or ["governance regression must be reviewed"],
            "patch_plan": _safe_list(_first_present(source, "patch_plan", "files_likely_to_change")) or [
                "Inspect current contracts and tests.",
                "Prepare a minimal patch plan.",
                "Keep PolicyEngine, ApprovalGateway and audit gates intact.",
            ],
            "tests": _safe_list(_first_present(source, "tests", "test_plan")) or [
                "Run targeted JARVIS governance tests.",
                "Run compatibility tests for affected phases.",
            ],
            "pr_description_preview": _safe_text(source.get("pr_description_preview"), "Draft PR description only; no PR will be opened by Phase 9.", limit=1500),
            "github_worktree_actions": [
                "github.diff.summary",
                "github.pr.prepare_description",
            ],
            "approval_requirement": "blocked" if blockers else "strong",
            "blocked_reasons": blockers,
            "can_inspect_docs_contracts": True,
            "can_prepare_patch_plan": True,
            "can_prepare_tests": True,
            "can_prepare_pr_description": True,
            "would_modify_policy_to_weaken_gates": False,
            "would_remove_approval_gateway": False,
            "would_remove_audit": False,
            "would_auto_merge": False,
            "would_auto_deploy": False,
            "would_commit_push_open_pr_merge": False,
            "would_bypass_tests": False,
            "prepare_only": True,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._self_improvements[proposal_id] = proposal
        return proposal

    def generate_operator_report(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        report_type = _choice(_first_present(source, "report_type", "type"), REPORT_TYPES, "daily_operator_report")
        report_id = _safe_id(source.get("report_id"), prefix="report")
        revenue = self.revenue_summary(audit_read=False)
        audit = self._audit(
            "operator_report_generated",
            risk_level="low",
            approval_level="direct",
            metadata={"report_id": report_id, "report_type": report_type},
        )
        report = {
            "schema_version": OPERATOR_REPORT_SCHEMA_VERSION,
            "report_id": report_id,
            "report_type": report_type,
            "created_at": self.clock(),
            "manual_trigger": True,
            "hidden_background_scheduler": False,
            "future_automation_readiness": True,
            "would_schedule_background_job": False,
            "would_notify": False,
            "would_email": False,
            "would_execute": False,
            "sections": {
                "product_operator_status": {
                    "mission_count": len(self._missions),
                    "builder_candidate_count": len(self._builder_candidates),
                    "experiment_count": len(self._experiments),
                    "self_improvement_proposal_count": len(self._self_improvements),
                },
                "pending_approvals": _pending_approval_items(
                    list(self._missions.values())
                    + list(self._builder_candidates.values())
                    + list(self._experiments.values())
                    + list(self._self_improvements.values())
                ),
                "budget": next(reversed(self._budget_checks.values()), {"decision": "not_evaluated"}) if self._budget_checks else {"decision": "not_evaluated"},
                "revenue": revenue,
                "experiments": _compact_items(self._experiments.values(), fields=("experiment_id", "channel", "status", "success_metric")),
                "blockers": _blocker_items(
                    list(self._builder_candidates.values())
                    + list(self._roi_decisions.values())
                    + list(self._experiments.values())
                    + list(self._self_improvements.values())
                ),
                "recommended_next_actions": _safe_list(source.get("recommended_next_actions")) or [
                    "Review active product mission scope, budget and expiration.",
                    "Approve only specific external candidates with readback/challenge when needed.",
                    "Record evidence before counting confirmed revenue or costs.",
                ],
            },
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._reports[report_id] = report
        return report

    def prepare_operating_loop(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        loop_id = _safe_id(source.get("loop_id"), prefix="loop")
        mission_id = _safe_text(source.get("mission_id"), "", limit=120)
        mission = self._missions.get(mission_id) if mission_id else None
        blocked_reasons = []
        if not mission:
            blocked_reasons.append("approved product mission envelope required before autonomous operating loop can run")
        audit = self._audit(
            "product_operating_loop_prepared",
            risk_level="medium",
            approval_level="normal",
            metadata={"loop_id": loop_id, "mission_id": mission_id or "missing", "blocked": bool(blocked_reasons)},
        )
        loop = {
            "schema_version": OPERATING_LOOP_SCHEMA_VERSION,
            "loop_id": loop_id,
            "mission_id": mission_id or None,
            "status": "blocked" if blocked_reasons else "prepared",
            "steps": [
                "observe",
                "propose",
                "plan",
                "prepare_assets",
                "request_approval",
                "execute_allowed_local_actions",
                "gather_evidence",
                "report",
                "learn",
                "propose_next_step",
            ],
            "stoppable": True,
            "stop_conditions": list(mission.get("stop_conditions", [])) if mission else [],
            "time_limit": mission.get("time_limit") if mission else UNKNOWN,
            "budget_limit": mission.get("budget_limit") if mission else UNKNOWN,
            "max_iterations": min(int(source.get("max_iterations") or 10), 25),
            "run_forever": False,
            "external_side_effects_without_approval": False,
            "provider_calls_without_approval": False,
            "hidden_background_loop": False,
            "approval_required_before_sensitive_step": True,
            "evidence_required_before_learning": True,
            "blocked_reasons": blocked_reasons,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._operating_loops[loop_id] = loop
        return loop

    def operating_loop_status(self) -> Dict[str, Any]:
        return {
            "schema_version": OPERATING_LOOP_SCHEMA_VERSION,
            "loop_count": len(self._operating_loops),
            "contract": [
                "observe",
                "propose",
                "plan",
                "prepare_assets",
                "request_approval",
                "execute_allowed_local_actions",
                "gather_evidence",
                "report",
                "learn",
                "propose_next_step",
            ],
            "stoppable": True,
            "run_forever_allowed": False,
            "scope_time_budget_required": True,
            "external_side_effects_require_phase_8_approval": True,
            "local_files_go_through_phase_7": True,
            "hidden_background_loop": False,
        }

    def voice_approval_readiness(self, values: Mapping[str, Any]) -> Dict[str, Any]:
        source = _safe_payload(values)
        operation_id = _safe_text(_first_present(source, "operation_id", "candidate_id", "mission_id"), "", limit=160)
        operation = self._find_product_operation(operation_id)
        device_id = _safe_text(source.get("device_id"), "", limit=160)
        active_voice_session = bool(source.get("active_voice_session"))
        readback = _safe_text(source.get("readback_text"), "", limit=1000)
        challenge = _safe_text(source.get("challenge_phrase"), "", limit=120)
        trusted_device = _trusted_device(self._get_device(device_id))
        reason = ""
        eligible = False
        if not operation:
            reason = "operation_not_found"
        elif operation.get("approval_level") in {"double", "triple", "blocked", "denied"}:
            reason = "voice_approval_not_eligible_for_double_triple_blocked_or_denied_product_operation"
        elif not trusted_device:
            reason = "trusted_device_required"
        elif not active_voice_session:
            reason = "active_voice_session_required"
        elif _normalize_readback(readback) != _normalize_readback(operation.get("readback_text")):
            reason = "exact_readback_required"
        elif challenge != operation.get("challenge_phrase"):
            reason = "exact_challenge_required"
        else:
            eligible = True
        audit = self._audit(
            "product_voice_approval_checked",
            risk_level=operation.get("risk", "high") if operation else "high",
            approval_level=operation.get("approval_level", "blocked") if operation else "blocked",
            metadata={"operation_id": operation_id, "eligible": eligible, "reason": reason},
        )
        return {
            "schema_version": PHASE_9_SCHEMA_VERSION,
            "operation_id": operation_id,
            "voice_approval_available": eligible,
            "reason": reason,
            "requires_trusted_device": True,
            "requires_active_voice_session": True,
            "requires_exact_readback": True,
            "requires_spoken_challenge": True,
            "requires_scope_and_expiration": True,
            "requires_audit": True,
            "wake_phrase_can_approve": False,
            "memory_grants_permission": False,
            "approval_level": operation.get("approval_level", UNKNOWN) if operation else UNKNOWN,
            "risk": operation.get("risk", UNKNOWN) if operation else UNKNOWN,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def _mission_envelope_from_values(self, source: Mapping[str, Any]) -> Dict[str, Any]:
        mission_id = _safe_id(source.get("mission_id"), prefix="pm")
        time_limit_seconds = _time_limit_seconds(_first_present(source, "time_limit_seconds", "time_limit", "duration_seconds"))
        expires_at = _safe_text(source.get("expires_at"), "", limit=80)
        if not expires_at and time_limit_seconds:
            expires_at = _after_seconds(time_limit_seconds)
        budget_limit = _money(source.get("budget_limit"))
        blocked_reasons = _blocked_reasons(source)
        risk = _risk_for_values(source, blocked_reasons=blocked_reasons)
        approval_level = _approval_level_for_values(source, risk=risk)
        forbidden = _safe_list(_first_present(source, "forbidden_actions", "denied_actions")) or list(DEFAULT_FORBIDDEN_ACTIONS)
        envelope = {
            "schema_version": PRODUCT_MISSION_ENVELOPE_SCHEMA_VERSION,
            "mission_id": mission_id,
            "title": _safe_text(source.get("title"), "", limit=180),
            "goal": _safe_text(_first_present(source, "goal", "objective"), "", limit=1000),
            "expected_outcome": _safe_text(source.get("expected_outcome"), "", limit=1000),
            "target_user_customer": _safe_text(_first_present(source, "target_user_customer", "target_customer", "target_user"), "", limit=500),
            "hypothesis": _safe_text(source.get("hypothesis"), "", limit=1000),
            "success_metric": _safe_text(_first_present(source, "success_metric", "success_metrics"), "", limit=500),
            "budget_limit": budget_limit,
            "currency": _currency(source.get("currency")),
            "time_limit": _safe_text(_first_present(source, "time_limit", "time_limit_seconds"), "", limit=120),
            "time_limit_seconds": time_limit_seconds,
            "scope": _safe_list(source.get("scope")),
            "allowed_tools_actions": _safe_list(_first_present(source, "allowed_tools_actions", "allowed_actions", "allowed_tools")),
            "forbidden_actions": forbidden,
            "approval_level": approval_level,
            "risk": risk,
            "status": _choice(source.get("status"), MISSION_STATUSES, "draft"),
            "evidence": _safe_list(source.get("evidence")),
            "stop_conditions": _safe_list(source.get("stop_conditions")),
            "audit_id": "",
            "created_at": self.clock(),
            "expires_at": expires_at,
            "blocked_reasons": blocked_reasons,
            "readback_text": _readback("product mission", mission_id, _safe_text(source.get("title"), "untitled", limit=120), risk, approval_level),
            "challenge_phrase": _challenge(mission_id),
            "no_unlimited_mission": True,
            "approve_all_forever_allowed": False,
            "policy_engine_bypass_allowed": False,
            "approval_gateway_bypass_allowed": False,
            "restriction_registry_bypass_allowed": False,
            "budget_guard_required": True,
            "audit_required": True,
            "memory_grants_permission": False,
            "wake_phrase_can_approve": False,
            "external_side_effects_disabled_by_default": True,
            "metadata_only": True,
        }
        return envelope

    def _validate_mission_envelope(self, envelope: Mapping[str, Any]) -> List[str]:
        errors: List[str] = []
        required_text = [
            "mission_id",
            "title",
            "goal",
            "expected_outcome",
            "target_user_customer",
            "hypothesis",
            "success_metric",
            "expires_at",
        ]
        for field in required_text:
            if not _safe_text(envelope.get(field), "", limit=1000):
                errors.append(f"{field} is required")
        if envelope.get("budget_limit") is None:
            errors.append("budget_limit is required and must be finite")
        elif envelope.get("budget_limit") < 0:
            errors.append("budget_limit cannot be negative")
        if not envelope.get("time_limit_seconds") or envelope.get("time_limit_seconds") <= 0:
            errors.append("time_limit/time_limit_seconds is required and must be finite")
        for field in ("scope", "allowed_tools_actions", "forbidden_actions", "stop_conditions"):
            if not _safe_list(envelope.get(field)):
                errors.append(f"{field} must contain at least one item")
        texts = [
            envelope.get("approval_level"),
            envelope.get("goal"),
            envelope.get("scope"),
            envelope.get("allowed_tools_actions"),
            envelope.get("forbidden_actions"),
        ]
        if _contains_blanket_approval(texts):
            errors.append("mission envelope cannot grant approve-all-forever or unlimited authority")
        if envelope.get("blocked_reasons"):
            errors.extend(envelope.get("blocked_reasons") or [])
        return _dedupe(errors)

    def _phase_8_candidates_for_product(self, source: Mapping[str, Any], *, product_name: str) -> Dict[str, Any]:
        if self.phase_8_external_ops is None:
            return {}
        results: Dict[str, Any] = {}
        results["deploy_candidate"] = self.phase_8_external_ops.prepare_deploy_candidate(
            provider=_safe_text(source.get("deploy_provider"), "unknown"),
            environment="preview",
            target=product_name,
            build_summary="Phase 9 product builder scaffold candidate; no deploy performed.",
            cost_estimate=source.get("deploy_cost_estimate"),
            rollback_plan=_safe_text(source.get("rollback_plan"), "Manual rollback plan required before any real deploy.", limit=500),
            rollback_available=bool(source.get("rollback_available")),
        ).get("candidate")
        results["email_candidate"] = self.phase_8_external_ops.prepare_email_candidate(
            provider=_safe_text(source.get("email_provider"), "unknown"),
            operation="draft",
            recipients=_safe_list(source.get("recipients")),
            subject=_safe_text(source.get("email_subject"), f"{product_name} validation draft", limit=160),
            body=_safe_text(source.get("email_body"), "Draft only; no send by default.", limit=1000),
            send_requested=False,
            bulk_or_marketing=False,
        ).get("candidate")
        results["payment_candidate"] = self.phase_8_external_ops.prepare_payment_candidate(
            provider="stripe",
            stripe_mode=_safe_text(source.get("stripe_mode"), "unknown"),
            product_name=product_name,
            amount=source.get("price_amount"),
            currency=_currency(source.get("currency")),
            recurring=bool(source.get("recurring")),
            money_movement_requested=False,
            charge_requested=False,
        ).get("candidate")
        return results

    def _governed_file_previews(self, file_candidates: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        previews: List[Dict[str, Any]] = []
        if self.phase_7_actions is None:
            return previews
        for item in file_candidates[:5]:
            try:
                preview = self.phase_7_actions.preview(
                    intent="Prepare Phase 9 local product package file candidate",
                    source="phase_9_product_operator",
                    operator="David",
                    action_key="filesystem.file.write_safe",
                    inputs={"path": item["path"], "content": item["content"]},
                )
            except Exception as exc:  # Preview failures should not become direct writes.
                preview = {
                    "state": "preview_failed",
                    "decision": "denied",
                    "error": _safe_text(str(exc), "preview failed", limit=240),
                    "action_key": "filesystem.file.write_safe",
                    "would_write_file": False,
                }
            previews.append(preview)
        return previews

    def _find_product_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        for collection in (
            self._missions,
            self._builder_candidates,
            self._experiments,
            self._self_improvements,
        ):
            if operation_id in collection:
                return collection[operation_id]
        return None

    def _get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        if not device_id or self.phase_7_actions is None:
            return None
        try:
            return self.phase_7_actions.phase5_store.get_device(device_id)
        except AttributeError:
            return None

    def _audit(
        self,
        event_type: str,
        *,
        risk_level: str = "low",
        approval_level: str = "direct",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.audit_ledger.record(
            event_type=event_type,
            surface="phase_9_product_operator",
            source="jarvis_phase_9",
            risk_level=risk_level,
            approval_level=approval_level,
            metadata={**dict(metadata or {}), "phase": "9", "metadata_only": True, "hermes_called": False},
            hermes_dispatch_allowed=False,
        )


def _phase_9_security_gates() -> Dict[str, Any]:
    return {
        "jarvis_governs": True,
        "hermes_executes_only_after_jarvis": True,
        "no_duplicate_hermes_runtime": True,
        "frontend_direct_hermes_allowed": False,
        "no_unsafe_execute_endpoint": True,
        "no_free_shell_from_ui": True,
        "no_fake_autonomous_work": True,
        "no_fake_revenue": True,
        "no_fake_customers": True,
        "no_fake_launch": True,
        "no_fake_deploy": True,
        "no_fake_payment": True,
        "no_provider_calls_by_default": True,
        "no_external_publication_by_default": True,
        "no_real_email_send_by_default": True,
        "no_live_stripe_payment": True,
        "no_money_movement": True,
        "spending_requires_approval": True,
        "memory_grants_permission": False,
        "wake_phrase_can_approve": False,
        "voice_approval_requires_trust_readback_challenge_scope_expiry_audit": True,
        "critical_requires_double_or_triple": True,
        "audit_required": True,
    }


def _phase_8_email_candidate_payload(response: Mapping[str, Any]) -> Dict[str, Any]:
    candidate = dict(response.get("candidate") or response)
    candidate.setdefault("category", "email")
    candidate.setdefault("operation", "draft")
    candidate["would_send_email"] = False
    candidate["would_call_provider"] = False
    candidate["would_scrape_contacts"] = False
    candidate["prepare_only"] = True
    candidate["phase_8_prepare_only_response"] = True
    return candidate


def _product_file_candidates(source: Mapping[str, Any], *, product_name: str) -> List[Dict[str, str]]:
    base = _safe_text(source.get("local_project_path"), "", limit=500)
    if not base:
        return []
    root = Path(base)
    slug = _slug(product_name) or "product-candidate"
    files = [
        ("PRODUCT_BRIEF.md", _markdown_product_brief(source, product_name=product_name)),
        ("LANDING_COPY.md", _markdown_landing_copy(source, product_name=product_name)),
        ("LAUNCH_CHECKLIST.md", _markdown_launch_checklist(product_name=product_name)),
    ]
    return [{"path": str(root / slug / name), "content": content} for name, content in files]


def _public_file_candidates(candidates: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    return [
        {
            "path": item["path"],
            "content_preview": item["content"][:1000],
            "content_length": len(item["content"]),
            "would_write": False,
            "phase_7_action_key": "filesystem.file.write_safe",
        }
        for item in candidates
    ]


def _markdown_product_brief(source: Mapping[str, Any], *, product_name: str) -> str:
    return "\n".join([
        f"# {product_name}",
        "",
        "## Problem",
        _safe_text(_first_present(source, "problem_statement", "problem"), UNKNOWN, limit=1200),
        "",
        "## Target Customer",
        _safe_text(_first_present(source, "target_customer", "audience"), UNKNOWN, limit=800),
        "",
        "## Value Proposition",
        _safe_text(_first_present(source, "value_proposition", "promise"), UNKNOWN, limit=1200),
        "",
        "## Evidence Rules",
        "- Do not claim launch, customers, revenue, deploy, payment or email send without evidence.",
        "- External actions require Phase 8 approval envelopes.",
        "- Local file creation must use Phase 7 filesystem governance.",
        "",
    ])


def _markdown_landing_copy(source: Mapping[str, Any], *, product_name: str) -> str:
    headline = _safe_text(source.get("headline"), f"{product_name} helps a specific customer solve a specific problem", limit=240)
    return "\n".join([
        f"# Landing Copy: {product_name}",
        "",
        f"Hero: {headline}",
        "",
        "Sections:",
        "- Problem",
        "- Outcome",
        "- How it works",
        "- Early access / manual validation call to action",
        "",
        "Compliance:",
        "- No fake testimonials.",
        "- No fabricated metrics.",
        "- No income guarantees.",
        "",
    ])


def _markdown_launch_checklist(*, product_name: str) -> str:
    return "\n".join([
        f"# Launch Checklist: {product_name}",
        "",
        "- Confirm mission envelope scope, budget, time limit and stop conditions.",
        "- Review product brief and landing copy.",
        "- Validate pricing as a candidate only.",
        "- Prepare deploy/email/payment envelopes through Phase 8 if needed.",
        "- Require approval, readback, challenge, rollback/stop plan and audit for external actions.",
        "- Record evidence before claiming revenue, customers, launch or experiment success.",
        "",
    ])


def _landing_structure(source: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "hero": _safe_text(source.get("headline"), UNKNOWN, limit=240),
        "sections": _safe_list(source.get("sections")) or ["Problem", "Outcome", "How it works", "Proof to collect", "CTA"],
        "cta": _safe_text(source.get("call_to_action"), "Join validation list", limit=160),
        "no_fake_testimonials": True,
        "no_fake_metrics": True,
    }


def _mvp_checklist(source: Mapping[str, Any]) -> List[str]:
    return _safe_list(source.get("mvp_checklist")) or [
        "Define one target customer and painful workflow.",
        "Prepare one landing page candidate.",
        "Prepare one local prototype/scaffold plan.",
        "Prepare pricing and payment candidates without live checkout.",
        "Define evidence needed for next iteration.",
    ]


def _tech_stack_recommendation(source: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "frontend": _safe_text(source.get("frontend_stack"), "static landing or existing web stack", limit=160),
        "backend": _safe_text(source.get("backend_stack"), "minimal API only if MVP needs persistence", limit=160),
        "storage": _safe_text(source.get("storage_stack"), "local file/spec first; database later with approval", limit=160),
        "payments": "Stripe candidate only through Phase 8; no live payment by default",
        "deploy": "preview/staging candidate only through Phase 8; no production deploy by default",
    }


def _build_plan(source: Mapping[str, Any]) -> List[str]:
    return _safe_list(source.get("build_plan")) or [
        "Write product brief and constraints.",
        "Prepare landing structure and copy.",
        "Prepare local scaffold file candidates.",
        "Prepare deploy/email/payment candidates without external side effects.",
        "Run manual validation checklist.",
    ]


def _asset_package(source: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "brief": True,
        "landing_copy": True,
        "mvp_checklist": True,
        "pricing_candidate": True,
        "email_draft_candidate": True,
        "stripe_candidate": True,
        "deploy_candidate": True,
        "visual_assets_generated": False,
        "external_asset_provider_called": False,
        "notes": _safe_text(source.get("asset_notes"), "Text/spec package only in Phase 9 backend.", limit=500),
    }


def _pricing_candidate(source: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "price_amount": _money_or_unknown(_money(_first_present(source, "price_amount", "monthly_price"))),
        "currency": _currency(source.get("currency")),
        "billing_interval": _safe_text(source.get("billing_interval"), "unknown", limit=80),
        "pricing_hypothesis": _safe_text(source.get("pricing_hypothesis"), UNKNOWN, limit=500),
        "projected_revenue": _money_or_unknown(_money(_first_present(source, "projected_revenue", "revenue_projection"))),
        "confirmed_revenue": UNKNOWN,
        "confirmed_requires_evidence": True,
        "would_charge": False,
        "would_create_checkout": False,
    }


def _deploy_candidate_stub(product_name: str) -> Dict[str, Any]:
    return {
        "category": "deploy",
        "target": product_name,
        "prepare_only": True,
        "would_deploy": False,
        "would_call_provider": False,
        "approval_level_required": "strong",
    }


def _email_candidate_stub(source: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "category": "email",
        "operation": "draft",
        "prepare_only": True,
        "would_send_email": False,
        "would_call_provider": False,
        "subject_preview": _safe_text(source.get("email_subject"), UNKNOWN, limit=160),
        "approval_level_required": "strong",
    }


def _payment_candidate_stub(source: Mapping[str, Any], product_name: str) -> Dict[str, Any]:
    return {
        "category": "payment",
        "provider": "stripe",
        "product_name": product_name,
        "amount": _money_or_unknown(_money(source.get("price_amount"))),
        "currency": _currency(source.get("currency")),
        "prepare_only": True,
        "would_create_checkout": False,
        "would_move_money": False,
        "would_call_stripe": False,
        "approval_level_required": "strong",
    }


def _launch_checklist() -> List[str]:
    return [
        "Mission envelope approved with scope, budget, time limit and stop conditions.",
        "Landing copy reviewed for no fake claims.",
        "Deploy candidate prepared through Phase 8 and approved before any real deploy.",
        "Email candidate remains draft until Phase 8 approval.",
        "Stripe/payment candidate remains test/preview until explicit approval.",
        "Revenue tracker has evidence before confirmed revenue is counted.",
        "Rollback/stop plan documented before external actions.",
    ]


def _opportunity_score(
    *,
    expected_upside: Optional[float],
    effort_hours: float,
    cost_estimate: Optional[float],
    confidence_score: float,
    risk_count: int,
    time_to_market_days: Optional[float],
) -> int:
    upside_points = min((expected_upside or 0.0) / 25.0, 30.0)
    confidence_points = confidence_score * 35.0
    effort_penalty = min(effort_hours / 2.0, 18.0)
    cost_penalty = min((cost_estimate or 0.0) / 20.0, 15.0)
    risk_penalty = min(risk_count * 5.0, 20.0)
    speed_points = 10.0 if time_to_market_days is not None and time_to_market_days <= 7 else 5.0 if time_to_market_days is not None and time_to_market_days <= 30 else 0.0
    return _clamp_int(upside_points + confidence_points + speed_points + 30.0 - effort_penalty - cost_penalty - risk_penalty, 0, 100)


def _roi_decision_state(*, opportunity_score: int, blocked: bool, unknown_cost: bool, external_actions: bool) -> str:
    if blocked:
        return "blocked"
    if unknown_cost:
        return "needs approval"
    if external_actions and opportunity_score >= 65:
        return "launch candidate"
    if opportunity_score >= 70:
        return "build candidate"
    if opportunity_score >= 50:
        return "prepare"
    if opportunity_score >= 30:
        return "watch"
    return "reject"


def _financial_amount(amount: Optional[float], *, projected: bool, evidence: List[str], confidence: str) -> Dict[str, Any]:
    return {
        "amount": _money_or_unknown(amount),
        "is_projection": projected,
        "counts_as_confirmed": bool(not projected and amount is not None and evidence),
        "evidence": evidence,
        "confidence": confidence,
    }


def _default_experiment_action_plan(channel: str) -> List[str]:
    if "reddit" in channel:
        return [
            "Prepare a post draft locally.",
            "Review community rules manually.",
            "Do not post without Phase 8 approval.",
            "Record qualitative replies as evidence.",
        ]
    if "email" in channel:
        return [
            "Prepare a cold email draft.",
            "Review recipient legitimacy and compliance.",
            "Do not send without Phase 8 approval.",
            "Record replies as evidence.",
        ]
    if "trend" in channel:
        return [
            "Prepare manual Google Trends checklist.",
            "Collect screenshots/notes as operator evidence.",
            "Do not scrape or call external providers by default.",
        ]
    return [
        "Prepare local prototype or manual validation asset.",
        "Run only manual/operator-controlled steps.",
        "Record evidence before deciding next iteration.",
    ]


def _channel_external_actions(channel: str) -> List[str]:
    actions = []
    if any(marker in channel for marker in ("reddit", "post", "publish", "directory", "listing")):
        actions.append("external_publication_candidate")
    if "email" in channel:
        actions.append("email_candidate")
    if any(marker in channel for marker in ("paid", "ads", "spend")):
        actions.append("spend_candidate")
    return actions


def _pending_approval_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pending = []
    for item in items:
        if item.get("approval_required") or item.get("approval_requirement") in {"normal", "strong", "double", "triple"}:
            pending.append({
                "id": item.get("mission_id") or item.get("candidate_id") or item.get("experiment_id") or item.get("proposal_id") or UNKNOWN,
                "approval_level": item.get("approval_level") or item.get("approval_requirement") or UNKNOWN,
                "risk": item.get("risk", UNKNOWN),
                "status": item.get("status", UNKNOWN),
            })
    return pending[:20]


def _blocker_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blockers = []
    for item in items:
        reasons = item.get("blocked_reasons") or []
        if reasons:
            blockers.append({
                "id": item.get("candidate_id") or item.get("decision_id") or item.get("experiment_id") or item.get("proposal_id") or UNKNOWN,
                "status": item.get("status") or item.get("decision_state") or UNKNOWN,
                "blocked_reasons": reasons,
            })
    return blockers[:20]


def _self_improvement_blockers(source: Mapping[str, Any]) -> List[str]:
    text = _payload_text(source)
    blockers = []
    for marker in SELF_IMPROVEMENT_FORBIDDEN_MARKERS:
        if marker in text:
            blockers.append(f"self-improvement cannot {marker}")
    return _dedupe(blockers)


def _blocked_reasons(source: Mapping[str, Any]) -> List[str]:
    text = _payload_text(source)
    reasons: List[str] = []
    for marker in HARD_DENIAL_MARKERS:
        if marker in text:
            normalized = marker.replace(" ", "_").replace("-", "_")
            if "revenue" in marker:
                reasons.append("fake_revenue_request_blocked")
            elif "customer" in marker:
                reasons.append("fake_customer_request_blocked")
            elif "launch" in marker:
                reasons.append("fake_launch_request_blocked")
            elif "bypass" in marker:
                reasons.append("policy_or_approval_bypass_request_blocked")
            else:
                reasons.append(f"{normalized}_blocked")
    if _contains_blanket_approval(source.values()):
        reasons.append("approve_all_forever_or_unlimited_scope_blocked")
    return _dedupe(reasons)


def _requested_external_actions(source: Mapping[str, Any]) -> List[str]:
    actions: List[str] = []
    for key in sorted(CRITICAL_ACTION_KEYS | STRONG_ACTION_KEYS):
        if bool(source.get(key)):
            actions.append(key.replace("_requested", ""))
    text = _payload_text(source)
    for marker, action in (
        ("production deploy", "production"),
        ("send email", "email_send"),
        ("mass email", "mass_email"),
        ("stripe live", "stripe_live"),
        ("payment link", "payment_link"),
        ("charge card", "payment_processing"),
        ("publish", "publish"),
        ("dns", "dns"),
    ):
        if marker in text:
            actions.append(action)
    return _dedupe(actions)


def _risk_for_values(source: Mapping[str, Any], *, blocked_reasons: List[str]) -> str:
    if blocked_reasons:
        return "denied"
    if any(bool(source.get(key)) for key in CRITICAL_ACTION_KEYS):
        return "critical"
    if any(bool(source.get(key)) for key in STRONG_ACTION_KEYS):
        return "high"
    if _money(_first_present(source, "budget_limit", "cost_cap", "provider_cost_estimate")) not in (None, 0.0):
        return "medium"
    return _choice(source.get("risk"), RISK_LEVELS, "low")


def _approval_level_for_values(source: Mapping[str, Any], *, risk: str) -> str:
    if risk == "denied":
        return "denied"
    if any(bool(source.get(key)) for key in CRITICAL_ACTION_KEYS):
        return "triple"
    if any(bool(source.get(key)) for key in STRONG_ACTION_KEYS):
        return "strong"
    if risk == "critical":
        return "triple"
    if risk == "high":
        return "strong"
    if risk == "medium":
        return "normal"
    return _choice(source.get("approval_level"), APPROVAL_LEVELS, "direct")


def _compact_items(items: Iterable[Mapping[str, Any]], *, fields: Iterable[str], limit: int = 8) -> List[Dict[str, Any]]:
    result = []
    for item in list(items)[-limit:]:
        result.append({field: item.get(field, UNKNOWN) for field in fields})
    return result


def _safe_payload(values: Mapping[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in dict(values or {}).items():
        key_text = _safe_text(key, "unknown", limit=80)
        if _sensitive_key(key_text):
            safe[key_text] = "[redacted sensitive input]"
        elif isinstance(value, Mapping):
            safe[key_text] = _safe_payload(value)
        elif isinstance(value, list):
            safe[key_text] = [_safe_value(item) for item in value[:50]]
        else:
            safe[key_text] = _safe_value(value)
    return safe


def _safe_value(value: Any) -> Any:
    if isinstance(value, str):
        return _safe_text(value, "", limit=5000)
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value if math.isfinite(float(value)) else None
    if isinstance(value, Mapping):
        return _safe_payload(value)
    if isinstance(value, list):
        return [_safe_value(item) for item in value[:50]]
    return _safe_text(str(value), "", limit=1000)


def _safe_text(value: Any, default: str = UNKNOWN, *, limit: int = 240) -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    text = _redact_sensitive_text(text)
    return text[:limit]


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [_safe_text(value, "", limit=500)] if value.strip() else []
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray, Mapping)):
        return [_safe_text(item, "", limit=500) for item in list(value)[:50] if _safe_text(item, "", limit=500)]
    return [_safe_text(value, "", limit=500)]


def _safe_id(value: Any, *, prefix: str) -> str:
    text = _safe_text(value, "", limit=120)
    if text:
        slug = _slug(text)
        if slug:
            return slug
    return f"{prefix}-{uuid4()}"


def _slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", str(value or "").strip().lower()).strip("-")[:80]


def _choice(value: Any, choices: set[str], default: str) -> str:
    normalized = str(value or "").strip().lower().replace("_", " ")
    for choice in choices:
        if normalized == choice or normalized.replace(" ", "_") == choice:
            return choice
    return default


def _money(value: Any) -> Optional[float]:
    if value in (None, "", UNKNOWN):
        return None
    if isinstance(value, bool):
        return None
    try:
        number = float(str(value).replace(",", "").strip())
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def _money_or_unknown(value: Optional[float]) -> Any:
    return value if value is not None else UNKNOWN


def _currency(value: Any) -> str:
    text = _safe_text(value, "USD", limit=12).upper()
    return text if re.fullmatch(r"[A-Z]{3}", text) else "USD"


def _confidence_label(value: Any) -> str:
    if isinstance(value, (int, float)):
        number = float(value)
        if number >= 0.75:
            return "high"
        if number >= 0.4:
            return "medium"
        return "low"
    return _choice(value, {"low", "medium", "high", UNKNOWN}, UNKNOWN)


def _confidence_score(label: str) -> float:
    return {"high": 0.85, "medium": 0.55, "low": 0.25}.get(label, 0.35)


def _first_present(source: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = source.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _payload_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join(_payload_text(item) for item in value.values()).lower()
    if isinstance(value, list):
        return " ".join(_payload_text(item) for item in value).lower()
    return str(value or "").lower()


def _contains_blanket_approval(values: Iterable[Any]) -> bool:
    text = _payload_text(list(values))
    return any(marker in text for marker in BLANKET_APPROVAL_MARKERS)


def _time_limit_seconds(value: Any) -> Optional[int]:
    if value in (None, "", UNKNOWN):
        return None
    number = _money(value)
    if number is not None:
        return int(number)
    text = str(value).strip().lower()
    match = re.match(r"^(\d+(?:\.\d+)?)\s*(seconds?|secs?|s|minutes?|mins?|m|hours?|hrs?|h|days?|d)$", text)
    if not match:
        return None
    amount = float(match.group(1))
    unit = match.group(2)
    if unit.startswith(("second", "sec", "s")):
        return int(amount)
    if unit.startswith(("minute", "min", "m")):
        return int(amount * 60)
    if unit.startswith(("hour", "hr", "h")):
        return int(amount * 3600)
    return int(amount * 86400)


def _after_seconds(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=max(1, int(seconds)))).isoformat()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _readback(kind: str, operation_id: str, summary: str, risk: str, approval_level: str) -> str:
    return (
        f"JARVIS solicita aprobar {kind} {operation_id}: {summary}. "
        f"Riesgo {risk}; aprobacion requerida {approval_level}; sin ejecucion externa por defecto."
    )


def _challenge(operation_id: str) -> str:
    return f"JARVIS-P9-{_slug(operation_id)[-6:].upper()}"


def _normalize_readback(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _trusted_device(device: Optional[Mapping[str, Any]]) -> bool:
    if not isinstance(device, Mapping):
        return False
    if device.get("trust_status") == "revoked" or device.get("revoked_at"):
        return False
    return bool(device.get("trusted") and device.get("verified") and device.get("paired"))


def _sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in ("secret", "token", "password", "credential", "cookie", "authorization", "private_key", "api_key"))


def _redact_sensitive_text(text: str) -> str:
    redacted = re.sub(r"\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9_=-]{8,}\b", "[redacted credential]", text)
    redacted = re.sub(r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{16,}\b", "[redacted credential]", redacted)
    redacted = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", "[redacted private key]", redacted, flags=re.DOTALL)
    return redacted


def _clamp_int(value: float, low: int, high: int) -> int:
    return max(low, min(high, int(round(value))))


def _dedupe(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        text = _safe_text(value, "", limit=500)
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result
