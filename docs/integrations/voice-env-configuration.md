# Configuración de voz por entorno en JARVIS

## Objetivo

Documentar cómo seleccionar el motor de voz de JARVIS usando variables de entorno, sin cambiar código.

JARVIS debe poder usar:

- mock
- gpt-sovits

## Provider por defecto

Si no se define ninguna variable, JARVIS usa:

`JARVIS_VOICE_PROVIDER=mock`

Esto activa `MockVoiceAdapter`.

MockVoiceAdapter:

- no usa APIs externas.
- no genera audio real.
- no requiere modelos.
- es seguro para tests y desarrollo.
- es el default recomendado.

## Activar GPT-SoVITS

Para usar GPT-SoVITS como sidecar local:

`JARVIS_VOICE_PROVIDER=gpt-sovits`

Variables disponibles:

- `JARVIS_GPT_SOVITS_BASE_URL=http://127.0.0.1:9880`
- `JARVIS_GPT_SOVITS_REF_AUDIO_PATH=/ruta/local/voz-autorizada.wav`
- `JARVIS_GPT_SOVITS_PROMPT_TEXT=Texto de referencia autorizado.`
- `JARVIS_GPT_SOVITS_PROMPT_LANG=es`
- `JARVIS_GPT_SOVITS_TIMEOUT_SECONDS=30`

## Ejemplo local

```bash
export JARVIS_VOICE_PROVIDER=gpt-sovits
export JARVIS_GPT_SOVITS_BASE_URL=http://127.0.0.1:9880
export JARVIS_GPT_SOVITS_REF_AUDIO_PATH=/home/david/voices/david.wav
export JARVIS_GPT_SOVITS_PROMPT_TEXT="Referencia de voz autorizada de David."
export JARVIS_GPT_SOVITS_PROMPT_LANG=es
export JARVIS_GPT_SOVITS_TIMEOUT_SECONDS=30
```

## Uso con /voice/tts

Una vez configurado, JARVIS puede llamar internamente:

`POST /voice/tts`

Ejemplo conceptual:

```json
{
  "text": "Misión completada, David.",
  "language": "es",
  "output_format": "wav",
  "metadata": {}
}
```

Si el provider es `mock`, devolverá una respuesta simulada.

Si el provider es `gpt-sovits`, JARVIS llamará al sidecar local configurado.

## ref_audio_path

El audio de referencia puede venir de:

- Variable de entorno: `JARVIS_GPT_SOVITS_REF_AUDIO_PATH`
- metadata en la request: `metadata.ref_audio_path`

La voz debe ser autorizada.

No usar voces de terceros sin consentimiento.

## Seguridad

El provider de voz no elimina controles de seguridad.

JARVIS sigue usando:

- PolicyEngine.
- ApprovalGateway.
- logs.
- aprobación humana para acciones sensibles.

## Acciones que requieren aprobación

Requieren Approval Gate:

- publicar audio generado.
- usar audio generado en contenido monetizado.
- usar voces de terceros.
- enviar audio o referencias de voz a APIs externas.
- usar voz en campañas de pago.
- generar mensajes sensibles en voz.
- cualquier uso que afecte identidad, reputación, dinero o publicación.

## Qué NO hace esta configuración

Esta configuración no:

- instala GPT-SoVITS.
- descarga modelos.
- entrena voces.
- verifica que el sidecar esté levantado.
- comprueba que el archivo `ref_audio_path` exista.
- publica audio.
- activa streaming.
- crea UI.

## Troubleshooting

Problemas comunes:

- `JARVIS_VOICE_PROVIDER` mal escrito.
- GPT-SoVITS no está ejecutándose.
- Puerto 9880 ocupado.
- `base_url` incorrecta.
- `ref_audio_path` ausente.
- `prompt_text` ausente o poco representativo.
- `timeout` demasiado bajo.
- `output_format` no soportado.
- sidecar devuelve HTTP 400.

## Recomendación

Para desarrollo y tests:

`JARVIS_VOICE_PROVIDER=mock`

Para probar voz real en local:

`JARVIS_VOICE_PROVIDER=gpt-sovits`

Siempre con voces autorizadas y sidecar controlado por David.
