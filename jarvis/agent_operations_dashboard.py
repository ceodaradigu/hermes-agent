from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AgentOperation:
    agent_id: str
    display_name: str
    role: str
    status: str = "idle"
    current_task: str = "No active task."
    tool_or_model: str = "JARVIS control-plane"
    provider: str = "local"
    paid_by: str = "local machine"
    cost_mode: str = "local_compute"
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    cost_known: bool = False
    usage_limit_status: str = "unknown"
    approval_required: bool = True
    strong_approval_required: bool = False
    double_confirmation_required: bool = False
    sandbox_scope: List[str] = field(default_factory=list)
    worktree: Optional[str] = None
    branch: Optional[str] = None
    risk_level: str = "medium"
    can_execute_now: bool = False
    blocked_reasons: List[str] = field(default_factory=lambda: ["real agent execution is disabled"])
    next_safe_step: str = "Review the agent plan and required approval gates."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_agent_operations_dashboard() -> List[AgentOperation]:
    common = dict(can_execute_now=False, cost_known=False, estimated_cost=None, actual_cost=None)
    return [
        AgentOperation("planner", "PlannerAgent", "Classify missions and prepare plans.", **common),
        AgentOperation("builder", "BuilderAgent", "Prepare implementation candidates.", **common),
        AgentOperation("reviewer", "ReviewerAgent", "Review diffs, safety, and quality.", **common),
        AgentOperation("tester", "TesterAgent", "Prepare and summarize test plans.", **common),
        AgentOperation("researcher", "ResearcherAgent", "Prepare research plans without external calls.", **common),
        AgentOperation("operator", "OperatorAgent", "Coordinate gated operational previews.", **common),
        AgentOperation(
            "codex-cli", "CodexCliAgent", "Govern a future Codex CLI adapter.",
            tool_or_model="CodexCliAdapter preview", provider="OpenAI", paid_by="ChatGPT subscription",
            cost_mode="subscription_limit", usage_limit_status="manual_input_required", risk_level="high",
            strong_approval_required=True, **common,
        ),
        AgentOperation(
            "claude-code", "ClaudeCodeAgent", "Govern a future Claude Code CLI adapter.",
            tool_or_model="ClaudeCodeCliAdapter preview", provider="Anthropic", paid_by="Claude subscription",
            cost_mode="subscription_limit", usage_limit_status="manual_input_required", risk_level="high",
            strong_approval_required=True, **common,
        ),
        AgentOperation(
            "claude-cowork", "ClaudeCoworkAgent", "Govern a future Claude Cowork adapter.",
            tool_or_model="ClaudeCoworkAdapter preview", provider="Anthropic", paid_by="Claude subscription",
            cost_mode="subscription_limit", usage_limit_status="manual_input_required", risk_level="high",
            strong_approval_required=True, **common,
        ),
        AgentOperation(
            "api-fallback", "ApiFallbackAgent", "Govern a future API fallback adapter.",
            tool_or_model="ApiFallbackAdapter preview", provider="unknown", paid_by="David API billing",
            cost_mode="api_tokens", usage_limit_status="unknown", risk_level="high",
            strong_approval_required=True, **common,
        ),
        AgentOperation(
            "local-script", "LocalScriptAgent", "Govern a future local script adapter.",
            tool_or_model="LocalScriptAdapter planned", provider="local", paid_by="local machine",
            cost_mode="local_compute", usage_limit_status="unknown", **common,
        ),
    ]

