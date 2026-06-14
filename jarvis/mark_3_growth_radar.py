from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.mark_3_mission_loop_models import UNKNOWN
from jarvis.mark_3_research_policy import ApprovalAwareResearchPolicy


@dataclass(frozen=True)
class ResearchRadarAuditEvent:
    event_id: str
    event_type: str
    created_at: str
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    redacted_fields: List[str] = field(default_factory=list)
    safe_to_execute: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AutonomousGrowthMissionPlanner:
    """Builds governed research mission previews. It never invokes adapters."""

    def build(self, values: Dict[str, Any], decision: Dict[str, Any]) -> Dict[str, Any]:
        safe, _ = redact_sensitive_data(dict(values or {}))
        source = decision["source"]
        goal = decision["goal"]
        query = _safe_text(safe.get("query", safe.get("topic")), _default_query(source, goal))
        return {
            "research_plan": [
                f"Frame exact research question for {goal}.",
                f"Query {source} only through the approved {decision['capability']} capability.",
                "Collect source links, summaries, limitations, and confidence notes.",
                "Convert useful findings into reviewable learning proposals or Hermes change proposals.",
                "Stop before install, commit, deploy, money movement, secret access, or production mutation.",
            ],
            "sources_to_query": [{
                "source": source,
                "query": query,
                "capability": decision["capability"],
                "network_required": decision["network_required"],
                "capability_status": decision["capability_status"],
            }],
            "expected_value": _expected_value(goal),
            "cost_estimate": safe.get("cost_estimate", UNKNOWN),
            "stop_conditions": _items(safe.get("stop_conditions")) or [
                "approval missing or expired",
                "capability is not connected",
                "source asks for credentials, secrets, payment, install, commit, deploy, or production change",
                "evidence cannot support the proposed learning",
            ],
            "evidence_required": _items(safe.get("evidence_required")) or [
                "source URL or local reference",
                "summary of the finding",
                "why it applies to JARVIS or Hermes",
                "risk and limitation notes",
            ],
            "candidate_actions": self._candidate_actions(decision, goal),
        }

    def _candidate_actions(self, decision: Dict[str, Any], goal: str) -> List[Dict[str, Any]]:
        query_status = decision["execution_status"]
        candidate_state = decision["candidate_state"]
        actions = [{
            "action_id": "query_source",
            "action_type": "research_query",
            "source": decision["source"],
            "goal": goal,
            "requires_approval": decision["requires_approval"],
            "approval_level": decision["approval_level"],
            "execution_status": query_status,
            "candidate_state": candidate_state,
            "is_executable_candidate": candidate_state == "executable_candidate",
            "capability": decision["capability"],
            "blocked_reasons": list(decision["blocked_reasons"]),
            "missing_requirements": list(decision["missing_requirements"]),
            "auto_execute": False,
            "side_effects": False,
        }]
        if goal in {"improve_hermes", "find_tools"}:
            actions.append({
                "action_id": "propose_hermes_change",
                "action_type": "proposal_only",
                "execution_status": "awaiting_review",
                "requires_approval": True,
                "approval_level": "simple",
                "auto_install": False,
                "auto_commit": False,
                "auto_deploy": False,
                "auto_execute": False,
            })
        for reason in decision["no_auto_actions"]:
            actions.append({
                "action_id": "blocked_auto_action",
                "action_type": "sensitive_action_guard",
                "reason": reason,
                "execution_status": "awaiting_approval",
                "requires_approval": True,
                "approval_level": decision["approval_level"],
                "auto_execute": False,
            })
        return actions


class ResearchRadarCandidateBuilder:
    def build(self, values: Dict[str, Any], decision: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": decision["source"],
            "goal": decision["goal"],
            "risk": decision["risk_level"],
            "risk_level": decision["risk_level"],
            "requires_approval": decision["requires_approval"],
            "approval_level": decision["approval_level"],
            "execution_status": decision["execution_status"],
            "candidate_state": decision["candidate_state"],
            "is_executable_candidate": decision["is_executable_candidate"],
            "capability_status": decision["capability_status"],
            "blocked_reasons": list(decision["blocked_reasons"]),
            "missing_requirements": list(decision["missing_requirements"]),
            "research_plan": plan["research_plan"],
            "sources_to_query": plan["sources_to_query"],
            "expected_value": plan["expected_value"],
            "cost_estimate": plan["cost_estimate"],
            "stop_conditions": plan["stop_conditions"],
            "evidence_required": plan["evidence_required"],
            "candidate_actions": plan["candidate_actions"],
            "executes_now": False,
            "scraping_performed": False,
            "web_called": False,
            "github_called": False,
            "hermes_is_execution_engine": True,
            "jarvis_governs_decides_approves_audits": True,
        }


class ResearchRadar:
    """Mark 3 governed research radar for autonomous growth preparation."""

    def __init__(
        self,
        *,
        policy: Optional[ApprovalAwareResearchPolicy] = None,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
    ) -> None:
        self.policy = policy or ApprovalAwareResearchPolicy()
        self.planner = AutonomousGrowthMissionPlanner()
        self.builder = ResearchRadarCandidateBuilder()
        self.clock = clock or _now_iso
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self._audit: List[ResearchRadarAuditEvent] = []
        self._plans: List[Dict[str, Any]] = []

    def status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "in_memory_only": True,
            "plan_count": len(self._plans),
            "audit_event_count": len(self._audit),
            "executes_internet_without_approval": False,
            "permanent_denial_for_missing_adapter": False,
            "github_web_can_become_executable_with_approval_and_capability": True,
            "hermes_remains_execution_engine": True,
        }

    def plan(self, values: Dict[str, Any]) -> Dict[str, Any]:
        decision = self.policy.evaluate(values)
        plan = self.planner.build(values, decision)
        candidate = self.builder.build(values, decision, plan)
        candidate["plan_id"] = _safe_text((values or {}).get("plan_id"), self.id_factory())
        candidate["created_at"] = self.clock()
        self._plans.append(candidate)
        self._append_audit("research_plan_created", "Research radar plan created; no external query executed.", {
            "plan_id": candidate["plan_id"],
            "source": candidate["source"],
            "goal": candidate["goal"],
            "execution_status": candidate["execution_status"],
            "candidate_state": candidate["candidate_state"],
            "approval_level": candidate["approval_level"],
        })
        return candidate

    def list_plans(self) -> List[Dict[str, Any]]:
        return list(self._plans)

    def audit(self) -> Dict[str, Any]:
        return {
            "append_only": True,
            "in_memory_only": True,
            "safe_to_execute": False,
            "events": [item.to_dict() for item in self._audit],
        }

    def _append_audit(self, event_type: str, summary: str, metadata: Dict[str, Any]) -> None:
        safe, redacted = redact_sensitive_data(metadata)
        self._audit.append(ResearchRadarAuditEvent(
            event_id=self.id_factory(),
            event_type=event_type,
            created_at=self.clock(),
            summary=summary,
            metadata=safe,
            redacted_fields=redacted,
        ))


def _default_query(source: str, goal: str) -> str:
    if source == "github":
        return f"repositories and issues that could {goal.replace('_', ' ')}"
    if source == "web":
        return f"current best practices to {goal.replace('_', ' ')}"
    if source == "docs":
        return f"documentation patterns to {goal.replace('_', ' ')}"
    return f"local repository patterns to {goal.replace('_', ' ')}"


def _expected_value(goal: str) -> str:
    return {
        "improve_jarvis": "better governed autonomy, safer decisions, and stronger mission outcomes",
        "improve_hermes": "targeted Hermes runtime improvements proposed through reviewable changes",
        "find_tools": "candidate tools for later security, license, value, and approval review",
        "detect_risks": "earlier detection of safety, scope, evidence, adapter, and approval gaps",
        "detect_opportunities": "new supervised automation opportunities for David",
    }.get(goal, UNKNOWN)


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_safe_text(item, "") for item in value if _safe_text(item, "")]
    text = _safe_text(value, "")
    return [text] if text else []


def _safe_text(value: Any, fallback: str) -> str:
    text = " ".join(str(value or "").strip().split())
    return text or fallback


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
