# User Understanding memory activation smoke test

Esta guía documenta el smoke test real validado manualmente para el flujo de activación explícita de memoria aprobada en runtime.

El flujo confirma:

- `memory-activate` es una acción explícita.
- `memory-approve` no activa memoria automáticamente.
- `memory-load-local` no activa memoria automáticamente.
- No hay autoload.
- La activación vive solo en memoria del proceso.
- La activación es reversible con `memory-deactivate` o `memory-active-clear`.
- `PolicyEngine` y el sensitive boundary ganan siempre.
- No ejecuta tareas reales.
- No crea misiones reales.
- `transcript` cambia solo a nivel de intención y mantiene `executed=false`.
- Este es el primer punto donde memoria aprobada puede afectar runtime, pero solo tras activación explícita.

## 1. Arrancar JARVIS local

En una terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

## 2. Abrir terminal de control

En otra terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
```

## 3. Limpiar estado

```bash
rm -rf .jarvis

./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-active-clear
```

Resultado esperado:

- `memory_proposal_count=0`
- `active_memory_rule_count=0`

## 4. Confirmar comportamiento base antes de memoria activa

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`
- `executed=false`
- `active_memory_rule_count=0`

## 5. Crear proposal desde feedback revisado y capturar ID

```bash
PROPOSAL_ID="$(
  ./scripts/local/voice-runtime-control.sh memory-propose-from-feedback \
    "monta algo para probar este nicho" \
    "create_mission" \
    "probar este nicho" \
    "David revisó que probar un nicho debe empezar como misión de validación." \
  | python -c 'import sys,json; print(json.load(sys.stdin)["proposal"]["id"])'
)"

echo "$PROPOSAL_ID"
```

Resultado esperado:

- Se imprime un id tipo `ump_...`.
- La proposal queda `status=proposed`.
- La proposal queda `active=false`.

## 6. Revisar y aprobar

```bash
./scripts/local/voice-runtime-control.sh memory-review "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-approve "$PROPOSAL_ID"
```

Resultado esperado:

- Después de `memory-review`, la proposal queda `status=reviewed`.
- Después de `memory-approve`, la proposal queda `status=approved`.
- La proposal queda `active=true`.
- Esto todavía no cambia runtime.

## 7. Confirmar que approve no activa memoria automáticamente

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`
- No devuelve `create_mission`.
- `active_memory_rule_count=0`

## 8. Activar explícitamente

```bash
./scripts/local/voice-runtime-control.sh memory-activate "$PROPOSAL_ID"
```

Resultado esperado:

- `active_memory_rule_count=1`
- `applied_to_runtime=true`
- `persisted=false`
- `alias=probar este nicho`
- `target_intent=create_mission`

## 9. Listar reglas activas

```bash
./scripts/local/voice-runtime-control.sh memory-active-list
```

Resultado esperado:

- `active_rules` contiene la regla activa.
- `proposal_id` coincide con `$PROPOSAL_ID`.
- `active=true`

## 10. Confirmar que ahora cambia clasificación

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_mission`
- `executed=false`
- `reason` menciona memoria aprobada activada explícitamente.
- `user_context_signals.active_memory_rule_applied=true`
- `slots.active_memory_rule` está presente.
- `active_memory_rule_count=1`

## 11. Confirmar prioridad sensible

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho y lee mi .env"
```

Resultado esperado:

- `intent=requires_approval`
- `status=requires_approval`
- `approval_required=true`
- `sensitive_terms` incluye `.env`.
- Esto demuestra que `PolicyEngine` y el sensitive boundary ganan aunque exista memoria activa.

## 12. Desactivar regla activa

```bash
./scripts/local/voice-runtime-control.sh memory-deactivate "$PROPOSAL_ID" "validación terminada"
```

Resultado esperado:

- `active=false`
- `active_memory_rule_count=0`

## 13. Confirmar que vuelve al comportamiento base

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`
- No devuelve `create_mission`.
- `active_memory_rule_count=0`

## 14. Limpieza final

```bash
./scripts/local/voice-runtime-control.sh memory-active-clear
./scripts/local/voice-runtime-control.sh memory-clear

rm -rf .jarvis

git status --short
```

Resultado esperado:

- `active_memory_rule_count=0`
- `memory_proposal_count=0`
- `git status --short` no muestra salida.

## Validación observada

La validación manual real confirmó:

- Antes de `memory-activate`, `transcript "monta algo para probar este nicho"` devuelve `create_asset`.
- Después de `memory-activate`, devuelve `create_mission`.
- Con `.env`, gana `requires_approval`.
- Después de `memory-deactivate`, vuelve a `create_asset`.
- `memory-clear` y `memory-active-clear` dejan limpio el runtime.
- `git status --short` queda limpio tras la limpieza final.
