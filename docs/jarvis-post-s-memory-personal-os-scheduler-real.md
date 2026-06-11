# Post-S Macro 5 - Memory, Personal OS & Scheduler Real

Esta macro PR consolida una capa real de control para memoria aprobada, Personal
OS y scheduler. "Real" significa que existen records, estado, cálculo de due
items, reviews, stop controls, gates y auditoría explícitos. No significa
autoload, ejecución recurrente, workers, watchers, notificaciones ni acceso a
fuentes externas.

## Por qué no es Phase T

Este trabajo no es Phase T. Phase S sigue siendo la última fase maestra
implementada y no existe Phase T aprobada o implícita. Macro 5 es trabajo
transversal post-S y mantiene el límite prepare-only.

## Memoria aprobada real

`ApprovedMemoryRecord` representa memoria explícita, redactada, auditable,
reversible y vinculada a un context fingerprint. Empieza con `approved=false` y
`active=false`. Memoria sensible requiere approval. Memoria privada o sensible
persistente requiere strong approval válido para el contexto exacto.

Memoria no es permiso: una memoria activa futura podría orientar contexto, pero
nunca autoriza acciones sensibles ni evita `PolicyEngine`, ApprovalGateway,
permission gates, controlled runtime o tool gates. No existe autoload ni
autoactivación.

## Personal OS control-plane

`PersonalOSState` representa modos, foco, prioridades, rutinas, recordatorios,
review queue, fuentes autorizadas/bloqueadas y stop controls. No lee calendario,
email, documentos, archivos privados o fuentes externas. `autoload_enabled`,
`execution_enabled`, `side_effects_enabled`, `scheduler_enabled` y
`watcher_enabled` permanecen siempre en false.

## Scheduler control-plane

`SchedulerItem` representa reminders, routines, daily/weekly reviews, approval
checks y maintenance. Crear o registrar un item no ejecuta nada. Un item `due`
solo significa que el cálculo de preview considera que llegó su fecha. Due no ejecuta,
una routine no corre y un reminder no notifica.

`SchedulerPreviewResult` separa due, próximos, pausados y cancelados, y mantiene
`would_execute=false`, `would_notify=false`, `would_call_tools=false` y
`would_call_external=false`. No existe background worker, cron operativo,
watcher, llamada de tool, calendario/email real ni notificación externa.

## Reviews y stop controls

Daily review y weekly review son resúmenes control-plane. No envían, ejecutan ni
llaman tools. Las señales ROI/monetización semanales son proyectadas o
planificadas, nunca ingresos confirmados.

`StopControls` puede representar pausa global y pausas de memoria, scheduler,
rutinas, Personal OS, fuentes externas y tools. Es un preview reversible; no
arranca ni detiene workers reales porque no existen en esta macro.

## Gates heredados

PR #122 aclara la semántica global: memoria activa no es permiso y scheduler
due no es permiso. Acciones programadas sensibles requieren aprobación válida;
acciones críticas requieren strong approval y doble confirmación antes de una
futura ejecución.

Macro 5 consume `ApprovalRecord`, `StrongApprovalPolicy`, context fingerprint,
`PermissionGateResult` y audit trail de Macro 2. Approval aprobado no activa ni
ejecuta.

Respeta `ControlledRuntimeExecutionRequest` y `ControlledRuntimeGateResult` de
Macro 3 como readiness futura. `safe_to_execute=true` no ejecuta.

Respeta `ToolDefinition`, `ConnectorDefinition`, `ToolInvocationPreview` y
`ToolPermissionCheckResult` de Macro 4 como dependencia futura.
`safe_to_invoke=true` no invoca y el scheduler no llama tools.

## Qué bloquea

- approval ausente, pendiente, rechazado, revocado, expirado o insuficiente;
- context fingerprint distinto;
- memoria sensible/privada persistente sin strong approval;
- secretos, fuentes privadas o externas no autorizadas;
- side effects, tool invocation, llamadas externas y notificaciones;
- autoload, autoactivación, watcher, worker o ejecución;
- cualquier `blocked_reason` o stop control aplicable.

Incluso cuando una preview queda ready, esta macro no ejecuta, persiste,
notifica, llama red/tools/Hermes ni muta missions/tasks.

## API control-plane

- `GET /personal-os/status`
- `GET /personal-os/policy`
- `POST /personal-os/preview-state`
- `POST /memory/preview-record`
- `POST /memory/preview-activation`
- `POST /memory/preview-deactivation`
- `GET /scheduler/status`
- `GET /scheduler/policy`
- `POST /scheduler/preview-item`
- `POST /scheduler/preview-due`
- `POST /scheduler/preview-daily-review`
- `POST /scheduler/preview-weekly-review`
- `POST /scheduler/preview-stop-controls`

No existen rutas peligrosas de memory autoload/auto-activate/read-env, scheduler
start/run/execute/worker/watch/send/notify/call-tool ni Personal OS
read-email/read-calendar/read-files/sync-external/start-agent.

## Siguiente macro PR

Esta capa preparó **Post-S Macro 6 - Local Wake Voice Runtime & Camera Control**.
Esa macro es opt-in, mantiene privacidad visible y no degrada
approvals, stop controls ni el límite de ejecución.

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_post_s_memory_personal_os_scheduler_real.py -q
pytest tests/jarvis/test_e2e_prepare_only_smoke_after_phase_s.py -q
pytest tests/jarvis -q -x --durations=20
```
