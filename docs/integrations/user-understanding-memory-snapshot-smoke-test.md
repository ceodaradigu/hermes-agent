# User Understanding memory snapshot CLI smoke test

Este documento registra el smoke test local validado manualmente para el flujo
Memory Snapshot CLI de User Understanding.

El objetivo es comprobar que el CLI puede exportar e importar snapshots JSON de
memory proposals usando solo strings JSON en memoria, sin persistencia en disco
y sin aplicar memoria al router ni al runtime.

Este flujo respeta `docs/jarvis-north-star.md`: JARVIS puede avanzar hacia una
memoria progresiva, revisable y controlada por David, pero esta fase sigue
siendo previa a cualquier persistencia local opt-in futura.

## Alcance

Este smoke test:

- Usa `scripts/local/voice-runtime-control.sh`.
- Valida `memory-clear`, `memory-propose-from-feedback`, `memory-snapshot`,
  `memory-snapshot-import`, `memory-proposals` y `transcript`.
- Mantiene el snapshot como string JSON en memoria.
- Confirma que `memory-snapshot-import` no acepta rutas de archivo.
- Confirma que import no cambia la clasificación de `transcript`.
- Confirma que no se ejecutan tareas reales ni se crean misiones reales.

Este smoke test no implementa ni valida:

- Persistencia en disco.
- Lectura de archivos.
- Escritura de archivos.
- Aplicación de memoria al router/runtime.
- Ejecución real de tareas.
- Creación real de misiones.
- Conexión con MissionControl.
- Conexión con Hermes runtime.
- Cambios de endpoints, router, runtime, CI o dependencias.

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

Crear proposal desde feedback revisado:

```bash
./scripts/local/voice-runtime-control.sh memory-propose-from-feedback \
  "monta algo para probar este nicho" \
  "create_mission" \
  "probar este nicho" \
  "David revisó que probar un nicho debe empezar como misión de validación."
```

Resultado esperado:

- Se crea una proposal.
- `status=proposed`.
- `active=false`.
- `memory_proposal_count=1`.

Exportar snapshot JSON a variable de shell, sin escribir archivo:

```bash
SNAPSHOT_JSON="$(
  ./scripts/local/voice-runtime-control.sh memory-snapshot \
    | python -c 'import sys,json; print(json.dumps(json.load(sys.stdin)["snapshot"], ensure_ascii=False))'
)"

echo "$SNAPSHOT_JSON"
```

Resultado esperado:

- JSON válido.
- `version` presente.
- `persisted=false`.
- `proposal_count=1`.
- `active_count=0`.
- `sensitive_count=0`.
- `proposals` contiene la proposal creada.

Limpiar proposals:

```bash
./scripts/local/voice-runtime-control.sh memory-clear
```

Resultado esperado: `memory_proposal_count=0`.

Importar snapshot desde string JSON literal en memoria:

```bash
./scripts/local/voice-runtime-control.sh memory-snapshot-import "$SNAPSHOT_JSON" true
```

Resultado esperado:

- `imported_count=1`.
- `memory_proposal_count=1`.
- `persisted=false`.
- `applied_to_runtime=false`.

Listar proposals:

```bash
./scripts/local/voice-runtime-control.sh memory-proposals
```

Resultado esperado:

- Vuelve a mostrar la proposal importada.
- `status` sigue siendo `proposed`.
- `active` sigue siendo `false`.

Confirmar que import no cambia runtime/router:

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- Sigue devolviendo `intent=create_asset`, no `create_mission`.
- Esto es correcto porque snapshot import todavía no aplica memoria al
  router/runtime.

Limpiar al final:

```bash
./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-proposals
./scripts/local/voice-runtime-control.sh status
```

Resultado esperado:

- `proposals=[]`.
- `memory_proposal_count=0`.

## Resultado global esperado

El smoke test se considera correcto cuando:

- `memory-clear` deja `memory_proposal_count=0`.
- `memory-propose-from-feedback` crea una proposal `proposed` e inactiva.
- `memory-snapshot` exporta JSON válido con `persisted=false`.
- El snapshot se guarda solo en `SNAPSHOT_JSON`, como string JSON en memoria.
- `memory-snapshot-import "$SNAPSHOT_JSON" true` importa una proposal.
- `memory-proposals` vuelve a mostrar la proposal importada.
- `transcript "monta algo para probar este nicho"` sigue devolviendo
  `create_asset`.
- El `memory-clear` final deja proposals vacío.
- `status` confirma `memory_proposal_count=0`.

## Interpretación

Que `transcript` siga devolviendo `create_asset` después de importar el snapshot
es el comportamiento esperado.

En esta fase, `memory-snapshot-import` solo restaura proposals dentro del store
en memoria del proceso local. No lee rutas de archivo, no escribe archivos, no
persiste memoria en disco, no carga memoria aprobada en runtime y no altera la
clasificación del router.

El flujo tampoco ejecuta tareas reales, no crea misiones reales, no conecta con
MissionControl y no conecta con Hermes runtime. Es una fase previa a una
persistencia local opt-in futura, que deberá diseñarse con seguridad, auditoría,
reversibilidad y control humano explícito.
