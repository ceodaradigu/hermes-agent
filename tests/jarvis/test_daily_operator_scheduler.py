import json
import os
from pathlib import Path
import socket
import subprocess

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from jarvis.api.app import DailyOperatorPreviewRequest, InMemoryTaskStore, create_app
from jarvis.daily_operator.scheduler import (
    DailyBriefingPreview,
    DailyOperatorSchedulerStatus,
    DailyPlanPreview,
    ExecutionWindowPreview,
    MissedRunRetryPolicyPreview,
    OperatorHandoffSummaryPreview,
    RecurrencePreview,
    ReminderNotificationPreview,
    ScheduleRulePreview,
    SchedulerApprovalRequirements,
    SchedulerSafetyPolicy,
    TaskQueuePreview,
)
from jarvis.mission_control import MissionControl
from jarvis.operator_console import OperatorConsoleSnapshot
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


POST_ROUTES = {
    "/daily-operator/briefing-preview": DailyBriefingPreview,
    "/daily-operator/daily-plan": DailyPlanPreview,
    "/daily-operator/schedule-rule": ScheduleRulePreview,
    "/daily-operator/recurrence-preview": RecurrencePreview,
    "/daily-operator/task-queue-preview": TaskQueuePreview,
    "/daily-operator/reminder-preview": ReminderNotificationPreview,
    "/daily-operator/execution-window": ExecutionWindowPreview,
    "/daily-operator/retry-policy": MissedRunRetryPolicyPreview,
    "/daily-operator/handoff-summary": OperatorHandoffSummaryPreview,
    "/daily-operator/approval-requirements": SchedulerApprovalRequirements,
}

DANGEROUS_ROUTES = (
    "/daily-operator/run",
    "/daily-operator/execute",
    "/daily-operator/start-worker",
    "/daily-operator/create-cron",
    "/daily-operator/create-timer",
    "/daily-operator/send-reminder",
    "/daily-operator/send-email",
    "/daily-operator/connect-calendar",
    "/daily-operator/enqueue",
    "/daily-operator/dequeue",
)

STATUS_FALSE_FIELDS = (
    "daily_operator_available",
    "scheduler_available",
    "background_worker_enabled",
    "cron_enabled",
    "system_timer_enabled",
    "task_execution_enabled",
    "reminder_sending_enabled",
    "notification_sending_enabled",
    "email_sending_enabled",
    "external_calendar_enabled",
    "external_calls_enabled",
    "secrets_access_enabled",
    "hermes_called",
    "approval_gateway_called",
    "execution_enabled",
    "persistence_enabled",
)

FORBIDDEN_FALSE_FIELDS = STATUS_FALSE_FIELDS + (
    "would_notify",
    "would_execute",
    "would_create_tasks",
    "would_schedule_tasks",
    "would_create_scheduler",
    "would_create_cron",
    "would_create_system_timer",
    "would_register_worker",
    "would_persist_schedule",
    "would_execute_recurring",
    "would_enqueue",
    "would_dequeue",
    "would_send",
    "push_sending_enabled",
    "would_start_worker",
    "retry_enabled",
    "catchup_enabled",
    "would_retry",
    "would_catch_up",
    "would_persist",
    "approval_created",
    "approval_granted",
    "approval_rejected",
)


class FailAdapter:
    def run(self, message: str, **kwargs):
        raise AssertionError("Hermes must not be called by Daily Operator")


def _app():
    return create_app(adapter_factory=FailAdapter)


def _endpoint(app, path, method):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def _get(app, path):
    return _endpoint(app, path, "GET")()


def _post(app, path, data):
    return _endpoint(app, path, "POST")(DailyOperatorPreviewRequest(**data))


def test_status_endpoint_is_http_200_prepare_only_and_fully_disabled():
    app = _app()
    route = next(route for route in app.routes if route.path == "/daily-operator/status")
    payload = route.endpoint()

    assert "GET" in route.methods
    assert route.status_code in (None, 200)
    assert payload["prepare_only"] is True
    for key in STATUS_FALSE_FIELDS:
        assert payload[key] is False


def test_policy_endpoint_is_default_deny_and_requires_strong_approval():
    payload = _get(_app(), "/daily-operator/policy")

    assert payload["prepare_only"] is True
    assert all(payload.values())
    for key in (
        "strong_approval_required_for_background_execution",
        "strong_approval_required_for_recurring_execution",
        "strong_approval_required_for_notifications",
        "strong_approval_required_for_external_calendar",
        "strong_approval_required_for_money_or_publish_related_tasks",
    ):
        assert payload[key] is True


def test_briefing_uses_only_provided_data_and_never_reads_calendar_or_calls_external_services():
    payload = _post(
        _app(),
        "/daily-operator/briefing-preview",
        {"date": "2026-06-09", "source_data": "provided", "priorities": ["Review Phase O"]},
    )

    assert payload["source_data"] == "provided"
    assert payload["priorities"] == ["Review Phase O"]
    assert payload["no_external_calendar_read"] is True
    assert payload["no_external_calls"] is True
    assert payload["would_notify"] is False
    assert payload["would_execute"] is False


def test_daily_plan_does_not_create_tasks_schedules_or_execute():
    payload = _post(
        _app(),
        "/daily-operator/daily-plan",
        {"task_candidates": ["Prepare report"], "focus_blocks": ["09:00-10:00"]},
    )

    assert payload["task_candidates"] == ["Prepare report"]
    assert payload["would_create_tasks"] is False
    assert payload["would_schedule_tasks"] is False
    assert payload["would_execute"] is False
    assert payload["approval_required"] is True


def test_schedule_rule_never_creates_scheduler_cron_timer_worker_or_execution():
    payload = _post(_app(), "/daily-operator/schedule-rule", {"rule_name": "Morning plan", "cadence": "once"})

    assert payload["would_create_scheduler"] is False
    assert payload["would_create_cron"] is False
    assert payload["would_create_system_timer"] is False
    assert payload["would_register_worker"] is False
    assert payload["would_execute"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is False


@pytest.mark.parametrize("cadence", ["daily", "weekly", "monthly"])
def test_recurring_schedule_rule_requires_strong_approval(cadence):
    payload = _post(_app(), "/daily-operator/schedule-rule", {"cadence": cadence})
    assert payload["strong_approval_required"] is True


def test_recurrence_preview_never_persists_or_executes_recurring_work():
    payload = _post(
        _app(),
        "/daily-operator/recurrence-preview",
        {"recurrence_requested": True, "recurrence_rule": "weekly", "max_runs": 4},
    )

    assert payload["recurrence_requested"] is True
    assert payload["max_runs"] == 4
    assert payload["would_persist_schedule"] is False
    assert payload["would_execute_recurring"] is False
    assert payload["strong_approval_required"] is True


def test_task_queue_preview_never_enqueues_dequeues_executes_persists_or_calls_bridges():
    payload = _post(
        _app(),
        "/daily-operator/task-queue-preview",
        {"queued_items_preview": ["Prepare draft", "Review draft"], "execution_order": ["Prepare draft"]},
    )

    assert payload["queue_size"] == 2
    assert payload["would_enqueue"] is False
    assert payload["would_dequeue"] is False
    assert payload["would_execute"] is False
    assert payload["persistence_enabled"] is False
    assert payload["hermes_called"] is False
    assert payload["approval_gateway_called"] is False


@pytest.mark.parametrize("channel", ["email", "push", "calendar"])
def test_reminder_preview_never_sends_external_notifications_and_requires_strong_approval(channel):
    payload = _post(_app(), "/daily-operator/reminder-preview", {"reminder_requested": True, "channel": channel})

    assert payload["would_send"] is False
    assert payload["email_sending_enabled"] is False
    assert payload["push_sending_enabled"] is False
    assert payload["external_calendar_enabled"] is False
    assert payload["strong_approval_required"] is True


def test_reminder_preview_redacts_sensitive_input():
    payload = _post(
        _app(),
        "/daily-operator/reminder-preview",
        {"message_preview": "Use API key secret-value", "recipient_preview": "email address private@example.test"},
    )
    serialized = json.dumps(payload).lower()

    assert payload["message_preview"] == "[redacted sensitive input]"
    assert payload["recipient_preview"] == "[redacted sensitive input]"
    assert payload["sensitive_input_redacted"] is True
    assert "secret-value" not in serialized
    assert "private@example.test" not in serialized


def test_execution_window_never_starts_worker_or_executes_and_is_blocked():
    payload = _post(_app(), "/daily-operator/execution-window", {"window_name": "Morning"})

    assert payload["quiet_hours_respected"] is True
    assert payload["would_start_worker"] is False
    assert payload["would_execute"] is False
    assert payload["blocked"] is True


def test_retry_policy_never_retries_or_catches_up_and_side_effects_require_strong_approval():
    payload = _post(
        _app(),
        "/daily-operator/retry-policy",
        {"max_retries": 3, "backoff_preview": "5m, 15m", "side_effect_task": True},
    )

    assert payload["max_retries"] == 3
    assert payload["retry_enabled"] is False
    assert payload["catchup_enabled"] is False
    assert payload["would_retry"] is False
    assert payload["would_catch_up"] is False
    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True


def test_handoff_summary_never_persists_notifies_or_executes():
    payload = _post(_app(), "/daily-operator/handoff-summary", {"pending_preview": ["Review approval"]})

    assert payload["pending_preview"] == ["Review approval"]
    assert payload["would_notify"] is False
    assert payload["would_persist"] is False
    assert payload["would_execute"] is False


@pytest.mark.parametrize(
    "risk",
    [
        "background_requested",
        "recurring_requested",
        "notification_requested",
        "external_calendar_requested",
        "money_requested",
        "publish_requested",
    ],
)
def test_approval_requirements_describe_strong_approval_without_creating_it(risk):
    payload = _post(_app(), "/daily-operator/approval-requirements", {risk: True})

    assert payload["approval_required"] is True
    assert payload["strong_approval_required"] is True
    assert payload["approval_gateway_called"] is False
    assert payload["approval_created"] is False
    assert payload["approval_granted"] is False
    assert payload["approval_rejected"] is False


def test_all_endpoints_have_no_forbidden_side_effects(monkeypatch):
    app = _app()

    def fail(*args, **kwargs):
        raise AssertionError("Daily Operator preview attempted a forbidden side effect")

    monkeypatch.setattr(ApprovalGateway, "create_request", fail)
    monkeypatch.setattr(HermesRuntimeAdapter, "run", fail, raising=False)
    monkeypatch.setattr(MissionControl, "create_mission", fail)
    monkeypatch.setattr(InMemoryTaskStore, "create", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(os, "system", fail)
    monkeypatch.setattr(socket, "socket", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "write_bytes", fail)
    monkeypatch.setattr("builtins.open", fail)

    assert _get(app, "/daily-operator/status")["execution_enabled"] is False
    assert _get(app, "/daily-operator/policy")["no_external_calls_by_default"] is True
    for path in POST_ROUTES:
        assert _post(app, path, {})["prepare_only"] is True


def test_api_schema_does_not_request_tokens_secrets_or_external_calendar_credentials():
    fields = set(DailyOperatorPreviewRequest.model_fields)
    for forbidden in ("token", "api_key", "credentials", "calendar_token", "calendar_account", "webhook_url"):
        assert forbidden not in fields


@pytest.mark.parametrize("path", DANGEROUS_ROUTES)
def test_dangerous_routes_do_not_exist(path):
    assert path not in [route.path for route in _app().routes]


def test_no_daily_operator_websocket_exists():
    assert not any(
        route.path.startswith("/daily-operator") and route.__class__.__name__ == "APIWebSocketRoute"
        for route in _app().routes
    )


def test_command_center_and_operator_console_remain_prepare_only():
    app = _app()
    command_center = _get(app, "/command-center")
    operator = _get(app, "/operator/console/snapshot")

    assert command_center["prepare_only"] is True
    assert command_center["execution_enabled"] is False
    assert command_center["metadata"]["daily_operator_scheduler"] == "prepare_only"
    assert operator["prepare_only"] is True
    assert operator["metadata"]["daily_operator_scheduler"] == "prepare_only"
    assert operator["daily_operator_status"] == DailyOperatorSchedulerStatus.placeholder().to_dict()
    assert operator["scheduler_safety_policy"] == SchedulerSafetyPolicy.placeholder().to_dict()
    assert operator["capability_matrix"]["read_daily_operator_status"] is True
    assert operator["capability_matrix"]["read_scheduler_safety_policy"] is True
    assert operator["capability_matrix"]["preview_daily_operator"] is True
    assert operator["capability_matrix"]["run_background"] is False
    for key in STATUS_FALSE_FIELDS:
        assert operator["daily_operator_status"][key] is False


@pytest.mark.parametrize(
    "model",
    [
        DailyOperatorSchedulerStatus,
        DailyBriefingPreview,
        DailyPlanPreview,
        ScheduleRulePreview,
        RecurrencePreview,
        TaskQueuePreview,
        ReminderNotificationPreview,
        ExecutionWindowPreview,
        MissedRunRetryPolicyPreview,
        OperatorHandoffSummaryPreview,
        SchedulerApprovalRequirements,
    ],
)
def test_from_dict_cannot_enable_forbidden_scheduler_capabilities(model):
    hostile = {"prepare_only": False, **{key: True for key in FORBIDDEN_FALSE_FIELDS}}
    payload = model.from_dict(hostile).to_dict()

    assert payload["prepare_only"] is True
    for key in FORBIDDEN_FALSE_FIELDS:
        if key in payload:
            assert payload[key] is False


def test_policy_from_dict_cannot_disable_safety_requirements():
    payload = SchedulerSafetyPolicy.from_dict(
        {name: False for name in SchedulerSafetyPolicy.__dataclass_fields__}
    ).to_dict()
    assert all(payload.values())


def test_operator_console_from_dict_cannot_enable_daily_operator():
    payload = OperatorConsoleSnapshot.from_dict(
        {
            "daily_operator_status": {
                "background_worker_enabled": True,
                "cron_enabled": True,
                "task_execution_enabled": True,
                "persistence_enabled": True,
            },
            "scheduler_safety_policy": {"no_task_execution_by_default": False},
            "capability_matrix": {"run_background": True},
        }
    ).to_dict()

    assert payload["daily_operator_status"]["background_worker_enabled"] is False
    assert payload["daily_operator_status"]["cron_enabled"] is False
    assert payload["daily_operator_status"]["task_execution_enabled"] is False
    assert payload["daily_operator_status"]["persistence_enabled"] is False
    assert payload["scheduler_safety_policy"]["no_task_execution_by_default"] is True
    assert payload["capability_matrix"]["run_background"] is False
