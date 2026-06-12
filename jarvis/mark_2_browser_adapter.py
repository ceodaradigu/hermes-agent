from __future__ import annotations

from typing import Any, Dict
from urllib.parse import urlparse


class BrowserToolAdapter:
    def preview_open_url(self, url: str, **values: Any) -> Dict[str, Any]:
        return self._preview("open_url", url, **values)

    def preview_click(self, url: str, **values: Any) -> Dict[str, Any]:
        return self._preview("click", url, **values)

    def preview_fill_form(self, url: str, **values: Any) -> Dict[str, Any]:
        return self._preview("fill_form", url, **values)

    def preview_submit_form(self, url: str, **values: Any) -> Dict[str, Any]:
        return self._preview("submit_form", url, **values)

    def preview_download(self, url: str, **values: Any) -> Dict[str, Any]:
        return self._preview("download", url, **values)

    def candidate_browser_action(self, operation: str, url: str, **values: Any) -> Dict[str, Any]:
        return self._preview(operation, url, **values)

    def _preview(self, operation: str, url: str, **values: Any) -> Dict[str, Any]:
        text = f"{operation} {url} {values}".lower()
        mutation = operation in {"click", "fill_form", "submit_form"}
        credentials = bool(values.get("credentials_required") or "login" in text)
        pii = bool(values.get("user_data_risk") or any(item in text for item in ("pii", "personal", "card")))
        payment = any(item in text for item in ("payment", "purchase", "checkout", "card", "pay"))
        return {
            "adapter_name": "browser",
            "url": url,
            "domain": urlparse(url).hostname or "",
            "operation": operation,
            "browser_required": True,
            "network_required": True,
            "external_mutation": mutation,
            "credentials_required": credentials,
            "user_data_risk": "critical" if payment else "high" if pii else "low",
            "approval_required": mutation,
            "strong_approval_required": credentials or pii or payment,
            "double_confirmation_required": payment,
            "triple_confirmation_required": payment,
            "blocked_by_default": True,
            "would_launch_browser": False,
            "would_submit_data": False,
            "eligible_after_valid_approval": True,
            "rollback_or_stop_plan": str(values.get("rollback_or_stop_plan") or "close browser before submission"),
            "blocked_reasons": ["browser real launch disabled", "network disabled"],
        }
