# User Understanding Feedback Preview

Este endpoint interno prepara aprendizaje futuro para el perfil de entendimiento de David sin aplicar ese aprendizaje automáticamente.

`POST /voice/runtime/feedback/preview` recibe una corrección explícita, construye un `UserUnderstandingFeedback` temporal y devuelve un `UserUnderstandingFeedbackPreview` serializable. El preview describe qué convendría revisar más adelante, como un alias sugerido, el área probable del perfil, la intención corregida y el nivel de riesgo.

Garantías actuales:

- Solo analiza el feedback recibido en la request.
- No guarda feedback en el `feedback_store`.
- No persiste nada en disco ni base de datos.
- No modifica `UserUnderstandingProfile`.
- No modifica `VoiceIntentRouter`.
- No cambia la clasificación actual del router.
- No ejecuta tareas, no crea misiones, no llama a MissionControl y no conecta con Hermes runtime.
- Devuelve siempre `applied=false`.
- Devuelve siempre `requires_review=true`.
- Respeta `docs/jarvis-north-star.md`: aprendizaje explícito, revisable y sin automatismos opacos.

## Ejemplo con curl

```bash
curl -s -X POST "http://127.0.0.1:8000/voice/runtime/feedback/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "original_text": "monta algo para probar este nicho",
    "interpreted_intent": "create_asset",
    "corrected_intent": "create_mission",
    "correction_note": "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero.",
    "preferred_next_step": "Crear misión de validación antes de crear landing."
  }'
```

Tambien puede probarse desde el CLI local sin escribir el `curl` completo:

```bash
scripts/local/voice-runtime-control.sh feedback-preview \
  "monta algo para probar este nicho" \
  "create_asset" \
  "create_mission" \
  "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero." \
  "Crear misión de validación antes de crear landing."
```

Respuesta esperada, abreviada:

```json
{
  "preview": {
    "original_text": "monta algo para probar este nicho",
    "corrected_intent": "create_mission",
    "suggested_alias": "probar este nicho",
    "suggested_profile_area": "intent_aliases",
    "risk_level": "medium",
    "requires_review": true,
    "applied": false,
    "reason": "..."
  },
  "applied": false,
  "requires_review": true,
  "feedback_count": 0
}
```

`feedback_count` no sube por usar el preview. Si después llamas a `GET /voice/runtime/feedback`, el listado sigue vacío salvo que antes hayas usado el endpoint real `POST /voice/runtime/feedback`.

## Uso desde Python

```python
from jarvis.voice import UserUnderstandingFeedback, create_feedback_preview

feedback = UserUnderstandingFeedback(
    original_text="monta algo para probar este nicho",
    interpreted_intent="create_asset",
    corrected_intent="create_mission",
)

preview = create_feedback_preview(feedback).to_dict()
```

El preview sugiere que `"probar este nicho"` puede pertenecer a `intent_aliases` para `create_mission`, pero no aprende, no guarda y no aplica esa sugerencia.
