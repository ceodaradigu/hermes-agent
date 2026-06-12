# JARVIS Mark 2 Macro 4 - Real Deploy, Stripe, Email, External Operations & AI CLI Adapters

## Qué añade

Mark 1 quedó cerrado como Release Candidate. Mark 2 Macro 1 preparó daemon
local, wake listener, desktop runtime y Voice Approval Channel. Macro 2 preparó
tool execution gobernado. Macro 3 hizo visibles agentes, sesiones, approvals,
riesgos, costes, worktrees, tests y audit. Macro 4 añade candidatos de
operaciones externas y adapters AI CLI gobernados. No completa Mark 2.

**Restrictions are approval gates, not permanent bans.** Una operación legal,
segura, autorizada y soportada puede quedar `eligible_after_valid_approval`.
Ilegal, inseguro, no autorizado, imposible o unsupported permanece como
permanent denial.

## Preview, candidate y gated execution

- **Preview:** describe qué ocurriría; nunca ejecuta.
- **Candidate:** prepara riesgo, gates, approval, coste, audit y rollback/stop.
- **Gated execution:** puede quedar elegible tras approval válida; la invocación
  real sigue disabled by default.
- **Blocked/permanent denial:** explica gates pendientes o límites permanentes.
- **Manual handoff:** David realiza login, configura access material o confirma
  directamente en el proveedor cuando sea necesario.

## Operaciones externas

`DeployOperationCandidate` prepara targets, build/deploy command previews,
preflight, smoke tests, healthcheck y rollback. Producción es critical y exige
strong approval, doble confirmación y rollback.

`StripeOperationCandidate` prepara checkout, prices, customers, subscriptions,
refunds, charges y webhooks. Stripe live es critical. Money movement exige
strong approval y doble/triple confirmación. Test mode sigue gated por red y
access material. Nunca llama Stripe ni mueve dinero.

`EmailOperationCandidate` permite draft preview y candidatos de send/reply/bulk.
Send requiere approval; contenido sensible, bulk o marketing requiere strong
approval. Recipients y body se resumen/redactan. Nunca usa Gmail/SMTP real.

`DomainPublishingCandidate` prepara DNS, domain connect, landing publishing y
custom domains. DNS/custom domain requiere strong approval; producción requiere
doble confirmación y rollback/unpublish plan. Nunca modifica DNS ni publica.

## AI CLI adapters y Routine Execution Bridge

Codex CLI y Claude Code son herramientas supervisadas para trabajo pesado en
worktree/sandbox. Deben devolver diff, tests, review y summary. No hacen commit,
push, merge o deploy. Claude Code no habilita hooks peligrosos ni MCP externos
sin approval.

Claude Cowork/Desktop es una rutina local supervisada para review, browser
assist, documentos o formularios. No envía formularios, maneja dinero, toca
producción ni sustituye una API estable 24/7.

API fallback sirve para JSON estable, clasificación, workers, automatización
24/7 y fallback. Requiere red, access material, approval y budget guard. Su
cost mode es `api_tokens`, pero no se inventa coste ni se consulta billing.

`RoutineExecutionBridge` elige según misión, riesgo y coste: local first cuando
sea posible, subscription CLI para desarrollo pesado y API para JSON estable,
workers, 24/7 o fallback. Siempre conserva `would_execute=false`.

## Seguridad, approvals, costes y audit

JARVIS no usa cookies, no roba tokens, no usa session tokens, no automatiza las
webs de ChatGPT/Claude y no guarda access material. Login y configuración de
proveedor son manual handoff. Costes, pagador y usage limits se muestran como
estimados, manuales o unknown; **no fake costs**.

Acciones sensibles requieren strong approval. Producción y dinero requieren
doble confirmación; riesgo muy alto puede exigir triple confirmación. Voice
Approval Channel puede satisfacer approval solo con estado válido, readback,
contexto, expiración y confirmaciones. Una wake phrase nunca aprueba. Kill
switch y stop phrase bloquean/cancelan candidates.

`ExternalOperationAuditEvent` registra actor, canal, proveedor, riesgo,
approval, coste, red, impacto, adapter y rollback/stop plan con contenido
redactado. Siempre registra `executed=false`, `external_call_made=false`,
`money_moved=false` y `production_touched=false`.

## Endpoints control-plane

- `GET /mark-2/external-ops/status`
- `GET /mark-2/external-ops/policy`
- `POST /mark-2/external-ops/preview-deploy`
- `POST /mark-2/external-ops/preview-stripe`
- `POST /mark-2/external-ops/preview-email`
- `POST /mark-2/external-ops/preview-domain`
- `GET /mark-2/ai-cli/status`
- `POST /mark-2/ai-cli/preview-codex`
- `POST /mark-2/ai-cli/preview-claude-code`
- `POST /mark-2/ai-cli/preview-claude-cowork`
- `POST /mark-2/ai-cli/preview-api-fallback`
- `POST /mark-2/routine-execution/preview`
- `GET /mark-2/external-ops/audit-preview`

No existen rutas para deploy/pago/email/DNS real, lanzamiento real de AI CLI,
uso de cookies/session tokens, auto-approval, approve-all o ejecución libre.

## Siguiente macro y tests

La siguiente macro es **Mark 2 Release Candidate Hardening**.

PR #130 cierra después Mark 2 como Release Candidate controlado. Macro 4 queda
consolidada, pero deploy, Stripe live, email send, domain publish y AI CLI real
siguen desactivados por defecto y requieren manual setup más approvals válidos.

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_mark_2_real_deploy_stripe_email_external_ops_ai_cli_adapters.py -q
pytest tests/jarvis -q -x --durations=20
```
