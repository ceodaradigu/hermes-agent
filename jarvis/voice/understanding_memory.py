from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from jarvis.voice.understanding_feedback import UserUnderstandingAppliedFeedbackRule


class UserUnderstandingMemoryStatus(str, Enum):
    PROPOSED = "proposed"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    ACTIVE = "active"
    DISABLED = "disabled"
    DELETED = "deleted"
    EXPIRED = "expired"


SENSITIVE_MEMORY_TERMS = (
    ".env",
    "password",
    "token",
    "credenciales",
    "banco",
    "tarjeta",
)


@dataclass
class UserUnderstandingMemoryProposal:
    id: str
    type: str
    source: str
    alias: str | None
    target_intent: str
    confidence: str
    scope: str
    approved_by: str | None
    created_at: str
    expires_at: str | None
    sensitive: bool
    status: UserUnderstandingMemoryStatus = UserUnderstandingMemoryStatus.PROPOSED
    active: bool = False
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "alias": self.alias,
            "target_intent": self.target_intent,
            "confidence": self.confidence,
            "scope": self.scope,
            "approved_by": self.approved_by,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "sensitive": self.sensitive,
            "status": self.status.value,
            "active": self.active,
            "reason": self.reason,
            "evidence": dict(self.evidence),
            "audit": [dict(event) for event in self.audit],
        }

    def to_dict(self) -> dict[str, Any]:
        return self.as_dict()


class UserUnderstandingMemoryProposalStore:
    """In-memory proposal store for future User Understanding memory.

    This store intentionally does not persist, read files, connect to runtime,
    update the intent router, create tasks, or execute missions.
    """

    def __init__(self) -> None:
        self._proposals: dict[str, UserUnderstandingMemoryProposal] = {}

    def propose_from_feedback_rule(
        self,
        rule: UserUnderstandingAppliedFeedbackRule,
    ) -> UserUnderstandingMemoryProposal:
        now = self._now()
        evidence = {
            "original_text": rule.original_text,
            "suggested_alias": rule.suggested_alias,
            "corrected_intent": rule.corrected_intent,
            "rule_source": rule.source,
            "rule_applied_persistently": rule.applied_persistently,
        }
        alias = rule.suggested_alias or self._normalize(rule.original_text) or None
        proposal = UserUnderstandingMemoryProposal(
            id=f"ump_{uuid4().hex}",
            type="intent_alias",
            source=rule.source,
            alias=alias,
            target_intent=rule.corrected_intent,
            confidence="reviewed",
            scope="voice_runtime",
            approved_by=None,
            created_at=now,
            expires_at=None,
            sensitive=self._contains_sensitive_terms(alias, evidence),
            status=UserUnderstandingMemoryStatus.PROPOSED,
            active=False,
            reason=rule.reason,
            evidence=evidence,
            audit=[
                {
                    "at": now,
                    "event": UserUnderstandingMemoryStatus.PROPOSED.value,
                    "source": rule.source,
                }
            ],
        )
        self._proposals[proposal.id] = proposal
        return proposal

    def list_proposals(self) -> list[UserUnderstandingMemoryProposal]:
        return list(self._proposals.values())

    def get_proposal(self, proposal_id: str) -> UserUnderstandingMemoryProposal:
        return self._require(proposal_id)

    def mark_reviewed(self, proposal_id: str) -> UserUnderstandingMemoryProposal:
        proposal = self._require(proposal_id)
        proposal.status = UserUnderstandingMemoryStatus.REVIEWED
        proposal.active = False
        self._audit(proposal, "reviewed")
        return proposal

    def approve(
        self,
        proposal_id: str,
        approved_by: str = "David",
    ) -> UserUnderstandingMemoryProposal:
        proposal = self._require(proposal_id)
        if proposal.sensitive:
            proposal.active = False
            proposal.reason = (
                "Sensitive memory proposals require explicit future policy "
                "and cannot be approved by this in-memory proposal store."
            )
            self._audit(proposal, "approval_rejected_sensitive", by=approved_by)
            raise ValueError("Sensitive memory proposals cannot be approved automatically.")

        proposal.status = UserUnderstandingMemoryStatus.APPROVED
        proposal.active = True
        proposal.approved_by = approved_by
        self._audit(proposal, "approved", by=approved_by)
        return proposal

    def disable(self, proposal_id: str, reason: str = "") -> UserUnderstandingMemoryProposal:
        proposal = self._require(proposal_id)
        proposal.status = UserUnderstandingMemoryStatus.DISABLED
        proposal.active = False
        if reason:
            proposal.reason = reason
        self._audit(proposal, "disabled", reason=reason)
        return proposal

    def delete(self, proposal_id: str, reason: str = "") -> UserUnderstandingMemoryProposal:
        proposal = self._require(proposal_id)
        proposal.status = UserUnderstandingMemoryStatus.DELETED
        proposal.active = False
        if reason:
            proposal.reason = reason
        self._audit(proposal, "deleted", reason=reason)
        return proposal

    def count(self) -> int:
        return len(self._proposals)

    def clear(self) -> None:
        self._proposals.clear()

    def _require(self, proposal_id: str) -> UserUnderstandingMemoryProposal:
        try:
            return self._proposals[proposal_id]
        except KeyError as exc:
            raise KeyError(f"Unknown memory proposal id: {proposal_id}") from exc

    def _audit(self, proposal: UserUnderstandingMemoryProposal, event: str, **extra: Any) -> None:
        entry = {"at": self._now(), "event": event}
        entry.update({key: value for key, value in extra.items() if value})
        proposal.audit.append(entry)

    @staticmethod
    def _contains_sensitive_terms(alias: str | None, evidence: dict[str, Any]) -> bool:
        text = " ".join(
            str(value)
            for value in (alias, *evidence.values())
            if value is not None
        ).lower()
        return any(term in text for term in SENSITIVE_MEMORY_TERMS)

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.strip().lower().split())

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
