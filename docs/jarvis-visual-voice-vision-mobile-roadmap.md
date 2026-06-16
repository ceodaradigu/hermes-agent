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

### PR #146 - Backend wiring read model

Objective:

- Connect the dashboard shell to existing read-only/preview endpoints.

Scope:

- Add a typed frontend API client for JARVIS surfaces.
- Poll read-only endpoints with conservative error states.
- Normalize endpoint payloads into one UI view model.
- Surface `unknown`, `prepare_only`, `disabled`, `blocked`, `approval_required`
  and `safe_to_render` truthfully.

Probable files:

- `web/src/lib/jarvis-api.ts`
- `web/src/lib/jarvis-view-model.ts`
- `web/src/hooks/useJarvisStatus.ts`
- `web/src/components/jarvis/*`

Endpoints consumed:

- `GET /command-center`
- `GET /operator/console/snapshot`
- `GET /mark-2/dashboard/overview`
- `GET /mark-3/release-candidate/status`
- `GET /mark-3/mission-loop/status`
- `GET /mark-3/hermes-runtime/status`
- `GET /voice/runtime/status`
- `GET /voice-runtime/status`
- `GET /camera-control/status`
- `GET /ambient-vision/status`
- `GET /mobile/companion/status`
- `GET /devices/runtime/status`

New endpoints needed:

- Optional later aggregator: `GET /jarvis/command-center/snapshot`.
- Do not add it unless endpoint fan-out becomes fragile.

Expected tests:

- API client mapping tests.
- Frontend build.
- Backend tests proving consumed endpoints still return safe payloads.

Must not do:

- No UI execution.
- No UI approve/reject.
- No WebSocket yet.
- No direct Hermes call from the browser.

Exit criteria:

- Dashboard reflects real backend posture and degrades to `unknown` instead of
  inventing data.

### PR #147 - Approval Console visual

Objective:

- Build a serious visual Approval Console for pending and preview approvals,
  still read-only unless a later backend approval-action path exists.

Scope:

- Show exact action, risk level, affected scope, requester, channel, readback,
  strong approval, double/triple confirmation, expiry, context fingerprint,
  missing gates and rollback/stop plan.
- Clearly distinguish preview approvals, pending approvals and executable
  approvals.
- Add disabled approve/reject controls with explicit "not connected" state.

Probable files:

- `web/src/components/jarvis/ApprovalConsole.tsx`
- `web/src/components/jarvis/ApprovalDetail.tsx`
- `web/src/lib/jarvis-approvals.ts`

Endpoints consumed:

- `GET /mark-2/dashboard/approvals`
- `GET /approvals/status`
- `GET /approvals/policy`
- `GET /approval-execution/status`
- `POST /approval-execution/preview-decision`
- `POST /approval-execution/preview-critical-warning`
- `POST /mark-2/voice-approval/preview-flow`

New endpoints needed:

- Later, not in this PR: scoped `POST /approvals/{id}/approve` and
  `POST /approvals/{id}/reject` backed by `ApprovalGateway`, expiry, readback,
  challenge and audit.

Expected tests:

- Rendering tests for normal, sensitive, strong, expired, blocked and unknown
  approvals.
- Backend absence-of-dangerous-routes test if new endpoints are added later.

Must not do:

- No approve-all.
- No approval without exact scope.
- No wake phrase as approval.
- No execution after approval.

Exit criteria:

- David can understand exactly what approval would mean and what gates are
  missing before anything can execute.

### PR #148 - Hermes Execution Visibility Panel

Objective:

- Show what Hermes is allowed to do for JARVIS today and what it is doing when
  a governed session exists.

Scope:

- Render Hermes runtime status, supported capability, disabled capabilities,
  session count, running sessions, candidate id, mission id, scope fingerprint,
  status, interrupt state, tool calls and evidence summary.
- Provide a visible stop control for existing Hermes session stop route when
  authorized backend semantics are already satisfied.

Probable files:

- `web/src/components/jarvis/HermesExecutionPanel.tsx`
- `web/src/components/jarvis/HermesSessionDrawer.tsx`
- `web/src/lib/jarvis-hermes.ts`

Endpoints consumed:

- `GET /mark-3/hermes-runtime/status`
- `GET /mark-3/hermes-runtime/sessions/{session_id}`
- `POST /mark-3/hermes-runtime/sessions/{session_id}/stop`
- `GET /mark-3/mission-loop/missions/{mission_id}`
- `GET /mark-3/mission-loop/missions/{mission_id}/audit`

New endpoints needed:

- `GET /mark-3/hermes-runtime/sessions` if the UI needs a session list rather
  than known session ids.
- Do not add general execute endpoints.

Expected tests:

- UI mapping tests for idle/running/stopped/blocked/timeout states.
- Backend tests for any new list endpoint proving it redacts content and does
  not expose raw file contents.

Must not do:

- No generic `POST /hermes/execute`.
- No arbitrary tool invocation.
- No terminal/browser/network/money.
- No raw secret or file content display.

Exit criteria:

- David can see Hermes as the internal execution engine and can see that the UI
  is not a second executor.

### PR #149 - Mission Control and conversation panel

Objective:

- Let David talk/type to JARVIS locally and turn conversation into mission
  proposals, risk, permissions and next step without auto-execution.

Scope:

- Add local chat/conversation panel.
- Use existing intent preview first.
- Show detected intent, confidence, risk, policy decision, approval need,
  candidate mission fields and next safe action.
- Add a mission creation review form that posts to Mark 3 Mission Loop only
  after David explicitly chooses "create mission proposal".
- Show mission lifecycle, plan, candidates, outcomes, audit and stop.

Probable files:

- `web/src/components/jarvis/ConversationPanel.tsx`
- `web/src/components/jarvis/MissionControlPanel.tsx`
- `web/src/lib/jarvis-missions.ts`

Endpoints consumed:

- `POST /voice/companion/preview`
- `POST /mobile/intent/preview`
- `GET /mark-3/mission-loop/policy`
- `POST /mark-3/mission-loop/missions`
- `GET /mark-3/mission-loop/missions/{mission_id}`
- `POST /mark-3/mission-loop/missions/{mission_id}/advance`
- `POST /mark-3/mission-loop/missions/{mission_id}/feedback`
- `POST /mark-3/mission-loop/missions/{mission_id}/stop`
- `GET /mark-3/mission-loop/missions/{mission_id}/audit`

New endpoints needed:

- Optional: `POST /jarvis/conversation/preview` to avoid overloading voice or
  mobile intent preview for desktop chat.

Expected tests:

- Conversation preview tests for allowed, requires approval, denied, sensitive
  redacted and unknown.
- Mission form tests requiring scope, stop conditions and explicit create
  action.

Must not do:

- No auto mission creation from plain chat.
- No execution from chat.
- No Hermes call before policy/approval/candidate.

Exit criteria:

- David can ask for a mission, review what JARVIS understood, see risk/gates and
  create a governed mission proposal deliberately.

### PR #150 - Voice Core visual and TTS wiring

Objective:

- Add the central animated Voice Core visual and wire it to safe voice state,
  TTS status and subtitles without activating microphone.

Scope:

- Build a non-human central core animation.
- Map voice states: dormant, wake-word listening, command listening, thinking,
  speaking, approval required, Hermes executing, paused, blocked and error.
- Show live subtitles from text transcript previews.
- Show TTS provider status and generated-audio status when `save_audio=true`
  is explicitly used through backend.
- Prepare Web Audio analyser integration later, but do not require it now.

Probable files:

- `web/src/components/jarvis/VoiceCore.tsx`
- `web/src/components/jarvis/VoiceStatusPanel.tsx`
- `web/src/lib/jarvis-voice.ts`

Endpoints consumed:

- `GET /voice/status`
- `POST /voice/tts`
- `GET /voice/runtime/status`
- `POST /voice/runtime/control`
- `POST /voice/runtime/transcript`
- `GET /voice/companion/status`
- `GET /voice/companion/control-policy`
- `POST /voice/companion/preview`

New endpoints needed:

- Optional later: `GET /voice/runtime/events` for live subtitles/state.

Expected tests:

- Component state mapping tests.
- TTS request tests proving `save_audio=false` by default.
- Browser verification for animation and responsive layout.

Must not do:

- No microphone.
- No raw audio storage.
- No external audio service unless configured and approved.
- No voice-only critical approval.

Exit criteria:

- JARVIS visibly communicates whether it is asleep, listening, thinking,
  speaking, waiting for approval, executing through Hermes, paused or blocked.

### PR #151 - Wake word local safe flow

Objective:

- Add a safe local wake-word UX flow without enabling always-on microphone by
  default.

Scope:

- Expose wake-word policy, supported phrases and stop phrases.
- Add push-to-talk/simulated transcript controls.
- Show clear state difference between mic hard-off, wake-word-only and
  listening-command.
- Add a future implementation plan for local wake engine and STT adapter if
  David approves a later runtime PR.

Probable files:

- `web/src/components/jarvis/WakeWordPanel.tsx`
- `web/src/lib/jarvis-wake.ts`
- optional docs/runbook update for local wake runtime

Endpoints consumed:

- `GET /voice-runtime/status`
- `GET /voice-runtime/policy`
- `POST /voice-runtime/preview-wake-parse`
- `POST /voice-runtime/preview-session`
- `POST /voice-runtime/preview-command`
- `POST /voice-runtime/preview-stop`
- `GET /mark-2/wake-listener/status`
- `POST /mark-2/wake-listener/preview-transcript`

New endpoints needed:

- Later only, behind explicit setup: `POST /voice/runtime/start-microphone` is
  not recommended until threat model, local provider choice and visual
  indicator are implemented.

Expected tests:

- Wake parse tests for `Hola Jarvis`, `Jarvis`, low confidence and command
  extraction.
- UI tests proving wake phrase never toggles approval.

Must not do:

- No always-on mic.
- No background listening by default.
- No wake phrase approval.
- No external STT by default.

Exit criteria:

- David can safely test the wake UX with typed/push-to-talk input and see why it
  cannot execute or approve by itself.

### PR #152 - Camera/Vision Privacy Panel

Objective:

- Add the camera/vision privacy surface before any real camera or vision
  runtime work.

Scope:

- Show camera state: off, available, preview requested, analyzing requested,
  recording disabled, recording active only when future permission exists.
- Show explicit privacy policy, stop phrase `no mires`, no recording by
  default, no streaming by default, no retention by default, no external upload.
- Add disabled controls for future preview/analyze/record with clear approval
  requirements.
- Optionally build browser permission UI skeleton without calling
  `getUserMedia` yet.

Probable files:

- `web/src/components/jarvis/CameraPrivacyPanel.tsx`
- `web/src/components/jarvis/VisionScopePanel.tsx`
- `web/src/lib/jarvis-vision.ts`

Endpoints consumed:

- `GET /camera-control/status`
- `GET /camera-control/policy`
- `POST /camera-control/preview-session`
- `POST /camera-control/preview-stop`
- `GET /ambient-vision/status`
- `GET /ambient-vision/privacy-policy`
- `POST /ambient-vision/session-preview`
- `GET /ambient-vision/stop-control`

New endpoints needed:

- Later only: a local camera runtime endpoint must require explicit opt-in,
  visible indicator, no retention, stop and audit before using real frames.

Expected tests:

- UI tests for off/available/preview/analyzing/recording-disabled states.
- Backend tests if any new preview fields are added.

Must not do:

- No real camera activation.
- No recording.
- No streaming.
- No image storage.
- No face/person analysis by default.
- No external vision upload.

Exit criteria:

- David can always tell whether camera/vision is off, available, previewing,
  analyzing or blocked, and the UI cannot silently start capture.

### PR #153 - Mobile Companion / PWA baseline

Objective:

- Add a minimal mobile-safe JARVIS companion surface, preferably as responsive
  PWA pages in existing `web/` before considering native apps.

Scope:

- Responsive mobile route with status, pending approvals, mission state,
  mic/camera indicators, alerts placeholder and kill switch placeholder.
- Use reduced Mobile Command Center snapshot.
- Support text intent preview from mobile.
- Prepare approve/reject UI as disabled until trusted-device approval path
  exists.

Probable files:

- `web/src/pages/JarvisMobilePage.tsx`
- `web/src/components/jarvis/mobile/*`
- `web/public/manifest.webmanifest` only if PWA is explicitly accepted and no
  dependency is needed.

Endpoints consumed:

- `GET /mobile/companion/status`
- `GET /mobile/companion/permissions`
- `GET /mobile/command-center`
- `POST /mobile/intent/preview`
- `GET /devices/runtime/status`
- `GET /devices/registry`
- `POST /devices/pairing/preview`
- `POST /devices/approval-channel/preview`

New endpoints needed:

- Later: authenticated pairing, revoke, trusted device and approval decision
  endpoints.

Expected tests:

- Responsive/browser verification on mobile viewport.
- UI tests proving mobile cannot approve, reject or execute when backend says
  disabled.

Must not do:

- No native app.
- No push.
- No background sync.
- No mobile secrets.
- No mobile direct filesystem/Hermes.

Exit criteria:

- David can open a mobile-sized JARVIS companion view locally and inspect state
  without creating a new runtime or approval bypass.

### PR #154 - Finance/ROI and Product Builder panels

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

Recommended next PR after this roadmap:

```text
PR #145 - JARVIS Local Dashboard Shell
```

Why:

- It gives David the visible cockpit without enabling dangerous actions.
- It uses existing `web/` and existing local dependencies.
- It proves the information architecture before wiring live controls.
- It keeps the central rule intact: JARVIS governs, Hermes executes.
