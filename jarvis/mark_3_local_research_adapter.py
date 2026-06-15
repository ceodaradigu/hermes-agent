from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


LOCAL_RESEARCH_SOURCE_TYPES = {"docs", "local_repo"}
LOCAL_RESEARCH_ADAPTER_NAME = "local_docs_repo_read_adapter"
DEFAULT_LOCAL_RESEARCH_MAX_BYTES = 64 * 1024


@dataclass(frozen=True)
class LocalResearchReadAdapter:
    """Bounded local read adapter for Mark 3 research.

    This is intentionally not a generic executor. It reads one exact file scope
    after local path validation and never scans directories, follows symlinks,
    starts workers, invokes tools, shells out, or calls network providers.
    """

    repo_root: Path
    max_bytes: int = DEFAULT_LOCAL_RESEARCH_MAX_BYTES

    def __init__(self, repo_root: Optional[Path | str] = None, *, max_bytes: int = DEFAULT_LOCAL_RESEARCH_MAX_BYTES) -> None:
        root = Path(repo_root or Path.cwd())
        object.__setattr__(self, "repo_root", root.resolve())
        object.__setattr__(self, "max_bytes", max(1, int(max_bytes)))

    def read(self, *, source_type: str, scope: Any) -> Dict[str, Any]:
        normalized_source = _clean_text(source_type).lower()
        if normalized_source not in LOCAL_RESEARCH_SOURCE_TYPES:
            return _blocked("unsupported_local_research_source", permanent_denial=True)

        scope_error = _scope_error(scope)
        if scope_error:
            return _blocked(scope_error, permanent_denial=scope_error in {"path_traversal_blocked", "sensitive_path_blocked"})

        requested_scope = _clean_text(scope)
        path_error = _path_text_error(requested_scope)
        if path_error:
            return _blocked(path_error, permanent_denial=path_error in {"path_traversal_blocked", "sensitive_path_blocked"})

        base_dir, target = self._target_path(normalized_source, requested_scope)
        containment_error = _containment_error(base_dir, target)
        if containment_error:
            return _blocked(containment_error, permanent_denial=True)

        symlink_error = _symlink_error(base_dir, target)
        if symlink_error:
            return _blocked(symlink_error, permanent_denial=True)

        if not target.exists():
            return _blocked("file_not_found", permanent_denial=False)
        if not target.is_file():
            return _blocked("exact_file_scope_required", permanent_denial=False)

        data = _read_bounded(target, self.max_bytes)
        truncated = len(data) > self.max_bytes
        if truncated:
            data = data[: self.max_bytes]
        if b"\x00" in data:
            return _blocked("non_text_file_not_supported", permanent_denial=False)

        text = data.decode("utf-8", errors="replace")
        if _sensitive_content_detected(text):
            return _blocked("sensitive_content_blocked", permanent_denial=True)

        relative_path = _relative_reference(self.repo_root, target)
        return {
            "adapter": LOCAL_RESEARCH_ADAPTER_NAME,
            "status": "success",
            "source_type": normalized_source,
            "scope": requested_scope,
            "path_reference": relative_path,
            "encoding": "utf-8",
            "bytes_read": len(data),
            "max_bytes": self.max_bytes,
            "truncated": truncated,
            "line_count": len(text.splitlines()),
            "content_sha256": hashlib.sha256(data).hexdigest(),
            "content": text,
            "read_performed": True,
            "local_repo_scan_performed": False,
            "commands_executed": False,
            "threads_started": 0,
            "network_called": False,
        }

    def _target_path(self, source_type: str, requested_scope: str) -> tuple[Path, Path]:
        if source_type == "docs":
            docs_root = self.repo_root / "docs"
            parts = Path(requested_scope).parts
            target = self.repo_root / requested_scope if parts and parts[0] == "docs" else docs_root / requested_scope
            return docs_root, target
        return self.repo_root, self.repo_root / requested_scope


def _scope_error(scope: Any) -> str:
    if scope is None or _clean_text(scope) == "":
        return "exact_file_scope_required"
    if isinstance(scope, (list, tuple, set)):
        return "multi_scope_blocked"
    return ""


def _path_text_error(scope: str) -> str:
    normalized_scope = scope.replace("\\", "/")
    path = Path(normalized_scope)
    if path.is_absolute() or normalized_scope.startswith("~"):
        return "path_traversal_blocked"
    if any(part in {"..", ""} for part in path.parts):
        return "path_traversal_blocked"
    if _is_broad_scope(normalized_scope):
        return "exact_file_scope_required"
    if _is_sensitive_path(normalized_scope):
        return "sensitive_path_blocked"
    return ""


def _containment_error(base_dir: Path, target: Path) -> str:
    try:
        target.relative_to(base_dir)
        return ""
    except ValueError:
        return "path_traversal_blocked"


def _symlink_error(base_dir: Path, target: Path) -> str:
    current = base_dir
    if current.is_symlink():
        return "symlink_blocked"
    try:
        relative = target.relative_to(base_dir)
    except ValueError:
        return "path_traversal_blocked"
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return "symlink_blocked"
    return ""


def _relative_reference(repo_root: Path, target: Path) -> str:
    try:
        return target.relative_to(repo_root).as_posix()
    except ValueError:
        return target.name


def _read_bounded(target: Path, max_bytes: int) -> bytes:
    with target.open("rb") as handle:
        return handle.read(max_bytes + 1)


def _blocked(reason: str, *, permanent_denial: bool) -> Dict[str, Any]:
    return {
        "adapter": LOCAL_RESEARCH_ADAPTER_NAME,
        "status": "blocked",
        "blocked_reasons": [reason],
        "permanent_denial": permanent_denial,
        "read_performed": False,
        "local_repo_scan_performed": False,
        "commands_executed": False,
        "threads_started": 0,
        "network_called": False,
    }


def _is_broad_scope(scope: str) -> bool:
    normalized = _clean_text(scope).lower().rstrip("/")
    return normalized in {"", ".", "*", "docs", "repo", "repository", "root", "repo root", "all", "entire repo", "whole repo"}


def _is_sensitive_path(scope: str) -> bool:
    for part in Path(scope).parts:
        normalized = part.lower().replace("-", "_").replace(" ", "_")
        stem = Path(part).stem.lower().replace("-", "_").replace(" ", "_")
        if normalized == ".env" or stem == ".env":
            return True
        if any(marker in normalized for marker in _SENSITIVE_PATH_SUBSTRINGS):
            return True
        if stem in {"key", "keys"} or normalized in {"key", "keys"}:
            return True
        if normalized.endswith(".key") or ".key." in normalized:
            return True
    return False


def _sensitive_content_detected(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SENSITIVE_CONTENT_PATTERNS)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(item for item in (_clean_text(item) for item in value) if item)
    return " ".join(str(value).strip().split())


_SENSITIVE_PATH_SUBSTRINGS: Iterable[str] = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "credentials",
    "password",
    "private_key",
    "privatekey",
    "secret",
    "token",
)

_SENSITIVE_CONTENT_PATTERNS: Iterable[re.Pattern[str]] = (
    re.compile(r"(?i)(?:^|[/\s])\.env(?:\b|[._/-])"),
    re.compile(
        r"(?i)\b(?:api[_ -]?key|apikey|authorization|bearer|credential|credentials|"
        r"password|private[_ -]?key|privatekey|secret|token)\b['\"]?\s*[:=]"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{6,}"),
)
