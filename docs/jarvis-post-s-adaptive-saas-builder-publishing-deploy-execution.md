# Post-S Macro 9 - Product Builder Adaptativo / Adaptive SaaS Builder

## Qué consolida

Esta macro de **Mark 1** convierte una idea en un producto SaaS publicable y
desplegable como candidato controlado:

```text
idea -> nicho -> validación -> diferenciación -> MVP -> arquitectura adaptativa
-> pricing -> blueprint -> scaffold plan -> landing -> publishing plan
-> deploy plan -> execution candidate -> launch readiness
```

Este trabajo no es Phase T y no crea Phase T. Phase S continúa siendo la última
fase maestra.

## Por qué no es Template Builder

El nombre obligatorio es **Product Builder Adaptativo / Adaptive SaaS Builder**.
Los patrones reutilizables y capability blocks son guardrails componibles, no
plantillas rígidas. Auth, pagos, base de datos, API o admin solo entran cuando
el producto los justifica. Cada blueprint exige problema, público, propuesta de
valor, diferenciación, razón para existir, MVP concreto, monetización, métrica,
riesgos, assumptions y unknowns.

Regla de calidad: **si dos productos parecen hermanos gemelos, el builder ha
fallado**. Un producto genérico, clonado o parecido a boilerplate falla el
quality gate y debe refinarse o rechazarse antes de publicar o desplegar.

## Flujo adaptativo

- `ProductIdeaIntake` conserva incertidumbre y no inventa audiencia, presupuesto
  o timeline.
- `ProductValidationPreview` actúa como abogado del diablo, no inventa demanda
  y recomienda `proceed`, `refine` o `reject`.
- `DifferentiationReview` detecta template risk, clone risk y decisiones poco
  específicas.
- `CapabilityBlockPlan` compone solo los bloques justificados.
- `SaaSProductBlueprint` limita el MVP y conecta pricing con el Monetization
  Engine sin presentar revenue estimado como confirmado.
- `TechStackRecommendation` prioriza coste bajo, declara servicios de pago y no
  asume credenciales.
- `RepoScaffoldPlan` describe archivos, tests, comandos y secretos requeridos
  sin crear repo ni escribir archivos.
- `LandingPagePlan` prepara copy vendible sin claims falsos.
- `PublishingPlan` y `DeployExecutionPlan` preparan checks, secretos, rollback y
  approvals sin publicar ni desplegar.
- `ProductExecutionCandidate` representa una acción futura, no su ejecución.
- `LaunchReadinessReview` bloquea launch sin diferenciación, legal, privacidad,
  seguridad, approval o rollback de producción.

## Approval-controlled execution

**Restrictions are approval gates, not permanent bans.**

Por defecto no se crean repos, no se escriben scaffolds, no se publica, no se
despliega, no se toca producción, no se leen credenciales y no se llaman
plataformas externas. Una acción legal, segura, autorizada y soportada puede
quedar elegible tras aprobación válida y todas las gates.

- Repo externo, filesystem sensible y otras acciones sensibles requieren strong
  approval cuando corresponda.
- Publicación o deploy de producción requieren strong approval y doble
  confirmación.
- Producción requiere rollback.
- Ilegal, inseguro, no autorizado, imposible o unsupported permanece denegado.
- Wake phrase, scheduler due y memory active pueden iniciar previews, pero no
  conceden permiso.

PR #122 aporta default-deny, valid approval, strong approval, doble confirmación,
permanent denial, warnings y eligibility. PR #123 aporta pricing readiness,
budget guard, payment approval y Stripe readiness sin inventar revenue. PR #118
y PR #119 siguen aportando readiness/candidates; no ejecutan deploy ni llaman
GitHub, browser o APIs desde esta macro.

## Ejemplos

- Idea simple: intake explícito -> validación -> blueprint diferenciado y MVP
  acotado.
- Presupuesto desconocido: `budget_limit` permanece `null` y aparece en
  `unknowns`.
- Producto sin diferenciación: `refine` o `reject`.
- Producto parecido a plantilla: `quality_gate_passed=false`.
- Deploy staging sin aprobación: blocked.
- Deploy producción con aprobación normal: blocked por falta de strong approval
  y doble confirmación.
- Deploy producción con strong approval, doble confirmación, gates y rollback:
  candidato elegible, pero no se ejecuta en esta PR.

## Endpoints control-plane

- `GET /product-builder/status`
- `GET /product-builder/policy`
- `POST /product-builder/preview-intake`
- `POST /product-builder/preview-validation`
- `POST /product-builder/preview-differentiation`
- `POST /product-builder/preview-capability-blocks`
- `POST /product-builder/preview-blueprint`
- `POST /product-builder/preview-stack`
- `POST /product-builder/preview-scaffold`
- `POST /product-builder/preview-landing`
- `POST /product-builder/preview-publishing`
- `POST /product-builder/preview-deploy`
- `POST /product-builder/preview-execution-candidate`
- `POST /product-builder/preview-launch-readiness`
- `POST /product-builder/preview-action`

No existen rutas de create-repo, write-files, publish, deploy, execute, run,
call-github, call-vercel, call-render, call-stripe, auto-approve o approve-all.

## Qué no ejecuta esta PR

No crea una app SaaS real, repos reales ni scaffolds externos. No publica
servicios, no despliega producción, no llama GitHub/Vercel/Render/Cloudflare/
Stripe, no usa red, no lee `.env`, no usa credenciales, no mueve dinero y no
ejecuta subprocess.

## Próxima macro

**Post-S Macro 10 — Mark 1 Hardening, E2E Real Ops & Release Candidate**

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_post_s_adaptive_saas_builder_publishing_deploy_execution.py -q
pytest tests/jarvis -q -x --durations=20
```
