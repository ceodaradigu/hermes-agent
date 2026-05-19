# User Understanding memory local maintenance smoke test

Esta guia valida el mantenimiento local explicito de snapshots bajo `.jarvis/user_understanding/`.

El flujo cubre `memory-save-local`, `memory-local-status`, `memory-backup-local` y `memory-delete-local`. No hay autoload, no se aplica memoria al router/runtime, no cambia `transcript`, no ejecuta tareas reales y no crea misiones reales.

## 1. Arrancar JARVIS local

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

## 2. Preparar terminal de prueba

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
rm -rf .jarvis
./scripts/local/voice-runtime-control.sh memory-clear
```

Resultado esperado:

- No queda memoria local previa.
- `memory_proposal_count=0`.

## 3. Crear proposal

```bash
./scripts/local/voice-runtime-control.sh memory-propose-from-feedback \
  "monta algo para probar este nicho" \
  "create_mission" \
  "probar este nicho" \
  "David reviso que probar un nicho debe empezar como mision de validacion."
```

Resultado esperado:

- Se crea una proposal.
- `status=proposed`.
- `active=false`.

## 4. Guardar snapshot local

```bash
./scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" true
```

Resultado esperado:

- `saved=true`.
- `persisted=true`.
- `applied_to_runtime=false`.
- Existe `.jarvis/user_understanding/memory_proposals.snapshot.json`.

## 5. Consultar estado local

```bash
./scripts/local/voice-runtime-control.sh memory-local-status ".jarvis"
```

Resultado esperado:

- `snapshot_exists=true`.
- `audit_log_exists=true`.
- `persisted=true`.
- `checksum` presente.
- `can_load_explicitly=true`.
- `applied_to_runtime=false`.

## 6. Crear backup manual

```bash
./scripts/local/voice-runtime-control.sh memory-backup-local ".jarvis"
find .jarvis/user_understanding -maxdepth 3 -type f -print
cat .jarvis/user_understanding/audit_log.jsonl
```

Resultado esperado:

- `backed_up=true`.
- Existe un archivo `.jarvis/user_understanding/backups/memory_proposals.snapshot.<timestamp>.json`.
- El audit log contiene `event=memory_snapshot_backed_up`.
- El audit log no incluye `proposals`, `alias` ni `evidence`.

## 7. Borrar memoria local

```bash
./scripts/local/voice-runtime-control.sh memory-delete-local ".jarvis" true
```

Resultado esperado:

- `deleted=true`.
- `snapshot_deleted=true`.
- `audit_log_deleted=true`.
- `backups_deleted=true`.
- `applied_to_runtime=false`.

## 8. Confirmar estado despues del delete

```bash
./scripts/local/voice-runtime-control.sh memory-local-status ".jarvis"
```

Resultado esperado:

- `snapshot_exists=false`.
- `audit_log_exists=false`.
- `backups_dir_exists=false`.
- `can_load_explicitly=false`.

## 9. Confirmar que no hay autoload

Reinicia el proceso local o crea una nueva instancia de runtime mediante el flujo de desarrollo habitual y consulta:

```bash
./scripts/local/voice-runtime-control.sh memory-proposals
```

Resultado esperado:

- No aparece memoria cargada automaticamente desde `.jarvis`.
- Cualquier carga futura debe hacerse con `memory-load-local` explicito.

## 10. Confirmar que transcript no cambia

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- La clasificacion sigue siendo la clasificacion base del router.
- No se aplica la proposal como memoria activa.
- No se crean tareas ni misiones reales.

## 11. Limpieza

```bash
rm -rf .jarvis
./scripts/local/voice-runtime-control.sh memory-clear
git status --short
```

Resultado esperado:

- No quedan artefactos locales de prueba bajo `.jarvis`.
- El repo queda limpio salvo cambios intencionados de la PR.
