#!/usr/bin/env bash
set -euo pipefail

: "${JARVIS_BASE_URL:=http://127.0.0.1:8000}"

usage() {
  cat >&2 <<'EOF'
Uso: voice-runtime-control.sh <comando> [argumentos]

Comandos:
  status                 GET    /voice/runtime/status
  start                  POST   /voice/runtime/start
  stop                   POST   /voice/runtime/stop
  mode <mode>            POST   /voice/runtime/mode
  control <text>         POST   /voice/runtime/control
  transcript <text>      POST   /voice/runtime/transcript
  feedback-list          GET    /voice/runtime/feedback
  feedback-clear         DELETE /voice/runtime/feedback

Variables:
  JARVIS_BASE_URL        URL base de JARVIS (default: http://127.0.0.1:8000)
EOF
}

if [[ "$#" -eq 0 ]]; then
  usage
  exit 2
fi

COMMAND="$1"
shift

METHOD=""
ENDPOINT=""
PAYLOAD_KIND="none"
PAYLOAD_VALUE=""

case "$COMMAND" in
  status)
    METHOD="GET"
    ENDPOINT="/voice/runtime/status"
    ;;
  start)
    METHOD="POST"
    ENDPOINT="/voice/runtime/start"
    ;;
  stop)
    METHOD="POST"
    ENDPOINT="/voice/runtime/stop"
    ;;
  mode)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <mode>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/mode"
    PAYLOAD_KIND="mode"
    PAYLOAD_VALUE="$1"
    ;;
  control)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <text>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/control"
    PAYLOAD_KIND="text"
    PAYLOAD_VALUE="$*"
    ;;
  transcript)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <text>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/transcript"
    PAYLOAD_KIND="text"
    PAYLOAD_VALUE="$*"
    ;;
  feedback-list)
    METHOD="GET"
    ENDPOINT="/voice/runtime/feedback"
    ;;
  feedback-clear)
    METHOD="DELETE"
    ENDPOINT="/voice/runtime/feedback"
    ;;
  *)
    echo "Error: comando desconocido: $COMMAND" >&2
    usage
    exit 2
    ;;
esac

python - "$JARVIS_BASE_URL" "$METHOD" "$ENDPOINT" "$PAYLOAD_KIND" "$PAYLOAD_VALUE" <<'PY'
import json
import sys
import urllib.error
import urllib.request

base_url = sys.argv[1].rstrip("/")
method = sys.argv[2]
endpoint = sys.argv[3]
payload_kind = sys.argv[4]
payload_value = sys.argv[5]

data = None
headers = {}
if payload_kind != "none":
    key = "mode" if payload_kind == "mode" else "text"
    data = json.dumps({key: payload_value}).encode("utf-8")
    headers["Content-Type"] = "application/json"

request = urllib.request.Request(
    f"{base_url}{endpoint}",
    data=data,
    headers=headers,
    method=method,
)

try:
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8")
    print(body, file=sys.stderr)
    sys.exit(1)
except urllib.error.URLError as exc:
    print(f"Error: no se pudo conectar con JARVIS en {base_url}: {exc}", file=sys.stderr)
    sys.exit(1)

print(body)
PY
