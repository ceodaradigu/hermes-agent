from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable


class FilesystemToolAdapter:
    """Path-only filesystem planning. It never reads, writes, patches, or deletes."""

    def __init__(
        self,
        repo_root: str | Path = ".",
        *,
        allowed_paths: Iterable[str] = (".",),
        denied_paths: Iterable[str] = (".env", ".git", "secrets"),
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.allowed_paths = [self._resolve(item) for item in allowed_paths]
        self.denied_paths = [self._resolve(item) for item in denied_paths]

    def preview_read_file(self, path: str) -> Dict[str, Any]:
        return self._preview("read_file", path)

    def preview_write_file(self, path: str, content: str = "") -> Dict[str, Any]:
        return self._preview("write_file", path, content=content)

    def preview_patch_file(self, path: str, patch: str = "") -> Dict[str, Any]:
        return self._preview("patch_file", path, content=patch)

    def preview_create_directory(self, path: str) -> Dict[str, Any]:
        return self._preview("create_directory", path)

    def preview_delete_file(self, path: str, rollback_plan: str = "") -> Dict[str, Any]:
        return self._preview("delete_file", path, rollback_plan=rollback_plan)

    def candidate_write_file(self, path: str, content: str = "") -> Dict[str, Any]:
        return self._preview("write_file", path, content=content, candidate=True)

    def candidate_patch_file(self, path: str, patch: str = "") -> Dict[str, Any]:
        return self._preview("patch_file", path, content=patch, candidate=True)

    def candidate_delete_file(self, path: str, rollback_plan: str = "") -> Dict[str, Any]:
        return self._preview("delete_file", path, candidate=True, rollback_plan=rollback_plan)

    def _resolve(self, path: str | Path) -> Path:
        candidate = Path(path)
        return candidate.resolve() if candidate.is_absolute() else (self.repo_root / candidate).resolve()

    def _preview(
        self,
        operation: str,
        path: str,
        *,
        content: str = "",
        candidate: bool = False,
        rollback_plan: str = "",
    ) -> Dict[str, Any]:
        normalized = self._resolve(path)
        within_repo = _within(normalized, self.repo_root)
        allowlist = within_repo and any(_within(normalized, item) for item in self.allowed_paths)
        denylist = any(_within(normalized, item) for item in self.denied_paths) or _secret_path(normalized)
        write = operation in {"write_file", "patch_file", "create_directory"}
        delete = operation == "delete_file"
        reasons = []
        if not within_repo:
            reasons.append("filesystem target is outside repo")
        if not allowlist:
            reasons.append("filesystem target is outside allowlist")
        if denylist:
            reasons.append("filesystem target matches denylist or secret path")
        if delete and not rollback_plan:
            reasons.append("delete requires rollback plan")
        return {
            "adapter_name": "filesystem",
            "operation": operation,
            "repo_root": str(self.repo_root),
            "allowed_paths": [str(item) for item in self.allowed_paths],
            "denied_paths": [str(item) for item in self.denied_paths],
            "path_normalized": str(normalized),
            "within_repo": within_repo,
            "within_allowlist": allowlist,
            "allowlist_match": allowlist,
            "denylist_match": denylist,
            "denied_reason": "; ".join(reasons),
            "would_read": operation == "read_file" and not reasons,
            "would_write": False,
            "would_delete": False,
            "requested_write": write,
            "requested_delete": delete,
            "approval_required": write or delete,
            "strong_approval_required": delete,
            "rollback_plan": rollback_plan or ("restore previous file content" if write else ""),
            "diff_preview": _diff_preview(operation, content),
            "candidate": candidate,
            "blocked_reasons": reasons,
            "executed": False,
            "filesystem_changed": False,
        }


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _secret_path(path: Path) -> bool:
    lowered = [part.lower() for part in path.parts]
    return any(part == ".env" or part.startswith(".env.") or part in {"secrets", "credentials"} for part in lowered)


def _diff_preview(operation: str, content: str) -> str:
    if operation not in {"write_file", "patch_file"}:
        return "[no content diff]"
    return f"[redacted {operation} preview: {len(str(content or ''))} characters]"
