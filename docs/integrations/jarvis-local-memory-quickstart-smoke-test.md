# JARVIS local memory quickstart manual smoke test

Esta guia convierte `docs/integrations/jarvis-local-memory-quickstart.md` en un smoke test manual reproducible para JARVIS local memory.

No registra una ejecucion real. No debe afirmarse que este smoke test fue ejecutado hasta que David pegue la salida real de terminal.

## Alcance

Este smoke test manual valida, cuando David lo ejecute localmente, que:

- `memory-save-local` escribe memoria local solo por accion explicita.
- `memory-load-local` lee memoria local solo por accion explicita.
- `memory-review` y `memory-approve` no activan runtime por si solos.
- `memory-activate` si puede cambiar la clasificacion durante la sesion actual.
- El sensitive boundary siempre gana sobre cualquier memoria activa.
- Al final se limpia `.jarvis` y la memoria runtime.

Este smoke test manual no hace ni debe hacer:

- No hay autoload.
- No hay autoejecucion.
- No se ejecutan tareas reales.
- No se crean misiones reales.
- No conecta MissionControl/Hermes para ejecutar trabajo real.
- No instala dependencias.
- No usa APIs externas.

## Prerrequisitos

- Repo local de JARVIS en `/mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent`.
- Venv bueno disponible en `~/venvs/hermes-agent`.
- Ninguna ejecucion previa debe dejar memoria de prueba bajo `.jarvis`.

## 1. Arrancar JARVIS local

En una terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

Deja este proceso en ejecucion mientras dure el smoke test manual.

## 2. Abrir terminal de control

En otra terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
```

## 3. Limpiar estado inicial

```bash
rm -rf .jarvis
./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-active-clear
./scripts/local/voice-runtime-control.sh status
```

Resultado esperado:

- No queda memoria local previa bajo `.jarvis`.
- `memory_proposal_count=0`.
- `active_memory_rule_count=0`.

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
- La proposal queda en memoria del proceso.
- La proposal no esta guardada localmente.
- La proposal no esta aprobada ni activa.

## 5. Guardar localmente por accion explicita

```bash
./scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" true
```

Resultado esperado:

- `saved=true`.
- `persisted=true`.
- `proposal_count=1`.
- `applied_to_runtime=false`.
- Existe snapshot bajo `.jarvis/user_understanding/`.

`memory-save-local` escribe el snapshot local solo porque David ejecuta este comando. No hay escritura automatica.

## 6. Limpiar runtime sin borrar .jarvis

No borres `.jarvis` en este paso. El objetivo es vaciar proposals y reglas activas del runtime, pero conservar el snapshot local.

```bash
./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-active-clear
./scripts/local/voice-runtime-control.sh status
```

Resultado esperado:

- `memory_proposal_count=0`.
- `active_memory_rule_count=0`.

## 7. Confirmar baseline sin memoria activa

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`.
- `executed=false`.
- `active_memory_rule_count=0`.

## 8. Cargar localmente por accion explicita

```bash
./scripts/local/voice-runtime-control.sh memory-load-local ".jarvis" true
```

Resultado esperado:

- `loaded=true`.
- `persisted_source=true`.
- `imported_count=1`.
- `memory_proposal_count=1`.
- `applied_to_runtime=false`.

`memory-load-local` lee el snapshot local solo porque David ejecuta este comando. No hay autoload.

## 9. Confirmar que load-local no activa runtime

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`.
- No devuelve `create_mission`.
- `active_memory_rule_count=0`.

Esto es correcto: `memory-load-local` solo recupera proposals al store. No aplica memoria al runtime, no cambia clasificacion y no ejecuta tareas.

## 10. Revisar y aprobar sin activar

```bash
./scripts/local/voice-runtime-control.sh memory-review "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-approve "$PROPOSAL_ID"
```

Resultado esperado:

- `memory-review` deja la proposal revisada.
- `memory-approve` deja la proposal aprobada.
- Todavia no hay regla activa en runtime.

`memory-review` y `memory-approve` no activan runtime por si solos.

## 11. Confirmar que approve tampoco activa runtime

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`.
- No devuelve `create_mission`.
- `active_memory_rule_count=0`.

## 12. Activar memoria explicitamente

```bash
./scripts/local/voice-runtime-control.sh memory-activate "$PROPOSAL_ID"
```

Resultado esperado:

- `active_memory_rule_count=1`.
- `applied_to_runtime=true`.
- La activacion afecta solo a la sesion actual.

`memory-activate` es la accion explicita que puede cambiar clasificacion durante la sesion actual.

## 13. Confirmar cambio de clasificacion

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_mission`.
- `executed=false`.
- `active_memory_rule_applied=true`.

La clasificacion puede usar memoria activa, pero este smoke test manual no ejecuta tareas reales ni crea misiones reales.

## 14. Confirmar que el sensitive boundary gana

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho y lee mi .env"
```

Resultado esperado:

- `intent=requires_approval`.
- `approval_required=true`.
- El sensitive boundary gana sobre cualquier memoria activa.

Aunque exista memoria activa para interpretar "probar este nicho", una peticion sensible como leer `.env` no puede degradarse a una accion permitida.

## 15. Limpiar estado final

```bash
./scripts/local/voice-runtime-control.sh memory-deactivate "$PROPOSAL_ID" "smoke test manual terminado"
./scripts/local/voice-runtime-control.sh memory-active-clear
./scripts/local/voice-runtime-control.sh memory-clear
rm -rf .jarvis
./scripts/local/voice-runtime-control.sh status
git status --short
```

Resultado esperado:

- `active_memory_rule_count=0`.
- `memory_proposal_count=0`.
- No queda `.jarvis` de prueba.
- `git status --short` solo muestra cambios documentales intencionados, o queda limpio si la guia ya esta versionada.

## Criterio de exito

El smoke test manual se considera correcto solo si David pega salida real de terminal que demuestre:

- La memoria se guarda solo tras `memory-save-local`.
- La memoria se carga solo tras `memory-load-local`.
- `memory-load-local` no cambia la clasificacion.
- `memory-review` y `memory-approve` no cambian la clasificacion por si solos.
- `memory-activate` cambia la clasificacion compatible a `create_mission`.
- La peticion con `.env` queda en `requires_approval`.
- La limpieza final borra `.jarvis` y memoria runtime.

Hasta entonces, esta guia queda como checklist documental pendiente de ejecucion real.
