# JARVIS Mark 3 Governed Research Execution Bridge

PR #136 queda recortada a un control-plane mínimo para preparar investigación
sin ejecutarla.

Flujo:

```text
research request
  -> normalización segura
  -> policy
  -> approval requirement
  -> capability status
  -> candidate_state
```

## Alcance

La capa nueva vive en `jarvis/mark_3_research_execution.py` y soporta cuatro
sources:

- `github`
- `web`
- `docs`
- `local_repo`

Todas las capabilities están por defecto en:

```text
capability_not_connected_yet
setup_required
```

Eso no es denegación permanente. Una petición legal, segura y autorizada puede
convertirse en candidate ejecutable en el futuro cuando exista capability real,
approval válido y canal de aprobación suficiente.

## Lo Que No Hace

- No ejecuta research real.
- No lee archivos.
- No escanea repo local.
- No usa threads.
- No llama GitHub, web, browser ni APIs externas.
- No invoca adapters.
- No crea stop endpoint.
- No ejecuta por `research_id` rehidratando texto guardado.

## Normalización

`normalize_research_request(...)` separa:

- `source_type`
- `query`
- `topic`
- `scope`
- `risk_level`
- `goal`

Aliases:

- `topic` es alias de `query`.
- `source` es alias de `source_type`.
- `risk` es alias de `risk_level`.

`None`, `""` y `" "` cuentan como ausentes. `query` no se copia desde `scope`
y `scope` no se copia desde `query`. El fingerprint se calcula solo sobre los
campos seguros normalizados y redactados. Campos internos como approval,
capability status o ids no entran en el risk text.

## Policy

La policy devuelve:

- `candidate_state`
- `approval_required`
- `required_approval_level`
- `approval_valid`
- `capability_status`
- `blocked_reasons`
- `can_become_executable_candidate`
- `permanent_denial`

GitHub y web requieren aprobación por red externa. Docs y local repo tampoco
ejecutan en esta PR; devuelven `setup_required` porque la capability no está
conectada.

Secretos o credenciales (`.env`, `token`, `password`, `credential`, etc.),
peticiones ilegales, inseguras o no autorizadas devuelven:

```text
candidate_state=blocked
can_become_executable_candidate=false
permanent_denial=true
```

Install, commit, push, merge, deploy, producción y dinero elevan el riesgo y
requieren aprobación fuerte/doble/triple según corresponda. Cuando double o
triple no tienen canal real, la respuesta queda en `setup_required` con
`stronger_approval_channel_not_connected`.

## Snapshots Y Candidate

Preview guarda solo un snapshot seguro/redactado. Ese snapshot se marca como no
rehidratable para ejecución:

```text
safe_to_revalidate_for_execution=false
```

`candidate` con solo `research_id` no recalcula policy desde el snapshot y
devuelve `setup_required` con:

```text
full_request_required_for_safe_policy_recalculation
redacted_snapshot_not_revalidatable
execute_by_id_rehydration_disabled
```

Para recalcular seguridad, el caller debe enviar de nuevo el request completo
en `request` o en campos directos. Incluso entonces esta PR no ejecuta adapters:
solo recalcula policy y devuelve `setup_required` o `blocked`.

## API

Rutas añadidas:

- `GET /mark-3/research-execution/status`
- `POST /mark-3/research-execution/preview`
- `POST /mark-3/research-execution/candidate`
- `GET /mark-3/research-execution/{research_id}`

No existe endpoint stop para esta capa.

## Integración Segura

Para requests legales bloqueadas solo por capability missing, la capa puede
registrar:

- outcome `setup_required`;
- failure memory `adapter_not_connected`;
- learning proposal candidate seguro para conectar capability gobernada.

No registra proposals ni memoria de integración para requests bloqueadas por
policy.
