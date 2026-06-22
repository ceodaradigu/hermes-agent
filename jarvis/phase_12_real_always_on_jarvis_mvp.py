from __future__ import annotations

import importlib.util
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib import request as urllib_request
from urllib.parse import quote_plus, urlparse
from uuid import uuid4

from hermes_constants import get_hermes_home, is_wsl
from jarvis.phase_10_hands_free_runtime_persona_api_router import (
    PHASE_10_EXACT_APPROVAL_PHRASE,
    Phase10HandsFreeRuntimePersonaApiRouter,
    normalize_confidence,
    normalize_spanish,
)
from jarvis.phase_11_real_provider_controller_iphone_companion import (
    DEFAULT_MONTHLY_BUDGET_EUR,
    Phase11RealProviderControllerIPhoneCompanion,
)
from jarvis.phase_12_ports import (
    BACKEND_BASE_URL,
    BACKEND_PORT,
    FRONTEND_BASE_URL,
    FRONTEND_PORT,
    JARVIS_FRONTEND_URL,
    MOBILE_FRONTEND_URL,
    frontend_url,
)
from jarvis.phase_12_wake_listener import build_wake_listener_status, match_wake_phrase


PHASE_12_SCHEMA_VERSION = "jarvis.phase_12_real_always_on_mvp.v1"
PHASE_12_WAKE_SCHEMA_VERSION = "jarvis.phase_12.always_on_runtime.v1"
PHASE_12_CONVERSATION_SCHEMA_VERSION = "jarvis.phase_12.conversation_brain.v1"
PHASE_12_ACTION_SCHEMA_VERSION = "jarvis.phase_12.governed_actions.v1"
PHASE_12_REMOTE_SCHEMA_VERSION = "jarvis.phase_12.secure_remote_bridge.v1"
PHASE_12_VOICE_SCHEMA_VERSION = "jarvis.phase_12.voice_stack.v1"
PHASE_12_STARTUP_SCHEMA_VERSION = "jarvis.phase_12.startup_contract.v1"

WAKE_PHRASES_ES = ("jarvis", "hola jarvis")
STOP_PHRASES_ES = ("jarvis para", "para", "jarvis callate", "callate", "jarvis cállate", "cállate")
VOICE_UI_VARIANTS = {
    "ui.panel.open": ("abre panel", "abre el panel", "muestra panel", "ensename panel", "enséñame panel"),
    "ui.panel.close": ("cierra panel", "cierra el panel", "oculta panel", "quita panel"),
    "voice.activate": ("activa voz", "enciende voz", "pon voz"),
    "voice.deactivate": ("desactiva voz", "apaga voz", "sin voz"),
    "voice.repeat": ("repite", "repiteme", "repíteme", "dilo otra vez"),
    "voice.stop": ("para voz", "deten voz", "cállate", "callate", "silencio"),
    "camera.start": ("abre camara", "abre cámara", "enciende camara", "activa cámara"),
    "camera.stop": ("cierra camara", "cierra cámara", "apaga camara", "apaga cámara"),
    "audio.start": ("graba audio", "empieza grabacion audio", "empieza grabación audio"),
    "audio.stop": ("para grabacion", "deten grabacion", "deja de grabar"),
    "status.review": ("estado", "revisa estado", "comprueba estado", "status"),
    "cancel": ("cancela", "cancelar", "para", "detente"),
    "persona.utron": ("activa modo utron", "modo utron"),
    "persona.jarvis": ("desactiva utron", "quita utron", "modo jarvis"),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, fallback: str = "", *, limit: int = 800) -> str:
    text = " ".join(str(value if value is not None else fallback).split())
    if not text:
        text = fallback
    return _redact_secrets(text)[: max(1, int(limit))]


def _redact_secrets(value: Any) -> str:
    text = str(value or "")
    patterns = (
        r"\bsk-[A-Za-z0-9_-]{8,}\b",
        r"\bsk-or-[A-Za-z0-9_-]{8,}\b",
        r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{12,}\b",
        r"\b(?:api[_-]?key|token|secret|password|authorization|bearer)\s*[:=]\s*['\"]?[^'\"\s,;]+",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
    )
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, "[redacted]", redacted, flags=re.IGNORECASE)
    return redacted


def _safe_metadata(metadata: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in dict(metadata or {}).items():
        clean_key = _safe_text(key, limit=80)
        lower = clean_key.casefold()
        if any(marker in lower for marker in ("password", "secret", "token", "api_key", "apikey", "authorization", "cookie")):
            safe[clean_key] = "[redacted]"
        elif isinstance(value, Mapping):
            safe[clean_key] = _safe_metadata(value)
        elif isinstance(value, (list, tuple, set)):
            safe[clean_key] = [_safe_text(item, limit=160) for item in list(value)[:20]]
        elif isinstance(value, bool):
            safe[clean_key] = value
        elif isinstance(value, (int, float)):
            safe[clean_key] = value if math.isfinite(float(value)) else "unknown"
        else:
            safe[clean_key] = _safe_text(value, limit=220)
    return safe


def _env_bool(name: str, default: bool = False, *, env: Optional[Mapping[str, str]] = None) -> bool:
    source = env if env is not None else os.environ
    raw = str(source.get(name, "")).strip().casefold()
    if raw in {"1", "true", "yes", "on", "enabled"}:
        return True
    if raw in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _voice_output_default_enabled(env: Optional[Mapping[str, str]] = None) -> bool:
    source = env if env is not None else os.environ
    if "JARVIS_VOICE_OUTPUT_DEFAULT_ON" in source:
        return _env_bool("JARVIS_VOICE_OUTPUT_DEFAULT_ON", True, env=source)
    return _env_bool("JARVIS_VOICE_DEFAULT_ON", True, env=source)


def _env_float(name: str, default: float, *, env: Optional[Mapping[str, str]] = None) -> float:
    source = env if env is not None else os.environ
    try:
        value = float(source.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if math.isfinite(value) else default


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


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
    return value


def _looks_like_url(text: Any) -> bool:
    value = str(text or "").strip()
    return bool(re.match(r"^https?://", value, re.I) or re.match(r"^[a-z0-9.-]+\.[a-z]{2,}(?:/.*)?$", value, re.I))


def _search_url(query: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(query)}"


def _origin(url: str) -> str:
    parsed = urlparse(str(url or ""))
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""


class Phase12AuditLog:
    def __init__(self, *, limit: int = 300) -> None:
        self.limit = max(20, int(limit))
        self._events: List[Dict[str, Any]] = []

    def record(
        self,
        event_type: str,
        *,
        surface: str,
        result: str,
        risk_level: str = "low",
        channel: str = "desktop",
        action_id: str = "",
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        event = {
            "schema_version": PHASE_12_SCHEMA_VERSION,
            "event_id": f"phase12_audit_{uuid4()}",
            "created_at": _now_iso(),
            "event_type": _safe_text(event_type, limit=100),
            "surface": _safe_text(surface, limit=100),
            "result": _safe_text(result, limit=160),
            "risk_level": _safe_text(risk_level, "low", limit=40),
            "channel": _safe_text(channel, "desktop", limit=80),
            "action_id": _safe_text(action_id, limit=120),
            "metadata": _safe_metadata(metadata),
            "contains_secret": False,
            "contains_raw_audio": False,
            "metadata_only": True,
        }
        self._events.append(event)
        if len(self._events) > self.limit:
            self._events = self._events[-self.limit :]
        return dict(event)

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        return list(self._events[-max(1, int(limit)) :])

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_12_SCHEMA_VERSION,
            "event_count": len(self._events),
            "recent": self.recent(10),
            "contains_secret": False,
            "contains_raw_audio": False,
            "metadata_only": True,
        }


class AlwaysOnLocalRuntime:
    def __init__(
        self,
        *,
        phase10: Phase10HandsFreeRuntimePersonaApiRouter,
        phase11: Phase11RealProviderControllerIPhoneCompanion,
        audit: Phase12AuditLog,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.phase10 = phase10
        self.phase11 = phase11
        self.audit = audit
        self.env = env if env is not None else os.environ
        self.runtime_id = f"phase12_always_on_{uuid4()}"
        self.enabled = False
        self.conversation_active = False
        self.wake_listening = False
        self.last_wake_event: Optional[Dict[str, Any]] = None
        self.last_wake_greeting: Optional[Dict[str, Any]] = None
        self.last_stop_event: Optional[Dict[str, Any]] = None
        self.last_ui_presence: Optional[Dict[str, Any]] = None
        self.last_ui_presence_epoch = 0.0
        self.last_browser_open_epoch = 0.0
        self.last_browser_open_at: Optional[str] = None
        self.started_at: Optional[str] = None
        self.stopped_at: Optional[str] = None

    def _ui_presence_ttl_seconds(self) -> float:
        return _env_float("JARVIS_UI_PRESENCE_TTL_SECONDS", 18.0, env=self.env)

    def _browser_open_cooldown_seconds(self) -> float:
        return _env_float("JARVIS_WAKE_BROWSER_OPEN_COOLDOWN_SECONDS", 20.0, env=self.env)

    def _ui_presence_recent(self, *, now_epoch: Optional[float] = None) -> bool:
        if not self.last_ui_presence:
            return False
        now = time.time() if now_epoch is None else now_epoch
        path = str(self.last_ui_presence.get("path") or "")
        visible = self.last_ui_presence.get("visible", True) is not False
        return bool(visible and "/jarvis" in path and now - self.last_ui_presence_epoch <= self._ui_presence_ttl_seconds())

    def _browser_open_cooldown_active(self, *, now_epoch: Optional[float] = None) -> bool:
        if self.last_browser_open_epoch <= 0:
            return False
        now = time.time() if now_epoch is None else now_epoch
        return now - self.last_browser_open_epoch <= self._browser_open_cooldown_seconds()

    def _wake_open_decision(self, *, open_jarvis: bool) -> Dict[str, Any]:
        now = time.time()
        always_open = _env_bool("JARVIS_WAKE_ALWAYS_OPEN_BROWSER", False, env=self.env)
        ui_recent = self._ui_presence_recent(now_epoch=now)
        cooldown = self._browser_open_cooldown_active(now_epoch=now)
        should_open = bool(open_jarvis and (always_open or not ui_recent) and not cooldown)
        reason = "open_requested"
        if not open_jarvis:
            reason = "open_not_requested"
        elif cooldown:
            reason = "skipped_open_cooldown"
        elif ui_recent and not always_open:
            reason = "skipped_recent_ui_presence"
        elif always_open:
            reason = "always_open_configured"
        return {
            "requested": bool(open_jarvis),
            "should_open": should_open,
            "reason": reason,
            "ui_presence_recent": ui_recent,
            "browser_open_cooldown_active": cooldown,
            "always_open_configured": always_open,
            "cooldown_seconds": self._browser_open_cooldown_seconds(),
            "ui_presence_ttl_seconds": self._ui_presence_ttl_seconds(),
            "last_browser_open_at": self.last_browser_open_at,
            "raw_audio_stored": False,
        }

    def record_ui_presence(
        self,
        *,
        client_id: str = "jarvis_ui",
        surface: str = "jarvis",
        path: str = "/jarvis",
        visible: bool = True,
        channel: str = "jarvis_ui",
    ) -> Dict[str, Any]:
        self.last_ui_presence_epoch = time.time()
        self.last_ui_presence = {
            "schema_version": "jarvis.phase_12.ui_presence.v1",
            "client_id": _safe_text(client_id, fallback="jarvis_ui", limit=120),
            "surface": _safe_text(surface, fallback="jarvis", limit=80),
            "path": _safe_text(path, fallback="/jarvis", limit=200),
            "visible": bool(visible),
            "channel": _safe_text(channel, fallback="jarvis_ui", limit=80),
            "last_seen_at": _now_iso(),
            "ttl_seconds": self._ui_presence_ttl_seconds(),
            "recent": True,
            "raw_audio_stored": False,
            "frontend_executes_hermes": False,
        }
        return {
            "schema_version": "jarvis.phase_12.ui_presence.v1",
            "status": "recorded",
            "ui_presence": self.last_ui_presence,
        }

    def claim_pending_greeting(
        self,
        *,
        client_id: str = "jarvis_ui",
        channel: str = "jarvis_ui",
        speak_supported: bool = False,
    ) -> Dict[str, Any]:
        greeting = self.last_wake_greeting
        if not greeting or greeting.get("status") != "pending":
            return {
                "schema_version": "jarvis.phase_12.wake_greeting_claim.v1",
                "status": "no_pending_greeting",
                "greeting": None,
                "raw_audio_stored": False,
                "wake_phrase_can_approve": False,
            }
        delivered = {
            **greeting,
            "status": "delivered",
            "delivered_at": _now_iso(),
            "delivered_to_client_id": _safe_text(client_id, fallback="jarvis_ui", limit=120),
            "delivered_channel": _safe_text(channel, fallback="jarvis_ui", limit=80),
            "browser_tts_supported_at_claim": bool(speak_supported),
            "wake_phrase_can_approve": False,
            "wake_phrase_can_execute": False,
            "did_execute_action": False,
        }
        self.last_wake_greeting = delivered
        return {
            "schema_version": "jarvis.phase_12.wake_greeting_claim.v1",
            "status": "delivered",
            "assistant_text": delivered["assistant_text"],
            "greeting": delivered,
            "raw_audio_stored": False,
            "wake_phrase_can_approve": False,
            "wake_phrase_can_execute": False,
        }

    def dependency_status(self) -> Dict[str, Any]:
        wake_listener = build_wake_listener_status(env=self.env)
        return {
            "openwakeword_installed": wake_listener["engine"]["openwakeword_package_available"],
            "vosk_installed": wake_listener["engine"]["vosk_package_available"],
            "sounddevice_installed": wake_listener["microphone"]["sounddevice_available"],
            "numpy_installed": wake_listener["engine"]["numpy_available"],
            "optional_audio_wake_loop_available": wake_listener["state"]["real_microphone_wake_available"],
            "real_microphone_wake_active": wake_listener["state"]["wake_active"],
            "selected_backend": wake_listener["state"]["selected_backend"],
            "builtin_openwakeword_phrase_note": "openWakeWord/custom wake models remain optional; Phase 12 guarantees the shorter JARVIS wake path first.",
            "custom_wake_model_path_configured": wake_listener["engine"]["model_path_configured"],
            "custom_hola_jarvis_model_path_configured": wake_listener["engine"]["model_path_configured"],
            "no_dependency_install_performed": True,
            "no_model_download_performed": True,
            "diagnostic_es": wake_listener["diagnostic"]["spanish"],
            "wake_contract": wake_listener.get("wake_contract", {}),
        }

    def status(self) -> Dict[str, Any]:
        deps = self.dependency_status()
        return {
            "schema_version": PHASE_12_WAKE_SCHEMA_VERSION,
            "runtime_id": self.runtime_id,
            "state": {
                "mode": "local_always_on_controller_pilot",
                "enabled": self.enabled,
                "wake_listening": self.wake_listening,
                "conversation_active": self.conversation_active,
                "wake_greeting_available": bool(self.last_wake_greeting),
                "pending_wake_greeting": bool(self.last_wake_greeting and self.last_wake_greeting.get("status") == "pending"),
                "ui_presence_recent": self._ui_presence_recent(),
                "started_at": self.started_at,
                "stopped_at": self.stopped_at,
                "backend_port": BACKEND_PORT,
                "frontend_port": FRONTEND_PORT,
                "opens_route_on_wake": "/jarvis",
                "opens_url_on_wake": JARVIS_FRONTEND_URL,
                "backend_api_url": BACKEND_BASE_URL,
                "frontend_url": FRONTEND_BASE_URL,
                "real_microphone_wake_available": deps["optional_audio_wake_loop_available"],
                "real_microphone_wake_active": deps["real_microphone_wake_active"],
            },
            "primary_wake_phrase": "JARVIS",
            "supported_wake_phrases": ["JARVIS"],
            "experimental_wake_aliases": ["Hola JARVIS"],
            "experimental_aliases_best_effort": True,
            "supported_stop_phrases": ["JARVIS, para", "para", "JARVIS, cállate", "cállate"],
            "dependencies": deps,
            "privacy": {
                "hidden_raw_audio_storage": False,
                "raw_audio_stored_by_default": False,
                "continuous_full_transcription_by_default": False,
                "wake_listening_separated_from_active_transcription": True,
                "wake_metadata_visible": True,
                "raw_audio_recording_requires_explicit_opt_in": True,
            },
            "approval": {
                "wake_phrase_can_approve": False,
                "wake_phrase_can_execute": False,
                "exact_confirmation_phrase": PHASE_10_EXACT_APPROVAL_PHRASE,
            },
            "real_vs_readiness": {
                "real": [
                    "stateful local always-on controller lifecycle",
                    "primary JARVIS wake and stop phrase detection over daemon events and explicit test transcript ingest",
                    "wake greeting state for visible/spoken UI response when /jarvis is active",
                    "governed /jarvis open request through the Phase 11 local controller",
                    "metadata-only audit of wake, stop and lifecycle events",
                ],
                "optional": [
                    "scripts/jarvis-wake-listener runs a real openWakeWord microphone loop when openwakeword, sounddevice, numpy and a local model path are installed",
                    "scripts/jarvis-wake-listener runs a real local Vosk microphone STT wake loop for the primary JARVIS phrase when vosk, sounddevice and a Spanish model path are configured",
                    "Hola JARVIS remains a best-effort alias when the local STT transcript is favorable",
                ],
                "readiness": [
                    "Longer phrase aliases such as Hola JARVIS are not guaranteed with Vosk; use JARVIS as the Phase 12 wake contract",
                    "the transcript ingest endpoint is for tests/dev injection and is not a substitute for always-on microphone wake",
                ],
            },
            "wake_listener": build_wake_listener_status(env=self.env),
            "transcript_ingest_endpoint": {
                "path": "/mark-3/phase-12/always-on/ingest-transcript",
                "test_only": True,
                "substitute_for_real_microphone_wake": False,
            },
            "last_wake_event": self.last_wake_event,
            "last_wake_greeting": self.last_wake_greeting,
            "ui_presence": {
                "last": self.last_ui_presence,
                "recent": self._ui_presence_recent(),
                "ttl_seconds": self._ui_presence_ttl_seconds(),
            },
            "browser_open": {
                "last_open_at": self.last_browser_open_at,
                "cooldown_seconds": self._browser_open_cooldown_seconds(),
                "cooldown_active": self._browser_open_cooldown_active(),
                "always_open_configured": _env_bool("JARVIS_WAKE_ALWAYS_OPEN_BROWSER", False, env=self.env),
            },
            "last_stop_event": self.last_stop_event,
            "source_endpoint": "/mark-3/phase-12/always-on/status",
            "metadata_only": True,
        }

    def _build_wake_greeting(self, *, source: str, matched_wake_phrase: str, confidence: float) -> Dict[str, Any]:
        persona = self.phase10.persona.state
        if persona.mode == "utron":
            text = "UTRON activo. Habla, David, antes de que la humanidad vuelva a decepcionarme."
        else:
            text = "Estoy aquí, David. Te escucho."
        return {
            "schema_version": "jarvis.phase_12.wake_greeting.v1",
            "greeting_id": f"phase12_wake_greeting_{uuid4()}",
            "created_at": _now_iso(),
            "status": "pending",
            "speaker": persona.visible_name,
            "persona_mode": persona.mode,
            "assistant_text": text,
            "voice_output_requested": True,
            "voice_output_available": "browser_or_configured_local_tts",
            "conversation_active": True,
            "source": source,
            "matched_wake_phrase": matched_wake_phrase,
            "confidence": normalize_confidence(confidence),
            "raw_audio_stored": False,
            "approval_granted": False,
            "wake_phrase_can_approve": False,
            "wake_phrase_can_execute": False,
            "did_execute_action": False,
            "metadata_only": True,
        }

    def start(self, *, actor: str = "David", channel: str = "desktop") -> Dict[str, Any]:
        self.enabled = True
        self.wake_listening = True
        self.started_at = _now_iso()
        self.stopped_at = None
        audit = self.audit.record(
            "phase12_always_on_started",
            surface="always_on_runtime",
            channel=channel,
            result="wake_listening",
            metadata={"actor": actor, "backend_port": BACKEND_PORT, "frontend_port": FRONTEND_PORT},
        )
        return {
            **self.status(),
            "status": "started",
            "spanish_response": "JARVIS queda activo en este PC. Escucha solo wake metadata; la transcripción completa empieza después de activación.",
            "audit_id": audit["event_id"],
        }

    def stop(self, *, actor: str = "David", channel: str = "desktop", reason: str = "operator_stop") -> Dict[str, Any]:
        self.enabled = False
        self.wake_listening = False
        self.conversation_active = False
        self.stopped_at = _now_iso()
        audit = self.audit.record(
            "phase12_always_on_stopped",
            surface="always_on_runtime",
            channel=channel,
            result="stopped",
            metadata={"actor": actor, "reason": reason},
        )
        self.last_stop_event = audit
        return {
            **self.status(),
            "status": "stopped",
            "spanish_response": "JARVIS queda detenido. No hay escucha de wake ni conversación activa.",
            "audit_id": audit["event_id"],
        }

    def ingest_transcript(
        self,
        *,
        text: str,
        confidence: float = 1.0,
        source: str = "wake_daemon_text_event",
        open_jarvis: bool = True,
    ) -> Dict[str, Any]:
        normalized = normalize_spanish(text)
        stop_phrase = _match_stop(normalized)
        if stop_phrase:
            self.conversation_active = False
            self.wake_listening = self.enabled
            audit = self.audit.record(
                "phase12_stop_phrase_detected",
                surface="always_on_runtime",
                result="stopped_conversation",
                metadata={"source": source, "matched_stop_phrase": stop_phrase},
            )
            self.last_stop_event = audit
            return {
                "schema_version": PHASE_12_WAKE_SCHEMA_VERSION,
                "status": "stopped_conversation",
                "conversation_active": False,
                "wake_listening": self.wake_listening,
                "matched_stop_phrase": stop_phrase,
                "opened_jarvis": False,
                "approval_granted": False,
                "wake_phrase_can_approve": False,
                "raw_audio_stored": False,
                "audit_id": audit["event_id"],
                "spanish_response": "Paro la conversación. Sigo en espera si el runtime está activo.",
            }

        phase12_match = match_wake_phrase(text)
        if phase12_match["accepted"]:
            preview = {
                "wake_phrase_detected": True,
                "matched_wake_phrase": phase12_match["matched_wake_phrase"],
                "extracted_command": "",
                "phase12_match": phase12_match,
            }
        else:
            preview = self.phase10.wake_stop.preview(text, confidence=confidence)
            preview["phase12_match"] = phase12_match
        wake_detected = bool(preview.get("wake_phrase_detected"))
        opened = False
        launch_result: Dict[str, Any] = {}
        open_decision: Dict[str, Any] = {}
        if wake_detected:
            self.enabled = True
            self.wake_listening = True
            self.conversation_active = True
            greeting = self._build_wake_greeting(
                source=source,
                matched_wake_phrase=str(preview.get("matched_wake_phrase") or ""),
                confidence=confidence,
            )
            open_decision = self._wake_open_decision(open_jarvis=open_jarvis)
            if open_decision["should_open"]:
                candidate = self.phase11.local_controller.prepare_launch(app_name="Chrome", actor="David", channel=source)
                if candidate.get("candidate_id"):
                    launch_result = self.phase11.local_controller.launch(
                        candidate_id=candidate["candidate_id"],
                        actor="David",
                        trusted_session=True,
                    )
                    opened = bool(launch_result.get("executed"))
                    if opened:
                        self.last_browser_open_epoch = time.time()
                        self.last_browser_open_at = _now_iso()
                        launch_result["browser_open_recorded_at"] = self.last_browser_open_at
            else:
                launch_result = {
                    "status": "skipped",
                    "reason": open_decision["reason"],
                    "executed": False,
                    "open_decision": open_decision,
                }
            audit = self.audit.record(
                "phase12_wake_phrase_detected",
                surface="always_on_runtime",
                result="conversation_active",
                metadata={
                    "source": source,
                    "matched_wake_phrase": preview.get("matched_wake_phrase"),
                    "phase12_match_reason": phase12_match.get("reason"),
                    "opened_jarvis": opened,
                    "open_skipped_reason": open_decision.get("reason", "") if not opened else "",
                    "launch_status": launch_result.get("status", ""),
                    "greeting_id": greeting["greeting_id"],
                    "greeting_text": greeting["assistant_text"],
                    "persona_mode": greeting["persona_mode"],
                },
            )
            self.last_wake_event = audit
            greeting["audit_id"] = audit["event_id"]
            self.last_wake_greeting = greeting
            return {
                "schema_version": PHASE_12_WAKE_SCHEMA_VERSION,
                "status": "conversation_active",
                "wake_phrase_detected": True,
                "conversation_active": True,
                "opened_jarvis": opened,
                "open_decision": open_decision,
                "launch_result": launch_result,
                "phase12_match": phase12_match,
                "extracted_command": preview.get("extracted_command", ""),
                "approval_granted": False,
                "wake_phrase_can_approve": False,
                "wake_phrase_can_execute": False,
                "raw_audio_stored": False,
                "audit_id": audit["event_id"],
                "assistant_text": greeting["assistant_text"],
                "greeting": greeting,
                "spanish_response": greeting["assistant_text"],
            }

        return {
            "schema_version": PHASE_12_WAKE_SCHEMA_VERSION,
            "status": "ignored_no_wake_phrase",
            "wake_phrase_detected": False,
            "conversation_active": self.conversation_active,
            "opened_jarvis": False,
            "approval_granted": False,
            "wake_phrase_can_approve": False,
            "raw_audio_stored": False,
            "spanish_response": "Sigo esperando 'JARVIS'. 'Hola JARVIS' queda como alias experimental según reconocimiento local.",
        }


def _match_stop(normalized: str) -> str:
    compact = normalized.strip(" ,;:!.?")
    for phrase in STOP_PHRASES_ES:
        if compact == normalize_spanish(phrase):
            return phrase
    return ""


class _UrllibOpenRouterHTTP:
    def post(self, url: str, *, headers: Mapping[str, str], json_payload: Mapping[str, Any], timeout: int) -> Dict[str, Any]:
        body = json.dumps(dict(json_payload)).encode("utf-8")
        request = urllib_request.Request(url, data=body, method="POST", headers=dict(headers))
        with urllib_request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))


class Phase12ConversationBrain:
    def __init__(
        self,
        *,
        phase10: Phase10HandsFreeRuntimePersonaApiRouter,
        phase11: Phase11RealProviderControllerIPhoneCompanion,
        audit: Phase12AuditLog,
        env: Optional[Mapping[str, str]] = None,
        http_post: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.phase10 = phase10
        self.phase11 = phase11
        self.audit = audit
        self.env = env if env is not None else os.environ
        self.http_post = http_post
        self._history: Dict[str, List[Dict[str, Any]]] = {}

    def status(self) -> Dict[str, Any]:
        providers = self.phase11.providers.status()
        return {
            "schema_version": PHASE_12_CONVERSATION_SCHEMA_VERSION,
            "state": {
                "mode": "router_backed_conversation_brain",
                "spanish_default": True,
                "conversation_history_enabled": True,
                "persistent_safe_summary_enabled": False,
                "openrouter_configured": providers["summary"]["openrouter_configured"],
                "openrouter_live_calls_enabled": providers["providers"]["openrouter"]["paid_calls_enabled"],
                "fallback_deterministic_when_no_provider": True,
            },
            "provider_status": providers,
            "persona": self.phase10.persona.status(),
            "safety": {
                "no_live_paid_call_in_tests_by_default": True,
                "budget_guard_monthly_eur": DEFAULT_MONTHLY_BUDGET_EUR,
                "memory_grants_permission": False,
                "memory_downgrades_risk": False,
                "frontends_call_this_brain_not_hermes": True,
                "hermes_dispatch_allowed": False,
            },
            "source_endpoint": "/mark-3/phase-12/conversation/status",
        }

    def turn(
        self,
        *,
        user_text: str,
        conversation_id: str = "jarvis",
        channel: str = "desktop",
        source: str = "typed_text",
        transcript_confidence: float = 1.0,
    ) -> Dict[str, Any]:
        text = _safe_text(user_text, limit=2000)
        phase10_result = self.phase10.handle_conversation_text(text)
        persona_response = phase10_result.get("persona", {}).get("response") or ""
        task = self.phase11.model_router.classify_task(text)
        decision = self.phase11.model_router.decide(
            task_type=task["task_type"],
            quality_required=task["quality_required"],
            estimated_input_tokens=max(400, len(text.split()) * 3 + self._history_token_estimate(conversation_id)),
            estimated_output_tokens=500,
        )
        provider_text = ""
        provider_call = {
            "attempted": False,
            "external_call_performed": False,
            "status": "not_needed",
            "reason": "",
        }

        if persona_response:
            assistant_text = persona_response
            status = "normal"
        elif decision["selected_provider"] == "openrouter":
            if decision["requires_approval"]:
                assistant_text = (
                    f"Eso necesita aprobación antes de usar un modelo de pago. Coste estimado: "
                    f"{decision['estimated_cost_eur']} EUR. Frase exacta: {PHASE_10_EXACT_APPROVAL_PHRASE}."
                )
                status = "approval_required"
                provider_call["reason"] = "approval_required"
            elif not decision["provider_status"]["paid_calls_enabled"]:
                assistant_text = "Todavía no tengo OpenRouter activado. Puedo funcionar en modo local/fallback o ayudarte a configurarlo."
                status = "blocked"
                provider_call["reason"] = "live_calls_disabled"
            else:
                provider_call = self._call_openrouter(text=text, conversation_id=conversation_id, decision=decision)
                provider_text = provider_call.get("assistant_text", "")
                assistant_text = provider_text or self._deterministic_response(text, decision=decision)
                status = "normal" if provider_call.get("external_call_performed") else "blocked"
        elif decision["selected_provider"] == "none":
            if decision["blocked_reason"] == "missing_OPENROUTER_API_KEY":
                assistant_text = "Todavía no tengo OpenRouter activado. Puedo funcionar en modo local/fallback o ayudarte a configurarlo."
            else:
                assistant_text = "No voy a bajar la calidad a ciegas. Esta petición necesita mejor razonamiento o más presupuesto antes de continuar."
            status = "blocked"
        else:
            assistant_text = self._deterministic_response(text, decision=decision)
            status = "normal"

        if self.phase10.persona.state.mode == "utron" and not persona_response:
            assistant_text = self.phase10.persona.format_response(assistant_text)

        turn = {
            "schema_version": PHASE_12_CONVERSATION_SCHEMA_VERSION,
            "turn_id": f"phase12_turn_{uuid4()}",
            "conversation_id": _safe_text(conversation_id or "jarvis", limit=120),
            "created_at": _now_iso(),
            "channel": _safe_text(channel, limit=80),
            "source": _safe_text(source, limit=80),
            "status": status,
            "assistant_text": assistant_text,
            "persona": self.phase10.persona.status(),
            "router": {
                "task": task,
                "decision": decision,
                "used_router_v2": True,
                "external_provider_called": bool(provider_call.get("external_call_performed")),
            },
            "provider_call": provider_call,
            "memory": {
                "current_session_history_turns": len(self._history.get(conversation_id, [])),
                "persistent_summary_written": False,
                "secrets_stored": False,
                "memory_grants_permission": False,
                "memory_downgrades_risk": False,
            },
            "safety": {
                "did_execute": False,
                "hermes_dispatch_allowed": False,
                "frontend_direct_hermes_allowed": False,
                "mobile_direct_hermes_allowed": False,
                "wake_phrase_can_approve": False,
                "raw_audio_stored": False,
                "transcript_confidence": transcript_confidence,
            },
        }
        self._record_history(conversation_id, text, assistant_text, channel=channel, source=source, status=status)
        self.audit.record(
            "phase12_conversation_turn",
            surface="conversation_brain",
            channel=channel,
            result=status,
            metadata={
                "conversation_id_hash": _safe_text(conversation_id, limit=120),
                "task_type": task["task_type"],
                "selected_provider": decision["selected_provider"],
                "external_provider_called": provider_call.get("external_call_performed", False),
            },
        )
        return turn

    def clear(self, *, conversation_id: str = "jarvis") -> Dict[str, Any]:
        self._history.pop(conversation_id, None)
        return {
            "schema_version": PHASE_12_CONVERSATION_SCHEMA_VERSION,
            "cleared": True,
            "conversation_id": _safe_text(conversation_id, "jarvis", limit=120),
            "memory_grants_permission": False,
            "memory_downgrades_risk": False,
        }

    def _record_history(self, conversation_id: str, user_text: str, assistant_text: str, *, channel: str, source: str, status: str) -> None:
        turns = self._history.setdefault(conversation_id, [])
        turns.append(
            {
                "created_at": _now_iso(),
                "user_text": _safe_text(user_text, limit=1000),
                "assistant_text": _safe_text(assistant_text, limit=1400),
                "channel": _safe_text(channel, limit=80),
                "source": _safe_text(source, limit=80),
                "status": _safe_text(status, limit=40),
            }
        )
        self._history[conversation_id] = turns[-30:]

    def _history_token_estimate(self, conversation_id: str) -> int:
        text = " ".join(
            f"{turn.get('user_text', '')} {turn.get('assistant_text', '')}" for turn in self._history.get(conversation_id, [])[-8:]
        )
        return max(0, len(text.split()) * 2)

    def _call_openrouter(self, *, text: str, conversation_id: str, decision: Mapping[str, Any]) -> Dict[str, Any]:
        key = str(self.env.get("OPENROUTER_API_KEY") or self.env.get("JARVIS_OPENROUTER_API_KEY") or "").strip()
        if not key:
            return {"attempted": False, "external_call_performed": False, "status": "blocked", "reason": "missing_OPENROUTER_API_KEY"}
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres JARVIS para David. Responde en español, humano, útil, directo y elegante. "
                    "No finjas acciones. Si hay riesgo, pide aprobación con 'confirmo y autorizo'."
                ),
            }
        ]
        for turn in self._history.get(conversation_id, [])[-8:]:
            messages.append({"role": "user", "content": turn["user_text"]})
            messages.append({"role": "assistant", "content": turn["assistant_text"]})
        messages.append({"role": "user", "content": text})
        payload = {"model": decision["selected_model"], "messages": messages, "temperature": 0.7}
        poster = self.http_post
        try:
            if poster is not None:
                response = poster(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=25,
                )
            else:
                response = _UrllibOpenRouterHTTP().post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json_payload=payload,
                    timeout=25,
                )
        except Exception as exc:  # pragma: no cover - defensive live-provider path
            return {
                "attempted": True,
                "external_call_performed": False,
                "status": "error",
                "reason": _safe_text(exc, limit=180),
                "provider_key_exposed": False,
            }
        content = _extract_openrouter_content(response)
        return {
            "attempted": True,
            "external_call_performed": True,
            "status": "ok",
            "assistant_text": content,
            "provider": "openrouter",
            "model": decision["selected_model"],
            "provider_key_exposed": False,
        }

    def _deterministic_response(self, text: str, *, decision: Mapping[str, Any]) -> str:
        folded = normalize_spanish(text)
        if any(marker in folded for marker in ("que puedes hacer", "qué puedes hacer", "capacidades")):
            return "Puedo conversar contigo, abrir JARVIS, abrir URLs seguras, buscar en el navegador y preparar acciones con aprobación cuando haya riesgo."
        if any(marker in folded for marker in ("estado", "status", "doctor")):
            return "Estoy activo en modo local. Reviso estado, puertos, proveedor, voz, puente remoto y acciones sin enseñar secretos."
        if any(marker in folded for marker in ("gracias", "ok", "vale")):
            return "Hecho, David. Me quedo atento."
        if decision.get("selected_provider") == "local":
            return "Te sigo. Puedo ayudarte con el siguiente paso y, si la petición implica tocar algo real, te diré el riesgo antes de actuar."
        return "Puedo continuar, pero necesito mejor configuración o aprobación antes de usar un proveedor de más calidad."


def _extract_openrouter_content(response: Any) -> str:
    payload = response
    if hasattr(response, "json"):
        payload = response.json()
    if isinstance(payload, Mapping):
        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, Mapping):
                message = first.get("message")
                if isinstance(message, Mapping) and message.get("content"):
                    return _safe_text(message.get("content"), limit=4000)
                if first.get("text"):
                    return _safe_text(first.get("text"), limit=4000)
    return ""


@dataclass(frozen=True)
class NativeAppDefinition:
    app_id: str
    display_name: str
    aliases: Tuple[str, ...]
    risk_level: str = "low"
    requires_approval: bool = False
    kind: str = "binary"
    commands: Tuple[Tuple[str, ...], ...] = ()
    env_path_keys: Tuple[str, ...] = ()
    url: str = ""
    folder: str = ""


class Phase12ActionRouter:
    def __init__(
        self,
        *,
        phase11: Phase11RealProviderControllerIPhoneCompanion,
        audit: Phase12AuditLog,
        env: Optional[Mapping[str, str]] = None,
        launcher: Optional[Callable[[Sequence[str]], bool]] = None,
        opener: Optional[Callable[[str], bool]] = None,
    ) -> None:
        self.phase11 = phase11
        self.audit = audit
        self.env = env if env is not None else os.environ
        self.launcher = launcher or self._default_launch
        self.opener = opener or (lambda url: bool(webbrowser.open(url, new=1, autoraise=True)))
        self._candidates: Dict[str, Dict[str, Any]] = {}
        self._apps = _native_apps()
        self._custom_apps = self._load_custom_apps()

    def status(self) -> Dict[str, Any]:
        apps = {app_id: self._app_status(app) for app_id, app in {**self._apps, **self._custom_apps}.items()}
        return {
            "schema_version": PHASE_12_ACTION_SCHEMA_VERSION,
            "state": {
                "mode": "governed_real_action_launcher",
                "known_app_count": len(apps),
                "pending_candidate_count": len(self._candidates),
                "safe_url_open_real": True,
                "web_search_real": True,
                "known_app_launch_real_when_resolved": True,
                "arbitrary_shell_allowed": False,
                "raw_command_from_ui_allowed": False,
            },
            "known_apps": apps,
            "unknown_app_message_es": "No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida.",
            "custom_app_registry": {
                "path": str(_custom_app_registry_path()),
                "profile_safe": True,
                "secret_storage_allowed": False,
                "entry_count": len(self._custom_apps),
            },
            "safety": {
                "jarvis_governs": True,
                "hermes_executes_for_agent_work": True,
                "local_controller_handles_bounded_desktop_actions": True,
                "no_generic_execute": True,
                "no_shell": True,
                "audit_every_attempt": True,
                "sensitive_apps_require_approval": True,
            },
            "source_endpoint": "/mark-3/phase-12/actions/status",
        }

    def prepare(self, *, text: str, actor: str = "David", channel: str = "desktop") -> Dict[str, Any]:
        normalized = normalize_spanish(text)
        ui_intent = _match_voice_ui(normalized)
        if ui_intent:
            return self._candidate(
                intent="ui.control",
                target=ui_intent,
                actor=actor,
                channel=channel,
                risk_level="medium" if ui_intent in {"camera.start", "audio.start"} else "low",
                requires_approval=ui_intent in {"camera.start", "audio.start"},
                real_supported=True,
                metadata={"ui_intent": ui_intent},
            )

        if _looks_like_url(text):
            url = _safe_url(text)
            return self._candidate(
                intent="browser.open_url",
                target=url,
                actor=actor,
                channel=channel,
                risk_level="low",
                requires_approval=False,
                real_supported=bool(url),
                metadata={"url_origin": _origin(url)},
            )

        if any(marker in normalized for marker in ("busca", "buscar", "googlea", "search")):
            query = re.sub(r"\b(busca|buscar|googlea|search|en internet|internet)\b", "", normalized).strip() or normalized
            url = _search_url(query)
            return self._candidate(
                intent="web.search",
                target=url,
                actor=actor,
                channel=channel,
                risk_level="low",
                requires_approval=False,
                real_supported=True,
                metadata={"query_fingerprint": _safe_text(str(abs(hash(query))), limit=32), "url_origin": _origin(url)},
            )

        if any(marker in normalized for marker in ("abre jarvis", "abrir jarvis", "/jarvis")):
            return self._candidate(
                intent="app.open",
                target="chrome",
                actor=actor,
                channel=channel,
                risk_level="low",
                requires_approval=False,
                real_supported=True,
                metadata={"app_id": "chrome"},
            )

        if any(marker in normalized for marker in ("abre carpeta", "abrir carpeta", "carpeta jarvis", "proyecto jarvis")):
            app_id = "jarvis_project" if "jarvis" in normalized or "proyecto" in normalized else "documents"
            return self._app_candidate(app_id=app_id, requested=text, actor=actor, channel=channel)

        if any(marker in normalized for marker in ("abre", "abrir", "lanza", "inicia")):
            requested = _strip_launch_verbs(normalized)
            app = self._resolve_app(requested)
            if app:
                return self._app_candidate(app_id=app.app_id, requested=text, actor=actor, channel=channel)
            audit = self.audit.record(
                "phase12_unknown_app",
                surface="actions",
                channel=channel,
                result="unknown_app",
                metadata={"requested_app_hash": str(abs(hash(requested)))},
            )
            return {
                "schema_version": PHASE_12_ACTION_SCHEMA_VERSION,
                "status": "unknown_app",
                "known": False,
                "spanish_response": "No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida.",
                "executed": False,
                "would_execute": False,
                "raw_command_accepted": False,
                "freeform_shell_allowed": False,
                "audit_id": audit["event_id"],
            }

        return self._candidate(
            intent="conversation",
            target=_safe_text(text, limit=200),
            actor=actor,
            channel=channel,
            risk_level="low",
            requires_approval=False,
            real_supported=False,
            metadata={"reason": "not_an_action"},
        )

    def dispatch(
        self,
        *,
        candidate_id: str,
        actor: str = "David",
        approval_id: str = "",
        trusted_session: bool = False,
    ) -> Dict[str, Any]:
        candidate = self._candidates.get(str(candidate_id or ""))
        if not candidate:
            return {"schema_version": PHASE_12_ACTION_SCHEMA_VERSION, "status": "blocked", "reason": "candidate_not_found", "executed": False}
        if candidate.get("requires_approval") and not (approval_id or trusted_session):
            return {**candidate, "status": "approval_required", "executed": False, "reason": "approval_required"}
        if not candidate.get("real_supported"):
            return {**candidate, "status": "readiness_only", "executed": False, "reason": "real_dispatch_not_supported_for_candidate"}

        intent = str(candidate.get("intent"))
        target = str(candidate.get("target") or "")
        try:
            if intent in {"browser.open_url", "web.search"}:
                executed = bool(self.opener(target))
            elif intent == "app.open":
                executed = self._dispatch_app(candidate)
            elif intent == "ui.control":
                executed = True
            else:
                executed = False
            status = "executed" if executed else "failed"
            reason = "" if executed else "launcher_returned_false"
        except Exception as exc:  # pragma: no cover - defensive local platform path
            executed = False
            status = "failed"
            reason = _safe_text(exc, limit=180)

        audit = self.audit.record(
            "phase12_action_dispatch",
            surface="actions",
            channel=str(candidate.get("channel") or "desktop"),
            result=status,
            risk_level=str(candidate.get("risk_level") or "low"),
            action_id=str(candidate.get("action_id") or ""),
            metadata={"intent": intent, "target_origin": _origin(target), "approval_id": approval_id},
        )
        candidate.update({"status": status, "executed": executed, "last_result": reason})
        return {**candidate, "audit_id": audit["event_id"], "reason": reason, "did_execute": executed}

    def register_app_path(
        self,
        *,
        app_id: str,
        path: str,
        display_name: str = "",
        aliases: Optional[List[str]] = None,
        actor: str = "David",
    ) -> Dict[str, Any]:
        safe_path = Path(path).expanduser()
        if not safe_path.is_absolute():
            return {"schema_version": PHASE_12_ACTION_SCHEMA_VERSION, "status": "rejected", "reason": "absolute_path_required"}
        if any(marker in str(safe_path).casefold() for marker in (".env", "secret", "token", "password")):
            return {"schema_version": PHASE_12_ACTION_SCHEMA_VERSION, "status": "rejected", "reason": "secret_like_path_rejected"}
        definition = NativeAppDefinition(
            app_id=_safe_text(app_id, limit=60),
            display_name=_safe_text(display_name or app_id, limit=100),
            aliases=tuple(normalize_spanish(alias) for alias in (aliases or [display_name, app_id]) if alias),
            risk_level="medium",
            requires_approval=True,
            commands=((str(safe_path),),),
        )
        self._custom_apps[definition.app_id] = definition
        self._save_custom_apps()
        audit = self.audit.record(
            "phase12_custom_app_saved",
            surface="actions",
            result="saved",
            risk_level="medium",
            metadata={"actor": actor, "app_id": definition.app_id},
        )
        return {
            "schema_version": PHASE_12_ACTION_SCHEMA_VERSION,
            "status": "saved",
            "app": self._app_status(definition),
            "audit_id": audit["event_id"],
        }

    def _app_candidate(self, *, app_id: str, requested: str, actor: str, channel: str) -> Dict[str, Any]:
        app = {**self._apps, **self._custom_apps}[app_id]
        resolved = self._resolve_command(app)
        real_supported = bool(resolved or app.kind == "url" or app.app_id == "chrome")
        return self._candidate(
            intent="app.open",
            target=app.app_id,
            actor=actor,
            channel=channel,
            risk_level=app.risk_level,
            requires_approval=app.requires_approval,
            real_supported=real_supported,
            metadata={"app_id": app.app_id, "requested": requested, "resolved": bool(resolved), "resolution": _safe_text(" ".join(resolved), limit=160)},
        )

    def _candidate(
        self,
        *,
        intent: str,
        target: str,
        actor: str,
        channel: str,
        risk_level: str,
        requires_approval: bool,
        real_supported: bool,
        metadata: Mapping[str, Any],
    ) -> Dict[str, Any]:
        candidate_id = f"phase12_action_{uuid4()}"
        action_id = f"{intent}_{uuid4()}"
        candidate = {
            "schema_version": PHASE_12_ACTION_SCHEMA_VERSION,
            "candidate_id": candidate_id,
            "action_id": action_id,
            "intent": intent,
            "target": _safe_text(target, limit=300),
            "status": "prepared",
            "risk_level": risk_level,
            "requires_approval": requires_approval,
            "requires_exact_phrase": requires_approval,
            "required_phrase": PHASE_10_EXACT_APPROVAL_PHRASE if requires_approval else "",
            "real_supported": real_supported,
            "would_execute": real_supported,
            "executed": False,
            "actor": _safe_text(actor, limit=80),
            "channel": _safe_text(channel, limit=80),
            "raw_command_accepted": False,
            "freeform_shell_allowed": False,
            "frontend_direct_hermes_allowed": False,
            "metadata": _safe_metadata(metadata),
            "spanish_response": _action_response(intent, target, requires_approval, real_supported),
        }
        self._candidates[candidate_id] = candidate
        audit = self.audit.record(
            "phase12_action_prepared",
            surface="actions",
            channel=channel,
            result="prepared",
            risk_level=risk_level,
            action_id=action_id,
            metadata=metadata,
        )
        return {**candidate, "audit_id": audit["event_id"]}

    def _resolve_app(self, requested: str) -> Optional[NativeAppDefinition]:
        normalized = normalize_spanish(requested)
        for app in {**self._apps, **self._custom_apps}.values():
            if normalized == normalize_spanish(app.display_name) or normalized in app.aliases:
                return app
        return None

    def _resolve_command(self, app: NativeAppDefinition) -> List[str]:
        for env_key in app.env_path_keys:
            value = str(self.env.get(env_key, "")).strip()
            if value:
                return [value]
        if app.kind == "folder":
            folder = _folder_path(app.folder)
            return _folder_open_command(folder) if folder else []
        if app.kind == "url":
            return []
        for command in app.commands:
            if not command:
                continue
            exe = command[0]
            if Path(exe).is_absolute() and Path(exe).exists():
                return list(command)
            found = shutil.which(exe)
            if found:
                return [found, *command[1:]]
        return []

    def _dispatch_app(self, candidate: Mapping[str, Any]) -> bool:
        app = {**self._apps, **self._custom_apps}.get(str(candidate.get("target") or ""))
        if app is None:
            return False
        if app.app_id == "chrome":
            return bool(self.opener(JARVIS_FRONTEND_URL))
        if app.kind == "url":
            return bool(self.opener(app.url))
        command = self._resolve_command(app)
        if not command:
            return False
        return bool(self.launcher(command))

    def _default_launch(self, argv: Sequence[str]) -> bool:
        subprocess.Popen(list(argv), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        return True

    def _app_status(self, app: NativeAppDefinition) -> Dict[str, Any]:
        command = self._resolve_command(app)
        return {
            "app_id": app.app_id,
            "display_name": app.display_name,
            "aliases": list(app.aliases),
            "risk_level": app.risk_level,
            "requires_approval": app.requires_approval,
            "kind": app.kind,
            "resolved": bool(command or app.kind == "url" or app.app_id == "chrome"),
            "resolution_hint": _safe_text(" ".join(command), limit=160) if command else "",
            "raw_shell": False,
        }

    def _load_custom_apps(self) -> Dict[str, NativeAppDefinition]:
        path = _custom_app_registry_path()
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        apps: Dict[str, NativeAppDefinition] = {}
        for item in payload.get("apps", []):
            if not isinstance(item, Mapping):
                continue
            command = str(item.get("path") or "").strip()
            if not command:
                continue
            app = NativeAppDefinition(
                app_id=_safe_text(item.get("app_id"), limit=60),
                display_name=_safe_text(item.get("display_name"), limit=100),
                aliases=tuple(normalize_spanish(alias) for alias in item.get("aliases", []) if alias),
                risk_level="medium",
                requires_approval=True,
                commands=((command,),),
            )
            apps[app.app_id] = app
        return apps

    def _save_custom_apps(self) -> None:
        path = _custom_app_registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": PHASE_12_ACTION_SCHEMA_VERSION,
            "apps": [
                {
                    "app_id": app.app_id,
                    "display_name": app.display_name,
                    "aliases": list(app.aliases),
                    "path": app.commands[0][0] if app.commands else "",
                }
                for app in self._custom_apps.values()
            ],
            "secrets_allowed": False,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _native_apps() -> Dict[str, NativeAppDefinition]:
    project_root = str(Path(__file__).resolve().parents[1])
    return {
        "chrome": NativeAppDefinition("chrome", "Chrome/browser", ("chrome", "google chrome", "navegador", "browser"), kind="url", url=JARVIS_FRONTEND_URL),
        "cursor": NativeAppDefinition("cursor", "Cursor", ("cursor",), risk_level="medium", requires_approval=True, commands=(("cursor",),), env_path_keys=("JARVIS_APP_CURSOR_PATH",)),
        "vscode": NativeAppDefinition("vscode", "VS Code", ("vs code", "visual studio code", "code"), risk_level="medium", requires_approval=True, commands=(("code",), ("code-insiders",)), env_path_keys=("JARVIS_APP_VSCODE_PATH",)),
        "terminal": NativeAppDefinition("terminal", "Windows Terminal/Terminal/WSL", ("terminal", "consola", "wsl", "windows terminal"), risk_level="high", requires_approval=True, commands=_terminal_commands(), env_path_keys=("JARVIS_APP_TERMINAL_PATH",)),
        "file_explorer": NativeAppDefinition("file_explorer", "File Explorer", ("explorador", "explorador de archivos", "file explorer"), risk_level="medium", requires_approval=True, kind="folder", folder="home"),
        "whatsapp": NativeAppDefinition("whatsapp", "WhatsApp", ("whatsapp", "wasap"), risk_level="medium", requires_approval=True, kind="url", url="https://web.whatsapp.com/"),
        "spotify": NativeAppDefinition("spotify", "Spotify", ("spotify", "musica", "música"), commands=(("spotify",),), url="https://open.spotify.com/"),
        "jarvis_project": NativeAppDefinition("jarvis_project", "JARVIS project folder", ("carpeta jarvis", "proyecto jarvis", "jarvis project folder"), risk_level="medium", requires_approval=True, kind="folder", folder=project_root),
        "documents": NativeAppDefinition("documents", "Documents folder", ("documentos", "carpeta documentos"), risk_level="medium", requires_approval=True, kind="folder", folder="documents"),
    }


def _terminal_commands() -> Tuple[Tuple[str, ...], ...]:
    if sys.platform == "win32":
        return (("wt.exe",), ("cmd.exe",))
    if is_wsl():
        return (("wt.exe",), ("cmd.exe",))
    if sys.platform == "darwin":
        return (("open", "-a", "Terminal"),)
    return (("x-terminal-emulator",), ("gnome-terminal",), ("konsole",), ("xterm",))


def _folder_path(name: str) -> str:
    if not name:
        return ""
    raw = Path(name).expanduser()
    if raw.is_absolute():
        return str(raw)
    home = Path.home()
    if name == "home":
        return str(home)
    if name == "documents":
        return str(home / "Documents")
    return ""


def _folder_open_command(path: str) -> List[str]:
    if not path:
        return []
    if sys.platform == "win32":
        return ["explorer.exe", path]
    if is_wsl() and shutil.which("explorer.exe"):
        return ["explorer.exe", path]
    if sys.platform == "darwin" and shutil.which("open"):
        return ["open", path]
    xdg = shutil.which("xdg-open")
    return [xdg, path] if xdg else []


def _custom_app_registry_path() -> Path:
    return get_hermes_home() / "jarvis" / "known_apps.json"


def _strip_launch_verbs(normalized: str) -> str:
    return re.sub(r"\b(abre|abrir|lanza|inicia|la|el|aplicacion|aplicación)\b", " ", normalized).strip()


def _match_voice_ui(normalized: str) -> str:
    simplified = _strip_articles(normalized)
    for intent, variants in VOICE_UI_VARIANTS.items():
        if any(variant in normalized or _strip_articles(variant) in simplified for variant in variants):
            return intent
    return ""


def _strip_articles(value: str) -> str:
    return " ".join(token for token in normalize_spanish(value).split() if token not in {"el", "la", "los", "las", "un", "una"})


def _action_response(intent: str, target: str, requires_approval: bool, real_supported: bool) -> str:
    if requires_approval:
        return f"Eso necesita aprobación. Leeré alcance, coste y riesgo; la frase exacta es {PHASE_10_EXACT_APPROVAL_PHRASE}."
    if real_supported and intent in {"browser.open_url", "web.search"}:
        return "Puedo abrirlo ahora en el navegador visible."
    if real_supported and intent == "app.open":
        return "Puedo abrir esa app o carpeta mediante el lanzador gobernado."
    if intent == "ui.control":
        return "Puedo aplicar ese control de la interfaz."
    return "Puedo conversarlo, pero no hay una acción real segura asociada todavía."


class Phase12VoiceStack:
    def __init__(self, *, env: Optional[Mapping[str, str]] = None) -> None:
        self.env = env if env is not None else os.environ

    def status(self) -> Dict[str, Any]:
        piper_binary = str(self.env.get("JARVIS_PIPER_BINARY") or "piper")
        piper_detected = bool(shutil.which(piper_binary) or (Path(piper_binary).is_absolute() and Path(piper_binary).exists()))
        jarvis_model = str(self.env.get("JARVIS_PIPER_JARVIS_MODEL_PATH") or "").strip()
        utron_model = str(self.env.get("JARVIS_PIPER_UTRON_MODEL_PATH") or "").strip()
        gpt_sovits_enabled = str(self.env.get("JARVIS_VOICE_PROVIDER", "")).strip().casefold() == "gpt-sovits"
        voice_default_on = _voice_output_default_enabled(self.env)
        return {
            "schema_version": PHASE_12_VOICE_SCHEMA_VERSION,
            "state": {
                "selected_provider": str(self.env.get("JARVIS_VOICE_PROVIDER", "browser")).strip().casefold() or "browser",
                "browser_speech_synthesis_fallback": True,
                "voice_output_default_enabled": voice_default_on,
                "wake_greeting_spoken_by_default": voice_default_on,
                "voice_output_for_answers": True,
                "stop_interruption_supported": True,
                "repeat_supported": True,
                "copyrighted_voice_clone_allowed": False,
                "browser_autoplay_prompt_es": "El navegador necesita una primera interacción para activar la voz. Pulsa una vez y seguiré hablando automáticamente.",
            },
            "preferences": {
                "jarvis": "humana, cálida, elegante, tecnológica; no clon de actor ni voz de película",
                "utron": "más grave, oscura y autoritaria; sin saltarse seguridad",
            },
            "providers": {
                "browser_speech_synthesis": {
                    "status": "fallback_client_side",
                    "local_only": False,
                    "network_required_by_backend": False,
                    "cost": "0 EUR",
                },
                "piper": {
                    "status": "ready" if piper_detected and jarvis_model else "missing_model" if piper_detected else "missing_binary",
                    "binary_detected": piper_detected,
                    "jarvis_model_configured": bool(jarvis_model),
                    "utron_model_configured": bool(utron_model),
                    "enabled_when_JARVIS_VOICE_PROVIDER": "piper",
                    "local_only": True,
                    "network_required": False,
                    "model_download_performed": False,
                },
                "gpt_sovits": {
                    "status": "configured" if gpt_sovits_enabled else "available_optional_sidecar",
                    "enabled": gpt_sovits_enabled,
                    "local_sidecar": True,
                    "network_required": "local_http_only",
                    "secrets_required": False,
                },
            },
            "errors_user_facing_es": {
                "missing_api": "Todavía no tengo OpenRouter activado. Puedo funcionar en modo local/fallback o ayudarte a configurarlo.",
                "missing_voice": "La voz local no está lista; sigo por texto o voz del navegador.",
            },
            "safety": {
                "no_hidden_audio_storage": True,
                "no_voice_clone_of_copyrighted_actor": True,
                "voice_approval_requires_active_trusted_gated_readback": True,
                "wake_phrase_can_approve": False,
            },
        }


class Phase12RemoteBridge:
    def __init__(
        self,
        *,
        phase11: Phase11RealProviderControllerIPhoneCompanion,
        audit: Phase12AuditLog,
        env: Optional[Mapping[str, str]] = None,
    ) -> None:
        self.phase11 = phase11
        self.audit = audit
        self.env = env if env is not None else os.environ
        self.kill_switch_enabled = _env_bool("JARVIS_REMOTE_KILL_SWITCH", False, env=self.env)

    def status(self) -> Dict[str, Any]:
        tailscale_binary = shutil.which("tailscale")
        remote_enabled = _env_bool("JARVIS_REMOTE_BRIDGE_ENABLED", False, env=self.env)
        mode = str(self.env.get("JARVIS_REMOTE_BRIDGE_MODE") or "tailscale").strip().casefold()
        return {
            "schema_version": PHASE_12_REMOTE_SCHEMA_VERSION,
            "state": {
                "mode": mode,
                "enabled": remote_enabled and not self.kill_switch_enabled,
                "kill_switch_enabled": self.kill_switch_enabled,
                "same_jarvis": True,
                "separate_mobile_assistant": False,
                "iphone_client_surface": "Safari/PWA",
                "execution_stays_on_pc": True,
            },
            "connection_modes": {
                "local_loopback": {"url": JARVIS_FRONTEND_URL, "available": True},
                "lan": {"url": frontend_url("/mobile", host="<IP-LAN-PC>"), "requires_same_wifi": True},
                "tailscale": {
                    "preferred_for_outside_home": True,
                    "binary_detected": bool(tailscale_binary),
                    "enabled": remote_enabled and mode == "tailscale" and bool(tailscale_binary) and not self.kill_switch_enabled,
                    "url_hint": self.env.get("JARVIS_TAILSCALE_URL", frontend_url("/mobile", host="<tailscale-ip-or-name>")),
                    "frontend_port_required": FRONTEND_PORT,
                },
                "telegram_bridge": {
                    "available_if_existing_gateway_configured": bool(self.env.get("TELEGRAM_BOT_TOKEN")),
                    "execution_direct": False,
                    "approval_notifications_future": True,
                },
                "cloudflare_tunnel": {
                    "optional_future": True,
                    "requires_auth": True,
                    "enabled_by_default": False,
                },
            },
            "pairing": self.phase11.pairing.status(),
            "security": {
                "public_unauthenticated_exposure": False,
                "raw_pc_port_to_internet": False,
                "pairing_required": True,
                "approval_bound_to_action_id_scope_channel_device": True,
                "expiry_required": True,
                "revocation_supported": True,
                "mobile_direct_hermes_allowed": False,
                "mobile_raw_shell_allowed": False,
            },
            "user_facing_es": {
                "needs_secure_bridge": "El acceso remoto necesita activar el puente seguro.",
                "tailscale_recommended": "Para usar el iPhone en la calle, instala Tailscale en el PC y el iPhone y abre la URL Tailscale de JARVIS.",
            },
            "source_endpoint": "/mark-3/phase-12/remote/status",
        }

    def set_kill_switch(self, *, enabled: bool, actor: str = "David") -> Dict[str, Any]:
        self.kill_switch_enabled = bool(enabled)
        audit = self.audit.record(
            "phase12_remote_kill_switch",
            surface="remote_bridge",
            result="enabled" if enabled else "disabled",
            risk_level="medium",
            metadata={"actor": actor},
        )
        return {**self.status(), "audit_id": audit["event_id"]}


class Phase12StartupContract:
    def __init__(self, *, env: Optional[Mapping[str, str]] = None) -> None:
        self.env = env if env is not None else os.environ

    def status(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_12_STARTUP_SCHEMA_VERSION,
            "commands": {
                "start": "scripts/jarvis-start",
                "stop": "scripts/jarvis-stop",
                "doctor": "scripts/jarvis-doctor",
                "wake_listener": "scripts/jarvis-wake-listener",
                "wake_setup": "scripts/jarvis-wake-setup",
            },
            "ports": {
                "backend": BACKEND_PORT,
                "frontend": FRONTEND_PORT,
                "backend_url": BACKEND_BASE_URL,
                "frontend_url": FRONTEND_BASE_URL,
                "frontend_proxy_target": BACKEND_BASE_URL,
                "consistent": True,
                "port_confusion_fixed": True,
            },
            "urls": {
                "pc_jarvis": JARVIS_FRONTEND_URL,
                "pc_mobile": MOBILE_FRONTEND_URL,
                "backend_api": BACKEND_BASE_URL,
                "iphone_lan": frontend_url("/mobile", host="<PC-LAN-IP>"),
                "iphone_tailscale": self.env.get("JARVIS_TAILSCALE_URL", frontend_url("/mobile", host="<tailscale-ip-or-name>")),
            },
            "checks": {
                "openrouter_configured": bool(self.env.get("OPENROUTER_API_KEY") or self.env.get("JARVIS_OPENROUTER_API_KEY")),
                "openrouter_budget_eur": _env_float("JARVIS_API_MONTHLY_BUDGET_EUR", DEFAULT_MONTHLY_BUDGET_EUR, env=self.env),
                "tts_provider": str(self.env.get("JARVIS_VOICE_PROVIDER", "browser")),
                "voice_default_on": _voice_output_default_enabled(self.env),
                "tailscale_binary_detected": bool(shutil.which("tailscale")),
                "piper_binary_detected": bool(shutil.which(str(self.env.get("JARVIS_PIPER_BINARY") or "piper"))),
                "real_wake_listener_available": build_wake_listener_status(env=self.env)["state"]["real_microphone_wake_available"],
                "real_wake_listener_active": build_wake_listener_status(env=self.env)["state"]["wake_active"],
                "wake_backend_selected": build_wake_listener_status(env=self.env)["state"]["selected_backend"],
            },
            "wake_listener": build_wake_listener_status(env=self.env),
            "spanish_errors": {
                "backend_down": "JARVIS backend no está escuchando en 9119.",
                "frontend_down": "La interfaz web no está escuchando en 5173.",
                "openrouter_missing": "Todavía no tengo OpenRouter activado. Puedo funcionar en modo local/fallback o ayudarte a configurarlo.",
                "remote_missing": "El acceso remoto necesita activar el puente seguro.",
            },
        }


class Phase12RealAlwaysOnJarvisMVP:
    def __init__(
        self,
        *,
        phase10: Phase10HandsFreeRuntimePersonaApiRouter,
        phase11: Phase11RealProviderControllerIPhoneCompanion,
        env: Optional[Mapping[str, str]] = None,
        opener: Optional[Callable[[str], bool]] = None,
        launcher: Optional[Callable[[Sequence[str]], bool]] = None,
        openrouter_http_post: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.phase10 = phase10
        self.phase11 = phase11
        self.env = env if env is not None else os.environ
        self.audit = Phase12AuditLog()
        self.always_on = AlwaysOnLocalRuntime(phase10=phase10, phase11=phase11, audit=self.audit, env=self.env)
        self.conversation = Phase12ConversationBrain(
            phase10=phase10,
            phase11=phase11,
            audit=self.audit,
            env=self.env,
            http_post=openrouter_http_post,
        )
        self.actions = Phase12ActionRouter(phase11=phase11, audit=self.audit, env=self.env, opener=opener, launcher=launcher)
        self.voice = Phase12VoiceStack(env=self.env)
        self.remote = Phase12RemoteBridge(phase11=phase11, audit=self.audit, env=self.env)
        self.startup = Phase12StartupContract(env=self.env)

    @classmethod
    def from_environment(
        cls,
        *,
        phase10: Phase10HandsFreeRuntimePersonaApiRouter,
        phase11: Phase11RealProviderControllerIPhoneCompanion,
        opener: Optional[Callable[[str], bool]] = None,
    ) -> "Phase12RealAlwaysOnJarvisMVP":
        return cls(phase10=phase10, phase11=phase11, opener=opener)

    def status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        return {
            "schema_version": PHASE_12_SCHEMA_VERSION,
            "phase": "Phase 12",
            "title": "Real Always-On JARVIS MVP",
            "status": "implemented_as_real_local_controller_mvp_with_optional_audio_wake_and_secure_remote_bridge",
            "implemented_blocks": {
                "always_on_runtime_state": True,
                "wake_phrase_detection": True,
                "stop_phrase_detection": True,
                "router_backed_conversation": True,
                "openrouter_budget_guard": True,
                "local_tts_piper_optional": True,
                "browser_tts_fallback": True,
                "natural_voice_command_variants": True,
                "real_safe_url_search_open": True,
                "known_app_launcher_registry": True,
                "iphone_remote_bridge_tailscale_path": True,
                "same_jarvis_shared_state": True,
                "startup_scripts": True,
            },
            "real_vs_readiness": {
                "real": [
                    "stateful local JARVIS always-on runtime lifecycle",
                    "wake/stop transcript event handling with /jarvis open",
                    "router-backed conversation path with OpenRouter live-call gate and deterministic fallback",
                    "safe URL/search browser open",
                    "known app/folder launcher candidates with real dispatch when resolved and approved",
                    "Piper CLI local TTS adapter and GPT-SoVITS/browser fallback status",
                    "Tailscale-first remote bridge status, pairing, revocation and kill switch",
                ],
                "readiness": [
                    "dedicated wake models for longer aliases such as Hola JARVIS are optional and not bundled",
                    "persistent cross-device conversation summaries are not auto-written",
                    "browser form filling, submit, buy, pay and publish stay gated/preview",
                    "Cloudflare/VPS relay remains optional future work",
                ],
            },
            "routes": {
                "status": "/mark-3/phase-12/status" in routes,
                "conversation_turn": "/mark-3/phase-12/conversation/turn" in routes,
                "always_on_ingest": "/mark-3/phase-12/always-on/ingest-transcript" in routes,
                "always_on_ui_presence": "/mark-3/phase-12/always-on/ui-presence" in routes,
                "always_on_claim_greeting": "/mark-3/phase-12/always-on/claim-greeting" in routes,
                "actions_dispatch": "/mark-3/phase-12/actions/dispatch" in routes,
                "remote_status": "/mark-3/phase-12/remote/status" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "startup": self.startup.status(),
            "always_on": self.always_on.status(),
            "conversation": self.conversation.status(),
            "voice": self.voice.status(),
            "actions": self.actions.status(),
            "remote": self.remote.status(),
            "shared_state": self.phase11.shared_state.to_dict(channel="phase12_status"),
            "audit": self.audit.status(),
            "security_gates": {
                "jarvis_governs": True,
                "hermes_executes": True,
                "no_duplicate_hermes_runtime": True,
                "frontend_direct_hermes_allowed": False,
                "mobile_direct_hermes_allowed": False,
                "no_generic_execute": True,
                "no_arbitrary_shell_from_ui_or_mobile": True,
                "wake_phrase_can_approve": False,
                "voice_approval_requires_active_trusted_gated_readback_audit": True,
                "dangerous_exact_phrase": PHASE_10_EXACT_APPROVAL_PHRASE,
                "memory_grants_permission": False,
                "memory_downgrades_risk": False,
                "utron_bypasses_approvals": False,
                "secrets_exposed": False,
                "raw_audio_stored_by_default": False,
            },
            "source_endpoint": "/mark-3/phase-12/status",
        }
