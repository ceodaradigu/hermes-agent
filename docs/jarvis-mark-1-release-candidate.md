# JARVIS Mark 1 Release Candidate

## Qué significa cerrar Mark 1

Mark 1 queda consolidado como release candidate funcional, seguro, documentado
y operable desde control-plane. No significa que JARVIS esté terminado para
siempre ni que la ejecución externa real esté activa.

Phase S sigue siendo la última fase maestra. No existe Phase T. Después de Phase
S, el trabajo se organiza mediante macro-PRs grandes dentro de Mark 1, Mark 2 y
Mark 3.

## Qué incluye

- governance global, audit, approval hardening y permission gates;
- semántica approval-controlled: **Restrictions are approval gates, not permanent bans.**
- controlled runtime bridge y tool invocation layer;
- memory, Personal OS, scheduler y stop controls;
- wake voice y camera control-plane local/opt-in;
- Monetization Engine, budget guard y Stripe readiness preview;
- Product Builder Adaptativo / Adaptive SaaS Builder;
- publishing/deploy plans y execution candidates;
- Operational Console, Command Center y Operator Console;
- smoke E2E real-ops seguro, documentación y runbook.

Una acción legal, segura, autorizada y soportada puede quedar elegible tras
aprobación válida y todas las gates. Acciones sensibles requieren strong
approval. Acciones críticas, como deploy de producción, Stripe live, pagos,
publicación externa o activación real de sensores, requieren strong approval y
doble confirmación. Audit, permission gates, context fingerprint cuando aplique
y rollback/stop plan cuando aplique siguen siendo obligatorios.

## E2E real-ops seguro

`Mark1E2ERealOpsSmoke` recorre:

```text
idea -> validación contrarian -> diferenciación -> blueprint -> pricing
-> revenue projection -> budget guard -> publishing/deploy candidates
-> approval decision -> critical warning -> launch readiness
```

Incluso con aprobación simulada válida, el resultado puede ser
`eligible_after_valid_approval=true`, pero conserva `would_execute=false`. No
crea repos, no escribe filesystem externo, no llama GitHub/Vercel/Render/Stripe,
no usa credenciales, no publica, no despliega y no mueve dinero.

## Qué no incluye

Mark 1 no incluye daemon local real, wake listener real de micrófono, UI visual
avanzada, ejecución profunda real de tools, browser/GitHub/filesystem externos
reales, Stripe live, deploy automático real, infraestructura 24/7, multiagente
avanzado ni aprendizaje continuo autónomo.

Las primeras capacidades pertenecen a Mark 2. Multiagente avanzado,
aprendizaje continuo y operación 24/7 pertenecen a Mark 3.

Mark 2 Macro 1 empieza en PR #126 con una base local desactivada por defecto:
daemon, desktop runtime, wake listener preparado y approval por voz. Esto no
cambia el estado cerrado de Mark 1 ni significa que Mark 2 esté completo.
PR #127 inicia Mark 2 Macro 2 con requests/candidates y adapters seguros de
tools, sin activar ejecución externa libre ni completar Mark 2.
PR #128 inicia Mark 2 Macro 3 con datos estructurados para dashboard visual,
approval console y agent operations, sin frontend final ni ejecución real.
PR #129 inicia Mark 2 Macro 4 con deploy/Stripe/email/domain candidates,
adapters Codex/Claude/Cowork/API fallback y Routine Execution Bridge. Toda
invocación externa real permanece desactivada y Mark 2 aún no está completo.

PR #130 cierra posteriormente Mark 2 como Release Candidate controlado. Esto no
modifica el cierre de Mark 1 ni convierte Mark 2 en autonomía libre. El
siguiente paso pasa a Mark 3 planning o a un piloto Mark 2 con setup manual y
approvals válidos.

## Endpoints

Todos son GET, read-only y control-plane:

- `/mark-1/status`
- `/mark-1/capabilities`
- `/mark-1/e2e-smoke`
- `/mark-1/dangerous-route-audit`
- `/mark-1/approval-path-audit`
- `/mark-1/docs-status`
- `/mark-1/runbook`
- `/mark-1/known-limitations`
- `/mark-1/next-plan`

No existen rutas Mark 1 de execute, run, deploy, publish, pay, charge,
create-repo, write-files, auto-approve o approve-all.

## Roadmap

Mark 2 añade daemon/wake/desktop real, tools reales, UI y approval console,
deploy/Stripe/email reales y su release candidate hardening. Mark 3 añade
multiagente, aprendizaje continuo, opportunity/product/growth engine e
infraestructura 24/7 con monitorización, recuperación y control de costes.

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_post_s_mark_1_hardening_e2e_real_ops_release_candidate.py -q
pytest tests/jarvis -q -x --durations=20
```
