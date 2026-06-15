# JARVIS Mark 3 Release Candidate + Pilot

## Meaning

PR #141 closes Mark 3 as a controlled Release Candidate. Mark 3 is
`ready_as_controlled_release_candidate`; it is not ready for free autonomy.
JARVIS remains local-first, human-controlled and audit-first.

Central rule:

```text
Restrictions are approval gates, not permanent bans.
```

If an action is legal, safe, authorized and technically supported, JARVIS may
prepare it and, where a real capability exists, route it through the appropriate
approval, scope, budget, audit and stop/rollback gates. Illegal, unsafe,
unauthorized, bypass, deceptive or fake-capability requests remain permanently
denied.

Hermes remains the execution engine. JARVIS governs, classifies risk, asks for
approval, audits and routes bounded tasks to Hermes only when real capability
and valid approval exist.

## Explicit RC Status

- `release_candidate_status`: `ready_as_controlled_release_candidate`
- `ready_as_controlled_release_candidate`: true
- `not_ready_for_free_autonomy`: true
- `local_first`: true
- `human_control_required`: true
- `restrictions_are_approval_gates_not_permanent_bans`: true

No real pilot is executed by this PR. No free autonomy, real scheduler,
external network, GitHub/web/providers, real email, Stripe live, deploy,
publish, domain, account access, credential use, dependency install or money
movement is enabled.

## Capability Matrix

`GET /mark-3/release-candidate/capabilities` consolidates:

- master planning;
- autonomous mission loop;
- governed Hermes runtime `read_file`;
- outcome/failure memory;
- learning proposals;
- growth radar;
- research execution control-plane;
- local docs/repo research adapter;
- product/revenue factory;
- local routine scheduler + personal/family ops;
- moonshot lab + research/experiment engine.

The matrix distinguishes prepare-only candidates from the real supported local
read slices. The governed Hermes `read_file` slice and local docs/repo adapter
are not free execution: they require exact scope, valid approval and their
specific guarded paths.

## Readiness Matrix

`GET /mark-3/release-candidate/readiness` declares Mark 3 ready as a controlled
RC, ready to prepare the first local pilot, and not ready for:

- free autonomy;
- default real provider execution;
- real scheduler or background 24/7 operation;
- production, money, email, deploy, domain, account, credential or publication
  operations without explicit setup and approvals.

## Dangerous Route Audit

`GET /mark-3/release-candidate/dangerous-route-audit` confirms there are no new
free routes for:

- research execute;
- experiment execute;
- real scheduler, cron or worker;
- send email;
- Gmail/Calendar/Contacts real access;
- login/account access;
- password storage;
- token/cookie/session material use;
- Stripe live, payment or checkout;
- deploy, publish or domain/DNS operations;
- install, subprocess, thread or network real operations;
- fake revenue, costs, benchmark, result or capability.

The existing `/mark-3/hermes-runtime/execute-read` route is treated separately:
it is an allowed gated route, not free autonomy. It requires a valid mission
candidate, approval, scope fingerprint and operator authorization.

## Approval Path Audit

`GET /mark-3/release-candidate/approval-path-audit` covers:

- Level 0-1: low-risk reasoning, plans, candidates and checklists.
- Level 2: scoped local read/repo/docs work.
- Level 3: external research, private metrics, AI CLI, sensitive authorized
  data and provider setup candidates.
- Level 4: production, money, identity, credentials, publication, deploy,
  domain/DNS and real email.
- Level 5: illegal, unsafe, unauthorized, bypass, deception and fake
  capability/result/revenue/cost/benchmark requests.

Approval is not execution. Permission does not create capability.

## E2E Prepare-Only/Gated Smoke

`GET /mark-3/release-candidate/e2e-smoke` creates in-memory candidates for:

- product/revenue;
- routine ops;
- moonshot lab;
- local docs research preview with exact scope.

It confirms:

- no side effects;
- no fake revenue, costs, results, benchmarks or capability;
- no execution by `research_id` alone;
- web/GitHub/providers remain not connected;
- Hermes remains the execution engine and is not duplicated.

## Pilot Plan

The first Mark 3 pilot is local, useful and controlled. It excludes production,
money, external network, real email, real accounts, credentials and free
autonomy. It captures scope, approvals, evidence, failures, real elapsed time
and real costs when measured.

The next safe step is to review the RC endpoints and then run the local
controlled pilot manually only after explicit operator approval. In short: the
local controlled pilot is the next action, not something PR #141 executes.

## Known Limitations

- no free autonomy;
- no real provider execution by default;
- no real scheduler yet;
- no cloud/VPS/Mac mini until revenue or technical need;
- no fake costs/revenue;
- no fake results, benchmarks, breakthroughs, completion or capability claims;
- no background 24/7 by default;
- no external account ops without explicit setup and approvals.

## Post-Mark-3 Next Steps

- run the controlled local pilot;
- harden findings from the pilot;
- start Mark 4 only if the pilot justifies it with evidence;
- avoid micro-PR explosion;
- no micro-PR explosion.
