from __future__ import annotations

from typing import Any, Dict


class GitHubToolAdapter:
    def preview_create_issue(self, **values: Any) -> Dict[str, Any]:
        return self._preview("create_issue", **values)

    def preview_create_branch(self, **values: Any) -> Dict[str, Any]:
        return self._preview("create_branch", **values)

    def preview_create_pr(self, **values: Any) -> Dict[str, Any]:
        return self._preview("create_pr", **values)

    def preview_comment_pr(self, **values: Any) -> Dict[str, Any]:
        return self._preview("comment_pr", **values)

    def preview_merge_pr(self, **values: Any) -> Dict[str, Any]:
        return self._preview("merge_pr", **values)

    candidate_create_issue = preview_create_issue
    candidate_create_branch = preview_create_branch
    candidate_create_pr = preview_create_pr
    candidate_comment_pr = preview_comment_pr
    candidate_merge_pr = preview_merge_pr

    def _preview(self, operation: str, **values: Any) -> Dict[str, Any]:
        branch = str(values.get("branch") or "")
        protected = bool(values.get("protected_branch") or branch in {"main", "master"})
        merge = operation == "merge_pr"
        return {
            "adapter_name": "github",
            "repo": str(values.get("repo") or ""),
            "branch": branch,
            "pr_number": values.get("pr_number"),
            "operation": operation,
            "remote_mutation": True,
            "credentials_required": True,
            "network_required": True,
            "approval_required": True,
            "strong_approval_required": merge or protected,
            "double_confirmation_required": merge and protected,
            "blocked_by_default": True,
            "would_call_github": False,
            "eligible_after_valid_approval": True,
            "rollback_or_stop_plan": str(values.get("rollback_or_stop_plan") or "stop before remote mutation"),
            "blocked_reasons": ["GitHub real calls disabled", "network disabled", "credentials access disabled"],
        }
