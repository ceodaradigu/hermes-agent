from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.mark_2_external_operations_policy import safe_text


@dataclass(frozen=True)
class ClaudeCodeAdapter:
    adapter_name: str = "Claude Code"
    invocation_mode: str = "subscription_cli"
    manual_login_required: bool = True
    stores_access_material: bool = False
    uses_cookies: bool = False
    automates_web_ui: bool = False
    command_preview: str = "claude code task preview; no process will start"
    worktree_required: bool = True
    sandbox_required: bool = True
    expected_outputs: List[str] = field(default_factory=lambda: ["diff", "tests", "review", "summary"])
    approval_required: bool = True
    strong_approval_required: bool = False
    dangerous_hooks_allowed: bool = False
    external_mcp_tools_allowed: bool = False
    would_invoke_real_cli: bool = False
    would_commit: bool = False
    would_push: bool = False
    would_merge: bool = False
    would_deploy: bool = False
    usage_limit_status: str = "manual_input_required"
    paid_by: str = "Claude subscription"
    cost_mode: str = "subscription_limit"
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    cost_known: bool = False
    blocked_reasons: List[str] = field(default_factory=lambda: ["real Claude Code invocation is disabled"])
    next_safe_step: str = "Manually confirm login, worktree, sandbox, hooks, tools, usage limits, and approval."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def preview(cls, **values: Any) -> "ClaudeCodeAdapter":
        sensitive = any(marker in str(values.get("task_summary") or "").lower() for marker in ("push", "merge", "deploy", "production"))
        return cls(
            invocation_mode=str(values.get("invocation_mode") or "subscription_cli"),
            command_preview=safe_text(values.get("command_preview"), cls.command_preview),
            strong_approval_required=sensitive,
            blocked_reasons=["real Claude Code invocation is disabled", "dangerous hooks and external tools require separate approval"],
        )
