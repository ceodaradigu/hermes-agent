# JARVIS Phase M - Marketing / Distribution Engine Foundation

Phase M adds a reviewable, deterministic planning layer for marketing and distribution. It is a
`prepare_only` foundation: it can structure user-provided audience assumptions, channel strategy,
campaign plans, draft distribution content, measurement plans, budget guards, launch checklists,
and approval requirements.

## Safety Boundary

This phase does not publish, send emails or DMs, post to social networks, create ads, spend money,
connect external accounts, use a real identity, scrape, automate spam, install tracking, call
analytics, call external services, read secrets, call Hermes, create missions/tasks, or call
`ApprovalGateway.create_request`.

All status capabilities remain disabled. Deserialization cannot enable publishing, sending, paid
ads, external accounts, identity usage, spending, external calls, secrets, Hermes, or ApprovalGateway.
There are no publish/send/spend/connect/scrape/run routes and no WebSocket.

The policy requires review before distribution and forbids spam, fake claims, fake social proof,
fabricated metrics, and income guarantees. Real publish, send, paid ads, account connection,
identity use, secrets use, and budget spend require strong approval in a future execution phase.
Phase M records that requirement but never creates or grants an approval.

## Safe API

Read-only status and policy:

- `GET /marketing-distribution/status`
- `GET /marketing-distribution/policy`

Pure preview endpoints:

- `POST /marketing-distribution/audience-preview`
- `POST /marketing-distribution/channel-strategy`
- `POST /marketing-distribution/campaign-plan`
- `POST /marketing-distribution/content-pack`
- `POST /marketing-distribution/measurement-plan`
- `POST /marketing-distribution/budget-guard`
- `POST /marketing-distribution/launch-checklist`
- `POST /marketing-distribution/approval-requirements`

Example audience preview request:

```json
{
  "audience_name": "Independent product teams",
  "problem": "Distribution planning is inconsistent",
  "pains": ["Limited review time"],
  "desired_outcomes": ["A repeatable organic launch plan"],
  "channels": ["SEO", "community"],
  "data_source": "user_provided",
  "confidence": "medium"
}
```

The response preserves the supplied planning inputs while returning
`no_external_research_performed=true` and `no_personal_data_required=true`.

Example campaign plan request:

```json
{
  "campaign_name": "Reviewable launch",
  "objective": "Prepare a launch narrative",
  "audience": "Independent product teams",
  "channels": ["SEO", "community"],
  "assets_needed": ["Landing page draft", "Community post draft"],
  "success_metrics": ["Reviewed visits", "Qualified replies"]
}
```

The response always has `would_publish=false`, `would_send=false`, `would_spend=false`, and
`would_call_external_service=false`.

Example content distribution pack request:

```json
{
  "posts": ["Draft social post for review"],
  "email_drafts": ["Draft email for review"],
  "community_posts": ["Draft community post"],
  "outreach_messages": ["Draft outreach message"],
  "seo_snippets": ["Reviewable SEO description"],
  "cta_variants": ["Review the proposal"]
}
```

The pack covers SEO, social, community, email, outreach, and CTA previews. It never sends or
publishes. Sensitive inputs are redacted, and safety flags prohibit fake claims, fake social proof,
fabricated metrics, and income guarantees.

Example measurement plan request:

```json
{
  "utm_plan": ["utm_source=community", "utm_campaign=reviewable_launch"],
  "metrics": ["Reviewed visits", "Qualified replies"],
  "attribution_assumptions": ["Last-touch is only a planning assumption"],
  "dashboard_fields_preview": ["channel", "campaign", "metric"]
}
```

This produces a UTM/measurement preview only. It installs no tracking, makes no analytics calls,
and collects no personal data by default.

Example budget guard and launch checklist:

```json
{"budget_requested": "100 EUR maximum"}
```

```json
{
  "required_assets": ["Reviewed content pack"],
  "identity_requested": true,
  "external_account_requested": true,
  "budget_requested": "100 EUR maximum"
}
```

The budget guard never spends or configures payments/ads. The launch checklist remains
`ready_to_launch=false` and marks the required identity, account, paid-budget, publish, legal, and
strong approvals.

## Relationship To Existing Foundations

Asset Factory / Web Builder can prepare reviewable assets and copy that Phase M references in
campaign and distribution plans. Phase M does not build or publish those assets.

Deploy & Publishing Control can prepare future publishing targets and readiness checks. Phase M
only prepares distribution intent and launch readiness. Neither foundation publishes, deploys,
connects accounts, or spends. A future execution phase must pass policy, exact-scope strong
approval, and the relevant publishing controls before any real distribution action.

Command Center and Operator Console expose only a `marketing_distribution_engine=prepare_only`
marker plus safe status, policy, and launch-readiness placeholders. They do not enable publishing,
sending, paid ads, account connection, identity usage, or spend.

## Why Phase M Does Not Distribute

Distribution can affect reputation, identity, privacy, legal obligations, platform accounts, and
money. Separating preparation from execution makes plans and content reviewable before any
irreversible action. This phase establishes that review boundary without introducing external
accounts, credentials, network calls, or execution paths.
