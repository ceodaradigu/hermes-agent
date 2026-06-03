from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from jarvis.command_center import build_command_center_view_model
from jarvis.mission_control import MissionControl
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter
from jarvis.voice.base import VoiceAdapter, VoiceSynthesisRequest
from jarvis.voice.feedback_preview import preview_user_understanding_feedback
from jarvis.voice.factory import create_voice_adapter_from_env
from jarvis.voice.gpt_sovits_adapter import GPTSoVITSAdapter
from jarvis.voice.mock_adapter import MockVoiceAdapter
from jarvis.voice.runtime import VoiceRuntime, VoiceRuntimeState
from jarvis.voice.storage import VoiceAudioStorage
from jarvis.voice.understanding_feedback import UserUnderstandingAppliedFeedbackRule, UserUnderstandingFeedback


class CreateTaskRequest(BaseModel):
    prompt: str


class CreateMissionStepRequest(BaseModel):
    prompt: str


class CancelTaskResponse(BaseModel):
    task_id: str
    status: str


class VoiceTTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    language: str = "es"
    output_format: str = "wav"
    metadata: Optional[dict] = None
    save_audio: bool = False


class VoiceTTSResponse(BaseModel):
    provider: str
    content_type: str
    audio_path: Optional[str] = None
    has_audio_bytes: bool
    duration_seconds: Optional[float] = None
    metadata: dict
    status: Optional[str] = None
    approval_request_id: Optional[str] = None


class VoiceRuntimeModeRequest(BaseModel):
    mode: str


class VoiceRuntimeTextRequest(BaseModel):
    text: str


class VoiceRuntimeFeedbackRequest(BaseModel):
    original_text: str
    interpreted_intent: Optional[str] = None
    corrected_intent: str
    correction_note: Optional[str] = None
    preferred_next_step: Optional[str] = None
    confidence_before: Optional[str] = None


class VoiceRuntimeFeedbackPreviewRequest(BaseModel):
    original_text: Optional[str] = None
    interpreted_intent: Optional[str] = None
    corrected_intent: Optional[str] = None
    correction_note: Optional[str] = None
    preferred_next_step: Optional[str] = None
    confidence_before: Optional[str] = None


class VoiceRuntimeMemoryProposalFromAppliedFeedbackRequest(BaseModel):
    original_text: str
    corrected_intent: str
    suggested_alias: Optional[str] = None
    reason: Optional[str] = None
    source: str = "user_reviewed_feedback"
    applied_persistently: bool = False


class VoiceRuntimeMemoryProposalApproveRequest(BaseModel):
    approved_by: Optional[str] = "David"


class VoiceRuntimeMemoryProposalDisableRequest(BaseModel):
    reason: Optional[str] = None


class VoiceRuntimeMemoryProposalActivateRequest(BaseModel):
    activated_by: Optional[str] = "David"


class VoiceRuntimeMemoryRuleDeactivateRequest(BaseModel):
    reason: Optional[str] = None


class VoiceRuntimeMemorySnapshotImportRequest(BaseModel):
    snapshot: Optional[Any] = None
    replace: bool = False
    path: Optional[Any] = None
    file: Optional[Any] = None


class VoiceRuntimeMemoryLocalSaveRequest(BaseModel):
    base_dir: Optional[str] = None
    create_backup: bool = True


class VoiceRuntimeMemoryLocalLoadRequest(BaseModel):
    base_dir: Optional[str] = None
    replace: Optional[Any] = None
    path: Optional[Any] = None
    file: Optional[Any] = None


class VoiceRuntimeMemoryLocalBackupRequest(BaseModel):
    base_dir: Optional[str] = None
    path: Optional[Any] = None
    file: Optional[Any] = None


class VoiceRuntimeMemoryLocalDeleteRequest(BaseModel):
    base_dir: Optional[str] = None
    include_backups: Optional[Any] = True
    path: Optional[Any] = None
    file: Optional[Any] = None


@dataclass
class TaskRecord:
    task_id: str
    prompt: str
    status: str
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approval_request_id: Optional[str] = None


class InMemoryTaskStore:
    def __init__(self):
        self._items: Dict[str, TaskRecord] = {}
        self._lock = Lock()

    def create(self, prompt: str) -> TaskRecord:
        now = _now_iso()
        task = TaskRecord(task_id=str(uuid4()), prompt=prompt, status="pending", created_at=now, updated_at=now)
        with self._lock:
            self._items[task.task_id] = task
        return task

    def get(self, task_id: str) -> TaskRecord:
        with self._lock:
            item = self._items.get(task_id)
        if not item:
            raise KeyError(task_id)
        return item

    def list(self) -> List[TaskRecord]:
        with self._lock:
            return list(self._items.values())

    def update(self, task: TaskRecord) -> TaskRecord:
        task.updated_at = _now_iso()
        with self._lock:
            self._items[task.task_id] = task
        return task


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_voice_metadata(metadata: dict) -> dict:
    blocked_exact = {"base_url", "prompt_text"}
    blocked_substrings = ("secret", "token", "key", "password")
    sanitized = {}

    for key, value in metadata.items():
        key_text = str(key)
        key_lower = key_text.lower()
        if key_lower in blocked_exact:
            continue
        if key_lower.endswith("_path"):
            continue
        if any(blocked in key_lower for blocked in blocked_substrings):
            continue
        sanitized[key] = value

    return sanitized


def _voice_runtime_state_payload(state: VoiceRuntimeState) -> dict:
    return {
        "mode": state.mode.value,
        "enabled": state.enabled,
        "frontend_required": state.frontend_required,
        "input_language": state.input_language,
        "output_language": state.output_language,
        "last_error": state.last_error,
        "last_transcript": state.last_transcript,
        "last_intent": state.last_intent,
        "wake_words": list(state.wake_words),
        "feedback_count": state.feedback_count,
        "applied_feedback_count": state.applied_feedback_count,
        "memory_proposal_count": state.memory_proposal_count,
        "active_memory_rule_count": state.active_memory_rule_count,
    }


def create_app(
    *,
    policy_engine: Optional[PolicyEngine] = None,
    approval_gateway: Optional[ApprovalGateway] = None,
    adapter_factory: Optional[Callable[[], HermesRuntimeAdapter]] = None,
    task_store: Optional[InMemoryTaskStore] = None,
    voice_adapter: Optional[VoiceAdapter] = None,
    voice_audio_storage: Optional[VoiceAudioStorage] = None,
    voice_runtime: Optional[VoiceRuntime] = None,
) -> FastAPI:
    app = FastAPI(title="JARVIS Gateway API", version="0.1.0")

    app.state.policy_engine = policy_engine or PolicyEngine()
    app.state.approval_gateway = approval_gateway or ApprovalGateway()
    app.state.adapter_factory = adapter_factory or (lambda: HermesRuntimeAdapter())
    app.state.voice_adapter = voice_adapter or create_voice_adapter_from_env()
    app.state.voice_runtime = voice_runtime or VoiceRuntime()
    app.state.task_store = task_store or InMemoryTaskStore()
    app.state.voice_audio_storage = voice_audio_storage or VoiceAudioStorage()
    app.state.mission_control = MissionControl(
        mission_store=None,
        policy_engine=app.state.policy_engine,
        approval_gateway=app.state.approval_gateway,
        adapter_factory=app.state.adapter_factory,
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/command-center")
    def command_center() -> dict:
        view = build_command_center_view_model(
            view_id=f"command-center-{uuid4()}",
            generated_at=_now_iso(),
            metadata={
                "phase": "D.1",
                "source": "empty_placeholder_snapshot",
                "store_connected": False,
            },
        )
        return view.to_dict()

    @app.post("/missions")
    def create_mission() -> dict:
        mission = app.state.mission_control.create_mission()
        return asdict(mission)

    @app.get("/missions")
    def list_missions() -> list[dict]:
        return [asdict(m) for m in app.state.mission_control.list_missions()]

    @app.get("/missions/{mission_id}")
    def get_mission(mission_id: str) -> dict:
        try:
            mission = app.state.mission_control.get_mission(mission_id)
            steps = app.state.mission_control.store.list_steps(mission_id)
            return {**asdict(mission), "steps": [asdict(s) for s in steps]}
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/missions/{mission_id}/steps")
    def add_mission_step(mission_id: str, payload: CreateMissionStepRequest) -> dict:
        prompt = payload.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt must be non-empty")
        try:
            step = app.state.mission_control.add_step(mission_id, prompt)
            mission = app.state.mission_control.get_mission(mission_id)
            return {"mission": asdict(mission), "step": asdict(step)}
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/missions/{mission_id}/cancel")
    def cancel_mission(mission_id: str) -> dict:
        try:
            mission = app.state.mission_control.cancel_mission(mission_id)
            return asdict(mission)
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/tasks")
    def create_task(payload: CreateTaskRequest) -> dict:
        prompt = payload.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt must be non-empty")

        task = app.state.task_store.create(prompt=prompt)
        decision = app.state.policy_engine.classify_action(prompt)

        if decision.decision == PolicyDecision.DENIED:
            task.status = "failed"
            task.error = f"denied: {decision.reason}"
            app.state.task_store.update(task)
            return asdict(task)

        if decision.decision == PolicyDecision.REQUIRES_APPROVAL:
            approval = app.state.approval_gateway.create_request(
                action=prompt,
                rationale="Prompt requires human approval before execution.",
            )
            task.status = "pending_approval"
            task.error = "requires_approval"
            task.approval_request_id = approval.request_id
            app.state.task_store.update(task)
            return asdict(task)

        task.status = "running"
        app.state.task_store.update(task)

        try:
            adapter = app.state.adapter_factory()
            result = adapter.run(prompt, task_id=task.task_id)
            task.status = "completed"
            task.result = result
            task.error = None
        except Exception as exc:
            task.status = "failed"
            task.error = f"execution_error: {type(exc).__name__}: {exc}"

        app.state.task_store.update(task)
        return asdict(task)

    @app.get("/tasks/{task_id}")
    def get_task(task_id: str) -> dict:
        try:
            task = app.state.task_store.get(task_id)
            return asdict(task)
        except KeyError:
            raise HTTPException(status_code=404, detail="task not found")

    @app.get("/tasks")
    def list_tasks() -> list[dict]:
        return [asdict(task) for task in app.state.task_store.list()]

    @app.post("/voice/tts", response_model=VoiceTTSResponse)
    def voice_tts(payload: VoiceTTSRequest) -> VoiceTTSResponse:
        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="text must be non-empty")
        if not payload.language or not payload.language.strip():
            raise HTTPException(status_code=400, detail="language must be non-empty")

        decision = app.state.policy_engine.classify_action(text)
        if decision.decision == PolicyDecision.DENIED:
            raise HTTPException(status_code=403, detail=f"voice_tts denied: {decision.reason}")
        if decision.decision == PolicyDecision.REQUIRES_APPROVAL:
            approval = app.state.approval_gateway.create_request(
                action=text,
                rationale="Voice TTS request requires human approval before synthesis.",
            )
            return VoiceTTSResponse(
                provider="mock",
                content_type="application/json",
                has_audio_bytes=False,
                metadata={"policy_reason": decision.reason},
                status="pending_approval",
                approval_request_id=approval.request_id,
            )

        try:
            request = VoiceSynthesisRequest(
                text=text,
                voice_id=payload.voice_id,
                language=payload.language.strip(),
                output_format=payload.output_format,
                metadata=payload.metadata or {},
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        try:
            result = app.state.voice_adapter.synthesize(request)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception:
            raise HTTPException(status_code=502, detail="voice synthesis failed")

        audio_path = str(result.audio_path) if result.audio_path else None
        if payload.save_audio and result.audio_bytes is not None:
            audio_path = app.state.voice_audio_storage.save_audio(result.audio_bytes, request.output_format)

        return VoiceTTSResponse(
            provider=result.provider,
            content_type=result.content_type,
            audio_path=audio_path,
            has_audio_bytes=result.audio_bytes is not None,
            duration_seconds=result.duration_seconds,
            metadata=_sanitize_voice_metadata(result.metadata),
        )

    @app.get("/voice/status")
    def voice_status() -> dict:
        adapter = app.state.voice_adapter

        if isinstance(adapter, MockVoiceAdapter):
            return {
                "provider": "mock",
                "configured": True,
                "can_synthesize": True,
                "details": {},
            }

        if isinstance(adapter, GPTSoVITSAdapter):
            has_base_url = bool(adapter.base_url and adapter.base_url.strip())
            has_ref_audio_path = bool(adapter.ref_audio_path and str(adapter.ref_audio_path).strip())
            has_prompt_text = bool(adapter.prompt_text and str(adapter.prompt_text).strip())
            return {
                "provider": "gpt-sovits",
                "configured": has_base_url,
                "can_synthesize": has_base_url and has_ref_audio_path,
                "details": {
                    "base_url": adapter.base_url,
                    "has_ref_audio_path": has_ref_audio_path,
                    "has_prompt_text": has_prompt_text,
                    "prompt_lang": adapter.prompt_lang,
                    "timeout_seconds": adapter.timeout_seconds,
                },
            }

        return {
            "provider": "unknown",
            "configured": False,
            "can_synthesize": False,
            "details": {"class_name": adapter.__class__.__name__},
        }

    @app.get("/voice/runtime/status")
    def voice_runtime_status() -> dict:
        return _voice_runtime_state_payload(app.state.voice_runtime.status())

    @app.post("/voice/runtime/start")
    def voice_runtime_start() -> dict:
        return _voice_runtime_state_payload(app.state.voice_runtime.start())

    @app.post("/voice/runtime/stop")
    def voice_runtime_stop() -> dict:
        return _voice_runtime_state_payload(app.state.voice_runtime.stop())

    @app.post("/voice/runtime/mode")
    def voice_runtime_set_mode(payload: VoiceRuntimeModeRequest) -> dict:
        try:
            state = app.state.voice_runtime.set_mode(payload.mode)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return _voice_runtime_state_payload(state)

    @app.post("/voice/runtime/control")
    def voice_runtime_control(payload: VoiceRuntimeTextRequest) -> dict:
        result = app.state.voice_runtime.handle_control_phrase(payload.text)
        return {
            "recognized": result["handled"],
            "result": result,
            "state": _voice_runtime_state_payload(app.state.voice_runtime.status()),
        }

    @app.post("/voice/runtime/transcript")
    def voice_runtime_transcript(payload: VoiceRuntimeTextRequest) -> dict:
        result = app.state.voice_runtime.handle_transcript(payload.text)
        return {
            "result": result,
            "state": _voice_runtime_state_payload(app.state.voice_runtime.status()),
        }

    @app.get("/voice/runtime/feedback")
    def voice_runtime_feedback_list() -> dict:
        feedback = [item.to_dict() for item in app.state.voice_runtime.list_feedback()]
        return {
            "feedback": feedback,
            "feedback_count": len(feedback),
        }

    @app.post("/voice/runtime/feedback")
    def voice_runtime_feedback_add(payload: VoiceRuntimeFeedbackRequest) -> dict:
        original_text = payload.original_text.strip()
        corrected_intent = payload.corrected_intent.strip()
        if not original_text:
            raise HTTPException(status_code=400, detail="original_text must be non-empty")
        if not corrected_intent:
            raise HTTPException(status_code=400, detail="corrected_intent must be non-empty")

        feedback = app.state.voice_runtime.add_feedback(
            original_text=original_text,
            interpreted_intent=payload.interpreted_intent,
            corrected_intent=corrected_intent,
            correction_note=payload.correction_note,
            preferred_next_step=payload.preferred_next_step,
            confidence_before=payload.confidence_before,
        )
        return {
            "feedback": feedback.to_dict(),
            "feedback_count": app.state.voice_runtime.status().feedback_count,
            "applied_persistently": feedback.applied_persistently,
        }

    @app.post("/voice/runtime/feedback/preview")
    def voice_runtime_feedback_preview(payload: VoiceRuntimeFeedbackPreviewRequest) -> dict:
        original_text = (payload.original_text or "").strip()
        corrected_intent = (payload.corrected_intent or "").strip()
        if not original_text:
            raise HTTPException(status_code=400, detail="original_text must be non-empty")
        if not corrected_intent:
            raise HTTPException(status_code=400, detail="corrected_intent must be non-empty")

        feedback = UserUnderstandingFeedback(
            original_text=original_text,
            interpreted_intent=payload.interpreted_intent,
            corrected_intent=corrected_intent,
            correction_note=payload.correction_note,
            preferred_next_step=payload.preferred_next_step,
            confidence_before=payload.confidence_before,
            applied_persistently=False,
            requires_review=True,
        )
        preview = preview_user_understanding_feedback(feedback).to_dict()
        return {
            "preview": preview,
            "applied": preview["applied"],
            "requires_review": preview["requires_review"],
            "feedback_count": app.state.voice_runtime.status().feedback_count,
        }

    @app.post("/voice/runtime/feedback/apply-reviewed")
    def voice_runtime_feedback_apply_reviewed(payload: VoiceRuntimeFeedbackRequest) -> dict:
        original_text = payload.original_text.strip()
        corrected_intent = payload.corrected_intent.strip()
        if not original_text:
            raise HTTPException(status_code=400, detail="original_text must be non-empty")
        if not corrected_intent:
            raise HTTPException(status_code=400, detail="corrected_intent must be non-empty")

        rule = app.state.voice_runtime.apply_reviewed_feedback(
            original_text=original_text,
            interpreted_intent=payload.interpreted_intent,
            corrected_intent=corrected_intent,
            correction_note=payload.correction_note,
            preferred_next_step=payload.preferred_next_step,
            confidence_before=payload.confidence_before,
        )
        return {
            "applied_rule": rule.to_dict(),
            "applied_feedback_count": app.state.voice_runtime.status().applied_feedback_count,
            "applied_persistently": False,
        }

    @app.get("/voice/runtime/feedback/applied")
    def voice_runtime_feedback_applied_list() -> dict:
        rules = [rule.to_dict() for rule in app.state.voice_runtime.list_applied_feedback()]
        return {
            "applied_rules": rules,
            "applied_feedback_count": len(rules),
            "applied_persistently": False,
        }

    @app.delete("/voice/runtime/feedback/applied")
    def voice_runtime_feedback_applied_clear() -> dict:
        app.state.voice_runtime.clear_applied_feedback()
        return {
            "applied_feedback_count": app.state.voice_runtime.status().applied_feedback_count,
            "applied_persistently": False,
        }

    @app.delete("/voice/runtime/feedback")
    def voice_runtime_feedback_clear() -> dict:
        app.state.voice_runtime.clear_feedback()
        return {"feedback_count": app.state.voice_runtime.status().feedback_count}

    @app.get("/voice/runtime/memory/proposals")
    def voice_runtime_memory_proposals_list() -> dict:
        proposals = [proposal.to_dict() for proposal in app.state.voice_runtime.list_memory_proposals()]
        return {
            "proposals": proposals,
            "memory_proposal_count": len(proposals),
        }

    @app.post("/voice/runtime/memory/proposals/from-applied-feedback")
    def voice_runtime_memory_proposal_from_applied_feedback(
        payload: VoiceRuntimeMemoryProposalFromAppliedFeedbackRequest,
    ) -> dict:
        original_text = payload.original_text.strip()
        corrected_intent = payload.corrected_intent.strip()
        if not original_text:
            raise HTTPException(status_code=400, detail="original_text must be non-empty")
        if not corrected_intent:
            raise HTTPException(status_code=400, detail="corrected_intent must be non-empty")

        rule = UserUnderstandingAppliedFeedbackRule(
            original_text=original_text,
            corrected_intent=corrected_intent,
            suggested_alias=(payload.suggested_alias or "").strip() or None,
            reason=(payload.reason or "").strip(),
            source=(payload.source or "user_reviewed_feedback").strip() or "user_reviewed_feedback",
            applied_persistently=payload.applied_persistently,
            requires_review=False,
            approval_required=False,
        )
        proposal = app.state.voice_runtime.propose_memory_from_applied_feedback(rule)
        return {
            "proposal": proposal.to_dict(),
            "memory_proposal_count": app.state.voice_runtime.status().memory_proposal_count,
            "applied_persistently": False,
        }

    @app.delete("/voice/runtime/memory/proposals")
    def voice_runtime_memory_proposals_clear() -> dict:
        app.state.voice_runtime.clear_memory_proposals()
        return {
            "memory_proposal_count": app.state.voice_runtime.status().memory_proposal_count,
        }

    @app.get("/voice/runtime/memory/active")
    def voice_runtime_memory_active_list() -> dict:
        active_rules = [
            rule.to_dict()
            for rule in app.state.voice_runtime.list_active_memory_rules()
        ]
        return {
            "active_rules": active_rules,
            "active_memory_rule_count": len(active_rules),
            "applied_to_runtime": True,
        }

    @app.delete("/voice/runtime/memory/active")
    def voice_runtime_memory_active_clear() -> dict:
        app.state.voice_runtime.clear_active_memory_rules()
        return {
            "active_memory_rule_count": app.state.voice_runtime.status().active_memory_rule_count,
            "applied_to_runtime": True,
        }

    @app.get("/voice/runtime/memory/snapshot")
    def voice_runtime_memory_snapshot() -> dict:
        return {
            "snapshot": app.state.voice_runtime.export_memory_snapshot().to_dict(),
            "persisted": False,
        }

    @app.post("/voice/runtime/memory/snapshot/import")
    def voice_runtime_memory_snapshot_import(
        payload: VoiceRuntimeMemorySnapshotImportRequest,
    ) -> dict:
        if payload.path is not None or payload.file is not None:
            raise HTTPException(status_code=400, detail="path/file inputs are not accepted")
        if payload.snapshot is None:
            raise HTTPException(status_code=400, detail="snapshot is required")

        try:
            imported_count = app.state.voice_runtime.import_memory_snapshot(
                payload.snapshot,
                replace=payload.replace,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "imported_count": imported_count,
            "memory_proposal_count": app.state.voice_runtime.status().memory_proposal_count,
            "persisted": False,
            "applied_to_runtime": False,
        }

    @app.post("/voice/runtime/memory/local/save")
    def voice_runtime_memory_local_save(
        payload: Optional[VoiceRuntimeMemoryLocalSaveRequest] = None,
    ) -> dict:
        base_dir = payload.base_dir if payload else None
        create_backup = payload.create_backup if payload else True
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.save_memory_snapshot_local(
                base_dir=base_dir,
                create_backup=create_backup,
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "persisted": True,
            "applied_to_runtime": False,
        }

    @app.post("/voice/runtime/memory/local/load")
    def voice_runtime_memory_local_load(
        payload: Optional[VoiceRuntimeMemoryLocalLoadRequest] = None,
    ) -> dict:
        if payload and (payload.path is not None or payload.file is not None):
            raise HTTPException(status_code=400, detail="path/file inputs are not accepted")
        base_dir = payload.base_dir if payload else None
        replace = True if payload is None or payload.replace is None else payload.replace
        if not isinstance(replace, bool):
            raise HTTPException(status_code=400, detail="replace must be boolean")
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.load_memory_snapshot_local(
                base_dir=base_dir,
                replace=replace,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "persisted_source": result["persisted_source"],
            "applied_to_runtime": False,
        }

    @app.get("/voice/runtime/memory/local/status")
    def voice_runtime_memory_local_status(base_dir: Optional[str] = None) -> dict:
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.get_memory_local_status(base_dir=base_dir)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "applied_to_runtime": False,
        }

    @app.post("/voice/runtime/memory/local/backup")
    def voice_runtime_memory_local_backup(
        payload: Optional[VoiceRuntimeMemoryLocalBackupRequest] = None,
    ) -> dict:
        if payload and (payload.path is not None or payload.file is not None):
            raise HTTPException(status_code=400, detail="path/file inputs are not accepted")
        base_dir = payload.base_dir if payload else None
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.backup_memory_snapshot_local(base_dir=base_dir)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "applied_to_runtime": False,
        }

    @app.delete("/voice/runtime/memory/local")
    def voice_runtime_memory_local_delete(
        payload: Optional[VoiceRuntimeMemoryLocalDeleteRequest] = None,
    ) -> dict:
        if payload and (payload.path is not None or payload.file is not None):
            raise HTTPException(status_code=400, detail="path/file inputs are not accepted")
        base_dir = payload.base_dir if payload else None
        include_backups = True if payload is None or payload.include_backups is None else payload.include_backups
        if not isinstance(include_backups, bool):
            raise HTTPException(status_code=400, detail="include_backups must be boolean")
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.delete_memory_local(
                base_dir=base_dir,
                include_backups=include_backups,
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "applied_to_runtime": False,
        }

    @app.get("/voice/runtime/memory/proposals/{proposal_id}")
    def voice_runtime_memory_proposal_get(proposal_id: str) -> dict:
        try:
            proposal = app.state.voice_runtime.get_memory_proposal(proposal_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        return {"proposal": proposal.to_dict()}

    @app.post("/voice/runtime/memory/proposals/{proposal_id}/review")
    def voice_runtime_memory_proposal_review(proposal_id: str) -> dict:
        try:
            proposal = app.state.voice_runtime.review_memory_proposal(proposal_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        return {"proposal": proposal.to_dict()}

    @app.post("/voice/runtime/memory/proposals/{proposal_id}/approve")
    def voice_runtime_memory_proposal_approve(
        proposal_id: str,
        payload: Optional[VoiceRuntimeMemoryProposalApproveRequest] = None,
    ) -> dict:
        try:
            proposal = app.state.voice_runtime.approve_memory_proposal(
                proposal_id,
                approved_by=(payload.approved_by or "David") if payload else "David",
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"proposal": proposal.to_dict()}

    @app.post("/voice/runtime/memory/proposals/{proposal_id}/activate")
    def voice_runtime_memory_proposal_activate(
        proposal_id: str,
        payload: Optional[VoiceRuntimeMemoryProposalActivateRequest] = None,
    ) -> dict:
        try:
            rule = app.state.voice_runtime.activate_memory_proposal(
                proposal_id,
                activated_by=(payload.activated_by or "David") if payload else "David",
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {
            "active_rule": rule.to_dict(),
            "active_memory_rule_count": app.state.voice_runtime.status().active_memory_rule_count,
            "applied_to_runtime": True,
            "persisted": False,
        }

    @app.post("/voice/runtime/memory/active/{proposal_id}/deactivate")
    def voice_runtime_memory_active_deactivate(
        proposal_id: str,
        payload: Optional[VoiceRuntimeMemoryRuleDeactivateRequest] = None,
    ) -> dict:
        try:
            rule = app.state.voice_runtime.deactivate_memory_rule(
                proposal_id,
                reason=(payload.reason or "") if payload else "",
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="active memory rule not found")
        return {
            "active_rule": rule.to_dict(),
            "active_memory_rule_count": app.state.voice_runtime.status().active_memory_rule_count,
            "applied_to_runtime": True,
            "persisted": False,
        }

    @app.post("/voice/runtime/memory/proposals/{proposal_id}/disable")
    def voice_runtime_memory_proposal_disable(
        proposal_id: str,
        payload: Optional[VoiceRuntimeMemoryProposalDisableRequest] = None,
    ) -> dict:
        try:
            proposal = app.state.voice_runtime.disable_memory_proposal(
                proposal_id,
                reason=(payload.reason or "") if payload else "",
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        return {"proposal": proposal.to_dict()}

    @app.delete("/voice/runtime/memory/proposals/{proposal_id}")
    def voice_runtime_memory_proposal_delete(proposal_id: str) -> dict:
        try:
            proposal = app.state.voice_runtime.delete_memory_proposal(proposal_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        return {"proposal": proposal.to_dict()}

    @app.post("/tasks/{task_id}/cancel", response_model=CancelTaskResponse)
    def cancel_task(task_id: str) -> CancelTaskResponse:
        try:
            task = app.state.task_store.get(task_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="task not found")

        if task.status in {"completed", "failed", "cancelled"}:
            return CancelTaskResponse(task_id=task.task_id, status=task.status)

        task.status = "cancelled"
        app.state.task_store.update(task)
        return CancelTaskResponse(task_id=task.task_id, status=task.status)

    return app


app = create_app()
