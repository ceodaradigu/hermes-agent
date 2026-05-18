# User Understanding memory proposals CLI smoke test

Este documento registra el smoke test local validado manualmente para el flujo de
Memory Proposals CLI de User Understanding.

El objetivo es comprobar que el CLI permite limpiar, crear, revisar, aprobar,
consultar, desactivar y volver a limpiar proposals en memoria, sin persistencia
y sin aplicar memoria al router ni al runtime.

Este flujo respeta `docs/jarvis-north-star.md`: JARVIS puede avanzar hacia un
aprendizaje progresivo, revisable y controlado por David, pero esta fase sigue
siendo previa al aprendizaje persistente real.

## Alcance

Este smoke test:

- Usa `scripts/local/voice-runtime-control.sh`.
- Valida proposals en memoria durante la vida del proceso local.
- Confirma el ciclo `proposed` -> `reviewed` -> `approved` -> `disabled`.
- Confirma que `approve` no cambia la clasificación de `transcript`.
- Confirma que no se ejecutan tareas reales ni se crean misiones reales.

Este smoke test no implementa ni valida:

- Persistencia.
- Escritura de memoria en disco.
- Aplicación de memoria al router/runtime.
- Ejecución real de tareas.
- Creación real de misiones.
- Conexión con MissionControl.
- Conexión con Hermes runtime.
- Cambios de endpoints, router, runtime, CI o dependencias.

Nota: el snapshot API permite export/import en memoria para pruebas, pero
todavia no es persistencia en disco. No lee archivos, no escribe archivos y no
carga memoria en el router/runtime.

## Precondiciones

Arrancar JARVIS local en una terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
```

## Flujo validado

Limpiar proposals:

```bash
./scripts/local/voice-runtime-control.sh memory-clear
```

Resultado esperado: `memory_proposal_count=0`.

Listar proposals vacías:

```bash
./scripts/local/voice-runtime-control.sh memory-proposals
```

Resultado esperado: lista de proposals vacía.

Crear proposal desde feedback revisado:

```bash
./scripts/local/voice-runtime-control.sh memory-propose-from-feedback \
  "monta algo para probar este nicho" \
  "create_mission" \
  "probar este nicho" \
  "David revisó que probar un nicho debe empezar como misión de validación."
```

Resultado esperado:

- `status=proposed`.
- `active=false`.
- El audit contiene el evento `proposed`.

Copiar el `proposal_id` devuelto:

```bash
PROPOSAL_ID="ump_..."
```

Consultar la proposal:

```bash
./scripts/local/voice-runtime-control.sh memory-proposal "$PROPOSAL_ID"
```

Resultado esperado: se muestra la proposal creada, todavía en estado
`proposed` y `active=false`.

Revisar la proposal:

```bash
./scripts/local/voice-runtime-control.sh memory-review "$PROPOSAL_ID"
```

Resultado esperado:

- `status=reviewed`.
- El audit contiene `proposed` y `reviewed`.

Aprobar la proposal:

```bash
./scripts/local/voice-runtime-control.sh memory-approve "$PROPOSAL_ID"
```

Resultado esperado:

- `status=approved`.
- `active=true`.
- `approved_by=David`.
- El audit contiene `proposed`, `reviewed` y `approved`.

Confirmar estado aprobado:

```bash
./scripts/local/voice-runtime-control.sh memory-proposal "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-proposals
```

Resultado esperado: la proposal aparece aprobada y activa dentro del store en
memoria.

Confirmar que aprobar la proposal no cambia el router/runtime:

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- Sigue devolviendo `create_asset`, no `create_mission`.
- Esto es correcto en esta fase porque memory proposals todavía no se aplican
  al router/runtime.

Desactivar la proposal:

```bash
./scripts/local/voice-runtime-control.sh memory-disable "$PROPOSAL_ID" \
  "Validación terminada; limpiando propuesta temporal."
```

Resultado esperado:

- `status=disabled`.
- `active=false`.

Limpiar proposals:

```bash
./scripts/local/voice-runtime-control.sh memory-clear
```

Resultado esperado: proposals vacío y `memory_proposal_count=0`.

Confirmar vacío y estado final:

```bash
./scripts/local/voice-runtime-control.sh memory-proposals
./scripts/local/voice-runtime-control.sh status
```

Resultados esperados:

- `memory-proposals` devuelve proposals vacío.
- `status` devuelve `memory_proposal_count=0`.

## Resultado global esperado

El smoke test se considera correcto cuando:

- `memory-clear` devuelve `memory_proposal_count=0`.
- `memory-propose-from-feedback` devuelve `status=proposed` y `active=false`.
- `memory-review` devuelve `status=reviewed`.
- `memory-approve` devuelve `status=approved`, `active=true` y
  `approved_by=David`.
- El audit contiene `proposed`, `reviewed` y `approved`.
- `transcript "monta algo para probar este nicho"` sigue devolviendo
  `create_asset`.
- `memory-disable` devuelve `status=disabled` y `active=false`.
- El `memory-clear` final deja proposals vacío.
- `status` confirma `memory_proposal_count=0`.

## Interpretación

Que `transcript` siga devolviendo `create_asset` después de `memory-approve` es
el comportamiento esperado.

En esta fase, aprobar una proposal solo cambia su estado dentro del store en
memoria del proceso local. No persiste memoria, no escribe en disco, no carga
memoria aprobada en runtime y no altera la clasificación del router.

La persistencia real, la carga de memorias aprobadas y cualquier efecto sobre
router/runtime quedan para una fase posterior con diseño explícito de seguridad,
auditoría, reversibilidad y control humano.
