#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys


def build_status() -> dict:
    token_present = bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
    allowed_users_present = bool(os.getenv("TELEGRAM_ALLOWED_USERS", "").strip())
    explicitly_enabled = os.getenv("JARVIS_PHASE8_TELEGRAM_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    return {
        "pilot": "jarvis_phase8_telegram_readiness",
        "status": "manual_pilot_ready" if token_present and allowed_users_present and explicitly_enabled else "disabled_by_default_or_incomplete",
        "token_present": token_present,
        "token_value_exposed": False,
        "allowed_users_configured": allowed_users_present,
        "enabled_by_config": explicitly_enabled,
        "bot_started": False,
        "polling_started": False,
        "webhook_opened": False,
        "telegram_api_called": False,
        "remote_execution_allowed": False,
        "direct_hermes_allowed": False,
        "notes": "Default mode is readiness-only. Use the existing Hermes gateway adapter for a future governed manual pilot.",
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="JARVIS Phase 8 Telegram readiness pilot")
    parser.add_argument("--run", action="store_true", help="Refuse by default; included to make manual pilot gating explicit.")
    args = parser.parse_args(argv)

    status = build_status()
    if args.run and os.getenv("JARVIS_PHASE8_TELEGRAM_PILOT_ALLOW_RUN", "").strip().lower() not in {"1", "true", "yes", "on"}:
        status["status"] = "refused_run_flag_without_explicit_manual_override"
        status["refusal_reason"] = "Phase 8 does not start a Telegram bot automatically."
        print(json.dumps(status, indent=2, sort_keys=True))
        return 2

    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
