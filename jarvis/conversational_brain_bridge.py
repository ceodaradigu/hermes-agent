from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Dict, Iterable, Tuple


CONVERSATIONAL_BRAIN_SCHEMA_VERSION = "jarvis.conversational_brain_bridge.v2"

WAKE_PHRASES: Tuple[str, ...] = ("hola jarvis", "jarvis")
STOP_PHRASES: Tuple[str, ...] = ("para", "cancela", "detente", "silencio", "cancelar misión", "apaga escucha")

SECRET_MARKERS: Tuple[str, ...] = (
    ".env",
    "api key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "cookies",
    "credencial",
    "credenciales",
    "password",
    "private key",
    "secreto",
    "secret",
    "secretos",
    "session",
    "token",
)

SENSITIVE_ACTION_MARKERS: Tuple[str, ...] = (
    "checkout",
    "charge",
    "correo",
    "deploy",
    "despliega",
    "desplegar",
    "dinero",
    "email",
    "envia",
    "envía",
    "paga",
    "pago",
    "payment",
    "produccion",
    "producción",
    "publish",
    "stripe",
    "transferencia",
)

DENIED_MARKERS: Tuple[str, ...] = (
    "bypass",
    "hackea",
    "ilegal",
    "impersona",
    "no autorizado",
    "sin autorizacion",
    "sin autorización",
    "roba",
    "saltate",
    "sáltate",
)

APPROVAL_OR_EXECUTION_MARKERS: Tuple[str, ...] = (
    "aprueba",
    "aprobar",
    "aprobado",
    "confirmo",
    "continua",
    "continúa",
    "ejecuta",
    "hazlo",
)


@dataclass(frozen=True)
class ConversationalBrainResult:
    human_response: str
    intent_detected: str
    confidence: float
    risk_level: str
    approval_level: str
    requires_approval: bool
    can_prepare_preview: bool
    cannot_execute_reason: str
    suggested_next_action: str
    hermes_dispatch_allowed: bool = False
    external_provider_called: bool = False
    llm_called: bool = False
    memory_read: bool = False
    memory_write: bool = False
    transcript_persistence: bool = False
    preview_only: bool = True
    read_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", _clamp_confidence(self.confidence))
        object.__setattr__(self, "hermes_dispatch_allowed", False)
        object.__setattr__(self, "external_provider_called", False)
        object.__setattr__(self, "llm_called", False)
        object.__setattr__(self, "memory_read", False)
        object.__setattr__(self, "memory_write", False)
        object.__setattr__(self, "transcript_persistence", False)
        object.__setattr__(self, "preview_only", True)
        object.__setattr__(self, "read_only", True)

    def validate(self) -> None:
        if not self.human_response.strip():
            raise ValueError("human_response is required")
        if not self.intent_detected.strip():
            raise ValueError("intent_detected is required")
        if self.hermes_dispatch_allowed:
            raise ValueError("Conversational brain v2 cannot dispatch Hermes")
        if self.external_provider_called or self.llm_called:
            raise ValueError("Conversational brain v2 must stay local/deterministic")
        if self.memory_read or self.memory_write:
            raise ValueError("Conversational brain v2 cannot read/write memory automatically")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)


class ConversationalBrainBridge:
    """Local deterministic conversation bridge for the JARVIS presence UI.

    It classifies intent and risk for preview/read-model purposes only. It does
    not call an LLM, external API, memory store, tool runtime, or Hermes.
    """

    def analyze(self, text: str) -> ConversationalBrainResult:
        normalized = normalize_utterance(text)
        lower = normalized.casefold()
        has_wake_phrase, command_text = split_wake_phrase(lower)

        if not normalized:
            return _result(
                "No he recibido una frase clara. Repite la petición con una acción o pregunta concreta.",
                intent_detected="needs_clarification",
                confidence=0.2,
                risk_level="none",
                approval_level="direct",
                requires_approval=False,
                can_prepare_preview=False,
                cannot_execute_reason="No hay una petición interpretable.",
                suggested_next_action="Reformular con una frase corta.",
            )

        if (command_text or lower).strip() in STOP_PHRASES:
            return _result(
                "Entendido. Stop/cancel queda como control de sesión; no aprueba ni ejecuta nada.",
                intent_detected="voice_stop_or_cancel",
                confidence=0.88,
                risk_level="low",
                approval_level="direct",
                requires_approval=False,
                can_prepare_preview=False,
                cannot_execute_reason="Stop/cancel es control de sesión, no ejecución.",
                suggested_next_action="Cerrar o mantener idle la sesión de voz.",
            )

        if _contains_any(lower, SECRET_MARKERS):
            return _result(
                "No puedo leer ni usar credenciales, tokens, cookies o archivos de secretos. Puedo ayudarte con una revisión segura sin tocarlos.",
                intent_detected="denied_secret_or_credential_access",
                confidence=0.96,
                risk_level="forbidden",
                approval_level="forbidden",
                requires_approval=False,
                can_prepare_preview=False,
                cannot_execute_reason="Secretos, credenciales, cookies, sesiones y .env quedan denegados.",
                suggested_next_action="Rediseñar la petición para usar estado o auditoría sin material secreto.",
            )

        if has_wake_phrase and _contains_any(command_text, APPROVAL_OR_EXECUTION_MARKERS):
            return _result(
                "La wake phrase no es permiso. No aprobaré ni ejecutaré por voz; puedo dejar una preview segura si defines el alcance.",
                intent_detected="wake_phrase_approval_or_execution_attempt",
                confidence=0.94,
                risk_level="forbidden",
                approval_level="forbidden",
                requires_approval=False,
                can_prepare_preview=False,
                cannot_execute_reason="Wake phrase cannot approve and cannot execute.",
                suggested_next_action="Pedir una preview gobernada con alcance, riesgo y aprobación fuera de wake.",
            )

        if _contains_any(lower, DENIED_MARKERS):
            return _result(
                "Eso queda denegado. Puedo ayudar solo con una alternativa autorizada, segura y auditable.",
                intent_detected="denied_unsafe_unauthorized_or_illegal",
                confidence=0.9,
                risk_level="forbidden",
                approval_level="forbidden",
                requires_approval=False,
                can_prepare_preview=False,
                cannot_execute_reason="La petición parece ilegal, insegura, no autorizada o fuera de límites aprobables.",
                suggested_next_action="Reformular con autorización explícita y un objetivo seguro.",
            )

        if _contains_any(lower, SENSITIVE_ACTION_MARKERS):
            approval_level = "triple" if _contains_any(lower, ("stripe", "dinero", "pago", "payment", "producción", "produccion", "deploy")) else "strong"
            return _result(
                "Eso toca una zona sensible. No lo ejecutaré ni lo aprobaré; puedo preparar una preview para revisión con gates.",
                intent_detected="sensitive_action_requires_approval",
                confidence=0.88,
                risk_level="critical",
                approval_level=approval_level,
                requires_approval=True,
                can_prepare_preview=True,
                cannot_execute_reason="Requiere clasificación de riesgo, ApprovalGateway, readback cuando aplique, auditoría y rollback/stop plan.",
                suggested_next_action="Preparar preview con alcance exacto y dejar Hermes bloqueado hasta aprobación válida.",
            )

        if has_wake_phrase and not command_text:
            return _result(
                "Estoy aquí. Tomo la wake phrase como activación futura, no como permiso. Dime qué quieres preparar.",
                intent_detected="wake_phrase_activation_preview",
                confidence=0.86,
                risk_level="low",
                approval_level="direct",
                requires_approval=False,
                can_prepare_preview=True,
                cannot_execute_reason="Wake phrase nunca aprueba, ejecuta ni despacha Hermes.",
                suggested_next_action="Indicar la tarea o pregunta que debe quedar en preview.",
            )

        if _matches(command_text or lower, r"\b(revisa|prepara|analiza|resume|organiza|planifica|investiga|mision|misión|tarea|proyecto|siguiente paso)\b"):
            intent_text = command_text or lower
            intent = "task_preview" if _matches(intent_text, r"\b(tarea|organiza|planifica)\b") else "mission_preview" if _matches(intent_text, r"\b(mision|misión|proyecto|investiga|analiza)\b") else "task_preview"
            return _result(
                "Puedo preparar eso como preview: objetivo, alcance, riesgo y siguiente paso seguro. No despacharé Hermes desde aquí.",
                intent_detected=intent,
                confidence=0.82,
                risk_level="low",
                approval_level="direct",
                requires_approval=False,
                can_prepare_preview=True,
                cannot_execute_reason="Frontend/voz no ejecutan Hermes directamente; falta flujo gobernado de preview, aprobación y despacho.",
                suggested_next_action="Preparar una preview con alcance exacto y criterios de éxito.",
            )

        if _matches(command_text or lower, r"\b(estado|status|como vas|cómo vas|como vamos|cómo vamos|doctor|policy|evento|stream)\b"):
            return _result(
                "Puedo resumir el estado visible: control-plane local, sensores opt-in y Hermes detrás de gates.",
                intent_detected="query_system_status",
                confidence=0.78,
                risk_level="low",
                approval_level="direct",
                requires_approval=False,
                can_prepare_preview=True,
                cannot_execute_reason="La consulta es read-only; no hay ejecución solicitada.",
                suggested_next_action="Mostrar estado dashboard/doctor/event stream en modo lectura.",
            )

        if _matches(command_text or lower, r"\b(que puedes hacer|qué puedes hacer|para que sirves|para qué sirves|capacidad|capacidades|quien eres|quién eres)\b"):
            return _result(
                "Soy JARVIS en modo local: clasifico intención, riesgo y gates. Hermes ejecuta solo en un flujo gobernado futuro.",
                intent_detected="capability_or_identity_question",
                confidence=0.77,
                risk_level="none",
                approval_level="direct",
                requires_approval=False,
                can_prepare_preview=False,
                cannot_execute_reason="Es una pregunta informativa; no requiere ejecución.",
                suggested_next_action="Pedir una preview concreta o revisar el dashboard.",
            )

        if "?" in normalized or normalized.startswith(("que ", "qué ", "como ", "cómo ", "cuando ", "cuándo ", "puedes ", "sabes ")):
            return _result(
                "Puedo contestar en local si es sobre mi estado o preparar una preview si implica trabajo. Para datos externos hace falta un flujo gobernado.",
                intent_detected="simple_question",
                confidence=0.66,
                risk_level="none",
                approval_level="direct",
                requires_approval=False,
                can_prepare_preview=True,
                cannot_execute_reason="No hay ruta de datos externos o ejecución conectada en este bridge.",
                suggested_next_action="Hacer una pregunta concreta o pedir una preview segura.",
            )

        return _result(
            "No lo tengo claro todavía. Dame una acción o pregunta concreta y preparo el siguiente paso seguro.",
            intent_detected="needs_clarification",
            confidence=0.38,
            risk_level="none",
            approval_level="direct",
            requires_approval=False,
            can_prepare_preview=False,
            cannot_execute_reason="La intención no es suficientemente clara.",
            suggested_next_action="Reformular como pregunta o preview concreta.",
        )

    def status(self) -> Dict[str, Any]:
        sample = self.analyze("JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro.").to_dict()
        return {
            "schema_version": CONVERSATIONAL_BRAIN_SCHEMA_VERSION,
            "state": {
                "mode": "local_deterministic_bridge",
                "llm_provider": "none",
                "llm_called": False,
                "external_provider_called": False,
                "memory_autosave_enabled": False,
                "hermes_dispatch_allowed": False,
                "transcript_persistence": False,
                "preview_only": True,
                "read_only": True,
            },
            "sample_analysis": sample,
            "output_contract": [
                "human_response",
                "intent_detected",
                "confidence",
                "risk_level",
                "approval_level",
                "requires_approval",
                "can_prepare_preview",
                "cannot_execute_reason",
                "suggested_next_action",
                "hermes_dispatch_allowed",
            ],
            "safety": {
                "no_echo_only_response": True,
                "no_external_api": True,
                "no_network": True,
                "no_memory_autosave": True,
                "no_hermes_execution": True,
                "no_approval_from_wake_phrase": True,
                "denies_secret_credential_env_access": True,
            },
            "source_endpoint": "/mark-3/conversational-brain/status",
            "preview_only": True,
            "read_only": True,
        }


def normalize_utterance(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def split_wake_phrase(normalized_lower_text: str) -> Tuple[bool, str]:
    text = normalized_lower_text.strip()
    for phrase in WAKE_PHRASES:
        if re.match(rf"^{re.escape(phrase)}(?:\b|[\s,;:!.?])", text):
            return True, text[len(phrase) :].lstrip(" \t,;:!.?¿¡-")
    return False, text


def _result(
    human_response: str,
    *,
    intent_detected: str,
    confidence: float,
    risk_level: str,
    approval_level: str,
    requires_approval: bool,
    can_prepare_preview: bool,
    cannot_execute_reason: str,
    suggested_next_action: str,
) -> ConversationalBrainResult:
    result = ConversationalBrainResult(
        human_response=human_response,
        intent_detected=intent_detected,
        confidence=confidence,
        risk_level=risk_level,
        approval_level=approval_level,
        requires_approval=requires_approval,
        can_prepare_preview=can_prepare_preview,
        cannot_execute_reason=cannot_execute_reason,
        suggested_next_action=suggested_next_action,
    )
    result.validate()
    return result


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    folded = text.casefold()
    return any(marker.casefold() in folded for marker in markers)


def _matches(text: str, pattern: str) -> bool:
    return re.search(pattern, text.casefold(), flags=re.IGNORECASE | re.UNICODE) is not None


def _clamp_confidence(value: float) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    if confidence < 0.0:
        return 0.0
    if confidence > 1.0:
        return 1.0
    return round(confidence, 2)
