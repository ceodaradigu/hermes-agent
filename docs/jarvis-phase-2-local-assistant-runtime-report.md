# JARVIS Phase 2 Local Assistant Runtime Report

Fecha: 2026-06-19

## Resultado Ejecutivo

Phase 2 queda implementada como macro-fase coherente: JARVIS ya tiene un runtime local gobernado usable para acciones locales seguras, approvals v2, historial persistente, stop/rollback contracts, readiness de voz/wake, browser verification, daemon/tray readiness y UI compacta en `/jarvis`.

No se creó otro Hermes. `repo.file.read_safe` usa el `Mark3HermesRuntimeBridge` existente. El resto de acciones Phase 2 son acciones locales allowlisted, con argv fijo o control-plane read-only.

## Flujo E2E

```text
intent/source
  -> backend /mark-3/execution/preview
  -> action catalog allowlisted
  -> risk/policy recalculation
  -> preview + stop/rollback contract
  -> approval request if needed
  -> approval v2 decision
  -> governed dispatch
  -> audit metadata-only
  -> execution history metadata-only
  -> dashboard/event stream/read model
```

## Implementación Por Bloque

### A - Strong Approval v2

Implementado en `Phase2LocalAssistantRuntimeControlPlane`.

Cobertura real:

- approval levels: `none`, `soft`, `normal`, `strong`, `double`, `triple`, `blocked`, `unsupported`;
- high recalcula a `strong`;
- critical recalcula a `triple`;
- critical queda blocked si no hay canal double/triple real;
- readback para high/critical;
- confirmation phrase para strong;
- approvals expiran;
- approvals single-use;
- actor/source/channel voice/wake bloqueados para approve;
- frontend no decide solo;
- backend recalcula antes de decide/dispatch;
- audit metadata-only.

### B - Hermes Action Bridge Allowlisted

Catálogo Phase 2:

- `local.status.read`
- `local.doctor.run`
- `repo.status.read`
- `repo.tests.run_allowlisted`
- `repo.diff.read`
- `repo.log.read`
- `repo.file.read_safe`
- `jarvis.phase.status`
- `jarvis.audit.status`
- `jarvis.memory.status`
- `jarvis.execution.history.read`
- `jarvis.execution.preview`

Acciones reales:

- status/control-plane reads locales;
- comandos git fijos sin shell;
- pytest allowlisted fijo;
- file read por Hermes bridge existente.

No se implementó shell libre ni command runner genérico.

### C - Execution History

`ExecutionHistoryStore` usa SQLite si hay `JARVIS_LOCAL_STATE_DIR`/`JARVIS_STATE_DIR`, o memoria si no hay state dir. Guarda metadata segura, no outputs sensibles.

Endpoints:

- `GET /mark-3/execution/history`
- `GET /mark-3/execution/history/{execution_id}`

### D - Stop/Rollback Contracts

Todas las acciones declaran:

- stop supported/method;
- rollback supported/plan/risk/approval/status/limitations.

Read-only usa `not_required`. Prepare-only usa `discard_preview`. Stop unsupported devuelve estado honesto.

### E - Voice/Wake Runtime

`GET /mark-3/voice-runtime/status` incluye `phase_2_runtime` con:

- voice runtime diagnostics;
- browser STT/TTS capability contract;
- selected voice metadata;
- TTS interrupt/stop contract;
- low confidence clarification;
- voice intent submitted to preview;
- wake runtime readiness disabled/not_configured;
- privacy status.

No hay wake always-on, no openWakeWord activo, no audio bruto backend.

### F - Browser Verification

`GET /mark-3/browser-verification/status` entrega checklist:

- API reachability;
- voice capability;
- approval panel;
- event stream;
- audit;
- memory;
- execution history;
- no auto getUserMedia;
- no `/execute`;
- no frontend direct Hermes.

No se añadió Playwright.

### G - Local Daemon/Tray Readiness

`GET /mark-3/local-runtime/status` declara:

- daemon readiness;
- tray readiness;
- startup manual;
- local-only binding;
- no auto mic/camera/wake;
- no auto-start;
- state dir/audit/history contract;
- failure modes.

No instala daemon ni tray real.

### H - Pilot Local

Evidencia automatizada inicial:

```text
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_pr_166_phase_2_local_assistant_runtime.py -q -x
.....                                                                    [100%]
5 passed, 5 warnings in 3.02s
```

Validado por esa suite:

- rutas nuevas;
- ausencia de `/execute`;
- action catalog;
- denied actions;
- approval v2 levels;
- high -> strong;
- critical -> blocked;
- expired approval blocked;
- reused approval blocked;
- voice/wake cannot approve;
- credential denial exact phrase;
- allowlisted local dispatch;
- Hermes read file via existing bridge;
- history persistence/reload with `tmp_path`;
- no secret/raw audio/frame flags;
- stop unsupported honest;
- rollback statuses;
- voice low-confidence clarification;
- wake disabled/not_configured;
- daemon/tray readiness;
- browser verification status;
- dashboard/event stream Phase 2;
- frontend static checks.

Manual pendiente:

- abrir `/jarvis` en navegador;
- comprobar render de approval panel/drawers;
- comprobar STT/TTS real del navegador;
- comprobar que no aparece prompt de mic/camera al cargar;
- confirmar event stream desde navegador;
- crear preview safe desde UI.

### I - UI `/jarvis`

Cambios en `JarvisDebugDrawer`:

- `Action Catalog Allowlist`;
- `Execution History`;
- `Phase 2 / Local Runtime`;
- `Browser Verification`;
- voice diagnostics Phase 2;
- stop/rollback rows.

El centro visual principal no se convirtió en JSON.

### J - API/Backend

Endpoints añadidos:

- `GET /mark-3/phase-2/status`
- `GET /mark-3/execution/action-catalog`
- `GET /mark-3/execution/history`
- `GET /mark-3/execution/history/{execution_id}`
- `GET /mark-3/approval/status`
- `GET /mark-3/local-runtime/status`
- `GET /mark-3/browser-verification/status`

Endpoints existentes ampliados:

- `POST /mark-3/execution/preview`
- `POST /mark-3/execution/request-approval`
- `POST /mark-3/execution/approval-decision`
- `POST /mark-3/execution/dispatch`
- `POST /mark-3/execution/stop`
- `GET /mark-3/execution/status`
- `GET /mark-3/voice-runtime/status`
- `GET /mark-3/dashboard/status`
- `GET /mark-3/dashboard/events`
- `GET /mark-3/dashboard/events/stream`

## Seguridad Revisada

Se revisaron explícitamente:

- no `/execute`;
- no direct Hermes frontend path;
- no shell libre;
- no command string arbitrary execution;
- fixed argv only;
- no `.env`;
- no secrets/tokens/passwords/cookies/session material;
- no raw audio backend;
- no camera frames;
- no auto mic;
- no auto camera;
- no auto wake;
- no dinero/Stripe/deploy/email/publicación;
- no APIs externas;
- no dependencias pesadas nuevas;
- no package lock changes requeridos.

## Repos Externas Revisadas

| Repo | Licencia visible | Patrón usado |
|---|---|---|
| `langchain-ai/langgraph` | MIT | durable state/HITL/memory conceptual |
| `OpenInterpreter/open-interpreter` | Apache-2.0 | riesgos de ejecución local |
| `Significant-Gravitas/AutoGPT` | Polyform Shield + MIT parcial | agent loop/safety conceptual |
| `crewAIInc/crewAI` | MIT | orchestration conceptual |
| `microsoft/autogen` | MIT + CC-BY docs | approval/tool execution conceptual |
| `OpenVoiceOS/ovos-core` | Apache-2.0 | intent/skills separation |
| `OpenVoiceOS/ovos-audio` | Apache-2.0 | audio service separation |
| `dscripka/openWakeWord` | Apache-2.0 | wake readiness only |
| `SYSTRAN/faster-whisper` | MIT | STT readiness only |
| `ggml-org/whisper.cpp` | MIT | STT readiness only |
| `OHF-Voice/piper1-gpl` | GPL-3.0 | license awareness only |
| `getzep/graphiti` | Apache-2.0 | memory provenance conceptual |
| `mem0ai/mem0` | Apache-2.0 | memory influence conceptual |
| `sigstore/rekor` | Apache-2.0 | transparency log conceptual |
| `google/trillian` | Apache-2.0 | verifiable log conceptual |
| `Yelp/detect-secrets` | Apache-2.0 | secret classes/redaction conceptual |
| `trufflesecurity/trufflehog` | AGPL-3.0 | credential risks only, no copy |
| `semgrep/semgrep` | LGPL-2.1 | static guardrail ideas only |

Código copiado externo: ninguno.

Adaptado/reimplementado:

- state/checkpoint/history local;
- HITL approval steps;
- metadata-only audit/history;
- secret denial/redaction categories;
- voice/wake readiness contracts;
- memory influence provenance;
- allowlisted local action bridge.

## Qué NO Se Implementó

- double/triple real multi-channel;
- daemon real;
- tray real;
- Playwright automation;
- wake always-on;
- openWakeWord activo;
- faster-whisper/whisper.cpp/Piper instalados;
- Web Audio nuevo;
- audio bruto backend;
- camera frame backend;
- shell libre;
- arbitrary commands;
- package installs;
- deploy;
- Stripe/dinero;
- email;
- publicación;
- operaciones externas productivas.

## Riesgos Pendientes

- Hay que diseñar double/triple real con pasos separados y canal confiable.
- El pilot de navegador sigue manual/estático.
- Daemon/tray readiness debe materializarse en Phase 3.
- `repo.tests.run_allowlisted` está limitado al target PR166.
- Las capacidades de voz dependen del navegador.
- Comandos git fijos son read-only pero todavía ejecutan procesos locales; mantener allowlist estricta.

## Validación Final Codex

Ejecutado:

```text
python -m py_compile $(find jarvis -name '*.py')
```

Resultado: exit code 0.

Ejecutado:

```text
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_pr_166_phase_2_local_assistant_runtime.py -q -x
```

Resultado:

```text
5 passed, 5 warnings in 3.05s
```

Ejecutado:

```text
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20
```

Resultado:

```text
2001 passed, 2001 warnings in 208.88s (0:03:28)
```

Ejecutado:

```text
git diff --check
```

Resultado: exit code 0.

Frontend build:

```text
cd web && npm run build
```

Resultado:

```text
sh: 1: tsc: not found
```

Se intentó el fallback pedido:

```text
npm_config_cache=/tmp/jarvis-npm-cache-pr166 npm ci --fetch-retries=5 --fetch-retry-mintimeout=2000 --fetch-retry-maxtimeout=60000
```

Resultado real:

```text
npm ERR! code EAI_AGAIN
npm ERR! request to https://registry.npmjs.org/zod-validation-error/-/zod-validation-error-4.0.2.tgz failed, reason: getaddrinfo EAI_AGAIN registry.npmjs.org
```

No se modificó `package.json` ni `package-lock.json`.

## Siguiente Macro-Fase Recomendada

Phase 3: Local Runtime Daemon + Trusted Approval Channels.

Objetivos recomendados:

- daemon local real con lifecycle;
- tray real opt-in;
- auth local operator/session;
- double/triple confirmations separadas;
- trusted device model;
- browser verification automatizada si ya existe tooling;
- stop observable para procesos largos allowlisted;
- expansión conservadora del action catalog;
- export seguro de history/audit.
