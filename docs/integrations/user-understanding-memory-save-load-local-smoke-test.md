# User Understanding memory save/load-local smoke test

Esta guia valida el flujo real completo de `memory-save-local` + `memory-load-local`.

El objetivo es confirmar que JARVIS puede guardar y cargar proposals desde `.jarvis` solo mediante acciones explicitas, sin autoload y sin aplicar memoria al router/runtime.

Este smoke test no ejecuta tareas reales, no crea misiones reales, no conecta con MissionControl y no conecta con Hermes runtime. Tambien confirma que `transcript` no cambia: recuperar proposals al store no activa aprendizaje operativo.

## Alcance

Este flujo valida:

- `memory-save-local` escribe en disco solo por accion explicita.
- `memory-load-local` lee desde disco solo por accion explicita.
- No hay autoload.
- `load-local` no aplica memoria al router/runtime.
- `transcript` no cambia tras cargar el snapshot.
- `.jarvis` es memoria local de usuario y no debe versionarse.
- El flujo respeta `docs/jarvis-north-star.md`: privacidad local, control humano, incertidumbre explicita y no ejecucion sin aprobacion.

Esta fase permite recuperar proposals, no activar aprendizaje operativo todavia.

Para validar el flujo completo desde memoria local persistida hasta activacion aprobada, ver `docs/integrations/user-understanding-memory-load-approve-activate-smoke-test.md`. Ese smoke test cubre `load-local` -> `review` -> `approve` -> `activate` y confirma que la clasificacion cambia solo tras `memory-activate`.

## 1. Arrancar JARVIS local

En una terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

## 2. Abrir otra terminal

En una segunda terminal:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
```

## 3. Limpiar memoria local de prueba

```bash
rm -rf .jarvis
```

Resultado esperado:

- No queda memoria local previa bajo `.jarvis` para este smoke test.

## 4. Limpiar proposals en runtime

```bash
./scripts/local/voice-runtime-control.sh memory-clear
```

Resultado esperado:

- `memory_proposal_count=0`

## 5. Crear proposal desde feedback revisado

```bash
./scripts/local/voice-runtime-control.sh memory-propose-from-feedback \
  "monta algo para probar este nicho" \
  "create_mission" \
  "probar este nicho" \
  "David reviso que probar un nicho debe empezar como mision de validacion."
```

Resultado esperado:

- Se crea una proposal.
- `status=proposed`
- `active=false`
- `memory_proposal_count=1`

## 6. Guardar snapshot local explicitamente

```bash
./scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" true
```

Resultado esperado:

- `saved=true`
- `persisted=true`
- `applied_to_runtime=false`
- `proposal_count=1`
- `active_count=0`
- `sensitive_count=0`
- `checksum` presente
- `snapshot_path=.jarvis/user_understanding/memory_proposals.snapshot.json`
- `audit_log_path=.jarvis/user_understanding/audit_log.jsonl`

## 7. Verificar archivos escritos

```bash
find .jarvis/user_understanding -maxdepth 3 -type f -print
cat .jarvis/user_understanding/memory_proposals.snapshot.json
cat .jarvis/user_understanding/audit_log.jsonl
```

Resultado esperado:

- Existe `.jarvis/user_understanding/memory_proposals.snapshot.json`.
- Existe `.jarvis/user_understanding/audit_log.jsonl`.
- El snapshot contiene `persisted=true`.
- El snapshot contiene `proposal_count=1`.
- El audit log contiene `event=memory_snapshot_saved`.

## 8. Limpiar proposals del runtime sin borrar .jarvis

No borres `.jarvis` en este paso. El objetivo es vaciar el store en runtime y conservar el snapshot local.

```bash
./scripts/local/voice-runtime-control.sh memory-clear
./scripts/local/voice-runtime-control.sh memory-proposals
```

Resultado esperado:

- `proposals=[]`
- `memory_proposal_count=0`

## 9. Cargar snapshot local explicitamente

```bash
./scripts/local/voice-runtime-control.sh memory-load-local ".jarvis" true
```

Resultado esperado:

- `loaded=true`
- `persisted_source=true`
- `imported_count=1`
- `memory_proposal_count=1`
- `applied_to_runtime=false`
- `checksum` presente
- El audit log contiene `event=memory_snapshot_loaded`.

## 10. Confirmar que la proposal vuelve al store

```bash
./scripts/local/voice-runtime-control.sh memory-proposals
```

Resultado esperado:

- Vuelve a aparecer la proposal.
- `alias=probar este nicho`
- `target_intent=create_mission`
- `status=proposed`
- `active=false`

## 11. Confirmar que load-local no cambia router/runtime

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

Resultado esperado:

- `intent=create_asset`
- No debe devolver `create_mission`.
- `executed=false`

Esto es correcto: `memory-load-local` solo recupera proposals al store. No activa memoria en el router/runtime y no cambia la clasificacion de `transcript`.

Nota PR #47: incluso despues de `memory-load-local` y `memory-approve`, la memoria sigue sin afectar al runtime hasta ejecutar `memory-activate <proposal_id>` de forma explicita. No hay autoload ni activacion automatica por aprobar.

## 12. Confirmar status

```bash
./scripts/local/voice-runtime-control.sh status
```

Resultado esperado:

- `memory_proposal_count=1`
- `feedback_count=0` si no hubo feedback adicional.
- `applied_feedback_count=0` si no hubo feedback aplicado.

## 13. Limpieza final

```bash
rm -rf .jarvis
./scripts/local/voice-runtime-control.sh memory-clear
git status --short
```

Resultado esperado:

- No queda memoria local de prueba.
- El repo queda limpio salvo cambios documentales intencionados de esta PR.

## Opcional: mantenimiento local PR #46

Despues de `memory-save-local`, consultar estado local:

```bash
./scripts/local/voice-runtime-control.sh memory-local-status ".jarvis"
```

Resultado esperado:

- `snapshot_exists=true`
- `persisted=true`
- `checksum` presente
- `applied_to_runtime=false`

Crear backup manual:

```bash
./scripts/local/voice-runtime-control.sh memory-backup-local ".jarvis"
```

Resultado esperado:

- `backed_up=true`
- Se crea un archivo en `.jarvis/user_understanding/backups/`.
- El audit log contiene `event=memory_snapshot_backed_up`.

Borrar memoria local:

```bash
./scripts/local/voice-runtime-control.sh memory-delete-local ".jarvis" true
./scripts/local/voice-runtime-control.sh memory-local-status ".jarvis"
```

Resultado esperado:

- `deleted=true` en el delete.
- `snapshot_exists=false` despues del delete.
- No hay autoload.
- No aplica memoria al router/runtime.
- `transcript` no cambia.

Confirmar repo limpio o solo con cambios intencionados:

```bash
git status --short
```

## Confirmaciones de seguridad

- `.jarvis` es memoria local de usuario y no debe versionarse.
- `memory-save-local` no implica que la memoria sea segura para aplicar.
- `memory-load-local` no activa proposals ni aplica aprendizaje operativo.
- No hay autoload.
- El router/runtime no lee ni aplica esta memoria.
- `transcript` conserva su comportamiento previo.
- Ningun paso ejecuta tareas reales ni crea misiones reales.
