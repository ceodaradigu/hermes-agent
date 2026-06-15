# JARVIS Mark 3 Product/Revenue Factory

PR #138 añade una capa de Product/Revenue Factory gobernada y prepare-only.
JARVIS prepara candidates de producto, monetización, experimentos y decisiones,
pero no ejecuta operaciones externas ni crea otro runtime. Hermes sigue siendo
el motor de ejecución cuando exista capacidad real; JARVIS gobierna, clasifica
riesgo, pide approval, audita y separa evidencia de hipótesis.

## Alcance

La factoría puede preparar:

- oportunidad de producto;
- validación de nicho;
- SaaS/product blueprint;
- oferta o landing candidate;
- pricing candidate;
- unit economics básicos;
- revenue model;
- experiment plan;
- measurement plan;
- kill/continue recommendation;
- approval requirements por riesgo;
- expected evidence;
- stop conditions;
- rollback/stop plan cuando aplique.

No publica, no despliega, no crea checkout, no llama Stripe, no compra
dominios, no envía emails, no usa web/GitHub real, no mueve dinero, no usa
credenciales y no promete ingresos.

## Invariantes

- `no_fake_revenue`
- `no_fake_costs`
- `candidate_is_not_publication`
- `candidate_is_not_payment`
- `candidate_is_not_deploy`
- `approval_is_not_execution`

Todo candidate incluye `risk_level`, `approval_required`,
`required_approval_level`, `scope`, `budget_limit`, `assumptions`,
`evidence_required`, `stop_conditions`, `next_safe_action` y `audit_summary`.

## Revenue y Costes

La salida separa siempre:

- `projected_revenue`
- `confirmed_revenue`
- `gross_revenue`
- `expenses`
- `net_revenue`

Si falta información o evidencia, el valor es `unknown`. Las proyecciones no son
ingresos confirmados. Los costes no se inventan. `net_revenue` solo se calcula
desde `gross_revenue` y `expenses` proporcionados explícitamente, o queda
`unknown`.

## Riesgo y Approval

Stripe live, checkout real, producción, deploy, dominio/DNS, dinero,
publicación real, email real o identidad de David son Nivel 4: strong approval,
readback, doble confirmación y triple confirmación cuando el riesgo sea muy alto.
Esta PR solo marca esos requisitos; no crea approval real ni ejecuta la acción.

Web, GitHub, Stripe, email y deploy externos quedan `setup_required` hasta que
exista una capability gobernada real en otra capa. Falta de capability no es una
denegación permanente. Ilegal, inseguro, no autorizado, credenciales o petición
de revenue/costes falsos sí se bloquea.

## API

- `GET /mark-3/product-revenue/status`
- `POST /mark-3/product-revenue/opportunity`
- `POST /mark-3/product-revenue/blueprint`
- `POST /mark-3/product-revenue/experiment`
- `POST /mark-3/product-revenue/decision`

No existe endpoint Product/Revenue `/execute`, `/pay`, `/deploy`, `/send` ni
`/publish`.
