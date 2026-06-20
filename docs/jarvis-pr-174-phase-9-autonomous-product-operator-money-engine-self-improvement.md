# PR #174 - Phase 9 Autonomous Product Operator, Money Engine & Self-Improvement

Status: implemented as a governed prepare-only product-operator control plane.

Phase 9 turns the existing JARVIS governed capability platform into a safer
personal product-operations planner. It can shape product missions, produce
candidate product packages, score opportunities, plan experiments, track
truthful revenue evidence, evaluate spend, propose JARVIS improvements and
generate operator reports. It does not publish, deploy, email, charge money,
move money, scrape, commit, push, open PRs, merge, call Hermes directly from the
frontend or run hidden background loops.

The implementation lives in `jarvis/phase_9_product_operator.py` and is exposed
through `/mark-3/product-operator/*` API routes, dashboard status, event stream
state and the `/jarvis` cockpit.

## Core Contract

JARVIS governs. Hermes executes. Phase 9 only prepares governed product
operation candidates and hands sensitive work back to the existing Phase 7 and
Phase 8 contracts.

Hard invariants:

- no unlimited mission;
- no approve-all-forever;
- memory never grants permission or expands budget;
- wake phrase never approves;
- voice approval is eligible only with trusted device, active voice session,
  exact readback, challenge phrase, scope, expiration and audit;
- PolicyEngine, ApprovalGateway, restriction registry, budget guard and audit
  remain required for sensitive work;
- frontend never calls Hermes directly;
- no generic `/execute` or shell-freeform product endpoint;
- no live Stripe charge, checkout, payout, refund or money movement;
- no real email send, mass email, external publication or production deploy by
  default;
- no DNS changes or public internet exposure by default;
- no fake product launch, fake customer, fake revenue, fake provider result or
  fake rollback;
- no self-merge, self-deploy, commit, push, PR creation or merge by Phase 9.

## Autonomous Product Mission Envelope v1

`create_mission_envelope()` validates product missions for work such as niche
validation, micro-SaaS candidate preparation, landing copy, local scaffold
planning, pricing, deploy/email/payment candidates, experiment tracking and
iteration proposals.

Required fields:

- `mission_id`;
- `title`;
- `goal`;
- `expected_outcome`;
- `target_user_customer`;
- `hypothesis`;
- `success_metric`;
- `budget_limit`;
- `time_limit_seconds` or bounded `time_limit`;
- `scope`;
- `allowed_tools_actions`;
- `forbidden_actions`;
- `approval_level`;
- `risk`;
- `status`;
- `evidence`;
- `stop_conditions`;
- `audit_id`;
- `expires_at`.

The validator rejects missing scope, missing budget, missing time limit, missing
stop conditions, missing expiration, blanket approval language and unsupported
dangerous/fake requests. Created envelopes include readback text, a challenge
phrase, audit id and explicit booleans that show bypasses are not allowed.

## Product Builder v1

`prepare_product_builder()` creates a governed candidate package:

- product idea brief;
- problem statement;
- target customer;
- value proposition;
- competitor/alternative notes;
- landing structure;
- feature scope and MVP checklist;
- tech-stack recommendation;
- build plan;
- asset package;
- local scaffold plan;
- deploy candidate;
- pricing candidate;
- email/campaign candidate;
- Stripe/payment candidate;
- launch checklist.

When `local_project_path` is provided, Phase 9 prepares candidate Markdown file
payloads and calls Phase 7 filesystem previews with
`filesystem.file.write_safe`. It does not write files itself. If Phase 7 is not
available, files remain preview-only in the candidate package.

Deploy, email and payment candidates are prepared through the Phase 8 control
plane when available. Provider calls, sends, publishes, deploys, checkouts and
charges remain disabled.

## Money / ROI Engine v1

`evaluate_roi()` scores opportunities using:

- opportunity score;
- expected upside;
- effort estimate;
- cost estimate;
- time-to-market;
- confidence;
- risks;
- dependencies;
- human time required;
- net benefit per David-hour;
- decision state.

Supported decision states:

- `reject`;
- `watch`;
- `prepare`;
- `build candidate`;
- `launch candidate`;
- `needs approval`;
- `blocked`.

Revenue fields are separated:

- projected revenue;
- confirmed revenue;
- gross revenue;
- fees;
- costs;
- net revenue;
- evidence/source;
- confidence.

Projected revenue is always labelled as a projection and never counted as
confirmed. Confirmed revenue requires evidence/source. Unknown cost blocks or
requires strong approval. Spend remains recommendation-only until an approved
external operation exists.

## Experiment Planner v1

`plan_experiment()` prepares product/business tests such as:

- landing idea validation;
- Reddit post draft;
- cold email draft;
- Google Trends/manual research checklist;
- directory/listing strategy;
- no-code/manual sales test;
- local prototype test.

The model includes `experiment_id`, hypothesis, channel, target audience, asset
needed, cost cap, time window, success metric, expected signal, action plan,
approval requirement, status, evidence and next step.

It never posts, emails, scrapes, publishes or spends by default. External
channels are marked approval-required and routed as Phase 8 candidates.

## Revenue Tracker v1

`record_revenue_event()` and `revenue_summary()` implement a truthful local
revenue tracker.

Supported event types:

- `projected`;
- `confirmed`;
- `refund`;
- `cost`;
- `fee`;
- `net_calculation`.

Each event stores amount, currency, source, evidence, timestamp, confidence,
linked product, linked mission, linked experiment and audit id.

Confirmed revenue without evidence is downgraded to
`unconfirmed_missing_evidence` and is not counted. Projected revenue is not
counted as confirmed. Net revenue is calculated as:

```text
net = gross - fees - costs - refunds
```

No metric is invented. Missing evidence keeps revenue projected or unconfirmed.

## Budget Guard / Spend Control v2

`evaluate_budget_guard()` extends the Phase 8 budget contract for product work.

It supports:

- global monthly product budget;
- per-mission budget;
- per-action spending limit;
- provider cost estimate;
- unknown cost handling;
- hard stop when over budget;
- approval requirement;
- audit.

JARVIS can recommend spending but cannot spend. Unknown provider cost blocks or
requires strong approval. Over-limit costs hard-stop. Confirmed spend consumes
budget only when evidence is provided. Memory/preferences cannot expand budget.

## Self-Improvement Proposal System v1

`propose_self_improvement()` lets JARVIS prepare safe improvement candidates for
itself:

- inspect docs/contracts;
- propose improvements;
- create improvement candidates;
- prepare patch plans;
- prepare tests;
- prepare PR description preview;
- score expected value;
- identify risks;
- ask for approval.

It blocks attempts to remove or weaken PolicyEngine, ApprovalGateway, audit,
tests, permissions or governance. It cannot commit, push, open PRs, merge,
auto-deploy or self-merge.

## Operator Scheduler / Daily Report v1

`generate_operator_report()` creates manual/readiness reports:

- daily operator report;
- weekly product report;
- pending approval report;
- budget report;
- revenue report;
- experiment report;
- blocker report;
- recommended next actions.

There is no hidden background scheduler by default. Reports do not notify,
email or execute anything. Future automation must be attached to an approved,
scoped product mission envelope.

## Product Operating Loop v1

`prepare_operating_loop()` defines the safe loop:

```text
observe -> propose -> plan -> prepare_assets -> request_approval ->
execute_allowed_local_actions -> gather_evidence -> report -> learn ->
propose_next_step
```

The loop requires an existing product mission envelope, inherits its stop
conditions, time limit and budget limit, is stoppable and never runs forever.
External side effects require Phase 8 approval. Local file work goes through
Phase 7.

## Integration

Phase 7:

- local project package generation uses `filesystem.file.write_safe` previews;
- Phase 9 does not create a new runtime or bypass governed filesystem actions.

Phase 8:

- deploy, email and payment outputs are candidate envelopes only;
- budget guard and voice approval readiness reuse external-op safety rules;
- provider calls remain disabled by default.

Voice / identity:

- product operation voice approval readiness requires trusted device, active
  session, exact readback, challenge, scope, expiration and audit;
- double/triple/blocked/denied product operations are not voice-eligible.

Audit:

- every mission, builder candidate, ROI decision, experiment, revenue event,
  budget check, self-improvement proposal, report, operating-loop preparation
  and voice-readiness check writes a metadata-only persistent audit event.

Dashboard / event stream / UI:

- `/mark-3/phase-9/status`;
- `/mark-3/product-operator/status`;
- product operator summary in `/mark-3/dashboard/status`;
- event types for Phase 9 state, missions, builder, ROI, experiments, revenue,
  self-improvement and reports;
- `/jarvis` finance cockpit card exposing read-only status and safety lines.

## API Endpoints

- `GET /mark-3/phase-9/status`
- `GET /mark-3/product-operator/status`
- `POST /mark-3/product-operator/missions`
- `POST /mark-3/product-operator/builder`
- `POST /mark-3/product-operator/roi-decision`
- `POST /mark-3/product-operator/experiments`
- `POST /mark-3/product-operator/revenue-events`
- `GET /mark-3/product-operator/revenue-summary`
- `POST /mark-3/product-operator/budget-guard`
- `POST /mark-3/product-operator/self-improvement`
- `POST /mark-3/product-operator/reports`
- `POST /mark-3/product-operator/operating-loop`
- `POST /mark-3/product-operator/voice-approval-readiness`

These are product-operation control-plane endpoints, not free execution
endpoints.

## What Is Real vs Readiness

Real:

- deterministic product mission envelope validation;
- prepare-only product builder candidates;
- Phase 7 filesystem preview integration;
- Phase 8 deploy/email/payment candidate integration;
- ROI scoring with cost, effort, confidence and risk inputs;
- projected vs confirmed revenue separation;
- confirmed revenue evidence requirement;
- budget guard v2 for unknown/over-limit cost;
- prepare-only experiment plans;
- governed self-improvement proposals;
- manual operator reports;
- stoppable operating-loop contract;
- metadata-only audit and dashboard/event-stream visibility.

Readiness:

- no durable product-operator persistence beyond the process-local control
  plane and persistent audit entries;
- no autonomous background scheduler;
- no real launch, deploy, email send, publication, scrape, checkout, charge,
  payout, refund or money movement;
- no real provider execution or rollback;
- no automatic worktree mutation, commit, push, PR, merge or self-deploy;
- no real customer/revenue validation without David-provided evidence.

## Public Research Notes

Network search was available. Repos/libraries inspected:

- `wasp-lang/open-saas` - MIT license. Useful as a conceptual SaaS packaging
  reference. No code adopted because Phase 9 should not scaffold a public SaaS
  runtime or imply production launch readiness.
- `growthbook/growthbook` - mixed license: GrowthBook Enterprise License for
  enterprise paths and MIT Expat elsewhere. Useful as an experiment-tracking
  reference. No code adopted because Phase 9 only needs a lightweight local
  prepare-only experiment contract.
- `langchain-ai/langgraph` - MIT license. Useful as a conceptual state-machine
  reference. Rejected as a runtime dependency because JARVIS already has an
  autonomous mission loop and Hermes execution contract.
- `temporalio/samples-typescript` - MIT license. Useful as a durable workflow
  reference. Rejected for this PR because no hidden scheduler or new runtime is
  allowed.
- arXiv "A Self-Improving Coding Agent" - conceptual reference for
  improvement proposals. No implementation adopted; Phase 9 keeps
  self-improvement prepare-only and approval-gated.

## Validation

Recommended local validation:

```bash
source venv/bin/activate
python -m pytest tests/jarvis/test_pr_174_phase_9_product_operator.py -q
python -m pytest \
  tests/jarvis/test_pr_170_phase_5_local_controller_identity_voice.py \
  tests/jarvis/test_pr_171_phase_6_real_voice_wake_memory_sensor_runtime.py \
  tests/jarvis/test_pr_172_phase_7_governed_actions.py \
  tests/jarvis/test_pr_173_phase_8_governed_remote_external_ops.py -q
python -m pytest tests/jarvis/ -q
cd web && npm run build
```

Manual validation:

1. Start the local API with the normal JARVIS development command.
2. Open `GET /mark-3/phase-9/status` and confirm `prepare_only` is true.
3. Create a mission envelope with budget, time limit, scope and stop
   conditions; confirm missing fields return an error.
4. Prepare a product builder candidate with `local_project_path`; confirm Phase
   7 previews exist and no files were written by Phase 9 directly.
5. Record projected revenue and confirmed revenue without evidence; confirm only
   evidenced confirmed revenue counts.
6. Evaluate unknown and over-limit spend; confirm `can_spend` is false.
7. Prepare a self-improvement proposal that tries to weaken governance; confirm
   it is blocked.
8. Open `/jarvis`; confirm Phase 9 appears as read-only cockpit state, not an
   execution console.

## Next Recommended Phase

Stabilization / release-candidate work should focus on durable product-operator
state, explicit ApprovalGateway handoff for selected product candidates,
end-to-end UI tests, one test-mode-only provider pilot and a manual scheduler
runner that is off by default. Live external operation should remain excluded
until the approval bridge, rollback/stop plans, budget evidence and audit
queries are exercised end-to-end.
