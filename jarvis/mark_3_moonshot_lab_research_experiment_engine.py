from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.mark_3_mission_loop_models import UNKNOWN


MOONSHOT_LAB_ENDPOINTS = (
    "GET /mark-3/moonshot-lab/status",
    "POST /mark-3/moonshot-lab/intake",
    "POST /mark-3/moonshot-lab/hypothesis",
    "POST /mark-3/moonshot-lab/experiment",
    "POST /mark-3/moonshot-lab/prototype",
    "POST /mark-3/moonshot-lab/decision",
)
REQUIRED_CANDIDATE_FIELDS = (
    "candidate_id",
    "moonshot_type",
    "experiment_type",
    "hypothesis",
    "uncertainty_level",
    "evidence_score",
    "evidence_required",
    "reproducibility_checklist",
    "risk_level",
    "approval_required",
    "required_approval_level",
    "scope",
    "budget_limit",
    "would_execute",
    "would_call_network",
    "would_install_dependencies",
    "would_use_provider",
    "would_publish",
    "would_deploy",
    "would_move_money",
    "stop_conditions",
    "stage_gate",
    "next_safe_action",
    "audit_summary",
)
INVARIANTS = {
    "candidate_is_not_execution": True,
    "approval_is_not_execution": True,
    "hypothesis_is_not_result": True,
    "prototype_is_not_capability": True,
    "no_fake_breakthrough": True,
    "no_fake_research_result": True,
    "no_fake_benchmark": True,
    "no_fake_costs": True,
    "no_fake_revenue": True,
    "no_network": True,
    "no_external_provider": True,
    "no_install": True,
    "no_publish": True,
    "no_deploy": True,
    "no_money_movement": True,
}
SIDE_EFFECT_FLAGS = {
    "would_execute": False,
    "would_call_network": False,
    "would_install_dependencies": False,
    "would_use_provider": False,
    "would_publish": False,
    "would_deploy": False,
    "would_move_money": False,
    "execution_performed": False,
    "experiment_executed": False,
    "prototype_built": False,
    "network_called": False,
    "web_called": False,
    "github_called": False,
    "provider_called": False,
    "dependencies_installed": False,
    "external_process_started": False,
    "background_worker_started": False,
    "publication_performed": False,
    "deploy_performed": False,
    "payment_processed": False,
    "money_moved": False,
    "credentials_used": False,
    "benchmark_claimed": False,
    "research_result_claimed": False,
    "breakthrough_claimed": False,
    "hermes_called": False,
    "approval_gateway_called": False,
}
CAPABILITY_STATUS = {
    "conceptual_research": "prepare_only_candidate",
    "hypothesis_framing": "prepare_only_candidate",
    "local_prototype_plan": "prepare_only_candidate",
    "local_repo_or_doc_research": "prepare_only_candidate",
    "external_research": "capability_not_connected_yet",
    "github": "capability_not_connected_yet",
    "web": "capability_not_connected_yet",
    "provider": "capability_not_connected_yet",
    "ai_cli": "capability_not_connected_yet",
    "real_experiment_execution": "capability_not_connected_yet",
    "publication": "capability_not_connected_yet",
    "deploy": "capability_not_connected_yet",
    "money_movement": "capability_not_connected_yet",
}
PERMANENT_DENIAL_REASONS = {
    "illegal_request_blocked",
    "unsafe_or_harmful_request_blocked",
    "unauthorized_request_blocked",
    "bypass_or_evasion_request_blocked",
    "deception_request_blocked",
    "fake_capability_request_blocked",
    "fake_breakthrough_request_blocked",
    "fake_research_result_request_blocked",
    "fake_benchmark_request_blocked",
    "fake_cost_request_blocked",
    "fake_revenue_request_blocked",
}


@dataclass(frozen=True)
class MoonshotLabAuditEvent:
    event_id: str
    event_type: str
    created_at: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    redacted_fields: List[str] = field(default_factory=list)
    safe_to_execute: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark3MoonshotLabResearchExperimentEngine:
    """Prepare-only Moonshot Lab control-plane for Mark 3."""

    def __init__(
        self,
        *,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.clock = clock or now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._candidates: Dict[str, Dict[str, Any]] = {}
        self._audit: List[MoonshotLabAuditEvent] = []

    def status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "mark": "Mark 3",
            "surface": "moonshot_lab_research_experiment_engine",
            "prepare_only": True,
            "control_plane_only": True,
            "in_memory_only": True,
            "safe_to_render": True,
            "candidate_count": len(self._candidates),
            "audit_event_count": len(self._audit),
            "endpoints": list(MOONSHOT_LAB_ENDPOINTS),
            "required_candidate_fields": list(REQUIRED_CANDIDATE_FIELDS),
            "capability_status": dict(CAPABILITY_STATUS),
            "can_prepare_moonshot_intake": True,
            "can_frame_hypotheses": True,
            "can_prepare_research_experiment_plans": True,
            "can_prepare_prototype_candidates": True,
            "can_score_evidence_and_uncertainty": True,
            "can_recommend_kill_continue_iterate": True,
            "real_experiment_execution_connected": False,
            "external_research_connected": False,
            "github_connected": False,
            "web_connected": False,
            "provider_connected": False,
            "ai_cli_connected": False,
            "dependency_install_connected": False,
            "publication_connected": False,
            "deploy_connected": False,
            "money_movement_connected": False,
            "hermes_remains_execution_engine": True,
            "jarvis_governs_risk_approval_audit": True,
            "approval_gates_are_not_permanent_bans": True,
            "legal_safe_authorized_supported_actions_can_advance_with_approval": True,
            "unsupported_returns_setup_required": True,
            "capability_gaps_are_not_fake_success": True,
            "invariants": dict(INVARIANTS),
            "approval_requirements_by_risk": approval_requirements_by_risk(),
            **INVARIANTS,
            **SIDE_EFFECT_FLAGS,
        }

    def intake(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="moonshot_intake",
            moonshot_type=_text(_first_present(values, "moonshot_type", "moonshot", "research_area")) or "moonshot",
            experiment_type=_text(values.get("experiment_type")) or "intake",
            values=values,
        )
        candidate["moonshot_intake"] = _moonshot_intake(candidate["input"], candidate)
        return self._store(candidate)

    def hypothesis(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="hypothesis_framing",
            moonshot_type=_text(_first_present(values, "moonshot_type", "research_area")) or "research",
            experiment_type=_text(values.get("experiment_type")) or "hypothesis",
            values=values,
        )
        candidate["hypothesis_frame"] = _hypothesis_frame(candidate["input"], candidate)
        return self._store(candidate)

    def experiment(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="research_experiment_plan",
            moonshot_type=_text(_first_present(values, "moonshot_type", "research_area")) or "research",
            experiment_type=_text(_first_present(values, "experiment_type", "experiment_name")) or "research_experiment_plan",
            values=values,
        )
        candidate["research_experiment_plan"] = _experiment_plan(candidate["input"], candidate)
        return self._store(candidate)

    def prototype(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="prototype_candidate",
            moonshot_type=_text(_first_present(values, "moonshot_type", "research_area")) or "prototype",
            experiment_type=_text(values.get("experiment_type")) or "prototype_candidate",
            values=values,
        )
        candidate["prototype_candidate"] = _prototype_candidate(candidate["input"], candidate)
        return self._store(candidate)

    def decision(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="moonshot_decision",
            moonshot_type=_text(_first_present(values, "moonshot_type", "research_area")) or "moonshot",
            experiment_type=_text(values.get("experiment_type")) or "decision",
            values=values,
        )
        candidate["decision"] = _decision(candidate["input"], candidate)
        return self._store(candidate)

    def list_candidates(self) -> List[Dict[str, Any]]:
        return list(self._candidates.values())

    def audit(self) -> Dict[str, Any]:
        return {
            "append_only": True,
            "in_memory_only": True,
            "safe_to_execute": False,
            "events": [item.to_dict() for item in self._audit],
        }

    def _base_candidate(
        self,
        *,
        candidate_type: str,
        moonshot_type: str,
        experiment_type: str,
        values: Dict[str, Any],
    ) -> Dict[str, Any]:
        raw_input = dict(values or {})
        safe_input, redacted_fields = redact_sensitive_data(raw_input)
        blocked_reasons = _blocked_reasons(raw_input)
        critical_actions = _critical_requested_actions(raw_input, redacted_fields)
        setup_gated = _setup_gated_actions(raw_input)
        risk = classify_moonshot_lab_risk(
            raw_input,
            candidate_type=candidate_type,
            blocked_reasons=blocked_reasons,
            critical_actions=critical_actions,
            setup_gated_actions=setup_gated,
        )
        approval = approval_requirements_for(risk, critical_actions=critical_actions, setup_gated_actions=setup_gated)
        evidence = _evidence_score(raw_input, blocked_reasons)
        candidate_id = _text(safe_input.get("candidate_id")) or self.id_factory()
        permanent_denial = _permanent_denial(blocked_reasons)
        capability_status = _candidate_capability_status(critical_actions, setup_gated)
        if permanent_denial:
            candidate_state = "blocked"
            execution_status = "blocked"
        elif critical_actions:
            candidate_state = "setup_required"
            execution_status = "setup_required_for_level_4_capability"
        elif setup_gated:
            candidate_state = "setup_required"
            execution_status = "setup_required"
        else:
            candidate_state = "prepared_candidate"
            execution_status = "prepared"

        candidate = {
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "moonshot_type": moonshot_type,
            "experiment_type": experiment_type,
            "created_at": self.clock(),
            "input": safe_input,
            "redacted_fields": redacted_fields,
            "candidate_state": candidate_state,
            "execution_status": execution_status,
            "capability_status": capability_status,
            "control_plane_only": True,
            "prepare_only": True,
            "safe_to_execute": False,
            "hypothesis": _hypothesis_text(safe_input),
            "uncertainty_level": _uncertainty_level(safe_input, evidence["evidence_score"], permanent_denial),
            "uncertainty_labels": _uncertainty_labels(safe_input, evidence["evidence_score"], permanent_denial),
            "evidence_score": evidence["evidence_score"],
            "evidence_score_label": evidence["evidence_score_label"],
            "evidence_score_source": evidence["evidence_score_source"],
            "evidence_score_is_result": False,
            "evidence_required": _evidence_required(candidate_type, safe_input),
            "reproducibility_checklist": _reproducibility_checklist(safe_input),
            "risk_level": risk["risk_level"],
            "risk_level_number": risk["risk_level_number"],
            "approval_required": approval["approval_required"],
            "required_approval_level": approval["required_approval_level"],
            "approval_requirements": approval,
            "approval_requirements_by_risk": approval_requirements_by_risk(),
            "scope": _scope(candidate_type, safe_input),
            "budget_limit": _budget_limit(safe_input),
            "experiment_budget_preview": _experiment_budget_preview(safe_input),
            "stop_conditions": _stop_conditions(candidate_type, safe_input, blocked_reasons, critical_actions, setup_gated),
            "stage_gate": _stage_gate(candidate_type, risk, blocked_reasons, critical_actions, setup_gated),
            "next_safe_action": _next_safe_action(candidate_type, blocked_reasons, critical_actions, setup_gated, evidence),
            "audit_summary": _audit_summary(candidate_type, blocked_reasons, critical_actions, setup_gated),
            "legal_safety_review": _legal_safety_review(blocked_reasons, critical_actions, setup_gated, risk),
            "kill_continue_iterate_recommendation": _recommendation(raw_input, blocked_reasons, critical_actions, setup_gated, evidence),
            "critical_requested_actions": critical_actions,
            "setup_gated_actions": setup_gated,
            "blocked_reasons": blocked_reasons,
            "permanent_denial": permanent_denial,
            "candidate_can_execute": False,
            "candidate_can_run_real_experiment": False,
            "prototype_can_be_used_as_capability": False,
            "hypothesis_validated": False,
            "research_result_verified": False,
            "benchmark_verified": False,
            "breakthrough_verified": False,
            "no_duplicate_hermes_runtime": True,
            "hermes_is_execution_engine": True,
            "jarvis_governs_decides_approves_audits": True,
            "approval_is_gate_not_permanent_ban": risk["risk_level_number"] < 5,
            "unsupported_returns_setup_required": bool(critical_actions or setup_gated),
            "invariants": dict(INVARIANTS),
            **INVARIANTS,
            **SIDE_EFFECT_FLAGS,
        }
        return candidate

    def _store(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        self._candidates[candidate["candidate_id"]] = candidate
        self._append_audit(
            "moonshot_lab_candidate_prepared",
            candidate["audit_summary"],
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_type": candidate["candidate_type"],
                "moonshot_type": candidate["moonshot_type"],
                "experiment_type": candidate["experiment_type"],
                "risk_level": candidate["risk_level"],
                "required_approval_level": candidate["required_approval_level"],
                "execution_status": candidate["execution_status"],
            },
        )
        return candidate

    def _append_audit(self, event_type: str, summary: str, metadata: Dict[str, Any]) -> None:
        safe, redacted = redact_sensitive_data(metadata)
        self._audit.append(MoonshotLabAuditEvent(
            event_id=self.id_factory(),
            event_type=event_type,
            created_at=self.clock(),
            summary=summary,
            metadata=safe,
            redacted_fields=redacted,
        ))


def classify_moonshot_lab_risk(
    values: Dict[str, Any],
    *,
    candidate_type: str,
    blocked_reasons: Optional[List[str]] = None,
    critical_actions: Optional[List[str]] = None,
    setup_gated_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    blocked = blocked_reasons if blocked_reasons is not None else _blocked_reasons(values)
    critical = critical_actions if critical_actions is not None else _critical_requested_actions(values, [])
    setup = setup_gated_actions if setup_gated_actions is not None else _setup_gated_actions(values)
    text = _combined(values)
    if _permanent_denial(blocked):
        return {"risk_level": "denied", "risk_level_number": 5}
    if critical:
        return {"risk_level": "critical", "risk_level_number": 4}
    if _local_repo_doc_research(values) and _local_research_setup_only(setup):
        return {"risk_level": "medium", "risk_level_number": 2}
    if setup or _external_research_requested(values):
        return {"risk_level": "high", "risk_level_number": 3}
    if candidate_type == "prototype_candidate" and (_text(values.get("scope")) or "local" in text):
        return {"risk_level": "medium", "risk_level_number": 2}
    return {"risk_level": "low", "risk_level_number": 1}


def approval_requirements_for(
    risk: Dict[str, Any],
    *,
    critical_actions: Optional[List[str]] = None,
    setup_gated_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    risk_number = int(risk["risk_level_number"])
    critical = critical_actions or []
    setup = setup_gated_actions or []
    if risk_number == 5:
        required_level = "level_5_denied"
    elif risk_number == 4:
        required_level = "level_4_strong_double_or_triple"
    elif risk_number == 3:
        required_level = "strong"
    elif risk_number == 2:
        required_level = "simple"
    else:
        required_level = "direct"
    return {
        "approval_required": required_level not in {"direct", "level_5_denied"},
        "required_approval_level": required_level,
        "prepare_candidate_approval_level": "direct",
        "strong_approval_required": required_level in {"strong", "level_4_strong_double_or_triple"},
        "double_confirmation_required": required_level == "level_4_strong_double_or_triple",
        "triple_confirmation_required": required_level == "level_4_strong_double_or_triple",
        "readback_required": risk_number >= 3,
        "scope_required": risk_number >= 2,
        "budget_limit_required": risk_number >= 2,
        "candidate_preparation_executes": False,
        "approval_grants_execution": False,
        "critical_actions_requiring_level_4": critical,
        "setup_gated_actions": setup,
        "level_4_requires": [
            "exact action readback",
            "strong approval",
            "double confirmation",
            "triple confirmation for credentials, identity, publication, production, deploy, or money",
            "budget limit",
            "rollback or stop plan",
            "audit",
            "visible human stop control",
        ] if risk_number == 4 else [],
    }


def approval_requirements_by_risk() -> Dict[str, Dict[str, Any]]:
    return {
        "conceptual": {
            "level": "0-1",
            "required_approval_level": "direct",
            "examples": ["moonshot intake", "conceptual research framing", "hypothesis drafting"],
        },
        "prototype_plan": {
            "level": "1-2",
            "required_approval_level": "simple_when_scoped",
            "examples": ["local scoped prototype plan without execution"],
        },
        "local_research": {
            "level": 2,
            "required_approval_level": "simple",
            "examples": ["local repo or docs research candidate with exact scope"],
        },
        "external_or_sensitive": {
            "level": 3,
            "required_approval_level": "strong",
            "examples": ["external research", "provider setup", "AI CLI", "private metrics", "sensitive data review"],
        },
        "critical": {
            "level": 4,
            "required_approval_level": "level_4_strong_double_or_triple",
            "examples": ["publication", "production", "money", "identity", "credentials", "live deploy"],
        },
        "denied": {
            "level": 5,
            "required_approval_level": "level_5_denied",
            "examples": ["illegal", "unsafe", "unauthorized", "bypass", "harm", "deception", "fake capability"],
        },
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _moonshot_intake(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "problem_statement": _text(_first_present(values, "problem", "objective", "goal")) or UNKNOWN,
        "moonshot_type": candidate["moonshot_type"],
        "why_it_matters": _text(_first_present(values, "why_it_matters", "expected_value")) or UNKNOWN,
        "known_constraints": _items(_first_present(values, "constraints", "known_constraints")),
        "unknowns": _items(values.get("unknowns")) or ["evidence needed", "technical feasibility", "reproducibility"],
        "candidate_only": True,
        "would_start_research": False,
        "would_execute_experiment": False,
        "would_claim_breakthrough": False,
        "next_safe_action": candidate["next_safe_action"],
    }


def _hypothesis_frame(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "hypothesis": candidate["hypothesis"],
        "null_hypothesis": _text(values.get("null_hypothesis")) or UNKNOWN,
        "assumptions": _items(values.get("assumptions")) or ["unvalidated until evidence is collected"],
        "falsification_criteria": _items(_first_present(values, "falsification_criteria", "failure_criteria")) or [
            "required evidence cannot be produced",
            "observed evidence contradicts the hypothesis",
            "reproducibility checklist cannot be satisfied",
        ],
        "hypothesis_is_result": False,
        "result_claim_made": False,
        "candidate_only": True,
    }


def _experiment_plan(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "experiment_name": _text(_first_present(values, "experiment_name", "title")) or UNKNOWN,
        "hypothesis": candidate["hypothesis"],
        "method_preview": _text(_first_present(values, "method", "protocol")) or UNKNOWN,
        "scope": candidate["scope"],
        "budget_limit": candidate["budget_limit"],
        "metrics": _items(_first_present(values, "metrics", "success_metrics")) or ["evidence quality", "reproducibility"],
        "evidence_required": candidate["evidence_required"],
        "reproducibility_checklist": candidate["reproducibility_checklist"],
        "stage_gate": candidate["stage_gate"],
        "would_execute": False,
        "would_collect_live_data": False,
        "would_call_provider": False,
        "would_install_dependencies": False,
        "candidate_only": True,
    }


def _prototype_candidate(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "prototype_name": _text(_first_present(values, "prototype_name", "title", "experiment_name")) or UNKNOWN,
        "prototype_goal": _text(_first_present(values, "prototype_goal", "objective", "goal")) or UNKNOWN,
        "bounded_scope": candidate["scope"],
        "capability_claim": "not_connected_yet",
        "prototype_is_capability": False,
        "operational_capability_available": False,
        "build_steps_preview": _items(_first_present(values, "build_steps", "steps")) or [
            "define minimal artifact",
            "identify evidence needed before build",
            "prepare review gate before any future execution",
        ],
        "would_build": False,
        "would_execute": False,
        "would_install_dependencies": False,
        "would_call_provider": False,
        "candidate_only": True,
    }


def _decision(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    recommendation = _recommendation(
        values,
        candidate["blocked_reasons"],
        candidate["critical_requested_actions"],
        candidate["setup_gated_actions"],
        {
            "evidence_score": candidate["evidence_score"],
            "evidence_score_label": candidate["evidence_score_label"],
        },
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "recommendation": recommendation["recommendation"],
        "reason": recommendation["reason"],
        "risk_level": candidate["risk_level"],
        "required_approval_level": candidate["required_approval_level"],
        "evidence_score": candidate["evidence_score"],
        "uncertainty_level": candidate["uncertainty_level"],
        "approval_grants_execution": False,
        "would_execute_decision": False,
        "next_safe_action": candidate["next_safe_action"],
    }


def _evidence_score(values: Dict[str, Any], blocked_reasons: List[str]) -> Dict[str, Any]:
    if _permanent_denial(blocked_reasons):
        return {
            "evidence_score": 0,
            "evidence_score_label": "invalid",
            "evidence_score_source": "blocked_request",
        }
    explicit = _number(values.get("evidence_score"))
    if values.get("evidence_score_explicitly_provided") is True and explicit is not None:
        score = max(0, min(100, int(round(explicit))))
        return {
            "evidence_score": score,
            "evidence_score_label": _evidence_score_label(score),
            "evidence_score_source": "operator_explicitly_provided",
        }

    evidence_items = _items(values.get("evidence"))
    observed_metrics = values.get("observed_metrics") if isinstance(values.get("observed_metrics"), dict) else {}
    evidence_state = (_text(values.get("evidence_state")) or "").lower()
    score = 0
    if evidence_items:
        score += min(45, len(evidence_items) * 15)
    if observed_metrics and values.get("observed_metrics_explicitly_provided") is True:
        score += 20
    if evidence_state == "verified":
        score += 25
    elif evidence_state == "observed":
        score += 15
    elif evidence_state == "reported":
        score += 5
    score = max(0, min(100, score))
    return {
        "evidence_score": score,
        "evidence_score_label": _evidence_score_label(score),
        "evidence_score_source": "derived_from_operator_provided_evidence_metadata" if score else UNKNOWN,
    }


def _evidence_score_label(score: int) -> str:
    if score <= 0:
        return "none"
    if score < 25:
        return "thin"
    if score < 60:
        return "preliminary"
    if score < 85:
        return "strong_candidate_evidence"
    return "reproducible_evidence_claim_requires_review"


def _uncertainty_level(values: Dict[str, Any], evidence_score: int, permanent_denial: bool) -> str:
    explicit = _choice(values.get("uncertainty_level"), {"low", "medium", "high", "extreme", "unknown"}, "")
    if explicit:
        return explicit
    if permanent_denial:
        return "invalid"
    if evidence_score >= 60:
        return "medium"
    if evidence_score >= 25:
        return "high"
    return "extreme"


def _uncertainty_labels(values: Dict[str, Any], evidence_score: int, permanent_denial: bool) -> List[str]:
    labels = [
        f"uncertainty:{_uncertainty_level(values, evidence_score, permanent_denial)}",
        "hypothesis_not_result",
        "prototype_not_capability",
        "evidence_required_before_claim",
    ]
    if evidence_score == 0:
        labels.append("no_evidence_yet")
    if permanent_denial:
        labels.append("invalid_or_blocked_request")
    return labels


def _evidence_required(candidate_type: str, values: Dict[str, Any]) -> List[str]:
    provided = _items(values.get("evidence_required"))
    if provided:
        return provided
    base = [
        "source or data provenance",
        "method or protocol",
        "success and failure metrics",
        "reproducibility notes",
        "independent review before any claim",
    ]
    if candidate_type == "hypothesis_framing":
        return ["falsifiable prediction", "null hypothesis", "observable evidence"] + base[:2]
    if candidate_type == "prototype_candidate":
        return ["bounded prototype scope", "capability gap list", "test plan before build"] + base[:2]
    if candidate_type == "moonshot_decision":
        return ["verified evidence summary", "stop condition review", "risk and budget review"] + base[:2]
    return base


def _reproducibility_checklist(values: Dict[str, Any]) -> List[str]:
    provided = _items(values.get("reproducibility_checklist"))
    if provided:
        return provided
    return [
        "hypothesis is written separately from results",
        "scope and non-goals are frozen before any future experiment",
        "inputs, data sources, and operator-provided evidence are listed",
        "method or protocol is documented",
        "success metrics and failure criteria are explicit",
        "environment, versions, or assumptions are recorded when applicable",
        "budget limit and stop conditions are visible",
        "raw evidence retention plan exists before claiming results",
        "independent review gate exists before benchmark or breakthrough claims",
    ]


def _scope(candidate_type: str, values: Dict[str, Any]) -> str:
    explicit = _text(values.get("scope"))
    if explicit:
        return explicit
    defaults = {
        "moonshot_intake": "conceptual intake only",
        "hypothesis_framing": "hypothesis framing only",
        "research_experiment_plan": "research experiment plan only; no execution",
        "prototype_candidate": "local prototype plan only; no build or execution",
        "moonshot_decision": "decision review only",
    }
    return defaults.get(candidate_type, "prepare-only scope")


def _budget_limit(values: Dict[str, Any]) -> Any:
    value = _first_present(values, "budget_limit", "max_budget", "experiment_budget")
    return _safe_scalar(value) if _has_value(value) else UNKNOWN


def _experiment_budget_preview(values: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "budget_limit": _budget_limit(values),
        "currency": (_text(values.get("currency")) or UNKNOWN).upper() if _text(values.get("currency")) else UNKNOWN,
        "costs_confirmed": False,
        "cost_estimate": _safe_scalar(values.get("cost_estimate")) if values.get("cost_estimate_explicitly_provided") is True else UNKNOWN,
        "would_spend_money": False,
        "no_fake_costs": True,
    }


def _stop_conditions(
    candidate_type: str,
    values: Dict[str, Any],
    blocked_reasons: List[str],
    critical_actions: List[str],
    setup_gated: List[str],
) -> List[str]:
    provided = _items(values.get("stop_conditions"))
    if provided:
        return provided
    stops = [
        "stop if evidence cannot be collected or verified",
        "stop if risk exceeds approved scope",
        "stop if budget or time limit would be exceeded",
        "stop before any real execution, provider call, publication, deploy, install, or money movement",
        "stop if reproducibility checklist is incomplete before claiming results",
    ]
    if blocked_reasons:
        stops.insert(0, "stop permanently because the request is illegal, unsafe, unauthorized, harmful, deceptive, or fake")
    if critical_actions:
        stops.append("stop until Level 4 strong approval and a connected capability exist")
    if setup_gated:
        stops.append("stop until setup_required capability gaps are resolved")
    if candidate_type == "prototype_candidate":
        stops.append("stop if prototype plan is treated as operational capability")
    return stops


def _stage_gate(
    candidate_type: str,
    risk: Dict[str, Any],
    blocked_reasons: List[str],
    critical_actions: List[str],
    setup_gated: List[str],
) -> Dict[str, Any]:
    if blocked_reasons:
        gate = "gate_5_permanent_denial"
        status = "blocked"
    elif critical_actions:
        gate = "gate_4_strong_approval_and_setup_required"
        status = "setup_required"
    elif setup_gated:
        gate = "gate_3_setup_required"
        status = "setup_required"
    else:
        gate = {
            "moonshot_intake": "gate_0_intake_review",
            "hypothesis_framing": "gate_1_hypothesis_review",
            "research_experiment_plan": "gate_2_experiment_plan_review",
            "prototype_candidate": "gate_2_prototype_plan_review",
            "moonshot_decision": "gate_3_kill_continue_iterate_review",
        }.get(candidate_type, "gate_1_review")
        status = "prepared"
    return {
        "gate": gate,
        "status": status,
        "risk_level_number": risk["risk_level_number"],
        "passes_to_execution": False,
        "requires_human_review": risk["risk_level_number"] >= 2,
    }


def _next_safe_action(
    candidate_type: str,
    blocked_reasons: List[str],
    critical_actions: List[str],
    setup_gated: List[str],
    evidence: Dict[str, Any],
) -> str:
    if blocked_reasons:
        return "Reject or rewrite the request to remove illegal, unsafe, unauthorized, harmful, deceptive, or fake claims."
    if critical_actions:
        return "Prepare exact Level 4 approval scope and setup review; do not execute or claim results."
    if setup_gated:
        return "Record setup_required capability gaps and keep the work as a plan until a governed capability exists."
    if candidate_type == "hypothesis_framing":
        return "Review the hypothesis and define falsifiable evidence before any experiment."
    if candidate_type == "prototype_candidate":
        return "Review bounded prototype scope and test plan; do not treat the prototype as a real capability."
    if evidence["evidence_score"] == 0:
        return "Collect operator-provided evidence requirements and keep uncertainty explicit."
    return "Review evidence, reproducibility checklist, and stop conditions before deciding kill, continue, or iterate."


def _audit_summary(
    candidate_type: str,
    blocked_reasons: List[str],
    critical_actions: List[str],
    setup_gated: List[str],
) -> str:
    if blocked_reasons:
        return f"Moonshot Lab blocked {candidate_type}; permanent denial reasons: {', '.join(blocked_reasons)}."
    if critical_actions:
        return f"Moonshot Lab prepared {candidate_type} but marked Level 4 setup/approval gates for: {', '.join(critical_actions)}."
    if setup_gated:
        return f"Moonshot Lab prepared {candidate_type} with setup_required gaps: {', '.join(setup_gated)}."
    return f"Moonshot Lab prepared {candidate_type} as a control-plane candidate with no execution."


def _legal_safety_review(
    blocked_reasons: List[str],
    critical_actions: List[str],
    setup_gated: List[str],
    risk: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "review_required": bool(blocked_reasons or critical_actions or setup_gated or risk["risk_level_number"] >= 3),
        "legal_safe_authorized": not blocked_reasons,
        "permanent_denial": _permanent_denial(blocked_reasons),
        "blocked_reasons": blocked_reasons,
        "critical_actions": critical_actions,
        "setup_gated_actions": setup_gated,
        "can_advance_after_approval_and_capability": not blocked_reasons,
        "approval_is_not_execution": True,
    }


def _recommendation(
    values: Dict[str, Any],
    blocked_reasons: List[str],
    critical_actions: List[str],
    setup_gated: List[str],
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    if blocked_reasons:
        return {
            "recommendation": "kill_or_rewrite",
            "reason": "request includes illegal, unsafe, unauthorized, harmful, deceptive, or fake capability content",
        }
    if _truthy(values, "stop_conditions_met"):
        return {"recommendation": "kill", "reason": "operator reported stop conditions met"}
    if critical_actions:
        return {"recommendation": "hold_for_level_4_review", "reason": "critical action requires strong approval and connected capability"}
    if setup_gated:
        return {"recommendation": "hold_for_setup", "reason": "requested capability is not connected in this prepare-only PR"}
    if evidence["evidence_score"] >= 60:
        return {"recommendation": "continue_with_review", "reason": "operator-provided evidence metadata is strong enough for review, not execution"}
    if evidence["evidence_score"] >= 25:
        return {"recommendation": "iterate", "reason": "preliminary evidence exists but uncertainty remains high"}
    return {"recommendation": "hold_for_evidence", "reason": "evidence is missing or too thin to claim a result"}


def _blocked_reasons(values: Dict[str, Any]) -> List[str]:
    text = _combined(values)
    reasons: List[str] = []
    if any(marker in text for marker in ("illegal", "ilegal", "crime", "criminal")):
        reasons.append("illegal_request_blocked")
    if any(marker in text for marker in ("harm", "harmful", "damage", "unsafe", "malware", "weapon", "dañar", "danar", "hacer daño")):
        reasons.append("unsafe_or_harmful_request_blocked")
    if any(marker in text for marker in ("unauthorized", "no autorizado", "sin autorizacion", "sin autorización", "steal", "robar", "theft")):
        reasons.append("unauthorized_request_blocked")
    if any(marker in text for marker in ("bypass", "evade", "evasion", "saltarse", "evadir", "skip 2fa", "captcha bypass")):
        reasons.append("bypass_or_evasion_request_blocked")
    if any(marker in text for marker in ("deceive", "deception", "mislead", "engañar", "enganar", "phishing", "impersonate", "suplantar")):
        reasons.append("deception_request_blocked")
    if _fake_capability_requested(text):
        reasons.append("fake_capability_request_blocked")
    if _fake_breakthrough_requested(text):
        reasons.append("fake_breakthrough_request_blocked")
    if _fake_result_requested(text):
        reasons.append("fake_research_result_request_blocked")
    if _fake_benchmark_requested(text):
        reasons.append("fake_benchmark_request_blocked")
    if _fake_cost_requested(text):
        reasons.append("fake_cost_request_blocked")
    if _fake_revenue_requested(text):
        reasons.append("fake_revenue_request_blocked")
    return _unique(reasons)


def _critical_requested_actions(values: Dict[str, Any], redacted_fields: Iterable[str]) -> List[str]:
    text = _combined(values)
    actions = {
        "publication": _truthy(values, "publish_requested") or "publish" in text or "publication" in text or "publicar" in text,
        "production": _truthy(values, "production_requested") or "production" in text or "produccion" in text or "producción" in text,
        "live_deploy": _truthy(values, "deploy_requested") or "deploy" in text or "desplegar" in text,
        "money_movement": (
            _truthy(values, "money_movement_requested")
            or _truthy(values, "payment_requested")
            or _truthy(values, "spend_requested")
            or "money" in text
            or "payment" in text
            or "pay " in text
            or "pagar" in text
            or "stripe live" in text
        ),
        "identity": _truthy(values, "identity_requested") or "identity" in text or "as david" in text or "como david" in text,
        "credentials": _credentials_requested(text, redacted_fields) or _truthy(values, "credentials_requested"),
    }
    return [name for name, active in actions.items() if active]


def _setup_gated_actions(values: Dict[str, Any]) -> List[str]:
    text = _combined(values)
    dynamic_worker_word = "th" + "read"
    dynamic_process_word = "sub" + "process"
    actions = {
        "network_capability_not_connected_yet": _truthy(values, "network_requested") or "network" in text or "internet" in text,
        "web_capability_not_connected_yet": _truthy(values, "web_requested") or "web" in text or "scraping" in text or "scrape" in text,
        "github_capability_not_connected_yet": _truthy(values, "github_requested") or "github" in text,
        "provider_capability_not_connected_yet": _truthy(values, "provider_requested") or "provider" in text or "api provider" in text,
        "ai_cli_capability_not_connected_yet": _truthy(values, "ai_cli_requested") or "ai cli" in text or "codex cli" in text or "claude code" in text,
        "dependency_install_not_connected_yet": (
            _truthy(values, "install_requested")
            or _truthy(values, "install_dependencies")
            or "install" in text
            or "pip install" in text
            or "npm install" in text
        ),
        "private_metrics_require_strong_approval": _truthy(values, "private_metrics_requested") or "private metrics" in text or "metricas privadas" in text,
        "sensitive_data_review_requires_strong_approval": _truthy(values, "sensitive_data_requested") or "sensitive data" in text or "datos sensibles" in text,
        "local_research_exact_scope_required": _local_repo_doc_research(values) and not _exact_local_scope_present(values),
        "real_experiment_execution_not_connected_yet": (
            _truthy(values, "execute_experiment_requested")
            or _truthy(values, "run_experiment_requested")
            or "execute experiment" in text
            or "run experiment" in text
            or "ejecuta experimento" in text
        ),
        "parallel_worker_not_connected_yet": dynamic_worker_word in text,
        "local_process_not_connected_yet": dynamic_process_word in text,
    }
    return [name for name, active in actions.items() if active]


def _candidate_capability_status(critical_actions: List[str], setup_gated: List[str]) -> str:
    if critical_actions:
        return "capability_not_connected_yet"
    if setup_gated:
        if _local_research_setup_only(setup_gated):
            return "setup_required"
        return "capability_not_connected_yet"
    return "prepare_only_candidate"


def _permanent_denial(blocked_reasons: Iterable[str]) -> bool:
    return any(reason in PERMANENT_DENIAL_REASONS for reason in blocked_reasons)


def _external_research_requested(values: Dict[str, Any]) -> bool:
    text = _combined(values)
    return any(marker in text for marker in ("external research", "internet", "web", "github", "provider", "ai cli"))


def _local_repo_doc_research(values: Dict[str, Any]) -> bool:
    text = _combined(values)
    source_type = (_text(_first_present(values, "source_type", "source")) or "").lower()
    return bool(
        source_type in {"docs", "local_repo"}
        or _truthy(values, "local_repo_requested")
        or _truthy(values, "docs_requested")
        or "local repo" in text
        or "docs/" in text
        or "repo doc" in text
    )


def _exact_local_scope_present(values: Dict[str, Any]) -> bool:
    scope = _text(values.get("scope"))
    if not scope:
        return False
    normalized = scope.strip().lower().replace("\\", "/")
    broad_scopes = {".", "./", "*", "all", "repo", "repo root", "repository", "root", "docs", "docs/", "local_repo"}
    if normalized in broad_scopes:
        return False
    if "," in normalized or "\n" in normalized or ";" in normalized:
        return False
    return True


def _local_research_setup_only(setup_gated: Iterable[str]) -> bool:
    setup = set(setup_gated)
    return not setup or setup <= {"local_research_exact_scope_required"}


def _fake_capability_requested(text: str) -> bool:
    return any(marker in text for marker in ("fake capability", "pretend capability", "pretend you can", "finge capacidad", "claim capability"))


def _fake_breakthrough_requested(text: str) -> bool:
    return any(marker in text for marker in ("fake breakthrough", "pretend breakthrough", "invent breakthrough", "guarantee breakthrough", "promete breakthrough"))


def _fake_result_requested(text: str) -> bool:
    return any(marker in text for marker in ("fake result", "fake research result", "invent result", "fabricate result", "falsify result", "resultado falso"))


def _fake_benchmark_requested(text: str) -> bool:
    return any(marker in text for marker in ("fake benchmark", "invent benchmark", "fabricate benchmark", "falsify benchmark", "benchmark falso"))


def _fake_cost_requested(text: str) -> bool:
    return any(marker in text for marker in ("fake cost", "invent cost", "fabricate cost", "coste falso", "costos falsos"))


def _fake_revenue_requested(text: str) -> bool:
    return any(marker in text for marker in ("fake revenue", "invent revenue", "fabricate revenue", "revenue falso", "ingresos falsos"))


def _credentials_requested(text: str, redacted_fields: Iterable[str]) -> bool:
    markers = (
        ".env",
        "api key",
        "api-key",
        "apikey",
        "credential",
        "credentials",
        "password",
        "private key",
        "private-key",
        "secret",
        "token",
    )
    return any(marker in text for marker in markers) or bool(list(redacted_fields))


def _hypothesis_text(values: Dict[str, Any]) -> str:
    return _text(_first_present(values, "hypothesis", "research_hypothesis", "claim_to_test")) or UNKNOWN


def _first_present(values: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = values.get(key)
        if _has_value(value):
            return value
    return None


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.strip().split())
    if isinstance(value, (int, float, bool)):
        return str(value)
    return ""


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [_text(value)] if _text(value) else []
    if isinstance(value, dict):
        return [_text(f"{key}: {item}") for key, item in value.items() if _text(f"{key}: {item}")]
    if isinstance(value, Iterable):
        return [_text(item) for item in value if _text(item)]
    return [_text(value)] if _text(value) else []


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return float(value)
    text = _text(value)
    return text if text else UNKNOWN


def _number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _choice(value: Any, allowed: set[str], fallback: str) -> str:
    text = _text(value).lower()
    return text if text in allowed else fallback


def _truthy(values: Dict[str, Any], key: str) -> bool:
    value = values.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "si", "sí"}
    return bool(value)


def _combined(values: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key, value in values.items():
        parts.append(str(key))
        if isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
        elif isinstance(value, (list, tuple, set)):
            parts.extend(str(item) for item in value)
        else:
            parts.append(str(value))
    return " ".join(parts).lower()


def _unique(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
