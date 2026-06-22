from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from hermes_constants import display_hermes_home, get_hermes_home
from jarvis.phase_12_ports import (
    BACKEND_BASE_URL,
    BACKEND_HOST,
    BACKEND_PORT,
    FRONTEND_BASE_URL,
    FRONTEND_HOST,
    FRONTEND_PORT,
    JARVIS_FRONTEND_URL,
    MOBILE_FRONTEND_URL,
    frontend_url,
    url_uses_frontend_port,
)
from jarvis.phase_12_wake_config import merge_persisted_wake_env
from jarvis.phase_12_wake_listener import build_wake_listener_status


STARTUP_SCHEMA_VERSION = "jarvis.phase_12.startup_command.v1"


def runtime_dir() -> Path:
    path = get_hermes_home() / "runtime" / "phase12"
    path.mkdir(parents=True, exist_ok=True)
    return path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def pid_file() -> Path:
    return runtime_dir() / "jarvis-processes.json"


def _port_open(host: str, port: int, *, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for_port(host: str, port: int, *, timeout_seconds: float = 8.0) -> bool:
    deadline = time.time() + max(0.1, timeout_seconds)
    while time.time() < deadline:
        if _port_open(host, port):
            return True
        time.sleep(0.2)
    return _port_open(host, port)


def _process_alive(pid: Optional[int]) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _load_pids() -> Dict[str, Any]:
    try:
        return json.loads(pid_file().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": STARTUP_SCHEMA_VERSION, "processes": {}}


def _write_pids(processes: Mapping[str, Any]) -> None:
    payload = {
        "schema_version": STARTUP_SCHEMA_VERSION,
        "updated_at": int(time.time()),
        "hermes_home": display_hermes_home(),
        "processes": dict(processes),
    }
    pid_file().write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _env_summary(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    source = env if env is not None else os.environ
    openrouter_configured = bool(source.get("OPENROUTER_API_KEY") or source.get("JARVIS_OPENROUTER_API_KEY"))
    voice_default_on_raw = str(
        source.get("JARVIS_VOICE_OUTPUT_DEFAULT_ON") or source.get("JARVIS_VOICE_DEFAULT_ON") or ""
    ).strip().lower()
    voice_output_default_enabled = voice_default_on_raw not in {"0", "false", "no", "off", "disabled"}
    return {
        "openrouter": {
            "configured": openrouter_configured,
            "live_calls_enabled": str(
                source.get("JARVIS_OPENROUTER_LIVE_CALLS_ENABLED")
                or source.get("JARVIS_OPENROUTER_LIVE_CALLS")
                or ""
            )
            .strip()
            .lower()
            in {"1", "true", "yes", "on", "enabled"},
            "secret_value_exposed": False,
        },
        "tts": {
            "provider": source.get("JARVIS_VOICE_PROVIDER", "browser_fallback"),
            "voice_output_default_enabled": voice_output_default_enabled,
            "wake_greeting_spoken_by_default": voice_output_default_enabled,
            "piper_binary_configured": bool(source.get("JARVIS_PIPER_BINARY")),
            "piper_jarvis_model_configured": bool(source.get("JARVIS_PIPER_JARVIS_MODEL_PATH")),
            "piper_utron_model_configured": bool(source.get("JARVIS_PIPER_UTRON_MODEL_PATH")),
        },
        "wake": {
            "backend": source.get("JARVIS_WAKE_BACKEND", "auto"),
            "openwakeword_model_configured": bool(source.get("JARVIS_OPENWAKEWORD_MODEL_PATH")),
            "vosk_model_configured": bool(source.get("JARVIS_VOSK_MODEL_PATH")),
            "raw_audio_recording_default": False,
        },
        "remote": {
            "bridge_enabled": str(source.get("JARVIS_REMOTE_BRIDGE_ENABLED", "")).strip().lower()
            in {"1", "true", "yes", "on", "enabled"},
            "mode": source.get("JARVIS_REMOTE_BRIDGE_MODE", "tailscale"),
            "tailscale_url_configured": bool(source.get("JARVIS_TAILSCALE_URL")),
            "public_unauthenticated_exposure": False,
        },
    }


def _detect_lan_ip(env: Optional[Mapping[str, str]] = None) -> str:
    source = env if env is not None else os.environ
    configured = str(source.get("JARVIS_LAN_HOST") or "").strip()
    if configured:
        return configured
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 80))
            candidate = sock.getsockname()[0]
    except OSError:
        candidate = ""
    if candidate and not candidate.startswith("127."):
        return candidate
    return "<PC-LAN-IP>"


def _tailscale_url(env: Optional[Mapping[str, str]] = None) -> str:
    source = env if env is not None else os.environ
    configured = str(source.get("JARVIS_TAILSCALE_URL") or "").strip()
    if configured:
        return configured
    host = str(source.get("JARVIS_TAILSCALE_HOST") or "<tailscale-ip-or-name>").strip()
    return frontend_url("/mobile", host=host)


def _url_summary(env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    lan_ip = _detect_lan_ip(env)
    tailscale = _tailscale_url(env)
    return {
        "backend_api": BACKEND_BASE_URL,
        "frontend_ui": FRONTEND_BASE_URL,
        "pc_jarvis": JARVIS_FRONTEND_URL,
        "pc_mobile": MOBILE_FRONTEND_URL,
        "iphone_lan": frontend_url("/mobile", host=lan_ip),
        "iphone_tailscale": tailscale,
        "iphone_tailscale_uses_frontend_port": url_uses_frontend_port(tailscale) or "<tailscale" in tailscale,
        "production_static_backend_note": "Si sirves el frontend estático desde el backend, documenta esa ruta aparte; en desarrollo abre 5173.",
    }


def _next_actions(
    *,
    backend_open: bool,
    frontend_open: bool,
    wake_status: Mapping[str, Any],
    env_summary: Mapping[str, Any],
    urls: Mapping[str, Any],
) -> List[str]:
    actions: List[str] = []
    if not backend_open or not frontend_open:
        actions.append("Ejecuta scripts/jarvis-start para levantar backend 9119 y frontend 5173.")
    if backend_open and frontend_open:
        actions.append(f"Abre JARVIS en este PC: {urls['pc_jarvis']}.")
    if not wake_status.get("state", {}).get("real_microphone_wake_available"):
        actions.append(str(wake_status.get("diagnostic", {}).get("spanish") or "Ejecuta scripts/jarvis-wake-setup status."))
    elif not wake_status.get("state", {}).get("wake_active"):
        actions.append("Ejecuta scripts/jarvis-wake-listener run o scripts/jarvis-start para activar wake real.")
    if not env_summary.get("openrouter", {}).get("configured"):
        actions.append("Configura OPENROUTER_API_KEY y activa JARVIS_OPENROUTER_LIVE_CALLS_ENABLED=true solo cuando quieras llamadas reales.")
    if not env_summary.get("remote", {}).get("bridge_enabled"):
        actions.append(f"Para iPhone fuera de casa, activa Tailscale y abre {urls['iphone_tailscale']}.")
    return actions


def doctor(*, env: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    effective_env = merge_persisted_wake_env(env)
    pids = _load_pids().get("processes", {})
    backend_pid = _safe_pid(pids.get("backend", {}).get("pid"))
    frontend_pid = _safe_pid(pids.get("frontend", {}).get("pid"))
    wake_pid = _safe_pid(pids.get("wake_listener", {}).get("pid"))
    backend_open = _port_open(BACKEND_HOST, BACKEND_PORT)
    frontend_open = _port_open(FRONTEND_HOST, FRONTEND_PORT)
    wake_status = build_wake_listener_status(env=effective_env, process_pid=wake_pid)
    env_summary = _env_summary(effective_env)
    urls = _url_summary(effective_env)
    npm = _npm_binary()
    return {
        "schema_version": STARTUP_SCHEMA_VERSION,
        "status": "ok" if backend_open and frontend_open else "needs_attention",
        "spanish_summary": _doctor_spanish_summary(backend_open=backend_open, frontend_open=frontend_open),
        "commands": {
            "start": "scripts/jarvis-start",
            "stop": "scripts/jarvis-stop",
            "doctor": "scripts/jarvis-doctor",
            "wake_listener": "scripts/jarvis-wake-listener",
            "wake_setup": "scripts/jarvis-wake-setup",
        },
        "repo_root": str(repo_root()),
        "hermes_home": display_hermes_home(),
        "pid_file": str(pid_file()),
        "ports": {
            "backend": BACKEND_PORT,
            "frontend": FRONTEND_PORT,
            "backend_url": BACKEND_BASE_URL,
            "frontend_url": FRONTEND_BASE_URL,
            "frontend_proxy_target": BACKEND_BASE_URL,
            "port_confusion_fixed": True,
            "backend_open": backend_open,
            "frontend_open": frontend_open,
        },
        "urls": urls,
        "processes": {
            "backend": {"pid": backend_pid, "alive": _process_alive(backend_pid), "port_open": backend_open},
            "frontend": {"pid": frontend_pid, "alive": _process_alive(frontend_pid), "port_open": frontend_open},
            "wake_listener": {"pid": wake_pid, "alive": _process_alive(wake_pid), "real_microphone_wake_active": wake_status["state"]["wake_active"]},
        },
        "dependencies": {
            "python": sys.executable,
            "uvicorn_module": _module_available("uvicorn"),
            "npm": npm or "",
            "npm_available": bool(npm),
            "tailscale_cli": bool(shutil.which("tailscale")),
            "piper_cli": bool(shutil.which(str(effective_env.get("JARVIS_PIPER_BINARY", "piper")))),
            "microphone": wake_status["microphone"],
            "wake_engine": wake_status["engine"],
            "wake_backend_status": wake_status["backends"],
            "no_dependency_install_performed": True,
        },
        "config": env_summary,
        "wake_listener": wake_status,
        "next_actions": _next_actions(
            backend_open=backend_open,
            frontend_open=frontend_open,
            wake_status=wake_status,
            env_summary=env_summary,
            urls=urls,
        ),
        "security": {
            "bind_host": BACKEND_HOST,
            "public_internet_bind_default": False,
            "raw_pc_port_opened_to_internet": False,
            "frontend_executes_hermes_directly": False,
            "mobile_executes_hermes_directly": False,
            "secrets_exposed": False,
        },
    }


def start(*, start_backend: bool = True, start_frontend: bool = True, start_wake_listener: bool = True) -> Dict[str, Any]:
    root = repo_root()
    logs_dir = runtime_dir()
    pids = _load_pids().get("processes", {})
    started: Dict[str, Any] = {}
    effective_env = merge_persisted_wake_env()

    if start_backend:
        if _port_open(BACKEND_HOST, BACKEND_PORT):
            started["backend"] = {"status": "already_running", "port": BACKEND_PORT}
        else:
            proc = _spawn(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "jarvis.api.app:app",
                    "--host",
                    BACKEND_HOST,
                    "--port",
                    str(BACKEND_PORT),
                ],
                cwd=root,
                log_path=logs_dir / "backend.log",
            )
            pids["backend"] = {"pid": proc.pid, "port": BACKEND_PORT, "log": str(logs_dir / "backend.log")}
            started["backend"] = {"status": "started", "pid": proc.pid, "port": BACKEND_PORT}
            started["backend"]["port_open_after_wait"] = _wait_for_port(BACKEND_HOST, BACKEND_PORT)

    if start_frontend:
        if _port_open(FRONTEND_HOST, FRONTEND_PORT):
            started["frontend"] = {"status": "already_running", "port": FRONTEND_PORT}
        else:
            npm = _npm_binary()
            if npm and (root / "web" / "package.json").exists():
                proc = _spawn(
                    [
                        npm,
                        "--prefix",
                        "web",
                        "run",
                        "dev",
                        "--",
                        "--host",
                        FRONTEND_HOST,
                        "--port",
                        str(FRONTEND_PORT),
                    ],
                    cwd=root,
                    log_path=logs_dir / "frontend.log",
                )
                pids["frontend"] = {"pid": proc.pid, "port": FRONTEND_PORT, "log": str(logs_dir / "frontend.log")}
                started["frontend"] = {"status": "started", "pid": proc.pid, "port": FRONTEND_PORT}
                started["frontend"]["port_open_after_wait"] = _wait_for_port(FRONTEND_HOST, FRONTEND_PORT)
            else:
                started["frontend"] = {"status": "not_started", "reason": "npm no está disponible o falta web/package.json"}

    if start_wake_listener:
        wake_pid = _safe_pid(pids.get("wake_listener", {}).get("pid"))
        wake_status = build_wake_listener_status(env=effective_env, process_pid=wake_pid)
        if wake_status["state"]["wake_active"]:
            started["wake_listener"] = {
                "status": "already_running",
                "pid": wake_pid,
                "real_microphone_wake_active": True,
                "backend": wake_status["state"]["selected_backend"],
            }
        elif wake_status["state"]["real_microphone_wake_available"]:
            proc = _spawn(
                [
                    sys.executable,
                    "-m",
                    "jarvis.phase_12_wake_listener",
                    "run",
                    "--backend-url",
                    BACKEND_BASE_URL,
                ],
                cwd=root,
                log_path=logs_dir / "wake-listener.log",
                extra_env=effective_env,
            )
            pids["wake_listener"] = {"pid": proc.pid, "log": str(logs_dir / "wake-listener.log")}
            started["wake_listener"] = {
                "status": "started",
                "pid": proc.pid,
                "real_microphone_wake_active": True,
                "backend": wake_status["state"]["selected_backend"],
            }
        else:
            started["wake_listener"] = {
                "status": "not_started",
                "real_microphone_wake_active": False,
                "reason": wake_status["diagnostic"]["spanish"],
                "missing": wake_status["diagnostic"]["missing"],
            }

    _write_pids(pids)
    status = doctor(env=effective_env)
    wake_listener_running = bool(status["processes"]["wake_listener"]["alive"])
    wake_active = bool(status["wake_listener"]["state"]["wake_active"])
    voice_default_on = bool(status["config"]["tts"].get("voice_output_default_enabled", True))
    final_state = {
        "backend_running": bool(status["ports"]["backend_open"]),
        "frontend_running": bool(status["ports"]["frontend_open"]),
        "wake_listener_running": wake_listener_running,
        "wake_active": wake_active,
        "wake_running": wake_active,
        "voice_default_on": voice_default_on,
        "backend_url": status["urls"]["backend_api"],
        "frontend_url": status["urls"]["frontend_ui"],
        "pc_url": status["urls"]["pc_jarvis"],
        "iphone_lan_url": status["urls"]["iphone_lan"],
        "iphone_tailscale_url": status["urls"]["iphone_tailscale"],
        "wake_reason": "" if wake_active else status["wake_listener"]["diagnostic"]["spanish"],
    }
    missing = []
    if not final_state["backend_running"]:
        missing.append("backend 9119 no responde")
    if not final_state["frontend_running"]:
        missing.append("frontend 5173 no responde")
    if not final_state["wake_active"]:
        missing.append(f"wake por micrófono no está activo: {final_state['wake_reason']}")
    missing_text = " Pendiente: " + "; ".join(missing) + "." if missing else ""
    return {
        "schema_version": STARTUP_SCHEMA_VERSION,
        "status": "started",
        "spanish_summary": (
            "Estado final de JARVIS: "
            f"backend running={str(final_state['backend_running']).lower()}, "
            f"frontend running={str(final_state['frontend_running']).lower()}, "
            f"wake listener running={str(final_state['wake_listener_running']).lower()}, "
            f"wake active={str(final_state['wake_active']).lower()}, "
            f"voice default on={str(final_state['voice_default_on']).lower()}. "
            f"PC URL: {final_state['pc_url']}. iPhone LAN: {final_state['iphone_lan_url']}."
            f"{missing_text}"
        ),
        "final_state": final_state,
        "started": started,
        "urls": status["urls"],
        "wake_status": status["wake_listener"],
        "doctor": status,
    }


def stop() -> Dict[str, Any]:
    payload = _load_pids()
    pids = payload.get("processes", {})
    stopped: Dict[str, Any] = {}
    for name in ("wake_listener", "frontend", "backend"):
        pid = _safe_pid(pids.get(name, {}).get("pid"))
        if pid and _process_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                stopped[name] = {"status": "stop_requested", "pid": pid}
            except OSError as exc:
                stopped[name] = {"status": "stop_failed", "pid": pid, "error": type(exc).__name__}
        else:
            stopped[name] = {"status": "not_running", "pid": pid}
    _write_pids({})
    return {
        "schema_version": STARTUP_SCHEMA_VERSION,
        "status": "stopped",
        "spanish_summary": "He pedido parar los procesos conocidos de JARVIS. Si un puerto sigue ocupado, lo arrancó otro proceso.",
        "stopped": stopped,
        "doctor": doctor(),
    }


def _spawn(
    argv: List[str],
    *,
    cwd: Path,
    log_path: Path,
    extra_env: Optional[Mapping[str, str]] = None,
) -> subprocess.Popen:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("ab")
    env = os.environ.copy()
    if extra_env:
        env.update({key: str(value) for key, value in extra_env.items()})
    env.setdefault("PYTHONPATH", str(cwd))
    return subprocess.Popen(
        argv,
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        close_fds=os.name != "nt",
    )


def _safe_pid(value: Any) -> Optional[int]:
    try:
        pid = int(value)
    except (TypeError, ValueError):
        return None
    return pid if pid > 0 else None


def _module_available(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def _npm_binary() -> str:
    return shutil.which("npm.cmd" if os.name == "nt" else "npm") or ""


def _doctor_spanish_summary(*, backend_open: bool, frontend_open: bool) -> str:
    if backend_open and frontend_open:
        return f"JARVIS está levantado: backend API 9119 y frontend 5173 responden. Abre {JARVIS_FRONTEND_URL}."
    if backend_open and not frontend_open:
        return "El backend API responde en 9119, pero el frontend 5173 no está activo; /jarvis usable está en el frontend."
    if frontend_open and not backend_open:
        return "El frontend responde en 5173, pero el backend API 9119 no está activo."
    return "JARVIS no está levantado todavía. Ejecuta scripts/jarvis-start."


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="JARVIS Phase 12 startup controller")
    parser.add_argument("command", choices=("start", "stop", "doctor"))
    parser.add_argument("--backend-only", action="store_true")
    parser.add_argument("--frontend-only", action="store_true")
    parser.add_argument("--no-wake-listener", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "start":
        result = start(
            start_backend=not args.frontend_only,
            start_frontend=not args.backend_only,
            start_wake_listener=not args.no_wake_listener and not args.frontend_only,
        )
    elif args.command == "stop":
        result = stop()
    else:
        result = doctor()
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
