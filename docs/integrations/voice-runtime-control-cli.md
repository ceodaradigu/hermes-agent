# Voice Runtime control CLI

`scripts/local/voice-runtime-control.sh` permite consultar y controlar la Voice Runtime API local sin usar micrófono, wake word, STT ni reproducción de audio.

El script usa `http://127.0.0.1:8000` como URL base por defecto. Puedes cambiarla con `JARVIS_BASE_URL`.

```bash
scripts/local/voice-runtime-control.sh status
JARVIS_BASE_URL=http://127.0.0.1:9000 scripts/local/voice-runtime-control.sh status
```

## Comandos

Consultar estado:

```bash
scripts/local/voice-runtime-control.sh status
```

Arrancar o detener el runtime:

```bash
scripts/local/voice-runtime-control.sh start
scripts/local/voice-runtime-control.sh stop
```

Cambiar modo:

```bash
scripts/local/voice-runtime-control.sh mode awake
scripts/local/voice-runtime-control.sh mode asleep
```

Enviar comandos de control simulados:

```bash
scripts/local/voice-runtime-control.sh control "jarvis silencio"
scripts/local/voice-runtime-control.sh control "jarvis no escuches"
```

Enviar una transcripcion simulada:

```bash
scripts/local/voice-runtime-control.sh transcript "abre el panel de estado"
```

Consultar o limpiar feedback acumulado:

```bash
scripts/local/voice-runtime-control.sh feedback-list
scripts/local/voice-runtime-control.sh feedback-clear
```

Guardar una corrección de entendimiento en memoria:

```bash
scripts/local/voice-runtime-control.sh feedback-add \
  "monta algo para probar este nicho" \
  "create_asset" \
  "create_mission" \
  "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero." \
  "Crear misión de validación antes de crear landing."
```

`feedback-add` llama a `POST /voice/runtime/feedback`, imprime la respuesta JSON de la API y solo guarda feedback temporal en memoria. No aplica la corrección automáticamente.

`interpreted_intent` puede pasarse como cadena vacía:

```bash
scripts/local/voice-runtime-control.sh feedback-add \
  "monta algo para probar este nicho" \
  "" \
  "create_mission"
```

Previsualizar una corrección de entendimiento sin guardarla ni aplicarla:

```bash
scripts/local/voice-runtime-control.sh feedback-preview \
  "monta algo para probar este nicho" \
  "create_asset" \
  "create_mission" \
  "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero." \
  "Crear misión de validación antes de crear landing."
```

`interpreted_intent` puede pasarse como cadena vacía:

```bash
scripts/local/voice-runtime-control.sh feedback-preview \
  "monta algo para probar este nicho" \
  "" \
  "create_mission"
```

Aplicar una corrección revisada como regla temporal en memoria:

```bash
scripts/local/voice-runtime-control.sh feedback-apply-reviewed \
  "monta algo para probar este nicho" \
  "create_asset" \
  "create_mission" \
  "Cuando hablo de probar un nicho, normalmente quiero una misión de validación primero." \
  "Crear misión de validación antes de crear landing."
```

`feedback-apply-reviewed` llama a `POST /voice/runtime/feedback/apply-reviewed`. La regla solo vive en memoria durante el proceso, devuelve `applied_persistently=false` y puede corregir transcripciones posteriores que contengan el alias sugerido, por ejemplo `"probar este nicho"`.

Listar o limpiar reglas temporales aplicadas:

```bash
scripts/local/voice-runtime-control.sh feedback-applied-list
scripts/local/voice-runtime-control.sh feedback-applied-clear
```

`feedback-applied-clear` elimina las reglas aplicadas sin tocar el buffer de `feedback-add`.

## Memory proposal commands

Listar propuestas de memoria User Understanding en memoria:

```bash
scripts/local/voice-runtime-control.sh memory-proposals
```

Crear una propuesta desde feedback revisado:

```bash
scripts/local/voice-runtime-control.sh memory-propose-from-feedback \
  "monta algo para probar este nicho" \
  "create_mission" \
  "probar este nicho" \
  "David reviso que probar un nicho debe empezar como mision de validacion."
```

`memory-propose-from-feedback` llama a `POST /voice/runtime/memory/proposals/from-applied-feedback` con `source=user_reviewed_feedback` y `applied_persistently=false`.

Consultar una propuesta por id:

```bash
scripts/local/voice-runtime-control.sh memory-proposal ump_123
```

Marcar una propuesta como revisada:

```bash
scripts/local/voice-runtime-control.sh memory-review ump_123
```

Aprobar una propuesta:

```bash
scripts/local/voice-runtime-control.sh memory-approve ump_123
scripts/local/voice-runtime-control.sh memory-approve ump_123 David
```

Si no se pasa `approved_by`, el CLI usa `David`. La aprobacion solo cambia el estado de la propuesta en memoria; no aplica memoria al router ni al runtime.

Activar explicitamente una propuesta aprobada en el runtime actual:

```bash
scripts/local/voice-runtime-control.sh memory-activate ump_123
scripts/local/voice-runtime-control.sh memory-activate ump_123 David
```

`memory-activate` llama a `POST /voice/runtime/memory/proposals/{proposal_id}/activate`. Solo acepta proposals aprobadas, activas, no sensibles y con `alias` y `target_intent` no vacios. La regla activa vive solo en memoria del proceso, devuelve `persisted=false` y `applied_to_runtime=true`, y puede reclasificar transcripts que contengan el alias.

`memory-activate` si aplica una proposal `approved` al runtime de la sesion. Esa aplicacion es explicita, reversible y vive solo en memoria del proceso.

`memory-activate` es el primer punto donde una memoria aprobada puede afectar el runtime, y requiere una accion explicita. `memory-approve` no activa memoria automaticamente, `memory-load-local` no activa memoria automaticamente y no hay autoload.

Listar, desactivar o limpiar reglas activas:

```bash
scripts/local/voice-runtime-control.sh memory-active-list
scripts/local/voice-runtime-control.sh memory-deactivate ump_123 "validacion terminada"
scripts/local/voice-runtime-control.sh memory-active-clear
```

`memory-active-list` solo inspecciona reglas activas en memoria del proceso. `memory-deactivate` revierte una regla activa por proposal id y `memory-active-clear` elimina todas las reglas activas runtime sin borrar necesariamente las proposals.

Las reglas activas no ejecutan tareas ni crean misiones reales. `transcript` cambia solo a nivel de intencion y mantiene `executed=false`. El boundary sensible gana siempre: si el transcript contiene `.env`, `password` u otros terminos sensibles, el resultado sigue siendo `requires_approval`.

Desactivar una propuesta:

```bash
scripts/local/voice-runtime-control.sh memory-disable ump_123
scripts/local/voice-runtime-control.sh memory-disable ump_123 "Ya no aplica."
```

Eliminar una propuesta:

```bash
scripts/local/voice-runtime-control.sh memory-delete ump_123
```

Limpiar todas las propuestas:

```bash
scripts/local/voice-runtime-control.sh memory-clear
```

Estos comandos gestionan proposals en memoria durante la vida del proceso. No persisten, no escriben memoria en disco y no cambian el comportamiento de `transcript`.

## Memory snapshot commands

Exportar un snapshot JSON de las propuestas de memoria User Understanding en memoria:

```bash
scripts/local/voice-runtime-control.sh memory-snapshot
```

Importar un snapshot JSON literal:

```bash
scripts/local/voice-runtime-control.sh memory-snapshot-import \
  '{"version":"1","proposals":[],"proposal_count":0,"active_count":0,"sensitive_count":0,"persisted":false}' \
  false
```

`memory-snapshot` llama a `GET /voice/runtime/memory/snapshot` e imprime la respuesta JSON.

`memory-snapshot-import` llama a `POST /voice/runtime/memory/snapshot/import` con el JSON literal recibido como argumento. El argumento opcional `replace` acepta `true` o `false`; si se omite, usa `false`.

Estos comandos exportan e importan snapshots solo en memoria/string JSON. No aceptan rutas de archivo, no leen archivos, no escriben archivos y no persisten memoria en disco. Importar un snapshot no aplica memoria al router/runtime y no cambia la clasificacion de `transcript`.

Guardar un snapshot local por accion explicita:

```bash
scripts/local/voice-runtime-control.sh memory-save-local
scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" true
scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" false
```

`memory-save-local` llama a `POST /voice/runtime/memory/local/save`, exporta el snapshot actual desde memoria y lo escribe bajo `.jarvis/user_understanding/`. El argumento opcional `base_dir` usa `.jarvis` por defecto. El argumento opcional `create_backup` acepta solo `true` o `false` y usa `true` por defecto.

Este comando crea `memory_proposals.snapshot.json`, anade un evento a `audit_log.jsonl` y crea backup en `backups/` solo si ya existia un snapshot previo y `create_backup=true`. No implementa `load-local`, no lee memoria local, no autoload, no aplica memoria al router/runtime y no cambia `transcript`.

Cargar un snapshot local por accion explicita:

```bash
scripts/local/voice-runtime-control.sh memory-load-local
scripts/local/voice-runtime-control.sh memory-load-local ".jarvis" true
scripts/local/voice-runtime-control.sh memory-load-local ".jarvis" false
```

`memory-load-local` llama a `POST /voice/runtime/memory/local/load` y lee solo `.jarvis/user_understanding/memory_proposals.snapshot.json`, resuelto por el backend. El argumento opcional `base_dir` usa `.jarvis` por defecto. El argumento opcional `replace` acepta solo `true` o `false` y usa `true` por defecto.

`memory-load-local` no activa runtime. Solo recupera proposals al store para inspeccion, revision y aprobacion posterior.

Este comando importa proposals al store para poder listarlas y revisarlas. No acepta ruta directa al snapshot, no implementa autoload, no aplica memoria al router/runtime, no cambia `transcript`, no ejecuta tareas reales y no crea misiones reales.

Consultar estado de memoria local por accion explicita:

```bash
scripts/local/voice-runtime-control.sh memory-local-status
scripts/local/voice-runtime-control.sh memory-local-status ".jarvis"
```

`memory-local-status` llama a `GET /voice/runtime/memory/local/status`, inspecciona solo las rutas controladas bajo `.jarvis/user_understanding/`, informa existencia, tamanos, backups, checksum y `persisted` cuando el snapshot existe. No importa memoria, no autoload, no aplica memoria al router/runtime y no cambia `transcript`.

Crear backup manual del snapshot local:

```bash
scripts/local/voice-runtime-control.sh memory-backup-local
scripts/local/voice-runtime-control.sh memory-backup-local ".jarvis"
```

`memory-backup-local` llama a `POST /voice/runtime/memory/local/backup` y copia `memory_proposals.snapshot.json` a `.jarvis/user_understanding/backups/`. Tambien escribe el evento `memory_snapshot_backed_up` en `audit_log.jsonl` sin incluir contenido de proposals.

Borrar memoria local explicitamente:

```bash
scripts/local/voice-runtime-control.sh memory-delete-local
scripts/local/voice-runtime-control.sh memory-delete-local ".jarvis" true
scripts/local/voice-runtime-control.sh memory-delete-local ".jarvis" false
```

`memory-delete-local` llama a `DELETE /voice/runtime/memory/local`. El argumento opcional `include_backups` acepta `true` o `false` y usa `true` por defecto. Borra snapshot y audit log; si `include_backups=true`, borra tambien `backups/`.

## Endpoints

| Comando | Metodo | Endpoint |
| --- | --- | --- |
| `status` | `GET` | `/voice/runtime/status` |
| `start` | `POST` | `/voice/runtime/start` |
| `stop` | `POST` | `/voice/runtime/stop` |
| `mode <mode>` | `POST` | `/voice/runtime/mode` |
| `control <text>` | `POST` | `/voice/runtime/control` |
| `transcript <text>` | `POST` | `/voice/runtime/transcript` |
| `feedback-list` | `GET` | `/voice/runtime/feedback` |
| `feedback-clear` | `DELETE` | `/voice/runtime/feedback` |
| `feedback-add <original_text> <interpreted_intent> <corrected_intent> [correction_note] [preferred_next_step]` | `POST` | `/voice/runtime/feedback` |
| `feedback-preview <original_text> <interpreted_intent> <corrected_intent> [correction_note] [preferred_next_step]` | `POST` | `/voice/runtime/feedback/preview` |
| `feedback-apply-reviewed <original_text> <interpreted_intent> <corrected_intent> [correction_note] [preferred_next_step]` | `POST` | `/voice/runtime/feedback/apply-reviewed` |
| `feedback-applied-list` | `GET` | `/voice/runtime/feedback/applied` |
| `feedback-applied-clear` | `DELETE` | `/voice/runtime/feedback/applied` |
| `memory-proposals` | `GET` | `/voice/runtime/memory/proposals` |
| `memory-propose-from-feedback <original_text> <corrected_intent> [suggested_alias] [reason]` | `POST` | `/voice/runtime/memory/proposals/from-applied-feedback` |
| `memory-proposal <proposal_id>` | `GET` | `/voice/runtime/memory/proposals/{proposal_id}` |
| `memory-review <proposal_id>` | `POST` | `/voice/runtime/memory/proposals/{proposal_id}/review` |
| `memory-approve <proposal_id> [approved_by]` | `POST` | `/voice/runtime/memory/proposals/{proposal_id}/approve` |
| `memory-disable <proposal_id> [reason]` | `POST` | `/voice/runtime/memory/proposals/{proposal_id}/disable` |
| `memory-delete <proposal_id>` | `DELETE` | `/voice/runtime/memory/proposals/{proposal_id}` |
| `memory-clear` | `DELETE` | `/voice/runtime/memory/proposals` |
| `memory-snapshot` | `GET` | `/voice/runtime/memory/snapshot` |
| `memory-snapshot-import <snapshot_json> [replace]` | `POST` | `/voice/runtime/memory/snapshot/import` |
| `memory-save-local [base_dir] [create_backup]` | `POST` | `/voice/runtime/memory/local/save` |
| `memory-load-local [base_dir] [replace]` | `POST` | `/voice/runtime/memory/local/load` |
| `memory-local-status [base_dir]` | `GET` | `/voice/runtime/memory/local/status` |
| `memory-backup-local [base_dir]` | `POST` | `/voice/runtime/memory/local/backup` |
| `memory-delete-local [base_dir] [include_backups]` | `DELETE` | `/voice/runtime/memory/local` |

El script imprime la respuesta JSON que devuelve la API. Si no recibe comando, muestra el uso y sale con codigo `2`.
