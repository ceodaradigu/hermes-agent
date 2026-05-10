#!/usr/bin/env bash
set -euo pipefail

: "${JARVIS_BASE_URL:=http://127.0.0.1:8000}"

if [[ "$#" -eq 0 ]]; then
  echo "Uso: $0 \"texto para enviar al Voice Runtime\"" >&2
  echo "Ejemplo: $0 \"hola jarvis\"" >&2
  echo "Ejemplo: $0 \"crea una landing para X\"" >&2
  exit 2
fi

TEXT="$*"
NORMALIZED="$(printf '%s' "$TEXT" | tr '[:upper:]' '[:lower:]' | xargs)"
ENDPOINT="/voice/runtime/transcript"

case "$NORMALIZED" in
  "hola jarvis"|"jarvis"|"jarvis silencio"|"jarvis duerme")
    ENDPOINT="/voice/runtime/control"
    ;;
  "jarvis no escuches"*)
    ENDPOINT="/voice/runtime/control"
    ;;
esac

python - "$JARVIS_BASE_URL" "$ENDPOINT" "$TEXT" <<'PY'
import json
import sys
import urllib.error
import urllib.request

base_url = sys.argv[1].rstrip("/")
endpoint = sys.argv[2]
text = sys.argv[3]

request = urllib.request.Request(
    f"{base_url}{endpoint}",
    data=json.dumps({"text": text}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
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
