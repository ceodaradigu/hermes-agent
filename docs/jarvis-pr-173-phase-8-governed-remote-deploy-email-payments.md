# PR #173 - Phase 8 Governed Remote Channels, Deploy, Email & Payments

Date: 2026-06-20

## Summary

Phase 8 turns remote, deploy, email and payment readiness into governed
prepare-only pilot contracts. The boundary remains unchanged:

```text
JARVIS governs, classifies risk, asks approval, audits, stops and controls.
Hermes executes only behind JARVIS-governed execution paths.
```

This phase does not add `/execute`, shell-freeform execution, direct frontend
Hermes calls, hidden remote listeners, public internet exposure, live Telegram
runtime, production deploy, DNS changes, secret reads, email sending, Stripe
charges, payouts, refunds, fake provider success, fake rollback or fake revenue.

## What Is Real

- `Phase8GovernedRemoteExternalOpsControlPlane` adds a local control-plane
  contract for remote channels, Telegram readiness, mobile approval center
  readiness, deploy/email/payment candidates, budget checks and revenue events.
- Remote channel registry v1 exposes Telegram, mobile/PWA, local controller
  notification and future approval center statuses with trusted device binding,
  pairing, revocation, rate-limit metadata, anti-replay, expiration and remote
  kill switch state.
- Remote device pairing reuses the existing Phase 5 identity store and converts
  successful remote pairings into trusted non-local devices scoped for
  notification/readback/remote approval intent only. Remote devices cannot
  execute or call Hermes directly.
- Telegram readiness detects token/config presence from environment without
  printing, storing or logging token values. It reports webhook/polling
  readiness and refuses bot autostart.
- Mobile approval center readiness exposes preview/readback/challenge
  contracts only. It cannot approve final actions, execute, call Hermes, Git,
  filesystem or browser directly.
- Deploy/email/payment candidate endpoints create external operation envelopes
  with risk, cost estimate, approval level, readback text, rollback or
  compensation plan, challenge phrase, expiration, audit id and evidence
  requirements.
- Budget guard v1 blocks spending by default, blocks unknown cost when spending
  is requested, blocks over per-action/monthly limits and consumes budget only
  from confirmed evidence.
- Revenue events separate projected from confirmed revenue. Confirmed revenue
  without evidence is rejected as fake revenue.
- Phase 5/6 voice approval readiness is exposed for eligible external
  operations only when there is a trusted device, active voice session, exact
  readback/challenge, expiration and audit. Double/triple-risk operations remain
  outside voice-only authorization.
- Dashboard read model, event stream and `/jarvis` debug drawer expose Phase 8
  status without secrets or direct execution controls.
- `scripts/jarvis_phase8_telegram_pilot.py` is a manual readiness script. It
  prints redacted status and refuses `--run` unless an explicit manual override
  env var is present; it still does not implement or start a real bot.

## What Remains Readiness

- Telegram bot runtime is not implemented in this phase. The existing Hermes
  gateway adapter remains the future integration point, but Phase 8 does not
  start polling or open a webhook.
- Deploy execution is not implemented. Candidates are dry-run/prepare-only and
  do not call Vercel, Render, Fly, Railway or any provider.
- Rollback is a declared plan field only unless the operator provides a real
  provider rollback contract in a future phase.
- Email sending is not implemented. Drafts are metadata/redacted previews and
  provider APIs are not called.
- Stripe integration is readiness only. Key mode is detected from env shape
  without exposing values, but no Checkout Session, product, price, charge,
  payout or refund is created.
- Mobile/PWA approval center UI is represented through cockpit/readiness status
  and drawer copy, not a full mobile app.
- Remote approval intent is accepted only as `accepted_pending_local_approval_bridge`.
  It does not grant approval or dispatch execution by itself.

## Endpoints

New Phase 8 endpoints:

- `GET /mark-3/phase-8/status`
- `GET /mark-3/remote-channels/status`
- `GET /mark-3/telegram-readiness/status`
- `GET /mark-3/mobile-approval-center/status`
- `POST /mark-3/remote-channels/pairing/challenge`
- `POST /mark-3/remote-channels/pairing/verify`
- `POST /mark-3/remote-channels/revoke`
- `POST /mark-3/remote-channels/kill-switch`
- `POST /mark-3/remote-channels/approval-intent`
- `GET /mark-3/external-operations/status`
- `POST /mark-3/external-operations/prepare-deploy`
- `POST /mark-3/external-operations/prepare-email`
- `POST /mark-3/external-operations/prepare-payment`
- `POST /mark-3/external-operations/revenue-event`
- `POST /mark-3/external-operations/budget-guard`
- `POST /mark-3/external-operations/voice-approval-readiness`

Existing dashboard endpoints now include Phase 8 state:

- `GET /mark-3/dashboard/status`
- `GET /mark-3/dashboard/events`
- `GET /mark-3/dashboard/events/stream`

There is still no `/execute` or `/jarvis/execute`.

## Remote Channel Rules

- Remote channels send intent into JARVIS Gateway/control plane only.
- Remote channels never call Hermes directly.
- Remote execution is disabled by default and no channel is execution-capable.
- Remote approval intent is limited, scoped, expiring and audited.
- Pairing is required for approval-capable channels.
- Revoked devices cannot approve.
- Remote kill switch blocks notifications and remote approval intents.
- There is no approve-all-forever scope.
- Public internet exposure and hidden background listeners are off by default.

## Telegram Rules

- Token presence is detected from `TELEGRAM_BOT_TOKEN`; token value is never
  returned, printed, logged or stored by Phase 8.
- Telegram remains disabled by default through `JARVIS_PHASE8_TELEGRAM_ENABLED`.
- `TELEGRAM_ALLOWED_USERS` is required before readiness can report
  `manual_pilot_ready`.
- Webhook mode is a contract when `TELEGRAM_WEBHOOK_URL` is present; polling is
  a readiness contract otherwise.
- Allowed future operations are notification, blocked-action notification,
  deploy/email/payment candidate notification, deny/cancel intent and receiving
  approval intent only after paired/trusted/challenged gates pass.
- Blocked operations include remote execute, free shell, direct Hermes call,
  approve-all-forever and provider secret read.

## Deploy Rules

- Deploy candidates include provider, redacted app/project id, environment,
  target, diff/build summary, required secret names, cost estimate, rollback
  availability, risk and approval requirement.
- Preview/staging candidates require strong approval before any future
  execution path.
- Production candidates require triple approval and remain disabled by default.
- No provider is called, no production deploy occurs, no DNS changes are made
  and no secret values are read.
- Unknown cost is a blocker or strong-approval escalation.

## Email Rules

- Email candidates are drafts/previews by default.
- Recipients are summarized/redacted; body/subject are redacted for sensitive
  markers; attachments are metadata-only.
- Personal identity use requires strong approval.
- Bulk/campaign send requires an explicit campaign envelope and compliance
  checklist.
- Send is disabled by default, provider APIs are not called and contact
  scraping is blocked.

## Payment And Stripe Rules

- Stripe readiness detects test/live/unknown mode from env key shape without
  exposing key values and without API calls.
- Payment candidates include product/price reference, amount, currency,
  recurring flag, approval level and blocked reasons.
- Test-mode candidates are allowed only as prepare-only/no-money-movement
  records.
- Live mode and money movement are blocked by default and require future
  triple/stronger governed execution before any provider call.
- No Checkout Session, charge, payout, refund, customer or subscription is
  created in this PR.
- Revenue events keep projected and confirmed revenue separate. Confirmed
  revenue requires evidence/source.

## External Operation Envelope

Every deploy/email/payment candidate creates an envelope with:

- `operation_id`
- category/provider/actor/requested channel
- risk and approval level
- side effects and cost estimate
- readback text and challenge phrase
- rollback or compensation plan
- status, audit id and expiration
- evidence requirements
- `execution_enabled=false`, `prepare_only=true`, `hermes_called=false`,
  `provider_called=false` and `metadata_only=true`

Remote approval intent can reference an envelope, but acceptance only records a
pending local approval bridge state. It does not grant approval and does not
execute.

## Budget Guard Rules

- Monthly budget and per-action maximum are explicit inputs.
- Unknown provider cost blocks or requires strong approval when spending is
  requested.
- Over-limit estimates block.
- Spending requires explicit approval.
- Budget consumed is based only on confirmed spend evidence, not estimates or
  claims.
- Every budget decision is audited as metadata.

## Voice Approval For External Operations

Voice can be ready for eligible external operations only when all gates are
present:

- trusted, non-revoked device;
- active voice session;
- exact readback;
- challenge phrase;
- risk/cost/scope summary;
- expiration;
- anti-replay;
- metadata-only audit.

Wake phrase alone never approves. Memory never grants permission. Double/triple
external operations are not voice-only eligible in Phase 8.

## Dashboard And UI

The dashboard read model includes:

- `phase_8_status`
- `remote_channels`
- `telegram_readiness`
- `mobile_approval_center`
- `external_operations`
- `external_budget_guard`

The event stream adds:

- `phase_8_state`
- `remote_channel_state`
- `external_operation_state`
- `budget_guard_state`
- `payment_provider_state`

The `/jarvis` drawer keeps this cockpit-style: it displays remote channel and
external operation readiness, safety gates, Stripe live block, budget behavior
and no-secret/no-direct-Hermes rules. It does not add an admin execution console.

## External Research

Network research was available. No external code was copied or vendored.

- `python-telegram-bot/python-telegram-bot`
  (https://github.com/python-telegram-bot/python-telegram-bot) - GPL-3.0,
  LGPL-3.0 and dual-license notices in repo. Inspected for async Telegram
  polling/webhook shape and rejected for this PR because starting a runtime
  would require credentials, public exposure decisions and stronger pilot ops.
- `aiogram/aiogram` (https://github.com/aiogram/aiogram) - MIT. Inspected for
  async Telegram framework pattern. Rejected for this PR for the same reason:
  Phase 8 should only define governed readiness contracts.
- Telegram Bot API (https://core.telegram.org/bots/api) - inspected
  `getUpdates` and `setWebhook` semantics, including polling/webhook exclusion
  and webhook secret-token support. Adopted only as readiness vocabulary.
- Vercel CLI deploy docs (https://vercel.com/docs/cli/deploy) - inspected
  `vercel deploy`, `--target` and `--prod` implications. Adopted only as
  candidate fields and production risk escalation.
- Stripe Checkout Session API docs
  (https://docs.stripe.com/api/checkout/sessions/create) and
  `stripe-samples/checkout-one-time-payments`
  (https://github.com/stripe-samples/checkout-one-time-payments) - MIT sample.
  Adopted only the future API recommendation to use Checkout Sessions for
  checkout/payment candidates.
- Resend Node SDK/docs (https://github.com/resend/resend-node and
  https://resend.com/docs/send-with-nodejs) - MIT SDK. Inspected for provider
  send shape and rejected for runtime use; Phase 8 keeps email as draft-only.

## Manual Validation

1. Start the API with the normal local environment.
2. Confirm `/execute` and `/jarvis/execute` are absent.
3. Open `GET /mark-3/phase-8/status` and verify all safety gates are false for
   direct Hermes, provider calls, remote execution, public exposure, live money,
   production deploy, email send and fake revenue.
4. Open `GET /mark-3/remote-channels/status` and verify remote execution is
   disabled and kill switch state is visible.
5. Set `TELEGRAM_BOT_TOKEN` to a dummy value, `TELEGRAM_ALLOWED_USERS=42` and
   `JARVIS_PHASE8_TELEGRAM_ENABLED=true`; open
   `GET /mark-3/telegram-readiness/status` and verify the token value is absent.
6. Run `python scripts/jarvis_phase8_telegram_pilot.py` and verify it prints
   redacted readiness only. Run with `--run` and verify it refuses unless the
   explicit manual override env var is set.
7. Create a remote pairing challenge, verify it with the exact phrase, then
   revoke the device and confirm later approval intent is rejected.
8. Prepare a staging deploy candidate and confirm it is dry-run/prepare-only.
9. Prepare a production deploy candidate and confirm it requires triple
   approval and still does not deploy, call a provider, change DNS or read
   secrets.
10. Prepare an email send candidate and confirm recipients/content are redacted,
    attachments are metadata-only and send/provider calls are false.
11. Prepare a Stripe live payment candidate and confirm live mode and money
    movement are blocked and no Checkout Session is created.
12. Record confirmed revenue without evidence and confirm it is rejected as fake
    revenue. Record confirmed revenue with evidence and confirm gross/fees/net
    are separated.
13. Evaluate budget guard with unknown cost and over-limit cost and confirm
    both block. Confirm estimates do not consume budget.
14. Check `/mark-3/dashboard/status`, `/mark-3/dashboard/events` and `/jarvis`
    for Phase 8 state with no secrets.

## Current Limitations

- Remote approval intent is not wired into final ApprovalGateway execution.
- There is no persistent remote channel registry beyond the Phase 5 identity
  device store and in-memory operation envelopes.
- Envelopes are in-memory and expire in-process; a future phase needs durable
  pending operation storage.
- Telegram notifications are readiness-only and do not send messages.
- Mobile approval center is not a standalone mobile app yet.
- Deploy/email/payment providers are not called.
- Rollback/compensation remains contractual except where a future provider
  adapter proves a real rollback.

## Next Recommended Macro-Phase

Phase 9 should turn one low-risk external operation into a real governed manual
pilot without widening the boundary:

- persist external operation envelopes and remote decisions;
- wire remote approval intent into the existing ApprovalGateway as a pending
  signal, not a final approval;
- implement notification-only Telegram send for approval pending/blocked events
  with token locks, allowed user IDs and explicit manual startup;
- add a mobile-friendly approval center view that can deny/cancel and display
  readback/challenge;
- pilot one test-mode provider flow, preferably Stripe Checkout Session
  creation in test mode only, with no live money and full evidence capture;
- add rollback/compensation evidence contracts before any real deploy pilot.
