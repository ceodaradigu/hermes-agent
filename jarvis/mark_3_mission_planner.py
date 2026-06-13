from __future__ import annotations

import math
from typing import Any, Callable, Dict, List

from jarvis.mark_3_mission_loop_models import MissionClassification, MissionIntake, MissionStep
from jarvis.mark_3_mission_loop_policy import risk_controls


class ControlledMissionPlanner:
    def __init__(self, *, id_factory: Callable[[], str]) -> None:
        self.id_factory = id_factory

    def plan(self, intake: MissionIntake, classification: MissionClassification) -> List[MissionStep]:
        sources = intake.proposed_steps or [{
            "description": f"Prepare bounded candidate for: {intake.objective}",
            "objective": intake.objective,
            "action_type": "internal_prepare",
            "required_capability": "internal_prepare",
            "scope": list(intake.allowed_scope),
            "expected_outputs": [intake.desired_outcome or "bounded preview"],
        }]
        if len(sources) > intake.max_steps:
            raise ValueError("plan exceeds max_steps")
        steps: List[MissionStep] = []
        ids = [str(source.get("step_id") or f"step-{index + 1}") for index, source in enumerate(sources)]
        default_timeout = (
            max(1, intake.time_budget_seconds // len(sources))
            if intake.time_budget_seconds is not None
            else None
        )
        if len(set(ids)) != len(ids):
            raise ValueError("step IDs must be unique")
        for index, source in enumerate(sources):
            declared_risk = int(source.get("risk_level", classification.risk_level))
            if not 0 <= declared_risk <= 5:
                raise ValueError("step risk_level must be between 0 and 5")
            risk = max(declared_risk, classification.risk_level)
            controls = risk_controls(risk)
            scope = _items(source.get("scope")) or list(intake.allowed_scope)
            tool = _optional(source.get("tool_candidate"))
            budget = _optional_non_negative_number(source.get("budget"), "step budget")
            timeout = _optional_non_negative_number(
                source.get("timeout_seconds", default_timeout),
                "step timeout_seconds",
            )
            blocked: List[str] = []
            if declared_risk < classification.risk_level:
                blocked.append("step risk downgrade prevented")
            if not _subset(scope, intake.allowed_scope):
                blocked.append("step scope is outside mission scope")
            if tool and tool.lower() in {item.lower() for item in intake.prohibited_tools}:
                blocked.append("tool is prohibited")
            if tool and tool.lower() not in {item.lower() for item in intake.allowed_tools}:
                blocked.append("tool is not in allowed tools")
            if budget is not None and intake.monetary_budget is not None and budget > intake.monetary_budget:
                blocked.append("step budget exceeds mission budget")
            required = _text(source.get("required_capability")) or "internal_prepare"
            capability_available = required == "internal_prepare"
            if not capability_available:
                blocked.append("required capability is unavailable")
            dependencies = _items(source.get("dependencies"))
            steps.append(MissionStep(
                step_id=ids[index],
                order=index + 1,
                description=_text(source.get("description")) or f"Step {index + 1}",
                objective=_text(source.get("objective")) or intake.objective,
                action_type=_text(source.get("action_type")) or "internal_prepare",
                inputs=dict(source.get("inputs") or {}),
                expected_outputs=_items(source.get("expected_outputs")) or ["bounded result"],
                required_capability=required,
                tool_candidate=tool,
                scope=scope,
                budget=budget,
                timeout_seconds=timeout,
                risk_level=risk,
                approval_required=controls["approval_required"],
                strong_approval_required=controls["strong_approval_required"],
                double_confirmation_required=controls["double_confirmation_required"],
                triple_confirmation_required=bool(source.get("triple_confirmation_required", classification.triple_confirmation_required)),
                preconditions=_items(source.get("preconditions")),
                dependencies=dependencies,
                evidence_requirements=_items(source.get("evidence_requirements")) or list(classification.evidence_requirements),
                stop_condition=_text(source.get("stop_condition")) or "; ".join(intake.stop_conditions) or "stop on any policy violation",
                rollback_compensation=_text(source.get("rollback_compensation")) or intake.expected_rollback or "no side effects; no rollback needed",
                status="blocked" if blocked else "planned",
                blocked_reasons=list(dict.fromkeys(blocked)),
                capability_available=capability_available,
            ))
        self._validate_dependencies(steps)
        total_budget = sum(step.budget or 0 for step in steps)
        individual_budget_blocked = any(
            "step budget exceeds mission budget" in step.blocked_reasons for step in steps
        )
        if intake.monetary_budget is not None and total_budget > intake.monetary_budget and not individual_budget_blocked:
            raise ValueError("plan aggregate budget exceeds mission budget")
        total_timeout = sum(step.timeout_seconds or 0 for step in steps)
        if intake.time_budget_seconds is not None and total_timeout > intake.time_budget_seconds:
            raise ValueError("plan aggregate timeout exceeds mission time budget")
        return steps

    @staticmethod
    def _validate_dependencies(steps: List[MissionStep]) -> None:
        graph = {step.step_id: list(step.dependencies) for step in steps}
        known = set(graph)
        for step_id, dependencies in graph.items():
            unknown = set(dependencies) - known
            if unknown:
                raise ValueError(f"step {step_id} has unknown dependencies: {sorted(unknown)}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(step_id: str) -> None:
            if step_id in visiting:
                raise ValueError("plan contains circular dependencies")
            if step_id in visited:
                return
            visiting.add(step_id)
            for dependency in graph[step_id]:
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in graph:
            visit(step_id)


def _subset(values: List[str], allowed: List[str]) -> bool:
    normalized = {item.lower() for item in allowed}
    return bool(normalized) and all(item.lower() in normalized for item in values)


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_text(item) for item in value if _text(item)]
    return [_text(value)] if _text(value) else []


def _optional(value: Any) -> str | None:
    return _text(value) or None


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _optional_non_negative_number(value: Any, name: str) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a non-negative finite number")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a non-negative finite number")
    return value
