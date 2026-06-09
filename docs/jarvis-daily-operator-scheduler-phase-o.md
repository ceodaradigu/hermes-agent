# JARVIS Phase O - Daily Operator / Scheduler

Phase O adds a complete `prepare_only` foundation for reviewing daily briefings, plans, schedule
rules, recurrence, task queues, reminders, execution windows, retry policies, handoffs, and approval
requirements. It operates only on request data and returns deterministic previews.

It does not create or run a scheduler.

## Safety boundary

Every status, policy, preview, API route, Command Center marker, and Operator Console field remains
prepare-only. Phase O does **not**:

- create cron jobs, systemd timers, background workers, queues, missions, or tasks;
- execute, retry, catch up, enqueue, dequeue, pause, resume, or persist scheduled work;
- send reminders, notifications, emails, DMs, posts, or calendar events;
- connect to or read an external calendar;
- call Hermes, ApprovalGateway, external services, subprocesses, shells, or package managers;
- read `.env`, tokens, credentials, secrets, or external account data;
- publish, deploy, spend, charge, move money, or modify runtime/CI/deploy configuration.

Strong approval is required before any future real background execution, recurring execution,
external notification, external calendar action, money-related task, or publish/deploy task. Phase O
records that requirement only. It never creates or decides an approval.

## API

Read-only status and policy:

- `GET /daily-operator/status`
- `GET /daily-operator/policy`

Prepare-only previews:

- `POST /daily-operator/briefing-preview`
- `POST /daily-operator/daily-plan`
- `POST /daily-operator/schedule-rule`
- `POST /daily-operator/recurrence-preview`
- `POST /daily-operator/task-queue-preview`
- `POST /daily-operator/reminder-preview`
- `POST /daily-operator/execution-window`
- `POST /daily-operator/retry-policy`
- `POST /daily-operator/handoff-summary`
- `POST /daily-operator/approval-requirements`

There are no run, execute, worker, cron, timer, send, calendar-connect, queue mutation, or WebSocket
routes.

## Daily briefing and plan

A briefing uses only explicitly provided data:

```json
POST /daily-operator/briefing-preview
{
  "date": "2026-06-09",
  "timezone": "Europe/Madrid",
  "source_data": "provided",
  "priorities": ["Review Phase O"],
  "blocked_items": ["Approval needed for future publication"]
}
```

The response always declares `no_external_calendar_read: true`, `no_external_calls: true`,
`would_notify: false`, and `would_execute: false`.

```json
{
  "prepare_only": true,
  "source_data": "provided",
  "no_external_calendar_read": true,
  "no_external_calls": true,
  "would_notify": false,
  "would_execute": false
}
```

A daily plan can organize focus blocks, task candidates, priority order, effort, dependencies, and
approval blockers. It never creates tasks, schedules tasks, or executes them.

## Schedule rule and recurrence

A schedule rule can describe `once`, `daily`, `weekly`, `monthly`, `manual`, or `unknown` cadence,
plus start time, timezone, allowed window, and quiet hours. It never creates a scheduler, cron job,
system timer, worker, or execution. Daily, weekly, and monthly cadence requires strong approval for
any future activation.

Recurrence preview can describe a recurrence rule, next-run preview, maximum runs, and stop
condition. It never persists a schedule or executes recurring work and always records strong
approval as required.

```json
POST /daily-operator/schedule-rule
{
  "rule_name": "Morning review",
  "cadence": "daily",
  "start_time": "09:00",
  "timezone": "Europe/Madrid"
}
```

```json
{
  "prepare_only": true,
  "cadence": "daily",
  "would_create_scheduler": false,
  "would_create_cron": false,
  "would_create_system_timer": false,
  "would_register_worker": false,
  "would_execute": false,
  "approval_required": true,
  "strong_approval_required": true
}
```

## Task queue and reminders

Task queue preview presents user-provided queue items, execution order, and blocked items. Queue size
is derived in memory. It never enqueues, dequeues, executes, persists, calls Hermes, or calls
ApprovalGateway.

Reminder preview supports `none`, `local`, `email`, `push`, `calendar`, and `unknown` as descriptive
channels. It never sends. Email, push, and calendar previews require strong approval for any future
real action. Secret-like message or recipient input is redacted.

## Execution window and retry policy

Execution window preview can describe an allowed start/end, timezone, quiet hours, and maximum
runtime. It is blocked by default, respects quiet hours, and never starts a worker or executes.

Missed-run/retry policy preview can describe maximum retries and backoff. Retry and catch-up remain
disabled. A future retry of a side-effect task requires strong approval.

## Operator handoff

Operator handoff summary preview structures completed items, pending items, risks, approvals needed,
and next actions. It never notifies, persists, or executes.

## Product integration

Command Center exposes `daily_operator_scheduler: prepare_only`.

Operator Console exposes:

- prepare-only Daily Operator status and scheduler safety policy;
- read and preview capabilities only;
- disabled background execution, task execution, approval creation, Hermes, network, secrets,
  notifications, external calendar, and persistence.

Mission Core may supply future reviewable mission/task references, but Phase O does not create or
execute them. Payments & Revenue tasks involving money require strong approval. Marketing &
Distribution tasks involving notification, sending, posting, or paid activity require strong
approval. Deploy & Publishing tasks involving publishing or deployment require strong approval.
None of those actions are enabled by this phase.

Phase O intentionally stops before real scheduling because real activation requires durable
persistence, audited lifecycle controls, cancel/pause/resume behavior, worker isolation, concurrency
control, missed-run semantics, notification credentials, external-calendar authorization, and a
strong-approval execution bridge. Those capabilities remain outside this safe foundation.
