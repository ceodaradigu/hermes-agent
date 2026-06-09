# JARVIS Master Build Map

JARVIS es un sistema operativo personal de IA para David, privado/no SaaS, que convierte intención en misión, misión en acciones, acciones en activos, activos en medición y medición en mejora/monetización.

Este documento es el mapa maestro operativo para construir JARVIS por fases sin olvidar piezas críticas. No implementa código, runtime, endpoints, router, scripts, CI, dependencias, integraciones externas ni conexión nueva con Hermes/MissionControl.

**JARVIS_MASTER_BUILD_MAP.md is the source of truth for master phase names and order.**

Las foundations prepare-only pueden completarse antes que el objetivo runtime completo de una fase. Una extensión transversal, como Operator Console, no crea ni sustituye una fase maestra.

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

Límites actuales:

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

Estado: siguiente fase maestra recomendada; foundation pendiente.

- Objetivo: permitir "mira conmigo" sin convertir la cámara en vigilancia.
- Incluye: camera session, indicador visible camera-active, "no mires" hard stop, privacy redaction, no recording by default, no face/person analysis by default, document/screen awareness, useful alerts y audit of camera sessions.
- Permite: ayudar con documentos, pantallas, objetos o contexto visual explícito.
- NO permite: grabación continua invisible, análisis de personas por defecto ni envío de video sensible sin approval.
- Criterios mínimos: inicio/fin auditado, indicador visible, stop inmediato, redacción de privacidad y no-retention por defecto.
- Monetización: puede ayudar a revisar assets, pantallas, diseños, documentos y operaciones.
- Approval: cámara continua, exportación, publicación o análisis sensible requiere strong approval.

### Phase H - Multi-device Runtime

- Objetivo: coordinar desktop, móvil, reloj, gafas, tablet, servidor y workers sin varios cerebros.
- Incluye: device registry, trusted devices, revoke device, approval from trusted devices, device capability model, sync state y notification routing.
- Permite: presencia distribuida, handoff, aprobaciones y estado sincronizado.
- NO permite: que un dispositivo gobierne, ejecute solo o cree approve-all-forever.
- Criterios mínimos: identidad de dispositivo, revocación, capacidades declaradas, expiración y audit correlation id.
- Monetización: reduce fricción para aprobar ventas, publicaciones, gastos y misiones largas.
- Approval: trusted device no sustituye strong approval; solo habilita canal autorizado.

### Phase I - Sandbox Execution

- Objetivo: ejecutar comandos y tools con aislamiento y límites.
- Incluye: safe command executor, filesystem scope guard, allowlist, no secrets scanner, rollback plan, execution audit, dry-run required before execution y no production without strong approval.
- Permite: pruebas, builds y comandos acotados bajo policy.
- NO permite: host escape, secretos, producción, red amplia o installs silenciosas.
- Criterios mínimos: scope de filesystem, límites de tiempo/red, scanner de secretos, dry-run previo y rollback documentado.
- Monetización: permite construir y validar assets sin poner en riesgo repos, credenciales o producción.
- Approval: ejecución con side effects requiere approval; producción, dinero y credenciales requieren strong approval.

### Phase J - Tool Adoption Pipeline

- Objetivo: evaluar herramientas externas antes de adoptarlas.
- Incluye: discover tool, license check, repo health, dependency risk, sandbox install proposal, spike runner, value measurement, keep/rollback decision, Graphify/CodeGraph/Open Design as candidates y no silent core dependency.
- Permite: investigar y medir herramientas.
- NO permite: instalar, ejecutar o convertir en dependencia core sin aprobación y medición.
- Criterios mínimos: licencia, permisos, dependencias, seguridad, artefactos, rollback y medición de tiempo/tokens/errores/valor.
- Monetización: adopta solo herramientas que mejoran velocidad, calidad o revenue.
- Approval: install/spike requiere approval; core dependency o ejecución con permisos amplios requiere strong approval.

### Phase K - Asset Factory / Web Builder

- Objetivo: transformar oportunidades en activos digitales medibles.
- Incluye: landing generator, website generator, offer builder, copy generator, design assets, templates, demo builder, GitHub PR automation y Open Design evaluation when useful.
- Permite: crear borradores, demos, landings, ofertas y assets revisables.
- NO permite: publicar, gastar, usar identidad ni prometer ingresos.
- Criterios mínimos: hipótesis, público, métrica, coste, riesgo, tracking plan y condición de cierre.
- Monetización: convierte misiones en activos reutilizables con vía de revenue.
- Approval: publicar, comprar dominio, conectar cuenta externa o usar identidad requiere strong approval.

### Phase L - Deploy & Publishing

- Objetivo: llevar assets a preview y producción con control.
- Incluye: preview deploy, Vercel/Render adapters, env guard, domain checklist, production approval, rollback deploy y publication audit.
- Permite: previews revisables y publicación controlada.
- NO permite: producción automática, secretos en logs ni dominios/cuentas sin scope.
- Criterios mínimos: diff/config visible, env guard, rollback, auditoría y checklist de dominio.
- Monetización: habilita experimentos públicos y productos.
- Approval: producción, dominios, identidad y publicación real requieren strong approval.

### Phase M - Communication & Sales

- Objetivo: preparar y gestionar comunicación comercial sin envíos silenciosos.
- Incluye: lead model, email draft builder, message approval, CRM simple, outreach tracker, reply tracker, Gmail/SMTP bridge later y no send without strong approval.
- Permite: leads, borradores, seguimiento y respuestas propuestas.
- NO permite: enviar emails, mensajes o representar a David sin aprobación.
- Criterios mínimos: destinatario, canal, texto exacto, identidad usada, objetivo, riesgo y audit.
- Monetización: convierte activos en conversaciones, leads y ventas.
- Approval: cualquier envío externo como David requiere strong approval.

### Phase N - Payments & Revenue

- Objetivo: medir y operar revenue sin confundir proyección con dinero real.
- Incluye: Stripe/Gumroad adapter, checkout proposal, pricing model, expense tracker, confirmed vs projected revenue, net revenue calculator, ROI tracker, budget guard advanced y no payments without strong approval.
- Permite: proponer precios, checkouts, métricas y tracking financiero.
- NO permite: crear pagos, mover dinero, activar cobros o prometer ingresos garantizados.
- Criterios mínimos: revenue projected/confirmed, gross revenue, expenses, net revenue, coste máximo y audit.
- Monetización: cierra el ciclo de ingresos medibles.
- Approval: pagos, checkouts, gastos, contratos y datos financieros requieren strong approval.

### Phase O - Daily Operator / Scheduler

- Objetivo: operar el día con planes, reportes y colas de aprobación.
- Incluye: daily mission loop, morning plan, evening report, stop conditions, retry logic, notifications, approval queue y weekly review.
- Permite: planificar, agrupar, recordar, preparar y reportar.
- NO permite: autoejecución sensible ni watchers con side effects.
- Criterios mínimos: horarios claros, stop conditions, retries limitados, cancel/pause/resume y digest auditable.
- Monetización: mantiene cadencia sobre assets, leads, revenue y aprendizaje.
- Approval: scheduler puede proponer; ejecutar acciones sensibles requiere approval o strong approval.

### Phase P - Continuous Learning / Tech Radar

- Objetivo: mantener JARVIS actualizado sin auto-modificación.
- Incluye: tech radar, relevance filter, contrarian review, proposal creation, approval workflow, PR planner, no auto-update, no auto-install y no auto-deploy.
- Permite: investigar, filtrar, proponer y planificar PRs.
- NO permite: instalar, modificar runtime, cambiar prompts o desplegar automáticamente.
- Criterios mínimos: propuesta con impacto, riesgos, dependencias, tests, rollback y decisión recomendada.
- Monetización: prioriza novedades que ahorran tiempo, reducen errores o aumentan revenue.
- Approval: aplicar cambios, instalar dependencias o modificar runtime requiere approval; producción/credenciales requieren strong approval.

### Phase Q - Personal OS / Environment Intelligence

- Objetivo: coordinar contexto, atención, entorno y rutinas de David.
- Incluye: PC state awareness, calendar/email/doc awareness with approval, local files scope, context switching, attention protection, environment signals, personal routines y energy/focus support.
- Permite: daily state, modos, atención, notificaciones y contexto autorizado.
- NO permite: vigilancia opaca, inferencias sensibles sin consentimiento ni mezcla personal/profesional indebida.
- Criterios mínimos: consentimiento por fuente, separación de contextos, privacidad, modo invitado y razones visibles.
- Monetización: protege foco humano y prioriza acciones de mayor ROI.
- Approval: leer fuentes sensibles o cruzar datos privados requiere approval; enviar/actuar requiere strong approval si aplica.

### Phase R - Advanced Personalization / User Model

- Objetivo: aprender cómo piensa, habla, decide y monetiza David de forma explícita.
- Incluye: David understanding, preferences, speech patterns, business goals, contrarian mode, memory proposals, approved/reversible memory, uncertainty handling y no opaque learning.
- Permite: memoria aprobada, tono adaptativo, preferencias y mejores decisiones.
- NO permite: aprendizaje opaco, manipulación, memoria como permiso ni certezas privadas inventadas.
- Criterios mínimos: proposal, review, approve, activate, deactivate, audit, reversión y manejo de incertidumbre.
- Monetización: mejora priorización, copy, producto, ventas y foco.
- Approval: memoria puede orientar; nunca autoriza acciones sensibles.

### Phase S - Future/Moonshot Layer

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

## Orden Inmediato Recomendado

Orden conceptual actualizado tras PR #99:

1. PR #79 - Mission Approval Bridge v1. Mergeado.
2. PR #80 - Mission Safety Baseline Gate v1. Mergeado.
3. PR #81 - Complete Phase B remaining bridges/guards. Mergeado.
4. PR #82 - Hermes Runtime Bridge Contract. Mergeado.
5. PRs #93-#94 - Command Center foundation. Mergeadas.
6. PRs #95-#97 - Voice Companion foundation. Mergeadas.
7. PR #98 - Mobile Companion foundation. Mergeado.
8. PR #99 - Operator Console Foundation como extensión de Command Center / operator layer. Mergeado; no es Phase G maestra.
9. Siguiente fase maestra recomendada - Phase G: Ambient Vision / Camera Companion.

Los números pueden ajustarse si el repo cambia su secuencia, pero el orden conceptual debe mantenerse: approvals, safety, policy bridge y budget guard antes de revenue execution, y Hermes bridge antes de ejecución real.
