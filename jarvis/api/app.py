from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from jarvis.asset_factory.foundation import (
    AssetFactoryStatus,
    AssetGenerationPolicy,
    BuildPackagePreview,
    CopyContentPackPreview,
    LandingPagePlan,
    MonetizationOfferPreview,
    PublishingReadinessPreview,
    StaticAssetManifestPreview,
    WebProjectBrief,
    WebsiteStructurePlan,
)
from jarvis.advanced_personalization.foundation import (
    AdvancedPersonalizationStatus,
    BusinessGoalModelPreview,
    ContrarianModeProfilePreview,
    DecisionModelPreview,
    MemoryAuditReversalPreview,
    MemoryLifecyclePreview,
    MemoryProposalPreview,
    MemoryReviewPreview,
    PersonalizationApprovalRequirements,
    PersonalizationRecommendationPreview,
    SensitiveInferenceGuardPreview,
    SpeechStylePatternPreview,
    UncertaintyHandlingPreview,
    UserModelSafetyPolicy,
    UserPreferenceProfilePreview,
)
from jarvis.ambient_vision.companion import (
    AmbientVisionPrivacyPolicy,
    AmbientVisionSessionPreview,
    AmbientVisionStatus,
    AmbientVisionStopControl,
)
from jarvis.approval_hardening import ApprovalHardeningService, StrongApprovalPolicy
from jarvis.approval_execution_semantics import GlobalApprovalExecutionSemantics
from jarvis.adaptive_saas_builder import AdaptiveSaaSBuilder
from jarvis.camera_control_runtime import CameraControlRuntime
from jarvis.command_center import build_command_center_view_model
from jarvis.controlled_runtime_bridge import ControlledRuntimeBridge
from jarvis.dashboard_event_stream import build_jarvis_event_snapshot, encode_sse_event
from jarvis.dashboard_read_model import build_local_doctor_status, build_mark_3_dashboard_status
from jarvis.desktop_runtime import DesktopRuntime
from jarvis.continuous_learning.foundation import (
    ApprovalWorkflowPreview,
    ContinuousLearningStatus,
    ContrarianReviewPreview,
    LearningBacklogPreview,
    LearningProposalPreview,
    PRPlannerPreview,
    ProposalImpactAnalysis,
    ProposalRiskAnalysis,
    RelevanceFilterPreview,
    TechRadarDecisionPreview,
    TechRadarSafetyPolicy,
    TechnologyCandidateProfile,
)
from jarvis.deploy_publishing.foundation import (
    DeployPublishingPolicy,
    DeployPublishingStatus,
    DeploymentTargetPreview,
    DomainConnectionPreview,
    ExternalAccountConnectionPreview,
    ProductionReleasePreview,
    PublishingApprovalRequirements,
    PublishingPlanPreview,
    PublishingReadinessChecklist,
    PublishingRollbackPreview,
)
from jarvis.daily_operator.scheduler import (
    DailyBriefingPreview,
    DailyOperatorSchedulerStatus,
    DailyPlanPreview,
    ExecutionWindowPreview,
    MissedRunRetryPolicyPreview,
    OperatorHandoffSummaryPreview,
    RecurrencePreview,
    ReminderNotificationPreview,
    ScheduleRulePreview,
    SchedulerApprovalRequirements,
    SchedulerSafetyPolicy,
    TaskQueuePreview,
)
from jarvis.future_moonshot.foundation import (
    AROverlayPreview,
    ControlledEnvironmentPreview,
    DeepSimulationPreview,
    FutureMoonshotStatus,
    IdentityImpersonationGuardPreview,
    ImmediateStopPreview,
    LegalSafetyReviewPreview,
    MonetizationAdvantageReviewPreview,
    MoonshotApprovalRequirements,
    MoonshotAuditRollbackPreview,
    MoonshotCapabilityPreview,
    MoonshotSafetyPolicy,
    PhysicalWorldAutomationPreview,
    RoboticsDroneSafetyReviewPreview,
    SmartGlassesIntegrationPreview,
)
from jarvis.mission_control import MissionControl
from jarvis.marketing_distribution.foundation import (
    AudienceSegmentPreview,
    BudgetSpendGuardPreview,
    CampaignPlanPreview,
    ChannelStrategyPreview,
    ContentDistributionPackPreview,
    DistributionApprovalRequirements,
    LaunchChecklistPreview,
    MarketingDistributionPolicy,
    MarketingDistributionStatus,
    MeasurementPlanPreview,
)
from jarvis.mark_1_e2e_readiness import Mark1E2ERealOpsSmoke
from jarvis.mark_1_operational_runbook import Mark1KnownLimitations, Mark1OperationalRunbook, Mark2NextPlan
from jarvis.mark_1_release_candidate import (
    Mark1ApprovalPathAudit,
    Mark1CapabilityMatrix,
    Mark1DangerousRouteAudit,
    Mark1DocumentationStatus,
    Mark1ReleaseCandidateStatus,
)
from jarvis.mark_2_tool_execution import Mark2ToolExecutionLayer
from jarvis.mark_2_approval_path_audit import Mark2ApprovalPathAudit
from jarvis.mark_2_dangerous_route_audit import Mark2DangerousRouteAudit
from jarvis.mark_2_deploy_adapter import Mark2DeployAdapter
from jarvis.mark_2_domain_publishing_adapter import Mark2DomainPublishingAdapter
from jarvis.mark_2_email_adapter import Mark2EmailAdapter
from jarvis.mark_2_external_operations_policy import ExternalOperationsPolicyEngine
from jarvis.mark_2_stripe_adapter import Mark2StripeAdapter
from jarvis.mark_2_e2e_readiness import Mark2E2EReadinessSmoke
from jarvis.mark_2_operational_runbook import Mark2KnownLimitations, Mark2NextSteps, Mark2OperationalRunbook
from jarvis.mark_2_release_candidate import (
    Mark2CapabilityMatrix,
    Mark2ReadinessMatrix,
    Mark2ReleaseCandidateStatus,
)
from jarvis.mark_3_master_planning import (
    get_mark_3_capability_areas,
    get_mark_3_execution_principles,
    get_mark_3_guardrails,
    get_mark_3_macro_roadmap,
    get_mark_3_pilot_plan,
    get_mark_3_planning_status,
    get_mark_3_readiness,
    get_mark_3_risk_approval_model,
)
from jarvis.mark_3_approval_path_audit import Mark3ApprovalPathAudit
from jarvis.mark_3_dangerous_route_audit import Mark3DangerousRouteAudit
from jarvis.mark_3_e2e_readiness import Mark3E2EReadinessSmoke
from jarvis.mark_3_mission_loop import Mark3MissionLoop
from jarvis.mark_3_outcome_memory import OutcomeMemoryStore
from jarvis.mark_3_learning_proposals import LearningProposalEngine
from jarvis.mark_3_growth_radar import ResearchRadar
from jarvis.mark_3_research_execution import ResearchExecutionControlPlane
from jarvis.mark_3_hermes_runtime_bridge import Mark3HermesRuntimeBridge
from jarvis.mark_3_product_revenue_factory import Mark3ProductRevenueFactory
from jarvis.mark_3_local_routine_scheduler_personal_family_ops import Mark3RoutineOpsControlPlane
from jarvis.mark_3_moonshot_lab_research_experiment_engine import Mark3MoonshotLabResearchExperimentEngine
from jarvis.mark_3_operational_runbook import Mark3KnownLimitations, Mark3NextSteps, Mark3OperationalRunbook
from jarvis.mark_3_pilot_plan import Mark3ControlledPilotPlan
from jarvis.mark_3_release_candidate import (
    Mark3CapabilityMatrix,
    Mark3ReadinessMatrix,
    Mark3ReleaseCandidateStatus,
)
from jarvis.codex_cli_adapter import CodexCliAdapter
from jarvis.claude_code_adapter import ClaudeCodeAdapter
from jarvis.claude_cowork_adapter import ClaudeCoworkAdapter
from jarvis.api_fallback_adapter import ApiFallbackAdapter
from jarvis.routine_execution_bridge import RoutineExecutionBridge
from jarvis.ai_cli_session_audit import build_external_operation_audit_event
from jarvis.local_daemon import LocalDaemonControl
from jarvis.local_runtime_safety import LocalRuntimeSafetyPolicy
from jarvis.monetization_engine import MonetizationEngine
from jarvis.payments_revenue.foundation import (
    CheckoutPlanPreview,
    FinancialRiskGuardPreview,
    InvoicePaymentLinkPreview,
    PaymentApprovalRequirements,
    PaymentProviderPreview,
    PaymentsRevenuePolicy,
    PaymentsRevenueStatus,
    PricingModelPreview,
    RefundChargebackPolicyPreview,
    RevenueExperimentPreview,
    RevenueMetricsPreview,
    SubscriptionPlanPreview,
)
from jarvis.mobile.companion import (
    MobileCommandCenterSnapshot,
    MobileCompanionPermissionPolicy,
    MobileCompanionStatus,
    MobileIntentPreview,
)
from jarvis.multidevice.runtime import (
    DeviceApprovalChannelPreview,
    DeviceCapabilityProfile,
    DevicePairingPreview,
    DeviceRegistrySnapshot,
    DeviceRevokePreview,
    DeviceSyncPreview,
    MultiDeviceRuntimeStatus,
    NotificationRoutingPreview,
)
from jarvis.operator_console import (
    OperatorConsoleCapabilityMatrix,
    OperatorConsolePreview,
    OperatorConsoleStatus,
    build_operational_console_summary,
    build_operator_console_snapshot,
)
from jarvis.personal_memory import PersonalMemoryControlPlane
from jarvis.operational_consolidation import (
    build_capability_registry_view,
    build_operational_system_status,
    build_readiness_matrix_view,
    build_safety_boundary_summary,
)
from jarvis.personal_os.control_plane import PersonalOSControlPlane
from jarvis.personal_os.foundation import (
    AttentionProtectionPreview,
    AwarenessSourcePreview,
    ContextSourceConsentPreview,
    ContextSwitchingPreview,
    DailyStatePreview,
    EnergyFocusSupportPreview,
    GuestModeContextPreview,
    LocalFilesScopePreview,
    PCEnvironmentStatePreview,
    PersonalOSApprovalRequirements,
    PersonalOSEnvironmentStatus,
    PersonalOSPrivacyPolicy,
    PersonalRoutinePreview,
    VisibleReasonAuditPreview,
)
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine
from jarvis.permission_gates import evaluate_permission_gate
from jarvis.real_wake_listener import RealWakeListener
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter
from jarvis.sandbox_execution.foundation import (
    SandboxAuditPreview,
    SandboxCommandPlan,
    SandboxDryRunResult,
    SandboxExecutionPolicy,
    SandboxExecutionStatus,
    SandboxRollbackPreview,
)
from jarvis.sensor_ledger import SensorLedger
from jarvis.tool_adoption.pipeline import (
    ToolAdoptionDecisionPreview,
    ToolAdoptionStatus,
    ToolCandidateProfile,
    ToolDependencyRiskReview,
    ToolLicenseReview,
    ToolRepoHealthReview,
    ToolSandboxInstallProposal,
    ToolSpikePlan,
    ToolValueMeasurementPreview,
)
from jarvis.tool_connectors import preview_connector
from jarvis.tool_invocation_layer import ToolInvocationLayer
from jarvis.tool_registry import preview_tool_registration
from jarvis.scheduler_control import SchedulerControlPlane
from jarvis.voice.base import VoiceAdapter, VoiceSynthesisRequest
from jarvis.voice.companion import (
    VoiceCompanionControlPolicy,
    VoiceCompanionIntentPreview,
    VoiceCompanionStatus,
)
from jarvis.voice.feedback_preview import preview_user_understanding_feedback
from jarvis.voice.factory import create_voice_adapter_from_env
from jarvis.voice.gpt_sovits_adapter import GPTSoVITSAdapter
from jarvis.voice.mock_adapter import MockVoiceAdapter
from jarvis.voice.runtime import VoiceRuntime, VoiceRuntimeState
from jarvis.voice.storage import VoiceAudioStorage
from jarvis.voice.understanding_feedback import UserUnderstandingAppliedFeedbackRule, UserUnderstandingFeedback
from jarvis.voice_session_control import VoiceSessionControl
from jarvis.voice_approval_channel import VoiceApprovalChannel
from jarvis.visual_command_center import VisualCommandCenter
from jarvis.wake_voice_runtime import WakeVoiceRuntime


class CreateTaskRequest(BaseModel):
    prompt: str


class CreateMissionStepRequest(BaseModel):
    prompt: str


class CancelTaskResponse(BaseModel):
    task_id: str
    status: str


class VoiceTTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    language: str = "es"
    output_format: str = "wav"
    metadata: Optional[dict] = None
    save_audio: bool = False


class VoiceTTSResponse(BaseModel):
    provider: str
    content_type: str
    audio_path: Optional[str] = None
    has_audio_bytes: bool
    duration_seconds: Optional[float] = None
    metadata: dict
    status: Optional[str] = None
    approval_request_id: Optional[str] = None


class VoiceRuntimeModeRequest(BaseModel):
    mode: str


class VoiceRuntimeTextRequest(BaseModel):
    text: str


class VoiceCompanionPreviewRequest(BaseModel):
    text: str


class WakeVoicePreviewRequest(BaseModel):
    text: str = ""
    confidence: float = 1.0
    answer_mode: str = "text"


class Mark2VoiceApprovalRequest(BaseModel):
    approval_id: Optional[str] = None
    action: str = "deploy production"
    phrase: str = ""
    phrases: Optional[List[str]] = None
    risk_level: Optional[str] = None
    require_triple_confirmation: bool = False
    cost_summary: str = "unknown; operator review required"
    production_impact_summary: str = "none in preview"
    rollback_or_stop_plan_summary: str = "stop before execution; rollback required when applicable"


class Mark2ToolExecutionPreviewRequest(BaseModel):
    request_id: Optional[str] = None
    actor: str = "David"
    channel: str = "local_api"
    natural_language_command: str = ""
    action_type: str = "preview"
    target_type: str = "filesystem"
    target: str = ""
    environment: str = "preview"
    method: str = "GET"
    content: str = ""
    patch: str = ""
    payload: Optional[Dict[str, Any]] = None
    branch: str = ""
    pr_number: Optional[int] = None
    protected_branch: bool = False
    requires_network: bool = False
    requires_credentials: bool = False
    requires_filesystem_write: bool = False
    requires_external_write: bool = False
    risk_level_declared: str = "medium"
    approval_context: Optional[Dict[str, Any]] = None
    voice_approval_context: Optional[Dict[str, Any]] = None
    rollback_or_stop_plan: str = ""
    kill_switch_active: bool = False
    stop_phrase_detected: bool = False


class Mark2ExternalOperationPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    operation_type: str = "unknown"
    provider: str = "unknown"
    environment: str = "preview"
    operation: str = "unknown"
    task_summary: str = ""
    routine_type: str = "unknown"
    use_case: str = ""
    preferred_mode: str = ""
    repo: str = ""
    worktree: str = ""
    expected_outputs: Optional[List[str]] = None
    allow_real_execution: bool = False
    allow_file_write: bool = False
    allow_network: bool = False
    allow_codex_real: bool = False
    allow_claude_real: bool = False
    allow_deploy: bool = False
    allow_money: bool = False
    project_name: str = ""
    artifact_summary: str = ""
    build_command_preview: str = ""
    deploy_command_preview: str = ""
    rollback_plan: str = ""
    rollback_or_stop_plan: str = ""
    rollback_or_unpublish_plan: str = ""
    stripe_mode: str = "unknown"
    amount: Optional[float] = None
    currency: str = "unknown"
    subject_summary: str = ""
    body_summary: str = ""
    target_summary: str = ""
    contains_sensitive_data: bool = False
    bulk_or_marketing: bool = False
    production_impact: bool = False
    money_movement: bool = False
    valid_approval_present: bool = False
    valid_voice_approval_present: bool = False
    readback_completed: bool = False
    strong_approval_present: bool = False
    strong_approval_satisfied: bool = False
    double_confirmation_present: bool = False
    double_confirmation_satisfied: bool = False
    triple_confirmation_present: bool = False
    triple_confirmation_satisfied: bool = False
    kill_switch_active: bool = False
    stop_phrase_detected: bool = False


class CameraControlPreviewRequest(BaseModel):
    opt_in_present: bool = False
    visible_indicator_ready: bool = False
    recording_requested: bool = False
    analyze_people_requested: bool = False
    screen_capture_requested: bool = False
    external_video_requested: bool = False
    phrase: str = ""


class MobileIntentPreviewRequest(BaseModel):
    text: str


class OperatorConsolePreviewRequest(BaseModel):
    text: str


class ApprovalPreviewRequest(BaseModel):
    action_type: str
    requested_by: str = "jarvis"
    reason: str = ""
    approval_kind: str = "normal"
    expires_in_seconds: int = 900
    context: Optional[Dict[str, Any]] = None


class ApprovalDecisionPreviewRequest(BaseModel):
    approval_id: str
    decision: str
    actor: str = "operator"
    reason: str = ""
    confirmation_phrase: Optional[str] = None


class ApprovalGatePreviewRequest(BaseModel):
    approval_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class Mark3MissionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    objective: str
    allowed_scope: List[str]
    context: str = ""
    desired_outcome: str = "unknown"
    success_criteria: Optional[List[str]] = None
    declared_authorization: str = "unknown"
    allowed_paths_resources: Optional[List[str]] = None
    allowed_tools: Optional[List[str]] = None
    prohibited_tools: Optional[List[str]] = None
    monetary_budget: Optional[float] = None
    time_budget_seconds: Optional[int] = None
    max_steps: int = 10
    allowed_data: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    stop_conditions: Optional[List[str]] = None
    expected_rollback: str = "unknown"
    instruction_origin: str = "api"
    direct_intent_evidence: Optional[str] = None
    requested_risk_level: Optional[int] = None
    proposed_steps: Optional[List[Dict[str, Any]]] = None
    uncertainties: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class Mark3MissionAdvanceRequest(BaseModel):
    approval_id: Optional[str] = None
    step_id: Optional[str] = None


class Mark3MissionOutcomeRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    summary: str
    step_id: Optional[str] = None
    verification_state: str = "reported"
    evidence: Optional[List[Dict[str, Any]]] = None
    costs_known: Any = "unknown"
    revenue_known: Any = "unknown"
    time_known_seconds: Any = "unknown"


class Mark3MissionFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    feedback: str = ""


class Mark3MissionStopRequest(BaseModel):
    reason: str


class Mark3HermesRuntimeExecuteReadRequest(BaseModel):
    mission_id: str
    candidate_id: str
    approval_id: str


class Mark3HermesRuntimeStopRequest(BaseModel):
    reason: str = "operator stop"


class Mark3OutcomeRecordRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    mission_id: str = "unknown"
    step_id: str = "unknown"
    candidate_id: str = "unknown"
    goal: str = "unknown"
    tool_used: str = "unknown"
    capability_used: str = "unknown"
    result_status: str = "unknown"
    evidence_state: str = "unknown"
    errors: Optional[List[str]] = None
    duration_seconds: Any = "unknown"
    cost: Any = "unknown"
    approval_level: str = "unknown"
    what_worked: str = "unknown"
    what_failed: str = "unknown"
    next_recommended_action: str = "unknown"


class Mark3LearningProposalRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    proposal: str = ""
    evidence: str = ""
    confidence: str = "unknown"
    risk: str = "unknown"
    requires_approval: bool = True
    source_outcome_id: Optional[str] = None
    source_outcome_ids: Optional[List[str]] = None
    source_failure_ids: Optional[List[str]] = None


class Mark3LearningProposalDecisionRequest(BaseModel):
    actor: str = "operator"
    approval_level: str = "simple"
    reason: str = ""


class Mark3ResearchRadarPlanRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: str = "local_repo"
    goal: str = "improve_jarvis"
    query: str = ""
    risk: str = "low"
    approval_valid: bool = False
    approval_level: str = "direct"
    capabilities_connected: Optional[Any] = None
    cost_estimate: Any = "unknown"
    stop_conditions: Optional[List[str]] = None
    evidence_required: Optional[List[str]] = None


class Mark3ResearchExecutionPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    research_id: Optional[str] = None
    source_type: Optional[str] = None
    source: Optional[str] = None
    topic: Optional[Any] = None
    goal: str = "improve_jarvis"
    query: Optional[Any] = None
    query_or_scope: Optional[Any] = None
    scope: Optional[Any] = None
    risk_level: Optional[str] = None
    risk: Optional[str] = None
    approval_id: Optional[str] = None
    authorized: bool = True


class Mark3ResearchExecutionCandidateRequest(Mark3ResearchExecutionPreviewRequest):
    pass


class Mark3ProductRevenueFactoryRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    candidate_id: Optional[str] = None
    objective: str = ""
    opportunity: Optional[str] = None
    idea: Optional[str] = None
    product_idea: Optional[str] = None
    product_name: Optional[str] = None
    niche: Optional[str] = None
    market: Optional[str] = None
    audience: Optional[str] = None
    target_customer: Optional[str] = None
    problem: Optional[str] = None
    value_proposition: Optional[str] = None
    differentiation: Optional[str] = None
    expected_value: Optional[str] = None
    confidence: str = "unknown"
    scope: Optional[str] = None
    budget_limit: Optional[Any] = None
    max_budget: Optional[Any] = None
    experiment_budget: Optional[Any] = None
    assumptions: Optional[List[str]] = None
    evidence_required: Optional[List[str]] = None
    stop_conditions: Optional[List[str]] = None
    mvp_scope: Optional[List[str]] = None
    out_of_scope: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    unknowns: Optional[List[str]] = None
    offer_name: Optional[str] = None
    headline: Optional[str] = None
    promise: Optional[str] = None
    call_to_action: Optional[str] = None
    trust_requirements: Optional[List[str]] = None
    pricing_hypothesis: Optional[str] = None
    pricing_tiers: Optional[List[str]] = None
    price_amount: Optional[Any] = None
    monthly_price: Optional[Any] = None
    currency: str = "unknown"
    billing_interval: str = "unknown"
    projected_revenue: Optional[Any] = None
    revenue_projection: Optional[Any] = None
    confirmed_revenue: Optional[Any] = None
    confirmed_revenue_explicitly_provided: bool = False
    gross_revenue: Optional[Any] = None
    gross_revenue_explicitly_provided: bool = False
    expenses: Optional[Any] = None
    expenses_explicitly_provided: bool = False
    net_revenue: Optional[Any] = None
    net_revenue_explicitly_provided: bool = False
    expected_customers: Optional[Any] = None
    projected_customers: Optional[Any] = None
    acquisition_spend: Optional[Any] = None
    acquired_customers: Optional[Any] = None
    monthly_revenue_per_customer: Optional[Any] = None
    gross_margin_rate: Optional[Any] = None
    monthly_churn_rate: Optional[Any] = None
    revenue_model: Optional[str] = None
    business_model: Optional[str] = None
    monetization_path: Optional[str] = None
    pricing_basis: Optional[str] = None
    experiment_name: Optional[str] = None
    hypothesis: Optional[str] = None
    success_metrics: Optional[List[str]] = None
    pricing_variants: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    baseline: Optional[Any] = None
    baseline_explicitly_provided: bool = False
    instrumentation: Optional[List[str]] = None
    attribution_assumptions: Optional[List[str]] = None
    observed_metrics: Optional[Dict[str, Any]] = None
    observed_metrics_explicitly_provided: bool = False
    evidence: Optional[List[str]] = None
    evidence_explicitly_provided: bool = False
    evidence_state: str = "unknown"
    stop_conditions_met: bool = False
    success_metrics_met: bool = False
    opportunity_score: Optional[Any] = None
    opportunity_score_explicitly_provided: bool = False
    willingness_to_pay: Optional[Any] = None
    willingness_to_pay_explicitly_provided: bool = False
    validation_questions: Optional[List[str]] = None
    checkout_requested: bool = False
    stripe_live_requested: bool = False
    payment_requested: bool = False
    money_movement_requested: bool = False
    spend_requested: bool = False
    budget_spend_requested: bool = False
    deploy_requested: bool = False
    production_requested: bool = False
    domain_requested: bool = False
    publish_requested: bool = False
    email_requested: bool = False
    send_requested: bool = False
    identity_requested: bool = False
    web_requested: bool = False
    github_requested: bool = False
    provider_requested: bool = False
    external_email_requested: bool = False
    external_deploy_requested: bool = False
    secrets_requested: bool = False


class Mark3RoutineOpsRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    candidate_id: Optional[str] = None
    routine_type: Optional[str] = None
    ops_type: Optional[str] = None
    plan_type: Optional[str] = None
    title: Optional[str] = None
    objective: Optional[str] = None
    goal: Optional[str] = None
    scope: Optional[str] = None
    budget_limit: Optional[Any] = None
    max_budget: Optional[Any] = None
    cadence: Optional[str] = None
    frequency: Optional[str] = None
    schedule_expression: Optional[str] = None
    schedule: Optional[str] = None
    recurrence_rule: Optional[str] = None
    timezone: Optional[str] = None
    next_run_preview: Optional[str] = None
    due_at: Optional[str] = None
    start_time: Optional[str] = None
    quiet_hours: Optional[str] = None
    tasks: Optional[Any] = None
    task_candidates: Optional[Any] = None
    routine_steps: Optional[Any] = None
    daily_plan: Optional[Any] = None
    weekly_plan: Optional[Any] = None
    health_checks: Optional[Any] = None
    checks: Optional[Any] = None
    checklist: Optional[Any] = None
    evidence_required: Optional[Any] = None
    stop_conditions: Optional[Any] = None
    family_member: Optional[str] = None
    consent_recorded: Optional[Any] = None
    consent_valid: Optional[Any] = None
    family_consent: Optional[Any] = None
    authorized: Optional[Any] = None
    authorization_valid: Optional[Any] = None
    account_provider: Optional[str] = None
    provider: Optional[str] = None
    service: Optional[str] = None
    account_owner: Optional[str] = None
    account_identifier: Optional[str] = None
    username_hint: Optional[str] = None
    email_hint: Optional[str] = None
    schedule_real_requested: Optional[Any] = None
    create_cron: Optional[Any] = None
    background_worker_requested: Optional[Any] = None
    watcher_requested: Optional[Any] = None
    email_requested: Optional[Any] = None
    send_email: Optional[Any] = None
    calendar_requested: Optional[Any] = None
    calendar_access_requested: Optional[Any] = None
    gmail_requested: Optional[Any] = None
    gmail_access_requested: Optional[Any] = None
    contacts_requested: Optional[Any] = None
    contacts_access_requested: Optional[Any] = None
    account_access_requested: Optional[Any] = None
    login_requested: Optional[Any] = None
    perform_recovery_requested: Optional[Any] = None
    reset_password_now: Optional[Any] = None
    store_password: Optional[Any] = None
    password_storage_requested: Optional[Any] = None
    repo_health_requested: Optional[Any] = None
    local_file_health_requested: Optional[Any] = None
    money_requested: Optional[Any] = None
    production_requested: Optional[Any] = None
    completed: Optional[Any] = None
    execution_completed: Optional[Any] = None
    mark_complete: Optional[Any] = None


class Mark3MoonshotLabRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    candidate_id: Optional[str] = None
    moonshot_type: Optional[str] = None
    moonshot: Optional[str] = None
    research_area: Optional[str] = None
    experiment_type: Optional[str] = None
    experiment_name: Optional[str] = None
    title: Optional[str] = None
    objective: Optional[str] = None
    goal: Optional[str] = None
    problem: Optional[str] = None
    why_it_matters: Optional[str] = None
    expected_value: Optional[str] = None
    hypothesis: Optional[str] = None
    research_hypothesis: Optional[str] = None
    claim_to_test: Optional[str] = None
    null_hypothesis: Optional[str] = None
    assumptions: Optional[Any] = None
    constraints: Optional[Any] = None
    known_constraints: Optional[Any] = None
    unknowns: Optional[Any] = None
    scope: Optional[str] = None
    budget_limit: Optional[Any] = None
    max_budget: Optional[Any] = None
    experiment_budget: Optional[Any] = None
    currency: Optional[str] = None
    cost_estimate: Optional[Any] = None
    cost_estimate_explicitly_provided: bool = False
    method: Optional[str] = None
    protocol: Optional[str] = None
    metrics: Optional[Any] = None
    success_metrics: Optional[Any] = None
    failure_criteria: Optional[Any] = None
    falsification_criteria: Optional[Any] = None
    evidence: Optional[Any] = None
    evidence_required: Optional[Any] = None
    evidence_state: str = "unknown"
    evidence_score: Optional[Any] = None
    evidence_score_explicitly_provided: bool = False
    observed_metrics: Optional[Dict[str, Any]] = None
    observed_metrics_explicitly_provided: bool = False
    uncertainty_level: Optional[str] = None
    reproducibility_checklist: Optional[Any] = None
    stop_conditions: Optional[Any] = None
    stop_conditions_met: Optional[Any] = None
    prototype_name: Optional[str] = None
    prototype_goal: Optional[str] = None
    build_steps: Optional[Any] = None
    steps: Optional[Any] = None
    source_type: Optional[str] = None
    source: Optional[str] = None
    local_repo_requested: Optional[Any] = None
    docs_requested: Optional[Any] = None
    network_requested: Optional[Any] = None
    web_requested: Optional[Any] = None
    github_requested: Optional[Any] = None
    provider_requested: Optional[Any] = None
    ai_cli_requested: Optional[Any] = None
    install_requested: Optional[Any] = None
    install_dependencies: Optional[Any] = None
    execute_experiment_requested: Optional[Any] = None
    run_experiment_requested: Optional[Any] = None
    private_metrics_requested: Optional[Any] = None
    sensitive_data_requested: Optional[Any] = None
    publish_requested: Optional[Any] = None
    production_requested: Optional[Any] = None
    deploy_requested: Optional[Any] = None
    money_movement_requested: Optional[Any] = None
    payment_requested: Optional[Any] = None
    spend_requested: Optional[Any] = None
    identity_requested: Optional[Any] = None
    credentials_requested: Optional[Any] = None


class ApprovalExecutionDecisionPreviewRequest(BaseModel):
    action_name: str = ""
    action_category: str = "normal"
    risk_level: str = "medium"
    valid_approval_present: bool = False
    strong_approval_present: bool = False
    double_confirmation_present: bool = False
    context_fingerprint_matches: bool = False
    permission_gates_passed: bool = False
    audit_present: bool = False
    rollback_or_stop_plan_required: bool = False
    rollback_or_stop_plan_present: bool = False
    execution_capable_when_approved: bool = False
    illegal: bool = False
    unsafe: bool = False
    unauthorized: bool = False
    impossible: bool = False
    unsupported: bool = False


class CriticalActionWarningPreviewRequest(BaseModel):
    action_name: str = ""
    affected_system: str = "unspecified system"
    possible_consequences: Optional[List[str]] = None
    estimated_cost: Optional[str] = None
    irreversible_or_hard_to_reverse: bool = True
    rollback_available: bool = False


class RuntimePreviewRequest(BaseModel):
    request_id: Optional[str] = None
    action_type: str = ""
    target: str = ""
    scope: Optional[List[str]] = None
    command: Optional[str] = None
    tool_name: Optional[str] = None
    payload_summary: Optional[Dict[str, Any]] = None
    environment: str = "preview"
    production: bool = False
    external_call: bool = False
    secrets: bool = False
    filesystem_write: bool = False
    network_access: bool = False
    side_effects: bool = False
    persistent_changes: bool = False
    requested_by: str = "jarvis"
    reason: str = ""
    approval_id: Optional[str] = None
    policy_allowed: bool = False
    sandbox_available: bool = False
    filesystem_scope_present: bool = False
    network_allowed: bool = False
    secrets_authorized: bool = False
    timeout_present: bool = False
    rollback_available: bool = False
    rollback_steps: Optional[List[str]] = None
    rollback_notes: str = ""


class ToolRegistrationPreviewRequest(BaseModel):
    tool_id: str = ""
    name: str = ""
    connector_type: str = "mock_safe"
    description: str = ""
    capabilities: Optional[List[str]] = None
    required_permissions: Optional[List[str]] = None
    risk_level: str = "medium"
    requires_approval: bool = True
    requires_strong_approval: bool = False
    external_call_required: bool = False
    filesystem_access_required: bool = False
    network_access_required: bool = False
    secrets_required: bool = False
    production_capable: bool = False
    write_capable: bool = False
    side_effect_capable: bool = False
    enabled: bool = False


class ConnectorPreviewRequest(BaseModel):
    connector_id: str = ""
    connector_type: str = "mock_safe"
    allowed_scopes: Optional[List[str]] = None
    denied_scopes: Optional[List[str]] = None
    requires_credentials: bool = False
    network_required: bool = False
    external_call_required: bool = False
    filesystem_scope_required: bool = False
    approval_required: bool = True
    strong_approval_required: bool = False
    enabled: bool = False
    status: str = "preview_only"
    blocked_reasons: Optional[List[str]] = None


class ToolInvocationPreviewRequest(BaseModel):
    invocation_id: Optional[str] = None
    tool_id: str = ""
    connector_id: str = ""
    action_type: str = ""
    target: str = ""
    scope: Optional[List[str]] = None
    payload_summary: Optional[Dict[str, Any]] = None
    requested_by: str = "jarvis"
    reason: str = ""
    environment: str = "preview"
    external_call: bool = False
    filesystem_write: bool = False
    credentials: bool = False
    production: bool = False
    side_effects: bool = False
    persistent_changes: bool = False
    network_access: bool = False
    approval_id: Optional[str] = None
    granted_permissions: Optional[List[str]] = None
    policy_allowed: bool = False
    sandbox_available: bool = False
    filesystem_scope_present: bool = False
    network_allowed: bool = False
    secrets_authorized: bool = False
    timeout_present: bool = False
    rollback_available: bool = False
    rollback_steps: Optional[List[str]] = None


class MemoryRecordPreviewRequest(BaseModel):
    memory_id: Optional[str] = None
    memory_type: str = "unknown"
    content_summary: str = ""
    source: str = "operator_provided"
    created_by: str = "jarvis"
    reason: str = ""
    sensitivity_level: str = "normal"
    approved: bool = False
    approval_id: Optional[str] = None
    active: bool = False
    reversible: bool = True
    created_at: str = ""
    approved_at: Optional[str] = None
    activated_at: Optional[str] = None
    expires_at: Optional[str] = None
    tags: Optional[List[str]] = None
    blocked_reasons: Optional[List[str]] = None
    persistent: bool = False
    private_data: bool = False
    external_source: bool = False
    stop_controls_blocked: bool = False


class PersonalOSStatePreviewRequest(BaseModel):
    active_mode: str = "manual"
    focus_mode: str = "off"
    daily_priorities: Optional[List[str]] = None
    weekly_priorities: Optional[List[str]] = None
    routines: Optional[List[Dict[str, Any]]] = None
    reminders: Optional[List[Dict[str, Any]]] = None
    review_queue: Optional[List[Dict[str, Any]]] = None
    authorized_sources: Optional[List[str]] = None
    blocked_sources: Optional[List[str]] = None
    blocked_reasons: Optional[List[str]] = None


class SchedulerControlPreviewRequest(BaseModel):
    item_id: Optional[str] = None
    title: str = "untitled scheduler preview"
    item_type: str = "reminder"
    schedule_expression: Optional[str] = None
    due_at: Optional[str] = None
    timezone: str = "UTC"
    payload_summary: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    requires_strong_approval: bool = False
    side_effects: bool = False
    tool_invocation_required: bool = False
    controlled_runtime_required: bool = False
    external_call_required: bool = False
    private_source_required: bool = False
    status: str = "draft"
    created_at: str = ""
    last_previewed_at: Optional[str] = None
    blocked_reasons: Optional[List[str]] = None
    items: Optional[List[Dict[str, Any]]] = None
    now: Optional[str] = None
    review_id: Optional[str] = None
    date: Optional[str] = None
    week: Optional[str] = None
    priorities: Optional[List[str]] = None
    pending_approvals: Optional[List[str]] = None
    pending_memory_reviews: Optional[List[str]] = None
    due_scheduler_items: Optional[List[str]] = None
    money_or_roi_items: Optional[List[str]] = None
    completed_items: Optional[List[str]] = None
    pending_items: Optional[List[str]] = None
    postponed_items: Optional[List[str]] = None
    memory_changes: Optional[List[str]] = None
    scheduler_changes: Optional[List[str]] = None
    roi_or_monetization_signals: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    recommended_next_actions: Optional[List[str]] = None
    global_pause: bool = False
    memory_activation_paused: bool = False
    scheduler_paused: bool = False
    routines_paused: bool = False
    personal_os_paused: bool = False
    external_sources_paused: bool = True
    tool_invocations_paused: bool = True
    reason: str = ""


class PersonalizationPreviewRequest(BaseModel):
    preference_name: Optional[str] = None
    preference_type: str = "unknown"
    evidence_preview: Optional[List[str]] = None
    confidence: str = "unknown"
    uncertainty_notes: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    pattern_name: Optional[str] = None
    observed_style_preview: Optional[str] = None
    preferred_response_style: Optional[str] = None
    examples_preview: Optional[List[str]] = None
    decision_axis: Optional[str] = None
    observed_preference: Optional[str] = None
    tradeoffs: Optional[List[str]] = None
    risk_tolerance: Optional[str] = None
    monetization_bias: Optional[str] = None
    contrarian_needed: bool = False
    goal_name: Optional[str] = None
    goal_type: str = "unknown"
    expected_value: Optional[str] = None
    constraints: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    priority_reason: Optional[str] = None
    contrarian_mode_requested: bool = False
    critique_style: Optional[str] = None
    challenge_threshold: Optional[str] = None
    allowed_pushback: Optional[List[str]] = None
    blocked_pushback: Optional[List[str]] = None
    proposal_id_preview: Optional[str] = None
    proposed_memory: Optional[str] = None
    memory_category: str = "unknown"
    evidence: Optional[List[str]] = None
    usefulness: Optional[str] = None
    sensitivity_level: str = "unknown"
    review_status: str = "unknown"
    acceptance_reasons: Optional[List[str]] = None
    rejection_reasons: Optional[List[str]] = None
    sensitivity_warnings: Optional[List[str]] = None
    suggested_revision: Optional[str] = None
    requested_action: str = "unknown"
    memory_id_preview: Optional[str] = None
    audit_reason: Optional[str] = None
    current_state_preview: Optional[str] = None
    claim_or_preference: Optional[str] = None
    unknowns: Optional[List[str]] = None
    assumptions: Optional[List[str]] = None
    evidence_needed: Optional[List[str]] = None
    recommendation_name: Optional[str] = None
    basis: Optional[List[str]] = None
    expected_benefit: Optional[str] = None
    recommendation_type: str = "unknown"
    input_category: Optional[str] = None
    sensitive_attribute_risk: str = "unknown"
    blocked_inferences: Optional[List[str]] = None
    allowed_non_sensitive_summary: Optional[str] = None
    sensitive_memory_requested: bool = False
    sensitive_source_requested: bool = False
    private_source_requested: bool = False
    cross_context_requested: bool = False
    action_based_on_personalization_requested: bool = False
    private_data_requested: bool = False
    sensitive_attribute_requested: bool = False


class AmbientVisionSessionPreviewRequest(BaseModel):
    session_requested: bool = False
    camera_requested: bool = False
    recording_requested: bool = False
    streaming_requested: bool = False
    continuous_watch_requested: bool = False
    face_analysis_requested: bool = False
    person_analysis_requested: bool = False
    external_vision_requested: bool = False
    image_storage_requested: bool = False
    sensitive_capture_requested: bool = False


class DevicePairingPreviewRequest(BaseModel):
    device_id: str = "device-placeholder"
    device_type: str = "unknown"
    pairing_requested: bool = False


class DeviceRevokePreviewRequest(BaseModel):
    device_id: str = "device-placeholder"
    revoke_requested: bool = False


class DeviceApprovalChannelPreviewRequest(BaseModel):
    device_id: str = "device-placeholder"
    approval_channel_requested: bool = False


class DeviceSyncPreviewRequest(BaseModel):
    device_id: str = "device-placeholder"
    sync_requested: bool = False


class NotificationRoutingPreviewRequest(BaseModel):
    device_id: str = "device-placeholder"
    notification_requested: bool = False


class SandboxCommandRequest(BaseModel):
    command: str = ""
    working_directory: str = ""


class ToolCandidateProfileRequest(BaseModel):
    tool_name: str = "unknown"
    source_url: str = ""
    declared_use_case: str = "unknown"
    license: str = "unknown"
    repo_health: str = "unknown"
    dependency_risk: str = "unknown"
    security_risk: str = "unknown"
    expected_value: str = "unknown"


class ToolLicenseReviewRequest(BaseModel):
    license: str = "unknown"


class ToolRepoHealthReviewRequest(BaseModel):
    metadata: Optional[dict] = None


class ToolDependencyRiskReviewRequest(BaseModel):
    dependencies: Optional[List[str]] = None


class ToolSandboxInstallProposalRequest(BaseModel):
    tool_name: str = "unknown"


class ToolSpikePlanRequest(BaseModel):
    hypothesis: str = "unknown"
    scope: str = "unknown"
    success_metric: str = "unknown"
    max_time: str = "unknown"
    max_cost: str = "unknown"
    rollback: str = "required before any real spike"


class ToolValueMeasurementPreviewRequest(BaseModel):
    time_saved: Optional[str] = None
    token_saved: Optional[str] = None
    error_reduction: Optional[str] = None
    asset_quality_improvement: Optional[str] = None
    revenue_enablement: Optional[str] = None
    confirmed_revenue: bool = False


class ToolAdoptionDecisionPreviewRequest(BaseModel):
    license: str = "unknown"
    repo_health: str = "unknown"
    dependency_risk: str = "unknown"
    expected_value: str = "unknown"
    blocked: bool = False
    install_requested: bool = False
    execution_requested: bool = False
    network_requested: bool = False
    secrets_requested: bool = False
    core_dependency_requested: bool = False


class AssetFactoryPreviewRequest(BaseModel):
    project_name: Optional[str] = None
    audience: Optional[str] = None
    problem: Optional[str] = None
    promise_or_value_proposition: Optional[str] = None
    offer_type: Optional[str] = None
    monetization_hypothesis: Optional[str] = None
    tone: Optional[str] = None
    constraints: Optional[List[str]] = None
    confirmed_roi: Optional[str] = None
    confirmed_roi_explicitly_provided: bool = False
    hero: Optional[str] = None
    sections: Optional[List[str]] = None
    cta: Optional[str] = None
    trust_elements: Optional[List[str]] = None
    faq: Optional[List[str]] = None
    risk_disclaimers: Optional[List[str]] = None
    conversion_goal: Optional[str] = None
    pages: Optional[List[str]] = None
    navigation: Optional[List[str]] = None
    components: Optional[List[str]] = None
    data_requirements: Optional[List[str]] = None
    static_dynamic_classification: Optional[str] = None
    headlines: Optional[List[str]] = None
    subheadlines: Optional[List[str]] = None
    cta_copy: Optional[List[str]] = None
    offer_copy: Optional[List[str]] = None
    faq_copy: Optional[List[str]] = None
    disclaimer_copy: Optional[List[str]] = None
    files_to_create: Optional[List[str]] = None
    directories: Optional[List[str]] = None
    framework: Optional[str] = None
    package_type: Optional[str] = None
    dependencies_preview: Optional[List[str]] = None
    build_steps_preview: Optional[List[str]] = None
    required_checks: Optional[List[str]] = None
    missing_items: Optional[List[str]] = None
    offer_name: Optional[str] = None
    pricing_hypothesis: Optional[str] = None
    revenue_hypothesis: Optional[str] = None
    confirmed_revenue_explicitly_provided: bool = False


class DeployPublishingPreviewRequest(BaseModel):
    target_name: Optional[str] = None
    target_type: str = "unknown"
    environment: str = "unknown"
    production_target: bool = False
    asset_reference: Optional[str] = None
    publish_destination: Optional[str] = None
    domain_requested: bool = False
    domain_name: Optional[str] = None
    account_type: Optional[str] = None
    production_requested: bool = False
    paid_resource_requested: bool = False
    identity_requested: bool = False
    secrets_requested: bool = False
    publish_requested: bool = False
    required_checks: Optional[List[str]] = None
    missing_items: Optional[List[str]] = None
    rollback_steps_preview: Optional[List[str]] = None
    irreversible_risks: Optional[List[str]] = None
    warnings: Optional[List[str]] = None


class MarketingDistributionPreviewRequest(BaseModel):
    audience_name: Optional[str] = None
    problem: Optional[str] = None
    pains: Optional[List[str]] = None
    desired_outcomes: Optional[List[str]] = None
    objections: Optional[List[str]] = None
    data_source: str = "unknown"
    confidence: str = "unknown"
    channels: Optional[List[str]] = None
    rationale: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    expected_effort: Optional[str] = None
    expected_cost: str = "unknown"
    campaign_name: Optional[str] = None
    objective: Optional[str] = None
    audience: Optional[str] = None
    offer: Optional[str] = None
    assets_needed: Optional[List[str]] = None
    schedule_preview: Optional[List[str]] = None
    success_metrics: Optional[List[str]] = None
    posts: Optional[List[str]] = None
    email_drafts: Optional[List[str]] = None
    community_posts: Optional[List[str]] = None
    outreach_messages: Optional[List[str]] = None
    seo_snippets: Optional[List[str]] = None
    cta_variants: Optional[List[str]] = None
    utm_plan: Optional[List[str]] = None
    metrics: Optional[List[str]] = None
    attribution_assumptions: Optional[List[str]] = None
    dashboard_fields_preview: Optional[List[str]] = None
    budget_requested: Optional[str] = None
    required_assets: Optional[List[str]] = None
    missing_items: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    publish_requested: bool = False
    send_requested: bool = False
    paid_requested: bool = False
    external_account_requested: bool = False
    identity_requested: bool = False
    secrets_requested: bool = False
    budget_spend_requested: bool = False


class PaymentsRevenuePreviewRequest(BaseModel):
    product_name: Optional[str] = None
    audience: Optional[str] = None
    offer_type: Optional[str] = None
    pricing_hypothesis: Optional[str] = None
    pricing_tiers: Optional[List[str]] = None
    currency: str = "unknown"
    assumptions: Optional[List[str]] = None
    confirmed_revenue: Optional[str] = None
    confirmed_revenue_explicitly_provided: bool = False
    checkout_requested: bool = False
    provider: str = "unknown"
    provider_name: Optional[str] = None
    product_reference: Optional[str] = None
    price_reference: Optional[str] = None
    metrics: Optional[Dict[str, str]] = None
    metrics_explicitly_provided: bool = False
    dashboard_fields_preview: Optional[List[str]] = None
    plan_name: Optional[str] = None
    billing_interval: Optional[str] = None
    trial_policy: Optional[str] = None
    cancellation_policy: Optional[str] = None
    invoice_requested: bool = False
    payment_link_requested: bool = False
    refund_policy: Optional[str] = None
    chargeback_risk: Optional[str] = None
    risk_level: str = "unknown"
    experiment_name: Optional[str] = None
    hypothesis: Optional[str] = None
    pricing_variants: Optional[List[str]] = None
    success_metrics: Optional[List[str]] = None
    max_budget: Optional[str] = None
    warnings: Optional[List[str]] = None
    provider_requested: bool = False
    provider_connection_requested: bool = False
    bank_requested: bool = False
    card_requested: bool = False
    bank_or_card_data_requested: bool = False
    money_movement_requested: bool = False
    payment_requested: bool = False
    refund_requested: bool = False
    subscription_requested: bool = False
    identity_requested: bool = False
    secrets_requested: bool = False
    payout_requested: bool = False
    tax_requested: bool = False
    legal_requested: bool = False
    income_claim_requested: bool = False
    income_guarantee_requested: bool = False


class MonetizationPreviewRequest(BaseModel):
    plan_id: Optional[str] = None
    name: Optional[str] = None
    price_amount: Optional[float] = None
    currency: str = "EUR"
    billing_interval: str = "monthly"
    included_usage: Optional[str] = None
    overage_price: Optional[float] = None
    target_customer: Optional[str] = None
    value_proposition: Optional[str] = None
    margin_notes: Optional[List[str]] = None
    risk_notes: Optional[List[str]] = None
    expected_customers: Optional[float] = None
    conversion_rate: Optional[float] = None
    churn_rate: Optional[float] = None
    monthly_price: Optional[float] = None
    confidence_level: Optional[str] = None
    assumptions: Optional[List[str]] = None
    unknowns: Optional[List[str]] = None
    monthly_budget_limit: Optional[float] = None
    per_action_spend_limit: Optional[float] = None
    current_spend_estimate: Optional[float] = None
    proposed_spend: Optional[float] = None
    action_name: Optional[str] = None
    action_type: Optional[str] = None
    amount: Optional[float] = None
    provider: str = "unknown"
    mode: str = "preview"
    valid_approval_present: bool = False
    strong_approval_present: bool = False
    double_confirmation_present: bool = False
    context_fingerprint_matches: bool = False
    permission_gates_passed: bool = False
    audit_present: bool = False
    rollback_or_stop_plan_present: bool = False
    real_money_requested: bool = False
    illegal: bool = False
    fraudulent: bool = False
    unsafe: bool = False
    unauthorized: bool = False
    impossible: bool = False
    unsupported: bool = False
    product_catalog_preview: Optional[List[Dict[str, Any]]] = None
    checkout_preview: Optional[Dict[str, Any]] = None
    acquisition_spend: Optional[float] = None
    acquired_customers: Optional[float] = None
    monthly_revenue_per_customer: Optional[float] = None
    gross_margin_rate: Optional[float] = None
    monthly_churn_rate: Optional[float] = None
    investment: Optional[float] = None
    return_amount: Optional[float] = None
    confidence: Optional[str] = None


class ProductBuilderPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    action_type: str = ""
    environment: str = "preview"


class DailyOperatorPreviewRequest(BaseModel):
    date: Optional[str] = None
    timezone: str = "unknown"
    priorities: Optional[List[str]] = None
    open_loops: Optional[List[str]] = None
    blocked_items: Optional[List[str]] = None
    scheduled_items_preview: Optional[List[str]] = None
    risk_warnings: Optional[List[str]] = None
    source_data: str = "unknown"
    plan_date: Optional[str] = None
    focus_blocks: Optional[List[str]] = None
    task_candidates: Optional[List[str]] = None
    priority_order: Optional[List[str]] = None
    estimated_effort: Optional[str] = None
    dependency_notes: Optional[List[str]] = None
    blocked_by_approval: Optional[List[str]] = None
    rule_name: Optional[str] = None
    cadence: str = "unknown"
    start_time: Optional[str] = None
    allowed_window: Optional[str] = None
    quiet_hours: Optional[str] = None
    recurrence_requested: bool = False
    recurrence_rule: Optional[str] = None
    next_run_preview: Optional[str] = None
    max_runs: Optional[int] = None
    stop_condition: Optional[str] = None
    queued_items_preview: Optional[List[str]] = None
    execution_order: Optional[List[str]] = None
    reminder_requested: bool = False
    channel: str = "none"
    message_preview: Optional[str] = None
    recipient_preview: Optional[str] = None
    window_name: Optional[str] = None
    allowed_start: Optional[str] = None
    allowed_end: Optional[str] = None
    max_runtime: Optional[str] = None
    max_retries: int = 0
    backoff_preview: Optional[str] = None
    side_effect_task: bool = False
    summary_date: Optional[str] = None
    completed_preview: Optional[List[str]] = None
    pending_preview: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    approvals_needed: Optional[List[str]] = None
    next_actions_preview: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    background_requested: bool = False
    background_execution_requested: bool = False
    recurring_requested: bool = False
    notification_requested: bool = False
    external_notification_requested: bool = False
    external_calendar_requested: bool = False
    calendar_requested: bool = False
    money_requested: bool = False
    money_movement_requested: bool = False
    payment_requested: bool = False
    spend_requested: bool = False
    publish_requested: bool = False
    deploy_requested: bool = False
    external_side_effect_requested: bool = False


class ContinuousLearningPreviewRequest(BaseModel):
    candidate_name: Optional[str] = None
    category: Optional[str] = None
    source_reference: Optional[str] = None
    claimed_benefit: Optional[str] = None
    use_case: Optional[str] = None
    maturity: str = "unknown"
    license: str = "unknown"
    dependency_risk: str = "unknown"
    security_risk: str = "unknown"
    maintenance_signal: str = "unknown"
    revenue_or_efficiency_hypothesis: Optional[str] = None
    warnings: Optional[List[str]] = None
    relevance_score: str = "unknown"
    fit_reasons: Optional[List[str]] = None
    rejection_reasons: Optional[List[str]] = None
    monetization_relevance: str = "unknown"
    time_saving_relevance: str = "unknown"
    error_reduction_relevance: str = "unknown"
    revenue_enablement_relevance: str = "unknown"
    unknowns: Optional[List[str]] = None
    skeptical_questions: Optional[List[str]] = None
    failure_modes: Optional[List[str]] = None
    hidden_costs: Optional[List[str]] = None
    security_concerns: Optional[List[str]] = None
    maintenance_concerns: Optional[List[str]] = None
    vendor_lock_in_risk: str = "unknown"
    overengineering_risk: str = "unknown"
    recommendation_pressure_check: str = "unknown"
    proposal_title: Optional[str] = None
    summary: Optional[str] = None
    expected_impact: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    tests_required: Optional[List[str]] = None
    rollback_plan: Optional[List[str]] = None
    decision_recommendation: str = "unknown"
    confidence: str = "unknown"
    impact_categories: Optional[Dict[str, str]] = None
    confirmed_roi: Optional[str] = None
    confirmed_roi_explicitly_provided: bool = False
    maintenance_risk: str = "unknown"
    product_risk: str = "unknown"
    cost_risk: str = "unknown"
    privacy_risk: str = "unknown"
    production_risk: str = "unknown"
    secret_risk: str = "unknown"
    runtime_risk: str = "unknown"
    branch_name_preview: Optional[str] = None
    files_likely_to_change: Optional[List[str]] = None
    test_plan: Optional[List[str]] = None
    review_plan: Optional[List[str]] = None
    migration_notes: Optional[List[str]] = None
    next_manual_review_steps: Optional[List[str]] = None
    backlog_items: Optional[List[str]] = None
    priority_order: Optional[List[str]] = None
    reasons: Optional[List[str]] = None
    blocked_items: Optional[List[str]] = None
    review_cadence: Optional[str] = None
    decision: str = "unknown"
    rationale: Optional[List[str]] = None
    required_evidence: Optional[List[str]] = None
    required_approvals: Optional[List[str]] = None
    install_requested: bool = False
    runtime_requested: bool = False
    prompt_requested: bool = False
    production_requested: bool = False
    credentials_requested: bool = False
    secrets_requested: bool = False
    deploy_requested: bool = False
    dependency_modification_requested: bool = False


class PersonalOSPreviewRequest(BaseModel):
    source_name: Optional[str] = None
    source_type: str = "unknown"
    access_requested: bool = False
    consent_status: str = "missing"
    scope_preview: Optional[List[str]] = None
    visible_reason: Optional[str] = None
    warnings: Optional[List[str]] = None
    date: Optional[str] = None
    timezone: Optional[str] = None
    mode: Optional[str] = None
    priorities: Optional[List[str]] = None
    focus_state: Optional[str] = None
    open_loops: Optional[List[str]] = None
    blocked_items: Optional[List[str]] = None
    energy_hint: Optional[str] = None
    source_data: str = "unknown"
    device_state_summary: Optional[str] = None
    active_context: Optional[str] = None
    environment_signals: Optional[List[str]] = None
    interruption_risk: Optional[str] = None
    focus_mode_suggestion: Optional[str] = None
    calendar_awareness_requested: bool = False
    email_awareness_requested: bool = False
    document_awareness_requested: bool = False
    local_file_awareness_requested: bool = False
    scope_name: Optional[str] = None
    allowed_paths_preview: Optional[List[str]] = None
    denied_paths_preview: Optional[List[str]] = None
    current_context: Optional[str] = None
    target_context: Optional[str] = None
    switch_reason: Optional[str] = None
    context_boundary_risk: Optional[str] = None
    cross_context_requested: bool = False
    private_professional_boundary: bool = False
    focus_window: Optional[str] = None
    interruption_policy: Optional[str] = None
    allowed_interruptions: Optional[List[str]] = None
    blocked_interruptions: Optional[List[str]] = None
    routine_name: Optional[str] = None
    routine_type: str = "unknown"
    steps_preview: Optional[List[str]] = None
    triggers_preview: Optional[List[str]] = None
    energy_state: str = "unknown"
    focus_recommendation: Optional[str] = None
    workload_risk: Optional[str] = None
    break_suggestion: Optional[str] = None
    action_or_preview_name: Optional[str] = None
    data_sources_used: Optional[List[str]] = None
    data_sources_blocked: Optional[List[str]] = None
    approvals_needed: Optional[List[str]] = None
    uncertainty_notes: Optional[List[str]] = None
    sensitive_source_requested: bool = False
    private_source_requested: bool = False
    sending_requested: bool = False
    acting_requested: bool = False
    camera_requested: bool = False
    microphone_requested: bool = False
    screen_requested: bool = False
    external_account_requested: bool = False
    private_files_requested: bool = False
    broad_scope_requested: bool = False
    private_scope_requested: bool = False
    notification_requested: bool = False
    system_change_requested: bool = False
    contact_people_requested: bool = False
    secrets_requested: bool = False


class FutureMoonshotPreviewRequest(BaseModel):
    capability_name: Optional[str] = None
    capability_type: str = "unknown"
    concept_summary: Optional[str] = None
    intended_value: Optional[str] = None
    monetization_or_efficiency_hypothesis: Optional[str] = None
    device_name: Optional[str] = None
    integration_goal: Optional[str] = None
    data_inputs_preview: Optional[List[str]] = None
    output_modes_preview: Optional[List[str]] = None
    overlay_name: Optional[str] = None
    overlay_goal: Optional[str] = None
    display_context: Optional[str] = None
    data_sources_preview: Optional[List[str]] = None
    system_name: Optional[str] = None
    system_type: str = "unknown"
    intended_use: Optional[str] = None
    simulation_name: Optional[str] = None
    simulation_goal: Optional[str] = None
    simulated_domain: Optional[str] = None
    assumptions: Optional[List[str]] = None
    limits: Optional[List[str]] = None
    failure_modes: Optional[List[str]] = None
    automation_name: Optional[str] = None
    target_environment: Optional[str] = None
    intended_action: Optional[str] = None
    safety_controls: Optional[List[str]] = None
    stop_plan: Optional[str] = None
    rollback_plan: Optional[Any] = None
    review_subject: Optional[str] = None
    legal_questions: Optional[List[str]] = None
    safety_questions: Optional[List[str]] = None
    required_evidence: Optional[List[str]] = None
    jurisdiction: Optional[str] = None
    environment_name: Optional[str] = None
    isolation_level: Optional[str] = None
    allowed_capabilities: Optional[List[str]] = None
    blocked_capabilities: Optional[List[str]] = None
    stop_name: Optional[str] = None
    stop_scope: Optional[List[str]] = None
    stop_triggers: Optional[List[str]] = None
    automatic_stop_preview: Optional[List[str]] = None
    subject: Optional[str] = None
    audit_events_preview: Optional[List[str]] = None
    evidence_required: Optional[List[str]] = None
    idea_name: Optional[str] = None
    claimed_advantage: Optional[str] = None
    practical_value: Optional[str] = None
    revenue_or_efficiency_path: Optional[str] = None
    evidence_needed: Optional[List[str]] = None
    scenario_name: Optional[str] = None
    prohibited_impersonation_actions: Optional[List[str]] = None
    allowed_safe_summary: Optional[str] = None
    spectacle_risk: str = "unknown"
    safety_risk: str = "unknown"
    legal_risk: str = "unknown"
    identity_risk: str = "unknown"
    privacy_risk: str = "unknown"
    always_on_risk: str = "unknown"
    bystander_privacy_risk: str = "unknown"
    distraction_risk: str = "unknown"
    physical_world_dependency: Optional[str] = None
    bystander_safety_risk: str = "unknown"
    property_damage_risk: str = "unknown"
    physical_risk: str = "unknown"
    impersonation_risk: str = "unknown"
    warnings: Optional[List[str]] = None
    physical_requested: bool = False
    legal_requested: bool = False
    identity_requested: bool = False
    money_requested: bool = False
    safety_requested: bool = False
    camera_requested: bool = False
    microphone_requested: bool = False
    screen_requested: bool = False
    surveillance_requested: bool = False
    external_device_requested: bool = False
    robotics_requested: bool = False
    drones_requested: bool = False
    ar_overlay_requested: bool = False


class VoiceRuntimeFeedbackRequest(BaseModel):
    original_text: str
    interpreted_intent: Optional[str] = None
    corrected_intent: str
    correction_note: Optional[str] = None
    preferred_next_step: Optional[str] = None
    confidence_before: Optional[str] = None


class VoiceRuntimeFeedbackPreviewRequest(BaseModel):
    original_text: Optional[str] = None
    interpreted_intent: Optional[str] = None
    corrected_intent: Optional[str] = None
    correction_note: Optional[str] = None
    preferred_next_step: Optional[str] = None
    confidence_before: Optional[str] = None


class VoiceRuntimeMemoryProposalFromAppliedFeedbackRequest(BaseModel):
    original_text: str
    corrected_intent: str
    suggested_alias: Optional[str] = None
    reason: Optional[str] = None
    source: str = "user_reviewed_feedback"
    applied_persistently: bool = False


class VoiceRuntimeMemoryProposalApproveRequest(BaseModel):
    approved_by: Optional[str] = "David"


class VoiceRuntimeMemoryProposalDisableRequest(BaseModel):
    reason: Optional[str] = None


class VoiceRuntimeMemoryProposalActivateRequest(BaseModel):
    activated_by: Optional[str] = "David"


class VoiceRuntimeMemoryRuleDeactivateRequest(BaseModel):
    reason: Optional[str] = None


class VoiceRuntimeMemorySnapshotImportRequest(BaseModel):
    snapshot: Optional[Any] = None
    replace: bool = False
    path: Optional[Any] = None
    file: Optional[Any] = None


class VoiceRuntimeMemoryLocalSaveRequest(BaseModel):
    base_dir: Optional[str] = None
    create_backup: bool = True


class VoiceRuntimeMemoryLocalLoadRequest(BaseModel):
    base_dir: Optional[str] = None
    replace: Optional[Any] = None
    path: Optional[Any] = None
    file: Optional[Any] = None


class VoiceRuntimeMemoryLocalBackupRequest(BaseModel):
    base_dir: Optional[str] = None
    path: Optional[Any] = None
    file: Optional[Any] = None


class VoiceRuntimeMemoryLocalDeleteRequest(BaseModel):
    base_dir: Optional[str] = None
    include_backups: Optional[Any] = True
    path: Optional[Any] = None
    file: Optional[Any] = None


@dataclass
class TaskRecord:
    task_id: str
    prompt: str
    status: str
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approval_request_id: Optional[str] = None


class InMemoryTaskStore:
    def __init__(self):
        self._items: Dict[str, TaskRecord] = {}
        self._lock = Lock()

    def create(self, prompt: str) -> TaskRecord:
        now = _now_iso()
        task = TaskRecord(task_id=str(uuid4()), prompt=prompt, status="pending", created_at=now, updated_at=now)
        with self._lock:
            self._items[task.task_id] = task
        return task

    def get(self, task_id: str) -> TaskRecord:
        with self._lock:
            item = self._items.get(task_id)
        if not item:
            raise KeyError(task_id)
        return item

    def list(self) -> List[TaskRecord]:
        with self._lock:
            return list(self._items.values())

    def update(self, task: TaskRecord) -> TaskRecord:
        task.updated_at = _now_iso()
        with self._lock:
            self._items[task.task_id] = task
        return task


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_voice_metadata(metadata: dict) -> dict:
    blocked_exact = {"base_url", "prompt_text"}
    blocked_substrings = ("secret", "token", "key", "password")
    sanitized = {}

    for key, value in metadata.items():
        key_text = str(key)
        key_lower = key_text.lower()
        if key_lower in blocked_exact:
            continue
        if key_lower.endswith("_path"):
            continue
        if any(blocked in key_lower for blocked in blocked_substrings):
            continue
        sanitized[key] = value

    return sanitized


def _voice_runtime_state_payload(state: VoiceRuntimeState) -> dict:
    return {
        "mode": state.mode.value,
        "enabled": state.enabled,
        "frontend_required": state.frontend_required,
        "input_language": state.input_language,
        "output_language": state.output_language,
        "last_error": state.last_error,
        "last_transcript": state.last_transcript,
        "last_intent": state.last_intent,
        "wake_words": list(state.wake_words),
        "feedback_count": state.feedback_count,
        "applied_feedback_count": state.applied_feedback_count,
        "memory_proposal_count": state.memory_proposal_count,
        "active_memory_rule_count": state.active_memory_rule_count,
    }


def create_app(
    *,
    policy_engine: Optional[PolicyEngine] = None,
    approval_gateway: Optional[ApprovalGateway] = None,
    adapter_factory: Optional[Callable[[], HermesRuntimeAdapter]] = None,
    hermes_runtime_adapter_factory: Optional[Callable[[Callable[[str, Dict[str, Any]], Any]], Any]] = None,
    hermes_runtime_authorize: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    task_store: Optional[InMemoryTaskStore] = None,
    voice_adapter: Optional[VoiceAdapter] = None,
    voice_audio_storage: Optional[VoiceAudioStorage] = None,
    voice_runtime: Optional[VoiceRuntime] = None,
) -> FastAPI:
    app = FastAPI(title="JARVIS Gateway API", version="0.1.0")

    app.state.policy_engine = policy_engine or PolicyEngine()
    app.state.approval_gateway = approval_gateway or ApprovalGateway()
    app.state.approval_hardening = ApprovalHardeningService()
    app.state.mark_3_mission_loop = Mark3MissionLoop(approval_service=app.state.approval_hardening)
    app.state.mark_3_outcome_memory = OutcomeMemoryStore()
    app.state.mark_3_learning_proposals = LearningProposalEngine()
    app.state.mark_3_research_radar = ResearchRadar()
    app.state.mark_3_research_execution_bridge = ResearchExecutionControlPlane(
        approval_service=app.state.approval_hardening,
        outcome_memory=app.state.mark_3_outcome_memory,
        learning_proposals=app.state.mark_3_learning_proposals,
        research_radar=app.state.mark_3_research_radar,
    )
    app.state.mark_3_product_revenue_factory = Mark3ProductRevenueFactory()
    app.state.mark_3_routine_ops = Mark3RoutineOpsControlPlane()
    app.state.mark_3_moonshot_lab = Mark3MoonshotLabResearchExperimentEngine()
    app.state.approval_execution_semantics = GlobalApprovalExecutionSemantics()
    app.state.monetization_engine = MonetizationEngine(app.state.approval_execution_semantics)
    app.state.adaptive_saas_builder = AdaptiveSaaSBuilder(app.state.approval_execution_semantics)
    app.state.controlled_runtime_bridge = ControlledRuntimeBridge(
        audit_trail=app.state.approval_hardening.audit_trail,
    )
    app.state.tool_invocation_layer = ToolInvocationLayer(
        runtime_bridge=app.state.controlled_runtime_bridge,
        audit_trail=app.state.approval_hardening.audit_trail,
    )
    app.state.personal_memory_control = PersonalMemoryControlPlane(
        audit_trail=app.state.approval_hardening.audit_trail,
    )
    app.state.personal_os_control = PersonalOSControlPlane()
    app.state.scheduler_control = SchedulerControlPlane()
    app.state.wake_voice_runtime = WakeVoiceRuntime()
    app.state.voice_session_control = VoiceSessionControl(
        wake_runtime=app.state.wake_voice_runtime,
        policy_engine=app.state.policy_engine,
    )
    app.state.sensor_ledger = SensorLedger()
    app.state.camera_control_runtime = CameraControlRuntime()
    app.state.local_daemon_control = LocalDaemonControl()
    app.state.desktop_runtime = DesktopRuntime()
    app.state.local_runtime_safety_policy = LocalRuntimeSafetyPolicy()
    app.state.real_wake_listener = RealWakeListener(session_control=app.state.voice_session_control)
    app.state.voice_approval_channel = VoiceApprovalChannel()
    app.state.mark_2_tool_execution = Mark2ToolExecutionLayer()
    app.state.mark_2_external_operations_policy = ExternalOperationsPolicyEngine()
    app.state.mark_2_deploy_adapter = Mark2DeployAdapter()
    app.state.mark_2_stripe_adapter = Mark2StripeAdapter()
    app.state.mark_2_email_adapter = Mark2EmailAdapter()
    app.state.mark_2_domain_adapter = Mark2DomainPublishingAdapter()
    app.state.visual_command_center = VisualCommandCenter()
    app.state.adapter_factory = adapter_factory or (lambda: HermesRuntimeAdapter())
    app.state.hermes_runtime_authorize = hermes_runtime_authorize
    app.state.voice_adapter = voice_adapter or create_voice_adapter_from_env()
    app.state.voice_runtime = voice_runtime or VoiceRuntime()
    app.state.task_store = task_store or InMemoryTaskStore()
    app.state.voice_audio_storage = voice_audio_storage or VoiceAudioStorage()
    app.state.mission_control = MissionControl(
        mission_store=None,
        policy_engine=app.state.policy_engine,
        approval_gateway=app.state.approval_gateway,
        adapter_factory=app.state.adapter_factory,
    )
    app.state.mark_3_hermes_runtime_bridge = Mark3HermesRuntimeBridge(
        app.state.mark_3_mission_loop,
        adapter_factory=hermes_runtime_adapter_factory,
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/mark-1/status")
    def mark_1_status() -> dict:
        return Mark1ReleaseCandidateStatus().to_dict()

    @app.get("/mark-2/local-daemon/status")
    def mark_2_local_daemon_status() -> dict:
        return app.state.local_daemon_control.status()

    @app.get("/mark-2/desktop-runtime/status")
    def mark_2_desktop_runtime_status() -> dict:
        return app.state.desktop_runtime.status().to_dict()

    @app.get("/mark-2/local-runtime/safety-policy")
    def mark_2_local_runtime_safety_policy() -> dict:
        return app.state.local_runtime_safety_policy.to_dict()

    @app.get("/mark-2/wake-listener/status")
    def mark_2_wake_listener_status() -> dict:
        return app.state.real_wake_listener.status()

    @app.post("/mark-2/wake-listener/preview-transcript")
    def mark_2_wake_listener_preview_transcript(payload: WakeVoicePreviewRequest) -> dict:
        return app.state.real_wake_listener.preview_transcript(payload.text, confidence=payload.confidence)

    @app.get("/mark-2/voice-approval/status")
    def mark_2_voice_approval_status() -> dict:
        return app.state.voice_approval_channel.status()

    @app.post("/mark-2/voice-approval/preview-start")
    def mark_2_voice_approval_preview_start(payload: Mark2VoiceApprovalRequest) -> dict:
        try:
            return app.state.voice_approval_channel.start(
                action=payload.action,
                risk_level=payload.risk_level,
                require_triple_confirmation=payload.require_triple_confirmation,
                cost_summary=payload.cost_summary,
                production_impact_summary=payload.production_impact_summary,
                rollback_or_stop_plan_summary=payload.rollback_or_stop_plan_summary,
            ).to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/mark-2/voice-approval/preview-confirm")
    def mark_2_voice_approval_preview_confirm(payload: Mark2VoiceApprovalRequest) -> dict:
        if not payload.approval_id:
            raise HTTPException(status_code=400, detail="approval_id is required")
        try:
            return app.state.voice_approval_channel.confirm(payload.approval_id, payload.phrase).to_dict()
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="voice approval preview not found") from exc

    @app.post("/mark-2/voice-approval/preview-flow")
    def mark_2_voice_approval_preview_flow(payload: Mark2VoiceApprovalRequest) -> dict:
        return app.state.voice_approval_channel.preview_flow(
            payload.action,
            payload.phrases or [],
            require_triple_confirmation=payload.require_triple_confirmation,
        )

    @app.get("/mark-2/local-daemon/command-preview")
    def mark_2_local_daemon_command_preview(command: str = "daemon_status") -> dict:
        return app.state.local_daemon_control.preview_command(command).to_dict()

    @app.get("/mark-2/local-audit/preview")
    def mark_2_local_audit_preview() -> dict:
        return app.state.voice_approval_channel.audit_preview()

    @app.get("/mark-2/tools/status")
    def mark_2_tools_status() -> dict:
        return app.state.mark_2_tool_execution.status()

    @app.get("/mark-2/tools/policy")
    def mark_2_tools_policy() -> dict:
        return app.state.mark_2_tool_execution.policy()

    def _mark_2_tool_request(payload: Mark2ToolExecutionPreviewRequest):
        return app.state.mark_2_tool_execution.prepare_request(**payload.model_dump())

    def _mark_2_adapter_preview(payload: Mark2ToolExecutionPreviewRequest):
        request = _mark_2_tool_request(payload)
        return request, app.state.mark_2_tool_execution.preview_adapter(request, **payload.model_dump())

    @app.post("/mark-2/tools/preview-request")
    def mark_2_tools_preview_request(payload: Mark2ToolExecutionPreviewRequest) -> dict:
        return _mark_2_tool_request(payload).to_dict()

    @app.post("/mark-2/tools/preview-candidate")
    def mark_2_tools_preview_candidate(payload: Mark2ToolExecutionPreviewRequest) -> dict:
        request, preview = _mark_2_adapter_preview(payload)
        return app.state.mark_2_tool_execution.prepare_candidate(
            request,
            adapter_preview=preview,
            kill_switch_active=payload.kill_switch_active,
            stop_phrase_detected=payload.stop_phrase_detected,
        ).to_dict()

    @app.post("/mark-2/tools/preview-filesystem")
    def mark_2_tools_preview_filesystem(payload: Mark2ToolExecutionPreviewRequest) -> dict:
        request = app.state.mark_2_tool_execution.prepare_request(
            **{**payload.model_dump(), "target_type": "filesystem"}
        )
        return app.state.mark_2_tool_execution.preview_adapter(request, **payload.model_dump())

    @app.post("/mark-2/tools/preview-github")
    def mark_2_tools_preview_github(payload: Mark2ToolExecutionPreviewRequest) -> dict:
        request = app.state.mark_2_tool_execution.prepare_request(**{**payload.model_dump(), "target_type": "github"})
        return app.state.mark_2_tool_execution.preview_adapter(request, **payload.model_dump())

    @app.post("/mark-2/tools/preview-browser")
    def mark_2_tools_preview_browser(payload: Mark2ToolExecutionPreviewRequest) -> dict:
        request = app.state.mark_2_tool_execution.prepare_request(**{**payload.model_dump(), "target_type": "browser"})
        return app.state.mark_2_tool_execution.preview_adapter(request, **payload.model_dump())

    @app.post("/mark-2/tools/preview-api")
    def mark_2_tools_preview_api(payload: Mark2ToolExecutionPreviewRequest) -> dict:
        request = app.state.mark_2_tool_execution.prepare_request(**{**payload.model_dump(), "target_type": "external_api"})
        return app.state.mark_2_tool_execution.preview_adapter(request, **payload.model_dump())

    @app.post("/mark-2/tools/preview-execution")
    def mark_2_tools_preview_execution(payload: Mark2ToolExecutionPreviewRequest) -> dict:
        request, preview = _mark_2_adapter_preview(payload)
        candidate = app.state.mark_2_tool_execution.prepare_candidate(
            request,
            adapter_preview=preview,
            kill_switch_active=payload.kill_switch_active,
            stop_phrase_detected=payload.stop_phrase_detected,
        )
        return app.state.mark_2_tool_execution.preview_result(request, candidate).to_dict()

    @app.get("/mark-2/tools/audit-preview")
    def mark_2_tools_audit_preview() -> dict:
        return app.state.mark_2_tool_execution.audit_preview()

    @app.get("/mark-2/dashboard/status")
    def mark_2_dashboard_status() -> dict:
        return app.state.visual_command_center.status()

    @app.get("/mark-2/dashboard/overview")
    def mark_2_dashboard_overview() -> dict:
        return app.state.visual_command_center.overview()

    @app.get("/mark-2/dashboard/panels")
    def mark_2_dashboard_panels() -> dict:
        return {"panels": app.state.visual_command_center.panels(), "safe_to_render": True}

    @app.get("/mark-2/dashboard/agents")
    def mark_2_dashboard_agents() -> dict:
        return {"agents": app.state.visual_command_center.agents(), "real_agent_execution_enabled": False}

    @app.get("/mark-2/dashboard/sessions")
    def mark_2_dashboard_sessions() -> dict:
        return {"sessions": app.state.visual_command_center.sessions(), "real_ai_cli_invocation_enabled": False}

    @app.get("/mark-2/dashboard/costs")
    def mark_2_dashboard_costs() -> dict:
        return {"cost_usage": app.state.visual_command_center.costs(), "no_fake_costs": True}

    @app.get("/mark-2/dashboard/approvals")
    def mark_2_dashboard_approvals() -> dict:
        return {"approvals": app.state.visual_command_center.approvals(), "preview_only": True}

    @app.get("/mark-2/dashboard/risks")
    def mark_2_dashboard_risks() -> dict:
        return {"risks": app.state.visual_command_center.risks(), "safe_to_render": True}

    @app.get("/mark-2/dashboard/worktree-guard")
    def mark_2_dashboard_worktree_guard() -> dict:
        return app.state.visual_command_center.worktree_guard()

    @app.get("/mark-2/dashboard/diffs-tests-reviews")
    def mark_2_dashboard_diffs_tests_reviews() -> dict:
        return app.state.visual_command_center.diff_test_review()

    @app.get("/mark-2/dashboard/audit")
    def mark_2_dashboard_audit() -> dict:
        return {"audit_timeline": app.state.visual_command_center.audit(), "safe_to_render": True}

    @app.get("/mark-2/dashboard/next-actions")
    def mark_2_dashboard_next_actions() -> dict:
        return {"next_actions": app.state.visual_command_center.next_actions(), "would_execute": False}

    @app.get("/mark-2/external-ops/status")
    def mark_2_external_ops_status() -> dict:
        return app.state.mark_2_external_operations_policy.status()

    @app.get("/mark-2/external-ops/policy")
    def mark_2_external_ops_policy() -> dict:
        return app.state.mark_2_external_operations_policy.policy()

    @app.post("/mark-2/external-ops/preview-deploy")
    def mark_2_external_ops_preview_deploy(payload: Mark2ExternalOperationPreviewRequest) -> dict:
        return app.state.mark_2_deploy_adapter.preview(**payload.model_dump()).to_dict()

    @app.post("/mark-2/external-ops/preview-stripe")
    def mark_2_external_ops_preview_stripe(payload: Mark2ExternalOperationPreviewRequest) -> dict:
        return app.state.mark_2_stripe_adapter.preview(**payload.model_dump()).to_dict()

    @app.post("/mark-2/external-ops/preview-email")
    def mark_2_external_ops_preview_email(payload: Mark2ExternalOperationPreviewRequest) -> dict:
        return app.state.mark_2_email_adapter.preview(**payload.model_dump()).to_dict()

    @app.post("/mark-2/external-ops/preview-domain")
    def mark_2_external_ops_preview_domain(payload: Mark2ExternalOperationPreviewRequest) -> dict:
        return app.state.mark_2_domain_adapter.preview(**payload.model_dump()).to_dict()

    @app.get("/mark-2/ai-cli/status")
    def mark_2_ai_cli_status() -> dict:
        status = app.state.mark_2_external_operations_policy.status()
        return {key: value for key, value in status.items() if "adapter" in key or "invocation" in key or key in {"current_mark", "mark_2_macro"}}

    @app.post("/mark-2/ai-cli/preview-codex")
    def mark_2_ai_cli_preview_codex(payload: Mark2ExternalOperationPreviewRequest) -> dict:
        return CodexCliAdapter.preview(**payload.model_dump()).to_dict()

    @app.post("/mark-2/ai-cli/preview-claude-code")
    def mark_2_ai_cli_preview_claude_code(payload: Mark2ExternalOperationPreviewRequest) -> dict:
        return ClaudeCodeAdapter.preview(**payload.model_dump()).to_dict()

    @app.post("/mark-2/ai-cli/preview-claude-cowork")
    def mark_2_ai_cli_preview_claude_cowork(payload: Mark2ExternalOperationPreviewRequest) -> dict:
        return ClaudeCoworkAdapter.preview(**payload.model_dump()).to_dict()

    @app.post("/mark-2/ai-cli/preview-api-fallback")
    def mark_2_ai_cli_preview_api_fallback(payload: Mark2ExternalOperationPreviewRequest) -> dict:
        return ApiFallbackAdapter.preview(**payload.model_dump()).to_dict()

    @app.post("/mark-2/routine-execution/preview")
    def mark_2_routine_execution_preview(payload: Mark2ExternalOperationPreviewRequest) -> dict:
        return RoutineExecutionBridge.preview(**payload.model_dump()).to_dict()

    @app.get("/mark-2/external-ops/audit-preview")
    def mark_2_external_ops_audit_preview() -> dict:
        return build_external_operation_audit_event().to_dict()

    @app.get("/mark-2/release-candidate/status")
    def mark_2_release_candidate_status() -> dict:
        return Mark2ReleaseCandidateStatus().to_dict()

    @app.get("/mark-2/release-candidate/capabilities")
    def mark_2_release_candidate_capabilities() -> dict:
        return Mark2CapabilityMatrix().to_dict()

    @app.get("/mark-2/release-candidate/readiness")
    def mark_2_release_candidate_readiness() -> dict:
        return Mark2ReadinessMatrix().to_dict()

    @app.get("/mark-2/release-candidate/dangerous-route-audit")
    def mark_2_release_candidate_dangerous_route_audit() -> dict:
        return Mark2DangerousRouteAudit().audit(route.path for route in app.routes)

    @app.get("/mark-2/release-candidate/approval-path-audit")
    def mark_2_release_candidate_approval_path_audit() -> dict:
        return Mark2ApprovalPathAudit().audit()

    @app.get("/mark-2/release-candidate/e2e-smoke")
    def mark_2_release_candidate_e2e_smoke() -> dict:
        return Mark2E2EReadinessSmoke().run()

    @app.get("/mark-2/release-candidate/runbook")
    def mark_2_release_candidate_runbook() -> dict:
        return Mark2OperationalRunbook().to_dict()

    @app.get("/mark-2/release-candidate/known-limitations")
    def mark_2_release_candidate_known_limitations() -> dict:
        return Mark2KnownLimitations().to_dict()

    @app.get("/mark-2/release-candidate/next-steps")
    def mark_2_release_candidate_next_steps() -> dict:
        return Mark2NextSteps().to_dict()

    @app.get("/mark-3/release-candidate/status")
    def mark_3_release_candidate_status() -> dict:
        return Mark3ReleaseCandidateStatus().to_dict()

    @app.get("/mark-3/release-candidate/capabilities")
    def mark_3_release_candidate_capabilities() -> dict:
        return Mark3CapabilityMatrix().to_dict()

    @app.get("/mark-3/release-candidate/readiness")
    def mark_3_release_candidate_readiness() -> dict:
        return Mark3ReadinessMatrix().to_dict()

    @app.get("/mark-3/release-candidate/dangerous-route-audit")
    def mark_3_release_candidate_dangerous_route_audit() -> dict:
        return Mark3DangerousRouteAudit().audit(route.path for route in app.routes)

    @app.get("/mark-3/release-candidate/approval-path-audit")
    def mark_3_release_candidate_approval_path_audit() -> dict:
        return Mark3ApprovalPathAudit().audit()

    @app.get("/mark-3/release-candidate/e2e-smoke")
    def mark_3_release_candidate_e2e_smoke() -> dict:
        return Mark3E2EReadinessSmoke().run()

    @app.get("/mark-3/release-candidate/pilot-plan")
    def mark_3_release_candidate_pilot_plan() -> dict:
        return Mark3ControlledPilotPlan().to_dict()

    @app.get("/mark-3/release-candidate/runbook")
    def mark_3_release_candidate_runbook() -> dict:
        return Mark3OperationalRunbook().to_dict()

    @app.get("/mark-3/release-candidate/known-limitations")
    def mark_3_release_candidate_known_limitations() -> dict:
        return Mark3KnownLimitations().to_dict()

    @app.get("/mark-3/release-candidate/next-steps")
    def mark_3_release_candidate_next_steps() -> dict:
        return Mark3NextSteps().to_dict()

    @app.get("/mark-3/dashboard/status")
    def mark_3_dashboard_status() -> dict:
        return build_mark_3_dashboard_status(
            app_state=app.state,
            route_paths=(route.path for route in app.routes),
            generated_at=_now_iso(),
        )

    @app.get("/mark-3/dashboard/events")
    def mark_3_dashboard_events() -> dict:
        generated_at = _now_iso()
        dashboard_status = build_mark_3_dashboard_status(
            app_state=app.state,
            route_paths=(route.path for route in app.routes),
            generated_at=generated_at,
        )
        return build_jarvis_event_snapshot(
            dashboard_status=dashboard_status,
            generated_at=generated_at,
        )

    @app.get("/mark-3/dashboard/events/stream")
    def mark_3_dashboard_events_stream() -> StreamingResponse:
        generated_at = _now_iso()
        dashboard_status = build_mark_3_dashboard_status(
            app_state=app.state,
            route_paths=(route.path for route in app.routes),
            generated_at=generated_at,
        )
        snapshot = build_jarvis_event_snapshot(
            dashboard_status=dashboard_status,
            generated_at=generated_at,
        )

        def _stream():
            yield encode_sse_event("jarvis_event_snapshot", snapshot)
            yield encode_sse_event("heartbeat", snapshot["heartbeat"])
            yield ": JARVIS read-only event stream heartbeat; no secrets, no raw audio, no camera frames\n\n"

        return StreamingResponse(
            _stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-store",
                "X-Jarvis-Read-Only": "true",
            },
        )

    @app.get("/mark-3/local-doctor/status")
    def mark_3_local_doctor_status() -> dict:
        return build_local_doctor_status(
            app_state=app.state,
            route_paths=(route.path for route in app.routes),
            generated_at=_now_iso(),
            health={"status": "ok"},
            hermes_runtime=app.state.mark_3_hermes_runtime_bridge.status(),
        )

    @app.get("/mark-3/planning/status")
    def mark_3_planning_status() -> dict:
        return get_mark_3_planning_status()

    @app.get("/mark-3/planning/principles")
    def mark_3_planning_principles() -> dict:
        return get_mark_3_execution_principles()

    @app.get("/mark-3/planning/risk-approval-model")
    def mark_3_planning_risk_approval_model() -> dict:
        return get_mark_3_risk_approval_model()

    @app.get("/mark-3/planning/capabilities")
    def mark_3_planning_capabilities() -> dict:
        return get_mark_3_capability_areas()

    @app.get("/mark-3/planning/roadmap")
    def mark_3_planning_roadmap() -> dict:
        return get_mark_3_macro_roadmap()

    @app.get("/mark-3/planning/guardrails")
    def mark_3_planning_guardrails() -> dict:
        return get_mark_3_guardrails()

    @app.get("/mark-3/planning/pilot-plan")
    def mark_3_planning_pilot_plan() -> dict:
        return get_mark_3_pilot_plan()

    @app.get("/mark-3/planning/readiness")
    def mark_3_planning_readiness() -> dict:
        return get_mark_3_readiness()

    @app.get("/mark-3/mission-loop/status")
    def mark_3_mission_loop_status() -> dict:
        return app.state.mark_3_mission_loop.status()

    @app.get("/mark-3/mission-loop/policy")
    def mark_3_mission_loop_policy() -> dict:
        return app.state.mark_3_mission_loop.policy()

    @app.post("/mark-3/mission-loop/missions")
    def mark_3_mission_loop_create(payload: Mark3MissionCreateRequest) -> dict:
        try:
            return app.state.mark_3_mission_loop.create_mission(payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/mark-3/mission-loop/missions/{mission_id}")
    def mark_3_mission_loop_get(mission_id: str) -> dict:
        try:
            return app.state.mark_3_mission_loop.get_mission(mission_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/mark-3/mission-loop/missions/{mission_id}/advance")
    def mark_3_mission_loop_advance(mission_id: str, payload: Mark3MissionAdvanceRequest) -> dict:
        try:
            return app.state.mark_3_mission_loop.advance(
                mission_id,
                approval_id=payload.approval_id,
                step_id=payload.step_id,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/mark-3/mission-loop/missions/{mission_id}/record-outcome")
    def mark_3_mission_loop_record_outcome(mission_id: str, payload: Mark3MissionOutcomeRequest) -> dict:
        try:
            return app.state.mark_3_mission_loop.record_outcome(mission_id, payload.model_dump())
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/mark-3/mission-loop/missions/{mission_id}/feedback")
    def mark_3_mission_loop_feedback(mission_id: str, payload: Mark3MissionFeedbackRequest) -> dict:
        try:
            return app.state.mark_3_mission_loop.add_feedback(mission_id, payload.model_dump())
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/mark-3/mission-loop/missions/{mission_id}/stop")
    def mark_3_mission_loop_stop(mission_id: str, payload: Mark3MissionStopRequest) -> dict:
        try:
            return app.state.mark_3_mission_loop.stop(mission_id, reason=payload.reason)
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/mark-3/mission-loop/missions/{mission_id}/audit")
    def mark_3_mission_loop_audit(mission_id: str) -> dict:
        try:
            return app.state.mark_3_mission_loop.audit(mission_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.get("/mark-3/hermes-runtime/status")
    def mark_3_hermes_runtime_status() -> dict:
        return app.state.mark_3_hermes_runtime_bridge.status()

    def _require_hermes_runtime_authorized(operation: str, payload: Dict[str, Any]) -> None:
        callback = app.state.hermes_runtime_authorize
        if callback is None:
            raise HTTPException(status_code=503, detail="operator authorization channel not configured")
        if callback(operation, payload) is not True:
            raise HTTPException(status_code=403, detail="operator authorization denied")

    @app.post("/mark-3/hermes-runtime/execute-read")
    def mark_3_hermes_runtime_execute_read(payload: Mark3HermesRuntimeExecuteReadRequest) -> dict:
        data = payload.model_dump()
        _require_hermes_runtime_authorized("execute_read", data)
        try:
            approval = app.state.approval_hardening.get(payload.approval_id)
            return app.state.mark_3_hermes_runtime_bridge.execute_read(
                mission_id=payload.mission_id,
                candidate_id=payload.candidate_id,
                approval=approval,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @app.get("/mark-3/hermes-runtime/sessions/{session_id}")
    def mark_3_hermes_runtime_session(session_id: str) -> dict:
        try:
            return app.state.mark_3_hermes_runtime_bridge.get_session(session_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="session not found")

    @app.post("/mark-3/hermes-runtime/sessions/{session_id}/stop")
    def mark_3_hermes_runtime_stop(session_id: str, payload: Mark3HermesRuntimeStopRequest) -> dict:
        _require_hermes_runtime_authorized("stop", {"session_id": session_id, "reason": payload.reason})
        try:
            return app.state.mark_3_hermes_runtime_bridge.stop(session_id, reason=payload.reason)
        except KeyError:
            raise HTTPException(status_code=404, detail="session not found")

    @app.get("/mark-3/growth/status")
    def mark_3_growth_status() -> dict:
        return {
            "mark": "Mark 3",
            "autonomous_growth_learning_radar_available": True,
            "jarvis_not_caged": True,
            "approval_gates_are_not_permanent_bans": True,
            "legal_safe_authorized_supported_actions_can_advance_with_approval": True,
            "hermes_remains_execution_engine": True,
            "jarvis_governs_decides_classifies_approves_audits": True,
            "no_duplicate_hermes_runtime": True,
            "outcome_memory": app.state.mark_3_outcome_memory.status(),
            "learning_proposals": app.state.mark_3_learning_proposals.status(),
            "research_radar": app.state.mark_3_research_radar.status(),
            "research_execution": app.state.mark_3_research_execution_bridge.status(),
            "product_revenue_factory": app.state.mark_3_product_revenue_factory.status(),
            "routine_ops": app.state.mark_3_routine_ops.status(),
            "moonshot_lab": app.state.mark_3_moonshot_lab.status(),
            "hermes_runtime": app.state.mark_3_hermes_runtime_bridge.status(),
            "delicate_actions_require_approval": {
                "install": "strong_or_higher",
                "commit": "double_or_higher",
                "deploy": "triple",
                "production": "triple",
                "money": "triple",
                "secrets": "blocked",
            },
        }

    @app.get("/mark-3/product-revenue/status")
    def mark_3_product_revenue_status() -> dict:
        return {
            **app.state.mark_3_product_revenue_factory.status(),
            "audit": app.state.mark_3_product_revenue_factory.audit(),
        }

    def _product_revenue_values(payload: Mark3ProductRevenueFactoryRequest) -> Dict[str, Any]:
        return payload.model_dump(exclude_none=True, exclude_defaults=True)

    @app.post("/mark-3/product-revenue/opportunity")
    def mark_3_product_revenue_opportunity(payload: Mark3ProductRevenueFactoryRequest) -> dict:
        return app.state.mark_3_product_revenue_factory.opportunity(_product_revenue_values(payload))

    @app.post("/mark-3/product-revenue/blueprint")
    def mark_3_product_revenue_blueprint(payload: Mark3ProductRevenueFactoryRequest) -> dict:
        return app.state.mark_3_product_revenue_factory.blueprint(_product_revenue_values(payload))

    @app.post("/mark-3/product-revenue/experiment")
    def mark_3_product_revenue_experiment(payload: Mark3ProductRevenueFactoryRequest) -> dict:
        return app.state.mark_3_product_revenue_factory.experiment(_product_revenue_values(payload))

    @app.post("/mark-3/product-revenue/decision")
    def mark_3_product_revenue_decision(payload: Mark3ProductRevenueFactoryRequest) -> dict:
        return app.state.mark_3_product_revenue_factory.decision(_product_revenue_values(payload))

    @app.get("/mark-3/routine-ops/status")
    def mark_3_routine_ops_status() -> dict:
        return {
            **app.state.mark_3_routine_ops.status(),
            "audit": app.state.mark_3_routine_ops.audit(),
        }

    def _routine_ops_values(payload: Mark3RoutineOpsRequest) -> Dict[str, Any]:
        return payload.model_dump(exclude_none=True, exclude_defaults=True)

    @app.post("/mark-3/routine-ops/plan")
    def mark_3_routine_ops_plan(payload: Mark3RoutineOpsRequest) -> dict:
        return app.state.mark_3_routine_ops.plan(_routine_ops_values(payload))

    @app.post("/mark-3/routine-ops/personal")
    def mark_3_routine_ops_personal(payload: Mark3RoutineOpsRequest) -> dict:
        return app.state.mark_3_routine_ops.personal(_routine_ops_values(payload))

    @app.post("/mark-3/routine-ops/family")
    def mark_3_routine_ops_family(payload: Mark3RoutineOpsRequest) -> dict:
        return app.state.mark_3_routine_ops.family(_routine_ops_values(payload))

    @app.post("/mark-3/routine-ops/account-assistance")
    def mark_3_routine_ops_account_assistance(payload: Mark3RoutineOpsRequest) -> dict:
        return app.state.mark_3_routine_ops.account_assistance(_routine_ops_values(payload))

    @app.post("/mark-3/routine-ops/decision")
    def mark_3_routine_ops_decision(payload: Mark3RoutineOpsRequest) -> dict:
        return app.state.mark_3_routine_ops.decision(_routine_ops_values(payload))

    @app.get("/mark-3/moonshot-lab/status")
    def mark_3_moonshot_lab_status() -> dict:
        return {
            **app.state.mark_3_moonshot_lab.status(),
            "audit": app.state.mark_3_moonshot_lab.audit(),
        }

    def _moonshot_lab_values(payload: Mark3MoonshotLabRequest) -> Dict[str, Any]:
        return payload.model_dump(exclude_none=True, exclude_defaults=True)

    @app.post("/mark-3/moonshot-lab/intake")
    def mark_3_moonshot_lab_intake(payload: Mark3MoonshotLabRequest) -> dict:
        return app.state.mark_3_moonshot_lab.intake(_moonshot_lab_values(payload))

    @app.post("/mark-3/moonshot-lab/hypothesis")
    def mark_3_moonshot_lab_hypothesis(payload: Mark3MoonshotLabRequest) -> dict:
        return app.state.mark_3_moonshot_lab.hypothesis(_moonshot_lab_values(payload))

    @app.post("/mark-3/moonshot-lab/experiment")
    def mark_3_moonshot_lab_experiment(payload: Mark3MoonshotLabRequest) -> dict:
        return app.state.mark_3_moonshot_lab.experiment(_moonshot_lab_values(payload))

    @app.post("/mark-3/moonshot-lab/prototype")
    def mark_3_moonshot_lab_prototype(payload: Mark3MoonshotLabRequest) -> dict:
        return app.state.mark_3_moonshot_lab.prototype(_moonshot_lab_values(payload))

    @app.post("/mark-3/moonshot-lab/decision")
    def mark_3_moonshot_lab_decision(payload: Mark3MoonshotLabRequest) -> dict:
        return app.state.mark_3_moonshot_lab.decision(_moonshot_lab_values(payload))

    @app.post("/mark-3/outcomes/record")
    def mark_3_outcomes_record(payload: Mark3OutcomeRecordRequest) -> dict:
        return app.state.mark_3_outcome_memory.record(payload.model_dump())

    @app.get("/mark-3/outcomes")
    def mark_3_outcomes_list() -> dict:
        return {
            "outcomes": app.state.mark_3_outcome_memory.list_outcomes(),
            "failures": app.state.mark_3_outcome_memory.list_failures(),
            "audit": app.state.mark_3_outcome_memory.audit(),
        }

    @app.post("/mark-3/learning/proposals")
    def mark_3_learning_proposals_create(payload: Mark3LearningProposalRequest) -> dict:
        data = payload.model_dump()
        source_outcome_id = data.get("source_outcome_id")
        try:
            if source_outcome_id:
                outcome = app.state.mark_3_outcome_memory.get_outcome(source_outcome_id)
                return app.state.mark_3_learning_proposals.create_from_outcome(outcome, data)
            return app.state.mark_3_learning_proposals.create(data)
        except KeyError:
            raise HTTPException(status_code=404, detail="source outcome not found")

    @app.get("/mark-3/learning/proposals")
    def mark_3_learning_proposals_list() -> dict:
        return {
            "proposals": app.state.mark_3_learning_proposals.list(),
            "audit": app.state.mark_3_learning_proposals.audit(),
        }

    @app.post("/mark-3/learning/proposals/{proposal_id}/approve")
    def mark_3_learning_proposals_approve(proposal_id: str, payload: Mark3LearningProposalDecisionRequest) -> dict:
        try:
            return app.state.mark_3_learning_proposals.approve(
                proposal_id,
                actor=payload.actor,
                approval_level=payload.approval_level,
                reason=payload.reason,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="proposal not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/mark-3/learning/proposals/{proposal_id}/reject")
    def mark_3_learning_proposals_reject(proposal_id: str, payload: Mark3LearningProposalDecisionRequest) -> dict:
        try:
            return app.state.mark_3_learning_proposals.reject(
                proposal_id,
                actor=payload.actor,
                reason=payload.reason,
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="proposal not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/mark-3/research-radar/plan")
    def mark_3_research_radar_plan(payload: Mark3ResearchRadarPlanRequest) -> dict:
        return app.state.mark_3_research_radar.plan(payload.model_dump())

    @app.get("/mark-3/research-radar/status")
    def mark_3_research_radar_status() -> dict:
        return {
            **app.state.mark_3_research_radar.status(),
            "audit": app.state.mark_3_research_radar.audit(),
        }

    @app.get("/mark-3/research-execution/status")
    def mark_3_research_execution_status() -> dict:
        return app.state.mark_3_research_execution_bridge.status()

    @app.post("/mark-3/research-execution/preview")
    def mark_3_research_execution_preview(payload: Mark3ResearchExecutionPreviewRequest) -> dict:
        return app.state.mark_3_research_execution_bridge.preview(payload.model_dump())

    @app.post("/mark-3/research-execution/candidate")
    def mark_3_research_execution_candidate(payload: Mark3ResearchExecutionCandidateRequest) -> dict:
        return app.state.mark_3_research_execution_bridge.candidate(payload.model_dump())

    @app.get("/mark-3/research-execution/{research_id}")
    def mark_3_research_execution_get(research_id: str) -> dict:
        try:
            return app.state.mark_3_research_execution_bridge.get(research_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="research execution not found")

    @app.get("/mark-1/capabilities")
    def mark_1_capabilities() -> dict:
        return Mark1CapabilityMatrix().to_dict()

    @app.get("/mark-1/e2e-smoke")
    def mark_1_e2e_smoke() -> dict:
        return Mark1E2ERealOpsSmoke(
            builder=app.state.adaptive_saas_builder,
            monetization=app.state.monetization_engine,
        ).run()

    @app.get("/mark-1/dangerous-route-audit")
    def mark_1_dangerous_route_audit() -> dict:
        return Mark1DangerousRouteAudit().audit(route.path for route in app.routes)

    @app.get("/mark-1/approval-path-audit")
    def mark_1_approval_path_audit() -> dict:
        return Mark1ApprovalPathAudit(app.state.approval_execution_semantics).audit()

    @app.get("/mark-1/docs-status")
    def mark_1_docs_status() -> dict:
        return Mark1DocumentationStatus().to_dict()

    @app.get("/mark-1/runbook")
    def mark_1_runbook() -> dict:
        return Mark1OperationalRunbook().to_dict()

    @app.get("/mark-1/known-limitations")
    def mark_1_known_limitations() -> dict:
        return Mark1KnownLimitations().to_dict()

    @app.get("/mark-1/next-plan")
    def mark_1_next_plan() -> dict:
        return Mark2NextPlan().to_dict()

    @app.get("/operational/status")
    def operational_status() -> dict:
        return build_operational_system_status().to_dict()

    @app.get("/operational/capabilities")
    def operational_capabilities() -> dict:
        return build_capability_registry_view().to_dict()

    @app.get("/operational/readiness")
    def operational_readiness() -> dict:
        return build_readiness_matrix_view().to_dict()

    @app.get("/operational/safety-boundaries")
    def operational_safety_boundaries() -> dict:
        return build_safety_boundary_summary().to_dict()

    @app.get("/operational/console-summary")
    def operational_console_summary() -> dict:
        return build_operational_console_summary()

    @app.get("/voice-runtime/status")
    def wake_voice_status() -> dict:
        return app.state.wake_voice_runtime.status()

    @app.get("/voice-runtime/policy")
    def wake_voice_policy() -> dict:
        return app.state.wake_voice_runtime.policy()

    @app.post("/voice-runtime/preview-wake-parse")
    def wake_voice_preview_parse(payload: WakeVoicePreviewRequest) -> dict:
        return app.state.wake_voice_runtime.parse(payload.text, confidence=payload.confidence).to_dict()

    @app.post("/voice-runtime/preview-session")
    def wake_voice_preview_session(payload: WakeVoicePreviewRequest) -> dict:
        return app.state.voice_session_control.preview_session(
            payload.text,
            confidence=payload.confidence,
            answer_mode=payload.answer_mode,
        ).to_dict()

    @app.post("/voice-runtime/preview-command")
    def wake_voice_preview_command(payload: WakeVoicePreviewRequest) -> dict:
        return app.state.voice_session_control.preview_command(payload.text, confidence=payload.confidence).to_dict()

    @app.post("/voice-runtime/preview-stop")
    def wake_voice_preview_stop(payload: WakeVoicePreviewRequest) -> dict:
        return app.state.voice_session_control.preview_stop(payload.text).to_dict()

    @app.get("/camera-control/status")
    def camera_control_status() -> dict:
        return app.state.camera_control_runtime.status()

    @app.get("/camera-control/policy")
    def camera_control_policy() -> dict:
        return app.state.camera_control_runtime.policy()

    @app.post("/camera-control/preview-session")
    def camera_control_preview_session(payload: CameraControlPreviewRequest) -> dict:
        return app.state.camera_control_runtime.preview_session(
            **payload.model_dump(exclude={"phrase"})
        ).to_dict()

    @app.post("/camera-control/preview-stop")
    def camera_control_preview_stop(payload: CameraControlPreviewRequest) -> dict:
        return app.state.camera_control_runtime.preview_stop(payload.phrase).to_dict()

    @app.get("/approvals/status")
    def approvals_status() -> dict:
        return app.state.approval_hardening.status()

    @app.get("/approvals/policy")
    def approvals_policy() -> dict:
        return StrongApprovalPolicy().to_dict()

    @app.get("/approvals/audit-preview")
    def approvals_audit_preview() -> dict:
        return app.state.approval_hardening.audit_trail.preview()

    @app.get("/approval-execution/status")
    def approval_execution_status() -> dict:
        return app.state.approval_execution_semantics.status()

    @app.get("/approval-execution/policy")
    def approval_execution_policy() -> dict:
        return app.state.approval_execution_semantics.policy()

    @app.post("/approval-execution/preview-decision")
    def approval_execution_preview_decision(payload: ApprovalExecutionDecisionPreviewRequest) -> dict:
        try:
            return app.state.approval_execution_semantics.preview_decision(**payload.model_dump()).to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/approval-execution/preview-critical-warning")
    def approval_execution_preview_critical_warning(payload: CriticalActionWarningPreviewRequest) -> dict:
        return app.state.approval_execution_semantics.preview_critical_warning(**payload.model_dump()).to_dict()

    @app.get("/roadmap/marks")
    def roadmap_marks() -> dict:
        return app.state.approval_execution_semantics.roadmap().to_dict()

    @app.post("/approvals/preview-request")
    def approvals_preview_request(payload: ApprovalPreviewRequest) -> dict:
        try:
            record = app.state.approval_hardening.request(**payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return record.to_dict()

    @app.post("/approvals/preview-decision")
    def approvals_preview_decision(payload: ApprovalDecisionPreviewRequest) -> dict:
        try:
            record = app.state.approval_hardening.decide(**payload.model_dump())
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return record.to_dict()

    @app.post("/approvals/preview-gate")
    def approvals_preview_gate(payload: ApprovalGatePreviewRequest) -> dict:
        approval = None
        if payload.approval_id:
            try:
                approval = app.state.approval_hardening.get(payload.approval_id)
                app.state.approval_hardening.refresh_expiration(approval)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
        return evaluate_permission_gate(
            payload.context or {},
            approval,
            audit_trail=app.state.approval_hardening.audit_trail,
        ).to_dict()

    def runtime_request(payload: RuntimePreviewRequest):
        values = payload.model_dump(
            exclude={
                "approval_id",
                "policy_allowed",
                "sandbox_available",
                "filesystem_scope_present",
                "network_allowed",
                "secrets_authorized",
                "timeout_present",
                "rollback_available",
                "rollback_steps",
                "rollback_notes",
            }
        )
        values["request_id"] = values["request_id"] or str(uuid4())
        values["scope"] = values["scope"] or []
        values["payload_summary"] = values["payload_summary"] or {}
        return app.state.controlled_runtime_bridge.prepare_request(**values)

    @app.get("/runtime/status")
    def runtime_status() -> dict:
        return app.state.controlled_runtime_bridge.status()

    @app.get("/runtime/policy")
    def runtime_policy() -> dict:
        return app.state.controlled_runtime_bridge.policy()

    @app.post("/runtime/preview-plan")
    def runtime_preview_plan(payload: RuntimePreviewRequest) -> dict:
        return runtime_request(payload).to_dict()

    @app.post("/runtime/preview-dry-run")
    def runtime_preview_dry_run(payload: RuntimePreviewRequest) -> dict:
        return app.state.controlled_runtime_bridge.preview_dry_run(runtime_request(payload)).to_dict()

    @app.post("/runtime/preview-rollback")
    def runtime_preview_rollback(payload: RuntimePreviewRequest) -> dict:
        return app.state.controlled_runtime_bridge.preview_rollback(
            runtime_request(payload),
            rollback_available=payload.rollback_available,
            rollback_steps=payload.rollback_steps,
            rollback_notes=payload.rollback_notes,
        ).to_dict()

    @app.post("/runtime/preview-gate")
    def runtime_preview_gate(payload: RuntimePreviewRequest) -> dict:
        request = runtime_request(payload)
        approval = None
        if payload.approval_id:
            try:
                approval = app.state.approval_hardening.get(payload.approval_id)
                app.state.approval_hardening.refresh_expiration(approval)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
        dry_run = app.state.controlled_runtime_bridge.preview_dry_run(request)
        sandbox = app.state.controlled_runtime_bridge.preview_sandbox(
            request,
            sandbox_available=payload.sandbox_available,
            filesystem_scope_present=payload.filesystem_scope_present,
            network_allowed=payload.network_allowed,
            secrets_authorized=payload.secrets_authorized,
            timeout_present=payload.timeout_present,
        )
        rollback = app.state.controlled_runtime_bridge.preview_rollback(
            request,
            rollback_available=payload.rollback_available,
            rollback_steps=payload.rollback_steps,
            rollback_notes=payload.rollback_notes,
        )
        return app.state.controlled_runtime_bridge.preview_gate(
            request,
            dry_run=dry_run,
            sandbox=sandbox,
            rollback=rollback,
            approval=approval,
            policy_allowed=payload.policy_allowed,
        ).to_dict()

    def tool_invocation_preview(payload: ToolInvocationPreviewRequest):
        values = payload.model_dump(
            exclude={
                "approval_id",
                "granted_permissions",
                "policy_allowed",
                "sandbox_available",
                "filesystem_scope_present",
                "network_allowed",
                "secrets_authorized",
                "timeout_present",
                "rollback_available",
                "rollback_steps",
            }
        )
        values["scope"] = values["scope"] or []
        values["payload_summary"] = values["payload_summary"] or {}
        return app.state.tool_invocation_layer.preview_invocation(**values)

    @app.get("/tools/status")
    def tools_status() -> dict:
        return app.state.tool_invocation_layer.status()

    @app.get("/tools/registry")
    def tools_registry() -> dict:
        return app.state.tool_invocation_layer.registry.snapshot().to_dict()

    @app.get("/tools/policy")
    def tools_policy() -> dict:
        return app.state.tool_invocation_layer.policy()

    @app.post("/tools/preview-registration")
    def tools_preview_registration(payload: ToolRegistrationPreviewRequest) -> dict:
        return preview_tool_registration(payload.model_dump()).to_dict()

    @app.post("/tools/preview-connector")
    def tools_preview_connector(payload: ConnectorPreviewRequest) -> dict:
        return preview_connector(payload.model_dump()).to_dict()

    @app.post("/tools/preview-invocation")
    def tools_preview_invocation(payload: ToolInvocationPreviewRequest) -> dict:
        return tool_invocation_preview(payload).to_dict()

    @app.post("/tools/preview-permission")
    def tools_preview_permission(payload: ToolInvocationPreviewRequest) -> dict:
        approval = None
        if payload.approval_id:
            try:
                approval = app.state.approval_hardening.get(payload.approval_id)
                app.state.approval_hardening.refresh_expiration(approval)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
        return app.state.tool_invocation_layer.preview_permission(
            tool_invocation_preview(payload),
            approval=approval,
            granted_permissions=payload.granted_permissions,
            policy_allowed=payload.policy_allowed,
            sandbox_available=payload.sandbox_available,
            filesystem_scope_present=payload.filesystem_scope_present,
            network_allowed=payload.network_allowed,
            secrets_authorized=payload.secrets_authorized,
            timeout_present=payload.timeout_present,
            rollback_available=payload.rollback_available,
            rollback_steps=payload.rollback_steps,
        ).to_dict()

    def memory_record(payload: MemoryRecordPreviewRequest):
        values = payload.model_dump(exclude={"stop_controls_blocked"})
        values["tags"] = values["tags"] or []
        values["blocked_reasons"] = values["blocked_reasons"] or []
        return app.state.personal_memory_control.preview_record(**values)

    @app.get("/personal-memory/status")
    def personal_memory_status() -> dict:
        return app.state.personal_memory_control.status()

    @app.post("/memory/preview-record")
    def memory_preview_record(payload: MemoryRecordPreviewRequest) -> dict:
        return memory_record(payload).to_dict()

    @app.post("/memory/preview-activation")
    def memory_preview_activation(payload: MemoryRecordPreviewRequest) -> dict:
        approval = None
        if payload.approval_id:
            try:
                approval = app.state.approval_hardening.get(payload.approval_id)
                app.state.approval_hardening.refresh_expiration(approval)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
        return app.state.personal_memory_control.preview_activation(
            memory_record(payload),
            approval=approval,
            stop_controls_blocked=payload.stop_controls_blocked,
        ).to_dict()

    @app.post("/memory/preview-deactivation")
    def memory_preview_deactivation(payload: MemoryRecordPreviewRequest) -> dict:
        return app.state.personal_memory_control.preview_deactivation(
            memory_record(payload),
            reason=payload.reason,
        )

    def scheduler_item(payload: SchedulerControlPreviewRequest):
        values = payload.model_dump(
            include={
                "item_id",
                "title",
                "item_type",
                "schedule_expression",
                "due_at",
                "timezone",
                "payload_summary",
                "requires_approval",
                "requires_strong_approval",
                "side_effects",
                "tool_invocation_required",
                "controlled_runtime_required",
                "external_call_required",
                "private_source_required",
                "status",
                "created_at",
                "last_previewed_at",
                "blocked_reasons",
            }
        )
        values["payload_summary"] = values["payload_summary"] or {}
        values["blocked_reasons"] = values["blocked_reasons"] or []
        return app.state.scheduler_control.preview_item(**values)

    @app.get("/scheduler/status")
    def scheduler_status() -> dict:
        return app.state.scheduler_control.status()

    @app.get("/scheduler/policy")
    def scheduler_policy() -> dict:
        return app.state.scheduler_control.policy()

    @app.post("/scheduler/preview-item")
    def scheduler_preview_item(payload: SchedulerControlPreviewRequest) -> dict:
        return scheduler_item(payload).to_dict()

    @app.post("/scheduler/preview-due")
    def scheduler_preview_due(payload: SchedulerControlPreviewRequest) -> dict:
        items = [
            app.state.scheduler_control.preview_item(**dict(item))
            for item in (payload.items or [])
        ]
        if not items and payload.item_id:
            items = [scheduler_item(payload)]
        return app.state.scheduler_control.preview_due(items, now=payload.now).to_dict()

    @app.post("/scheduler/preview-daily-review")
    def scheduler_preview_daily_review(payload: SchedulerControlPreviewRequest) -> dict:
        return app.state.scheduler_control.preview_daily_review(**payload.model_dump()).to_dict()

    @app.post("/scheduler/preview-weekly-review")
    def scheduler_preview_weekly_review(payload: SchedulerControlPreviewRequest) -> dict:
        return app.state.scheduler_control.preview_weekly_review(**payload.model_dump()).to_dict()

    @app.post("/scheduler/preview-stop-controls")
    def scheduler_preview_stop_controls(payload: SchedulerControlPreviewRequest) -> dict:
        return app.state.scheduler_control.preview_stop_controls(
            **payload.model_dump(
                include={
                    "global_pause",
                    "memory_activation_paused",
                    "scheduler_paused",
                    "routines_paused",
                    "personal_os_paused",
                    "external_sources_paused",
                    "tool_invocations_paused",
                    "reason",
                }
            )
        ).to_dict()

    @app.get("/command-center")
    def command_center() -> dict:
        view = build_command_center_view_model(
            view_id=f"command-center-{uuid4()}",
            generated_at=_now_iso(),
            metadata={
                "phase": "D.1",
                "source": "empty_placeholder_snapshot",
                "store_connected": False,
                "operator_console": "prepare_only",
                "multi_device_runtime": "prepare_only",
                "sandbox_execution": "prepare_only",
                "tool_adoption_pipeline": "prepare_only",
                "asset_factory_web_builder": "prepare_only",
                "deploy_publishing_control": "prepare_only",
                "marketing_distribution_engine": "prepare_only",
                "payments_revenue": "prepare_only",
                "daily_operator_scheduler": "prepare_only",
                "continuous_learning_tech_radar": "prepare_only",
                "advanced_personalization_user_model": "prepare_only",
                "future_moonshot_layer": "prepare_only",
            },
        )
        return view.to_dict()

    @app.get("/continuous-learning/status")
    def continuous_learning_status() -> dict:
        return ContinuousLearningStatus.placeholder().to_dict()

    @app.get("/continuous-learning/policy")
    def continuous_learning_policy() -> dict:
        return TechRadarSafetyPolicy.placeholder().to_dict()

    @app.post("/continuous-learning/candidate-profile")
    def continuous_learning_candidate_profile(payload: ContinuousLearningPreviewRequest) -> dict:
        return TechnologyCandidateProfile.from_request(payload.model_dump()).to_dict()

    @app.post("/continuous-learning/relevance-filter")
    def continuous_learning_relevance_filter(payload: ContinuousLearningPreviewRequest) -> dict:
        return RelevanceFilterPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/continuous-learning/contrarian-review")
    def continuous_learning_contrarian_review(payload: ContinuousLearningPreviewRequest) -> dict:
        return ContrarianReviewPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/continuous-learning/proposal-preview")
    def continuous_learning_proposal_preview(payload: ContinuousLearningPreviewRequest) -> dict:
        return LearningProposalPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/continuous-learning/impact-analysis")
    def continuous_learning_impact_analysis(payload: ContinuousLearningPreviewRequest) -> dict:
        return ProposalImpactAnalysis.from_request(payload.model_dump()).to_dict()

    @app.post("/continuous-learning/risk-analysis")
    def continuous_learning_risk_analysis(payload: ContinuousLearningPreviewRequest) -> dict:
        return ProposalRiskAnalysis.from_request(payload.model_dump()).to_dict()

    @app.post("/continuous-learning/pr-planner")
    def continuous_learning_pr_planner(payload: ContinuousLearningPreviewRequest) -> dict:
        return PRPlannerPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/continuous-learning/approval-workflow")
    def continuous_learning_approval_workflow(payload: ContinuousLearningPreviewRequest) -> dict:
        return ApprovalWorkflowPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/continuous-learning/backlog-preview")
    def continuous_learning_backlog_preview(payload: ContinuousLearningPreviewRequest) -> dict:
        return LearningBacklogPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/continuous-learning/decision-preview")
    def continuous_learning_decision_preview(payload: ContinuousLearningPreviewRequest) -> dict:
        return TechRadarDecisionPreview.from_request(payload.model_dump()).to_dict()

    @app.get("/personalization/status")
    def personalization_status() -> dict:
        return AdvancedPersonalizationStatus.placeholder().to_dict()

    @app.get("/personalization/policy")
    def personalization_policy() -> dict:
        return UserModelSafetyPolicy.placeholder().to_dict()

    @app.post("/personalization/preference-profile")
    def personalization_preference_profile(payload: PersonalizationPreviewRequest) -> dict:
        return UserPreferenceProfilePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/speech-style")
    def personalization_speech_style(payload: PersonalizationPreviewRequest) -> dict:
        return SpeechStylePatternPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/decision-model")
    def personalization_decision_model(payload: PersonalizationPreviewRequest) -> dict:
        return DecisionModelPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/business-goal")
    def personalization_business_goal(payload: PersonalizationPreviewRequest) -> dict:
        return BusinessGoalModelPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/contrarian-mode")
    def personalization_contrarian_mode(payload: PersonalizationPreviewRequest) -> dict:
        return ContrarianModeProfilePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/memory-proposal")
    def personalization_memory_proposal(payload: PersonalizationPreviewRequest) -> dict:
        return MemoryProposalPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/memory-review")
    def personalization_memory_review(payload: PersonalizationPreviewRequest) -> dict:
        return MemoryReviewPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/memory-lifecycle")
    def personalization_memory_lifecycle(payload: PersonalizationPreviewRequest) -> dict:
        return MemoryLifecyclePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/memory-audit-reversal")
    def personalization_memory_audit_reversal(payload: PersonalizationPreviewRequest) -> dict:
        return MemoryAuditReversalPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/uncertainty")
    def personalization_uncertainty(payload: PersonalizationPreviewRequest) -> dict:
        return UncertaintyHandlingPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/recommendation")
    def personalization_recommendation(payload: PersonalizationPreviewRequest) -> dict:
        return PersonalizationRecommendationPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/sensitive-inference-guard")
    def personalization_sensitive_inference_guard(payload: PersonalizationPreviewRequest) -> dict:
        return SensitiveInferenceGuardPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personalization/approval-requirements")
    def personalization_approval_requirements(payload: PersonalizationPreviewRequest) -> dict:
        return PersonalizationApprovalRequirements.from_request(payload.model_dump()).to_dict()

    @app.get("/future-moonshot/status")
    def future_moonshot_status() -> dict:
        return FutureMoonshotStatus.placeholder().to_dict()

    @app.get("/future-moonshot/policy")
    def future_moonshot_policy() -> dict:
        return MoonshotSafetyPolicy.placeholder().to_dict()

    @app.post("/future-moonshot/capability-preview")
    def future_moonshot_capability_preview(payload: FutureMoonshotPreviewRequest) -> dict:
        return MoonshotCapabilityPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/smart-glasses-preview")
    def future_moonshot_smart_glasses_preview(payload: FutureMoonshotPreviewRequest) -> dict:
        return SmartGlassesIntegrationPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/ar-overlay-preview")
    def future_moonshot_ar_overlay_preview(payload: FutureMoonshotPreviewRequest) -> dict:
        return AROverlayPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/robotics-drone-safety-review")
    def future_moonshot_robotics_drone_safety_review(payload: FutureMoonshotPreviewRequest) -> dict:
        return RoboticsDroneSafetyReviewPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/deep-simulation-preview")
    def future_moonshot_deep_simulation_preview(payload: FutureMoonshotPreviewRequest) -> dict:
        return DeepSimulationPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/physical-automation-preview")
    def future_moonshot_physical_automation_preview(payload: FutureMoonshotPreviewRequest) -> dict:
        return PhysicalWorldAutomationPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/legal-safety-review")
    def future_moonshot_legal_safety_review(payload: FutureMoonshotPreviewRequest) -> dict:
        return LegalSafetyReviewPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/controlled-environment-preview")
    def future_moonshot_controlled_environment_preview(payload: FutureMoonshotPreviewRequest) -> dict:
        return ControlledEnvironmentPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/immediate-stop-preview")
    def future_moonshot_immediate_stop_preview(payload: FutureMoonshotPreviewRequest) -> dict:
        return ImmediateStopPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/audit-rollback-preview")
    def future_moonshot_audit_rollback_preview(payload: FutureMoonshotPreviewRequest) -> dict:
        return MoonshotAuditRollbackPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/monetization-advantage-review")
    def future_moonshot_monetization_advantage_review(payload: FutureMoonshotPreviewRequest) -> dict:
        return MonetizationAdvantageReviewPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/identity-impersonation-guard")
    def future_moonshot_identity_impersonation_guard(payload: FutureMoonshotPreviewRequest) -> dict:
        return IdentityImpersonationGuardPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/future-moonshot/approval-requirements")
    def future_moonshot_approval_requirements(payload: FutureMoonshotPreviewRequest) -> dict:
        return MoonshotApprovalRequirements.from_request(payload.model_dump()).to_dict()

    @app.get("/personal-os/status")
    def personal_os_status() -> dict:
        return {
            **app.state.personal_os_control.status(),
            **PersonalOSEnvironmentStatus.placeholder().to_dict(),
        }

    @app.get("/personal-os/policy")
    def personal_os_policy() -> dict:
        return app.state.personal_os_control.policy()

    @app.post("/personal-os/preview-state")
    def personal_os_preview_state(payload: PersonalOSStatePreviewRequest) -> dict:
        values = payload.model_dump()
        for name in (
            "daily_priorities",
            "weekly_priorities",
            "routines",
            "reminders",
            "review_queue",
            "authorized_sources",
            "blocked_sources",
            "blocked_reasons",
        ):
            values[name] = values[name] or []
        return app.state.personal_os_control.preview_state(**values).to_dict()

    @app.get("/personal-os/privacy-policy")
    def personal_os_privacy_policy() -> dict:
        return PersonalOSPrivacyPolicy.placeholder().to_dict()

    @app.post("/personal-os/source-consent-preview")
    def personal_os_source_consent_preview(payload: PersonalOSPreviewRequest) -> dict:
        return ContextSourceConsentPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/daily-state")
    def personal_os_daily_state(payload: PersonalOSPreviewRequest) -> dict:
        return DailyStatePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/pc-environment-state")
    def personal_os_pc_environment_state(payload: PersonalOSPreviewRequest) -> dict:
        return PCEnvironmentStatePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/awareness-source-preview")
    def personal_os_awareness_source_preview(payload: PersonalOSPreviewRequest) -> dict:
        return AwarenessSourcePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/local-files-scope")
    def personal_os_local_files_scope(payload: PersonalOSPreviewRequest) -> dict:
        return LocalFilesScopePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/context-switch")
    def personal_os_context_switch(payload: PersonalOSPreviewRequest) -> dict:
        return ContextSwitchingPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/attention-protection")
    def personal_os_attention_protection(payload: PersonalOSPreviewRequest) -> dict:
        return AttentionProtectionPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/personal-routine")
    def personal_os_personal_routine(payload: PersonalOSPreviewRequest) -> dict:
        return PersonalRoutinePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/energy-focus-support")
    def personal_os_energy_focus_support(payload: PersonalOSPreviewRequest) -> dict:
        return EnergyFocusSupportPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/guest-mode")
    def personal_os_guest_mode(payload: PersonalOSPreviewRequest) -> dict:
        return GuestModeContextPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/visible-reason-audit")
    def personal_os_visible_reason_audit(payload: PersonalOSPreviewRequest) -> dict:
        return VisibleReasonAuditPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/personal-os/approval-requirements")
    def personal_os_approval_requirements(payload: PersonalOSPreviewRequest) -> dict:
        return PersonalOSApprovalRequirements.from_request(payload.model_dump()).to_dict()

    @app.get("/daily-operator/status")
    def daily_operator_status() -> dict:
        return DailyOperatorSchedulerStatus.placeholder().to_dict()

    @app.get("/daily-operator/policy")
    def daily_operator_policy() -> dict:
        return SchedulerSafetyPolicy.placeholder().to_dict()

    @app.post("/daily-operator/briefing-preview")
    def daily_operator_briefing_preview(payload: DailyOperatorPreviewRequest) -> dict:
        return DailyBriefingPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/daily-operator/daily-plan")
    def daily_operator_daily_plan(payload: DailyOperatorPreviewRequest) -> dict:
        return DailyPlanPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/daily-operator/schedule-rule")
    def daily_operator_schedule_rule(payload: DailyOperatorPreviewRequest) -> dict:
        return ScheduleRulePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/daily-operator/recurrence-preview")
    def daily_operator_recurrence_preview(payload: DailyOperatorPreviewRequest) -> dict:
        return RecurrencePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/daily-operator/task-queue-preview")
    def daily_operator_task_queue_preview(payload: DailyOperatorPreviewRequest) -> dict:
        return TaskQueuePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/daily-operator/reminder-preview")
    def daily_operator_reminder_preview(payload: DailyOperatorPreviewRequest) -> dict:
        return ReminderNotificationPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/daily-operator/execution-window")
    def daily_operator_execution_window(payload: DailyOperatorPreviewRequest) -> dict:
        return ExecutionWindowPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/daily-operator/retry-policy")
    def daily_operator_retry_policy(payload: DailyOperatorPreviewRequest) -> dict:
        return MissedRunRetryPolicyPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/daily-operator/handoff-summary")
    def daily_operator_handoff_summary(payload: DailyOperatorPreviewRequest) -> dict:
        return OperatorHandoffSummaryPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/daily-operator/approval-requirements")
    def daily_operator_approval_requirements(payload: DailyOperatorPreviewRequest) -> dict:
        return SchedulerApprovalRequirements.from_request(payload.model_dump()).to_dict()

    @app.get("/payments-revenue/status")
    def payments_revenue_status() -> dict:
        return PaymentsRevenueStatus.placeholder().to_dict()

    @app.get("/payments-revenue/policy")
    def payments_revenue_policy() -> dict:
        return PaymentsRevenuePolicy.placeholder().to_dict()

    @app.post("/payments-revenue/pricing-preview")
    def payments_revenue_pricing_preview(payload: PaymentsRevenuePreviewRequest) -> dict:
        return PricingModelPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/payments-revenue/checkout-plan")
    def payments_revenue_checkout_plan(payload: PaymentsRevenuePreviewRequest) -> dict:
        return CheckoutPlanPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/payments-revenue/provider-preview")
    def payments_revenue_provider_preview(payload: PaymentsRevenuePreviewRequest) -> dict:
        return PaymentProviderPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/payments-revenue/metrics-preview")
    def payments_revenue_metrics_preview(payload: PaymentsRevenuePreviewRequest) -> dict:
        return RevenueMetricsPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/payments-revenue/subscription-preview")
    def payments_revenue_subscription_preview(payload: PaymentsRevenuePreviewRequest) -> dict:
        return SubscriptionPlanPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/payments-revenue/invoice-payment-link-preview")
    def payments_revenue_invoice_payment_link_preview(payload: PaymentsRevenuePreviewRequest) -> dict:
        return InvoicePaymentLinkPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/payments-revenue/refund-chargeback-policy")
    def payments_revenue_refund_chargeback_policy(payload: PaymentsRevenuePreviewRequest) -> dict:
        return RefundChargebackPolicyPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/payments-revenue/financial-risk-guard")
    def payments_revenue_financial_risk_guard(payload: PaymentsRevenuePreviewRequest) -> dict:
        return FinancialRiskGuardPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/payments-revenue/revenue-experiment")
    def payments_revenue_revenue_experiment(payload: PaymentsRevenuePreviewRequest) -> dict:
        return RevenueExperimentPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/payments-revenue/approval-requirements")
    def payments_revenue_approval_requirements(payload: PaymentsRevenuePreviewRequest) -> dict:
        return PaymentApprovalRequirements.from_request(payload.model_dump()).to_dict()

    @app.get("/monetization/status")
    def monetization_status() -> dict:
        return app.state.monetization_engine.status()

    @app.get("/monetization/policy")
    def monetization_policy() -> dict:
        return app.state.monetization_engine.policy()

    @app.post("/monetization/preview-pricing")
    def monetization_preview_pricing(payload: MonetizationPreviewRequest) -> dict:
        return app.state.monetization_engine.preview_pricing(payload.model_dump())

    @app.post("/monetization/preview-revenue")
    def monetization_preview_revenue(payload: MonetizationPreviewRequest) -> dict:
        return app.state.monetization_engine.preview_revenue(payload.model_dump())

    @app.post("/monetization/preview-budget")
    def monetization_preview_budget(payload: MonetizationPreviewRequest) -> dict:
        return app.state.monetization_engine.preview_budget(payload.model_dump())

    @app.post("/monetization/preview-payment-approval")
    def monetization_preview_payment_approval(payload: MonetizationPreviewRequest) -> dict:
        return app.state.monetization_engine.preview_payment_approval(payload.model_dump())

    @app.post("/monetization/preview-stripe-readiness")
    def monetization_preview_stripe_readiness(payload: MonetizationPreviewRequest) -> dict:
        return app.state.monetization_engine.preview_stripe_readiness(payload.model_dump())

    @app.post("/monetization/preview-action")
    def monetization_preview_action(payload: MonetizationPreviewRequest) -> dict:
        return app.state.monetization_engine.preview_action(payload.model_dump())

    @app.post("/monetization/preview-unit-economics")
    def monetization_preview_unit_economics(payload: MonetizationPreviewRequest) -> dict:
        return app.state.monetization_engine.preview_unit_economics(payload.model_dump())

    @app.get("/product-builder/status")
    def product_builder_status() -> dict:
        return app.state.adaptive_saas_builder.status()

    @app.get("/product-builder/policy")
    def product_builder_policy() -> dict:
        return app.state.adaptive_saas_builder.policy()

    @app.post("/product-builder/preview-intake")
    def product_builder_preview_intake(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_intake(payload.model_dump())

    @app.post("/product-builder/preview-validation")
    def product_builder_preview_validation(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_validation(payload.model_dump())

    @app.post("/product-builder/preview-differentiation")
    def product_builder_preview_differentiation(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_differentiation(payload.model_dump())

    @app.post("/product-builder/preview-capability-blocks")
    def product_builder_preview_capability_blocks(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_capability_blocks(payload.model_dump())

    @app.post("/product-builder/preview-blueprint")
    def product_builder_preview_blueprint(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_blueprint(payload.model_dump())

    @app.post("/product-builder/preview-stack")
    def product_builder_preview_stack(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_stack(payload.model_dump())

    @app.post("/product-builder/preview-scaffold")
    def product_builder_preview_scaffold(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_scaffold(payload.model_dump())

    @app.post("/product-builder/preview-landing")
    def product_builder_preview_landing(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_landing(payload.model_dump())

    @app.post("/product-builder/preview-publishing")
    def product_builder_preview_publishing(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_publishing(payload.model_dump())

    @app.post("/product-builder/preview-deploy")
    def product_builder_preview_deploy(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_deploy(payload.model_dump())

    @app.post("/product-builder/preview-execution-candidate")
    def product_builder_preview_execution_candidate(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_execution_candidate(payload.model_dump())

    @app.post("/product-builder/preview-launch-readiness")
    def product_builder_preview_launch_readiness(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_launch_readiness(payload.model_dump())

    @app.post("/product-builder/preview-action")
    def product_builder_preview_action(payload: ProductBuilderPreviewRequest) -> dict:
        return app.state.adaptive_saas_builder.preview_action(payload.model_dump())

    @app.get("/marketing-distribution/status")
    def marketing_distribution_status() -> dict:
        return MarketingDistributionStatus.placeholder().to_dict()

    @app.get("/marketing-distribution/policy")
    def marketing_distribution_policy() -> dict:
        return MarketingDistributionPolicy.placeholder().to_dict()

    @app.post("/marketing-distribution/audience-preview")
    def marketing_distribution_audience_preview(payload: MarketingDistributionPreviewRequest) -> dict:
        return AudienceSegmentPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/marketing-distribution/channel-strategy")
    def marketing_distribution_channel_strategy(payload: MarketingDistributionPreviewRequest) -> dict:
        return ChannelStrategyPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/marketing-distribution/campaign-plan")
    def marketing_distribution_campaign_plan(payload: MarketingDistributionPreviewRequest) -> dict:
        return CampaignPlanPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/marketing-distribution/content-pack")
    def marketing_distribution_content_pack(payload: MarketingDistributionPreviewRequest) -> dict:
        return ContentDistributionPackPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/marketing-distribution/measurement-plan")
    def marketing_distribution_measurement_plan(payload: MarketingDistributionPreviewRequest) -> dict:
        return MeasurementPlanPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/marketing-distribution/budget-guard")
    def marketing_distribution_budget_guard(payload: MarketingDistributionPreviewRequest) -> dict:
        return BudgetSpendGuardPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/marketing-distribution/launch-checklist")
    def marketing_distribution_launch_checklist(payload: MarketingDistributionPreviewRequest) -> dict:
        return LaunchChecklistPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/marketing-distribution/approval-requirements")
    def marketing_distribution_approval_requirements(payload: MarketingDistributionPreviewRequest) -> dict:
        return DistributionApprovalRequirements.from_request(payload.model_dump()).to_dict()

    @app.get("/deploy-publishing/status")
    def deploy_publishing_status() -> dict:
        return DeployPublishingStatus.placeholder().to_dict()

    @app.get("/deploy-publishing/policy")
    def deploy_publishing_policy() -> dict:
        return DeployPublishingPolicy.placeholder().to_dict()

    @app.post("/deploy-publishing/target-preview")
    def deploy_publishing_target_preview(payload: DeployPublishingPreviewRequest) -> dict:
        return DeploymentTargetPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/deploy-publishing/publish-plan")
    def deploy_publishing_publish_plan(payload: DeployPublishingPreviewRequest) -> dict:
        return PublishingPlanPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/deploy-publishing/domain-preview")
    def deploy_publishing_domain_preview(payload: DeployPublishingPreviewRequest) -> dict:
        return DomainConnectionPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/deploy-publishing/account-preview")
    def deploy_publishing_account_preview(payload: DeployPublishingPreviewRequest) -> dict:
        return ExternalAccountConnectionPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/deploy-publishing/production-preview")
    def deploy_publishing_production_preview(payload: DeployPublishingPreviewRequest) -> dict:
        return ProductionReleasePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/deploy-publishing/rollback-preview")
    def deploy_publishing_rollback_preview(payload: DeployPublishingPreviewRequest) -> dict:
        return PublishingRollbackPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/deploy-publishing/readiness-checklist")
    def deploy_publishing_readiness_checklist(payload: DeployPublishingPreviewRequest) -> dict:
        return PublishingReadinessChecklist.from_request(payload.model_dump()).to_dict()

    @app.post("/deploy-publishing/approval-requirements")
    def deploy_publishing_approval_requirements(payload: DeployPublishingPreviewRequest) -> dict:
        return PublishingApprovalRequirements.from_request(payload.model_dump()).to_dict()

    @app.get("/asset-factory/status")
    def asset_factory_status() -> dict:
        return AssetFactoryStatus.placeholder().to_dict()

    @app.get("/asset-factory/policy")
    def asset_factory_policy() -> dict:
        return AssetGenerationPolicy.placeholder().to_dict()

    @app.post("/asset-factory/web-brief")
    def asset_factory_web_brief(payload: AssetFactoryPreviewRequest) -> dict:
        return WebProjectBrief.from_request(payload.model_dump()).to_dict()

    @app.post("/asset-factory/landing-plan")
    def asset_factory_landing_plan(payload: AssetFactoryPreviewRequest) -> dict:
        return LandingPagePlan.from_request(payload.model_dump()).to_dict()

    @app.post("/asset-factory/website-structure")
    def asset_factory_website_structure(payload: AssetFactoryPreviewRequest) -> dict:
        return WebsiteStructurePlan.from_request(payload.model_dump()).to_dict()

    @app.post("/asset-factory/copy-pack")
    def asset_factory_copy_pack(payload: AssetFactoryPreviewRequest) -> dict:
        return CopyContentPackPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/asset-factory/static-asset-manifest")
    def asset_factory_static_asset_manifest(payload: AssetFactoryPreviewRequest) -> dict:
        return StaticAssetManifestPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/asset-factory/build-package-preview")
    def asset_factory_build_package_preview(payload: AssetFactoryPreviewRequest) -> dict:
        return BuildPackagePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/asset-factory/publishing-readiness")
    def asset_factory_publishing_readiness(payload: AssetFactoryPreviewRequest) -> dict:
        return PublishingReadinessPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/asset-factory/monetization-offer-preview")
    def asset_factory_monetization_offer_preview(payload: AssetFactoryPreviewRequest) -> dict:
        return MonetizationOfferPreview.from_request(payload.model_dump()).to_dict()

    @app.get("/tools/adoption/status")
    def tool_adoption_status() -> dict:
        return ToolAdoptionStatus.placeholder().to_dict()

    @app.post("/tools/candidate/profile")
    def tool_candidate_profile(payload: ToolCandidateProfileRequest) -> dict:
        return ToolCandidateProfile.from_request(payload.model_dump()).to_dict()

    @app.post("/tools/license/review")
    def tool_license_review(payload: ToolLicenseReviewRequest) -> dict:
        return ToolLicenseReview.from_request(payload.model_dump()).to_dict()

    @app.post("/tools/repo-health/review")
    def tool_repo_health_review(payload: ToolRepoHealthReviewRequest) -> dict:
        return ToolRepoHealthReview.from_request(payload.model_dump()).to_dict()

    @app.post("/tools/dependency-risk/review")
    def tool_dependency_risk_review(payload: ToolDependencyRiskReviewRequest) -> dict:
        return ToolDependencyRiskReview.from_request(payload.model_dump()).to_dict()

    @app.post("/tools/sandbox-install/proposal")
    def tool_sandbox_install_proposal(payload: ToolSandboxInstallProposalRequest) -> dict:
        return ToolSandboxInstallProposal.from_request(payload.model_dump()).to_dict()

    @app.post("/tools/spike/plan")
    def tool_spike_plan(payload: ToolSpikePlanRequest) -> dict:
        return ToolSpikePlan.from_request(payload.model_dump()).to_dict()

    @app.post("/tools/value/preview")
    def tool_value_preview(payload: ToolValueMeasurementPreviewRequest) -> dict:
        return ToolValueMeasurementPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/tools/adoption/decision-preview")
    def tool_adoption_decision_preview(payload: ToolAdoptionDecisionPreviewRequest) -> dict:
        return ToolAdoptionDecisionPreview.from_request(payload.model_dump()).to_dict()

    @app.get("/sandbox/execution/status")
    def sandbox_execution_status() -> dict:
        return SandboxExecutionStatus.placeholder().to_dict()

    @app.get("/sandbox/execution/policy")
    def sandbox_execution_policy() -> dict:
        return SandboxExecutionPolicy.placeholder().to_dict()

    @app.post("/sandbox/command/plan")
    def sandbox_command_plan(payload: SandboxCommandRequest) -> dict:
        return SandboxCommandPlan.from_request(payload.model_dump()).to_dict()

    @app.post("/sandbox/command/dry-run")
    def sandbox_command_dry_run(payload: SandboxCommandRequest) -> dict:
        return SandboxDryRunResult.from_request(payload.model_dump()).to_dict()

    @app.post("/sandbox/rollback/preview")
    def sandbox_rollback_preview(payload: SandboxCommandRequest) -> dict:
        return SandboxRollbackPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/sandbox/audit/preview")
    def sandbox_audit_preview(payload: SandboxCommandRequest) -> dict:
        return SandboxAuditPreview.from_request(payload.model_dump()).to_dict()

    @app.get("/devices/runtime/status")
    def multi_device_runtime_status() -> dict:
        return MultiDeviceRuntimeStatus.placeholder().to_dict()

    @app.get("/devices/registry")
    def device_registry() -> dict:
        return DeviceRegistrySnapshot.placeholder().to_dict()

    @app.get("/devices/capabilities")
    def device_capabilities() -> dict:
        return DeviceCapabilityProfile.placeholder().to_dict()

    @app.post("/devices/pairing/preview")
    def device_pairing_preview(payload: DevicePairingPreviewRequest) -> dict:
        return DevicePairingPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/devices/revoke/preview")
    def device_revoke_preview(payload: DeviceRevokePreviewRequest) -> dict:
        return DeviceRevokePreview.from_request(payload.model_dump()).to_dict()

    @app.post("/devices/approval-channel/preview")
    def device_approval_channel_preview(payload: DeviceApprovalChannelPreviewRequest) -> dict:
        return DeviceApprovalChannelPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/devices/sync/preview")
    def device_sync_preview(payload: DeviceSyncPreviewRequest) -> dict:
        return DeviceSyncPreview.from_request(payload.model_dump()).to_dict()

    @app.post("/devices/notifications/preview")
    def notification_routing_preview(payload: NotificationRoutingPreviewRequest) -> dict:
        return NotificationRoutingPreview.from_request(payload.model_dump()).to_dict()

    @app.get("/ambient-vision/status")
    def ambient_vision_status() -> dict:
        return AmbientVisionStatus.placeholder().to_dict()

    @app.get("/ambient-vision/privacy-policy")
    def ambient_vision_privacy_policy() -> dict:
        return AmbientVisionPrivacyPolicy.placeholder().to_dict()

    @app.post("/ambient-vision/session-preview")
    def ambient_vision_session_preview(payload: AmbientVisionSessionPreviewRequest) -> dict:
        return AmbientVisionSessionPreview.from_request(payload.model_dump()).to_dict()

    @app.get("/ambient-vision/stop-control")
    def ambient_vision_stop_control() -> dict:
        return AmbientVisionStopControl.placeholder().to_dict()

    @app.get("/operator/console/status")
    def operator_console_status() -> dict:
        return OperatorConsoleStatus.placeholder().to_dict()

    @app.get("/operator/console/capabilities")
    def operator_console_capabilities() -> dict:
        return OperatorConsoleCapabilityMatrix.placeholder().to_dict()

    @app.get("/operator/console/snapshot")
    def operator_console_snapshot() -> dict:
        snapshot = build_operator_console_snapshot(
            view_id=f"operator-command-center-{uuid4()}",
            generated_at=_now_iso(),
        )
        return snapshot.to_dict()

    @app.post("/operator/console/preview")
    def operator_console_preview(payload: OperatorConsolePreviewRequest) -> dict:
        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="text must be non-empty")
        preview = OperatorConsolePreview.from_text(
            text,
            policy_engine=app.state.policy_engine,
        )
        return preview.to_dict()

    @app.get("/mobile/companion/status")
    def mobile_companion_status() -> dict:
        return MobileCompanionStatus.placeholder().to_dict()

    @app.get("/mobile/companion/permissions")
    def mobile_companion_permissions() -> dict:
        return MobileCompanionPermissionPolicy.placeholder().to_dict()

    @app.get("/mobile/command-center")
    def mobile_command_center() -> dict:
        view = build_command_center_view_model(
            view_id=f"mobile-command-center-{uuid4()}",
            generated_at=_now_iso(),
            metadata={
                "phase": "F",
                "source": "mobile_empty_placeholder_snapshot",
                "store_connected": False,
                "mobile_companion": "prepare_only",
            },
        )
        return MobileCommandCenterSnapshot.from_command_center_view(view).to_dict()

    @app.post("/mobile/intent/preview")
    def mobile_intent_preview(payload: MobileIntentPreviewRequest) -> dict:
        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="text must be non-empty")
        preview = MobileIntentPreview.from_text(
            text,
            policy_engine=app.state.policy_engine,
        )
        return preview.to_dict()

    @app.post("/missions")
    def create_mission() -> dict:
        mission = app.state.mission_control.create_mission()
        return asdict(mission)

    @app.get("/missions")
    def list_missions() -> list[dict]:
        return [asdict(m) for m in app.state.mission_control.list_missions()]

    @app.get("/missions/{mission_id}")
    def get_mission(mission_id: str) -> dict:
        try:
            mission = app.state.mission_control.get_mission(mission_id)
            steps = app.state.mission_control.store.list_steps(mission_id)
            return {**asdict(mission), "steps": [asdict(s) for s in steps]}
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/missions/{mission_id}/steps")
    def add_mission_step(mission_id: str, payload: CreateMissionStepRequest) -> dict:
        prompt = payload.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt must be non-empty")
        try:
            step = app.state.mission_control.add_step(mission_id, prompt)
            mission = app.state.mission_control.get_mission(mission_id)
            return {"mission": asdict(mission), "step": asdict(step)}
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/missions/{mission_id}/cancel")
    def cancel_mission(mission_id: str) -> dict:
        try:
            mission = app.state.mission_control.cancel_mission(mission_id)
            return asdict(mission)
        except KeyError:
            raise HTTPException(status_code=404, detail="mission not found")

    @app.post("/tasks")
    def create_task(payload: CreateTaskRequest) -> dict:
        prompt = payload.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt must be non-empty")

        task = app.state.task_store.create(prompt=prompt)
        decision = app.state.policy_engine.classify_action(prompt)

        if decision.decision == PolicyDecision.DENIED:
            task.status = "failed"
            task.error = f"denied: {decision.reason}"
            app.state.task_store.update(task)
            return asdict(task)

        if decision.decision == PolicyDecision.REQUIRES_APPROVAL:
            approval = app.state.approval_gateway.create_request(
                action=prompt,
                rationale="Prompt requires human approval before execution.",
            )
            task.status = "pending_approval"
            task.error = "requires_approval"
            task.approval_request_id = approval.request_id
            app.state.task_store.update(task)
            return asdict(task)

        task.status = "running"
        app.state.task_store.update(task)

        try:
            adapter = app.state.adapter_factory()
            result = adapter.run(prompt, task_id=task.task_id)
            task.status = "completed"
            task.result = result
            task.error = None
        except Exception as exc:
            task.status = "failed"
            task.error = f"execution_error: {type(exc).__name__}: {exc}"

        app.state.task_store.update(task)
        return asdict(task)

    @app.get("/tasks/{task_id}")
    def get_task(task_id: str) -> dict:
        try:
            task = app.state.task_store.get(task_id)
            return asdict(task)
        except KeyError:
            raise HTTPException(status_code=404, detail="task not found")

    @app.get("/tasks")
    def list_tasks() -> list[dict]:
        return [asdict(task) for task in app.state.task_store.list()]

    @app.post("/voice/tts", response_model=VoiceTTSResponse)
    def voice_tts(payload: VoiceTTSRequest) -> VoiceTTSResponse:
        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="text must be non-empty")
        if not payload.language or not payload.language.strip():
            raise HTTPException(status_code=400, detail="language must be non-empty")

        decision = app.state.policy_engine.classify_action(text)
        if decision.decision == PolicyDecision.DENIED:
            raise HTTPException(status_code=403, detail=f"voice_tts denied: {decision.reason}")
        if decision.decision == PolicyDecision.REQUIRES_APPROVAL:
            approval = app.state.approval_gateway.create_request(
                action=text,
                rationale="Voice TTS request requires human approval before synthesis.",
            )
            return VoiceTTSResponse(
                provider="mock",
                content_type="application/json",
                has_audio_bytes=False,
                metadata={"policy_reason": decision.reason},
                status="pending_approval",
                approval_request_id=approval.request_id,
            )

        try:
            request = VoiceSynthesisRequest(
                text=text,
                voice_id=payload.voice_id,
                language=payload.language.strip(),
                output_format=payload.output_format,
                metadata=payload.metadata or {},
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        try:
            result = app.state.voice_adapter.synthesize(request)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception:
            raise HTTPException(status_code=502, detail="voice synthesis failed")

        audio_path = str(result.audio_path) if result.audio_path else None
        if payload.save_audio and result.audio_bytes is not None:
            audio_path = app.state.voice_audio_storage.save_audio(result.audio_bytes, request.output_format)

        return VoiceTTSResponse(
            provider=result.provider,
            content_type=result.content_type,
            audio_path=audio_path,
            has_audio_bytes=result.audio_bytes is not None,
            duration_seconds=result.duration_seconds,
            metadata=_sanitize_voice_metadata(result.metadata),
        )

    @app.get("/voice/status")
    def voice_status() -> dict:
        adapter = app.state.voice_adapter

        if isinstance(adapter, MockVoiceAdapter):
            return {
                "provider": "mock",
                "configured": True,
                "can_synthesize": True,
                "details": {},
            }

        if isinstance(adapter, GPTSoVITSAdapter):
            has_base_url = bool(adapter.base_url and adapter.base_url.strip())
            has_ref_audio_path = bool(adapter.ref_audio_path and str(adapter.ref_audio_path).strip())
            has_prompt_text = bool(adapter.prompt_text and str(adapter.prompt_text).strip())
            return {
                "provider": "gpt-sovits",
                "configured": has_base_url,
                "can_synthesize": has_base_url and has_ref_audio_path,
                "details": {
                    "base_url": adapter.base_url,
                    "has_ref_audio_path": has_ref_audio_path,
                    "has_prompt_text": has_prompt_text,
                    "prompt_lang": adapter.prompt_lang,
                    "timeout_seconds": adapter.timeout_seconds,
                },
            }

        return {
            "provider": "unknown",
            "configured": False,
            "can_synthesize": False,
            "details": {"class_name": adapter.__class__.__name__},
        }

    @app.get("/voice/companion/status")
    def voice_companion_status() -> dict:
        return VoiceCompanionStatus.placeholder().to_dict()

    @app.get("/voice/companion/control-policy")
    def voice_companion_control_policy() -> dict:
        return VoiceCompanionControlPolicy.placeholder().to_dict()

    @app.post("/voice/companion/preview")
    def voice_companion_preview(payload: VoiceCompanionPreviewRequest) -> dict:
        text = payload.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="text must be non-empty")
        preview = VoiceCompanionIntentPreview.from_text(
            text,
            policy_engine=app.state.policy_engine,
        )
        return preview.to_dict()

    @app.get("/voice/runtime/status")
    def voice_runtime_status() -> dict:
        return _voice_runtime_state_payload(app.state.voice_runtime.status())

    @app.post("/voice/runtime/start")
    def voice_runtime_start() -> dict:
        return _voice_runtime_state_payload(app.state.voice_runtime.start())

    @app.post("/voice/runtime/stop")
    def voice_runtime_stop() -> dict:
        return _voice_runtime_state_payload(app.state.voice_runtime.stop())

    @app.post("/voice/runtime/mode")
    def voice_runtime_set_mode(payload: VoiceRuntimeModeRequest) -> dict:
        try:
            state = app.state.voice_runtime.set_mode(payload.mode)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return _voice_runtime_state_payload(state)

    @app.post("/voice/runtime/control")
    def voice_runtime_control(payload: VoiceRuntimeTextRequest) -> dict:
        result = app.state.voice_runtime.handle_control_phrase(payload.text)
        return {
            "recognized": result["handled"],
            "result": result,
            "state": _voice_runtime_state_payload(app.state.voice_runtime.status()),
        }

    @app.post("/voice/runtime/transcript")
    def voice_runtime_transcript(payload: VoiceRuntimeTextRequest) -> dict:
        result = app.state.voice_runtime.handle_transcript(payload.text)
        return {
            "result": result,
            "state": _voice_runtime_state_payload(app.state.voice_runtime.status()),
        }

    @app.get("/voice/runtime/feedback")
    def voice_runtime_feedback_list() -> dict:
        feedback = [item.to_dict() for item in app.state.voice_runtime.list_feedback()]
        return {
            "feedback": feedback,
            "feedback_count": len(feedback),
        }

    @app.post("/voice/runtime/feedback")
    def voice_runtime_feedback_add(payload: VoiceRuntimeFeedbackRequest) -> dict:
        original_text = payload.original_text.strip()
        corrected_intent = payload.corrected_intent.strip()
        if not original_text:
            raise HTTPException(status_code=400, detail="original_text must be non-empty")
        if not corrected_intent:
            raise HTTPException(status_code=400, detail="corrected_intent must be non-empty")

        feedback = app.state.voice_runtime.add_feedback(
            original_text=original_text,
            interpreted_intent=payload.interpreted_intent,
            corrected_intent=corrected_intent,
            correction_note=payload.correction_note,
            preferred_next_step=payload.preferred_next_step,
            confidence_before=payload.confidence_before,
        )
        return {
            "feedback": feedback.to_dict(),
            "feedback_count": app.state.voice_runtime.status().feedback_count,
            "applied_persistently": feedback.applied_persistently,
        }

    @app.post("/voice/runtime/feedback/preview")
    def voice_runtime_feedback_preview(payload: VoiceRuntimeFeedbackPreviewRequest) -> dict:
        original_text = (payload.original_text or "").strip()
        corrected_intent = (payload.corrected_intent or "").strip()
        if not original_text:
            raise HTTPException(status_code=400, detail="original_text must be non-empty")
        if not corrected_intent:
            raise HTTPException(status_code=400, detail="corrected_intent must be non-empty")

        feedback = UserUnderstandingFeedback(
            original_text=original_text,
            interpreted_intent=payload.interpreted_intent,
            corrected_intent=corrected_intent,
            correction_note=payload.correction_note,
            preferred_next_step=payload.preferred_next_step,
            confidence_before=payload.confidence_before,
            applied_persistently=False,
            requires_review=True,
        )
        preview = preview_user_understanding_feedback(feedback).to_dict()
        return {
            "preview": preview,
            "applied": preview["applied"],
            "requires_review": preview["requires_review"],
            "feedback_count": app.state.voice_runtime.status().feedback_count,
        }

    @app.post("/voice/runtime/feedback/apply-reviewed")
    def voice_runtime_feedback_apply_reviewed(payload: VoiceRuntimeFeedbackRequest) -> dict:
        original_text = payload.original_text.strip()
        corrected_intent = payload.corrected_intent.strip()
        if not original_text:
            raise HTTPException(status_code=400, detail="original_text must be non-empty")
        if not corrected_intent:
            raise HTTPException(status_code=400, detail="corrected_intent must be non-empty")

        rule = app.state.voice_runtime.apply_reviewed_feedback(
            original_text=original_text,
            interpreted_intent=payload.interpreted_intent,
            corrected_intent=corrected_intent,
            correction_note=payload.correction_note,
            preferred_next_step=payload.preferred_next_step,
            confidence_before=payload.confidence_before,
        )
        return {
            "applied_rule": rule.to_dict(),
            "applied_feedback_count": app.state.voice_runtime.status().applied_feedback_count,
            "applied_persistently": False,
        }

    @app.get("/voice/runtime/feedback/applied")
    def voice_runtime_feedback_applied_list() -> dict:
        rules = [rule.to_dict() for rule in app.state.voice_runtime.list_applied_feedback()]
        return {
            "applied_rules": rules,
            "applied_feedback_count": len(rules),
            "applied_persistently": False,
        }

    @app.delete("/voice/runtime/feedback/applied")
    def voice_runtime_feedback_applied_clear() -> dict:
        app.state.voice_runtime.clear_applied_feedback()
        return {
            "applied_feedback_count": app.state.voice_runtime.status().applied_feedback_count,
            "applied_persistently": False,
        }

    @app.delete("/voice/runtime/feedback")
    def voice_runtime_feedback_clear() -> dict:
        app.state.voice_runtime.clear_feedback()
        return {"feedback_count": app.state.voice_runtime.status().feedback_count}

    @app.get("/voice/runtime/memory/proposals")
    def voice_runtime_memory_proposals_list() -> dict:
        proposals = [proposal.to_dict() for proposal in app.state.voice_runtime.list_memory_proposals()]
        return {
            "proposals": proposals,
            "memory_proposal_count": len(proposals),
        }

    @app.post("/voice/runtime/memory/proposals/from-applied-feedback")
    def voice_runtime_memory_proposal_from_applied_feedback(
        payload: VoiceRuntimeMemoryProposalFromAppliedFeedbackRequest,
    ) -> dict:
        original_text = payload.original_text.strip()
        corrected_intent = payload.corrected_intent.strip()
        if not original_text:
            raise HTTPException(status_code=400, detail="original_text must be non-empty")
        if not corrected_intent:
            raise HTTPException(status_code=400, detail="corrected_intent must be non-empty")

        rule = UserUnderstandingAppliedFeedbackRule(
            original_text=original_text,
            corrected_intent=corrected_intent,
            suggested_alias=(payload.suggested_alias or "").strip() or None,
            reason=(payload.reason or "").strip(),
            source=(payload.source or "user_reviewed_feedback").strip() or "user_reviewed_feedback",
            applied_persistently=payload.applied_persistently,
            requires_review=False,
            approval_required=False,
        )
        proposal = app.state.voice_runtime.propose_memory_from_applied_feedback(rule)
        return {
            "proposal": proposal.to_dict(),
            "memory_proposal_count": app.state.voice_runtime.status().memory_proposal_count,
            "applied_persistently": False,
        }

    @app.delete("/voice/runtime/memory/proposals")
    def voice_runtime_memory_proposals_clear() -> dict:
        app.state.voice_runtime.clear_memory_proposals()
        return {
            "memory_proposal_count": app.state.voice_runtime.status().memory_proposal_count,
        }

    @app.get("/voice/runtime/memory/active")
    def voice_runtime_memory_active_list() -> dict:
        active_rules = [
            rule.to_dict()
            for rule in app.state.voice_runtime.list_active_memory_rules()
        ]
        return {
            "active_rules": active_rules,
            "active_memory_rule_count": len(active_rules),
            "applied_to_runtime": True,
        }

    @app.delete("/voice/runtime/memory/active")
    def voice_runtime_memory_active_clear() -> dict:
        app.state.voice_runtime.clear_active_memory_rules()
        return {
            "active_memory_rule_count": app.state.voice_runtime.status().active_memory_rule_count,
            "applied_to_runtime": True,
        }

    @app.get("/voice/runtime/memory/snapshot")
    def voice_runtime_memory_snapshot() -> dict:
        return {
            "snapshot": app.state.voice_runtime.export_memory_snapshot().to_dict(),
            "persisted": False,
        }

    @app.post("/voice/runtime/memory/snapshot/import")
    def voice_runtime_memory_snapshot_import(
        payload: VoiceRuntimeMemorySnapshotImportRequest,
    ) -> dict:
        if payload.path is not None or payload.file is not None:
            raise HTTPException(status_code=400, detail="path/file inputs are not accepted")
        if payload.snapshot is None:
            raise HTTPException(status_code=400, detail="snapshot is required")

        try:
            imported_count = app.state.voice_runtime.import_memory_snapshot(
                payload.snapshot,
                replace=payload.replace,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "imported_count": imported_count,
            "memory_proposal_count": app.state.voice_runtime.status().memory_proposal_count,
            "persisted": False,
            "applied_to_runtime": False,
        }

    @app.post("/voice/runtime/memory/local/save")
    def voice_runtime_memory_local_save(
        payload: Optional[VoiceRuntimeMemoryLocalSaveRequest] = None,
    ) -> dict:
        base_dir = payload.base_dir if payload else None
        create_backup = payload.create_backup if payload else True
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.save_memory_snapshot_local(
                base_dir=base_dir,
                create_backup=create_backup,
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "persisted": True,
            "applied_to_runtime": False,
        }

    @app.post("/voice/runtime/memory/local/load")
    def voice_runtime_memory_local_load(
        payload: Optional[VoiceRuntimeMemoryLocalLoadRequest] = None,
    ) -> dict:
        if payload and (payload.path is not None or payload.file is not None):
            raise HTTPException(status_code=400, detail="path/file inputs are not accepted")
        base_dir = payload.base_dir if payload else None
        replace = True if payload is None or payload.replace is None else payload.replace
        if not isinstance(replace, bool):
            raise HTTPException(status_code=400, detail="replace must be boolean")
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.load_memory_snapshot_local(
                base_dir=base_dir,
                replace=replace,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "persisted_source": result["persisted_source"],
            "applied_to_runtime": False,
        }

    @app.get("/voice/runtime/memory/local/status")
    def voice_runtime_memory_local_status(base_dir: Optional[str] = None) -> dict:
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.get_memory_local_status(base_dir=base_dir)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "applied_to_runtime": False,
        }

    @app.post("/voice/runtime/memory/local/backup")
    def voice_runtime_memory_local_backup(
        payload: Optional[VoiceRuntimeMemoryLocalBackupRequest] = None,
    ) -> dict:
        if payload and (payload.path is not None or payload.file is not None):
            raise HTTPException(status_code=400, detail="path/file inputs are not accepted")
        base_dir = payload.base_dir if payload else None
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.backup_memory_snapshot_local(base_dir=base_dir)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "applied_to_runtime": False,
        }

    @app.delete("/voice/runtime/memory/local")
    def voice_runtime_memory_local_delete(
        payload: Optional[VoiceRuntimeMemoryLocalDeleteRequest] = None,
    ) -> dict:
        if payload and (payload.path is not None or payload.file is not None):
            raise HTTPException(status_code=400, detail="path/file inputs are not accepted")
        base_dir = payload.base_dir if payload else None
        include_backups = True if payload is None or payload.include_backups is None else payload.include_backups
        if not isinstance(include_backups, bool):
            raise HTTPException(status_code=400, detail="include_backups must be boolean")
        if base_dir is not None:
            if "\0" in base_dir:
                raise HTTPException(status_code=400, detail="base_dir must not contain null bytes")
            if not base_dir.strip():
                raise HTTPException(status_code=400, detail="base_dir must not be empty")

        try:
            result = app.state.voice_runtime.delete_memory_local(
                base_dir=base_dir,
                include_backups=include_backups,
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "result": result,
            "applied_to_runtime": False,
        }

    @app.get("/voice/runtime/memory/proposals/{proposal_id}")
    def voice_runtime_memory_proposal_get(proposal_id: str) -> dict:
        try:
            proposal = app.state.voice_runtime.get_memory_proposal(proposal_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        return {"proposal": proposal.to_dict()}

    @app.post("/voice/runtime/memory/proposals/{proposal_id}/review")
    def voice_runtime_memory_proposal_review(proposal_id: str) -> dict:
        try:
            proposal = app.state.voice_runtime.review_memory_proposal(proposal_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        return {"proposal": proposal.to_dict()}

    @app.post("/voice/runtime/memory/proposals/{proposal_id}/approve")
    def voice_runtime_memory_proposal_approve(
        proposal_id: str,
        payload: Optional[VoiceRuntimeMemoryProposalApproveRequest] = None,
    ) -> dict:
        try:
            proposal = app.state.voice_runtime.approve_memory_proposal(
                proposal_id,
                approved_by=(payload.approved_by or "David") if payload else "David",
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"proposal": proposal.to_dict()}

    @app.post("/voice/runtime/memory/proposals/{proposal_id}/activate")
    def voice_runtime_memory_proposal_activate(
        proposal_id: str,
        payload: Optional[VoiceRuntimeMemoryProposalActivateRequest] = None,
    ) -> dict:
        try:
            rule = app.state.voice_runtime.activate_memory_proposal(
                proposal_id,
                activated_by=(payload.activated_by or "David") if payload else "David",
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {
            "active_rule": rule.to_dict(),
            "active_memory_rule_count": app.state.voice_runtime.status().active_memory_rule_count,
            "applied_to_runtime": True,
            "persisted": False,
        }

    @app.post("/voice/runtime/memory/active/{proposal_id}/deactivate")
    def voice_runtime_memory_active_deactivate(
        proposal_id: str,
        payload: Optional[VoiceRuntimeMemoryRuleDeactivateRequest] = None,
    ) -> dict:
        try:
            rule = app.state.voice_runtime.deactivate_memory_rule(
                proposal_id,
                reason=(payload.reason or "") if payload else "",
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="active memory rule not found")
        return {
            "active_rule": rule.to_dict(),
            "active_memory_rule_count": app.state.voice_runtime.status().active_memory_rule_count,
            "applied_to_runtime": True,
            "persisted": False,
        }

    @app.post("/voice/runtime/memory/proposals/{proposal_id}/disable")
    def voice_runtime_memory_proposal_disable(
        proposal_id: str,
        payload: Optional[VoiceRuntimeMemoryProposalDisableRequest] = None,
    ) -> dict:
        try:
            proposal = app.state.voice_runtime.disable_memory_proposal(
                proposal_id,
                reason=(payload.reason or "") if payload else "",
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        return {"proposal": proposal.to_dict()}

    @app.delete("/voice/runtime/memory/proposals/{proposal_id}")
    def voice_runtime_memory_proposal_delete(proposal_id: str) -> dict:
        try:
            proposal = app.state.voice_runtime.delete_memory_proposal(proposal_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="memory proposal not found")
        return {"proposal": proposal.to_dict()}

    @app.post("/tasks/{task_id}/cancel", response_model=CancelTaskResponse)
    def cancel_task(task_id: str) -> CancelTaskResponse:
        try:
            task = app.state.task_store.get(task_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="task not found")

        if task.status in {"completed", "failed", "cancelled"}:
            return CancelTaskResponse(task_id=task.task_id, status=task.status)

        task.status = "cancelled"
        app.state.task_store.update(task)
        return CancelTaskResponse(task_id=task.task_id, status=task.status)

    return app


app = create_app()
