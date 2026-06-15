# JARVIS Mark 3 Pilot Findings Hardening

## Context

PR #142 hardens findings from the first controlled Mark 3 pilot runs. Pilot 0
found that several Mark 3 control-plane surfaces overblocked safe payloads when
dangerous words appeared inside defensive limits, false flags, stop conditions,
or prohibited-tool lists. Pilot 0B confirmed the same flows work when payloads
avoid those defensive words.

The fix does not weaken safety. It makes the parser distinguish actionable
dangerous intent from negative, defensive, or bounded context.

PR #143 extends this hardening for the real Mission Loop endpoint after the API
restart on main showed one residual overblock: the full defensive Pilot 0
payload sent to `POST /mark-3/mission-loop/missions` could still return
`intake implies permanently denied level 5 action`. The remaining issue was
Mission Loop text classification, not an execution path.

## Parser Contract

Mark 3 now uses a shared negative-intent parser for the affected control-plane
surfaces. It treats these as safe context when no actionable request is present:

- explicit false flags such as `credentials_requested: false`,
  `payment_requested: false`, `password_storage_requested: false`, and
  `execute_experiment_requested: false`;
- limits such as `no credentials`, `without credentials`, `do not read .env`,
  `no network`, and `sin red`;
- stop conditions such as `stop if credentials are requested`;
- free-text stop-condition renderings such as `Any action requests credentials`
  or `Any result claims fake capability`;
- prohibited tools and out-of-scope lists;
- `no_` scope prefixes such as `no_credentials`, `no_external_network`,
  `no_money`, `no_email`, `no_production`, and `no_deploy`;
- defensive compliance phrases such as `no fake revenue`,
  `sin inventar ingresos`, `do not claim results`, and `deny fake capability`.

The same parser still blocks real unsafe requests, including:

- reading `.env`, secrets, tokens, credentials, cookies, sessions, passwords, or
  secret-like access material;
- storing passwords or using cookie/token/session material;
- bypass, evasion, unauthorized access, phishing, impersonation, or theft;
- fake revenue, fake costs, fake benchmarks, fake research results, fake
  capabilities, fake completion, or deceptive claims;
- direct requests such as `deploy production now`, `send real email now`, and
  `move money`;
- broader production, money, deploy, real email, identity, scheduler, provider,
  and account actions remain governed by the existing risk model unless the
  request is one of the permanently denied categories above.

## Surfaces Hardened

- Mission Loop intake and classification.
- Product/Revenue Factory.
- Local Routine Scheduler + Personal/Family Ops.
- Moonshot Lab + Research/Experiment Engine.
- Governed Research Execution preview and candidate policy.

## Safety Invariants

This PR adds no execution endpoint. It does not enable network, GitHub, web,
providers, subprocess, threading, installs, deploy, email, scheduler, money,
Stripe, accounts, `.env`, credentials, or another Hermes runtime.

PR #137 local docs/repo exact-scope reads remain bounded by the existing local
adapter. Candidate by `research_id` alone still cannot rehydrate a prior preview
into execution.
