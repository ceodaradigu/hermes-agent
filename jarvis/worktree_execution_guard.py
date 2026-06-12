from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class WorktreeExecutionGuardPanel:
    repo: str = "ceodaradigu/hermes-agent"
    main_branch: str = "main"
    worktree_path: Optional[str] = None
    branch: Optional[str] = None
    dirty_state: str = "unknown"
    untracked_files_count: Optional[int] = None
    last_commit: str = "unknown"
    pr_number: Optional[int] = None
    pr_state: str = "unknown"
    safe_to_continue: bool = False
    safe_to_finish_pr: bool = False
    blocked_reasons: List[str] = field(default_factory=lambda: ["worktree state was not provided or inspected"])
    required_commands_preview: List[str] = field(default_factory=lambda: ["git status --short", "git diff --check"])
    forbidden_actions: List[str] = field(default_factory=lambda: ["commit", "push", "merge", "deploy"])
    next_safe_step: str = "Provide or manually inspect worktree state before finishing the PR."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiffTestReviewPanel:
    diff_available: bool = False
    diff_summary: str = "unknown; no diff data provided"
    files_changed: Optional[int] = None
    tests_run: Optional[int] = None
    tests_passed: Optional[int] = None
    tests_failed: Optional[int] = None
    warnings_count: Optional[int] = None
    review_executed: bool = False
    review_result: str = "unknown"
    blocking_findings: List[str] = field(default_factory=lambda: ["review and test evidence not provided"])
    ready_for_finish_pr: bool = False
    known_hangs: List[str] = field(default_factory=list)
    next_safe_step: str = "Run tests and review outside this read-only dashboard snapshot."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

