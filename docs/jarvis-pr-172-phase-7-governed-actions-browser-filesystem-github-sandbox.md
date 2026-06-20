# PR #172 - Phase 7 Governed Actions, Browser, Filesystem, GitHub & Sandbox

Date: 2026-06-20

## Summary

Phase 7 turns governed action readiness into a local pilot for useful actions
while preserving the core boundary:

```text
JARVIS governs, classifies risk, asks approval, audits, stops and controls.
Hermes executes only behind existing JARVIS-governed execution paths.
```

This phase does not add `/execute`, shell-freeform execution, direct frontend
Hermes calls, hidden filesystem writes, hidden browser automation, credential
entry, purchases, posting, deploys, email sending, money movement, production
publication, Git commit/push/PR/merge, fake providers, fake metrics or fake
rollback.

## What Is Real

- Action Catalog v2 is exposed from the existing governed execution catalog.
  Every action includes action id, title, category, risk, approval requirement,
  allowed input schema, side effects, filesystem/network/GitHub/browser/sandbox
  flags, stop/rollback contract, dry-run availability, audit requirements,
  voice approval eligibility and default enabled state.
- Safe filesystem adapter v1 can read one non-secret UTF-8 text file, list one
  directory as metadata, and create/update one safe text file inside explicit
  allowed roots.
- Filesystem writes create a diff preview, require approval, create a backup
  before overwrite under `.jarvis/phase_7_backups`, audit the backup/write and
  do not return raw written content.
- Secret/preflight scanning blocks or redacts `.env`, secret-like paths, API
  keys, tokens, private keys, passwords, Stripe live keys, payment/production
  markers and destructive operation markers.
- Git/worktree adapter v1 runs fixed read-only local git commands for status,
  worktree status, changed files and diff summaries. It also prepares branch
  names and PR description text locally.
- Sandbox execution v1 supports command plans, dry-runs and execution only for
  fixed command IDs with `shell=False`, sanitized environment, timeout and
  redacted stdout/stderr.
- Phase 5/6 spoken approval can authorize eligible Phase 7 actions only through
  trusted, non-revoked devices, active voice session requirements, exact
  readback, challenge when required, expiry, anti-replay and audit.
- Dashboard status, event stream and `/jarvis` expose Phase 7 catalog/adapters,
  preflight state, pending previews, stop/rollback availability and what is real
  versus readiness without exposing secrets.

## What Remains Readiness

- Browser automation is a governed plan/readiness adapter only. It returns
  Playwright-compatible plan metadata and evidence metadata, but does not launch
  a visible browser yet.
- Browser click/submit remains plan-only and strong-approval scoped. It does
  not perform external side effects.
- Local branch/worktree mutation remains disabled in this PR workflow.
- Delete is dry-run-only.
- The sandbox runner is guarded local subprocess execution, not an OS-level
  sandbox such as bubblewrap or nsjail.
- Commit, push, opening PRs and merge remain prepare-only/disabled unless a
  future workflow explicitly adds stronger approval and permits them.

## Endpoints

New Phase 7 endpoint:

- `GET /mark-3/phase-7/status`

Existing governed action endpoints now expose Phase 7 actions:

- `GET /mark-3/execution/action-catalog`
- `GET /mark-3/execution/status`
- `POST /mark-3/execution/preview`
- `POST /mark-3/execution/request-approval`
- `POST /mark-3/execution/approval-decision`
- `POST /mark-3/execution/dispatch`
- `GET /mark-3/dashboard/status`
- `GET /mark-3/dashboard/events`
- `GET /mark-3/dashboard/events/stream`

There is still no `/execute` or `/jarvis/execute`.

## Action Catalog Rules

- The catalog is allowlist-only.
- There is no generic command or generic browser action.
- Risk and approval level are recalculated server-side.
- Memory never grants permissions or downgrades risk.
- Wake phrase alone never approves.
- High/browser-submit style actions require strong approval or remain plan-only.
- Critical/double/triple behavior remains governed by existing stronger approval
  rules and cannot be silently downgraded.
- Unsupported or forbidden actions are marked unsupported/denied rather than
  faked as successful.

## Filesystem Rules

- Allowed roots are explicit: current working directory plus
  `JARVIS_PHASE7_ALLOWED_ROOTS` entries.
- Path traversal, `~`, null bytes, out-of-root paths and symlink paths are
  blocked.
- `.env`, secret, token, password, credential, private key and similar paths are
  blocked by default.
- Reads are limited to safe text files and perform content preflight before
  returning content.
- Directory lists are metadata-only and redact secret-like entries.
- Writes require preview, diff, approval, preflight and audit.
- Overwrites create a backup first.
- Delete remains dry-run-only.

## GitHub And Worktree Rules

- Real actions are local read-only git helpers with fixed argv and no network:
  status, worktree status, changed files and diff summary.
- Branch names and PR descriptions are prepared locally for human review.
- GitHub API is not called in this phase.
- Commit, push, PR open, merge and real branch/worktree mutation are disabled or
  dry-run-only for this PR workflow.
- Frontend never calls GitHub or Hermes directly.

## Browser Automation Rules

- Browser adapter is governed by JARVIS policy, preview, approval and audit.
- It produces visible-browser-required plans and evidence metadata.
- It does not launch a hidden browser.
- It does not capture or store credentials.
- It does not buy, pay, post, publish or submit externally.
- Credential entry and private-account scraping are blocked by default.
- Future execution must use a visible Playwright-compatible runner with exact
  scope, readback, approval and evidence capture.

## Sandbox Rules

- The UI and API accept command IDs, not raw shell.
- Allowed command IDs are fixed in `SANDBOX_COMMANDS`.
- Commands run with `shell=False`, sanitized env, limited timeout and working
  directory allowlist.
- Inherited secrets are disabled.
- Output is redacted and truncated.
- `python -m py_compile` and targeted pytest commands require explicit path or
  target allowlisting.
- No general process rollback is claimed.

## Preflight Rules

Preflight reports:

- redacted findings;
- severity;
- blocking reason;
- approval recommendation;
- metadata-only audit id.

Preflight blocks secrets and destructive markers. Production/payment markers
escalate approval recommendation and remain visible as findings without
exposing raw secrets.

## Voice Approval For Actions

Spoken approval is valid only when all existing Phase 5/6 gates pass:

- trusted non-revoked device;
- device scoped for `voice_approval`;
- active voice session where required;
- exact readback;
- exact action id/scope/cost context;
- challenge phrase for strong/high risk;
- expiration;
- anti-replay;
- metadata-only audit.

Wake phrase alone cannot approve. Memory cannot approve. Voice cannot authorize
actions marked voice-ineligible in the catalog.

## External Research

No external network research or code adoption was performed for this PR in this
worktree. The implementation used repo-local contracts and conservative
standard-library patterns only. Candidate libraries for future validation remain
Playwright, browser-use, Skyvern, GitPython, detect-secrets, TruffleHog,
Gitleaks, Semgrep, OPA, Cedar, bubblewrap, nsjail, nox/tox and pytest safe
runners. No external code was copied.

## Manual Validation

1. Start the API with the normal local environment.
2. Confirm `/execute` and `/jarvis/execute` are absent.
3. Open `GET /mark-3/phase-7/status`.
4. Confirm `GET /mark-3/execution/action-catalog` reports catalog version 2 and
   Phase 7 action keys.
5. Set `JARVIS_PHASE7_ALLOWED_ROOTS` to a test workspace.
6. Preview and dispatch `filesystem.file.read_text` for a safe text file.
7. Preview and dispatch `filesystem.directory.list` and confirm `.env` entries
   are redacted.
8. Preview reading `../outside.txt` and a `.env` file and confirm both deny.
9. Preview `filesystem.file.write_safe`, review diff, request approval, approve
   and dispatch. Confirm backup-before-overwrite exists.
10. Try writing a Stripe live key and confirm preflight denies and redacts it.
11. Dispatch `github.repo.status` and `github.diff.summary`; confirm no network
   or GitHub API call occurs.
12. Preview branch creation and confirm it is disabled/dry-run-only.
13. Preview browser open/screenshot/fill/click actions and confirm no browser
   launches; click/submit stays strong-approval plan-only.
14. Preview an arbitrary sandbox command id such as `rm -rf /`; confirm it is
   rejected before dispatch.
15. Preview and approve `sandbox.command.run_allowlisted` with `git_status`;
   confirm `shell=false`, sanitized env and redacted output.
16. Pair a trusted voice device, create an eligible filesystem write approval,
   approve by voice with exact readback/challenge and dispatch.
17. Revoke the device and confirm further voice approval is blocked.
18. Open `/jarvis` and confirm Phase 7 appears as cockpit/readiness state, not
   as a dense execution/admin console.

## Next Recommended Macro-Phase

PR #173 should validate a real visible browser runner and stronger local
sandbox isolation:

- connect a visible Playwright runner behind the Phase 7 browser plan contract;
- add screenshot/evidence artifact storage with redaction and expiry;
- keep credential entry, purchases, posting and private scraping blocked;
- evaluate bubblewrap/nsjail or a platform-specific sandbox for local commands;
- expand filesystem write rollback into a governed restore action;
- add real manual pilot evidence from David's machine before widening action
  scope.
