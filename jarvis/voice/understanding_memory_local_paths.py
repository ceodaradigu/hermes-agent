from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


SNAPSHOT_FILENAME = "memory_proposals.snapshot.json"
AUDIT_LOG_FILENAME = "audit_log.jsonl"
USER_UNDERSTANDING_DIRNAME = "user_understanding"
BACKUPS_DIRNAME = "backups"

_DANGEROUS_FILE_SUFFIXES = {
    ".db",
    ".env",
    ".ini",
    ".json",
    ".jsonl",
    ".log",
    ".sqlite",
    ".sqlite3",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class UserUnderstandingMemoryLocalPaths:
    root_dir: Path
    user_understanding_dir: Path
    snapshot_path: Path
    audit_log_path: Path
    backups_dir: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "root_dir": str(self.root_dir),
            "user_understanding_dir": str(self.user_understanding_dir),
            "snapshot_path": str(self.snapshot_path),
            "audit_log_path": str(self.audit_log_path),
            "backups_dir": str(self.backups_dir),
        }

    def to_dict(self) -> dict[str, str]:
        return self.as_dict()


def resolve_user_understanding_memory_local_paths(
    base_dir: str | Path | None = None,
) -> UserUnderstandingMemoryLocalPaths:
    root_dir = _coerce_base_dir(base_dir)
    user_understanding_dir = root_dir / USER_UNDERSTANDING_DIRNAME

    return UserUnderstandingMemoryLocalPaths(
        root_dir=root_dir,
        user_understanding_dir=user_understanding_dir,
        snapshot_path=user_understanding_dir / SNAPSHOT_FILENAME,
        audit_log_path=user_understanding_dir / AUDIT_LOG_FILENAME,
        backups_dir=user_understanding_dir / BACKUPS_DIRNAME,
    )


def validate_user_understanding_memory_local_paths(
    paths: UserUnderstandingMemoryLocalPaths,
) -> dict[str, Any]:
    if not isinstance(paths, UserUnderstandingMemoryLocalPaths):
        raise TypeError("paths must be UserUnderstandingMemoryLocalPaths.")

    notes = [
        "Path validation is lexical only.",
        "No directories are created.",
        "No files are read.",
        "No files are written.",
        "Local memory persistence is not enabled.",
    ]

    return {
        "valid": True,
        "can_write": False,
        "can_read": False,
        "persisted": False,
        "root_dir": str(paths.root_dir),
        "user_understanding_dir": str(paths.user_understanding_dir),
        "snapshot_path": str(paths.snapshot_path),
        "audit_log_path": str(paths.audit_log_path),
        "backups_dir": str(paths.backups_dir),
        "notes": notes,
    }


def _coerce_base_dir(base_dir: str | Path | None) -> Path:
    if base_dir is None:
        return Path(".jarvis")

    if isinstance(base_dir, Path):
        raw = str(base_dir)
    elif isinstance(base_dir, str):
        raw = base_dir
    else:
        raise TypeError("base_dir must be str, pathlib.Path, or None.")

    if not raw.strip():
        raise ValueError("base_dir must not be empty.")
    if "\0" in raw:
        raise ValueError("base_dir must not contain null bytes.")

    path = Path(raw)
    if any(part == ".." for part in path.parts):
        raise ValueError("base_dir must not contain path traversal.")
    if path.name in {"", ".", ".."}:
        raise ValueError("base_dir must point to a directory path.")
    if path.suffix.lower() in _DANGEROUS_FILE_SUFFIXES:
        raise ValueError("base_dir appears to be a file path, not a directory.")

    return path
