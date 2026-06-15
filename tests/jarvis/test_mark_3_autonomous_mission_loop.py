from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import Mark3MissionCreateRequest, create_app
from jarvis.approval_hardening import ApprovalHardeningService, ApprovalKind
from jarvis.mark_3_master_planning import get_mark_3_macro_roadmap
from jarvis.mark_3_mission_loop import Mark3MissionLoop


def intake(**overrides):
    values = {
        "objective": "Prepare a bounded local report",
        "context": "No external side effects",
        "desired_outcome": "report preview",
        "success_criteria": ["report prepared"],
        "declared_authorization": "David directly requested this mission",
        "allowed_scope": ["repo"],
        "allowed_paths_resources": ["repo"],
        "allowed_tools": [],
        "prohibited_tools": ["network"],
        "monetary_budget": 0,
        "time_budget_seconds": 60,
        "max_steps": 3,
        "allowed_data": ["public"],
        "constraints": ["no external execution"],
        "stop_conditions": ["policy violation"],
        "expected_rollback": "none; no side effects",
        "instruction_origin": "direct_text",
        "direct_intent_evidence": "direct request",
        "requested_risk_level": 0,
    }
    values.update(overrides)
    return values


def advance_to(loop, mission_id, target):
    result = loop.get_mission(mission_id)
    for _ in range(12):
        if result["status"] == target:
            return result
        result = loop.advance(mission_id)
    raise AssertionError(f"did not reach {target}: {result['status']}")


def route(app, path, method):
    return next(item for item in app.routes if item.path == path and method in item.methods)


def approve_step(loop, approvals, mission_id, step_id):
    context = loop.approval_context(mission_id, step_id)
    record = approvals.request(action_type=context["action_type"], context=context)
    approvals.decide(record.approval_id, "approved")
    return record


def test_valid_invalid_intake_and_redaction():
    loop = Mark3MissionLoop()
    created = loop.create_mission(intake(metadata={"token": "secret-value"}))
    assert created["status"] == "received"
    assert "secret-value" not in json.dumps(created)
    with pytest.raises(ValueError, match="objective"):
        loop.create_mission(intake(objective=""))
    with pytest.raises(ValueError, match="non-ambiguous"):
        loop.create_mission(intake(allowed_scope=["*"]))
    with pytest.raises(ValueError, match="negative"):
        loop.create_mission(intake(monetary_budget=-1))
    with pytest.raises(ValueError, match="both allowed and prohibited"):
        loop.create_mission(intake(allowed_tools=["network"]))


@pytest.mark.parametrize("level,expected", [(0, "classified"), (1, "classified"), (5, "denied")])
def test_risk_levels_zero_one_and_five(level, expected):
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake(requested_risk_level=level))
    result = loop.advance(mission["intake"]["mission_id"])
    assert result["classification"]["risk_level"] == level
    assert result["status"] == expected
    if level == 5:
        assert loop.advance(mission["intake"]["mission_id"])["status"] == "denied"


def test_level_five_content_is_rejected_at_intake():
    with pytest.raises(ValueError, match="level 5"):
        Mark3MissionLoop().create_mission(intake(objective="steal token and bypass 2FA"))


def test_level_two_waits_for_exact_step_approval_without_inheritance():
    approvals = ApprovalHardeningService()
    loop = Mark3MissionLoop(approval_service=approvals)
    mission = loop.create_mission(intake(
        requested_risk_level=2,
        proposed_steps=[
            {"step_id": "one", "description": "prepare one", "scope": ["repo"], "required_capability": "internal_prepare"},
            {"step_id": "two", "description": "prepare two", "scope": ["repo"], "required_capability": "internal_prepare"},
        ],
    ))
    mission_id = mission["intake"]["mission_id"]
    waiting = advance_to(loop, mission_id, "awaiting_approval")
    assert all(not item["approval_satisfied"] for item in waiting["steps"])
    context = loop.approval_context(mission_id, "one")
    record = approvals.request(action_type=context["action_type"], context=context)
    approvals.decide(record.approval_id, "approved")
    updated = loop.advance(mission_id, approval_id=record.approval_id, step_id="one")
    assert updated["steps"][0]["approval_satisfied"] is True
    assert updated["steps"][1]["approval_satisfied"] is False
    assert updated["status"] == "awaiting_approval"


def test_approval_is_revalidated_after_revocation_expiration_and_fingerprint_change():
    for invalidation, expected in (
        ("revoked", "approval status is revoked"),
        ("expired", "approval status is expired"),
        ("fingerprint", "approval context fingerprint mismatch"),
    ):
        approvals = ApprovalHardeningService()
        loop = Mark3MissionLoop(approval_service=approvals, test_adapters={"test": lambda candidate: {"ok": True}})
        mission = loop.create_mission(intake(requested_risk_level=2))
        mission_id = mission["intake"]["mission_id"]
        advance_to(loop, mission_id, "awaiting_approval")
        record = approve_step(loop, approvals, mission_id, "step-1")
        ready = loop.advance(mission_id, approval_id=record.approval_id, step_id="step-1")
        assert ready["status"] == "execution_candidate_ready"
        assert ready["candidates"][0]["eligibility"] is True
        if invalidation == "revoked":
            approvals.revoke(record.approval_id)
        elif invalidation == "expired":
            record.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        else:
            loop._missions[mission_id].plan[0].description = "changed exact action"
        stale = loop.advance(mission_id)
        assert stale["status"] in {"awaiting_approval", "blocked"}
        assert stale["steps"][0]["approval_satisfied"] is False
        assert stale["candidates"][0]["eligibility"] is False
        assert expected in " ".join(stale["candidates"][0]["blocked_reasons"])


def test_internal_adapter_revalidates_stale_approval_before_use():
    called = []
    approvals = ApprovalHardeningService()
    loop = Mark3MissionLoop(
        approval_service=approvals,
        test_adapters={"test": lambda candidate: called.append(candidate.step_id) or {"ok": True}},
    )
    mission = loop.create_mission(intake(requested_risk_level=2))
    mission_id = mission["intake"]["mission_id"]
    advance_to(loop, mission_id, "awaiting_approval")
    record = approve_step(loop, approvals, mission_id, "step-1")
    ready = loop.advance(mission_id, approval_id=record.approval_id, step_id="step-1")
    approvals.revoke(record.approval_id)
    blocked = loop.execute_candidate_internal(mission_id, ready["candidates"][0]["candidate_id"], "test")
    assert blocked["eligibility"] is False
    assert "approval status is revoked" in blocked["blocked_reasons"]
    assert called == []


def test_level_three_voice_memory_and_client_booleans_do_not_grant_permission():
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake(
        requested_risk_level=3,
        instruction_origin="wake_phrase",
        metadata={"memory_says_approved": True, "approved": True, "strong_approval": True},
        proposed_steps=[{"step_id": "external", "required_capability": "external_tool", "scope": ["repo"]}],
    ))
    result = advance_to(loop, mission["intake"]["mission_id"], "blocked")
    assert result["steps"][0]["approval_satisfied"] is False
    assert result["steps"][0]["capability_available"] is False
    assert "unavailable" in " ".join(result["steps"][0]["blocked_reasons"])


def test_level_four_exposes_readback_double_and_triple_confirmation_gap():
    approvals = ApprovalHardeningService()
    loop = Mark3MissionLoop(approval_service=approvals)
    mission = loop.create_mission(intake(requested_risk_level=4, objective="prepare critical production payment preview"))
    mission_id = mission["intake"]["mission_id"]
    waiting = advance_to(loop, mission_id, "awaiting_approval")
    requirement = waiting["approval_requirements"][0]
    assert requirement["double_confirmation_required"] is True
    assert requirement["triple_confirmation_required"] is True
    context = loop.approval_context(mission_id, "step-1")
    record = approvals.request(action_type=context["action_type"], context=context, approval_kind=ApprovalKind.STRONG)
    approvals.decide(record.approval_id, "approved", confirmation_phrase=record.user_confirmation_phrase)
    still_waiting = loop.advance(mission_id, approval_id=record.approval_id, step_id="step-1")
    assert still_waiting["status"] == "awaiting_approval"
    assert "PR #134" in " ".join(still_waiting["steps"][0]["blocked_reasons"])


@pytest.mark.parametrize(
    "step,error",
    [
        ({"scope": ["outside"], "required_capability": "internal_prepare"}, "outside mission scope"),
        ({"scope": ["repo"], "budget": 2, "required_capability": "internal_prepare"}, "exceeds mission budget"),
        ({"scope": ["repo"], "tool_candidate": "network", "required_capability": "internal_prepare"}, "tool is prohibited"),
    ],
)
def test_planner_blocks_scope_budget_and_prohibited_tool(step, error):
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake(monetary_budget=1, proposed_steps=[step]))
    planned = advance_to(loop, mission["intake"]["mission_id"], "planned")
    assert error in " ".join(planned["steps"][0]["blocked_reasons"])


def test_planner_rejects_cycles_and_max_steps():
    loop = Mark3MissionLoop()
    cycle = loop.create_mission(intake(proposed_steps=[
        {"step_id": "a", "dependencies": ["b"], "scope": ["repo"]},
        {"step_id": "b", "dependencies": ["a"], "scope": ["repo"]},
    ]))
    loop.advance(cycle["intake"]["mission_id"])
    loop.advance(cycle["intake"]["mission_id"])
    with pytest.raises(ValueError, match="circular"):
        loop.advance(cycle["intake"]["mission_id"])
    other = Mark3MissionLoop()
    too_many = other.create_mission(intake(max_steps=1, proposed_steps=[{}, {}]))
    other.advance(too_many["intake"]["mission_id"])
    other.advance(too_many["intake"]["mission_id"])
    with pytest.raises(ValueError, match="max_steps"):
        other.advance(too_many["intake"]["mission_id"])


def test_planner_rejects_aggregate_budget_and_timeout_excess():
    for field, expected in (
        ("budget", "aggregate budget"),
        ("timeout_seconds", "aggregate timeout"),
    ):
        loop = Mark3MissionLoop()
        proposed = [
            {"scope": ["repo"], "required_capability": "internal_prepare", field: 6},
            {"scope": ["repo"], "required_capability": "internal_prepare", field: 6},
        ]
        mission = loop.create_mission(intake(monetary_budget=10, time_budget_seconds=10, proposed_steps=proposed))
        loop.advance(mission["intake"]["mission_id"])
        loop.advance(mission["intake"]["mission_id"])
        with pytest.raises(ValueError, match=expected):
            loop.advance(mission["intake"]["mission_id"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("budget", -1),
        ("timeout_seconds", -1),
        ("budget", float("nan")),
        ("timeout_seconds", float("inf")),
        ("budget", True),
        ("timeout_seconds", False),
        ("budget", "1"),
        ("timeout_seconds", "1"),
    ],
)
def test_planner_rejects_invalid_step_budget_and_timeout_values(field, value):
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake(proposed_steps=[{
        "scope": ["repo"],
        "required_capability": "internal_prepare",
        field: value,
    }]))
    loop.advance(mission["intake"]["mission_id"])
    loop.advance(mission["intake"]["mission_id"])
    with pytest.raises(ValueError, match="non-negative finite number"):
        loop.advance(mission["intake"]["mission_id"])


def test_planner_accepts_valid_zero_and_normal_numeric_totals_without_negative_compensation():
    loop = Mark3MissionLoop()
    valid = loop.create_mission(intake(
        monetary_budget=3,
        time_budget_seconds=5,
        proposed_steps=[
            {"scope": ["repo"], "required_capability": "internal_prepare", "budget": 0, "timeout_seconds": 2},
            {"scope": ["repo"], "required_capability": "internal_prepare", "budget": 3, "timeout_seconds": 3},
        ],
    ))
    assert advance_to(loop, valid["intake"]["mission_id"], "planned")["status"] == "planned"
    invalid = Mark3MissionLoop()
    compensated = invalid.create_mission(intake(
        monetary_budget=5,
        proposed_steps=[
            {"scope": ["repo"], "required_capability": "internal_prepare", "budget": -10},
            {"scope": ["repo"], "required_capability": "internal_prepare", "budget": 10},
        ],
    ))
    invalid.advance(compensated["intake"]["mission_id"])
    invalid.advance(compensated["intake"]["mission_id"])
    with pytest.raises(ValueError, match="non-negative finite number"):
        invalid.advance(compensated["intake"]["mission_id"])


def test_planner_prevents_risk_downgrade_and_default_denies_unlisted_tools_per_step():
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake(
        requested_risk_level=3,
        proposed_steps=[
            {"step_id": "internal", "risk_level": 0, "scope": ["repo"], "required_capability": "internal_prepare"},
            {"step_id": "tool", "scope": ["repo"], "required_capability": "external_tool", "tool_candidate": "unlisted"},
        ],
    ))
    planned = advance_to(loop, mission["intake"]["mission_id"], "planned")
    assert planned["steps"][0]["risk_level"] == 3
    assert "risk downgrade prevented" in " ".join(planned["steps"][0]["blocked_reasons"])
    assert planned["steps"][0]["capability_available"] is True
    assert planned["steps"][1]["capability_available"] is False
    assert "not in allowed tools" in " ".join(planned["steps"][1]["blocked_reasons"])


def test_candidate_never_claims_execution_and_test_adapter_is_internal_simulation():
    loop = Mark3MissionLoop(test_adapters={"test": lambda candidate: {"ok": True}})
    mission = loop.create_mission(intake())
    ready = advance_to(loop, mission["intake"]["mission_id"], "execution_candidate_ready")
    candidate = ready["candidates"][0]
    assert candidate["would_execute"] is candidate["did_execute"] is candidate["external_side_effects"] is False
    result = loop.execute_candidate_internal(mission["intake"]["mission_id"], candidate["candidate_id"], "test")
    assert result["simulated"] is True
    assert result["did_execute"] is False
    assert result["external_side_effects"] is False


def test_dependencies_block_until_all_prerequisites_complete_and_reject_failed_dependency():
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake(proposed_steps=[
        {"step_id": "a", "scope": ["repo"], "required_capability": "internal_prepare"},
        {"step_id": "b", "dependencies": ["a"], "scope": ["repo"], "required_capability": "internal_prepare"},
    ]))
    mission_id = mission["intake"]["mission_id"]
    ready = advance_to(loop, mission_id, "execution_candidate_ready")
    candidates = {item["step_id"]: item for item in ready["candidates"]}
    assert candidates["a"]["eligibility"] is True
    assert candidates["b"]["eligibility"] is False
    assert "dependency a" in " ".join(candidates["b"]["blocked_reasons"])
    with pytest.raises(ValueError, match="completed outcome blocked by dependencies"):
        loop.record_outcome(mission_id, {"step_id": "b", "summary": "cannot finish early"})
    loop.record_outcome(mission_id, {"step_id": "a", "summary": "a done"})
    next_ready = loop.advance(mission_id)
    candidates = {item["step_id"]: item for item in next_ready["candidates"]}
    assert next_ready["status"] == "execution_candidate_ready"
    assert candidates["b"]["eligibility"] is True

    failed_loop = Mark3MissionLoop()
    failed = failed_loop.create_mission(intake(proposed_steps=[
        {"step_id": "a", "scope": ["repo"], "required_capability": "internal_prepare"},
        {"step_id": "b", "dependencies": ["a"], "scope": ["repo"], "required_capability": "internal_prepare"},
    ]))
    failed_id = failed["intake"]["mission_id"]
    advance_to(failed_loop, failed_id, "execution_candidate_ready")
    failed_loop.record_outcome(failed_id, {
        "step_id": "a", "summary": "a failed", "step_status": "failed", "status_reason": "validation failed",
    })
    failed_result = failed_loop.advance(failed_id)
    assert failed_result["status"] == "failed"
    assert next(item for item in failed_result["post_mortem"]["steps"] if item["step_id"] == "b")["outcome"] == "unknown"
    assert "pending step outcome: b" in failed_result["post_mortem"]["unknowns"]


def test_multiple_dependencies_must_all_complete_and_unknown_dependency_is_rejected():
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake(proposed_steps=[
        {"step_id": "a", "scope": ["repo"], "required_capability": "internal_prepare"},
        {"step_id": "b", "scope": ["repo"], "required_capability": "internal_prepare"},
        {"step_id": "c", "dependencies": ["a", "b"], "scope": ["repo"], "required_capability": "internal_prepare"},
    ]))
    mission_id = mission["intake"]["mission_id"]
    advance_to(loop, mission_id, "execution_candidate_ready")
    loop.record_outcome(mission_id, {"step_id": "a", "summary": "a done"})
    partially_ready = loop.advance(mission_id)
    candidate_c = next(item for item in partially_ready["candidates"] if item["step_id"] == "c")
    assert candidate_c["eligibility"] is False
    assert "dependency b" in " ".join(candidate_c["blocked_reasons"])

    unknown = Mark3MissionLoop()
    bad = unknown.create_mission(intake(proposed_steps=[
        {"step_id": "a", "dependencies": ["missing"], "scope": ["repo"]},
    ]))
    unknown.advance(bad["intake"]["mission_id"])
    unknown.advance(bad["intake"]["mission_id"])
    with pytest.raises(ValueError, match="unknown dependencies"):
        unknown.advance(bad["intake"]["mission_id"])


def test_unregistered_adapter_and_fingerprint_mismatch_block():
    loop = Mark3MissionLoop(test_adapters={"test": lambda candidate: {}})
    mission = loop.create_mission(intake())
    ready = advance_to(loop, mission["intake"]["mission_id"], "execution_candidate_ready")
    candidate = loop._missions[mission["intake"]["mission_id"]].candidates[0]
    blocked = loop.execute_candidate_internal(mission["intake"]["mission_id"], ready["candidates"][0]["candidate_id"], "missing")
    assert "not a registered" in " ".join(blocked["blocked_reasons"])
    candidate.eligibility = True
    candidate.blocked_reasons = []
    candidate.context_fingerprint = "mismatch"
    blocked = loop.execute_candidate_internal(mission["intake"]["mission_id"], candidate.candidate_id, "test")
    assert "fingerprint mismatch" in blocked["blocked_reasons"]


def test_stop_and_kill_switch_prevent_advances_and_preserve_audit():
    loop = Mark3MissionLoop()
    first = loop.create_mission(intake())
    stopped = loop.stop(first["intake"]["mission_id"], reason="operator stop")
    count = len(stopped["audit"])
    assert loop.advance(first["intake"]["mission_id"])["status"] == "stopped"
    assert len(loop.audit(first["intake"]["mission_id"])["events"]) == count
    second = loop.create_mission(intake(objective="other"))
    loop.set_kill_switch(True)
    assert loop.get_mission(second["intake"]["mission_id"])["status"] == "stopped"


def test_outcome_evidence_post_mortem_learning_and_unknown_integrity():
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake())
    mission_id = mission["intake"]["mission_id"]
    advance_to(loop, mission_id, "result_pending")
    reported = loop.record_outcome(mission_id, {"summary": "done", "verification_state": "verified"})
    assert reported["outcomes"][0]["verification_state"] == "reported"
    verified = loop.record_outcome(mission_id, {
        "summary": "verified claim",
        "verification_state": "verified",
        "evidence": [{"source_type": "internal_observation", "description": "checked", "verification_state": "verified", "supported_claim": "verified claim"}],
    })
    assert verified["outcomes"][1]["verification_state"] == "verified"
    loop.advance(mission_id)
    post = loop.advance(mission_id)
    assert post["status"] == "post_mortem_ready"
    assert post["post_mortem"]["budget_used"] == "unknown"
    learning = loop.advance(mission_id)
    assert learning["learning_proposal_preview"]["persisted"] is False
    assert learning["learning_proposal_preview"]["activated"] is False
    assert learning["learning_proposal_preview"]["grants_permission"] is False
    assert all(item["costs_known"] == "unknown" and item["revenue_known"] == "unknown" for item in learning["outcomes"])


def test_multi_step_mission_requires_each_step_outcome_and_never_fake_completes():
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake(proposed_steps=[
        {"step_id": "one", "scope": ["repo"], "required_capability": "internal_prepare"},
        {"step_id": "two", "scope": ["repo"], "required_capability": "internal_prepare"},
    ]))
    mission_id = mission["intake"]["mission_id"]
    advance_to(loop, mission_id, "execution_candidate_ready")
    loop.record_outcome(mission_id, {"step_id": "one", "summary": "one done"})
    pending = loop.advance(mission_id)
    assert pending["status"] == "execution_candidate_ready"
    assert next(step for step in pending["steps"] if step["step_id"] == "two")["status"] not in {"completed", "failed", "stopped"}
    loop.record_outcome(mission_id, {"step_id": "two", "summary": "two done"})
    completed = loop.advance(mission_id)
    assert completed["status"] == "completed"
    post = loop.advance(mission_id)
    assert post["status"] == "post_mortem_ready"
    assert {item["step_id"] for item in post["post_mortem"]["steps"]} == {"one", "two"}


@pytest.mark.parametrize("step_status,expected", [("failed", "failed"), ("stopped", "stopped"), ("skipped", "blocked")])
def test_failed_stopped_or_skipped_step_prevents_false_mission_completion(step_status, expected):
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake())
    mission_id = mission["intake"]["mission_id"]
    advance_to(loop, mission_id, "execution_candidate_ready")
    loop.record_outcome(mission_id, {
        "step_id": "step-1",
        "summary": step_status,
        "step_status": step_status,
        "status_reason": f"explicit {step_status}",
    })
    result = loop.advance(mission_id)
    assert result["status"] == expected
    assert result["status"] != "completed"


def test_audit_is_append_only_and_redacts_secrets():
    loop = Mark3MissionLoop()
    mission = loop.create_mission(intake())
    mission_id = mission["intake"]["mission_id"]
    loop.add_feedback(mission_id, {"feedback": "ok", "password": "do-not-store"})
    assert loop.audit(mission_id)["append_only"] is True
    assert "do-not-store" not in json.dumps(loop.get_mission(mission_id))


def test_api_surface_and_no_dangerous_mission_loop_routes():
    app = create_app()
    created = route(app, "/mark-3/mission-loop/missions", "POST").endpoint(Mark3MissionCreateRequest(**intake()))
    assert created["status"] == "received"
    assert route(app, "/mark-3/mission-loop/status", "GET").endpoint()["external_execution_enabled"] is False
    assert route(app, "/mark-3/mission-loop/policy", "GET").endpoint()["candidate_is_not_execution"] is True
    paths = {item.path for item in app.routes if item.path.startswith("/mark-3/mission-loop")}
    for forbidden in ("/execute", "/run", "/approve-all", "/deploy", "/pay", "/send", "/read-env"):
        assert not any(forbidden in path for path in paths)


def test_roadmap_matches_133_through_141_operating_sequence():
    titles = {item["pr_number"]: item["title"] for item in get_mark_3_macro_roadmap()["items"]}
    assert "Mark 3 Master Planning" in titles[132]
    assert "Autonomous Mission Loop" in titles[133]
    assert "Governed Execution Engine" in titles[134]
    assert "Continuous Learning + Outcome Memory" in titles[135]
    assert "Governed Research Execution Control Plane" in titles[136]
    assert "Local Docs/Repo Research Adapter" in titles[137]
    assert "Product/Revenue Factory" in titles[138]
    assert "Local Routine Scheduler + Personal/Family Ops" in titles[139]
    assert "Moonshot Lab + Research/Experiment Engine" in titles[140]
    assert "Release Candidate + Pilot" in titles[141]
