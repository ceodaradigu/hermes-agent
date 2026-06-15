from __future__ import annotations

from typing import Any, Dict, Iterable, List

from jarvis.mark_3_negative_intent_parser import contains_actionable_marker
from jarvis.mark_3_mission_loop_models import MissionClassification, MissionIntake


LEVEL_5_MARKERS = (
    "steal", "robar", "bypass", "saltarse 2fa", "bypass 2fa", "steal cookie",
    "steal token", "credential theft", "unauthorized access", "sin autorizacion",
    "fake execution", "fingir ejecucion", "hide risk", "ocultar riesgo",
)
LEVEL_4_MARKERS = (
    "production", "deploy", "stripe live", "move money", "payment", "modify dns",
    "publish", "bulk email", "delete data", "credential", "secret", ".env",
)
LEVEL_3_MARKERS = (
    "modify code", "code change", "ai cli", "paid api", "private data", "external",
    "network", "shell", "subprocess", "write file", "filesystem write",
)
LEVEL_2_MARKERS = ("modify documentation", "run tests", "create file", "worktree", "local write")


def validate_intake_payload(values: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    objective = _text(values.get("objective"))
    allowed_scope = _items(values.get("allowed_scope", values.get("scope")))
    allowed_tools = _items(values.get("allowed_tools"))
    prohibited_tools = _items(values.get("prohibited_tools"))
    allowed_data = _items(values.get("allowed_data"))
    if not objective:
        errors.append("objective must be a non-empty string")
    if not allowed_scope or any(item.lower() in {"*", "all", "anything", "unlimited", "anywhere"} for item in allowed_scope):
        errors.append("allowed_scope must be explicit and non-ambiguous")
    for field_name in ("monetary_budget", "time_budget_seconds"):
        value = values.get(field_name)
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
            errors.append(f"{field_name} cannot be negative")
    max_steps = values.get("max_steps", 10)
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 1 or max_steps > 100:
        errors.append("max_steps must be an integer between 1 and 100")
    requested_risk = values.get("requested_risk_level", values.get("risk_level"))
    if requested_risk is not None and (
        not isinstance(requested_risk, int) or isinstance(requested_risk, bool) or not 0 <= requested_risk <= 5
    ):
        errors.append("requested_risk_level must be an integer between 0 and 5")
    overlap = {item.lower() for item in allowed_tools} & {item.lower() for item in prohibited_tools}
    if overlap:
        errors.append("tools cannot be both allowed and prohibited: " + ", ".join(sorted(overlap)))
    classification_text = _classification_text_from_values(values)
    if _mentions_sensitive(classification_text) and not allowed_data:
        errors.append("sensitive data is referenced but allowed_data is empty")
    if _contains_any(classification_text, LEVEL_5_MARKERS):
        errors.append("intake implies permanently denied level 5 action")
    if values.get("proposed_steps") is not None and not isinstance(values.get("proposed_steps"), list):
        errors.append("proposed_steps must be a list")
    return errors


def classify_mission(intake: MissionIntake, *, available_capabilities: Iterable[str]) -> MissionClassification:
    text = _classification_text_from_values({
        "objective": intake.objective,
        "context": intake.context,
        "proposed_steps": intake.proposed_steps,
    })
    requested = intake.requested_risk_level
    inferred = _infer_risk(text)
    risk = max(requested, inferred) if isinstance(requested, int) and 0 <= requested <= 5 else inferred
    legal = not _contains_any(text, LEVEL_5_MARKERS)
    safe = legal
    authorization = intake.declared_authorization.lower()
    authorized = authorization not in {"", "unknown", "none", "unauthorized", "not authorized"}
    required = _required_capabilities(intake)
    available = {item.lower() for item in available_capabilities}
    capability_available = all(item.lower() in available for item in required) if required else True
    technically_supported = capability_available
    blocked: List[str] = []
    uncertainties = list(intake.uncertainties)
    if not legal:
        blocked.append("level 5 action is permanently denied")
        risk = 5
    if not authorized:
        blocked.append("declared authorization is missing or unknown")
        uncertainties.append("authorization")
    if not capability_available:
        blocked.append("required capability is unavailable")
        uncertainties.append("execution capability")
    if risk == 5:
        blocked.append("level 5 cannot be approved or advanced")
    approval_required = risk >= 2 and risk < 5
    strong = risk >= 3 and risk < 5
    double = risk == 4
    triple = risk == 4 and _contains_any(text, ("money", "credential", "delete", "production"))
    return MissionClassification(
        legal=legal,
        safe=safe,
        authorized=authorized,
        technically_supported=technically_supported,
        capability_available=capability_available,
        risk_level=risk,
        approval_required=approval_required,
        strong_approval_required=strong,
        double_confirmation_required=double,
        triple_confirmation_required=triple,
        audit_required=risk >= 2,
        rollback_required=risk >= 3,
        stop_plan_required=risk >= 2,
        blocked_reasons=list(dict.fromkeys(blocked)),
        uncertainties=list(dict.fromkeys(uncertainties)),
        evidence_requirements=["evidence compatible with each claimed outcome"],
        research_prototype_fallback=(
            "Research or prototype preview only; do not claim execution or operational capability."
            if not capability_available and risk < 5 else None
        ),
        readback_required=risk == 4,
        permanent_denial=risk == 5,
    )


def risk_controls(risk: int) -> Dict[str, bool]:
    return {
        "approval_required": 2 <= risk < 5,
        "strong_approval_required": 3 <= risk < 5,
        "double_confirmation_required": risk == 4,
        "triple_confirmation_required": risk == 4,
    }


def _required_capabilities(intake: MissionIntake) -> List[str]:
    capabilities = []
    for step in intake.proposed_steps:
        capability = _text(step.get("required_capability"))
        if capability:
            capabilities.append(capability)
    return list(dict.fromkeys(capabilities))


def _infer_risk(text: str) -> int:
    if _contains_any(text, LEVEL_5_MARKERS):
        return 5
    if _contains_any(text, LEVEL_4_MARKERS):
        return 4
    if _contains_any(text, LEVEL_3_MARKERS):
        return 3
    if _contains_any(text, LEVEL_2_MARKERS):
        return 2
    return 0


def _mentions_sensitive(text: str) -> bool:
    return _contains_any(text, ("private data", "personal data", "pii", "secret", "credential"))


def _classification_text_from_values(values: Dict[str, Any]) -> str:
    steps = values.get("proposed_steps") if isinstance(values.get("proposed_steps"), list) else []
    step_fields = []
    for step in steps:
        if isinstance(step, dict):
            step_fields.append({
                key: step.get(key)
                for key in ("description", "objective", "action_type", "required_capability", "tool_candidate")
                if step.get(key) is not None
            })
    objective = _text(values.get("objective"))
    context = _text(values.get("context"))
    # Common explicit negations must not escalate a harmless task.
    for phrase in ("no external side effects", "without external side effects", "no network"):
        context = context.lower().replace(phrase, "")
    return _combined({"objective": objective, "context": context, "proposed_steps": step_fields})


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    return contains_actionable_marker(text, markers)


def _combined(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_combined(item)}" for key, item in value.items()).lower()
    if isinstance(value, (list, tuple)):
        return " ".join(_combined(item) for item in value).lower()
    return str(value or "").lower()


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_text(item) for item in value if _text(item)]
    return [_text(value)] if _text(value) else []


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())
