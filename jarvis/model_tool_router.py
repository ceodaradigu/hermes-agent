from __future__ import annotations

from typing import Any, Dict, List


def build_model_tool_router_preview() -> List[Dict[str, Any]]:
    return [
        {
            "adapter": name,
            "status": status,
            "governed_by_jarvis": True,
            "real_invocation_enabled": False,
            "would_invoke_real_tool": False,
            "requires_policy_and_approval": True,
            "sandbox_required": True,
            "allowlist_required": True,
            "denylist_checked": False,
            "readiness": "candidate_or_preview_only",
            "next_safe_step": "Classify mission, prepare sandbox/worktree, then request required approval.",
        }
        for name, status in (
            ("CodexCliAdapter", "preview"),
            ("ClaudeCodeCliAdapter", "preview"),
            ("ClaudeCoworkAdapter", "preview"),
            ("ApiFallbackAdapter", "preview"),
            ("RoutineExecutionBridge", "preview"),
            ("DeployOperationAdapter", "candidate"),
            ("StripeOperationAdapter", "candidate"),
            ("EmailOperationAdapter", "candidate"),
            ("DomainPublishingAdapter", "candidate"),
            ("LocalScriptAdapter", "planned"),
            ("FilesystemToolAdapter", "candidate"),
            ("GitHubToolAdapter", "candidate"),
            ("BrowserToolAdapter", "candidate"),
            ("ExternalAPIToolAdapter", "candidate"),
        )
    ]
