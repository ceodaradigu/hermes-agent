from __future__ import annotations

import hashlib
import os
import re
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from jarvis.persistent_audit import PersistentAuditLedger


PHASE_8_SCHEMA_VERSION = "jarvis.phase_8_governed_remote_deploy_email_payments.v1"
REMOTE_CHANNEL_REGISTRY_SCHEMA_VERSION = "jarvis.remote_channel_registry.v1"
TELEGRAM_READINESS_SCHEMA_VERSION = "jarvis.telegram_governed_channel_readiness.v1"
MOBILE_APPROVAL_CENTER_SCHEMA_VERSION = "jarvis.mobile_approval_center_readiness.v1"
EXTERNAL_OPERATION_ENVELOPE_SCHEMA_VERSION = "jarvis.external_operation_envelope.v1"
BUDGET_GUARD_SCHEMA_VERSION = "jarvis.external_cost_budget_guard.v1"
REVENUE_EVENT_SCHEMA_VERSION = "jarvis.revenue_event.v1"

REMOTE_PAIRING_TTL_SECONDS = 180
REMOTE_APPROVAL_INTENT_TTL_SECONDS = 180
REMOTE_APPROVAL_SCOPE = {
    "notification",
    "approval_preview",
    "readback",
    "remote_approval_intent",
    "deny",
    "cancel",
}
REMOTE_CHANNEL_IDS = (
    "telegram",
    "mobile_pwa",
    "local_controller_notifications",
    "remote_approval_center_future",
)
EXTERNAL_CATEGORIES = {"deploy", "email", "payment", "remote"}
SENSITIVE_KEY_RE = re.compile(
    r"(api[_-]?key|authorization|bearer|client[_-]?secret|cookie|credential|cvv|password|private[_-]?key|secret|token)",
    re.IGNORECASE,
)
SENSITIVE_TEXT_RE = re.compile(
    r"(sk_live_[A-Za-z0-9_=-]{8,}|rk_live_[A-Za-z0-9_=-]{8,}|sk_test_[A-Za-z0-9_=-]{8,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|api[_ -]?key|authorization:|bearer |client[_ -]?secret|"
    r"cookie|credential|password|private[_ -]?key|secret|token)",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
STRIPE_TEST_KEY_RE = re.compile(r"\b(?:sk|rk)_test_[A-Za-z0-9_=-]{8,}\b")
STRIPE_LIVE_KEY_RE = re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9_=-]{8,}\b")


@dataclass(frozen=True)
class ExternalOperationEnvelope:
    operation_id: str
    category: str
    provider: str
    actor: str
    requested_by_channel: str
    risk: str
    side_effects: List[str]
    cost_estimate: Dict[str, Any]
    approval_level: str
    readback_text: str
    rollback_or_compensation_plan: str
    status: str
    audit_id: str
    created_at: str
    expires_at: str
    evidence: Dict[str, Any]
    challenge_phrase: str
    execution_enabled: bool = False
    prepare_only: bool = True
    approval_required: bool = True
    remote_approval_intent_allowed: bool = True
    hermes_called: bool = False
    provider_called: bool = False
    frontend_direct_hermes_allowed: bool = False
    metadata_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["side_effects"] = list(self.side_effects)
        data["cost_estimate"] = dict(self.cost_estimate)
        data["evidence"] = dict(self.evidence)
        data["schema_version"] = EXTERNAL_OPERATION_ENVELOPE_SCHEMA_VERSION
        return data


class Phase8GovernedRemoteExternalOpsControlPlane:
    """Governed remote/deploy/email/payment readiness without provider execution.

    JARVIS owns the remote intent, risk, approval, budget and audit contract.
    Hermes and external providers are never called from this control plane.
    """

    def __init__(
        self,
        *,
        identity_control: Any,
        audit_ledger: Optional[PersistentAuditLedger] = None,
        clock: Any = None,
    ) -> None:
        self.identity_control = identity_control
        self.audit_ledger = audit_ledger or PersistentAuditLedger.from_environment()
        self.clock = clock or _now_iso
        self._remote_kill_switch_enabled = False
        self._operations: Dict[str, ExternalOperationEnvelope] = {}
        self._remote_decisions: List[Dict[str, Any]] = []

    def phase_8_status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        audit = self._audit(
            "phase_8_status_read",
            surface="phase_8",
            risk_level="low",
            approval_level="direct",
            metadata={"route_count": len(routes), "metadata_only": True},
        )
        return {
            "schema_version": PHASE_8_SCHEMA_VERSION,
            "phase": "Phase 8",
            "title": "PR #173 -- Governed Remote Channels, Deploy, Email & Payments",
            "status": "implemented_as_governed_readiness_and_prepare_only_pilot",
            "implemented_blocks": {
                "remote_channel_registry_v1": True,
                "telegram_readiness_pilot_v1": True,
                "mobile_approval_center_readiness_v1": True,
                "deploy_provider_candidate_v1": True,
                "email_provider_candidate_v1": True,
                "payments_stripe_candidate_v1": True,
                "budget_guard_v1": True,
                "external_operation_envelope_v1": True,
                "voice_approval_external_operation_contract": True,
                "dashboard_event_stream_phase_8": True,
            },
            "route_readiness": {
                "phase_8_status": "/mark-3/phase-8/status" in routes,
                "remote_channels_status": "/mark-3/remote-channels/status" in routes,
                "telegram_readiness_status": "/mark-3/telegram-readiness/status" in routes,
                "mobile_approval_center_status": "/mark-3/mobile-approval-center/status" in routes,
                "external_operations_status": "/mark-3/external-operations/status" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "remote_channels": self.remote_channels_status(audit_read=False),
            "telegram": self.telegram_readiness_status(audit_read=False),
            "mobile_approval_center": self.mobile_approval_center_status(audit_read=False),
            "external_operations": self.external_operations_status(audit_read=False),
            "budget_guard": self.evaluate_budget_guard(audit_read=False),
            "security_gates": {
                "jarvis_governs": True,
                "hermes_executes_only_after_jarvis": True,
                "remote_channels_call_hermes_directly": False,
                "frontend_can_execute_hermes_directly": False,
                "remote_execution_enabled_by_default": False,
                "public_internet_exposure_default": False,
                "telegram_bot_autostart": False,
                "provider_calls_enabled_by_default": False,
                "live_money_movement_enabled": False,
                "production_deploy_enabled_by_default": False,
                "real_email_send_enabled_by_default": False,
                "memory_grants_permission": False,
                "wake_phrase_can_approve": False,
                "fake_revenue_allowed": False,
            },
            "real_vs_readiness": {
                "real": [
                    "deterministic provider readiness detection without secret disclosure",
                    "metadata-only audit events",
                    "local remote-channel pairing contract",
                    "prepare-only external operation envelopes",
                    "budget and revenue evidence validation",
                ],
                "readiness": [
                    "Telegram bot runtime is not started",
                    "mobile/PWA approval center is preview/readback/challenge contract",
                    "deploy/email/payment execution remains disabled",
                    "rollback is declared only when an actual provider rollback exists",
                ],
            },
            "recent_operation_count": len(self._operations),
            "recent_remote_decision_count": len(self._remote_decisions),
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
            "source_endpoint": "/mark-3/phase-8/status",
        }

    def remote_channels_status(self, *, audit_read: bool = True) -> Dict[str, Any]:
        if audit_read:
            self._audit("remote_channel_status_read", surface="remote_channels", metadata={"metadata_only": True})
        devices = self._trusted_devices()
        remote_devices = [item for item in devices if not bool(item.get("local_only")) and not bool(item.get("revoked"))]
        channels = [self._channel_status(channel_id, devices) for channel_id in REMOTE_CHANNEL_IDS]
        return {
            "schema_version": REMOTE_CHANNEL_REGISTRY_SCHEMA_VERSION,
            "status": "remote_channels_registered_disabled_by_default",
            "remote_kill_switch": {
                "enabled": self._remote_kill_switch_enabled,
                "blocks_notifications": self._remote_kill_switch_enabled,
                "blocks_remote_approval_intents": self._remote_kill_switch_enabled,
                "blocks_remote_execution": True,
            },
            "defaults": {
                "remote_execution_enabled": False,
                "public_internet_exposure": False,
                "hidden_background_listener": False,
                "approve_all_forever_allowed": False,
                "frontend_or_remote_direct_hermes": False,
            },
            "requirements": {
                "trusted_device_binding": True,
                "pairing_required": True,
                "revocation_supported": True,
                "rate_limit": {
                    "max_failed_attempts": 3,
                    "lockout_seconds": 120,
                },
                "anti_replay": True,
                "approval_scope_expires": True,
                "exact_readback_required": True,
                "challenge_required": True,
                "audit_required": True,
            },
            "channels": channels,
            "trusted_remote_device_count": len(remote_devices),
            "recent_remote_decisions": list(self._remote_decisions[-10:]),
            "metadata_only": True,
            "source_endpoint": "/mark-3/remote-channels/status",
        }

    def telegram_readiness_status(self, *, audit_read: bool = True) -> Dict[str, Any]:
        if audit_read:
            self._audit(
                "telegram_readiness_checked",
                surface="telegram",
                metadata={"token_present": _token_present(), "token_value_exposed": False},
            )
        enabled = _env_bool("JARVIS_PHASE8_TELEGRAM_ENABLED")
        token_present = _token_present()
        allowed_users_present = bool(os.getenv("TELEGRAM_ALLOWED_USERS", "").strip())
        webhook_url_present = bool(os.getenv("TELEGRAM_WEBHOOK_URL", "").strip())
        webhook_secret_present = bool(os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip())
        mode = "webhook" if webhook_url_present else "polling_contract"
        ready = bool(enabled and token_present and allowed_users_present and not self._remote_kill_switch_enabled)
        return {
            "schema_version": TELEGRAM_READINESS_SCHEMA_VERSION,
            "provider": "telegram",
            "provider_status": "manual_pilot_ready" if ready else "disabled_by_default_or_incomplete",
            "enabled_by_config": enabled,
            "disabled_by_default": not enabled,
            "token_present": token_present,
            "token_source": "env:TELEGRAM_BOT_TOKEN" if token_present else "missing",
            "token_value_exposed": False,
            "token_printed": False,
            "allowed_users_configured": allowed_users_present,
            "allow_all_users_enabled": _env_bool("TELEGRAM_ALLOW_ALL_USERS"),
            "webhook": {
                "configured": webhook_url_present,
                "secret_present": webhook_secret_present,
                "url_value_exposed": False,
                "public_internet_exposure_default": False,
            },
            "polling": {
                "supported_by_existing_gateway_adapter": True,
                "auto_started_by_phase_8": False,
                "mode": mode,
            },
            "allowed_operations": [
                "notify_approval_pending",
                "notify_action_blocked",
                "notify_deploy_candidate",
                "notify_email_candidate",
                "notify_payment_candidate",
                "receive_approval_intent_if_paired_trusted_challenged",
                "deny_intent",
                "cancel_intent",
            ],
            "blocked_operations": [
                "remote_execute",
                "free_shell",
                "direct_hermes_call",
                "approve_all_forever",
                "provider_secret_read",
            ],
            "runtime": {
                "bot_started": False,
                "webhook_opened": False,
                "polling_started": False,
                "external_api_called": False,
                "credentials_stored": False,
            },
            "remote_kill_switch_enabled": self._remote_kill_switch_enabled,
            "metadata_only": True,
            "source_endpoint": "/mark-3/telegram-readiness/status",
        }

    def mobile_approval_center_status(self, *, audit_read: bool = True) -> Dict[str, Any]:
        if audit_read:
            self._audit("remote_channel_status_read", surface="mobile_approval_center", metadata={"metadata_only": True})
        return {
            "schema_version": MOBILE_APPROVAL_CENTER_SCHEMA_VERSION,
            "status": "mobile_pwa_approval_center_readiness",
            "mode": "preview_readback_challenge_only",
            "can_preview_remote_approval": True,
            "can_show_readback": True,
            "can_show_risk_cost_scope": True,
            "can_show_challenge_phrase": True,
            "can_deny_or_cancel_intent": True,
            "can_approve_real_actions": False,
            "can_execute": False,
            "can_call_hermes_directly": False,
            "can_access_git_filesystem_browser": False,
            "requirements": {
                "device_identity": True,
                "pairing_required": True,
                "revocation_supported": True,
                "expiration_required": True,
                "anti_replay": True,
                "audit_trail": True,
                "scope_exact_match": True,
            },
            "preview_fields": [
                "operation_id",
                "category",
                "provider",
                "risk",
                "cost_estimate",
                "scope",
                "readback_text",
                "challenge_phrase",
                "rollback_or_compensation_plan",
                "expires_at",
            ],
            "remote_kill_switch_enabled": self._remote_kill_switch_enabled,
            "metadata_only": True,
            "source_endpoint": "/mark-3/mobile-approval-center/status",
        }

    def external_operations_status(self, *, audit_read: bool = True) -> Dict[str, Any]:
        if audit_read:
            self._audit("phase_8_status_read", surface="external_operations", metadata={"metadata_only": True})
        return {
            "schema_version": PHASE_8_SCHEMA_VERSION,
            "status": "prepare_only_external_operation_contracts_ready",
            "execution_enabled": False,
            "provider_calls_enabled": False,
            "deploy": {
                "available": True,
                "dry_run_default": True,
                "production_deploy_default": False,
                "dns_changes_enabled": False,
                "secret_reads_enabled": False,
            },
            "email": {
                "available": True,
                "draft_default": True,
                "send_enabled_by_default": False,
                "mass_email_enabled": False,
                "contact_scraping_enabled": False,
            },
            "payments": {
                "available": True,
                "stripe_readiness": self.payment_provider_readiness(),
                "live_mode_blocked_by_default": True,
                "money_movement_enabled": False,
                "fake_revenue_allowed": False,
            },
            "operation_count": len(self._operations),
            "recent_operations": [item.to_dict() for item in list(self._operations.values())[-5:]],
            "metadata_only": True,
            "source_endpoint": "/mark-3/external-operations/status",
        }

    def set_remote_kill_switch(self, *, enabled: bool, actor: str = "David", reason: str = "operator request") -> Dict[str, Any]:
        self._remote_kill_switch_enabled = bool(enabled)
        audit = self._audit(
            "remote_kill_switch_changed",
            surface="remote_channels",
            risk_level="high",
            approval_level="direct",
            metadata={"enabled": self._remote_kill_switch_enabled, "actor": _safe_text(actor), "reason": _safe_text(reason)},
        )
        return {
            "schema_version": REMOTE_CHANNEL_REGISTRY_SCHEMA_VERSION,
            "remote_kill_switch": "enabled" if self._remote_kill_switch_enabled else "disabled",
            "remote_execution_allowed": False,
            "audit_id": audit.get("audit_id", ""),
            "channels": self.remote_channels_status(audit_read=False),
        }

    def create_remote_pairing_challenge(self, **values: Any) -> Dict[str, Any]:
        channel_id = _channel_id(values.get("channel_id") or values.get("channel") or "mobile_pwa")
        if channel_id not in REMOTE_CHANNEL_IDS:
            raise ValueError("unsupported remote channel")
        scope = _safe_scope(values.get("scope") or ["notification", "approval_preview", "readback", "remote_approval_intent", "deny", "cancel"])
        if self._remote_kill_switch_enabled:
            return {
                "schema_version": REMOTE_CHANNEL_REGISTRY_SCHEMA_VERSION,
                "pairing_status": "blocked",
                "reason": "remote_kill_switch_enabled",
                "remote_execution_allowed": False,
                "metadata_only": True,
            }
        result = self.identity_control.phase5_store.create_pairing_challenge(
            display_name=_safe_text(values.get("display_name"), f"{channel_id} device"),
            public_identifier=_safe_text(values.get("public_identifier"), "remote-device-public-id"),
            channel=channel_id,
            scope=scope,
            capabilities={
                "can_receive_notifications": True,
                "remote_approval_intent": True,
                "can_execute": False,
                "direct_hermes": False,
            },
            ttl_seconds=min(int(values.get("ttl_seconds") or REMOTE_PAIRING_TTL_SECONDS), REMOTE_PAIRING_TTL_SECONDS),
            risk_limit="high",
            metadata={"phase": "8", "remote_channel": channel_id},
        )
        audit = self._audit(
            "remote_channel_pairing_challenge_created",
            surface="remote_channels",
            risk_level="medium",
            approval_level="direct",
            metadata={"channel_id": channel_id, "challenge_id": result.get("challenge_id"), "scope": scope},
        )
        result.update({
            "channel_id": channel_id,
            "remote_approval_allowed": False,
            "remote_approval_intent_after_pairing": True,
            "remote_execution_allowed": False,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        })
        return result

    def verify_remote_pairing_challenge(self, **values: Any) -> Dict[str, Any]:
        channel_id = _channel_id(values.get("channel_id") or values.get("channel") or "mobile_pwa")
        scope = _safe_scope(values.get("scope") or ["notification", "approval_preview", "readback", "remote_approval_intent", "deny", "cancel"])
        result = self.identity_control.phase5_store.verify_pairing_challenge(
            challenge_id=str(values.get("challenge_id") or ""),
            nonce=str(values.get("nonce") or ""),
            response_phrase=str(values.get("response_phrase") or ""),
            public_identifier=str(values.get("public_identifier") or ""),
            display_name=_safe_text(values.get("display_name"), f"{channel_id} device"),
            scope=scope,
        )
        if result.get("pairing_status") == "trusted_device_bound":
            device_id = result["device"]["device_id"]
            remote_device = self.identity_control.phase5_store.upsert_trusted_device(
                device_id=device_id,
                display_name=result["device"].get("display_name") or f"{channel_id} device",
                channel_type=channel_id,
                public_identifier=str(values.get("public_identifier") or device_id),
                fingerprint_material=f"phase8:{channel_id}:{values.get('challenge_id')}:{values.get('nonce')}",
                capabilities={
                    "can_receive_notifications": True,
                    "remote_approval_intent": True,
                    "can_execute": False,
                    "direct_hermes": False,
                    "can_grant_normal": False,
                    "can_grant_strong": False,
                    "can_grant_double": False,
                    "can_grant_triple": False,
                },
                approval_scope=scope,
                metadata={"phase": "8", "channel_id": channel_id, "remote_execution_allowed": False},
                trust_source="phase8_remote_pairing_challenge",
                paired_challenge_id=str(values.get("challenge_id") or ""),
                local_only=False,
            )
            result["device"] = remote_device
            event = "remote_channel_pairing_challenge_consumed"
        else:
            event = "remote_channel_pairing_challenge_failed"
        audit = self._audit(
            event,
            surface="remote_channels",
            risk_level="medium",
            approval_level="direct" if event.endswith("consumed") else "blocked",
            metadata={
                "channel_id": channel_id,
                "challenge_id": _safe_text(values.get("challenge_id")),
                "pairing_status": result.get("pairing_status"),
                "reason": result.get("reason", ""),
            },
        )
        result.update({
            "channel_id": channel_id,
            "remote_approval_allowed": result.get("pairing_status") == "trusted_device_bound",
            "remote_execution_allowed": False,
            "direct_hermes_allowed": False,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        })
        return result

    def revoke_remote_device(self, *, device_id: str, actor: str = "David", reason: str = "operator revoke") -> Dict[str, Any]:
        device = self.identity_control.phase5_store.revoke_device(device_id, reason=reason)
        audit = self._audit(
            "remote_channel_revoked",
            surface="remote_channels",
            risk_level="medium",
            approval_level="direct",
            metadata={"device_id": _safe_text(device_id), "actor": _safe_text(actor), "reason": _safe_text(reason)},
        )
        return {
            "schema_version": REMOTE_CHANNEL_REGISTRY_SCHEMA_VERSION,
            "device": _public_device(device),
            "remote_approval_allowed": False,
            "remote_execution_allowed": False,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def prepare_deploy_candidate(self, **values: Any) -> Dict[str, Any]:
        provider = _safe_text(values.get("provider"), "unknown")
        environment = _choice(values.get("environment"), {"preview", "staging", "production"}, "preview")
        target = _safe_text(values.get("target"), _safe_text(values.get("project_name"), "unspecified target"))
        cost = _cost_estimate(values.get("cost_estimate"), values.get("currency", "USD"))
        production = environment == "production" or bool(values.get("production"))
        risk = "critical" if production else "high" if values.get("external_network_enabled") else "medium"
        approval_level = "triple" if production else "strong"
        rollback = _safe_text(values.get("rollback_plan") or values.get("rollback_or_stop_plan"), "")
        rollback_available = bool(values.get("rollback_available")) and bool(rollback)
        blocked = []
        if production:
            blocked.append("production deploy disabled by default")
        if not rollback:
            blocked.append("rollback or restore plan required")
        if cost["known"] is False:
            blocked.append("unknown provider cost requires strong approval")
        candidate = {
            "candidate_id": f"deploy-{uuid4()}",
            "category": "deploy",
            "provider": provider,
            "project_or_app_id_redacted": _redacted_identifier(values.get("project_id") or values.get("app_id") or target),
            "environment": environment,
            "target": target,
            "diff_or_build_summary": _safe_text(values.get("diff_summary") or values.get("build_summary"), "operator build/diff summary required"),
            "required_secrets_checklist": _safe_list(values.get("required_secrets_checklist")) or ["secret names only; values must not be read"],
            "cost_estimate": cost,
            "rollback": {
                "available": rollback_available,
                "plan": rollback if rollback else "not available until operator provides a real rollback or restore plan",
                "fake_rollback": False,
            },
            "risk_level": risk,
            "approval_level_required": approval_level,
            "dry_run_default": True,
            "prepare_only": True,
            "would_deploy": False,
            "would_call_provider": False,
            "would_change_dns": False,
            "would_read_secrets": False,
            "execution_enabled": False,
            "blocked_reasons": _dedupe(blocked),
        }
        return self._candidate_response(candidate, actor=values.get("actor"), requested_by_channel=values.get("requested_by_channel", "local_api"))

    def prepare_email_candidate(self, **values: Any) -> Dict[str, Any]:
        operation = _choice(values.get("operation"), {"draft", "test_send", "send", "campaign"}, "draft")
        recipients = values.get("recipients") if isinstance(values.get("recipients"), list) else []
        bulk = bool(values.get("bulk_or_marketing") or operation == "campaign" or len(recipients) > 10)
        personal_identity = bool(values.get("personal_identity_use") or values.get("identity_use"))
        send_requested = operation in {"test_send", "send", "campaign"} or bool(values.get("send_requested"))
        risk = "critical" if bulk and send_requested else "high" if personal_identity or send_requested else "medium"
        approval_level = "triple" if bulk and send_requested else "strong" if personal_identity or send_requested else "normal"
        blocked = []
        if send_requested:
            blocked.append("email send disabled by default")
        if bulk:
            blocked.append("campaign envelope and compliance checklist required")
        candidate = {
            "candidate_id": f"email-{uuid4()}",
            "category": "email",
            "provider": _safe_text(values.get("provider"), "unknown"),
            "operation": operation,
            "recipients_summary": _recipient_summary(recipients),
            "subject_preview": _redact_text(values.get("subject") or values.get("subject_summary") or "subject not provided"),
            "body_preview": _redact_text(values.get("body") or values.get("body_summary") or "body not provided"),
            "attachment_metadata_only": _attachment_metadata(values.get("attachments")),
            "identity_use_warning": "personal identity use requires strong approval" if personal_identity else "sender identity must be reviewed before send",
            "unsubscribe_compliance_checklist": _campaign_checklist(bulk),
            "cost_rate_limit_metadata": {
                "estimated_cost": _cost_estimate(values.get("cost_estimate"), values.get("currency", "USD")),
                "rate_limit": _safe_text(values.get("rate_limit"), "provider rate limit unknown"),
                "unknown_cost_blocks_or_requires_strong_approval": values.get("cost_estimate") in (None, "", "unknown"),
            },
            "risk_level": risk,
            "approval_level_required": approval_level,
            "send_disabled_by_default": True,
            "test_mode_only": operation == "test_send",
            "would_send_email": False,
            "would_call_provider": False,
            "would_scrape_contacts": False,
            "prepare_only": True,
            "blocked_reasons": _dedupe(blocked),
        }
        return self._candidate_response(candidate, actor=values.get("actor"), requested_by_channel=values.get("requested_by_channel", "local_api"))

    def payment_provider_readiness(self) -> Dict[str, Any]:
        test_key = _first_env("STRIPE_TEST_SECRET_KEY", "STRIPE_TEST_API_KEY")
        live_key = _first_env("STRIPE_LIVE_SECRET_KEY", "STRIPE_LIVE_API_KEY")
        generic_key = _first_env("STRIPE_SECRET_KEY", "STRIPE_API_KEY")
        generic_mode = "live" if generic_key and STRIPE_LIVE_KEY_RE.search(generic_key) else "test" if generic_key and STRIPE_TEST_KEY_RE.search(generic_key) else "unknown"
        return {
            "provider": "stripe",
            "test_mode_key_present": bool(test_key) or generic_mode == "test",
            "live_mode_key_present": bool(live_key) or generic_mode == "live",
            "unknown_mode_key_present": bool(generic_key and generic_mode == "unknown"),
            "mode_detected": "live" if live_key or generic_mode == "live" else "test" if test_key or generic_mode == "test" else "not_configured",
            "api_key_value_exposed": False,
            "api_key_logged": False,
            "api_called": False,
            "checkout_creation_enabled": False,
            "live_mode_blocked_by_default": True,
            "money_movement_enabled": False,
        }

    def prepare_payment_candidate(self, **values: Any) -> Dict[str, Any]:
        readiness = self.payment_provider_readiness()
        explicit_mode = _choice(values.get("stripe_mode") or values.get("mode"), {"test", "live", "unknown"}, "unknown")
        mode = explicit_mode if explicit_mode != "unknown" else readiness["mode_detected"]
        amount = _money(values.get("amount"))
        recurring = bool(values.get("recurring") or str(values.get("billing_interval") or "").lower() not in {"", "unknown", "one_time", "one-time"})
        live = mode == "live"
        money_movement = bool(values.get("money_movement_requested") or values.get("charge_requested") or live)
        approval_level = "triple" if live or money_movement else "strong"
        blocked = []
        if live:
            blocked.append("Stripe live mode blocked by default")
        if money_movement:
            blocked.append("money movement disabled by default")
        if amount is None:
            blocked.append("amount must be explicit for payment candidate")
        candidate = {
            "candidate_id": f"payment-{uuid4()}",
            "category": "payment",
            "provider": "stripe",
            "provider_readiness": readiness,
            "stripe_mode": mode,
            "live_mode": live,
            "product_or_price_candidate": {
                "product_name": _safe_text(values.get("product_name"), "unnamed product"),
                "price_reference_redacted": _redacted_identifier(values.get("price_id") or values.get("price_reference") or "not provided"),
                "recommended_future_api": "Checkout Sessions + Billing APIs" if recurring else "Checkout Sessions",
            },
            "amount": amount,
            "currency": _currency(values.get("currency")),
            "recurring": recurring,
            "test_mode_candidate_allowed_without_money_movement": bool(mode == "test" and not money_movement),
            "approval_level_required": approval_level,
            "risk_level": "critical" if live or money_movement else "high",
            "would_call_stripe": False,
            "would_create_checkout": False,
            "would_move_money": False,
            "would_create_payout": False,
            "would_issue_refund": False,
            "prepare_only": True,
            "blocked_reasons": _dedupe(blocked),
        }
        return self._candidate_response(candidate, actor=values.get("actor"), requested_by_channel=values.get("requested_by_channel", "local_api"))

    def record_revenue_event(self, **values: Any) -> Dict[str, Any]:
        projected = _money(values.get("projected_revenue"))
        confirmed = _money(values.get("confirmed_revenue"))
        gross = _money(values.get("gross"))
        fees = _money(values.get("fees")) or 0.0
        net = _money(values.get("net"))
        evidence = _safe_list(values.get("evidence")) or _safe_list(values.get("source"))
        event_status = "projected_only"
        blocked_reasons: List[str] = []
        if confirmed is not None and not evidence:
            event_status = "rejected_fake_revenue"
            blocked_reasons.append("confirmed revenue requires evidence/source")
            confirmed = None
        elif confirmed is not None:
            event_status = "confirmed_with_evidence"
        if gross is not None and net is None:
            net = gross - fees
        audit = self._audit(
            "revenue_event_recorded",
            surface="payments",
            risk_level="high" if confirmed is not None else "medium",
            approval_level="strong" if confirmed is not None else "normal",
            metadata={"status": event_status, "confirmed": confirmed is not None, "evidence_count": len(evidence)},
        )
        return {
            "schema_version": REVENUE_EVENT_SCHEMA_VERSION,
            "revenue_event_id": f"rev-{uuid4()}",
            "status": event_status,
            "projected_revenue": projected,
            "confirmed_revenue": confirmed,
            "gross": gross,
            "fees": fees if gross is not None else None,
            "net": net,
            "evidence": evidence,
            "source": _safe_text(values.get("source"), "missing" if not evidence else "operator_provided"),
            "projected_is_not_confirmed": True,
            "no_fake_revenue": True,
            "blocked_reasons": blocked_reasons,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def evaluate_budget_guard(self, *, audit_read: bool = True, **values: Any) -> Dict[str, Any]:
        monthly_budget = _money(values.get("monthly_budget"))
        per_action_max = _money(values.get("per_action_max_cost"))
        estimate = _money(values.get("provider_cost_estimate"))
        confirmed_this_month = _money(values.get("confirmed_spend_this_month")) or 0.0
        spending_requested = bool(values.get("spending_requested", estimate is not None and estimate > 0))
        explicit_approval = bool(values.get("explicit_approval_present"))
        evidence = _safe_list(values.get("confirmed_spend_evidence"))
        violations: List[str] = []
        decision = "allowed_prepare_only"
        if estimate is None and spending_requested:
            decision = "blocked_unknown_cost"
            violations.append("unknown provider cost blocks or requires strong approval")
        if estimate is not None and per_action_max is not None and estimate > per_action_max:
            decision = "blocked_over_per_action_limit"
            violations.append("provider cost estimate exceeds per-action max")
        remaining = monthly_budget - confirmed_this_month if monthly_budget is not None else None
        if estimate is not None and remaining is not None and estimate > remaining:
            decision = "blocked_over_monthly_budget"
            violations.append("provider cost estimate exceeds remaining monthly budget")
        if spending_requested and not explicit_approval:
            decision = "requires_explicit_approval" if not violations else decision
            violations.append("spending requires explicit approval")
        consumed = confirmed_this_month if evidence else 0.0
        if confirmed_this_month and not evidence:
            violations.append("budget consumed only by confirmed evidence, not estimates or claims")
        if audit_read:
            self._audit(
                "budget_guard_evaluated",
                surface="budget_guard",
                risk_level="high" if violations else "medium",
                approval_level="strong" if violations else "normal",
                metadata={"decision": decision, "violation_count": len(violations), "spending_requested": spending_requested},
            )
        return {
            "schema_version": BUDGET_GUARD_SCHEMA_VERSION,
            "decision": decision,
            "can_spend": False,
            "monthly_budget": monthly_budget,
            "per_action_max_cost": per_action_max,
            "provider_cost_estimate": estimate,
            "confirmed_spend_this_month": confirmed_this_month,
            "budget_consumed": consumed,
            "budget_consumed_only_by_confirmed_evidence": True,
            "estimates_consume_budget": False,
            "remaining_budget": monthly_budget - consumed if monthly_budget is not None else None,
            "violations": _dedupe(violations),
            "unknown_cost_blocks_or_requires_strong_approval": estimate is None and spending_requested,
            "explicit_approval_required_for_spending": True,
            "metadata_only": True,
            "source_endpoint": "/mark-3/external-operations/budget-guard",
        }

    def receive_remote_approval_intent(self, **values: Any) -> Dict[str, Any]:
        operation_id = str(values.get("operation_id") or "")
        decision = _choice(values.get("decision"), {"approve", "deny", "cancel"}, "approve")
        channel_id = _channel_id(values.get("channel_id") or "mobile_pwa")
        device_id = str(values.get("device_id") or "")
        envelope = self._operations.get(operation_id)
        reason = ""
        accepted = False
        if self._remote_kill_switch_enabled:
            reason = "remote_kill_switch_enabled"
        elif envelope is None:
            reason = "operation_not_found"
        elif _expired(envelope.expires_at):
            reason = "operation_expired"
        elif channel_id not in {"telegram", "mobile_pwa", "remote_approval_center_future"}:
            reason = "channel_not_approval_capable"
        elif not _trusted_remote_device(self.identity_control.phase5_store.get_device(device_id)):
            reason = "paired_trusted_non_revoked_device_required"
        elif str(values.get("challenge_phrase") or "") != envelope.challenge_phrase:
            reason = "exact_challenge_required"
        elif _normalize_readback(values.get("readback_text")) != _normalize_readback(envelope.readback_text):
            reason = "exact_readback_required"
        else:
            accepted = True
        event = "remote_approval_intent_received" if accepted else "remote_approval_intent_rejected"
        audit = self._audit(
            event,
            surface="remote_approval",
            risk_level=envelope.risk if envelope else "high",
            approval_level=envelope.approval_level if envelope else "blocked",
            metadata={"operation_id": operation_id, "decision": decision, "channel_id": channel_id, "device_id": _safe_text(device_id), "reason": reason},
        )
        result = {
            "schema_version": REMOTE_CHANNEL_REGISTRY_SCHEMA_VERSION,
            "operation_id": operation_id,
            "decision": decision,
            "channel_id": channel_id,
            "device_id": _safe_text(device_id),
            "intent_status": "accepted_pending_local_approval_bridge" if accepted and decision == "approve" else "accepted_cancelled_or_denied" if accepted else "rejected",
            "accepted": accepted,
            "reason": reason,
            "approval_gateway_called": False,
            "approval_granted": False,
            "execution_allowed": False,
            "hermes_called": False,
            "anti_replay_metadata_only": True,
            "expires_at": envelope.expires_at if envelope else "",
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }
        self._remote_decisions.append(result)
        return result

    def voice_approval_external_operation_readiness(self, *, operation_id: str, device_id: str = "", active_voice_session: bool = False) -> Dict[str, Any]:
        envelope = self._operations.get(operation_id)
        eligible = bool(
            envelope
            and not _expired(envelope.expires_at)
            and envelope.approval_level in {"normal", "strong"}
            and active_voice_session
            and _trusted_device(self.identity_control.phase5_store.get_device(device_id))
        )
        return {
            "schema_version": PHASE_8_SCHEMA_VERSION,
            "operation_id": operation_id,
            "voice_approval_available": eligible,
            "requires_active_voice_session": True,
            "requires_trusted_device": True,
            "requires_exact_readback": True,
            "requires_spoken_challenge": True,
            "wake_phrase_can_approve": False,
            "higher_risk_requires_double_or_triple": bool(envelope and envelope.approval_level in {"double", "triple"}),
            "approval_level": envelope.approval_level if envelope else "unknown",
            "risk": envelope.risk if envelope else "unknown",
            "metadata_only": True,
        }

    def _candidate_response(self, candidate: Dict[str, Any], *, actor: Any = None, requested_by_channel: Any = "local_api") -> Dict[str, Any]:
        audit = self._audit(
            "external_operation_candidate_prepared",
            surface=candidate["category"],
            risk_level=candidate.get("risk_level", "medium"),
            approval_level=candidate.get("approval_level_required", "normal"),
            metadata={"candidate_id": candidate.get("candidate_id"), "category": candidate.get("category"), "provider": candidate.get("provider")},
        )
        envelope = self._build_envelope(candidate, actor=_safe_text(actor, "David"), requested_by_channel=_safe_text(requested_by_channel, "local_api"))
        return {
            "schema_version": PHASE_8_SCHEMA_VERSION,
            "candidate": candidate,
            "envelope": envelope.to_dict(),
            "audit_id": audit.get("audit_id", ""),
            "prepare_only": True,
            "execution_enabled": False,
            "hermes_called": False,
            "provider_called": False,
            "metadata_only": True,
        }

    def _build_envelope(self, candidate: Dict[str, Any], *, actor: str, requested_by_channel: str) -> ExternalOperationEnvelope:
        operation_id = f"op-{uuid4()}"
        category = candidate.get("category", "remote")
        risk = candidate.get("risk_level", "medium")
        approval_level = candidate.get("approval_level_required", "normal")
        cost = candidate.get("cost_estimate") or candidate.get("cost_rate_limit_metadata", {}).get("estimated_cost") or {"amount": None, "currency": "unknown", "known": False}
        readback = _readback_for_candidate(candidate, operation_id)
        expires_at = _after_seconds(REMOTE_APPROVAL_INTENT_TTL_SECONDS)
        challenge = f"JARVIS-{secrets.token_hex(3).upper()}"
        audit = self._audit(
            "external_operation_envelope_created",
            surface=category,
            risk_level=risk,
            approval_level=approval_level,
            metadata={"operation_id": operation_id, "provider": candidate.get("provider"), "expires_at": expires_at},
        )
        envelope = ExternalOperationEnvelope(
            operation_id=operation_id,
            category=category,
            provider=_safe_text(candidate.get("provider"), "unknown"),
            actor=actor,
            requested_by_channel=requested_by_channel,
            risk=risk,
            side_effects=_side_effects_for_candidate(candidate),
            cost_estimate=dict(cost),
            approval_level=approval_level,
            readback_text=readback,
            rollback_or_compensation_plan=_rollback_for_candidate(candidate),
            status="awaiting_approval",
            audit_id=audit.get("audit_id", ""),
            created_at=self.clock(),
            expires_at=expires_at,
            evidence={
                "required": True,
                "source": "operator_or_provider_evidence_required_before_confirming_result",
                "projected_is_not_confirmed": True,
            },
            challenge_phrase=challenge,
        )
        self._operations[operation_id] = envelope
        return envelope

    def _channel_status(self, channel_id: str, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        trusted = [item for item in devices if item.get("channel_type") == channel_id and item.get("trusted") and not item.get("revoked")]
        base = {
            "channel_id": channel_id,
            "trusted_device_count": len(trusted),
            "trusted_device_binding": True,
            "pairing_required": True,
            "revocation_supported": True,
            "rate_limit": True,
            "anti_replay": True,
            "remote_kill_switch_enabled": self._remote_kill_switch_enabled,
            "execution_capable": False,
            "execution_enabled": False,
            "direct_hermes_allowed": False,
            "approval_scope": "scoped_expiring_intent_only",
        }
        if channel_id == "telegram":
            telegram = self.telegram_readiness_status(audit_read=False)
            return {
                **base,
                "display_name": "Telegram",
                "status": telegram["provider_status"],
                "notification_capable": bool(telegram["token_present"] and telegram["allowed_users_configured"] and not self._remote_kill_switch_enabled),
                "approval_capable": bool(trusted and not self._remote_kill_switch_enabled),
                "provider_token_present": telegram["token_present"],
                "provider_token_exposed": False,
                "bot_started": False,
            }
        if channel_id == "mobile_pwa":
            return {
                **base,
                "display_name": "Mobile / PWA",
                "status": "readiness_preview",
                "notification_capable": False,
                "approval_capable": bool(trusted and not self._remote_kill_switch_enabled),
                "pwa_runtime_connected": False,
            }
        if channel_id == "local_controller_notifications":
            return {
                **base,
                "display_name": "Local Controller Notifications",
                "status": "local_metadata_notification_ready",
                "notification_capable": True,
                "approval_capable": False,
            }
        return {
            **base,
            "display_name": "Future Remote Approval Center",
            "status": "future_gated",
            "notification_capable": False,
            "approval_capable": False,
        }

    def _trusted_devices(self) -> List[Dict[str, Any]]:
        try:
            return list(self.identity_control.phase5_store.list_devices())
        except AttributeError:
            return []

    def _audit(self, event_type: str, *, surface: str = "phase_8", risk_level: str = "low", approval_level: str = "direct", metadata: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        return self.audit_ledger.record(
            event_type=event_type,
            surface=surface,
            source="jarvis_phase_8",
            risk_level=risk_level,
            approval_level=approval_level,
            metadata={**dict(metadata or {}), "phase": "8", "metadata_only": True, "hermes_called": False},
            hermes_dispatch_allowed=False,
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _after_seconds(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=max(1, int(seconds)))).isoformat()


def _expired(expires_at: str) -> bool:
    try:
        return datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc)
    except ValueError:
        return True


def _env_bool(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _token_present() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())


def _safe_text(value: Any, default: str = "", *, limit: int = 400) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return default
    text = EMAIL_RE.sub(lambda match: f"{match.group(1)}***@{match.group(2)}", text)
    if SENSITIVE_TEXT_RE.search(text):
        return "[redacted sensitive input]"
    return text[:limit]


def _redact_text(value: Any) -> str:
    text = _safe_text(value, "not provided", limit=1200)
    return EMAIL_RE.sub(lambda match: f"{match.group(1)}***@{match.group(2)}", text)


def _safe_list(value: Any) -> List[str]:
    if value is None:
        return []
    items = value if isinstance(value, list) else [value]
    return [_safe_text(item) for item in items[:50] if _safe_text(item)]


def _safe_scope(value: Any) -> List[str]:
    items = [str(item).strip().lower() for item in (value if isinstance(value, list) else [value])]
    clean = [item for item in items if item in REMOTE_APPROVAL_SCOPE]
    if "execute" in items or "approve_all_forever" in items:
        raise ValueError("remote scope cannot grant execution or blanket approval")
    return clean or ["notification", "approval_preview"]


def _channel_id(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return text or "unknown"


def _choice(value: Any, choices: set[str], default: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_")
    return text if text in choices else default


def _money(value: Any) -> Optional[float]:
    if value in (None, "", "unknown"):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    return amount if amount >= 0 else None


def _currency(value: Any) -> str:
    text = str(value or "USD").strip().upper()
    return text if re.fullmatch(r"[A-Z]{3}", text) else "USD"


def _cost_estimate(value: Any, currency: Any = "USD") -> Dict[str, Any]:
    amount = _money(value)
    return {
        "amount": amount,
        "currency": _currency(currency) if amount is not None else "unknown",
        "known": amount is not None,
        "source": "operator_estimate" if amount is not None else "unknown",
        "confirmed": False,
        "estimates_consume_budget": False,
    }


def _redacted_identifier(value: Any) -> str:
    text = _safe_text(value, "not provided")
    if text in {"not provided", "[redacted sensitive input]"}:
        return text
    return f"redacted:{hashlib.sha256(text.encode('utf-8')).hexdigest()[:10]}"


def _recipient_summary(recipients: List[Any]) -> Dict[str, Any]:
    domains: Dict[str, int] = {}
    for recipient in recipients[:200]:
        match = EMAIL_RE.search(str(recipient))
        domain = match.group(2).lower() if match else "unknown"
        domains[domain] = domains.get(domain, 0) + 1
    return {
        "recipient_count": len(recipients),
        "domains": domains,
        "identities_redacted": True,
        "contact_scraping_used": False,
    }


def _attachment_metadata(value: Any) -> List[Dict[str, Any]]:
    attachments = value if isinstance(value, list) else []
    result = []
    for item in attachments[:20]:
        data = item if isinstance(item, dict) else {"name": str(item)}
        result.append({
            "name": _safe_text(data.get("name"), "attachment"),
            "content_type": _safe_text(data.get("content_type"), "unknown"),
            "size_bytes": int(data.get("size_bytes") or 0) if str(data.get("size_bytes") or "0").isdigit() else 0,
            "content_included": False,
        })
    return result


def _campaign_checklist(bulk: bool) -> List[str]:
    if not bulk:
        return ["not a campaign; still review recipients and sender identity before send"]
    return [
        "explicit audience envelope",
        "consent or legal basis documented",
        "unsubscribe path present",
        "sender identity reviewed",
        "rate limit and cost reviewed",
        "strong approval required",
    ]


def _side_effects_for_candidate(candidate: Mapping[str, Any]) -> List[str]:
    category = candidate.get("category")
    if category == "deploy":
        return ["external_provider_deploy_if_future_enabled", "production_impact_possible", "cost_possible"]
    if category == "email":
        return ["recipient_contact_if_future_send_enabled", "identity_use_possible", "cost_or_rate_limit_possible"]
    if category == "payment":
        return ["checkout_or_payment_if_future_enabled", "money_movement_possible", "customer_data_possible"]
    return ["remote_notification_or_approval_intent"]


def _rollback_for_candidate(candidate: Mapping[str, Any]) -> str:
    category = candidate.get("category")
    if category == "deploy":
        rollback = candidate.get("rollback", {})
        return str(rollback.get("plan") or "rollback not available")
    if category == "email":
        return "stop before send; sent email cannot be recalled reliably"
    if category == "payment":
        return "stop before provider call; refund/payout/refund execution not implemented in this PR"
    return "cancel remote intent before approval expiration"


def _readback_for_candidate(candidate: Mapping[str, Any], operation_id: str) -> str:
    category = candidate.get("category", "operation")
    provider = candidate.get("provider", "unknown")
    risk = candidate.get("risk_level", "unknown")
    approval = candidate.get("approval_level_required", "unknown")
    return (
        f"Operation {operation_id}: prepare {category} candidate using provider {provider}. "
        f"Risk {risk}; approval {approval}; execution disabled; provider not called."
    )


def _normalize_readback(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _dedupe(items: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(str(item) for item in items if str(item)))


def _public_device(device: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not device:
        return {}
    return {
        "device_id": device.get("device_id", ""),
        "display_name": device.get("display_name", ""),
        "channel_type": device.get("channel_type", "unknown"),
        "trusted": bool(device.get("trusted")) and not bool(device.get("revoked")),
        "paired": bool(device.get("paired")),
        "verified": bool(device.get("verified")),
        "revoked": bool(device.get("revoked")),
        "local_only": bool(device.get("local_only")),
        "approval_scope": list(device.get("approval_scope") or []),
        "capabilities": {
            "remote_approval_intent": bool((device.get("capabilities") or {}).get("remote_approval_intent")),
            "can_execute": False,
            "direct_hermes": False,
        },
    }


def _trusted_device(device: Optional[Mapping[str, Any]]) -> bool:
    return bool(device and device.get("trusted") and device.get("verified") and device.get("paired") and not device.get("revoked"))


def _trusted_remote_device(device: Optional[Mapping[str, Any]]) -> bool:
    if not _trusted_device(device):
        return False
    caps = dict(device.get("capabilities") or {})
    scope = set(device.get("approval_scope") or [])
    return bool(caps.get("remote_approval_intent") and "remote_approval_intent" in scope and not caps.get("can_execute"))
