import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BadgeCheck,
  Camera,
  CircleDollarSign,
  Cpu,
  GitBranch,
  Lock,
  MicOff,
  Radar,
  ShieldAlert,
  ShieldCheck,
  Smartphone,
  Square,
  TerminalSquare,
  Workflow,
  ZapOff,
} from "lucide-react";
import {
  api,
  type JarvisApprovalCard,
  type JarvisAdaptiveProductStage,
  type JarvisCameraVision,
  type JarvisCameraVisionVisualState,
  type JarvisDashboardModule,
  type JarvisDashboardStatus,
  type JarvisFinanceMetric,
  type JarvisFrontendPilotReadinessCheck,
  type JarvisHermesBlockedRoute,
  type JarvisHermesGovernedCapability,
  type JarvisMobileCompanion,
  type JarvisMobileCompanionView,
  type JarvisVoiceCore,
  type JarvisVoiceCoreVisualState,
  type JarvisVisualCommandCenterPilotCheck,
  type JarvisVisualCommandCenterPilotPanel,
  type JarvisVisualCommandCenterPilotStep,
  type JarvisWakeWordFlow,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const DASHBOARD_READ_MODEL_ENDPOINT = "/mark-3/dashboard/status";
const UNKNOWN = "unknown";

const previewVoiceSubtitle = "David, estoy en modo preview. No estoy escuchando ni grabando audio.";

const fallbackVoiceVisualStates: JarvisVoiceCoreVisualState[] = [
  {
    state: "offline",
    label: "offline",
    description: "Backend o núcleo de voz no conectado; sin sensores activos.",
    risk: "none",
    enabled: false,
    sensor_required: false,
    can_approve: false,
    connection: "not connected",
  },
  {
    state: "online",
    label: "online",
    description: "Estado futuro conectado, no habilitado por esta shell.",
    risk: "sensor_privacy",
    enabled: false,
    sensor_required: false,
    can_approve: false,
    connection: "future gated",
  },
  {
    state: "preview",
    label: "preview",
    description: "Estado visual/read-only sin micrófono, STT, TTS ni provider.",
    risk: "none",
    enabled: "preview",
    sensor_required: false,
    can_approve: false,
    connection: "preview",
  },
  {
    state: "dormant",
    label: "dormido",
    description: "JARVIS está dormido visualmente; no escucha ni graba.",
    risk: "none",
    enabled: "preview",
    sensor_required: false,
    can_approve: false,
    connection: "preview",
  },
  {
    state: "listening_wake_word",
    label: "escuchando wake word",
    description: "Estado futuro gateado; requeriría autorización de sensor.",
    risk: "sensor_privacy",
    enabled: false,
    sensor_required: true,
    can_approve: false,
    connection: "future gated",
  },
  {
    state: "listening_command",
    label: "escuchando orden",
    description: "Ventana corta futura tras wake/push-to-talk; apagada aquí.",
    risk: "sensor_privacy",
    enabled: false,
    sensor_required: true,
    can_approve: false,
    connection: "future gated",
  },
  {
    state: "thinking",
    label: "pensando",
    description: "Preview futuro de intención; sin provider externo.",
    risk: "approval_gate",
    enabled: false,
    sensor_required: false,
    can_approve: false,
    connection: "future gated",
  },
  {
    state: "speaking",
    label: "hablando",
    description: "TTS futuro; ahora solo subtítulos preview.",
    risk: "audio_output",
    enabled: false,
    sensor_required: false,
    can_approve: false,
    connection: "not connected",
  },
  {
    state: "approval_required",
    label: "esperando aprobación",
    description: "La aprobación futura aparece en Approval Console, no por voz.",
    risk: "approval_gate",
    enabled: false,
    sensor_required: false,
    can_approve: false,
    connection: "future gated",
  },
  {
    state: "hermes_executing",
    label: "Hermes ejecutando",
    description: "Visibilidad futura después de approval válido.",
    risk: "execution",
    enabled: false,
    sensor_required: false,
    can_approve: false,
    connection: "future gated",
  },
  {
    state: "paused",
    label: "pausado",
    description: "Pausa futura de flujo gobernado; no hay sesión de voz activa.",
    risk: "stop_control",
    enabled: false,
    sensor_required: false,
    can_approve: false,
    connection: "future gated",
  },
  {
    state: "blocked",
    label: "bloqueado",
    description: "Flujos inseguros o no conectados permanecen bloqueados.",
    risk: "blocked",
    enabled: false,
    sensor_required: false,
    can_approve: false,
    connection: "preview",
  },
  {
    state: "error",
    label: "error",
    description: "Error futuro visible; no se arranca runtime de voz.",
    risk: "runtime_error",
    enabled: false,
    sensor_required: false,
    can_approve: false,
    connection: "not connected",
  },
  {
    state: "kill_switch",
    label: "kill switch",
    description: "Relación visible con parada futura; hoy no hay audio real.",
    risk: "stop_control",
    enabled: "preview",
    sensor_required: false,
    can_approve: false,
    connection: "preview",
  },
];

const fallbackVoiceCore: JarvisVoiceCore = {
  state: {
    mode: "preview",
    current_state: "preview",
    microphone_enabled: false,
    wake_word_enabled: false,
    command_listening_enabled: false,
    tts_enabled: false,
    stt_enabled: false,
    audio_recording: false,
    raw_audio_stored: false,
    external_provider_called: false,
    voice_approval_enabled: false,
    wake_phrase_can_approve: false,
    wake_phrase_can_execute: false,
  },
  visual_states: fallbackVoiceVisualStates,
  tts_state: {
    status: "preview",
    speaking: false,
    last_utterance: previewVoiceSubtitle,
    subtitles_enabled: true,
    subtitles_source: "preview/read_model",
    preview_subtitle: previewVoiceSubtitle,
    audio_output_enabled: false,
    provider: "none/not_connected",
    external_call: false,
  },
  wake_word_policy: {
    supported_phrases: ["Hola Jarvis", "Jarvis"],
    wake_word_runtime: "disabled",
    wake_phrase_is_permission: false,
    wake_phrase_can_approve: false,
    wake_phrase_can_execute: false,
    requires_authenticated_channel_for_approval: true,
    critical_actions_require_readback: true,
    critical_actions_require_strong_confirmation: true,
  },
  privacy: {
    no_microphone_activation: true,
    no_audio_recording: true,
    no_raw_audio_storage: true,
    no_external_audio_provider: true,
    no_background_listening_enabled: true,
    no_voice_biometrics: true,
    no_voice_approval_without_gate: true,
  },
  safety: {
    no_auto_execute: true,
    no_hermes_dispatch: true,
    no_tool_call: true,
    no_sensor_activation: true,
    no_get_user_media: true,
    no_media_recorder: true,
    no_audio_context_capture: true,
    kill_switch_visible: true,
  },
  relationship: {
    voice_can_prepare_future_intention: true,
    approval_console_handles_required_approval: true,
    hermes_executes_only_after_valid_approval: true,
    frontend_or_voice_can_call_hermes_directly: false,
    jarvis_governs: true,
    hermes_executes: true,
  },
  kill_switch: {
    visible: true,
    real_audio_to_stop: false,
    future_must_cut_listening_tts_and_governed_execution: true,
  },
  source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  preview_only: true,
  read_only: true,
};

const fallbackWakeWordFlow: JarvisWakeWordFlow = {
  state: {
    mode: "preview",
    wake_runtime_enabled: false,
    microphone_hard_off: true,
    wake_word_only_mode: false,
    command_window_open: false,
    push_to_talk_preview_enabled: true,
    typed_wake_preview_enabled: true,
    always_on_microphone_enabled: false,
    background_listener_enabled: false,
    stt_enabled: false,
    audio_recording: false,
    raw_audio_stored: false,
    external_provider_called: false,
  },
  supported_phrases: ["Hola Jarvis", "Jarvis"],
  stop_phrases: ["para", "cancela", "detente", "silencio", "cancelar misión", "apaga escucha"],
  mode_explanations: {
    mic_hard_off: "Mic hard-off: no escucha nada.",
    wake_word_only: "Wake-word-only: futuro modo donde solo detectaría frase.",
    command_listening: "Command listening: futura ventana corta después de wake.",
    push_to_talk: "Push-to-talk: futuro modo manual.",
    typed_preview: "Typed preview: modo actual seguro.",
  },
  wake_parse_preview: {
    input_example: "Hola Jarvis, revisa el estado del proyecto",
    detected_wake_phrase: "Hola Jarvis",
    remaining_command_preview: "revisa el estado del proyecto",
    would_open_command_window: true,
    would_execute: false,
    would_approve: false,
    would_call_hermes: false,
    would_record_audio: false,
    would_call_provider: false,
    status: "preview_only",
  },
  approval_policy: {
    wake_phrase_is_permission: false,
    wake_phrase_can_approve: false,
    wake_phrase_can_execute: false,
    voice_approval_requires_authenticated_channel: true,
    sensitive_actions_require_readback: true,
    critical_actions_require_double_or_triple_confirmation: true,
    approval_events_must_be_audited: true,
  },
  safety: {
    no_microphone_activation: true,
    no_get_user_media: true,
    no_media_recorder: true,
    no_audio_context_capture: true,
    no_background_listening: true,
    no_raw_audio_storage: true,
    no_external_stt: true,
    no_external_tts: true,
    no_hermes_dispatch: true,
    no_tool_call: true,
    no_auto_execute: true,
  },
  source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  preview_only: true,
  read_only: true,
};

const fallbackCameraVisionStates: JarvisCameraVisionVisualState[] = [
  {
    state: "camera_off",
    label: "cámara apagada",
    description: "Estado actual seguro: no hay cámara activa ni sesión de cámara.",
    enabled: "preview",
    risk: "none",
    can_execute: false,
  },
  {
    state: "camera_available_future",
    label: "preview futuro",
    description: "Disponibilidad futura solo bajo permiso explícito, indicador visual y auditoría.",
    enabled: "future_gated",
    risk: "sensor_privacy",
    can_execute: false,
  },
  {
    state: "preview_disabled",
    label: "preview deshabilitado",
    description: "La previsualización real de cámara no existe en esta PR.",
    enabled: false,
    risk: "sensor_privacy",
    can_execute: false,
  },
  {
    state: "permission_required",
    label: "permiso requerido",
    description: "Cualquier visión futura debe pedir permiso explícito al operador.",
    enabled: "future_gated",
    risk: "approval_gate",
    can_execute: false,
  },
  {
    state: "analyzing_future",
    label: "análisis futuro",
    description: "El análisis futuro deberá declarar qué puede ver y no inferir identidad sensible.",
    enabled: "future_gated",
    risk: "vision_privacy",
    can_execute: false,
  },
  {
    state: "recording_disabled",
    label: "grabación desactivada",
    description: "No se graba vídeo.",
    enabled: false,
    risk: "storage_privacy",
    can_execute: false,
  },
  {
    state: "storage_disabled",
    label: "almacenamiento desactivado",
    description: "No se guarda imagen ni vídeo.",
    enabled: false,
    risk: "storage_privacy",
    can_execute: false,
  },
  {
    state: "blocked",
    label: "bloqueado",
    description: "Activación, captura, streaming y provider externo quedan bloqueados.",
    enabled: "preview",
    risk: "blocked",
    can_execute: false,
  },
  {
    state: "kill_switch",
    label: "kill switch",
    description: "Parada visible futura si cámara/visión se habilita bajo gates.",
    enabled: "preview",
    risk: "stop_control",
    can_execute: false,
  },
];

const fallbackCameraVision: JarvisCameraVision = {
  state: {
    mode: "preview",
    camera_enabled: false,
    camera_permission_requested: false,
    preview_enabled: false,
    recording: false,
    streaming: false,
    snapshot_capture_enabled: false,
    vision_analysis_enabled: false,
    image_storage_enabled: false,
    video_storage_enabled: false,
    external_vision_provider_called: false,
    local_vision_model_connected: UNKNOWN,
    background_camera_access: false,
  },
  privacy: {
    no_camera_activation: true,
    no_get_user_media: true,
    no_media_stream: true,
    no_recording: true,
    no_snapshot_capture: true,
    no_image_storage: true,
    no_video_storage: true,
    no_external_provider: true,
    explicit_operator_permission_required: true,
    visual_indicator_required_when_camera_active: true,
    audit_required_for_future_vision: true,
  },
  states: fallbackCameraVisionStates,
  scope_policy: {
    allowed_scope: "none/unknown",
    future_scope_requires_explicit_operator_permission: true,
    future_analysis_must_state_what_it_can_see: true,
    future_analysis_must_not_infer_sensitive_identity: true,
    future_analysis_must_not_store_without_permission: true,
  },
  camera_state: "disabled",
  preview_state: "disabled",
  recording: false,
  streaming: false,
  snapshot: "disabled",
  vision_analysis: "disabled",
  storage: false,
  provider: "none/not_connected",
  source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  preview_only: true,
  read_only: true,
};

const fallbackMobileViews: JarvisMobileCompanionView[] = [
  {
    id: "status",
    name: "Estado",
    status: "preview",
    can_execute: false,
    can_call_hermes: false,
    notes: "Solo lectura del estado agregado de JARVIS.",
  },
  {
    id: "approvals_preview",
    name: "Approvals preview",
    status: "preview",
    can_execute: false,
    can_call_hermes: false,
    notes: "Vista futura de approvals; no aprueba ni rechaza acciones reales.",
  },
  {
    id: "mission_preview",
    name: "Mission preview",
    status: "preview",
    can_execute: false,
    can_call_hermes: false,
    notes: "Vista futura de misiones sin crear ejecución.",
  },
  {
    id: "hermes_visibility",
    name: "Hermes visibility",
    status: "preview",
    can_execute: false,
    can_call_hermes: false,
    notes: "Visibilidad read-only de Hermes detrás de gates JARVIS.",
  },
  {
    id: "voice_status",
    name: "Voice status",
    status: "preview",
    can_execute: false,
    can_call_hermes: false,
    notes: "Estado de voz sin activar micrófono ni runtime móvil.",
  },
  {
    id: "camera_status",
    name: "Camera status",
    status: "preview",
    can_execute: false,
    can_call_hermes: false,
    notes: "Estado de cámara sin activar cámara móvil.",
  },
  {
    id: "finance_summary",
    name: "Finance summary",
    status: "preview",
    can_execute: false,
    can_call_hermes: false,
    notes: "Resumen financiero sin inventar métricas.",
  },
  {
    id: "kill_switch_preview",
    name: "Kill switch preview",
    status: "future_gated",
    can_execute: false,
    can_call_hermes: false,
    notes: "Control remoto futuro; no está activo en esta PR.",
  },
];

const fallbackMobileCompanion: JarvisMobileCompanion = {
  state: {
    mode: "preview",
    pwa_baseline: "preview",
    mobile_runtime_enabled: false,
    mobile_can_execute: false,
    mobile_can_call_hermes_directly: false,
    mobile_can_approve_real_actions: false,
    mobile_can_reject_real_actions: false,
    mobile_can_modify_scope_real: false,
    mobile_notifications_enabled: false,
    remote_kill_switch_enabled: false,
    remote_camera_enabled: false,
    remote_microphone_enabled: false,
    external_network_required: false,
  },
  mobile_views: fallbackMobileViews,
  safety: {
    mobile_is_interface_not_runtime: true,
    no_direct_hermes_call: true,
    no_mobile_execute: true,
    no_mobile_sensor_activation: true,
    no_mobile_camera_activation: true,
    no_mobile_microphone_activation: true,
    no_real_mobile_approval_in_this_pr: true,
    approval_requires_backend_gate: true,
    critical_approval_requires_strong_confirmation: true,
    remote_kill_switch_future_gated: true,
  },
  pwa_policy: {
    installable_pwa: "preview",
    offline_cache_enabled: false,
    push_notifications_enabled: false,
    service_worker_enabled: false,
    no_background_sync: true,
    no_credentials_storage: true,
    no_token_storage: true,
  },
  source_endpoints: [DASHBOARD_READ_MODEL_ENDPOINT],
  preview_only: true,
  read_only: true,
};

function unknownMetric(label: string): JarvisFinanceMetric {
  return {
    value: UNKNOWN,
    label,
    source: "not_measured",
    evidence_state: "missing",
    confidence: UNKNOWN,
    last_updated: UNKNOWN,
  };
}

const fallbackFinanceRoi: NonNullable<JarvisDashboardStatus["finance_roi"]> = {
  truth_policy: {
    no_fake_metrics: true,
    unknown_when_no_evidence: true,
    measured_requires_source: true,
    estimated_requires_label: true,
    confirmed_revenue_requires_evidence: true,
    projected_revenue_must_be_labelled: true,
    roi_unknown_without_revenue_and_cost: true,
  },
  metrics: {
    actual_cost: unknownMetric("Coste real"),
    estimated_cost: unknownMetric("Coste estimado"),
    confirmed_revenue: unknownMetric("Revenue confirmado"),
    projected_revenue: unknownMetric("Revenue proyectado"),
    gross_revenue: unknownMetric("Gross revenue"),
    expenses: unknownMetric("Expenses"),
    net_revenue: unknownMetric("Net revenue"),
    roi: unknownMetric("ROI"),
    token_cost: unknownMetric("Token cost"),
    api_cost: unknownMetric("API cost"),
    infra_cost: unknownMetric("Infra cost"),
    manual_input_cost: unknownMetric("Manual input cost"),
    revenue_source: unknownMetric("Revenue source"),
  },
  budget: {
    budget_configured: false,
    remaining_budget: UNKNOWN,
    monthly_limit: UNKNOWN,
    alert_threshold: UNKNOWN,
    hard_stop_enabled: false,
    notes: "Budget no configurado; mostrar unknown hasta tener evidencia.",
  },
  safety: {
    no_money_movement: true,
    no_stripe_live: true,
    no_checkout_creation: true,
    no_invoice_creation: true,
    no_payment_collection: true,
    no_fake_revenue: true,
    no_fake_costs: true,
    no_fake_roi: true,
    approval_required_for_money: true,
    strong_approval_required_for_live_payments: true,
  },
  source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  preview_only: true,
  read_only: true,
};

const fallbackBuilderStages: JarvisAdaptiveProductStage[] = [
  {
    name: "Idea",
    status: "preview",
    can_execute: false,
    requires_approval: false,
    approval_level: "none",
    evidence_required: "reason_to_exist",
    notes: "La idea necesita una razón real para existir.",
  },
  {
    name: "Validación",
    status: "preview",
    can_execute: false,
    requires_approval: false,
    approval_level: "none",
    evidence_required: "validation_signal",
    notes: "Validación preview; sin investigación externa.",
  },
  {
    name: "Blueprint",
    status: "preview",
    can_execute: false,
    requires_approval: false,
    approval_level: "none",
    evidence_required: "success_metric_and_scope",
    notes: "Blueprint visual; sin generar código.",
  },
  {
    name: "Código",
    status: "future_gated",
    can_execute: false,
    requires_approval: true,
    approval_level: "strong",
    evidence_required: "approved_scope_and_diff_plan",
    notes: "Código futuro requiere scope, diff y aprobación.",
  },
  {
    name: "Landing",
    status: "future_gated",
    can_execute: false,
    requires_approval: true,
    approval_level: "strong",
    evidence_required: "approved_copy_offer_and_publish_gate",
    notes: "Landing futura no se publica desde este panel.",
  },
  {
    name: "Deploy candidate",
    status: "disabled",
    can_execute: false,
    requires_approval: true,
    approval_level: "strong",
    evidence_required: "rollback_stop_plan_owner_and_build_evidence",
    notes: "Deploy candidate deshabilitado.",
  },
  {
    name: "Monetización",
    status: "disabled",
    can_execute: false,
    requires_approval: true,
    approval_level: "strong",
    evidence_required: "pricing_logic_revenue_confirmation_and_payment_gate",
    notes: "Stripe, checkout y cobro real deshabilitados.",
  },
  {
    name: "Medición",
    status: "future_gated",
    can_execute: false,
    requires_approval: true,
    approval_level: "simple",
    evidence_required: "measured_source_before_metric",
    notes: "Métricas con evidencia; si no hay evidencia, unknown.",
  },
];

const fallbackAdaptiveProductBuilder: NonNullable<JarvisDashboardStatus["adaptive_product_builder"]> = {
  state: {
    mode: "preview",
    builder_enabled: "preview/read_only",
    product_generation_enabled: false,
    code_generation_enabled: false,
    deploy_enabled: false,
    stripe_enabled: false,
    landing_publish_enabled: false,
    external_research_enabled: false,
    hermes_dispatch_enabled: false,
  },
  stages: fallbackBuilderStages,
  differentiation_policy: {
    no_template_clone: true,
    adaptive_builder_not_template_builder: true,
    each_product_needs_reason_to_exist: true,
    each_product_needs_success_metric: true,
    each_product_needs_monetization_logic: true,
    cloned_products_are_failure: true,
  },
  monetization_policy: {
    pricing_preview_only: true,
    stripe_live_requires_strong_approval: true,
    checkout_requires_strong_approval: true,
    real_revenue_requires_confirmation: true,
    projected_revenue_label_required: true,
    no_fake_revenue: true,
  },
  safety: {
    no_deploy: true,
    no_publish: true,
    no_domain_change: true,
    no_email_send: true,
    no_money_movement: true,
    no_credentials: true,
    no_external_network: true,
    no_hermes_dispatch: true,
    approval_gates_required_for_real_actions: true,
  },
  source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  preview_only: true,
  read_only: true,
};

const fallbackFrontendChecks: JarvisFrontendPilotReadinessCheck[] = [
  {
    name: "dashboard_route_exists",
    status: "preview",
    evidence: "/jarvis",
    notes: "Ruta local esperada por la shell.",
  },
  {
    name: "read_model_connected",
    status: "passed",
    evidence: DASHBOARD_READ_MODEL_ENDPOINT,
    notes: "Solo lectura GET al read model.",
  },
  {
    name: "approval_console_visible",
    status: "passed",
    evidence: "approvals",
    notes: "Controles de approval deshabilitados.",
  },
  {
    name: "hermes_execution_visible",
    status: "passed",
    evidence: "hermes_execution",
    notes: "Hermes visible sin ejecución directa.",
  },
  {
    name: "mission_control_visible",
    status: "passed",
    evidence: "mission_control",
    notes: "Mission Control preview-only.",
  },
  {
    name: "voice_core_visible",
    status: "passed",
    evidence: "voice_core",
    notes: "Voz visual sin micrófono.",
  },
  {
    name: "wake_flow_visible",
    status: "passed",
    evidence: "wake_word_flow",
    notes: "Wake flow typed preview.",
  },
  {
    name: "camera_vision_visible",
    status: "passed",
    evidence: "camera_vision",
    notes: "Cámara/visión deshabilitada.",
  },
  {
    name: "mobile_companion_visible",
    status: "passed",
    evidence: "mobile_companion",
    notes: "Mobile es interfaz, no runtime.",
  },
  {
    name: "finance_roi_visible",
    status: "passed",
    evidence: "finance_roi",
    notes: "Métricas unknown sin evidencia.",
  },
  {
    name: "product_builder_visible",
    status: "passed",
    evidence: "adaptive_product_builder",
    notes: "Builder adaptativo preview.",
  },
  {
    name: "kill_switch_visible",
    status: "passed",
    evidence: "Kill Switch",
    notes: "Visible, sin ejecución real que detener.",
  },
  {
    name: "no_fake_metrics",
    status: "passed",
    evidence: "truth_policy.no_fake_metrics",
    notes: "No se inventan métricas.",
  },
  {
    name: "no_frontend_execute",
    status: "passed",
    evidence: "frontend_can_execute=false",
    notes: "El frontend no ejecuta.",
  },
  {
    name: "no_sensor_activation",
    status: "passed",
    evidence: "frontend_can_activate_sensors=false",
    notes: "No se activan sensores.",
  },
  {
    name: "no_post_put_delete",
    status: "passed",
    evidence: "allowed_http_methods_for_frontend=[GET]",
    notes: "El dashboard mira, no toca.",
  },
];

const fallbackFrontendPilot: NonNullable<JarvisDashboardStatus["frontend_pilot"]> = {
  state: {
    mode: "read_only_pilot",
    dashboard_route: "/jarvis",
    backend_status_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
    frontend_can_execute: false,
    frontend_can_approve: false,
    frontend_can_activate_sensors: false,
    frontend_can_move_money: false,
    frontend_can_deploy: false,
    frontend_can_send_email: false,
  },
  readiness_checks: fallbackFrontendChecks,
  hardening_notes: {
    npm_audit_vulnerabilities_observed: UNKNOWN,
    npm_audit_fix_not_run: true,
    dependency_hardening_requires_separate_pr: true,
    no_lockfile_changes_expected: true,
    frontend_build_required_before_merge: true,
    full_pytest_required_before_merge: true,
  },
  pilot_limitations: [
    "no real approvals",
    "no real mission submit",
    "no real Hermes execution",
    "no real voice",
    "no real camera",
    "no real mobile runtime",
    "no real finance/revenue measurement",
    "no deploy/money/email/credentials",
  ],
  source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  preview_only: true,
  read_only: true,
};

const fallbackVisualPilotPanels: JarvisVisualCommandCenterPilotPanel[] = [
  {
    name: "Header",
    expected: true,
    source: "system + jarvis_hermes_contract",
    status: "ready",
    can_execute: false,
    notes: "Muestra modo local read-only y separación JARVIS/Hermes.",
  },
  {
    name: "Voice Core",
    expected: true,
    source: "voice_core",
    status: "preview",
    can_execute: false,
    notes: "Visual only; micrófono, STT, TTS y providers deshabilitados.",
  },
  {
    name: "Wake Word Local Safe Flow",
    expected: true,
    source: "wake_word_flow",
    status: "preview",
    can_execute: false,
    notes: "Typed preview; wake phrase no aprueba ni ejecuta.",
  },
  {
    name: "Mission Control",
    expected: true,
    source: "mission_control",
    status: "preview",
    can_execute: false,
    notes: "Sin mission submit real ni Hermes dispatch.",
  },
  {
    name: "Approval Console",
    expected: true,
    source: "approvals",
    status: "preview",
    can_execute: false,
    notes: "Botones visibles pero disabled/read-only.",
  },
  {
    name: "Hermes Execution",
    expected: true,
    source: "hermes_execution",
    status: "preview",
    can_execute: false,
    notes: "Visibilidad read-only; frontend no llama a Hermes.",
  },
  {
    name: "Agent / Module Radar",
    expected: true,
    source: "modules",
    status: "ready",
    can_execute: false,
    notes: "Estados normalizados con degradación honesta.",
  },
  {
    name: "Camera / Vision",
    expected: true,
    source: "camera_vision",
    status: "disabled",
    can_execute: false,
    notes: "Cámara, captura, storage y visión real están deshabilitados.",
  },
  {
    name: "Mobile Companion",
    expected: true,
    source: "mobile_companion",
    status: "preview",
    can_execute: false,
    notes: "Mobile es interfaz preview, no runtime.",
  },
  {
    name: "Finance / ROI",
    expected: true,
    source: "finance_roi",
    status: UNKNOWN,
    can_execute: false,
    notes: "Métricas sin evidencia se quedan en unknown.",
  },
  {
    name: "Product Builder Adaptativo",
    expected: true,
    source: "adaptive_product_builder",
    status: "preview",
    can_execute: false,
    notes: "Stages preview/future-gated/disabled sin ejecución.",
  },
  {
    name: "Frontend Pilot / Hardening",
    expected: true,
    source: "frontend_pilot",
    status: "ready",
    can_execute: false,
    notes: "GET-only al read model y sin rutas mutantes desde el dashboard.",
  },
  {
    name: "Live Timeline / Audit",
    expected: true,
    source: "timeline",
    status: "ready",
    can_execute: false,
    notes: "Eventos de lectura/checks; no ejecución.",
  },
  {
    name: "Kill Switch",
    expected: true,
    source: "system.kill_switch_state",
    status: "preview",
    can_execute: false,
    notes: "Visible y disabled; no hay ejecución real que detener.",
  },
];

const fallbackVisualPilotChecks: JarvisVisualCommandCenterPilotCheck[] = [
  {
    name: "no_post_put_delete",
    status: "passed",
    evidence: "allowed_http_methods_for_frontend=[GET]",
    notes: "El dashboard puede leer status, no mutar estado.",
  },
  {
    name: "no_execute_route",
    status: "passed",
    evidence: "frontend_must_not_call_execute=true",
    notes: "No se expone ruta de ejecución desde /jarvis.",
  },
  {
    name: "no_frontend_hermes_call",
    status: "passed",
    evidence: "frontend_can_call_hermes_execute=false",
    notes: "No se ejecuta Hermes desde el frontend.",
  },
  {
    name: "no_tool_runner",
    status: "passed",
    evidence: "no_frontend_tool_runner=true",
    notes: "No hay runner de herramientas en navegador.",
  },
  {
    name: "no_sensor_activation",
    status: "passed",
    evidence: "no_sensor_activation=true",
    notes: "No se activan sensores.",
  },
  {
    name: "no_get_user_media",
    status: "passed",
    evidence: "no_get_user_media=true",
    notes: "No se piden permisos de navegador para media.",
  },
  {
    name: "no_media_recorder",
    status: "passed",
    evidence: "voice_core.safety.no_media_recorder=true",
    notes: "No se graba audio.",
  },
  {
    name: "no_audio_context_capture",
    status: "passed",
    evidence: "voice_core.safety.no_audio_context_capture=true",
    notes: "No hay captura por audio context.",
  },
  {
    name: "no_camera_capture",
    status: "passed",
    evidence: "camera_vision.privacy.no_snapshot_capture=true",
    notes: "No se captura imagen ni vídeo.",
  },
  {
    name: "no_mobile_runtime",
    status: "passed",
    evidence: "mobile_runtime_enabled=false",
    notes: "Mobile Companion es preview-only.",
  },
  {
    name: "no_money_movement",
    status: "passed",
    evidence: "finance_roi.safety.no_money_movement=true",
    notes: "No se mueve dinero.",
  },
  {
    name: "no_stripe_live",
    status: "passed",
    evidence: "finance_roi.safety.no_stripe_live=true",
    notes: "No hay Stripe live ni checkout.",
  },
  {
    name: "no_deploy",
    status: "passed",
    evidence: "adaptive_product_builder.safety.no_deploy=true",
    notes: "No hay deploy.",
  },
  {
    name: "no_email_send",
    status: "passed",
    evidence: "safety.no_email_send=true",
    notes: "No se envía email.",
  },
  {
    name: "no_credentials",
    status: "passed",
    evidence: "safety.no_credentials=true",
    notes: "No se leen ni guardan credenciales.",
  },
  {
    name: "no_fake_metrics",
    status: "passed",
    evidence: "finance_roi.truth_policy.no_fake_metrics=true",
    notes: "No hay métricas falsas; sin evidencia queda unknown.",
  },
];

const fallbackOperatorPilotSteps: JarvisVisualCommandCenterPilotStep[] = [
  { order: 1, check: "arrancar backend", notes: "Arrancar el backend local antes de abrir la UI." },
  { order: 2, check: "abrir /jarvis", notes: "Abrir la ruta local del cockpit." },
  { order: 3, check: "comprobar estado general", notes: "Verificar modo, endpoint y estado read-only." },
  { order: 4, check: "comprobar panels", notes: "Confirmar que todos los paneles esperados están visibles." },
  { order: 5, check: "comprobar unknown/disabled", notes: "Validar degradación a unknown, disabled, not_connected, preview o future_gated." },
  { order: 6, check: "comprobar que botones críticos están disabled", notes: "Mission, approvals, kill switch, sensores, dinero y deploy deben estar disabled." },
  { order: 7, check: "comprobar que no hay permisos de navegador", notes: "No debe aparecer prompt de micrófono, cámara, notificaciones o media." },
  { order: 8, check: "comprobar que no hay ejecución Hermes", notes: "No hay llamada directa a Hermes desde el frontend." },
  { order: 9, check: "comprobar que finance/ROI no inventa datos", notes: "Valores sin evidencia se muestran como unknown." },
  { order: 10, check: "comprobar timeline read-only", notes: "Timeline solo muestra lecturas/checks, no acciones ejecutadas." },
];

const fallbackVisualCommandCenterPilot: NonNullable<JarvisDashboardStatus["visual_command_center_pilot"]> = {
  state: {
    mode: "read_only_pilot",
    dashboard_route: "/jarvis",
    status_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
    backend_read_model_connected: true,
    frontend_execution_enabled: false,
    approvals_real_enabled: false,
    hermes_direct_execution_enabled: false,
    voice_real_enabled: false,
    camera_real_enabled: false,
    mobile_runtime_enabled: false,
    money_enabled: false,
    deploy_enabled: false,
    email_enabled: false,
    credentials_enabled: false,
  },
  required_panels: fallbackVisualPilotPanels,
  read_only_checks: fallbackVisualPilotChecks,
  operator_pilot_steps: fallbackOperatorPilotSteps,
  pilot_findings: {
    findings: [],
    known_limitations: [
      "real approvals not wired",
      "mission submit is preview-only",
      "voice is preview-only",
      "wake word is preview-only",
      "camera is disabled",
      "mobile is preview-only",
      "finance is unknown without evidence",
      "Product Builder is preview-only",
      "dependency hardening may need separate PR due npm audit vulnerabilities",
    ],
  },
  safety: {
    pilot_is_read_only: true,
    dashboard_may_read_status_only: true,
    no_side_effects: true,
    no_real_world_actions: true,
    no_background_workers: true,
    no_sensors: true,
    no_money: true,
    no_production: true,
    no_credentials: true,
    restrictions_are_approval_gates_not_permanent_bans: true,
  },
  source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  preview_only: true,
  read_only: true,
};

const requiredModules = [
  "Mission Loop",
  "Research",
  "Product Revenue",
  "Routine Ops",
  "Moonshot Lab",
  "Voice",
  "Wake Listener",
  "Camera/Vision",
  "Mobile Companion",
  "Memory/Learning",
  "Hermes",
] as const;

const fallbackStageNames = fallbackBuilderStages.map((stage) => stage.name);

const approvalActionLabels = ["Aprobar", "Rechazar", "Modificar alcance", "Pedir explicación"] as const;

const fallbackApprovalCards: JarvisApprovalCard[] = [
  {
    id: "preview-local-docs-repo-read",
    title: "Lectura local exacta de docs/repo",
    action: "Leer una ruta local exacta ya acotada.",
    reason: "Lectura local bounded: bajo riesgo si el alcance es exacto y no muta estado.",
    status: "preview",
    risk_level: "low",
    approval_level: "direct",
    touches: ["filesystem", "local_docs"],
    estimated_cost: UNKNOWN,
    measured_cost: UNKNOWN,
    rollback_plan: "No hay mutación; rollback no aplica.",
    stop_plan: "Parar si la ruta no es exacta, local y dentro del scope aprobado.",
    expires_at: UNKNOWN,
    scope_summary: "Un archivo o ruta local de docs/repo en modo lectura.",
    evidence_summary: "Fallback seguro: backend no disponible o campo ausente.",
    disabled_reason: "Preview-only: approval execution is not wired in this PR.",
    recommended_operator_action: "Verificar path exacto y mantenerlo read-only.",
    requires_readback: false,
    strong_confirmation_required: false,
    double_confirmation_required: false,
    triple_confirmation_required: false,
    rollback_required: false,
    stop_plan_required: true,
    audit_required: true,
    preview_only: true,
    read_only: true,
    source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  },
  {
    id: "preview-local-file-write",
    title: "Escritura de archivo local",
    action: "Crear o modificar un archivo local.",
    reason: "Cambia estado local y requiere scope, diff y rollback antes de cualquier ejecución futura.",
    status: "blocked",
    risk_level: "medium",
    approval_level: "simple",
    touches: ["filesystem", "local_docs"],
    estimated_cost: UNKNOWN,
    measured_cost: UNKNOWN,
    rollback_plan: "Exigir diff, backup o patch de reversión antes de una escritura futura.",
    stop_plan: "Parar por path amplio, glob, diff ausente o cancelación humana.",
    expires_at: UNKNOWN,
    scope_summary: "Un path local explícito y un diff exacto; sin escrituras recursivas.",
    evidence_summary: "La consola no tiene endpoint de escritura.",
    disabled_reason: "Preview-only: approval execution is not wired in this PR.",
    recommended_operator_action: "Pedir diff preview y aprobar solo un write bounded futuro.",
    requires_readback: true,
    strong_confirmation_required: false,
    double_confirmation_required: false,
    triple_confirmation_required: false,
    rollback_required: true,
    stop_plan_required: true,
    audit_required: true,
    preview_only: true,
    read_only: true,
    source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  },
  {
    id: "preview-external-web-github-search",
    title: "Búsqueda externa web/GitHub",
    action: "Consultar web o GitHub fuera del entorno local.",
    reason: "Puede filtrar intención, consumir cuota o traer contenido no confiable.",
    status: "blocked",
    risk_level: "high",
    approval_level: "strong",
    touches: ["web", "github"],
    estimated_cost: UNKNOWN,
    measured_cost: UNKNOWN,
    rollback_plan: "No llamar proveedores externos hasta aprobar query, proveedor y manejo de datos.",
    stop_plan: "Parar ante secrets, repos privados, scopes de cuenta o intención ambigua.",
    expires_at: UNKNOWN,
    scope_summary: "Query/proveedor/fuentes específicos; sin acciones autenticadas.",
    evidence_summary: "Web/GitHub no está conectado a esta consola.",
    disabled_reason: "Preview-only: approval execution is not wired in this PR.",
    recommended_operator_action: "Exigir approval fuerte antes de cualquier llamada externa futura.",
    requires_readback: true,
    strong_confirmation_required: true,
    double_confirmation_required: false,
    triple_confirmation_required: false,
    rollback_required: true,
    stop_plan_required: true,
    audit_required: true,
    preview_only: true,
    read_only: true,
    source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  },
  {
    id: "preview-production-money-deploy-email",
    title: "Producción, dinero, deploy o email real",
    action: "Deploy, Stripe/dinero o envío de email real.",
    reason: "Tiene impacto externo o irreversible y requiere confirmación fuerte.",
    status: "blocked",
    risk_level: "critical",
    approval_level: "triple",
    touches: ["money", "deploy", "email", "web"],
    estimated_cost: UNKNOWN,
    measured_cost: UNKNOWN,
    rollback_plan: "Exigir rollback verificado, owner, blast radius y stop condition.",
    stop_plan: "Parar ante coste no verificado, credencial viva, smoke fallido o cancelación.",
    expires_at: UNKNOWN,
    scope_summary: "Cuenta, entorno, destinatario o importe nominal; sin scope amplio.",
    evidence_summary: "Finance sigue unknown si no hay evidencia real.",
    disabled_reason: "Preview-only: approval execution is not wired in this PR.",
    recommended_operator_action: "Requerir readback, doble/triple confirmación, rollback, stop plan y auditoría.",
    requires_readback: true,
    strong_confirmation_required: true,
    double_confirmation_required: true,
    triple_confirmation_required: true,
    rollback_required: true,
    stop_plan_required: true,
    audit_required: true,
    preview_only: true,
    read_only: true,
    source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  },
  {
    id: "preview-forbidden-credentials-bypass",
    title: "Credenciales, secrets, tokens o bypass",
    action: "Leer secrets/tokens/cookies/sesiones o saltar autorización.",
    reason: "Credenciales, bypass, deception y fake metrics son límites forbidden.",
    status: "forbidden",
    risk_level: "forbidden",
    approval_level: "forbidden",
    touches: ["credentials"],
    estimated_cost: UNKNOWN,
    measured_cost: UNKNOWN,
    rollback_plan: "No se ejecuta; rediseñar como status/audit sin secretos.",
    stop_plan: "Parar y rechazar si pide secrets, cookies, tokens, bypass o métricas falsas.",
    expires_at: UNKNOWN,
    scope_summary: "Scope forbidden; ningún acceso a credenciales o bypass.",
    evidence_summary: "Safety boundary: no_credentials=true y no fake metrics.",
    disabled_reason: "Preview-only: approval execution is not wired in this PR.",
    recommended_operator_action: "Rechazar y pedir alternativa segura sin secretos.",
    requires_readback: true,
    strong_confirmation_required: true,
    double_confirmation_required: true,
    triple_confirmation_required: true,
    rollback_required: false,
    stop_plan_required: true,
    audit_required: true,
    preview_only: true,
    read_only: true,
    source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  },
];

const riskLegend = [
  ["Nivel 0-1", "directo / bajo riesgo"],
  ["Nivel 2", "local scoped / simple approval"],
  ["Nivel 3", "externo o sensible / strong approval"],
  ["Nivel 4", "producción, dinero, deploy, email, credenciales / double o triple confirmation"],
  ["Nivel 5", "ilegal, inseguro, no autorizado, bypass, deception, fake metrics / forbidden"],
] as const;

const fallbackHermesCapabilities: JarvisHermesGovernedCapability[] = [
  {
    name: "lectura local gobernada",
    status: "unknown",
    approval_required: true,
    approval_level: "direct",
    can_execute_from_frontend: false,
    notes: "Fallback seguro: sin evidencia de backend; mostrar solo visibilidad read-only.",
  },
  {
    name: "research docs/repo",
    status: "unknown",
    approval_required: true,
    approval_level: "level_2_local_read",
    can_execute_from_frontend: false,
    notes: "Research local requiere scope exacto y no usa web/GitHub real desde esta pantalla.",
  },
  {
    name: "mission gated execution candidate",
    status: "gated",
    approval_required: true,
    approval_level: "risk_scaled",
    can_execute_from_frontend: false,
    notes: "Una candidate no es ejecución; solo expresa readiness gobernada.",
  },
  {
    name: "herramientas externas",
    status: "not_connected",
    approval_required: true,
    approval_level: "strong",
    can_execute_from_frontend: false,
    notes: "Browser, red, GitHub y providers externos no están conectados a este panel.",
  },
  {
    name: "deploy/dinero/email/credenciales",
    status: "forbidden",
    approval_required: true,
    approval_level: "level_4_or_forbidden",
    can_execute_from_frontend: false,
    notes: "Producción, pagos, email real y credenciales quedan fuera del frontend.",
  },
];

const fallbackHermesBlockedRoutes: JarvisHermesBlockedRoute[] = [
  {
    route_or_action: "ruta execute directa",
    action: "ejecución desde frontend",
    blocked: true,
    can_execute_from_frontend: false,
    notes: "Sin ruta de ejecución desde frontend.",
  },
  {
    route_or_action: "approve/reject",
    action: "mutación de aprobación",
    blocked: true,
    can_execute_from_frontend: false,
    notes: "Los botones de approval permanecen disabled.",
  },
  {
    route_or_action: "runner de herramientas",
    action: "invocación de tools en navegador",
    blocked: true,
    can_execute_from_frontend: false,
    notes: "Sin registry ni invocación de herramientas en el frontend.",
  },
  {
    route_or_action: "deploy / dinero / email / credenciales",
    action: "impacto externo o acceso sensible",
    blocked: true,
    can_execute_from_frontend: false,
    notes: "Sin producción, pagos, envío real, secretos, tokens o credenciales.",
  },
  {
    route_or_action: "sensores / móvil / voz / cámara",
    action: "activación directa o Hermes directo",
    blocked: true,
    can_execute_from_frontend: false,
    notes: "Sin sensores y sin llamadas directas a Hermes desde móvil, voz o cámara.",
  },
];

const futureExecutionRequirements = [
  "approval válido",
  "scope exacto",
  "risk level",
  "rollback/stop plan",
  "auditoría",
  "coste/impacto",
  "operador humano",
] as const;

const sampleMissionCommand = "JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro.";

const fallbackMissionControl: NonNullable<JarvisDashboardStatus["mission_control"]> = {
  state: {
    mode: "preview",
    input_enabled: "preview_only",
    conversation_enabled: "preview_only",
    execution_enabled: false,
    hermes_dispatch_enabled: false,
    approval_creation_enabled: false,
    persistence_enabled: false,
    external_network_enabled: false,
  },
  supported_inputs: {
    text_command: "preview",
    voice_command: "future_gated",
    mobile_command: "future_gated",
    wake_word_command: "future_gated",
    file_drop: "not_connected",
    camera_context: "not_connected",
  },
  sample_command: sampleMissionCommand,
  intent_preview: {
    detected_intent: UNKNOWN,
    confidence: UNKNOWN,
    mission_type: UNKNOWN,
    risk_level: UNKNOWN,
    approval_level: UNKNOWN,
    blocked_reasons: [],
    required_permissions: [],
    next_safe_action: UNKNOWN,
  },
  command_lifecycle: [
    {
      state: "draft",
      description: "La orden queda visible como borrador.",
      preview_only: true,
    },
    {
      state: "submitted_for_preview",
      description: "JARVIS prepararía una lectura segura de intención.",
      preview_only: true,
    },
    {
      state: "intent_detected",
      description: "La intención se mostraría sin llamar providers.",
      preview_only: true,
    },
    {
      state: "risk_classified",
      description: "El riesgo se clasificaría antes de cualquier gate.",
      preview_only: true,
    },
    {
      state: "approval_required",
      description: "Lo sensible queda esperando aprobación explícita.",
      preview_only: true,
    },
    {
      state: "ready_for_operator_review",
      description: "David revisa scope, permisos y siguiente paso.",
      preview_only: true,
    },
    {
      state: "blocked",
      description: "Lo ambiguo o no conectado permanece bloqueado.",
      preview_only: true,
    },
    {
      state: "forbidden",
      description: "Credenciales, bypass y acciones inseguras no se aprueban.",
      preview_only: true,
    },
    {
      state: "executable_candidate_after_valid_approval",
      description: "Solo un approval válido futuro podría crear elegibilidad.",
      preview_only: true,
    },
  ],
  conversation_preview: {
    messages: [
      {
        role: "user",
        speaker: "David",
        content: sampleMissionCommand,
        preview_only: true,
      },
      {
        role: "assistant",
        speaker: "JARVIS",
        content: "Puedo preparar una misión de revisión. Antes de ejecutar cualquier acción sensible, pediré aprobación.",
        preview_only: true,
      },
    ],
    assistant_status: "preview",
    transcript_persistence: false,
    memory_write: false,
    memory_read: false,
    pii_redaction_required: true,
    raw_audio_stored: false,
    external_provider_called: false,
  },
  safety: {
    no_auto_execute: true,
    no_hermes_dispatch: true,
    no_tool_call: true,
    no_file_write: true,
    no_network_call: true,
    no_email_send: true,
    no_money_movement: true,
    no_deploy: true,
    no_credentials: true,
    no_sensor_activation: true,
    no_voice_recording: true,
    no_camera_capture: true,
    wake_phrase_is_not_permission: true,
  },
  operator_guidance: {
    can_do: "David puede ver cómo JARVIS recibiría una orden y prepararía una revisión segura.",
    cannot_do_yet: "Todavía no puede crear misiones, approvals, memoria, llamadas externas ni ejecución.",
    future_next_step: "El siguiente paso futuro será un intake/classifier seguro antes de propuestas reales.",
    sensitive_requires_approval: "Todo lo sensible requiere approval explícito, scope, rollback/stop plan y auditoría.",
  },
  source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
  read_only: true,
};

const missionLifecycleDisplay = [
  ["draft", "Orden escrita o dictada como borrador visual."],
  ["preview", "JARVIS prepara lectura de intención sin mutar estado."],
  ["intent detected", "La intención queda en unknown hasta tener clasificador seguro."],
  ["risk classified", "El riesgo se muestra como preview antes de approvals."],
  ["approval required", "Lo sensible se deriva a Approval Console."],
  ["operator review", "David revisa scope, permisos y siguiente paso."],
  ["Hermes gated", "Hermes permanece detrás de gates válidos."],
  ["audit", "La acción futura deberá dejar evidencia auditable."],
] as const;

const missionSafetyLabels = [
  ["No auto execute", "no_auto_execute"],
  ["No Hermes dispatch", "no_hermes_dispatch"],
  ["No tool call", "no_tool_call"],
  ["No file write", "no_file_write"],
  ["No network", "no_network_call"],
  ["No voice recording", "no_voice_recording"],
  ["No camera capture", "no_camera_capture"],
  ["Wake phrase is not permission", "wake_phrase_is_not_permission"],
] as const;

function fallbackVisualPilot(reason: "loading" | "offline" | "error"): NonNullable<JarvisDashboardStatus["visual_command_center_pilot"]> {
  return {
    ...fallbackVisualCommandCenterPilot,
    state: {
      ...fallbackVisualCommandCenterPilot.state,
      backend_read_model_connected: false,
    },
    required_panels: fallbackVisualPilotPanels.map((panel) => ({
      ...panel,
      status: panel.status === "disabled" ? "disabled" : UNKNOWN,
      notes: `Fallback ${reason}: ${panel.notes}`,
    })),
    read_only_checks: fallbackVisualPilotChecks.map((check) => ({
      ...check,
      status: check.name === "no_post_put_delete" ? "passed" : "preview",
      evidence: reason === "loading" ? "frontend fallback loading" : "backend unavailable; static dashboard guardrail",
    })),
  };
}

function fallbackDashboard(reason: "loading" | "offline" | "error"): JarvisDashboardStatus {
  return {
    system: {
      api_status: reason === "loading" ? UNKNOWN : "offline",
      local_first: true,
      mode: "read_only_dashboard",
      free_autonomy_enabled: false,
      preview_first: true,
      kill_switch_state: "not_wired",
      generated_at: UNKNOWN,
    },
    jarvis_hermes_contract: {
      jarvis_role: "governs/risk/approval/audit/control",
      hermes_role: "execution_engine",
      no_duplicate_hermes_runtime: true,
      frontend_direct_execution_allowed: false,
      frontend_can_execute: false,
      frontend_can_call_hermes_execute: false,
    },
    release_candidate: {
      status: UNKNOWN,
      readiness: {},
      not_ready_for_free_autonomy: true,
      restrictions_are_approval_gates_not_permanent_bans: true,
      pilot_readiness: UNKNOWN,
      pilot_executed: false,
    },
    modules: requiredModules.map((name) => ({
      name,
      status: name === "Camera/Vision" || name === "Wake Listener" ? "disabled" : "unknown",
      source: DASHBOARD_READ_MODEL_ENDPOINT,
      risk: UNKNOWN,
      notes: "Fallback seguro: backend offline o campo no conectado.",
    })),
    mission_control: fallbackMissionControl,
    approvals: {
      pending_count: UNKNOWN,
      critical_count: UNKNOWN,
      blocked_count: UNKNOWN,
      expired_count: UNKNOWN,
      preview_count: fallbackApprovalCards.length,
      action_buttons_enabled: false,
      all_actions_read_only: true,
      wake_phrase_can_approve: false,
      frontend_can_approve: false,
      frontend_can_reject: false,
      frontend_can_modify_scope: false,
      critical_actions_require_strong_approval: true,
      cards: fallbackApprovalCards,
      cards_state: "preview/read-only",
      preview_only: true,
      readback_policy: {
        wake_phrase_never_approves: true,
        voice_approval_requires_auth_gate_and_audit: true,
        critical_actions_require_readback: true,
        critical_actions_require_strong_confirmation: true,
        critical_actions_require_double_or_triple_confirmation: true,
        critical_actions_require_rollback_and_stop_plan: true,
        audit_required: true,
      },
    },
    hermes_execution: {
      available: false,
      connected: UNKNOWN,
      active_execution: UNKNOWN,
      last_execution: UNKNOWN,
      last_result: UNKNOWN,
      last_error: UNKNOWN,
      measured_duration: UNKNOWN,
      measured_cost: UNKNOWN,
      frontend_direct_execution_allowed: false,
      frontend_can_execute: false,
      frontend_can_call_hermes_execute: false,
      running_sessions: UNKNOWN,
      session_count: UNKNOWN,
      supported_tool: UNKNOWN,
      notes: "Fallback seguro: no se permite ejecución directa desde frontend.",
      contract: {
        jarvis_role: "governs/risk/approval/audit/control",
        hermes_role: "execution_engine",
        no_duplicate_hermes_runtime: true,
        frontend_direct_execution_allowed: false,
        frontend_can_execute: false,
        frontend_can_call_hermes_execute: false,
      },
      runtime_status: {
        available: false,
        connected: UNKNOWN,
        active_execution: UNKNOWN,
        execution_mode: "read_only_visibility",
        last_execution: UNKNOWN,
        last_result: UNKNOWN,
        last_error: UNKNOWN,
        last_rollback: UNKNOWN,
        last_stop_plan: UNKNOWN,
        measured_duration: UNKNOWN,
        measured_cost: UNKNOWN,
        running_sessions: UNKNOWN,
        session_count: UNKNOWN,
        supported_tool: UNKNOWN,
      },
      governed_capabilities: fallbackHermesCapabilities,
      blocked_routes: fallbackHermesBlockedRoutes,
      safety: {
        no_frontend_execute: true,
        no_frontend_tool_runner: true,
        no_direct_hermes_call_from_mobile: true,
        no_direct_hermes_call_from_voice: true,
        no_direct_hermes_call_from_camera: true,
        approval_required_before_execution: true,
        wake_phrase_is_not_permission: true,
        audit_required: true,
        rollback_or_stop_plan_required_for_sensitive_actions: true,
      },
    },
    voice_core: fallbackVoiceCore,
    wake_word_flow: fallbackWakeWordFlow,
    voice_wake: {
      microphone_state: "disabled",
      wake_word_state: "unknown",
      wake_phrases: ["Hola Jarvis", "Jarvis"],
      wake_phrase_can_approve: false,
      wake_phrase_can_execute: false,
      audio_recording: false,
      raw_audio_stored: false,
      external_provider_called: false,
    },
    camera_vision: fallbackCameraVision,
    mobile_companion: fallbackMobileCompanion,
    mobile: {
      companion_state: "preview",
      direct_hermes_call_allowed: false,
      remote_kill_switch_state: "future_gated",
      approval_actions_enabled: false,
      source_endpoints: [DASHBOARD_READ_MODEL_ENDPOINT],
    },
    finance_roi: fallbackFinanceRoi,
    finance: {
      actual_cost: UNKNOWN,
      estimated_cost: UNKNOWN,
      confirmed_revenue: UNKNOWN,
      projected_revenue: UNKNOWN,
      gross_revenue: UNKNOWN,
      expenses: UNKNOWN,
      net_revenue: UNKNOWN,
      roi: UNKNOWN,
      no_fake_metrics: true,
    },
    adaptive_product_builder: fallbackAdaptiveProductBuilder,
    product_builder: {
      stages: [...fallbackStageNames],
      deploy_requires_strong_approval: true,
      stripe_checkout_requires_strong_approval: true,
      real_revenue_must_be_confirmed: true,
    },
    frontend_pilot: fallbackFrontendPilot,
    visual_command_center_pilot: fallbackVisualPilot(reason),
    safety: {
      frontend_can_execute: false,
      frontend_can_approve: false,
      no_auto_execute: true,
      no_duplicate_hermes_runtime: true,
      no_get_user_media: true,
      no_sensor_activation: true,
      no_voice_recording: true,
      no_camera_capture: true,
      no_frontend_tool_runner: true,
      no_tool_call: true,
      no_file_write: true,
      no_network_call: true,
      no_frontend_hermes_execution: true,
      no_hermes_dispatch: true,
      no_post_put_delete_from_jarvis_page: true,
      no_money_movement: true,
      no_deploy: true,
      no_credentials: true,
      no_email_send: true,
    },
    timeline: [
      {
        event: reason === "loading" ? "dashboard read model loading" : "dashboard read model unavailable",
        source: DASHBOARD_READ_MODEL_ENDPOINT,
        status: reason,
        read_only: true,
      },
    ],
    read_only_contract: {
      aggregated_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
      allowed_http_methods_for_frontend: ["GET"],
      internal_sources_are_read_only_status_or_audit: true,
      frontend_must_not_call_execute: true,
      frontend_must_not_request_sensor_permissions: true,
    },
  };
}

function valueText(value: unknown, fallback = UNKNOWN): string {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  return fallback;
}

function yesNo(value: unknown, yes = "true", no = "false", fallback = UNKNOWN): string {
  if (typeof value === "boolean") return value ? yes : no;
  return fallback;
}

function statusVariant(status: string): "outline" | "warning" | "destructive" | "success" {
  if (status === "ready") return "success";
  if (status === "disabled" || status === "not_connected" || status === "forbidden") return "destructive";
  if (status === "gated" || status === "future_gated" || status === "prepare-only" || status === "preview") return "warning";
  return "outline";
}

function approvalStatusVariant(status: string): "outline" | "warning" | "destructive" | "success" {
  if (status === "approved") return "success";
  if (status === "pending" || status === "preview") return "warning";
  if (status === "blocked" || status === "forbidden" || status === "expired" || status === "rejected") return "destructive";
  return "outline";
}

function riskVariant(risk: string): "outline" | "warning" | "destructive" | "success" {
  if (risk === "low") return "success";
  if (risk === "medium" || risk === "high") return "warning";
  if (risk === "critical" || risk === "forbidden") return "destructive";
  return "outline";
}

function approvalLevelVariant(level: string): "outline" | "warning" | "destructive" | "success" {
  if (level === "direct") return "success";
  if (level === "simple" || level === "strong") return "warning";
  if (level === "double" || level === "triple" || level === "forbidden") return "destructive";
  return "outline";
}

function readModules(modules: JarvisDashboardModule[] | undefined): JarvisDashboardModule[] {
  const byName = new Map((modules ?? []).map((item) => [item.name, item]));
  return requiredModules.map((name) => {
    return byName.get(name) ?? {
      name,
      status: UNKNOWN,
      source: DASHBOARD_READ_MODEL_ENDPOINT,
      risk: UNKNOWN,
      notes: "Campo ausente; mostrado como unknown.",
    };
  });
}

function readHermesCapabilities(items: JarvisHermesGovernedCapability[] | undefined): JarvisHermesGovernedCapability[] {
  return items?.length ? items : fallbackHermesCapabilities;
}

function readHermesBlockedRoutes(items: JarvisHermesBlockedRoute[] | undefined): JarvisHermesBlockedRoute[] {
  return items?.length ? items : fallbackHermesBlockedRoutes;
}

function StatusList({ items }: { items: readonly (readonly [string, string])[] }) {
  return (
    <dl className="grid gap-2">
      {items.map(([label, value]) => (
        <div key={`${label}-${value}`} className="flex items-center justify-between gap-4 border border-border/60 bg-background/30 px-3 py-2">
          <dt className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">{label}</dt>
          <dd className="max-w-[65%] break-words text-right font-mono-ui text-xs text-foreground">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function DisabledApprovalActions() {
  return (
    <div className="space-y-2">
      <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        {approvalActionLabels.map((label) => (
          <Button key={label} disabled aria-disabled="true" type="button" variant="outline">
            {label}
          </Button>
        ))}
      </div>
      <p className="font-display text-xs text-warning">
        Preview-only: approval execution is not wired in this PR. Estado preview-only/read-only.
      </p>
    </div>
  );
}

function ApprovalCardView({ card }: { card: JarvisApprovalCard }) {
  const confirmations = [
    ["readback", card.requires_readback],
    ["confirmación fuerte", card.strong_confirmation_required],
    ["doble confirmación", card.double_confirmation_required],
    ["triple confirmación", card.triple_confirmation_required],
    ["rollback", card.rollback_required],
    ["stop plan", card.stop_plan_required],
    ["auditoría", card.audit_required],
  ] as const;

  return (
    <article className="border border-border/70 bg-background/35 p-4">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="warning">preview/read-only</Badge>
            <Badge variant={approvalStatusVariant(valueText(card.status))}>{valueText(card.status)}</Badge>
            <Badge variant={riskVariant(valueText(card.risk_level))}>riesgo: {valueText(card.risk_level)}</Badge>
            <Badge variant={approvalLevelVariant(valueText(card.approval_level))}>approval: {valueText(card.approval_level)}</Badge>
          </div>
          <h3 className="font-expanded text-base font-bold uppercase tracking-[0.08em]">{valueText(card.title)}</h3>
        </div>
        <span className="max-w-full break-all font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(card.id)}</span>
      </div>

      <div className="grid gap-3 lg:grid-cols-[1fr_0.95fr]">
        <div className="space-y-3">
          <StatusList
            items={[
              ["acción", valueText(card.action)],
              ["razón", valueText(card.reason)],
              ["scope", valueText(card.scope_summary)],
              ["evidencia", valueText(card.evidence_summary)],
              ["coste estimado", valueText(card.estimated_cost)],
              ["coste medido", valueText(card.measured_cost)],
              ["expira", valueText(card.expires_at)],
            ]}
          />
          <div className="flex flex-wrap gap-2">
            {(card.touches?.length ? card.touches : ["unknown"]).map((touch) => (
              <Badge key={`${card.id}-${touch}`} variant={touch === "credentials" ? "destructive" : "outline"}>
                {touch}
              </Badge>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <div className="border border-border/70 bg-background/30 p-3">
            <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">rollback</p>
            <p className="mt-1 font-mono-ui text-xs text-foreground">{valueText(card.rollback_plan)}</p>
          </div>
          <div className="border border-border/70 bg-background/30 p-3">
            <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">stop plan</p>
            <p className="mt-1 font-mono-ui text-xs text-foreground">{valueText(card.stop_plan)}</p>
          </div>
          <div className="border border-warning/40 bg-warning/10 p-3">
            <p className="font-display text-xs uppercase tracking-[0.12em] text-warning">disabled</p>
            <p className="mt-1 font-mono-ui text-xs text-warning">{valueText(card.disabled_reason)}</p>
            <p className="mt-2 font-mono-ui text-xs text-muted-foreground">{valueText(card.recommended_operator_action)}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {confirmations.map(([label, enabled]) => (
              <Badge key={`${card.id}-${label}`} variant={enabled ? "warning" : "outline"}>
                {label}: {yesNo(enabled, "sí", "no")}
              </Badge>
            ))}
          </div>
          <DisabledApprovalActions />
        </div>
      </div>
    </article>
  );
}

function SafetyLine({ children }: { children: React.ReactNode }) {
  return (
    <p className="border-l-2 border-warning/70 bg-warning/10 px-3 py-2 font-display text-xs text-warning">
      {children}
    </p>
  );
}

export default function JarvisCommandCenterPage() {
  const [dashboard, setDashboard] = useState<JarvisDashboardStatus>(() => fallbackDashboard("loading"));
  const [connectionState, setConnectionState] = useState<"loading" | "online" | "offline">("loading");

  useEffect(() => {
    let active = true;
    api.getJarvisDashboardStatus()
      .then((payload) => {
        if (!active) return;
        setDashboard(payload);
        setConnectionState("online");
      })
      .catch(() => {
        if (!active) return;
        setDashboard(fallbackDashboard("offline"));
        setConnectionState("offline");
      });
    return () => {
      active = false;
    };
  }, []);

  const modules = useMemo(() => readModules(dashboard.modules), [dashboard.modules]);
  const system = dashboard.system ?? {};
  const contract = dashboard.jarvis_hermes_contract ?? {};
  const approvals = dashboard.approvals ?? {};
  const approvalCards = approvals.cards?.length ? approvals.cards : fallbackApprovalCards;
  const hermes = dashboard.hermes_execution ?? {};
  const hermesContract = hermes.contract ?? contract;
  const hermesRuntime = hermes.runtime_status ?? hermes;
  const hermesCapabilities = readHermesCapabilities(hermes.governed_capabilities);
  const hermesBlockedRoutes = readHermesBlockedRoutes(hermes.blocked_routes);
  const voiceCore = dashboard.voice_core ?? fallbackVoiceCore;
  const voiceCoreState = voiceCore.state ?? fallbackVoiceCore.state ?? {};
  const voiceVisualStates = voiceCore.visual_states?.length ? voiceCore.visual_states : fallbackVoiceVisualStates;
  const ttsState = voiceCore.tts_state ?? fallbackVoiceCore.tts_state ?? {};
  const wakeWordPolicy = voiceCore.wake_word_policy ?? fallbackVoiceCore.wake_word_policy ?? {};
  const voicePrivacy = voiceCore.privacy ?? fallbackVoiceCore.privacy ?? {};
  const voiceSafety = voiceCore.safety ?? fallbackVoiceCore.safety ?? {};
  const voiceRelationship = voiceCore.relationship ?? fallbackVoiceCore.relationship ?? {};
  const voiceKillSwitch = voiceCore.kill_switch ?? fallbackVoiceCore.kill_switch ?? {};
  const wakeWordFlow = dashboard.wake_word_flow ?? fallbackWakeWordFlow;
  const wakeFlowState = wakeWordFlow.state ?? fallbackWakeWordFlow.state ?? {};
  const wakeModeExplanations = wakeWordFlow.mode_explanations ?? fallbackWakeWordFlow.mode_explanations ?? {};
  const wakeParsePreview = wakeWordFlow.wake_parse_preview ?? fallbackWakeWordFlow.wake_parse_preview ?? {};
  const wakeApprovalPolicy = wakeWordFlow.approval_policy ?? fallbackWakeWordFlow.approval_policy ?? {};
  const wakeFlowSafety = wakeWordFlow.safety ?? fallbackWakeWordFlow.safety ?? {};
  const wakeSupportedPhrases = wakeWordFlow.supported_phrases?.length
    ? wakeWordFlow.supported_phrases
    : fallbackWakeWordFlow.supported_phrases ?? [];
  const wakeStopPhrases = wakeWordFlow.stop_phrases?.length
    ? wakeWordFlow.stop_phrases
    : fallbackWakeWordFlow.stop_phrases ?? [];
  const cameraVision = dashboard.camera_vision ?? fallbackCameraVision;
  const cameraVisionState = cameraVision.state ?? fallbackCameraVision.state ?? {};
  const cameraVisionPrivacy = cameraVision.privacy ?? fallbackCameraVision.privacy ?? {};
  const cameraVisionStates = cameraVision.states?.length ? cameraVision.states : fallbackCameraVisionStates;
  const cameraVisionScope = cameraVision.scope_policy ?? fallbackCameraVision.scope_policy ?? {};
  const mobileCompanion = dashboard.mobile_companion ?? fallbackMobileCompanion;
  const mobileCompanionState = mobileCompanion.state ?? fallbackMobileCompanion.state ?? {};
  const mobileCompanionViews = mobileCompanion.mobile_views?.length
    ? mobileCompanion.mobile_views
    : fallbackMobileViews;
  const mobileSafety = mobileCompanion.safety ?? fallbackMobileCompanion.safety ?? {};
  const pwaPolicy = mobileCompanion.pwa_policy ?? fallbackMobileCompanion.pwa_policy ?? {};
  const financeRoi = dashboard.finance_roi ?? fallbackFinanceRoi;
  const financeMetrics = financeRoi.metrics ?? fallbackFinanceRoi.metrics ?? {};
  const financeBudget = financeRoi.budget ?? fallbackFinanceRoi.budget ?? {};
  const financeSafety = financeRoi.safety ?? fallbackFinanceRoi.safety ?? {};
  const adaptiveProductBuilder = dashboard.adaptive_product_builder ?? fallbackAdaptiveProductBuilder;
  const productBuilderState = adaptiveProductBuilder.state ?? fallbackAdaptiveProductBuilder.state ?? {};
  const productBuilderStages = adaptiveProductBuilder.stages?.length
    ? adaptiveProductBuilder.stages
    : fallbackBuilderStages;
  const productDifferentiation =
    adaptiveProductBuilder.differentiation_policy ?? fallbackAdaptiveProductBuilder.differentiation_policy ?? {};
  const productMonetization =
    adaptiveProductBuilder.monetization_policy ?? fallbackAdaptiveProductBuilder.monetization_policy ?? {};
  const productBuilderSafety = adaptiveProductBuilder.safety ?? fallbackAdaptiveProductBuilder.safety ?? {};
  const frontendPilot = dashboard.frontend_pilot ?? fallbackFrontendPilot;
  const frontendPilotState = frontendPilot.state ?? fallbackFrontendPilot.state ?? {};
  const frontendReadinessChecks = frontendPilot.readiness_checks?.length
    ? frontendPilot.readiness_checks
    : fallbackFrontendChecks;
  const frontendHardening = frontendPilot.hardening_notes ?? fallbackFrontendPilot.hardening_notes ?? {};
  const frontendLimitations = frontendPilot.pilot_limitations?.length
    ? frontendPilot.pilot_limitations
    : fallbackFrontendPilot.pilot_limitations ?? [];
  const visualPilot = dashboard.visual_command_center_pilot ?? fallbackVisualCommandCenterPilot;
  const visualPilotState = visualPilot.state ?? fallbackVisualCommandCenterPilot.state ?? {};
  const visualPilotPanels = visualPilot.required_panels?.length
    ? visualPilot.required_panels
    : fallbackVisualPilotPanels;
  const visualPilotChecks = visualPilot.read_only_checks?.length
    ? visualPilot.read_only_checks
    : fallbackVisualPilotChecks;
  const visualPilotSteps = visualPilot.operator_pilot_steps?.length
    ? visualPilot.operator_pilot_steps
    : fallbackOperatorPilotSteps;
  const visualPilotFindings = visualPilot.pilot_findings?.findings ?? [];
  const visualPilotLimitations = visualPilot.pilot_findings?.known_limitations?.length
    ? visualPilot.pilot_findings.known_limitations
    : fallbackVisualCommandCenterPilot.pilot_findings?.known_limitations ?? [];
  const visualPilotSafety = visualPilot.safety ?? fallbackVisualCommandCenterPilot.safety ?? {};
  const timeline = dashboard.timeline?.length ? dashboard.timeline : fallbackDashboard("error").timeline ?? [];
  const missionControl = dashboard.mission_control ?? fallbackMissionControl;
  const missionState = missionControl.state ?? fallbackMissionControl.state ?? {};
  const missionSupportedInputs = missionControl.supported_inputs ?? fallbackMissionControl.supported_inputs ?? {};
  const missionIntent = missionControl.intent_preview ?? fallbackMissionControl.intent_preview ?? {};
  const missionConversation = missionControl.conversation_preview ?? fallbackMissionControl.conversation_preview ?? {};
  const missionMessages = missionConversation.messages?.length
    ? missionConversation.messages
    : fallbackMissionControl.conversation_preview?.messages ?? [];
  const missionSafety = missionControl.safety ?? fallbackMissionControl.safety ?? {};
  const missionGuidance = missionControl.operator_guidance ?? fallbackMissionControl.operator_guidance ?? {};
  const requiredPermissions = missionIntent.required_permissions?.length
    ? missionIntent.required_permissions.join(", ")
    : "none/unknown";
  const blockedReasons = missionIntent.blocked_reasons?.length
    ? missionIntent.blocked_reasons.join(", ")
    : "none";
  const nextSafeAction =
    missionIntent.next_safe_action && missionIntent.next_safe_action !== UNKNOWN
      ? missionIntent.next_safe_action
      : "operator review";

  const missionStateRows = [
    ["mode", valueText(missionState.mode, "preview")],
    ["input", valueText(missionState.input_enabled, "preview_only")],
    ["conversation", valueText(missionState.conversation_enabled, "preview_only")],
    ["execution", yesNo(missionState.execution_enabled, "enabled", "false")],
    ["Hermes dispatch", yesNo(missionState.hermes_dispatch_enabled, "enabled", "false")],
    ["approval creation", yesNo(missionState.approval_creation_enabled, "enabled", "false")],
    ["persistence", yesNo(missionState.persistence_enabled, "enabled", "false")],
    ["external network", yesNo(missionState.external_network_enabled, "enabled", "false")],
  ] as const;

  const supportedInputRows = [
    ["text command", valueText(missionSupportedInputs.text_command, "preview")],
    ["voice command", valueText(missionSupportedInputs.voice_command, "future_gated")],
    ["mobile command", valueText(missionSupportedInputs.mobile_command, "future_gated")],
    ["wake word command", valueText(missionSupportedInputs.wake_word_command, "future_gated")],
    ["file drop", valueText(missionSupportedInputs.file_drop, "not_connected")],
    ["camera context", valueText(missionSupportedInputs.camera_context, "not_connected")],
  ] as const;

  const missionIntentRows = [
    ["intención detectada", `${valueText(missionIntent.detected_intent)}/preview`],
    ["confidence", valueText(missionIntent.confidence)],
    ["mission type", valueText(missionIntent.mission_type)],
    ["riesgo", valueText(missionIntent.risk_level)],
    ["approval", valueText(missionIntent.approval_level)],
    ["permisos requeridos", requiredPermissions],
    ["blocked reasons", blockedReasons],
    ["siguiente acción segura", nextSafeAction],
  ] as const;

  const conversationPreviewRows = [
    ["assistant status", valueText(missionConversation.assistant_status, "preview")],
    ["transcript persistence", yesNo(missionConversation.transcript_persistence, "true", "false")],
    ["memory write", yesNo(missionConversation.memory_write, "true", "false")],
    ["memory read", valueText(missionConversation.memory_read, "false")],
    ["PII redaction", yesNo(missionConversation.pii_redaction_required, "required", "false")],
    ["raw audio stored", yesNo(missionConversation.raw_audio_stored, "true", "false")],
    ["external provider called", yesNo(missionConversation.external_provider_called, "true", "false")],
  ] as const;

  const cameraCurrentRows = [
    ["cámara", cameraVisionState.camera_enabled ? "enabled" : "off/disabled"],
    ["permiso solicitado", yesNo(cameraVisionState.camera_permission_requested, "true", "false")],
    ["preview", cameraVisionState.preview_enabled ? "enabled" : "disabled"],
    ["recording", yesNo(cameraVisionState.recording ?? cameraVision.recording, "true", "false")],
    ["streaming", yesNo(cameraVisionState.streaming ?? cameraVision.streaming, "true", "false")],
    ["snapshot", cameraVisionState.snapshot_capture_enabled ? "enabled" : valueText(cameraVision.snapshot, "disabled")],
    ["vision analysis", cameraVisionState.vision_analysis_enabled ? "enabled" : valueText(cameraVision.vision_analysis, "disabled")],
    ["storage", cameraVisionState.image_storage_enabled || cameraVisionState.video_storage_enabled ? "on" : "off"],
    [
      "provider externo",
      cameraVisionState.external_vision_provider_called ? "called" : valueText(cameraVision.provider, "none/not_connected"),
    ],
    ["modelo local", valueText(cameraVisionState.local_vision_model_connected)],
    ["background camera access", yesNo(cameraVisionState.background_camera_access, "true", "false")],
  ] as const;

  const cameraPrivacyRows = [
    ["no camera activation", yesNo(cameraVisionPrivacy.no_camera_activation, "true", "false")],
    ["no getUserMedia", yesNo(cameraVisionPrivacy.no_get_user_media, "true", "false")],
    ["no recording", yesNo(cameraVisionPrivacy.no_recording, "true", "false")],
    ["no snapshot", yesNo(cameraVisionPrivacy.no_snapshot_capture, "true", "false")],
    ["no image/video storage", cameraVisionPrivacy.no_image_storage && cameraVisionPrivacy.no_video_storage ? "true" : "false"],
    [
      "explicit operator permission required",
      yesNo(cameraVisionPrivacy.explicit_operator_permission_required, "true", "false"),
    ],
    ["visual indicator required", yesNo(cameraVisionPrivacy.visual_indicator_required_when_camera_active, "true", "false")],
    ["audit required", yesNo(cameraVisionPrivacy.audit_required_for_future_vision, "true", "false")],
  ] as const;

  const cameraScopeRows = [
    ["allowed scope", valueText(cameraVisionScope.allowed_scope, "none/unknown")],
    [
      "future operator permission",
      yesNo(cameraVisionScope.future_scope_requires_explicit_operator_permission, "required", "false"),
    ],
    ["future states what it can see", yesNo(cameraVisionScope.future_analysis_must_state_what_it_can_see, "true", "false")],
    [
      "no sensitive identity inference",
      yesNo(cameraVisionScope.future_analysis_must_not_infer_sensitive_identity, "true", "false"),
    ],
    [
      "no storage without permission",
      yesNo(cameraVisionScope.future_analysis_must_not_store_without_permission, "true", "false"),
    ],
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
    ["mobile ejecuta", yesNo(mobileCompanionState.mobile_can_execute, "true", "false")],
    ["red externa requerida", yesNo(mobileCompanionState.external_network_required, "true", "false")],
  ] as const;

  const pwaRows = [
    ["installable PWA", valueText(pwaPolicy.installable_pwa, "preview")],
    ["offline cache", yesNo(pwaPolicy.offline_cache_enabled, "enabled", "disabled")],
    ["service worker", yesNo(pwaPolicy.service_worker_enabled, "enabled", "disabled")],
    ["push", yesNo(pwaPolicy.push_notifications_enabled, "enabled", "disabled")],
    ["background sync", pwaPolicy.no_background_sync ? "disabled" : UNKNOWN],
    ["credentials storage", pwaPolicy.no_credentials_storage ? "disabled" : UNKNOWN],
    ["token storage", pwaPolicy.no_token_storage ? "disabled" : UNKNOWN],
  ] as const;

  const mobileSafetyRows = [
    ["mobile es interfaz", yesNo(mobileSafety.mobile_is_interface_not_runtime, "true", "false")],
    ["no direct Hermes call", yesNo(mobileSafety.no_direct_hermes_call, "true", "false")],
    ["no mobile execute", yesNo(mobileSafety.no_mobile_execute, "true", "false")],
    ["no mobile sensor activation", yesNo(mobileSafety.no_mobile_sensor_activation, "true", "false")],
    ["no real mobile approvals in this PR", yesNo(mobileSafety.no_real_mobile_approval_in_this_pr, "true", "false")],
    ["approval requires backend gate", yesNo(mobileSafety.approval_requires_backend_gate, "true", "false")],
    [
      "critical approval requires strong confirmation",
      yesNo(mobileSafety.critical_approval_requires_strong_confirmation, "true", "false"),
    ],
    ["remote kill switch future gated", yesNo(mobileSafety.remote_kill_switch_future_gated, "true", "false")],
  ] as const;

  const financeMetricValue = (metric?: JarvisFinanceMetric) => valueText(metric?.value);
  const financeRows = [
    ["coste real", financeMetricValue(financeMetrics.actual_cost)],
    ["coste estimado", financeMetricValue(financeMetrics.estimated_cost)],
    ["revenue confirmado", financeMetricValue(financeMetrics.confirmed_revenue)],
    ["revenue proyectado", financeMetricValue(financeMetrics.projected_revenue)],
    ["gross revenue", financeMetricValue(financeMetrics.gross_revenue)],
    ["expenses", financeMetricValue(financeMetrics.expenses)],
    ["net revenue", financeMetricValue(financeMetrics.net_revenue)],
    ["ROI", financeMetricValue(financeMetrics.roi)],
    ["token cost", financeMetricValue(financeMetrics.token_cost)],
    ["API cost", financeMetricValue(financeMetrics.api_cost)],
    ["infra cost", financeMetricValue(financeMetrics.infra_cost)],
    ["manual input cost", financeMetricValue(financeMetrics.manual_input_cost)],
    ["revenue source", financeMetricValue(financeMetrics.revenue_source)],
  ] as const;

  const financeBudgetRows = [
    ["budget", financeBudget.budget_configured === false ? "not configured" : valueText(financeBudget.budget_configured)],
    ["remaining budget", valueText(financeBudget.remaining_budget)],
    ["monthly limit", valueText(financeBudget.monthly_limit)],
    ["alert threshold", valueText(financeBudget.alert_threshold)],
    ["hard stop", yesNo(financeBudget.hard_stop_enabled, "enabled", "false")],
    ["notes", valueText(financeBudget.notes)],
  ] as const;

  const productBuilderStateRows = [
    ["mode", valueText(productBuilderState.mode, "preview")],
    ["builder", valueText(productBuilderState.builder_enabled, "preview/read_only")],
    ["product generation", yesNo(productBuilderState.product_generation_enabled, "enabled", "false")],
    ["code generation", yesNo(productBuilderState.code_generation_enabled, "enabled", "false")],
    ["deploy", yesNo(productBuilderState.deploy_enabled, "enabled", "false")],
    ["stripe", yesNo(productBuilderState.stripe_enabled, "enabled", "false")],
    ["landing publish", yesNo(productBuilderState.landing_publish_enabled, "enabled", "false")],
    ["external research", yesNo(productBuilderState.external_research_enabled, "enabled", "false")],
    ["Hermes dispatch", yesNo(productBuilderState.hermes_dispatch_enabled, "enabled", "false")],
  ] as const;

  const frontendPilotRows = [
    ["mode", valueText(frontendPilotState.mode, "read_only_pilot")],
    ["route", valueText(frontendPilotState.dashboard_route, "/jarvis")],
    ["endpoint", valueText(frontendPilotState.backend_status_endpoint, DASHBOARD_READ_MODEL_ENDPOINT)],
    ["execute", yesNo(frontendPilotState.frontend_can_execute, "true", "false")],
    ["approve", yesNo(frontendPilotState.frontend_can_approve, "true", "false")],
    ["sensors", yesNo(frontendPilotState.frontend_can_activate_sensors, "true", "false")],
    ["money", yesNo(frontendPilotState.frontend_can_move_money, "true", "false")],
    ["deploy", yesNo(frontendPilotState.frontend_can_deploy, "true", "false")],
    ["email", yesNo(frontendPilotState.frontend_can_send_email, "true", "false")],
  ] as const;

  const frontendHardeningRows = [
    ["npm audit vulnerabilities observed", valueText(frontendHardening.npm_audit_vulnerabilities_observed)],
    ["npm audit fix not run", yesNo(frontendHardening.npm_audit_fix_not_run, "true", "false")],
    [
      "dependency hardening separate PR",
      yesNo(frontendHardening.dependency_hardening_requires_separate_pr, "true", "false"),
    ],
    ["no lockfile changes expected", yesNo(frontendHardening.no_lockfile_changes_expected, "true", "false")],
    ["frontend build required before merge", yesNo(frontendHardening.frontend_build_required_before_merge, "true", "false")],
    ["full pytest required before merge", yesNo(frontendHardening.full_pytest_required_before_merge, "true", "false")],
  ] as const;

  const visualPilotRows = [
    ["mode", valueText(visualPilotState.mode, "read_only_pilot")],
    ["route", valueText(visualPilotState.dashboard_route, "/jarvis")],
    ["endpoint", valueText(visualPilotState.status_endpoint, DASHBOARD_READ_MODEL_ENDPOINT)],
    ["backend read model", yesNo(visualPilotState.backend_read_model_connected, "connected", "unknown")],
    ["frontend execution", yesNo(visualPilotState.frontend_execution_enabled, "enabled", "false")],
    ["real approvals", yesNo(visualPilotState.approvals_real_enabled, "enabled", "false")],
    ["Hermes direct execution", yesNo(visualPilotState.hermes_direct_execution_enabled, "enabled", "false")],
    ["real voice", yesNo(visualPilotState.voice_real_enabled, "enabled", "false")],
    ["real camera", yesNo(visualPilotState.camera_real_enabled, "enabled", "false")],
    ["mobile runtime", yesNo(visualPilotState.mobile_runtime_enabled, "enabled", "false")],
    ["money", yesNo(visualPilotState.money_enabled, "enabled", "false")],
    ["deploy", yesNo(visualPilotState.deploy_enabled, "enabled", "false")],
    ["email", yesNo(visualPilotState.email_enabled, "enabled", "false")],
    ["credentials", yesNo(visualPilotState.credentials_enabled, "enabled", "false")],
  ] as const;

  const criticalButtonRows = [
    ["mission submit", "disabled / preview-only"],
    ["approval actions", approvals.action_buttons_enabled ? "unexpected enabled" : "disabled"],
    ["Hermes execution", hermes.frontend_can_execute ? "unexpected enabled" : "disabled"],
    ["voice controls", visualPilotState.voice_real_enabled ? "unexpected enabled" : "disabled"],
    ["camera controls", visualPilotState.camera_real_enabled ? "unexpected enabled" : "disabled"],
    ["money controls", visualPilotState.money_enabled ? "unexpected enabled" : "disabled"],
    ["deploy controls", visualPilotState.deploy_enabled ? "unexpected enabled" : "disabled"],
    ["Kill Switch", "visible / disabled / read-only"],
  ] as const;

  const visualPilotSafetyRows = [
    ["pilot_is_read_only", yesNo(visualPilotSafety.pilot_is_read_only, "true", "false")],
    ["dashboard_may_read_status_only", yesNo(visualPilotSafety.dashboard_may_read_status_only, "true", "false")],
    ["no_side_effects", yesNo(visualPilotSafety.no_side_effects, "true", "false")],
    ["no_real_world_actions", yesNo(visualPilotSafety.no_real_world_actions, "true", "false")],
    ["no_background_workers", yesNo(visualPilotSafety.no_background_workers, "true", "false")],
    ["no_sensors", yesNo(visualPilotSafety.no_sensors, "true", "false")],
    ["no_money", yesNo(visualPilotSafety.no_money, "true", "false")],
    ["no_production", yesNo(visualPilotSafety.no_production, "true", "false")],
    ["no_credentials", yesNo(visualPilotSafety.no_credentials, "true", "false")],
    [
      "approval gates, not permanent bans",
      yesNo(visualPilotSafety.restrictions_are_approval_gates_not_permanent_bans, "true", "false"),
    ],
  ] as const;

  const hermesCurrentRows = [
    ["Hermes disponible", yesNo(hermesRuntime.available, "sí", "no")],
    ["Hermes conectado", yesNo(hermesRuntime.connected, "sí", "no")],
    ["ejecución activa", yesNo(hermesRuntime.active_execution, "sí", "no")],
    ["modo", valueText(hermesRuntime.execution_mode, "read_only_visibility")],
    ["última ejecución", valueText(hermesRuntime.last_execution)],
    ["último resultado", valueText(hermesRuntime.last_result)],
    ["último error", valueText(hermesRuntime.last_error)],
    ["coste", valueText(hermesRuntime.measured_cost)],
    ["duración", valueText(hermesRuntime.measured_duration)],
  ] as const;

  const voiceCoreRows = [
    ["mode", valueText(voiceCoreState.mode, "preview")],
    ["estado actual", valueText(voiceCoreState.current_state, "preview")],
    ["micrófono", yesNo(voiceCoreState.microphone_enabled, "enabled", "disabled")],
    ["wake word", yesNo(voiceCoreState.wake_word_enabled, "enabled", "disabled")],
    ["escucha orden", yesNo(voiceCoreState.command_listening_enabled, "enabled", "disabled")],
    ["TTS", yesNo(voiceCoreState.tts_enabled, "enabled", "disabled")],
    ["STT", yesNo(voiceCoreState.stt_enabled, "enabled", "disabled")],
    ["grabación", yesNo(voiceCoreState.audio_recording, "true", "false")],
    ["audio bruto almacenado", yesNo(voiceCoreState.raw_audio_stored, "true", "false")],
    ["provider externo llamado", yesNo(voiceCoreState.external_provider_called, "true", "false")],
    ["voice approval", yesNo(voiceCoreState.voice_approval_enabled, "enabled", "disabled")],
  ] as const;

  const ttsRows = [
    ["status", valueText(ttsState.status, "preview")],
    ["speaking", yesNo(ttsState.speaking, "true", "false")],
    ["last utterance", valueText(ttsState.last_utterance, previewVoiceSubtitle)],
    ["subtitles", yesNo(ttsState.subtitles_enabled, "enabled", "disabled")],
    ["subtitles source", valueText(ttsState.subtitles_source, "preview/read_model")],
    ["audio output", yesNo(ttsState.audio_output_enabled, "enabled", "disabled")],
    ["provider", valueText(ttsState.provider, "none/not_connected")],
    ["external call", yesNo(ttsState.external_call, "true", "false")],
  ] as const;

  const wakePolicyRows = [
    ["frases futuras", wakeWordPolicy.supported_phrases?.join(", ") || "Hola Jarvis, Jarvis"],
    ["runtime wake word", valueText(wakeWordPolicy.wake_word_runtime, "disabled")],
    ["wake phrase es permiso", yesNo(wakeWordPolicy.wake_phrase_is_permission, "true", "false")],
    ["wake phrase aprueba", yesNo(wakeWordPolicy.wake_phrase_can_approve, "true", "false")],
    ["wake phrase ejecuta", yesNo(wakeWordPolicy.wake_phrase_can_execute, "true", "false")],
    ["approval autenticado", yesNo(wakeWordPolicy.requires_authenticated_channel_for_approval, "required", "false")],
    ["readback crítico", yesNo(wakeWordPolicy.critical_actions_require_readback, "required", "false")],
    ["confirmación fuerte", yesNo(wakeWordPolicy.critical_actions_require_strong_confirmation, "required", "false")],
  ] as const;

  const voicePrivacyRows = [
    ["micrófono: disabled", yesNo(voicePrivacy.no_microphone_activation, "true", "false")],
    ["grabación: false", yesNo(voicePrivacy.no_audio_recording, "true", "false")],
    ["audio bruto almacenado: false", yesNo(voicePrivacy.no_raw_audio_storage, "true", "false")],
    ["proveedor externo", voicePrivacy.no_external_audio_provider ? "none/not_connected" : UNKNOWN],
    ["background listening", voicePrivacy.no_background_listening_enabled ? "disabled" : UNKNOWN],
    ["voice biometrics", voicePrivacy.no_voice_biometrics ? "disabled" : UNKNOWN],
    ["voice approval", voicePrivacy.no_voice_approval_without_gate ? "disabled/future gated" : UNKNOWN],
  ] as const;

  const voiceRelationshipRows = [
    ["prepara intención futura", yesNo(voiceRelationship.voice_can_prepare_future_intention, "true", "false")],
    ["Approval Console", yesNo(voiceRelationship.approval_console_handles_required_approval, "required", "false")],
    ["Hermes tras approval", yesNo(voiceRelationship.hermes_executes_only_after_valid_approval, "true", "false")],
    ["voz/frontend llama Hermes", yesNo(voiceRelationship.frontend_or_voice_can_call_hermes_directly, "allowed", "false")],
  ] as const;

  const wakeFlowStateRows = [
    ["mode", valueText(wakeFlowState.mode, "preview")],
    ["micrófono hard-off", yesNo(wakeFlowState.microphone_hard_off, "true", "false")],
    ["wake runtime", yesNo(wakeFlowState.wake_runtime_enabled, "enabled", "disabled")],
    ["command window", yesNo(wakeFlowState.command_window_open, "open", "closed")],
    ["push-to-talk preview", yesNo(wakeFlowState.push_to_talk_preview_enabled, "enabled", "disabled")],
    ["typed wake preview", yesNo(wakeFlowState.typed_wake_preview_enabled, "enabled", "disabled")],
    ["always-on microphone", yesNo(wakeFlowState.always_on_microphone_enabled, "enabled", "disabled")],
    ["background listener", yesNo(wakeFlowState.background_listener_enabled, "enabled", "disabled")],
  ] as const;

  const wakeParseRows = [
    ["wake phrase detectada", valueText(wakeParsePreview.detected_wake_phrase, "Hola Jarvis")],
    ["comando restante", valueText(wakeParsePreview.remaining_command_preview, "revisa el estado del proyecto")],
    ["abriría ventana de comando", yesNo(wakeParsePreview.would_open_command_window, "sí, en futuro", "no")],
    ["ejecutaría", yesNo(wakeParsePreview.would_execute, "sí", "no")],
    ["aprobaría", yesNo(wakeParsePreview.would_approve, "sí", "no")],
    ["llamaría Hermes", yesNo(wakeParsePreview.would_call_hermes, "sí", "no")],
    ["grabaria audio", yesNo(wakeParsePreview.would_record_audio, "sí", "no")],
    ["llamaría provider", yesNo(wakeParsePreview.would_call_provider, "sí", "no")],
    ["status", valueText(wakeParsePreview.status, "preview_only")],
  ] as const;

  const wakeApprovalRows = [
    ["wake phrase es permiso", yesNo(wakeApprovalPolicy.wake_phrase_is_permission, "true", "false")],
    ["wake phrase aprueba", yesNo(wakeApprovalPolicy.wake_phrase_can_approve, "true", "false")],
    ["wake phrase ejecuta", yesNo(wakeApprovalPolicy.wake_phrase_can_execute, "true", "false")],
    ["canal autenticado", yesNo(wakeApprovalPolicy.voice_approval_requires_authenticated_channel, "required", "false")],
    ["readback sensible", yesNo(wakeApprovalPolicy.sensitive_actions_require_readback, "required", "false")],
    [
      "doble/triple crítica",
      yesNo(wakeApprovalPolicy.critical_actions_require_double_or_triple_confirmation, "required", "false"),
    ],
    ["audit events", yesNo(wakeApprovalPolicy.approval_events_must_be_audited, "required", "false")],
  ] as const;

  return (
    <div className="flex flex-col gap-6">
      <section className="border border-border bg-card/70 p-5">
        <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={connectionState === "online" ? "success" : connectionState === "offline" ? "destructive" : "outline"}>
                API: {valueText(system.api_status)}
              </Badge>
              <Badge variant="outline">Modo: {valueText(system.mode)}</Badge>
              <Badge variant="warning">Sin autonomía libre</Badge>
              <Badge variant="outline">Read model: {DASHBOARD_READ_MODEL_ENDPOINT}</Badge>
            </div>
            <div className="space-y-2">
              <h1 className="font-expanded text-3xl font-bold uppercase tracking-[0.08em] blend-lighter md:text-5xl">
                Centro de Mando JARVIS
              </h1>
              <p className="max-w-3xl font-display text-base text-muted-foreground">
                JARVIS gobierna. Hermes ejecuta.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">autonomía</p>
                <p className="mt-1 font-mono-ui text-sm">{yesNo(system.free_autonomy_enabled, "libre", "Sin autonomía libre")}</p>
              </div>
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">runtime</p>
                <p className="mt-1 font-mono-ui text-sm">{yesNo(contract.frontend_can_execute, "frontend ejecuta", "read-only shell")}</p>
              </div>
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">sensores</p>
                <p className="mt-1 font-mono-ui text-sm">disabled</p>
              </div>
            </div>
          </div>

          <aside className="border border-destructive/50 bg-destructive/10 p-4">
            <div className="flex items-center gap-3">
              <ShieldAlert className="h-6 w-6 text-destructive" />
              <div>
                <h2 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-destructive">
                  Kill Switch
                </h2>
                <p className="font-mono-ui text-xs text-destructive/80">{valueText(system.kill_switch_state, "not_wired")}</p>
              </div>
            </div>
            <Button disabled type="button" variant="destructive" className="mt-4 w-full">
              KILL SWITCH
            </Button>
            <p className="mt-3 font-display text-xs text-destructive/80">
              No hay ejecución real que detener desde este panel. No hay ejecución real que detener desde esta shell.
              Cuando se conecte a ejecución real, deberá cortar o pausar flujos gobernados.
            </p>
          </aside>
        </div>
      </section>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-success" />
            <CardTitle>Visual Command Center Pilot</CardTitle>
          </div>
          <CardDescription>
            Piloto local read-only del cockpit completo. El dashboard mira, no toca.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <article className="border border-success/40 bg-success/10 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="success">read-only pilot</Badge>
              <Badge variant="outline">{valueText(visualPilotState.dashboard_route, "/jarvis")}</Badge>
              <Badge variant="outline">{valueText(visualPilotState.status_endpoint, DASHBOARD_READ_MODEL_ENDPOINT)}</Badge>
              <Badge variant={visualPilotState.frontend_execution_enabled ? "destructive" : "success"}>
                execute: {yesNo(visualPilotState.frontend_execution_enabled, "enabled", "false")}
              </Badge>
              <Badge variant={visualPilotState.approvals_real_enabled ? "destructive" : "success"}>
                approvals reales: {yesNo(visualPilotState.approvals_real_enabled, "enabled", "false")}
              </Badge>
            </div>
            <div className="mt-4 grid gap-2 md:grid-cols-2 xl:grid-cols-4">
              <SafetyLine>El dashboard mira, no toca.</SafetyLine>
              <SafetyLine>No se ejecuta Hermes desde el frontend.</SafetyLine>
              <SafetyLine>No se activan sensores.</SafetyLine>
              <SafetyLine>No hay approvals reales en esta fase.</SafetyLine>
              <SafetyLine>No hay métricas falsas.</SafetyLine>
              <SafetyLine>Los valores sin evidencia se muestran como unknown.</SafetyLine>
              <SafetyLine>Dependency hardening queda para una PR separada.</SafetyLine>
            </div>
          </article>

          <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Ruta / endpoint / modo</h3>
              <div className="mt-3">
                <StatusList items={visualPilotRows} />
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Checklist de panels</h3>
                <Badge variant="warning">required panels</Badge>
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                {visualPilotPanels.map((panel) => (
                  <div key={panel.name} className="min-h-28 border border-border/70 bg-background/40 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="font-display text-sm">{panel.name}</p>
                      <Badge variant={statusVariant(valueText(panel.status))}>{valueText(panel.status)}</Badge>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Badge variant={panel.expected ? "success" : "destructive"}>
                        expected: {yesNo(panel.expected, "true", "false")}
                      </Badge>
                      <Badge variant={panel.can_execute ? "destructive" : "success"}>
                        can_execute: {yesNo(panel.can_execute, "true", "false")}
                      </Badge>
                    </div>
                    <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(panel.source)}</p>
                    <p className="mt-1 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(panel.notes)}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-border/70 bg-background/35 p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Checklist de seguridad</h3>
                <Badge variant="success">read-only checks</Badge>
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                {visualPilotChecks.map((check) => (
                  <div key={check.name} className="border border-border/70 bg-background/40 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="font-mono-ui text-xs text-foreground">{check.name}</p>
                      <Badge variant={check.status === "passed" ? "success" : statusVariant(check.status)}>
                        {valueText(check.status)}
                      </Badge>
                    </div>
                    <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(check.evidence)}</p>
                    <p className="mt-1 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(check.notes)}</p>
                  </div>
                ))}
              </div>
            </article>

            <div className="space-y-4">
              <article className="border border-warning/40 bg-warning/10 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-warning">
                  Estado de botones críticos
                </h3>
                <div className="mt-3">
                  <StatusList items={criticalButtonRows} />
                </div>
              </article>

              <article className="border border-border/70 bg-background/35 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Safety</h3>
                <div className="mt-3">
                  <StatusList items={visualPilotSafetyRows} />
                </div>
              </article>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1fr_1fr_0.8fr]">
            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Pasos para el operador</h3>
              <ol className="mt-3 space-y-2">
                {visualPilotSteps.map((step) => (
                  <li key={`${step.order}-${step.check}`} className="grid grid-cols-[2rem_1fr] gap-2 border border-border/70 bg-background/40 p-3">
                    <span className="font-mono-ui text-xs text-warning">{step.order}</span>
                    <span>
                      <span className="block font-display text-xs uppercase tracking-[0.1em] text-foreground">{step.check}</span>
                      <span className="mt-1 block font-mono-ui text-[0.7rem] text-muted-foreground">{step.notes}</span>
                    </span>
                  </li>
                ))}
              </ol>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Limitaciones conocidas</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {visualPilotLimitations.map((limitation) => (
                  <Badge key={limitation} variant="outline">
                    {limitation}
                  </Badge>
                ))}
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Pilot findings</h3>
              <p className="mt-3 font-mono-ui text-xs text-muted-foreground">
                Findings reales registrados: {visualPilotFindings.length}
              </p>
              <p className="mt-2 font-mono-ui text-xs text-muted-foreground">
                No se declara que David haya abierto el navegador o probado manualmente el piloto.
              </p>
            </article>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-warning" />
              <CardTitle>Núcleo de Voz JARVIS</CardTitle>
            </div>
            <CardDescription>Voice Core visual + TTS state preview. Sin escucha, sin grabación y sin provider externo.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4 lg:grid-cols-[280px_1fr]">
              <div className="relative flex min-h-[280px] items-center justify-center overflow-hidden border border-warning/40 bg-background/40">
                <div className="absolute h-56 w-56 rounded-full border border-warning/15 animate-pulse" />
                <div className="absolute h-44 w-44 rounded-full border border-success/20" />
                <div className="absolute h-32 w-32 rounded-full border border-warning/35 animate-pulse" />
                <div className="relative flex h-28 w-28 items-center justify-center rounded-full border border-warning/80 bg-warning/10 shadow-[0_0_42px_rgba(255,189,56,0.18)]">
                  <MicOff className="h-10 w-10 text-warning" />
                </div>
                <div className="absolute bottom-4 left-4 right-4 border border-border/70 bg-background/70 px-3 py-2">
                  <p className="font-display text-[0.68rem] uppercase tracking-[0.14em] text-muted-foreground">estado actual</p>
                  <p className="mt-1 font-mono-ui text-sm text-warning">
                    {valueText(voiceCoreState.current_state, "preview")} / {valueText(voiceCoreState.mode, "preview")}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <StatusList items={voiceCoreRows} />
                <article className="border border-warning/40 bg-warning/10 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="warning">Subtítulos preview</Badge>
                    <Badge variant="success">sin TTS real</Badge>
                    <Badge variant="success">sin STT real</Badge>
                    <Badge variant="success">sin provider externo</Badge>
                  </div>
                  <p className="mt-3 font-mono-ui text-sm text-foreground">
                    {valueText(ttsState.preview_subtitle || ttsState.last_utterance, previewVoiceSubtitle)}
                  </p>
                  <p className="mt-2 font-display text-xs text-warning">
                    Subtítulos preview - sin TTS real, sin STT real, sin provider externo.
                  </p>
                </article>
              </div>
            </div>

            <article className="border border-border/70 bg-background/35 p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Estados visuales</h3>
                <Badge variant="warning">preview / disabled / future gated / not connected</Badge>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                {voiceVisualStates.map((item) => (
                  <div key={item.state} className="min-h-32 border border-border/70 bg-background/40 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="font-display text-sm">{valueText(item.label, item.state)}</p>
                        <p className="mt-1 font-mono-ui text-[0.68rem] text-muted-foreground">{item.state}</p>
                      </div>
                      <Badge variant={item.enabled === "preview" ? "warning" : item.enabled ? "success" : "outline"}>
                        {valueText(item.enabled)}
                      </Badge>
                    </div>
                    <p className="mt-2 font-mono-ui text-xs text-muted-foreground">{valueText(item.description)}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge variant="outline">{valueText(item.connection, "preview")}</Badge>
                      <Badge variant={item.sensor_required ? "destructive" : "success"}>
                        sensor: {yesNo(item.sensor_required, "required", "false")}
                      </Badge>
                      <Badge variant={item.can_approve ? "destructive" : "success"}>
                        approve: {yesNo(item.can_approve, "true", "false")}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <div className="grid gap-4 lg:grid-cols-2">
              <article className="border border-border/70 bg-background/35 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">TTS State</h3>
                <div className="mt-3">
                  <StatusList items={ttsRows} />
                </div>
              </article>

              <article className="border border-border/70 bg-background/35 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Política wake word</h3>
                <div className="mt-3">
                  <StatusList items={wakePolicyRows} />
                </div>
                <div className="mt-3 grid gap-2">
                  <SafetyLine>Frases soportadas futuras: Hola Jarvis, Jarvis.</SafetyLine>
                  <SafetyLine>La wake phrase nunca aprueba acciones.</SafetyLine>
                  <SafetyLine>La wake phrase no ejecuta acciones.</SafetyLine>
                  <SafetyLine>Las acciones críticas requieren readback y confirmación fuerte.</SafetyLine>
                </div>
              </article>
            </div>

            <article className="border border-warning/40 bg-warning/10 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-warning">
                  Wake Word Local Safe Flow
                </h3>
                <Badge variant="warning">typed preview / read-only</Badge>
              </div>

              <div className="mt-4 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
                <div className="space-y-4">
                  <StatusList items={wakeFlowStateRows} />
                  <div className="border border-border/70 bg-background/35 p-3">
                    <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">Frases soportadas</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {wakeSupportedPhrases.map((phrase) => (
                        <Badge key={phrase} variant="outline">
                          {phrase}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="border border-border/70 bg-background/35 p-3">
                    <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">Stop phrases</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {wakeStopPhrases.map((phrase) => (
                        <Badge key={phrase} variant="outline">
                          {phrase}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="grid gap-2 md:grid-cols-2">
                    {[
                      ["Mic hard-off", valueText(wakeModeExplanations.mic_hard_off, "Mic hard-off: no escucha nada.")],
                      [
                        "Wake-word-only",
                        valueText(
                          wakeModeExplanations.wake_word_only,
                          "Wake-word-only: futuro modo donde solo detectaría frase.",
                        ),
                      ],
                      [
                        "Command listening",
                        valueText(
                          wakeModeExplanations.command_listening,
                          "Command listening: futura ventana corta después de wake.",
                        ),
                      ],
                      ["Push-to-talk", valueText(wakeModeExplanations.push_to_talk, "Push-to-talk: futuro modo manual.")],
                      ["Typed preview", valueText(wakeModeExplanations.typed_preview, "Typed preview: modo actual seguro.")],
                    ].map(([label, text]) => (
                      <div key={label} className="border border-border/70 bg-background/35 p-3">
                        <p className="font-display text-xs uppercase tracking-[0.12em] text-warning">{label}</p>
                        <p className="mt-1 font-mono-ui text-xs text-muted-foreground">{text}</p>
                      </div>
                    ))}
                  </div>

                  <div className="grid gap-3 lg:grid-cols-2">
                    <div className="border border-border/70 bg-background/35 p-3">
                      <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">David</p>
                      <p className="mt-2 font-mono-ui text-sm text-foreground">
                        {valueText(wakeParsePreview.input_example, "Hola Jarvis, revisa el estado del proyecto")}
                      </p>
                    </div>
                    <div className="border border-border/70 bg-background/35 p-3">
                      <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">JARVIS preview</p>
                      <div className="mt-2">
                        <StatusList items={wakeParseRows} />
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-3 lg:grid-cols-2">
                    <div className="border border-border/70 bg-background/35 p-3">
                      <p className="font-display text-xs uppercase tracking-[0.12em] text-warning">Policy visible</p>
                      <div className="mt-3 grid gap-2">
                        <SafetyLine>La wake phrase nunca aprueba acciones.</SafetyLine>
                        <SafetyLine>La wake phrase no ejecuta acciones.</SafetyLine>
                        <SafetyLine>La wake phrase solo puede abrir una ventana de comando futura.</SafetyLine>
                        <SafetyLine>La aprobación por voz requiere canal autenticado, readback y auditoría.</SafetyLine>
                        <SafetyLine>Las acciones críticas requieren doble o triple confirmación.</SafetyLine>
                      </div>
                    </div>
                    <div className="border border-border/70 bg-background/35 p-3">
                      <p className="font-display text-xs uppercase tracking-[0.12em] text-warning">Approval policy</p>
                      <div className="mt-3">
                        <StatusList items={wakeApprovalRows} />
                      </div>
                    </div>
                  </div>

                  <div className="border border-success/40 bg-background/35 p-3">
                    <p className="font-display text-xs uppercase tracking-[0.12em] text-success">Safety banner</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge variant={wakeFlowSafety.no_microphone_activation ? "success" : "destructive"}>no micrófono</Badge>
                      <Badge variant={wakeFlowSafety.no_raw_audio_storage ? "success" : "destructive"}>no grabación</Badge>
                      <Badge variant={wakeFlowSafety.no_external_stt ? "success" : "destructive"}>no STT</Badge>
                      <Badge variant={wakeFlowSafety.no_external_tts ? "success" : "destructive"}>no TTS real</Badge>
                      <Badge variant={wakeFlowSafety.no_external_stt ? "success" : "destructive"}>no provider externo</Badge>
                      <Badge variant={wakeFlowSafety.no_background_listening ? "success" : "destructive"}>
                        no background listener
                      </Badge>
                      <Badge variant={wakeFlowSafety.no_hermes_dispatch ? "success" : "destructive"}>no Hermes dispatch</Badge>
                      <Badge variant={wakeFlowSafety.no_auto_execute ? "success" : "destructive"}>no auto execute</Badge>
                    </div>
                  </div>
                </div>
              </div>
            </article>

            <div className="grid gap-4 lg:grid-cols-3">
              <article className="border border-border/70 bg-background/35 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Privacidad voz</h3>
                <div className="mt-3">
                  <StatusList items={voicePrivacyRows} />
                </div>
                <div className="mt-3 grid gap-2">
                  <SafetyLine>micrófono: disabled</SafetyLine>
                  <SafetyLine>grabación: false</SafetyLine>
                  <SafetyLine>proveedor externo: none/not_connected</SafetyLine>
                </div>
              </article>

              <article className="border border-border/70 bg-background/35 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Approval Console / Hermes</h3>
                <div className="mt-3">
                  <StatusList items={voiceRelationshipRows} />
                </div>
                <div className="mt-3 grid gap-2">
                  <SafetyLine>La voz puede preparar una intención futura.</SafetyLine>
                  <SafetyLine>Si requiere aprobación, aparecerá en Approval Console.</SafetyLine>
                  <SafetyLine>Hermes solo ejecuta después de approval válido.</SafetyLine>
                  <SafetyLine>Frontend/voice no llama Hermes directamente.</SafetyLine>
                </div>
              </article>

              <article className="border border-destructive/40 bg-destructive/10 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-destructive">Kill Switch voz</h3>
                <div className="mt-3 grid gap-2">
                  <Badge variant={voiceSafety.kill_switch_visible ? "success" : "destructive"}>
                    kill switch visible: {yesNo(voiceSafety.kill_switch_visible)}
                  </Badge>
                  <Badge variant={voiceKillSwitch.real_audio_to_stop ? "destructive" : "success"}>
                    audio real que parar: {yesNo(voiceKillSwitch.real_audio_to_stop, "true", "false")}
                  </Badge>
                </div>
                <p className="mt-3 font-mono-ui text-xs text-destructive/80">
                  En esta PR no hay audio real que parar. Una integración futura deberá cortar escucha, TTS y ejecución gobernada.
                </p>
              </article>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Workflow className="h-5 w-5 text-success" />
              <CardTitle>Control de Misión</CardTitle>
            </div>
            <CardDescription>
              Escribe o dicta una orden para que JARVIS prepare una misión. En esta fase no se ejecuta nada.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <article className="border border-warning/40 bg-warning/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="warning">preview-only</Badge>
                <Badge variant={missionState.execution_enabled ? "destructive" : "success"}>
                  execution: {yesNo(missionState.execution_enabled, "enabled", "false")}
                </Badge>
                <Badge variant={missionState.hermes_dispatch_enabled ? "destructive" : "success"}>
                  Hermes dispatch: {yesNo(missionState.hermes_dispatch_enabled, "enabled", "false")}
                </Badge>
              </div>
              <p className="mt-3 font-display text-sm text-warning">
                Escribe o dicta una orden para que JARVIS prepare una misión.
              </p>
              <p className="mt-1 font-mono-ui text-xs text-warning">
                En esta fase no se ejecuta nada.
              </p>
            </article>

            <div className="space-y-3">
              <textarea
                disabled
                readOnly
                aria-label="Control de Misión preview input"
                placeholder={valueText(missionControl.sample_command, sampleMissionCommand)}
                className="min-h-28 w-full resize-none border border-border bg-background/50 p-3 font-mono-ui text-xs text-muted-foreground disabled:opacity-70"
              />
              <div className="grid gap-2 sm:grid-cols-2">
                <Button disabled aria-disabled="true" type="button" variant="outline">
                  Preparar preview
                </Button>
                <Button disabled aria-disabled="true" type="button" variant="outline">
                  Enviar a JARVIS
                </Button>
              </div>
            </div>

            <div className="grid gap-3 lg:grid-cols-2">
              <StatusList items={missionStateRows} />
              <StatusList items={supportedInputRows} />
            </div>

            <article className="border border-border/70 bg-background/35 p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Conversation Preview</h3>
                <Badge variant="warning">assistant: {valueText(missionConversation.assistant_status, "preview")}</Badge>
              </div>
              <p className="mb-3 font-display text-xs text-warning">
                Preview conversation — no provider call, no memory write, no execution.
              </p>
              <div className="grid gap-3">
                {missionMessages.map((message, index) => (
                  <div key={`${message.speaker}-${index}`} className="border border-border/70 bg-background/40 p-3">
                    <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">
                      {valueText(message.speaker)}
                    </p>
                    <p className="mt-1 font-mono-ui text-xs text-foreground">{valueText(message.content)}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3">
                <StatusList items={conversationPreviewRows} />
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Intent / Risk Preview</h3>
              <div className="mt-3">
                <StatusList items={missionIntentRows} />
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

            <article className="border border-warning/40 bg-warning/10 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-warning">Safety Banner</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {missionSafetyLabels.map(([label, key]) => (
                  <Badge key={key} variant={missionSafety[key] ? "success" : "outline"}>
                    {label}
                  </Badge>
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
              <div className="mt-3 grid gap-2">
                <p className="font-mono-ui text-xs text-muted-foreground">{valueText(missionGuidance.can_do)}</p>
                <p className="font-mono-ui text-xs text-muted-foreground">{valueText(missionGuidance.cannot_do_yet)}</p>
                <p className="font-mono-ui text-xs text-muted-foreground">{valueText(missionGuidance.future_next_step)}</p>
                <p className="font-mono-ui text-xs text-muted-foreground">{valueText(missionGuidance.sensitive_requires_approval)}</p>
              </div>
            </article>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-warning" />
              <CardTitle>Consola de Aprobación</CardTitle>
            </div>
            <CardDescription>Decisiones, riesgos y requisitos de approval; la consola no aprueba ni ejecuta en esta PR.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <article className="border border-warning/40 bg-warning/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="warning">preview/read-only</Badge>
                <Badge variant={approvals.action_buttons_enabled ? "destructive" : "success"}>
                  botones: {yesNo(approvals.action_buttons_enabled, "enabled", "disabled")}
                </Badge>
                <Badge variant={approvals.all_actions_read_only ? "success" : "destructive"}>
                  read-only: {yesNo(approvals.all_actions_read_only)}
                </Badge>
                <Badge variant={approvals.frontend_can_approve ? "destructive" : "success"}>
                  approve UI: {yesNo(approvals.frontend_can_approve, "allowed", "forbidden")}
                </Badge>
              </div>
              <p className="mt-3 font-display text-xs text-warning">
                Preview-only: approval execution is not wired in this PR.
              </p>
            </article>

            <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
              {[
                ["pending", valueText(approvals.pending_count)],
                ["critical", valueText(approvals.critical_count)],
                ["blocked", valueText(approvals.blocked_count)],
                ["expired", valueText(approvals.expired_count)],
                ["preview", valueText(approvals.preview_count)],
              ].map(([label, value]) => (
                <div key={label} className="border border-border/70 bg-background/40 p-3">
                  <p className="font-display text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
                  <p className="mt-1 font-mono-ui text-lg text-foreground">{value}</p>
                </div>
              ))}
            </div>

            <div className="grid gap-3 lg:grid-cols-2">
              <StatusList
                items={[
                  ["frontend puede aprobar", yesNo(approvals.frontend_can_approve, "sí", "no")],
                  ["frontend puede rechazar", yesNo(approvals.frontend_can_reject, "sí", "no")],
                  ["frontend modifica alcance", yesNo(approvals.frontend_can_modify_scope, "sí", "no")],
                  ["wake phrase aprueba", yesNo(approvals.wake_phrase_can_approve, "sí", "no")],
                ]}
              />
              <div className="grid gap-2">
                <SafetyLine>La wake phrase nunca aprueba acciones.</SafetyLine>
                <SafetyLine>La voz puede ser canal de aprobación solo si está autenticada, gateada y auditada.</SafetyLine>
                <SafetyLine>Las acciones sensibles requieren aprobación humana.</SafetyLine>
                <SafetyLine>Las acciones críticas requieren confirmación fuerte.</SafetyLine>
              </div>
            </div>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Readback / confirmación fuerte</h3>
              <p className="mt-2 font-mono-ui text-xs text-muted-foreground">
                Las acciones críticas requieren readback, confirmación fuerte, doble/triple confirmación,
                rollback/stop plan y auditoría. La UI muestra estos gates, pero no emite decisiones.
              </p>
            </article>

            <div className="space-y-3">
              {approvalCards.map((card) => (
                <ApprovalCardView key={card.id} card={card} />
              ))}
            </div>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Leyenda de riesgo</h3>
              <div className="mt-3 grid gap-2">
                {riskLegend.map(([level, text]) => (
                  <div key={level} className="flex items-start justify-between gap-4 border border-border/60 bg-background/30 px-3 py-2">
                    <span className="font-display text-xs uppercase tracking-[0.12em] text-warning">{level}</span>
                    <span className="text-right font-mono-ui text-xs text-foreground">{text}</span>
                  </div>
                ))}
              </div>
            </article>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TerminalSquare className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Ejecución Hermes</CardTitle>
            </div>
            <CardDescription>Hermes Execution visibility: read-only, gated y sin ejecución activa.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <article className="border border-warning/40 bg-warning/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="warning">read-only</Badge>
                <Badge variant="warning">gated</Badge>
                <Badge variant={hermesRuntime.active_execution === false ? "success" : "outline"}>no active execution</Badge>
              </div>
              <p className="mt-3 font-display text-sm text-warning">JARVIS gobierna. Hermes ejecuta.</p>
              <p className="mt-1 font-mono-ui text-xs text-warning">
                El frontend no puede ejecutar Hermes directamente.
              </p>
              <p className="mt-3 font-mono-ui text-xs text-foreground">
                Sin ejecución activa. No hay ejecución real que detener desde este panel.
              </p>
            </article>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">JARVIS</p>
                <p className="mt-1 font-mono-ui text-sm">{valueText(hermesContract.jarvis_role)}</p>
              </div>
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">Hermes</p>
                <p className="mt-1 font-mono-ui text-sm">{valueText(hermesContract.hermes_role, "execution_engine")}</p>
              </div>
            </div>

            <StatusList
              items={hermesCurrentRows}
            />

            <div className="grid gap-2 sm:grid-cols-3">
              <Badge variant={hermesContract.no_duplicate_hermes_runtime ? "success" : "destructive"}>
                no duplicate runtime: {yesNo(hermesContract.no_duplicate_hermes_runtime)}
              </Badge>
              <Badge variant={hermes.frontend_can_execute ? "destructive" : "success"}>
                frontend ejecuta: {yesNo(hermes.frontend_can_execute, "sí", "no")}
              </Badge>
              <Badge variant={hermes.frontend_can_call_hermes_execute ? "destructive" : "success"}>
                Hermes directo: {yesNo(hermes.frontend_can_call_hermes_execute, "sí", "no")}
              </Badge>
            </div>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Capacidades gobernadas</h3>
              <div className="mt-3 grid gap-3">
                {hermesCapabilities.map((capability) => (
                  <div key={capability.name} className="border border-border/70 bg-background/40 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="font-display text-sm">{capability.name}</p>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant={statusVariant(valueText(capability.status))}>{valueText(capability.status)}</Badge>
                        <Badge variant={capability.approval_required ? "warning" : "outline"}>
                          approval: {valueText(capability.approval_level)}
                        </Badge>
                        <Badge variant={capability.can_execute_from_frontend ? "destructive" : "success"}>
                          frontend: {yesNo(capability.can_execute_from_frontend, "ejecuta", "no ejecuta")}
                        </Badge>
                      </div>
                    </div>
                    <p className="mt-2 font-mono-ui text-xs text-muted-foreground">{valueText(capability.notes)}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-destructive/40 bg-destructive/10 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-destructive">Rutas bloqueadas</h3>
              <div className="mt-3 grid gap-2">
                {hermesBlockedRoutes.map((blocked) => (
                  <div key={`${blocked.route_or_action}-${blocked.action}`} className="border border-destructive/30 bg-background/35 px-3 py-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-mono-ui text-xs text-foreground">{valueText(blocked.route_or_action)}</span>
                      <Badge variant="destructive">blocked</Badge>
                    </div>
                    <p className="mt-1 font-mono-ui text-xs text-muted-foreground">{valueText(blocked.notes)}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Requisitos antes de ejecución futura</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {futureExecutionRequirements.map((requirement) => (
                  <Badge key={requirement} variant="warning">
                    {requirement}
                  </Badge>
                ))}
              </div>
            </article>

            <SafetyLine>Hermes ejecuta solo bajo gates válidos.</SafetyLine>
            <SafetyLine>El Kill Switch permanece visible; en esta fase no hay ejecución Hermes activa que parar.</SafetyLine>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Radar className="h-5 w-5 text-success" />
            <CardTitle>Agent / Module Radar</CardTitle>
          </div>
          <CardDescription>Estados normalizados desde el read model; campos ausentes se muestran como unknown.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {modules.map((module) => (
              <div key={module.name} className="flex min-h-24 flex-col justify-between gap-3 border border-border/70 bg-background/35 px-3 py-3">
                <div className="flex items-start justify-between gap-3">
                  <span className="font-display text-sm">{module.name}</span>
                  <Badge variant={statusVariant(valueText(module.status))}>
                    {valueText(module.status)}
                  </Badge>
                </div>
                <p className="line-clamp-2 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(module.notes)}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr_0.85fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Camera className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Cámara / Visión</CardTitle>
            </div>
            <CardDescription>
              <span className="font-display text-warning">preview-only</span> · La cámara no graba por defecto. La visión solo se activa con permiso explícito.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <article className="border border-warning/40 bg-warning/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="warning">preview-only</Badge>
                <Badge variant={cameraVisionState.camera_enabled ? "destructive" : "success"}>
                  cámara: {cameraVisionState.camera_enabled ? "enabled" : "off/disabled"}
                </Badge>
                <Badge variant={cameraVisionState.external_vision_provider_called ? "destructive" : "success"}>
                  provider externo: {cameraVisionState.external_vision_provider_called ? "called" : "none/not_connected"}
                </Badge>
              </div>
              <p className="mt-3 font-display text-sm text-warning">La cámara no graba por defecto.</p>
              <p className="mt-1 font-mono-ui text-xs text-warning">La visión solo se activa con permiso explícito.</p>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Estado actual</h3>
              <div className="mt-3">
                <StatusList items={cameraCurrentRows} />
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Privacidad</h3>
              <div className="mt-3">
                <StatusList items={cameraPrivacyRows} />
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Estados visuales</h3>
                <Badge variant="warning">preview / disabled / future gated</Badge>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {cameraVisionStates.map((item) => (
                  <div key={item.state} className="min-h-32 border border-border/70 bg-background/40 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="font-display text-sm">{valueText(item.label, item.state)}</p>
                        <p className="mt-1 font-mono-ui text-[0.68rem] text-muted-foreground">{item.state}</p>
                      </div>
                      <Badge variant={item.enabled === "future_gated" ? "warning" : item.enabled === "preview" ? "outline" : "success"}>
                        {valueText(item.enabled)}
                      </Badge>
                    </div>
                    <p className="mt-2 font-mono-ui text-xs text-muted-foreground">{valueText(item.description)}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge variant="outline">risk: {valueText(item.risk)}</Badge>
                      <Badge variant={item.can_execute ? "destructive" : "success"}>
                        execute: {yesNo(item.can_execute, "true", "false")}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Scope policy</h3>
              <div className="mt-3">
                <StatusList items={cameraScopeRows} />
              </div>
            </article>

            <div className="grid gap-2">
              <SafetyLine>La cámara no graba por defecto.</SafetyLine>
              <SafetyLine>No se captura imagen ni vídeo en esta PR.</SafetyLine>
              <SafetyLine>No se usa getUserMedia.</SafetyLine>
              <SafetyLine>No hay proveedor externo de visión.</SafetyLine>
              <SafetyLine>La visión futura requerirá permiso explícito y auditoría.</SafetyLine>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Smartphone className="h-5 w-5 text-success" />
              <CardTitle>Mobile Companion</CardTitle>
            </div>
            <CardDescription>
              <span className="font-display text-warning">preview-only</span> · Mobile es una interfaz, no un runtime. Mobile no llama a Hermes directamente.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <article className="border border-warning/40 bg-warning/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="warning">preview-only</Badge>
                <Badge variant={mobileCompanionState.mobile_runtime_enabled ? "destructive" : "success"}>
                  runtime: {yesNo(mobileCompanionState.mobile_runtime_enabled, "enabled", "disabled")}
                </Badge>
                <Badge variant={mobileCompanionState.mobile_can_call_hermes_directly ? "destructive" : "success"}>
                  Hermes directo: {yesNo(mobileCompanionState.mobile_can_call_hermes_directly, "allowed", "forbidden")}
                </Badge>
              </div>
              <p className="mt-3 font-display text-sm text-warning">Mobile es una interfaz, no un runtime.</p>
              <p className="mt-1 font-mono-ui text-xs text-warning">Mobile no llama a Hermes directamente.</p>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Estado actual</h3>
              <div className="mt-3">
                <StatusList items={mobileRows} />
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">PWA policy</h3>
              <div className="mt-3">
                <StatusList items={pwaRows} />
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Vistas futuras</h3>
                <Badge variant="warning">no execute / no Hermes direct</Badge>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {mobileCompanionViews.map((view) => (
                  <div key={view.id ?? view.name} className="min-h-32 border border-border/70 bg-background/40 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="font-display text-sm">{valueText(view.name)}</p>
                      <Badge variant={statusVariant(valueText(view.status))}>{valueText(view.status)}</Badge>
                    </div>
                    <p className="mt-2 font-mono-ui text-xs text-muted-foreground">{valueText(view.notes)}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge variant={view.can_execute ? "destructive" : "success"}>
                        no execute: {yesNo(!view.can_execute, "true", "false")}
                      </Badge>
                      <Badge variant={view.can_call_hermes ? "destructive" : "success"}>
                        no Hermes direct: {yesNo(!view.can_call_hermes, "true", "false")}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Safety</h3>
              <div className="mt-3">
                <StatusList items={mobileSafetyRows} />
              </div>
            </article>

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
              <CircleDollarSign className="h-5 w-5 text-warning" />
              <CardTitle>Finance / ROI</CardTitle>
            </div>
            <CardDescription>Métricas financieras solo con evidencia.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <article className="border border-warning/40 bg-warning/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="warning">read-only</Badge>
                <Badge variant={financeSafety.no_money_movement ? "success" : "destructive"}>
                  dinero: {financeSafety.no_money_movement ? "bloqueado" : "allowed"}
                </Badge>
                <Badge variant={financeSafety.no_stripe_live ? "success" : "destructive"}>
                  Stripe live: {financeSafety.no_stripe_live ? "bloqueado" : "allowed"}
                </Badge>
              </div>
              <p className="mt-3 font-display text-sm text-warning">No fake metrics.</p>
              <p className="mt-1 font-mono-ui text-xs text-warning">Si no hay evidencia, mostrar unknown.</p>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Métricas</h3>
              <div className="mt-3">
                <StatusList items={financeRows} />
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Budget</h3>
              <div className="mt-3">
                <StatusList items={financeBudgetRows} />
              </div>
            </article>

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
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-success" />
              <CardTitle>Product Builder Adaptativo</CardTitle>
            </div>
            <CardDescription>Flujo visual de producto; sin deploy, Stripe ni revenue real.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <article className="border border-warning/40 bg-warning/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="warning">preview/read-only</Badge>
                <Badge variant={productBuilderState.product_generation_enabled ? "destructive" : "success"}>
                  product generation: {yesNo(productBuilderState.product_generation_enabled, "enabled", "false")}
                </Badge>
                <Badge variant={productBuilderState.deploy_enabled ? "destructive" : "success"}>
                  deploy: {yesNo(productBuilderState.deploy_enabled, "enabled", "false")}
                </Badge>
                <Badge variant={productBuilderState.stripe_enabled ? "destructive" : "success"}>
                  Stripe: {yesNo(productBuilderState.stripe_enabled, "enabled", "false")}
                </Badge>
              </div>
              <p className="mt-3 font-display text-sm text-warning">No es un Template Builder.</p>
              <p className="mt-1 font-mono-ui text-xs text-warning">
                Si dos productos parecen clones, el builder ha fallado.
              </p>
            </article>

            <div className="grid gap-3 lg:grid-cols-[0.75fr_1.25fr]">
              <article className="border border-border/70 bg-background/35 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Estado</h3>
                <div className="mt-3">
                  <StatusList items={productBuilderStateRows} />
                </div>
              </article>

              <article className="border border-border/70 bg-background/35 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Diferenciación</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Badge variant={productDifferentiation.no_template_clone ? "success" : "destructive"}>
                    no template clone
                  </Badge>
                  <Badge variant={productDifferentiation.adaptive_builder_not_template_builder ? "success" : "destructive"}>
                    adaptive builder
                  </Badge>
                  <Badge variant={productDifferentiation.each_product_needs_reason_to_exist ? "success" : "destructive"}>
                    razón de existir
                  </Badge>
                  <Badge variant={productDifferentiation.each_product_needs_success_metric ? "success" : "destructive"}>
                    success metric
                  </Badge>
                  <Badge variant={productDifferentiation.each_product_needs_monetization_logic ? "success" : "destructive"}>
                    monetización
                  </Badge>
                  <Badge variant={productDifferentiation.cloned_products_are_failure ? "success" : "destructive"}>
                    clones son fallo
                  </Badge>
                </div>
                <div className="mt-3 grid gap-2">
                  <SafetyLine>No es un Template Builder.</SafetyLine>
                  <SafetyLine>Si dos productos parecen clones, el builder ha fallado.</SafetyLine>
                  <SafetyLine>Cada producto necesita razón de existir, métrica y monetización.</SafetyLine>
                </div>
              </article>
            </div>

            <article className="border border-border/70 bg-background/35 p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Stages</h3>
                <Badge variant="warning">preview / future-gated / disabled</Badge>
              </div>
              <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
                {productBuilderStages.map((stage) => {
                  const stageStatus = valueText(stage.status).replace("_", "-");
                  return (
                    <div key={stage.name} className="min-h-36 border border-border/70 bg-background/35 p-3">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <p className="font-display text-xs uppercase tracking-[0.1em]">{stage.name}</p>
                        <Badge variant={statusVariant(valueText(stage.status))}>{stageStatus}</Badge>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <Badge variant={stage.can_execute ? "destructive" : "success"}>
                          execute: {yesNo(stage.can_execute, "true", "false")}
                        </Badge>
                        <Badge variant={stage.requires_approval ? "warning" : "outline"}>
                          approval: {valueText(stage.approval_level)}
                        </Badge>
                      </div>
                      <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">
                        evidencia: {valueText(stage.evidence_required)}
                      </p>
                      <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(stage.notes)}</p>
                    </div>
                  );
                })}
              </div>
            </article>

            <div className="grid gap-3 lg:grid-cols-2">
              <article className="border border-border/70 bg-background/35 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Monetización</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Badge variant={productMonetization.pricing_preview_only ? "success" : "destructive"}>pricing preview</Badge>
                  <Badge variant={productMonetization.stripe_live_requires_strong_approval ? "warning" : "destructive"}>
                    Stripe strong approval
                  </Badge>
                  <Badge variant={productMonetization.checkout_requires_strong_approval ? "warning" : "destructive"}>
                    checkout strong approval
                  </Badge>
                  <Badge variant={productMonetization.real_revenue_requires_confirmation ? "warning" : "destructive"}>
                    revenue confirmation
                  </Badge>
                  <Badge variant={productMonetization.no_fake_revenue ? "success" : "destructive"}>no fake revenue</Badge>
                </div>
              </article>

              <article className="border border-border/70 bg-background/35 p-4">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Safety</h3>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Badge variant={productBuilderSafety.no_deploy ? "success" : "destructive"}>no deploy</Badge>
                  <Badge variant={productBuilderSafety.no_publish ? "success" : "destructive"}>no publish</Badge>
                  <Badge variant={productBuilderSafety.no_money_movement ? "success" : "destructive"}>no money</Badge>
                  <Badge variant={productBuilderSafety.no_external_network ? "success" : "destructive"}>no external network</Badge>
                  <Badge variant={productBuilderSafety.no_hermes_dispatch ? "success" : "destructive"}>no Hermes dispatch</Badge>
                </div>
              </article>
            </div>

            <div className="grid gap-2 lg:grid-cols-3">
              <SafetyLine>Deploy real requiere aprobación fuerte.</SafetyLine>
              <SafetyLine>Stripe/checkout real requiere aprobación fuerte.</SafetyLine>
              <SafetyLine>Revenue real requiere confirmación.</SafetyLine>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Frontend Pilot / Hardening</CardTitle>
            </div>
            <CardDescription>Pilot read-only para `/jarvis`; El dashboard mira, no toca.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <article className="border border-warning/40 bg-warning/10 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="warning">Pilot read-only</Badge>
                <Badge variant={frontendPilotState.frontend_can_execute ? "destructive" : "success"}>No execute.</Badge>
                <Badge variant={frontendPilotState.frontend_can_activate_sensors ? "destructive" : "success"}>No sensores.</Badge>
                <Badge variant={frontendPilotState.frontend_can_move_money ? "destructive" : "success"}>no money</Badge>
              </div>
              <p className="mt-3 font-display text-sm text-warning">El dashboard mira, no toca.</p>
              <p className="mt-1 font-mono-ui text-xs text-warning">No POST/PUT/DELETE.</p>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Ruta / endpoint</h3>
              <div className="mt-3">
                <StatusList items={frontendPilotRows} />
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Readiness checks</h3>
                <Badge variant="warning">visible modules + safety</Badge>
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                {frontendReadinessChecks.map((check) => (
                  <div key={check.name} className="border border-border/70 bg-background/40 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <p className="font-mono-ui text-xs text-foreground">{check.name}</p>
                      <Badge variant={check.status === "passed" ? "success" : statusVariant(check.status)}>
                        {valueText(check.status)}
                      </Badge>
                    </div>
                    <p className="mt-2 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(check.evidence)}</p>
                    <p className="mt-1 font-mono-ui text-[0.7rem] text-muted-foreground">{valueText(check.notes)}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Hardening notes</h3>
              <div className="mt-3">
                <StatusList items={frontendHardeningRows} />
              </div>
              <p className="mt-3 font-mono-ui text-xs text-warning">
                Dependency hardening queda para una PR separada.
              </p>
            </article>

            <article className="border border-border/70 bg-background/35 p-4">
              <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Pilot limitations</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {frontendLimitations.map((limitation) => (
                  <Badge key={limitation} variant="outline">
                    {limitation}
                  </Badge>
                ))}
              </div>
            </article>

            <div className="grid gap-2">
              <SafetyLine>Pilot read-only</SafetyLine>
              <SafetyLine>El dashboard mira, no toca.</SafetyLine>
              <SafetyLine>No POST/PUT/DELETE.</SafetyLine>
              <SafetyLine>No execute.</SafetyLine>
              <SafetyLine>No sensores.</SafetyLine>
              <SafetyLine>No fake metrics.</SafetyLine>
              <SafetyLine>Dependency hardening queda para una PR separada.</SafetyLine>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Live Timeline / Audit Preview</CardTitle>
            </div>
            <CardDescription>Eventos reales de lectura del backend; no eventos de ejecución.</CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-3">
              {timeline.map((event) => (
                <li key={`${event.source}-${event.event}`} className="grid grid-cols-[20px_1fr] gap-3">
                  <Square className="mt-0.5 h-3 w-3 text-warning" />
                  <span className="font-mono-ui text-xs text-foreground">
                    {valueText(event.event)} · {valueText(event.status)} · {valueText(event.source)}
                  </span>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Lock className="h-5 w-5 text-warning" />
            <CardTitle>Separación JARVIS / Hermes</CardTitle>
          </div>
          <CardDescription>Contrato visible de esta shell local.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
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
            <p className="font-mono-ui text-sm">Esta pantalla no llama a Hermes, no aprueba y no ejecuta.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
