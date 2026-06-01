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

## 5. Estado actual de JARVIS después de PR #76

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

PR actual: Phase C — Hermes Runtime Bridge. Objetivo: contrato prepare-only para payloads Hermes, dry-run bridge, execution result futuro, audit integration y agent registry bridge, sin ejecutar Hermes, conectar MissionControl, llamar ApprovalGateway ni crear runtime activo.

Siguiente recomendado: Command Center Visual Interface o Sandbox Execution, según el orden operativo de `docs/JARVIS_MASTER_BUILD_MAP.md`.

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

Ya completado:

- PR #51 - docs: add JARVIS handoff context and working protocol.
- PR #52 - documentar `docs/integrations/jarvis-local-memory-quickstart-smoke-test.md` como checklist de smoke test manual de JARVIS local memory. PR mergeado y validado con smoke test real manual.
- PR #53 - diseño de conversational runtime natural. PR mergeado.
- PR #54 - natural runtime contracts. PR mergeado.
- PR #55 - future capabilities backlog / moonshot map. PR mergeado.
- PR #56 - Hermes inside JARVIS integration contract. PR mergeado.
- PR #57 - deployment modes local/server/hybrid contract. PR mergeado.
- PR #58 - mobile voice command and approval contract. PR mergeado.
- PR #59 - restriction registry and policy override contract. PR mergeado.
- PR #60 - Code Intelligence / CodeGraph Evaluation Contract. PR mergeado.
- PR #61 - Home / Voice / Sensor Hardware Layer. PR mergeado.
- PR #62 - Personal OS / Environment Intelligence Backlog. PR mergeado.
- PR #63 - Distributed Personal OS Capabilities Backlog. PR mergeado.
- PR #64 - Authorized Security Research / Bug Bounty Mode Contract. PR mergeado.
- PR #65 - Personal Memory / User Model Layer. PR mergeado.
- PR #66 - Core Intelligence and Personal Memory Backlog. PR mergeado.
- PR #67 - Developer / Stark Workshop Layer. PR mergeado.
- PR #68 - Personal Knowledge / RAG Layer. PR mergeado.
- PR #69 - Mission Autonomy / Self-Improvement / Revenue Execution Contract. PR mergeado.
- PR #70 - Mission Envelope v1. PR mergeado.
- PR #71 - Mission Approval Request v1. PR mergeado.
- PR #72 - Mission Audit Log v1. PR mergeado.
- PR #73 - Mission State Store v1. PR mergeado.
- PR #74 - Mission Lifecycle Validator v1. PR mergeado.

Actual:

- PR #75 - Mission Command Builder v1: comando preparado serializable y validable, sin runtime ni ejecución real.

Siguiente recomendado:

- PR #76 - Mission Snapshot Serializer v1 o Mission Dry-Run Evaluator v1.

Después:

- No seguir ampliando backlog general salvo necesidad concreta. Nuevas ideas deben entrar como misiones/spikes, no como arquitectura infinita.

## 11. Cómo iniciar un hilo nuevo

Bloque copiável:

```text
Lee docs/jarvis-handoff-context.md, docs/jarvis-north-star.md, docs/jarvis-architecture.md y docs/integrations/jarvis-local-memory-quickstart.md. Mantén la forma de trabajo por PR/worktree, prompts cerrados, validación con venv bueno, sin autoejecución, sin autoload y con PolicyEngine/sensitive boundary siempre por encima.
```
