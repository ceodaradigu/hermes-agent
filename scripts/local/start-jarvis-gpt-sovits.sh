#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "$REPO_ROOT"

if [[ -f "$HOME/venvs/hermes-agent/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$HOME/venvs/hermes-agent/bin/activate"
fi

export PYTHONPATH=.

DEFAULT_JARVIS_REF_AUDIO_PATH="/mnt/c/Users/${USER}/Desktop/JARVIS/test-voice.wav"

: "${JARVIS_VOICE_PROVIDER:=gpt-sovits}"
: "${JARVIS_GPT_SOVITS_BASE_URL:=http://127.0.0.1:9880}"
: "${JARVIS_GPT_SOVITS_REF_AUDIO_PATH:=$DEFAULT_JARVIS_REF_AUDIO_PATH}"
: "${JARVIS_GPT_SOVITS_PROMPT_LANG:=en}"
: "${JARVIS_GPT_SOVITS_TIMEOUT_SECONDS:=60}"
: "${JARVIS_HOST:=127.0.0.1}"
: "${JARVIS_PORT:=8000}"

export JARVIS_VOICE_PROVIDER
export JARVIS_GPT_SOVITS_BASE_URL
export JARVIS_GPT_SOVITS_REF_AUDIO_PATH
export JARVIS_GPT_SOVITS_PROMPT_LANG
export JARVIS_GPT_SOVITS_TIMEOUT_SECONDS
export JARVIS_HOST
export JARVIS_PORT

if [[ ! -f "$JARVIS_GPT_SOVITS_REF_AUDIO_PATH" ]]; then
  echo "Error: no existe JARVIS_GPT_SOVITS_REF_AUDIO_PATH:" >&2
  echo "  $JARVIS_GPT_SOVITS_REF_AUDIO_PATH" >&2
  echo "Define una ruta valida a un WAV de referencia autorizado antes de arrancar JARVIS." >&2
  exit 1
fi

GPT_SOVITS_DOCS_URL="${JARVIS_GPT_SOVITS_BASE_URL%/}/docs"

python - "$GPT_SOVITS_DOCS_URL" <<'PY'
import sys
import urllib.error
import urllib.request

url = sys.argv[1]
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        if response.status >= 400:
            raise RuntimeError(f"HTTP {response.status}")
except (OSError, RuntimeError, urllib.error.URLError) as exc:
    print("Error: GPT-SoVITS no responde en /docs.", file=sys.stderr)
    print(f"  URL: {url}", file=sys.stderr)
    print(f"  Detalle: {exc}", file=sys.stderr)
    print(
        "Arranca GPT-SoVITS aparte con: python api_v2.py -a 127.0.0.1 -p 9880",
        file=sys.stderr,
    )
    sys.exit(1)
PY

echo "JARVIS voice provider: $JARVIS_VOICE_PROVIDER"
echo "GPT-SoVITS sidecar: $JARVIS_GPT_SOVITS_BASE_URL"
echo "Referencia de voz: $JARVIS_GPT_SOVITS_REF_AUDIO_PATH"
echo "Arrancando JARVIS en http://$JARVIS_HOST:$JARVIS_PORT"

exec python -m uvicorn jarvis.api.app:app --host "$JARVIS_HOST" --port "$JARVIS_PORT"
