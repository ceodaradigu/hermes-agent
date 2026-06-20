# PR #176 - Phase 10 Hands-Free Runtime + Persona + API Brain Router

## Objetivo

Phase 10 hace que JARVIS empiece a comportarse como operador personal manos
libres sin crear otro Hermes ni abrir una ruta peligrosa de ejecución.

El contrato sigue intacto:

- JARVIS gobierna, clasifica riesgo, pide aprobación, audita y controla.
- Hermes ejecuta solo detrás de rutas gobernadas existentes.
- El frontend nunca ejecuta Hermes directamente.
- No hay `/execute`, shell genérico, fake execution ni aprobación por wake
  phrase.

## Implementado

- Nuevo control plane:
  `jarvis/phase_10_hands_free_runtime_persona_api_router.py`.
- Nuevos endpoints:
  - `GET /mark-3/phase-10/status`
  - `POST /mark-3/phase-10/wake/preview`
  - `POST /mark-3/phase-10/voice-ui/intent`
  - `GET/POST /mark-3/phase-10/app-launcher/*`
  - `GET/POST /mark-3/phase-10/browser-intent/*`
  - `GET/POST /mark-3/phase-10/approval/*`
  - `GET/POST /mark-3/phase-10/persona/*`
  - `GET /mark-3/phase-10/voice-providers/status`
  - `GET/POST /mark-3/model-router/*`
- Dashboard read model expone `phase_10_status`, `persona`, `model_router`,
  `voice_ui_intent_router`, `app_launcher`, `browser_intents`,
  `phase_10_approval_v2` y `phase_10_voice_provider_architecture`.
- Event stream añade `phase_10_state`, `persona_state`, `model_router_state`,
  `voice_ui_intent_state`, `app_launcher_state` y `browser_intent_state`.
- `/mark-3/conversation/turn` preserva el flujo seguro de PR #175 y añade
  metadata Phase 10/persona. Activar UTRON desde texto/voz cambia estado
  visible, no permisos.
- `/jarvis` enruta transcripciones de voz primero por el router de comandos de
  UI. Si no es control local, cae al turno conversacional existente.

## Real Ahora

- Wake/stop recognition como contrato determinista de transcript:
  `Hola JARVIS`, `JARVIS`, `para`, `JARVIS para`, `cállate`,
  `JARVIS cállate`.
- Conversación de voz browser: cuando `SpeechRecognition` funciona y David abre
  sesión con el micrófono, JARVIS vuelve a escuchar después de responder hasta
  stop/cancel/timeout.
- Historial escrito de conversación y respuesta completa se preservan.
- TTS browser con `speechSynthesis`, `voz on/off`, `repetir` y `detener voz`.
- Comandos de UI por voz:
  abrir/cerrar panel, activar/desactivar voz, repetir, detener voz, revisar
  estado, cancelar, activar/desactivar UTRON.
- Cámara, grabación de audio y grabación de vídeo se preparan como acción
  sensible y requieren frase exacta antes de pedir permiso al navegador.
- UTRON cambia nombre visible a UTRON, tema/orbe rojo y preferencia de voz
  más profunda/autoritativa cuando el navegador/proveedor lo permita.
- Model/API Router v1 decide local vs OpenRouter sin hacer llamadas externas.
- Budget guard por defecto: 30 EUR/mes.

## Readiness / Fallback

- Wake always-on de sistema: readiness only. No hay escucha oculta, servicio de
  sistema ni raw audio persistente.
- Si `/jarvis` no está abierto, abrir Chrome queda como contrato de local
  controller/Hermes gobernado. El frontend no abre procesos ni shell.
- App launcher prepara intents conocidos/unknown, riesgo, approval y audit
  metadata. No finge que abrió una app.
- Browser/navigation prepara intents para buscar, abrir URL, resumir página,
  preparar formulario/mensaje o navegar servicio. No navega ni envía formularios
  sin adaptador gobernado.
- Form filling es preview-first; submit, compras, pagos y publicación requieren
  aprobación fuerte.
- Login requiere acción manual de David o futura bóveda aprobada. No se guardan
  passwords en claro.
- Local TTS y premium API voice son readiness/config status. No se usa voz de
  pago por defecto.
- OpenRouter se marca ready solo si hay key configurada, pero tests/status no
  llaman a la red ni exponen secretos.

## Aprobación v2

Para acciones risky/dangerous JARVIS debe leer:

- qué hará;
- coste;
- qué puede tocar/cambiar/publicar/enviar;
- riesgo;
- plan de parada/rollback;
- frase exacta.

Frase exacta:

```text
confirmo y autorizo
```

Reglas:

- Variantes naturales valen para comandos UI low-risk.
- Dangerous/high/critical requieren frase exacta.
- Voice approval requiere sesión activa/confiable cuando aplica.
- Wake phrase nunca aprueba.
- UTRON no bypass approvals.
- Replay de frase para otra acción se rechaza por fingerprint/contexto.

## Persona

JARVIS:

- Español por defecto.
- Cercano, elegante, calmado, inteligente, premium.
- Menos técnico salvo petición explícita.
- Admite limitaciones honestamente.

UTRON:

- Activación: `JARVIS, activa modo UTRON`.
- Desactivación: `desactiva UTRON`.
- Nombre visible UTRON, tema rojo, preferencia de voz más profunda.
- Tono más sarcástico/autoritario con humor oscuro.
- Sigue siendo útil y obediente a David.
- No insulta gravemente a David, no manipula, no oculta riesgo, no salta
  approvals, no clona voces/diálogos de películas.

## Model/API Router

Provider registry:

- `local`: coste 0, preferido para simple chat, summarization y voice response
  cuando calidad sea suficiente.
- `openrouter`: prioridad para planning, code, browser research y risky
  operation reasoning si está configurado y dentro de presupuesto.
- `openai_future` / `anthropic_future`: contratos futuros, disabled.

Decision object:

- selected provider/model;
- why;
- quality tier;
- estimated cost;
- budget remaining;
- requires approval;
- fallback provider.

No secrets:

- keys se muestran como redacted/configured boolean.
- no API calls en tests.
- no paid usage sin key/config y aprobación.

## Seguridad

- No hidden recording.
- No raw audio storage by default.
- No always-on transcription.
- No frontend direct Hermes execution.
- No arbitrary command/shell from UI.
- No app/browser fake completion.
- Memory never grants permission or downgrades risk.
- Illegal, unsafe, unauthorized, impossible or unsupported requests are denied
  or marked unsupported.

## Validación Manual

1. Abrir backend en `127.0.0.1:8000` y `/jarvis`.
2. Escribir `JARVIS, activa modo UTRON`.
3. Confirmar header/orbe rojo y nombre visible `UTRON`.
4. Escribir `desactiva UTRON` y confirmar retorno a JARVIS/cyan.
5. Pulsar micrófono en navegador compatible y decir `revisa el estado`.
6. Confirmar respuesta en historial y que la escucha vuelve tras hablar.
7. Decir `repite` y confirmar que repite la última respuesta.
8. Decir `cállate` o `para` y confirmar que TTS/escucha se detienen.
9. Decir `abre la cámara`.
10. Confirmar que JARVIS pide `confirmo y autorizo` y no pide permiso aún.
11. Decir otra frase cualquiera y confirmar rechazo.
12. Decir `confirmo y autorizo` y confirmar que solo entonces pide permiso de
    cámara del navegador.
13. Probar `graba audio` con la misma confirmación exacta.
14. Consultar `/mark-3/phase-10/status` y `/mark-3/model-router/status`.
15. Confirmar `frontend_direct_hermes_allowed=false`,
    `wake_phrase_can_approve=false`, presupuesto 30 EUR y secrets redacted.

## Tests

Focused tests:

```bash
PYTHONPATH=. python -m pytest tests/jarvis/test_pr_176_phase_10_hands_free_runtime_persona_api_router.py -q
```

Compatibility recommended:

```bash
PYTHONPATH=. python -m pytest tests/jarvis/test_pr_175_conversational_ux_send_button.py -q
PYTHONPATH=. python -m pytest tests/jarvis/test_pr_170_phase_5_identity_store.py tests/jarvis/test_pr_171_phase_6_real_voice_wake_memory_sensor_runtime.py tests/jarvis/test_pr_172_phase_7_governed_actions.py tests/jarvis/test_pr_173_phase_8_governed_remote_external_ops.py tests/jarvis/test_pr_174_phase_9_product_operator.py -q
PYTHONPATH=. python -m pytest tests/jarvis -q
npm --prefix web run build
git diff --check
```

In the PR #176 worktree used for this report, `venv/bin/activate` and
`web/node_modules` were absent, so Python checks used system Python and web
build requires dependencies to be installed before it can run.
