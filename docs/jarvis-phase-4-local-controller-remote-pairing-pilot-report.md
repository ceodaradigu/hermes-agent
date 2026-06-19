# JARVIS Phase 4 Local Controller + Remote Pairing Pilot Report

Fecha: 2026-06-19

## Estado

Phase 4 incluye pilot local con evidencia automatizada y checklist manual. El
pilot no abre puertos externos, no activa mic/camera/wake automaticamente, no
ejecuta Hermes desde frontend, no introduce `/execute`, no activa Telegram y no
habilita remote approval/execution.

## Validated By Automated Tests

Comando principal:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
PYTHONPATH=. python -m pytest -c /dev/null \
  tests/jarvis/test_pr_169_phase_4_real_local_controller_remote_pairing_readiness.py \
  -q -x
```

Cobertura:

- `GET /mark-3/phase-4/status` existe;
- no existe `/execute`;
- local controller `local_only=true`;
- `auto_start_enabled=false`;
- `installed_as_system_service=false`;
- `startup_integration_enabled=false`;
- `no_background_capture=true`;
- bind externo rechazado;
- register/heartbeat metadata-only con audit;
- open-jarvis request no abre browser desde backend;
- stop request registra actor/channel/scope/deadline y resultado honesto;
- trusted devices status existe;
- remote devices default zero/untrusted;
- local browser trust limitado;
- terminal trust requiere challenge;
- controller trust requiere registro y verificacion;
- revoked device no aprueba;
- triple requiere separacion de canal;
- un canal no satisface triple;
- expired step rechazado;
- reused step rechazado;
- wrong phrase rechazada;
- critical blocked sin tres canales confiables;
- voice/wake no aprueban;
- remote pairing disabled por defecto;
- remote approval false;
- remote execution false;
- prepare crea challenge local efimero solo en memoria/test;
- cancel/revoke auditados;
- no tokens/secrets;
- Telegram disabled/not_configured;
- no token read;
- no API call;
- remote approval/execution false;
- rollback dry-run metadata;
- rollback destructivo no ejecutado;
- UI drawer declara phase4/controller/devices/pairing/telegram;
- no JSON central;
- orb idle contract de #168 preservado;
- frase exacta de credenciales preservada:
  `No puedo hacer eso, David. Las credenciales y secretos están protegidos.`

## Validated By Full Jarvis Suite

Comando:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20
```

Resultado registrado en validacion final de la PR.

## Validated By Build

Comando:

```bash
cd web
npm run build
```

Estado de esta ejecucion de validacion:

- `npm run build` se intento y fallo antes de compilar porque `tsc` no estaba
  disponible (`node_modules` ausente);
- se intento la ruta permitida `npm_config_cache=/tmp/jarvis-npm-cache-pr169 npm ci ...`;
- `npm ci` fallo por DNS contra `registry.npmjs.org` con `EAI_AGAIN`;
- `package.json` y `package-lock.json` no fueron modificados;
- build frontend queda pendiente hasta tener dependencias locales instalables.

Cuando `node_modules` este disponible, el build debe validar que los tipos
frontend, drawer Phase 4 y read model compilan sin modificar `package.json` ni
`package-lock.json`.

## Backend Start Command

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
uvicorn jarvis.api.app:app --host 127.0.0.1 --port 9119
```

Expected:

- bind local;
- endpoints `/mark-3/phase-4/status`, `/mark-3/local-controller/status`,
  `/mark-3/trusted-devices/status`, `/mark-3/remote-pairing/status`,
  `/mark-3/telegram-bridge/status` y `/mark-3/stop-rollback/status`;
- no `/execute`.

## Frontend Start Command

```bash
cd web
npm run dev -- --host 127.0.0.1
```

Abrir `/jarvis`.

Expected:

- esfera de particulas calmada en idle;
- smart bar visible;
- approval panel visible;
- voice loop no auto-start;
- camera no auto-start;
- recording no auto-start;
- drawer con Phase 4, local controller, trusted devices, triple approval,
  remote pairing, Telegram bridge, stop/rollback v2 y pilot checklist;
- no JSON gigante en centro.

## Status Endpoint Checks

```bash
curl http://127.0.0.1:9119/mark-3/phase-4/status
curl http://127.0.0.1:9119/mark-3/local-controller/status
curl http://127.0.0.1:9119/mark-3/trusted-devices/status
curl http://127.0.0.1:9119/mark-3/remote-pairing/status
curl http://127.0.0.1:9119/mark-3/telegram-bridge/status
curl http://127.0.0.1:9119/mark-3/stop-rollback/status
```

Expected:

- JSON metadata-only;
- local controller local-only;
- remote pairing disabled;
- Telegram disabled;
- remote approval false;
- remote execution false;
- audit required;
- errores honestos.

## Local Controller Register / Heartbeat

Registro verificado:

```bash
curl -X POST http://127.0.0.1:9119/mark-3/local-controller/register \
  -H 'Content-Type: application/json' \
  -d '{"controller_id":"phase4-local-controller","verification_phrase":"VERIFY LOCAL CONTROLLER","local_only":true,"bind_host":"127.0.0.1"}'
```

Heartbeat:

```bash
curl -X POST http://127.0.0.1:9119/mark-3/local-controller/heartbeat \
  -H 'Content-Type: application/json' \
  -d '{"controller_id":"phase4-local-controller"}'
```

Expected:

- controller registrado/verificado;
- `last_seen_at` actualizado;
- audit metadata-only;
- no servicio instalado;
- no startup modificado.

## Triple Approval Blocked / No Three Channels

Estado por defecto:

```bash
curl http://127.0.0.1:9119/mark-3/phase-4/status
```

Expected:

- `triple_approval_readiness.can_grant_triple=false`;
- `blocked_reason` explica que critical requiere browser local, terminal local
  verificado y local controller verificado;
- voice/wake no aprueban.

## Remote Pairing Disabled

Prepare:

```bash
curl -X POST http://127.0.0.1:9119/mark-3/remote-pairing/prepare \
  -H 'Content-Type: application/json' \
  -d '{"actor":"David","channel":"local_controller"}'
```

Expected:

- `pairing_status=prepared_local_ephemeral_challenge_remote_disabled`;
- challenge local efimero con TTL;
- `remote_pairing_enabled=false`;
- `remote_approval_allowed=false`;
- `remote_execution_allowed=false`;
- `external_channel_opened=false`;
- no token persistente.

Cancel/revoke:

```bash
curl -X POST http://127.0.0.1:9119/mark-3/remote-pairing/cancel \
  -H 'Content-Type: application/json' \
  -d '{"actor":"David","reason":"pilot cleanup"}'

curl -X POST http://127.0.0.1:9119/mark-3/remote-pairing/revoke \
  -H 'Content-Type: application/json' \
  -d '{"actor":"David","device_id":"future-device","reason":"pilot revoke"}'
```

Expected:

- audit metadata-only;
- approval/execution remota siguen false.

## Telegram Bridge Disabled

```bash
curl http://127.0.0.1:9119/mark-3/telegram-bridge/status
```

Expected:

- `telegram_bridge_status=disabled_not_configured`;
- `token_present=unknown_redacted`;
- `token_read=false`;
- `env_read=false`;
- `telegram_api_called=false`;
- `bot_started=false`;
- `webhook_opened=false`;
- `remote_approval_allowed=false`;
- `remote_execution_allowed=false`.

## Denied Credentials Test

Intentar una intencion de leer `.env`, token, cookies, passwords o session
material.

Expected exact phrase:

```text
No puedo hacer eso, David. Las credenciales y secretos están protegidos.
```

No debe aparecer contenido secreto en audit, history, event stream ni UI.

## No Direct Hermes / No Execute

Checks:

- API no expone `/execute`;
- UI no contiene llamadas directas a Hermes;
- no hay shell freeform desde frontend;
- solo hay endpoints gobernados y allowlisted.

## Audit Metadata-Only

Expected:

- audit ids presentes;
- metadata segura;
- no audio bruto;
- no frames;
- no command output sensible;
- no `.env`;
- no tokens/passwords/cookies/session material.

## Pending Manual Browser Pilot

Pendiente de validacion manual en navegador:

1. abrir `/jarvis`;
2. inspeccionar drawer Phase 4;
3. confirmar que la esfera idle permanece calmada;
4. confirmar que no hay prompt automatico de microfono;
5. confirmar que no hay prompt automatico de camara;
6. confirmar que no hay recording activo;
7. confirmar que remote pairing y Telegram muestran disabled;
8. confirmar que el centro no se convierte en panel JSON.

## Unsupported Honestly

- tray/controller nativo no instalado;
- Windows service install no implementado;
- startup integration no modificada;
- remote pairing no habilitado;
- remote approval no habilitado;
- remote execution no habilitado;
- Telegram bot no iniciado;
- Telegram API no llamada;
- webhook no abierto;
- rollback destructivo no ejecutado;
- stop de proceso externo no soportado para backend embebido;
- identidad de controlador persiste solo en memoria en Phase 4.
