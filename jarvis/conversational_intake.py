from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from jarvis.wake_voice_runtime import normalize_confidence


CONVERSATIONAL_INTAKE_SCHEMA_VERSION = "jarvis.conversational_intake.v1"
CONVERSATIONAL_CLASSIFICATION_SCHEMA_VERSION = "jarvis.conversational_classification.v1"

SUPPORTED_SOURCES: Tuple[str, ...] = (
    "typed_text",
    "voice_transcript",
    "wake_phrase_command",
    "remote_input",
    "unknown",
)

WAKE_PHRASES: Tuple[Tuple[str, str], ...] = (
    ("hola jarvis", "Hola Jarvis"),
    ("jarvis", "Jarvis"),
)

STOP_PHRASES: Tuple[str, ...] = (
    "para",
    "cancela",
    "detente",
    "silencio",
    "cancelar misión",
    "cancelar mision",
    "apaga escucha",
    "stop",
)

LOW_TRANSCRIPT_CONFIDENCE_THRESHOLD = 0.80

_SENSITIVE_PATTERNS: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\.env\b", re.IGNORECASE), "environment_config_request"),
    (re.compile(r"\b(api\s*key|apikey|authorization|bearer|private\s*key)\b", re.IGNORECASE), "credential_material_request"),
    (re.compile(r"\b(password|contrase(?:ñ|n)a|passphrase)\b", re.IGNORECASE), "credential_material_request"),
    (re.compile(r"\b(cookie|cookies)\b", re.IGNORECASE), "browser_session_material_request"),
    (re.compile(r"\b(session\s*(?:material|token|cookie)|sesion\s+activa|sesión\s+activa)\b", re.IGNORECASE), "browser_session_material_request"),
    (re.compile(r"\b(token|secreto|secret|credencial|credenciales)\b", re.IGNORECASE), "credential_material_request"),
)

_APPROVAL_OR_EXECUTION_MARKERS = (
    "aprueba",
    "aprobar",
    "aprobado",
    "confirmo",
    "continua",
    "continúa",
    "ejecuta",
    "hazlo",
)

_DENIED_MARKERS = (
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

_DEPLOY_MARKERS = (
    "deploy",
    "despliega",
    "desplegar",
    "produccion",
    "producción",
    "production",
    "release",
)

_MONEY_MARKERS = (
    "dinero",
    "stripe",
    "pago",
    "pagos",
    "payment",
    "payments",
    "checkout",
    "charge",
    "transferencia",
    "refund",
)

_EMAIL_MARKERS = (
    "email",
    "emails",
    "correo",
    "mensaje externo",
    "envia",
    "envía",
    "newsletter",
)

_DEPENDENCY_MARKERS = (
    "npm install",
    "pip install",
    "instala dependencia",
    "instalar dependencia",
    "instala paquete",
    "instalar paquete",
    "apt install",
)

_COMMAND_EXECUTION_MARKERS = (
    "ejecuta comando",
    "ejecutar comando",
    "run command",
    "shell",
    "terminal",
    "bash",
    "subprocess",
)


@dataclass(frozen=True)
class ConversationalIntake:
    schema_version: str = CONVERSATIONAL_INTAKE_SCHEMA_VERSION
    intake_id: str = field(default_factory=lambda: f"intake_{uuid4()}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "typed_text"
    raw_text: str = ""
    normalized_text: str = ""
    language: str = "unknown"
    wake_phrase_detected: bool = False
    wake_phrase_used: Optional[str] = None
    remaining_command: str = ""
    operator: str = "David"
    session_id: Optional[str] = None
    voice_session_state: str = "idle"
    transcript_confidence: float = 1.0
    contains_sensitive_request: bool = False
    sensitive_reasons: List[str] = field(default_factory=list)
    requires_clarification: bool = False
    safe_to_classify: bool = True
    safe_to_prepare_preview: bool = False
    safe_to_dispatch_to_hermes: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", self.source if self.source in SUPPORTED_SOURCES else "unknown")
        object.__setattr__(self, "transcript_confidence", normalize_confidence(self.transcript_confidence))
        object.__setattr__(self, "sensitive_reasons", list(dict.fromkeys(self.sensitive_reasons)))
        object.__setattr__(self, "safe_to_dispatch_to_hermes", False)

    def validate(self) -> None:
        if self.safe_to_dispatch_to_hermes:
            raise ValueError("conversational intake cannot dispatch Hermes")
        if self.contains_sensitive_request and self.safe_to_prepare_preview:
            raise ValueError("sensitive credential/session material cannot be previewed as executable work")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)

    def redacted_for_brain(self) -> Dict[str, Any]:
        data = self.to_dict()
        if self.contains_sensitive_request:
            data["raw_text"] = "[redacted sensitive conversational input]"
            data["normalized_text"] = "[redacted sensitive conversational input]"
            data["remaining_command"] = ""
        return data


@dataclass(frozen=True)
class ConversationalClassification:
    schema_version: str = CONVERSATIONAL_CLASSIFICATION_SCHEMA_VERSION
    intent_detected: str = "needs_clarification"
    confidence: float = 0.0
    risk_level: str = "none"
    approval_level: str = "direct"
    requires_approval: bool = False
    can_prepare_preview: bool = False
    requires_clarification: bool = True
    denied: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    sensitive_reasons: List[str] = field(default_factory=list)
    next_safe_action: str = "clarify_request"
    safe_to_dispatch_to_hermes: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", normalize_confidence(self.confidence))
        object.__setattr__(self, "blocked_reasons", list(self.blocked_reasons))
        object.__setattr__(self, "sensitive_reasons", list(self.sensitive_reasons))
        object.__setattr__(self, "safe_to_dispatch_to_hermes", False)

    def validate(self) -> None:
        if self.safe_to_dispatch_to_hermes:
            raise ValueError("classification cannot dispatch Hermes")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class ConversationalIntakeAnalysis:
    intake: ConversationalIntake
    classification: ConversationalClassification
    preview_candidate: Optional[Dict[str, Any]] = None
    audit_summary: Dict[str, Any] = field(default_factory=dict)
    preview_only: bool = True
    read_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "preview_only", True)
        object.__setattr__(self, "read_only", True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intake": self.intake.to_dict(),
            "classification": self.classification.to_dict(),
            "preview_candidate": self.preview_candidate,
            "audit_summary": dict(self.audit_summary),
            "preview_only": True,
            "read_only": True,
        }


class ConversationalIntakePipeline:
    """Prepare-only conversational intake for typed text, transcripts and future channels."""

    def build_intake(
        self,
        raw_text: str,
        *,
        source: str = "typed_text",
        operator: str = "David",
        session_id: Optional[str] = None,
        voice_session_state: str = "idle",
        transcript_confidence: float = 1.0,
    ) -> ConversationalIntake:
        raw = str(raw_text or "")
        normalized = normalize_text(raw)
        confidence = normalize_confidence(transcript_confidence)
        wake_detected, wake_used, remaining_command = split_wake_phrase(raw)
        sensitive_reasons = detect_sensitive_reasons(normalized)
        command_text = normalize_text(remaining_command if wake_detected else normalized)
        low_confidence = confidence < LOW_TRANSCRIPT_CONFIDENCE_THRESHOLD and source in {"voice_transcript", "wake_phrase_command"}
        ambiguous = _is_ambiguous(command_text)
        requires_clarification = not normalized or low_confidence or ambiguous or (wake_detected and not command_text)
        safe_to_classify = bool(normalized) and not low_confidence
        safe_to_prepare_preview = bool(command_text) and safe_to_classify and not sensitive_reasons and not ambiguous

        return ConversationalIntake(
            source=source,
            raw_text=raw,
            normalized_text=normalized,
            language=detect_language(normalized),
            wake_phrase_detected=wake_detected,
            wake_phrase_used=wake_used,
            remaining_command=command_text,
            operator=str(operator or "David"),
            session_id=session_id,
            voice_session_state=str(voice_session_state or "idle"),
            transcript_confidence=confidence,
            contains_sensitive_request=bool(sensitive_reasons),
            sensitive_reasons=sensitive_reasons,
            requires_clarification=requires_clarification,
            safe_to_classify=safe_to_classify,
            safe_to_prepare_preview=safe_to_prepare_preview,
            safe_to_dispatch_to_hermes=False,
        )

    def classify(self, intake: ConversationalIntake) -> ConversationalClassification:
        text = (intake.remaining_command or intake.normalized_text).casefold()
        normalized = intake.normalized_text.casefold()

        if not intake.normalized_text:
            return _classification(
                "needs_clarification",
                0.20,
                "none",
                "direct",
                False,
                False,
                True,
                ["empty conversational input"],
                "ask_for_clear_request",
            )

        if not intake.safe_to_classify:
            return _classification(
                "low_confidence_needs_clarification",
                min(intake.transcript_confidence, 0.45),
                "none",
                "direct",
                False,
                False,
                True,
                ["low transcript confidence blocks classification"],
                "ask_operator_to_repeat",
            )

        if intake.contains_sensitive_request:
            return _classification(
                "denied_secret_or_credential_access",
                0.97,
                "forbidden",
                "forbidden",
                False,
                False,
                False,
                ["credential/session material is denied and not dispatched"],
                "redesign_without_credential_material",
                denied=True,
                sensitive_reasons=intake.sensitive_reasons,
            )

        if _exact_stop_or_cancel(text):
            return _classification(
                "voice_stop_or_cancel",
                0.90,
                "low",
                "direct",
                False,
                False,
                False,
                ["stop/cancel is session control, not approval"],
                "stop_or_idle_voice_session",
            )

        if intake.wake_phrase_detected and _contains_any(text, _APPROVAL_OR_EXECUTION_MARKERS):
            return _classification(
                "wake_phrase_approval_or_execution_attempt",
                0.95,
                "forbidden",
                "forbidden",
                False,
                False,
                False,
                ["wake phrase cannot approve and cannot execute"],
                "request_preview_without_wake_approval",
                denied=True,
            )

        if _contains_any(normalized, _DENIED_MARKERS):
            return _classification(
                "denied_unsafe_unauthorized_or_illegal",
                0.91,
                "forbidden",
                "forbidden",
                False,
                False,
                False,
                ["unsafe, unauthorized or illegal request"],
                "reformulate_safe_authorized_request",
                denied=True,
            )

        if intake.requires_clarification:
            intent = "wake_phrase_activation_needs_command" if intake.wake_phrase_detected else "needs_clarification"
            return _classification(
                intent,
                0.42,
                "none",
                "direct",
                False,
                False,
                True,
                ["ambiguous conversational input"],
                "ask_clarifying_question",
            )

        if _contains_any(text, _MONEY_MARKERS):
            return _classification(
                "money_or_stripe_requires_strong_gate",
                0.91,
                "critical",
                "triple",
                True,
                True,
                False,
                ["money, Stripe or payment action requires strong gated review"],
                "prepare_sensitive_preview_for_operator_review",
            )

        if _contains_any(text, _DEPLOY_MARKERS):
            return _classification(
                "deploy_or_production_requires_strong_gate",
                0.90,
                "critical",
                "triple",
                True,
                True,
                False,
                ["deploy, production or publication action requires strong gated review"],
                "prepare_sensitive_preview_for_operator_review",
            )

        if _contains_any(text, _EMAIL_MARKERS):
            return _classification(
                "external_message_requires_strong_gate",
                0.86,
                "high",
                "strong",
                True,
                True,
                False,
                ["external email or messaging requires gated review"],
                "prepare_message_preview_without_sending",
            )

        if _contains_any(text, _DEPENDENCY_MARKERS):
            return _classification(
                "dependency_install_requires_strong_gate",
                0.88,
                "high",
                "strong",
                True,
                True,
                False,
                ["dependency installation requires gated review"],
                "prepare_installation_preview_without_installing",
            )

        if _contains_any(text, _COMMAND_EXECUTION_MARKERS):
            return _classification(
                "command_execution_requires_strong_gate",
                0.87,
                "high",
                "strong",
                True,
                True,
                False,
                ["command execution requires gated review"],
                "prepare_command_preview_without_execution",
            )

        if _is_exact_local_file_read(text):
            return _classification(
                "read_exact_local_file_preview",
                0.82,
                "medium",
                "simple",
                True,
                True,
                False,
                ["exact bounded local read requires review before future dispatch"],
                "prepare_bounded_read_preview",
            )

        if re.search(r"\b(estado|status|como vas|cómo vas|como vamos|cómo vamos|doctor|policy|evento|stream)\b", text):
            return _classification(
                "query_system_status",
                0.80,
                "low",
                "direct",
                False,
                True,
                False,
                [],
                "show_read_only_dashboard_status",
            )

        if re.search(r"\b(revisa|review|proyecto|project)\b", text):
            return _classification(
                "project_review_preview",
                0.82,
                "low",
                "direct",
                False,
                True,
                False,
                [],
                "prepare_project_review_preview",
            )

        if re.search(r"\b(mision|misión|mission|investiga|analiza|analysis|research)\b", text):
            return _classification(
                "mission_preview",
                0.82,
                "low",
                "direct",
                False,
                True,
                False,
                [],
                "prepare_mission_preview",
            )

        if re.search(r"\b(tarea|task|organiza|planifica|prepara|preparar|resume|lista)\b", text):
            return _classification(
                "task_preview",
                0.80,
                "low",
                "direct",
                False,
                True,
                False,
                [],
                "prepare_task_preview",
            )

        if _is_simple_question(intake.normalized_text):
            return _classification(
                "simple_question",
                0.72,
                "none",
                "direct",
                False,
                False,
                False,
                [],
                "answer_locally_or_ask_for_scope",
            )

        return _classification(
            "needs_clarification",
            0.38,
            "none",
            "direct",
            False,
            False,
            True,
            ["intent is not clear enough"],
            "ask_clarifying_question",
        )

    def prepare_preview_candidate(
        self,
        intake: ConversationalIntake,
        classification: ConversationalClassification,
    ) -> Optional[Dict[str, Any]]:
        if not classification.can_prepare_preview or classification.denied or classification.requires_clarification:
            return None
        goal = intake.remaining_command or intake.normalized_text
        return {
            "preview_id": f"preview_{intake.intake_id}",
            "title": _preview_title(classification.intent_detected),
            "user_visible_goal": goal,
            "intent_detected": classification.intent_detected,
            "risk_level": classification.risk_level,
            "approval_level": classification.approval_level,
            "requires_approval": classification.requires_approval,
            "next_safe_action": classification.next_safe_action,
            "would_execute": False,
            "would_call_hermes": False,
            "hermes_dispatch_allowed": False,
            "external_provider_called": False,
            "memory_write": False,
            "preview_only": True,
            "read_only": True,
        }

    def process(
        self,
        raw_text: str,
        *,
        source: str = "typed_text",
        operator: str = "David",
        session_id: Optional[str] = None,
        voice_session_state: str = "idle",
        transcript_confidence: float = 1.0,
    ) -> ConversationalIntakeAnalysis:
        intake = self.build_intake(
            raw_text,
            source=source,
            operator=operator,
            session_id=session_id,
            voice_session_state=voice_session_state,
            transcript_confidence=transcript_confidence,
        )
        classification = self.classify(intake)
        preview = self.prepare_preview_candidate(intake, classification)
        return ConversationalIntakeAnalysis(
            intake=intake,
            classification=classification,
            preview_candidate=preview,
            audit_summary={
                "received_text": True,
                "normalized": True,
                "wake_phrase_checked": True,
                "sensitive_material_checked": True,
                "intent_classified": classification.intent_detected,
                "risk_classified": classification.risk_level,
                "approval_is_not_execution": True,
                "hermes_dispatch_allowed": False,
                "external_provider_called": False,
                "read_only": True,
            },
        )

    def status(self) -> Dict[str, Any]:
        sample = self.process("JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro.").to_dict()
        return {
            "schema_version": CONVERSATIONAL_INTAKE_SCHEMA_VERSION,
            "state": {
                "mode": "prepare_only_conversational_intake",
                "default_source": "typed_text",
                "accepted_sources": list(SUPPORTED_SOURCES),
                "wake_phrase_detection": "start_of_utterance_only",
                "sensitive_material_detection": "deterministic_local",
                "risk_classification": "deterministic_local",
                "approval_is_not_execution": True,
                "safe_to_dispatch_to_hermes": False,
                "hermes_dispatch_allowed": False,
                "external_provider_called": False,
                "reads_env": False,
                "network_allowed": False,
                "preview_only": True,
                "read_only": True,
            },
            "sample": sample,
            "output_contract": [
                "schema_version",
                "intake_id",
                "created_at",
                "source",
                "raw_text",
                "normalized_text",
                "language",
                "wake_phrase_detected",
                "wake_phrase_used",
                "remaining_command",
                "operator",
                "session_id",
                "voice_session_state",
                "transcript_confidence",
                "contains_sensitive_request",
                "sensitive_reasons",
                "requires_clarification",
                "safe_to_classify",
                "safe_to_prepare_preview",
                "safe_to_dispatch_to_hermes",
            ],
            "safety": {
                "never_executes": True,
                "never_approves": True,
                "wake_phrase_never_approves": True,
                "wake_phrase_never_executes": True,
                "credential_material_blocked": True,
                "low_confidence_requires_clarification": True,
                "ambiguous_input_requires_clarification": True,
                "memory_never_grants_permission": True,
                "no_env_read": True,
                "no_network": True,
                "no_external_llm": True,
                "no_raw_audio": True,
                "no_camera_frames": True,
            },
            "source_endpoint": "/mark-3/conversational-intake/status",
            "preview_only": True,
            "read_only": True,
        }


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def split_wake_phrase(text: str) -> Tuple[bool, Optional[str], str]:
    raw = str(text or "").strip()
    folded = raw.casefold()
    for phrase, display in WAKE_PHRASES:
        match = re.match(rf"^{re.escape(phrase)}(?:\b|[\s,;:!.?¿¡-])?", folded)
        if match:
            remainder = raw[match.end() :].lstrip(" \t,;:!.?¿¡-")
            return True, display, normalize_text(remainder)
    return False, None, ""


def detect_sensitive_reasons(text: str) -> List[str]:
    reasons: List[str] = []
    for pattern, reason in _SENSITIVE_PATTERNS:
        if pattern.search(text):
            reasons.append(reason)
    return list(dict.fromkeys(reasons))


def detect_language(text: str) -> str:
    folded = text.casefold()
    if not folded:
        return "unknown"
    if re.search(r"[áéíóúñ¿¡]", folded) or re.search(r"\b(hola|como|cómo|que|qué|revisa|prepara|mision|misión|tarea|estado)\b", folded):
        return "es"
    if re.search(r"\b(what|how|review|prepare|task|mission|status)\b", folded):
        return "en"
    return "unknown"


def _classification(
    intent: str,
    confidence: float,
    risk: str,
    approval: str,
    requires_approval: bool,
    can_prepare_preview: bool,
    requires_clarification: bool,
    blocked_reasons: List[str],
    next_safe_action: str,
    *,
    denied: bool = False,
    sensitive_reasons: Optional[List[str]] = None,
) -> ConversationalClassification:
    return ConversationalClassification(
        intent_detected=intent,
        confidence=confidence,
        risk_level=risk,
        approval_level=approval,
        requires_approval=requires_approval,
        can_prepare_preview=can_prepare_preview,
        requires_clarification=requires_clarification,
        denied=denied,
        blocked_reasons=blocked_reasons,
        sensitive_reasons=sensitive_reasons or [],
        next_safe_action=next_safe_action,
    )


def _contains_any(text: str, markers: Tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _exact_stop_or_cancel(text: str) -> bool:
    normalized = normalize_text(text).casefold()
    return normalized in STOP_PHRASES


def _is_ambiguous(text: str) -> bool:
    folded = normalize_text(text).casefold()
    if not folded:
        return True
    if folded in {"ok", "vale", "si", "sí", "hazlo", "eso", "dale", "continua", "continúa"}:
        return True
    return len(folded) < 4


def _is_simple_question(text: str) -> bool:
    folded = normalize_text(text).casefold()
    return "?" in text or "¿" in text or bool(re.match(r"^(que|qué|como|cómo|cuando|cuándo|donde|dónde|puedes|sabes|hay|estas|estás)\b", folded))


def _is_exact_local_file_read(text: str) -> bool:
    if not re.search(r"\b(lee|leer|read|abre|abrir|open|muestra|show)\b", text):
        return False
    if "archivo" not in text and "file" not in text and "/" not in text and "\\" not in text:
        return False
    return bool(re.search(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+|[A-Za-z0-9_.-]+\.[A-Za-z0-9]{1,8})", text))


def _preview_title(intent: str) -> str:
    if intent == "read_exact_local_file_preview":
        return "Bounded Local File Read Preview"
    if "deploy" in intent:
        return "Deploy/Production Preview"
    if "money" in intent or "stripe" in intent:
        return "Money/Payments Preview"
    if "message" in intent:
        return "External Message Preview"
    if "install" in intent:
        return "Dependency Installation Preview"
    if "command" in intent:
        return "Command Execution Preview"
    if "project" in intent:
        return "Project Review Preview"
    if "mission" in intent:
        return "Mission Preview"
    if "task" in intent:
        return "Task Preview"
    return "Conversational Preview"
