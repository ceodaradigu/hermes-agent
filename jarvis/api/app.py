from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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
from jarvis.ambient_vision.companion import (
    AmbientVisionPrivacyPolicy,
    AmbientVisionSessionPreview,
    AmbientVisionStatus,
    AmbientVisionStopControl,
)
from jarvis.command_center import build_command_center_view_model
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
    build_operator_console_snapshot,
)
from jarvis.policy.approval_gateway import ApprovalGateway
from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine
from jarvis.runtime.hermes_adapter import HermesRuntimeAdapter
from jarvis.sandbox_execution.foundation import (
    SandboxAuditPreview,
    SandboxCommandPlan,
    SandboxDryRunResult,
    SandboxExecutionPolicy,
    SandboxExecutionStatus,
    SandboxRollbackPreview,
)
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


class MobileIntentPreviewRequest(BaseModel):
    text: str


class OperatorConsolePreviewRequest(BaseModel):
    text: str


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
    task_store: Optional[InMemoryTaskStore] = None,
    voice_adapter: Optional[VoiceAdapter] = None,
    voice_audio_storage: Optional[VoiceAudioStorage] = None,
    voice_runtime: Optional[VoiceRuntime] = None,
) -> FastAPI:
    app = FastAPI(title="JARVIS Gateway API", version="0.1.0")

    app.state.policy_engine = policy_engine or PolicyEngine()
    app.state.approval_gateway = approval_gateway or ApprovalGateway()
    app.state.adapter_factory = adapter_factory or (lambda: HermesRuntimeAdapter())
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

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

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
            },
        )
        return view.to_dict()

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
