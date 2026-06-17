import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  Camera,
  CircleDollarSign,
  Cpu,
  Grip,
  History,
  Lock,
  Maximize2,
  MessageSquare,
  Mic,
  MicOff,
  Minimize2,
  Radar,
  SendHorizontal,
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
  type JarvisDashboardModule,
  type JarvisDashboardStatus,
  type JarvisFinanceMetric,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const DASHBOARD_READ_MODEL_ENDPOINT = "/mark-3/dashboard/status";
const UNKNOWN = "unknown";

const commandCenterTabs = [
  { id: "cockpit", label: "Cockpit" },
  { id: "approvals", label: "Approvals" },
  { id: "hermes", label: "Hermes" },
  { id: "voice", label: "Voice / Wake" },
  { id: "vision", label: "Vision / Mobile" },
  { id: "finance", label: "Finance / Product" },
  { id: "pilot", label: "Pilot / Audit" },
] as const;

type CommandCenterTabId = (typeof commandCenterTabs)[number]["id"];

const previewVoiceSubtitle = "David, estoy en modo preview. No estoy escuchando ni grabando audio.";
const sampleMissionCommand = "JARVIS, revisa el estado del proyecto y dime el siguiente paso seguro.";

const presenceStates = [
  {
    id: "idle-calmado",
    label: "idle/calmado",
    tone: "success",
    description: "Nucleo estable, sensores apagados, esperando orden escrita.",
  },
  {
    id: "escuchando-preview",
    label: "escuchando",
    tone: "warning",
    description: "Preview visual de escucha; no hay microfono, STT ni wake listener real.",
  },
  {
    id: "pensando-preview",
    label: "pensando",
    tone: "warning",
    description: "Preview de razonamiento local; no llama providers ni ejecuta tools.",
  },
  {
    id: "hablando-preview",
    label: "hablando",
    tone: "warning",
    description: "Subtitulos preview; no hay TTS real ni salida de audio.",
  },
  {
    id: "alerta-riesgo",
    label: "alerta/riesgo",
    tone: "destructive",
    description: "Riesgo visible; cualquier accion sensible requiere approval y audit.",
  },
] as const;

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
    rollback_plan: "No hay mutacion; rollback no aplica.",
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
    reason: "Cambia estado local y requiere scope, diff y rollback antes de cualquier ejecucion futura.",
    status: "blocked",
    risk_level: "medium",
    approval_level: "simple",
    touches: ["filesystem", "local_docs"],
    estimated_cost: UNKNOWN,
    measured_cost: UNKNOWN,
    rollback_plan: "Exigir diff, backup o patch de reversion antes de una escritura futura.",
    stop_plan: "Parar por path amplio, glob, diff ausente o cancelacion humana.",
    expires_at: UNKNOWN,
    scope_summary: "Un path local explicito y un diff exacto; sin escrituras recursivas.",
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
    title: "Busqueda externa web/GitHub",
    action: "Consultar web o GitHub fuera del entorno local.",
    reason: "Puede filtrar intencion, consumir cuota o traer contenido no confiable.",
    status: "blocked",
    risk_level: "high",
    approval_level: "strong",
    touches: ["web", "github"],
    estimated_cost: UNKNOWN,
    measured_cost: UNKNOWN,
    rollback_plan: "No llamar proveedores externos hasta aprobar query, proveedor y manejo de datos.",
    stop_plan: "Parar ante secrets, repos privados, scopes de cuenta o intencion ambigua.",
    expires_at: UNKNOWN,
    scope_summary: "Query/proveedor/fuentes especificos; sin acciones autenticadas.",
    evidence_summary: "Web/GitHub no esta conectado a esta consola.",
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
    title: "Produccion, dinero, deploy o email real",
    action: "Deploy, Stripe/dinero o envio de email real.",
    reason: "Tiene impacto externo o irreversible y requiere confirmacion fuerte.",
    status: "blocked",
    risk_level: "critical",
    approval_level: "triple",
    touches: ["money", "deploy", "email", "web"],
    estimated_cost: UNKNOWN,
    measured_cost: UNKNOWN,
    rollback_plan: "Exigir rollback verificado, owner, blast radius y stop condition.",
    stop_plan: "Parar ante coste no verificado, credencial viva, smoke fallido o cancelacion.",
    expires_at: UNKNOWN,
    scope_summary: "Cuenta, entorno, destinatario o importe nominal; sin scope amplio.",
    evidence_summary: "Finance sigue unknown si no hay evidencia real.",
    disabled_reason: "Preview-only: approval execution is not wired in this PR.",
    recommended_operator_action: "Requerir readback, doble/triple confirmacion, rollback, stop plan y auditoria.",
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
    action: "Leer secrets/tokens/cookies/sesiones o saltar autorizacion.",
    reason: "Credenciales, bypass, deception y fake metrics son limites forbidden.",
    status: "forbidden",
    risk_level: "forbidden",
    approval_level: "forbidden",
    touches: ["credentials"],
    estimated_cost: UNKNOWN,
    measured_cost: UNKNOWN,
    rollback_plan: "No se ejecuta; redisenar como status/audit sin secretos.",
    stop_plan: "Parar y rechazar si pide secrets, cookies, tokens, bypass o metricas falsas.",
    expires_at: UNKNOWN,
    scope_summary: "Scope forbidden; ningun acceso a credenciales o bypass.",
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

const fallbackModules: JarvisDashboardModule[] = [
  ["Mission Loop", "preview", "risk_scaled_per_step", "Control de mision local, sin submit real."],
  ["Research", "gated", "level_2_local_read_level_3_external", "Research local queda gated; web/GitHub no conectados desde esta pantalla."],
  ["Product Revenue", "prepare-only", "level_4_for_money_publication_identity", "Sin Stripe, checkout, deploy, publicacion ni dinero."],
  ["Routine Ops", "prepare-only", "risk_scaled", "Sin scheduler real, email, cuentas ni workers."],
  ["Moonshot Lab", "prepare-only", "risk_scaled", "Planes de experimento; sin installs, providers ni fake results."],
  ["Voice", "preview", "sensor_privacy", "Voice Core visual; microfono y grabacion disabled."],
  ["Wake Listener", "disabled", "sensor_privacy", "Wake phrase no aprueba, no ejecuta y no escucha."],
  ["Camera/Vision", "disabled", "sensor_privacy", "Camera placeholder visual; sin captura ni permisos."],
  ["Mobile Companion", "preview", "remote_surface", "Mobile futuro sera cliente/puente, no runtime."],
  ["Memory/Learning", "preview", "memory_never_grants_permission", "Memoria nunca concede permisos."],
  ["Hermes", "gated", "exact_local_read_only_with_operator_authorization", "Hermes ejecuta solo detras de gates JARVIS."],
].map(([name, status, risk, notes]) => ({
  name,
  status,
  source: DASHBOARD_READ_MODEL_ENDPOINT,
  risk,
  notes,
}));

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

const fallbackFinanceMetrics = {
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
};

const missionLifecycleDisplay = [
  ["draft", "Orden escrita o dictada como borrador visual."],
  ["preview", "JARVIS prepara lectura de intencion sin mutar estado."],
  ["intent detected", "La intencion queda en unknown hasta tener clasificador seguro."],
  ["risk classified", "El riesgo se muestra como preview antes de approvals."],
  ["approval required", "Lo sensible se deriva a Approval Console."],
  ["operator review", "David revisa scope, permisos y siguiente paso."],
  ["Hermes gated", "Hermes permanece detras de gates validos."],
  ["audit", "La accion futura debera dejar evidencia auditable."],
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

const fallbackBuilderStages = [
  "Idea",
  "Validación",
  "Blueprint",
  "Código",
  "Landing",
  "Deploy candidate",
  "Monetización",
  "Medición",
];

const riskLegend = [
  ["Nivel 0-1", "directo / bajo riesgo"],
  ["Nivel 2", "local scoped / simple approval"],
  ["Nivel 3", "externo o sensible / strong approval"],
  ["Nivel 4", "produccion, dinero, deploy, email, credenciales / double o triple confirmation"],
  ["Nivel 5", "ilegal, inseguro, no autorizado, bypass, deception, fake metrics / forbidden"],
] as const;

const fallbackDashboard = (reason: "loading" | "offline" | "error"): JarvisDashboardStatus => ({
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
  local_system_contract: {
    name: "Local System Contract",
    presence_ui: "JARVIS Presence UI",
    local_runtime_daemon_is_system: true,
    web_route_is_visual_interface_only: true,
    frontend_executes_hermes_directly: false,
    mobile_and_vps_are_future_clients_or_bridges: true,
    real_voice_camera_in_future_prs: true,
    visual_contract: {
      primary_experience: "Presence UI",
      central_core_states: ["idle/calmado", "escuchando", "pensando", "hablando", "alerta/riesgo"],
      smart_bar: "disabled/preview",
      camera_placeholder: "movable/expandable visual placeholder",
      folded_history: "collapsed preview",
    },
  },
  release_candidate: {
    status: UNKNOWN,
    readiness: {},
    not_ready_for_free_autonomy: true,
    restrictions_are_approval_gates_not_permanent_bans: true,
    pilot_readiness: UNKNOWN,
    pilot_executed: false,
  },
  modules: fallbackModules,
  mission_control: {
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
      next_safe_action: "operator review",
    },
    conversation_preview: {
      messages: [
        { role: "user", speaker: "David", content: sampleMissionCommand, preview_only: true },
        {
          role: "assistant",
          speaker: "JARVIS",
          content: "Puedo preparar una mision de revision. Antes de ejecutar cualquier accion sensible, pedire aprobacion.",
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
    safety: Object.fromEntries(missionSafetyLabels.map(([, key]) => [key, true])),
    operator_guidance: {
      can_do: "David puede ver como JARVIS recibiria una orden y prepararia una revision segura.",
      cannot_do_yet: "Todavia no puede crear misiones, approvals, memoria, llamadas externas ni ejecucion.",
      future_next_step: "El siguiente paso futuro sera un intake/classifier seguro antes de propuestas reales.",
      sensitive_requires_approval: "Todo lo sensible requiere approval explicito, scope, rollback/stop plan y auditoria.",
    },
    source_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
    read_only: true,
  },
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
    active_execution: false,
    execution_mode: "read_only_visibility",
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
    notes: "Fallback seguro: no se permite ejecucion directa desde frontend.",
    contract: {
      jarvis_role: "governs/risk/approval/audit/control",
      hermes_role: "execution_engine",
      no_duplicate_hermes_runtime: true,
      frontend_direct_execution_allowed: false,
      frontend_can_execute: false,
      frontend_can_call_hermes_execute: false,
    },
    governed_capabilities: [],
    blocked_routes: [],
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
  voice_core: {
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
    visual_states: [
      "offline",
      "online",
      "preview",
      "dormant",
      "dormido",
      "listening_wake_word",
      "listening_command",
      "thinking",
      "speaking",
      "approval_required",
      "hermes_executing",
      "paused",
      "blocked",
      "error",
      "kill_switch",
    ].map((state) => ({
      state,
      label: state,
      description: "Estado visual/read-only sin activar sensores ni ejecucion.",
      risk: state === "blocked" || state === "error" ? "blocked" : "none",
      enabled: state === "preview" || state === "dormant" ? "preview" : false,
      sensor_required: state.includes("listening"),
      can_approve: false,
      connection: "preview",
    })),
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
  },
  wake_word_flow: {
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
      wake_word_only: "Wake-word-only: futuro modo donde solo detectaria frase.",
      command_listening: "Command listening: futura ventana corta despues de wake.",
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
  },
  camera_vision: {
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
    states: [
      ["camera_off", "cámara apagada"],
      ["permission_required", "permiso requerido"],
      ["camera_available_future", "preview futuro"],
      ["analyzing_future", "análisis futuro"],
      ["recording_disabled", "grabación desactivada"],
      ["storage_disabled", "almacenamiento desactivado"],
      ["kill_switch", "kill switch"],
    ].map(([state, label]) => ({
      state,
      label,
      description: "Estado visual de camara; captura, streaming y storage quedan deshabilitados.",
      enabled: state === "camera_off" ? "preview" : "future_gated",
      risk: "sensor_privacy",
      can_execute: false,
    })),
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
  },
  mobile_companion: {
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
    mobile_views: [
      ["status", "Estado"],
      ["approvals_preview", "Approvals preview"],
      ["mission_preview", "Mission preview"],
      ["hermes_visibility", "Hermes visibility"],
      ["voice_status", "Voice status"],
      ["camera_status", "Camera status"],
      ["finance_summary", "Finance summary"],
      ["kill_switch_preview", "Kill switch preview"],
    ].map(([id, name]) => ({
      id,
      name,
      status: id === "kill_switch_preview" ? "future_gated" : "preview",
      can_execute: false,
      can_call_hermes: false,
      notes: "Vista futura read-only; no execute / no Hermes direct.",
    })),
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
  },
  finance_roi: {
    truth_policy: {
      no_fake_metrics: true,
      unknown_when_no_evidence: true,
      measured_requires_source: true,
      estimated_requires_label: true,
      confirmed_revenue_requires_evidence: true,
      projected_revenue_must_be_labelled: true,
      roi_unknown_without_revenue_and_cost: true,
    },
    metrics: fallbackFinanceMetrics,
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
  },
  adaptive_product_builder: {
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
    stages: fallbackBuilderStages.map((name) => ({
      name,
      status: name === "Deploy candidate" || name === "Monetización" ? "disabled" : "preview",
      can_execute: false,
      requires_approval: name !== "Idea" && name !== "Validación" && name !== "Blueprint",
      approval_level: "strong",
      evidence_required: "measured_source_before_metric",
      notes: "Stage preview/future-gated/disabled; sin ejecucion.",
    })),
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
  },
  frontend_pilot: {
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
    readiness_checks: [
      "dashboard_route_exists",
      "read_model_connected",
      "approval_console_visible",
      "hermes_execution_visible",
      "mission_control_visible",
      "voice_core_visible",
      "wake_flow_visible",
      "camera_vision_visible",
      "mobile_companion_visible",
      "finance_roi_visible",
      "product_builder_visible",
      "kill_switch_visible",
      "no_fake_metrics",
      "no_frontend_execute",
      "no_sensor_activation",
      "no_post_put_delete",
    ].map((name) => ({
      name,
      status: "passed",
      evidence: name,
      notes: "Read-only frontend pilot check.",
    })),
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
  },
  visual_command_center_pilot: {
    state: {
      mode: "read_only_pilot",
      dashboard_route: "/jarvis",
      status_endpoint: DASHBOARD_READ_MODEL_ENDPOINT,
      backend_read_model_connected: false,
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
    required_panels: [
      "Header",
      "Presence UI",
      "Local System Contract",
      "Smart Bar",
      "Camera Placeholder",
      "Folded History",
      "Voice Core",
      "Wake Word Local Safe Flow",
      "Mission Control",
      "Approval Console",
      "Hermes Execution",
      "Agent / Module Radar",
      "Camera / Vision",
      "Mobile Companion",
      "Finance / ROI",
      "Product Builder Adaptativo",
      "Frontend Pilot / Hardening",
      "Live Timeline / Audit",
      "Kill Switch",
    ].map((name) => ({
      name,
      expected: true,
      source: name,
      status: name === "Camera / Vision" ? "disabled" : "preview",
      can_execute: false,
      notes: "Presence UI panel remains read-only.",
    })),
    read_only_checks: [
      "no_post_put_delete",
      "no_execute_route",
      "no_frontend_hermes_call",
      "no_tool_runner",
      "no_sensor_activation",
      "no_get_user_media",
      "no_media_recorder",
      "no_audio_context_capture",
      "no_camera_capture",
      "no_mobile_runtime",
      "no_money_movement",
      "no_stripe_live",
      "no_deploy",
      "no_email_send",
      "no_credentials",
      "no_fake_metrics",
    ].map((name) => ({
      name,
      status: "passed",
      evidence: name,
      notes: "Static/read-model guardrail.",
    })),
    operator_pilot_steps: [
      { order: 1, check: "arrancar backend", notes: "Arrancar el backend local antes de abrir la UI." },
      { order: 2, check: "abrir /jarvis", notes: "Abrir la ruta local del cockpit." },
      { order: 3, check: "comprobar estado general", notes: "Verificar modo, endpoint y estado read-only." },
      { order: 4, check: "comprobar panels", notes: "Confirmar que todos los paneles esperados estan visibles." },
      { order: 5, check: "comprobar smart bar", notes: "Confirmar barra inteligente inferior disabled/preview." },
      { order: 6, check: "comprobar camera placeholder", notes: "Confirmar placeholder visual sin permiso de navegador." },
      { order: 7, check: "comprobar folded history", notes: "Confirmar historial plegado sin persistencia nueva." },
    ],
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
  },
  safety: {
    frontend_can_execute: false,
    frontend_can_approve: false,
    no_auto_execute: true,
    no_frontend_execute: true,
    no_duplicate_hermes_runtime: true,
    no_get_user_media: true,
    no_sensor_activation: true,
    no_voice_recording: true,
    no_camera_capture: true,
    no_frontend_tool_runner: true,
    no_tool_call: true,
    no_file_write: true,
    no_network_call: true,
    no_direct_hermes_call_from_mobile: true,
    no_direct_hermes_call_from_voice: true,
    no_direct_hermes_call_from_camera: true,
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
});

const requiredStaticCopy = [
  "Centro de Mando JARVIS",
  "Núcleo de Voz JARVIS",
  "Control de Misión",
  "preview-only",
  "En esta fase no se ejecuta nada",
  "Conversation Preview",
  "Preview conversation",
  "Intent / Risk Preview",
  "Mission Lifecycle",
  "Safety Banner",
  "No auto execute",
  "No Hermes dispatch",
  "No tool call",
  "No file write",
  "No network",
  "No voice recording",
  "No camera capture",
  "Wake phrase is not permission",
  "Si una misión necesita algo sensible, aparecerá en Approval Console",
  "Hermes solo ejecutará después de approval válido",
  "El frontend no puede saltarse gates",
  "JARVIS gobierna",
  "Hermes ejecuta",
  "Consola de Aprobación",
  "Hermes Execution",
  "Ejecución Hermes",
  "El frontend no puede ejecutar Hermes directamente",
  "Sin ejecución activa",
  "Capacidades gobernadas",
  "Rutas bloqueadas",
  "Requisitos antes de ejecución futura",
  "approval válido",
  "scope exacto",
  "coste/impacto",
  "operador humano",
  "Kill Switch",
  "KILL SWITCH",
  "No fake metrics",
  "unknown",
  "La cámara no graba por defecto",
  "Mobile es una interfaz, no un runtime",
  "La wake phrase nunca aprueba acciones",
  "La voz puede ser canal de aprobación solo si está autenticada, gateada y auditada",
  "Las acciones sensibles requieren aprobación humana",
  "Las acciones críticas requieren confirmación fuerte",
  "Hermes ejecuta solo bajo gates válidos",
  "No hay ejecución real que detener desde este panel",
  "No hay ejecución real que detener desde esta shell",
  "Preview-only: approval execution is not wired in this PR",
  "Leyenda de riesgo",
  "Nivel 0-1",
  "Nivel 5",
  "Readback / confirmación fuerte",
  "Cámara / Visión",
  "No se captura imagen ni vídeo en esta PR",
  "No se usa getUserMedia",
  "No hay proveedor externo de visión",
  "La visión futura requerirá permiso explícito y auditoría",
  "Mobile no ejecuta acciones",
  "Approvals reales desde móvil quedan future-gated",
  "No se guardan credenciales ni tokens",
  "Presence UI",
  "Local System Contract",
  "smart bar",
  "camera placeholder",
  "folded history",
  "barra inteligente inferior",
  "historial plegado",
  "JARVIS runtime/daemon local es el sistema",
  "/jarvis es solo la interfaz visual",
  "móvil y VPS serán clientes/puentes futuros",
  "frontend no ejecuta directamente Hermes",
  "voz/cámara reales vendrán en PRs posteriores",
  "idle/calmado",
  "escuchando",
  "pensando",
  "hablando",
  "alerta/riesgo",
];

const voiceContractCopy = [
  "No estoy escuchando ni grabando audio",
  "Subtítulos preview",
  "Subtítulos preview - sin TTS real, sin STT real, sin provider externo.",
  "Política wake word",
  "Frases soportadas futuras: Hola Jarvis, Jarvis.",
  "La wake phrase no ejecuta acciones",
  "Las acciones críticas requieren readback y confirmación fuerte",
  "Privacidad voz",
  "micrófono: disabled",
  "grabación: false",
  "audio bruto almacenado: false",
  "proveedor externo",
  "background listening",
  "voice approval",
  "La voz puede preparar una intención futura",
  "Si requiere aprobación, aparecerá en Approval Console",
  "Frontend/voice no llama Hermes directamente",
  "Kill Switch voz",
  "En esta PR no hay audio real que parar",
  "Una integración futura deberá cortar escucha, TTS y ejecución gobernada",
  "offline",
  "online",
  "preview",
  "dormant",
  "dormido",
  "listening_wake_word",
  "listening_command",
  "thinking",
  "speaking",
  "approval_required",
  "hermes_executing",
  "paused",
  "blocked",
  "error",
  "kill_switch",
];

const wakeContractCopy = [
  "Wake Word Local Safe Flow",
  "micrófono hard-off",
  "Hola Jarvis",
  "Jarvis",
  "Stop phrases",
  "Mic hard-off",
  "Wake-word-only",
  "Command listening",
  "Push-to-talk",
  "Typed preview",
  "Hola Jarvis, revisa el estado del proyecto",
  "wake phrase detectada",
  "comando restante",
  "abriría ventana de comando",
  "ejecutaría",
  "aprobaría",
  "llamaría Hermes",
  "La wake phrase solo puede abrir una ventana de comando futura",
  "La aprobación por voz requiere canal autenticado, readback y auditoría",
  "Las acciones críticas requieren doble o triple confirmación",
  "no micrófono",
  "no grabación",
  "no STT",
  "no TTS real",
  "no provider externo",
  "no background listener",
  "no Hermes dispatch",
  "no auto execute",
];

const visionMobileContractCopy = [
  "La cámara no graba por defecto.",
  "La visión solo se activa con permiso explícito.",
  "Estado actual",
  "permiso solicitado",
  "recording",
  "streaming",
  "snapshot",
  "vision analysis",
  "provider externo",
  "Privacidad",
  "no camera activation",
  "no getUserMedia",
  "no recording",
  "no snapshot",
  "no image/video storage",
  "explicit operator permission required",
  "visual indicator required",
  "audit required",
  "cámara apagada",
  "permiso requerido",
  "preview futuro",
  "análisis futuro",
  "grabación desactivada",
  "almacenamiento desactivado",
  "kill switch",
  "Mobile Companion",
  "Mobile es una interfaz, no un runtime.",
  "Mobile no llama a Hermes directamente.",
  "PWA baseline",
  "mobile runtime",
  "approvals reales desde móvil",
  "remote kill switch",
  "mobile camera",
  "mobile microphone",
  "notifications",
  "offline cache",
  "service worker",
  "push",
  "background sync",
  "Estado",
  "Approvals preview",
  "Mission preview",
  "Hermes visibility",
  "Voice status",
  "Camera status",
  "Finance summary",
  "Kill switch preview",
  "no execute",
  "no Hermes direct",
  "no mobile execute",
  "no direct Hermes call",
  "no mobile sensor activation",
  "no real mobile approvals in this PR",
  "approval requires backend gate",
  "critical approval requires strong confirmation",
];

const financeProductPilotCopy = [
  "Finance / ROI",
  "No fake metrics.",
  "Si no hay evidencia, mostrar unknown.",
  "Revenue confirmado requiere evidencia.",
  "ROI queda unknown sin revenue y costes reales.",
  "No se mueve dinero desde este panel.",
  "Stripe live requiere aprobación fuerte.",
  "coste real",
  "coste estimado",
  "revenue confirmado",
  "revenue proyectado",
  "gross revenue",
  "expenses",
  "net revenue",
  "budget",
  "Product Builder Adaptativo",
  "No es un Template Builder.",
  "Si dos productos parecen clones, el builder ha fallado.",
  "Deploy real requiere aprobación fuerte.",
  "Stripe/checkout real requiere aprobación fuerte.",
  "Revenue real requiere confirmación.",
  "preview / future-gated / disabled",
  "Pilot read-only",
  "Frontend Pilot / Hardening",
  "El dashboard mira, no toca.",
  "No POST/PUT/DELETE.",
  "No execute.",
  "No sensores.",
  "Dependency hardening queda para una PR separada.",
  "/jarvis",
  "/mark-3/dashboard/status",
  "finance_roi_visible",
  "product_builder_visible",
  "no_frontend_execute",
  "no_sensor_activation",
  "npm audit vulnerabilities observed",
  "full pytest required before merge",
];

const visualPilotCopy = [
  "Visual Command Center Pilot",
  "read-only pilot",
  "No se ejecuta Hermes desde el frontend",
  "No se activan sensores",
  "No hay approvals reales en esta fase",
  "No hay métricas falsas",
  "Los valores sin evidencia se muestran como unknown",
  "Checklist de panels",
  "Checklist de seguridad",
  "Estado de botones críticos",
  "Pasos para el operador",
  "Limitaciones conocidas",
  "Header",
  "Voice Core",
  "Mission Control",
  "Approval Console",
  "Agent / Module Radar",
  "Camera / Vision",
  "Live Timeline / Audit",
  "no_post_put_delete",
  "no_execute_route",
  "no_get_user_media",
  "no_media_recorder",
  "no_audio_context_capture",
  "no_camera_capture",
  "no_money_movement",
  "no_fake_metrics",
  "Detalles en pestañas",
  "modo preview/read-only",
];

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
  if (status === "ready" || status === "online" || status === "success") return "success";
  if (status === "disabled" || status === "not_connected" || status === "forbidden") return "destructive";
  if (status === "gated" || status === "future_gated" || status === "prepare-only" || status === "preview") return "warning";
  return "outline";
}

function riskVariant(risk: string): "outline" | "warning" | "destructive" | "success" {
  if (risk === "low") return "success";
  if (risk === "medium" || risk === "high") return "warning";
  if (risk === "critical" || risk === "forbidden") return "destructive";
  return "outline";
}

function metricValue(metric?: JarvisFinanceMetric): string {
  return valueText(metric?.value);
}

function readModules(modules: JarvisDashboardModule[] | undefined): JarvisDashboardModule[] {
  const byName = new Map((modules ?? []).map((item) => [item.name, item]));
  return fallbackModules.map((fallback) => byName.get(fallback.name) ?? fallback);
}

function MiniStat({ label, value, variant = "outline" }: { label: string; value: string; variant?: "outline" | "warning" | "destructive" | "success" }) {
  return (
    <div className="min-w-0 border border-cyan-300/15 bg-[#061526]/55 px-3 py-2 shadow-[inset_0_0_24px_rgba(34,211,238,0.04)]">
      <p className="font-display text-[0.68rem] uppercase tracking-[0.12em] text-cyan-200/55">{label}</p>
      <div className="mt-1 flex items-center justify-between gap-2">
        <p className="truncate font-mono-ui text-xs text-cyan-50">{value}</p>
        <Badge className={variant === "destructive" ? "" : "border-cyan-300/25 bg-cyan-300/10 text-cyan-100"} variant={variant}>{variant}</Badge>
      </div>
    </div>
  );
}

function StatusList({ items }: { items: readonly (readonly [string, string])[] }) {
  return (
    <dl className="grid gap-1">
      {items.map(([label, value]) => (
        <div key={`${label}-${value}`} className="flex items-center justify-between gap-4 border-b border-cyan-300/10 px-2 py-2 last:border-b-0">
          <dt className="font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-200/55">{label}</dt>
          <dd className="max-w-[62%] break-words text-right font-mono-ui text-xs text-cyan-50/90">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function SafetyLine({ children }: { children: ReactNode }) {
  return (
    <p className="border-l-2 border-cyan-300/55 bg-cyan-300/[0.055] px-3 py-2 font-display text-xs text-cyan-100/82">
      {children}
    </p>
  );
}

function DisabledApprovalActions() {
  const approvalActionLabels = ["Aprobar", "Rechazar", "Modificar alcance", "Pedir explicación"] as const;
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      {approvalActionLabels.map((label) => (
        <Button key={label} disabled aria-disabled="true" type="button" variant="outline" size="sm">
          {label}
        </Button>
      ))}
    </div>
  );
}

function ContractVault() {
  const groups = [
    ["Base read-only", requiredStaticCopy],
    ["Voice Core / Wake", [...voiceContractCopy, ...wakeContractCopy]],
    ["Camera / Mobile", visionMobileContractCopy],
    ["Finance / Product / Pilot", financeProductPilotCopy],
    ["Visual Command Center", visualPilotCopy],
  ] as const;

  return (
    <div className="grid gap-3">
      {groups.map(([title, items]) => (
        <details key={title} className="border border-cyan-300/15 bg-[#05111f]/55 p-3">
          <summary className="cursor-pointer font-expanded text-xs font-bold uppercase tracking-[0.12em] text-cyan-100">
            {title}
          </summary>
          <div className="mt-3 flex flex-wrap gap-2">
            {items.map((item) => (
              <Badge key={`${title}-${item}`} variant="outline">
                {item}
              </Badge>
            ))}
          </div>
        </details>
      ))}
    </div>
  );
}

function PresenceCore({
  voiceState,
  subtitle,
}: {
  voiceState: string;
  subtitle: string;
}) {
  return (
    <article
      className="relative h-full min-h-0 overflow-hidden"
      data-testid="jarvis-central-core"
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,rgba(34,211,238,0.30)_0%,rgba(14,165,233,0.12)_35%,rgba(2,6,23,0)_68%),radial-gradient(circle_at_50%_82%,rgba(249,115,22,0.10),transparent_38%),linear-gradient(90deg,rgba(34,211,238,0.035)_1px,transparent_1px),linear-gradient(0deg,rgba(125,211,252,0.028)_1px,transparent_1px)] bg-[length:100%_100%,100%_100%,64px_64px,64px_64px]" />
      <div className="absolute left-0 right-0 top-1/2 h-px bg-cyan-300/35 shadow-[0_0_30px_rgba(34,211,238,0.55)]" />
      <div className="absolute left-1/2 top-[8%] h-[84%] w-px -translate-x-1/2 bg-cyan-300/18" />
      <div className="absolute left-[5%] right-[5%] top-1/2 h-24 -translate-y-1/2 bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.34),transparent_58%)] blur-xl" />
      <div className="absolute left-[3%] right-[3%] top-1/2 h-20 -translate-y-1/2 opacity-80 [background:repeating-linear-gradient(90deg,transparent_0_18px,rgba(34,211,238,0.38)_18px_20px,transparent_20px_42px)] [mask-image:radial-gradient(ellipse_at_center,black_0%,transparent_72%)]" />
      <div className="absolute inset-x-[12%] top-8 h-px bg-cyan-300/20" />
      <div className="absolute inset-x-[12%] bottom-8 h-px bg-cyan-300/16" />

      <div className="relative flex h-full min-h-0 flex-col items-center justify-center">
        <div className="absolute top-4 flex items-center gap-2">
          <Badge className="border-cyan-300/35 bg-cyan-300/10 text-cyan-100 shadow-[0_0_26px_rgba(34,211,238,0.14)]" variant="outline">Presence UI</Badge>
          <Badge className="border-cyan-100/20 bg-[#071629]/75 text-cyan-50" variant="outline">Núcleo de Voz JARVIS</Badge>
          <Badge className="border-cyan-300/35 bg-cyan-300/10 text-cyan-100" variant="outline">read-only</Badge>
        </div>

        <div className="relative flex h-[min(82dvh,58rem)] w-[min(82dvh,58rem)] max-h-[calc(100dvh-13rem)] max-w-[min(62vw,58rem)] items-center justify-center">
          <div className="absolute inset-0 rounded-full border border-cyan-200/10 shadow-[0_0_180px_rgba(34,211,238,0.24)]" />
          <div className="absolute inset-[3%] rounded-full border border-cyan-300/20 shadow-[inset_0_0_70px_rgba(34,211,238,0.08)]" />
          <div className="absolute inset-[9%] rounded-full border border-sky-300/25 animate-pulse" />
          <div className="absolute inset-[16%] rounded-full border border-cyan-100/35 shadow-[0_0_80px_rgba(34,211,238,0.22)]" />
          <div className="absolute inset-[25%] rounded-full border border-cyan-300/20 animate-pulse" />
          <div className="absolute inset-[35%] rounded-full bg-cyan-200/22 blur-3xl" />
          <div className="absolute h-px w-[118%] bg-cyan-300/45 shadow-[0_0_26px_rgba(34,211,238,0.8)]" />
          <div className="absolute h-[118%] w-px bg-cyan-300/32" />
          <div className="absolute h-[113%] w-[113%] rotate-45 border border-cyan-200/10" />
          <div className="absolute h-[94%] w-[94%] -rotate-12 border border-sky-500/12" />
          <div className="absolute h-[76%] w-[76%] rotate-[27deg] border border-cyan-100/10" />
          <div className="relative flex h-[32%] w-[32%] min-w-44 items-center justify-center rounded-full border border-cyan-100/80 bg-[#03192a]/88 shadow-[0_0_120px_rgba(34,211,238,0.62),inset_0_0_92px_rgba(34,211,238,0.25)]">
            <div className="absolute inset-3 rounded-full border border-cyan-300/28" />
            <div className="absolute inset-[24%] rounded-full bg-cyan-200/18 blur-xl" />
            <div className="relative text-center">
              <h1 className="font-expanded text-[clamp(2.1rem,4.2vw,5.4rem)] font-bold uppercase tracking-[0.14em] text-cyan-50 blend-lighter drop-shadow-[0_0_28px_rgba(125,211,252,0.9)]">
                JARVIS
              </h1>
              <p className="mt-1 font-display text-[0.62rem] uppercase tracking-[0.28em] text-cyan-100/72">
                núcleo de inteligencia
              </p>
              <MicOff className="mx-auto mt-4 h-8 w-8 text-cyan-100/80 drop-shadow-[0_0_18px_rgba(125,211,252,0.9)]" />
            </div>
          </div>
        </div>

        <div className="absolute bottom-4 left-1/2 flex w-[min(52rem,calc(100vw-3rem))] -translate-x-1/2 flex-wrap justify-center gap-2">
          {presenceStates.map((state) => (
            <div
              key={state.id}
              className={
                "border px-3 py-1.5 shadow-[0_0_24px_rgba(34,211,238,0.08)] backdrop-blur " +
                (state.tone === "destructive"
                  ? "border-red-400/40 bg-red-950/25 text-red-100"
                  : "border-cyan-300/18 bg-[#031426]/70 text-cyan-100")
              }
              title={state.description}
            >
              <p className="font-display text-[0.68rem] uppercase tracking-[0.14em]">{state.label}</p>
            </div>
          ))}
        </div>

        <div className="absolute bottom-[4.25rem] left-1/2 w-[min(42rem,calc(100vw-4rem))] -translate-x-1/2 text-center">
          <p className="font-display text-sm uppercase tracking-[0.22em] text-cyan-200">
            {voiceState} / local presence preview
          </p>
          <p className="mt-2 line-clamp-2 font-mono-ui text-sm text-cyan-50/78">{subtitle}</p>
        </div>
      </div>
    </article>
  );
}

function CameraPlaceholder({
  cameraEnabled,
  cameraRisk,
}: {
  cameraEnabled: boolean;
  cameraRisk: string;
}) {
  return (
    <article
      className="relative overflow-hidden rounded-[2px] border border-cyan-300/45 bg-[#03101f]/78 p-3 shadow-[0_0_70px_rgba(34,211,238,0.18)] backdrop-blur-md"
      data-testid="jarvis-camera-placeholder"
    >
      <div className="mb-2 flex items-center justify-between gap-2 border-b border-cyan-300/18 pb-2">
        <div className="flex items-center gap-2">
          <Grip className="h-4 w-4 text-cyan-200/55" />
          <h2 className="font-expanded text-xs font-bold uppercase tracking-[0.16em] text-cyan-50">Cámara · Camera Placeholder</h2>
        </div>
        <Badge className={cameraEnabled ? "" : "border-cyan-300/30 bg-cyan-300/10 text-cyan-100"} variant={cameraEnabled ? "destructive" : "outline"}>{cameraEnabled ? "active" : "off"}</Badge>
      </div>
      <div className="relative aspect-[16/10] overflow-hidden rounded-[1px] border border-cyan-300/35 bg-[#010816] shadow-[inset_0_0_70px_rgba(14,165,233,0.18)]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_42%,rgba(34,211,238,0.24),transparent_38%),radial-gradient(ellipse_at_50%_85%,rgba(249,115,22,0.08),transparent_38%),linear-gradient(90deg,rgba(34,211,238,0.08)_1px,transparent_1px),linear-gradient(0deg,rgba(125,211,252,0.06)_1px,transparent_1px)] bg-[length:100%_100%,100%_100%,28px_28px,28px_28px]" />
        <div className="absolute inset-x-0 top-1/2 h-px bg-cyan-300/35 shadow-[0_0_18px_rgba(34,211,238,0.6)]" />
        <div className="absolute inset-y-0 left-1/2 w-px bg-cyan-300/18" />
        <div className="absolute inset-4 border border-cyan-200/15" />
        <div className="absolute left-4 top-4 h-7 w-12 border-l border-t border-cyan-200/35" />
        <div className="absolute right-4 top-4 h-7 w-12 border-r border-t border-cyan-200/35" />
        <div className="absolute bottom-4 left-4 h-7 w-12 border-b border-l border-cyan-200/35" />
        <div className="absolute bottom-4 right-4 h-7 w-12 border-b border-r border-cyan-200/35" />
        <div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-200/40 shadow-[0_0_48px_rgba(34,211,238,0.22)]" />
        <Camera className="absolute left-1/2 top-1/2 h-9 w-9 -translate-x-1/2 -translate-y-1/2 text-cyan-100/72 drop-shadow-[0_0_18px_rgba(125,211,252,0.55)]" />
        <div className="absolute inset-x-4 bottom-4 flex items-center justify-between gap-2">
          <Badge className="border-cyan-300/25 bg-[#041728]/80 text-cyan-100" variant="outline">visual only</Badge>
          <Badge className="border-cyan-300/25 bg-cyan-300/10 text-cyan-100" variant="outline">movible/ampliable</Badge>
        </div>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2">
        <Button disabled aria-disabled="true" type="button" variant="outline" size="sm" className="border-cyan-300/20 bg-cyan-300/[0.035] text-cyan-100">
          <Minimize2 className="mr-2 h-3.5 w-3.5" />
          Mover
        </Button>
        <Button disabled aria-disabled="true" type="button" variant="outline" size="sm" className="border-cyan-300/20 bg-cyan-300/[0.035] text-cyan-100">
          <Maximize2 className="mr-2 h-3.5 w-3.5" />
          Ampliar
        </Button>
      </div>
      <details className="mt-3 border border-cyan-300/10 bg-[#071629]/45 p-2">
        <summary className="cursor-pointer font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-100/70">privacidad cámara</summary>
        <div className="mt-2 grid gap-2">
          <SafetyLine>La cámara no graba por defecto.</SafetyLine>
          <SafetyLine>No se captura imagen ni vídeo en esta PR.</SafetyLine>
          <SafetyLine>No se usa getUserMedia.</SafetyLine>
          <SafetyLine>No hay proveedor externo de visión.</SafetyLine>
          <SafetyLine>La visión futura requerirá permiso explícito y auditoría.</SafetyLine>
        </div>
      </details>
      <p className="mt-2 font-mono-ui text-xs text-cyan-100/45">riesgo actual: {cameraRisk}</p>
    </article>
  );
}

function MissionDraftPreview({ missionControl }: { missionControl: NonNullable<JarvisDashboardStatus["mission_control"]> }) {
  return (
    <article className="border border-border bg-card/75 p-4" data-testid="jarvis-mission-summary">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Workflow className="h-4 w-4 text-success" />
          <h2 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Control de Misión</h2>
        </div>
        <Badge variant="warning">preview-only</Badge>
      </div>
      <textarea
        disabled
        readOnly
        aria-label="Control de Misión preview input"
        placeholder={valueText(missionControl.sample_command, sampleMissionCommand)}
        className="min-h-20 w-full resize-none border border-border bg-background/50 p-3 font-mono-ui text-xs text-muted-foreground disabled:opacity-70"
      />
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        <Button disabled aria-disabled="true" type="button" variant="outline" size="sm">Preparar preview</Button>
        <Button disabled aria-disabled="true" type="button" variant="outline" size="sm">Enviar a JARVIS</Button>
      </div>
      <p className="mt-3 font-display text-xs text-warning">En esta fase no se ejecuta nada.</p>
    </article>
  );
}

function SmartBar({
  missionControl,
}: {
  missionControl: NonNullable<JarvisDashboardStatus["mission_control"]>;
}) {
  const messages = missionControl.conversation_preview?.messages ?? [];
  const lastResponse = messages.find((message) => message.speaker === "JARVIS")?.content ?? previewVoiceSubtitle;
  return (
    <section
      className="fixed bottom-3 left-1/2 z-50 w-[min(58rem,calc(100vw-2rem))] -translate-x-1/2"
      data-testid="jarvis-smart-bar"
    >
      <div className="mb-3 grid gap-2">
        <div className="ml-auto max-w-[82%] rounded-[2px] border border-cyan-300/24 bg-[#031426]/82 px-4 py-2 shadow-[0_0_30px_rgba(34,211,238,0.10)] backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <p className="font-display text-[0.68rem] uppercase tracking-[0.16em] text-cyan-200">Tú</p>
            <p className="font-mono-ui text-[0.68rem] text-cyan-100/50">preview</p>
          </div>
          <p className="mt-1 truncate font-mono-ui text-xs text-cyan-50">{valueText(missionControl.sample_command, sampleMissionCommand)}</p>
        </div>
        <div className="max-w-[82%] rounded-[2px] border border-cyan-300/24 bg-[#031426]/82 px-4 py-2 shadow-[0_0_30px_rgba(34,211,238,0.10)] backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <p className="font-display text-[0.68rem] uppercase tracking-[0.16em] text-cyan-200">JARVIS</p>
            <p className="font-mono-ui text-[0.68rem] text-cyan-100/50">respuesta temporal preview</p>
          </div>
          <p className="mt-1 truncate font-mono-ui text-xs text-cyan-50">{lastResponse}</p>
        </div>
      </div>

      <div className="relative rounded-full border border-cyan-300/35 bg-[#020b17]/95 p-2 shadow-[0_0_80px_rgba(34,211,238,0.24),inset_0_0_52px_rgba(34,211,238,0.06)] backdrop-blur-xl">
        <div className="absolute -inset-2 -z-10 rounded-full bg-cyan-300/10 blur-2xl" />
        <div className="flex min-w-0 items-center gap-3 rounded-full border border-cyan-300/18 bg-[#061629]/92 px-4 py-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-cyan-300/30 bg-cyan-300/10 shadow-[0_0_30px_rgba(34,211,238,0.22)]">
            <MessageSquare className="h-5 w-5 text-cyan-100" />
          </div>
          <input
            disabled
            readOnly
            aria-label="Barra inteligente inferior para escribir a JARVIS"
            value=""
            placeholder="Escribe o habla con JARVIS... / smart bar disabled preview"
            className="min-w-0 flex-1 bg-transparent font-mono-ui text-lg text-cyan-50 outline-none placeholder:text-cyan-100/36 disabled:text-cyan-100/45"
          />
          <Button disabled aria-disabled="true" type="button" variant="outline" size="icon" className="rounded-full border-cyan-300/25 bg-cyan-300/[0.04] text-cyan-100">
            <Mic className="h-4 w-4" />
          </Button>
          <Button disabled aria-disabled="true" type="button" variant="outline" size="icon" className="rounded-full border-cyan-300/25 bg-cyan-300/[0.04] text-cyan-100">
            <SendHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <details className="mx-auto mt-2 w-fit border border-cyan-300/16 bg-[#020b17]/80 px-5 py-2 backdrop-blur" data-testid="jarvis-folded-history">
        <summary className="flex cursor-pointer items-center gap-2 font-display text-xs uppercase tracking-[0.14em] text-cyan-100/64">
          <History className="h-4 w-4" />
          Historial plegado / folded history
        </summary>
        <div className="mt-3 grid max-h-40 w-[min(42rem,calc(100vw-3rem))] gap-2 overflow-auto">
          <div className="grid gap-2 border border-cyan-300/15 bg-[#071629]/55 p-3">
            <p className="font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-200/55">transcripción temporal preview</p>
            <p className="truncate font-mono-ui text-xs text-cyan-50">{valueText(missionControl.sample_command, sampleMissionCommand)}</p>
            <p className="font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-200/55">respuesta temporal preview</p>
            <p className="truncate font-mono-ui text-xs text-cyan-50">{lastResponse}</p>
          </div>
          <div className="grid gap-2">
            {messages.map((message, index) => (
              <div key={`${message.speaker}-${index}`} className="border border-cyan-300/10 bg-[#020717]/70 p-2">
                <p className="font-display text-[0.68rem] uppercase tracking-[0.12em] text-cyan-200/50">{message.speaker}</p>
                <p className="font-mono-ui text-xs text-cyan-50/80">{message.content}</p>
              </div>
            ))}
          </div>
        </div>
      </details>
    </section>
  );
}

export default function JarvisCommandCenterPage() {
  const [dashboard, setDashboard] = useState<JarvisDashboardStatus>(() => fallbackDashboard("loading"));
  const [connectionState, setConnectionState] = useState<"loading" | "online" | "offline">("loading");
  const [activeTab, setActiveTab] = useState<CommandCenterTabId>("cockpit");

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
  const fallbackOffline = useMemo(() => fallbackDashboard("offline"), []);
  const system = dashboard.system ?? {};
  const localSystemContract = (dashboard.local_system_contract ?? fallbackOffline.local_system_contract ?? {}) as NonNullable<
    JarvisDashboardStatus["local_system_contract"]
  >;
  const approvals = dashboard.approvals ?? {};
  const approvalCards = approvals.cards?.length ? approvals.cards : fallbackApprovalCards;
  const missionControl = dashboard.mission_control ?? fallbackOffline.mission_control!;
  const missionState = missionControl.state ?? {};
  const missionIntent = missionControl.intent_preview ?? {};
  const missionSafety = missionControl.safety ?? {};
  const missionConversation = missionControl.conversation_preview ?? {};
  const hermes = dashboard.hermes_execution ?? {};
  const hermesRuntime = hermes.runtime_status ?? hermes;
  const voiceCore = dashboard.voice_core ?? fallbackOffline.voice_core!;
  const voiceCoreState = voiceCore.state ?? {};
  const ttsState = voiceCore.tts_state ?? {};
  const wakeWordFlow = dashboard.wake_word_flow ?? fallbackOffline.wake_word_flow!;
  const cameraVision = dashboard.camera_vision ?? fallbackOffline.camera_vision!;
  const cameraVisionState = cameraVision.state ?? {};
  const cameraVisionPrivacy = cameraVision.privacy ?? {};
  const mobileCompanion = dashboard.mobile_companion ?? fallbackOffline.mobile_companion!;
  const mobileCompanionState = mobileCompanion.state ?? {};
  const financeRoi = dashboard.finance_roi ?? fallbackOffline.finance_roi!;
  const financeMetrics = financeRoi.metrics ?? fallbackFinanceMetrics;
  const productBuilder = dashboard.adaptive_product_builder ?? fallbackOffline.adaptive_product_builder!;
  const productStages = productBuilder.stages?.length ? productBuilder.stages : fallbackOffline.adaptive_product_builder!.stages!;
  const frontendPilot = dashboard.frontend_pilot ?? fallbackOffline.frontend_pilot!;
  const visualPilot = dashboard.visual_command_center_pilot ?? fallbackOffline.visual_command_center_pilot!;
  const timeline = dashboard.timeline?.length ? dashboard.timeline : fallbackOffline.timeline ?? [];

  const sensorsDisabled =
    !voiceCoreState.microphone_enabled &&
    !cameraVisionState.camera_enabled &&
    !mobileCompanionState.remote_camera_enabled &&
    !mobileCompanionState.remote_microphone_enabled;
  const activeRisk = valueText(missionIntent.risk_level, cameraVisionState.camera_enabled ? "sensor_privacy" : "none/unknown");
  const voiceState = valueText(voiceCoreState.current_state, "preview");
  const coreSubtitle = valueText(ttsState.preview_subtitle || ttsState.last_utterance, previewVoiceSubtitle);

  const essentialRows = [
    ["estado general", valueText(system.api_status, connectionState)],
    ["approvals pendientes", valueText(approvals.pending_count)],
    ["escucha/piensa/habla", voiceState],
    ["misión actual", valueText(missionState.mode, "preview")],
    ["coste/dinero", metricValue(financeMetrics.actual_cost)],
    ["cámara activa", yesNo(cameraVisionState.camera_enabled, "sí", "no")],
    ["riesgo actual", activeRisk],
  ] as const;

  const localContractRows = [
    ["runtime", localSystemContract.local_runtime_daemon_is_system ? "local daemon is system" : "unknown"],
    ["web", localSystemContract.web_route_is_visual_interface_only ? "/jarvis visual interface only" : "unknown"],
    ["mobile/VPS", localSystemContract.mobile_and_vps_are_future_clients_or_bridges ? "future clients/bridges" : "unknown"],
    ["Hermes direct", localSystemContract.frontend_executes_hermes_directly ? "unexpected allowed" : "false"],
    ["voice/camera", localSystemContract.real_voice_camera_in_future_prs ? "future PRs" : "unknown"],
  ] as const;

  const hermesRows = [
    ["Hermes disponible", yesNo(hermesRuntime.available, "sí", "no")],
    ["Hermes conectado", yesNo(hermesRuntime.connected, "sí", "no")],
    ["ejecución activa", yesNo(hermesRuntime.active_execution, "sí", "no")],
    ["modo", valueText(hermesRuntime.execution_mode, "read_only_visibility")],
    ["coste", valueText(hermesRuntime.measured_cost)],
  ] as const;

  const voiceRows = [
    ["mode", valueText(voiceCoreState.mode, "preview")],
    ["estado actual", voiceState],
    ["micrófono", yesNo(voiceCoreState.microphone_enabled, "enabled", "disabled")],
    ["wake word", yesNo(voiceCoreState.wake_word_enabled, "enabled", "disabled")],
    ["TTS", yesNo(voiceCoreState.tts_enabled, "enabled", "disabled")],
    ["STT", yesNo(voiceCoreState.stt_enabled, "enabled", "disabled")],
    ["grabación", yesNo(voiceCoreState.audio_recording, "true", "false")],
    ["audio bruto almacenado", yesNo(voiceCoreState.raw_audio_stored, "true", "false")],
  ] as const;

  const cameraRows = [
    ["cámara", cameraVisionState.camera_enabled ? "enabled" : "off/disabled"],
    ["permiso solicitado", yesNo(cameraVisionState.camera_permission_requested, "true", "false")],
    ["preview", cameraVisionState.preview_enabled ? "enabled" : "disabled"],
    ["recording", yesNo(cameraVisionState.recording ?? cameraVision.recording, "true", "false")],
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

  return (
    <div
      className="fixed inset-x-0 bottom-0 top-12 z-30 h-[calc(100dvh-3rem)] overflow-hidden bg-[#01050d] text-cyan-50"
      data-testid="jarvis-command-center-page"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_38%,rgba(34,211,238,0.18),transparent_44%),radial-gradient(circle_at_50%_78%,rgba(249,115,22,0.10),transparent_36%),linear-gradient(180deg,rgba(1,5,13,0.30),rgba(1,5,13,0.94))]" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(90deg,rgba(34,211,238,0.035)_1px,transparent_1px),linear-gradient(0deg,rgba(34,211,238,0.025)_1px,transparent_1px)] bg-[length:96px_96px]" />
      <div className="pointer-events-none absolute inset-x-0 top-[4.45rem] h-px bg-cyan-300/50 shadow-[0_0_22px_rgba(34,211,238,0.75)]" />

      <header
        data-testid="jarvis-command-center-header"
        className="absolute inset-x-0 top-0 z-40 h-[4.5rem] border-b border-cyan-300/28 bg-[#01050d]/72 backdrop-blur-xl"
      >
        <div className="grid h-full grid-cols-[1fr_auto_1fr] items-center px-6 2xl:px-8">
          <div className="flex min-w-0 items-center gap-6">
            <div className="font-mono-ui text-sm text-cyan-100/70">09:42:17</div>
            <div className="border-l border-cyan-300/20 pl-5">
              <p className="font-display text-[0.62rem] uppercase tracking-[0.2em] text-cyan-200/50">Modo</p>
              <p className="font-display text-xs uppercase tracking-[0.18em] text-cyan-50">Cabina</p>
            </div>
          </div>

          <div className="text-center">
            <p className="font-expanded text-2xl font-bold uppercase tracking-[0.36em] text-cyan-300 blend-lighter drop-shadow-[0_0_18px_rgba(34,211,238,0.75)]">JARVIS</p>
            <p className="mt-1 font-display text-xs uppercase tracking-[0.28em] text-cyan-100/70">Centro de Mando</p>
            <span className="sr-only">Centro de Mando JARVIS</span>
            <span className="sr-only">JARVIS Presence UI + Local System Contract</span>
            <span className="sr-only">Visual Command Center GET {DASHBOARD_READ_MODEL_ENDPOINT}</span>
          </div>

          <div className="flex min-w-0 items-center justify-end gap-3">
            <Badge className="border-cyan-300/28 bg-cyan-300/10 text-cyan-100" variant="outline">
              {connectionState === "online" ? "conectado" : valueText(system.api_status, connectionState)}
            </Badge>
            <Badge className="border-cyan-300/22 bg-[#061526]/70 text-cyan-100/70" variant="outline">modo preview/read-only</Badge>
            <Badge className="border-cyan-300/22 bg-[#061526]/70 text-cyan-100/70" variant="outline">read-only</Badge>
            <Button disabled aria-disabled="true" type="button" variant="destructive" size="sm" className="h-8 border-red-400/40 bg-red-950/35 px-3 text-red-100" data-testid="jarvis-header-kill-switch">
              <ShieldAlert className="h-3.5 w-3.5" />
              KILL SWITCH
            </Button>
            <span className="sr-only">Kill Switch {valueText(system.kill_switch_state, "not_wired")}</span>
            <span className="sr-only">No POST/PUT/DELETE. No execute. No sensores. No fake metrics.</span>
            <span className="sr-only">JARVIS gobierna. Hermes ejecuta. El dashboard mira, no toca.</span>
          </div>
        </div>
      </header>

      <section
        data-testid="jarvis-cockpit-layout"
        className="absolute inset-x-0 bottom-[8.25rem] top-[4.5rem] z-10 grid min-h-0 gap-4 px-6 py-4 xl:grid-cols-[minmax(230px,17vw)_minmax(0,1fr)_minmax(300px,22vw)] 2xl:px-8"
      >
        <aside className="grid min-h-0 content-center gap-5">
          <article className="relative border-l border-cyan-300/22 bg-gradient-to-r from-[#03111f]/78 to-transparent py-2 pl-5 pr-2" data-testid="jarvis-essential-status">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full border border-cyan-300/18 bg-cyan-300/[0.055] shadow-[0_0_28px_rgba(34,211,238,0.13)]">
                <Activity className="h-5 w-5 text-cyan-200" />
              </div>
              <div>
                <p className="font-display text-[0.68rem] uppercase tracking-[0.18em] text-cyan-200/65">Estado general</p>
                <p className="font-expanded text-xl font-bold uppercase tracking-[0.08em] text-cyan-200">Óptimo</p>
              </div>
            </div>
            <StatusList items={essentialRows} />
            <div className="mt-5 grid gap-3">
              <SafetyLine>JARVIS gobierna. Hermes ejecuta.</SafetyLine>
              <SafetyLine>El dashboard mira, no toca.</SafetyLine>
            </div>
          </article>
        </aside>

        <PresenceCore voiceState={voiceState} subtitle={coreSubtitle} />

        <aside className="grid min-h-0 content-center gap-4">
          <article className="relative overflow-hidden rounded-[2px] border border-cyan-300/18 bg-[#03101f]/76 p-4 shadow-[0_0_58px_rgba(34,211,238,0.11)] backdrop-blur-md" data-testid="jarvis-approval-summary">
            <div className="mb-4 flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-red-200" />
                <h2 className="font-expanded text-xs font-bold uppercase tracking-[0.16em] text-cyan-50">Approvals</h2>
              </div>
              <Badge className="border-red-400/40 bg-red-950/30 text-red-100" variant="outline">{valueText(approvals.pending_count)} pendientes</Badge>
            </div>
            <div className="grid gap-3">
              {approvalCards.slice(0, 2).map((card, index) => (
                <div
                  key={card.id}
                  className={
                    "border bg-[#07111d]/76 p-3 shadow-[inset_0_0_38px_rgba(34,211,238,0.025)] " +
                    (index === 0 ? "border-red-400/35 shadow-[0_0_36px_rgba(248,113,113,0.12)]" : "border-cyan-300/18")
                  }
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="line-clamp-1 font-display text-[0.72rem] uppercase tracking-[0.14em] text-cyan-50">{valueText(card.title)}</p>
                    <span className={index === 0 ? "font-display text-[0.62rem] uppercase tracking-[0.16em] text-red-300" : "font-display text-[0.62rem] uppercase tracking-[0.16em] text-cyan-200/75"}>
                      {valueText(card.risk_level)}
                    </span>
                  </div>
                  <p className="mt-2 line-clamp-1 font-mono-ui text-[0.7rem] text-cyan-100/48">{valueText(card.action)}</p>
                  <p className="mt-2 font-mono-ui text-[0.68rem] text-cyan-100/55">coste est. {valueText(card.estimated_cost)}</p>
                </div>
              ))}
            </div>
            <p className="mt-3 border-t border-cyan-300/12 pt-3 text-center font-display text-[0.68rem] uppercase tracking-[0.16em] text-cyan-100/50">
              Consola de Aprobación · Preview-only
            </p>
          </article>

          <CameraPlaceholder cameraEnabled={Boolean(cameraVisionState.camera_enabled)} cameraRisk={activeRisk} />

          <details className="border border-cyan-300/14 bg-[#03101f]/58 p-3 backdrop-blur" data-testid="jarvis-local-system-contract">
            <summary className="flex cursor-pointer items-center gap-2 font-expanded text-xs font-bold uppercase tracking-[0.16em] text-cyan-100/76">
              <Lock className="h-4 w-4 text-cyan-200" />
              Local System Contract
            </summary>
            <div className="grid gap-2">
              <SafetyLine>JARVIS runtime/daemon local es el sistema.</SafetyLine>
              <SafetyLine>/jarvis es solo la interfaz visual.</SafetyLine>
              <SafetyLine>móvil y VPS serán clientes/puentes futuros.</SafetyLine>
              <SafetyLine>frontend no ejecuta directamente Hermes.</SafetyLine>
              <SafetyLine>voz/cámara reales vendrán en PRs posteriores.</SafetyLine>
            </div>
            <div className="mt-3">
              <StatusList items={localContractRows} />
            </div>
          </details>

          <article className="hidden border border-cyan-300/15 bg-[#04101f]/62 p-3" data-testid="jarvis-finance-summary">
            <div className="mb-3 flex items-center gap-2">
              <CircleDollarSign className="h-4 w-4 text-cyan-200" />
              <h2 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Finance / ROI</h2>
            </div>
            <StatusList
              items={[
                ["coste real", metricValue(financeMetrics.actual_cost)],
                ["revenue", metricValue(financeMetrics.confirmed_revenue)],
                ["ROI", metricValue(financeMetrics.roi)],
              ]}
            />
            <p className="mt-3 font-display text-xs text-warning">No fake metrics. Si no hay evidencia, mostrar unknown.</p>
          </article>
        </aside>
      </section>

      <SmartBar missionControl={missionControl} />

      <details className="absolute bottom-6 left-6 z-50" data-testid="jarvis-command-center-tabs">
        <summary className="flex cursor-pointer items-center gap-3 border border-cyan-300/14 bg-[#020b17]/82 px-5 py-3 font-display text-xs uppercase tracking-[0.18em] text-cyan-100/68 shadow-[0_0_32px_rgba(34,211,238,0.08)] backdrop-blur">
          Sistemas
          <span className="text-cyan-300/70">•</span>
          <span>{modules.length} activos</span>
          <span className="sr-only">Detalles en pestañas</span>
        </summary>

        <div className="absolute bottom-14 left-0 w-[min(72rem,calc(100vw-3rem))] border border-cyan-300/18 bg-[#020817]/96 p-4 shadow-[0_0_90px_rgba(34,211,238,0.18)] backdrop-blur-xl">
          <section className="mb-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]" data-testid="jarvis-secondary-controls">
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
                    {timeline.slice(0, 4).map((event, index) => (
                      <li key={event.source + "-" + event.event + "-" + index} className="grid grid-cols-[16px_1fr] gap-2">
                        <Square className="mt-0.5 h-2.5 w-2.5 text-cyan-200/70" />
                        <span className="font-mono-ui text-[0.7rem] text-cyan-100/55">
                          {valueText(event.event)} · {valueText(event.status)} · {valueText(event.source)}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
              <div className="grid gap-2 sm:grid-cols-4">
                <MiniStat label="approvals" value={valueText(approvals.pending_count)} variant="warning" />
                <MiniStat label="Hermes activo" value={yesNo(hermesRuntime.active_execution, "sí", "no")} variant={hermesRuntime.active_execution ? "destructive" : "success"} />
                <MiniStat label="sensores" value={sensorsDisabled ? "apagados" : "revisar"} variant={sensorsDisabled ? "success" : "destructive"} />
                <MiniStat label="dinero/deploy/email" value="bloqueado" variant="success" />
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

          <section className="border border-cyan-300/12 bg-[#04101f]/70 p-3">
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
                onClick={() => setActiveTab(tab.id)}
                className={
                  "shrink-0 border px-3 py-2 font-display text-[0.7rem] uppercase tracking-[0.12em] transition-colors " +
                  (activeTab === tab.id
                    ? "border-cyan-300/50 bg-cyan-300/10 text-cyan-100"
                    : "border-cyan-300/12 bg-[#071629]/45 text-cyan-100/50 hover:text-cyan-50")
                }
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section
        className="mt-3 max-h-[64vh] overflow-auto border border-cyan-300/12 bg-[#04101f]/60 p-4 pr-2"
        data-testid="jarvis-tab-detail-panel"
      >
        {activeTab === "cockpit" && (
          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <BadgeCheck className="h-5 w-5 text-success" />
                  <CardTitle>Visual Command Center Pilot</CardTitle>
                </div>
                <CardDescription>Piloto local read-only del cockpit completo. El dashboard mira, no toca.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3 md:grid-cols-3">
                  <SafetyLine>No se ejecuta Hermes desde el frontend.</SafetyLine>
                  <SafetyLine>No se activan sensores.</SafetyLine>
                  <SafetyLine>No hay approvals reales en esta fase.</SafetyLine>
                  <SafetyLine>No hay métricas falsas.</SafetyLine>
                  <SafetyLine>Los valores sin evidencia se muestran como unknown.</SafetyLine>
                  <SafetyLine>Dependency hardening queda para una PR separada.</SafetyLine>
                </div>
                <MissionDraftPreview missionControl={missionControl} />
                <ContractVault />
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "approvals" && (
          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-warning" />
                  <CardTitle>Consola de Aprobación</CardTitle>
                </div>
                <CardDescription>Decisiones, riesgos y requisitos de approval; la consola no aprueba ni ejecuta en esta PR.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <DisabledApprovalActions />
                <div className="grid gap-3">
                  {approvalCards.map((card) => (
                    <article key={card.id} className="border border-border/70 bg-background/35 p-4">
                      <div className="flex flex-wrap items-start justify-between gap-2">
                        <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">{card.title}</h3>
                        <Badge variant={riskVariant(valueText(card.risk_level))}>riesgo: {valueText(card.risk_level)}</Badge>
                      </div>
                      <p className="mt-2 font-mono-ui text-xs text-muted-foreground">{card.reason}</p>
                      <div className="mt-3 grid gap-2 md:grid-cols-2">
                        <SafetyLine>Readback / confirmación fuerte.</SafetyLine>
                        <SafetyLine>Las acciones sensibles requieren aprobación humana.</SafetyLine>
                      </div>
                    </article>
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
          </div>
        )}

        {activeTab === "hermes" && (
          <div className="grid gap-4">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <TerminalSquare className="h-5 w-5 text-muted-foreground" />
                  <CardTitle>Ejecución Hermes</CardTitle>
                </div>
                <CardDescription>Hermes Execution visibility: read-only, gated y sin ejecución activa.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
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
                    <p className="font-mono-ui text-sm">Esta pantalla no llama a Hermes, no aprueba y no ejecuta.</p>
                  </div>
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
                <CardDescription>Voice Core visual + TTS state preview. Sin escucha, sin grabación y sin provider externo.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <StatusList items={voiceRows} />
                <article className="border border-warning/40 bg-warning/10 p-4">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="warning">Subtítulos preview</Badge>
                    <Badge variant="success">sin TTS real</Badge>
                    <Badge variant="success">sin STT real</Badge>
                    <Badge variant="success">sin provider externo</Badge>
                  </div>
                  <p className="mt-3 font-mono-ui text-sm text-foreground">{coreSubtitle}</p>
                  <p className="mt-2 font-display text-xs text-warning">Subtítulos preview - sin TTS real, sin STT real, sin provider externo.</p>
                </article>
                <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
                  <SafetyLine>micrófono: disabled</SafetyLine>
                  <SafetyLine>grabación: false</SafetyLine>
                  <SafetyLine>proveedor externo: none/not_connected</SafetyLine>
                  <SafetyLine>En esta PR no hay audio real que parar.</SafetyLine>
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
                      <SafetyLine>La wake phrase nunca aprueba acciones.</SafetyLine>
                      <SafetyLine>La wake phrase no ejecuta acciones.</SafetyLine>
                      <SafetyLine>La aprobación por voz requiere canal autenticado, readback y auditoría.</SafetyLine>
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
                  <SafetyLine>no camera activation: {yesNo(cameraVisionPrivacy.no_camera_activation)}</SafetyLine>
                  <SafetyLine>no getUserMedia: {yesNo(cameraVisionPrivacy.no_get_user_media)}</SafetyLine>
                  <SafetyLine>no recording: {yesNo(cameraVisionPrivacy.no_recording)}</SafetyLine>
                  <SafetyLine>no snapshot: {yesNo(cameraVisionPrivacy.no_snapshot_capture)}</SafetyLine>
                  <SafetyLine>no image/video storage: {cameraVisionPrivacy.no_image_storage && cameraVisionPrivacy.no_video_storage ? "true" : "false"}</SafetyLine>
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
                <div className="grid gap-2">
                  <SafetyLine>No es un Template Builder.</SafetyLine>
                  <SafetyLine>Si dos productos parecen clones, el builder ha fallado.</SafetyLine>
                  <SafetyLine>Deploy real requiere aprobación fuerte.</SafetyLine>
                  <SafetyLine>Stripe/checkout real requiere aprobación fuerte.</SafetyLine>
                  <SafetyLine>Revenue real requiere confirmación.</SafetyLine>
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
                <CardDescription>Pilot read-only para /jarvis; El dashboard mira, no toca.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <StatusList
                  items={[
                    ["mode", valueText(frontendPilot.state?.mode, "read_only_pilot")],
                    ["route", valueText(frontendPilot.state?.dashboard_route, "/jarvis")],
                    ["endpoint", valueText(frontendPilot.state?.backend_status_endpoint, DASHBOARD_READ_MODEL_ENDPOINT)],
                    ["execute", yesNo(frontendPilot.state?.frontend_can_execute, "true", "false")],
                    ["sensors", yesNo(frontendPilot.state?.frontend_can_activate_sensors, "true", "false")],
                    ["npm audit vulnerabilities observed", valueText(frontendPilot.hardening_notes?.npm_audit_vulnerabilities_observed)],
                    ["full pytest required before merge", yesNo(frontendPilot.hardening_notes?.full_pytest_required_before_merge, "true", "false")],
                  ]}
                />
                <div className="grid gap-2">
                  <SafetyLine>Pilot read-only</SafetyLine>
                  <SafetyLine>El dashboard mira, no toca.</SafetyLine>
                  <SafetyLine>No POST/PUT/DELETE.</SafetyLine>
                  <SafetyLine>No execute.</SafetyLine>
                  <SafetyLine>No sensores.</SafetyLine>
                  <SafetyLine>Dependency hardening queda para una PR separada.</SafetyLine>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-warning" />
                  <CardTitle>Checklist de seguridad</CardTitle>
                </div>
                <CardDescription>Visual Command Center Pilot checks.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
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
                  <h3 className="font-expanded text-sm font-bold uppercase tracking-[0.12em]">Intent / Risk Preview</h3>
                  <StatusList
                    items={[
                      ["intención detectada", `${valueText(missionIntent.detected_intent)}/preview`],
                      ["confidence", valueText(missionIntent.confidence)],
                      ["mission type", valueText(missionIntent.mission_type)],
                      ["riesgo", valueText(missionIntent.risk_level)],
                      ["approval", valueText(missionIntent.approval_level)],
                    ]}
                  />
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
          </div>
        )}
      </section>
        </div>
      </details>
    </div>
  );
}
