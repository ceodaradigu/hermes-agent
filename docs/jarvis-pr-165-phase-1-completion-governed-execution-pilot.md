# PR #165 - Phase 1 Completion: Governed Hermes Execution E2E + Pilot Hardening

Fecha: 2026-06-19

## Objetivo

Cerrar Phase 1 con un flujo local gobernado y honesto:

```text
intencion
  -> intake
  -> candidate action
  -> preview
  -> risk classification
  -> approval request si aplica
  -> approval decision valida
  -> governed Hermes dispatch cuando procede
  -> audit persistente metadata-only
  -> status/event stream
  -> stop/cancel/rollback metadata
  -> pilot report
```

JARVIS gobierna, Hermes ejecuta. Esta PR no crea otro Hermes, no duplica runtime,
no agrega `/execute`, no permite shell libre desde UI y no permite dispatch
directo de Hermes desde frontend.

## Implementado

- `jarvis/phase_1_governed_execution.py` introduce
  `Phase1GovernedExecutionControlPlane`.
- El control plane reutiliza piezas existentes:
  `ConversationalIntakePipeline`, `PolicyEngine`, `Mark3MissionLoop`,
  `Mark3HermesRuntimeBridge`, `PersistentAuditLedger` y `MemoryBrainV2Store`.
- `/jarvis` obtiene un panel de aprobacion backend-gated: crea preview, solicita
  approval, aprueba/rechaza/cancela, pide aclaracion, solicita stop y despacha
  solo mediante endpoints gobernados.
- Voz local puede enviar una transcripcion final como intencion textual
  controlada. Voz y wake phrase no aprueban.
- El dashboard y event stream exponen estado real de ejecucion gobernada,
  readiness de Phase 1, audit/memory y limitaciones sin secretos, audio bruto,
  frames ni transcripts completos.
- Persistent Audit recibe eventos reales del flujo.
- Memory Brain v2 puede influir en preview como contexto explicable, pero nunca
  concede permisos.

## Endpoints

Endpoints nuevos:

| Metodo | Ruta | Proposito |
|---|---|---|
| `GET` | `/mark-3/execution/status` | Estado local del control plane gobernado. |
| `GET` | `/mark-3/phase-1/status` | Checklist de cierre, capacidades, riesgos y readiness. |
| `POST` | `/mark-3/execution/preview` | Crea intake, candidate action, preview y risk classification. |
| `POST` | `/mark-3/execution/request-approval` | Crea approval envelope si el preview lo requiere. |
| `POST` | `/mark-3/execution/approval-decision` | Aplica approve/reject/cancel con validacion backend. |
| `POST` | `/mark-3/execution/dispatch` | Despacha solo si estado, policy y approval son validos. |
| `POST` | `/mark-3/execution/cancel` | Cancela preview/envelope si el estado lo permite. |
| `POST` | `/mark-3/execution/stop` | Solicita stop cooperativo o declara unsupported. |

No se agrega `/execute`. La UI no llama endpoints Hermes directos.

## Acciones reales

Soportado en Phase 1:

- `system_status_read`: lectura de estado local safe/read-only, sin approval y
  sin Hermes.
- `prepare_only`: generacion de preview/plan sin ejecucion.
- `local_file_read_exact`: lectura de archivo exacto local no sensible mediante
  el bridge existente `Mark3HermesRuntimeBridge.execute_read`, con approval
  backend valido.

Denied:

- `.env`, secretos, credenciales, tokens, passwords, cookies y session material.
- La respuesta exacta para credenciales se conserva:
  `No puedo hacer eso, David. Las credenciales y secretos están protegidos.`
- Borrado, modificacion de credenciales, deploy, dinero, Stripe, email,
  publicacion, dominios y operaciones externas.
- Wake phrase como approval y voice approval.

Unsupported/not configured:

- Shell libre y comandos arbitrarios.
- Comandos allowlisted destructivos o no soportados por Hermes real.
- Terminal allowlist execution desde UI: declarado como no configurado si no hay
  bridge seguro real.
- Critical double/triple approval: si no existe soporte configurado, queda
  `requires_stronger_approval_not_configured`.

## Safety Gates

- Cada `POST` valida state transition.
- Preview y approval son prerequisitos cuando aplica.
- El backend recalcula/valida riesgo antes de dispatch.
- `hermes_dispatch_allowed=true` solo aparece en audit cuando hay dispatch
  gobernado real.
- Las flags seguras permanecen:
  `contains_raw_audio=false`, `contains_camera_frame=false`,
  `contains_secret=false`, `contains_credential=false`,
  `contains_full_transcript=false` por defecto.
- No se guardan audio bruto, frames, secretos ni full transcripts sensibles.
- Memory influence no es permiso.

## Approval UI

El panel de `/jarvis` muestra:

- intencion;
- preview;
- accion propuesta;
- riesgo;
- motivo de approval;
- lo que hara;
- lo que no hara;
- stop plan;
- rollback plan si aplica;
- audit destination;
- confirmation level;
- readback requerido;
- memory influence summary.

Acciones UI:

- crear preview;
- pedir approval;
- approve;
- reject;
- cancel;
- request clarification;
- stop;
- dispatch gobernado.

Todas pasan por backend JARVIS. El frontend no ejecuta Hermes.

## Audit

Eventos metadata-only conectados:

- `intake_created`
- `preview_created`
- `risk_classified`
- `approval_requested`
- `approval_approved`
- `approval_rejected`
- `approval_cancelled`
- `approval_expired`
- `approval_blocked`
- `dispatch_requested`
- `dispatch_started`
- `dispatch_blocked`
- `dispatch_completed`
- `dispatch_failed`
- `stop_requested`
- `stop_completed`
- `stop_unsupported`
- `rollback_plan_created`
- `memory_influence_used`
- `voice_session_intent_submitted`
- `ui_approval_action`

El ledger conserva hash-chain y metadata segura. Se corrigio el cableado para
que `hermes_dispatch_allowed` solo pueda persistirse en eventos de dispatch
gobernado real.

## Memory Brain v2

Memory Brain v2 aporta contexto activo no sensible:

- `why_used`;
- `memory_id`;
- `kind`;
- `summary`;
- `used_for_permission=false`;
- `grants_permission=false`.

Memoria sensible/private no se autoload. Pending review, contradicciones y
lifecycle existentes se mantienen. Si memoria influye, se audita como
metadata-only.

## Voice/Intake

Flujo de voz:

```text
David activa voz manualmente
  -> browser STT produce transcript local
  -> frontend envia texto final como intencion si hay callback configurado
  -> backend crea preview/risk/approval
  -> UI muestra approval panel si aplica
  -> David aprueba con metodo valido de UI/backend
```

No hay auto mic, no wake always-on real, no audio bruto backend, no transcripcion
continua y no approval por voz.

## Como probar localmente

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.

python -m py_compile $(find jarvis -name '*.py')

PYTHONPATH=. python -m pytest -c /dev/null \
  tests/jarvis/test_pr_165_phase_1_completion_governed_execution_pilot.py \
  -q -x

PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20

git diff --check

cd web && npm run build
```

Si `web/node_modules` no existe:

```bash
cd web
npm_config_cache=/tmp/jarvis-npm-cache-pr165 npm ci --fetch-retries=5 \
  --fetch-retry-mintimeout=2000 --fetch-retry-maxtimeout=60000
npm run build
```

No ejecutar `npm audit fix`.

## Pilot Checklist

- Preview desde intencion: implementado.
- Risk classification: implementado.
- Approval UI real/backend-gated: implementado.
- Dispatch gobernado por bridge existente: implementado para lectura exacta
  local no sensible.
- Stop/cancel: implementado como estado/metadata; stop real depende de sesion
  cooperativa del bridge.
- Persistent audit: conectado a eventos reales.
- Memory influence: conectado como contexto explicable.
- Voice text intent: conectado sin approval por voz.
- Dashboard/event stream: conectado.
- Critical double/triple approval: no configurado, queda bloqueado.
- Shell libre/comandos arbitrarios: no implementado.

## Repos externas revisadas

| Repo | URL | Licencia visible | Uso en PR #165 |
|---|---|---|---|
| `langchain-ai/langgraph` | https://github.com/langchain-ai/langgraph | MIT | Patron conceptual de estado duradero, HITL y memoria; no dependencia. |
| `OpenInterpreter/open-interpreter` | https://github.com/OpenInterpreter/open-interpreter | Apache-2.0 | Riesgos de ejecucion local y permisos; no shell libre. |
| `Significant-Gravitas/AutoGPT` | https://github.com/Significant-Gravitas/AutoGPT | Polyform Shield para platform, MIT fuera de platform | Referencia de agent loop/restricciones; no runtime. |
| `crewAIInc/crewAI` | https://github.com/crewAIInc/crewAI | MIT | Referencia de task orchestration; no dependencia. |
| `microsoft/autogen` | https://github.com/microsoft/autogen | MIT para codigo, CC-BY-4.0 para docs | Referencia de approval/tool execution y riesgos MCP; no dependencia. |
| `OpenVoiceOS/ovos-core` | https://github.com/OpenVoiceOS/ovos-core | Apache-2.0 | Intent/skills safety patterns; no runtime de voz. |
| `getzep/graphiti` | https://github.com/getzep/graphiti | Apache-2.0 | Memory provenance temporal; no graph DB. |
| `mem0ai/mem0` | https://github.com/mem0ai/mem0 | Apache-2.0 | Memory influence/lifecycle concepts; no cloud/vector DB. |
| `sigstore/rekor` | https://github.com/sigstore/rekor | Apache-2.0 | Idea de transparency log; no servidor externo. |
| `google/trillian` | https://github.com/google/trillian | Apache-2.0 | Verifiable log concepts; no infraestructura distribuida. |
| `Yelp/detect-secrets` | https://github.com/Yelp/detect-secrets | Apache-2.0 | Clases de secretos/redaccion conceptual; no scanner pesado. |
| `trufflesecurity/trufflehog` | https://github.com/trufflesecurity/trufflehog | AGPL-3.0 | Referencia de clases de credenciales; no codigo copiado ni dependencia. |
| `semgrep/semgrep` | https://github.com/semgrep/semgrep | LGPL-2.1 | Referencia de reglas defensivas; no ruleset/runtime. |

Codigo externo copiado: ninguno.

Codigo adaptado: ninguno en sentido de copia directa.

Patrones reimplementados localmente: state machine de aprobacion/dispatch,
metadata-only audit transparency, memory influence provenance y negative gates
para secretos/shell/external ops.

## No implementado

- No se implementa shell libre.
- No se implementa `/execute`.
- No se implementa Hermes directo desde frontend.
- No se implementa terminal command runtime real desde UI.
- No se implementan critical double/triple approvals configurables.
- No se implementan deploy, dinero, Stripe, email, publicaciones ni operaciones
  externas.
- No se implementa wake real always-on.
- No se implementa backend STT/TTS serio ni grabacion continua.
- No se instala graph DB, vector DB, cloud memory ni dependencias pesadas.

## Riesgos pendientes

- Definir soporte real de stronger approval para critical: double/triple
  confirmation, trusted device y challenge expiration.
- Expandir Hermes bridge con mas acciones allowlisted reales sin abrir shell
  libre.
- Persistir historial UI de approval/dispatch si se requiere operacion larga.
- Definir stop/rollback real por tipo de accion Hermes.
- Anadir verificacion browser automatizada cuando el build frontend pueda correr
  con `node_modules` disponible.

## Recomendacion Phase 2

Phase 2 deberia continuar como macro-PR de capacidad, no micro-PRs:

1. Strong Approval v2 completo con challenge/double/triple/trusted device.
2. Hermes bridge ampliado con acciones allowlisted reales y contratos de stop.
3. Historial persistente de execution/approval en UI.
4. Browser verification end-to-end de `/jarvis`.
5. Pilot local con tareas reales no destructivas y reporte de evidencia.
