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

## Routine Scheduler Y Supervised Autonomy

Mark 3 planifica rutinas locales, tareas repetitivas, reports y health checks de
repo, producto, métricas y budget. Deben ser acotadas, auditables, pausables y
cancelables.

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
- **PR #134** — Continuous Learning: outcome/failure/ROI memory, experiments y
  tech radar.
- **PR #135** — Multi-Agent Orchestration: roles, budgets, locks, handoffs y
  conflict resolution.
- **PR #136** — Revenue Product Factory: oportunidad a SaaS, monetización y
  measurement.
- **PR #137** — Local Routine Scheduler: supervised autonomy en el PC de David.
- **PR #138** — Authorized Account and Credential Assistance: recuperación
  oficial, consentimiento y seguridad.
- **PR #139** — Moonshot Lab: hard problems, research, prototypes y evidence.
- **PR #140** — Release Candidate hardening y controlled pilot.

Son macro-PRs grandes y coherentes; no habrá micro-PR explosion.

## Pilot Plan

El primer piloto Mark 3 será una misión local útil, acotada y reversible en el
ordenador actual de David. Antes de ejecutar debe mostrar risk level, approval,
scope, budget, herramientas, plan, stop conditions, rollback y audit.

El piloto excluye producción, dinero, Stripe live, DNS, bulk email,
credenciales, bypass y autonomía sin límites. Captura outcomes, fallos, tiempo,
costes reales y post-mortem. El aprendizaje resultante es una propuesta que
requiere revisión antes de persistirse o activarse.

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
