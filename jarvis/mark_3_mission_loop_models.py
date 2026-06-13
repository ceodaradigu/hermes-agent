from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from jarvis.approval_audit import redact_sensitive_data


UNKNOWN = "unknown"


class MissionLoopStatus(str, Enum):
    RECEIVED = "received"
    CLASSIFIED = "classified"
    PLANNING = "planning"
    PLANNED = "planned"
    PREVIEW_READY = "preview_ready"
    AWAITING_APPROVAL = "awaiting_approval"
    BLOCKED = "blocked"
    EXECUTION_CANDIDATE_READY = "execution_candidate_ready"
    RUNNING_INTERNAL = "running_internal"
    STOPPED = "stopped"
    RESULT_PENDING = "result_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    DENIED = "denied"
    POST_MORTEM_READY = "post_mortem_ready"
    LEARNING_PROPOSAL_READY = "learning_proposal_ready"


class VerificationState(str, Enum):
    REPORTED = "reported"
    OBSERVED = "observed"
    VERIFIED = "verified"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass
class MissionIntake:
    mission_id: str
    objective: str
    context: str
    desired_outcome: str
    success_criteria: List[str]
    declared_authorization: str
    allowed_scope: List[str]
    allowed_paths_resources: List[str]
    allowed_tools: List[str]
    prohibited_tools: List[str]
    monetary_budget: Optional[float]
    time_budget_seconds: Optional[int]
    max_steps: int
    allowed_data: List[str]
    constraints: List[str]
    stop_conditions: List[str]
    expected_rollback: str
    instruction_origin: str
    direct_intent_evidence: Optional[str]
    created_at: str
    updated_at: str
    correlation_id: str
    requested_risk_level: Optional[int] = None
    proposed_steps: List[Dict[str, Any]] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        safe, _ = redact_sensitive_data(asdict(self))
        return safe


@dataclass
class MissionClassification:
    legal: bool
    safe: bool
    authorized: bool
    technically_supported: bool
    capability_available: bool
    risk_level: int
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    triple_confirmation_required: bool
    audit_required: bool
    rollback_required: bool
    stop_plan_required: bool
    blocked_reasons: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    evidence_requirements: List[str] = field(default_factory=list)
    research_prototype_fallback: Optional[str] = None
    readback_required: bool = False
    permanent_denial: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MissionStep:
    step_id: str
    order: int
    description: str
    objective: str
    action_type: str
    inputs: Dict[str, Any]
    expected_outputs: List[str]
    required_capability: str
    tool_candidate: Optional[str]
    scope: List[str]
    budget: Optional[float]
    timeout_seconds: Optional[int]
    risk_level: int
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    triple_confirmation_required: bool
    preconditions: List[str]
    dependencies: List[str]
    evidence_requirements: List[str]
    stop_condition: str
    rollback_compensation: str
    status: str = "planned"
    blocked_reasons: List[str] = field(default_factory=list)
    capability_available: bool = False
    approval_satisfied: bool = False
    approval_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        safe, _ = redact_sensitive_data(asdict(self))
        return safe


@dataclass
class ExecutionCandidate:
    candidate_id: str
    mission_id: str
    step_id: str
    exact_action: str
    adapter_capability: str
    tool_candidate: Optional[str]
    scope: List[str]
    budget: Optional[float]
    timeout_seconds: Optional[int]
    risk_level: int
    approval_requirement: Dict[str, Any]
    context_fingerprint: str
    audit_correlation_id: str
    stop_plan: str
    rollback_plan: str
    evidence_requirements: List[str]
    capability_available: bool
    eligibility: bool
    blocked_reasons: List[str] = field(default_factory=list)
    approval_required: bool = False
    approval_satisfied: bool = False
    execution_capability_available: bool = False
    would_execute: bool = False
    did_execute: bool = False
    external_side_effects: bool = False

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["would_execute"] = False
        data["did_execute"] = False
        data["external_side_effects"] = False
        return data


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_type: str
    description: str
    correlation_id: str
    timestamp: str
    verification_state: VerificationState
    redaction_status: str
    safe_hash_reference: str
    limitations: List[str]
    supported_claim: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["verification_state"] = self.verification_state.value
        return data


@dataclass
class MissionOutcome:
    outcome_id: str
    mission_id: str
    step_id: Optional[str]
    summary: str
    verification_state: VerificationState
    evidence_ids: List[str]
    step_status: str = "completed"
    status_reason: str = ""
    costs_known: Any = UNKNOWN
    revenue_known: Any = UNKNOWN
    time_known_seconds: Any = UNKNOWN
    recorded_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["verification_state"] = self.verification_state.value
        return data


@dataclass(frozen=True)
class MissionAuditEvent:
    event_id: str
    mission_id: str
    event_type: str
    timestamp: str
    correlation_id: str
    summary: str
    metadata: Dict[str, Any]
    redacted_fields: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MissionWorkingMemory:
    intake: MissionIntake
    classification: Optional[MissionClassification] = None
    status: MissionLoopStatus = MissionLoopStatus.RECEIVED
    plan: List[MissionStep] = field(default_factory=list)
    candidates: List[ExecutionCandidate] = field(default_factory=list)
    approval_requirements: List[Dict[str, Any]] = field(default_factory=list)
    outcomes: List[MissionOutcome] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)
    feedback: List[Dict[str, Any]] = field(default_factory=list)
    post_mortem: Optional[Dict[str, Any]] = None
    learning_proposal_preview: Optional[Dict[str, Any]] = None
    audit: List[MissionAuditEvent] = field(default_factory=list)
    next_action: str = "classify mission"
    stop_reason: Optional[str] = None
    kill_switch_active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intake": self.intake.to_dict(),
            "classification": self.classification.to_dict() if self.classification else None,
            "status": self.status.value,
            "plan": [item.to_dict() for item in self.plan],
            "steps": [item.to_dict() for item in self.plan],
            "candidates": [item.to_dict() for item in self.candidates],
            "approval_requirements": list(self.approval_requirements),
            "outcomes": [item.to_dict() for item in self.outcomes],
            "evidence": [item.to_dict() for item in self.evidence],
            "feedback": list(self.feedback),
            "post_mortem": self.post_mortem,
            "learning_proposal_preview": self.learning_proposal_preview,
            "audit": [item.to_dict() for item in self.audit],
            "next_action": self.next_action,
            "stop_reason": self.stop_reason,
            "kill_switch_active": self.kill_switch_active,
            "in_memory_only": True,
            "persisted": False,
        }
