# JARVIS Mark 2 Macro 1 - Local Daemon, Real Wake Listener, Desktop Runtime & Voice Approval

## Qué empieza Mark 2

Mark 1 quedó cerrado como Release Candidate con governance, audit, permission
gates, approval-controlled execution semantics, controlled runtime bridge,
tools, memoria, Personal OS, scheduler, voice/camera control-plane,
monetización, Adaptive SaaS Builder y consolas operacionales.

Esta PR empieza Mark 2 con contratos reales para un runtime local controlado,
pero no completa Mark 2. No activa herramientas externas, browser, GitHub,
Stripe live, deploy, UI avanzada, multiagente ni operación 24/7. La siguiente
macro es **Mark 2 Macro 2 — Real Tool Execution: Browser, GitHub, Filesystem &
APIs**.

## Runtime local seguro

`LocalDaemonStatus` y `LocalDaemonCommandPreview` definen estado, healthcheck,
shutdown seguro, kill switch y previews de start/stop. El daemon está
disponible pero desactivado, no corre, no tiene auto-start y no instala un
servicio del sistema.

`DesktopRuntimeState` define los modos `disabled`, `standby`, `listening`,
`processing`, `awaiting_approval`, `executing` y `stopped`. Escuchar exige un
estado visible. Una acción crítica no puede pasar a ejecución desde este
preview. Kill switch y stop phrase permanecen disponibles.

`LocalRuntimeSafetyPolicy` mantiene micrófono/cámara con opt-in, red y tools
externas desactivadas por defecto, audit obligatorio, expiración y strong
approval para producción o dinero. **Restrictions are approval gates, not
permanent bans.**

## Real Wake Listener preparado

`RealWakeListenerPlan` prepara las wake phrases `Hola Jarvis` y `Jarvis`, stop
phrases, manejo de ruido, falsos positivos, audit y proveedor local futuro. El
micrófono real está desactivado por defecto y solo podrá elegirse con opt-in
local explícito y un indicador visible. Los tests no acceden al micrófono.
No se graba ni transmite audio y no se llama una API externa de speech.

Una wake phrase inicia una sesión, nunca concede permiso:

- `Hola Jarvis` despierta y no aprueba.
- `Jarvis, despliega producción` extrae el comando e inicia el approval flow;
  no ejecuta.

## La voz puede aprobar, la wake phrase no puede aprobar

`VoiceApprovalChannel` permite usar una confirmación hablada explícita como
canal de approval. La wake phrase no es una confirmación. El canal está
desactivado por defecto y sus endpoints son previews.

Para una acción crítica JARVIS lee acción, riesgo, coste, impacto de producción
y rollback/stop plan. Después exige:

1. Primera confirmación: `Sí, continúa`.
2. Confirmación fuerte exacta: `JARVIS, entiendo los riesgos, hazlo`.
3. Para riesgo muy alto puede exigir `JARVIS, confirmación final`.

`Sí` solo, `JARVIS hazlo` fuera del contexto correcto, una frase incorrecta,
ruido o una approval expirada no aprueban. El resultado válido puede quedar
`eligible_after_valid_voice_approval=true`, pero conserva
`would_execute=false` en esta PR.

## Audit local

`LocalAuditEvent` registra actor, canal, acción resumida, riesgo, presencia de
readback, hash/redacción de la frase, coste, impacto, rollback/stop plan,
resultado y expiración. No guarda audio bruto, no guarda secretos y no necesita
persistencia externa. El transcript completo está desactivado por defecto.

## Endpoints control-plane

- `GET /mark-2/local-daemon/status`
- `GET /mark-2/desktop-runtime/status`
- `GET /mark-2/local-runtime/safety-policy`
- `GET /mark-2/wake-listener/status`
- `POST /mark-2/wake-listener/preview-transcript`
- `GET /mark-2/voice-approval/status`
- `POST /mark-2/voice-approval/preview-start`
- `POST /mark-2/voice-approval/preview-confirm`
- `POST /mark-2/voice-approval/preview-flow`
- `GET /mark-2/local-daemon/command-preview`
- `GET /mark-2/local-audit/preview`

No existen rutas para start-real, install-service, start-microphone, record,
stream, approve-all, auto-approve, execute, deploy, pay, publish, create-repo o
write-files.

## Integración con Mark 1

La clasificación strong/critical reutiliza `StrongApprovalPolicy`; la
elegibilidad del flow reutiliza `GlobalApprovalExecutionSemantics`; wake parsing
y command classification reutilizan `WakeVoiceRuntime` y
`VoiceSessionControl`. Approval de voz sigue siendo autorización limitada y
auditable, no ejecución.

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_mark_2_local_daemon_real_wake_desktop_runtime_voice_approval.py -q
pytest tests/jarvis -q -x --durations=20
```
