# JARVIS handoff context

## 1. Propósito del documento

Este documento es la fuente oficial de handoff para continuar el trabajo de JARVIS en nuevos hilos, nuevas sesiones de Codex o nuevas PRs sin perder contexto operativo.

No es código. No ejecuta nada. No conecta servicios. No cambia runtime, router, endpoints, persistencia ni lógica de JARVIS. Solo documenta el contexto de trabajo, reglas de seguridad, comandos, estado actual y roadmap inmediato.

Debe mantenerse actualizado cuando cambie el flujo de trabajo, el estado real de JARVIS, los comandos locales, las validaciones confirmadas o el roadmap inmediato.

## 2. Identidad del proyecto

Repo:

```text
ceodaradigu/hermes-agent
```

Ruta local principal:

```bash
/mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
```

Worktrees:

```bash
~/jarvis-worktrees/<branch-name>
```

Venv bueno:

```bash
~/venvs/hermes-agent
```

Comando normal de tests:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q
```

Servidor local:

```bash
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

CLI local:

```bash
./scripts/local/voice-runtime-control.sh <command>
```

## 3. Forma de trabajar

Protocolo operativo:

1. Trabajar siempre en una rama/worktree por PR.
2. No tocar `main` directamente.
3. Crear worktree desde `main`.
4. Abrir Codex dentro del worktree.
5. Dar prompt cerrado con objetivo, alcance, prohibiciones, validación y formato de respuesta.
6. Codex no debe hacer commit ni PR salvo instrucción explícita.
7. Validar fuera de Codex con el venv bueno.
8. Si pasa, hacer commit, push y PR con `gh` CLI.
9. Verificar PR.
10. Mergear cuando esté verde.
11. Actualizar `main` local.
12. Eliminar worktree y rama local.
13. Hacer smoke test real si aplica.
14. Limpiar `.jarvis` si se usó memoria local de prueba.
15. Confirmar `git status` limpio.

Comandos base:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent

git checkout main
git pull
git status --short

mkdir -p ~/jarvis-worktrees

git worktree add -b pr-XX-nombre \
  ~/jarvis-worktrees/pr-XX-nombre main

cd ~/jarvis-worktrees/pr-XX-nombre

codex
```

Limpieza:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent

git checkout main
git pull
git status --short

git worktree remove ~/jarvis-worktrees/pr-XX-nombre
git branch -d pr-XX-nombre

git worktree list
git status --short
```

## 4. Reglas de seguridad

- No inventar información.
- No usar APIs externas salvo petición explícita.
- No cambiar CI ni requirements salvo instrucción clara.
- No conectar MissionControl/Hermes runtime salvo PR específica.
- No ejecutar tareas reales.
- No crear misiones reales.
- No autoload.
- No autoejecución.
- No auto-modificación.
- No auto-deploy.
- No instalar dependencias sin aprobación explícita.
- No guardar secretos.
- No mandar memoria privada a servicios externos sin diseño aprobado.
- `PolicyEngine` / sensitive boundary siempre gana.
- Cualquier comando con `.env`, password, token, credenciales, banco o tarjeta debe ir a `requires_approval`.
- JARVIS puede sugerir, preparar, proponer y documentar, pero no debe actuar peligrosamente sin aprobación.

## 5. Estado actual de JARVIS después de Phase S

`JARVIS_MASTER_BUILD_MAP.md` is the source of truth for master phase names and order.

Actualización #157 / Fase 1 base operativa local:

- `/mark-3/dashboard/status` expone `sensor_ledger`, `policy_status`,
  `event_bus` robusto y `local_doctor` ampliado.
- `/mark-3/dashboard/events` y `/mark-3/dashboard/events/stream` son GET
  read-only con `schema_version`, `event_id`, `created_at`, `risk_level`,
  payload seguro y heartbeat. No ejecutan, no aprueban y no transportan audio
  bruto, frames ni secretos.
- Sensor Ledger es metadata-only local/in-memory: soporta `camera`,
  `recording`, `wake`, `voice_session`, `tts`, `stt` y eventos `requested`,
  `started`, `stopped`, `cancelled`, `failed`, `deleted`,
  `retention_updated`.
- Doctor local declara backend/frontend esperado, stream, Hermes, deps
  opcionales, Python, plataforma, proceso/psutil opcional, puertos esperados y
  capacidades browser-only como `client_side_unknown`, sin activar sensores.
- `/jarvis` muestra Sensor Ledger, Doctor Local, Event Stream Health y Policy
  Status en el drawer `Sistemas`.
- Sigue prohibido añadir `/execute`, frontend directo a Hermes, POST/PUT/DELETE
  peligrosos, wake phrase como approval o sensores sin opt-in visible y
  stop/cancel.

Actualización #157 / Fase 2 orbe 3D real:

- `/jarvis` tiene un orbe WebGL manual reforzado: partículas orbitando, anillos
  radiales, marcas holográficas, profundidad, glow/bloom simulado, ondas por
  estado y HUD cinematográfico.
- Estados visuales soportados: `idle`, `wake_listening`, `listening`,
  `transcribing`, `thinking`, `speaking`, `alert`, `error`, `stopped`,
  `executing`.
- Performance budget integrado: `targetFrameMs`, `particleBudget`,
  `prefers-reduced-motion`, pixel ratio limitado y fallback visible si
  WebGL/canvas falla.
- No se añadieron dependencias frontend. No se activaron sensores nuevos, cámara
  nueva, micrófono nuevo, grabación nueva, wake real, STT/TTS local, remoto ni
  ejecución Hermes.
- Si en una fase futura se migra a R3F/Three, debe mantenerse fallback,
  screenshot/browser verification y no introducir APIs de sensor en el orbe.

Actualización #157 / Subfase Conversational Brain Bridge + vídeo local:

- `/jarvis` ya no responde sólo repitiendo la transcripción. El fallback local
  `buildLocalJarvisResponse` clasifica intención básica y responde de forma
  breve: preguntas simples, estado/capacidades, previews de misión/tarea/activo,
  acciones sensibles y aclaración cuando no entiende.
- No hay LLM externo ni API nueva. Es un bridge conversacional local y
  determinista; la integración futura con LLM/Hermes debe entrar por ruta
  gobernada, con risk classification, ApprovalGateway, audit y rollback/stop.
- La smart bar muestra la respuesta humana en primer plano y deja el debug
  plegado como `intent_detected`, `risk_level`, `requires_approval`,
  `can_prepare_preview`, `cannot_execute_reason` y
  `suggested_next_action`.
- Acciones de credenciales/secretos se bloquean; wake phrase sigue sin aprobar;
  frontend no ejecuta Hermes y no existe `/execute`.
- Cámara local ahora incluye grabación de vídeo opt-in: botón separado
  `Grabar vídeo`, permiso navegador, indicador `REC local`, stop, descarga de
  blob local y borrado/revocación. No graba al cargar, no sube vídeo al backend,
  no hace streaming externo, no captura snapshot automático y no analiza
  personas/identidad.
- Read model/event stream declaran `browser_local_video_recorder` inactivo por
  defecto y metadata-only. Sensor Ledger/read model declara metadata segura de
  audio/vídeo, y el event stream añade overlay local `sensor_ledger_state` para
  sesiones del navegador sin POST de media al backend, audio bruto, frames ni
  secretos.

Actualización #159 / Fase 1 Conversational Intake + LLM Brain Adapter:

- Existe `ConversationalIntakePipeline` en `jarvis/conversational_intake.py`.
  Normaliza texto escrito, transcripción de voz, comando futuro tras wake phrase
  e input remoto futuro en un `ConversationalIntake` serializable.
- El intake separa recibir texto, normalizar, detectar wake phrase, detectar
  material sensible, clasificar intención/riesgo, preparar preview y declarar
  `safe_to_dispatch_to_hermes=false`.
- Existe `LLMBrainAdapter` en `jarvis/llm_brain_adapter.py` con contratos
  `BrainRequest`, `BrainResponse` y `BrainProviderStatus`.
- Provider actual por defecto: `deterministic_local`, usando el bridge local
  existente. Provider externo visible: `disabled_external_llm`, deshabilitado
  por defecto.
- No hay LLM externo real, no hay red, no se lee `.env`, no se leen variables
  secretas, no se guardan prompts privados y no se despacha Hermes.
- `/mark-3/dashboard/status` expone `conversational_intake` y `brain_adapter`.
  `/mark-3/dashboard/events` y `/stream` exponen `intake_state` y
  `brain_adapter_state` solo con metadata segura.
- `/jarvis` muestra provider actual, external called false y riesgo de intake
  de forma compacta; los detalles técnicos quedan plegados.
- Local Voice Loop puede usar la respuesta del intake/brain en modo
  prepare-only sin perder el bloqueo de credenciales introducido en #158.

Actualización #163 / Fase 1 Voice Runtime Pack:

- Existe `VoiceRuntimePack` en `jarvis/voice_runtime_pack.py` con
  `schema_version=jarvis.voice_runtime_pack.v1` y endpoint GET
  `/mark-3/voice-runtime/status`.
- El pack declara sesion de voz manual/local, `manual_push_to_talk_enabled=true`,
  estados `idle/listening/transcribing/thinking/speaking/cancelled/stopped/error/
  approval_required/wake_listening_available/wake_listening_disabled`, provider
  contracts STT/TTS y lifecycle de transcript/TTS.
- Browser STT/TTS se declaran client-side (`client_side_unknown` en backend);
  providers locales futuros `faster_whisper_disabled_or_missing`,
  `whisper_cpp_disabled_or_missing` y `piper_local_disabled_or_missing` quedan
  `enabled=false`, sin instalar dependencias ni descargar modelos.
- `/mark-3/dashboard/status` expone `voice_runtime_pack`; `/mark-3/dashboard/events`
  y `/stream` exponen `voice_runtime_state`; Local Doctor marca
  `voice_runtime_pack_endpoint=true`, `no_voice_provider_install=true` y
  `no_voice_model_download=true`.
- `/jarvis` mejora el Local Voice Loop: stop/cancel visible, interrupt de TTS,
  cola corta `speechSynthesis`, filtro de posible eco y estados visuales
  `cancelled/stopped` mapeados a esfera calmada.
- Siguen falsos por defecto: `raw_audio_sent_to_backend=false`,
  `transcript_persistence=false`, `voice_approval_enabled=false`,
  `wake_phrase_can_approve=false`, `wake_phrase_can_execute=false` y
  `hermes_dispatch_allowed=false`.

Actualización #160 / Fase 1 Presence UI real + 3D Orb/HUD adoption:

- `/jarvis` pasa a Presence UI orb-first: header reducido, nucleo central
  dominante, laterales minimos, panel derecho contextual, smart bar inferior y
  detalles tecnicos plegados en `Sistemas`/`details`.
- `JarvisOrb3D` sigue en WebGL manual, sin dependencias nuevas. Añade estado
  `approval_required`, marcas de performance budget, anillos/glow extra,
  `motion-reduce`, fallback visible sin WebGL/canvas y pixel ratio limitado.
- Smart bar acepta borrador local de texto, muestra transcripcion/respuesta
  humana corta y deja intent/risk/debug plegado. El boton enviar sigue
  deshabilitado; no hay POST, `/execute` ni Hermes dispatch.
- Camara lateral queda como modulo premium opt-in y ampliable. No arranca al
  cargar, no sube video, no envia frames y no añade vision analysis.
- Repos externas revisadas y documentadas en
  `docs/jarvis-pr-160-presence-ui-real-3d-orb-hud-adoption.md`; todo lo tomado
  fue reimplementacion visual/conceptual, no copia de runtimes.
- Recomendacion original posterior: Presence verification and visual QA con
  screenshots/browser checks, canvas no blanco y medicion de frame budget. #161
  se uso antes para la remodelacion visual v2; esa QA queda recomendada como
  #162.

Actualización #161 / Fase 1 Presence UI Visual Overhaul v2 + Audio-Reactive Orb:

- #161 corrige la direccion visual de #160 porque el resultado anterior seguia
  demasiado uniforme: fondo, halo, particulas y nucleo compartian demasiado cian
  y los laterales seguian leyendo como dashboard.
- `/jarvis` ahora usa fondo mucho mas oscuro (`#00030a`), halo exterior mas
  contenido, particulas cian/turquesa frias y nucleo azul-blanco diferenciado
  (`#e6fbff`) con `coreGlow`/`jarvis-core-breathe`.
- `JarvisOrb3D` añade contrato visual testeable:
  `data-visual-layering`, `data-voice-reactive-mode`,
  `data-orb-reactive-states`, `data-testid="jarvis-distinct-core"`.
- `useJarvisOrbState` añade `stateReactiveEnergy`, `coreColor`, `coreGlow` y
  `outerGlow`; el shader WebGL usa `u_reactivity` para que idle/listening/
  transcribing/thinking/speaking/approval/error/stopped se sientan distintos.
- La reactividad es state-driven y usa señales ya disponibles. No abre Web
  Audio, no captura amplitud nueva, no auto-activa micro/camara y no envia audio
  ni frames.
- Laterales, approvals, camara, audio bruto y finance quedan mas discretos y
  premium mediante paneles plegados/minimos. Smart bar sigue siendo el centro de
  interaccion humana, con respuesta/transcripcion visibles y detalles plegados.
- No se añadieron dependencias. Se revisaron repos externas y se documento todo
  en `docs/jarvis-pr-161-presence-ui-visual-overhaul-v2-audio-reactive-orb.md`.
- Siguiente PR recomendada: #162 Presence Visual QA + Browser Verification con
  screenshots desktop/mobile, canvas nonblank, fallback WebGL y medicion simple
  de frame budget.

Actualización #162 / Fase 1 Particle Sphere Motion Polish + Visual QA:

- #162 corrige el visual central despues de #161: la esfera ya no debe leerse
  como nucleo fijo, logo, placa, reactor circular ni HUD tecnico. Es una nube
  viva de particulas Canvas 2D, blanco frio/azul hielo, con aire, profundidad y
  variacion de tamano/opacidad.
- `JarvisOrb3D` usa 2600 particulas precomputadas, distribucion volumetrica,
  centro emergente por concentracion y fallback CSS de particulas si Canvas 2D
  falla. El error tecnico queda en `data-canvas-error`, no como mensaje visible.
- Estados pulidos: idle respira y casi no tiene centro; listening se contrae y
  tensa; transcribing reorganiza; thinking genera turbulencia/remolinos;
  speaking usa pseudo-audio determinista local con picos/ondas radiales;
  alert/error expanden mas agresivo; stopped se reduce y atenua.
- Visual QA local: drawer `Sistemas` incluye controles para Auto, Idle,
  Listening, Transcribing, Thinking, Speaking, Alert y Stopped. Tambien se puede
  abrir con `?jarvisVisualPreview=speaking`. No llama Hermes, no aprueba, no
  activa micro/camara, no abre Web Audio y no toca backend de ejecucion.
- Laterales, smart bar, camara, approvals, audio bruto local, finance plegado y
  drawers se mantienen. La zona central queda limpia.
- No se añadieron dependencias ni se copio codigo externo. Repos y licencias
  documentadas en
  `docs/jarvis-pr-162-particle-sphere-motion-polish-visual-qa.md`.
- Siguiente PR recomendada: #163 Visual Browser Verification con screenshots
  desktop/mobile, canvas no blanco/no negro, fallback, reduced motion y firmas
  visuales diferenciadas por estado.

Estado alineado de las fases maestras:

| Fase maestra | Estado actual |
|---|---|
| Phase A-Phase S | Cerradas como foundations del mapa maestro actual. |
| Phase S — Future/Moonshot Layer | Última fase maestra implementada; no existe Phase T aprobada. |

Operator Console Foundation está completada como extensión read-only de Command Center / operator layer. No es Phase G maestra y no sustituye Ambient Vision / Camera Companion.

El cierre de Phase A-Phase S no activa capacidades runtime/producción reales. Los trabajos posteriores son backlog transversal/no-fase y deben mantener prepare-only, approvals, strong approval, privacidad, auditoría y rollback según aplique.

Ya existe:

- Runtime local de voz/control.
- Feedback de entendimiento.
- Proposals de memoria.
- Snapshot JSON en memoria.
- `save-local` explícito.
- `load-local` explícito.
- Local status/backup/delete.
- Activation explícita de memoria aprobada.
- Quickstart local de memoria.
- Continuous learning system design.
- Principio de interacción natural.
- Contratos documentales mergeados para Hermes inside JARVIS, deployment modes, mobile voice approval, restriction registry, CodeGraph evaluation, Home / Voice / Sensor Hardware Layer, Personal OS / Environment Intelligence, Distributed Personal OS Capabilities, Authorized Security Research / Bug Bounty Mode, Personal Memory / User Model Layer, Core Intelligence / Personal Memory Backlog, Developer / Stark Workshop Layer, Personal Knowledge / RAG Layer y Mission Autonomy / Self-Improvement / Revenue Execution.

JARVIS puede:

1. Crear proposal desde feedback.
2. Guardar proposal en `.jarvis` con `memory-save-local`.
3. Cargar proposal desde `.jarvis` con `memory-load-local`.
4. Revisarla con `memory-review`.
5. Aprobarla con `memory-approve`.
6. Activarla explícitamente con `memory-activate`.
7. Cambiar clasificación de transcript durante la sesión.
8. Revertir con `memory-deactivate` o `memory-active-clear`.
9. Proteger sensitive boundary con `requires_approval`.
10. Limpiar runtime/local memory.

JARVIS aún NO debe:

1. Autocargar memoria.
2. Activar memoria automáticamente.
3. Ejecutar tareas reales.
4. Crear misiones reales.
5. Saltarse `ApprovalGateway`.
6. Usar frases rígidas predeterminadas como personalidad.
7. Auto-modificarse.
8. Instalar dependencias solo.
9. Hacer deploy solo.

PR #70 está mergeado y es la primera PR de código real posterior a esa fase documental general: introduce Mission Envelope v1 como contrato Python validable y testeado, sin planner, ejecución real, endpoints, tool adoption ni conexión nueva con Hermes/MissionControl.

PR #71 está mergeado e introduce Mission Approval Request v1: una solicitud de aprobación clara, auditable y limitada derivada de `MissionEnvelope` + acción propuesta, sin ejecutar acciones reales.

PR #72 está mergeado e introduce Mission Audit Log v1: eventos auditables, serializables y validables para misiones JARVIS, sin persistencia, runtime, endpoints ni conexión con Hermes/MissionControl.

PR #73 está mergeado e introduce Mission State Store v1: estado mínimo serializable y validable para agrupar envelope, approvals, audit events y status, con store en memoria sin persistencia real.

PR #74 está mergeado e introduce Mission Lifecycle Validator v1: validación declarativa de transiciones entre estados de misión, sin mutar estado, ejecutar acciones, persistir ni conectar runtime.

PR #75 está mergeado e introduce Mission Command Builder v1: comando preparado serializable y validable desde `MissionState` + acción + contexto opcional, sin ejecutar, persistir ni conectar runtime.

PR #76 está mergeado e introduce Mission Dry-Run Evaluator v1: evaluación serializable y validable de un `MissionCommand` preparado antes de cualquier ejecución futura, sin ejecutar, persistir ni conectar runtime.

PR #77 está mergeado e introduce Mission Snapshot Serializer v1: snapshot serializable y validable de `MissionState`, comandos preparados y dry-runs, sin escribir archivos, persistir, ejecutar ni conectar runtime.

PR #78 está mergeado e introduce JARVIS Master Build Map: mapa maestro documental para construir JARVIS por fases sin olvidar Hermes, Command Center, voz, móvil, cámara, multi-dispositivo, approvals, ejecución, herramientas, asset factory, publicación, ventas, pagos, scheduler y monetización, sin implementar código.

PR #79 está mergeado e introduce Mission Approval Bridge v1: payload prepare-only que conecta `MissionState`, `MissionCommand` y `MissionDryRunEvaluation` con una futura solicitud de aprobación humana, sin aprobar, ejecutar, llamar `ApprovalGateway`, conectar Hermes/MissionControl ni mutar estado.

PR #80 está mergeado e introduce Mission Safety Baseline Gate v1: evaluación prepare-only de riesgos de misión antes de cualquier ejecución futura, sin aprobar, ejecutar, llamar `ApprovalGateway`, conectar Hermes/MissionControl ni mutar estado.

PR #81 está mergeado y completa Phase B — Approval & Safety Bridge: Mission Policy Bridge v1, Mission Budget Guard v1, Approval Payload Hardening v1 y Legal/AI Content Safety Baseline v1, manteniendo alcance prepare-only y sin ejecución real.

PR #82 está mergeado y completa la foundation contractual de Phase C — Hermes Runtime Bridge en modo prepare-only, sin ejecutar Hermes, conectar MissionControl, llamar ApprovalGateway ni crear runtime activo.

PRs #93 y #94 están mergeadas y completan la foundation de Phase D — Command Center con view model y API read-only, sin UI visual completa ni acciones de ejecución/aprobación.

PRs #95, #96 y #97 están mergeadas y completan la foundation de Phase E — Voice Companion en modo prepare-only, sin activar micrófono, wake word, grabación, streaming ni ejecución.

PR #98 está mergeado y completa la foundation de Phase F — Mobile Companion en modo prepare-only, sin app móvil, pairing, push, background sync ni acciones remotas reales.

PR #99 está mergeado y completa Operator Console Foundation como extensión read-only de Command Center / operator layer. No es una Phase G maestra ni sustituye Ambient Vision / Camera Companion.

Phase S — Future/Moonshot Layer foundation prepare-only está completada. Es la última fase maestra implementada del mapa actual.

No existe una siguiente fase maestra aprobada. Para el backlog seguro posterior a Phase S, ver `docs/JARVIS_MASTER_BUILD_MAP.md`.

## 6. Validaciones reales ya confirmadas

Flujo de activación:

- Antes de `memory-activate`:
  transcript `"monta algo para probar este nicho"` => `create_asset`
- Después de `memory-activate`:
  transcript `"monta algo para probar este nicho"` => `create_mission`
- Con `.env`:
  transcript `"monta algo para probar este nicho y lee mi .env"` => `requires_approval`
- Después de `memory-deactivate`:
  vuelve a `create_asset`

Flujo local:

- `save-local` guarda snapshot explícitamente.
- `clear runtime` borra proposals del proceso.
- `load-local` recupera proposals desde `.jarvis`.
- `load-local` NO activa runtime.
- `review` + `approve` NO activa runtime por sí solo.
- `memory-activate` SÍ cambia clasificación durante la sesión.
- `memory-active-clear` y `memory-clear` limpian.
- `git status` queda limpio tras `rm -rf .jarvis`.

## 7. Principio de interacción natural

David no quiere que JARVIS use frases predeterminadas rígidas.

JARVIS debe:

- Responder dinámicamente según contexto.
- Usar memoria activa.
- Entender intención.
- Considerar riesgo.
- Priorizar negocio y monetización.
- Sonar como operador vivo, no bot de menú.
- Tener criterio.
- Tener iniciativa supervisada.
- Poder decir "no" si algo no monetiza o distrae.
- Adaptar tono según situación: directo, estratégico, técnico, cauteloso, urgente o contrarian.
- Evitar respuestas vacías tipo "Entendido" si puede aportar algo útil.
- Explicar cuando necesita aprobación.
- Respetar `PolicyEngine`, `ApprovalGateway` y límites sensibles.

Definición:

"Vida propia" significa criterio contextual e iniciativa supervisada, no autoejecución peligrosa.

Ejemplo malo:

> "Entendido. Procesando solicitud."

Ejemplo mejor:

> "Esto suena a validación de nicho, no a crear una landing todavía. Te propongo abrir una misión de validación primero y dejar la landing para cuando tengamos señal."

## 8. Continuous Learning System

JARVIS debe mantenerse al día con novedades tecnológicas, pero no auto-modificarse en silencio.

Flujo:

```text
investigar -> filtrar -> resumir -> proponer -> pedir aprobación -> crear issue/plan/PR -> pasar tests -> documentar aprendizaje -> aplicar solo tras merge
```

Componentes futuros:

- Tech Radar Agent.
- Relevance Filter.
- Contrarian Review.
- Learning Proposal.
- Approval Workflow.
- Implementation Planner.
- Test and Rollback Gate.
- Memory/Roadmap Update.

Regla:

Continuous Learning no significa auto-update, auto-deploy, auto-modificación ni instalación automática de dependencias.

## 9. Comandos útiles actuales

Estado:

```bash
./scripts/local/voice-runtime-control.sh status
```

Memoria proposals:

```bash
./scripts/local/voice-runtime-control.sh memory-proposals
./scripts/local/voice-runtime-control.sh memory-proposal "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-propose-from-feedback ...
./scripts/local/voice-runtime-control.sh memory-review "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-approve "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-clear
```

Memoria local:

```bash
./scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" true
./scripts/local/voice-runtime-control.sh memory-load-local ".jarvis" true
./scripts/local/voice-runtime-control.sh memory-local-status ".jarvis"
./scripts/local/voice-runtime-control.sh memory-backup-local ".jarvis"
./scripts/local/voice-runtime-control.sh memory-delete-local ".jarvis" true
```

Memoria activa:

```bash
./scripts/local/voice-runtime-control.sh memory-activate "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-active-list
./scripts/local/voice-runtime-control.sh memory-deactivate "$PROPOSAL_ID" "razón"
./scripts/local/voice-runtime-control.sh memory-active-clear
```

Transcript:

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

## 10. Roadmap inmediato recomendado

Phase A-Phase S están cerradas. No existe una Phase T aprobada ni una siguiente fase maestra recomendada.

La regla global post-S es **Restrictions are approval gates, not permanent bans.**
La implementación actual sigue siendo control-plane segura; JARVIS no es
prepare-only para siempre y está diseñado para ejecutar tras aprobación válida,
strong approval/doble confirmación cuando aplique y todas las gates. Ilegal,
inseguro, dañino o no autorizado permanece denegado. Lo difícil, no resuelto o
unsupported puede tratarse como investigación/prototipo con incertidumbre
explícita, nunca como capacidad o éxito fingido.

El roadmap usa Mark 1, Mark 2 y Mark 3 mediante macro-PRs grandes. PR #125
cierra Mark 1 como release candidate seguro y operacionalmente claro, sin
activar ejecución externa real. El siguiente trabajo recomendado es **Mark 2
Macro 1 - Local Daemon, Real Wake Listener & Desktop Runtime**. Ver
`docs/jarvis-mark-1-release-candidate.md` y
`docs/jarvis-mark-1-operational-runbook.md`.

PR #126 inicia Mark 2 Macro 1: local daemon, desktop runtime, real wake listener
preparado y Voice Approval Channel. Todo queda disabled by default; no hay
micrófono real, audio bruto, red, servicios del sistema ni ejecución crítica.
La siguiente recomendación es **Mark 2 Macro 2 — Real Tool Execution: Browser,
GitHub, Filesystem & APIs**.

PR #127 inicia Mark 2 Macro 2 con policy, requests/candidates, adapters seguros,
sandbox, allowlist/denylist, approvals, audit y rollback. Los endpoints siguen
siendo preview-only y toda ejecución externa real queda disabled by default. La
siguiente recomendación es **Mark 2 Macro 3 — Visual Command Center UI & Human
Approval Console**.

PR #128 inicia Mark 2 Macro 3 con Visual Command Center, Human Approval
Console, Agent Operations Dashboard, AI coding session previews, costes/límites
sin datos inventados, riesgos, worktree guard, diff/tests/reviews y audit
timeline. Sigue siendo control-plane: no lanza Codex/Claude/Cowork, no consulta
billing y no ejecuta agentes o tools. La siguiente recomendación es **Mark 2
Macro 4 — Real Deploy, Stripe, Email, External Operations & AI CLI Adapters**.

PR #129 inicia Mark 2 Macro 4 con deploy/Stripe/email/domain candidates,
adapters Codex CLI/Claude Code/Claude Cowork/API fallback, Routine Execution
Bridge y external-operation audit. Toda invocación real, red, access material,
producción y dinero permanecen disabled by default. La siguiente recomendación
es **Mark 2 Release Candidate Hardening**.

PR #130 cierra Mark 2 como Release Candidate serio: cuatro macros consolidadas,
capability/readiness matrices, dangerous-route audit, approval-path audit, E2E
prepare-only smoke y runbook. Mark 2 no es autonomía libre; red externa, access
material, producción, dinero y ejecución real siguen disabled by default. La
siguiente recomendación es Mark 3 planning o piloto Mark 2 con setup manual y
approvals válidos.

El piloto local controlado posterior detectó que `RoutineExecutionBridge`
seleccionaba Codex CLI para una misión `local_first_preview` aunque Codex y
Claude reales estuvieran deshabilitados. PR #131 endurece la selección:
`preferred_mode` y flags `allow_*` se respetan, el caso local-first usa
`LocalScriptAdapter` preview-only y se añaden plan de mejora genérico,
`risk_review`, `audit_summary` y requisitos incumplidos. No se activa ejecución
real, red, escritura, deploy ni dinero.

PR #132 abre Mark 3 Master Planning. Define Universal Governed Execution:
preview/read-only es el default, no el techo permanente. El riesgo determina
approval, scope, budget, audit y rollback/stop; solo lo ilegal, inseguro,
dañino, no autorizado, engañoso o de bypass/robo queda permanentemente
denegado. Wake phrase no es permiso y tono/contexto solo informan intención
low-risk no sensible.

El roadmap Mark 3 usa macro-PRs #132-#141 para Mission Loop, Continuous
Learning, Multi-Agent Orchestration, Product/Revenue Factory, Local Routine
Scheduler, authorized account recovery y Moonshot Lab + Research/Experiment
Engine, cerrando con Release Candidate + Pilot plan. JARVIS
permanece en el ordenador actual de David; no Mac mini ni VPS hasta revenue
suficiente o necesidad técnica demostrada. Ver
`docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md`.

PR #133 implementa el primer Autonomous Mission Loop gobernado e in-memory:
intake, clasificación 0-5, plan determinista, preview, approvals exactos por
step, bounded execution candidates, outcomes/evidence, post-mortem y learning
proposal preview. No ejecuta herramientas externas.

PR #134, PR #135 y PR #136 están cerradas. PR #134 conectó el primer vertical
slice gobernado con Hermes para lectura local `read_file`; PR #135 añadió
Outcome Memory, Failure Memory, Learning Proposals y Research Radar; PR #136
añadió el Governed Research Execution Control Plane. Este handoff antiguo queda
actualizado: PR #137 es **Local Docs/Repo Research Adapter**, no Product/Revenue
Factory.

PR #137 conecta research local read-only para `docs/local_repo` desde el
Research Control Plane. Acepta solo un scope exacto de archivo permitido,
rechaza multi-scope, symlinks, path traversal, `.env`, tokens, passwords,
credentials, secrets, keys y broad root scans sin approval/setup. No usa web,
GitHub real, providers, threads, comandos, installs, commit/push/merge/PR ni
deploy. No añade endpoint research `/execute`; `/candidate` exige request
completa y no rehidrata snapshots redactados por `research_id`.

PR #138 es **Mark 3 Product/Revenue Factory**. Añade candidates prepare-only
para oportunidad, validación de nicho, blueprint, oferta/landing, pricing, unit
economics, revenue model, experiment plan, measurement plan y decisión
kill/continue. No publica, no despliega, no crea checkout, no llama Stripe, no
usa web/GitHub real, no envía emails, no compra dominios, no mueve dinero y no
usa credenciales. Debe mantener `no_fake_revenue`, `no_fake_costs`,
`candidate_is_not_publication`, `candidate_is_not_payment`,
`candidate_is_not_deploy` y `approval_is_not_execution`; siempre separa
`projected_revenue`, `confirmed_revenue`, `gross_revenue`, `expenses` y
`net_revenue`, usando `unknown` cuando falte evidencia. Stripe live,
producción, dominios, dinero, publicación real o identidad de David quedan como
Nivel 4 con strong approval y doble/triple confirmación.

PR #139 es **Mark 3 Local Routine Scheduler + Personal/Family Ops**. Añade
candidates prepare-only para rutinas locales supervisadas, tareas repetitivas
low-risk, daily/weekly routine plans, personal ops, family ops autorizadas,
authorized account assistance por official recovery, password manager checklist,
2FA checklist, recordatorios sin scheduling real y health checks de
repo/producto/budget sin ejecucion real. No crea scheduler real, cron jobs,
background workers ni watchers; no envia emails, no lee Calendar/Gmail/contactos,
no accede a cuentas reales, no guarda passwords, no salta 2FA, no usa cookies,
tokens o session material y no finge completion. Si falta capability devuelve
`setup_required` o `capability_not_connected_yet`; bypass, hacking, robo,
suplantacion, password storage, 2FA bypass y cookie/token/session theft son
Nivel 5.

PR #140 es **Mark 3 Moonshot Lab + Research/Experiment Engine**. Añade
candidates prepare-only para moonshot intake, hypothesis framing, research
experiment plan, prototype candidate, evidence scoring, uncertainty labels,
reproducibility checklist, stage gates, approval requirements, experiment budget
preview, stop conditions, safety/legal review, kill/continue/iterate
recommendation, audit summary y next safe action. Mantiene
`candidate_is_not_execution`, `approval_is_not_execution`,
`hypothesis_is_not_result`, `prototype_is_not_capability`,
`no_fake_breakthrough`, `no_fake_research_result`, `no_fake_benchmark`,
`no_fake_costs`, `no_fake_revenue`, `no_network`, `no_external_provider`,
`no_install`, `no_publish`, `no_deploy` y `no_money_movement`. No ejecuta
experimentos reales, no lanza tools reales, no usa red/GitHub/web/providers, no
instala dependencias, no crea procesos, no publica, no despliega, no mueve
dinero, no lee `.env`, no usa credenciales y no finge breakthroughs,
benchmarks, resultados, costes ni revenue. Producción, publicación, identidad,
dinero, live deploy y credenciales son Nivel 4; ilegal, inseguro, no
autorizado, bypass, daño, engaño o fake capability son Nivel 5.

PR #141 cierra **Mark 3 Release Candidate + Pilot**. Consolida status RC,
capability matrix, readiness matrix, dangerous-route audit, approval-path audit,
E2E prepare-only/gated smoke, pilot plan, pilot readiness, runbook, known
limitations y next steps. Declara Mark 3
`ready_as_controlled_release_candidate`, `not_ready_for_free_autonomy`,
`local_first`, `human_control_required` y
`restrictions_are_approval_gates_not_permanent_bans`. No ejecuta el piloto real,
no activa autonomia libre, no crea scheduler real, no usa red externa,
GitHub/web/providers reales, email, cuentas, credenciales, deploy, publish,
Stripe live, checkout, dinero ni installs. El primer piloto recomendado es
local, util, controlado, no-produccion, sin dinero, sin red externa, sin email,
sin cuentas reales y sin credenciales. Despues de Mark 3 RC, el siguiente paso
es ejecutar ese piloto local controlado, endurecer findings y empezar Mark 4
solo si el piloto lo justifica; no crear micro-PR explosion.

PR #142 endurece findings reales de Pilot 0 / Pilot 0B. Añade parsing central
de intención negativa/defensiva para que Mission Loop, Product/Revenue,
Routine Ops, Moonshot Lab y Research Execution no bloqueen por palabras
sensibles cuando aparecen como `false`, límite, stop condition, prohibited tool
o checklist defensivo. Mantiene bloqueos para secretos, `.env`, tokens,
password storage, bypass, acceso no autorizado, fake revenue/costs/results,
fake capability, producción, dinero, deploy, email real, cuentas reales,
providers, installs, subprocess, threads y red no conectada. No añade endpoints
de ejecución ni activa capacidades reales.

PR #143 corrige el caso restante observado al reiniciar la API despues de #142:
el payload defensivo completo de Pilot 0 enviado a
`POST /mark-3/mission-loop/missions` aun podia devolver
`intake implies permanently denied level 5 action`. Mission Loop ahora reconoce
prefijos `no_`, `sin ...`, `without ...`, listas de `prohibited_tools`,
constraints defensivas y stop conditions tipo `Any action requests ...` /
`Any result claims ...` como límites, no acciones. Las solicitudes reales de
`.env`, tokens, password storage, bypass, acceso no autorizado, fake
revenue/cost/result/capability, deploy/email/money reales y deception siguen
bloqueadas como Nivel 5.

Regla operativa vigente: JARVIS sigue con restrictions as approval gates, no
permanent bans. Lo ilegal, inseguro, no autorizado o engañoso sí es denegación
permanente. Hermes sigue siendo el motor de ejecución; JARVIS gobierna,
clasifica riesgo, decide, pide approval, audita y manda tareas bounded a Hermes
cuando exista capacidad aplicable.

PR #144 es **JARVIS Visual Voice Vision Mobile Roadmap Audit**. Crea
`docs/jarvis-visual-voice-vision-mobile-roadmap.md` como auditoria tecnica y
roadmap por macro-PRs para construir la experiencia real de JARVIS: Command
Center visual, Approval Console, Hermes Execution Panel, Mission Control,
Voice Core, wake word local seguro, conversacion, camera/vision privacy panel,
Mobile Companion/PWA, finance/ROI, Product Builder Adaptativo y hardening.
No implementa frontend, no activa microfono/camara, no instala dependencias, no
crea runtime, no duplica Hermes, no usa red externa, no despliega y no mueve
dinero. El siguiente PR recomendado es **PR #145 - JARVIS Local Dashboard
Shell**: primera pantalla local read-only dentro de `web/`, usando endpoints
existentes y manteniendo `JARVIS gobierna. Hermes ejecuta.`

PR #145 es **JARVIS Local Dashboard Shell**. Añade la ruta local `/jarvis` en
el frontend existente `web/` como primera pantalla visual/read-only del Centro
de Mando JARVIS. Implementa header, Voice Core visual, Mission Control,
Consola de Aprobación, Hermes Execution, radar de módulos, Camera/Vision
Privacy, Mobile Companion, Finance/ROI, Product Builder Adaptativo, timeline
audit preview y Kill Switch visible. No conecta backend wiring real, approvals
reales, voz real, wake word real, cámara real, mobile real ni Hermes execution;
los controles quedan `preview`, `disabled`, `not connected`, `gated` o
`unknown` según corresponda. Mantiene la regla operativa:
`JARVIS gobierna. Hermes ejecuta.`

PR #146 es **Visual Command Center Real Status Wiring**. Añade el read model
agregado `GET /mark-3/dashboard/status` y conecta la ruta `/jarvis` a ese
estado real de backend en modo read-only. El endpoint normaliza health,
release-candidate status/readiness/capabilities, dangerous-route audit,
approval-path audit, e2e smoke, pilot plan, Mission Loop, Hermes runtime,
Research, Product Revenue, Routine Ops, Moonshot Lab, Voice/Wake,
Camera/Vision, Mobile, approvals, finance, safety y timeline. La UI solo hace
lectura GET y degrada a `offline`, `unknown`, `not_connected` o `disabled` si
falta backend o evidencia. No añade ejecución, no aprueba, no activa sensores,
no pide permisos de navegador, no graba, no mueve dinero, no despliega, no
envía email, no toca credenciales y no duplica Hermes. Finance/ROI permanece
`unknown` hasta que exista medición real: no fake metrics.

PR #147 es **Approval Console Visual**. Enriquece el read model
`GET /mark-3/dashboard/status` con una estructura de approvals visuales:
`pending_count`, `critical_count`, `blocked_count`, `expired_count`,
`preview_count`, flags explícitos de read-only y tarjetas preview normalizadas.
Las tarjetas cubren lectura local exacta de docs/repo, escritura local
bloqueada, búsqueda web/GitHub no conectada, producción/dinero/deploy/Stripe/
email crítico y credenciales/secrets/tokens/cookies/session bypass como
forbidden/blocked. Cada tarjeta muestra acción, razón, status, risk level,
approval level, touches, costes `unknown`, scope, evidencia, expiry,
rollback/stop plan, disabled reason y acción recomendada para el operador. La
UI `/jarvis` renderiza resumen, badges, tarjetas, botones Aprobar/Rechazar/
Modificar alcance/Pedir explicación deshabilitados, aviso preview-only,
readback/confirmación fuerte, doble/triple confirmación, rollback/stop plan,
auditoría y leyenda de riesgo. No añade POST/PUT/DELETE, no añade endpoints
approve/reject/execute, no aprueba nada real, no llama a Hermes, no activa voz,
micrófono, cámara, sensores, dinero, deploy, email ni credenciales. Mantiene:
`JARVIS gobierna. Hermes ejecuta.`

PR #148 es **Hermes Execution Visibility Panel**. Enriquece
`GET /mark-3/dashboard/status` dentro de `hermes_execution` con contrato
JARVIS/Hermes, runtime status, capabilities gobernadas, rutas bloqueadas,
safety flags y timeline read-only. La UI `/jarvis` convierte el panel
`Hermes Execution` en `Ejecución Hermes` y muestra claramente:
`JARVIS gobierna. Hermes ejecuta.`, `El frontend no puede ejecutar Hermes
directamente.`, estado read-only/gated/no active execution, disponibilidad,
conexión, ejecución activa, últimos resultado/error/coste/duración como
`unknown` si no hay evidencia real, capacidades gobernadas, rutas bloqueadas y
requisitos antes de una ejecución futura: approval válido, scope exacto, risk
level, rollback/stop plan, auditoría, coste/impacto y operador humano. Kill
Switch sigue visible, pero aclara que en esta fase no hay ejecución Hermes
activa que parar. No añade endpoint execute, no añade POST/PUT/DELETE desde
`/jarvis`, no aprueba/rechaza, no ejecuta, no llama Hermes execute, no activa
tools reales, no crea tool runner frontend, no activa sensores, micrófono,
cámara o `getUserMedia`, no toca deploy/dinero/email/credenciales, no duplica
Hermes y no inventa métricas ni ejecuciones. Prepara el dashboard para Mission
Control posterior sin romper la regla: JARVIS gobierna; Hermes ejecuta.

PR #149 es **Mission Control Conversation Preview**. Enriquece
`GET /mark-3/dashboard/status` con `mission_control` para que `/jarvis` muestre
cómo JARVIS recibiría una orden de David, qué estructura de intención/riesgo/
approval esperaría y cuál sería el siguiente paso seguro. Incluye estado
`mode=preview`, input/conversation `preview_only`, ejecución deshabilitada,
Hermes dispatch deshabilitado, creación de approvals deshabilitada,
persistencia deshabilitada y red externa deshabilitada. Declara inputs
soportados como texto preview, voz/móvil/wake word future-gated y file drop/
camera context no conectados. Añade un `sample_command`, `intent_preview` en
`unknown`, lifecycle visual, `conversation_preview` con mensajes seguros de
David/JARVIS, `external_provider_called=false`, `memory_write=false`,
`raw_audio_stored=false`, `transcript_persistence=false`, `pii_redaction_required=true`
y safety flags para no auto execute, no Hermes dispatch, no tool call, no file
write, no network, no money, no deploy, no email, no credentials, no sensor
activation, no voice recording y no camera capture. La UI `/jarvis` muestra
`Control de Misión`, input deshabilitado, botones visuales disabled,
Conversation Preview, Intent/Risk Preview, Mission Lifecycle, Safety Banner y
la relación con Approval Console y Hermes Panel. No añade endpoints nuevos, no
llama providers, no guarda memoria, no crea misiones, no crea approvals, no
despacha a Hermes, no activa micrófono/cámara/sensores y no ejecuta nada.
Prepara conversación real futura sin convertir todavía una orden en ejecución.

PR #150 es **Voice Interaction Layer**. Agrupa Voice Core Visual, TTS State
Preview y Wake Word Local Safe Flow. Enriquece `GET /mark-3/dashboard/status`
con `voice_core` para que `/jarvis` muestre el núcleo visual de voz, estados
visuales, subtítulos preview, política wake word, privacidad de voz, relación
con Approval Console/Hermes y Kill Switch sin implementar voz real.
`voice_core.state` declara `mode=preview`,
`current_state=preview|dormant`, `microphone_enabled=false`,
`wake_word_enabled=false`, `command_listening_enabled=false`,
`tts_enabled=false`, `stt_enabled=false`, `audio_recording=false`,
`raw_audio_stored=false`, `external_provider_called=false`,
`voice_approval_enabled=false`, `wake_phrase_can_approve=false` y
`wake_phrase_can_execute=false`. `tts_state` mantiene subtítulos preview desde
`preview/read_model`, `speaking=false`, `audio_output_enabled=false`, provider
`none/not_connected` y `external_call=false`. `wake_word_policy` documenta las
frases futuras `Hola Jarvis` y `Jarvis`, pero la wake phrase no es permiso, no
aprueba y no ejecuta; las acciones críticas requieren readback y confirmación
fuerte. La UI muestra `Núcleo de Voz JARVIS`, el texto seguro
`David, estoy en modo preview. No estoy escuchando ni grabando audio.`, estados
preview/disabled/future-gated/not connected, privacidad (`micrófono: disabled`,
`grabación: false`, audio bruto no almacenado, provider externo none/not
connected, background listening disabled, voice approval disabled/future gated)
y deja claro que la voz puede preparar una intención futura, Approval Console
recibe approvals y Hermes solo ejecuta después de approval válido. No añade
endpoints nuevos, no llama providers, no activa micrófono, no activa wake word,
no graba audio, no guarda audio bruto, no usa captura de audio del navegador,
no hace STT/TTS real, no aprueba por voz y no despacha a Hermes. Prepara wake
word local seguro futuro como contrato visual/read-only, no como runtime.

La misma PR añade `wake_word_flow` en modo preview/read-only:
`wake_runtime_enabled=false`, `microphone_hard_off=true`,
`wake_word_only_mode=false`, `command_window_open=false`,
`push_to_talk_preview_enabled=true`, `typed_wake_preview_enabled=true`,
`always_on_microphone_enabled=false`, `background_listener_enabled=false`,
`stt_enabled=false`, `audio_recording=false`, `raw_audio_stored=false` y
`external_provider_called=false`. Expone frases soportadas `Hola Jarvis` y
`Jarvis`, stop phrases futuras (`para`, `cancela`, `detente`, `silencio`,
`cancelar misión`, `apaga escucha`) y explica modos: mic hard-off,
wake-word-only futuro, command listening futuro, push-to-talk futuro y typed
preview actual. Incluye `wake_parse_preview` para
`Hola Jarvis, revisa el estado del proyecto`: detecta `Hola Jarvis`, deja
`revisa el estado del proyecto` como comando restante, abriría una ventana de
comando futura, pero `would_execute=false`, `would_approve=false`,
`would_call_hermes=false`, `would_record_audio=false` y
`would_call_provider=false`. La policy mantiene wake phrase como no-permiso:
no aprueba, no ejecuta, approval por voz requiere canal autenticado, readback y
auditoría, y acciones críticas requieren doble/triple confirmación. La UI
muestra `Wake Word Local Safe Flow`, estado actual, frases soportadas, stop
phrases, parsing preview, policy visible y safety banner: no micrófono, no
grabación, no STT, no TTS real, no provider externo, no background listener, no
Hermes dispatch y no auto execute.

PR #151 es **Vision + Mobile Companion Layer**. Agrupa Camera / Vision Privacy
Panel y Mobile Companion / PWA baseline preview dentro de `/jarvis` y
`GET /mark-3/dashboard/status`, sin activar cámara real, visión real, sensores,
runtime móvil, approvals reales desde móvil ni ejecución.

Incluye `camera_vision` con `mode=preview`, `camera_enabled=false`,
`camera_permission_requested=false`, `preview_enabled=false`, `recording=false`,
`streaming=false`, `snapshot_capture_enabled=false`,
`vision_analysis_enabled=false`, `image_storage_enabled=false`,
`video_storage_enabled=false`, `external_vision_provider_called=false`,
`local_vision_model_connected=unknown` si no hay evidencia y
`background_camera_access=false`. Su privacidad declara no camera activation, no
browser media capture, no media stream, no recording, no snapshot capture, no
image/video storage, no external provider, explicit operator permission
required, visual indicator required when camera active y audit required for
future vision. Los estados visuales cubren camera off, camera available future,
preview disabled, permission required, analyzing future, recording disabled,
storage disabled, blocked y kill switch; todos tienen `can_execute=false`.

Incluye `mobile_companion` con `mode=preview`, `pwa_baseline=preview`,
`mobile_runtime_enabled=false`, `mobile_can_execute=false`,
`mobile_can_call_hermes_directly=false`,
`mobile_can_approve_real_actions=false`,
`mobile_can_reject_real_actions=false`,
`mobile_can_modify_scope_real=false`, `mobile_notifications_enabled=false`,
`remote_kill_switch_enabled=false`, `remote_camera_enabled=false`,
`remote_microphone_enabled=false` y `external_network_required=false`. Las
vistas futuras son status, approvals preview, mission preview, Hermes
visibility, voice status, camera status, finance summary y kill switch preview;
todas mantienen `can_execute=false` y `can_call_hermes=false`.

`mobile_companion.safety` declara mobile is interface not runtime, no direct
Hermes call, no mobile execute, no mobile sensor/camera/microphone activation,
no real mobile approval in this PR, approval requires backend gate, critical
approval requires strong confirmation y remote kill switch future gated.
`pwa_policy` deja installable PWA en preview, offline cache false, push false,
service worker false, no background sync, no credentials storage y no token
storage.

La UI `/jarvis` muestra `Cámara / Visión` y `Mobile Companion` como
`preview-only`. Los textos obligatorios quedan visibles: `La cámara no graba
por defecto.`, `No se captura imagen ni vídeo en esta PR.`, `No se usa
getUserMedia.`, `No hay proveedor externo de visión.`, `La visión futura
requerirá permiso explícito y auditoría.`, `Mobile es una interfaz, no un
runtime.`, `Mobile no llama a Hermes directamente.`, `Mobile no ejecuta
acciones.`, `Approvals reales desde móvil quedan future-gated.` y `No se
guardan credenciales ni tokens.`

PR #151 no implementa cámara real, browser media capture, snapshot, grabación,
streaming, image/video storage, visión/análisis visual real, provider externo
de visión, mobile runtime, mobile execution, mobile real approvals/rejections,
direct mobile/camera/frontend call to Hermes, service worker, push, background
sync, offline cache, credential storage, token storage, sensores, micrófono,
dinero, deploy, email, credenciales o red externa. Mantiene:
`JARVIS gobierna. Hermes ejecuta.`

PR #152 es **Product Finance Pilot Hardening**. Agrupa Finance/ROI, Product
Builder Adaptativo y Frontend Pilot/Hardening dentro de `/jarvis` y
`GET /mark-3/dashboard/status`. Sigue siendo read-only/preview: no mueve
dinero, no usa Stripe live, no crea checkout, no factura, no cobra, no crea
productos reales, no publica, no hace deploy, no envía email, no toca
credenciales, no activa sensores, no llama red externa, no ejecuta Hermes y no
añade POST/PUT/DELETE desde el dashboard.

Incluye `finance_roi` con `truth_policy`: no fake metrics,
unknown_when_no_evidence, measured_requires_source, estimated_requires_label,
confirmed_revenue_requires_evidence, projected_revenue_must_be_labelled y
roi_unknown_without_revenue_and_cost. Todas las métricas financieras son
objetos con value, label, source, evidence_state, confidence y last_updated.
Si no hay evidencia real, quedan `value=unknown`, `source=not_measured`,
`evidence_state=missing` y `confidence=unknown`. Esto cubre actual cost,
estimated cost, confirmed revenue, projected revenue, gross revenue, expenses,
net revenue, ROI, token/API/infra/manual input cost y revenue source. Budget
queda not configured/unknown. Safety declara no money movement, no Stripe live,
no checkout/invoice/payment collection, no fake revenue/costs/ROI y approval
fuerte para pagos reales futuros.

Incluye `adaptive_product_builder` con `mode=preview` y builder
`preview/read_only`: product generation, code generation, deploy, Stripe,
landing publish, external research y Hermes dispatch están en false. Las
stages son Idea, Validación, Blueprint, Código, Landing, Deploy candidate,
Monetización y Medición; todas tienen `can_execute=false`. La diferenciación
declara que no es Template Builder, no clona plantillas, cada producto necesita
razón de existir, métrica de éxito y lógica de monetización, y los productos
clonados son fallo. Monetization policy deja pricing preview only, Stripe live
y checkout bajo aprobación fuerte, revenue real bajo confirmación y projected
revenue etiquetado.

Incluye `frontend_pilot` con `mode=read_only_pilot`, ruta `/jarvis`, endpoint
`/mark-3/dashboard/status` y flags: frontend cannot execute, approve, activate
sensors, move money, deploy or send email. Readiness checks cubren route,
read-model connection, Approval Console, Hermes Execution, Mission Control,
Voice Core, Wake Flow, Camera/Vision, Mobile Companion, Finance/ROI, Product
Builder, Kill Switch, no fake metrics, no frontend execute, no sensor
activation y no POST/PUT/DELETE. Hardening notes dejan claro que si `npm ci`
observa audit vulnerabilities se registran como observadas, pero `npm audit
fix` no se ejecuta; dependency hardening queda en PR separada si toca lockfile
o dependencias, no se esperan cambios de lockfile, y frontend build/full pytest
son requeridos antes de merge.

La UI `/jarvis` muestra tres paneles nuevos con los textos obligatorios:
`No fake metrics.`, `Si no hay evidencia, mostrar unknown.`, `Revenue
confirmado requiere evidencia.`, `ROI queda unknown sin revenue y costes
reales.`, `No se mueve dinero desde este panel.`, `Stripe live requiere
aprobación fuerte.`, `No es un Template Builder.`, `Si dos productos parecen
clones, el builder ha fallado.`, `Deploy real requiere aprobación fuerte.`,
`Stripe/checkout real requiere aprobación fuerte.`, `Revenue real requiere
confirmación.`, `Pilot read-only`, `El dashboard mira, no toca.`,
`No POST/PUT/DELETE.`, `No execute.`, `No sensores.`, `No fake metrics.` y
`Dependency hardening queda para una PR separada.`

PR #152 mantiene la separación: JARVIS piensa, clasifica riesgo, pide
aprobación, audita, controla y muestra estado; Hermes sigue siendo solo motor
de ejecución detrás de gates válidos. Frontend, móvil, voz y cámara no llaman a
Hermes directamente.

PR #153 es **Visual Command Center Pilot**. Cierra un piloto local serio del
cockpit `/jarvis` sin convertirlo en operativo real. Añade
`visual_command_center_pilot` a `GET /mark-3/dashboard/status` con
`mode=read_only_pilot`, `dashboard_route=/jarvis`,
`status_endpoint=/mark-3/dashboard/status`, read-model backend conectado y
flags en false para frontend execution, approvals reales, Hermes direct
execution, voz real, cámara real, mobile runtime, money, deploy, email y
credentials.

El read model enumera los paneles requeridos: Header, Voice Core, Wake Word
Local Safe Flow, Mission Control, Approval Console, Hermes Execution, Agent /
Module Radar, Camera / Vision, Mobile Companion, Finance / ROI, Product Builder
Adaptativo, Frontend Pilot / Hardening, Live Timeline / Audit y Kill Switch.
Cada panel declara `expected=true`, source, status, `can_execute=false` y notas.
Los checks read-only cubren no POST/PUT/DELETE, no execute route, no frontend
Hermes call, no tool runner, no sensor activation, no getUserMedia, no
MediaRecorder, no AudioContext capture, no camera capture, no mobile runtime,
no money movement, no Stripe live, no deploy, no email send, no credentials y
no fake metrics.

La UI `/jarvis` muestra un panel `Visual Command Center Pilot` con ruta,
endpoint, modo, checklist de panels, checklist de seguridad, limitaciones
conocidas, pasos para David, estado de botones críticos y los textos: `El
dashboard mira, no toca.`, `No se ejecuta Hermes desde el frontend.`, `No se
activan sensores.`, `No hay approvals reales en esta fase.`, `No hay métricas
falsas.`, `Los valores sin evidencia se muestran como unknown.` y `Dependency
hardening queda para una PR separada.` El runbook está en
`docs/jarvis-visual-command-center-pilot.md`.

PR #153 no activa approvals reales, submit real de misión, ejecución Hermes,
voz real, wake listener real, cámara real, mobile runtime, dinero, Stripe,
checkout, deploy, email, credenciales, dependency hardening ni fake metrics. No
afirma que David haya probado manualmente el piloto.

PR #155 es **JARVIS Presence UI + Local System Contract**. Rediseña `/jarvis`
para que sea la presencia visual local de JARVIS, no una web ni un dashboard de
administracion. La primera pantalla pasa a estar dominada por un nucleo/orbe
central de JARVIS con estados visuales `idle/calmado`, `escuchando`,
`pensando`, `hablando` y `alerta/riesgo`, todos en modo preview/read-only.

El read model `GET /mark-3/dashboard/status` expone `local_system_contract`:
`JARVIS runtime/daemon local es el sistema`, `/jarvis` es solo la interfaz
visual/control center, movil y VPS seran clientes/puentes futuros, el frontend
no ejecuta directamente Hermes y voz/camara reales vendran en PRs posteriores.
Mantiene `JARVIS gobierna. Hermes ejecuta.` y `no_duplicate_hermes_runtime`.

La UI principal conserva solo informacion esencial: estado general, approvals
pendientes, escucha/piensa/habla, mision actual, coste/dinero, camara activa y
riesgo actual. Los detalles largos quedan en tabs/contratos plegados. Se anade
un `camera placeholder` lateral visual movible/ampliable sin getUserMedia,
captura, streaming, grabacion, storage ni permisos del navegador. Se anade una
`smart bar` inferior para escribir a JARVIS, transcripcion temporal preview,
respuesta temporal preview e `folded history`, todo disabled/preview.

PR #155 no activa voz real, wake listener real, STT, TTS, camara real,
getUserMedia, captura, streaming, sensores, grabacion, ejecucion Hermes,
misiones reales, approvals reales, movil real, VPS real, dinero, deploy, email
ni credenciales.

PR #156 es **Local Voice Loop + Presence Reactor**. Convierte la smart bar
inferior de `/jarvis` en una prueba real, local/browser-controlled y segura de
voz manual, y refuerza el nucleo central con presencia visual tipo
reactor/orbe cinematografico. El usuario debe pulsar el boton de microfono una
vez para abrir una conversacion manual; JARVIS escucha, responde y vuelve a
escuchar hasta stop/cancel o timeout. No hay always-listening autonomo, no wake
listener persistente real y la wake phrase nunca concede permiso.

Funciona realmente cuando el navegador lo soporta:

- STT via `SpeechRecognition` o `webkitSpeechRecognition`.
- TTS via `speechSynthesis`.
- conversacion manual continua hasta stop/cancel o timeout;
- seleccion preferente de voz en espanol si el navegador ofrece una voz mejor;
- transcripcion temporal visible en la smart bar;
- respuesta local/controlada de JARVIS, preview-only y con texto visible mas
  humano; los IDs tecnicos de intent/risk quedan secundarios;
- tono visual/TTS basico: `calmado`, `concentrado`, `alerta`, `intenso`;
- estados visuales del nucleo: `idle/calmado`, `escuchando`,
  `transcribiendo`, `pensando`, `hablando`, `error/no disponible`;
- control stop/cancel para cortar escucha y habla.
- nucleo central con capas, anillos, bloom, particulas sutiles y HUD; el
  movimiento responde al estado/tone de voz.

Dependencias y verdad de soporte:

- El soporte de STT/TTS depende del navegador.
- No se afirma que sea 100% local: el navegador puede usar servicios propios
  para SpeechRecognition/speechSynthesis.
- Si no hay soporte, `/jarvis` muestra `not_supported`/`unavailable` y no
  simula escucha.
- No se usa `getUserMedia`, `MediaRecorder` ni `AudioContext` para capturar
  audio bruto desde la UI.

Read model:

- `GET /mark-3/dashboard/status` expone `local_voice_loop`.
- `browser_stt_supported=unknown` y `browser_tts_supported=unknown`, porque el
  backend no puede saber las capacidades reales del navegador hasta que carga
  `/jarvis`.
- `manual_continuous_conversation=true`.
- `conversation_active=false` en el read model inicial; el estado real vive en
  el navegador cuando David activa el modo manual.
- `wake_listening=false` y `wake_listening_real_enabled=false`.
- `recording=false`.
- `audio_storage=false`.
- `raw_audio_sent_to_backend=false`.
- `approval_by_voice_enabled=false`.
- `wake_phrase_approval=false`.

Distincion futura de wake:

- `wake_listening` queda como contrato futuro: escucha minima de activacion sin
  grabacion, sin transcripcion continua, sin backend raw audio, sin ejecutar y
  sin aprobar.
- `conversation_active` empieza por activacion manual en esta PR; aqui si se
  transcribe lo que David dice para mostrarlo en smart bar y responder con TTS.
- `recording` sigue siendo `false`; no se guarda audio bruto.
- Texto operativo: "JARVIS aun no tiene wake listener persistente real en esta
  PR; la conversacion se activa manualmente. Arquitectura preparada para wake
  phrase sin grabar ni transcribir todo."

Seguridad que sigue bloqueada:

- no POST/PUT/DELETE desde `/jarvis`;
- no endpoint `/execute`;
- no Hermes directo desde frontend/voz;
- no misiones reales;
- no approvals criticos por voz;
- no dinero, deploy, email, credenciales, Stripe ni produccion;
- no camara real ni permisos de camara;
- no grabacion continua ni almacenamiento de audio bruto.

Como probar localmente:

1. Arrancar backend local para que `GET /mark-3/dashboard/status` responda.
2. Arrancar la app web y abrir `/jarvis`.
3. Usar un navegador con `SpeechRecognition`/`webkitSpeechRecognition` para
   probar STT; Chrome/Edge suelen ser los candidatos practicos.
4. Pulsar el boton de microfono en la smart bar, conceder permiso si el
   navegador lo pide, dictar una frase corta y verificar transcripcion,
   respuesta local, TTS si existe, reentrada automatica a escucha y cambio de
   estado visual.
5. Pulsar stop/cancel y verificar que escucha/habla se detienen y que no se
   crea ninguna ejecucion ni approval real.

## 11. Cómo iniciar un hilo nuevo

Bloque copiável:

```text
Lee docs/jarvis-handoff-context.md, docs/jarvis-north-star.md, docs/jarvis-architecture.md y docs/integrations/jarvis-local-memory-quickstart.md. Mantén la forma de trabajo por PR/worktree, prompts cerrados, validación con venv bueno, sin autoejecución, sin autoload y con PolicyEngine/sensitive boundary siempre por encima.
```
## PR #158 — Conversational Brain + Voice Session/Wake Architecture

PR #158 añade la base read-only para un cerebro conversacional determinista y
una arquitectura formal de Voice Session/Wake sin activar sensores always-on ni
ejecución. El contrato mantiene: JARVIS gobierna, Hermes ejecuta, el frontend no
despacha Hermes directamente y la wake phrase nunca aprueba.

- `jarvis/conversational_brain_bridge.py` expone un bridge v2 local/determinista
  que devuelve respuesta humana, intención, confianza, riesgo, nivel de
  aprobación, `requires_approval`, `can_prepare_preview`,
  `cannot_execute_reason`, `suggested_next_action` y
  `hermes_dispatch_allowed=false`.
- `jarvis/voice_session_control.py` añade el read model `jarvis.voice_session_manager.v1`
  con estados `idle`, `wake_listening_available`,
  `wake_listening_disabled`, `conversation_active`, `listening`,
  `transcribing`, `thinking`, `speaking`, `approval_required`, `cancelled`,
  `stopped` y `error`.
- `/mark-3/dashboard/status` agrega `conversational_brain`, `voice_session` y
  `wake_architecture`; `/mark-3/dashboard/events` y `/stream` agregan
  `brain_state` y `voice_session_state` metadata-only.
- `/jarvis` muestra la respuesta humana breve, diferencia wake disponible de
  conversación activa y deja claro que no hay transcripción continua, approval
  por wake ni Hermes directo.
- Documento de cierre: `docs/jarvis-pr-158-conversational-brain-voice-session-wake-architecture.md`.

No implementa wake real always-on, STT/TTS local backend serio, aprobación real
desde voz/frontend, dispatch Hermes end-to-end, lectura de secretos ni memoria
automática.

## PR #164 — Persistent Sensor/Voice Audit + Memory Brain v2

PR #164 añade auditoria persistente metadata-only y Memory Brain v2 local antes
de activar Hermes end-to-end.

- `jarvis/persistent_audit.py` implementa `PersistentAuditLedger` con SQLite
  opcional, `schema_version=jarvis.persistent_audit.v1`, hash-chain SHA-256
  (`previous_hash` + `entry_hash`) y `verify_chain()` para tamper detection
  basica.
- `jarvis/memory_brain_v2.py` implementa `MemoryBrainV2Store` con entities,
  facts, preferences, decisions, projects, contradictions, provenance,
  confidence, sensitivity, approval/review flags, active/forgotten/deleted,
  `reason_to_remember`, `influence_summary` y `why_used`.
- Los stores escriben bajo `.jarvis/audit/persistent_audit.sqlite3` y
  `.jarvis/memory_brain_v2/memory_brain_v2.sqlite3` solo cuando hay
  `base_dir`/`db_path` explicito o `JARVIS_LOCAL_STATE_DIR`/`JARVIS_STATE_DIR`;
  `create_app()` por defecto no crea `.jarvis` en el repo.
- Nuevos GET read-only:
  `/mark-3/audit/status`, `/mark-3/memory-brain/status`,
  `/mark-3/memory-brain/preview`.
- `/mark-3/dashboard/status`, `/events` y `/stream` exponen
  `persistent_audit_state` y `memory_brain_v2_state`, metadata-only.
- `/jarvis` muestra audit/memory en drawer `Sistemas`; no añade `/execute`,
  Hermes directo, POST/PUT/DELETE peligrosos ni approvals reales.

Sigue bloqueado: audio bruto, frames, secretos, `.env`, tokens, passwords,
cookies, session material, full transcripts, sensores nuevos, providers
externos, graph/vector DB obligatoria, cloud memory, dinero, deploy y email.

Documento de cierre:
`docs/jarvis-pr-164-persistent-audit-memory-brain-v2.md`.

## PR #165 — Phase 1 Completion: Governed Hermes Execution E2E + Pilot Hardening

PR #165 cierra Phase 1 como piloto local gobernado. JARVIS ya puede completar el
flujo intencion -> preview -> riesgo -> approval -> dispatch gobernado ->
auditoria -> status/event stream para capacidades soportadas, sin crear otro
Hermes y sin `/execute`.

- `jarvis/phase_1_governed_execution.py` introduce
  `Phase1GovernedExecutionControlPlane`.
- Reutiliza `ConversationalIntakePipeline`, `PolicyEngine`,
  `Mark3MissionLoop`, `Mark3HermesRuntimeBridge`, `PersistentAuditLedger` y
  `MemoryBrainV2Store`.
- Nuevos endpoints gobernados:
  `/mark-3/execution/status`, `/mark-3/phase-1/status`,
  `/mark-3/execution/preview`, `/mark-3/execution/request-approval`,
  `/mark-3/execution/approval-decision`, `/mark-3/execution/dispatch`,
  `/mark-3/execution/cancel` y `/mark-3/execution/stop`.
- `/jarvis` tiene approval panel backend-gated real. El frontend no llama Hermes
  directo, no ejecuta shell libre y no tiene `/execute`.
- Acciones reales en Phase 1: estado local safe/read-only, prepare-only y
  lectura exacta local no sensible mediante bridge Hermes existente con approval
  valido.
- `.env`, secretos, credenciales, tokens, passwords, cookies y session material
  quedan denied con la frase exacta protegida:
  `No puedo hacer eso, David. Las credenciales y secretos están protegidos.`
- Deploy, dinero, Stripe, email, publicacion, borrado, modificaciones
  destructivas y operaciones externas quedan denied/bloqueadas.
- Critical sin double/triple approval configurado queda
  `requires_stronger_approval_not_configured`.
- Voz puede enviar intencion textual manual; voz y wake phrase no aprueban.
- Persistent Audit recibe eventos reales metadata-only de intake, preview,
  risk, approval, dispatch, stop/cancel, rollback, memory influence, voice text
  intent y UI approval action.
- Memory Brain v2 puede explicar influencia (`why_used`) pero nunca concede
  permisos ni salta policy/approval.

Documentos de cierre:

- `docs/jarvis-pr-165-phase-1-completion-governed-execution-pilot.md`
- `docs/jarvis-phase-1-completion-report.md`
