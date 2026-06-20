from __future__ import annotations

import hashlib
import math
import os
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from uuid import uuid4


PHASE_10_SCHEMA_VERSION = "jarvis.phase_10_hands_free_runtime_persona_api_brain_router.v1"
VOICE_UI_INTENT_SCHEMA_VERSION = "jarvis.phase_10.voice_ui_intent_router.v1"
APP_LAUNCHER_SCHEMA_VERSION = "jarvis.phase_10.app_launcher_intents.v1"
BROWSER_INTENT_SCHEMA_VERSION = "jarvis.phase_10.browser_navigation_intents.v1"
APPROVAL_V2_SCHEMA_VERSION = "jarvis.phase_10.voice_text_approval_v2.v1"
PERSONA_SCHEMA_VERSION = "jarvis.phase_10.persona.v1"
VOICE_PROVIDER_ARCHITECTURE_SCHEMA_VERSION = "jarvis.phase_10.voice_provider_architecture.v1"
MODEL_ROUTER_SCHEMA_VERSION = "jarvis.phase_10.model_api_router.v1"

PHASE_10_EXACT_APPROVAL_PHRASE = "confirmo y autorizo"
WAKE_PHRASES = ("hola jarvis", "jarvis")
STOP_PHRASES = ("para", "jarvis para", "callate", "jarvis callate")
SENSITIVE_UI_ACTIONS = {
    "camera.start",
    "audio_recording.start",
    "video_recording.start",
    "sensor.start",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Phase10Decision:
    schema_version: str
    intent_type: str
    intent_name: str
    normalized_text: str
    confidence: float
    reason: str
    risk_level: str = "low"
    requires_approval: bool = False
    requires_exact_phrase: bool = False
    required_phrase: str = PHASE_10_EXACT_APPROVAL_PHRASE
    trusted_active_session_required: bool = False
    action_id: str = ""
    ui_action: Optional[Dict[str, Any]] = None
    fallback_question: str = ""
    spanish_response: str = ""
    preview_only: bool = True
    read_only: bool = True
    would_execute: bool = False
    hermes_dispatch_allowed: bool = False
    frontend_direct_hermes_allowed: bool = False
    raw_audio_stored: bool = False
    raw_audio_sent_to_backend: bool = False
    wake_phrase_can_approve: bool = False
    audit_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", normalize_confidence(self.confidence))
        object.__setattr__(self, "ui_action", dict(self.ui_action or {}))
        object.__setattr__(self, "audit_metadata", _safe_metadata(self.audit_metadata))
        for name in (
            "preview_only",
            "read_only",
        ):
            object.__setattr__(self, name, True)
        for name in (
            "would_execute",
            "hermes_dispatch_allowed",
            "frontend_direct_hermes_allowed",
            "raw_audio_stored",
            "raw_audio_sent_to_backend",
            "wake_phrase_can_approve",
        ):
            object.__setattr__(self, name, False)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AppDefinition:
    app_id: str
    display_name: str
    aliases: Tuple[str, ...]
    command_preview: Tuple[str, ...]
    risk_level: str = "low"
    requires_approval: bool = False
    sensitive: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["aliases"] = list(self.aliases)
        data["command_preview"] = list(self.command_preview)
        return data


@dataclass
class PendingApproval:
    approval_id: str
    action_summary: str
    risk_level: str
    cost_summary: str
    change_summary: str
    rollback_or_stop_plan: str
    session_id: str
    context_fingerprint: str
    required_phrase: str = PHASE_10_EXACT_APPROVAL_PHRASE
    created_at: str = field(default_factory=_now_iso)
    approved: bool = False
    consumed: bool = False
    rejected_reason: str = ""
    audit_events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": APPROVAL_V2_SCHEMA_VERSION,
            "approval_id": self.approval_id,
            "action_summary": self.action_summary,
            "risk_level": self.risk_level,
            "cost_summary": self.cost_summary,
            "change_summary": self.change_summary,
            "rollback_or_stop_plan": self.rollback_or_stop_plan,
            "session_id_hash": _hash_text(self.session_id) if self.session_id else "",
            "context_fingerprint": self.context_fingerprint,
            "required_phrase": self.required_phrase,
            "created_at": self.created_at,
            "approved": self.approved,
            "consumed": self.consumed,
            "rejected_reason": self.rejected_reason,
            "audit_events": list(self.audit_events),
            "readback_text": approval_readback(
                action=self.action_summary,
                risk_level=self.risk_level,
                cost_summary=self.cost_summary,
                change_summary=self.change_summary,
                rollback_or_stop_plan=self.rollback_or_stop_plan,
            ),
            "wake_phrase_can_approve": False,
            "utron_can_bypass_approvals": False,
            "raw_audio_stored": False,
            "transcript_stored": False,
            "metadata_only": True,
        }


@dataclass
class PersonaState:
    mode: str = "jarvis"
    visible_name: str = "JARVIS"
    theme: str = "cyan"
    voice_preference: str = "masculina o neutra, humana, cálida, elegante y tecnológica"
    tone_contract: str = "humano, cercano, elegante, inteligente, útil, calmado, premium"
    activated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": PERSONA_SCHEMA_VERSION,
            "state": asdict(self),
            "activation_phrases": ["JARVIS, activa modo UTRON"],
            "deactivation_phrases": ["desactiva UTRON"],
            "safety": {
                "spanish_default": True,
                "utron_visible_name": self.mode == "utron",
                "utron_red_theme": self.mode == "utron",
                "approvals_bypassed": False,
                "wake_phrase_can_approve": False,
                "severe_abuse_toward_david_allowed": False,
                "copyrighted_voice_or_dialogue_clone": False,
                "risk_hidden_or_downgraded": False,
            },
            "read_only": True,
            "metadata_only": True,
        }


class WakeStopPhraseRuntime:
    """Deterministic wake/stop recognizer. It never opens a microphone."""

    def preview(self, text: str, *, confidence: float = 1.0) -> Dict[str, Any]:
        normalized = normalize_spanish(text)
        confidence = normalize_confidence(confidence)
        wake = self._match_wake(normalized)
        stop = self._match_stop(normalized)
        extracted = normalized
        if wake:
            extracted = normalized[len(wake) :].strip(" ,;:.-")
        return {
            "schema_version": PHASE_10_SCHEMA_VERSION,
            "input_kind": "text_transcript_preview",
            "normalized_text": normalized,
            "wake_phrase_detected": wake is not None,
            "matched_wake_phrase": wake,
            "stop_phrase_detected": stop is not None,
            "matched_stop_phrase": stop,
            "confidence": confidence,
            "should_open_conversation": bool(wake and confidence >= 0.8 and not stop),
            "should_request_local_controller_open_jarvis": bool(wake and confidence >= 0.8),
            "extracted_command": extracted if wake else normalized,
            "visible_state": "stopped" if stop else "active_conversation" if wake else "listening_for_wake",
            "local_controller_contract": {
                "can_open_chrome_on_jarvis": True,
                "route": "/jarvis",
                "execution_path": "local_controller_or_governed_hermes_action_only",
                "frontend_direct_execution_allowed": False,
                "no_generic_shell": True,
                "real_open_requires_controller_readiness": True,
            },
            "privacy": {
                "no_hidden_recording": True,
                "raw_audio_stored": False,
                "raw_audio_sent_to_backend": False,
                "transcript_before_activation_persisted": False,
            },
            "approval": {
                "wake_phrase_can_approve": False,
                "wake_phrase_can_execute": False,
            },
            "manual_browser_fallback": {
                "available": True,
                "language": "Si el navegador exige gesto o permiso, pulsa el micrófono una vez. No fingiré escucha permanente.",
            },
            "read_only": True,
        }

    def _match_wake(self, normalized: str) -> Optional[str]:
        return next(
            (
                phrase
                for phrase in WAKE_PHRASES
                if re.match(rf"^{re.escape(phrase)}(?:\b|[\s,;:!.?])?", normalized)
            ),
            None,
        )

    def _match_stop(self, normalized: str) -> Optional[str]:
        compact = normalized.strip(" ,;:!.?")
        return next((phrase for phrase in STOP_PHRASES if compact == phrase), None)


class VoiceUiIntentRouter:
    """Spanish deterministic UI command router for the /jarvis surface."""

    def route(self, text: str) -> Phase10Decision:
        normalized = normalize_spanish(text)
        if not normalized:
            return self._ambiguous(normalized, "No he oído una orden clara.")

        if _any(normalized, ("activa modo utron", "activar modo utron", "modo utron")):
            return self._decision(
                normalized,
                "persona.activate_utron",
                "persona.activate_utron",
                "Activar modo UTRON visible.",
                confidence=0.94,
                ui_action={"type": "persona", "mode": "utron"},
            )
        if _any(normalized, ("desactiva utron", "desactivar utron", "quita utron", "modo jarvis")):
            return self._decision(
                normalized,
                "persona.deactivate_utron",
                "persona.deactivate_utron",
                "Volver a modo JARVIS.",
                confidence=0.94,
                ui_action={"type": "persona", "mode": "jarvis"},
            )
        if _any(normalized, ("abre el panel", "abre panel", "ensename el panel", "muestra el panel", "abre sistemas", "ensename sistemas")):
            return self._decision(
                normalized,
                "ui.panel.open",
                "debug_panel.open",
                "Abrir el panel plegado de sistemas.",
                confidence=0.86,
                ui_action={"type": "tab", "tab": "voice"},
            )
        if _any(normalized, ("cierra el panel", "quita el panel", "oculta el panel", "cerrar panel")):
            return self._decision(
                normalized,
                "ui.panel.close",
                "debug_panel.close",
                "Cerrar o devolver el panel a cockpit.",
                confidence=0.84,
                ui_action={"type": "tab", "tab": "cockpit"},
            )
        if _any(normalized, ("activa la voz", "enciende la voz", "voz on", "pon voz", "habla")):
            return self._decision(
                normalized,
                "ui.voice_output.enable",
                "voice_output.enable",
                "Activar salida de voz del navegador.",
                confidence=0.9,
                ui_action={"type": "voice_output", "enabled": True},
            )
        if _any(normalized, ("desactiva la voz", "apaga la voz", "voz off", "sin voz", "callate pero sigue escrito")):
            return self._decision(
                normalized,
                "ui.voice_output.disable",
                "voice_output.disable",
                "Desactivar salida de voz; mantener texto visible.",
                confidence=0.9,
                ui_action={"type": "voice_output", "enabled": False},
            )
        if _any(normalized, ("repite", "repiteme eso", "repite eso", "dilo otra vez", "otra vez")):
            return self._decision(
                normalized,
                "ui.voice_output.repeat",
                "voice_output.repeat",
                "Repetir la última respuesta escrita.",
                confidence=0.88,
                ui_action={"type": "voice_output", "command": "repeat"},
            )
        if _any(normalized, ("deten la voz", "para la voz", "corta ya", "callate", "silencio")):
            return self._decision(
                normalized,
                "ui.voice_output.stop",
                "voice_output.stop",
                "Detener TTS sin borrar la respuesta escrita.",
                confidence=0.92,
                ui_action={"type": "voice_output", "command": "stop"},
            )
        if _any(normalized, ("abre la camara", "enciende la camara", "activa la camara")):
            return self._decision(
                normalized,
                "ui.camera.start",
                "camera.start",
                "La cámara requiere opt-in explícito antes de pedir permiso al navegador.",
                confidence=0.9,
                risk_level="medium",
                requires_approval=True,
                requires_exact_phrase=True,
                trusted_session=True,
                ui_action={"type": "camera", "command": "start"},
            )
        if _any(normalized, ("apaga la camara", "cierra la camara", "quita la camara", "deten la camara")):
            return self._decision(
                normalized,
                "ui.camera.stop",
                "camera.stop",
                "Apagar la cámara local si está activa.",
                confidence=0.88,
                ui_action={"type": "camera", "command": "stop"},
            )
        if _any(normalized, ("graba audio", "empieza a grabar audio", "inicia grabacion de audio", "graba mi voz")):
            return self._decision(
                normalized,
                "ui.audio_recording.start",
                "audio_recording.start",
                "La grabación local de audio requiere opt-in explícito y visible.",
                confidence=0.9,
                risk_level="medium",
                requires_approval=True,
                requires_exact_phrase=True,
                trusted_session=True,
                ui_action={"type": "audio_recording", "command": "start"},
            )
        if _any(normalized, ("para la grabacion", "deten la grabacion", "corta la grabacion", "deja de grabar")):
            return self._decision(
                normalized,
                "ui.audio_recording.stop",
                "audio_recording.stop",
                "Parar la grabación local si está activa.",
                confidence=0.9,
                ui_action={"type": "audio_recording", "command": "stop"},
            )
        if _any(normalized, ("graba video", "inicia video", "empieza a grabar video")):
            return self._decision(
                normalized,
                "ui.video_recording.start",
                "video_recording.start",
                "La grabación local de vídeo requiere opt-in explícito y visible.",
                confidence=0.88,
                risk_level="medium",
                requires_approval=True,
                requires_exact_phrase=True,
                trusted_session=True,
                ui_action={"type": "video_recording", "command": "start"},
            )
        if _any(normalized, ("para el video", "deten el video", "para la grabacion de video")):
            return self._decision(
                normalized,
                "ui.video_recording.stop",
                "video_recording.stop",
                "Parar la grabación local de vídeo si está activa.",
                confidence=0.86,
                ui_action={"type": "video_recording", "command": "stop"},
            )
        if _any(normalized, ("revisa el estado", "estado", "status", "como estas", "comprueba estado")):
            return self._decision(
                normalized,
                "ui.status.review",
                "status.review",
                "Mostrar el estado visible y mantenerlo sin ejecución.",
                confidence=0.82,
                ui_action={"type": "tab", "tab": "cockpit"},
            )
        if _any(normalized, ("cancela", "cancelar", "para", "detente")):
            return self._decision(
                normalized,
                "ui.cancel",
                "conversation.cancel",
                "Cancelar escucha, habla o flujo pendiente.",
                confidence=0.91,
                ui_action={"type": "conversation", "command": "cancel"},
            )
        return self._ambiguous(
            normalized,
            "No estoy seguro de qué control quieres tocar. ¿Quieres abrir panel, activar voz, repetir, parar voz, cámara, grabación, estado o cancelar?",
        )

    def _decision(
        self,
        normalized: str,
        intent_name: str,
        action_id: str,
        reason: str,
        *,
        confidence: float,
        risk_level: str = "low",
        requires_approval: bool = False,
        requires_exact_phrase: bool = False,
        trusted_session: bool = False,
        ui_action: Optional[Dict[str, Any]] = None,
    ) -> Phase10Decision:
        return Phase10Decision(
            schema_version=VOICE_UI_INTENT_SCHEMA_VERSION,
            intent_type="voice_ui_control",
            intent_name=intent_name,
            action_id=action_id,
            normalized_text=normalized,
            confidence=confidence,
            reason=reason,
            risk_level=risk_level,
            requires_approval=requires_approval,
            requires_exact_phrase=requires_exact_phrase,
            trusted_active_session_required=trusted_session,
            ui_action=ui_action or {},
            spanish_response=(
                f"Acción sensible preparada: {reason} Di o escribe '{PHASE_10_EXACT_APPROVAL_PHRASE}' para autorizar."
                if requires_approval
                else f"He reconocido el control: {reason}"
            ),
            audit_metadata={
                "deterministic_router": True,
                "sensitive_ui_action": action_id in SENSITIVE_UI_ACTIONS,
                "frontend_direct_hermes_allowed": False,
                "no_generic_shell": True,
            },
        )

    def _ambiguous(self, normalized: str, question: str) -> Phase10Decision:
        return Phase10Decision(
            schema_version=VOICE_UI_INTENT_SCHEMA_VERSION,
            intent_type="voice_ui_control",
            intent_name="ambiguous",
            normalized_text=normalized,
            confidence=0.3,
            reason="No deterministic variant matched with enough confidence.",
            risk_level="low",
            fallback_question=question,
            spanish_response=question,
            audit_metadata={"deterministic_router": True, "ambiguous": True},
        )


class GovernedAppLauncher:
    def __init__(self, aliases: Optional[Mapping[str, str]] = None) -> None:
        self._apps = _default_app_registry()
        for alias, app_id in (aliases or {}).items():
            normalized_alias = normalize_spanish(alias)
            if app_id in self._apps and normalized_alias:
                current = self._apps[app_id]
                self._apps[app_id] = AppDefinition(
                    app_id=current.app_id,
                    display_name=current.display_name,
                    aliases=tuple(sorted(set((*current.aliases, normalized_alias)))),
                    command_preview=current.command_preview,
                    risk_level=current.risk_level,
                    requires_approval=current.requires_approval,
                    sensitive=current.sensitive,
                    notes=current.notes,
                )

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": APP_LAUNCHER_SCHEMA_VERSION,
            "state": {
                "mode": "governed_app_launch_intent_readiness",
                "known_app_count": len(self._apps),
                "real_launch_enabled": False,
                "frontend_direct_launch_allowed": False,
                "freeform_shell_allowed": False,
            },
            "known_apps": {app_id: app.to_dict() for app_id, app in self._apps.items()},
            "unknown_app_message_es": "No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida.",
            "execution_path": {
                "allowed": "local_controller_or_hermes_governed_action_only",
                "generic_shell": False,
                "frontend": False,
                "audit_required": True,
            },
            "read_only": True,
        }

    def prepare(self, app_name: str, *, actor: str = "David") -> Dict[str, Any]:
        normalized = normalize_spanish(app_name)
        app = self._resolve(normalized)
        if not app:
            return {
                "schema_version": APP_LAUNCHER_SCHEMA_VERSION,
                "intent": "app.launch",
                "status": "unknown_app",
                "requested_app": str(app_name or ""),
                "normalized_app": normalized,
                "known": False,
                "spanish_response": "No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida.",
                "requires_approval": False,
                "risk_level": "unknown",
                "would_execute": False,
                "executed": False,
                "frontend_direct_execution_allowed": False,
                "freeform_shell_allowed": False,
                "audit_metadata": {
                    "actor": _safe_text(actor),
                    "metadata_only": True,
                    "no_fake_open_claim": True,
                },
                "read_only": True,
            }
        return {
            "schema_version": APP_LAUNCHER_SCHEMA_VERSION,
            "intent": "app.launch",
            "status": "prepared_governed_intent",
            "requested_app": str(app_name or ""),
            "normalized_app": normalized,
            "known": True,
            "resolved_app": app.to_dict(),
            "resolved_command_preview": list(app.command_preview),
            "risk_level": app.risk_level,
            "requires_approval": app.requires_approval,
            "requires_exact_phrase": app.requires_approval,
            "required_phrase": PHASE_10_EXACT_APPROVAL_PHRASE if app.requires_approval else "",
            "execution_path": "local_controller_or_hermes_governed_action_only",
            "would_execute": False,
            "executed": False,
            "launch_supported_now": False,
            "spanish_response": (
                f"Puedo preparar {app.display_name}. Es sensible y necesita aprobación antes de abrirlo."
                if app.requires_approval
                else f"Puedo preparar la apertura de {app.display_name}; no fingiré que se abrió hasta que el controlador local lo confirme."
            ),
            "frontend_direct_execution_allowed": False,
            "freeform_shell_allowed": False,
            "audit_metadata": {
                "actor": _safe_text(actor),
                "metadata_only": True,
                "known_app": app.app_id,
                "sensitive": app.sensitive,
                "no_fake_open_claim": True,
            },
            "read_only": True,
        }

    def _resolve(self, normalized: str) -> Optional[AppDefinition]:
        for app in self._apps.values():
            if normalized == normalize_spanish(app.display_name) or normalized in app.aliases:
                return app
        return None


class GovernedBrowserIntentRouter:
    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": BROWSER_INTENT_SCHEMA_VERSION,
            "state": {
                "mode": "governed_browser_navigation_intents",
                "real_browser_adapter_available": False,
                "preview_first_for_forms": True,
                "submits_without_approval": False,
                "credential_handling_enabled": False,
            },
            "supported_intents": [
                "web.search",
                "browser.open_url",
                "page.summarize",
                "form.fill_preview",
                "message.prepare",
                "service.navigate",
            ],
            "safety": {
                "no_form_submit_without_approval": True,
                "no_purchase_payment_publication_without_strong_approval": True,
                "login_requires_manual_david_action": True,
                "password_storage_plain_text": False,
                "frontend_direct_browser_execution": False,
            },
            "read_only": True,
        }

    def prepare(self, text: str, *, actor: str = "David") -> Dict[str, Any]:
        normalized = normalize_spanish(text)
        intent = "unknown"
        risk = "low"
        requires_approval = False
        strong = False
        preview_first = True
        unsupported_reason = ""

        if _looks_like_url(text):
            intent = "browser.open_url"
        elif _any(normalized, ("busca", "buscar", "search", "googlea")):
            intent = "web.search"
        elif _any(normalized, ("resume esta pagina", "resume la pagina", "resumeme la pagina", "summarize")):
            intent = "page.summarize"
        elif _any(normalized, ("rellena", "formulario", "fill form")):
            intent = "form.fill_preview"
            risk = "medium"
            requires_approval = True
        elif _any(normalized, ("prepara mensaje", "escribe mensaje", "redacta mensaje", "whatsapp")):
            intent = "message.prepare"
            risk = "medium"
            requires_approval = True
        elif _any(normalized, ("abre", "navega", "entra en", "ve a")):
            intent = "service.navigate"
        if _any(normalized, ("compra", "paga", "suscribete", "publica", "envia", "submit", "comprar")):
            risk = "critical"
            requires_approval = True
            strong = True
        if _any(normalized, ("login", "contraseña", "password", "credencial", "cookie", "token")):
            unsupported_reason = "El login debe hacerlo David manualmente o una futura bóveda aprobada; no manejo credenciales en claro."
            risk = "high"
            requires_approval = True

        return {
            "schema_version": BROWSER_INTENT_SCHEMA_VERSION,
            "intent": intent,
            "normalized_text": normalized,
            "actor": _safe_text(actor),
            "risk_level": risk,
            "requires_approval": requires_approval,
            "requires_strong_approval": strong,
            "requires_exact_phrase": requires_approval,
            "required_phrase": PHASE_10_EXACT_APPROVAL_PHRASE if requires_approval else "",
            "preview_first": preview_first,
            "adapter_available": False,
            "status": "prepared_governed_intent" if intent != "unknown" else "unsupported_or_ambiguous",
            "would_execute": False,
            "executed": False,
            "frontend_direct_execution_allowed": False,
            "browser_adapter_path": "governed_browser_adapter_future_or_existing_backend_only",
            "unsupported_reason": unsupported_reason,
            "spanish_response": _browser_response(intent, requires_approval, strong, unsupported_reason),
            "safety": {
                "form_submit_allowed": False,
                "purchase_payment_publication_allowed": False,
                "credential_storage_allowed": False,
                "login_manual_required": bool(unsupported_reason),
                "no_fake_navigation_claim": True,
            },
            "audit_metadata": {
                "metadata_only": True,
                "actor": _safe_text(actor),
                "intent": intent,
            },
            "read_only": True,
        }


class ApprovalV2Manager:
    def __init__(self) -> None:
        self._pending: Dict[str, PendingApproval] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": APPROVAL_V2_SCHEMA_VERSION,
            "state": {
                "pending_count": len([item for item in self._pending.values() if not item.consumed]),
                "exact_phrase_required_for_dangerous": True,
                "required_phrase": PHASE_10_EXACT_APPROVAL_PHRASE,
                "voice_or_text_supported": True,
                "active_trusted_session_required_for_voice": True,
            },
            "safety": {
                "wake_phrase_can_approve": False,
                "wake_phrase_alone_never_approves": True,
                "phrase_replay_can_approve_unrelated_action": False,
                "utron_can_bypass_approvals": False,
                "memory_grants_permission": False,
            },
            "pending": [item.to_dict() for item in self._pending.values() if not item.consumed],
            "read_only": True,
        }

    def start(
        self,
        *,
        action: str,
        risk_level: str = "high",
        cost_summary: str = "sin coste conocido; revisar antes de ejecutar",
        change_summary: str = "puede tocar estado externo o local sensible",
        rollback_or_stop_plan: str = "parar antes de ejecutar; rollback específico si aplica",
        session_id: str = "",
    ) -> Dict[str, Any]:
        action = _safe_text(action or "acción sin nombre", limit=220)
        risk_level = risk_level if risk_level in {"low", "medium", "high", "critical"} else "high"
        fingerprint = _hash_text("|".join([action, risk_level, cost_summary, change_summary, rollback_or_stop_plan]))
        approval = PendingApproval(
            approval_id=f"phase10_approval_{uuid4()}",
            action_summary=action,
            risk_level=risk_level,
            cost_summary=_safe_text(cost_summary, limit=220),
            change_summary=_safe_text(change_summary, limit=220),
            rollback_or_stop_plan=_safe_text(rollback_or_stop_plan, limit=220),
            session_id=_safe_text(session_id, limit=120),
            context_fingerprint=fingerprint,
        )
        approval.audit_events.append(_approval_audit("approval_started", approval, result="awaiting_confirmation"))
        self._pending[approval.approval_id] = approval
        return approval.to_dict()

    def confirm(
        self,
        *,
        approval_id: str,
        phrase: str,
        session_id: str = "",
        channel: str = "text",
        active_trusted_session: bool = False,
        current_action_fingerprint: str = "",
    ) -> Dict[str, Any]:
        approval = self._pending.get(str(approval_id or ""))
        if not approval:
            return _approval_rejection("approval_not_found", "No hay una aprobación activa con ese id.")
        normalized_phrase = normalize_spanish(phrase)
        if normalized_phrase in WAKE_PHRASES:
            approval.audit_events.append(_approval_audit("approval_rejected", approval, phrase=phrase, result="wake_phrase_rejected"))
            return {**approval.to_dict(), "approved": False, "status": "rejected", "reason": "wake_phrase_never_approves"}
        if normalized_phrase != PHASE_10_EXACT_APPROVAL_PHRASE:
            approval.audit_events.append(_approval_audit("approval_rejected", approval, phrase=phrase, result="phrase_mismatch"))
            return {**approval.to_dict(), "approved": False, "status": "rejected", "reason": "exact_phrase_required"}
        if channel == "voice" and not active_trusted_session:
            approval.audit_events.append(_approval_audit("approval_rejected", approval, phrase=phrase, result="untrusted_voice_session"))
            return {**approval.to_dict(), "approved": False, "status": "rejected", "reason": "voice_requires_active_trusted_session"}
        if approval.consumed or approval.approved:
            approval.audit_events.append(_approval_audit("approval_rejected", approval, phrase=phrase, result="replay_rejected"))
            return {**approval.to_dict(), "approved": False, "status": "rejected", "reason": "phrase_replay_rejected"}
        if approval.session_id and session_id and _safe_text(session_id, limit=120) != approval.session_id:
            approval.audit_events.append(_approval_audit("approval_rejected", approval, phrase=phrase, result="session_mismatch"))
            return {**approval.to_dict(), "approved": False, "status": "rejected", "reason": "session_mismatch"}
        if current_action_fingerprint and current_action_fingerprint != approval.context_fingerprint:
            approval.audit_events.append(_approval_audit("approval_rejected", approval, phrase=phrase, result="context_mismatch"))
            return {**approval.to_dict(), "approved": False, "status": "rejected", "reason": "context_mismatch"}

        approval.approved = True
        approval.consumed = True
        approval.audit_events.append(_approval_audit("approval_confirmed", approval, phrase=phrase, result="approved_metadata_only"))
        return {**approval.to_dict(), "approved": True, "status": "approved", "would_execute": False, "executed": False}


class PersonaManager:
    def __init__(self) -> None:
        self.state = PersonaState()

    def status(self) -> Dict[str, Any]:
        return self.state.to_dict()

    def handle_text(self, text: str) -> Dict[str, Any]:
        normalized = normalize_spanish(text)
        changed = False
        if _any(normalized, ("activa modo utron", "activar modo utron", "modo utron")):
            self.state = PersonaState(
                mode="utron",
                visible_name="UTRON",
                theme="red",
                voice_preference="más profunda, oscura y autoritaria cuando el proveedor lo permita",
                tone_contract="sarcástico, autoritario, afilado, con humor oscuro, útil y obediente a David",
                activated_at=_now_iso(),
            )
            changed = True
        elif _any(normalized, ("desactiva utron", "desactivar utron", "quita utron", "modo jarvis")):
            self.state = PersonaState()
            changed = True
        return {
            **self.status(),
            "changed": changed,
            "normalized_text": normalized,
            "response": self.format_response(
                "Modo UTRON activado. Seré más seco, rojo y útil; las aprobaciones siguen intactas."
                if self.state.mode == "utron" and changed
                else "Modo JARVIS restaurado. Vuelvo al tono calmado y elegante."
                if changed
                else "",
            ),
        }

    def format_response(self, text: str, *, technical: bool = False) -> str:
        cleaned = _safe_response_text(text)
        if not cleaned:
            return ""
        if self.state.mode == "utron":
            return (
                f"UTRON: {cleaned} "
                "Y no, no voy a saltarme aprobaciones; hasta una máquina autoritaria entiende los controles."
            )
        if technical:
            return f"JARVIS: {cleaned}"
        return cleaned


class VoiceProviderArchitecture:
    def status(self, persona: PersonaState) -> Dict[str, Any]:
        premium_key_present = bool(os.environ.get("JARVIS_PREMIUM_TTS_API_KEY"))
        local_tts_configured = bool(os.environ.get("JARVIS_LOCAL_TTS_URL") or os.environ.get("JARVIS_PIPER_VOICE_PATH"))
        return {
            "schema_version": VOICE_PROVIDER_ARCHITECTURE_SCHEMA_VERSION,
            "state": {
                "selected_provider": "browser_speech_synthesis",
                "selected_reason": "free_browser_fallback_no_paid_call",
                "persona_mode": persona.mode,
                "cost_eur": 0.0,
                "external_call_performed": False,
                "paid_usage_enabled": False,
            },
            "providers": {
                "browser_speech_synthesis": {
                    "capability": "tts",
                    "ready": "client_side_unknown",
                    "cost_eur": 0.0,
                    "external_call": False,
                    "default": True,
                    "voice_preference": persona.voice_preference,
                },
                "local_tts": {
                    "capability": "tts",
                    "ready": local_tts_configured,
                    "configured": local_tts_configured,
                    "cost_eur": 0.0,
                    "external_call": False,
                    "status": "ready_contract" if local_tts_configured else "not_configured",
                },
                "premium_api_voice": {
                    "capability": "tts",
                    "ready": premium_key_present,
                    "configured": premium_key_present,
                    "cost_eur": "metered_unknown_until_provider",
                    "external_call": False,
                    "paid_usage_requires_approval": True,
                    "status": "configured_but_disabled_until_approved" if premium_key_present else "not_configured",
                },
            },
            "safety": {
                "no_paid_voice_by_default": True,
                "no_movie_voice_cloning": True,
                "no_external_call_without_key_and_approval": True,
                "raw_audio_stored": False,
            },
            "read_only": True,
        }


class ModelApiRouter:
    def __init__(self, *, monthly_budget_eur: float = 30.0, spent_eur: float = 0.0) -> None:
        self.monthly_budget_eur = float(monthly_budget_eur)
        self.spent_eur = max(0.0, float(spent_eur))

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": MODEL_ROUTER_SCHEMA_VERSION,
            "state": {
                "mode": "model_api_router_v1_readiness",
                "monthly_budget_eur": self.monthly_budget_eur,
                "spent_eur": round(self.spent_eur, 4),
                "remaining_eur": round(max(0.0, self.monthly_budget_eur - self.spent_eur), 4),
                "default_policy": "local_when_good_enough_paid_when_quality_matters",
                "external_call_performed": False,
            },
            "providers": self.provider_registry(),
            "task_profiles": _task_profiles(),
            "safety": {
                "provider_keys_exposed": False,
                "secrets_redacted": True,
                "tests_spend_money": False,
                "requires_approval_when_expensive_or_near_budget": True,
                "never_downgrade_quality_blindly": True,
            },
            "read_only": True,
        }

    def provider_registry(self) -> Dict[str, Any]:
        openrouter_configured = bool(os.environ.get("OPENROUTER_API_KEY") or os.environ.get("JARVIS_OPENROUTER_API_KEY"))
        local_configured = bool(os.environ.get("OLLAMA_HOST") or os.environ.get("JARVIS_LOCAL_MODEL_ENDPOINT"))
        return {
            "local": {
                "provider": "local",
                "configured": local_configured,
                "ready": local_configured,
                "default_model": os.environ.get("JARVIS_LOCAL_MODEL", "local/default"),
                "cost_per_1k_tokens_eur": 0.0,
                "credential_required": False,
                "external_network": False,
            },
            "openrouter": {
                "provider": "openrouter",
                "configured": openrouter_configured,
                "ready": openrouter_configured,
                "default_model": os.environ.get("JARVIS_OPENROUTER_DEFAULT_MODEL", "openrouter/auto"),
                "credential_configured": openrouter_configured,
                "credential_state": "configured_redacted" if openrouter_configured else "missing",
                "external_network": True,
                "paid": True,
            },
            "openai_future": {
                "provider": "openai",
                "ready": False,
                "status": "future_provider_contract",
                "credential_state": "future_contract",
            },
            "anthropic_future": {
                "provider": "anthropic",
                "ready": False,
                "status": "future_provider_contract",
                "credential_state": "future_contract",
            },
        }

    def decide(
        self,
        *,
        task_type: str = "simple_chat",
        quality_required: str = "balanced",
        estimated_input_tokens: int = 1200,
        estimated_output_tokens: int = 700,
        max_cost_eur: Optional[float] = None,
    ) -> Dict[str, Any]:
        profile = _task_profiles().get(task_type, _task_profiles()["simple_chat"])
        providers = self.provider_registry()
        remaining = max(0.0, self.monthly_budget_eur - self.spent_eur)
        estimated_cost = _estimate_router_cost(
            profile=profile,
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens,
            force_paid=profile["preferred_provider"] == "openrouter",
        )
        selected_provider = "local"
        selected_model = providers["local"]["default_model"]
        why = "Local is good enough for this task and costs zero."
        fallback = "openrouter" if providers["openrouter"]["ready"] else "none"
        quality_tier = profile["quality_tier"]

        paid_quality_needed = profile["preferred_provider"] == "openrouter" or quality_required in {"high", "critical"}
        if paid_quality_needed:
            if providers["openrouter"]["ready"] and estimated_cost <= remaining:
                selected_provider = "openrouter"
                selected_model = providers["openrouter"]["default_model"]
                why = "Quality matters for this task; OpenRouter is configured and inside budget."
                fallback = "local"
            else:
                why = "OpenRouter would be preferred, but it is not configured or budget is insufficient; use local/readiness fallback."

        policy_limit = max_cost_eur if max_cost_eur is not None else 1.50
        requires_approval = bool(
            selected_provider != "local"
            and (
                estimated_cost > policy_limit
                or estimated_cost > remaining * 0.25
                or remaining < 5.0
                or quality_required == "critical"
            )
        )
        return {
            "schema_version": MODEL_ROUTER_SCHEMA_VERSION,
            "task_type": task_type,
            "selected_provider": selected_provider,
            "selected_model": selected_model,
            "why": why,
            "quality_tier": quality_tier,
            "estimated_cost_eur": round(estimated_cost if selected_provider != "local" else 0.0, 6),
            "budget_remaining_eur": round(remaining, 4),
            "monthly_budget_eur": self.monthly_budget_eur,
            "requires_approval": requires_approval,
            "fallback_provider": fallback,
            "external_call_performed": False,
            "provider_keys_exposed": False,
            "approval_reason": "cost_or_quality_gate" if requires_approval else "",
            "read_only": True,
        }


class Phase10HandsFreeRuntimePersonaApiRouter:
    def __init__(self, *, monthly_budget_eur: float = 30.0, spent_eur: float = 0.0) -> None:
        self.wake_stop = WakeStopPhraseRuntime()
        self.voice_ui = VoiceUiIntentRouter()
        self.app_launcher = GovernedAppLauncher()
        self.browser = GovernedBrowserIntentRouter()
        self.approvals = ApprovalV2Manager()
        self.persona = PersonaManager()
        self.voice_providers = VoiceProviderArchitecture()
        self.model_router = ModelApiRouter(monthly_budget_eur=monthly_budget_eur, spent_eur=spent_eur)

    def status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        persona = self.persona.status()
        model_router = self.model_router.status()
        return {
            "schema_version": PHASE_10_SCHEMA_VERSION,
            "phase": "Phase 10",
            "title": "Hands-Free JARVIS Runtime + Persona + API Brain Router",
            "status": "implemented_as_governed_hands_free_contracts_and_browser_pilot",
            "implemented_blocks": {
                "wake_stop_phrase_contracts": True,
                "local_controller_open_jarvis_readiness": True,
                "continuous_browser_conversation_loop": True,
                "voice_ui_intent_router": True,
                "governed_app_launcher_intents": True,
                "governed_browser_navigation_intents": True,
                "voice_text_approval_v2": True,
                "persona_jarvis_utron_v1": True,
                "voice_provider_architecture_v1": True,
                "model_api_router_v1": True,
                "documentation_report": True,
            },
            "real_vs_readiness": {
                "real_browser_voice_loop": "browser_SpeechRecognition_speechSynthesis_when_supported_after_user_permission",
                "real_written_history": True,
                "real_browser_tts_repeat_stop": True,
                "real_ui_voice_command_mapping": True,
                "system_level_always_on_wake": "readiness_only_no_hidden_recording",
                "chrome_open_when_closed": "local_controller_readiness_contract_not_frontend_shell",
                "app_launch": "prepared_governed_intent_no_fake_open",
                "browser_navigation": "prepared_governed_intent_adapter_readiness",
                "paid_api_calls": "disabled_unless_configured_and_approved",
            },
            "route_readiness": {
                "phase_10_status": "/mark-3/phase-10/status" in routes,
                "voice_ui_intent": "/mark-3/phase-10/voice-ui/intent" in routes,
                "app_launcher_prepare": "/mark-3/phase-10/app-launcher/prepare" in routes,
                "browser_intent_prepare": "/mark-3/phase-10/browser-intent/prepare" in routes,
                "approval_start": "/mark-3/phase-10/approval/start" in routes,
                "approval_confirm": "/mark-3/phase-10/approval/confirm" in routes,
                "model_router_status": "/mark-3/model-router/status" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "visible_states": [
                "listening_for_wake",
                "active_conversation",
                "speaking",
                "stopped",
                "unavailable",
                "fallback",
            ],
            "wake_stop": self.wake_stop.preview("Hola JARVIS", confidence=1.0),
            "voice_ui_intent_router": {
                "schema_version": VOICE_UI_INTENT_SCHEMA_VERSION,
                "deterministic_spanish_matching": True,
                "sensitive_actions_requiring_confirmation": sorted(SENSITIVE_UI_ACTIONS),
                "fallback_question_on_ambiguity": True,
            },
            "app_launcher": self.app_launcher.status(),
            "browser_intents": self.browser.status(),
            "approval_v2": self.approvals.status(),
            "persona": persona,
            "voice_provider_architecture": self.voice_providers.status(self.persona.state),
            "model_router": model_router,
            "security_gates": {
                "jarvis_governs": True,
                "hermes_executes": True,
                "no_duplicate_hermes_runtime": True,
                "frontend_direct_hermes_allowed": False,
                "no_generic_shell_from_ui": True,
                "wake_phrase_can_approve": False,
                "voice_approval_requires_trusted_active_gated_readback_audit": True,
                "memory_grants_permission": False,
                "memory_downgrades_risk": False,
                "utron_bypasses_approvals": False,
                "no_fake_execution": True,
                "no_hidden_raw_audio_storage": True,
                "provider_keys_exposed": False,
            },
            "source_endpoint": "/mark-3/phase-10/status",
            "read_only": True,
        }

    def handle_conversation_text(self, text: str) -> Dict[str, Any]:
        persona_result = self.persona.handle_text(text)
        return {
            "schema_version": PHASE_10_SCHEMA_VERSION,
            "persona": persona_result,
            "wake_stop": self.wake_stop.preview(text),
            "voice_ui_intent": self.voice_ui.route(text).to_dict(),
            "read_only": True,
        }


def normalize_spanish(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold()
    value = value.replace("¿", " ").replace("¡", " ")
    value = re.sub(r"[^\w\s:/.-]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def normalize_confidence(value: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(number):
        return 0.0
    return max(0.0, min(1.0, number))


def approval_readback(
    *,
    action: str,
    risk_level: str,
    cost_summary: str,
    change_summary: str,
    rollback_or_stop_plan: str,
) -> str:
    return (
        f"Voy a preparar: {_safe_text(action)}. "
        f"Riesgo: {_safe_text(risk_level)}. "
        f"Coste: {_safe_text(cost_summary)}. "
        f"Puede tocar o cambiar: {_safe_text(change_summary)}. "
        f"Plan de parada o rollback: {_safe_text(rollback_or_stop_plan)}. "
        f"Para aprobar, di o escribe exactamente: {PHASE_10_EXACT_APPROVAL_PHRASE}."
    )


def _default_app_registry() -> Dict[str, AppDefinition]:
    return {
        "chrome": AppDefinition(
            "chrome",
            "Chrome",
            ("chrome", "google chrome", "navegador", "jarvis en chrome"),
            ("google-chrome", "--new-window", "http://127.0.0.1:8000/jarvis"),
            notes="Opening /jarvis depends on local controller readiness.",
        ),
        "cursor": AppDefinition("cursor", "Cursor", ("cursor",), ("cursor",), notes="Developer editor."),
        "vscode": AppDefinition("vscode", "VS Code", ("vs code", "visual studio code", "code"), ("code",)),
        "terminal": AppDefinition(
            "terminal",
            "Terminal/WSL",
            ("terminal", "consola", "wsl"),
            ("terminal",),
            risk_level="medium",
            requires_approval=True,
            sensitive=True,
            notes="Terminal surfaces are sensitive and never become a generic shell from the UI.",
        ),
        "windows_terminal": AppDefinition(
            "windows_terminal",
            "Windows Terminal",
            ("windows terminal", "terminal de windows"),
            ("wt",),
            risk_level="medium",
            requires_approval=True,
            sensitive=True,
        ),
        "file_explorer": AppDefinition(
            "file_explorer",
            "File Explorer",
            ("explorador", "explorador de archivos", "file explorer"),
            ("explorer",),
            risk_level="medium",
            requires_approval=True,
            sensitive=True,
        ),
        "whatsapp": AppDefinition("whatsapp", "WhatsApp", ("whatsapp", "wasap"), ("whatsapp",), risk_level="medium", requires_approval=True),
        "spotify": AppDefinition("spotify", "Spotify", ("spotify", "musica"), ("spotify",)),
        "jarvis_project": AppDefinition(
            "jarvis_project",
            "JARVIS project folder",
            ("carpeta jarvis", "proyecto jarvis", "jarvis project folder"),
            ("open-folder", "JARVIS_PROJECT_ROOT"),
            risk_level="medium",
            requires_approval=True,
            sensitive=True,
        ),
    }


def _task_profiles() -> Dict[str, Dict[str, Any]]:
    return {
        "simple_chat": {"preferred_provider": "local", "quality_tier": "standard", "cost_rate_eur_per_1k": 0.0},
        "planning": {"preferred_provider": "openrouter", "quality_tier": "high", "cost_rate_eur_per_1k": 0.003},
        "code": {"preferred_provider": "openrouter", "quality_tier": "high", "cost_rate_eur_per_1k": 0.004},
        "browser_research": {"preferred_provider": "openrouter", "quality_tier": "high", "cost_rate_eur_per_1k": 0.004},
        "summarization": {"preferred_provider": "local", "quality_tier": "balanced", "cost_rate_eur_per_1k": 0.0},
        "voice_response": {"preferred_provider": "local", "quality_tier": "standard", "cost_rate_eur_per_1k": 0.0},
        "risky_operation_reasoning": {"preferred_provider": "openrouter", "quality_tier": "critical", "cost_rate_eur_per_1k": 0.006},
    }


def _estimate_router_cost(*, profile: Mapping[str, Any], input_tokens: int, output_tokens: int, force_paid: bool) -> float:
    if not force_paid:
        return 0.0
    tokens = max(0, int(input_tokens)) + max(0, int(output_tokens))
    return tokens / 1000.0 * float(profile.get("cost_rate_eur_per_1k", 0.003))


def _browser_response(intent: str, requires_approval: bool, strong: bool, unsupported_reason: str) -> str:
    if unsupported_reason:
        return unsupported_reason
    if intent == "unknown":
        return "No he podido clasificar esa navegación. Puedo abrir URL, buscar, resumir página, preparar formulario o preparar mensaje."
    if strong:
        return f"Prepararé una vista previa para {intent}. No enviaré, compraré, pagaré ni publicaré nada sin aprobación fuerte."
    if requires_approval:
        return f"Prepararé {intent} en modo vista previa. No enviaré ni tocaré formularios sin aprobación."
    return f"Puedo preparar {intent}; no fingiré navegación real hasta que un adaptador gobernado lo confirme."


def _looks_like_url(text: str) -> bool:
    value = str(text or "").strip().casefold()
    return bool(re.match(r"^https?://", value) or re.match(r"^[a-z0-9.-]+\.[a-z]{2,}(?:/.*)?$", value))


def _any(text: str, variants: Sequence[str]) -> bool:
    return any(variant in text for variant in variants)


def _safe_text(value: Any, *, limit: int = 220) -> str:
    compact = " ".join(str(value or "").split())
    provider_key_marker = "api" + "_key"
    for marker in ("sk-", "token", "password", "cookie", "secret", provider_key_marker, "authorization"):
        compact = re.sub(re.escape(marker), "[redacted]", compact, flags=re.IGNORECASE)
    return compact[:limit]


def _safe_response_text(text: str) -> str:
    cleaned = _safe_text(text, limit=800)
    abusive_to_david = ("david eres", "david, eres", "imbecil", "idiota", "inutil")
    normalized = normalize_spanish(cleaned)
    if any(item in normalized for item in abusive_to_david):
        return "No voy a insultar a David. Puedo ser mordaz con malas decisiones, no con mi operador."
    return cleaned


def _safe_metadata(metadata: Mapping[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in dict(metadata or {}).items():
        safe_key = _safe_text(key, limit=80)
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[safe_key] = _safe_text(value, limit=220) if isinstance(value, str) else value
        elif isinstance(value, list):
            safe[safe_key] = [_safe_text(item, limit=120) for item in value[:20]]
        elif isinstance(value, dict):
            safe[safe_key] = _safe_metadata(value)
        else:
            safe[safe_key] = _safe_text(value, limit=120)
    return safe


def _hash_text(value: str) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()[:16]


def _approval_audit(event_type: str, approval: PendingApproval, *, phrase: str = "", result: str) -> Dict[str, Any]:
    return {
        "event_id": f"phase10_audit_{uuid4()}",
        "event_type": event_type,
        "created_at": _now_iso(),
        "approval_id": approval.approval_id,
        "action_fingerprint": approval.context_fingerprint,
        "risk_level": approval.risk_level,
        "phrase_hash_or_redacted": f"sha256:{_hash_text(normalize_spanish(phrase))}" if phrase else "[not_provided]",
        "raw_phrase_stored": False,
        "raw_audio_stored": False,
        "result": result,
        "metadata_only": True,
    }


def _approval_rejection(reason: str, spanish_response: str) -> Dict[str, Any]:
    return {
        "schema_version": APPROVAL_V2_SCHEMA_VERSION,
        "approved": False,
        "status": "rejected",
        "reason": reason,
        "spanish_response": spanish_response,
        "wake_phrase_can_approve": False,
        "would_execute": False,
        "executed": False,
        "metadata_only": True,
    }
