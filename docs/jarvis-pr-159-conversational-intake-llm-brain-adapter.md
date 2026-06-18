# PR #159 — Phase 1 Conversational Intake + LLM Brain Adapter

Fecha: 2026-06-18

## Qué se implementó

- `jarvis/conversational_intake.py`
  - `ConversationalIntakePipeline` normaliza texto escrito, transcripciones de voz, comandos tras wake phrase y futuros inputs remotos.
  - Genera `ConversationalIntake` serializable con `schema_version`, `intake_id`, `created_at`, `source`, `raw_text`, `normalized_text`, `language`, `wake_phrase_detected`, `wake_phrase_used`, `remaining_command`, `operator`, `session_id`, `voice_session_state`, `transcript_confidence`, flags de material sensible, aclaración y `safe_to_dispatch_to_hermes=false`.
  - Clasifica intención/riesgo en modo local determinista y prepara `preview_candidate` cuando es seguro.
  - Detecta `.env`, credenciales, tokens, passwords, cookies y material de sesión como bloqueado/denegado para ejecución.
  - Baja confianza y ambigüedad piden aclaración.
- `jarvis/llm_brain_adapter.py`
  - Contratos `BrainRequest`, `BrainResponse` y `BrainProviderStatus`.
  - Provider por defecto `deterministic_local`, usando el bridge local existente.
  - Provider `disabled_external_llm` visible y deshabilitado por defecto.
  - `external_llm_enabled=false`, `external_provider_called=false`, `reads_env=false`, `network_allowed=false`, `api_key_loaded=false`.
  - `BrainRequest` redacta material sensible antes del cerebro y no transporta audio bruto ni frames.
  - `BrainResponse` devuelve respuesta humana, intención, confianza, riesgo, approval level, preview, siguiente acción, evidencia, incertidumbre y auditoría sin permitir Hermes dispatch.
- API/read model/UI:
  - Nuevos GET read-only: `/mark-3/conversational-intake/status` y `/mark-3/brain-adapter/status`.
  - `/mark-3/dashboard/status` expone `conversational_intake` y `brain_adapter`.
  - `/mark-3/dashboard/events` y `/stream` añaden `intake_state` y `brain_adapter_state` solo con metadata segura.
  - `/jarvis` muestra de forma compacta provider actual, external called false y riesgo de intake; detalles técnicos quedan plegados en `Sistemas`.
- Tests de PR #159:
  - Normalización, wake phrase, bloqueo de credenciales, baja confianza, ambigüedad, pregunta simple, preview de misión/tarea, dinero/deploy/email/comando/install gates, request/response del brain, provider externo disabled, dashboard/event stream, frontend y voz.

## Qué NO se implementó

- No se activó LLM externo real.
- No se llamó OpenAI, Anthropic, Gemini ni otro proveedor.
- No se leyó `.env` ni variables secretas.
- No se añadieron API keys.
- No se guardaron prompts privados.
- No se envió texto privado fuera del repo.
- No se activó Hermes dispatch desde conversación.
- No se añadió `/execute`.
- No se añadieron POST/PUT/DELETE desde `/jarvis`.
- No se añadió approve/reject real desde `/jarvis`.
- No se activó micrófono, cámara, wake real, STT/TTS local serio ni grabación automática.
- No se instalaron dependencias nuevas.
- No se hizo commit, push, PR ni merge.

## Por qué no se activó LLM externo real

Esta PR prepara el contrato seguro y verificable antes de conectar proveedores. Activar un LLM externo ahora rompería los límites de Fase 1: requeriría gates de configuración, política de coste, red, privacidad, auditoría, prompt handling, no-secret guarantees y evidencia honesta de llamadas. Por eso el provider real por defecto es `deterministic_local` y el externo queda declarado como `disabled_external_llm`.

## Cómo probar

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.

python -m py_compile $(find jarvis -name '*.py')
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_pr_159_conversational_intake_llm_brain_adapter.py -q
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_pr_158_dashboard_voice_brain_read_model.py tests/jarvis/test_pr_158_frontend_jarvis_contracts.py -q
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20
git diff --check
cd web && npm run build
```

Endpoints manuales:

```text
GET /mark-3/conversational-intake/status
GET /mark-3/brain-adapter/status
GET /mark-3/dashboard/status
GET /mark-3/dashboard/events
GET /mark-3/dashboard/events/stream
GET /jarvis
```

## Validaciones

- Wake phrase nunca aprueba y nunca ejecuta.
- Approval no es ejecución.
- Memoria no concede permisos.
- `.env`, credenciales, tokens, passwords, cookies y material de sesión quedan bloqueados.
- Dinero, Stripe, pagos, deploy, producción, email, comandos e instalación de dependencias requieren gates fuertes antes de cualquier ejecución futura.
- Input ambiguo o transcripción de baja confianza pide aclaración.
- `BrainRequest` redacta material sensible y declara no audio bruto/no frames.
- `BrainResponse` declara `external_provider_called=false`.
- Provider externo queda disabled by default.
- Event stream no transporta raw text sensible, audio bruto, frames ni comandos ejecutables.
- Frontend `/jarvis` no llama Hermes, no añade `/execute` y no introduce mutaciones peligrosas.

## Validaciones observadas en este entorno

- `python -m py_compile $(find jarvis -name '*.py')`: OK, sin salida.
- `PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_pr_159_conversational_intake_llm_brain_adapter.py -q -x`:
  `22 passed, 22 warnings in 1.86s`.
- `PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_pr_158_dashboard_voice_brain_read_model.py tests/jarvis/test_pr_158_frontend_jarvis_contracts.py -q -x`:
  `6 passed, 6 warnings in 1.91s`.
- `PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20`:
  se interrumpió con código 130 tras más de cuatro minutos sin resumen ni fallo
  visible. Relanzado con `timeout 90 env PYTHONPATH=. python -m pytest -c
  /dev/null tests/jarvis -vv -x --durations=20`, recogió `1940 items`, avanzó
  hasta `tests/jarvis/test_api.py::test_health_ok` y `timeout` cerró con código
  124. Validación directa del endpoint sin `TestClient`: `{'status': 'ok'}` y
  `routes 406`. Causa probable: bloqueo de `fastapi.testclient.TestClient` en
  este entorno Python 3.14/FastAPI/Starlette, ya observado en el cierre de #158.
- `git diff --check`: OK, sin salida.
- `cd web && npm run build`: falló con código 127:
  `sh: 1: tsc: not found`.
- `cd web && npm ci`: falló con código 1 durante `esbuild` postinstall:
  `spawnSync .../web/node_modules/esbuild/bin/esbuild EPERM`; Node.js
  `v22.22.1`. El binario respondió versión `0.27.4`, pero el sandbox devolvió
  `EPERM`.
- Reintento `cd web && npm run build` tras `npm ci`: falló con código 127:
  `sh: 1: tsc: not found`.

## Riesgos

- La clasificación sigue siendo determinista, no semántica profunda.
- `deterministic_local` no sustituye un LLM gobernado real.
- El Local Voice Loop del navegador sigue dependiendo de `SpeechRecognition`/`speechSynthesis` del browser.
- El dashboard muestra una muestra local segura; no procesa texto arbitrario desde `/jarvis` porque no se añadió endpoint de mutación.
- El futuro LLM externo debe diseñarse con red, coste, privacidad, audit y no-secret gates explícitos antes de habilitarse.

## Siguiente PR recomendada dentro de Fase 1

PR #160 debería implementar un flujo prepare-only de `typed/voice transcript -> intake -> brain response -> mission preview draft` con auditoría local y sin Hermes dispatch. Debe seguir sin LLM externo por defecto, sin `/execute`, sin mutaciones desde `/jarvis` y con tests de preview/audit/clarification.
