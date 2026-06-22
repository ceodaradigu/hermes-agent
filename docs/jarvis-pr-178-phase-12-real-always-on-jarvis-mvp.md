# PR #178 - Phase 12 Real Always-On JARVIS MVP

Phase 12 moves JARVIS from readiness surfaces toward a usable local operator:
one JARVIS on David's PC, reachable from `/jarvis` and iPhone Safari/PWA,
with a local runtime, an optional real microphone wake listener, current-session
conversation, the best available voice path, safe browser/app targets, and
explicit approval for risky actions.

Core invariant remains unchanged: JARVIS governs; Hermes executes. The frontend
and iPhone never execute Hermes directly, there is no generic `/execute`, no
raw shell from mobile/UI, wake phrase never approves, and risky actions require
readback plus the exact phrase `confirmo y autorizo`.

## What is real now

- `Phase12RealAlwaysOnJarvisMVP` is a single aggregate runtime layered on top
  of Phase 10 persona/wake logic and Phase 11 provider/controller/iPhone state.
- Local always-on controller lifecycle is stateful: start, stop, wake event
  handling, stop phrase handling, metadata-only audit, no raw audio storage by
  default.
- A real local wake listener command now exists:
  `scripts/jarvis-wake-listener`.
- A real setup helper now exists:
  `scripts/jarvis-wake-setup`.
- The wake listener supports two local backends:
  - `openwakeword`: requires a custom local model path for
    the primary wake phrase `JARVIS`;
  - `vosk`: local STT fallback that listens to short wake snippets and detects
    the shorter `jarvis` phrase without cloud calls or raw-audio storage.
- It fails gracefully when not available:
  `Wake por micrófono no está activo. Falta instalar/configurar X. Ejecuta
  scripts/jarvis-wake-setup status.`
- Guaranteed Phase 12 wake phrase: `JARVIS`.
- `Hola JARVIS` remains as an experimental/best-effort alias (`alias experimental`).
  It may work when Vosk transcribes the phrase favorably, but it is not a
  closure requirement because real testing showed the shorter `JARVIS` trigger
  is more reliable with the current local STT path.
- Vosk wake matching is tolerant to common short transcripts for the primary
  phrase: `jarvis`, `yarvis`, `jervis`, `jarbis`, `servis`. The longer alias
  keeps bounded experimental matching for variants such as `hola jarvis`,
  `hola travis`, `hola traves`/`hola través`, `hola travez`, `hola jarbi` and
  `hola yervis`, but those variants are best-effort and must not block Phase
  12. Random speech still rejects.
- On wake, JARVIS marks conversation active and creates a pending
  visible/spoken greeting. JARVIS says `Estoy aquí, David. Te escucho.` UTRON
  says `UTRON activo. Habla, David, antes de que la humanidad vuelva a
  decepcionarme.` Wake still cannot approve or execute actions.
- `/jarvis` sends a UI presence heartbeat to
  `/mark-3/phase-12/always-on/ui-presence`. If that heartbeat is recent, wake
  does not open another browser window/tab; it updates backend state and the UI
  claims the pending greeting from `/mark-3/phase-12/always-on/claim-greeting`.
  The duplicate-tab guard only controls browser opening; it does not suppress
  backend activation, conversation-active state or greeting creation.
- If no recent `/jarvis` UI presence exists, wake opens the real UI at
  `http://127.0.0.1:5173/jarvis` through the governed Phase 11 local
  controller. A browser-open cooldown prevents repeated wake detections from
  spawning many windows.
- Stop phrases supported: `JARVIS, para`, `para`, `JARVIS, callate`,
  `callate`, `JARVIS, cállate`, `cállate`.
- Wake opens the real UI only when no recent `/jarvis` heartbeat is present.
  Backend `9119` is the API/proxy target, not the dev UI URL.
- Conversation now has a Phase 12 route using Model/API Router v2:
  `/mark-3/phase-12/conversation/turn`.
- The `/jarvis` UI now posts conversation turns to the Phase 12 brain instead
  of the old deterministic endpoint.
- OpenRouter is used only when configured and live calls are explicitly enabled;
  missing provider is reported in Spanish without technical dumps.
- Current-session conversation history is retained in memory. Clearing session
  history is supported. Memory never grants permission or lowers risk.
- Safe browser actions are real: open safe URL and search web in the browser.
- Known local app/folder launcher is real when a safe path/command resolves and
  approval gates are satisfied. Unknown apps return:

```text
No sé dónde está esa aplicación. Dime la ruta una vez y la guardaré como app conocida.
```

- Custom known-app registry persists to profile-safe
  `HERMES_HOME/jarvis/known_apps.json`.
- Piper CLI local TTS adapter exists as an optional local provider. Browser
  `speechSynthesis` remains fallback. GPT-SoVITS sidecar remains optional.
- Voice output is enabled by default. Wake greetings and answers are spoken by
  default when the browser or configured local TTS can speak. David can mute it,
  and that browser preference is persisted locally. If the browser blocks
  `speechSynthesis` until a first tap/click, `/jarvis` shows:

```text
El navegador necesita una primera pulsación para desbloquear la voz. Pulsa aquí una vez y seguiré hablando automáticamente.
```

- Voice preferences are explicit and non-cloning:
  JARVIS = human, warm, elegant, technological; UTRON = deeper, darker,
  authoritative. No copyrighted movie/actor clone.
- Natural Spanish voice variants map to panel, voice, repeat, stop, camera,
  audio recording, status, cancel, UTRON, URL/search/app/folder actions.
- Secure remote bridge status is Tailscale-first, with kill switch, pairing,
  revocation and iPhone approval binding inherited from Phase 11.
- Startup scripts exist:
  - `scripts/jarvis-start`
  - `scripts/jarvis-stop`
  - `scripts/jarvis-doctor`
  - `scripts/jarvis-wake-listener`
  - `scripts/jarvis-wake-setup`
- Startup/doctor standardize ports:
  - backend `127.0.0.1:9119`
  - frontend `127.0.0.1:5173`
  - frontend proxy target `http://127.0.0.1:9119`
- Startup/doctor report the PC URL `http://127.0.0.1:5173/jarvis`, iPhone LAN
  URL `http://<PC-LAN-IP>:5173/mobile`, Tailscale URL
  `http://<tailscale-ip-or-name>:5173/mobile`, wake listener availability,
  wake active/inactive state and raw-audio disabled state.
- Dashboard/read model/event stream expose Phase 12, always-on, conversation,
  actions, voice, secure remote bridge and startup status without secrets.
- `/jarvis` shows compact local/LAN/remote, port, wake and voice provider
  status for desktop and iPhone/PWA users.

## What remains readiness or optional

- A bundled Spanish acoustic wake model for a longer phrase such as
  `Hola JARVIS` is not included. `Hola JARVIS` remains an experimental alias,
  not the Phase 12 guarantee. A future dedicated wake model or improved STT can
  make longer phrases reliable.
- Vosk fallback does not need a phrase-specific wake model, but it does need a
  local Spanish Vosk model path via `JARVIS_VOSK_MODEL_PATH`.
- No hidden microphone daemon is installed automatically.
- `/mark-3/phase-12/always-on/ingest-transcript` is for tests/dev transcript
  injection. It is not a substitute for always-on microphone wake.
- Browser form filling remains preview-first. Submit/buy/pay/publish require
  approval and are not silently executed.
- Login/credentials require manual login or a future secure vault. No plain text
  passwords are stored.
- Remote outside home is safest via Tailscale setup. JARVIS does not expose the
  raw PC port to the public internet by default.
- Persistent cross-device conversation summaries are not auto-written yet.
  Current session state and Phase 11 shared state are real.
- Cloudflare Tunnel/VPS relay remain optional future paths, not defaults.

## Startup

Recommended local start:

```bash
scripts/jarvis-start
```

Doctor:

```bash
scripts/jarvis-doctor
```

Stop:

```bash
scripts/jarvis-stop
```

Wake listener status:

```bash
scripts/jarvis-wake-listener status
```

Dry-run wake phrase matcher:

```bash
scripts/jarvis-wake-listener match "jarvis"
scripts/jarvis-wake-listener match "jervis"
scripts/jarvis-wake-listener match "hola mundo"
scripts/jarvis-wake-listener match "la fama ferrovial"
```

Experimental/best-effort alias checks for longer local STT transcripts:

```bash
scripts/jarvis-wake-listener match "hola jarvis"
scripts/jarvis-wake-listener match "hola travis"
scripts/jarvis-wake-listener match "hola través"
scripts/jarvis-wake-listener match "hola traves"
scripts/jarvis-wake-listener match "hola travez"
scripts/jarvis-wake-listener match "hola yervis"
scripts/jarvis-wake-listener match "ola jervis"
```

Full wake activation smoke without microphone:

```bash
scripts/jarvis-wake-listener simulate "jarvis"
```

`simulate` uses the same matcher and posts the raw simulated transcript to the
same backend wake activation endpoint as the microphone listener. It creates
the same pending greeting, respects UI presence/cooldown for browser opening,
and still cannot approve or execute actions.

Wake setup status:

```bash
scripts/jarvis-wake-setup status
```

Run real microphone wake if local dependencies/model are installed:

```bash
scripts/jarvis-wake-listener run
```

`scripts/jarvis-start` checks the wake listener and starts it only when it is
truly available. Use `scripts/jarvis-start --no-wake-listener` to start only
backend/frontend.

The scripts activate `venv` or `.venv` when present and then run
`python -m jarvis.phase_12_startup`. Process state and logs are written under
the active profile's `HERMES_HOME/runtime/phase12`.

Manual equivalent:

```bash
python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 9119
npm --prefix web run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173/jarvis
```

On LAN/iPhone at home, use the PC LAN IP:

```text
http://<PC-LAN-IP>:5173/mobile
```

## Real Wake Test

Check whether real microphone wake is available:

```bash
scripts/jarvis-wake-listener status
```

If it reports missing dependencies, install/configure them outside the repo:

Recommended for Spanish without a custom wake-word model:

```bash
scripts/jarvis-wake-setup install --backend vosk --yes
scripts/jarvis-wake-setup configure-env \
  --backend vosk \
  --vosk-model-path "$HOME/.hermes/models/vosk/vosk-model-small-es-0.42"
scripts/jarvis-wake-listener run
```

That `configure-env` command writes only non-secret wake settings to the active
profile `.env`:

```text
JARVIS_WAKE_BACKEND=vosk
JARVIS_VOSK_MODEL_PATH=/home/diazd/.hermes/models/vosk/vosk-model-small-es-0.42
```

After that, fresh terminals can use:

```bash
scripts/jarvis-doctor
scripts/jarvis-start
```

Alternative openWakeWord path if David has a compatible custom model:

```bash
scripts/jarvis-wake-setup install --backend openwakeword --yes
export JARVIS_WAKE_BACKEND=openwakeword
export JARVIS_OPENWAKEWORD_MODEL_PATH=/path/to/hola-jarvis.onnx
scripts/jarvis-wake-listener run
```

Optional safe profile `.env` update:

```bash
scripts/jarvis-wake-setup configure-env \
  --backend openwakeword \
  --openwakeword-model-path /path/to/hola-jarvis.onnx
```

No model is bundled or downloaded by this repo. The setup script installs only
Python packages when explicitly called with `--yes`; it never silently downloads
unknown model blobs. The listener does not store raw audio and does not send
audio to cloud providers. Vosk mode transcribes short local wake snippets only;
it does not inject everything into conversation. While running, it prints
metadata for heard snippets: raw transcript text from Vosk, normalized text,
token candidates, matched wake phrase, confidence/reason and whether the wake
event was posted. When a wake is posted it also prints backend status, browser
open reason, `greeting_created`, `greeting_status`, and the safety flags proving
wake did not approve or execute anything.
It never prints or stores raw audio.

## Transcript Ingest Test

This is test/dev injection only. It proves the backend wake-state flow, not real
microphone wake.

Start runtime state:

```bash
curl -X POST http://127.0.0.1:9119/mark-3/phase-12/always-on/start \
  -H 'Content-Type: application/json' \
  -d '{"actor":"David","channel":"desktop"}'
```

Inject a wake transcript event:

```bash
curl -X POST http://127.0.0.1:9119/mark-3/phase-12/always-on/ingest-transcript \
  -H 'Content-Type: application/json' \
  -d '{"text":"JARVIS","confidence":0.99,"source":"manual_test"}'
```

Inject a stop phrase:

```bash
curl -X POST http://127.0.0.1:9119/mark-3/phase-12/always-on/ingest-transcript \
  -H 'Content-Type: application/json' \
  -d '{"text":"JARVIS, cállate","confidence":0.99,"source":"manual_test"}'
```

Expected: no approval is granted, no raw audio is stored, and the audit remains
metadata-only.

## OpenRouter

Environment:

```bash
OPENROUTER_API_KEY=...
JARVIS_OPENROUTER_ENABLED=true
JARVIS_OPENROUTER_LIVE_CALLS_ENABLED=false
JARVIS_API_MONTHLY_BUDGET_EUR=30
JARVIS_API_SPEND_EUR=0
JARVIS_API_APPROVAL_THRESHOLD_EUR=1
```

Default is safe. With key missing or live calls disabled, JARVIS says:

```text
Todavía no tengo OpenRouter activado. Puedo funcionar en modo local/fallback o ayudarte a configurarlo.
```

With key present and `JARVIS_OPENROUTER_LIVE_CALLS_ENABLED=true`, JARVIS can
make a real OpenRouter chat-completions call through the safe adapter. Tests use
mocked HTTP only; no live paid calls run in CI.

Budget: default monthly cap is 30 EUR. Significant spend, high risk or critical
quality requires approval. Overspend is blocked. Cheap/local downgrade is
rejected when quality would noticeably suffer.

## Voice

Voz activa. Puedes hablar con JARVIS. Voice output is ON by default. Normal path: wake
greeting and assistant answers are spoken and written. Browser speech synthesis
is the built-in fallback; Piper or a configured local provider can be preferred
when ready.

Optional Piper:

```bash
JARVIS_VOICE_PROVIDER=piper
JARVIS_PIPER_BINARY=/path/to/piper
JARVIS_PIPER_JARVIS_MODEL_PATH=/path/to/jarvis.onnx
JARVIS_PIPER_UTRON_MODEL_PATH=/path/to/utron.onnx
```

Piper adapter uses argv lists, never shell, never downloads voices and deletes
temporary WAV output after reading it.

Stop and repeat remain supported. Errors are shown honestly:

```text
La voz local no está lista; sigo por texto o voz del navegador.
El navegador necesita una primera pulsación para desbloquear la voz. Pulsa aquí una vez y seguiré hablando automáticamente.
```

## Actions

Safe real actions now include:

- open `/jarvis`;
- open safe `http/https` URL;
- search web in browser;
- open JARVIS project folder when the local launcher can resolve it;
- open known apps/folders when resolved and allowed:
  Chrome/browser, Cursor, VS Code, Terminal/WSL, File Explorer, WhatsApp,
  Spotify.

Safety rules:

- no arbitrary shell;
- no raw command from frontend/mobile;
- no `/execute`;
- every attempt is audited;
- sensitive apps/actions require approval;
- form submit, payment, purchase and publication require approval;
- login/passwords are manual/future vault only.

## iPhone outside home

Preferred MVP path: Tailscale private VPN.

1. Install Tailscale on the PC and iPhone.
2. Sign in to the same tailnet.
3. Start JARVIS on the PC.
4. Open the Tailscale URL in iPhone Safari:

```text
http://<tailscale-ip-or-name>:5173/mobile
```

The iPhone is the same JARVIS control surface, not a second assistant. Pairing,
expiry, revocation and iPhone approval binding are inherited from Phase 11.
Execution stays on the PC. Mobile direct Hermes execution and raw shell remain
false.

Remote status:

```bash
curl http://127.0.0.1:9119/mark-3/phase-12/remote/status
```

Kill switch:

```bash
curl -X POST http://127.0.0.1:9119/mark-3/phase-12/remote/kill-switch \
  -H 'Content-Type: application/json' \
  -d '{"enabled":true,"actor":"David"}'
```

## GitHub repos researched

| Repo | License | Used/adapted/inspired | Safe decision |
| --- | --- | --- | --- |
| https://github.com/dscripka/openWakeWord | Apache-2.0 | Wake word architecture and optional dependency detection | No code copied. Optional for future dedicated wake models; Phase 12 guarantees the shorter `JARVIS` path first. |
| https://github.com/Picovoice/porcupine | Apache-2.0 | Wake-word alternative evaluation | No code copied. Rejected as default because access-key/custom model flow is heavier for this phase. |
| https://github.com/SYSTRAN/faster-whisper | MIT | Offline STT option and readiness notes | No code copied. Existing optional voice stack can detect/use later. |
| https://github.com/ggml-org/whisper.cpp | MIT | Local/offline STT deployment pattern | No code copied. Good future binary-backed STT candidate. |
| https://github.com/alphacep/vosk-api | Apache-2.0 | Offline STT alternative | No code copied. Rejected as default because model/runtime selection needs user setup. |
| https://github.com/rhasspy/piper | MIT | Local TTS CLI provider pattern | No code copied. Implemented independent Piper CLI adapter. Avoided the newer GPL fork as a copied dependency. |
| https://github.com/browser-use/browser-use | MIT | Browser automation risk model inspiration | No code copied. Rejected for default because broad browser automation is too powerful for MVP without stronger preview/approval. |
| https://github.com/OpenInterpreter/open-interpreter | Apache-2.0 | Desktop assistant/controller comparison | No code copied. Rejected because it would duplicate Hermes/runtime and allow broader execution than JARVIS governance permits. |
| https://github.com/tailscale/tailscale | BSD-3-Clause | Secure private remote bridge pattern | No code copied. Adopted as preferred setup/status path. |
| https://github.com/OpenRouterTeam/openrouter-examples | MIT | OpenRouter chat-completions request shape | No code copied. Used as API-pattern confirmation only. |

No GPL or unknown-license code was copied into this repo.

## Endpoints

```text
GET  /mark-3/phase-12/status
GET  /mark-3/phase-12/always-on/status
POST /mark-3/phase-12/always-on/start
POST /mark-3/phase-12/always-on/stop
POST /mark-3/phase-12/always-on/ingest-transcript
POST /mark-3/phase-12/always-on/ui-presence
POST /mark-3/phase-12/always-on/claim-greeting
GET  /mark-3/phase-12/conversation/status
POST /mark-3/phase-12/conversation/turn
POST /mark-3/phase-12/conversation/clear
GET  /mark-3/phase-12/actions/status
POST /mark-3/phase-12/actions/prepare
POST /mark-3/phase-12/actions/dispatch
POST /mark-3/phase-12/actions/register-app
GET  /mark-3/phase-12/voice/status
GET  /mark-3/phase-12/remote/status
POST /mark-3/phase-12/remote/kill-switch
GET  /mark-3/phase-12/startup/status
```

## Validation

Focused:

```bash
PYTHONPATH=. python -m pytest -c /dev/null \
  tests/jarvis/test_pr_178_phase_12_real_always_on_jarvis_mvp.py -q
```

Compatibility:

```bash
PYTHONPATH=. python -m pytest tests/jarvis -q
npm --prefix web run build
git diff --check
```

Latest local run in this hardening pass:

- Wake-focused matcher/setup subset:
  - `PYTHONPATH=. python3 -m pytest tests/jarvis/test_pr_178_phase_12_real_always_on_jarvis_mvp.py -k "wake" -q -n 0`
  - `8 passed, 11 deselected`
- Full Phase 12 targeted file:
  - `PYTHONPATH=. python3 -m pytest tests/jarvis/test_pr_178_phase_12_real_always_on_jarvis_mvp.py -q -n 0`
  - `19 passed`
- Dashboard/event subset:
  - `PYTHONPATH=. python3 -m pytest tests/jarvis/test_jarvis_dashboard_event_stream.py tests/jarvis/test_jarvis_dashboard_status_read_model.py -q -n 0`
  - `43 passed`
- PR170-PR177 compatibility subset:
  - `PYTHONPATH=. python3 -m pytest tests/jarvis/test_pr_170_phase_5_identity_store.py tests/jarvis/test_pr_170_phase_5_local_controller_identity_voice.py tests/jarvis/test_pr_171_phase_6_real_voice_wake_memory_sensor_runtime.py tests/jarvis/test_pr_172_phase_7_governed_actions.py tests/jarvis/test_pr_173_phase_8_governed_remote_external_ops.py tests/jarvis/test_pr_174_phase_9_product_operator.py tests/jarvis/test_pr_175_conversational_ux_send_button.py tests/jarvis/test_pr_176_phase_10_hands_free_runtime_persona_api_router.py tests/jarvis/test_pr_177_phase_11_real_provider_controller_iphone_companion.py -q -n 0`
  - `63 passed`
- Full non-xdist JARVIS suite:
  - `PYTHONPATH=. python3 -m pytest tests/jarvis -q -n 0`
  - `2098 passed`
- `npm --prefix web run build`
  - passed; Vite reported the existing chunk-size warning.
- `git diff --check`
  - passed.

## Security limits

- Wake phrase never approves and never executes.
- Exact approval phrase is `confirmo y autorizo`.
- Voice approval must be active, trusted, gated, readback-bound and audited.
- iPhone approval must bind approval id, action id, scope, channel and device.
- UTRON cannot bypass approvals or hide risk.
- Memory never grants permission, budget or risk downgrade.
- Secrets are redacted from status, event stream, dashboard and tests.
- Raw audio is never stored by default.
