from __future__ import annotations

import json
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


@dataclass
class UserUnderstandingMemorySnapshot:
    version: int
    exported_at: str
    proposals: list[UserUnderstandingMemoryProposal]
    proposal_count: int
    active_count: int
    sensitive_count: int
    source: str = "user_understanding_memory_proposal_store"
    persisted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "exported_at": self.exported_at,
            "source": self.source,
            "persisted": self.persisted,
            "proposal_count": self.proposal_count,
            "active_count": self.active_count,
            "sensitive_count": self.sensitive_count,
            "proposals": [proposal.as_dict() for proposal in self.proposals],
        }

    def to_dict(self) -> dict[str, Any]:
        return self.as_dict()

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "UserUnderstandingMemorySnapshot":
        if not isinstance(payload, dict):
            raise ValueError("Memory snapshot must be a JSON object.")

        proposals_payload = payload.get("proposals")
        if not isinstance(proposals_payload, list):
            raise ValueError("Memory snapshot must include a proposals list.")

        version = payload.get("version")
        exported_at = payload.get("exported_at")
        if isinstance(version, bool) or not isinstance(version, int):
            raise ValueError("Memory snapshot must include an integer version.")
        if not isinstance(exported_at, str) or not exported_at:
            raise ValueError("Memory snapshot must include exported_at.")

        proposals = [
            _proposal_from_dict(proposal_payload)
            for proposal_payload in proposals_payload
        ]
        proposal_count = _coerce_count(
            payload.get("proposal_count", len(proposals)),
            "proposal_count",
        )
        active_count = _coerce_count(
            payload.get("active_count", sum(1 for proposal in proposals if proposal.active)),
            "active_count",
        )
        sensitive_count = _coerce_count(
            payload.get("sensitive_count", sum(1 for proposal in proposals if proposal.sensitive)),
            "sensitive_count",
        )
        source = payload.get("source", "user_understanding_memory_proposal_store")
        persisted = payload.get("persisted", False)
        if not isinstance(source, str) or not source:
            raise ValueError("Memory snapshot source must be a non-empty string.")
        if not isinstance(persisted, bool):
            raise ValueError("Memory snapshot persisted flag must be boolean.")

        if proposal_count != len(proposals):
            raise ValueError("Memory snapshot proposal_count does not match proposals.")
        if active_count != sum(1 for proposal in proposals if proposal.active):
            raise ValueError("Memory snapshot active_count does not match proposals.")
        if sensitive_count != sum(1 for proposal in proposals if proposal.sensitive):
            raise ValueError("Memory snapshot sensitive_count does not match proposals.")

        return cls(
            version=version,
            exported_at=exported_at,
            proposals=proposals,
            proposal_count=proposal_count,
            active_count=active_count,
            sensitive_count=sensitive_count,
            source=source,
            persisted=persisted,
        )

    @classmethod
    def from_json(cls, payload: str) -> "UserUnderstandingMemorySnapshot":
        if not isinstance(payload, str):
            raise ValueError("Memory snapshot JSON must be a string.")
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("Memory snapshot JSON is invalid.") from exc
        return cls.from_dict(data)


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

    def export_snapshot(self) -> UserUnderstandingMemorySnapshot:
        proposals = self.list_proposals()
        return UserUnderstandingMemorySnapshot(
            version=1,
            exported_at=self._now(),
            proposals=proposals,
            proposal_count=len(proposals),
            active_count=sum(1 for proposal in proposals if proposal.active),
            sensitive_count=sum(1 for proposal in proposals if proposal.sensitive),
            persisted=False,
        )

    def export_snapshot_json(self, indent: int = 2) -> str:
        return self.export_snapshot().to_json(indent=indent)

    def import_snapshot(
        self,
        snapshot: UserUnderstandingMemorySnapshot | dict[str, Any] | str,
        replace: bool = False,
    ) -> int:
        parsed_snapshot = self._parse_snapshot(snapshot)
        if parsed_snapshot.persisted:
            raise ValueError(
                "Persisted memory snapshots are not accepted by the in-memory proposal import."
            )

        imported: dict[str, UserUnderstandingMemoryProposal] = {}
        for proposal in parsed_snapshot.proposals:
            if proposal.sensitive and (
                proposal.active
                or proposal.status
                in {
                    UserUnderstandingMemoryStatus.APPROVED,
                    UserUnderstandingMemoryStatus.ACTIVE,
                }
            ):
                raise ValueError(
                    "Sensitive memory proposals cannot be imported as approved or active."
                )
            imported[proposal.id] = proposal

        if replace:
            self.clear()
        self._proposals.update(imported)
        return len(imported)

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

    @staticmethod
    def _parse_snapshot(
        snapshot: UserUnderstandingMemorySnapshot | dict[str, Any] | str,
    ) -> UserUnderstandingMemorySnapshot:
        if isinstance(snapshot, UserUnderstandingMemorySnapshot):
            return snapshot
        if isinstance(snapshot, str):
            return UserUnderstandingMemorySnapshot.from_json(snapshot)
        if isinstance(snapshot, dict):
            return UserUnderstandingMemorySnapshot.from_dict(snapshot)
        raise ValueError("Memory snapshot must be a snapshot object, dict, or JSON string.")


def _coerce_count(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Memory snapshot {field_name} must be a non-negative integer.")
    return value


def _proposal_from_dict(payload: Any) -> UserUnderstandingMemoryProposal:
    if not isinstance(payload, dict):
        raise ValueError("Memory snapshot proposals must be JSON objects.")

    required_fields = {
        "id": str,
        "type": str,
        "source": str,
        "target_intent": str,
        "confidence": str,
        "scope": str,
        "created_at": str,
        "sensitive": bool,
        "active": bool,
    }
    for field_name, field_type in required_fields.items():
        value = payload.get(field_name)
        if not isinstance(value, field_type):
            raise ValueError(f"Memory proposal {field_name} is required.")

    status_value = payload.get("status", UserUnderstandingMemoryStatus.PROPOSED.value)
    try:
        status = UserUnderstandingMemoryStatus(status_value)
    except ValueError as exc:
        raise ValueError(f"Unknown memory proposal status: {status_value}") from exc

    alias = payload.get("alias")
    approved_by = payload.get("approved_by")
    expires_at = payload.get("expires_at")
    reason = payload.get("reason", "")
    evidence = payload.get("evidence", {})
    audit = payload.get("audit", [])
    if alias is not None and not isinstance(alias, str):
        raise ValueError("Memory proposal alias must be a string or null.")
    if approved_by is not None and not isinstance(approved_by, str):
        raise ValueError("Memory proposal approved_by must be a string or null.")
    if expires_at is not None and not isinstance(expires_at, str):
        raise ValueError("Memory proposal expires_at must be a string or null.")
    if not isinstance(reason, str):
        raise ValueError("Memory proposal reason must be a string.")
    if not isinstance(evidence, dict):
        raise ValueError("Memory proposal evidence must be an object.")
    if not isinstance(audit, list) or not all(isinstance(event, dict) for event in audit):
        raise ValueError("Memory proposal audit must be a list of objects.")

    return UserUnderstandingMemoryProposal(
        id=payload["id"],
        type=payload["type"],
        source=payload["source"],
        alias=alias,
        target_intent=payload["target_intent"],
        confidence=payload["confidence"],
        scope=payload["scope"],
        approved_by=approved_by,
        created_at=payload["created_at"],
        expires_at=expires_at,
        sensitive=payload["sensitive"],
        status=status,
        active=payload["active"],
        reason=reason,
        evidence=dict(evidence),
        audit=[dict(event) for event in audit],
    )
