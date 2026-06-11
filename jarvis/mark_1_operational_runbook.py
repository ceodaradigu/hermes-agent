from __future__ import annotations

from typing import Any, Dict


class Mark1OperationalRunbook:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 1",
            "read_only": True,
            "steps": [
                "Open Codex from the dedicated PR worktree, never from main.",
                "Activate ~/venvs/hermes-agent and export PYTHONPATH=.",
                "Run git status --short and the requested validation suite.",
                "Start the local API with python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000 when needed.",
                "Review GET /mark-1/status and the remaining /mark-1 read-only endpoints.",
                "Treat approvals as scoped, expiring authorization records; approval is not execution.",
                "Treat execution candidates as reviewed eligibility, never proof that an action ran.",
                "Review monetization estimates as projections, never confirmed revenue.",
                "Review Adaptive SaaS Builder quality, differentiation, budget, publish, deploy, and rollback previews.",
                "Never perform a critical action without valid strong approval, double confirmation, audit, permission gates, and rollback or stop plan.",
                "Close an approved PR with jarvis-finish-pr after tests and review pass.",
                "Begin Mark 2 only as the next approved macro, without creating Phase T.",
            ],
            "github_cli_401": "A GitHub CLI 401 means authentication is invalid or expired; do not bypass it or expose credentials.",
            "worktree_cleanup": "After merge outside this PR, remove the worktree and local branch only after confirming a clean status.",
            "macro_pr_rule": "Use large coherent macro-PRs; do not fragment Mark 2 or Mark 3 into 120 micro-PRs.",
        }


class Mark1KnownLimitations:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mark_1_is_not_finished_forever": True,
            "limitations": [
                {"limitation": "no real local daemon yet", "target_mark": "Mark 2"},
                {"limitation": "no real microphone wake listener yet", "target_mark": "Mark 2"},
                {"limitation": "no advanced visual UI yet", "target_mark": "Mark 2"},
                {"limitation": "no deep real tool execution yet", "target_mark": "Mark 2"},
                {"limitation": "no real browser, GitHub, or external filesystem execution yet", "target_mark": "Mark 2"},
                {"limitation": "no Stripe live execution yet", "target_mark": "Mark 2"},
                {"limitation": "no automatic real deploy yet", "target_mark": "Mark 2"},
                {"limitation": "no 24/7 infrastructure yet", "target_mark": "Mark 3"},
                {"limitation": "no advanced multi-agent operating system yet", "target_mark": "Mark 3"},
                {"limitation": "no continuous self-improvement loop yet", "target_mark": "Mark 3"},
            ],
        }


class Mark2NextPlan:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "next_recommended_mark": "Mark 2",
            "phase_t_exists": False,
            "no_micro_pr_policy": True,
            "mark_2": [
                "Mark 2 Macro 1 - Local Daemon, Real Wake Listener & Desktop Runtime",
                "Mark 2 Macro 2 - Real Tool Execution: Browser, GitHub, Filesystem & APIs",
                "Mark 2 Macro 3 - Visual Command Center UI & Human Approval Console",
                "Mark 2 Macro 4 - Real Deploy, Stripe, Email & External Operations",
                "Mark 2 Release Candidate Hardening",
            ],
            "mark_3": [
                "Mark 3 Macro 1 - Multi-Agent Operating System",
                "Mark 3 Macro 2 - Continuous Learning & Self-Improvement Loop",
                "Mark 3 Macro 3 - Autonomous Opportunity, Product & Growth Engine",
                "Mark 3 Macro 4 - 24/7 Infrastructure, Monitoring, Recovery & Cost Control",
                "Mark 3 Release Candidate Hardening",
            ],
        }
