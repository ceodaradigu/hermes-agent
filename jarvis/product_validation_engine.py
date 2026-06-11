from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ProductIdeaIntake:
    idea_summary: str
    target_customer: Optional[str]
    problem_statement: Optional[str]
    proposed_solution: Optional[str]
    must_have_features: List[str] = field(default_factory=list)
    must_not_have_features: List[str] = field(default_factory=list)
    budget_limit: Optional[float] = None
    timeline: Optional[str] = None
    technical_level: Optional[str] = None
    monetization_goal: Optional[str] = None
    privacy_constraints: List[str] = field(default_factory=list)
    deployment_preference: Optional[str] = None
    differentiation_goal: Optional[str] = None
    unknowns: List[str] = field(default_factory=list)
    clarification_needed: bool = False

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ProductIdeaIntake":
        source = dict(data or {})
        values = {
            name: _optional_text(source.get(name))
            for name in (
                "target_customer", "problem_statement", "proposed_solution", "timeline",
                "technical_level", "monetization_goal", "deployment_preference", "differentiation_goal",
            )
        }
        budget = _number(source.get("budget_limit"))
        unknowns = _list(source.get("unknowns"))
        for value, label in (
            (values["target_customer"], "target_customer"),
            (budget, "budget_limit"),
            (values["timeline"], "timeline"),
        ):
            if value is None:
                unknowns.append(label)
        return cls(
            idea_summary=_text(source.get("idea_summary")) or "Unspecified product idea",
            must_have_features=_list(source.get("must_have_features")),
            must_not_have_features=_list(source.get("must_not_have_features")),
            budget_limit=budget,
            privacy_constraints=_list(source.get("privacy_constraints")),
            unknowns=list(dict.fromkeys(unknowns)),
            clarification_needed=bool(unknowns),
            **values,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductValidationPreview:
    niche: str
    target_customer: str
    problem_severity: str
    willingness_to_pay_estimate: str
    competition_level: str
    differentiation: str
    acquisition_channels: List[str]
    validation_score: int
    confidence_level: str
    assumptions: List[str]
    unknowns: List[str]
    red_flags: List[str]
    recommendation: str
    no_fake_market_claims: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "no_fake_market_claims", True)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "ProductValidationPreview":
        source = dict(data or {})
        niche = _text(source.get("niche")) or "unknown"
        customer = _text(source.get("target_customer")) or "unknown"
        differentiation = _text(source.get("differentiation")) or "unknown"
        monetization = _text(source.get("monetization_goal"))
        evidence = _list(source.get("validation_evidence"))
        unknowns = _list(source.get("unknowns"))
        for value, label in ((niche if niche != "unknown" else "", "niche"), (customer if customer != "unknown" else "", "target_customer")):
            if not value:
                unknowns.append(label)
        red_flags = _list(source.get("red_flags"))
        if differentiation.lower() in {"", "unknown", "generic", "none"}:
            red_flags.append("differentiation is insufficient or unproven")
        if not monetization:
            red_flags.append("monetization path is unclear")
        score = max(0, min(100, _integer(source.get("validation_score"), 50) - 15 * len(red_flags) - 5 * len(unknowns)))
        recommendation = "reject" if score < 25 else ("refine" if red_flags or unknowns else "proceed")
        return cls(
            niche=niche,
            target_customer=customer,
            problem_severity=_choice(source.get("problem_severity"), {"low", "medium", "high", "unknown"}, "unknown"),
            willingness_to_pay_estimate=_text(source.get("willingness_to_pay_estimate")) or "unknown; requires validation",
            competition_level=_choice(source.get("competition_level"), {"low", "medium", "high", "unknown"}, "unknown"),
            differentiation=differentiation,
            acquisition_channels=_list(source.get("acquisition_channels")),
            validation_score=score,
            confidence_level="low" if not evidence or unknowns else _choice(source.get("confidence_level"), {"low", "medium", "high"}, "medium"),
            assumptions=_list(source.get("assumptions")),
            unknowns=list(dict.fromkeys(unknowns)),
            red_flags=list(dict.fromkeys(red_flags)),
            recommendation=recommendation,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DifferentiationReview:
    differentiation_score: int
    generic_template_risk: bool
    clone_risk: bool
    looks_like_common_boilerplate: bool
    unique_angle: str
    unfair_advantage_or_edge: str
    product_specific_decisions: List[str]
    missing_differentiators: List[str]
    recommendation: str
    required_changes: List[str]
    quality_gate_passed: bool

    def __post_init__(self) -> None:
        if self.generic_template_risk or self.clone_risk or self.looks_like_common_boilerplate:
            object.__setattr__(self, "quality_gate_passed", False)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "DifferentiationReview":
        source = dict(data or {})
        angle = _text(source.get("unique_angle"))
        edge = _text(source.get("unfair_advantage_or_edge"))
        decisions = _list(source.get("product_specific_decisions"))
        generic = source.get("looks_like_common_boilerplate") is True or source.get("generic_template_risk") is True
        clone = source.get("clone_risk") is True or source.get("products_could_look_like_twins") is True
        missing = _list(source.get("missing_differentiators"))
        if not angle:
            missing.append("unique angle")
        if not edge:
            missing.append("defensible edge")
        if not decisions:
            missing.append("product-specific decisions")
        score = max(0, min(100, _integer(source.get("differentiation_score"), 70) - 25 * generic - 25 * clone - 10 * len(missing)))
        passed = score >= 60 and not generic and not clone and bool(angle) and bool(decisions)
        changes = _list(source.get("required_changes"))
        if not passed:
            changes.extend(["define a product-specific reason to exist", "replace generic decisions with differentiated product choices"])
        return cls(
            differentiation_score=score,
            generic_template_risk=generic,
            clone_risk=clone,
            looks_like_common_boilerplate=generic,
            unique_angle=angle or "unknown",
            unfair_advantage_or_edge=edge or "unknown",
            product_specific_decisions=decisions,
            missing_differentiators=list(dict.fromkeys(missing)),
            recommendation="proceed" if passed else ("reject" if score < 25 else "refine"),
            required_changes=list(dict.fromkeys(changes)),
            quality_gate_passed=passed,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProductValidationEngine:
    def intake(self, data: Optional[Dict[str, Any]]) -> ProductIdeaIntake:
        return ProductIdeaIntake.from_request(data)

    def validate(self, data: Optional[Dict[str, Any]]) -> ProductValidationPreview:
        return ProductValidationPreview.from_request(data)

    def review_differentiation(self, data: Optional[Dict[str, Any]]) -> DifferentiationReview:
        return DifferentiationReview.from_request(data)


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:1000]


def _optional_text(value: Any) -> Optional[str]:
    return _text(value) or None


def _list(value: Any) -> List[str]:
    return [_text(item) for item in (value or []) if _text(item)]


def _number(value: Any) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _integer(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _choice(value: Any, choices: set[str], default: str) -> str:
    normalized = _text(value).lower()
    return normalized if normalized in choices else default
