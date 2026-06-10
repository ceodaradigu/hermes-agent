# JARVIS Phase R: Advanced Personalization / User Model

Phase R provides a privacy-first, prepare-only foundation for explicit personalization. It can build reviewable previews of preferences, communication style, decision patterns, business goals, contrarian mode, memory proposals, lifecycle operations, uncertainty, recommendations, sensitive-inference guards, and approval requirements.

It does not learn, store, activate, deactivate, reverse, delete, or modify real memory. It does not read private sources, infer sensitive attributes, manipulate the user, invent private certainty, call Hermes, create approvals, create missions/tasks, execute actions, access secrets, persist state, or make external calls. Memory may inform a future recommendation after explicit review; it is never permission and never authorizes an action.

## Safety Contract

- Every DTO and endpoint is `prepare_only=true`.
- Opaque learning and automatic memory are disabled.
- Memory proposals require explicit review and approval.
- Sensitive memory, private sources, cross-context personalization, and actions based on personalization require strong approval.
- Proposed memory must be reversible and auditable.
- Low or unknown confidence requires asking the user before treating a claim as fact.
- Sensitive inference is blocked even when requested as preview input.
- Business-goal previews preserve hypotheses and never invent ROI or confirmed revenue.
- Contrarian mode permits respectful challenge, never humiliation or manipulation.
- Deserialization cannot enable memory writes, activation/deactivation, inference, execution, persistence, Hermes, ApprovalGateway, network, or secrets access.

## API

Read-only foundation status:

- `GET /personalization/status`
- `GET /personalization/policy`

Pure local previews:

- `POST /personalization/preference-profile`
- `POST /personalization/speech-style`
- `POST /personalization/decision-model`
- `POST /personalization/business-goal`
- `POST /personalization/contrarian-mode`
- `POST /personalization/memory-proposal`
- `POST /personalization/memory-review`
- `POST /personalization/memory-lifecycle`
- `POST /personalization/memory-audit-reversal`
- `POST /personalization/uncertainty`
- `POST /personalization/recommendation`
- `POST /personalization/sensitive-inference-guard`
- `POST /personalization/approval-requirements`

No save, activate, deactivate, delete, learn, auto-learn, action-authorization, sensitive-inference, private-source, or WebSocket route exists.

## Examples

Preference preview:

```json
POST /personalization/preference-profile
{
  "preference_name": "Concise answers",
  "preference_type": "format",
  "evidence_preview": ["Explicitly requested concise output"],
  "confidence": "medium",
  "uncertainty_notes": ["May vary by task"]
}
```

The response preserves the supplied evidence and uncertainty while returning `would_store_memory=false`, `would_activate_memory=false`, and `approval_required=true`.

Memory proposal preview:

```json
POST /personalization/memory-proposal
{
  "proposal_id_preview": "proposal-preview-1",
  "proposed_memory": "Prefer concise output",
  "memory_category": "preference",
  "sensitivity_level": "medium"
}
```

The response returns `reversible=true`, `would_store=false`, `would_activate=false`, `approval_required=true`, and `strong_approval_required=true`. Review, approve, activate, deactivate, audit, and reversal are represented only through previews; none changes memory.

Uncertainty preview:

```json
POST /personalization/uncertainty
{
  "claim_or_preference": "Prefers direct answers",
  "confidence": "low",
  "unknowns": ["Whether this applies to every task"],
  "evidence_needed": ["Explicit confirmation"]
}
```

The response returns `must_ask_user_before_using_as_fact=true`, `no_private_certainty_claim=true`, and `would_store_memory=false`.

Sensitive inference guard:

```json
POST /personalization/sensitive-inference-guard
{
  "input_category": "provided text",
  "sensitive_attribute_risk": "high"
}
```

The response blocks sensitive inference and storage and marks strong approval as required for any future explicitly requested sensitive-memory flow.

## Personalization Surfaces

- Preference profile: tone, workflow, format, project, risk, monetization, and learning preferences.
- Speech/style pattern: response-style observations without identity claims.
- Decision model: explicit tradeoffs, risk tolerance, monetization bias, and respectful contrarian need.
- Business goals: revenue, portfolio, automation, learning, product, and job hypotheses without fake ROI.
- Contrarian mode: bounded, respectful pushback.
- Memory lifecycle: proposal, review, approve, activate, deactivate, reverse, and audit previews only.
- Recommendations: tone, workflow, focus, monetization, product, and learning suggestions without execution or action authorization.

## Integration

Command Center exposes the `advanced_personalization_user_model=prepare_only` marker. Operator Console exposes prepare-only status, safety policy, memory-proposal readiness, and preview capabilities. It does not expose memory-write, activation, inference, approval, or execution controls.

Personal OS may provide future explicitly consented context, but Phase R reads no private sources. Daily Operator may consume future approved preferences for prioritization, but memory cannot authorize scheduled actions. Mission Core and ApprovalGateway remain authoritative for actions and approvals. Voice Understanding memory remains separate and is not read or modified by Phase R. Operator Console only displays safe placeholders.

These previews can improve prioritization, copy, product choices, sales hypotheses, and focus by making preferences and uncertainty explicit. Expected benefits remain hypotheses until supported by reviewed evidence; Phase R never invents ROI or revenue.
