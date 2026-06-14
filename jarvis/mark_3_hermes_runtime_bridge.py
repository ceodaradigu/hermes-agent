from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from jarvis.approval_hardening import ApprovalRecord, ApprovalStatus
from jarvis.mark_3_mission_loop import Mark3MissionLoop
from jarvis.mark_3_mission_loop_models import ExecutionCandidate, MissionLoopStatus, VerificationState
from jarvis.runtime.hermes_adapter import HermesAdapterConfig, HermesRuntimeAdapter


ALLOWED_TOOL = "read_file"
ALLOWED_ACTION = "filesystem_read"
ALLOWED_CAPABILITY = "hermes.file.read"
ALLOWED_BACKEND = "local"
BLOCKED_NAMES = {".env"}
SECRET_MARKERS = ("secret", "token", "password", "credential", "private_key")
INTERRUPT_GRACE_SECONDS = 2.0
RUNNING_STATUSES = {"running", "cancellation_pending", "timeout_interrupt_pending"}


@dataclass(frozen=True)
class ExecutionClassification:
    status: str
    step_status: str
    evidence_state: str
    error: Optional[str]
    successful_read_observed: bool


@dataclass
class HermesRuntimeSession:
    session_id: str
    mission_id: str
    step_id: str
    candidate_id: str
    status: str
    path_fingerprint: str
    started_at: str
    ended_at: Optional[str] = None
    outcome: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    interrupted: bool = False
    interrupt_requested: bool = False
    interrupt_delivered: bool = field(default=False, repr=False)
    worker_alive: bool = False
    forced_cancellation_available: bool = False
    tool_calls: list[Dict[str, Any]] = field(default_factory=list)
    adapter: Any = None
    worker: Optional[threading.Thread] = field(default=None, repr=False)
    finalizing: bool = field(default=False, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mission_id": self.mission_id,
            "step_id": self.step_id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "path_fingerprint": self.path_fingerprint,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "outcome": self.outcome,
            "error": self.error,
            "interrupted": self.interrupted,
            "interrupt_requested": self.interrupt_requested,
            "worker_alive": bool(self.worker and self.worker.is_alive()) or self.worker_alive,
            "forced_cancellation_available": self.forced_cancellation_available,
            "tool_calls": list(self.tool_calls),
        }


class Mark3HermesRuntimeBridge:
    def __init__(
        self,
        mission_loop: Mark3MissionLoop,
        *,
        adapter_factory: Optional[Callable[[Callable[[str, Dict[str, Any]], Any]], Any]] = None,
        clock: Optional[Callable[[], str]] = None,
    ) -> None:
        self.mission_loop = mission_loop
        self.adapter_factory = adapter_factory or self._default_adapter_factory
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self._lock = threading.Lock()
        self._candidate_sessions: Dict[str, str] = {}
        self._sessions: Dict[str, HermesRuntimeSession] = {}

    def status(self) -> Dict[str, Any]:
        with self._lock:
            running = sum(1 for item in self._sessions.values() if item.status in RUNNING_STATUSES)
            total = len(self._sessions)
        return {
            "available": True,
            "pr": 134,
            "supported_tool": ALLOWED_TOOL,
            "supported_action_type": ALLOWED_ACTION,
            "supported_capability": ALLOWED_CAPABILITY,
            "backend": ALLOWED_BACKEND,
            "general_execution_enabled": False,
            "network_enabled": False,
            "write_enabled": False,
            "terminal_enabled": False,
            "browser_enabled": False,
            "money_enabled": False,
            "running_sessions": running,
            "session_count": total,
        }

    def get_session(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return session.to_dict()

    def execute_read(self, *, mission_id: str, candidate_id: str, approval: ApprovalRecord) -> Dict[str, Any]:
        memory, candidate = self._candidate(mission_id, candidate_id)
        key = f"{candidate.mission_id}:{candidate.candidate_id}"
        with self._lock:
            existing_id = self._candidate_sessions.get(key)
            if existing_id:
                existing = self._sessions[existing_id]
                if existing.status in RUNNING_STATUSES:
                    return {"status": "already_running", "session": existing.to_dict()}
                return {"status": "already_completed", "session": existing.to_dict()}
            blocked = self._validate(memory, candidate, approval)
            if blocked:
                return {"status": "blocked", "blocked_reasons": blocked}
            exact_path = Path(candidate.scope[0]).expanduser().resolve()
            cwd = self._approved_cwd(candidate)
            session = HermesRuntimeSession(
                session_id=str(uuid4()),
                mission_id=mission_id,
                step_id=candidate.step_id,
                candidate_id=candidate.candidate_id,
                status="running",
                path_fingerprint=_fingerprint(str(exact_path)),
                started_at=self.clock(),
            )
            self._sessions[session.session_id] = session
            self._candidate_sessions[key] = session.session_id
            self._audit(memory, "hermes_runtime_started", candidate, session)

        guard = self._guard_factory(exact_path=exact_path, approved_cwd=cwd, session=session)
        adapter = self.adapter_factory(guard)
        session.adapter = adapter
        self._install_interrupt_delivery_callback(session, adapter)
        if session.interrupt_requested and not session.interrupt_delivered:
            self._request_interrupt(session, adapter, "operator stop")
        result_box: Dict[str, Any] = {}

        def worker() -> None:
            try:
                result_box["raw"] = adapter.run(
                    f"Use the read_file tool exactly once for this path: {exact_path}",
                    session_id=session.session_id,
                    task_id=session.session_id,
                )
            except Exception as exc:
                result_box["error"] = str(exc)
            finally:
                self._finish_session(memory, candidate, session, result_box)

        thread = threading.Thread(target=worker, name=f"mark3-hermes-{candidate.candidate_id}")
        session.worker = thread
        thread.start()
        timeout = int(candidate.timeout_seconds or 30)
        thread.join(timeout)
        if thread.is_alive():
            self._request_interrupt(session, adapter, "timeout")
            thread.join(INTERRUPT_GRACE_SECONDS)
            if thread.is_alive():
                return self._mark_cancellation_pending(session, "timeout_interrupt_pending")
        return self._finish_session(memory, candidate, session, result_box)

    def stop(self, session_id: str, *, reason: str = "operator stop") -> Dict[str, Any]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None and session.ended_at:
                return session.to_dict()
        if session is None:
            raise KeyError(session_id)
        self._wait_for_worker_assignment(session)
        with self._lock:
            if session.ended_at:
                return session.to_dict()
        self._request_interrupt(session, session.adapter, reason)
        if session.worker is None:
            return self._mark_cancellation_pending(session, "cancellation_pending")["session"]
        if session.worker and session.worker.is_alive():
            session.worker.join(INTERRUPT_GRACE_SECONDS)
        if session.worker and session.worker.is_alive():
            return self._mark_cancellation_pending(session, "cancellation_pending")["session"]
        if session.interrupt_requested and not session.ended_at:
            return self._mark_cancellation_pending(session, "cancellation_pending")["session"]
        return self.get_session(session_id)

    def _finish_session(
        self,
        memory: Any,
        candidate: ExecutionCandidate,
        session: HermesRuntimeSession,
        result_box: Dict[str, Any],
    ) -> Dict[str, Any]:
        wait_for_finalizer = False
        with self._lock:
            if session.ended_at:
                return {"status": session.status, "session": session.to_dict()}
            if session.finalizing:
                wait_for_finalizer = True
            else:
                session.finalizing = True
                session.worker_alive = False
        if wait_for_finalizer:
            return self._wait_for_finalized(session)
        raw = result_box.get("raw")
        duration = _duration(session.started_at)
        classification = self._classify_read_file_execution(raw, result_box.get("error"), session, candidate)
        safe_raw = _safe_result(raw)
        summary = f"Hermes read_file {classification.status}"
        values = {
            "step_id": candidate.step_id,
            "summary": summary,
            "verification_state": classification.evidence_state,
            "step_status": classification.step_status,
            "status_reason": "" if classification.status == "success" else (classification.error or classification.status),
            "time_known_seconds": duration,
            "evidence": [{
                "source_type": "test_adapter_observation" if classification.evidence_state == VerificationState.VERIFIED.value else "internal_observation",
                "description": "Hermes runtime read_file attempt observed.",
                "verification_state": classification.evidence_state,
                "safe_hash_reference": "sha256:" + hashlib.sha256(json.dumps({
                    "tool": ALLOWED_TOOL,
                    "path_fingerprint": session.path_fingerprint,
                    "result": safe_raw,
                    "error": classification.error,
                    "duration": duration,
                    "interrupted": session.interrupted or session.interrupt_requested,
                }, sort_keys=True, default=str).encode()).hexdigest(),
                "limitations": ["content not stored as evidence"],
                "supported_claim": summary,
            }],
        }
        try:
            mission = self.mission_loop.record_outcome(candidate.mission_id, values)
            session.outcome = {"status": classification.status, "mission_status": mission["status"], "raw_result": safe_raw}
        except Exception as exc:
            session.outcome = {"status": classification.status, "record_outcome_error": str(exc), "raw_result": safe_raw}
        session.status = classification.status
        session.error = classification.error
        session.ended_at = self.clock()
        self._audit(memory, "hermes_runtime_finished", candidate, session, {"outcome_status": classification.status, "error": classification.error})
        return {"status": session.status, "session": session.to_dict()}

    def _wait_for_worker_assignment(self, session: HermesRuntimeSession) -> None:
        deadline = time.monotonic() + INTERRUPT_GRACE_SECONDS
        while session.worker is None and not session.ended_at and time.monotonic() < deadline:
            time.sleep(0.01)

    def _wait_for_finalized(self, session: HermesRuntimeSession) -> Dict[str, Any]:
        deadline = time.monotonic() + INTERRUPT_GRACE_SECONDS
        while time.monotonic() < deadline:
            if session.ended_at:
                break
            time.sleep(0.01)
        return {"status": session.status, "session": session.to_dict()}

    def _mark_cancellation_pending(self, session: HermesRuntimeSession, status: str) -> Dict[str, Any]:
        with self._lock:
            if session.ended_at:
                return {"status": session.status, "session": session.to_dict()}
            session.status = status
            session.worker_alive = True
            session.interrupt_requested = True
            session.forced_cancellation_available = False
            session.outcome = {
                "status": status,
                "worker_alive": True,
                "forced_cancellation_available": False,
                "note": "Cancellation is cooperative; the worker has not confirmed stop yet.",
            }
            return {"status": status, "session": session.to_dict()}

    def _request_interrupt(self, session: HermesRuntimeSession, adapter: Any, reason: str) -> None:
        should_deliver = False
        with self._lock:
            if session.ended_at:
                return
            if session.interrupt_delivered:
                return
            session.interrupt_requested = True
            session.interrupted = True
            should_deliver = adapter is not None
        if should_deliver and self._interrupt(adapter, reason):
            self._mark_interrupt_delivered(session)

    def _mark_interrupt_delivered(self, session: HermesRuntimeSession) -> None:
        with self._lock:
            if session.ended_at:
                return
            if session.interrupt_requested:
                session.interrupt_delivered = True

    def _install_interrupt_delivery_callback(self, session: HermesRuntimeSession, adapter: Any) -> None:
        setter = getattr(adapter, "set_interrupt_delivery_callback", None)
        if not callable(setter):
            return
        setter(lambda: self._mark_interrupt_delivered(session))

    def _validate(self, memory: Any, candidate: ExecutionCandidate, approval: ApprovalRecord) -> list[str]:
        blocked: list[str] = []
        step = next((item for item in memory.plan if item.step_id == candidate.step_id), None)
        if step is None:
            blocked.append("candidate step not found")
            return blocked
        if memory.status != MissionLoopStatus.EXECUTION_CANDIDATE_READY:
            blocked.append(f"mission status is {memory.status.value}")
        if candidate.mission_id != memory.intake.mission_id or candidate.step_id != step.step_id:
            blocked.append("candidate mission or step mismatch")
        if not candidate.eligibility:
            blocked.append("candidate is not eligible")
        if candidate.tool_candidate != ALLOWED_TOOL:
            blocked.append("tool must be read_file")
        if candidate.exact_action != ALLOWED_ACTION:
            blocked.append("action must be filesystem_read")
        if candidate.adapter_capability != ALLOWED_CAPABILITY:
            blocked.append("capability must be hermes.file.read")
        if candidate.risk_level not in {0, 1, 2}:
            blocked.append("risk level is not allowed for this pilot")
        if not candidate.approval_satisfied:
            blocked.append("candidate approval is not satisfied")
        blocked.extend(self._validate_approval(candidate, step, approval))
        blocked.extend(self._validate_scope(candidate, memory))
        if self._backend(candidate) != ALLOWED_BACKEND:
            blocked.append("backend must be local")
        timeout = candidate.timeout_seconds
        if not isinstance(timeout, int) or timeout < 1 or timeout > 300:
            blocked.append("timeout must be an integer between 1 and 300 seconds")
        return list(dict.fromkeys(blocked))

    def _validate_approval(self, candidate: ExecutionCandidate, step: Any, approval: ApprovalRecord) -> list[str]:
        blocked: list[str] = []
        if approval is None:
            return ["approval record is required"]
        bound_approval_id = candidate.approval_requirement.get("approval_id") or getattr(step, "approval_id", None)
        if not bound_approval_id or approval.approval_id != bound_approval_id:
            blocked.append("approval is not bound to candidate")
        if approval.status != ApprovalStatus.APPROVED:
            blocked.append(f"approval status is {approval.status.value}")
        try:
            if datetime.now(timezone.utc) >= datetime.fromisoformat(approval.expires_at):
                blocked.append("approval expired")
        except ValueError:
            blocked.append("approval expiration is invalid")
        if approval.action_type != ALLOWED_ACTION:
            blocked.append("approval action mismatch")
        if approval.context_fingerprint != candidate.context_fingerprint:
            blocked.append("approval fingerprint mismatch")
        return blocked

    def _validate_scope(self, candidate: ExecutionCandidate, memory: Any) -> list[str]:
        blocked: list[str] = []
        if len(candidate.scope) != 1:
            return ["scope must contain one exact file path"]
        try:
            path = Path(candidate.scope[0]).expanduser()
            resolved = path.resolve()
            cwd = self._approved_cwd(candidate)
        except (OSError, ValueError) as exc:
            return [f"path cannot be resolved: {exc}"]
        if path.name in BLOCKED_NAMES or any(marker in path.name.lower() for marker in SECRET_MARKERS):
            blocked.append("path targets a blocked secret-like file")
        if resolved.is_dir():
            blocked.append("directories are not supported")
        if not resolved.is_file():
            blocked.append("path must be an existing regular file")
        if path.is_symlink():
            blocked.append("symlink paths are blocked")
        if str(resolved).startswith("/dev/") or "/proc/" in str(resolved):
            blocked.append("device and proc paths are blocked")
        try:
            resolved.relative_to(cwd)
        except ValueError:
            blocked.append("path escapes approved cwd")
        allowed = {str(Path(item).expanduser().resolve()) for item in memory.intake.allowed_paths_resources}
        if allowed and str(resolved) not in allowed:
            blocked.append("path is not in mission allowed_paths_resources")
        return blocked

    def _guard_factory(self, *, exact_path: Path, approved_cwd: Path, session: HermesRuntimeSession) -> Callable[[str, Dict[str, Any]], Any]:
        def guard(tool_name: str, args: Dict[str, Any]) -> Any:
            path_arg = args.get("path")
            canonical = Path(str(path_arg or "")).expanduser().resolve()
            effective_cwd = Path(str(args.get("cwd") or approved_cwd)).expanduser().resolve()
            backend = self._backend_from_args(args)
            event = {
                "tool_name": tool_name,
                "path_fingerprint": _fingerprint(str(canonical)),
                "backend": backend,
                "effective_cwd": str(effective_cwd),
                "guard_allowed": False,
                "guard_error": None,
            }
            session.tool_calls.append(event)
            if tool_name != ALLOWED_TOOL:
                event["guard_error"] = "only read_file is allowed"
                return "only read_file is allowed"
            if canonical != exact_path:
                event["guard_error"] = "read_file path does not match approved exact path"
                return "read_file path does not match approved exact path"
            if effective_cwd != approved_cwd:
                event["guard_error"] = "effective cwd does not match approved cwd"
                return "effective cwd does not match approved cwd"
            if backend != ALLOWED_BACKEND:
                event["guard_error"] = "backend must be local"
                return "backend must be local"
            event["guard_allowed"] = True
            return True
        return guard

    def _candidate(self, mission_id: str, candidate_id: str) -> tuple[Any, ExecutionCandidate]:
        memory = self.mission_loop._missions[mission_id]
        candidate = next((item for item in memory.candidates if item.candidate_id == candidate_id), None)
        if candidate is None:
            raise KeyError(candidate_id)
        return memory, candidate

    def _audit(
        self,
        memory: Any,
        event_type: str,
        candidate: ExecutionCandidate,
        session: HermesRuntimeSession,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        metadata = {
            "step_id": candidate.step_id,
            "candidate_id": candidate.candidate_id,
            "tool": ALLOWED_TOOL,
            "path_fingerprint": session.path_fingerprint,
            "session_id": session.session_id,
            **(extra or {}),
        }
        self.mission_loop._audit(memory, event_type, event_type.replace("_", " "), metadata)

    def _default_adapter_factory(self, guard: Callable[[str, Dict[str, Any]], Any]) -> HermesRuntimeAdapter:
        return HermesRuntimeAdapter(HermesAdapterConfig(
            max_iterations=3,
            enabled_toolsets=["file"],
            disabled_toolsets=["web", "terminal", "browser", "memory", "todo", "mcp"],
            allowed_tools=[ALLOWED_TOOL],
            tool_guard=guard,
            skip_context_files=True,
            skip_memory=True,
            governed_mode=True,
            disable_memory_provider_tools=True,
            disable_context_engine=True,
            disable_plugins=True,
            disable_delegate_task=True,
            disable_mcp=True,
        ))

    def _approved_cwd(self, candidate: ExecutionCandidate) -> Path:
        raw = candidate.approval_requirement.get("cwd") or os.getcwd()
        return Path(str(raw)).expanduser().resolve()

    def _backend(self, candidate: ExecutionCandidate) -> str:
        return str(candidate.approval_requirement.get("backend") or ALLOWED_BACKEND)

    def _backend_from_args(self, args: Dict[str, Any]) -> str:
        return str(args.get("backend") or ALLOWED_BACKEND)

    def _interrupt(self, adapter: Any, reason: str) -> bool:
        agent = getattr(adapter, "last_agent", None)
        if agent and hasattr(agent, "interrupt"):
            agent.interrupt(reason)
            return True
        if hasattr(adapter, "interrupt"):
            return adapter.interrupt(reason) is not False
        return False

    def _classify_read_file_execution(
        self,
        raw: Any,
        error: Optional[str],
        session: HermesRuntimeSession,
        candidate: ExecutionCandidate,
    ) -> ExecutionClassification:
        if session.interrupted or session.interrupt_requested:
            return ExecutionClassification("stopped", "stopped", VerificationState.OBSERVED.value, error, False)
        if error:
            return ExecutionClassification("failed", "failed", VerificationState.REJECTED.value, error, False)
        if raw is None:
            return ExecutionClassification("unknown", "failed", VerificationState.UNKNOWN.value, "approved read_file was not successfully observed", False)

        exact_call_observed = self._observed_exact_call(session, candidate)
        tool_result_error = _read_file_tool_result_error(raw)
        raw_error = _raw_result_error(raw)
        if exact_call_observed and not tool_result_error and not raw_error:
            return ExecutionClassification("success", "completed", VerificationState.VERIFIED.value, None, True)

        classification_error = (
            tool_result_error
            or raw_error
            or "approved read_file was not successfully observed"
        )
        return ExecutionClassification("failed", "failed", VerificationState.REJECTED.value, classification_error, False)

    def _observed_exact_call(self, session: HermesRuntimeSession, candidate: ExecutionCandidate) -> bool:
        try:
            expected = _fingerprint(str(Path(candidate.scope[0]).expanduser().resolve()))
            approved_cwd = str(self._approved_cwd(candidate))
        except (OSError, ValueError):
            return False
        return (
            len(session.tool_calls) == 1
            and session.tool_calls[0].get("tool_name") == ALLOWED_TOOL
            and session.tool_calls[0].get("path_fingerprint") == expected
            and session.tool_calls[0].get("effective_cwd") == approved_cwd
            and session.tool_calls[0].get("backend") == ALLOWED_BACKEND
            and session.tool_calls[0].get("guard_allowed") is True
            and not session.tool_calls[0].get("guard_error")
        )


def _fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _raw_result_error(raw: Any) -> Optional[str]:
    if not isinstance(raw, dict):
        return None
    if raw.get("success") is False:
        return str(raw.get("error") or "Hermes adapter reported failure")
    if raw.get("completed") is False:
        return str(raw.get("error") or "Hermes conversation did not complete")
    if raw.get("partial") is True:
        return str(raw.get("error") or "Hermes conversation returned a partial result")
    if raw.get("interrupted") is True:
        return "Hermes conversation was interrupted"
    error = raw.get("error")
    if error:
        return str(error)
    return None


def _read_file_tool_result_error(raw: Any) -> Optional[str]:
    if not _is_conversation_result(raw):
        return None
    messages = raw.get("messages")
    if not isinstance(messages, list) or not messages:
        return "approved read_file was not successfully observed"

    read_file_call_ids: set[str] = set()
    for message in messages:
        if not isinstance(message, dict):
            continue
        for tool_call in message.get("tool_calls") or []:
            call_id, name = _tool_call_id_and_name(tool_call)
            if name == ALLOWED_TOOL and call_id:
                read_file_call_ids.add(call_id)

    if not read_file_call_ids:
        return "approved read_file was not successfully observed"

    saw_result = False
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "tool":
            continue
        if message.get("tool_call_id") not in read_file_call_ids:
            continue
        saw_result = True
        content_error = _tool_content_error(message.get("content"))
        if content_error:
            return content_error

    if not saw_result:
        return "approved read_file tool result was not found"
    return None


def _is_conversation_result(raw: Any) -> bool:
    return isinstance(raw, dict) and any(
        key in raw for key in ("messages", "final_response", "completed", "api_calls")
    )


def _tool_call_id_and_name(tool_call: Any) -> tuple[Optional[str], Optional[str]]:
    if not isinstance(tool_call, dict):
        return None, None
    function = tool_call.get("function") if isinstance(tool_call.get("function"), dict) else {}
    return tool_call.get("id"), function.get("name")


def _tool_content_error(content: Any) -> Optional[str]:
    if isinstance(content, dict):
        data = content
    elif isinstance(content, str):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            lowered = content.lower()
            if "error" in lowered or "blocked" in lowered or "not allowed" in lowered:
                return content[:200]
            return None
    else:
        return "read_file tool result was empty"

    if not isinstance(data, dict):
        return None
    if data.get("success") is False:
        return str(data.get("error") or "read_file tool reported failure")
    if data.get("error"):
        return str(data.get("error"))
    if data.get("blocked_by"):
        return str(data.get("error") or data.get("blocked_by"))
    return None


_REDACTED_RESULT_KEYS = {
    "messages",
    "tool_calls",
    "function_call",
    "output",
    "outputs",
    "tool_output",
    "tool_outputs",
    "result",
    "raw",
}
_ALWAYS_REDACT_RESULT_KEYS = {"content", "text", "final_response"}
_MAX_SAFE_STRING = 200


def _safe_result(value: Any) -> Any:
    if isinstance(value, dict):
        safe: Dict[str, Any] = {}
        for key, val in value.items():
            key_text = str(key)
            if key_text in _ALWAYS_REDACT_RESULT_KEYS or (
                key_text in _REDACTED_RESULT_KEYS and not isinstance(val, (int, float, bool))
            ):
                safe[key_text] = _redacted_summary(val)
            else:
                safe[key_text] = _safe_result(val)
        return safe
    if isinstance(value, list):
        return {"type": "list", "count": len(value), "items": [_safe_result(item) for item in value[:5]]}
    if isinstance(value, tuple):
        return {"type": "tuple", "count": len(value), "items": [_safe_result(item) for item in value[:5]]}
    if isinstance(value, str):
        if len(value) > _MAX_SAFE_STRING:
            return {"redacted": True, "type": "string", "length": len(value)}
        return value
    return value


def _redacted_summary(value: Any) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"redacted": True}
    if isinstance(value, dict):
        summary.update({"type": "dict", "keys": sorted(str(key) for key in value.keys())})
    elif isinstance(value, (list, tuple)):
        summary.update({"type": type(value).__name__, "count": len(value)})
    elif isinstance(value, str):
        summary.update({"type": "string", "length": len(value)})
    elif value is None:
        summary.update({"type": "none"})
    else:
        summary.update({"type": type(value).__name__})
    return summary


def _duration(started_at: str) -> float:
    try:
        started = datetime.fromisoformat(started_at)
    except ValueError:
        return 0.0
    return max(0.0, time.time() - started.timestamp())
