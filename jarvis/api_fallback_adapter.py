from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ApiFallbackAdapter:
    provider: str = "unknown"
    use_case: str = "fallback"
    api_usage_required: bool = True
    network_required: bool = True
    cost_mode: str = "api_tokens"
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    cost_known: bool = False
    access_material_required: bool = True
    approval_required: bool = True
    budget_guard_required: bool = True
    would_call_api: bool = False
    blocked_reasons: List[str] = field(default_factory=lambda: ["real API invocation is disabled"])
    next_safe_step: str = "Provide provider access manually, define a budget guard, and review the structured use case."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def preview(cls, **values: Any) -> "ApiFallbackAdapter":
        return cls(
            provider=str(values.get("provider") or "unknown").lower(),
            use_case=str(values.get("use_case") or "fallback").lower(),
            estimated_cost=values.get("estimated_cost"),
            cost_known=values.get("estimated_cost") is not None,
            blocked_reasons=["real API invocation is disabled", "external network and provider access gates are disabled"],
        )
