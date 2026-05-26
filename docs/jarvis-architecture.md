# JARVIS Architecture (MVP Foundation)

## Qué es JARVIS
JARVIS es un sistema personal de agentes IA para uso exclusivo de David, orientado a crear activos digitales y automatizaciones bajo supervisión humana.

## Qué papel tiene Hermes
Hermes Agent actúa como runtime interno de ejecución (conversación + tools). JARVIS añade una capa ligera de integración y gobernanza, sin reescribir Hermes ni alterar su comportamiento base.

## Qué es Mission Control (MVP)
Mission Control es una capa de orquestación por encima de `tasks/runtime`.

- Mantiene misiones y pasos en memoria (sin DB).
- Evalúa **cada step** con `PolicyEngine` antes de invocar Hermes.
- Ejecuta Hermes solo cuando policy devuelve `allowed`.
- Mantiene endpoints `/tasks` existentes intactos.

## API Mission Control (sin UI, sin WebSocket)
- `POST /missions`
- `GET /missions`
- `GET /missions/{mission_id}`
- `POST /missions/{mission_id}/steps`
- `POST /missions/{mission_id}/cancel`

## Reglas de ejecución de steps
1. **denied**
   - no ejecuta Hermes;
   - step queda `denied`;
   - `mission.status = blocked`.

2. **requires_approval**
   - no ejecuta Hermes;
   - crea `ApprovalRequest`;
   - step queda `pending_approval` con `approval_request_id`;
   - `mission.status = pending_approval`.

3. **allowed**
   - ejecuta Hermes exactamente una vez por step;
   - step queda `completed` si no hay error.

4. Si existe cualquier step `pending_approval`, la misión **no** debe quedar en `running`.

## Fuera de alcance MVP
- Sin persistencia en base de datos.
- Sin endpoint de approve/reject.
- Sin interfaz de usuario.
- Sin WebSocket.

## Roadmap futuro (Command Center)
Para la fase posterior al Command Center base, ver la propuesta de **Dominion / Overdrive Mode** en `docs/roadmap/pr-future-overdrive-dominion-mode.md` (capa visual/conversacional futura, sin cambios al modelo de seguridad).

JARVIS North Star: principio rector del proyecto para que JARVIS evolucione de asistente de comandos a operador personal de David, aprendiendo progresivamente cómo piensa, decide, habla, prioriza y monetiza, manteniendo privacidad, pensamiento crítico, incertidumbre explícita y ApprovalGateway para acciones sensibles en `docs/jarvis-north-star.md`.

También ver `docs/roadmap/pr-future-voice-runtime-adapter.md` para el roadmap de integración de voz mediante adapters desacoplados, manteniendo `PolicyEngine`, `ApprovalGateway` y control humano en acciones sensibles.

Always-on local voice runtime: diseño futuro para wake word, STT multidioma, TTS multidioma, reproducción local, frontend opcional, autoarranque opt-in, modos de escucha y ApprovalGateway obligatorio para acciones sensibles en `docs/roadmap/always-on-local-voice-runtime.md`.

David Understanding Profile: capa futura para que JARVIS aprenda progresivamente cómo piensa, decide, habla, prioriza y monetiza David, manteniendo privacidad, transparencia, aclaraciones cuando haya baja confianza y ApprovalGateway para acciones sensibles.

User Understanding persistent memory design: diseño futuro para pasar de feedback temporal revisado a memoria persistente aprobada, auditable y reversible, manteniendo privacidad, ApprovalGateway, PolicyEngine y la North Star en `docs/roadmap/user-understanding-persistent-memory.md`.

JARVIS Continuous Learning System: diseño futuro para radar tecnológico semanal, filtrado de relevancia, revisión contrarian, propuestas de aprendizaje, aprobación humana, PRs y tests antes de aplicar cambios. Ver `docs/roadmap/jarvis-continuous-learning-system.md`.

User Understanding memory proposals smoke test: guía para validar el flujo local memory-clear → memory-propose-from-feedback → memory-review → memory-approve → transcript sin cambio → memory-disable → memory-clear usando el CLI, sin persistencia ni aplicación al router/runtime, en `docs/integrations/user-understanding-memory-proposals-smoke-test.md`.

User Understanding memory snapshot smoke test: guía para validar el flujo local memory-clear → memory-propose-from-feedback → memory-snapshot → memory-clear → memory-snapshot-import → memory-proposals → transcript sin cambio, sin persistencia en disco ni aplicación al router/runtime, en `docs/integrations/user-understanding-memory-snapshot-smoke-test.md`.

User Understanding local persistence design: diseño futuro para persistencia local opt-in de memory snapshots, con rutas propuestas bajo `.jarvis`, auditoría, backups, borrado reversible, bloqueo de secretos y sin aplicación automática al router/runtime, en `docs/roadmap/user-understanding-local-persistence-design.md`.

User Understanding save/load local smoke test: guía para validar el flujo completo memory-propose-from-feedback → memory-save-local → memory-clear → memory-load-local → memory-proposals → transcript sin cambio, en `docs/integrations/user-understanding-memory-save-load-local-smoke-test.md`.

User Understanding memory activation smoke test: guía para validar memory-propose-from-feedback → memory-review → memory-approve → memory-activate → transcript cambia → sensitive boundary gana → memory-deactivate revierte, en `docs/integrations/user-understanding-memory-activation-smoke-test.md`.

User Understanding load-local approval activation smoke test: guía para validar save-local → clear runtime → load-local → review → approve → activate → transcript cambia, con sensitive boundary ganando, en `docs/integrations/user-understanding-memory-load-approve-activate-smoke-test.md`.

JARVIS local memory quickstart: guía para usar memoria local de forma explícita y principio de interacción natural sin frases rígidas, en `docs/integrations/jarvis-local-memory-quickstart.md`.

JARVIS local memory quickstart manual smoke test: checklist documental para ejecutar manualmente el quickstart como smoke test reproducible, sin autoload, sin autoejecucion, sin tareas reales y sin afirmar validacion hasta que David pegue salida real de terminal, en `docs/integrations/jarvis-local-memory-quickstart-smoke-test.md`.

JARVIS conversational runtime natural design: diseño futuro para que JARVIS evolucione desde comandos rígidos hacia una capa conversacional contextual, crítica y segura, sin autoejecución peligrosa y manteniendo `PolicyEngine`, `ApprovalGateway` y sensitive boundary por encima, en `docs/roadmap/pr-53-conversational-runtime-natural-design.md`.

JARVIS natural runtime contracts: contrato documental para futuras implementaciones del modelo de respuesta natural/contextual, con inputs, outputs, estados, matriz tono/riesgo, baja confianza, acciones sensibles, pensamiento contrarian y criterios de aceptación, en `docs/roadmap/pr-54-natural-runtime-contracts.md`.

JARVIS future capabilities backlog: vision map documental de 70 capacidades futuras y moonshots, con clasificacion por riesgo, modo probable, approval, monetizacion y dependencias como Hermes, mobile, server/hybrid, Money Engine y Asset Factory, en `docs/roadmap/jarvis-future-capabilities-backlog.md`.

Hermes inside JARVIS integration contract: contrato documental para usar Hermes como runtime/engine interno de JARVIS solo mediante adapter/control layer, despues de `PolicyEngine`, `ApprovalGateway` cuando aplique, sensitive boundary y auditoria, en `docs/roadmap/pr-56-hermes-inside-jarvis-contract.md`.

JARVIS deployment modes contract: contrato documental para futuros Local Mode, Server Mode y Hybrid Mode, manteniendo un unico `PolicyEngine`, un unico `ApprovalGateway`, Hermes detras de JARVIS control layer y sin exponer JARVIS directamente a internet sin auth/audit, en `docs/roadmap/pr-57-deployment-modes-contract.md`.

JARVIS mobile voice command and approval contract: contrato documental para que el movil sea una interfaz remota segura de voz/texto/aprobacion mediante JARVIS Gateway, `PolicyEngine`, `ApprovalGateway`, auditoria y limites sensibles, sin llamar a Hermes directo ni afirmar app movil/wake word implementados, en `docs/roadmap/pr-58-mobile-voice-command-approval-contract.md`.

JARVIS restriction registry and policy override contract: contrato documental para explicar restricciones en lenguaje humano, permitir overrides temporales/reversibles solo cuando sea seguro y mantener `PolicyEngine`, `ApprovalGateway`, auditoria y hard boundaries por encima, en `docs/roadmap/pr-59-restriction-registry-policy-override-contract.md`.

JARVIS Code Intelligence / CodeGraph evaluation contract: contrato documental para evaluar CodeGraph como herramienta local/opcional candidata para reducir exploracion ciega del codebase, tool calls, tokens y tiempo, sin instalarlo, ejecutarlo ni adoptarlo, en `docs/roadmap/pr-60-codegraph-evaluation-contract.md`.

JARVIS Home / Voice / Sensor Hardware Layer contract: contrato documental para futura capa fisica/domestica local-first con Home Assistant, voz local, sensores, camaras, presencia, privacidad, ApprovalGateway y adapters/capabilities detras de JARVIS, sin implementar hardware ni integraciones reales, en `docs/roadmap/pr-61-home-voice-sensor-hardware-layer.md`.

JARVIS Personal OS / Environment Intelligence backlog: contrato documental para que JARVIS evolucione hacia sistema operativo personal de David, con Command Center, contexto/memoria, proactividad elegida, modos operativos, daily state, notificaciones, vida/trabajo, socio tecnico, privacidad, consentimiento y auditoria, sin implementar UI, memoria, scheduler ni notificaciones reales, en `docs/roadmap/pr-62-personal-os-environment-intelligence-backlog.md`.

JARVIS Distributed Personal OS Capabilities backlog: contrato documental para presencia distribuida futura en movil, PC, reloj, coche, auriculares, altavoces, pantallas, casa, IDE, servidor y workers, con Gateway, policy, approvals, auditoria, sincronizacion de estado, fallback offline, watchers prepare-only, operaciones largas y coste visible, sin implementar clientes, sync, watchers, notificaciones ni device registry real, en `docs/roadmap/pr-63-distributed-personal-os-capabilities-backlog.md`.

JARVIS Authorized Security Research / Bug Bounty Mode contract: contrato documental para seguridad autorizada, laboratorios, CTF, auditoria defensiva, bug bounty dentro de scope, evidence handling y report writing, manteniendo `PolicyEngine`, `ApprovalGateway`, Restriction Registry, auditoria, hard boundaries y stop conditions, sin implementar scanners, target registry ni evidence locker reales, en `docs/roadmap/pr-64-authorized-security-bug-bounty-mode-contract.md`.

JARVIS Personal Memory / User Model Layer: contrato documental para la futura capa de memoria profunda de David, con preferencias, habitos, decisiones, proyectos, memoria episodica, separacion personal/profesional, sensibilidad, conflictos, borrado/reversion, consentimiento y auditoria, manteniendo que memoria no es permiso y nunca salta `PolicyEngine`, `ApprovalGateway`, Restriction Registry ni hard boundaries, en `docs/roadmap/pr-65-personal-memory-user-model-layer.md`.

JARVIS handoff context: fuente operativa para continuar el proyecto en nuevos hilos, con rutas, comandos, workflow de PRs, reglas de seguridad, estado actual, validaciones reales y roadmap inmediato. Ver `docs/jarvis-handoff-context.md`.

Para la guía específica de operación de GPT-SoVITS como sidecar local o servicio externo desacoplado, ver `docs/integrations/gpt-sovits-sidecar.md`.

Voice local smoke test: guía para validar localmente `/voice/tts` con mock y GPT-SoVITS sidecar en `docs/integrations/voice-local-smoke-test.md`.

Voice Runtime CLI full-flow smoke test: guía para validar el flujo local status → start → control → transcript → feedback → clear feedback con los scripts locales, sin micrófono real ni ejecución de tareas, en `docs/integrations/voice-runtime-cli-full-flow-smoke-test.md`.

GPT-SoVITS local WSL runbook: guía validada para instalar, arrancar y probar GPT-SoVITS como sidecar local de voz para JARVIS en `docs/integrations/gpt-sovits-wsl-local-runbook.md`.

Helper local GPT-SoVITS: `scripts/local/start-jarvis-gpt-sovits.sh` arranca JARVIS con defaults locales seguros apuntando al sidecar ya levantado.

Voice audio storage runbook: guía para validar almacenamiento local con `save_audio` y `.jarvis/voice_outputs` en `docs/integrations/voice-audio-storage-runbook.md`.

Y ver `docs/roadmap/pr-future-content-youtube-factory.md` para la propuesta de Content / YouTube Factory orientada a activos monetizables, con `Approval Gate` obligatorio para publicación, gasto y uso de identidad.

Y ver `docs/roadmap/pr-future-money-roi-engine.md` para el roadmap del Money Engine / ROI Engine, centrado en priorización por retorno, protección de atención humana y `Approval Gate` para gasto o compromisos financieros.

Y ver `docs/roadmap/pr-future-asset-factory.md` para el roadmap de la Asset Factory, enfocada en transformar oportunidades en activos medibles y monetizables con `Approval Gate` en acciones sensibles.

## PR #5 — VoiceAdapter base
Este PR introduce una abstracción mínima para runtime de voz en `jarvis/voice/` con `VoiceSynthesisRequest`, `VoiceSynthesisResult`, el contrato `VoiceAdapter` y un `MockVoiceAdapter` seguro para desarrollo y tests.

No integra motores reales ni genera audio real. La integración efectiva con GPT-SoVITS y VoxCPM queda explícitamente para un PR posterior, manteniendo este cambio pequeño, testeable y sin dependencias pesadas.

## PR #6 — GPT-SoVITS HTTP Adapter
Este PR añade un adapter HTTP desacoplado para GPT-SoVITS en `jarvis/voice/gpt_sovits_adapter.py`, basado en el contrato `VoiceAdapter`.

- No levanta GPT-SoVITS real.
- No descarga modelos.
- GPT-SoVITS debe correr como sidecar local (o servicio externo equivalente).
- Los tests usan mocks/fakes y no realizan llamadas de red reales.

## PR #7 — Voice TTS API endpoint
Este PR añade un endpoint interno mínimo `POST /voice/tts` para síntesis de voz en JARVIS.

- Evalúa `PolicyEngine` antes de sintetizar cualquier texto.
- Usa `MockVoiceAdapter` por defecto cuando no se inyecta un adapter.
- Permite inyectar un adapter real (por ejemplo GPT-SoVITS) sin hacerlo obligatorio.
- No publica audio.
- No devuelve `audio_bytes` en JSON (solo `has_audio_bytes`).

## PR #8 — Voice config factory
Este PR agrega una factory de configuración en `jarvis/voice/factory.py` para seleccionar el motor de voz vía variables de entorno.

- JARVIS puede seleccionar `mock` o `gpt-sovits` usando `JARVIS_VOICE_PROVIDER`.
- `mock` se mantiene como default seguro.
- `gpt-sovits` sigue operando como sidecar local (o servicio externo equivalente).
- La factory solo construye el adapter configurado: no levanta motores, no descarga modelos y no realiza llamadas de red.
- Guía de configuración por variables de entorno: `docs/integrations/voice-env-configuration.md`.

## PR #10 — Voice provider status endpoint
Este PR añade un endpoint interno mínimo `GET /voice/status` para diagnosticar el provider de voz activo.

- Permite ver qué provider está configurado (`mock`, `gpt-sovits` o `unknown`) y si está listo para sintetizar.
- No sintetiza audio.
- No llama al sidecar GPT-SoVITS ni realiza validaciones de red.
- No expone rutas sensibles como `ref_audio_path` ni contenido sensible como `prompt_text`.

## PR #11 — Voice local audio storage
Este PR añade almacenamiento local opcional y seguro para audio generado por `POST /voice/tts`.

- `save_audio` es opcional en la request y por defecto es `false`.
- Cuando `save_audio=true` y el adapter devuelve `audio_bytes`, JARVIS guarda el audio en una carpeta local controlada (`.jarvis/voice_outputs` por defecto o inyectada para tests).
- No publica audio ni agrega UI/streaming.
- La respuesta JSON no expone `audio_bytes`; solo devuelve `audio_path` cuando existe.
- El almacenamiento valida formato (`wav/mp3/ogg`) y evita path traversal.
