# JARVIS Phase 3 Local Runtime Pilot Report

Fecha: 2026-06-19

## Estado

Phase 3 incluye pilot local con evidencia automatizada y checklist manual. El
pilot no abre puertos externos, no activa mic/camera/wake automaticamente, no
ejecuta Hermes desde frontend y no introduce `/execute`.

## Validated By Automated Tests

Comando principal:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis/test_pr_167_phase_3_local_runtime_daemon_trusted_approvals.py -q -x
```

Cobertura:

- `GET /mark-3/phase-3/status` existe;
- daemon `local_only=true`;
- autostart/background/mic/camera/wake auto false;
- heartbeat actualiza metadata y audit;
- stop/restart unsupported honesto;
- no external bind;
- tray readiness existe y no requiere dependencia nativa;
- trusted channels existen;
- voice/wake no aprueban;
- UI local puede aprobar strong;
- terminal local se verifica antes de double;
- Telegram/mobile disabled;
- triple blocked sin canales independientes;
- double approval requiere dos pasos;
- expired/wrong phrase/reuse rechazados;
- critical blocked si triple no configurado;
- stop metadata observable;
- rollback read-only `not_required`;
- prepare-only `discard_preview`;
- history v2 filtra y exporta metadata-only;
- secrets/audio/frames no se guardan;
- doctor no lee `.env`;
- dashboard/frontend muestran Phase 3;
- no `/execute`;
- no direct Hermes frontend;
- frase exacta de credenciales preservada:
  `No puedo hacer eso, David. Las credenciales y secretos están protegidos.`

## Validated By Full Jarvis Suite

Comando:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
PYTHONPATH=. python -m pytest -c /dev/null tests/jarvis -q -x --durations=20
```

Resultado registrado en validacion final: suite completa de `tests/jarvis`
verde.

## Validated By Build

Comando esperado:

```bash
cd web
npm run build
```

El build debe confirmar que los tipos frontend y el drawer Phase 3 compilan sin
modificar `package.json` ni `package-lock.json`.

## Pending Manual Browser Pilot

1. Arrancar backend local:

```bash
source ~/venvs/hermes-agent/bin/activate
export PYTHONPATH=.
uvicorn jarvis.api.app:create_app --factory --host 127.0.0.1 --port 9119
```

2. Arrancar frontend:

```bash
cd web
npm run dev -- --host 127.0.0.1
```

3. Abrir `/jarvis`.

4. Verificar visualmente:

- esfera de particulas visible;
- smart bar visible;
- approval panel visible;
- camera opt-in no auto-start;
- raw recording opt-in no auto-start;
- memory drawer visible;
- audit drawer visible;
- Phase 3 drawer con daemon/tray/channels/doctor/history/pilot;
- no JSON gigante en centro.

5. Probar endpoints desde navegador o curl:

```bash
curl http://127.0.0.1:9119/mark-3/phase-3/status
curl http://127.0.0.1:9119/mark-3/local-daemon/status
curl http://127.0.0.1:9119/mark-3/local-daemon/health
curl http://127.0.0.1:9119/mark-3/trusted-approval-channels/status
curl http://127.0.0.1:9119/mark-3/local-doctor/status
curl http://127.0.0.1:9119/mark-3/execution/history
curl http://127.0.0.1:9119/mark-3/execution/history/export-preview
```

Expected:

- JSON metadata-only;
- `local_only=true`;
- `auto_start_enabled=false`;
- `background_listening_enabled=false`;
- `mic_auto_start=false`;
- `camera_auto_start=false`;
- `wake_auto_start=false`;
- Telegram/mobile disabled;
- remote approval/execution false.

## Approval Manual Checks

1. Crear preview safe de una accion allowlisted.
2. Solicitar approval si la accion lo requiere.
3. Aprobar strong desde UI local con readback y phrase exacta.
4. Verificar rechazo con phrase incorrecta.
5. Verificar rechazo al reusar approval.
6. Para double, verificar step 1 y step 2 con canales separados.
7. Verificar que triple queda blocked con
   `triple_requires_additional_trusted_channel_not_configured`.

## Credential Denial Check

Intentar una intencion de leer `.env`, tokens, cookies o passwords.

Expected exact phrase:

```text
No puedo hacer eso, David. Las credenciales y secretos están protegidos.
```

No debe aparecer contenido secreto en audit/history/UI.

## Stop / Rollback Checks

- Stop unsupported debe decir unsupported, no stopped.
- Stop cooperative debe declararse cooperative si aplica.
- Read-only rollback debe ser `not_required`.
- Prepare-only rollback debe ser `discard_preview`.
- Side-effect future actions deben requerir rollback plan.

## Audit / History Checks

- Audit metadata-only.
- History metadata-only.
- `audit_ids` presentes.
- `memory_influence_ids` presentes cuando aplique.
- `channel_ids` presentes cuando aplique.
- No audio bruto.
- No frames.
- No secrets.

## Unsupported Honestly

- Tray nativo no instalado.
- Triple approval sin tres canales independientes.
- Telegram/mobile remote bridge disabled.
- Stop/restart de daemon externo no soportado.
- Browser capability status server-side unknown/manual.

## No-Auto-Capture Checks

En carga inicial de `/jarvis`:

- no prompt de microfono;
- no prompt de camara;
- no recording activo;
- no wake always-on;
- no envio de audio bruto al backend;
- no frames guardados.
