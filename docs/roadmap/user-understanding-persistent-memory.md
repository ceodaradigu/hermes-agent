# User Understanding Persistent Memory

## 1. Objetivo

Esta fase diseña la futura memoria persistente segura de User Understanding para pasar de reglas temporales en memoria a memoria persistente revisada, aprobada, auditable y reversible.

El diseño debe mantenerse alineado con `docs/jarvis-north-star.md`: JARVIS debe aprender de David de forma progresiva sin perder privacidad, transparencia, pensamiento critico, seguridad ni control humano.

La memoria futura debe permitir aprender de David de forma amplia:

- comunicacion y tono.
- intencion real detras de frases incompletas o indirectas.
- contexto personal, tecnico y de negocio.
- ejecucion y ritmo de trabajo preferido.
- monetizacion, foco y retorno esperado.
- frustracion, bloqueos y patrones de decision.
- prioridades, limites y estilo de decision.

## 2. Que NO implementa esta fase

Esta fase es solo documentacion. No implementa:

- persistencia.
- base de datos.
- archivos de memoria.
- aprendizaje automatico opaco.
- ejecucion real.
- conexion con MissionControl.
- conexion con Hermes runtime.
- memoria sensible sin consentimiento explicito.

Tampoco crea misiones reales, tareas reales, threads, background services, audio, wake word, STT, reproduccion de audio, autoarranque, dependencias, CI ni cambios de runtime.

## 3. Principios de seguridad

La memoria persistente futura debe obedecer estos principios:

- Privacidad local: las memorias deben permanecer bajo control local por defecto.
- Transparencia: David debe poder ver que se propone recordar, por que y desde que feedback nace.
- Auditabilidad: cada cambio de estado debe dejar rastro revisable.
- Reversibilidad: una memoria debe poder desactivarse, eliminarse o expirar sin efectos ocultos.
- Revision humana: ninguna memoria persistente debe activarse sin aprobacion explicita.
- ApprovalGateway obligatorio para acciones sensibles.
- PolicyEngine sigue ganando ante cualquier conflicto.
- Los terminos sensibles no pueden ser degradados por memoria aprendida.
- La memoria nunca puede usarse para saltarse aprobaciones.

Una preferencia aprendida puede orientar estilo, interpretacion o priorizacion, pero no puede autorizar acciones sensibles ni reducir limites de seguridad.

## 4. Tipos de memoria futura

Tipos conceptuales de memoria:

- `communication_preferences`: tono, idioma, longitud, nivel de detalle y formato preferido.
- `intent_aliases`: frases de David que suelen mapear a intenciones conocidas.
- `business_goals`: objetivos de negocio, productos, nichos o lineas de trabajo.
- `monetization_preferences`: preferencias sobre ROI, modelos de ingreso, pricing, validacion y foco comercial.
- `execution_preferences`: tamano de PR, pasos pequenos, validacion frecuente, aversion a romper flujos existentes.
- `decision_style`: como decide David, que evidencia pide y cuando prefiere velocidad frente a analisis.
- `contrarian_triggers`: patrones que deben activar contradiccion o revision critica.
- `sensitive_boundaries`: limites explicitos sobre privacidad, identidad, datos, acciones o temas.
- `project_context`: contexto estable de proyectos, objetivos, restricciones y estado conceptual.
- `rejected_assumptions`: interpretaciones o suposiciones que David ya rechazo.
- `learning_notes`: notas revisadas que todavia no encajan en un tipo mas especifico.

## 5. Ciclo propuesto

Flujo futuro propuesto:

1. `feedback-preview`: mostrar como se interpretaria el feedback antes de aplicarlo.
2. `feedback-add`: registrar feedback temporal para revision.
3. `feedback-apply-reviewed`: aplicar reglas revisadas temporales.
4. `memory-proposal`: generar una propuesta explicita de memoria persistente.
5. Human approval: David revisa y aprueba, edita, rechaza o pospone.
6. Persist reviewed memory: guardar solo la memoria revisada y aprobada.
7. Audit log: registrar origen, aprobacion, cambios y estado.
8. Reversible delete/disable: permitir desactivar o eliminar el efecto de la memoria.
9. Runtime loads approved memory: el runtime carga solo memorias aprobadas, activas y no expiradas.

El paso de feedback temporal a memoria persistente debe ser deliberado. El sistema no debe convertir patrones observados en memoria activa sin una propuesta visible y aprobacion humana.

El sistema de aprendizaje continuo podrá proponer nuevas memorias o roadmap items, pero no debe persistir ni aplicar aprendizaje sin aprobación explícita.

## 6. Estados de una memoria

Estados conceptuales:

- `proposed`: propuesta generada, todavia sin revision.
- `reviewed`: revisada por un flujo humano o semi-asistido, pero no aprobada.
- `approved`: aprobada por David para persistir.
- `active`: aprobada, no expirada y cargable por runtime.
- `disabled`: conservada para auditoria, pero sin efecto.
- `deleted`: eliminada como memoria aplicable; puede quedar un rastro minimo de auditoria si el diseno de privacidad lo permite.
- `expired`: ya no aplicable por fecha o politica de caducidad.

## 7. Modelo de datos conceptual

Ejemplo JSON conceptual, no codigo productivo:

```json
{
  "id": "mem_01HYPOTHETICAL",
  "type": "intent_alias",
  "source": "feedback_apply_reviewed",
  "alias": "probar este nicho",
  "target_intent": "create_mission",
  "confidence": "reviewed",
  "scope": "voice_runtime",
  "approved_by": "David",
  "created_at": "2026-05-14T10:00:00Z",
  "expires_at": null,
  "sensitive": false,
  "active": true,
  "audit": [
    {
      "at": "2026-05-14T10:00:00Z",
      "event": "proposed",
      "source": "feedback_apply_reviewed"
    },
    {
      "at": "2026-05-14T10:05:00Z",
      "event": "approved",
      "by": "David"
    }
  ]
}
```

Campos como `id`, `created_at`, `expires_at`, `scope`, `sensitive`, `active` y `audit` son conceptuales. La forma final debe definirse en una PR posterior antes de implementar persistencia.

## PR #32 — Memory proposal model

Se añade un modelo local en memoria para propuestas futuras de User Understanding memory.

Alcance:

- No persiste propuestas.
- No escribe memoria en disco.
- No aplica propuestas al router.
- No carga propuestas en runtime.
- No cambia la conducta de JARVIS.
- Mantiene propuestas revisables, auditables, reversibles y serializables.

Este paso prepara la siguiente fase: una API de proposals en memoria. La persistencia real sigue fuera de alcance hasta que exista un flujo explicito de revision, aprobacion, auditoria y reversibilidad.

## PR #33 — In-memory memory proposals API

Se exponen endpoints internos para gestionar propuestas de User Understanding memory durante la sesion actual:

- `GET /voice/runtime/memory/proposals`
- `POST /voice/runtime/memory/proposals/from-applied-feedback`
- `GET /voice/runtime/memory/proposals/{proposal_id}`
- `POST /voice/runtime/memory/proposals/{proposal_id}/review`
- `POST /voice/runtime/memory/proposals/{proposal_id}/approve`
- `POST /voice/runtime/memory/proposals/{proposal_id}/disable`
- `DELETE /voice/runtime/memory/proposals/{proposal_id}`
- `DELETE /voice/runtime/memory/proposals`

Alcance:

- No persiste propuestas.
- No escribe memoria en disco.
- `approve` solo aprueba dentro del store de propuestas en memoria.
- `approve` no aplica memoria al router.
- `approve` no cambia comportamiento del runtime ni clasificacion de transcripts.
- No conecta con MissionControl ni Hermes runtime.
- No ejecuta tareas ni crea misiones reales.

Este paso prepara el siguiente flujo de revision: review workflow/CLI para inspeccionar, aprobar, desactivar y eliminar propuestas antes de disenar persistencia.

## PR #34 — Memory proposals CLI

Se anaden comandos locales en `scripts/local/voice-runtime-control.sh` para gestionar propuestas de User Understanding memory en memoria.

Alcance:

- No persiste propuestas.
- `approve` solo cambia el estado del proposal.
- `approve` no aplica memoria al router/runtime.
- No cambia comportamiento de transcript.
- Prepara un review workflow humano para listar, crear, revisar, aprobar, desactivar, eliminar y limpiar proposals antes de disenar persistencia.

## PR #35 — Memory proposals CLI smoke test docs

PR #35 documenta el smoke test real del CLI de memory proposals y confirma que aprobar proposals todavía no cambia el runtime ni persiste memoria.

## PR #36 — JSON snapshot model

Se anade un modelo de snapshot JSON serializable para exportar e importar propuestas de User Understanding memory en memoria.

Alcance:

- Export/import funciona solo desde objeto, dict o string JSON recibido explicitamente.
- No escribe archivos.
- No lee archivos.
- No persiste propuestas.
- No aplica memoria al router/runtime.
- No cambia clasificacion de transcript.
- Snapshots exportados se marcan con `persisted: false`.
- Snapshots importados con `persisted: true` se rechazan para evitar tratar datos persistidos o externos como fuente controlada.

## PR #47 — Explicit runtime activation

Una proposal aprobada puede activarse explicitamente en el runtime con `memory-activate`; no hay autoload, `approve` y `load-local` no activan memoria, la activacion es solo en memoria del proceso y el boundary sensible sigue ganando siempre.
- Propuestas sensibles `active` o `approved` no pueden importarse activas.

Este paso prepara la siguiente fase: persistencia local opt-in con auditoria, revision explicita y reglas de seguridad antes de cargar memoria en runtime.

## PR #48 — Memory activation smoke test docs

PR #48 documenta la validacion real del flujo `memory-propose-from-feedback` -> `memory-review` -> `memory-approve` -> `memory-activate`: `approve` y `memory-load-local` no activan memoria automaticamente, `memory-activate` puede cambiar la clasificacion durante la sesion, y el sensitive boundary sigue ganando siempre.

## PR #37 — Memory snapshot API

Se exponen endpoints internos para exportar/importar snapshots JSON de propuestas de User Understanding memory en memoria:

- `GET /voice/runtime/memory/snapshot`
- `POST /voice/runtime/memory/snapshot/import`

Alcance:

- Export/import ocurre solo en memoria.
- No lee archivos.
- No escribe archivos.
- No persiste propuestas.
- Import solo recibe dict o string JSON en el request.
- Snapshots con `persisted=true` se rechazan.
- Propuestas sensibles `active` o `approved` se rechazan.

## PR #46 — Local status/delete/backup

Se anaden operaciones explicitas de mantenimiento local (`memory-local-status`, `memory-backup-local`, `memory-delete-local`) para inspeccionar, respaldar y borrar snapshots bajo `.jarvis/user_understanding/`, sin autoload, sin aplicar memoria al router/runtime y sin cambiar transcript.
- Import no aplica memoria al router/runtime.
- Import no cambia transcript ni clasificacion.

## PR #38 — Memory snapshot CLI

Se anaden comandos locales en `scripts/local/voice-runtime-control.sh` para exportar/importar snapshots JSON de propuestas de User Understanding memory:

- `memory-snapshot`
- `memory-snapshot-import <snapshot_json> [replace]`

Alcance:

- `memory-snapshot-import` recibe JSON literal como argumento.
- No lee archivos.
- No escribe archivos.
- No persiste memoria en disco.
- Import no aplica memoria al router/runtime.
- Import no cambia transcript ni clasificacion.
- Prepara persistencia local opt-in futura.

## PR #39 — Memory snapshot CLI smoke test docs

PR #39 documenta el smoke test real del CLI de memory snapshots y confirma que export/import funciona solo como JSON en memoria, sin leer/escribir archivos, sin persistencia en disco y sin cambiar el runtime/router.

## PR #40 — Local persistence opt-in design

PR #40 documenta la futura persistencia local opt-in para memory snapshots. No implementa escritura/lectura de archivos. Define ubicacion propuesta, seguridad, auditoria, reversibilidad y roadmap antes de cualquier persistencia real.

## PR #41 — Local path resolver + guardrails

PR #41 prepara resolucion de rutas locales seguras sin I/O como paso previo a persistencia opt-in.

## PR #42 — Explicit save-local

PR #42 anade guardado local explicito de snapshots bajo `.jarvis/user_understanding/`, con audit log JSONL, backup opcional si ya existe snapshot, rechazo de propuestas sensibles `active`/`approved`, y sin `load-local`, autoload, aplicacion al router/runtime ni cambios de transcript.

## PR #43 — Explicit load-local

PR #43 anade carga local explicita desde `.jarvis/user_understanding/memory_proposals.snapshot.json` al store de proposals, con audit log local, rechazo de JSON corrupto y propuestas sensibles `active`/`approved`, sin autoload, sin aplicacion al router/runtime y sin cambios de transcript.

## 8. Reglas anti-autoengano

La memoria no debe convertir a JARVIS en un sistema que siempre confirma a David.

Reglas futuras:

- La memoria no debe confirmar siempre a David ni reforzar decisiones malas solo porque coinciden con preferencias pasadas.
- Contrarian Agent debe revisar patrones dudosos, especialmente cuando haya perdida de foco, complejidad innecesaria, monetizacion debil o riesgo tecnico.
- Si una preferencia aprendida entra en conflicto con seguridad, gana seguridad.
- Si una preferencia aprendida entra en conflicto con monetizacion o foco, JARVIS debe pedir aclaracion o contradecir con argumentos concretos.
- El sistema debe distinguir hecho confirmado, preferencia explicita, patron probable y suposicion.
- Las memorias deben conservar incertidumbre cuando aplique; no deben convertirse en certezas falsas.

## 9. Reglas de privacidad

La memoria persistente futura no debe guardar:

- secretos.
- credenciales.
- contenido de `.env`.
- datos bancarios.
- audio bruto salvo consentimiento explicito futuro.
- datos sensibles sin consentimiento y sin diseno especifico.

Tampoco debe enviar memorias a APIs externas sin un diseno explicito, aprobado y documentado. Cualquier exportacion, sincronizacion o uso externo debe tratarse como una capacidad nueva con revision de seguridad propia.

## 10. Endpoints persistentes futuros propuestos

Los endpoints en memoria de PR #33 ya existen para proposals. Endpoints persistentes y de auditoria siguen siendo futuros:

- `GET /voice/runtime/memory/audit`

Los endpoints persistentes deberian exponer auditoria sin ejecutar acciones reales ni saltarse `PolicyEngine` o `ApprovalGateway`.

## 11. CLI futuro propuesto

Solo propuesto, no implementar en esta fase:

- `memory-propose`
- `memory-list`
- `memory-approve`
- `memory-disable`
- `memory-delete`
- `memory-audit`

El CLI futuro debe priorizar revision clara, diffs legibles, origen de cada propuesta, estado actual, efecto esperado y capacidad de revertir.

## 12. Tests futuros

Casos futuros a cubrir cuando exista implementacion:

- No persistir sin aprobacion.
- No cargar memoria sensible sin consentimiento y politica explicita.
- `PolicyEngine` gana siempre.
- Eliminar memoria desactiva su efecto.
- Memoria expirada no se aplica.
- Audit log se conserva segun la politica definida.
- Nuevas instancias cargan solo memorias aprobadas, activas y no expiradas.
- Memoria aprendida no degrada terminos sensibles.
- Memoria aprendida no salta `ApprovalGateway`.

## 13. Roadmap incremental

PRs futuras propuestas:

- PR A: memory proposal model sin persistencia.
- PR B: in-memory memory proposal API.
- PR C: local JSON persistence opt-in.
- PR D: audit log local.
- PR E: load approved memory at startup.
- PR F: UI/CLI review workflow.
- PR G: encryption/vault design if needed.

Cada PR debe mantener el alcance pequeno, revisable y compatible con `docs/jarvis-north-star.md`. La persistencia real no debe aparecer hasta que exista un flujo claro de propuesta, aprobacion, auditoria y reversibilidad.
