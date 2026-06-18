# PR #158 — Conversational Brain + Voice Session/Wake Architecture

Fecha: 2026-06-18

## Qué se implementó

- Conversational Brain Bridge v2 local/determinista en `jarvis/conversational_brain_bridge.py`.
  - Devuelve `human_response`, `intent_detected`, `confidence`, `risk_level`, `approval_level`, `requires_approval`, `can_prepare_preview`, `cannot_execute_reason`, `suggested_next_action` y `hermes_dispatch_allowed=false`.
  - No llama LLM, red, APIs externas, memoria ni Hermes.
  - Bloquea secretos, credenciales, cookies, tokens y `.env`.
  - Trata wake phrase como contexto/activación futura, nunca como aprobación o ejecución.
- Voice Session Manager read-only en `jarvis/voice_session_control.py`.
  - Estados formales: `idle`, `wake_listening_available`, `wake_listening_disabled`, `conversation_active`, `listening`, `transcribing`, `thinking`, `speaking`, `approval_required`, `cancelled`, `stopped`, `error`.
  - Separa wake listening, conversación activa, push-to-talk, STT, TTS, grabación raw audio, voice approval y Hermes execution.
  - Declara `raw_audio_sent_to_backend=false`, `transcript_persistence=false`, `background_transcription=false`, `always_on_stt=false`, `microphone_auto_start=false`.
- Wake Architecture contract.
  - Provider contract `openWakeWord`.
  - Dependency detection honesta vía `python_importlib`.
  - `auto_start=false`, `activation_endpoint_enabled=false`.
  - Frases: `Hola Jarvis`, `Jarvis`.
  - Stop phrases: `para`, `cancela`, `detente`, `silencio`, `cancelar misión`, `apaga escucha`.
  - Buffer efímero en memoria, sin persistencia de audio ni transcripción antes de activación válida.
- Dashboard/read model.
  - `GET /mark-3/conversational-brain/status`.
  - `GET /voice-runtime/session-status`.
  - `/mark-3/dashboard/status` añade `conversational_brain`, `voice_session` y `wake_architecture`.
  - `/mark-3/dashboard/events` y `/stream` añaden eventos `brain_state` y `voice_session_state` solo con metadata segura.
- UI `/jarvis`.
  - Smart bar muestra respuesta humana corta y deja detalles técnicos plegados.
  - Distingue `wake_listening_available/disabled` de `conversation_active`.
  - Expone que wake no aprueba, no ejecuta, no hay transcripción continua y no hay Hermes directo.
  - No añade POST/PUT/DELETE, `/execute`, approve/reject real, Hermes directo ni `getUserMedia` automático.

## Qué NO se implementó

- No se implementó wake always-on real.
- No se activó micrófono automáticamente.
- No se implementó STT/TTS local serio de backend.
- No se ejecuta Hermes desde intención, voz o frontend.
- No se añadió aprobación real desde `/jarvis`.
- No se graba ni envía audio bruto al backend.
- No se leen secretos, credenciales ni `.env`.
- No se añadieron dependencias nuevas.
- No se hizo deploy, commit, push, PR ni merge.

## Cómo probarlo

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
python -m py_compile $(find jarvis -name '*.py')
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_conversational_brain_bridge_v2.py tests/jarvis/test_voice_session_wake_architecture.py tests/jarvis/test_pr_158_dashboard_voice_brain_read_model.py tests/jarvis/test_pr_158_frontend_jarvis_contracts.py -q
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_jarvis_dashboard_status_read_model.py tests/jarvis/test_jarvis_dashboard_event_stream.py -q
git diff --check
cd web && npm run build
```

Para inspección manual:

```bash
GET /mark-3/conversational-brain/status
GET /voice-runtime/session-status
GET /mark-3/dashboard/status
GET /mark-3/dashboard/events
GET /mark-3/dashboard/events/stream
```

## Riesgos

- El bridge es determinista y útil como base, pero no sustituye un LLM gobernado real.
- El estado de wake `available` depende de dependencia instalada; aun disponible, sigue disabled por defecto.
- El Local Voice Loop sigue dependiendo de capacidades del navegador.
- `SpeechRecognition` del navegador puede usar servicios del proveedor del navegador; el backend no recibe audio.
- La suite completa `tests/jarvis -q` puede quedar bloqueada en `TestClient` en este entorno con Python 3.14/FastAPI/Starlette; validar con tests directos a endpoints cuando ocurra.

## Validaciones esperadas

- Brain bridge no hace eco simple y clasifica intención básica.
- Secretos/credenciales/`.env` quedan denegados.
- Wake phrase no aprueba y no ejecuta.
- Voice session separa wake/conversation/STT/TTS/recording/approval/Hermes.
- Dashboard status incluye voice session/wake architecture/conversational brain.
- Event stream no contiene audio bruto, frames, secretos ni comandos ejecutables.
- Frontend `/jarvis` no introduce `/execute`, Hermes directo, mutaciones peligrosas ni `getUserMedia` automático.

## Validaciones observadas en este entorno

- `python -m py_compile $(find jarvis -name '*.py')`: OK, sin salida.
- Tests específicos PR #158:
  `16 passed, 16 warnings in 1.49s`.
- Tests existentes dashboard/status/event stream:
  `43 passed, 43 warnings in 12.07s`.
- Validación alternativa directa de endpoints:
  `/health ok`, conversational brain schema v2, voice session schema v1 idle,
  dashboard read-only con `conversational_brain` y `voice_session`.
- `git diff --check`: OK, sin salida.
- `PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q`: quedó
  bloqueado en este entorno; relanzado con `-vv --maxfail=1` se detuvo al
  entrar en `tests/jarvis/test_api.py::test_health_ok`. Aislado con
  `timeout 30`, el test recogió 1 item y expiró con código 124 antes de
  completar `client.get("/health")`. Esto apunta a entorno/TestClient
  Python 3.14/FastAPI/Starlette, no a la lógica PR #158.
- `cd web && npm run build`: falló con `sh: 1: tsc: not found` porque
  `web/node_modules` no está instalado en este worktree. No se instalaron
  dependencias.

## Siguiente fase recomendada

1. Añadir intake preview gobernado para texto/voz que genere un mission preview auditado, todavía sin despacho Hermes.
2. Conectar un LLM local o proveedor explícito detrás de un contrato honesto `llm_called=true`, con red/gastos/gates visibles.
3. Diseñar STT/TTS local backend opt-in con indicadores visibles, retención cero y tests de audio metadata-only.
4. Implementar wake real solo si `openWakeWord` está instalado, disabled by default, con daemon local, stop/cancel y sensor ledger metadata-only.
5. Diseñar el futuro flujo intención -> preview -> approval -> Hermes dispatch -> audit -> rollback/stop sin exponer ejecución al frontend.
