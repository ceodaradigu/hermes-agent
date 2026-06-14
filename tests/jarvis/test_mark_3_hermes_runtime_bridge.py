from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi")

import run_agent
from fastapi import HTTPException

from jarvis.api.app import Mark3HermesRuntimeExecuteReadRequest, create_app
from jarvis.approval_hardening import ApprovalHardeningService
import jarvis.mark_3_hermes_runtime_bridge as bridge_module
from jarvis.mark_3_hermes_runtime_bridge import Mark3HermesRuntimeBridge
from jarvis.mark_3_mission_loop import Mark3MissionLoop
from jarvis.mark_3_mission_loop_models import ExecutionCandidate, MissionLoopStatus, MissionStep
from jarvis.runtime.hermes_adapter import HermesAdapterConfig, HermesRuntimeAdapter
from run_agent import AIAgent


class FakeAdapter:
    def __init__(self, guard, *, result=None, delay=0, fail=False, wait_for_interrupt=False):
        self.guard = guard
        self.result = result if result is not None else {"success": True}
        self.delay = delay
        self.fail = fail
        self.wait_for_interrupt = wait_for_interrupt
        self.calls = 0
        self.interrupts = 0
        self.interrupted = threading.Event()

    def run(self, message, **kwargs):
        self.calls += 1
        if self.delay:
            time.sleep(self.delay)
        if self.wait_for_interrupt:
            self.interrupted.wait(3)
        if self.fail:
            raise RuntimeError("fake failure")
        path = message.split("path: ", 1)[1]
        verdict = self.guard("read_file", {"path": path})
        if verdict is not True:
            return {"success": False, "error": verdict}
        return self.result

    def interrupt(self, reason):
        self.interrupts += 1
        self.interrupted.set()


class NonCooperativeAdapter(FakeAdapter):
    def __init__(self, guard):
        super().__init__(guard)
        self.release = threading.Event()

    def run(self, message, **kwargs):
        self.calls += 1
        self.release.wait(10)
        path = message.split("path: ", 1)[1]
        verdict = self.guard("read_file", {"path": path})
        return {"success": verdict is True}

    def interrupt(self, reason):
        self.interrupts += 1


class ScriptedAdapter(FakeAdapter):
    def __init__(self, guard, *, result, guard_call=None):
        super().__init__(guard, result=result)
        self.guard_call = guard_call

    def run(self, message, **kwargs):
        self.calls += 1
        if self.guard_call:
            name, args = self.guard_call
            self.guard(name, args)
        return self.result


class NoGuardSuccessAdapter(FakeAdapter):
    def run(self, message, **kwargs):
        self.calls += 1
        return {"success": True}


class EarlyStopAdapter(FakeAdapter):
    def __init__(self, guard):
        super().__init__(guard)
        self.run_entered = threading.Event()
        self.allow_agent = threading.Event()
        self.pending_reason = None
        self.delivery_callback = None
        self.last_agent = None

    def set_interrupt_delivery_callback(self, callback):
        self.delivery_callback = callback

    def interrupt(self, reason):
        if self.last_agent is None:
            self.pending_reason = reason
            return False
        self.interrupts += 1
        self.last_agent.interrupted = True
        if self.delivery_callback:
            self.delivery_callback()
        return True

    def run(self, message, **kwargs):
        self.calls += 1
        self.run_entered.set()
        self.allow_agent.wait(3)
        self.last_agent = SimpleNamespace(interrupted=False)
        if self.pending_reason:
            reason = self.pending_reason
            self.pending_reason = None
            self.interrupt(reason)
        if self.last_agent.interrupted:
            return {"success": False, "error": "interrupted before read"}
        path = message.split("path: ", 1)[1]
        verdict = self.guard("read_file", {"path": path})
        if verdict is not True:
            return {"success": False, "error": verdict}
        return {"success": True}


def _tool_def(name):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": f"{name} tool",
            "parameters": {"type": "object", "properties": {}},
        },
    }


def _tool_call(name, arguments, call_id):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _assistant_message(*tool_calls):
    return SimpleNamespace(tool_calls=list(tool_calls))


class FakeContextCompressor:
    context_length = 200000
    threshold_tokens = 100000
    compression_count = 0
    last_prompt_tokens = 0
    last_completion_tokens = 0

    def __init__(self, *args, tool_schema_names=None, **kwargs):
        self.tool_schema_names = list(tool_schema_names or [])

    def get_tool_schemas(self):
        return [
            {
                "name": name,
                "description": f"{name} context tool",
                "parameters": {"type": "object", "properties": {}},
            }
            for name in self.tool_schema_names
        ]

    def on_session_start(self, *args, **kwargs):
        return None

    def on_session_reset(self):
        return None

    def on_session_end(self, *args, **kwargs):
        return None

    def update_model(self, *args, **kwargs):
        return None


def _governed_agent(allowed_path, *, guard_calls=None, allowed_paths=None, **kwargs):
    allowed = {
        Path(item).resolve()
        for item in (allowed_paths if allowed_paths is not None else [allowed_path])
    }

    def guard(name, args):
        if guard_calls is not None:
            guard_calls.append((name, dict(args)))
        if name != "read_file":
            return "tool must be read_file"
        if Path(args.get("path", "")).resolve() not in allowed:
            return "path is outside approved Mark 3 scope"
        return True

    with (
        patch("run_agent.get_tool_definitions", return_value=[_tool_def("read_file")]),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("hermes_logging.setup_logging"),
        patch("run_agent.OpenAI"),
    ):
        agent = AIAgent(
            api_key="test-key-1234567890",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            tool_delay=0,
            allowed_tools=["read_file"],
            governed_mode=True,
            tool_guard=guard,
            **kwargs,
        )
        agent.valid_tool_names = {"read_file"}
        return agent


def route(app, path, method):
    return next(item for item in app.routes if item.path == path and method in item.methods)


def make_bridge(tmp_path, *, adapter=None, mutate=None, approval=True):
    path = tmp_path / "allowed.txt"
    path.write_text("ok", encoding="utf-8")
    approvals = ApprovalHardeningService()
    loop = Mark3MissionLoop(approval_service=approvals)
    mission = loop.create_mission({
        "objective": "read one local file",
        "context": "local only",
        "desired_outcome": "file evidence",
        "success_criteria": ["read attempted"],
        "declared_authorization": "operator requested",
        "allowed_scope": ["repo"],
        "allowed_paths_resources": [str(path.resolve())],
        "allowed_tools": ["read_file"],
        "prohibited_tools": ["terminal", "browser", "network", "money"],
        "monetary_budget": 0,
        "time_budget_seconds": 30,
        "max_steps": 1,
        "allowed_data": ["local test file"],
        "constraints": ["no writes"],
        "stop_conditions": ["operator stop"],
        "expected_rollback": "none",
        "instruction_origin": "test",
        "requested_risk_level": 1,
    })
    mission_id = mission["intake"]["mission_id"]
    record = approvals.request(
        action_type="filesystem_read",
        context={"action_type": "filesystem_read", "target": "read", "tool_name": "read_file"},
    )
    approvals.decide(record.approval_id, "approved")
    step = MissionStep(
        step_id="step-1",
        order=1,
        description="filesystem_read",
        objective="read",
        action_type="filesystem_read",
        inputs={},
        expected_outputs=["evidence"],
        required_capability="hermes.file.read",
        tool_candidate="read_file",
        scope=[str(path)],
        budget=0,
        timeout_seconds=2,
        risk_level=1,
        approval_required=True,
        strong_approval_required=False,
        double_confirmation_required=False,
        triple_confirmation_required=False,
        preconditions=[],
        dependencies=[],
        evidence_requirements=[],
        stop_condition="stop on request",
        rollback_compensation="none",
        capability_available=True,
        approval_satisfied=approval,
        approval_id=record.approval_id if approval else None,
    )
    candidate = ExecutionCandidate(
        candidate_id="candidate-step-1",
        mission_id=mission_id,
        step_id="step-1",
        exact_action="filesystem_read",
        adapter_capability="hermes.file.read",
        tool_candidate="read_file",
        scope=[str(path)],
        budget=0,
        timeout_seconds=2,
        risk_level=1,
        approval_requirement={
            "backend": "local",
            "cwd": str(path.parent.resolve()),
            "approval_id": record.approval_id if approval else None,
        },
        context_fingerprint=record.context_fingerprint,
        audit_correlation_id=mission["intake"]["correlation_id"],
        stop_plan="stop",
        rollback_plan="none",
        evidence_requirements=[],
        capability_available=True,
        eligibility=True,
        approval_required=True,
        approval_satisfied=approval,
        execution_capability_available=True,
    )
    if mutate:
        mutate(path, record, step, candidate)
    memory = loop._missions[mission_id]
    memory.plan = [step]
    memory.candidates = [candidate]
    memory.status = MissionLoopStatus.EXECUTION_CANDIDATE_READY
    made = []

    def factory(guard):
        item = adapter or FakeAdapter(guard)
        if isinstance(item, type):
            item = item(guard)
        elif getattr(item, "guard", None) is None:
            item.guard = guard
        made.append(item)
        return item

    return loop, Mark3HermesRuntimeBridge(loop, adapter_factory=factory), candidate, record, made


def execute(tmp_path, **kwargs):
    loop, bridge, candidate, record, made = make_bridge(tmp_path, **kwargs)
    return bridge.execute_read(mission_id=candidate.mission_id, candidate_id=candidate.candidate_id, approval=record), made, loop


def _conversation_result(messages, **overrides):
    result = {
        "final_response": "done",
        "messages": messages,
        "api_calls": 1,
        "completed": True,
        "partial": False,
        "interrupted": False,
    }
    result.update(overrides)
    return result


def _assistant_tool_message(tool_name, args, call_id="call-read"):
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{
            "id": call_id,
            "type": "function",
            "function": {"name": tool_name, "arguments": json.dumps(args)},
        }],
    }


def _tool_result_message(content, call_id="call-read"):
    return {"role": "tool", "tool_call_id": call_id, "content": content}


def test_candidate_valid_executes_read_file_once(tmp_path):
    result, made, loop = execute(tmp_path)
    assert result["status"] == "success"
    assert made[0].calls == 1
    assert loop.get_mission(result["session"]["mission_id"])["outcomes"][0]["step_status"] == "completed"


@pytest.mark.parametrize("mutate,reason", [
    (lambda p, r, s, c: c.scope.__setitem__(0, str(p.with_name("other.txt"))), "path must be an existing regular file"),
    (lambda p, r, s, c: (p.unlink(), p.mkdir()), "directories are not supported"),
    (lambda p, r, s, c: c.scope.__setitem__(0, str(p.with_name(".env"))), "blocked secret-like"),
    (lambda p, r, s, c: setattr(c, "tool_candidate", "search_files"), "tool must be read_file"),
    (lambda p, r, s, c: setattr(c, "tool_candidate", "delegate_task"), "tool must be read_file"),
    (lambda p, r, s, c: setattr(c, "tool_candidate", "memory"), "tool must be read_file"),
    (lambda p, r, s, c: setattr(c, "tool_candidate", "todo"), "tool must be read_file"),
    (lambda p, r, s, c: setattr(c, "approval_satisfied", False), "approval is not satisfied"),
    (lambda p, r, s, c: setattr(r, "context_fingerprint", "bad"), "fingerprint mismatch"),
    (lambda p, r, s, c: c.approval_requirement.__setitem__("backend", "ssh"), "backend must be local"),
    (lambda p, r, s, c: c.approval_requirement.__setitem__("cwd", str(p.parent / "elsewhere")), "escapes approved cwd"),
])
def test_invalid_gates_block_before_hermes(tmp_path, mutate, reason):
    result, made, _ = execute(tmp_path, mutate=mutate)
    assert result["status"] == "blocked"
    assert reason in " ".join(result["blocked_reasons"])
    assert made == []


def test_symlink_escape_blocked(tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    link = tmp_path / "allowed.txt"
    link.symlink_to(outside)
    result, made, _ = execute(tmp_path, mutate=lambda p, r, s, c: None)
    assert result["status"] == "blocked"
    assert "symlink paths are blocked" in " ".join(result["blocked_reasons"])
    assert made == []


def test_approval_absent_and_expired_blocked(tmp_path):
    loop, bridge, candidate, record, made = make_bridge(tmp_path, approval=False)
    assert bridge.execute_read(mission_id=candidate.mission_id, candidate_id=candidate.candidate_id, approval=None)["status"] == "blocked"
    loop, bridge, candidate, record, made = make_bridge(tmp_path)
    record.expires_at = "2000-01-01T00:00:00+00:00"
    result = bridge.execute_read(mission_id=candidate.mission_id, candidate_id=candidate.candidate_id, approval=record)
    assert "expired" in " ".join(result["blocked_reasons"])


def test_duplicate_approval_not_bound_to_candidate_is_blocked_before_adapter(tmp_path):
    loop, bridge, candidate, record, made = make_bridge(tmp_path)
    duplicate = loop.approval_service.request(
        action_type=record.action_type,
        context={"action_type": "filesystem_read", "target": "read", "tool_name": "read_file"},
    )
    loop.approval_service.decide(duplicate.approval_id, "approved")
    assert duplicate.approval_id != candidate.approval_requirement["approval_id"]
    assert duplicate.context_fingerprint == record.context_fingerprint

    result = bridge.execute_read(
        mission_id=candidate.mission_id,
        candidate_id=candidate.candidate_id,
        approval=duplicate,
    )

    assert result["status"] == "blocked"
    assert "approval is not bound to candidate" in result["blocked_reasons"]
    assert made == []


def test_exact_bound_approval_allows_execution(tmp_path):
    result, made, _ = execute(tmp_path)

    assert result["status"] == "success"
    assert made[0].calls == 1


def test_two_concurrent_calls_execute_hermes_once(tmp_path):
    adapter = FakeAdapter(None, delay=0.2)
    loop, bridge, candidate, record, made = make_bridge(tmp_path, adapter=adapter)
    results = []
    threads = [threading.Thread(target=lambda: results.append(bridge.execute_read(
        mission_id=candidate.mission_id, candidate_id=candidate.candidate_id, approval=record))) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert adapter.calls == 1
    assert {item["status"] for item in results} <= {"success", "already_running", "already_completed"}


def test_same_candidate_id_in_different_missions_does_not_share_session(tmp_path):
    adapter_one = FakeAdapter(None)
    first_dir = tmp_path / "one"
    second_dir = tmp_path / "two"
    first_dir.mkdir()
    second_dir.mkdir()
    loop_one, bridge_one, candidate_one, record_one, _ = make_bridge(first_dir, adapter=adapter_one)
    result_one = bridge_one.execute_read(
        mission_id=candidate_one.mission_id,
        candidate_id=candidate_one.candidate_id,
        approval=record_one,
    )
    adapter_two = FakeAdapter(None)
    loop_two, _, candidate_two, record_two, _ = make_bridge(second_dir, adapter=adapter_two)
    loop_one._missions[candidate_two.mission_id] = loop_two._missions[candidate_two.mission_id]
    bridge_one.adapter_factory = lambda guard: (setattr(adapter_two, "guard", guard), adapter_two)[1]
    result_two = bridge_one.execute_read(
        mission_id=candidate_two.mission_id,
        candidate_id=candidate_two.candidate_id,
        approval=record_two,
    )
    assert candidate_one.candidate_id == candidate_two.candidate_id
    assert result_one["session"]["session_id"] != result_two["session"]["session_id"]
    assert adapter_one.calls == adapter_two.calls == 1


def test_timeout_requests_interrupt_once_and_waits_for_worker(tmp_path):
    adapter = FakeAdapter(None, wait_for_interrupt=True)
    result, made, _ = execute(tmp_path, adapter=adapter, mutate=lambda p, r, s, c: setattr(c, "timeout_seconds", 1))
    assert result["status"] == "stopped"
    assert adapter.interrupts == 1
    assert result["session"]["ended_at"]


def test_non_cooperative_timeout_returns_pending_without_confirmed_stop(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_module, "INTERRUPT_GRACE_SECONDS", 0.05)
    adapter = NonCooperativeAdapter(None)
    loop, bridge, candidate, record, _ = make_bridge(
        tmp_path,
        adapter=adapter,
        mutate=lambda p, r, s, c: setattr(c, "timeout_seconds", 1),
    )
    result = bridge.execute_read(mission_id=candidate.mission_id, candidate_id=candidate.candidate_id, approval=record)
    assert result["status"] == "timeout_interrupt_pending"
    assert result["session"]["interrupt_requested"] is True
    assert result["session"]["worker_alive"] is True
    assert result["session"]["forced_cancellation_available"] is False
    assert result["session"]["ended_at"] is None
    assert result["session"]["status"] != "stopped"
    assert adapter.interrupts == 1
    assert adapter.calls == 1
    assert bridge.status()["running_sessions"] == 1
    adapter.release.set()
    for _ in range(50):
        if bridge.get_session(result["session"]["session_id"])["ended_at"]:
            break
        time.sleep(0.02)


def test_non_cooperative_timeout_late_result_records_without_reexecution(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_module, "INTERRUPT_GRACE_SECONDS", 0.05)
    adapter = NonCooperativeAdapter(None)
    loop, bridge, candidate, record, _ = make_bridge(
        tmp_path,
        adapter=adapter,
        mutate=lambda p, r, s, c: setattr(c, "timeout_seconds", 1),
    )
    result = bridge.execute_read(mission_id=candidate.mission_id, candidate_id=candidate.candidate_id, approval=record)
    assert result["status"] == "timeout_interrupt_pending"
    adapter.release.set()
    for _ in range(50):
        session = bridge.get_session(result["session"]["session_id"])
        if session["ended_at"]:
            break
        time.sleep(0.02)
    assert session["status"] == "stopped"
    assert adapter.calls == 1
    assert len(loop.get_mission(candidate.mission_id)["outcomes"]) == 1


def test_stop_cooperative(tmp_path):
    adapter = FakeAdapter(None, wait_for_interrupt=True)
    loop, bridge, candidate, record, made = make_bridge(tmp_path, adapter=adapter)
    holder = {}
    thread = threading.Thread(target=lambda: holder.setdefault("result", bridge.execute_read(
        mission_id=candidate.mission_id, candidate_id=candidate.candidate_id, approval=record)))
    thread.start()
    while not bridge.status()["running_sessions"]:
        time.sleep(0.01)
    session_id = next(iter(bridge._sessions))
    stopped = bridge.stop(session_id, reason="test stop")
    thread.join()
    assert stopped["interrupt_requested"] is True
    assert adapter.interrupts == 1


def test_stop_after_success_does_not_mutate_terminal_session(tmp_path):
    adapter = FakeAdapter(None, result={"success": True})
    loop, bridge, candidate, record, _ = make_bridge(tmp_path, adapter=adapter)
    result = bridge.execute_read(
        mission_id=candidate.mission_id,
        candidate_id=candidate.candidate_id,
        approval=record,
    )
    session_id = result["session"]["session_id"]
    before = bridge.get_session(session_id)

    stopped = bridge.stop(session_id, reason="late stop")
    after = bridge.get_session(session_id)

    assert before["status"] == "success"
    assert stopped == before
    assert after == before
    assert after["interrupt_requested"] is False
    assert after["interrupted"] is False
    assert adapter.interrupts == 0


def test_stop_after_failed_does_not_mutate_terminal_session(tmp_path):
    adapter = FakeAdapter(None, result={"success": False})
    loop, bridge, candidate, record, _ = make_bridge(tmp_path, adapter=adapter)
    result = bridge.execute_read(
        mission_id=candidate.mission_id,
        candidate_id=candidate.candidate_id,
        approval=record,
    )
    session_id = result["session"]["session_id"]
    before = bridge.get_session(session_id)

    stopped = bridge.stop(session_id, reason="late stop")
    after = bridge.get_session(session_id)

    assert before["status"] == "failed"
    assert stopped == before
    assert after == before
    assert after["interrupt_requested"] is False
    assert after["interrupted"] is False
    assert adapter.interrupts == 0


def test_early_stop_interrupt_stays_pending_until_agent_exists(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_module, "INTERRUPT_GRACE_SECONDS", 0.05)
    adapter = EarlyStopAdapter(None)
    loop, bridge, candidate, record, _ = make_bridge(tmp_path, adapter=adapter)
    holder = {}
    runner = threading.Thread(target=lambda: holder.setdefault("result", bridge.execute_read(
        mission_id=candidate.mission_id,
        candidate_id=candidate.candidate_id,
        approval=record,
    )))
    runner.start()
    assert adapter.run_entered.wait(2)
    session_id = next(iter(bridge._sessions))

    stopped = bridge.stop(session_id, reason="early stop")
    session = bridge._sessions[session_id]

    assert stopped["status"] == "cancellation_pending"
    assert session.interrupt_requested is True
    assert session.interrupt_delivered is False
    assert adapter.interrupts == 0

    adapter.allow_agent.set()
    runner.join(2)
    session = bridge._sessions[session_id]

    assert adapter.interrupts == 1
    assert session.interrupt_delivered is True
    assert bridge.get_session(session_id)["status"] == "stopped"
    assert holder["result"]["session"]["status"] != "success"


def test_non_cooperative_stop_returns_pending_without_hanging(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge_module, "INTERRUPT_GRACE_SECONDS", 0.05)
    adapter = NonCooperativeAdapter(None)
    loop, bridge, candidate, record, _ = make_bridge(
        tmp_path,
        adapter=adapter,
        mutate=lambda p, r, s, c: setattr(c, "timeout_seconds", 10),
    )
    holder = {}
    runner = threading.Thread(target=lambda: holder.setdefault("result", bridge.execute_read(
        mission_id=candidate.mission_id,
        candidate_id=candidate.candidate_id,
        approval=record,
    )))
    runner.start()
    while not bridge.status()["running_sessions"]:
        time.sleep(0.01)
    session_id = next(iter(bridge._sessions))
    started = time.time()
    stopped = bridge.stop(session_id, reason="test stop")
    assert time.time() - started < 1
    assert stopped["status"] == "cancellation_pending"
    assert stopped["interrupt_requested"] is True
    assert stopped["worker_alive"] is True
    assert stopped["forced_cancellation_available"] is False
    assert stopped["ended_at"] is None
    assert adapter.interrupts == 1
    assert bridge.status()["running_sessions"] == 1
    assert bridge.stop(session_id, reason="second stop")["status"] == "cancellation_pending"
    assert adapter.interrupts == 1
    adapter.release.set()
    runner.join(2)


class NullAdapter(FakeAdapter):
    def run(self, message, **kwargs):
        self.calls += 1
        return None


@pytest.mark.parametrize("adapter,expected", [
    (FakeAdapter(None, result={"success": True}), "success"),
    (FakeAdapter(None, result={"success": False}), "failed"),
    (FakeAdapter(None, fail=True), "failed"),
    (NullAdapter(None), "unknown"),
])
def test_outcome_success_failure_unknown_mapping(tmp_path, adapter, expected):
    result, _, _ = execute(tmp_path, adapter=adapter)
    assert result["status"] == expected


def test_register_outcome_failure_does_not_reexecute(tmp_path, monkeypatch):
    adapter = FakeAdapter(None)
    loop, bridge, candidate, record, made = make_bridge(tmp_path, adapter=adapter)
    monkeypatch.setattr(loop, "record_outcome", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("store down")))
    first = bridge.execute_read(mission_id=candidate.mission_id, candidate_id=candidate.candidate_id, approval=record)
    second = bridge.execute_read(mission_id=candidate.mission_id, candidate_id=candidate.candidate_id, approval=record)
    assert adapter.calls == 1
    assert second["status"] == "already_completed"
    assert "record_outcome_error" in first["session"]["outcome"]


def test_api_without_callback_returns_503():
    app = create_app()
    endpoint = route(app, "/mark-3/hermes-runtime/execute-read", "POST").endpoint
    with pytest.raises(HTTPException) as exc:
        endpoint(Mark3HermesRuntimeExecuteReadRequest(mission_id="m", candidate_id="c", approval_id="a"))
    assert exc.value.status_code == 503


def test_api_with_callback_allows_operation(tmp_path):
    app = create_app(hermes_runtime_authorize=lambda operation, payload: True)
    loop, bridge, candidate, record, made = make_bridge(tmp_path)
    app.state.mark_3_mission_loop = loop
    app.state.mark_3_hermes_runtime_bridge = bridge
    app.state.approval_hardening._records[record.approval_id] = record
    response = route(app, "/mark-3/hermes-runtime/execute-read", "POST").endpoint(
        Mark3HermesRuntimeExecuteReadRequest(
            mission_id=candidate.mission_id,
            candidate_id=candidate.candidate_id,
            approval_id=record.approval_id,
        )
    )
    assert response["status"] == "success"


def test_no_real_provider_write_network_terminal_or_money(tmp_path):
    result, made, _ = execute(tmp_path)
    assert made[0].calls == 1
    assert result["session"]["tool_calls"][0]["tool_name"] == "read_file"
    assert "terminal" not in str(result)
    assert "money" not in str(result)


def test_default_governed_adapter_config_disables_ambient_context_and_dynamic_tools():
    bridge = Mark3HermesRuntimeBridge(Mark3MissionLoop())
    adapter = bridge._default_adapter_factory(lambda name, args: True)
    config = adapter.config

    assert config.governed_mode is True
    assert config.skip_memory is True
    assert config.skip_context_files is True
    assert config.allowed_tools == ["read_file"]
    assert config.disable_memory_provider_tools is True
    assert config.disable_context_engine is True
    assert config.disable_plugins is True
    assert config.disable_delegate_task is True
    assert config.disable_mcp is True


def test_runtime_adapter_passes_governed_flags_to_ai_agent(monkeypatch):
    captured = {}

    class RecordingAgent:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(run_agent, "AIAgent", RecordingAgent)
    adapter = HermesRuntimeAdapter(HermesAdapterConfig(
        allowed_tools=["read_file"],
        skip_memory=True,
        skip_context_files=True,
        governed_mode=True,
        disable_memory_provider_tools=True,
        disable_context_engine=True,
        disable_plugins=True,
        disable_delegate_task=True,
        disable_mcp=True,
    ))

    adapter.create_agent(session_id="session-1")

    assert captured["session_id"] == "session-1"
    assert captured["skip_memory"] is True
    assert captured["skip_context_files"] is True
    assert captured["allowed_tools"] == ["read_file"]
    assert captured["governed_mode"] is True
    assert captured["disable_memory_provider_tools"] is True
    assert captured["disable_context_engine"] is True
    assert captured["disable_plugins"] is True
    assert captured["disable_delegate_task"] is True
    assert captured["disable_mcp"] is True


def test_allowed_tool_names_final_filter_removes_later_injected_context_tools(monkeypatch):
    blocked_initial = [
        "memory",
        "session_search",
        "delegate_task",
        "terminal",
        "write_file",
        "patch",
        "search_files",
        "browser_navigate",
        "mcp_call",
    ]
    blocked_injected = ["lcm_grep", "lcm_expand", "memory_context"]

    monkeypatch.setattr(
        run_agent,
        "ContextCompressor",
        lambda *args, **kwargs: FakeContextCompressor(tool_schema_names=blocked_injected),
    )
    monkeypatch.setattr(AIAgent, "_check_compression_model_feasibility", lambda self: None)
    with (
        patch("run_agent.get_tool_definitions", return_value=[_tool_def("read_file"), *[_tool_def(name) for name in blocked_initial]]),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("hermes_logging.setup_logging"),
        patch("run_agent.OpenAI"),
    ):
        agent = AIAgent(
            api_key="test-key-1234567890",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            allowed_tool_names=["read_file"],
        )

    assert [tool["function"]["name"] for tool in agent.tools] == ["read_file"]
    assert agent.valid_tool_names == {"read_file"}
    surface = json.dumps({"tools": agent.tools, "valid": sorted(agent.valid_tool_names)}, sort_keys=True, default=str)
    for blocked in [*blocked_initial, *blocked_injected]:
        assert blocked not in surface


def test_governed_mode_fails_if_extra_tool_is_added_after_final_filter(tmp_path):
    allowed = tmp_path / "allowed.txt"
    allowed.write_text("ok", encoding="utf-8")
    agent = _governed_agent(allowed)
    agent.tools.append(_tool_def("memory"))
    agent.valid_tool_names.add("memory")

    with pytest.raises(RuntimeError, match="governed session tool surface violation"):
        agent.run_conversation("read the approved file")


def test_non_governed_mode_keeps_normal_tool_surface(monkeypatch):
    monkeypatch.setattr(run_agent, "ContextCompressor", lambda *args, **kwargs: FakeContextCompressor())
    monkeypatch.setattr(AIAgent, "_check_compression_model_feasibility", lambda self: None)
    with (
        patch("run_agent.get_tool_definitions", return_value=[
            _tool_def("read_file"),
            _tool_def("memory"),
            _tool_def("delegate_task"),
        ]),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("hermes_logging.setup_logging"),
        patch("run_agent.OpenAI"),
    ):
        agent = AIAgent(
            api_key="test-key-1234567890",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
            governed_mode=False,
        )

    assert {"read_file", "memory", "delegate_task"} <= agent.valid_tool_names


def test_real_adapter_with_safe_create_agent_calls_exact_guard(tmp_path, monkeypatch):
    path = tmp_path / "allowed.txt"
    path.write_text("ok", encoding="utf-8")
    observed = []

    def guard(name, args):
        observed.append((name, args["path"]))
        return Path(args["path"]).resolve() == path.resolve()

    adapter = HermesRuntimeAdapter(HermesAdapterConfig(
        enabled_toolsets=["file"],
        allowed_tools=["read_file"],
        tool_guard=guard,
    ))

    class SafeAgent:
        def run_conversation(self, **kwargs):
            assert adapter.config.allowed_tools == ["read_file"]
            verdict = adapter.config.tool_guard("read_file", {"path": str(path)})
            return {"success": verdict is True}

    monkeypatch.setattr(adapter, "create_agent", lambda session_id=None: SafeAgent())
    assert adapter.run("read")["success"] is True
    assert observed == [("read_file", str(path))]


def test_nested_raw_result_is_sanitized_from_session_outcome_evidence_and_audit(tmp_path):
    secret = "SECRET_FILE_CONTENT"
    raw = {
        "success": True,
        "messages": [
            {"role": "tool", "content": secret, "tool_calls": [{"function": {"name": "read_file"}}]},
            {"role": "assistant", "content": "done"},
        ],
        "metadata": {
            "status": "ok",
            "duration": 0.1,
            "tool_name": "read_file",
            "path_fingerprint": "sha256:test",
            "counts": {"messages": 2},
        },
    }
    result, _, loop = execute(tmp_path, adapter=FakeAdapter(None, result=raw))
    session = result["session"]
    mission = loop.get_mission(session["mission_id"])
    audit = loop.audit(session["mission_id"])
    serialized = json.dumps({
        "session": session,
        "outcome": session["outcome"],
        "mission_outcomes": mission["outcomes"],
        "audit": audit,
    }, sort_keys=True, default=str)

    assert secret not in serialized
    assert session["outcome"]["raw_result"]["messages"]["redacted"] is True
    assert session["outcome"]["raw_result"]["metadata"]["status"] == "ok"
    assert session["outcome"]["raw_result"]["metadata"]["tool_name"] == "read_file"
    assert session["outcome"]["raw_result"]["metadata"]["counts"]["messages"] == 2


def test_run_conversation_text_without_tools_fails_and_records_failed_step(tmp_path):
    raw = _conversation_result([{"role": "assistant", "content": "I can explain it without tools."}])
    result, _, loop = execute(tmp_path, adapter=FakeAdapter(None, result=raw))
    mission = loop.get_mission(result["session"]["mission_id"])

    assert result["status"] == "failed"
    assert result["session"]["error"] == "approved read_file was not successfully observed"
    assert mission["outcomes"][0]["step_status"] == "failed"
    assert mission["outcomes"][0]["verification_state"] == "rejected"


def test_run_conversation_empty_messages_fails(tmp_path):
    raw = _conversation_result([])
    result, _, loop = execute(tmp_path, adapter=FakeAdapter(None, result=raw))

    assert result["status"] == "failed"
    assert loop.get_mission(result["session"]["mission_id"])["outcomes"][0]["step_status"] == "failed"


def test_run_conversation_other_tool_fails(tmp_path):
    path = tmp_path / "allowed.txt"
    raw = _conversation_result([
        _assistant_tool_message("todo", {"todos": []}, "call-todo"),
        _tool_result_message(json.dumps({"success": True}), "call-todo"),
    ])
    adapter = ScriptedAdapter(None, result=raw, guard_call=("todo", {"todos": [], "path": str(path)}))
    result, _, loop = execute(tmp_path, adapter=adapter)

    assert result["status"] == "failed"
    assert result["session"]["tool_calls"][0]["tool_name"] == "todo"
    assert result["session"]["tool_calls"][0]["guard_allowed"] is False
    assert loop.get_mission(result["session"]["mission_id"])["outcomes"][0]["step_status"] == "failed"


def test_run_conversation_read_file_wrong_path_fails(tmp_path):
    allowed = tmp_path / "allowed.txt"
    denied = tmp_path / "denied.txt"
    denied.write_text("no", encoding="utf-8")
    raw = _conversation_result([
        _assistant_tool_message("read_file", {"path": str(denied)}),
        _tool_result_message(json.dumps({"success": True})),
    ])
    adapter = ScriptedAdapter(None, result=raw, guard_call=("read_file", {"path": str(denied)}))
    result, _, loop = execute(tmp_path, adapter=adapter)

    assert allowed.exists()
    assert result["status"] == "failed"
    assert result["session"]["tool_calls"][0]["guard_allowed"] is False
    assert loop.get_mission(result["session"]["mission_id"])["outcomes"][0]["verification_state"] == "rejected"


def test_run_conversation_read_file_tool_error_fails(tmp_path):
    allowed = tmp_path / "allowed.txt"
    raw = _conversation_result([
        _assistant_tool_message("read_file", {"path": str(allowed)}),
        _tool_result_message(json.dumps({"error": "read failed"})),
    ])
    result, _, loop = execute(tmp_path, adapter=FakeAdapter(None, result=raw))

    assert result["status"] == "failed"
    assert result["session"]["error"] == "read failed"
    assert loop.get_mission(result["session"]["mission_id"])["outcomes"][0]["step_status"] == "failed"


def test_guard_blocked_read_file_fails_without_verified_evidence(tmp_path):
    denied = tmp_path / "denied.txt"
    denied.write_text("no", encoding="utf-8")
    raw = _conversation_result([
        _assistant_tool_message("read_file", {"path": str(denied)}),
        _tool_result_message(json.dumps({
            "success": False,
            "blocked_by": "hermes_runtime_tool_guard",
            "error": "blocked",
        })),
    ])
    adapter = ScriptedAdapter(None, result=raw, guard_call=("read_file", {"path": str(denied)}))
    result, _, loop = execute(tmp_path, adapter=adapter)

    assert result["status"] == "failed"
    assert result["session"]["tool_calls"][0]["guard_allowed"] is False
    outcome = loop.get_mission(result["session"]["mission_id"])["outcomes"][0]
    assert outcome["step_status"] == "failed"
    assert outcome["verification_state"] == "rejected"


def test_run_conversation_exact_read_file_with_valid_tool_output_completes(tmp_path):
    allowed = tmp_path / "allowed.txt"
    raw = _conversation_result([
        _assistant_tool_message("read_file", {"path": str(allowed)}),
        _tool_result_message(json.dumps({"success": True, "metadata": {"bytes": 2}})),
    ])
    result, _, loop = execute(tmp_path, adapter=FakeAdapter(None, result=raw))

    assert result["status"] == "success"
    outcome = loop.get_mission(result["session"]["mission_id"])["outcomes"][0]
    assert outcome["step_status"] == "completed"
    assert outcome["verification_state"] == "verified"


def test_fake_success_without_observed_read_fails(tmp_path):
    result, _, loop = execute(tmp_path, adapter=NoGuardSuccessAdapter(None))

    assert result["status"] == "failed"
    assert result["session"]["error"] == "approved read_file was not successfully observed"
    assert loop.get_mission(result["session"]["mission_id"])["outcomes"][0]["step_status"] == "failed"


def test_fake_success_with_explicit_observed_read_completes(tmp_path):
    result, _, loop = execute(tmp_path, adapter=FakeAdapter(None, result={"success": True}))

    assert result["status"] == "success"
    assert result["session"]["tool_calls"][0]["guard_allowed"] is True
    assert loop.get_mission(result["session"]["mission_id"])["outcomes"][0]["step_status"] == "completed"


def test_observed_exact_call_false_forces_failed_step_status(tmp_path):
    raw = _conversation_result([
        _assistant_tool_message("read_file", {"path": str(tmp_path / "denied.txt")}),
        _tool_result_message(json.dumps({"success": True})),
    ])
    result, _, loop = execute(
        tmp_path,
        adapter=ScriptedAdapter(None, result=raw, guard_call=("read_file", {"path": str(tmp_path / "denied.txt")})),
    )

    assert result["status"] == "failed"
    assert loop.get_mission(result["session"]["mission_id"])["outcomes"][0]["step_status"] == "failed"


def test_api_response_does_not_expose_secret_file_content(tmp_path):
    secret = "SECRET_FILE_CONTENT"
    raw = _conversation_result([
        _assistant_tool_message("read_file", {"path": str(tmp_path / "allowed.txt")}),
        _tool_result_message(json.dumps({"success": True, "content": secret})),
    ])
    app = create_app(hermes_runtime_authorize=lambda operation, payload: True)
    loop, bridge, candidate, record, _ = make_bridge(tmp_path, adapter=FakeAdapter(None, result=raw))
    app.state.mark_3_mission_loop = loop
    app.state.mark_3_hermes_runtime_bridge = bridge
    app.state.approval_hardening._records[record.approval_id] = record
    response = route(app, "/mark-3/hermes-runtime/execute-read", "POST").endpoint(
        Mark3HermesRuntimeExecuteReadRequest(
            mission_id=candidate.mission_id,
            candidate_id=candidate.candidate_id,
            approval_id=record.approval_id,
        )
    )
    session = bridge.get_session(response["session"]["session_id"])
    mission = loop.get_mission(candidate.mission_id)
    audit = loop.audit(candidate.mission_id)

    assert secret not in json.dumps(response, sort_keys=True, default=str)
    assert secret not in json.dumps(session, sort_keys=True, default=str)
    assert secret not in json.dumps(mission["outcomes"], sort_keys=True, default=str)
    assert secret not in json.dumps(audit, sort_keys=True, default=str)


def test_final_response_is_redacted_from_governed_read_api_and_session(tmp_path):
    secret = "SECRET_FILE_CONTENT"
    raw = _conversation_result(
        [
            _assistant_tool_message("read_file", {"path": str(tmp_path / "allowed.txt")}),
            _tool_result_message(json.dumps({"success": True, "metadata": {"bytes": 19}})),
        ],
        final_response=secret,
    )
    app = create_app(hermes_runtime_authorize=lambda operation, payload: True)
    loop, bridge, candidate, record, _ = make_bridge(tmp_path, adapter=FakeAdapter(None, result=raw))
    app.state.mark_3_mission_loop = loop
    app.state.mark_3_hermes_runtime_bridge = bridge
    app.state.approval_hardening._records[record.approval_id] = record

    execute_response = route(app, "/mark-3/hermes-runtime/execute-read", "POST").endpoint(
        Mark3HermesRuntimeExecuteReadRequest(
            mission_id=candidate.mission_id,
            candidate_id=candidate.candidate_id,
            approval_id=record.approval_id,
        )
    )
    session_response = route(app, "/mark-3/hermes-runtime/sessions/{session_id}", "GET").endpoint(
        execute_response["session"]["session_id"]
    )
    session = bridge.get_session(execute_response["session"]["session_id"])
    mission = loop.get_mission(candidate.mission_id)
    audit = loop.audit(candidate.mission_id)

    assert secret not in json.dumps(execute_response, sort_keys=True, default=str)
    assert secret not in json.dumps(session_response, sort_keys=True, default=str)
    assert secret not in json.dumps(session, sort_keys=True, default=str)
    assert secret not in json.dumps(session["outcome"], sort_keys=True, default=str)
    assert secret not in json.dumps(mission["outcomes"], sort_keys=True, default=str)
    assert secret not in json.dumps(audit, sort_keys=True, default=str)
    assert session["outcome"]["raw_result"]["final_response"]["redacted"] is True


def test_governed_single_read_file_sequential_path_guard_blocks_before_dispatch(tmp_path):
    allowed = tmp_path / "allowed.txt"
    denied = tmp_path / "denied.txt"
    allowed.write_text("ok", encoding="utf-8")
    denied.write_text("no", encoding="utf-8")
    starts = []
    completes = []
    progress = []
    agent = _governed_agent(
        allowed,
        tool_start_callback=lambda *args: starts.append(args),
        tool_complete_callback=lambda *args: completes.append(args),
        tool_progress_callback=lambda *args, **kwargs: progress.append((args, kwargs)),
    )

    def fake_dispatch(name, args, task_id, **kwargs):
        return json.dumps({"success": True, "path": args["path"]})

    with patch("run_agent.handle_function_call", side_effect=fake_dispatch) as dispatch:
        allowed_messages = []
        agent._execute_tool_calls(
            _assistant_message(_tool_call("read_file", {"path": str(allowed)}, "allowed-call")),
            allowed_messages,
            "task-1",
        )
        denied_messages = []
        agent._execute_tool_calls(
            _assistant_message(_tool_call("read_file", {"path": str(denied)}, "denied-call")),
            denied_messages,
            "task-1",
        )

    assert dispatch.call_count == 1
    assert dispatch.call_args.args[:3] == ("read_file", {"path": str(allowed)}, "task-1")
    assert json.loads(allowed_messages[0]["content"])["success"] is True
    denied_result = json.loads(denied_messages[0]["content"])
    assert denied_result["success"] is False
    assert denied_result["blocked_by"] == "hermes_runtime_tool_guard"
    assert "outside approved Mark 3 scope" in denied_result["error"]
    assert starts == [("allowed-call", "read_file", {"path": str(allowed)})]
    assert completes == [("allowed-call", "read_file", {"path": str(allowed)}, allowed_messages[0]["content"])]
    assert [entry[0][0] for entry in progress] == ["tool.started", "tool.completed"]


def test_governed_concurrent_read_file_path_guard_still_blocks_before_dispatch(tmp_path):
    allowed = tmp_path / "allowed.txt"
    denied = tmp_path / "denied.txt"
    allowed.write_text("ok", encoding="utf-8")
    denied.write_text("no", encoding="utf-8")
    starts = []
    completes = []
    agent = _governed_agent(
        allowed,
        tool_start_callback=lambda *args: starts.append(args),
        tool_complete_callback=lambda *args: completes.append(args),
    )
    message = _assistant_message(
        _tool_call("read_file", {"path": str(allowed)}, "allowed-call"),
        _tool_call("read_file", {"path": str(denied)}, "denied-call"),
    )
    messages = []

    with patch("run_agent.handle_function_call", return_value=json.dumps({"success": True})) as dispatch:
        agent._execute_tool_calls(message, messages, "task-1")

    assert dispatch.call_count == 1
    assert dispatch.call_args.args[:3] == ("read_file", {"path": str(allowed)}, "task-1")
    assert len(messages) == 2
    assert messages[0]["tool_call_id"] == "denied-call"
    denied_result = json.loads(messages[0]["content"])
    assert denied_result["success"] is False
    assert denied_result["blocked_by"] == "hermes_runtime_tool_guard"
    assert messages[1]["tool_call_id"] == "allowed-call"
    assert starts == [("allowed-call", "read_file", {"path": str(allowed)})]
    assert completes == [("allowed-call", "read_file", {"path": str(allowed)}, messages[1]["content"])]


def test_governed_sequential_allowed_read_file_invokes_guard_once(tmp_path):
    allowed = tmp_path / "allowed.txt"
    allowed.write_text("ok", encoding="utf-8")
    guard_calls = []
    agent = _governed_agent(allowed, guard_calls=guard_calls)
    messages = []

    with patch("run_agent.handle_function_call", return_value=json.dumps({"success": True})) as dispatch:
        agent._execute_tool_calls(
            _assistant_message(_tool_call("read_file", {"path": str(allowed)}, "allowed-call")),
            messages,
            "task-1",
        )

    assert len(guard_calls) == 1
    assert dispatch.call_count == 1
    assert json.loads(messages[0]["content"])["success"] is True


def test_governed_concurrent_allowed_read_file_invokes_guard_once_per_call(tmp_path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("one", encoding="utf-8")
    second.write_text("two", encoding="utf-8")
    guard_calls = []
    agent = _governed_agent(first, guard_calls=guard_calls, allowed_paths=[first, second])
    messages = []

    with patch("run_agent.handle_function_call", return_value=json.dumps({"success": True})) as dispatch:
        agent._execute_tool_calls(
            _assistant_message(
                _tool_call("read_file", {"path": str(first)}, "first-call"),
                _tool_call("read_file", {"path": str(second)}, "second-call"),
            ),
            messages,
            "task-1",
        )

    assert len(guard_calls) == 2
    assert [call[1]["path"] for call in guard_calls] == [str(first), str(second)]
    assert dispatch.call_count == 2
    assert [message["tool_call_id"] for message in messages] == ["first-call", "second-call"]


def test_governed_denied_read_file_does_not_reach_dispatcher(tmp_path):
    allowed = tmp_path / "allowed.txt"
    denied = tmp_path / "denied.txt"
    allowed.write_text("ok", encoding="utf-8")
    denied.write_text("no", encoding="utf-8")
    guard_calls = []
    agent = _governed_agent(allowed, guard_calls=guard_calls)
    messages = []

    with patch("run_agent.handle_function_call") as dispatch:
        agent._execute_tool_calls(
            _assistant_message(_tool_call("read_file", {"path": str(denied)}, "denied-call")),
            messages,
            "task-1",
        )

    assert len(guard_calls) == 1
    dispatch.assert_not_called()
    assert json.loads(messages[0]["content"])["blocked_by"] == "hermes_runtime_tool_guard"


def test_direct_invoke_tool_still_applies_guard(tmp_path):
    allowed = tmp_path / "allowed.txt"
    denied = tmp_path / "denied.txt"
    allowed.write_text("ok", encoding="utf-8")
    denied.write_text("no", encoding="utf-8")
    guard_calls = []
    agent = _governed_agent(allowed, guard_calls=guard_calls)

    with patch("run_agent.handle_function_call") as dispatch:
        result = agent._invoke_tool("read_file", {"path": str(denied)}, "task-1", "denied-call")

    assert len(guard_calls) == 1
    dispatch.assert_not_called()
    assert json.loads(result)["blocked_by"] == "hermes_runtime_tool_guard"
