from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.missions.state_store import MissionState


class MissionBudgetGuardDecision(str, Enum):
    ALLOWED = "allowed"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_STRONG_APPROVAL = "requires_strong_approval"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MissionBudgetGuardResult:
    result_id: str
    mission_id: Optional[str]
    decision: MissionBudgetGuardDecision
    can_spend: bool
    cost_summary: Dict[str, Optional[float]]
    violations: List[str]
    budget_remaining: Optional[float]
    audit_summary: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision", _coerce_enum(MissionBudgetGuardDecision, self.decision, "decision"))
        object.__setattr__(self, "cost_summary", dict(self.cost_summary or {}))
        object.__setattr__(self, "violations", _list_from(self.violations))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        if self.can_spend:
            raise ValueError("budget guard cannot permit spending in v1")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionBudgetGuardResult":
        return cls(
            result_id=str(data.get("result_id", "")),
            mission_id=data.get("mission_id"),
            decision=data.get("decision", ""),
            can_spend=bool(data.get("can_spend", False)),
            cost_summary=dict(data.get("cost_summary") or {}),
            violations=_list_from(data.get("violations")),
            budget_remaining=data.get("budget_remaining"),
            audit_summary=str(data.get("audit_summary", "")),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "mission_id": self.mission_id,
            "decision": self.decision.value,
            "can_spend": self.can_spend,
            "cost_summary": dict(self.cost_summary),
            "violations": list(self.violations),
            "budget_remaining": self.budget_remaining,
            "audit_summary": self.audit_summary,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


def evaluate_mission_budget_guard(
    state: Optional[MissionState] = None,
    *,
    budget_limit: Optional[float] = None,
    cost_limit_per_action: Optional[float] = None,
    estimated_cost: Optional[float] = None,
    proposed_cost: Optional[float] = None,
    projected_cost: Optional[float] = None,
    confirmed_cost: Optional[float] = None,
    evaluator: str = "jarvis",
) -> MissionBudgetGuardResult:
    if state is not None and not isinstance(state, MissionState):
        raise ValueError("state must be a MissionState")
    if state is not None:
        if budget_limit is None:
            budget_limit = state.envelope.budget_limit
        if cost_limit_per_action is None:
            cost_limit_per_action = state.envelope.cost_limit_per_action

    costs = {
        "budget_limit": _as_float(budget_limit),
        "cost_limit_per_action": _as_float(cost_limit_per_action),
        "estimated_cost": _as_float(estimated_cost),
        "proposed_cost": _as_float(proposed_cost),
        "projected_cost": _as_float(projected_cost),
        "confirmed_cost": _as_float(confirmed_cost),
    }
    spend_candidates = [
        value
        for key, value in costs.items()
        if key not in {"budget_limit", "cost_limit_per_action"} and value is not None
    ]
    highest_cost = max(spend_candidates) if spend_candidates else None
    budget_remaining = None
    if costs["budget_limit"] is not None and costs["confirmed_cost"] is not None:
        budget_remaining = costs["budget_limit"] - costs["confirmed_cost"]

    violations: List[str] = []
    decision = MissionBudgetGuardDecision.ALLOWED

    for key, value in costs.items():
        if value is not None and value < 0:
            violations.append(f"{key} cannot be negative")
    if violations:
        decision = MissionBudgetGuardDecision.BLOCKED
    elif spend_candidates and costs["budget_limit"] is None:
        decision = MissionBudgetGuardDecision.REQUIRES_STRONG_APPROVAL if highest_cost and highest_cost > 0 else MissionBudgetGuardDecision.REQUIRES_APPROVAL
        violations.append("spending without budget_limit requires approval")
    else:
        if highest_cost is not None and costs["budget_limit"] is not None and highest_cost > costs["budget_limit"]:
            decision = MissionBudgetGuardDecision.REQUIRES_STRONG_APPROVAL
            violations.append("cost exceeds budget_limit")
        if (
            highest_cost is not None
            and costs["cost_limit_per_action"] is not None
            and highest_cost > costs["cost_limit_per_action"]
        ):
            decision = MissionBudgetGuardDecision.REQUIRES_STRONG_APPROVAL
            violations.append("cost exceeds cost_limit_per_action")
        if costs["confirmed_cost"] is not None and costs["projected_cost"] is not None and costs["confirmed_cost"] > costs["projected_cost"]:
            decision = MissionBudgetGuardDecision.REQUIRES_APPROVAL
            violations.append("confirmed_cost exceeds projected_cost")

    return MissionBudgetGuardResult(
        result_id=str(uuid4()),
        mission_id=state.mission_id if state is not None else None,
        decision=decision,
        can_spend=False,
        cost_summary=costs,
        violations=violations,
        budget_remaining=budget_remaining,
        audit_summary=(
            f"Budget guard evaluated mission {state.mission_id if state is not None else 'none'}: "
            f"decision={decision.value}; no payment, external API call, or spend occurred."
        ),
        created_at=_now_iso(),
        metadata={"evaluator": evaluator or "jarvis", "prepare_only": True, "external_api_called": False},
    )


def _as_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return float(value)


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
