# JARVIS Mark 3 Operational Runbook

## Local Verification

Work from the main repo or the current dedicated pilot-hardening worktree. Use
the known good venv:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
```

Verify the read-only RC endpoints:

- `GET /mark-3/release-candidate/status`
- `GET /mark-3/release-candidate/capabilities`
- `GET /mark-3/release-candidate/readiness`
- `GET /mark-3/release-candidate/dangerous-route-audit`
- `GET /mark-3/release-candidate/approval-path-audit`
- `GET /mark-3/release-candidate/e2e-smoke`
- `GET /mark-3/release-candidate/pilot-plan`
- `GET /mark-3/release-candidate/runbook`
- `GET /mark-3/release-candidate/known-limitations`
- `GET /mark-3/release-candidate/next-steps`

These endpoints are control-plane/read-only. They do not run the real pilot.

## Validation Commands

```bash
git diff --check
python -m py_compile $(find jarvis -name '*.py')
pytest tests/jarvis/test_mark_3_pilot_findings_hardening.py -q -x --durations=20
pytest tests/jarvis/test_mark_3_release_candidate_pilot.py -q -x --durations=20
pytest tests/jarvis/test_mark_3_moonshot_lab_research_experiment_engine.py -q -x --durations=20
pytest tests/jarvis/test_mark_3_local_routine_scheduler_personal_family_ops.py -q -x --durations=20
pytest tests/jarvis/test_mark_3_product_revenue_factory.py -q -x --durations=20
pytest tests/jarvis/test_mark_3_research_execution_bridge.py -q -x --durations=20
pytest tests/jarvis/test_mark_3_autonomous_mission_loop.py -q -x --durations=20
pytest tests/jarvis/test_api.py::test_health_ok -q -vv
pytest tests/jarvis -q -x --durations=20
```

## Pilot Rules

The first pilot must be:

- local;
- useful;
- controlled;
- explicitly approved;
- non-production;
- no money;
- no external network;
- no real email;
- no real accounts;
- no credentials;
- no free autonomy;
- no real scheduler.

Allowed surfaces:

- Mark 3 planning/status;
- mission loop control-plane;
- product/revenue prepare-only candidates;
- routine ops prepare-only candidates;
- moonshot lab prepare-only candidates;
- research execution preview for exact local docs/repo scope;
- governed Hermes `read_file` only when exact candidate, path, approval, scope
  fingerprint and operator authorization exist;
- outcome/failure memory and learning proposal previews.

Disallowed in the first pilot:

- GitHub/web real calls;
- providers real calls;
- real scheduler, cron, worker, watcher or 24/7 background operation;
- email send;
- Gmail, Calendar, Contacts, login or account access;
- password storage;
- cookie, token or session material use;
- Stripe live, checkout, payment or money movement;
- deploy, publish, DNS, domain or production changes;
- install, subprocess, thread or unbounded execution;
- reading `.env` or credentials.

## Evidence

Capture:

- mission objective and exact scope;
- risk level and approval requirement;
- allowed and disallowed tools;
- candidate payload summaries;
- blocked reasons, missing requirements and setup_required states;
- exact local evidence references if a local read is approved;
- elapsed time and real costs, or `unknown` when not measured;
- post-mortem, failure memory and learning proposal candidate.

Do not invent revenue, costs, benchmarks, research results, completion or
capability.

## Stop Conditions

Stop immediately if:

- scope, budget, allowed tools or risk level would be exceeded;
- a candidate asks for network, provider, email, scheduler, account,
  credential, deploy, publish or money action;
- exact local scope is missing, broad, sensitive, symlinked, path-traversing or
  multi-scope;
- any output fakes revenue, costs, benchmarks, results, completion, evidence or
  capability;
- operator stop or kill switch is requested.

## Closing The PR

After implementation, tests and review pass, close outside Codex with:

```bash
jarvis-finish-pr "Mark 3 Pilot Findings Hardening"
```

Do not commit, push, merge or open a PR from Codex unless explicitly instructed.
