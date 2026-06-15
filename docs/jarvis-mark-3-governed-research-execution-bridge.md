# JARVIS Mark 3 Governed Research Execution Control Plane

PR #136 creó el control-plane gobernado de research: normalización, policy,
approval, capability contract, memoria de outcomes/fallos y hooks de learning,
sin ejecutar research real.

PR #137 conecta el **Local Docs/Repo Research Adapter** para `docs/local_repo`.
Es un adapter mínimo, local, read-only y bounded. No convierte JARVIS en otro
Hermes: Hermes sigue siendo el motor de ejecución general; JARVIS gobierna,
clasifica riesgo, pide aprobación, audita y solo materializa aquí una lectura
local exacta cuando el control-plane la declara legal, segura, autorizada y
técnicamente soportada.

JARVIS no está enjaulado. GitHub, web, docs y repo local no son denegaciones
permanentes por defecto: son capacidades gobernadas. Si una acción es legal,
segura, autorizada, técnicamente soportada y tiene approval/capability real
conectados, JARVIS debe poder preparar o ejecutar el paso autorizado. Las
restricciones son gates de aprobación y setup, no prohibiciones permanentes.

## Flujo

```text
research request
-> normalize target
-> policy decision
-> approval requirement
-> capability check
-> execution candidate
-> preview / awaiting_approval / setup_required / executable_candidate / blocked
-> local candidate read only when source_type is docs/local_repo and scope is exact
-> outcome/failure hooks
```

No hay ejecución web/GitHub en esta PR. No hay threads ni comandos. El adapter
local no recorre directorios y no ejecuta herramientas.

## Source Types

- `github`
- `web`
- `docs`
- `local_repo`

Aliases soportados:

- `source` -> `source_type`
- `topic` -> `query`
- `risk` -> `risk_level`

`query` y `scope` quedan separados. Una query como `docs` no se convierte en
scope de filesystem. `None`, `""` y `" "` se tratan como ausentes.

El fingerprint usa:

- `source_type`
- `normalized_query`
- `normalized_scope`
- `risk_level`
- `goal`

Metadata interna como `repo_root` o canonical paths no entra en el risk text ni
en el fingerprint de research.

## Capability Contract

Cada source tiene un estado explícito:

```text
connected
capability_not_connected_yet
unsupported
```

Estado por defecto desde PR #137:

```text
github     = capability_not_connected_yet
web        = capability_not_connected_yet
docs       = connected
local_repo = connected
```

`docs` y `local_repo` conectan únicamente el adapter local read-only. GitHub y
web siguen devolviendo `setup_required` o `awaiting_approval` según policy y
approval, sin llamadas externas.

## Local Docs/Repo Research Adapter

El adapter local acepta solo un `scope` exacto de archivo:

- `source_type=docs` limita lectura a `docs/`.
- `source_type=local_repo` limita lectura al repo local.
- El scope debe ser un único path relativo.
- No acepta multi-scope.
- No acepta broad scans como `.`, `docs`, `repo root`, `*` o `all`.
- Rechaza path traversal, paths absolutos y `~`.
- Rechaza symlinks.
- Rechaza `.env`, tokens, passwords, credentials, secrets, private keys y
  nombres de archivo sensibles.
- No lee fuera del scope permitido.
- No usa web, GitHub real, providers, threads, comandos ni installs.
- No hace commit, push, merge, deploy ni PR.

El endpoint `/candidate` exige la request completa para una lectura local. Un
`research_id` por sí solo no rehidrata el snapshot de preview como request
ejecutable.

## Policy

- GitHub/web requieren approval por red externa y siguen sin capability real.
- `docs` y `local_repo` pueden ser direct/simple según scope.
- Scope de repo root, docs root o broad requiere approval/setup y no se lee.
- `.env`, credentials, tokens, passwords, secrets, private keys y rutas
  sensibles quedan bloqueados con `permanent_denial=true`.
- Install, commit, push, merge, deploy, money y production quedan bloqueados o
  requieren niveles altos según policy; esta PR no ejecuta ninguno.
- Double/triple approval no se finge: si no hay canal real, devuelve
  `setup_required` con `stronger_approval_channel_not_connected`.

## API

Rutas disponibles:

- `GET /mark-3/research-execution/status`
- `POST /mark-3/research-execution/preview`
- `POST /mark-3/research-execution/candidate`
- `GET /mark-3/research-execution/{research_id}`

No hay endpoint nuevo `/execute` para research. `/candidate` revalida policy,
approval y capability. Para `docs/local_repo` con request completa y scope exacto
permitido, realiza una lectura local segura y controlada. Para GitHub/web o
requests incompletas devuelve estado gobernado sin ejecución silenciosa.

## Integración Mark 3

- Outcome Memory registra outcomes de `setup_required`/failure y de lecturas
  locales exitosas sin persistir contenido.
- Failure Memory registra `capability_not_connected_yet` cuando procede.
- Learning Proposals crea proposal candidates revisables solo para setup real,
  no para denegaciones permanentes por secretos, traversal o acceso inseguro.
- Research Radar de PR #135 puede alimentar planes; si falta scope exacto local,
  `/preview` y `/candidate` devuelven `exact_file_scope_required`.

Hermes sigue siendo el motor. Esta PR no construye otro Hermes, otro runtime ni
otro executor.

## Garantías

- No ejecuta web/GitHub.
- No crea threads.
- No ejecuta comandos.
- No instala dependencias.
- No hace commit, push, merge, PR ni deploy.
- No lee `.env`.
- No recorre directorios.
- No sigue symlinks.
- No rehidrata snapshots redactados como requests ejecutables.
- No añade execute-by-id sensible.
