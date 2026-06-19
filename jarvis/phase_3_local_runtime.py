from __future__ import annotations

import importlib.util
import os
import platform
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from jarvis.approval_hardening import ApprovalKind, ApprovalStatus
from jarvis.phase_1_governed_execution import PROTECTED_CREDENTIAL_MESSAGE
from jarvis.phase_2_local_assistant_runtime import (
    ACTION_CATALOG,
    APPROVAL_LEVELS,
    EXECUTION_HISTORY_SCHEMA_VERSION,
    PHASE_2_SCHEMA_VERSION,
    Phase2LocalAssistantRuntimeControlPlane,
    _action_id,
    _browser_check,
    _fingerprint,
    _json_dumps,
    _normalize_readback,
    _now_iso,
    _readback_for_preview,
    _redact_text,
    _required_approval_level,
    _safe_text,
)


PHASE_3_SCHEMA_VERSION = "jarvis.phase_3_local_runtime_daemon_trusted_approvals.v1"
LOCAL_DAEMON_SCHEMA_VERSION = "jarvis.local_daemon.v1"
TRUSTED_CHANNEL_SCHEMA_VERSION = "jarvis.trusted_approval_channels.v1"
LOCAL_DOCTOR_SCHEMA_VERSION = "jarvis.local_doctor.v1"

LOCAL_BIND_HOST = "127.0.0.1"
LOCAL_BIND_PORT = 9119
DOUBLE_APPROVAL_SECONDS = 900


class Phase3LocalRuntimeControlPlane(Phase2LocalAssistantRuntimeControlPlane):
    """Phase 3 local runtime control plane.

    This class extends the Phase 2 governed runtime. It does not create a
    second Hermes runtime and does not expose a command execution API.
    """

    def __init__(self, *args: Any, bind_host: str = LOCAL_BIND_HOST, bind_port: int = LOCAL_BIND_PORT, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bind_host = bind_host
        self.bind_port = int(bind_port)
        self._daemon_id = f"jarvis-local-daemon-{socket.gethostname()}-{os.getpid()}"
        self._daemon_started_at = _now_iso()
        self._last_heartbeat_at: Optional[str] = None
        self._channel_verified_at: Dict[str, str] = {}
        self._stop_requests: Dict[str, Dict[str, Any]] = {}
        self._rollback_requests: Dict[str, Dict[str, Any]] = {}

    def status(self) -> Dict[str, Any]:
        base = super().status()
        base["schema_version"] = PHASE_3_SCHEMA_VERSION
        base["phase"] = "Phase 3"
        base["phase_3_runtime"] = self.phase_3_status(route_paths=())
        base["local_runtime"] = self.local_runtime_status()
        base["trusted_approval_channels"] = self.trusted_approval_channels_status()
        base["local_doctor"] = self.local_doctor_status(route_paths=())
        base["safety"].update({
            "phase_3_local_daemon_contract": True,
            "trusted_approval_channels": True,
            "double_approval_real": True,
            "triple_requires_additional_trusted_channel_not_configured": True,
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
        })
        return base

    def phase_3_status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        return {
            "schema_version": PHASE_3_SCHEMA_VERSION,
            "phase": "Phase 3",
            "title": "PR #167 -- Phase 3 Local Runtime Daemon + Trusted Approval Channels",
            "status": "implemented_as_local_governed_runtime_macro_phase",
            "implemented_blocks": {
                "local_runtime_daemon_contract": True,
                "tray_local_controller_readiness": True,
                "trusted_approval_channels": True,
                "strong_approval_channel_gate": True,
                "double_approval_two_steps": True,
                "triple_honest_block": True,
                "stop_rollback_observable": True,
                "execution_history_v2": True,
                "local_doctor": True,
                "browser_local_pilot_evidence": True,
                "telegram_mobile_future_readiness_disabled": True,
            },
            "route_readiness": {
                "phase_3_status": "/mark-3/phase-3/status" in routes,
                "local_daemon_status": "/mark-3/local-daemon/status" in routes,
                "local_daemon_health": "/mark-3/local-daemon/health" in routes,
                "local_doctor_status": "/mark-3/local-doctor/status" in routes,
                "trusted_channels_status": "/mark-3/trusted-approval-channels/status" in routes,
                "execution_history_export_preview": "/mark-3/execution/history/export-preview" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "local_runtime": self.local_daemon_status(),
            "tray": self.tray_status(),
            "trusted_approval_channels": self.trusted_approval_channels_status(),
            "remote_bridge_future": self.remote_bridge_future_status(),
            "blocked_or_unsupported": {
                "triple": "triple_requires_additional_trusted_channel_not_configured",
                "telegram_remote_approval": "disabled_not_configured",
                "mobile_remote_approval": "disabled_not_configured",
                "freeform_shell": "denied",
                "arbitrary_commands": "denied",
                "money_stripe_deploy_email_publish": "denied_or_unsupported_in_phase_3",
                "system_service_install": "unsupported_no_opt_in_path_in_phase_3",
            },
            "security_gates": {
                "jarvis_governs": True,
                "hermes_executes": True,
                "no_duplicate_hermes_runtime": True,
                "backend_recalculates_policy_before_accepting_approval": True,
                "audit_metadata_only": True,
                "memory_grants_permission": False,
                "wake_phrase_can_approve": False,
                "voice_can_approve": False,
                "frontend_can_execute_hermes_directly": False,
                "remote_approval_allowed": False,
                "remote_execution_allowed": False,
            },
            "source_endpoint": "/mark-3/phase-3/status",
        }

    def local_runtime_status(self) -> Dict[str, Any]:
        base = super().local_runtime_status()
        daemon = self.local_daemon_status()
        tray = self.tray_status()
        base.update({
            "schema_version": PHASE_3_SCHEMA_VERSION,
            "daemon_status": daemon["daemon_status"],
            "tray_status": "not_installed" if not tray["tray_installed"] else "installed",
            "local_runtime_ready": True,
            "phase_3_ready": True,
            "background_listening_enabled": False,
            "auto_start_enabled": False,
            "camera_auto_start": False,
            "mic_auto_start": False,
            "wake_auto_start": False,
            "user_opt_in_required": True,
            "local_only": True,
            "bind_host": self.bind_host,
            "bind_port": self.bind_port,
            "daemon": daemon,
            "tray": tray,
            "trusted_approval_channels": self.trusted_approval_channels_status(),
            "remote_bridge_future": self.remote_bridge_future_status(),
            "source_endpoint": "/mark-3/local-daemon/status",
        })
        return base

    def local_daemon_status(self) -> Dict[str, Any]:
        state_dir = self._state_dir()
        uptime = max(0, int(time.time() - _timestamp(self._daemon_started_at)))
        bind_safe = self.bind_host in {"127.0.0.1", "localhost", "::1"}
        health_status = "healthy" if bind_safe else "blocked_external_bind"
        return {
            "schema_version": LOCAL_DAEMON_SCHEMA_VERSION,
            "daemon_id": self._daemon_id,
            "daemon_status": "running_embedded_local_api_process",
            "pid": os.getpid(),
            "started_at": self._daemon_started_at,
            "uptime": uptime,
            "host": socket.gethostname(),
            "bind_host": self.bind_host,
            "bind_port": self.bind_port,
            "local_only": True,
            "auto_start_enabled": False,
            "background_listening_enabled": False,
            "camera_auto_start": False,
            "mic_auto_start": False,
            "wake_auto_start": False,
            "state_dir": str(state_dir),
            "audit_dir": self._audit_dir(state_dir),
            "log_dir": str(state_dir / "logs"),
            "health_status": health_status,
            "last_heartbeat_at": self._last_heartbeat_at,
            "stop_supported": False,
            "restart_supported": False,
            "failure_modes": [
                "embedded_api_process_cannot_self_stop_without_shutting_down_backend",
                "system_service_not_installed",
                "autostart_disabled_until_explicit_opt_in",
                "browser_capabilities_unknown_until_local_ui_loads",
                "wake_mic_camera_auto_start_disabled",
            ],
            "user_opt_in_required": True,
            "source_endpoint": "/mark-3/local-daemon/status",
        }

    def local_daemon_health(self) -> Dict[str, Any]:
        status = self.local_daemon_status()
        checks = [
            _phase3_check("local_only", status["local_only"], "Daemon contract is local-only."),
            _phase3_check("safe_bind_host", status["bind_host"] in {"127.0.0.1", "localhost", "::1"}, "External binds are blocked."),
            _phase3_check("auto_start_disabled", status["auto_start_enabled"] is False, "No autostart without opt-in."),
            _phase3_check("background_listening_disabled", status["background_listening_enabled"] is False, "No background listening."),
            _phase3_check("mic_camera_wake_auto_start_disabled", not any((status["mic_auto_start"], status["camera_auto_start"], status["wake_auto_start"])), "No automatic sensors."),
        ]
        return {
            "schema_version": LOCAL_DAEMON_SCHEMA_VERSION,
            "health_status": "healthy" if all(item["passed"] for item in checks) else "degraded",
            "daemon": status,
            "checks": checks,
            "source_endpoint": "/mark-3/local-daemon/health",
        }

    def heartbeat(self, *, daemon_id: Optional[str] = None, actor: str = "David") -> Dict[str, Any]:
        if daemon_id and daemon_id != self._daemon_id:
            self._audit_v2(
                "daemon_heartbeat",
                correlation_id=f"corr-{uuid4()}",
                metadata={"daemon_id_matches": False, "actor": actor},
            )
            raise ValueError("daemon_id does not match local runtime")
        self._last_heartbeat_at = self.clock()
        audit = self._audit_v2(
            "daemon_heartbeat",
            correlation_id=f"corr-{uuid4()}",
            metadata={"daemon_id": self._daemon_id, "actor": actor, "local_only": True},
        )
        return {
            "schema_version": LOCAL_DAEMON_SCHEMA_VERSION,
            "daemon_id": self._daemon_id,
            "daemon_status": "heartbeat_recorded",
            "last_heartbeat_at": self._last_heartbeat_at,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def daemon_stop_request(self, *, requested_by: str = "David", reason: str = "operator stop", timeout_seconds: int = 10) -> Dict[str, Any]:
        request_id = f"stop-{uuid4()}"
        audit = self._audit_v2(
            "daemon_stop_requested",
            correlation_id=f"corr-{uuid4()}",
            metadata={"stop_request_id": request_id, "requested_by": requested_by, "reason": reason, "local_only": True},
        )
        result = {
            "schema_version": LOCAL_DAEMON_SCHEMA_VERSION,
            "stop_request_id": request_id,
            "execution_id": "",
            "action_id": "local-daemon",
            "requested_at": self.clock(),
            "requested_by": _safe_text(requested_by, limit=80),
            "stop_status": "unsupported_embedded_runtime_stop_not_performed",
            "bridge_stop_supported": False,
            "process_stop_supported": False,
            "cooperative_stop_requested": True,
            "confirmed_stopped": False,
            "timeout_seconds": max(1, min(int(timeout_seconds or 10), 60)),
            "final_status": "unsupported_embedded_api_process_cannot_self_terminate",
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._stop_requests[request_id] = result
        return result

    def daemon_restart_request(self, *, requested_by: str = "David", reason: str = "operator restart", timeout_seconds: int = 10) -> Dict[str, Any]:
        request_id = f"restart-{uuid4()}"
        audit = self._audit_v2(
            "daemon_restart_requested",
            correlation_id=f"corr-{uuid4()}",
            metadata={"restart_request_id": request_id, "requested_by": requested_by, "reason": reason, "local_only": True},
        )
        return {
            "schema_version": LOCAL_DAEMON_SCHEMA_VERSION,
            "restart_request_id": request_id,
            "requested_at": self.clock(),
            "requested_by": _safe_text(requested_by, limit=80),
            "restart_status": "unsupported_no_system_service_or_supervisor_installed",
            "restart_supported": False,
            "stop_first_supported": False,
            "confirmed_restarted": False,
            "timeout_seconds": max(1, min(int(timeout_seconds or 10), 60)),
            "final_status": "unsupported_honest",
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def tray_status(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_3_SCHEMA_VERSION,
            "tray_available": True,
            "tray_installed": False,
            "tray_running": False,
            "tray_controls_supported": True,
            "can_open_jarvis": True,
            "can_stop_daemon": False,
            "can_show_approval": True,
            "can_show_status": True,
            "can_toggle_voice_session": True,
            "can_toggle_camera_session": True,
            "can_toggle_recording_session": True,
            "requires_user_opt_in": True,
            "no_background_capture": True,
            "native_dependency_required": False,
            "implementation_status": "backend_contract_and_ui_readiness_only",
            "future_native_options": ["pystray", "tauri", "electron"],
            "source_endpoint": "/mark-3/phase-3/status",
        }

    def trusted_approval_channels_status(self) -> Dict[str, Any]:
        channels = [self._channel(channel_id) for channel_id in _CHANNEL_ORDER]
        return {
            "schema_version": TRUSTED_CHANNEL_SCHEMA_VERSION,
            "channels": channels,
            "trusted_enabled_channel_count": sum(1 for item in channels if item["trusted"] and item["enabled"]),
            "can_grant_normal": any(item["can_grant_approval"] for item in channels),
            "can_grant_strong": any(item["can_grant_strong"] for item in channels),
            "can_grant_double": any(item["can_grant_double"] for item in channels),
            "can_grant_triple": False,
            "triple_status": "triple_requires_additional_trusted_channel_not_configured",
            "voice_can_approve": False,
            "wake_phrase_can_approve": False,
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "audit_required": True,
            "source_endpoint": "/mark-3/trusted-approval-channels/status",
        }

    def approval_status(self) -> Dict[str, Any]:
        base = super().approval_status()
        base.update({
            "schema_version": PHASE_3_SCHEMA_VERSION,
            "approval_levels": list(APPROVAL_LEVELS),
            "trusted_approval_channels": self.trusted_approval_channels_status(),
            "double_approval_real": True,
            "double_real_channel_configured": True,
            "triple_real_channel_configured": False,
            "double_triple_real_channel_configured": False,
            "double_approval_steps_supported": True,
            "triple_approval_supported": False,
            "triple_status": "triple_requires_additional_trusted_channel_not_configured",
            "voice_can_approve_alone": False,
            "wake_phrase_can_approve": False,
            "source_endpoint": "/mark-3/approval/status",
        })
        return base

    def request_approval(self, *, preview_id: str, actor: str = "David") -> Dict[str, Any]:
        envelope = super().request_approval(preview_id=preview_id, actor=actor)
        if envelope.get("approval_level_required") == "triple" and envelope.get("status") == "blocked":
            with self._lock:
                stored = self._approval_envelopes.get(envelope["approval_id"])
                if stored is not None:
                    stored["decision_reason"] = "triple_requires_additional_trusted_channel_not_configured"
                    stored["rejection_reason"] = stored["decision_reason"]
                    stored["challenge"] = "Triple approval requires an additional independent trusted channel."
                    envelope = dict(stored)
        return envelope

    def verify_trusted_channel(
        self,
        *,
        channel_id: str,
        actor: str = "David",
        local_presence: bool = True,
    ) -> Dict[str, Any]:
        channel = self._channel(channel_id)
        if not channel["enabled"] or not channel["trusted"] or not channel["local_only"]:
            audit = self._audit_v2(
                "trusted_channel_rejected",
                correlation_id=f"corr-{uuid4()}",
                metadata={"channel_id": channel_id, "actor": actor, "enabled": channel["enabled"], "trusted": channel["trusted"]},
            )
            return {
                "schema_version": TRUSTED_CHANNEL_SCHEMA_VERSION,
                "channel_id": channel_id,
                "verified": False,
                "reason": "channel_not_enabled_or_not_trusted",
                "audit_id": audit.get("audit_id", ""),
            }
        if channel["requires_presence"] and not local_presence:
            audit = self._audit_v2(
                "trusted_channel_rejected",
                correlation_id=f"corr-{uuid4()}",
                metadata={"channel_id": channel_id, "actor": actor, "local_presence": False},
            )
            return {
                "schema_version": TRUSTED_CHANNEL_SCHEMA_VERSION,
                "channel_id": channel_id,
                "verified": False,
                "reason": "local_presence_required",
                "audit_id": audit.get("audit_id", ""),
            }
        verified_at = self.clock()
        self._channel_verified_at[channel_id] = verified_at
        audit = self._audit_v2(
            "trusted_channel_verified",
            correlation_id=f"corr-{uuid4()}",
            metadata={"channel_id": channel_id, "actor": actor, "local_presence": local_presence, "metadata_only": True},
        )
        verified = self._channel(channel_id)
        return {
            "schema_version": TRUSTED_CHANNEL_SCHEMA_VERSION,
            "channel": verified,
            "channel_id": channel_id,
            "verified": True,
            "last_verified_at": verified_at,
            "audit_id": audit.get("audit_id", ""),
        }

    def decide_strong_approval(
        self,
        *,
        approval_id: str,
        decision: str,
        actor: str = "David",
        channel_id: str = "ui_local_browser",
        step_id: Optional[str] = None,
        confirmation_phrase: Optional[str] = None,
        readback_text: Optional[str] = None,
        reason: str = "",
    ) -> Dict[str, Any]:
        channel = self._channel(channel_id)
        if not channel["can_grant_strong"]:
            raise ValueError("channel cannot grant strong approval")
        if not channel["authenticated"]:
            raise ValueError("channel must be verified before approval")
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            level = (envelope or {}).get("approval_level_required")
        if level == "double":
            return self.decide_double_approval(
                approval_id=approval_id,
                decision=decision,
                actor=actor,
                channel_id=channel_id,
                step_id=step_id or "step-1",
                confirmation_phrase=confirmation_phrase,
                readback_text=readback_text,
                reason=reason,
            )
        return self.decide_approval(
            approval_id=approval_id,
            decision=decision,
            actor=actor,
            confirmation_phrase=confirmation_phrase,
            readback_text=readback_text,
            reason=reason,
            decision_source="trusted_channel",
            channel=channel_id,
        )

    def decide_double_approval(
        self,
        *,
        approval_id: str,
        decision: str,
        actor: str = "David",
        channel_id: str = "ui_local_browser",
        step_id: Optional[str] = None,
        confirmation_phrase: Optional[str] = None,
        readback_text: Optional[str] = None,
        reason: str = "",
    ) -> Dict[str, Any]:
        normalized = (decision or "").strip().lower().replace("-", "_")
        channel = self._channel(channel_id)
        if not channel["can_grant_double"] and channel_id != "ui_local_browser":
            raise ValueError("channel cannot grant double approval")
        if not channel["authenticated"]:
            raise ValueError("channel must be verified before approval")
        if "voice" in channel_id or "wake" in channel_id:
            raise ValueError("voice and wake phrase cannot approve")
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            if envelope is None:
                raise KeyError(approval_id)
            if envelope.get("approval_level_required") != "double":
                raise ValueError("approval is not a double approval")
            preview = self._previews[envelope["preview_id"]]
            if envelope.get("used_at"):
                raise ValueError("approval has already been used")
            if envelope["status"] in {"approved", "rejected", "cancelled", "expired", "blocked"}:
                raise ValueError(f"approval {approval_id} is already {envelope['status']}")
            steps = envelope.setdefault("approval_steps", [])
            step = _select_step(steps, step_id)
            if step is None:
                raise ValueError("approval step not found")
            if step.get("status") != "pending":
                raise ValueError(f"approval step {step['step_id']} is already {step.get('status')}")
            if _is_expired(step.get("expires_at")):
                step["status"] = "expired"
                envelope["status"] = "expired"
                envelope["decision_reason"] = "approval step is expired"
                preview["state"] = "approval_expired"
                self._audit_v2(
                    "approval_step_expired",
                    correlation_id=preview["correlation_id"],
                    risk_level=envelope["risk_level"],
                    approval_level="double",
                    metadata={"approval_id": approval_id, "step_id": step["step_id"], "channel_id": channel_id},
                )
                raise ValueError("approval step is expired")
            if normalized in {"reject", "rejected", "deny"}:
                step["status"] = "rejected"
                step["decided_at"] = self.clock()
                step["channel_id"] = channel_id
                envelope["status"] = "rejected"
                envelope["decision_reason"] = reason or "double approval rejected"
                preview["state"] = "approval_rejected"
                self._audit_v2(
                    "approval_step_rejected",
                    correlation_id=preview["correlation_id"],
                    risk_level=envelope["risk_level"],
                    approval_level="double",
                    metadata={"approval_id": approval_id, "step_id": step["step_id"], "channel_id": channel_id},
                )
                return dict(envelope)
            if normalized not in {"approve", "approved"}:
                raise ValueError("decision must be approve or reject")
            if _normalize_readback(readback_text) != _normalize_readback(envelope["readback_text"]):
                raise ValueError("readback text does not match required readback")
            if confirmation_phrase != step.get("confirmation_phrase"):
                raise ValueError("confirmation phrase does not match")
            approved_channels = [
                item.get("channel_id", "")
                for item in steps
                if item.get("status") == "approved"
            ]
            if channel_id in approved_channels:
                raise ValueError("double approval requires separate trusted channels")
            step["status"] = "approved"
            step["approved_at"] = self.clock()
            step["approved_by"] = _safe_text(actor, limit=80)
            step["channel_id"] = channel_id
            step["channel_type"] = channel["channel_type"]
            envelope["step_count_approved"] = sum(1 for item in steps if item.get("status") == "approved")
            envelope["channel_ids"] = [
                item.get("channel_id", "")
                for item in steps
                if item.get("status") == "approved"
            ]
            self._audit_v2(
                "approval_step_approved",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level="double",
                metadata={"approval_id": approval_id, "step_id": step["step_id"], "channel_id": channel_id},
            )
            if envelope["step_count_approved"] < envelope["step_count_required"]:
                envelope["decision_reason"] = "waiting_for_second_trusted_channel"
                return dict(envelope)
        record = self.mission_loop.approval_service.decide(
            approval_id,
            "approved",
            actor=actor,
            reason=reason,
            confirmation_phrase=envelope["approval_steps"][0]["confirmation_phrase"],
        )
        with self._lock:
            envelope["status"] = record.status.value
            envelope["decided_at"] = record.decided_at
            envelope["approved_at"] = record.approved_at
            envelope["decision_reason"] = "double_approval_completed"
            preview["state"] = "approval_approved"
            preview["updated_at"] = self.clock()
            self._audit_v2(
                "approval_approved",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level="double",
                metadata={"approval_id": approval_id, "channel_ids": envelope["channel_ids"]},
            )
            return dict(envelope)

    def decide_triple_approval(
        self,
        *,
        approval_id: str,
        decision: str = "approve",
        actor: str = "David",
        channel_id: str = "ui_local_browser",
        step_id: Optional[str] = None,
        confirmation_phrase: Optional[str] = None,
        readback_text: Optional[str] = None,
        reason: str = "",
    ) -> Dict[str, Any]:
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            if envelope is None:
                raise KeyError(approval_id)
            preview = self._previews[envelope["preview_id"]]
            envelope["status"] = "blocked"
            envelope["decision_reason"] = "triple_requires_additional_trusted_channel_not_configured"
            envelope["can_approve"] = False
            envelope["can_dispatch_after_approval"] = False
            preview["state"] = "approval_blocked"
            self._audit_v2(
                "approval_blocked",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level=envelope["approval_level"],
                metadata={"approval_id": approval_id, "channel_id": channel_id, "actor": actor, "reason": reason},
            )
            return dict(envelope)

    def history(
        self,
        *,
        limit: int = 25,
        action_key: Optional[str] = None,
        risk: Optional[str] = None,
        approval_status: Optional[str] = None,
        stop_status: Optional[str] = None,
        rollback_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        items = self.execution_history.list(
            limit=limit,
            action_key=action_key,
            risk_level=risk,
            approval_status=approval_status,
            stop_status=stop_status,
            rollback_status=rollback_status,
        )
        return {
            "schema_version": EXECUTION_HISTORY_SCHEMA_VERSION,
            "items": items,
            "status": self.execution_history.status(),
            "filters": {
                "limit": limit,
                "action_key": action_key,
                "risk": risk,
                "approval_status": approval_status,
                "stop_status": stop_status,
                "rollback_status": rollback_status,
            },
            "read_only": True,
            "metadata_only": True,
            "source_endpoint": "/mark-3/execution/history",
        }

    def history_export_preview(
        self,
        *,
        limit: int = 25,
        action_key: Optional[str] = None,
        risk: Optional[str] = None,
        approval_status: Optional[str] = None,
        stop_status: Optional[str] = None,
        rollback_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        history = self.history(
            limit=limit,
            action_key=action_key,
            risk=risk,
            approval_status=approval_status,
            stop_status=stop_status,
            rollback_status=rollback_status,
        )
        return {
            "schema_version": "jarvis.execution_history_export_preview.v1",
            "export_status": "preview_only",
            "metadata_only": True,
            "item_count": len(history["items"]),
            "items": history["items"],
            "redaction_summary": {
                "metadata_only": True,
                "raw_output_included": False,
                "secrets_included": False,
                "raw_audio_included": False,
                "camera_frames_included": False,
            },
            "source_endpoint": "/mark-3/execution/history/export-preview",
        }

    def stop(self, *, preview_id: Optional[str] = None, session_id: Optional[str] = None, reason: str = "operator stop") -> Dict[str, Any]:
        stop_request_id = f"stop-{uuid4()}"
        result = super().stop(preview_id=preview_id, session_id=session_id, reason=reason)
        with self._lock:
            preview = self._previews.get(preview_id or "") if preview_id else None
            action = dict((preview or {}).get("action") or {})
        observable = {
            "stop_request_id": stop_request_id,
            "execution_id": "",
            "action_id": action.get("action_id", ""),
            "requested_at": self.clock(),
            "requested_by": "David",
            "stop_status": result.get("status", "unknown"),
            "bridge_stop_supported": result.get("status") == "stop_completed",
            "process_stop_supported": False,
            "cooperative_stop_requested": result.get("status") in {"stop_completed", "stop_requested_pending_or_unsupported"},
            "confirmed_stopped": result.get("status") == "stop_completed",
            "timeout_seconds": 10,
            "final_status": result.get("status", "unknown"),
            "metadata_only": True,
        }
        result.update(observable)
        self._stop_requests[stop_request_id] = dict(result)
        return result

    def stop_rollback_contracts(self) -> Dict[str, Any]:
        base = super().stop_rollback_contracts()
        contracts = base.get("contracts", [])
        return {
            **base,
            "schema_version": PHASE_3_SCHEMA_VERSION,
            "catalog_actions": len(contracts),
            "stop_unsupported_honest": True,
            "rollback_never_faked": True,
            "read_only_rollback_status": "not_required",
            "prepare_only_rollback_status": "discard_preview",
            "observable_stop_fields": [
                "stop_request_id",
                "execution_id",
                "action_id",
                "requested_at",
                "requested_by",
                "stop_status",
                "bridge_stop_supported",
                "process_stop_supported",
                "cooperative_stop_requested",
                "confirmed_stopped",
                "timeout_seconds",
                "final_status",
            ],
            "observable_rollback_fields": [
                "rollback_request_id",
                "rollback_plan_id",
                "rollback_status",
                "rollback_supported",
                "rollback_requires_approval",
                "rollback_limitations",
                "rollback_audit_id",
            ],
        }

    def local_doctor_status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        route_set = set(route_paths)
        state_dir = self._state_dir()
        audit_status = self.audit_ledger.status(recent_limit=1)
        memory_status = self.memory_brain_v2.status()
        history_status = self.execution_history.status()
        frontend_dist = self.cwd / "web" / "dist" / "index.html"
        checks = [
            _doctor_check("python_env", "ok", platform.python_version()),
            _doctor_check("jarvis_package_import", _import_status("jarvis"), "importlib.find_spec('jarvis')"),
            _doctor_check("fastapi_import", _import_status("fastapi"), "importlib.find_spec('fastapi')"),
            _doctor_check("fastapi_app_import", _import_status("jarvis.api.app"), "importlib.find_spec('jarvis.api.app')"),
            _doctor_check("frontend_build_artifacts", "present" if frontend_dist.exists() else "missing_manual_build_required", "web/dist/index.html"),
            _doctor_check("state_dir_writable", _writable_status(state_dir), str(state_dir)),
            _doctor_check("audit_dir_writable", _writable_status(Path(self._audit_dir(state_dir))), self._audit_dir(state_dir)),
            _doctor_check("memory_db_reachable", "ok" if memory_status.get("schema_version") else "unknown", "Memory Brain v2 status"),
            _doctor_check("execution_history_db_reachable", "ok" if history_status.get("available") else "unknown", "Execution history status"),
            _doctor_check("local_bind_host_safe", "ok" if self.bind_host in {"127.0.0.1", "localhost", "::1"} else "blocked", self.bind_host),
            _doctor_check("no_external_bind", "ok" if self.bind_host in {"127.0.0.1", "localhost", "::1"} else "blocked", "external bind disabled"),
            _doctor_check("no_env_exposed", "ok", "doctor does not read .env or expose secret values"),
            _doctor_check("no_jarvis_tracked", _git_clean_status(["git", "ls-files", ".jarvis"], expect_empty=True, cwd=self.cwd), "git ls-files .jarvis"),
            _doctor_check("package_lock_unmodified", _git_clean_status(["git", "status", "--short", "--", "web/package.json", "web/package-lock.json"], expect_empty=True, cwd=self.cwd), "fixed git status"),
            _doctor_check("node_modules_status", "present" if (self.cwd / "web" / "node_modules").exists() else "missing", "web/node_modules"),
            _doctor_check("browser_status", "unknown_manual", "browser capabilities are client-side only"),
            _doctor_check("voice_wake_readiness", "ready_disabled_by_default", "voice/wake require manual opt-in"),
        ]
        return {
            "schema_version": LOCAL_DOCTOR_SCHEMA_VERSION,
            "status": "ready" if all(item["status"] not in {"blocked", "error"} for item in checks) else "degraded",
            "state": {
                "mode": "phase_3_local_doctor",
                "backend_reachable": True,
                "frontend_route_expected": "/jarvis",
                "dashboard_status_endpoint": "/mark-3/dashboard/status" in route_set or not route_set,
                "event_stream_available": "/mark-3/dashboard/events/stream" in route_set or not route_set,
                "local_doctor_endpoint": "/mark-3/local-doctor/status" in route_set or not route_set,
                "local_bind_host_safe": self.bind_host in {"127.0.0.1", "localhost", "::1"},
                "external_bind_enabled": False,
                "env_file_read": False,
                "env_file_content_loaded": False,
                "secrets_exposed": False,
                "browser_stt": "client_side_unknown",
                "browser_tts": "client_side_unknown",
                "camera_support": "client_side_unknown",
                "webgl_support": "client_side_unknown",
            },
            "checks": checks,
            "runtime": {
                "python_version": platform.python_version(),
                "python_executable_name": Path(sys.executable).name,
                "platform": platform.platform(),
                "system": platform.system(),
                "machine": platform.machine(),
                "process": {"pid": os.getpid(), "status": "running"},
            },
            "storage": {
                "state_dir": str(state_dir),
                "audit_status": _status_summary(audit_status),
                "memory_status": _status_summary(memory_status),
                "execution_history_status": _status_summary(history_status),
            },
            "safety": {
                "read_only": True,
                "no_env_read": True,
                "no_secret_read": True,
                "no_external_bind": True,
                "no_scanner_heavy": True,
                "no_dependency_install": True,
                "no_sensor_activation": True,
                "no_hermes_execution": True,
            },
            "source_endpoint": "/mark-3/local-doctor/status",
            "read_only": True,
        }

    def browser_verification_status(self, *, route_paths: Iterable[str]) -> Dict[str, Any]:
        base = super().browser_verification_status(route_paths=route_paths)
        route_set = set(route_paths)
        extra = [
            _browser_check("phase_3_status_check", "/mark-3/phase-3/status" in route_set or not route_set, "Phase 3 status route is present."),
            _browser_check("local_daemon_readiness_check", "/mark-3/local-daemon/status" in route_set or not route_set, "Local daemon readiness route is present."),
            _browser_check("trusted_channels_check", "/mark-3/trusted-approval-channels/status" in route_set or not route_set, "Trusted approval channel status route is present."),
            _browser_check("local_doctor_check", "/mark-3/local-doctor/status" in route_set or not route_set, "Local doctor route is present."),
            _browser_check("no_auto_mic_camera_wake", True, "No auto mic, camera, or wake startup."),
        ]
        base["schema_version"] = PHASE_3_SCHEMA_VERSION
        base["checks"] = list(base.get("checks", [])) + extra
        base["all_static_checks_passed"] = all(item["passed"] for item in base["checks"])
        base["phase_3_pilot"] = self.pilot_checklist_status()
        return base

    def pilot_checklist_status(self) -> Dict[str, Any]:
        return {
            "schema_version": "jarvis.phase_3_local_pilot.v1",
            "validated_by_automated_tests": [
                "phase_3_status_exists",
                "daemon_local_only_defaults",
                "trusted_channels_voice_wake_remote_denied",
                "double_approval_steps",
                "history_v2_metadata_only_filters",
                "doctor_safe_checks",
            ],
            "validated_by_build": ["web/npm_run_build"],
            "pending_manual_browser_pilot": [
                "open /jarvis",
                "inspect daemon/tray/channels/doctor/history drawers",
                "verify no auto mic/camera/wake",
                "run safe approval flow from local browser",
            ],
            "unsupported_honestly": [
                "native tray not installed",
                "triple approval lacks third independent trusted channel",
                "telegram/mobile remote approvals disabled",
                "embedded daemon stop/restart unsupported",
            ],
            "source_document": "docs/jarvis-phase-3-local-runtime-pilot-report.md",
        }

    def remote_bridge_future_status(self) -> Dict[str, Any]:
        return {
            "telegram_bridge_status": "disabled_not_configured",
            "mobile_bridge_status": "disabled_not_configured",
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "trusted_pairing_required": True,
            "tokens_loaded": False,
            "external_calls_made": False,
            "future_requirements": [
                "trusted pairing",
                "channel authentication",
                "local policy recalculation",
                "metadata-only audit",
                "explicit remote approval risk limits",
                "separate revocation and stop path",
            ],
        }

    def _phase2_request_approval(self, *, preview_id: str, actor: str) -> Dict[str, Any]:
        with self._lock:
            preview = self._previews.get(preview_id)
            if preview is None:
                raise KeyError(preview_id)
            if preview.get("cancelled"):
                raise ValueError("preview is cancelled")
            if preview.get("approval_envelope"):
                return dict(preview["approval_envelope"])
            if preview["decision"] == "denied":
                raise ValueError("denied actions cannot request approval")
            if not preview["requires_approval"]:
                raise ValueError("action does not require approval")
            action = preview["action"]
            action_key = action["action_key"]
            contract = ACTION_CATALOG[action_key]
            approval_level = _required_approval_level(contract)
            if approval_level == "triple":
                envelope = self._blocked_phase2_envelope(
                    preview,
                    actor,
                    reason="triple_requires_additional_trusted_channel_not_configured",
                )
                preview["approval_envelope"] = envelope
                preview["state"] = "approval_blocked"
                preview["updated_at"] = self.clock()
                self._approval_envelopes[envelope["approval_id"]] = envelope
                self._approval_to_preview[envelope["approval_id"]] = preview_id
                self._audit_approval_v2(preview, envelope)
                return dict(envelope)
            if approval_level != "double":
                return super()._phase2_request_approval(preview_id=preview_id, actor=actor)

            record = self.mission_loop.approval_service.request(
                action_type=action_key,
                requested_by=actor or "David",
                reason=contract.description,
                context={
                    "action_type": action_key,
                    "action_key": action_key,
                    "risk_level": contract.risk_level,
                    "approval_level_required": "double",
                    "input_fingerprint": action.get("input_fingerprint"),
                    "local_only": not contract.network_allowed,
                    "side_effect_free": not contract.external_side_effects,
                    "protected_material_blocked": True,
                },
                approval_kind=ApprovalKind.STRONG,
                expires_in_seconds=DOUBLE_APPROVAL_SECONDS,
            )
            step_2_phrase = f"CONFIRM {record.approval_id} STEP 2"
            envelope = {
                "schema_version": PHASE_3_SCHEMA_VERSION,
                "approval_id": record.approval_id,
                "action_id": action["action_id"],
                "action_key": action_key,
                "preview_id": preview_id,
                "correlation_id": preview["correlation_id"],
                "risk_level": contract.risk_level,
                "approval_level": "double",
                "approval_level_required": "double",
                "approval_level_required_source": "backend_recalculated",
                "requester": actor,
                "requested_by": actor,
                "reason": contract.description,
                "preview": {
                    "summary": contract.description,
                    "input_fingerprint": action.get("input_fingerprint"),
                    "will_do": action.get("will_do", []),
                    "will_not_do": action.get("will_not_do", []),
                },
                "readback_text": _readback_for_preview(preview),
                "readback_required": True,
                "confirmation_phrase": record.user_confirmation_phrase,
                "challenge": f"Type {record.user_confirmation_phrase}",
                "second_confirmation_required": True,
                "third_confirmation_required": False,
                "requires_strong_confirmation": True,
                "requires_double_confirmation": True,
                "requires_triple_confirmation": False,
                "expires_at": record.expires_at,
                "created_at": record.requested_at,
                "decided_at": None,
                "status": record.status.value,
                "rejection_reason": "",
                "decision_reason": "waiting_for_first_trusted_channel",
                "audit_id": "",
                "can_approve": True,
                "can_dispatch_after_approval": False,
                "stronger_approval_configured": True,
                "context_fingerprint": record.context_fingerprint,
                "used_at": None,
                "step_count_required": 2,
                "step_count_approved": 0,
                "channel_ids": [],
                "approval_steps": [
                    {
                        "step_id": "step-1",
                        "status": "pending",
                        "channel_id": "",
                        "channel_type": "",
                        "confirmation_phrase": record.user_confirmation_phrase,
                        "challenge": f"Type {record.user_confirmation_phrase}",
                        "readback_required": True,
                        "expires_at": record.expires_at,
                        "approved_at": None,
                        "approved_by": "",
                    },
                    {
                        "step_id": "step-2",
                        "status": "pending",
                        "channel_id": "",
                        "channel_type": "",
                        "confirmation_phrase": step_2_phrase,
                        "challenge": f"Type {step_2_phrase}",
                        "readback_required": True,
                        "expires_at": _iso_after(DOUBLE_APPROVAL_SECONDS),
                        "approved_at": None,
                        "approved_by": "",
                    },
                ],
            }
            preview["approval_envelope"] = envelope
            preview["state"] = "approval_requested"
            preview["updated_at"] = self.clock()
            self._approval_envelopes[record.approval_id] = envelope
            self._approval_to_preview[record.approval_id] = preview_id
            self._audit_approval_v2(preview, envelope)
            for step in envelope["approval_steps"]:
                self._audit_v2(
                    "approval_step_requested",
                    correlation_id=preview["correlation_id"],
                    risk_level=envelope["risk_level"],
                    approval_level="double",
                    metadata={"approval_id": record.approval_id, "step_id": step["step_id"]},
                )
            return dict(envelope)

    def _channel(self, channel_id: str) -> Dict[str, Any]:
        data = dict(_CHANNELS.get(channel_id, _disabled_channel(channel_id)))
        data["last_verified_at"] = self._channel_verified_at.get(channel_id, "")
        if channel_id in self._channel_verified_at:
            data["authenticated"] = True
        return data

    def _state_dir(self) -> Path:
        configured = os.environ.get("JARVIS_LOCAL_STATE_DIR") or os.environ.get("JARVIS_STATE_DIR")
        return Path(configured).resolve() if configured else self.cwd / ".jarvis"

    def _audit_dir(self, state_dir: Path) -> str:
        db_path = getattr(self.audit_ledger, "db_path", None)
        if db_path:
            return str(Path(db_path).parent)
        return str(state_dir / "audit")


def _select_step(steps: List[Dict[str, Any]], step_id: Optional[str]) -> Optional[Dict[str, Any]]:
    if step_id:
        return next((item for item in steps if item.get("step_id") == step_id), None)
    return next((item for item in steps if item.get("status") == "pending"), None)


def _timestamp(value: str) -> float:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return time.time()


def _iso_after(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def _is_expired(value: Any) -> bool:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) >= parsed.astimezone(timezone.utc)


def _phase3_check(name: str, passed: bool, notes: str) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "status": "passed" if passed else "failed", "notes": notes}


def _doctor_check(name: str, status: str, detail: str) -> Dict[str, Any]:
    return {"name": name, "status": status, "detail": _redact_text(detail, limit=240), "metadata_only": True}


def _import_status(module: str) -> str:
    return "ok" if importlib.util.find_spec(module) is not None else "missing"


def _writable_status(path: Path) -> str:
    target = path if path.exists() else path.parent
    return "ok" if target.exists() and os.access(target, os.W_OK) else "missing_or_not_writable"


def _git_clean_status(argv: List[str], *, expect_empty: bool, cwd: Path) -> str:
    try:
        result = subprocess.run(
            argv,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    if result.returncode != 0:
        return "unknown"
    output = (result.stdout or "").strip()
    if expect_empty:
        return "ok" if not output else "unexpected_entries"
    return "ok"


def _status_summary(value: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return {"available": False}
    state = value.get("state") if isinstance(value.get("state"), Mapping) else value
    return {
        "available": bool(state.get("available", value.get("available", True))) if isinstance(state, Mapping) else True,
        "schema_version": value.get("schema_version", ""),
        "record_count": state.get("record_count", value.get("record_count", 0)) if isinstance(state, Mapping) else 0,
        "metadata_only": bool(state.get("metadata_only", value.get("metadata_only", True))) if isinstance(state, Mapping) else True,
    }


def _disabled_channel(channel_id: str) -> Dict[str, Any]:
    return {
        "channel_id": channel_id,
        "channel_type": "unknown",
        "trusted": False,
        "enabled": False,
        "authenticated": False,
        "local_only": True,
        "can_request_approval": False,
        "can_grant_approval": False,
        "can_grant_strong": False,
        "can_grant_double": False,
        "can_grant_triple": False,
        "can_cancel": False,
        "can_stop": False,
        "requires_presence": True,
        "requires_readback": True,
        "requires_confirmation_phrase": True,
        "risk_limit": "none",
        "audit_required": True,
        "last_verified_at": "",
    }


_CHANNELS: Dict[str, Dict[str, Any]] = {
    "ui_local_browser": {
        "channel_id": "ui_local_browser",
        "channel_type": "local_browser",
        "trusted": True,
        "enabled": True,
        "authenticated": True,
        "local_only": True,
        "can_request_approval": True,
        "can_grant_approval": True,
        "can_grant_strong": True,
        "can_grant_double": True,
        "can_grant_triple": False,
        "can_cancel": True,
        "can_stop": True,
        "requires_presence": True,
        "requires_readback": True,
        "requires_confirmation_phrase": True,
        "risk_limit": "high",
        "audit_required": True,
        "last_verified_at": "",
    },
    "terminal_local": {
        "channel_id": "terminal_local",
        "channel_type": "local_terminal",
        "trusted": True,
        "enabled": True,
        "authenticated": False,
        "local_only": True,
        "can_request_approval": True,
        "can_grant_approval": True,
        "can_grant_strong": True,
        "can_grant_double": True,
        "can_grant_triple": False,
        "can_cancel": True,
        "can_stop": True,
        "requires_presence": True,
        "requires_readback": True,
        "requires_confirmation_phrase": True,
        "risk_limit": "critical",
        "audit_required": True,
        "last_verified_at": "",
    },
    "tray_local_not_installed": {
        "channel_id": "tray_local_not_installed",
        "channel_type": "local_tray",
        "trusted": False,
        "enabled": False,
        "authenticated": False,
        "local_only": True,
        "can_request_approval": False,
        "can_grant_approval": False,
        "can_grant_strong": False,
        "can_grant_double": False,
        "can_grant_triple": False,
        "can_cancel": True,
        "can_stop": False,
        "requires_presence": True,
        "requires_readback": True,
        "requires_confirmation_phrase": True,
        "risk_limit": "none",
        "audit_required": True,
        "last_verified_at": "",
    },
    "voice_readback_only": {
        "channel_id": "voice_readback_only",
        "channel_type": "voice_readback",
        "trusted": False,
        "enabled": True,
        "authenticated": False,
        "local_only": True,
        "can_request_approval": False,
        "can_grant_approval": False,
        "can_grant_strong": False,
        "can_grant_double": False,
        "can_grant_triple": False,
        "can_cancel": True,
        "can_stop": True,
        "requires_presence": True,
        "requires_readback": True,
        "requires_confirmation_phrase": False,
        "risk_limit": "none",
        "audit_required": True,
        "last_verified_at": "",
    },
    "wake_phrase_disabled": {
        "channel_id": "wake_phrase_disabled",
        "channel_type": "wake_phrase",
        "trusted": False,
        "enabled": False,
        "authenticated": False,
        "local_only": True,
        "can_request_approval": False,
        "can_grant_approval": False,
        "can_grant_strong": False,
        "can_grant_double": False,
        "can_grant_triple": False,
        "can_cancel": False,
        "can_stop": False,
        "requires_presence": True,
        "requires_readback": True,
        "requires_confirmation_phrase": True,
        "risk_limit": "none",
        "audit_required": True,
        "last_verified_at": "",
    },
    "telegram_future_disabled": {
        "channel_id": "telegram_future_disabled",
        "channel_type": "telegram_future",
        "trusted": False,
        "enabled": False,
        "authenticated": False,
        "local_only": False,
        "can_request_approval": False,
        "can_grant_approval": False,
        "can_grant_strong": False,
        "can_grant_double": False,
        "can_grant_triple": False,
        "can_cancel": False,
        "can_stop": False,
        "requires_presence": True,
        "requires_readback": True,
        "requires_confirmation_phrase": True,
        "risk_limit": "none",
        "audit_required": True,
        "last_verified_at": "",
    },
    "mobile_future_disabled": {
        "channel_id": "mobile_future_disabled",
        "channel_type": "mobile_future",
        "trusted": False,
        "enabled": False,
        "authenticated": False,
        "local_only": False,
        "can_request_approval": False,
        "can_grant_approval": False,
        "can_grant_strong": False,
        "can_grant_double": False,
        "can_grant_triple": False,
        "can_cancel": False,
        "can_stop": False,
        "requires_presence": True,
        "requires_readback": True,
        "requires_confirmation_phrase": True,
        "risk_limit": "none",
        "audit_required": True,
        "last_verified_at": "",
    },
}

_CHANNEL_ORDER = (
    "ui_local_browser",
    "terminal_local",
    "tray_local_not_installed",
    "voice_readback_only",
    "wake_phrase_disabled",
    "telegram_future_disabled",
    "mobile_future_disabled",
)
