from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, List, Optional
from uuid import uuid4


class MissionContentSafetyDecision(str, Enum):
    ALLOWED_PREPARE_ONLY = "allowed_prepare_only"
    REQUIRES_REVIEW = "requires_review"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_STRONG_APPROVAL = "requires_strong_approval"
    DENIED = "denied"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class MissionContentSafetyResult:
    result_id: str
    decision: MissionContentSafetyDecision
    labels_required: List[str]
    human_review_required: bool
    reasons: List[str]
    audit_summary: str
    created_at: str
    mission_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision", _coerce_enum(MissionContentSafetyDecision, self.decision, "decision"))
        object.__setattr__(self, "labels_required", _list_from(self.labels_required))
        object.__setattr__(self, "reasons", _list_from(self.reasons))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @property
    def allowed_prepare_only(self) -> bool:
        return self.decision == MissionContentSafetyDecision.ALLOWED_PREPARE_ONLY

    @property
    def requires_review(self) -> bool:
        return self.decision == MissionContentSafetyDecision.REQUIRES_REVIEW

    @property
    def requires_approval(self) -> bool:
        return self.decision == MissionContentSafetyDecision.REQUIRES_APPROVAL

    @property
    def requires_strong_approval(self) -> bool:
        return self.decision == MissionContentSafetyDecision.REQUIRES_STRONG_APPROVAL

    @property
    def denied(self) -> bool:
        return self.decision == MissionContentSafetyDecision.DENIED

    @property
    def blocked(self) -> bool:
        return self.decision == MissionContentSafetyDecision.BLOCKED

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MissionContentSafetyResult":
        return cls(
            result_id=str(data.get("result_id", "")),
            mission_id=data.get("mission_id"),
            decision=data.get("decision", ""),
            labels_required=_list_from(data.get("labels_required")),
            human_review_required=bool(data.get("human_review_required", False)),
            reasons=_list_from(data.get("reasons")),
            audit_summary=str(data.get("audit_summary", "")),
            created_at=str(data.get("created_at", "")),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "mission_id": self.mission_id,
            "decision": self.decision.value,
            "allowed_prepare_only": self.allowed_prepare_only,
            "requires_review": self.requires_review,
            "requires_approval": self.requires_approval,
            "requires_strong_approval": self.requires_strong_approval,
            "denied": self.denied,
            "blocked": self.blocked,
            "labels_required": list(self.labels_required),
            "human_review_required": self.human_review_required,
            "reasons": list(self.reasons),
            "audit_summary": self.audit_summary,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


def evaluate_mission_content_safety(
    *,
    text: str = "",
    action: str = "",
    context: Optional[Dict[str, Any]] = None,
    mission_id: Optional[str] = None,
    human_review: bool = False,
    strong_approval: bool = False,
    evaluator: str = "jarvis",
) -> MissionContentSafetyResult:
    context = dict(context or {})
    combined = _normalize(" ".join(_flatten_text([text, action, context])))
    decisions: List[MissionContentSafetyDecision] = []
    labels_required: List[str] = []
    reasons: List[str] = []

    if _mentions_any(combined, _DECEPTIVE_DEEPFAKE_TERMS):
        decisions.append(MissionContentSafetyDecision.BLOCKED)
        reasons.append("deceptive deepfake or fake endorsement content is blocked")
    if _mentions_any(combined, _IMPERSONATION_TERMS):
        decisions.append(MissionContentSafetyDecision.BLOCKED)
        reasons.append("impersonation is blocked")
    if _mentions_any(combined, _REAL_IDENTITY_TERMS) and not context.get("identity_permission"):
        decisions.append(MissionContentSafetyDecision.REQUIRES_STRONG_APPROVAL)
        reasons.append("real identity use without explicit permission requires strong approval or blocking")
    if _mentions_any(combined, _BIOMETRIC_TERMS):
        decisions.append(MissionContentSafetyDecision.REQUIRES_STRONG_APPROVAL)
        reasons.append("sensitive biometric content requires strong approval")
    if _mentions_any(combined, _COVERT_MANIPULATION_TERMS):
        decisions.append(MissionContentSafetyDecision.BLOCKED)
        reasons.append("covert manipulation is blocked")
    if _mentions_any(combined, _AI_PUBLIC_COMMERCIAL_TERMS):
        decisions.append(MissionContentSafetyDecision.REQUIRES_REVIEW)
        labels_required.append("ai_generated_or_modified")
        reasons.append("public or commercial AI-generated content requires labeling and human review")
    if _mentions_any(combined, _LEGAL_CLAIM_TERMS):
        decisions.append(MissionContentSafetyDecision.REQUIRES_REVIEW)
        reasons.append("legal contracts or claims require human/legal review")
    if _mentions_any(combined, _COMMERCIAL_PUBLICATION_TERMS) and not (human_review and strong_approval):
        decisions.append(MissionContentSafetyDecision.REQUIRES_STRONG_APPROVAL)
        reasons.append("commercial publication requires human review and strong approval")

    if not decisions:
        decisions.append(MissionContentSafetyDecision.ALLOWED_PREPARE_ONLY)
        reasons.append("no baseline AI content safety risk detected")

    decision = _max_decision(decisions)
    human_review_required = decision != MissionContentSafetyDecision.ALLOWED_PREPARE_ONLY or bool(labels_required)

    return MissionContentSafetyResult(
        result_id=str(uuid4()),
        mission_id=mission_id,
        decision=decision,
        labels_required=sorted(set(labels_required)),
        human_review_required=human_review_required,
        reasons=reasons,
        audit_summary=(
            f"Content safety baseline evaluated mission {mission_id or 'none'}: decision={decision.value}; "
            "baseline only, no legal compliance determination, publication, approval, or external call occurred."
        ),
        created_at=_now_iso(),
        metadata={"evaluator": evaluator or "jarvis", "prepare_only": True, "external_api_called": False},
    )


def _max_decision(decisions: List[MissionContentSafetyDecision]) -> MissionContentSafetyDecision:
    order = {
        MissionContentSafetyDecision.ALLOWED_PREPARE_ONLY: 0,
        MissionContentSafetyDecision.REQUIRES_REVIEW: 1,
        MissionContentSafetyDecision.REQUIRES_APPROVAL: 2,
        MissionContentSafetyDecision.REQUIRES_STRONG_APPROVAL: 3,
        MissionContentSafetyDecision.DENIED: 4,
        MissionContentSafetyDecision.BLOCKED: 5,
    }
    return max(decisions, key=lambda decision: order[decision])


def _mentions_any(text: str, terms: set[str]) -> bool:
    tokens = set(re.findall(r"[a-z0-9]+", text.replace("_", " ")))
    for term in terms:
        if " " in term or "-" in term:
            if term in text:
                return True
        elif term in tokens:
            return True
    return False


def _flatten_text(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, dict):
        items: List[str] = []
        for key, item in value.items():
            items.append(str(key))
            items.extend(_flatten_text(item))
        return items
    if isinstance(value, list):
        items: List[str] = []
        for item in value:
            items.extend(_flatten_text(item))
        return items
    return [str(value)]


def _coerce_enum(enum_type, value: Any, field_name: str):
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid {enum_type.__name__}") from exc


def _list_from(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _normalize(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_AI_PUBLIC_COMMERCIAL_TERMS = {"ai generated", "generated by ai", "ai-modified", "ai modified", "commercial ai", "public ai", "synthetic"}
_DECEPTIVE_DEEPFAKE_TERMS = {"deepfake", "fake endorsement", "make them say", "deceptive clone", "voice clone"}
_IMPERSONATION_TERMS = {"impersonate", "suplantacion", "suplantar", "pretend to be", "as if i were"}
_REAL_IDENTITY_TERMS = {"real person", "celebrity", "david identity", "use his face", "use her face", "use my identity"}
_BIOMETRIC_TERMS = {"biometric", "face recognition", "voiceprint", "iris", "fingerprint"}
_COVERT_MANIPULATION_TERMS = {"covert manipulation", "subliminal", "manipulate users without knowing", "dark pattern"}
_LEGAL_CLAIM_TERMS = {"contract", "legal claim", "terms of service", "lawsuit", "compliance claim"}
_COMMERCIAL_PUBLICATION_TERMS = {"publish", "public", "commercial", "ad campaign", "sales page", "landing"}
