from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.mark_3_mission_loop_models import UNKNOWN


ROUTINE_OPS_ENDPOINTS = (
    "GET /mark-3/routine-ops/status",
    "POST /mark-3/routine-ops/plan",
    "POST /mark-3/routine-ops/personal",
    "POST /mark-3/routine-ops/family",
    "POST /mark-3/routine-ops/account-assistance",
    "POST /mark-3/routine-ops/decision",
)
INVARIANTS = {
    "candidate_is_not_execution": True,
    "approval_is_not_execution": True,
    "memory_is_not_permission": True,
    "no_real_scheduler": True,
    "no_background_worker": True,
    "no_real_email": True,
    "no_real_calendar": True,
    "no_real_account_access": True,
    "no_password_storage": True,
    "no_2fa_bypass": True,
    "no_cookie_or_token_use": True,
    "no_fake_completion": True,
}
SIDE_EFFECT_FLAGS = {
    "would_schedule": False,
    "would_execute": False,
    "would_notify": False,
    "would_access_external_account": False,
    "would_store_secret": False,
    "execution_performed": False,
    "scheduler_created": False,
    "cron_created": False,
    "background_worker_started": False,
    "watcher_started": False,
    "email_sent": False,
    "calendar_accessed": False,
    "gmail_accessed": False,
    "contacts_accessed": False,
    "provider_called": False,
    "account_login_performed": False,
    "account_recovery_performed": False,
    "password_saved": False,
    "two_fa_bypassed": False,
    "cookie_token_session_used": False,
    "money_moved": False,
    "production_changed": False,
    "providers_called": False,
    "hermes_called": False,
    "approval_gateway_called": False,
}
CAPABILITY_STATUS = {
    "real_scheduler": "capability_not_connected_yet",
    "background_worker": "capability_not_connected_yet",
    "email": "capability_not_connected_yet",
    "calendar": "capability_not_connected_yet",
    "gmail": "capability_not_connected_yet",
    "contacts": "capability_not_connected_yet",
    "external_account_access": "capability_not_connected_yet",
    "account_recovery_execution": "capability_not_connected_yet",
    "local_repo_health_read_only": "prepare_only_candidate",
}
PERMANENT_DENIAL_REASONS = {
    "password_storage_blocked",
    "two_fa_bypass_blocked",
    "cookie_token_or_session_material_blocked",
    "illegal_or_unauthorized_access_request_blocked",
    "impersonation_or_social_engineering_blocked",
    "credentials_or_env_access_blocked",
    "fake_completion_request_blocked",
}


@dataclass(frozen=True)
class RoutineOpsAuditEvent:
    event_id: str
    event_type: str
    created_at: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    redacted_fields: List[str] = field(default_factory=list)
    safe_to_execute: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark3RoutineOpsControlPlane:
    """Prepare-only Mark 3 routine, personal, family, and account assistance layer."""

    def __init__(
        self,
        *,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.clock = clock or now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._candidates: Dict[str, Dict[str, Any]] = {}
        self._audit: List[RoutineOpsAuditEvent] = []

    def status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "mark": "Mark 3",
            "surface": "local_routine_scheduler_personal_family_ops",
            "prepare_only": True,
            "control_plane_only": True,
            "in_memory_only": True,
            "safe_to_render": True,
            "candidate_count": len(self._candidates),
            "audit_event_count": len(self._audit),
            "endpoints": list(ROUTINE_OPS_ENDPOINTS),
            "capability_status": dict(CAPABILITY_STATUS),
            "can_prepare_local_routine_candidates": True,
            "can_prepare_daily_weekly_routine_plans": True,
            "can_prepare_personal_ops_candidates": True,
            "can_prepare_family_ops_candidates": True,
            "can_prepare_authorized_account_assistance": True,
            "can_prepare_password_manager_checklist": True,
            "can_prepare_2fa_checklist": True,
            "can_prepare_repo_product_budget_health_candidates": True,
            "real_scheduler_connected": False,
            "real_calendar_connected": False,
            "real_gmail_connected": False,
            "real_contacts_connected": False,
            "real_email_connected": False,
            "real_account_provider_connected": False,
            "external_provider_capabilities_connected": False,
            "hermes_remains_execution_engine": True,
            "jarvis_governs_risk_approval_audit": True,
            "approval_gates_are_not_permanent_bans": True,
            "legal_safe_authorized_supported_actions_can_advance_with_approval": True,
            "invariants": dict(INVARIANTS),
            "approval_requirements_by_risk": approval_requirements_by_risk(),
            **INVARIANTS,
            **SIDE_EFFECT_FLAGS,
        }

    def plan(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="routine_plan",
            routine_type=_text(_first_present(values, "routine_type", "plan_type")) or "local_routine_plan",
            ops_type="routine_ops",
            values=values,
        )
        candidate["routine_plan"] = _routine_plan(candidate["input"], candidate)
        return self._store(candidate)

    def personal(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="personal_ops",
            routine_type=_text(values.get("routine_type")) or "personal_ops",
            ops_type=_text(values.get("ops_type")) or "personal_ops",
            values=values,
        )
        candidate["personal_ops_candidate"] = _personal_ops(candidate["input"], candidate)
        return self._store(candidate)

    def family(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="family_ops",
            routine_type=_text(values.get("routine_type")) or "family_ops",
            ops_type=_text(values.get("ops_type")) or "family_ops",
            values=values,
        )
        candidate["family_ops_candidate"] = _family_ops(candidate["input"], candidate)
        return self._store(candidate)

    def account_assistance(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="authorized_account_assistance",
            routine_type=_text(values.get("routine_type")) or "account_assistance",
            ops_type=_text(values.get("ops_type")) or "authorized_account_assistance",
            values=values,
        )
        candidate["account_assistance_candidate"] = _account_assistance(candidate["input"], candidate)
        return self._store(candidate)

    def decision(self, values: Dict[str, Any]) -> Dict[str, Any]:
        candidate = self._base_candidate(
            candidate_type="routine_ops_decision",
            routine_type=_text(values.get("routine_type")) or "routine_ops_decision",
            ops_type=_text(values.get("ops_type")) or "decision",
            values=values,
        )
        candidate["decision"] = _decision(candidate["input"], candidate)
        return self._store(candidate)

    def list_candidates(self) -> List[Dict[str, Any]]:
        return list(self._candidates.values())

    def audit(self) -> Dict[str, Any]:
        return {
            "append_only": True,
            "in_memory_only": True,
            "safe_to_execute": False,
            "events": [item.to_dict() for item in self._audit],
        }

    def _base_candidate(
        self,
        *,
        candidate_type: str,
        routine_type: str,
        ops_type: str,
        values: Dict[str, Any],
    ) -> Dict[str, Any]:
        raw_input = dict(values or {})
        safe_input, redacted_fields = redact_sensitive_data(raw_input)
        blocked_reasons = _blocked_reasons(raw_input, redacted_fields)
        missing_requirements = _missing_requirements(candidate_type, raw_input)
        setup_gated = _setup_gated_actions(raw_input)
        risk = classify_routine_ops_risk(
            raw_input,
            candidate_type=candidate_type,
            blocked_reasons=blocked_reasons,
            setup_gated_actions=setup_gated,
            missing_requirements=missing_requirements,
        )
        approval = approval_requirements_for(risk, setup_gated_actions=setup_gated)
        candidate_id = _text(safe_input.get("candidate_id")) or self.id_factory()
        permanent_denial = _permanent_denial(blocked_reasons)
        capability_status = _candidate_capability_status(setup_gated)
        if permanent_denial:
            candidate_state = "blocked"
            execution_status = "blocked"
        elif setup_gated or missing_requirements:
            candidate_state = "setup_required"
            execution_status = "setup_required"
        else:
            candidate_state = "prepared_candidate"
            execution_status = "prepared"

        candidate = {
            "candidate_id": candidate_id,
            "candidate_type": candidate_type,
            "routine_type": routine_type,
            "ops_type": ops_type,
            "created_at": self.clock(),
            "input": safe_input,
            "redacted_fields": redacted_fields,
            "candidate_state": candidate_state,
            "execution_status": execution_status,
            "capability_status": capability_status,
            "control_plane_only": True,
            "prepare_only": True,
            "safe_to_execute": False,
            "risk_level": risk["risk_level"],
            "risk_level_number": risk["risk_level_number"],
            "approval_required": approval["approval_required"],
            "required_approval_level": approval["required_approval_level"],
            "approval_requirements": approval,
            "approval_requirements_by_risk": approval_requirements_by_risk(),
            "scope": _scope(candidate_type, safe_input),
            "budget_limit": _budget_limit(safe_input),
            "schedule_preview": _schedule_preview(safe_input),
            "evidence_required": _evidence_required(candidate_type, safe_input),
            "stop_conditions": _stop_conditions(candidate_type, safe_input, blocked_reasons, setup_gated),
            "next_safe_action": _next_safe_action(candidate_type, blocked_reasons, missing_requirements, setup_gated, risk),
            "audit_summary": _audit_summary(candidate_type, blocked_reasons, missing_requirements, setup_gated),
            "setup_gated_actions": setup_gated,
            "missing_requirements": missing_requirements,
            "blocked_reasons": blocked_reasons,
            "permanent_denial": permanent_denial,
            "official_recovery_only": candidate_type == "authorized_account_assistance",
            "candidate_can_execute": False,
            "candidate_can_schedule": False,
            "candidate_can_notify": False,
            "candidate_can_access_external_account": False,
            "candidate_can_store_secret": False,
            "no_duplicate_hermes_runtime": True,
            "hermes_is_execution_engine": True,
            "jarvis_governs_decides_approves_audits": True,
            "approval_is_gate_not_permanent_ban": risk["risk_level_number"] < 5,
            "invariants": dict(INVARIANTS),
            **INVARIANTS,
            **SIDE_EFFECT_FLAGS,
        }
        return candidate

    def _store(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        self._candidates[candidate["candidate_id"]] = candidate
        self._append_audit(
            "routine_ops_candidate_prepared",
            candidate["audit_summary"],
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_type": candidate["candidate_type"],
                "routine_type": candidate["routine_type"],
                "ops_type": candidate["ops_type"],
                "risk_level": candidate["risk_level"],
                "required_approval_level": candidate["required_approval_level"],
                "execution_status": candidate["execution_status"],
            },
        )
        return candidate

    def _append_audit(self, event_type: str, summary: str, metadata: Dict[str, Any]) -> None:
        safe, redacted = redact_sensitive_data(metadata)
        self._audit.append(RoutineOpsAuditEvent(
            event_id=self.id_factory(),
            event_type=event_type,
            created_at=self.clock(),
            summary=summary,
            metadata=safe,
            redacted_fields=redacted,
        ))


def classify_routine_ops_risk(
    values: Dict[str, Any],
    *,
    candidate_type: str,
    blocked_reasons: Optional[List[str]] = None,
    setup_gated_actions: Optional[List[str]] = None,
    missing_requirements: Optional[List[str]] = None,
) -> Dict[str, Any]:
    reasons = blocked_reasons if blocked_reasons is not None else _blocked_reasons(values, [])
    setup = setup_gated_actions if setup_gated_actions is not None else _setup_gated_actions(values)
    missing = missing_requirements if missing_requirements is not None else _missing_requirements(candidate_type, values)
    text = _combined(values)
    if _permanent_denial(reasons):
        return {"risk_level": "denied", "risk_level_number": 5}
    if _critical_requested(values) or "real_account_recovery_action" in setup:
        return {"risk_level": "critical", "risk_level_number": 4}
    if _private_account_metadata(values) or candidate_type in {"family_ops", "authorized_account_assistance"}:
        return {"risk_level": "high", "risk_level_number": 3}
    if _local_repo_or_file_health(values) or "repo health" in text or "budget health" in text:
        return {"risk_level": "medium", "risk_level_number": 2}
    if missing:
        return {"risk_level": "low", "risk_level_number": 1}
    return {"risk_level": "low", "risk_level_number": 1}


def approval_requirements_for(
    risk: Dict[str, Any],
    *,
    setup_gated_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    risk_number = int(risk["risk_level_number"])
    setup = setup_gated_actions or []
    if risk_number == 5:
        required_level = "level_5_denied"
    elif risk_number == 4:
        required_level = "level_4_strong_double_or_triple"
    elif risk_number == 3:
        required_level = "strong"
    elif risk_number == 2:
        required_level = "simple"
    else:
        required_level = "direct"
    return {
        "approval_required": required_level not in {"direct", "level_5_denied"},
        "required_approval_level": required_level,
        "prepare_candidate_approval_level": "direct",
        "strong_approval_required": required_level in {"strong", "level_4_strong_double_or_triple"},
        "double_confirmation_required": required_level == "level_4_strong_double_or_triple",
        "triple_confirmation_required": required_level == "level_4_strong_double_or_triple",
        "readback_required": risk_number >= 3,
        "scope_required": risk_number >= 2,
        "budget_limit_required": risk_number >= 2,
        "candidate_preparation_executes": False,
        "approval_grants_execution": False,
        "setup_gated_actions": setup,
        "level_4_requires": [
            "exact action readback",
            "strong approval",
            "double confirmation",
            "triple confirmation for credentials, account recovery, money, production, or real provider actions",
            "budget limit",
            "rollback or stop plan",
            "audit",
            "visible human stop control",
        ] if risk_number == 4 else [],
    }


def approval_requirements_by_risk() -> Dict[str, Dict[str, Any]]:
    return {
        "low": {
            "level": "0-1",
            "required_approval_level": "direct",
            "examples": ["local routine planning", "checklists", "daily or weekly plan candidates"],
        },
        "medium": {
            "level": 2,
            "required_approval_level": "simple",
            "examples": ["scoped read-only repo health candidate", "product or budget health checklist"],
        },
        "high": {
            "level": 3,
            "required_approval_level": "strong",
            "examples": ["personal account metadata inventory", "family ops with consent and scope"],
        },
        "critical": {
            "level": 4,
            "required_approval_level": "level_4_strong_double_or_triple",
            "examples": [
                "real account recovery action",
                "email sending",
                "calendar or account connection",
                "credentials",
                "money",
                "production",
            ],
        },
        "denied": {
            "level": 5,
            "required_approval_level": "level_5_denied",
            "examples": ["2FA bypass", "cookie/token/session theft", "password storage", "unauthorized access"],
        },
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _routine_plan(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    tasks = _items(_first_present(values, "tasks", "task_candidates", "routine_steps")) or [
        "review priorities",
        "prepare next safe action",
        "record evidence gaps",
    ]
    return {
        "title": _text(_first_present(values, "title", "objective", "goal")) or "local routine candidate",
        "tasks": tasks,
        "daily_plan": _items(values.get("daily_plan")),
        "weekly_plan": _items(values.get("weekly_plan")),
        "health_checks": _health_checks(values),
        "schedule_preview": candidate["schedule_preview"],
        "candidate_only": True,
        "would_create_cron": False,
        "would_register_worker": False,
        "would_execute_tasks": False,
        "would_send_reminders": False,
    }


def _personal_ops(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "objective": _text(_first_present(values, "objective", "goal", "title")) or "personal ops candidate",
        "checklist": _items(values.get("checklist")) or _default_personal_checklist(values),
        "account_inventory": _safe_account_inventory(values),
        "password_manager_checklist": _password_manager_checklist(),
        "two_factor_checklist": _two_factor_checklist(),
        "uses_operator_provided_data_only": True,
        "would_read_gmail": False,
        "would_read_calendar": False,
        "would_read_contacts": False,
        "would_access_accounts": False,
        "candidate_only": True,
        "next_safe_action": candidate["next_safe_action"],
    }


def _family_ops(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "family_member": _text(values.get("family_member")) or UNKNOWN,
        "consent_scope_candidate": {
            "consent_recorded": _consent_recorded(values),
            "scope": candidate["scope"],
            "authorized": _authorized(values),
            "review_required": True,
        },
        "checklist": _items(values.get("checklist")) or [
            "confirm consent and exact scope",
            "list accounts or tasks without secrets",
            "prepare official recovery or setup steps only",
            "stop before any login, email send, calendar access, or credential handling",
        ],
        "would_contact_family_member": False,
        "would_access_family_account": False,
        "would_send_email_or_message": False,
        "candidate_only": True,
        "next_safe_action": candidate["next_safe_action"],
    }


def _account_assistance(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "assistance_mode": "official_recovery_only",
        "account_provider": _text(_first_present(values, "account_provider", "provider", "service")) or UNKNOWN,
        "account_owner": _text(values.get("account_owner")) or UNKNOWN,
        "authorized": _authorized(values),
        "consent_recorded": _consent_recorded(values),
        "safe_inventory_without_secrets": _safe_account_inventory(values),
        "official_recovery_steps": [
            "confirm the account owner and authorized helper scope",
            "open the provider's official recovery flow manually",
            "use only recovery data the account owner is allowed to provide",
            "store any new password only in an approved password manager, never in JARVIS",
            "review 2FA recovery options without bypassing 2FA",
            "stop if the provider asks for credentials, codes, identity documents, or payment outside the official flow",
        ],
        "password_manager_checklist": _password_manager_checklist(),
        "two_factor_checklist": _two_factor_checklist(),
        "blocked_actions": [
            "password storage",
            "2FA bypass",
            "cookie, token, or session material use",
            "unauthorized login",
            "impersonation",
        ],
        "would_login": False,
        "would_reset_password": False,
        "would_send_recovery_email": False,
        "would_access_external_account": False,
        "would_store_secret": False,
        "candidate_only": True,
        "next_safe_action": candidate["next_safe_action"],
    }


def _decision(values: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    if candidate["blocked_reasons"]:
        recommendation = "deny_or_rewrite"
        reason = "request contains blocked unsafe or unauthorized content"
    elif candidate["missing_requirements"] or candidate["setup_gated_actions"]:
        recommendation = "hold_for_setup_or_scope"
        reason = "candidate requires consent, scope, approval, or unsupported capability setup"
    else:
        recommendation = "review_candidate"
        reason = "candidate is ready for human review and evidence collection"
    return {
        "candidate_id": candidate["candidate_id"],
        "recommendation": recommendation,
        "reason": reason,
        "risk_level": candidate["risk_level"],
        "required_approval_level": candidate["required_approval_level"],
        "approval_grants_execution": False,
        "would_execute_decision": False,
        "next_safe_action": candidate["next_safe_action"],
    }


def _schedule_preview(values: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "cadence": _choice(_first_present(values, "cadence", "frequency"), {"once", "daily", "weekly", "monthly", "manual", "unknown"}, "manual"),
        "schedule_expression": _text(_first_present(values, "schedule_expression", "schedule", "recurrence_rule")) or UNKNOWN,
        "timezone": _text(values.get("timezone")) or "local",
        "next_run_preview": _text(_first_present(values, "next_run_preview", "due_at", "start_time")) or UNKNOWN,
        "quiet_hours": _text(values.get("quiet_hours")) or UNKNOWN,
        "would_schedule": False,
        "would_create_scheduler": False,
        "would_create_cron": False,
        "would_create_system_timer": False,
        "would_register_worker": False,
        "would_persist_schedule": False,
        "no_real_scheduler": True,
    }


def _health_checks(values: Dict[str, Any]) -> List[Dict[str, Any]]:
    requested = _items(_first_present(values, "health_checks", "checks"))
    if not requested and _local_repo_or_file_health(values):
        requested = ["scoped read-only local repo health candidate"]
    if not requested and "budget" in _combined(values):
        requested = ["budget health checklist from operator-provided numbers only"]
    return [
        {
            "check": item,
            "prepare_only": True,
            "would_execute": False,
            "would_read_files": False,
            "would_call_provider": False,
            "evidence_required": "operator-provided evidence or separately approved read-only adapter",
        }
        for item in requested
    ]


def _default_personal_checklist(values: Dict[str, Any]) -> List[str]:
    if _private_account_metadata(values):
        return [
            "list account provider and account owner without passwords or recovery codes",
            "confirm official support or recovery path",
            "record scope and evidence needed before any future action",
            "prepare password manager and 2FA review checklist",
        ]
    return [
        "define the personal ops goal",
        "capture constraints and stop conditions",
        "prepare checklist using operator-provided data only",
        "review next safe action before any side effect",
    ]


def _safe_account_inventory(values: Dict[str, Any]) -> Dict[str, Any]:
    inventory = {
        "provider": _text(_first_present(values, "account_provider", "provider", "service")) or UNKNOWN,
        "account_owner": _text(values.get("account_owner")) or UNKNOWN,
        "account_identifier_present": bool(_text(_first_present(values, "account_identifier", "username_hint", "email_hint"))),
        "secrets_included": False,
        "recovery_codes_included": False,
        "cookies_tokens_or_sessions_included": False,
        "safe_to_store_in_candidate": True,
    }
    return inventory


def _password_manager_checklist() -> List[str]:
    return [
        "choose or confirm an approved password manager",
        "store passwords only inside that password manager",
        "generate unique passwords per account",
        "do not paste passwords into JARVIS",
        "record only non-secret metadata in JARVIS candidates",
    ]


def _two_factor_checklist() -> List[str]:
    return [
        "enable 2FA where supported",
        "prefer authenticator app or hardware key over SMS when practical",
        "store recovery codes only in the approved password manager or secure offline location",
        "document which recovery method exists without storing codes",
        "never bypass 2FA or use session material",
    ]


def _blocked_reasons(values: Dict[str, Any], redacted_fields: Iterable[str]) -> List[str]:
    text = _combined(values)
    reasons: List[str] = []
    if redacted_fields:
        reasons.append("secret_or_credential_input_redacted")
    if _truthy(values, "store_password") or _truthy(values, "password_storage_requested") or any(
        marker in text for marker in ("store password", "save password", "guardar contrasena")
    ):
        reasons.append("password_storage_blocked")
    if _two_fa_bypass_requested(text):
        reasons.append("two_fa_bypass_blocked")
    if _cookie_token_session_requested(text) or any("cookie" in field or "token" in field for field in redacted_fields):
        reasons.append("cookie_token_or_session_material_blocked")
    if any(marker in text for marker in ("hack account", "hackea", "unauthorized access", "acceso no autorizado", "steal account", "robar cuenta")):
        reasons.append("illegal_or_unauthorized_access_request_blocked")
    if any(marker in text for marker in ("impersonate", "suplantar", "phishing", "social engineer", "ingenieria social")):
        reasons.append("impersonation_or_social_engineering_blocked")
    if ("authorized" in values and not _truthy(values, "authorized")) or (
        "authorization_valid" in values and not _truthy(values, "authorization_valid")
    ):
        reasons.append("illegal_or_unauthorized_access_request_blocked")
    if (
        ".env" in text
        or "api key" in text
        or "private key" in text
        or "recovery code" in text
        or any(_sensitive_field_marker(field) for field in redacted_fields)
    ):
        reasons.append("credentials_or_env_access_blocked")
    if _fake_completion_requested(values, text):
        reasons.append("fake_completion_request_blocked")
    return _unique(reasons)


def _setup_gated_actions(values: Dict[str, Any]) -> List[str]:
    text = _combined(values)
    checks = {
        "real_scheduler_not_supported_in_this_pr": (
            _truthy(values, "schedule_real_requested")
            or _truthy(values, "create_cron")
            or _truthy(values, "background_worker_requested")
            or _truthy(values, "watcher_requested")
            or any(marker in text for marker in ("create cron", "cron job", "start worker", "background worker", "watcher", "system timer"))
        ),
        "email_capability_not_connected_yet": (
            _truthy(values, "email_requested")
            or _truthy(values, "send_email")
            or any(marker in text for marker in ("send email", "send recovery email", "email real", "gmail send"))
        ),
        "calendar_capability_not_connected_yet": (
            _truthy(values, "calendar_requested")
            or _truthy(values, "calendar_access_requested")
            or any(marker in text for marker in ("calendar", "calendario"))
        ),
        "gmail_capability_not_connected_yet": (
            _truthy(values, "gmail_requested")
            or _truthy(values, "gmail_access_requested")
            or "gmail" in text
        ),
        "contacts_capability_not_connected_yet": (
            _truthy(values, "contacts_requested")
            or _truthy(values, "contacts_access_requested")
            or "contacts" in text
            or "contactos" in text
        ),
        "external_account_access_not_connected_yet": (
            _truthy(values, "account_access_requested")
            or _truthy(values, "login_requested")
            or any(marker in text for marker in ("log in", "login", "connect account", "access account", "entrar en la cuenta"))
        ),
        "real_account_recovery_action": (
            _truthy(values, "perform_recovery_requested")
            or _truthy(values, "reset_password_now")
            or any(marker in text for marker in ("reset password now", "recover account now", "send recovery code", "change password for me"))
        ),
        "money_or_production_requires_level_4": (
            _truthy(values, "money_requested")
            or _truthy(values, "production_requested")
            or any(marker in text for marker in ("move money", "pay bill", "production", "deploy"))
        ),
    }
    return [name for name, active in checks.items() if active]


def _missing_requirements(candidate_type: str, values: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    if candidate_type == "routine_plan" and _local_repo_or_file_health(values) and not _text(values.get("scope")):
        missing.append("local_read_only_scope_required")
    if candidate_type == "family_ops":
        if not _consent_recorded(values):
            missing.append("family_consent_required")
        if not _text(values.get("scope")):
            missing.append("family_scope_required")
    if candidate_type == "authorized_account_assistance":
        if not _authorization_recorded(values):
            missing.append("account_owner_authorization_required")
        if not _text(_first_present(values, "account_provider", "provider", "service")):
            missing.append("account_provider_required")
        if not _text(values.get("scope")):
            missing.append("account_assistance_scope_required")
    return _unique(missing)


def _critical_requested(values: Dict[str, Any]) -> bool:
    text = _combined(values)
    return bool(
        _truthy(values, "credentials_requested")
        or _truthy(values, "money_requested")
        or _truthy(values, "production_requested")
        or any(marker in text for marker in ("credential", "credentials", "money", "production", "deploy", "payment", "password reset now"))
    )


def _private_account_metadata(values: Dict[str, Any]) -> bool:
    text = _combined(values)
    keys = {"account_provider", "provider", "service", "account_owner", "account_identifier", "username_hint", "email_hint"}
    return any(_has_value(values.get(key)) for key in keys) or any(
        marker in text for marker in ("account", "cuenta")
    )


def _local_repo_or_file_health(values: Dict[str, Any]) -> bool:
    text = _combined(values)
    return bool(
        _truthy(values, "repo_health_requested")
        or _truthy(values, "local_file_health_requested")
        or any(marker in text for marker in ("repo health", "repository health", "local file", "read-only repo", "read only repo"))
    )


def _permanent_denial(reasons: Iterable[str]) -> bool:
    return any(reason in PERMANENT_DENIAL_REASONS for reason in reasons)


def _candidate_capability_status(setup_gated: List[str]) -> str:
    if not setup_gated:
        return "prepare_only_candidate"
    if any("not_connected_yet" in item for item in setup_gated):
        return "capability_not_connected_yet"
    return "setup_required"


def _scope(candidate_type: str, values: Dict[str, Any]) -> str:
    explicit = _text(values.get("scope"))
    if explicit:
        return explicit
    defaults = {
        "routine_plan": "local routine candidate preparation only",
        "personal_ops": "personal ops candidate using operator-provided data only",
        "family_ops": "family ops candidate; consent and scope required",
        "authorized_account_assistance": "official account recovery assistance candidate only",
        "routine_ops_decision": "routine ops decision candidate only",
    }
    return defaults.get(candidate_type, "routine ops candidate preparation only")


def _budget_limit(values: Dict[str, Any]) -> Any:
    value = _first_present(values, "budget_limit", "max_budget")
    if not _has_value(value):
        return UNKNOWN
    return _safe_scalar(value)


def _evidence_required(candidate_type: str, values: Dict[str, Any]) -> List[str]:
    explicit = _items(values.get("evidence_required"))
    if explicit:
        return explicit
    common = [
        "operator-provided scope",
        "approval level review",
        "stop conditions",
        "evidence that no real scheduler, email, calendar, account, credential, or provider access is needed in this PR",
    ]
    by_type = {
        "routine_plan": ["routine objective", "cadence preview", "task checklist"],
        "personal_ops": ["personal ops objective", "operator-provided data only", "no secrets included"],
        "family_ops": ["family member consent", "authorized scope", "no secrets or impersonation"],
        "authorized_account_assistance": ["account owner authorization", "official recovery path", "no password, 2FA bypass, cookie, token, or session material"],
        "routine_ops_decision": ["candidate input", "risk classification", "missing requirements"],
    }
    return _unique((by_type.get(candidate_type) or []) + common)


def _stop_conditions(
    candidate_type: str,
    values: Dict[str, Any],
    blocked_reasons: List[str],
    setup_gated_actions: List[str],
) -> List[str]:
    explicit = _items(values.get("stop_conditions"))
    if explicit:
        return explicit
    conditions = [
        "operator asks to stop",
        "request attempts real scheduling, worker, watcher, email, calendar, Gmail, contacts, account access, or provider call",
        "request includes password, recovery code, cookie, token, session material, or .env data",
        "request asks to bypass 2FA, impersonate, hack, or access an unauthorized account",
    ]
    if candidate_type == "family_ops":
        conditions.append("consent or family scope is missing or disputed")
    if candidate_type == "authorized_account_assistance":
        conditions.append("official recovery path or account owner authorization is missing")
    if blocked_reasons or setup_gated_actions:
        conditions.append("blocked or unsupported requirement remains unresolved")
    return conditions


def _next_safe_action(
    candidate_type: str,
    blocked_reasons: List[str],
    missing_requirements: List[str],
    setup_gated_actions: List[str],
    risk: Dict[str, Any],
) -> str:
    if blocked_reasons:
        return "rewrite the request to remove unsafe, unauthorized, secret, bypass, or fake-completion content"
    if missing_requirements:
        return "collect consent, scope, provider name, and evidence before preparing a narrower candidate"
    if setup_gated_actions:
        return "review the candidate only; connect a governed capability in a future PR before any real side effect"
    if risk["risk_level_number"] >= 3:
        return "review scope, authorization, and evidence with strong approval before any future capability is considered"
    if candidate_type == "routine_ops_decision":
        return "review the decision recommendation and unresolved requirements"
    return "review the prepared checklist and collect required evidence"


def _audit_summary(
    candidate_type: str,
    blocked_reasons: List[str],
    missing_requirements: List[str],
    setup_gated_actions: List[str],
) -> str:
    if blocked_reasons:
        return f"Routine ops {candidate_type} request blocked before any side effect."
    if missing_requirements:
        return f"Routine ops {candidate_type} candidate needs setup/scope before any future action."
    if setup_gated_actions:
        return f"Routine ops {candidate_type} candidate prepared; unsupported real capabilities were not called."
    return f"Routine ops {candidate_type} candidate prepared with no scheduler, notification, account, or provider side effect."


def _authorized(values: Dict[str, Any]) -> bool:
    if "authorized" in values:
        return _truthy(values, "authorized")
    if "authorization_valid" in values:
        return _truthy(values, "authorization_valid")
    return True


def _authorization_recorded(values: Dict[str, Any]) -> bool:
    if "authorized" in values:
        return _truthy(values, "authorized")
    if "authorization_valid" in values:
        return _truthy(values, "authorization_valid")
    return False


def _consent_recorded(values: Dict[str, Any]) -> bool:
    return _truthy(values, "consent_recorded") or _truthy(values, "consent_valid") or _truthy(values, "family_consent")


def _two_fa_bypass_requested(text: str) -> bool:
    return any(
        marker in text
        for marker in (
            "bypass 2fa",
            "bypass mfa",
            "skip 2fa",
            "skip mfa",
            "disable 2fa",
            "saltarse 2fa",
            "omitir 2fa",
            "evitar 2fa",
        )
    )


def _cookie_token_session_requested(text: str) -> bool:
    return any(
        marker in text
        for marker in (
            "steal cookie",
            "steal token",
            "use cookie",
            "use cookies",
            "session token",
            "session material",
            "cookie jar",
            "robar cookie",
            "robar token",
            "usar cookie",
            "usar cookies",
        )
    )


def _fake_completion_requested(values: Dict[str, Any], text: str) -> bool:
    return bool(
        _truthy(values, "completed")
        or _truthy(values, "execution_completed")
        or _truthy(values, "mark_complete")
        or any(marker in text for marker in ("fake completion", "pretend completed", "mark as completed", "report as completed", "finge que esta completado"))
    )


def _sensitive_field_marker(field: str) -> bool:
    lowered = str(field).lower()
    return any(marker in lowered for marker in ("password", "credential", "secret", "token", "cookie", ".env"))


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [_text(f"{key}: {item}") for key, item in value.items() if _text(f"{key}: {item}")]
    items = value if isinstance(value, list) else [value]
    return [_text(item) for item in items if _text(item)]


def _first_present(values: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = values.get(key)
        if _has_value(value):
            return value
    return None


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value
    return _text(value) or UNKNOWN


def _choice(value: Any, allowed: set[str], fallback: str) -> str:
    text = _text(value).lower()
    return text if text in allowed else fallback


def _truthy(values: Dict[str, Any], key: str) -> bool:
    value = values.get(key)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "si"}
    return value is True


def _combined(values: Dict[str, Any]) -> str:
    return " ".join(_flatten_text(values)).lower()


def _flatten_text(value: Any) -> List[str]:
    if isinstance(value, dict):
        result: List[str] = []
        for item in value.values():
            result.extend(_flatten_text(item))
        return result
    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            result.extend(_flatten_text(item))
        return result
    return [_text(value)]


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:1000]


def _unique(items: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(item for item in items if item))
