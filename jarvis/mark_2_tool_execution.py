from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.approval_hardening import RiskLevel
from jarvis.mark_2_browser_adapter import BrowserToolAdapter
from jarvis.mark_2_external_api_adapter import ExternalAPIToolAdapter
from jarvis.mark_2_filesystem_adapter import FilesystemToolAdapter
from jarvis.mark_2_github_adapter import GitHubToolAdapter
from jarvis.mark_2_tool_audit import ToolExecutionAuditEvent, build_tool_execution_audit_event
from jarvis.mark_2_tool_execution_policy import Mark2ToolExecutionPolicyEngine, RISK_ORDER


@dataclass(frozen=True)
class ToolExecutionRequest:
    request_id: str
    actor: str
    channel: str
    natural_language_command: str
    action_type: str
    target_type: str
    target: str
    environment: str
    requires_network: bool
    requires_credentials: bool
    requires_filesystem_write: bool
    requires_external_write: bool
    requires_browser: bool
    requires_github: bool
    requires_api_call: bool
    risk_level_declared: RiskLevel
    risk_level_classified: RiskLevel
    risk_downgrade_attempted: bool
    approval_context: Dict[str, Any] = field(default_factory=dict)
    voice_approval_context: Dict[str, Any] = field(default_factory=dict)
    rollback_or_stop_plan: str = ""
    requested_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["risk_level_declared"] = self.risk_level_declared.value
        data["risk_level_classified"] = self.risk_level_classified.value
        data["target"] = _safe_text(self.target)
        return data


@dataclass(frozen=True)
class ToolExecutionCandidate:
    candidate_id: str
    request_id: str
    action_type: str
    target_type: str
    target: str
    adapter_name: str
    preview_summary: str
    execution_steps: List[str]
    sandbox_scope: List[str]
    allowlist_match: bool
    denylist_match: bool
    approval_required: bool
    strong_approval_required: bool
    double_confirmation_required: bool
    triple_confirmation_required: bool
    valid_approval_present: bool
    valid_voice_approval_present: bool
    eligible_after_valid_approval: bool
    execution_allowed: bool
    would_execute: bool = False
    would_call_external: bool = False
    would_write_filesystem: bool = False
    would_modify_remote: bool = False
    would_touch_production: bool = False
    would_move_money: bool = False
    audit_required: bool = True
    credentials_required: bool = False
    network_required: bool = False
    production_impact: bool = False
    cost_impact: bool = False
    rollback_or_stop_plan_required: bool = False
    sensitive_payload_detected: bool = False
    user_data_risk: str = "low"
    rollback_or_stop_plan_present: bool = False
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "Review candidate and satisfy every approval and safety gate."

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["target"] = _safe_text(self.target)
        return data


@dataclass(frozen=True)
class ToolExecutionReadiness:
    candidate_id: str
    ready_after_all_gates: bool
    candidate_ready_after_policy_gates: bool
    execution_ready: bool
    real_execution_enabled: bool = False
    approval_ready: bool = False
    sandbox_ready: bool = False
    allowlist_ready: bool = False
    denylist_clear: bool = False
    rollback_ready: bool = False
    network_ready: bool = False
    credentials_ready: bool = False
    production_ready: bool = False
    kill_switch_clear: bool = True
    stop_phrase_clear: bool = True
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "Review readiness in the human approval console."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolExecutionResult:
    result_id: str
    candidate_id: str
    executed: bool
    success: bool
    mode: str
    adapter_name: str
    action_summary: str
    safe_output: Dict[str, Any]
    redacted_output: bool
    external_call_made: bool = False
    filesystem_changed: bool = False
    remote_changed: bool = False
    money_moved: bool = False
    production_touched: bool = False
    audit_event_id: str = ""
    blocked_reasons: List[str] = field(default_factory=list)
    next_safe_step: str = "Keep real execution disabled until a reviewed runtime path exists."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Mark2ToolExecutionLayer:
    """Mark 2 preparation and gated-readiness layer. External execution is intentionally absent."""

    def __init__(self, *, repo_root: str = ".") -> None:
        self.policy_engine = Mark2ToolExecutionPolicyEngine()
        self.filesystem = FilesystemToolAdapter(repo_root)
        self.github = GitHubToolAdapter()
        self.browser = BrowserToolAdapter()
        self.external_api = ExternalAPIToolAdapter()
        self._audit_events: Dict[str, ToolExecutionAuditEvent] = {}
        self._audit_lock = Lock()

    def status(self) -> Dict[str, Any]:
        return self.policy_engine.status()

    def policy(self) -> Dict[str, Any]:
        return self.policy_engine.policy()

    def prepare_request(self, **values: Any) -> ToolExecutionRequest:
        target_type = _clean(values.get("target_type")).lower() or "unknown"
        action = _clean(values.get("action_type")) or "preview"
        command = _safe_text(values.get("natural_language_command") or action)
        target = _clean(values.get("target"))
        policy_values = dict(values)
        policy_values.update(
            action_type=action,
            target_type=target_type,
            target=target,
            allowlist_match=values.get("allowlist_match", target_type != "filesystem"),
        )
        classified = self.policy_engine.evaluate(**policy_values).risk_level
        declared = RiskLevel(values.get("risk_level_declared") or RiskLevel.MEDIUM)
        return ToolExecutionRequest(
            request_id=str(values.get("request_id") or uuid4()),
            actor=_clean(values.get("actor")) or "David",
            channel=_clean(values.get("channel")) or "local_api",
            natural_language_command=command,
            action_type=action,
            target_type=target_type,
            target=target,
            environment=_clean(values.get("environment")) or "preview",
            requires_network=bool(values.get("requires_network") or target_type in {"github", "browser", "external_api"}),
            requires_credentials=bool(values.get("requires_credentials")),
            requires_filesystem_write=bool(values.get("requires_filesystem_write")),
            requires_external_write=bool(values.get("requires_external_write")),
            requires_browser=bool(values.get("requires_browser") or target_type == "browser"),
            requires_github=bool(values.get("requires_github") or target_type == "github"),
            requires_api_call=bool(values.get("requires_api_call") or target_type == "external_api"),
            risk_level_declared=declared,
            risk_level_classified=classified,
            risk_downgrade_attempted=RISK_ORDER[declared] < RISK_ORDER[classified],
            approval_context=dict(values.get("approval_context") or {}),
            voice_approval_context=dict(values.get("voice_approval_context") or {}),
            rollback_or_stop_plan=_safe_text(values.get("rollback_or_stop_plan")),
            requested_at=str(values.get("requested_at") or datetime.now(timezone.utc).isoformat()),
        )

    def preview_adapter(self, request: ToolExecutionRequest, **values: Any) -> Dict[str, Any]:
        if request.target_type == "filesystem":
            operation = request.action_type if request.action_type.startswith(("read_", "write_", "patch_", "delete_", "create_")) else "write_file"
            method = getattr(self.filesystem, f"preview_{operation}", self.filesystem.preview_write_file)
            if operation == "write_file":
                return method(request.target, content=values.get("content", ""))
            if operation == "patch_file":
                return method(request.target, patch=values.get("patch", ""))
            if operation == "delete_file":
                return method(request.target, rollback_plan=request.rollback_or_stop_plan)
            return method(request.target)
        if request.target_type == "github":
            method = getattr(self.github, f"preview_{request.action_type}", self.github.preview_create_pr)
            adapter_values = dict(values)
            adapter_values.pop("repo", None)
            return method(repo=request.target, **adapter_values)
        if request.target_type == "browser":
            method = getattr(self.browser, f"preview_{request.action_type}", self.browser.preview_open_url)
            return method(request.target, **values)
        if request.target_type == "external_api":
            method = str(values.get("method") or ("POST" if "post" in request.action_type else "GET"))
            adapter_values = dict(values)
            adapter_values.pop("method", None)
            adapter_values.pop("endpoint", None)
            return self.external_api.candidate_api_call(method, request.target, **adapter_values)
        return {"adapter_name": "unsupported", "blocked_reasons": ["unsupported target type"]}

    def prepare_candidate(
        self,
        request: ToolExecutionRequest,
        *,
        adapter_preview: Dict[str, Any] | None = None,
        kill_switch_active: bool = False,
        stop_phrase_detected: bool = False,
        network_enabled: bool = False,
        access_material_enabled: bool = False,
        production_operations_enabled: bool = False,
        money_movement_enabled: bool = False,
    ) -> ToolExecutionCandidate:
        preview = adapter_preview or self.preview_adapter(request)
        allowlist = bool(preview.get("allowlist_match", request.target_type != "filesystem"))
        denylist = bool(preview.get("denylist_match", False))
        adapter_mutation = bool(preview.get("external_mutation") or preview.get("remote_mutation"))
        credentials_required = bool(request.requires_credentials or preview.get("credentials_required"))
        network_required = bool(request.requires_network or preview.get("network_required"))
        production_impact = bool(preview.get("production_impact"))
        cost_impact = bool(preview.get("cost_impact") or preview.get("triple_confirmation_required"))
        sensitive_payload = bool(preview.get("sensitive_payload_detected"))
        user_data_risk = str(preview.get("user_data_risk") or "low")
        policy = self.policy_engine.evaluate(
            action_type=request.action_type,
            target_type=request.target_type,
            target=request.target,
            environment=request.environment,
            risk_level=request.risk_level_classified,
            requires_network=network_required,
            requires_credentials=credentials_required,
            mutation=request.requires_filesystem_write or request.requires_external_write or adapter_mutation,
            production_impact=production_impact,
            cost_impact=cost_impact,
            allowlist_match=allowlist,
            denylist_match=denylist,
            network_enabled=network_enabled,
            access_material_enabled=access_material_enabled,
            production_operations_enabled=production_operations_enabled,
            money_movement_enabled=money_movement_enabled,
        )
        credentials_required = credentials_required or policy.credentials_required
        network_required = network_required or policy.network_required
        production_impact = production_impact or policy.production_impact
        cost_impact = cost_impact or policy.cost_impact
        approval = _valid_approval(request.approval_context)
        voice = _valid_voice_approval(request.voice_approval_context)
        strong = bool(request.approval_context.get("strong_approval_present") or request.voice_approval_context.get("strong_approval_satisfied"))
        double = bool(request.approval_context.get("double_confirmation_present") or request.voice_approval_context.get("double_confirmation_satisfied"))
        triple = bool(request.approval_context.get("triple_confirmation_present") or request.voice_approval_context.get("triple_confirmation_satisfied"))
        approval_required = bool(policy.approval_required or preview.get("approval_required"))
        strong_required = bool(
            policy.strong_approval_required
            or preview.get("strong_approval_required")
            or sensitive_payload
            or user_data_risk in {"high", "critical"}
        )
        double_required = bool(policy.double_confirmation_required or preview.get("double_confirmation_required"))
        triple_required = bool(policy.triple_confirmation_required or preview.get("triple_confirmation_required"))
        rollback_required = bool(
            policy.rollback_or_stop_plan_required
            or preview.get("rollback_or_stop_plan_required")
            or adapter_mutation
        )
        blocked = list(policy.blocked_reasons) + list(preview.get("blocked_reasons") or [])
        if approval_required and not (approval or voice):
            blocked.append("valid explicit approval required")
        if strong_required and not strong:
            blocked.append("valid strong approval required")
        if double_required and not double:
            blocked.append("double confirmation required")
        if triple_required and not triple:
            blocked.append("triple confirmation required")
        if rollback_required and not request.rollback_or_stop_plan:
            blocked.append("required rollback or stop plan is missing")
        if network_required and not network_enabled:
            blocked.append("external network gate disabled")
        if credentials_required and not access_material_enabled:
            blocked.append("credentials access gate disabled")
        if production_impact and not production_operations_enabled:
            blocked.append("production operations gate disabled")
        if cost_impact and not money_movement_enabled:
            blocked.append("money movement gate disabled")
        if kill_switch_active:
            blocked.append("kill switch active")
        if stop_phrase_detected:
            blocked.append("candidate cancelled by stop phrase")
        blocked = list(dict.fromkeys(blocked))
        return ToolExecutionCandidate(
            candidate_id=str(uuid4()),
            request_id=request.request_id,
            action_type=request.action_type,
            target_type=request.target_type,
            target=request.target,
            adapter_name=str(preview.get("adapter_name") or request.target_type),
            preview_summary=f"Prepare {request.action_type} for {request.target_type}; no real execution.",
            execution_steps=["validate target", "validate sandbox and allowlist", "validate approval", "recheck runtime gates"],
            sandbox_scope=[request.target] if request.target else [],
            allowlist_match=allowlist,
            denylist_match=denylist,
            approval_required=approval_required,
            strong_approval_required=strong_required,
            double_confirmation_required=double_required,
            triple_confirmation_required=triple_required,
            valid_approval_present=approval,
            valid_voice_approval_present=voice,
            eligible_after_valid_approval=bool(
                policy.eligible_after_valid_approval and preview.get("eligible_after_valid_approval", True)
            ),
            execution_allowed=not blocked,
            would_call_external=network_required,
            would_write_filesystem=request.requires_filesystem_write,
            would_modify_remote=request.requires_external_write or adapter_mutation,
            would_touch_production=production_impact,
            would_move_money=cost_impact,
            credentials_required=credentials_required,
            network_required=network_required,
            production_impact=production_impact,
            cost_impact=cost_impact,
            rollback_or_stop_plan_required=rollback_required,
            sensitive_payload_detected=sensitive_payload,
            user_data_risk=user_data_risk,
            rollback_or_stop_plan_present=bool(request.rollback_or_stop_plan),
            blocked_reasons=blocked,
        )

    def preview_result(self, request: ToolExecutionRequest, candidate: ToolExecutionCandidate) -> ToolExecutionResult:
        audit = build_tool_execution_audit_event(
            **request.to_dict(),
            candidate_id=candidate.candidate_id,
            adapter_name=candidate.adapter_name,
            risk_level=request.risk_level_classified.value,
            valid_approval_present=candidate.valid_approval_present,
            valid_voice_approval_present=candidate.valid_voice_approval_present,
            sandbox_scope=candidate.sandbox_scope,
            allowlist_match=candidate.allowlist_match,
            denylist_match=candidate.denylist_match,
        )
        with self._audit_lock:
            self._audit_events[audit.event_id] = audit
            if len(self._audit_events) > 100:
                self._audit_events.pop(next(iter(self._audit_events)))
        mode = "candidate" if candidate.eligible_after_valid_approval else "blocked"
        return ToolExecutionResult(
            result_id=str(uuid4()),
            candidate_id=candidate.candidate_id,
            executed=False,
            success=False,
            mode=mode,
            adapter_name=candidate.adapter_name,
            action_summary=candidate.preview_summary,
            safe_output={"execution_allowed": candidate.execution_allowed, "would_execute": False},
            redacted_output=True,
            audit_event_id=audit.event_id,
            blocked_reasons=candidate.blocked_reasons,
        )

    def preview_readiness(
        self,
        candidate: ToolExecutionCandidate,
        *,
        real_execution_enabled: bool = False,
    ) -> ToolExecutionReadiness:
        reasons = list(candidate.blocked_reasons)
        candidate_ready = candidate.execution_allowed
        execution_ready = candidate_ready and real_execution_enabled
        return ToolExecutionReadiness(
            candidate_id=candidate.candidate_id,
            ready_after_all_gates=execution_ready,
            candidate_ready_after_policy_gates=candidate_ready,
            execution_ready=execution_ready,
            real_execution_enabled=real_execution_enabled,
            approval_ready=candidate.valid_approval_present or candidate.valid_voice_approval_present,
            sandbox_ready=bool(candidate.sandbox_scope),
            allowlist_ready=candidate.allowlist_match,
            denylist_clear=not candidate.denylist_match,
            rollback_ready=candidate.rollback_or_stop_plan_present,
            network_ready=not candidate.would_call_external,
            credentials_ready=not candidate.credentials_required,
            production_ready=not candidate.production_impact,
            kill_switch_clear="kill switch active" not in reasons,
            stop_phrase_clear="candidate cancelled by stop phrase" not in reasons,
            blocked_reasons=reasons,
        )

    def audit_preview(self, event_id: str = "") -> Dict[str, Any]:
        with self._audit_lock:
            if event_id:
                events = [self._audit_events[event_id]] if event_id in self._audit_events else []
            else:
                events = list(self._audit_events.values())[-1:]
        return {"audit_safe": True, "secrets_redacted": True, "events": [event.to_dict() for event in events]}


def _valid_approval(context: Dict[str, Any]) -> bool:
    return bool(context.get("valid_approval_present")) and not any(
        context.get(name) for name in ("expired", "revoked", "scheduler_due", "memory_active", "wake_phrase")
    )


def _valid_voice_approval(context: Dict[str, Any]) -> bool:
    return bool(context.get("valid_voice_approval_present") and context.get("readback_completed")) and not any(
        context.get(name) for name in ("expired", "cancelled", "wake_phrase")
    )


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_text(value: Any) -> str:
    safe, _ = redact_sensitive_data(str(value or ""))
    return _clean(safe)
