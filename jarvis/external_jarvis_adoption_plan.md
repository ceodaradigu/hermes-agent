# External JARVIS Adoption Plan

Auditoria para `ceodaradigu/hermes-agent`, rama `pr-156-local-voice-loop`.

Regla arquitectonica permanente:

- JARVIS gobierna, decide, clasifica riesgo, pide aprobacion, audita y controla.
- Hermes ejecuta.
- No se debe construir otro Hermes.
- No se debe duplicar runtime de ejecucion sin sentido.
- Las restricciones son gates de aprobacion, no prohibiciones permanentes.
- Wake phrase nunca aprueba.
- La voz puede aprobar solo si esta autenticada, gateada y auditada.

Nota: este documento es un plan de investigacion y adopcion. No implica que las
capacidades aqui descritas ya existan ni que hayan sido implementadas.

## 1. Resumen ejecutivo

### Estado real de nuestro JARVIS hoy

- `/jarvis` existe como Presence UI local.
- Hay contrato explicito: JARVIS gobierna; Hermes ejecuta.
- Hay dashboard/read model en `GET /mark-3/dashboard/status`.
- Hay modulos preview/read-only para approvals, Hermes Execution, Mission
  Control, Voice/Wake, Vision/Mobile, Finance/Product, Pilot/Audit.
- En esta rama hay Local Voice Loop en progreso:
  - `SpeechRecognition` / `webkitSpeechRecognition` en navegador.
  - `speechSynthesis` en navegador.
  - conversacion manual continua en el worktree actual.
  - smart bar con transcripcion/respuesta temporal.
  - estados `idle`, `listening`, `transcribing`, `thinking`, `speaking`,
    `error/not_supported/unavailable`.
  - contrato `wake_listening` futuro sin activarlo.
  - `recording=false`, `raw_audio_sent_to_backend=false`,
    `approval_by_voice_enabled=false`, `wake_phrase_approval=false`.
- Hay un nucleo visual cinematografico CSS/React mejorado, pero todavia no es
  un sistema 3D real con pipeline de audio, postprocessing y WebGL avanzado.
- Hay runtime local y multiples piezas de JARVIS/Hermes ya existentes en
  backend: voice runtime, wake listener, voice storage, approval gateway, Hermes
  bridge, mission loop, personal memory, mobile companion, camera control.
- Muchas piezas siguen siendo preview, read-only, contract-first o
  control-plane, no operativas completas.

### Que esta bien

- La arquitectura base es superior a muchas repos externas: nuestro JARVIS ya
  separa gobierno, approvals, auditoria y ejecucion. Varias repos JARVIS
  externas mezclan UI, voz, LLM y ejecucion directa.
- Tenemos una regla clara: JARVIS gobierna; Hermes ejecuta.
- Hay tests de seguridad que bloquean `/execute`, POST/PUT/DELETE peligrosos,
  Hermes directo desde frontend, grabacion cruda y sensores no controlados.
- Hay una vision de producto completa: local daemon, movil, VPS, camara, voz,
  memoria, approvals, finance/product, Hermes bridge.
- El Local Voice Loop actual es honesto: si el navegador no soporta STT/TTS, no
  finge exito.

### Que esta mediocre

- El nucleo visual todavia no compite con repos Three.js/R3F especializadas como
  `openclaw-jarvis-ui`, `Jarvis-CV`, `my-jarvis` o visualizadores
  audio-reactivos.
- La voz depende del navegador y suena limitada. No hay voz premium local/API
  integrada todavia.
- No hay wake listening real seguro.
- No hay WebSocket/SSE vivo desde `/jarvis` hacia eventos de JARVIS/Hermes.
- La camara/vision sigue como placeholder/control-plane.
- La memoria existe en varias capas, pero falta una experiencia unificada tipo
  brain visible con contradiccion, entidad, decision, recencia y compactacion.
- Falta empaquetado local serio: tray/system daemon, doctor, dependency checks,
  service install, health panel real.
- El frontend aun puede sentirse dashboard en partes secundarias; la direccion
  correcta es Presence-first, detalles plegados.

### Que falta para hacerlo extremo

- Orb 3D real con React Three Fiber, Drei, postprocessing, shaders, bloom,
  particulas y performance budget.
- Event bus local: estado de escucha, TTS, Hermes, approvals, memoria, wake,
  camara y ejecucion en tiempo real.
- Wake listening local con deteccion minima, sin grabar ni transcribir todo.
- STT local opcional: `faster-whisper`/Whisper o stack Wyoming.
- TTS premium: local Piper/Coqui/Kitten/OpenVoice-compatible o API futura, sin
  clonar voz protegida.
- Persona engine: tono, brevedad, cortesia, humor seco opcional, niveles de
  urgencia, readback.
- Memoria operacional: entidad/decision/preferencia con verificacion,
  contradiccion, caducidad, compactacion y approval para memorias sensibles.
- Camara opt-in con indicador fuerte, stop, scope, redaction, no face/person
  analysis por defecto.
- Grabacion local explicita: opt-in, indicador, retencion, borrado, audit log.
- Mobile/VPS/Telegram como canales gobernados, no runtimes libres.
- Approval por voz solo con canal autenticado, challenge, readback, audit y
  fallback no-voz.

### Repos externas mas utiles

Prioridad alta:

- `jincocodev/openclaw-jarvis-ui`: HUD, orb Three.js, chat, monitor, TTS,
  SSE/WebSocket, mobile.
- `TheStack-ai/jarvis-orb`: memoria visible, MCP brain, orb desktop, eventos de
  pensamiento.
- `Suryansh777777/Jarvis-CV`: camara, MediaPipe, gestos, R3F/Drei, 60fps.
- `ethanplusai/jarvis`: asistente voice-first macOS, personalidad, memoria,
  AppleScript, WebSocket, orb audio-reactivo.
- `OpenVoiceOS/ovos-core` y `dscripka/openWakeWord`: arquitectura voice
  assistant y wake word local.

Prioridad media:

- `chevgan/react-ai-voice-visualizer`: componentes de voz, transcripcion
  animada, VAD, canvas 60fps.
- `zoharbarzilai/Generative-3D-Audio-Visualizer`: esfera audio-reactiva,
  starfield, bloom, Web Audio.
- `harsh-raj00/my-jarvis`: FastAPI/WebSocket, plugins, 8K particles,
  logging/rate limits, pero con menos governance.
- `SYSTRAN/faster-whisper`, `openai/whisper`, `rhasspy/piper`,
  `OHF-Voice/wyoming`: piezas de voz local.

## 2. Repos investigadas

### 2.1 `jincocodev/openclaw-jarvis-ui`

- URL: https://github.com/jincocodev/openclaw-jarvis-ui
- Stack: JavaScript, CSS, HTML, Vite, Three.js, Express server, WebSocket
  relay, SSE, Edge TTS, macOS `say`.
- Que hace:
  - HUD estilo JARVIS para OpenClaw.
  - Orb Three.js interactivo con estados `IDLE`, `THINKING`, `RESPONDING`.
  - Chat en streaming via OpenClaw Gateway WebSocket.
  - System monitor via SSE.
  - Audio visualizer con spectrum, ring y waveform.
  - Task manager CRUD.
  - Memory timeline desde `memory/*.md`.
  - Schedule/cron view.
  - Skills browser.
  - TTS Edge/macOS.
  - Temas y power save mode.
  - Mobile/PWA.
- Piezas utiles:
  - Estructura visual de HUD real.
  - Separacion `core/` escena/audio/particulas y `components/`.
  - WebSocket relay + SSE para estado vivo.
  - Power save mode 60fps/15fps.
  - Memory timeline plegable.
  - Skills browser como referencia para nuestro catalogo de capabilities.
  - TTS server-side con Edge TTS o `say`.
- Piezas que no sirven tal cual:
  - Integra OpenClaw Gateway, no nuestro Hermes/JARVIS read model.
  - Task CRUD desde UI chocaria con nuestro modelo de approvals si se copia
    directo.
  - Remote insecure auth no debe replicarse sin threat model.
  - Edge TTS puede implicar dependencia externa; no encaja con sin API externa
    por ahora salvo fase futura opcional.
- Dificultad de integracion: media.
- Dependencias: Node 20, Express, Three.js, Edge TTS Python, ffmpeg opcional.
- Riesgos:
  - Duplicar gateway/runtime.
  - Anadir mutaciones directas al frontend.
  - Mezclar OpenClaw session model con Hermes.
- Prioridad: alta para visual/event architecture; baja para CRUD.
- Conviene: adaptar patrones visuales y eventos, no copiar runtime.
- Encaja en nuestro JARVIS:
  - `/jarvis` Presence UI.
  - Futura capa `jarvis_event_stream`.
  - TTS provider opcional.
  - Memory timeline visual.

### 2.2 `chevgan/react-ai-voice-visualizer`

- URL: https://github.com/chevgan/react-ai-voice-visualizer
- Stack: React, TypeScript, Canvas, Web Audio API, `simplex-noise`.
- Que hace:
  - UI kit de componentes para interfaces de voz IA.
  - `VoiceOrb`, `VoiceWave`, `VoiceParticles`, `VoiceRing`, `VoiceNeural`.
  - Estados `idle`, `listening`, `thinking`, `speaking`.
  - Hooks de microfono, analisis de audio y VAD.
  - `TranscriptionText` con cursor, typing animation y word confidence.
  - `SpeechConfidenceBar`.
  - 60fps canvas.
- Piezas utiles:
  - State model visual de voz.
  - Transcripcion animada para smart bar.
  - VAD/confidence UI.
  - Ideas de movimiento para `listening/thinking/speaking`.
- Piezas que no sirven tal cual:
  - Hooks de microfono usan captura de audio; en nuestro contrato actual no se
    puede introducir sin PR especifica.
  - No resuelve STT/TTS, approvals ni runtime.
  - Es Canvas 2D/2.5D, no necesariamente nucleo 3D final.
- Dificultad de integracion: baja/media.
- Dependencias: paquete npm, `simplex-noise`.
- Riesgos:
  - `useMicrophoneStream` implicaria `getUserMedia`; ahora esta prohibido en
    `/jarvis`.
  - Puede chocar con nuestro contrato no raw audio capture si se integra sin
    gating.
- Prioridad: media-alta para voice UI; baja para mic hooks ahora.
- Conviene: adaptar componentes visuales o ideas, no activar mic hooks todavia.
- Encaja:
  - Smart bar.
  - Mini visualizers.
  - Futura fase audio-reactive con opt-in.

### 2.3 `TheStack-ai/jarvis-orb`

- URL: https://github.com/TheStack-ai/jarvis-orb
- Stack: Python, aiosqlite, FTS5, MCP stdio, WebSocket, Tauri, Three.js, WebGL.
- Que hace:
  - Persistent memory MCP server + desktop orb.
  - 4-tier memory: episodic, semantic, project, procedural.
  - Temporal scoring.
  - Contradiction detection.
  - Entity tracking.
  - Relationship storage.
  - FTS5 search.
  - Orb always-on-top, draggable, responds to brain events.
- Piezas utiles:
  - Modelo mental orb no decorativo: evento del brain cambia visual.
  - Memory/entity schema.
  - Contradiction/superseded/verified state.
  - WebSocket para orb desktop.
  - Desktop app lightweight.
  - MCP-like memory tools, pero debemos mapearlo a JARVIS governance.
- Piezas que no sirven tal cual:
  - Esta orientado a Claude Code/Cursor MCP, no a Hermes.
  - Crear otro brain completo duplicaria parte de JARVIS si se copia.
  - Tauri app aparte puede fragmentar si `/jarvis` sigue siendo interfaz
    principal.
- Dificultad de integracion: media-alta.
- Dependencias: Python, aiosqlite, websockets, MCP, Tauri/Rust, Three.js.
- Riesgos:
  - Duplicar memoria.
  - Duplicar entidad/control-plane.
  - Introducir MCP sidecar sin gates.
- Prioridad: alta para memoria visible y orb-event semantics.
- Conviene: adaptar modelo de memoria/eventos; no copiar brain como runtime
  paralelo.
- Encaja:
  - `jarvis/personal_memory.py`
  - `jarvis/mark_3_outcome_memory.py`
  - `jarvis/mark_3_learning_proposals.py`
  - `/jarvis` nucleo visual y timeline.

### 2.4 `cam-hm/jarvis`

- URL: https://github.com/cam-hm/jarvis
- Stack: FastAPI, WebSockets, Gemini API, Piper TTS, custom JARVIS Hugging Face
  model, Web Speech API, Vanilla JS, Three.js, Docker.
- Que hace:
  - Asistente voice-activated con Arc Reactor HUD.
  - Voz input/output.
  - Gemini brain.
  - Piper TTS con modelo JARVIS.
  - Sentence-level WebSocket audio streaming.
  - Arc Reactor audio-reactive.
- Piezas utiles:
  - FastAPI/WebSocket streaming para habla incremental.
  - Piper local como via de TTS local.
  - HUD Arc Reactor como referencia estetica.
  - Docker packaging.
- Piezas que no sirven tal cual:
  - Gemini API externa no aplica ahora.
  - Modelo `jarvis voice` puede tener riesgo legal/etico si clona voz exacta.
  - Arquitectura de assistant directo no tiene approvals/Hermes gates.
- Dificultad de integracion: media.
- Dependencias: FastAPI, WebSockets, Piper, Gemini API, Docker.
- Riesgos:
  - Voz estilo pelicula mal gestionada.
  - API externa.
  - Ejecucion directa si se copia assistant logic.
- Prioridad: media-alta para streaming/TTS local; media para HUD.
- Conviene: referencia para streaming + Piper, no copiar persona/LLM flow.
- Encaja:
  - Futura `jarvis_voice_tts_provider`.
  - Futura `voice_streaming_status`.
  - `/jarvis` reactor.

### 2.5 `Suryansh777777/Jarvis-CV`

- URL: https://github.com/Suryansh777777/Jarvis-CV
- Stack: React 18, TypeScript, Vite, Three.js, React Three Fiber, Drei,
  MediaPipe, Web Audio API, Zustand, Tailwind, shadcn/ui.
- Que hace:
  - Futuristic browser HUD con camara/vision.
  - Face detection.
  - Pose tracking.
  - Hand gesture recognition.
  - Audio visualizer.
  - AR overlays.
  - 3D animated UI.
  - Performance 60fps, lazy loading, code splitting.
- Piezas utiles:
  - Stack frontend moderno que encaja: React + Vite + TS + Tailwind.
  - R3F/Drei para nuestro nucleo 3D.
  - MediaPipe como opcion camara/gestos local browser.
  - Performance budget y modularizacion.
  - Gesture/face/pose como future opt-in.
- Piezas que no sirven tal cual:
  - Usa camara real; nuestra PR actual no puede activarla.
  - Face recognition/detection debe tener policy estricta.
  - Gestos no deben ejecutar comandos sin approval.
- Dificultad de integracion: media.
- Dependencias: `three`, `@react-three/fiber`, `@react-three/drei`,
  `@mediapipe/*`, Zustand.
- Riesgos:
  - Sensores.
  - Privacidad biometrica.
  - Rendimiento en maquinas modestas.
- Prioridad: alta para vision/orb stack; camara real en fase separada.
- Conviene: adaptar stack y performance patterns; no copiar camara activa en
  #156.
- Encaja:
  - Fase Orbe 3D.
  - Fase Camara/Vision opt-in.
  - Fase gesture preview, no execute.

### 2.6 `zoharbarzilai/Generative-3D-Audio-Visualizer`

- URL: https://github.com/zoharbarzilai/Generative-3D-Audio-Visualizer
- Stack: React, Vite, Three.js, React Three Fiber, Drei, Postprocessing, Web
  Audio API, Tailwind.
- Que hace:
  - Esfera audio-reactiva 3D.
  - Starfield.
  - Bloom.
  - OrbitControls.
  - AnalyserNode.
  - Microphone input.
- Piezas utiles:
  - Bloom y profundidad visual.
  - Esfera audio-reactiva.
  - Starfield/particulas.
  - R3F + postprocessing stack.
- Piezas que no sirven tal cual:
  - Usa microfono/Web Audio directamente.
  - Es visualizer, no assistant.
  - No tiene approvals, STT, TTS, memory.
- Dificultad de integracion: baja/media para visual; alta si se quiere audio
  real cumpliendo contrato.
- Dependencias: `three`, `@react-three/fiber`, `@react-three/drei`,
  `@react-three/postprocessing`.
- Riesgos:
  - `getUserMedia`/Web Audio prohibido hasta PR opt-in.
  - Performance.
- Prioridad: alta para nucleo 3D; baja para audio capture ahora.
- Conviene: adaptar visual/rendering; no activar mic input.
- Encaja:
  - Fase Orbe 3D.
  - Fase audio-reactive a partir de TTS state o synthetic amplitude, antes de raw
    mic.

### 2.7 `ethanplusai/jarvis`

- URL: https://github.com/ethanplusai/jarvis
- Stack: Next.js, React, Tailwind, Framer Motion, FastAPI, WebSockets, OpenAI,
  Whisper, ElevenLabs, LangGraph, ChromaDB, AppleScript, Playwright, macOS.
- Que hace:
  - Personal AI assistant for macOS.
  - Always-listening wake detection.
  - Speech-to-speech.
  - Voice/keyboard control.
  - macOS system control via AppleScript.
  - Browser automation.
  - Memory with ChromaDB.
  - Orb particle animation audio-reactive.
  - WebSocket state.
- Piezas utiles:
  - Persona/UX voice-first.
  - Desktop assistant framing.
  - State machine de voice assistant.
  - Orb audio-reactive.
  - Memory for personal context.
  - WebSocket between backend/frontend.
  - macOS automation as future Hermes-controlled tool surface.
- Piezas que no sirven tal cual:
  - Always-listening actual no encaja sin diseno wake seguro.
  - ElevenLabs/OpenAI no aplica ahora.
  - Direct system control no debe entrar al frontend ni bypass approvals.
  - Mac-only; David parece Windows/WSL tambien.
- Dificultad de integracion: alta si se adopta runtime; media como referencia.
- Dependencias: FastAPI, WebSocket, OpenAI, Whisper, ElevenLabs, LangGraph,
  ChromaDB, AppleScript.
- Riesgos:
  - Coste/API.
  - Privacidad.
  - Direct system automation.
  - Platform lock-in.
- Prioridad: alta como referencia de behavior/persona; media para architecture;
  baja para copy.
- Conviene: referencia, no copiar runtime.
- Encaja:
  - Persona engine.
  - Voice Session Manager.
  - Desktop command candidates routed through Hermes approvals.
  - Memory UX.

### 2.8 `harsh-raj00/my-jarvis`

- URL: https://github.com/harsh-raj00/my-jarvis
- Stack: React/Vite/TypeScript, Three.js, Tailwind, FastAPI, WebSockets,
  Gemini, ElevenLabs, plugins, rate limiting, logging.
- Que hace:
  - Full-stack AI assistant.
  - 8K particle JARVIS orb.
  - Real-time voice pipeline.
  - STT/TTS.
  - WebSocket full duplex.
  - Plugin system.
  - Rate limiting and logs.
  - Camera/voice/game plugin examples.
- Piezas utiles:
  - Orb particle ambition.
  - FastAPI/WebSocket voice pipeline.
  - Plugin/service separation.
  - Logging/rate limit patterns.
- Piezas que no sirven tal cual:
  - Gemini/ElevenLabs API not for now.
  - Plugins pueden ejecutar sin nuestro approval model.
  - No trae Hermes/JARVIS governance.
- Dificultad de integracion: media.
- Dependencias: FastAPI, WebSocket, Gemini, ElevenLabs, Three.js.
- Riesgos:
  - Direct plugin execution.
  - External APIs.
  - Secrets.
- Prioridad: media-alta para WebSocket/orb reference; baja para execution
  plugins.
- Conviene: referencia de full-stack realtime, no copiar action path.
- Encaja:
  - Event bus.
  - Orb.
  - Diagnostics/logging.

### 2.9 `Leon-AI/leon`

- URL: https://github.com/Leon-AI/leon
- Stack: Node.js, Python, web app, STT/TTS/hotword, modules/packages.
- Que hace:
  - Open-source personal assistant.
  - Modular skills/packages.
  - Speech and text input.
  - Offline-first ambition.
  - Web UI.
- Piezas utiles:
  - Assistant skill/package structure.
  - Offline/local-first framing.
  - Wake/hotword/STT/TTS architecture reference.
- Piezas que no sirven tal cual:
  - Es otro assistant runtime completo; copiarlo duplicaria Hermes/JARVIS.
  - Su plugin system no tiene nuestro approval/audit model.
- Dificultad: alta si se integra, baja como referencia.
- Dependencias: Node, Python, STT/TTS providers.
- Riesgos:
  - Duplicacion de runtime.
  - Plugin execution bypass.
- Prioridad: media.
- Conviene: referencia de modular assistant, no adopcion directa.
- Encaja:
  - Inspiration para capability catalog, installation flow, assistant packages.

### 2.10 `OpenVoiceOS/ovos-core`

- URL: https://github.com/OpenVoiceOS/ovos-core
- Stack: Python voice assistant framework, message bus, skills, wake/STT/TTS
  ecosystem.
- Que hace:
  - Nucleo de asistente de voz open source.
  - Skills.
  - Message bus.
  - Configuracion de STT/TTS/wake.
- Piezas utiles:
  - Arquitectura madura de voice assistant.
  - Message bus local.
  - Separacion wake/STT/TTS/skills.
  - Buen modelo para no atar JARVIS a navegador.
- Piezas que no sirven tal cual:
  - Es runtime completo y podria duplicar Hermes.
  - Skills OVOS no pueden ejecutar acciones sin traduccion a nuestro approval
    path.
- Dificultad: alta.
- Dependencias: Python, multiples plugins voice.
- Riesgos:
  - Duplicar runtime.
  - Importar demasiada superficie.
- Prioridad: alta como referencia arquitectonica; baja como dependencia core.
- Conviene: estudiar/adaptar patrones, no meter OVOS entero.
- Encaja:
  - Wake daemon.
  - Voice bus.
  - STT/TTS provider abstraction.

### 2.11 `MycroftAI/mycroft-core`

- URL: https://github.com/MycroftAI/mycroft-core
- Stack: Python voice assistant, message bus, skills, STT/TTS/wake.
- Que hace:
  - Assistant framework historico.
  - Skills y message bus.
  - Voice interaction pipeline.
- Piezas utiles:
  - Patrones probados de assistant lifecycle.
  - Wake/STT/TTS separation.
  - Skill registration.
- Piezas que no sirven:
  - Proyecto historico/legacy.
  - No debemos adoptar core completo.
- Dificultad: alta.
- Dependencias: Python, STT/TTS/wake.
- Riesgos: mantenimiento, duplicacion.
- Prioridad: baja-media.
- Conviene: referencia historica.
- Encaja:
  - Diseno conceptual del voice daemon.

### 2.12 `dscripka/openWakeWord`

- URL: https://github.com/dscripka/openWakeWord
- Stack: Python, ONNX/TFLite-style wake word models.
- Que hace:
  - Wake word detection local.
  - Modelos pre-entrenados.
  - Custom wake word training.
- Piezas utiles:
  - Candidato para `wake_listening`.
  - Puede detectar `Jarvis` sin enviar audio al backend.
  - Encaja con wake listening sin conversacion completa.
- Piezas que no sirven tal cual:
  - No resuelve privacidad completa; hay que disenar buffer, no persistencia,
    audit, indicator.
  - No aprueba ni ejecuta.
- Dificultad: media.
- Dependencias: Python, audio input, model runtime.
- Riesgos:
  - Falsos positivos/negativos.
  - Audio capture local permanente requiere permisos, indicador, stop.
- Prioridad: alta para wake listening futuro.
- Conviene: evaluar en spike aislado.
- Encaja:
  - `jarvis/real_wake_listener.py`
  - `jarvis/wake_voice_runtime.py`
  - service local daemon.

### 2.13 `openai/whisper`

- URL: https://github.com/openai/whisper
- Stack: Python, PyTorch.
- Que hace:
  - STT general-purpose.
  - Modelos multilingues.
- Piezas utiles:
  - STT local/offline opcional.
  - Mejor control que browser SpeechRecognition.
- Piezas que no sirven tal cual:
  - Pesado para low-latency always-on.
  - No wake word.
  - No diarizacion ni VAD completo.
- Dificultad: media.
- Dependencias: Python, PyTorch, ffmpeg, CPU/GPU.
- Riesgos:
  - Latencia y consumo.
  - Instalacion pesada.
- Prioridad: media-alta para STT local post-wake.
- Conviene: proveedor STT opcional, no default de PR #156.
- Encaja:
  - `jarvis/voice/runtime.py`
  - `jarvis/voice/base.py`

### 2.14 `SYSTRAN/faster-whisper`

- URL: https://github.com/SYSTRAN/faster-whisper
- Stack: Python, CTranslate2.
- Que hace:
  - Whisper inference mas eficiente.
  - CPU/GPU optimizado.
- Piezas utiles:
  - Mejor candidato para STT local practico que Whisper puro.
  - Segment streaming/batching posible.
- Piezas que no sirven:
  - Sigue siendo STT, no wake.
  - Requiere packaging y model cache.
- Dificultad: media.
- Dependencias: CTranslate2, model downloads, ffmpeg.
- Riesgos: instalacion, GPU/CPU variance.
- Prioridad: alta para STT local fase futura.
- Conviene: spike local.
- Encaja:
  - STT provider local.

### 2.15 `rhasspy/piper`

- URL: https://github.com/rhasspy/piper
- Stack: C++/Python TTS, ONNX voices.
- Que hace:
  - TTS local rapido.
  - Muchas voces.
- Piezas utiles:
  - TTS local sin API.
  - Latencia razonable.
  - Voz masculina elegante si se encuentra modelo adecuado.
- Piezas que no sirven:
  - No garantiza voz JARVIS pelicula.
  - Integracion de audio streaming requiere trabajo.
- Dificultad: media.
- Dependencias: Piper binary, voice models.
- Riesgos: calidad variable por voz.
- Prioridad: alta para voz local.
- Conviene: provider opcional.
- Encaja:
  - `jarvis/voice/gpt_sovits_adapter.py` style provider abstraction.
  - Future `piper_adapter`.

### 2.16 `OHF-Voice/wyoming`

- URL: https://github.com/OHF-Voice/wyoming
- Stack: Python protocol ecosystem for local voice satellites/services.
- Que hace:
  - Protocol for local voice services.
  - Used by Home Assistant voice ecosystem.
- Piezas utiles:
  - Separar JARVIS daemon de STT/TTS/wake services.
  - Encaja con VPS/movil/satellites.
- Piezas que no sirven:
  - Anade complejidad protocolar.
  - No necesario para PR #156.
- Dificultad: media-alta.
- Dependencias: Wyoming services.
- Riesgos: sobrearquitectura temprana.
- Prioridad: media.
- Conviene: estudiar para fase voice daemon.
- Encaja:
  - Multi-device voice runtime.

## 3. Comparativa contra nuestro JARVIS

| Area | Estado en nuestro JARVIS | Que tienen otras repos | Que nos falta | Repos utiles | Recomendacion | Prioridad |
|---|---|---|---|---|---|---|
| Arquitectura general | Governance fuerte, read model, Hermes bridge, preview gates | Muchas mezclan assistant/runtime/UI | Realtime bus operativo | OpenClaw UI, OVOS, Leon | Adoptar patrones, no runtime | Alta |
| Runtime local/daemon | Hay local daemon/control planes, pero UI sigue read mostly | OVOS/Mycroft tienen daemon voice real | Service manager/tray/doctor | OVOS, Mycroft | Disenar daemon JARVIS propio | Alta |
| UI/HUD/Presence | Presence UI buena, aun dashboard en detalles | HUD completo, mobile, monitor | HUD 3D + realtime | OpenClaw, Jarvis-CV | Evolucionar `/jarvis`, no reemplazar | Alta |
| Orbe 3D/reactor | CSS/React reactor en progreso | R3F, particles, bloom, starfield | WebGL/R3F verdadero | Jarvis-CV, Generative Visualizer, my-jarvis | PR especifica de orb 3D | Alta |
| Voz visual | Estados + smart bar | VoiceOrb, waves, particles, transcript animations | Visualizer robusto por estado/amplitud | react-ai-voice-visualizer | Adaptar UI sin mic capture | Media-alta |
| STT | Browser STT manual | Whisper/faster-whisper/local stacks | Provider local | faster-whisper, Whisper | Anadir provider abstraction | Alta |
| TTS | Browser TTS | Piper, ElevenLabs, Edge TTS | Voz premium local/API | Piper, cam-hm, my-jarvis | Piper local primero, API despues | Alta |
| Voz estilo JARVIS | Tone profiles basicos | Custom voice/API voices | Voz masculina premium legal | Piper, ElevenLabs-style future | No clonar exacto; voz licenciada | Alta |
| Wake phrase | Contrato futuro, no real | openWakeWord, OVOS hotword | Wake daemon seguro | openWakeWord, OVOS | Spike aislado | Alta |
| Conversacion continua | En PR #156 manual continua | Voice assistants reales | Session manager backend | ethanplusai, OVOS | Formalizar `VoiceSession` | Alta |
| Comportamiento/persona | Respuestas locales simples | Persona voice-first | Persona engine | ethanplusai | Crear behavior layer | Alta |
| Camara real | Placeholder/control-plane | MediaPipe/gestos/face/pose | Opt-in camera runtime | Jarvis-CV | PR separada con privacy gates | Media-alta |
| Vision/analisis visual | Preview | MediaPipe + AR overlays | Local vision model / redaction | Jarvis-CV | Empezar con preview opt-in | Media |
| Grabacion audio bruto | Bloqueado, contrato futuro | Algunas capturan mic | Opt-in storage lifecycle | Nuestro `voice/storage.py` | Disenar con retention/delete/audit | Media |
| Memoria | Personal/outcome/learning pieces | Jarvis Orb 4-tier, ChromaDB | Unified visible memory | TheStack, ethanplusai | Consolidar memory read model | Alta |
| Compactacion/aprendizaje | Hay docs y learning proposals | Some vector memory | Memory compaction UI | TheStack | Implementar memory approval flow | Alta |
| Approvals | Muy fuerte | Casi ninguna repo lo tiene | Voice approvals future | Nuestro stack | Mantener ventaja | Alta |
| Ejecucion gobernada | Hermes bridge | Otras ejecutan directo | Mas adapters bajo gates | Nuestra arquitectura | No copiar direct execution | Alta |
| Mobile | Preview/PWA plan | OpenClaw mobile/PWA | Pairing/revocation | OpenClaw, mobile docs | Mobile client gobernado | Media |
| VPS/remoto | Future clients/bridges | WebSocket/server deployments | Secure tunnel/device registry | OpenClaw, OVOS | Fase posterior | Media |
| Telegram-Hermes | Gateway existe | Few repos | JARVIS-governed remote approvals | Nuestro gateway | Integrar con device trust | Media-alta |
| WebSocket/streaming | Falta en `/jarvis` | Varias tienen WS/SSE | `jarvis_event_stream` | OpenClaw, my-jarvis, ethanplusai | Anadir read-only event bus | Alta |
| Diagnostico local | Doctor CLI existe en Hermes | Some logs/rate limits | JARVIS local doctor panel | my-jarvis, Hermes doctor | Unificar checks | Media |
| Instalacion/deps | Muchas piezas docs/tests | Docker/setup scripts | One-command JARVIS local | cam-hm, OpenClaw | Crear installer/doctor | Alta |
| Seguridad | Mejor que externas | Algunas sin auth/gates | Threat model formal para sensors | Nuestro stack | Mantener contract-first | Alta |
| Auditoria | Fuerte en backend | Pocas externas | Audit visible realtime | TheStack/OpenClaw ideas | Timeline/audit stream | Alta |
| Rendimiento | No medido visualmente | 60fps budgets | FPS/power save | OpenClaw, Jarvis-CV | Perf budget PR | Media |
| Escalabilidad | Buen docs roadmap | Realtime services | Service boundaries | OVOS/Wyoming | Event bus + providers | Alta |
| Mantenibilidad | Tests extensos | Algunas demos simples | Reduce monolithic TSX | OpenClaw components | Component extraction | Alta |

## 4. Gap analysis completo

### Visual / presencia

Falta:

- R3F/Three.js real.
- Postprocessing bloom.
- Shader/material propio del reactor.
- Particulas con instancing.
- Audio-driven amplitude segura.
- Performance budget desktop/mobile.
- Power-save mode.
- Componentizacion del TSX actual.
- Visual states mapeados a eventos backend reales.
- Orb thinking ligado a razonamiento/memoria/Hermes, no solo voice state.

### Voz

Falta:

- Voice provider abstraction formal para navegador/local/API.
- STT local despues de wake/manual.
- TTS local premium.
- Voice queue manager.
- Ducking/cancel/interrupt.
- Latency budget.
- Confidence/readback.
- VAD seguro.
- Separacion `wake_listening` vs `conversation_active` vs `recording`.
- Tests con mocks de SpeechRecognition/TTS.
- Consent UX mas formal.

### Comportamiento

Falta:

- Persona engine.
- Respuestas con estilo consistente.
- Modos: calmado, concentrado, alerta, intenso, critico.
- Conversation memory visible pero controlada.
- Clarification policy.
- "No puedo hacer eso todavia" elegante.
- Readback para acciones sensibles.
- Anti-overpromising.

### Camara / vision

Falta:

- Camara real opt-in.
- Indicador visible persistente.
- Stop global.
- Scope: que puede mirar.
- Redaction/local-only.
- No face/person analysis por defecto.
- MediaPipe/gesture preview.
- Local vision model optional.
- Frame retention policy.
- Audit events.

### Memoria

Falta:

- Unificacion memory providers vs JARVIS memory.
- Entidades, preferencias, decisiones, projects.
- Contradiction detection.
- Superseded/verified status.
- Memory approval for sensitive memory.
- Compaction jobs.
- Forget/delete UI.
- Memory influence audit: por que JARVIS recordo esto.

### Ejecucion

Falta:

- Mas adapters reales bajo Hermes gates.
- Execution preview -> approval -> Hermes dispatch -> audit -> rollback.
- Stop/kill handling real.
- Terminal/browser/filesystem guard integration visible.
- Dry-run required before sensitive execution.
- Approval expiration/challenge.

### Remoto / movil

Falta:

- Pairing seguro.
- Device trust registry.
- Revocation.
- Push/notifications.
- Offline mode no-side-effects.
- Telegram-Hermes bridge gobernado por JARVIS.
- VPS bridge with auth, audit, and no secrets leakage.
- Remote kill switch.

### Seguridad

Falta:

- Threat model formal para sensors/voice/remote.
- Sensor permission ledger.
- Audio/video retention and deletion policy.
- Voice approval challenge protocol.
- Tamper-evident audit log.
- Secrets scanning before execution.
- Rate limiting / abuse protection.
- Local-only vs cloud modes.

### Instalacion

Falta:

- One-command local install.
- Dependency doctor para STT/TTS/wake/camera/GPU.
- Service install/uninstall.
- Tray app.
- Port conflict handling.
- Model cache management.
- ffmpeg/Piper/Whisper checks.

### Escalabilidad

Falta:

- Event bus.
- Provider interfaces.
- Service boundaries.
- Backpressure.
- Streaming state model.
- Telemetry/metrics.
- Componentized frontend.
- Performance regression tests.

## 5. Plan maestro por fases

### Fase 0 - External JARVIS Adoption Plan

- Objetivo: congelar decisiones antes de copiar patrones externos.
- Implementa: documento de arquitectura, matriz adopt/adapt/reject.
- Repos: todas las investigadas.
- Dependencias: ninguna.
- Archivos probables: docs.
- Tests: docs/static tests si el repo exige docs contract.
- Prueba: revision de David.
- Riesgos: scope creep.
- Criterio: David aprueba fases.
- Requiere aprobacion David: si.

### Fase 1 - Cerrar PR #156 como Local Voice Loop + Presence Reactor baseline

- Objetivo: terminar loop manual seguro y reactor CSS/React baseline.
- Implementa: test green, docs, no ampliar mas scope.
- Repos externas: ninguna directa.
- Dependencias: ninguna.
- Archivos: los ya tocados.
- Tests: dashboard shell/status, build.
- Prueba: navegador compatible y no compatible.
- Riesgos: meter demasiado 3D en #156.
- Criterio: voz manual continua, fallback honesto, no seguridad rota.
- Aprobacion David: no para cerrar, si si se cambia scope.

### Fase 2 - Componentizar `/jarvis`

- Objetivo: sacar el TSX monolitico a componentes mantenibles.
- Implementa: `PresenceCore`, `SmartBar`, `VoicePanel`, `CameraPanel`,
  `ApprovalPanel`, `types`.
- Repos: OpenClaw UI como referencia de estructura.
- Dependencias: ninguna.
- Archivos: `web/src/pages/jarvis/*`, `web/src/components/jarvis/*`.
- Tests: static no dangerous APIs; build.
- Prueba: UI igual funcional.
- Riesgos: romper tests por strings.
- Criterio: sin cambio funcional, mas mantenible.
- Aprobacion David: no.

### Fase 3 - Orbe 3D WebGL real

- Objetivo: nucleo cinematografico real.
- Implementa: R3F scene, reactor mesh, rings, particles, bloom, state-driven
  animation.
- Repos: Jarvis-CV, Generative 3D Audio Visualizer, OpenClaw UI.
- Dependencias npm: `three`, `@react-three/fiber`, `@react-three/drei`,
  `@react-three/postprocessing`.
- Archivos: `JarvisOrbScene.tsx`, `jarvisOrbConfig.ts`, tests.
- Tests: build, static dependency tests, Playwright screenshot si esta
  disponible.
- Prueba: desktop/mobile viewport, FPS sanity.
- Riesgos: WebGL performance.
- Criterio: nonblank canvas, state changes, no sensor activation.
- Aprobacion David: si por nuevas deps.

### Fase 4 - Event bus read-only `/jarvis`

- Objetivo: UI viva con stream local.
- Implementa: SSE/WebSocket read-only para voice state, Hermes state, approvals,
  timeline.
- Repos: OpenClaw UI, my-jarvis, ethanplusai.
- Dependencias: preferir SSE primero; WS si necesita bidireccional.
- Archivos: `jarvis/api/app.py`, `dashboard_event_stream.py`, frontend hook.
- Tests: no mutation routes, event schema.
- Prueba: backend emits fake/local events; UI updates.
- Riesgos: abrir canal remoto inseguro.
- Criterio: read-only stream, auth/local constraints.
- Aprobacion David: si.

### Fase 5 - Voice Session Manager

- Objetivo: sacar conversacion manual del frontend a contrato formal.
- Implementa: `VoiceSession` local: active, idle timeout, interrupt, cancel,
  transcript lifecycle.
- Repos: OVOS/Mycroft patterns, ethanplusai behavior.
- Dependencias: ninguna inicial.
- Archivos: `jarvis/voice_session_control.py`, API status.
- Tests: timeout, cancel, no execution, no raw audio.
- Prueba: `/jarvis` reflects session.
- Riesgos: parecer runtime duplicado.
- Criterio: JARVIS controla session; Hermes no se toca.
- Aprobacion David: no.

### Fase 6 - TTS local provider

- Objetivo: voz mejor que navegador sin API externa.
- Implementa: Piper provider, voice selection, streaming/caching, fallback
  browser.
- Repos: Piper, cam-hm.
- Dependencias Python/system: Piper binary/model, ffmpeg opcional.
- Archivos: `jarvis/voice/piper_adapter.py`, scripts local, docs.
- Tests: provider unavailable, no raw upload, cache policy.
- Prueba: local TTS smoke.
- Riesgos: instalacion/modelos.
- Criterio: voz local opt-in, no cloud.
- Aprobacion David: si por binarios/modelos.

### Fase 7 - STT local provider

- Objetivo: reemplazar/alternar browser STT.
- Implementa: faster-whisper provider para `conversation_active`.
- Repos: faster-whisper, Whisper.
- Dependencias: CTranslate2, ffmpeg, models.
- Archivos: `jarvis/voice/stt_faster_whisper.py`.
- Tests: provider unavailable, transcript lifecycle, no raw persistence.
- Prueba: local mic opt-in test.
- Riesgos: CPU/GPU latency.
- Criterio: local STT works after manual activation.
- Aprobacion David: si.

### Fase 8 - Wake Listening seguro

- Objetivo: detectar `Jarvis/Hola Jarvis` sin grabar ni transcribir todo.
- Implementa: wake daemon opt-in, openWakeWord spike, indicator, stop.
- Repos: openWakeWord, OVOS.
- Dependencias: openWakeWord/model, audio device access.
- Archivos: `jarvis/real_wake_listener.py`, service scripts.
- Tests: no raw storage, no transcript until activation, no approval.
- Prueba: wake opens `conversation_active`; false positive handling.
- Riesgos: privacidad, always mic confusion.
- Criterio: wake listening != recording != transcribing.
- Aprobacion David: si, explicita.

### Fase 9 - Audio bruto local opt-in

- Objetivo: permitir grabacion local futura bajo control fuerte.
- Implementa: opt-in, visible indicator, stop, retention, delete, audit.
- Repos: nuestro `voice/storage.py`; no copiar demos.
- Dependencias: local filesystem, maybe ffmpeg.
- Archivos: `jarvis/voice/storage.py`, docs/runbook.
- Tests: retention, delete, audit, disabled by default.
- Prueba: manual recording session.
- Riesgos: datos sensibles.
- Criterio: default false; user can purge.
- Aprobacion David: si, fuerte.

### Fase 10 - Persona / Behavior Engine

- Objetivo: JARVIS elegante, calmado, premium, humano.
- Implementa: response style layer, tone policy, refusal style, confirmations.
- Repos: ethanplusai as reference; no copy prompts.
- Dependencias: ninguna.
- Archivos: `jarvis/voice/behavior.py`, frontend metadata.
- Tests: no technical IDs visible, sensitive actions require approval.
- Prueba: transcript examples.
- Riesgos: overpromising.
- Criterio: tone consistent, safe.
- Aprobacion David: si para personality.

### Fase 11 - Memoria visible y compactada

- Objetivo: brain real y observable.
- Implementa: memory read model, entities, decisions, contradictions, proposals.
- Repos: TheStack jarvis-orb.
- Dependencias: SQLite/FTS ya disponible; vector optional later.
- Archivos: `jarvis/personal_memory.py`, `dashboard_read_model.py`, UI memory
  panel.
- Tests: no opaque memory, approval for sensitive memory, delete.
- Prueba: memory proposal -> approve -> visible influence.
- Riesgos: privacy.
- Criterio: memory explains itself.
- Aprobacion David: si.

### Fase 12 - Camara / vision opt-in

- Objetivo: vision real segura.
- Implementa: camera session, visual indicator, stop, MediaPipe preview, no
  face/person by default.
- Repos: Jarvis-CV.
- Dependencias: `@mediapipe/*`, maybe `@tensorflow/tfjs`.
- Archivos: camera runtime, UI panel.
- Tests: no default camera, explicit permission, audit.
- Prueba: start camera manually; stop; no storage.
- Riesgos: privacy/biometrics.
- Criterio: opt-in only, no background camera.
- Aprobacion David: si.

### Fase 13 - Vision analysis local

- Objetivo: analizar pantalla/documento/camara con scope.
- Implementa: local vision model/provider abstraction, redaction, scope
  statement.
- Repos: Jarvis-CV ideas, Hermes vision tools.
- Dependencias: model/provider later.
- Archivos: `tools/vision_tools.py`, `jarvis/ambient_vision`.
- Tests: no sensitive inference, no external provider unless approved.
- Prueba: bounded image analysis.
- Riesgos: hallucination, privacy.
- Criterio: states what it sees and uncertainty.
- Aprobacion David: si.

### Fase 14 - Mobile / Telegram / Remote governed channels

- Objetivo: remoto sin convertir movil/VPS en runtime libre.
- Implementa: device pairing, revocation, Telegram status/approvals preview,
  challenge.
- Repos: OpenClaw mobile/PWA; our gateway Telegram.
- Dependencias: existing gateway, maybe PWA later.
- Archivos: `jarvis/mobile`, `gateway/platforms/telegram.py`.
- Tests: no direct Hermes, device trust, approval gates.
- Prueba: Telegram status command and guarded approval preview.
- Riesgos: remote attack surface.
- Criterio: channel authenticated/gated/audited.
- Aprobacion David: si.

### Fase 15 - Voice approvals

- Objetivo: permitir approvals por voz solo bajo condiciones fuertes.
- Implementa: authenticated channel, challenge code, readback, anti-wake
  approval.
- Repos: none directly; our approval gateway.
- Dependencias: VoiceSession + trusted device.
- Archivos: `jarvis/voice_approval_channel.py`, `approval_gateway.py`.
- Tests: wake phrase never approves; critical requires challenge.
- Prueba: low-risk approval mock; high-risk blocked without challenge.
- Riesgos: accidental approval.
- Criterio: no critical action approved by casual voice.
- Aprobacion David: si, fuerte.

### Fase 16 - Hermes execution expansion under JARVIS

- Objetivo: acciones reales graduales.
- Implementa: exact scope, dry-run, approval, Hermes dispatch, audit, rollback.
- Repos: no external runtime.
- Dependencias: existing Hermes.
- Archivos: `jarvis/missions/*`, `runtime/hermes_adapter.py`.
- Tests: no bypass, dangerous routes blocked.
- Prueba: local read-only -> low-risk action -> higher-risk gated.
- Riesgos: real side effects.
- Criterio: every execution has approval/audit.
- Aprobacion David: si por action class.

### Fase 17 - Diagnostics / installer

- Objetivo: JARVIS operativo en PC de David.
- Implementa: doctor checks, model checks, ports, audio devices, browser
  support.
- Repos: cam-hm Docker ideas, our `hermes_cli/doctor.py`.
- Dependencias: optional.
- Archivos: `jarvis/doctor.py`, scripts local.
- Tests: missing deps reported honestly.
- Prueba: run doctor.
- Riesgos: platform variance Windows/WSL.
- Criterio: user knows exactly what works.
- Aprobacion David: no.

### Fase 18 - Performance and power modes

- Objetivo: 60fps when possible, graceful fallback.
- Implementa: FPS monitor, power-save, particle budgets.
- Repos: OpenClaw, Jarvis-CV.
- Dependencias: none.
- Archivos: orb config/perf hook.
- Tests: rendering fallback.
- Prueba: desktop/mobile viewport.
- Riesgos: complexity.
- Criterio: no blank canvas, no UI lockup.
- Aprobacion David: no.

### Fase 19 - Audit hardening

- Objetivo: cada sensor/action/memory event auditable.
- Implementa: audit stream, retention, export, tamper awareness.
- Repos: TheStack ideas; our audit modules.
- Dependencias: SQLite/logging.
- Archivos: `jarvis/approval_audit.py`, dashboard timeline.
- Tests: audit for wake/session/record/camera/approval.
- Prueba: timeline shows events.
- Riesgos: log sensitive data.
- Criterio: audit metadata without secrets/raw audio.
- Aprobacion David: si for retention policy.

### Fase 20 - Personal OS integration

- Objetivo: JARVIS real como sistema local de David.
- Implementa: calendar/docs/email previews, focus/context, routines, family ops.
- Repos: none directly; our roadmap.
- Dependencias: connectors.
- Archivos: `jarvis/personal_os`, `daily_operator`.
- Tests: sensitive reads require approval, no sends without strong approval.
- Prueba: local daily brief preview.
- Riesgos: privacy and scope creep.
- Criterio: useful without violating gates.
- Aprobacion David: si.

## 6. Orden recomendado

1. Cerrar PR #156 con Local Voice Loop manual + Presence Reactor baseline, sin
   ampliar mas.
2. Crear PR de arquitectura/docs: External JARVIS Adoption Plan.
3. Componentizar `/jarvis`.
4. Implementar orbe 3D real con R3F/postprocessing.
5. Anadir event bus read-only.
6. Formalizar Voice Session Manager.
7. Anadir TTS local Piper.
8. Anadir STT local faster-whisper.
9. Wake listening seguro con openWakeWord.
10. Persona/Behavior Engine.
11. Memoria visible/compactada.
12. Camara opt-in con MediaPipe preview.
13. Audio bruto local opt-in.
14. Mobile/Telegram/remoto gobernado.
15. Voice approvals con challenge/readback.
16. Ejecucion Hermes real ampliada bajo gates.
17. Installer/doctor.
18. Performance/power modes.
19. Audit hardening.
20. Personal OS integration.

## 7. Que hacer con la PR actual #156

Recomendacion: cerrar #156 como Local Voice Loop basico/manual continuo +
Presence Reactor baseline, no convertirla en la mega-adopcion de todas las repos
externas.

No meter en #156:

- R3F/Three.js real.
- MediaPipe/camara real.
- Wake listener real.
- Piper/faster-whisper.
- WebSocket event bus.
- Mobile/Telegram approvals.
- Grabacion local de audio bruto.

Si dejar en #156:

- Manual continuous conversation si ya esta estable.
- Fallback honesto STT/TTS.
- Smart bar humana.
- Contrato `wake_listening` futuro.
- Reactor visual CSS/React baseline.
- Tests/docs de seguridad.

Despues conviene una PR especifica: External JARVIS Adoption Plan o JARVIS 3D
Presence Architecture, aprobada por David antes de anadir dependencias.

## 8. Dependencias recomendadas

### npm obligatorias futuras

- `three`: motor 3D.
- `@react-three/fiber`: integracion React.
- `@react-three/drei`: helpers, controls, effects, text, performance helpers.
- `@react-three/postprocessing`: bloom/glow cinematografico.
- `zustand`: opcional para estado UI si se componentiza mucho.
- `framer-motion`: opcional para transiciones UI no-canvas.
- `@mediapipe/tasks-vision` o paquetes MediaPipe: solo fase camara/gestos.

### npm opcionales

- `leva`: tuning dev de escena, no en UI final.
- `stats.js`: FPS/debug dev.
- `simplex-noise`: particulas organicas.
- `tone` o Web Audio utils: solo cuando audio capture opt-in este aprobado.

### Python obligatorias futuras

- `fastapi`/`uvicorn`: ya hay API; para event stream si aplica.
- `websockets` o SSE compatible.
- `faster-whisper`: STT local.
- `openwakeword`: wake word local.
- `piper-tts`/Piper binary: TTS local.
- `sounddevice`/`pyaudio`: solo en daemon local, no frontend.
- `numpy`: audio processing.
- `aiosqlite`: memoria/eventos locales si se expande.
- `pytest`: necesario en este entorno, ahora falta.

### Sistema operativo

- `ffmpeg`: STT/TTS/audio conversion.
- Audio device access.
- GPU optional for STT.
- Windows/WSL bridge decision: cuidado con mic/camera desde WSL.
- Service/tray layer:
  - Windows service/task scheduler.
  - macOS launch agent si aplica.
  - Linux systemd si aplica.

### No anadir todavia

- ElevenLabs.
- Gemini/OpenAI/Claude API para voz.
- MediaPipe.
- `getUserMedia` camera/mic arbitrary.
- Audio recording library.
- Wake daemon dependency.

## 9. Voz estilo JARVIS

### Objetivo

Voz masculina, elegante, premium, calmada, precisa, con ligera sensacion
britanica si es posible, pero sin clonar una voz exacta protegida.

### Ruta por niveles

#### Nivel 1 - Navegador

- Usar `speechSynthesis`.
- Preferir voces `en-GB` o `es-ES` masculinas/naturales si existen.
- Pros: cero dependencia.
- Contras: calidad inconsistente, voces roboticas, navegador puede usar
  servicios internos.
- Coste: cero.
- Privacidad: depende del navegador.
- Uso: PR #156.

#### Nivel 2 - Sistema local

- Windows/macOS installed voices.
- Elegir voz masculina premium si David instala una voz de sistema.
- Pros: local, simple.
- Contras: API browser puede no exponer todas.
- Coste: depende de voice pack.

#### Nivel 3 - Piper local

- Buscar voz masculina inglesa britanica o espanola sobria.
- Ajustar pitch/rate/prosody.
- Pros: local, sin API.
- Contras: calidad menor que ElevenLabs.
- Coste: cero.
- Privacidad: alta.
- Recomendado como primer TTS real.

#### Nivel 4 - TTS neural local avanzado

- Coqui XTTS / GPT-SoVITS / OpenVoice-style si legalmente se usa voz propia o
  licenciada.
- Pros: calidad alta.
- Contras: GPU, modelos, legalidad, latencia.
- Coste: hardware.
- Requiere politica de voces.

#### Nivel 5 - API futura

- ElevenLabs, Azure Neural Voice, OpenAI TTS, etc.
- Pros: mejor calidad.
- Contras: coste, privacidad, latencia, dependencia externa.
- Debe ser opt-in y auditado.
- Nunca usar para secretos sin aprobacion.

### Persona/prompt

- Frases cortas.
- Tono calmado.
- Evitar IDs tecnicos.
- No exagerar capacidad.
- Para riesgo: "Eso requiere revision segura."
- Para ejecucion: "Puedo prepararlo; no lo ejecutare sin aprobacion."
- Para wake phrase: "Estoy contigo. La activacion no es permiso."
- Para errores: "No tengo soporte de voz en este navegador; no voy a fingir
  escucha."

## 10. Seguridad y privacidad

### Wake listening sin grabar ni transcribir todo

- Wake listener escucha solo patron de activacion.
- Buffer circular efimero en memoria.
- No persistir audio.
- No enviar audio al backend externo.
- No transcribir conversacion completa.
- No crear historial.
- Indicador visible `wake listening`.
- Stop global.
- Audit metadata: started/stopped/device/model, no raw audio.

### Conversation active separada

- Empieza tras wake valido o activacion manual.
- Aqui si puede haber STT de frase de David.
- Transcript temporal.
- Retencion por defecto: cero o sesion actual.
- Stop/cancel corta STT/TTS.
- Timeout automatico.

### Grabacion local explicita

- Boton separado: grabar.
- Confirmacion clara.
- Indicador persistente.
- Ruta local visible.
- Retencion configurable.
- Delete/purge.
- Audit event.
- No grabar durante wake listening por defecto.

### Audio bruto

- `audio_storage=false` por defecto.
- `raw_audio_sent_to_backend=false` siempre salvo fase explicita aprobada.
- Si se guarda: local only, encrypted optional, retention, delete.

### Approvals por voz

- Wake phrase nunca aprueba.
- Voz solo puede aprobar si:
  - canal autenticado;
  - dispositivo confiable;
  - action scope exacto;
  - readback;
  - challenge/passphrase;
  - audit;
  - riesgo permite voice approval.
- Critical actions: double/triple confirmation, preferably non-voice fallback.

### Camara segura

- No background camera.
- No camera on page load.
- Indicador visible.
- Scope: document/screen/object, not person identity by default.
- Stop visible.
- No recording by default.
- No face/person inference by default.
- Audit metadata.

### Canal remoto seguro

- Pairing.
- Device registry.
- Token revocation.
- No secrets in notifications.
- Remote commands become JARVIS intents, not Hermes execution.
- Telegram-Hermes bridge:
  - Telegram sends request.
  - JARVIS classifies risk.
  - ApprovalGateway decides.
  - Hermes executes only after valid gates.
  - Audit logs every step.

## 11. Informe final

### Plan recomendado

Cerrar #156 como base segura. Despues hacer una PR de plan/adopcion externa y,
tras aprobacion, empezar por componentizar `/jarvis` y construir el orbe 3D
real. No meter wake/camara/STT local/TTS local en la misma PR visual.

### Primera fase concreta

Primera fase despues de #156:

`PR #157 - JARVIS External Adoption Plan + /jarvis Component Architecture`

- No dependencias nuevas.
- No sensores.
- No runtime nuevo.
- Divide TSX.
- Documenta que se adopta de cada repo.
- Prepara interfaces para `PresenceCore3D`, `VoiceSession`,
  `JarvisEventStream`.

### Que NO tocar todavia

- No `getUserMedia`.
- No MediaRecorder.
- No AudioContext capture.
- No wake daemon real.
- No camera real.
- No Piper/faster-whisper install.
- No ElevenLabs/OpenAI/Gemini.
- No approvals por voz.
- No Telegram execution path.
- No Hermes direct from frontend.
- No `/execute`.

### Que debe decidir David antes de implementar

- Si acepta R3F/Three/postprocessing como dependencias frontend.
- Si quiere TTS local Piper primero o seguir con navegador.
- Si wake listening real sera prioridad antes o despues de camara.
- Que nivel de voz premium acepta: local imperfecta vs API futura.
- Politica de grabacion local: si se permite, donde, cuanto tiempo, como
  borrar.
- Si movil/Telegram entra antes o despues de memoria/camara.
- Si el orbe debe vivir solo en `/jarvis` o tambien como desktop overlay/tray
  futuro.

### Riesgos criticos

- Scope creep: intentar meter voz local, wake, camara, orb 3D y remoto en una
  PR.
- Duplicar Hermes copiando runtimes externos.
- Activar sensores sin contrato.
- Voz JARVIS ilegal si se clona una voz exacta.
- WebSocket/remoto sin auth.
- Memoria opaca o sensible sin approval.
- Performance de WebGL en PCs modestos.
- Windows/WSL audio/camera friction.

### Proximos comandos/pasos sugeridos

No ejecutar implementacion hasta que David decida:

1. Cerrar #156 o recortarla si esta demasiado grande.
2. Aprobar PR de arquitectura/adopcion externa.
3. Aprobar dependencias 3D.
4. Definir prioridad: orbe 3D primero, o TTS/STT local primero.

Recomendacion tecnica: orbe 3D + event bus read-only antes de wake/camara,
porque mejora la presencia sin abrir todavia la superficie de privacidad mas
peligrosa.
