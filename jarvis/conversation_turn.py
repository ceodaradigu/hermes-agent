from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


CONVERSATION_TURN_SCHEMA_VERSION = "jarvis.conversation.turn.v1"

SUPPORTED_CONVERSATION_SOURCES = {
    "typed_text",
    "voice_transcript",
    "wake_phrase_command",
    "remote_input",
    "unknown",
}

UNSUPPORTED_MARKERS = (
    "busca en internet",
    "buscar en internet",
    "internet",
    "web externa",
    "navega",
    "browser",
    "telegram",
    "whatsapp",
    "proveedor externo",
    "provider externo",
    "modelo externo",
    "llm externo",
    "api externa",
    "escucha continua",
    "transcripcion continua",
    "transcripción continua",
    "wake continuo",
    "always on",
)


def conversation_source_for(channel: str, requested_source: Optional[str] = None) -> str:
    if requested_source in SUPPORTED_CONVERSATION_SOURCES:
        return str(requested_source)
    folded = str(channel or "").casefold()
    if "voice" in folded or "voz" in folded:
        return "voice_transcript"
    if "wake" in folded:
        return "wake_phrase_command"
    if "remote" in folded:
        return "remote_input"
    return "typed_text"


def build_conversation_turn(
    *,
    user_text: str,
    channel: str,
    conversation_id: Optional[str],
    source: str,
    adapter_result: Dict[str, Any],
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a user-facing conversation turn from the safe intake/brain result.

    The return payload is structured for UI state, but the main assistant text
    is intentionally plain Spanish. It does not expose the raw adapter dump to
    the frontend and never claims execution.
    """

    created_at = generated_at or datetime.now(timezone.utc).isoformat()
    analysis = _dict(adapter_result.get("analysis"))
    classification = _dict(analysis.get("classification"))
    intake = _dict(analysis.get("intake"))
    brain_response = _dict(adapter_result.get("brain_response"))
    preview_candidate = _dict(brain_response.get("preview_candidate")) or _dict(analysis.get("preview_candidate"))

    status = _conversation_status(user_text, classification, brain_response)
    assistant_text = _assistant_text(
        user_text=user_text,
        status=status,
        classification=classification,
        brain_response=brain_response,
        preview_candidate=preview_candidate,
    )

    return {
        "schema_version": CONVERSATION_TURN_SCHEMA_VERSION,
        "turn_id": f"turn_{uuid4()}",
        "conversation_id": conversation_id or f"jarvis_ui_{uuid4()}",
        "created_at": created_at,
        "channel": channel or "jarvis_ui",
        "source": source,
        "status": status,
        "assistant_text": assistant_text,
        "display": {
            "language": "es",
            "tone": _tone_for(status),
            "label": _label_for(status),
            "summary": _summary_for(status),
        },
        "intent": {
            "intent_detected": str(brain_response.get("intent_detected") or classification.get("intent_detected") or "unknown"),
            "confidence": brain_response.get("confidence", classification.get("confidence", 0.0)),
            "risk_level": str(brain_response.get("risk_level") or classification.get("risk_level") or "none"),
            "approval_level": str(brain_response.get("approval_level") or classification.get("approval_level") or "direct"),
            "requires_approval": bool(brain_response.get("requires_approval") or classification.get("requires_approval")),
            "can_prepare_preview": bool(brain_response.get("can_prepare_preview") or classification.get("can_prepare_preview")),
        },
        "preview": _preview_payload(preview_candidate, status),
        "safety": {
            "preview_only": True,
            "read_only": True,
            "did_execute": False,
            "would_execute": False,
            "no_hermes_dispatch": True,
            "hermes_dispatch_allowed": False,
            "frontend_direct_hermes_allowed": False,
            "external_provider_called": False,
            "memory_read": False,
            "memory_write": False,
            "wake_phrase_can_approve": False,
            "wake_phrase_can_execute": False,
            "raw_audio_included": False,
            "camera_frames_included": False,
        },
        "audit_metadata": {
            "metadata_only": True,
            "intake_id": intake.get("intake_id"),
            "response_id": brain_response.get("response_id"),
            "sensitive_request": bool(intake.get("contains_sensitive_request")),
            "requires_clarification": bool(classification.get("requires_clarification")),
            "blocked_reasons": list(classification.get("blocked_reasons") or []),
            "raw_text_omitted": True,
            "approval_is_not_execution": True,
        },
    }


def _conversation_status(
    user_text: str,
    classification: Dict[str, Any],
    brain_response: Dict[str, Any],
) -> str:
    text = str(user_text or "").strip().casefold()
    intent = str(brain_response.get("intent_detected") or classification.get("intent_detected") or "")

    if not text:
        return "error"
    if _looks_unsupported(text, intent):
        return "unsupported"
    if bool(classification.get("denied")) or str(classification.get("risk_level")) == "forbidden":
        return "blocked"
    if bool(brain_response.get("requires_approval") or classification.get("requires_approval")):
        return "approval_required"
    if bool(brain_response.get("can_prepare_preview") or classification.get("can_prepare_preview")):
        return "preview"
    return "normal"


def _assistant_text(
    *,
    user_text: str,
    status: str,
    classification: Dict[str, Any],
    brain_response: Dict[str, Any],
    preview_candidate: Dict[str, Any],
) -> str:
    text = str(user_text or "").strip()
    folded = text.casefold()
    intent = str(brain_response.get("intent_detected") or classification.get("intent_detected") or "")

    if status == "error":
        return "Escríbeme una petición concreta y la preparo sin ejecutar nada."

    if status == "blocked":
        if "secret" in intent or "credential" in intent:
            return "No puedo leer ni usar credenciales, tokens, cookies o secretos. Puedo ayudarte a revisar el estado sin tocar material sensible."
        if "wake_phrase" in intent:
            return "La frase de activación no es permiso. No aprobaré ni ejecutaré nada por voz; si quieres, puedo preparar una vista previa segura."
        return "Eso queda bloqueado por seguridad. Puedo ayudarte con una alternativa autorizada, segura y auditable."

    if status == "unsupported":
        if any(marker in folded for marker in ("escucha continua", "transcripcion continua", "transcripción continua", "wake continuo", "always on")):
            return "Wake activo con Vosk cuando el runtime local está arrancado. Di 'JARVIS'; 'Hola JARVIS' queda como alias experimental según reconocimiento local. No guardo audio bruto y la frase de activación no aprueba ni ejecuta acciones."
        return "Esa parte todavía no está conectada. Puedo prepararla como plan seguro o decirte qué falta, pero no voy a fingir que ya está disponible."

    if status == "approval_required":
        return "Eso necesita tu aprobación antes de hacerlo. Te mostraré exactamente qué haría, el alcance y cómo pararlo; podrás aceptar o cancelar."

    if folded in {"hola jarvis", "hola, jarvis", "jarvis"} or folded.startswith("hola jarvis "):
        return "Estoy aquí, David. Te escucho."

    if intent == "query_system_status" or "estado" in folded or "status" in folded:
        return "Estoy activo, David. Voz activa. Puedes hablar con JARVIS; las acciones sensibles siguen pidiendo aprobación."

    if "qué puedes hacer" in folded or "que puedes hacer" in folded or "capacidad" in folded or "capacidades" in folded:
        return "Ahora puedo conversar contigo por voz o texto, revisar el estado visible y preparar próximos pasos seguros con calma. Si algo toca dinero, producción, correo, secretos o ejecución, pediré aprobación o lo bloquearé."

    if "readiness" in folded or "reales" in folded or "real" in folded:
        return "Lo real ahora incluye conversación local, wake local con Vosk cuando el runtime está arrancado, estado visible y vistas previas seguras. Proveedores externos, dinero, deploy o envíos reales siguen bloqueados o requieren aprobación."

    if status == "preview":
        goal = _goal_summary(preview_candidate, text)
        return f"Puedo prepararlo como vista previa: {goal}. Lo dejaré en modo seguro, sin ejecutar nada, con alcance y siguiente paso claro."

    return _sanitize_human_text(str(brain_response.get("human_response") or "Estoy aquí. Dime qué quieres preparar y lo mantengo en modo seguro."))


def _preview_payload(preview_candidate: Dict[str, Any], status: str) -> Dict[str, Any]:
    return {
        "available": bool(preview_candidate) and status in {"preview", "approval_required"},
        "title": str(preview_candidate.get("title") or _label_for(status)),
        "goal_summary": _goal_summary(preview_candidate, ""),
        "requires_approval": status == "approval_required" or bool(preview_candidate.get("requires_approval")),
        "next_safe_action": str(preview_candidate.get("next_safe_action") or _summary_for(status)),
        "would_execute": False,
        "would_call_hermes": False,
        "hermes_dispatch_allowed": False,
        "preview_only": True,
        "read_only": True,
    }


def _looks_unsupported(text: str, intent: str) -> bool:
    if any(marker in text for marker in UNSUPPORTED_MARKERS):
        return True
    if "external" in intent and "message" not in intent:
        return True
    return False


def _goal_summary(preview_candidate: Dict[str, Any], fallback: str) -> str:
    raw = str(preview_candidate.get("user_visible_goal") or fallback or "la petición de David").strip()
    if _contains_sensitive_marker(raw):
        return "contenido sensible omitido"
    compact = " ".join(raw.split())
    if len(compact) > 180:
        return f"{compact[:177]}..."
    return compact or "la petición de David"


def _sanitize_human_text(text: str) -> str:
    replacements = {
        "ApprovalGateway": "la aprobación",
        "approval": "aprobación",
        "gates": "controles de seguridad",
        "dispatch": "ejecución",
        "Frontend": "Esta pantalla",
        "frontend": "esta pantalla",
        "provider": "servicio",
        "LLM": "modelo",
        "preview": "vista previa",
    }
    sanitized = str(text or "")
    for old, new in replacements.items():
        sanitized = sanitized.replace(old, new)
    return sanitized.strip()


def _contains_sensitive_marker(text: str) -> bool:
    folded = str(text or "").casefold()
    return any(marker in folded for marker in (".env", "token", "password", "cookie", "secret", "secreto", "credencial"))


def _tone_for(status: str) -> str:
    if status in {"blocked", "unsupported", "error"}:
        return "alerta"
    if status == "approval_required":
        return "alerta"
    if status == "preview":
        return "concentrado"
    return "calmado"


def _label_for(status: str) -> str:
    return {
        "normal": "Respuesta",
        "preview": "Vista previa",
        "approval_required": "Necesita aprobación",
        "blocked": "Bloqueado",
        "unsupported": "No conectado",
        "error": "Error",
    }.get(status, "Respuesta")


def _summary_for(status: str) -> str:
    return {
        "normal": "Respuesta local segura.",
        "preview": "Preparar vista previa sin ejecución.",
        "approval_required": "Mostrar alcance y pedir aprobación antes de cualquier acción.",
        "blocked": "No continuar con esa petición.",
        "unsupported": "Explicar qué falta sin fingir capacidad.",
        "error": "Pedir una petición clara.",
    }.get(status, "Respuesta local segura.")


def _dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
