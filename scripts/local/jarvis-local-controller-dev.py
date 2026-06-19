#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from urllib import request


DEFAULT_BASE_URL = "http://127.0.0.1:9119"


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual/dev JARVIS local controller client. No autostart, no external bind.")
    parser.add_argument("command", choices=("status", "opt-in", "opt-out", "register", "heartbeat", "start-request", "stop-request", "kill-switch-on", "kill-switch-off"))
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--controller-id", default="jarvis-dev-local-controller")
    args = parser.parse_args()

    if not args.base_url.startswith("http://127.0.0.1:") and not args.base_url.startswith("http://localhost:"):
        raise SystemExit("Refusing non-local JARVIS URL. Use 127.0.0.1 or localhost.")

    if args.command == "status":
        payload = _get(args.base_url, "/mark-3/local-controller/status")
    elif args.command in {"opt-in", "opt-out"}:
        payload = _post(args.base_url, "/mark-3/local-controller/opt-in", {"enabled": args.command == "opt-in", "actor": "David"})
    elif args.command == "register":
        payload = _post(
            args.base_url,
            "/mark-3/local-controller/register",
            {
                "controller_id": args.controller_id,
                "display_name": "JARVIS Dev Local Controller",
                "verification_phrase": "VERIFY LOCAL CONTROLLER",
                "local_only": True,
                "bind_host": "127.0.0.1",
            },
        )
    elif args.command == "heartbeat":
        payload = _post(args.base_url, "/mark-3/local-controller/heartbeat", {"controller_id": args.controller_id})
    elif args.command == "start-request":
        payload = _post(args.base_url, "/mark-3/local-controller/start-request", {"actor": "David"})
    elif args.command == "stop-request":
        payload = _post(args.base_url, "/mark-3/local-controller/stop-request", {"controller_id": args.controller_id, "actor": "David"})
    elif args.command in {"kill-switch-on", "kill-switch-off"}:
        payload = _post(args.base_url, "/mark-3/local-controller/kill-switch", {"enabled": args.command == "kill-switch-on", "actor": "David"})
    else:
        raise AssertionError(args.command)

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _get(base_url: str, path: str) -> dict:
    with request.urlopen(f"{base_url}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _post(base_url: str, path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{base_url}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    sys.exit(main())
