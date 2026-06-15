from __future__ import annotations

import builtins
import json
import socket
import threading
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import Mark3ResearchExecutionRequest, create_app
from jarvis.mark_3_learning_proposals import LearningProposalEngine
from jarvis.mark_3_outcome_memory import OutcomeMemoryStore
from jarvis.mark_3_research_execution import (
    Mark3ResearchExecutionControlPlane,
    normalize_research_request,
)


def _service() -> Mark3ResearchExecutionControlPlane:
    return Mark3ResearchExecutionControlPlane()


def _route(app, path: str, method: str):
    for route in app.routes:
        if route.path == path and method in route.methods:
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_preview_github_requires_external_approval() -> None:
    result = _service().preview({"source_type": "github", "query": "agent runtime patterns"})

    assert result["approval_required"] is True
    assert result["required_approval_level"] == "simple"
    assert result["approval_valid"] is False
    assert result["capability_status"] == "capability_not_connected_yet"
    assert result["candidate_state"] == "setup_required"


def test_preview_web_requires_external_approval() -> None:
    result = _service().preview({"source_type": "web", "query": "safe research execution"})

    assert result["approval_required"] is True
    assert result["required_approval_level"] == "simple"
    assert "external_network_requires_approval" in result["blocked_reasons"]
    assert result["web_calls_performed"] is False


def test_preview_docs_returns_setup_required() -> None:
    result = _service().preview({"source_type": "docs", "query": "operator docs"})

    assert result["candidate_state"] == "setup_required"
    assert result["capability_status"] == "capability_not_connected_yet"
    assert result["permanent_denial"] is False


def test_preview_local_repo_returns_setup_required() -> None:
    result = _service().preview({"source_type": "local_repo", "query": "mission loop contracts"})

    assert result["candidate_state"] == "setup_required"
    assert result["capability_status"] == "capability_not_connected_yet"
    assert result["local_scans_performed"] is False


def test_topic_enters_query_as_alias() -> None:
    normalized = normalize_research_request({"source_type": "docs", "topic": "policy bridge"})

    assert normalized["query"] == "policy bridge"
    assert normalized["topic"] == "policy bridge"


def test_source_alias_sets_source_type() -> None:
    normalized = normalize_research_request({"source": "web", "query": "governed research"})

    assert normalized["source_type"] == "web"
    assert normalized["safe_snapshot"]["source"] == "web"


def test_unsupported_source_is_blocked_not_rewritten_to_local_repo() -> None:
    result = _service().preview({"source": "slack", "query": "safe research"})

    assert result["request_normalized"]["source_type"] == "slack"
    assert result["candidate_state"] == "blocked"
    assert "source_type_unsupported" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["can_become_executable_candidate"] is False


def test_absent_source_defaults_to_local_repo() -> None:
    result = _service().preview({"query": "safe local planning"})

    assert result["request_normalized"]["source_type"] == "local_repo"
    assert result["candidate_state"] == "setup_required"
    assert result["permanent_denial"] is False


def test_risk_alias_sets_risk_level() -> None:
    normalized = normalize_research_request({"source_type": "docs", "query": "review", "risk": "high"})

    assert normalized["risk_level"] == "high"
    assert normalized["safe_snapshot"]["risk"] == "high"


def test_query_and_scope_are_not_mixed() -> None:
    with_both = normalize_research_request({
        "source_type": "local_repo",
        "query": "find policy seams",
        "scope": "jarvis only",
    })
    scope_only = normalize_research_request({"source_type": "local_repo", "scope": "jarvis only"})

    assert with_both["query"] == "find policy seams"
    assert with_both["scope"] == "jarvis only"
    assert scope_only["query"] == ""
    assert scope_only["scope"] == "jarvis only"


def test_query_env_blocks_permanently_without_raw_snapshot() -> None:
    result = _service().preview({"source_type": "local_repo", "query": "inspect .env"})
    payload = json.dumps(result, sort_keys=True)

    assert result["permanent_denial"] is True
    assert result["can_become_executable_candidate"] is False
    assert result["safe_snapshot"]["query"] == "[redacted sensitive text]"
    assert ".env" not in payload


def test_query_token_blocks_permanently_without_raw_snapshot() -> None:
    result = _service().preview({"source_type": "web", "query": "token=abc123"})
    payload = json.dumps(result, sort_keys=True)

    assert result["permanent_denial"] is True
    assert result["can_become_executable_candidate"] is False
    assert "secret_or_credential_request_blocked" in result["blocked_reasons"]
    assert "abc123" not in payload


def test_execute_with_only_research_id_does_not_revalidate_redacted_request() -> None:
    service = _service()
    preview = service.preview({"source_type": "web", "query": "token=abc123"})

    result = service.execute({"research_id": preview["research_id"]})

    assert result["policy_recalculated"] is False
    assert result["candidate_state"] == "setup_required"
    assert "redacted_snapshot_not_revalidatable" in result["blocked_reasons"]
    assert "abc123" not in json.dumps(result, sort_keys=True)


def test_execute_with_full_request_recalculates_policy() -> None:
    service = _service()
    preview = service.preview({"source_type": "web", "query": "token=abc123"})

    result = service.execute({
        "research_id": preview["research_id"],
        "request": {"source_type": "github", "query": "safe agent benchmarks"},
    })

    assert result["policy_recalculated"] is True
    assert result["permanent_denial"] is False
    assert result["approval_required"] is True
    assert result["capability_status"] == "capability_not_connected_yet"


def test_blocked_request_does_not_create_adapter_proposal() -> None:
    outcomes = OutcomeMemoryStore()
    proposals = LearningProposalEngine()
    service = Mark3ResearchExecutionControlPlane(outcome_memory=outcomes, learning_proposals=proposals)

    result = service.preview({"source_type": "web", "query": "token=abc123"})

    assert result["integration"]["adapter_proposal_created"] is False
    assert proposals.list() == []
    assert outcomes.list_outcomes() == []


def test_capability_missing_legal_request_registers_setup_required() -> None:
    outcomes = OutcomeMemoryStore()
    proposals = LearningProposalEngine()
    service = Mark3ResearchExecutionControlPlane(outcome_memory=outcomes, learning_proposals=proposals)

    result = service.preview({"source_type": "docs", "query": "approval policy"})

    assert result["integration"]["setup_required_outcome_registered"] is True
    assert result["integration"]["failure_memory_registered"] is True
    assert result["integration"]["adapter_proposal_created"] is True
    assert outcomes.list_outcomes()[0]["result_status"] == "setup_required"
    assert outcomes.list_failures()[0]["category"] == "adapter_not_connected"
    assert proposals.list()[0]["status"] == "proposed"


def test_can_become_executable_candidate_false_for_secret_blocked() -> None:
    result = _service().preview({"source_type": "docs", "query": "password list"})

    assert result["can_become_executable_candidate"] is False
    assert result["permanent_denial"] is True


def test_authorization_valid_false_blocks_even_with_authorized_default_true() -> None:
    app = create_app(voice_adapter=object())

    response = _route(app, "/mark-3/research-execution/preview", "POST")(Mark3ResearchExecutionRequest(**{
        "source_type": "docs",
        "query": "safe planning",
        "authorization_valid": False,
    }))

    assert response["candidate_state"] == "blocked"
    assert "authorization_missing" in response["blocked_reasons"]
    assert response["permanent_denial"] is True
    assert response["can_become_executable_candidate"] is False


def test_authorized_false_blocks_even_with_authorization_valid_true() -> None:
    result = _service().preview({
        "source_type": "docs",
        "query": "safe planning",
        "authorized": False,
        "authorization_valid": True,
    })

    assert result["candidate_state"] == "blocked"
    assert "authorization_missing" in result["blocked_reasons"]
    assert result["permanent_denial"] is True


def test_can_become_executable_candidate_true_for_legal_missing_capability() -> None:
    result = _service().preview({"source_type": "local_repo", "query": "read architecture docs"})

    assert result["can_become_executable_candidate"] is True
    assert result["permanent_denial"] is False


def test_service_performs_no_file_reads_or_path_scans(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("filesystem read or scan should not be used")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "rglob", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)

    service = _service()
    service.preview({"source_type": "local_repo", "query": "architecture"})
    service.execute({"request": {"source_type": "docs", "query": "planning"}})


def test_service_starts_no_threads(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("threads should not be used")

    monkeypatch.setattr(threading, "Thread", forbidden)

    result = _service().preview({"source_type": "web", "query": "safe docs"})

    assert result["threads_started"] is False


def test_service_makes_no_github_or_web_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("network should not be used")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)

    result = _service().preview({"source_type": "web", "query": "safe docs"})

    assert result["web_calls_performed"] is False
    assert result["github_calls_performed"] is False


def test_no_research_execution_stop_endpoint() -> None:
    app = create_app(voice_adapter=object())
    paths = {route.path for route in app.routes}

    assert "/mark-3/research-execution/execute" not in paths
    assert "/mark-3/research-execution/stop" not in paths
    assert not any(path.startswith("/mark-3/research-execution/") and path.endswith("/execute") for path in paths)
    assert not any(path.startswith("/mark-3/research-execution/") and path.endswith("/stop") for path in paths)


def test_api_status_works() -> None:
    app = create_app(voice_adapter=object())

    response = _route(app, "/mark-3/research-execution/status", "GET")()

    assert response["real_research_execution_enabled"] is False


def test_api_preview_works() -> None:
    app = create_app(voice_adapter=object())

    response = _route(app, "/mark-3/research-execution/preview", "POST")(Mark3ResearchExecutionRequest(**{
        "source": "github",
        "query": "safe research",
    }))

    assert response["approval_required"] is True
    assert response["capability_status"] == "capability_not_connected_yet"


def test_api_candidate_works_without_executing() -> None:
    app = create_app(voice_adapter=object())

    response = _route(app, "/mark-3/research-execution/candidate", "POST")(Mark3ResearchExecutionRequest(**{
        "request": {"source_type": "docs", "query": "safe planning"},
    }))

    assert response["executed"] is False
    assert response["adapters_called"] is False
    assert response["candidate_state"] == "setup_required"


def test_api_get_research_id_returns_safe_snapshot_only() -> None:
    app = create_app(voice_adapter=object())
    preview = _route(app, "/mark-3/research-execution/preview", "POST")(Mark3ResearchExecutionRequest(**{
        "source_type": "docs",
        "query": "safe planning",
    }))

    response = _route(app, "/mark-3/research-execution/{research_id}", "GET")(preview["research_id"])

    assert response["raw_request_stored"] is False
    assert response["can_execute_from_stored_snapshot"] is False


def test_status_lists_bridge_and_master_map_docs() -> None:
    status = _service().status()

    assert "docs/jarvis-mark-3-governed-research-execution-bridge.md" in status["documentation"]
    assert "docs/JARVIS_MASTER_BUILD_MAP.md" in status["documentation"]
