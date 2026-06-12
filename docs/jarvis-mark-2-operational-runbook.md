# JARVIS Mark 2 Operational Runbook

## Arranque y verificación local

Trabaja desde el worktree dedicado. Activa `~/venvs/hermes-agent`, exporta
`PYTHONPATH=.`, ejecuta tests y, solo si hace falta, arranca la API local con
`python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000`.

Revisa status, capability matrix, readiness matrix, dangerous route audit,
approval path audit y E2E smoke bajo `/mark-2/release-candidate/`. Revisa
dashboard, approvals, risks, costes, agentes, sesiones, worktree,
diff/tests/review y audit.

## Approvals, voz y parada

Voice Approval Channel puede aprobar solo con readback exacto, frase válida,
expiración, audit y confirmaciones requeridas. Frases válidas según riesgo:
`Sí, continúa`, `JARVIS, entiendo los riesgos, hazlo` y, cuando aplica,
`JARVIS, confirmación final`. Una wake phrase como `Hola Jarvis` o `Jarvis`
nunca es permiso.

Usa stop control o kill switch para parar. No deploy, Stripe, email, DNS,
producción ni dinero sin approval válida, audit y rollback/stop plan.

## Worktrees, Codex y cierre de PR

Crea un worktree para cada macro PR con
`git worktree add ~/jarvis-worktrees/<branch> -b <branch> main`, entra con
`cd ~/jarvis-worktrees/<branch>` y abre Codex allí con `codex`. No trabajes
desde main. Tras tests y review, cierra con `jarvis-finish-pr`.

El aviso known `fatal: 'main' is already used by worktree` no es bloqueo si el
PR state es `MERGED` y el script actualizó main y limpió el worktree terminado.

## Validación

Ejecuta `git diff --check`, py_compile de los módulos RC, los tests específicos
de Mark 2 y `pytest tests/jarvis -q -x --durations=20`.

Existe un hang conocido de TestClient dentro de Codex. Si `test_api.py` o la
suite completa se bloquean, detén la ejecución, documenta el hang sin afirmar
que pasó y valida `tests/jarvis/test_api.py` fuera de Codex.

## Manual setup y límites

Requieren manual setup: login Codex CLI, login Claude Code, Claude
Cowork/Desktop, Stripe provider, email provider, deploy provider, domain
provider y API provider solo si se elige API fallback.

No guardar access material en JARVIS. No usar cookies ni session tokens. La
red externa, ejecución real, producción y dinero permanecen desactivados por
defecto. Mark 2 Release Candidate no es autonomía libre. El siguiente paso es
Mark 3 planning o un piloto Mark 2 limitado con setup manual y approvals
válidos.

## Verificación de Routine Execution Bridge tras el piloto

Para `POST /mark-2/routine-execution/preview`, comprobar siempre que
`preferred_mode` y los flags `allow_*` se reflejan en la respuesta. En
`local_first_preview`, con Codex y Claude reales deshabilitados, la selección
debe ser `LocalScriptAdapter` preview-only, nunca una invocación AI CLI real.

PR #131 añade `selected_adapter_mode`, flags efectivos, requisitos incumplidos,
`improvement_plan_preview`, `risk_review` y `audit_summary`. El endpoint sigue
sin ejecutar, escribir, llamar red, desplegar, mover dinero ni leer access
material.
