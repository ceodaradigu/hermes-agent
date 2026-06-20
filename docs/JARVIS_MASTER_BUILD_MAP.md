# JARVIS Master Build Map

JARVIS es un sistema operativo personal de IA para David, privado/no SaaS, que convierte intención en misión, misión en acciones, acciones en activos, activos en medición y medición en mejora/monetización.

Este documento es el mapa maestro operativo para construir JARVIS por fases sin olvidar piezas críticas. No implementa código, runtime, endpoints, router, scripts, CI, dependencias, integraciones externas ni conexión nueva con Hermes/MissionControl.

**JARVIS_MASTER_BUILD_MAP.md is the source of truth for master phase names and order.**

Las foundations prepare-only pueden completarse antes que el objetivo runtime completo de una fase. Una extensión transversal, como Operator Console, no crea ni sustituye una fase maestra.

Las fases maestras Phase A-Phase S están cerradas en el mapa actual. Phase S es la última fase maestra implementada; cerrar una fase foundation no implica que sus capacidades runtime/producción estén activas.

## JARVIS vs Hermes

- JARVIS = cerebro, orquestador, interfaz, control, negocio y seguridad.
- Hermes = runtime interno, agentes, tools y ejecución controlada.
- Hermes no decide permisos.
- Hermes no ejecuta si JARVIS no entrega una acción permitida.
- JARVIS mantiene `PolicyEngine`, `ApprovalGateway`, audit log, `MissionState` y strong approval.

Flujo rector:

```text
David / interfaces / dispositivos
  -> JARVIS Gateway / Natural Runtime
  -> Mission / Policy / Approval / Audit
  -> HermesAdapter solo si la acción está permitida
  -> Hermes runtime/tools/agents
  -> resultado auditado para JARVIS
```

## Principio Central

- Preparar no es ejecutar.
- Aprobar no es ejecutar.
- Snapshot no es persistir.
- Dry-run no es ejecutar.
- Voz no salta seguridad.
- Móvil, reloj y gafas pueden aprobar si son dispositivos confiables y pasan strong approval.
- Ningún dispositivo puede hacer approve-all-forever.
- Dinero, identidad, publicación, producción, credenciales y contratos requieren strong approval.
- Memoria no es permiso.
- RAG no es permiso.
- Herramientas externas no son confiables hasta evaluarlas.

## Strong Approval

Strong approval = aprobación reforzada para acciones de alto riesgo.

Debe incluir:

- acción exacta.
- dispositivo confiable.
- challenge code/passphrase.
- scope.
- coste máximo si aplica.
- duración.
- rollback si aplica.
- audit log.
- expiración.
- no approve-all-forever.
- puede darse desde móvil, reloj, gafas o desktop si el dispositivo está autorizado y la acción queda clara.

Requieren strong approval como mínimo:

- mover dinero, crear pagos, activar checkout o comprometer gasto.
- publicar como David o usar su identidad.
- desplegar a producción o cambiar dominios.
- leer, usar o modificar credenciales/secretos.
- aceptar contratos, términos o compromisos legales.
- borrar, sobrescribir o ejecutar acciones irreversibles.
- instalar o ejecutar software externo no evaluado fuera de sandbox.

## Estado Actual Construido

Piezas de misión ya documentadas como mergeadas:

- `MissionEnvelope` v1.
- `MissionApprovalRequest` v1.
- `MissionAuditLog` v1.
- `MissionStateStore` v1.
- `MissionLifecycleValidator` v1.
- `MissionCommandBuilder` v1.
- `MissionDryRunEvaluator` v1.
- `MissionSnapshotSerializer` v1.
- `MissionApprovalBridge` v1 actual: payload prepare-only para aprobación futura sin aprobar, ejecutar, llamar `ApprovalGateway`, conectar runtime ni mutar estado.

Piezas relevantes ya documentadas:

- `PolicyEngine` como límite de decisión antes de ejecución.
- `ApprovalGateway` como vía obligatoria para acciones sensibles.
- Sensor Ledger metadata-only local para `camera`, `recording`, `wake`,
  `voice_session`, `tts` y `stt`, expuesto solo como read model desde
  `/mark-3/dashboard/status`; no guarda audio bruto, frames ni secretos.
- Event stream de dashboard robusto con `schema_version`, `event_id`,
  `created_at`, `risk_level`, payload seguro y heartbeat en
  `/mark-3/dashboard/events` y `/mark-3/dashboard/events/stream`; no ejecuta.
- Local Doctor ampliado con backend, frontend esperado `/jarvis`, stream,
  Hermes, deps opcionales, Python/plataforma/proceso, puertos esperados y
  capacidades browser-only marcadas `client_side_unknown`, sin activar sensores.
- Policy Status read-only visible: JARVIS gobierna, Hermes ejecuta, frontend no
  ejecuta Hermes directamente, wake phrase nunca aprueba, sensores requieren
  opt-in y ejecución peligrosa requiere `ApprovalGateway` + riesgo + auditoría +
  rollback/stop.
- Orbe 3D/HUD de `/jarvis` reforzado en WebGL manual: partículas orbitando,
  anillos radiales, marcas holográficas, profundidad, glow/bloom simulado,
  estados visuales `idle`/`wake_listening`/`listening`/`transcribing`/
  `thinking`/`speaking`/`alert`/`error`/`stopped`/`executing`, performance budget
  y fallback visible sin WebGL/canvas.
- Conversational Intake Pipeline de PR #159: normaliza texto escrito,
  transcripción de voz, comando futuro tras wake phrase e input remoto futuro en
  `ConversationalIntake`; detecta wake phrase, material sensible, baja
  confianza y ambigüedad; clasifica intención/riesgo; prepara preview cuando es
  seguro; siempre declara `safe_to_dispatch_to_hermes=false`.
- LLM Brain Adapter de PR #159: contratos `BrainRequest`, `BrainResponse` y
  `BrainProviderStatus`; provider por defecto `deterministic_local` apoyado en
  el bridge local existente; provider externo `disabled_external_llm` visible y
  deshabilitado por defecto. No llama APIs externas, no lee `.env`, no lee
  variables secretas, no persiste prompts y no despacha Hermes.
- Dashboard/Event Stream de PR #159: `/mark-3/dashboard/status` expone
  `conversational_intake` y `brain_adapter`; `/mark-3/dashboard/events` y
  `/stream` exponen `intake_state` y `brain_adapter_state` con metadata segura,
  sin raw text sensible, audio bruto, frames ni comandos ejecutables.
- Conversational UX Hardening de PR #175: `/jarvis` pasa de smart bar
  decorativa a cockpit conversacional basico usable. `POST
  /mark-3/conversation/turn` acepta texto o transcripción de voz manual,
  reutiliza intake/brain adapter local determinista, devuelve una respuesta
  humana en español y estados `normal/preview/approval_required/blocked/
  unsupported/error`. La UI mantiene historial local en memoria, Enter envia,
  Shift+Enter inserta salto de linea y el boton de enviar solo se deshabilita
  con mensaje vacio o turno activo. La respuesta completa queda en un historial
  legible con wrap/scroll/copia, mientras la tira inferior muestra solo preview.
  Las respuestas escritas intentan TTS via `speechSynthesis` del navegador
  cuando existe y la voz esta activada; hay controles de voz on/off, repetir y
  detener, con fallback escrito si TTS no esta disponible. Repetir habla solo la
  ultima respuesta de JARVIS; detener cancela la utterance local sin borrar el
  texto. La UI declara modo voz manual y que decir "Hola JARVIS" no activa wake
  real en esta PR. PR #176 queda como Voice Identity, Wake Pilot & Natural
  Conversation Loop. No añade `/execute`, Hermes directo,
  proveedores externos, memoria automatica ni side effects.
- Presence UI de PR #160: `/jarvis` queda reorientado a una experiencia
  orb-first, menos dashboard/admin console y mas presencia viva. Header, rails,
  smart bar, camara lateral y detalles tecnicos fueron compactados/plegados.
  `JarvisOrb3D` mantiene WebGL manual sin dependencias nuevas, añade
  `approval_required`, fallback visible, `prefers-reduced-motion`, pixel ratio
  limitado y performance budget. No añade Hermes dispatch, `/execute`,
  approve/reject real, sensores auto-start ni providers externos.
- Presence UI Visual Overhaul v2 de PR #161: corrige la direccion visual de
  #160 con fondo mucho mas oscuro (`#00030a`), nucleo azul-blanco diferenciado
  (`#e6fbff`), particulas frias separadas, glow concentrado en el centro,
  `stateReactiveEnergy`/`u_reactivity` por estado de voz y paneles laterales
  premium/minimos. La reactividad es state-driven; no abre Web Audio, no pide
  permisos nuevos, no auto-start mic/camara, no añade dependencias y no cambia
  el contrato JARVIS gobierna / Hermes ejecuta.
- Particle Sphere Motion Polish + Visual QA de PR #162: el centro de `/jarvis`
  queda como esfera/nube viva de particulas Canvas 2D, con 2600 particulas
  precomputadas, distribucion volumetrica, centro emergente por concentracion
  y sin logo, texto, nucleo fijo ni reactor circular visible. Los estados
  visuales quedan diferenciados: idle respira suave, listening se concentra,
  transcribing reorganiza, thinking usa turbulencia/remolino, speaking usa
  pseudo-audio determinista con picos radiales, alert/error expanden mas brusco
  y stopped se reduce/atenua. Añade Visual QA local plegado via controles y
  query param `jarvisVisualPreview`, sin Hermes, approvals, sensores, Web Audio
  nuevo, backend upload ni dependencias nuevas.
- Voice Runtime Pack de PR #163: agrega `VoiceRuntimePack` y GET
  `/mark-3/voice-runtime/status` como control-plane/read model seguro para la
  sesion de voz local/manual. Declara estados
  `idle/listening/transcribing/thinking/speaking/cancelled/stopped/error/
  approval_required/wake_listening_available/wake_listening_disabled`,
  contracts STT/TTS para browser y futuros providers locales, y flags duros
  `raw_audio_sent_to_backend=false`, `transcript_persistence=false`,
  `voice_approval_enabled=false`, `wake_phrase_can_approve=false`,
  `wake_phrase_can_execute=false`, `hermes_dispatch_allowed=false`. No instala
  faster-whisper, whisper.cpp, Piper, ffmpeg, sounddevice, torch, openWakeWord,
  MediaPipe ni TFJS; no descarga modelos; no activa wake always-on ni Hermes
  directo desde frontend.
- Phase 2 Local Assistant Runtime de PR #166: JARVIS añade ejecución local
  gobernada usable sin crear otro Hermes. `Phase2LocalAssistantRuntimeControlPlane`
  extiende Phase 1, reutiliza el `Mark3HermesRuntimeBridge` existente para
  `repo.file.read_safe`, y añade catálogo allowlisted para
  `local.status.read`, `local.doctor.run`, `repo.status.read`,
  `repo.tests.run_allowlisted`, `repo.diff.read`, `repo.log.read`,
  `jarvis.phase.status`, `jarvis.audit.status`, `jarvis.memory.status`,
  `jarvis.execution.history.read` y `jarvis.execution.preview`. Strong
  Approval v2 soporta `none/soft/normal/strong/double/triple/blocked/unsupported`;
  high requiere strong y critical queda blocked si double/triple real no está
  configurado. Execution History persiste metadata-only en SQLite cuando hay
  state dir. Stop/rollback contracts, browser verification, voice/wake
  readiness y daemon/tray readiness quedan visibles en API, event stream y
  drawer de `/jarvis`. Sigue sin `/execute`, shell libre, comandos arbitrarios,
  frontend Hermes directo, auto mic/camera/wake, secretos, dinero, Stripe,
  deploy, email ni publicación.
- Phase 4 Real Local Controller + Remote Pairing Readiness de PR #169: JARVIS
  convierte la readiness local en un controlador local opt-in realista sin
  instalar servicio, tray nativo ni autostart. `Phase4LocalControllerRemotePairingControlPlane`
  extiende Phase 3, modela `controller_id`, status/mode, bind local
  `127.0.0.1`, capacidades de status/approvals/stop/cancel/toggles, no
  background capture y failure modes honestos. Trusted Devices agrega navegador
  local, terminal local verificado por challenge y local controller registrado
  y verificado; voz/wake no aprueban y remoto queda untrusted por defecto.
  Triple approval queda preparado con tres pasos, canales separados,
  challenge/readback/phrase/expiry/anti-reuse/audit por paso y recalculo de
  policy antes de finalizar; critical sigue blocked si faltan tres canales.
  Remote pairing y Telegram/Hermes bridge quedan readiness-only,
  deshabilitados, sin tokens, sin `.env`, sin API calls, sin webhook, sin
  approval remoto y sin ejecucion remota. Stop/Rollback v2 expone metadata
  observable sin ejecutar rollback destructivo. `/jarvis` muestra Phase 4 en el
  drawer y preserva la esfera calmada de #168.
- Mission Control MVP con evaluación de cada step antes de Hermes.
- Voz base con `VoiceAdapter`, `MockVoiceAdapter`, adapter HTTP GPT-SoVITS, `/voice/tts`, `/voice/status` y almacenamiento local opcional de audio.
- Runtime local de voz/control documentado con feedback de entendimiento y comandos locales.
- Memoria local explícita: proposals, snapshot, `save-local`, `load-local`, review, approve, activate, deactivate y limpieza.
- Handoff workflow para continuar PRs en worktrees sin perder contexto.
- Contratos documentales de Hermes inside JARVIS, deployment modes, mobile voice approval, distributed personal OS, developer workshop, RAG, continuous learning, Money Engine y Asset Factory.
- Mark 3 Outcome Memory, Failure Memory, Learning Proposals y Research Radar de PR #135.
- Governed Research Execution Control Plane de PR #136: JARVIS normaliza research requests, decide policy/approval, valida capability contract y prepara hooks de Outcome/Failure Memory y Learning Proposals.
- Local Docs/Repo Research Adapter de PR #137: `docs/local_repo` tienen adapter local read-only conectado para un archivo exacto permitido. GitHub/web siguen en `capability_not_connected_yet`. No instala, no modifica, no hace commit/push/merge/deploy, no mueve dinero, no usa web/GitHub real, no crea threads, no ejecuta comandos, no sigue symlinks y no lee `.env`.
- Mark 3 Product/Revenue Factory de PR #138: prepara candidates de oportunidad, blueprint, pricing, unit economics, experimentos y decisiones sin publicacion, deploy, Stripe live, checkout, dominios, email, dinero, credenciales ni fake revenue/costs.
- Mark 3 Local Routine Scheduler + Personal/Family Ops de PR #139: prepara candidates para rutinas locales, personal/family ops autorizadas, authorized account assistance por official recovery, password manager checklist, 2FA checklist y health checks sin scheduler real, email, calendar, Gmail, contacts, account access, password storage, 2FA bypass, cookie/token/session use ni fake completion.
- Mark 3 Moonshot Lab + Research/Experiment Engine de PR #140: prepara moonshot intake, hypothesis framing, research experiment plans, prototype candidates, evidence scoring, uncertainty labels, reproducibility checklist, stage gates, safety/legal review y kill/continue/iterate decisions sin ejecutar experimentos, red, GitHub/web real, providers, installs, procesos, publicación, deploy, dinero, `.env`, credenciales ni fake breakthrough/benchmark/result.
- Mark 3 Release Candidate + Pilot de PR #141: consolida status RC, capability/readiness matrices, dangerous-route audit, approval-path audit, E2E prepare-only/gated smoke, pilot plan, runbook, known limitations y next steps. Mark 3 queda listo como RC controlado, no como autonomia libre. El primer piloto queda preparado, no ejecutado.
- Mark 3 Pilot Findings Hardening de PR #142: corrige overblocking de
  payloads defensivos/negativos del piloto mediante parsing central de
  intención accionable vs límites, flags `false`, stop conditions y prohibited
  tools. No añade endpoints ni habilita red, providers, scheduler, email,
  dinero, deploy, subprocess, threads, installs, cuentas reales o credenciales.
- Mark 3 Mission Loop Negative Intent Hardening de PR #143: cierra el caso
  restante descubierto al reiniciar API despues de #142, donde
  `POST /mark-3/mission-loop/missions` podia tratar stop conditions,
  `prohibited_tools`, prefijos `no_`, `sin ...` y frases `without ...` como
  intención Nivel 5. Mantiene bloqueos Nivel 5 para solicitudes reales de
  `.env`, tokens, password storage, bypass, acceso no autorizado, fake claims,
  deploy/email/money reales y deception.

Límites actuales:

- Phase A-Phase S están cerradas como foundations del mapa maestro actual; Phase S es la última fase maestra implementada.
- Mission Safety Baseline Gate de misión ya está mergeado.
- PR #81 completa los bridges/guards restantes de Phase B en modo prepare-only: Policy Bridge, Budget Guard, Approval Payload Hardening y Legal/AI Content Safety Baseline.
- Hermes Runtime Bridge foundation está completada en modo contrato/prepare-only; no hay ejecución Hermes real para misiones.
- Command Center foundation está completada con view model y API read-only; no hay Command Center visual real.
- Voice Companion foundation está completada en modo status/control-policy/preview prepare-only; no hay companion de voz runtime real.
- Mobile Companion foundation está completada como superficie API prepare-only; no hay app móvil ni multi-device runtime real.
- Operator Console Foundation está completada como extensión read-only de Command Center / operator layer. No es Phase G ni sustituye Ambient Vision.
- No hay tool adoption pipeline real.
- No hay Asset Factory, Deploy/Publishing, Sales, Payments ni Scheduler reales.

## Qué Falta Por Construir

Esta lista describe capacidades runtime/producción completas pendientes; no contradice el estado completado de sus foundations prepare-only.

- Approval Bridge.
- Safety Baseline Gate.
- Policy Bridge.
- Budget Guard.
- Hermes Runtime Bridge.
- Command Center visual.
- Voice Companion.
- Mobile Companion.
- Ambient Vision / Camera Companion.
- Multi-device runtime real.
- Trusted devices persistentes/remotos.
- Strong approval desde cualquier dispositivo autorizado real.
- Remote pairing activado con threat model completo.
- Telegram/mobile bridge activo bajo pairing y policy.
- Sandbox execution.
- Tool Adoption Pipeline.
- Graphify/CodeGraph/Open Design evaluation.
- Asset Factory / Web Builder.
- Deploy & Publishing.
- Communication & Sales.
- Payments & Revenue.
- Scheduler / Daily Operator.
- Continuous Learning / Tech Radar.
- Security/Legal Safety gates.
- Memory/RAG integration.
- User model / David understanding.
- Personal OS / environment intelligence.
- Wearables / smart glasses support.
- Interface visual de JARVIS.

## Fases Maestras

### Phase A - Mission Core Foundation

Estado: completada como foundation contractual prepare-only.

- Objetivo: definir contratos de misión serializables y validables.
- Permite: modelos de misión, approvals, audit, state, lifecycle, commands, dry-run y snapshots.
- NO permite: ejecución, persistencia real, conexión Hermes/MissionControl nueva, endpoints nuevos ni autonomía real.
- Criterios mínimos: contratos versionados, validación, serialización, estados claros y documentación de límites.
- Monetización: crea la base para misiones con métricas, objetivos y futuras acciones de revenue.
- Approval: no ejecuta; no requiere strong approval salvo que una futura acción derivada toque riesgo alto.

### Phase B - Approval & Safety Bridge

Estado: completada en modo prepare-only tras PR #81.

- Objetivo: conectar misión preparada con approvals y safety baseline sin ejecutar.
- Incluye: Mission Approval Bridge, Mission Safety Baseline Gate, Mission Policy Bridge, Budget Guard y legal/AI content safety baseline.
- Permite: convertir acciones preparadas en solicitudes aprobables con scope, riesgo, coste y expiración.
- NO permite: ejecutar por el hecho de aprobar ni usar approval como permiso global.
- Criterios mínimos: bridge auditable, rechazo de acciones ambiguas, expiración, budget visible y separación normal/sensitive/strong.
- Monetización: bloquea gasto, publicación, ventas y pagos hasta tener autorización clara.
- Approval: dinero, identidad, producción, publicación, credenciales y contratos requieren strong approval.

### Phase C - Hermes Runtime Bridge

Estado: foundation contractual completada en modo prepare-only; runtime de ejecución real pendiente.

- Objetivo: definir y construir la puerta segura entre JARVIS y Hermes.
- Incluye: Hermes adapter contract, command payload, dry-run bridge, execution result, safe execution adapter, audit integration y Hermes agent registry bridge.
- Permite: enviar a Hermes solo acciones ya permitidas, acotadas y auditables.
- NO permite: Mobile/voice/UI -> Hermes directo ni Hermes decidiendo permisos.
- Criterios mínimos: rechazar payloads sin policy/approval, límites de rutas/red/secretos, resultado estructurado y auditoría.
- Monetización: habilita ejecución controlada de activos, análisis y builders sin romper seguridad.
- Approval: ejecutar acciones con side effects requiere approval según riesgo; deploy, gasto e identidad requieren strong approval.

### Phase D - Command Center Visual Interface

Estado: foundation completada con view model y API read-only; interfaz visual operativa completa pendiente.

- Extensión transversal completada: Operator Console Foundation como Command Center / operator layer read-only. No sustituye ninguna fase maestra.
- Objetivo: crear la interfaz visual operativa de JARVIS.
- Incluye: visual shell, dashboard, missions view, approvals view, audit timeline, agents view, money/ROI view, device view, voice/camera controls e interfaz visual de JARVIS.
- Permite: ver estado, riesgos, approvals, misiones, ROI, dispositivos y controles.
- NO permite: que la UI ejecute saltándose policy.
- Criterios mínimos: dashboard usable, colas de aprobación claras, audit timeline visible y controles de pausa/cancelación.
- Monetización: muestra pipeline de activos, costes, revenue proyectado/confirmado y ROI.
- Approval: la UI puede iniciar approvals, pero strong approval sigue exigiendo challenge y scope exacto.

### Phase E - Voice Companion

Estado: foundation completada en modo prepare-only; conversación de voz runtime y controles activos pendientes.

- Objetivo: hacer que JARVIS pueda conversar por voz de forma segura.
- Incluye: wake phrase where possible, push-to-talk fallback, STT, TTS, voice conversation, voice approval flow, transcript confidence, low-confidence no-action rule y controles "no escuches" / "pausa".
- Permite: hablar, escuchar con control y pedir aprobaciones por voz.
- NO permite: ejecutar acciones sensibles por wake phrase ni aceptar confirmaciones peligrosas solo por voz.
- Criterios mínimos: indicador de escucha, fallback push-to-talk, baja confianza bloquea ejecución, logs sin audio sensible por defecto.
- Monetización: acelera briefing, construcción y revisión de activos; publicar o monetizar audio requiere approval.
- Approval: voz puede ayudar a confirmar, pero strong approval requiere challenge/passphrase y dispositivo confiable.

### Phase F - Mobile Companion

Estado: foundation completada en modo prepare-only; app móvil, pairing y acciones remotas reales pendientes.

- Objetivo: convertir móvil/PWA/app en interfaz remota segura.
- Incluye: approvals desde móvil, passphrase/challenge code, notifications, mission status, camera access, mic access, quick actions y offline/limited mode.
- Permite: revisar estado, aprobar/denegar, hablar, recibir notificaciones y controlar misiones.
- NO permite: llamar Hermes directo, leer filesystem local ni aprobar scopes vagos.
- Criterios mínimos: device pairing, sesión revocable, approvals expirables, notificaciones sin secretos y offline sin side effects sensibles.
- Monetización: permite desbloquear aprobaciones de ventas, publicación o gastos sin estar en desktop.
- Approval: strong approval desde móvil solo si el dispositivo es confiable y la acción exacta está clara.

### Phase G - Ambient Vision / Camera Companion

Estado: foundation prepare-only completada; runtime visual real pendiente.

- Objetivo: permitir "mira conmigo" sin convertir la cámara en vigilancia.
- Incluye: camera session, indicador visible camera-active, "no mires" hard stop, privacy redaction, no recording by default, no face/person analysis by default, document/screen awareness, useful alerts y audit of camera sessions.
- Permite: ayudar con documentos, pantallas, objetos o contexto visual explícito.
- NO permite: grabación continua invisible, análisis de personas por defecto ni envío de video sensible sin approval.
- Criterios mínimos: inicio/fin auditado, indicador visible, stop inmediato, redacción de privacidad y no-retention por defecto.
- Monetización: puede ayudar a revisar assets, pantallas, diseños, documentos y operaciones.
- Approval: cámara continua, exportación, publicación o análisis sensible requiere strong approval.

### Phase H - Multi-device Runtime

Estado: foundation prepare-only completada; runtime multi-dispositivo real pendiente.

- Objetivo: coordinar desktop, móvil, reloj, gafas, tablet, servidor y workers sin varios cerebros.
- Incluye: device registry, trusted devices, revoke device, approval from trusted devices, device capability model, sync state y notification routing.
- Permite: presencia distribuida, handoff, aprobaciones y estado sincronizado.
- NO permite: que un dispositivo gobierne, ejecute solo o cree approve-all-forever.
- Criterios mínimos: identidad de dispositivo, revocación, capacidades declaradas, expiración y audit correlation id.
- Monetización: reduce fricción para aprobar ventas, publicaciones, gastos y misiones largas.
- Approval: trusted device no sustituye strong approval; solo habilita canal autorizado.

### Phase I - Sandbox Execution

Estado: foundation prepare-only completada; ejecución real pendiente.

- Objetivo: ejecutar comandos y tools con aislamiento y límites.
- Incluye: safe command executor, filesystem scope guard, allowlist, no secrets scanner, rollback plan, execution audit, dry-run required before execution y no production without strong approval.
- Permite: pruebas, builds y comandos acotados bajo policy.
- NO permite: host escape, secretos, producción, red amplia o installs silenciosas.
- Criterios mínimos: scope de filesystem, límites de tiempo/red, scanner de secretos, dry-run previo y rollback documentado.
- Monetización: permite construir y validar assets sin poner en riesgo repos, credenciales o producción.
- Approval: ejecución con side effects requiere approval; producción, dinero y credenciales requieren strong approval.

### Phase J - Tool Adoption Pipeline

Estado: foundation prepare-only completada; adopción, instalación y ejecución real de herramientas pendientes.

- Objetivo: evaluar herramientas externas antes de adoptarlas.
- Incluye: discover tool, license check, repo health, dependency risk, sandbox install proposal, spike runner, value measurement, keep/rollback decision, Graphify/CodeGraph/Open Design as candidates y no silent core dependency.
- Permite: investigar y medir herramientas.
- NO permite: instalar, ejecutar o convertir en dependencia core sin aprobación y medición.
- Criterios mínimos: licencia, permisos, dependencias, seguridad, artefactos, rollback y medición de tiempo/tokens/errores/valor.
- Monetización: adopta solo herramientas que mejoran velocidad, calidad o revenue.
- Approval: install/spike requiere approval; core dependency o ejecución con permisos amplios requiere strong approval.

### Phase K - Asset Factory / Web Builder

Estado: foundation prepare-only completada; generación y escritura real de activos pendientes.

- Objetivo: transformar oportunidades en activos digitales medibles.
- Incluye: landing generator, website generator, offer builder, copy generator, design assets, templates, demo builder, GitHub PR automation y Open Design evaluation when useful.
- Permite: crear borradores, demos, landings, ofertas y assets revisables.
- NO permite: publicar, gastar, usar identidad ni prometer ingresos.
- Criterios mínimos: hipótesis, público, métrica, coste, riesgo, tracking plan y condición de cierre.
- Monetización: convierte misiones en activos reutilizables con vía de revenue.
- Approval: publicar, comprar dominio, conectar cuenta externa o usar identidad requiere strong approval.

### Phase L - Deploy & Publishing

Estado: foundation prepare-only completada; deploy y publicación reales pendientes.

- Objetivo: llevar assets a preview y producción con control.
- Incluye: preview deploy, Vercel/Render adapters, env guard, domain checklist, production approval, rollback deploy y publication audit.
- Permite: previews revisables y publicación controlada.
- NO permite: producción automática, secretos en logs ni dominios/cuentas sin scope.
- Criterios mínimos: diff/config visible, env guard, rollback, auditoría y checklist de dominio.
- Monetización: habilita experimentos públicos y productos.
- Approval: producción, dominios, identidad y publicación real requieren strong approval.

### Phase M - Marketing / Distribution Engine

Estado: foundation completada en modo prepare-only; distribución, cuentas y ejecución real pendientes.

- Objetivo: preparar audiencias, campañas, canales, contenido, medición y lanzamiento de forma revisable.
- Incluye: audience preview, channel strategy, campaign plan, content distribution pack, SEO/social/community/email outreach preview, UTM/measurement plan, budget guard, launch checklist y approval requirements.
- Permite: estructurar planes y borradores con inputs proporcionados por el usuario.
- NO permite: publicar, enviar, crear ads, conectar cuentas, usar identidad real, gastar, scrapear, automatizar spam ni llamar servicios externos.
- Criterios mínimos: prepare-only, no fake claims/social proof/income guarantees, redacción sensible, no tracking instalado, launch no-ready por defecto y API sin side effects.
- Monetización: prepara distribución medible sin confundir hipótesis, métricas planificadas o presupuesto solicitado con resultados o gasto real.
- Approval: publicar, enviar, paid ads, cuentas externas, identidad, secretos y gasto requieren strong approval.

### Phase N - Payments & Revenue

Estado: foundation prepare-only completada; pagos, cobros y conexión real con providers pendientes.

- Objetivo: medir y operar revenue sin confundir proyección con dinero real.
- Incluye: Stripe/Gumroad adapter, checkout proposal, pricing model, expense tracker, confirmed vs projected revenue, net revenue calculator, ROI tracker, budget guard advanced y no payments without strong approval.
- Permite: proponer precios, checkouts, métricas y tracking financiero.
- NO permite: crear pagos, mover dinero, activar cobros o prometer ingresos garantizados.
- Criterios mínimos: revenue projected/confirmed, gross revenue, expenses, net revenue, coste máximo y audit.
- Monetización: cierra el ciclo de ingresos medibles.
- Approval: pagos, checkouts, gastos, contratos y datos financieros requieren strong approval.

### Phase O - Daily Operator / Scheduler

Estado: foundation prepare-only completada; scheduling y ejecución recurrente reales pendientes.

- Objetivo: operar el día con planes, reportes y colas de aprobación.
- Incluye: daily mission loop, morning plan, evening report, stop conditions, retry logic, notifications, approval queue y weekly review.
- Permite: planificar, agrupar, recordar, preparar y reportar.
- NO permite: autoejecución sensible ni watchers con side effects.
- Criterios mínimos: horarios claros, stop conditions, retries limitados, cancel/pause/resume y digest auditable.
- Monetización: mantiene cadencia sobre assets, leads, revenue y aprendizaje.
- Approval: scheduler puede proponer; ejecutar acciones sensibles requiere approval o strong approval.

### Phase P - Continuous Learning / Tech Radar

Estado: foundation prepare-only completada; investigación externa y aplicación real de cambios pendientes.

- Objetivo: mantener JARVIS actualizado sin auto-modificación.
- Incluye: tech radar, relevance filter, contrarian review, proposal creation, approval workflow, PR planner, no auto-update, no auto-install y no auto-deploy.
- Permite: investigar, filtrar, proponer y planificar PRs.
- NO permite: instalar, modificar runtime, cambiar prompts o desplegar automáticamente.
- Criterios mínimos: propuesta con impacto, riesgos, dependencias, tests, rollback y decisión recomendada.
- Monetización: prioriza novedades que ahorran tiempo, reducen errores o aumentan revenue.
- Approval: aplicar cambios, instalar dependencias o modificar runtime requiere approval; producción/credenciales requieren strong approval.

### Phase Q - Personal OS / Environment Intelligence

Estado: foundation prepare-only completada; lectura de fuentes y awareness real pendientes.

- Objetivo: coordinar contexto, atención, entorno y rutinas de David.
- Incluye: PC state awareness, calendar/email/doc awareness with approval, local files scope, context switching, attention protection, environment signals, personal routines y energy/focus support.
- Permite: daily state, modos, atención, notificaciones y contexto autorizado.
- NO permite: vigilancia opaca, inferencias sensibles sin consentimiento ni mezcla personal/profesional indebida.
- Criterios mínimos: consentimiento por fuente, separación de contextos, privacidad, modo invitado y razones visibles.
- Monetización: protege foco humano y prioriza acciones de mayor ROI.
- Approval: leer fuentes sensibles o cruzar datos privados requiere approval; enviar/actuar requiere strong approval si aplica.

### Phase R - Advanced Personalization / User Model

Estado: foundation prepare-only completada; aprendizaje y memoria real pendientes.

- Objetivo: aprender cómo piensa, habla, decide y monetiza David de forma explícita.
- Incluye: David understanding, preferences, speech patterns, business goals, contrarian mode, memory proposals, approved/reversible memory, uncertainty handling y no opaque learning.
- Permite: memoria aprobada, tono adaptativo, preferencias y mejores decisiones.
- NO permite: aprendizaje opaco, manipulación, memoria como permiso ni certezas privadas inventadas.
- Criterios mínimos: proposal, review, approve, activate, deactivate, audit, reversión y manejo de incertidumbre.
- Monetización: mejora priorización, copy, producto, ventas y foco.
- Approval: memoria puede orientar; nunca autoriza acciones sensibles.

### Phase S - Future/Moonshot Layer

Estado: foundation prepare-only completada. Es la última fase maestra implementada del mapa actual; no existe Phase T aprobada.

- Objetivo: explorar capacidades avanzadas sin saltarse seguridad.
- Incluye: smart glasses deeper integration, AR overlays, robotics/drones only if safe/legal, deep simulation, physical-world automation y always with safety and approval.
- Permite: prototipos seguros y evaluaciones futuras.
- NO permite: automatización física peligrosa, vigilancia, suplantación, acciones ilegales o permisos implícitos.
- Criterios mínimos: legal/safety review, sandbox o entorno controlado, stop inmediato, audit y rollback.
- Monetización: solo si aporta ventaja real, no por espectáculo.
- Approval: físico, legal, identidad, dinero y seguridad requieren strong approval.

## Wake Phrase, Voz y Cámara

- "Hola JARVIS" o una frase configurable es objetivo futuro.
- En iOS puede requerir Shortcuts, App Intents, botón, acción o app abierta según limitaciones de plataforma.
- En Android/desktop puede haber más opciones.
- Siempre debe existir fallback push-to-talk.
- Baja confianza de transcript implica no-action o aclaración.
- "No escuches" detiene escucha activa o vuelve a modo limitado.
- Cámara continua requiere indicador visible, stop inmediato y privacidad.
- "No mires" detiene la sesión de cámara.
- No hay grabación por defecto.
- No hay face/person analysis por defecto.

## Herramientas Externas

Graphify, CodeGraph, Open Design, OpenClaw u otras herramientas externas deben tratarse como no confiables hasta evaluación.

Reglas:

- no instalar sin approval.
- no ejecutar sin sandbox.
- no convertir en dependencia core sin medición.
- evaluar licencia, dependencias, permisos, seguridad y valor.
- medir si reduce tiempo, tokens, errores o mejora activos.
- verificar outputs contra fuentes reales, código real y tests cuando aplique.
- no indexar secretos ni carpetas fuera de scope.
- no crear artefactos persistentes en el repo sin decisión explícita.

## Monetización

Antes de decir "gana 500€ con 50€ en 30 días", JARVIS debe tener:

- mission revenue model.
- strategy generator.
- experiment planner.
- budget guard.
- asset factory.
- communication/sales.
- publishing/deploy.
- payments/revenue tracker.
- scheduler.
- approval flows.
- execution sandbox.

Debe separar:

- revenue projected.
- revenue confirmed.
- gross revenue.
- expenses.
- net revenue.

JARVIS puede maximizar probabilidad, reducir coste, preparar experimentos y medir señales. Nunca debe prometer ingresos garantizados ni tratar proyecciones como dinero confirmado.

## Estado después de Phase S

- Phase A-Phase S están cerradas como foundations del mapa maestro actual.
- Phase S es la última fase maestra implementada.
- No existe una siguiente fase maestra aprobada ni una Phase T implícita.
- El cierre de las fases no activa ejecución real todavía: la implementación actual sigue siendo control-plane segura.
- **Restrictions are approval gates, not permanent bans.** JARVIS no es prepare-only para siempre: acciones legales, seguras, autorizadas y soportadas podrán ejecutarse tras aprobación válida y todas las gates.
- Ilegal, inseguro, dañino o no autorizado permanece como denegación
  permanente. Lo difícil, no resuelto o actualmente unsupported puede avanzar
  como investigación, hipótesis o prototipo, pero nunca como capacidad o éxito
  falsamente afirmado.
- Wake Phrase, Voz y Cámara; Herramientas Externas; y Monetización son áreas transversales/post-fase. No deben convertirse en una nueva fase sin una decisión explícita y una actualización previa de este mapa.

## Roadmap Mark 1 / Mark 2 / Mark 3

El roadmap usa macro-PRs grandes y coherentes, no cientos de micro-PRs por Mark.

- **Mark 1:** PR #122 semántica global; PR #123 Monetization Engine Real; PR #124 SaaS/Product Builder + Publishing/Deploy Execution; PR #125 hardening, E2E Real Ops y release candidate.
- **Mark 2:** daemon/wake/desktop real; tools reales; UI y approval console; deploy/Stripe/email reales; release candidate hardening.
- **Mark 3:** Universal Governed Execution; mission loop; multiagente;
  aprendizaje continuo; product/revenue factory; rutinas locales supervisadas;
  authorized account assistance; Moonshot Lab; medición/ROI; release candidate
  hardening.

La definición completa está en `docs/jarvis-post-s-global-approval-controlled-execution-semantics-mark-roadmap.md`.

Post-S Macro 8 / PR #123 implementa Monetization Engine Real dentro de Mark 1:
pricing, revenue projections, budget guard, payment approval readiness, Stripe
readiness y unit economics/ROI. No mueve dinero real ni llama Stripe. La
siguiente recomendación es **Post-S Macro 9 — SaaS/Product Builder +
Publishing/Deploy Execution**.

PR #124 / Post-S Macro 9 consolida el **Product Builder Adaptativo / Adaptive
SaaS Builder** y los candidatos de publishing/deploy bajo aprobación, sin crear
repos, escribir scaffolds externos, publicar o desplegar. La siguiente
recomendación es **Post-S Macro 10 — Mark 1 Hardening, E2E Real Ops & Release
Candidate**.

## Mark 1 Release Candidate

PR #125 / Post-S Macro 10 cierra Mark 1 como release candidate coherente,
documentado, testeado y operacionalmente claro. Phase S continúa siendo la
última fase maestra y no existe Phase T.

Mark 1 consolida governance, approval-controlled execution semantics, audit,
permission gates, runtime/tool readiness, memory/Personal OS/scheduler,
wake/voice/camera control-plane, monetización, Adaptive SaaS Builder,
publishing/deploy candidates y consolas operacionales. La ejecución externa
real, dinero real, deploy/publicación reales y sensores reales permanecen
deshabilitados por defecto.

La siguiente recomendación es **Mark 2 Macro 1 - Local Daemon, Real Wake
Listener & Desktop Runtime**. Ver `docs/jarvis-mark-1-release-candidate.md` y
`docs/jarvis-mark-1-operational-runbook.md`.

Criterios obligatorios:

- No crear nuevas fases sin actualizar primero este mapa maestro y registrar la decisión explícita.
- No pasar del control-plane actual a ejecución real sin approval válido, strong approval y doble confirmación cuando aplique.
- No ejecutar revenue ni afirmar resultados sin separar `projected`, `confirmed`, `gross`, `expenses` y `net`.
- No instalar, ejecutar ni adoptar herramientas externas sin evaluar licencia, seguridad, permisos y valor.
- No habilitar cámara o voz continua sin indicador visible, stop inmediato y controles de privacidad.

## Mark 2 Macro 1 iniciada

PR #126 inicia Mark 2 con local daemon desactivado por defecto, desktop runtime
visible, real wake listener preparado sin acceso real al micrófono y Voice
Approval Channel. La voz puede aprobar tras readback y confirmaciones fuertes;
la wake phrase nunca concede permiso. No completa Mark 2 ni activa ejecución
externa. La siguiente recomendación es **Mark 2 Macro 2 — Real Tool Execution:
Browser, GitHub, Filesystem & APIs**.

## Mark 2 Macro 2 iniciada

PR #127 añade policy, requests, candidates, readiness, adapters seguros de
filesystem/GitHub/browser/APIs, sandbox boundaries, allowlist/denylist, audit y
rollback/stop plans. Todos los endpoints son preview/control-plane: red,
credenciales, producción, dinero y ejecución externa real siguen disabled by
default. La siguiente recomendación es **Mark 2 Macro 3 — Visual Command Center
UI & Human Approval Console**.

## Mark 2 Macro 3 iniciada

PR #128 añade Visual Command Center, Human Approval Console, Agent Operations
Dashboard, AI coding session control, costes/límites, riesgos, worktree guard,
diff/tests/reviews y audit timeline como capa de datos control-plane. No crea
un frontend final, no lanza Codex/Claude/Cowork, no consulta billing y no
ejecuta agentes o tools. La siguiente recomendación es **Mark 2 Macro 4 — Real
Deploy, Stripe, Email, External Operations & AI CLI Adapters**.

## Mark 2 Macro 4 iniciada

PR #129 prepara operaciones externas gobernadas de deploy, Stripe/payment,
email y domain publishing, junto con adapters Codex CLI, Claude Code, Claude
Cowork/Desktop, API fallback, Routine Execution Bridge y audit seguro. No
ejecuta proveedores reales, no usa cookies/tokens/access material y no completa
Mark 2. La siguiente recomendación es **Mark 2 Release Candidate Hardening**.

## Mark 2 Release Candidate

PR #130 cierra Mark 2 como Release Candidate controlado. Consolida las cuatro
macros, capability/readiness matrices, dangerous-route y approval-path audits,
E2E prepare-only smoke y runbook operacional. Mark 2 no es autonomía libre:
ejecución real, red externa, access material, producción y dinero permanecen
desactivados por defecto. La siguiente recomendación es Mark 3 planning o un
piloto Mark 2 limitado con setup manual y approvals válidos.

## Mark 2 Pilot Findings Hardening

El piloto local controlado posterior a PR #130 detectó un gap en
`RoutineExecutionBridge`: `local_first_preview` no estaba gobernando la
selección antes del tipo de rutina. PR #131 corrige esa decisión para respetar
`preferred_mode` y los flags `allow_*`, devolver un preview local seguro cuando
Codex/Claude reales están deshabilitados y bloquear API fallback sin red. No
activa ejecución real ni abre Mark 3.

## Mark 3 Master Planning

PR #132 abre Mark 3 como **Universal Governed Execution**. Mark 3 no es
read-only ni preview-only permanente: preview/read-only es el default inicial,
y las acciones legales, seguras, autorizadas, técnicamente posibles y
soportadas pueden avanzar con aprobación y controles proporcionales al riesgo.

PR #132 solo planifica y añade endpoints GET deterministas. Define niveles de
aprobación 0-5, Autonomous Mission Loop, Continuous Learning, Multi-Agent
Orchestration, Product/Revenue Factory, supervised local routines, authorized
account recovery, Moonshot Lab, Measurement/ROI y local-first infrastructure.
No activa ejecución Mark 3. El roadmap continúa con macro-PRs #133-#141; no
usa micro-PR explosion. Ver
`docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md`.

PR #133 añade el Autonomous Mission Loop in-memory y genera bounded execution
candidates sin ejecución externa. El orden operativo posterior es: PR #134
Governed Execution Engine, #135 Continuous Learning + Outcome Memory, #136
Governed Research Execution Control Plane, #137 Local Docs/Repo Research
Adapter, #138 Product/Revenue Factory, #139 Local Routine Scheduler +
Personal/Family Ops, #140 Moonshot Lab + Research/Experiment Engine y #141
Release Candidate + Pilot.

PR #134 conecta el primer vertical slice de ejecución real gobernada con
Hermes: `Mark3MissionLoop candidate -> governed validation ->
HermesRuntimeAdapter -> AIAgent -> read_file -> outcome/evidence`. Sigue
limitado a filesystem read local aprobado, sin red, terminal, browser, dinero,
writes ni providers reales fuera del adapter gobernado.

PR #135 añade Autonomous Growth + Outcome Learning + Research Radar. JARVIS no
está enjaulado: acciones legales, seguras, autorizadas y técnicamente
soportadas pueden avanzar con approval proporcional. Esta capa registra Outcome
Memory y Failure Memory, genera Learning Proposals revisables, prepara research
para GitHub/web/docs/local_repo y devuelve `setup_required` cuando falta adapter
real en vez de convertirlo en permanent-deny. No crea otro Hermes ni otro
executor: Hermes sigue siendo el motor; JARVIS gobierna, decide, clasifica
riesgo, pide approval, audita y propone cambios a Hermes cuando necesita
mejorar el motor. Ver
`docs/jarvis-mark-3-autonomous-growth-learning-radar.md`.

PR #136 añade el Governed Research Execution Control Plane. PR #137 conecta el
Local Docs/Repo Research Adapter: `docs/local_repo` pasan a `connected` solo
para lectura local segura de un scope exacto de archivo. Broad root scans,
multi-scope, symlinks, path traversal, `.env`, tokens, passwords, credentials,
secrets y keys quedan rechazados por policy/adapter. No hay endpoint research
`/execute`; `/candidate` exige request completa y no rehidrata snapshots por
`research_id`.

PR #138 añade Mark 3 Product/Revenue Factory como control-plane seguro:
oportunidad, validación de nicho, blueprint, oferta/landing candidate, pricing,
unit economics, revenue model, experiment plan, measurement plan y decisión
kill/continue. No publica, no despliega, no crea checkout, no llama Stripe, no
compra dominios, no envía emails, no usa web/GitHub real, no mueve dinero, no
usa credenciales y no inventa revenue, costes ni métricas. Siempre separa
`projected_revenue`, `confirmed_revenue`, `gross_revenue`, `expenses` y
`net_revenue`; si falta evidencia devuelve `unknown`. Stripe live, producción,
dominios, dinero, publicación real o identidad de David siguen como Nivel 4 con
strong approval y doble/triple confirmación.

PR #139 añade Mark 3 Local Routine Scheduler + Personal/Family Ops como
control-plane seguro: rutinas locales supervisadas, tareas repetitivas
low-risk, daily/weekly routine plans, personal ops, family ops autorizadas,
authorized account assistance por official recovery, password manager checklist,
2FA checklist, recordatorios sin scheduling real y health checks de
repo/producto/budget sin ejecucion real. Todo candidate incluye risk,
approval, scope, budget, schedule preview, evidence required, stop conditions,
next safe action y audit summary. No hay scheduler real, cron, background
worker, watcher, email, calendar, Gmail, contacts, provider real, account
access, password storage, 2FA bypass, cookie/token/session use ni fake
completion. Capacidades no conectadas devuelven `setup_required` o
`capability_not_connected_yet`; bypass, hacking, robo, suplantacion y acceso no
autorizado son Nivel 5.

PR #140 añade Mark 3 Moonshot Lab + Research/Experiment Engine como
control-plane prepare-only: moonshot intake, hypothesis framing, research
experiment plan, prototype candidate, evidence scoring, uncertainty labels,
reproducibility checklist, stage gates, approval requirements, experiment budget
preview, stop conditions, safety/legal review, audit summary y next safe action.
No ejecuta experimentos reales, no usa red/GitHub/web/providers reales, no
instala dependencias, no crea procesos, no publica, no despliega, no mueve
dinero, no lee `.env`, no usa credenciales y no finge breakthroughs,
benchmarks, resultados, costes ni revenue. Producción, publicación, identidad,
dinero, live deploy y credenciales son Nivel 4; ilegal, inseguro, no autorizado,
bypass, daño, engaño o fake capability son Nivel 5.

## Mark 3 Release Candidate + Pilot

PR #141 cierra Mark 3 como Release Candidate controlado y prepara el primer
piloto local real sin ejecutarlo todavía. Consolida capability matrix,
readiness matrix, dangerous-route audit, approval-path audit, E2E
prepare-only/gated smoke, pilot plan, operational runbook, known limitations y
post-Mark-3 next steps.

Mark 3 RC declara:

- `release_candidate_status=ready_as_controlled_release_candidate`;
- `ready_as_controlled_release_candidate=true`;
- `not_ready_for_free_autonomy=true`;
- `local_first=true`;
- `human_control_required=true`;
- `restrictions_are_approval_gates_not_permanent_bans=true`.

No activa scheduler real, autonomía libre, red externa, GitHub/web/providers
reales, email real, cuentas reales, credenciales, `.env`, deploy, publish,
dominios, Stripe live, checkout, money movement, installs ni background 24/7.
El piloto inicial debe ser local, util, controlado, no-produccion, sin dinero,
sin red externa, sin email, sin cuentas reales y sin credenciales. La siguiente
recomendación es ejecutar ese piloto local controlado, endurecer findings y
abrir Mark 4 solo si el piloto lo justifica con evidencia; no micro-PR
explosion.

## Mark 3 Pilot Findings Hardening

PR #142 corrige el bug funcional descubierto por Pilot 0: las superficies Mark
3 no deben elevar a Nivel 5 o bloquear solo porque una palabra sensible aparece
en una negación, límite, stop condition, prohibited-tool list, checklist
defensivo o flag booleano explícito `false`.

El hardening aplica a Mission Loop, Product/Revenue Factory, Routine Ops,
Moonshot Lab y Research Execution. Solicitudes reales de secretos, `.env`,
tokens, password storage, bypass, acceso no autorizado, fake revenue/costs,
fake results, fake capabilities, producción, dinero, deploy, email real,
cuentas reales o capacidades no conectadas siguen bloqueadas o gated según el
modelo Mark 3.

## Mark 3 Mission Loop Negative Intent Hardening

PR #143 corrige el caso restante de Mission Loop real descubierto despues de
#142: el payload defensivo completo de Pilot 0 enviado a
`POST /mark-3/mission-loop/missions` podia devolver
`intake implies permanently denied level 5 action` porque el clasificador leia
listas defensivas renderizadas en texto libre como si fueran acciones.

Mission Loop ahora distingue prefijos `no_`, frases `no hacer X`, `sin X`,
`without X`, listas de `prohibited_tools`, constraints defensivas y stop
conditions como `Any action requests ...` / `Any result claims ...`. Las
peticiones reales de leer `.env`, usar tokens, guardar passwords, saltarse 2FA,
acceder sin autorizacion, fingir revenue/result/capability, desplegar
produccion ahora, enviar email real ahora o mover dinero siguen denegadas como
Nivel 5.

## Visual Voice Vision Mobile Roadmap Audit

PR #144 no abre una nueva fase maestra ni implementa frontend. Documenta el
roadmap tecnico para convertir las foundations existentes en una experiencia
local-first real de JARVIS sin duplicar Hermes.

Documento principal:

- `docs/jarvis-visual-voice-vision-mobile-roadmap.md`

Alcance cubierto:

- Dashboard / Visual Command Center.
- Operator Console.
- Approval Console visual.
- Hermes Execution Panel.
- Mission Control y conversacion.
- Voice Core visual.
- Wake word local seguro.
- Camera/vision privacy panel.
- Mobile Companion/PWA.
- Finance/ROI con `measured`, `estimated` y `unknown`.
- Product Builder Adaptativo.
- Frontend pilot y hardening.

Reglas fijadas:

- `JARVIS gobierna. Hermes ejecuta.`
- No duplicate Hermes.
- No frontend directo a Hermes.
- No wake word como approval.
- No microfono/camara/grabacion por defecto.
- No fake metrics, no fake revenue, no fake costs y `unknown` cuando falte
  evidencia.
- No Mac mini/VPS hasta revenue o necesidad tecnica real.

Siguiente PR recomendado:

- **PR #145 - JARVIS Local Dashboard Shell**, una primera pantalla read-only
  dentro de `web/`, sin nuevos runtimes, sin dependencias nuevas, sin sensores
  reales, sin dinero, sin deploy y sin approvals ejecutables.

## JARVIS Local Dashboard Shell

PR #145 implementa la primera shell visual local de JARVIS en la ruta `/jarvis`
del frontend existente `web/`.

Incluye:

- Centro de Mando JARVIS read-only.
- Voice Core visual en modo preview seguro.
- Mission Control sin creación de misiones reales.
- Consola de Aprobación demo/preview, sin approve/reject real.
- Hermes Execution Panel que muestra que JARVIS no ejecuta y Hermes ejecuta
  solo bajo gates válidos.
- Agent / Module Radar, Camera/Vision Privacy, Mobile Companion, Finance/ROI,
  Product Builder Adaptativo, Live Timeline / Audit Preview y Kill Switch
  visible no conectado.

No implementa:

- backend wiring real;
- approvals reales;
- voz real;
- wake word real;
- cámara real;
- mobile real;
- Hermes execution desde frontend.

La separación sigue siendo obligatoria:

```text
JARVIS gobierna.
Hermes ejecuta.
```

El siguiente trabajo recomendado es PR #146 - Backend wiring read model, si se
quiere conectar esta shell a endpoints read-only/preview existentes sin abrir
acciones de ejecución.

## JARVIS Visual Command Center Real Status Wiring

PR #146 conecta la ruta local `/jarvis` a estado real de backend mediante el
read model agregado `GET /mark-3/dashboard/status`.

Incluye:

- Read model normalizado para System, contrato JARVIS/Hermes, Release
  Candidate, módulos, approvals, Hermes Execution, Voice/Wake, Camera/Vision,
  Mobile, Finance/ROI, Product Builder, safety y timeline.
- Lectura de fuentes existentes seguras: `/health`, Mark 3 release-candidate
  status/readiness/capabilities/audits/e2e-smoke/pilot-plan, Mission Loop,
  Hermes runtime status, Research, Product Revenue, Routine Ops, Moonshot Lab,
  Voice/Wake, Camera Control, Mobile Companion, outcomes y learning proposals.
- Frontend `/jarvis` con un único cliente read-only hacia
  `GET /mark-3/dashboard/status`.
- Fallback seguro: backend offline o campos ausentes se muestran como
  `offline`, `unknown`, `not_connected` o `disabled`.

No implementa:

- ejecución desde frontend;
- approve/reject real;
- llamada directa del navegador a Hermes;
- tool runner frontend;
- getUserMedia, microfono, camara, grabacion o permisos de navegador;
- WebSocket;
- dinero, Stripe, deploy, email, credenciales o produccion;
- metricas falsas de coste, revenue, ROI, resultados o capacidades;
- runtime Hermes duplicado.

La regla sigue fija:

```text
JARVIS gobierna.
Hermes ejecuta.
```

El siguiente trabajo recomendado tras PR #146 era PR #147 - Approval Console
visual, manteniendo controles approve/reject deshabilitados hasta que exista
una ruta backend gobernada, auditada y explicitamente aprobada. Ese trabajo
queda descrito abajo.

## JARVIS Approval Console Visual

PR #147 convierte la Consola de Aprobación del Visual Command Center en una
pieza visual útil para el operador humano, sin convertirla en una superficie de
ejecución.

Incluye:

- `GET /mark-3/dashboard/status` expone approvals enriquecidas dentro del read
  model existente: summary counts, flags read-only y tarjetas preview
  normalizadas.
- Summary visible: pending, critical, blocked, expired y preview; todos los
  botones de acción permanecen disabled.
- Tarjetas preview para lectura local exacta docs/repo, escritura local,
  web/GitHub externo, producción/dinero/deploy/Stripe/email real y
  credenciales/secrets/tokens/cookies/session bypass.
- Cada tarjeta declara acción, razón, status, risk level, approval level,
  touches, coste estimado/medido `unknown`, scope, evidencia, expiry,
  rollback plan, stop plan, disabled reason y acción recomendada.
- La UI `/jarvis` muestra badges de riesgo y nivel de aprobación, touched
  surfaces, rollback/stop plan, readback, confirmación fuerte, doble/triple
  confirmación, auditoría, botones Aprobar/Rechazar/Modificar alcance/Pedir
  explicación deshabilitados y leyenda de riesgo nivel 0-5.

No implementa:

- approve/reject real;
- endpoint de approve/reject/execute;
- POST/PUT/DELETE desde la página `/jarvis`;
- llamada directa a Hermes desde el navegador;
- tool runner frontend;
- activación de voz, micrófono, cámara, sensores o grabación;
- dinero, Stripe, deploy, email real, credenciales o producción;
- métricas falsas de coste, revenue, ROI, resultados o capacidades;
- runtime Hermes duplicado.

La regla sigue fija:

```text
JARVIS gobierna.
Hermes ejecuta.
```

El siguiente trabajo recomendado es PR #148 - Hermes Execution Visibility
Panel, manteniendo el frontend como superficie de lectura y control visual,
sin crear un ejecutor paralelo a Hermes.

## JARVIS Hermes Execution Visibility Panel

PR #148 mejora el panel `Hermes Execution` de `/jarvis` y el read model
`GET /mark-3/dashboard/status` para mostrar Hermes como motor de ejecución
gobernado, sin darle al frontend poder de ejecución.

Incluye:

- `hermes_execution.contract` con la separación explícita: JARVIS gobierna
  intención, riesgo, approval, auditoría y control; Hermes es
  `execution_engine`.
- Flags de seguridad: no duplicate Hermes runtime, frontend direct execution
  disabled, frontend cannot execute and frontend cannot call Hermes execute.
- `runtime_status` con disponibilidad/conexión/ejecución activa, modo
  `read_only_visibility` y campos `unknown` para last result/error/rollback,
  duración y coste cuando no existe evidencia real.
- `governed_capabilities` para lectura local gobernada, docs/repo research,
  mission-gated candidates, approval-gated execution, herramientas externas y
  deploy/email/money/credentials.
- `blocked_routes` para execute, approve/reject, tool runner, deploy, money,
  email, credentials, sensores, camera/mic y red externa no gateada.
- `/jarvis` muestra `Ejecución Hermes`, `JARVIS gobierna. Hermes ejecuta.`,
  `El frontend no puede ejecutar Hermes directamente.`, `Sin ejecución
  activa`, rutas bloqueadas y requisitos antes de cualquier ejecución futura.

No implementa:

- endpoint execute nuevo;
- POST/PUT/DELETE desde `/jarvis`;
- stop real de Hermes;
- approval/reject real;
- tool runner frontend;
- sensores, micrófono, cámara o `getUserMedia`;
- dinero, Stripe, deploy, email, credenciales o producción;
- runtime Hermes duplicado;
- métricas, coste, duración, resultado o ejecución inventados.

PR #148 prepara el dashboard para Mission Control posterior: una futura UX de
misiones podrá mostrar intención, riesgo, scope y approvals, pero Hermes seguirá
ejecutando solo bajo gates válidos emitidos por JARVIS.

## JARVIS Mission Control Conversation Preview

PR #149 mejora `Control de Misión` en `/jarvis` y el read model
`GET /mark-3/dashboard/status` para mostrar cómo sería hablar o escribir a
JARVIS sin abrir ejecución.

Incluye:

- `mission_control.state` con `mode=preview`, input/conversation preview-only y
  execution, Hermes dispatch, approval creation, persistence y external network
  deshabilitados.
- `supported_inputs` para texto preview, voz/móvil/wake word future-gated y
  file drop/camera context no conectados.
- `sample_command` seguro:
  `JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro.`
- `intent_preview` con detected intent, confidence, mission type, risk level,
  approval level y next safe action en `unknown`, sin inventar clasificación.
- `command_lifecycle` visual para draft, submitted for preview, intent
  detected, risk classified, approval required, operator review, blocked,
  forbidden y executable candidate after valid approval.
- `conversation_preview` con mensajes placeholder de David/JARVIS,
  `external_provider_called=false`, `memory_write=false`,
  `raw_audio_stored=false`, transcript persistence off y redacción PII requerida.
- Safety flags: no auto execute, no Hermes dispatch, no tool call, no file
  write, no network call, no money movement, no deploy, no email, no
  credentials, no sensor activation, no voice recording, no camera capture y
  wake phrase is not permission.
- Timeline read-only: Mission Control preview read, Conversation preview read,
  No command execution performed y Hermes dispatch disabled from Mission
  Control.
- `/jarvis` muestra input deshabilitado, botones disabled, Conversation
  Preview, Intent/Risk Preview, Mission Lifecycle, Safety Banner y la relación
  con Approval Console y Hermes Panel.

No implementa:

- endpoint nuevo de submit;
- creación de misión real;
- creación de approval real;
- Hermes dispatch;
- llamadas a providers externos;
- escritura de memoria o transcript persistence;
- file write, network call, tool call o ejecución;
- voz real, micrófono, cámara, sensores o `getUserMedia`;
- dinero, Stripe, deploy, email, credenciales o producción.

PR #149 prepara conversación real futura, pero mantiene la separación:

```text
JARVIS gobierna.
Hermes ejecuta.
```

## JARVIS Voice Interaction Layer

PR #150 mejora la capa de interacción de voz de `/jarvis` y el read model
`GET /mark-3/dashboard/status` sin implementar voz real. Agrupa:

- Voice Core Visual;
- TTS State Preview;
- Wake Word Local Safe Flow.

Incluye:

- `voice_core.state` con `mode=preview`, `current_state=preview|dormant`,
  `microphone_enabled=false`, `wake_word_enabled=false`,
  `command_listening_enabled=false`, `tts_enabled=false`, `stt_enabled=false`,
  `audio_recording=false`, `raw_audio_stored=false`,
  `external_provider_called=false`, `voice_approval_enabled=false`,
  `wake_phrase_can_approve=false` y `wake_phrase_can_execute=false`.
- `visual_states` para offline, online, preview, dormant,
  listening_wake_word, listening_command, thinking, speaking,
  approval_required, hermes_executing, paused, blocked, error y kill_switch,
  con label, description, risk, enabled preview/false, sensor_required y
  `can_approve=false`.
- `tts_state` con subtítulos preview desde `preview/read_model`, speaking false,
  audio output false, provider `none/not_connected` y external call false.
- `wake_word_policy` con frases futuras `Hola Jarvis` y `Jarvis`; la wake
  phrase no es permiso, no aprueba y no ejecuta; approval futuro requiere canal
  autenticado, readback y confirmación fuerte para acciones críticas.
- `privacy` y `safety`: no microphone activation, no audio recording, no raw
  audio storage, no external audio provider, no background listening, no voice
  biometrics, no voice approval without gate, no auto execute, no Hermes
  dispatch, no tool call, no sensor activation, no browser media capture APIs
  and kill switch visible.
- Timeline read-only: Voice Core visual state read, Voice/TTS state preview
  generated, Microphone disabled, Wake word runtime not active y No audio
  recording performed.
- `/jarvis` muestra `Núcleo de Voz JARVIS`, núcleo central con anillos CSS,
  estados visuales, subtítulos preview:
  `David, estoy en modo preview. No estoy escuchando ni grabando audio.`,
  política wake word, privacidad de voz, relación con Approval Console/Hermes y
  Kill Switch de voz.
- `wake_word_flow.state` con `mode=preview`,
  `wake_runtime_enabled=false`, `microphone_hard_off=true`,
  `wake_word_only_mode=false`, `command_window_open=false`,
  `push_to_talk_preview_enabled=true`, `typed_wake_preview_enabled=true`,
  `always_on_microphone_enabled=false`, `background_listener_enabled=false`,
  `stt_enabled=false`, `audio_recording=false`, `raw_audio_stored=false` y
  `external_provider_called=false`.
- `wake_word_flow.supported_phrases`: `Hola Jarvis`, `Jarvis`.
- `wake_word_flow.stop_phrases`: `para`, `cancela`, `detente`, `silencio`,
  `cancelar misión`, `apaga escucha`.
- `wake_word_flow.mode_explanations` diferencia mic hard-off, wake-word-only,
  command listening, push-to-talk y typed preview.
- `wake_word_flow.wake_parse_preview` modela
  `Hola Jarvis, revisa el estado del proyecto`: detecta `Hola Jarvis`, deja
  `revisa el estado del proyecto` como comando restante, abriría una ventana
  futura, pero no ejecuta, no aprueba, no llama Hermes, no graba audio y no
  llama providers.
- `wake_word_flow.approval_policy`: wake phrase no es permiso, no aprueba, no
  ejecuta; approval por voz requiere canal autenticado, readback y auditoría;
  acciones críticas requieren doble/triple confirmación.
- `wake_word_flow.safety`: no microphone activation, no browser media capture,
  no background listening, no raw audio storage, no external STT/TTS, no Hermes
  dispatch, no tool call y no auto execute.
- Timeline read-only adicional: Wake word flow preview read, Microphone
  hard-off confirmed, Typed wake preview available, Wake phrase cannot approve,
  Wake phrase cannot execute y No background listener started.
- `/jarvis` muestra `Wake Word Local Safe Flow` con estado actual, frases
  soportadas, stop phrases, diferencia de modos, preview de parsing, policy
  visible y safety banner.

No implementa:

- voz real;
- activación de micrófono;
- wake word real;
- listener wake word real;
- escucha de comandos;
- STT real;
- TTS real;
- salida de audio;
- grabación o almacenamiento de audio bruto;
- background listening;
- voice biometrics;
- provider externo;
- aprobación por voz;
- endpoint nuevo;
- llamada directa a Hermes desde frontend o voz.

PR #150 prepara una futura wake word local segura, pero solo como presencia
visual/read-only y contrato de seguridad. La wake phrase nunca aprueba ni
ejecuta, y solo podría abrir una ventana de comando futura bajo gates explícitos.

## JARVIS Vision + Mobile Companion Layer

PR #151 mejora `/jarvis` y `GET /mark-3/dashboard/status` con una capa
read-only de visión y móvil. Agrupa:

- Camera / Vision Privacy Panel;
- Mobile Companion / PWA baseline preview.

Incluye `camera_vision`:

- `state.mode=preview`;
- `camera_enabled=false`;
- `camera_permission_requested=false`;
- `preview_enabled=false`;
- `recording=false`;
- `streaming=false`;
- `snapshot_capture_enabled=false`;
- `vision_analysis_enabled=false`;
- `image_storage_enabled=false`;
- `video_storage_enabled=false`;
- `external_vision_provider_called=false`;
- `local_vision_model_connected=unknown` si no hay evidencia;
- `background_camera_access=false`.

Incluye privacidad y scope policy para cámara/visión:

- no camera activation;
- no browser media capture;
- no media stream;
- no recording;
- no snapshot capture;
- no image/video storage;
- no external provider;
- explicit operator permission required;
- visual indicator required when camera active;
- audit required for future vision;
- future analysis must state what it can see;
- future analysis must not infer sensitive identity;
- future analysis must not store without permission.

Los estados visuales de cámara son camera off, camera available future, preview
disabled, permission required, analyzing future, recording disabled, storage
disabled, blocked y kill switch; todos tienen label, description, risk,
enabled false/preview/future-gated y `can_execute=false`.

Incluye `mobile_companion`:

- `state.mode=preview`;
- `pwa_baseline=preview`;
- `mobile_runtime_enabled=false`;
- `mobile_can_execute=false`;
- `mobile_can_call_hermes_directly=false`;
- `mobile_can_approve_real_actions=false`;
- `mobile_can_reject_real_actions=false`;
- `mobile_can_modify_scope_real=false`;
- `mobile_notifications_enabled=false`;
- `remote_kill_switch_enabled=false`;
- `remote_camera_enabled=false`;
- `remote_microphone_enabled=false`;
- `external_network_required=false`.

Las vistas móviles futuras son status, approvals preview, mission preview,
Hermes visibility, voice status, camera status, finance summary y kill switch
preview; todas son preview/future-gated/disabled/unknown con
`can_execute=false` y `can_call_hermes=false`.

Incluye `mobile_companion.safety` y `pwa_policy`:

- mobile is interface not runtime;
- no direct Hermes call;
- no mobile execute;
- no mobile sensor/camera/microphone activation;
- no real mobile approval in this PR;
- approval requires backend gate;
- critical approval requires strong confirmation;
- remote kill switch future gated;
- installable PWA preview;
- offline cache disabled;
- push notifications disabled;
- service worker disabled;
- no background sync;
- no credentials storage;
- no token storage.

La UI `/jarvis` muestra `Cámara / Visión` y `Mobile Companion` como
`preview-only`, con estado actual, privacidad/safety, estados o vistas futuras,
PWA policy y los textos de guardrail obligatorios:

- `La cámara no graba por defecto.`
- `No se captura imagen ni vídeo en esta PR.`
- `No se usa getUserMedia.`
- `No hay proveedor externo de visión.`
- `La visión futura requerirá permiso explícito y auditoría.`
- `Mobile es una interfaz, no un runtime.`
- `Mobile no llama a Hermes directamente.`
- `Mobile no ejecuta acciones.`
- `Approvals reales desde móvil quedan future-gated.`
- `No se guardan credenciales ni tokens.`

No implementa:

- cámara real;
- browser media capture;
- snapshot capture;
- grabación;
- streaming;
- image/video storage;
- visión/análisis visual real;
- provider externo de visión;
- mobile runtime;
- mobile execution;
- mobile approvals reales;
- direct mobile/camera/frontend call to Hermes;
- service worker;
- push;
- background sync;
- offline cache;
- credential/token storage;
- sensores, micrófono, dinero, deploy, email, credenciales o red externa.

## JARVIS Product Finance Pilot Hardening

PR #152 mejora `/jarvis` y `GET /mark-3/dashboard/status` como macro-PR
read-only/preview. Agrupa:

- Finance / ROI Panel realista;
- Product Builder Adaptativo;
- Frontend Pilot / Hardening.

Incluye `finance_roi`:

- `truth_policy.no_fake_metrics=true`;
- `unknown_when_no_evidence=true`;
- `measured_requires_source=true`;
- `estimated_requires_label=true`;
- `confirmed_revenue_requires_evidence=true`;
- `projected_revenue_must_be_labelled=true`;
- `roi_unknown_without_revenue_and_cost=true`.

Todas las métricas financieras son objetos con `value`, `label`, `source`,
`evidence_state`, `confidence` y `last_updated`. Sin evidencia real, actual
cost, estimated cost, confirmed revenue, projected revenue, gross revenue,
expenses, net revenue, ROI, token cost, API cost, infra cost, manual input cost
y revenue source quedan como:

- `value=unknown`;
- `source=not_measured`;
- `evidence_state=missing`;
- `confidence=unknown`.

Budget queda not configured/unknown, y la safety de finance declara:

- no money movement;
- no Stripe live;
- no checkout creation;
- no invoice creation;
- no payment collection;
- no fake revenue;
- no fake costs;
- no fake ROI;
- approval required for money;
- strong approval required for live payments.

Incluye `adaptive_product_builder`:

- `state.mode=preview`;
- `builder_enabled=preview/read_only`;
- `product_generation_enabled=false`;
- `code_generation_enabled=false`;
- `deploy_enabled=false`;
- `stripe_enabled=false`;
- `landing_publish_enabled=false`;
- `external_research_enabled=false`;
- `hermes_dispatch_enabled=false`.

Las stages son Idea, Validación, Blueprint, Código, Landing, Deploy candidate,
Monetización y Medición. Cada stage tiene status preview/future-gated/disabled,
`can_execute=false`, approval metadata, evidence required y notas. La policy
declara que Product Builder Adaptativo no es Template Builder, no clona
plantillas, cada producto necesita razón de existir, success metric y lógica de
monetización, y los productos clonados son fallo. Monetization policy deja
pricing preview only, Stripe live y checkout bajo aprobación fuerte, revenue
real bajo confirmación, projected revenue etiquetado y no fake revenue.

Incluye `frontend_pilot`:

- `mode=read_only_pilot`;
- `dashboard_route=/jarvis`;
- `backend_status_endpoint=/mark-3/dashboard/status`;
- `frontend_can_execute=false`;
- `frontend_can_approve=false`;
- `frontend_can_activate_sensors=false`;
- `frontend_can_move_money=false`;
- `frontend_can_deploy=false`;
- `frontend_can_send_email=false`.

Readiness checks cubren dashboard route, read model, Approval Console, Hermes
Execution, Mission Control, Voice Core, Wake Flow, Camera/Vision, Mobile
Companion, Finance/ROI, Product Builder, Kill Switch, no fake metrics, no
frontend execute, no sensor activation y no POST/PUT/DELETE. Hardening notes
declaran que `npm audit fix` no se ejecuta, dependency hardening queda en PR
separada si toca lockfile/deps, no se esperan cambios de lockfile y frontend
build/full pytest son requeridos antes de merge.

La UI `/jarvis` muestra los tres paneles con guardrails visibles:

- `No fake metrics.`
- `Si no hay evidencia, mostrar unknown.`
- `Revenue confirmado requiere evidencia.`
- `ROI queda unknown sin revenue y costes reales.`
- `No se mueve dinero desde este panel.`
- `Stripe live requiere aprobación fuerte.`
- `Product Builder Adaptativo`
- `No es un Template Builder.`
- `Si dos productos parecen clones, el builder ha fallado.`
- `Deploy real requiere aprobación fuerte.`
- `Stripe/checkout real requiere aprobación fuerte.`
- `Revenue real requiere confirmación.`
- `Pilot read-only`
- `El dashboard mira, no toca.`
- `No POST/PUT/DELETE.`
- `No execute.`
- `No sensores.`
- `Dependency hardening queda para una PR separada.`

No implementa:

- dinero real;
- Stripe live;
- checkout real;
- invoices;
- payment collection;
- productos reales;
- publicación;
- deploy;
- envío de email;
- credenciales;
- red externa;
- sensores;
- frontend file writes;
- Hermes execution;
- fake revenue/cost/ROI;
- dependency hardening o `npm audit fix` en esta PR si requiere lockfile/deps.

PR #152 conserva la separación:

```text
JARVIS gobierna.
Hermes ejecuta.
```

## JARVIS Visual Command Center Pilot

PR #153 cierra un piloto/hardening local del cockpit `/jarvis` como Visual
Command Center read-only. No activa acciones reales; valida que el dashboard
completo carga, lee `GET /mark-3/dashboard/status`, mantiene todos los paneles
esperados y degrada honestamente valores sin evidencia a `unknown`, `disabled`,
`not_connected`, `preview` o `future_gated`.

Backend:

- `jarvis/dashboard_read_model.py` expone
  `visual_command_center_pilot.state.mode=read_only_pilot`.
- `dashboard_route=/jarvis`.
- `status_endpoint=/mark-3/dashboard/status`.
- `backend_read_model_connected=true`.
- `frontend_execution_enabled=false`.
- `approvals_real_enabled=false`.
- `hermes_direct_execution_enabled=false`.
- `voice_real_enabled=false`.
- `camera_real_enabled=false`.
- `mobile_runtime_enabled=false`.
- `money_enabled=false`.
- `deploy_enabled=false`.
- `email_enabled=false`.
- `credentials_enabled=false`.

Required panels:

- Header.
- Voice Core.
- Wake Word Local Safe Flow.
- Mission Control.
- Approval Console.
- Hermes Execution.
- Agent / Module Radar.
- Camera / Vision.
- Mobile Companion.
- Finance / ROI.
- Product Builder Adaptativo.
- Frontend Pilot / Hardening.
- Live Timeline / Audit.
- Kill Switch.

Cada panel declara `expected=true`, source, status, `can_execute=false` y notas.
Los read-only checks cubren no POST/PUT/DELETE, no execute route, no frontend
Hermes call, no tool runner, no sensor activation, no getUserMedia, no
MediaRecorder, no AudioContext capture, no camera capture, no mobile runtime,
no money movement, no Stripe live, no deploy, no email send, no credentials y
no fake metrics.

Frontend:

- `/jarvis` muestra el panel `Visual Command Center Pilot`.
- Muestra `/jarvis`, `/mark-3/dashboard/status` y `read-only pilot`.
- Muestra checklist de panels, checklist de seguridad, limitaciones conocidas,
  pasos para el operador y estado de botones críticos.
- Copia visible: `El dashboard mira, no toca.`, `No se ejecuta Hermes desde el
  frontend.`, `No se activan sensores.`, `No hay approvals reales en esta
  fase.`, `No hay métricas falsas.`, `Los valores sin evidencia se muestran
  como unknown.` y `Dependency hardening queda para una PR separada.`

Docs:

- `docs/jarvis-visual-command-center-pilot.md` documenta que valida el piloto,
  que no valida, como arrancar backend, como abrir `/jarvis`, checklist manual,
  checklist de seguridad, criterios de exito/fallo, findings que requieren PR y
  fuera de alcance.

PR #153 no implementa:

- approvals reales;
- submit real de misión;
- ejecución Hermes;
- voz real;
- wake listener real;
- cámara real;
- mobile runtime;
- dinero, Stripe, checkout;
- deploy;
- email;
- credenciales;
- dependency hardening;
- fake metrics.

PR #153 conserva la separación:

```text
JARVIS gobierna.
Hermes ejecuta.
```

## JARVIS Presence UI + Local System Contract

PR #155 convierte `/jarvis` en la presencia visual local de JARVIS. La ruta no
representa una web SaaS ni un runtime: es la cara/control center del sistema
local que vive en el ordenador de David. El sistema real es el runtime/daemon
local de JARVIS; movil y VPS quedan como clientes o puentes seguros futuros.

Backend:

- `GET /mark-3/dashboard/status` expone `local_system_contract`.
- `local_runtime_daemon_is_system=true`.
- `web_route=/jarvis`.
- `web_route_is_visual_interface_only=true`.
- `frontend_executes_hermes_directly=false`.
- `mobile_and_vps_are_future_clients_or_bridges=true`.
- `real_voice_camera_in_future_prs=true`.
- `jarvis_governs=true`.
- `hermes_executes=true`.

Visual:

- Presence UI como primera experiencia.
- nucleo/orbe central dominante con estados preview: `idle/calmado`,
  `escuchando`, `pensando`, `hablando`, `alerta/riesgo`.
- laterales con informacion esencial solamente: estado general, approvals
  pendientes, escucha/piensa/habla, mision actual, coste/dinero, camara activa
  y riesgo actual.
- `camera placeholder` lateral movible/ampliable visual, sin captura real.
- `smart bar` inferior disabled/preview para escribir, transcripcion temporal,
  respuesta temporal e historial plegado.
- detalles largos en paneles plegados/tabs secundarios, no como experiencia
  principal.

No implementa:

- ejecucion Hermes;
- POST/PUT/DELETE desde `/jarvis`;
- approvals reales;
- mission submit real;
- voz real, STT, TTS o wake listener;
- camara real, getUserMedia, streaming, captura, grabacion o storage;
- movil real ni VPS real;
- dinero, Stripe, deploy, email o credenciales.

PR #155 conserva la separación:

```text
JARVIS gobierna.
Hermes ejecuta.
```

## Local Voice Loop

PR #156 añade una prueba real y controlada de voz en `/jarvis`, sin convertir
la Presence UI en runtime operativo ni duplicar Hermes. La mejora actual añade
conversacion manual continua y refuerza el nucleo central como reactor/orbe
cinematografico: capas, anillos, bloom, particulas sutiles, HUD y movimiento
segun estado/tone.

Backend/read model:

- `GET /mark-3/dashboard/status` expone `local_voice_loop`.
- `local_voice_loop.state.mode=browser_controlled_manual_loop`.
- `activation=explicit_operator_button`.
- `always_listening=false`.
- `manual_continuous_conversation=true`.
- `conversation_active=false` como estado inicial del read model.
- `conversation_timeout_seconds=180`.
- `wake_listening=false`.
- `wake_listening_real_enabled=false`.
- `recording=false`.
- `continuous_recording=false`.
- `wake_listener_enabled=false`.
- `browser_stt_supported=unknown`.
- `browser_tts_supported=unknown`.
- `audio_storage=false`.
- `raw_audio_sent_to_backend=false`.
- `approval_by_voice_enabled=false`.
- `wake_phrase_approval=false`.
- `browser_may_use_external_services=true`, porque SpeechRecognition/TTS
  dependen del navegador.

Frontend `/jarvis`:

- boton de microfono para iniciar conversacion manual continua solo con accion
  manual;
- `SpeechRecognition` / `webkitSpeechRecognition` si el navegador lo soporta;
- `speechSynthesis` para TTS si el navegador lo soporta;
- seleccion preferente de voz en espanol si el navegador la ofrece, con
  fallback visible si no existe una voz buena;
- smart bar con transcripcion temporal local y respuesta local controlada;
- respuesta local mas humana; intent/risk tecnico queda secundario/plegado;
- al terminar de hablar, JARVIS vuelve a escuchar mientras `conversation_active`
  siga activo;
- stop/cancel para cortar escucha, habla y cerrar la conversacion manual;
- estados visuales del nucleo: `idle/calmado`, `escuchando`,
  `transcribiendo`, `pensando`, `hablando`, `error/no disponible`;
- tonos `calmado`, `concentrado`, `alerta`, `intenso` reflejados en clase
  visual y parametros basicos TTS (`rate`, `pitch`, `volume`).
- nucleo visual tipo reactor/orbe con profundidad, glow azul/cian, bloom,
  anillos, particulas y HUD; `alerta/intenso/error` empujan acentos
  naranja/rojo.

Conversational Brain Bridge en `/jarvis`:

- el fallback local ya no hace eco de la transcripcion;
- responde preguntas simples como `¿Me escuchas?` o `¿Qué puedes hacer ahora?`;
- prepara previews de misión/tarea/activo sin ejecutar;
- bloquea credenciales/secretos y declara approval para acciones sensibles;
- muestra `intent_detected`, `risk_level`, `requires_approval`,
  `can_prepare_preview`, `cannot_execute_reason` y
  `suggested_next_action` en detalle plegado;
- no llama LLM externo ni Hermes; la ruta futura debe pasar por
  ApprovalGateway, risk, audit y rollback/stop.

Camara y video local opt-in:

- preview de camara con `getUserMedia` solo tras boton explicito;
- grabacion de video con `MediaRecorder` solo tras boton `Grabar video`;
- indicador visible `REC local`, stop, descarga de blob local y borrado con
  revocacion de URL;
- no graba al cargar, no sube video al backend, no hace streaming externo, no
  captura snapshot automatico y no analiza personas/identidad;
- read model/event stream declaran `browser_local_video_recorder` inactivo por
  defecto y metadata-only;
- el event stream puede superponer `sensor_ledger_state` local con metadata de
  sesiones del navegador, sin POST de media al backend.

Contrato de wake futuro:

- `wake_listening` significa escucha minima para activacion, sin grabacion ni
  transcripcion continua.
- En esta PR `wake_listening=false` y no hay listener persistente real.
- `conversation_active` empieza por activacion manual; aqui si puede haber STT
  de la frase de David para la smart bar.
- `recording=false` sigue significando que no se guarda audio bruto.
- Texto de UI/docs: "JARVIS aun no tiene wake listener persistente real en esta
  PR; la conversacion se activa manualmente. Arquitectura preparada para wake
  phrase sin grabar ni transcribir todo."

No implementa:

- always-listening;
- wake listener persistente;
- wake listening real;
- wake phrase como approval;
- approvals criticos por voz;
- ejecucion Hermes directa desde frontend;
- POST/PUT/DELETE desde `/jarvis`;
- endpoint `/execute`;
- subida o almacenamiento de audio bruto;
- `AudioContext` para capturar audio bruto;
- ejecucion, streaming externo, snapshot automatico o analisis de vision;
- dinero, deploy, email, credenciales, Stripe, produccion;
- camara autonoma o vision real.

Cómo probar:

- abrir `/jarvis` en navegador compatible;
- pulsar el microfono en la smart bar;
- conceder permiso si el navegador lo solicita;
- dictar una orden corta;
- verificar transcripcion, respuesta local, TTS si disponible y estados
  visuales;
- probar stop/cancel;
- en navegador sin STT/TTS, verificar estado `not_supported` o `unavailable`
  visible sin simular exito.

PR #151 conserva la separación:

```text
JARVIS gobierna.
Hermes ejecuta.
```
## PR #158 — Conversational Brain + Voice Session/Wake Architecture

PR #158 formaliza la siguiente base segura:

- Conversational Brain Bridge v2 local/determinista, sin LLM real declarado,
  sin APIs externas, sin memoria automática y sin Hermes dispatch.
- Voice Session Manager read-only con estados mínimos:
  `idle`, `wake_listening_available`, `wake_listening_disabled`,
  `conversation_active`, `listening`, `transcribing`, `thinking`, `speaking`,
  `approval_required`, `cancelled`, `stopped`, `error`.
- Wake Architecture para `openWakeWord` o equivalente, disabled by default,
  `auto_start=false`, `activation_endpoint_enabled=false`, buffer efímero en
  memoria, sin persistencia de audio, sin transcripción previa a activación
  válida, sin approval y sin execution.
- `/mark-3/dashboard/status` expone `conversational_brain`, `voice_session` y
  `wake_architecture`; el event stream agrega `brain_state` y
  `voice_session_state`, metadata-only.
- `/jarvis` muestra respuesta humana breve y estado de sesión de voz/wake, con
  detalles técnicos plegados. No añade mutaciones, `/execute`, approvals reales,
  Hermes directo ni `getUserMedia` automático.

Sigue fuera de alcance: wake listener persistente real, always-on STT, STT/TTS
local backend serio, aprobación real por voz, ejecución Hermes end-to-end y
lectura de secretos/credenciales.

## PR #164 — Persistent Sensor/Voice Audit + Memory Brain v2

Estado: implementado en control-plane local/read-only.

Incluye:

- `PersistentAuditLedger` en `jarvis/persistent_audit.py`.
- `MemoryBrainV2Store` en `jarvis/memory_brain_v2.py`.
- SQLite local opcional bajo `.jarvis/` solo con instancia explicita o
  `JARVIS_LOCAL_STATE_DIR`/`JARVIS_STATE_DIR`.
- Hash-chain metadata-only para voz/sensores/intake/brain/memory/approval.
- Memory lifecycle prepare-only: propose, review, approve, activate,
  deactivate, supersede contradiction, forget/delete metadata.
- Nuevos GET read-only:
  - `/mark-3/audit/status`
  - `/mark-3/memory-brain/status`
  - `/mark-3/memory-brain/preview`
- Dashboard/event stream:
  - `persistent_audit`
  - `memory_brain_v2`
  - `persistent_audit_state`
  - `memory_brain_v2_state`
- `/jarvis` muestra ambos en `Sistemas`, no en la experiencia central.

No incluye ejecucion Hermes, `/execute`, approvals reales desde UI, sensores
nuevos, auto mic/camera, raw audio/frame storage, LLM externo, cloud memory ni
graph/vector DB obligatoria.

Siguiente recomendado: PR #165 consola gobernada de review de memoria + rotacion/export auditado.

Documento: `docs/jarvis-pr-164-persistent-audit-memory-brain-v2.md`.

## PR #165 — Phase 1 Completion: Governed Hermes Execution E2E + Pilot Hardening

Estado: implementado como control-plane local gobernado y piloto de cierre de
Phase 1.

Incluye:

- `Phase1GovernedExecutionControlPlane` en
  `jarvis/phase_1_governed_execution.py`.
- Pipeline real: intake, candidate action, preview, risk classification,
  allowed/requires_approval/denied/unsupported, approval envelope, decision,
  dispatch gobernado, audit persistente, status/event stream y stop/cancel
  metadata.
- Reutilizacion de Hermes/JARVIS existentes: `PolicyEngine`,
  `ApprovalGateway`-compatible envelopes, `Mark3MissionLoop`,
  `Mark3HermesRuntimeBridge`, `ConversationalIntakePipeline`,
  `PersistentAuditLedger` y `MemoryBrainV2Store`.
- Endpoints gobernados:
  - `GET /mark-3/execution/status`
  - `GET /mark-3/phase-1/status`
  - `POST /mark-3/execution/preview`
  - `POST /mark-3/execution/request-approval`
  - `POST /mark-3/execution/approval-decision`
  - `POST /mark-3/execution/dispatch`
  - `POST /mark-3/execution/cancel`
  - `POST /mark-3/execution/stop`
- `/jarvis` muestra approval panel backend-gated real, risk badge, preview,
  what-will/what-will-not, confirmation/readback, audit destination, memory
  influence, stop/cancel y Phase 1 readiness.
- Dashboard/event stream exponen `governed_execution`, `phase_1_completion` y
  `phase_1_state`.
- Persistent Audit queda conectado a eventos reales metadata-only.
- Memory Brain v2 influye solo como contexto explicable, nunca como permiso.
- Voice loop puede iniciar intencion textual manual, pero voz y wake phrase no
  aprueban.

Acciones reales soportadas en cierre Phase 1:

- estado local safe/read-only;
- prepare-only;
- lectura exacta local no sensible mediante bridge Hermes existente con approval
  valido.

Sigue bloqueado o fuera de alcance:

- `/execute`;
- frontend directo a Hermes;
- shell libre;
- comandos arbitrarios;
- `.env`, secretos, credenciales, tokens, passwords, cookies y session material;
- deploy, dinero, Stripe, email, publicacion, dominios y operaciones externas;
- critical double/triple approval configurable;
- wake always-on real;
- audio bruto backend, frames o transcripts completos sensibles.

Recomendacion: Phase 2 debe continuar como macro-PR para Strong Approval v2,
Hermes Action Bridge allowlisted, execution history, stop/rollback contracts y
pilot local con evidencia.

Documentos:

- `docs/jarvis-pr-165-phase-1-completion-governed-execution-pilot.md`
- `docs/jarvis-phase-1-completion-report.md`

## PR #167 - Phase 3 Local Runtime Daemon + Trusted Approval Channels

Estado: implementado como macro-fase local gobernada.

Objetivo cerrado:

- daemon local readiness real sin servicio del sistema;
- tray/local controller readiness sin dependencia pesada;
- trusted approval channels;
- double approval real;
- triple blocked honesto hasta canal adicional;
- stop/rollback observable;
- execution history v2;
- local doctor seguro;
- browser/local pilot;
- Telegram/mobile future bridge disabled.

Endpoints principales:

- `GET /mark-3/phase-3/status`
- `GET /mark-3/local-daemon/status`
- `GET /mark-3/local-daemon/health`
- `POST /mark-3/local-daemon/heartbeat`
- `POST /mark-3/local-daemon/stop-request`
- `POST /mark-3/local-daemon/restart-request`
- `GET /mark-3/trusted-approval-channels/status`
- `POST /mark-3/trusted-approval-channels/verify`
- `POST /mark-3/approval/strong-decision`
- `POST /mark-3/approval/double-decision`
- `POST /mark-3/approval/triple-decision`
- `GET /mark-3/local-doctor/status`
- `GET /mark-3/execution/history/export-preview`

Invariantes:

- no `/execute`;
- no shell libre;
- no frontend directo a Hermes;
- no wake approval;
- no voice approval;
- no auto mic/camera/wake;
- no puertos externos;
- no secrets/env read;
- audit/history metadata-only.

Documentos:

- `docs/jarvis-pr-167-phase-3-local-runtime-daemon-trusted-approvals.md`
- `docs/jarvis-phase-3-local-runtime-daemon-trusted-approval-report.md`
- `docs/jarvis-phase-3-local-runtime-pilot-report.md`

## PR #170 - Phase 5 Local Controller, Trusted Identity, Pairing & Voice Approval

Estado: implementado como fundacion local gobernada, con partes nativas
marcadas honestamente como readiness.

Incluye:

- control plane Phase 5 en
  `jarvis/phase_5_local_controller_trusted_identity_voice_approval.py`;
- controlador local opt-in v1: status, opt-in, start intent, kill switch,
  local-only, no autostart, no background hidden behavior, no external exposure;
- store SQLite local para identidad persistente de dispositivos confiables;
- revocacion persistente: un device revocado queda revocado tras restart;
- pairing local hardened: nonce, challenge exacto, TTL, one-time use, scope
  exacto, binding de device, rate limit, audit y revoke path;
- contrato de voice approval v1: wake phrase no aprueba, transcript fixture,
  trusted device, exact readback, challenge/phrase, scope/cost/action, expiry,
  anti-replay y audit;
- triple approval endurecido con identidad persistente, action id, scope
  fingerprint opcional, canal esperado y verificacion de audit chain;
- notification readiness metadata-only para approval pending, pairing requested,
  device trusted/revoked, action blocked, approval expired y voice accepted/denied;
- script manual/dev local-only:
  `scripts/local/jarvis-local-controller-dev.py`;
- `/jarvis`, dashboard read model y event stream exponen Phase 5 sin crear
  controles de ejecucion directa.

Endpoints principales:

- `GET /mark-3/phase-5/status`
- `POST /mark-3/local-controller/opt-in`
- `POST /mark-3/local-controller/start-request`
- `POST /mark-3/local-controller/kill-switch`
- `POST /mark-3/trusted-devices/import-preview`
- `GET /mark-3/local-pairing/status`
- `POST /mark-3/local-pairing/challenge`
- `POST /mark-3/local-pairing/verify`
- `GET /mark-3/voice-approval/status`
- `POST /mark-3/voice-approval/start`
- `POST /mark-3/voice-approval/decision`
- `GET /mark-3/notifications/status`

Invariantes:

- no `/execute`;
- no shell libre;
- no frontend directo a Hermes;
- no Telegram/mobile remote execution;
- no native tray fake;
- no autostart;
- no public bind;
- no wake phrase approval;
- no raw audio stored by default;
- memory never grants permission;
- pairing never bypasses ApprovalGateway or calls Hermes.

Real vs readiness:

- Real: local contracts, SQLite identity, pairing challenge verification,
  revocation persistence, voice transcript approval gates, triple persistent
  identity gates, audit events, dashboard/UI exposure.
- Readiness: native tray, OS notifications, Telegram/mobile notifications,
  real STT/VAD/TTS/wake engine, hardware-backed device attestation.

Documento:

- `docs/jarvis-pr-170-phase-5-local-controller-trusted-identity-voice-approval.md`
- `docs/jarvis-phase-5-local-controller-trusted-identity-voice-approval-report.md`

## PR #171 - Phase 6 Real Voice, Wake, Memory & Sensor Runtime

Estado: implementado como piloto local gobernado, con proveedores nativos
marcados honestamente como readiness salvo contratos/manual fixtures.

Incluye:

- registro `VoiceProviderRegistry` para browser STT/TTS, faster-whisper,
  whisper.cpp, Silero VAD, openWakeWord, Piper y Wyoming;
- diagnostico honesto de disponibilidad: no fake readiness, no instalaciones,
  no descargas de modelos y no llamadas externas por defecto;
- `VoiceSessionManagerV2` con estados idle/listening/transcribing/thinking/
  speaking/awaiting_approval/awaiting_spoken_challenge/cancelled/error;
- sesiones manual push-to-talk, wake-start, timeout, cancelacion, stop global y
  transcript metadata-only/redacted;
- spoken approval v2 sobre Phase 5: `voice_session_id` explicito requiere
  sesion Phase 6 activa en servidor; el modo legacy/direct sin id mantiene
  compatibilidad PR170 sin simular microfono real; trusted device, exact
  readback, challenge, anti-replay, expiracion, frases espanolas y limites
  hablados siguen obligatorios;
- `WakeRuntimeOptIn` opt-in/manual fixture: wake abre sesion pero nunca aprueba
  ni ejecuta;
- `MemoryBrainV3` sobre Memory Brain v2 con review, compaction preview,
  influence explanation, provenance/confidence/sensitivity y sin permisos;
- `SensorRuntimeOptIn` metadata-only para microfono, camara, screen context,
  audio/video recording y wake, con opt-in, indicador, stop/cancel y delete;
- `/jarvis`, dashboard read model y event stream exponen Phase 6 sin raw audio,
  frames, secretos ni controles directos de Hermes.

Endpoints principales:

- `GET /mark-3/phase-6/status`
- `POST /mark-3/phase-6/stop-global`
- `GET /mark-3/voice-providers/status`
- `GET /mark-3/voice-session-v2/status`
- `POST /mark-3/voice-session-v2/start`
- `POST /mark-3/voice-session-v2/transition`
- `POST /mark-3/voice-session-v2/cancel`
- `GET /mark-3/wake-runtime/status`
- `POST /mark-3/wake-runtime/opt-in`
- `POST /mark-3/wake-runtime/fixture`
- `GET /mark-3/sensor-runtime/status`
- `POST /mark-3/sensor-runtime/opt-in`
- `POST /mark-3/sensor-runtime/start`
- `POST /mark-3/sensor-runtime/stop`
- `POST /mark-3/sensor-runtime/delete`
- `GET /mark-3/memory-brain-v3/status`
- `GET /mark-3/memory-brain-v3/review`
- `GET /mark-3/memory-brain-v3/compaction-preview`
- `GET /mark-3/memory-brain-v3/influence`

Invariantes:

- no `/execute`;
- no shell libre;
- no frontend directo a Hermes;
- no proveedor de voz marcado ready sin deteccion/configuracion real;
- no hidden mic/camera;
- no continuous transcription por defecto;
- no raw audio/video storage por defecto;
- wake phrase no aprueba;
- voice no baja riesgo;
- memoria nunca concede permisos;
- sensores y grabacion empiezan off y requieren opt-in visible.

Real vs readiness:

- Real: contratos y diagnosticos de proveedor, sesiones de voz v2 en memoria,
  wake manual fixture opt-in, spoken approval por transcript gobernado, Memory
  Brain v3 wrapper, sensor opt-in metadata-only, dashboard/UI/event stream.
- Readiness: openWakeWord, Silero VAD, whisper.cpp, faster-whisper, Piper y
  Wyoming no se ejecutan automaticamente; requieren modelos/binarios/config
  explicitos y validacion manual local.

Documento:

- `docs/jarvis-pr-171-phase-6-real-voice-wake-memory-sensor-runtime.md`

## PR #172 - Phase 7 Governed Actions, Browser, Filesystem, GitHub & Sandbox

Estado: implementado como piloto local gobernado para acciones utiles, con
browser marcado honestamente como readiness y sandbox declarado como guarded
local command runner, no OS-level sandbox.

Incluye:

- control plane Phase 7 en `jarvis/phase_7_governed_actions.py`, montado sobre
  Phase 5/Phase 2 sin crear otro Hermes;
- Action Catalog v2 con `action_id`, titulo, categoria, riesgo, approval,
  allowed inputs, side effects, flags filesystem/network/GitHub/browser/sandbox,
  stop/rollback, dry-run, audit, voice approval eligibility y default state;
- filesystem adapter real para read safe text, list directory metadata y
  write safe project file con diff preview, approval y backup-before-overwrite;
- path traversal, home-wide paths, symlinks, out-of-root access, `.env`,
  secrets, tokens, private keys y credentials bloqueados por defecto;
- Git/worktree adapter real read-only para status, worktree status, changed
  files y diff summary con fixed argv y sin GitHub API/network;
- branch name y PR description prepare-only; branch creation, commit, push,
  open PR y merge siguen disabled/dry-run-only en este workflow;
- browser adapter v1 como Playwright-compatible plan/readiness: open URL plan,
  screenshot metadata, form-fill dry-run y click/submit plan strong-gated sin
  hidden browser, credentials, purchase, posting ni external side effects;
- sandbox execution v1 como command IDs allowlisted con `shell=False`,
  sanitized env, timeout, working directory allowlist, stdout/stderr redaction y
  no inherited secrets;
- preflight v1 con findings redacted, severity, blocking reason, approval
  recommendation y audit metadata-only;
- Phase 5/6 spoken approval integrado para acciones elegibles: trusted
  non-revoked device, active session/readback/challenge/scope/expiry/
  anti-replay/audit; wake phrase y memory no aprueban;
- `/mark-3/phase-7/status`, dashboard read model, event stream y drawer
  `/jarvis` exponen Phase 7 sin controles directos Hermes ni secretos.

Endpoints principales:

- `GET /mark-3/phase-7/status`
- `GET /mark-3/execution/action-catalog`
- `POST /mark-3/execution/preview`
- `POST /mark-3/execution/request-approval`
- `POST /mark-3/execution/approval-decision`
- `POST /mark-3/execution/dispatch`
- `GET /mark-3/dashboard/status`
- `GET /mark-3/dashboard/events`

Invariantes:

- no `/execute`;
- no shell libre;
- no frontend directo a Hermes, GitHub ni filesystem;
- no hidden filesystem writes;
- no secret reads by default;
- no credential storage;
- no hidden browser;
- no arbitrary browser actions;
- no money, Stripe live, deploy, email, purchase, publish or production action;
- no commit/push/PR/merge by JARVIS in this workflow;
- no fake browser automation;
- no fake sandbox or fake rollback;
- memory never grants permission;
- wake phrase never approves.

Real vs readiness:

- Real: catalog classification, safe filesystem read/list/write with backup,
  preflight scanning/redaction, read-only git helpers, branch/PR text prep,
  guarded command IDs, voice approval gates, audit/dashboard/event stream/UI
  visibility.
- Readiness: browser execution is plan-only, delete is dry-run-only, branch
  creation/worktree mutation is disabled, sandbox is not OS-level isolation.

Documento:

- `docs/jarvis-pr-172-phase-7-governed-actions-browser-filesystem-github-sandbox.md`

## PR #173 - Phase 8 Governed Remote Channels, Deploy, Email & Payments

Estado: implementado como piloto gobernado prepare-only para canales remotos,
deploy, email, pagos y budget guard. No anade ejecucion remota libre ni llama
providers externos.

Incluye:

- control plane Phase 8 en `jarvis/phase_8_governed_remote_external_ops.py`;
- remote channel registry v1 para Telegram, mobile/PWA, local controller
  notifications y future remote approval center;
- pairing remoto sobre identidad Phase 5 con trusted device binding,
  revocacion, scope, expiracion, challenge, anti-replay y audit;
- remote kill switch para bloquear notificaciones/intentos remotos;
- Telegram readiness v1 con deteccion de token/config sin exponer valores,
  disabled-by-default, webhook/polling contract y sin bot autostart;
- mobile approval center readiness v1 como preview/readback/challenge only;
- deploy candidate model provider-agnostic con proyecto/app redacted,
  ambiente, target, build/diff summary, secret names checklist, cost estimate,
  rollback plan, risk y approval;
- email draft/candidate con recipients redacted, body/subject preview,
  attachment metadata only, identity-use warning, campaign checklist y send
  disabled;
- Stripe/payment candidate con test/live/unknown readiness sin exponer keys,
  product/price candidate, amount/currency, recurring flag, live blocked y no
  money movement;
- revenue event model que separa projected y confirmed revenue; confirmed
  requiere evidence/source y fake revenue queda rechazado;
- budget guard v1 con monthly budget, per-action max, unknown/over-limit
  blocking y budget consumed solo por evidence confirmada;
- external operation envelope v1 con operation id, category, provider, actor,
  channel, risk, side effects, cost, approval, readback, rollback/compensation,
  status, audit id, expiration, challenge y evidence;
- voice approval readiness para external ops elegibles solo con trusted device,
  active session, exact readback/challenge, scope, expiracion y audit;
- dashboard/event stream y drawer `/jarvis` con Phase 8 sin secretos ni
  controles directos Hermes;
- script manual `scripts/jarvis_phase8_telegram_pilot.py` que imprime readiness
  redacted y no inicia bot.

Endpoints principales:

- `GET /mark-3/phase-8/status`
- `GET /mark-3/remote-channels/status`
- `GET /mark-3/telegram-readiness/status`
- `GET /mark-3/mobile-approval-center/status`
- `POST /mark-3/remote-channels/pairing/challenge`
- `POST /mark-3/remote-channels/pairing/verify`
- `POST /mark-3/remote-channels/revoke`
- `POST /mark-3/remote-channels/kill-switch`
- `POST /mark-3/remote-channels/approval-intent`
- `GET /mark-3/external-operations/status`
- `POST /mark-3/external-operations/prepare-deploy`
- `POST /mark-3/external-operations/prepare-email`
- `POST /mark-3/external-operations/prepare-payment`
- `POST /mark-3/external-operations/revenue-event`
- `POST /mark-3/external-operations/budget-guard`
- `POST /mark-3/external-operations/voice-approval-readiness`

Invariantes:

- no `/execute`;
- no shell libre;
- no frontend directo a Hermes;
- remote channels nunca llaman Hermes directamente;
- remote execution disabled by default;
- no public internet exposure by default;
- no hidden remote listener;
- no Telegram bot autostart;
- no token/secret value exposed in API, audit, UI or tests;
- no production deploy by default;
- no DNS changes;
- no provider calls or secret reads;
- no email send or contact scraping;
- no Stripe live charge, checkout, payout, refund or money movement;
- no fake provider success, fake rollback or fake revenue;
- memory never grants permission;
- wake phrase never approves.

Real vs readiness:

- Real: deterministic readiness detection, Phase 5-backed remote pairing,
  revocation, kill switch state, metadata-only audit, prepare-only envelopes,
  budget/revenue validation, dashboard/event stream/UI exposure, manual
  Telegram readiness script.
- Readiness: Telegram runtime, standalone mobile approval center, provider
  deploy/email/payment execution, durable pending envelope storage, real
  rollback/compensation and final remote ApprovalGateway bridge.

Documento:

- `docs/jarvis-pr-173-phase-8-governed-remote-deploy-email-payments.md`

## PR #174 - Phase 9 Autonomous Product Operator, Money Engine & Self-Improvement

Estado: implementado como control plane gobernado prepare-only para operar
misiones pequenas de producto/negocio bajo control de David. No anade un nuevo
runtime, no duplica Hermes, no crea un SaaS publico y no habilita ejecucion
externa por defecto.

Incluye:

- control plane Phase 9 en `jarvis/phase_9_product_operator.py`;
- autonomous product mission envelope v1 con `mission_id`, title, goal,
  expected outcome, target user/customer, hypothesis, success metric, budget,
  time limit, scope, allowed/forbidden actions, approval, risk, status,
  evidence, stop conditions, audit id y expiration;
- rechazo de misiones sin scope/budget/time/stop conditions/expiration,
  approve-all-forever, unlimited authority y requests falsas/ilegales;
- Product Builder v1 para preparar brief, problem statement, customer, value
  proposition, competitor notes, landing structure, MVP checklist, stack,
  build plan, asset package, scaffold plan, deploy/email/payment candidates,
  pricing y launch checklist;
- integracion Phase 7 para previews `filesystem.file.write_safe` cuando hay
  `local_project_path`, sin writes directos desde Phase 9;
- integracion Phase 8 para candidatos deploy/email/payment, sin provider calls;
- Money/ROI Engine v1 con opportunity score, upside, effort, cost,
  time-to-market, confidence, risks, dependencies, David-hours y decision
  state;
- separacion estricta entre projected, confirmed, gross, fees, costs, net,
  evidence/source y confidence;
- Revenue Tracker v1 con confirmed revenue solo cuando hay evidence/source;
- Budget Guard v2 para global monthly product budget, per-mission budget,
  per-action limit, provider estimate, unknown-cost blocking y hard stop;
- Experiment Planner v1 prepare-only para landing, Reddit draft, cold email
  draft, research checklist, directory/listing, manual sales y local prototype
  tests;
- Self-Improvement Proposal System v1 que prepara patch plan/tests/PR
  description pero bloquea debilitar PolicyEngine, ApprovalGateway, audit,
  tests, permisos, self-merge y self-deploy;
- Operator Scheduler/Report v1 manual/readiness-only, sin scheduler oculto;
- Product Operating Loop v1 stoppable:
  observe -> propose -> plan -> prepare_assets -> request_approval ->
  execute_allowed_local_actions -> gather_evidence -> report -> learn ->
  propose_next_step;
- voice approval readiness para operaciones de producto elegibles solo con
  trusted device, active voice session, exact readback, challenge, scope,
  expiration y audit;
- dashboard, event stream y `/jarvis` exponen Phase 9 como cockpit read-only,
  no como consola de ejecucion.

Endpoints principales:

- `GET /mark-3/phase-9/status`
- `GET /mark-3/product-operator/status`
- `POST /mark-3/product-operator/missions`
- `POST /mark-3/product-operator/builder`
- `POST /mark-3/product-operator/roi-decision`
- `POST /mark-3/product-operator/experiments`
- `POST /mark-3/product-operator/revenue-events`
- `GET /mark-3/product-operator/revenue-summary`
- `POST /mark-3/product-operator/budget-guard`
- `POST /mark-3/product-operator/self-improvement`
- `POST /mark-3/product-operator/reports`
- `POST /mark-3/product-operator/operating-loop`
- `POST /mark-3/product-operator/voice-approval-readiness`

Invariantes:

- no unlimited mission;
- no approve-all-forever;
- no memoria como permiso o presupuesto;
- no wake phrase approval;
- no frontend directo a Hermes;
- no `/execute` ni shell libre;
- no external publication, deploy production, DNS, email send, scraping,
  checkout, charge, payout, refund o money movement por defecto;
- no fake launch, fake customers, fake revenue, fake providers o fake rollback;
- no self-merge, self-deploy, commit, push, PR o merge por Phase 9;
- operaciones sensibles siguen requiriendo PolicyEngine, ApprovalGateway,
  budget guard, readback/challenge, stop/rollback plan y audit.

Real vs readiness:

- Real: validacion deterministica de product mission envelopes, Product Builder
  prepare-only, previews Phase 7, candidatos Phase 8, ROI scoring,
  revenue tracker evidence-first, budget guard v2, experiment planner,
  self-improvement proposals, reports manuales, operating-loop contract,
  audit/dashboard/event stream/UI.
- Readiness: persistencia durable de estado de producto, scheduler automatico,
  provider execution, launch/deploy/email/payment live, rollback real,
  ApprovalGateway handoff final y test-mode provider pilot.

Documento:

- `docs/jarvis-pr-174-phase-9-autonomous-product-operator-money-engine-self-improvement.md`
