# Post-S Macro 7 - Global Approval-Controlled Execution Semantics & Mark Roadmap

## Qué corrige esta macro

Esta macro corrige la semántica global de JARVIS:

**Restrictions are approval gates, not permanent bans.**

JARVIS no es prepare-only para siempre. El estado actual sigue siendo
control-plane/preview y no ejecuta acciones reales, pero los contratos declaran
que una acción legal, segura, autorizada y técnicamente soportada puede quedar
elegible para ejecución después de una aprobación válida y de pasar todas las
gates.

Este trabajo es transversal post-Phase S. No es Phase T y no crea Phase T.
Phase S sigue siendo la última fase maestra implementada.

## Semántica global

- Default-deny: sin aprobación válida, `execution_allowed=false`.
- Acciones normales: aprobación explícita válida más todas las gates.
- Acciones sensibles: strong approval válida más todas las gates.
- Acciones críticas: strong approval, doble confirmación y todas las gates.
- Auditoría, context fingerprint cuando aplique y permission gates son
  obligatorios.
- Rollback o stop plan es obligatorio cuando sea posible y requerido.
- Una aprobación nunca salta legalidad, seguridad, autorización o capacidad
  técnica real.
- Acciones ilegales, inseguras, no autorizadas, imposibles o unsupported
  producen `permanent_denial=true`, incluso si David las solicita o aprueba.

`safe_to_execute` y `safe_to_invoke` significan elegibilidad/readiness después
de gates, no ejecución real. En esta macro `execution_enabled=false`,
`would_execute=false` y todos los endpoints son control-plane/preview.

## Ejemplos

- Deploy de producción sin aprobación: bloqueado.
- Deploy de producción con aprobación normal: bloqueado; requiere strong
  approval y doble confirmación.
- Deploy de producción con strong approval, doble confirmación, fingerprint,
  permisos, auditoría y rollback válidos: `execution_allowed=true` como
  elegibilidad; esta macro no realiza el deploy.
- Acción ilegal aunque David la pida: `permanent_denial=true`.
- `"Hola Jarvis, despliega producción"`: wake detecta la orden, pero wake phrase
  no es permiso y el deploy exige strong approval y doble confirmación.
- Scheduler due no es permiso y memoria activa no es permiso.

## Avisos críticos

`CriticalActionWarning` presenta sistema afectado, consecuencias posibles,
coste estimado opcional, dificultad de reversión, disponibilidad de rollback y
frase de doble confirmación para producción, Stripe live, pagos/gastos, email
masivo, publicación externa, credenciales, filesystem sensible, GitHub,
browser, cámara/micrófono y otras operaciones reales delicadas.

## API control-plane

- `GET /approval-execution/status`
- `GET /approval-execution/policy`
- `POST /approval-execution/preview-decision`
- `POST /approval-execution/preview-critical-warning`
- `GET /roadmap/marks`

Estas rutas no ejecutan, no llaman tools, red, GitHub, browser, APIs externas,
Stripe, email, credenciales, sensores ni producción.
Los booleanos enviados a `preview-decision` son assertions de simulación, no
approval records autoritativos. Sus gates usan defaults conservadores y PR #117
sigue siendo la autoridad real de approval, strong approval, expiración,
revocación, context fingerprint y audit.

## Roadmap por Marks

### Mark 1

JARVIS funcional, seguro y ejecutable bajo aprobación. Núcleo completo: policy,
approvals, runtime, tools, memoria, voz, monetización, builder, deploy
controlado y release candidate.

- PR #122 - Global Approval-Controlled Execution Semantics & Mark Roadmap
- PR #123 - Monetization Engine Real
- PR #124 - SaaS/Product Builder + Publishing/Deploy Execution
- PR #125 - Mark 1 Hardening, E2E Real Ops & Release Candidate

### Mark 2

Ejecución real profunda: daemon local, wake real, UI seria,
browser/GitHub/filesystem/tools reales, Stripe/deploy/email reales bajo
aprobación y desktop/runtime real.

- Mark 2 Macro 1 - Local Daemon, Real Wake Listener & Desktop Runtime
- Mark 2 Macro 2 - Real Tool Execution: Browser, GitHub, Filesystem & APIs
- Mark 2 Macro 3 - Visual Command Center UI & Human Approval Console
- Mark 2 Macro 4 - Real Deploy, Stripe, Email & External Operations
- Mark 2 Release Candidate Hardening

### Mark 3

Autonomía avanzada: multiagente, aprendizaje continuo, operación 24/7,
infraestructura, monitorización, recuperación, optimización de costes y mejora
continua.

- Mark 3 Macro 1 - Multi-Agent Operating System
- Mark 3 Macro 2 - Continuous Learning & Self-Improvement Loop
- Mark 3 Macro 3 - Autonomous Opportunity, Product & Growth Engine
- Mark 3 Macro 4 - 24/7 Infrastructure, Monitoring, Recovery & Cost Control
- Mark 3 Release Candidate Hardening

No se crearán 120 PRs por cada Mark. El roadmap usa macro-PRs grandes,
coherentes y validables.

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_post_s_global_approval_controlled_execution_semantics_mark_roadmap.py -q
pytest tests/jarvis -q -x --durations=20
```
