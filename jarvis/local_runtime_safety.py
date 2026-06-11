from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class LocalRuntimeSafetyPolicy:
    default_disabled: bool = True
    microphone_requires_opt_in: bool = True
    camera_requires_opt_in: bool = True
    network_disabled_by_default: bool = True
    external_tools_disabled_by_default: bool = True
    production_actions_require_strong_approval: bool = True
    money_actions_require_strong_approval: bool = True
    critical_actions_require_double_confirmation: bool = True
    optional_triple_confirmation_for_high_risk: bool = True
    wake_phrase_never_grants_permission: bool = True
    voice_approval_allowed: bool = True
    voice_approval_requires_readback: bool = True
    voice_approval_requires_exact_phrase_for_critical: bool = True
    voice_approval_expires: bool = True
    voice_approval_ttl_seconds: int = 300
    audit_required: bool = True
    stop_phrase_always_available: bool = True
    kill_switch_always_available: bool = True
    restrictions_are_approval_gates: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

