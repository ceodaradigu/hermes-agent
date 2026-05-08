# PR futuro — Voice Runtime Adapter

## Objetivo

Documentar una futura integración de voz natural para JARVIS mediante adapters desacoplados, empezando por candidatos como GPT-SoVITS y VoxCPM.

La voz debe permitir que JARVIS pueda hablar, narrar misiones, generar alertas, crear audio para contenido y participar en el futuro Command Center.

## Principio de arquitectura

JARVIS no debe integrar motores pesados de voz directamente en el core.

Arquitectura deseada:

JARVIS Core
→ VoiceAdapter
→ motor de voz local/externo
→ audio generado

Los motores de voz deben ejecutarse como sidecar local, servicio externo o adapter desacoplado.

## Candidatos iniciales

### GPT-SoVITS

Uso potencial:
- voice cloning controlado.
- TTS con audio de referencia.
- voz personalizada para JARVIS.
- narraciones y contenido.

Notas:
- Debe tratarse como servicio externo/local.
- No importar módulos internos directamente en el core.
- No descargar modelos automáticamente en este PR futuro.
- Requiere revisión de instalación, licencia, dependencias y rendimiento.

### VoxCPM

Uso potencial:
- voz natural multilingüe.
- diseño de voces.
- clonación o referencia de voz controlada.
- posible voz principal de JARVIS.
- voz para Dominion Mode / Overdrive Mode.
- narración para YouTube, podcasts y alertas.

Notas:
- Evaluar si funciona mejor que GPT-SoVITS para voz principal.
- Mantener como adapter intercambiable.
- Validar licencia, requisitos de hardware y calidad real en local.

## Scope inicial del futuro PR

### Must

- Crear carpeta:
  jarvis/voice/

- Crear interface o adapter base:
  VoiceAdapter

- Crear documentación de configuración local.

- Implementar al menos un adapter inicial mockeable:
  GPTSoVITSAdapter o VoxCPMAdapter

- Tests con mocks.
- No levantar motores reales en CI.
- No descargar modelos en tests.
- No meter dependencias pesadas en el core.

### Should

- Configurar motor por variables de entorno.
- Permitir seleccionar voz autorizada.
- Guardar audio generado en una carpeta local controlada.
- Devolver path o bytes de audio.
- Preparar integración futura con Command Center.
- Preparar integración futura con YouTube/Content Factory.

### Won’t

- No UI.
- No streaming todavía.
- No entrenamiento automático de voz.
- No clonación de voces de terceros.
- No publicación automática de audio.
- No subir audios a servicios externos sin aprobación.
- No convertir JARVIS en plataforma pública de clonación de voz.
- No usar voz para suplantar personas.

## Seguridad y consentimiento

Solo se permitirá usar:

- Voz propia de David.
- Voces con permiso explícito.
- Voces sintéticas/licenciadas.
- Modelos locales controlados.

Debe bloquearse o requerir aprobación para:

- Clonar voces de terceros.
- Usar audio de una persona sin consentimiento.
- Generar audio que pueda suplantar identidad.
- Publicar audio generado.
- Usar voz en campañas, anuncios o contenido monetizado sin aprobación.
- Enviar audio o referencias de voz a APIs externas.

## Approval Gate

La generación local simple de una respuesta hablada puede ser una acción permitida.

Pero deben requerir aprobación:

- publicación de audio.
- uso comercial.
- campañas de pago.
- clonación de voz.
- uso de voz de terceros.
- envío de audio a servicios externos.
- generación de mensajes sensibles en voz.
- cualquier acción que afecte identidad, reputación, dinero o publicación.

## Relación con Dominion / Overdrive Mode

Voice Runtime Adapter podrá usarse en el futuro para dar voz a Dominion / Overdrive Mode.

Ese modo puede tener voz más oscura, fría, arrogante y cinematográfica.

Pero el tono no cambia las restricciones reales:
- PolicyEngine sigue activo.
- ApprovalGateway sigue activo.
- JARVIS puede sonar peligroso, pero no puede actuar de forma peligrosa.

## Relación con Content / YouTube Factory

Voice Runtime Adapter podrá usarse para:

- narraciones de vídeos.
- shorts.
- podcasts.
- resúmenes hablados.
- intros/outros.
- alertas.
- contenido educativo.
- contenido de afiliación.

Toda publicación o uso monetizado debe pasar por aprobación humana.

## Riesgos

- Dependencias pesadas.
- Requisitos de GPU/CPU.
- Latencia.
- Calidad variable.
- Licencias de modelos.
- Riesgo de suplantación.
- Riesgo reputacional.
- Costes de APIs externas.
- Fuga de datos si se envían audios a terceros.

## Decisión

JARVIS debe tener voz, pero de forma soberana, modular y segura.

El futuro PR debe implementar un adapter desacoplado, no acoplar el core a un motor concreto.

Orden recomendado:

1. Documentar candidatos.
2. Probar GPT-SoVITS y VoxCPM en local.
3. Elegir adapter inicial.
4. Implementar VoiceAdapter con mocks.
5. Conectar al Command Center cuando exista UI base.
