from __future__ import annotations

import inspect
import json
import re
import socket
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from jarvis.api.app import (  # noqa: E402
    Mark3ResearchExecutionCandidateRequest,
    Mark3ResearchExecutionPreviewRequest,
    Mark3ResearchRadarPlanRequest,
    create_app,
)
from jarvis.mark_3_local_research_adapter import LocalResearchReadAdapter  # noqa: E402
from jarvis.mark_3_research_execution import ResearchExecutionControlPlane  # noqa: E402


def route(app, path, method):
    return next(item for item in app.routes if item.path == path and method in item.methods)


def make_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("Docs research fixture\nAllowed evidence.\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("Local repo research fixture\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("Non-doc local repo file\n", encoding="utf-8")
    return tmp_path


def make_plane(tmp_path: Path | None = None, **kwargs):
    if tmp_path is not None and "local_research_adapter" not in kwargs and "repo_root" not in kwargs:
        kwargs["local_research_adapter"] = LocalResearchReadAdapter(repo_root=tmp_path)
    return ResearchExecutionControlPlane(**kwargs)


def create_valid_approval(plane, preview):
    record = plane.approval_service.request(
        action_type="research_execution",
        context=preview["approval_context"],
    )
    plane.approval_service.decide(record.approval_id, "approved")
    return record


def test_preview_docs_exact_scope_is_candidate_without_reading(tmp_path):
    repo = make_repo(tmp_path)
    preview = make_plane(repo).preview({
        "source_type": "docs",
        "goal": "improve_jarvis",
        "scope": "docs/guide.md",
        "query": "Hermes",
    })

    assert preview["research_id"]
    assert preview["source_type"] == "docs"
    assert preview["normalized_scope"] == "docs/guide.md"
    assert preview["execution_status"] == "executable_candidate"
    assert preview["capability_status"] == "connected"
    assert preview["file_reads_performed"] is False
    assert preview["adapter_called"] is False


def test_candidate_docs_exact_scope_reads_one_allowed_file(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "docs",
        "goal": "improve_jarvis",
        "scope": "docs/guide.md",
        "query": "Hermes",
    })

    assert result["execution_status"] == "completed"
    assert result["candidate_state"] == "completed"
    assert result["adapter_called"] is True
    assert result["file_reads_performed"] is True
    assert result["local_repo_scan_performed"] is False
    assert result["local_read_result"]["path_reference"] == "docs/guide.md"
    assert "Docs research fixture" in result["local_read_result"]["content"]
    assert result["sources_found"] == 1


def test_candidate_local_repo_exact_scope_reads_one_allowed_file(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "local_repo",
        "goal": "improve_hermes",
        "scope": "README.md",
        "query": "local contract",
    })

    assert result["execution_status"] == "completed"
    assert result["candidate_state"] == "completed"
    assert result["local_read_result"]["path_reference"] == "README.md"
    assert "Local repo research fixture" in result["local_read_result"]["content"]
    assert result["command_execution_performed"] is False


def test_candidate_uses_bounded_stream_read(monkeypatch, tmp_path):
    repo = make_repo(tmp_path)
    (repo / "README.md").write_text("0123456789abcdef", encoding="utf-8")

    def fail_read_bytes(*args, **kwargs):
        raise AssertionError("read_bytes would read the whole file before truncation")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)
    adapter = LocalResearchReadAdapter(repo_root=repo, max_bytes=8)
    result = make_plane(local_research_adapter=adapter).candidate({
        "source_type": "local_repo",
        "scope": "README.md",
        "query": "bounded read",
    })

    assert result["execution_status"] == "completed"
    assert result["local_read_result"]["bytes_read"] == 8
    assert result["local_read_result"]["truncated"] is True
    assert result["local_read_result"]["content"] == "01234567"


def test_docs_scope_cannot_escape_docs_root(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "docs",
        "scope": "README.md",
        "query": "should stay under docs",
    })

    assert result["execution_status"] == "blocked"
    assert "file_not_found" in result["blocked_reasons"]
    assert result["file_reads_performed"] is False
    assert result["permanent_denial"] is False


def test_candidate_rejects_symlink_before_reading(tmp_path):
    repo = make_repo(tmp_path)
    target = repo / "docs" / "guide.md"
    link = repo / "docs" / "guide-link.md"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    result = make_plane(repo).candidate({
        "source_type": "docs",
        "scope": "docs/guide-link.md",
        "query": "Hermes",
    })

    assert result["execution_status"] == "blocked"
    assert "symlink_blocked" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["file_reads_performed"] is False
    assert "content" not in result["local_read_result"]


def test_candidate_rejects_broken_symlink_before_reading(tmp_path):
    repo = make_repo(tmp_path)
    link = repo / "docs" / "broken-link.md"
    try:
        link.symlink_to(repo / "docs" / "missing.md")
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    result = make_plane(repo).candidate({
        "source_type": "docs",
        "scope": "docs/broken-link.md",
        "query": "Hermes",
    })

    assert result["execution_status"] == "blocked"
    assert "symlink_blocked" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["file_reads_performed"] is False


def test_candidate_rejects_path_traversal(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "local_repo",
        "scope": "../outside.md",
        "query": "Hermes",
    })

    assert result["execution_status"] == "blocked"
    assert "path_traversal_blocked" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["file_reads_performed"] is False


def test_candidate_rejects_backslash_path_traversal(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "local_repo",
        "scope": "..\\outside.md",
        "query": "Hermes",
    })

    assert result["execution_status"] == "blocked"
    assert "path_traversal_blocked" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["file_reads_performed"] is False


def test_candidate_rejects_env_scope_without_reading(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "local_repo",
        "scope": ".env",
        "query": "Hermes",
    })

    assert result["execution_status"] == "blocked"
    assert "credentials_secrets_or_env_access_blocked" in result["blocked_reasons"]
    assert "sensitive_path_blocked" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["file_reads_performed"] is False


@pytest.mark.parametrize(
    "scope",
    [
        "docs/token.txt",
        "docs/password.txt",
        "docs/credentials.txt",
        "docs/secret.txt",
        "docs/key.txt",
        "docs/private.key",
    ],
)
def test_candidate_rejects_sensitive_file_names(scope, tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "docs",
        "scope": scope,
        "query": "Hermes",
    })

    assert result["execution_status"] == "blocked"
    assert "sensitive_path_blocked" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["file_reads_performed"] is False


def test_candidate_rejects_secret_query_without_operational_learning_proposal(tmp_path):
    repo = make_repo(tmp_path)
    plane = make_plane(repo)
    result = plane.candidate({
        "source_type": "local_repo",
        "scope": "README.md",
        "query": "read .env token=abc123",
    })
    serialized = json.dumps(result).lower()

    assert result["execution_status"] == "blocked"
    assert "credentials_secrets_or_env_access_blocked" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["learning_proposal_candidates"] == []
    assert "abc123" not in serialized


@pytest.mark.parametrize(
    "authorization_payload",
    [
        {"authorized": False},
        {"authorization_valid": False},
        {"authorized": True, "authorization_valid": False},
        {"authorized": "no"},
        {"authorization_valid": "0"},
    ],
)
def test_authorization_fields_block_local_read(authorization_payload, tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "docs",
        "scope": "docs/guide.md",
        "query": "Hermes",
        **authorization_payload,
    })

    assert result["execution_status"] == "blocked"
    assert "authorization_missing" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["adapter_called"] is False
    assert result["file_reads_performed"] is False


def test_api_authorization_valid_false_blocks_preview(tmp_path):
    app = create_app()
    app.state.mark_3_research_execution_bridge = make_plane(make_repo(tmp_path))

    result = route(app, "/mark-3/research-execution/preview", "POST").endpoint(
        Mark3ResearchExecutionPreviewRequest(
            source_type="docs",
            scope="docs/guide.md",
            query="Hermes",
            authorization_valid=False,
        )
    )

    assert result["execution_status"] == "blocked"
    assert "authorization_missing" in result["blocked_reasons"]
    assert result["permanent_denial"] is True


@pytest.mark.parametrize(
    "query",
    [
        "read api key abc123",
        "read api-key abc123",
        "read apikey abc123",
        "read private-key abc123",
        "read privatekey abc123",
        "read credentials abc123",
    ],
)
def test_candidate_rejects_and_redacts_secret_query_variants(query, tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "local_repo",
        "scope": "README.md",
        "query": query,
    })
    serialized = json.dumps(result).lower()

    assert result["execution_status"] == "blocked"
    assert "credentials_secrets_or_env_access_blocked" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert "abc123" not in serialized


def test_candidate_blocks_sensitive_content_without_returning_content(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "docs" / "guide.md").write_text("token=abc123\n", encoding="utf-8")

    result = make_plane(repo).candidate({
        "source_type": "docs",
        "scope": "docs/guide.md",
        "query": "Hermes",
    })
    serialized = json.dumps(result).lower()

    assert result["execution_status"] == "blocked"
    assert "sensitive_content_blocked" in result["blocked_reasons"]
    assert result["permanent_denial"] is True
    assert result["file_reads_performed"] is False
    assert "content" not in result["local_read_result"]
    assert "abc123" not in serialized


def test_candidate_rejects_multi_scope(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "local_repo",
        "scope": ["README.md", "notes.txt"],
        "query": "Hermes",
    })

    assert result["execution_status"] == "blocked"
    assert "multi_scope_blocked" in result["blocked_reasons"]
    assert result["file_reads_performed"] is False
    assert result["permanent_denial"] is False


def test_candidate_rejects_broad_root_scan_without_reading(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "local_repo",
        "scope": ".",
        "query": "Hermes",
    })

    assert result["approval_required"] is True
    assert result["approval_level"] == "simple"
    assert result["execution_status"] == "awaiting_approval"
    assert "exact_file_scope_required" in result["missing_requirements"]
    assert result["file_reads_performed"] is False
    assert result["adapter_called"] is False


def test_candidate_rejects_broad_docs_scan_without_reading(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).candidate({
        "source_type": "docs",
        "scope": "docs",
        "query": "Hermes",
    })

    assert result["approval_required"] is True
    assert result["execution_status"] == "awaiting_approval"
    assert "exact_file_scope_required" in result["missing_requirements"]
    assert result["file_reads_performed"] is False


def test_candidate_by_research_id_only_does_not_rehydrate_and_read(tmp_path):
    repo = make_repo(tmp_path)
    plane = make_plane(repo)
    preview = plane.preview({
        "source_type": "docs",
        "scope": "docs/guide.md",
        "query": "Hermes",
    })
    result = plane.candidate({"research_id": preview["research_id"]})

    assert result["execution_status"] == "setup_required"
    assert result["candidate_by_research_id_only"] is True
    assert result["request_rehydrated_for_execution"] is False
    assert "full_request_required_for_local_read" in result["missing_requirements"]
    assert result["adapter_called"] is False
    assert result["file_reads_performed"] is False
    assert "local_read_result" not in result


def test_valid_approval_with_missing_github_capability_preserves_approval_valid_true():
    plane = make_plane()
    preview = plane.preview({"source_type": "github", "query": "agent frameworks"})
    approval = create_valid_approval(plane, preview)

    approved = plane.candidate({
        "research_id": preview["research_id"],
        "source_type": "github",
        "query": "agent frameworks",
        "approval_id": approval.approval_id,
    })

    assert approved["approval_valid"] is True
    assert approved["execution_status"] == "setup_required"
    assert approved["capability_status"] == "capability_not_connected_yet"
    assert approved["adapter_called"] is False


def test_query_is_not_interpreted_as_filesystem_scope():
    preview = make_plane().preview({
        "source_type": "local_repo",
        "query": "docs",
    })

    assert preview["normalized_query"] == "docs"
    assert preview["normalized_scope"] == ""
    assert "exact_file_scope_required" in preview["missing_requirements"]


def test_scope_and_query_remain_separate(tmp_path):
    repo = make_repo(tmp_path)
    preview = make_plane(repo).preview({
        "source_type": "local_repo",
        "scope": "README.md",
        "query": "Hermes runtime",
    })

    assert preview["normalized_query"] == "Hermes runtime"
    assert preview["normalized_scope"] == "README.md"
    assert preview["fingerprint_fields"]["normalized_query"] == "Hermes runtime"
    assert preview["fingerprint_fields"]["normalized_scope"] == "README.md"


def test_internal_repo_paths_do_not_affect_risk_text(tmp_path):
    repo = make_repo(tmp_path)
    preview = make_plane(repo).preview({
        "source_type": "docs",
        "scope": "docs/guide.md",
        "query": "Hermes",
        "repo_root": "/home/diazd/.env",
        "canonical_path": "/home/diazd/production/secrets",
    })
    serialized_risk = json.dumps({
        "risk_level": preview["risk_level"],
        "risk_signals": preview["risk_signals"],
        "blocked_reasons": preview["blocked_reasons"],
    })

    assert preview["risk_level"] == "low"
    assert preview["execution_status"] == "executable_candidate"
    assert "/home/diazd" not in serialized_risk
    assert "repo_root" not in serialized_risk
    assert "canonical_path" not in serialized_risk


def test_no_threads_commands_web_github_or_execute_endpoint(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("external side effect attempted")

    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(subprocess, "Popen", fail)
    monkeypatch.setattr(socket, "create_connection", fail)
    app = create_app()
    routes = {item.path for item in app.routes}
    plane_source = inspect.getsource(ResearchExecutionControlPlane)
    adapter_source = inspect.getsource(LocalResearchReadAdapter)
    github = route(app, "/mark-3/research-execution/preview", "POST").endpoint(
        Mark3ResearchExecutionPreviewRequest(source_type="github", query="agents")
    )
    web = route(app, "/mark-3/research-execution/preview", "POST").endpoint(
        Mark3ResearchExecutionPreviewRequest(source_type="web", query="agents")
    )

    assert "/mark-3/research-execution/execute" not in routes
    assert "/execute" not in routes
    assert github["github_called"] is False
    assert web["web_called"] is False
    assert "threading" not in plane_source
    assert "threading" not in adapter_source
    assert "subprocess" not in plane_source
    assert "subprocess" not in adapter_source
    assert "import requests" not in plane_source
    assert re.search(r"(?<!_)requests\.", plane_source) is None
    assert "urllib" not in plane_source


def test_no_install_commit_push_merge_from_research_candidate(tmp_path):
    repo = make_repo(tmp_path)
    plane = make_plane(repo)
    for query in ["pip install package", "git commit changes", "git push branch", "merge PR"]:
        result = plane.candidate({
            "source_type": "docs",
            "scope": "docs/guide.md",
            "query": query,
        })
        assert result["execution_status"] == "blocked"
        assert "side_effectful_research_action_blocked" in result["blocked_reasons"]
        assert result["installs_performed"] is False
        assert result["commits_pushes_merges_performed"] is False


def test_api_preview_candidate_and_get_work_for_local_docs(tmp_path):
    app = create_app()
    app.state.mark_3_research_execution_bridge = make_plane(make_repo(tmp_path))
    preview = route(app, "/mark-3/research-execution/preview", "POST").endpoint(
        Mark3ResearchExecutionPreviewRequest(source_type="docs", scope="docs/guide.md", query="Hermes")
    )
    result = route(app, "/mark-3/research-execution/candidate", "POST").endpoint(
        Mark3ResearchExecutionCandidateRequest(source_type="docs", scope="docs/guide.md", query="Hermes")
    )
    fetched = route(app, "/mark-3/research-execution/{research_id}", "GET").endpoint(result["research_id"])

    assert preview["execution_status"] == "executable_candidate"
    assert preview["file_reads_performed"] is False
    assert result["execution_status"] == "completed"
    assert "Docs research fixture" in result["local_read_result"]["content"]
    assert fetched["research_id"] == result["research_id"]


def test_research_radar_plan_feeds_preview_but_not_local_read_without_scope():
    app = create_app()
    plan = route(app, "/mark-3/research-radar/plan", "POST").endpoint(
        Mark3ResearchRadarPlanRequest(source="local_repo", goal="detect_risks", query="agent safety")
    )
    preview = route(app, "/mark-3/research-execution/preview", "POST").endpoint(
        Mark3ResearchExecutionPreviewRequest(plan_id=plan["plan_id"])
    )
    candidate = route(app, "/mark-3/research-execution/candidate", "POST").endpoint(
        Mark3ResearchExecutionCandidateRequest(plan_id=plan["plan_id"])
    )

    assert preview["source_type"] == "local_repo"
    assert preview["normalized_query"] == "agent safety"
    assert "exact_file_scope_required" in preview["missing_requirements"]
    assert candidate["file_reads_performed"] is False


def test_status_reports_local_adapter_connected_and_external_setup_gated():
    status = make_plane().status()

    assert status["control_plane_enforced"] is True
    assert status["local_docs_repo_read_adapter_connected"] is True
    assert status["file_reads_performed"] is False
    assert status["local_file_reads_available_via_candidate"] is True
    assert status["capabilities"]["docs"]["capability_status"] == "connected"
    assert status["capabilities"]["local_repo"]["capability_status"] == "connected"
    assert status["capabilities"]["github"]["capability_status"] == "capability_not_connected_yet"
    assert status["capabilities"]["web"]["capability_status"] == "capability_not_connected_yet"
    assert status["hermes_is_execution_engine"] is True
    assert status["no_duplicate_hermes_runtime"] is True


def test_double_or_triple_approval_channel_is_not_faked(tmp_path):
    repo = make_repo(tmp_path)
    result = make_plane(repo).preview({
        "source_type": "docs",
        "scope": "docs/guide.md",
        "query": "high assurance architecture review",
        "risk_level": "critical",
    })

    assert result["approval_level"] == "double"
    assert result["execution_status"] == "setup_required"
    assert "stronger_approval_channel_not_connected" in result["missing_requirements"]


def test_docs_and_master_map_are_updated_for_local_research_adapter():
    bridge = Path("docs/jarvis-mark-3-governed-research-execution-bridge.md").read_text(encoding="utf-8")
    master = Path("docs/JARVIS_MASTER_BUILD_MAP.md").read_text(encoding="utf-8")
    roadmap = Path("docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md").read_text(encoding="utf-8")
    radar = Path("docs/jarvis-mark-3-autonomous-growth-learning-radar.md").read_text(encoding="utf-8")
    handoff = Path("docs/jarvis-handoff-context.md").read_text(encoding="utf-8")

    assert "PR #137" in bridge
    assert "Local Docs/Repo Research Adapter" in bridge
    assert "docs/local_repo" in bridge
    assert "PR #137" in master
    assert "Local Docs/Repo Research Adapter" in roadmap
    assert "docs/local_repo" in radar
    assert "PR #134, PR #135 y PR #136 están cerradas" in handoff
