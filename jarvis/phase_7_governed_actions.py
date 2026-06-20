from __future__ import annotations

import difflib
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple
from urllib.parse import urlparse
from uuid import uuid4

from jarvis.approval_hardening import ApprovalStatus
from jarvis.phase_2_local_assistant_runtime import (
    ACTION_CATALOG,
    PHASE_2_SCHEMA_VERSION,
    ActionContract,
    _action_id,
    _completed,
    _fingerprint,
    _json_dumps,
    _path_is_secret_like,
    _redact_text,
    _safe_inputs_for_public,
    _safe_text,
)
from jarvis.phase_5_local_controller_trusted_identity_voice_approval import (
    Phase5LocalControllerTrustedIdentityVoiceApprovalControlPlane,
)


PHASE_7_SCHEMA_VERSION = "jarvis.phase_7_governed_actions_browser_filesystem_github_sandbox.v1"
ACTION_CATALOG_V2_SCHEMA_VERSION = "jarvis.governed_action_catalog.v2"
PHASE7_BACKUP_DIR = Path(".jarvis") / "phase_7_backups"

PHASE7_ACTION_KEYS: Tuple[str, ...] = (
    "filesystem.file.read_text",
    "filesystem.directory.list",
    "filesystem.file.write_safe",
    "filesystem.file.delete_dry_run",
    "github.repo.status",
    "github.worktree.status",
    "github.changed_files.list",
    "github.diff.summary",
    "github.branch.prepare",
    "github.pr.prepare_description",
    "github.branch.create_local",
    "browser.url.open_plan",
    "browser.screenshot.plan",
    "browser.form.fill_dry_run",
    "browser.click.submit_plan",
    "sandbox.command.plan",
    "sandbox.command.dry_run",
    "sandbox.command.run_allowlisted",
    "preflight.scan",
)

SANDBOX_COMMANDS: Dict[str, Dict[str, Any]] = {
    "git_status": {
        "argv": ["git", "status", "--short", "--branch"],
        "risk_level": "low",
        "read_only": True,
        "timeout_seconds": 10,
        "description": "Read git worktree status.",
    },
    "git_diff_stat": {
        "argv": ["git", "diff", "--stat"],
        "risk_level": "low",
        "read_only": True,
        "timeout_seconds": 10,
        "description": "Read git diff stat.",
    },
    "git_diff_check": {
        "argv": ["git", "diff", "--check"],
        "risk_level": "low",
        "read_only": True,
        "timeout_seconds": 10,
        "description": "Run git whitespace/conflict marker check.",
    },
    "python_py_compile": {
        "argv": [sys.executable, "-m", "py_compile"],
        "risk_level": "medium",
        "read_only": False,
        "timeout_seconds": 30,
        "description": "Compile one allowlisted Python file by path.",
        "path_arg": True,
    },
    "pytest_targeted": {
        "argv": [sys.executable, "-m", "pytest", "-c", "/dev/null"],
        "risk_level": "medium",
        "read_only": False,
        "timeout_seconds": 120,
        "description": "Run one allowlisted targeted pytest file.",
        "target_arg": True,
        "allowed_targets": [
            "tests/jarvis/test_pr_172_phase_7_governed_actions.py",
            "tests/jarvis/test_pr_165_phase_1_completion_governed_execution_pilot.py",
            "tests/jarvis/test_pr_166_phase_2_local_assistant_runtime.py",
            "tests/jarvis/test_pr_170_phase_5_local_controller_identity_voice.py",
            "tests/jarvis/test_pr_171_phase_6_real_voice_wake_memory_sensor_runtime.py",
        ],
    },
}


SECRET_PATTERNS: Tuple[Tuple[str, str, str], ...] = (
    ("private_key", "critical", r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |)?PRIVATE KEY-----"),
    ("stripe_live_key", "critical", r"\b(?:sk|rk)_live_[A-Za-z0-9]{12,}\b"),
    ("openai_key", "high", r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    ("github_token", "high", r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}\b"),
    ("aws_access_key", "high", r"\bAKIA[0-9A-Z]{16}\b"),
    ("slack_token", "high", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    ("password_assignment", "high", r"\bpassword\s*[:=]\s*['\"]?[^'\"\s]{6,}"),
    ("api_key_assignment", "high", r"\b(?:api[_-]?key|token|secret)\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
)
SECRET_FILE_NAMES = {".env", ".env.local", ".env.production", ".npmrc", ".pypirc", "id_rsa", "id_ed25519"}
DESTRUCTIVE_MARKERS = ("rm -rf", "git reset --hard", "git clean -fd", "drop table", "delete from", "truncate table")
PRODUCTION_MARKERS = ("production", "prod.", "stripe live", "sk_live", "deploy", "publish", "payment", "money")


def _contract(
    action_key: str,
    title: str,
    description: str,
    *,
    category: str,
    risk_level: str,
    approval_required: str,
    timeout_seconds: int,
    filesystem_scope: str = "none",
    side_effects: Optional[List[str]] = None,
    filesystem: bool = False,
    github: bool = False,
    browser: bool = False,
    sandbox: bool = False,
    dry_run_available: bool = True,
    rollback_supported: bool = False,
    rollback_plan: str = "not_required",
    rollback_status: str = "not_required",
    rollback_requires_approval: bool = False,
    stop_supported: bool = False,
    stop_method: str = "timeout_only",
    network_allowed: bool = False,
    external_side_effects: bool = False,
    voice_approval_eligible: Optional[bool] = None,
    default_enabled: bool = True,
    default_disabled_reason: str = "",
    allowed_inputs_schema: Optional[Dict[str, Any]] = None,
    audit_event_types: Optional[List[str]] = None,
    output_redaction: str = "metadata_only",
    execution_backend: str = "phase_7_governed_action_adapter",
    rollback_limitations: Optional[List[str]] = None,
) -> ActionContract:
    return ActionContract(
        action_key=action_key,
        title=title,
        category=category,
        description=description,
        allowed_inputs_schema=allowed_inputs_schema or {"type": "object", "properties": {}, "additionalProperties": False},
        risk_level=risk_level,
        approval_required=approval_required,
        timeout_seconds=timeout_seconds,
        stop_supported=stop_supported,
        rollback_supported=rollback_supported,
        audit_event_types=audit_event_types or ["preview_created", "dispatch_started", "dispatch_completed"],
        output_redaction=output_redaction,
        filesystem_scope=filesystem_scope,
        network_allowed=network_allowed,
        external_side_effects=external_side_effects,
        secrets_policy="deny_and_redact",
        stop_method=stop_method,
        rollback_plan=rollback_plan,
        rollback_risk="none" if rollback_supported or rollback_status == "not_required" else "unsupported",
        rollback_requires_approval=rollback_requires_approval,
        rollback_status=rollback_status,
        rollback_limitations=rollback_limitations or [],
        execution_backend=execution_backend,
        side_effects=side_effects or [],
        filesystem=filesystem,
        github=github,
        browser=browser,
        sandbox=sandbox,
        dry_run_available=dry_run_available,
        voice_approval_eligible=voice_approval_eligible,
        default_enabled=default_enabled,
        default_disabled_reason=default_disabled_reason,
    )


PHASE7_ACTION_CATALOG: Dict[str, ActionContract] = {
    "filesystem.file.read_text": _contract(
        "filesystem.file.read_text",
        "Read Safe Text File",
        "Read one non-secret UTF-8 text file from an explicit allowed local root.",
        category="filesystem",
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        filesystem_scope="one_safe_text_file_inside_allowed_root",
        filesystem=True,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"path": {"type": "string", "minLength": 1}},
            "required": ["path"],
            "additionalProperties": False,
        },
        output_redaction="content_returned_only_after_secret_scan_and_size_limit",
    ),
    "filesystem.directory.list": _contract(
        "filesystem.directory.list",
        "List Safe Directory",
        "List metadata for one non-secret directory inside an explicit allowed local root.",
        category="filesystem",
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        filesystem_scope="one_directory_metadata_inside_allowed_root",
        filesystem=True,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"path": {"type": "string", "minLength": 1}, "limit": {"type": "integer", "minimum": 1, "maximum": 200}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    "filesystem.file.write_safe": _contract(
        "filesystem.file.write_safe",
        "Write Safe Project File",
        "Create or update one non-secret text file in an allowed project root after preview, diff and approval.",
        category="filesystem",
        risk_level="medium",
        approval_required="normal",
        timeout_seconds=10,
        filesystem_scope="one_text_file_inside_allowed_root",
        filesystem=True,
        side_effects=["filesystem_write", "backup_created_before_overwrite"],
        rollback_supported=True,
        rollback_plan="restore_backup_for_overwrite_or_delete_created_file_manually_after_review",
        rollback_status="backup_before_overwrite",
        rollback_requires_approval=True,
        dry_run_available=True,
        voice_approval_eligible=True,
        allowed_inputs_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "minLength": 1},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        audit_event_types=["preview_created", "preflight_completed", "approval_requested", "approval_approved", "filesystem_backup_created", "dispatch_started", "dispatch_completed"],
        output_redaction="diff_preview_redacted_and_content_not_stored_in_history",
    ),
    "filesystem.file.delete_dry_run": _contract(
        "filesystem.file.delete_dry_run",
        "Delete File Dry Run",
        "Preview deletion of one safe file only; actual delete remains disabled.",
        category="filesystem",
        risk_level="high",
        approval_required="strong",
        timeout_seconds=5,
        filesystem_scope="one_file_inside_allowed_root",
        filesystem=True,
        side_effects=[],
        rollback_supported=False,
        rollback_plan="not_available_because_delete_execution_is_disabled",
        rollback_status="dry_run_only",
        rollback_limitations=["Actual delete is not implemented in Phase 7."],
        default_enabled=False,
        default_disabled_reason="delete remains dry-run-only in Phase 7",
        voice_approval_eligible=False,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"path": {"type": "string", "minLength": 1}},
            "required": ["path"],
            "additionalProperties": False,
        },
    ),
    "github.repo.status": _contract(
        "github.repo.status",
        "Read Repo Status",
        "Read git status metadata with fixed argv and no network.",
        category="github_worktree",
        risk_level="low",
        approval_required="none",
        timeout_seconds=10,
        filesystem_scope="repo_metadata_only",
        github=True,
    ),
    "github.worktree.status": _contract(
        "github.worktree.status",
        "Read Worktree Status",
        "Read branch and worktree metadata with fixed read-only git argv.",
        category="github_worktree",
        risk_level="low",
        approval_required="none",
        timeout_seconds=10,
        filesystem_scope="repo_metadata_only",
        github=True,
    ),
    "github.changed_files.list": _contract(
        "github.changed_files.list",
        "List Changed Files",
        "List changed file paths from git status without patch bodies.",
        category="github_worktree",
        risk_level="low",
        approval_required="none",
        timeout_seconds=10,
        filesystem_scope="repo_metadata_only",
        github=True,
        output_redaction="secret_like_paths_redacted",
    ),
    "github.diff.summary": _contract(
        "github.diff.summary",
        "Read Diff Summary",
        "Read git diff stat and diff check output without full patch bodies.",
        category="github_worktree",
        risk_level="low",
        approval_required="none",
        timeout_seconds=10,
        filesystem_scope="repo_metadata_only",
        github=True,
    ),
    "github.branch.prepare": _contract(
        "github.branch.prepare",
        "Prepare Branch Name",
        "Prepare a safe local branch name without creating it.",
        category="github_worktree",
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        filesystem_scope="none",
        github=True,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"title": {"type": "string"}, "prefix": {"type": "string"}},
            "additionalProperties": False,
        },
    ),
    "github.pr.prepare_description": _contract(
        "github.pr.prepare_description",
        "Prepare PR Description",
        "Prepare a local PR description draft without calling GitHub or opening a PR.",
        category="github_worktree",
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        filesystem_scope="none",
        github=True,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"title": {"type": "string"}, "summary": {"type": "string"}, "tests": {"type": "array", "items": {"type": "string"}}},
            "additionalProperties": False,
        },
        output_redaction="secret_scan_before_return",
    ),
    "github.branch.create_local": _contract(
        "github.branch.create_local",
        "Create Local Branch Readiness",
        "Dry-run local branch creation. Actual branch mutation is disabled in this PR workflow.",
        category="github_worktree",
        risk_level="medium",
        approval_required="normal",
        timeout_seconds=10,
        filesystem_scope="git_refs",
        github=True,
        dry_run_available=True,
        rollback_supported=False,
        rollback_status="not_available_dry_run_only",
        default_enabled=False,
        default_disabled_reason="current PR workflow forbids git mutation by the agent",
        voice_approval_eligible=False,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"branch": {"type": "string", "minLength": 1}},
            "required": ["branch"],
            "additionalProperties": False,
        },
    ),
    "browser.url.open_plan": _contract(
        "browser.url.open_plan",
        "Open URL Plan",
        "Prepare a visible browser open-URL plan without launching a hidden browser.",
        category="browser",
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        browser=True,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"url": {"type": "string", "minLength": 1}},
            "required": ["url"],
            "additionalProperties": False,
        },
        execution_backend="browser_readiness_plan_only",
        voice_approval_eligible=False,
    ),
    "browser.screenshot.plan": _contract(
        "browser.screenshot.plan",
        "Screenshot Plan",
        "Prepare evidence capture metadata for a future visible Playwright run.",
        category="browser",
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        browser=True,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}, "selector": {"type": "string"}},
            "required": ["url"],
            "additionalProperties": False,
        },
        execution_backend="browser_readiness_plan_only",
        voice_approval_eligible=False,
    ),
    "browser.form.fill_dry_run": _contract(
        "browser.form.fill_dry_run",
        "Fill Form Dry Run",
        "Create a form-fill dry run plan without entering credentials or submitting.",
        category="browser",
        risk_level="medium",
        approval_required="normal",
        timeout_seconds=5,
        browser=True,
        dry_run_available=True,
        execution_backend="browser_readiness_plan_only",
        voice_approval_eligible=False,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}, "fields": {"type": "object"}},
            "required": ["url", "fields"],
            "additionalProperties": False,
        },
    ),
    "browser.click.submit_plan": _contract(
        "browser.click.submit_plan",
        "Click Submit Plan",
        "Plan a click/submit action; external side effects remain approval-gated and not executed.",
        category="browser",
        risk_level="high",
        approval_required="strong",
        timeout_seconds=5,
        browser=True,
        dry_run_available=True,
        side_effects=["possible_external_browser_side_effect_if_future_executor_enabled"],
        rollback_supported=False,
        rollback_plan="no_rollback_for_external_browser_submit; execution remains plan_only",
        rollback_status="not_available_plan_only",
        execution_backend="browser_readiness_plan_only",
        voice_approval_eligible=False,
        allowed_inputs_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}, "selector": {"type": "string"}, "intent": {"type": "string"}},
            "required": ["url", "selector"],
            "additionalProperties": False,
        },
    ),
    "sandbox.command.plan": _contract(
        "sandbox.command.plan",
        "Sandbox Command Plan",
        "Classify an allowlisted command ID without executing shell text.",
        category="sandbox",
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        sandbox=True,
        execution_backend="phase_7_guarded_command_planner",
        allowed_inputs_schema={
            "type": "object",
            "properties": {"command_id": {"type": "string"}, "path": {"type": "string"}, "target": {"type": "string"}},
            "required": ["command_id"],
            "additionalProperties": False,
        },
    ),
    "sandbox.command.dry_run": _contract(
        "sandbox.command.dry_run",
        "Sandbox Command Dry Run",
        "Dry-run an allowlisted command ID with working directory and secret preflight checks.",
        category="sandbox",
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        sandbox=True,
        execution_backend="phase_7_guarded_command_planner",
        allowed_inputs_schema={
            "type": "object",
            "properties": {"command_id": {"type": "string"}, "path": {"type": "string"}, "target": {"type": "string"}},
            "required": ["command_id"],
            "additionalProperties": False,
        },
    ),
    "sandbox.command.run_allowlisted": _contract(
        "sandbox.command.run_allowlisted",
        "Run Allowlisted Local Command",
        "Run one command ID from a fixed allowlist with no shell and redacted environment/output.",
        category="sandbox",
        risk_level="medium",
        approval_required="normal",
        timeout_seconds=120,
        sandbox=True,
        side_effects=["local_process_execution", "possible_pycache_or_pytest_tmp_files"],
        rollback_supported=False,
        rollback_plan="no general rollback; command output is redacted and execution is limited to safe command IDs",
        rollback_status="not_available_for_process_execution",
        rollback_limitations=["This is a guarded local runner, not an OS-level sandbox such as bubblewrap/nsjail."],
        execution_backend="phase_7_guarded_local_command_runner_not_os_sandbox",
        allowed_inputs_schema={
            "type": "object",
            "properties": {"command_id": {"type": "string"}, "path": {"type": "string"}, "target": {"type": "string"}},
            "required": ["command_id"],
            "additionalProperties": False,
        },
        audit_event_types=["preview_created", "preflight_completed", "approval_requested", "approval_approved", "dispatch_started", "dispatch_completed"],
        output_redaction="stdout_stderr_secret_redaction_and_truncation",
    ),
    "preflight.scan": _contract(
        "preflight.scan",
        "Secret Preflight Scan",
        "Scan proposed action inputs for secrets, production/payment markers and destructive operations.",
        category="preflight",
        risk_level="low",
        approval_required="none",
        timeout_seconds=5,
        filesystem_scope="input_metadata_only",
        allowed_inputs_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}, "path": {"type": "string"}, "action_key": {"type": "string"}},
            "additionalProperties": False,
        },
        output_redaction="findings_only_with_redacted_samples",
    ),
}


ACTION_CATALOG.update({key: value for key, value in PHASE7_ACTION_CATALOG.items() if key not in ACTION_CATALOG})


class Phase7GovernedActionsControlPlane(Phase5LocalControllerTrustedIdentityVoiceApprovalControlPlane):
    """Phase 7 governed action pilot.

    JARVIS still owns classification, approval, preflight, audit, stop and
    rollback contracts. Hermes remains the existing execution engine for its
    already-governed read bridge; Phase 7 adds local adapters only for narrowly
    allowlisted actions.
    """

    def status(self) -> Dict[str, Any]:
        base = super().status()
        base["schema_version"] = PHASE_7_SCHEMA_VERSION
        base["phase"] = "Phase 7"
        base["state"].update({
            "mode": "phase_7_governed_actions_control_plane",
            "phase_7_governed_actions": True,
            "action_catalog_v2": True,
            "safe_filesystem_actions": True,
            "safe_github_worktree_actions": True,
            "browser_automation_readiness": True,
            "guarded_sandbox_command_runner": True,
            "preflight_secret_scan": True,
            "generic_execute_route": False,
            "shell_freeform_allowed": False,
            "frontend_direct_hermes_allowed": False,
            "supported_real_dispatch": "safe_filesystem_read_list_write_with_backup_readonly_git_helpers_and_guarded_allowlisted_command_ids",
        })
        base["phase_7_status"] = self.phase_7_status(route_paths=())
        base["filesystem_adapter"] = self.filesystem_adapter_status()
        base["github_worktree_adapter"] = self.github_worktree_adapter_status()
        base["browser_automation"] = self.browser_automation_status()
        base["sandbox_execution"] = self.sandbox_execution_status()
        base["preflight"] = self.preflight_status()
        base["recent_previews"] = [
            _public_phase7_preview(item) if isinstance(item, Mapping) else item
            for item in base.get("recent_previews", [])
        ]
        base["safety"].update({
            "phase_7_action_catalog_v2": True,
            "safe_filesystem_allowed_roots_only": True,
            "filesystem_backup_before_overwrite": True,
            "github_commit_push_pr_merge_unapproved": False,
            "browser_plan_only_no_hidden_browser": True,
            "sandbox_no_freeform_shell": True,
            "secret_preflight_blocks": True,
            "voice_approval_reuses_phase_5_trust_gates": True,
        })
        return base

    def phase_7_status(self, *, route_paths: Iterable[str] = ()) -> Dict[str, Any]:
        routes = set(route_paths)
        return {
            "schema_version": PHASE_7_SCHEMA_VERSION,
            "phase": "Phase 7",
            "title": "PR #172 -- Governed Actions, Browser, Filesystem, GitHub & Sandbox",
            "status": "implemented_as_governed_local_action_pilot",
            "implemented_blocks": {
                "governed_action_catalog_v2": True,
                "filesystem_action_adapter_v1": True,
                "github_worktree_action_adapter_v1": True,
                "browser_automation_adapter_v1_readiness": True,
                "sandbox_execution_v1_guarded_runner": True,
                "secret_scanning_preflight_v1": True,
                "stop_rollback_contracts": True,
                "voice_approval_integration": True,
                "dashboard_event_stream_visibility": True,
            },
            "route_readiness": {
                "phase_7_status": "/mark-3/phase-7/status" in routes,
                "action_catalog": "/mark-3/execution/action-catalog" in routes,
                "execution_preview": "/mark-3/execution/preview" in routes,
                "generic_execute_absent": "/execute" not in routes and "/jarvis/execute" not in routes,
            },
            "real_vs_readiness": {
                "real": [
                    "catalog classification and backend action matching",
                    "safe filesystem read/list/write with backup-before-overwrite",
                    "read-only git status/worktree/changed-files/diff-summary helpers",
                    "branch and PR description preparation without GitHub API calls",
                    "secret/preflight scanner with redaction",
                    "guarded command IDs with no shell and sanitized env",
                    "Phase 5 spoken approval gates for eligible normal/strong actions",
                ],
                "readiness": [
                    "browser automation is plan/dry-run metadata only until a visible Playwright runner is explicitly wired",
                    "local branch/worktree creation remains disabled in this PR workflow",
                    "sandbox runner is guarded subprocess execution, not an OS-level sandbox",
                    "delete remains dry-run-only",
                ],
            },
            "adapters": {
                "filesystem": self.filesystem_adapter_status(),
                "github_worktree": self.github_worktree_adapter_status(),
                "browser": self.browser_automation_status(),
                "sandbox": self.sandbox_execution_status(),
                "preflight": self.preflight_status(),
            },
            "security_gates": {
                "jarvis_governs": True,
                "hermes_executes": True,
                "no_duplicate_hermes_runtime": True,
                "frontend_can_execute_hermes_directly": False,
                "no_execute_endpoint": True,
                "no_shell_freeform": True,
                "memory_grants_permission": False,
                "wake_phrase_can_approve": False,
                "voice_can_approve_only_when_trusted_governed": True,
                "critical_requires_strong_readback_rollback_audit": True,
            },
            "source_endpoint": "/mark-3/phase-7/status",
        }

    def action_catalog(self) -> Dict[str, Any]:
        catalog = super().action_catalog()
        actions = [self._phase7_action_dict(contract) for contract in ACTION_CATALOG.values()]
        categories: Dict[str, int] = {}
        for action in actions:
            categories[action.get("category", "unknown")] = categories.get(action.get("category", "unknown"), 0) + 1
        return {
            **catalog,
            "schema_version": ACTION_CATALOG_V2_SCHEMA_VERSION,
            "phase": "Phase 7",
            "catalog_version": 2,
            "allowlist_only": True,
            "freeform_shell_allowed": False,
            "arbitrary_command_allowed": False,
            "actions": actions,
            "categories": categories,
            "required_fields": [
                "action_id",
                "action_key",
                "title",
                "description",
                "category",
                "risk_level",
                "approval_required",
                "allowed_inputs_schema",
                "side_effects",
                "flags",
                "rollback_supported",
                "dry_run_available",
                "audit_requirements",
                "voice_approval_eligible",
                "default_state",
            ],
            "denied_actions": sorted(set(catalog.get("denied_actions", [])) | {
                "commit_unapproved",
                "push_unapproved",
                "pr_open_unapproved",
                "merge_unapproved",
                "browser_submit_without_strong_approval",
                "credential_entry",
                "purchase_payment",
                "hidden_browser",
                "hidden_filesystem_write",
                "shell_freeform",
            }),
            "source_endpoint": "/mark-3/execution/action-catalog",
        }

    def filesystem_adapter_status(self) -> Dict[str, Any]:
        roots = [str(root) for root in self._allowed_roots()]
        return {
            "schema_version": PHASE_7_SCHEMA_VERSION,
            "adapter": "filesystem",
            "status": "real_safe_local_adapter",
            "allowed_roots": roots,
            "default_allowed_roots_explicit": True,
            "home_wide_access": False,
            "path_traversal_allowed": False,
            "secret_paths_blocked": True,
            "safe_read": True,
            "safe_list": True,
            "write_requires_approval": True,
            "backup_before_overwrite": True,
            "delete_enabled": False,
            "delete_dry_run_only": True,
            "rollback": "backup_restore_manual_contract_for_overwrite",
            "metadata_only_audit": True,
        }

    def github_worktree_adapter_status(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_7_SCHEMA_VERSION,
            "adapter": "github_worktree",
            "status": "real_read_only_git_helpers_and_prepare_only_mutations",
            "network_calls": False,
            "github_api_called": False,
            "read_only_commands": ["git status --short --branch", "git worktree list --porcelain", "git diff --stat", "git diff --check"],
            "prepare_only": ["branch name", "PR description", "local branch creation dry-run"],
            "commit_enabled": False,
            "push_enabled": False,
            "open_pr_enabled": False,
            "merge_enabled": False,
            "worktree_mutation_enabled": False,
            "approval_required_for_future_mutation": "strong/double/triple depending risk",
        }

    def browser_automation_status(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_7_SCHEMA_VERSION,
            "adapter": "browser",
            "status": "readiness_and_plan_only",
            "playwright_contract": "compatible_plan_metadata",
            "playwright_runtime_connected": False,
            "hidden_browser_allowed": False,
            "credential_entry_allowed": False,
            "purchase_payment_allowed": False,
            "posting_publishing_allowed": False,
            "click_submit_requires_strong_approval": True,
            "evidence_capture_metadata": True,
            "external_side_effects_execute": False,
        }

    def sandbox_execution_status(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_7_SCHEMA_VERSION,
            "adapter": "sandbox",
            "status": "guarded_local_command_runner_not_os_sandbox",
            "os_sandbox_available": False,
            "shell_freeform_allowed": False,
            "allowed_command_ids": sorted(SANDBOX_COMMANDS),
            "working_directory_allowlist": [str(root) for root in self._allowed_roots()],
            "timeout_enforced": True,
            "environment_sanitized": True,
            "inherited_secrets": False,
            "stdout_stderr_redacted": True,
            "rollback_preview": "honest_no_general_process_rollback",
        }

    def preflight_status(self) -> Dict[str, Any]:
        return {
            "schema_version": PHASE_7_SCHEMA_VERSION,
            "adapter": "preflight",
            "status": "enabled",
            "detects": [
                ".env and secret-like paths",
                "API keys and tokens",
                "private keys",
                "password assignments",
                "Stripe live keys and payment markers",
                "production/deploy markers",
                "destructive commands",
            ],
            "redaction": True,
            "blocking": True,
            "approval_recommendation": True,
            "audit_preview": True,
        }

    def browser_verification_status(self, *, route_paths: Iterable[str]) -> Dict[str, Any]:
        base = super().browser_verification_status(route_paths=route_paths)
        checks = list(base.get("checks", []))
        checks.extend([
            _phase7_check("browser_plan_only", True, "Browser adapter emits plans/metadata only; no hidden browser is launched."),
            _phase7_check("no_credential_entry", True, "Credential entry and storage are blocked by preflight and browser policy."),
            _phase7_check("click_submit_gated", True, "Click/submit is a strong-approval plan only in Phase 7."),
        ])
        base.update({
            "schema_version": PHASE_7_SCHEMA_VERSION,
            "phase_7_browser_automation": self.browser_automation_status(),
            "checks": checks,
            "all_static_checks_passed": all(item.get("passed") for item in checks),
        })
        return base

    def start_voice_approval_session(self, **kwargs: Any) -> Dict[str, Any]:
        approval_id = str(kwargs.get("approval_id") or "")
        with self._lock:
            envelope = self._approval_envelopes.get(approval_id)
            action_key = str((envelope or {}).get("action_key") or "")
        contract = ACTION_CATALOG.get(action_key)
        if contract is not None:
            voice_allowed = self._phase7_action_dict(contract)["voice_approval_eligible"]
            if not voice_allowed:
                raise ValueError("action is not eligible for voice approval")
        return super().start_voice_approval_session(**kwargs)

    def _validate_inputs(self, action_key: str, inputs: Mapping[str, Any]) -> Dict[str, Any]:
        if action_key not in PHASE7_ACTION_KEYS:
            return super()._validate_inputs(action_key, inputs)
        raw = dict(inputs or {})
        if action_key == "filesystem.file.read_text":
            return {"path": _required_text(raw, "path")}
        if action_key == "filesystem.directory.list":
            return {"path": _required_text(raw, "path"), "limit": _bounded_int(raw.get("limit"), default=50, low=1, high=200)}
        if action_key == "filesystem.file.write_safe":
            return {"path": _required_text(raw, "path"), "content": str(raw.get("content") if raw.get("content") is not None else "")}
        if action_key == "filesystem.file.delete_dry_run":
            return {"path": _required_text(raw, "path")}
        if action_key in {"github.branch.prepare", "github.pr.prepare_description"}:
            return _safe_public_inputs(raw)
        if action_key == "github.branch.create_local":
            return {"branch": _required_text(raw, "branch", limit=120)}
        if action_key.startswith("github."):
            if raw:
                raise ValueError("inputs are not supported for this action")
            return {}
        if action_key in {"browser.url.open_plan", "browser.screenshot.plan"}:
            return {"url": _required_url(raw.get("url")), "selector": _safe_text(raw.get("selector"), limit=120)}
        if action_key == "browser.form.fill_dry_run":
            fields = raw.get("fields")
            if not isinstance(fields, Mapping):
                raise ValueError("fields must be an object")
            return {"url": _required_url(raw.get("url")), "fields": _redacted_fields(fields)}
        if action_key == "browser.click.submit_plan":
            return {
                "url": _required_url(raw.get("url")),
                "selector": _required_text(raw, "selector", limit=160),
                "intent": _safe_text(raw.get("intent"), limit=160),
            }
        if action_key in {"sandbox.command.plan", "sandbox.command.dry_run", "sandbox.command.run_allowlisted"}:
            command_id = _required_text(raw, "command_id", limit=80)
            if command_id not in SANDBOX_COMMANDS:
                raise ValueError("command_id is not allowlisted")
            safe: Dict[str, Any] = {"command_id": command_id}
            if raw.get("path"):
                safe["path"] = _required_text(raw, "path", limit=500)
            if raw.get("target"):
                safe["target"] = _required_text(raw, "target", limit=500)
            return safe
        if action_key == "preflight.scan":
            return {
                "text": _safe_text(raw.get("text"), limit=10000),
                "path": _safe_text(raw.get("path"), limit=500),
                "action_key": _safe_text(raw.get("action_key"), limit=120),
            }
        raise ValueError("action_key is not allowlisted")

    def _phase2_action_preview(
        self,
        *,
        intent: str,
        source: str,
        operator: str,
        session_id: Optional[str],
        action_key: str,
        inputs: Dict[str, Any],
        transcript_confidence: float,
    ) -> Dict[str, Any]:
        preview = super()._phase2_action_preview(
            intent=intent,
            source=source,
            operator=operator,
            session_id=session_id,
            action_key=action_key,
            inputs=inputs,
            transcript_confidence=transcript_confidence,
        )
        if action_key not in PHASE7_ACTION_KEYS:
            return preview
        enriched = self._enrich_phase7_preview(preview, action_key=action_key, inputs=inputs, intent=intent)
        with self._lock:
            stored = self._previews.get(enriched["preview_id"])
            if stored is not None:
                stored.update(enriched)
        return _public_phase7_preview(enriched)

    def _execute_local_action(self, action_key: str, preview: Mapping[str, Any]) -> Dict[str, Any]:
        if action_key not in PHASE7_ACTION_KEYS:
            return super()._execute_local_action(action_key, preview)
        inputs = dict(preview.get("_phase7_private_inputs") or preview.get("inputs") or {})
        preflight = self._preflight(action_key=action_key, inputs=inputs, intent=(preview.get("action") or {}).get("summary", ""))
        if preflight["blocking"] and action_key != "preflight.scan":
            raise ValueError(preflight["blocking_reason"])
        if action_key == "filesystem.file.read_text":
            path, _root = self._resolve_allowed_path(inputs["path"], must_exist=True, directory=False)
            return _completed("Safe text file read.", {"file": self._read_safe_text(path), "path_fingerprint": _fingerprint(str(path))})
        if action_key == "filesystem.directory.list":
            path, _root = self._resolve_allowed_path(inputs["path"], must_exist=True, directory=True)
            return _completed("Safe directory metadata listed.", {"directory": self._list_directory(path, limit=int(inputs.get("limit") or 50)), "path_fingerprint": _fingerprint(str(path))})
        if action_key == "filesystem.file.write_safe":
            return self._write_safe_file(preview, inputs)
        if action_key == "filesystem.file.delete_dry_run":
            path, _root = self._resolve_allowed_path(inputs["path"], must_exist=True, directory=False)
            return _completed("Delete dry run completed; no file was deleted.", {"would_delete": True, "did_delete": False, "path_fingerprint": _fingerprint(str(path)), "rollback_status": "not_available_dry_run_only"})
        if action_key == "github.repo.status":
            return _completed("Repo status read.", {"git_status": self._run_guarded(["git", "status", "--short", "--branch"], timeout=10)})
        if action_key == "github.worktree.status":
            return _completed("Worktree status read.", {
                "branch": self._run_guarded(["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=10),
                "worktrees": self._run_guarded(["git", "worktree", "list", "--porcelain"], timeout=10),
            })
        if action_key == "github.changed_files.list":
            changed = self._run_guarded(["git", "status", "--porcelain"], timeout=10)
            return _completed("Changed files listed.", {"changed_files": _redacted_lines(changed.get("summary", "")), "exit_code": changed["exit_code"]})
        if action_key == "github.diff.summary":
            return _completed("Diff summary read.", {
                "diff_stat": self._run_guarded(["git", "diff", "--stat"], timeout=10),
                "diff_check": self._run_guarded(["git", "diff", "--check"], timeout=10),
            })
        if action_key == "github.branch.prepare":
            return _completed("Branch name prepared.", {"branch": _prepare_branch_name(inputs.get("title") or "phase-7-work", prefix=inputs.get("prefix") or "jarvis")})
        if action_key == "github.pr.prepare_description":
            return _completed("PR description prepared.", {"description": _prepare_pr_description(inputs)})
        if action_key == "github.branch.create_local":
            branch = _prepare_branch_name(inputs.get("branch") or "phase-7-work", prefix="")
            return _completed("Local branch creation is dry-run only in this PR workflow.", {"branch": branch, "would_create_branch": True, "did_create_branch": False, "reason": "git mutation disabled for Phase 7 current workflow"})
        if action_key.startswith("browser."):
            return _completed("Browser automation plan prepared; no browser launched.", self._browser_plan(action_key, inputs))
        if action_key in {"sandbox.command.plan", "sandbox.command.dry_run"}:
            return _completed("Sandbox command dry-run completed.", self._sandbox_plan(inputs, execute=False))
        if action_key == "sandbox.command.run_allowlisted":
            return self._run_sandbox_command(inputs)
        if action_key == "preflight.scan":
            return _completed("Preflight scan completed.", self._preflight(action_key=str(inputs.get("action_key") or "preflight.scan"), inputs=inputs, intent=str(inputs.get("text") or "")))
        raise ValueError(f"Unsupported action key: {action_key}")

    def _enrich_phase7_preview(self, preview: Dict[str, Any], *, action_key: str, inputs: Dict[str, Any], intent: str) -> Dict[str, Any]:
        contract = ACTION_CATALOG[action_key]
        preflight = self._preflight(action_key=action_key, inputs=inputs, intent=intent)
        path_error = self._preview_path_error(action_key, inputs)
        if path_error:
            preflight = dict(preflight)
            findings = list(preflight.get("findings", []))
            findings.append(_finding("filesystem_scope", "critical", "blocked", path_error, str(inputs.get("path") or "")))
            preflight.update({
                "status": "blocked",
                "blocking": True,
                "blocking_reason": "preflight_blocked:filesystem_scope",
                "findings": findings,
                "finding_count": len(findings),
                "max_severity": "critical",
                "approval_recommendation": "block",
            })
        action = dict(preview.get("action") or {})
        action.update({
            "title": contract.title or action_key,
            "category": contract.category,
            "side_effects": list(contract.side_effects),
            "flags": contract.to_dict()["flags"],
            "dry_run_available": contract.dry_run_available,
            "voice_approval_eligible": self._phase7_action_dict(contract)["voice_approval_eligible"],
            "default_enabled": contract.default_enabled,
            "default_disabled_reason": contract.default_disabled_reason,
            "preflight": _public_preflight(preflight),
            "rollback_supported": contract.rollback_supported,
            "rollback_status": contract.rollback_status,
            "rollback_plan": contract.rollback_plan,
        })
        preview = dict(preview)
        preview["schema_version"] = PHASE_7_SCHEMA_VERSION
        preview["phase"] = "Phase 7"
        preview["_phase7_private_inputs"] = dict(inputs)
        preview["inputs"] = _phase7_public_inputs(action_key, inputs)
        preview["preflight"] = _public_preflight(preflight)
        preview["real_vs_readiness"] = _action_real_vs_readiness(action_key)
        preview["preview"] = dict(preview.get("preview") or {})
        preview["preview"]["preflight"] = _public_preflight(preflight)
        preview["preview"]["stop_rollback_contract"] = contract.to_dict()["contract"]
        preview["preview"]["side_effects"] = list(contract.side_effects)
        if action_key == "filesystem.file.write_safe":
            preview["preview"]["diff_preview"] = self._diff_preview(inputs)
            preview["preview"]["backup_plan"] = "Create backup before overwrite in .jarvis/phase_7_backups; new file has no prior content to back up."
        if action_key == "filesystem.file.delete_dry_run":
            preview["decision"] = "requires_approval"
            preview["requires_approval"] = True
            preview["unsupported_reason"] = "delete_execution_disabled_dry_run_only"
            action["unsupported_reason"] = "delete_execution_disabled_dry_run_only"
        if not contract.default_enabled:
            preview["preview"]["default_disabled_reason"] = contract.default_disabled_reason
        if preflight["blocking"]:
            preview["decision"] = "denied"
            preview["state"] = "denied"
            preview["risk_level"] = "forbidden"
            preview["approval_level"] = "blocked"
            preview["approval_level_required"] = "blocked"
            preview["requires_approval"] = False
            preview["denied_reason"] = preflight["blocking_reason"]
            preview["protected_message"] = "No puedo hacer eso, David. Preflight bloqueó secretos, credenciales o una acción destructiva."
            action.update({
                "decision": "denied",
                "risk_level": "forbidden",
                "approval_level": "blocked",
                "approval_level_required": "blocked",
                "requires_approval": False,
                "denied_reason": preflight["blocking_reason"],
            })
        preview["action"] = action
        return preview

    def _preview_path_error(self, action_key: str, inputs: Mapping[str, Any]) -> str:
        try:
            if action_key in {"filesystem.file.read_text", "filesystem.file.delete_dry_run"}:
                self._resolve_allowed_path(inputs.get("path"), must_exist=True, directory=False)
            elif action_key == "filesystem.directory.list":
                self._resolve_allowed_path(inputs.get("path"), must_exist=True, directory=True)
            elif action_key == "filesystem.file.write_safe":
                self._resolve_allowed_path(inputs.get("path"), must_exist=False, directory=False)
            elif action_key == "sandbox.command.run_allowlisted" and inputs.get("path"):
                self._resolve_allowed_path(inputs.get("path"), must_exist=True, directory=False)
        except ValueError as exc:
            return str(exc)
        return ""

    def _phase7_action_dict(self, contract: ActionContract) -> Dict[str, Any]:
        data = contract.to_dict()
        if contract.action_key == "repo.file.read_safe":
            data["category"] = "filesystem"
            data["flags"]["filesystem"] = True
            data["voice_approval_eligible"] = True
        return data

    def _allowed_roots(self) -> List[Path]:
        raw = os.environ.get("JARVIS_PHASE7_ALLOWED_ROOTS", "")
        candidates = [self.cwd]
        for item in raw.split(os.pathsep):
            if item.strip():
                candidates.append(Path(item.strip()))
        roots: List[Path] = []
        for candidate in candidates:
            try:
                root = candidate.resolve()
            except (OSError, RuntimeError):
                continue
            if root.exists() and root.is_dir() and root not in roots:
                roots.append(root)
        return roots or [self.cwd]

    def _resolve_allowed_path(self, raw_path: Any, *, must_exist: bool, directory: bool) -> Tuple[Path, Path]:
        text = str(raw_path or "").strip()
        if not text:
            raise ValueError("path is required")
        if "\x00" in text or any(part == ".." for part in Path(text).parts):
            raise ValueError("path traversal is blocked")
        if text.startswith("~"):
            raise ValueError("home-wide paths are not allowed")
        if _path_is_secret_like(text):
            raise ValueError("secret or credential paths are denied")
        candidate = Path(text)
        if not candidate.is_absolute():
            candidate = self.cwd / candidate
        try:
            resolved = candidate.resolve()
        except (OSError, RuntimeError) as exc:
            raise ValueError(f"path cannot be resolved: {exc}") from exc
        roots = self._allowed_roots()
        root = next((item for item in roots if _is_relative_to(resolved, item)), None)
        if root is None:
            raise ValueError("path is outside allowed roots")
        if _path_is_secret_like(str(resolved)):
            raise ValueError("secret or credential paths are denied")
        if must_exist and not resolved.exists():
            raise ValueError("path does not exist")
        if resolved.exists() and resolved.is_symlink():
            raise ValueError("symlink paths are blocked")
        if directory and resolved.exists() and not resolved.is_dir():
            raise ValueError("path must be a directory")
        if not directory and resolved.exists() and not resolved.is_file():
            raise ValueError("path must be a regular file")
        if not must_exist and not resolved.parent.exists():
            raise ValueError("parent directory must exist")
        if not must_exist and resolved.parent.is_symlink():
            raise ValueError("symlink parent paths are blocked")
        return resolved, root

    def _preflight(self, *, action_key: str, inputs: Mapping[str, Any], intent: str = "") -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []
        for key, value in dict(inputs or {}).items():
            text = str(value or "")
            lowered_key = str(key).casefold()
            if "path" in lowered_key and _secret_path_reason(text):
                findings.append(_finding("secret_path", "critical", "blocked", "Path points to secret-like material.", text))
            if lowered_key in {"content", "text", "summary", "intent", "branch", "target"} or isinstance(value, str):
                findings.extend(_scan_text(text))
        findings.extend(_scan_text(intent))
        joined = " ".join(str(value or "") for value in list(inputs.values()) + [intent]).casefold()
        if any(marker in joined for marker in DESTRUCTIVE_MARKERS):
            findings.append(_finding("destructive_operation", "critical", "blocked", "Destructive operation marker detected.", joined))
        if any(marker in joined for marker in PRODUCTION_MARKERS):
            findings.append(_finding("production_or_payment_marker", "medium", "requires_strong_approval", "Production/payment marker detected.", joined))
        blocking = any(item["blocking"] for item in findings)
        max_severity = _max_severity(findings)
        recommendation = "block" if blocking else ("strong_approval" if max_severity in {"medium", "high", "critical"} else "allow")
        audit = self._audit_v2(
            "preflight_completed",
            correlation_id=f"corr-{uuid4()}",
            surface="preflight",
            risk_level="forbidden" if blocking else max_severity,
            approval_level="blocked" if blocking else ("strong" if recommendation == "strong_approval" else "none"),
            metadata={
                "action_key": action_key,
                "finding_count": len(findings),
                "blocking": blocking,
                "approval_recommendation": recommendation,
            },
        )
        return {
            "schema_version": PHASE_7_SCHEMA_VERSION,
            "status": "blocked" if blocking else "passed",
            "blocking": blocking,
            "blocking_reason": _blocking_reason(findings),
            "findings": findings[:20],
            "finding_count": len(findings),
            "max_severity": max_severity,
            "approval_recommendation": recommendation,
            "redaction_applied": True,
            "audit_id": audit.get("audit_id", ""),
            "metadata_only": True,
        }

    def _read_safe_text(self, path: Path) -> Dict[str, Any]:
        data = path.read_bytes()
        if len(data) > 256_000:
            raise ValueError("file is too large for safe text read")
        if b"\x00" in data:
            raise ValueError("binary files are blocked")
        text = data.decode("utf-8")
        preflight = self._preflight(action_key="filesystem.file.read_text", inputs={"content": text, "path": str(path)}, intent="")
        if preflight["blocking"]:
            raise ValueError(preflight["blocking_reason"])
        return {
            "name": path.name,
            "bytes": len(data),
            "sha256": _fingerprint(text),
            "content": text[:20_000],
            "truncated": len(text) > 20_000,
        }

    def _list_directory(self, path: Path, *, limit: int) -> Dict[str, Any]:
        items = []
        for child in sorted(path.iterdir(), key=lambda item: item.name.casefold())[:limit]:
            if _path_is_secret_like(str(child)):
                items.append({"name": "[redacted-secret-like-path]", "kind": "redacted", "secret_like": True})
                continue
            kind = "directory" if child.is_dir() else "file" if child.is_file() else "other"
            items.append({
                "name": child.name,
                "kind": kind,
                "bytes": child.stat().st_size if child.is_file() else None,
                "secret_like": False,
            })
        return {"path_fingerprint": _fingerprint(str(path)), "item_count": len(items), "items": items}

    def _diff_preview(self, inputs: Mapping[str, Any]) -> Dict[str, Any]:
        path, _root = self._resolve_allowed_path(inputs.get("path"), must_exist=False, directory=False)
        new_text = str(inputs.get("content") or "")
        old_text = ""
        existed = path.exists()
        if existed:
            old_text = self._read_safe_text(path)["content"]
        diff_lines = list(difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile=f"a/{path.name}",
            tofile=f"b/{path.name}",
            lineterm="",
        ))
        redacted = [_redact_text(line, limit=500) for line in diff_lines[:120]]
        return {
            "path_fingerprint": _fingerprint(str(path)),
            "existed": existed,
            "line_count": len(diff_lines),
            "truncated": len(diff_lines) > 120,
            "diff": "\n".join(redacted),
            "content_stored_in_audit": False,
        }

    def _write_safe_file(self, preview: Mapping[str, Any], inputs: Mapping[str, Any]) -> Dict[str, Any]:
        path, root = self._resolve_allowed_path(inputs.get("path"), must_exist=False, directory=False)
        content = str(inputs.get("content") or "")
        content_scan = self._preflight(action_key="filesystem.file.write_safe", inputs={"path": str(path), "content": content}, intent="")
        if content_scan["blocking"]:
            raise ValueError(content_scan["blocking_reason"])
        backup_path = ""
        if path.exists():
            backup_dir = root / PHASE7_BACKUP_DIR
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_name = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{_fingerprint(str(path))[-12:]}-{path.name}.bak"
            backup = backup_dir / backup_name
            shutil.copy2(path, backup)
            backup_path = str(backup)
            self._audit_v2(
                "filesystem_backup_created",
                correlation_id=str(preview.get("correlation_id") or f"corr-{uuid4()}"),
                surface="filesystem",
                risk_level="medium",
                approval_level="normal",
                metadata={"path_fingerprint": _fingerprint(str(path)), "backup_fingerprint": _fingerprint(backup_path)},
            )
        path.write_text(content, encoding="utf-8")
        self._audit_v2(
            "filesystem_write_completed",
            correlation_id=str(preview.get("correlation_id") or f"corr-{uuid4()}"),
            surface="filesystem",
            risk_level="medium",
            approval_level="normal",
            metadata={"path_fingerprint": _fingerprint(str(path)), "backup_created": bool(backup_path), "bytes": len(content.encode("utf-8"))},
        )
        return _completed("Safe file write completed with governed backup contract.", {
            "path_fingerprint": _fingerprint(str(path)),
            "bytes_written": len(content.encode("utf-8")),
            "backup_created": bool(backup_path),
            "backup_path_fingerprint": _fingerprint(backup_path) if backup_path else "",
            "rollback_status": "backup_available" if backup_path else "created_file_no_prior_backup",
            "content_returned": False,
        })

    def _run_guarded(self, argv: List[str], *, timeout: int) -> Dict[str, Any]:
        result = subprocess.run(
            argv,
            cwd=str(self.cwd),
            env=_sanitized_env(self.cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        output = "\n".join(item for item in (result.stdout, result.stderr) if item)
        return {
            "argv_id": _argv_id(argv),
            "exit_code": result.returncode,
            "summary": _redact_output(output),
            "line_count": len(output.splitlines()),
            "output_truncated": len(output) > 1600,
        }

    def _browser_plan(self, action_key: str, inputs: Mapping[str, Any]) -> Dict[str, Any]:
        url = str(inputs.get("url") or "")
        parsed = urlparse(url)
        return {
            "action_key": action_key,
            "url_origin": f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else "invalid",
            "url_fingerprint": _fingerprint(url),
            "selector_fingerprint": _fingerprint(inputs.get("selector", "")) if inputs.get("selector") else "",
            "visible_browser_required": True,
            "hidden_browser_allowed": False,
            "credentials_allowed": False,
            "submit_or_click_executes": False,
            "evidence_capture_metadata": True,
            "playwright_runtime_connected": False,
            "readiness_only": True,
        }

    def _sandbox_plan(self, inputs: Mapping[str, Any], *, execute: bool) -> Dict[str, Any]:
        command_id = str(inputs.get("command_id") or "")
        spec = SANDBOX_COMMANDS[command_id]
        argv = list(spec["argv"])
        target = str(inputs.get("target") or "")
        path = str(inputs.get("path") or "")
        if spec.get("path_arg"):
            resolved, _root = self._resolve_allowed_path(path, must_exist=True, directory=False)
            if resolved.suffix != ".py":
                raise ValueError("python_py_compile requires a .py file")
            argv.append(str(resolved))
        if spec.get("target_arg"):
            if target not in spec.get("allowed_targets", []):
                raise ValueError("pytest target is not allowlisted")
            argv.extend([target, "-q", "-x"])
        return {
            "command_id": command_id,
            "argv_id": _argv_id(argv),
            "description": spec["description"],
            "risk_level": spec["risk_level"],
            "read_only": bool(spec["read_only"]),
            "timeout_seconds": int(spec["timeout_seconds"]),
            "working_directory_fingerprint": _fingerprint(str(self.cwd)),
            "allowed_working_directory": any(_is_relative_to(self.cwd, root) for root in self._allowed_roots()),
            "shell": False,
            "environment_sanitized": True,
            "inherited_secrets": False,
            "would_execute": execute,
            "os_sandbox_available": False,
            "guarded_runner": True,
            "rollback_preview": "no general rollback for local process execution",
        }

    def _run_sandbox_command(self, inputs: Mapping[str, Any]) -> Dict[str, Any]:
        plan = self._sandbox_plan(inputs, execute=True)
        if not plan["allowed_working_directory"]:
            raise ValueError("working directory is outside allowed roots")
        command_id = str(inputs["command_id"])
        spec = SANDBOX_COMMANDS[command_id]
        argv = list(spec["argv"])
        if spec.get("path_arg"):
            resolved, _root = self._resolve_allowed_path(inputs.get("path"), must_exist=True, directory=False)
            argv.append(str(resolved))
        if spec.get("target_arg"):
            target = str(inputs.get("target") or "")
            argv.extend([target, "-q", "-x"])
        started = time.monotonic()
        result = self._run_guarded(argv, timeout=int(spec["timeout_seconds"]))
        result["duration_ms"] = int((time.monotonic() - started) * 1000)
        return {
            "status": "completed" if result["exit_code"] == 0 else "failed",
            "result_summary": "Allowlisted command completed." if result["exit_code"] == 0 else "Allowlisted command failed.",
            "error_summary": "" if result["exit_code"] == 0 else result["summary"],
            "data": {"plan": plan, "result": result},
        }


def _phase7_check(name: str, passed: bool, notes: str) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "status": "passed" if passed else "missing", "notes": notes}


def _public_preflight(preflight: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "schema_version": preflight.get("schema_version", PHASE_7_SCHEMA_VERSION),
        "status": preflight.get("status", "unknown"),
        "blocking": bool(preflight.get("blocking", False)),
        "blocking_reason": preflight.get("blocking_reason", ""),
        "finding_count": preflight.get("finding_count", 0),
        "max_severity": preflight.get("max_severity", "none"),
        "approval_recommendation": preflight.get("approval_recommendation", "allow"),
        "findings": list(preflight.get("findings", []) or [])[:10],
        "redaction_applied": True,
        "metadata_only": True,
    }


def _public_phase7_preview(preview: Mapping[str, Any]) -> Dict[str, Any]:
    public = dict(preview)
    public.pop("_phase7_private_inputs", None)
    return public


def _phase7_public_inputs(action_key: str, inputs: Mapping[str, Any]) -> Dict[str, Any]:
    if action_key == "filesystem.file.write_safe":
        content = str(inputs.get("content") or "")
        return {
            "path": {"sha256": _fingerprint(inputs.get("path", ""))},
            "content": {"sha256": _fingerprint(content), "bytes": len(content.encode("utf-8")), "omitted": True},
        }
    if action_key == "preflight.scan":
        text = str(inputs.get("text") or "")
        return {
            "text": {"sha256": _fingerprint(text), "bytes": len(text.encode("utf-8")), "omitted": True},
            "path": {"sha256": _fingerprint(inputs.get("path", ""))} if inputs.get("path") else "",
            "action_key": _safe_text(inputs.get("action_key"), limit=120),
        }
    if action_key.startswith("browser.") and "fields" in inputs:
        return {"url": {"sha256": _fingerprint(inputs.get("url", ""))}, "fields": _redacted_fields(dict(inputs.get("fields") or {}))}
    return _safe_inputs_for_public(inputs)


def _action_real_vs_readiness(action_key: str) -> Dict[str, str]:
    if action_key.startswith("browser."):
        return {"status": "readiness", "reason": "Browser actions return Playwright-compatible plans only; no hidden browser is launched."}
    if action_key in {"github.branch.create_local", "filesystem.file.delete_dry_run"}:
        return {"status": "readiness", "reason": "Mutation is disabled/dry-run-only in this PR workflow."}
    if action_key == "sandbox.command.run_allowlisted":
        return {"status": "real_guarded_runner", "reason": "Executes fixed argv without shell, but is not an OS-level sandbox."}
    return {"status": "real", "reason": "Implemented as a local governed adapter action."}


def _required_text(values: Mapping[str, Any], key: str, *, limit: int = 500) -> str:
    text = _safe_text(values.get(key), limit=limit)
    if not text:
        raise ValueError(f"{key} is required")
    return text


def _bounded_int(value: Any, *, default: int, low: int, high: int) -> int:
    try:
        number = int(value if value is not None else default)
    except (TypeError, ValueError):
        raise ValueError("value must be an integer") from None
    return max(low, min(number, high))


def _required_url(value: Any) -> str:
    text = _safe_text(value, limit=1200)
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url must be http or https")
    return text


def _safe_public_inputs(raw: Mapping[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in dict(raw or {}).items():
        if isinstance(value, list):
            safe[str(key)] = [_safe_text(item, limit=160) for item in value[:20]]
        elif isinstance(value, Mapping):
            safe[str(key)] = _redacted_fields(value)
        else:
            safe[str(key)] = _safe_text(value, limit=1000)
    return safe


def _redacted_fields(fields: Mapping[str, Any]) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in dict(fields or {}).items():
        field = _safe_text(key, limit=120)
        if _contains_sensitive_word(field) or _contains_sensitive_word(value):
            safe[field] = "[redacted]"
        else:
            safe[field] = _safe_text(value, limit=240)
    return safe


def _secret_path_reason(value: str) -> str:
    if not value:
        return ""
    name = Path(value).name.casefold()
    if name in SECRET_FILE_NAMES:
        return "secret file name"
    if _path_is_secret_like(value):
        return "secret path marker"
    return ""


def _scan_text(value: str) -> List[Dict[str, Any]]:
    text = str(value or "")
    if not text:
        return []
    findings: List[Dict[str, Any]] = []
    for finding_type, severity, pattern in SECRET_PATTERNS:
        match = re.search(pattern, text, re.I)
        if match:
            findings.append(_finding(finding_type, severity, "blocked", f"{finding_type} detected.", match.group(0)))
    return findings


def _finding(finding_type: str, severity: str, action: str, message: str, sample: str) -> Dict[str, Any]:
    return {
        "type": finding_type,
        "severity": severity,
        "action": action,
        "message": message,
        "redacted_sample": _redact_sample(sample),
        "blocking": action == "blocked" or severity == "critical",
    }


def _redact_sample(value: str) -> str:
    text = str(value or "").strip()
    if len(text) <= 6:
        return "[redacted]"
    return f"{text[:3]}...[redacted]...{text[-3:]}"


def _max_severity(findings: Iterable[Mapping[str, Any]]) -> str:
    order = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    current = "none"
    for item in findings:
        severity = str(item.get("severity") or "none")
        if order.get(severity, 0) > order[current]:
            current = severity
    return current


def _blocking_reason(findings: Iterable[Mapping[str, Any]]) -> str:
    blocking = [str(item.get("type") or "finding") for item in findings if item.get("blocking")]
    if not blocking:
        return ""
    return "preflight_blocked:" + ",".join(blocking[:5])


def _contains_sensitive_word(value: Any) -> bool:
    text = str(value or "").casefold()
    return any(marker in text for marker in ("password", "token", "secret", "credential", "cookie", "authorization", "api_key", "apikey", "private key"))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _redact_output(output: str) -> str:
    text = output[:1600]
    for _name, _severity, pattern in SECRET_PATTERNS:
        text = re.sub(pattern, "[redacted-secret]", text, flags=re.I)
    lines = []
    for line in text.splitlines():
        if _path_is_secret_like(line) or _contains_sensitive_word(line):
            lines.append("[redacted]")
        else:
            lines.append(line)
    rendered = "\n".join(lines)
    return rendered + (" [truncated]" if len(output) > 1600 else "")


def _redacted_lines(output: str) -> List[str]:
    lines = []
    for line in output.splitlines()[:200]:
        lines.append("[redacted-secret-like-path]" if _path_is_secret_like(line) else line[:300])
    return lines


def _sanitized_env(cwd: Path) -> Dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(cwd),
        "PYTHONPATH": str(cwd),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
    }


def _argv_id(argv: List[str]) -> str:
    return _fingerprint(" ".join(argv))


def _prepare_branch_name(title: Any, *, prefix: Any = "jarvis") -> str:
    raw = _safe_text(title, limit=120).casefold()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-") or "phase-7-work"
    safe_prefix = re.sub(r"[^a-z0-9._/-]+", "-", _safe_text(prefix, limit=40).casefold()).strip("/-")
    if safe_prefix:
        branch = f"{safe_prefix}/{slug}"
    else:
        branch = slug
    return branch[:80].strip("/-") or "jarvis/phase-7-work"


def _prepare_pr_description(inputs: Mapping[str, Any]) -> str:
    title = _safe_text(inputs.get("title"), limit=120) or "Phase 7 governed action update"
    summary = _redact_text(inputs.get("summary") or "Prepared by JARVIS; review before use.", limit=800)
    tests = inputs.get("tests") if isinstance(inputs.get("tests"), list) else []
    test_lines = "\n".join(f"- {_redact_text(item, limit=160)}" for item in tests[:12]) or "- Not run yet."
    return f"## Summary\n{summary}\n\n## Tests\n{test_lines}\n\n## Safety\n- No commit, push, PR creation, merge, deploy, payment, email, or publication was performed."
