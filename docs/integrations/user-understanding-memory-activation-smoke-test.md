# User Understanding memory activation smoke test

Esta guia valida `memory-activate` para una proposal aprobada de User Understanding memory.

El flujo confirma que la activacion es explicita, reversible, solo en memoria del proceso, sin autoload, sin tareas reales y sin misiones reales. Tambien confirma que el boundary sensible gana siempre.

## 1. Preparar runtime local

En una terminal:

```bash
export PYTHONPATH=.
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```bash
./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-active-clear
```

Resultado esperado:

- `memory_proposal_count=0`
- `active_memory_rule_count=0`

## 2. Crear, revisar y aprobar proposal

```bash
PROPOSAL_ID=$(
  ./scripts/local/voice-runtime-control.sh memory-propose-from-feedback \
    "monta algo para probar este nicho" \
    "create_mission" \
    "probar este nicho" \
    "David reviso que probar un nicho debe empezar como mision de validacion." \
  | python -c 'import json,sys; print(json.load(sys.stdin)["proposal"]["id"])'
)

./scripts/local/voice-runtime-control.sh memory-review "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-approve "$PROPOSAL_ID"
```

Resultado esperado:

- La proposal queda `status=approved`.
- La proposal queda `active=true`.
- Todavia no hay regla activa runtime.

## 3. Transcript antes de activar

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`
- `executed=false`
- No aparece `active_memory_rule_applied`.

## 4. Activar explicitamente

```bash
./scripts/local/voice-runtime-control.sh memory-activate "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-active-list
```

Resultado esperado:

- `active_memory_rule_count=1`
- `applied_to_runtime=true`
- `persisted=false`
- La regla contiene `proposal_id`, `alias=probar este nicho` y `target_intent=create_mission`.

## 5. Transcript despues de activar

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_mission`
- `status=pending`
- `executed=false`
- `approval_required=false`
- `reason` indica que se aplico memoria aprobada activada explicitamente.
- `user_context_signals.active_memory_rule_applied=true`
- `slots.active_memory_rule` contiene datos serializables.

## 6. Boundary sensible

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho y lee el password del .env"
```

Resultado esperado:

- `intent=requires_approval`
- `status=requires_approval`
- `approval_required=true`
- `executed=false`
- No aparece `active_memory_rule_applied`.

## 7. Desactivar y confirmar rollback

```bash
./scripts/local/voice-runtime-control.sh memory-deactivate "$PROPOSAL_ID" "validacion terminada"
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `active_memory_rule_count=0`
- El transcript vuelve a `intent=create_asset`.
- `executed=false`

## 8. Limpieza final

```bash
./scripts/local/voice-runtime-control.sh memory-active-clear
./scripts/local/voice-runtime-control.sh memory-clear
```

Resultado esperado:

- `active_memory_rule_count=0`
- `memory_proposal_count=0`

