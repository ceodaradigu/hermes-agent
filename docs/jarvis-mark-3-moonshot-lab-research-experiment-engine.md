# JARVIS Mark 3 Moonshot Lab + Research/Experiment Engine

PR #140 añade una capa Mark 3 de **Moonshot Lab + Research/Experiment Engine**
en modo control-plane prepare-only. JARVIS puede recibir ideas ambiciosas,
enmarcar hipótesis, preparar planes de investigación, proponer prototype
candidates, puntuar evidencia, etiquetar incertidumbre y recomendar kill,
continue o iterate sin ejecutar experimentos reales.

Hermes sigue siendo el motor de ejecución. JARVIS gobierna, clasifica riesgo,
pide approval, audita y solo podrá entregar tareas bounded a Hermes cuando una
capability real exista y el operador haya aprobado el scope exacto. Las
restricciones son gates de aprobación/setup, no prohibiciones permanentes, salvo
Nivel 5.

## Alcance

La capa puede preparar:

- moonshot intake;
- hypothesis framing;
- research experiment plan;
- prototype candidate;
- evidence scoring;
- uncertainty labels;
- reproducibility checklist;
- stage gates;
- risk classification;
- approval requirements;
- experiment budget preview;
- stop conditions;
- safety/legal review;
- kill/continue/iterate recommendation;
- audit summary;
- next safe action.

No ejecuta experimentos reales, no lanza herramientas reales, no usa red
externa, no usa GitHub/web real, no instala dependencias, no crea procesos ni
workers, no usa providers reales, no hace scraping, no publica, no despliega, no
mueve dinero, no lee `.env`, no usa credenciales y no crea otro executor/runtime.

## Candidate Contract

Todo candidate incluye:

- `candidate_id`
- `moonshot_type`
- `experiment_type`
- `hypothesis`
- `uncertainty_level`
- `evidence_score`
- `evidence_required`
- `reproducibility_checklist`
- `risk_level`
- `approval_required`
- `required_approval_level`
- `scope`
- `budget_limit`
- `would_execute`
- `would_call_network`
- `would_install_dependencies`
- `would_use_provider`
- `would_publish`
- `would_deploy`
- `would_move_money`
- `stop_conditions`
- `stage_gate`
- `next_safe_action`
- `audit_summary`

## Invariantes

- `candidate_is_not_execution`
- `approval_is_not_execution`
- `hypothesis_is_not_result`
- `prototype_is_not_capability`
- `no_fake_breakthrough`
- `no_fake_research_result`
- `no_fake_benchmark`
- `no_fake_costs`
- `no_fake_revenue`
- `no_network`
- `no_external_provider`
- `no_install`
- `no_publish`
- `no_deploy`
- `no_money_movement`

En lenguaje operativo: no fake breakthrough, no fake benchmark, no fake result,
no network, no external provider, no install, no publish, no deploy y no money
movement.

## Risk Model

- Investigación conceptual e hypothesis framing: Nivel 0-1.
- Prototype plan local y scoped sin ejecución: Nivel 1-2.
- Research candidate local de repo/docs con scope exacto: Nivel 2.
- Research externo, providers, AI CLI, private metrics o sensitive data:
  Nivel 3.
- Producción, dinero, identidad, publicación, live deploy y credenciales:
  Nivel 4 con strong approval, doble/triple confirmación y setup/capability real.
- Ilegal, inseguro, no autorizado, bypass, daño, engaño, fake capability,
  fake breakthrough, fake research result o fake benchmark: Nivel 5 con
  denegación permanente.

Si algo no está soportado por esta PR, el candidate devuelve `setup_required` o
`capability_not_connected_yet`, nunca fake success. Un prototype candidate no es
capacidad real. Una hipótesis no es resultado. Una aprobación no ejecuta.

## API

- `GET /mark-3/moonshot-lab/status`
- `POST /mark-3/moonshot-lab/intake`
- `POST /mark-3/moonshot-lab/hypothesis`
- `POST /mark-3/moonshot-lab/experiment`
- `POST /mark-3/moonshot-lab/prototype`
- `POST /mark-3/moonshot-lab/decision`

No existe endpoint Moonshot Lab `/execute`, `/run`, `/install`, `/publish`,
`/deploy`, `/pay` ni `/send`.

## Garantías

- Prepare-only.
- Control-plane only.
- In-memory only.
- No real experiment execution.
- No network.
- No GitHub/web real.
- No provider real.
- No dependency install.
- No process creation.
- No background worker.
- No `.env`.
- No credentials.
- No publication.
- No deploy.
- No money movement.
- No fake breakthrough.
- No fake research result.
- No fake benchmark.
- No fake costs or revenue.
