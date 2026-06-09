# JARVIS Asset Factory / Web Builder - Phase K

Phase K adds a complete prepare-only Asset Factory / Web Builder foundation. It structures reviewable digital
asset plans from caller-provided inputs without publishing, deploying, creating domains, connecting accounts,
spending money, using a real identity, executing builds, installing dependencies, writing generated files,
calling external services, calling Hermes, creating ApprovalGateway requests, or mutating persistent state.

## What It Allows

- Inspect a fully disabled Asset Factory status and conservative generation policy.
- Prepare a web project brief while preserving unknowns and refusing to infer confirmed ROI.
- Prepare landing-page and website-structure plans.
- Preview copy/content packs with sensitive-input redaction and explicit anti-fabrication rules.
- Preview a static asset manifest without touching the filesystem.
- Preview a build package without installing, building, running, or changing package files.
- Preview publication readiness while keeping publication blocked.
- Preview a monetization offer without confirmed revenue, guarantees, payment setup, or payment calls.
- Inspect prepare-only markers and status/policy placeholders in Command Center and Operator Console.

## Safe API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/asset-factory/status` | Fully disabled prepare-only capability status |
| GET | `/asset-factory/policy` | Default-deny generation/publication policy |
| POST | `/asset-factory/web-brief` | Prepare a project brief |
| POST | `/asset-factory/landing-plan` | Prepare a landing-page plan |
| POST | `/asset-factory/website-structure` | Prepare pages, navigation, components, and data needs |
| POST | `/asset-factory/copy-pack` | Preview reviewable copy with anti-fabrication rules |
| POST | `/asset-factory/static-asset-manifest` | Preview future files/directories without writes |
| POST | `/asset-factory/build-package-preview` | Preview framework, dependencies, and build steps |
| POST | `/asset-factory/publishing-readiness` | Preview missing publication checks and approvals |
| POST | `/asset-factory/monetization-offer-preview` | Preview an offer/revenue hypothesis without payments |

There are deliberately no publish, deploy, domain, account-connection, payment, build, file-write, or run routes.

## Examples

Web project brief:

```json
POST /asset-factory/web-brief
{
  "project_name": "Reviewable demo",
  "audience": "Small teams",
  "problem": "Planning a clear landing page",
  "promise_or_value_proposition": "A concise, reviewable proposal",
  "monetization_hypothesis": "A subscription could be validated later"
}
```

The response keeps unprovided values and confirmed ROI as `unknown`, and always returns
`would_publish=false`, `would_deploy=false`, `would_spend=false`, and `would_use_identity=false`.

Landing and website structure previews:

```json
POST /asset-factory/landing-plan
{"hero": "A reviewable draft", "sections": ["Problem", "Offer", "FAQ"], "cta": "Review the proposal"}
```

```json
POST /asset-factory/website-structure
{"pages": ["Home", "FAQ"], "navigation": ["Home", "FAQ"], "static_dynamic_classification": "static"}
```

Landing plans explicitly prohibit income guarantees, fake testimonials, fake metrics, and fake legal claims.
Website structure plans default to no build, no deployment, and no external services.

Copy and static asset previews:

```json
POST /asset-factory/copy-pack
{"headlines": ["A clear draft"], "cta_copy": ["Review"], "disclaimer_copy": ["Results require validation"]}
```

```json
POST /asset-factory/static-asset-manifest
{"files_to_create": ["index.html", "assets/site.css"], "directories": ["assets"]}
```

Copy packs do not invent claims, testimonials, numbers, ROI, or income. Sensitive input is redacted. Static
asset manifests are names only: `would_write_files=false` and `would_overwrite_files=false`. Any future file
generation requires explicit filesystem scope, Sandbox Execution, and approval.

Build and publication previews:

```json
POST /asset-factory/build-package-preview
{"framework": "static html", "dependencies_preview": ["candidate-package"], "build_steps_preview": ["future build"]}
```

The response marks new dependencies for Tool Adoption review and keeps install, build, run, and package-file
modification disabled. It does not invoke Tool Adoption or Sandbox Execution.

```json
POST /asset-factory/publishing-readiness
{"required_checks": ["Legal review", "Identity approval"], "missing_items": ["Domain approval"]}
```

Publishing readiness always defaults to `ready_to_publish=false` and `publish_allowed=false`. Publication,
deployment, domains, paid resources, external accounts, and identity use remain outside Phase K. A future
publication path requires review and strong approval, but no such path exists here.

Monetization preview:

```json
POST /asset-factory/monetization-offer-preview
{"offer_name": "Draft offer", "pricing_hypothesis": "Test a price later", "revenue_hypothesis": "Unknown"}
```

This is a hypothesis only. It provides no fake ROI, confirmed revenue, income guarantee, payment setup, Stripe
call, or other payment call.

## Integration Boundaries

Command Center and Operator Console expose `asset_factory_web_builder: prepare_only`. Operator Console can read
the disabled status/policy and advertise preview capability, but cannot publish, deploy, spend, use identity,
write files, execute builds, approve actions, call Hermes, or create ApprovalGateway requests.

Phase K prepares contracts for future interaction with Phase I Sandbox Execution and Phase J Tool Adoption:
future file generation/build execution belongs in a scoped approved sandbox, and every new dependency requires
Tool Adoption review. Phase K invokes neither pipeline and creates only in-memory response DTOs.
