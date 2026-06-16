# JARVIS Visual Voice Vision Mobile Roadmap Audit

PR #144 is a roadmap and architecture audit for the real JARVIS experience:
visual command center, voice, wake word, camera/vision, conversation, mobile,
approval visibility, Hermes execution visibility, finance/ROI and adaptive
product building.

This document does not implement a frontend, start sensors, install
dependencies, create a runtime, deploy, move money, connect credentials or
open a new execution path.

## 1. North Star

This stage turns the existing JARVIS control plane into a buildable roadmap for
the user experience David actually wants: a local-first command center where
JARVIS can be seen, heard, paused, audited and approved without becoming a
second Hermes.

It is:

- a technical audit of current modules, endpoints and gaps;
- a phased roadmap by coherent macro-PRs;
- a safety contract for future UI, voice, wake word, camera/vision and mobile
  work;
- a handoff document that lets David say, "Codex, build phase X".

It is not:

- a frontend implementation;
- a UI mockup PR;
- a wake-word or microphone activation PR;
- a camera activation PR;
- a mobile app PR;
- a real approval execution PR;
- a new Hermes runtime;
- a dependency installation PR.

## 2. Separacion JARVIS / Hermes

Fixed rule:

```text
JARVIS gobierna.
Hermes ejecuta.
```

JARVIS owns:

- user intent and conversation state;
- risk classification;
- `PolicyEngine` and sensitive boundary;
- `ApprovalGateway`, strong approval, readback and expiry;
- mission state, stop conditions and kill switch;
- audit timeline and evidence rules;
- UI state, mobile state, voice/camera state and user-facing explanations;
- finance truth labels: measured, estimated, unknown.

Hermes owns:

- agent loop execution;
- tool calls;
- local task execution when explicitly routed through a governed adapter;
- results returned to JARVIS for audit and evidence.

No duplicate Hermes:

- no frontend directo a Hermes;
- no `frontend -> Hermes` direct path;
- no `mobile -> Hermes` direct path;
- no `voice -> Hermes` direct path;
- no `camera -> Hermes` direct path;
- no browser UI executor that reimplements `AIAgent`;
- no second tool registry or free tool runner in the frontend;
- no approval bypass because a command came from wake word, voice, mobile or a
  trusted device.

The only valid future execution path is:

```text
UI / voice / mobile / camera
  -> JARVIS API / Gateway
  -> intent, policy, approval, scope, budget, audit
  -> governed adapter
  -> Hermes runtime only when allowed and supported
  -> result/evidence back to JARVIS
```

## 3. Estado actual detectado en el repo

### Existing web surface

- Existing frontend lives in `web/`.
- Stack is already present: Vite, React, TypeScript, Tailwind, lucide-react and
  local UI primitives.
- Current `web/src/App.tsx` is a Hermes Agent admin UI with status, sessions,
  analytics, logs, cron, skills, config and keys.
- There is no JARVIS-specific Command Center page yet.
- Future JARVIS UI should extend this app or add a JARVIS section, not create
  another web project or install a new frontend stack.

### Visual Command Center / Command Center

Modules:

- `jarvis/visual_command_center.py`
- `jarvis/command_center.py`
- `jarvis/cost_usage_dashboard.py`
- `jarvis/agent_operations_dashboard.py`
- `jarvis/agent_session_audit.py`
- `jarvis/worktree_execution_guard.py`

Endpoints:

- `GET /command-center`
- `GET /mark-2/dashboard/status`
- `GET /mark-2/dashboard/overview`
- `GET /mark-2/dashboard/panels`
- `GET /mark-2/dashboard/agents`
- `GET /mark-2/dashboard/sessions`
- `GET /mark-2/dashboard/costs`
- `GET /mark-2/dashboard/approvals`
- `GET /mark-2/dashboard/risks`
- `GET /mark-2/dashboard/worktree-guard`
- `GET /mark-2/dashboard/diffs-tests-reviews`
- `GET /mark-2/dashboard/audit`
- `GET /mark-2/dashboard/next-actions`

Detected capability:

- Backend DTOs exist and are safe to render.
- `VisualCommandCenterStatus` exposes `kill_switch_visible`,
  `stop_control_visible`, `voice_approval_visible`, `control_plane_only` and
  `no_fake_costs`.
- `CommandCenterViewModel` includes missions, approvals, audit timeline,
  agents, risk/budget panels, Hermes payload views, devices, multi-device
  status, voice/camera controls and cost/ROI placeholder.

Limit:

- `real_frontend_enabled=false`.
- Command Center is read-only/prepared data; it cannot approve, reject, execute
  or call Hermes.

### Operator Console

Module:

- `jarvis/operator_console.py`

Endpoints:

- `GET /operator/console/status`
- `GET /operator/console/capabilities`
- `GET /operator/console/snapshot`
- `POST /operator/console/preview`

Detected capability:

- Aggregates Command Center, Voice Companion, Mobile Companion, Ambient Vision,
  Multi-device, sandbox, tool adoption, asset factory, payments/revenue, daily
  operator, continuous learning, Personal OS, personalization and moonshot
  placeholders.
- Redacts sensitive operator input.

Limit:

- `frontend_available=false`.
- `websocket_enabled=false`.
- `execution_enabled=false`.
- `approval_actions_enabled=false`.
- `hermes_connected=false`.

### Approval Console and approval semantics

Modules:

- `jarvis/human_approval_console.py`
- `jarvis/approval_hardening.py`
- `jarvis/approval_execution_semantics.py`
- `jarvis/approval_audit.py`
- `jarvis/permission_gates.py`
- `jarvis/policy/approval_gateway.py`
- `jarvis/voice_approval_channel.py`

Endpoints:

- `GET /approvals/status`
- `GET /approvals/policy`
- `GET /approvals/audit-preview`
- `POST /approvals/preview-request`
- `POST /approvals/preview-decision`
- `POST /approvals/preview-gate`
- `GET /approval-execution/status`
- `GET /approval-execution/policy`
- `POST /approval-execution/preview-decision`
- `POST /approval-execution/preview-critical-warning`
- `GET /mark-2/voice-approval/status`
- `POST /mark-2/voice-approval/preview-start`
- `POST /mark-2/voice-approval/preview-confirm`
- `POST /mark-2/voice-approval/preview-flow`

Detected capability:

- Preview models show approval kind, risk, strong approval, double/triple
  confirmation, readback, expiry and rollback/stop plan.
- Voice Approval Channel can model explicit readback and confirmation.

Limit:

- Current visual approval console actions are preview-only.
- There is no general production-ready UI approve/reject action path.
- Approval is not execution.

### Voice runtime

Modules:

- `jarvis/voice/base.py`
- `jarvis/voice/mock_adapter.py`
- `jarvis/voice/gpt_sovits_adapter.py`
- `jarvis/voice/factory.py`
- `jarvis/voice/runtime.py`
- `jarvis/voice/intent_router.py`
- `jarvis/voice/companion.py`
- `jarvis/voice/storage.py`
- `jarvis/voice/understanding_feedback.py`
- `jarvis/voice/understanding_memory.py`
- `jarvis/voice/understanding_memory_local_store.py`

Endpoints:

- `POST /voice/tts`
- `GET /voice/status`
- `GET /voice/companion/status`
- `GET /voice/companion/control-policy`
- `POST /voice/companion/preview`
- `GET /voice/runtime/status`
- `POST /voice/runtime/start`
- `POST /voice/runtime/stop`
- `POST /voice/runtime/mode`
- `POST /voice/runtime/control`
- `POST /voice/runtime/transcript`
- `GET/POST/DELETE /voice/runtime/feedback*`
- `GET/POST/DELETE /voice/runtime/memory/*`

Detected capability:

- TTS adapter contract exists.
- Mock TTS is default.
- GPT-SoVITS adapter can be configured as sidecar.
- Optional local audio output storage exists only when `save_audio=true`.
- Runtime modes exist: `off`, `wake_word`, `listening`, `processing`,
  `speaking`, `error`.
- Text transcript routing and explicit user-understanding feedback/memory flows
  exist.

Limit:

- No real microphone.
- No real wake engine.
- No STT adapter connected.
- No audio playback adapter.
- No background voice process or tray indicator.
- No raw audio storage by default.

### Wake listener

Modules:

- `jarvis/wake_voice_runtime.py`
- `jarvis/real_wake_listener.py`
- `jarvis/voice_session_control.py`

Endpoints:

- `GET /voice-runtime/status`
- `GET /voice-runtime/policy`
- `POST /voice-runtime/preview-wake-parse`
- `POST /voice-runtime/preview-session`
- `POST /voice-runtime/preview-command`
- `POST /voice-runtime/preview-stop`
- `GET /mark-2/wake-listener/status`
- `POST /mark-2/wake-listener/preview-transcript`

Detected capability:

- Supported wake phrases are `Hola Jarvis` and `Jarvis`.
- Wake phrase must appear at the start of transcript.
- Low confidence blocks command processing.
- Stop phrases include `no escuches`, `para`, `callate`, `stop`, `detente`.

Limit:

- Wake listener is disabled by default.
- It parses text only.
- It never opens microphone, records, streams, sends audio or grants approval.

### Camera control and Ambient Vision

Modules:

- `jarvis/camera_control_runtime.py`
- `jarvis/ambient_vision/companion.py`

Endpoints:

- `GET /camera-control/status`
- `GET /camera-control/policy`
- `POST /camera-control/preview-session`
- `POST /camera-control/preview-stop`
- `GET /ambient-vision/status`
- `GET /ambient-vision/privacy-policy`
- `POST /ambient-vision/session-preview`
- `GET /ambient-vision/stop-control`

Detected capability:

- Camera status and privacy policy contracts exist.
- `no mires` is the hard-stop phrase.
- The model requires explicit opt-in and visible indicator.
- Recording, streaming, external vision, face/person analysis, retention and
  execution are disabled by default.

Limit:

- No real camera preview.
- No browser `getUserMedia` wiring.
- No local vision adapter.
- No image/video storage, and none should exist without explicit permission.

### Mobile Companion and Multi-device

Modules:

- `jarvis/mobile/companion.py`
- `jarvis/multidevice/runtime.py`

Endpoints:

- `GET /mobile/companion/status`
- `GET /mobile/companion/permissions`
- `GET /mobile/command-center`
- `POST /mobile/intent/preview`
- `GET /devices/runtime/status`
- `GET /devices/registry`
- `GET /devices/capabilities`
- `POST /devices/pairing/preview`
- `POST /devices/revoke/preview`
- `POST /devices/approval-channel/preview`
- `POST /devices/sync/preview`
- `POST /devices/notifications/preview`

Detected capability:

- Mobile-safe status and Command Center projection exist.
- Intent preview reuses Voice Companion intent categories.
- Device pairing/revoke/approval-channel/sync/notification previews exist.

Limit:

- No app, PWA, auth, pairing, trusted device, push, background sync or mobile
  approval action.
- `can_approve=false`, `can_reject=false`, `can_execute=false`.
- Mobile must not call Hermes directly.

### Hermes runtime

Modules:

- `jarvis/runtime/hermes_adapter.py`
- `jarvis/mark_3_hermes_runtime_bridge.py`
- `run_agent.py`

Endpoints:

- `GET /mark-3/hermes-runtime/status`
- `POST /mark-3/hermes-runtime/execute-read`
- `GET /mark-3/hermes-runtime/sessions/{session_id}`
- `POST /mark-3/hermes-runtime/sessions/{session_id}/stop`

Detected capability:

- `HermesRuntimeAdapter` is a thin wrapper over `AIAgent`.
- `Mark3HermesRuntimeBridge` supports one governed real slice:
  `read_file` / `filesystem_read` / `hermes.file.read` / local backend.
- It requires mission candidate, approval, scope fingerprint and operator
  authorization.
- It tracks sessions, status, interruption and audited outcome.

Limit:

- General execution is disabled.
- Network, write, terminal, browser and money are disabled.
- This is not a general frontend execution API.

### Mark 3 Mission Loop

Module:

- `jarvis/mark_3_mission_loop.py`

Endpoints:

- `GET /mark-3/mission-loop/status`
- `GET /mark-3/mission-loop/policy`
- `POST /mark-3/mission-loop/missions`
- `GET /mark-3/mission-loop/missions/{mission_id}`
- `POST /mark-3/mission-loop/missions/{mission_id}/advance`
- `POST /mark-3/mission-loop/missions/{mission_id}/record-outcome`
- `POST /mark-3/mission-loop/missions/{mission_id}/feedback`
- `POST /mark-3/mission-loop/missions/{mission_id}/stop`
- `GET /mark-3/mission-loop/missions/{mission_id}/audit`

Detected capability:

- In-memory governed mission loop exists.
- It classifies risk, plans, previews, prepares candidates, records outcomes,
  builds post-mortem and learning proposal preview.
- It has an internal kill switch and mission stop.
- PR #143 hardened negative/defensive intent parsing for `robar`-inside-safe
  words and similar defensive payloads.

Limit:

- It is not free autonomy.
- It has no persistent mission DB.
- Global kill switch is internal; UI will need a governed endpoint in a future
  PR if David needs a real button.

### Product Revenue, Finance and ROI

Modules:

- `jarvis/mark_3_product_revenue_factory.py`
- `jarvis/monetization_engine.py`
- `jarvis/payments_revenue/foundation.py`
- `jarvis/revenue_modeling.py`
- `jarvis/pricing_strategy.py`
- `jarvis/cost_usage_dashboard.py`

Endpoints:

- `GET /mark-3/product-revenue/status`
- `POST /mark-3/product-revenue/opportunity`
- `POST /mark-3/product-revenue/blueprint`
- `POST /mark-3/product-revenue/experiment`
- `POST /mark-3/product-revenue/decision`
- `GET /monetization/status`
- `GET /monetization/policy`
- `POST /monetization/preview-*`
- `GET /payments-revenue/status`
- `GET /payments-revenue/policy`
- `POST /payments-revenue/*`
- `GET /mark-2/dashboard/costs`

Detected capability:

- Product/Revenue Factory separates `projected_revenue`,
  `confirmed_revenue`, `gross_revenue`, `expenses` and `net_revenue`.
- Cost dashboard refuses fake actual cost and exposes unknown/manual input
  where no source exists.
- Payments/revenue layer is prepare-only and blocks checkout, provider
  connection, payment processing, bank/card handling and money movement.

Limit:

- No billing integration.
- No real Stripe/checkout/payment.
- ROI is placeholder/unknown unless evidence is provided.

### Product Builder Adaptativo

Modules:

- `jarvis/adaptive_saas_builder.py`
- `jarvis/product_validation_engine.py`
- `jarvis/product_blueprint.py`
- `jarvis/saas_execution_candidates.py`
- `jarvis/asset_factory/foundation.py`
- `jarvis/deploy_publishing/foundation.py`
- `jarvis/marketing_distribution/foundation.py`

Endpoints:

- `GET /product-builder/status`
- `GET /product-builder/policy`
- `POST /product-builder/preview-intake`
- `POST /product-builder/preview-validation`
- `POST /product-builder/preview-differentiation`
- `POST /product-builder/preview-capability-blocks`
- `POST /product-builder/preview-blueprint`
- `POST /product-builder/preview-stack`
- `POST /product-builder/preview-scaffold`
- `POST /product-builder/preview-landing`
- `POST /product-builder/preview-publishing`
- `POST /product-builder/preview-deploy`
- `POST /product-builder/preview-execution-candidate`
- `POST /product-builder/preview-launch-readiness`
- `POST /product-builder/preview-action`
- `GET/POST /asset-factory/*`
- `GET/POST /deploy-publishing/*`
- `GET/POST /marketing-distribution/*`

Detected capability:

- Idea, validation, differentiation, blueprint, stack, scaffold, landing,
  publishing, deploy and execution-candidate previews exist.
- It explicitly disables repo creation, filesystem write, publish, deploy and
  external platform calls.

Limit:

- It does not write product code.
- It does not publish, deploy, create checkout or monetize for real.

### Routine Ops, Moonshot and Research

Modules:

- `jarvis/mark_3_local_routine_scheduler_personal_family_ops.py`
- `jarvis/mark_3_moonshot_lab_research_experiment_engine.py`
- `jarvis/mark_3_research_execution.py`
- `jarvis/mark_3_local_research_adapter.py`
- `jarvis/mark_3_growth_radar.py`

Endpoints:

- `GET/POST /mark-3/routine-ops/*`
- `GET/POST /mark-3/moonshot-lab/*`
- `GET /mark-3/research-execution/status`
- `POST /mark-3/research-execution/preview`
- `POST /mark-3/research-execution/candidate`
- `GET /mark-3/research-execution/{research_id}`
- `POST /mark-3/research-radar/plan`
- `GET /mark-3/research-radar/status`

Detected capability:

- Routine Ops, Moonshot and Research are governed control-plane surfaces.
- Research local docs/repo adapter supports exact-scope local reads for
  allowed docs/repo paths.

Limit:

- No real scheduler, cron, background worker, web/GitHub/provider calls,
  subprocess, install, deploy, money or fake result.

## 4. Gaps detectados

The important missing work is experience and wiring, not a new runtime.

- No real JARVIS Command Center page in `web/`.
- No JARVIS UI information architecture that covers command center, approvals,
  Hermes execution, mission control, voice core, camera/vision, mobile,
  finance/ROI, product builder, memory/learning and kill switch together.
- No frontend API client typed for JARVIS endpoints.
- No UI state machine mapping API payloads to visible states like sleeping,
  listening wake word, thinking, speaking, approval required, Hermes executing,
  paused, blocked and kill switch.
- No visual Approval Console that can show exact action, risk, scope, readback,
  expiry, challenge, missing gates and why approval is not execution.
- No production-grade approve/reject action endpoint for the visual console.
  Existing routes are preview-oriented.
- No Hermes Execution Panel that displays supported Hermes capability,
  session status, tool calls, stop state, candidate, scope fingerprint and
  evidence without exposing content/secrets.
- No conversation panel that turns chat into mission proposal, risk, permissions
  and next step without auto-execution.
- No mission-control UI workflow for creating, advancing, stopping and auditing
  Mark 3 missions.
- No real wake word engine, microphone capture, STT, playback, tray indicator
  or short listening window.
- No live Voice Core visual linked to runtime state or Web Audio analyser.
- No camera preview panel, `getUserMedia` permission handling, local vision
  adapter or privacy overlay.
- No mobile/PWA surface with status, pending approvals, mic/camera state,
  alerts and kill switch.
- No trusted-device pairing/auth/revocation for mobile.
- No push notification or background sync.
- No real cost/revenue data source beyond explicit user input or provided
  evidence.
- No real ROI calculator connected to measured execution cost and confirmed
  revenue.
- No global UI kill-switch endpoint. Mission stop and Hermes session stop exist,
  but a visible global kill switch needs a governed backend path.
- No event stream/WebSocket/SSE for live operations. Polling can work for early
  PRs.
- No frontend tests for JARVIS pages.

## 5. Roadmap por fases y PRs

This roadmap uses macro-PRs, not 50 tiny PRs. Numbers are suggested after this
PR; David can renumber if needed.

### PR #144 - Roadmap/documentation audit

Objective:

- Document the technical roadmap for visual, voice, wake, camera/vision and
  mobile JARVIS without implementing frontend or runtime.

Scope:

- New roadmap document.
- Handoff and master map links.
- Simple docs test.

Probable files:

- `docs/jarvis-visual-voice-vision-mobile-roadmap.md`
- `docs/jarvis-handoff-context.md`
- `docs/JARVIS_MASTER_BUILD_MAP.md`
- `tests/jarvis/test_jarvis_visual_voice_vision_mobile_roadmap.py`

Endpoints consumed:

- None.

New endpoints needed:

- None.

Expected tests:

- Docs content test.
- Existing JARVIS test suite.

Must not do:

- No frontend, runtime, sensors, dependencies, commit, push, deploy or money.

Exit criteria:

- Roadmap is clear enough that David can ask Codex to build a specific phase.

### PR #145 - Local Dashboard Shell

Objective:

- Add the first JARVIS Command Center shell inside existing `web/`, local-first
  and read-only.

Status in this PR:

- Implemented as the local `/jarvis` route in the existing Vite/React web app.
- Static/local UI state only; no backend wiring, sensor activation, approval
  decision path or Hermes execution path is connected.
- The shell shows the required Command Center zones: header, Voice Core visual,
  Mission Control, Approval Console, Hermes Execution, Agent/Module Radar,
  Camera/Vision privacy, Mobile Companion, Finance/ROI, Product Builder,
  timeline/audit preview and visible Kill Switch.
- All unknown or unmeasured cost, revenue and ROI values stay `unknown`; no
  fake metrics, fake revenue or fake costs are displayed.

Scope:

- Add a JARVIS route/nav item to the existing web app.
- Build a dense operator layout, not a marketing page.
- Include panels for system state, Mission Control, Approval Console, Hermes
  Execution, Agent/Module Radar, Timeline, Finance/ROI, Product Builder,
  Memory/Learning, Voice Core, Camera/Privacy, Mobile and Kill Switch.
- Use static/local UI state first if backend wiring is not part of this PR.

Probable files:

- `web/src/App.tsx`
- `web/src/pages/JarvisCommandCenterPage.tsx`
- `web/src/components/jarvis/*`
- `web/src/lib/jarvis-api.ts`
- `web/src/index.css`

Endpoints consumed:

- Optional health/status only: `GET /health`, `GET /operator/console/status`.

New endpoints needed:

- None.

Expected tests:

- `npm run build` from `web/`.
- Component smoke tests only if the repo already has a frontend test pattern.
- Manual Playwright/browser verification if a dev server is used.

Must not do:

- No approval actions.
- No Hermes calls.
- No microphone/camera activation.
- No new dependencies.
- No fake metrics.

Exit criteria:

- David can open a local JARVIS dashboard shell and see all required panels,
  with disabled/unknown states clearly marked.
- PR #145 still does not implement backend wiring real, approvals reales, voz
  real, wake word real, cámara real, mobile real or Hermes execution.

### PR #146 - Backend wiring read model

Objective:

- Connect the dashboard shell to existing read-only/preview endpoints.

Status in this PR:

- Implemented `GET /mark-3/dashboard/status` as the normalized read model for
  the local `/jarvis` dashboard.
- The endpoint aggregates safe local status/readiness/audit sources including
  `/health`, Mark 3 release-candidate status/readiness/capabilities,
  dangerous-route audit, approval-path audit, e2e smoke, pilot plan,
  mission-loop status, Hermes runtime status, voice/wake status,
  camera-control status and mobile companion status.
- The frontend now reads that single endpoint with a conservative fallback to
  `offline`, `unknown`, `not_connected` or `disabled` when the backend or a
  field is unavailable.
- The dashboard remains read-only: no POST/PUT/DELETE from `/jarvis`, no
  approvals, no Hermes execution, no tool runner, no sensor permission request,
  no microphone, no camera, no recording, no WebSocket and no fake metrics.
- JARVIS/Hermes separation remains explicit: JARVIS governs risk, approval,
  audit and control; Hermes remains the execution engine and is not duplicated.

Scope:

- Add a typed frontend API client for JARVIS surfaces.
- Read the aggregated dashboard status endpoint with conservative error states.
- Normalize endpoint payloads into one UI view model/read model.
- Surface `unknown`, `prepare_only`, `disabled`, `blocked`, `approval_required`
  and `safe_to_render` truthfully.

Probable files:

- `jarvis/dashboard_read_model.py`
- `jarvis/api/app.py`
- `web/src/lib/api.ts`
- `web/src/pages/JarvisCommandCenterPage.tsx`
- `tests/jarvis/test_jarvis_dashboard_status_read_model.py`

Endpoints consumed:

- `GET /mark-3/dashboard/status`
- `GET /health`
- `GET /mark-3/release-candidate/status`
- `GET /mark-3/release-candidate/readiness`
- `GET /mark-3/release-candidate/capabilities`
- `GET /mark-3/release-candidate/dangerous-route-audit`
- `GET /mark-3/release-candidate/approval-path-audit`
- `GET /mark-3/release-candidate/e2e-smoke`
- `GET /mark-3/release-candidate/pilot-plan`
- `GET /voice-runtime/status`
- `GET /mark-2/wake-listener/status`
- `GET /camera-control/status`
- `GET /mobile/companion/status`
- `GET /mobile/companion/permissions`
- `GET /mark-3/hermes-runtime/status`
- `GET /mark-3/mission-loop/status`
- `GET /mark-3/research-execution/status`
- `GET /mark-3/product-revenue/status`
- `GET /mark-3/routine-ops/status`
- `GET /mark-3/moonshot-lab/status`
- `GET /mark-3/outcomes`
- `GET /mark-3/learning/proposals`

New endpoints needed:

- `GET /mark-3/dashboard/status`.
- No action endpoint, execute endpoint or approval mutation endpoint was added.

Expected tests:

- API client mapping tests.
- Frontend build.
- Backend tests proving consumed endpoints still return safe payloads.
- Static tests proving `/jarvis` does not call execute paths, browser sensor
  APIs, getUserMedia, POST/PUT/DELETE, or functional approval controls.

Must not do:

- No UI execution.
- No UI approve/reject.
- No WebSocket yet.
- No direct Hermes call from the browser.
- No microphone/camera activation or recording.
- No fake cost, revenue, ROI, results or capability claims.

Exit criteria:

- Dashboard reflects real backend posture and degrades to `unknown` instead of
  inventing data.
- The dashboard can look, but cannot touch: no execution, no approval, no
  sensors, no money, no deploy, no email, no credentials and no duplicate
  Hermes runtime.

### PR #147 - Approval Console visual

Objective:

- Implemented: build a serious visual Approval Console for pending/preview
  approvals while keeping the local dashboard read-only.
- The console shows what an operator would approve, the risk, the scope,
  missing gates and rollback/stop requirements, but it does not approve,
  reject, modify scope, call Hermes or execute anything real.

Scope:

- `jarvis/dashboard_read_model.py` enriches `approvals` with summary counts,
  read-only flags and normalized preview cards.
- Preview cards cover exact local docs/repo read, local file write, external
  web/GitHub search, production/deploy/money/Stripe/email and
  credentials/secrets/tokens/session bypass.
- Every card declares status, risk level, approval level, touched systems,
  estimated/measured cost as `unknown`, scope, evidence, expiry, disabled
  reason, recommended operator action, rollback plan and stop plan.
- Critical actions require readback, strong confirmation, double/triple
  confirmation, rollback/stop plan and audit.
- The UI renders summary counts, risk/approval badges, touched surfaces,
  rollback/stop information, disabled action controls and a risk legend.

Files:

- `jarvis/dashboard_read_model.py`
- `web/src/pages/JarvisCommandCenterPage.tsx`
- `web/src/lib/api.ts`

Endpoints consumed:

- `GET /mark-3/dashboard/status`
- Internal status/audit reads used by that read model remain GET-only.

New endpoints needed:

- None in PR #147.
- Later only: scoped approve/reject backend paths backed by `ApprovalGateway`,
  expiry, readback, challenge and audit.

Expected tests:

- Backend tests prove enriched approvals, disabled frontend approval flags,
  critical gates, forbidden credential/bypass card, no approve/reject routes,
  no active execution/sensors/money/email/deploy and finance/ROI still
  `unknown` without evidence.
- Static frontend tests prove `/jarvis` contains the Approval Console and
  disabled controls, contains the wake phrase/strong confirmation warnings,
  has no POST/PUT/DELETE wiring, no approve/reject/execute paths and no
  browser sensor APIs.

Must not do:

- No approve-all.
- No approval without exact scope.
- No wake phrase as approval.
- No execution after approval.
- No frontend approval execution.
- No Hermes call from the browser.

Exit criteria:

- David can understand exactly what approval would mean and what gates are
  missing before anything can execute.
- JARVIS governs; Hermes executes. This PR prepares the Approval Console UX
  but still approves nothing real and does not duplicate Hermes.

### PR #148 - Hermes Execution Visibility Panel

Objective:

- Make Hermes visible as the governed execution engine behind JARVIS without
  giving the frontend any execution power.

Scope:

- Enrich `GET /mark-3/dashboard/status` under `hermes_execution` with the
  JARVIS/Hermes contract, runtime readiness, active-execution state, last known
  evidence fields, measured cost/duration placeholders and read-only safety
  flags.
- Show governed capabilities: local governed read, local docs/repo research,
  mission-gated execution candidates, approval-gated execution, external tools
  and deploy/email/money/credentials boundaries.
- Show blocked frontend routes/actions: no execute route, no approve/reject
  mutation, no tool runner, no deploy, no money, no email, no credentials, no
  sensor activation, no camera/mic activation and no external network unless a
  future governed backend gate exists.
- Render the `/jarvis` Hermes Execution panel with `JARVIS gobierna. Hermes
  ejecuta.`, read-only/gated/no-active-execution badges, `Sin ejecución
  activa`, unknown cost/duration/result/error and future execution
  requirements: valid approval, exact scope, risk level, rollback/stop plan,
  audit, cost/impact and human operator.
- Keep Kill Switch visible but label it as non-operational for Hermes in this
  PR: there is no active Hermes execution to stop from the panel.

Files:

- `jarvis/dashboard_read_model.py`
- `web/src/pages/JarvisCommandCenterPage.tsx`
- `web/src/lib/api.ts`

Endpoints consumed:

- Frontend consumes only `GET /mark-3/dashboard/status`.
- The read model may internally read existing safe status/audit objects such as
  `/mark-3/hermes-runtime/status`, but it must not call execute or stop routes.

New endpoints needed:

- None in PR #148.

Expected tests:

- Backend tests proving `hermes_execution` contains the contract, refuses
  frontend execution, lists governed capabilities, lists blocked routes,
  requires approval/audit/rollback or stop plan and does not invent execution
  events.
- Static frontend tests proving `/jarvis` contains the Hermes visibility text,
  has no POST/PUT/DELETE wiring, has no execute path literal, no frontend tool
  runner, no browser sensor APIs and keeps Approval Console buttons disabled.

Must not do:

- No generic `POST /hermes/execute`.
- No arbitrary tool invocation.
- No terminal/browser/network/money.
- No raw secret or file content display.
- No stop control wired to a real Hermes session.
- No fake metrics, fake execution, fake result, fake duration or fake cost.

Exit criteria:

- David can see Hermes as the internal execution engine and can see that the UI
  is not a second executor.
- The dashboard is prepared for later Mission Control work, but still cannot
  execute, approve, reject, stop real work or call Hermes directly.

### PR #149 - Mission Control Conversation Preview

Objective:

- Improve `/jarvis` Mission Control so David can see how JARVIS would receive
  a typed or spoken order, classify intent/risk/approval needs and suggest the
  next safe operator review step without opening execution.

Scope:

- Enrich `GET /mark-3/dashboard/status` with `mission_control`:
  `state`, `supported_inputs`, `sample_command`, `intent_preview`,
  `command_lifecycle`, `conversation_preview`, `safety` and
  `operator_guidance`.
- Keep `state.mode=preview` and declare input/conversation as preview-only.
- Keep execution, Hermes dispatch, approval creation, persistence and external
  network disabled.
- Show a safe conversation placeholder:
  David asks JARVIS to review project status and JARVIS explains that sensitive
  action will require approval.
- Show Mission Lifecycle steps visually: draft, preview, intent detected, risk
  classified, approval required, operator review, Hermes gated and audit.
- Show safety labels: No auto execute, No Hermes dispatch, No tool call, No
  file write, No network, No voice recording, No camera capture and Wake phrase
  is not permission.
- Explain how Mission Control relates to Approval Console and Hermes Panel:
  sensitive missions appear in Approval Console, Hermes only executes after a
  valid approval, and frontend cannot bypass gates.

Probable files:

- `jarvis/dashboard_read_model.py`
- `web/src/pages/JarvisCommandCenterPage.tsx`
- `web/src/lib/api.ts`

Endpoints consumed:

- Frontend consumes only `GET /mark-3/dashboard/status`.
- The read model remains local/read-only and does not call Hermes execute,
  providers, sensors, memory writes or mission mutation endpoints.

New endpoints needed:

- None in PR #149.

Expected tests:

- Backend tests proving `mission_control` exists, all execution/dispatch/
  approval/persistence/network flags are disabled, `conversation_preview`
  declares no provider call, no memory write and no raw audio storage, safety
  forbids auto execute/tool/file/network/sensors, timeline contains only
  read-only preview events and no new dangerous endpoints are added.
- Static frontend tests proving `/jarvis` contains Control de Misión,
  preview-only, conversation preview, intent/risk preview, lifecycle, safety
  labels, Approval Console/Hermes relation text, no POST/PUT/DELETE literals, no
  execution path wiring, no submit handler and no browser sensor API.

Must not do:

- No real command submit.
- No mission creation.
- No approval creation.
- No Hermes dispatch.
- No tool call.
- No provider call.
- No memory write or transcript persistence.
- No file write.
- No network call.
- No voice recording, camera capture, microphone or `getUserMedia`.
- No money, deploy, email or credentials.

Exit criteria:

- David can see how it would feel to type or speak to JARVIS, inspect the
  intended classification shape, review safety gates and understand the next
  safe operator-review step, while the system remains preview/read-only and
  Hermes remains separate behind JARVIS gates.

### PR #150 - Voice Interaction Layer

Objective:

- Deliver the macro voice interaction layer for `/jarvis`: Voice Core Visual,
  TTS State Preview and Wake Word Local Safe Flow, all through a safe read-only
  dashboard contract without activating microphone, wake word, STT, TTS,
  recording, providers or Hermes execution.

Scope:

- Enrich `GET /mark-3/dashboard/status` with `voice_core`.
- Expose `voice_core.state` with `mode=preview`, `current_state=preview` or
  `dormant`, and all runtime capabilities disabled:
  `microphone_enabled=false`, `wake_word_enabled=false`,
  `command_listening_enabled=false`, `tts_enabled=false`, `stt_enabled=false`,
  `audio_recording=false`, `raw_audio_stored=false`,
  `external_provider_called=false`, `voice_approval_enabled=false`,
  `wake_phrase_can_approve=false` and `wake_phrase_can_execute=false`.
- Expose `visual_states` for offline, online, preview, dormant,
  listening_wake_word, listening_command, thinking, speaking,
  approval_required, hermes_executing, paused, blocked, error and kill_switch.
  Each state declares label, description, risk, enabled preview/false,
  sensor requirement and `can_approve=false`.
- Expose `tts_state` as preview/disabled visibility only: speaking false,
  preview subtitles enabled from `preview/read_model`, audio output disabled,
  provider `none/not_connected` and no external call.
- Expose `wake_word_policy` with future phrases `Hola Jarvis` and `Jarvis`,
  wake runtime disabled/not connected/preview, wake phrase not permission,
  cannot approve, cannot execute, authenticated approval channel required for
  future approval, and critical actions requiring readback plus strong
  confirmation.
- Expose privacy and safety contracts: no microphone activation, no audio
  recording, no raw audio storage, no external audio provider, no background
  listening, no voice biometrics, no voice approval without gate, no auto
  execute, no Hermes dispatch, no tool call, no sensor activation, no browser
  media capture APIs and visible kill switch.
- Add timeline events: Voice Core visual state read, Voice/TTS state preview
  generated, Microphone disabled, Wake word runtime not active and No audio
  recording performed.
- Update `/jarvis` Voice Core to show a serious central voice nucleus, visual
  states, preview subtitles, wake policy, privacy, Approval Console/Hermes
  relationship and Kill Switch semantics.
- Enrich `GET /mark-3/dashboard/status` with `wake_word_flow`.
- Expose `wake_word_flow.state` with `mode=preview`,
  `wake_runtime_enabled=false`, `microphone_hard_off=true`,
  `wake_word_only_mode=false`, `command_window_open=false`,
  `push_to_talk_preview_enabled=true`, `typed_wake_preview_enabled=true`,
  `always_on_microphone_enabled=false`, `background_listener_enabled=false`,
  `stt_enabled=false`, `audio_recording=false`, `raw_audio_stored=false` and
  `external_provider_called=false`.
- Expose supported wake phrases `Hola Jarvis` and `Jarvis`, plus future safe
  stop phrases such as `para`, `cancela`, `detente`, `silencio`,
  `cancelar misión` and `apaga escucha`.
- Explain mode differences: mic hard-off, future wake-word-only, future command
  listening, future push-to-talk and current typed preview.
- Expose typed `wake_parse_preview` for
  `Hola Jarvis, revisa el estado del proyecto`: detected wake phrase
  `Hola Jarvis`, remaining command preview `revisa el estado del proyecto`,
  would open a command window in the future, but would not execute, approve,
  call Hermes, record audio or call providers.
- Expose wake approval policy: wake phrase is not permission, cannot approve,
  cannot execute, voice approval requires authenticated channel, sensitive
  actions require readback, critical actions require double/triple confirmation
  and approval events must be audited.
- Expose wake flow safety: no microphone activation, no browser media capture,
  no background listening, no raw audio storage, no external STT/TTS, no Hermes
  dispatch, no tool call and no auto execute.
- Add timeline events: Wake word flow preview read, Microphone hard-off
  confirmed, Typed wake preview available, Wake phrase cannot approve, Wake
  phrase cannot execute and No background listener started.
- Update `/jarvis` with `Wake Word Local Safe Flow`, current state, supported
  phrases, stop phrases, mode explanations, typed parsing preview, policy and
  safety banner.

Probable files:

- `jarvis/dashboard_read_model.py`
- `web/src/pages/JarvisCommandCenterPage.tsx`
- `web/src/lib/api.ts`

Endpoints consumed:

- `/jarvis` consumes only `GET /mark-3/dashboard/status`.
- The read model internally reads safe status sources only:
  `GET /voice-runtime/status` and `GET /mark-2/wake-listener/status`.

New endpoints needed:

- None in PR #150.

Expected tests:

- Backend read model tests proving `voice_core` exists and all microphone,
  wake word, TTS, STT, recording, raw storage, provider, approval and execution
  flags remain disabled.
- Backend read model tests proving `wake_word_flow` exists, wake runtime and
  background listener are disabled, mic hard-off is true, supported/stop
  phrases are exposed, typed parsing would not execute/approve/call Hermes and
  all wake flow safety flags remain true.
- Frontend/static shell tests proving `/jarvis` contains the Voice Core visual,
  preview subtitles, Wake Word Local Safe Flow, wake phrase warnings, privacy
  rows and no browser sensor APIs, no submit handlers and no mutating frontend
  calls.
- Roadmap docs tests proving the visual/voice/vision/mobile contract remains
  explicit and safe.

Must not do:

- No microphone.
- No wake word runtime.
- No wake word listener.
- No command listening.
- No STT.
- No TTS.
- No audio output.
- No voice approval.
- No raw audio storage.
- No background listening.
- No browser media capture.
- No external audio service unless configured and approved.
- No voice-only critical approval.
- No direct Hermes call from voice or frontend.

Exit criteria:

- JARVIS visibly communicates whether it is asleep, listening, thinking,
  speaking, waiting for approval, executing through Hermes, paused, blocked or
  under kill switch as visual states, while the current state remains safe
  preview/dormant and no real audio is captured, stored, played or sent.
- PR #150 includes the local wake word safe flow as typed preview/read-only:
  JARVIS can show how `Hola Jarvis` or `Jarvis` would open a future command
  window, while wake phrase still cannot approve, execute, call Hermes, record
  audio or call providers.

### PR #151 - Vision + Mobile Companion Layer

Objective:

- Add visibility and future structure for camera/vision and mobile companion
  without activating sensors, capture, runtime, approvals or execution.
- Group two safe read-only surfaces:
  Camera / Vision Privacy Panel and Mobile Companion / PWA baseline preview.

Scope:

- Enrich `GET /mark-3/dashboard/status` with `camera_vision`:
  `mode=preview`, camera enabled false, permission requested false, preview
  disabled, recording false, streaming false, snapshot capture disabled, vision
  analysis disabled, image/video storage disabled, external provider not called,
  local vision model unknown unless evidence exists and background camera access
  false.
- Add `camera_vision.privacy` and `scope_policy`: no camera activation, no
  browser media capture, no stream, no recording, no snapshot, no image/video
  storage, no external provider, explicit operator permission required, visible
  indicator required for any future camera activity and audit required for
  future vision.
- Add camera visual states for camera off, future availability, preview
  disabled, permission required, analysis future, recording disabled, storage
  disabled, blocked and kill switch; every state has label, description, risk,
  enabled false/preview/future-gated and `can_execute=false`.
- Add `mobile_companion`:
  `mode=preview`, PWA baseline preview, mobile runtime disabled, mobile cannot
  execute, cannot call Hermes directly, cannot approve/reject/modify real
  actions, notifications disabled, remote kill switch disabled/future-gated,
  mobile camera/microphone disabled and no external network requirement.
- Add future mobile views for status, approvals preview, mission preview,
  Hermes visibility, voice status, camera status, finance summary and kill
  switch preview. Every mobile view is preview/future-gated/disabled/unknown,
  `can_execute=false`, `can_call_hermes=false`.
- Add `pwa_policy`: installable PWA preview only, offline cache disabled, push
  notifications disabled, service worker disabled unless a safe one already
  exists, no background sync, no credential storage and no token storage.
- Upgrade `/jarvis` with two visible panels:
  `Cámara / Visión` and `Mobile Companion`.

Probable files:

- `jarvis/dashboard_read_model.py`
- `web/src/lib/api.ts`
- `web/src/pages/JarvisCommandCenterPage.tsx`
- `tests/jarvis/test_jarvis_dashboard_status_read_model.py`
- `tests/jarvis/test_jarvis_local_dashboard_shell.py`
- `docs/jarvis-visual-voice-vision-mobile-roadmap.md`
- `docs/jarvis-handoff-context.md`
- `docs/JARVIS_MASTER_BUILD_MAP.md`

Endpoints consumed:

- `GET /mark-3/dashboard/status`
- Existing read-only sources inside that read model:
  `GET /camera-control/status`, `GET /mobile/companion/status` and
  `GET /mobile/companion/permissions`.

New endpoints needed:

- None.

Expected tests:

- Backend read-model tests proving camera/vision and mobile companion sections
  exist and all real sensor/runtime/action flags stay false.
- Static `/jarvis` tests proving the required safety text is visible and no
  sensor API, service worker, push, background sync, POST/PUT/DELETE,
  `/execute`, approval mutation or Hermes direct call is added.
- Roadmap docs tests proving PR #151 is documented as Vision + Mobile Companion
  Layer.

Must not do:

- No camera activation.
- No browser media capture.
- No snapshot capture.
- No recording.
- No streaming.
- No image or video storage.
- No vision analysis real.
- No external vision provider.
- No local vision model connection unless evidence exists.
- No mobile runtime.
- No mobile execution.
- No direct mobile/camera/voice/frontend call to Hermes.
- No real mobile approvals.
- No service worker, push notification, background sync, offline cache,
  credentials storage or token storage.
- No sensors.
- No deploy, money, email, credentials or external network.

Exit criteria:

- David can see camera/vision privacy status and mobile companion/PWA baseline
  preview in `/jarvis`, with truthful disabled/future-gated states and no real
  sensor activation, capture, storage, mobile runtime, approval bypass or
  Hermes direct path.

### PR #152 - Product Finance Pilot Hardening

Objective:

- Close the visual/operational dashboard pilot with honest Finance/ROI,
  Adaptive Product Builder and Frontend Pilot/Hardening panels.
- Group three safe surfaces: Finance / ROI Panel realista, Product Builder
  Adaptativo and Frontend Pilot / Hardening.
- Keep `/jarvis` as a read-only preview surface consuming only
  `GET /mark-3/dashboard/status`.

Scope:

- Enrich `GET /mark-3/dashboard/status` with `finance_roi`, including
  `truth_policy`, metric objects, budget, safety and timeline.
- All finance metrics default to `unknown` with `source=not_measured`,
  `evidence_state=missing` and `confidence=unknown` unless real evidence is
  connected. This covers actual cost, estimated cost, confirmed revenue,
  projected revenue, gross revenue, expenses, net revenue, ROI, token/API/infra
  cost, manual input cost and revenue source.
- Enrich the read model with `adaptive_product_builder` in `mode=preview`:
  product generation, code generation, deploy, Stripe, landing publish,
  external research and Hermes dispatch are all disabled.
- Product Builder stages are Idea, Validación, Blueprint, Código, Landing,
  Deploy candidate, Monetización and Medición. Every stage has
  `can_execute=false`, evidence requirements and approval metadata.
- Enrich the read model with `frontend_pilot` in `mode=read_only_pilot`, route
  `/jarvis`, endpoint `/mark-3/dashboard/status`, readiness checks, hardening
  notes and pilot limitations.
- Upgrade `/jarvis` with three panels: `Finance / ROI`, `Product Builder
  Adaptativo` and `Frontend Pilot / Hardening`.

Truth and safety rules:

- No fake metrics.
- No fake revenue.
- No fake costs.
- No fake ROI.
- Confirmed revenue requires evidence.
- Projected revenue must be labeled.
- ROI remains unknown without real revenue and real costs.
- No money movement.
- No Stripe live.
- No checkout creation.
- No invoice creation.
- No payment collection.
- No product generation.
- No real deploy.
- No publishing.
- No external network.
- No email.
- No credentials.
- No direct Hermes dispatch from frontend, mobile, voice or camera.

Frontend pilot and dependency notes:

- `/jarvis` remains a read-only pilot: the dashboard looks, it does not touch.
- The page must not add frontend execute, approval mutation, sensor activation,
  money, deploy, email, credential or product-publish paths.
- `No POST/PUT/DELETE` is a visible safety rule for the dashboard page; any
  dependency hardening or `npm audit fix` that changes lockfiles/dependencies
  belongs in a separate PR.
- Dependency hardening queda para una PR separada si toca lockfile/deps.
- Full pytest and frontend build remain required before merge.

Expected tests:

- Backend read-model tests proving `finance_roi`, `adaptive_product_builder`
  and `frontend_pilot` exist and keep all real action flags disabled.
- Static `/jarvis` tests proving the required copy is visible, the dashboard
  consumes only the read model and no execute, Stripe checkout, money movement
  or fake metrics implementation is introduced.
- Roadmap/docs tests proving PR #152 is documented as Product Finance Pilot
  Hardening and remains read-only/preview.

Must not do:

- No Stripe live.
- No checkout.
- No invoice.
- No payment collection.
- No deploy.
- No publish.
- No real product creation.
- No fake revenue, cost or ROI.
- No sensor activation.
- No frontend file writes.
- No Hermes execution.
- No dependency or lockfile hardening unless intentionally split into another
  PR.

Exit criteria:

- David can see honest finance/product/pilot readiness state in `/jarvis`, with
  unknowns preserved where evidence is absent, and no real money, Stripe,
  deploy, publishing, email, credentials, sensors or Hermes execution path.

### PR #154 - Future real Finance/ROI and Product Builder activation

Note: PR #152 implements the read-only/preview Finance/ROI and Adaptive Product
Builder dashboard panels. This later section is only for a future activation
phase if JARVIS gains real evidence connectors or product actions under
separate approvals.

Objective:

- Make revenue, cost, ROI and product-building truth visible in the Command
  Center.

Scope:

- Show measured cost, estimated cost, confirmed revenue, projected revenue,
  gross revenue, expenses, net revenue and ROI with source labels.
- Show Product Builder Adaptativo lifecycle: idea, validation, blueprint, code
  candidate, landing, deploy candidate, monetization and blocked gates.
- Display `unknown` when evidence is missing.

Probable files:

- `web/src/components/jarvis/FinanceRoiPanel.tsx`
- `web/src/components/jarvis/ProductBuilderPanel.tsx`
- `web/src/lib/jarvis-finance.ts`
- `web/src/lib/jarvis-product-builder.ts`

Endpoints consumed:

- `GET /mark-2/dashboard/costs`
- `GET /mark-3/product-revenue/status`
- `POST /mark-3/product-revenue/opportunity`
- `POST /mark-3/product-revenue/blueprint`
- `POST /mark-3/product-revenue/experiment`
- `POST /mark-3/product-revenue/decision`
- `GET/POST /monetization/*`
- `GET/POST /payments-revenue/*`
- `GET/POST /product-builder/*`
- `GET/POST /asset-factory/*`
- `GET/POST /deploy-publishing/*`

New endpoints needed:

- Optional later: `GET /jarvis/finance/summary` if aggregating evidence across
  modules becomes necessary.

Expected tests:

- Mapping tests for measured/estimated/unknown.
- UI tests ensuring no fake revenue/cost/ROI is displayed.

Must not do:

- No Stripe live.
- No checkout.
- No deploy.
- No domain purchase.
- No real publishing.
- No invented revenue, cost or ROI.

Exit criteria:

- David sees honest finance and product-builder state, with every value labeled
  measured, estimated or unknown.

### PR #155 - Frontend pilot and hardening

Objective:

- Run a controlled local frontend pilot and harden findings before activating
  any real sensors or execution actions.

Scope:

- E2E test the dashboard with the local API.
- Add accessibility, responsive and error-state hardening.
- Add visual regression/browser screenshots if the repo accepts that pattern.
- Document pilot findings.
- Verify no UI path calls dangerous endpoints.

Probable files:

- `docs/jarvis-visual-command-center-pilot-findings.md`
- `web/src/**`
- `tests/jarvis/**`
- optional frontend test files under existing web test conventions if added

Endpoints consumed:

- All dashboard read/preview endpoints used by earlier PRs.

New endpoints needed:

- None unless pilot finds a read-only aggregation gap.

Expected tests:

- `git diff --check`
- backend JARVIS tests
- `npm run build`
- browser smoke on desktop and mobile viewport

Must not do:

- No production deployment.
- No real mic/camera.
- No real money.
- No email.
- No external network by default.
- No approval bypass.

Exit criteria:

- David can use a local JARVIS Command Center pilot that is truthful, safe,
  responsive and ready for the next backend capability decision.

## 6. Safety model

### Microphone

- Hard-off means no microphone usage.
- Wake-word-only means local activation phrase detection only.
- Command listening is short-window and visible.
- No raw audio storage by default.
- External STT requires explicit setup and approval.

### Wake word

- `Hola JARVIS` and `JARVIS` may open a session.
- Wake phrase is not permission.
- Wake phrase cannot approve.
- Low confidence means no action or clarification.

### Voice

- Voice can explain, preview, read back and request approval.
- Critical approvals require strong confirmation and visual/written readback,
  not voice alone.
- TTS must not publish or store audio unless explicitly requested.

### Camera / vision

- Camera off is default.
- Camera preview requires explicit opt-in and visible indicator.
- No recording by default.
- No streaming by default.
- No retention by default.
- No external upload by default.
- Face/person analysis is disabled by default.
- `no mires` must stop future sessions immediately.

### Approvals

- Approval must show exact action, scope, risk, duration, challenge/readback,
  rollback/stop and audit.
- Approval is not execution.
- Strong approval is required for money, production, deploy, publishing,
  identity, credentials, contracts, irreversible changes and sensitive capture.

### Hermes

- Hermes never receives direct calls from UI/mobile/voice/camera.
- Hermes executes only bounded tasks routed by JARVIS after policy and approval.
- Current real slice is local `read_file` only.

### Mobile

- Mobile is an interface, not a runtime.
- No mobile direct Hermes.
- No mobile direct filesystem.
- No secrets in notifications.
- Pairing/trust must be revocable and scoped.

### Kill switch

- Kill switch must be visible.
- Stop controls must be reachable from desktop and mobile surfaces.
- A future global kill endpoint must be governed, audited and must stop
  missions, Hermes sessions, voice listening and camera sessions where active.

## 7. UX states

Every panel should map backend state into one of these visible states:

- `offline`: API/runtime unavailable.
- `online`: available and safe to render.
- `preview`: user is reviewing a prepare-only candidate.
- `listening_wake_word`: wake-word-only, no command processing.
- `listening_command`: short command window after wake or push-to-talk.
- `thinking`: JARVIS is classifying, planning or waiting for backend response.
- `speaking`: TTS/voice response active or simulated.
- `approval_required`: action needs approval before any execution.
- `hermes_executing`: governed Hermes session is running.
- `paused`: runtime or mission is paused/stopped by user control.
- `blocked`: policy, approval, scope, capability or setup gate blocks progress.
- `error`: failed request, invalid payload or runtime error.
- `kill_switch`: global or mission-level stop control is active.

State rules:

- `approval_required` cannot be shown as `executing`.
- `preview` cannot be shown as completed work.
- `unknown` must stay visible when no measured data exists.
- `hermes_executing` only applies to actual governed Hermes sessions.
- Mic and camera states must be visible independently from mission state.

## 8. Data truth rules

The UI must label data as:

- `measured`: captured from a real execution, provider, audit event or explicit
  evidence.
- `estimated`: calculated or projected from assumptions, with source and
  confidence.
- `unknown`: not measured and not safely inferable.

Rules:

- never fake metrics;
- never fake revenue;
- never fake costs;
- never fake ROI;
- never show projected revenue as confirmed revenue;
- never show a candidate as deployed, published, paid or completed;
- use `unknown/no fake metrics` when evidence is absent;
- local compute may show direct provider cost as `0` only when clearly labeled,
  while hardware/electricity stay `unknown`;
- subscription limits are not per-call API cost unless manually/evidentially
  measured.

## 9. Que NO debe construirse porque duplicaria Hermes

- A new frontend agent loop.
- A browser-side tool runner.
- A second tool registry.
- A separate mission executor in React.
- Direct mobile/voice/camera calls into Hermes.
- Generic `/hermes/execute` endpoints.
- UI scripts that run terminal/browser/network operations.
- A frontend queue that retries sensitive actions automatically.
- A metrics engine that invents cost, revenue or ROI.
- A wake-word runtime that approves or executes.
- A camera runtime that streams/records by default.

## 10. Recommended next PR

Recommended next PR after PR #151:

```text
PR #152 - Product Finance Pilot Hardening
```

Why:

- PR #145 gave David the visible cockpit without enabling dangerous actions.
- PR #146 wires real read-only status into that cockpit without execution.
- PR #147 improves the Approval Console visual with normalized preview cards,
  disabled approval affordances and risk/readback/rollback visibility while
  still approving nothing real.
- PR #148 makes Hermes execution visibility clearer without giving the browser
  a direct tool runner, stop control, execute route or duplicate runtime.
- PR #149 added Mission Control Conversation Preview without creating missions,
  approvals, providers, memory writes or Hermes dispatch.
- PR #150 gives Voice Core visual presence, TTS state preview and Wake Word
  Local Safe Flow without microphone, wake runtime, STT, TTS, recording, raw
  storage, background listener or providers.
- PR #151 adds camera/vision privacy and mobile/PWA companion state without
  activating camera, capture, sensors, service worker, push, mobile runtime,
  mobile approvals or direct Hermes calls.
- The next safe step is Product Finance Pilot Hardening: Finance/ROI truth,
  Adaptive Product Builder preview and Frontend Pilot/Hardening without money,
  Stripe live, checkout, product creation, deploy, fake metrics or frontend
  execution.
- It keeps the central rule intact: JARVIS governs, Hermes executes.
