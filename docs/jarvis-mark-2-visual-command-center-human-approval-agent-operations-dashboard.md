# JARVIS Mark 2 Macro 3 - Visual Command Center, Human Approval Console & Agent Operations Dashboard

## Qué añade

Mark 2 Macro 1 cerró daemon local, desktop runtime, wake listener preparado,
kill switch, stop phrase y Voice Approval Channel. Mark 2 Macro 2 cerró la
preparación gobernada de candidates para filesystem, GitHub, browser y APIs.

Mark 2 Macro 3 añade el modelo visual, estado operacional y endpoints de datos
para un dashboard operativo. Define paneles listos para una UI futura donde
David pueda entender qué está preparado, bloqueado, pendiente de approval,
unknown o listo para revisión. No implementa un frontend final pesado.

**Restrictions are approval gates, not permanent bans.** Esta PR muestra y
prepara esas gates; no ejecuta.

## Paneles preparados

- System Status, agents, sessions y AI coding sessions.
- Costes, consumo, límites manuales/unknown, budget y ROI unknown.
- Pending approvals, riesgos y tool execution candidates.
- Diffs, tests, reviews, worktree guard y next safe actions.
- Audit timeline seguro y redactado.
- Kill switch, stop control, aprobación por voz y por texto.

`VisualCommandCenterStatus` declara que la capa de datos está disponible, pero
el frontend real, ejecución de agentes, invocación AI CLI, red y access
material permanecen desactivados.

## Agents y sesiones AI

El Agent Operations Dashboard representa PlannerAgent, BuilderAgent,
ReviewerAgent, TesterAgent, ResearcherAgent, OperatorAgent, CodexCliAgent,
ClaudeCodeAgent, ClaudeCoworkAgent, ApiFallbackAgent y LocalScriptAgent. Todos
muestran rol, estado, proveedor, quién paga, cost mode, sandbox, worktree,
branch, riesgo, bloqueos y siguiente paso. Ninguno puede ejecutar ahora.

Codex CLI, Claude Code, Claude Cowork y API fallback son adapters gobernados por
JARVIS, no cerebros libres. JARVIS debe clasificar misión, estimar riesgo,
aplicar PolicyEngine/ApprovalGateway, preparar worktree/sandbox, recoger
diff/tests/review, auditar y pedir approval antes de push, merge, deploy,
producción o dinero. Esta PR solo muestra previews; no lanza procesos reales,
no automatiza webs, no usa cookies y no guarda login ni access material.

## Costes, consumo y límites

El Cost Usage Dashboard separa API usage, subscription, local compute y
unknown. Una subscription consume límites de suscripción, no coste API por
unidad. API usage solo puede estimarse con datos explícitos. Local compute
puede mostrar coste directo 0, pero hardware y energía quedan unknown.

Muestra quién paga: David API billing, ChatGPT subscription, Claude
subscription, local machine o unknown. No consulta billing real, no inventa
gasto real ni límites disponibles, y marca unknown/manual input required cuando
faltan datos. Todos los registros declaran `no_fake_costs`.

## Approval, riesgo y audit

Human Approval Console muestra approvals pendientes y qué falta: canal,
readback, frase requerida, strong approval, doble/triple confirmación,
expiración, audit y stop/rollback plan. Sus acciones son preview-only.

La voz puede aprobar mediante Voice Approval Channel explícito, con readback,
contexto exacto, expiración y confirmaciones requeridas. Una wake phrase solo
abre una sesión: la wake phrase nunca aprueba.

Risk Panel cubre producción, dinero, access material, filesystem, GitHub,
browser, external API, privacidad, legal y unknown. Audit Timeline solo
presenta resúmenes seguros y redactados.

Worktree Guard y Diff/Test/Review Panel no ejecutan git ni llaman GitHub. Si no
reciben evidencia, muestran estado unknown y `safe_to_finish_pr=false`.

## Endpoints control-plane

Todos son GET read-only:

- `/mark-2/dashboard/status`
- `/mark-2/dashboard/overview`
- `/mark-2/dashboard/panels`
- `/mark-2/dashboard/agents`
- `/mark-2/dashboard/sessions`
- `/mark-2/dashboard/costs`
- `/mark-2/dashboard/approvals`
- `/mark-2/dashboard/risks`
- `/mark-2/dashboard/worktree-guard`
- `/mark-2/dashboard/diffs-tests-reviews`
- `/mark-2/dashboard/audit`
- `/mark-2/dashboard/next-actions`

No existen rutas para ejecutar agentes, lanzar Codex/Claude real, leer entorno,
usar sesiones de proveedor, approve-all, auto-approve, deploy, pagos, push o
merge. Ningún endpoint llama red, consulta billing, mueve dinero, despliega,
publica o aprueba realmente acciones críticas.

## Siguiente macro

Mark 2 no está completo. La siguiente macro es **Mark 2 Macro 4 — Real Deploy,
Stripe, Email, External Operations & AI CLI Adapters**, siempre bajo approval,
audit, permission gates, sandbox/worktree y stop controls.

PR #129 implementa Macro 4 y alimenta este dashboard con external operations
status, deploy/Stripe/email/domain candidates, adapters Codex/Claude/Cowork/API
fallback y Routine Execution Bridge. Costes y límites siguen unknown/manuales
cuando no existe evidencia; no se consulta billing ni se inventan costes.

PR #130 consolida esta Macro 3 dentro de Mark 2 Release Candidate. Dashboard,
approval console, agent operations, costes, worktrees, tests, review y audit
quedan listos como control-plane, con no fake costs y sin autoridad de
ejecución.

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_mark_2_visual_command_center_human_approval_agent_operations_dashboard.py -q
pytest tests/jarvis -q -x --durations=20
```
