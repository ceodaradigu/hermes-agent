# Voice local smoke test para JARVIS

## Objetivo

Documentar cómo validar localmente que el sistema de voz de JARVIS funciona con el provider mock y, opcionalmente, con GPT-SoVITS como sidecar local.

Esta guía no instala GPT-SoVITS ni descarga modelos.
Solo explica cómo probar que JARVIS llama correctamente a `/voice/tts`.

## Requisitos previos

- Repo de JARVIS instalado localmente.
- Tests JARVIS pasando.
- API local de JARVIS ejecutándose.
- Para mock: no hace falta ningún servicio externo.
- Para gpt-sovits: GPT-SoVITS debe estar levantado aparte como sidecar local.

## Smoke test con mock provider

El mock provider es el modo seguro por defecto.

Variables recomendadas:

```bash
export JARVIS_VOICE_PROVIDER=mock
export JARVIS_VOICE_ENABLED=true
```

Levantar API local de JARVIS (ajusta a tu comando habitual):

```bash
python -m uvicorn jarvis_api.main:app --reload --host 127.0.0.1 --port 8000
```

Ejemplo de request a `POST /voice/tts`:

```bash
curl -X POST "http://127.0.0.1:8000/voice/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hola, esta es una prueba local de voz",
    "voice": "default",
    "format": "wav"
  }'
```

Resultado esperado (alto nivel):

- HTTP `200 OK`.
- Respuesta JSON válida.
- El payload incluye metadatos de salida de TTS (por ejemplo: provider usado, formato, o referencia al audio generado por el mock).
- No hay llamadas a servicios externos.

## Smoke test con gpt-sovits provider (sidecar local)

Este test valida el cableado de JARVIS contra un sidecar ya levantado.

> Importante: esta guía **no** instala GPT-SoVITS ni descarga modelos.

Variables recomendadas (ajusta host/puerto según tu sidecar):

```bash
export JARVIS_VOICE_PROVIDER=gpt-sovits
export JARVIS_VOICE_ENABLED=true
export JARVIS_GPTSOVITS_BASE_URL=http://127.0.0.1:9880
```

Verificación rápida del sidecar (endpoint de salud o raíz, según tu despliegue):

```bash
curl -i "http://127.0.0.1:9880/"
```

Request a JARVIS (`POST /voice/tts`):

```bash
curl -X POST "http://127.0.0.1:8000/voice/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hola, prueba con GPT-SoVITS sidecar",
    "voice": "default",
    "format": "wav"
  }'
```

Resultado esperado (alto nivel):

- HTTP `200 OK` si el sidecar está sano y la configuración es correcta.
- En logs de JARVIS se observa que el provider activo es `gpt-sovits`.
- La respuesta refleja que la generación fue delegada al proveedor configurado.

## Probar `POST /voice/tts` con casos mínimos

Casos sugeridos para validar contrato del endpoint:

1. **Texto corto válido**
   - Input: `"ok"`
   - Esperado: `200`.

2. **Texto normal (frase completa)**
   - Input: `"Hola JARVIS, prueba uno dos tres"`
   - Esperado: `200`.

3. **Texto vacío**
   - Input: `""`
   - Esperado: `4xx` por validación.

4. **Payload malformado**
   - Input: JSON inválido o sin campo `text`.
   - Esperado: `4xx`.

5. **Provider no disponible**
   - Configurar `gpt-sovits` sin sidecar levantado.
   - Esperado: error controlado (`5xx` o error de integración), sin crash del proceso.

## Errores comunes

1. **`connection refused` contra GPT-SoVITS**
   - Causa: sidecar apagado o URL/puerto incorrectos.
   - Acción: revisar `JARVIS_GPTSOVITS_BASE_URL` y estado del sidecar.

2. **Provider incorrecto cargado**
   - Causa: variable `JARVIS_VOICE_PROVIDER` no exportada en la misma shell.
   - Acción: re-exportar variables y reiniciar la API de JARVIS.

3. **`422 Unprocessable Entity` en `/voice/tts`**
   - Causa: payload no cumple esquema.
   - Acción: verificar JSON y campos requeridos (`text`, etc.).

4. **Timeouts intermitentes**
   - Causa: sidecar local saturado o lento.
   - Acción: probar texto corto, revisar recursos locales, reintentar.

5. **Confusión entre seguridad y voz**
   - Aclaración: el pipeline de voz no reemplaza controles de seguridad.
   - Recordatorio: acciones sensibles siguen pasando por `PolicyEngine` y `ApprovalGateway`.

## Checklist de validación local

- [ ] Con `mock`, `POST /voice/tts` responde `200` con JSON válido.
- [ ] Con `mock`, no hay dependencia de servicios externos.
- [ ] Con `gpt-sovits`, JARVIS alcanza el sidecar configurado.
- [ ] Con `gpt-sovits`, `POST /voice/tts` responde exitosamente cuando el sidecar está sano.
- [ ] Si el sidecar falla, JARVIS devuelve error controlado y trazable.
- [ ] Casos inválidos (texto vacío, JSON malformado) devuelven `4xx`.
- [ ] Logs permiten identificar provider activo y causa de error.
- [ ] No se modificaron controles de seguridad (`PolicyEngine`, `ApprovalGateway`).

## Notas finales

- Usa `mock` como baseline en desarrollo local.
- Usa `gpt-sovits` solo cuando necesites validar integración real con sidecar.
- Mantén estas pruebas como smoke test rápido previo a cambios mayores de voz.
