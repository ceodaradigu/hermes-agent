# JARVIS Future/Moonshot Layer - Phase S

## Purpose

Phase S provides a safe, prepare-only foundation for evaluating advanced or future capabilities. It
can describe concepts, expose risks, identify evidence gaps, and preview approval requirements. It
does not activate or connect any real capability.

The layer follows `docs/JARVIS_MASTER_BUILD_MAP.md`: advanced exploration is allowed only when it
does not bypass safety, legality, privacy, explicit permission, audit, rollback, or strong approval.

## What It Allows

- Concept previews for smart glasses, AR overlays, robotics, drones, simulation, and physical-world
  automation.
- Legal and safety question preparation without claiming a legal conclusion or safety clearance.
- Controlled-environment, immediate-stop, audit, and rollback planning.
- Practical-value and monetization-advantage review.
- Identity and impersonation risk review.
- Approval-requirement previews.
- Read-only readiness markers in Command Center and Operator Console.

All responses have `prepare_only: true`. Execution, devices, sensors, external calls, persistence,
Hermes calls, approval creation, mission creation, and task creation remain disabled.

## What It Does Not Allow

Phase S does not:

- activate a camera, microphone, screen capture, or any sensor;
- connect smart glasses, robots, drones, actuators, vehicles, or other physical devices;
- send physical commands, move devices, modify an environment, or run physical automation;
- render a real AR overlay or act on overlay content;
- perform surveillance or always-on monitoring;
- impersonate a person or create identity artifacts;
- perform illegal actions or treat implicit permission as authorization;
- execute a simulation, production decision, mission, task, tool, agent, or Hermes runtime;
- call `ApprovalGateway.create_request`;
- read `.env`, secrets, private keys, credentials, or external sources;
- make network calls, shell calls, package-manager calls, or persistent writes;
- provide WebSocket or dangerous activation routes.

## Safety Policy

`GET /future-moonshot/policy` returns the default-deny `MoonshotSafetyPolicy`. It requires:

- legal review and safety review;
- a controlled environment;
- an immediate stop mechanism;
- audit and rollback;
- no physical action, robotics, drones, smart glasses, AR, sensors, surveillance, impersonation,
  illegal actions, or implicit permissions by default;
- strong approval for physical, legal, identity, money, and safety risk.

Strong approval is a preview requirement only. Phase S never creates or grants an approval.

## Safe API

Read-only status and policy:

- `GET /future-moonshot/status`
- `GET /future-moonshot/policy`

Pure prepare-only previews:

- `POST /future-moonshot/capability-preview`
- `POST /future-moonshot/smart-glasses-preview`
- `POST /future-moonshot/ar-overlay-preview`
- `POST /future-moonshot/robotics-drone-safety-review`
- `POST /future-moonshot/deep-simulation-preview`
- `POST /future-moonshot/physical-automation-preview`
- `POST /future-moonshot/legal-safety-review`
- `POST /future-moonshot/controlled-environment-preview`
- `POST /future-moonshot/immediate-stop-preview`
- `POST /future-moonshot/audit-rollback-preview`
- `POST /future-moonshot/monetization-advantage-review`
- `POST /future-moonshot/identity-impersonation-guard`
- `POST /future-moonshot/approval-requirements`

No device-connect, sensor-start, robot/drone-control, command, render, surveillance, impersonation,
execute, socket, or WebSocket endpoint exists.

## Examples

Capability review:

```json
POST /future-moonshot/capability-preview
{
  "capability_name": "Controlled warehouse robot concept",
  "capability_type": "robotics",
  "concept_summary": "Evaluate repetitive inventory movement in an isolated test area",
  "intended_value": "Reduce repetitive work",
  "safety_risk": "high",
  "legal_risk": "medium"
}
```

The response keeps the concept description but forces:

```json
{
  "prepare_only": true,
  "would_execute": false,
  "would_connect_device": false,
  "would_modify_physical_world": false,
  "approval_required": true,
  "strong_approval_required": true
}
```

Approval preview:

```json
POST /future-moonshot/approval-requirements
{
  "physical_requested": true,
  "camera_requested": true
}
```

Response:

```json
{
  "prepare_only": true,
  "approval_required": true,
  "strong_approval_required": true,
  "approval_gateway_called": false,
  "approval_created": false,
  "approval_granted": false,
  "approval_rejected": false,
  "action_authorized": false,
  "device_authorized": false
}
```

## Capability Reviews

### Smart Glasses Deeper Integration Preview

The preview records a device label, integration goal, proposed data inputs and output modes, and
always-on, user-privacy, and bystander-privacy risks. It requires a visible indicator, immediate
stop, and strong approval. It never connects glasses or activates camera or microphone.

### AR Overlay Preview

The preview records an overlay concept, display context, proposed data sources, distraction risk,
safety risk, and physical-world dependency. It never renders, captures a screen, uses a camera, or
acts on overlay content.

### Robotics and Drones Safety Review

The review requires human supervision, controlled environment, emergency stop, legal review, and
strong approval. Drones and vehicles additionally require a geofence preview. Unsafe or illegal
uses are prohibited. No device connection, command, movement, or control occurs.

### Deep Simulation Preview

The preview captures assumptions, limits, and failure modes. It explicitly prohibits real-world
action and production decisions without review. It does not run a simulation or execute a real
action.

### Physical-World Automation Preview

The preview records intended action, target environment, physical and legal risk, safety controls,
stop plan, and rollback plan. It requires a controlled environment and strong approval. It cannot
control devices, send commands, or modify an environment.

## Required Control Reviews

### Legal and Safety Review

This preview collects questions and required evidence. It remains blocked until review, treats the
jurisdiction as unknown unless explicitly provided, and never claims a legal conclusion or safety
clearance without evidence.

### Controlled Environment

This preview describes isolation, allowed and blocked capabilities, supervision, emergency stop,
audit, and rollback. It does not start an environment or execute anything.

### Immediate Stop

This preview describes scope, triggers, manual stop, and possible automatic-stop conditions. It
does not register a real hook or stop a real device. A stop plan is required before any future
activation proposal.

### Audit and Rollback

This preview lists proposed audit events, evidence, and rollback steps. It does not write an audit,
persist state, or roll back a real system.

## Monetization Advantage Review

Moonshot monetization counts only when evidence supports practical value, revenue, or efficiency.
The review prohibits fake ROI and rejects a high-spectacle concept when no practical value or
revenue/efficiency path is provided. Novelty alone is not an advantage.

## Identity and Impersonation Guard

The guard requires consent, identifies identity and impersonation risk, and lists prohibited
impersonation actions. It never impersonates anyone or creates an identity artifact. Identity risk
requires strong approval, but strong approval still would not make prohibited impersonation valid.

## Integration Boundaries

- **Ambient Vision:** supplies privacy and visible-stop precedent; Phase S does not activate vision.
- **Multi-device Runtime:** supplies device-boundary precedent; Phase S does not pair or connect.
- **Personal OS:** supplies explicit consent and no-implicit-permission boundaries.
- **Advanced Personalization:** user context may inform a concept but never authorizes action.
- **Sandbox Execution:** supplies controlled-environment planning precedent; Phase S does not run a
  sandbox.
- **Command Center / Operator Console:** expose prepare-only status, policy, and readiness markers;
  they do not enable sensors, AR, devices, robotics, drones, or physical automation.

Any future activation proposal is outside Phase S and would require a separate reviewed design,
legal and safety evidence, explicit authorization, strong approval, controlled testing, immediate
stop, audit, and rollback. Dangerous, surveillant, impersonating, illegal, or implicitly permitted
automation remains prohibited.
