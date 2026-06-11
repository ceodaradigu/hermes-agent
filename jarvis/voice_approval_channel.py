from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.approval_execution_semantics import GlobalApprovalExecutionSemantics
from jarvis.approval_hardening import RiskLevel, StrongApprovalPolicy
from jarvis.local_runtime_safety import LocalRuntimeSafetyPolicy


EXACT_CRITICAL_PHRASE = "JARVIS, entiendo los riesgos, hazlo."


@dataclass(frozen=True)
class LocalAuditEvent:
    event_id: str
    timestamp: str
    event_type: str
    actor: str
    channel: str
    action_summary: str
    risk_level: str
    readback_present: bool
    confirmation_phrase_hash_or_redacted: str
    raw_audio_stored: bool = False
    transcript_stored: bool = False
    secrets_redacted: bool = True
    cost_summary: str = "unknown; operator review required"
    production_impact_summary: str = "none in preview"
    rollback_or_stop_plan_summary: str = "stop before execution; rollback required when applicable"
    result: str = "preview_only"
    expires_at: Optional[str] = None
    audit_safe: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VoiceApprovalState:
    approval_id: str
    voice_approval_available: bool = True
    voice_approval_enabled: bool = False
    owner_name: str = "David"
    approval_channel: str = "voice"
    pending_action: str = ""
    action_risk_level: str = "medium"
    readback_required: bool = True
    readback_text: str = ""
    risk_summary: str = ""
    cost_summary: str = "unknown; operator review required"
    production_impact_summary: str = "none in preview"
    rollback_or_stop_plan_summary: str = "stop before execution; rollback required when applicable"
    confirmation_steps_required: int = 1
    confirmation_steps_completed: int = 0
    required_phrases: List[str] = field(default_factory=list)
    accepted_phrases: List[str] = field(default_factory=list)
    rejected_phrases: List[str] = field(default_factory=list)
    unclear_input_count: int = 0
    max_unclear_attempts: int = 3
    expires_at: str = ""
    expired: bool = False
    audit_required: bool = True
    audit_event_preview: List[Dict[str, Any]] = field(default_factory=list)
    valid_voice_approval_present: bool = False
    strong_approval_satisfied: bool = False
    double_confirmation_satisfied: bool = False
    triple_confirmation_satisfied: bool = False
    eligible_after_valid_voice_approval: bool = False
    would_execute: bool = False
    readback_completed: bool = True
    cancelled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        self.expired = self.expired or _is_expired(self.expires_at)
        if self.expired:
            self.valid_voice_approval_present = False
            self.eligible_after_valid_voice_approval = False
        return asdict(self)


class VoiceApprovalChannel:
    def __init__(self, *, owner_name: str = "David", policy: LocalRuntimeSafetyPolicy | None = None) -> None:
        self.owner_name = owner_name
        self.policy = policy or LocalRuntimeSafetyPolicy()
        self.strong_policy = StrongApprovalPolicy()
        self.execution_semantics = GlobalApprovalExecutionSemantics()
        self._states: Dict[str, VoiceApprovalState] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "voice_approval_available": True,
            "voice_approval_enabled": False,
            "owner_name": self.owner_name,
            "approval_channel": "voice",
            "voice_can_approve": True,
            "wake_phrase_is_permission": False,
            "readback_required": True,
            "critical_exact_phrase_required": True,
            "critical_double_confirmation_required": True,
            "high_risk_triple_confirmation_available": True,
            "would_execute": False,
        }

    def start(
        self,
        *,
        action: str,
        risk_level: str | None = None,
        require_triple_confirmation: bool = False,
        cost_summary: str = "unknown; operator review required",
        production_impact_summary: str = "none in preview",
        rollback_or_stop_plan_summary: str = "stop before execution; rollback required when applicable",
        now: Optional[str] = None,
    ) -> VoiceApprovalState:
        raw_action = " ".join(str(action or "unnamed action").split())
        action = redact_sensitive_data({"action": raw_action})[0]["action"]
        context = _action_context(raw_action)
        classified_risk, strong_required, _ = self.strong_policy.classify(context)
        requested_risk = RiskLevel(risk_level) if risk_level else classified_risk
        risk = max((classified_risk, requested_risk), key=_risk_rank)
        cost_summary = _safe_summary(cost_summary, "unknown; operator review required")
        production_impact_summary = _safe_summary(production_impact_summary, "none in preview")
        rollback_or_stop_plan_summary = _safe_summary(
            rollback_or_stop_plan_summary,
            "stop before execution; rollback required when applicable",
        )
        critical = risk == RiskLevel.CRITICAL
        triple = bool(require_triple_confirmation)
        required = 3 if triple else 2 if critical or risk == RiskLevel.HIGH else 1
        phrases = ["sí, continúa"]
        if critical:
            phrases.append(EXACT_CRITICAL_PHRASE)
        elif strong_required or risk == RiskLevel.HIGH:
            phrases.append("JARVIS hazlo")
        if triple:
            phrases.append("JARVIS, confirmación final.")
        started = _parse_time(now) if now else datetime.now(timezone.utc)
        state = VoiceApprovalState(
            approval_id=str(uuid4()),
            owner_name=self.owner_name,
            pending_action=action,
            action_risk_level=risk.value,
            readback_text=f"{self.owner_name}, acción: {action}. Riesgo: {risk.value}. Coste: {cost_summary}. Impacto: {production_impact_summary}. Plan de parada o rollback: {rollback_or_stop_plan_summary}.",
            risk_summary=f"{risk.value} risk action requiring explicit voice approval",
            cost_summary=cost_summary,
            production_impact_summary=production_impact_summary,
            rollback_or_stop_plan_summary=rollback_or_stop_plan_summary,
            confirmation_steps_required=required,
            required_phrases=phrases,
            expires_at=(started + timedelta(seconds=self.policy.voice_approval_ttl_seconds)).isoformat(),
        )
        state.audit_event_preview.append(self._audit(state, "voice_approval_started", "awaiting_confirmation").to_dict())
        self._states[state.approval_id] = state
        return state

    def confirm(self, approval_id: str, phrase: str, *, now: Optional[str] = None) -> VoiceApprovalState:
        state = self._states[approval_id]
        if _is_expired(state.expires_at, now=now):
            state.expired = True
            state.valid_voice_approval_present = False
            state.audit_event_preview.append(self._audit(state, "voice_approval_expired", "expired", phrase).to_dict())
            return state
        if state.cancelled or state.valid_voice_approval_present:
            state.audit_event_preview.append(
                self._audit(
                    state,
                    "voice_approval_confirmation_ignored",
                    "cancelled" if state.cancelled else "already_valid",
                    phrase,
                ).to_dict()
            )
            return state
        normalized = _normalize_phrase(phrase)
        expected = _normalize_phrase(state.required_phrases[state.confirmation_steps_completed])
        if normalized in {"", "ruido", "no se entiende", "unclear"}:
            state.unclear_input_count += 1
            state.cancelled = state.unclear_input_count >= state.max_unclear_attempts
            state.audit_event_preview.append(self._audit(state, "voice_approval_unclear", "cancelled" if state.cancelled else "unclear", phrase).to_dict())
            return state
        if normalized != expected:
            state.rejected_phrases.append("[redacted mismatched phrase]")
            state.audit_event_preview.append(self._audit(state, "voice_approval_phrase_rejected", "rejected", phrase).to_dict())
            return state
        state.accepted_phrases.append("[accepted phrase hash recorded in audit]")
        state.confirmation_steps_completed += 1
        state.strong_approval_satisfied = state.confirmation_steps_completed >= 2 and state.action_risk_level in {"high", "critical"}
        state.double_confirmation_satisfied = state.confirmation_steps_completed >= 2
        state.triple_confirmation_satisfied = state.confirmation_steps_completed >= 3
        state.valid_voice_approval_present = state.confirmation_steps_completed >= state.confirmation_steps_required
        state.eligible_after_valid_voice_approval = state.valid_voice_approval_present
        state.audit_event_preview.append(self._audit(state, "voice_approval_confirmed", "valid" if state.valid_voice_approval_present else "partial", phrase).to_dict())
        return state

    def preview_flow(self, action: str, phrases: List[str], *, require_triple_confirmation: bool = False) -> Dict[str, Any]:
        state = self.start(action=action, require_triple_confirmation=require_triple_confirmation)
        for phrase in phrases:
            self.confirm(state.approval_id, phrase)
        decision = self.execution_semantics.preview_decision(
            action_name=action,
            action_category="critical" if state.action_risk_level == "critical" else "sensitive",
            risk_level=state.action_risk_level,
            valid_approval_present=state.valid_voice_approval_present,
            strong_approval_present=state.strong_approval_satisfied,
            double_confirmation_present=state.double_confirmation_satisfied,
            context_fingerprint_matches=state.valid_voice_approval_present,
            permission_gates_passed=state.valid_voice_approval_present,
            audit_present=True,
            rollback_or_stop_plan_required=True,
            rollback_or_stop_plan_present=True,
            execution_capable_when_approved=False,
        ).to_dict()
        return {**state.to_dict(), "mark_1_execution_eligibility_preview": decision, "would_execute": False}

    def audit_preview(self) -> Dict[str, Any]:
        sample = self.start(action="deploy production")
        return {"audit_safe": True, "events": sample.audit_event_preview, "raw_audio_stored": False}

    def _audit(self, state: VoiceApprovalState, event_type: str, result: str, phrase: str = "") -> LocalAuditEvent:
        digest = hashlib.sha256(_normalize_phrase(phrase).encode("utf-8")).hexdigest()[:16] if phrase else "[not provided]"
        return LocalAuditEvent(
            event_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            actor=self.owner_name,
            channel="voice",
            action_summary=state.pending_action[:160],
            risk_level=state.action_risk_level,
            readback_present=state.readback_completed,
            confirmation_phrase_hash_or_redacted=f"sha256:{digest}" if phrase else digest,
            cost_summary=state.cost_summary,
            production_impact_summary=state.production_impact_summary,
            rollback_or_stop_plan_summary=state.rollback_or_stop_plan_summary,
            result=result,
            expires_at=state.expires_at,
        )


def _action_context(action: str) -> Dict[str, Any]:
    text = action.casefold()
    context: Dict[str, Any] = {"action_type": action}
    for name, markers in (
        ("production", ("production", "producción", "produccion", "deploy", "despliega")),
        ("money_or_payments", ("stripe", "payment", "pago", "charge", "cobra")),
        ("external_call", ("deploy", "stripe", "publish", "publica")),
    ):
        if any(item in text for item in markers):
            context[name] = True
    return context


def _risk_rank(risk: RiskLevel) -> int:
    return {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }[risk]


def _safe_summary(value: str, fallback: str) -> str:
    safe = redact_sensitive_data({"summary": " ".join(str(value or "").split())})[0]["summary"]
    return safe or fallback


def _normalize_phrase(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _is_expired(expires_at: str, *, now: Optional[str] = None) -> bool:
    current = _parse_time(now) if now else datetime.now(timezone.utc)
    return current >= _parse_time(expires_at)


def mark_2_macro_1_markers() -> Dict[str, Any]:
    return {
        "mark_2_started": True,
        "mark_2_current": True,
        "mark_2_macro_1_local_daemon_real_wake_desktop_runtime_voice_approval": True,
        "local_daemon_available": True,
        "local_daemon_enabled": False,
        "local_daemon_disabled_by_default": True,
        "desktop_runtime_available": True,
        "real_wake_listener_available": True,
        "wake_listener_disabled_by_default": True,
        "wake_listener_enabled": False,
        "microphone_requires_opt_in": True,
        "microphone_active": False,
        "microphone_inactive_by_default": True,
        "voice_approval_channel_available": True,
        "voice_approval_enabled": False,
        "voice_can_approve": True,
        "wake_phrase_is_not_permission": True,
        "voice_approval_requires_readback": True,
        "critical_voice_approval_requires_exact_phrase": True,
        "critical_voice_approval_requires_double_confirmation": True,
        "high_risk_voice_approval_can_require_triple_confirmation": True,
        "kill_switch_available": True,
        "stop_phrase_always_available": True,
        "visible_listening_indicator_required": True,
        "raw_audio_storage_disabled": True,
        "raw_audio_storage_enabled": False,
        "external_speech_api_disabled": True,
        "external_speech_api_enabled": False,
        "mark_1_release_candidate_complete": True,
        "mark_2_macro_2_planned": True,
        "next_recommended_macro_pr": "Mark 2 Macro 2 — Real Tool Execution: Browser, GitHub, Filesystem & APIs",
        "restrictions_are_approval_gates": True,
    }
