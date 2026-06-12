from __future__ import annotations

from typing import Any, Dict


class Mark2OperationalRunbook:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_mark": "Mark 2",
            "release_candidate": True,
            "read_only": True,
            "steps": [
                "Open the dedicated worktree and activate ~/venvs/hermes-agent, then export PYTHONPATH=.",
                "Start local JARVIS only when needed with python -m uvicorn jarvis.api.app:app --host 127.0.0.1 --port 8000.",
                "Verify GET /mark-2/release-candidate/status, readiness, dangerous-route-audit, approval-path-audit, and e2e-smoke.",
                "Review dashboard, pending approvals, risk, cost, worktree, diff, tests, review, and audit panels.",
                "Use Voice Approval Channel only with exact readback, required phrase, expiry, audit, and confirmations.",
                "Valid voice phrases include Sí, continúa; JARVIS, entiendo los riesgos, hazlo; and JARVIS, confirmación final when required.",
                "Wake phrases such as Hola Jarvis and Jarvis only open a session and never approve.",
                "Stop JARVIS with the stop control or kill switch; stop and rollback remain available before real execution.",
                "Create a worktree with git worktree add ~/jarvis-worktrees/<branch> -b <branch> main, then cd into it.",
                "Open Codex inside the dedicated worktree with codex; never launch it from main for PR implementation.",
                "Close a reviewed and approved PR with jarvis-finish-pr only after tests and review pass.",
                "Never deploy, call Stripe, send email, modify DNS, use external network, or touch production without valid approvals.",
                "Do not store access material in JARVIS and do not use cookies or session tokens.",
            ],
            "known_main_worktree_warning": "fatal: 'main' is already used by worktree is not a blocker when PR state is MERGED and jarvis-finish-pr updated main and cleaned the completed worktree.",
            "testclient_known_hang": "If tests/jarvis/test_api.py or the full suite hangs inside Codex TestClient, stop it, document the hang without claiming a pass, and validate test_api.py outside Codex.",
            "manual_setup_required": [
                "Codex CLI login",
                "Claude Code login",
                "Claude Cowork/Desktop setup",
                "Stripe provider setup",
                "email provider setup",
                "deploy provider setup",
                "domain provider setup",
                "API provider setup only when API fallback is selected",
            ],
            "validation": [
                "git diff --check",
                "python -m py_compile jarvis/mark_2_release_candidate.py jarvis/mark_2_e2e_readiness.py jarvis/mark_2_operational_runbook.py jarvis/mark_2_dangerous_route_audit.py jarvis/mark_2_approval_path_audit.py",
                "pytest tests/jarvis/test_mark_2_release_candidate_hardening.py -q",
                "pytest tests/jarvis -q -x --durations=20",
            ],
        }


class Mark2KnownLimitations:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mark_2_not_full_autonomy": True,
            "limitations": [
                "Real execution remains disabled by default.",
                "Production pilot requires explicit manual provider setup and valid approvals.",
                "External network and access material remain disabled by default.",
                "AI CLI and Cowork adapters remain previews and require supervised manual setup.",
                "Costs remain estimated, manually supplied, or unknown unless evidence exists.",
                "TestClient may hang inside Codex and must then be validated outside Codex.",
            ],
        }


class Mark2NextSteps:
    def to_dict(self) -> Dict[str, Any]:
        return {
            "next_recommended_mark": "Mark 3",
            "recommended_options": [
                "Plan Mark 3 as coherent macro PRs.",
                "Run a limited Mark 2 production pilot only after explicit manual setup and valid approvals.",
            ],
            "phase_t_exists": False,
            "free_autonomy_recommended": False,
        }
