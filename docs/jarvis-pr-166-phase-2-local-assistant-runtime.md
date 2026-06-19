# PR #166 - Phase 2 Local Assistant Runtime

Fecha: 2026-06-19

## Resumen

PR #166 convierte JARVIS de base local gobernada a asistente local usable con runtime local gobernado, sin crear otro Hermes y sin abrir shell libre. La fase mantiene el contrato:

- JARVIS gobierna intención, policy, riesgo, approval, audit, stop/rollback e historial.
- Hermes ejecuta solo por el bridge existente cuando una acción allowlisted lo requiere.
- El frontend de `/jarvis` nunca ejecuta Hermes directamente.
- Voz puede iniciar intención/preview y leer readback, pero no aprueba.
- Wake phrase nunca aprueba.
- Memoria puede influir contexto, pero nunca concede permisos.
- Auditoría e historial son metadata-only.

## Qué Se Implementó

### Strong Approval v2

Se añadió una envoltura v2 sobre el `ApprovalGateway`/`ApprovalHardeningService` existente dentro de `Phase2LocalAssistantRuntimeControlPlane`.

Niveles soportados:

- `none`
- `soft`
- `normal`
- `strong`
- `double`
- `triple`
- `blocked`
- `unsupported`

El envelope v2 modela:

- `approval_id`
- `action_id`
- `action_key`
- `risk_level`
- `approval_level_required`
- `requester`
- `reason`
- `preview`
- `readback_text`
- `confirmation_phrase`
- `challenge`
- `second_confirmation_required`
- `third_confirmation_required`
- `expires_at`
- `created_at`
- `decided_at`
- `status`
- `rejection_reason`
- `audit_id`
- `correlation_id`

Reglas activas:

- Low puede usar `none` o `soft` si la acción es read-only y policy lo permite.
- Medium usa `normal` en acciones allowlisted como `repo.tests.run_allowlisted` y `repo.file.read_safe`.
- High recalcula a `strong`, exige readback y confirmation phrase.
- Critical recalcula a `triple`; como no hay canal double/triple real configurado, queda `blocked` con `requires_stronger_approval_not_configured`.
- Approvals caducan.
- Approvals son single-use.
- Backend recalcula risk/policy antes de aceptar approval y antes de dispatch.
- Voice/wake no pueden aprobar por `actor`, `decision_source` ni `channel`.
- Readback obligatorio para high/critical.
- Confirmation phrase obligatoria para strong/double/triple cuando el canal existe.
- Secrets/credentials/.env/tokens/passwords/cookies/session material quedan denied siempre.

## Hermes Action Bridge Allowlisted

Se añadió `jarvis/phase_2_local_assistant_runtime.py`. No es otro Hermes; extiende `Phase1GovernedExecutionControlPlane` y reutiliza el `Mark3HermesRuntimeBridge` existente para `repo.file.read_safe`.

Acciones allowlisted:

| action_key | Riesgo | Approval | Ejecuta real |
|---|---:|---:|---|
| `local.status.read` | low | none | Sí, control-plane local read |
| `local.doctor.run` | low | none | Sí, checks deterministas |
| `repo.status.read` | low | none | Sí, `git status --short --branch` fijo, sin shell |
| `repo.tests.run_allowlisted` | medium | normal | Sí, pytest target allowlisted fijo |
| `repo.diff.read` | low | none | Sí, `git diff --stat` y `--name-only` fijos |
| `repo.log.read` | low | none | Sí, `git log --oneline -n N` fijo y validado |
| `repo.file.read_safe` | medium | normal | Sí, bridge Hermes existente `read_file` |
| `jarvis.phase.status` | low | none | Sí, status local |
| `jarvis.audit.status` | low | none | Sí, status metadata-only |
| `jarvis.memory.status` | low | none | Sí, status metadata-only |
| `jarvis.execution.history.read` | low | none | Sí, historial metadata-only |
| `jarvis.execution.preview` | low | none | Sí, prepare-only/discard preview |

Cada acción declara:

- schema de inputs permitido;
- `risk_level`;
- `approval_required`;
- `timeout_seconds`;
- `stop_supported`;
- `rollback_supported`;
- tipos de audit;
- redacción de output;
- scope filesystem;
- network permitido;
- side effects externos;
- política de secrets;
- contrato de stop/rollback.

No se acepta:

- shell libre;
- comandos arbitrarios;
- lectura de `.env`;
- secrets/tokens/passwords/cookies/session material;
- borrado;
- escritura destructiva;
- instalación de dependencias;
- deploy;
- dinero/Stripe/email/publicación;
- browser automation no gobernada;
- operaciones externas.

## Execution History

Se añadió `ExecutionHistoryStore` con SQLite local metadata-only. Por defecto usa memoria si no hay state dir; si existe `JARVIS_LOCAL_STATE_DIR` o `JARVIS_STATE_DIR`, persiste en:

```text
<state_dir>/execution_history/execution_history.sqlite3
```

Campos persistidos:

- `execution_id`
- `action_id`
- `approval_id`
- `intent_summary`
- `action_key`
- `status`
- `risk_level`
- `approval_level`
- `started_at`
- `finished_at`
- `duration_ms`
- `result_summary`
- `error_summary`
- `stop_requested`
- `rollback_requested`
- `rollback_status`
- `audit_ids`
- `memory_influence_ids`
- `redaction_summary`
- `contains_secret=false`
- `contains_credential=false`
- `contains_raw_audio=false`
- `contains_camera_frame=false`

No guarda outputs completos sensibles, contenido de archivos, audio bruto, frames ni secretos.

## Stop/Rollback Contracts

Todas las acciones declaran:

- `stop_supported`
- `stop_method`
- `rollback_supported`
- `rollback_plan`
- `rollback_risk`
- `rollback_requires_approval`
- `rollback_status`
- `rollback_limitations`

Reglas:

- Read-only: `rollback_status=not_required`.
- Prepare-only: `rollback_status=discard_preview`.
- Stop real solo si el bridge lo soporta.
- Stop no soportado devuelve `stop_requested_pending_or_unsupported`, no éxito falso.
- Rollback no se finge.
- Cualquier acción futura con side effects deberá tener rollback plan y approval de rollback antes de ejecución.

Audit event types añadidos:

- `rollback_requested`
- `rollback_completed`
- `rollback_unsupported`
- `rollback_failed`
- `execution_history_recorded`

Los event types previos de stop/rollback siguen activos.

## Voice/Wake Runtime

Phase 2 añade diagnóstico y contrato de readiness sin vigilancia ambiental:

- browser STT/TTS capability queda declarado como verificación client-side;
- selected voice metadata limitada a nombre/lang/voiceURI;
- TTS interrupt/stop apoyado en `speechSynthesis.cancel` cuando el navegador lo soporta;
- low-confidence voice preview exige clarification antes de preview ejecutable;
- voice intent submitted se conecta a execution preview;
- voice puede cancelar/stop si UI/backend lo permite;
- voice no aprueba;
- wake provider status queda `disabled` o `not_configured`;
- no wake always-on real;
- no openWakeWord activo;
- no auto mic;
- no audio bruto backend;
- no transcribir todo.

## Browser Verification

Se añadió `GET /mark-3/browser-verification/status` con checklist estático/manual:

- API reachability;
- voice capability check;
- approval panel render;
- event stream;
- audit status;
- memory status;
- execution history;
- no auto getUserMedia;
- no `/execute`;
- no frontend direct Hermes.

No se añadió Playwright ni dependencia pesada.

## Daemon/Tray Readiness

Se añadió `GET /mark-3/local-runtime/status` como contrato de readiness:

- `daemon_status=readiness_contract_only`
- `tray_status=readiness_contract_only`
- `local_runtime_ready=true`
- `startup_mode=manual`
- `background_listening_enabled=false`
- `auto_start_enabled=false`
- `user_opt_in_required=true`
- binding local-only recomendado `127.0.0.1`
- state dir contract para audit/history
- failure modes explícitos

No instala daemon real, tray real, servicio de auto-start ni listener background.

## UI `/jarvis`

Se actualizó el drawer `Sistemas`:

- catálogo allowlisted compacto;
- execution history compacta;
- stop/rollback status;
- voice diagnostics Phase 2;
- daemon/tray readiness;
- browser verification checklist;
- phase 2 status.

No se tocó el centro principal como JSON. Se mantiene:

- esfera de partículas;
- smart bar;
- voice loop;
- camera opt-in;
- raw recording opt-in;
- memory drawer;
- audit drawer.

## Endpoints

GET:

- `/mark-3/phase-2/status`
- `/mark-3/execution/action-catalog`
- `/mark-3/execution/history`
- `/mark-3/execution/history/{execution_id}`
- `/mark-3/execution/status`
- `/mark-3/approval/status`
- `/mark-3/local-runtime/status`
- `/mark-3/browser-verification/status`
- `/mark-3/voice-runtime/status` con `phase_2_runtime`
- `/mark-3/dashboard/status` con Phase 2
- `/mark-3/dashboard/events` con `phase_2_state`, `action_catalog_state`, `execution_history_state`
- `/mark-3/dashboard/events/stream`

POST gobernados existentes:

- `/mark-3/execution/preview`
- `/mark-3/execution/request-approval`
- `/mark-3/execution/approval-decision`
- `/mark-3/execution/dispatch`
- `/mark-3/execution/cancel`
- `/mark-3/execution/stop`

No existe `/execute`.

## Seguridad

Controles activos:

- no shell libre;
- no comandos arbitrarios desde UI;
- argv fijo para acciones git/pytest;
- no `shell=True`;
- inputs validados por action_key;
- outputs resumidos/redactados;
- secretos bloqueados por intent/input/path;
- audit metadata-only;
- history metadata-only;
- approvals expiran;
- approvals single-use;
- approval no se reutiliza para otra acción;
- backend recalcula policy/risk;
- frontend no decide solo;
- wake phrase no aprueba;
- voz no aprueba sola;
- critical sin double/triple real queda blocked.

## Repos Externas Revisadas

| Repo | URL | Licencia visible | Uso |
|---|---|---|---|
| langgraph | https://github.com/langchain-ai/langgraph | MIT | Patrones de state, durable execution, HITL y memory. |
| open-interpreter | https://github.com/OpenInterpreter/open-interpreter | Apache-2.0 | Riesgos de ejecución local; no shell libre. |
| AutoGPT | https://github.com/Significant-Gravitas/AutoGPT | Polyform Shield para platform, MIT fuera de platform | Agent loop/safety como referencia. |
| crewAI | https://github.com/crewAIInc/crewAI | MIT | Orquestación conceptual. |
| autogen | https://github.com/microsoft/autogen | MIT código, CC-BY docs | Approval/tool execution patterns. |
| ovos-core | https://github.com/OpenVoiceOS/ovos-core | Apache-2.0 | Separación intents/skills y stop/deactivate. |
| ovos-audio | https://github.com/OpenVoiceOS/ovos-audio | Apache-2.0 | Separación de servicio de audio; no runtime adoptado. |
| openWakeWord | https://github.com/dscripka/openWakeWord | Apache-2.0 | Wake readiness, sin activar always-on. |
| faster-whisper | https://github.com/SYSTRAN/faster-whisper | MIT | STT local readiness, sin instalar. |
| whisper.cpp | https://github.com/ggml-org/whisper.cpp | MIT | STT local readiness, sin compilar. |
| piper1-gpl | https://github.com/OHF-Voice/piper1-gpl | GPL-3.0 | TTS local readiness/licencia; no copiar ni instalar. |
| graphiti | https://github.com/getzep/graphiti | Apache-2.0 | Memory provenance conceptual, sin graph DB. |
| mem0 | https://github.com/mem0ai/mem0 | Apache-2.0 | Memory influence/lifecycle conceptual, sin cloud/vector DB. |
| rekor | https://github.com/sigstore/rekor | Apache-2.0 | Transparency/audit ideas, sin servidor. |
| trillian | https://github.com/google/trillian | Apache-2.0 | Verifiable log conceptual, sin infra. |
| detect-secrets | https://github.com/Yelp/detect-secrets | Apache-2.0 | Categorías de secrets/redacción conceptual. |
| trufflehog | https://github.com/trufflesecurity/trufflehog | AGPL-3.0 | Riesgos/clases de credenciales; no copiar. |
| semgrep | https://github.com/semgrep/semgrep | LGPL-2.1 | Guardrails estáticos conceptuales; no dependencia. |

Código externo copiado: ninguno.

Patrones reimplementados localmente:

- state machine de approvals/dispatch;
- metadata history;
- audit transparency-style;
- memory influence provenance;
- safety/deny lists para secretos y ejecución local;
- readiness contracts para voz/wake/daemon.

## Qué No Se Implementó

- dinero;
- Stripe;
- deploy;
- email;
- publicación;
- operaciones externas de producción;
- shell libre;
- comandos arbitrarios;
- browser automation no gobernada;
- wake always-on real;
- openWakeWord activo;
- STT local pesado;
- TTS local pesado;
- descarga/compilación de modelos;
- daemon/tray real instalable;
- auto-start;
- auto mic/camera;
- grabación ambiental;
- envío de audio bruto al backend;
- graph DB/vector DB/cloud memory.

## Cómo Probar Local

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.

python -m py_compile $(find jarvis -name '*.py')

PYTHONPATH=. python -m pytest -c /dev/null \
  tests/jarvis/test_pr_166_phase_2_local_assistant_runtime.py \
  -q -x

PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20

git diff --check

cd web
npm run build
```

Si falta `node_modules`:

```bash
cd web
npm_config_cache=/tmp/jarvis-npm-cache-pr166 npm ci --fetch-retries=5 --fetch-retry-mintimeout=2000 --fetch-retry-maxtimeout=60000
npm run build
```

## Pilot Checklist

Validado por tests:

- rutas Phase 2;
- ausencia de `/execute`;
- catálogo allowlisted completo;
- denies de shell/secret/deploy/stripe/email;
- high -> strong;
- critical -> blocked si no hay double/triple;
- approval expirado no dispatch;
- approval single-use;
- wake no aprueba;
- voice no aprueba;
- readback high requerido;
- dispatch local allowlisted;
- dispatch `repo.file.read_safe` por bridge Hermes existente;
- historial metadata-only persistente con `tmp_path`;
- stop unsupported honesto;
- rollback `not_required`/`discard_preview`;
- voice low confidence clarification;
- wake readiness disabled/not_configured;
- local runtime readiness;
- browser verification status;
- dashboard/event stream Phase 2;
- frontend sin `/execute` ni Hermes directo.

Pendiente de pilot manual con navegador real:

- levantar backend local;
- levantar frontend;
- abrir `/jarvis`;
- verificar esfera/smart bar/drawers;
- comprobar capability real de STT/TTS del navegador;
- crear preview desde la UI;
- confirmar panel de approval;
- revisar event stream en navegador;
- confirmar no prompt de mic/camera al cargar.

## Riesgos Pendientes

- Double/triple real requiere canal separado futuro.
- Daemon/tray es readiness, no servicio instalado.
- Browser verification es estático/manual; Playwright no se añadió.
- `repo.tests.run_allowlisted` ejecuta solo el target fijo de PR166.
- Comandos git allowlisted son read-only/metadata pero dependen del repo local.
- Voice STT/TTS depende del navegador y puede usar servicios del navegador según implementación del browser.

## Siguiente Macro-Fase Recomendada

Phase 3 debería implementar un local runtime daemon/tray real con canales de aprobación fuerte multi-step, dispositivo confiable, UI de historial/stop persistente, browser verification automatizada si ya existe Playwright, y extensión progresiva del action catalog sin abrir shell libre.
