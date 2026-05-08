from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


@dataclass
class MissionStepRecord:
    step_id: str
    mission_id: str
    prompt: str
    status: str
    created_at: str
    updated_at: str
    policy_decision: Optional[str] = None
    policy_reason: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approval_request_id: Optional[str] = None


@dataclass
class MissionRecord:
    mission_id: str
    status: str
    created_at: str
    updated_at: str


class InMemoryMissionStore:
    def __init__(self) -> None:
        self._missions: Dict[str, MissionRecord] = {}
        self._steps: Dict[str, List[MissionStepRecord]] = {}
        self._lock = Lock()

    def create_mission(self) -> MissionRecord:
        now = _now_iso()
        mission = MissionRecord(mission_id=str(uuid4()), status="running", created_at=now, updated_at=now)
        with self._lock:
            self._missions[mission.mission_id] = mission
            self._steps[mission.mission_id] = []
        return mission

    def list_missions(self) -> List[MissionRecord]:
        with self._lock:
            return list(self._missions.values())

    def get_mission(self, mission_id: str) -> MissionRecord:
        with self._lock:
            mission = self._missions.get(mission_id)
        if not mission:
            raise KeyError(mission_id)
        return mission

    def add_step(self, mission_id: str, prompt: str) -> MissionStepRecord:
        now = _now_iso()
        step = MissionStepRecord(
            step_id=str(uuid4()),
            mission_id=mission_id,
            prompt=prompt,
            status="pending",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            if mission_id not in self._missions:
                raise KeyError(mission_id)
            self._steps[mission_id].append(step)
        return step

    def list_steps(self, mission_id: str) -> List[MissionStepRecord]:
        with self._lock:
            if mission_id not in self._missions:
                raise KeyError(mission_id)
            return list(self._steps[mission_id])

    def update_step(self, step: MissionStepRecord) -> None:
        step.updated_at = _now_iso()

    def update_mission_status(self, mission: MissionRecord, status: str) -> None:
        mission.status = status
        mission.updated_at = _now_iso()


class MissionControl:
    def __init__(
        self,
        *,
        mission_store: Optional[InMemoryMissionStore] = None,
        policy_engine: Optional[PolicyEngine] = None,
        approval_gateway: Optional[ApprovalGateway] = None,
        adapter_factory=None,
    ):
        self.store = mission_store or InMemoryMissionStore()
        self.policy_engine = policy_engine or PolicyEngine()
        self.approval_gateway = approval_gateway or ApprovalGateway()
        self.adapter_factory = adapter_factory or (lambda: HermesRuntimeAdapter())

    def create_mission(self) -> MissionRecord:
        return self.store.create_mission()

    def list_missions(self) -> List[MissionRecord]:
        return self.store.list_missions()

    def get_mission(self, mission_id: str) -> MissionRecord:
        return self.store.get_mission(mission_id)

    def cancel_mission(self, mission_id: str) -> MissionRecord:
        mission = self.store.get_mission(mission_id)
        if mission.status not in {"completed", "cancelled"}:
            self.store.update_mission_status(mission, "cancelled")
        return mission

    def add_step(self, mission_id: str, prompt: str) -> MissionStepRecord:
        mission = self.store.get_mission(mission_id)
        step = self.store.add_step(mission_id, prompt)

        decision = self.policy_engine.classify_action(prompt)
        step.policy_decision = decision.decision.value
        step.policy_reason = decision.reason

        if decision.decision == PolicyDecision.DENIED:
            step.status = "denied"
            step.error = f"denied: {decision.reason}"
            self.store.update_step(step)
            self.store.update_mission_status(mission, "blocked")
            return step

        if decision.decision == PolicyDecision.REQUIRES_APPROVAL:
            req = self.approval_gateway.create_request(
                action=prompt,
                rationale="Mission step requires human approval before execution.",
            )
            step.status = "pending_approval"
            step.error = "requires_approval"
            step.approval_request_id = req.request_id
            self.store.update_step(step)
            self.store.update_mission_status(mission, "pending_approval")
            return step

        step.status = "running"
        self.store.update_step(step)

        adapter = self.adapter_factory()
        result = adapter.run(prompt, task_id=f"{mission_id}:{step.step_id}")
        step.result = result
        step.status = "completed"
        step.error = None
        self.store.update_step(step)

        self._refresh_mission_status(mission_id)
        return step

    def _refresh_mission_status(self, mission_id: str) -> None:
        mission = self.store.get_mission(mission_id)
        steps = self.store.list_steps(mission_id)
        if any(s.status == "pending_approval" for s in steps):
            self.store.update_mission_status(mission, "pending_approval")
            return
        if mission.status in {"blocked", "cancelled"}:
            return
        if steps and all(s.status == "completed" for s in steps):
            self.store.update_mission_status(mission, "completed")
        else:
            self.store.update_mission_status(mission, "running")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
