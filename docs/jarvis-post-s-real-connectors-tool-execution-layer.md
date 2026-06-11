# Post-S Macro 4 - Real Connectors & Tool Execution Layer

Esta macro PR consolida una capa de control segura para representar herramientas,
conectores, permisos e invocaciones futuras. No activa ejecución real ni conecta
servicios externos.

## Por qué no es Phase T

Este trabajo no es Phase T. Phase S sigue siendo la última fase maestra
implementada y no existe Phase T. Es una macro PR transversal posterior a Phase
S que mantiene el límite prepare-only.

## Tool Registry y Connector Contracts

El Tool Registry registra definiciones declarativas de herramientas y
conectores. Registro no significa permiso. Todas las herramientas y conectores
están deshabilitados por defecto y `execution_enabled=false`.

Los Connector Contracts modelan:

- `local_filesystem_scoped`, que exige scope explícito;
- `github`, que declara red y credenciales requeridas pero nunca las carga;
- `web_browser`, que declara red externa bloqueada por defecto;
- `external_api`, que declara red, credenciales y strong approval;
- `mock_safe`, para previews controlados sin ejecución.

Todos los conectores son read-only y write-disabled por defecto.

## Tool Invocation Preview

PR #122 define `safe_to_invoke` como elegibilidad potencial después de
aprobación válida y gates, no como tool call real. Sin aprobación es false;
puede ser true como readiness si todo pasa; nunca puede ser true para una
capacidad ilegal, insegura, no autorizada, imposible o unsupported.

`ToolInvocationPreview` representa acción, target, scope, payload redactado,
riesgo e intención solicitada. Puede preparar un
`ControlledRuntimeExecutionRequest`, pero siempre devuelve
`would_execute=false`, `would_call_external=false`, `would_write_files=false` y
`would_use_credentials=false`.

`ToolPermissionCheckResult` compone registry, connector scope, permisos,
approval, strong approval, context fingerprint y el gate del Controlled Runtime
Bridge. `allowed` permanece siempre en false. `safe_to_invoke=true` significa
solo readiness futura y no ejecuta nada.

## Integración con PR #117 y PR #118

La capa consume `ApprovalRecord`, `StrongApprovalPolicy`, context fingerprint,
`PermissionGateResult` y audit trail a través del bridge existente de PR #117.
También consume `ControlledRuntimeExecutionRequest`, dry-run, sandbox,
rollback y `ControlledRuntimeGateResult` de PR #118.

Approval aprobado no invoca. Permission gate permitido no invoca. Runtime
`safe_to_execute=true` no invoca. Tool `safe_to_invoke=true` tampoco invoca.

## Qué bloquea

- tool o connector no registrado o deshabilitado;
- scope, target o action type vacíos;
- permisos declarados ausentes;
- scope fuera del contrato del connector;
- red externa sin permiso;
- credenciales sin strong approval válido;
- filesystem write sin scope y rollback;
- producción sin strong approval;
- side effects sin rollback;
- dry-run, sandbox, approval, context fingerprint o runtime gate inválidos;
- cualquier `blocked_reason`.

## API control-plane

- `GET /tools/status`
- `GET /tools/registry`
- `GET /tools/policy`
- `POST /tools/preview-registration`
- `POST /tools/preview-invocation`
- `POST /tools/preview-permission`
- `POST /tools/preview-connector`

No existen rutas de execute, run, call, deploy, install, send, pay,
read-secret, read-env, GitHub actions, browser open, API request, files write,
shell o subprocess.

## Qué no ejecuta todavía

No llama herramientas, Hermes, GitHub, navegador, APIs, red, credenciales,
filesystem, producción, subprocess, misiones ni tareas. No lee secretos y no
persiste estado externo.

## Siguiente macro PR

Esta capa prepara **Post-S Macro 5 - Memory, Personal OS & Scheduler Real** sin
habilitar connectors ni tool calls reales.

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_post_s_real_connectors_tool_execution_layer.py -q
pytest tests/jarvis/test_post_s_controlled_runtime_execution_bridge.py -q
pytest tests/jarvis/test_post_s_approval_audit_permission_hardening.py -q
pytest tests/jarvis/test_e2e_prepare_only_smoke_after_phase_s.py -q
```
