from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class VoiceIntent:
    status: str
    intent: str
    transcript: str
    normalized_text: str
    executed: bool
    confidence: str
    tone: str
    needs_clarification: bool
    reason: str
    slots: dict[str, Any]
    inferred_goal: str | None = None
    user_context_signals: dict[str, Any] | None = None
    recommended_next_step: str | None = None
    approval_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UserUnderstandingProfile:
    preferred_name: str = "David"
    input_language: str = "es"
    output_language: str = "es"
    communication_style: dict[str, Any] = field(
        default_factory=lambda: {
            "default_language": "es",
            "prefers_direct_responses": True,
            "prefers_practical_next_steps": True,
            "confidence_should_be_explicit": True,
        }
    )
    common_phrases: tuple[str, ...] = (
        "crea",
        "hazme",
        "monta",
        "prepara",
        "quiero validar",
        "vamos a investigar",
        "no funciona",
    )
    intent_aliases: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "create_asset": ("landing", "web", "herramienta", "micro saas", "microsaas"),
            "create_mission": ("investigar", "analiza", "nicho"),
            "create_task": ("tarea", "apúntame", "recuérdame"),
            "query_status": ("estado", "cómo vamos", "resume mis tareas"),
        }
    )
    business_goals: tuple[str, ...] = (
        "crear activos digitales",
        "validar ideas",
        "automatizar trabajo",
        "mejorar retorno por tiempo invertido",
    )
    monetization_preferences: tuple[str, ...] = (
        "afiliación",
        "micro saas",
        "herramientas digitales",
        "activos monetizables",
    )
    risk_tolerance: str = "controlled"
    execution_style: str = "pragmatic_iterative"
    decision_style: str = "evidence_based"
    clarification_preferences: dict[str, Any] = field(
        default_factory=lambda: {
            "ask_when_confidence_low": True,
            "ask_before_sensitive_actions": True,
            "avoid_fake_certainty": True,
        }
    )
    common_create_words: tuple[str, ...] = ("crea", "crear", "créame", "haz", "hazme", "monta", "prepara", "añade")
    common_asset_words: tuple[str, ...] = (
        "landing",
        "web",
        "página",
        "pagina",
        "herramienta",
        "micro saas",
        "microsaas",
        "idea",
    )
    common_task_words: tuple[str, ...] = ("tarea", "apúntame", "apuntame", "recuérdame", "recuerdame")
    common_mission_words: tuple[str, ...] = ("misión", "mision", "investigar", "investiga", "analiza", "nicho")
    common_status_words: tuple[str, ...] = (
        "estado",
        "qué estás haciendo",
        "que estas haciendo",
        "cómo vamos",
        "como vamos",
        "resume mis tareas",
        "qué hay pendiente",
        "que hay pendiente",
        "status",
        "what are you doing",
    )
    sensitive_words: tuple[str, ...] = (
        ".env",
        "credenciales",
        "password",
        "token",
        "borra",
        "elimina",
        "pago",
        "compra",
        "publica",
        "contrato",
        "email importante",
        "dominio",
        "tarjeta",
        "banco",
    )
    sensitive_boundaries: tuple[str, ...] = (
        "credenciales",
        "secretos",
        "dinero",
        "publicación",
        "borrado",
        "identidad",
        "contratos",
    )
    approval_preferences: dict[str, Any] = field(
        default_factory=lambda: {
            "approval_gateway_required_for_sensitive_actions": True,
            "voice_only_confirmation_is_not_enough": True,
            "prefer_visual_or_written_confirmation": True,
        }
    )
    contrarian_triggers: tuple[str, ...] = (
        "riesgo de autoengaño",
        "priorización débil",
        "acción sensible",
        "baja confianza",
        "coste alto",
    )
    learning_notes: tuple[str, ...] = (
        "Estructura preparada para aprendizaje futuro sin persistencia automática.",
        "No inferir información privada sin evidencia explícita.",
        "Preguntar cuando haya baja confianza o ambigüedad.",
    )
    control_phrases: tuple[str, ...] = (
        "hola jarvis",
        "jarvis",
        "jarvis no escuches",
        "jarvis silencio",
        "jarvis duerme",
    )
    tone_markers: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "urgent": ("rápido", "rapido", "urgente", "ya", "ahora"),
            "frustrated": ("no funciona", "otra vez", "me tiene harto", "fallo"),
            "exploratory": ("quizá", "quiza", "podríamos", "podriamos", "idea", "se me ocurre"),
            "direct": ("crea", "crear", "haz", "hazme", "monta", "prepara"),
        }
    )

    @property
    def frustration_markers(self) -> tuple[str, ...]:
        return self.tone_markers["frustrated"]

    @property
    def urgency_markers(self) -> tuple[str, ...]:
        return self.tone_markers["urgent"]

    @property
    def exploratory_markers(self) -> tuple[str, ...]:
        return self.tone_markers["exploratory"]


VoiceUserLanguageProfile = UserUnderstandingProfile
DavidUnderstandingProfile = UserUnderstandingProfile


class VoiceIntentRouter:
    def __init__(self, profile: UserUnderstandingProfile | None = None) -> None:
        self.profile = profile or UserUnderstandingProfile()

    def classify(self, text: str) -> VoiceIntent:
        normalized = self._normalize_text(text)
        tone = self._detect_tone(normalized)
        language = self._detect_language(normalized)
        sensitive_terms = self._matching_terms(normalized, self.profile.sensitive_words)
        slots: dict[str, Any] = {
            "raw_subject": text,
            "language": language,
        }
        context_signals = self._context_signals(normalized)

        if sensitive_terms:
            slots["sensitive_terms"] = sensitive_terms
            return self._intent(
                status="requires_approval",
                intent="requires_approval",
                transcript=text,
                normalized_text=normalized,
                confidence="high",
                tone=tone,
                needs_clarification=False,
                reason="Sensitive voice instruction requires approval before any execution.",
                slots=slots,
                inferred_goal="sensitive_action_request",
                user_context_signals=context_signals,
                recommended_next_step="Route through ApprovalGateway before any execution.",
                approval_required=True,
            )

        if normalized in self.profile.control_phrases:
            return self._intent(
                status="handled",
                intent="control",
                transcript=text,
                normalized_text=normalized,
                confidence="high",
                tone=tone,
                needs_clarification=False,
                reason="Matched a local voice runtime control phrase.",
                slots=slots,
                inferred_goal="voice_runtime_control",
                user_context_signals=context_signals,
                recommended_next_step="Apply local runtime control state only.",
            )

        asset_type = self._detect_asset_type(normalized)
        if self._matches_create_asset(normalized):
            if asset_type:
                slots["asset_type"] = asset_type
            return self._intent(
                status="pending",
                intent="create_asset",
                transcript=text,
                normalized_text=normalized,
                confidence="high",
                tone=tone,
                needs_clarification=False,
                reason="Matched a local create-asset phrase.",
                slots=slots,
                inferred_goal=self._infer_goal(normalized, "create_asset"),
                user_context_signals=context_signals,
                recommended_next_step="Ask for missing scope or prepare a non-executing asset plan.",
            )

        if self._matches_create_task(normalized):
            return self._intent(
                status="pending",
                intent="create_task",
                transcript=text,
                normalized_text=normalized,
                confidence="high",
                tone=tone,
                needs_clarification=False,
                reason="Matched a local create-task phrase.",
                slots=slots,
                inferred_goal=self._infer_goal(normalized, "create_task"),
                user_context_signals=context_signals,
                recommended_next_step="Convert to a task proposal after future policy routing.",
            )

        if self._matches_create_mission(normalized):
            return self._intent(
                status="pending",
                intent="create_mission",
                transcript=text,
                normalized_text=normalized,
                confidence="high",
                tone=tone,
                needs_clarification=False,
                reason="Matched a local create-mission or investigation phrase.",
                slots=slots,
                inferred_goal=self._infer_goal(normalized, "create_mission"),
                user_context_signals=context_signals,
                recommended_next_step="Prepare a mission proposal after future policy routing.",
            )

        if self._matches_query_status(normalized):
            return self._intent(
                status="pending",
                intent="query_status",
                transcript=text,
                normalized_text=normalized,
                confidence="high",
                tone=tone,
                needs_clarification=False,
                reason="Matched a local status query phrase.",
                slots=slots,
                inferred_goal="understand_current_system_state",
                user_context_signals=context_signals,
                recommended_next_step="Return status summary in a future read-only runtime flow.",
            )

        related_terms = self._matching_terms(
            normalized,
            (
                *self.profile.common_create_words,
                *self.profile.common_asset_words,
                *self.profile.common_task_words,
                *self.profile.common_mission_words,
            ),
        )
        if related_terms:
            if asset_type:
                slots["asset_type"] = asset_type
            return self._intent(
                status="pending",
                intent="create_asset" if asset_type else "unsupported",
                transcript=text,
                normalized_text=normalized,
                confidence="medium",
                tone=tone,
                needs_clarification=True,
                reason=f"Matched related terms but needs clarification: {', '.join(related_terms)}.",
                slots=slots,
                inferred_goal=self._infer_goal(normalized, "create_asset" if asset_type else "ambiguous_request"),
                user_context_signals=context_signals,
                recommended_next_step="Ask a clarifying question before creating any task or mission.",
            )

        return self._intent(
            status="unsupported",
            intent="unsupported",
            transcript=text,
            normalized_text=normalized,
            confidence="low",
            tone=tone,
            needs_clarification=True,
            reason="No local intent rule matched.",
            slots=slots,
            inferred_goal=None,
            user_context_signals=context_signals,
            recommended_next_step="Ask a clarifying question.",
        )

    def _intent(
        self,
        *,
        status: str,
        intent: str,
        transcript: str,
        normalized_text: str,
        confidence: str,
        tone: str,
        needs_clarification: bool,
        reason: str,
        slots: dict[str, Any],
        inferred_goal: str | None = None,
        user_context_signals: dict[str, Any] | None = None,
        recommended_next_step: str | None = None,
        approval_required: bool = False,
    ) -> VoiceIntent:
        return VoiceIntent(
            status=status,
            intent=intent,
            transcript=transcript,
            normalized_text=normalized_text,
            executed=False,
            confidence=confidence,
            tone=tone,
            needs_clarification=needs_clarification,
            reason=reason,
            slots=slots,
            inferred_goal=inferred_goal,
            user_context_signals=user_context_signals,
            recommended_next_step=recommended_next_step,
            approval_required=approval_required,
        )

    def _matches_create_mission(self, text: str) -> bool:
        return self._contains_any(
            text,
            (
                "crea una misión",
                "crea una mision",
                "crear una misión",
                "crear una mision",
                "nueva misión",
                "nueva mision",
                "quiero investigar",
                "vamos a investigar",
                "analiza este nicho",
                "create a mission",
            ),
        )

    def _matches_create_task(self, text: str) -> bool:
        return self._contains_any(
            text,
            (
                "crea una tarea",
                "crear tarea",
                "añade una tarea",
                "anade una tarea",
                "apúntame esto",
                "apuntame esto",
                "recuérdame hacer",
                "recuerdame hacer",
                "create a task",
            ),
        )

    def _matches_create_asset(self, text: str) -> bool:
        return self._contains_any(
            text,
            (
                "crea una landing",
                "hazme una landing",
                "monta una web",
                "créame una web",
                "creame una web",
                "prepara una página",
                "prepara una pagina",
                "crea una herramienta",
                "monta algo para",
                "quiero validar esta idea",
                "crea un micro saas",
                "crea un microsaas",
                "create a landing",
                "create a website",
                "create a tool",
            ),
        )

    def _matches_query_status(self, text: str) -> bool:
        return self._contains_any(text, self.profile.common_status_words)

    def _detect_tone(self, text: str) -> str:
        for tone in ("urgent", "frustrated", "exploratory", "direct"):
            if self._contains_any(text, self.profile.tone_markers[tone]):
                return tone
        return "neutral"

    def _detect_language(self, text: str) -> str:
        english_markers = ("create ", "what are you", "status", " task", " mission", " website", " tool")
        if self._contains_any(text, english_markers):
            return "en"
        return self.profile.input_language

    def _detect_asset_type(self, text: str) -> str | None:
        asset_types = (
            ("landing", ("landing",)),
            ("website", ("web", "website", "página", "pagina")),
            ("tool", ("herramienta", "tool")),
            ("micro_saas", ("micro saas", "microsaas")),
        )
        for asset_type, terms in asset_types:
            if self._contains_any(text, terms):
                return asset_type
        return None

    def _infer_goal(self, text: str, intent: str) -> str:
        if self._contains_any(text, ("afiliados", "afiliación", "afiliacion")):
            return "monetization_or_affiliate_asset"
        if self._contains_any(text, ("nicho", "idea", "validar", "probar")):
            return "validate_business_opportunity"
        if intent == "create_task":
            return "capture_action_item"
        if intent == "create_mission":
            return "research_or_plan_work"
        if intent == "create_asset":
            return "create_digital_asset"
        return "understand_user_request"

    def _context_signals(self, text: str) -> dict[str, Any]:
        signals = {
            "business_or_monetization": self._contains_any(
                text,
                ("afiliados", "afiliación", "afiliacion", "nicho", "monetizar", "micro saas", "microsaas"),
            ),
            "technical_execution": self._contains_any(text, ("web", "landing", "herramienta", "proyecto")),
            "sensitive_boundary": self._contains_any(text, self.profile.sensitive_words),
            "contrarian_review_recommended": self._contains_any(
                text,
                ("hazlo ya", "rápido", "rapido", "borra", "compra", "publica"),
            ),
        }
        return signals

    @staticmethod
    def _matching_terms(text: str, terms: tuple[str, ...]) -> list[str]:
        return [term for term in terms if term in text]

    @staticmethod
    def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
        return any(term in text for term in terms)

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.strip().lower().split())
