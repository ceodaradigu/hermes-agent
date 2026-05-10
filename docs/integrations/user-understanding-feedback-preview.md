# User Understanding Feedback Preview

This module prepares future learning for David's user-understanding profile without applying that learning automatically.

`jarvis.voice.feedback_preview` receives a `UserUnderstandingFeedback` item and returns a serializable `UserUnderstandingFeedbackPreview`. The preview describes what might be useful to review later, such as a suggested alias, the likely profile area, the corrected intent, and the risk level.

Current guarantees:

- It does not persist anything.
- It does not modify `UserUnderstandingProfile`.
- It does not modify `VoiceIntentRouter`.
- It does not change the current intent classification.
- It does not execute tasks, create missions, call MissionControl, or connect to Hermes runtime.
- It always returns `applied=false`.
- It returns `requires_review=true` by default.

Example:

```python
from jarvis.voice import UserUnderstandingFeedback, create_feedback_preview

feedback = UserUnderstandingFeedback(
    original_text="monta algo para probar este nicho",
    interpreted_intent="create_asset",
    corrected_intent="create_mission",
)

preview = create_feedback_preview(feedback).to_dict()
```

The preview suggests that `"probar este nicho"` may belong in `intent_aliases` for `create_mission`, but it does not learn, save, or apply that suggestion.
