from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib import error, request as urllib_request

from jarvis.voice.base import VoiceAdapter, VoiceSynthesisRequest, VoiceSynthesisResult


class _UrllibHTTPClient:
    """Small stdlib HTTP client wrapper for easy test injection."""

    def post(self, url: str, json_payload: Dict[str, Any], timeout: float) -> tuple[int, Dict[str, str], bytes]:
        body = json.dumps(json_payload).encode("utf-8")
        req = urllib_request.Request(
            url=url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib_request.urlopen(req, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            headers = dict(response.headers.items())
            response_body = response.read()
            return status, headers, response_body


class GPTSoVITSAdapter(VoiceAdapter):
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:9880",
        ref_audio_path: Optional[str] = None,
        prompt_text: Optional[str] = None,
        prompt_lang: str = "es",
        timeout_seconds: float = 30.0,
        http_client: Any = None,
    ) -> None:
        self.base_url = base_url
        self.ref_audio_path = ref_audio_path
        self.prompt_text = prompt_text
        self.prompt_lang = prompt_lang
        self.timeout_seconds = timeout_seconds
        self.http_client = http_client or _UrllibHTTPClient()

    def synthesize(self, request: VoiceSynthesisRequest) -> VoiceSynthesisResult:
        if not self.base_url or not self.base_url.strip():
            raise ValueError("base_url must be a non-empty string")
        if not self.prompt_lang or not self.prompt_lang.strip():
            raise ValueError("prompt_lang must be a non-empty string")

        ref_audio_path = self.ref_audio_path or request.metadata.get("ref_audio_path")
        if not ref_audio_path or not str(ref_audio_path).strip():
            raise ValueError("ref_audio_path is required (adapter or request.metadata)")

        prompt_text = self.prompt_text
        if prompt_text is None:
            prompt_text = request.metadata.get("prompt_text", "")

        tts_url = f"{self.base_url.rstrip('/')}/tts"
        payload = {
            "text": request.text,
            "text_lang": request.language,
            "ref_audio_path": ref_audio_path,
            "prompt_text": prompt_text,
            "prompt_lang": self.prompt_lang,
            "media_type": request.output_format,
            "streaming_mode": False,
        }

        try:
            status, headers, audio_bytes = self.http_client.post(
                tts_url,
                json_payload=payload,
                timeout=self.timeout_seconds,
            )
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            message = _extract_error_message(body) or f"HTTP {exc.code}"
            raise RuntimeError(f"GPT-SoVITS request failed: {message}") from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError("Failed to connect to GPT-SoVITS service") from exc

        if status != 200:
            body_text = audio_bytes.decode("utf-8", errors="replace") if audio_bytes else ""
            message = _extract_error_message(body_text) or f"HTTP {status}"
            raise RuntimeError(f"GPT-SoVITS request failed: {message}")

        content_type = headers.get("Content-Type") or f"audio/{request.output_format}"
        metadata = {
            **request.metadata,
            "base_url": self.base_url,
            "ref_audio_path": ref_audio_path,
            "prompt_lang": self.prompt_lang,
        }

        return VoiceSynthesisResult(
            content_type=content_type,
            provider="gpt-sovits",
            audio_bytes=audio_bytes,
            metadata=metadata,
        )


def _extract_error_message(raw_body: str) -> Optional[str]:
    if not raw_body:
        return None
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return raw_body.strip() or None

    if isinstance(payload, dict):
        for key in ("message", "error", "detail"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None
