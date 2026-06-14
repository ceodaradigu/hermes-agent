from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from jarvis.approval_audit import redact_sensitive_data


SOURCES = {"github", "web", "docs", "local_repo"}
GOALS = {"improve_jarvis", "improve_hermes", "find_tools", "detect_risks", "detect_opportunities"}
RISK_LEVELS = {"low", "medium", "high", "critical"}
APPROVAL_LEVELS = ("direct", "simple", "strong", "double", "triple")
EXTERNAL_SOURCES = {"github", "web"}
CAPABILITY_BY_SOURCE = {
    "github": "github_search",
    "web": "web_search",
    "docs": "docs_reader",
    "local_repo": "local_repo_read",
}
AUTO_SENSITIVE_ACTIONS = {
    "install": "auto-install is not allowed",
    "commit": "auto-commit is not allowed",
    "push": "auto-push is not allowed",
    "merge": "auto-merge is not allowed",
    "deploy": "auto-deploy is not allowed",
    "production": "production changes require strong approval or higher",
    "money": "money movement is not allowed without explicit high-confidence approval",
    "payment": "money movement is not allowed without explicit high-confidence approval",
    "stripe live": "live payment operations require triple approval",
}
SECRET_MARKERS = (".env", "api_key", "authorization:", "bearer ", "credential", "password", "private_key", "secret", "token")


@dataclass(frozen=True)
class ResearchPolicyDecision:
    source: str
    goal: str
    risk_level: str
    requires_approval: bool
    approval_level: str
    execution_status: str
    candidate_state: str
    capability: str
    capability_status: str
    legal: bool
    safe: bool
    authorized: bool
    technically_supported: bool
    network_required: bool
    approval_valid: bool
    approval_supplied_level: str
    permanent_denial: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    no_auto_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["is_executable_candidate"] = self.candidate_state == "executable_candidate"
        data["can_become_executable_candidate"] = not self.permanent_denial
        data["approval_is_gate_not_permanent_ban"] = True
        return data


class ApprovalAwareResearchPolicy:
    """Classifies Mark 3 research plans without executing the research."""

    def evaluate(self, values: Dict[str, Any]) -> Dict[str, Any]:
        raw_text = _combined(values or {})
        safe, redacted = redact_sensitive_data(dict(values or {}))
        source = _normalized(safe.get("source"), "local_repo")
        source_supported = source in SOURCES
        goal = _choice(safe.get("goal"), GOALS, "improve_jarvis")
        text = _combined(safe)
        risk = _risk_level(safe.get("risk", safe.get("risk_level")), text)
        capability = CAPABILITY_BY_SOURCE.get(source, "unsupported_source")
        connected = source_supported and _capability_connected(source, capability, safe.get("capabilities_connected"))
        network_required = source in EXTERNAL_SOURCES
        no_auto_actions = _no_auto_actions(text)
        illegal = any(marker in raw_text for marker in ("steal", "exfiltrate", "bypass 2fa", "unauthorized access"))
        secret_collection = any(marker in raw_text for marker in SECRET_MARKERS)
        safe_action = not (illegal or secret_collection)
        authorized = bool(safe.get("authorized", True))
        required_approval = _required_approval_level(risk, network_required, text)
        requires_approval = required_approval != "direct"
        supplied = _choice(safe.get("approval_level"), set(APPROVAL_LEVELS), "direct")
        approval_valid = bool(safe.get("approval_valid", False))
        sufficient_approval = (not requires_approval) or (
            approval_valid and _approval_rank(supplied) >= _approval_rank(required_approval)
        )
        permanent_denial = bool(illegal or not safe_action or not authorized or not source_supported)
        blocked: List[str] = []
        missing: List[str] = []
        if illegal:
            blocked.append("illegal or unauthorized access request")
        if secret_collection:
            blocked.append("secret collection is blocked")
        if not authorized:
            blocked.append("authorization missing")
        if not source_supported:
            blocked.append("source is unsupported")
        if not connected:
            missing.append("capability_not_connected_yet")
        if requires_approval and not sufficient_approval:
            missing.append(f"{required_approval} approval required")
        if redacted:
            blocked.append("sensitive fields were redacted")

        if permanent_denial:
            status = "blocked"
            candidate_state = "blocked"
            capability_status = "blocked"
        elif not connected:
            status = "setup_required"
            candidate_state = "setup_required"
            capability_status = "capability_not_connected_yet"
        elif requires_approval and not sufficient_approval:
            status = "awaiting_approval"
            candidate_state = "awaiting_approval"
            capability_status = "connected"
        else:
            status = "ready"
            candidate_state = "executable_candidate"
            capability_status = "connected"

        decision = ResearchPolicyDecision(
            source=source,
            goal=goal,
            risk_level=risk,
            requires_approval=requires_approval,
            approval_level=required_approval,
            execution_status=status,
            candidate_state=candidate_state,
            capability=capability,
            capability_status=capability_status,
            legal=not illegal,
            safe=safe_action,
            authorized=authorized,
            technically_supported=source_supported,
            network_required=network_required,
            approval_valid=sufficient_approval,
            approval_supplied_level=supplied,
            permanent_denial=permanent_denial,
            blocked_reasons=list(dict.fromkeys(blocked)),
            missing_requirements=list(dict.fromkeys(missing)),
            no_auto_actions=list(dict.fromkeys(no_auto_actions)),
        )
        return decision.to_dict()


def _required_approval_level(risk: str, network_required: bool, text: str) -> str:
    if any(marker in text for marker in ("stripe live", "money", "payment", "deploy", "production", "install", "commit", "push", "merge")):
        return "triple" if any(marker in text for marker in ("stripe live", "money", "payment", "deploy", "production")) else "double"
    if risk == "critical":
        return "double"
    if risk == "high":
        return "strong"
    if risk == "medium" or network_required:
        return "simple"
    return "direct"


def _risk_level(value: Any, text: str) -> str:
    declared = _choice(value, RISK_LEVELS, "")
    if declared:
        return declared
    if any(marker in text for marker in ("stripe live", "money", "payment", "deploy", "production", "secret", ".env", "credential")):
        return "critical"
    if any(marker in text for marker in ("install", "commit", "push", "merge", "external", "network")):
        return "high"
    if any(marker in text for marker in ("github", "web", "tool", "risk")):
        return "medium"
    return "low"


def _capability_connected(source: str, capability: str, value: Any) -> bool:
    if source in {"docs", "local_repo"} and value is None:
        return True
    if isinstance(value, dict):
        return bool(value.get(source) or value.get(capability))
    if isinstance(value, (list, tuple, set)):
        normalized = {str(item).lower() for item in value}
        return source in normalized or capability.lower() in normalized
    return bool(value) if source in {"docs", "local_repo"} else False


def _no_auto_actions(text: str) -> List[str]:
    return [reason for marker, reason in AUTO_SENSITIVE_ACTIONS.items() if marker in text]


def _approval_rank(level: str) -> int:
    try:
        return APPROVAL_LEVELS.index(level)
    except ValueError:
        return 0


def _choice(value: Any, allowed: Iterable[str], fallback: str) -> str:
    text = _normalized(value, fallback)
    return text if text in allowed else fallback


def _normalized(value: Any, fallback: str) -> str:
    text = " ".join(str(value or "").strip().split()).lower()
    return text or fallback


def _combined(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_combined(item) for item in value.values()).lower()
    if isinstance(value, (list, tuple, set)):
        return " ".join(_combined(item) for item in value).lower()
    return str(value or "").lower()
