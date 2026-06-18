from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.conversational_brain_bridge import ConversationalBrainBridge
from jarvis.conversational_intake import (
    ConversationalClassification,
    ConversationalIntake,
    ConversationalIntakeAnalysis,
    ConversationalIntakePipeline,
)


BRAIN_REQUEST_SCHEMA_VERSION = "jarvis.brain_request.v1"
BRAIN_RESPONSE_SCHEMA_VERSION = "jarvis.brain_response.v1"
BRAIN_PROVIDER_STATUS_SCHEMA_VERSION = "jarvis.brain_provider_status.v1"
BRAIN_ADAPTER_SCHEMA_VERSION = "jarvis.llm_brain_adapter.v1"

DEFAULT_BRAIN_PROVIDER = "deterministic_local"


@dataclass(frozen=True)
class BrainProviderStatus:
    schema_version: str = BRAIN_PROVIDER_STATUS_SCHEMA_VERSION
    provider_name: str = DEFAULT_BRAIN_PROVIDER
    provider_mode: str = "local_deterministic_prepare_only"
    available: bool = True
    default_provider: str = DEFAULT_BRAIN_PROVIDER
    external_llm_enabled: bool = False
    external_provider_called: bool = False
    api_key_required: bool = False
    api_key_loaded: bool = False
    reads_env: bool = False
    network_allowed: bool = False
    honest_status: str = "available_local_deterministic"
    missing_configuration: List[str] = field(default_factory=list)
    safety: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "default_provider", DEFAULT_BRAIN_PROVIDER)
        object.__setattr__(self, "external_llm_enabled", False)
        object.__setattr__(self, "external_provider_called", False)
        object.__setattr__(self, "api_key_loaded", False)
        object.__setattr__(self, "reads_env", False)
        object.__setattr__(self, "network_allowed", False)
        object.__setattr__(self, "missing_configuration", list(self.missing_configuration))
        safety = {
            "no_external_api": True,
            "no_network": True,
            "no_env_read": True,
            "no_secret_read": True,
            "no_prompt_persistence": True,
            "no_raw_audio": True,
            "no_camera_frames": True,
            "no_hermes_dispatch": True,
            **dict(self.safety),
        }
        object.__setattr__(self, "safety", safety)

    def validate(self) -> None:
        if self.external_llm_enabled:
            raise ValueError("external LLM providers are disabled by default")
        if self.external_provider_called:
            raise ValueError("external provider must not be called")
        if self.api_key_loaded:
            raise ValueError("brain adapter must not load API keys in this PR")
        if self.reads_env or self.network_allowed:
            raise ValueError("brain adapter cannot read env or use network")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class BrainRequest:
    schema_version: str = BRAIN_REQUEST_SCHEMA_VERSION
    request_id: str = ""
    intake: Dict[str, Any] = field(default_factory=dict)
    user_visible_goal: str = ""
    context_summary: str = ""
    allowed_context: List[str] = field(default_factory=list)
    forbidden_context: List[str] = field(default_factory=list)
    risk_constraints: Dict[str, Any] = field(default_factory=dict)
    policy_constraints: Dict[str, Any] = field(default_factory=dict)
    memory_policy: Dict[str, Any] = field(default_factory=dict)
    hermes_dispatch_policy: Dict[str, Any] = field(default_factory=dict)
    external_provider_policy: Dict[str, Any] = field(default_factory=dict)
    max_cost_budget: str = "not_configured"
    no_secrets: bool = True
    no_raw_audio: bool = True
    no_camera_frames: bool = True
    preview_only: bool = True
    read_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "no_secrets", True)
        object.__setattr__(self, "no_raw_audio", True)
        object.__setattr__(self, "no_camera_frames", True)
        object.__setattr__(self, "preview_only", True)
        object.__setattr__(self, "read_only", True)
        hermes_policy = {
            "dispatch_allowed": False,
            "safe_to_dispatch_to_hermes": False,
            "frontend_or_voice_can_call_hermes_directly": False,
            "approval_is_not_execution": True,
            **dict(self.hermes_dispatch_policy),
        }
        hermes_policy["dispatch_allowed"] = False
        hermes_policy["safe_to_dispatch_to_hermes"] = False
        external_policy = {
            "external_llm_enabled": False,
            "external_provider_called": False,
            "network_allowed": False,
            "reads_env": False,
            "may_call_provider": False,
            **dict(self.external_provider_policy),
        }
        external_policy["external_llm_enabled"] = False
        external_policy["external_provider_called"] = False
        external_policy["network_allowed"] = False
        external_policy["reads_env"] = False
        object.__setattr__(self, "hermes_dispatch_policy", hermes_policy)
        object.__setattr__(self, "external_provider_policy", external_policy)

    def validate(self) -> None:
        if self.hermes_dispatch_policy.get("dispatch_allowed") is not False:
            raise ValueError("BrainRequest cannot allow Hermes dispatch")
        if self.external_provider_policy.get("external_provider_called") is not False:
            raise ValueError("BrainRequest cannot call external providers")
        if self.external_provider_policy.get("reads_env") is not False:
            raise ValueError("BrainRequest cannot read environment")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class BrainResponse:
    schema_version: str = BRAIN_RESPONSE_SCHEMA_VERSION
    response_id: str = ""
    human_response: str = ""
    intent_detected: str = "needs_clarification"
    confidence: float = 0.0
    risk_level: str = "none"
    approval_level: str = "direct"
    requires_approval: bool = False
    can_prepare_preview: bool = False
    preview_candidate: Optional[Dict[str, Any]] = None
    cannot_execute_reason: str = ""
    suggested_next_action: str = ""
    clarification_question: Optional[str] = None
    memory_write_proposal: Optional[Dict[str, Any]] = None
    hermes_candidate: Optional[Dict[str, Any]] = None
    hermes_dispatch_allowed: bool = False
    external_provider_called: bool = False
    provider_name: str = DEFAULT_BRAIN_PROVIDER
    provider_mode: str = "local_deterministic_prepare_only"
    evidence: List[str] = field(default_factory=list)
    uncertainty: List[str] = field(default_factory=list)
    audit_summary: Dict[str, Any] = field(default_factory=dict)
    preview_only: bool = True
    read_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "hermes_dispatch_allowed", False)
        object.__setattr__(self, "external_provider_called", False)
        object.__setattr__(self, "evidence", list(self.evidence))
        object.__setattr__(self, "uncertainty", list(self.uncertainty))
        object.__setattr__(self, "audit_summary", dict(self.audit_summary))
        object.__setattr__(self, "preview_only", True)
        object.__setattr__(self, "read_only", True)

    def validate(self) -> None:
        if not self.human_response.strip():
            raise ValueError("human_response is required")
        if self.hermes_dispatch_allowed:
            raise ValueError("BrainResponse cannot allow Hermes dispatch by default")
        if self.external_provider_called:
            raise ValueError("BrainResponse cannot claim an external provider was called")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)


class DeterministicLocalBrainProvider:
    name = DEFAULT_BRAIN_PROVIDER
    mode = "local_deterministic_prepare_only"

    def __init__(self, *, bridge: Optional[ConversationalBrainBridge] = None) -> None:
        self.bridge = bridge or ConversationalBrainBridge()

    def status(self) -> BrainProviderStatus:
        return BrainProviderStatus(
            provider_name=self.name,
            provider_mode=self.mode,
            available=True,
            api_key_required=False,
            honest_status="available_local_deterministic_bridge_v2",
        )

    def respond(
        self,
        request: BrainRequest,
        *,
        analysis: ConversationalIntakeAnalysis,
    ) -> BrainResponse:
        intake = analysis.intake
        classification = analysis.classification
        bridge_result = self.bridge.analyze(intake.remaining_command or intake.normalized_text).to_dict()
        human_response = _human_response_for(classification, bridge_result)
        preview = analysis.preview_candidate
        hermes_candidate = _hermes_candidate_for(preview, classification)
        return BrainResponse(
            response_id=f"brain_{request.request_id}",
            human_response=human_response,
            intent_detected=classification.intent_detected,
            confidence=classification.confidence or float(bridge_result.get("confidence", 0.0)),
            risk_level=classification.risk_level,
            approval_level=classification.approval_level,
            requires_approval=classification.requires_approval,
            can_prepare_preview=classification.can_prepare_preview,
            preview_candidate=preview,
            cannot_execute_reason=_cannot_execute_reason(classification),
            suggested_next_action=classification.next_safe_action,
            clarification_question=_clarification_question(classification, intake),
            memory_write_proposal={
                "would_write_memory": False,
                "requires_explicit_review": True,
                "reason": "memory never grants permission and no automatic memory write is enabled",
            },
            hermes_candidate=hermes_candidate,
            hermes_dispatch_allowed=False,
            external_provider_called=False,
            provider_name=self.name,
            provider_mode=self.mode,
            evidence=[
                "Conversational intake normalized locally.",
                "Sensitive material detection used deterministic local markers.",
                "Conversational Brain Bridge v2 provided local deterministic response shape.",
                "No external provider, network, env read, memory write or Hermes dispatch occurred.",
            ],
            uncertainty=_uncertainty_for(classification, intake),
            audit_summary={
                **analysis.audit_summary,
                "brain_provider": self.name,
                "provider_mode": self.mode,
                "external_provider_called": False,
                "hermes_dispatch_allowed": False,
                "approval_is_not_execution": True,
                "no_raw_audio": True,
                "no_camera_frames": True,
            },
        )


class DisabledExternalLLMProvider:
    name = "disabled_external_llm"
    mode = "external_provider_disabled_by_policy"

    def status(self) -> BrainProviderStatus:
        return BrainProviderStatus(
            provider_name=self.name,
            provider_mode=self.mode,
            available=False,
            api_key_required=True,
            honest_status="disabled_by_default_not_configured_not_called",
            missing_configuration=[
                "external_llm_enabled flag is false",
                "provider selection remains deterministic_local",
                "API key loading is intentionally disabled",
                "network calls are not allowed in this PR",
            ],
        )


class LLMBrainAdapter:
    """Safe brain contract adapter with deterministic local default and disabled external mode."""

    def __init__(
        self,
        *,
        intake_pipeline: Optional[ConversationalIntakePipeline] = None,
        local_provider: Optional[DeterministicLocalBrainProvider] = None,
        disabled_external_provider: Optional[DisabledExternalLLMProvider] = None,
    ) -> None:
        self.intake_pipeline = intake_pipeline or ConversationalIntakePipeline()
        self.local_provider = local_provider or DeterministicLocalBrainProvider()
        self.disabled_external_provider = disabled_external_provider or DisabledExternalLLMProvider()

    def build_request(self, analysis: ConversationalIntakeAnalysis) -> BrainRequest:
        intake = analysis.intake
        classification = analysis.classification
        goal = _safe_goal(intake)
        return BrainRequest(
            request_id=f"brain_request_{intake.intake_id}",
            intake=intake.redacted_for_brain(),
            user_visible_goal=goal,
            context_summary=_context_summary(intake, classification),
            allowed_context=[
                "operator-provided non-sensitive text category",
                "safe dashboard/read-model metadata",
                "deterministic local policy and risk markers",
            ],
            forbidden_context=[
                "credential material",
                "browser session material",
                "raw media payloads",
                "camera or screen frames",
                "private prompt logs",
                "external provider payloads",
            ],
            risk_constraints={
                "risk_level": classification.risk_level,
                "approval_level": classification.approval_level,
                "requires_approval": classification.requires_approval,
                "wake_phrase_never_approves": True,
                "approval_is_not_execution": True,
                "memory_never_grants_permission": True,
            },
            policy_constraints={
                "illegal_unsafe_unauthorized_impossible_or_unsupported": "denied",
                "credential_material": "denied",
                "money_deploy_production_email_identity": "strong_gated",
                "ambiguous_or_low_confidence": "clarify",
                "restrictions_are_approval_gates_not_permanent_bans": True,
            },
            memory_policy={
                "memory_read_allowed": False,
                "memory_write_allowed": False,
                "memory_write_requires_explicit_review": True,
                "memory_never_grants_permission": True,
            },
            hermes_dispatch_policy={
                "dispatch_allowed": False,
                "safe_to_dispatch_to_hermes": False,
                "requires_future_governed_preview_approval_audit": True,
            },
            external_provider_policy={
                "default_provider": DEFAULT_BRAIN_PROVIDER,
                "external_llm_enabled": False,
                "external_provider_called": False,
                "reads_env": False,
                "network_allowed": False,
            },
            max_cost_budget="not_configured",
        )

    def respond(self, request: BrainRequest, *, analysis: ConversationalIntakeAnalysis) -> BrainResponse:
        return self.local_provider.respond(request, analysis=analysis)

    def process(
        self,
        raw_text: str,
        *,
        source: str = "typed_text",
        operator: str = "David",
        session_id: Optional[str] = None,
        voice_session_state: str = "idle",
        transcript_confidence: float = 1.0,
    ) -> Dict[str, Any]:
        analysis = self.intake_pipeline.process(
            raw_text,
            source=source,
            operator=operator,
            session_id=session_id,
            voice_session_state=voice_session_state,
            transcript_confidence=transcript_confidence,
        )
        request = self.build_request(analysis)
        response = self.respond(request, analysis=analysis)
        return {
            "analysis": analysis.to_dict(),
            "brain_request": request.to_dict(),
            "brain_response": response.to_dict(),
            "provider_status": self.local_provider.status().to_dict(),
            "disabled_external_provider_status": self.disabled_external_provider.status().to_dict(),
            "preview_only": True,
            "read_only": True,
        }

    def status(self) -> Dict[str, Any]:
        sample = self.process("JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro.")
        return {
            "schema_version": BRAIN_ADAPTER_SCHEMA_VERSION,
            "state": {
                "mode": "safe_brain_adapter_prepare_only",
                "default_provider": DEFAULT_BRAIN_PROVIDER,
                "current_provider": DEFAULT_BRAIN_PROVIDER,
                "external_llm_enabled": False,
                "external_provider_called": False,
                "api_key_required": False,
                "api_key_loaded": False,
                "reads_env": False,
                "network_allowed": False,
                "hermes_dispatch_allowed": False,
                "memory_autosave_enabled": False,
                "prompt_persistence_enabled": False,
                "max_cost_budget": "not_configured",
                "preview_only": True,
                "read_only": True,
            },
            "providers": {
                DEFAULT_BRAIN_PROVIDER: self.local_provider.status().to_dict(),
                "disabled_external_llm": self.disabled_external_provider.status().to_dict(),
            },
            "sample": sample,
            "contracts": {
                "brain_request_schema_version": BRAIN_REQUEST_SCHEMA_VERSION,
                "brain_response_schema_version": BRAIN_RESPONSE_SCHEMA_VERSION,
                "provider_status_schema_version": BRAIN_PROVIDER_STATUS_SCHEMA_VERSION,
                "brain_request_contains_no_secret_material": True,
                "brain_request_contains_no_raw_audio": True,
                "brain_request_contains_no_camera_frames": True,
                "brain_response_external_provider_called_default": False,
                "brain_response_hermes_dispatch_allowed_default": False,
            },
            "safety": {
                "no_external_llm_by_default": True,
                "no_external_api": True,
                "no_env_read": True,
                "no_api_key_load": True,
                "no_network": True,
                "no_prompt_persistence": True,
                "no_private_text_export": True,
                "no_raw_audio": True,
                "no_camera_frames": True,
                "no_memory_autosave": True,
                "no_hermes_dispatch": True,
                "does_not_claim_real_llm": True,
            },
            "source_endpoint": "/mark-3/brain-adapter/status",
            "preview_only": True,
            "read_only": True,
        }


def _safe_goal(intake: ConversationalIntake) -> str:
    if intake.contains_sensitive_request:
        return "[redacted sensitive conversational goal]"
    return intake.remaining_command or intake.normalized_text


def _context_summary(intake: ConversationalIntake, classification: ConversationalClassification) -> str:
    if intake.contains_sensitive_request:
        return "Sensitive credential/session material was requested; content redacted before brain processing."
    return (
        f"Source={intake.source}; language={intake.language}; "
        f"intent={classification.intent_detected}; risk={classification.risk_level}; "
        "Hermes dispatch disabled."
    )


def _human_response_for(classification: ConversationalClassification, bridge_result: Dict[str, Any]) -> str:
    if classification.intent_detected == "low_confidence_needs_clarification":
        return "No tengo suficiente confianza en la transcripción. Repite la petición antes de preparar nada."
    if classification.intent_detected == "denied_secret_or_credential_access":
        return "No puedo leer ni usar credenciales, secretos o material de sesión. Puedo ayudarte con una revisión segura sin tocarlos."
    if classification.intent_detected == "wake_phrase_approval_or_execution_attempt":
        return "La wake phrase no es permiso. No aprobaré ni ejecutaré por voz; puedo preparar una preview segura si defines el alcance."
    if classification.requires_clarification:
        return "No lo tengo claro todavía. Dame una acción o pregunta concreta y preparo el siguiente paso seguro."
    if classification.requires_approval:
        return "Eso toca una zona sensible. No lo ejecutaré ni lo aprobaré; puedo preparar una preview para revisión con gates."
    return str(bridge_result.get("human_response") or "Puedo responder o preparar una preview segura sin ejecutar nada.")


def _cannot_execute_reason(classification: ConversationalClassification) -> str:
    if classification.denied:
        return "La petición queda bloqueada o denegada por política; no hay ejecución ni aprobación automática."
    if classification.requires_clarification:
        return "La petición necesita aclaración antes de cualquier preview o gate."
    if classification.requires_approval:
        return "Requiere clasificación de riesgo, approval válido, auditoría y rollback/stop plan antes de cualquier ejecución futura."
    return "Esta PR solo prepara intake/preview/brain response; Hermes dispatch sigue deshabilitado."


def _clarification_question(classification: ConversationalClassification, intake: ConversationalIntake) -> Optional[str]:
    if classification.intent_detected == "low_confidence_needs_clarification":
        return "¿Puedes repetirlo con una frase corta y clara?"
    if classification.requires_clarification:
        if intake.wake_phrase_detected:
            return "He detectado la wake phrase. ¿Qué tarea o pregunta concreta quieres preparar?"
        return "¿Qué objetivo concreto quieres que JARVIS prepare en modo preview?"
    return None


def _hermes_candidate_for(preview: Optional[Dict[str, Any]], classification: ConversationalClassification) -> Optional[Dict[str, Any]]:
    if preview is None:
        return None
    return {
        "candidate_id": f"hermes_candidate_{preview['preview_id']}",
        "intent_detected": classification.intent_detected,
        "risk_level": classification.risk_level,
        "approval_level": classification.approval_level,
        "requires_approval": classification.requires_approval,
        "dispatch_allowed": False,
        "would_execute": False,
        "eligible_after_valid_approval": False,
        "disabled_reason": "Hermes dispatch is disabled until a future governed preview/approval/audit flow.",
        "preview_only": True,
    }


def _uncertainty_for(classification: ConversationalClassification, intake: ConversationalIntake) -> List[str]:
    uncertainty: List[str] = []
    if classification.requires_clarification:
        uncertainty.append("operator intent needs clarification")
    if intake.source in {"voice_transcript", "wake_phrase_command"} and intake.transcript_confidence < 1.0:
        uncertainty.append("transcript confidence is browser/provider supplied and must be treated conservatively")
    if classification.requires_approval:
        uncertainty.append("approval gate and exact execution scope are not satisfied in this PR")
    if not uncertainty:
        uncertainty.append("external facts, cost and execution feasibility are not measured by this adapter")
    return uncertainty
