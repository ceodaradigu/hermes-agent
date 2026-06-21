from __future__ import annotations

import hashlib
import math
import os
import re
import secrets
import webbrowser
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import quote_plus, urlparse
from uuid import uuid4

from jarvis.phase_10_hands_free_runtime_persona_api_router import (
    PHASE_10_EXACT_APPROVAL_PHRASE,
    Phase10HandsFreeRuntimePersonaApiRouter,
    normalize_spanish,
)


PHASE_11_SCHEMA_VERSION = "jarvis.phase_11_real_provider_controller_iphone_companion.v1"
PROVIDER_STATUS_SCHEMA_VERSION = "jarvis.phase_11.provider_status.v1"
MODEL_ROUTER_V2_SCHEMA_VERSION = "jarvis.phase_11.model_api_router_v2.v1"
APP_CONTROLLER_SCHEMA_VERSION = "jarvis.phase_11.local_controller_pilot.v1"
BROWSER_PILOT_SCHEMA_VERSION = "jarvis.phase_11.browser_navigation_pilot.v1"
APPROVAL_V3_SCHEMA_VERSION = "jarvis.phase_11.approval_v3.v1"
IPHONE_COMPANION_SCHEMA_VERSION = "jarvis.phase_11.iphone_companion.v1"
SHARED_STATE_SCHEMA_VERSION = "jarvis.phase_11.shared_state.v1"

DEFAULT_MONTHLY_BUDGET_EUR = 30.0
DEFAULT_APPROVAL_THRESHOLD_EUR = 1.0
MAX_PAIRING_TTL_SECONDS = 300
DEFAULT_PAIRING_TTL_SECONDS = 180
DEFAULT_APPROVAL_TTL_SECONDS = 180

WAKE_APPROVAL_REJECTIONS = {"jarvis", "hola jarvis"}
SUPPORTED_TASK_TYPES = {
    "simple_chat",
    "planning",
    "code",
    "browser_research",
    "summarization",
    "risky_operation_reasoning",
    "voice_response",
}
QUALITY_ORDER = {"standard": 1, "balanced": 2, "high": 3, "critical": 4}
RISK_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_at(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=max(1, int(seconds)))).isoformat()


def _parse_iso(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _expired(value: str) -> bool:
    parsed = _parse_iso(value)
    if parsed is None:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed <= datetime.now(timezone.utc)


def _hash_text(value: Any) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:16]


def _scope_fingerprint(scope: Sequence[str]) -> str:
    return _hash_text("|".join(sorted(_safe_text(item, limit=120) for item in scope)))


def _safe_text(value: Any, fallback: str = "", *, limit: int = 240) -> str:
    text = " ".join(str(value if value is not None else fallback).split())
    if not text:
        text = fallback
    text = _redact_secrets(text)
    return text[: max(1, int(limit))]


def _safe_list(values: Any, *, limit: int = 12) -> List[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    return [_safe_text(item, limit=120) for item in list(values)[:limit]]


def _redact_secrets(value: Any) -> str:
    text = str(value or "")
    patterns = [
        r"\bsk-[A-Za-z0-9_-]{8,}\b",
        r"\bsk-or-[A-Za-z0-9_-]{8,}\b",
        r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{12,}\b",
        r"\b(?:api[_-]?key|token|secret|password|authorization|bearer)\s*[:=]\s*['\"]?[^'\"\s,;]+",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    ]
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, "[redacted]", redacted, flags=re.IGNORECASE)
    return redacted


def _env_bool(name: str, default: bool = False, *, env: Optional[Mapping[str, str]] = None) -> bool:
    source = env if env is not None else os.environ
    raw = str(source.get(name, "")).strip().lower()
    if raw in {"1", "true", "yes", "on", "enabled"}:
        return True
    if raw in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _env_float(name: str, default: float, *, env: Optional[Mapping[str, str]] = None) -> float:
    source = env if env is not None else os.environ
    try:
        value = float(source.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if math.isfinite(value) else default


def _first_env(*names: str, env: Optional[Mapping[str, str]] = None) -> str:
    source = env if env is not None else os.environ
    for name in names:
        value = str(source.get(name, "")).strip()
        if value:
            return value
    return ""


def _cap(value: float, *, low: float = 0.0, high: float = 999999.0) -> float:
    return max(low, min(high, float(value)))


def _quality_at_least(actual: str, required: str) -> bool:
    return QUALITY_ORDER.get(actual, 0) >= QUALITY_ORDER.get(required, 0)


def _risk_at_least(actual: str, required: str) -> bool:
    return RISK_ORDER.get(actual, 0) >= RISK_ORDER.get(required, 0)


def _safe_url(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if not parsed.scheme:
        value = f"https://{value}"
        parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if parsed.username or parsed.password:
        return ""
    host = parsed.netloc.lower()
    if any(marker in host for marker in ("\n", "\r", "\t", "@")):
        return ""
    return value


def _looks_like_url(text: Any) -> bool:
    value = str(text or "").strip()
    return bool(re.match(r"^https?://", value, re.I) or re.match(r"^[a-z0-9.-]+\.[a-z]{2,}(?:/.*)?$", value, re.I))


def _search_url(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}"


def _default_opener(url: str) -> bool:
    return bool(webbrowser.open(url, new=1, autoraise=True))


@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    created_at: str
    surface: str
    actor: str = "David"
    risk_level: str = "low"
    action_id: str = ""
    channel: str = ""
    device_id_hash: str = ""
    result: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_11_SCHEMA_VERSION,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "created_at": self.created_at,
            "surface": self.surface,
            "actor": _safe_text(self.actor, limit=80),
            "risk_level": self.risk_level,
            "action_id": _safe_text(self.action_id, limit=120),
            "channel": _safe_text(self.channel, limit=80),
            "device_id_hash": self.device_id_hash,
            "result": _safe_text(self.result, limit=160),
            "metadata": _safe_metadata(self.metadata),
            "metadata_only": True,
        }


class Phase11AuditLog:
    def __init__(self, *, limit: int = 200) -> None:
        self.limit = max(20, int(limit))
        self._events: List[AuditEvent] = []

    def record(
        self,
        event_type: str,
        *,
        surface: str,
        actor: str = "David",
        risk_level: str = "low",
        action_id: str = "",
        channel: str = "",
        device_id: str = "",
        result: str = "",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        event = AuditEvent(
            event_id=f"phase11_audit_{uuid4()}",
            event_type=_safe_text(event_type, limit=100),
            created_at=_now_iso(),
            surface=_safe_text(surface, limit=100),
            actor=_safe_text(actor, limit=80),
            risk_level=risk_level if risk_level in RISK_ORDER else "low",
            action_id=_safe_text(action_id, limit=120),
            channel=_safe_text(channel, limit=80),
            device_id_hash=_hash_text(device_id) if device_id else "",
            result=_safe_text(result, limit=160),
            metadata=dict(metadata or {}),
        )
        self._events.append(event)
        if len(self._events) > self.limit:
            self._events = self._events[-self.limit :]
        return event.to_dict()

    def recent(self, limit: int = 25) -> List[Dict[str, Any]]:
        return [event.to_dict() for event in self._events[-max(1, int(limit)) :]]

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_11_SCHEMA_VERSION,
            "event_count": len(self._events),
            "recent": self.recent(10),
            "metadata_only": True,
            "contains_secret": False,
            "contains_raw_audio": False,
            "contains_camera_frame": False,
        }


def _safe_metadata(metadata: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in dict(metadata or {}).items():
        clean_key = _safe_text(key, limit=80)
        lower = clean_key.lower()
        if any(marker in lower for marker in ("password", "secret", "token", "api_key", "apikey", "authorization", "cookie")):
            safe[clean_key] = "[redacted]"
        elif isinstance(value, Mapping):
            safe[clean_key] = _safe_metadata(value)
        elif isinstance(value, (list, tuple, set)):
            safe[clean_key] = [_safe_text(item, limit=160) for item in list(value)[:20]]
        elif isinstance(value, (bool, int, float)) and not isinstance(value, bool):
            safe[clean_key] = value if math.isfinite(float(value)) else "unknown"
        elif isinstance(value, bool):
            safe[clean_key] = value
        else:
            safe[clean_key] = _safe_text(value, limit=220)
    return safe


class Phase11BudgetLedger:
    def __init__(
        self,
        *,
        monthly_budget_eur: float = DEFAULT_MONTHLY_BUDGET_EUR,
        spent_eur: float = 0.0,
        approval_threshold_eur: float = DEFAULT_APPROVAL_THRESHOLD_EUR,
    ) -> None:
        self.monthly_budget_eur = round(_cap(monthly_budget_eur, high=100000.0), 4)
        self.spent_eur = round(_cap(spent_eur, high=100000.0), 4)
        self.approval_threshold_eur = round(_cap(approval_threshold_eur, high=100000.0), 4)
        self._entries: List[Dict[str, Any]] = []

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "Phase11BudgetLedger":
        return cls(
            monthly_budget_eur=_env_float("JARVIS_API_MONTHLY_BUDGET_EUR", DEFAULT_MONTHLY_BUDGET_EUR, env=env),
            spent_eur=_env_float("JARVIS_API_SPEND_EUR", 0.0, env=env),
            approval_threshold_eur=_env_float("JARVIS_API_APPROVAL_THRESHOLD_EUR", DEFAULT_APPROVAL_THRESHOLD_EUR, env=env),
        )

    @property
    def remaining_eur(self) -> float:
        return round(max(0.0, self.monthly_budget_eur - self.spent_eur), 4)

    def would_exceed(self, amount_eur: float) -> bool:
        return round(float(amount_eur), 6) > self.remaining_eur

    def requires_approval_for(self, amount_eur: float, *, quality_required: str, risk_level: str = "low") -> bool:
        amount = max(0.0, float(amount_eur))
        if amount <= 0:
            return False
        return bool(
            amount >= self.approval_threshold_eur
            or amount > max(0.0, self.remaining_eur) * 0.25
            or self.remaining_eur < 5.0
            or quality_required == "critical"
            or _risk_at_least(risk_level, "high")
        )

    def record_metadata_only(self, *, provider: str, model: str, estimated_cost_eur: float, action_id: str) -> Dict[str, Any]:
        entry = {
            "entry_id": f"phase11_budget_{uuid4()}",
            "created_at": _now_iso(),
            "provider": _safe_text(provider, limit=80),
            "model": _safe_text(model, limit=140),
            "estimated_cost_eur": round(max(0.0, float(estimated_cost_eur)), 6),
            "action_id": _safe_text(action_id, limit=120),
            "metadata_only": True,
            "charged": False,
        }
        self._entries.append(entry)
        self._entries = self._entries[-100:]
        return dict(entry)

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": MODEL_ROUTER_V2_SCHEMA_VERSION,
            "currency": "EUR",
            "monthly_budget_eur": self.monthly_budget_eur,
            "spent_eur": round(self.spent_eur, 4),
            "remaining_eur": self.remaining_eur,
            "default_monthly_budget_eur": DEFAULT_MONTHLY_BUDGET_EUR,
            "approval_threshold_eur": self.approval_threshold_eur,
            "overspend_prevented": True,
            "ledger_metadata_only": True,
            "live_charges_recorded": False,
            "recent_entries": list(self._entries[-10:]),
        }


class Phase11ProviderRegistry:
    def __init__(self, *, budget: Phase11BudgetLedger, env: Optional[Mapping[str, str]] = None) -> None:
        self.budget = budget
        self.env = env if env is not None else os.environ
        self._last_errors: Dict[str, str] = {}

    def set_last_error(self, provider: str, error: Any) -> None:
        self._last_errors[_safe_text(provider, limit=80)] = _redact_secrets(error)

    def status(self) -> Dict[str, Any]:
        providers = self.providers()
        return {
            "schema_version": PROVIDER_STATUS_SCHEMA_VERSION,
            "providers": providers,
            "budget": self.budget.status(),
            "summary": {
                "openrouter_configured": providers["openrouter"]["configured"],
                "openrouter_enabled": providers["openrouter"]["enabled"],
                "local_ready": providers["local"]["ready"],
                "paid_calls_enabled": providers["openrouter"]["paid_calls_enabled"],
                "secrets_redacted": True,
                "keys_exposed": False,
            },
            "read_only": True,
            "metadata_only": True,
        }

    def providers(self) -> Dict[str, Dict[str, Any]]:
        openrouter_key = _first_env("OPENROUTER_API_KEY", "JARVIS_OPENROUTER_API_KEY", env=self.env)
        openrouter_configured = bool(openrouter_key)
        openrouter_enabled = openrouter_configured and _env_bool("JARVIS_OPENROUTER_ENABLED", True, env=self.env)
        openrouter_live = openrouter_enabled and _env_bool("JARVIS_OPENROUTER_LIVE_CALLS_ENABLED", False, env=self.env)
        local_endpoint = _first_env("JARVIS_LOCAL_MODEL_ENDPOINT", "OLLAMA_HOST", env=self.env)
        local_model = _first_env("JARVIS_LOCAL_MODEL", "OLLAMA_MODEL", env=self.env) or "local/default"
        local_configured = bool(local_endpoint or _first_env("JARVIS_LOCAL_MODEL", "OLLAMA_MODEL", env=self.env))
        local_enabled = _env_bool("JARVIS_LOCAL_PROVIDER_ENABLED", True, env=self.env)
        deterministic_local = _env_bool("JARVIS_ALLOW_DETERMINISTIC_LOCAL_FALLBACK", True, env=self.env)
        return {
            "local": {
                "provider": "local",
                "configured": local_configured,
                "enabled": local_enabled,
                "ready": bool(local_enabled and (local_configured or deterministic_local)),
                "disabled": not local_enabled,
                "missing": [] if local_configured else ["JARVIS_LOCAL_MODEL_ENDPOINT or OLLAMA_HOST"],
                "model": local_model,
                "capabilities": {
                    "simple_chat": True,
                    "summarization": True,
                    "voice_response": True,
                    "planning": bool(local_configured),
                    "code": bool(local_configured and _env_bool("JARVIS_LOCAL_CODE_MODEL_GOOD_ENOUGH", False, env=self.env)),
                    "browser_research": bool(local_configured and _env_bool("JARVIS_LOCAL_RESEARCH_MODEL_GOOD_ENOUGH", False, env=self.env)),
                    "risky_operation_reasoning": False,
                    "max_quality_tier": "balanced" if local_configured else "standard",
                },
                "cost_per_1k_tokens_eur": 0.0,
                "external_network": False,
                "credential_required": False,
                "last_error": _redact_secrets(self._last_errors.get("local", "")),
            },
            "openrouter": {
                "provider": "openrouter",
                "configured": openrouter_configured,
                "enabled": openrouter_enabled,
                "disabled": not openrouter_enabled,
                "ready": openrouter_enabled,
                "missing": [] if openrouter_configured else ["OPENROUTER_API_KEY"],
                "default_model": _first_env("JARVIS_OPENROUTER_DEFAULT_MODEL", env=self.env) or "anthropic/claude-sonnet-4.5",
                "quality_model": _first_env("JARVIS_OPENROUTER_QUALITY_MODEL", env=self.env) or "anthropic/claude-sonnet-4.5",
                "economy_model": _first_env("JARVIS_OPENROUTER_ECONOMY_MODEL", env=self.env) or "openai/gpt-4.1-mini",
                "credential_state": "configured_redacted" if openrouter_configured else "missing_OPENROUTER_API_KEY",
                "credential_value_exposed": False,
                "paid": True,
                "paid_calls_enabled": openrouter_live,
                "external_network": True,
                "capabilities": {
                    "simple_chat": True,
                    "planning": True,
                    "code": True,
                    "browser_research": True,
                    "summarization": True,
                    "voice_response": True,
                    "risky_operation_reasoning": True,
                    "max_quality_tier": "critical",
                },
                "budget_remaining_eur": self.budget.remaining_eur,
                "last_error": _redact_secrets(self._last_errors.get("openrouter", "")),
            },
            "openai_future": {
                "provider": "openai",
                "configured": bool(_first_env("OPENAI_API_KEY", env=self.env)),
                "enabled": False,
                "ready": False,
                "disabled": True,
                "missing": ["future_adapter_not_enabled"],
                "credential_state": "future_slot_redacted",
                "capabilities": {"future_provider_slot": True},
                "last_error": _redact_secrets(self._last_errors.get("openai", "")),
            },
            "anthropic_future": {
                "provider": "anthropic",
                "configured": bool(_first_env("ANTHROPIC_API_KEY", env=self.env)),
                "enabled": False,
                "ready": False,
                "disabled": True,
                "missing": ["future_adapter_not_enabled"],
                "credential_state": "future_slot_redacted",
                "capabilities": {"future_provider_slot": True},
                "last_error": _redact_secrets(self._last_errors.get("anthropic", "")),
            },
        }


class ModelApiRouterV2:
    def __init__(self, *, providers: Phase11ProviderRegistry, budget: Phase11BudgetLedger) -> None:
        self.providers = providers
        self.budget = budget

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": MODEL_ROUTER_V2_SCHEMA_VERSION,
            "state": {
                "mode": "model_api_router_v2_real_provider_wiring_no_live_paid_calls_by_default",
                "monthly_budget_eur": self.budget.monthly_budget_eur,
                "spent_eur": self.budget.spent_eur,
                "remaining_eur": self.budget.remaining_eur,
                "default_policy": "prefer_local_when_good_enough_preserve_quality_when_it_matters",
                "live_paid_calls_default": False,
                "external_call_performed": False,
            },
            "providers": self.providers.providers(),
            "task_profiles": _task_profiles_v2(),
            "safety": {
                "secrets_redacted": True,
                "tests_spend_money": False,
                "budget_overspend_prevented": True,
                "meaningful_cost_requires_approval": True,
                "cheap_quality_downgrade_rejected": True,
                "memory_grants_permission": False,
            },
            "read_only": True,
        }

    def classify_task(self, text: str) -> Dict[str, Any]:
        normalized = normalize_spanish(text)
        task_type = "simple_chat"
        if any(word in normalized for word in ("codigo", "code", "test", "pytest", "bug", "repo", "programa")):
            task_type = "code"
        elif any(word in normalized for word in ("busca", "internet", "web", "research", "investiga")):
            task_type = "browser_research"
        elif any(word in normalized for word in ("resume", "resumen", "summarize")):
            task_type = "summarization"
        elif any(word in normalized for word in ("plan", "estrategia", "roadmap", "arquitectura")):
            task_type = "planning"
        elif any(word in normalized for word in ("riesgo", "deploy", "produccion", "pago", "terminal", "borrar", "publica")):
            task_type = "risky_operation_reasoning"
        elif any(word in normalized for word in ("di", "habla", "voz", "responde corto")):
            task_type = "voice_response"
        profile = _task_profiles_v2()[task_type]
        return {
            "schema_version": MODEL_ROUTER_V2_SCHEMA_VERSION,
            "task_type": task_type,
            "quality_required": profile["quality_tier"],
            "reason": profile["reason"],
            "normalized_text_omitted": True,
            "external_call_performed": False,
        }

    def decide(
        self,
        *,
        task_type: str = "simple_chat",
        quality_required: str = "balanced",
        estimated_input_tokens: int = 1200,
        estimated_output_tokens: int = 700,
        user_preference: str = "auto",
        max_cost_eur: Optional[float] = None,
        allow_quality_downgrade: bool = False,
    ) -> Dict[str, Any]:
        task_type = task_type if task_type in SUPPORTED_TASK_TYPES else "simple_chat"
        quality_required = quality_required if quality_required in QUALITY_ORDER else _task_profiles_v2()[task_type]["quality_tier"]
        profile = _task_profiles_v2()[task_type]
        if QUALITY_ORDER[profile["quality_tier"]] > QUALITY_ORDER[quality_required]:
            quality_required = profile["quality_tier"]
        provider_status = self.providers.providers()
        local = provider_status["local"]
        openrouter = provider_status["openrouter"]
        tokens = max(0, int(estimated_input_tokens)) + max(0, int(estimated_output_tokens))
        paid_estimate = _estimate_openrouter_cost(task_type, quality_required, tokens)
        remaining = self.budget.remaining_eur
        local_good_enough = bool(local["ready"] and _local_good_enough(local, task_type, quality_required))
        paid_needed = not local_good_enough or quality_required in {"high", "critical"} or profile["preferred_provider"] == "openrouter"
        cheap_requested = user_preference in {"cheap", "cheapest", "economy"}
        rejected_downgrades: List[str] = []
        selected_provider = "local"
        selected_model = str(local["model"])
        quality_tier = "standard" if not local.get("configured") else str(local["capabilities"].get("max_quality_tier", "balanced"))
        reason = "Local is good enough for this task and preserves the budget."
        fallback = "openrouter" if openrouter["ready"] else "none"
        estimated_cost = 0.0
        blocked_reason = ""
        quality_downgrade_rejected = False

        if cheap_requested and paid_needed and not allow_quality_downgrade:
            rejected_downgrades.append("cheap_or_local_downgrade_rejected_because_quality_required")
            quality_downgrade_rejected = True

        if paid_needed:
            if openrouter["ready"] and paid_estimate <= remaining:
                selected_provider = "openrouter"
                selected_model = _select_openrouter_model(openrouter, quality_required, cheap_requested and not quality_downgrade_rejected)
                quality_tier = quality_required
                fallback = "local" if local["ready"] else "none"
                estimated_cost = paid_estimate
                reason = "Quality matters here; OpenRouter is configured, enabled and inside the monthly budget."
            elif local_good_enough and allow_quality_downgrade:
                selected_provider = "local"
                selected_model = str(local["model"])
                quality_tier = str(local["capabilities"].get("max_quality_tier", "balanced"))
                reason = "OpenRouter is unavailable or over budget; local fallback is allowed for this request."
                fallback = "none"
            else:
                selected_provider = "none"
                selected_model = ""
                quality_tier = quality_required
                blocked_reason = "openrouter_missing_disabled_or_budget_exceeded"
                if not openrouter["configured"]:
                    blocked_reason = "missing_OPENROUTER_API_KEY"
                elif not openrouter["enabled"]:
                    blocked_reason = "openrouter_disabled"
                elif paid_estimate > remaining:
                    blocked_reason = "budget_exceeded"
                reason = "I will not downgrade blindly: this task needs higher quality than the safe local fallback can provide."
                fallback = "local_prepare_only" if local["ready"] else "none"

        if max_cost_eur is not None and estimated_cost > float(max_cost_eur):
            blocked_reason = "per_request_cost_limit_exceeded"
            selected_provider = "none"
            selected_model = ""
            reason = "Estimated provider cost exceeds the request cost cap."

        requires_approval = bool(
            selected_provider == "openrouter"
            and self.budget.requires_approval_for(estimated_cost, quality_required=quality_required, risk_level=profile["risk_level"])
        )
        budget_entry = None
        if selected_provider == "openrouter":
            budget_entry = self.budget.record_metadata_only(
                provider=selected_provider,
                model=selected_model,
                estimated_cost_eur=estimated_cost,
                action_id=f"model_route_{uuid4()}",
            )
        return {
            "schema_version": MODEL_ROUTER_V2_SCHEMA_VERSION,
            "task_type": task_type,
            "selected_provider": selected_provider,
            "selected_model": selected_model,
            "selected_profile": profile["profile_id"],
            "reason": reason,
            "why": reason,
            "quality_tier": quality_tier,
            "quality_required": quality_required,
            "estimated_cost_eur": round(estimated_cost, 6),
            "requires_approval": requires_approval,
            "approval_reason": "cost_or_risk_readback_required" if requires_approval else "",
            "fallback": fallback,
            "fallback_provider": fallback,
            "budget_remaining_eur": remaining,
            "monthly_budget_eur": self.budget.monthly_budget_eur,
            "budget_would_exceed": bool(paid_estimate > remaining),
            "blocked_reason": blocked_reason,
            "quality_downgrade_rejected": quality_downgrade_rejected,
            "rejected_downgrades": rejected_downgrades,
            "local_good_enough": local_good_enough,
            "provider_status": {
                "local_ready": local["ready"],
                "openrouter_configured": openrouter["configured"],
                "openrouter_enabled": openrouter["enabled"],
                "paid_calls_enabled": openrouter["paid_calls_enabled"],
            },
            "budget_ledger_entry": budget_entry,
            "external_call_performed": False,
            "provider_keys_exposed": False,
            "read_only": True,
        }


def _task_profiles_v2() -> Dict[str, Dict[str, Any]]:
    return {
        "simple_chat": {
            "profile_id": "local_simple_chat",
            "preferred_provider": "local",
            "quality_tier": "standard",
            "risk_level": "low",
            "reason": "Simple conversational work should stay local when possible.",
            "rate_eur_per_1k": 0.0015,
        },
        "planning": {
            "profile_id": "planning_high_quality",
            "preferred_provider": "openrouter",
            "quality_tier": "high",
            "risk_level": "medium",
            "reason": "Planning quality matters; use paid model only if configured and budgeted.",
            "rate_eur_per_1k": 0.003,
        },
        "code": {
            "profile_id": "code_high_quality",
            "preferred_provider": "openrouter",
            "quality_tier": "high",
            "risk_level": "medium",
            "reason": "Coding benefits from higher-quality reasoning; do not downgrade blindly.",
            "rate_eur_per_1k": 0.004,
        },
        "browser_research": {
            "profile_id": "browser_research_high_quality",
            "preferred_provider": "openrouter",
            "quality_tier": "high",
            "risk_level": "medium",
            "reason": "Research needs reliable synthesis and citations; paid model may be justified.",
            "rate_eur_per_1k": 0.004,
        },
        "summarization": {
            "profile_id": "local_summarization",
            "preferred_provider": "local",
            "quality_tier": "standard",
            "risk_level": "low",
            "reason": "Summarization is usually safe to keep local.",
            "rate_eur_per_1k": 0.002,
        },
        "risky_operation_reasoning": {
            "profile_id": "critical_risk_reasoning",
            "preferred_provider": "openrouter",
            "quality_tier": "critical",
            "risk_level": "high",
            "reason": "Risky operations need top-quality reasoning and approval readback.",
            "rate_eur_per_1k": 0.006,
        },
        "voice_response": {
            "profile_id": "local_voice_response",
            "preferred_provider": "local",
            "quality_tier": "standard",
            "risk_level": "low",
            "reason": "Short spoken responses should stay local/free by default.",
            "rate_eur_per_1k": 0.001,
        },
    }


def _local_good_enough(local: Mapping[str, Any], task_type: str, quality_required: str) -> bool:
    capabilities = local.get("capabilities", {}) if isinstance(local.get("capabilities"), Mapping) else {}
    if not bool(local.get("ready")) or not bool(capabilities.get(task_type, False)):
        return False
    return _quality_at_least(str(capabilities.get("max_quality_tier", "standard")), quality_required)


def _estimate_openrouter_cost(task_type: str, quality_required: str, tokens: int) -> float:
    profile = _task_profiles_v2()[task_type]
    multiplier = 1.5 if quality_required == "critical" else 1.15 if quality_required == "high" else 1.0
    return round(max(0, tokens) / 1000.0 * float(profile["rate_eur_per_1k"]) * multiplier, 6)


def _select_openrouter_model(openrouter: Mapping[str, Any], quality_required: str, cheap_allowed: bool) -> str:
    if cheap_allowed and quality_required in {"standard", "balanced"}:
        return str(openrouter.get("economy_model") or openrouter.get("default_model") or "openrouter/auto")
    if quality_required in {"high", "critical"}:
        return str(openrouter.get("quality_model") or openrouter.get("default_model") or "openrouter/auto")
    return str(openrouter.get("default_model") or "openrouter/auto")


class SafeOpenRouterAdapter:
    """Small OpenRouter adapter with explicit paid-call gates.

    No production route calls this directly. Tests can inject ``http_post`` and
    verify that authorization, budget and key redaction are enforced without
    touching the real network.
    """

    def __init__(
        self,
        *,
        providers: Phase11ProviderRegistry,
        budget: Phase11BudgetLedger,
        http_post: Optional[Callable[..., Any]] = None,
        timeout_seconds: int = 20,
    ) -> None:
        self.providers = providers
        self.budget = budget
        self.http_post = http_post
        self.timeout_seconds = max(1, int(timeout_seconds))

    def chat_completion(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        estimated_cost_eur: float,
        approval_confirmed: bool = False,
        allow_paid_call: bool = False,
    ) -> Dict[str, Any]:
        provider = self.providers.providers()["openrouter"]
        if not provider["configured"]:
            return self._blocked("missing_OPENROUTER_API_KEY")
        if not provider["enabled"]:
            return self._blocked("openrouter_disabled")
        if not provider["paid_calls_enabled"] or not allow_paid_call:
            return self._blocked("live_paid_calls_disabled_by_default")
        if self.budget.would_exceed(estimated_cost_eur):
            return self._blocked("budget_exceeded")
        if self.budget.requires_approval_for(estimated_cost_eur, quality_required="high") and not approval_confirmed:
            return self._blocked("approval_required")
        if self.http_post is None:
            return self._blocked("http_adapter_not_injected")
        key = _first_env("OPENROUTER_API_KEY", "JARVIS_OPENROUTER_API_KEY", env=self.providers.env)
        try:
            response = self.http_post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "messages": list(messages)},
                timeout=self.timeout_seconds,
            )
        except Exception as exc:  # pragma: no cover - defensive redaction path
            error = _redact_secrets(exc)
            self.providers.set_last_error("openrouter", error)
            return {"status": "error", "error": error, "provider_key_exposed": False}
        return {
            "status": "ok",
            "response": response,
            "external_call_performed": True,
            "provider_key_exposed": False,
        }

    def _blocked(self, reason: str) -> Dict[str, Any]:
        return {
            "status": "blocked",
            "reason": reason,
            "external_call_performed": False,
            "provider_key_exposed": False,
        }


@dataclass
class ApprovalV3Record:
    approval_id: str
    action_id: str
    scope: List[str]
    scope_fingerprint: str
    action_summary: str
    risk_level: str
    approval_level: str
    cost_summary: str
    change_summary: str
    rollback_or_stop_plan: str
    created_at: str
    expires_at: str
    channel: str = "desktop"
    device_id_hash: str = ""
    required_phrase: str = PHASE_10_EXACT_APPROVAL_PHRASE
    status: str = "pending"
    consumed: bool = False
    audit_events: List[Dict[str, Any]] = field(default_factory=list)

    def readback_text(self) -> str:
        return (
            f"Voy a preparar: {self.action_summary}. "
            f"Riesgo: {self.risk_level}. Coste: {self.cost_summary}. "
            f"Alcance: {', '.join(self.scope) if self.scope else 'accion actual'}. "
            f"Puede cambiar: {self.change_summary}. "
            f"Parada/rollback: {self.rollback_or_stop_plan}. "
            f"Para aprobar, di o escribe exactamente: {self.required_phrase}."
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": APPROVAL_V3_SCHEMA_VERSION,
            "approval_id": self.approval_id,
            "action_id": self.action_id,
            "scope": list(self.scope),
            "scope_fingerprint": self.scope_fingerprint,
            "action_summary": self.action_summary,
            "risk_level": self.risk_level,
            "approval_level": self.approval_level,
            "cost_summary": self.cost_summary,
            "change_summary": self.change_summary,
            "rollback_or_stop_plan": self.rollback_or_stop_plan,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "channel": self.channel,
            "device_id_hash": self.device_id_hash,
            "required_phrase": self.required_phrase,
            "status": self.status,
            "consumed": self.consumed,
            "readback_text": self.readback_text(),
            "audit_events": list(self.audit_events),
            "wake_phrase_can_approve": False,
            "utron_can_bypass_approvals": False,
            "memory_grants_permission": False,
            "metadata_only": True,
        }


class ApprovalV3Manager:
    def __init__(self, *, audit: Phase11AuditLog, trusted_device_checker: Optional[Callable[[str], bool]] = None) -> None:
        self.audit = audit
        self.trusted_device_checker = trusted_device_checker or (lambda _device_id: False)
        self._pending: Dict[str, ApprovalV3Record] = {}

    def status(self) -> Dict[str, Any]:
        self._expire_old()
        pending = [record.to_dict() for record in self._pending.values() if record.status == "pending"]
        return {
            "schema_version": APPROVAL_V3_SCHEMA_VERSION,
            "state": {
                "pending_count": len(pending),
                "required_phrase": PHASE_10_EXACT_APPROVAL_PHRASE,
                "text_voice_mobile_parity": True,
                "mobile_requires_pairing": True,
                "expiry_required": True,
                "anti_replay": True,
            },
            "pending": pending,
            "safety": {
                "wake_phrase_can_approve": False,
                "utron_can_bypass_approvals": False,
                "memory_grants_permission": False,
                "unauthenticated_mobile_approval_allowed": False,
            },
            "read_only": True,
        }

    def start(
        self,
        *,
        action_summary: str,
        risk_level: str = "high",
        scope: Optional[List[str]] = None,
        action_id: Optional[str] = None,
        cost_summary: str = "0 EUR estimados",
        change_summary: str = "puede tocar estado local o externo",
        rollback_or_stop_plan: str = "parar antes de ejecutar; rollback especifico si aplica",
        channel: str = "desktop",
        device_id: str = "",
        ttl_seconds: int = DEFAULT_APPROVAL_TTL_SECONDS,
    ) -> Dict[str, Any]:
        clean_scope = _safe_list(scope or ["current_action"], limit=12)
        risk = risk_level if risk_level in RISK_ORDER else "high"
        approval_level = "strong" if _risk_at_least(risk, "high") else "normal" if risk == "medium" else "direct"
        record = ApprovalV3Record(
            approval_id=f"phase11_approval_{uuid4()}",
            action_id=_safe_text(action_id or f"phase11_action_{uuid4()}", limit=120),
            scope=clean_scope,
            scope_fingerprint=_scope_fingerprint(clean_scope),
            action_summary=_safe_text(action_summary or "accion sin nombre", limit=220),
            risk_level=risk,
            approval_level=approval_level,
            cost_summary=_safe_text(cost_summary, limit=180),
            change_summary=_safe_text(change_summary, limit=220),
            rollback_or_stop_plan=_safe_text(rollback_or_stop_plan, limit=220),
            created_at=_now_iso(),
            expires_at=_expires_at(min(max(30, int(ttl_seconds or DEFAULT_APPROVAL_TTL_SECONDS)), 900)),
            channel=_safe_text(channel, limit=80),
            device_id_hash=_hash_text(device_id) if device_id else "",
        )
        audit = self.audit.record(
            "approval_v3_started",
            surface="approval_v3",
            risk_level=risk,
            action_id=record.action_id,
            channel=channel,
            device_id=device_id,
            result="pending",
            metadata={"scope_fingerprint": record.scope_fingerprint, "approval_id": record.approval_id},
        )
        record.audit_events.append(audit)
        self._pending[record.approval_id] = record
        return record.to_dict()

    def confirm(
        self,
        *,
        approval_id: str,
        action_id: str,
        scope: Optional[List[str]] = None,
        phrase: str = "",
        channel: str = "text",
        device_id: str = "",
        active_trusted_session: bool = False,
        readback_confirmed: bool = True,
    ) -> Dict[str, Any]:
        self._expire_old()
        record = self._pending.get(str(approval_id or ""))
        if record is None:
            return self._reject_empty("approval_not_found")
        normalized_phrase = normalize_spanish(phrase)
        clean_scope = _safe_list(scope or record.scope, limit=12)
        reason = ""
        if record.status != "pending" or record.consumed:
            reason = "phrase_replay_rejected"
        elif _expired(record.expires_at):
            record.status = "expired"
            reason = "approval_expired"
        elif action_id != record.action_id:
            reason = "action_id_mismatch"
        elif _scope_fingerprint(clean_scope) != record.scope_fingerprint:
            reason = "scope_mismatch"
        elif normalized_phrase in WAKE_APPROVAL_REJECTIONS:
            reason = "wake_phrase_never_approves"
        elif normalized_phrase != PHASE_10_EXACT_APPROVAL_PHRASE:
            reason = "exact_phrase_required"
        elif channel == "voice" and not active_trusted_session:
            reason = "voice_requires_active_trusted_session"
        elif channel in {"mobile", "iphone", "iphone_pwa"} and not self.trusted_device_checker(device_id):
            reason = "mobile_device_not_paired_or_trusted"
        elif not readback_confirmed:
            reason = "readback_required"
        if reason:
            audit = self.audit.record(
                "approval_v3_rejected",
                surface="approval_v3",
                risk_level=record.risk_level,
                action_id=record.action_id,
                channel=channel,
                device_id=device_id,
                result=reason,
                metadata={"approval_id": record.approval_id, "scope_fingerprint": _scope_fingerprint(clean_scope)},
            )
            record.audit_events.append(audit)
            return {**record.to_dict(), "approved": False, "status": "rejected", "reason": reason, "would_execute": False}
        record.status = "approved"
        record.consumed = True
        audit = self.audit.record(
            "approval_v3_approved",
            surface="approval_v3",
            risk_level=record.risk_level,
            action_id=record.action_id,
            channel=channel,
            device_id=device_id,
            result="approved",
            metadata={"approval_id": record.approval_id, "scope_fingerprint": record.scope_fingerprint},
        )
        record.audit_events.append(audit)
        return {**record.to_dict(), "approved": True, "status": "approved", "would_execute": False, "executed": False}

    def _expire_old(self) -> None:
        for record in self._pending.values():
            if record.status == "pending" and _expired(record.expires_at):
                record.status = "expired"

    def _reject_empty(self, reason: str) -> Dict[str, Any]:
        return {
            "schema_version": APPROVAL_V3_SCHEMA_VERSION,
            "approved": False,
            "status": "rejected",
            "reason": reason,
            "would_execute": False,
            "executed": False,
            "wake_phrase_can_approve": False,
        }


@dataclass
class PairedIPhone:
    device_id: str
    display_name: str
    public_identifier_hash: str
    paired_at: str
    expires_at: str
    revoked: bool = False
    scope: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "display_name": self.display_name,
            "public_identifier_hash": self.public_identifier_hash,
            "paired_at": self.paired_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "trusted": not self.revoked and not _expired(self.expires_at),
            "scope": list(self.scope),
            "capabilities": {
                "can_read_same_jarvis_state": True,
                "can_send_text_commands": True,
                "can_approve_bound_actions": True,
                "can_execute": False,
                "can_call_hermes_directly": False,
                "can_use_generic_shell": False,
            },
            "metadata_only": True,
        }


class IPhonePairingManager:
    def __init__(self, *, audit: Phase11AuditLog) -> None:
        self.audit = audit
        self._challenges: Dict[str, Dict[str, Any]] = {}
        self._devices: Dict[str, PairedIPhone] = {}

    def status(self) -> Dict[str, Any]:
        self._expire_challenges()
        devices = [device.to_dict() for device in self._devices.values()]
        trusted = [device for device in devices if device["trusted"]]
        return {
            "schema_version": IPHONE_COMPANION_SCHEMA_VERSION,
            "pairing_required": True,
            "pairing_ttl_seconds": DEFAULT_PAIRING_TTL_SECONDS,
            "pending_pairing_count": len(self._challenges),
            "paired_device_count": len(devices),
            "trusted_device_count": len(trusted),
            "revocation_supported": True,
            "devices": devices,
            "safety": {
                "public_exposure_default": False,
                "unauthenticated_control_allowed": False,
                "mobile_direct_execution_allowed": False,
                "mobile_direct_hermes_allowed": False,
                "approval_bound_to_action_scope_channel_device": True,
            },
            "metadata_only": True,
        }

    def start_pairing(
        self,
        *,
        display_name: str = "David iPhone",
        public_identifier: str = "iphone-safari",
        ttl_seconds: int = DEFAULT_PAIRING_TTL_SECONDS,
    ) -> Dict[str, Any]:
        ttl = min(max(30, int(ttl_seconds or DEFAULT_PAIRING_TTL_SECONDS)), MAX_PAIRING_TTL_SECONDS)
        challenge_id = f"iphone_pair_{uuid4()}"
        code = f"{secrets.randbelow(1000000):06d}"
        nonce = secrets.token_urlsafe(12)
        scope = ["read_state", "send_text", "approval_readback", "approve_bound_action", "deny", "utron_toggle"]
        self._challenges[challenge_id] = {
            "challenge_id": challenge_id,
            "code_hash": _hash_text(code),
            "nonce_hash": _hash_text(nonce),
            "display_name": _safe_text(display_name or "David iPhone", limit=80),
            "public_identifier_hash": _hash_text(public_identifier),
            "created_at": _now_iso(),
            "expires_at": _expires_at(ttl),
            "scope": scope,
            "used": False,
        }
        audit = self.audit.record(
            "iphone_pairing_started",
            surface="iphone_pairing",
            risk_level="medium",
            channel="iphone_pwa",
            result="pending",
            metadata={"challenge_id": challenge_id, "ttl_seconds": ttl, "scope": scope},
        )
        return {
            "schema_version": IPHONE_COMPANION_SCHEMA_VERSION,
            "pairing_status": "pending",
            "challenge_id": challenge_id,
            "pairing_code": code,
            "nonce": nonce,
            "expires_at": self._challenges[challenge_id]["expires_at"],
            "qr_payload": f"jarvis-iphone://pair?challenge_id={challenge_id}&nonce={nonce}",
            "scope": scope,
            "audit_id": audit["event_id"],
            "metadata_only": True,
            "remote_execution_allowed": False,
            "direct_hermes_allowed": False,
        }

    def verify_pairing(
        self,
        *,
        challenge_id: str,
        pairing_code: str,
        nonce: str,
        public_identifier: str = "iphone-safari",
        display_name: str = "David iPhone",
    ) -> Dict[str, Any]:
        self._expire_challenges()
        challenge = self._challenges.get(str(challenge_id or ""))
        reason = ""
        if not challenge:
            reason = "pairing_not_found_or_expired"
        elif challenge.get("used"):
            reason = "pairing_replay_rejected"
        elif _hash_text(pairing_code) != challenge.get("code_hash"):
            reason = "pairing_code_mismatch"
        elif _hash_text(nonce) != challenge.get("nonce_hash"):
            reason = "nonce_mismatch"
        elif _hash_text(public_identifier) != challenge.get("public_identifier_hash"):
            reason = "device_identifier_mismatch"
        if reason:
            audit = self.audit.record(
                "iphone_pairing_failed",
                surface="iphone_pairing",
                risk_level="medium",
                channel="iphone_pwa",
                result=reason,
                metadata={"challenge_id": _safe_text(challenge_id, limit=120)},
            )
            return {
                "schema_version": IPHONE_COMPANION_SCHEMA_VERSION,
                "pairing_status": "rejected",
                "reason": reason,
                "audit_id": audit["event_id"],
                "remote_execution_allowed": False,
                "direct_hermes_allowed": False,
            }
        challenge["used"] = True
        device = PairedIPhone(
            device_id=f"iphone_{_hash_text(public_identifier + challenge_id)}",
            display_name=_safe_text(display_name or challenge["display_name"], limit=80),
            public_identifier_hash=challenge["public_identifier_hash"],
            paired_at=_now_iso(),
            expires_at=_expires_at(7 * 24 * 60 * 60),
            scope=list(challenge.get("scope") or []),
        )
        self._devices[device.device_id] = device
        self._challenges.pop(challenge_id, None)
        audit = self.audit.record(
            "iphone_pairing_verified",
            surface="iphone_pairing",
            risk_level="medium",
            channel="iphone_pwa",
            device_id=device.device_id,
            result="trusted_device_bound",
            metadata={"challenge_id": challenge_id, "scope": device.scope},
        )
        return {
            "schema_version": IPHONE_COMPANION_SCHEMA_VERSION,
            "pairing_status": "trusted_device_bound",
            "device": device.to_dict(),
            "audit_id": audit["event_id"],
            "remote_execution_allowed": False,
            "direct_hermes_allowed": False,
            "metadata_only": True,
        }

    def revoke(self, *, device_id: str, actor: str = "David", reason: str = "operator revoke") -> Dict[str, Any]:
        device = self._devices.get(str(device_id or ""))
        if device:
            device.revoked = True
        audit = self.audit.record(
            "iphone_device_revoked",
            surface="iphone_pairing",
            risk_level="medium",
            channel="iphone_pwa",
            device_id=device_id,
            actor=actor,
            result="revoked" if device else "device_not_found",
            metadata={"reason": reason},
        )
        return {
            "schema_version": IPHONE_COMPANION_SCHEMA_VERSION,
            "revoked": bool(device),
            "device": device.to_dict() if device else None,
            "audit_id": audit["event_id"],
            "remote_execution_allowed": False,
            "direct_hermes_allowed": False,
        }

    def is_trusted(self, device_id: str) -> bool:
        device = self._devices.get(str(device_id or ""))
        return bool(device and not device.revoked and not _expired(device.expires_at))

    def _expire_challenges(self) -> None:
        expired = [challenge_id for challenge_id, challenge in self._challenges.items() if _expired(challenge["expires_at"])]
        for challenge_id in expired:
            self._challenges.pop(challenge_id, None)


@dataclass
class KnownApp:
    app_id: str
    display_name: str
    aliases: Tuple[str, ...]
    risk_level: str = "low"
    requires_approval: bool = False
    real_launch_supported: bool = False
    route: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "app_id": self.app_id,
            "display_name": self.display_name,
            "aliases": list(self.aliases),
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "real_launch_supported": self.real_launch_supported,
            "route": self.route,
        }


class LocalControllerPilot:
    def __init__(
        self,
        *,
        audit: Phase11AuditLog,
        opener: Optional[Callable[[str], bool]] = None,
        jarvis_url: str = "http://127.0.0.1:8000/jarvis",
    ) -> None:
        self.audit = audit
        self.opener = opener or _default_opener
        self.jarvis_url = _safe_url(jarvis_url) or "http://127.0.0.1:8000/jarvis"
        self._candidates: Dict[str, Dict[str, Any]] = {}
        self._apps = _known_apps()

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": APP_CONTROLLER_SCHEMA_VERSION,
            "state": {
                "mode": "bounded_real_local_controller_pilot",
                "open_jarvis_real_supported": True,
                "known_app_count": len(self._apps),
                "arbitrary_shell_allowed": False,
                "raw_command_accepted": False,
                "frontend_direct_execution_allowed": False,
            },
            "known_apps": {app_id: app.to_dict() for app_id, app in self._apps.items()},
            "jarvis_url": self.jarvis_url,
            "real_vs_readiness": {
                "real": ["open /jarvis in the system browser through a governed backend call", "open safe http/https URLs through the browser pilot"],
                "readiness": ["Cursor/VS Code/Terminal/File Explorer/WhatsApp/Spotify launch candidates are prepared but not started by default"],
            },
            "security": {
                "no_generic_shell": True,
                "known_apps_only": True,
                "audit_required": True,
                "approval_required_for_sensitive_apps": True,
                "unknown_app_message_es": "No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida.",
            },
            "pending_candidate_count": len(self._candidates),
            "metadata_only": True,
        }

    def prepare_launch(self, *, app_name: str, actor: str = "David", channel: str = "desktop") -> Dict[str, Any]:
        normalized = normalize_spanish(app_name)
        app = self._resolve(normalized)
        if app is None:
            audit = self.audit.record(
                "local_app_launch_unknown",
                surface="local_controller",
                actor=actor,
                channel=channel,
                result="unknown_app",
                metadata={"requested_app_hash": _hash_text(app_name)},
            )
            return {
                "schema_version": APP_CONTROLLER_SCHEMA_VERSION,
                "candidate_id": "",
                "status": "unknown_app",
                "known": False,
                "spanish_response": "No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida.",
                "would_execute": False,
                "executed": False,
                "freeform_shell_allowed": False,
                "raw_command_accepted": False,
                "audit_id": audit["event_id"],
            }
        candidate_id = f"launch_{uuid4()}"
        action_id = f"local_launch_{app.app_id}_{_hash_text(candidate_id)}"
        candidate = {
            "schema_version": APP_CONTROLLER_SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "action_id": action_id,
            "status": "prepared_governed_launch_candidate",
            "known": True,
            "app": app.to_dict(),
            "risk_level": app.risk_level,
            "requires_approval": app.requires_approval,
            "requires_exact_phrase": app.requires_approval,
            "required_phrase": PHASE_10_EXACT_APPROVAL_PHRASE if app.requires_approval else "",
            "real_launch_supported_now": app.real_launch_supported,
            "execution_path": "phase11_local_controller_pilot_known_app_only",
            "would_execute": False,
            "executed": False,
            "freeform_shell_allowed": False,
            "raw_command_accepted": False,
            "frontend_direct_execution_allowed": False,
            "route": app.route or self.jarvis_url if app.app_id == "chrome" else app.route,
        }
        self._candidates[candidate_id] = candidate
        audit = self.audit.record(
            "local_app_launch_prepared",
            surface="local_controller",
            actor=actor,
            risk_level=app.risk_level,
            action_id=action_id,
            channel=channel,
            result="prepared",
            metadata={"app_id": app.app_id, "real_launch_supported_now": app.real_launch_supported},
        )
        return {
            **candidate,
            "audit_id": audit["event_id"],
            "spanish_response": (
                f"Puedo abrir {app.display_name} ahora por el controlador local gobernado."
                if app.real_launch_supported
                else f"Puedo preparar {app.display_name}; aún no lo arrancaré hasta tener launcher nativo seguro."
            ),
        }

    def launch(self, *, candidate_id: str, actor: str = "David", approval_id: str = "", trusted_session: bool = False) -> Dict[str, Any]:
        candidate = self._candidates.get(str(candidate_id or ""))
        if not candidate:
            return {
                "schema_version": APP_CONTROLLER_SCHEMA_VERSION,
                "status": "blocked",
                "reason": "candidate_not_found",
                "executed": False,
                "freeform_shell_allowed": False,
            }
        app = candidate["app"]
        if candidate.get("requires_approval") and not approval_id and not trusted_session:
            return {**candidate, "status": "approval_required", "executed": False, "reason": "approval_required_for_sensitive_app"}
        if not candidate.get("real_launch_supported_now"):
            audit = self.audit.record(
                "local_app_launch_readiness_only",
                surface="local_controller",
                actor=actor,
                risk_level=candidate["risk_level"],
                action_id=candidate["action_id"],
                result="readiness_only",
                metadata={"app_id": app.get("app_id")},
            )
            return {
                **candidate,
                "status": "readiness_only",
                "executed": False,
                "reason": "known_app_launch_not_wired_yet",
                "audit_id": audit["event_id"],
            }
        url = self.jarvis_url if app.get("app_id") == "chrome" else _safe_url(candidate.get("route"))
        try:
            opened = bool(self.opener(url))
            status = "executed" if opened else "failed"
            reason = "" if opened else "browser_opener_returned_false"
        except Exception as exc:  # pragma: no cover - defensive local platform path
            opened = False
            status = "failed"
            reason = _safe_text(exc, limit=160)
        audit = self.audit.record(
            "local_app_launch_attempted",
            surface="local_controller",
            actor=actor,
            risk_level=candidate["risk_level"],
            action_id=candidate["action_id"],
            result=status,
            metadata={"app_id": app.get("app_id"), "url_origin": _url_origin(url), "approval_id": approval_id},
        )
        candidate.update({"status": status, "executed": opened, "last_result": reason})
        return {**candidate, "did_open_browser": opened, "audit_id": audit["event_id"], "reason": reason}

    def _resolve(self, normalized: str) -> Optional[KnownApp]:
        for app in self._apps.values():
            if normalized == normalize_spanish(app.display_name) or normalized in app.aliases:
                return app
        if normalized in {"jarvis", "abre jarvis", "abre /jarvis"}:
            return self._apps["chrome"]
        return None


def _known_apps() -> Dict[str, KnownApp]:
    return {
        "chrome": KnownApp("chrome", "Chrome/browser", ("chrome", "google chrome", "navegador", "browser", "jarvis en chrome"), real_launch_supported=True, route="/jarvis"),
        "cursor": KnownApp("cursor", "Cursor", ("cursor",), risk_level="medium", requires_approval=True),
        "vscode": KnownApp("vscode", "VS Code", ("vs code", "visual studio code", "code"), risk_level="medium", requires_approval=True),
        "terminal": KnownApp("terminal", "Windows Terminal/Terminal/WSL", ("terminal", "consola", "wsl", "windows terminal"), risk_level="high", requires_approval=True),
        "file_explorer": KnownApp("file_explorer", "File Explorer", ("explorador", "explorador de archivos", "file explorer"), risk_level="medium", requires_approval=True),
        "whatsapp": KnownApp("whatsapp", "WhatsApp", ("whatsapp", "wasap"), risk_level="medium", requires_approval=True),
        "spotify": KnownApp("spotify", "Spotify", ("spotify", "musica"), risk_level="low"),
        "jarvis_project": KnownApp("jarvis_project", "JARVIS project folder", ("carpeta jarvis", "proyecto jarvis", "jarvis project folder"), risk_level="medium", requires_approval=True),
    }


class GovernedBrowserNavigationPilot:
    def __init__(self, *, audit: Phase11AuditLog, opener: Optional[Callable[[str], bool]] = None) -> None:
        self.audit = audit
        self.opener = opener or _default_opener
        self._candidates: Dict[str, Dict[str, Any]] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": BROWSER_PILOT_SCHEMA_VERSION,
            "state": {
                "mode": "governed_browser_navigation_pilot",
                "safe_url_open_real_supported": True,
                "search_open_real_supported": True,
                "form_fill_prepare_only": True,
                "page_summarize_readiness": True,
                "credential_entry_enabled": False,
            },
            "supported_intents": ["browser.open_url", "web.search", "page.summarize", "form.fill_preview", "message.prepare", "service.navigate"],
            "safety": {
                "no_form_submit_without_approval": True,
                "no_purchase_payment_publication_without_strong_approval": True,
                "credential_entry_allowed": False,
                "plain_text_password_storage": False,
                "login_manual_required": True,
                "hidden_browser_allowed": False,
                "audit_required": True,
            },
            "pending_candidate_count": len(self._candidates),
            "metadata_only": True,
        }

    def prepare(self, *, text: str, actor: str = "David", channel: str = "desktop") -> Dict[str, Any]:
        normalized = normalize_spanish(text)
        intent = "unknown"
        target_url = ""
        risk = "low"
        requires_approval = False
        strong = False
        unsupported_reason = ""
        if _looks_like_url(text):
            intent = "browser.open_url"
            target_url = _safe_url(text)
            if not target_url:
                unsupported_reason = "URL no segura o no soportada."
        elif any(word in normalized for word in ("busca", "buscar", "search", "googlea")):
            intent = "web.search"
            query = re.sub(r"\b(busca|buscar|search|googlea)\b", "", normalized).strip() or normalized
            target_url = _search_url(query)
        elif any(word in normalized for word in ("resume esta pagina", "resume la pagina", "resumeme la pagina", "summarize")):
            intent = "page.summarize"
            unsupported_reason = "Resumen de pagina abierta queda en readiness hasta tener contexto de pagina visible."
        elif any(word in normalized for word in ("rellena", "formulario", "fill form")):
            intent = "form.fill_preview"
            risk = "medium"
            requires_approval = True
        elif any(word in normalized for word in ("prepara mensaje", "escribe mensaje", "redacta mensaje", "whatsapp")):
            intent = "message.prepare"
            risk = "medium"
            requires_approval = True
        elif any(word in normalized for word in ("abre", "navega", "entra en", "ve a")):
            intent = "service.navigate"
            target_url = _safe_url(normalized.replace("abre", "").replace("navega", "").replace("entra en", "").replace("ve a", "").strip())
        if any(word in normalized for word in ("compra", "paga", "suscribete", "publica", "envia", "submit", "comprar")):
            risk = "critical"
            requires_approval = True
            strong = True
        if any(word in normalized for word in ("login", "contraseña", "password", "credencial", "cookie", "token")):
            risk = "high"
            requires_approval = True
            unsupported_reason = "El login debe hacerlo David manualmente o una futura boveda aprobada; no manejo credenciales en claro."
        candidate_id = f"browser_{uuid4()}"
        action_id = f"browser_{intent}_{_hash_text(candidate_id)}"
        real_supported = intent in {"browser.open_url", "web.search"} and bool(target_url) and not requires_approval
        candidate = {
            "schema_version": BROWSER_PILOT_SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "action_id": action_id,
            "intent": intent,
            "status": "prepared_governed_browser_candidate" if intent != "unknown" else "unsupported_or_ambiguous",
            "risk_level": risk,
            "requires_approval": requires_approval,
            "requires_strong_approval": strong,
            "requires_exact_phrase": requires_approval,
            "required_phrase": PHASE_10_EXACT_APPROVAL_PHRASE if requires_approval else "",
            "target_url_origin": _url_origin(target_url),
            "target_url_fingerprint": _hash_text(target_url) if target_url else "",
            "real_open_supported_now": real_supported,
            "preview_first": True,
            "unsupported_reason": unsupported_reason,
            "would_execute": False,
            "executed": False,
            "frontend_direct_execution_allowed": False,
            "safety": {
                "form_submit_allowed": False,
                "purchase_payment_publication_allowed": False,
                "credential_storage_allowed": False,
                "login_manual_required": bool("login" in unsupported_reason.lower()),
                "hidden_browser_allowed": False,
                "no_fake_navigation_claim": True,
            },
            "_target_url": target_url,
        }
        self._candidates[candidate_id] = candidate
        audit = self.audit.record(
            "browser_navigation_prepared",
            surface="browser_pilot",
            actor=actor,
            risk_level=risk,
            action_id=action_id,
            channel=channel,
            result=candidate["status"],
            metadata={"intent": intent, "url_origin": _url_origin(target_url), "real_open_supported_now": real_supported},
        )
        return {k: v for k, v in {**candidate, "audit_id": audit["event_id"], "spanish_response": _browser_spanish_response(intent, requires_approval, strong, unsupported_reason, real_supported)}.items() if not k.startswith("_")}

    def open_candidate(self, *, candidate_id: str, actor: str = "David", approval_id: str = "", trusted_session: bool = False) -> Dict[str, Any]:
        candidate = self._candidates.get(str(candidate_id or ""))
        if not candidate:
            return {"schema_version": BROWSER_PILOT_SCHEMA_VERSION, "status": "blocked", "reason": "candidate_not_found", "executed": False}
        if candidate.get("requires_approval") and not approval_id and not trusted_session:
            return {**_public_candidate(candidate), "status": "approval_required", "executed": False, "reason": "approval_required"}
        if not candidate.get("real_open_supported_now"):
            audit = self.audit.record(
                "browser_navigation_readiness_only",
                surface="browser_pilot",
                actor=actor,
                risk_level=candidate["risk_level"],
                action_id=candidate["action_id"],
                result="readiness_only",
                metadata={"intent": candidate["intent"]},
            )
            return {**_public_candidate(candidate), "status": "readiness_only", "executed": False, "audit_id": audit["event_id"], "reason": "browser_automation_beyond_open_url_is_readiness"}
        url = candidate.get("_target_url") or ""
        try:
            opened = bool(self.opener(str(url)))
            status = "executed" if opened else "failed"
            reason = "" if opened else "browser_opener_returned_false"
        except Exception as exc:  # pragma: no cover - defensive local platform path
            opened = False
            status = "failed"
            reason = _safe_text(exc, limit=160)
        audit = self.audit.record(
            "browser_navigation_attempted",
            surface="browser_pilot",
            actor=actor,
            risk_level=candidate["risk_level"],
            action_id=candidate["action_id"],
            result=status,
            metadata={"intent": candidate["intent"], "url_origin": _url_origin(url), "approval_id": approval_id},
        )
        candidate.update({"status": status, "executed": opened, "last_result": reason})
        return {**_public_candidate(candidate), "did_open_browser": opened, "audit_id": audit["event_id"], "reason": reason}


def _public_candidate(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in candidate.items() if not str(k).startswith("_")}


def _browser_spanish_response(intent: str, requires_approval: bool, strong: bool, unsupported_reason: str, real_supported: bool) -> str:
    if unsupported_reason:
        return unsupported_reason
    if intent == "unknown":
        return "No he podido clasificar esa navegacion. Puedo abrir URL, buscar, resumir pagina, preparar formulario o preparar mensaje."
    if strong:
        return "Preparare una vista previa. No enviare, comprare, pagare ni publicare nada sin aprobacion fuerte."
    if requires_approval:
        return "Preparare vista previa. No enviare ni tocare formularios sin aprobacion."
    if real_supported:
        return "Puedo abrirlo ahora en el navegador visible mediante el piloto gobernado."
    return "Puedo prepararlo; no fingire navegacion real hasta que un adaptador gobernado lo confirme."


def _url_origin(url: str) -> str:
    parsed = urlparse(str(url or ""))
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""


class SharedJarvisState:
    def __init__(
        self,
        *,
        phase10: Phase10HandsFreeRuntimePersonaApiRouter,
        providers: Phase11ProviderRegistry,
        budget: Phase11BudgetLedger,
        approvals: ApprovalV3Manager,
        pairing: IPhonePairingManager,
        audit: Phase11AuditLog,
    ) -> None:
        self.phase10 = phase10
        self.providers = providers
        self.budget = budget
        self.approvals = approvals
        self.pairing = pairing
        self.audit = audit
        self._conversation: List[Dict[str, Any]] = []

    def record_turn(
        self,
        *,
        conversation_id: str,
        user_text: str,
        assistant_text: str,
        channel: str,
        source: str,
        status: str,
    ) -> Dict[str, Any]:
        turn = {
            "turn_id": f"shared_turn_{uuid4()}",
            "created_at": _now_iso(),
            "conversation_id": _safe_text(conversation_id or "default", limit=120),
            "channel": _safe_text(channel, limit=80),
            "source": _safe_text(source, limit=80),
            "status": _safe_text(status, limit=40),
            "user_text": _safe_text(user_text, limit=800),
            "assistant_text": _safe_text(assistant_text, limit=1200),
            "persona_mode": self.phase10.persona.state.mode,
            "metadata_only": False,
        }
        self._conversation.append(turn)
        self._conversation = self._conversation[-50:]
        self.audit.record(
            "shared_conversation_turn_recorded",
            surface="shared_state",
            channel=channel,
            result=status,
            metadata={"conversation_id_hash": _hash_text(conversation_id), "source": source},
        )
        return dict(turn)

    def handle_iphone_command(self, *, text: str, device_id: str, conversation_id: str = "iphone") -> Dict[str, Any]:
        if not self.pairing.is_trusted(device_id):
            audit = self.audit.record(
                "iphone_command_rejected",
                surface="iphone_companion",
                channel="iphone_pwa",
                device_id=device_id,
                result="device_not_paired",
            )
            return {
                "schema_version": IPHONE_COMPANION_SCHEMA_VERSION,
                "status": "rejected",
                "reason": "iphone_device_not_paired_or_trusted",
                "audit_id": audit["event_id"],
                "would_execute": False,
                "executed": False,
            }
        phase10_result = self.phase10.handle_conversation_text(text)
        persona_response = phase10_result.get("persona", {}).get("response") or ""
        if persona_response:
            assistant_text = persona_response
            status = "normal"
        else:
            assistant_text = "Te leo desde el mismo JARVIS. Puedo conversar, preparar acciones gobernadas y pedir aprobacion si hay riesgo; no ejecuto nada directo desde el iPhone."
            status = "preview"
        turn = self.record_turn(
            conversation_id=conversation_id,
            user_text=text,
            assistant_text=assistant_text,
            channel="iphone_pwa",
            source="iphone_text",
            status=status,
        )
        audit = self.audit.record(
            "iphone_command_accepted",
            surface="iphone_companion",
            channel="iphone_pwa",
            device_id=device_id,
            result=status,
            metadata={"conversation_id_hash": _hash_text(conversation_id), "persona_mode": self.phase10.persona.state.mode},
        )
        return {
            "schema_version": IPHONE_COMPANION_SCHEMA_VERSION,
            "status": status,
            "assistant_text": assistant_text,
            "turn": turn,
            "persona": self.phase10.persona.status(),
            "phase_10": phase10_result,
            "audit_id": audit["event_id"],
            "would_execute": False,
            "executed": False,
            "direct_hermes_allowed": False,
        }

    def to_dict(self, *, channel: str = "desktop") -> Dict[str, Any]:
        provider_status = self.providers.status()
        approval_status = self.approvals.status()
        return {
            "schema_version": SHARED_STATE_SCHEMA_VERSION,
            "state_id": f"shared_jarvis_{_hash_text(str(len(self._conversation)) + self.phase10.persona.state.mode)}",
            "channel": _safe_text(channel, limit=80),
            "generated_at": _now_iso(),
            "same_jarvis_brain": True,
            "separate_mobile_agent": False,
            "persona": self.phase10.persona.status(),
            "provider_status": provider_status,
            "budget": self.budget.status(),
            "pending_approvals": approval_status.get("pending", []),
            "approval_status": approval_status,
            "conversation": list(self._conversation[-25:]),
            "conversation_sync": {
                "current_session_sync": True,
                "persistent_cross_device_history": "readiness_contract",
                "mobile_has_separate_memory": False,
            },
            "pairing": self.pairing.status(),
            "audit": self.audit.status(),
            "governance": {
                "jarvis_governs": True,
                "hermes_executes": True,
                "frontend_direct_hermes_allowed": False,
                "mobile_direct_hermes_allowed": False,
                "wake_phrase_can_approve": False,
                "memory_grants_permission": False,
                "utron_can_bypass_approvals": False,
                "dangerous_confirmation_phrase": PHASE_10_EXACT_APPROVAL_PHRASE,
            },
            "metadata_only": False,
        }


class Phase11RealProviderControllerIPhoneCompanion:
    def __init__(
        self,
        *,
        phase10: Phase10HandsFreeRuntimePersonaApiRouter,
        monthly_budget_eur: float = DEFAULT_MONTHLY_BUDGET_EUR,
        spent_eur: float = 0.0,
        env: Optional[Mapping[str, str]] = None,
        opener: Optional[Callable[[str], bool]] = None,
        openrouter_http_post: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.phase10 = phase10
        self.audit = Phase11AuditLog()
        self.budget = Phase11BudgetLedger(monthly_budget_eur=monthly_budget_eur, spent_eur=spent_eur)
        if env is not None:
            self.budget = Phase11BudgetLedger.from_env(env)
        self.providers = Phase11ProviderRegistry(budget=self.budget, env=env)
        self.model_router = ModelApiRouterV2(providers=self.providers, budget=self.budget)
        self.pairing = IPhonePairingManager(audit=self.audit)
        self.approvals = ApprovalV3Manager(audit=self.audit, trusted_device_checker=self.pairing.is_trusted)
        self.local_controller = LocalControllerPilot(audit=self.audit, opener=opener)
        self.browser = GovernedBrowserNavigationPilot(audit=self.audit, opener=opener)
        self.openrouter_adapter = SafeOpenRouterAdapter(providers=self.providers, budget=self.budget, http_post=openrouter_http_post)
        self.shared_state = SharedJarvisState(
            phase10=phase10,
            providers=self.providers,
            budget=self.budget,
            approvals=self.approvals,
            pairing=self.pairing,
            audit=self.audit,
        )

    @classmethod
    def from_environment(
        cls,
        *,
        phase10: Phase10HandsFreeRuntimePersonaApiRouter,
        opener: Optional[Callable[[str], bool]] = None,
    ) -> "Phase11RealProviderControllerIPhoneCompanion":
        return cls(
            phase10=phase10,
            monthly_budget_eur=_env_float("JARVIS_API_MONTHLY_BUDGET_EUR", DEFAULT_MONTHLY_BUDGET_EUR),
            spent_eur=_env_float("JARVIS_API_SPEND_EUR", 0.0),
            opener=opener,
        )

    def status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        providers = self.providers.status()
        return {
            "schema_version": PHASE_11_SCHEMA_VERSION,
            "phase": "Phase 11",
            "title": "Real Provider Wiring + Local Controller + iPhone Companion",
            "status": "implemented_as_bounded_real_provider_controller_iphone_pilot",
            "implemented_blocks": {
                "openrouter_provider_status": True,
                "local_provider_status": True,
                "model_api_router_v2": True,
                "monthly_budget_guard_30_eur_default": True,
                "approval_v3_provider_mobile_local_browser": True,
                "bounded_local_controller_open_jarvis": True,
                "governed_browser_open_url_search": True,
                "iphone_safari_pwa_companion": True,
                "shared_jarvis_state_read_model": True,
                "pwa_manifest": "/manifest.webmanifest" in routes,
            },
            "real_vs_readiness": {
                "real": [
                    "OpenRouter/local provider readiness and redacted status",
                    "Model/API Router v2 decisions with 30 EUR budget guard",
                    "metadata-only budget ledger entries for provider decisions",
                    "bounded real open of /jarvis through local controller pilot",
                    "bounded real open of safe URL/search through browser pilot",
                    "short-lived iPhone pairing and revocation in the same JARVIS control plane",
                    "iPhone text commands, UTRON toggle and approvals bound to action/scope/device",
                    "current-session shared conversation read model",
                ],
                "readiness": [
                    "live OpenRouter calls remain disabled unless live-call env and explicit adapter approval are supplied",
                    "Cursor/VS Code/Terminal/File Explorer/WhatsApp/Spotify real launchers are prepared only",
                    "form fill, submit, purchase, payment, publication and credential entry remain preview/blocked",
                    "remote access outside LAN needs future secure tunnel/bridge/native iOS decision",
                    "persistent cross-device conversation sync is contract/readiness only",
                ],
            },
            "route_readiness": {
                "phase_11_status": "/mark-3/phase-11/status" in routes,
                "providers_status": "/mark-3/providers/status" in routes,
                "model_router_v2_status": "/mark-3/model-router-v2/status" in routes,
                "iphone_status": "/iphone/companion/status" in routes,
                "iphone_pairing_start": "/iphone/pairing/start" in routes,
                "iphone_approval_decision": "/iphone/approval/decision" in routes,
                "local_controller_launch": "/mark-3/phase-11/local-controller/launch" in routes,
                "browser_open": "/mark-3/phase-11/browser/open" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "providers": providers,
            "model_router_v2": self.model_router.status(),
            "approval_v3": self.approvals.status(),
            "local_controller_pilot": self.local_controller.status(),
            "browser_navigation_pilot": self.browser.status(),
            "iphone_companion": self.iphone_status(),
            "shared_state": self.shared_state.to_dict(channel="phase11_status"),
            "security_gates": {
                "jarvis_governs": True,
                "hermes_executes": True,
                "no_duplicate_hermes_runtime": True,
                "frontend_direct_hermes_allowed": False,
                "mobile_direct_hermes_allowed": False,
                "no_generic_execute": True,
                "no_generic_shell_from_ui_or_mobile": True,
                "wake_phrase_can_approve": False,
                "voice_approval_requires_trusted_active_gated_readback_audit": True,
                "mobile_approval_requires_pairing_action_scope_expiry": True,
                "dangerous_exact_phrase": PHASE_10_EXACT_APPROVAL_PHRASE,
                "memory_grants_permission": False,
                "memory_downgrades_risk": False,
                "utron_bypasses_approvals": False,
                "provider_keys_exposed": False,
                "public_pc_exposure_enabled_by_default": False,
            },
            "source_endpoint": "/mark-3/phase-11/status",
            "metadata_only": False,
        }

    def iphone_status(self) -> Dict[str, Any]:
        shared = self.shared_state.to_dict(channel="iphone_pwa")
        return {
            "schema_version": IPHONE_COMPANION_SCHEMA_VERSION,
            "status": "iphone_safari_pwa_same_jarvis_control_surface",
            "mode": "local_lan_first_pwa",
            "same_jarvis_brain": True,
            "separate_mobile_agent": False,
            "mobile_available": True,
            "native_ios_app_built": False,
            "pwa_installable": True,
            "lan_access_first": True,
            "remote_access": "readiness_only_secure_tunnel_or_bridge_required",
            "connection": {
                "local_loopback": "desktop",
                "lan": "supported_when_backend_bound_safely_and_device_paired",
                "public_internet": "disabled_by_default",
                "secure_tunnel_future": True,
                "telegram_bridge_future": True,
                "native_ios_app_store_future": True,
                "vps_not_required_now": True,
            },
            "capabilities": {
                "read_state": True,
                "see_conversation": True,
                "send_text_commands": True,
                "browser_microphone_if_safari_allows": True,
                "hear_responses_if_safari_tts_allows": True,
                "approve_or_deny_pending_actions_when_paired": True,
                "toggle_utron_when_paired": True,
                "execute_directly": False,
                "call_hermes_directly": False,
                "raw_shell": False,
            },
            "shared_state": shared,
            "pairing": self.pairing.status(),
            "remote_kill_switch": {
                "surfaced": True,
                "state": "not_enabled",
                "blocks_mobile_control_when_enabled": True,
            },
            "security": {
                "pairing_required": True,
                "unauthenticated_control_allowed": False,
                "approval_bound_to_action_id_scope_channel_device": True,
                "approval_expires": True,
                "replay_rejected": True,
                "wake_phrase_can_approve": False,
                "no_public_exposure_by_default": True,
                "secrets_shown": False,
            },
            "metadata_only": False,
        }

