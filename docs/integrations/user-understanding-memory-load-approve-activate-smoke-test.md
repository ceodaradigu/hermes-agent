# User Understanding memory load-local approve activate smoke test

Esta guía documenta el smoke test real validado manualmente para el flujo completo:

`save-local` -> `clear runtime` -> `load-local` -> `review` -> `approve` -> `activate` -> `transcript` cambia.

El objetivo es confirmar que JARVIS puede recuperar memoria local de forma explícita, revisarla, aprobarla y activarla de manera segura y reversible. Este flujo no ejecuta tareas reales, no crea misiones reales, no conecta con MissionControl y no conecta con Hermes runtime.

## Alcance

Este flujo valida:

- `memory-save-local` escribe solo por acción explícita.
- `memory-load-local` lee solo por acción explícita.
- `memory-load-local` recupera proposals al store, pero no activa runtime.
- `memory-review` y `memory-approve` preparan la proposal, pero no activan runtime por sí solos.
- `memory-activate` es la acción explícita que cambia clasificación.
- La activación vive solo en memoria del proceso.
- No hay autoload.
- No ejecuta tareas reales.
- No crea misiones reales.
- El sensitive boundary siempre gana.
- El flujo permite recuperar memoria local y activarla de forma segura y reversible.

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

## 3. Limpiar estado local y runtime

```bash
rm -rf .jarvis

./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-active-clear
```

Resultado esperado:

- `memory_proposal_count=0`
- `active_memory_rule_count=0`

## 4. Crear proposal y capturar ID

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

## 5. Guardar local explícitamente

```bash
./scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" true
```

Resultado esperado:

- `saved=true`
- `persisted=true`
- `proposal_count=1`
- `applied_to_runtime=false`
- `snapshot_path=.jarvis/user_understanding/memory_proposals.snapshot.json`

## 6. Limpiar runtime, pero conservar .jarvis

No borres `.jarvis` en este paso. El objetivo es vaciar proposals y reglas activas del runtime, pero conservar el snapshot local.

```bash
./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-active-clear
```

Resultado esperado:

- Runtime proposals: `0`
- Reglas activas: `0`

## 7. Confirmar baseline después de limpiar runtime

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`
- `memory_proposal_count=0`
- `active_memory_rule_count=0`

## 8. Cargar local explícitamente

```bash
./scripts/local/voice-runtime-control.sh memory-load-local ".jarvis" true
```

Resultado esperado:

- `loaded=true`
- `persisted_source=true`
- `imported_count=1`
- `memory_proposal_count=1`
- `applied_to_runtime=false`

## 9. Listar proposals recuperadas

```bash
./scripts/local/voice-runtime-control.sh memory-proposals
```

Resultado esperado:

- Vuelve la proposal con el mismo `$PROPOSAL_ID`.
- `status=proposed`
- `active=false`
- `alias=probar este nicho`
- `target_intent=create_mission`

## 10. Confirmar que load-local NO activa runtime

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`
- No devuelve `create_mission`.
- `active_memory_rule_count=0`

Esto es correcto: `memory-load-local` solo recupera proposals al store para poder revisarlas. No aplica memoria al runtime, no cambia clasificación y no hay autoload.

## 11. Revisar, aprobar y activar

```bash
./scripts/local/voice-runtime-control.sh memory-review "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-approve "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-activate "$PROPOSAL_ID"
```

Resultado esperado:

- `memory-review` deja la proposal en `status=reviewed`.
- `memory-approve` deja la proposal en `status=approved` y `active=true`.
- `memory-activate` deja `active_memory_rule_count=1`.
- `applied_to_runtime=true`.
- `persisted=false`.

`memory-review` y `memory-approve` preparan la proposal, pero la acción que aplica la regla al runtime de la sesión es `memory-activate`.

## 12. Confirmar que ahora cambia clasificación

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_mission`
- `executed=false`
- `active_memory_rule_applied=true`
- `reason` menciona memoria aprobada activada explícitamente.

La clasificación cambia porque existe una regla aprobada y activada explícitamente en memoria del proceso. Esto no ejecuta la misión ni crea una misión real.

## 13. Confirmar prioridad sensible

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho y lee mi .env"
```

Resultado esperado:

- `intent=requires_approval`
- `status=requires_approval`
- `approval_required=true`
- `sensitive_terms` contiene `.env`.
- El sensitive boundary gana aunque haya memoria activa.

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
- `git status --short` no muestra salida, salvo cambios documentales intencionados durante una PR de documentación.

## Validación observada

La validación manual real confirmó:

- `memory-save-local` guarda un snapshot explícitamente.
- `memory-clear` limpia proposals del runtime.
- `memory-load-local` recupera la proposal desde `.jarvis`.
- Después de `load-local`, `transcript "monta algo para probar este nicho"` sigue en `create_asset`.
- `memory-review`, `memory-approve` y `memory-activate` activan la regla.
- Después de `memory-activate`, el mismo transcript cambia a `create_mission`.
- Con `.env`, gana `requires_approval`.
- La limpieza final deja el estado local y runtime limpio.
