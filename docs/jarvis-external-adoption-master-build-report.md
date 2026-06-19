# JARVIS External Adoption Master Build Report

Fecha: 2026-06-18

## Actualización PR #163 - Phase 1 Voice Runtime Pack

Implementado en esta rama:

- `VoiceRuntimePack` backend/control-plane con GET
  `/mark-3/voice-runtime/status`, integrado en `/mark-3/dashboard/status`,
  `/mark-3/dashboard/events`, `/stream` y Local Doctor.
- Provider contracts seguros:
  `browser_speech_recognition`, `browser_speech_synthesis`,
  `piper_local_disabled_or_missing`, `faster_whisper_disabled_or_missing` y
  `whisper_cpp_disabled_or_missing`.
- Local Voice Loop mejora stop/cancel, interrupt TTS, cola corta
  `speechSynthesis`, filtro de posible eco, estados `cancelled/stopped` y
  fallback honesto cuando STT/TTS del navegador no existe.
- La esfera de particulas sigue state-driven: listening concentrado,
  transcribing reorganizado, thinking turbulento, speaking con picos/ondas,
  error como patron error y stopped/cancelled calmado. No se abre Web Audio ni
  se piden permisos nuevos para visuales.
- Seguridad mantenida: `raw_audio_sent_to_backend=false`,
  `transcript_persistence=false`, `voice_approval_enabled=false`,
  `wake_phrase_can_approve=false`, `wake_phrase_can_execute=false`,
  `hermes_dispatch_allowed=false`.
- Repos revisadas para #163: `OpenVoiceOS/ovos-core` (Apache-2.0),
  `MycroftAI/mycroft-core` (Apache-2.0), `dscripka/openWakeWord` (Apache-2.0),
  `SYSTRAN/faster-whisper` (MIT), `openai/whisper` (MIT),
  `ggml-org/whisper.cpp` (MIT), `OHF-Voice/piper1-gpl` (GPL-3.0),
  `OHF-Voice/wyoming` (MIT), `ethanplusai/jarvis` (personal/no comercial),
  `harsh-raj00/my-jarvis` (MIT) y `chevgan/react-ai-voice-visualizer` (MIT).
- No se copio codigo externo, no se adopto runtime externo, no se instalaron
  dependencias, no se descargaron modelos, no se activo wake always-on, no se
  abrieron proveedores externos y no se cambio el contrato: JARVIS gobierna;
  Hermes ejecuta.
- Documentacion completa: `docs/jarvis-pr-163-voice-runtime-pack.md`.

## Actualización PR #162 - Particle Sphere Motion Polish + Visual QA

Implementado en esta rama:

- `/jarvis` pule el visual central sobre #161: esfera/nube viva de particulas
  Canvas 2D, 2600 particulas precomputadas, distribucion volumetrica,
  profundidad, variacion de tamano/opacidad y aire entre particulas.
- No hay logo, texto grande, nucleo fijo, placa de lectura ni reactor circular
  visible dentro del centro. El centro aparece solo por concentracion temporal
  y se diluye cuando la nube se expande.
- Estados visuales diferenciados: idle suave, listening concentrado,
  transcribing ordenado, thinking turbulento, speaking con pseudo-audio
  determinista y picos/ondas radiales, alert/error mas agresivos y stopped
  reducido/atenuado.
- Visual QA local plegado en `Sistemas` permite forzar Auto, Idle, Listening,
  Transcribing, Thinking, Speaking, Alert y Stopped. Tambien existe query param
  `jarvisVisualPreview`. Es solo visual/frontend: no llama Hermes, no ejecuta,
  no aprueba, no activa mic/camara, no abre Web Audio y no añade backend.
- Repos revisadas para #162: `jincocodev/openclaw-jarvis-ui` (ISC),
  `Suryansh777777/Jarvis-CV` (licencia no visible),
  `zoharbarzilai/Generative-3D-Audio-Visualizer` (licencia no visible),
  `harsh-raj00/my-jarvis` (MIT), `TheStack-ai/jarvis-orb` (MIT),
  `chevgan/react-ai-voice-visualizer` (MIT), `ethanplusai/jarvis`
  (personal/non-commercial visible), `pmndrs/react-three-fiber`/`drei`/
  `react-postprocessing` (MIT).
- No se copio codigo externo, no se adopto runtime externo, no se instalaron
  dependencias, no se abrieron sensores nuevos y se mantiene el contrato:
  JARVIS gobierna; Hermes ejecuta.
- Documentacion completa:
  `docs/jarvis-pr-162-particle-sphere-motion-polish-visual-qa.md`.

## Actualización PR #161 - Presence UI Visual Overhaul v2 + Audio-Reactive Orb

Implementado en esta rama:

- `/jarvis` recibe una correccion fuerte de direccion visual sobre #160:
  fondo mucho mas oscuro, glow general reducido, nucleo azul-blanco
  diferenciado, particulas frias separadas y alert/approval en canal cromatico
  propio.
- `JarvisOrb3D` mantiene WebGL manual sin dependencias nuevas. Añade
  `stateReactiveEnergy`, `coreColor`, `coreGlow`, `outerGlow`, uniform
  `u_reactivity`, respiracion CSS `jarvis-core-breathe` y contratos testeables
  (`data-visual-layering`, `data-voice-reactive-mode`,
  `data-orb-reactive-states`, `jarvis-distinct-core`).
- La reactividad audio/voice es state-driven: idle, wake_listening, listening,
  transcribing, thinking, speaking, approval_required, alert/error y stopped
  cambian energia, particulas, ondas y glow sin Web Audio, sin amplitud real
  nueva, sin auto-start y sin permisos adicionales.
- Laterales, approvals, camara, audio bruto y finance se suavizan como paneles
  premium/minimos. La smart bar sigue siendo centro humano de interaccion con
  respuesta y transcripcion visibles, envio deshabilitado y detalles plegados.
- Repos revisadas para #161: `jincocodev/openclaw-jarvis-ui` (ISC),
  `Suryansh777777/Jarvis-CV` (licencia no visible),
  `zoharbarzilai/Generative-3D-Audio-Visualizer` (licencia no visible),
  `harsh-raj00/my-jarvis` (MIT), `TheStack-ai/jarvis-orb` (MIT),
  `chevgan/react-ai-voice-visualizer` (MIT), `ethanplusai/jarvis`
  (personal/non-commercial visible), `pmndrs/react-three-fiber`/`drei`/
  `react-postprocessing` (MIT).
- No se copio codigo externo, no se adopto runtime externo, no se instalaron
  dependencias, no se abrieron sensores nuevos y se mantiene el contrato:
  JARVIS gobierna; Hermes ejecuta.
- Documentacion completa: `docs/jarvis-pr-161-presence-ui-visual-overhaul-v2-audio-reactive-orb.md`.

## Actualización PR #160 - Presence UI real + 3D Orb/HUD adoption

Implementado en esta rama:

- `/jarvis` deja de priorizar la sensacion de dashboard/admin console y pasa a
  una Presence UI orb-first: nucleo central dominante, header reducido, rails
  minimos, smart bar inferior humana, camara lateral opt-in ampliable y detalles
  tecnicos plegados.
- `JarvisOrb3D` se mantiene en WebGL manual sin dependencias nuevas. Se refuerza
  con estado `approval_required`, anillos/glow extra, fallback visible sin WebGL,
  `motion-reduce`, pixel ratio limitado y budget declarativo de frames y
  particulas.
- Smart bar acepta borrador local de texto y muestra respuesta humana corta,
  sin enviar nada al backend. El debug de `intent_detected`, `risk_level`,
  approval y credenciales queda plegado.
- Camara sigue siendo opt-in: no hay auto-start, no upload, no frames event
  stream, no vision analysis y no permisos nuevos.
- Repos revisadas: `jincocodev/openclaw-jarvis-ui` (ISC),
  `Suryansh777777/Jarvis-CV` (licencia no visible),
  `zoharbarzilai/Generative-3D-Audio-Visualizer` (licencia no visible),
  `harsh-raj00/my-jarvis` (MIT), `TheStack-ai/jarvis-orb` (MIT),
  `chevgan/react-ai-voice-visualizer` (MIT), `ethanplusai/jarvis`
  (personal/non-commercial visible), `pmndrs/react-three-fiber`/`drei`/
  `react-postprocessing` (MIT).
- No se copio codigo externo ni runtimes. Todo lo adoptado fue
  reimplementacion visual/conceptual sobre los componentes existentes.

## Actualización Fase 1 - Base operativa local

Implementado en esta rama:

- Sensor Ledger backend metadata-only para `camera`, `recording`, `wake`,
  `voice_session`, `tts` y `stt`, con eventos `requested`, `started`,
  `stopped`, `cancelled`, `failed`, `deleted` y `retention_updated`.
- Event stream `/mark-3/dashboard/events` y `/stream` fortalecido con
  `schema_version`, `event_id`, `created_at`, `risk_level`, payload seguro y
  heartbeat SSE. Sigue siendo read-only y no transporta secretos, audio bruto,
  frames ni comandos.
- Doctor local ampliado con backend/frontend esperado, stream, Hermes, deps
  opcionales, Python, plataforma, proceso/psutil opcional, puertos esperados y
  capacidades browser-only como `client_side_unknown`, sin activar sensores.
- Policy status visible/read-only: JARVIS gobierna, Hermes ejecuta, frontend
  nunca ejecuta Hermes, wake phrase nunca aprueba, sensores requieren opt-in y
  ejecución peligrosa requiere `ApprovalGateway` + riesgo + auditoría +
  rollback/stop.
- `/jarvis` muestra Sensor Ledger, Doctor Local, Event Stream Health y Policy
  Status dentro del drawer `Sistemas`, sin convertirlo en vista principal.

## Actualización Fase 2 - Orbe 3D real con performance budget

Implementado en esta rama:

- El núcleo visual de `/jarvis` evolucionó a un orbe WebGL manual más
  cinematográfico: partículas orbitando, anillos radiales, marcas holográficas,
  profundidad, glow/bloom simulado, ondas por estado y HUD agresivo.
- Estados visuales soportados: `idle`, `wake_listening`, `listening`,
  `transcribing`, `thinking`, `speaking`, `alert`, `error`, `stopped`,
  `executing`.
- El orbe reacciona a estados existentes: voz local, kill switch, ejecución
  activa declarada por read model, wake runtime declarado por event stream y
  approvals pendientes. No inventa ejecución real ni llama Hermes.
- Performance budget: buffer WebGL estático, throttling por estado,
  `prefers-reduced-motion`, `particleBudget`, `targetFrameMs`, pixel ratio
  limitado y reducción de partículas en idle/power-save.
- Fallback seguro: si WebGL no existe, falla el shader o se pierde el contexto,
  se muestra fallback CSS visible con explicación; no queda canvas blanco.
- No se añadieron dependencias. Se adaptaron patrones visuales de R3F/Drei,
  OpenClaw HUD, Jarvis-CV y visualizadores de audio 3D, pero se mantuvo WebGL
  manual para evitar peso y riesgo de instalación en esta fase.
- No se tocaron cámara real, wake real, STT/TTS local, grabación, remoto ni
  ejecución Hermes.

## Actualización Subfase conversacional + vídeo local opt-in

Implementado en esta rama:

- `buildLocalJarvisResponse` deja de ser eco de transcripción y actúa como
  Conversational Brain Bridge local/determinista: clasifica intención básica,
  responde preguntas simples, prepara previews de misión/tarea/activo, bloquea
  credenciales/secretos y declara cuándo algo requiere approval.
- La smart bar expone `intent_detected`, `risk_level`, `requires_approval`,
  `can_prepare_preview`, `cannot_execute_reason` y `suggested_next_action` en
  detalles plegados. La vista principal mantiene frases humanas cortas.
- No se llama a APIs externas ni se afirma LLM real. El fallback actual es
  local, útil y honesto; la ruta LLM/Hermes gobernada queda futura.
- Se reutiliza el contrato existente de Mission Control / intent-risk preview,
  Policy Status, ApprovalGateway como frontera declarada, Sensor Ledger y Event
  Stream. Frontend sigue sin ejecutar Hermes ni llamar `/execute`.
- Cámara añade grabación de vídeo local opt-in: botón separado `Grabar vídeo`,
  permiso navegador, indicador `REC local`, stop, descarga de blob local y
  borrado con revocación de URL. No hay subida al backend, streaming externo,
  snapshot automático ni análisis de personas/identidad.
- Read model y event stream declaran `browser_local_video_recorder` como
  inactivo por defecto, metadata-only, con `raw_video_sent_to_backend=false`.
  Sensor Ledger declara modalidades seguras `audio_metadata` y
  `video_metadata`; el event stream añade overlay local `sensor_ledger_state`
  para sesiones del navegador sin hacer POST de media al backend.

Cómo probar:

1. Abrir `/jarvis`.
2. Pulsar micrófono y preguntar: `¿Me escuchas?`, `¿Qué puedes hacer ahora?`,
   `Abre una misión para revisar el proyecto`, `Lee mis credenciales`.
3. Verificar que JARVIS responde con ayuda o bloqueo natural, no con eco.
4. Abrir cámara con `Abrir`; luego pulsar `Grabar vídeo`.
5. Verificar indicador `REC local`, `Stop vídeo`, `Descargar vídeo` y
   `Borrar vídeo`.
6. Confirmar que no aparece ninguna ejecución Hermes, approval real, POST de
   media ni `/execute`.

## 1. Resumen ejecutivo

Segunda pasada sobre #157 en la misma rama. Se mantuvo la regla principal:
JARVIS gobierna; Hermes ejecuta. No se creó otro Hermes, no se añadió ejecución
directa desde frontend y no se creó una ruta insegura `/execute`.

Lo que antes quedaba mayormente como contrato se convirtió en implementación
real donde era seguro hacerlo: cámara local opt-in en navegador, grabación local
de audio bruto opt-in, event bus con estados reales del read model, brain visible
read-only y doctor local read-only. Wake real sigue sin activarse; ahora declara
un adapter `openWakeWord` verificable y dependencias detectables, sin micrófono
automático.

El orbe permanece en WebGL manual. Se reintentó instalar Three/R3F/postprocessing,
pero el entorno bloqueó la operación: primero por cache npm global en solo
lectura (`EROFS`) y después por DNS (`EAI_AGAIN registry.npmjs.org`) usando cache
en `/tmp`.

## 2. Implementado por subfase

### Subfase 1 - Contratos convertidos en implementación real

Implementado real:

- Cámara local opt-in con `getUserMedia` solo dentro de
  `useJarvisCameraControl`.
- Grabación local de audio bruto con `MediaRecorder` solo dentro de
  `useJarvisAudioRecorder`.
- Event bus read-only con overlay local de cámara/grabación.
- Brain visible read-only con outcomes, failures, learning proposals y política
  de memoria.
- Doctor local read-only con backend, event stream, Hermes status, browser
  unknown/client-side y dependencias opcionales.

Implementado parcial:

- Auditoría de cámara/grabación existe como metadata local visible en UI y event
  overlay. Auditoría backend completa queda pendiente.
- Hermes se muestra con estado real, sesiones y capacidades gobernadas. La UI no
  ejecuta ni detiene Hermes.

Solo contrato:

- Wake listening real con `openWakeWord`.
- STT/TTS backend local con Whisper/faster-whisper/Piper/Wyoming.
- Memory CRUD/forget/compaction persistente.
- Pairing/revocación remoto y Telegram-Hermes gobernado.

## 3. Arquitectura y UI

- `/jarvis` sigue componentizado:
  `JarvisPresenceShell`, `JarvisOrb3D`, `JarvisSmartBar`, `JarvisSideRail`,
  `JarvisCameraPanel`, `JarvisRecordingPanel`, `JarvisApprovalPanel`,
  `JarvisDebugDrawer`.
- Hooks añadidos o ampliados:
  `useJarvisCameraControl`, `useJarvisAudioRecorder`,
  `useJarvisEventStream`, `useLocalVoiceLoop`.
- El lateral derecho ahora usa scroll interno para evitar solapes con cámara,
  grabación, approvals y resumen.
- El drawer `Sistemas` muestra `Memory Brain` y `Doctor Local`.

## 4. Orbe 3D / HUD

- Se mantiene `JarvisOrb3D` en WebGL manual con partículas, anillos,
  profundidad, glow, estados visuales, fallback sin WebGL y power-save.
- No se migró a R3F por bloqueo de entorno:
  - `npm install three @react-three/fiber @react-three/drei @react-three/postprocessing --package-lock-only --ignore-scripts --fetch-retries=0 --fetch-timeout=15000`
    falló con `EROFS` escribiendo en `/home/diazd/.npm/_cacache`.
  - Reintento con `npm_config_cache=/tmp/jarvis-npm-cache` falló con
    `EAI_AGAIN registry.npmjs.org`.

## 5. Event bus vivo

- `jarvis/dashboard_event_stream.py` ahora emite datos reales del read model:
  Hermes availability/sessions, approvals, mission state, wake adapter,
  camera policy, raw audio recorder, memory brain, doctor, audit timeline.
- `useJarvisEventStream` superpone estados locales de cámara y grabación sin
  audio bruto ni frames.
- Endpoints GET:
  - `/mark-3/dashboard/events`
  - `/mark-3/dashboard/events/stream`
- Garantías:
  read-only, sin secretos, sin audio bruto, sin frames de cámara, sin ejecución.

## 6. Hermes

- Se aprovecha el bridge existente de Hermes mediante estado real:
  `available`, `running_sessions`, `session_count`, tool/action soportados,
  capacidades gobernadas y rutas bloqueadas.
- No se añadió ejecución desde `/jarvis`.
- Las rutas POST existentes de Hermes siguen backend-gated por autorización; la
  UI no las llama.
- Pendiente para activar ejecución candidata desde UI: flujo backend de mission
  candidate + approval_id válido + readback/rollback/stop/audit end-to-end.

## 7. Voz y wake

- `Local Voice Loop` sigue siendo manual y gobernado por navegador:
  SpeechRecognition/speechSynthesis si el browser lo soporta.
- La grabación local de audio bruto está separada de hablar con JARVIS.
- `RealWakeListener.status()` declara:
  provider `openWakeWord`, si la dependencia está instalada, `auto_start=false`,
  `activation_endpoint_enabled=false`, plan de pruebas y no acceso a micrófono en
  tests.
- Wake phrase nunca aprueba, nunca ejecuta y no se activa automáticamente.

## 8. Cámara real opt-in

- Implementado `useJarvisCameraControl`.
- Requisitos cubiertos:
  botón explícito, permiso navegador, preview lateral, indicador visible,
  stop/cancel, `audio:false`, sin streaming externo, sin grabación automática,
  sin snapshot, sin análisis de identidad/personas, cleanup de tracks.
- El event bus refleja estado local como `/jarvis/browser-camera`.
- Auditoría backend completa queda pendiente; la UI muestra metadata local.

## 9. Grabación local de audio bruto

- Implementado `useJarvisAudioRecorder` y `JarvisRecordingPanel`.
- Requisitos cubiertos:
  botón explícito separado de voz, indicador visible, stop, descarga local,
  borrado/revocación de blob URL, sin upload backend, sin STT, sin proveedor.
- Retención:
  blob en memoria del navegador hasta descarga, borrado o cierre de sesión.
- Auditoría backend completa queda pendiente; la UI muestra metadata local.

## 10. Memory brain

- Añadido `memory_brain` al read model:
  entities/preferences/decisions/contradictions visibles, counts de outcomes,
  failures, learning proposals, explicación de por qué JARVIS recuerda algo,
  compaction contract y forget/delete future-gated.
- Usa stores existentes:
  `mark_3_outcome_memory`, `mark_3_learning_proposals`,
  `personal_memory_control`.
- Añadido `GET /personal-memory/status`.
- Memoria nunca concede permisos; memorias sensibles requieren approval.

## 11. Doctor local

- Añadido `build_local_doctor_status` y `GET /mark-3/local-doctor/status`.
- Checks read-only:
  backend, dashboard endpoint, event stream, Hermes status, navegador STT/TTS
  unknown/client-side, cámara unknown/client-side, WebGL unknown/client-side.
- Dependencias opcionales detectadas sin instalar:
  `ffmpeg`, `openwakeword`, `faster_whisper`, `piper`, `sounddevice`, `torch`.
- No lee `.env`, no instala, no activa sensores y no ejecuta Hermes.

## 12. Repos externas: adopción

No se copió código externo. Se adaptaron patrones:

- `jincocodev/openclaw-jarvis-ui`: HUD/event stream/presence.
- `TheStack-ai/jarvis-orb`: brain visible y orb conectado a eventos.
- `Suryansh777777/Jarvis-CV`: panel de cámara/visión, sin MediaPipe ni análisis.
- `zoharbarzilai/Generative-3D-Audio-Visualizer`: esfera reactiva y profundidad.
- `ethanplusai/jarvis`: voz first/manual y personalidad calmada.
- `harsh-raj00/my-jarvis`: event-driven UI sin plugin execution.
- `OpenVoiceOS/ovos-core` / `MycroftAI/mycroft-core`: separación wake/STT/TTS/session.
- `dscripka/openWakeWord`: adapter contract, no wake runtime activo.
- `openai/whisper` / `SYSTRAN/faster-whisper` / `rhasspy/piper`: doctor detecta
  dependencias futuras, sin instalarlas.

## 13. Dependencias añadidas

No se añadieron dependencias.

Dependencias 3D intentadas pero bloqueadas:

- `three`
- `@react-three/fiber`
- `@react-three/drei`
- `@react-three/postprocessing`

## 14. Archivos modificados principales

- `jarvis/api/app.py`
- `jarvis/dashboard_read_model.py`
- `jarvis/dashboard_event_stream.py`
- `jarvis/real_wake_listener.py`
- `web/src/pages/JarvisCommandCenterPage.tsx`
- `web/src/components/jarvis/*`
- `web/src/hooks/jarvis/*`
- `web/src/lib/api.ts`
- `tests/jarvis/test_jarvis_dashboard_event_stream.py`
- `tests/jarvis/test_jarvis_dashboard_status_read_model.py`
- `tests/jarvis/test_jarvis_local_dashboard_shell.py`
- `tests/jarvis/test_mark_2_local_daemon_real_wake_desktop_runtime_voice_approval.py`

## 15. Pendiente para fase siguiente

- Auditoría backend persistente para cámara/grabación local.
- Wake daemon real opt-in con `openWakeWord`, indicador, stop y pruebas de
  falsas activaciones.
- STT/TTS local backend con Piper/faster-whisper y Voice Session Manager formal.
- Memory CRUD/forget/compaction persistente y explicación por record real.
- Activación UI de ejecución candidata Hermes solo si existe flujo completo
  mission/approval/readback/rollback/stop/audit.
- Pairing/revocación remoto y Telegram-Hermes como canal gobernado.
- Verificación visual con browser/dev server cuando el entorno permita listen.

## 16. Validaciones ejecutadas

Ejecutadas:

- `python -m py_compile $(find jarvis -name '*.py')`
- `python -m py_compile tests/jarvis/test_jarvis_dashboard_status_read_model.py tests/jarvis/test_jarvis_dashboard_event_stream.py tests/jarvis/test_jarvis_local_dashboard_shell.py tests/jarvis/test_mark_2_local_daemon_real_wake_desktop_runtime_voice_approval.py`
- `git diff --check`
- `cd web && npm run build`

Bloqueadas:

- `python -m pytest ...`: `/home/diazd/miniconda3/bin/python: No module named pytest`.
- `python -m pytest tests/jarvis -q -x --durations=20`: mismo bloqueo, `No module named pytest`.
- Smoke directo de `jarvis.api.app`: bloqueado por `ModuleNotFoundError: No module named 'fastapi'`.
- `source venv/bin/activate`: no aplica; `venv/` no existe en este worktree.
- Instalación R3F: `EROFS` en cache npm global y luego `EAI_AGAIN` contra registry.

## 17. Cómo probarlo

1. En entorno con dependencias Python instaladas, arrancar backend JARVIS.
2. En `web/`, ejecutar `npm ci` en entorno normal; si el sandbox bloquea
   postinstall de `esbuild`, usar dependencias ya instaladas o repetir
   `npm ci --ignore-scripts` solo para validación local.
3. Ejecutar `npm run build`.
4. Abrir `/jarvis`.
5. Verificar:
   - orbe WebGL con partículas/anillos;
   - event bus `stream`, `snapshot` o `local`;
   - botón de voz manual y stop/cancel;
   - cámara local: pulsar `Abrir`, conceder permiso, ver indicador y pulsar
     `Stop`;
   - audio bruto local: pulsar `Grabar`, `Stop`, descargar y borrar;
   - drawer `Sistemas` con `Memory Brain` y `Doctor Local`;
   - approvals visibles pero sin botones funcionales;
   - ausencia de ejecución Hermes desde frontend.
6. Revisar endpoints:
   - `GET /mark-3/dashboard/status`
   - `GET /mark-3/dashboard/events`
   - `GET /mark-3/dashboard/events/stream`
   - `GET /mark-3/local-doctor/status`
   - `GET /personal-memory/status`

## 18. Riesgos

- Cámara y grabadora dependen del navegador y permisos del usuario.
- Auditoría de sensores en esta pasada es metadata local visible; no ledger
  backend persistente todavía.
- SpeechRecognition puede depender de servicios internos del navegador.
- Wake real no está implementado; solo adapter contract.
- Sin pytest/fastapi local no se pudieron ejecutar tests backend reales.
- El orbe WebGL manual es mantenible para esta fase, pero R3F/postprocessing
  sería preferible si el registry funciona.

## 19. Seguridad revisada

- No se añadió `/execute` inseguro.
- No se añadió Hermes directo desde frontend.
- No se añadieron POST/PUT/DELETE nuevos para `/jarvis`.
- Cámara no se activa al cargar.
- Micrófono de voz no se activa al cargar.
- Grabación local no se activa al cargar.
- Wake phrase nunca aprueba ni ejecuta.
- Audio bruto no se envía al backend.
- Frames de cámara no se envían al backend.
- No se tocaron `.env`, credenciales ni secretos.
- Event bus no incluye secretos, audio bruto ni frames.

## 20. Siguiente fase recomendada

1. Reparar entorno Python (`venv`/`fastapi`/`pytest`) y ejecutar
   `pytest tests/jarvis -q -x --durations=20`.
2. Añadir sensor ledger backend para cámara/grabación/wake con retención y
   borrado auditado.
3. Implementar Voice Session Manager backend y wake opt-in real con
   `openWakeWord`.
4. Instalar Three/R3F/postprocessing en entorno con registry funcional o decidir
   formalmente mantener WebGL manual.
5. Preparar ejecución Hermes candidata desde UI solo cuando el flujo de approval
   completo esté probado end-to-end.
## PR #158 — Conversational Brain + Voice Session/Wake Architecture

PR #158 construye una base segura para conversación y voz sin activar sensores
always-on ni ejecución:

- `ConversationalBrainBridge` v2 local/determinista:
  - no LLM real si no se llama a un LLM;
  - no red ni APIs externas;
  - no memoria automática;
  - no Hermes dispatch;
  - bloqueo de secretos/credenciales/`.env`;
  - respuesta humana breve con detalles técnicos separados.
- `VoiceSessionControl.status()` formaliza el control-plane de voz:
  - estados mínimos completos;
  - wake listening separado de active conversation;
  - push-to-talk, STT, TTS, raw recording, voice approval y Hermes execution
    como capacidades distintas;
  - `raw_audio_sent_to_backend=false`,
    `transcript_persistence=false`, `background_transcription=false`,
    `always_on_stt=false`, `microphone_auto_start=false`.
- Wake Architecture:
  - provider contract `openWakeWord`;
  - dependency detection honesta;
  - `auto_start=false`;
  - `activation_endpoint_enabled=false`;
  - frases `Hola Jarvis` y `Jarvis`;
  - stop phrases `para`, `cancela`, `detente`, `silencio`,
    `cancelar misión`, `apaga escucha`;
  - buffer efímero en memoria, sin persistencia de audio, sin transcripción
    hasta activación válida, sin approval y sin execution.
- Dashboard/event stream:
  - `/mark-3/dashboard/status` incluye `conversational_brain`,
    `voice_session`, `wake_architecture`;
  - `/mark-3/dashboard/events` y `/stream` incluyen `brain_state` y
    `voice_session_state` metadata-only.
- `/jarvis`:
  - muestra respuesta humana corta;
  - diferencia wake disponible/deshabilitado de conversación activa;
  - mantiene detalles técnicos plegados;
  - no añade POST/PUT/DELETE, `/execute`, Hermes directo, approvals reales ni
    `getUserMedia` automático.

Documento de cierre: `docs/jarvis-pr-158-conversational-brain-voice-session-wake-architecture.md`.

## PR #164 — External Adoption Notes: Persistent Audit + Memory Brain v2

Repos revisadas para esta PR:

| Repo | Licencia visible | Decision |
|---|---|---|
| `TheStack-ai/jarvis-orb` | MIT | Reimplementar patrones de memoria local, contradicciones, entidades y visibilidad. No copiar MCP/orb/runtime. |
| `getzep/graphiti` | Apache-2.0 | Tomar solo patron conceptual de temporal/provenance memory. No adoptar Neo4j/graph runtime. |
| `mem0ai/mem0` | Apache-2.0 | Tomar patron conceptual de lifecycle de memoria. No copiar algoritmo ni dependencia. |
| `chroma-core/chroma` | Apache-2.0 | No adoptar vector DB obligatoria en Fase 1. |
| `codenotary/immudb` | Business Source License 1.1; Change License Apache 2.0 | Reimplementar hash-chain local simple; no servidor ni libreria. |
| `sigstore/rekor` | Apache-2.0 | Reimplementar idea metadata transparency log local; no servidor externo. |
| `google/trillian` | Apache-2.0 | No adoptar infraestructura distribuida; solo referencia de log verificable. |
| `Yelp/detect-secrets` | Apache-2.0 | Reimplementar marcadores locales de redaccion; no scanner externo. |
| `trufflesecurity/trufflehog` | AGPL-3.0 | No copiar ni instalar; solo referencia conceptual de clases de credenciales. |
| `semgrep/semgrep` | LGPL-2.1 | No integrar runtime/ruleset; solo referencia conceptual de reglas. |

Resultado:

- Se prefirio SQLite local primero.
- No se agregaron dependencias nuevas.
- No se metio graph DB, vector DB, cloud memory ni servidor externo.
- Codigo copiado/adaptado desde repos externas: ninguno.
- Patrones reimplementados: hash-chain, lifecycle de memoria explicable,
  superseding/contradiction, redaccion basica metadata-only.

Documento: `docs/jarvis-pr-164-persistent-audit-memory-brain-v2.md`.
