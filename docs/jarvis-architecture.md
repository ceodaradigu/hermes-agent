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

También ver `docs/roadmap/pr-future-voice-runtime-adapter.md` para el roadmap de integración de voz mediante adapters desacoplados, manteniendo `PolicyEngine`, `ApprovalGateway` y control humano en acciones sensibles.

Para la guía específica de operación de GPT-SoVITS como sidecar local o servicio externo desacoplado, ver `docs/integrations/gpt-sovits-sidecar.md`.

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
