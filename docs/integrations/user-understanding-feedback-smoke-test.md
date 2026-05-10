# User Understanding Feedback API smoke test

## Objetivo

Documentar cómo probar en real la API local de feedback de entendimiento de usuario añadida al runtime de voz de JARVIS.

Esta guía valida el contrato HTTP de:

- `GET /voice/runtime/status`
- `POST /voice/runtime/feedback`
- `GET /voice/runtime/feedback`
- `DELETE /voice/runtime/feedback`

El objetivo funcional es comprobar que JARVIS puede recibir correcciones explícitas sobre una intención mal interpretada. Esto respeta `docs/jarvis-north-star.md`: el aprendizaje debe empezar por feedback explícito, controlado y revisable antes de cualquier memoria automática.

## Requisitos previos

- Repo de JARVIS instalado localmente.
- Entorno virtual disponible en `venv/`.
- API local de JARVIS ejecutable.
- `curl` disponible en la terminal.
- Ningún servicio externo es necesario para este smoke test.

Importante:

- El feedback solo vive en memoria.
- No hay persistencia en disco ni base de datos.
- Reiniciar el proceso de la API borra el feedback acumulado.
- El feedback no se aplica automáticamente todavía al router de intención.
- La API no ejecuta tareas reales.
- La API no crea misiones reales.

## Cómo arrancar JARVIS local

Desde la raíz del repo:

```bash
source venv/bin/activate
python -m uvicorn jarvis.api.app:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Si tu entorno local ya usa otro comando para levantar la API, puedes usarlo siempre que exponga los endpoints de `jarvis.api.app` en `http://127.0.0.1:8000`.

## Cómo consultar `/voice/runtime/status`

En otra terminal:

```bash
curl -s "http://127.0.0.1:8000/voice/runtime/status"
```

Respuesta esperada a alto nivel:

```json
{
  "mode": "off",
  "enabled": false,
  "frontend_required": false,
  "input_language": "es",
  "output_language": "es",
  "last_error": null,
  "last_transcript": null,
  "last_intent": null,
  "wake_words": ["jarvis", "hola jarvis"],
  "feedback_count": 0
}
```

El valor clave para este smoke test es `feedback_count`.

## Cómo enviar feedback con `POST /voice/runtime/feedback`

Ejemplo real de corrección:

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

Respuesta esperada a alto nivel:

```json
{
  "feedback": {
    "original_text": "monta algo para probar este nicho",
    "interpreted_intent": "create_asset",
    "corrected_intent": "create_mission",
    "correction_note": "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero.",
    "preferred_next_step": "Crear misión de validación antes de crear landing.",
    "confidence_before": null,
    "source": "user",
    "applied_persistently": false,
    "requires_review": true
  },
  "feedback_count": 1,
  "applied_persistently": false
}
```

Notas de contrato:

- `original_text` debe ser no vacío.
- `corrected_intent` debe ser no vacío.
- `interpreted_intent`, `correction_note`, `preferred_next_step` y `confidence_before` son opcionales.
- `applied_persistently` debe seguir siendo `false`.
- `requires_review` debe seguir siendo `true`.

## Cómo listar feedback con `GET /voice/runtime/feedback`

```bash
curl -s "http://127.0.0.1:8000/voice/runtime/feedback"
```

Respuesta esperada después del `POST` anterior:

```json
{
  "feedback": [
    {
      "original_text": "monta algo para probar este nicho",
      "interpreted_intent": "create_asset",
      "corrected_intent": "create_mission",
      "correction_note": "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero.",
      "preferred_next_step": "Crear misión de validación antes de crear landing.",
      "confidence_before": null,
      "source": "user",
      "applied_persistently": false,
      "requires_review": true
    }
  ],
  "feedback_count": 1
}
```

Este listado solo muestra el buffer en memoria del proceso actual.

## Cómo limpiar feedback con `DELETE /voice/runtime/feedback`

```bash
curl -s -X DELETE "http://127.0.0.1:8000/voice/runtime/feedback"
```

Respuesta esperada:

```json
{
  "feedback_count": 0
}
```

Después de limpiar, puedes confirmar con:

```bash
curl -s "http://127.0.0.1:8000/voice/runtime/feedback"
```

Respuesta esperada:

```json
{
  "feedback": [],
  "feedback_count": 0
}
```

## Checklist de validación

- [ ] `GET /voice/runtime/status` responde `200` con JSON válido.
- [ ] `feedback_count` aparece en el estado del runtime.
- [ ] `POST /voice/runtime/feedback` acepta la corrección real de ejemplo.
- [ ] La respuesta del `POST` incluye `applied_persistently: false`.
- [ ] La respuesta del `POST` incluye `requires_review: true` dentro de `feedback`.
- [ ] `GET /voice/runtime/feedback` lista el feedback enviado.
- [ ] `DELETE /voice/runtime/feedback` limpia el buffer en memoria.
- [ ] Un nuevo `GET /voice/runtime/feedback` devuelve lista vacía.

## Límites actuales

Esta API es un primer punto de entrada para feedback explícito y revisable. En su estado actual:

- No persiste feedback.
- No modifica memoria.
- No entrena modelos.
- No cambia automáticamente futuras clasificaciones.
- No ejecuta workflows.
- No crea activos.
- No crea misiones.
- No sustituye aprobaciones humanas ni controles de seguridad.

La utilidad del endpoint es capturar correcciones de entendimiento de forma transparente para futuras fases de aprendizaje, manteniendo privacidad, revisión humana y control explícito, tal como exige `docs/jarvis-north-star.md`.
