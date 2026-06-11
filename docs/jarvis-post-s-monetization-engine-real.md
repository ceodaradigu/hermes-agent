# Post-S Macro 8 - Monetization Engine Real

## Qué consolida esta macro

Esta macro construye la capa real de decisión y control monetario de JARVIS:
planes de pricing, proyecciones de revenue, budget guard, approval de pagos,
readiness de Stripe, acciones monetarias y unit economics/ROI.

Es control-plane seguro. Prepara contratos y elegibilidad para ejecución futura,
pero no mueve dinero real, no cobra, no gasta, no crea checkout, no usa
credenciales, no llama Stripe y no llama APIs externas.

## Por qué no es Phase T

Este trabajo no es Phase T y no crea Phase T. Phase S sigue siendo la última
fase maestra implementada. Post-S Macro 8 pertenece a **Mark 1**, donde JARVIS
consolida capacidades ejecutables bajo aprobación válida sin degradar las gates.

## Semántica de aprobación

**Restrictions are approval gates, not permanent bans.**

- Sin aprobación válida, una acción monetaria queda bloqueada.
- Stripe live, cobros, pagos y gasto real son críticos: requieren strong
  approval y doble confirmación.
- Una acción legal, segura, autorizada y soportada puede quedar
  `eligible_after_approval=true`.
- Eligibility no es ejecución: en esta PR `execution_allowed=false`,
  `would_charge_real_money=false`, `would_spend_real_money=false` y
  `would_call_payment_provider=false`.
- Ilegal, fraudulento, inseguro, no autorizado, imposible o unsupported produce
  permanent denial aunque David lo solicite.
- PR #117 sigue siendo autoridad de approval, expiración, revocación, context
  fingerprint y audit. PR #118 y PR #119 aportan readiness, no pagos.
- Wake phrase, scheduler due y memory active pueden proponer trabajo, pero no
  conceden permiso monetario.

## Pricing y revenue

`PricingPlan` propone planes monthly, yearly, one-time o usage-based. Todo plan
es preview y mantiene `live_billing_enabled=false`.

`RevenueProjection` calcula MRR y ARR estimados solo con inputs explícitos.
Marca unknowns cuando faltan datos, no inventa clientes ni conversiones y
mantiene `is_confirmed_revenue=false`. El revenue estimado no es revenue confirmado
y no se ofrecen garantías de ingresos.

## Budget guard y payment approval

`BudgetGuard` calcula presupuesto restante, detecta límites excedidos y bloquea
costes desconocidos. Sin aprobación válida, `spend_allowed=false`. Superar un
límite o desconocer el coste exige strong approval y doble confirmación.

`PaymentApprovalDecision` reutiliza
`jarvis/approval_execution_semantics.py`. Stripe test puede quedar elegible como
preview sin llamada externa. Stripe live o dinero real requieren strong
approval y doble confirmación, y aun así esta PR solo declara eligibility.

## Stripe readiness

`StripeReadinessPreview` expone un catálogo y checkout de preview. No lee
`.env`, no acepta ni imprime claves, declara la clave como no cargada y
redactada, mantiene live disabled y no llama Stripe. No crea productos,
precios, clientes, checkout ni links reales.

## Unit economics y ROI

La capa calcula estimaciones simples de CAC, LTV, gross margin, payback y ROI a
partir de inputs explícitos. Conserva assumptions y unknowns, marca ROI negativo
o incierto y siempre declara `not_financial_advice=true` y
`not_confirmed_results=true`.

## API control-plane

- `GET /monetization/status`
- `GET /monetization/policy`
- `POST /monetization/preview-pricing`
- `POST /monetization/preview-revenue`
- `POST /monetization/preview-budget`
- `POST /monetization/preview-payment-approval`
- `POST /monetization/preview-stripe-readiness`
- `POST /monetization/preview-action`
- `POST /monetization/preview-unit-economics`

No existen rutas de charge, pay, spend, execute, auto-approve, approve-all ni
creación Stripe live.

## Ejemplos

- Crear pricing preview: proponer Starter por 20 EUR/mes produce un plan con
  live billing deshabilitado.
- Estimar MRR: 10 clientes esperados por 20 EUR produce `estimated_mrr=200`,
  claramente marcado como estimate y no confirmado.
- Evaluar gasto de 20 EUR: calcula remaining budget, pero bloquea gasto real sin
  approval.
- Intentar Stripe live sin aprobación: bloqueado; requiere strong approval y
  doble confirmación.
- Aprobar un pago crítico con strong approval y doble confirmación: puede quedar
  eligible, pero no ejecuta ni llama proveedor en esta PR.

## Siguiente macro

**Post-S Macro 9 — SaaS/Product Builder + Publishing/Deploy Execution**

## Tests

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_post_s_monetization_engine_real.py -q
pytest tests/jarvis -q -x --durations=20
```
