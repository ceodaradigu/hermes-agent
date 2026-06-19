from __future__ import annotations

import os
import socket
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from jarvis.approval_hardening import ApprovalKind, ApprovalStatus
from jarvis.phase_2_local_assistant_runtime import (
    ACTION_CATALOG,
    _normalize_readback,
    _readback_for_preview,
    _required_approval_level,
    _safe_text,
)
from jarvis.phase_3_local_runtime import (
    LOCAL_BIND_HOST,
    LOCAL_BIND_PORT,
    PHASE_3_SCHEMA_VERSION,
    Phase3LocalRuntimeControlPlane,
    _is_expired,
    _iso_after,
    _select_step,
)


PHASE_4_SCHEMA_VERSION = "jarvis.phase_4_real_local_controller_remote_pairing_readiness.v1"
LOCAL_CONTROLLER_SCHEMA_VERSION = "jarvis.local_controller.v1"
TRUSTED_DEVICE_SCHEMA_VERSION = "jarvis.trusted_devices.v1"
TRIPLE_APPROVAL_SCHEMA_VERSION = "jarvis.triple_approval_readiness.v1"
REMOTE_PAIRING_SCHEMA_VERSION = "jarvis.remote_pairing_readiness.v1"
TELEGRAM_BRIDGE_SCHEMA_VERSION = "jarvis.telegram_bridge_readiness.v1"
STOP_ROLLBACK_V2_SCHEMA_VERSION = "jarvis.stop_rollback_v2.v1"

LOCAL_CONTROLLER_VERIFICATION_PHRASE = "VERIFY LOCAL CONTROLLER"
TERMINAL_VERIFICATION_PHRASE = "VERIFY TERMINAL CHANNEL"
TRIPLE_APPROVAL_SECONDS = 900
REMOTE_PAIRING_TTL_SECONDS = 300
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


class Phase4LocalControllerRemotePairingControlPlane(Phase3LocalRuntimeControlPlane):
    """Phase 4 local controller and remote pairing readiness.

    This extends the existing governed local runtime. It does not start a new
    Hermes runtime, expose a freeform shell, open public ports, read tokens, or
    enable remote approval/execution.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._phase4_started_at = self.clock()
        self._controllers: Dict[str, Dict[str, Any]] = {}
        self._revoked_devices: Dict[str, str] = {}
        self._pairing_challenges: Dict[str, Dict[str, Any]] = {}
        self._revoked_pairing_count = 0
        self._last_pairing_attempt_at: Optional[str] = None
        self._phase4_stop_requests: Dict[str, Dict[str, Any]] = {}
        self._rollback_dry_runs: Dict[str, Dict[str, Any]] = {}

    def status(self) -> Dict[str, Any]:
        base = super().status()
        base["schema_version"] = PHASE_4_SCHEMA_VERSION
        base["phase"] = "Phase 4"
        base["phase_4_status"] = self.phase_4_status(route_paths=())
        base["local_controller"] = self.local_controller_status()
        base["trusted_devices"] = self.trusted_devices_status()
        base["triple_approval_readiness"] = self.triple_approval_readiness_status()
        base["remote_pairing"] = self.remote_pairing_status()
        base["telegram_bridge"] = self.telegram_bridge_status()
        base["stop_rollback_v2"] = self.stop_rollback_status()
        base["safety"].update({
            "phase_4_local_controller_opt_in": True,
            "remote_pairing_enabled": False,
            "telegram_bridge_enabled": False,
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "no_execute_route": True,
            "no_external_bind": self.bind_host in LOCAL_HOSTS,
        })
        return base

    def phase_4_status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        triple = self.triple_approval_readiness_status()
        return {
            "schema_version": PHASE_4_SCHEMA_VERSION,
            "phase": "Phase 4",
            "title": "PR #169 -- Phase 4 Real Local Controller + Remote Pairing Readiness",
            "status": "implemented_as_local_controller_remote_pairing_readiness_macro_phase",
            "implemented_blocks": {
                "real_local_controller_opt_in": True,
                "trusted_device_controller_identity": True,
                "triple_approval_readiness": True,
                "remote_pairing_readiness_disabled": True,
                "telegram_hermes_bridge_readiness_disabled": True,
                "pairing_challenges_ephemeral": True,
                "stop_rollback_v2_observable": True,
                "local_pilot_phase_4": True,
                "documentation_phase_4": True,
            },
            "route_readiness": {
                "phase_4_status": "/mark-3/phase-4/status" in routes,
                "local_controller_status": "/mark-3/local-controller/status" in routes,
                "trusted_devices_status": "/mark-3/trusted-devices/status" in routes,
                "remote_pairing_status": "/mark-3/remote-pairing/status" in routes,
                "telegram_bridge_status": "/mark-3/telegram-bridge/status" in routes,
                "stop_rollback_status": "/mark-3/stop-rollback/status" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "local_controller": self.local_controller_status(),
            "trusted_devices": self.trusted_devices_status(),
            "triple_approval_readiness": triple,
            "remote_pairing": self.remote_pairing_status(),
            "telegram_bridge": self.telegram_bridge_status(),
            "stop_rollback_v2": self.stop_rollback_status(),
            "pilot": self.pilot_checklist_status(),
            "blocked_or_unsupported": {
                "critical_without_three_channels": (
                    "ready_after_three_verified_local_channels"
                    if triple["can_grant_triple"] else "blocked_no_three_verified_channels"
                ),
                "remote_pairing": "disabled_readiness_only",
                "telegram_bot": "disabled_not_configured_not_called",
                "remote_approval": "disabled",
                "remote_execution": "disabled",
                "native_service_install": "unsupported_no_service_install_in_phase_4",
                "startup_integration": "unsupported_no_startup_modification_in_phase_4",
                "freeform_shell": "denied",
                "arbitrary_commands": "denied",
            },
            "security_gates": {
                "jarvis_governs": True,
                "hermes_executes": True,
                "no_duplicate_hermes_runtime": True,
                "frontend_can_execute_hermes_directly": False,
                "backend_recalculates_policy_before_final_triple": True,
                "audit_metadata_only": True,
                "memory_grants_permission": False,
                "wake_phrase_can_approve": False,
                "voice_can_approve": False,
                "remote_pairing_enabled": False,
                "remote_approval_allowed": False,
                "remote_execution_allowed": False,
                "telegram_api_called": False,
                "env_read_for_tokens": False,
                "external_bind_allowed": False,
            },
            "external_adoption": self.external_adoption_references(),
            "source_endpoint": "/mark-3/phase-4/status",
        }

    def local_controller_status(self) -> Dict[str, Any]:
        controller = self._active_controller()
        bind_safe = self.bind_host in LOCAL_HOSTS
        return {
            "schema_version": LOCAL_CONTROLLER_SCHEMA_VERSION,
            "controller_id": controller.get("controller_id", self._default_controller_id()),
            "controller_status": controller.get("controller_status", "not_registered"),
            "controller_mode": controller.get("controller_mode", "local_opt_in_readiness"),
            "local_only": True,
            "bind_host": self.bind_host,
            "bind_port": self.bind_port,
            "controller_url": f"http://{LOCAL_BIND_HOST}:{self.bind_port}/jarvis",
            "can_open_jarvis": True,
            "can_show_status": True,
            "can_show_approvals": True,
            "can_request_stop": True,
            "can_request_cancel": True,
            "can_toggle_voice_session": True,
            "can_toggle_camera_session": True,
            "can_toggle_recording_session": True,
            "auto_start_enabled": False,
            "installed_as_system_service": False,
            "startup_integration_enabled": False,
            "user_opt_in_required": True,
            "no_background_capture": True,
            "last_seen_at": controller.get("last_seen_at"),
            "health_status": "healthy" if bind_safe else "blocked_external_bind",
            "verified": bool(controller.get("verified", False)),
            "registered": bool(controller),
            "failure_modes": [
                "native_tray_or_controller_process_not_installed",
                "registered_controller_is_process_memory_only",
                "system_service_install_not_supported",
                "startup_integration_not_supported",
                "external_bind_blocked",
                "stop_request_is_cooperative_observable_not_process_kill",
                "voice_camera_recording_toggles_are_ui_contracts_only",
            ],
            "source_endpoint": "/mark-3/local-controller/status",
            "metadata_only": True,
        }

    def register_local_controller(
        self,
        *,
        controller_id: Optional[str] = None,
        display_name: str = "JARVIS Local Controller",
        actor: str = "David",
        verification_phrase: str = "",
        local_only: bool = True,
        bind_host: str = LOCAL_BIND_HOST,
        bind_port: Optional[int] = None,
    ) -> Dict[str, Any]:
        requested_host = _safe_text(bind_host, limit=120) or LOCAL_BIND_HOST
        if not local_only or requested_host not in LOCAL_HOSTS:
            self._audit_v2(
                "local_controller_registered",
                correlation_id=f"corr-{uuid4()}",
                surface="local_controller",
                risk_level="high",
                approval_level="blocked",
                metadata={"registered": False, "reason": "external_bind_or_non_local_controller_rejected"},
            )
            raise ValueError("local controller must be local_only and bound to 127.0.0.1")
        now = self.clock()
        safe_controller_id = _safe_text(controller_id, limit=120) or self._default_controller_id()
        safe_display = _safe_text(display_name, limit=120) or "JARVIS Local Controller"
        verified = verification_phrase == LOCAL_CONTROLLER_VERIFICATION_PHRASE
        controller = {
            "schema_version": LOCAL_CONTROLLER_SCHEMA_VERSION,
            "controller_id": safe_controller_id,
            "device_id": f"device-{safe_controller_id}",
            "display_name": safe_display,
            "controller_status": "registered_verified" if verified else "registered_unverified",
            "controller_mode": "local_opt_in_controller",
            "local_only": True,
            "bind_host": LOCAL_BIND_HOST,
            "bind_port": int(bind_port or self.bind_port or LOCAL_BIND_PORT),
            "created_at": self._controllers.get(safe_controller_id, {}).get("created_at", now),
            "last_seen_at": now,
            "trusted": verified,
            "verified": verified,
            "paired": verified,
            "revoked": False,
        }
        self._controllers[safe_controller_id] = controller
        audit = self._audit_v2(
            "local_controller_registered",
            correlation_id=f"corr-{uuid4()}",
            surface="local_controller",
            risk_level="medium",
            approval_level="none",
            metadata={
                "controller_id": safe_controller_id,
                "verified": verified,
                "local_only": True,
                "bind_host": LOCAL_BIND_HOST,
                "metadata_only": True,
            },
        )
        return {
            "schema_version": LOCAL_CONTROLLER_SCHEMA_VERSION,
            "controller_id": safe_controller_id,
            "controller_status": controller["controller_status"],
            "verified": verified,
            "trusted_device": self._controller_device(controller, audit_ids=[audit.get("audit_id", "")]),
            "controller": self.local_controller_status(),
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def local_controller_heartbeat(self, *, controller_id: Optional[str] = None, actor: str = "David") -> Dict[str, Any]:
        controller = self._resolve_controller(controller_id)
        now = self.clock()
        controller["last_seen_at"] = now
        controller["controller_status"] = "heartbeat_verified" if controller.get("verified") else "heartbeat_unverified"
        audit = self._audit_v2(
            "local_controller_heartbeat",
            correlation_id=f"corr-{uuid4()}",
            surface="local_controller",
            metadata={"controller_id": controller["controller_id"], "actor": actor, "verified": bool(controller.get("verified"))},
        )
        return {
            "schema_version": LOCAL_CONTROLLER_SCHEMA_VERSION,
            "controller_id": controller["controller_id"],
            "controller_status": controller["controller_status"],
            "last_seen_at": now,
            "health_status": "healthy",
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def local_controller_open_jarvis_request(
        self,
        *,
        controller_id: Optional[str] = None,
        actor: str = "David",
        reason: str = "operator open jarvis request",
    ) -> Dict[str, Any]:
        controller = self._resolve_controller(controller_id, allow_missing=True)
        audit = self._audit_v2(
            "local_controller_open_requested",
            correlation_id=f"corr-{uuid4()}",
            surface="local_controller",
            metadata={
                "controller_id": controller.get("controller_id", self._default_controller_id()),
                "actor": actor,
                "reason": reason,
                "did_open_browser": False,
            },
        )
        return {
            "schema_version": LOCAL_CONTROLLER_SCHEMA_VERSION,
            "request_status": "recorded_not_executed",
            "can_open_jarvis": True,
            "did_open_browser": False,
            "controller_url": f"http://{LOCAL_BIND_HOST}:{self.bind_port}/jarvis",
            "reason": "controller contract recorded; backend does not open UI windows in Phase 4",
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def local_controller_stop_request(
        self,
        *,
        controller_id: Optional[str] = None,
        actor: str = "David",
        reason: str = "operator stop",
        scope: Optional[List[str]] = None,
        deadline_seconds: int = 10,
    ) -> Dict[str, Any]:
        controller = self._resolve_controller(controller_id, allow_missing=True)
        stop_request_id = f"stop-{uuid4()}"
        now = self.clock()
        deadline = (datetime.now(timezone.utc) + timedelta(seconds=max(1, min(int(deadline_seconds or 10), 60)))).isoformat()
        audit = self._audit_v2(
            "local_controller_stop_requested",
            correlation_id=f"corr-{uuid4()}",
            surface="stop_rollback",
            risk_level="medium",
            approval_level="none",
            metadata={
                "stop_request_id": stop_request_id,
                "controller_id": controller.get("controller_id", self._default_controller_id()),
                "actor": actor,
                "channel": "local_controller",
                "scope": [_safe_text(item, limit=80) for item in (scope or ["local_controller"])],
                "reason": reason,
            },
        )
        result = {
            "schema_version": STOP_ROLLBACK_V2_SCHEMA_VERSION,
            "stop_request_id": stop_request_id,
            "stop_reason": _safe_text(reason, limit=160),
            "stop_actor": _safe_text(actor, limit=80),
            "stop_channel": "local_controller",
            "stop_scope": [_safe_text(item, limit=80) for item in (scope or ["local_controller"])],
            "stop_deadline": deadline,
            "stop_confirmation": "cooperative_stop_signal_recorded",
            "cooperative_stop_signal": True,
            "bridge_stop_attempt": "not_attempted_no_active_external_bridge",
            "result_observed": False,
            "final_state": "unsupported_embedded_backend_not_stopped",
            "rollback_plan_detail_metadata": "No rollback executed; request is observable metadata only.",
            "rollback_preconditions": ["active_execution_id", "supported_rollback_contract", "valid_approval_if_destructive"],
            "rollback_dry_run_mode": True,
            "rollback_approval_requirement": "required_for_destructive_rollback",
            "requested_at": now,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._phase4_stop_requests[stop_request_id] = result
        return result

    def trusted_devices_status(self) -> Dict[str, Any]:
        devices = [
            self._local_browser_device(),
            self._terminal_device(),
            self._controller_device(self._active_controller()),
            self._voice_device(),
            self._wake_device(),
            self._remote_placeholder_device("telegram_future_disabled", "Telegram future bridge"),
            self._remote_placeholder_device("mobile_future_disabled", "Mobile future bridge"),
        ]
        remote_devices = [item for item in devices if not item["local_only"]]
        active_trusted = [item for item in devices if item["trusted"] and item["verified"] and item["paired"] and not item["revoked"]]
        return {
            "schema_version": TRUSTED_DEVICE_SCHEMA_VERSION,
            "devices": devices,
            "trusted_device_count": len(active_trusted),
            "paired_devices_count": sum(1 for item in devices if item["paired"] and not item["revoked"]),
            "remote_devices_count": len([item for item in remote_devices if item["paired"] and not item["revoked"]]),
            "remote_trusted_devices_count": len([item for item in remote_devices if item["trusted"] and not item["revoked"]]),
            "default_remote_devices_zero_untrusted": True,
            "local_browser_trust_limited": True,
            "terminal_trust_requires_challenge": True,
            "controller_trust_requires_registration_and_verification": True,
            "revoked_devices_count": len(self._revoked_devices),
            "can_grant_normal": any(item["can_grant_normal"] for item in active_trusted),
            "can_grant_strong": any(item["can_grant_strong"] for item in active_trusted),
            "can_grant_double": len({item["channel_type"] for item in active_trusted if item["can_grant_double"]}) >= 2,
            "can_grant_triple": self.triple_approval_readiness_status()["can_grant_triple"],
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "source_endpoint": "/mark-3/trusted-devices/status",
            "metadata_only": True,
        }

    def trusted_approval_channels_status(self) -> Dict[str, Any]:
        base = super().trusted_approval_channels_status()
        readiness = self.triple_approval_readiness_status()
        channels = [self._channel(str(item.get("channel_id"))) for item in base.get("channels", [])]
        channels.append(self._channel("local_controller"))
        base.update({
            "schema_version": TRUSTED_DEVICE_SCHEMA_VERSION,
            "channels": channels,
            "trusted_devices": self.trusted_devices_status(),
            "trusted_enabled_channel_count": sum(1 for item in channels if item["trusted"] and item["enabled"]),
            "can_grant_triple": readiness["can_grant_triple"],
            "triple_status": readiness["triple_status"],
            "triple_ready_channel_ids": readiness["ready_channel_ids"],
            "source_endpoint": "/mark-3/trusted-devices/status",
        })
        return base

    def verify_trusted_channel(
        self,
        *,
        channel_id: str,
        actor: str = "David",
        local_presence: bool = True,
        challenge_response: Optional[str] = None,
    ) -> Dict[str, Any]:
        if channel_id == "terminal_local" and challenge_response is not None and challenge_response != TERMINAL_VERIFICATION_PHRASE:
            audit = self._audit_v2(
                "trusted_channel_rejected",
                correlation_id=f"corr-{uuid4()}",
                metadata={"channel_id": channel_id, "actor": actor, "challenge_valid": False},
            )
            return {
                "schema_version": TRUSTED_DEVICE_SCHEMA_VERSION,
                "channel_id": channel_id,
                "verified": False,
                "reason": "terminal_challenge_invalid",
                "audit_id": audit.get("audit_id", ""),
            }
        return super().verify_trusted_channel(channel_id=channel_id, actor=actor, local_presence=local_presence)

    def triple_approval_readiness_status(self) -> Dict[str, Any]:
        channels = self._triple_ready_channels()
        channel_types = {item["channel_type"] for item in channels}
        ready = len(channels) >= 3 and len(channel_types) >= 3
        return {
            "schema_version": TRIPLE_APPROVAL_SCHEMA_VERSION,
            "triple_status": "ready_three_verified_local_channels" if ready else "blocked_no_three_verified_channels",
            "can_grant_triple": ready,
            "required_step_count": 3,
            "ready_channel_ids": [item["channel_id"] for item in channels],
            "ready_channel_types": sorted(channel_types),
            "channel_separation_required": True,
            "challenge_per_step": True,
            "readback_per_step": True,
            "confirmation_phrase_per_step": True,
            "expiry_per_step": True,
            "anti_reuse": True,
            "audit_per_step": True,
            "policy_recalculation_before_final_decision": True,
            "voice_can_approve": False,
            "wake_phrase_can_approve": False,
            "blocked_reason": "" if ready else "critical requires ui_local_browser + verified terminal_local + verified local_controller",
            "source_endpoint": "/mark-3/phase-4/status",
            "metadata_only": True,
        }

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
        normalized = (decision or "").strip().lower().replace("-", "_")
        if "voice" in channel_id or "wake" in channel_id:
            raise ValueError("voice and wake phrase cannot approve")
        channel = self._channel(channel_id)
        if not channel.get("can_grant_triple"):
            raise ValueError("channel cannot grant triple approval")
        if not channel.get("authenticated"):
            raise ValueError("channel must be verified before approval")
        readiness = self.triple_approval_readiness_status()
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            if envelope is None:
                raise KeyError(approval_id)
            preview = self._previews[envelope["preview_id"]]
            if envelope.get("approval_level_required") != "triple":
                raise ValueError("approval is not a triple approval")
            if not readiness["can_grant_triple"] or envelope.get("status") == "blocked":
                envelope["status"] = "blocked"
                envelope["decision_reason"] = "blocked_no_three_verified_channels"
                envelope["can_approve"] = False
                envelope["can_dispatch_after_approval"] = False
                preview["state"] = "approval_blocked"
                self._audit_v2(
                    "approval_blocked",
                    correlation_id=preview["correlation_id"],
                    risk_level=envelope["risk_level"],
                    approval_level="triple",
                    metadata={"approval_id": approval_id, "channel_id": channel_id, "reason": envelope["decision_reason"]},
                )
                return dict(envelope)
            if envelope.get("used_at"):
                raise ValueError("approval has already been used")
            if envelope["status"] in {"approved", "rejected", "cancelled", "expired"}:
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
                    approval_level="triple",
                    metadata={"approval_id": approval_id, "step_id": step["step_id"], "channel_id": channel_id},
                )
                raise ValueError("approval step is expired")
            if normalized in {"reject", "rejected", "deny"}:
                step["status"] = "rejected"
                step["decided_at"] = self.clock()
                step["channel_id"] = channel_id
                envelope["status"] = "rejected"
                envelope["decision_reason"] = reason or "triple approval rejected"
                preview["state"] = "approval_rejected"
                self._audit_v2(
                    "approval_step_rejected",
                    correlation_id=preview["correlation_id"],
                    risk_level=envelope["risk_level"],
                    approval_level="triple",
                    metadata={"approval_id": approval_id, "step_id": step["step_id"], "channel_id": channel_id},
                )
                return dict(envelope)
            if normalized not in {"approve", "approved"}:
                raise ValueError("decision must be approve or reject")
            if _normalize_readback(readback_text) != _normalize_readback(envelope["readback_text"]):
                raise ValueError("readback text does not match required readback")
            if confirmation_phrase != step.get("confirmation_phrase"):
                raise ValueError("confirmation phrase does not match")
            approved_channels = [item.get("channel_id", "") for item in steps if item.get("status") == "approved"]
            approved_types = [item.get("channel_type", "") for item in steps if item.get("status") == "approved"]
            if channel_id in approved_channels or channel.get("channel_type") in approved_types:
                raise ValueError("triple approval requires three separate trusted channels")
            step["status"] = "approved"
            step["approved_at"] = self.clock()
            step["approved_by"] = _safe_text(actor, limit=80)
            step["channel_id"] = channel_id
            step["channel_type"] = channel["channel_type"]
            envelope["step_count_approved"] = sum(1 for item in steps if item.get("status") == "approved")
            envelope["channel_ids"] = [item.get("channel_id", "") for item in steps if item.get("status") == "approved"]
            self._audit_v2(
                "approval_step_approved",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level="triple",
                metadata={"approval_id": approval_id, "step_id": step["step_id"], "channel_id": channel_id},
            )
            if envelope["step_count_approved"] < envelope["step_count_required"]:
                envelope["decision_reason"] = f"waiting_for_triple_step_{envelope['step_count_approved'] + 1}"
                return dict(envelope)
            action_key = preview["action"]["action_key"]
            recalculated = _required_approval_level(ACTION_CATALOG[action_key]) if action_key in ACTION_CATALOG else envelope["approval_level_required"]
            if recalculated != "triple":
                envelope["status"] = "blocked"
                envelope["decision_reason"] = "approval_policy_changed_before_final_decision"
                preview["state"] = "approval_blocked"
                raise ValueError("approval policy changed before final decision")
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
            envelope["decision_reason"] = "triple_approval_completed_policy_recalculated"
            envelope["can_dispatch_after_approval"] = True
            preview["state"] = "approval_approved"
            preview["updated_at"] = self.clock()
            self._audit_v2(
                "approval_approved",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level="triple",
                metadata={"approval_id": approval_id, "channel_ids": envelope["channel_ids"], "policy_recalculated": True},
            )
            return dict(envelope)

    def remote_pairing_status(self) -> Dict[str, Any]:
        pending = [item for item in self._pairing_challenges.values() if not _is_expired(item["expires_at"])]
        return {
            "schema_version": REMOTE_PAIRING_SCHEMA_VERSION,
            "pairing_status": "disabled_readiness_only",
            "remote_pairing_enabled": False,
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "trusted_pairing_required": True,
            "pairing_code_created": bool(pending),
            "pairing_code_ttl_seconds": REMOTE_PAIRING_TTL_SECONDS,
            "pairing_challenge_required": True,
            "pairing_channel": "local_ephemeral_challenge_only",
            "pairing_risk_limit": "none_until_enabled_in_future_phase",
            "paired_devices_count": 0,
            "pending_pairing_count": len(pending),
            "revoked_pairing_count": self._revoked_pairing_count,
            "last_pairing_attempt_at": self._last_pairing_attempt_at,
            "audit_required": True,
            "external_channel_opened": False,
            "tokens_persisted": False,
            "secrets_stored": False,
            "source_endpoint": "/mark-3/remote-pairing/status",
            "metadata_only": True,
        }

    def remote_pairing_prepare(self, *, actor: str = "David", channel: str = "local_controller") -> Dict[str, Any]:
        now = self.clock()
        challenge_id = f"pairing-{uuid4()}"
        challenge = {
            "challenge_id": challenge_id,
            "created_at": now,
            "expires_at": _iso_after(REMOTE_PAIRING_TTL_SECONDS),
            "channel": _safe_text(channel, limit=80) or "local_controller",
            "status": "prepared_local_only_remote_disabled",
        }
        self._pairing_challenges[challenge_id] = challenge
        self._last_pairing_attempt_at = now
        audit = self._audit_v2(
            "remote_pairing_prepared",
            correlation_id=f"corr-{uuid4()}",
            surface="remote_pairing",
            risk_level="medium",
            approval_level="blocked",
            metadata={
                "challenge_id": challenge_id,
                "actor": actor,
                "channel": challenge["channel"],
                "remote_pairing_enabled": False,
                "remote_approval_allowed": False,
                "remote_execution_allowed": False,
            },
        )
        return {
            "schema_version": REMOTE_PAIRING_SCHEMA_VERSION,
            "pairing_status": "prepared_local_ephemeral_challenge_remote_disabled",
            "challenge": challenge,
            "pairing_code_created": True,
            "pairing_code_persistent": False,
            "remote_pairing_enabled": False,
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "external_channel_opened": False,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def remote_pairing_cancel(self, *, actor: str = "David", challenge_id: Optional[str] = None, reason: str = "operator cancel") -> Dict[str, Any]:
        cancelled = 0
        if challenge_id:
            cancelled = 1 if self._pairing_challenges.pop(challenge_id, None) else 0
        else:
            cancelled = len(self._pairing_challenges)
            self._pairing_challenges.clear()
        audit = self._audit_v2(
            "remote_pairing_cancelled",
            correlation_id=f"corr-{uuid4()}",
            surface="remote_pairing",
            metadata={"challenge_id": challenge_id or "all", "actor": actor, "reason": reason, "cancelled_count": cancelled},
        )
        return {
            "schema_version": REMOTE_PAIRING_SCHEMA_VERSION,
            "pairing_status": "cancelled",
            "cancelled_count": cancelled,
            "remote_pairing_enabled": False,
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def remote_pairing_revoke(self, *, actor: str = "David", device_id: Optional[str] = None, reason: str = "operator revoke") -> Dict[str, Any]:
        self._revoked_pairing_count += 1
        if device_id:
            self._revoked_devices[_safe_text(device_id, limit=160)] = self.clock()
        audit = self._audit_v2(
            "remote_pairing_revoked",
            correlation_id=f"corr-{uuid4()}",
            surface="remote_pairing",
            risk_level="medium",
            approval_level="none",
            metadata={"device_id": device_id or "future_remote_pairing", "actor": actor, "reason": reason},
        )
        return {
            "schema_version": REMOTE_PAIRING_SCHEMA_VERSION,
            "pairing_status": "revoked",
            "device_id": _safe_text(device_id, limit=160),
            "revoked_pairing_count": self._revoked_pairing_count,
            "remote_pairing_enabled": False,
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def telegram_bridge_status(self) -> Dict[str, Any]:
        return {
            "schema_version": TELEGRAM_BRIDGE_SCHEMA_VERSION,
            "telegram_bridge_status": "disabled_not_configured",
            "hermes_telegram_available_unknown_or_detected": "unknown_not_imported_not_called",
            "token_present": "unknown_redacted",
            "token_read": False,
            "env_read": False,
            "telegram_api_called": False,
            "bot_started": False,
            "webhook_opened": False,
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "pairing_required": True,
            "strong_approval_allowed": False,
            "can_receive_notifications_future": True,
            "can_request_approval_future": False,
            "can_execute_future": False,
            "future_requirements": [
                "explicit remote pairing enablement",
                "trusted device verification",
                "risk limit lower than critical by default",
                "local policy recalculation",
                "metadata-only audit",
                "revocation path",
            ],
            "source_endpoint": "/mark-3/telegram-bridge/status",
            "metadata_only": True,
        }

    def stop_rollback_status(self) -> Dict[str, Any]:
        latest_stop = next(iter(self._phase4_stop_requests.values()), None) if self._phase4_stop_requests else None
        return {
            "schema_version": STOP_ROLLBACK_V2_SCHEMA_VERSION,
            "status": "observable_metadata_only",
            "stop_reason": (latest_stop or {}).get("stop_reason", ""),
            "stop_actor": (latest_stop or {}).get("stop_actor", ""),
            "stop_channel": (latest_stop or {}).get("stop_channel", ""),
            "stop_scope": (latest_stop or {}).get("stop_scope", []),
            "stop_deadline": (latest_stop or {}).get("stop_deadline", ""),
            "stop_confirmation": (latest_stop or {}).get("stop_confirmation", "not_requested"),
            "cooperative_stop_signal": bool((latest_stop or {}).get("cooperative_stop_signal", False)),
            "bridge_stop_attempt": (latest_stop or {}).get("bridge_stop_attempt", "not_attempted"),
            "result_observed": bool((latest_stop or {}).get("result_observed", False)),
            "final_state": (latest_stop or {}).get("final_state", "no_active_stop_request"),
            "rollback_plan_detail_metadata": "Rollback is represented as metadata; destructive rollback is not executed.",
            "rollback_preconditions": ["supported_contract", "non_destructive_dry_run", "approval_for_destructive_rollback"],
            "rollback_dry_run_mode": True,
            "rollback_approval_requirement": "required_for_destructive_or_external_rollback",
            "destructive_rollback_executed": False,
            "rollback_never_faked": True,
            "stop_requests": list(self._phase4_stop_requests.values())[:5],
            "rollback_dry_runs": list(self._rollback_dry_runs.values())[:5],
            "source_endpoint": "/mark-3/stop-rollback/status",
            "metadata_only": True,
        }

    def record_rollback_dry_run(self, *, actor: str = "David", reason: str = "operator dry run") -> Dict[str, Any]:
        rollback_request_id = f"rollback-{uuid4()}"
        audit = self._audit_v2(
            "rollback_dry_run_recorded",
            correlation_id=f"corr-{uuid4()}",
            surface="stop_rollback",
            risk_level="medium",
            approval_level="none",
            metadata={"rollback_request_id": rollback_request_id, "actor": actor, "reason": reason, "destructive": False},
        )
        result = {
            "schema_version": STOP_ROLLBACK_V2_SCHEMA_VERSION,
            "rollback_request_id": rollback_request_id,
            "rollback_status": "dry_run_metadata_only",
            "rollback_supported": False,
            "rollback_destructive_executed": False,
            "rollback_plan_detail_metadata": "No destructive rollback was executed.",
            "rollback_preconditions": ["supported_action_contract", "valid_approval", "operator_readback"],
            "rollback_approval_requirement": "required_for_destructive_rollback",
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._rollback_dry_runs[rollback_request_id] = result
        return result

    def browser_verification_status(self, *, route_paths: Iterable[str]) -> Dict[str, Any]:
        base = super().browser_verification_status(route_paths=route_paths)
        route_set = set(route_paths)
        base["schema_version"] = PHASE_4_SCHEMA_VERSION
        base["phase_4_pilot"] = self.pilot_checklist_status()
        base["checks"] = list(base.get("checks", [])) + [
            _browser_check("phase_4_status_check", "/mark-3/phase-4/status" in route_set or not route_set, "Phase 4 status route is present."),
            _browser_check("local_controller_check", "/mark-3/local-controller/status" in route_set or not route_set, "Local controller route is present."),
            _browser_check("trusted_devices_check", "/mark-3/trusted-devices/status" in route_set or not route_set, "Trusted devices route is present."),
            _browser_check("remote_pairing_disabled_check", "/mark-3/remote-pairing/status" in route_set or not route_set, "Remote pairing status route is present and disabled."),
            _browser_check("telegram_bridge_disabled_check", "/mark-3/telegram-bridge/status" in route_set or not route_set, "Telegram bridge readiness route is present and disabled."),
        ]
        base["all_static_checks_passed"] = all(item["passed"] for item in base["checks"])
        return base

    def pilot_checklist_status(self) -> Dict[str, Any]:
        return {
            "schema_version": "jarvis.phase_4_local_controller_remote_pairing_pilot.v1",
            "backend_start_command": "source ~/venvs/hermes-agent/bin/activate && export PYTHONPATH=. && uvicorn jarvis.api.app:app --host 127.0.0.1 --port 9119",
            "frontend_start_command": "cd web && npm run dev -- --host 127.0.0.1",
            "validated_by_automated_tests": [
                "phase_4_status_exists",
                "local_controller_local_only_defaults",
                "local_controller_register_heartbeat_metadata_only",
                "trusted_devices_default_remote_zero_untrusted",
                "triple_approval_blocked_without_three_channels",
                "remote_pairing_disabled_prepare_local_only",
                "telegram_bridge_disabled_no_token_read",
                "stop_rollback_v2_metadata_only",
                "credential_block_exact_phrase",
                "no_execute_route",
            ],
            "validated_by_build": ["web/npm_run_build"],
            "pending_manual_browser_pilot": [
                "open /jarvis",
                "inspect Phase 4 drawer panels",
                "verify orb idle remains calm",
                "verify no auto mic/camera/recording permission prompt",
                "verify remote pairing and Telegram show disabled",
            ],
            "unsupported_honestly": [
                "native tray/controller process not installed",
                "Windows service install not implemented",
                "startup integration not modified",
                "remote pairing not enabled",
                "Telegram bot not started",
                "destructive rollback not executed",
            ],
            "status_endpoints": [
                "/mark-3/phase-4/status",
                "/mark-3/local-controller/status",
                "/mark-3/trusted-devices/status",
                "/mark-3/remote-pairing/status",
                "/mark-3/telegram-bridge/status",
                "/mark-3/stop-rollback/status",
            ],
            "source_document": "docs/jarvis-phase-4-local-controller-remote-pairing-pilot-report.md",
            "metadata_only": True,
        }

    def external_adoption_references(self) -> List[Dict[str, str]]:
        return [
            {
                "repo": "OpenInterpreter/open-interpreter",
                "url": "https://github.com/OpenInterpreter/open-interpreter",
                "license": "AGPL-3.0",
                "adopted": "local state/sandbox/approval separation pattern; no code copied",
            },
            {
                "repo": "microsoft/autogen",
                "url": "https://github.com/microsoft/autogen",
                "license": "MIT",
                "adopted": "human-in-the-loop tool approval concept; reimplemented as local triple envelope",
            },
            {
                "repo": "langchain-ai/langgraph",
                "url": "https://github.com/langchain-ai/langgraph",
                "license": "MIT",
                "adopted": "explicit state/checkpoint thinking for approval steps; no dependency added",
            },
            {
                "repo": "home-assistant/core",
                "url": "https://github.com/home-assistant/core",
                "license": "Apache-2.0",
                "adopted": "local-first controller/status/opt-in posture; no integration copied",
            },
            {
                "repo": "python-telegram-bot/python-telegram-bot",
                "url": "https://github.com/python-telegram-bot/python-telegram-bot",
                "license": "LGPL-3.0",
                "adopted": "bot readiness boundaries only; no dependency or code copied",
            },
        ]

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
        if approval_level != "triple":
            return super()._phase2_request_approval(preview_id=preview_id, actor=actor)
        envelope = self._build_triple_envelope(preview, actor, contract, ready=self.triple_approval_readiness_status()["can_grant_triple"])
        with self._lock:
            preview["approval_envelope"] = envelope
            preview["state"] = "approval_requested" if envelope["status"] == "pending" else "approval_blocked"
            preview["updated_at"] = self.clock()
            self._approval_envelopes[envelope["approval_id"]] = envelope
            self._approval_to_preview[envelope["approval_id"]] = preview_id
        self._audit_approval_v2(preview, envelope)
        for step in envelope["approval_steps"]:
            self._audit_v2(
                "approval_step_requested",
                correlation_id=preview["correlation_id"],
                risk_level=envelope["risk_level"],
                approval_level="triple",
                metadata={"approval_id": envelope["approval_id"], "step_id": step["step_id"], "status": step["status"]},
            )
        return dict(envelope)

    def _build_triple_envelope(self, preview: Mapping[str, Any], actor: str, contract: Any, *, ready: bool) -> Dict[str, Any]:
        action = preview["action"]
        readback = _readback_for_preview(preview)
        if ready:
            record = self.mission_loop.approval_service.request(
                action_type=action["action_key"],
                requested_by=actor or "David",
                reason=contract.description,
                context={
                    "action_type": action["action_key"],
                    "action_key": action["action_key"],
                    "risk_level": contract.risk_level,
                    "approval_level_required": "triple",
                    "input_fingerprint": action.get("input_fingerprint"),
                    "local_only": not contract.network_allowed,
                    "side_effect_free": not contract.external_side_effects,
                    "protected_material_blocked": True,
                    "three_channel_approval": True,
                },
                approval_kind=ApprovalKind.STRONG,
                expires_in_seconds=TRIPLE_APPROVAL_SECONDS,
            )
            approval_id = record.approval_id
            created_at = record.requested_at
            expires_at = record.expires_at
            first_phrase = record.user_confirmation_phrase
            status = record.status.value
            decision_reason = "waiting_for_triple_step_1"
            can_approve = True
        else:
            approval_id = f"blocked-triple-{uuid4()}"
            created_at = self.clock()
            expires_at = ""
            first_phrase = f"BLOCKED {approval_id} STEP 1"
            status = "blocked"
            decision_reason = "blocked_no_three_verified_channels"
            can_approve = False
        phrases = [
            first_phrase,
            f"CONFIRM {approval_id} STEP 2",
            f"CONFIRM {approval_id} STEP 3",
        ]
        return {
            "schema_version": TRIPLE_APPROVAL_SCHEMA_VERSION,
            "approval_id": approval_id,
            "action_id": action["action_id"],
            "action_key": action["action_key"],
            "preview_id": preview["preview_id"],
            "correlation_id": preview["correlation_id"],
            "risk_level": contract.risk_level,
            "approval_level": "triple",
            "approval_level_required": "triple",
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
            "readback_text": readback,
            "readback_required": True,
            "confirmation_phrase": phrases[0],
            "challenge": f"Type {phrases[0]}",
            "second_confirmation_required": True,
            "third_confirmation_required": True,
            "requires_strong_confirmation": True,
            "requires_double_confirmation": True,
            "requires_triple_confirmation": True,
            "expires_at": expires_at,
            "created_at": created_at,
            "decided_at": None if ready else created_at,
            "status": status,
            "rejection_reason": "" if ready else decision_reason,
            "decision_reason": decision_reason,
            "audit_id": "",
            "can_approve": can_approve,
            "can_dispatch_after_approval": False,
            "stronger_approval_configured": ready,
            "context_fingerprint": "",
            "used_at": None,
            "step_count_required": 3,
            "step_count_approved": 0,
            "channel_ids": [],
            "channel_separation_required": True,
            "policy_recalculation_before_final_decision": True,
            "approval_steps": [
                _triple_step("step-1", phrases[0], expires_at or _iso_after(TRIPLE_APPROVAL_SECONDS), "ui_local_browser", status),
                _triple_step("step-2", phrases[1], _iso_after(TRIPLE_APPROVAL_SECONDS), "terminal_local", status),
                _triple_step("step-3", phrases[2], _iso_after(TRIPLE_APPROVAL_SECONDS), "local_controller", status),
            ],
        }

    def _channel(self, channel_id: str) -> Dict[str, Any]:
        if channel_id == "local_controller":
            controller = self._active_controller()
            device_id = str(controller.get("device_id") or f"device-{controller.get('controller_id')}")
            verified = bool(controller.get("verified")) and not controller.get("revoked") and device_id not in self._revoked_devices
            return {
                "channel_id": "local_controller",
                "channel_type": "local_controller",
                "trusted": verified,
                "enabled": bool(controller),
                "authenticated": verified,
                "local_only": True,
                "can_request_approval": verified,
                "can_grant_approval": verified,
                "can_grant_strong": verified,
                "can_grant_double": verified,
                "can_grant_triple": verified,
                "can_cancel": True,
                "can_stop": True,
                "requires_presence": True,
                "requires_readback": True,
                "requires_confirmation_phrase": True,
                "risk_limit": "critical" if verified else "none",
                "audit_required": True,
                "last_verified_at": controller.get("last_seen_at", ""),
            }
        data = super()._channel(channel_id)
        device_id = _device_id_for_channel(channel_id)
        if device_id in self._revoked_devices:
            data["trusted"] = False
            data["authenticated"] = False
            data["can_grant_approval"] = False
            data["can_grant_strong"] = False
            data["can_grant_double"] = False
            data["can_grant_triple"] = False
        if channel_id in {"ui_local_browser", "terminal_local"}:
            data["can_grant_triple"] = bool(data.get("trusted") and data.get("enabled") and data.get("authenticated"))
        return data

    def _triple_ready_channels(self) -> List[Dict[str, Any]]:
        candidates = [self._channel("ui_local_browser"), self._channel("terminal_local"), self._channel("local_controller")]
        return [
            item for item in candidates
            if item.get("enabled") and item.get("trusted") and item.get("authenticated") and item.get("local_only") and item.get("can_grant_triple")
        ]

    def _default_controller_id(self) -> str:
        return f"jarvis-local-controller-{socket.gethostname()}-{os.getpid()}"

    def _active_controller(self) -> Dict[str, Any]:
        if not self._controllers:
            return {}
        return next(reversed(self._controllers.values()))

    def _resolve_controller(self, controller_id: Optional[str], *, allow_missing: bool = False) -> Dict[str, Any]:
        if controller_id:
            controller = self._controllers.get(controller_id)
        else:
            controller = self._active_controller()
        if not controller and not allow_missing:
            raise ValueError("local controller is not registered")
        return controller or {"controller_id": self._default_controller_id(), "verified": False, "last_seen_at": None}

    def _local_browser_device(self) -> Dict[str, Any]:
        revoked_at = self._revoked_devices.get("device-ui_local_browser")
        return _device(
            device_id="device-ui_local_browser",
            controller_id="",
            display_name="Local browser",
            channel_type="local_browser",
            local_only=True,
            trusted=revoked_at is None,
            verified=revoked_at is None,
            paired=revoked_at is None,
            created_at=self._phase4_started_at,
            last_seen_at=self._phase4_started_at,
            trust_level="local_session",
            risk_limit="high",
            can_grant_normal=revoked_at is None,
            can_grant_strong=revoked_at is None,
            can_grant_double=revoked_at is None,
            can_grant_triple=False,
            revoked=revoked_at is not None,
            revoked_at=revoked_at,
        )

    def _terminal_device(self) -> Dict[str, Any]:
        verified_at = self._channel_verified_at.get("terminal_local")
        revoked_at = self._revoked_devices.get("device-terminal_local")
        active = bool(verified_at) and revoked_at is None
        return _device(
            device_id="device-terminal_local",
            controller_id="",
            display_name="Local terminal",
            channel_type="local_terminal",
            local_only=True,
            trusted=active,
            verified=active,
            paired=active,
            created_at=self._phase4_started_at,
            last_seen_at=verified_at,
            trust_level="local_challenge_verified" if active else "challenge_required",
            risk_limit="critical" if active else "none",
            can_grant_normal=active,
            can_grant_strong=active,
            can_grant_double=active,
            can_grant_triple=active,
            revoked=revoked_at is not None,
            revoked_at=revoked_at,
        )

    def _controller_device(self, controller: Mapping[str, Any], *, audit_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        if not controller:
            return _device(
                device_id="device-local_controller",
                controller_id="",
                display_name="Local controller",
                channel_type="local_controller",
                local_only=True,
                trusted=False,
                verified=False,
                paired=False,
                created_at=self._phase4_started_at,
                last_seen_at=None,
                trust_level="registration_required",
                risk_limit="none",
                can_grant_normal=False,
                can_grant_strong=False,
                can_grant_double=False,
                can_grant_triple=False,
                revoked=False,
                revoked_at=None,
                audit_ids=audit_ids or [],
            )
        device_id = str(controller.get("device_id") or f"device-{controller.get('controller_id')}")
        revoked_at = self._revoked_devices.get(device_id)
        active = bool(controller.get("trusted") and controller.get("verified") and controller.get("paired")) and revoked_at is None
        return _device(
            device_id=device_id,
            controller_id=str(controller.get("controller_id") or ""),
            display_name=str(controller.get("display_name") or "Local controller"),
            channel_type="local_controller",
            local_only=True,
            trusted=active,
            verified=active,
            paired=active,
            created_at=controller.get("created_at") or self._phase4_started_at,
            last_seen_at=controller.get("last_seen_at"),
            trust_level="local_verified_controller" if active else "verification_required",
            risk_limit="critical" if active else "none",
            can_grant_normal=active,
            can_grant_strong=active,
            can_grant_double=active,
            can_grant_triple=active,
            revoked=revoked_at is not None,
            revoked_at=revoked_at,
            audit_ids=audit_ids or [],
        )

    def _voice_device(self) -> Dict[str, Any]:
        return _device(
            device_id="device-voice_readback_only",
            controller_id="",
            display_name="Voice readback only",
            channel_type="voice_readback",
            local_only=True,
            trusted=False,
            verified=False,
            paired=False,
            created_at=self._phase4_started_at,
            last_seen_at=None,
            trust_level="not_an_approval_channel",
            risk_limit="none",
            can_grant_normal=False,
            can_grant_strong=False,
            can_grant_double=False,
            can_grant_triple=False,
            revoked=False,
            revoked_at=None,
        )

    def _wake_device(self) -> Dict[str, Any]:
        return _device(
            device_id="device-wake_phrase_disabled",
            controller_id="",
            display_name="Wake phrase",
            channel_type="wake_phrase",
            local_only=True,
            trusted=False,
            verified=False,
            paired=False,
            created_at=self._phase4_started_at,
            last_seen_at=None,
            trust_level="not_an_approval_channel",
            risk_limit="none",
            can_grant_normal=False,
            can_grant_strong=False,
            can_grant_double=False,
            can_grant_triple=False,
            revoked=False,
            revoked_at=None,
        )

    def _remote_placeholder_device(self, device_id: str, display_name: str) -> Dict[str, Any]:
        revoked_at = self._revoked_devices.get(device_id)
        return _device(
            device_id=device_id,
            controller_id="",
            display_name=display_name,
            channel_type="remote_future",
            local_only=False,
            trusted=False,
            verified=False,
            paired=False,
            created_at=self._phase4_started_at,
            last_seen_at=None,
            trust_level="remote_pairing_disabled",
            risk_limit="none",
            can_grant_normal=False,
            can_grant_strong=False,
            can_grant_double=False,
            can_grant_triple=False,
            revoked=revoked_at is not None,
            revoked_at=revoked_at,
        )


def _triple_step(step_id: str, phrase: str, expires_at: str, expected_channel_id: str, envelope_status: str) -> Dict[str, Any]:
    return {
        "step_id": step_id,
        "status": "pending" if envelope_status == "pending" else "blocked",
        "channel_id": "",
        "channel_type": "",
        "expected_channel_id": expected_channel_id,
        "confirmation_phrase": phrase,
        "challenge": f"Type {phrase}",
        "readback_required": True,
        "expires_at": expires_at,
        "approved_at": None,
        "approved_by": "",
        "anti_reuse": True,
        "audit_required": True,
    }


def _device(
    *,
    device_id: str,
    controller_id: str,
    display_name: str,
    channel_type: str,
    local_only: bool,
    trusted: bool,
    verified: bool,
    paired: bool,
    created_at: Any,
    last_seen_at: Any,
    trust_level: str,
    risk_limit: str,
    can_grant_normal: bool,
    can_grant_strong: bool,
    can_grant_double: bool,
    can_grant_triple: bool,
    revoked: bool,
    revoked_at: Any,
    audit_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "device_id": device_id,
        "controller_id": controller_id,
        "display_name": display_name,
        "channel_type": channel_type,
        "local_only": local_only,
        "trusted": trusted,
        "verified": verified,
        "paired": paired,
        "created_at": created_at,
        "last_seen_at": last_seen_at,
        "trust_level": trust_level,
        "risk_limit": risk_limit,
        "can_grant_normal": can_grant_normal,
        "can_grant_strong": can_grant_strong,
        "can_grant_double": can_grant_double,
        "can_grant_triple": can_grant_triple,
        "revoked": revoked,
        "revoked_at": revoked_at,
        "audit_ids": audit_ids or [],
    }


def _device_id_for_channel(channel_id: str) -> str:
    return f"device-{channel_id}"


def _browser_check(name: str, passed: bool, notes: str) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "status": "passed" if passed else "failed", "notes": notes}
