from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4


class MissionStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PENDING_APPROVAL = "pending_approval"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MissionStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PENDING_APPROVAL = "pending_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MissionLogRecord:
    log_id: str
    mission_id: str
    level: str
    message: str
    created_at: str


@dataclass
class MissionStepRecord:
    step_id: str
    mission_id: str
    prompt: str
    agent: str
    status: MissionStepStatus
    policy_decision: str
    policy_reason: str
    approval_request_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class MissionRecord:
    mission_id: str
    objective: str
    status: MissionStatus
    agents: List[str]
    steps: List[MissionStepRecord]
    logs: List[MissionLogRecord]
    estimated_cost: float
    actual_cost: float
    risk: RiskLevel
    result: Optional[Dict[str, Any]]
    metrics: Dict[str, int]
    approvals: List[str]
    created_at: str
    updated_at: str


class InMemoryMissionStore:
    def __init__(self):
        self._items: Dict[str, MissionRecord] = {}
        self._lock = Lock()

    def create(self, objective: str, agents: Optional[List[str]] = None) -> MissionRecord:
        now = _now_iso()
        mission = MissionRecord(
            mission_id=str(uuid4()),
            objective=objective,
            status=MissionStatus.DRAFT,
            agents=agents or ["hermes"],
            steps=[],
            logs=[],
            estimated_cost=0.0,
            actual_cost=0.0,
            risk=RiskLevel.UNKNOWN,
            result=None,
            metrics={
                "steps_total": 0,
                "steps_completed": 0,
                "steps_failed": 0,
                "steps_pending_approval": 0,
            },
            approvals=[],
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._items[mission.mission_id] = mission
        return mission

    def get(self, mission_id: str) -> MissionRecord:
        with self._lock:
            item = self._items.get(mission_id)
        if not item:
            raise KeyError(mission_id)
        return item

    def list(self) -> List[MissionRecord]:
        with self._lock:
            return list(self._items.values())

    def update(self, mission: MissionRecord) -> MissionRecord:
        mission.updated_at = _now_iso()
        with self._lock:
            self._items[mission.mission_id] = mission
        return mission

    def add_step(self, mission: MissionRecord, prompt: str, agent: str = "hermes") -> MissionStepRecord:
        now = _now_iso()
        step = MissionStepRecord(
            step_id=str(uuid4()),
            mission_id=mission.mission_id,
            prompt=prompt,
            agent=agent,
            status=MissionStepStatus.PENDING,
            policy_decision="",
            policy_reason="",
            created_at=now,
            updated_at=now,
        )
        mission.steps.append(step)
        mission.agents = sorted(set(mission.agents + [agent]))
        self._append_log(mission, "info", f"step_created:{step.step_id}")
        self._recompute_metrics(mission)
        self.update(mission)
        return step

    def update_step(self, mission: MissionRecord, step: MissionStepRecord) -> MissionStepRecord:
        step.updated_at = _now_iso()
        self._recompute_metrics(mission)
        self.update(mission)
        return step

    def cancel_open_steps(self, mission: MissionRecord) -> None:
        for step in mission.steps:
            if step.status in {MissionStepStatus.PENDING, MissionStepStatus.RUNNING, MissionStepStatus.PENDING_APPROVAL}:
                step.status = MissionStepStatus.CANCELLED
                step.updated_at = _now_iso()
        self._append_log(mission, "info", "mission_cancelled")
        self._recompute_metrics(mission)
        self.update(mission)

    def has_pending_approvals(self, mission: MissionRecord) -> bool:
        return any(step.status == MissionStepStatus.PENDING_APPROVAL for step in mission.steps)

    def append_log_event(self, mission: MissionRecord, event: str, step_id: Optional[str] = None) -> MissionLogRecord:
        suffix = f":{step_id}" if step_id else ""
        log = self._append_log(mission, "info", f"{event}{suffix}")
        self.update(mission)
        return log

    def _recompute_metrics(self, mission: MissionRecord) -> None:
        mission.metrics = {
            "steps_total": len(mission.steps),
            "steps_completed": sum(1 for s in mission.steps if s.status == MissionStepStatus.COMPLETED),
            "steps_failed": sum(1 for s in mission.steps if s.status == MissionStepStatus.FAILED),
            "steps_pending_approval": sum(1 for s in mission.steps if s.status == MissionStepStatus.PENDING_APPROVAL),
        }

    def _append_log(self, mission: MissionRecord, level: str, message: str) -> MissionLogRecord:
        log = MissionLogRecord(
            log_id=str(uuid4()),
            mission_id=mission.mission_id,
            level=level,
            message=message,
            created_at=_now_iso(),
        )
        mission.logs.append(log)
        return log


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
