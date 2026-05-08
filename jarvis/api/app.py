from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from jarvis.mission_control import InMemoryMissionStore, MissionStatus, MissionStepStatus
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


class CreateTaskRequest(BaseModel):
    prompt: str


class CancelTaskResponse(BaseModel):
    task_id: str
    status: str


class CreateMissionRequest(BaseModel):
    objective: str


class CreateMissionStepRequest(BaseModel):
    prompt: str
    agent: str = "hermes"


class CancelMissionResponse(BaseModel):
    mission_id: str
    status: str


@dataclass
class TaskRecord:
    task_id: str
    prompt: str
    status: str
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approval_request_id: Optional[str] = None


class InMemoryTaskStore:
    def __init__(self):
        self._items: Dict[str, TaskRecord] = {}
        self._lock = Lock()

    def create(self, prompt: str) -> TaskRecord:
        now = _now_iso()
        task = TaskRecord(
            task_id=str(uuid4()),
            prompt=prompt,
            status="pending",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._items[task.task_id] = task
        return task

    def get(self, task_id: str) -> TaskRecord:
        with self._lock:
            item = self._items.get(task_id)
        if not item:
            raise KeyError(task_id)
        return item

    def list(self) -> List[TaskRecord]:
        with self._lock:
            return list(self._items.values())

    def update(self, task: TaskRecord) -> TaskRecord:
        task.updated_at = _now_iso()
        with self._lock:
            self._items[task.task_id] = task
        return task



def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_app(
    *,
    policy_engine: Optional[PolicyEngine] = None,
    approval_gateway: Optional[ApprovalGateway] = None,
    adapter_factory: Optional[Callable[[], HermesRuntimeAdapter]] = None,
    task_store: Optional[InMemoryTaskStore] = None,
) -> FastAPI:
    app = FastAPI(title="JARVIS Gateway API", version="0.1.0")

    app.state.policy_engine = policy_engine or PolicyEngine()
    app.state.approval_gateway = approval_gateway or ApprovalGateway()
    app.state.adapter_factory = adapter_factory or (lambda: HermesRuntimeAdapter())
    app.state.task_store = task_store or InMemoryTaskStore()
    app.state.mission_store = InMemoryMissionStore()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/tasks")
    def create_task(payload: CreateTaskRequest) -> dict:
        prompt = payload.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt must be non-empty")

        task = app.state.task_store.create(prompt=prompt)
        decision = app.state.policy_engine.classify_action(prompt)

        if decision.decision == PolicyDecision.DENIED:
            task.status = "failed"
            task.error = f"denied: {decision.reason}"
            app.state.task_store.update(task)
            return asdict(task)

        if decision.decision == PolicyDecision.REQUIRES_APPROVAL:
            approval = app.state.approval_gateway.create_request(
                action=prompt,
                rationale="Prompt requires human approval before execution.",
            )
            task.status = "pending_approval"
            task.error = "requires_approval"
            task.approval_request_id = approval.request_id
            app.state.task_store.update(task)
            return asdict(task)

        task.status = "running"
        app.state.task_store.update(task)

        try:
            adapter = app.state.adapter_factory()
            result = adapter.run(prompt, task_id=task.task_id)
            task.status = "completed"
            task.result = result
            task.error = None
        except Exception as exc:
            task.status = "failed"
            task.error = f"execution_error: {type(exc).__name__}: {exc}"

        app.state.task_store.update(task)
        return asdict(task)


    @app.post("/missions")
    def create_mission(payload: CreateMissionRequest) -> dict:
        objective = payload.objective.strip()
        if not objective:
            raise HTTPException(status_code=400, detail="objective must be non-empty")

        mission = app.state.mission_store.create(objective=objective)
        return asdict(mission)

    @app.get("/missions")
    def list_missions() -> list[dict]:
        return [asdict(m) for m in app.state.mission_store.list()]

    @app.get("/missions/{mission_id}")
    def get_mission(mission_id: str) -> dict:
        try:
            mission = app.state.mission_store.get(mission_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")
        return asdict(mission)

    @app.post("/missions/{mission_id}/steps")
    def create_mission_step(mission_id: str, payload: CreateMissionStepRequest) -> dict:
        try:
            mission = app.state.mission_store.get(mission_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

        if mission.status in {MissionStatus.CANCELLED, MissionStatus.COMPLETED, MissionStatus.FAILED}:
            raise HTTPException(status_code=400, detail=f"mission is {mission.status.value} and cannot accept new steps")

        prompt = payload.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt must be non-empty")

        agent = payload.agent.strip()
        if not agent:
            raise HTTPException(status_code=400, detail="agent must be non-empty")

        step = app.state.mission_store.add_step(mission, prompt=prompt, agent=agent)
        decision = app.state.policy_engine.classify_action(prompt)
        step.policy_decision = decision.decision.value
        step.policy_reason = decision.reason

        if decision.decision == PolicyDecision.DENIED:
            step.status = MissionStepStatus.FAILED
            step.error = f"denied: {decision.reason}"
            mission.status = MissionStatus.BLOCKED
            app.state.mission_store.append_log_event(mission, "step_denied", step.step_id)
            app.state.mission_store.update_step(mission, step)
            return asdict(mission)

        if decision.decision == PolicyDecision.REQUIRES_APPROVAL:
            approval = app.state.approval_gateway.create_request(
                action=prompt,
                rationale="Mission step requires human approval before execution.",
            )
            step.status = MissionStepStatus.PENDING_APPROVAL
            step.error = "requires_approval"
            step.approval_request_id = approval.request_id
            mission.approvals.append(approval.request_id)
            mission.status = MissionStatus.PENDING_APPROVAL
            app.state.mission_store.append_log_event(mission, "step_pending_approval", step.step_id)
            app.state.mission_store.update_step(mission, step)
            return asdict(mission)

        step.status = MissionStepStatus.RUNNING
        mission.status = MissionStatus.RUNNING
        app.state.mission_store.update_step(mission, step)

        try:
            adapter = app.state.adapter_factory()
            result = adapter.run(prompt, task_id=step.step_id)
            step.status = MissionStepStatus.COMPLETED
            step.result = result
            step.error = None
            mission.result = result
            app.state.mission_store.append_log_event(mission, "step_completed", step.step_id)
        except Exception as exc:
            step.status = MissionStepStatus.FAILED
            step.error = f"execution_error: {type(exc).__name__}: {exc}"
            mission.status = MissionStatus.FAILED
            app.state.mission_store.append_log_event(mission, "step_failed", step.step_id)

        if step.status == MissionStepStatus.COMPLETED:
            mission.status = (
                MissionStatus.PENDING_APPROVAL
                if app.state.mission_store.has_pending_approvals(mission)
                else MissionStatus.RUNNING
            )

        app.state.mission_store.update_step(mission, step)
        return asdict(mission)

    @app.post("/missions/{mission_id}/cancel", response_model=CancelMissionResponse)
    def cancel_mission(mission_id: str) -> CancelMissionResponse:
        try:
            mission = app.state.mission_store.get(mission_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

        if mission.status in {MissionStatus.COMPLETED, MissionStatus.FAILED, MissionStatus.CANCELLED}:
            return CancelMissionResponse(mission_id=mission.mission_id, status=mission.status.value)

        mission.status = MissionStatus.CANCELLED
        app.state.mission_store.cancel_open_steps(mission)
        app.state.mission_store.update(mission)
        return CancelMissionResponse(mission_id=mission.mission_id, status=mission.status.value)

    @app.get("/tasks/{task_id}")
    def get_task(task_id: str) -> dict:
        try:
            task = app.state.task_store.get(task_id)
            return asdict(task)
        except KeyError:
            raise HTTPException(status_code=404, detail="task not found")

    @app.get("/tasks")
    def list_tasks() -> list[dict]:
        return [asdict(task) for task in app.state.task_store.list()]

    @app.post("/tasks/{task_id}/cancel", response_model=CancelTaskResponse)
    def cancel_task(task_id: str) -> CancelTaskResponse:
        try:
            task = app.state.task_store.get(task_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="task not found")

        if task.status in {"completed", "failed", "cancelled"}:
            return CancelTaskResponse(task_id=task.task_id, status=task.status)

        task.status = "cancelled"
        app.state.task_store.update(task)
        return CancelTaskResponse(task_id=task.task_id, status=task.status)

    return app


app = create_app()
