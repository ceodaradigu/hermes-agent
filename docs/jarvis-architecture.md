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

User Understanding memory proposals smoke test: guía para validar el flujo local memory-clear → memory-propose-from-feedback → memory-review → memory-approve → transcript sin cambio → memory-disable → memory-clear usando el CLI, sin persistencia ni aplicación al router/runtime, en `docs/integrations/user-understanding-memory-proposals-smoke-test.md`.

User Understanding memory snapshot smoke test: guía para validar el flujo local memory-clear → memory-propose-from-feedback → memory-snapshot → memory-clear → memory-snapshot-import → memory-proposals → transcript sin cambio, sin persistencia en disco ni aplicación al router/runtime, en `docs/integrations/user-understanding-memory-snapshot-smoke-test.md`.

User Understanding local persistence design: diseño futuro para persistencia local opt-in de memory snapshots, con rutas propuestas bajo `.jarvis`, auditoría, backups, borrado reversible, bloqueo de secretos y sin aplicación automática al router/runtime, en `docs/roadmap/user-understanding-local-persistence-design.md`.

User Understanding save/load local smoke test: guía para validar el flujo completo memory-propose-from-feedback → memory-save-local → memory-clear → memory-load-local → memory-proposals → transcript sin cambio, en `docs/integrations/user-understanding-memory-save-load-local-smoke-test.md`.

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
