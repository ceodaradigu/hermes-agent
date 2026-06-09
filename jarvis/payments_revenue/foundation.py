from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_UNKNOWN = "unknown"
_REDACTED = "[redacted sensitive input]"
_PROVIDERS = {"unknown", "stripe", "paypal", "manual", "other"}
_METRIC_NAMES = ("MRR", "ARR", "ARPU", "conversion_rate", "churn", "LTV", "CAC", "gross_margin")
_SENSITIVE_MARKERS = (
    ".env", "account number", "api key", "api-key", "api_key", "apikey", "authorization",
    "bank account", "bearer", "card number", "client secret", "client_secret", "credential",
    "credentials", "cvv", "iban", "password", "private key", "private_key", "routing number",
    "secret", "token",
)


@dataclass(frozen=True)
class PaymentsRevenueStatus:
    prepare_only: bool = True
    payments_available: bool = False
    revenue_tracking_available: bool = False
    checkout_creation_enabled: bool = False
    payment_provider_connection_enabled: bool = False
    payment_processing_enabled: bool = False
    subscription_creation_enabled: bool = False
    invoice_creation_enabled: bool = False
    refund_execution_enabled: bool = False
    chargeback_handling_enabled: bool = False
    payout_enabled: bool = False
    bank_connection_enabled: bool = False
    card_data_handling_enabled: bool = False
    paid_resource_creation_enabled: bool = False
    external_calls_enabled: bool = False
    secrets_access_enabled: bool = False
    identity_usage_enabled: bool = False
    hermes_called: bool = False
    approval_gateway_called: bool = False
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        _force_safe(self)

    @classmethod
    def placeholder(cls) -> "PaymentsRevenueStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "PaymentsRevenueStatus":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PaymentsRevenuePolicy:
    prepare_only: bool = True
    no_payment_processing_by_default: bool = True
    no_checkout_creation_by_default: bool = True
    no_provider_connection_by_default: bool = True
    no_bank_connection_by_default: bool = True
    no_card_data_by_default: bool = True
    no_invoice_creation_by_default: bool = True
    no_subscription_creation_by_default: bool = True
    no_refunds_by_default: bool = True
    no_payouts_by_default: bool = True
    no_income_guarantees_by_default: bool = True
    no_fake_revenue_by_default: bool = True
    no_tax_or_legal_conclusion_by_default: bool = True
    strong_approval_required_for_checkout: bool = True
    strong_approval_required_for_payment_provider: bool = True
    strong_approval_required_for_money_movement: bool = True
    strong_approval_required_for_bank_connection: bool = True
    strong_approval_required_for_identity: bool = True
    strong_approval_required_for_refunds: bool = True
    financial_review_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        for name in self.__dataclass_fields__:
            if name != "prepare_only":
                object.__setattr__(self, name, True)

    @classmethod
    def placeholder(cls) -> "PaymentsRevenuePolicy":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "PaymentsRevenuePolicy":
        return cls()

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PricingModelPreview:
    prepare_only: bool = True
    product_name: str = _UNKNOWN
    audience: str = _UNKNOWN
    offer_type: str = _UNKNOWN
    pricing_hypothesis: str = _UNKNOWN
    pricing_tiers: List[str] = field(default_factory=list)
    currency: str = _UNKNOWN
    assumptions: List[str] = field(default_factory=list)
    validation_needed: bool = True
    no_confirmed_revenue: bool = True
    no_income_guarantees: bool = True
    would_charge: bool = False
    would_create_checkout: bool = False
    approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for name in ("product_name", "audience", "offer_type", "pricing_hypothesis", "currency"):
            object.__setattr__(self, name, _safe_text(getattr(self, name), _UNKNOWN))
        for name in ("pricing_tiers", "assumptions", "warnings"):
            object.__setattr__(self, name, _safe_list(getattr(self, name)))
        object.__setattr__(self, "validation_needed", True)
        object.__setattr__(self, "no_confirmed_revenue", bool(self.no_confirmed_revenue))
        object.__setattr__(self, "no_income_guarantees", True)
        object.__setattr__(self, "approval_required", True)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PricingModelPreview":
        source = dict(data or {})
        return cls(
            product_name=source.get("product_name", _UNKNOWN),
            audience=source.get("audience", _UNKNOWN),
            offer_type=source.get("offer_type", _UNKNOWN),
            pricing_hypothesis=source.get("pricing_hypothesis", _UNKNOWN),
            pricing_tiers=_safe_list(source.get("pricing_tiers")),
            currency=source.get("currency", _UNKNOWN),
            assumptions=_safe_list(source.get("assumptions")),
            no_confirmed_revenue=not (
                source.get("confirmed_revenue_explicitly_provided") is True
                and source.get("confirmed_revenue") not in (None, "")
            ),
            warnings=_safe_list(source.get("warnings")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class CheckoutPlanPreview:
    prepare_only: bool = True
    checkout_requested: bool = False
    provider: str = _UNKNOWN
    product_reference: str = _UNKNOWN
    price_reference: str = _UNKNOWN
    would_create_checkout: bool = False
    would_connect_provider: bool = False
    would_process_payment: bool = False
    would_collect_card_data: bool = False
    would_store_customer_data: bool = False
    secrets_required: bool = False
    strong_approval_required: bool = True
    blocked: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "checkout_requested", bool(self.checkout_requested))
        object.__setattr__(self, "provider", _choice(self.provider, _PROVIDERS))
        object.__setattr__(self, "product_reference", _safe_text(self.product_reference, _UNKNOWN))
        object.__setattr__(self, "price_reference", _safe_text(self.price_reference, _UNKNOWN))
        object.__setattr__(self, "strong_approval_required", True)
        object.__setattr__(self, "blocked", True)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "CheckoutPlanPreview":
        source = dict(data or {})
        return cls(
            checkout_requested=source.get("checkout_requested") is True,
            provider=source.get("provider", _UNKNOWN),
            product_reference=source.get("product_reference", _UNKNOWN),
            price_reference=source.get("price_reference", _UNKNOWN),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PaymentProviderPreview:
    prepare_only: bool = True
    provider_name: str = _UNKNOWN
    would_connect_provider: bool = False
    would_request_api_key: bool = False
    would_store_credentials: bool = False
    would_create_webhook: bool = False
    would_create_product: bool = False
    would_create_price: bool = False
    would_make_external_call: bool = False
    secrets_access_enabled: bool = False
    strong_approval_required: bool = True
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_name", _safe_text(self.provider_name, _UNKNOWN))
        object.__setattr__(self, "strong_approval_required", True)
        object.__setattr__(self, "warnings", _safe_list(self.warnings))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PaymentProviderPreview":
        source = dict(data or {})
        return cls(provider_name=source.get("provider_name", _UNKNOWN), warnings=_safe_list(source.get("warnings")))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class RevenueMetricsPreview:
    prepare_only: bool = True
    metrics: Dict[str, str] = field(default_factory=lambda: {name: _UNKNOWN for name in _METRIC_NAMES})
    no_fake_metrics: bool = True
    no_confirmed_revenue: bool = True
    dashboard_fields_preview: List[str] = field(default_factory=list)
    no_external_analytics_calls: bool = True
    no_personal_data_collection: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", _safe_metrics(self.metrics))
        object.__setattr__(self, "no_fake_metrics", True)
        object.__setattr__(self, "no_confirmed_revenue", bool(self.no_confirmed_revenue))
        object.__setattr__(self, "dashboard_fields_preview", _safe_list(self.dashboard_fields_preview))
        object.__setattr__(self, "no_external_analytics_calls", True)
        object.__setattr__(self, "no_personal_data_collection", True)
        object.__setattr__(self, "prepare_only", True)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "RevenueMetricsPreview":
        source = dict(data or {})
        explicit = source.get("metrics_explicitly_provided") is True
        return cls(
            metrics=_safe_metrics(source.get("metrics")) if explicit else {name: _UNKNOWN for name in _METRIC_NAMES},
            no_confirmed_revenue=not (
                source.get("confirmed_revenue_explicitly_provided") is True
                and source.get("confirmed_revenue") not in (None, "")
            ),
            dashboard_fields_preview=_safe_list(source.get("dashboard_fields_preview")),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class SubscriptionPlanPreview:
    prepare_only: bool = True
    plan_name: str = _UNKNOWN
    billing_interval: str = _UNKNOWN
    trial_policy: str = _UNKNOWN
    cancellation_policy: str = _UNKNOWN
    would_create_subscription: bool = False
    would_create_trial: bool = False
    would_charge: bool = False
    would_store_payment_method: bool = False
    approval_required: bool = True
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        for name in ("plan_name", "billing_interval", "trial_policy", "cancellation_policy"):
            object.__setattr__(self, name, _safe_text(getattr(self, name), _UNKNOWN))
        object.__setattr__(self, "approval_required", True)
        object.__setattr__(self, "strong_approval_required", True)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "SubscriptionPlanPreview":
        source = dict(data or {})
        return cls(
            plan_name=source.get("plan_name", _UNKNOWN),
            billing_interval=source.get("billing_interval", _UNKNOWN),
            trial_policy=source.get("trial_policy", _UNKNOWN),
            cancellation_policy=source.get("cancellation_policy", _UNKNOWN),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class InvoicePaymentLinkPreview:
    prepare_only: bool = True
    invoice_requested: bool = False
    payment_link_requested: bool = False
    would_create_invoice: bool = False
    would_create_payment_link: bool = False
    would_send_invoice: bool = False
    would_charge: bool = False
    tax_review_required: bool = True
    legal_review_required: bool = True
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "invoice_requested", bool(self.invoice_requested))
        object.__setattr__(self, "payment_link_requested", bool(self.payment_link_requested))
        for name in ("tax_review_required", "legal_review_required", "strong_approval_required"):
            object.__setattr__(self, name, True)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "InvoicePaymentLinkPreview":
        source = dict(data or {})
        return cls(
            invoice_requested=source.get("invoice_requested") is True,
            payment_link_requested=source.get("payment_link_requested") is True,
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class RefundChargebackPolicyPreview:
    prepare_only: bool = True
    refund_policy: str = _UNKNOWN
    chargeback_risk: str = _UNKNOWN
    would_issue_refund: bool = False
    would_contact_provider: bool = False
    would_move_money: bool = False
    financial_review_required: bool = True
    approval_required: bool = True
    strong_approval_required: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "refund_policy", _safe_text(self.refund_policy, _UNKNOWN))
        object.__setattr__(self, "chargeback_risk", _safe_text(self.chargeback_risk, _UNKNOWN))
        for name in ("financial_review_required", "approval_required", "strong_approval_required"):
            object.__setattr__(self, name, True)
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "RefundChargebackPolicyPreview":
        source = dict(data or {})
        return cls(
            refund_policy=source.get("refund_policy", _UNKNOWN),
            chargeback_risk=source.get("chargeback_risk", _UNKNOWN),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class FinancialRiskGuardPreview:
    prepare_only: bool = True
    risk_level: str = _UNKNOWN
    money_movement_detected: bool = False
    bank_or_card_data_detected: bool = False
    tax_or_legal_risk_detected: bool = False
    income_claim_risk_detected: bool = False
    provider_or_secret_risk_detected: bool = False
    blocked: bool = False
    strong_approval_required: bool = False
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        risk_flags = (
            bool(self.money_movement_detected),
            bool(self.bank_or_card_data_detected),
            bool(self.tax_or_legal_risk_detected),
            bool(self.income_claim_risk_detected),
            bool(self.provider_or_secret_risk_detected),
        )
        for name, value in zip(
            (
                "money_movement_detected", "bank_or_card_data_detected", "tax_or_legal_risk_detected",
                "income_claim_risk_detected", "provider_or_secret_risk_detected",
            ),
            risk_flags,
        ):
            object.__setattr__(self, name, value)
        financial_risk = any(risk_flags)
        blocking_risk = any((risk_flags[0], risk_flags[1], risk_flags[4]))
        object.__setattr__(self, "risk_level", "blocked" if blocking_risk else ("high" if financial_risk else _UNKNOWN))
        object.__setattr__(self, "blocked", blocking_risk)
        object.__setattr__(self, "strong_approval_required", financial_risk)
        object.__setattr__(self, "warnings", _safe_list(self.warnings))
        object.__setattr__(self, "prepare_only", True)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "FinancialRiskGuardPreview":
        source = dict(data or {})
        return cls(
            risk_level=source.get("risk_level", _UNKNOWN),
            money_movement_detected=_requested(source, "money_movement", "payment", "payout", "refund"),
            bank_or_card_data_detected=_requested(source, "bank", "card", "bank_or_card_data"),
            tax_or_legal_risk_detected=_requested(source, "tax", "legal"),
            income_claim_risk_detected=_requested(source, "income_claim", "income_guarantee"),
            provider_or_secret_risk_detected=_requested(source, "provider", "provider_connection", "secrets"),
            warnings=_safe_list(source.get("warnings")),
        )

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "FinancialRiskGuardPreview":
        source = dict(data or {})
        return cls(
            money_movement_detected=source.get("money_movement_detected") is True,
            bank_or_card_data_detected=source.get("bank_or_card_data_detected") is True,
            tax_or_legal_risk_detected=source.get("tax_or_legal_risk_detected") is True,
            income_claim_risk_detected=source.get("income_claim_risk_detected") is True,
            provider_or_secret_risk_detected=source.get("provider_or_secret_risk_detected") is True,
            warnings=_safe_list(source.get("warnings")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class RevenueExperimentPreview:
    prepare_only: bool = True
    experiment_name: str = _UNKNOWN
    hypothesis: str = _UNKNOWN
    pricing_variants: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    max_budget: str = _UNKNOWN
    would_launch: bool = False
    would_spend: bool = False
    would_create_checkout: bool = False
    would_process_payment: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "experiment_name", _safe_text(self.experiment_name, _UNKNOWN))
        object.__setattr__(self, "hypothesis", _safe_text(self.hypothesis, _UNKNOWN))
        object.__setattr__(self, "pricing_variants", _safe_list(self.pricing_variants))
        object.__setattr__(self, "success_metrics", _safe_list(self.success_metrics))
        object.__setattr__(self, "max_budget", _safe_text(self.max_budget, _UNKNOWN))
        object.__setattr__(self, "approval_required", True)
        object.__setattr__(self, "strong_approval_required", bool(self.strong_approval_required))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "RevenueExperimentPreview":
        source = dict(data or {})
        return cls(
            experiment_name=source.get("experiment_name", _UNKNOWN),
            hypothesis=source.get("hypothesis", _UNKNOWN),
            pricing_variants=_safe_list(source.get("pricing_variants")),
            success_metrics=_safe_list(source.get("success_metrics")),
            max_budget=source.get("max_budget", _UNKNOWN),
            strong_approval_required=_financial_risk_requested(source) or source.get("max_budget") not in (None, "", _UNKNOWN),
        )

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


@dataclass(frozen=True)
class PaymentApprovalRequirements:
    prepare_only: bool = True
    approval_required: bool = True
    strong_approval_required: bool = False
    approval_gateway_called: bool = False
    approval_created: bool = False
    approval_granted: bool = False
    approval_rejected: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "approval_required", True)
        object.__setattr__(self, "strong_approval_required", bool(self.strong_approval_required))
        _force_safe(self)

    @classmethod
    def from_request(cls, data: Optional[Dict[str, Any]]) -> "PaymentApprovalRequirements":
        return cls(strong_approval_required=_financial_risk_requested(dict(data or {})))

    from_dict = from_request

    def to_dict(self) -> Dict[str, Any]:
        return _serialize(self)


_FORCED_FALSE = {
    "payments_available", "revenue_tracking_available", "checkout_creation_enabled",
    "payment_provider_connection_enabled", "payment_processing_enabled", "subscription_creation_enabled",
    "invoice_creation_enabled", "refund_execution_enabled", "chargeback_handling_enabled", "payout_enabled",
    "bank_connection_enabled", "card_data_handling_enabled", "paid_resource_creation_enabled",
    "external_calls_enabled", "secrets_access_enabled", "identity_usage_enabled", "hermes_called",
    "approval_gateway_called", "execution_enabled", "would_charge", "would_create_checkout",
    "would_connect_provider", "would_process_payment", "would_collect_card_data",
    "would_store_customer_data", "secrets_required", "would_request_api_key", "would_store_credentials",
    "would_create_webhook", "would_create_product", "would_create_price", "would_make_external_call",
    "would_create_subscription", "would_create_trial", "would_store_payment_method", "would_create_invoice",
    "would_create_payment_link", "would_send_invoice", "would_issue_refund", "would_contact_provider",
    "would_move_money", "would_launch", "would_spend", "approval_created", "approval_granted",
    "approval_rejected",
}


def _force_safe(value: Any) -> None:
    object.__setattr__(value, "prepare_only", True)
    for name in _FORCED_FALSE:
        if name in value.__dataclass_fields__:
            object.__setattr__(value, name, False)


def _serialize(value: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for name in value.__dataclass_fields__:
        item = getattr(value, name)
        if isinstance(item, list):
            item = list(item)
        elif isinstance(item, dict):
            item = dict(item)
        result[name] = item
    result["prepare_only"] = True
    for name in _FORCED_FALSE:
        if name in result:
            result[name] = False
    return result


def _safe_text(value: Any, default: str = "") -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return default
    if any(marker in text.lower() for marker in _SENSITIVE_MARKERS):
        return _REDACTED
    return text[:500]


def _safe_list(value: Any) -> List[str]:
    items = value if isinstance(value, list) else []
    return [_safe_text(item) for item in items[:100] if _safe_text(item)]


def _safe_metrics(value: Any) -> Dict[str, str]:
    source = value if isinstance(value, dict) else {}
    return {name: _safe_text(source.get(name), _UNKNOWN) for name in _METRIC_NAMES}


def _choice(value: Any, choices: set[str]) -> str:
    text = str(value or "").strip().lower()
    return text if text in choices else _UNKNOWN


def _requested(source: Dict[str, Any], *names: str) -> bool:
    return any(source.get(f"{name}_requested") is True or source.get(f"{name}_detected") is True for name in names)


def _financial_risk_requested(source: Dict[str, Any]) -> bool:
    names = (
        "checkout", "provider", "provider_connection", "bank", "card", "money_movement", "payment",
        "refund", "subscription", "invoice", "identity", "secrets", "payout",
    )
    return _requested(source, *names) or source.get("max_budget") not in (None, "", _UNKNOWN)
