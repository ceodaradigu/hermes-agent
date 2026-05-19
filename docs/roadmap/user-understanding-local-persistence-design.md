# User Understanding Local Persistence Design

## 1. Objetivo

Esta PR documenta el diseno futuro para pasar de snapshots JSON de User Understanding memory en memoria a persistencia local opt-in.

El objetivo es preparar una fase posterior donde David pueda guardar, cargar, auditar, respaldar y borrar snapshots locales de forma explicita, sin que esa memoria gane capacidad de ejecucion ni salte controles de seguridad.

Principios:

- Mantener privacidad local por defecto.
- Mantener aprobacion explicita de David antes de cualquier escritura, carga o activacion.
- Mantener auditabilidad de cada accion relevante.
- Mantener reversibilidad mediante disable, delete, clear, backup y restore explicito.
- Impedir que memoria aprendida salte `PolicyEngine` o `ApprovalGateway`.
- Separar persistencia local de aplicacion al router/runtime.

La persistencia local futura debe ser una capacidad de almacenamiento controlada, no una autorizacion implicita para ejecutar acciones, reclasificar transcripts o modificar comportamiento sensible.

## 2. Que NO implementa esta fase

Esta fase es solo documentacion. No implementa:

- Codigo.
- Archivos reales de memoria.
- Base de datos.
- Cifrado.
- Carga automatica.
- Aplicacion al router.
- Aplicacion al runtime.
- Ejecucion real.
- Conexion con MissionControl.
- Conexion con Hermes runtime.
- Cambios de endpoints.
- Cambios de CLI.
- Cambios de scripts.
- Cambios de tests.
- Cambios de CI.
- Cambios de requirements.

Tampoco crea misiones reales, ejecuta tareas reales, cambia clasificacion de transcript ni introduce persistencia en disco.

## 3. Ubicacion futura propuesta

Rutas locales propuestas para una implementacion futura:

- `.jarvis/user_understanding/memory_proposals.snapshot.json`
- `.jarvis/user_understanding/audit_log.jsonl`
- `.jarvis/user_understanding/backups/`

Estas rutas no se crean en esta PR.

Si se implementan en una PR posterior, deben quedar fuera de git mediante `.gitignore`, porque pueden contener preferencias, contexto personal, historial de aprobacion o metadatos privados. La ruta `.jarvis/user_understanding/` debe tratarse como estado local privado del usuario, no como artefacto versionable del repositorio.

## 4. Formato futuro

La persistencia local futura debe partir del snapshot JSON actual y conservar compatibilidad conceptual con `UserUnderstandingMemorySnapshot`.

Campos propuestos:

- `schema_version`: version explicita del formato.
- `exported_at`: fecha ISO-8601 del snapshot.
- `persisted`: `true` solo cuando el snapshot se haya escrito de forma explicita mediante un comando o endpoint local de persistencia.
- `proposals`: lista de propuestas de memoria.
- `counts`: resumen de conteos por estado, tipo o sensibilidad.
- `checksum`: opcional futuro para detectar corrupcion o manipulacion accidental.
- `audit`: metadatos minimos de auditoria del snapshot o referencia a eventos del audit log.

Ejemplo conceptual:

```json
{
  "schema_version": 1,
  "exported_at": "2026-05-18T10:00:00Z",
  "persisted": true,
  "source": "local_opt_in",
  "proposals": [],
  "counts": {
    "total": 0,
    "approved": 0,
    "active": 0,
    "disabled": 0,
    "sensitive": 0
  },
  "checksum": null,
  "audit": {
    "saved_at": "2026-05-18T10:00:00Z",
    "saved_by": "David",
    "origin": "memory-save-local"
  }
}
```

`persisted=true` no debe significar "seguro para aplicar". Solo significa "fue escrito localmente por una accion explicita". La activacion runtime debe ser otra fase separada.

## 5. Flujo futuro opt-in

Flujo propuesto:

1. `memory-snapshot` exporta el estado actual en memoria como JSON.
2. `memory-save-local` crea o sobrescribe el archivo local solo tras comando explicito.
3. `memory-backup-local` crea un backup antes de sobrescribir cuando exista un snapshot local previo.
4. `memory-load-local` lee el archivo local solo tras comando explicito.
5. `memory-delete-local` borra la memoria local solo tras confirmacion futura.
6. `memory-restore-local` restaura un backup elegido de forma explicita.
7. `memory-local-status` muestra estado local sin aplicar memoria.
8. `memory-enable-autoload` queda para otra PR separada, porque carga automatica es peligrosa.
9. `memory-disable-autoload`, si existe autoload en el futuro, debe desactivarlo de forma clara y auditable.

La carga local debe reconstruir proposals en memoria, pero no debe aplicar memoria al router/runtime. Cualquier cambio de comportamiento debe requerir una fase posterior con revision, aprobacion, seguridad y auditoria propias.

## 6. Seguridad

Reglas de seguridad para la implementacion futura:

- Nunca guardar secretos.
- Bloquear contenido de `.env`.
- Bloquear passwords.
- Bloquear tokens.
- Bloquear credenciales.
- Bloquear datos bancarios.
- Bloquear tarjetas.
- Rechazar proposals sensibles en estado `active` o `approved` si no existe una politica explicita mas estricta.
- Si hay duda sobre sensibilidad, guardar como `disabled` o rechazar.
- No enviar snapshots ni audit logs a APIs externas.
- No incluir secretos en logs.
- Usar permisos de archivo restrictivos cuando sea posible.
- Marcar cualquier carga local con `source=local_opt_in`.

La memoria local no debe convertirse en un canal para introducir instrucciones peligrosas, degradar terminos sensibles o autorizar acciones que normalmente requieren aprobacion.

## 7. Auditoria

Cada operacion futura de persistencia local debe dejar un evento auditable:

- `save`
- `load`
- `delete`
- `backup`
- `restore`
- `autoload_enable`
- `autoload_disable`

Cada evento debe incluir:

- Accion.
- Fecha.
- Origen, por ejemplo CLI o endpoint local.
- Conteo de proposals.
- Ruta logica o identificador local no sensible.
- Checksum si existe.
- Resultado de validacion.

El audit log no debe incluir secretos ni contenido sensible completo. Debe registrar hechos operativos suficientes para revisar que paso, sin convertir la auditoria en otra copia de datos privados.

## 8. Reversibilidad

La persistencia local futura debe ser reversible:

- `memory-disable` desactiva proposals aplicables.
- `memory-delete` elimina proposals seleccionadas.
- `memory-clear` limpia proposals en memoria.
- `memory-delete-local` elimina el snapshot local.
- Backups permiten recuperacion ante overwrite accidental.
- Restore debe ser explicito.
- Nunca borrar memoria local sin confirmacion futura.

La reversibilidad tambien implica que cargar un snapshot no debe activar comportamiento oculto. Si David carga un snapshot, debe poder inspeccionarlo antes de cualquier aplicacion runtime.

## 9. Carga al runtime

En esta fase futura, cargar un snapshot local no debe aplicar memoria al router/runtime.

PR #48 documenta la validacion real de activacion explicita: `approve` y `memory-load-local` no activan memoria; `memory-activate` si permite cambiar la clasificacion durante la sesion; el sensitive boundary sigue ganando siempre.

## PR #49 — Load-local to approved activation smoke test

PR #49 documenta el flujo real de recuperacion local, revision, aprobacion y activacion:

- Recupera memoria local con `memory-load-local` desde un snapshot guardado explicitamente.
- Confirma que `memory-load-local` no activa runtime.
- Confirma que `memory-review` y `memory-approve` preparan la proposal, pero no cambian clasificacion por si solos.
- Confirma que `memory-activate` si cambia la clasificacion durante la sesion.
- Confirma que el sensitive boundary sigue ganando aunque exista memoria activa.

Aplicar memoria al router debe ser otra fase separada y solo para memoria:

- `reviewed`.
- `approved`.
- segura.
- no sensible.
- activada explicitamente.
- registrada en auditoria.

`PolicyEngine` siempre gana. `ApprovalGateway` siempre gana para acciones sensibles. Ninguna memoria aprendida puede autorizar ejecucion, reducir aprobaciones, relajar limites sensibles o cambiar una denegacion en aprobacion.

## 10. CLI futuro propuesto

Comandos propuestos, no implementados en esta PR:

- `memory-save-local`
- `memory-load-local`
- `memory-delete-local`
- `memory-backup-local`
- `memory-restore-local`
- `memory-local-status`
- `memory-autoload-enable`
- `memory-autoload-disable`

Estos comandos deben ser explicitos, visibles y orientados a control humano. Los comandos de carga y borrado deben mostrar estado, conteos, riesgos y confirmaciones cuando aplique.

## 11. Endpoints futuros propuestos

Endpoints propuestos, no implementados en esta PR:

- `POST /voice/runtime/memory/local/save`
- `POST /voice/runtime/memory/local/load`
- `DELETE /voice/runtime/memory/local`
- `POST /voice/runtime/memory/local/backup`
- `POST /voice/runtime/memory/local/restore`
- `GET /voice/runtime/memory/local/status`

Estos endpoints no deben ejecutar tareas reales, crear misiones reales, conectar con MissionControl, conectar con Hermes runtime ni aplicar memoria al router.

## 12. Tests futuros

Casos futuros a cubrir cuando exista implementacion:

- Save no ocurre sin comando explicito.
- Los archivos locales quedan fuera de git.
- Load rechaza snapshot `persisted=false` si falta metadata requerida para carga local.
- Load rechaza secretos.

## PR #47 — Explicit runtime activation of approved memory

PR #47 anade activacion runtime explicita para proposals aprobadas de User Understanding memory.

- `memory-activate <proposal_id>` activa una proposal aprobada en el runtime actual.
- La activacion es una accion explicita de David.
- No hay autoload.
- `memory-load-local` no activa memoria.
- `memory-approve` no activa memoria.
- La activacion vive solo en memoria del proceso.
- Es reversible con `memory-deactivate <proposal_id>` o `memory-active-clear`.
- `PolicyEngine` y el boundary sensible ganan siempre; textos con `.env`, `password` u otros terminos sensibles siguen en `requires_approval`.
- La memoria activada puede reclasificar el transcript, pero no ejecuta tareas ni crea misiones reales.
- No conecta con MissionControl ni con Hermes runtime.
- Load no aplica router/runtime.
- Delete borra memoria local.
- Backup ocurre antes de overwrite.
- JSON corrupto se rechaza.
- Checksum invalido se rechaza.
- Permisos restrictivos se aplican si la plataforma lo permite.

Tambien debe probarse que los logs no incluyen secretos y que cualquier snapshot cargado queda marcado como `source=local_opt_in`.

## 13. Roadmap recomendado

Roadmap incremental recomendado:

- PR A: local path resolver y guardrails sin escritura.
- PR B: `save-local` explicito.
- PR C: `load-local` explicito.
- PR D: backup/delete/status.
- PR E: audit log JSONL.
- PR F: autoload opt-in separado.
- PR G: active memory application separado y con `ApprovalGateway`.

Cada fase debe mantener alcance pequeno y revisable. La persistencia local debe aparecer antes que cualquier autoload o aplicacion runtime, y la aplicacion runtime debe llegar solo despues de una revision de seguridad especifica.

## PR #41 — Local path resolver + guardrails

Se anade un modulo interno para calcular las rutas locales futuras de User Understanding memory bajo `.jarvis/user_understanding/`.

Alcance:

- Calcula `memory_proposals.snapshot.json`, `audit_log.jsonl` y `backups/`.
- No crea directorios.
- No lee archivos.
- No escribe archivos.
- Los guardrails devuelven `can_read=false` y `can_write=false`.
- Mantiene `persisted=false`.
- Prepara una PR futura de `save-local` explicito.

Este paso no habilita persistencia local, autoload, aplicacion al router/runtime ni ejecucion real.

## PR #42 — Explicit save-local

PR #42 implementa `memory-save-local` como primera escritura local explicita de snapshots de User Understanding memory.

Alcance:

- `memory-save-local` escribe un snapshot solo por accion explicita de David.
- El snapshot se guarda bajo `.jarvis/user_understanding/memory_proposals.snapshot.json`.
- El audit log se escribe en `.jarvis/user_understanding/audit_log.jsonl`.
- Si ya existe snapshot local y `create_backup=true`, crea backup en `.jarvis/user_understanding/backups/`.
- El archivo guardado marca `persisted=true` solo al escribir.
- Rechaza propuestas sensibles `active` o `approved`.
- Rechaza proposals `active` o `approved` cuyo alias/evidence contenga `.env`, password, token, credenciales, banco o tarjeta.
- No implementa `load-local`.
- No implementa autoload.
- No aplica memoria al router/runtime.
- No cambia transcript ni clasificacion.
- No ejecuta tareas reales ni crea misiones reales.

Este paso toca disco solo por accion explicita de save-local y no convierte el snapshot persistido en memoria activa.

## PR #43 — Explicit load-local

PR #43 implementa `memory-load-local` como lectura local explicita de snapshots de User Understanding memory.

Alcance:

- `memory-load-local` lee un snapshot solo por accion explicita de David.
- Lee unicamente desde `.jarvis/user_understanding/memory_proposals.snapshot.json`, resuelto por el resolver local controlado.
- No acepta rutas directas a archivos ni rutas arbitrarias de snapshot.
- No implementa autoload.
- No carga memoria automaticamente al arrancar.
- No aplica memoria al router/runtime.
- No cambia transcript ni clasificacion.
- Importa proposals al store para poder revisar/listar proposals.
- Acepta `persisted=true` solo cuando viene de este archivo local controlado y por load-local explicito.
- Rechaza JSON corrupto o snapshots que no sean objeto JSON.
- Rechaza propuestas sensibles `active` o `approved`.
- Rechaza proposals `active` o `approved` cuyo alias/evidence contenga `.env`, password, token, credenciales, banco o tarjeta.
- Escribe un evento local `memory_snapshot_loaded` en `.jarvis/user_understanding/audit_log.jsonl`.
- No ejecuta tareas reales ni crea misiones reales.

Este paso permite recuperar proposals persistidas al store de revision, pero no convierte esas proposals en aprendizaje activo ni modifica el comportamiento del runtime.

## PR #44 — Save/load local smoke test

PR #44 documenta el flujo real combinado de `memory-save-local` + `memory-load-local` en `docs/integrations/user-understanding-memory-save-load-local-smoke-test.md`.

Alcance:

- Confirma escritura explicita mediante `memory-save-local`.
- Confirma lectura explicita mediante `memory-load-local`.
- Confirma que no hay autoload.
- Confirma que `load-local` no aplica memoria al router/runtime.
- Confirma que `transcript` sigue sin cambiar.

Este paso es solo documentacion: no implementa persistencia nueva, no cambia endpoints, no cambia runtime y no activa aprendizaje operativo.

## PR #46 — Local status/delete/backup

PR #46 implementa mantenimiento local basico para snapshots de User Understanding memory bajo `.jarvis/user_understanding/`.

Alcance:

- `memory-local-status` inspecciona memoria local de forma explicita.
- `memory-backup-local` crea un backup manual de `memory_proposals.snapshot.json` en `backups/`.
- `memory-delete-local` borra memoria local de forma explicita.
- Las operaciones solo actuan bajo `.jarvis/user_understanding/`, resuelto por el resolver local controlado.
- `status` puede calcular checksum y `persisted` si existe snapshot, pero no importa proposals al store.
- `backup` escribe un evento `memory_snapshot_backed_up` en `audit_log.jsonl` sin incluir contenido de proposals, alias, evidence ni secretos.
- `delete` puede borrar snapshot, audit log y backups; con `include_backups=false` conserva backups.
- No hay autoload.
- No carga memoria automaticamente al arrancar.
- No aplica memoria al router/runtime.
- No cambia transcript ni clasificacion.
- No ejecuta tareas reales ni crea misiones reales.

Este paso anade controles explicitos de mantenimiento local, pero mantiene separada la persistencia de cualquier aplicacion operativa de memoria.
