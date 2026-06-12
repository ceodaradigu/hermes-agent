from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class CostUsageEntry:
    provider: str
    tool: str
    paid_by: str
    billing_mode: str
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    currency: str = "unknown"
    cost_known: bool = False
    cost_confidence: str = "unknown"
    token_input_estimate: Optional[int] = None
    token_output_estimate: Optional[int] = None
    token_actual: Optional[int] = None
    usage_limit_status: str = "unknown"
    usage_limit_known: bool = False
    renewal_time_known: bool = False
    manual_check_url_or_hint: str = "Check the provider account manually outside JARVIS."
    budget_limit: Optional[float] = None
    budget_remaining: Optional[float] = None
    roi_estimate: Optional[float] = None
    roi_known: bool = False
    notes: str = "No billing service was queried and no real cost was invented."
    no_fake_costs: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_cost_usage_dashboard() -> List[CostUsageEntry]:
    return [
        CostUsageEntry("OpenAI API", "API fallback", "David API billing", "api_usage", usage_limit_status="manual_input_required"),
        CostUsageEntry("Codex CLI / ChatGPT subscription", "Codex CLI", "ChatGPT subscription", "subscription", usage_limit_status="manual_input_required"),
        CostUsageEntry("Anthropic API", "API fallback", "David API billing", "api_usage", usage_limit_status="manual_input_required"),
        CostUsageEntry("Claude Code subscription", "Claude Code", "Claude subscription", "subscription", usage_limit_status="manual_input_required"),
        CostUsageEntry("Claude Cowork/Desktop subscription", "Claude Cowork", "Claude subscription", "subscription", usage_limit_status="manual_input_required"),
        CostUsageEntry("Local/Ollama future", "Local model or script", "local machine", "local_compute", estimated_cost=0.0, notes="Direct model usage is zero-priced; hardware and electricity remain unknown."),
        CostUsageEntry("Unknown provider", "Unclassified future adapter", "unknown", "unknown"),
    ]

