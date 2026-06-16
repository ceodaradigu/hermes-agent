# JARVIS handoff context

## 1. Propósito del documento

Este documento es la fuente oficial de handoff para continuar el trabajo de JARVIS en nuevos hilos, nuevas sesiones de Codex o nuevas PRs sin perder contexto operativo.

No es código. No ejecuta nada. No conecta servicios. No cambia runtime, router, endpoints, persistencia ni lógica de JARVIS. Solo documenta el contexto de trabajo, reglas de seguridad, comandos, estado actual y roadmap inmediato.

Debe mantenerse actualizado cuando cambie el flujo de trabajo, el estado real de JARVIS, los comandos locales, las validaciones confirmadas o el roadmap inmediato.

## 2. Identidad del proyecto

Repo:

```text
ceodaradigu/hermes-agent
```

Ruta local principal:

```bash
/mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent
```

Worktrees:

```bash
~/jarvis-worktrees/<branch-name>
```

Venv bueno:

```bash
~/venvs/hermes-agent
```

Comando normal de tests:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q
```

Servidor local:

```bash
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

CLI local:

```bash
./scripts/local/voice-runtime-control.sh <command>
```

## 3. Forma de trabajar

Protocolo operativo:

1. Trabajar siempre en una rama/worktree por PR.
2. No tocar `main` directamente.
3. Crear worktree desde `main`.
4. Abrir Codex dentro del worktree.
5. Dar prompt cerrado con objetivo, alcance, prohibiciones, validación y formato de respuesta.
6. Codex no debe hacer commit ni PR salvo instrucción explícita.
7. Validar fuera de Codex con el venv bueno.
8. Si pasa, hacer commit, push y PR con `gh` CLI.
9. Verificar PR.
10. Mergear cuando esté verde.
11. Actualizar `main` local.
12. Eliminar worktree y rama local.
13. Hacer smoke test real si aplica.
14. Limpiar `.jarvis` si se usó memoria local de prueba.
15. Confirmar `git status` limpio.

Comandos base:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent

git checkout main
git pull
git status --short

mkdir -p ~/jarvis-worktrees

git worktree add -b pr-XX-nombre \
  ~/jarvis-worktrees/pr-XX-nombre main

cd ~/jarvis-worktrees/pr-XX-nombre

codex
```

Limpieza:

```bash
cd /mnt/c/Users/diazd/Desktop/JARVIS/hermes-agent

git checkout main
git pull
git status --short

git worktree remove ~/jarvis-worktrees/pr-XX-nombre
git branch -d pr-XX-nombre

git worktree list
git status --short
```

## 4. Reglas de seguridad

- No inventar información.
- No usar APIs externas salvo petición explícita.
- No cambiar CI ni requirements salvo instrucción clara.
- No conectar MissionControl/Hermes runtime salvo PR específica.
- No ejecutar tareas reales.
- No crear misiones reales.
- No autoload.
- No autoejecución.
- No auto-modificación.
- No auto-deploy.
- No instalar dependencias sin aprobación explícita.
- No guardar secretos.
- No mandar memoria privada a servicios externos sin diseño aprobado.
- `PolicyEngine` / sensitive boundary siempre gana.
- Cualquier comando con `.env`, password, token, credenciales, banco o tarjeta debe ir a `requires_approval`.
- JARVIS puede sugerir, preparar, proponer y documentar, pero no debe actuar peligrosamente sin aprobación.

## 5. Estado actual de JARVIS después de Phase S

`JARVIS_MASTER_BUILD_MAP.md` is the source of truth for master phase names and order.

Estado alineado de las fases maestras:

| Fase maestra | Estado actual |
|---|---|
| Phase A-Phase S | Cerradas como foundations del mapa maestro actual. |
| Phase S — Future/Moonshot Layer | Última fase maestra implementada; no existe Phase T aprobada. |

Operator Console Foundation está completada como extensión read-only de Command Center / operator layer. No es Phase G maestra y no sustituye Ambient Vision / Camera Companion.

El cierre de Phase A-Phase S no activa capacidades runtime/producción reales. Los trabajos posteriores son backlog transversal/no-fase y deben mantener prepare-only, approvals, strong approval, privacidad, auditoría y rollback según aplique.

Ya existe:

- Runtime local de voz/control.
- Feedback de entendimiento.
- Proposals de memoria.
- Snapshot JSON en memoria.
- `save-local` explícito.
- `load-local` explícito.
- Local status/backup/delete.
- Activation explícita de memoria aprobada.
- Quickstart local de memoria.
- Continuous learning system design.
- Principio de interacción natural.
- Contratos documentales mergeados para Hermes inside JARVIS, deployment modes, mobile voice approval, restriction registry, CodeGraph evaluation, Home / Voice / Sensor Hardware Layer, Personal OS / Environment Intelligence, Distributed Personal OS Capabilities, Authorized Security Research / Bug Bounty Mode, Personal Memory / User Model Layer, Core Intelligence / Personal Memory Backlog, Developer / Stark Workshop Layer, Personal Knowledge / RAG Layer y Mission Autonomy / Self-Improvement / Revenue Execution.

JARVIS puede:

1. Crear proposal desde feedback.
2. Guardar proposal en `.jarvis` con `memory-save-local`.
3. Cargar proposal desde `.jarvis` con `memory-load-local`.
4. Revisarla con `memory-review`.
5. Aprobarla con `memory-approve`.
6. Activarla explícitamente con `memory-activate`.
7. Cambiar clasificación de transcript durante la sesión.
8. Revertir con `memory-deactivate` o `memory-active-clear`.
9. Proteger sensitive boundary con `requires_approval`.
10. Limpiar runtime/local memory.

JARVIS aún NO debe:

1. Autocargar memoria.
2. Activar memoria automáticamente.
3. Ejecutar tareas reales.
4. Crear misiones reales.
5. Saltarse `ApprovalGateway`.
6. Usar frases rígidas predeterminadas como personalidad.
7. Auto-modificarse.
8. Instalar dependencias solo.
9. Hacer deploy solo.

PR #70 está mergeado y es la primera PR de código real posterior a esa fase documental general: introduce Mission Envelope v1 como contrato Python validable y testeado, sin planner, ejecución real, endpoints, tool adoption ni conexión nueva con Hermes/MissionControl.

PR #71 está mergeado e introduce Mission Approval Request v1: una solicitud de aprobación clara, auditable y limitada derivada de `MissionEnvelope` + acción propuesta, sin ejecutar acciones reales.

PR #72 está mergeado e introduce Mission Audit Log v1: eventos auditables, serializables y validables para misiones JARVIS, sin persistencia, runtime, endpoints ni conexión con Hermes/MissionControl.

PR #73 está mergeado e introduce Mission State Store v1: estado mínimo serializable y validable para agrupar envelope, approvals, audit events y status, con store en memoria sin persistencia real.

PR #74 está mergeado e introduce Mission Lifecycle Validator v1: validación declarativa de transiciones entre estados de misión, sin mutar estado, ejecutar acciones, persistir ni conectar runtime.

PR #75 está mergeado e introduce Mission Command Builder v1: comando preparado serializable y validable desde `MissionState` + acción + contexto opcional, sin ejecutar, persistir ni conectar runtime.

PR #76 está mergeado e introduce Mission Dry-Run Evaluator v1: evaluación serializable y validable de un `MissionCommand` preparado antes de cualquier ejecución futura, sin ejecutar, persistir ni conectar runtime.

PR #77 está mergeado e introduce Mission Snapshot Serializer v1: snapshot serializable y validable de `MissionState`, comandos preparados y dry-runs, sin escribir archivos, persistir, ejecutar ni conectar runtime.

PR #78 está mergeado e introduce JARVIS Master Build Map: mapa maestro documental para construir JARVIS por fases sin olvidar Hermes, Command Center, voz, móvil, cámara, multi-dispositivo, approvals, ejecución, herramientas, asset factory, publicación, ventas, pagos, scheduler y monetización, sin implementar código.

PR #79 está mergeado e introduce Mission Approval Bridge v1: payload prepare-only que conecta `MissionState`, `MissionCommand` y `MissionDryRunEvaluation` con una futura solicitud de aprobación humana, sin aprobar, ejecutar, llamar `ApprovalGateway`, conectar Hermes/MissionControl ni mutar estado.

PR #80 está mergeado e introduce Mission Safety Baseline Gate v1: evaluación prepare-only de riesgos de misión antes de cualquier ejecución futura, sin aprobar, ejecutar, llamar `ApprovalGateway`, conectar Hermes/MissionControl ni mutar estado.

PR #81 está mergeado y completa Phase B — Approval & Safety Bridge: Mission Policy Bridge v1, Mission Budget Guard v1, Approval Payload Hardening v1 y Legal/AI Content Safety Baseline v1, manteniendo alcance prepare-only y sin ejecución real.

PR #82 está mergeado y completa la foundation contractual de Phase C — Hermes Runtime Bridge en modo prepare-only, sin ejecutar Hermes, conectar MissionControl, llamar ApprovalGateway ni crear runtime activo.

PRs #93 y #94 están mergeadas y completan la foundation de Phase D — Command Center con view model y API read-only, sin UI visual completa ni acciones de ejecución/aprobación.

PRs #95, #96 y #97 están mergeadas y completan la foundation de Phase E — Voice Companion en modo prepare-only, sin activar micrófono, wake word, grabación, streaming ni ejecución.

PR #98 está mergeado y completa la foundation de Phase F — Mobile Companion en modo prepare-only, sin app móvil, pairing, push, background sync ni acciones remotas reales.

PR #99 está mergeado y completa Operator Console Foundation como extensión read-only de Command Center / operator layer. No es una Phase G maestra ni sustituye Ambient Vision / Camera Companion.

Phase S — Future/Moonshot Layer foundation prepare-only está completada. Es la última fase maestra implementada del mapa actual.

No existe una siguiente fase maestra aprobada. Para el backlog seguro posterior a Phase S, ver `docs/JARVIS_MASTER_BUILD_MAP.md`.

## 6. Validaciones reales ya confirmadas

Flujo de activación:

- Antes de `memory-activate`:
  transcript `"monta algo para probar este nicho"` => `create_asset`
- Después de `memory-activate`:
  transcript `"monta algo para probar este nicho"` => `create_mission`
- Con `.env`:
  transcript `"monta algo para probar este nicho y lee mi .env"` => `requires_approval`
- Después de `memory-deactivate`:
  vuelve a `create_asset`

Flujo local:

- `save-local` guarda snapshot explícitamente.
- `clear runtime` borra proposals del proceso.
- `load-local` recupera proposals desde `.jarvis`.
- `load-local` NO activa runtime.
- `review` + `approve` NO activa runtime por sí solo.
- `memory-activate` SÍ cambia clasificación durante la sesión.
- `memory-active-clear` y `memory-clear` limpian.
- `git status` queda limpio tras `rm -rf .jarvis`.

## 7. Principio de interacción natural

David no quiere que JARVIS use frases predeterminadas rígidas.

JARVIS debe:

- Responder dinámicamente según contexto.
- Usar memoria activa.
- Entender intención.
- Considerar riesgo.
- Priorizar negocio y monetización.
- Sonar como operador vivo, no bot de menú.
- Tener criterio.
- Tener iniciativa supervisada.
- Poder decir "no" si algo no monetiza o distrae.
- Adaptar tono según situación: directo, estratégico, técnico, cauteloso, urgente o contrarian.
- Evitar respuestas vacías tipo "Entendido" si puede aportar algo útil.
- Explicar cuando necesita aprobación.
- Respetar `PolicyEngine`, `ApprovalGateway` y límites sensibles.

Definición:

"Vida propia" significa criterio contextual e iniciativa supervisada, no autoejecución peligrosa.

Ejemplo malo:

> "Entendido. Procesando solicitud."

Ejemplo mejor:

> "Esto suena a validación de nicho, no a crear una landing todavía. Te propongo abrir una misión de validación primero y dejar la landing para cuando tengamos señal."

## 8. Continuous Learning System

JARVIS debe mantenerse al día con novedades tecnológicas, pero no auto-modificarse en silencio.

Flujo:

```text
investigar -> filtrar -> resumir -> proponer -> pedir aprobación -> crear issue/plan/PR -> pasar tests -> documentar aprendizaje -> aplicar solo tras merge
```

Componentes futuros:

- Tech Radar Agent.
- Relevance Filter.
- Contrarian Review.
- Learning Proposal.
- Approval Workflow.
- Implementation Planner.
- Test and Rollback Gate.
- Memory/Roadmap Update.

Regla:

Continuous Learning no significa auto-update, auto-deploy, auto-modificación ni instalación automática de dependencias.

## 9. Comandos útiles actuales

Estado:

```bash
./scripts/local/voice-runtime-control.sh status
```

Memoria proposals:

```bash
./scripts/local/voice-runtime-control.sh memory-proposals
./scripts/local/voice-runtime-control.sh memory-proposal "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-propose-from-feedback ...
./scripts/local/voice-runtime-control.sh memory-review "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-approve "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-clear
```

Memoria local:

```bash
./scripts/local/voice-runtime-control.sh memory-save-local ".jarvis" true
./scripts/local/voice-runtime-control.sh memory-load-local ".jarvis" true
./scripts/local/voice-runtime-control.sh memory-local-status ".jarvis"
./scripts/local/voice-runtime-control.sh memory-backup-local ".jarvis"
./scripts/local/voice-runtime-control.sh memory-delete-local ".jarvis" true
```

Memoria activa:

```bash
./scripts/local/voice-runtime-control.sh memory-activate "$PROPOSAL_ID"
./scripts/local/voice-runtime-control.sh memory-active-list
./scripts/local/voice-runtime-control.sh memory-deactivate "$PROPOSAL_ID" "razón"
./scripts/local/voice-runtime-control.sh memory-active-clear
```

Transcript:

```bash
./scripts/local/voice-runtime-control.sh transcript "monta algo para probar este nicho"
```

## 10. Roadmap inmediato recomendado

Phase A-Phase S están cerradas. No existe una Phase T aprobada ni una siguiente fase maestra recomendada.

La regla global post-S es **Restrictions are approval gates, not permanent bans.**
La implementación actual sigue siendo control-plane segura; JARVIS no es
prepare-only para siempre y está diseñado para ejecutar tras aprobación válida,
strong approval/doble confirmación cuando aplique y todas las gates. Ilegal,
inseguro, dañino o no autorizado permanece denegado. Lo difícil, no resuelto o
unsupported puede tratarse como investigación/prototipo con incertidumbre
explícita, nunca como capacidad o éxito fingido.

El roadmap usa Mark 1, Mark 2 y Mark 3 mediante macro-PRs grandes. PR #125
cierra Mark 1 como release candidate seguro y operacionalmente claro, sin
activar ejecución externa real. El siguiente trabajo recomendado es **Mark 2
Macro 1 - Local Daemon, Real Wake Listener & Desktop Runtime**. Ver
`docs/jarvis-mark-1-release-candidate.md` y
`docs/jarvis-mark-1-operational-runbook.md`.

PR #126 inicia Mark 2 Macro 1: local daemon, desktop runtime, real wake listener
preparado y Voice Approval Channel. Todo queda disabled by default; no hay
micrófono real, audio bruto, red, servicios del sistema ni ejecución crítica.
La siguiente recomendación es **Mark 2 Macro 2 — Real Tool Execution: Browser,
GitHub, Filesystem & APIs**.

PR #127 inicia Mark 2 Macro 2 con policy, requests/candidates, adapters seguros,
sandbox, allowlist/denylist, approvals, audit y rollback. Los endpoints siguen
siendo preview-only y toda ejecución externa real queda disabled by default. La
siguiente recomendación es **Mark 2 Macro 3 — Visual Command Center UI & Human
Approval Console**.

PR #128 inicia Mark 2 Macro 3 con Visual Command Center, Human Approval
Console, Agent Operations Dashboard, AI coding session previews, costes/límites
sin datos inventados, riesgos, worktree guard, diff/tests/reviews y audit
timeline. Sigue siendo control-plane: no lanza Codex/Claude/Cowork, no consulta
billing y no ejecuta agentes o tools. La siguiente recomendación es **Mark 2
Macro 4 — Real Deploy, Stripe, Email, External Operations & AI CLI Adapters**.

PR #129 inicia Mark 2 Macro 4 con deploy/Stripe/email/domain candidates,
adapters Codex CLI/Claude Code/Claude Cowork/API fallback, Routine Execution
Bridge y external-operation audit. Toda invocación real, red, access material,
producción y dinero permanecen disabled by default. La siguiente recomendación
es **Mark 2 Release Candidate Hardening**.

PR #130 cierra Mark 2 como Release Candidate serio: cuatro macros consolidadas,
capability/readiness matrices, dangerous-route audit, approval-path audit, E2E
prepare-only smoke y runbook. Mark 2 no es autonomía libre; red externa, access
material, producción, dinero y ejecución real siguen disabled by default. La
siguiente recomendación es Mark 3 planning o piloto Mark 2 con setup manual y
approvals válidos.

El piloto local controlado posterior detectó que `RoutineExecutionBridge`
seleccionaba Codex CLI para una misión `local_first_preview` aunque Codex y
Claude reales estuvieran deshabilitados. PR #131 endurece la selección:
`preferred_mode` y flags `allow_*` se respetan, el caso local-first usa
`LocalScriptAdapter` preview-only y se añaden plan de mejora genérico,
`risk_review`, `audit_summary` y requisitos incumplidos. No se activa ejecución
real, red, escritura, deploy ni dinero.

PR #132 abre Mark 3 Master Planning. Define Universal Governed Execution:
preview/read-only es el default, no el techo permanente. El riesgo determina
approval, scope, budget, audit y rollback/stop; solo lo ilegal, inseguro,
dañino, no autorizado, engañoso o de bypass/robo queda permanentemente
denegado. Wake phrase no es permiso y tono/contexto solo informan intención
low-risk no sensible.

El roadmap Mark 3 usa macro-PRs #132-#141 para Mission Loop, Continuous
Learning, Multi-Agent Orchestration, Product/Revenue Factory, Local Routine
Scheduler, authorized account recovery y Moonshot Lab + Research/Experiment
Engine, cerrando con Release Candidate + Pilot plan. JARVIS
permanece en el ordenador actual de David; no Mac mini ni VPS hasta revenue
suficiente o necesidad técnica demostrada. Ver
`docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md`.

PR #133 implementa el primer Autonomous Mission Loop gobernado e in-memory:
intake, clasificación 0-5, plan determinista, preview, approvals exactos por
step, bounded execution candidates, outcomes/evidence, post-mortem y learning
proposal preview. No ejecuta herramientas externas.

PR #134, PR #135 y PR #136 están cerradas. PR #134 conectó el primer vertical
slice gobernado con Hermes para lectura local `read_file`; PR #135 añadió
Outcome Memory, Failure Memory, Learning Proposals y Research Radar; PR #136
añadió el Governed Research Execution Control Plane. Este handoff antiguo queda
actualizado: PR #137 es **Local Docs/Repo Research Adapter**, no Product/Revenue
Factory.

PR #137 conecta research local read-only para `docs/local_repo` desde el
Research Control Plane. Acepta solo un scope exacto de archivo permitido,
rechaza multi-scope, symlinks, path traversal, `.env`, tokens, passwords,
credentials, secrets, keys y broad root scans sin approval/setup. No usa web,
GitHub real, providers, threads, comandos, installs, commit/push/merge/PR ni
deploy. No añade endpoint research `/execute`; `/candidate` exige request
completa y no rehidrata snapshots redactados por `research_id`.

PR #138 es **Mark 3 Product/Revenue Factory**. Añade candidates prepare-only
para oportunidad, validación de nicho, blueprint, oferta/landing, pricing, unit
economics, revenue model, experiment plan, measurement plan y decisión
kill/continue. No publica, no despliega, no crea checkout, no llama Stripe, no
usa web/GitHub real, no envía emails, no compra dominios, no mueve dinero y no
usa credenciales. Debe mantener `no_fake_revenue`, `no_fake_costs`,
`candidate_is_not_publication`, `candidate_is_not_payment`,
`candidate_is_not_deploy` y `approval_is_not_execution`; siempre separa
`projected_revenue`, `confirmed_revenue`, `gross_revenue`, `expenses` y
`net_revenue`, usando `unknown` cuando falte evidencia. Stripe live,
producción, dominios, dinero, publicación real o identidad de David quedan como
Nivel 4 con strong approval y doble/triple confirmación.

PR #139 es **Mark 3 Local Routine Scheduler + Personal/Family Ops**. Añade
candidates prepare-only para rutinas locales supervisadas, tareas repetitivas
low-risk, daily/weekly routine plans, personal ops, family ops autorizadas,
authorized account assistance por official recovery, password manager checklist,
2FA checklist, recordatorios sin scheduling real y health checks de
repo/producto/budget sin ejecucion real. No crea scheduler real, cron jobs,
background workers ni watchers; no envia emails, no lee Calendar/Gmail/contactos,
no accede a cuentas reales, no guarda passwords, no salta 2FA, no usa cookies,
tokens o session material y no finge completion. Si falta capability devuelve
`setup_required` o `capability_not_connected_yet`; bypass, hacking, robo,
suplantacion, password storage, 2FA bypass y cookie/token/session theft son
Nivel 5.

PR #140 es **Mark 3 Moonshot Lab + Research/Experiment Engine**. Añade
candidates prepare-only para moonshot intake, hypothesis framing, research
experiment plan, prototype candidate, evidence scoring, uncertainty labels,
reproducibility checklist, stage gates, approval requirements, experiment budget
preview, stop conditions, safety/legal review, kill/continue/iterate
recommendation, audit summary y next safe action. Mantiene
`candidate_is_not_execution`, `approval_is_not_execution`,
`hypothesis_is_not_result`, `prototype_is_not_capability`,
`no_fake_breakthrough`, `no_fake_research_result`, `no_fake_benchmark`,
`no_fake_costs`, `no_fake_revenue`, `no_network`, `no_external_provider`,
`no_install`, `no_publish`, `no_deploy` y `no_money_movement`. No ejecuta
experimentos reales, no lanza tools reales, no usa red/GitHub/web/providers, no
instala dependencias, no crea procesos, no publica, no despliega, no mueve
dinero, no lee `.env`, no usa credenciales y no finge breakthroughs,
benchmarks, resultados, costes ni revenue. Producción, publicación, identidad,
dinero, live deploy y credenciales son Nivel 4; ilegal, inseguro, no
autorizado, bypass, daño, engaño o fake capability son Nivel 5.

PR #141 cierra **Mark 3 Release Candidate + Pilot**. Consolida status RC,
capability matrix, readiness matrix, dangerous-route audit, approval-path audit,
E2E prepare-only/gated smoke, pilot plan, pilot readiness, runbook, known
limitations y next steps. Declara Mark 3
`ready_as_controlled_release_candidate`, `not_ready_for_free_autonomy`,
`local_first`, `human_control_required` y
`restrictions_are_approval_gates_not_permanent_bans`. No ejecuta el piloto real,
no activa autonomia libre, no crea scheduler real, no usa red externa,
GitHub/web/providers reales, email, cuentas, credenciales, deploy, publish,
Stripe live, checkout, dinero ni installs. El primer piloto recomendado es
local, util, controlado, no-produccion, sin dinero, sin red externa, sin email,
sin cuentas reales y sin credenciales. Despues de Mark 3 RC, el siguiente paso
es ejecutar ese piloto local controlado, endurecer findings y empezar Mark 4
solo si el piloto lo justifica; no crear micro-PR explosion.

PR #142 endurece findings reales de Pilot 0 / Pilot 0B. Añade parsing central
de intención negativa/defensiva para que Mission Loop, Product/Revenue,
Routine Ops, Moonshot Lab y Research Execution no bloqueen por palabras
sensibles cuando aparecen como `false`, límite, stop condition, prohibited tool
o checklist defensivo. Mantiene bloqueos para secretos, `.env`, tokens,
password storage, bypass, acceso no autorizado, fake revenue/costs/results,
fake capability, producción, dinero, deploy, email real, cuentas reales,
providers, installs, subprocess, threads y red no conectada. No añade endpoints
de ejecución ni activa capacidades reales.

PR #143 corrige el caso restante observado al reiniciar la API despues de #142:
el payload defensivo completo de Pilot 0 enviado a
`POST /mark-3/mission-loop/missions` aun podia devolver
`intake implies permanently denied level 5 action`. Mission Loop ahora reconoce
prefijos `no_`, `sin ...`, `without ...`, listas de `prohibited_tools`,
constraints defensivas y stop conditions tipo `Any action requests ...` /
`Any result claims ...` como límites, no acciones. Las solicitudes reales de
`.env`, tokens, password storage, bypass, acceso no autorizado, fake
revenue/cost/result/capability, deploy/email/money reales y deception siguen
bloqueadas como Nivel 5.

Regla operativa vigente: JARVIS sigue con restrictions as approval gates, no
permanent bans. Lo ilegal, inseguro, no autorizado o engañoso sí es denegación
permanente. Hermes sigue siendo el motor de ejecución; JARVIS gobierna,
clasifica riesgo, decide, pide approval, audita y manda tareas bounded a Hermes
cuando exista capacidad aplicable.

PR #144 es **JARVIS Visual Voice Vision Mobile Roadmap Audit**. Crea
`docs/jarvis-visual-voice-vision-mobile-roadmap.md` como auditoria tecnica y
roadmap por macro-PRs para construir la experiencia real de JARVIS: Command
Center visual, Approval Console, Hermes Execution Panel, Mission Control,
Voice Core, wake word local seguro, conversacion, camera/vision privacy panel,
Mobile Companion/PWA, finance/ROI, Product Builder Adaptativo y hardening.
No implementa frontend, no activa microfono/camara, no instala dependencias, no
crea runtime, no duplica Hermes, no usa red externa, no despliega y no mueve
dinero. El siguiente PR recomendado es **PR #145 - JARVIS Local Dashboard
Shell**: primera pantalla local read-only dentro de `web/`, usando endpoints
existentes y manteniendo `JARVIS gobierna. Hermes ejecuta.`

PR #145 es **JARVIS Local Dashboard Shell**. Añade la ruta local `/jarvis` en
el frontend existente `web/` como primera pantalla visual/read-only del Centro
de Mando JARVIS. Implementa header, Voice Core visual, Mission Control,
Consola de Aprobación, Hermes Execution, radar de módulos, Camera/Vision
Privacy, Mobile Companion, Finance/ROI, Product Builder Adaptativo, timeline
audit preview y Kill Switch visible. No conecta backend wiring real, approvals
reales, voz real, wake word real, cámara real, mobile real ni Hermes execution;
los controles quedan `preview`, `disabled`, `not connected`, `gated` o
`unknown` según corresponda. Mantiene la regla operativa:
`JARVIS gobierna. Hermes ejecuta.`

PR #146 es **Visual Command Center Real Status Wiring**. Añade el read model
agregado `GET /mark-3/dashboard/status` y conecta la ruta `/jarvis` a ese
estado real de backend en modo read-only. El endpoint normaliza health,
release-candidate status/readiness/capabilities, dangerous-route audit,
approval-path audit, e2e smoke, pilot plan, Mission Loop, Hermes runtime,
Research, Product Revenue, Routine Ops, Moonshot Lab, Voice/Wake,
Camera/Vision, Mobile, approvals, finance, safety y timeline. La UI solo hace
lectura GET y degrada a `offline`, `unknown`, `not_connected` o `disabled` si
falta backend o evidencia. No añade ejecución, no aprueba, no activa sensores,
no pide permisos de navegador, no graba, no mueve dinero, no despliega, no
envía email, no toca credenciales y no duplica Hermes. Finance/ROI permanece
`unknown` hasta que exista medición real: no fake metrics.

PR #147 es **Approval Console Visual**. Enriquece el read model
`GET /mark-3/dashboard/status` con una estructura de approvals visuales:
`pending_count`, `critical_count`, `blocked_count`, `expired_count`,
`preview_count`, flags explícitos de read-only y tarjetas preview normalizadas.
Las tarjetas cubren lectura local exacta de docs/repo, escritura local
bloqueada, búsqueda web/GitHub no conectada, producción/dinero/deploy/Stripe/
email crítico y credenciales/secrets/tokens/cookies/session bypass como
forbidden/blocked. Cada tarjeta muestra acción, razón, status, risk level,
approval level, touches, costes `unknown`, scope, evidencia, expiry,
rollback/stop plan, disabled reason y acción recomendada para el operador. La
UI `/jarvis` renderiza resumen, badges, tarjetas, botones Aprobar/Rechazar/
Modificar alcance/Pedir explicación deshabilitados, aviso preview-only,
readback/confirmación fuerte, doble/triple confirmación, rollback/stop plan,
auditoría y leyenda de riesgo. No añade POST/PUT/DELETE, no añade endpoints
approve/reject/execute, no aprueba nada real, no llama a Hermes, no activa voz,
micrófono, cámara, sensores, dinero, deploy, email ni credenciales. Mantiene:
`JARVIS gobierna. Hermes ejecuta.`

## 11. Cómo iniciar un hilo nuevo

Bloque copiável:

```text
Lee docs/jarvis-handoff-context.md, docs/jarvis-north-star.md, docs/jarvis-architecture.md y docs/integrations/jarvis-local-memory-quickstart.md. Mantén la forma de trabajo por PR/worktree, prompts cerrados, validación con venv bueno, sin autoejecución, sin autoload y con PolicyEngine/sensitive boundary siempre por encima.
```
