# Post-S Macro 2 - Real Approval, Audit & Permission Hardening

Esta macro PR consolida records de approval verificables, strong approval, expiracion, revocacion,
fingerprints de contexto, auditoria append-only interna y permission gates para una futura conexion
de runtime. Es trabajo post-Phase S y no es Phase T. No existe Phase T aprobada ni implicita.

## Boundary prepare-only

La macro no ejecuta acciones, comandos, despliegues, pagos, mensajes, llamadas externas, acceso a
secretos, captura de sensores ni automatizacion fisica. Un approval aprobado solo produce estado
verificable. Incluso un gate valido devuelve `safe_to_execute=false`; solo queda marcado como
permitido para una futura capa de ejecucion que todavia no existe.

## Approval normal y strong approval

Un approval normal registra una decision humana explicita para un contexto exacto. No sirve cuando
la policy exige strong approval.

Strong approval requiere un record de tipo `strong` y la cadena de confirmacion exacta generada para
ese approval. Se exige para produccion, deploy, dinero/pagos, secretos/credenciales, identidad/cuentas,
datos privados/personales, memoria sensible persistente, instalaciones/dependencias, shell/subprocess,
llamadas externas, email/mensajeria, camara/microfono/pantalla, robot/dron/dispositivos y cambios de
runtime/policy/security.

## Expiracion, revocacion y contexto

Los approvals pendientes, rechazados, revocados o expirados bloquean el gate. La revocacion solo se
aplica a approvals previamente aprobados.

El context fingerprint canoniza los campos relevantes y calcula SHA-256. Cambios en `action_type`,
target, command, amount/budget, environment, production, tool name, secret/external-call flags o
payload relevante cambian el fingerprint y bloquean el gate. Payloads estructurados y valores
sensibles se representan por hash; no se conserva contenido sensible completo.

## Audit trail

La auditoria interna es append-only e incluye request, approve, reject, revoke, expire, context
mismatch, gate denied y gate allowed-for-future-execution. Redacta claves y textos sospechosos como
tokens, secrets, passwords, credenciales y `.env`. No usa persistencia externa.

## API control-plane

Las rutas seguras son:

- `GET /approvals/status`
- `GET /approvals/policy`
- `GET /approvals/audit-preview`
- `POST /approvals/preview-request`
- `POST /approvals/preview-decision`
- `POST /approvals/preview-gate`

No existen rutas de execute, run, deploy, send, install, pay, read-secret o activacion de sensores.

## Siguiente macro PR

La siguiente recomendacion es **Post-S Macro 3 - Controlled Runtime Execution Bridge**. Esa futura
macro debera consumir estos gates sin degradarlos y mantener rollback, audit y bloqueo por contexto.

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_post_s_approval_audit_permission_hardening.py -q
pytest tests/jarvis -q -x --durations=20
```
