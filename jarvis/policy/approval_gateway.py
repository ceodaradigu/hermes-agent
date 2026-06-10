from __future__ import annotations

from typing import Any, Dict, Optional

from jarvis.approval_hardening import (
    ApprovalHardeningService,
    ApprovalKind,
    ApprovalRequest,
    ApprovalStatus,
)


class ApprovalGateway:
    def __init__(self):
        self._service = ApprovalHardeningService()

    def create_request(
        self,
        action: str,
        rationale: str = "",
        *,
        requested_by: str = "jarvis",
        context: Optional[Dict[str, Any]] = None,
        approval_kind: ApprovalKind | str = ApprovalKind.NORMAL,
        expires_in_seconds: int = 900,
        expires_at: Optional[str] = None,
    ) -> ApprovalRequest:
        action_normalized = (action or "").strip()
        if not action_normalized:
            raise ValueError("action must be a non-empty string")
        return self._service.request(
            action_type=action_normalized,
            requested_by=requested_by,
            reason=rationale,
            context=context,
            approval_kind=approval_kind,
            expires_in_seconds=expires_in_seconds,
            expires_at=expires_at,
        )

    def approve(self, request_id: str, note: str = "", confirmation_phrase: Optional[str] = None) -> ApprovalRequest:
        return self._service.decide(
            request_id,
            "approved",
            reason=note,
            confirmation_phrase=confirmation_phrase,
        )

    def reject(self, request_id: str, note: str = "") -> ApprovalRequest:
        return self._service.decide(request_id, "rejected", reason=note)

    def revoke(self, request_id: str, note: str = "") -> ApprovalRequest:
        return self._service.revoke(request_id, reason=note)

    def get_status(self, request_id: str) -> ApprovalStatus:
        req = self._get_existing(request_id)
        return self._service.refresh_expiration(req).status

    def get_request(self, request_id: str) -> ApprovalRequest:
        return self._get_existing(request_id)

    def list_requests(self) -> list[ApprovalRequest]:
        return self._service.list_records()

    def _get_existing(self, request_id: str) -> ApprovalRequest:
        return self._service.get(request_id)
