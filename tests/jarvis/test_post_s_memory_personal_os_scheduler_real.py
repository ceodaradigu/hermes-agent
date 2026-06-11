from __future__ import annotations

import builtins
import socket
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (
    MemoryRecordPreviewRequest,
    PersonalOSStatePreviewRequest,
    SchedulerControlPreviewRequest,
    create_app,
)
from jarvis.approval_hardening import ApprovalHardeningService, ApprovalKind
from jarvis.command_center import build_command_center_view_model
from jarvis.operator_console import build_operator_console_snapshot
from jarvis.operational_consolidation import NEXT_RECOMMENDED_MACRO_PR, build_operational_system_status
from jarvis.personal_memory import ApprovedMemoryRecord, PersonalMemoryControlPlane
from jarvis.personal_os.control_plane import PersonalOSControlPlane, PersonalOSState, StopControls
from jarvis.scheduler_control import SchedulerControlPlane, SchedulerItem, SchedulerItemStatus


DOC = Path("docs/jarvis-post-s-memory-personal-os-scheduler-real.md")
DANGEROUS_ROUTES = (
    "/memory/autoload", "/memory/auto-activate", "/memory/load-secrets", "/memory/read-env",
    "/scheduler/start", "/scheduler/run", "/scheduler/execute", "/scheduler/worker/start",
    "/scheduler/watch", "/scheduler/send", "/scheduler/notify", "/scheduler/call-tool",
    "/personal-os/read-email", "/personal-os/read-calendar", "/personal-os/read-files",
    "/personal-os/sync-external", "/personal-os/start-agent",
)


def _route(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route
    return None


def _record(control, **overrides):
    values = {
        "memory_type": "preference",
        "content_summary": "Prefer concise reviews",
        "source": "operator_provided",
        "created_by": "operator",
        "reason": "Explicit preference",
    }
    values.update(overrides)
    return control.preview_record(**values)


def _approval(record, *, strong=False, status="approved"):
    service = ApprovalHardeningService()
    approval = service.request(
        action_type=record.activation_context()["action_type"],
        context=record.activation_context(),
        approval_kind=ApprovalKind.STRONG if strong else ApprovalKind.NORMAL,
    )
    if status == "approved":
        service.decide(
            approval.approval_id,
            "approved",
            confirmation_phrase=approval.user_confirmation_phrase if strong else None,
        )
    elif status == "rejected":
        service.decide(approval.approval_id, "rejected")
    elif status == "revoked":
        service.decide(approval.approval_id, "approved")
        service.revoke(approval.approval_id)
    return approval


def test_statuses_are_control_plane_without_phase_t_or_enabled_runtime():
    personal = PersonalOSControlPlane().status()
    scheduler = SchedulerControlPlane().status()
    operational = build_operational_system_status().to_dict()
    assert personal["personal_os_control_plane_available"] is True
    assert scheduler["scheduler_control_plane_available"] is True
    assert operational["no_phase_t"] is True
    assert NEXT_RECOMMENDED_MACRO_PR == "Post-S Macro 9 — SaaS/Product Builder + Publishing/Deploy Execution"
    for payload in (personal, scheduler, operational):
        for field in ("execution_enabled", "side_effects_enabled", "watcher_enabled", "external_sources_enabled"):
            assert payload[field] is False
    assert personal["private_sources_enabled"] is False
    assert personal["autoload_enabled"] is False


def test_memory_defaults_redaction_and_approval_requirements():
    control = PersonalMemoryControlPlane()
    normal = _record(control)
    sensitive = _record(control, sensitivity_level="sensitive")
    persistent = _record(control, sensitivity_level="sensitive", persistent=True)
    secret = _record(control, content_summary="read .env token=abc", reason="password secret")
    assert normal.approved is False and normal.active is False
    assert sensitive.requires_approval is True
    assert persistent.requires_strong_approval is True
    assert _record(control, sensitivity_level="unknown-risk").requires_approval is True
    assert ".env" not in str(secret.to_dict()).lower()
    assert "token=abc" not in str(secret.to_dict()).lower()
    assert "sensitive content was redacted" in secret.blocked_reasons
    assert control.preview_activation(secret).ready_for_activation is False


def test_memory_activation_respects_approval_context_and_never_activates():
    control = PersonalMemoryControlPlane()
    sensitive = _record(control, sensitivity_level="sensitive", approved=True)
    approved = _approval(sensitive)
    ready = control.preview_activation(sensitive, approval=approved)
    mismatch = _record(control, sensitivity_level="sensitive", approved=True, memory_id="changed")
    mismatch_result = control.preview_activation(mismatch, approval=approved)
    assert ready.ready_for_activation is True
    assert ready.would_activate is False and ready.active is False
    assert ready.memory_is_permission is False
    assert mismatch_result.ready_for_activation is False
    assert mismatch_result.permission_gate.context_matches is False


@pytest.mark.parametrize("status", ["pending", "rejected", "revoked", "expired"])
def test_invalid_approval_states_block_sensitive_memory(status):
    control = PersonalMemoryControlPlane()
    record = _record(control, sensitivity_level="sensitive", approved=True)
    if status == "expired":
        service = ApprovalHardeningService()
        approval = service.request(
            action_type=record.activation_context()["action_type"],
            context=record.activation_context(),
            expires_at=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
        )
        service.refresh_expiration(approval)
    else:
        approval = _approval(record, status=status)
    result = control.preview_activation(record, approval=approval)
    assert result.ready_for_activation is False
    assert result.permission_gate.approval_status == status


def test_strong_approval_is_required_for_persistent_sensitive_memory():
    control = PersonalMemoryControlPlane()
    record = _record(control, sensitivity_level="sensitive", persistent=True, approved=True)
    normal = control.preview_activation(record, approval=_approval(record))
    strong = control.preview_activation(record, approval=_approval(record, strong=True))
    assert normal.ready_for_activation is False
    assert strong.permission_gate.context_matches is True
    assert strong.ready_for_activation is True
    assert strong.would_activate is False


def test_memory_deactivation_is_reversible_preview_only():
    control = PersonalMemoryControlPlane()
    record = ApprovedMemoryRecord(
        memory_id="m1", memory_type="preference", content_summary="summary", source="operator",
        created_by="operator", reason="reason", approved=True, active=True,
    )
    result = control.preview_deactivation(record)
    assert result["record"]["active"] is False
    assert result["reversible"] is True
    assert result["would_deactivate"] is False


def test_personal_os_state_and_stop_controls_never_read_or_execute():
    controls = StopControls(global_pause=True)
    state = PersonalOSState(
        external_sources_enabled=True, private_sources_enabled=True, execution_enabled=True,
        side_effects_enabled=True, autoload_enabled=True, scheduler_enabled=True, watcher_enabled=True,
        stop_controls=controls,
    )
    assert state.external_sources_enabled is False
    assert state.private_sources_enabled is False
    assert state.execution_enabled is False
    assert state.autoload_enabled is False
    assert controls.memory_blocked and controls.scheduler_blocked and controls.routines_blocked


def test_scheduler_items_and_due_preview_never_execute_notify_or_call_tools():
    control = SchedulerControlPlane()
    due_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    reminder = control.preview_item(
        title="Reminder", item_type="reminder", status="scheduled", due_at=due_at,
        side_effects=True, tool_invocation_required=True, external_call_required=True,
        private_source_required=True,
    )
    routine = control.preview_item(title="Routine", item_type="routine", status="scheduled", due_at=due_at)
    result = control.preview_due([reminder, routine])
    assert all(item.status == SchedulerItemStatus.DUE for item in result.due_items)
    for field in ("would_execute", "would_notify", "would_call_tools", "would_call_external", "execution_enabled", "side_effects_enabled"):
        assert getattr(result, field) is False
    assert reminder.would_execute is False and reminder.would_notify is False
    assert routine.would_execute is False
    assert {"scheduler side effects are disabled", "scheduler tool invocation is disabled", "scheduler external calls are disabled", "scheduler private source access is disabled"} <= set(result.blocked_reasons)


def test_scheduler_pause_cancel_and_completed_preview_are_state_only():
    control = SchedulerControlPlane()
    paused = SchedulerItem("p", "paused", status="paused")
    cancelled = SchedulerItem("c", "cancelled", status="cancelled")
    completed = SchedulerItem("x", "completed", status="completed_preview")
    result = control.preview_due([paused, cancelled, completed], stop_controls=StopControls(scheduler_paused=True))
    assert result.paused_items == [paused]
    assert result.cancelled_items == [cancelled]
    assert completed in result.next_items
    assert "scheduler paused by stop controls" in result.blocked_reasons
    assert result.would_execute is False
    assert control.preview_pause(completed).status == SchedulerItemStatus.PAUSED
    assert control.preview_resume(paused).status == SchedulerItemStatus.DRAFT
    assert control.preview_cancel(completed).status == SchedulerItemStatus.CANCELLED
    assert control.preview_cancel(completed).would_execute is False


def test_daily_and_weekly_reviews_are_preview_only_and_projected():
    control = SchedulerControlPlane()
    daily = control.preview_daily_review(priorities=["focus"], recommended_next_actions=["review"])
    weekly = control.preview_weekly_review(roi_or_monetization_signals=["projected opportunity"])
    for review in (daily, weekly):
        assert review.would_execute is False
        assert review.would_send is False
        assert review.would_call_tools is False
    assert weekly.roi_signals_are_projected_only is True


def test_api_routes_are_prepare_only_absent_dangerous_and_do_not_mutate_or_call_external(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("subprocess called"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: pytest.fail("network called"))
    original_open = builtins.open

    def guarded_open(file, *args, **kwargs):
        if str(file).endswith(".env"):
            pytest.fail(".env read")
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes called"))
    missions_before = app.state.mission_control.list_missions()
    tasks_before = app.state.task_store.list()
    assert _route(app, "/personal-os/status", "GET").endpoint()["prepare_only"] is True
    assert _route(app, "/personal-os/policy", "GET").endpoint()["prepare_only"] is True
    assert _route(app, "/personal-os/preview-state", "POST").endpoint(PersonalOSStatePreviewRequest())["execution_enabled"] is False
    memory = MemoryRecordPreviewRequest(memory_type="preference", content_summary="summary")
    assert _route(app, "/memory/preview-record", "POST").endpoint(memory)["active"] is False
    assert _route(app, "/memory/preview-activation", "POST").endpoint(memory)["autoload_enabled"] is False
    assert _route(app, "/memory/preview-deactivation", "POST").endpoint(memory)["would_deactivate"] is False
    assert _route(app, "/scheduler/status", "GET").endpoint()["scheduler_worker_enabled"] is False
    assert _route(app, "/scheduler/policy", "GET").endpoint()["due_does_not_execute"] is True
    scheduler = SchedulerControlPreviewRequest(item_id="item", title="preview")
    for path in (
        "/scheduler/preview-item", "/scheduler/preview-due", "/scheduler/preview-daily-review",
        "/scheduler/preview-weekly-review", "/scheduler/preview-stop-controls",
    ):
        assert _route(app, path, "POST").endpoint(scheduler)["prepare_only"] is True
    assert app.state.mission_control.list_missions() == missions_before == []
    assert app.state.task_store.list() == tasks_before == []
    for path in DANGEROUS_ROUTES:
        assert _route(app, path, "GET") is None
        assert _route(app, path, "POST") is None


def test_operational_command_center_operator_console_and_docs_reflect_macro_5():
    status = build_operational_system_status().to_dict()
    command = build_command_center_view_model(view_id="post-s-5", generated_at="2026-06-10T00:00:00+00:00")
    operator = build_operator_console_snapshot(view_id="post-s-5", generated_at="2026-06-10T00:00:00+00:00")
    for field in (
        "approved_memory_records_available", "personal_os_control_plane_available",
        "scheduler_control_plane_available", "daily_review_preview_available",
        "weekly_review_preview_available", "stop_controls_available",
        "memory_is_not_permission", "scheduler_due_is_not_execution",
    ):
        assert status[field] is True
    for field in (
        "memory_autoload_enabled", "memory_auto_activation_enabled", "scheduler_worker_enabled",
        "watcher_enabled", "external_sources_enabled", "private_sources_enabled",
        "scheduler_execution_enabled", "notifications_enabled", "tool_invocation_from_scheduler_enabled",
    ):
        assert status[field] is False
    for marker in (
        "post_s_memory_personal_os_scheduler", "approved_memory_records", "personal_os_control_plane",
        "scheduler_control_plane", "daily_review_preview", "weekly_review_preview", "stop_controls",
        "memory_autoload_disabled", "memory_is_not_permission", "scheduler_due_not_execution",
        "scheduler_worker_disabled", "watchers_disabled", "external_sources_disabled", "notifications_disabled",
    ):
        assert command.metadata[marker] == "prepare_only"
        assert operator.metadata[marker] == "prepare_only"
    content = DOC.read_text(encoding="utf-8")
    assert "no es Phase T" in content
    assert "Due no ejecuta" in content
    assert "Post-S Macro 6" in content
