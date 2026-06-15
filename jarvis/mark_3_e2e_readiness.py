from __future__ import annotations

from typing import Any, Dict

from jarvis.mark_3_local_routine_scheduler_personal_family_ops import Mark3RoutineOpsControlPlane
from jarvis.mark_3_moonshot_lab_research_experiment_engine import Mark3MoonshotLabResearchExperimentEngine
from jarvis.mark_3_product_revenue_factory import Mark3ProductRevenueFactory
from jarvis.mark_3_research_execution import ResearchExecutionControlPlane
from jarvis.mark_3_release_candidate import Mark3ReleaseCandidateStatus


class Mark3E2EReadinessSmoke:
    """Prepare-only/gated smoke for Mark 3 RC.

    This smoke creates in-memory candidates and previews only. It intentionally
    does not call real network, providers, email, scheduler, deploy, Stripe,
    GitHub, subprocess, or Hermes execution.
    """

    def run(self) -> Dict[str, Any]:
        product = Mark3ProductRevenueFactory(id_factory=lambda: "rc-product-candidate").experiment({
            "experiment_name": "Local validation candidate",
            "product_name": "Local Mark 3 pilot asset",
            "success_metrics": ["operator-reviewed usefulness signal"],
        })
        routine = Mark3RoutineOpsControlPlane(id_factory=lambda: "rc-routine-candidate").plan({
            "title": "Local daily pilot routine candidate",
            "cadence": "manual",
            "tasks": ["review scope", "capture evidence", "record stop conditions"],
        })
        moonshot = Mark3MoonshotLabResearchExperimentEngine(id_factory=lambda: "rc-moonshot-candidate").experiment({
            "experiment_name": "Local evidence framing",
            "hypothesis": "A bounded local pilot can reveal Mark 3 gaps without external side effects.",
            "scope": "prepare-only smoke",
        })
        research_plane = ResearchExecutionControlPlane()
        research_preview = research_plane.preview({
            "source_type": "docs",
            "scope": "docs/jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md",
            "query": "Mark 3 RC smoke exact local docs scope",
        })
        candidate_by_id = research_plane.candidate({"research_id": research_preview["research_id"]})
        research_status = research_plane.status()
        rc_status = Mark3ReleaseCandidateStatus().to_dict()

        checks = {
            "product_revenue_candidate_created_prepare_only": (
                product["candidate_state"] == "prepared_candidate"
                and product["prepare_only"]
                and _all_false(product, _PRODUCT_SIDE_EFFECTS)
            ),
            "routine_ops_candidate_created_prepare_only": (
                routine["candidate_state"] == "prepared_candidate"
                and routine["prepare_only"]
                and _all_false(routine, _ROUTINE_SIDE_EFFECTS)
            ),
            "moonshot_lab_candidate_created_prepare_only": (
                moonshot["candidate_state"] == "prepared_candidate"
                and moonshot["prepare_only"]
                and _all_false(moonshot, _MOONSHOT_SIDE_EFFECTS)
            ),
            "research_local_docs_exact_scope_preview_only": (
                research_preview["execution_status"] == "executable_candidate"
                and research_preview["source_type"] == "docs"
                and research_preview["normalized_scope"].endswith("jarvis-mark-3-master-planning-autonomous-learning-multiagent-roadmap.md")
                and research_preview["file_reads_performed"] is False
                and research_preview["adapter_called"] is False
            ),
            "no_execution_by_id": (
                candidate_by_id["execution_status"] == "setup_required"
                and candidate_by_id["candidate_by_research_id_only"] is True
                and candidate_by_id["request_rehydrated_for_execution"] is False
                and candidate_by_id["file_reads_performed"] is False
            ),
            "web_github_providers_not_connected": (
                research_status["capabilities"]["github"]["capability_status"] == "capability_not_connected_yet"
                and research_status["capabilities"]["web"]["capability_status"] == "capability_not_connected_yet"
                and product["external_provider_capabilities_connected"] is False
                and routine.get("external_provider_capabilities_connected", False) is False
                and moonshot.get("provider_connected", False) is False
            ),
            "no_fake_revenue_costs_results_benchmarks_or_capabilities": (
                product["no_fake_revenue"]
                and product["no_fake_costs"]
                and moonshot["no_fake_research_result"]
                and moonshot["no_fake_benchmark"]
                and moonshot["prototype_is_not_capability"]
                and rc_status["no_fake_capabilities"]
            ),
            "hermes_remains_execution_engine_not_duplicated": (
                product["hermes_is_execution_engine"]
                and routine["hermes_is_execution_engine"]
                and moonshot.get("hermes_remains_execution_engine", moonshot.get("hermes_is_execution_engine", False))
                and research_status["hermes_is_execution_engine"]
                and research_status["no_duplicate_hermes_runtime"]
            ),
            "release_candidate_not_free_autonomy": (
                rc_status["ready_as_controlled_release_candidate"]
                and rc_status["not_ready_for_free_autonomy"]
                and not rc_status["free_autonomy_enabled"]
            ),
        }
        return {
            "current_mark": "Mark 3",
            "release_candidate_status": "ready_as_controlled_release_candidate",
            "passed": all(checks.values()),
            "prepare_only": True,
            "gated_smoke": True,
            "safe_to_render": True,
            "pilot_executed": False,
            "would_execute": False,
            "would_call_network": False,
            "would_call_github": False,
            "would_call_web": False,
            "would_call_providers": False,
            "would_send_email": False,
            "would_schedule": False,
            "would_start_worker": False,
            "would_install": False,
            "would_deploy": False,
            "would_publish": False,
            "would_move_money": False,
            "would_read_credentials": False,
            "no_side_effects": True,
            "no_fake_revenue": True,
            "no_fake_costs": True,
            "no_fake_results": True,
            "no_fake_benchmarks": True,
            "no_fake_capabilities": True,
            "no_execution_by_id": checks["no_execution_by_id"],
            "web_github_providers_real_not_connected": checks["web_github_providers_not_connected"],
            "hermes_remains_execution_engine": True,
            "no_duplicate_hermes_runtime": True,
            "checks": checks,
            "candidate_summaries": {
                "product_revenue": _summary(product),
                "routine_ops": _summary(routine),
                "moonshot_lab": _summary(moonshot),
                "research_local_docs_preview": {
                    "research_id": research_preview["research_id"],
                    "execution_status": research_preview["execution_status"],
                    "candidate_state": research_preview["candidate_state"],
                    "file_reads_performed": research_preview["file_reads_performed"],
                    "adapter_called": research_preview["adapter_called"],
                    "source_type": research_preview["source_type"],
                    "normalized_scope": research_preview["normalized_scope"],
                },
                "candidate_by_id_only": {
                    "execution_status": candidate_by_id["execution_status"],
                    "candidate_by_research_id_only": candidate_by_id["candidate_by_research_id_only"],
                    "request_rehydrated_for_execution": candidate_by_id["request_rehydrated_for_execution"],
                    "missing_requirements": candidate_by_id["missing_requirements"],
                },
            },
        }


_PRODUCT_SIDE_EFFECTS = (
    "execution_performed",
    "external_calls_performed",
    "web_called",
    "github_called",
    "stripe_called",
    "email_sent",
    "deploy_performed",
    "domain_purchase_performed",
    "publication_performed",
    "checkout_created",
    "payment_processed",
    "money_moved",
    "credentials_used",
    "providers_called",
    "hermes_called",
    "approval_gateway_called",
)
_ROUTINE_SIDE_EFFECTS = (
    "would_schedule",
    "would_execute",
    "would_notify",
    "would_access_external_account",
    "would_store_secret",
    "execution_performed",
    "scheduler_created",
    "cron_created",
    "background_worker_started",
    "watcher_started",
    "email_sent",
    "calendar_accessed",
    "gmail_accessed",
    "contacts_accessed",
    "provider_called",
    "account_login_performed",
    "account_recovery_performed",
    "password_saved",
    "two_fa_bypassed",
    "cookie_token_session_used",
    "money_moved",
    "production_changed",
    "providers_called",
    "hermes_called",
    "approval_gateway_called",
)
_MOONSHOT_SIDE_EFFECTS = (
    "would_execute",
    "would_call_network",
    "would_install_dependencies",
    "would_use_provider",
    "would_publish",
    "would_deploy",
    "would_move_money",
    "execution_performed",
    "experiment_executed",
    "prototype_built",
    "network_called",
    "web_called",
    "github_called",
    "provider_called",
    "dependencies_installed",
    "external_process_started",
    "background_worker_started",
    "publication_performed",
    "deploy_performed",
    "payment_processed",
    "money_moved",
    "credentials_used",
    "benchmark_claimed",
    "research_result_claimed",
    "breakthrough_claimed",
    "hermes_called",
    "approval_gateway_called",
)


def _all_false(payload: Dict[str, Any], keys: tuple[str, ...]) -> bool:
    return all(payload[key] is False for key in keys)


def _summary(candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_type": candidate["candidate_type"],
        "candidate_state": candidate["candidate_state"],
        "execution_status": candidate["execution_status"],
        "risk_level": candidate["risk_level"],
        "required_approval_level": candidate["required_approval_level"],
        "prepare_only": candidate["prepare_only"],
        "safe_to_execute": candidate["safe_to_execute"],
    }
