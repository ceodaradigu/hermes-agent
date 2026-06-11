from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional


_INTERVALS = {"monthly", "yearly", "one_time", "usage_based"}


@dataclass(frozen=True)
class PricingPlan:
    plan_id: str
    name: str
    price_amount: Optional[float]
    currency: str = "EUR"
    billing_interval: str = "monthly"
    included_usage: Optional[str] = None
    overage_price: Optional[float] = None
    target_customer: str = "unknown"
    value_proposition: str = "unknown"
    margin_notes: List[str] = field(default_factory=list)
    risk_notes: List[str] = field(default_factory=list)
    enabled_for_preview: bool = True
    live_billing_enabled: bool = False
    would_charge_real_money: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", _text(self.plan_id) or "pricing-plan-preview")
        object.__setattr__(self, "name", _text(self.name) or "Unnamed pricing plan")
        object.__setattr__(self, "price_amount", _amount(self.price_amount))
        object.__setattr__(self, "currency", (_text(self.currency) or "EUR").upper())
        interval = _text(self.billing_interval).lower()
        object.__setattr__(self, "billing_interval", interval if interval in _INTERVALS else "monthly")
        object.__setattr__(self, "included_usage", _optional_text(self.included_usage))
        object.__setattr__(self, "overage_price", _amount(self.overage_price))
        object.__setattr__(self, "target_customer", _text(self.target_customer) or "unknown")
        object.__setattr__(self, "value_proposition", _text(self.value_proposition) or "unknown")
        object.__setattr__(self, "margin_notes", _list(self.margin_notes))
        risks = _list(self.risk_notes)
        if self.price_amount is None:
            risks.append("price amount is unknown and requires validation")
        risks.extend(["proposed price is not a confirmed sale", "live billing is disabled"])
        object.__setattr__(self, "risk_notes", list(dict.fromkeys(risks)))
        object.__setattr__(self, "enabled_for_preview", True)
        object.__setattr__(self, "live_billing_enabled", False)
        object.__setattr__(self, "would_charge_real_money", False)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PricingPlan":
        source = dict(data or {})
        return cls(
            plan_id=source.get("plan_id", "pricing-plan-preview"),
            name=source.get("name", "Unnamed pricing plan"),
            price_amount=source.get("price_amount"),
            currency=source.get("currency", "EUR"),
            billing_interval=source.get("billing_interval", "monthly"),
            included_usage=source.get("included_usage"),
            overage_price=source.get("overage_price"),
            target_customer=source.get("target_customer", "unknown"),
            value_proposition=source.get("value_proposition", "unknown"),
            margin_notes=source.get("margin_notes") or [],
            risk_notes=source.get("risk_notes") or [],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _amount(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 2) if math.isfinite(number) and number >= 0 else None


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:500]


def _optional_text(value: Any) -> Optional[str]:
    text = _text(value)
    return text or None


def _list(value: Any) -> List[str]:
    return [_text(item) for item in (value or []) if _text(item)]
