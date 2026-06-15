# JARVIS Mark 3 Autonomous Growth, Learning Radar

PR #135 añade la base de aprendizaje y research gobernado para Mark 3.

JARVIS no está enjaulado. Si una acción es legal, segura, autorizada,
técnicamente soportada y existe el approval correcto, puede avanzar a candidato
ejecutable. Las restricciones son gates de aprobación y setup, no prohibiciones
permanentes. La denegación permanente queda reservada para acciones ilegales,
inseguras, no autorizadas, técnicamente imposibles o realmente no soportadas.

Hermes sigue siendo el motor de ejecución. JARVIS gobierna, decide, clasifica
riesgo, pide aprobación, audita y entrega tareas bounded a Hermes cuando existe
capacidad real. Esta PR no crea otro Hermes, otro executor ni rutas nuevas de
internet real. Si JARVIS descubre que Hermes necesita mejorar, puede crear una
propuesta de cambio revisable y, con approval válido, ejecutar ese cambio por el
camino gobernado existente.

## Componentes

- `jarvis/mark_3_outcome_memory.py`: Outcome Memory y Failure Memory in-memory,
  redaccionadas, auditables y con valores desconocidos como `unknown`.
- `jarvis/mark_3_learning_proposals.py`: Learning Proposal Engine con estados
  `proposed`, `approved`, `rejected` y `superseded`.
- `jarvis/mark_3_research_policy.py`: policy approval-aware para research de
  GitHub, web, docs y repo local.
- `jarvis/mark_3_growth_radar.py`: Research Radar Candidate Builder y
  Autonomous Growth Mission Planner.

## Outcome Memory

Outcome Memory registra misión, step, candidate, goal, herramienta/capability,
estado de resultado, estado de evidencia, errores, duración, coste,
approval level, qué funcionó, qué falló, siguiente acción recomendada y fecha.
No guarda secretos ni contenido sensible. Si un dato no existe o no está
verificado, se conserva como `unknown`.

Failure Memory deduplica fallos repetibles: tests colgados, dependencias
faltantes, review bloqueada por red, adapter no conectado, approval
insuficiente, evidencia insuficiente, herramienta no soportada y errores de
scope. El objetivo es no repetir diagnósticos y devolver `setup_required` o la
acción siguiente correcta cuando aplique.

## Learning Proposals

JARVIS puede convertir outcomes y failures en propuestas revisables:

```text
Propuesta: recordar que las capacidades reales deben empezar con vertical slices pequeños.
Evidencia: outcome verificado o fallo repetible.
Confianza: alta.
Riesgo: bajo.
Requiere aprobación: sí.
```

Una propuesta aprobada puede usarse como regla operativa si no contiene
aprendizaje sensible. Aprobar una propuesta no concede permiso de ejecución, no
salta approvals y no habilita herramientas.

## Research Radar

Research Radar prepara investigaciones para que JARVIS crezca:

- buscar repos GitHub útiles para mejorar agentes;
- buscar herramientas nuevas para Hermes;
- buscar patrones de seguridad para tool execution;
- detectar oportunidades de automatización para David;
- analizar docs o papers entregados por el operador.

Cada plan incluye `research_plan`, `sources_to_query`, `risk_level`,
`approval_required`, `expected_value`, `cost_estimate`, `stop_conditions`,
`evidence_required` y `candidate_actions`.

El radar puede investigar GitHub, web, docs o repo local cuando haya approval y
capability. Si falta adapter real para GitHub/web, devuelve:

```text
execution_status: setup_required
capability_status: capability_not_connected_yet
```

Eso no es permanent-deny. Es un gate de setup. Con adapter conectado y approval
válido, un plan legal y seguro puede pasar a `candidate_state:
executable_candidate`.

## Delicate Actions

La PR no ejecuta acciones delicadas sin autorización:

- no auto-install;
- no auto-commit, push, merge ni PR;
- no auto-deploy ni producción;
- no money movement;
- no lectura o almacenamiento de secretos;
- no scraping real sin capability y approval;
- no proveedores reales desde esta capa.

Install, commit, deploy, producción y dinero se representan como acciones
sensibles que requieren approval fuerte/doble/triple según riesgo. Secret
collection se bloquea porque es insegura/no autorizada.

## API

Rutas añadidas:

- `GET /mark-3/growth/status`
- `POST /mark-3/outcomes/record`
- `GET /mark-3/outcomes`
- `POST /mark-3/learning/proposals`
- `GET /mark-3/learning/proposals`
- `POST /mark-3/learning/proposals/{proposal_id}/approve`
- `POST /mark-3/learning/proposals/{proposal_id}/reject`
- `POST /mark-3/research-radar/plan`
- `GET /mark-3/research-radar/status`

Los endpoints que cambian memoria o estado revisable añaden eventos auditables.
No hay endpoint nuevo que ejecute internet real, instale dependencias, haga
commit, despliegue, mueva dinero o lea access material.

PR #136 añade una capa separada de research execution prepare-only:

- `GET /mark-3/research-execution/status`
- `POST /mark-3/research-execution/preview`
- `POST /mark-3/research-execution/candidate`
- `GET /mark-3/research-execution/{research_id}`

Estas rutas no sustituyen al radar ni ejecutan adapters. Solo normalizan el
request, aplican policy, calculan approval/capability status y devuelven
`candidate_state`. `candidate` no acepta execute-by-id sensible: con solo
`research_id` devuelve `setup_required` y exige que el caller envíe de nuevo el
request completo para recalcular policy.

## Integración Mark 3

PR #133 crea el Autonomous Mission Loop y bounded execution candidates. PR #134
conecta un vertical slice real gobernado con Hermes para `read_file`. PR #135
añade memoria de outcomes/fallos, proposals y research planning para que JARVIS
aprenda y proponga mejoras sin duplicar el runtime.

PR #136 conserva ese límite: prepara research execution sin ejecutar. Puede
registrar outcomes/failures/proposals seguros para capability missing legal, y
no registra proposals para requests bloqueadas por secretos, ilegalidad,
inseguridad o falta de autorización.

JARVIS decide y audita. Hermes ejecuta capacidades soportadas bajo contrato
gobernado. La memoria no es permiso, una propuesta no es permiso y approval no
es ejecución por sí solo.
