from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AICodingSessionControl:
    session_id: str
    session_type: str
    status: str
    task_summary: str
    repo: str
    worktree: Optional[str]
    branch: Optional[str]
    command_preview: str
    model_or_tool: str
    provider: str
    paid_by: str
    cost_mode: str
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    usage_limit_status: str = "unknown"
    input_context_summary: str = "Operator-provided context only."
    diff_summary: str = "unknown; no session has run"
    tests_summary: str = "unknown; no session has run"
    review_summary: str = "unknown; no session has run"
    approval_state: str = "not_requested"
    merge_allowed: bool = False
    deploy_allowed: bool = False
    push_allowed: bool = False
    production_allowed: bool = False
    money_allowed: bool = False
    would_invoke_real_tool: bool = False
    next_safe_step: str = "Review the preview, worktree, scope, costs, and approval requirements."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_ai_coding_sessions() -> List[AICodingSessionControl]:
    specs = (
        ("codex-preview", "codex_cli", "CodexCliAdapter preview", "OpenAI", "ChatGPT subscription", "subscription_limit", "manual_input_required"),
        ("claude-code-preview", "claude_code", "ClaudeCodeCliAdapter preview", "Anthropic", "Claude subscription", "subscription_limit", "manual_input_required"),
        ("claude-cowork-preview", "claude_cowork", "ClaudeCoworkAdapter preview", "Anthropic", "Claude subscription", "subscription_limit", "manual_input_required"),
        ("api-fallback-preview", "api_fallback", "ApiFallbackAdapter preview", "unknown", "David API billing", "api_tokens", "unknown"),
        ("local-script-preview", "local_script", "LocalScriptAdapter planned", "local", "local machine", "local_compute", "unknown"),
    )
    return [
        AICodingSessionControl(
            session_id=session_id,
            session_type=session_type,
            status="planned",
            task_summary="No real task assigned; governed session preview only.",
            repo="ceodaradigu/hermes-agent",
            worktree=None,
            branch=None,
            command_preview=f"preview {session_type} session; no process will start",
            model_or_tool=tool,
            provider=provider,
            paid_by=paid_by,
            cost_mode=cost_mode,
            usage_limit_status=limit,
        )
        for session_id, session_type, tool, provider, paid_by, cost_mode, limit in specs
    ]

