from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

from hermes_constants import display_hermes_home, is_wsl
from jarvis.phase_12_wake_config import (
    SAFE_WAKE_ENV_KEYS,
    safe_wake_env_updates,
    wake_env_file,
    write_safe_wake_env,
)
from jarvis.phase_12_wake_listener import build_wake_listener_status


WAKE_SETUP_SCHEMA_VERSION = "jarvis.phase_12.wake_setup.v1"


def _python_ok() -> bool:
    return sys.version_info >= (3, 10)


def _inside_virtualenv() -> bool:
    return bool(getattr(sys, "base_prefix", sys.prefix) != sys.prefix or os.environ.get("VIRTUAL_ENV"))


def _pip_command(packages: Iterable[str]) -> str:
    return " ".join([sys.executable, "-m", "pip", "install", *packages])


def _packages_for_backend(backend: str) -> list[str]:
    if backend == "openwakeword":
        return ["numpy", "sounddevice", "openwakeword"]
    if backend == "vosk":
        return ["sounddevice", "vosk"]
    return ["numpy", "sounddevice", "openwakeword", "vosk"]


def _env_file_path(env_path: str = "") -> Path:
    return wake_env_file(env_path)


def _safe_env_updates(
    *,
    backend: str,
    openwakeword_model_path: str = "",
    vosk_model_path: str = "",
) -> Dict[str, str]:
    return safe_wake_env_updates(
        backend=backend,
        openwakeword_model_path=openwakeword_model_path,
        vosk_model_path=vosk_model_path,
    )


def _write_env_values(path: Path, values: Mapping[str, str]) -> Dict[str, Any]:
    safe_values = {key: value for key, value in values.items() if key in SAFE_WAKE_ENV_KEYS}
    return write_safe_wake_env(path, safe_values)


def build_wake_setup_status(
    *,
    backend: str = "auto",
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    requested = backend if backend in {"auto", "openwakeword", "vosk"} else "auto"
    merged_env = dict(env if env is not None else os.environ)
    if requested != "auto":
        merged_env["JARVIS_WAKE_BACKEND"] = requested
    wake_status = build_wake_listener_status(env=merged_env)
    packages = _packages_for_backend(requested)
    windows_or_wsl = platform.system().lower() == "windows" or is_wsl()
    return {
        "schema_version": WAKE_SETUP_SCHEMA_VERSION,
        "status": "ready" if wake_status["state"]["real_microphone_wake_available"] else "needs_setup",
        "backend_requested": requested,
        "backend_selected": wake_status["state"]["selected_backend"],
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
            "supported": _python_ok(),
            "inside_virtualenv": _inside_virtualenv(),
            "hermes_home": display_hermes_home(),
        },
        "wake_listener": wake_status,
        "dependency_install": {
            "auto_install_default": False,
            "requires_explicit_yes": True,
            "no_model_downloads": True,
            "pip_command": _pip_command(packages),
            "packages": packages,
        },
        "audio_backend_notes": {
            "windows_or_wsl": windows_or_wsl,
            "wsl_note": (
                "En WSL, el micrófono puede requerir WSLg/PulseAudio/USB passthrough. "
                "Si sounddevice no ve entradas, ejecuta el listener en Windows nativo."
            )
            if is_wsl()
            else "",
            "windows_note": "En Windows puede hacer falta seleccionar el micrófono predeterminado y permitir acceso al micrófono."
            if platform.system().lower() == "windows"
            else "",
            "linux_note": "En Linux instala PortAudio/ALSA si sounddevice no detecta entrada." if platform.system().lower() == "linux" and not is_wsl() else "",
        },
        "model_setup": {
            "openwakeword": {
                "works_for_primary_jarvis": "requires_custom_model_path",
                "works_for_hola_jarvis": "experimental_requires_custom_or_stt_match",
                "env": "JARVIS_OPENWAKEWORD_MODEL_PATH=/path/to/jarvis.onnx",
                "silent_download": False,
            },
            "vosk": {
                "works_for_primary_jarvis": "yes_with_spanish_local_model",
                "works_for_hola_jarvis": "best_effort_with_spanish_local_model",
                "env": "JARVIS_VOSK_MODEL_PATH=/path/to/vosk-model-small-es",
                "phrase_specific_model_required": False,
                "silent_download": False,
            },
        },
        "recommended_path": {
            "backend": "vosk",
            "why": "Vosk local STT is reliable enough for the short primary wake phrase 'JARVIS'. 'Hola JARVIS' remains best-effort because longer local STT transcripts vary by microphone/model.",
            "commands": [
                "scripts/jarvis-wake-setup install --backend vosk --yes",
                'scripts/jarvis-wake-setup configure-env --backend vosk --vosk-model-path "$HOME/.hermes/models/vosk/vosk-model-small-es-0.42"',
                "scripts/jarvis-wake-listener run",
            ],
        },
        "security": {
            "raw_audio_storage_enabled": False,
            "cloud_audio_upload": False,
            "unknown_binary_blob_download": False,
            "secrets_written": False,
        },
    }


def run_install(
    *,
    backend: str,
    yes: bool,
    env: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    status = build_wake_setup_status(backend=backend, env=env)
    packages = status["dependency_install"]["packages"]
    if not yes:
        return {
            **status,
            "install_attempted": False,
            "spanish_summary": "No instalo nada sin --yes. Ejecuta el comando pip mostrado si quieres instalar dependencias Python.",
        }
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", *packages],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        **build_wake_setup_status(backend=backend, env=env),
        "install_attempted": True,
        "install_result": {
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-2000:],
            "stderr_tail": result.stderr[-2000:],
            "model_downloaded": False,
            "unknown_binary_blob_downloaded_by_script": False,
        },
        "spanish_summary": "Dependencias Python instaladas; configura el modelo local y ejecuta scripts/jarvis-wake-listener run."
        if result.returncode == 0
        else "No pude instalar dependencias automáticamente. Usa el comando pip mostrado o instala el backend manualmente.",
    }


def configure_env(
    *,
    backend: str,
    openwakeword_model_path: str = "",
    vosk_model_path: str = "",
    env_path: str = "",
) -> Dict[str, Any]:
    updates = _safe_env_updates(
        backend=backend,
        openwakeword_model_path=openwakeword_model_path,
        vosk_model_path=vosk_model_path,
    )
    if not updates:
        return {
            "schema_version": WAKE_SETUP_SCHEMA_VERSION,
            "status": "no_changes",
            "spanish_summary": "No escribí .env porque falta backend o ruta de modelo.",
            "safe_keys_only": True,
        }
    written = _write_env_values(_env_file_path(env_path), updates)
    return {
        "schema_version": WAKE_SETUP_SCHEMA_VERSION,
        "status": "written",
        "env": written,
        "spanish_summary": "Variables de wake escritas. scripts/jarvis-start, scripts/jarvis-doctor y scripts/jarvis-wake-listener las leerán en una terminal nueva.",
        "safe_keys_only": True,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="JARVIS Phase 12 wake setup helper")
    parser.add_argument("command", choices=("status", "install", "configure-env"))
    parser.add_argument("--backend", choices=("auto", "openwakeword", "vosk"), default="auto")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--openwakeword-model-path", default="")
    parser.add_argument("--vosk-model-path", default="")
    parser.add_argument("--env-path", default="")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "install":
        payload = run_install(backend=args.backend, yes=args.yes)
    elif args.command == "configure-env":
        payload = configure_env(
            backend=args.backend,
            openwakeword_model_path=args.openwakeword_model_path,
            vosk_model_path=args.vosk_model_path,
            env_path=args.env_path,
        )
    else:
        payload = build_wake_setup_status(backend=args.backend)
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
