from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from jarvis.mission_control import MissionControl
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter


class CreateTaskRequest(BaseModel):
    prompt: str


class CreateMissionStepRequest(BaseModel):
    prompt: str


class CancelTaskResponse(BaseModel):
    task_id: str
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
        task = TaskRecord(task_id=str(uuid4()), prompt=prompt, status="pending", created_at=now, updated_at=now)
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
    app.state.mission_control = MissionControl(
        mission_store=None,
        policy_engine=app.state.policy_engine,
        approval_gateway=app.state.approval_gateway,
        adapter_factory=app.state.adapter_factory,
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/missions")
    def create_mission() -> dict:
        mission = app.state.mission_control.create_mission()
        return asdict(mission)

    @app.get("/missions")
    def list_missions() -> list[dict]:
        return [asdict(m) for m in app.state.mission_control.list_missions()]

    @app.get("/missions/{mission_id}")
    def get_mission(mission_id: str) -> dict:
        try:
            mission = app.state.mission_control.get_mission(mission_id)
            steps = app.state.mission_control.store.list_steps(mission_id)
            return {**asdict(mission), "steps": [asdict(s) for s in steps]}
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/missions/{mission_id}/steps")
    def add_mission_step(mission_id: str, payload: CreateMissionStepRequest) -> dict:
        prompt = payload.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt must be non-empty")
        try:
            step = app.state.mission_control.add_step(mission_id, prompt)
            mission = app.state.mission_control.get_mission(mission_id)
            return {"mission": asdict(mission), "step": asdict(step)}
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/missions/{mission_id}/cancel")
    def cancel_mission(mission_id: str) -> dict:
        try:
            mission = app.state.mission_control.cancel_mission(mission_id)
            return asdict(mission)
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

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
