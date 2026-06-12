# JARVIS Mark 2 Macro 2 - Real Tool Execution: Browser, GitHub, Filesystem & APIs

## Qué añade

Mark 2 Macro 1 cerró la base local: daemon, desktop runtime visible, real wake
listener preparado, kill switch, stop phrase y Voice Approval Channel. Macro 2
añade la capa que prepara y gobierna ejecución real de filesystem, GitHub,
browser y APIs externas.

Esta PR no activa ejecución libre. `real_execution_enabled`, red externa,
credenciales, producción, dinero, writes externos, browser real, GitHub real y
APIs reales permanecen `false` por defecto. Restrictions are approval gates,
not permanent bans: una acción legal, segura, autorizada y soportada puede
quedar eligible tras aprobación válida y todas las gates.

## Preview, candidate y gated execution

- **preview** explica qué ocurriría y nunca ejecuta;
- **candidate** prepara target, riesgo, sandbox, allowlist/denylist, approval,
  audit y rollback, pero no ejecuta;
- **gated execution** solo puede quedar elegible si pasan todas las gates. En
  endpoints y tests de esta PR conserva `would_execute=false`;
- **blocked/unsupported** no finge ejecución. Ilegal, inseguro, no autorizado,
  imposible o unsupported es permanent denial.

## Adapters seguros

`FilesystemToolAdapter` normaliza rutas, exige repo/allowlist, bloquea traversal,
`.env`, secretos y paths denegados. Write/patch requieren approval; delete
requiere strong approval y rollback. Sus previews no leen ni escriben archivos.

`GitHubToolAdapter` prepara issues, branches, PRs, comentarios y merges. Declara
red y credenciales requeridas, pero no usa tokens, `gh` ni GitHub real. Merge de
main/protected requiere strong approval y doble confirmación.

`BrowserToolAdapter` prepara open, click, fill, submit y download sin lanzar un
navegador, cookies o sesiones. Login/PII requiere strong approval. Un submit de
pago es critical y requiere doble/triple confirmación.

`ExternalAPIToolAdapter` prepara GET, POST y webhooks, redacta payloads y nunca
llama red. Mutaciones externas requieren approval; credenciales, pagos y
producción elevan strong/doble/triple confirmation.

## Approvals, sandbox y audit

Approval normal aplica a mutaciones acotadas de riesgo normal. Strong approval
aplica a credenciales, datos sensibles y acciones high risk. Producción y
dinero son critical y requieren strong approval más doble confirmación; dinero
puede exigir triple confirmación.

La voz puede satisfacer approval de tool execution únicamente mediante un
Voice Approval Channel válido, explícito, con readback, contexto exacto,
expiración y confirmaciones requeridas. Una wake phrase inicia una request, pero
nunca concede permiso. Scheduler due y memory active tampoco son permiso.

Todo candidate declara sandbox scope, allowlist, denylist y rollback/stop plan.
Kill switch bloquea ejecución y stop phrase cancela el candidate. Audit registra
request/candidate, approval, voice approval, scope, allowlist/denylist y cambios
reales; secretos, tokens, `.env` y payloads sensibles se redactan.

## Ejemplos

- write dentro del repo: candidate con approval y rollback, sin write real;
- read `.env`: blocked;
- GitHub create PR: candidate con red/credenciales requeridas, sin live call;
- GitHub merge main/protected: strong approval + double confirmation;
- browser submit payment form: critical + double/triple, blocked by default;
- external POST webhook: approval + network gate;
- wake phrase + command: crea request, no permission;
- voice confirmation válida: satisface approval, pero no ejecuta si falta otra gate.

## Endpoints control-plane

- `GET /mark-2/tools/status`
- `GET /mark-2/tools/policy`
- `POST /mark-2/tools/preview-request`
- `POST /mark-2/tools/preview-candidate`
- `POST /mark-2/tools/preview-filesystem`
- `POST /mark-2/tools/preview-github`
- `POST /mark-2/tools/preview-browser`
- `POST /mark-2/tools/preview-api`
- `POST /mark-2/tools/preview-execution`
- `GET /mark-2/tools/audit-preview`

No existen rutas de execute-free/any, auto-approve, approve-all, read-env,
use-token, GitHub/browser/API live, deploy, pay, charge, write-anywhere o
delete-anywhere.

## Tests y siguiente macro

Los tests no usan red, credenciales, browser, GitHub, APIs, producción, dinero,
`.env` ni filesystem externo. Ejecución:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
pytest tests/jarvis/test_mark_2_real_tool_execution_browser_github_filesystem_apis.py -q
pytest tests/jarvis -q -x --durations=20
```

Siguiente macro: **Mark 2 Macro 3 — Visual Command Center UI & Human Approval Console**.

PR #128 implementa esa Macro 3 con paneles operacionales, agent/session
monitor, approval console, costes/límites, riesgos, worktree, diff/tests/review
y audit timeline. Los candidates de Macro 2 se muestran, pero no se ejecutan.
La siguiente macro es **Mark 2 Macro 4 — Real Deploy, Stripe, Email, External
Operations & AI CLI Adapters**.
