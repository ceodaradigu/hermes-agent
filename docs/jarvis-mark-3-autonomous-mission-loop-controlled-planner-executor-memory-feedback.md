# JARVIS Mark 3 Autonomous Mission Loop

PR #133 implementa el primer lifecycle central gobernado de misión. Es una
macro-PR coherente y exclusivamente control-plane in-memory.

## Flujo

`received -> classified -> planning -> planned -> preview_ready ->
awaiting_approval|blocked|execution_candidate_ready -> result_pending ->
completed -> post_mortem_ready -> learning_proposal_ready`

También existen `running_internal`, `stopped`, `failed` y `denied`. No todas
las misiones recorren todos los estados. Stop y kill switch impiden nuevos
avances y conservan audit, evidence y resultados previos.

## Límites

- No hay ejecución externa, red, shell, subprocess, filesystem write, AI CLI,
  deploy, email, DNS, Stripe, producción ni movimiento de dinero.
- Candidate no significa ejecución. Approval no significa ejecución.
- Cada step tiene approval, fingerprint, scope, budget, tool y riesgo propios.
- Nivel 5 es denegación permanente.
- Los adapters inyectados existen solo para tests internos y sus resultados se
  etiquetan como simulados, internos y sin efectos externos.
- Working memory, outcomes, feedback, post-mortem y learning proposal no se
  persisten. PR #135 implementará Outcome Memory.
- PR #134 conectará el Governed Execution Engine real.

## Approvals

El loop reutiliza `ApprovalHardeningService`, `ApprovalRecord`,
`evaluate_permission_gate()` y sus context fingerprints. Booleanos del cliente
no satisfacen approvals. Un approval debe estar aprobado, vigente, ser del tipo
normal/strong correcto y coincidir con el contexto exacto de mission ID, step
ID, acción, scope, tool, budget y riesgo.

## Evidence Y Honestidad

Outcomes distinguen `reported`, `observed`, `verified`, `rejected` y `unknown`.
Un claim solo queda `verified` con evidencia compatible marcada como verified.
Costes, revenue y tiempo permanecen `unknown` cuando no existe evidencia.
Audit y evidence redaccionan contenido sensible y guardan referencias seguras,
no secretos completos.

## Roadmap

Después de PR #133: #134 Governed Execution Engine, #135 Continuous Learning +
Outcome Memory, #136 Multi-Agent Orchestration, #137 Product/Revenue Factory,
#138 Local Routine Scheduler + Personal/Family Ops, #139 Moonshot Lab +
Research/Experiment Engine y #140 Mark 3 Release Candidate + Pilot.
