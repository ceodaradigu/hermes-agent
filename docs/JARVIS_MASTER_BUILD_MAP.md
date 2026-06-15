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
- Multi-device runtime.
- Trusted devices.
- Strong approval desde cualquier dispositivo autorizado.
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
