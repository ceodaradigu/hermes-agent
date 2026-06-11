# Post-S Macro 6 - Local Wake Voice Runtime & Camera Control

Esta macro PR consolida contratos y endpoints control-plane para wake phrase
local, sesiones de voz y cámara opt-in. Es prepare-only: interpreta texto de
preview, representa decisiones y publica estado seguro, pero no activa sensores,
no ejecuta y no llama servicios externos.

## Por qué no es Phase T

Phase S sigue siendo la última fase maestra implementada. No existe Phase T.
Este trabajo es transversal post-S y mantiene todos los límites de policy,
approval, strong approval, permission gates, controlled runtime, tool gates y
auditoría.

## Wake phrase y sesión

Las wake phrases soportadas son **"Hola Jarvis"** y **"Jarvis"**. Deben aparecer
al inicio del transcript para reducir falsos positivos cuando Jarvis sea una
palabra normal.

- `"Hola Jarvis"` y `"Jarvis"` abren una sesión preview y responden que JARVIS
  está escuchando.
- `"Hola Jarvis, resume el estado"` extrae `resume el estado`.
- `"Jarvis prepara la siguiente PR"` extrae `prepara la siguiente PR`.
- Si la orden viene detrás de la wake phrase no se exige una segunda frase.
- Baja confianza bloquea el procesamiento y cualquier acción sensible.

La wake phrase no es permiso. Voz no evita `PolicyEngine`, approvals, strong
approval, controlled runtime ni tool gates. Una orden como `"Jarvis despliega
producción"` se clasifica como crítica, exige strong approval y doble
confirmación, y nunca se ejecuta en esta macro. Restrictions are approval gates,
not permanent bans.

Push-to-talk permanece como fallback explícito cuando wake listening está
deshabilitado. Las stop phrases de voz son `no escuches`, `para`, `cállate`,
`stop` y `detente`.

## Privacidad de audio y cámara

Wake listening está deshabilitado por defecto, es local-only y no existe
background listening sin configuración/aprobación futura explícita. No se
retiene audio, no se graba y no se envía audio a servicios externos.

La cámara requiere opt-in explícito e indicador visible. `no mires` representa
el stop inmediato. Incluso con opt-in, la preview no activa cámara, no graba,
no analiza personas/caras, no captura pantalla y no envía vídeo externamente.

## API control-plane

- `GET /voice-runtime/status`
- `GET /voice-runtime/policy`
- `POST /voice-runtime/preview-wake-parse`
- `POST /voice-runtime/preview-session`
- `POST /voice-runtime/preview-command`
- `POST /voice-runtime/preview-stop`
- `GET /camera-control/status`
- `GET /camera-control/policy`
- `POST /camera-control/preview-session`
- `POST /camera-control/preview-stop`

No existen rutas de start-microphone, record, stream, send-audio, execute, run,
call-tool, deploy, pay, start-camera, send-video, analyze-face, capture-screen
o watch.

## Qué no hace

No activa micrófono o cámara, no graba audio/vídeo, no hace streaming, no llama
Hermes/tools/red/GitHub/navegador/APIs, no lee secretos, no muta missions/tasks,
no envía mensajes, no despliega, no paga y no toca producción.
`execution_enabled=false` y `side_effects_enabled=false` permanecen forzados.

## Siguiente macro PR

Esta capa prepara **PR #123 - Monetization Engine Real**, que también
deberá conservar approvals, separación projected/confirmed y el límite
prepare-only mientras no exista autorización explícita de ejecución.

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_post_s_local_wake_voice_camera_control.py -q
pytest tests/jarvis/test_e2e_prepare_only_smoke_after_phase_s.py -q
pytest tests/jarvis -q -x --durations=20
```
