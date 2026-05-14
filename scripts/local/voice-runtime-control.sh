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
  feedback-add <original_text> <interpreted_intent> <corrected_intent> [correction_note] [preferred_next_step]
                         POST   /voice/runtime/feedback
  feedback-preview <original_text> <interpreted_intent> <corrected_intent> [correction_note] [preferred_next_step]
                         POST   /voice/runtime/feedback/preview
  feedback-apply-reviewed <original_text> <interpreted_intent> <corrected_intent> [correction_note] [preferred_next_step]
                         POST   /voice/runtime/feedback/apply-reviewed
  feedback-applied-list  GET    /voice/runtime/feedback/applied
  feedback-applied-clear DELETE /voice/runtime/feedback/applied
  memory-proposals       GET    /voice/runtime/memory/proposals
  memory-propose-from-feedback <original_text> <corrected_intent> [suggested_alias] [reason]
                         POST   /voice/runtime/memory/proposals/from-applied-feedback
  memory-proposal <proposal_id>
                         GET    /voice/runtime/memory/proposals/{proposal_id}
  memory-review <proposal_id>
                         POST   /voice/runtime/memory/proposals/{proposal_id}/review
  memory-approve <proposal_id> [approved_by]
                         POST   /voice/runtime/memory/proposals/{proposal_id}/approve
  memory-disable <proposal_id> [reason]
                         POST   /voice/runtime/memory/proposals/{proposal_id}/disable
  memory-delete <proposal_id>
                         DELETE /voice/runtime/memory/proposals/{proposal_id}
  memory-clear           DELETE /voice/runtime/memory/proposals

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
FEEDBACK_ORIGINAL_TEXT=""
FEEDBACK_INTERPRETED_INTENT=""
FEEDBACK_CORRECTED_INTENT=""
FEEDBACK_CORRECTION_NOTE=""
FEEDBACK_PREFERRED_NEXT_STEP=""
MEMORY_ORIGINAL_TEXT=""
MEMORY_CORRECTED_INTENT=""
MEMORY_SUGGESTED_ALIAS=""
MEMORY_REASON=""
MEMORY_APPROVED_BY=""

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
  feedback-applied-list)
    METHOD="GET"
    ENDPOINT="/voice/runtime/feedback/applied"
    ;;
  feedback-applied-clear)
    METHOD="DELETE"
    ENDPOINT="/voice/runtime/feedback/applied"
    ;;
  feedback-add)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <original_text>." >&2
      usage
      exit 2
    fi
    if [[ "$#" -lt 3 ]]; then
      echo "Error: falta <corrected_intent>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/feedback"
    PAYLOAD_KIND="feedback"
    FEEDBACK_ORIGINAL_TEXT="$1"
    FEEDBACK_INTERPRETED_INTENT="$2"
    FEEDBACK_CORRECTED_INTENT="$3"
    FEEDBACK_CORRECTION_NOTE="${4:-}"
    FEEDBACK_PREFERRED_NEXT_STEP="${5:-}"
    ;;
  feedback-apply-reviewed)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <original_text>." >&2
      usage
      exit 2
    fi
    if [[ "$#" -lt 3 ]]; then
      echo "Error: falta <corrected_intent>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/feedback/apply-reviewed"
    PAYLOAD_KIND="feedback"
    FEEDBACK_ORIGINAL_TEXT="$1"
    FEEDBACK_INTERPRETED_INTENT="$2"
    FEEDBACK_CORRECTED_INTENT="$3"
    FEEDBACK_CORRECTION_NOTE="${4:-}"
    FEEDBACK_PREFERRED_NEXT_STEP="${5:-}"
    ;;
  feedback-preview)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <original_text>." >&2
      usage
      exit 2
    fi
    if [[ "$#" -lt 3 ]]; then
      echo "Error: falta <corrected_intent>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/feedback/preview"
    PAYLOAD_KIND="feedback-preview"
    FEEDBACK_ORIGINAL_TEXT="$1"
    FEEDBACK_INTERPRETED_INTENT="$2"
    FEEDBACK_CORRECTED_INTENT="$3"
    FEEDBACK_CORRECTION_NOTE="${4:-}"
    FEEDBACK_PREFERRED_NEXT_STEP="${5:-}"
    ;;
  memory-proposals)
    METHOD="GET"
    ENDPOINT="/voice/runtime/memory/proposals"
    ;;
  memory-propose-from-feedback)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <original_text>." >&2
      usage
      exit 2
    fi
    if [[ "$#" -lt 2 ]]; then
      echo "Error: falta <corrected_intent>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/memory/proposals/from-applied-feedback"
    PAYLOAD_KIND="memory-from-feedback"
    MEMORY_ORIGINAL_TEXT="$1"
    MEMORY_CORRECTED_INTENT="$2"
    MEMORY_SUGGESTED_ALIAS="${3:-}"
    MEMORY_REASON="${4:-}"
    ;;
  memory-proposal)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <proposal_id>." >&2
      usage
      exit 2
    fi
    METHOD="GET"
    ENDPOINT="/voice/runtime/memory/proposals/$1"
    ;;
  memory-review)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <proposal_id>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/memory/proposals/$1/review"
    ;;
  memory-approve)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <proposal_id>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/memory/proposals/$1/approve"
    PAYLOAD_KIND="memory-approve"
    MEMORY_APPROVED_BY="${2:-David}"
    ;;
  memory-disable)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <proposal_id>." >&2
      usage
      exit 2
    fi
    METHOD="POST"
    ENDPOINT="/voice/runtime/memory/proposals/$1/disable"
    PAYLOAD_KIND="memory-disable"
    MEMORY_REASON="${2:-}"
    ;;
  memory-delete)
    if [[ "$#" -eq 0 ]]; then
      echo "Error: falta <proposal_id>." >&2
      usage
      exit 2
    fi
    METHOD="DELETE"
    ENDPOINT="/voice/runtime/memory/proposals/$1"
    ;;
  memory-clear)
    METHOD="DELETE"
    ENDPOINT="/voice/runtime/memory/proposals"
    ;;
  *)
    echo "Error: comando desconocido: $COMMAND" >&2
    usage
    exit 2
    ;;
esac

python - "$JARVIS_BASE_URL" "$METHOD" "$ENDPOINT" "$PAYLOAD_KIND" "$PAYLOAD_VALUE" \
  "$FEEDBACK_ORIGINAL_TEXT" "$FEEDBACK_INTERPRETED_INTENT" "$FEEDBACK_CORRECTED_INTENT" \
  "$FEEDBACK_CORRECTION_NOTE" "$FEEDBACK_PREFERRED_NEXT_STEP" \
  "$MEMORY_ORIGINAL_TEXT" "$MEMORY_CORRECTED_INTENT" "$MEMORY_SUGGESTED_ALIAS" \
  "$MEMORY_REASON" "$MEMORY_APPROVED_BY" <<'PY'
import json
import sys
import urllib.error
import urllib.request

base_url = sys.argv[1].rstrip("/")
method = sys.argv[2]
endpoint = sys.argv[3]
payload_kind = sys.argv[4]
payload_value = sys.argv[5]
feedback_original_text = sys.argv[6]
feedback_interpreted_intent = sys.argv[7]
feedback_corrected_intent = sys.argv[8]
feedback_correction_note = sys.argv[9]
feedback_preferred_next_step = sys.argv[10]
memory_original_text = sys.argv[11]
memory_corrected_intent = sys.argv[12]
memory_suggested_alias = sys.argv[13]
memory_reason = sys.argv[14]
memory_approved_by = sys.argv[15]

data = None
headers = {}
if payload_kind in {"feedback", "feedback-preview"}:
    payload = {
        "original_text": feedback_original_text,
        "interpreted_intent": feedback_interpreted_intent,
        "corrected_intent": feedback_corrected_intent,
    }
    if feedback_correction_note:
        payload["correction_note"] = feedback_correction_note
    if feedback_preferred_next_step:
        payload["preferred_next_step"] = feedback_preferred_next_step
    data = json.dumps(payload).encode("utf-8")
    headers["Content-Type"] = "application/json"
elif payload_kind == "memory-from-feedback":
    payload = {
        "original_text": memory_original_text,
        "corrected_intent": memory_corrected_intent,
        "source": "user_reviewed_feedback",
        "applied_persistently": False,
    }
    if memory_suggested_alias:
        payload["suggested_alias"] = memory_suggested_alias
    if memory_reason:
        payload["reason"] = memory_reason
    data = json.dumps(payload).encode("utf-8")
    headers["Content-Type"] = "application/json"
elif payload_kind == "memory-approve":
    data = json.dumps({"approved_by": memory_approved_by or "David"}).encode("utf-8")
    headers["Content-Type"] = "application/json"
elif payload_kind == "memory-disable":
    payload = {}
    if memory_reason:
        payload["reason"] = memory_reason
    data = json.dumps(payload).encode("utf-8")
    headers["Content-Type"] = "application/json"
elif payload_kind != "none":
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
