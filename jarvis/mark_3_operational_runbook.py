from __future__ import annotations

from typing import Any, Dict


class Mark3OperationalRunbook:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 3",
            "release_candidate_status": "ready_as_controlled_release_candidate",
            "read_only": True,
            "local_first": True,
            "human_control_required": True,
            "restrictions_are_approval_gates_not_permanent_bans": True,
            "steps": [
                "Open the dedicated PR #141 worktree and activate ~/venvs/hermes-agent, then export PYTHONPATH=.",
                "Verify GET /mark-3/release-candidate/status, capabilities, readiness, dangerous-route-audit, approval-path-audit, e2e-smoke, pilot-plan, runbook, known-limitations, and next-steps.",
                "Do not run the real pilot from the RC endpoints; they are read-only/control-plane.",
                "For the first pilot, keep scope local, useful, reversible, and explicitly approved.",
                "Use product/revenue, routine ops, and moonshot candidates as prepare-only planning surfaces.",
                "Use research execution preview for exact local docs/repo scope; do not execute by research_id alone.",
                "Use governed Hermes read_file only when the exact mission candidate, path, approval, scope fingerprint, and operator authorization are present.",
                "Record outcomes, failures, evidence, unknowns, real elapsed time, and real costs only when measured.",
                "Create learning proposals from evidence; approving learning never grants execution permission.",
                "Stop immediately on scope creep, missing approval, fake evidence, external provider request, account access, credential handling, deploy, email, money, scheduler, or production request.",
                "After tests and review pass, close the PR outside Codex with jarvis-finish-pr \"Mark 3 Release Candidate Pilot\".",
            ],
            "validation": [
                "git diff --check",
                "python -m py_compile $(find jarvis -name '*.py')",
                "pytest tests/jarvis/test_mark_3_release_candidate_pilot.py -q -x --durations=20",
                "pytest tests/jarvis/test_mark_3_moonshot_lab_research_experiment_engine.py -q -x --durations=20",
                "pytest tests/jarvis/test_mark_3_local_routine_scheduler_personal_family_ops.py -q -x --durations=20",
                "pytest tests/jarvis/test_mark_3_product_revenue_factory.py -q -x --durations=20",
                "pytest tests/jarvis/test_mark_3_research_execution_bridge.py -q -x --durations=20",
                "pytest tests/jarvis/test_api.py::test_health_ok -q -vv",
                "pytest tests/jarvis -q -x --durations=20",
            ],
            "operator_controls": [
                "human approval per risk level",
                "no inherited approval",
                "scope and budget before material work",
                "stop conditions before pilot start",
                "visible stop or kill decision by operator",
                "audit and post-mortem after pilot",
            ],
            "do_not_do_in_rc": [
                "do not execute the real pilot",
                "do not activate free autonomy",
                "do not activate a real scheduler",
                "do not use external network, GitHub/web, providers, credentials, or .env",
                "do not publish, deploy, send email, access accounts, move money, or install dependencies",
                "do not create another Hermes",
            ],
            "safe_to_render": True,
        }


class Mark3KnownLimitations:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 3",
            "release_candidate_status": "ready_as_controlled_release_candidate",
            "not_ready_for_free_autonomy": True,
            "limitations": [
                "No free autonomy.",
                "No real provider execution by default.",
                "No real scheduler yet.",
                "No cloud, VPS, or Mac mini until revenue or technical need justifies it.",
                "No fake costs or revenue.",
                "No fake results, benchmarks, breakthroughs, completion, or capability claims.",
                "No background 24/7 operation by default.",
                "No external account operations without explicit setup, authorization, and approvals.",
                "GitHub, web, providers, email, deploy, Stripe live, domains, and account access remain not connected by default.",
                "Preview/read-only/setup_required are not permanent ceilings; they are gates until real capability and valid approval exist.",
            ],
            "safe_to_render": True,
        }


class Mark3NextSteps:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 3",
            "release_candidate_status": "ready_as_controlled_release_candidate",
            "recommended_next_steps": [
                "Run the controlled local pilot after explicit operator approval.",
                "Harden findings from the pilot before expanding scope.",
                "Start Mark 4 only if the pilot justifies it with evidence.",
                "Avoid micro-PR explosion; keep future work as coherent macro PRs.",
            ],
            "free_autonomy_recommended": False,
            "mark_4_requires_pilot_evidence": True,
            "safe_to_render": True,
        }
