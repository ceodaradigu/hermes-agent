# JARVIS Capability Research Adoption Plan

Fecha: 2026-06-18
Repo/rama: `ceodaradigu/hermes-agent` / `pr-157-external-jarvis-adoption-master-build`

Este informe es una auditoria externa nueva y amplia. No implica adopcion
automatica, copia de codigo ni instalacion de dependencias. La regla permanente
se mantiene:

- JARVIS gobierna: intencion, riesgo, aprobacion, auditoria, memoria y control.
- Hermes ejecuta.
- No construir otro Hermes ni duplicar runtime de ejecucion.
- Sensores solo con opt-in, indicador visible, stop/cancel y auditoria.
- Wake phrase nunca aprueba.
- Ejecucion peligrosa solo via `ApprovalGateway`, clasificacion de riesgo,
  auditoria, y plan de rollback/stop.

## Estado de implementacion de Fase 1

La Fase 1 recomendada en este informe ya fue implementada en la rama
`pr-157-external-jarvis-adoption-master-build` como base operativa local:

- Sensor Ledger backend metadata-only para sensores/sesiones, sin audio bruto,
  frames ni material de credenciales.
- Event stream read-only con `schema_version`, `event_id`, `created_at`,
  `risk_level`, payload seguro y heartbeat.
- Doctor local ampliado con estado de backend, frontend esperado, stream,
  Hermes, deps opcionales, Python, plataforma, proceso/psutil opcional, puertos
  esperados y capacidades browser-only marcadas como `client_side_unknown`.
- Policy status visible/read-only con separacion directa/simple/strong/double/
  triple/denied y el contrato JARVIS gobierna / Hermes ejecuta.
- `/jarvis` muestra esos estados en el drawer `Sistemas`; no se añadieron rutas
  de ejecucion, approval o sensor mutation.

La siguiente fase recomendada pasa a ser F2: evolucionar HUD/orbe/R3F y
performance/fallback sin añadir nuevos permisos de sensores ni ejecución.

## Estado de implementacion de Fase 2

La Fase 2 tambien quedo implementada en esta rama, sin instalar dependencias:

- `/jarvis` usa un orbe WebGL manual reforzado con particulas orbitando,
  anillos radiales, marcas holograficas, profundidad, glow/bloom simulado y
  ondas por estado.
- Estados visuales soportados: `idle`, `wake_listening`, `listening`,
  `transcribing`, `thinking`, `speaking`, `alert`, `error`, `stopped`,
  `executing`.
- Se adapto la direccion visual de `pmndrs/react-three-fiber`, `drei`,
  `react-postprocessing`, OpenClaw/Jarvis-CV y visualizadores de audio 3D, pero
  se reimplemento en WebGL manual para evitar nuevas dependencias y mantener
  control fino de performance.
- Performance budget: `targetFrameMs`, `particleBudget`, reduccion con
  `prefers-reduced-motion`, pixel ratio limitado y fallback si WebGL/canvas
  falla.
- No se activaron sensores nuevos ni ejecucion Hermes.

La siguiente fase recomendada pasa a ser F3: retencion/auditoria local de audio
bruto y sesiones de sensores, manteniendo metadata-only backend y opt-in visible.

## 1. Resumen ejecutivo

Nuestro JARVIS ya tiene una base mejor gobernada que la mayoria de asistentes
externos: `/jarvis` es una Presence UI local, el read model expone Hermes,
approvals, mission state, memoria, sensores y doctor en modo read-only, y el
frontend no ejecuta Hermes directamente. En el estado actual del worktree ya
existen event stream read-only, camara local opt-in en navegador, grabadora local
de audio bruto, brain visible read-only, doctor local read-only, `ApprovalGateway`
y `PolicyEngine` inicial.

La oportunidad externa no es "copiar otro JARVIS". Es adoptar piezas
especializadas que eleven presencia, voz, memoria, auditoria, seguridad,
operacion local y remoto gobernado sin romper el contrato JARVIS/Hermes.

Prioridad recomendada:

1. Cerrar la base operativa local: sensor ledger backend, voice session manager,
   doctor mas preciso y event stream mas robusto.
2. Evolucionar el orbe/HUD a R3F/Three con performance budget, sin activar
   sensores nuevos.
3. Formalizar voz local: VAD + STT/TTS providers, despues wake opt-in.
4. Consolidar memoria temporal/contradicciones/provenance con SQLite primero;
   Graphiti/mem0 como referencia, no como runtime inmediato.
5. Endurecer ejecucion: policy-as-code, secret scanning, sandbox opcional,
   audit tamper-evident, y solo despues expandir acciones Hermes.
6. Remoto/Telegram/desktop tray solo como canales gobernados, nunca como bypass.

Capacidades nuevas mas importantes respecto al informe anterior:

- Policy-as-code con OPA/Cedar para separar reglas de aprobacion del regex MVP.
- Tamper-evident audit local inspirado en immudb/Rekor/Trillian.
- Sandbox layer para ejecucion local con bubblewrap/nsjail/gVisor/Firecracker,
  pero solo detras de Hermes.
- Secret scanning y preflight safety con TruffleHog/detect-secrets/Semgrep.
- Memoria temporal con provenance y contradiccion automatica inspirada en
  Graphiti.
- Browser automation gobernada con Playwright/browser-use/Skyvern como
  adaptadores de Hermes, no runtime autonomo.
- Desktop tray/daemon con Tauri o pystray para indicador visible y kill switch.
- Remote trust layer con Tailscale/frp solo si hay pairing, revocacion y audit.
- Audio local persistente en IndexedDB solo con retencion y borrado explicitos.
- Observability/health con OpenTelemetry/Prometheus/psutil para hacer JARVIS
  operable, no solo visual.

## 2. Metodologia de busqueda

Se leyeron primero:

- `jarvis/external_jarvis_adoption_plan.md`
- `docs/jarvis-external-adoption-master-build-report.md`
- estado actual del repo y archivos clave de JARVIS: dashboard read model,
  event stream, API, frontend `/jarvis`, approval/policy, wake, audio storage y
  desktop runtime.

Despues se busco en GitHub por capacidades, no por nombre "JARVIS":

- UI 3D/WebGL/R3F/orbe/HUD/performance.
- Voz: STT, TTS, wake word, VAD, voice service protocol.
- Audio bruto local: MediaRecorder, IndexedDB, retencion/borrado.
- Vision/camara: MediaPipe, TFJS, OpenCV, overlays.
- Memoria: semantic memory, temporal graph, vector DB, contradiction/provenance.
- Event bus: FastAPI/SSE/WebSocket/realtime state.
- Desktop daemon/tray/service packaging.
- Mobile/remoto/Telegram/pairing/tunnels.
- Seguridad: approval workflow, policy engine, sandbox, audit tamper-evident,
  dangerous command/secret detection.
- Agentes/automatizacion: planner/executor, browser automation, computer use.
- Doctor/installer/diagnostico/performance/observability.

Madurez es cualitativa y combina popularidad, releases, actividad, uso en
produccion, estabilidad de API y coste de integracion. No se clono ningun repo,
no se instalaron dependencias y no se copio codigo externo.

## 3. Repos/librerias seleccionadas

### 3.1 UI 3D / HUD / performance

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `pmndrs/react-three-fiber` | https://github.com/pmndrs/react-three-fiber | React, Three.js, TS | Alta | Renderer React para Three.js | Orbe declarativo, escenas state-driven, React 19 compatible | Convertir todo `/jarvis` en canvas | Adoptar como dependencia cuando David apruebe | `three`, `@react-three/fiber` | Bundle, WebGL blank, aprendizaje | Alta | F2 |
| `pmndrs/drei` | https://github.com/pmndrs/drei | R3F helpers | Alta | Helpers R3F, `PerformanceMonitor`, `Hud`, `AdaptiveDpr` | Performance/power-save, HUD 3D, helpers de escena | Controles dev visibles | Adoptar parcialmente | `@react-three/drei` | Sobrecarga si se importa sin criterio | Alta | F2 |
| `pmndrs/react-postprocessing` | https://github.com/pmndrs/react-postprocessing | R3F, postprocessing | Media-alta | Bloom, depth, vignette, effects chain | Glow cinematografico del orbe | Efectos pesados en low-end | Adoptar con feature flag | `@react-three/postprocessing` | FPS, mobile GPU | Media-alta | F2 |
| `utsuboco/r3f-perf` | https://github.com/utsuboco/r3f-perf | TS, R3F | Media | Monitor FPS/GPU/memoria para R3F | Dev-only perf panel y report headless | UI final visible | Adoptar dev-only o reimplementar minimal | `r3f-perf` | Exponer debug en produccion | Media | F2/F8 |
| `jincocodev/openclaw-jarvis-ui` | https://github.com/jincocodev/openclaw-jarvis-ui | Vite, Three, Express, WS/SSE | Referencia util | HUD, orbe, SSE/WS, monitor, mobile | Patrones HUD, state stream, power save | Runtime OpenClaw y CRUD directo | Adaptar patrones, no copiar runtime | Three, Express, TTS opcional | Duplicar gateway/runtime | Alta | F2/F3 |
| `Suryansh777777/Jarvis-CV` | https://github.com/Suryansh777777/Jarvis-CV | React, TS, R3F, Drei, MediaPipe | Referencia/demo | HUD 3D + vision + overlays | Stack visual y vision local opt-in | Face/person analysis por defecto | Adaptar visual/MediaPipe patterns | R3F, MediaPipe | Biometria, sensor creep | Media-alta | F2/F6 |
| `zoharbarzilai/Generative-3D-Audio-Visualizer` | https://github.com/zoharbarzilai/Generative-3D-Audio-Visualizer | R3F, Web Audio | Referencia/demo | Esfera audio-reactiva con bloom | Orbe reactivo a estado/amplitud sintetica | Captura de micro directa | Reimplementar visual controlado | R3F, postprocessing | `getUserMedia` accidental | Media | F2 |

### 3.2 Voz / wake / VAD / STT / TTS

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `dscripka/openWakeWord` | https://github.com/dscripka/openWakeWord | Python, ONNX | Media-alta | Wake word local, modelos preentrenados, `hey jarvis` | Wake opt-in local sin cloud | Web audio streaming demo sin gates | Spike aislado detras de daemon | `openwakeword`, audio device | Falsos positivos, always-mic | Alta | F5 |
| `snakers4/silero-vad` | https://github.com/snakers4/silero-vad | Python, Torch/ONNX | Alta | Voice activity detection ligero | VAD para cortar STT y evitar transcribir silencio | Guardar audio o diarizar personas | Adoptar como provider opcional | `torch`/`onnxruntime`, audio IO | Licencia/modelos, CPU variance | Alta | F4 |
| `SYSTRAN/faster-whisper` | https://github.com/SYSTRAN/faster-whisper | Python, CTranslate2 | Alta | Whisper mas rapido/menos memoria | STT local post-activacion | Always-on STT | Adoptar como provider opcional | `faster-whisper`, ffmpeg, modelos | Latencia, modelos pesados | Alta | F4 |
| `ggml-org/whisper.cpp` | https://github.com/ggml-org/whisper.cpp | C/C++, ggml | Alta | Whisper local portable/quantized | Binario local para Windows/CPU | Integracion compleja directa | Evaluar para distribucion local | Binarios/modelos | Packaging multiplataforma | Media-alta | F4/F9 |
| `openai/whisper` | https://github.com/openai/whisper | Python, PyTorch | Alta | STT general multilingue | Baseline de calidad y modelos | Runtime principal por peso | Referencia/fallback tecnico | PyTorch, ffmpeg | Pesado | Media | F4 |
| `OHF-Voice/piper1-gpl` | https://github.com/OHF-Voice/piper1-gpl | C++/Python, ONNX/espeak | Media-alta | TTS neural local rapido | Voz local sin API, web server/API | Clonar voz protegida | Adoptar provider opcional si GPL aceptable | `piper-tts`, modelos | GPL, calidad variable | Alta | F4 |
| `OHF-Voice/wyoming` | https://github.com/OHF-Voice/wyoming | Python, TCP JSONL+PCM | Media | Protocolo P2P para voice services | Separar wake/STT/TTS como servicios locales | Meter red de satellites pronto | Adaptar protocolo o inspirar API | servicios Wyoming | Sobrearquitectura | Media | F7 |
| `OpenVoiceOS/ovos-core` | https://github.com/OpenVoiceOS/ovos-core | Python assistant framework | Media | Voice assistant FOSS con bus/skills | Arquitectura wake/STT/TTS/session | Importar runtime/skills | Referencia, no dependencia core | muchas | Construir otro Hermes | Media | F7 |
| `ethanplusai/jarvis` | https://github.com/ethanplusai/jarvis | Next, FastAPI, WS, Whisper, ElevenLabs | Referencia/demo | Assistant macOS voice-first | UX/persona/state machine | APIs externas/control directo | Adaptar UX, no runtime | OpenAI/ElevenLabs/LangGraph | Privacy/coste/bypass | Media | F10 |

### 3.3 Audio bruto local / retencion / borrado

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `jakearchibald/idb` | https://github.com/jakearchibald/idb | TS/JS, IndexedDB | Alta | IndexedDB promise wrapper pequeno | Audio blob metadata, retention, delete, audit local | Sync remoto | Adoptar para browser local storage si David aprueba | `idb` | Persistir audio sensible | Media-alta | F3 |
| `dexie/Dexie.js` | https://github.com/dexie/Dexie.js | TS/JS, IndexedDB | Alta | IndexedDB ORM | Queries de grabaciones/audit local | Complejidad ORM si no hace falta | Evaluar si `idb` queda corto | `dexie` | Schema creep | Media | F3 |
| `muaz-khan/RecordRTC` | https://github.com/muaz-khan/RecordRTC | JS, WebRTC/MediaRecorder | Media | Grabacion audio/video/screen | Referencia compatibilidad browser | Captura video/screen amplia | No adoptar ahora; reimplementar minimal | WebRTC | Superficie sensor grande | Baja | No tocar |
| `ai/audio-recorder-polyfill` | https://github.com/ai/audio-recorder-polyfill | JS polyfill | Baja-media | Polyfill MediaRecorder audio | Safari/legacy fallback | Activar soporte viejo sin tests | Solo si hay necesidad real | polyfill | Formatos/compat | Baja | F3+ |

### 3.4 Camara / vision / overlays

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `google-ai-edge/mediapipe` | https://github.com/google-ai-edge/mediapipe | C++/Python/JS, on-device ML | Alta | Vision/audio/text tasks on-device | Hands/gesture/object overlays local-only | Face/person identity by default | Adoptar solo en camera opt-in PR | `@mediapipe/tasks-vision` | Metrics/privacy, biometria | Media-alta | F6 |
| `tensorflow/tfjs` | https://github.com/tensorflow/tfjs | JS/WebGL/WebGPU | Alta | ML en navegador/Node | Lightweight local object models | Entrenar/servir modelos grandes | Evaluar posterior | `@tensorflow/tfjs` | Bundle/FPS | Media | F6/F7 |
| `tensorflow/tfjs-models` | https://github.com/tensorflow/tfjs-models | JS pretrained models | Alta | Modelos preentrenados browser | Object detection/pose si MediaPipe no basta | Modelos obsoletos sin policy | Evaluar por caso | TFJS | Privacy/model drift | Media | F7 |
| `opencv/opencv` | https://github.com/opencv/opencv | C++/Python/JS build | Muy alta | Computer vision clasico | Redaction, blur, image preprocessing | Importar OpenCV.js pesado sin necesidad | Reimplementar small ops o provider optional | OpenCV/OpenCV.js | Bundle, CPU | Media | F7 |

### 3.5 Memoria / conocimiento / contradicciones

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `getzep/graphiti` | https://github.com/getzep/graphiti | Python, temporal KG, Neo4j/FalkorDB | Alta emergente | Temporal context graph, provenance, fact invalidation | Contradiccion, historial temporal, provenance | Meter Neo4j ahora | Adaptar modelo primero en SQLite | Graph DB, embeddings, LLM | Complejidad, APIs externas por defecto | Alta | F8 |
| `mem0ai/mem0` | https://github.com/mem0ai/mem0 | Python/TS, memory SDK/server | Alta | Memoria multi-nivel, hybrid search, entity linking | Ideas de extraction/retrieval/eval | Cloud/API key y auto-write sin approval | Referencia/eval, no core inmediato | embeddings/LLM/vector | Memoria opaca, privacy | Media-alta | F8 |
| `chroma-core/chroma` | https://github.com/chroma-core/chroma | Rust/Python/TS | Alta | Vector/search infrastructure | Semantic search local si SQLite FTS no basta | Sustituir memoria explicable | Optional vector backend | Chroma, embeddings | Another DB, privacy | Media | F8+ |
| `getzep/zep` | https://github.com/getzep/zep | Python/Go examples/cloud | Media-alta | Agent memory examples/integrations | Benchmarks/ontology/reference | Managed cloud memory | Referencia, no dependencia | Zep Cloud SDK | Cloud/privacy | Baja-media | F8+ |
| `TheStack-ai/jarvis-orb` | https://github.com/TheStack-ai/jarvis-orb | Python, SQLite FTS, MCP, Tauri/WebGL | Referencia util | Visible memory orb, entity/contradiction | Brain UI + event semantics | MCP brain paralelo | Adaptar schema/UI ideas | aiosqlite/Tauri | Duplicar brain | Alta | F8 |

### 3.6 Event bus / realtime assistant state

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `sysid/sse-starlette` | https://github.com/sysid/sse-starlette | Python, Starlette/FastAPI SSE | Media-alta | Production-ready SSE, disconnect, ping, shutdown | Reemplazar/fortalecer SSE manual | Bidirectional commands | Adoptar si SSE actual crece | `sse-starlette` | Extra dep, auth | Alta | F1 |
| `fastapi/fastapi` | https://github.com/fastapi/fastapi | Python ASGI | Alta | API framework actual | WebSocket/SSE patterns, OpenAPI | Cambiar stack | Mantener | ya usado | Route sprawl | Alta | F1 |
| `python-websockets/websockets` | https://github.com/python-websockets/websockets | Python WS | Alta | WebSocket server/client | Future bidirectional voice/service channel | Approvals/execution over WS sin gates | Adoptar solo cuando haga falta duplex | `websockets` | Remote attack surface | Media | F7/F11 |

### 3.7 Desktop daemon / tray / packaging

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `tauri-apps/tauri` | https://github.com/tauri-apps/tauri | Rust, system WebView, TS | Alta | Desktop/mobile shell, tray, updater, native notifications | Tray/orb overlay/kill switch/visible indicator | Rust app before daemon contract | Adopt when desktop shell approved | Rust, Tauri, OS webviews | Build complexity, Rust toolchain | Media-alta | F9 |
| `electron/electron` | https://github.com/electron/electron | Chromium/Node | Muy alta | Cross-platform desktop apps | Fallback if Tauri blocked | Heavy runtime | Avoid unless Tauri impossible | Electron | RAM/bundle/security | Baja-media | F9 alt |
| `moses-palmer/pystray` | https://github.com/moses-palmer/pystray | Python | Media | System tray icons/menu | Lightweight tray for daemon status/stop | Rich desktop UI | Adopt small if Python daemon first | pystray, pillow | OS quirks | Media | F5/F9 |
| `pyinstaller/pyinstaller` | https://github.com/pyinstaller/pyinstaller | Python packaging | Alta | Standalone executables | Local doctor/daemon packaging | Full installer/updater | Evaluate for Windows helper | PyInstaller | AV false positives, size | Media | F9 |

### 3.8 Mobile / remoto / Telegram / trusted devices

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `python-telegram-bot/python-telegram-bot` | https://github.com/python-telegram-bot/python-telegram-bot | Python asyncio | Alta | Telegram Bot API wrapper | Approval previews, challenge, trusted chat | Direct Hermes commands | Reuse gateway direction if license accepted | `python-telegram-bot` | LGPL/GPL concerns, thread safety | Media-alta | F10 |
| `aiogram/aiogram` | https://github.com/aiogram/aiogram | Python asyncio | Alta | Async Telegram framework | Alternative for callbacks/state routers | Second Telegram stack | Evaluate vs existing gateway | `aiogram` | Duplicate platform code | Baja-media | F10 alt |
| `tailscale/tailscale` | https://github.com/tailscale/tailscale | Go, WireGuard | Alta | Private mesh VPN, device identity | Trusted device network for remote JARVIS | Public exposure as default | Recommend over raw public tunnels | Tailscale daemon | Account dependency, network config | Media | F10 |
| `fatedier/frp` | https://github.com/fatedier/frp | Go reverse proxy | Alta | Expose local services behind NAT | Controlled tunnel for self-hosted remote | Unauthenticated public JARVIS | Only behind auth/pairing | frp server/client | Exposes attack surface | Baja-media | F10+ |

### 3.9 Seguridad / policy / sandbox / audit / secrets

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `open-policy-agent/opa` | https://github.com/open-policy-agent/opa | Go, Rego, WASM/REST | Muy alta | General-purpose policy engine | Risk/approval policy-as-code | Reemplazar `ApprovalGateway` | Prototype external policy evaluator | OPA binary/SDK | Rego complexity | Alta | F11 |
| `cedar-policy/cedar` | https://github.com/cedar-policy/cedar | Rust policy language | Alta | Authorization policy language | Explicit allow/forbid/action/resource model | Full AWS-style auth model now | Study for policy DSL shape | Rust/Cedar libs | Rust/tooling, learning | Media | F11 |
| `containers/bubblewrap` | https://github.com/containers/bubblewrap | C, Linux namespaces/seccomp | Alta | Unprivileged sandboxing | Local command sandbox behind Hermes | Windows/WSL universal solution | Adopt Linux-only later | system package | Wrong args = weak sandbox | Media-alta | F12 |
| `google/nsjail` | https://github.com/google/nsjail | C++, namespaces/cgroups/seccomp | Alta | Process isolation jail | Stronger execution sandbox for risky commands | Everyday desktop UX | Evaluate for Linux backend | nsjail binary | Privileges, OS variance | Media | F12 |
| `google/gvisor` | https://github.com/google/gvisor | Go, application kernel | Alta | Container isolation | Defense-in-depth for container executor | Local lightweight default | Later for container env | Docker/containerd | Heavy ops | Baja-media | F12+ |
| `firecracker-microvm/firecracker` | https://github.com/firecracker-microvm/firecracker | Rust/KVM microVM | Alta | Secure microVMs | Future high-risk sandbox | Desktop default | Not now; architecture reference | KVM/Linux | Too heavy, WSL issues | Baja | F12+ |
| `codenotary/immudb` | https://github.com/codenotary/immudb | Go, immutable DB | Media-alta | Tamperproof DB/history | Audit ledger for approvals/sensors/execution | Replace SQLite entirely | Evaluate or reimplement hash-chain SQLite | immudb server | Another service | Media | F11 |
| `sigstore/rekor` | https://github.com/sigstore/rekor | Go, transparency log | Alta | Tamper-resistant metadata log | Audit design/proofs | Public log for private data | Reference or local-only later | Rekor/Trillian | Privacy, ops | Media | F11 |
| `google/trillian` | https://github.com/google/trillian | Go, verifiable log | Alta | Cryptographic append-only log | Merkle audit model | Operate full log now | Reference | DB/server | Operational load | Baja-media | F11+ |
| `trufflesecurity/trufflehog` | https://github.com/trufflesecurity/trufflehog | Go | Alta | Finds/verifies leaked secrets | Preflight before deploy/publish/send | Uploading secrets to external services | Optional local check | trufflehog binary | False positives, runtime cost | Alta | F11 |
| `Yelp/detect-secrets` | https://github.com/Yelp/detect-secrets | Python | Alta | Prevent/detect secrets in code | Lightweight local preflight | Treat as complete DLP | Adopt candidate | Python package | Baseline management | Media-alta | F11 |
| `semgrep/semgrep` | https://github.com/semgrep/semgrep | OCaml/Python | Alta | Static pattern analysis | Dangerous code/command policy checks | Full SAST in first pass | Optional ruleset | semgrep | Noise | Media | F11 |
| `koalaman/shellcheck` | https://github.com/koalaman/shellcheck | Haskell | Alta | Shell script linting | Detect dangerous shell patterns before Hermes runs scripts | Security classifier alone | Use in doctor/preflight | shellcheck binary | False assurance | Media | F11 |

### 3.10 Agentes / automatizacion / browser computer use

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `microsoft/playwright` | https://github.com/microsoft/playwright | TS/JS/Python/Java/.NET | Alta | Browser testing/automation | Visual verification, governed browser adapter | Autonomous execution from UI | Already aligned with Hermes tools | browsers | Credentials/session leakage | Alta | F12 |
| `browser-use/browser-use` | https://github.com/browser-use/browser-use | Python, browser agent | Alta emergente | AI browser automation | Patterns for page state/actions | Direct web agent runtime | Reference/adapt under Hermes only | Playwright/LLM | Bypass approvals | Media | F12 |
| `Skyvern-AI/skyvern` | https://github.com/Skyvern-AI/skyvern | Python/TS, browser workflows | Alta emergente | AI browser workflows | Durable browser task patterns | Full external platform | Reference for workflow audit | many | Side effects on websites | Media | F12 |
| `langchain-ai/langgraph` | https://github.com/langchain-ai/langgraph | Python, agent orchestration | Alta | Stateful/durable human-in-loop agents | Human-in-loop/state checkpoints patterns | Replacing Hermes loop | Reference only unless mission loop needs durability | LangGraph | Duplicate agent runtime | Media | F13 |

### 3.11 Doctor / installer / observability / other operations

| Nombre | URL | Stack | Madurez | Que hace | Nos interesa | No interesa | Conviene | Dependencias | Riesgos | Prioridad | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `giampaolo/psutil` | https://github.com/giampaolo/psutil | Python/C | Alta | Process/system metrics | Doctor: CPU, RAM, processes, ports, battery | Background monitoring without opt-in | Adopt for doctor/daemon | `psutil` | Platform differences | Alta | F1/F9 |
| `Textualize/rich` | https://github.com/Textualize/rich | Python | Alta | Terminal formatting | Doctor CLI output | New UI framework | Already repo uses Rich; reuse | rich | None material | Media | F1 |
| `tiangolo/typer` | https://github.com/fastapi/typer | Python CLI | Alta | CLI apps with type hints | Doctor/install subcommands | Rewrite CLI now | Evaluate for new doctor commands only | typer | CLI inconsistency | Baja-media | F9 |
| `open-telemetry/opentelemetry-python` | https://github.com/open-telemetry/opentelemetry-python | Python | Alta | Traces/metrics/logs standard | Local observability for daemon/Hermes bridge | Sending telemetry externally | Local/export opt-in only | OTel SDK | Privacy, overhead | Media | F13 |
| `prometheus/client_python` | https://github.com/prometheus/client_python | Python | Alta | Metrics endpoint/client | Local health/perf metrics | Public metrics endpoint | Optional local-only metrics | prometheus client | Leaking env/status | Media | F13 |
| `temporalio/sdk-python` | https://github.com/temporalio/sdk-python | Python, Temporal | Alta | Durable workflows | Long-running governed missions later | New execution runtime now | Reference/later only | Temporal server | Duplicates mission executor | Baja-media | F13+ |

## 4. Gap analysis ampliado de JARVIS

| Area | Que tenemos | Que existe fuera | Que falta | Que adoptar | Prioridad | Fase |
|---|---|---|---|---|---|---|
| UI 3D/HUD | `JarvisOrb3D` WebGL manual, Presence UI componentizada | R3F/Drei/postprocessing, OpenClaw HUD, perf monitors | R3F scene, bloom, instancing, screenshot/FPS checks | R3F + Drei + postprocessing + perf budget | Alta | F2 |
| Voz manual | Browser SpeechRecognition/TTS, `useLocalVoiceLoop` | faster-whisper, whisper.cpp, Piper, Wyoming, VAD | Backend VoiceSession, local providers, cancel/ducking | VAD + provider interfaces, Piper/faster-whisper opt-in | Alta | F4 |
| Wake | `RealWakeListener` adapter contract only | openWakeWord, OVOS hotword patterns | Daemon opt-in, buffer ephemeral, false-positive tests | openWakeWord spike after sensor ledger | Alta | F5 |
| Audio bruto | Local MediaRecorder in browser, blob memory/download/delete | idb/Dexie retention stores | Persistent retention policy, purge ledger | idb only if storage approved | Media-alta | F3 |
| Camara/vision | Browser camera preview opt-in, no backend stream | MediaPipe, TFJS, OpenCV | Local analysis scope, redaction, no person identity default | MediaPipe tasks only in separate PR | Media | F6 |
| Memoria | outcome/learning/personal memory, visible brain read-only | Graphiti, mem0, Chroma, jarvis-orb | Provenance, contradiction lifecycle, forget/compact workflow | SQLite temporal facts first; Graphiti model later | Alta | F8 |
| Event bus | Read-only event snapshot/SSE endpoints | sse-starlette, WS libraries | Robust disconnect/ping/backpressure/schema versioning | sse-starlette if current SSE grows | Alta | F1 |
| Desktop daemon/tray | `DesktopRuntime` control plane, local daemon docs | Tauri, pystray, PyInstaller | Tray indicator, stop/kill, service install | pystray for daemon MVP, Tauri later | Media-alta | F5/F9 |
| Mobile/Telegram | Gateway exists, mobile companion preview | PTB/aiogram, Tailscale/frp | Pairing, revocation, trusted devices, challenge approvals | Existing gateway + PTB patterns, Tailscale preferred | Media | F10 |
| Security policy | Regex `PolicyEngine`, `ApprovalGateway` | OPA, Cedar, Semgrep, secret scanners | Policy-as-code, preflight before risky actions | OPA/Cedar prototype; TruffleHog/detect-secrets | Alta | F11 |
| Sandbox | Hermes envs, terminal approvals, local safety docs | bubblewrap, nsjail, gVisor, Firecracker | OS-level isolation profile per risk | bubblewrap/nsjail Linux-only later | Media-alta | F12 |
| Audit | Approval/audit modules, event timeline | immudb, Rekor, Trillian | Hash-chain/tamper evidence, sensor ledger | SQLite hash-chain first, immudb later | Alta | F1/F11 |
| Browser automation | Hermes browser tools and tests | Playwright, browser-use, Skyvern | Approval-bound browser workflows and screenshots | Playwright verification first; browser-use reference | Alta | F12 |
| Doctor/installer | Local doctor read-only and Hermes CLI doctor patterns | psutil, PyInstaller, Tauri updater | Device checks, ports, browser capabilities, model cache checks | psutil, platform-specific checks | Alta | F1/F9 |
| Performance | Power-save contract, WebGL fallback | R3F Perf, Drei adaptive DPR, stats.js | FPS budget, nonblank canvas tests, mobile profile | Drei PerformanceMonitor/dev perf | Media | F2/F8 |
| Observability | Status/read models, tests | OpenTelemetry/Prometheus | Runtime traces/metrics local-only | optional local metrics later | Media | F13 |

## 5. Capacidades nuevas que no estaban en el informe anterior

1. Policy-as-code: OPA/Cedar como evaluador declarativo de riesgo y aprobacion.
   Mantiene `ApprovalGateway` como puerta, pero externaliza reglas para evitar
   regex crecientes e inconsistentes.
2. Sensor ledger backend: no basta con metadata local visible. Camara, wake,
   grabadora, STT y TTS deben registrar start/stop/error/retention/delete sin
   audio ni frames.
3. Tamper-evident audit: hash-chain SQLite como primer paso; immudb/Rekor/
   Trillian solo si se necesita verificacion fuerte.
4. Secret and side-effect preflight: antes de deploy/email/publish/browser form,
   ejecutar detection local de secretos y clasificar side effects.
5. Sandbox profiles por riesgo: lectura local sin sandbox fuerte; comandos con
   write/network bajo perfiles; acciones criticas requieren sandbox + approval +
   rollback.
6. Temporal memory graph: facts con `valid_from`, `superseded_at`, provenance,
   confianza, contradiccion y explicacion de influencia.
7. Durable mission checkpoints: patrones LangGraph/Temporal solo como referencia
   para misiones largas; no se reemplaza Hermes.
8. Trusted device mesh: Tailscale/pairing/revocation como capa para remoto antes
   de exponer cualquier dashboard o Telegram approval.
9. Desktop visible control: tray siempre visible para listening/recording/
   executing, stop global y kill switch.
10. Local observability: metrics/traces locales para saber si JARVIS esta
    escuchando, hablando, pensando, esperando aprobacion o ejecutando.
11. Browser automation with approval envelopes: browser-use/Skyvern solo sirven
    si sus acciones se convierten en candidatos Hermes con readback.
12. WebGL verification pipeline: Playwright screenshot + canvas-pixel checks +
    FPS sanity antes de aceptar el orbe 3D.

## 6. Plan por fases actualizado

### Fase 0 - Mantener contrato y estabilizar informe

- Objetivo: dejar claro que la adopcion externa no crea otro Hermes.
- Entrega: este documento y decisiones de David.
- Dependencias: ninguna.
- Criterio: plan aprobado, sin codigo.

### Fase 1 - Operability baseline sin dependencias pesadas

- Implementar sensor ledger backend para camara/grabacion/wake/voice sessions:
  metadata only, retention/delete, no raw audio ni frames.
- Fortalecer event stream con schema version, heartbeat/disconnect y tests.
- Ampliar doctor local: audio devices detectable, browser support, ports,
  optional deps, GPU/CPU/memory, model cache, WebGL status client-side.
- Candidatos: `sse-starlette`, `psutil`, reuse Rich.
- No activar wake ni STT/TTS backend todavia.

### Fase 2 - Orbe 3D real con performance budget

- Adoptar `three`, `@react-three/fiber`, `@react-three/drei`,
  `@react-three/postprocessing` si David aprueba.
- Orbe state-driven desde event stream, fallback WebGL manual o static.
- Verificacion: Playwright screenshot, canvas nonblank, desktop/mobile layout,
  FPS/power-save sanity.
- No sensor/audio capture nuevo.

### Fase 3 - Audio bruto local persistente opcional

- Mantener grabadora separada de voz conversacional.
- Si David aprueba persistencia: `idb` para IndexedDB, retencion, purge,
  export, audit ledger.
- Default: no persistir, no backend upload.

### Fase 4 - Voice Session Manager + STT/TTS local opt-in

- Backend `VoiceSession`: active, timeout, interrupt, cancel, transcript
  lifecycle, confidence, readback.
- VAD con Silero como provider opcional.
- STT con faster-whisper/whisper.cpp despues de activacion manual.
- TTS con Piper provider y browser fallback.
- No wake always-on todavia.

### Fase 5 - Wake daemon seguro

- openWakeWord opt-in desde daemon/tray, indicador visible, stop global.
- Buffer circular en memoria, no persistencia, no STT hasta wake valido.
- Wake abre sesion; wake nunca aprueba ni ejecuta.
- Tests de falsos positivos/negativos y audit events.

### Fase 6 - Vision local opt-in

- MediaPipe task preview solo tras camara manual.
- Scope visible: gesture/object/document; no identity/person analysis default.
- No frames backend, no snapshots automaticos, stop visible.
- Redaction/blur opcional antes de cualquier analisis persistente.

### Fase 7 - Voice services / multi-device voice protocol

- Evaluar Wyoming si hay satellites/servicios de voz locales.
- Mantener JARVIS como controlador de sesion; servicios solo transcriben/sintetizan.
- No skill runtime externo.

### Fase 8 - Memory brain v2

- SQLite temporal facts primero: entities, facts, decisions, preferences,
  contradictions, provenance, `superseded_at`, `verified_by`, `sensitivity`.
- UI: "por que JARVIS recuerda esto", forget/delete, compaction proposals.
- Graphiti/mem0 como referencia/eval, no dependencia obligatoria inicial.

### Fase 9 - Desktop daemon/tray/install

- Tray: visible listening/recording/executing, stop/cancel/kill.
- Service install/uninstall/doctor for Windows/macOS/Linux.
- pystray/PyInstaller for MVP or Tauri for richer shell after approval.

### Fase 10 - Remote/mobile/Telegram governed channels

- Pairing, trusted device registry, revocation, challenge.
- Telegram can request/preview/approve only through JARVIS gates.
- Tailscale preferred for private access; frp only with explicit auth threat model.
- Remote never calls Hermes directly.

### Fase 11 - Policy, audit and preflight hardening

- OPA/Cedar prototype for risk/approval policy.
- TruffleHog/detect-secrets/Semgrep/ShellCheck preflight for dangerous classes.
- Tamper-evident audit: SQLite hash-chain first; immudb/Rekor/Trillian later.
- Every dangerous execution: risk class, approval id, readback, rollback/stop,
  audit id.

### Fase 12 - Governed browser/computer automation

- Playwright verification and browser tasks as Hermes adapters.
- browser-use/Skyvern patterns only for candidate generation and observability.
- All form submits, purchases, emails, deploys, account changes need approval.

### Fase 13 - Durable missions and observability

- Study LangGraph/Temporal only for checkpoints/human-in-loop patterns.
- Local OpenTelemetry/Prometheus optional, no external telemetry by default.
- Avoid replacing Hermes execution loop.

## 7. Primera fase recomendada

Primera fase real: **Fase 1 - Operability baseline sin dependencias pesadas**.

Motivo: el repo ya tiene camara local, grabacion local, event stream, brain y
doctor. Antes de meter R3F, wake o STT local, hay que cerrar la auditoria
persistente y la operabilidad minima:

- sensor ledger backend para start/stop/error/delete;
- event stream robusto y versionado;
- doctor local con checks reales de puertos, procesos, dependencias opcionales,
  browser capabilities y model cache;
- policy status visible: que puede hacer JARVIS, que prepara, que requiere
  approval y que esta bloqueado.

Dependencias candidatas de Fase 1:

- `psutil` para doctor local.
- `sse-starlette` solo si el SSE manual empieza a crecer o necesita backpressure.
- Ninguna dependencia 3D, voz, wake, vision o sandbox todavia.

## 8. Que no tocar todavia

- No activar wake daemon real antes de sensor ledger + tray/indicator.
- No mover STT/TTS local a default antes de Voice Session Manager.
- No usar MediaPipe/TFJS/OpenCV antes de cerrar policy de camara/vision.
- No persistir audio en IndexedDB por defecto.
- No importar Graphiti/mem0/Chroma como memoria principal todavia.
- No meter OPA/Cedar como requisito hard hasta tener un prototype pequeno.
- No exponer dashboard remoto publico.
- No permitir Telegram approval sin pairing, challenge, scope y audit.
- No usar browser-use/Skyvern como runtime autonomo.
- No meter Firecracker/gVisor/Temporal ahora.
- No aprobar por wake phrase nunca.
- No crear `/execute` ni Hermes directo desde frontend.

## 9. Dependencias candidatas

### Frontend

- Alta prioridad futura: `three`, `@react-three/fiber`,
  `@react-three/drei`, `@react-three/postprocessing`.
- Dev/perf: `r3f-perf` o monitor propio; no visible en produccion.
- Audio storage opcional: `idb` antes que Dexie por simplicidad.
- Vision opcional: `@mediapipe/tasks-vision`; TFJS/OpenCV.js solo por caso.

### Python/backend

- Doctor: `psutil`.
- Event stream: `sse-starlette` si se necesita robustez extra.
- Voice: `silero-vad`, `faster-whisper`, `openwakeword`, Piper provider.
- Telegram: seguir gateway actual; evaluar `python-telegram-bot`/`aiogram`
  solo si el adapter existente no cubre callbacks/challenges.
- Policy/preflight: OPA binary/REST or subprocess; `detect-secrets`;
  optional Semgrep/TruffleHog/ShellCheck.
- Observability: OpenTelemetry/Prometheus solo local y opt-in.

### Sistema

- `ffmpeg` para audio.
- Piper binary/model cache.
- Audio device access and OS permission checks.
- Windows/macOS/Linux service installer strategy.
- Tailscale for private remote mesh if remote is approved.
- bubblewrap/nsjail only for Linux sandbox profiles.

### No candidatas ahora

- ElevenLabs/OpenAI/Gemini voice as default.
- Graph DB server as mandatory memory backend.
- Firecracker/gVisor as local desktop default.
- Temporal as mission runtime.
- Electron unless Tauri/pystray route is rejected.

## 10. Riesgos de seguridad y privacidad

- Sensor confusion: wake, conversation STT and raw recording must be separate
  states with separate controls.
- Audio retention: persistent audio is sensitive even if local; needs purge,
  retention, location visibility and audit.
- Camera biometrics: MediaPipe face/person analysis must be off by default.
- Remote attack surface: Telegram/tunnels can become an execution bypass unless
  every command becomes a JARVIS intent.
- Policy drift: regex classifiers will become fragile; policy-as-code is needed
  before broad execution.
- Sandbox false confidence: bubblewrap/nsjail only protect if profiles are
  correctly generated and tested.
- Memory privacy: automatic memory extraction can store sensitive facts without
  consent; sensitive memory needs approval and provenance.
- Secret leakage: browser automation/deploy/email must run preflight scans before
  execution.
- Audit leakage: audit logs must never store raw audio, frames, secrets or full
  credential paths.
- Desktop daemon trust: tray/daemon must show visible state and expose stop/kill.
- WebGL performance: R3F/bloom/particles can make `/jarvis` unusable on modest
  devices without adaptive DPR and fallback.

## 11. Decisiones pendientes para David

1. Aprobar o rechazar dependencias 3D: `three`, R3F, Drei, postprocessing.
2. Elegir primera voz real: Piper local primero, browser-only por ahora, o API
   premium futura opt-in.
3. Definir si audio bruto persistente se permite; si si, donde, cuanto tiempo y
   como se borra.
4. Priorizar wake vs STT/TTS local vs vision: mi recomendacion es STT/TTS
   manual antes que wake always-on.
5. Decidir si el desktop control sera pystray/Python MVP o Tauri shell.
6. Elegir remoto: solo LAN/local, Tailscale trusted mesh, o tunnel publico con
   hard auth.
7. Confirmar politica de Telegram approvals: riesgos permitidos por voz/chat,
   challenge required y expiracion.
8. Aprobar el modelo de memoria sensible: que categorias requieren approval y
   cuales nunca se guardan.
9. Elegir si policy-as-code debe ser OPA/Rego, Cedar-like DSL, o motor propio.
10. Definir sandbox target inicial: Linux/WSL only, Docker/env existing, o
    esperar.
11. Definir retencion de audit logs y si se requiere tamper-evidence fuerte.
12. Confirmar que browser automation solo llega despues de ApprovalGateway +
    rollback/stop plan.

## 12. Conclusion accionable

La mejor adopcion externa para JARVIS no es una feature vistosa aislada. Es una
secuencia:

1. Cerrar operabilidad y auditoria local.
2. Subir presencia visual con R3F sin sensores nuevos.
3. Formalizar voz local manual.
4. Activar wake solo con daemon/tray/ledger.
5. Consolidar memoria temporal explicable.
6. Endurecer policy/preflight/audit/sandbox.
7. Abrir remoto y automatizacion solo como canales gobernados.

Asi JARVIS se vuelve mas real, escalable y operativo sin perder la ventaja
arquitectonica principal: JARVIS gobierna, Hermes ejecuta.
