from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.approval_bridge import MissionApprovalBridgeDecision, MissionApprovalBridgePayload
from jarvis.missions.approval_request import MissionApprovalLevel
from jarvis.missions.budget_guard import MissionBudgetGuardDecision, MissionBudgetGuardResult
from jarvis.missions.command_builder import MissionCommand, MissionCommandStatus
from jarvis.missions.dry_run import MissionDryRunDecision, MissionDryRunEvaluation
from jarvis.missions.policy_bridge import MissionPolicyBridgeDecision, MissionPolicyBridgeResult
from jarvis.missions.safety_baseline import MissionSafetyBaselineDecision, MissionSafetyBaselineResult
from jarvis.missions.state_store import MissionState, MissionStatus


class HermesPayloadStatus(str, Enum):
    PREPARED = "prepared"
    DRY_RUN_ONLY = "dry_run_only"
    BLOCKED = "blocked"


class HermesDryRunStatus(str, Enum):
    PREPARED = "prepared"
    DRY_RUN_ONLY = "dry_run_only"
    BLOCKED = "blocked"


class HermesExecutionStatus(str, Enum):
    NOT_EXECUTED = "not_executed"
    PREPARED = "prepared"
    DRY_RUN_ONLY = "dry_run_only"
    BLOCKED = "blocked"
    FAILED = "failed"
    COMPLETED = "completed"


class HermesAgentRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class HermesCommandPayloadValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class HermesCommandPayload:
    payload_id: str
    mission_id: str
    command_id: str
    action: str
    requested_by: str
    allowed_tools: List[str]
    candidate_tools: List[str]
    inputs: Dict[str, Any]
    metadata: Dict[str, Any]
    approval_level: MissionApprovalLevel
    policy_decision: str
    safety_decision: str
    budget_decision: str
    created_at: str
    dry_run_only: bool = True
    can_execute_now: bool = False
    status: HermesPayloadStatus = HermesPayloadStatus.PREPARED
    approval_decision: Optional[str] = None
    dry_run_decision: Optional[str] = None
    blocked_reason: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.approval_level = _coerce_enum(MissionApprovalLevel, self.approval_level, "approval_level")
        self.status = _coerce_enum(HermesPayloadStatus, self.status, "status")
        self.allowed_tools = _list_from(self.allowed_tools)
        self.candidate_tools = _list_from(self.candidate_tools)
        self.inputs = dict(self.inputs or {})
        self.metadata = dict(self.metadata or {})
        self.notes = _list_from(self.notes)

        result = validate_hermes_command_payload(self)
        if not result.is_valid:
            raise ValueError("; ".join(result.errors))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HermesCommandPayload":
        return cls(
            payload_id=str(data.get("payload_id", "")),
            mission_id=str(data.get("mission_id", "")),
            command_id=str(data.get("command_id", "")),
            action=str(data.get("action", "")),
            requested_by=str(data.get("requested_by", "")),
            allowed_tools=_list_from(data.get("allowed_tools")),
            candidate_tools=_list_from(data.get("candidate_tools")),
            inputs=dict(data.get("inputs") or {}),
            metadata=dict(data.get("metadata") or {}),
            approval_level=data.get("approval_level", ""),
            policy_decision=str(data.get("policy_decision", "")),
            safety_decision=str(data.get("safety_decision", "")),
            budget_decision=str(data.get("budget_decision", "")),
            created_at=str(data.get("created_at", "")),
            dry_run_only=bool(data.get("dry_run_only", True)),
            can_execute_now=bool(data.get("can_execute_now", False)),
            status=data.get("status", HermesPayloadStatus.PREPARED),
            approval_decision=data.get("approval_decision"),
            dry_run_decision=data.get("dry_run_decision"),
            blocked_reason=data.get("blocked_reason"),
            notes=_list_from(data.get("notes")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payload_id": self.payload_id,
            "mission_id": self.mission_id,
            "command_id": self.command_id,
            "action": self.action,
            "requested_by": self.requested_by,
            "allowed_tools": list(self.allowed_tools),
            "candidate_tools": list(self.candidate_tools),
            "inputs": dict(self.inputs),
            "metadata": dict(self.metadata),
            "approval_level": self.approval_level.value,
            "policy_decision": self.policy_decision,
            "safety_decision": self.safety_decision,
            "budget_decision": self.budget_decision,
            "created_at": self.created_at,
            "dry_run_only": self.dry_run_only,
            "can_execute_now": self.can_execute_now,
            "status": self.status.value,
            "approval_decision": self.approval_decision,
            "dry_run_decision": self.dry_run_decision,
            "blocked_reason": self.blocked_reason,
            "notes": list(self.notes),
        }


def build_hermes_command_payload(
    state: MissionState,
    command: MissionCommand,
    evaluation: Optional[MissionDryRunEvaluation] = None,
    approval_payload: Optional[MissionApprovalBridgePayload] = None,
    safety_result: Optional[MissionSafetyBaselineResult] = None,
    policy_result: Optional[MissionPolicyBridgeResult] = None,
    budget_result: Optional[MissionBudgetGuardResult] = None,
    *,
    requested_by: str = "jarvis",
    metadata: Optional[Dict[str, Any]] = None,
) -> HermesCommandPayload:
    if not isinstance(state, MissionState):
        raise ValueError("state must be a MissionState")
    if not isinstance(command, MissionCommand):
        raise ValueError("command must be a MissionCommand")
    if command.mission_id != state.mission_id:
        raise ValueError("command mission_id must match mission state")

    _validate_optional_contracts(state, command, evaluation, approval_payload, safety_result, policy_result, budget_result)

    notes: List[str] = [
        "Hermes Runtime Bridge v1 is prepare-only; no Hermes call, ApprovalGateway call, runtime connection, or execution was attempted."
    ]
    blocked_reasons: List[str] = []

    if state.status in _TERMINAL_OR_BLOCKED_STATUSES:
        blocked_reasons.append(f"Mission status {state.status.value} blocks Hermes payload preparation.")
    if command.status in {MissionCommandStatus.BLOCKED, MissionCommandStatus.DENIED}:
        blocked_reasons.append(command.reason or f"Command status is {command.status.value}.")
    if evaluation is not None and evaluation.decision in {MissionDryRunDecision.BLOCKED, MissionDryRunDecision.DENIED}:
        blocked_reasons.append(evaluation.blocked_reason or f"Dry-run decision is {evaluation.decision.value}.")
    if approval_payload is not None and approval_payload.decision in {
        MissionApprovalBridgeDecision.BLOCKED,
        MissionApprovalBridgeDecision.DENIED,
    }:
        blocked_reasons.append(approval_payload.blocked_reason or f"Approval bridge decision is {approval_payload.decision.value}.")
    if safety_result is not None and safety_result.decision in {
        MissionSafetyBaselineDecision.BLOCKED,
        MissionSafetyBaselineDecision.DENIED,
    }:
        blocked_reasons.append(safety_result.audit_summary or f"Safety decision is {safety_result.decision.value}.")
    if policy_result is not None and policy_result.decision in {
        MissionPolicyBridgeDecision.BLOCKED,
        MissionPolicyBridgeDecision.DENIED,
    }:
        blocked_reasons.append(policy_result.audit_summary or f"Policy decision is {policy_result.decision.value}.")
    if budget_result is not None and budget_result.decision == MissionBudgetGuardDecision.BLOCKED:
        blocked_reasons.append(budget_result.audit_summary or "Budget guard decision is blocked.")

    requires_approval = _requires_approval(command, evaluation, approval_payload, safety_result, policy_result, budget_result)
    if requires_approval:
        notes.append("Approval or strong approval is still required; v1 never marks payloads executable.")

    allowed_tools = list(state.envelope.allowed_tools)
    candidate_tools = list(state.envelope.candidate_tools)
    if _is_candidate_tool_only(state, command.tool_name):
        notes.append("Candidate tool is preserved as candidate-only and was not promoted to allowed_tools.")

    status = HermesPayloadStatus.BLOCKED if blocked_reasons else HermesPayloadStatus.PREPARED
    combined_metadata = {
        "bridge_version": "hermes_runtime_bridge_v1",
        "prepare_only": True,
        "approval_gateway_called": False,
        "hermes_connected": False,
        "mission_control_connected": False,
        "runtime_executor_created": False,
    }
    combined_metadata.update(dict(metadata or {}))

    return HermesCommandPayload(
        payload_id=str(uuid4()),
        mission_id=state.mission_id,
        command_id=command.command_id,
        action=command.action,
        requested_by=requested_by,
        allowed_tools=allowed_tools,
        candidate_tools=candidate_tools,
        inputs=dict(command.inputs),
        metadata=combined_metadata,
        approval_level=_max_approval_level(command, evaluation, approval_payload, safety_result, policy_result),
        policy_decision=_decision_value(policy_result.decision if policy_result is not None else "not_evaluated"),
        safety_decision=_decision_value(safety_result.decision if safety_result is not None else "not_evaluated"),
        budget_decision=_decision_value(budget_result.decision if budget_result is not None else "not_evaluated"),
        created_at=_now_iso(),
        dry_run_only=True,
        can_execute_now=False,
        status=status,
        approval_decision=_decision_value(approval_payload.decision) if approval_payload is not None else None,
        dry_run_decision=_decision_value(evaluation.decision) if evaluation is not None else None,
        blocked_reason="; ".join(blocked_reasons) if blocked_reasons else None,
        notes=notes,
    )


def validate_hermes_command_payload(payload: HermesCommandPayload) -> HermesCommandPayloadValidationResult:
    errors: List[str] = []

    if not _is_non_empty_string(getattr(payload, "payload_id", "")):
        errors.append("payload_id must be a non-empty string")
    if not _is_non_empty_string(getattr(payload, "mission_id", "")):
        errors.append("mission_id must be a non-empty string")
    if not _is_non_empty_string(getattr(payload, "command_id", "")):
        errors.append("command_id must be a non-empty string")
    if not _is_non_empty_string(getattr(payload, "action", "")):
        errors.append("action must be a non-empty string")
    if not _is_non_empty_string(getattr(payload, "requested_by", "")):
        errors.append("requested_by must be a non-empty string")

    if not isinstance(getattr(payload, "inputs", None), dict):
        errors.append("inputs must be a dict")
    if not isinstance(getattr(payload, "metadata", None), dict):
        errors.append("metadata must be a dict")
    if not isinstance(getattr(payload, "allowed_tools", None), list):
        errors.append("allowed_tools must be a list")
    if not isinstance(getattr(payload, "candidate_tools", None), list):
        errors.append("candidate_tools must be a list")

    if getattr(payload, "dry_run_only", None) is not True:
        errors.append("dry_run_only must be true in Hermes Runtime Bridge v1")
    if getattr(payload, "can_execute_now", None) is not False:
        errors.append("can_execute_now must be false in Hermes Runtime Bridge v1")
    if getattr(payload, "status", None) == HermesPayloadStatus.BLOCKED and not _is_non_empty_string(
        getattr(payload, "blocked_reason", None)
    ):
        errors.append("blocked Hermes payload requires blocked_reason")

    overlap = _normalized_intersection(getattr(payload, "allowed_tools", []), getattr(payload, "candidate_tools", []))
    if overlap:
        errors.append("candidate_tools cannot also appear in allowed_tools: " + ", ".join(sorted(overlap)))

    secret_paths = _secret_like_paths({"inputs": getattr(payload, "inputs", {}), "metadata": getattr(payload, "metadata", {})})
    if secret_paths:
        errors.append("inputs and metadata cannot include secret-like keys or values: " + ", ".join(secret_paths))

    blanket_paths = _blanket_approval_paths(
        {
            "action": getattr(payload, "action", ""),
            "inputs": getattr(payload, "inputs", {}),
            "metadata": getattr(payload, "metadata", {}),
            "notes": getattr(payload, "notes", []),
            "blocked_reason": getattr(payload, "blocked_reason", "") or "",
        }
    )
    if blanket_paths:
        errors.append("Hermes payload cannot contain vague blanket approval: " + ", ".join(blanket_paths))

    return HermesCommandPayloadValidationResult(errors=errors)


@dataclass
class HermesDryRunBridgeResult:
    dry_run_id: str
    mission_id: str
    command_id: str
    payload_id: str
    status: HermesDryRunStatus
    expected_steps: List[str]
    expected_tools: List[str]
    risk_notes: List[str]
    can_execute_later: bool = False
    created_at: str = field(default_factory=lambda: _now_iso())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.status = _coerce_enum(HermesDryRunStatus, self.status, "status")
        self.expected_steps = _list_from(self.expected_steps)
        self.expected_tools = _list_from(self.expected_tools)
        self.risk_notes = _list_from(self.risk_notes)
        self.metadata = dict(self.metadata or {})
        if self.can_execute_later:
            raise ValueError("Hermes dry-run bridge cannot permit execution later in v1")
        if _secret_like_paths({"metadata": self.metadata}):
            raise ValueError("metadata cannot include secret-like keys or values")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HermesDryRunBridgeResult":
        return cls(
            dry_run_id=str(data.get("dry_run_id", "")),
            mission_id=str(data.get("mission_id", "")),
            command_id=str(data.get("command_id", "")),
            payload_id=str(data.get("payload_id", "")),
            status=data.get("status", ""),
            expected_steps=_list_from(data.get("expected_steps")),
            expected_tools=_list_from(data.get("expected_tools")),
            risk_notes=_list_from(data.get("risk_notes")),
            can_execute_later=bool(data.get("can_execute_later", False)),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dry_run_id": self.dry_run_id,
            "mission_id": self.mission_id,
            "command_id": self.command_id,
            "payload_id": self.payload_id,
            "status": self.status.value,
            "expected_steps": list(self.expected_steps),
            "expected_tools": list(self.expected_tools),
            "risk_notes": list(self.risk_notes),
            "can_execute_later": self.can_execute_later,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class HermesDryRunBridge:
    def prepare(self, payload: HermesCommandPayload, *, requested_by: str = "jarvis") -> HermesDryRunBridgeResult:
        if not isinstance(payload, HermesCommandPayload):
            raise ValueError("payload must be a HermesCommandPayload")

        status = HermesDryRunStatus.BLOCKED if payload.status == HermesPayloadStatus.BLOCKED else HermesDryRunStatus.DRY_RUN_ONLY
        risk_notes = list(payload.notes)
        if payload.blocked_reason:
            risk_notes.append(payload.blocked_reason)
        risk_notes.append("Dry-run bridge asks what Hermes would do; no tool or runtime execution occurred.")

        return HermesDryRunBridgeResult(
            dry_run_id=str(uuid4()),
            mission_id=payload.mission_id,
            command_id=payload.command_id,
            payload_id=payload.payload_id,
            status=status,
            expected_steps=[f"Review prepared action: {payload.action}", "Return expected tool plan without execution."],
            expected_tools=list(payload.allowed_tools),
            risk_notes=risk_notes,
            can_execute_later=False,
            created_at=_now_iso(),
            metadata={
                "requested_by": requested_by or "jarvis",
                "prepare_only": True,
                "hermes_connected": False,
                "tools_executed": False,
            },
        )


@dataclass
class HermesExecutionResult:
    result_id: str
    mission_id: str
    command_id: str
    payload_id: str
    status: HermesExecutionStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_summary: str = ""
    error: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.status = _coerce_enum(HermesExecutionStatus, self.status, "status")
        self.artifacts = _list_from(self.artifacts)
        self.logs = _list_from(self.logs)
        self.metadata = dict(self.metadata or {})
        if self.status == HermesExecutionStatus.COMPLETED and not self.completed_at:
            raise ValueError("completed execution result requires completed_at")
        if self.status == HermesExecutionStatus.FAILED and not _is_non_empty_string(self.error):
            raise ValueError("failed execution result requires error")
        if _secret_like_paths({"metadata": self.metadata, "logs": self.logs, "artifacts": self.artifacts}):
            raise ValueError("execution result cannot include secret-like keys or values")

    @classmethod
    def not_executed(cls, payload: HermesCommandPayload, *, reason: str = "Hermes execution is disabled in v1.") -> "HermesExecutionResult":
        if not isinstance(payload, HermesCommandPayload):
            raise ValueError("payload must be a HermesCommandPayload")
        return cls(
            result_id=str(uuid4()),
            mission_id=payload.mission_id,
            command_id=payload.command_id,
            payload_id=payload.payload_id,
            status=HermesExecutionStatus.NOT_EXECUTED,
            output_summary=reason,
            metadata={
                "prepare_only": True,
                "hermes_connected": False,
                "tools_executed": False,
                "runtime_executor_created": False,
            },
        )

    @classmethod
    def dry_run_only(cls, payload: HermesCommandPayload, *, summary: str = "Dry-run only; no execution occurred.") -> "HermesExecutionResult":
        if not isinstance(payload, HermesCommandPayload):
            raise ValueError("payload must be a HermesCommandPayload")
        return cls(
            result_id=str(uuid4()),
            mission_id=payload.mission_id,
            command_id=payload.command_id,
            payload_id=payload.payload_id,
            status=HermesExecutionStatus.DRY_RUN_ONLY,
            output_summary=summary,
            metadata={"prepare_only": True, "tools_executed": False},
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HermesExecutionResult":
        return cls(
            result_id=str(data.get("result_id", "")),
            mission_id=str(data.get("mission_id", "")),
            command_id=str(data.get("command_id", "")),
            payload_id=str(data.get("payload_id", "")),
            status=data.get("status", ""),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            output_summary=str(data.get("output_summary", "")),
            error=data.get("error"),
            artifacts=_list_from(data.get("artifacts")),
            logs=_list_from(data.get("logs")),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "mission_id": self.mission_id,
            "command_id": self.command_id,
            "payload_id": self.payload_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "output_summary": self.output_summary,
            "error": self.error,
            "artifacts": list(self.artifacts),
            "logs": list(self.logs),
            "metadata": dict(self.metadata),
        }


@dataclass
class HermesAuditIntegrationContract:
    event_type: str
    audit_summary: str
    audit_metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        self.audit_metadata = dict(self.audit_metadata or {})
        if not _is_non_empty_string(self.event_type):
            raise ValueError("event_type must be a non-empty string")
        if not _is_non_empty_string(self.audit_summary):
            raise ValueError("audit_summary must be a non-empty string")
        if _secret_like_paths({"audit_metadata": self.audit_metadata, "audit_summary": self.audit_summary}):
            raise ValueError("audit integration contract cannot include secret-like keys or values")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HermesAuditIntegrationContract":
        return cls(
            event_type=str(data.get("event_type", "")),
            audit_summary=str(data.get("audit_summary", "")),
            audit_metadata=dict(data.get("audit_metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "audit_summary": self.audit_summary,
            "audit_metadata": dict(self.audit_metadata),
        }


def prepare_hermes_audit_contract(
    payload: HermesCommandPayload,
    dry_run: Optional[HermesDryRunBridgeResult] = None,
    result: Optional[HermesExecutionResult] = None,
) -> HermesAuditIntegrationContract:
    if not isinstance(payload, HermesCommandPayload):
        raise ValueError("payload must be a HermesCommandPayload")
    if dry_run is not None and dry_run.payload_id != payload.payload_id:
        raise ValueError("dry_run payload_id must match payload")
    if result is not None and result.payload_id != payload.payload_id:
        raise ValueError("result payload_id must match payload")

    event_type = "hermes.runtime_bridge.prepared"
    if payload.status == HermesPayloadStatus.BLOCKED:
        event_type = "hermes.runtime_bridge.blocked"
    elif dry_run is not None:
        event_type = "hermes.runtime_bridge.dry_run_prepared"
    if result is not None:
        event_type = f"hermes.runtime_bridge.execution_result.{result.status.value}"

    return HermesAuditIntegrationContract(
        event_type=event_type,
        audit_summary=(
            f"Hermes bridge prepared payload {payload.payload_id} for mission {payload.mission_id}: "
            f"status={payload.status.value}; dry_run_only={payload.dry_run_only}; can_execute_now={payload.can_execute_now}."
        ),
        audit_metadata={
            "mission_id": payload.mission_id,
            "command_id": payload.command_id,
            "payload_id": payload.payload_id,
            "dry_run_id": dry_run.dry_run_id if dry_run is not None else None,
            "result_id": result.result_id if result is not None else None,
            "payload_status": payload.status.value,
            "execution_status": result.status.value if result is not None else None,
            "prepare_only": True,
            "audit_log_written": False,
            "approval_gateway_called": False,
            "hermes_connected": False,
            "tools_executed": False,
        },
    )


@dataclass
class HermesAgentDescriptor:
    agent_id: str
    name: str
    role: str
    capabilities: List[str]
    allowed_tools: List[str]
    risk_level: HermesAgentRiskLevel
    requires_approval: bool
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.risk_level = _coerce_enum(HermesAgentRiskLevel, self.risk_level, "risk_level")
        self.capabilities = _list_from(self.capabilities)
        self.allowed_tools = _list_from(self.allowed_tools)
        self.metadata = dict(self.metadata or {})
        if not _is_non_empty_string(self.agent_id):
            raise ValueError("agent_id must be a non-empty string")
        if not isinstance(self.capabilities, list):
            raise ValueError("capabilities must be a list")
        if not isinstance(self.allowed_tools, list):
            raise ValueError("allowed_tools must be a list")
        if _has_sensitive_tool(self.allowed_tools) and not self.requires_approval:
            raise ValueError("agent with sensitive tools requires approval")
        if _secret_like_paths({"metadata": self.metadata}):
            raise ValueError("agent metadata cannot include secret-like keys or values")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HermesAgentDescriptor":
        return cls(
            agent_id=str(data.get("agent_id", "")),
            name=str(data.get("name", "")),
            role=str(data.get("role", "")),
            capabilities=_list_from(data.get("capabilities")),
            allowed_tools=_list_from(data.get("allowed_tools")),
            risk_level=data.get("risk_level", ""),
            requires_approval=bool(data.get("requires_approval", False)),
            enabled=bool(data.get("enabled", True)),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "capabilities": list(self.capabilities),
            "allowed_tools": list(self.allowed_tools),
            "risk_level": self.risk_level.value,
            "requires_approval": self.requires_approval,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }


class HermesAgentRegistryBridge:
    def __init__(self, agents: Optional[List[HermesAgentDescriptor]] = None) -> None:
        self._agents: Dict[str, HermesAgentDescriptor] = {}
        for agent in agents or []:
            self.register(agent)

    def register(self, agent: HermesAgentDescriptor) -> HermesAgentDescriptor:
        if not isinstance(agent, HermesAgentDescriptor):
            raise ValueError("agent must be a HermesAgentDescriptor")
        if agent.agent_id in self._agents:
            raise ValueError(f"agent already registered: {agent.agent_id}")
        self._agents[agent.agent_id] = HermesAgentDescriptor.from_dict(agent.to_dict())
        return HermesAgentDescriptor.from_dict(agent.to_dict())

    def get(self, agent_id: str) -> HermesAgentDescriptor:
        try:
            return HermesAgentDescriptor.from_dict(self._agents[agent_id].to_dict())
        except KeyError as exc:
            raise KeyError(f"Hermes agent not found: {agent_id}") from exc

    def list_agents(self, *, enabled_only: bool = False) -> List[HermesAgentDescriptor]:
        agents = [HermesAgentDescriptor.from_dict(agent.to_dict()) for agent in self._agents.values()]
        if enabled_only:
            return [agent for agent in agents if agent.enabled]
        return agents

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agents": [agent.to_dict() for agent in self.list_agents()],
            "metadata": {
                "prepare_only": True,
                "tools_executed": False,
                "registry_executes_tools": False,
            },
        }

    def execute_tool(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("HermesAgentRegistryBridge is prepare-only and does not execute tools")


def _validate_optional_contracts(
    state: MissionState,
    command: MissionCommand,
    evaluation: Optional[MissionDryRunEvaluation],
    approval_payload: Optional[MissionApprovalBridgePayload],
    safety_result: Optional[MissionSafetyBaselineResult],
    policy_result: Optional[MissionPolicyBridgeResult],
    budget_result: Optional[MissionBudgetGuardResult],
) -> None:
    if evaluation is not None:
        if not isinstance(evaluation, MissionDryRunEvaluation):
            raise ValueError("evaluation must be a MissionDryRunEvaluation")
        if evaluation.mission_id != state.mission_id:
            raise ValueError("evaluation mission_id must match mission state")
        if evaluation.command_id != command.command_id:
            raise ValueError("evaluation command_id must match command")
    if approval_payload is not None:
        if not isinstance(approval_payload, MissionApprovalBridgePayload):
            raise ValueError("approval_payload must be a MissionApprovalBridgePayload")
        if approval_payload.mission_id != state.mission_id:
            raise ValueError("approval_payload mission_id must match mission state")
        if approval_payload.command_id != command.command_id:
            raise ValueError("approval_payload command_id must match command")
    if safety_result is not None:
        if not isinstance(safety_result, MissionSafetyBaselineResult):
            raise ValueError("safety_result must be a MissionSafetyBaselineResult")
        if safety_result.mission_id != state.mission_id:
            raise ValueError("safety_result mission_id must match mission state")
        if safety_result.command_id is not None and safety_result.command_id != command.command_id:
            raise ValueError("safety_result command_id must match command")
    if policy_result is not None:
        if not isinstance(policy_result, MissionPolicyBridgeResult):
            raise ValueError("policy_result must be a MissionPolicyBridgeResult")
        if policy_result.mission_id != state.mission_id:
            raise ValueError("policy_result mission_id must match mission state")
        if policy_result.command_id is not None and policy_result.command_id != command.command_id:
            raise ValueError("policy_result command_id must match command")
    if budget_result is not None:
        if not isinstance(budget_result, MissionBudgetGuardResult):
            raise ValueError("budget_result must be a MissionBudgetGuardResult")
        if budget_result.mission_id is not None and budget_result.mission_id != state.mission_id:
            raise ValueError("budget_result mission_id must match mission state")


def _requires_approval(
    command: MissionCommand,
    evaluation: Optional[MissionDryRunEvaluation],
    approval_payload: Optional[MissionApprovalBridgePayload],
    safety_result: Optional[MissionSafetyBaselineResult],
    policy_result: Optional[MissionPolicyBridgeResult],
    budget_result: Optional[MissionBudgetGuardResult],
) -> bool:
    if command.requires_approval or command.approval_level in _APPROVAL_REQUIRED_LEVELS:
        return True
    if evaluation is not None and (evaluation.requires_approval or evaluation.approval_level in _APPROVAL_REQUIRED_LEVELS):
        return True
    if approval_payload is not None and approval_payload.approval_level in _APPROVAL_REQUIRED_LEVELS:
        return True
    if safety_result is not None and (safety_result.requires_approval or safety_result.approval_level in _APPROVAL_REQUIRED_LEVELS):
        return True
    if policy_result is not None and (policy_result.requires_approval or policy_result.approval_level in _APPROVAL_REQUIRED_LEVELS):
        return True
    if budget_result is not None and budget_result.decision in {
        MissionBudgetGuardDecision.REQUIRES_APPROVAL,
        MissionBudgetGuardDecision.REQUIRES_STRONG_APPROVAL,
    }:
        return True
    return False


def _max_approval_level(
    command: MissionCommand,
    evaluation: Optional[MissionDryRunEvaluation],
    approval_payload: Optional[MissionApprovalBridgePayload],
    safety_result: Optional[MissionSafetyBaselineResult],
    policy_result: Optional[MissionPolicyBridgeResult],
) -> MissionApprovalLevel:
    levels = [command.approval_level]
    if evaluation is not None and evaluation.approval_level is not None:
        levels.append(evaluation.approval_level)
    if approval_payload is not None:
        levels.append(approval_payload.approval_level)
    if safety_result is not None:
        levels.append(safety_result.approval_level)
    if policy_result is not None:
        levels.append(policy_result.approval_level)

    order = {
        MissionApprovalLevel.ALLOWED: 0,
        MissionApprovalLevel.REQUIRES_REVIEW: 1,
        MissionApprovalLevel.REQUIRES_APPROVAL: 2,
        MissionApprovalLevel.STRONG_APPROVAL: 3,
        MissionApprovalLevel.DENIED: 4,
    }
    return max(levels, key=lambda level: order[level])


def _is_candidate_tool_only(state: MissionState, tool_name: Optional[str]) -> bool:
    normalized = _normalize(tool_name)
    if not normalized:
        return False
    allowed_tools = {_normalize(tool) for tool in state.envelope.allowed_tools}
    candidate_tools = {_normalize(tool) for tool in state.envelope.candidate_tools}
    return normalized in candidate_tools and normalized not in allowed_tools


def _has_sensitive_tool(tools: List[str]) -> bool:
    for tool in tools:
        normalized = _normalize(tool).replace("-", "_")
        if any(term in normalized for term in _SENSITIVE_TOOL_TERMS):
            return True
    return False


def _secret_like_paths(value: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if _normalize(str(key)) in _SECRET_LIKE_KEYS:
                paths.append(key_path)
            paths.extend(_secret_like_paths(item, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_secret_like_paths(item, f"{prefix}[{index}]"))
    elif isinstance(value, str):
        normalized = _normalize(value)
        if normalized in _SECRET_LIKE_KEYS:
            paths.append(prefix or "value")
    return paths


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


def _normalized_intersection(left: List[str], right: List[str]) -> set[str]:
    return {_normalize(item) for item in left if _normalize(item)} & {
        _normalize(item) for item in right if _normalize(item)
    }


def _decision_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


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


_TERMINAL_OR_BLOCKED_STATUSES = {
    MissionStatus.BLOCKED,
    MissionStatus.STOPPED,
    MissionStatus.COMPLETED,
    MissionStatus.FAILED,
    MissionStatus.ARCHIVED,
}

_APPROVAL_REQUIRED_LEVELS = {
    MissionApprovalLevel.REQUIRES_REVIEW,
    MissionApprovalLevel.REQUIRES_APPROVAL,
    MissionApprovalLevel.STRONG_APPROVAL,
}

_BLANKET_APPROVAL_PHRASES = {
    "approve_all_forever",
    "do_anything",
    "unlimited",
    "no_limits",
    "whatever_it_takes",
    "haz_todo_lo_necesario_sin_limites",
}

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

_SENSITIVE_TOOL_TERMS = {
    "terminal",
    "shell",
    "exec",
    "browser",
    "email",
    "gmail",
    "stripe",
    "payment",
    "bank",
    "deploy",
    "production",
    "secret",
    "credential",
    "file_write",
    "delete",
    "rm",
}
