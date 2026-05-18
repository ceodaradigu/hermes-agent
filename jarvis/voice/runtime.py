from dataclasses import dataclass
from enum import Enum
from typing import Any

from jarvis.voice.intent_router import VoiceIntentRouter
from jarvis.voice.understanding_feedback import (
    UserUnderstandingAppliedFeedbackRule,
    UserUnderstandingAppliedFeedbackStore,
    UserUnderstandingFeedback,
    UserUnderstandingFeedbackStore,
)
from jarvis.voice.understanding_memory import (
    UserUnderstandingMemorySnapshot,
    UserUnderstandingMemoryProposal,
    UserUnderstandingMemoryProposalStore,
)
from jarvis.voice.understanding_memory_local_store import (
    UserUnderstandingMemoryLocalLoadResult,
    UserUnderstandingMemoryLocalSaveResult,
    load_user_understanding_memory_snapshot_local,
    save_user_understanding_memory_snapshot_local,
)


class VoiceRuntimeMode(str, Enum):
    OFF = "off"
    WAKE_WORD = "wake_word"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class VoiceRuntimeState:
    mode: VoiceRuntimeMode
    enabled: bool
    frontend_required: bool
    input_language: str
    output_language: str
    last_error: str | None
    last_transcript: str | None
    last_intent: dict[str, Any] | None
    wake_words: tuple[str, ...]
    feedback_count: int = 0
    applied_feedback_count: int = 0
    memory_proposal_count: int = 0


class VoiceRuntime:
    """Control-plane state for future local voice runtime work.

    This class intentionally does not access microphones, wake-word engines,
    STT providers, playback devices, threads, or background services.
    """

    _SLEEP_CONTROL_PHRASES = {
        "jarvis no escuches",
        "jarvis silencio",
        "jarvis duerme",
    }
    _WAKE_CONTROL_PHRASES = {
        "hola jarvis",
        "jarvis",
    }

    def __init__(
        self,
        *,
        enabled: bool = False,
        mode: VoiceRuntimeMode | str = VoiceRuntimeMode.OFF,
        frontend_required: bool = False,
        input_language: str = "es",
        output_language: str = "es",
        wake_words: tuple[str, ...] = ("jarvis", "hola jarvis"),
        intent_router: VoiceIntentRouter | None = None,
        feedback_store: UserUnderstandingFeedbackStore | None = None,
        applied_feedback_store: UserUnderstandingAppliedFeedbackStore | None = None,
        memory_proposal_store: UserUnderstandingMemoryProposalStore | None = None,
    ) -> None:
        self._intent_router = intent_router or VoiceIntentRouter()
        self._feedback_store = feedback_store or UserUnderstandingFeedbackStore()
        self._applied_feedback_store = applied_feedback_store or UserUnderstandingAppliedFeedbackStore()
        self._memory_proposal_store = memory_proposal_store or UserUnderstandingMemoryProposalStore()
        self._state = VoiceRuntimeState(
            mode=self._coerce_mode(mode),
            enabled=enabled,
            frontend_required=frontend_required,
            input_language=input_language,
            output_language=output_language,
            last_error=None,
            last_transcript=None,
            last_intent=None,
            wake_words=wake_words,
            feedback_count=self._feedback_store.count(),
            applied_feedback_count=self._applied_feedback_store.count(),
            memory_proposal_count=self._memory_proposal_store.count(),
        )

    def status(self) -> VoiceRuntimeState:
        return self._state

    def start(self) -> VoiceRuntimeState:
        self._state.enabled = True
        self._state.mode = VoiceRuntimeMode.WAKE_WORD
        self._state.last_error = None
        return self.status()

    def stop(self) -> VoiceRuntimeState:
        self._state.enabled = False
        self._state.mode = VoiceRuntimeMode.OFF
        return self.status()

    def set_mode(self, mode: VoiceRuntimeMode | str) -> VoiceRuntimeState:
        self._state.mode = self._coerce_mode(mode)
        self._state.last_error = None
        return self.status()

    def handle_control_phrase(self, text: str) -> dict[str, Any]:
        normalized = self._normalize_text(text)

        if normalized in self._SLEEP_CONTROL_PHRASES:
            self.set_mode(VoiceRuntimeMode.WAKE_WORD)
            return {"handled": True, "mode": self._state.mode.value, "action": "wake_word_only"}

        if normalized in self._WAKE_CONTROL_PHRASES:
            self.set_mode(VoiceRuntimeMode.LISTENING)
            return {"handled": True, "mode": self._state.mode.value, "action": "listen_briefly"}

        return {"handled": False, "mode": self._state.mode.value, "action": "none"}

    def handle_transcript(self, text: str) -> dict[str, Any]:
        self._state.last_transcript = text
        intent = self._intent_router.classify(text).to_dict()
        if not intent.get("approval_required") and intent.get("status") != "requires_approval":
            rule = self._applied_feedback_store.find_matching_intent(text)
            if rule:
                intent = self._apply_reviewed_feedback_rule(intent, rule)
        self._state.last_intent = intent
        return self._state.last_intent

    def add_feedback(
        self,
        *,
        original_text: str,
        corrected_intent: str,
        interpreted_intent: str | None = None,
        correction_note: str | None = None,
        preferred_next_step: str | None = None,
        confidence_before: str | None = None,
        source: str = "user",
    ) -> UserUnderstandingFeedback:
        feedback = self._feedback_store.add_feedback(
            original_text=original_text,
            interpreted_intent=interpreted_intent,
            corrected_intent=corrected_intent,
            correction_note=correction_note,
            preferred_next_step=preferred_next_step,
            confidence_before=confidence_before,
            source=source,
        )
        self._state.feedback_count = self._feedback_store.count()
        return feedback

    def list_feedback(self) -> list[UserUnderstandingFeedback]:
        return self._feedback_store.list_feedback()

    def clear_feedback(self) -> None:
        self._feedback_store.clear()
        self._state.feedback_count = self._feedback_store.count()

    def apply_reviewed_feedback(
        self,
        *,
        original_text: str,
        corrected_intent: str,
        interpreted_intent: str | None = None,
        correction_note: str | None = None,
        preferred_next_step: str | None = None,
        confidence_before: str | None = None,
    ) -> UserUnderstandingAppliedFeedbackRule:
        feedback = UserUnderstandingFeedback(
            original_text=original_text,
            interpreted_intent=interpreted_intent,
            corrected_intent=corrected_intent,
            correction_note=correction_note,
            preferred_next_step=preferred_next_step,
            confidence_before=confidence_before,
            source="user_reviewed_feedback",
            applied_persistently=False,
            requires_review=False,
        )
        rule = self._applied_feedback_store.apply_feedback(feedback)
        self._state.applied_feedback_count = self._applied_feedback_store.count()
        return rule

    def list_applied_feedback(self) -> list[UserUnderstandingAppliedFeedbackRule]:
        return self._applied_feedback_store.list_rules()

    def clear_applied_feedback(self) -> None:
        self._applied_feedback_store.clear()
        self._state.applied_feedback_count = self._applied_feedback_store.count()

    @property
    def memory_proposal_store(self) -> UserUnderstandingMemoryProposalStore:
        return self._memory_proposal_store

    def propose_memory_from_applied_feedback(
        self,
        rule: UserUnderstandingAppliedFeedbackRule,
    ) -> UserUnderstandingMemoryProposal:
        proposal = self._memory_proposal_store.propose_from_feedback_rule(rule)
        self._state.memory_proposal_count = self._memory_proposal_store.count()
        return proposal

    def list_memory_proposals(self) -> list[UserUnderstandingMemoryProposal]:
        return self._memory_proposal_store.list_proposals()

    def get_memory_proposal(self, proposal_id: str) -> UserUnderstandingMemoryProposal:
        return self._memory_proposal_store.get_proposal(proposal_id)

    def review_memory_proposal(self, proposal_id: str) -> UserUnderstandingMemoryProposal:
        return self._memory_proposal_store.mark_reviewed(proposal_id)

    def approve_memory_proposal(
        self,
        proposal_id: str,
        approved_by: str = "David",
    ) -> UserUnderstandingMemoryProposal:
        return self._memory_proposal_store.approve(proposal_id, approved_by=approved_by)

    def disable_memory_proposal(
        self,
        proposal_id: str,
        reason: str = "",
    ) -> UserUnderstandingMemoryProposal:
        return self._memory_proposal_store.disable(proposal_id, reason=reason)

    def delete_memory_proposal(
        self,
        proposal_id: str,
        reason: str = "",
    ) -> UserUnderstandingMemoryProposal:
        return self._memory_proposal_store.delete(proposal_id, reason=reason)

    def clear_memory_proposals(self) -> None:
        self._memory_proposal_store.clear()
        self._state.memory_proposal_count = self._memory_proposal_store.count()

    def export_memory_snapshot(self) -> UserUnderstandingMemorySnapshot:
        return self._memory_proposal_store.export_snapshot()

    def export_memory_snapshot_json(self) -> str:
        return self._memory_proposal_store.export_snapshot_json()

    def save_memory_snapshot_local(
        self,
        base_dir: str | None = None,
        create_backup: bool = True,
    ) -> dict[str, Any]:
        result: UserUnderstandingMemoryLocalSaveResult = save_user_understanding_memory_snapshot_local(
            self._memory_proposal_store.export_snapshot(),
            base_dir=base_dir,
            create_backup=create_backup,
        )
        return result.to_dict()

    def load_memory_snapshot_local(
        self,
        base_dir: str | None = None,
        replace: bool = True,
    ) -> dict[str, Any]:
        result: UserUnderstandingMemoryLocalLoadResult = load_user_understanding_memory_snapshot_local(
            self._memory_proposal_store,
            base_dir=base_dir,
            replace=replace,
        )
        self._state.memory_proposal_count = self._memory_proposal_store.count()
        return result.to_dict()

    def import_memory_snapshot(
        self,
        snapshot: UserUnderstandingMemorySnapshot | dict[str, Any] | str,
        replace: bool = False,
    ) -> int:
        imported_count = self._memory_proposal_store.import_snapshot(snapshot, replace=replace)
        self._state.memory_proposal_count = self._memory_proposal_store.count()
        return imported_count

    @staticmethod
    def _coerce_mode(mode: VoiceRuntimeMode | str) -> VoiceRuntimeMode:
        if isinstance(mode, VoiceRuntimeMode):
            return mode

        try:
            return VoiceRuntimeMode(mode)
        except ValueError as exc:
            allowed = ", ".join(item.value for item in VoiceRuntimeMode)
            raise ValueError(f"Invalid voice runtime mode '{mode}'. Allowed values: {allowed}") from exc

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.strip().lower().split())

    @staticmethod
    def _apply_reviewed_feedback_rule(
        intent: dict[str, Any],
        rule: UserUnderstandingAppliedFeedbackRule,
    ) -> dict[str, Any]:
        corrected_intent = rule.corrected_intent
        corrected = dict(intent)
        corrected["intent"] = corrected_intent
        corrected["executed"] = False
        corrected["confidence"] = "high"
        corrected["needs_clarification"] = False
        corrected["approval_required"] = corrected_intent == "requires_approval"
        corrected["status"] = "requires_approval" if corrected["approval_required"] else "pending"
        corrected["reason"] = (
            "Applied temporary reviewed feedback rule from David; no persistent learning "
            f"or real execution occurred. {rule.reason}"
        )
        corrected["recommended_next_step"] = (
            "Prepare a non-executing proposal for the corrected intent."
        )
        signals = dict(corrected.get("user_context_signals") or {})
        signals["reviewed_feedback_applied"] = True
        corrected["user_context_signals"] = signals
        slots = dict(corrected.get("slots") or {})
        slots["applied_feedback_rule"] = rule.to_dict()
        corrected["slots"] = slots
        return corrected
