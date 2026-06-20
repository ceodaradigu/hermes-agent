import { Activity, AlertTriangle, BadgeCheck, Brain, Camera, CircleDollarSign, Cpu, Radar, ScrollText, Smartphone, Stethoscope, TerminalSquare, Workflow, ZapOff } from "lucide-react";
import type {
  JarvisActionContract,
  JarvisBrowserVerificationCheck,
  JarvisBrowserVerificationStatus,
  JarvisDashboardStatus,
  JarvisExecutionHistoryItem,
  JarvisExecutionHistoryStatus,
  JarvisLocalRuntimeStatus,
  JarvisPhase2VoiceRuntime,
} from "@/lib/api";
import type { JarvisEvent } from "./types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DASHBOARD_READ_MODEL_ENDPOINT,
  commandCenterTabs,
  contractCopyGroups,
  fallbackApprovalCards,
  fallbackDashboard,
  fallbackFinanceMetrics,
  missionLifecycleDisplay,
  missionSafetyLabels,
  sampleMissionCommand,
  visualQaPreviewStates,
  type CommandCenterTabId,
} from "./contracts";
import { ContractVault, MiniStat, SafetyLine, StatusList } from "./JarvisPanels";
import { metricValue, statusVariant, valueText, yesNo } from "./utils";
import type { JarvisOrbVisualState } from "./types";

interface JarvisDebugDrawerProps {
  dashboard: JarvisDashboardStatus;
  activeTab: CommandCenterTabId;
  onTabChange: (tab: CommandCenterTabId) => void;
  events: JarvisEvent[];
  eventConnectionState: string;
  connectionState: "loading" | "online" | "offline";
  conversationActive: boolean;
  sttText: string;
  ttsText: string;
  coreSubtitle: string;
  visualPreviewState: JarvisOrbVisualState | null;
  resolvedVisualState: JarvisOrbVisualState;
  onVisualPreviewStateChange: (state: JarvisOrbVisualState | null) => void;
}

export function JarvisDebugDrawer({
  dashboard,
  activeTab,
  onTabChange,
  events,
  eventConnectionState,
  connectionState,
  conversationActive,
  sttText,
  ttsText,
  coreSubtitle,
  visualPreviewState,
  resolvedVisualState,
  onVisualPreviewStateChange,
}: JarvisDebugDrawerProps) {
  const fallbackOffline = fallbackDashboard("offline");
  const modules = dashboard.modules?.length ? dashboard.modules : fallbackOffline.modules ?? [];
  const approvals = dashboard.approvals ?? {};
  const approvalCards = approvals.cards?.length ? approvals.cards : fallbackApprovalCards;
  const missionControl = dashboard.mission_control ?? fallbackOffline.mission_control!;
  const missionIntent = missionControl.intent_preview ?? {};
  const missionSafety = missionControl.safety ?? {};
  const missionConversation = missionControl.conversation_preview ?? {};
  const conversationalBrain = dashboard.conversational_brain ?? fallbackOffline.conversational_brain!;
  const brainPreview = conversationalBrain.sample_analysis;
  const conversationalIntake = dashboard.conversational_intake ?? fallbackOffline.conversational_intake!;
  const intakeSample = conversationalIntake.sample ?? {};
  const intakePreview = intakeSample.classification ?? {};
  const brainAdapter = dashboard.brain_adapter ?? fallbackOffline.brain_adapter!;
  const brainAdapterState = brainAdapter.state ?? {};
  const localBrainProvider = brainAdapter.providers?.deterministic_local;
  const externalBrainProvider = brainAdapter.providers?.disabled_external_llm;
  const brainResponse = brainAdapter.sample?.brain_response ?? {};
  const hermes = dashboard.hermes_execution ?? {};
  const hermesRuntime = hermes.runtime_status ?? hermes;
  const voiceRuntimePack = dashboard.voice_runtime_pack ?? {};
  const voiceCore = dashboard.voice_core ?? fallbackOffline.voice_core!;
  const voiceSession = dashboard.voice_session ?? fallbackOffline.voice_session!;
  const voiceCoreState = voiceCore.state ?? {};
  const localVoiceLoop = dashboard.local_voice_loop ?? fallbackOffline.local_voice_loop!;
  const wakeWordFlow = dashboard.wake_word_flow ?? fallbackOffline.wake_word_flow!;
  const cameraVision = dashboard.camera_vision ?? fallbackOffline.camera_vision!;
  const cameraVisionState = cameraVision.state ?? {};
  const cameraVisionPrivacy = cameraVision.privacy ?? {};
  const cameraVideoRecorder = cameraVision.video_recorder ?? {};
  const mobileCompanion = dashboard.mobile_companion ?? fallbackOffline.mobile_companion!;
  const mobileCompanionState = mobileCompanion.state ?? {};
  const financeRoi = dashboard.finance_roi ?? fallbackOffline.finance_roi!;
  const financeMetrics = financeRoi.metrics ?? fallbackFinanceMetrics;
  const productBuilder = dashboard.adaptive_product_builder ?? fallbackOffline.adaptive_product_builder!;
  const productStages = productBuilder.stages ?? fallbackOffline.adaptive_product_builder!.stages!;
  const frontendPilot = dashboard.frontend_pilot ?? fallbackOffline.frontend_pilot!;
  const visualPilot = dashboard.visual_command_center_pilot ?? fallbackOffline.visual_command_center_pilot!;
  const memoryBrain = dashboard.memory_brain ?? {};
  const persistentAudit = dashboard.persistent_audit ?? {};
  const localDoctor = dashboard.local_doctor ?? {};
  const rawAudioRecording = dashboard.raw_audio_recording ?? {};
  const sensorLedger = dashboard.sensor_ledger ?? {};
  const eventBus = dashboard.event_bus ?? {};
  const policyStatus = dashboard.policy_status ?? {};
  const localDoctorRuntime = localDoctor.runtime as Record<string, unknown> | undefined;
  const localDoctorProcess = localDoctorRuntime?.process as Record<string, unknown> | undefined;
  const timeline = dashboard.timeline?.length ? dashboard.timeline : fallbackOffline.timeline ?? [];
  const phase2Status = (dashboard.phase_2_status ?? {}) as Record<string, unknown>;
  const phase3Status = (dashboard.phase_3_status ?? {}) as Record<string, unknown>;
  const phase4Status = (dashboard.phase_4_status ?? {}) as Record<string, unknown>;
  const phase5Status = (dashboard.phase_5_status ?? {}) as Record<string, unknown>;
  const phase7Status = (dashboard.phase_7_status ?? {}) as Record<string, unknown>;
  const phase8Status = (dashboard.phase_8_status ?? fallbackOffline.phase_8_status ?? {}) as Record<string, any>;
  const remoteChannels = (dashboard.remote_channels ?? fallbackOffline.remote_channels ?? {}) as Record<string, any>;
  const telegramReadiness = (dashboard.telegram_readiness ?? fallbackOffline.telegram_readiness ?? {}) as Record<string, any>;
  const mobileApprovalCenter = (dashboard.mobile_approval_center ?? fallbackOffline.mobile_approval_center ?? {}) as Record<string, any>;
  const externalOperations = (dashboard.external_operations ?? fallbackOffline.external_operations ?? {}) as Record<string, any>;
  const externalBudgetGuard = (dashboard.external_budget_guard ?? fallbackOffline.external_budget_guard ?? {}) as Record<string, any>;
  const stripeReadiness = (externalOperations.payments?.stripe_readiness ?? {}) as Record<string, unknown>;
  const filesystemAdapter = (dashboard.filesystem_adapter ?? {}) as Record<string, unknown>;
  const githubWorktreeAdapter = (dashboard.github_worktree_adapter ?? {}) as Record<string, unknown>;
  const browserAutomation = (dashboard.browser_automation ?? {}) as Record<string, unknown>;
  const sandboxExecution = (dashboard.sandbox_execution ?? {}) as Record<string, unknown>;
  const preflight = (dashboard.preflight ?? {}) as Record<string, unknown>;
  const actionCatalogItems: JarvisActionContract[] = (dashboard.action_catalog?.actions ?? dashboard.governed_execution?.action_catalog ?? []).slice(0, 18);
  const executionHistoryStatus: JarvisExecutionHistoryStatus = dashboard.execution_history?.status ?? dashboard.governed_execution?.execution_history ?? {};
  const executionHistoryItems: JarvisExecutionHistoryItem[] = (dashboard.execution_history?.items ?? dashboard.governed_execution?.execution_history?.recent ?? []).slice(0, 5);
  const localRuntime: JarvisLocalRuntimeStatus = dashboard.local_runtime ?? dashboard.governed_execution?.local_runtime ?? {};
  const localDaemon = (dashboard.local_daemon ?? localRuntime.daemon ?? {}) as Record<string, unknown>;
  const localController = (dashboard.local_controller ?? phase4Status.local_controller ?? {}) as Record<string, unknown>;
  const trayReadiness = (dashboard.tray_readiness ?? localRuntime.tray ?? {}) as Record<string, unknown>;
  const trustedChannels = (dashboard.trusted_approval_channels ?? localRuntime.trusted_approval_channels ?? {}) as Record<string, unknown>;
  const trustedChannelItems = (trustedChannels.channels as Record<string, unknown>[] | undefined ?? []).slice(0, 7);
  const trustedDevices = (dashboard.trusted_devices ?? phase4Status.trusted_devices ?? {}) as Record<string, unknown>;
  const trustedDeviceItems = (trustedDevices.devices as Record<string, unknown>[] | undefined ?? []).slice(0, 8);
  const tripleReadiness = (phase4Status.triple_approval_readiness ?? {}) as Record<string, unknown>;
  const phase5TripleReadiness = (phase5Status.triple_approval_readiness ?? tripleReadiness) as Record<string, unknown>;
  const localPairing = (dashboard.local_pairing ?? phase5Status.local_pairing ?? {}) as Record<string, unknown>;
  const voiceApproval = (dashboard.voice_approval ?? phase5Status.voice_approval ?? {}) as Record<string, unknown>;
  const notifications = (dashboard.notifications ?? phase5Status.notifications ?? {}) as Record<string, unknown>;
  const remotePairing = (dashboard.remote_pairing ?? phase4Status.remote_pairing ?? {}) as Record<string, unknown>;
  const telegramBridge = (dashboard.telegram_bridge ?? phase4Status.telegram_bridge ?? {}) as Record<string, unknown>;
  const remoteBridgeFuture = (localRuntime.remote_bridge_future ?? phase3Status.remote_bridge_future ?? {}) as Record<string, unknown>;
  const browserVerification: JarvisBrowserVerificationStatus = dashboard.browser_verification ?? dashboard.governed_execution?.browser_verification ?? {};
  const phase3Pilot = (browserVerification.phase_3_pilot ?? phase3Status.browser_local_pilot ?? {}) as Record<string, unknown>;
  const phase4Pilot = (browserVerification.phase_4_pilot ?? phase4Status.pilot ?? {}) as Record<string, unknown>;
  const browserChecks: JarvisBrowserVerificationCheck[] = (browserVerification.checks ?? []).slice(0, 8);
  const stopRollbackContracts = (dashboard.stop_rollback_contracts ?? dashboard.governed_execution?.stop_rollback_contracts ?? {}) as Record<string, unknown>;
  const stopRollbackV2 = (dashboard.stop_rollback_v2 ?? phase4Status.stop_rollback_v2 ?? {}) as Record<string, unknown>;
  const voicePhase2Runtime: JarvisPhase2VoiceRuntime = voiceRuntimePack.phase_2_runtime ?? {};
  const voiceDiagnostics = voicePhase2Runtime.voice_runtime_diagnostics ?? {};
  const wakeRuntimeReadiness = voicePhase2Runtime.wake_runtime_readiness ?? {};

  const hermesRows = [
    ["Hermes disponible", yesNo(hermesRuntime.available, "sí", "no")],
    ["Hermes conectado", yesNo(hermesRuntime.connected, "sí", "no")],
    ["ejecución activa", yesNo(hermesRuntime.active_execution, "sí", "no")],
    ["modo", valueText(hermesRuntime.execution_mode, "read_only_visibility")],
    ["coste", valueText(hermesRuntime.measured_cost)],
  ] as const;

  const phase2Rows = [
    ["phase", valueText(phase2Status.phase, "phase_2_local_assistant_runtime")],
    ["status", valueText(phase2Status.status, "ready")],
    ["allowlist", yesNo(phase2Status.allowlist_only, "true", "false")],
    ["approval v2", yesNo(phase2Status.strong_approval_v2, "enabled", "unknown")],
    ["history", yesNo(phase2Status.execution_history, "enabled", "unknown")],
    ["local runtime ready", yesNo(phase2Status.local_runtime_ready, "true", "false")],
  ] as const;

  const phase3Rows = [
    ["phase", valueText(phase3Status.phase, "Phase 3")],
    ["status", valueText(phase3Status.status, "ready")],
    ["daemon contract", yesNo((phase3Status.implemented_blocks as Record<string, unknown> | undefined)?.local_runtime_daemon_contract, "implemented", "unknown")],
    ["trusted channels", yesNo((phase3Status.implemented_blocks as Record<string, unknown> | undefined)?.trusted_approval_channels, "implemented", "unknown")],
    ["double approval", yesNo((phase3Status.implemented_blocks as Record<string, unknown> | undefined)?.double_approval_two_steps, "real", "unknown")],
    ["triple", valueText((phase3Status.blocked_or_unsupported as Record<string, unknown> | undefined)?.triple, "blocked")],
    ["remote approval", yesNo((phase3Status.security_gates as Record<string, unknown> | undefined)?.remote_approval_allowed, "allowed", "false")],
  ] as const;

  const phase4Rows = [
    ["phase", valueText(phase4Status.phase, "Phase 4")],
    ["status", valueText(phase4Status.status, "readiness")],
    ["local controller", yesNo((phase4Status.implemented_blocks as Record<string, unknown> | undefined)?.real_local_controller_opt_in, "implemented", "unknown")],
    ["trusted devices", yesNo((phase4Status.implemented_blocks as Record<string, unknown> | undefined)?.trusted_device_controller_identity, "implemented", "unknown")],
    ["triple readiness", valueText(tripleReadiness.triple_status, "blocked_no_three_verified_channels")],
    ["remote pairing", yesNo((phase4Status.security_gates as Record<string, unknown> | undefined)?.remote_pairing_enabled, "enabled", "false")],
    ["Telegram API", yesNo((phase4Status.security_gates as Record<string, unknown> | undefined)?.telegram_api_called, "called", "false")],
  ] as const;

  const phase5Rows = [
    ["phase", valueText(phase5Status.phase, "Phase 5")],
    ["status", valueText(phase5Status.status, "trusted identity / voice foundation")],
    ["persistent identity", yesNo((phase5Status.implemented_blocks as Record<string, unknown> | undefined)?.persistent_trusted_device_identity_v1, "implemented", "unknown")],
    ["local pairing", yesNo((phase5Status.implemented_blocks as Record<string, unknown> | undefined)?.hardened_local_pairing_v1, "implemented", "unknown")],
    ["voice approval", yesNo((phase5Status.implemented_blocks as Record<string, unknown> | undefined)?.governed_voice_approval_contract_v1, "governed", "unknown")],
    ["notifications", yesNo((phase5Status.implemented_blocks as Record<string, unknown> | undefined)?.notification_readiness_contracts, "ready", "unknown")],
    ["wake approves", yesNo((phase5Status.security_gates as Record<string, unknown> | undefined)?.wake_phrase_can_approve, "allowed", "false")],
    ["remote execution", yesNo((phase5Status.security_gates as Record<string, unknown> | undefined)?.remote_execution_allowed, "allowed", "false")],
  ] as const;

  const phase7Rows = [
    ["phase", valueText(phase7Status.phase, "Phase 7")],
    ["status", valueText(phase7Status.status, "governed local action pilot")],
    ["catalog v2", yesNo((phase7Status.implemented_blocks as Record<string, unknown> | undefined)?.governed_action_catalog_v2, "implemented", "unknown")],
    ["filesystem", valueText(filesystemAdapter.status, "real_safe_local_adapter")],
    ["Git/worktree", valueText(githubWorktreeAdapter.status, "read_only_helpers")],
    ["browser", valueText(browserAutomation.status, "readiness_and_plan_only")],
    ["sandbox", valueText(sandboxExecution.status, "guarded_runner")],
    ["preflight", valueText(preflight.status, "enabled")],
  ] as const;

  const phase7AdapterRows = [
    ["allowed roots", valueText((filesystemAdapter.allowed_roots as unknown[] | undefined)?.length, "0")],
    ["backup overwrite", yesNo(filesystemAdapter.backup_before_overwrite, "enabled", "unknown")],
    ["delete", yesNo(filesystemAdapter.delete_enabled, "enabled", "dry-run only")],
    ["GitHub API", yesNo(githubWorktreeAdapter.github_api_called, "called", "false")],
    ["commit/push/PR", yesNo(githubWorktreeAdapter.commit_enabled || githubWorktreeAdapter.push_enabled || githubWorktreeAdapter.open_pr_enabled, "enabled", "disabled")],
    ["hidden browser", yesNo(browserAutomation.hidden_browser_allowed, "allowed", "blocked")],
    ["shell freeform", yesNo(sandboxExecution.shell_freeform_allowed, "allowed", "blocked")],
    ["secret scanning", yesNo(preflight.redaction, "redacts", "unknown")],
  ] as const;

  const phase8Rows = [
    ["phase", valueText(phase8Status.phase, "Phase 8")],
    ["status", valueText(phase8Status.status, "governed remote/external ops pilot")],
    ["remote Hermes direct", yesNo(phase8Status.security_gates?.remote_channels_call_hermes_directly, "allowed", "false")],
    ["remote execution default", yesNo(phase8Status.security_gates?.remote_execution_enabled_by_default, "enabled", "disabled")],
    ["Telegram autostart", yesNo(phase8Status.security_gates?.telegram_bot_autostart, "enabled", "false")],
    ["provider calls default", yesNo(phase8Status.security_gates?.provider_calls_enabled_by_default, "enabled", "disabled")],
    ["live money movement", yesNo(phase8Status.security_gates?.live_money_movement_enabled, "enabled", "blocked")],
    ["fake revenue", yesNo(phase8Status.security_gates?.fake_revenue_allowed, "allowed", "blocked")],
  ] as const;

  const remoteChannelRows = [
    ["registry", valueText(remoteChannels.status, "remote_channels_registered_disabled_by_default")],
    ["trusted remote devices", valueText(remoteChannels.trusted_remote_device_count, "0")],
    ["kill switch", yesNo(remoteChannels.remote_kill_switch?.enabled, "enabled", "disabled")],
    ["pairing required", yesNo(remoteChannels.requirements?.pairing_required, "required", "unknown")],
    ["anti replay", yesNo(remoteChannels.requirements?.anti_replay, "required", "unknown")],
    ["approve all forever", yesNo(remoteChannels.defaults?.approve_all_forever_allowed, "allowed", "forbidden")],
    ["remote execution", yesNo(remoteChannels.defaults?.remote_execution_enabled, "enabled", "disabled")],
    ["direct Hermes", yesNo(remoteChannels.defaults?.frontend_or_remote_direct_hermes, "allowed", "forbidden")],
  ] as const;

  const telegramReadinessRows = [
    ["provider", valueText(telegramReadiness.provider, "telegram")],
    ["status", valueText(telegramReadiness.provider_status, "disabled_by_default_or_incomplete")],
    ["enabled by config", yesNo(telegramReadiness.enabled_by_config, "enabled", "disabled")],
    ["token present", yesNo(telegramReadiness.token_present, "present redacted", "missing")],
    ["token exposed", yesNo(telegramReadiness.token_value_exposed, "exposed", "false")],
    ["bot started", yesNo(telegramReadiness.runtime?.bot_started, "started", "false")],
    ["webhook opened", yesNo(telegramReadiness.runtime?.webhook_opened, "opened", "false")],
    ["remote execution", "disabled"],
  ] as const;

  const mobileApprovalRows = [
    ["mobile center", valueText(mobileApprovalCenter.status, "mobile_pwa_approval_center_readiness")],
    ["mode", valueText(mobileApprovalCenter.mode, "preview_readback_challenge_only")],
    ["readback", yesNo(mobileApprovalCenter.can_show_readback, "available", "unknown")],
    ["risk/cost/scope", yesNo(mobileApprovalCenter.can_show_risk_cost_scope, "shown", "unknown")],
    ["approve real actions", yesNo(mobileApprovalCenter.can_approve_real_actions, "enabled", "false")],
    ["execute", yesNo(mobileApprovalCenter.can_execute, "enabled", "disabled")],
    ["direct Hermes", yesNo(mobileApprovalCenter.can_call_hermes_directly, "allowed", "forbidden")],
    ["expiration", yesNo(mobileApprovalCenter.requirements?.expiration_required, "required", "unknown")],
  ] as const;

  const externalOpsRows = [
    ["status", valueText(externalOperations.status, "prepare_only_external_operation_contracts_ready")],
    ["execution", yesNo(externalOperations.execution_enabled, "enabled", "disabled")],
    ["provider calls", yesNo(externalOperations.provider_calls_enabled, "enabled", "disabled")],
    ["deploy dry-run", yesNo(externalOperations.deploy?.dry_run_default, "default", "unknown")],
    ["email send default", yesNo(externalOperations.email?.send_enabled_by_default, "enabled", "disabled")],
    ["Stripe mode", valueText(stripeReadiness.mode_detected, "not_configured")],
    ["Stripe key exposed", yesNo(stripeReadiness.api_key_value_exposed, "exposed", "false")],
    ["money movement", yesNo(externalOperations.payments?.money_movement_enabled, "enabled", "disabled")],
  ] as const;

  const externalBudgetRows = [
    ["decision", valueText(externalBudgetGuard.decision, "allowed_prepare_only")],
    ["can spend", yesNo(externalBudgetGuard.can_spend, "true", "false")],
    ["budget consumed by evidence", yesNo(externalBudgetGuard.budget_consumed_only_by_confirmed_evidence, "true", "unknown")],
    ["estimates consume budget", yesNo(externalBudgetGuard.estimates_consume_budget, "true", "false")],
    ["approval required for spend", yesNo(externalBudgetGuard.explicit_approval_required_for_spending, "true", "unknown")],
    ["unknown cost gate", yesNo(externalBudgetGuard.unknown_cost_blocks_or_requires_strong_approval, "blocks", "not triggered")],
  ] as const;

  const localRuntimeRows = [
    ["daemon", valueText(localRuntime.daemon_status, "not_running")],
    ["tray", valueText(localRuntime.tray_status, "not_running")],
    ["ready", yesNo(localRuntime.local_runtime_ready, "true", "false")],
    ["startup", valueText(localRuntime.startup_mode, "manual")],
    ["background listening", yesNo(localRuntime.background_listening_enabled, "true", "false")],
    ["auto start", yesNo(localRuntime.auto_start_enabled, "true", "false")],
    ["opt-in", yesNo(localRuntime.user_opt_in_required, "true", "false")],
    ["binding", valueText(localRuntime.local_only_binding, "127.0.0.1/localhost")],
  ] as const;

  const daemonRows = [
    ["daemon_id", valueText(localDaemon.daemon_id)],
    ["status", valueText(localDaemon.daemon_status, "running_embedded_local_api_process")],
    ["pid", valueText(localDaemon.pid)],
    ["bind", `${valueText(localDaemon.bind_host, "127.0.0.1")}:${valueText(localDaemon.bind_port, "9119")}`],
    ["local_only", yesNo(localDaemon.local_only, "true", "false")],
    ["auto_start", yesNo(localDaemon.auto_start_enabled, "true", "false")],
    ["background", yesNo(localDaemon.background_listening_enabled, "true", "false")],
    ["mic/camera/wake auto", `${yesNo(localDaemon.mic_auto_start, "true", "false")}/${yesNo(localDaemon.camera_auto_start, "true", "false")}/${yesNo(localDaemon.wake_auto_start, "true", "false")}`],
    ["health", valueText(localDaemon.health_status, "healthy")],
    ["heartbeat", valueText(localDaemon.last_heartbeat_at, "none")],
    ["stop", yesNo(localDaemon.stop_supported, "supported", "unsupported")],
    ["restart", yesNo(localDaemon.restart_supported, "supported", "unsupported")],
  ] as const;

  const localControllerRows = [
    ["controller_id", valueText(localController.controller_id)],
    ["status", valueText(localController.controller_status, "not_registered")],
    ["mode", valueText(localController.controller_mode, "local_opt_in_readiness")],
    ["bind", `${valueText(localController.bind_host, "127.0.0.1")}:${valueText(localController.bind_port, "9119")}`],
    ["local_only", yesNo(localController.local_only, "true", "false")],
    ["verified", yesNo(localController.verified, "true", "false")],
    ["auto_start", yesNo(localController.auto_start_enabled, "true", "false")],
    ["system service", yesNo(localController.installed_as_system_service, "true", "false")],
    ["startup integration", yesNo(localController.startup_integration_enabled, "true", "false")],
    ["no background capture", yesNo(localController.no_background_capture, "true", "false")],
    ["last seen", valueText(localController.last_seen_at, "none")],
    ["health", valueText(localController.health_status, "healthy")],
  ] as const;

  const trayRows = [
    ["available", yesNo(trayReadiness.tray_available, "true", "false")],
    ["installed", yesNo(trayReadiness.tray_installed, "true", "false")],
    ["running", yesNo(trayReadiness.tray_running, "true", "false")],
    ["open JARVIS", yesNo(trayReadiness.can_open_jarvis, "true", "false")],
    ["show approval", yesNo(trayReadiness.can_show_approval, "true", "false")],
    ["show status", yesNo(trayReadiness.can_show_status, "true", "false")],
    ["voice/camera/recording", `${yesNo(trayReadiness.can_toggle_voice_session, "voice", "no voice")} · ${yesNo(trayReadiness.can_toggle_camera_session, "camera", "no camera")} · ${yesNo(trayReadiness.can_toggle_recording_session, "recording", "no recording")}`],
    ["no background capture", yesNo(trayReadiness.no_background_capture, "true", "false")],
  ] as const;

  const trustedChannelRows = [
    ["trusted enabled", valueText(trustedChannels.trusted_enabled_channel_count, "0")],
    ["normal", yesNo(trustedChannels.can_grant_normal, "available", "false")],
    ["strong", yesNo(trustedChannels.can_grant_strong, "available", "false")],
    ["double", yesNo(trustedChannels.can_grant_double, "available", "false")],
    ["triple", yesNo(trustedChannels.can_grant_triple, "available", "false")],
    ["voice approves", yesNo(trustedChannels.voice_can_approve, "allowed", "false")],
    ["wake approves", yesNo(trustedChannels.wake_phrase_can_approve, "allowed", "false")],
    ["remote approval", yesNo(trustedChannels.remote_approval_allowed, "allowed", "false")],
  ] as const;

  const trustedDeviceRows = [
    ["trusted devices", valueText(trustedDevices.trusted_device_count, "0")],
    ["paired devices", valueText(trustedDevices.paired_devices_count, "0")],
    ["remote devices", valueText(trustedDevices.remote_devices_count, "0")],
    ["remote trusted", valueText(trustedDevices.remote_trusted_devices_count, "0")],
    ["remote default", yesNo(trustedDevices.default_remote_devices_zero_untrusted, "zero/untrusted", "unknown")],
    ["terminal challenge", yesNo(trustedDevices.terminal_trust_requires_challenge, "required", "unknown")],
    ["controller verification", yesNo(trustedDevices.controller_trust_requires_registration_and_verification, "required", "unknown")],
    ["triple", yesNo(trustedDevices.can_grant_triple, "ready", "blocked")],
  ] as const;

  const tripleApprovalRows = [
    ["status", valueText(phase5TripleReadiness.triple_status, "blocked_no_three_persistent_verified_channels")],
    ["steps", valueText(phase5TripleReadiness.required_step_count, "3")],
    ["ready channels", valueText((phase5TripleReadiness.ready_channel_ids as unknown[] | undefined)?.join?.(", "), "none")],
    ["persistent identity", yesNo(phase5TripleReadiness.persistent_identity_required, "required", "unknown")],
    ["channel separation", yesNo(phase5TripleReadiness.channel_separation_required, "required", "unknown")],
    ["challenge per step", yesNo(phase5TripleReadiness.challenge_per_step, "required", "unknown")],
    ["readback per step", yesNo(phase5TripleReadiness.readback_per_step, "required", "unknown")],
    ["anti-reuse", yesNo(phase5TripleReadiness.anti_reuse ?? phase5TripleReadiness.no_replay, "enabled", "unknown")],
    ["audit chain", yesNo(phase5TripleReadiness.audit_chain_required, "required", "unknown")],
    ["policy recalc final", yesNo(phase5TripleReadiness.policy_recalculation_before_final_decision, "required", "unknown")],
  ] as const;

  const doubleApprovalRows = [
    ["step 1", "strong local browser/terminal"],
    ["step 2", "separate trusted channel"],
    ["same approval_id", "true"],
    ["different step_id", "true"],
    ["readback", "required"],
    ["confirmation phrase", "required"],
    ["anti-reuse", "enabled"],
    ["triple", valueText(trustedChannels.triple_status, "triple_requires_additional_trusted_channel_not_configured")],
  ] as const;

  const remotePairingRows = [
    ["status", valueText(remotePairing.pairing_status, "disabled_readiness_only")],
    ["remote pairing", yesNo(remotePairing.remote_pairing_enabled, "enabled", "false")],
    ["remote approval", yesNo(remotePairing.remote_approval_allowed, "allowed", "false")],
    ["remote execution", yesNo(remotePairing.remote_execution_allowed, "allowed", "false")],
    ["pairing code", yesNo(remotePairing.pairing_code_created, "created", "false")],
    ["TTL", valueText(remotePairing.pairing_code_ttl_seconds, "300")],
    ["pending", valueText(remotePairing.pending_pairing_count, "0")],
    ["revoked", valueText(remotePairing.revoked_pairing_count, "0")],
  ] as const;

  const localPairingRows = [
    ["status", valueText(localPairing.pairing_status, "local_hardened_pairing_available")],
    ["nonce", yesNo(localPairing.nonce_required, "required", "unknown")],
    ["one-time", yesNo(localPairing.one_time_use, "required", "unknown")],
    ["exact scope", yesNo(localPairing.exact_scope_required, "required", "unknown")],
    ["trusted binding", yesNo(localPairing.trusted_device_binding, "required", "unknown")],
    ["pending", valueText(localPairing.pending_pairing_count, "0")],
    ["failed attempts", valueText(localPairing.failed_attempt_count, "0")],
    ["remote execution", yesNo(localPairing.remote_execution_allowed, "allowed", "false")],
  ] as const;

  const voiceApprovalRows = [
    ["available", yesNo(voiceApproval.voice_approval_available, "true", "false")],
    ["enabled", yesNo(voiceApproval.voice_approval_enabled, "true", "false")],
    ["active session", yesNo(voiceApproval.requires_active_voice_session, "required", "unknown")],
    ["trusted device", yesNo(voiceApproval.requires_trusted_device, "required", "unknown")],
    ["exact readback", yesNo(voiceApproval.requires_exact_readback, "required", "unknown")],
    ["spoken challenge", yesNo(voiceApproval.requires_spoken_challenge, "required", "unknown")],
    ["anti-replay sessions", valueText(voiceApproval.active_session_count, "0")],
    ["wake approves", yesNo(voiceApproval.wake_phrase_can_approve, "allowed", "false")],
    ["raw audio", yesNo(voiceApproval.raw_audio_stored_by_default, "stored", "false")],
  ] as const;

  const notificationRows = [
    ["status", valueText(notifications.status, "local_notification_contract_ready")],
    ["external notifications", yesNo(notifications.external_notifications_enabled, "enabled", "false")],
    ["Telegram", yesNo(notifications.telegram_notification_only_readiness, "readiness", "false")],
    ["remote execution", yesNo(notifications.remote_execution_allowed, "allowed", "false")],
    ["events", valueText((notifications.supported_events as unknown[] | undefined)?.length, "0")],
    ["recent", valueText((notifications.recent_events as unknown[] | undefined)?.length, "0")],
  ] as const;

  const telegramBridgeRows = [
    ["status", valueText(telegramBridge.telegram_bridge_status, "disabled_not_configured")],
    ["Hermes Telegram", valueText(telegramBridge.hermes_telegram_available_unknown_or_detected, "unknown_not_imported_not_called")],
    ["token", valueText(telegramBridge.token_present, "unknown_redacted")],
    ["token read", yesNo(telegramBridge.token_read, "true", "false")],
    ["API called", yesNo(telegramBridge.telegram_api_called, "true", "false")],
    ["bot started", yesNo(telegramBridge.bot_started, "true", "false")],
    ["remote approval", yesNo(telegramBridge.remote_approval_allowed, "allowed", "false")],
    ["remote execution", yesNo(telegramBridge.remote_execution_allowed, "allowed", "false")],
  ] as const;

  const browserVerificationRows = [
    ["status", valueText(browserVerification.status, "ready_for_manual_or_static_verification")],
    ["route", valueText(browserVerification.route, "/jarvis")],
    ["checks", valueText(browserVerification.check_count ?? browserChecks.length, "0")],
    ["playwright", valueText(browserVerification.playwright_status, "not_required")],
    ["auto mic", yesNo(browserVerification.no_auto_get_user_media, "blocked", "unknown")],
    ["generic execute route", yesNo(browserVerification.no_execute_route, "absent", "unknown")],
    ["frontend Hermes", yesNo(browserVerification.no_direct_hermes_frontend, "blocked", "unknown")],
  ] as const;

  const stopRollbackRows = [
    ["catalog actions", valueText(stopRollbackContracts.catalog_actions, String(actionCatalogItems.length || 0))],
    ["stop unsupported honest", yesNo(stopRollbackContracts.stop_unsupported_honest, "true", "unknown")],
    ["rollback never faked", yesNo(stopRollbackContracts.rollback_never_faked, "true", "unknown")],
    ["read-only rollback", valueText(stopRollbackContracts.read_only_rollback_status, "not_required")],
    ["prepare-only rollback", valueText(stopRollbackContracts.prepare_only_rollback_status, "discard_preview")],
  ] as const;

  const stopRollbackV2Rows = [
    ["status", valueText(stopRollbackV2.status, "observable_metadata_only")],
    ["stop reason", valueText(stopRollbackV2.stop_reason, "none")],
    ["stop actor", valueText(stopRollbackV2.stop_actor, "none")],
    ["stop channel", valueText(stopRollbackV2.stop_channel, "none")],
    ["cooperative signal", yesNo(stopRollbackV2.cooperative_stop_signal, "true", "false")],
    ["bridge attempt", valueText(stopRollbackV2.bridge_stop_attempt, "not_attempted")],
    ["result observed", yesNo(stopRollbackV2.result_observed, "true", "false")],
    ["rollback dry-run", yesNo(stopRollbackV2.rollback_dry_run_mode, "true", "false")],
    ["destructive rollback", yesNo(stopRollbackV2.destructive_rollback_executed, "true", "false")],
  ] as const;

  const voiceRows = [
    ["mode", valueText(voiceCoreState.mode, "preview")],
    ["estado actual", valueText(voiceCoreState.current_state, "preview")],
    ["micrófono", yesNo(voiceCoreState.microphone_enabled, "enabled", "disabled")],
    ["wake word", yesNo(voiceCoreState.wake_word_enabled, "enabled", "disabled")],
    ["TTS", yesNo(voiceCoreState.tts_enabled, "enabled", "disabled")],
    ["STT", yesNo(voiceCoreState.stt_enabled, "enabled", "disabled")],
    ["grabación", yesNo(voiceCoreState.audio_recording, "true", "false")],
    ["audio bruto almacenado", yesNo(voiceCoreState.raw_audio_stored, "true", "false")],
  ] as const;

  const localVoiceRows = [
    ["loop", valueText(localVoiceLoop.state?.mode, "browser_controlled_manual_loop")],
    ["activación", valueText(localVoiceLoop.state?.activation, "explicit_operator_button")],
    ["conversation_active", conversationActive ? "true" : "false"],
    ["wake_listening", yesNo(localVoiceLoop.state?.wake_listening, "true", "false")],
    ["recording", yesNo(localVoiceLoop.state?.recording, "true", "false")],
    ["STT navegador", sttText],
    ["TTS navegador", ttsText],
    ["backend STT", valueText(localVoiceLoop.capabilities?.backend_stt_provider, "none/not_called")],
    ["backend TTS", valueText(localVoiceLoop.capabilities?.backend_tts_provider, "none/not_called")],
    ["audio storage", yesNo(localVoiceLoop.audio_storage ?? localVoiceLoop.privacy?.audio_storage, "true", "false")],
    ["raw audio backend", yesNo(localVoiceLoop.raw_audio_sent_to_backend ?? localVoiceLoop.privacy?.raw_audio_sent_to_backend, "true", "false")],
    ["voice approval", yesNo(localVoiceLoop.approval_by_voice_enabled ?? localVoiceLoop.approval_policy?.approval_by_voice_enabled, "enabled", "disabled")],
    ["wake phrase approval", yesNo(localVoiceLoop.wake_phrase_approval ?? localVoiceLoop.approval_policy?.wake_phrase_approval, "enabled", "disabled")],
  ] as const;

  const voiceRuntimePackRows = [
    ["runtime pack", valueText(voiceRuntimePack.current_state, "idle")],
    ["mode", valueText(voiceRuntimePack.mode, "local_manual_browser_voice_control_plane")],
    ["manual PTT", yesNo(voiceRuntimePack.manual_push_to_talk_enabled, "enabled", "disabled")],
    ["browser STT", valueText(voiceRuntimePack.browser_stt_available, "client_side_unknown")],
    ["browser TTS", valueText(voiceRuntimePack.browser_tts_available, "client_side_unknown")],
    ["faster-whisper", valueText(voiceRuntimePack.local_stt_provider_status?.faster_whisper_disabled_or_missing?.status, "missing")],
    ["whisper.cpp", valueText(voiceRuntimePack.local_stt_provider_status?.whisper_cpp_disabled_or_missing?.status, "missing")],
    ["Piper", valueText(voiceRuntimePack.local_tts_provider_status?.piper_local_disabled_or_missing?.status, "missing")],
    ["wake runtime", valueText(voiceRuntimePack.wake_runtime_status?.status, "wake_listening_disabled")],
    ["can interrupt", yesNo(voiceRuntimePack.can_interrupt, "true", "false")],
    ["can cancel", yesNo(voiceRuntimePack.can_cancel, "true", "false")],
    ["raw audio backend", yesNo(voiceRuntimePack.raw_audio_sent_to_backend, "true", "false")],
    ["transcript persistence", yesNo(voiceRuntimePack.transcript_persistence, "true", "false")],
    ["voice approval", yesNo(voiceRuntimePack.voice_approval_enabled, "enabled", "disabled")],
    ["Hermes dispatch", yesNo(voiceRuntimePack.hermes_dispatch_allowed, "allowed", "false")],
  ] as const;

  const phase2VoiceRows = [
    ["diagnostics", "ready_for_browser_capability_check"],
    ["browser STT", valueText(voiceDiagnostics.browser_stt_capability, "client_side_unknown")],
    ["browser TTS", valueText(voiceDiagnostics.browser_tts_capability, "client_side_unknown")],
    ["selected voice", valueText(voiceDiagnostics.selected_voice_metadata, "browser_selected_voice_name_lang_voice_uri_only")],
    ["low confidence", valueText(voiceDiagnostics.low_confidence_clarification_threshold, "0.65")],
    ["intent submitted", yesNo(voiceDiagnostics.voice_intent_submitted_to_preview, "execution_preview_only", "false")],
    ["wake provider", valueText(wakeRuntimeReadiness.provider_status, "disabled")],
    ["always-on wake", yesNo(wakeRuntimeReadiness.wake_always_on_real, "enabled", "disabled")],
  ] as const;

  const voiceSessionRows = [
    ["voice session", valueText(voiceSession.state?.current_state ?? voiceSession.current_state, "idle")],
    ["wake listening", valueText(voiceSession.state?.wake_listening_state ?? voiceSession.wake_listening_state, "wake_listening_disabled")],
    ["conversation active", yesNo(voiceSession.state?.conversation_active, "true", "false")],
    ["manual PTT", yesNo(voiceSession.state?.manual_push_to_talk_active, "active", "idle")],
    ["raw audio backend", yesNo(voiceSession.privacy?.raw_audio_sent_to_backend, "true", "false")],
    ["transcript persistence", yesNo(voiceSession.privacy?.transcript_persistence, "true", "false")],
    ["background transcription", yesNo(voiceSession.privacy?.background_transcription, "true", "false")],
    ["always-on STT", yesNo(voiceSession.privacy?.always_on_stt, "true", "false")],
    ["microphone auto-start", yesNo(voiceSession.privacy?.microphone_auto_start, "true", "false")],
    ["Hermes dispatch", yesNo(voiceSession.separation?.hermes_execution?.dispatch_allowed, "allowed", "false")],
  ] as const;

  const cameraRows = [
    ["Estado actual", valueText(cameraVisionState.mode, "preview")],
    ["cámara", cameraVisionState.camera_enabled ? "enabled" : "off/disabled"],
    ["permiso solicitado", yesNo(cameraVisionState.camera_permission_requested, "true", "false")],
    ["recording", yesNo(cameraVisionState.recording ?? cameraVision.recording, "true", "false")],
    ["video recorder", valueText(cameraVideoRecorder.mode, "browser_local_video_recorder")],
    ["video opt-in", yesNo(cameraVisionPrivacy.video_recording_manual_opt_in_only, "true", "false")],
    ["video backend", yesNo(cameraVideoRecorder.backend_upload_enabled, "enabled", "disabled")],
    ["streaming", yesNo(cameraVisionState.streaming ?? cameraVision.streaming, "true", "false")],
    ["snapshot", cameraVisionState.snapshot_capture_enabled ? "enabled" : valueText(cameraVision.snapshot, "disabled")],
    ["vision analysis", cameraVisionState.vision_analysis_enabled ? "enabled" : valueText(cameraVision.vision_analysis, "disabled")],
    ["provider externo", cameraVisionState.external_vision_provider_called ? "called" : valueText(cameraVision.provider, "none/not_connected")],
  ] as const;

  const mobileRows = [
    ["PWA baseline", valueText(mobileCompanionState.pwa_baseline, "preview")],
    ["mobile runtime", yesNo(mobileCompanionState.mobile_runtime_enabled, "enabled", "disabled")],
    ["approvals reales desde móvil", yesNo(mobileCompanionState.mobile_can_approve_real_actions, "enabled", "disabled")],
    ["remote kill switch", yesNo(mobileCompanionState.remote_kill_switch_enabled, "enabled", "future gated")],
    ["mobile camera", yesNo(mobileCompanionState.remote_camera_enabled, "enabled", "disabled")],
    ["mobile microphone", yesNo(mobileCompanionState.remote_microphone_enabled, "enabled", "disabled")],
    ["notifications", yesNo(mobileCompanionState.mobile_notifications_enabled, "enabled", "disabled")],
    ["Hermes directo desde móvil", yesNo(mobileCompanionState.mobile_can_call_hermes_directly, "allowed", "forbidden")],
  ] as const;

  const financeRows = [
    ["coste real", metricValue(financeMetrics.actual_cost)],
    ["coste estimado", metricValue(financeMetrics.estimated_cost)],
    ["revenue confirmado", metricValue(financeMetrics.confirmed_revenue)],
    ["revenue proyectado", metricValue(financeMetrics.projected_revenue)],
    ["gross revenue", metricValue(financeMetrics.gross_revenue)],
    ["expenses", metricValue(financeMetrics.expenses)],
    ["net revenue", metricValue(financeMetrics.net_revenue)],
    ["ROI", metricValue(financeMetrics.roi)],
    ["budget", valueText(financeRoi.budget?.budget_configured, "not configured")],
  ] as const;

  const brainRows = [
    ["modo", valueText(memoryBrain.state?.mode, "visible_read_only_brain")],
    ["outcomes", valueText(memoryBrain.counts?.outcomes, "0")],
    ["failures", valueText(memoryBrain.counts?.failures, "0")],
    ["learning proposals", valueText(memoryBrain.counts?.learning_proposals, "0")],
    ["entidades", valueText(memoryBrain.counts?.entities ?? memoryBrain.entities?.length, "0")],
    ["facts", valueText(memoryBrain.counts?.facts ?? memoryBrain.facts?.length, "0")],
    ["preferencias", valueText(memoryBrain.counts?.preferences ?? memoryBrain.preferences?.length, "0")],
    ["decisiones", valueText(memoryBrain.counts?.decisions ?? memoryBrain.decisions?.length, "0")],
    ["proyectos", valueText(memoryBrain.counts?.projects ?? memoryBrain.projects?.length, "0")],
    ["contradicciones", valueText(memoryBrain.counts?.contradictions ?? memoryBrain.contradictions?.length, "0")],
    ["active memories", valueText(memoryBrain.counts?.active_memories, "0")],
    ["pending review", valueText(memoryBrain.counts?.pending_review, "0")],
    ["forgotten/deleted", valueText(memoryBrain.counts?.forgotten_deleted, "0")],
    ["compactación", valueText(memoryBrain.compaction?.status, "contract_only")],
    ["forget/delete", valueText(memoryBrain.forget_delete?.status, "future_gated")],
    ["autoload", yesNo(memoryBrain.state?.memory_autoload_enabled, "enabled", "disabled")],
  ] as const;

  const persistentAuditRows = [
    ["modo", valueText(persistentAudit.state?.mode, "in_memory_metadata_audit_ledger")],
    ["persistente", yesNo(persistentAudit.state?.persistent, "true", "false")],
    ["storage configured", yesNo(persistentAudit.state?.storage_configured, "true", "false")],
    ["eventos", valueText(persistentAudit.state?.event_count, "0")],
    ["tamper evident", yesNo(persistentAudit.state?.tamper_evident, "true", "false")],
    ["hash-chain", persistentAudit.chain?.valid === false ? "tamper_detected" : "valid"],
    ["checked", valueText(persistentAudit.chain?.checked_count, "0")],
    ["raw audio", yesNo(persistentAudit.safety?.contains_raw_audio, "present", "false")],
    ["camera frames", yesNo(persistentAudit.safety?.contains_camera_frame, "present", "false")],
    ["credentials", yesNo(persistentAudit.safety?.contains_credential, "present", "false")],
    ["full transcript", yesNo(persistentAudit.safety?.contains_full_transcript, "present", "false")],
    ["Hermes dispatch", yesNo(persistentAudit.safety?.hermes_dispatch_allowed, "allowed", "false")],
  ] as const;

  const safeAuditEntries = (persistentAudit.recent_entries ?? []).slice(0, 4);
  const memoryWhy = memoryBrain.explanation_preview?.why_jarvis_remembers?.length
    ? memoryBrain.explanation_preview.why_jarvis_remembers
    : memoryBrain.why_jarvis_remembers ?? ["JARVIS no tiene memoria personal persistida por defecto."];
  const memoryInfluence = memoryBrain.explanation_preview?.what_memory_influenced ?? ["No active memory influenced this preview."];
  const memoryPendingApproval = memoryBrain.explanation_preview?.pending_approval ?? [];

  const conversationalBrainRows = [
    ["modo", valueText(conversationalBrain.state?.mode, "local_deterministic_bridge")],
    ["LLM", yesNo(conversationalBrain.state?.llm_called, "called", "none")],
    ["provider externo", yesNo(conversationalBrain.state?.external_provider_called, "called", "false")],
    ["memoria autosave", yesNo(conversationalBrain.state?.memory_autosave_enabled, "enabled", "false")],
    ["Hermes dispatch", yesNo(conversationalBrain.state?.hermes_dispatch_allowed, "allowed", "false")],
    ["intent", valueText(brainPreview?.intent_detected)],
    ["confidence", valueText(brainPreview?.confidence)],
    ["risk", valueText(brainPreview?.risk_level)],
    ["approval", valueText(brainPreview?.approval_level)],
  ] as const;

  const conversationalIntakeRows = [
    ["modo", valueText(conversationalIntake.state?.mode, "prepare_only_conversational_intake")],
    ["source", valueText(intakeSample.intake?.source, "typed_text")],
    ["language", valueText(intakeSample.intake?.language, "unknown")],
    ["wake detected", yesNo(intakeSample.intake?.wake_phrase_detected, "true", "false")],
    ["sensitive request", yesNo(intakeSample.intake?.contains_sensitive_request, "true", "false")],
    ["clarification", yesNo(intakeSample.intake?.requires_clarification, "true", "false")],
    ["safe classify", yesNo(intakeSample.intake?.safe_to_classify, "true", "false")],
    ["safe preview", yesNo(intakeSample.intake?.safe_to_prepare_preview, "true", "false")],
    ["Hermes dispatch", yesNo(intakeSample.intake?.safe_to_dispatch_to_hermes, "allowed", "false")],
    ["intent", valueText(intakePreview.intent_detected)],
    ["risk", valueText(intakePreview.risk_level)],
    ["next", valueText(intakePreview.next_safe_action)],
  ] as const;

  const brainAdapterRows = [
    ["modo", valueText(brainAdapterState.mode, "safe_brain_adapter_prepare_only")],
    ["provider", valueText(brainAdapterState.current_provider, "deterministic_local")],
    ["provider mode", valueText(localBrainProvider?.provider_mode, "local_deterministic_prepare_only")],
    ["external enabled", yesNo(brainAdapterState.external_llm_enabled, "true", "false")],
    ["external called", yesNo(brainAdapterState.external_provider_called, "true", "false")],
    ["reads env", yesNo(brainAdapterState.reads_env, "true", "false")],
    ["network", yesNo(brainAdapterState.network_allowed, "true", "false")],
    ["Hermes dispatch", yesNo(brainAdapterState.hermes_dispatch_allowed, "allowed", "false")],
    ["disabled external", valueText(externalBrainProvider?.honest_status, "disabled_by_default_not_configured_not_called")],
    ["response intent", valueText(brainResponse.intent_detected)],
    ["response risk", valueText(brainResponse.risk_level)],
    ["response next", valueText(brainResponse.suggested_next_action)],
  ] as const;

  const doctorRows = [
    ["backend", yesNo(localDoctor.state?.backend_reachable, "reachable", "offline")],
    ["frontend route", valueText(localDoctor.state?.frontend_route_expected, "/jarvis")],
    ["dashboard", yesNo(localDoctor.state?.dashboard_status_endpoint, "ok", "missing")],
    ["event stream", yesNo(localDoctor.state?.event_stream_available ?? localDoctor.state?.event_stream_endpoint, "ok", "missing")],
    ["Hermes status", valueText(localDoctor.state?.hermes_status, yesNo(localDoctor.state?.hermes_status_endpoint, "ok", "missing"))],
    ["Python", valueText(localDoctorRuntime?.python_version)],
    ["platform", valueText(localDoctorRuntime?.system ?? localDoctorRuntime?.platform)],
    ["process", valueText(localDoctorProcess?.status)],
    ["STT navegador", valueText(localDoctor.state?.browser_stt, "client_side_unknown")],
    ["TTS navegador", valueText(localDoctor.state?.browser_tts, "client_side_unknown")],
    ["cámara navegador", valueText(localDoctor.state?.camera_support, "client_side_unknown")],
    ["WebGL", valueText(localDoctor.state?.webgl_support, "client_side_unknown")],
    ["ffmpeg", yesNo(localDoctor.optional_dependencies?.ffmpeg?.available, "available", "missing")],
    ["openWakeWord", yesNo(localDoctor.optional_dependencies?.openwakeword?.available, "available", "missing")],
    ["psutil", yesNo(localDoctor.optional_dependencies?.psutil?.available, "available", "unavailable")],
  ] as const;

  const phase3DoctorRows = [
    ["schema", valueText(localDoctor.schema_version, "jarvis.local_doctor.v1")],
    ["bind safe", yesNo(localDoctor.state?.local_bind_host_safe, "true", "false")],
    ["external bind", yesNo(localDoctor.state?.external_bind_enabled, "true", "false")],
    [".env read", yesNo(localDoctor.state?.env_file_read, "true", "false")],
    ["secrets exposed", yesNo(localDoctor.state?.secrets_exposed, "true", "false")],
    ["state dir", valueText((localDoctor.storage as Record<string, unknown> | undefined)?.state_dir)],
    ["node_modules", valueText((localDoctor.checks as Record<string, unknown>[] | undefined)?.find((check) => check.name === "node_modules_status")?.status)],
    ["package lock", valueText((localDoctor.checks as Record<string, unknown>[] | undefined)?.find((check) => check.name === "package_lock_unmodified")?.status)],
  ] as const;

  const remoteBridgeRows = [
    ["telegram", valueText(remoteBridgeFuture.telegram_bridge_status, "disabled_not_configured")],
    ["mobile", valueText(remoteBridgeFuture.mobile_bridge_status, "disabled_not_configured")],
    ["remote approval", yesNo(remoteBridgeFuture.remote_approval_allowed, "allowed", "false")],
    ["remote execution", yesNo(remoteBridgeFuture.remote_execution_allowed, "allowed", "false")],
    ["trusted pairing", yesNo(remoteBridgeFuture.trusted_pairing_required, "required", "unknown")],
    ["tokens loaded", yesNo(remoteBridgeFuture.tokens_loaded, "true", "false")],
    ["external calls", yesNo(remoteBridgeFuture.external_calls_made, "true", "false")],
  ] as const;

  const sensorLedgerRows = [
    ["schema", valueText(sensorLedger.schema_version, "jarvis.sensor_ledger.v1")],
    ["modo", valueText(sensorLedger.state?.mode, "read_only_sensor_metadata_ledger")],
    ["eventos", valueText(sensorLedger.state?.event_count, "0")],
    ["sensores", valueText(sensorLedger.state?.supported_sensors?.join?.(", "), "camera, recording, wake, voice_session, tts, stt")],
    ["retención", valueText(sensorLedger.retention?.storage, "metadata_only_in_memory")],
    ["raw audio", yesNo(sensorLedger.safety?.no_raw_audio, "blocked", "unknown")],
    ["frames", yesNo(sensorLedger.safety?.no_camera_frames, "blocked", "unknown")],
    ["secrets", yesNo(sensorLedger.safety?.no_credential_material, "blocked", "unknown")],
  ] as const;

  const eventStreamRows = [
    ["schema", valueText(eventBus.schema_version ?? events[0]?.schema_version, "jarvis.dashboard.events.v1")],
    ["snapshot", valueText(eventBus.snapshot_endpoint, "/mark-3/dashboard/events")],
    ["stream", valueText(eventBus.sse_endpoint, "/mark-3/dashboard/events/stream")],
    ["connection", eventConnectionState],
    ["heartbeat", yesNo(eventBus.heartbeat_enabled, "enabled", "unknown")],
    ["disconnect-safe", yesNo(eventBus.disconnect_safe, "true", "unknown")],
    ["read-only", yesNo(eventBus.read_only, "true", "unknown")],
    ["stream executes", yesNo(eventBus.stream_can_execute, "allowed", "false")],
  ] as const;

  const policyRows = [
    ["modo", valueText(policyStatus.state?.mode, "read_only_policy_status")],
    ["JARVIS", yesNo(policyStatus.state?.jarvis_governs, "gobierna", "unknown")],
    ["Hermes", yesNo(policyStatus.state?.hermes_executes, "ejecuta", "unknown")],
    ["wake approves", yesNo(policyStatus.state?.wake_phrase_never_approves, "never", "unknown")],
    ["frontend Hermes", yesNo(policyStatus.state?.frontend_executes_hermes_directly, "allowed", "forbidden")],
    ["sensor opt-in", yesNo(policyStatus.state?.sensors_require_opt_in, "required", "unknown")],
    ["direct", valueText(policyStatus.direct_allowed?.length, "0")],
    ["denied", valueText(policyStatus.denied?.length, "0")],
  ] as const;

  return (
    <details className="absolute bottom-6 left-6 z-50" data-testid="jarvis-command-center-tabs">
      <summary className="flex cursor-pointer items-center gap-3 border border-cyan-300/14 bg-[#020b17]/82 px-5 py-3 font-display text-xs uppercase tracking-[0.18em] text-cyan-100/68 shadow-[0_0_32px_rgba(34,211,238,0.08)] backdrop-blur">
        Sistemas
        <span className="text-cyan-300/70">•</span>
        <span>{modules.length} activos</span>
        <span className="sr-only">Detalles en pestañas</span>
        <span className="sr-only">max-h-[64vh] overflow-auto</span>
      </summary>

      <div className="absolute bottom-14 left-0 w-[min(72rem,calc(100vw-3rem))] border border-cyan-300/18 bg-[#020817]/96 p-4 shadow-[0_0_90px_rgba(34,211,238,0.18)] backdrop-blur-xl">
        <section className="mb-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]" data-testid="jarvis-secondary-controls">
          <article
            className="border border-cyan-300/12 bg-[#04101f]/60 p-4 xl:col-span-2"
            data-testid="jarvis-visual-qa-preview-controls"
            data-visual-qa-preview="local-front-end-only"
            data-visual-qa-no-hermes="true"
            data-visual-qa-no-sensors="true"
            data-visual-qa-no-direct-approval="true"
            data-visual-qa-no-backend-execution="true"
            data-visual-qa-query-param="jarvisVisualPreview"
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-cyan-50">Visual QA</h2>
                <p className="mt-1 font-mono-ui text-xs text-cyan-100/50">Estado visual: {resolvedVisualState}. Preview local, sin sensores ni ejecución.</p>
              </div>
              <Badge variant={visualPreviewState ? "warning" : "outline"}>{visualPreviewState ? `forced:${visualPreviewState}` : "auto"}</Badge>
            </div>
            <div className="mt-3 flex max-w-full gap-1 overflow-x-auto scrollbar-none" role="group" aria-label="Visual particle sphere preview states">
              <button
                type="button"
                aria-pressed={visualPreviewState === null}
                onClick={() => onVisualPreviewStateChange(null)}
                className={
                  "h-8 whitespace-nowrap border px-3 font-display text-[0.68rem] uppercase tracking-[0.12em] " +
                  (visualPreviewState === null ? "border-cyan-200/70 bg-cyan-300/18 text-cyan-50" : "border-cyan-300/12 bg-[#020b17]/70 text-cyan-100/56")
                }
              >
                Auto
              </button>
              {visualQaPreviewStates.map(([state, label]) => (
                <button
                  key={state}
                  type="button"
                  aria-pressed={visualPreviewState === state}
                  onClick={() => onVisualPreviewStateChange(state)}
                  className={
                    "h-8 whitespace-nowrap border px-3 font-display text-[0.68rem] uppercase tracking-[0.12em] " +
                    (visualPreviewState === state ? "border-cyan-200/70 bg-cyan-300/18 text-cyan-50" : "border-cyan-300/12 bg-[#020b17]/70 text-cyan-100/56")
                  }
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="sr-only">
              idle listening transcribing thinking speaking alert stopped visual QA preview states; no Hermes call, no sensor permission call, no direct approval action, no generic execute route
            </div>
          </article>
          <article className="border border-cyan-300/12 bg-[#04101f]/60 p-4" data-testid="jarvis-hermes-timeline-summary">
            <div className="mb-3 grid gap-3 lg:grid-cols-2">
              <div>
                <div className="flex items-center gap-2">
                  <TerminalSquare className="h-4 w-4 text-cyan-200/65" />
                  <h2 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-cyan-50">Hermes Execution</h2>
                </div>
                <p className="mt-2 font-mono-ui text-xs text-cyan-100/50">
                  {yesNo(hermesRuntime.active_execution, "ejecución activa", "Sin ejecución activa")}. El frontend no puede ejecutar Hermes directamente.
                </p>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-cyan-200/65" />
                  <h2 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-cyan-50">Live Timeline / Audit</h2>
                </div>
                <ol className="mt-2 max-h-24 space-y-2 overflow-auto pr-1">
                  {[...events.slice(0, 4), ...timeline.slice(0, 2)].slice(0, 5).map((event, index) => (
                    <li key={`${valueText("event_type" in event ? event.event_type : event.event)}-${index}`} className="grid grid-cols-[16px_1fr] gap-2">
                      <span className="mt-1 h-2.5 w-2.5 border border-cyan-200/70" />
                      <span className="font-mono-ui text-[0.7rem] text-cyan-100/55">
                        {"event_type" in event ? valueText(event.event_type) : valueText(event.event)} · {valueText(event.status)} · {valueText(event.source)}
                      </span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-4">
              <MiniStat label="approvals" value={valueText(approvals.pending_count)} variant="warning" />
              <MiniStat label="Hermes activo" value={yesNo(hermesRuntime.active_execution, "sí", "no")} variant={hermesRuntime.active_execution ? "destructive" : "success"} />
              <MiniStat label="event bus" value={eventConnectionState} variant={eventConnectionState === "stream" || eventConnectionState === "snapshot" ? "success" : "warning"} />
              <MiniStat label="backend" value={connectionState} variant={connectionState === "online" ? "success" : "warning"} />
            </div>
          </article>

          <article className="border border-cyan-300/12 bg-[#04101f]/60 p-4" data-testid="jarvis-agent-radar">
            <div className="mb-3 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Radar className="h-4 w-4 text-cyan-200/65" />
                <h2 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-cyan-50">Agent / Module Radar</h2>
              </div>
              <Badge variant="outline">{modules.length} modules</Badge>
            </div>
            <div className="grid max-h-52 gap-2 overflow-auto pr-1 sm:grid-cols-2 xl:grid-cols-3">
              {modules.map((module) => (
                <div key={module.name} className="border border-cyan-300/10 bg-[#071629]/45 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-display text-xs uppercase tracking-[0.1em] text-cyan-50">{module.name}</span>
                    <Badge variant={statusVariant(valueText(module.status))}>{valueText(module.status)}</Badge>
                  </div>
                  <p className="mt-2 line-clamp-2 font-mono-ui text-[0.7rem] text-cyan-100/45">{valueText(module.notes)}</p>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="border border-cyan-300/12 bg-[#04101f]/70 p-3" data-testid="jarvis-tab-detail-panel">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-display text-xs uppercase tracking-[0.12em] text-cyan-200/55">Detalles en pestañas</p>
              <p className="font-mono-ui text-xs text-cyan-100/45">
                La experiencia principal es la presencia; el contrato largo queda plegado y con scroll interno.
              </p>
            </div>
            <div className="flex max-w-full gap-1 overflow-x-auto scrollbar-none" role="tablist" aria-label="JARVIS command center modes">
              {commandCenterTabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={
                    "h-8 whitespace-nowrap border px-3 font-display text-[0.68rem] uppercase tracking-[0.12em] " +
                    (activeTab === tab.id
                      ? "border-cyan-200/70 bg-cyan-300/18 text-cyan-50"
                      : "border-cyan-300/12 bg-[#020b17]/70 text-cyan-100/56")
                  }
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-4 max-h-[64vh] overflow-auto pr-1">
            {activeTab === "cockpit" && (
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Visual Command Center Pilot</CardTitle>
                    <CardDescription>governed pilot · El dashboard no ejecuta Hermes directo.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-2 sm:grid-cols-2">
                      <SafetyLine>No se ejecuta Hermes desde el frontend.</SafetyLine>
                      <SafetyLine>No se activan sensores sin control manual explícito.</SafetyLine>
                      <SafetyLine>Approvals reales pasan por backend gobernado; no hay aprobación directa de frontend.</SafetyLine>
                      <SafetyLine>No hay métricas falsas.</SafetyLine>
                      <SafetyLine>Los valores sin evidencia se muestran como unknown.</SafetyLine>
                      <SafetyLine>Dependency hardening queda para una PR separada.</SafetyLine>
                    </div>
                    <ContractVault groups={contractCopyGroups} />
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Control de Misión</CardTitle>
                    <CardDescription>Preview conversation / Intent / Risk Preview.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <textarea
                      disabled
                      readOnly
                      aria-label="Control de Misión preview input"
                      placeholder={valueText(missionControl.sample_command, sampleMissionCommand)}
                      className="min-h-20 w-full resize-none border border-border bg-background/50 p-3 font-mono-ui text-xs text-muted-foreground disabled:opacity-70"
                    />
                    <div className="grid gap-2 sm:grid-cols-2">
                      <button disabled aria-disabled="true" type="button" className="border border-border bg-background/30 px-3 py-2 text-sm text-muted-foreground">Preparar preview</button>
                      <button disabled aria-disabled="true" type="button" className="border border-border bg-background/30 px-3 py-2 text-sm text-muted-foreground">Enviar a JARVIS</button>
                    </div>
                    <p className="font-display text-xs text-warning">En esta fase no se ejecuta nada.</p>
                    <StatusList
                      items={[
                        ["intención detectada", `${valueText(missionIntent.detected_intent)}/preview`],
                        ["confidence", valueText(missionIntent.confidence)],
                        ["mission type", valueText(missionIntent.mission_type)],
                        ["riesgo", valueText(missionIntent.risk_level)],
                        ["approval", valueText(missionIntent.approval_level)],
                      ]}
                    />
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Brain className="h-5 w-5 text-cyan-200/70" />
                      <CardTitle>Memory Brain v2</CardTitle>
                    </div>
                    <CardDescription>persistente/explicable · memoria nunca concede permisos.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={brainRows} />
                    <div className="grid gap-2 md:grid-cols-2">
                      {memoryWhy.slice(0, 3).map((reason) => (
                        <SafetyLine key={reason}>{reason}</SafetyLine>
                      ))}
                      {memoryInfluence.slice(0, 2).map((reason) => (
                        <SafetyLine key={reason}>{reason}</SafetyLine>
                      ))}
                      <SafetyLine>Pendiente approval/review: {memoryPendingApproval.length}</SafetyLine>
                      <SafetyLine>Memorias sensibles requieren approval; no hay autosave sensible.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <ScrollText className="h-5 w-5 text-cyan-200/70" />
                      <CardTitle>Persistent Audit</CardTitle>
                    </div>
                    <CardDescription>metadata-only hash-chain · voz / sensores / brain / intake.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={persistentAuditRows} />
                    <div className="grid gap-2">
                      {safeAuditEntries.length === 0 ? (
                        <SafetyLine>No hay entradas persistentes recientes en este read model.</SafetyLine>
                      ) : safeAuditEntries.map((entry, index) => (
                        <SafetyLine key={`${valueText(entry["audit_id"])}-${index}`}>
                          {valueText(entry["event_type"])} · {valueText(entry["surface"])} · {valueText(entry["risk_level"])} · metadata_only
                        </SafetyLine>
                      ))}
                      <SafetyLine>No guarda audio bruto, frames, secretos, credenciales ni transcripción completa.</SafetyLine>
                      <SafetyLine>Hash-chain tamper-evident: previous_hash + entry_hash.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Stethoscope className="h-5 w-5 text-cyan-200/70" />
                      <CardTitle>Doctor Local</CardTitle>
                    </div>
                    <CardDescription>diagnóstico read-only · no instala dependencias ni lee secretos.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={doctorRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Browser STT/TTS, cámara y WebGL se validan en cliente.</SafetyLine>
                      <SafetyLine>ffmpeg/openWakeWord son dependencias opcionales detectadas, no instaladas.</SafetyLine>
                      <SafetyLine>El doctor no ejecuta Hermes, no abre sensores y no lee .env.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Sensor Ledger</CardTitle>
                    <CardDescription>metadata-only · camera / recording / wake / voice_session / tts / stt.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={sensorLedgerRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Sensor Ledger solo registra metadata segura.</SafetyLine>
                      <SafetyLine>No guarda audio bruto, frames, vídeo, imágenes, tokens ni credenciales.</SafetyLine>
                      <SafetyLine>requested / started / stopped / cancelled / failed / deleted / retention_updated.</SafetyLine>
                      <SafetyLine>Sensores requieren opt-in, indicador visible, stop/cancel y auditoría.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Event Stream Health</CardTitle>
                    <CardDescription>schema_version / event_id / heartbeat · read-only SSE.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={eventStreamRows} />
                    <div className="grid gap-2">
                      <SafetyLine>El stream no ejecuta comandos.</SafetyLine>
                      <SafetyLine>No transporta secretos, audio bruto ni frames.</SafetyLine>
                      <SafetyLine>Heartbeat y snapshot son seguros ante desconexión.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Policy Status</CardTitle>
                    <CardDescription>JARVIS gobierna · Hermes ejecuta · frontend read-only.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={policyRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Wake phrase never approves.</SafetyLine>
                      <SafetyLine>Frontend never executes Hermes directly.</SafetyLine>
                      <SafetyLine>Dangerous execution requires ApprovalGateway, risk classification, audit and rollback/stop plan.</SafetyLine>
                      <SafetyLine>Denied: credential extraction, bypass, hidden sensors and frontend direct execution.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
                <Card data-testid="jarvis-phase-5-status">
                  <CardHeader>
                    <CardTitle>Phase 5 Trust Layer</CardTitle>
                    <CardDescription>persistent identity · pairing · voice approval · notifications.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={phase5Rows} />
                    <div className="grid gap-2 md:grid-cols-2">
                      <SafetyLine>Dispositivos confiables persisten en SQLite local y pueden revocarse.</SafetyLine>
                      <SafetyLine>Pairing usa nonce, TTL, scope exacto, one-time use y rate limiting.</SafetyLine>
                      <SafetyLine>La voz solo aprueba con sesión válida, device trusted, readback exacto, challenge y audit.</SafetyLine>
                      <SafetyLine>Wake phrase alone never approves.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === "approvals" && (
              <div className="grid gap-4 xl:grid-cols-2">
                <Card data-testid="jarvis-trusted-approval-channels">
                  <CardHeader>
                    <CardTitle>Trusted Approval Channels</CardTitle>
                    <CardDescription>Canales locales confiables; voz/wake/remoto no conceden approval.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={trustedChannelRows} />
                    <div className="grid gap-2 md:grid-cols-2">
                      {trustedChannelItems.map((channel) => (
                        <div key={valueText(channel.channel_id)} className="border border-border/70 bg-background/35 p-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-display text-xs uppercase tracking-[0.12em]">{valueText(channel.channel_id)}</p>
                            <Badge variant={Boolean(channel.enabled) ? "success" : "outline"}>{yesNo(channel.enabled, "enabled", "disabled")}</Badge>
                          </div>
                          <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">
                            {valueText(channel.channel_type)} · risk {valueText(channel.risk_limit)} · trusted {yesNo(channel.trusted)}
                          </p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            <Badge variant={Boolean(channel.can_grant_strong) ? "success" : "outline"}>strong {yesNo(channel.can_grant_strong, "yes", "no")}</Badge>
                            <Badge variant={Boolean(channel.can_grant_double) ? "success" : "outline"}>double {yesNo(channel.can_grant_double, "yes", "no")}</Badge>
                            <Badge variant={Boolean(channel.can_grant_triple) ? "warning" : "outline"}>triple {yesNo(channel.can_grant_triple, "yes", "no")}</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-phase-5-trusted-devices">
                  <CardHeader>
                    <CardTitle>Persistent Trusted Devices</CardTitle>
                    <CardDescription>Identidad durable local; import/deserialization no puede crear trust.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={trustedDeviceRows} />
                    <div className="grid gap-2 md:grid-cols-2">
                      {trustedDeviceItems.map((device) => (
                        <div key={valueText(device.device_id)} className="border border-border/70 bg-background/35 p-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-display text-xs uppercase tracking-[0.12em]">{valueText(device.display_name, valueText(device.device_id))}</p>
                            <Badge variant={Boolean(device.revoked) ? "destructive" : Boolean(device.trusted) ? "success" : "outline"}>
                              {Boolean(device.revoked) ? "revoked" : yesNo(device.trusted, "trusted", "untrusted")}
                            </Badge>
                          </div>
                          <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">
                            {valueText(device.channel_type)} · scope {valueText((device.approval_scope as unknown[] | undefined)?.join?.(", "), "none")} · last_seen {valueText(device.last_seen_at, "none")}
                          </p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            <Badge variant="outline">fingerprint hash</Badge>
                            <Badge variant={Boolean(device.can_voice_approve) ? "warning" : "outline"}>voice {yesNo(device.can_voice_approve, "yes", "no")}</Badge>
                            <Badge variant={Boolean(device.can_grant_triple) ? "warning" : "outline"}>triple {yesNo(device.can_grant_triple, "yes", "no")}</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-phase-5-triple-approval">
                  <CardHeader>
                    <CardTitle>Triple Approval Persistent Gate</CardTitle>
                    <CardDescription>Device identity, action id, scope, expiry, no replay and audit chain.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={tripleApprovalRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Critical approvals require three persistent trusted local identities.</SafetyLine>
                      <SafetyLine>Each step is bound to an exact channel, readback and challenge.</SafetyLine>
                      <SafetyLine>Revoked devices cannot satisfy triple approval after restart.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-local-pairing-status">
                  <CardHeader>
                    <CardTitle>Local Pairing</CardTitle>
                    <CardDescription>Short-lived challenge · nonce · exact scope · rate limit.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={localPairingRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Pairing does not call Hermes and cannot enable remote execution.</SafetyLine>
                      <SafetyLine>Pairing creates only scoped trusted identity after exact local challenge.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-notification-readiness">
                  <CardHeader>
                    <CardTitle>Notification Readiness</CardTitle>
                    <CardDescription>Local contracts only; remote channels remain notification-only readiness.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={notificationRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Approval pending, pairing, trust/revoke, blocked action, expiry and voice decisions are modeled.</SafetyLine>
                      <SafetyLine>No Telegram/mobile remote execution is enabled by this readiness layer.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-double-approval-steps">
                  <CardHeader>
                    <CardTitle>Double Approval Steps</CardTitle>
                    <CardDescription>Dos pasos independientes, readback y challenge obligatorio.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={doubleApprovalRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Step 1 y step 2 usan el mismo approval_id con step_id diferente.</SafetyLine>
                      <SafetyLine>No se reutilizan approvals ya decididos o usados.</SafetyLine>
                      <SafetyLine>Triple queda bloqueado hasta tener otro canal confiable independiente.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                {approvalCards.map((card) => (
                  <Card key={card.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between gap-3">
                        <CardTitle>{card.title}</CardTitle>
                        <Badge variant={statusVariant(valueText(card.status))}>{valueText(card.status)}</Badge>
                      </div>
                      <CardDescription>{card.action}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <StatusList
                        items={[
                          ["risk", valueText(card.risk_level)],
                          ["approval", valueText(card.approval_level)],
                          ["scope", valueText(card.scope_summary)],
                          ["rollback", valueText(card.rollback_plan)],
                          ["stop", valueText(card.stop_plan)],
                        ]}
                      />
                      <SafetyLine>Readback / confirmación fuerte: {card.requires_readback ? "required" : "not required"}</SafetyLine>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {activeTab === "hermes" && (
              <div className="grid gap-4">
                <article className="border border-warning/40 bg-warning/10 p-4">
                  <p className="font-display text-sm text-warning">JARVIS gobierna. Hermes ejecuta.</p>
                  <p className="mt-1 font-mono-ui text-xs text-warning">El frontend no puede ejecutar Hermes directamente.</p>
                  <p className="mt-3 font-mono-ui text-xs text-foreground">Sin ejecución activa. No hay ejecución real que detener desde este panel.</p>
                </article>
                <StatusList items={hermesRows} />
                <div className="grid gap-2 md:grid-cols-3">
                  <SafetyLine>Capacidades gobernadas.</SafetyLine>
                  <SafetyLine>Rutas bloqueadas.</SafetyLine>
                  <SafetyLine>Requisitos antes de ejecución futura: approval válido, scope exacto, coste/impacto, operador humano.</SafetyLine>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div className="border border-border/70 bg-background/35 p-4">
                    <BadgeCheck className="mb-3 h-5 w-5 text-success" />
                    <p className="font-mono-ui text-sm">JARVIS gobierna intención, riesgo, policy, approval y auditoría.</p>
                  </div>
                  <div className="border border-border/70 bg-background/35 p-4">
                    <TerminalSquare className="mb-3 h-5 w-5 text-muted-foreground" />
                    <p className="font-mono-ui text-sm">Hermes ejecuta solo cuando JARVIS entrega gates válidos.</p>
                  </div>
                  <div className="border border-border/70 bg-background/35 p-4">
                    <ZapOff className="mb-3 h-5 w-5 text-warning" />
                    <p className="font-mono-ui text-sm">Esta pantalla pide approvals al backend gobernado; no llama a Hermes directo.</p>
                  </div>
                </div>
                <Card data-testid="jarvis-action-catalog-drawer">
                  <CardHeader>
                    <CardTitle>Action Catalog Allowlist</CardTitle>
                    <CardDescription>Phase 7 action catalog status; no shell libre ni comandos arbitrarios.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={phase2Rows} />
                    <StatusList items={phase7Rows} />
                    <StatusList items={phase7AdapterRows} />
                    <StatusList items={stopRollbackRows} />
                    <div className="grid gap-2 lg:grid-cols-2">
                      {actionCatalogItems.length === 0 ? (
                        <SafetyLine>No hay catálogo cargado en este snapshot.</SafetyLine>
                      ) : actionCatalogItems.map((action: JarvisActionContract) => (
                        <div key={valueText(action.action_key)} className="border border-border/70 bg-background/35 p-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-display text-xs uppercase tracking-[0.12em] text-foreground">{valueText(action.action_key)}</p>
                            <Badge variant={statusVariant(valueText(action.risk_level))}>{valueText(action.risk_level)}</Badge>
                          </div>
                          <p className="mt-2 line-clamp-2 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(action.description)}</p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            <Badge variant="outline">approval {valueText(action.approval_required)}</Badge>
                            <Badge variant={action.stop_supported ? "success" : "outline"}>stop {yesNo(action.stop_supported, "supported", "unsupported")}</Badge>
                            <Badge variant={action.rollback_supported ? "success" : "outline"}>rollback {valueText(action.rollback_status)}</Badge>
                            <Badge variant={action.network_allowed ? "warning" : "success"}>network {yesNo(action.network_allowed, "allowed", "false")}</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="grid gap-2 md:grid-cols-3">
                      <SafetyLine>Allowlist-only; UI no acepta comandos libres.</SafetyLine>
                      <SafetyLine>Outputs pasan por redacción antes de llegar al dashboard.</SafetyLine>
                      <SafetyLine>Secrets, tokens, cookies, passwords y .env quedan denied.</SafetyLine>
                      <SafetyLine>Filesystem writes require backend approval and backup-before-overwrite.</SafetyLine>
                      <SafetyLine>Browser automation is readiness/plan-only; no hidden browser.</SafetyLine>
                      <SafetyLine>Sandbox uses command IDs only; no freeform shell.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === "voice" && (
              <div className="grid gap-4">
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Activity className="h-5 w-5 text-warning" />
                      <CardTitle>Núcleo de Voz JARVIS</CardTitle>
                    </div>
                    <CardDescription>Local Voice Loop con SpeechRecognition/speechSynthesis si el navegador lo soporta. Sin audio bruto al backend ni approvals por voz.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={voiceRows} />
                    <StatusList items={voiceRuntimePackRows} />
                    <StatusList items={phase2VoiceRows} />
                    <StatusList items={voiceSessionRows} />
                    <StatusList items={localVoiceRows} />
                    <article className="border border-warning/40 bg-warning/10 p-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="warning">Local Voice Loop</Badge>
                        <Badge variant={conversationActive ? "warning" : "outline"}>conversation_active={conversationActive ? "true" : "false"}</Badge>
                        <Badge variant="success">raw_audio_sent_to_backend=false</Badge>
                        <Badge variant="success">transcript_persistence=false</Badge>
                        <Badge variant="outline">provider browser/manual</Badge>
                        <Badge variant="outline">recording={valueText(rawAudioRecording.state?.recording_active, "false")}</Badge>
                        <Badge variant="outline">raw recorder {valueText(rawAudioRecording.state?.mode, "browser_local_recorder")}</Badge>
                      </div>
                      <p className="mt-3 font-mono-ui text-sm text-foreground">{coreSubtitle}</p>
                      <p className="mt-2 font-display text-xs text-warning">
                        Soporte dependiente del navegador; SpeechRecognition puede usar servicios del navegador. Esta UI no guarda audio bruto ni lo sube al backend.
                      </p>
                      <p className="mt-2 font-mono-ui text-xs text-foreground">
                        Conversación manual continua: David pulsa una vez, JARVIS escucha, responde y vuelve a escuchar hasta stop/cancel o timeout.
                      </p>
                    </article>
                    <article className="border border-cyan-300/15 bg-[#061526]/50 p-4">
                      <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-cyan-100">Conversational Brain Bridge v2</h3>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <StatusList items={conversationalBrainRows} />
                        <div className="grid gap-2">
                          <SafetyLine>Respuesta humana breve; detalles técnicos plegados.</SafetyLine>
                          <SafetyLine>No LLM real declarado si no se llama a un LLM.</SafetyLine>
                          <SafetyLine>No memoria automática.</SafetyLine>
                          <SafetyLine>No Hermes dispatch desde este bridge.</SafetyLine>
                        </div>
                      </div>
                    </article>
                    <article className="border border-cyan-300/15 bg-[#061526]/50 p-4">
                      <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-cyan-100">Conversational Intake Pipeline</h3>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <StatusList items={conversationalIntakeRows} />
                        <div className="grid gap-2">
                          <SafetyLine>Normaliza texto escrito, transcripción de voz, wake phrase y canales futuros.</SafetyLine>
                          <SafetyLine>Detecta wake phrase, baja confianza, ambigüedad y material sensible antes de preview.</SafetyLine>
                          <SafetyLine>safe_to_dispatch_to_hermes=false.</SafetyLine>
                          <SafetyLine>Approval no es ejecución.</SafetyLine>
                        </div>
                      </div>
                    </article>
                    <article className="border border-cyan-300/15 bg-[#061526]/50 p-4">
                      <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-cyan-100">LLM Brain Adapter</h3>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <StatusList items={brainAdapterRows} />
                        <div className="grid gap-2">
                          <SafetyLine>Provider actual: deterministic_local.</SafetyLine>
                          <SafetyLine>External LLM disabled; external_provider_called=false.</SafetyLine>
                          <SafetyLine>No lee entorno, no usa red, no persiste prompts privados.</SafetyLine>
                          <SafetyLine>No prepara Hermes dispatch; solo respuesta humana y preview candidato.</SafetyLine>
                        </div>
                      </div>
                    </article>
                    <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
                      <SafetyLine>micrófono: manual bajo botón explícito</SafetyLine>
                      <SafetyLine>wake_listening: false</SafetyLine>
                      <SafetyLine>approval_by_voice_enabled=false</SafetyLine>
                      <SafetyLine>Stop cancela escucha y speechSynthesis.</SafetyLine>
                    </div>
                    <article className="border border-warning/40 bg-warning/10 p-4">
                      <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-warning">Wake Word Local Safe Flow</h3>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <StatusList
                          items={[
                            ["micrófono hard-off", yesNo(wakeWordFlow.state?.microphone_hard_off, "true", "false")],
                            ["wake runtime", yesNo(wakeWordFlow.state?.wake_runtime_enabled, "enabled", "disabled")],
                            ["typed wake preview", yesNo(wakeWordFlow.state?.typed_wake_preview_enabled, "enabled", "disabled")],
                            ["background listener", yesNo(wakeWordFlow.state?.background_listener_enabled, "enabled", "disabled")],
                          ]}
                        />
                        <div className="grid gap-2">
                          <SafetyLine>Wake phrase is not permission.</SafetyLine>
                          <SafetyLine>wake listening sin grabación ni transcripción continua.</SafetyLine>
                          <SafetyLine>La wake phrase nunca aprueba acciones.</SafetyLine>
                          <SafetyLine>La wake phrase no ejecuta acciones.</SafetyLine>
                          <SafetyLine>La wake phrase solo puede abrir una ventana de comando futura.</SafetyLine>
                          <SafetyLine>La aprobación por voz requiere canal autenticado, readback y auditoría.</SafetyLine>
                        </div>
                      </div>
                    </article>
                    <article className="border border-cyan-300/15 bg-[#061526]/50 p-4" data-testid="jarvis-voice-approval-contract">
                      <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-cyan-100">Spoken Permission Contract</h3>
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <StatusList items={voiceApprovalRows} />
                        <div className="grid gap-2">
                          <SafetyLine>“JARVIS, autorizo”, “JARVIS, confirmo” y “JARVIS, apruebo esta acción” solo son válidas dentro de una sesión activa gobernada.</SafetyLine>
                          <SafetyLine>Acciones de riesgo alto requieren challenge exacto; critical/triple no baja de riesgo por voz.</SafetyLine>
                          <SafetyLine>“JARVIS, cancela” y “JARVIS, deniega” cierran la decisión como denegada.</SafetyLine>
                          <SafetyLine>No se guarda audio bruto ni transcript completo por defecto.</SafetyLine>
                        </div>
                      </div>
                    </article>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === "vision" && (
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Camera className="h-5 w-5 text-muted-foreground" />
                      <CardTitle>Cámara / Visión</CardTitle>
                    </div>
                    <CardDescription><span className="font-display text-warning">preview-only</span> · La cámara no graba por defecto. La visión solo se activa con permiso explícito.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={cameraRows} />
                    <div className="grid gap-2">
                      <SafetyLine>no camera activation on load: {yesNo(cameraVisionPrivacy.no_camera_activation_on_load)}</SafetyLine>
                      <SafetyLine>manual getUserMedia only: {yesNo(cameraVisionPrivacy.get_user_media_button_gated)}</SafetyLine>
                      <SafetyLine>no recording: {yesNo(cameraVisionPrivacy.no_recording)}</SafetyLine>
                      <SafetyLine>video recording manual opt-in only: {yesNo(cameraVisionPrivacy.video_recording_manual_opt_in_only)}</SafetyLine>
                      <SafetyLine>video recorder inactive on load: {yesNo(cameraVisionPrivacy.video_recording_inactive_on_load)}</SafetyLine>
                      <SafetyLine>video download/delete local only: {yesNo(cameraVisionPrivacy.video_recording_local_download_delete_only)}</SafetyLine>
                      <SafetyLine>no snapshot: {yesNo(cameraVisionPrivacy.no_snapshot_capture)}</SafetyLine>
                      <SafetyLine>no image/video storage: {cameraVisionPrivacy.no_image_storage && cameraVisionPrivacy.no_video_storage ? "true" : "false"}</SafetyLine>
                      <SafetyLine>No hay proveedor externo de visión.</SafetyLine>
                      <SafetyLine>No se sube vídeo al backend.</SafetyLine>
                      <SafetyLine>explicit operator permission required: {yesNo(cameraVisionPrivacy.explicit_operator_permission_required)}</SafetyLine>
                      <SafetyLine>visual indicator required: {yesNo(cameraVisionPrivacy.visual_indicator_required_when_camera_active)}</SafetyLine>
                      <SafetyLine>audit required: {yesNo(cameraVisionPrivacy.audit_required_for_future_vision)}</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Smartphone className="h-5 w-5 text-success" />
                      <CardTitle>Mobile Companion</CardTitle>
                    </div>
                    <CardDescription><span className="font-display text-warning">preview-only</span> · Mobile es una interfaz, no un runtime. Mobile no llama a Hermes directamente.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={mobileRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Mobile es una interfaz, no un runtime.</SafetyLine>
                      <SafetyLine>Mobile no llama a Hermes directamente.</SafetyLine>
                      <SafetyLine>Mobile no ejecuta acciones.</SafetyLine>
                      <SafetyLine>Approvals reales desde móvil quedan future-gated.</SafetyLine>
                      <SafetyLine>No se guardan credenciales ni tokens.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Radar className="h-5 w-5 text-warning" />
                      <CardTitle>Phase 8 Remote Channels</CardTitle>
                    </div>
                    <CardDescription>Remote channels are governed interfaces, not Hermes runtimes.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={phase8Rows} />
                    <StatusList items={remoteChannelRows} />
                    <StatusList items={telegramReadinessRows} />
                    <StatusList items={mobileApprovalRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Remote channels must send intent into JARVIS Gateway/control plane.</SafetyLine>
                      <SafetyLine>Frontend and remote channels never call Hermes directly.</SafetyLine>
                      <SafetyLine>Telegram readiness does not run a bot automatically.</SafetyLine>
                      <SafetyLine>Telegram token presence is redacted; token value is never shown.</SafetyLine>
                      <SafetyLine>Mobile approval center is preview/readback/challenge only; it does not execute or approve real actions directly.</SafetyLine>
                      <SafetyLine>Remote approval intent requires paired trusted device, exact readback, challenge, expiration, anti-replay and audit.</SafetyLine>
                      <SafetyLine>Remote execution is disabled by default.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === "finance" && (
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <CircleDollarSign className="h-5 w-5 text-warning" />
                      <CardTitle>Finance / ROI</CardTitle>
                    </div>
                    <CardDescription>Métricas financieras solo con evidencia.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={financeRows} />
                    <div className="grid gap-2">
                      <SafetyLine>No fake metrics.</SafetyLine>
                      <SafetyLine>Si no hay evidencia, mostrar unknown.</SafetyLine>
                      <SafetyLine>Revenue confirmado requiere evidencia.</SafetyLine>
                      <SafetyLine>ROI queda unknown sin revenue y costes reales.</SafetyLine>
                      <SafetyLine>No se mueve dinero desde este panel.</SafetyLine>
                      <SafetyLine>Stripe live requiere aprobación fuerte.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Workflow className="h-5 w-5 text-success" />
                      <CardTitle>Product Builder Adaptativo</CardTitle>
                    </div>
                    <CardDescription>Flujo visual de producto; sin deploy, Stripe ni revenue real.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                      {productStages.map((stage) => (
                        <div key={stage.name} className="border border-border/70 bg-background/35 p-3">
                          <p className="font-display text-xs uppercase tracking-[0.1em]">{stage.name}</p>
                          <Badge className="mt-2" variant={statusVariant(valueText(stage.status))}>{valueText(stage.status)}</Badge>
                        </div>
                      ))}
                    </div>
                    <p className="font-display text-xs text-warning">preview / future-gated / disabled</p>
                    <div className="grid gap-2">
                      <SafetyLine>No es un Template Builder.</SafetyLine>
                      <SafetyLine>Si dos productos parecen clones, el builder ha fallado.</SafetyLine>
                      <SafetyLine>Deploy real requiere aprobación fuerte.</SafetyLine>
                      <SafetyLine>Stripe/checkout real requiere aprobación fuerte.</SafetyLine>
                      <SafetyLine>Revenue real requiere confirmación.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <BadgeCheck className="h-5 w-5 text-warning" />
                      <CardTitle>Phase 8 External Ops</CardTitle>
                    </div>
                    <CardDescription>Deploy, email and payment candidates are prepare-only envelopes.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={externalOpsRows} />
                    <StatusList items={externalBudgetRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Deploy candidate is dry-run/prepare-only by default; no production deploy, DNS change or secret read.</SafetyLine>
                      <SafetyLine>Email candidate previews recipients, subject, body and attachments as metadata only; real send is disabled by default.</SafetyLine>
                      <SafetyLine>Stripe live mode is blocked by default; payment candidate does not move money.</SafetyLine>
                      <SafetyLine>Projected revenue and confirmed revenue stay separate.</SafetyLine>
                      <SafetyLine>Confirmed revenue requires evidence/source; fake revenue is blocked.</SafetyLine>
                      <SafetyLine>Budget guard consumes budget only from confirmed evidence, not estimates.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === "pilot" && (
              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Cpu className="h-5 w-5 text-muted-foreground" />
                      <CardTitle>Frontend Pilot / Hardening</CardTitle>
                    </div>
                    <CardDescription>Pilot backend-gated para /jarvis; el dashboard no ejecuta Hermes directo.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList
                      items={[
                        ["mode", valueText(frontendPilot.state?.mode, "governed_pilot")],
                        ["route", valueText(frontendPilot.state?.dashboard_route, "/jarvis")],
                        ["endpoint", valueText(frontendPilot.state?.backend_status_endpoint, DASHBOARD_READ_MODEL_ENDPOINT)],
                        ["execute", yesNo(frontendPilot.state?.frontend_can_execute, "true", "false")],
                        ["sensors", yesNo(frontendPilot.state?.frontend_can_activate_sensors, "true", "false")],
                        ["npm audit vulnerabilities observed", valueText(frontendPilot.hardening_notes?.npm_audit_vulnerabilities_observed)],
                        ["full pytest required before merge", yesNo(frontendPilot.hardening_notes?.full_pytest_required_before_merge, "true", "false")],
                      ]}
                    />
                    <div className="grid gap-2">
                      <SafetyLine>Pilot backend-gated</SafetyLine>
                      <SafetyLine>El dashboard no ejecuta Hermes directo.</SafetyLine>
                      <SafetyLine>POST solo a endpoints gobernados.</SafetyLine>
                      <SafetyLine>No execute.</SafetyLine>
                      <SafetyLine>No sensores sin activación manual.</SafetyLine>
                      <SafetyLine>Dependency hardening queda para una PR separada.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-local-runtime-readiness">
                  <CardHeader>
                    <CardTitle>Phase 3 / Local Runtime</CardTitle>
                    <CardDescription>Daemon local, tray readiness y canales confiables sin auto mic/camera/wake.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={phase2Rows} />
                    <StatusList items={phase3Rows} />
                    <StatusList items={phase7Rows} />
                    <StatusList items={localRuntimeRows} />
                    <div className="grid gap-2 md:grid-cols-2">
                      <SafetyLine>Daemon local corre embebido en backend; no se instala servicio.</SafetyLine>
                      <SafetyLine>Tray queda capability model; no auto-start sin opt-in.</SafetyLine>
                      <SafetyLine>background_listening_enabled=false.</SafetyLine>
                      <SafetyLine>user_opt_in_required=true.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-phase-4-status">
                  <CardHeader>
                    <CardTitle>Phase 4 Status</CardTitle>
                    <CardDescription>Local controller + remote pairing readiness, sin ejecución remota peligrosa.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={phase4Rows} />
                    <div className="grid gap-2 md:grid-cols-2">
                      <SafetyLine>JARVIS gobierna; Hermes ejecuta solo detrás de gates válidos.</SafetyLine>
                      <SafetyLine>Remote pairing, remote approval y remote execution siguen false.</SafetyLine>
                      <SafetyLine>No se lee .env ni tokens.</SafetyLine>
                      <SafetyLine>No hay servicio del sistema, autostart ni puerto externo.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-local-controller-status">
                  <CardHeader>
                    <CardTitle>Local Controller</CardTitle>
                    <CardDescription>Controller local opt-in; contrato realista sin instalación nativa.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={localControllerRows} />
                    <div className="grid gap-2 md:grid-cols-2">
                      <SafetyLine>local_only=true y bind_host=127.0.0.1.</SafetyLine>
                      <SafetyLine>auto_start_enabled=false.</SafetyLine>
                      <SafetyLine>installed_as_system_service=false.</SafetyLine>
                      <SafetyLine>startup_integration_enabled=false.</SafetyLine>
                      <SafetyLine>user_opt_in_required=true.</SafetyLine>
                      <SafetyLine>no_background_capture=true.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-trusted-devices-status">
                  <CardHeader>
                    <CardTitle>Trusted Devices</CardTitle>
                    <CardDescription>Identidad de controller/dispositivo; remoto cero/untrusted por defecto.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={trustedDeviceRows} />
                    <div className="grid gap-2 md:grid-cols-2">
                      {trustedDeviceItems.map((device) => (
                        <div key={valueText(device.device_id)} className="border border-border/70 bg-background/35 p-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-display text-xs uppercase tracking-[0.12em]">{valueText(device.display_name ?? device.device_id)}</p>
                            <Badge variant={Boolean(device.trusted) ? "success" : "outline"}>{yesNo(device.trusted, "trusted", "untrusted")}</Badge>
                          </div>
                          <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">
                            {valueText(device.channel_type)} · paired {yesNo(device.paired)} · verified {yesNo(device.verified)} · risk {valueText(device.risk_limit)}
                          </p>
                        </div>
                      ))}
                    </div>
                    <div className="grid gap-2">
                      <SafetyLine>Revoked devices cannot approve.</SafetyLine>
                      <SafetyLine>Voz y wake no conceden permisos.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-triple-approval-readiness">
                  <CardHeader>
                    <CardTitle>Triple Approval Readiness</CardTitle>
                    <CardDescription>Tres pasos/canales separados, challenge, readback, expiry y anti-reuse.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={tripleApprovalRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Un solo canal repetido no satisface triple approval.</SafetyLine>
                      <SafetyLine>Critical queda blocked si no existen tres canales locales verificados.</SafetyLine>
                      <SafetyLine>La policy se recalcula antes de la decisión final.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-local-daemon-status">
                  <CardHeader>
                    <CardTitle>Local Daemon</CardTitle>
                    <CardDescription>Contrato local-only; stop/restart honestamente unsupported en runtime embebido.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={daemonRows} />
                    <div className="grid gap-2 md:grid-cols-2">
                      <SafetyLine>bind_host=127.0.0.1, sin puertos externos.</SafetyLine>
                      <SafetyLine>auto_start=false y background_listening=false.</SafetyLine>
                      <SafetyLine>mic_auto_start=false, camera_auto_start=false, wake_auto_start=false.</SafetyLine>
                      <SafetyLine>Stop/restart no se fingen si el proceso embebido no puede autocontrolarse.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-tray-readiness">
                  <CardHeader>
                    <CardTitle>Tray / Local Controller</CardTitle>
                    <CardDescription>Readiness de tray sin dependencia nativa pesada.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={trayRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Tray nativo no instalado.</SafetyLine>
                      <SafetyLine>Puede mostrar status/approval como contrato futuro.</SafetyLine>
                      <SafetyLine>No hay captura en background.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-phase-3-local-doctor">
                  <CardHeader>
                    <CardTitle>Local Doctor Phase 3</CardTitle>
                    <CardDescription>Checks locales seguros; no lee .env ni secretos.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={phase3DoctorRows} />
                    <div className="grid gap-2">
                      <SafetyLine>Comprueba imports, bind local, state/audit/history y build artifacts si existen.</SafetyLine>
                      <SafetyLine>Browser, voz y wake quedan unknown/manual cuando el backend no puede verificarlos sin sensores.</SafetyLine>
                      <SafetyLine>No ejecuta scanners pesados ni instala dependencias.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-remote-bridge-future-readiness">
                  <CardHeader>
                    <CardTitle>Telegram / Mobile Future Bridge</CardTitle>
                    <CardDescription>Readiness disabled; sin tokens, llamadas externas ni ejecución remota.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={remoteBridgeRows} />
                    <div className="grid gap-2">
                      <SafetyLine>remote_approval_allowed=false.</SafetyLine>
                      <SafetyLine>remote_execution_allowed=false.</SafetyLine>
                      <SafetyLine>trusted_pairing_required=true para una fase futura.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-remote-pairing-readiness">
                  <CardHeader>
                    <CardTitle>Remote Pairing Readiness</CardTitle>
                    <CardDescription>Pairing remoto preparado, pero desactivado por defecto.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={remotePairingRows} />
                    <div className="grid gap-2">
                      <SafetyLine>remote_pairing_enabled=false.</SafetyLine>
                      <SafetyLine>remote_approval_allowed=false.</SafetyLine>
                      <SafetyLine>remote_execution_allowed=false.</SafetyLine>
                      <SafetyLine>prepare solo crea challenge local efímero y metadata-only.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-telegram-bridge-readiness">
                  <CardHeader>
                    <CardTitle>Telegram / Hermes Bridge Readiness</CardTitle>
                    <CardDescription>Bridge futuro disabled/not_configured; no bot, no webhook, no token read.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={telegramBridgeRows} />
                    <div className="grid gap-2">
                      <SafetyLine>token_present=unknown_redacted.</SafetyLine>
                      <SafetyLine>No se llama Telegram y no se inicia bot.</SafetyLine>
                      <SafetyLine>No puede pedir approval ni ejecutar hasta pairing + policy + approval futuro.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-stop-rollback-v2">
                  <CardHeader>
                    <CardTitle>Stop / Rollback v2</CardTitle>
                    <CardDescription>Observabilidad metadata-only; rollback destructivo no se ejecuta ni se finge.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={stopRollbackV2Rows} />
                    <div className="grid gap-2">
                      <SafetyLine>Stop registra actor, canal, scope, deadline y estado final.</SafetyLine>
                      <SafetyLine>Rollback destructivo requiere preconditions y approval; aquí solo dry-run metadata.</SafetyLine>
                      <SafetyLine>No se finge rollback si no hay soporte real.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-execution-history-drawer">
                  <CardHeader>
                    <CardTitle>Execution History</CardTitle>
                    <CardDescription>Historial metadata-only de ejecuciones gobernadas.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList
                      items={[
                        ["status", executionHistoryStatus.metadata_only ? "metadata_only" : valueText(executionHistoryStatus.available, "metadata_only")],
                        ["count", valueText(executionHistoryStatus.record_count, "0")],
                        ["contains_secret", yesNo(executionHistoryStatus.contains_secret, "true", "false")],
                        ["contains_raw_audio", yesNo(executionHistoryStatus.contains_raw_audio, "true", "false")],
                        ["contains_camera_frame", yesNo(executionHistoryStatus.contains_camera_frame, "true", "false")],
                      ]}
                    />
                    <div className="grid gap-2">
                      {executionHistoryItems.length === 0 ? (
                        <SafetyLine>No hay ejecuciones recientes en este snapshot.</SafetyLine>
                      ) : executionHistoryItems.map((item: JarvisExecutionHistoryItem, index: number) => (
                        <div key={`${valueText(item.execution_id)}-${index}`} className="border border-border/70 bg-background/35 p-3">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-display text-xs uppercase tracking-[0.12em]">{valueText(item.action_key)}</p>
                            <Badge variant={statusVariant(valueText(item.status))}>{valueText(item.status)}</Badge>
                          </div>
                          <p className="mt-2 line-clamp-2 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(item.result_summary ?? item.error_summary ?? item.intent_summary)}</p>
                          <p className="mt-2 font-mono-ui text-[0.66rem] text-muted-foreground">
                            risk {valueText(item.risk_level)} · approval {valueText(item.approval_level)} · duration {valueText(item.duration_ms)}ms · redaction {valueText(item.redaction_summary)}
                          </p>
                        </div>
                      ))}
                      <SafetyLine>El historial no guarda salidas completas, audio bruto, frames, secretos ni credenciales.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-warning" />
                      <CardTitle>Phase 3 Pilot Checklist</CardTitle>
                    </div>
                    <CardDescription>Automated/build/manual split para browser/local pilot.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-2 sm:grid-cols-3">
                      {["validated_by_automated_tests", "validated_by_build", "pending_manual_browser_pilot"].map((key) => (
                        <div key={key} className="border border-border/70 bg-background/35 p-3">
                          <p className="font-display text-xs uppercase tracking-[0.12em]">{key}</p>
                          <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">
                            {Array.isArray(phase3Pilot[key]) ? (phase3Pilot[key] as unknown[]).length : 0} checks
                          </p>
                        </div>
                      ))}
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {(visualPilot.read_only_checks ?? []).map((check) => (
                        <div key={check.name} className="border border-border/70 bg-background/35 p-3">
                          <p className="font-mono-ui text-xs text-foreground">{check.name}</p>
                          <Badge className="mt-2" variant={check.status === "passed" ? "success" : statusVariant(valueText(check.status))}>{valueText(check.status)}</Badge>
                        </div>
                      ))}
                    </div>
                    <article className="border border-warning/40 bg-warning/10 p-4">
                      <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-warning">Safety Banner</h3>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {missionSafetyLabels.map(([label, key]) => <Badge key={key} variant={missionSafety[key] ? "success" : "outline"}>{label}</Badge>)}
                      </div>
                    </article>
                    <article className="border border-border/70 bg-background/35 p-4">
                      <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Conversation Preview</h3>
                      <p className="mb-3 font-display text-xs text-warning">Preview conversation - no provider call, no memory write, no execution.</p>
                      <div className="grid gap-3">
                        {(missionConversation.messages ?? []).map((message, index) => (
                          <div key={message.speaker + "-" + index} className="border border-border/70 bg-background/40 p-3">
                            <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">{valueText(message.speaker)}</p>
                            <p className="mt-1 font-mono-ui text-xs text-foreground">{valueText(message.content)}</p>
                          </div>
                        ))}
                      </div>
                    </article>
                    <article className="border border-border/70 bg-background/35 p-4">
                      <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Mission Lifecycle</h3>
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                        {missionLifecycleDisplay.map(([step, description]) => (
                          <div key={step} className="border border-border/70 bg-background/40 p-3">
                            <div className="flex items-center justify-between gap-2">
                              <span className="font-display text-xs uppercase tracking-[0.12em]">{step}</span>
                              <Badge variant="outline">preview</Badge>
                            </div>
                            <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">{description}</p>
                          </div>
                        ))}
                      </div>
                    </article>
                    <article className="border border-border/70 bg-background/35 p-4">
                      <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Approval Console / Hermes Panel</h3>
                      <div className="mt-3 grid gap-2">
                        <SafetyLine>Si una misión necesita algo sensible, aparecerá en Approval Console.</SafetyLine>
                        <SafetyLine>Hermes solo ejecutará después de approval válido.</SafetyLine>
                        <SafetyLine>El frontend no puede saltarse gates.</SafetyLine>
                      </div>
                    </article>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-phase-4-pilot-checklist">
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-warning" />
                      <CardTitle>Phase 4 Pilot Checklist</CardTitle>
                    </div>
                    <CardDescription>Automated/build/manual/unsupported split para controller y pairing.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList
                      items={[
                        ["backend start", valueText(phase4Pilot.backend_start_command, "uvicorn jarvis.api.app:app --host 127.0.0.1 --port 9119")],
                        ["frontend start", valueText(phase4Pilot.frontend_start_command, "cd web && npm run dev -- --host 127.0.0.1")],
                        ["source document", valueText(phase4Pilot.source_document, "docs/jarvis-phase-4-local-controller-remote-pairing-pilot-report.md")],
                      ]}
                    />
                    <div className="grid gap-2 sm:grid-cols-4">
                      {["validated_by_automated_tests", "validated_by_build", "pending_manual_browser_pilot", "unsupported_honestly"].map((key) => (
                        <div key={key} className="border border-border/70 bg-background/35 p-3">
                          <p className="font-display text-xs uppercase tracking-[0.12em]">{key}</p>
                          <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">
                            {Array.isArray(phase4Pilot[key]) ? (phase4Pilot[key] as unknown[]).length : 0} items
                          </p>
                        </div>
                      ))}
                    </div>
                    <div className="grid gap-2 md:grid-cols-2">
                      <SafetyLine>Status endpoints cubren phase4/controller/devices/pairing/telegram/stop-rollback.</SafetyLine>
                      <SafetyLine>Pending manual browser pilot: abrir /jarvis y confirmar esfera idle calmada.</SafetyLine>
                      <SafetyLine>Unsupported se muestra honestamente: native tray/service/autostart/remote pairing/Telegram.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>

                <Card data-testid="jarvis-browser-verification-checklist">
                  <CardHeader>
                    <CardTitle>Browser Verification</CardTitle>
                    <CardDescription>Checklist estático/manual para /jarvis y endpoints locales.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <StatusList items={browserVerificationRows} />
                    <div className="grid gap-2 sm:grid-cols-2">
                      {browserChecks.length === 0 ? (
                        <SafetyLine>No hay checklist de navegador cargado.</SafetyLine>
                      ) : browserChecks.map((check: JarvisBrowserVerificationCheck) => (
                        <div key={valueText(check.name)} className="border border-border/70 bg-background/35 p-3">
                          <div className="flex items-center justify-between gap-2">
                            <p className="font-mono-ui text-xs text-foreground">{valueText(check.name)}</p>
                            <Badge variant={check.status === "passed" ? "success" : statusVariant(valueText(check.status))}>{valueText(check.status)}</Badge>
                          </div>
                          <p className="mt-2 line-clamp-2 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(check.description ?? check.notes)}</p>
                        </div>
                      ))}
                    </div>
                    <div className="grid gap-2 md:grid-cols-3">
                      <SafetyLine>No auto getUserMedia on load.</SafetyLine>
                      <SafetyLine>No generic execute route.</SafetyLine>
                      <SafetyLine>No direct Hermes frontend path.</SafetyLine>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </section>
      </div>
    </details>
  );
}
