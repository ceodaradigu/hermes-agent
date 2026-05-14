# Voice Runtime CLI full-flow smoke test

## Objetivo

Validar localmente el flujo completo de Voice Runtime usando los CLIs ya existentes, sin micrófono real, wake word real, STT real, reproducción de audio, servicios en background ni ejecución de tareas.

Esta guía cubre:

- `GET /voice/runtime/status`
- `POST /voice/runtime/start`
- `POST /voice/runtime/control`
- `POST /voice/runtime/transcript`
- `POST /voice/runtime/feedback`
- `POST /voice/runtime/feedback/preview`
- `GET /voice/runtime/feedback`
- `DELETE /voice/runtime/feedback`

El objetivo funcional es comprobar el recorrido local `status -> start -> control -> transcript -> feedback -> clear feedback` con respuestas JSON observables. El flujo respeta `docs/jarvis-north-star.md`: la voz debe ayudar a entender mejor a David, pero sin saltarse controles, sin aprendizaje opaco y sin ejecutar acciones sensibles automáticamente.

## Requisitos previos

- Repo de JARVIS disponible en `/mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent`.
- Entorno virtual disponible en `~/venvs/hermes-agent`.
- API local de JARVIS ejecutable en `127.0.0.1:8000`.
- `curl` disponible si quieres enviar feedback directamente contra la API.
- Scripts locales existentes:
  - `scripts/local/voice-runtime-control.sh`
  - `scripts/local/voice-runtime-push-to-talk.sh`

Importante:

- No hay persistencia de feedback.
- Reiniciar el proceso de la API borra el estado en memoria.
- No se ejecutan tareas reales.
- No se crean misiones reales.
- No hay micrófono real.
- No hay wake word real.
- No hay STT real.
- No hay audio playback.
- El frontend no es obligatorio.

Nota: existe `POST /voice/runtime/feedback/preview` para previsualizar cómo una corrección podría influir en el perfil de entendimiento en el futuro. Ese endpoint solo analiza, devuelve `applied=false` y `requires_review=true`, no guarda feedback y no incrementa `feedback_count`. El flujo full-flow principal de esta guía sigue usando `POST /voice/runtime/feedback`, que guarda feedback real temporal en memoria para poder listar y limpiar el buffer durante el smoke test.

## 1. Arrancar JARVIS local

En la primera terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

Resultado esperado:

- Uvicorn arranca en `http://127.0.0.1:8000`.
- La API expone los endpoints de Voice Runtime.
- No se levanta ningún servicio de micrófono, wake word, STT ni audio playback.

## 2. Abrir una segunda terminal

En otra terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
```

Todos los comandos siguientes se ejecutan desde la raíz del repo.

## 3. Consultar status inicial

```bash
./scripts/local/voice-runtime-control.sh status
```

Resultado esperado:

- La respuesta es JSON válido.
- El estado inicial puede ser `off` o el estado actual del proceso si ya lo habías usado.
- Si el runtime está recién arrancado, lo esperable es `enabled=false` y `mode=off`.
- `frontend_required` debe indicar que el frontend no es obligatorio.
- `feedback_count` refleja el feedback acumulado en memoria, normalmente `0` en un proceso nuevo.

## 4. Arrancar runtime

```bash
./scripts/local/voice-runtime-control.sh start
```

Resultado esperado:

- La respuesta es JSON válido.
- `enabled=true`.
- `mode=wake_word`.
- El runtime queda preparado para recibir comandos simulados por HTTP.
- No se activa ningún micrófono real.
- No se inicia ningún servicio en background.

## 5. Simular wake/control

```bash
./scripts/local/voice-runtime-control.sh control "hola jarvis"
```

Resultado esperado:

- La respuesta es JSON válido.
- El texto se interpreta como control simulado.
- `mode` cambia a `listening`.
- Esto solo simula la transición de estado; no hay wake word real ni captura de audio.

## 6. Simular transcript normal

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- La respuesta es JSON válido.
- El runtime registra `last_transcript`.
- El runtime clasifica una intención para el texto.
- `executed=false`.
- No se ejecutan tareas reales.
- No se crean misiones reales.
- Si la intención no queda clara, este flujo sirve para capturar después feedback explícito.

## 7. Enviar feedback

Primero puedes consultar el feedback actual:

```bash
./scripts/local/voice-runtime-control.sh feedback-list
```

Para enviar una corrección completa, usa `curl` contra `POST /voice/runtime/feedback`:

```bash
curl -s -X POST "http://127.0.0.1:8000/voice/runtime/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "original_text": "monta algo para probar este nicho",
    "interpreted_intent": "create_asset",
    "corrected_intent": "create_mission",
    "correction_note": "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero.",
    "preferred_next_step": "Crear misión de validación antes de crear landing."
  }'
```

Resultado esperado:

- La respuesta es JSON válido.
- El feedback queda en memoria.
- `feedback_count` sube, normalmente de `0` a `1`.
- `applied_persistently=false`.
- La corrección queda disponible para revisión, no para aprendizaje automático opaco.

## 8. Listar feedback

```bash
./scripts/local/voice-runtime-control.sh feedback-list
```

Resultado esperado:

- La respuesta lista el feedback enviado.
- `feedback_count` refleja el número de correcciones en memoria.
- El item incluye:
  - `original_text="monta algo para probar este nicho"`
  - `interpreted_intent="create_asset"`
  - `corrected_intent="create_mission"`
  - `correction_note`
  - `preferred_next_step`

## 9. Limpiar feedback

```bash
./scripts/local/voice-runtime-control.sh feedback-clear
```

Resultado esperado:

- La respuesta es JSON válido.
- `feedback_count` vuelve a `0`.
- Un nuevo `feedback-list` debe devolver una lista vacía.
- No se borra nada persistente porque el feedback no se guarda en disco ni base de datos.

Verificación opcional:

```bash
./scripts/local/voice-runtime-control.sh feedback-list
```

## 10. Volver a wake-word-only

```bash
./scripts/local/voice-runtime-control.sh control "jarvis no escuches"
```

Resultado esperado:

- La respuesta es JSON válido.
- `mode` vuelve a `wake_word`.
- El runtime queda en modo de espera simulada.
- No se apaga la API local.
- No hay micrófono real escuchando.

## Checklist de validación

- [ ] `status` responde JSON válido.
- [ ] El status inicial muestra `off` o el estado actual del proceso.
- [ ] `start` cambia a `enabled=true` y `mode=wake_word`.
- [ ] `control "hola jarvis"` cambia a `mode=listening`.
- [ ] `transcript "monta algo para probar este nicho"` clasifica intención.
- [ ] La respuesta de transcript mantiene `executed=false`.
- [ ] El feedback queda en memoria.
- [ ] `feedback_count` sube después del `POST /voice/runtime/feedback`.
- [ ] `feedback-list` muestra la corrección enviada.
- [ ] `feedback-clear` borra el buffer en memoria.
- [ ] `control "jarvis no escuches"` vuelve a `mode=wake_word`.
- [ ] No se ejecutan tareas reales.
- [ ] No se crean misiones reales.
- [ ] El frontend no es obligatorio.

## Límites actuales

Este smoke test valida el cableado local de Voice Runtime y los scripts de control. En su estado actual:

- No implementa micrófono.
- No implementa wake word real.
- No implementa STT real.
- No implementa audio playback.
- No implementa threads.
- No implementa servicios en background.
- No implementa autoarranque.
- No persiste feedback.
- No ejecuta tareas reales.
- No crea misiones reales.
- No sustituye `PolicyEngine` ni `ApprovalGateway`.

La utilidad del flujo es comprobar que JARVIS puede recibir controles simulados, transcripciones simuladas y feedback explícito de entendimiento, manteniendo transparencia, revisión humana y control local como exige `docs/jarvis-north-star.md`.
