from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Mapping, Optional

from hermes_constants import get_hermes_home


SAFE_WAKE_ENV_KEYS = {
    "JARVIS_WAKE_BACKEND",
    "JARVIS_OPENWAKEWORD_MODEL_PATH",
    "JARVIS_VOSK_MODEL_PATH",
    "JARVIS_WAKE_SAMPLE_RATE",
    "JARVIS_WAKE_BLOCK_SIZE",
    "JARVIS_WAKE_DEBOUNCE_SECONDS",
}


def wake_env_file(env_path: str = "") -> Path:
    if env_path:
        return Path(env_path).expanduser()
    return get_hermes_home() / ".env"


def read_persisted_wake_env(*, env_path: str = "") -> Dict[str, str]:
    path = wake_env_file(env_path)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}

    values: Dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if key not in SAFE_WAKE_ENV_KEYS:
            continue
        value = raw_value.strip().strip('"').strip("'")
        if value:
            values[key] = value
    return values


def merge_persisted_wake_env(env: Optional[Mapping[str, str]] = None, *, env_path: str = "") -> Dict[str, str]:
    source = dict(env if env is not None else os.environ)
    for key, value in read_persisted_wake_env(env_path=env_path).items():
        source.setdefault(key, value)
    return source


def safe_wake_env_updates(
    *,
    backend: str,
    openwakeword_model_path: str = "",
    vosk_model_path: str = "",
) -> Dict[str, str]:
    updates: Dict[str, str] = {}
    if backend in {"openwakeword", "vosk"}:
        updates["JARVIS_WAKE_BACKEND"] = backend
    if openwakeword_model_path:
        updates["JARVIS_OPENWAKEWORD_MODEL_PATH"] = str(Path(openwakeword_model_path).expanduser())
    if vosk_model_path:
        updates["JARVIS_VOSK_MODEL_PATH"] = str(Path(vosk_model_path).expanduser())
    return {key: value for key, value in updates.items() if key in SAFE_WAKE_ENV_KEYS and value}


def write_safe_wake_env(path: Path, values: Mapping[str, str]) -> Dict[str, object]:
    safe_values = {key: str(value) for key, value in values.items() if key in SAFE_WAKE_ENV_KEYS and str(value)}
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen = set()
    output: list[str] = []
    for line in existing:
        stripped = line.strip()
        key = stripped.split("=", 1)[0] if "=" in stripped and not stripped.startswith("#") else ""
        if key in safe_values:
            output.append(f"{key}={safe_values[key]}")
            seen.add(key)
        else:
            output.append(line)
    for key, value in safe_values.items():
        if key not in seen:
            output.append(f"{key}={value}")
    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    return {"path": str(path), "written_keys": sorted(safe_values), "secrets_written": False}
