from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ClaudeCoworkAdapter:
    adapter_name: str = "Claude Cowork/Desktop"
    routine_type: str = "unknown"
    supervised_required: bool = True
    local_desktop_required: bool = True
    browser_or_app_access_possible: bool = True
    sensitive_actions_blocked_by_default: bool = True
    stores_access_material: bool = False
    uses_cookies: bool = False
    automates_web_ui: bool = False
    approval_required: bool = True
    strong_approval_required_when_sensitive: bool = True
    would_invoke_real_cowork: bool = False
    would_submit_forms: bool = False
    would_handle_money: bool = False
    would_touch_production: bool = False
    blocked_reasons: List[str] = field(default_factory=lambda: ["real Cowork/Desktop invocation is disabled"])
    next_safe_step: str = "Review the supervised desktop routine and keep sensitive actions blocked."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def preview(cls, **values: Any) -> "ClaudeCoworkAdapter":
        routine = str(values.get("routine_type") or "unknown").lower()
        blocked = ["real Cowork/Desktop invocation is disabled"]
        if routine in {"form_assist", "browser_assist"}:
            blocked.append("form submission and sensitive browser actions remain blocked")
        return cls(routine_type=routine, blocked_reasons=blocked)
