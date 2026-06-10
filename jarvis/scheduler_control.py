from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.personal_os.control_plane import StopControls


class SchedulerItemType(str, Enum):
    REMINDER = "reminder"
    ROUTINE = "routine"
    DAILY_REVIEW = "daily_review"
    WEEKLY_REVIEW = "weekly_review"
    APPROVAL_CHECK = "approval_check"
    MAINTENANCE = "maintenance"


class SchedulerItemStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    DUE = "due"
    COMPLETED_PREVIEW = "completed_preview"


@dataclass(frozen=True)
class SchedulerItem:
    item_id: str
    title: str
    item_type: SchedulerItemType = SchedulerItemType.REMINDER
    schedule_expression: Optional[str] = None
    due_at: Optional[str] = None
    timezone: str = "UTC"
    payload_summary: Dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False
    requires_strong_approval: bool = False
    side_effects: bool = False
    tool_invocation_required: bool = False
    controlled_runtime_required: bool = False
    external_call_required: bool = False
    private_source_required: bool = False
    status: SchedulerItemStatus = SchedulerItemStatus.DRAFT
    created_at: str = ""
    last_previewed_at: Optional[str] = None
    blocked_reasons: List[str] = field(default_factory=list)
    prepare_only: bool = True
    would_execute: bool = False
    would_notify: bool = False
    would_call_tools: bool = False
    would_call_external: bool = False
    execution_enabled: bool = False
    side_effects_enabled: bool = False

    def __post_init__(self) -> None:
        safe_payload, _ = redact_sensitive_data(dict(self.payload_summary or {}))
        object.__setattr__(self, "item_type", SchedulerItemType(self.item_type))
        object.__setattr__(self, "status", SchedulerItemStatus(self.status))
        object.__setattr__(self, "title", _clean_text(self.title)[:240])
        object.__setattr__(self, "timezone", _clean_text(self.timezone) or "UTC")
        object.__setattr__(self, "schedule_expression", _optional_text(self.schedule_expression))
        object.__setattr__(self, "payload_summary", safe_payload)
        object.__setattr__(self, "blocked_reasons", _deduplicate(self.blocked_reasons))
        object.__setattr__(self, "created_at", self.created_at or _now_iso())
        object.__setattr__(self, "prepare_only", True)
        for name in (
            "would_execute",
            "would_notify",
            "would_call_tools",
            "would_call_external",
            "execution_enabled",
            "side_effects_enabled",
        ):
            object.__setattr__(self, name, False)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["item_type"] = self.item_type.value
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class SchedulerPreviewResult:
    scheduler_available: bool = True
    due_items: List[SchedulerItem] = field(default_factory=list)
    next_items: List[SchedulerItem] = field(default_factory=list)
    paused_items: List[SchedulerItem] = field(default_factory=list)
    cancelled_items: List[SchedulerItem] = field(default_factory=list)
    would_execute: bool = False
    would_notify: bool = False
    would_call_tools: bool = False
    would_call_external: bool = False
    execution_enabled: bool = False
    side_effects_enabled: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    audit_events: List[Dict[str, Any]] = field(default_factory=list)
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "scheduler_available", True)
        for name in ("would_execute", "would_notify", "would_call_tools", "would_call_external", "execution_enabled", "side_effects_enabled"):
            object.__setattr__(self, name, False)
        object.__setattr__(self, "blocked_reasons", _deduplicate(self.blocked_reasons))
        object.__setattr__(self, "audit_events", list(self.audit_events))
        object.__setattr__(self, "prepare_only", True)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        for name in ("due_items", "next_items", "paused_items", "cancelled_items"):
            data[name] = [item.to_dict() for item in getattr(self, name)]
        return data


@dataclass(frozen=True)
class DailyReviewPreview:
    review_id: str
    date: str
    priorities: List[str] = field(default_factory=list)
    pending_approvals: List[str] = field(default_factory=list)
    pending_memory_reviews: List[str] = field(default_factory=list)
    due_scheduler_items: List[str] = field(default_factory=list)
    money_or_roi_items: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    recommended_next_actions: List[str] = field(default_factory=list)
    would_execute: bool = False
    would_send: bool = False
    would_call_tools: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    prepare_only: bool = True

    def __post_init__(self) -> None:
        _force_review_safe(self)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WeeklyReviewPreview:
    review_id: str
    week: str
    completed_items: List[str] = field(default_factory=list)
    pending_items: List[str] = field(default_factory=list)
    postponed_items: List[str] = field(default_factory=list)
    memory_changes: List[str] = field(default_factory=list)
    scheduler_changes: List[str] = field(default_factory=list)
    roi_or_monetization_signals: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    recommended_next_actions: List[str] = field(default_factory=list)
    roi_signals_are_projected_only: bool = True
    would_execute: bool = False
    would_send: bool = False
    would_call_tools: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    prepare_only: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "roi_signals_are_projected_only", True)
        _force_review_safe(self)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SchedulerControlPlane:
    """In-memory scheduler calculation and review previews. No worker or execution path."""

    def status(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "scheduler_available": True,
            "scheduler_control_plane_available": True,
            "daily_review_preview_available": True,
            "weekly_review_preview_available": True,
            "stop_controls_available": True,
            "scheduler_worker_enabled": False,
            "watcher_enabled": False,
            "execution_enabled": False,
            "scheduler_execution_enabled": False,
            "side_effects_enabled": False,
            "notifications_enabled": False,
            "external_sources_enabled": False,
            "private_sources_enabled": False,
            "tool_invocation_from_scheduler_enabled": False,
            "scheduler_due_is_not_execution": True,
        }

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "due_does_not_execute": True,
            "reminder_due_does_not_notify": True,
            "routine_registered_does_not_execute": True,
            "completed_preview_does_not_mean_executed": True,
            "approval_does_not_execute": True,
            "runtime_safe_to_execute_does_not_execute": True,
            "tool_safe_to_invoke_does_not_execute": True,
            "side_effects_blocked": True,
            "tool_invocations_blocked": True,
            "external_calls_blocked": True,
            "private_sources_blocked": True,
        }

    def preview_item(self, **values: Any) -> SchedulerItem:
        allowed = set(SchedulerItem.__dataclass_fields__)
        source = {key: value for key, value in dict(values).items() if key in allowed}
        source["item_id"] = _clean_text(source.get("item_id")) or str(uuid4())
        source["title"] = source.get("title") or "untitled scheduler preview"
        source["payload_summary"] = source.get("payload_summary") or {}
        blocked = list(source.get("blocked_reasons") or [])
        if source.get("side_effects"):
            blocked.append("scheduler side effects are disabled")
        if source.get("tool_invocation_required"):
            blocked.append("scheduler tool invocation is disabled")
        if source.get("external_call_required"):
            blocked.append("scheduler external calls are disabled")
        if source.get("private_source_required"):
            blocked.append("scheduler private source access is disabled")
        if source.get("due_at") and _try_parse_datetime(source["due_at"]) is None:
            blocked.append("due_at is invalid")
        source["blocked_reasons"] = blocked
        return SchedulerItem(**source)

    def preview_due(
        self,
        items: List[SchedulerItem],
        *,
        now: Optional[str] = None,
        stop_controls: Optional[StopControls] = None,
    ) -> SchedulerPreviewResult:
        current = _parse_datetime(now) if now else datetime.now(timezone.utc)
        due, upcoming, paused, cancelled = [], [], [], []
        blocked = []
        controls = stop_controls or StopControls()
        if controls.scheduler_blocked:
            blocked.append("scheduler paused by stop controls")
        for item in items:
            blocked.extend(item.blocked_reasons)
            if item.status == SchedulerItemStatus.PAUSED:
                paused.append(item)
            elif item.status == SchedulerItemStatus.CANCELLED:
                cancelled.append(item)
            elif item.status == SchedulerItemStatus.DUE or (
                item.status == SchedulerItemStatus.SCHEDULED
                and item.due_at
                and _try_parse_datetime(item.due_at) is not None
                and _parse_datetime(item.due_at) <= current
            ):
                due.append(replace(item, status=SchedulerItemStatus.DUE, last_previewed_at=current.isoformat()))
            else:
                upcoming.append(item)
        audit = [{"event": "scheduler_due_preview", "item_id": item.item_id, "executed": False} for item in due]
        return SchedulerPreviewResult(
            due_items=due,
            next_items=upcoming,
            paused_items=paused,
            cancelled_items=cancelled,
            blocked_reasons=blocked,
            audit_events=audit,
        )

    def preview_pause(self, item: SchedulerItem, *, reason: str = "") -> SchedulerItem:
        return self._preview_transition(item, SchedulerItemStatus.PAUSED, reason=reason)

    def preview_resume(self, item: SchedulerItem, *, reason: str = "") -> SchedulerItem:
        target = SchedulerItemStatus.SCHEDULED if item.due_at or item.schedule_expression else SchedulerItemStatus.DRAFT
        return self._preview_transition(item, target, reason=reason)

    def preview_cancel(self, item: SchedulerItem, *, reason: str = "") -> SchedulerItem:
        return self._preview_transition(item, SchedulerItemStatus.CANCELLED, reason=reason)

    def _preview_transition(
        self,
        item: SchedulerItem,
        status: SchedulerItemStatus,
        *,
        reason: str,
    ) -> SchedulerItem:
        safe_reason, _ = redact_sensitive_data(reason)
        blocked = list(item.blocked_reasons)
        if safe_reason:
            blocked.append(f"preview transition reason: {_clean_text(safe_reason)[:160]}")
        return replace(item, status=status, blocked_reasons=blocked, last_previewed_at=_now_iso())

    def preview_daily_review(self, **values: Any) -> DailyReviewPreview:
        source = _review_values(values, DailyReviewPreview)
        source["review_id"] = _clean_text(source.get("review_id")) or str(uuid4())
        source["date"] = _clean_text(source.get("date")) or datetime.now(timezone.utc).date().isoformat()
        return DailyReviewPreview(**source)

    def preview_weekly_review(self, **values: Any) -> WeeklyReviewPreview:
        source = _review_values(values, WeeklyReviewPreview)
        source["review_id"] = _clean_text(source.get("review_id")) or str(uuid4())
        source["week"] = _clean_text(source.get("week")) or datetime.now(timezone.utc).strftime("%G-W%V")
        return WeeklyReviewPreview(**source)

    def preview_stop_controls(self, **values: Any) -> StopControls:
        return StopControls(**values)


def _force_review_safe(review: Any) -> None:
    for name in review.__dataclass_fields__:
        value = getattr(review, name)
        if isinstance(value, list):
            safe, _ = redact_sensitive_data(value)
            object.__setattr__(review, name, [_clean_text(item) for item in safe if _clean_text(item)])
    object.__setattr__(review, "would_execute", False)
    object.__setattr__(review, "would_send", False)
    object.__setattr__(review, "would_call_tools", False)
    object.__setattr__(review, "prepare_only", True)


def _review_values(values: Dict[str, Any], cls: Any) -> Dict[str, Any]:
    allowed = set(cls.__dataclass_fields__)
    return {key: value for key, value in dict(values).items() if key in allowed}


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _try_parse_datetime(value: str) -> Optional[datetime]:
    try:
        return _parse_datetime(value)
    except (TypeError, ValueError):
        return None


def _optional_text(value: Any) -> Optional[str]:
    text = _clean_text(value)
    return text or None


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _deduplicate(values: List[Any]) -> List[str]:
    return list(dict.fromkeys(_clean_text(value) for value in values if _clean_text(value)))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
