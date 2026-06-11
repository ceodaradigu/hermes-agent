from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RevenueProjection:
    expected_customers: Optional[float]
    conversion_rate: Optional[float]
    churn_rate: Optional[float]
    monthly_price: Optional[float]
    estimated_mrr: Optional[float]
    estimated_arr: Optional[float]
    confidence_level: str
    assumptions: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    is_confirmed_revenue: bool = False
    is_estimate: bool = True
    blocked_reasons: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "is_confirmed_revenue", False)
        object.__setattr__(self, "is_estimate", True)
        object.__setattr__(self, "assumptions", _list(self.assumptions))
        object.__setattr__(self, "unknowns", _list(self.unknowns))
        object.__setattr__(self, "blocked_reasons", _list(self.blocked_reasons))

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "RevenueProjection":
        source = dict(data or {})
        customers = _number(source.get("expected_customers"))
        conversion = _rate(source.get("conversion_rate"))
        churn = _rate(source.get("churn_rate"))
        price = _number(source.get("monthly_price"))
        unknowns = _list(source.get("unknowns"))
        for value, label in (
            (customers, "expected_customers"),
            (conversion, "conversion_rate"),
            (price, "monthly_price"),
        ):
            if value is None:
                unknowns.append(label)
        if churn is None:
            unknowns.append("churn_rate")
        mrr = round(customers * price, 2) if customers is not None and price is not None else None
        arr = round(mrr * 12, 2) if mrr is not None else None
        blocked = _list(source.get("blocked_reasons"))
        if mrr is None:
            blocked.append("insufficient data to estimate MRR and ARR")
        confidence = _confidence(source.get("confidence_level"), unknowns)
        return cls(
            expected_customers=customers,
            conversion_rate=conversion,
            churn_rate=churn,
            monthly_price=price,
            estimated_mrr=mrr,
            estimated_arr=arr,
            confidence_level=confidence,
            assumptions=_list(source.get("assumptions")),
            unknowns=list(dict.fromkeys(unknowns)),
            blocked_reasons=list(dict.fromkeys(blocked)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UnitEconomicsProjection:
    cac_estimate: Optional[float]
    ltv_estimate: Optional[float]
    gross_margin_estimate: Optional[float]
    payback_period_months_estimate: Optional[float]
    roi_estimate: Optional[float]
    assumptions: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    confidence: str = "low"
    roi_assessment: str = "uncertain"
    not_financial_advice: bool = True
    not_confirmed_results: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "assumptions", _list(self.assumptions))
        object.__setattr__(self, "unknowns", _list(self.unknowns))
        object.__setattr__(self, "not_financial_advice", True)
        object.__setattr__(self, "not_confirmed_results", True)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "UnitEconomicsProjection":
        source = dict(data or {})
        acquisition_spend = _number(source.get("acquisition_spend"))
        acquired_customers = _number(source.get("acquired_customers"))
        monthly_revenue_per_customer = _number(source.get("monthly_revenue_per_customer"))
        gross_margin_rate = _rate(source.get("gross_margin_rate"))
        monthly_churn_rate = _rate(source.get("monthly_churn_rate"))
        investment = _number(source.get("investment"))
        return_amount = _number(source.get("return_amount"))
        unknowns = _list(source.get("unknowns"))
        values = (
            (acquisition_spend, "acquisition_spend"),
            (acquired_customers, "acquired_customers"),
            (monthly_revenue_per_customer, "monthly_revenue_per_customer"),
            (gross_margin_rate, "gross_margin_rate"),
            (monthly_churn_rate, "monthly_churn_rate"),
            (investment, "investment"),
            (return_amount, "return_amount"),
        )
        for value, label in values:
            if value is None:
                unknowns.append(label)
        cac = (
            round(acquisition_spend / acquired_customers, 2)
            if acquisition_spend is not None and acquired_customers not in (None, 0)
            else None
        )
        margin = (
            round(monthly_revenue_per_customer * gross_margin_rate, 2)
            if monthly_revenue_per_customer is not None and gross_margin_rate is not None
            else None
        )
        ltv = round(margin / monthly_churn_rate, 2) if margin is not None and monthly_churn_rate not in (None, 0) else None
        payback = round(cac / margin, 2) if cac is not None and margin not in (None, 0) else None
        roi = round(((return_amount - investment) / investment) * 100, 2) if investment not in (None, 0) and return_amount is not None else None
        assessment = "uncertain" if roi is None else ("negative" if roi < 0 else "positive_estimate")
        return cls(
            cac_estimate=cac,
            ltv_estimate=ltv,
            gross_margin_estimate=margin,
            payback_period_months_estimate=payback,
            roi_estimate=roi,
            assumptions=_list(source.get("assumptions")),
            unknowns=list(dict.fromkeys(unknowns)),
            confidence=_confidence(source.get("confidence"), unknowns),
            roi_assessment=assessment,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 4) if math.isfinite(number) and number >= 0 else None


def _rate(value: Any) -> Optional[float]:
    number = _number(value)
    return number if number is not None and number <= 1 else None


def _confidence(value: Any, unknowns: List[str]) -> str:
    requested = str(value or "").strip().lower()
    if unknowns:
        return "low"
    return requested if requested in {"low", "medium", "high"} else "medium"


def _list(value: Any) -> List[str]:
    return [" ".join(str(item).strip().split())[:500] for item in (value or []) if str(item).strip()]
