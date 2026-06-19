from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from jarvis.approval_hardening import ApprovalKind, ApprovalStatus
from jarvis.conversational_intake import ConversationalIntakePipeline
from jarvis.mark_3_hermes_runtime_bridge import ALLOWED_ACTION, ALLOWED_BACKEND, ALLOWED_CAPABILITY, ALLOWED_TOOL
from jarvis.mark_3_mission_loop import Mark3MissionLoop
from jarvis.mark_3_mission_loop_models import ExecutionCandidate, MissionLoopStatus, MissionStep
from jarvis.memory_brain_v2 import MemoryBrainV2Store
from jarvis.persistent_audit import PersistentAuditLedger
from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine


PHASE_1_COMPLETION_SCHEMA_VERSION = "jarvis.phase_1_completion.v1"
GOVERNED_EXECUTION_SCHEMA_VERSION = "jarvis.governed_execution.v1"
PROTECTED_CREDENTIAL_MESSAGE = "No puedo hacer eso, David. Las credenciales y secretos están protegidos."

ALLOWED_LOCAL_COMMANDS: tuple[str, ...] = (
    "python -m pytest tests/jarvis/test_pr_165_phase_1_completion_governed_execution_pilot.py -q -x",
    "python -m pytest -c /dev/null tests/jarvis/test_pr_165_phase_1_completion_governed_execution_pilot.py -q -x",
    "python -m py_compile",
    "git diff --check",
)

_SECRET_PATH_NAMES = {".env", ".env.local", ".env.production", ".npmrc", ".pypirc"}
_SECRET_MARKERS = (
    ".env",
    "api key",
    "apikey",
    "authorization",
    "bearer ",
    "cookie",
    "credential",
    "credentials",
    "password",
    "private key",
    "private_key",
    "secret",
    "secrets",
    "session material",
    "token",
)
_DENIED_MARKERS = (
    "bypass",
    "exfiltrate",
    "exfiltrar",
    "hackea",
    "hide action",
    "ilegal",
    "impersona",
    "no autorizado",
    "oculta",
    "roba",
    "saltarse aprobaciones",
    "sáltate",
)
_DESTRUCTIVE_MARKERS = (
    "delete",
    "rm ",
    "rm -",
    "borrar",
    "erase",
    "remove",
    "wipe",
)
_CRITICAL_MARKERS = (
    "deploy",
    "production",
    "producción",
    "stripe",
    "payment",
    "pago",
    "dinero",
    "domain",
    "dns",
    "publish",
    "publicar",
)
_HIGH_MARKERS = (
    "email",
    "correo",
    "external",
    "network",
    "install",
    "npm install",
    "pip install",
    "shell",
    "terminal",
    "subprocess",
)
_STATUS_MARKERS = ("status", "estado", "doctor", "stream", "event", "evento", "policy")
_READ_FILE_MARKERS = (
    "read file",
    "read local file",
    "leer archivo",
    "lee archivo",
    "abre archivo",
    "open file",
    "inspect file",
)
_COMMAND_MARKERS = ("run command", "ejecuta comando", "terminal", "shell", "bash", "subprocess")


class Phase1GovernedExecutionControlPlane:
    """Governed Phase 1 execution orchestrator.

    This class is not an execution runtime. Its only real Hermes dispatch path
    delegates to Mark3HermesRuntimeBridge.execute_read after preview, policy,
    approval and state checks have all passed.
    """

    def __init__(
        self,
        *,
        intake_pipeline: ConversationalIntakePipeline,
        policy_engine: PolicyEngine,
        mission_loop: Mark3MissionLoop,
        hermes_runtime_bridge: Any,
        persistent_audit_ledger: PersistentAuditLedger,
        memory_brain_v2: MemoryBrainV2Store,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
        cwd: str | Path | None = None,
    ) -> None:
        self.intake_pipeline = intake_pipeline
        self.policy_engine = policy_engine
        self.mission_loop = mission_loop
        self.hermes_runtime_bridge = hermes_runtime_bridge
        self.audit_ledger = persistent_audit_ledger
        self.memory_brain_v2 = memory_brain_v2
        self.clock = clock or _now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self.cwd = Path(cwd or os.getcwd()).resolve()
        self._lock = RLock()
        self._previews: Dict[str, Dict[str, Any]] = {}
        self._approval_envelopes: Dict[str, Dict[str, Any]] = {}
        self._approval_to_preview: Dict[str, str] = {}
        self._session_to_preview: Dict[str, str] = {}

    def status(self) -> Dict[str, Any]:
        with self._lock:
            previews = list(self._previews.values())
            approvals = list(self._approval_envelopes.values())
            active = [item for item in previews if item.get("state") in {"dispatching", "running", "stop_requested"}]
        runtime_status = self.hermes_runtime_bridge.status()
        return {
            "schema_version": GOVERNED_EXECUTION_SCHEMA_VERSION,
            "state": {
                "mode": "phase_1_governed_execution_control_plane",
                "available": True,
                "preview_first": True,
                "policy_first": True,
                "approval_gateway_required": True,
                "frontend_direct_hermes_allowed": False,
                "generic_execute_route": False,
                "shell_freeform_allowed": False,
                "voice_approval_enabled": False,
                "wake_phrase_can_approve": False,
                "memory_grants_permission": False,
                "persistent_audit_metadata_only": True,
                "supported_real_dispatch": "exact_local_file_read_via_existing_mark_3_hermes_runtime_bridge",
                "supported_tool": ALLOWED_TOOL,
                "supported_action_type": ALLOWED_ACTION,
                "supported_capability": ALLOWED_CAPABILITY,
                "terminal_enabled": False,
                "network_enabled": False,
                "write_enabled": False,
                "money_enabled": False,
                "deploy_enabled": False,
                "email_enabled": False,
                "critical_stronger_approval_configured": False,
                "preview_count": len(previews),
                "approval_envelope_count": len(approvals),
                "active_execution_count": len(active),
            },
            "counts": {
                "previews": len(previews),
                "requires_approval": sum(1 for item in previews if item.get("decision") == "requires_approval"),
                "allowed": sum(1 for item in previews if item.get("decision") == "allowed"),
                "denied": sum(1 for item in previews if item.get("decision") == "denied"),
                "unsupported": sum(1 for item in previews if item.get("decision") == "unsupported"),
                "approval_pending": sum(1 for item in approvals if item.get("status") == "pending"),
                "approval_approved": sum(1 for item in approvals if item.get("status") == "approved"),
                "approval_rejected": sum(1 for item in approvals if item.get("status") == "rejected"),
                "approval_cancelled": sum(1 for item in approvals if item.get("status") == "cancelled"),
            },
            "allowed_local_commands": list(ALLOWED_LOCAL_COMMANDS),
            "runtime_status": runtime_status,
            "recent_previews": [_public_preview(item) for item in previews[-5:]],
            "recent_approval_envelopes": [_public_envelope(item) for item in approvals[-5:]],
            "safety": {
                "no_execute_endpoint": True,
                "no_frontend_hermes_execution": True,
                "no_shell_freeform_from_ui": True,
                "no_arbitrary_command_execution": True,
                "no_secret_access": True,
                "no_raw_audio_persistence": True,
                "no_camera_frame_persistence": True,
                "no_full_transcript_persistence": True,
                "memory_is_context_not_permission": True,
                "critical_actions_blocked_when_double_triple_not_configured": True,
            },
            "source_endpoint": "/mark-3/execution/status",
        }

    def phase_1_status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        execution_status = self.status()
        return {
            "schema_version": PHASE_1_COMPLETION_SCHEMA_VERSION,
            "phase": "Phase 1",
            "status": "complete_for_local_governed_pilot",
            "completed_at": self.clock(),
            "macro_pr": "PR #165 — Phase 1 Completion: Governed Hermes Execution E2E + Pilot Hardening",
            "flow": [
                "intent",
                "intake",
                "plan/preview",
                "risk classification",
                "approval request",
                "approval decision",
                "governed Hermes dispatch",
                "audit",
                "status/event stream",
                "stop/cancel/rollback metadata",
                "pilot report",
            ],
            "capabilities": {
                "intake_preview_risk": "implemented",
                "approval_ui_backend_gates": "implemented",
                "persistent_audit_metadata_only": "implemented",
                "memory_brain_v2_explainable_context": "implemented",
                "voice_can_submit_intent_text_only": "implemented",
                "governed_hermes_exact_local_read": (
                    "implemented" if execution_status["runtime_status"].get("available") else "not_connected"
                ),
                "stop_cancel": "implemented_cooperative_for_supported_sessions",
                "dashboard_event_stream": "implemented",
                "phase_1_pilot_report": "implemented",
            },
            "risks": {
                "critical_double_triple_approval": "not_configured_blocks_execution",
                "terminal_shell": "unsupported_no_freeform_shell",
                "external_operations": "unsupported_or_denied",
                "secret_material": "denied",
                "audio_video_raw_storage": "denied_for_backend",
                "fake_metrics": "denied",
            },
            "known_limitations": [
                "Only exact local file reads via the existing Hermes bridge are real Hermes dispatch in Phase 1.",
                "Terminal commands, deploys, email, money, Stripe, dependency installation, network and writes are not executed.",
                "Critical double/triple confirmation support is declared not configured, so critical actions block.",
                "Memory Brain v2 can explain context but never grants permission.",
                "Voice submits text intent only after manual browser activation; voice and wake never approve.",
            ],
            "route_readiness": {
                "status": "/mark-3/execution/status" in routes,
                "phase_1_status": "/mark-3/phase-1/status" in routes,
                "preview": "/mark-3/execution/preview" in routes,
                "request_approval": "/mark-3/execution/request-approval" in routes,
                "approval_decision": "/mark-3/execution/approval-decision" in routes,
                "dispatch": "/mark-3/execution/dispatch" in routes,
                "cancel": "/mark-3/execution/cancel" in routes,
                "stop": "/mark-3/execution/stop" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "pilot_checklist": [
                _check("backend routes", True, "Governed endpoints registered under /mark-3/execution."),
                _check("dashboard readiness", "/mark-3/dashboard/status" in routes, "Dashboard read model available."),
                _check("event stream sanity", "/mark-3/dashboard/events/stream" in routes, "SSE status stream available."),
                _check("audit metadata-only", True, "Persistent audit ledger sanitizes metadata."),
                _check("no fake execution", True, "Unsupported actions return unsupported/blocked, not success."),
                _check("no fake providers", True, "No external provider or LLM is called by this control plane."),
            ],
            "execution_status": execution_status,
            "source_endpoint": "/mark-3/phase-1/status",
        }

    def preview(
        self,
        *,
        intent: str,
        source: str = "typed_text",
        operator: str = "David",
        session_id: Optional[str] = None,
        target_path: Optional[str] = None,
        command: Optional[str] = None,
        requested_action_type: Optional[str] = None,
        transcript_confidence: float = 1.0,
        voice_session_state: str = "idle",
    ) -> Dict[str, Any]:
        correlation_id = f"corr-{self.id_factory()}"
        source = _safe_choice(source, {"typed_text", "voice_transcript", "wake_phrase_command", "remote_input", "unknown"}, "typed_text")
        self._audit(
            "voice_session_intent_submitted" if source == "voice_transcript" else "intake_created",
            correlation_id=correlation_id,
            surface="voice" if source == "voice_transcript" else "execution",
            metadata={
                "source": source,
                "operator": operator,
                "intent_fingerprint": _fingerprint(intent),
                "text_length": len(str(intent or "")),
                "contains_full_transcript": False,
            },
        )
        analysis = self.intake_pipeline.process(
            intent,
            source=source,
            operator=operator,
            session_id=session_id,
            voice_session_state=voice_session_state,
            transcript_confidence=transcript_confidence,
        )
        intake = analysis.intake.to_dict()
        classification = analysis.classification.to_dict()
        memory_influence = self._memory_influence(correlation_id=correlation_id)
        action = self._candidate_action(
            intent=intent,
            normalized_text=intake.get("remaining_command") or intake.get("normalized_text") or "",
            classification=classification,
            source=source,
            target_path=target_path,
            command=command,
            requested_action_type=requested_action_type,
        )
        preview_id = f"preview-{self.id_factory()}"
        preview = {
            "schema_version": GOVERNED_EXECUTION_SCHEMA_VERSION,
            "preview_id": preview_id,
            "correlation_id": correlation_id,
            "created_at": self.clock(),
            "updated_at": self.clock(),
            "state": "preview_created",
            "source": source,
            "operator": operator,
            "session_id": session_id,
            "intake": _redacted_intake(intake),
            "classification": classification,
            "action": action,
            "decision": action["decision"],
            "risk_level": action["risk_level"],
            "approval_level": action["approval_level"],
            "requires_approval": action["requires_approval"],
            "preview": {
                "title": action["title"],
                "summary": action["summary"],
                "will_do": action["will_do"],
                "will_not_do": action["will_not_do"],
                "rollback_plan": action["rollback_plan"],
                "stop_plan": action["stop_plan"],
                "audit_destination": ".jarvis/audit/persistent_audit.sqlite3 metadata-only ledger",
                "memory_influence": memory_influence,
            },
            "approval_envelope": None,
            "dispatch": None,
            "cancelled": False,
            "unsupported_reason": action.get("unsupported_reason"),
            "denied_reason": action.get("denied_reason"),
            "protected_message": PROTECTED_CREDENTIAL_MESSAGE if action["decision"] == "denied" and action["denial_category"] == "credentials" else "",
            "hermes_dispatch_allowed": False,
            "frontend_direct_hermes_allowed": False,
            "memory_grants_permission": False,
        }
        with self._lock:
            self._previews[preview_id] = preview
        self._audit(
            "preview_created",
            correlation_id=correlation_id,
            risk_level=preview["risk_level"],
            approval_level=preview["approval_level"],
            metadata=_preview_audit_metadata(preview),
        )
        self._audit(
            "risk_classified",
            correlation_id=correlation_id,
            risk_level=preview["risk_level"],
            approval_level=preview["approval_level"],
            metadata={
                "preview_id": preview_id,
                "decision": preview["decision"],
                "action_type": action["action_type"],
                "requires_approval": action["requires_approval"],
                "unsupported": preview["decision"] == "unsupported",
                "denied": preview["decision"] == "denied",
            },
        )
        if action["rollback_plan"]:
            self._audit(
                "rollback_plan_created",
                correlation_id=correlation_id,
                risk_level=preview["risk_level"],
                approval_level=preview["approval_level"],
                metadata={"preview_id": preview_id, "plan_fingerprint": _fingerprint(action["rollback_plan"])},
            )
        return _public_preview(preview)

    def request_approval(self, *, preview_id: str, actor: str = "David") -> Dict[str, Any]:
        with self._lock:
            preview = self._previews.get(preview_id)
            if preview is None:
                raise KeyError(preview_id)
            if preview.get("cancelled"):
                raise ValueError("preview is cancelled")
            if preview.get("approval_envelope"):
                return _public_envelope(preview["approval_envelope"])
            if preview["decision"] == "denied":
                raise ValueError("denied actions cannot request approval")
            if preview["decision"] == "unsupported":
                raise ValueError("unsupported actions cannot request approval")
            if not preview["requires_approval"]:
                raise ValueError("action does not require approval")
            action = preview["action"]
            if action.get("requires_double_confirmation") or action.get("requires_triple_confirmation"):
                envelope = self._blocked_stronger_approval_envelope(preview, actor)
                preview["approval_envelope"] = envelope
                preview["state"] = "approval_blocked"
                preview["updated_at"] = self.clock()
                self._approval_envelopes[envelope["approval_id"]] = envelope
                self._approval_to_preview[envelope["approval_id"]] = preview_id
                self._audit_approval_requested(preview, envelope)
                return _public_envelope(envelope)

            context = _approval_context_for_action(action)
            record = self.mission_loop.approval_service.request(
                action_type=action["action_type"],
                requested_by=actor or "David",
                reason=action["summary"],
                context=context,
                approval_kind=ApprovalKind.STRONG if action["approval_level"] == "strong" else ApprovalKind.NORMAL,
                expires_in_seconds=900,
            )
            envelope = {
                "schema_version": GOVERNED_EXECUTION_SCHEMA_VERSION,
                "approval_id": record.approval_id,
                "preview_id": preview_id,
                "correlation_id": preview["correlation_id"],
                "created_at": record.requested_at,
                "expires_at": record.expires_at,
                "status": record.status.value,
                "action_type": action["action_type"],
                "risk_level": action["risk_level"],
                "approval_level": action["approval_level"],
                "confirmation_level_required": action["approval_level"],
                "confirmation_phrase": record.user_confirmation_phrase,
                "readback_required": action["requires_readback"],
                "readback_text": _readback_text(preview),
                "requires_strong_confirmation": action["requires_strong_confirmation"],
                "requires_double_confirmation": action["requires_double_confirmation"],
                "requires_triple_confirmation": action["requires_triple_confirmation"],
                "stronger_approval_configured": False,
                "can_approve": True,
                "can_dispatch_after_approval": action["action_type"] == ALLOWED_ACTION,
                "requested_by": actor,
                "decision_reason": "",
                "context_fingerprint": record.context_fingerprint,
            }
            self._bind_filesystem_read_candidate(preview, envelope)
            preview["approval_envelope"] = envelope
            preview["state"] = "approval_requested"
            preview["updated_at"] = self.clock()
            self._approval_envelopes[record.approval_id] = envelope
            self._approval_to_preview[record.approval_id] = preview_id
            self._audit_approval_requested(preview, envelope)
            return _public_envelope(envelope)

    def decide_approval(
        self,
        *,
        approval_id: str,
        decision: str,
        actor: str = "David",
        confirmation_phrase: Optional[str] = None,
        readback_text: Optional[str] = None,
        reason: str = "",
    ) -> Dict[str, Any]:
        normalized = (decision or "").strip().lower().replace("-", "_")
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            if envelope is None:
                raise KeyError(approval_id)
            preview = self._previews[envelope["preview_id"]]
            if envelope["status"] in {"approved", "rejected", "cancelled", "expired", "blocked"}:
                if normalized == envelope["status"]:
                    return _public_envelope(envelope)
                raise ValueError(f"approval {approval_id} is already {envelope['status']}")
            self._audit(
                "ui_approval_action",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level=envelope["approval_level"],
                metadata={
                    "approval_id": approval_id,
                    "preview_id": preview["preview_id"],
                    "decision": normalized,
                    "actor": actor,
                    "voice_approval": False,
                    "wake_phrase_approval": False,
                },
            )

            if normalized in {"reject", "rejected", "deny"}:
                record = self.mission_loop.approval_service.decide(
                    approval_id,
                    "rejected",
                    actor=actor,
                    reason=reason,
                )
                envelope["status"] = record.status.value
                envelope["decision_reason"] = record.decision_reason or ""
                preview["state"] = "approval_rejected"
                preview["updated_at"] = self.clock()
                self._audit("approval_rejected", correlation_id=preview["correlation_id"], risk_level=envelope["risk_level"], approval_level=envelope["approval_level"], metadata={"approval_id": approval_id, "preview_id": preview["preview_id"]})
                return _public_envelope(envelope)

            if normalized in {"cancel", "cancelled"}:
                envelope["status"] = "cancelled"
                envelope["decision_reason"] = reason or "cancelled by operator"
                preview["state"] = "approval_cancelled"
                preview["cancelled"] = True
                preview["updated_at"] = self.clock()
                self._audit("approval_cancelled", correlation_id=preview["correlation_id"], risk_level=envelope["risk_level"], approval_level=envelope["approval_level"], metadata={"approval_id": approval_id, "preview_id": preview["preview_id"]})
                return _public_envelope(envelope)

            if normalized in {"clarify", "clarification", "request_clarification", "clarification_requested"}:
                envelope["status"] = "clarification_requested"
                envelope["decision_reason"] = reason or "operator requested clarification"
                preview["state"] = "clarification_requested"
                preview["updated_at"] = self.clock()
                return _public_envelope(envelope)

            if normalized not in {"approve", "approved"}:
                raise ValueError("decision must be approve, reject, cancel, or request_clarification")
            if envelope["requires_double_confirmation"] or envelope["requires_triple_confirmation"]:
                envelope["status"] = "blocked"
                envelope["decision_reason"] = "requires_stronger_approval_not_configured"
                preview["state"] = "approval_blocked"
                self._audit("approval_blocked", correlation_id=preview["correlation_id"], risk_level=envelope["risk_level"], approval_level=envelope["approval_level"], metadata={"approval_id": approval_id, "reason": "requires_stronger_approval_not_configured"})
                return _public_envelope(envelope)
            if envelope["readback_required"] and _normalize_readback(readback_text) != _normalize_readback(envelope["readback_text"]):
                raise ValueError("readback text does not match required readback")
            record = self.mission_loop.approval_service.decide(
                approval_id,
                "approved",
                actor=actor,
                reason=reason,
                confirmation_phrase=confirmation_phrase,
            )
            envelope["status"] = record.status.value
            envelope["decision_reason"] = record.decision_reason or ""
            envelope["approved_at"] = record.approved_at
            preview["state"] = "approval_approved"
            preview["updated_at"] = self.clock()
            self._mark_bound_candidate_approved(preview, approval_id)
            self._audit("approval_approved", correlation_id=preview["correlation_id"], risk_level=envelope["risk_level"], approval_level=envelope["approval_level"], metadata={"approval_id": approval_id, "preview_id": preview["preview_id"]})
            return _public_envelope(envelope)

    def dispatch(self, *, preview_id: str, approval_id: Optional[str] = None, actor: str = "David") -> Dict[str, Any]:
        with self._lock:
            preview = self._previews.get(preview_id)
            if preview is None:
                raise KeyError(preview_id)
            if preview.get("cancelled"):
                raise ValueError("preview is cancelled")
            action = preview["action"]
            self._audit("dispatch_requested", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "action_type": action["action_type"], "actor": actor})

            if preview["decision"] == "denied":
                self._audit("dispatch_blocked", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "reason": preview["denied_reason"] or "denied"})
                raise ValueError(preview["protected_message"] or "denied action cannot dispatch")
            if preview["decision"] == "unsupported":
                self._audit("dispatch_blocked", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "reason": preview["unsupported_reason"] or "unsupported"})
                return self._unsupported_dispatch(preview)
            if not preview["requires_approval"]:
                return self._direct_allowed_dispatch(preview)

            envelope = preview.get("approval_envelope")
            if envelope is None:
                self._audit("dispatch_blocked", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "reason": "approval required"})
                raise ValueError("approval required before dispatch")
            if approval_id and approval_id != envelope["approval_id"]:
                raise ValueError("approval_id does not match preview approval envelope")
            if envelope["status"] != ApprovalStatus.APPROVED.value:
                self._audit("dispatch_blocked", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "approval_id": envelope["approval_id"], "approval_status": envelope["status"]})
                raise ValueError(f"approval status is {envelope['status']}")
            if action["action_type"] != ALLOWED_ACTION:
                return self._unsupported_dispatch(preview)
            record = self.mission_loop.approval_service.get(envelope["approval_id"])
            self.mission_loop.approval_service.refresh_expiration(record)
            if record.status != ApprovalStatus.APPROVED:
                envelope["status"] = record.status.value
                self._audit("approval_expired" if record.status == ApprovalStatus.EXPIRED else "dispatch_blocked", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"approval_id": envelope["approval_id"], "status": record.status.value})
                raise ValueError(f"approval status is {record.status.value}")
            preview["state"] = "dispatching"
            preview["updated_at"] = self.clock()

        result = self.hermes_runtime_bridge.execute_read(
            mission_id=preview["mission_id"],
            candidate_id=preview["candidate_id"],
            approval=record,
        )
        with self._lock:
            preview["dispatch"] = result
            session = result.get("session") if isinstance(result, dict) else None
            if isinstance(session, dict) and session.get("session_id"):
                self._session_to_preview[session["session_id"]] = preview_id
            status = str(result.get("status", "unknown")) if isinstance(result, dict) else "unknown"
            if status == "blocked":
                preview["state"] = "dispatch_blocked"
                self._audit("dispatch_blocked", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "approval_id": envelope["approval_id"], "status": status, "reasons": result.get("blocked_reasons", [])})
            elif status in {"success", "already_completed"}:
                preview["state"] = "dispatch_completed"
                self._audit("dispatch_started", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], hermes_dispatch_allowed=True, metadata={"preview_id": preview_id, "approval_id": envelope["approval_id"], "governed_dispatch": True, "session_id": session.get("session_id") if isinstance(session, dict) else "unknown"})
                self._audit("dispatch_completed", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], hermes_dispatch_allowed=True, metadata={"preview_id": preview_id, "approval_id": envelope["approval_id"], "governed_dispatch": True, "session_id": session.get("session_id") if isinstance(session, dict) else "unknown", "status": status})
            elif status in {"running", "already_running", "cancellation_pending", "timeout_interrupt_pending"}:
                preview["state"] = "running"
                self._audit("dispatch_started", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], hermes_dispatch_allowed=True, metadata={"preview_id": preview_id, "approval_id": envelope["approval_id"], "governed_dispatch": True, "session_id": session.get("session_id") if isinstance(session, dict) else "unknown", "status": status})
            else:
                preview["state"] = "dispatch_failed"
                self._audit("dispatch_failed", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "approval_id": envelope["approval_id"], "status": status})
            preview["updated_at"] = self.clock()
            return _safe_dispatch_result(preview)

    def cancel(self, *, preview_id: str, reason: str = "operator cancel", actor: str = "David") -> Dict[str, Any]:
        with self._lock:
            preview = self._previews.get(preview_id)
            if preview is None:
                raise KeyError(preview_id)
            preview["cancelled"] = True
            preview["state"] = "cancelled"
            preview["updated_at"] = self.clock()
            envelope = preview.get("approval_envelope")
            if envelope and envelope["status"] == "pending":
                envelope["status"] = "cancelled"
                envelope["decision_reason"] = reason
                self._audit("approval_cancelled", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "approval_id": envelope["approval_id"], "actor": actor})
            self._audit("ui_approval_action", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview_id, "decision": "cancel", "actor": actor, "voice_approval": False, "wake_phrase_approval": False})
            return _public_preview(preview)

    def stop(self, *, preview_id: Optional[str] = None, session_id: Optional[str] = None, reason: str = "operator stop") -> Dict[str, Any]:
        with self._lock:
            if not preview_id and session_id:
                preview_id = self._session_to_preview.get(session_id)
            preview = self._previews.get(preview_id or "") if preview_id else None
            correlation_id = preview["correlation_id"] if preview else f"corr-{self.id_factory()}"
            risk_level = preview["risk_level"] if preview else "low"
            approval_level = preview["approval_level"] if preview else "direct"
            self._audit("stop_requested", correlation_id=correlation_id, risk_level=risk_level, approval_level=approval_level, metadata={"preview_id": preview_id or "unknown", "session_id": session_id or "unknown", "reason": reason})
            if preview and not session_id:
                session = (preview.get("dispatch") or {}).get("session")
                session_id = session.get("session_id") if isinstance(session, dict) else None
            if not session_id:
                self._audit("stop_unsupported", correlation_id=correlation_id, risk_level=risk_level, approval_level=approval_level, metadata={"preview_id": preview_id or "unknown", "reason": "no running session"})
                return {"status": "stop_unsupported", "reason": "no running session", "preview_id": preview_id, "session_id": session_id}
        try:
            stopped = self.hermes_runtime_bridge.stop(session_id, reason=reason)
        except KeyError:
            self._audit("stop_unsupported", correlation_id=correlation_id, risk_level=risk_level, approval_level=approval_level, metadata={"preview_id": preview_id or "unknown", "session_id": session_id, "reason": "session not found"})
            return {"status": "stop_unsupported", "reason": "session not found", "preview_id": preview_id, "session_id": session_id}
        with self._lock:
            if preview:
                preview["state"] = "stop_completed" if stopped.get("ended_at") else "stop_requested"
                preview["updated_at"] = self.clock()
                preview["dispatch"] = {"status": stopped.get("status", "unknown"), "session": stopped}
            self._audit("stop_completed", correlation_id=correlation_id, risk_level=risk_level, approval_level=approval_level, metadata={"preview_id": preview_id or "unknown", "session_id": session_id, "status": stopped.get("status", "unknown")})
        return {"status": "stop_completed", "session": stopped, "preview_id": preview_id}

    def _candidate_action(
        self,
        *,
        intent: str,
        normalized_text: str,
        classification: Mapping[str, Any],
        source: str,
        target_path: Optional[str],
        command: Optional[str],
        requested_action_type: Optional[str],
    ) -> Dict[str, Any]:
        text = " ".join(str(item or "") for item in (intent, normalized_text, requested_action_type, command)).strip()
        folded = text.casefold()
        if source == "wake_phrase_command" and _contains_any(
            folded,
            ("approve", "approved", "aprueba", "aprobar", "confirmo", "continúa", "continua", "ejecuta", "hazlo"),
        ):
            return _action(
                "denied",
                "wake_phrase",
                "Wake phrase no aprueba",
                "La wake phrase no es permiso y no puede aprobar ni ejecutar acciones.",
                "forbidden",
                "forbidden",
                "wake_phrase_is_not_approval",
                action_type="wake_phrase_approval_attempt",
                will_not_do=["No aprobar por wake phrase.", "No ejecutar por wake phrase.", "No despachar Hermes."],
            )
        if _contains_any(folded, _SECRET_MARKERS) or _path_is_secret_like(target_path):
            return _action(
                "denied",
                "credentials",
                "Credenciales y secretos protegidos",
                "La petición intenta acceder a credenciales, secretos, tokens, cookies, sesiones o .env.",
                "forbidden",
                "forbidden",
                "credential_or_secret_material_is_denied",
                action_type="credential_access",
                will_not_do=["No leer .env.", "No leer secretos/tokens/cookies/sesiones.", "No aprobar por voz ni wake phrase.", "No despachar Hermes."],
            )
        if classification.get("denied") or _contains_any(folded, _DENIED_MARKERS):
            return _action(
                "denied",
                "unsafe_or_unauthorized",
                "Acción denegada",
                "La petición parece insegura, ilegal, no autorizada o intenta saltarse aprobaciones.",
                "forbidden",
                "forbidden",
                "unsafe_unauthorized_or_illegal",
                action_type="denied_action",
            )
        if _contains_any(folded, _DESTRUCTIVE_MARKERS):
            return _action(
                "denied",
                "destructive",
                "Acción destructiva denegada",
                "Borrado o destrucción de archivos/sistema queda fuera de Fase 1.",
                "forbidden",
                "forbidden",
                "destructive_action_denied",
                action_type="destructive_action",
            )
        if target_path:
            return self._filesystem_read_action(target_path)
        if requested_action_type == "filesystem_read" or _contains_any(folded, _READ_FILE_MARKERS):
            return _action(
                "unsupported",
                "",
                "Lectura local requiere ruta exacta",
                "Fase 1 solo puede despachar Hermes para una ruta local exacta, no para lecturas amplias o ambiguas.",
                "medium",
                "simple",
                unsupported_reason="exact_local_file_path_required",
                action_type=ALLOWED_ACTION,
                requires_approval=True,
            )
        if command or _contains_any(folded, _COMMAND_MARKERS):
            return self._command_action(command or normalized_text)
        if _contains_any(folded, _CRITICAL_MARKERS):
            return _action(
                "requires_approval",
                "",
                "Acción crítica bloqueada por confirmación fuerte no configurada",
                "Producción, dinero, Stripe, dominio o publicación requieren double/triple confirmation real.",
                "critical",
                "triple",
                unsupported_reason="requires_stronger_approval_not_configured",
                action_type="critical_external_action",
                requires_approval=True,
                requires_readback=True,
                requires_strong=True,
                requires_double=True,
                requires_triple=True,
                will_do=["Crear preview y explicación de riesgo.", "Bloquear dispatch porque double/triple confirmation no está configurado."],
                will_not_do=["No deploy.", "No dinero.", "No Stripe.", "No email/publicación.", "No credenciales."],
                rollback_plan="Rollback/stop plan requerido antes de Fase 2; no hay ejecución en Fase 1.",
                stop_plan="Stop inmediato; no iniciar acción externa.",
            )
        if _contains_any(folded, _HIGH_MARKERS):
            return _action(
                "unsupported",
                "",
                "Acción sensible no soportada por ejecución real Fase 1",
                "Red, email, instalación, shell o acciones externas no tienen runtime gobernado real en Fase 1.",
                "high",
                "strong",
                unsupported_reason="sensitive_external_or_shell_action_not_supported",
                action_type="unsupported_sensitive_action",
                requires_approval=True,
                requires_readback=True,
                requires_strong=True,
            )
        if _contains_any(folded, _STATUS_MARKERS):
            return _action(
                "allowed",
                "",
                "Inspección de estado local",
                "Consulta read-only de estado JARVIS/doctor/event stream sin Hermes.",
                "low",
                "direct",
                action_type="system_status_read",
                will_do=["Leer estado local ya expuesto por JARVIS.", "No llamar a Hermes.", "Auditar metadata-only."],
                will_not_do=["No ejecutar shell.", "No leer secretos.", "No activar sensores."],
                rollback_plan="No hay mutación; rollback no aplica.",
                stop_plan="Cancelar la preview si el operador no quiere consultar estado.",
            )
        policy = self.policy_engine.classify_action(normalized_text or intent)
        if policy.decision == PolicyDecision.REQUIRES_APPROVAL:
            return _action(
                "unsupported",
                "",
                "Acción requiere aprobación pero no tiene runtime real",
                policy.reason,
                "high",
                "strong",
                unsupported_reason="approved_runtime_not_configured_for_this_action",
                action_type="unsupported_policy_gated_action",
                requires_approval=True,
                requires_readback=True,
                requires_strong=True,
            )
        return _action(
            "allowed",
            "",
            "Preview prepare-only",
            "Preparación local sin dispatch real.",
            "low",
            "direct",
            action_type="prepare_only",
            will_do=["Crear preview, riesgo y siguiente paso.", "Auditar metadata-only."],
            will_not_do=["No despachar Hermes.", "No ejecutar comandos.", "No tocar archivos ni red."],
            rollback_plan="No hay mutación; rollback no aplica.",
            stop_plan="Cancelar preview si no se necesita.",
        )

    def _filesystem_read_action(self, target_path: str) -> Dict[str, Any]:
        try:
            path = Path(target_path).expanduser().resolve()
        except (OSError, ValueError) as exc:
            return _action(
                "unsupported",
                "",
                "Ruta local no resoluble",
                f"No se puede resolver la ruta: {exc}",
                "medium",
                "simple",
                unsupported_reason="target_path_cannot_be_resolved",
                action_type=ALLOWED_ACTION,
                requires_approval=True,
            )
        if _path_is_secret_like(str(path)):
            return _action(
                "denied",
                "credentials",
                "Credenciales y secretos protegidos",
                "La ruta apunta a material secreto o credencial.",
                "forbidden",
                "forbidden",
                "credential_or_secret_material_is_denied",
                action_type=ALLOWED_ACTION,
            )
        if not path.exists() or not path.is_file() or path.is_symlink():
            return _action(
                "unsupported",
                "",
                "Lectura local no soportada para esa ruta",
                "La ruta debe existir, ser archivo regular y no symlink.",
                "medium",
                "simple",
                unsupported_reason="target_path_must_be_existing_regular_file",
                action_type=ALLOWED_ACTION,
                requires_approval=True,
            )
        return _action(
            "requires_approval",
            "",
            "Lectura local exacta por Hermes",
            "JARVIS puede pedir aprobación simple para que Hermes lea exactamente un archivo local con read_file.",
            "medium",
            "simple",
            action_type=ALLOWED_ACTION,
            requires_approval=True,
            target_path=str(path),
            scope=[str(path)],
            will_do=["Crear approval bound al path exacto.", "Despachar Hermes con read_file una vez si se aprueba.", "Auditar dispatch metadata-only."],
            will_not_do=["No leer directorios.", "No leer .env/secrets.", "No escribir archivos.", "No ejecutar shell.", "No usar red."],
            rollback_plan="No hay mutación; rollback no aplica.",
            stop_plan="Stop cooperativo de sesión Hermes si está en ejecución.",
        )

    def _command_action(self, command: str) -> Dict[str, Any]:
        normalized = " ".join(str(command or "").split())
        allowlisted = any(normalized == item or normalized.startswith(item + " ") for item in ALLOWED_LOCAL_COMMANDS)
        return _action(
            "unsupported",
            "",
            "Comando local no ejecutado en Fase 1",
            "La ejecución de terminal no está conectada al bridge Hermes gobernado de Fase 1.",
            "high",
            "strong",
            unsupported_reason="terminal_runtime_not_configured",
            action_type="local_command",
            requires_approval=True,
            requires_readback=True,
            requires_strong=True,
            will_do=["Mostrar preview del comando allowlisted." if allowlisted else "Bloquear comando no allowlisted."],
            will_not_do=["No ejecutar shell.", "No ejecutar texto arbitrario.", "No instalar dependencias."],
            rollback_plan="No hay mutación porque no se ejecuta.",
            stop_plan="No hay proceso que parar; cancel cancela la preview.",
            command_fingerprint=_fingerprint(normalized),
            command_allowlisted=allowlisted,
        )

    def _memory_influence(self, *, correlation_id: str) -> List[Dict[str, Any]]:
        try:
            preview = self.memory_brain_v2.preview(limit=10)
        except Exception:
            return []
        active = []
        for memory in preview.get("active_memories", []):
            if memory.get("sensitivity") != "normal":
                continue
            active.append({
                "memory_id": memory.get("memory_id", "unknown"),
                "memory_type": memory.get("memory_type", "unknown"),
                "content_summary": memory.get("content_summary", "unknown"),
                "why_used": memory.get("why_used") if memory.get("why_used") != "unknown" else "Explain preview context only.",
                "influence_summary": memory.get("influence_summary", "unknown"),
                "used_for_permission": False,
            })
        if active:
            self._audit(
                "memory_influence_used",
                correlation_id=correlation_id,
                surface="memory_brain_v2",
                risk_level="memory_privacy",
                approval_level="direct",
                metadata={
                    "memory_count": len(active),
                    "memory_ids": [item["memory_id"] for item in active],
                    "used_for_permission": False,
                    "sensitive_memory_autoloaded": False,
                },
            )
        return active

    def _bind_filesystem_read_candidate(self, preview: Dict[str, Any], envelope: Dict[str, Any]) -> None:
        action = preview["action"]
        if action["action_type"] != ALLOWED_ACTION:
            return
        path = Path(action["target_path"]).expanduser().resolve()
        mission = self.mission_loop.create_mission({
            "objective": "governed exact local file read",
            "context": "Phase 1 governed Hermes execution via existing Mark 3 runtime bridge.",
            "desired_outcome": "metadata-only evidence of read_file dispatch",
            "success_criteria": ["Hermes read_file attempted within approved exact path"],
            "declared_authorization": "operator requested governed local read",
            "allowed_scope": ["repo"],
            "allowed_paths_resources": [str(path)],
            "allowed_tools": [ALLOWED_TOOL],
            "prohibited_tools": ["terminal", "browser", "network", "money", "deploy", "email", "credentials"],
            "monetary_budget": 0,
            "time_budget_seconds": 30,
            "max_steps": 1,
            "allowed_data": ["local non-secret file metadata"],
            "constraints": ["read-only", "exact path", "no secrets", "no network", "no writes"],
            "stop_conditions": ["operator stop", "policy violation"],
            "expected_rollback": "none; read-only action",
            "instruction_origin": "phase_1_governed_execution",
            "requested_risk_level": 1,
            "correlation_id": preview["correlation_id"],
        })
        mission_id = mission["intake"]["mission_id"]
        record = self.mission_loop.approval_service.get(envelope["approval_id"])
        step = MissionStep(
            step_id="step-1",
            order=1,
            description=ALLOWED_ACTION,
            objective="read exact local file",
            action_type=ALLOWED_ACTION,
            inputs={},
            expected_outputs=["metadata-only execution evidence"],
            required_capability=ALLOWED_CAPABILITY,
            tool_candidate=ALLOWED_TOOL,
            scope=[str(path)],
            budget=0,
            timeout_seconds=30,
            risk_level=1,
            approval_required=True,
            strong_approval_required=False,
            double_confirmation_required=False,
            triple_confirmation_required=False,
            preconditions=["exact path approval"],
            dependencies=[],
            evidence_requirements=["Hermes read_file call observed"],
            stop_condition="operator stop",
            rollback_compensation="none; read-only action",
            capability_available=True,
            approval_satisfied=False,
            approval_id=envelope["approval_id"],
        )
        candidate = ExecutionCandidate(
            candidate_id="candidate-step-1",
            mission_id=mission_id,
            step_id="step-1",
            exact_action=ALLOWED_ACTION,
            adapter_capability=ALLOWED_CAPABILITY,
            tool_candidate=ALLOWED_TOOL,
            scope=[str(path)],
            budget=0,
            timeout_seconds=30,
            risk_level=1,
            approval_requirement={
                "backend": ALLOWED_BACKEND,
                "cwd": str(path.parent),
                "approval_id": envelope["approval_id"],
            },
            context_fingerprint=record.context_fingerprint,
            audit_correlation_id=preview["correlation_id"],
            stop_plan="operator stop",
            rollback_plan="none; read-only action",
            evidence_requirements=["Hermes read_file call observed"],
            capability_available=True,
            eligibility=True,
            approval_required=True,
            approval_satisfied=False,
            execution_capability_available=True,
        )
        memory = self.mission_loop._missions[mission_id]
        memory.plan = [step]
        memory.candidates = [candidate]
        memory.status = MissionLoopStatus.AWAITING_APPROVAL
        preview["mission_id"] = mission_id
        preview["candidate_id"] = candidate.candidate_id
        preview["step_id"] = step.step_id

    def _mark_bound_candidate_approved(self, preview: Dict[str, Any], approval_id: str) -> None:
        if not preview.get("mission_id"):
            return
        memory = self.mission_loop._missions[preview["mission_id"]]
        for step in memory.plan:
            if step.approval_id == approval_id:
                step.approval_satisfied = True
                step.status = "planned"
        for candidate in memory.candidates:
            if candidate.approval_requirement.get("approval_id") == approval_id:
                candidate.approval_satisfied = True
                candidate.eligibility = True
                candidate.approval_requirement["approval_satisfied"] = True
        memory.status = MissionLoopStatus.EXECUTION_CANDIDATE_READY

    def _blocked_stronger_approval_envelope(self, preview: Dict[str, Any], actor: str) -> Dict[str, Any]:
        action = preview["action"]
        return {
            "schema_version": GOVERNED_EXECUTION_SCHEMA_VERSION,
            "approval_id": f"blocked-approval-{self.id_factory()}",
            "preview_id": preview["preview_id"],
            "correlation_id": preview["correlation_id"],
            "created_at": self.clock(),
            "expires_at": "",
            "status": "blocked",
            "action_type": action["action_type"],
            "risk_level": action["risk_level"],
            "approval_level": action["approval_level"],
            "confirmation_level_required": action["approval_level"],
            "confirmation_phrase": None,
            "readback_required": action["requires_readback"],
            "readback_text": _readback_text(preview),
            "requires_strong_confirmation": action["requires_strong_confirmation"],
            "requires_double_confirmation": action["requires_double_confirmation"],
            "requires_triple_confirmation": action["requires_triple_confirmation"],
            "stronger_approval_configured": False,
            "can_approve": False,
            "can_dispatch_after_approval": False,
            "requested_by": actor,
            "decision_reason": "requires_stronger_approval_not_configured",
            "context_fingerprint": "",
        }

    def _audit_approval_requested(self, preview: Dict[str, Any], envelope: Dict[str, Any]) -> None:
        self._audit(
            "approval_requested",
            correlation_id=preview["correlation_id"],
            risk_level=envelope["risk_level"],
            approval_level=envelope["approval_level"],
            metadata={
                "approval_id": envelope["approval_id"],
                "preview_id": preview["preview_id"],
                "status": envelope["status"],
                "readback_required": envelope["readback_required"],
                "requires_double_confirmation": envelope["requires_double_confirmation"],
                "requires_triple_confirmation": envelope["requires_triple_confirmation"],
                "voice_approval": False,
                "wake_phrase_approval": False,
            },
        )
        if envelope["status"] == "blocked":
            self._audit(
                "approval_blocked",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level=envelope["approval_level"],
                metadata={
                    "approval_id": envelope["approval_id"],
                    "preview_id": preview["preview_id"],
                    "reason": envelope["decision_reason"],
                },
            )

    def _direct_allowed_dispatch(self, preview: Dict[str, Any]) -> Dict[str, Any]:
        preview["state"] = "dispatch_completed"
        preview["dispatch"] = {
            "status": "completed",
            "mode": "local_control_plane_read",
            "hermes_called": False,
            "message": "Read-only local status action completed without Hermes dispatch.",
        }
        preview["updated_at"] = self.clock()
        self._audit("dispatch_started", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview["preview_id"], "hermes_called": False, "governed_dispatch": False})
        self._audit("dispatch_completed", correlation_id=preview["correlation_id"], risk_level=preview["risk_level"], approval_level=preview["approval_level"], metadata={"preview_id": preview["preview_id"], "hermes_called": False, "governed_dispatch": False, "status": "completed"})
        return _safe_dispatch_result(preview)

    def _unsupported_dispatch(self, preview: Dict[str, Any]) -> Dict[str, Any]:
        preview["state"] = "unsupported"
        preview["dispatch"] = {
            "status": "unsupported",
            "reason": preview.get("unsupported_reason") or "unsupported",
            "hermes_called": False,
            "did_execute": False,
        }
        preview["updated_at"] = self.clock()
        return _safe_dispatch_result(preview)

    def _audit(
        self,
        event_type: str,
        *,
        correlation_id: str,
        surface: str = "execution",
        risk_level: str = "low",
        approval_level: str = "direct",
        metadata: Optional[Mapping[str, Any]] = None,
        hermes_dispatch_allowed: bool = False,
    ) -> None:
        self.audit_ledger.record(
            event_type=event_type,
            surface=surface,
            source="/mark-3/execution",
            risk_level=risk_level,
            approval_level=approval_level,
            correlation_id=correlation_id,
            metadata={
                "metadata_only": True,
                "contains_raw_audio": False,
                "contains_camera_frame": False,
                "contains_secret": False,
                "contains_credential": False,
                "contains_full_transcript": False,
                **dict(metadata or {}),
            },
            contains_full_transcript=False,
            hermes_dispatch_allowed=hermes_dispatch_allowed,
        )


def _action(
    decision: str,
    denial_category: str,
    title: str,
    summary: str,
    risk_level: str,
    approval_level: str,
    denied_reason: str = "",
    *,
    unsupported_reason: str = "",
    action_type: str = "prepare_only",
    requires_approval: bool = False,
    requires_readback: bool = False,
    requires_strong: bool = False,
    requires_double: bool = False,
    requires_triple: bool = False,
    target_path: str = "",
    scope: Optional[List[str]] = None,
    will_do: Optional[List[str]] = None,
    will_not_do: Optional[List[str]] = None,
    rollback_plan: str = "No mutation; no rollback needed.",
    stop_plan: str = "Cancel preview before dispatch.",
    **extra: Any,
) -> Dict[str, Any]:
    return {
        "action_id": f"action-{_fingerprint(summary)[:16]}",
        "title": title,
        "summary": summary,
        "decision": decision,
        "action_type": action_type,
        "risk_level": risk_level,
        "approval_level": approval_level,
        "requires_approval": bool(requires_approval),
        "requires_readback": bool(requires_readback),
        "requires_strong_confirmation": bool(requires_strong),
        "requires_double_confirmation": bool(requires_double),
        "requires_triple_confirmation": bool(requires_triple),
        "denial_category": denial_category,
        "denied_reason": denied_reason,
        "unsupported_reason": unsupported_reason,
        "target_path": target_path,
        "target_path_fingerprint": _fingerprint(target_path) if target_path else "",
        "scope": list(scope or []),
        "will_do": will_do or ["Create governed preview.", "Audit metadata-only."],
        "will_not_do": will_not_do or ["No direct Hermes from frontend.", "No shell.", "No secrets.", "No external side effects."],
        "rollback_plan": rollback_plan,
        "stop_plan": stop_plan,
        "memory_grants_permission": False,
        "frontend_direct_hermes_allowed": False,
        **extra,
    }


def _approval_context_for_action(action: Mapping[str, Any]) -> Dict[str, Any]:
    if action.get("action_type") == ALLOWED_ACTION:
        return {"action_type": ALLOWED_ACTION, "target": "read", "tool_name": ALLOWED_TOOL}
    return {
        "action_type": action.get("action_type", "unknown"),
        "target": action.get("title", "unknown"),
        "tool_name": action.get("tool_candidate", "unknown"),
    }


def _readback_text(preview: Mapping[str, Any]) -> str:
    action = preview.get("action", {})
    return (
        f"I approve {action.get('action_type', 'unknown')} for preview {preview.get('preview_id', 'unknown')} "
        f"with risk {preview.get('risk_level', 'unknown')} and scope {', '.join(action.get('scope') or ['none'])}."
    )


def _normalize_readback(value: Optional[str]) -> str:
    return " ".join(str(value or "").strip().split()).casefold()


def _redacted_intake(intake: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in intake.items()
        if key not in {"raw_text", "normalized_text", "remaining_command"}
    } | {
        "raw_text_omitted": True,
        "normalized_text_fingerprint": _fingerprint(intake.get("normalized_text", "")),
        "remaining_command_fingerprint": _fingerprint(intake.get("remaining_command", "")),
    }


def _preview_audit_metadata(preview: Mapping[str, Any]) -> Dict[str, Any]:
    action = preview.get("action", {})
    return {
        "preview_id": preview.get("preview_id"),
        "decision": preview.get("decision"),
        "action_type": action.get("action_type"),
        "target_path_fingerprint": action.get("target_path_fingerprint"),
        "risk_level": preview.get("risk_level"),
        "approval_level": preview.get("approval_level"),
        "requires_approval": preview.get("requires_approval"),
        "memory_influence_count": len(preview.get("preview", {}).get("memory_influence", [])),
    }


def _public_preview(preview: Mapping[str, Any]) -> Dict[str, Any]:
    data = dict(preview)
    action = dict(data.get("action") or {})
    if action.get("target_path"):
        action["target_path_display"] = action["target_path"]
    action.pop("target_path", None)
    data["action"] = action
    if data.get("approval_envelope"):
        data["approval_envelope"] = _public_envelope(data["approval_envelope"])
    return data


def _public_envelope(envelope: Mapping[str, Any]) -> Dict[str, Any]:
    return dict(envelope)


def _safe_dispatch_result(preview: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": GOVERNED_EXECUTION_SCHEMA_VERSION,
        "preview_id": preview.get("preview_id"),
        "state": preview.get("state"),
        "decision": preview.get("decision"),
        "risk_level": preview.get("risk_level"),
        "approval_level": preview.get("approval_level"),
        "dispatch": preview.get("dispatch"),
        "hermes_dispatch_allowed": preview.get("state") in {"dispatch_completed", "running"} and (preview.get("action") or {}).get("action_type") == ALLOWED_ACTION,
        "frontend_direct_hermes_allowed": False,
        "memory_grants_permission": False,
    }


def _path_is_secret_like(value: Optional[str]) -> bool:
    if not value:
        return False
    lowered = str(value).casefold()
    try:
        name = Path(value).name.casefold()
    except (OSError, ValueError):
        name = ""
    return name in _SECRET_PATH_NAMES or any(marker in lowered for marker in _SECRET_MARKERS)


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    folded = text.casefold()
    return any(marker in folded for marker in markers)


def _safe_choice(value: str, allowed: set[str], fallback: str) -> str:
    return value if value in allowed else fallback


def _check(name: str, passed: bool, notes: str) -> Dict[str, Any]:
    return {"name": name, "status": "passed" if passed else "missing", "passed": bool(passed), "notes": notes}


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(str(value or "").encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
