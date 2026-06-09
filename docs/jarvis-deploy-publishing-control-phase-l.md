# JARVIS Deploy & Publishing Control - Phase L

Phase L adds a complete prepare-only Deploy & Publishing Control foundation. It turns caller-provided deployment
and publication intentions into reviewable previews without deploying, publishing, connecting domains or
accounts, changing DNS, requesting tokens, storing credentials, using identity, spending money, creating cloud
resources, running builds, calling external services, calling Hermes, creating ApprovalGateway requests, creating
missions/tasks, reading secrets, changing CI/deploy configuration, or mutating persistent state.

## What It Allows

- Inspect a fully disabled deployment/publication status and a default-deny policy.
- Preview deployment targets and identify production, paid-resource, domain, and identity risk.
- Preview a publication plan that remains blocked until a future readiness and approval flow exists.
- Preview domain and external-account requirements without connecting or verifying anything.
- Preview a production release and rollback plan without executing either.
- Prepare a conservative readiness checklist and approval requirements.
- Inspect prepare-only status, policy, readiness, and capability markers through Command Center and Operator Console.

## Safe API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/deploy-publishing/status` | Fully disabled prepare-only status |
| GET | `/deploy-publishing/policy` | Default-deny publication/deployment policy |
| POST | `/deploy-publishing/target-preview` | Preview a target and risk flags |
| POST | `/deploy-publishing/publish-plan` | Preview a blocked publication plan |
| POST | `/deploy-publishing/domain-preview` | Preview domain requirements without DNS/domain actions |
| POST | `/deploy-publishing/account-preview` | Preview account requirements without tokens/credentials |
| POST | `/deploy-publishing/production-preview` | Preview a blocked production release |
| POST | `/deploy-publishing/rollback-preview` | Preview rollback steps without rollback execution |
| POST | `/deploy-publishing/readiness-checklist` | Prepare required checks and missing items |
| POST | `/deploy-publishing/approval-requirements` | Calculate approval level without creating approval |

There are deliberately no publish, deploy, production-release, domain-connect, DNS-change, account-connect,
resource-create, payment, or rollback execution routes.

## Preview Examples

Deployment target:

```json
POST /deploy-publishing/target-preview
{"target_name": "review-host", "target_type": "cloud", "environment": "production"}
```

The response marks `production_target=true` and `strong_approval_required=true`, while keeping
`would_connect=false`, `would_create_resource=false`, `would_deploy=false`, `external_calls_enabled=false`, and
`secrets_required=false`.

Publication plan:

```json
POST /deploy-publishing/publish-plan
{"asset_reference": "asset-preview-1", "publish_destination": "review-host"}
```

Every publication plan returns `would_publish=false`, `would_deploy=false`, `blocked=true`,
`readiness_complete=false`, and strong approval required.

Domain and external account:

```json
POST /deploy-publishing/domain-preview
{"domain_requested": true, "domain_name": "example.invalid"}
```

```json
POST /deploy-publishing/account-preview
{"account_type": "hosting"}
```

The domain preview does not connect, change DNS, or verify ownership. The account preview does not connect,
request tokens, store credentials, or access secrets. Both require strong approval before any future real action.

Production and rollback:

```json
POST /deploy-publishing/production-preview
{"production_requested": true}
```

```json
POST /deploy-publishing/rollback-preview
{"rollback_steps_preview": ["Restore previous reviewed artifact"], "irreversible_risks": ["DNS propagation"]}
```

Production remains blocked and inaccessible. Rollback is required and auditable, but
`would_rollback=false` and `rollback_execution_enabled=false`.

Readiness and approval:

```json
POST /deploy-publishing/readiness-checklist
{
  "required_checks": ["Legal review", "Target review"],
  "domain_requested": true,
  "production_requested": true
}
```

```json
POST /deploy-publishing/approval-requirements
{"publish_requested": true, "production_requested": true}
```

Readiness always returns `ready_to_publish=false`. Strong approval is required before any future real publish or
deployment, and specifically for production, domains, paid resources, identity use, or secret access. Approval
requirements never call ApprovalGateway and never create, grant, or reject an approval.

## Integration Boundaries

Command Center exposes `deploy_publishing_control: prepare_only`. Operator Console can read the disabled status,
safe policy, and readiness placeholder and can advertise preview capability, but it cannot deploy, publish,
release production, connect domains/accounts, spend money, use identity, access secrets, approve, call Hermes, or
create ApprovalGateway requests.

Asset Factory provides reviewable asset references and publication-readiness inputs, but Phase L does not invoke
it or write generated assets. Sandbox Execution remains the future boundary for scoped build or deployment
commands, but Phase L does not invoke a sandbox or shell. Tool Adoption remains the future review boundary for
deployment adapters and dependencies, but Phase L installs and executes nothing.

This phase intentionally stops before real deployment and publication because those actions require external
connectivity, scoped credentials, identity/domain ownership, production controls, audit persistence, tested
rollback execution, and strong human approval. None of those execution paths exist in Phase L.
