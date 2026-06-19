# PR #169 - Phase 4 Real Local Controller + Remote Pairing Readiness

Fecha: 2026-06-19

## Resumen

PR #169 convierte la readiness de Phase 3 en una macro-fase local mas realista:
controlador local opt-in, identidad de controlador/dispositivo, triple approval
readiness con tres canales locales separados, remote pairing preparado pero
deshabilitado, Telegram/Hermes bridge readiness deshabilitada, stop/rollback v2
observable y pilot local documentado.

JARVIS sigue gobernando policy, riesgo, approvals, audit, stop/rollback y
readiness. Hermes sigue siendo solo el runtime ejecutor existente cuando una
accion allowlisted y aprobada lo requiere. No se crea otro Hermes, no se duplica
runtime y el frontend no ejecuta Hermes directamente.

No se implementa dinero, Stripe, deploy, email, publicacion externa, exposicion
publica, ejecucion remota libre, bot Telegram activo, webhook, servicios nativos,
autostart, puertos externos, shell libre, `/execute`, lectura de `.env`,
lectura de tokens ni APIs externas.

## Local Controller Opt-In

`Phase4LocalControllerRemotePairingControlPlane` extiende el control plane de
Phase 3 y modela un controlador local en memoria/proceso actual.

Contrato expuesto:

- `controller_id`
- `controller_status`
- `controller_mode`
- `local_only=true`
- `bind_host=127.0.0.1`
- `bind_port`
- `controller_url`
- `can_open_jarvis`
- `can_show_status`
- `can_show_approvals`
- `can_request_stop`
- `can_request_cancel`
- `can_toggle_voice_session`
- `can_toggle_camera_session`
- `can_toggle_recording_session`
- `auto_start_enabled=false`
- `installed_as_system_service=false`
- `startup_integration_enabled=false`
- `user_opt_in_required=true`
- `no_background_capture=true`
- `last_seen_at`
- `health_status`
- `failure_modes`

Endpoints:

- `GET /mark-3/local-controller/status`
- `POST /mark-3/local-controller/register`
- `POST /mark-3/local-controller/heartbeat`
- `POST /mark-3/local-controller/open-jarvis-request`
- `POST /mark-3/local-controller/stop-request`

Reglas:

- registro solo acepta controlador `local_only` y host local;
- bind externo queda rechazado;
- registro verificado requiere frase local exacta `VERIFY LOCAL CONTROLLER`;
- heartbeat actualiza metadata y audit;
- open request registra contrato, pero el backend no abre ventanas;
- stop request registra senal cooperativa observable, pero no mata procesos;
- no instala servicio, no toca startup y no abre puertos externos.

## Trusted Device Model

Phase 4 agrega `trusted_devices_status()` con identidad de dispositivo/control:

- `device_id`
- `controller_id`
- `display_name`
- `channel_type`
- `local_only`
- `trusted`
- `verified`
- `paired`
- `created_at`
- `last_seen_at`
- `trust_level`
- `risk_limit`
- `can_grant_normal`
- `can_grant_strong`
- `can_grant_double`
- `can_grant_triple`
- `revoked`
- `revoked_at`
- `audit_ids`

Modelo:

- remoto por defecto: cero dispositivos confiables y cero aprobaciones remotas;
- navegador local: trusted para normal/strong, pero no concede triple solo;
- terminal local: requiere challenge `VERIFY TERMINAL CHANNEL`;
- controlador local: requiere registro y verificacion;
- voz: readback only, no approval;
- wake phrase: disabled/no approval;
- Telegram/mobile: placeholders futuros disabled/untrusted;
- un dispositivo revocado no puede aprobar.

Endpoint:

- `GET /mark-3/trusted-devices/status`

## Triple Approval Readiness

Triple approval pasa de blocked permanente a readiness realista si hay tres
canales locales confiables y separados:

- `ui_local_browser`
- `terminal_local` verificado por challenge;
- `local_controller` registrado y verificado.

El envelope triple incluye:

- tres pasos;
- separacion de canal y tipo de canal;
- challenge/frase por paso;
- readback por paso;
- expiracion por paso;
- anti-reuse;
- audit por paso;
- recalculo de policy antes de la decision final.

Reglas:

- si no existen tres canales separados, critical sigue blocked;
- un canal repetido no satisface triple;
- frase incorrecta rechaza;
- paso expirado rechaza;
- paso reutilizado rechaza;
- voice/wake no aprueban;
- JARVIS recalcula policy antes de finalizar.

No se aprueba critical con un solo canal ni se finge triple cuando falta el
controlador verificado.

## Remote Pairing Readiness

Remote pairing queda preparado, pero deshabilitado:

- `pairing_status=disabled_readiness_only`
- `remote_pairing_enabled=false`
- `remote_approval_allowed=false`
- `remote_execution_allowed=false`
- `trusted_pairing_required=true`
- `pairing_code_created=false` por defecto
- `pairing_code_ttl_seconds=300`
- `pairing_challenge_required=true`
- `pairing_channel=local_ephemeral_challenge_only`
- `pairing_risk_limit=none_until_enabled_in_future_phase`
- `paired_devices_count=0`
- `pending_pairing_count`
- `revoked_pairing_count`
- `last_pairing_attempt_at`
- `audit_required=true`

Endpoints:

- `GET /mark-3/remote-pairing/status`
- `POST /mark-3/remote-pairing/prepare`
- `POST /mark-3/remote-pairing/cancel`
- `POST /mark-3/remote-pairing/revoke`

`prepare` crea un challenge local efimero en memoria, con TTL y audit. No abre
canal externo, no guarda token persistente, no lee secretos y no habilita
approval/ejecucion remota.

## Telegram / Hermes Bridge Readiness

Telegram/Hermes queda como readiness futura, no activa:

- `telegram_bridge_status=disabled_not_configured`
- `hermes_telegram_available_unknown_or_detected=unknown_not_imported_not_called`
- `token_present=unknown_redacted`
- `token_read=false`
- `env_read=false`
- `telegram_api_called=false`
- `bot_started=false`
- `webhook_opened=false`
- `remote_approval_allowed=false`
- `remote_execution_allowed=false`
- `pairing_required=true`
- `strong_approval_allowed=false`
- `can_receive_notifications_future=true`
- `can_request_approval_future=false`
- `can_execute_future=false`

Endpoint:

- `GET /mark-3/telegram-bridge/status`

No se importa ni llama Telegram, no se lee token, no se abre webhook y no se
envian mensajes.

## Stop / Rollback v2

Stop/Rollback v2 agrega observabilidad metadata-only:

- `stop_reason`
- `stop_actor`
- `stop_channel`
- `stop_scope`
- `stop_deadline`
- `stop_confirmation`
- `cooperative_stop_signal`
- `bridge_stop_attempt`
- `result_observed`
- `final_state`
- `rollback_plan_detail_metadata`
- `rollback_preconditions`
- `rollback_dry_run_mode`
- `rollback_approval_requirement`

Endpoint:

- `GET /mark-3/stop-rollback/status`

El controlador local puede registrar `stop-request`; el resultado honesto para
el backend embebido es `unsupported_embedded_backend_not_stopped`. Rollback
destructivo no se ejecuta ni se finge.

## API / Backend

GET anadidos:

- `/mark-3/phase-4/status`
- `/mark-3/local-controller/status`
- `/mark-3/trusted-devices/status`
- `/mark-3/remote-pairing/status`
- `/mark-3/telegram-bridge/status`
- `/mark-3/stop-rollback/status`

POST gobernados anadidos:

- `/mark-3/local-controller/register`
- `/mark-3/local-controller/heartbeat`
- `/mark-3/local-controller/open-jarvis-request`
- `/mark-3/local-controller/stop-request`
- `/mark-3/remote-pairing/prepare`
- `/mark-3/remote-pairing/cancel`
- `/mark-3/remote-pairing/revoke`

No existe `/execute`.

## UI `/jarvis`

El drawer incorpora paneles compactos:

- Phase 4 status;
- local controller;
- trusted devices;
- triple approval readiness;
- remote pairing readiness;
- Telegram bridge future status;
- stop/rollback v2;
- pilot checklist.

No se mueve JSON gigante al centro. Se preservan esfera, smart bar, approval
panel, voice loop, memory, audit y daemon/tray drawer. La esfera calmada de
PR #168 no se modifica.

## Security Gates

- JARVIS gobierna;
- Hermes ejecuta;
- no duplicate Hermes runtime;
- frontend no ejecuta Hermes directo;
- no shell libre;
- no comandos arbitrarios;
- no `/execute`;
- no wake approval;
- no voice approval;
- memoria no concede permisos;
- audit metadata-only;
- no `.env`;
- no tokens/passwords/cookies/session material;
- no Telegram API;
- no LLM externo;
- no cloud memory;
- no agentes externos;
- no puertos externos;
- no autostart;
- no servicio del sistema;
- no dinero, Stripe, deploy, email ni publicacion.

La frase exacta de credenciales se preserva:

```text
No puedo hacer eso, David. Las credenciales y secretos están protegidos.
```

## Como Probar Local

Backend:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
uvicorn jarvis.api.app:app --host 127.0.0.1 --port 9119
```

Frontend:

```bash
cd web
npm run dev -- --host 127.0.0.1
```

Status:

```bash
curl http://127.0.0.1:9119/mark-3/phase-4/status
curl http://127.0.0.1:9119/mark-3/local-controller/status
curl http://127.0.0.1:9119/mark-3/trusted-devices/status
curl http://127.0.0.1:9119/mark-3/remote-pairing/status
curl http://127.0.0.1:9119/mark-3/telegram-bridge/status
curl http://127.0.0.1:9119/mark-3/stop-rollback/status
```

## Repos Externas Revisadas

| Repo | URL | Licencia visible | Uso |
|---|---|---|---|
| `OpenInterpreter/open-interpreter` | https://github.com/OpenInterpreter/open-interpreter | AGPL-3.0 | Riesgos de controlador local/sandbox. No codigo. |
| `microsoft/autogen` | https://github.com/microsoft/autogen | MIT para codigo; CC-BY-4.0 docs | Patrones HITL/tool approval. No codigo. |
| `langchain-ai/langgraph` | https://github.com/langchain-ai/langgraph | MIT | State/checkpoint y pasos explicitos. No dependencia. |
| `OpenVoiceOS/ovos-core` | https://github.com/OpenVoiceOS/ovos-core | Apache-2.0 visible en repo/documentacion previa | Separacion runtime local/skills. No codigo. |
| `OpenVoiceOS/ovos-audio` | https://github.com/OpenVoiceOS/ovos-audio | Apache-2.0 visible en repo/documentacion previa | Separacion audio service. No codigo. |
| `home-assistant/core` | https://github.com/home-assistant/core | Apache-2.0 | Local-first/status/opt-in. No codigo. |
| `microsoft/PowerToys` | https://github.com/microsoft/PowerToys | MIT | Conceptos tray/controller Windows. No codigo. |
| `telegramdesktop/tdesktop` | https://github.com/telegramdesktop/tdesktop | GPL-3.0 con excepcion OpenSSL | Trust/client concepts. No codigo. |
| `python-telegram-bot/python-telegram-bot` | https://github.com/python-telegram-bot/python-telegram-bot | LGPL-3.0 | Readiness de bot sin dependencia. |
| `sigstore/rekor` | https://github.com/sigstore/rekor | Apache-2.0 | Audit transparency metadata-only. No servidor. |
| `google/trillian` | https://github.com/google/trillian | Apache-2.0 | Verifiable log conceptual. No infraestructura. |
| `Yelp/detect-secrets` | https://github.com/Yelp/detect-secrets | Apache-2.0 | Redaction/secret prevention ideas. No scanner. |
| `trufflesecurity/trufflehog` | https://github.com/trufflesecurity/trufflehog | AGPL-3.0 | Clases de credenciales. No copiar/instalar. |
| `semgrep/semgrep` | https://github.com/semgrep/semgrep | LGPL-2.1 | Guardrails conceptuales. No ruleset/dependencia. |

Codigo copiado externo: ninguno.

Patrones reimplementados localmente:

- contrato de controlador local opt-in;
- identidad de dispositivo/controlador;
- triple approval envelope con pasos;
- pairing challenge efimero local;
- Telegram bridge readiness disabled;
- stop/rollback v2 observable.

## Riesgos Pendientes

- controlador nativo/tray real sigue sin instalarse;
- registro de controlador es in-memory en esta fase;
- triple critical solo queda usable si tres canales locales se verifican;
- remote pairing sigue disabled;
- Telegram bridge no envia/recibe;
- rollback destructivo no existe;
- pilot browser manual sigue pendiente tras build/tests.

## Siguiente Macro-Fase Recomendada

Phase 5 deberia convertir el controlador local opt-in en proceso/tray real
instalable manualmente, con almacenamiento local seguro para identidad revocable,
pilot browser completo, hardening de pairing local y notificaciones remotas
solo despues de pairing explicitamente habilitado. Remote approval debe seguir
deshabilitado hasta tener threat model, revocation, rate limiting, audit
verificable y pruebas negativas.
