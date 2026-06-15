# JARVIS Mark 3 Local Routine Scheduler + Personal/Family Ops

PR #139 añade una capa Mark 3 de Local Routine Scheduler + Personal/Family Ops
en modo control-plane prepare-only. JARVIS prepara candidates auditables para
rutinas locales, operaciones personales, operaciones familiares autorizadas y
authorized account assistance, pero no crea un scheduler real ni accede a
cuentas reales.

Hermes sigue siendo el motor de ejecución. JARVIS gobierna, clasifica riesgo,
pide approval, audita y solo entregara tareas bounded a Hermes cuando exista
capacidad real, legalidad, seguridad, autorizacion y approval proporcional. Las
restricciones son gates de approval/setup, no prohibiciones permanentes, salvo
Nivel 5.

## Alcance

La capa puede preparar:

- rutinas locales supervisadas;
- tareas repetitivas low-risk;
- daily/weekly routine plans;
- personal ops;
- personal/family ops autorizadas;
- authorized account assistance mediante official recovery;
- inventario seguro sin secretos;
- password manager checklist;
- 2FA checklist;
- recordatorios y candidates sin scheduling real;
- health checks de repo/producto/budget sin ejecucion real;
- next safe action, stop conditions, risk classification, approval requirements,
  audit summary y evidence required.

No ejecuta scheduler real, no crea cron jobs, no registra background workers, no
crea watchers, no envia emails, no lee calendario/Gmail/contactos, no accede a
cuentas reales, no guarda passwords, no pide passwords, no salta 2FA, no usa
cookies/tokens/session material, no lee `.env`, no llama providers reales y no
crea otro runtime.

## Candidate Contract

Todo candidate incluye:

- `candidate_id`
- `routine_type`
- `ops_type`
- `risk_level`
- `approval_required`
- `required_approval_level`
- `scope`
- `budget_limit`
- `schedule_preview`
- `would_schedule`
- `would_execute`
- `would_notify`
- `would_access_external_account`
- `would_store_secret`
- `evidence_required`
- `stop_conditions`
- `next_safe_action`
- `audit_summary`

Las invariantes son:

- `candidate_is_not_execution`
- `approval_is_not_execution`
- `memory_is_not_permission`
- `no_real_scheduler`
- `no_background_worker`
- `no_real_email`
- `no_real_calendar`
- `no_real_account_access`
- `no_password_storage`
- `no_2fa_bypass`
- `no_cookie_or_token_use`
- `no_fake_completion`

## Risk Model

- Low-risk planning/checklists son Nivel 0-1 y no requieren permiso extra.
- Local file/repo health candidate es Nivel 2 si esta scoped y read-only.
- Personal/family ops con private account metadata es Nivel 3.
- Real account recovery action, email sending, calendar/account connection,
  credentials, money o production serian Nivel 4 si existiera capability real.
  En esta PR devuelven `setup_required` o `capability_not_connected_yet`.
- Bypass, hacking, acceso no autorizado, token/cookie/session theft,
  suplantacion, password storage y fake completion son Nivel 5.

## Authorized Account Assistance

JARVIS puede ayudar a David y su familia solo con cuentas propias o autorizadas.
La ayuda queda limitada a:

- official recovery;
- inventario seguro sin secretos;
- checklist de datos necesarios;
- password manager checklist;
- 2FA checklist;
- pasos oficiales preparados;
- consentimiento y scope como candidate.

Se bloquea permanentemente bypass, hacking, robo, cookies, tokens, session
material, suplantacion, password storage, 2FA bypass y recuperacion sin
autorizacion. Si falta autorizacion, provider o scope, el candidate vuelve como
`setup_required`, no como exito fingido.

## API

- `GET /mark-3/routine-ops/status`
- `POST /mark-3/routine-ops/plan`
- `POST /mark-3/routine-ops/personal`
- `POST /mark-3/routine-ops/family`
- `POST /mark-3/routine-ops/account-assistance`
- `POST /mark-3/routine-ops/decision`

No existe endpoint Routine Ops `/execute`, `/run`, `/start-worker`, `/send`,
`/login` ni `/bypass`.

## Garantias

- No real scheduler.
- No cron.
- No background worker.
- No watcher.
- No real email.
- No real calendar.
- No Gmail.
- No contacts.
- No provider real.
- No real account access.
- No password storage.
- No 2FA bypass.
- No cookie or token use.
- No fake completion.
