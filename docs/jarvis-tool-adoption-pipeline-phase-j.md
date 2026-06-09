# JARVIS Tool Adoption Pipeline - Phase J

Phase J adds a prepare-only evaluation layer for external tool candidates. It can structure caller-provided
information, identify unknowns and risky characteristics, prepare a sandbox proposal and spike plan, preview
value measurements, and produce a conservative adoption/keep/rollback decision.

It does not discover tools externally, clone repositories, install packages, run code, call a package manager,
execute a sandbox, access the network or secrets, call Hermes, create ApprovalGateway requests, create missions
or tasks, persist state, or add a tool as a core dependency.

## Safe API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/tools/adoption/status` | Fully disabled prepare-only capability status |
| POST | `/tools/candidate/profile` | Normalize a candidate profile and redact unsafe source URL content |
| POST | `/tools/license/review` | Prepare a license review without lookup or legal conclusion |
| POST | `/tools/repo-health/review` | Review only optional metadata supplied by the caller |
| POST | `/tools/dependency-risk/review` | Flag supplied native, binary, postinstall, network, or unknown dependencies |
| POST | `/tools/sandbox-install/proposal` | Prepare a blocked, approval-gated sandbox install proposal |
| POST | `/tools/spike/plan` | Prepare a bounded hypothesis, scope, metric, cost/time and rollback plan |
| POST | `/tools/value/preview` | Preserve supplied measurements without inventing ROI or revenue |
| POST | `/tools/adoption/decision-preview` | Preview reject/more-info/spike/blocked decisions and keep/rollback posture |

There are deliberately no `/tools/install`, `/tools/run`, `/tools/clone`, `/tools/adopt-core`,
`/tools/execute`, or `/tools/network` routes.

## Examples

Candidate profile:

```json
POST /tools/candidate/profile
{
  "tool_name": "Graphify",
  "source_url": "https://example.invalid/graphify",
  "declared_use_case": "Evaluate code graph review value"
}
```

The response keeps `license`, repository health, dependency/security risk and expected value as `unknown`;
sets `would_clone`, `would_install`, `would_execute`, and `would_become_core_dependency` to `false`; and blocks
adoption pending review and approval.

Dependency review:

```json
POST /tools/dependency-risk/review
{"dependencies": ["node-gyp native build", "postinstall download"]}
```

The response flags native, postinstall, and network characteristics, marks risk high, blocks the install
proposal, and requires strong approval. It does not call a package manager.

Spike plan:

```json
POST /tools/spike/plan
{
  "hypothesis": "The candidate reduces review time",
  "scope": "One synthetic fixture in an isolated future sandbox",
  "success_metric": "20 percent less review time",
  "max_time": "2 hours",
  "max_cost": "0",
  "rollback": "Discard isolated artifacts"
}
```

The response is a plan only. Real install or run remains disabled and requires approval first.

## Review And Decision Rules

- License review performs no external lookup and makes no legal conclusion. Missing, unknown, unclear, custom,
  or unlicensed status blocks adoption or needs more information. Commercial/proprietary licensing requires
  approval. Core adoption always requires strong approval.
- Repository health accepts optional caller metadata. Unknown values remain unknown; stars, forks, issues and
  activity are never invented.
- Dependency review accepts an optional list and flags native, binary, postinstall, network and unknown risk.
  High or unknown risk blocks an install proposal; high risk requires strong approval.
- Sandbox install proposals never install. They require an isolated sandbox, explicit filesystem scope, network
  blocked by default, secrets blocked, approval, strong approval, and rollback.
- Value previews preserve caller measurements. Unknown remains unknown, ROI is never fabricated, and revenue is
  not confirmed unless explicitly supplied by the caller.
- Adoption decision previews keep `keep_decision=false`, require a rollback plan, and keep core dependency
  adoption disabled. Install, execution, network, secrets, or core requests require strong approval and remain
  blocked.

Graphify, CodeGraph, Open Design, OpenClaw, and every other external tool are untrusted candidates until this
evaluation is complete. There is no silent core dependency path.

## Integrations

Command Center and Operator Console expose a `tool_adoption_pipeline: prepare_only` marker. Operator Console
can read the disabled status and preview the capability, but cannot install, execute, approve, call Hermes, or
adopt a core dependency.

Phase J relates to Sandbox Execution only by preparing a future proposal. It never invokes the sandbox.
Any future install/spike requires approval; core dependency adoption or execution with broad permissions
requires strong approval.
