from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.mark_2_external_operations_policy import safe_text


@dataclass(frozen=True)
class CodexCliAdapter:
    adapter_name: str = "Codex CLI"
    invocation_mode: str = "subscription_cli"
    logged_in_assumed: bool = False
    login_required_manual: bool = True
    stores_access_material: bool = False
    uses_cookies: bool = False
    automates_web_ui: bool = False
    command_preview: str = "codex task preview; no process will start"
    worktree_required: bool = True
    sandbox_required: bool = True
    allowed_commands: List[str] = field(default_factory=lambda: ["inspect", "edit in worktree", "run tests", "review diff"])
    forbidden_commands: List[str] = field(default_factory=lambda: ["commit", "push", "merge", "deploy"])
    task_summary: str = "No real task assigned."
    expected_outputs: List[str] = field(default_factory=lambda: ["diff", "tests", "review", "summary"])
    approval_required: bool = True
    strong_approval_required: bool = False
    would_invoke_real_cli: bool = False
    would_commit: bool = False
    would_push: bool = False
    would_merge: bool = False
    would_deploy: bool = False
    usage_limit_status: str = "manual_input_required"
    paid_by: str = "ChatGPT subscription"
    cost_mode: str = "subscription_limit"
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    cost_known: bool = False
    blocked_reasons: List[str] = field(default_factory=lambda: ["real Codex CLI invocation is disabled"])
    next_safe_step: str = "Manually confirm login, worktree, sandbox, task scope, usage limits, and approval."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def preview(cls, **values: Any) -> "CodexCliAdapter":
        sensitive = any(marker in str(values.get("task_summary") or "").lower() for marker in ("push", "merge", "deploy", "production"))
        return cls(
            invocation_mode=str(values.get("invocation_mode") or "subscription_cli"),
            command_preview=safe_text(values.get("command_preview"), cls.command_preview),
            task_summary=safe_text(values.get("task_summary"), "No real task assigned."),
            strong_approval_required=sensitive,
            blocked_reasons=["real Codex CLI invocation is disabled", "worktree and sandbox evidence required"],
        )
