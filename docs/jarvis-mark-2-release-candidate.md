# JARVIS Mark 2 Release Candidate

## Qué significa Mark 2 RC

Mark 2 queda cerrado como **Mark 2 Release Candidate** controlado. Puede
preparar y gobernar ejecución real, pero Mark 2 RC no es autonomía libre y no
está listo para producción libre. Restrictions are approval gates, not
permanent bans: una acción legal, segura, autorizada y soportada puede quedar
elegible tras aprobación válida y todas las gates.

Por defecto JARVIS no ejecuta, despliega, cobra, manda emails, modifica DNS,
lanza Codex/Claude/Cowork, usa red externa, usa access material, toca
producción ni mueve dinero.

## Macros consolidadas

- Macro 1: local daemon, desktop runtime, wake listener, Voice Approval Channel,
  kill switch y stop controls. La voz puede aprobar con readback, frase,
  expiración y audit; una wake phrase nunca concede permiso.
- Macro 2: candidates de filesystem, GitHub, browser y API con sandbox,
  allowlist/denylist, approval, audit y rollback.
- Macro 3: Visual Command Center, Human Approval Console, Agent Operations
  Dashboard, Cost Usage Dashboard, worktree/diff/tests/review y no fake costs.
- Macro 4: candidates de deploy, Stripe, email y domain; adapters gobernados
  Codex CLI, Claude Code, Claude Cowork/Desktop y API fallback; Routine
  Execution Bridge sin invocación externa real.

## Capability y readiness matrix

`GET /mark-2/release-candidate/capabilities` lista cada capacidad, riesgo,
approval, setup manual, limitaciones y siguiente paso seguro. Ninguna capacidad
tiene side effects reales habilitados ahora.

`GET /mark-2/release-candidate/readiness` declara Mark 2 listo como RC
controlado, no listo para autonomía libre, y producción como
`pilot_ready_after_manual_setup_and_valid_approvals`.

## Auditorías y smoke

La dangerous route audit confirma que no existen rutas de deploy/Stripe/pago/
email/DNS/AI CLI/cookies/session tokens/read-env libres. La approval path audit
cubre producción, dinero, deploy, Stripe, email, DNS, filesystem, GitHub,
browser, API, AI CLI, scheduler, memoria y setup de proveedor.

El E2E prepare-only smoke crea candidates y confirma que nada despliega, cobra,
envía, modifica DNS, llama red ni invoca AI CLI real. Confirma no fake costs,
audit seguro, red y access material desactivados, wake phrase sin permiso,
Voice Approval Channel disponible y kill switch/stop controls listos.

## Seguridad y setup manual

Producción exige strong approval, doble confirmación y rollback. Dinero exige
strong approval, doble confirmación y puede exigir triple confirmación. Email
send exige approval; bulk/sensitive exige strong approval. DNS/production
publish exige strong approval, doble confirmación y rollback/unpublish.

No usar cookies ni session tokens. No almacenar access material en JARVIS.
Codex CLI, Claude Code, Cowork/Desktop, Stripe, email, deploy, domain y API
fallback requieren manual setup explícito.

## Known limitations y siguiente paso

La ejecución real, red externa y proveedores permanecen desactivados por
defecto. Costes y límites siguen estimados, manuales o unknown si no hay
evidencia. El siguiente paso recomendado es Mark 3 planning o un piloto de
producción Mark 2 limitado, con setup manual y approvals válidos.
