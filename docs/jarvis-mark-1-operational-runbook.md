# JARVIS Mark 1 Operational Runbook

## Worktree y Codex

Trabaja siempre en un worktree dedicado, nunca directamente en `main`:

```bash
git worktree add -b pr-XX-name ~/jarvis-worktrees/pr-XX-name main
cd ~/jarvis-worktrees/pr-XX-name
codex
```

Abrir Codex desde el worktree correcto evita revisar o modificar otra rama.
Usa macro-PRs grandes, coherentes y validables; no fragmentes Mark 2 o Mark 3 en
120 micro-PRs.

## Validación

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
git diff --check
pytest tests/jarvis/test_post_s_mark_1_hardening_e2e_real_ops_release_candidate.py -q
pytest tests/jarvis -q -x --durations=20
```

API local, cuando aplique:

```bash
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000
```

Revisa los nueve endpoints GET `/mark-1/*`. Ninguno ejecuta acciones reales.

## Interpretación operativa

- Approval es autorización limitada y auditable; no es ejecución.
- Execution candidate es elegibilidad revisable; no demuestra que algo se haya
  ejecutado.
- Strong approval aplica a acciones sensibles.
- Doble confirmación aplica a acciones críticas.
- Monetization Engine produce estimaciones, no revenue confirmado.
- Adaptive SaaS Builder produce planes y candidatos, no repos o deploys reales.
- No ejecutes acciones críticas sin approval válida, audit, permission gates,
  fingerprint cuando aplique y rollback/stop plan.

## Cierre de PR

Después de tests y review, usa `jarvis-finish-pr` para cerrar la PR según el
flujo operativo del proyecto. Un `401` de GitHub CLI significa autenticación
inválida o expirada: no lo evites, no uses credenciales alternativas sin
autorización y no expongas secretos.

Después del merge realizado fuera de esta PR:

```bash
git worktree remove ~/jarvis-worktrees/pr-XX-name
git branch -d pr-XX-name
git worktree list
git status --short
```

## Continuar con Mark 2

No crear Phase T. Iniciar Mark 2 únicamente con la siguiente macro aprobada:
**Mark 2 Macro 1 - Local Daemon, Real Wake Listener & Desktop Runtime**. Mantener
approval gates, audit, permission gates, stop controls y defaults seguros.

PR #126 inicia esta macro sin arrancar daemon ni micrófono. Para validarla usa
`pytest tests/jarvis/test_mark_2_local_daemon_real_wake_desktop_runtime_voice_approval.py -q`.
Una wake phrase no es permission; approval por voz exige el flow explícito,
readback, audit, expiración y confirmaciones acordes al riesgo.

PR #127 / Mark 2 Macro 2 prepara tool execution gobernado. Valídala con
`pytest tests/jarvis/test_mark_2_real_tool_execution_browser_github_filesystem_apis.py -q`.
Preview y candidate no equivalen a ejecución; red, credenciales, browser,
GitHub, APIs, producción y dinero permanecen disabled by default.
