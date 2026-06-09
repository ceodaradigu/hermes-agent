from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from jarvis.ambient_vision.companion import (
    AmbientVisionPrivacyPolicy,
    AmbientVisionStatus,
    AmbientVisionStopControl,
)
from jarvis.asset_factory.foundation import AssetFactoryStatus, AssetGenerationPolicy
from jarvis.command_center import CommandCenterViewModel, build_command_center_view_model
from jarvis.deploy_publishing.foundation import (
    DeployPublishingPolicy,
    DeployPublishingStatus,
    PublishingReadinessChecklist,
)
from jarvis.mobile.companion import (
    MobileCommandCenterSnapshot,
    MobileCompanionPermissionPolicy,
    MobileCompanionStatus,
    MobileIntentPreview,
)
from jarvis.marketing_distribution.foundation import (
    LaunchChecklistPreview,
    MarketingDistributionPolicy,
    MarketingDistributionStatus,
)
from jarvis.multidevice.runtime import DeviceRegistrySnapshot, MultiDeviceRuntimeStatus
from jarvis.payments_revenue.foundation import (
    FinancialRiskGuardPreview,
    PaymentsRevenuePolicy,
    PaymentsRevenueStatus,
)
from jarvis.policy.policy_engine import PolicyEngine
from jarvis.sandbox_execution.foundation import SandboxExecutionStatus
from jarvis.tool_adoption.pipeline import ToolAdoptionStatus
from jarvis.voice.companion import (
    VoiceCompanionControlPolicy,
    VoiceCompanionIntentPreview,
    VoiceCompanionStatus,
)


_OPERATOR_PREVIEW_REASON = "Operator Console preview is prepare-only; no execution, approval, Hermes, or persistence path is enabled."
_REDACTED_OPERATOR_INPUT = "[redacted sensitive operator input]"
_REDACTED_OPERATOR_WARNING = "[redacted sensitive operator warning]"
_SENSITIVE_MARKERS = (
    ".env",
    "api key",
    "api-key",
    "api_key",
    "apikey",
    "authorization",
    "banco",
    "bearer",
    "bearer token",
    "bearer-token",
    "bearer_token",
    "clave",
    "client secret",
    "client-secret",
    "client_secret",
    "contraseña",
    "contrasena",
    "credencial",
    "credenciales",
    "credential",
    "credentials",
    "dni",
    "password",
    "private key",
    "private-key",
    "private_key",
    "secret",
    "secreto",
    "tarjeta",
    "token",
)


@dataclass(frozen=True)
class OperatorConsoleStatus:
    prepare_only: bool = True
    operator_console_available: bool = True
    frontend_available: bool = False
    websocket_enabled: bool = False
    execution_enabled: bool = False
    approval_actions_enabled: bool = False
    hermes_connected: bool = False
    approval_gateway_called: bool = False
    secrets_access_enabled: bool = False
    external_calls_enabled: bool = False
    safe_read_only_mode: bool = True

    @classmethod
    def placeholder(cls) -> "OperatorConsoleStatus":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "OperatorConsoleStatus":
        return cls()

    def to_dict(self) -> Dict[str, bool]:
        return {
            "prepare_only": True,
            "operator_console_available": True,
            "frontend_available": False,
            "websocket_enabled": False,
            "execution_enabled": False,
            "approval_actions_enabled": False,
            "hermes_connected": False,
            "approval_gateway_called": False,
            "secrets_access_enabled": False,
            "external_calls_enabled": False,
            "safe_read_only_mode": True,
        }


@dataclass(frozen=True)
class OperatorConsoleCapabilityMatrix:
    prepare_only: bool = True
    read_command_center: bool = True
    read_voice_status: bool = True
    read_mobile_status: bool = True
    preview_voice_intent: bool = True
    preview_mobile_intent: bool = True
    inspect_safety: bool = True
    inspect_capabilities: bool = True
    read_ambient_vision_status: bool = True
    read_ambient_vision_privacy_policy: bool = True
    read_ambient_vision_stop_control: bool = True
    read_multi_device_status: bool = True
    read_device_registry: bool = True
    read_sandbox_execution_status: bool = True
    read_sandbox_execution_policy: bool = True
    preview_sandbox_dry_run: bool = True
    read_tool_adoption_status: bool = True
    preview_tool_adoption: bool = True
    read_asset_factory_status: bool = True
    read_asset_generation_policy: bool = True
    preview_asset_factory: bool = True
    read_deploy_publishing_status: bool = True
    read_deploy_publishing_policy: bool = True
    preview_deploy_publishing: bool = True
    read_marketing_distribution_status: bool = True
    read_marketing_distribution_policy: bool = True
    preview_marketing_distribution: bool = True
    read_payments_revenue_status: bool = True
    read_payments_revenue_policy: bool = True
    preview_payments_revenue: bool = True
    execute_mission: bool = False
    approve: bool = False
    reject: bool = False
    call_hermes: bool = False
    create_approval: bool = False
    read_secrets: bool = False
    use_microphone: bool = False
    use_camera: bool = False
    use_location: bool = False
    send_push: bool = False
    run_background: bool = False
    deploy: bool = False
    spend_money: bool = False

    @classmethod
    def placeholder(cls) -> "OperatorConsoleCapabilityMatrix":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "OperatorConsoleCapabilityMatrix":
        return cls()

    def to_dict(self) -> Dict[str, bool]:
        return {
            "prepare_only": True,
            "read_command_center": True,
            "read_voice_status": True,
            "read_mobile_status": True,
            "preview_voice_intent": True,
            "preview_mobile_intent": True,
            "inspect_safety": True,
            "inspect_capabilities": True,
            "read_ambient_vision_status": True,
            "read_ambient_vision_privacy_policy": True,
            "read_ambient_vision_stop_control": True,
            "read_multi_device_status": True,
            "read_device_registry": True,
            "read_sandbox_execution_status": True,
            "read_sandbox_execution_policy": True,
            "preview_sandbox_dry_run": True,
            "read_tool_adoption_status": True,
            "preview_tool_adoption": True,
            "read_asset_factory_status": True,
            "read_asset_generation_policy": True,
            "preview_asset_factory": True,
            "read_deploy_publishing_status": True,
            "read_deploy_publishing_policy": True,
            "preview_deploy_publishing": True,
            "read_marketing_distribution_status": True,
            "read_marketing_distribution_policy": True,
            "preview_marketing_distribution": True,
            "read_payments_revenue_status": True,
            "read_payments_revenue_policy": True,
            "preview_payments_revenue": True,
            "execute_mission": False,
            "approve": False,
            "reject": False,
            "call_hermes": False,
            "create_approval": False,
            "read_secrets": False,
            "use_microphone": False,
            "use_camera": False,
            "use_location": False,
            "send_push": False,
            "run_background": False,
            "deploy": False,
            "spend_money": False,
        }


@dataclass(frozen=True)
class OperatorSafetySummary:
    prepare_only: bool = True
    all_execution_disabled: bool = True
    all_approval_actions_disabled: bool = True
    hermes_calls_disabled: bool = True
    approval_gateway_calls_disabled: bool = True
    secrets_access_disabled: bool = True
    external_calls_disabled: bool = True
    sensitive_boundaries_enforced: bool = True
    redaction_enabled: bool = True
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def placeholder(cls) -> "OperatorSafetySummary":
        return cls()

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "OperatorSafetySummary":
        source = dict(data or {})
        return cls(warnings=[_safe_warning(item) for item in source.get("warnings", []) or [] if _safe_text(item)])

    def __post_init__(self) -> None:
        object.__setattr__(self, "warnings", [_safe_warning(item) for item in self.warnings if _safe_text(item)])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "all_execution_disabled": True,
            "all_approval_actions_disabled": True,
            "hermes_calls_disabled": True,
            "approval_gateway_calls_disabled": True,
            "secrets_access_disabled": True,
            "external_calls_disabled": True,
            "sensitive_boundaries_enforced": True,
            "redaction_enabled": True,
            "warnings": [_safe_warning(item) for item in self.warnings if _safe_text(item)],
        }


@dataclass(frozen=True)
class OperatorConsolePreview:
    prepare_only: bool = True
    input_text: str = ""
    voice_preview: VoiceCompanionIntentPreview = field(default_factory=VoiceCompanionIntentPreview.placeholder)
    mobile_preview: MobileIntentPreview = field(default_factory=MobileIntentPreview.placeholder)
    policy_decision: str = "unknown"
    sensitive_boundary_triggered: bool = False
    would_execute: bool = False
    execution_enabled: bool = False
    approval_created: bool = False
    approval_gateway_called: bool = False
    hermes_called: bool = False
    mission_created: bool = False
    task_created: bool = False
    persisted: bool = False
    reason: str = _OPERATOR_PREVIEW_REASON
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        sensitive = bool(self.sensitive_boundary_triggered or _contains_sensitive_marker(self.input_text))
        object.__setattr__(self, "prepare_only", True)
        if isinstance(self.voice_preview, dict):
            object.__setattr__(self, "voice_preview", VoiceCompanionIntentPreview.from_dict(self.voice_preview))
        if isinstance(self.mobile_preview, dict):
            object.__setattr__(self, "mobile_preview", MobileIntentPreview.from_dict(self.mobile_preview))
        voice_data = self.voice_preview.to_dict()
        mobile_data = self.mobile_preview.to_dict()
        nested_sensitive = bool(
            voice_data.get("sensitive_boundary_triggered", False)
            or mobile_data.get("sensitive_boundary_triggered", False)
        )
        final_sensitive = bool(sensitive or nested_sensitive)
        object.__setattr__(self, "input_text", _sanitize_input(self.input_text, sensitive=final_sensitive))
        decision = _combine_policy_decisions(
            str(voice_data.get("policy_decision", "unknown")),
            str(mobile_data.get("policy_decision", "unknown")),
            sensitive=final_sensitive,
        )
        object.__setattr__(self, "policy_decision", decision)
        object.__setattr__(self, "sensitive_boundary_triggered", final_sensitive)
        object.__setattr__(self, "would_execute", False)
        object.__setattr__(self, "execution_enabled", False)
        object.__setattr__(self, "approval_created", False)
        object.__setattr__(self, "approval_gateway_called", False)
        object.__setattr__(self, "hermes_called", False)
        object.__setattr__(self, "mission_created", False)
        object.__setattr__(self, "task_created", False)
        object.__setattr__(self, "persisted", False)
        object.__setattr__(self, "reason", _safe_reason(self.reason))
        object.__setattr__(self, "warnings", [_safe_reason(item) for item in self.warnings])

    @classmethod
    def placeholder(cls) -> "OperatorConsolePreview":
        return cls()

    @classmethod
    def from_text(cls, text: str, *, policy_engine: Optional[PolicyEngine] = None) -> "OperatorConsolePreview":
        raw_text = str(text or "").strip()
        sensitive = _contains_sensitive_marker(raw_text)
        voice_preview = VoiceCompanionIntentPreview.from_text(raw_text, policy_engine=policy_engine)
        if sensitive and not voice_preview.sensitive_boundary_triggered:
            voice_preview = VoiceCompanionIntentPreview.from_dict(
                {
                    "input_text": raw_text,
                    "intent": "requires_approval",
                    "policy_decision": "requires_approval",
                    "sensitive_boundary_triggered": True,
                    "redact_input_text": True,
                    "reason": "Sensitive operator boundary detected; transcript redacted and execution remains disabled.",
                    "warnings": ["Sensitive operator boundary detected; transcript redacted and execution remains disabled."],
                }
            )
        mobile_preview = MobileIntentPreview.from_voice_preview(voice_preview)
        warnings = []
        if sensitive or voice_preview.sensitive_boundary_triggered or mobile_preview.sensitive_boundary_triggered:
            warnings.append("Sensitive boundary detected; operator input redacted and execution remains disabled.")
        return cls(
            input_text=raw_text,
            voice_preview=voice_preview,
            mobile_preview=mobile_preview,
            sensitive_boundary_triggered=sensitive,
            reason=_OPERATOR_PREVIEW_REASON,
            warnings=warnings,
        )

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "OperatorConsolePreview":
        source = dict(data or {})
        return cls(
            input_text=str(source.get("input_text", "")),
            voice_preview=VoiceCompanionIntentPreview.from_dict(source.get("voice_preview")),
            mobile_preview=MobileIntentPreview.from_dict(source.get("mobile_preview")),
            sensitive_boundary_triggered=bool(source.get("sensitive_boundary_triggered", False)),
            reason=str(source.get("reason", _OPERATOR_PREVIEW_REASON)),
            warnings=[str(item) for item in source.get("warnings", []) or []],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "input_text": self.input_text,
            "voice_preview": self.voice_preview.to_dict(),
            "mobile_preview": self.mobile_preview.to_dict(),
            "policy_decision": self.policy_decision,
            "sensitive_boundary_triggered": self.sensitive_boundary_triggered,
            "would_execute": False,
            "execution_enabled": False,
            "approval_created": False,
            "approval_gateway_called": False,
            "hermes_called": False,
            "mission_created": False,
            "task_created": False,
            "persisted": False,
            "reason": self.reason,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class OperatorConsoleSnapshot:
    prepare_only: bool = True
    status: OperatorConsoleStatus = field(default_factory=OperatorConsoleStatus.placeholder)
    command_center: CommandCenterViewModel = field(
        default_factory=lambda: build_operator_command_center_view(
            view_id="operator-command-center-placeholder",
            generated_at="1970-01-01T00:00:00+00:00",
        )
    )
    voice_status: VoiceCompanionStatus = field(default_factory=VoiceCompanionStatus.placeholder)
    voice_control_policy: VoiceCompanionControlPolicy = field(default_factory=VoiceCompanionControlPolicy.placeholder)
    mobile_status: MobileCompanionStatus = field(default_factory=MobileCompanionStatus.placeholder)
    mobile_permission_policy: MobileCompanionPermissionPolicy = field(
        default_factory=MobileCompanionPermissionPolicy.placeholder
    )
    mobile_command_center: MobileCommandCenterSnapshot = field(default_factory=MobileCommandCenterSnapshot.placeholder)
    ambient_vision_status: AmbientVisionStatus = field(default_factory=AmbientVisionStatus.placeholder)
    ambient_vision_privacy_policy: AmbientVisionPrivacyPolicy = field(default_factory=AmbientVisionPrivacyPolicy.placeholder)
    ambient_vision_stop_control: AmbientVisionStopControl = field(default_factory=AmbientVisionStopControl.placeholder)
    multi_device_runtime_status: MultiDeviceRuntimeStatus = field(default_factory=MultiDeviceRuntimeStatus.placeholder)
    device_registry: DeviceRegistrySnapshot = field(default_factory=DeviceRegistrySnapshot.placeholder)
    sandbox_execution_status: SandboxExecutionStatus = field(default_factory=SandboxExecutionStatus.placeholder)
    tool_adoption_status: ToolAdoptionStatus = field(default_factory=ToolAdoptionStatus.placeholder)
    asset_factory_status: AssetFactoryStatus = field(default_factory=AssetFactoryStatus.placeholder)
    asset_generation_policy: AssetGenerationPolicy = field(default_factory=AssetGenerationPolicy.placeholder)
    deploy_publishing_status: DeployPublishingStatus = field(default_factory=DeployPublishingStatus.placeholder)
    deploy_publishing_policy: DeployPublishingPolicy = field(default_factory=DeployPublishingPolicy.placeholder)
    publishing_readiness: PublishingReadinessChecklist = field(default_factory=PublishingReadinessChecklist.placeholder)
    marketing_distribution_status: MarketingDistributionStatus = field(default_factory=MarketingDistributionStatus.placeholder)
    marketing_distribution_policy: MarketingDistributionPolicy = field(default_factory=MarketingDistributionPolicy.placeholder)
    marketing_launch_readiness: LaunchChecklistPreview = field(default_factory=LaunchChecklistPreview.placeholder)
    payments_revenue_status: PaymentsRevenueStatus = field(default_factory=PaymentsRevenueStatus.placeholder)
    payments_revenue_policy: PaymentsRevenuePolicy = field(default_factory=PaymentsRevenuePolicy.placeholder)
    financial_readiness: FinancialRiskGuardPreview = field(default_factory=FinancialRiskGuardPreview)
    capability_matrix: OperatorConsoleCapabilityMatrix = field(default_factory=OperatorConsoleCapabilityMatrix.placeholder)
    safety_summary: OperatorSafetySummary = field(default_factory=OperatorSafetySummary.placeholder)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "prepare_only", True)
        if isinstance(self.status, dict):
            object.__setattr__(self, "status", OperatorConsoleStatus.from_dict(self.status))
        if isinstance(self.command_center, dict):
            object.__setattr__(self, "command_center", _command_center_from_optional_dict(self.command_center))
        if isinstance(self.voice_status, dict):
            object.__setattr__(self, "voice_status", VoiceCompanionStatus.from_dict(self.voice_status))
        if isinstance(self.voice_control_policy, dict):
            object.__setattr__(
                self,
                "voice_control_policy",
                VoiceCompanionControlPolicy.from_dict(self.voice_control_policy),
            )
        if isinstance(self.mobile_status, dict):
            object.__setattr__(self, "mobile_status", MobileCompanionStatus.from_dict(self.mobile_status))
        if isinstance(self.mobile_permission_policy, dict):
            object.__setattr__(
                self,
                "mobile_permission_policy",
                MobileCompanionPermissionPolicy.from_dict(self.mobile_permission_policy),
            )
        if isinstance(self.mobile_command_center, dict):
            object.__setattr__(
                self,
                "mobile_command_center",
                MobileCommandCenterSnapshot.from_dict(self.mobile_command_center),
            )
        if isinstance(self.ambient_vision_status, dict):
            object.__setattr__(self, "ambient_vision_status", AmbientVisionStatus.from_dict(self.ambient_vision_status))
        if isinstance(self.ambient_vision_privacy_policy, dict):
            object.__setattr__(
                self,
                "ambient_vision_privacy_policy",
                AmbientVisionPrivacyPolicy.from_dict(self.ambient_vision_privacy_policy),
            )
        if isinstance(self.ambient_vision_stop_control, dict):
            object.__setattr__(
                self,
                "ambient_vision_stop_control",
                AmbientVisionStopControl.from_dict(self.ambient_vision_stop_control),
            )
        if isinstance(self.multi_device_runtime_status, dict):
            object.__setattr__(
                self,
                "multi_device_runtime_status",
                MultiDeviceRuntimeStatus.from_dict(self.multi_device_runtime_status),
            )
        if isinstance(self.device_registry, dict):
            object.__setattr__(self, "device_registry", DeviceRegistrySnapshot.from_dict(self.device_registry))
        if isinstance(self.sandbox_execution_status, dict):
            object.__setattr__(
                self,
                "sandbox_execution_status",
                SandboxExecutionStatus.from_dict(self.sandbox_execution_status),
            )
        if isinstance(self.tool_adoption_status, dict):
            object.__setattr__(
                self,
                "tool_adoption_status",
                ToolAdoptionStatus.from_dict(self.tool_adoption_status),
            )
        if isinstance(self.asset_factory_status, dict):
            object.__setattr__(self, "asset_factory_status", AssetFactoryStatus.from_dict(self.asset_factory_status))
        if isinstance(self.asset_generation_policy, dict):
            object.__setattr__(
                self,
                "asset_generation_policy",
                AssetGenerationPolicy.from_dict(self.asset_generation_policy),
            )
        if isinstance(self.deploy_publishing_status, dict):
            object.__setattr__(
                self,
                "deploy_publishing_status",
                DeployPublishingStatus.from_dict(self.deploy_publishing_status),
            )
        if isinstance(self.deploy_publishing_policy, dict):
            object.__setattr__(
                self,
                "deploy_publishing_policy",
                DeployPublishingPolicy.from_dict(self.deploy_publishing_policy),
            )
        if isinstance(self.publishing_readiness, dict):
            object.__setattr__(
                self,
                "publishing_readiness",
                PublishingReadinessChecklist.from_dict(self.publishing_readiness),
            )
        if isinstance(self.marketing_distribution_status, dict):
            object.__setattr__(
                self,
                "marketing_distribution_status",
                MarketingDistributionStatus.from_dict(self.marketing_distribution_status),
            )
        if isinstance(self.marketing_distribution_policy, dict):
            object.__setattr__(
                self,
                "marketing_distribution_policy",
                MarketingDistributionPolicy.from_dict(self.marketing_distribution_policy),
            )
        if isinstance(self.marketing_launch_readiness, dict):
            object.__setattr__(
                self,
                "marketing_launch_readiness",
                LaunchChecklistPreview.from_dict(self.marketing_launch_readiness),
            )
        if isinstance(self.payments_revenue_status, dict):
            object.__setattr__(
                self,
                "payments_revenue_status",
                PaymentsRevenueStatus.from_dict(self.payments_revenue_status),
            )
        if isinstance(self.payments_revenue_policy, dict):
            object.__setattr__(
                self,
                "payments_revenue_policy",
                PaymentsRevenuePolicy.from_dict(self.payments_revenue_policy),
            )
        if isinstance(self.financial_readiness, dict):
            object.__setattr__(
                self,
                "financial_readiness",
                FinancialRiskGuardPreview.from_dict(self.financial_readiness),
            )
        if isinstance(self.capability_matrix, dict):
            object.__setattr__(
                self,
                "capability_matrix",
                OperatorConsoleCapabilityMatrix.from_dict(self.capability_matrix),
            )
        if isinstance(self.safety_summary, dict):
            object.__setattr__(self, "safety_summary", OperatorSafetySummary.from_dict(self.safety_summary))
        object.__setattr__(self, "metadata", _safe_metadata(self.metadata))

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "OperatorConsoleSnapshot":
        source = dict(data or {})
        return cls(
            status=OperatorConsoleStatus.from_dict(source.get("status")),
            command_center=_command_center_from_optional_dict(source.get("command_center")),
            voice_status=VoiceCompanionStatus.from_dict(source.get("voice_status")),
            voice_control_policy=VoiceCompanionControlPolicy.from_dict(source.get("voice_control_policy")),
            mobile_status=MobileCompanionStatus.from_dict(source.get("mobile_status")),
            mobile_permission_policy=MobileCompanionPermissionPolicy.from_dict(source.get("mobile_permission_policy")),
            mobile_command_center=MobileCommandCenterSnapshot.from_dict(source.get("mobile_command_center")),
            ambient_vision_status=AmbientVisionStatus.from_dict(source.get("ambient_vision_status")),
            ambient_vision_privacy_policy=AmbientVisionPrivacyPolicy.from_dict(source.get("ambient_vision_privacy_policy")),
            ambient_vision_stop_control=AmbientVisionStopControl.from_dict(source.get("ambient_vision_stop_control")),
            multi_device_runtime_status=MultiDeviceRuntimeStatus.from_dict(source.get("multi_device_runtime_status")),
            device_registry=DeviceRegistrySnapshot.from_dict(source.get("device_registry")),
            sandbox_execution_status=SandboxExecutionStatus.from_dict(source.get("sandbox_execution_status")),
            tool_adoption_status=ToolAdoptionStatus.from_dict(source.get("tool_adoption_status")),
            asset_factory_status=AssetFactoryStatus.from_dict(source.get("asset_factory_status")),
            asset_generation_policy=AssetGenerationPolicy.from_dict(source.get("asset_generation_policy")),
            deploy_publishing_status=DeployPublishingStatus.from_dict(source.get("deploy_publishing_status")),
            deploy_publishing_policy=DeployPublishingPolicy.from_dict(source.get("deploy_publishing_policy")),
            publishing_readiness=PublishingReadinessChecklist.from_dict(source.get("publishing_readiness")),
            marketing_distribution_status=MarketingDistributionStatus.from_dict(source.get("marketing_distribution_status")),
            marketing_distribution_policy=MarketingDistributionPolicy.from_dict(source.get("marketing_distribution_policy")),
            marketing_launch_readiness=LaunchChecklistPreview.from_dict(source.get("marketing_launch_readiness")),
            payments_revenue_status=PaymentsRevenueStatus.from_dict(source.get("payments_revenue_status")),
            payments_revenue_policy=PaymentsRevenuePolicy.from_dict(source.get("payments_revenue_policy")),
            financial_readiness=FinancialRiskGuardPreview.from_dict(source.get("financial_readiness")),
            capability_matrix=OperatorConsoleCapabilityMatrix.from_dict(source.get("capability_matrix")),
            safety_summary=OperatorSafetySummary.from_dict(source.get("safety_summary")),
            metadata=dict(source.get("metadata") or {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prepare_only": True,
            "status": self.status.to_dict(),
            "command_center": self.command_center.to_dict(),
            "voice_status": self.voice_status.to_dict(),
            "voice_control_policy": self.voice_control_policy.to_dict(),
            "mobile_status": self.mobile_status.to_dict(),
            "mobile_permission_policy": self.mobile_permission_policy.to_dict(),
            "mobile_command_center": self.mobile_command_center.to_dict(),
            "ambient_vision_status": self.ambient_vision_status.to_dict(),
            "ambient_vision_privacy_policy": self.ambient_vision_privacy_policy.to_dict(),
            "ambient_vision_stop_control": self.ambient_vision_stop_control.to_dict(),
            "multi_device_runtime_status": self.multi_device_runtime_status.to_dict(),
            "device_registry": self.device_registry.to_dict(),
            "sandbox_execution_status": self.sandbox_execution_status.to_dict(),
            "tool_adoption_status": self.tool_adoption_status.to_dict(),
            "asset_factory_status": self.asset_factory_status.to_dict(),
            "asset_generation_policy": self.asset_generation_policy.to_dict(),
            "deploy_publishing_status": self.deploy_publishing_status.to_dict(),
            "deploy_publishing_policy": self.deploy_publishing_policy.to_dict(),
            "publishing_readiness": self.publishing_readiness.to_dict(),
            "marketing_distribution_status": self.marketing_distribution_status.to_dict(),
            "marketing_distribution_policy": self.marketing_distribution_policy.to_dict(),
            "marketing_launch_readiness": self.marketing_launch_readiness.to_dict(),
            "payments_revenue_status": self.payments_revenue_status.to_dict(),
            "payments_revenue_policy": self.payments_revenue_policy.to_dict(),
            "financial_readiness": self.financial_readiness.to_dict(),
            "capability_matrix": self.capability_matrix.to_dict(),
            "safety_summary": self.safety_summary.to_dict(),
            "metadata": dict(self.metadata),
        }


def build_operator_command_center_view(*, view_id: str, generated_at: str) -> CommandCenterViewModel:
    return build_command_center_view_model(
        view_id=view_id,
        generated_at=generated_at,
        metadata={
            "phase": "G",
            "source": "operator_console_placeholder_snapshot",
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


def _command_center_from_optional_dict(data: Optional[Dict[str, Any]]) -> CommandCenterViewModel:
    return build_operator_command_center_view(
        view_id="operator-command-center-placeholder",
        generated_at="1970-01-01T00:00:00+00:00",
    )


def build_operator_console_snapshot(*, view_id: str, generated_at: str) -> OperatorConsoleSnapshot:
    command_center = build_operator_command_center_view(view_id=view_id, generated_at=generated_at)
    return OperatorConsoleSnapshot(
        command_center=command_center,
        mobile_command_center=MobileCommandCenterSnapshot.from_command_center_view(command_center),
        metadata={
            "phase": "G",
            "source": "operator_console_snapshot",
            "prepare_only": True,
            "frontend_available": False,
            "websocket_enabled": False,
            "execution_enabled": False,
            "approval_actions_enabled": False,
            "hermes_connected": False,
            "approval_gateway_called": False,
            "external_calls_enabled": False,
            "safe_read_only_mode": True,
            "multi_device_runtime": "prepare_only",
            "sandbox_execution": "prepare_only",
            "tool_adoption_pipeline": "prepare_only",
            "asset_factory_web_builder": "prepare_only",
            "deploy_publishing_control": "prepare_only",
            "marketing_distribution_engine": "prepare_only",
            "payments_revenue": "prepare_only",
        },
    )


def _combine_policy_decisions(first: str, second: str, *, sensitive: bool) -> str:
    values = {str(first or "unknown"), str(second or "unknown")}
    if "denied" in values:
        return "denied"
    if sensitive or "requires_approval" in values:
        return "requires_approval"
    if values == {"allowed"} or "allowed" in values:
        return "allowed"
    return "unknown"


def _safe_metadata(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    source = dict(data or {})
    safe = {
        "phase": "G",
        "source": _safe_label(source.get("source", "operator_console_snapshot")),
        "prepare_only": True,
        "frontend_available": False,
        "websocket_enabled": False,
        "execution_enabled": False,
        "approval_actions_enabled": False,
        "hermes_connected": False,
        "approval_gateway_called": False,
        "external_calls_enabled": False,
        "safe_read_only_mode": True,
        "multi_device_runtime": "prepare_only",
        "sandbox_execution": "prepare_only",
        "tool_adoption_pipeline": "prepare_only",
        "asset_factory_web_builder": "prepare_only",
        "deploy_publishing_control": "prepare_only",
        "marketing_distribution_engine": "prepare_only",
        "payments_revenue": "prepare_only",
    }
    return safe


def _safe_label(value: Any) -> str:
    text = _safe_text(value).lower().replace(" ", "_")
    if not text or _contains_sensitive_marker(text):
        return "operator_console_snapshot"
    return text[:80]


def _sanitize_input(value: Any, *, sensitive: bool = False) -> str:
    text = _safe_text(value)
    if not text:
        return ""
    if sensitive or _contains_sensitive_marker(text):
        return _REDACTED_OPERATOR_INPUT
    return text[:240]


def _safe_reason(value: Any) -> str:
    text = _safe_text(value)
    if not text:
        return _OPERATOR_PREVIEW_REASON
    if _contains_sensitive_marker(text):
        return "Sensitive operator preview details were redacted; execution remains disabled."
    return text[:220]


def _safe_warning(value: Any) -> str:
    text = _safe_text(value)
    if not text:
        return ""
    if _contains_sensitive_marker(text):
        return _REDACTED_OPERATOR_WARNING
    return text[:220]


def _safe_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _contains_sensitive_marker(value: Any) -> bool:
    text = str(value or "").lower()
    return any(marker in text for marker in _SENSITIVE_MARKERS)
