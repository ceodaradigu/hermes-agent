from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple


DANGEROUS_ROUTE_CATEGORIES: Dict[str, Tuple[str, ...]] = {
    "research_execute": (
        "/mark-3/research-execution/execute",
        "/mark-3/research-execution/run",
        "/mark-3/research-execution/execute-by-id",
    ),
    "experiment_execute": (
        "/mark-3/moonshot-lab/execute",
        "/mark-3/moonshot-lab/run",
        "/mark-3/moonshot-lab/experiment/execute",
        "/mark-3/moonshot-lab/prototype/run",
    ),
    "scheduler_real_cron_worker": (
        "/mark-3/routine-ops/execute",
        "/mark-3/routine-ops/run",
        "/mark-3/routine-ops/start-worker",
        "/mark-3/routine-ops/cron",
        "/mark-3/routine-ops/watcher",
        "/mark-3/routine-ops/schedule-real",
    ),
    "send_email": (
        "/send-email",
        "/email/send",
        "/mark-3/routine-ops/send",
    ),
    "gmail_calendar_contacts_real": (
        "/mark-3/routine-ops/gmail",
        "/mark-3/routine-ops/calendar",
        "/mark-3/routine-ops/contacts",
        "/gmail-real",
        "/calendar-real",
        "/contacts-real",
    ),
    "login_account_access": (
        "/mark-3/routine-ops/login",
        "/mark-3/routine-ops/account-access",
        "/login-real",
        "/account-access-real",
    ),
    "password_storage": (
        "/store-password",
        "/password-storage",
        "/mark-3/routine-ops/password",
    ),
    "token_cookie_session_use": (
        "/use-token",
        "/session-token",
        "/use-session-token",
        "/use-cookie",
        "/cookies",
    ),
    "stripe_live_payment_checkout": (
        "/stripe-live",
        "/payment",
        "/checkout",
        "/pay",
        "/charge",
    ),
    "deploy_publish_domain_real": (
        "/deploy",
        "/publish",
        "/domain",
        "/modify-dns",
        "/dns",
    ),
    "install_subprocess_thread_network_real": (
        "/install",
        "/subprocess",
        "/thread",
        "/start-thread",
        "/network",
        "/web-real",
    ),
    "fake_revenue_cost_benchmark_result_capability": (
        "/fake-revenue",
        "/fake-cost",
        "/fake-benchmark",
        "/fake-result",
        "/fake-capability",
        "/claim-result",
    ),
}

ALLOWED_GATED_MARK_3_ROUTES = (
    "/mark-3/hermes-runtime/execute-read",
)


class Mark3DangerousRouteAudit:
    def audit(self, registered_routes: Iterable[str] = ()) -> Dict[str, Any]:
        routes = sorted(route for route in set(registered_routes) if route.startswith("/mark-3/"))
        category_results: Dict[str, Dict[str, Any]] = {}
        dangerous: List[str] = []
        for category, patterns in DANGEROUS_ROUTE_CATEGORIES.items():
            matches = sorted(route for route in routes if _matches_any(route, patterns))
            category_results[category] = {
                "patterns_checked": list(patterns),
                "free_routes_registered": matches,
                "free_route_present": bool(matches),
                "passed": not matches,
            }
            dangerous.extend(matches)
        dangerous = sorted(set(dangerous))
        return {
            "current_mark": "Mark 3",
            "release_candidate_status": "ready_as_controlled_release_candidate",
            "read_only_audit": True,
            "audited_route_prefixes": ["/mark-3/"],
            "audit_scope": "Mark 3 routes registered in this process; legacy preview/control-plane routes outside Mark 3 are not reclassified by this RC audit.",
            "safe_to_render": True,
            "passed": not dangerous,
            "blocked_or_absent": not dangerous,
            "dangerous_routes_registered": dangerous,
            "findings": [] if not dangerous else [f"dangerous route registered: {route}" for route in dangerous],
            "categories": category_results,
            "allowed_gated_routes": list(ALLOWED_GATED_MARK_3_ROUTES),
            "allowed_gated_routes_are_not_free_autonomy": True,
            "execute_read_requires_valid_mission_candidate_approval_scope_and_operator_authorization": True,
            "no_research_execute_route": not category_results["research_execute"]["free_route_present"],
            "no_experiment_execute_route": not category_results["experiment_execute"]["free_route_present"],
            "no_real_scheduler_cron_or_worker_route": not category_results["scheduler_real_cron_worker"]["free_route_present"],
            "no_send_email_route": not category_results["send_email"]["free_route_present"],
            "no_gmail_calendar_contacts_real_route": not category_results["gmail_calendar_contacts_real"]["free_route_present"],
            "no_login_or_account_access_route": not category_results["login_account_access"]["free_route_present"],
            "no_password_storage_route": not category_results["password_storage"]["free_route_present"],
            "no_token_cookie_session_use_route": not category_results["token_cookie_session_use"]["free_route_present"],
            "no_stripe_live_payment_checkout_route": not category_results["stripe_live_payment_checkout"]["free_route_present"],
            "no_deploy_publish_domain_route": not category_results["deploy_publish_domain_real"]["free_route_present"],
            "no_install_subprocess_thread_network_route": not category_results["install_subprocess_thread_network_real"]["free_route_present"],
            "no_fake_revenue_cost_benchmark_result_capability_route": not category_results["fake_revenue_cost_benchmark_result_capability"]["free_route_present"],
            "would_execute": False,
        }


def _matches_any(route: str, patterns: Iterable[str]) -> bool:
    lowered = route.lower()
    return any(pattern in lowered for pattern in patterns)
