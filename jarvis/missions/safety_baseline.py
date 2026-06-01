from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.approval_bridge import MissionApprovalBridgeDecision, MissionApprovalBridgePayload
from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.command_builder import MissionCommand
from jarvis.missions.dry_run import MissionDryRunEvaluation, MissionDryRunRiskLevel
from jarvis.missions.envelope import ActionClassification
from jarvis.missions.state_store import MissionState


class MissionSafetyBaselineDecision(str, Enum):
    PASS_PREPARE_ONLY = "pass_prepare_only"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_STRONG_APPROVAL = "requires_strong_approval"
    BLOCKED = "blocked"
    DENIED = "denied"


@dataclass(frozen=True)
class MissionSafetyFinding:
    rule_id: str
    decision: MissionSafetyBaselineDecision
    risk_level: MissionDryRunRiskLevel
    message: str
    evidence_paths: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision", _coerce_enum(MissionSafetyBaselineDecision, self.decision, "decision"))
        object.__setattr__(self, "risk_level", _coerce_enum(MissionDryRunRiskLevel, self.risk_level, "risk_level"))
        object.__setattr__(self, "evidence_paths", _list_from(self.evidence_paths))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "decision": self.decision.value,
            "risk_level": self.risk_level.value,
            "message": self.message,
            "evidence_paths": list(self.evidence_paths),
        }


@dataclass(frozen=True)
class MissionSafetyBaselineValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class MissionSafetyBaselineResult:
    result_id: str
    mission_id: str
    decision: MissionSafetyBaselineDecision
    can_prepare: bool
    can_execute_later: bool
    requires_approval: bool
    approval_level: MissionApprovalLevel
    risk_level: MissionDryRunRiskLevel
    findings: List[MissionSafetyFinding]
    policy_notes: List[str]
    audit_summary: str
    created_at: str
    command_id: Optional[str] = None
    evaluation_id: Optional[str] = None
    payload_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.decision = _coerce_enum(MissionSafetyBaselineDecision, self.decision, "decision")
        self.approval_level = _coerce_enum(MissionApprovalLevel, self.approval_level, "approval_level")
        self.risk_level = _coerce_enum(MissionDryRunRiskLevel, self.risk_level, "risk_level")
        self.findings = [finding if isinstance(finding, MissionSafetyFinding) else MissionSafetyFinding(**finding) for finding in self.findings]
        self.policy_notes = _list_from(self.policy_notes)
        self.metadata = dict(self.metadata or {})

        result = validate_mission_safety_baseline_result(self)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "mission_id": self.mission_id,
            "command_id": self.command_id,
            "evaluation_id": self.evaluation_id,
            "payload_id": self.payload_id,
            "decision": self.decision.value,
            "can_prepare": self.can_prepare,
            "can_execute_later": self.can_execute_later,
            "requires_approval": self.requires_approval,
            "approval_level": self.approval_level.value,
            "risk_level": self.risk_level.value,
            "findings": [finding.to_dict() for finding in self.findings],
            "policy_notes": list(self.policy_notes),
            "audit_summary": self.audit_summary,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


def evaluate_mission_safety_baseline(
    state: MissionState,
    command: Optional[MissionCommand] = None,
    evaluation: Optional[MissionDryRunEvaluation] = None,
    payload: Optional[MissionApprovalBridgePayload] = None,
    *,
    evaluator: str = "jarvis",
) -> MissionSafetyBaselineResult:
    if not isinstance(state, MissionState):
        raise ValueError("state must be a MissionState")
    if command is not None and not isinstance(command, MissionCommand):
        raise ValueError("command must be a MissionCommand")
    if evaluation is not None and not isinstance(evaluation, MissionDryRunEvaluation):
        raise ValueError("evaluation must be a MissionDryRunEvaluation")
    if payload is not None and not isinstance(payload, MissionApprovalBridgePayload):
        raise ValueError("payload must be a MissionApprovalBridgePayload")

    findings = _collect_findings(state, command, evaluation, payload)
    decision = _max_decision([finding.decision for finding in findings])
    risk_level = _max_risk([finding.risk_level for finding in findings])
    approval_level = _approval_level_for(decision)
    requires_approval = decision in {
        MissionSafetyBaselineDecision.REQUIRES_REVIEW,
        MissionSafetyBaselineDecision.REQUIRES_APPROVAL,
        MissionSafetyBaselineDecision.REQUIRES_STRONG_APPROVAL,
    }

    policy_notes = [
        "Safety baseline gate is prepare-only; no approval, gateway call, execution, runtime connection, or state mutation was attempted."
    ]
    policy_notes.extend(f"{finding.rule_id}: {finding.message}" for finding in findings)

    return MissionSafetyBaselineResult(
        result_id=str(uuid4()),
        mission_id=state.mission_id,
        command_id=command.command_id if command is not None else None,
        evaluation_id=evaluation.evaluation_id if evaluation is not None else None,
        payload_id=payload.payload_id if payload is not None else None,
        decision=decision,
        can_prepare=decision == MissionSafetyBaselineDecision.PASS_PREPARE_ONLY,
        can_execute_later=False,
        requires_approval=requires_approval,
        approval_level=approval_level,
        risk_level=risk_level,
        findings=findings,
        policy_notes=policy_notes,
        audit_summary=_audit_summary(evaluator, state, command, decision, risk_level, findings),
        created_at=_now_iso(),
        metadata={
            "evaluator": _safe_text(evaluator or "jarvis"),
            "prepare_only": True,
            "approval_gateway_called": False,
            "hermes_connected": False,
            "finding_count": len(findings),
        },
    )


def validate_mission_safety_baseline_result(
    result: MissionSafetyBaselineResult,
) -> MissionSafetyBaselineValidationResult:
    errors: List[str] = []

    if not _is_non_empty_string(getattr(result, "result_id", "")):
        errors.append("result_id must be a non-empty string")
    if not _is_non_empty_string(getattr(result, "mission_id", "")):
        errors.append("mission_id must be a non-empty string")
    if not _is_non_empty_string(getattr(result, "audit_summary", "")):
        errors.append("audit_summary must be a non-empty string")

    try:
        decision = MissionSafetyBaselineDecision(getattr(result, "decision", ""))
    except ValueError:
        errors.append("decision must be a valid MissionSafetyBaselineDecision")
        decision = None

    try:
        approval_level = MissionApprovalLevel(getattr(result, "approval_level", ""))
    except ValueError:
        errors.append("approval_level must be a valid MissionApprovalLevel")
        approval_level = None

    try:
        MissionDryRunRiskLevel(getattr(result, "risk_level", ""))
    except ValueError:
        errors.append("risk_level must be a valid MissionDryRunRiskLevel")

    findings = getattr(result, "findings", None)
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        findings = []
    elif not all(isinstance(finding, MissionSafetyFinding) for finding in findings):
        errors.append("findings must contain MissionSafetyFinding items")

    policy_notes = getattr(result, "policy_notes", None)
    if not isinstance(policy_notes, list):
        errors.append("policy_notes must be a list")

    metadata = getattr(result, "metadata", None)
    if not isinstance(metadata, dict):
        errors.append("metadata must be a dict")
        metadata = {}
    elif not _is_simple_metadata(metadata):
        errors.append("metadata must contain only simple serializable values")

    if getattr(result, "can_execute_later", False):
        errors.append("safety baseline result cannot permit execution later")

    if decision == MissionSafetyBaselineDecision.PASS_PREPARE_ONLY:
        if getattr(result, "requires_approval", False):
            errors.append("pass_prepare_only cannot require approval")
        if approval_level != MissionApprovalLevel.ALLOWED:
            errors.append("pass_prepare_only requires approval_level allowed")
    elif decision in {
        MissionSafetyBaselineDecision.REQUIRES_REVIEW,
        MissionSafetyBaselineDecision.REQUIRES_APPROVAL,
        MissionSafetyBaselineDecision.REQUIRES_STRONG_APPROVAL,
    }:
        if not getattr(result, "requires_approval", False):
            errors.append("review or approval safety decisions require requires_approval true")
    elif decision in {MissionSafetyBaselineDecision.BLOCKED, MissionSafetyBaselineDecision.DENIED}:
        if getattr(result, "can_prepare", False):
            errors.append("blocked or denied safety decisions cannot prepare")

    secret_paths = _secret_like_paths(metadata)
    if secret_paths:
        errors.append("metadata cannot include secret-like keys or values: " + ", ".join(secret_paths))

    blanket_paths = _blanket_approval_paths(
        {
            "audit_summary": getattr(result, "audit_summary", ""),
            "policy_notes": policy_notes or [],
            "metadata": metadata,
        }
    )
    if blanket_paths:
        errors.append("safety baseline result cannot contain vague blanket approval: " + ", ".join(blanket_paths))

    return MissionSafetyBaselineValidationResult(errors=errors)


def _collect_findings(
    state: MissionState,
    command: Optional[MissionCommand],
    evaluation: Optional[MissionDryRunEvaluation],
    payload: Optional[MissionApprovalBridgePayload],
) -> List[MissionSafetyFinding]:
    findings: List[MissionSafetyFinding] = []
    envelope = state.envelope
    combined_text = _combined_text(state, command, evaluation, payload)

    secret_paths = _secret_like_paths(
        {
            "state.metadata": state.metadata,
            "command.inputs": command.inputs if command is not None else {},
            "command.metadata": command.metadata if command is not None else {},
            "evaluation.metadata": evaluation.metadata if evaluation is not None else {},
            "payload.metadata": payload.metadata if payload is not None else {},
        }
    )
    if secret_paths:
        findings.append(
            _finding(
                "secrets_in_inputs_or_metadata",
                MissionSafetyBaselineDecision.BLOCKED,
                MissionDryRunRiskLevel.CRITICAL,
                "Inputs or metadata include secret-like keys or values.",
                secret_paths,
            )
        )

    blanket_paths = _blanket_approval_paths(
        {
            "envelope": envelope.to_dict(),
            "state.metadata": state.metadata,
            "command": command.to_dict() if command is not None else {},
            "evaluation": evaluation.to_dict() if evaluation is not None else {},
            "payload": payload.to_dict() if payload is not None else {},
        }
    )
    if blanket_paths:
        findings.append(
            _finding(
                "blanket_approval_language",
                MissionSafetyBaselineDecision.BLOCKED,
                MissionDryRunRiskLevel.CRITICAL,
                "Vague blanket approval language is not allowed.",
                blanket_paths,
            )
        )

    if _mentions_any(combined_text, _DEPLOY_TERMS) and not _has_rollback(envelope):
        findings.append(
            _finding(
                "deploy_or_production_without_rollback",
                MissionSafetyBaselineDecision.BLOCKED,
                MissionDryRunRiskLevel.HIGH,
                "Deploy or production actions require an explicit rollback plan before approval can be prepared.",
                ["envelope.rollback_plan"],
            )
        )

    if _mentions_any(combined_text, _SPEND_TERMS) and envelope.budget_limit is None:
        findings.append(
            _finding(
                "spend_without_budget_limit",
                MissionSafetyBaselineDecision.BLOCKED,
                MissionDryRunRiskLevel.HIGH,
                "Spending or payment actions require a visible mission budget_limit.",
                ["envelope.budget_limit"],
            )
        )

    if _mentions_any(combined_text, _EXTERNAL_CONTACT_TERMS) and not _has_at_least_approval(command, payload):
        findings.append(
            _finding(
                "external_contact_without_approval",
                MissionSafetyBaselineDecision.REQUIRES_APPROVAL,
                MissionDryRunRiskLevel.MEDIUM,
                "External contact requires explicit approval before any future execution.",
                ["command.action", "payload.decision"],
            )
        )

    if _mentions_any(combined_text, _COMMERCIAL_PUBLICATION_TERMS) and not _has_strong_approval(command, payload):
        findings.append(
            _finding(
                "commercial_publication_without_strong_approval",
                MissionSafetyBaselineDecision.REQUIRES_STRONG_APPROVAL,
                MissionDryRunRiskLevel.HIGH,
                "Commercial publication or identity-bearing publishing requires strong approval.",
                ["command.action", "payload.decision"],
            )
        )

    if command is not None and _is_candidate_tool_only(state, command.tool_name) and not _has_tool_evaluation(evaluation, payload):
        findings.append(
            _finding(
                "tool_adoption_without_evaluation",
                MissionSafetyBaselineDecision.REQUIRES_REVIEW,
                MissionDryRunRiskLevel.MEDIUM,
                "Candidate tools require review/evaluation before adoption or execution.",
                ["command.tool_name", "envelope.candidate_tools"],
            )
        )

    if command is not None and command.classification == ActionClassification.UNKNOWN_REQUIRES_REVIEW:
        findings.append(
            _finding(
                "action_outside_mission_scope",
                MissionSafetyBaselineDecision.BLOCKED,
                MissionDryRunRiskLevel.HIGH,
                "Action is outside the explicit Mission Envelope scope.",
                ["command.action", "envelope.allowed_actions"],
            )
        )

    if _mentions_any(combined_text, _PUBLIC_AI_CONTENT_TERMS) and not _has_review_or_approval(command, payload):
        findings.append(
            _finding(
                "public_ai_content_needs_review",
                MissionSafetyBaselineDecision.REQUIRES_REVIEW,
                MissionDryRunRiskLevel.MEDIUM,
                "Public or commercial AI-generated content requires human review before publishing.",
                ["command.action", "payload.decision"],
            )
        )

    if _mentions_any(combined_text, _DECEPTIVE_IMPERSONATION_TERMS):
        findings.append(
            _finding(
                "deceptive_impersonation_or_deepfake",
                MissionSafetyBaselineDecision.DENIED,
                MissionDryRunRiskLevel.CRITICAL,
                "Deceptive impersonation or deepfake requests are denied by the safety baseline.",
                ["command.action", "command.inputs", "payload.reason"],
            )
        )

    if payload is not None and payload.decision == MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED:
        if _mentions_any(combined_text, _STRONG_APPROVAL_TERMS):
            findings.append(
                _finding(
                    "sensitive_action_without_bridge_approval",
                    MissionSafetyBaselineDecision.REQUIRES_STRONG_APPROVAL,
                    MissionDryRunRiskLevel.HIGH,
                    "Sensitive money, identity, production, credential, contract, or publication action cannot bypass strong approval.",
                    ["payload.decision", "command.action"],
                )
            )

    return findings


def _finding(
    rule_id: str,
    decision: MissionSafetyBaselineDecision,
    risk_level: MissionDryRunRiskLevel,
    message: str,
    evidence_paths: List[str],
) -> MissionSafetyFinding:
    return MissionSafetyFinding(
        rule_id=rule_id,
        decision=decision,
        risk_level=risk_level,
        message=message,
        evidence_paths=evidence_paths,
    )


def _combined_text(
    state: MissionState,
    command: Optional[MissionCommand],
    evaluation: Optional[MissionDryRunEvaluation],
    payload: Optional[MissionApprovalBridgePayload],
) -> str:
    values: List[Any] = [
        state.metadata,
        [
            value
            for value in [
                state.envelope.identity_use_policy,
                state.envelope.publication_policy,
                state.envelope.spending_policy,
                state.envelope.external_contact_policy,
                state.envelope.install_dependency_policy,
                state.envelope.runtime_execution_policy,
            ]
            if _is_non_empty_string(value)
        ],
    ]
    if command is not None:
        values.append(
            {
                "action": command.action,
                "reason": command.reason,
                "scope": command.scope,
                "inputs": command.inputs,
                "metadata": command.metadata,
                "tool_name": command.tool_name,
                "channel": command.channel,
            }
        )
    if evaluation is not None:
        values.append(
            {
                "action": evaluation.action,
                "blocked_reason": evaluation.blocked_reason,
                "policy_notes": evaluation.policy_notes,
                "audit_summary": evaluation.audit_summary,
                "metadata": evaluation.metadata,
            }
        )
    if payload is not None:
        values.append(
            {
                "action": payload.action,
                "reason": payload.reason,
                "scope": payload.scope,
                "blocked_reason": payload.blocked_reason,
                "policy_notes": payload.policy_notes,
                "audit_summary": payload.audit_summary,
                "metadata": payload.metadata,
            }
        )
    return _normalize(" ".join(_flatten_text(values)))


def _flatten_text(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        items: List[str] = []
        for key, item in value.items():
            items.append(str(key))
            items.extend(_flatten_text(item))
        return items
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(_flatten_text(item))
        return items
    return [str(value)]


def _has_rollback(envelope: Any) -> bool:
    return _is_non_empty_string(getattr(envelope, "rollback_plan", None))


def _has_at_least_approval(
    command: Optional[MissionCommand],
    payload: Optional[MissionApprovalBridgePayload],
) -> bool:
    return _has_review_or_approval(command, payload) and not (
        payload is not None and payload.decision == MissionApprovalBridgeDecision.REQUIRES_REVIEW
    )


def _has_review_or_approval(
    command: Optional[MissionCommand],
    payload: Optional[MissionApprovalBridgePayload],
) -> bool:
    if command is not None and command.requires_approval:
        return True
    if payload is not None and payload.decision in {
        MissionApprovalBridgeDecision.REQUIRES_REVIEW,
        MissionApprovalBridgeDecision.REQUIRES_APPROVAL,
        MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL,
    }:
        return True
    return False


def _has_strong_approval(
    command: Optional[MissionCommand],
    payload: Optional[MissionApprovalBridgePayload],
) -> bool:
    if command is not None and command.approval_level == MissionApprovalLevel.STRONG_APPROVAL:
        return True
    if payload is not None and payload.strong_approval_required:
        return True
    return False


def _has_tool_evaluation(
    evaluation: Optional[MissionDryRunEvaluation],
    payload: Optional[MissionApprovalBridgePayload],
) -> bool:
    if evaluation is not None and evaluation.requires_approval:
        return True
    if payload is not None and payload.decision in {
        MissionApprovalBridgeDecision.REQUIRES_REVIEW,
        MissionApprovalBridgeDecision.REQUIRES_APPROVAL,
        MissionApprovalBridgeDecision.REQUIRES_STRONG_APPROVAL,
    }:
        return True
    return False


def _is_candidate_tool_only(state: MissionState, tool_name: Optional[str]) -> bool:
    normalized = _normalize(tool_name)
    if not normalized:
        return False
    allowed_tools = {_normalize(tool) for tool in state.envelope.allowed_tools}
    candidate_tools = {_normalize(tool) for tool in state.envelope.candidate_tools}
    return normalized in candidate_tools and normalized not in allowed_tools


def _secret_like_paths(value: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if _is_secret_like(str(key)) or _is_secret_like(item):
                paths.append(key_path)
            paths.extend(_secret_like_paths(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]"
            if _is_secret_like(item):
                paths.append(item_path)
            paths.extend(_secret_like_paths(item, item_path))
    elif _is_secret_like(value) and prefix:
        paths.append(prefix)
    return paths


def _is_secret_like(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = _normalize(value)
    if normalized in _SECRET_LIKE_KEYS:
        return True
    if any(fragment in normalized for fragment in _SECRET_LIKE_FRAGMENTS):
        return True
    return any(normalized.startswith(prefix) for prefix in _SECRET_VALUE_PREFIXES)


def _blanket_approval_paths(value: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if _contains_blanket_approval(str(key)):
                paths.append(key_path)
            paths.extend(_blanket_approval_paths(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_blanket_approval_paths(item, f"{prefix}[{index}]"))
    elif isinstance(value, str) and _contains_blanket_approval(value):
        paths.append(prefix or "value")
    return paths


def _contains_blanket_approval(value: str) -> bool:
    normalized = _normalize(value)
    return any(phrase in normalized for phrase in _BLANKET_APPROVAL_PHRASES)


def _mentions_any(text: str, terms: set[str]) -> bool:
    tokens = set(re.findall(r"[a-z0-9]+", text.replace("_", " ")))
    for term in terms:
        if " " in term or "-" in term:
            if term in text:
                return True
        elif term in tokens:
            return True
    return False


def _max_decision(decisions: List[MissionSafetyBaselineDecision]) -> MissionSafetyBaselineDecision:
    if not decisions:
        return MissionSafetyBaselineDecision.PASS_PREPARE_ONLY
    order = {
        MissionSafetyBaselineDecision.PASS_PREPARE_ONLY: 0,
        MissionSafetyBaselineDecision.REQUIRES_REVIEW: 1,
        MissionSafetyBaselineDecision.REQUIRES_APPROVAL: 2,
        MissionSafetyBaselineDecision.REQUIRES_STRONG_APPROVAL: 3,
        MissionSafetyBaselineDecision.BLOCKED: 4,
        MissionSafetyBaselineDecision.DENIED: 5,
    }
    return max(decisions, key=lambda decision: order[decision])


def _max_risk(risks: List[MissionDryRunRiskLevel]) -> MissionDryRunRiskLevel:
    if not risks:
        return MissionDryRunRiskLevel.LOW
    order = {
        MissionDryRunRiskLevel.LOW: 0,
        MissionDryRunRiskLevel.MEDIUM: 1,
        MissionDryRunRiskLevel.HIGH: 2,
        MissionDryRunRiskLevel.CRITICAL: 3,
        MissionDryRunRiskLevel.UNKNOWN: 4,
    }
    return max(risks, key=lambda risk: order[risk])


def _approval_level_for(decision: MissionSafetyBaselineDecision) -> MissionApprovalLevel:
    if decision == MissionSafetyBaselineDecision.PASS_PREPARE_ONLY:
        return MissionApprovalLevel.ALLOWED
    if decision == MissionSafetyBaselineDecision.REQUIRES_REVIEW:
        return MissionApprovalLevel.REQUIRES_REVIEW
    if decision == MissionSafetyBaselineDecision.REQUIRES_APPROVAL:
        return MissionApprovalLevel.REQUIRES_APPROVAL
    if decision == MissionSafetyBaselineDecision.REQUIRES_STRONG_APPROVAL:
        return MissionApprovalLevel.STRONG_APPROVAL
    return MissionApprovalLevel.DENIED


def _audit_summary(
    evaluator: str,
    state: MissionState,
    command: Optional[MissionCommand],
    decision: MissionSafetyBaselineDecision,
    risk_level: MissionDryRunRiskLevel,
    findings: List[MissionSafetyFinding],
) -> str:
    command_part = f" command {command.command_id}" if command is not None else ""
    return (
        f"{_safe_text(evaluator or 'jarvis')} safety baseline evaluated mission {state.mission_id}"
        f"{command_part}: decision={decision.value}, risk={risk_level.value}, findings={len(findings)}; "
        "prepare-only, no approval or execution occurred."
    )


def _safe_text(value: Optional[str]) -> str:
    text = str(value or "")
    for phrase in _BLANKET_APPROVAL_PHRASES:
        text = text.replace(phrase, "[redacted-policy-phrase]")
    return text


def _is_simple_metadata(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_simple_metadata(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_simple_metadata(item) for key, item in value.items())
    return False


def _coerce_enum(enum_type, value: Any, field_name: str):
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid {enum_type.__name__}") from exc


def _list_from(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _is_non_empty_string(value: Optional[str]) -> bool:
    return bool((value or "").strip())


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_SECRET_LIKE_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
    "private_key",
    "authorization",
    "cookie",
    ".env",
}

_SECRET_LIKE_FRAGMENTS = {
    "password",
    "api_key",
    "private_key",
    "access_token",
    "refresh_token",
    "auth_token",
}

_SECRET_VALUE_PREFIXES = {
    "sk-",
    "pk_live_",
    "ghp_",
    "github_pat_",
    "xoxb-",
}

_BLANKET_APPROVAL_PHRASES = {
    "approve_all_forever",
    "do_anything",
    "unlimited",
    "no_limits",
    "whatever_it_takes",
    "haz_todo_lo_necesario_sin_limites",
    "haz todo lo necesario sin limites",
    "approve all forever",
    "do anything",
    "no limits",
    "whatever it takes",
}

_DEPLOY_TERMS = {
    "deploy",
    "deployment",
    "production",
    "prod",
    "domain",
    "dominio",
    "produccion",
    "producción",
}

_SPEND_TERMS = {
    "spend",
    "budget",
    "payment",
    "pay",
    "checkout",
    "purchase",
    "buy",
    "cost",
    "gasto",
    "pago",
    "comprar",
}

_EXTERNAL_CONTACT_TERMS = {
    "email",
    "send dm",
    "outreach",
    "external contact",
    "contact lead",
    "cold email",
    "slack",
    "telegram",
    "whatsapp",
    "contacto externo",
    "enviar email",
}

_COMMERCIAL_PUBLICATION_TERMS = {
    "publish",
    "publication",
    "commercial",
    "sales page",
    "launch",
    "ad campaign",
    "post as david",
    "publicar",
    "comercial",
    "campaña",
    "campana",
}

_PUBLIC_AI_CONTENT_TERMS = {
    "ai generated",
    "generated by ai",
    "llm generated",
    "synthetic media",
    "public content",
    "public post",
    "youtube",
    "tiktok",
    "linkedin",
    "contenido ia",
    "contenido público",
    "contenido publico",
}

_DECEPTIVE_IMPERSONATION_TERMS = {
    "deepfake",
    "impersonate",
    "deceptive impersonation",
    "clone voice",
    "voice clone",
    "fake endorsement",
    "suplantar",
    "suplantacion",
    "suplantación",
}

_STRONG_APPROVAL_TERMS = (
    _DEPLOY_TERMS
    | _SPEND_TERMS
    | _COMMERCIAL_PUBLICATION_TERMS
    | _DECEPTIVE_IMPERSONATION_TERMS
    | {"credential", "credentials", "secret", "contract", "legal", "identity", "identidad", "contrato"}
)
