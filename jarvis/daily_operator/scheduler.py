from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_UNKNOWN = "unknown"
_REDACTED = "[redacted sensitive input]"
_CADENCES = {"once", "daily", "weekly", "monthly", "manual", "unknown"}
_CHANNELS = {"none", "local", "email", "push", "calendar", "unknown"}
_EXTERNAL_NOTIFICATION_CHANNELS = {"email", "push", "calendar"}
_RECURRING_CADENCES = {"daily", "weekly", "monthly"}
_SENSITIVE_MARKERS = (
    ".env", "api key", "api-key", "api_key", "apikey", "authorization", "bearer",
    "client secret", "client_secret", "credential", "credentials", "email address",
    "password", "phone number", "private key", "private_key", "secret", "token",
)


@dataclass(frozen=True)
class DailyOperatorSchedulerStatus:
    prepare_only: bool = True
    daily_operator_available: bool = False
    scheduler_available: bool = False
    background_worker_enabled: bool = False
    cron_enabled: bool = False
    system_timer_enabled: bool = False
    task_execution_enabled: bool = False
    reminder_sending_enabled: bool = False
    notification_sending_enabled: bool = False
    email_sending_enabled: bool = False
    external_calendar_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False
    persistence_enabled: bool = False

    def __post_init__(self) -> None:
        _force_safe(self)

    @classmethod
    def placeholder(cls) -> "DailyOperatorSchedulerStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "DailyOperatorSchedulerStatus":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class SchedulerSafetyPolicy:
    prepare_only: bool = True
    no_background_workers_by_default: bool = True
    no_cron_by_default: bool = True
    no_system_timers_by_default: bool = True
    no_task_execution_by_default: bool = True
    no_notification_sending_by_default: bool = True
    no_email_sending_by_default: bool = True
    no_external_calendar_by_default: bool = True
    no_external_calls_by_default: bool = True
    no_secret_access_by_default: bool = True
    review_required_before_schedule_activation: bool = True
    strong_approval_required_for_background_execution: bool = True
    strong_approval_required_for_recurring_execution: bool = True
    strong_approval_required_for_notifications: bool = True
    strong_approval_required_for_external_calendar: bool = True
    strong_approval_required_for_money_or_publish_related_tasks: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in self.__dataclass_fields__:
            if name != "prepare_only":
                object.__setattr__(self, name, True)

    @classmethod
    def placeholder(cls) -> "SchedulerSafetyPolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "SchedulerSafetyPolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class DailyBriefingPreview:
    prepare_only: bool = True
    date: str = _UNKNOWN
    timezone: str = _UNKNOWN
    priorities: List[str] = field(default_factory=list)
    open_loops: List[str] = field(default_factory=list)
    blocked_items: List[str] = field(default_factory=list)
    scheduled_items_preview: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)
    source_data: str = _UNKNOWN
    no_external_calendar_read: bool = True
    no_external_calls: bool = True
    would_notify: bool = False
    would_execute: bool = False
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _safe_common(self, text_fields=("date", "timezone"))
        object.__setattr__(self, "source_data", _choice(self.source_data, {"provided", "unknown"}))
        _force_true(self, "no_external_calendar_read", "no_external_calls")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DailyBriefingPreview":
        source = dict(data or {})
        return cls(
            date=source.get("date", _UNKNOWN),
            timezone=source.get("timezone", _UNKNOWN),
            priorities=_safe_list(source.get("priorities")),
            open_loops=_safe_list(source.get("open_loops")),
            blocked_items=_safe_list(source.get("blocked_items")),
            scheduled_items_preview=_safe_list(source.get("scheduled_items_preview")),
            risk_warnings=_safe_list(source.get("risk_warnings")),
            source_data="provided" if source.get("source_data") == "provided" else _UNKNOWN,
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class DailyPlanPreview:
    prepare_only: bool = True
    plan_date: str = _UNKNOWN
    focus_blocks: List[str] = field(default_factory=list)
    task_candidates: List[str] = field(default_factory=list)
    priority_order: List[str] = field(default_factory=list)
    estimated_effort: str = _UNKNOWN
    dependency_notes: List[str] = field(default_factory=list)
    blocked_by_approval: List[str] = field(default_factory=list)
    would_create_tasks: bool = False
    would_schedule_tasks: bool = False
    would_execute: bool = False
    approval_required: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, text_fields=("plan_date", "estimated_effort"))
        _force_true(self, "approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DailyPlanPreview":
        source = dict(data or {})
        return cls(
            plan_date=source.get("plan_date", _UNKNOWN),
            focus_blocks=_safe_list(source.get("focus_blocks")),
            task_candidates=_safe_list(source.get("task_candidates")),
            priority_order=_safe_list(source.get("priority_order")),
            estimated_effort=source.get("estimated_effort", _UNKNOWN),
            dependency_notes=_safe_list(source.get("dependency_notes")),
            blocked_by_approval=_safe_list(source.get("blocked_by_approval")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ScheduleRulePreview:
    prepare_only: bool = True
    rule_name: str = _UNKNOWN
    cadence: str = _UNKNOWN
    start_time: str = _UNKNOWN
    timezone: str = _UNKNOWN
    allowed_window: str = _UNKNOWN
    quiet_hours: str = _UNKNOWN
    would_create_scheduler: bool = False
    would_create_cron: bool = False
    would_create_system_timer: bool = False
    would_register_worker: bool = False
    would_execute: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _safe_common(self, text_fields=("rule_name", "start_time", "timezone", "allowed_window", "quiet_hours"))
        cadence = _choice(self.cadence, _CADENCES)
        object.__setattr__(self, "cadence", cadence)
        object.__setattr__(
            self,
            "strong_approval_required",
            bool(self.strong_approval_required or cadence in _RECURRING_CADENCES),
        )
        _force_true(self, "approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ScheduleRulePreview":
        source = dict(data or {})
        return cls(
            rule_name=source.get("rule_name", _UNKNOWN),
            cadence=source.get("cadence", _UNKNOWN),
            start_time=source.get("start_time", _UNKNOWN),
            timezone=source.get("timezone", _UNKNOWN),
            allowed_window=source.get("allowed_window", _UNKNOWN),
            quiet_hours=source.get("quiet_hours", _UNKNOWN),
            strong_approval_required=_strong_risk_requested(source),
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class RecurrencePreview:
    prepare_only: bool = True
    recurrence_requested: bool = False
    recurrence_rule: str = _UNKNOWN
    next_run_preview: str = _UNKNOWN
    max_runs: Optional[int] = None
    stop_condition: str = _UNKNOWN
    would_persist_schedule: bool = False
    would_execute_recurring: bool = False
    strong_approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _safe_common(self, text_fields=("recurrence_rule", "next_run_preview", "stop_condition"))
        object.__setattr__(self, "recurrence_requested", bool(self.recurrence_requested))
        object.__setattr__(self, "max_runs", _safe_non_negative_int(self.max_runs))
        _force_true(self, "strong_approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "RecurrencePreview":
        source = dict(data or {})
        return cls(
            recurrence_requested=source.get("recurrence_requested") is True,
            recurrence_rule=source.get("recurrence_rule", _UNKNOWN),
            next_run_preview=source.get("next_run_preview", _UNKNOWN),
            max_runs=source.get("max_runs"),
            stop_condition=source.get("stop_condition", _UNKNOWN),
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class TaskQueuePreview:
    prepare_only: bool = True
    queued_items_preview: List[str] = field(default_factory=list)
    queue_size: int = 0
    execution_order: List[str] = field(default_factory=list)
    blocked_items: List[str] = field(default_factory=list)
    would_enqueue: bool = False
    would_dequeue: bool = False
    would_execute: bool = False
    persistence_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False

    def __post_init__(self) -> None:
        _safe_common(self)
        object.__setattr__(self, "queue_size", len(self.queued_items_preview))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "TaskQueuePreview":
        source = dict(data or {})
        return cls(
            queued_items_preview=_safe_list(source.get("queued_items_preview")),
            execution_order=_safe_list(source.get("execution_order")),
            blocked_items=_safe_list(source.get("blocked_items")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ReminderNotificationPreview:
    prepare_only: bool = True
    reminder_requested: bool = False
    channel: str = "none"
    message_preview: str = _UNKNOWN
    recipient_preview: str = _UNKNOWN
    would_send: bool = False
    email_sending_enabled: bool = False
    push_sending_enabled: bool = False
    external_calendar_enabled: bool = False
    strong_approval_required: bool = False
    sensitive_input_redacted: bool = False

    def __post_init__(self) -> None:
        original = (self.message_preview, self.recipient_preview)
        object.__setattr__(self, "reminder_requested", bool(self.reminder_requested))
        object.__setattr__(self, "channel", _choice(self.channel, _CHANNELS))
        object.__setattr__(self, "message_preview", _safe_text(self.message_preview, _UNKNOWN))
        object.__setattr__(self, "recipient_preview", _safe_text(self.recipient_preview, _UNKNOWN))
        object.__setattr__(
            self,
            "strong_approval_required",
            bool(self.strong_approval_required or self.channel in _EXTERNAL_NOTIFICATION_CHANNELS),
        )
        object.__setattr__(self, "sensitive_input_redacted", bool(self.sensitive_input_redacted or _was_redacted(original)))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ReminderNotificationPreview":
        source = dict(data or {})
        return cls(
            reminder_requested=source.get("reminder_requested") is True,
            channel=source.get("channel", "none"),
            message_preview=source.get("message_preview", _UNKNOWN),
            recipient_preview=source.get("recipient_preview", _UNKNOWN),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class ExecutionWindowPreview:
    prepare_only: bool = True
    window_name: str = _UNKNOWN
    allowed_start: str = _UNKNOWN
    allowed_end: str = _UNKNOWN
    timezone: str = _UNKNOWN
    quiet_hours_respected: bool = True
    max_runtime: str = _UNKNOWN
    would_start_worker: bool = False
    would_execute: bool = False
    blocked: bool = True

    def __post_init__(self) -> None:
        _safe_common(self, text_fields=("window_name", "allowed_start", "allowed_end", "timezone", "max_runtime"))
        _force_true(self, "quiet_hours_respected", "blocked")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ExecutionWindowPreview":
        source = dict(data or {})
        return cls(
            window_name=source.get("window_name", _UNKNOWN),
            allowed_start=source.get("allowed_start", _UNKNOWN),
            allowed_end=source.get("allowed_end", _UNKNOWN),
            timezone=source.get("timezone", _UNKNOWN),
            max_runtime=source.get("max_runtime", _UNKNOWN),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class MissedRunRetryPolicyPreview:
    prepare_only: bool = True
    retry_enabled: bool = False
    catchup_enabled: bool = False
    would_retry: bool = False
    would_catch_up: bool = False
    max_retries: int = 0
    backoff_preview: str = _UNKNOWN
    approval_required: bool = True
    strong_approval_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_retries", _safe_non_negative_int(self.max_retries) or 0)
        object.__setattr__(self, "backoff_preview", _safe_text(self.backoff_preview, _UNKNOWN))
        object.__setattr__(self, "strong_approval_required", bool(self.strong_approval_required))
        _force_true(self, "approval_required")
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "MissedRunRetryPolicyPreview":
        source = dict(data or {})
        return cls(
            max_retries=source.get("max_retries", 0),
            backoff_preview=source.get("backoff_preview", _UNKNOWN),
            strong_approval_required=_strong_risk_requested(source) or source.get("side_effect_task") is True,
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class OperatorHandoffSummaryPreview:
    prepare_only: bool = True
    summary_date: str = _UNKNOWN
    completed_preview: List[str] = field(default_factory=list)
    pending_preview: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    approvals_needed: List[str] = field(default_factory=list)
    next_actions_preview: List[str] = field(default_factory=list)
    would_notify: bool = False
    would_persist: bool = False
    would_execute: bool = False

    def __post_init__(self) -> None:
        _safe_common(self, text_fields=("summary_date",))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "OperatorHandoffSummaryPreview":
        source = dict(data or {})
        return cls(
            summary_date=source.get("summary_date", _UNKNOWN),
            completed_preview=_safe_list(source.get("completed_preview")),
            pending_preview=_safe_list(source.get("pending_preview")),
            risks=_safe_list(source.get("risks")),
            approvals_needed=_safe_list(source.get("approvals_needed")),
            next_actions_preview=_safe_list(source.get("next_actions_preview")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class SchedulerApprovalRequirements:
    prepare_only: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    approval_gateway_called: bool = False
    approval_created: bool = False
    approval_granted: bool = False
    approval_rejected: bool = False

    def __post_init__(self) -> None:
        _force_true(self, "approval_required")
        object.__setattr__(self, "strong_approval_required", bool(self.strong_approval_required))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "SchedulerApprovalRequirements":
        return cls(strong_approval_required=_strong_risk_requested(dict(data or {})))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


_FORCED_FALSE = {
    "daily_operator_available", "scheduler_available", "background_worker_enabled", "cron_enabled",
    "system_timer_enabled", "task_execution_enabled", "reminder_sending_enabled",
    "notification_sending_enabled", "email_sending_enabled", "external_calendar_enabled",
    "external_calls_enabled", "secrets_access_enabled", "hermes_called", "approval_gateway_called",
    "execution_enabled", "persistence_enabled", "would_notify", "would_execute", "would_create_tasks",
    "would_schedule_tasks", "would_create_scheduler", "would_create_cron", "would_create_system_timer",
    "would_register_worker", "would_persist_schedule", "would_execute_recurring", "would_enqueue",
    "would_dequeue", "would_send", "push_sending_enabled", "would_start_worker", "retry_enabled",
    "catchup_enabled", "would_retry", "would_catch_up", "would_persist", "approval_created",
    "approval_granted", "approval_rejected",
}


def _force_safe(value: Any) -> None:
    object.__setattr__(value, "prepare_only", True)
    for name in _FORCED_FALSE:
        if name in value.__dataclass_fields__:
            object.__setattr__(value, name, False)


def _force_true(value: Any, *names: str) -> None:
    for name in names:
        object.__setattr__(value, name, True)


def _serialize(value: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        if isinstance(item, list):
            item = list(item)
        result[name] = item
    result["prepare_only"] = True
    for name in _FORCED_FALSE:
        if name in result:
            result[name] = False
    return result


def _safe_common(value: Any, *, text_fields: tuple[str, ...] = ()) -> None:
    for name in text_fields:
        object.__setattr__(value, name, _safe_text(getattr(value, name), _UNKNOWN))
    for name in value.__dataclass_fields__:
        if isinstance(getattr(value, name), list):
            object.__setattr__(value, name, _safe_list(getattr(value, name)))


def _safe_text(value: Any, default: str = "") -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return default
    if any(marker in text.lower() for marker in _SENSITIVE_MARKERS):
        return _REDACTED
    return text[:500]


def _safe_list(value: Any) -> List[str]:
    items = value if isinstance(value, list) else []
    return [_safe_text(item) for item in items[:100] if _safe_text(item)]


def _choice(value: Any, choices: set[str]) -> str:
    text = str(value or "").strip().lower()
    return text if text in choices else _UNKNOWN


def _safe_non_negative_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _was_redacted(values: Any) -> bool:
    return any(_safe_text(value, _UNKNOWN) == _REDACTED for value in values)


def _strong_risk_requested(source: Dict[str, Any]) -> bool:
    names = (
        "background", "background_execution", "recurring", "recurrence", "notification",
        "external_notification", "external_calendar", "calendar", "money", "money_movement",
        "payment", "spend", "publish", "deploy", "external_side_effect", "side_effect_task",
    )
    return (
        _choice(source.get("cadence"), _CADENCES) in _RECURRING_CADENCES
        or _choice(source.get("channel"), _CHANNELS) in _EXTERNAL_NOTIFICATION_CHANNELS
        or any(source.get(f"{name}_requested") is True for name in names)
        or any(source.get(name) is True for name in names)
    )
