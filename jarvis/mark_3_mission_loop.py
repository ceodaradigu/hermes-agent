from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from jarvis.approval_audit import redact_sensitive_data
from jarvis.approval_hardening import ApprovalHardeningService, ApprovalKind, ApprovalStatus, build_context_fingerprint
from jarvis.mark_3_mission_loop_models import (
    UNKNOWN,
    EvidenceItem,
    ExecutionCandidate,
    MissionAuditEvent,
    MissionIntake,
    MissionLoopStatus,
    MissionOutcome,
    MissionWorkingMemory,
    VerificationState,
)
from jarvis.mark_3_mission_loop_policy import classify_mission, validate_intake_payload
from jarvis.mark_3_mission_planner import ControlledMissionPlanner
from jarvis.permission_gates import evaluate_permission_gate


TERMINAL_BLOCKING = {MissionLoopStatus.STOPPED, MissionLoopStatus.DENIED, MissionLoopStatus.FAILED}
INTERNAL_CAPABILITIES = {"internal_prepare"}
STEP_TERMINAL_STATUSES = {"completed", "failed", "stopped", "skipped"}


class Mark3MissionLoop:
    """In-memory governed mission loop. It never invokes external tools."""

    def __init__(
        self,
        *,
        approval_service: Optional[ApprovalHardeningService] = None,
        clock: Optional[Callable[[], str]] = None,
        id_factory: Optional[Callable[[], str]] = None,
        test_adapters: Optional[Dict[str, Callable[[ExecutionCandidate], Dict[str, Any]]]] = None,
    ) -> None:
        self.approval_service = approval_service or ApprovalHardeningService()
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self.id_factory = id_factory or (lambda: str(uuid4()))
        self.planner = ControlledMissionPlanner(id_factory=self.id_factory)
        self._missions: Dict[str, MissionWorkingMemory] = {}
        self._test_adapters = dict(test_adapters or {})
        self._kill_switch_active = False

    def status(self) -> Dict[str, Any]:
        return {
            "mark": "Mark 3",
            "mission_loop_available": True,
            "in_memory_only": True,
            "mission_count": len(self._missions),
            "kill_switch_active": self._kill_switch_active,
            "external_execution_enabled": False,
            "external_side_effects_enabled": False,
            "real_tools_connected": False,
            "safe_to_render": True,
        }

    def policy(self) -> Dict[str, Any]:
        return {
            **self.status(),
            "preview_first": True,
            "default_deny": True,
            "approval_is_not_execution": True,
            "candidate_is_not_execution": True,
            "memory_is_not_permission": True,
            "wake_phrase_is_not_permission": True,
            "approval_per_step": True,
            "level_5_permanently_denied": True,
            "unknown_values_preserved": True,
            "test_adapters_internal_simulation_only": True,
            "pr_134_connects_governed_real_execution": True,
        }

    def create_mission(self, values: Dict[str, Any]) -> Dict[str, Any]:
        errors = validate_intake_payload(values)
        if errors:
            raise ValueError("; ".join(errors))
        now = self.clock()
        mission_id = _text(values.get("mission_id")) or self.id_factory()
        if mission_id in self._missions:
            return self._missions[mission_id].to_dict()
        correlation_id = _text(values.get("correlation_id")) or self.id_factory()
        intake = MissionIntake(
            mission_id=mission_id,
            objective=_safe_text(values.get("objective")),
            context=_safe_text(values.get("context")),
            desired_outcome=_safe_text(values.get("desired_outcome")) or UNKNOWN,
            success_criteria=_items(values.get("success_criteria")),
            declared_authorization=_safe_text(values.get("declared_authorization")) or UNKNOWN,
            allowed_scope=_items(values.get("allowed_scope", values.get("scope"))),
            allowed_paths_resources=_items(values.get("allowed_paths_resources")),
            allowed_tools=_items(values.get("allowed_tools")),
            prohibited_tools=_items(values.get("prohibited_tools")),
            monetary_budget=values.get("monetary_budget"),
            time_budget_seconds=values.get("time_budget_seconds"),
            max_steps=int(values.get("max_steps", 10)),
            allowed_data=_items(values.get("allowed_data")),
            constraints=_items(values.get("constraints")),
            stop_conditions=_items(values.get("stop_conditions")) or ["stop on policy violation"],
            expected_rollback=_safe_text(values.get("expected_rollback")) or UNKNOWN,
            instruction_origin=_safe_text(values.get("instruction_origin")) or UNKNOWN,
            direct_intent_evidence=_safe_optional(values.get("direct_intent_evidence")),
            created_at=now,
            updated_at=now,
            correlation_id=correlation_id,
            requested_risk_level=values.get("requested_risk_level", values.get("risk_level")),
            proposed_steps=_safe_list_of_dicts(values.get("proposed_steps")),
            uncertainties=_items(values.get("uncertainties")),
            metadata=_safe_dict(values.get("metadata")),
        )
        memory = MissionWorkingMemory(intake=intake)
        self._missions[mission_id] = memory
        self._audit(memory, "mission_received", "Mission intake received and stored in-memory.")
        return memory.to_dict()

    def get_mission(self, mission_id: str) -> Dict[str, Any]:
        return self._get(mission_id).to_dict()

    def audit(self, mission_id: str) -> Dict[str, Any]:
        memory = self._get(mission_id)
        return {
            "mission_id": mission_id,
            "append_only": True,
            "in_memory_only": True,
            "events": [item.to_dict() for item in memory.audit],
        }

    def set_kill_switch(self, active: bool, *, reason: str = "operator control") -> Dict[str, Any]:
        self._kill_switch_active = bool(active)
        if active:
            for memory in self._missions.values():
                memory.kill_switch_active = True
                if memory.status not in TERMINAL_BLOCKING | {MissionLoopStatus.COMPLETED}:
                    self.stop(memory.intake.mission_id, reason=f"kill switch active: {reason}")
        return self.status()

    def stop(self, mission_id: str, *, reason: str) -> Dict[str, Any]:
        memory = self._get(mission_id)
        reason = _text(reason)
        if not reason:
            raise ValueError("stop reason must be non-empty")
        if memory.status == MissionLoopStatus.STOPPED:
            return memory.to_dict()
        memory.status = MissionLoopStatus.STOPPED
        memory.stop_reason = _safe_text(reason)
        memory.next_action = "none; explicit governed restart transition is not implemented"
        for step in memory.plan:
            if step.status not in {"completed", "failed"}:
                step.status = "stopped"
                step.blocked_reasons = list(dict.fromkeys(step.blocked_reasons + ["mission stopped"]))
        for candidate in memory.candidates:
            candidate.eligibility = False
            candidate.blocked_reasons = list(dict.fromkeys(candidate.blocked_reasons + ["mission stopped"]))
        self._audit(memory, "mission_stopped", "Mission stopped; prior audit and evidence retained.", {"reason": reason})
        return memory.to_dict()

    def advance(self, mission_id: str, *, approval_id: Optional[str] = None, step_id: Optional[str] = None) -> Dict[str, Any]:
        memory = self._get(mission_id)
        if self._kill_switch_active or memory.kill_switch_active:
            return self.stop(mission_id, reason="kill switch active")
        if memory.status in TERMINAL_BLOCKING:
            return memory.to_dict()
        if approval_id:
            self._apply_approval(memory, approval_id, step_id)
        status = memory.status
        if status == MissionLoopStatus.RECEIVED:
            memory.classification = classify_mission(memory.intake, available_capabilities=INTERNAL_CAPABILITIES)
            memory.status = MissionLoopStatus.DENIED if memory.classification.permanent_denial else MissionLoopStatus.CLASSIFIED
            memory.next_action = "none" if memory.classification.permanent_denial else "build deterministic plan"
            self._audit(memory, "mission_classified", f"Mission classified at risk level {memory.classification.risk_level}.")
        elif status == MissionLoopStatus.CLASSIFIED:
            memory.status = MissionLoopStatus.PLANNING
            memory.next_action = "validate deterministic plan"
            self._audit(memory, "planning_started", "Deterministic planning started.")
        elif status == MissionLoopStatus.PLANNING:
            memory.plan = self.planner.plan(memory.intake, memory.classification)
            memory.status = MissionLoopStatus.PLANNED
            memory.next_action = "prepare preview"
            self._audit(memory, "plan_created", "Deterministic bounded plan created.", {"steps": len(memory.plan)})
        elif status == MissionLoopStatus.PLANNED:
            memory.status = MissionLoopStatus.PREVIEW_READY
            memory.next_action = "review preview and approval requirements"
            self._audit(memory, "preview_ready", "Mission preview is ready; nothing executed.")
        elif status in {MissionLoopStatus.PREVIEW_READY, MissionLoopStatus.AWAITING_APPROVAL, MissionLoopStatus.BLOCKED}:
            self._prepare_candidates(memory)
        elif status == MissionLoopStatus.EXECUTION_CANDIDATE_READY:
            self._prepare_candidates(memory)
            if memory.status == MissionLoopStatus.EXECUTION_CANDIDATE_READY:
                memory.status = MissionLoopStatus.RESULT_PENDING
                memory.next_action = "record honest outcome and compatible evidence"
                self._audit(memory, "result_pending", "Candidate is ready but this PR does not execute it.")
        elif status == MissionLoopStatus.RESULT_PENDING:
            self._recalculate_mission_result_status(memory)
        elif status == MissionLoopStatus.COMPLETED:
            self._build_post_mortem(memory)
        elif status == MissionLoopStatus.POST_MORTEM_READY:
            self._build_learning_proposal(memory)
        return memory.to_dict()

    def execute_candidate_internal(self, mission_id: str, candidate_id: str, adapter_name: str) -> Dict[str, Any]:
        memory = self._get(mission_id)
        candidate = next((item for item in memory.candidates if item.candidate_id == candidate_id), None)
        if candidate is None:
            raise KeyError(candidate_id)
        blocked = self._candidate_runtime_blocks(memory, candidate, adapter_name)
        if blocked:
            candidate.eligibility = False
            candidate.blocked_reasons = list(dict.fromkeys(candidate.blocked_reasons + blocked))
            self._audit(memory, "internal_adapter_blocked", "Internal test adapter candidate blocked.", {"reasons": blocked})
            return candidate.to_dict()
        memory.status = MissionLoopStatus.RUNNING_INTERNAL
        raw = self._test_adapters[adapter_name](candidate)
        safe, redacted = redact_sensitive_data(raw if isinstance(raw, dict) else {"result": raw})
        result = {
            "mode": "internal_test_simulation",
            "simulated": True,
            "external_execution": False,
            "external_side_effects": False,
            "did_execute": False,
            "adapter_name": adapter_name,
            "safe_result": safe,
            "redacted_fields": redacted,
        }
        memory.status = MissionLoopStatus.RESULT_PENDING
        self._audit(memory, "internal_test_simulation_completed", "Injected test adapter returned internal simulated validation output.")
        return result

    def record_outcome(self, mission_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
        memory = self._get(mission_id)
        if memory.status in TERMINAL_BLOCKING:
            raise ValueError(f"cannot record a new outcome while mission is {memory.status.value}")
        if memory.status not in {
            MissionLoopStatus.EXECUTION_CANDIDATE_READY,
            MissionLoopStatus.RUNNING_INTERNAL,
            MissionLoopStatus.RESULT_PENDING,
        }:
            raise ValueError("outcome cannot be recorded before a bounded candidate reaches result_pending")
        step_status = self._outcome_step_status(memory, values)
        status_reason = _safe_text(values.get("status_reason"))
        if step_status in {"failed", "stopped", "skipped"} and not status_reason:
            raise ValueError(f"step status {step_status} requires status_reason")
        evidence_ids: List[str] = []
        compatible_verified = False
        claim = _safe_text(values.get("summary")) or UNKNOWN
        for item in values.get("evidence") or []:
            evidence = self._build_evidence(memory, item, claim)
            memory.evidence.append(evidence)
            evidence_ids.append(evidence.evidence_id)
            compatible_verified = compatible_verified or (
                evidence.verification_state == VerificationState.VERIFIED
                and evidence.supported_claim.lower() == claim.lower()
            )
        requested_state = VerificationState(values.get("verification_state", VerificationState.REPORTED.value))
        actual_state = requested_state
        if requested_state == VerificationState.VERIFIED and not compatible_verified:
            actual_state = VerificationState.REPORTED
        outcome = MissionOutcome(
            outcome_id=self.id_factory(),
            mission_id=mission_id,
            step_id=_safe_optional(values.get("step_id")),
            summary=claim,
            verification_state=actual_state,
            evidence_ids=evidence_ids,
            step_status=step_status,
            status_reason=status_reason,
            costs_known=self._verified_metric(memory, evidence_ids, "costs_known", values.get("costs_known", UNKNOWN)),
            revenue_known=self._verified_metric(memory, evidence_ids, "revenue_known", values.get("revenue_known", UNKNOWN)),
            time_known_seconds=self._verified_metric(
                memory, evidence_ids, "time_known_seconds", values.get("time_known_seconds", UNKNOWN)
            ),
            recorded_at=self.clock(),
        )
        memory.outcomes.append(outcome)
        if outcome.step_id:
            step = self._step(memory, outcome.step_id)
            step.status = outcome.step_status
        memory.status = MissionLoopStatus.RESULT_PENDING
        memory.next_action = "record outcomes for remaining steps or finalize mission result"
        self._audit(memory, "outcome_recorded", f"Outcome recorded as {actual_state.value}.", {"outcome_id": outcome.outcome_id})
        return memory.to_dict()

    def add_feedback(self, mission_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
        memory = self._get(mission_id)
        safe, _ = redact_sensitive_data(dict(values))
        feedback = {
            "feedback_id": self.id_factory(),
            "timestamp": self.clock(),
            "content": safe,
            "persisted": False,
            "grants_permission": False,
        }
        memory.feedback.append(feedback)
        self._audit(memory, "feedback_recorded", "Feedback recorded in mission working memory only.")
        return memory.to_dict()

    def _prepare_candidates(self, memory: MissionWorkingMemory) -> None:
        memory.candidates = []
        memory.approval_requirements = []
        waiting = False
        hard_block = False
        pending_steps = 0
        eligible_pending = False
        for step in memory.plan:
            approval_blocks = self._revalidate_step_approval(memory, step)
            context = self._step_context(memory, step)
            fingerprint = build_context_fingerprint(context)
            requirement = {
                "mission_id": memory.intake.mission_id,
                "step_id": step.step_id,
                "exact_action": step.description,
                "approval_required": step.approval_required,
                "strong_approval_required": step.strong_approval_required,
                "double_confirmation_required": step.double_confirmation_required,
                "triple_confirmation_required": step.triple_confirmation_required,
                "readback_required": step.risk_level == 4,
                "context_fingerprint": fingerprint,
                "approval_satisfied": step.approval_satisfied,
                "approval_id": step.approval_id,
            }
            blocked = [
                reason for reason in step.blocked_reasons
                if not _is_transient_candidate_block(reason)
            ]
            blocked.extend(approval_blocks)
            blocked.extend(self._dependency_blocks(memory, step))
            classification_blocks = memory.classification.blocked_reasons if memory.classification else []
            blocked.extend(reason for reason in classification_blocks if reason != "required capability is unavailable")
            terminal = step.status in STEP_TERMINAL_STATUSES
            if terminal:
                blocked.append(f"step already terminal: {step.status}")
            else:
                pending_steps += 1
            if not terminal and step.approval_required and not step.approval_satisfied:
                blocked.append("valid step-bound approval required")
                waiting = True
            if not terminal and (not step.capability_available or any(
                reason != "required capability is unavailable" for reason in classification_blocks
            )):
                blocked.append("execution capability unavailable")
                hard_block = True
            candidate = ExecutionCandidate(
                candidate_id=f"candidate-{step.step_id}",
                mission_id=memory.intake.mission_id,
                step_id=step.step_id,
                exact_action=step.description,
                adapter_capability=step.required_capability,
                tool_candidate=step.tool_candidate,
                scope=list(step.scope),
                budget=step.budget,
                timeout_seconds=step.timeout_seconds,
                risk_level=step.risk_level,
                approval_requirement=requirement,
                context_fingerprint=fingerprint,
                audit_correlation_id=memory.intake.correlation_id,
                stop_plan=step.stop_condition,
                rollback_plan=step.rollback_compensation,
                evidence_requirements=list(step.evidence_requirements),
                capability_available=step.capability_available,
                eligibility=not blocked,
                blocked_reasons=list(dict.fromkeys(blocked)),
                approval_required=step.approval_required,
                approval_satisfied=step.approval_satisfied,
                execution_capability_available=step.capability_available,
            )
            memory.candidates.append(candidate)
            eligible_pending = eligible_pending or (not terminal and candidate.eligibility)
            if step.approval_required:
                memory.approval_requirements.append(requirement)
        if pending_steps == 0:
            memory.status = MissionLoopStatus.RESULT_PENDING
            memory.next_action = "finalize mission result"
        elif hard_block:
            memory.status = MissionLoopStatus.BLOCKED
            memory.next_action = "resolve capability, scope, budget, tool, or policy blocks"
        elif waiting:
            memory.status = MissionLoopStatus.AWAITING_APPROVAL
            memory.next_action = "satisfy exact per-step approval requirements"
        elif eligible_pending:
            memory.status = MissionLoopStatus.EXECUTION_CANDIDATE_READY
            memory.next_action = "use eligible bounded candidate; blocked steps remain unavailable"
        elif any(
            not _is_approval_block(reason)
            for candidate in memory.candidates
            for reason in candidate.blocked_reasons
            if "step already terminal" not in reason
        ):
            memory.status = MissionLoopStatus.BLOCKED
            memory.next_action = "resolve capability, scope, budget, tool, or policy blocks"
        else:
            memory.status = MissionLoopStatus.EXECUTION_CANDIDATE_READY
            memory.next_action = "hand candidate to PR #134 governed execution engine"
        self._audit(memory, "execution_candidates_prepared", "Bounded execution candidates prepared; nothing executed.")

    def _apply_approval(self, memory: MissionWorkingMemory, approval_id: str, step_id: Optional[str]) -> None:
        if not step_id:
            raise ValueError("step_id is required; approvals never inherit across steps")
        step = next((item for item in memory.plan if item.step_id == step_id), None)
        if step is None:
            raise KeyError(step_id)
        record = self.approval_service.get(approval_id)
        context = self._step_context(memory, step)
        gate = evaluate_permission_gate(context, record, audit_trail=self.approval_service.audit_trail)
        missing = list(gate.missing_requirements)
        if step.strong_approval_required and record.approval_kind != ApprovalKind.STRONG:
            missing.append("strong approval required")
        if step.double_confirmation_required:
            missing.append("double confirmation record integration is required by PR #134")
        if step.triple_confirmation_required:
            missing.append("triple confirmation record integration is required by PR #134")
        if step.risk_level == 4:
            missing.append("readback record integration is required by PR #134")
        if record.status != ApprovalStatus.APPROVED:
            missing.append(f"approval status is {record.status.value}")
        if missing or not gate.allowed:
            step.approval_satisfied = False
            step.blocked_reasons = list(dict.fromkeys(step.blocked_reasons + missing))
            self._audit(memory, "approval_rejected_for_step", "Approval did not satisfy exact step requirement.", {"step_id": step_id})
            return
        step.approval_satisfied = True
        step.approval_id = approval_id
        step.blocked_reasons = [reason for reason in step.blocked_reasons if "approval" not in reason]
        self._audit(memory, "approval_satisfied_for_step", "Exact step-bound approval requirement satisfied.", {"step_id": step_id, "approval_id": approval_id})

    def _step_context(self, memory: MissionWorkingMemory, step: Any) -> Dict[str, Any]:
        exact_contract = {
            "mission_id": memory.intake.mission_id,
            "step_id": step.step_id,
            "exact_action": step.description,
            "action_type": step.action_type,
            "scope": step.scope,
            "tool": step.tool_candidate,
            "budget": step.budget,
            "timeout_seconds": step.timeout_seconds,
            "risk_level": step.risk_level,
        }
        contract_hash = hashlib.sha256(
            json.dumps(exact_contract, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        context = {
            "action_type": step.action_type,
            "target": step.description,
            "user_payload": {
                "mission_id": memory.intake.mission_id,
                "step_id": step.step_id,
                "scope": step.scope,
                "risk_level": step.risk_level,
                "exact_contract_sha256": contract_hash,
            },
        }
        if step.tool_candidate:
            context["tool_name"] = step.tool_candidate
        if step.budget is not None and step.budget > 0:
            context["budget"] = step.budget
        return context

    def approval_context(self, mission_id: str, step_id: str) -> Dict[str, Any]:
        memory = self._get(mission_id)
        step = next(item for item in memory.plan if item.step_id == step_id)
        return self._step_context(memory, step)

    def _candidate_runtime_blocks(self, memory: MissionWorkingMemory, candidate: ExecutionCandidate, adapter_name: str) -> List[str]:
        blocked: List[str] = []
        step = self._step(memory, candidate.step_id)
        approval_blocks = self._revalidate_step_approval(memory, step)
        dependency_blocks = self._dependency_blocks(memory, step)
        blocked.extend(approval_blocks)
        blocked.extend(dependency_blocks)
        candidate.approval_satisfied = step.approval_satisfied
        candidate.approval_requirement["approval_satisfied"] = step.approval_satisfied
        candidate.eligibility = candidate.eligibility and not approval_blocks and not dependency_blocks
        if self._kill_switch_active or memory.kill_switch_active:
            blocked.append("kill switch active")
        if memory.status == MissionLoopStatus.STOPPED:
            blocked.append("mission stopped")
        if adapter_name not in self._test_adapters:
            blocked.append("adapter is not a registered injected test adapter")
        if candidate.adapter_capability not in INTERNAL_CAPABILITIES:
            blocked.append("capability is not registered as internal")
        if not candidate.eligibility:
            blocked.append("candidate is not eligible")
        if not set(candidate.scope).issubset(set(memory.intake.allowed_scope)):
            blocked.append("scope mismatch")
        if candidate.tool_candidate and candidate.tool_candidate not in memory.intake.allowed_tools:
            blocked.append("tool mismatch")
        if candidate.budget is not None and memory.intake.monetary_budget is not None and candidate.budget > memory.intake.monetary_budget:
            blocked.append("budget exceeded")
        if candidate.exact_action != step.description:
            blocked.append("exact action mismatch")
        if candidate.scope != step.scope:
            blocked.append("candidate scope does not match step scope")
        if candidate.tool_candidate != step.tool_candidate:
            blocked.append("candidate tool does not match step tool")
        if candidate.budget != step.budget:
            blocked.append("candidate budget does not match step budget")
        if candidate.context_fingerprint != build_context_fingerprint(self._step_context(memory, step)):
            blocked.append("fingerprint mismatch")
        if blocked:
            candidate.eligibility = False
        return list(dict.fromkeys(blocked))

    def _revalidate_step_approval(self, memory: MissionWorkingMemory, step: Any) -> List[str]:
        if not step.approval_required:
            step.approval_satisfied = True
            return []
        if not step.approval_id:
            step.approval_satisfied = False
            return ["valid step-bound approval required"]
        try:
            record = self.approval_service.get(step.approval_id)
        except KeyError:
            step.approval_satisfied = False
            return ["approval record not found"]
        self.approval_service.refresh_expiration(record)
        context = self._step_context(memory, step)
        expected_fingerprint = build_context_fingerprint(context)
        blocked: List[str] = []
        if record.status != ApprovalStatus.APPROVED:
            blocked.append(f"approval status is {record.status.value}")
        if record.action_type != step.action_type:
            blocked.append("approval action mismatch")
        if record.context_fingerprint != expected_fingerprint:
            blocked.append("approval context fingerprint mismatch")
        if step.strong_approval_required and record.approval_kind != ApprovalKind.STRONG:
            blocked.append("strong approval required")
        gate = evaluate_permission_gate(context, record, audit_trail=self.approval_service.audit_trail)
        blocked.extend(gate.missing_requirements)
        step.approval_satisfied = not blocked and gate.allowed
        if not step.approval_satisfied:
            step.blocked_reasons = list(dict.fromkeys(step.blocked_reasons + blocked))
        return list(dict.fromkeys(blocked))

    def _dependency_blocks(self, memory: MissionWorkingMemory, step: Any) -> List[str]:
        blocked: List[str] = []
        for dependency_id in step.dependencies:
            dependency = self._step(memory, dependency_id)
            outcome = self._latest_step_outcome(memory, dependency_id)
            if dependency.status != "completed":
                blocked.append(f"dependency {dependency_id} status is {dependency.status}")
            elif outcome is None:
                blocked.append(f"dependency {dependency_id} has no outcome")
            elif outcome.verification_state in {VerificationState.REJECTED, VerificationState.UNKNOWN}:
                blocked.append(f"dependency {dependency_id} outcome is not policy-compatible")
        return blocked

    def _outcome_step_status(self, memory: MissionWorkingMemory, values: Dict[str, Any]) -> str:
        step_id = _safe_optional(values.get("step_id"))
        if not step_id:
            if len(memory.plan) != 1:
                raise ValueError("step_id is required for multi-step mission outcomes")
            step_id = memory.plan[0].step_id
            values["step_id"] = step_id
        self._step(memory, step_id)
        status = _text(values.get("step_status")) or "completed"
        if status not in STEP_TERMINAL_STATUSES:
            raise ValueError("step_status must be completed, failed, stopped, or skipped")
        if status == "completed":
            dependency_blocks = self._dependency_blocks(memory, self._step(memory, step_id))
            if dependency_blocks:
                raise ValueError("completed outcome blocked by dependencies: " + "; ".join(dependency_blocks))
        return status

    def _recalculate_mission_result_status(self, memory: MissionWorkingMemory) -> None:
        pending = [step for step in memory.plan if self._latest_step_outcome(memory, step.step_id) is None]
        failed = [step for step in memory.plan if step.status == "failed"]
        stopped = [step for step in memory.plan if step.status == "stopped"]
        skipped = [step for step in memory.plan if step.status == "skipped"]
        incompatible = [
            step for step in memory.plan
            if (outcome := self._latest_step_outcome(memory, step.step_id)) is not None
            and outcome.verification_state in {VerificationState.REJECTED, VerificationState.UNKNOWN}
        ]
        if failed:
            memory.status = MissionLoopStatus.FAILED
            memory.next_action = "generate failure post-mortem"
            memory.post_mortem = self._post_mortem_payload(memory)
            self._audit(memory, "mission_failed", "Mission failed because at least one required step failed.")
        elif stopped:
            memory.status = MissionLoopStatus.STOPPED
            memory.stop_reason = "at least one required step stopped"
            memory.next_action = "none; mission stopped"
            memory.post_mortem = self._post_mortem_payload(memory)
            self._audit(memory, "mission_stopped", "Mission stopped because at least one required step stopped.")
        elif skipped:
            memory.status = MissionLoopStatus.BLOCKED
            memory.next_action = "review explicitly skipped required steps"
            memory.post_mortem = self._post_mortem_payload(memory)
            self._audit(memory, "mission_blocked", "Mission cannot complete with skipped required steps.")
        elif incompatible:
            memory.status = MissionLoopStatus.BLOCKED
            memory.next_action = "resolve rejected or unknown step outcomes"
            memory.post_mortem = self._post_mortem_payload(memory)
            self._audit(memory, "mission_blocked", "Mission cannot complete with rejected or unknown step outcomes.")
        elif pending:
            self._prepare_candidates(memory)
        elif all(step.status == "completed" for step in memory.plan):
            memory.status = MissionLoopStatus.COMPLETED
            memory.next_action = "generate post-mortem"
            self._audit(memory, "mission_completed", "All required steps have compatible recorded outcomes.")

    def _latest_step_outcome(self, memory: MissionWorkingMemory, step_id: str) -> Optional[MissionOutcome]:
        return next((item for item in reversed(memory.outcomes) if item.step_id == step_id), None)

    def _step(self, memory: MissionWorkingMemory, step_id: str) -> Any:
        try:
            return next(item for item in memory.plan if item.step_id == step_id)
        except StopIteration as exc:
            raise KeyError(step_id) from exc

    def _build_evidence(self, memory: MissionWorkingMemory, values: Dict[str, Any], claim: str) -> EvidenceItem:
        safe, redacted = redact_sensitive_data(dict(values))
        description = _safe_text(safe.get("description")) or UNKNOWN
        reference = _safe_text(safe.get("safe_hash_reference"))
        if not reference:
            reference = "sha256:" + hashlib.sha256(json.dumps(safe, sort_keys=True, default=str).encode()).hexdigest()
        state = VerificationState(safe.get("verification_state", VerificationState.REPORTED.value))
        source_type = _text(safe.get("source_type")) or UNKNOWN
        if state == VerificationState.VERIFIED and source_type not in {
            "internal_observation",
            "test_adapter_observation",
            "audit_reference",
        }:
            state = VerificationState.REPORTED
        return EvidenceItem(
            evidence_id=_text(safe.get("evidence_id")) or self.id_factory(),
            source_type=source_type,
            description=description,
            correlation_id=_text(safe.get("correlation_id")) or memory.intake.correlation_id,
            timestamp=_text(safe.get("timestamp")) or self.clock(),
            verification_state=state,
            redaction_status="redacted" if redacted else "checked_no_sensitive_content",
            safe_hash_reference=reference,
            limitations=_items(safe.get("limitations")) or [UNKNOWN],
            supported_claim=_safe_text(safe.get("supported_claim")) or UNKNOWN,
        )

    def _verified_metric(self, memory: MissionWorkingMemory, evidence_ids: List[str], name: str, value: Any) -> Any:
        if value == UNKNOWN:
            return UNKNOWN
        compatible = any(
            item.evidence_id in evidence_ids
            and item.verification_state == VerificationState.VERIFIED
            and item.supported_claim == name
            for item in memory.evidence
        )
        return value if compatible else UNKNOWN

    def _build_post_mortem(self, memory: MissionWorkingMemory) -> None:
        memory.post_mortem = self._post_mortem_payload(memory)
        memory.status = MissionLoopStatus.POST_MORTEM_READY
        memory.next_action = "generate learning proposal preview"
        self._audit(memory, "post_mortem_ready", "Evidence-linked post-mortem generated.")

    def _post_mortem_payload(self, memory: MissionWorkingMemory) -> Dict[str, Any]:
        verified = [item for item in memory.outcomes if item.verification_state == VerificationState.VERIFIED]
        pending_steps = [
            step.step_id for step in memory.plan
            if self._latest_step_outcome(memory, step.step_id) is None
        ]
        achieved = list(memory.intake.success_criteria) if memory.outcomes and len(verified) == len(memory.outcomes) else []
        return {
            "objective": memory.intake.objective,
            "outcome": [item.to_dict() for item in memory.outcomes] or UNKNOWN,
            "steps": [
                {
                    "step_id": step.step_id,
                    "status": step.status,
                    "outcome": (
                        self._latest_step_outcome(memory, step.step_id).to_dict()
                        if self._latest_step_outcome(memory, step.step_id)
                        else UNKNOWN
                    ),
                }
                for step in memory.plan
            ],
            "criteria_achieved": achieved,
            "criteria_not_achieved": [item for item in memory.intake.success_criteria if item not in achieved],
            "failures": UNKNOWN,
            "blockers": list(memory.classification.blocked_reasons if memory.classification else []),
            "scope_used": sorted({scope for step in memory.plan for scope in step.scope}) or UNKNOWN,
            "budget_used": UNKNOWN,
            "time_known": next((item.time_known_seconds for item in memory.outcomes if item.time_known_seconds != UNKNOWN), UNKNOWN),
            "costs_known": next((item.costs_known for item in memory.outcomes if item.costs_known != UNKNOWN), UNKNOWN),
            "unknowns": list(dict.fromkeys(
                (memory.classification.uncertainties if memory.classification else [])
                + ["unverified costs", "unverified revenue"]
                + [f"pending step outcome: {step_id}" for step_id in pending_steps]
            )),
            "evidence": [item.evidence_id for item in memory.evidence],
            "risks_observed": [memory.classification.risk_level] if memory.classification else [UNKNOWN],
            "what_to_stop": ["any action outside approved scope or without evidence"],
            "what_to_continue": ["governed previews and evidence collection"],
            "next_action": "review learning proposal preview",
            "confidence": "medium" if verified else "low",
            "justification": "Based only on recorded mission outcomes and evidence.",
        }

    def _build_learning_proposal(self, memory: MissionWorkingMemory) -> None:
        evidence_refs = [item.evidence_id for item in memory.evidence if item.verification_state == VerificationState.VERIFIED]
        decision = "retain_for_review" if evidence_refs else "investigate"
        memory.learning_proposal_preview = {
            "proposal_id": self.id_factory(),
            "decision_suggested": decision,
            "confidence": "medium" if evidence_refs else "low",
            "evidence_references": evidence_refs,
            "revisable": True,
            "reversible": True,
            "persisted": False,
            "activated": False,
            "grants_permission": False,
        }
        memory.status = MissionLoopStatus.LEARNING_PROPOSAL_READY
        memory.next_action = "human review; do not persist or activate in PR #133"
        self._audit(memory, "learning_proposal_ready", "Non-persisted, non-activated learning proposal preview generated.")

    def _audit(self, memory: MissionWorkingMemory, event_type: str, summary: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        safe, redacted = redact_sensitive_data(metadata or {})
        memory.audit.append(MissionAuditEvent(
            event_id=self.id_factory(),
            mission_id=memory.intake.mission_id,
            event_type=event_type,
            timestamp=self.clock(),
            correlation_id=memory.intake.correlation_id,
            summary=_safe_text(summary),
            metadata=safe,
            redacted_fields=redacted,
        ))

    def _get(self, mission_id: str) -> MissionWorkingMemory:
        try:
            return self._missions[mission_id]
        except KeyError as exc:
            raise KeyError(f"mission not found: {mission_id}") from exc


def _safe_dict(value: Any) -> Dict[str, Any]:
    safe, _ = redact_sensitive_data(dict(value or {}))
    return safe


def _safe_list_of_dicts(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    safe, _ = redact_sensitive_data(value)
    return [dict(item) for item in safe if isinstance(item, dict)]


def _safe_text(value: Any) -> str:
    safe, _ = redact_sensitive_data(str(value or ""))
    return _text(safe)


def _safe_optional(value: Any) -> Optional[str]:
    return _safe_text(value) or None


def _items(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_safe_text(item) for item in value if _safe_text(item)]
    return [_safe_text(value)] if _safe_text(value) else []


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _is_approval_block(reason: str) -> bool:
    lowered = reason.lower()
    return "approval" in lowered or "approved context" in lowered or "confirmation" in lowered or "readback" in lowered


def _is_transient_candidate_block(reason: str) -> bool:
    lowered = reason.lower()
    return (
        _is_approval_block(reason)
        or lowered.startswith("dependency ")
        or lowered.startswith("step already terminal")
        or lowered in {"candidate is not eligible", "fingerprint mismatch"}
    )
