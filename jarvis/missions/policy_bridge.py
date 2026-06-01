from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.approval_bridge import MissionApprovalBridgeDecision, MissionApprovalBridgePayload
from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.command_builder import MissionCommand
from jarvis.missions.dry_run import MissionDryRunDecision, MissionDryRunEvaluation, MissionDryRunRiskLevel
from jarvis.missions.safety_baseline import MissionSafetyBaselineDecision, MissionSafetyBaselineResult
from jarvis.missions.state_store import MissionState, MissionStatus


class MissionPolicyBridgeDecision(str, Enum):
    ALLOWED_PREPARE_ONLY = "allowed_prepare_only"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_STRONG_APPROVAL = "requires_strong_approval"
    DENIED = "denied"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MissionPolicyBridgeResult:
    result_id: str
    mission_id: str
    decision: MissionPolicyBridgeDecision
    can_prepare: bool
    can_execute_later: bool
    requires_approval: bool
    approval_level: MissionApprovalLevel
    risk_level: MissionDryRunRiskLevel
    reasons: List[str]
    audit_summary: str
    created_at: str
    command_id: Optional[str] = None
    evaluation_id: Optional[str] = None
    payload_id: Optional[str] = None
    safety_result_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision", _coerce_enum(MissionPolicyBridgeDecision, self.decision, "decision"))
        object.__setattr__(self, "approval_level", _coerce_enum(MissionApprovalLevel, self.approval_level, "approval_level"))
        object.__setattr__(self, "risk_level", _coerce_enum(MissionDryRunRiskLevel, self.risk_level, "risk_level"))
        object.__setattr__(self, "reasons", _list_from(self.reasons))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

        if self.can_execute_later:
            raise ValueError("policy bridge cannot permit execution later in v1")
        if self.decision == MissionPolicyBridgeDecision.ALLOWED_PREPARE_ONLY and self.requires_approval:
            raise ValueError("allowed_prepare_only cannot require approval")
        if self.decision in {
            MissionPolicyBridgeDecision.REQUIRES_REVIEW,
            MissionPolicyBridgeDecision.REQUIRES_APPROVAL,
            MissionPolicyBridgeDecision.REQUIRES_STRONG_APPROVAL,
        } and not self.requires_approval:
            raise ValueError("review or approval decisions require requires_approval true")
        if not self.reasons:
            raise ValueError("policy bridge result requires at least one reason")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionPolicyBridgeResult":
        return cls(
            result_id=str(data.get("result_id", "")),
            mission_id=str(data.get("mission_id", "")),
            command_id=data.get("command_id"),
            evaluation_id=data.get("evaluation_id"),
            payload_id=data.get("payload_id"),
            safety_result_id=data.get("safety_result_id"),
            decision=data.get("decision", ""),
            can_prepare=bool(data.get("can_prepare", False)),
            can_execute_later=bool(data.get("can_execute_later", False)),
            requires_approval=bool(data.get("requires_approval", False)),
            approval_level=data.get("approval_level", ""),
            risk_level=data.get("risk_level", ""),
            reasons=_list_from(data.get("reasons")),
            audit_summary=str(data.get("audit_summary", "")),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "mission_id": self.mission_id,
            "command_id": self.command_id,
            "evaluation_id": self.evaluation_id,
            "payload_id": self.payload_id,
            "safety_result_id": self.safety_result_id,
            "decision": self.decision.value,
            "can_prepare": self.can_prepare,
            "can_execute_later": self.can_execute_later,
            "requires_approval": self.requires_approval,
            "approval_level": self.approval_level.value,
            "risk_level": self.risk_level.value,
            "reasons": list(self.reasons),
            "audit_summary": self.audit_summary,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


def evaluate_mission_policy_bridge(
    state: MissionState,
    command: Optional[MissionCommand] = None,
    evaluation: Optional[MissionDryRunEvaluation] = None,
    payload: Optional[MissionApprovalBridgePayload] = None,
    safety_result: Optional[MissionSafetyBaselineResult] = None,
    *,
    evaluator: str = "jarvis",
) -> MissionPolicyBridgeResult:
    if not isinstance(state, MissionState):
        raise ValueError("state must be a MissionState")
    if command is not None and not isinstance(command, MissionCommand):
        raise ValueError("command must be a MissionCommand")
    if evaluation is not None and not isinstance(evaluation, MissionDryRunEvaluation):
        raise ValueError("evaluation must be a MissionDryRunEvaluation")
    if payload is not None and not isinstance(payload, MissionApprovalBridgePayload):
        raise ValueError("payload must be a MissionApprovalBridgePayload")
    if safety_result is not None and not isinstance(safety_result, MissionSafetyBaselineResult):
        raise ValueError("safety_result must be a MissionSafetyBaselineResult")

    if command is not None and command.mission_id != state.mission_id:
        raise ValueError("command mission_id must match mission state")
    if evaluation is not None and evaluation.mission_id != state.mission_id:
        raise ValueError("evaluation mission_id must match mission state")
    if payload is not None and payload.mission_id != state.mission_id:
        raise ValueError("payload mission_id must match mission state")
    if safety_result is not None and safety_result.mission_id != state.mission_id:
        raise ValueError("safety_result mission_id must match mission state")

    decisions: List[MissionPolicyBridgeDecision] = []
    reasons: List[str] = []
    risk_levels: List[MissionDryRunRiskLevel] = []

    if state.status in _TERMINAL_OR_BLOCKED_STATUSES:
        decisions.append(MissionPolicyBridgeDecision.BLOCKED)
        reasons.append(f"Mission status {state.status.value} blocks policy bridge preparation.")

    if command is not None:
        command_decision = _decision_from_command(command)
        if _is_candidate_tool_only(state, command.tool_name) and command_decision == MissionPolicyBridgeDecision.ALLOWED_PREPARE_ONLY:
            command_decision = MissionPolicyBridgeDecision.REQUIRES_REVIEW
            reasons.append("Candidate tool is review-only and cannot become allowed.")
        decisions.append(command_decision)
        reasons.append(f"Command decision is {command_decision.value}.")

    if evaluation is not None:
        evaluation_decision = _decision_from_evaluation(evaluation)
        decisions.append(evaluation_decision)
        risk_levels.append(evaluation.risk_level)
        reasons.append(f"Dry-run decision is {evaluation_decision.value}.")

    if payload is not None:
        payload_decision = _decision_from_payload(payload)
        decisions.append(payload_decision)
        risk_levels.append(payload.risk_level)
        reasons.append(f"Approval bridge decision is {payload_decision.value}.")

    if safety_result is not None:
        safety_decision = _decision_from_safety(safety_result)
        decisions.append(safety_decision)
        risk_levels.append(safety_result.risk_level)
        reasons.append(f"Safety baseline decision is {safety_decision.value}.")

    if not decisions:
        decisions.append(MissionPolicyBridgeDecision.ALLOWED_PREPARE_ONLY)
        reasons.append("No command, dry-run, approval payload, or safety result required escalation.")

    decision = _max_decision(decisions)
    approval_level = _approval_level_for(decision)
    requires_approval = decision in {
        MissionPolicyBridgeDecision.REQUIRES_REVIEW,
        MissionPolicyBridgeDecision.REQUIRES_APPROVAL,
        MissionPolicyBridgeDecision.REQUIRES_STRONG_APPROVAL,
    }
    risk_level = _max_risk(risk_levels or [_risk_for_decision(decision)])

    return MissionPolicyBridgeResult(
        result_id=str(uuid4()),
        mission_id=state.mission_id,
        command_id=command.command_id if command is not None else None,
        evaluation_id=evaluation.evaluation_id if evaluation is not None else None,
        payload_id=payload.payload_id if payload is not None else None,
        safety_result_id=safety_result.result_id if safety_result is not None else None,
        decision=decision,
        can_prepare=decision == MissionPolicyBridgeDecision.ALLOWED_PREPARE_ONLY,
        can_execute_later=False,
        requires_approval=requires_approval,
        approval_level=approval_level,
        risk_level=risk_level,
        reasons=reasons,
        audit_summary=(
            f"Policy bridge evaluated mission {state.mission_id}: decision={decision.value}; "
            "prepare-only, no ApprovalGateway call, runtime connection, execution, or state mutation occurred."
        ),
        created_at=_now_iso(),
        metadata={
            "evaluator": evaluator or "jarvis",
            "prepare_only": True,
            "approval_gateway_called": False,
            "hermes_connected": False,
            "mission_control_connected": False,
            "can_execute_later_v1": False,
        },
    )


def _decision_from_command(command: MissionCommand) -> MissionPolicyBridgeDecision:
    return MissionPolicyBridgeDecision(command.status.value if command.status.value != "prepared" else "allowed_prepare_only")


def _decision_from_evaluation(evaluation: MissionDryRunEvaluation) -> MissionPolicyBridgeDecision:
    return MissionPolicyBridgeDecision(evaluation.decision.value)


def _decision_from_payload(payload: MissionApprovalBridgePayload) -> MissionPolicyBridgeDecision:
    if payload.decision == MissionApprovalBridgeDecision.NO_APPROVAL_NEEDED:
        return MissionPolicyBridgeDecision.ALLOWED_PREPARE_ONLY
    return MissionPolicyBridgeDecision(payload.decision.value)


def _decision_from_safety(result: MissionSafetyBaselineResult) -> MissionPolicyBridgeDecision:
    if result.decision == MissionSafetyBaselineDecision.PASS_PREPARE_ONLY:
        return MissionPolicyBridgeDecision.ALLOWED_PREPARE_ONLY
    return MissionPolicyBridgeDecision(result.decision.value)


def _max_decision(decisions: List[MissionPolicyBridgeDecision]) -> MissionPolicyBridgeDecision:
    order = {
        MissionPolicyBridgeDecision.ALLOWED_PREPARE_ONLY: 0,
        MissionPolicyBridgeDecision.REQUIRES_REVIEW: 1,
        MissionPolicyBridgeDecision.REQUIRES_APPROVAL: 2,
        MissionPolicyBridgeDecision.REQUIRES_STRONG_APPROVAL: 3,
        MissionPolicyBridgeDecision.DENIED: 4,
        MissionPolicyBridgeDecision.BLOCKED: 5,
    }
    return max(decisions, key=lambda decision: order[decision])


def _approval_level_for(decision: MissionPolicyBridgeDecision) -> MissionApprovalLevel:
    if decision == MissionPolicyBridgeDecision.ALLOWED_PREPARE_ONLY:
        return MissionApprovalLevel.ALLOWED
    if decision == MissionPolicyBridgeDecision.REQUIRES_REVIEW:
        return MissionApprovalLevel.REQUIRES_REVIEW
    if decision == MissionPolicyBridgeDecision.REQUIRES_APPROVAL:
        return MissionApprovalLevel.REQUIRES_APPROVAL
    if decision == MissionPolicyBridgeDecision.REQUIRES_STRONG_APPROVAL:
        return MissionApprovalLevel.STRONG_APPROVAL
    return MissionApprovalLevel.DENIED


def _risk_for_decision(decision: MissionPolicyBridgeDecision) -> MissionDryRunRiskLevel:
    if decision in {MissionPolicyBridgeDecision.BLOCKED, MissionPolicyBridgeDecision.DENIED}:
        return MissionDryRunRiskLevel.HIGH
    if decision == MissionPolicyBridgeDecision.REQUIRES_STRONG_APPROVAL:
        return MissionDryRunRiskLevel.HIGH
    if decision in {MissionPolicyBridgeDecision.REQUIRES_REVIEW, MissionPolicyBridgeDecision.REQUIRES_APPROVAL}:
        return MissionDryRunRiskLevel.MEDIUM
    return MissionDryRunRiskLevel.LOW


def _max_risk(risk_levels: List[MissionDryRunRiskLevel]) -> MissionDryRunRiskLevel:
    order = {
        MissionDryRunRiskLevel.LOW: 0,
        MissionDryRunRiskLevel.MEDIUM: 1,
        MissionDryRunRiskLevel.HIGH: 2,
        MissionDryRunRiskLevel.CRITICAL: 3,
        MissionDryRunRiskLevel.UNKNOWN: 1,
    }
    return max(risk_levels, key=lambda risk: order[risk])


def _is_candidate_tool_only(state: MissionState, tool_name: Optional[str]) -> bool:
    normalized = _normalize(tool_name)
    if not normalized:
        return False
    allowed_tools = {_normalize(tool) for tool in state.envelope.allowed_tools}
    candidate_tools = {_normalize(tool) for tool in state.envelope.candidate_tools}
    return normalized in candidate_tools and normalized not in allowed_tools


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


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_TERMINAL_OR_BLOCKED_STATUSES = {
    MissionStatus.BLOCKED,
    MissionStatus.STOPPED,
    MissionStatus.COMPLETED,
    MissionStatus.FAILED,
    MissionStatus.ARCHIVED,
}
