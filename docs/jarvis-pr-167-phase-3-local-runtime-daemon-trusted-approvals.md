# PR #167 - Phase 3 Local Runtime Daemon + Trusted Approval Channels

Fecha: 2026-06-19

## Resumen

PR #167 convierte el runtime local de JARVIS en una capa mas real sin crear otro
Hermes. JARVIS sigue gobernando policy, riesgo, approval, audit, stop/rollback
e historial. Hermes sigue siendo solo el ejecutor existente cuando una accion
allowlisted lo requiere.

La fase implementa daemon local embebido, readiness de tray/local controller,
trusted approval channels, double approval real, stop/rollback observable,
execution history v2, local doctor, browser/local pilot y readiness de
Telegram/mobile futuro deshabilitada.

No implementa dinero, Stripe, deploy, email, publicacion externa,
automatizacion destructiva, shell libre, `/execute`, autostart del sistema,
servicios nativos, puertos externos, cloud memory ni APIs externas.

## Daemon Local

`Phase3LocalRuntimeControlPlane.local_daemon_status()` modela un daemon local
gobernado por el proceso API actual:

- `daemon_id`
- `daemon_status=running_embedded_local_api_process`
- `pid`
- `started_at`
- `uptime`
- `host`
- `bind_host=127.0.0.1`
- `bind_port=9119`
- `local_only=true`
- `auto_start_enabled=false`
- `background_listening_enabled=false`
- `camera_auto_start=false`
- `mic_auto_start=false`
- `wake_auto_start=false`
- `state_dir`
- `audit_dir`
- `log_dir`
- `health_status`
- `last_heartbeat_at`
- `stop_supported=false`
- `restart_supported=false`
- `failure_modes`
- `user_opt_in_required=true`

Endpoints:

- `GET /mark-3/local-daemon/status`
- `GET /mark-3/local-daemon/health`
- `POST /mark-3/local-daemon/heartbeat`
- `POST /mark-3/local-daemon/stop-request`
- `POST /mark-3/local-daemon/restart-request`

Los POSTs solo afectan metadata/control del runtime local JARVIS. No aceptan
shell, comandos arbitrarios ni texto ejecutable. Stop/restart devuelven
unsupported honesto porque no hay servicio externo que detener o reiniciar en
esta fase.

## Tray / Local Controller Readiness

Se modela readiness de tray/local controller sin dependencia pesada:

- `tray_available=true`
- `tray_installed=false`
- `tray_running=false`
- `tray_controls_supported=true`
- `can_open_jarvis=true`
- `can_stop_daemon=false`
- `can_show_approval=true`
- `can_show_status=true`
- `can_toggle_voice_session=true`
- `can_toggle_camera_session=true`
- `can_toggle_recording_session=true`
- `requires_user_opt_in=true`
- `no_background_capture=true`

No se instala Electron, Tauri, pystray ni servicio de sistema.

## Trusted Approval Channels

Canales modelados:

- `ui_local_browser`
- `terminal_local`
- `tray_local_not_installed`
- `voice_readback_only`
- `wake_phrase_disabled`
- `telegram_future_disabled`
- `mobile_future_disabled`

Cada canal declara `channel_id`, `channel_type`, `trusted`, `enabled`,
`authenticated`, `local_only`, capacidades de approval, cancel/stop,
presencia, readback, confirmation phrase, risk limit, audit y
`last_verified_at`.

Reglas:

- UI local browser puede aprobar normal/strong si el challenge textual es
  valido.
- Terminal local puede aprobar strong/double tras `verify` local.
- Voice no aprueba; solo readback.
- Wake no aprueba.
- Telegram/mobile quedan disabled y no autentican.
- Triple requiere canales adicionales independientes y queda blocked.
- Backend recalcula policy/risk antes de aceptar approval.
- Todo se audita metadata-only.

Endpoints:

- `GET /mark-3/trusted-approval-channels/status`
- `POST /mark-3/trusted-approval-channels/verify`
- `POST /mark-3/approval/strong-decision`
- `POST /mark-3/approval/double-decision`
- `POST /mark-3/approval/triple-decision`

## Strong / Double / Triple Approval

Strong mantiene Phase 2 v2: readback, confirmation phrase, expiry, single-use,
action binding y policy recalculation.

Double approval ahora crea dos pasos:

- mismo `approval_id`;
- `step_id=step-1` y `step_id=step-2`;
- caducidad por paso;
- confirmation phrase por paso;
- readback obligatorio;
- canales separados;
- anti-reuse;
- audit por paso.

Triple queda blocked con:

```text
triple_requires_additional_trusted_channel_not_configured
```

No se finge critical approval sin tres canales independientes.

## Stop / Rollback Observable

Stop incluye `stop_request_id`, `execution_id`, `action_id`, `requested_at`,
`requested_by`, `stop_status`, `bridge_stop_supported`,
`process_stop_supported`, `cooperative_stop_requested`, `confirmed_stopped`,
`timeout_seconds` y `final_status`.

Rollback incluye `rollback_request_id`, `rollback_plan_id`,
`rollback_status`, `rollback_supported`, `rollback_requires_approval`,
`rollback_limitations` y `rollback_audit_id`.

Read-only usa `not_required`. Prepare-only usa `discard_preview`. Side effects
futuros requieren rollback plan antes de poder ejecutarse.

## Execution History v2

`ExecutionHistoryStore` sube a `jarvis.execution_history.v2`.

Mejoras:

- filtros por `action_key`, `risk`, `approval_status`, `stop_status`,
  `rollback_status`;
- ultimos N;
- detalle por `execution_id`;
- export preview metadata-only;
- `audit_ids`;
- `memory_influence_ids`;
- `channel_ids`;
- redaction summary;
- stop/rollback ids.

No guarda secretos, credenciales, audio bruto, frames, outputs completos
sensibles ni contenido de `.env`.

Endpoints:

- `GET /mark-3/execution/history`
- `GET /mark-3/execution/history/{execution_id}`
- `GET /mark-3/execution/history/export-preview`

## Local Doctor

`GET /mark-3/local-doctor/status` comprueba sin leer secretos:

- Python env;
- import basico de paquete;
- FastAPI app import;
- build frontend si existe;
- state dir writable;
- audit dir writable;
- memory db reachable;
- execution history db reachable;
- bind host local seguro;
- no external bind;
- no `.env` exposed;
- no `.jarvis` tracked;
- package lock limpio;
- `node_modules` status;
- browser status unknown/manual;
- voice/wake readiness.

No lee `.env`, no ejecuta scanners pesados y no instala dependencias.

## Browser / Local Pilot

Se crea `docs/jarvis-phase-3-local-runtime-pilot-report.md` con checklist
manual, endpoints, comandos backend/frontend, expected outputs, pruebas de
approval, denied credentials, safe action, history, audit, stop, daemon
readiness, trusted channels, no auto mic/camera y no `/execute`.

## UI `/jarvis`

`JarvisDebugDrawer` agrega secciones compactas para daemon status, tray
readiness, trusted approval channels, double approval steps, stop/rollback,
execution history v2, local doctor, phase 3 readiness, pilot checklist y
Telegram/mobile future readiness.

No se reemplaza el centro por JSON. Se preservan esfera, smart bar, voice loop,
approval panel, camera opt-in, raw recording opt-in, memory drawer y audit
drawer.

## Remote Bridge Future Readiness

Queda readiness deshabilitada:

- `telegram_bridge_status=disabled_not_configured`
- `mobile_bridge_status=disabled_not_configured`
- `remote_approval_allowed=false`
- `remote_execution_allowed=false`
- `trusted_pairing_required=true`

No hay tokens, bot real, llamadas externas ni lectura de variables secretas.

## Endpoints Nuevos

GET:

- `/mark-3/phase-3/status`
- `/mark-3/local-daemon/status`
- `/mark-3/local-daemon/health`
- `/mark-3/local-doctor/status`
- `/mark-3/trusted-approval-channels/status`
- `/mark-3/execution/history`
- `/mark-3/execution/history/{execution_id}`
- `/mark-3/execution/history/export-preview`

POST gobernados:

- `/mark-3/local-daemon/heartbeat`
- `/mark-3/local-daemon/stop-request`
- `/mark-3/local-daemon/restart-request`
- `/mark-3/trusted-approval-channels/verify`
- `/mark-3/approval/strong-decision`
- `/mark-3/approval/double-decision`
- `/mark-3/approval/triple-decision`

No existe `/execute`.

## Repos Externas Revisadas

| Repo | Licencia visible | Uso |
|---|---|---|
| `OpenInterpreter/open-interpreter` | Apache-2.0 | Ideas de permisos/sandbox local. No codigo. |
| `microsoft/autogen` | MIT, docs CC-BY-4.0 | Patrones de human-in-loop. No codigo. |
| `langchain-ai/langgraph` | MIT | Inspiracion de state/checkpoint/human-in-loop. No codigo. |
| `crewAIInc/crewAI` | MIT | Orquestacion conceptual. No dependencia. |
| `OpenVoiceOS/ovos-core` | Apache-2.0 | Separacion voice runtime/skills. No codigo. |
| `OpenVoiceOS/ovos-audio` | Apache-2.0 | Separacion audio service. No codigo. |
| `dscripka/openWakeWord` | Apache-2.0 code, models CC BY-NC-SA 4.0 | Wake readiness only. No modelo ni runtime. |
| `getzep/graphiti` | Apache-2.0 | Provenance temporal memory conceptual. |
| `mem0ai/mem0` | Apache-2.0 | Memory influence/lifecycle conceptual. |
| `sigstore/rekor` | Apache-2.0 | Transparencia/audit metadata. |
| `google/trillian` | Apache-2.0 | Log verificable conceptual. |
| `Yelp/detect-secrets` | Apache-2.0 | Redaction/secret prevention ideas. |
| `trufflesecurity/trufflehog` | AGPL-3.0 | No copiar ni instalar. Solo conceptos. |
| `semgrep/semgrep` | LGPL-2.1 | No integrar. Solo reglas conceptuales. |
| `mattermost/mattermost` | Multiple notices | Multi-channel approval concepts only. |

Codigo copiado externo: ninguno.

## Seguridad

- No `/execute`.
- No shell libre.
- No comandos arbitrarios.
- No frontend directo a Hermes.
- No wake approval.
- No voice approval.
- No auto mic/camera/wake.
- No audio bruto nuevo.
- No frames.
- No `.env` read.
- No tokens/passwords/cookies/session material.
- No APIs externas.
- No cloud memory.
- No agentes externos.
- No dependencias pesadas.
- No autostart ni servicio de sistema.
- No puertos externos.

## Siguiente Macro-Fase Recomendada

Phase 4 deberia implementar un tray/local controller real opt-in y un canal
adicional independiente para triple approval. Despues de eso, se puede preparar
pairing remoto gobernado, todavia sin ejecucion remota libre.
