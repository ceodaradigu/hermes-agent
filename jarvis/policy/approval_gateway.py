from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional
from uuid import uuid4


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class ApprovalRequest:
    request_id: str
    action: str
    rationale: str
    requested_at: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_at: Optional[str] = None
    decision_note: Optional[str] = None


class ApprovalGateway:
    def __init__(self):
        self._requests: Dict[str, ApprovalRequest] = {}

    def create_request(self, action: str, rationale: str = "") -> ApprovalRequest:
        action_normalized = (action or "").strip()
        if not action_normalized:
            raise ValueError("action must be a non-empty string")

        request_id = str(uuid4())
        req = ApprovalRequest(
            request_id=request_id,
            action=action_normalized,
            rationale=rationale,
            requested_at=self._now_iso(),
        )
        self._requests[request_id] = req
        return req

    def approve(self, request_id: str, note: str = "") -> ApprovalRequest:
        req = self._get_existing(request_id)
        self._ensure_pending(req)
        req.status = ApprovalStatus.APPROVED
        req.decided_at = self._now_iso()
        req.decision_note = note
        return req

    def reject(self, request_id: str, note: str = "") -> ApprovalRequest:
        req = self._get_existing(request_id)
        self._ensure_pending(req)
        req.status = ApprovalStatus.REJECTED
        req.decided_at = self._now_iso()
        req.decision_note = note
        return req

    def get_status(self, request_id: str) -> ApprovalStatus:
        return self._get_existing(request_id).status

    def get_request(self, request_id: str) -> ApprovalRequest:
        return self._get_existing(request_id)

    def list_requests(self) -> list[ApprovalRequest]:
        return list(self._requests.values())

    def _get_existing(self, request_id: str) -> ApprovalRequest:
        if request_id not in self._requests:
            raise KeyError(f"Approval request not found: {request_id}")
        return self._requests[request_id]

    @staticmethod
    def _ensure_pending(req: ApprovalRequest) -> None:
        if req.status != ApprovalStatus.PENDING:
            raise ValueError(f"request {req.request_id} is already {req.status.value}")

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
