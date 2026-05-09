# Voice audio storage runbook para JARVIS

## Objetivo

Documentar cómo funciona el almacenamiento local de audio generado por JARVIS y cómo validarlo de forma segura.

## Comportamiento actual

/voice/tts acepta:

- text
- language
- output_format
- metadata
- save_audio

Por defecto:

save_audio = false

Esto significa que JARVIS no guarda audio localmente salvo que se pida explícitamente.

## Carpeta por defecto

La carpeta local por defecto es:

.jarvis/voice_outputs

Esta carpeta es local y controlada por David.

No debe usarse como carpeta pública.

No debe subirse a Git.

## Cuándo se guarda audio

JARVIS solo guarda audio si:

- la acción pasa PolicyEngine como allowed.
- save_audio=true.
- el adapter devuelve audio_bytes.
- el formato es permitido: wav, mp3 u ogg.

Si falta audio_bytes, JARVIS no debe fallar.

Puede devolver audio_path si el adapter ya lo proporcionó.

## Cuándo NO se guarda audio

JARVIS no guarda audio si:

- save_audio=false.
- PolicyEngine devuelve denied.
- PolicyEngine devuelve requires_approval.
- no hay audio_bytes.
- el formato es inválido.
- la petición falla validación.

## Seguridad

JARVIS no devuelve audio_bytes en JSON.

Solo devuelve:

- provider
- content_type
- audio_path si existe
- has_audio_bytes
- duration_seconds
- metadata

No se debe publicar audio automáticamente.

No se debe usar audio generado en contenido monetizado sin aprobación.

No se deben usar voces de terceros sin consentimiento.

## Ejemplo con mock provider sin guardar

```bash
export JARVIS_VOICE_PROVIDER=mock

curl -X POST http://127.0.0.1:8000/voice/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Prueba de voz sin guardar.",
    "language": "es",
    "output_format": "wav",
    "save_audio": false,
    "metadata": {
      "source": "storage-runbook"
    }
  }'
```
