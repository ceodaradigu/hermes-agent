# Post-S Macro 3 - Controlled Runtime Execution Bridge

Esta macro PR consolida un puente de ejecución controlada exclusivamente de
control-plane. JARVIS puede representar una solicitud futura, producir un
dry-run, declarar requisitos de sandbox y rollback, consumir policy, approvals,
strong approval, permission gates y context fingerprint, y calcular readiness
auditable sin ejecutar nada.

## Por qué no es Phase T

Este trabajo no es Phase T. Phase S sigue siendo la última fase maestra
implementada y no existe Phase T aprobada. Es una macro PR transversal posterior
a Phase S que mantiene todas las superficies prepare-only.

## Contratos

`ControlledRuntimeExecutionRequest` describe acción, target, scope, comando o
tool opcional, resumen redactado, entorno, flags de riesgo, actor, razón y
context fingerprint.

`DryRunResult` es una simulación declarativa. Siempre devuelve
`would_execute=false`; no llama comandos, tools, Hermes, red o filesystem.

`SandboxRequirements` declara aislamiento, scope de filesystem, red default-deny,
bloqueo de secretos, timeout y rollback requeridos. No crea un sandbox real.

`RollbackPlan` declara si rollback es obligatorio, si existe y sus pasos
redactados. Side effects, filesystem writes, producción, deploy, llamadas
externas y cambios persistentes exigen rollback.

`ControlledRuntimeGateResult` compone todos los gates y calcula
`safe_to_execute`. Ese campo significa únicamente readiness futura. Incluso si
es `true`, no ejecuta, no habilita side effects y no muta misiones o tareas.

## Integración con PR #117

El bridge consume `ApprovalRecord`, `StrongApprovalPolicy`,
`build_context_fingerprint`, `PermissionGateResult`, `evaluate_permission_gate`
y `ApprovalAuditTrail`. No degrada approvals expirados, pendientes, rechazados,
revocados, normales cuando se exige strong approval, ni fingerprints que no
coinciden.

## Qué bloquea

- policy no permitida o permission gate denegado;
- approval inválido, ausente o insuficiente;
- context fingerprint distinto;
- sandbox, timeout o filesystem scope ausentes;
- secretos no autorizados o red sin permiso explícito;
- dry-run ausente o fallido;
- rollback obligatorio ausente;
- action type o target vacíos;
- scope vacío, abierto o irrestricto;
- comando ambiguo o ausencia de comando/tool.

## API control-plane

- `GET /runtime/status`
- `GET /runtime/policy`
- `POST /runtime/preview-plan`
- `POST /runtime/preview-dry-run`
- `POST /runtime/preview-gate`
- `POST /runtime/preview-rollback`

No existen rutas runtime de execute, run, deploy, install, send, pay,
read-secret, start-worker, sensores, shell o subprocess.

## Qué no ejecuta todavía

No ejecuta comandos, tools, Hermes, connectors, red, filesystem, producción,
deploys, pagos, scheduler, sensores, misiones ni tareas. Approval aprobado y
permission gate permitido tampoco ejecutan.

## Siguiente macro PR

Este bridge prepara **Post-S Macro 4 - Real Connectors & Tool Execution Layer**.
Esa macro futura deberá mantener estos gates y requerirá una decisión explícita
antes de habilitar cualquier ejecución real.

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_post_s_controlled_runtime_execution_bridge.py -q
pytest tests/jarvis/test_e2e_prepare_only_smoke_after_phase_s.py -q
pytest tests/jarvis -q -x --durations=20
```
