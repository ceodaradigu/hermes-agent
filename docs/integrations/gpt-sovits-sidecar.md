# GPT-SoVITS sidecar para JARVIS

## Objetivo

Documentar cómo debe integrarse GPT-SoVITS con JARVIS como sidecar local o servicio externo desacoplado.

JARVIS no importa GPT-SoVITS directamente.
JARVIS llama al servicio HTTP de GPT-SoVITS mediante GPTSoVITSAdapter.

## Arquitectura

JARVIS Core
→ VoiceAdapter
→ GPTSoVITSAdapter
→ GPT-SoVITS HTTP sidecar
→ audio generado

## Principios

- GPT-SoVITS corre fuera del proceso principal de JARVIS.
- JARVIS se comunica por HTTP.
- No se descargan modelos automáticamente desde JARVIS.
- No se entrena voz automáticamente desde JARVIS.
- No se usan voces de terceros sin consentimiento.
- El sidecar local debe configurarse explícitamente por David.

## Configuración esperada

URL local típica:

http://127.0.0.1:9880

Endpoint usado:

POST /tts

Campos principales:

- text
- text_lang
- ref_audio_path
- prompt_lang
- prompt_text
- media_type
- streaming_mode

JARVIS fuerza inicialmente:

streaming_mode = false

## Ejemplo conceptual de uso

JARVIS prepara una VoiceSynthesisRequest:

- text: texto que JARVIS va a decir.
- language: "es".
- output_format: "wav".
- metadata.ref_audio_path: ruta local a voz autorizada.

GPTSoVITSAdapter construye el payload y llama a:

POST http://127.0.0.1:9880/tts

El resultado vuelve como bytes de audio.

## Variables futuras

En un PR posterior podrían añadirse variables como:

- JARVIS_GPT_SOVITS_BASE_URL
- JARVIS_GPT_SOVITS_REF_AUDIO_PATH
- JARVIS_GPT_SOVITS_PROMPT_TEXT
- JARVIS_GPT_SOVITS_PROMPT_LANG

No implementarlas en esta PR; solo documentarlas como idea futura.

## Seguridad y consentimiento

Solo se deben usar:

- voz propia de David.
- voces con permiso explícito.
- voces sintéticas/licenciadas.
- referencias locales controladas.

No permitido:

- clonar voces de terceros sin consentimiento.
- suplantar personas.
- publicar audio generado sin aprobación.
- usar audio generado en campañas sin aprobación.
- enviar referencias de voz a servicios externos sin aprobación.
- usar voz para manipulación encubierta.

## Approval Gate

La síntesis local simple para uso privado puede ser permitida.

Requieren aprobación:

- publicación del audio.
- uso monetizado.
- campañas de pago.
- uso de voz de terceros.
- envío de audio a APIs externas.
- generación de mensajes sensibles en voz.
- cualquier uso que afecte identidad, reputación, dinero o publicación.

## Operación local esperada

Esta documentación no instala GPT-SoVITS.

David debe instalar y ejecutar GPT-SoVITS por separado, siguiendo la documentación oficial del proyecto.

JARVIS solo necesita que el endpoint HTTP esté disponible.

## Troubleshooting

Problemas comunes:

- sidecar no está levantado.
- base_url incorrecta.
- puerto 9880 ocupado.
- ref_audio_path no existe.
- modelo no cargado en GPT-SoVITS.
- idioma no soportado o mal configurado.
- respuesta HTTP 400 con mensaje del servicio.
- timeout por generación lenta.
- GPU/CPU insuficiente.

## Límites de esta integración

- No streaming todavía.
- No entrenamiento automático.
- No selección automática de modelo.
- No descarga automática.
- No gestión de pesos.
- No UI.
- No endpoints nuevos en JARVIS.

## Decisión

GPT-SoVITS debe quedar como motor de voz desacoplado.

JARVIS mantiene el control:
- decide cuándo sintetizar.
- valida permisos.
- llama por HTTP.
- registra resultados.
- pide aprobación para usos sensibles.
