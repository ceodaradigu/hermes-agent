from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ActionClassification(str, Enum):
    ALLOWED = "allowed"
    REQUIRES_APPROVAL = "requires_approval"
    STRONG_APPROVAL = "strong_approval"
    DENIED = "denied"
    UNKNOWN_REQUIRES_REVIEW = "unknown_requires_review"


@dataclass(frozen=True)
class MissionEnvelopeValidationResult:
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class MissionEnvelope:
    mission_id: str
    objective: str
    success_metric: str
    deadline: Optional[str] = None
    budget_limit: Optional[float] = None
    cost_limit_per_action: Optional[float] = None
    allowed_actions: List[str] = field(default_factory=list)
    requires_approval_actions: List[str] = field(default_factory=list)
    strong_approval_actions: List[str] = field(default_factory=list)
    denied_actions: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    candidate_tools: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)
    stop_conditions: List[str] = field(default_factory=list)
    audit_requirements: List[str] = field(default_factory=list)
    net_target: Optional[str] = None
    reporting_frequency: Optional[str] = None
    data_access_scope: List[str] = field(default_factory=list)
    identity_use_policy: Optional[str] = None
    publication_policy: Optional[str] = None
    spending_policy: Optional[str] = None
    external_contact_policy: Optional[str] = None
    install_dependency_policy: Optional[str] = None
    runtime_execution_policy: Optional[str] = None
    rollback_plan: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionEnvelope":
        return cls(
            mission_id=str(data.get("mission_id", "")),
            objective=str(data.get("objective", "")),
            success_metric=str(data.get("success_metric", "")),
            deadline=data.get("deadline"),
            budget_limit=data.get("budget_limit"),
            cost_limit_per_action=data.get("cost_limit_per_action"),
            allowed_actions=_list_from(data.get("allowed_actions")),
            requires_approval_actions=_list_from(data.get("requires_approval_actions")),
            strong_approval_actions=_list_from(data.get("strong_approval_actions")),
            denied_actions=_list_from(data.get("denied_actions")),
            allowed_tools=_list_from(data.get("allowed_tools")),
            candidate_tools=_list_from(data.get("candidate_tools")),
            channels=_list_from(data.get("channels")),
            stop_conditions=_list_from(data.get("stop_conditions")),
            audit_requirements=_list_from(data.get("audit_requirements")),
            net_target=data.get("net_target"),
            reporting_frequency=data.get("reporting_frequency"),
            data_access_scope=_list_from(data.get("data_access_scope")),
            identity_use_policy=data.get("identity_use_policy"),
            publication_policy=data.get("publication_policy"),
            spending_policy=data.get("spending_policy"),
            external_contact_policy=data.get("external_contact_policy"),
            install_dependency_policy=data.get("install_dependency_policy"),
            runtime_execution_policy=data.get("runtime_execution_policy"),
            rollback_plan=data.get("rollback_plan"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "success_metric": self.success_metric,
            "deadline": self.deadline,
            "budget_limit": self.budget_limit,
            "cost_limit_per_action": self.cost_limit_per_action,
            "allowed_actions": list(self.allowed_actions),
            "requires_approval_actions": list(self.requires_approval_actions),
            "strong_approval_actions": list(self.strong_approval_actions),
            "denied_actions": list(self.denied_actions),
            "allowed_tools": list(self.allowed_tools),
            "candidate_tools": list(self.candidate_tools),
            "channels": list(self.channels),
            "stop_conditions": list(self.stop_conditions),
            "audit_requirements": list(self.audit_requirements),
            "net_target": self.net_target,
            "reporting_frequency": self.reporting_frequency,
            "data_access_scope": list(self.data_access_scope),
            "identity_use_policy": self.identity_use_policy,
            "publication_policy": self.publication_policy,
            "spending_policy": self.spending_policy,
            "external_contact_policy": self.external_contact_policy,
            "install_dependency_policy": self.install_dependency_policy,
            "runtime_execution_policy": self.runtime_execution_policy,
            "rollback_plan": self.rollback_plan,
        }


_BLANKET_APPROVAL_PHRASES = {
    "approve_all_forever",
    "do_anything",
    "unlimited",
    "no_limits",
    "whatever_it_takes",
    "haz_todo_lo_necesario_sin_limites",
}


def validate_mission_envelope(envelope: MissionEnvelope) -> MissionEnvelopeValidationResult:
    errors: List[str] = []

    if not _is_non_empty_string(envelope.mission_id):
        errors.append("mission_id must be a non-empty string")
    if not _is_non_empty_string(envelope.objective):
        errors.append("objective must be a non-empty string")
    if not _is_non_empty_string(envelope.success_metric):
        errors.append("success_metric must be a non-empty string")

    if envelope.budget_limit is not None and envelope.budget_limit < 0:
        errors.append("budget_limit cannot be negative")
    if envelope.cost_limit_per_action is not None and envelope.cost_limit_per_action < 0:
        errors.append("cost_limit_per_action cannot be negative")
    if (
        envelope.budget_limit is not None
        and envelope.cost_limit_per_action is not None
        and envelope.cost_limit_per_action > envelope.budget_limit
    ):
        errors.append("cost_limit_per_action cannot exceed budget_limit")

    if not envelope.deadline and envelope.budget_limit is None and not envelope.stop_conditions:
        errors.append("mission envelope must include deadline, budget_limit, or stop_conditions")

    action_groups = {
        "allowed_actions": envelope.allowed_actions,
        "requires_approval_actions": envelope.requires_approval_actions,
        "strong_approval_actions": envelope.strong_approval_actions,
        "denied_actions": envelope.denied_actions,
    }
    for field_name, actions in action_groups.items():
        errors.extend(_validate_non_empty_list_items(field_name, actions))
        errors.extend(_validate_no_blanket_approval(field_name, actions))

    seen_actions: Dict[str, str] = {}
    for field_name, actions in action_groups.items():
        for action in actions:
            normalized = _normalize(action)
            if not normalized:
                continue
            previous_field = seen_actions.get(normalized)
            if previous_field:
                errors.append(f"action {action!r} appears in both {previous_field} and {field_name}")
            else:
                seen_actions[normalized] = field_name

    tool_overlap = _normalized_intersection(envelope.allowed_tools, envelope.candidate_tools)
    if tool_overlap:
        errors.append(
            "candidate_tools are proposals only and cannot also appear in allowed_tools: "
            + ", ".join(sorted(tool_overlap))
        )

    policy_values = [
        ("identity_use_policy", envelope.identity_use_policy),
        ("publication_policy", envelope.publication_policy),
        ("spending_policy", envelope.spending_policy),
        ("external_contact_policy", envelope.external_contact_policy),
        ("install_dependency_policy", envelope.install_dependency_policy),
        ("runtime_execution_policy", envelope.runtime_execution_policy),
    ]
    for field_name, value in policy_values:
        if value is not None and _normalize(value) in _BLANKET_APPROVAL_PHRASES:
            errors.append(f"{field_name} cannot grant vague blanket approval")

    return MissionEnvelopeValidationResult(errors=errors)


def classify_action(envelope: MissionEnvelope, action: str) -> ActionClassification:
    normalized = _normalize(action)
    if normalized in {_normalize(a) for a in envelope.denied_actions}:
        return ActionClassification.DENIED
    if normalized in {_normalize(a) for a in envelope.strong_approval_actions}:
        return ActionClassification.STRONG_APPROVAL
    if normalized in {_normalize(a) for a in envelope.requires_approval_actions}:
        return ActionClassification.REQUIRES_APPROVAL
    if normalized in {_normalize(a) for a in envelope.allowed_actions}:
        return ActionClassification.ALLOWED
    return ActionClassification.UNKNOWN_REQUIRES_REVIEW


def _list_from(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _is_non_empty_string(value: str) -> bool:
    return bool((value or "").strip())


def _validate_non_empty_list_items(field_name: str, values: List[str]) -> List[str]:
    return [f"{field_name} cannot contain empty strings" for value in values if not _is_non_empty_string(value)]


def _validate_no_blanket_approval(field_name: str, values: List[str]) -> List[str]:
    errors = []
    for value in values:
        if _normalize(value) in _BLANKET_APPROVAL_PHRASES:
            errors.append(f"{field_name} cannot include vague blanket approval: {value!r}")
    return errors


def _normalized_intersection(left: List[str], right: List[str]) -> set[str]:
    return {_normalize(item) for item in left if _normalize(item)} & {
        _normalize(item) for item in right if _normalize(item)
    }


def _normalize(value: str) -> str:
    return (value or "").strip().lower()
