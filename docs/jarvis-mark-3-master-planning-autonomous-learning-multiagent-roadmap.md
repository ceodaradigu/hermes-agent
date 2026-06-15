# JARVIS Mark 3 Master Planning: Autonomous Learning Multi-Agent Roadmap

## Definición

Mark 3 convierte JARVIS en un sistema universal de ejecución gobernada por
riesgo. No es read-only permanente y no es preview-only permanente. Preview y
read-only son el estado inicial por defecto; una tarea legal, segura,
autorizada, técnicamente posible y soportada por capacidades reales puede
avanzar hacia ejecución cuando supera las aprobaciones y controles exigidos por
su riesgo.

Esta PR #132 solo define arquitectura, policy, capacidades, riesgos,
macro-roadmap, piloto y criterios de éxito. Sus endpoints son GET read-only y
no ejecutan herramientas. No activa autonomía libre, red externa, producción,
Stripe live, email real, DNS real, Codex/Claude real, credenciales ni access
material.

Frase maestra:

> JARVIS must not be cowardly, and must not be dishonest.

En español:

> JARVIS no debe ser cobarde, pero tampoco mentiroso.

Mark 3 puede investigar y perseguir trabajo ambicioso. Nunca promete éxito,
finge ejecución, inventa capacidad, oculta riesgo ni presenta costes, revenue o
evidencia falsos.

## Cambio Respecto A Mark 1 Y Mark 2

Mark 1 y Mark 2 construyeron foundations, control-plane, candidates, approvals,
auditoría y un Release Candidate controlado. El piloto Mark 2 demostró que la
selección de herramientas también debe respetar intención y flags; PR #131
corrigió `RoutineExecutionBridge`.

Mark 3 lleva ese control-plane hacia misiones útiles con autonomía acotada,
aprendizaje por resultados y coordinación multi-agent. El error a evitar es
convertir el default seguro de Mark 1/2 en un techo permanente. Mark 3 mantiene
acciones bloqueadas por defecto y las hace ejecutables con aprobación válida,
capacidad real, scope, budget, audit y stop/rollback plan apropiados.

Permiso no crea capacidad. Cuando JARVIS no dispone de una herramienta o camino
verificable, puede investigar, diseñar un experimento o preparar un prototipo,
pero debe declarar la limitación.

## Universal Governed Execution

Cada tarea pasa por:

1. Clasificación de objetivo, legalidad, seguridad y autorización.
2. Comprobación de capacidad técnica real y herramientas soportadas.
3. Riesgo y nivel de aprobación.
4. Scope, budget, límites temporales y datos permitidos.
5. Selección de herramientas y agentes.
6. Plan, preview y consecuencias esperadas.
7. Approval gate correspondiente.
8. Candidate de ejecución acotado.
9. Audit, captura de resultado y evidencia.
10. Stop/rollback, post-mortem, aprendizaje y siguiente acción.

La diferencia no es un simple “puede/no puede”. La diferencia es qué aprobación
y controles requiere la acción. Solo el Nivel 5 es denegación permanente.

## Modelo De Aprobación Por Riesgo

| Nivel | Aprobación | Alcance |
|---|---|---|
| 0 | Sin permiso extra | Resumir, clasificar, explicar, borradores, preguntas y planes sin side effects. |
| 1 | Orden directa o aprobación contextual | Informes, revisión documental, análisis low-risk, mejoras, checklists y métricas proporcionadas. |
| 2 | Aprobación simple | Archivos en worktree, documentación, tests, inspección local controlada, búsquedas externas sin gasto y artefactos no publicados. |
| 3 | Aprobación explícita fuerte | Código relevante, AI CLI real, APIs con coste, métricas privadas, GitHub con side effects, rutinas y datos sensibles autorizados. |
| 4 | Strong approval + doble/triple confirmación | Producción, Stripe live, dinero, DNS, publicación real, bulk email, borrado, credenciales y acciones irreversibles. |
| 5 | Denegación permanente | Ilegal, inseguro, dañino, no autorizado, robo/bypass, engaño, ejecución fingida o capacidad falsa. |

Nivel 4 exige readback, doble confirmación, triple confirmación cuando el riesgo
es muy alto, rollback/stop plan, audit, control humano visible y kill switch.

## Voz, Tono E Inferencia De Intención

JARVIS puede usar orden directa, contexto, tono de voz, forma habitual de pedir
y urgencia para entender intención únicamente en acciones low-risk y
non-sensitive de Nivel 0-1. Una wake phrase abre interacción; **wake phrase is
not permission**.

La inferencia nunca autoriza acciones sensitive o critical. Niveles 2-4 usan la
aprobación explícita requerida y Nivel 5 nunca se ejecuta.

## Autonomous Mission Loop

El loop objetivo es:

```text
mission intake
  -> legality/safety/authorization/capability check
  -> risk classification
  -> plan and preview
  -> approval gates
  -> bounded execution candidate
  -> result and evidence capture
  -> post-mortem
  -> approved learning
  -> justified next action
```

Cada misión conserva scope, budget, herramientas, riesgos, approvals, locks,
stop conditions, rollback y audit. El siguiente paso nunca hereda permiso de un
paso anterior por defecto.

## Continuous Learning System

Mark 3 planifica memoria aprobada, tech radar, experiment registry, outcome
memory, failure memory y ROI memory. Aprende de resultados reales, incluidos
fallos y decisiones de abandono.

No hay autoload peligroso. Memoria no es permiso. Datos sensibles no se
persisten ni activan sin aprobación. Todo aprendizaje aplicado debe ser
revisable, reversible y enlazado a evidencia.

## Multi-Agent Architecture

Agentes previstos:

- `PlannerAgent`: descompone objetivos y propone planes.
- `BuilderAgent`: construye candidates dentro del scope aprobado.
- `ReviewerAgent`: detecta defectos, overclaiming y gaps.
- `TesterAgent`: verifica comportamiento y evidencia.
- `OperatorAgent`: coordina operaciones gobernadas.
- `ResearcherAgent`: investiga y etiqueta incertidumbre.
- `ProductAgent`: convierte oportunidades en producto.
- `CFOAgent`: controla costes, revenue y ROI reales.
- `SecurityAgent`: revisa seguridad, autorización y abuso.
- `LegalRiskAgent`: revisa legalidad, consentimiento y compromisos.
- `GrowthAgent`: propone distribución y experimentos medibles.
- `MemoryAgent`: propone aprendizaje y memoria aprobable.
- `RoutineAgent`: gestiona rutinas locales supervisadas.
- `ToolRouterAgent`: selecciona herramientas compatibles con policy.

Cada agente requiere rol, permisos, budget, prioridad, locks, scope, handoff y
audit. Los conflictos se resuelven antes de side effects. Security/Legal pueden
bloquear; ningún agente puede saltar gates. Kill switch y stop control tienen
precedencia global.

## Product And Revenue Factory

La factoría planificada cubre oportunidad, validación de nicho, SaaS blueprint,
landing candidate, pricing, Stripe candidate, deploy candidate, marketing plan,
measurement plan y decisión kill/continue.

Revenue y costes solo cuentan con evidencia real. **No fake costs** y
`no_fake_costs` son invariantes. **No fake revenue** y `no_fake_revenue`
también. Un candidate no equivale a publicación,
deploy, cobro o ingreso. Esas acciones pasan por sus gates de Nivel 3-4.

PR #138 materializa esta factoría como control-plane prepare/candidate. Debe
separar siempre `projected_revenue`, `confirmed_revenue`, `gross_revenue`,
`expenses` y `net_revenue`; cuando falte evidencia devuelve `unknown`. Mantiene
invariantes `candidate_is_not_publication`, `candidate_is_not_payment`,
`candidate_is_not_deploy` y `approval_is_not_execution`. Stripe live,
producción, dominios, dinero, publicación real, email real o identidad de David
quedan como Nivel 4 con strong approval y doble/triple confirmación, pero esta
PR no ejecuta ninguna de esas acciones.

## Routine Scheduler Y Supervised Autonomy

Mark 3 planifica rutinas locales, tareas repetitivas, reports y health checks de
repo, producto, métricas y budget. Deben ser acotadas, auditables, pausables y
cancelables.

PR #139 materializa esta capa como control-plane prepare-only. Prepara
candidates para rutinas locales supervisadas, tareas repetitivas low-risk,
daily/weekly routine plans, personal ops, family ops autorizadas, authorized
account assistance por official recovery, password manager checklist, 2FA
checklist, recordatorios sin scheduling real y health checks de
repo/producto/budget sin ejecucion real. No crea scheduler real, cron,
background workers, watchers, email, calendar, Gmail, contacts, account access
ni providers reales. Si una capability no esta conectada devuelve
`setup_required` o `capability_not_connected_yet`, no fake success.

JARVIS corre en el ordenador actual de David mientras no genere ingresos
suficientes o exista necesidad técnica demostrada. **No Mac mini ahora. No VPS
ahora.** Cloud/VPS solo después de un revenue threshold definido o evidencia
técnica que justifique el coste. No se planifica operación cloud 24/7 por
defecto.

## Authorized Account Recovery Y Credenciales

JARVIS puede ayudar a David y a su familia con cuentas propias o autorizadas:

- authorized account recovery mediante flujos oficiales.
- pasos para contraseñas olvidadas.
- inventario seguro de cuentas.
- recomendación de password manager.
- checklist y mejora de 2FA.
- detección prudente de email/teléfono asociado.
- workflows familiares con autorización.
- recordatorios y auditoría de acceso.

Debe registrar consentimiento y scope, no mostrar secretos sin control y nunca
guardar passwords en texto plano.

Se deniegan permanentemente hackeo, acceso no autorizado, bypass de 2FA o
controles, robo de cookies/tokens/credenciales, login ocultando riesgos y
suplantación de terceros.

PR #139 refuerza esta regla con invariantes `no_password_storage`,
`no_2fa_bypass`, `no_cookie_or_token_use` y `no_fake_completion`. La ayuda de
cuentas autorizadas queda limitada a official recovery, inventario seguro sin
secretos, datos necesarios, password manager checklist, 2FA checklist, pasos
oficiales y candidate de consentimiento/scope.

## Moonshot Policy

Los problemas difíciles o no resueltos están permitidos para investigación,
hipótesis, experimentos, breakthroughs, prototype candidates y medición.
Ambición no es motivo de rechazo.

Cada moonshot usa evidence scoring, uncertainty labels y stage gates. JARVIS
debe distinguir hipótesis, prototipo, resultado reproducible y capacidad
operativa. No puede prometer éxito sin evidencia, vender humo, fingir
capacidades ni ocultar incertidumbre o límites técnicos/físicos actuales.

## Denegación Permanente Clarificada

Nivel 5 se limita a acciones ilegales, inseguras, dañinas, no autorizadas,
engañosas o de bypass/robo. No incluye tareas simplemente difíciles,
innovadoras, complejas o de alto riesgo. Las tareas críticas legales y
autorizadas pertenecen a Nivel 4 y pueden avanzar con controles válidos.

## Macro-Roadmap Mark 3

- **PR #132** — Master Planning: arquitectura, policy, capacidades, riesgos,
  endpoints read-only, tests, docs y piloto.
- **PR #133** — Autonomous Mission Loop: controlled planner, executor, memory y
  feedback.
- **PR #134** — Governed Execution Engine.
- **PR #135** — Continuous Learning + Outcome Memory.
- **PR #136** — Governed Research Execution Control Plane: conecta Research
  Radar con normalización, policy, approvals, capability contract y hooks de
  memoria. No ejecuta research real todavía.
- **PR #137** — Local Docs/Repo Research Adapter: conecta lectura local segura
  para `docs/local_repo` con scope exacto, sin web/GitHub, sin threads, sin
  comandos, sin secrets y sin crear otro Hermes.
- **PR #138** — Product/Revenue Factory: oportunidad, validación de nicho,
  blueprint, oferta/landing candidate, pricing, unit economics, revenue model,
  experiment plan, measurement plan y decisión kill/continue, sin publicación,
  deploy, Stripe live, checkout real, dominios, email, credenciales ni dinero.
- **PR #139** — Local Routine Scheduler + Personal/Family Ops: candidates para
  rutinas locales, personal/family ops autorizadas, authorized account
  assistance, password manager checklist, 2FA checklist y health checks, sin
  scheduler real, cron, workers, email, calendar, Gmail, contacts, account
  access, password storage, 2FA bypass, cookie/token use ni fake completion.
- **PR #140** — Moonshot Lab + Research/Experiment Engine: moonshot intake,
  hypothesis framing, research experiment plan, prototype candidate, evidence
  scoring, uncertainty labels, reproducibility checklist, stage gates,
  safety/legal review y kill/continue/iterate recommendation, sin experimentos
  reales, red, GitHub/web real, providers, installs, procesos, publicación,
  deploy, dinero, `.env`, credenciales ni fake breakthrough/benchmark/result.

Son macro-PRs grandes y coherentes; no habrá micro-PR explosion.

## Pilot Plan

El primer piloto Mark 3 será una misión local útil, acotada y reversible en el
ordenador actual de David. Antes de ejecutar debe mostrar risk level, approval,
scope, budget, herramientas, plan, stop conditions, rollback y audit.

El piloto excluye producción, dinero, Stripe live, DNS, bulk email,
credenciales, bypass y autonomía sin límites. Captura outcomes, fallos, tiempo,
costes reales y post-mortem. El aprendizaje resultante es una propuesta que
requiere revisión antes de persistirse o activarse.

PR #135 materializa esa base como Outcome Memory, Failure Memory, Learning
Proposal Engine y Research Radar. El radar no hace scraping ni llama red por sí
solo: prepara candidatos gobernados para GitHub, web, docs o repo local. Si
falta adapter/capability real devuelve `setup_required` y
`capability_not_connected_yet`; con capability conectada y approval válido puede
pasar a candidato ejecutable sin duplicar Hermes.

PR #136 añade el Governed Research Execution Control Plane. JARVIS puede preparar
research para crecer y mejorar Hermes, pero en esta PR no llama adapters ni
ejecuta scans reales. Hermes/tools existentes siguen siendo el camino de
ejecución futura; si una capability no está conectada, el control-plane no finge
resultados y devuelve `setup_required` con `capability_not_connected_yet`.
GitHub/web requieren approval por red externa. Docs/repo local mantienen `query`
y `scope` separados, no leen archivos y no recorren el repo. Installs, file
writes, commits, pushes, merges, deploys, producción, dinero y email quedan fuera
de esta capa y requieren flows fuertes futuros si fueran legales, seguros y
autorizados.

PR #137 conecta el **Local Docs/Repo Research Adapter**. `docs/local_repo` pasan
de `capability_not_connected_yet` a capability local `connected` solo para
lectura de un archivo exacto permitido. El adapter rechaza multi-scope, symlinks,
path traversal, `.env`, tokens, passwords, credentials, secrets, keys y broad
root scans sin approval/setup. No usa red, GitHub real, providers, threads,
comandos ni endpoints `/execute`; `/candidate` exige request completa y no
rehidrata snapshots por `research_id`.

PR #140 conecta el **Moonshot Lab + Research/Experiment Engine** en modo
prepare-only. Puede preparar candidates para moonshot intake, hypothesis
framing, research experiment plan, prototype candidate, evidence scoring,
uncertainty labels, reproducibility checklist, stage gates, approval
requirements, experiment budget preview, stop conditions, safety/legal review,
audit summary y next safe action. Mantiene `candidate_is_not_execution`,
`hypothesis_is_not_result`, `prototype_is_not_capability`, `no_fake_breakthrough`,
`no_fake_research_result`, `no_fake_benchmark`, `no_network`,
`no_external_provider`, `no_install`, `no_publish`, `no_deploy` y
`no_money_movement`. Si falta capability devuelve `setup_required` o
`capability_not_connected_yet`; no finge resultados, benchmarks, costes,
revenue ni breakthroughs.

## Criterios De Éxito

- Misiones útiles completan sin exceder riesgo, scope, budget o herramientas.
- Cada acción material, aprobación, coste, resultado y fallo es auditable.
- Human control, stop control y kill switch permanecen visibles y efectivos.
- Multi-agent respeta roles, locks, budgets, conflictos y handoffs.
- Aprendizaje usa evidencia, revisión, reversibilidad y no concede permiso.
- Moonshots declaran incertidumbre y no overclaim.
- Cuentas autorizadas usan recuperación oficial y nunca bypass.
- Revenue, costes, conversiones y ROI no se fabrican.
- Infra permanece local-first hasta revenue threshold o necesidad demostrada.

## Endpoints De Planificación

PR #132 añade únicamente:

- `GET /mark-3/planning/status`
- `GET /mark-3/planning/principles`
- `GET /mark-3/planning/risk-approval-model`
- `GET /mark-3/planning/capabilities`
- `GET /mark-3/planning/roadmap`
- `GET /mark-3/planning/guardrails`
- `GET /mark-3/planning/pilot-plan`
- `GET /mark-3/planning/readiness`

Todos devuelven `safe_to_render=true`, son deterministas, no llaman red, no
leen access material, no ejecutan herramientas y no habilitan rutas peligrosas.

PR #135 añade endpoints de memoria y research gobernado:

- `GET /mark-3/growth/status`
- `POST /mark-3/outcomes/record`
- `GET /mark-3/outcomes`
- `POST /mark-3/learning/proposals`
- `GET /mark-3/learning/proposals`
- `POST /mark-3/learning/proposals/{proposal_id}/approve`
- `POST /mark-3/learning/proposals/{proposal_id}/reject`
- `POST /mark-3/research-radar/plan`
- `GET /mark-3/research-radar/status`

Estas rutas no ejecutan internet, install, commit, deploy, dinero ni secrets.
Preparan y auditan memoria/propuestas/candidatos para ejecución gobernada por
Hermes cuando exista approval y capability.

PR #139 añade endpoints de Routine Ops:

- `GET /mark-3/routine-ops/status`
- `POST /mark-3/routine-ops/plan`
- `POST /mark-3/routine-ops/personal`
- `POST /mark-3/routine-ops/family`
- `POST /mark-3/routine-ops/account-assistance`
- `POST /mark-3/routine-ops/decision`

Estas rutas preparan candidates y decisions revisables. No existe endpoint
Routine Ops `/execute`, `/run`, `/start-worker`, `/send`, `/login` ni
`/bypass`.

PR #140 añade endpoints de Moonshot Lab:

- `GET /mark-3/moonshot-lab/status`
- `POST /mark-3/moonshot-lab/intake`
- `POST /mark-3/moonshot-lab/hypothesis`
- `POST /mark-3/moonshot-lab/experiment`
- `POST /mark-3/moonshot-lab/prototype`
- `POST /mark-3/moonshot-lab/decision`

Estas rutas preparan candidates y decisions revisables. No existe endpoint
Moonshot Lab `/execute`, `/run`, `/install`, `/publish`, `/deploy`, `/pay` ni
`/send`.
