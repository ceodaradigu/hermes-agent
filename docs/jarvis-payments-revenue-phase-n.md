# JARVIS Phase N - Payments & Revenue

Phase N adds a complete `prepare_only` foundation for reviewing monetization, pricing, checkout
plans, provider requirements, revenue metrics, subscriptions, invoices, refund policies, financial
risk, and revenue experiments.

It separates hypotheses and explicitly supplied metrics from confirmed revenue. It does not process
payments or move money.

## Safety boundary

The foundation permits deterministic, in-memory previews from user-provided inputs. Every status,
policy, preview, API route, Command Center marker, and Operator Console field remains prepare-only.

It does **not**:

- create a checkout, payment link, invoice, subscription, trial, refund, payout, webhook, or paid resource;
- connect Stripe, PayPal, a bank, a card, an external account, or any payment provider;
- request or store API keys, tokens, credentials, card data, bank data, customer identity, or secrets;
- process a card, charge a customer, move money, contact a provider, or call an external service;
- call Hermes, create an ApprovalGateway request, create missions/tasks, or persist state;
- invent revenue or metrics, guarantee income, or provide a tax or legal conclusion.

Strong approval is required before any future real action involving checkout, provider connection,
bank or card data, money movement, refunds, subscriptions, invoices, identity, or secrets. Phase N
records that requirement only; it never creates or decides an approval.

## API

Read-only status and policy:

- `GET /payments-revenue/status`
- `GET /payments-revenue/policy`

Prepare-only previews:

- `POST /payments-revenue/pricing-preview`
- `POST /payments-revenue/checkout-plan`
- `POST /payments-revenue/provider-preview`
- `POST /payments-revenue/metrics-preview`
- `POST /payments-revenue/subscription-preview`
- `POST /payments-revenue/invoice-payment-link-preview`
- `POST /payments-revenue/refund-chargeback-policy`
- `POST /payments-revenue/financial-risk-guard`
- `POST /payments-revenue/revenue-experiment`
- `POST /payments-revenue/approval-requirements`

There are no execution routes and no WebSocket.

## Example previews

Pricing remains a hypothesis and never creates confirmed revenue:

```json
POST /payments-revenue/pricing-preview
{
  "product_name": "Reviewable product",
  "pricing_hypothesis": "10 EUR may be testable",
  "pricing_tiers": ["Starter: 10 EUR"],
  "currency": "EUR"
}
```

```json
{
  "prepare_only": true,
  "validation_needed": true,
  "no_confirmed_revenue": true,
  "no_income_guarantees": true,
  "would_charge": false,
  "would_create_checkout": false,
  "approval_required": true
}
```

A checkout plan records requested references but stays blocked:

```json
POST /payments-revenue/checkout-plan
{
  "checkout_requested": true,
  "provider": "stripe",
  "product_reference": "product-preview",
  "price_reference": "price-preview"
}
```

The response always includes:

```json
{
  "prepare_only": true,
  "would_create_checkout": false,
  "would_connect_provider": false,
  "would_process_payment": false,
  "would_collect_card_data": false,
  "secrets_required": false,
  "strong_approval_required": true,
  "blocked": true
}
```

Provider preview describes a provider without requesting a key, storing credentials, creating
provider resources, creating webhooks, or making external calls.

Revenue metrics preview exposes `MRR`, `ARR`, `ARPU`, `conversion_rate`, `churn`, `LTV`, `CAC`, and
`gross_margin`. Values remain `unknown` unless the request marks them as explicitly supplied.
Explicitly supplied values remain user input, not independently confirmed revenue. External analytics
calls and personal-data collection remain disabled.

Subscription preview can describe a plan, billing interval, trial policy, and cancellation policy.
It cannot create a subscription or trial, charge, or store a payment method.

Invoice/payment-link preview records whether an invoice or link was requested. It cannot create or
send either artifact and always requires tax review, legal review, and strong approval before a
future real action.

Refund/chargeback policy preview can structure policy text and risk assumptions. It cannot issue a
refund, contact a provider, or move money.

Financial risk guard classifies explicit risk signals. Money movement, bank/card, provider
connection, and secret risk are blocked. Tax/legal and income-claim signals are marked high risk for
review without producing a conclusion or income claim.

Revenue experiment preview can structure a hypothesis, pricing variants, success metrics, and a
maximum budget. It cannot launch, spend, create a checkout, or process a payment.

Approval requirements preview returns strong-approval requirements for checkout, provider, bank,
card, money movement, refunds, subscriptions, invoices, identity, and secrets. It never calls or
creates a real approval.

## Product integration

Command Center exposes `payments_revenue: prepare_only`.

Operator Console exposes:

- prepare-only payments/revenue status and policy;
- a financial readiness placeholder;
- read and preview capabilities only;
- disabled execution, spend, approval creation, Hermes, network, and secrets capabilities.

Marketing Distribution may provide campaign and measurement hypotheses to a revenue experiment, but
cannot launch it or spend. Asset Factory may provide offer and product references to pricing and
checkout previews, but cannot create a checkout. Deploy Publishing Control may prepare an asset for
publication, but cannot enable paid resources, provider connections, or payment processing.

This phase intentionally stops before payment execution. Real financial operations require provider
integration, credential handling, identity, compliance, audit, and strong approval boundaries that
are outside the safe scope of Phase N.
