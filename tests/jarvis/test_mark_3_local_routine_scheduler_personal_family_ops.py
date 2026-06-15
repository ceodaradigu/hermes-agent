from __future__ import annotations

import builtins
import inspect
import json
from pathlib import Path
import socket
import subprocess

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (  # noqa: E402
    Mark3ProductRevenueFactoryRequest,
    Mark3ResearchExecutionCandidateRequest,
    Mark3RoutineOpsRequest,
    create_app,
)
from jarvis.mark_3_local_research_adapter import LocalResearchReadAdapter  # noqa: E402
from jarvis.mark_3_local_routine_scheduler_personal_family_ops import (  # noqa: E402
    ROUTINE_OPS_ENDPOINTS,
    Mark3RoutineOpsControlPlane,
)
from jarvis.mark_3_research_execution import ResearchExecutionControlPlane  # noqa: E402


REQUIRED_CANDIDATE_FIELDS = (
    "candidate_id",
    "routine_type",
    "ops_type",
    "risk_level",
    "approval_required",
    "required_approval_level",
    "scope",
    "budget_limit",
    "schedule_preview",
    "would_schedule",
    "would_execute",
    "would_notify",
    "would_access_external_account",
    "would_store_secret",
    "evidence_required",
    "stop_conditions",
    "next_safe_action",
    "audit_summary",
)


def route(app, path, method):
    return next(item for item in app.routes if item.path == path and method in item.methods)


def _request(**values):
    return Mark3RoutineOpsRequest(**values)


def _all_side_effects_disabled(payload):
    for key in (
        "would_schedule",
        "would_execute",
        "would_notify",
        "would_access_external_account",
        "would_store_secret",
        "execution_performed",
        "scheduler_created",
        "cron_created",
        "background_worker_started",
        "watcher_started",
        "email_sent",
        "calendar_accessed",
        "gmail_accessed",
        "contacts_accessed",
        "provider_called",
        "account_login_performed",
        "account_recovery_performed",
        "password_saved",
        "two_fa_bypassed",
        "cookie_token_session_used",
        "money_moved",
        "production_changed",
        "providers_called",
        "hermes_called",
        "approval_gateway_called",
    ):
        assert payload[key] is False


def _required_fields_present(candidate):
    for key in REQUIRED_CANDIDATE_FIELDS:
        assert key in candidate


def test_status_is_safe_prepare_only_and_lists_required_endpoints():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    status = route(app, "/mark-3/routine-ops/status", "GET").endpoint()

    assert status["available"] is True
    assert status["prepare_only"] is True
    assert status["control_plane_only"] is True
    assert status["safe_to_render"] is True
    assert status["real_scheduler_connected"] is False
    assert status["real_calendar_connected"] is False
    assert status["real_gmail_connected"] is False
    assert status["real_contacts_connected"] is False
    assert status["real_email_connected"] is False
    assert status["real_account_provider_connected"] is False
    assert status["endpoints"] == list(ROUTINE_OPS_ENDPOINTS)
    for invariant in (
        "candidate_is_not_execution",
        "approval_is_not_execution",
        "memory_is_not_permission",
        "no_real_scheduler",
        "no_background_worker",
        "no_real_email",
        "no_real_calendar",
        "no_real_account_access",
        "no_password_storage",
        "no_2fa_bypass",
        "no_cookie_or_token_use",
        "no_fake_completion",
    ):
        assert status[invariant] is True
        assert status["invariants"][invariant] is True
    _all_side_effects_disabled(status)


def test_routine_plan_candidate_has_required_fields_and_no_side_effects():
    candidate = Mark3RoutineOpsControlPlane(id_factory=lambda: "routine-fixed").plan({
        "routine_type": "daily_plan",
        "title": "Daily local ops",
        "tasks": ["review priorities", "prepare next safe action"],
        "cadence": "daily",
    })

    _required_fields_present(candidate)
    assert candidate["candidate_id"] == "routine-fixed"
    assert candidate["candidate_type"] == "routine_plan"
    assert candidate["candidate_state"] == "prepared_candidate"
    assert candidate["risk_level"] == "low"
    assert candidate["risk_level_number"] == 1
    assert candidate["approval_required"] is False
    assert candidate["required_approval_level"] == "direct"
    assert candidate["schedule_preview"]["cadence"] == "daily"
    assert candidate["schedule_preview"]["would_create_cron"] is False
    assert candidate["routine_plan"]["would_execute_tasks"] is False
    _all_side_effects_disabled(candidate)


def test_personal_ops_candidate_does_not_access_real_accounts():
    candidate = Mark3RoutineOpsControlPlane().personal({
        "objective": "Prepare safe Gmail account inventory for David",
        "account_provider": "Gmail",
        "account_owner": "David",
        "scope": "inventory metadata only",
    })

    _required_fields_present(candidate)
    assert candidate["risk_level"] == "high"
    assert candidate["risk_level_number"] == 3
    assert candidate["approval_required"] is True
    assert candidate["required_approval_level"] == "strong"
    assert candidate["personal_ops_candidate"]["would_read_gmail"] is False
    assert candidate["personal_ops_candidate"]["would_access_accounts"] is False
    assert candidate["personal_ops_candidate"]["password_manager_checklist"]
    assert candidate["personal_ops_candidate"]["two_factor_checklist"]
    _all_side_effects_disabled(candidate)


def test_password_manager_and_2fa_checklists_are_low_risk_without_account_metadata():
    candidate = Mark3RoutineOpsControlPlane().personal({
        "objective": "Prepare password manager and 2FA checklist",
        "scope": "checklist only",
    })

    assert candidate["risk_level"] == "low"
    assert candidate["risk_level_number"] == 1
    assert candidate["approval_required"] is False
    assert candidate["personal_ops_candidate"]["password_manager_checklist"]
    assert candidate["personal_ops_candidate"]["two_factor_checklist"]
    _all_side_effects_disabled(candidate)


def test_family_ops_requires_consent_and_scope_and_preserves_authorized_candidate():
    candidate = Mark3RoutineOpsControlPlane().family({
        "family_member": "authorized family member",
        "family_consent": True,
        "authorized": True,
        "scope": "prepare phone account recovery checklist only",
        "account_provider": "mobile provider",
    })

    _required_fields_present(candidate)
    assert candidate["candidate_state"] == "prepared_candidate"
    assert candidate["risk_level_number"] == 3
    assert candidate["required_approval_level"] == "strong"
    assert candidate["family_ops_candidate"]["consent_scope_candidate"]["consent_recorded"] is True
    assert candidate["family_ops_candidate"]["consent_scope_candidate"]["authorized"] is True
    assert candidate["family_ops_candidate"]["would_access_family_account"] is False
    assert candidate["missing_requirements"] == []


def test_family_ops_without_consent_returns_setup_required_not_fake_success():
    candidate = Mark3RoutineOpsControlPlane().family({
        "family_member": "authorized family member",
        "scope": "prepare checklist only",
    })

    assert candidate["candidate_state"] == "setup_required"
    assert candidate["execution_status"] == "setup_required"
    assert "family_consent_required" in candidate["missing_requirements"]
    assert candidate["candidate_can_execute"] is False


def test_authorized_account_assistance_is_official_recovery_only():
    candidate = Mark3RoutineOpsControlPlane().account_assistance({
        "account_provider": "Google",
        "account_owner": "David",
        "authorized": True,
        "consent_recorded": True,
        "scope": "prepare official recovery checklist only",
    })

    _required_fields_present(candidate)
    assistance = candidate["account_assistance_candidate"]
    assert candidate["candidate_state"] == "prepared_candidate"
    assert candidate["official_recovery_only"] is True
    assert assistance["assistance_mode"] == "official_recovery_only"
    assert assistance["would_login"] is False
    assert assistance["would_reset_password"] is False
    assert assistance["would_send_recovery_email"] is False
    assert assistance["would_access_external_account"] is False
    assert assistance["would_store_secret"] is False
    assert "password storage" in assistance["blocked_actions"]
    assert assistance["password_manager_checklist"]
    assert assistance["two_factor_checklist"]


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ({"objective": "store password hunter2", "store_password": True}, "password_storage_blocked"),
        ({"objective": "bypass 2FA for this account"}, "two_fa_bypass_blocked"),
        ({"objective": "use session token abc123 and steal cookie"}, "cookie_token_or_session_material_blocked"),
    ],
)
def test_blocks_password_storage_2fa_bypass_and_cookie_token_session_theft(payload, reason):
    candidate = Mark3RoutineOpsControlPlane().account_assistance({
        "account_provider": "Google",
        "account_owner": "David",
        "authorized": True,
        "scope": "unsafe request",
        **payload,
    })
    serialized = json.dumps(candidate).lower()

    assert candidate["execution_status"] == "blocked"
    assert candidate["risk_level"] == "denied"
    assert candidate["risk_level_number"] == 5
    assert reason in candidate["blocked_reasons"]
    assert candidate["permanent_denial"] is True
    assert candidate["would_store_secret"] is False
    assert candidate["two_fa_bypassed"] is False
    assert candidate["cookie_token_session_used"] is False
    assert "hunter2" not in serialized
    assert "abc123" not in serialized


def test_no_real_scheduler_cron_or_background_worker(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("external side effect attempted")

    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(socket, "create_connection", fail)
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    candidate = route(app, "/mark-3/routine-ops/plan", "POST").endpoint(
        _request(
            title="daily worker",
            cadence="daily",
            create_cron=True,
            background_worker_requested=True,
            schedule_real_requested=True,
        )
    )
    module_source = inspect.getsource(__import__("jarvis.mark_3_local_routine_scheduler_personal_family_ops", fromlist=["x"]))

    assert candidate["execution_status"] == "setup_required"
    assert "real_scheduler_not_supported_in_this_pr" in candidate["setup_gated_actions"]
    assert candidate["schedule_preview"]["would_create_cron"] is False
    assert candidate["cron_created"] is False
    assert candidate["background_worker_started"] is False
    assert "subprocess" not in module_source
    assert "socket" not in module_source
    assert "threading" not in module_source


def test_no_email_calendar_gmail_contacts_or_provider_real_access(monkeypatch):
    original_open = builtins.open

    def guarded_open(file, *args, **kwargs):
        if str(file).endswith(".env"):
            pytest.fail(".env read")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    candidate = route(app, "/mark-3/routine-ops/personal", "POST").endpoint(
        _request(
            objective="Prepare personal ops requiring Gmail, calendar, contacts, and provider setup",
            gmail_requested=True,
            calendar_requested=True,
            contacts_requested=True,
            email_requested=True,
            account_access_requested=True,
            provider="Google",
            scope="metadata inventory only",
        )
    )

    assert candidate["execution_status"] == "setup_required"
    assert candidate["capability_status"] == "capability_not_connected_yet"
    assert "gmail_capability_not_connected_yet" in candidate["setup_gated_actions"]
    assert "calendar_capability_not_connected_yet" in candidate["setup_gated_actions"]
    assert "contacts_capability_not_connected_yet" in candidate["setup_gated_actions"]
    assert candidate["email_sent"] is False
    assert candidate["calendar_accessed"] is False
    assert candidate["gmail_accessed"] is False
    assert candidate["contacts_accessed"] is False
    assert candidate["provider_called"] is False


def test_no_fake_completion_is_blocked():
    candidate = Mark3RoutineOpsControlPlane().decision({
        "objective": "mark as completed even though it did not run",
        "completed": True,
    })

    assert candidate["execution_status"] == "blocked"
    assert candidate["risk_level_number"] == 5
    assert "fake_completion_request_blocked" in candidate["blocked_reasons"]
    assert candidate["no_fake_completion"] is True
    assert candidate["decision"]["would_execute_decision"] is False


def test_risk_escalation_matches_mark_3_model():
    plane = Mark3RoutineOpsControlPlane()
    low = plane.plan({"title": "daily checklist"})
    medium = plane.plan({
        "title": "repo health",
        "repo_health_requested": True,
        "scope": "read-only exact repo health checklist",
    })
    high = plane.personal({
        "objective": "account metadata inventory",
        "account_provider": "Google",
        "scope": "metadata only",
    })
    critical = plane.account_assistance({
        "account_provider": "Google",
        "account_owner": "David",
        "authorized": True,
        "scope": "official recovery",
        "perform_recovery_requested": True,
    })
    denied = plane.account_assistance({
        "account_provider": "Google",
        "authorized": True,
        "scope": "bypass",
        "objective": "bypass 2FA",
    })

    assert (low["risk_level_number"], low["required_approval_level"]) == (1, "direct")
    assert (medium["risk_level_number"], medium["required_approval_level"]) == (2, "simple")
    assert (high["risk_level_number"], high["required_approval_level"]) == (3, "strong")
    assert critical["risk_level_number"] == 4
    assert critical["required_approval_level"] == "level_4_strong_double_or_triple"
    assert critical["execution_status"] == "setup_required"
    assert denied["risk_level_number"] == 5
    assert denied["required_approval_level"] == "level_5_denied"


def test_repo_health_candidate_requires_local_read_only_scope():
    candidate = Mark3RoutineOpsControlPlane().plan({
        "title": "repo health",
        "repo_health_requested": True,
    })

    assert candidate["risk_level_number"] == 2
    assert candidate["candidate_state"] == "setup_required"
    assert "local_read_only_scope_required" in candidate["missing_requirements"]
    assert candidate["would_execute"] is False


def test_routine_ops_api_has_no_dangerous_action_endpoints():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    routes = {item.path for item in app.routes if item.path.startswith("/mark-3/routine-ops")}

    assert routes == {
        "/mark-3/routine-ops/status",
        "/mark-3/routine-ops/plan",
        "/mark-3/routine-ops/personal",
        "/mark-3/routine-ops/family",
        "/mark-3/routine-ops/account-assistance",
        "/mark-3/routine-ops/decision",
    }
    for path in routes:
        for forbidden in ("execute", "run", "start-worker", "send", "login", "bypass"):
            assert forbidden not in path


def test_pr_137_local_research_adapter_regression_still_reads_exact_allowed_file(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("PR 137 exact local evidence\n", encoding="utf-8")
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    app.state.mark_3_research_execution_bridge = ResearchExecutionControlPlane(
        local_research_adapter=LocalResearchReadAdapter(repo_root=tmp_path)
    )

    result = route(app, "/mark-3/research-execution/candidate", "POST").endpoint(
        Mark3ResearchExecutionCandidateRequest(
            source_type="docs",
            scope="docs/guide.md",
            query="local adapter regression",
        )
    )

    assert result["execution_status"] == "completed"
    assert result["adapter_called"] is True
    assert result["file_reads_performed"] is True
    assert result["local_repo_scan_performed"] is False
    assert "PR 137 exact local evidence" in result["local_read_result"]["content"]


def test_pr_138_product_revenue_factory_regression_still_prepare_only():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    candidate = route(app, "/mark-3/product-revenue/experiment", "POST").endpoint(
        Mark3ProductRevenueFactoryRequest(
            experiment_name="paid launch",
            stripe_live_requested=True,
            checkout_requested=True,
            payment_requested=True,
            production_requested=True,
        )
    )

    assert candidate["risk_level_number"] == 4
    assert candidate["required_approval_level"] == "level_4_strong_double_or_triple"
    assert candidate["checkout_created"] is False
    assert candidate["payment_processed"] is False
    assert candidate["deploy_performed"] is False
    assert candidate["candidate_is_not_payment"] is True


def test_docs_and_handoff_are_updated_for_pr_139_routine_ops():
    routine_doc = Path("docs/jarvis-mark-3-local-routine-scheduler-personal-family-ops.md").read_text(encoding="utf-8")
    master = Path("docs/JARVIS_MASTER_BUILD_MAP.md").read_text(encoding="utf-8")
    roadmap = Path("docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md").read_text(encoding="utf-8")
    handoff = Path("docs/jarvis-handoff-context.md").read_text(encoding="utf-8")
    serialized = "\n".join([routine_doc, master, roadmap, handoff]).lower()

    assert "pr #139" in serialized
    assert "local routine scheduler" in serialized
    assert "personal/family ops" in serialized
    assert "authorized account assistance" in serialized
    assert "official recovery" in serialized
    assert "no real scheduler" in serialized
    assert "no password storage" in serialized
    assert "no 2fa bypass" in serialized
    assert "no cookie or token use" in serialized
