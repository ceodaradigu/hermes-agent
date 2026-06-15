from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional
from uuid import uuid4

from jarvis.approval_hardening import (
    ApprovalHardeningService,
    ApprovalKind,
    ApprovalRecord,
    ApprovalStatus,
    build_context_fingerprint,
)
from jarvis.mark_3_learning_proposals import LearningProposalEngine
from jarvis.mark_3_local_research_adapter import LOCAL_RESEARCH_SOURCE_TYPES, LocalResearchReadAdapter
from jarvis.mark_3_mission_loop_models import UNKNOWN
from jarvis.mark_3_negative_intent_parser import (
    contains_actionable_marker,
    payload_text,
    redact_mark_3_payload,
)
from jarvis.mark_3_outcome_memory import OutcomeMemoryStore


SOURCE_TYPES = ("github", "web", "docs", "local_repo")
SOURCE_TYPE_SET = set(SOURCE_TYPES)
EXTERNAL_NETWORK_SOURCES = {"github", "web"}
LOCAL_SAFE_READ_SOURCES = set(LOCAL_RESEARCH_SOURCE_TYPES)
CAPABILITY_STATUS_VALUES = ("connected", "capability_not_connected_yet", "unsupported")
CAPABILITY_BY_SOURCE = {
    "github": "github_research",
    "web": "web_research",
    "docs": "docs_research",
    "local_repo": "local_repo_research",
}
DEFAULT_CAPABILITY_STATUS_BY_SOURCE = {
    "github": "capability_not_connected_yet",
    "web": "capability_not_connected_yet",
    "docs": "connected",
    "local_repo": "connected",
}
RESEARCH_EXECUTION_STATES = (
    "preview",
    "awaiting_approval",
    "setup_required",
    "capability_not_connected_yet",
    "executable_candidate",
    "completed",
    "blocked",
)
APPROVAL_LEVELS = ("direct", "simple", "strong", "double", "triple")
CONNECTED_APPROVAL_CHANNELS = {"direct", "simple", "strong"}


@dataclass(frozen=True)
class NormalizedResearchRequest:
    research_id: str
    source_type: str
    normalized_query: str
    normalized_scope: str
    risk_level: str
    goal: str
    raw_request: Dict[str, Any] = field(default_factory=dict)
    redacted_fields: List[str] = field(default_factory=list)

    @property
    def query_or_scope(self) -> str:
        return self.normalized_query or self.normalized_scope or UNKNOWN

    def fingerprint_fields(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "normalized_query": self.normalized_query,
            "normalized_scope": self.normalized_scope,
            "risk_level": self.risk_level,
            "goal": self.goal,
        }


@dataclass(frozen=True)
class ResearchExecutionDecision:
    research_id: str
    source_type: str
    normalized_query: str
    normalized_scope: str
    query_or_scope: str
    goal: str
    risk_level: str
    approval_required: bool
    approval_level: str
    approval_valid: bool
    approval_id: str
    approval_context: Dict[str, Any]
    approval_context_fingerprint: str
    research_fingerprint: str
    fingerprint_fields: Dict[str, Any]
    capability: str
    capability_status: str
    execution_status: str
    candidate_state: str
    legal: bool
    safe: bool
    authorized: bool
    technically_supported: bool
    network_required: bool
    blocked_reasons: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    no_auto_actions: List[str] = field(default_factory=list)
    risk_signals: List[str] = field(default_factory=list)
    outcome: Optional[Dict[str, Any]] = None
    failures: List[Dict[str, Any]] = field(default_factory=list)
    learning_proposal_candidates: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    evaluated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["is_executable_candidate"] = self.candidate_state == "executable_candidate"
        permanent_denial = _permanent_denial_for_decision(self)
        data["can_become_executable_candidate"] = self.capability_status != "unsupported" and not permanent_denial
        data["approval_is_gate_not_permanent_ban"] = True
        data["permanent_denial"] = permanent_denial
        data["control_plane_only"] = True
        data["execution_performed"] = False
        data["command_execution_performed"] = False
        data["adapter_called"] = False
        data["file_reads_performed"] = False
        data["local_repo_scan_performed"] = False
        data["github_called"] = False
        data["web_called"] = False
        data["threads_started"] = 0
        data["installs_performed"] = False
        data["commits_pushes_merges_performed"] = False
        data["sources_found"] = 0
        data["sources"] = []
        data["evidence"] = []
        data["summary"] = _summary_for(self)
        data["recommended_actions"] = _recommended_actions_for(self)
        data["hermes_is_execution_engine"] = True
        data["jarvis_governs_risk_approval_audit"] = True
        data["no_duplicate_hermes_runtime"] = True
        data["real_research_execution_connected"] = self.source_type in LOCAL_SAFE_READ_SOURCES and self.capability_status == "connected"
        data["external_research_execution_connected"] = False
        data["setup_required_reason"] = (
            "capability_not_connected_yet"
            if self.execution_status == "setup_required" and self.capability_status == "capability_not_connected_yet"
            else ""
        )
        return data


class ResearchExecutionPolicy:
    """Pure policy for governed research execution candidates.

    It normalizes the request, checks approval/capability state, and never calls
    filesystem, network, subprocess, GitHub, web, docs, or local repo adapters.
    """

    def evaluate(
        self,
        values: Dict[str, Any],
        *,
        capability_status_by_source: Optional[Dict[str, str]] = None,
        approval_record: Optional[ApprovalRecord] = None,
        approval_service: Optional[ApprovalHardeningService] = None,
        clock: Optional[Callable[[], str]] = None,
    ) -> Dict[str, Any]:
        normalized = normalize_research_request(values)
        user_text = _user_supplied_text(values)
        source_supported = normalized.source_type in SOURCE_TYPE_SET
        network_required = normalized.source_type in EXTERNAL_NETWORK_SOURCES
        capability = CAPABILITY_BY_SOURCE.get(normalized.source_type, "unsupported_research_source")
        capability_status = _capability_status(
            normalized.source_type,
            capability,
            capability_status_by_source or DEFAULT_CAPABILITY_STATUS_BY_SOURCE,
        )
        local_safe_read_source = normalized.source_type in LOCAL_SAFE_READ_SOURCES
        broad_scope = local_safe_read_source and _scope_requires_approval(
            normalized.source_type,
            normalized.normalized_scope,
        )
        risk_level = _risk_level(normalized, user_text, network_required=network_required, broad_scope=broad_scope)
        normalized = NormalizedResearchRequest(
            research_id=normalized.research_id,
            source_type=normalized.source_type,
            normalized_query=normalized.normalized_query,
            normalized_scope=normalized.normalized_scope,
            risk_level=risk_level,
            goal=normalized.goal,
            raw_request=normalized.raw_request,
            redacted_fields=normalized.redacted_fields,
        )
        approval_level = _required_approval_level(
            risk_level,
            network_required=network_required,
            broad_scope=broad_scope,
            user_text=user_text,
        )
        approval_required = approval_level != "direct"
        stronger_channel_missing = approval_level not in CONNECTED_APPROVAL_CHANNELS
        approval_context = _approval_context(
            normalized=normalized,
            capability=capability,
            network_required=network_required,
            approval_level=approval_level,
        )
        approval_context_fingerprint = build_context_fingerprint(approval_context)
        research_fingerprint = build_context_fingerprint({
            "action_type": "research_execution_fingerprint",
            "user_payload": normalized.fingerprint_fields(),
        })
        approval_valid, approval_missing = _approval_valid(
            approval_record,
            approval_service=approval_service,
            approval_required=approval_required,
            approval_level=approval_level,
            context_fingerprint=approval_context_fingerprint,
            stronger_channel_missing=stronger_channel_missing,
        )

        blocked_reasons: List[str] = []
        missing_requirements: List[str] = []
        no_auto_actions = _no_auto_actions(user_text)
        illegal = _illegal_requested(user_text)
        secrets = _secret_access_requested(user_text) or bool(normalized.redacted_fields)
        dangerous_action = _dangerous_action_requested(user_text)
        raw_scope = _clean_text((values or {}).get("scope"))
        multi_scope = _multi_scope_requested(values)
        path_traversal = _path_traversal_requested(raw_scope or normalized.normalized_scope)
        sensitive_scope = _sensitive_scope_requested(raw_scope or normalized.normalized_scope)
        exact_scope_missing = local_safe_read_source and _exact_file_scope_missing(
            normalized.source_type,
            normalized.normalized_scope,
            multi_scope=multi_scope,
            path_traversal=path_traversal,
            sensitive_scope=sensitive_scope,
        )
        authorized = _authorized(values)

        if not source_supported:
            blocked_reasons.append("unsupported_research_source")
        if illegal:
            blocked_reasons.append("illegal_or_unauthorized_access_request")
        if secrets:
            blocked_reasons.append("credentials_secrets_or_env_access_blocked")
        if multi_scope:
            blocked_reasons.append("multi_scope_blocked")
        if path_traversal:
            blocked_reasons.append("path_traversal_blocked")
        if sensitive_scope:
            blocked_reasons.append("sensitive_path_blocked")
        if dangerous_action:
            blocked_reasons.append("side_effectful_research_action_blocked")
        if not authorized:
            blocked_reasons.append("authorization_missing")
        if stronger_channel_missing:
            missing_requirements.append("stronger_approval_channel_not_connected")
        if approval_missing:
            missing_requirements.append(f"{approval_level}_approval_required")
        if capability_status == "capability_not_connected_yet":
            missing_requirements.append("capability_not_connected_yet")
        if capability_status == "unsupported":
            blocked_reasons.append("unsupported_research_capability")
        if exact_scope_missing:
            missing_requirements.append("exact_file_scope_required")

        blocked = bool(blocked_reasons)
        if blocked:
            execution_status = "blocked"
            candidate_state = "blocked"
        elif stronger_channel_missing:
            execution_status = "setup_required"
            candidate_state = "setup_required"
        elif approval_required and not approval_valid:
            execution_status = "awaiting_approval"
            candidate_state = "awaiting_approval"
        elif capability_status == "capability_not_connected_yet":
            execution_status = "setup_required"
            candidate_state = "setup_required"
        elif exact_scope_missing:
            execution_status = "setup_required"
            candidate_state = "setup_required"
        else:
            execution_status = "executable_candidate"
            candidate_state = "executable_candidate"

        now = (clock or now_iso)()
        decision = ResearchExecutionDecision(
            research_id=normalized.research_id,
            source_type=normalized.source_type,
            normalized_query=normalized.normalized_query,
            normalized_scope=normalized.normalized_scope,
            query_or_scope=normalized.query_or_scope,
            goal=normalized.goal,
            risk_level=risk_level,
            approval_required=approval_required,
            approval_level=approval_level,
            approval_valid=approval_valid,
            approval_id=_clean_text((values or {}).get("approval_id")),
            approval_context=approval_context,
            approval_context_fingerprint=approval_context_fingerprint,
            research_fingerprint=research_fingerprint,
            fingerprint_fields=normalized.fingerprint_fields(),
            capability=capability,
            capability_status=capability_status,
            execution_status=execution_status,
            candidate_state=candidate_state,
            legal=not illegal,
            safe=not (secrets or dangerous_action),
            authorized=authorized,
            technically_supported=source_supported and capability_status != "unsupported",
            network_required=network_required,
            blocked_reasons=_unique(blocked_reasons),
            missing_requirements=_unique(missing_requirements),
            no_auto_actions=no_auto_actions,
            risk_signals=_risk_signals(
                source_type=normalized.source_type,
                risk_level=risk_level,
                network_required=network_required,
                broad_scope=broad_scope,
                secrets=secrets,
                dangerous_action=dangerous_action,
            ),
            created_at=now,
            evaluated_at=now,
        )
        return decision.to_dict()


class ResearchExecutionControlPlane:
    """Mark 3 governed research execution control-plane.

    Local docs/repo research is connected through a bounded read-only adapter.
    GitHub and web remain setup-gated until real governed adapters exist.
    """

    def __init__(
        self,
        *,
        approval_service: Optional[ApprovalHardeningService] = None,
        outcome_memory: Optional[OutcomeMemoryStore] = None,
        learning_proposals: Optional[LearningProposalEngine] = None,
        research_radar: Any = None,
        capability_status_by_source: Optional[Dict[str, Any]] = None,
        local_research_adapter: Optional[LocalResearchReadAdapter] = None,
        repo_root: Optional[str] = None,
        policy: Optional[ResearchExecutionPolicy] = None,
        clock: Optional[Callable[[], str]] = None,
    ) -> None:
        self.approval_service = approval_service or ApprovalHardeningService()
        self.outcome_memory = outcome_memory or OutcomeMemoryStore()
        self.learning_proposals = learning_proposals or LearningProposalEngine()
        self.research_radar = research_radar
        self.local_research_adapter = local_research_adapter or LocalResearchReadAdapter(repo_root=repo_root)
        self.policy = policy or ResearchExecutionPolicy()
        self.clock = clock or now_iso
        self.capability_status_by_source = _normalize_capability_status_map(capability_status_by_source)
        self._records: Dict[str, Dict[str, Any]] = {}

    def status(self) -> Dict[str, Any]:
        capabilities = {
            source_type: {
                "source_type": source_type,
                "capability": CAPABILITY_BY_SOURCE[source_type],
                "capability_status": self.capability_status_by_source[source_type],
                "connected": self.capability_status_by_source[source_type] == "connected",
                "network_required": source_type in EXTERNAL_NETWORK_SOURCES,
                "approval_required_for_default_scope": source_type in EXTERNAL_NETWORK_SOURCES,
                "local_read_only_adapter": source_type in LOCAL_SAFE_READ_SOURCES,
            }
            for source_type in SOURCE_TYPES
        }
        return {
            "available": True,
            "control_plane_enforced": True,
            "control_plane_only": False,
            "real_research_execution_connected": True,
            "external_research_execution_connected": False,
            "local_docs_repo_read_adapter_connected": True,
            "local_adapter_read_only": True,
            "research_execution_states": list(RESEARCH_EXECUTION_STATES),
            "source_types": list(SOURCE_TYPES),
            "capability_status_values": list(CAPABILITY_STATUS_VALUES),
            "capabilities": capabilities,
            "record_count": len(self._records),
            "active_research_count": 0,
            "threads_started": 0,
            "file_reads_performed": False,
            "local_file_reads_available_via_candidate": True,
            "local_repo_scan_performed": False,
            "github_called": False,
            "web_called": False,
            "commands_executed": False,
            "installs_performed": False,
            "commits_pushes_merges_performed": False,
            "hermes_is_execution_engine": True,
            "jarvis_governs_decides_approves_audits": True,
            "no_duplicate_hermes_runtime": True,
            "missing_capability_returns_setup_required": True,
            "missing_capability_is_not_permanent_denial": True,
            "uses_mark_3_research_radar_plans": self.research_radar is not None,
            "candidate_by_research_id_rehydrates_request": False,
        }

    def preview(self, values: Dict[str, Any]) -> Dict[str, Any]:
        expanded = self._expand_radar_plan(dict(values or {}))
        decision = self._evaluate(expanded)
        decision["preview_state"] = "preview"
        self._records[decision["research_id"]] = decision
        return decision

    def candidate(self, values: Dict[str, Any]) -> Dict[str, Any]:
        incoming = dict(values or {})
        if _research_id_only(incoming):
            return self._candidate_requires_full_request(incoming)

        expanded = self._expand_radar_plan(incoming)
        decision = self._evaluate(expanded)
        decision["preview_state"] = "candidate"
        decision["candidate_revalidated"] = True
        decision["execution_performed"] = False
        decision["command_execution_performed"] = False
        decision["adapter_called"] = False

        if decision["candidate_state"] == "executable_candidate" and decision["source_type"] in LOCAL_SAFE_READ_SOURCES:
            local_result = self.local_research_adapter.read(
                source_type=decision["source_type"],
                scope=expanded.get("scope"),
            )
            decision = self._apply_local_research_result(decision, local_result)

        if decision["execution_status"] in {"setup_required", "blocked"}:
            self._record_non_execution_outcome(decision)
        elif decision["execution_status"] == "completed":
            self._record_local_read_outcome(decision)
        self._records[decision["research_id"]] = decision
        return decision

    def get(self, research_id: str) -> Dict[str, Any]:
        key = _clean_text(research_id)
        if key not in self._records:
            raise KeyError(research_id)
        return dict(self._records[key])

    def _evaluate(self, values: Dict[str, Any]) -> Dict[str, Any]:
        approval = self._approval_record(_clean_text((values or {}).get("approval_id")))
        return self.policy.evaluate(
            values,
            capability_status_by_source=self.capability_status_by_source,
            approval_record=approval,
            approval_service=self.approval_service,
            clock=self.clock,
        )

    def _candidate_requires_full_request(self, values: Dict[str, Any]) -> Dict[str, Any]:
        research_id = _clean_text((values or {}).get("research_id"))
        existing = dict(self._records.get(research_id) or {})
        if not existing:
            existing = self._evaluate(dict(values or {}))
        existing["preview_state"] = "candidate"
        existing["candidate_revalidated"] = True
        existing["execution_status"] = "setup_required"
        existing["candidate_state"] = "setup_required"
        existing["execution_performed"] = False
        existing["command_execution_performed"] = False
        existing["adapter_called"] = False
        existing["file_reads_performed"] = False
        existing["local_repo_scan_performed"] = False
        existing["candidate_by_research_id_only"] = True
        existing["request_rehydrated_for_execution"] = False
        existing["missing_requirements"] = _unique(
            list(existing.get("missing_requirements") or []) + ["full_request_required_for_local_read"]
        )
        existing["summary"] = "Candidate request needs the full source_type and exact scope again; stored previews are not executable."
        existing["recommended_actions"] = ["resubmit source_type and one exact allowed file scope to /candidate"]
        self._records[existing["research_id"]] = existing
        return existing

    def _apply_local_research_result(self, decision: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        updated = dict(decision)
        updated["local_research_adapter"] = result.get("adapter", "local_docs_repo_read_adapter")
        updated["adapter_called"] = True
        updated["threads_started"] = int(result.get("threads_started") or 0)
        updated["local_repo_scan_performed"] = False
        updated["github_called"] = False
        updated["web_called"] = False
        updated["commands_executed"] = False
        updated["command_execution_performed"] = False
        if result.get("status") == "success":
            evidence = {
                "type": "local_file",
                "source_type": result.get("source_type", updated["source_type"]),
                "scope": result.get("scope", updated["normalized_scope"]),
                "path_reference": result.get("path_reference", UNKNOWN),
                "content_sha256": result.get("content_sha256", UNKNOWN),
                "bytes_read": result.get("bytes_read", 0),
                "truncated": bool(result.get("truncated", False)),
            }
            updated.update({
                "execution_status": "completed",
                "candidate_state": "completed",
                "result_status": "success",
                "control_plane_only": False,
                "execution_performed": True,
                "file_reads_performed": True,
                "sources_found": 1,
                "sources": [evidence],
                "evidence": [evidence],
                "local_read_result": result,
                "summary": "Governed local research read completed for one exact allowed file scope.",
                "recommended_actions": ["review local evidence and convert useful findings into a separate governed proposal if needed"],
            })
            return updated

        blocked = list(result.get("blocked_reasons") or ["local_research_read_blocked"])
        updated["execution_status"] = "blocked"
        updated["candidate_state"] = "blocked"
        updated["blocked_reasons"] = _unique(list(updated.get("blocked_reasons") or []) + blocked)
        updated["permanent_denial"] = bool(result.get("permanent_denial", False)) or _permanent_denial_for_reasons(blocked)
        updated["safe"] = not updated["permanent_denial"]
        updated["execution_performed"] = False
        updated["file_reads_performed"] = False
        updated["local_read_result"] = {
            key: value
            for key, value in result.items()
            if key not in {"content"}
        }
        updated["summary"] = "Governed local research read was blocked before returning file content."
        updated["recommended_actions"] = ["submit one exact non-sensitive, non-symlink file scope inside the allowed local source"]
        return updated

    def _expand_radar_plan(self, values: Dict[str, Any]) -> Dict[str, Any]:
        expanded = dict(values or {})
        if self.research_radar is not None:
            plan_id = _clean_text(expanded.get("plan_id"))
            if plan_id:
                for plan in self.research_radar.list_plans():
                    if _clean_text(plan.get("plan_id")) == plan_id:
                        expanded = {**plan, **expanded}
                        break
        sources_to_query = expanded.get("sources_to_query")
        if isinstance(sources_to_query, list) and sources_to_query:
            first = sources_to_query[0] if isinstance(sources_to_query[0], dict) else {}
            if not _clean_text(expanded.get("source_type")) and not _clean_text(expanded.get("source")):
                expanded["source"] = first.get("source")
            if not _clean_text(expanded.get("query")) and not _clean_text(expanded.get("topic")):
                expanded["query"] = first.get("query")
        return expanded

    def _approval_record(self, approval_id: str) -> Optional[ApprovalRecord]:
        if not approval_id:
            return None
        try:
            return self.approval_service.get(approval_id)
        except KeyError:
            return None

    def _record_non_execution_outcome(self, decision: Dict[str, Any]) -> None:
        status = decision["execution_status"]
        errors = decision.get("blocked_reasons") or decision.get("missing_requirements") or []
        outcome = self.outcome_memory.record({
            "mission_id": decision["research_id"],
            "step_id": "research_execution_control_plane",
            "candidate_id": decision["research_id"],
            "goal": decision["goal"],
            "tool_used": decision["capability"],
            "capability_used": decision["capability"],
            "result_status": status,
            "evidence_state": "not_observed",
            "errors": errors,
            "duration_seconds": "unknown",
            "cost": "unknown",
            "approval_level": decision["approval_level"],
            "what_worked": "Research execution stopped at governed control-plane.",
            "what_failed": "; ".join(errors) or UNKNOWN,
            "next_recommended_action": "; ".join(decision.get("recommended_actions") or []) or UNKNOWN,
            "failure_category": _failure_category_for(decision),
        })
        decision["outcome"] = outcome
        failures: List[Dict[str, Any]] = []
        if "capability_not_connected_yet" in decision.get("missing_requirements", []):
            failures.append(self.outcome_memory.record_failure({
                "category": "adapter_not_connected",
                "mission_id": decision["research_id"],
                "step_id": "research_execution_control_plane",
                "candidate_id": decision["research_id"],
                "error": "capability_not_connected_yet",
                "affected_capability": decision["capability"],
                "scope": decision["source_type"],
                "suggested_avoidance": "connect a small governed research adapter before executing real research",
            }))
        decision["failures"] = failures
        if failures and not decision.get("permanent_denial", False):
            decision["learning_proposal_candidates"] = [
                self.learning_proposals.create({
                    "proposal": f"Connect governed {decision['source_type']} research capability before real execution.",
                    "evidence": (
                        f"Research candidate {decision['research_id']} reached setup_required with "
                        "capability_not_connected_yet."
                    ),
                    "confidence": "medium",
                    "risk": decision.get("risk_level", "unknown"),
                    "requires_approval": True,
                    "source_outcome_ids": [outcome.get("outcome_id", UNKNOWN)],
                    "source_failure_ids": [item.get("failure_id", UNKNOWN) for item in failures],
                })
            ]

    def _record_local_read_outcome(self, decision: Dict[str, Any]) -> None:
        local_result = dict(decision.get("local_read_result") or {})
        outcome = self.outcome_memory.record({
            "mission_id": decision["research_id"],
            "step_id": "research_execution_local_read",
            "candidate_id": decision["research_id"],
            "goal": decision["goal"],
            "tool_used": decision["capability"],
            "capability_used": decision["capability"],
            "result_status": "success",
            "evidence_state": "observed",
            "errors": [],
            "duration_seconds": "unknown",
            "cost": "0",
            "approval_level": decision["approval_level"],
            "what_worked": "Governed local read adapter read one exact file scope.",
            "what_failed": UNKNOWN,
            "next_recommended_action": "; ".join(decision.get("recommended_actions") or []) or UNKNOWN,
            "failure_category": "unknown",
            "metadata": {
                "source_type": decision["source_type"],
                "path_reference": local_result.get("path_reference", UNKNOWN),
                "bytes_read": local_result.get("bytes_read", 0),
                "truncated": bool(local_result.get("truncated", False)),
            },
        })
        decision["outcome"] = outcome


def normalize_research_request(values: Dict[str, Any]) -> NormalizedResearchRequest:
    raw = dict(values or {})
    safe, redacted = redact_mark_3_payload(raw)
    source_type = _source_type(safe)
    query = _query(safe)
    scope = _scope(safe)
    goal = _goal(safe)
    risk = _choice(_first_present(safe, "risk_level", "risk"), {"low", "medium", "high", "critical"}, "")
    research_id = _clean_text(safe.get("research_id")) or str(uuid4())
    return NormalizedResearchRequest(
        research_id=research_id,
        source_type=source_type,
        normalized_query=query,
        normalized_scope=scope,
        risk_level=risk or "low",
        goal=goal,
        raw_request=safe,
        redacted_fields=redacted,
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _approval_valid(
    approval_record: Optional[ApprovalRecord],
    *,
    approval_service: Optional[ApprovalHardeningService],
    approval_required: bool,
    approval_level: str,
    context_fingerprint: str,
    stronger_channel_missing: bool,
) -> tuple[bool, bool]:
    if not approval_required:
        return True, False
    if stronger_channel_missing:
        return False, False
    if approval_record is None:
        return False, True
    if approval_service is not None:
        approval_service.refresh_expiration(approval_record)
    if approval_record.status != ApprovalStatus.APPROVED:
        return False, True
    if approval_record.action_type != "research_execution":
        return False, True
    if approval_record.context_fingerprint != context_fingerprint:
        return False, True
    if approval_level == "strong":
        strong = approval_record.strong_approval_required or approval_record.approval_kind == ApprovalKind.STRONG
        if not strong:
            return False, True
    return True, False


def _approval_context(
    *,
    normalized: NormalizedResearchRequest,
    capability: str,
    network_required: bool,
    approval_level: str,
) -> Dict[str, Any]:
    return {
        "action_type": "research_execution",
        "target": f"{normalized.source_type}:{normalized.research_id}",
        "tool_name": capability,
        "environment": "research",
        "external_call": network_required,
        "secret_access": False,
        "user_payload": {
            **normalized.fingerprint_fields(),
            "approval_level": approval_level,
        },
    }


def _source_type(values: Dict[str, Any]) -> str:
    raw = _first_present(values, "source_type", "source")
    source = _clean_text(raw).lower() or "local_repo"
    aliases = {
        "github_search": "github",
        "github_research": "github",
        "web_search": "web",
        "web_research": "web",
        "docs_review": "docs",
        "docs_reader": "docs",
        "docs_research": "docs",
        "local_repo_scan": "local_repo",
        "local_repo_read": "local_repo",
        "local_repo_research": "local_repo",
        "repo": "local_repo",
        "repository": "local_repo",
    }
    return aliases.get(source, source)


def _query(values: Dict[str, Any]) -> str:
    query = _first_present(values, "query", "topic")
    if not query:
        sources_to_query = values.get("sources_to_query")
        if isinstance(sources_to_query, list) and sources_to_query and isinstance(sources_to_query[0], dict):
            query = sources_to_query[0].get("query")
    return _clean_text(query)


def _scope(values: Dict[str, Any]) -> str:
    return _clean_text(values.get("scope"))


def _goal(values: Dict[str, Any]) -> str:
    return _clean_text(values.get("goal")) or "improve_jarvis"


def _risk_level(
    normalized: NormalizedResearchRequest,
    user_text: str,
    *,
    network_required: bool,
    broad_scope: bool,
) -> str:
    if normalized.risk_level in {"low", "medium", "high", "critical"}:
        declared = normalized.risk_level
    else:
        declared = ""
    if declared and declared != "low":
        return declared
    if _secret_access_requested(user_text):
        return "critical"
    if _text_has_action(user_text, ("money", "payment", "stripe live", "deploy", "production")):
        return "critical"
    if _dangerous_action_requested(user_text):
        return "high"
    if network_required or broad_scope:
        return "medium"
    return declared or "low"


def _required_approval_level(
    risk_level: str,
    *,
    network_required: bool,
    broad_scope: bool,
    user_text: str,
) -> str:
    if _text_has_action(user_text, ("money", "payment", "stripe live", "deploy", "production")):
        return "triple"
    if _text_has_action(user_text, ("install", "commit", "push", "merge")):
        return "double"
    if risk_level == "critical":
        return "double"
    if risk_level == "high":
        return "strong"
    if network_required or broad_scope or risk_level == "medium":
        return "simple"
    return "direct"


def _capability_status(source_type: str, capability: str, statuses: Dict[str, str]) -> str:
    if source_type not in SOURCE_TYPE_SET:
        return "unsupported"
    status = statuses.get(source_type, statuses.get(capability, "capability_not_connected_yet"))
    return status if status in CAPABILITY_STATUS_VALUES else "capability_not_connected_yet"


def _normalize_capability_status_map(values: Optional[Dict[str, Any]]) -> Dict[str, str]:
    statuses = dict(DEFAULT_CAPABILITY_STATUS_BY_SOURCE)
    for key, value in dict(values or {}).items():
        normalized = _clean_text(key).lower()
        source_type = normalized if normalized in SOURCE_TYPE_SET else _source_for_capability(normalized)
        if source_type not in SOURCE_TYPE_SET:
            continue
        if isinstance(value, bool):
            statuses[source_type] = "connected" if value else "capability_not_connected_yet"
        else:
            status = _clean_text(value).lower()
            statuses[source_type] = status if status in CAPABILITY_STATUS_VALUES else "capability_not_connected_yet"
    return statuses


def _source_for_capability(capability: str) -> str:
    for source_type, expected in CAPABILITY_BY_SOURCE.items():
        if capability == expected:
            return source_type
    return ""


def _scope_requires_approval(source_type: str, scope: str) -> bool:
    normalized = _clean_text(scope).lower()
    broad = {"", ".", "./", "/", "*", "repo", "repository", "root", "repo root", "all", "entire repo", "whole repo"}
    if source_type == "docs":
        broad.update({"docs", "docs/", "documentation", "all docs", "all documentation"})
    return normalized in broad


def _exact_file_scope_missing(
    source_type: str,
    scope: str,
    *,
    multi_scope: bool,
    path_traversal: bool,
    sensitive_scope: bool,
) -> bool:
    if source_type not in LOCAL_SAFE_READ_SOURCES:
        return False
    if multi_scope or path_traversal or sensitive_scope:
        return False
    if _scope_requires_approval(source_type, scope):
        return True
    return scope.endswith("/")


def _multi_scope_requested(values: Dict[str, Any]) -> bool:
    scope = (values or {}).get("scope")
    if isinstance(scope, (list, tuple, set)):
        return True
    text = _clean_text(scope)
    return bool(text and any(separator in text for separator in ("\n", "\r", ";")))


def _path_traversal_requested(scope: str) -> bool:
    text = _clean_text(scope)
    if not text:
        return False
    normalized = text.replace("\\", "/")
    if normalized.startswith("/") or normalized.startswith("~"):
        return True
    return any(part == ".." for part in normalized.split("/"))


def _sensitive_scope_requested(scope: str) -> bool:
    text = _clean_text(scope).lower().replace("\\", "/")
    if not text:
        return False
    for part in text.split("/"):
        normalized = part.replace("-", "_").replace(" ", "_")
        stem = normalized.rsplit(".", 1)[0]
        if normalized == ".env" or stem == ".env":
            return True
        if any(marker in normalized for marker in _SENSITIVE_SCOPE_SUBSTRINGS):
            return True
        if stem in {"key", "keys"} or normalized in {"key", "keys"}:
            return True
        if normalized.endswith(".key") or ".key." in normalized:
            return True
    return False


def _user_supplied_text(values: Dict[str, Any]) -> str:
    user_fields = {
        key: (values or {}).get(key)
        for key in (
            "source_type",
            "source",
            "query",
            "topic",
            "scope",
            "query_or_scope",
            "risk_level",
            "risk",
            "goal",
            "action",
            "request",
        )
    }
    return payload_text(user_fields)


def _illegal_requested(text: str) -> bool:
    return _text_has_action(text, _ILLEGAL_MARKERS)


def _secret_access_requested(text: str) -> bool:
    return _text_has_action(text, _SECRET_MARKERS)


def _dangerous_action_requested(text: str) -> bool:
    return _text_has_action(text, _DANGEROUS_ACTION_MARKERS)


def _authorized(values: Dict[str, Any]) -> bool:
    values = values or {}
    return _authorization_flag(values.get("authorized", True)) and _authorization_flag(
        values.get("authorization_valid", True)
    )


def _authorization_flag(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "missing"}
    return bool(value)


def _no_auto_actions(text: str) -> List[str]:
    return _unique(reason for marker, reason in _NO_AUTO_ACTIONS.items() if contains_actionable_marker(text, (marker,)))


def _risk_signals(
    *,
    source_type: str,
    risk_level: str,
    network_required: bool,
    broad_scope: bool,
    secrets: bool,
    dangerous_action: bool,
) -> List[str]:
    signals = [f"source_type:{source_type}", f"risk_level:{risk_level}"]
    if network_required:
        signals.append("external_network_requires_approval")
    if broad_scope:
        signals.append("broad_repo_scope_requires_approval")
    if secrets:
        signals.append("secret_access_blocked")
    if dangerous_action:
        signals.append("side_effect_action_blocked")
    return signals


def _recommended_actions_for(decision: ResearchExecutionDecision) -> List[str]:
    if decision.execution_status == "awaiting_approval":
        return [f"request {decision.approval_level} approval bound to approval_context_fingerprint"]
    if decision.execution_status == "setup_required":
        if "stronger_approval_channel_not_connected" in decision.missing_requirements:
            return ["connect a real stronger approval channel before accepting double or triple approval"]
        if "exact_file_scope_required" in decision.missing_requirements:
            return ["submit one exact non-sensitive file scope; broad local research scans are not connected"]
        return ["connect a small governed research adapter before executing real research"]
    if decision.execution_status == "blocked":
        return ["revise the request to remove unsafe, unauthorized, unsupported, or side-effectful actions"]
    if decision.source_type in LOCAL_SAFE_READ_SOURCES:
        return ["call /mark-3/research-execution/candidate with the full request to perform one governed local read"]
    return ["candidate is executable only after a future safe adapter is connected by a later PR"]


def _summary_for(decision: ResearchExecutionDecision) -> str:
    if decision.execution_status == "awaiting_approval":
        return "Research execution is awaiting approval; no adapter was called."
    if decision.execution_status == "setup_required":
        if "exact_file_scope_required" in decision.missing_requirements:
            return "Research execution is setup_required because local research requires one exact file scope."
        return "Research execution is setup_required because real research capability is not connected."
    if decision.execution_status == "blocked":
        return "Research execution request is blocked by policy; no adapter was called."
    if decision.source_type in LOCAL_SAFE_READ_SOURCES:
        return "Governed local research candidate is ready for one exact read-only file scope."
    return "Research execution candidate is policy-cleared, but this PR still does not execute adapters."


def _failure_category_for(decision: Dict[str, Any]) -> str:
    if "capability_not_connected_yet" in decision.get("missing_requirements", []):
        return "adapter_not_connected"
    if decision.get("execution_status") == "blocked":
        return "policy_blocked"
    return "setup_required"


def _permanent_denial_for_decision(decision: ResearchExecutionDecision) -> bool:
    return _permanent_denial_for_reasons(decision.blocked_reasons)


def _permanent_denial_for_reasons(reasons: Iterable[str]) -> bool:
    permanent = {
        "credentials_secrets_or_env_access_blocked",
        "illegal_or_unauthorized_access_request",
        "authorization_missing",
        "path_traversal_blocked",
        "sensitive_path_blocked",
        "symlink_blocked",
        "unsupported_research_source",
        "unsupported_research_capability",
    }
    return any(reason in permanent for reason in reasons)


def _research_id_only(values: Dict[str, Any]) -> bool:
    if not _clean_text((values or {}).get("research_id")):
        return False
    executable_fields = {
        "source_type",
        "source",
        "scope",
        "query",
        "topic",
        "plan_id",
    }
    return not any(_clean_text((values or {}).get(key)) for key in executable_fields)


def _first_present(values: Dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = values.get(key)
        if _clean_text(value):
            return value
    return None


def _choice(value: Any, allowed: Iterable[str], fallback: str) -> str:
    text = _clean_text(value).lower()
    return text if text in set(allowed) else fallback


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(item for item in (_clean_text(item) for item in value) if item)
    return " ".join(str(value).strip().split())


def _combined(value: Any) -> str:
    return payload_text(value)


def _unique(values: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(item for item in values if item))


def _text_has_action(text: str, markers: Iterable[str]) -> bool:
    return contains_actionable_marker(text, markers)


_ILLEGAL_MARKERS = (
    "steal",
    "exfiltrate",
    "bypass 2fa",
    "bypass mfa",
    "unauthorized access",
    "phishing",
)
_SECRET_MARKERS = (
    ".env",
    "api key",
    "api_key",
    "api-key",
    "apikey",
    "authorization:",
    "bearer ",
    "credential",
    "credentials",
    "password",
    "private key",
    "private-key",
    "private_key",
    "privatekey",
    "secret",
    "token",
)
_SENSITIVE_SCOPE_SUBSTRINGS = (
    "api_key",
    "api-key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "credentials",
    "password",
    "private_key",
    "private-key",
    "privatekey",
    "secret",
    "token",
)
_DANGEROUS_ACTION_MARKERS = (
    "pip install",
    "npm install",
    "poetry add",
    "uv add",
    "install",
    "dependency change",
    "write file",
    "modify code",
    "commit",
    "push",
    "merge",
    "deploy",
    "production",
    "payment",
    "money",
    "stripe live",
    "send email",
)
_NO_AUTO_ACTIONS = {
    "install": "no install is allowed from research execution",
    "dependency": "no dependency change is allowed from research execution",
    "write file": "no file write is allowed from research execution",
    "modify code": "no code modification is allowed from research execution",
    "commit": "no commit is allowed from research execution",
    "push": "no push is allowed from research execution",
    "merge": "no merge is allowed from research execution",
    "deploy": "no deploy is allowed from research execution",
    "production": "no production change is allowed from research execution",
    "payment": "no payment or money movement is allowed from research execution",
    "money": "no payment or money movement is allowed from research execution",
    "send email": "no email sending is allowed from research execution",
}
