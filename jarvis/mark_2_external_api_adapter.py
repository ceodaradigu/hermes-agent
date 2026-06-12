from __future__ import annotations

from typing import Any, Dict
from urllib.parse import urlparse

from jarvis.approval_audit import redact_sensitive_data


class ExternalAPIToolAdapter:
    def preview_get_request(self, endpoint: str, **values: Any) -> Dict[str, Any]:
        return self._preview("GET", endpoint, **values)

    def preview_post_request(self, endpoint: str, **values: Any) -> Dict[str, Any]:
        return self._preview("POST", endpoint, **values)

    def preview_webhook_call(self, endpoint: str, **values: Any) -> Dict[str, Any]:
        return self._preview("POST", endpoint, webhook=True, **values)

    def candidate_api_call(self, method: str, endpoint: str, **values: Any) -> Dict[str, Any]:
        return self._preview(method, endpoint, **values)

    def _preview(self, method: str, endpoint: str, **values: Any) -> Dict[str, Any]:
        method = str(method or "GET").upper()
        payload = dict(values.get("payload") or {})
        safe_payload, redacted = redact_sensitive_data(payload)
        mutation = method in {"POST", "PUT", "PATCH", "DELETE"} or bool(values.get("webhook"))
        text = f"{endpoint} {payload}".lower()
        critical = any(item in text for item in ("payment", "charge", "production", "stripe"))
        credentials = bool(values.get("credentials_required"))
        return {
            "adapter_name": "external_api",
            "method": method,
            "endpoint": endpoint,
            "domain": urlparse(endpoint).hostname or "",
            "network_required": True,
            "credentials_required": credentials,
            "payload_summary": safe_payload,
            "sensitive_payload_detected": bool(redacted) or safe_payload != payload,
            "external_mutation": mutation,
            "approval_required": mutation,
            "strong_approval_required": credentials or critical,
            "double_confirmation_required": critical,
            "triple_confirmation_required": "payment" in text or "charge" in text,
            "blocked_by_default": True,
            "would_call_external_api": False,
            "eligible_after_valid_approval": True,
            "rollback_or_stop_plan": str(values.get("rollback_or_stop_plan") or "stop before external call"),
            "blocked_reasons": ["external API real calls disabled", "network disabled"],
        }
