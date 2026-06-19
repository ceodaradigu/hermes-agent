# PR #164 - Phase 1 Persistent Audit + Memory Brain v2

## Resumen

Esta PR pertenece a `Fase 1 - JARVIS usable en local`.

Implementa dos piezas de control-plane antes de cualquier ejecucion Hermes end-to-end:

1. Auditoria persistente metadata-only para voz, wake, STT/TTS, grabacion, camara, intake, brain adapter, memoria, approvals y Hermes dispatch bloqueado.
2. Memory Brain v2 persistente, explicable, reversible y seguro.

JARVIS gobierna, decide, clasifica riesgo, pide aprobacion, audita y controla. Hermes ejecuta solo en un flujo futuro gobernado. Esta PR no crea otro Hermes, no duplica runtime y no activa ejecucion real.

## Qué Se Implementó

Backend/control-plane:

- `jarvis/persistent_audit.py`
  - `PersistentAuditLedger`
  - SQLite local opcional
  - hash-chain SHA-256 con `previous_hash` + `entry_hash`
  - verificacion basica de tampering
  - export seguro metadata-only
- `jarvis/memory_brain_v2.py`
  - `MemoryBrainV2Store`
  - entities, facts, preferences, decisions, projects y contradictions
  - provenance, confidence, sensitivity, valid_from, superseded_at, source
  - approved, active, forgotten/deleted, review_required, approval_required
  - `reason_to_remember`, `influence_summary`, `why_used`
  - proposal/review/approve/activate/deactivate/supersede/forget/delete auditado
- Endpoints GET read-only:
  - `/mark-3/audit/status`
  - `/mark-3/memory-brain/status`
  - `/mark-3/memory-brain/preview`
- `/mark-3/dashboard/status` ahora expone:
  - `persistent_audit`
  - `memory_brain_v2`
  - `memory_brain` enriquecido con counts v2
- `/mark-3/dashboard/events` y `/stream` agregan:
  - `persistent_audit_state`
  - `memory_brain_v2_state`

Frontend `/jarvis`:

- Drawer `Sistemas` muestra `Persistent Audit`.
- Drawer `Sistemas` muestra `Memory Brain v2`.
- Se muestran counts de entities, facts, preferences, decisions, projects, contradictions, active memories, pending review y forgotten/deleted.
- Se muestra preview de explicacion: por que JARVIS recuerda, que memoria influyo y que queda pendiente de approval/review.
- La pantalla central sigue siendo presencia/orbe/smart bar, no dashboard pesado.

## Qué NO Se Implementó

- No se implemento ejecucion Hermes end-to-end.
- No se creo `/execute`.
- No se llamo Hermes desde frontend.
- No se añadieron approvals reales desde `/jarvis`.
- No se activaron sensores nuevos.
- No hay auto mic, auto camera, grabacion continua ni transcripcion continua.
- No se guarda audio bruto.
- No se guardan frames de camara.
- No se leen `.env`, credenciales ni secretos.
- No se añadieron APIs externas, LLM externo, cloud memory, graph DB obligatoria ni vector DB obligatoria.
- No se instalaron dependencias nuevas.
- No se activo dinero, Stripe, deploy ni email.

## Dónde Se Guarda

Los stores escriben en SQLite solo cuando una instancia recibe `base_dir`/`db_path` explicito o cuando se configura `JARVIS_LOCAL_STATE_DIR`/`JARVIS_STATE_DIR`.

Rutas por defecto bajo un `base_dir` local:

- Audit ledger: `.jarvis/audit/persistent_audit.sqlite3`
- Memory Brain v2: `.jarvis/memory_brain_v2/memory_brain_v2.sqlite3`

Si no hay `base_dir` ni variable de entorno, `create_app()` usa stores en memoria para no crear `.jarvis` en el repo durante tests o arranques read-only.

## Qué Datos Guarda

Audit ledger:

- `schema_version`
- `audit_id`
- `created_at`
- `event_type`
- `surface`
- `source`
- `risk_level`
- `approval_level`
- `session_id`
- `correlation_id`
- `metadata` sanitizada
- `redaction_summary`
- flags negativos de seguridad
- `previous_hash`
- `entry_hash`
- `tamper_evident=true`

Memory Brain v2:

- tipo de memoria: entity/fact/preference/decision/project/contradiction
- content summary seguro
- provenance metadata
- confidence
- sensitivity
- valid_from
- superseded_at / superseded_by
- source
- approved / active
- forgotten / deleted metadata
- reason_to_remember
- influence_summary
- why_used
- review_required / approval_required

## Qué Datos NO Guarda

- audio bruto;
- frames de camara;
- video bruto;
- imagenes;
- secretos;
- `.env`;
- tokens;
- passwords;
- cookies;
- credenciales;
- material de sesion;
- texto completo sensible;
- transcripcion completa;
- prompts privados completos;
- payloads de providers externos.

## Retención Inicial

Audit ledger:

- append-only metadata local;
- sin hard delete de entradas en esta PR;
- export seguro disponible;
- rotacion/retencion fina queda para una PR posterior.

Memory Brain v2:

- forget/delete no borra silenciosamente;
- marca `forgotten=true` o `deleted=true`, desactiva la memoria y deja audit metadata;
- hard delete fisico no se implementa en esta fase.

## Tamper Detection

Cada entrada de audit calcula `entry_hash = SHA256(JSON canonico de la entrada sin entry_hash)`.

Cada entrada enlaza `previous_hash` con el `entry_hash` anterior. La primera usa `GENESIS`.

`verify_chain()` detecta:

- `previous_hash_mismatch`;
- `entry_hash_mismatch`;
- primer `audit_id` invalido;
- cantidad de entradas verificadas.

Esto es tamper-evident basico local, no un transparency log distribuido.

## Cómo Se Explica Una Memoria

`MemoryBrainV2Store.why_remember(memory_id)` devuelve:

- reason_to_remember;
- provenance;
- confidence;
- sensitivity;
- evidence_state;
- approved/active;
- `memory_grants_permission=false`.

`MemoryBrainV2Store.why_used(memory_id)` devuelve:

- why_used;
- influence_summary;
- active;
- `used_for_permission=false`;
- `autoload_allowed=false`.

## Cómo Se Olvida O Desactiva

- `deactivate_memory()` marca `active=false` y audita `memory_proposal_deactivated`.
- `forget_memory()` marca `forgotten=true`, `active=false` y audita `memory_proposal_forgotten`.
- `delete_memory()` marca `deleted=true`, `forgotten=true`, `active=false` y audita `memory_proposal_deleted`.
- No hay borrado silencioso.

## Seguridad

- La memoria no concede permisos.
- La memoria activa no autoriza acciones sensibles.
- Memoria sensible requiere review/approval.
- Memoria sensible no se auto-activa.
- No hay autoload peligroso.
- No se guardan secretos ni credenciales.
- Atributos health/political/religion/sexual/biometric se rechazan salvo peticion explicita del usuario.
- Si falta evidencia, se conserva `unknown`.
- Hermes dispatch queda `false`.

## Cómo Probar

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.

python -m py_compile $(find jarvis -name '*.py')

PYTHONPATH=. python -m pytest -c /dev/null \
  tests/jarvis/test_pr_164_persistent_audit_memory_brain_v2.py \
  -q -x

PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20

git diff --check

cd web && npm run build
```

## Repos Externas Revisadas

| Repo | URL | Licencia visible | Qué se tomó |
|---|---|---|---|
| `TheStack-ai/jarvis-orb` | https://github.com/TheStack-ai/jarvis-orb | MIT | Patron conceptual de memoria local, entidades, contradicciones y visibilidad. Reimplementado en store propio; no MCP runtime, no orb runtime. |
| `getzep/graphiti` | https://github.com/getzep/graphiti | Apache-2.0 | Patron conceptual de temporal/provenance graph memory. No se adopto Neo4j ni graph runtime. |
| `mem0ai/mem0` | https://github.com/mem0ai/mem0 | Apache-2.0 | Patron conceptual de memoria con extraction/consolidation/retrieval. No se copio algoritmo ni dependencia. |
| `chroma-core/chroma` | https://github.com/chroma-core/chroma | Apache-2.0 | Referencia de vector/search infra. No se adopto vector DB obligatoria. |
| `codenotary/immudb` | https://github.com/codenotary/immudb | Business Source License 1.1; Change License Apache 2.0 | Patron conceptual de append-only/tamper-evident history. No se adopto servidor ni libreria. |
| `sigstore/rekor` | https://github.com/sigstore/rekor | Apache-2.0 | Patron conceptual de transparency log metadata-only. No se adopto servidor externo. |
| `google/trillian` | https://github.com/google/trillian | Apache-2.0 | Patron conceptual de log verificable. No se adopto infraestructura distribuida. |
| `Yelp/detect-secrets` | https://github.com/Yelp/detect-secrets | Apache-2.0 | Patron conceptual de denylist/redaction para secretos. Reimplementado con marcadores locales minimos. |
| `trufflesecurity/trufflehog` | https://github.com/trufflesecurity/trufflehog | AGPL-3.0 | Referencia de clases de secretos y credenciales. No se instalo ni se copio codigo. |
| `semgrep/semgrep` | https://github.com/semgrep/semgrep | LGPL-2.1 | Referencia conceptual de reglas/patrones. No se integro runtime ni ruleset externo. |

## Código Copiado/Adaptado/Reimplementado

- Codigo copiado: ninguno.
- Codigo adaptado desde repos externas: ninguno.
- Reimplementado:
  - SQLite local store.
  - hash-chain simple SHA-256.
  - redaccion/sanitizacion por marcadores locales.
  - memory lifecycle explicable.
  - read model/dashboard/event stream metadata-only.

## Riesgos

- Hash-chain local detecta cambios en filas, pero no protege contra borrado total del archivo.
- No hay firma externa ni timestamp authority.
- No hay compaction/retention avanzada.
- La memoria no hace retrieval semantico todavia.
- No hay UI de mutacion para aprobar/olvidar desde `/jarvis`; eso es intencional.
- Sensitive attribute detection inicial es conservadora y por marcadores.

## Siguiente PR Recomendada

PR #165 recomendado: `Governed Memory Review Console + Audit Rotation`.

Objetivo:

- UI/CLI interna para revisar propuestas de memoria sin acciones peligrosas.
- Retention/rotation del audit ledger.
- Export firmado local opcional.
- Diff de memoria antes/despues.
- Mantener approval real fuera de `/jarvis` hasta que el ApprovalGateway end-to-end este probado.
