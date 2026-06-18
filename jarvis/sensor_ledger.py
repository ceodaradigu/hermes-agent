from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping
from uuid import uuid4


SENSOR_LEDGER_SCHEMA_VERSION = "jarvis.sensor_ledger.v1"

SENSOR_TYPES = (
    "camera",
    "recording",
    "wake",
    "voice_session",
    "tts",
    "stt",
)

SENSOR_EVENT_TYPES = (
    "requested",
    "started",
    "stopped",
    "cancelled",
    "failed",
    "deleted",
    "retention_updated",
)

_SENSITIVE_KEY_MARKERS = (
    "audio_bytes",
    "raw_audio",
    "audio_blob",
    "audio_buffer",
    "frame",
    "frames",
    "image",
    "video",
    "blob",
    "secret",
    "token",
    "credential",
    "password",
    "api_key",
    "apikey",
    "cookie",
    "authorization",
)


@dataclass
class SensorLedger:
    """In-memory local ledger for safe sensor/session metadata.

    The ledger stores control-plane facts only. It is intentionally not a media
    store and has no API surface for raw microphone, camera, credential, or
    provider payloads.
    """

    max_events: int = 200
    _events: List[Dict[str, Any]] = field(default_factory=list)

    def record(
        self,
        *,
        sensor_type: str,
        event_type: str,
        source: str,
        metadata: Mapping[str, Any] | None = None,
        risk_level: str = "sensor_privacy",
        created_at: str | None = None,
    ) -> Dict[str, Any]:
        if sensor_type not in SENSOR_TYPES:
            raise ValueError(f"Unsupported sensor type: {sensor_type}")
        if event_type not in SENSOR_EVENT_TYPES:
            raise ValueError(f"Unsupported sensor event type: {event_type}")

        blocked_count = _blocked_field_count(metadata or {})
        safe_metadata = _sanitize_metadata(metadata or {})
        event = {
            "schema_version": SENSOR_LEDGER_SCHEMA_VERSION,
            "event_id": f"sensor-ledger-{uuid4()}",
            "sensor_type": sensor_type,
            "event_type": event_type,
            "source": _safe_scalar(source, default="/jarvis"),
            "created_at": created_at or _now_iso(),
            "risk_level": _safe_scalar(risk_level, default="sensor_privacy"),
            "metadata": safe_metadata,
            "blocked_field_count": blocked_count,
            "stores_raw_audio": False,
            "stores_frames": False,
            "stores_credential_material": False,
            "read_only_from_jarvis": True,
        }
        self._events.append(event)
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events :]
        return dict(event)

    def events(self, *, limit: int = 25) -> List[Dict[str, Any]]:
        return [dict(event) for event in self._events[-limit:]]


def build_sensor_ledger_status(
    *,
    ledger: SensorLedger | None = None,
    generated_at: str,
) -> Dict[str, Any]:
    events = ledger.events(limit=25) if ledger else []
    return {
        "schema_version": SENSOR_LEDGER_SCHEMA_VERSION,
        "state": {
            "mode": "read_only_sensor_metadata_ledger",
            "generated_at": generated_at,
            "local_only": True,
            "read_only_from_jarvis": True,
            "event_count": len(events),
            "supported_sensors": list(SENSOR_TYPES),
            "supported_events": list(SENSOR_EVENT_TYPES),
            "supported_recording_modalities": ["audio_metadata", "video_metadata"],
        },
        "events": events,
        "retention": {
            "storage": "metadata_only_in_memory",
            "stores_raw_audio": False,
            "stores_frames": False,
            "stores_credential_material": False,
            "raw_media_retention": "not_applicable",
            "delete_event_supported": True,
            "retention_update_event_supported": True,
        },
        "contracts": [
            {
                "sensor_type": sensor_type,
                "metadata_only": True,
                "safe_metadata_modalities": ["audio_metadata", "video_metadata"] if sensor_type == "recording" else ["session_metadata"],
                "requires_opt_in": True,
                "visible_indicator_required": True,
                "stop_or_cancel_required": True,
                "audit_required": True,
                "backend_media_upload_allowed": False,
            }
            for sensor_type in SENSOR_TYPES
        ],
        "safety": {
            "read_only": True,
            "metadata_only": True,
            "no_raw_audio": True,
            "no_camera_frames": True,
            "no_video_frames": True,
            "no_credential_material": True,
            "no_transcript_storage": True,
            "sensors_require_opt_in": True,
            "visible_indicator_required": True,
            "stop_cancel_required": True,
        },
        "source_endpoint": "/mark-3/dashboard/status",
        "read_only": True,
    }


def _sanitize_metadata(metadata: Mapping[str, Any]) -> Dict[str, Any]:
    sanitized: Dict[str, Any] = {}
    for key, value in metadata.items():
        safe_key = _safe_scalar(key, default="unknown_key")
        if _is_sensitive_key(safe_key):
            continue
        sanitized[safe_key[:80]] = _sanitize_value(value)
    return sanitized


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _sanitize_metadata(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value[:20]]
    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value[:20]]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return value
    return _safe_scalar(value)


def _blocked_field_count(metadata: Mapping[str, Any] | Iterable[Any]) -> int:
    count = 0
    if isinstance(metadata, Mapping):
        for key, value in metadata.items():
            if _is_sensitive_key(str(key)):
                count += 1
                continue
            if isinstance(value, (Mapping, list, tuple)):
                count += _blocked_field_count(value)
    elif isinstance(metadata, (list, tuple)):
        for value in metadata:
            if isinstance(value, (Mapping, list, tuple)):
                count += _blocked_field_count(value)
    return count


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in _SENSITIVE_KEY_MARKERS)


def _safe_scalar(value: Any, *, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return text[:500]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
