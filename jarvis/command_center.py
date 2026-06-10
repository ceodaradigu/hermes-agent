from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

from jarvis.ambient_vision.companion import (
    AmbientVisionPrivacyPolicy,
    AmbientVisionStatus,
    AmbientVisionStopControl,
)
from jarvis.missions.approval_bridge import MissionApprovalBridgePayload
from jarvis.missions.approval_request import MissionApprovalLevel, MissionApprovalRequest
from jarvis.missions.audit_log import MissionAuditEvent
from jarvis.missions.budget_guard import MissionBudgetGuardResult
from jarvis.missions.dry_run import MissionDryRunRiskLevel
from jarvis.missions.hermes_bridge import HermesAgentDescriptor, HermesCommandPayload
from jarvis.missions.state_store import MissionState, MissionStatus
from jarvis.multidevice.runtime import MultiDeviceRuntimeStatus
from jarvis.operational_consolidation import build_command_center_system_map
from jarvis.voice.companion import (
    VoiceCompanionControlPolicy,
    VoiceCompanionIntentPreview,
    VoiceCompanionStatus,
)


class CommandCenterViewStatus(str, Enum):
    READY = "ready"
    NEEDS_ATTENTION = "needs_attention"
    BLOCKED = "blocked"


class CommandCenterControlStatus(str, Enum):
    PLACEHOLDER = "placeholder"
    DISABLED = "disabled"


_REDACTED_AUDIT_SUMMARY = "[redacted sensitive audit summary]"
_REDACTED_ACTION = "[redacted sensitive action]"
_REDACTED_BLOCKED_REASON = "[redacted sensitive blocked reason]"
_REDACTED_MISSION_LAST_ERROR = "[redacted sensitive mission error]"
_SAFE_POLICY_BOUNDARY = (
    "PolicyEngine and ApprovalGateway remain authoritative; Phase D Command Center views are prepare-only "
    "and cannot approve, reject, execute, or call Hermes."
)
_REDACTED_APPROVAL_ACTION = "[redacted sensitive approval action]"
_REDACTED_APPROVAL_REASON = "[redacted sensitive approval reason]"
_REDACTED_APPROVAL_SCOPE = "[redacted sensitive approval scope]"
_RESERVED_METADATA_KEYS = {
    "prepare_only",
    "approval_gateway_called",
    "hermes_connected",
    "execution_enabled",
    "approval_enabled",
    "approve_reject_enabled",
    "runtime_connected",
}
_SAFETY_METADATA = {
    "prepare_only": True,
    "approval_gateway_called": False,
    "hermes_connected": False,
    "execution_enabled": False,
    "approval_enabled": False,
    "approve_reject_enabled": False,
    "runtime_connected": False,
}


@dataclass(frozen=True)
class SafetyIndicatorView:
    status: CommandCenterViewStatus
    approval_gateway_required: bool
    strong_approval_required: bool
    policy_engine_boundary: str
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _coerce_enum(CommandCenterViewStatus, self.status, "status"))
        object.__setattr__(self, "notes", _list_from(self.notes))
        if not _is_non_empty_string(self.policy_engine_boundary):
            raise ValueError("policy_engine_boundary must be a non-empty string")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SafetyIndicatorView":
        status = data.get("status", CommandCenterViewStatus.NEEDS_ATTENTION)
        if status == CommandCenterViewStatus.READY.value or status == CommandCenterViewStatus.READY:
            status = CommandCenterViewStatus.NEEDS_ATTENTION
        return cls(
            status=status,
            approval_gateway_required=True,
            strong_approval_required=bool(data.get("strong_approval_required", False)),
            policy_engine_boundary=_SAFE_POLICY_BOUNDARY,
            notes=_list_from(data.get("notes")) + ["deserialized safety indicator is conservative"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "approval_gateway_required": self.approval_gateway_required,
            "strong_approval_required": self.strong_approval_required,
            "policy_engine_boundary": self.policy_engine_boundary,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class MissionDashboardView:
    mission_id: str
    objective: str
    status: MissionStatus
    success_metric: str
    pending_approvals: int = 0
    audit_event_count: int = 0
    risk_level: MissionDryRunRiskLevel = MissionDryRunRiskLevel.UNKNOWN
    last_error: Optional[str] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _coerce_enum(MissionStatus, self.status, "status"))
        object.__setattr__(self, "risk_level", _coerce_enum(MissionDryRunRiskLevel, self.risk_level, "risk_level"))
        if not _is_non_empty_string(self.mission_id):
            raise ValueError("mission_id must be a non-empty string")
        if not _is_non_empty_string(self.objective):
            raise ValueError("objective must be a non-empty string")
        if not _is_non_empty_string(self.success_metric):
            raise ValueError("success_metric must be a non-empty string")
        object.__setattr__(self, "last_error", _safe_ui_text(self.last_error, _REDACTED_MISSION_LAST_ERROR))
        if self.pending_approvals < 0:
            raise ValueError("pending_approvals cannot be negative")
        if self.audit_event_count < 0:
            raise ValueError("audit_event_count cannot be negative")

    @classmethod
    def from_mission_state(cls, state: MissionState) -> "MissionDashboardView":
        if not isinstance(state, MissionState):
            raise ValueError("state must be a MissionState")
        pending = sum(1 for request in state.approval_requests if _approval_is_pending(request.approval_level))
        return cls(
            mission_id=state.mission_id,
            objective=state.envelope.objective,
            status=state.status,
            success_metric=state.envelope.success_metric,
            pending_approvals=pending,
            audit_event_count=len(state.audit_events),
            risk_level=_risk_from_status(state.status),
            last_error=state.last_error,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionDashboardView":
        return cls(
            mission_id=str(data.get("mission_id", "")),
            objective=str(data.get("objective", "")),
            status=data.get("status", ""),
            success_metric=str(data.get("success_metric", "")),
            pending_approvals=int(data.get("pending_approvals", 0)),
            audit_event_count=int(data.get("audit_event_count", 0)),
            risk_level=data.get("risk_level", MissionDryRunRiskLevel.UNKNOWN),
            last_error=data.get("last_error"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "status": self.status.value,
            "success_metric": self.success_metric,
            "pending_approvals": self.pending_approvals,
            "audit_event_count": self.audit_event_count,
            "risk_level": self.risk_level.value,
            "last_error": self.last_error,
        }


@dataclass(frozen=True)
class ApprovalQueueView:
    item_id: str
    mission_id: str
    action: str
    approval_level: MissionApprovalLevel
    risk_level: MissionDryRunRiskLevel
    reason: str
    scope: List[str]
    challenge_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "approval_level", _coerce_enum(MissionApprovalLevel, self.approval_level, "approval_level"))
        object.__setattr__(self, "risk_level", _coerce_enum(MissionDryRunRiskLevel, self.risk_level, "risk_level"))
        object.__setattr__(self, "action", _safe_ui_text(self.action, _REDACTED_APPROVAL_ACTION))
        object.__setattr__(self, "reason", _safe_ui_text(self.reason, _REDACTED_APPROVAL_REASON))
        object.__setattr__(
            self,
            "scope",
            [
                _safe_ui_text(scope_item, _REDACTED_APPROVAL_SCOPE)
                for scope_item in _list_from(self.scope)
            ],
        )
        if not _is_non_empty_string(self.item_id):
            raise ValueError("item_id must be a non-empty string")
        if not _is_non_empty_string(self.mission_id):
            raise ValueError("mission_id must be a non-empty string")
        if not _is_non_empty_string(self.action):
            raise ValueError("action must be a non-empty string")
        if not _is_non_empty_string(self.reason):
            raise ValueError("reason must be a non-empty string")

    @classmethod
    def from_approval_request(cls, request: MissionApprovalRequest) -> "ApprovalQueueView":
        if not isinstance(request, MissionApprovalRequest):
            raise ValueError("request must be a MissionApprovalRequest")
        return cls(
            item_id=request.request_id,
            mission_id=request.mission_id,
            action=request.action,
            approval_level=request.approval_level,
            risk_level=_risk_from_approval_level(request.approval_level),
            reason=request.reason,
            scope=list(request.scope),
            challenge_required=request.approval_level == MissionApprovalLevel.STRONG_APPROVAL,
        )

    @classmethod
    def from_bridge_payload(cls, payload: MissionApprovalBridgePayload) -> "ApprovalQueueView":
        if not isinstance(payload, MissionApprovalBridgePayload):
            raise ValueError("payload must be a MissionApprovalBridgePayload")
        return cls(
            item_id=payload.payload_id,
            mission_id=payload.mission_id,
            action=payload.action,
            approval_level=payload.approval_level,
            risk_level=payload.risk_level,
            reason=payload.reason,
            scope=list(payload.scope),
            challenge_required=payload.challenge_required,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApprovalQueueView":
        approval_level = _coerce_enum(MissionApprovalLevel, data.get("approval_level", ""), "approval_level")
        return cls(
            item_id=str(data.get("item_id", "")),
            mission_id=str(data.get("mission_id", "")),
            action=str(data.get("action", "")),
            approval_level=approval_level,
            risk_level=data.get("risk_level", ""),
            reason=str(data.get("reason", "")),
            scope=_list_from(data.get("scope")),
            challenge_required=approval_level == MissionApprovalLevel.STRONG_APPROVAL
            or bool(data.get("challenge_required", False)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "mission_id": self.mission_id,
            "action": self.action,
            "approval_level": self.approval_level.value,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "scope": list(self.scope),
            "challenge_required": self.challenge_required,
        }


@dataclass(frozen=True)
class AuditTimelineView:
    event_id: str
    mission_id: str
    event_type: str
    summary: str
    created_at: str
    outcome: str
    risk_level: str
    sensitive: bool = False
    redacted_fields: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "redacted_fields", _list_from(self.redacted_fields))
        if self.sensitive or self.redacted_fields:
            object.__setattr__(self, "summary", _REDACTED_AUDIT_SUMMARY)
            redacted_fields = set(self.redacted_fields)
            redacted_fields.add("summary")
            object.__setattr__(self, "redacted_fields", sorted(redacted_fields))
        for field_name in ("event_id", "mission_id", "event_type", "summary", "created_at", "outcome", "risk_level"):
            if not _is_non_empty_string(getattr(self, field_name)):
                raise ValueError(f"{field_name} must be a non-empty string")

    @classmethod
    def from_audit_event(cls, event: MissionAuditEvent) -> "AuditTimelineView":
        if not isinstance(event, MissionAuditEvent):
            raise ValueError("event must be a MissionAuditEvent")
        return cls(
            event_id=event.event_id,
            mission_id=event.mission_id,
            event_type=event.event_type.value,
            summary=_safe_audit_summary(event.summary, sensitive=event.sensitive, redacted_fields=event.redacted_fields),
            created_at=event.created_at,
            outcome=event.outcome.value,
            risk_level=event.risk_level.value,
            sensitive=event.sensitive,
            redacted_fields=list(event.redacted_fields),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditTimelineView":
        return cls(
            event_id=str(data.get("event_id", "")),
            mission_id=str(data.get("mission_id", "")),
            event_type=str(data.get("event_type", "")),
            summary=_safe_audit_summary(
                str(data.get("summary", "")),
                sensitive=bool(data.get("sensitive", False)),
                redacted_fields=_list_from(data.get("redacted_fields")),
            ),
            created_at=str(data.get("created_at", "")),
            outcome=str(data.get("outcome", "")),
            risk_level=str(data.get("risk_level", "")),
            sensitive=bool(data.get("sensitive", False)),
            redacted_fields=_list_from(data.get("redacted_fields")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "mission_id": self.mission_id,
            "event_type": self.event_type,
            "summary": self.summary,
            "created_at": self.created_at,
            "outcome": self.outcome,
            "risk_level": self.risk_level,
            "sensitive": self.sensitive,
            "redacted_fields": list(self.redacted_fields),
        }


@dataclass(frozen=True)
class AgentStatusView:
    agent_id: str
    name: str
    role: str
    enabled: bool
    risk_level: str
    requires_approval: bool
    capability_count: int
    allowed_tool_count: int

    @classmethod
    def from_agent_descriptor(cls, descriptor: HermesAgentDescriptor) -> "AgentStatusView":
        if not isinstance(descriptor, HermesAgentDescriptor):
            raise ValueError("descriptor must be a HermesAgentDescriptor")
        return cls(
            agent_id=descriptor.agent_id,
            name=descriptor.name,
            role=descriptor.role,
            enabled=descriptor.enabled,
            risk_level=descriptor.risk_level.value,
            requires_approval=descriptor.requires_approval,
            capability_count=len(descriptor.capabilities),
            allowed_tool_count=len(descriptor.allowed_tools),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentStatusView":
        return cls(
            agent_id=str(data.get("agent_id", "")),
            name=str(data.get("name", "")),
            role=str(data.get("role", "")),
            enabled=bool(data.get("enabled", False)),
            risk_level=str(data.get("risk_level", "")),
            requires_approval=bool(data.get("requires_approval", False)),
            capability_count=int(data.get("capability_count", 0)),
            allowed_tool_count=int(data.get("allowed_tool_count", 0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "enabled": self.enabled,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "capability_count": self.capability_count,
            "allowed_tool_count": self.allowed_tool_count,
        }


@dataclass(frozen=True)
class RiskAndBudgetPanelView:
    mission_id: str
    risk_level: MissionDryRunRiskLevel
    budget_limit: Optional[float]
    cost_limit_per_action: Optional[float]
    budget_decision: str = "not_evaluated"
    can_spend: bool = False
    violations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "risk_level", _coerce_enum(MissionDryRunRiskLevel, self.risk_level, "risk_level"))
        object.__setattr__(self, "violations", _list_from(self.violations))
        if not _is_non_empty_string(self.mission_id):
            raise ValueError("mission_id must be a non-empty string")
        if self.can_spend:
            raise ValueError("Command Center view cannot enable spending")

    @classmethod
    def from_mission_state(
        cls,
        state: MissionState,
        budget_result: Optional[MissionBudgetGuardResult] = None,
    ) -> "RiskAndBudgetPanelView":
        if not isinstance(state, MissionState):
            raise ValueError("state must be a MissionState")
        if budget_result is not None and not isinstance(budget_result, MissionBudgetGuardResult):
            raise ValueError("budget_result must be a MissionBudgetGuardResult")
        return cls(
            mission_id=state.mission_id,
            risk_level=_risk_from_status(state.status),
            budget_limit=state.envelope.budget_limit,
            cost_limit_per_action=state.envelope.cost_limit_per_action,
            budget_decision=budget_result.decision.value if budget_result is not None else "not_evaluated",
            can_spend=False,
            violations=list(budget_result.violations) if budget_result is not None else [],
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskAndBudgetPanelView":
        return cls(
            mission_id=str(data.get("mission_id", "")),
            risk_level=data.get("risk_level", ""),
            budget_limit=data.get("budget_limit"),
            cost_limit_per_action=data.get("cost_limit_per_action"),
            budget_decision=str(data.get("budget_decision", "not_evaluated")),
            can_spend=bool(data.get("can_spend", False)),
            violations=_list_from(data.get("violations")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "risk_level": self.risk_level.value,
            "budget_limit": self.budget_limit,
            "cost_limit_per_action": self.cost_limit_per_action,
            "budget_decision": self.budget_decision,
            "can_spend": self.can_spend,
            "violations": list(self.violations),
        }


@dataclass(frozen=True)
class HermesPayloadView:
    payload_id: str
    mission_id: str
    command_id: str
    action: str
    status: str
    dry_run_only: bool
    can_execute_now: bool
    approval_level: MissionApprovalLevel
    allowed_tool_count: int
    candidate_tool_count: int
    blocked_reason: Optional[str] = None
    redacted_fields: List[str] = field(default_factory=lambda: ["inputs", "metadata"])

    def __post_init__(self) -> None:
        object.__setattr__(self, "approval_level", _coerce_enum(MissionApprovalLevel, self.approval_level, "approval_level"))
        object.__setattr__(self, "redacted_fields", _list_from(self.redacted_fields))
        redacted_fields = set(self.redacted_fields)
        safe_action = _safe_ui_text(self.action, _REDACTED_ACTION)
        if safe_action != self.action:
            redacted_fields.add("action")
        object.__setattr__(self, "action", safe_action)
        if self.blocked_reason is not None:
            safe_blocked_reason = _safe_ui_text(self.blocked_reason, _REDACTED_BLOCKED_REASON)
            if safe_blocked_reason != self.blocked_reason:
                redacted_fields.add("blocked_reason")
            object.__setattr__(self, "blocked_reason", safe_blocked_reason)
        object.__setattr__(self, "redacted_fields", sorted(redacted_fields))
        for field_name in ("payload_id", "mission_id", "command_id", "action", "status"):
            if not _is_non_empty_string(getattr(self, field_name)):
                raise ValueError(f"{field_name} must be a non-empty string")
        if not self.dry_run_only:
            raise ValueError("HermesPayloadView must remain dry_run_only")
        if self.can_execute_now:
            raise ValueError("HermesPayloadView cannot mark payload executable")

    @classmethod
    def from_hermes_payload(cls, payload: HermesCommandPayload) -> "HermesPayloadView":
        if not isinstance(payload, HermesCommandPayload):
            raise ValueError("payload must be a HermesCommandPayload")
        return cls(
            payload_id=payload.payload_id,
            mission_id=payload.mission_id,
            command_id=payload.command_id,
            action=payload.action,
            status=payload.status.value,
            dry_run_only=payload.dry_run_only,
            can_execute_now=payload.can_execute_now,
            approval_level=payload.approval_level,
            allowed_tool_count=len(payload.allowed_tools),
            candidate_tool_count=len(payload.candidate_tools),
            blocked_reason=payload.blocked_reason,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HermesPayloadView":
        return cls(
            payload_id=str(data.get("payload_id", "")),
            mission_id=str(data.get("mission_id", "")),
            command_id=str(data.get("command_id", "")),
            action=str(data.get("action", "")),
            status=str(data.get("status", "")),
            dry_run_only=bool(data.get("dry_run_only", True)),
            can_execute_now=bool(data.get("can_execute_now", False)),
            approval_level=data.get("approval_level", ""),
            allowed_tool_count=int(data.get("allowed_tool_count", 0)),
            candidate_tool_count=int(data.get("candidate_tool_count", 0)),
            blocked_reason=data.get("blocked_reason"),
            redacted_fields=_list_from(data.get("redacted_fields") or ["inputs", "metadata"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "payload_id": self.payload_id,
            "mission_id": self.mission_id,
            "command_id": self.command_id,
            "action": self.action,
            "status": self.status,
            "dry_run_only": self.dry_run_only,
            "can_execute_now": self.can_execute_now,
            "approval_level": self.approval_level.value,
            "allowed_tool_count": self.allowed_tool_count,
            "candidate_tool_count": self.candidate_tool_count,
            "blocked_reason": self.blocked_reason,
            "redacted_fields": list(self.redacted_fields),
        }


@dataclass(frozen=True)
class DeviceStatusView:
    device_id: str
    label: str
    trusted: bool = False
    online: bool = False
    approval_capable: bool = False
    status: CommandCenterControlStatus = CommandCenterControlStatus.PLACEHOLDER

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _coerce_enum(CommandCenterControlStatus, self.status, "status"))
        if self.approval_capable:
            raise ValueError("DeviceStatusView placeholder cannot enable approvals")

    @classmethod
    def placeholder(cls) -> "DeviceStatusView":
        return cls(device_id="device-placeholder", label="Device runtime not connected")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceStatusView":
        return cls(
            device_id=str(data.get("device_id", "")),
            label=str(data.get("label", "")),
            trusted=bool(data.get("trusted", False)),
            online=bool(data.get("online", False)),
            approval_capable=bool(data.get("approval_capable", False)),
            status=data.get("status", CommandCenterControlStatus.PLACEHOLDER),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "label": self.label,
            "trusted": self.trusted,
            "online": self.online,
            "approval_capable": self.approval_capable,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class VoiceCameraControlsView:
    voice_status: CommandCenterControlStatus = CommandCenterControlStatus.PLACEHOLDER
    camera_status: CommandCenterControlStatus = CommandCenterControlStatus.PLACEHOLDER
    can_start_voice: bool = False
    can_start_camera: bool = False
    can_record: bool = False
    voice_companion_status: VoiceCompanionStatus = field(default_factory=VoiceCompanionStatus.placeholder)
    voice_companion_control_policy: VoiceCompanionControlPolicy = field(default_factory=VoiceCompanionControlPolicy.placeholder)
    voice_companion_preview: VoiceCompanionIntentPreview = field(default_factory=VoiceCompanionIntentPreview.placeholder)
    can_preview_transcript: bool = True
    ambient_vision_status: AmbientVisionStatus = field(default_factory=AmbientVisionStatus.placeholder)
    ambient_vision_privacy_policy: AmbientVisionPrivacyPolicy = field(default_factory=AmbientVisionPrivacyPolicy.placeholder)
    ambient_vision_stop_control: AmbientVisionStopControl = field(default_factory=AmbientVisionStopControl.placeholder)
    notes: List[str] = field(default_factory=lambda: ["placeholder only; no microphone or camera runtime is connected"])

    def __post_init__(self) -> None:
        object.__setattr__(self, "voice_status", _coerce_enum(CommandCenterControlStatus, self.voice_status, "voice_status"))
        object.__setattr__(self, "camera_status", _coerce_enum(CommandCenterControlStatus, self.camera_status, "camera_status"))
        if isinstance(self.voice_companion_status, dict):
            object.__setattr__(
                self,
                "voice_companion_status",
                VoiceCompanionStatus.from_dict(self.voice_companion_status),
            )
        if isinstance(self.voice_companion_control_policy, dict):
            object.__setattr__(
                self,
                "voice_companion_control_policy",
                VoiceCompanionControlPolicy.from_dict(self.voice_companion_control_policy),
            )
        if isinstance(self.voice_companion_preview, dict):
            object.__setattr__(
                self,
                "voice_companion_preview",
                VoiceCompanionIntentPreview.from_dict(self.voice_companion_preview),
            )
        if isinstance(self.ambient_vision_status, dict):
            object.__setattr__(self, "ambient_vision_status", AmbientVisionStatus.from_dict(self.ambient_vision_status))
        if isinstance(self.ambient_vision_privacy_policy, dict):
            object.__setattr__(
                self,
                "ambient_vision_privacy_policy",
                AmbientVisionPrivacyPolicy.from_dict(self.ambient_vision_privacy_policy),
            )
        if isinstance(self.ambient_vision_stop_control, dict):
            object.__setattr__(
                self,
                "ambient_vision_stop_control",
                AmbientVisionStopControl.from_dict(self.ambient_vision_stop_control),
            )
        if not isinstance(self.voice_companion_status, VoiceCompanionStatus):
            raise ValueError("voice_companion_status must be a VoiceCompanionStatus")
        if not isinstance(self.voice_companion_control_policy, VoiceCompanionControlPolicy):
            raise ValueError("voice_companion_control_policy must be a VoiceCompanionControlPolicy")
        if not isinstance(self.voice_companion_preview, VoiceCompanionIntentPreview):
            raise ValueError("voice_companion_preview must be a VoiceCompanionIntentPreview")
        object.__setattr__(self, "notes", _list_from(self.notes))
        companion = self.voice_companion_status
        control_policy = self.voice_companion_control_policy
        preview = self.voice_companion_preview
        if (
            self.can_start_voice
            or self.can_start_camera
            or self.can_record
            or companion.voice_available
            or companion.microphone_enabled
            or companion.wake_word_enabled
            or companion.recording_enabled
            or companion.streaming_enabled
            or companion.auto_start_enabled
            or companion.execution_enabled
            or not companion.prepare_only
            or not companion.approval_required_for_sensitive_actions
            or control_policy.microphone_requested
            or control_policy.wake_word_requested
            or control_policy.recording_requested
            or control_policy.streaming_requested
            or control_policy.auto_start_requested
            or control_policy.execution_requested
            or control_policy.activation_enabled
            or not control_policy.prepare_only
            or not control_policy.requires_approval_for_activation
            or not preview.prepare_only
            or preview.would_execute
            or preview.execution_enabled
            or preview.approval_created
            or preview.approval_gateway_called
            or preview.hermes_called
        ):
            raise ValueError("Voice/camera controls are placeholders and cannot start capture")

    @classmethod
    def placeholder(cls) -> "VoiceCameraControlsView":
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceCameraControlsView":
        return cls(
            voice_status=data.get("voice_status", CommandCenterControlStatus.PLACEHOLDER),
            camera_status=data.get("camera_status", CommandCenterControlStatus.PLACEHOLDER),
            can_start_voice=False,
            can_start_camera=False,
            can_record=False,
            voice_companion_status=VoiceCompanionStatus.from_dict(data.get("voice_companion_status")),
            voice_companion_control_policy=VoiceCompanionControlPolicy.from_dict(
                data.get("voice_companion_control_policy")
            ),
            voice_companion_preview=VoiceCompanionIntentPreview.from_dict(data.get("voice_companion_preview")),
            can_preview_transcript=bool(data.get("can_preview_transcript", True)),
            ambient_vision_status=AmbientVisionStatus.from_dict(data.get("ambient_vision_status")),
            ambient_vision_privacy_policy=AmbientVisionPrivacyPolicy.from_dict(data.get("ambient_vision_privacy_policy")),
            ambient_vision_stop_control=AmbientVisionStopControl.from_dict(data.get("ambient_vision_stop_control")),
            notes=_list_from(data.get("notes")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voice_status": self.voice_status.value,
            "camera_status": self.camera_status.value,
            "can_start_voice": self.can_start_voice,
            "can_start_camera": self.can_start_camera,
            "can_record": self.can_record,
            "voice_companion_status": self.voice_companion_status.to_dict(),
            "voice_companion_control_policy": self.voice_companion_control_policy.to_dict(),
            "voice_companion_preview": self.voice_companion_preview.to_dict(),
            "can_preview_transcript": self.can_preview_transcript,
            "ambient_vision_status": self.ambient_vision_status.to_dict(),
            "ambient_vision_privacy_policy": self.ambient_vision_privacy_policy.to_dict(),
            "ambient_vision_stop_control": self.ambient_vision_stop_control.to_dict(),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class CostRoiSummaryView:
    projected_cost: Optional[float] = None
    confirmed_cost: Optional[float] = None
    projected_revenue: Optional[float] = None
    confirmed_revenue: Optional[float] = None
    roi_status: CommandCenterControlStatus = CommandCenterControlStatus.PLACEHOLDER
    notes: List[str] = field(default_factory=lambda: ["ROI engine not connected"])

    def __post_init__(self) -> None:
        object.__setattr__(self, "roi_status", _coerce_enum(CommandCenterControlStatus, self.roi_status, "roi_status"))
        object.__setattr__(self, "notes", _list_from(self.notes))
        for value in (self.projected_cost, self.confirmed_cost, self.projected_revenue, self.confirmed_revenue):
            if value is not None and value < 0:
                raise ValueError("cost and revenue values cannot be negative")

    @classmethod
    def placeholder(cls) -> "CostRoiSummaryView":
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostRoiSummaryView":
        return cls(
            projected_cost=data.get("projected_cost"),
            confirmed_cost=data.get("confirmed_cost"),
            projected_revenue=data.get("projected_revenue"),
            confirmed_revenue=data.get("confirmed_revenue"),
            roi_status=data.get("roi_status", CommandCenterControlStatus.PLACEHOLDER),
            notes=_list_from(data.get("notes")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "projected_cost": self.projected_cost,
            "confirmed_cost": self.confirmed_cost,
            "projected_revenue": self.projected_revenue,
            "confirmed_revenue": self.confirmed_revenue,
            "roi_status": self.roi_status.value,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class CommandCenterViewModel:
    view_id: str
    generated_at: str
    status: CommandCenterViewStatus
    missions: List[MissionDashboardView] = field(default_factory=list)
    approvals: List[ApprovalQueueView] = field(default_factory=list)
    audit_timeline: List[AuditTimelineView] = field(default_factory=list)
    agents: List[AgentStatusView] = field(default_factory=list)
    risk_budget_panels: List[RiskAndBudgetPanelView] = field(default_factory=list)
    hermes_payloads: List[HermesPayloadView] = field(default_factory=list)
    devices: List[DeviceStatusView] = field(default_factory=lambda: [DeviceStatusView.placeholder()])
    multi_device_runtime_status: MultiDeviceRuntimeStatus = field(default_factory=MultiDeviceRuntimeStatus.placeholder)
    voice_camera_controls: VoiceCameraControlsView = field(default_factory=VoiceCameraControlsView.placeholder)
    cost_roi_summary: CostRoiSummaryView = field(default_factory=CostRoiSummaryView.placeholder)
    safety_indicator: SafetyIndicatorView = field(
        default_factory=lambda: SafetyIndicatorView(
            status=CommandCenterViewStatus.READY,
            approval_gateway_required=False,
            strong_approval_required=False,
            policy_engine_boundary=_SAFE_POLICY_BOUNDARY,
        )
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _coerce_enum(CommandCenterViewStatus, self.status, "status"))
        object.__setattr__(self, "missions", _coerce_list(self.missions, MissionDashboardView, "missions"))
        object.__setattr__(self, "approvals", _coerce_list(self.approvals, ApprovalQueueView, "approvals"))
        object.__setattr__(self, "audit_timeline", _coerce_list(self.audit_timeline, AuditTimelineView, "audit_timeline"))
        object.__setattr__(self, "agents", _coerce_list(self.agents, AgentStatusView, "agents"))
        object.__setattr__(self, "risk_budget_panels", _coerce_list(self.risk_budget_panels, RiskAndBudgetPanelView, "risk_budget_panels"))
        object.__setattr__(self, "hermes_payloads", _coerce_list(self.hermes_payloads, HermesPayloadView, "hermes_payloads"))
        object.__setattr__(self, "devices", _coerce_list(self.devices, DeviceStatusView, "devices"))
        if isinstance(self.multi_device_runtime_status, dict):
            object.__setattr__(
                self,
                "multi_device_runtime_status",
                MultiDeviceRuntimeStatus.from_dict(self.multi_device_runtime_status),
            )
        object.__setattr__(self, "metadata", _with_safety_metadata(self.metadata))
        if not _is_non_empty_string(self.view_id):
            raise ValueError("view_id must be a non-empty string")
        if not _is_non_empty_string(self.generated_at):
            raise ValueError("generated_at must be a non-empty string")
        if _secret_like_paths({"metadata": self.metadata}):
            raise ValueError("metadata cannot include secret-like keys or values")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandCenterViewModel":
        approvals = [ApprovalQueueView.from_dict(item) for item in data.get("approvals", []) or []]
        missions = [MissionDashboardView.from_dict(item) for item in data.get("missions", []) or []]
        hermes_payloads = [HermesPayloadView.from_dict(item) for item in data.get("hermes_payloads", []) or []]
        risk_budget_panels = [
            RiskAndBudgetPanelView.from_dict(item) for item in data.get("risk_budget_panels", []) or []
        ]
        devices = (
            [DeviceStatusView.from_dict(item) for item in data["devices"]]
            if "devices" in data
            else [DeviceStatusView.placeholder()]
        )
        status = _overall_status(missions, approvals, hermes_payloads, risk_budget_panels)
        return cls(
            view_id=str(data.get("view_id", "")),
            generated_at=str(data.get("generated_at", "")),
            status=status,
            missions=missions,
            approvals=approvals,
            audit_timeline=[AuditTimelineView.from_dict(item) for item in data.get("audit_timeline", []) or []],
            agents=[AgentStatusView.from_dict(item) for item in data.get("agents", []) or []],
            risk_budget_panels=risk_budget_panels,
            hermes_payloads=hermes_payloads,
            devices=devices,
            multi_device_runtime_status=MultiDeviceRuntimeStatus.from_dict(data.get("multi_device_runtime_status")),
            voice_camera_controls=VoiceCameraControlsView.from_dict(data.get("voice_camera_controls") or {}),
            cost_roi_summary=CostRoiSummaryView.from_dict(data.get("cost_roi_summary") or {}),
            safety_indicator=_safety_indicator_from_dict(
                data.get("safety_indicator"), status, approvals, risk_budget_panels
            ),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        metadata = dict(self.metadata)
        safety_flags = {
            key: metadata[key]
            for key in (
                "prepare_only",
                "execution_enabled",
                "approval_enabled",
                "approve_reject_enabled",
                "hermes_connected",
                "approval_gateway_called",
            )
        }
        return {
            "view_id": self.view_id,
            "generated_at": self.generated_at,
            "status": self.status.value,
            **safety_flags,
            "missions": [item.to_dict() for item in self.missions],
            "approvals": [item.to_dict() for item in self.approvals],
            "audit_timeline": [item.to_dict() for item in self.audit_timeline],
            "agents": [item.to_dict() for item in self.agents],
            "risk_budget_panels": [item.to_dict() for item in self.risk_budget_panels],
            "hermes_payloads": [item.to_dict() for item in self.hermes_payloads],
            "devices": [item.to_dict() for item in self.devices],
            "multi_device_runtime_status": self.multi_device_runtime_status.to_dict(),
            "voice_camera_controls": self.voice_camera_controls.to_dict(),
            "cost_roi_summary": self.cost_roi_summary.to_dict(),
            "safety_indicator": self.safety_indicator.to_dict(),
            "metadata": metadata,
        }


def build_command_center_view_model(
    *,
    view_id: str,
    generated_at: str,
    mission_states: Iterable[MissionState] = (),
    approval_payloads: Iterable[MissionApprovalBridgePayload] = (),
    hermes_payloads: Iterable[HermesCommandPayload] = (),
    agent_descriptors: Iterable[HermesAgentDescriptor] = (),
    budget_results: Iterable[MissionBudgetGuardResult] = (),
    metadata: Optional[Dict[str, Any]] = None,
) -> CommandCenterViewModel:
    states = list(mission_states)
    budgets_by_mission = {item.mission_id: item for item in budget_results}

    missions = [MissionDashboardView.from_mission_state(state) for state in states]
    approvals = [
        ApprovalQueueView.from_approval_request(request)
        for state in states
        for request in state.approval_requests
        if _approval_needs_attention(request.approval_level)
    ]
    approvals.extend(
        ApprovalQueueView.from_bridge_payload(payload)
        for payload in approval_payloads
        if _approval_needs_attention(payload.approval_level)
    )
    audit_timeline = [
        AuditTimelineView.from_audit_event(event)
        for state in states
        for event in state.audit_events
    ]
    risk_budget_panels = [
        RiskAndBudgetPanelView.from_mission_state(state, budgets_by_mission.get(state.mission_id))
        for state in states
    ]
    payload_views = [HermesPayloadView.from_hermes_payload(payload) for payload in hermes_payloads]
    agent_views = [AgentStatusView.from_agent_descriptor(descriptor) for descriptor in agent_descriptors]
    status = _overall_status(missions, approvals, payload_views, risk_budget_panels)

    return CommandCenterViewModel(
        view_id=view_id,
        generated_at=generated_at,
        status=status,
        missions=missions,
        approvals=approvals,
        audit_timeline=sorted(audit_timeline, key=lambda item: item.created_at, reverse=True),
        agents=agent_views,
        risk_budget_panels=risk_budget_panels,
        hermes_payloads=payload_views,
        safety_indicator=SafetyIndicatorView(
            status=status,
            approval_gateway_required=bool(approvals) or any(
                _budget_needs_attention(panel.budget_decision) for panel in risk_budget_panels
            ),
            strong_approval_required=any(item.approval_level == MissionApprovalLevel.STRONG_APPROVAL for item in approvals),
            policy_engine_boundary=_SAFE_POLICY_BOUNDARY,
            notes=[
                "prepare-only UI model",
                "no MissionControl mutation",
                "no ApprovalGateway call",
                "no Hermes runtime call",
            ],
        ),
        metadata={
            "phase": "D",
            "ui_ready": True,
            **dict(metadata or {}),
            "operator_console": "prepare_only",
            "mobile_companion": "prepare_only",
            "ambient_vision": "prepare_only",
            "multi_device_runtime": "prepare_only",
            "sandbox_execution": "prepare_only",
            "tool_adoption_pipeline": "prepare_only",
            "asset_factory_web_builder": "prepare_only",
            "deploy_publishing_control": "prepare_only",
            "marketing_distribution_engine": "prepare_only",
            "payments_revenue": "prepare_only",
            "daily_operator_scheduler": "prepare_only",
            "continuous_learning_tech_radar": "prepare_only",
            "personal_os_environment_intelligence": "prepare_only",
            "advanced_personalization_user_model": "prepare_only",
            "future_moonshot_layer": "prepare_only",
            **build_command_center_system_map(),
        },
    )


def _overall_status(
    missions: List[MissionDashboardView],
    approvals: List[ApprovalQueueView],
    payloads: List[HermesPayloadView],
    budget_panels: Optional[List[RiskAndBudgetPanelView]] = None,
) -> CommandCenterViewStatus:
    if any(item.status in {MissionStatus.BLOCKED, MissionStatus.FAILED} for item in missions):
        return CommandCenterViewStatus.BLOCKED
    if any(item.status == "blocked" for item in payloads):
        return CommandCenterViewStatus.BLOCKED
    if any(_approval_is_blocking(item.approval_level) for item in approvals):
        return CommandCenterViewStatus.BLOCKED
    if any(_budget_is_blocking(item.budget_decision) for item in budget_panels or []):
        return CommandCenterViewStatus.BLOCKED
    if any(_budget_needs_attention(item.budget_decision) for item in budget_panels or []):
        return CommandCenterViewStatus.NEEDS_ATTENTION
    if approvals or any(item.status == MissionStatus.AWAITING_APPROVAL for item in missions):
        return CommandCenterViewStatus.NEEDS_ATTENTION
    return CommandCenterViewStatus.READY


def _risk_from_status(status: MissionStatus) -> MissionDryRunRiskLevel:
    if status in {MissionStatus.BLOCKED, MissionStatus.FAILED}:
        return MissionDryRunRiskLevel.HIGH
    if status == MissionStatus.AWAITING_APPROVAL:
        return MissionDryRunRiskLevel.MEDIUM
    return MissionDryRunRiskLevel.LOW


def _risk_from_approval_level(level: MissionApprovalLevel) -> MissionDryRunRiskLevel:
    if level in {MissionApprovalLevel.STRONG_APPROVAL, MissionApprovalLevel.DENIED}:
        return MissionDryRunRiskLevel.HIGH
    if level in {MissionApprovalLevel.REQUIRES_REVIEW, MissionApprovalLevel.REQUIRES_APPROVAL}:
        return MissionDryRunRiskLevel.MEDIUM
    return MissionDryRunRiskLevel.LOW


def _approval_is_pending(level: MissionApprovalLevel) -> bool:
    return level in {
        MissionApprovalLevel.REQUIRES_REVIEW,
        MissionApprovalLevel.REQUIRES_APPROVAL,
        MissionApprovalLevel.STRONG_APPROVAL,
    }


def _approval_is_blocking(level: MissionApprovalLevel) -> bool:
    return level == MissionApprovalLevel.DENIED


def _approval_needs_attention(level: MissionApprovalLevel) -> bool:
    return _approval_is_pending(level) or _approval_is_blocking(level)


def _budget_is_blocking(decision: str) -> bool:
    return str(decision).lower() == "blocked"


def _budget_needs_attention(decision: str) -> bool:
    normalized = str(decision).lower()
    return normalized in {"blocked", "requires_approval", "requires_strong_approval"}


def _coerce_enum(enum_cls: Any, value: Any, field_name: str) -> Any:
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid {enum_cls.__name__}") from exc


def _coerce_list(items: Iterable[Any], item_type: Any, field_name: str) -> List[Any]:
    values = list(items or [])
    if not all(isinstance(item, item_type) for item in values):
        raise ValueError(f"{field_name} must contain {item_type.__name__} items")
    return values


def _list_from(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    return [str(value)]


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_audit_summary(summary: str, *, sensitive: bool, redacted_fields: Iterable[str]) -> str:
    if sensitive or list(redacted_fields):
        return _REDACTED_AUDIT_SUMMARY
    return _safe_ui_text(summary, _REDACTED_AUDIT_SUMMARY)


def _safe_ui_text(value: Optional[str], redacted_value: str) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    if _secret_like_text(text):
        return redacted_value
    return text


def _with_safety_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    filtered = {
        key: value
        for key, value in dict(metadata or {}).items()
        if str(key) not in _RESERVED_METADATA_KEYS
    }
    filtered.update(_SAFETY_METADATA)
    return filtered


def _safety_indicator_from_dict(
    data: Optional[Dict[str, Any]],
    status: CommandCenterViewStatus = CommandCenterViewStatus.NEEDS_ATTENTION,
    approvals: Optional[List[ApprovalQueueView]] = None,
    budget_panels: Optional[List[RiskAndBudgetPanelView]] = None,
) -> SafetyIndicatorView:
    if data:
        indicator = SafetyIndicatorView.from_dict(data)
        if status == CommandCenterViewStatus.BLOCKED and indicator.status != CommandCenterViewStatus.BLOCKED:
            return SafetyIndicatorView(
                status=CommandCenterViewStatus.BLOCKED,
                approval_gateway_required=indicator.approval_gateway_required,
                strong_approval_required=indicator.strong_approval_required,
                policy_engine_boundary=indicator.policy_engine_boundary,
                notes=indicator.notes,
            )
        return indicator
    pending_approvals = [approval for approval in approvals or [] if _approval_is_pending(approval.approval_level)]
    budget_attention = any(_budget_needs_attention(panel.budget_decision) for panel in budget_panels or [])
    derived_status = CommandCenterViewStatus.NEEDS_ATTENTION
    if status == CommandCenterViewStatus.BLOCKED:
        derived_status = CommandCenterViewStatus.BLOCKED
    return SafetyIndicatorView(
        status=derived_status,
        approval_gateway_required=bool(pending_approvals) or budget_attention,
        strong_approval_required=any(
            approval.approval_level == MissionApprovalLevel.STRONG_APPROVAL for approval in pending_approvals
        ),
        policy_engine_boundary=_SAFE_POLICY_BOUNDARY,
        notes=["safety_indicator missing; deserialized conservatively"],
    )


def _secret_like_paths(value: Any, prefix: str = "") -> List[str]:
    paths: List[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            if _secret_like_text(key_text):
                paths.append(path)
            paths.extend(_secret_like_paths(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_secret_like_paths(item, f"{prefix}[{index}]"))
    elif isinstance(value, str) and _secret_like_text(value):
        paths.append(prefix or "<value>")
    return paths


def _secret_like_text(value: str) -> bool:
    lowered = value.lower()
    return any(
        marker in lowered
        for marker in (
            "secret",
            "token",
            "password",
            "passphrase",
            "api_key",
            "apikey",
            "api key",
            "credential",
            "credentials",
            "bearer",
            "authorization",
            "auth",
            "private key",
            "access key",
            "refresh token",
            "client secret",
            ".env",
        )
    )
