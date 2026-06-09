# JARVIS Phase P - Continuous Learning / Tech Radar

Phase P adds a complete `prepare_only` foundation for reviewing technology candidates and planning
safe adoption proposals. It keeps JARVIS informed without enabling self-modification.

## Safety Boundary

Phase P can structure user-provided information, preserve unknowns, challenge claims, analyze risks,
prepare a learning backlog, and preview a possible PR plan. Every model and endpoint is local,
stateless, and side-effect free.

Phase P does **not**:

- perform external research or call external APIs
- clone repositories or install dependencies
- execute tools, shell commands, package managers, sandboxes, missions, or tasks
- read `.env`, credentials, or secrets
- call Hermes or `ApprovalGateway.create_request`
- update JARVIS, change runtime behavior, change prompts, or modify dependencies
- create branches, commits, pushes, or pull requests
- deploy or change CI/deploy configuration
- persist or schedule the learning backlog

`ContinuousLearningStatus` reports all operational capabilities as disabled.
`TechRadarSafetyPolicy` keeps auto-update, auto-install, auto-deploy, external research, secret
access, runtime changes, prompt changes, dependency changes, and PR creation denied by default.

Installs, runtime changes, prompt changes, production changes, deploys, credentials, and secrets
always require strong approval in previews. No real approval request is created.

## Safe API

Read-only status and policy:

- `GET /continuous-learning/status`
- `GET /continuous-learning/policy`

Local prepare-only previews:

- `POST /continuous-learning/candidate-profile`
- `POST /continuous-learning/relevance-filter`
- `POST /continuous-learning/contrarian-review`
- `POST /continuous-learning/proposal-preview`
- `POST /continuous-learning/impact-analysis`
- `POST /continuous-learning/risk-analysis`
- `POST /continuous-learning/pr-planner`
- `POST /continuous-learning/approval-workflow`
- `POST /continuous-learning/backlog-preview`
- `POST /continuous-learning/decision-preview`

There are intentionally no install, update, deploy, runtime modification, prompt modification,
external research, clone, execution, or real PR creation routes. No WebSocket is added.

## Tech Radar Flow

1. **Candidate profile:** records only supplied claims, maturity, license, risks, maintenance signal,
   use case, and revenue or efficiency hypothesis. It performs no lookup.
2. **Relevance filter:** compares the candidate with time saving, error reduction, monetization, and
   revenue enablement goals. Unknown values stay unknown and the result is not a final decision.
3. **Contrarian review:** forces skeptical questions, failure modes, hidden costs, security and
   maintenance concerns, vendor lock-in, overengineering, and recommendation-pressure review.
4. **Proposal preview:** requires expected impact, risks, dependencies, tests, rollback, a decision
   recommendation, and confidence. It never changes code or creates a PR.
5. **Impact and risk analysis:** separates hypotheses from confirmed evidence. Unresolved secret,
   production, runtime, or dependency risk blocks the proposal.
6. **PR planner:** previews branch name, likely files, tests, review, rollback, and migration notes
   without creating any git object.
7. **Approval workflow:** shows manual review steps and whether strong approval would be required.
8. **Backlog and decision:** prioritizes review work and recommends reject, keep watching,
   investigate, sandbox spike, propose PR, blocked, or unknown without automatic adoption.

## Examples

Candidate profile request:

```json
{
  "candidate_name": "Example technology",
  "category": "developer tooling",
  "source_reference": "user-provided note",
  "claimed_benefit": "reduce repetitive review",
  "maturity": "experimental",
  "license": "unknown"
}
```

Selected response fields:

```json
{
  "prepare_only": true,
  "candidate_name": "Example technology",
  "no_external_lookup": true,
  "would_install": false,
  "would_modify_runtime": false,
  "would_create_pr": false
}
```

Proposal preview request:

```json
{
  "candidate_name": "Example technology",
  "expected_impact": ["Possible manual time reduction; not measured"],
  "risks": ["Dependency risk unknown"],
  "dependencies": ["example-package"],
  "tests_required": ["Unit tests", "security review"],
  "rollback_plan": ["Revert reviewed change"],
  "decision_recommendation": "investigate"
}
```

Selected response fields:

```json
{
  "prepare_only": true,
  "decision_recommendation": "investigate",
  "would_create_pr": false,
  "would_modify_code": false,
  "approval_required": true
}
```

Risk analysis request:

```json
{
  "dependency_risk": "unknown",
  "security_risk": "high",
  "production_risk": "unknown"
}
```

Selected response fields:

```json
{
  "prepare_only": true,
  "blocked": true,
  "strong_approval_required": true
}
```

Impact analysis never invents ROI. `no_confirmed_roi` remains `true` unless a caller explicitly
provides reviewed ROI evidence and sets `confirmed_roi_explicitly_provided=true`.

## Product Prioritization

The relevance filter and backlog are designed to prioritize candidates that may save time, reduce
errors, improve quality, reduce cost, or enable revenue. These are hypotheses until evidence is
explicitly provided. Phase P never turns an estimate or claim into confirmed ROI.

## Integration Boundaries

- **Command Center:** exposes `continuous_learning_tech_radar: prepare_only`.
- **Operator Console:** exposes prepare-only status, safety policy, backlog readiness, and read/preview
  capabilities. It cannot execute, approve, install, update, deploy, or create PRs.
- **Tool Adoption:** a future approved proposal may hand off a reviewed tool candidate, but Phase P
  never invokes the adoption pipeline or installs anything.
- **Sandbox Execution:** a future approved sandbox spike may be planned, but Phase P never runs a
  sandbox or external code.
- **Daily Operator:** may later surface review cadence and backlog reminders, but Phase P does not
  schedule or persist them.
- **Mission Core:** may later coordinate approved work, but Phase P creates no missions or tasks.

Phase P stops at supervised research structure and proposal planning. Applying any change remains a
separate, explicitly approved engineering workflow.
