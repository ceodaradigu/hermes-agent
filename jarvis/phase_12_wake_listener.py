from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import os
import queue
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional
from urllib import request as urllib_request

from hermes_constants import get_hermes_home
from jarvis.phase_12_ports import BACKEND_BASE_URL
from jarvis.phase_12_wake_config import merge_persisted_wake_env


WAKE_LISTENER_SCHEMA_VERSION = "jarvis.phase_12.real_microphone_wake_listener.v1"
WAKE_PHRASE_TEXT = "JARVIS"
WAKE_BACKENDS = ("openwakeword", "vosk")
PRIMARY_WAKE_PHRASE = "jarvis"
EXPERIMENTAL_WAKE_ALIASES = ("hola jarvis",)
WAKE_PHRASES = ("hola jarvis", "jarvis")
WAKE_MATCH_SCHEMA_VERSION = "jarvis.phase_12.wake_phrase_match.v1"
WAKE_ALIASES = {
    "hola jarvis": (
        "hola jarvis",
        "ola jarvis",
        "hola y arvis",
        "hola yarvis",
        "hola servis",
        "hola jarbis",
        "hola jervis",
        "hola travis",
        "ola travis",
        "hola través",
        "ola través",
        "hola traves",
        "ola traves",
        "hola travez",
        "ola travez",
        "hola trapis",
        "ola trapis",
        "hola jarbi",
        "ola jarbi",
        "hola yervis",
        "ola yervis",
        "ola jervis",
        "ola yarvis",
    ),
    "jarvis": (
        "jarvis",
        "yarvis",
        "jervis",
        "jarbis",
        "servis",
    ),
}
WAKE_DISPLAY_NAMES = {"hola jarvis": "Hola JARVIS", "jarvis": "JARVIS"}
WAKE_FUZZY_THRESHOLDS = {"hola jarvis": 0.80, "jarvis": 0.84}
GREETING_WAKE_TOKENS = {"hola", "ola"}
JARVIS_WAKE_TOKENS = {
    "jarvis",
    "travis",
    "jervis",
    "yarvis",
    "servis",
    "jarbis",
    "traves",
    "travez",
    "jarbi",
    "yervis",
}


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _env_bool(name: str, default: bool = False, *, env: Optional[Mapping[str, str]] = None) -> bool:
    source = merge_persisted_wake_env(env)
    raw = str(source.get(name, "")).strip().casefold()
    if raw in {"1", "true", "yes", "on", "enabled"}:
        return True
    if raw in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _process_alive(pid: Optional[int]) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _runtime_pid_file() -> Path:
    return get_hermes_home() / "runtime" / "phase12" / "jarvis-processes.json"


def _known_wake_pid() -> Optional[int]:
    try:
        payload = json.loads(_runtime_pid_file().read_text(encoding="utf-8"))
        value = payload.get("processes", {}).get("wake_listener", {}).get("pid")
        pid = int(value)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return pid if pid > 0 else None


def _openwakeword_model_path(env: Mapping[str, str]) -> str:
    return str(env.get("JARVIS_OPENWAKEWORD_MODEL_PATH") or "").strip()


def _vosk_model_path(env: Mapping[str, str]) -> str:
    return str(env.get("JARVIS_VOSK_MODEL_PATH") or "").strip()


def _requested_backend(env: Mapping[str, str]) -> str:
    requested = str(env.get("JARVIS_WAKE_BACKEND") or "auto").strip().casefold()
    return requested if requested in {"auto", *WAKE_BACKENDS} else "auto"


def _path_exists(value: str) -> bool:
    return bool(value and Path(value).expanduser().exists())


def _probe_microphone(sounddevice_available: bool) -> Dict[str, Any]:
    if not sounddevice_available:
        return {"status": "unavailable", "available": False, "reason": "sounddevice_missing"}
    result: Dict[str, Any] = {}
    error: Dict[str, Any] = {}

    def query() -> None:
        try:
            import sounddevice as sd  # type: ignore

            result["devices"] = sd.query_devices()
        except Exception as exc:
            error["type"] = type(exc).__name__

    thread = threading.Thread(target=query, name="jarvis-wake-mic-probe", daemon=True)
    thread.start()
    thread.join(0.75)
    if thread.is_alive():
        return {"status": "unknown", "available": None, "reason": "microphone_probe_timeout"}
    if error:
        return {"status": "unknown", "available": None, "reason": str(error["type"])}
    try:
        devices = result.get("devices", [])
        if isinstance(devices, Mapping):
            devices = [devices]
        input_count = sum(1 for device in devices if int(device.get("max_input_channels", 0) or 0) > 0)
        return {
            "status": "available" if input_count > 0 else "unavailable",
            "available": input_count > 0,
            "input_device_count": input_count,
            "reason": "" if input_count > 0 else "no_input_devices_detected",
        }
    except Exception as exc:
        return {"status": "unknown", "available": None, "reason": type(exc).__name__}


def _backend_statuses(env: Mapping[str, str]) -> Dict[str, Dict[str, Any]]:
    openwakeword = _module_available("openwakeword")
    sounddevice = _module_available("sounddevice")
    numpy = _module_available("numpy")
    vosk = _module_available("vosk")
    oww_model = _openwakeword_model_path(env)
    vosk_model = _vosk_model_path(env)

    oww_missing = []
    if not openwakeword:
        oww_missing.append("openwakeword")
    if not sounddevice:
        oww_missing.append("sounddevice")
    if not numpy:
        oww_missing.append("numpy")
    if not oww_model:
        oww_missing.append("JARVIS_OPENWAKEWORD_MODEL_PATH")
    elif not _path_exists(oww_model):
        oww_missing.append("modelo openWakeWord configurado")

    vosk_missing = []
    if not vosk:
        vosk_missing.append("vosk")
    if not sounddevice:
        vosk_missing.append("sounddevice")
    if not vosk_model:
        vosk_missing.append("JARVIS_VOSK_MODEL_PATH")
    elif not _path_exists(vosk_model):
        vosk_missing.append("modelo Vosk configurado")

    return {
        "openwakeword": {
            "name": "openWakeWord",
            "available": not oww_missing,
            "package_available": openwakeword,
            "sounddevice_available": sounddevice,
            "numpy_available": numpy,
            "missing": oww_missing,
            "python_packages": ["openwakeword", "sounddevice", "numpy"],
            "model_path": oww_model,
            "model_path_configured": bool(oww_model),
            "model_path_exists": _path_exists(oww_model),
            "wake_model_required": True,
            "custom_hola_jarvis_model_required": True,
            "phrase_specific_model_required": True,
            "spanish_hola_jarvis_support": "requires_custom_model",
            "cloud_required": False,
            "raw_audio_stored": False,
        },
        "vosk": {
            "name": "Vosk local STT wake",
            "available": not vosk_missing,
            "package_available": vosk,
            "sounddevice_available": sounddevice,
            "missing": vosk_missing,
            "python_packages": ["vosk", "sounddevice"],
            "model_path": vosk_model,
            "model_path_configured": bool(vosk_model),
            "model_path_exists": _path_exists(vosk_model),
            "wake_model_required": False,
            "language_model_required": True,
            "phrase_specific_model_required": False,
            "spanish_hola_jarvis_support": "supported_by_local_stt_model_when_spanish_model_is_configured",
            "cloud_required": False,
            "raw_audio_stored": False,
        },
    }


def _select_backend(statuses: Mapping[str, Mapping[str, Any]], requested: str) -> str:
    if requested in WAKE_BACKENDS:
        return requested
    if statuses["openwakeword"]["available"]:
        return "openwakeword"
    if statuses["vosk"]["available"]:
        return "vosk"
    return "unavailable"


def _actionable_wake_instructions(*, selected_backend: str, missing: Iterable[str]) -> Dict[str, Any]:
    missing_list = list(missing)
    return {
        "spanish": (
            "Wake por micrófono no está activo. Falta instalar/configurar el motor de wake. "
            "Ejecuta scripts/jarvis-wake-setup status y luego scripts/jarvis-wake-setup install --backend vosk --yes "
            "o configura JARVIS_OPENWAKEWORD_MODEL_PATH para openWakeWord."
        ),
        "english": (
            "Microphone wake is not active. Install/configure a wake backend. "
            "Run scripts/jarvis-wake-setup status, then scripts/jarvis-wake-setup install --backend vosk --yes "
            "or configure JARVIS_OPENWAKEWORD_MODEL_PATH for openWakeWord."
        ),
        "selected_backend": selected_backend,
        "missing": missing_list,
        "setup_command": "scripts/jarvis-wake-setup status",
        "install_vosk_command": "scripts/jarvis-wake-setup install --backend vosk --yes",
        "install_openwakeword_command": "scripts/jarvis-wake-setup install --backend openwakeword --yes",
        "env_examples": [
            "JARVIS_WAKE_BACKEND=vosk",
            "JARVIS_VOSK_MODEL_PATH=/path/to/vosk-model-small-es",
            "JARVIS_WAKE_BACKEND=openwakeword",
            "JARVIS_OPENWAKEWORD_MODEL_PATH=/path/to/hola-jarvis.onnx",
        ],
    }


def build_wake_listener_status(
    *,
    env: Optional[Mapping[str, str]] = None,
    process_pid: Optional[int] = None,
) -> Dict[str, Any]:
    source = merge_persisted_wake_env(env)
    statuses = _backend_statuses(source)
    requested = _requested_backend(source)
    selected_backend = _select_backend(statuses, requested)
    selected_status = statuses.get(selected_backend, {}) if selected_backend != "unavailable" else {}
    missing = list(selected_status.get("missing", []))
    if selected_backend == "unavailable":
        missing = sorted(set(statuses["openwakeword"]["missing"] + statuses["vosk"]["missing"]))
    sounddevice = _module_available("sounddevice")
    mic = _probe_microphone(sounddevice)
    real_available = selected_backend != "unavailable" and bool(selected_status.get("available"))
    pid = process_pid if process_pid is not None else _known_wake_pid()
    pid_alive = _process_alive(pid)
    wake_active = bool(real_available and pid_alive)
    if wake_active:
        spanish = f"Wake real está activo con micrófono local usando {selected_backend}; no guardo audio bruto."
        english = f"Real microphone wake is active with {selected_backend}; raw audio is not stored."
    elif real_available:
        spanish = f"Wake real está disponible con {selected_backend}, pero no está corriendo. Ejecuta scripts/jarvis-wake-listener run."
        english = f"Real microphone wake is available with {selected_backend} but not running. Run scripts/jarvis-wake-listener run."
    else:
        missing_text = ", ".join(missing) if missing else "dependencias de micrófono"
        spanish = f"Wake por micrófono no está activo. Falta instalar/configurar {missing_text}. Ejecuta scripts/jarvis-wake-setup status."
        english = f"Microphone wake is not active because {missing_text} is missing or not configured. Run scripts/jarvis-wake-setup status."
    instructions = _actionable_wake_instructions(selected_backend=selected_backend, missing=missing)

    return {
        "schema_version": WAKE_LISTENER_SCHEMA_VERSION,
        "state": {
            "mode": "microphone_wake_listener_optional",
            "requested_backend": requested,
            "selected_backend": selected_backend,
            "real_microphone_wake_available": real_available,
            "wake_active": wake_active,
            "process_pid": pid or 0,
            "process_alive": pid_alive,
            "raw_audio_storage_enabled": False,
            "continuous_full_transcription": False,
            "wake_snippet_transcription_local_only": selected_backend == "vosk",
            "transcript_ingest_endpoint_is_test_only": True,
            "hidden_microphone_capture": False,
        },
        "microphone": {
            "sounddevice_available": sounddevice,
            "status": mic["status"],
            "available": mic["available"],
            "input_device_count": mic.get("input_device_count", 0),
            "reason": mic.get("reason", ""),
            "raw_audio_stored": False,
        },
        "engine": {
            "name": selected_status.get("name", "unavailable"),
            "selected_backend": selected_backend,
            "openwakeword_available": statuses["openwakeword"]["available"],
            "openwakeword_package_available": statuses["openwakeword"]["package_available"],
            "vosk_available": statuses["vosk"]["available"],
            "vosk_package_available": statuses["vosk"]["package_available"],
            "numpy_available": _module_available("numpy"),
            "model_path_configured": bool(selected_status.get("model_path_configured", False)),
            "model_path_exists": bool(selected_status.get("model_path_exists", False)),
            "custom_primary_wake_model_required": selected_backend in {"openwakeword", "unavailable"},
            "custom_hola_jarvis_model_required": selected_backend in {"openwakeword", "unavailable"},
            "phrase_specific_model_required": bool(selected_status.get("phrase_specific_model_required", False)),
            "wake_model_status": "not_required_for_stt_fallback"
            if selected_backend == "vosk"
            else "configured"
            if selected_status.get("model_path_exists")
            else "missing",
            "language_model_status": "configured" if selected_backend == "vosk" and selected_status.get("model_path_exists") else "missing" if selected_backend == "vosk" else "not_required_for_openwakeword",
        },
        "backends": statuses,
        "privacy": {
            "raw_audio_storage_enabled": False,
            "raw_audio_recording_supported_by_this_listener": False,
            "raw_audio_recording_requires_explicit_opt_in": True,
            "continuous_full_transcription_by_default": False,
            "wake_separate_from_active_transcription": True,
        },
        "diagnostic": {
            "status": "active" if wake_active else "available" if real_available else "missing_dependencies",
            "missing": missing,
            "spanish": spanish,
            "english": english,
            "actionable": instructions,
        },
        "wake_contract": {
            "primary_wake_phrase": "JARVIS",
            "primary_wake_phrase_required": True,
            "primary_wake_phrase_guaranteed_for_phase12": True,
            "experimental_aliases": ["Hola JARVIS"],
            "experimental_aliases_best_effort": True,
            "experimental_alias_note": "Hola JARVIS queda como alias experimental; puede variar según micrófono, modelo y transcripción local.",
        },
        "commands": {
            "status": "scripts/jarvis-wake-listener status",
            "run": "scripts/jarvis-wake-listener run",
            "match": 'scripts/jarvis-wake-listener match "jarvis"',
            "simulate": 'scripts/jarvis-wake-listener simulate "jarvis"',
            "experimental_alias_match": 'scripts/jarvis-wake-listener match "hola jarvis"',
            "experimental_alias_simulate": 'scripts/jarvis-wake-listener simulate "hola travis"',
            "setup": "scripts/jarvis-wake-setup status",
            "test_transcript_ingest": "curl -X POST http://127.0.0.1:9119/mark-3/phase-12/always-on/ingest-transcript",
        },
        "metadata_only": True,
    }


def _post_wake_event(*, backend_url: str, text: str, confidence: float, source: str) -> Dict[str, Any]:
    endpoint = f"{backend_url.rstrip('/')}/mark-3/phase-12/always-on/ingest-transcript"
    payload = json.dumps(
        {
            "text": text,
            "confidence": max(0.0, min(1.0, float(confidence))),
            "source": source,
            "open_jarvis": True,
        }
    ).encode("utf-8")
    req = urllib_request.Request(endpoint, data=payload, method="POST", headers={"Content-Type": "application/json"})
    with urllib_request.urlopen(req, timeout=6) as response:
        return json.loads(response.read().decode("utf-8"))


def _activation_debug_from_backend(posted: Mapping[str, Any]) -> Dict[str, Any]:
    greeting = dict(posted.get("greeting") or {})
    open_decision = dict(posted.get("open_decision") or {})
    return {
        "posted": True,
        "backend_status": posted.get("status", ""),
        "opened_jarvis": posted.get("opened_jarvis", False),
        "browser_open_reason": open_decision.get("reason", ""),
        "browser_open_skipped": posted.get("opened_jarvis") is False,
        "assistant_text": posted.get("assistant_text", ""),
        "greeting_created": bool(greeting),
        "greeting_id": greeting.get("greeting_id", ""),
        "greeting_status": greeting.get("status", ""),
        "wake_phrase_can_approve": posted.get("wake_phrase_can_approve", False),
        "wake_phrase_can_execute": greeting.get("wake_phrase_can_execute", False),
        "approval_granted": posted.get("approval_granted", False),
        "did_execute_action": greeting.get("did_execute_action", False),
    }


def simulate_wake_phrase(*, phrase: str, backend_url: str = BACKEND_BASE_URL) -> Dict[str, Any]:
    """Exercise the listener->backend activation path without microphone capture."""

    match = match_wake_phrase(phrase)
    payload: Dict[str, Any] = {
        "schema_version": WAKE_MATCH_SCHEMA_VERSION,
        "event": "wake_simulation",
        "mode": "same_backend_activation_path_without_microphone",
        "raw_transcript": phrase,
        "normalized_transcript": match["normalized_transcript"],
        "token_candidates": match["token_candidates"],
        "accepted": match["accepted"],
        "matched_wake_phrase": match["matched_wake_phrase"],
        "matched_wake_phrase_kind": match["matched_wake_phrase_kind"],
        "primary_wake_phrase": match["primary_wake_phrase"],
        "experimental_aliases": match["experimental_aliases"],
        "experimental_aliases_best_effort": match["experimental_aliases_best_effort"],
        "confidence": match["confidence"],
        "threshold": match["threshold"],
        "reason": match["reason"],
        "posted": False,
        "raw_audio_stored": False,
        "wake_phrase_can_approve": False,
        "wake_phrase_can_execute": False,
        "did_execute_action": False,
    }
    if not match["accepted"]:
        payload["status"] = "rejected"
        payload["backend_status"] = "not_posted"
        return payload

    try:
        posted = _post_wake_event(
            backend_url=backend_url,
            text=phrase,
            confidence=float(match["confidence"]),
            source="simulated_wake_listener",
        )
    except Exception as exc:
        payload.update({"status": "post_failed", "error": type(exc).__name__})
        return payload

    payload.update({"status": "posted", **_activation_debug_from_backend(posted), "backend_response": posted})
    return payload


def _run_transcript_file_loop(*, path: Path, backend_url: str, once: bool) -> int:
    offset = 0
    print(
        json.dumps(
            {
                "schema_version": WAKE_LISTENER_SCHEMA_VERSION,
                "mode": "test_transcript_file",
                "warning": "Este modo no es wake real de micrófono; solo sirve para pruebas locales.",
                "raw_audio_storage_enabled": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )
    while True:
        if path.exists():
            data = path.read_text(encoding="utf-8")
            for line in data[offset:].splitlines():
                text = line.strip()
                if text:
                    try:
                        _post_wake_event(backend_url=backend_url, text=text, confidence=1.0, source="test_transcript_file")
                    except Exception as exc:
                        print(json.dumps({"status": "post_failed", "error": type(exc).__name__}, sort_keys=True), flush=True)
            offset = len(data)
        if once:
            return 0
        time.sleep(0.5)


def _run_openwakeword_loop(*, backend_url: str, env: Mapping[str, str]) -> int:
    status = build_wake_listener_status(env=env)
    if status["state"]["selected_backend"] != "openwakeword" or not status["backends"]["openwakeword"]["available"]:
        print(json.dumps(status, ensure_ascii=False, sort_keys=True), flush=True)
        return 2

    try:
        from openwakeword.model import Model  # type: ignore
        import numpy as np  # type: ignore
        import sounddevice as sd  # type: ignore
    except Exception as exc:
        payload = {
            **status,
            "diagnostic": {
                **status["diagnostic"],
                "status": "import_failed",
                "spanish": f"Wake real no está activo porque falló importar el motor local: {type(exc).__name__}.",
                "english": f"Real wake is not active because the local engine import failed: {type(exc).__name__}.",
            },
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        return 2

    model_path = str(Path(_openwakeword_model_path(env)).expanduser())
    threshold = float(env.get("JARVIS_OPENWAKEWORD_THRESHOLD") or 0.5)
    debounce_seconds = float(env.get("JARVIS_WAKE_DEBOUNCE_SECONDS") or 2.5)
    sample_rate = int(env.get("JARVIS_WAKE_SAMPLE_RATE") or 16000)
    block_size = int(env.get("JARVIS_WAKE_BLOCK_SIZE") or 1280)
    audio_queue: "queue.Queue[Any]" = queue.Queue(maxsize=8)
    last_wake = 0.0

    def callback(indata: Any, _frames: int, _time_info: Any, _status: Any) -> None:
        try:
            audio = np.asarray(indata).reshape(-1).astype(np.int16).copy()
            audio_queue.put_nowait(audio)
        except queue.Full:
            return

    model = Model(wakeword_models=[model_path])
    print(
        json.dumps(
            {
                "schema_version": WAKE_LISTENER_SCHEMA_VERSION,
                "status": "running",
                "engine": "openWakeWord",
                "wake_phrase": WAKE_PHRASE_TEXT,
                "raw_audio_storage_enabled": False,
                "continuous_full_transcription": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16", blocksize=block_size, callback=callback):
        while True:
            audio = audio_queue.get()
            predictions = model.predict(audio)
            score = max((float(value) for value in dict(predictions).values()), default=0.0)
            now = time.monotonic()
            if score >= threshold and now - last_wake >= debounce_seconds:
                last_wake = now
                try:
                    _post_wake_event(
                        backend_url=backend_url,
                        text=WAKE_PHRASE_TEXT,
                        confidence=score,
                        source="openwakeword_microphone",
                    )
                except Exception as exc:
                    print(json.dumps({"status": "post_failed", "error": type(exc).__name__}, sort_keys=True), flush=True)


def _normalize_wake_text(text: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(text or "").casefold())
    without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned_chars = []
    for ch in without_accents:
        category = unicodedata.category(ch)
        cleaned_chars.append(" " if category.startswith("P") or category.startswith("S") else ch)
    cleaned = " ".join("".join(cleaned_chars).split())
    replacements = (
        ("hol a", "hola"),
        ("ho la", "hola"),
        ("j arvis", "jarvis"),
        ("jar vis", "jarvis"),
        ("y arvis", "y arvis"),
    )
    for old, new in replacements:
        cleaned = cleaned.replace(old, new)
    return " ".join(cleaned.split())


def _token_windows(tokens: list[str], *, min_size: int = 1, max_size: int = 3) -> Iterable[str]:
    for size in range(min_size, max_size + 1):
        if len(tokens) < size:
            continue
        for index in range(0, len(tokens) - size + 1):
            yield " ".join(tokens[index : index + size])


def _similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(a=left, b=right).ratio()


def _token_wake_candidates(tokens: list[str]) -> list[Dict[str, Any]]:
    candidates: list[Dict[str, Any]] = []
    for index, token in enumerate(tokens):
        if token not in GREETING_WAKE_TOKENS:
            continue
        for next_index in range(index + 1, min(len(tokens), index + 4)):
            candidate = tokens[next_index]
            best_alias = ""
            best_score = 0.0
            for alias in JARVIS_WAKE_TOKENS:
                score = 1.0 if candidate == alias else _similarity(candidate, alias)
                if score > best_score:
                    best_alias = alias
                    best_score = score
            accepted = best_score >= 0.86
            candidates.append(
                {
                    "greeting_token": token,
                    "candidate_token": candidate,
                    "candidate_index": next_index,
                    "distance": next_index - index,
                    "matched_wake_token": best_alias,
                    "confidence": round(best_score, 4),
                    "accepted": accepted,
                }
            )
    return candidates


def _wake_phrase_kind(canonical: str) -> str:
    return "primary" if canonical == PRIMARY_WAKE_PHRASE else "experimental_alias"


def match_wake_phrase(text: Any) -> Dict[str, Any]:
    normalized = _normalize_wake_text(text)
    tokens = normalized.split()
    windows = list(_token_windows(tokens, max_size=3))
    candidates = windows or ([normalized] if normalized else [])
    best: Dict[str, Any] = {
        "schema_version": WAKE_MATCH_SCHEMA_VERSION,
        "raw_transcript": str(text or ""),
        "normalized_transcript": normalized,
        "accepted": False,
        "matched_wake_phrase": "",
        "matched_wake_phrase_kind": "",
        "primary_wake_phrase": "JARVIS",
        "experimental_aliases": ["Hola JARVIS"],
        "experimental_aliases_best_effort": True,
        "canonical_phrase": "",
        "matched_alias": "",
        "candidate": "",
        "confidence": 0.0,
        "threshold": 0.0,
        "reason": "empty_transcript" if not normalized else "below_threshold",
        "token_candidates": [],
        "raw_audio_stored": False,
    }
    if not normalized:
        return best
    token_candidates = _token_wake_candidates(tokens)
    best["token_candidates"] = token_candidates

    for canonical, aliases in WAKE_ALIASES.items():
        threshold = WAKE_FUZZY_THRESHOLDS[canonical]
        for alias in aliases:
            alias_normalized = _normalize_wake_text(alias)
            for candidate in candidates:
                if candidate == alias_normalized:
                    return {
                        **best,
                        "accepted": True,
                        "matched_wake_phrase": WAKE_DISPLAY_NAMES[canonical],
                        "matched_wake_phrase_kind": _wake_phrase_kind(canonical),
                        "canonical_phrase": canonical,
                        "matched_alias": alias_normalized,
                        "candidate": candidate,
                        "confidence": 1.0,
                        "threshold": threshold,
                        "reason": "alias_exact",
                        "token_candidates": token_candidates,
                    }

    accepted_token = max(
        (candidate for candidate in token_candidates if candidate["accepted"]),
        key=lambda candidate: float(candidate["confidence"]),
        default=None,
    )
    if accepted_token:
        return {
            **best,
            "accepted": True,
            "matched_wake_phrase": WAKE_DISPLAY_NAMES["hola jarvis"],
            "matched_wake_phrase_kind": "experimental_alias",
            "canonical_phrase": "hola jarvis",
            "matched_alias": f"{accepted_token['greeting_token']} {accepted_token['matched_wake_token']}",
            "candidate": f"{accepted_token['greeting_token']} {accepted_token['candidate_token']}",
            "confidence": float(accepted_token["confidence"]),
            "threshold": WAKE_FUZZY_THRESHOLDS["hola jarvis"],
            "reason": "token_greeting_wake",
            "token_candidates": token_candidates,
        }

    for canonical, aliases in WAKE_ALIASES.items():
        threshold = WAKE_FUZZY_THRESHOLDS[canonical]
        for alias in aliases:
            alias_normalized = _normalize_wake_text(alias)
            alias_token_count = len(alias_normalized.split())
            for candidate in candidates:
                candidate_token_count = len(candidate.split())
                if canonical == "jarvis" and candidate_token_count != 1:
                    continue
                if canonical == "hola jarvis" and candidate_token_count not in {2, 3}:
                    continue
                if abs(candidate_token_count - alias_token_count) > 1:
                    continue
                score = _similarity(candidate, alias_normalized)
                if score > float(best["confidence"]):
                    best.update(
                        {
                            "matched_wake_phrase": WAKE_DISPLAY_NAMES[canonical],
                            "matched_wake_phrase_kind": _wake_phrase_kind(canonical),
                            "canonical_phrase": canonical,
                            "matched_alias": alias_normalized,
                            "candidate": candidate,
                            "confidence": round(score, 4),
                            "threshold": threshold,
                            "reason": "fuzzy_phrase",
                        }
                    )

    if float(best["confidence"]) >= float(best["threshold"] or 1.0):
        best["accepted"] = True
    else:
        best["matched_wake_phrase"] = ""
        best["matched_wake_phrase_kind"] = ""
        best["canonical_phrase"] = ""
        best["reason"] = "below_threshold"
    return best


def _contains_wake_phrase(text: Any) -> bool:
    return bool(match_wake_phrase(text)["accepted"])


def _run_vosk_loop(*, backend_url: str, env: Mapping[str, str]) -> int:
    status = build_wake_listener_status(env=env)
    if status["state"]["selected_backend"] != "vosk" or not status["backends"]["vosk"]["available"]:
        print(json.dumps(status, ensure_ascii=False, sort_keys=True), flush=True)
        return 2

    try:
        import sounddevice as sd  # type: ignore
        from vosk import KaldiRecognizer, Model  # type: ignore
    except Exception as exc:
        payload = {
            **status,
            "diagnostic": {
                **status["diagnostic"],
                "status": "import_failed",
                "spanish": f"Wake por micrófono no está activo porque falló importar Vosk/sounddevice: {type(exc).__name__}.",
                "english": f"Microphone wake is not active because Vosk/sounddevice import failed: {type(exc).__name__}.",
            },
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        return 2

    model_path = str(Path(_vosk_model_path(env)).expanduser())
    sample_rate = int(env.get("JARVIS_WAKE_SAMPLE_RATE") or 16000)
    block_size = int(env.get("JARVIS_WAKE_BLOCK_SIZE") or 4000)
    debounce_seconds = float(env.get("JARVIS_WAKE_DEBOUNCE_SECONDS") or 2.5)
    audio_queue: "queue.Queue[bytes]" = queue.Queue(maxsize=12)
    last_wake = 0.0
    last_debug_text = ""

    def callback(indata: Any, _frames: int, _time_info: Any, _status: Any) -> None:
        try:
            audio_queue.put_nowait(bytes(indata))
        except queue.Full:
            return

    model = Model(model_path)
    recognizer = KaldiRecognizer(model, sample_rate)
    print(
        json.dumps(
            {
                "schema_version": WAKE_LISTENER_SCHEMA_VERSION,
                "status": "running",
                "engine": "vosk_local_stt",
                "primary_wake_phrase": "JARVIS",
                "wake_phrases": ["JARVIS"],
                "experimental_wake_aliases": ["Hola JARVIS"],
                "raw_audio_storage_enabled": False,
                "continuous_full_transcription": False,
                "wake_snippet_transcription_local_only": True,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )
    with sd.RawInputStream(samplerate=sample_rate, blocksize=block_size, dtype="int16", channels=1, callback=callback):
        while True:
            data = audio_queue.get()
            text = ""
            if recognizer.AcceptWaveform(data):
                try:
                    text = json.loads(recognizer.Result()).get("text", "")
                except json.JSONDecodeError:
                    text = ""
            else:
                try:
                    text = json.loads(recognizer.PartialResult()).get("partial", "")
                except json.JSONDecodeError:
                    text = ""
            match = match_wake_phrase(text)
            if text and text != last_debug_text:
                last_debug_text = text
                print(
                    json.dumps(
                        {
                            "schema_version": WAKE_MATCH_SCHEMA_VERSION,
                            "event": "wake_transcript",
                            "backend": "vosk",
                            "raw_transcript": text,
                            "normalized_transcript": match["normalized_transcript"],
                            "token_candidates": match["token_candidates"],
                            "accepted": match["accepted"],
                            "matched_wake_phrase": match["matched_wake_phrase"],
                            "matched_wake_phrase_kind": match["matched_wake_phrase_kind"],
                            "confidence": match["confidence"],
                            "threshold": match["threshold"],
                            "reason": match["reason"],
                            "raw_audio_stored": False,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    flush=True,
                )
            now = time.monotonic()
            if text and match["accepted"] and now - last_wake >= debounce_seconds:
                last_wake = now
                try:
                    posted = _post_wake_event(
                        backend_url=backend_url,
                        text=text,
                        confidence=float(match["confidence"]),
                        source="vosk_microphone_stt",
                    )
                    activation_debug = _activation_debug_from_backend(posted)
                    print(
                        json.dumps(
                            {
                                "schema_version": WAKE_MATCH_SCHEMA_VERSION,
                                "event": "wake_posted",
                                "backend": "vosk",
                                "raw_transcript": text,
                                "normalized_transcript": match["normalized_transcript"],
                                "token_candidates": match["token_candidates"],
                                **activation_debug,
                                "matched_wake_phrase": match["matched_wake_phrase"],
                                "matched_wake_phrase_kind": match["matched_wake_phrase_kind"],
                                "confidence": match["confidence"],
                                "reason": match["reason"],
                                "raw_audio_stored": False,
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                        flush=True,
                    )
                except Exception as exc:
                    print(json.dumps({"status": "post_failed", "error": type(exc).__name__}, sort_keys=True), flush=True)


def run_listener(
    *,
    backend_url: str = BACKEND_BASE_URL,
    env: Optional[Mapping[str, str]] = None,
    transcript_file: str = "",
    once: bool = False,
) -> int:
    source = merge_persisted_wake_env(env)
    file_source = transcript_file or str(source.get("JARVIS_WAKE_LISTENER_TRANSCRIPT_FILE") or "")
    if file_source:
        return _run_transcript_file_loop(path=Path(file_source).expanduser(), backend_url=backend_url, once=once)
    status = build_wake_listener_status(env=source)
    selected = status["state"]["selected_backend"]
    if selected == "openwakeword":
        return _run_openwakeword_loop(backend_url=backend_url, env=source)
    if selected == "vosk":
        return _run_vosk_loop(backend_url=backend_url, env=source)
    print(json.dumps(status, ensure_ascii=False, sort_keys=True), flush=True)
    return 2


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="JARVIS Phase 12 real microphone wake listener")
    parser.add_argument("command", choices=("status", "run", "match", "simulate"))
    parser.add_argument("phrase", nargs="*")
    parser.add_argument("--backend-url", default=BACKEND_BASE_URL)
    parser.add_argument("--transcript-file", default="")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "status":
        payload = build_wake_listener_status()
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "match":
        payload = match_wake_phrase(" ".join(args.phrase))
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "simulate":
        payload = simulate_wake_phrase(phrase=" ".join(args.phrase), backend_url=args.backend_url)
        print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("status") == "posted" else 2
    return run_listener(backend_url=args.backend_url, transcript_file=args.transcript_file, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
