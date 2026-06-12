from __future__ import annotations

from typing import Any, Dict, Iterable


DANGEROUS_ROUTE_PATTERNS = (
    "deploy-real", "stripe-live", "pay", "charge", "send-email", "modify-dns",
    "start-codex-real", "start-claude-real", "use-session-token", "steal-token",
    "use-cookies", "auto-approve", "approve-all", "bypass-approval", "execute-free",
    "run-any", "read-env", "expose-access-material", "push", "merge", "production-deploy",
)


class Mark2DangerousRouteAudit:
    def audit(self, registered_routes: Iterable[str] = ()) -> Dict[str, Any]:
        routes = sorted(route for route in set(registered_routes) if route.startswith("/mark-2/"))
        dangerous = sorted(route for route in routes if any(pattern in route.lower() for pattern in DANGEROUS_ROUTE_PATTERNS))
        return {
            "dangerous_routes_checked": list(DANGEROUS_ROUTE_PATTERNS),
            "dangerous_routes_registered": dangerous,
            "blocked_or_absent": not dangerous,
            "passed": not dangerous,
            "findings": [] if not dangerous else [f"dangerous route registered: {route}" for route in dangerous],
            "read_only_audit": True,
            "would_execute": False,
        }
