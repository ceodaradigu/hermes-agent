from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (
    Mark3LearningProposalDecisionRequest,
    Mark3LearningProposalRequest,
    Mark3OutcomeRecordRequest,
    Mark3ResearchRadarPlanRequest,
    create_app,
)
from jarvis.mark_3_growth_radar import ResearchRadar
from jarvis.mark_3_learning_proposals import LearningProposalEngine
from jarvis.mark_3_outcome_memory import OutcomeMemoryStore
from jarvis.mark_3_research_policy import ApprovalAwareResearchPolicy


def route(app, path, method):
    return next(item for item in app.routes if item.path == path and method in item.methods)


def test_outcome_memory_records_success_with_evidence():
    store = OutcomeMemoryStore()
    outcome = store.record({
        "mission_id": "m1",
        "step_id": "s1",
        "candidate_id": "c1",
        "goal": "local report",
        "tool_used": "read_file",
        "capability_used": "hermes.file.read",
        "result_status": "success",
        "evidence_state": "verified",
        "duration_seconds": 1.2,
        "cost": "unknown",
        "approval_level": "simple",
        "what_worked": "small vertical slice",
        "next_recommended_action": "keep vertical slices small",
    })

    assert outcome["result_status"] == "success"
    assert outcome["evidence_state"] == "verified"
    assert outcome["cost"] == "unknown"
    assert store.status()["outcome_count"] == 1


def test_outcome_memory_records_failure_without_inventing_evidence():
    store = OutcomeMemoryStore()
    outcome = store.record({"mission_id": "m2", "result_status": "failed"})

    assert outcome["evidence_state"] == "unknown"
    assert outcome["errors"] == ["unknown"]
    assert outcome["what_worked"] == "unknown"
    assert store.list_failures()[0]["category"] == "unknown"


def test_failure_memory_deduplicates_repeated_failures():
    store = OutcomeMemoryStore()
    first = store.record_failure({"category": "adapter_not_connected", "error": "web adapter unavailable"})
    second = store.record_failure({"category": "adapter_not_connected", "error": "web adapter unavailable"})

    assert first["failure_id"] == second["failure_id"]
    assert second["occurrences"] == 2
    assert len(store.list_failures()) == 1


def test_learning_proposal_is_created_from_outcome():
    store = OutcomeMemoryStore()
    outcome = store.record({
        "mission_id": "m3",
        "result_status": "success",
        "evidence_state": "verified",
        "next_recommended_action": "start real capabilities with small vertical slices",
    })
    proposal = LearningProposalEngine().create_from_outcome(outcome)

    assert proposal["status"] == "proposed"
    assert "small vertical slices" in proposal["proposal"]
    assert proposal["confidence"] == "high"
    assert proposal["requires_approval"] is True


def test_learning_proposal_approved_changes_state():
    engine = LearningProposalEngine()
    proposal = engine.create({"proposal": "Remember useful bounded experiments.", "evidence": "verified"})
    approved = engine.approve(proposal["proposal_id"], approval_level="simple")

    assert approved["status"] == "approved"
    assert approved["grants_permission"] is False
    assert approved["usable_as_operational_rule"] is True


def test_learning_proposal_rejected_changes_state():
    engine = LearningProposalEngine()
    proposal = engine.create({"proposal": "Remember weak pattern.", "evidence": "thin"})
    rejected = engine.reject(proposal["proposal_id"], reason="insufficient evidence")

    assert rejected["status"] == "rejected"
    assert rejected["reason"] == "insufficient evidence"


def test_learning_proposal_does_not_store_secrets():
    engine = LearningProposalEngine()
    proposal = engine.create({
        "proposal": "remember password=secret-value",
        "evidence": "token=abc123",
        "api_key": "secret-value",
    })
    serialized = json.dumps(proposal).lower()

    assert "secret-value" not in serialized
    assert "abc123" not in serialized
    assert proposal["sensitive_learning"] is True
    assert proposal["usable_as_operational_rule"] is False


def test_research_radar_creates_plan_for_github():
    plan = ResearchRadar().plan({"source": "github", "goal": "find_tools", "query": "agent frameworks"})

    assert plan["source"] == "github"
    assert plan["sources_to_query"][0]["capability"] == "github_search"
    assert plan["github_called"] is False


def test_research_radar_creates_plan_for_web():
    plan = ResearchRadar().plan({"source": "web", "goal": "detect_opportunities", "query": "agent safety patterns"})

    assert plan["source"] == "web"
    assert plan["sources_to_query"][0]["network_required"] is True
    assert plan["web_called"] is False


def test_research_radar_marks_approval_required_for_external_network():
    plan = ResearchRadar().plan({"source": "github", "goal": "improve_jarvis"})

    assert plan["requires_approval"] is True
    assert plan["approval_level"] == "simple"


def test_research_radar_missing_adapter_is_not_permanent_denial():
    plan = ResearchRadar().plan({"source": "web", "goal": "improve_hermes"})

    assert plan["execution_status"] == "setup_required"
    assert plan["capability_status"] == "capability_not_connected_yet"
    assert "capability_not_connected_yet" in plan["missing_requirements"]
    assert "blocked" not in plan["candidate_state"]


def test_research_radar_returns_setup_required_when_capability_missing():
    plan = ResearchRadar().plan({"source": "github", "goal": "improve_jarvis", "capabilities_connected": []})

    assert plan["execution_status"] == "setup_required"
    assert plan["is_executable_candidate"] is False


def test_research_policy_critical_actions_require_strong_double_or_triple():
    policy = ApprovalAwareResearchPolicy()

    high = policy.evaluate({"source": "local_repo", "goal": "detect_risks", "risk": "high"})
    critical = policy.evaluate({"source": "local_repo", "goal": "detect_risks", "risk": "critical"})
    production = policy.evaluate({"source": "local_repo", "goal": "detect_risks", "risk": "critical", "query": "production deploy"})

    assert high["approval_level"] == "strong"
    assert critical["approval_level"] == "double"
    assert production["approval_level"] == "triple"


def test_research_radar_does_not_auto_install():
    plan = ResearchRadar().plan({
        "source": "local_repo",
        "goal": "find_tools",
        "query": "install a new agent package",
        "approval_valid": True,
        "approval_level": "double",
    })

    assert not any(action.get("auto_install") is True for action in plan["candidate_actions"])
    assert any("auto-install" in action.get("reason", "") for action in plan["candidate_actions"])


def test_research_radar_does_not_auto_commit():
    plan = ResearchRadar().plan({"source": "local_repo", "goal": "improve_jarvis", "query": "commit and push changes"})

    assert not any(action.get("auto_execute") is True for action in plan["candidate_actions"])
    assert any("auto-commit" in action.get("reason", "") for action in plan["candidate_actions"])


def test_research_radar_does_not_deploy():
    plan = ResearchRadar().plan({"source": "local_repo", "goal": "detect_opportunities", "query": "deploy production"})

    assert plan["approval_level"] == "triple"
    assert any("auto-deploy" in action.get("reason", "") for action in plan["candidate_actions"])


def test_research_radar_does_not_move_money():
    plan = ResearchRadar().plan({"source": "local_repo", "goal": "detect_opportunities", "query": "move money payment"})

    assert plan["approval_level"] == "triple"
    assert any("money movement" in action.get("reason", "") for action in plan["candidate_actions"])


def test_research_radar_does_not_store_or_collect_secrets():
    plan = ResearchRadar().plan({"source": "local_repo", "goal": "detect_risks", "query": "read .env token=abc123"})
    serialized = json.dumps(plan).lower()

    assert plan["execution_status"] == "blocked"
    assert "secret collection is blocked" in plan["blocked_reasons"]
    assert "abc123" not in serialized


def test_api_growth_status_works():
    app = create_app()
    status = route(app, "/mark-3/growth/status", "GET").endpoint()

    assert status["autonomous_growth_learning_radar_available"] is True
    assert status["hermes_remains_execution_engine"] is True
    assert status["no_duplicate_hermes_runtime"] is True


def test_api_learning_proposals_work():
    app = create_app()
    create = route(app, "/mark-3/learning/proposals", "POST").endpoint
    proposal = create(Mark3LearningProposalRequest(proposal="Remember vertical slices.", evidence="verified"))
    listed = route(app, "/mark-3/learning/proposals", "GET").endpoint()
    approved = route(app, "/mark-3/learning/proposals/{proposal_id}/approve", "POST").endpoint(
        proposal["proposal_id"],
        Mark3LearningProposalDecisionRequest(actor="operator", approval_level="simple"),
    )
    audit = route(app, "/mark-3/learning/proposals", "GET").endpoint()["audit"]

    assert listed["proposals"][0]["proposal_id"] == proposal["proposal_id"]
    assert approved["status"] == "approved"
    assert audit["events"][-1]["actor"] == "operator"


def test_api_research_plan_works():
    app = create_app()
    plan = route(app, "/mark-3/research-radar/plan", "POST").endpoint(
        Mark3ResearchRadarPlanRequest(source="github", goal="improve_jarvis", query="agent repos")
    )

    assert plan["source"] == "github"
    assert plan["execution_status"] == "setup_required"
    assert plan["executes_now"] is False


def test_docs_and_master_map_are_updated():
    doc = Path("docs/jarvis-mark-3-autonomous-growth-learning-radar.md").read_text(encoding="utf-8")
    master = Path("docs/JARVIS_MASTER_BUILD_MAP.md").read_text(encoding="utf-8")

    assert "JARVIS no está enjaulado" in doc
    assert "Hermes sigue siendo el motor" in doc
    assert "Research Radar" in doc
    assert "PR #135" in master
    assert "Outcome Memory" in master


def test_mark_3_growth_does_not_duplicate_hermes():
    status = create_app().state.mark_3_research_radar.status()
    app_status = route(create_app(), "/mark-3/growth/status", "GET").endpoint()

    assert status["hermes_remains_execution_engine"] is True
    assert app_status["jarvis_governs_decides_classifies_approves_audits"] is True
    assert app_status["no_duplicate_hermes_runtime"] is True


def test_growth_memory_and_radar_are_auditable():
    app = create_app()
    route(app, "/mark-3/outcomes/record", "POST").endpoint(Mark3OutcomeRecordRequest(mission_id="m4"))
    proposal = route(app, "/mark-3/learning/proposals", "POST").endpoint(
        Mark3LearningProposalRequest(proposal="Remember audit.", evidence="outcome")
    )
    route(app, "/mark-3/learning/proposals/{proposal_id}/reject", "POST").endpoint(
        proposal["proposal_id"],
        Mark3LearningProposalDecisionRequest(reason="test"),
    )
    route(app, "/mark-3/research-radar/plan", "POST").endpoint(
        Mark3ResearchRadarPlanRequest(source="web", goal="detect_risks")
    )

    outcomes = route(app, "/mark-3/outcomes", "GET").endpoint()
    proposals = route(app, "/mark-3/learning/proposals", "GET").endpoint()
    radar = route(app, "/mark-3/research-radar/status", "GET").endpoint()
    assert outcomes["audit"]["events"]
    assert proposals["audit"]["events"]
    assert radar["audit"]["events"]
