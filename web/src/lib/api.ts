const BASE = "";

// Ephemeral session token for protected endpoints (reveal).
// Fetched once on first reveal request and cached in memory.
let _sessionToken: string | null = null;

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

async function getSessionToken(): Promise<string> {
  if (_sessionToken) return _sessionToken;
  const resp = await fetchJSON<{ token: string }>("/api/auth/session-token");
  _sessionToken = resp.token;
  return _sessionToken;
}

export const api = {
  getJarvisDashboardStatus: () => fetchJSON<JarvisDashboardStatus>("/mark-3/dashboard/status"),
  getStatus: () => fetchJSON<StatusResponse>("/api/status"),
  getSessions: (limit = 20, offset = 0) =>
    fetchJSON<PaginatedSessions>(`/api/sessions?limit=${limit}&offset=${offset}`),
  getSessionMessages: (id: string) =>
    fetchJSON<SessionMessagesResponse>(`/api/sessions/${encodeURIComponent(id)}/messages`),
  deleteSession: (id: string) =>
    fetchJSON<{ ok: boolean }>(`/api/sessions/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),
  getLogs: (params: { file?: string; lines?: number; level?: string; component?: string }) => {
    const qs = new URLSearchParams();
    if (params.file) qs.set("file", params.file);
    if (params.lines) qs.set("lines", String(params.lines));
    if (params.level && params.level !== "ALL") qs.set("level", params.level);
    if (params.component && params.component !== "all") qs.set("component", params.component);
    return fetchJSON<LogsResponse>(`/api/logs?${qs.toString()}`);
  },
  getAnalytics: (days: number) =>
    fetchJSON<AnalyticsResponse>(`/api/analytics/usage?days=${days}`),
  getConfig: () => fetchJSON<Record<string, unknown>>("/api/config"),
  getDefaults: () => fetchJSON<Record<string, unknown>>("/api/config/defaults"),
  getSchema: () => fetchJSON<{ fields: Record<string, unknown>; category_order: string[] }>("/api/config/schema"),
  saveConfig: (config: Record<string, unknown>) =>
    fetchJSON<{ ok: boolean }>("/api/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config }),
    }),
  getConfigRaw: () => fetchJSON<{ yaml: string }>("/api/config/raw"),
  saveConfigRaw: (yaml_text: string) =>
    fetchJSON<{ ok: boolean }>("/api/config/raw", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ yaml_text }),
    }),
  getEnvVars: () => fetchJSON<Record<string, EnvVarInfo>>("/api/env"),
  setEnvVar: (key: string, value: string) =>
    fetchJSON<{ ok: boolean }>("/api/env", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key, value }),
    }),
  deleteEnvVar: (key: string) =>
    fetchJSON<{ ok: boolean }>("/api/env", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key }),
    }),
  revealEnvVar: async (key: string) => {
    const token = await getSessionToken();
    return fetchJSON<{ key: string; value: string }>("/api/env/reveal", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ key }),
    });
  },

  // Cron jobs
  getCronJobs: () => fetchJSON<CronJob[]>("/api/cron/jobs"),
  createCronJob: (job: { prompt: string; schedule: string; name?: string; deliver?: string }) =>
    fetchJSON<CronJob>("/api/cron/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(job),
    }),
  pauseCronJob: (id: string) =>
    fetchJSON<{ ok: boolean }>(`/api/cron/jobs/${id}/pause`, { method: "POST" }),
  resumeCronJob: (id: string) =>
    fetchJSON<{ ok: boolean }>(`/api/cron/jobs/${id}/resume`, { method: "POST" }),
  triggerCronJob: (id: string) =>
    fetchJSON<{ ok: boolean }>(`/api/cron/jobs/${id}/trigger`, { method: "POST" }),
  deleteCronJob: (id: string) =>
    fetchJSON<{ ok: boolean }>(`/api/cron/jobs/${id}`, { method: "DELETE" }),

  // Skills & Toolsets
  getSkills: () => fetchJSON<SkillInfo[]>("/api/skills"),
  toggleSkill: (name: string, enabled: boolean) =>
    fetchJSON<{ ok: boolean }>("/api/skills/toggle", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, enabled }),
    }),
  getToolsets: () => fetchJSON<ToolsetInfo[]>("/api/tools/toolsets"),

  // Session search (FTS5)
  searchSessions: (q: string) =>
    fetchJSON<SessionSearchResponse>(`/api/sessions/search?q=${encodeURIComponent(q)}`),

  // OAuth provider management
  getOAuthProviders: () =>
    fetchJSON<OAuthProvidersResponse>("/api/providers/oauth"),
  disconnectOAuthProvider: async (providerId: string) => {
    const token = await getSessionToken();
    return fetchJSON<{ ok: boolean; provider: string }>(
      `/api/providers/oauth/${encodeURIComponent(providerId)}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
  },
  startOAuthLogin: async (providerId: string) => {
    const token = await getSessionToken();
    return fetchJSON<OAuthStartResponse>(
      `/api/providers/oauth/${encodeURIComponent(providerId)}/start`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: "{}",
      },
    );
  },
  submitOAuthCode: async (providerId: string, sessionId: string, code: string) => {
    const token = await getSessionToken();
    return fetchJSON<OAuthSubmitResponse>(
      `/api/providers/oauth/${encodeURIComponent(providerId)}/submit`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ session_id: sessionId, code }),
      },
    );
  },
  pollOAuthSession: (providerId: string, sessionId: string) =>
    fetchJSON<OAuthPollResponse>(
      `/api/providers/oauth/${encodeURIComponent(providerId)}/poll/${encodeURIComponent(sessionId)}`,
    ),
  cancelOAuthSession: async (sessionId: string) => {
    const token = await getSessionToken();
    return fetchJSON<{ ok: boolean }>(
      `/api/providers/oauth/sessions/${encodeURIComponent(sessionId)}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
  },
};

export interface PlatformStatus {
  error_code?: string;
  error_message?: string;
  state: string;
  updated_at: string;
}

export interface JarvisDashboardModule {
  name: string;
  status: "ready" | "preview" | "prepare-only" | "gated" | "disabled" | "not_connected" | "unknown" | string;
  source: string;
  risk: string;
  notes: string;
}

export interface JarvisDashboardTimelineEvent {
  event: string;
  source: string;
  status: string;
  read_only?: boolean;
}

export type JarvisApprovalStatus =
  | "preview"
  | "pending"
  | "approved"
  | "rejected"
  | "expired"
  | "blocked"
  | "forbidden"
  | "unknown"
  | string;

export type JarvisRiskLevel =
  | "low"
  | "medium"
  | "high"
  | "critical"
  | "forbidden"
  | "unknown"
  | string;

export type JarvisApprovalLevel =
  | "direct"
  | "simple"
  | "strong"
  | "double"
  | "triple"
  | "forbidden"
  | "unknown"
  | string;

export interface JarvisApprovalCard {
  id: string;
  title: string;
  action: string;
  reason: string;
  status: JarvisApprovalStatus;
  risk_level: JarvisRiskLevel;
  approval_level: JarvisApprovalLevel;
  touches: string[];
  estimated_cost: string;
  measured_cost: string;
  rollback_plan: string;
  stop_plan: string;
  expires_at: string;
  scope_summary: string;
  evidence_summary: string;
  disabled_reason: string;
  recommended_operator_action: string;
  requires_readback?: boolean;
  strong_confirmation_required?: boolean;
  double_confirmation_required?: boolean;
  triple_confirmation_required?: boolean;
  rollback_required?: boolean;
  stop_plan_required?: boolean;
  audit_required?: boolean;
  preview_only?: boolean;
  read_only?: boolean;
  source_endpoint?: string;
}

export interface JarvisHermesContract {
  jarvis_role?: string;
  hermes_role?: string;
  no_duplicate_hermes_runtime?: boolean;
  frontend_direct_execution_allowed?: boolean;
  frontend_can_execute?: boolean;
  frontend_can_call_hermes_execute?: boolean;
}

export interface JarvisHermesRuntimeStatus {
  available?: boolean | string;
  connected?: boolean | string;
  active_execution?: boolean | string;
  execution_mode?: string;
  last_execution?: string;
  last_result?: string;
  last_error?: string;
  last_rollback?: string;
  last_stop_plan?: string;
  measured_duration?: string;
  measured_cost?: string;
  running_sessions?: number | string;
  session_count?: number | string;
  supported_tool?: string;
  supported_action_type?: string;
  supported_capability?: string;
  source_endpoint?: string;
}

export interface JarvisHermesGovernedCapability {
  name: string;
  status: "ready" | "gated" | "prepare-only" | "disabled" | "not_connected" | "forbidden" | "unknown" | string;
  approval_required: boolean;
  approval_level: string;
  can_execute_from_frontend: boolean;
  notes: string;
}

export interface JarvisHermesBlockedRoute {
  route_or_action: string;
  action: string;
  blocked: boolean;
  can_execute_from_frontend: boolean;
  notes: string;
}

export interface JarvisHermesExecution {
  available?: boolean | string;
  connected?: boolean | string;
  active_execution?: boolean | string;
  execution_mode?: string;
  last_execution?: string;
  last_result?: string;
  last_error?: string;
  last_rollback?: string;
  last_stop_plan?: string;
  measured_duration?: string;
  measured_cost?: string;
  frontend_direct_execution_allowed?: boolean;
  frontend_can_execute?: boolean;
  frontend_can_call_hermes_execute?: boolean;
  running_sessions?: number | string;
  session_count?: number | string;
  supported_tool?: string;
  notes?: string;
  contract?: JarvisHermesContract;
  runtime_status?: JarvisHermesRuntimeStatus;
  governed_capabilities?: JarvisHermesGovernedCapability[];
  blocked_routes?: JarvisHermesBlockedRoute[];
  safety?: Record<string, boolean>;
  source_endpoint?: string;
}

export interface JarvisMissionControlMessage {
  role: "user" | "assistant" | string;
  speaker: string;
  content: string;
  preview_only?: boolean;
}

export interface JarvisMissionControlLifecycleStep {
  state: string;
  description: string;
  preview_only?: boolean;
}

export interface JarvisMissionControl {
  state?: {
    mode?: string;
    input_enabled?: boolean | string;
    conversation_enabled?: boolean | string;
    execution_enabled?: boolean;
    hermes_dispatch_enabled?: boolean;
    approval_creation_enabled?: boolean;
    persistence_enabled?: boolean;
    external_network_enabled?: boolean;
  };
  supported_inputs?: {
    text_command?: string;
    voice_command?: string;
    mobile_command?: string;
    wake_word_command?: string;
    file_drop?: string;
    camera_context?: string;
  };
  sample_command?: string;
  intent_preview?: {
    detected_intent?: string;
    confidence?: string;
    mission_type?: string;
    risk_level?: string;
    approval_level?: string;
    blocked_reasons?: string[];
    required_permissions?: string[];
    next_safe_action?: string;
  };
  command_lifecycle?: JarvisMissionControlLifecycleStep[];
  conversation_preview?: {
    messages?: JarvisMissionControlMessage[];
    assistant_status?: string;
    transcript_persistence?: boolean;
    memory_write?: boolean;
    memory_read?: boolean | string;
    pii_redaction_required?: boolean;
    raw_audio_stored?: boolean;
    external_provider_called?: boolean;
  };
  safety?: Record<string, boolean>;
  operator_guidance?: {
    can_do?: string;
    cannot_do_yet?: string;
    future_next_step?: string;
    sensitive_requires_approval?: string;
  };
  source_endpoint?: string;
  read_only?: boolean;
}

export interface JarvisConversationalBrainResult {
  human_response?: string;
  intent_detected?: string;
  confidence?: number | string;
  risk_level?: string;
  approval_level?: string;
  requires_approval?: boolean;
  can_prepare_preview?: boolean;
  cannot_execute_reason?: string;
  suggested_next_action?: string;
  hermes_dispatch_allowed?: boolean;
  external_provider_called?: boolean;
  llm_called?: boolean;
  memory_read?: boolean;
  memory_write?: boolean;
  transcript_persistence?: boolean;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisConversationalBrain {
  schema_version?: string;
  state?: Record<string, string | boolean | number>;
  sample_analysis?: JarvisConversationalBrainResult;
  output_contract?: string[];
  safety?: Record<string, boolean>;
  source_endpoint?: string;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisVoiceSession {
  schema_version?: string;
  current_state?: string;
  wake_listening_state?: string;
  supported_states?: string[];
  state?: Record<string, string | boolean | number>;
  separation?: Record<string, Record<string, string | boolean | number>>;
  privacy?: Record<string, boolean>;
  approval_policy?: Record<string, boolean>;
  safety?: Record<string, boolean>;
  wake_architecture?: Record<string, unknown>;
  timeline?: JarvisDashboardTimelineEvent[];
  source_endpoint?: string;
  source_endpoints?: string[];
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisVoiceCoreVisualState {
  state: string;
  label: string;
  description: string;
  risk: string;
  enabled: boolean | "preview" | string;
  sensor_required: boolean;
  can_approve: boolean;
  connection?: string;
}

export interface JarvisVoiceCore {
  state?: {
    mode?: string;
    current_state?: string;
    microphone_enabled?: boolean;
    wake_word_enabled?: boolean;
    command_listening_enabled?: boolean;
    tts_enabled?: boolean;
    stt_enabled?: boolean;
    audio_recording?: boolean;
    raw_audio_stored?: boolean;
    external_provider_called?: boolean;
    voice_approval_enabled?: boolean;
    wake_phrase_can_approve?: boolean;
    wake_phrase_can_execute?: boolean;
  };
  visual_states?: JarvisVoiceCoreVisualState[];
  tts_state?: {
    status?: "disabled" | "preview" | "not_connected" | "unknown" | string;
    speaking?: boolean;
    last_utterance?: string;
    subtitles_enabled?: boolean;
    subtitles_source?: string;
    preview_subtitle?: string;
    audio_output_enabled?: boolean;
    provider?: string;
    external_call?: boolean;
  };
  wake_word_policy?: {
    supported_phrases?: string[];
    wake_word_runtime?: string;
    wake_phrase_is_permission?: boolean;
    wake_phrase_can_approve?: boolean;
    wake_phrase_can_execute?: boolean;
    requires_authenticated_channel_for_approval?: boolean;
    critical_actions_require_readback?: boolean;
    critical_actions_require_strong_confirmation?: boolean;
  };
  privacy?: Record<string, boolean>;
  safety?: Record<string, boolean>;
  relationship?: {
    voice_can_prepare_future_intention?: boolean;
    approval_console_handles_required_approval?: boolean;
    hermes_executes_only_after_valid_approval?: boolean;
    frontend_or_voice_can_call_hermes_directly?: boolean;
    jarvis_governs?: boolean;
    hermes_executes?: boolean;
  };
  kill_switch?: {
    visible?: boolean;
    real_audio_to_stop?: boolean;
    future_must_cut_listening_tts_and_governed_execution?: boolean;
  };
  source_endpoints?: string[];
  source_endpoint?: string;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisLocalVoiceToneProfile {
  tone: "calmado" | "concentrado" | "alerta" | "intenso" | string;
  rate?: number;
  pitch?: number;
  volume?: number;
}

export interface JarvisLocalVoiceLoop {
  state?: {
    mode?: string;
    current_state?: string;
    activation?: string;
    always_listening?: boolean;
    manual_continuous_conversation?: boolean;
    conversation_active?: boolean;
    conversation_timeout_seconds?: number;
    wake_listening?: boolean;
    wake_listening_real_enabled?: boolean;
    recording?: boolean;
    continuous_recording?: boolean;
    wake_listener_enabled?: boolean;
    wake_phrase_approval?: boolean;
    hermes_dispatch_enabled?: boolean;
    critical_action_execution_enabled?: boolean;
  };
  capabilities?: {
    browser_stt_supported?: boolean | string;
    browser_tts_supported?: boolean | string;
    browser_stt_detection?: string;
    browser_tts_detection?: string;
    support_detection_location?: string;
    browser_may_use_external_services?: boolean;
    backend_stt_provider?: string;
    backend_tts_provider?: string;
  };
  browser_stt_supported?: boolean | string;
  browser_tts_supported?: boolean | string;
  manual_microphone_opt_in?: boolean;
  audio_storage?: boolean;
  raw_audio_sent_to_backend?: boolean;
  approval_by_voice_enabled?: boolean;
  wake_phrase_approval?: boolean;
  visual_states?: string[];
  mode_contract?: {
    wake_listening?: Record<string, boolean | string | number | string[]>;
    conversation_active?: Record<string, boolean | string | number | string[]>;
    recording?: Record<string, boolean | string | number | string[]>;
  };
  tone_profiles?: JarvisLocalVoiceToneProfile[];
  privacy?: Record<string, boolean>;
  approval_policy?: Record<string, boolean>;
  safety?: Record<string, boolean>;
  wake_listening_contract?: Record<string, boolean | string | string[]>;
  response_policy?: Record<string, boolean>;
  source_endpoint?: string;
  source_endpoints?: string[];
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisWakeWordFlow {
  state?: {
    mode?: string;
    wake_runtime_enabled?: boolean;
    microphone_hard_off?: boolean;
    wake_word_only_mode?: boolean;
    command_window_open?: boolean;
    push_to_talk_preview_enabled?: boolean;
    typed_wake_preview_enabled?: boolean;
    always_on_microphone_enabled?: boolean;
    background_listener_enabled?: boolean;
    stt_enabled?: boolean;
    audio_recording?: boolean;
    raw_audio_stored?: boolean;
    external_provider_called?: boolean;
  };
  supported_phrases?: string[];
  stop_phrases?: string[];
  mode_explanations?: {
    mic_hard_off?: string;
    wake_word_only?: string;
    command_listening?: string;
    push_to_talk?: string;
    typed_preview?: string;
  };
  wake_parse_preview?: {
    input_example?: string;
    detected_wake_phrase?: string;
    remaining_command_preview?: string;
    would_open_command_window?: boolean;
    would_execute?: boolean;
    would_approve?: boolean;
    would_call_hermes?: boolean;
    would_record_audio?: boolean;
    would_call_provider?: boolean;
    status?: string;
  };
  approval_policy?: {
    wake_phrase_is_permission?: boolean;
    wake_phrase_can_approve?: boolean;
    wake_phrase_can_execute?: boolean;
    voice_approval_requires_authenticated_channel?: boolean;
    sensitive_actions_require_readback?: boolean;
    critical_actions_require_double_or_triple_confirmation?: boolean;
    approval_events_must_be_audited?: boolean;
  };
  safety?: Record<string, boolean>;
  source_endpoint?: string;
  source_endpoints?: string[];
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisCameraVisionVisualState {
  state: string;
  label: string;
  description: string;
  enabled: boolean | "preview" | "future_gated" | string;
  risk: string;
  can_execute: boolean;
}

export interface JarvisCameraVision {
  state?: {
    mode?: string;
    camera_enabled?: boolean;
    camera_permission_requested?: boolean;
    preview_enabled?: boolean | string;
    recording?: boolean;
    video_recording_available?: string;
    video_recording_active?: boolean;
    video_recording_permission_requested?: boolean;
    video_recording_blob_ready?: boolean;
    raw_video_sent_to_backend?: boolean;
    streaming?: boolean;
    snapshot_capture_enabled?: boolean;
    vision_analysis_enabled?: boolean;
    image_storage_enabled?: boolean;
    video_storage_enabled?: boolean;
    external_vision_provider_called?: boolean;
    local_vision_model_connected?: boolean | string;
    background_camera_access?: boolean;
  };
  privacy?: Record<string, boolean>;
  states?: JarvisCameraVisionVisualState[];
  scope_policy?: {
    allowed_scope?: string;
    future_scope_requires_explicit_operator_permission?: boolean;
    future_analysis_must_state_what_it_can_see?: boolean;
    future_analysis_must_not_infer_sensitive_identity?: boolean;
    future_analysis_must_not_store_without_permission?: boolean;
  };
  video_recorder?: Record<string, string | boolean>;
  timeline?: JarvisDashboardTimelineEvent[];
  camera_state?: string;
  preview_state?: string;
  recording?: boolean;
  streaming?: boolean;
  snapshot?: string;
  vision_analysis?: string;
  storage?: boolean;
  provider?: string;
  source_endpoint?: string;
  source_endpoints?: string[];
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisMobileCompanionView {
  id?: string;
  name: string;
  status: "preview" | "future_gated" | "disabled" | "unknown" | string;
  can_execute: boolean;
  can_call_hermes: boolean;
  notes: string;
}

export interface JarvisMobileCompanion {
  state?: {
    mode?: string;
    pwa_baseline?: string;
    mobile_runtime_enabled?: boolean;
    mobile_can_execute?: boolean;
    mobile_can_call_hermes_directly?: boolean;
    mobile_can_approve_real_actions?: boolean;
    mobile_can_reject_real_actions?: boolean;
    mobile_can_modify_scope_real?: boolean;
    mobile_notifications_enabled?: boolean;
    remote_kill_switch_enabled?: boolean;
    remote_camera_enabled?: boolean;
    remote_microphone_enabled?: boolean;
    external_network_required?: boolean | string;
  };
  mobile_views?: JarvisMobileCompanionView[];
  safety?: Record<string, boolean>;
  pwa_policy?: {
    installable_pwa?: string;
    offline_cache_enabled?: boolean;
    push_notifications_enabled?: boolean;
    service_worker_enabled?: boolean;
    no_background_sync?: boolean;
    no_credentials_storage?: boolean;
    no_token_storage?: boolean;
  };
  timeline?: JarvisDashboardTimelineEvent[];
  source_endpoints?: string[];
  source_status?: Record<string, boolean | string | number>;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisFinanceMetric {
  value?: string | number | boolean;
  label?: string;
  source?: string;
  evidence_state?: string;
  confidence?: string;
  last_updated?: string;
}

export interface JarvisFinanceRoi {
  truth_policy?: Record<string, boolean>;
  metrics?: {
    actual_cost?: JarvisFinanceMetric;
    estimated_cost?: JarvisFinanceMetric;
    confirmed_revenue?: JarvisFinanceMetric;
    projected_revenue?: JarvisFinanceMetric;
    gross_revenue?: JarvisFinanceMetric;
    expenses?: JarvisFinanceMetric;
    net_revenue?: JarvisFinanceMetric;
    roi?: JarvisFinanceMetric;
    token_cost?: JarvisFinanceMetric;
    api_cost?: JarvisFinanceMetric;
    infra_cost?: JarvisFinanceMetric;
    manual_input_cost?: JarvisFinanceMetric;
    revenue_source?: JarvisFinanceMetric;
    [key: string]: JarvisFinanceMetric | undefined;
  };
  budget?: {
    budget_configured?: boolean | string;
    remaining_budget?: string;
    monthly_limit?: string;
    alert_threshold?: string;
    hard_stop_enabled?: boolean | string;
    notes?: string;
  };
  safety?: Record<string, boolean>;
  timeline?: JarvisDashboardTimelineEvent[];
  source_endpoint?: string;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisAdaptiveProductStage {
  name: string;
  status: "preview" | "future_gated" | "disabled" | "unknown" | string;
  can_execute: boolean;
  requires_approval: boolean;
  approval_level: string;
  evidence_required: string;
  notes: string;
}

export interface JarvisAdaptiveProductBuilder {
  state?: {
    mode?: string;
    builder_enabled?: string;
    product_generation_enabled?: boolean;
    code_generation_enabled?: boolean;
    deploy_enabled?: boolean;
    stripe_enabled?: boolean;
    landing_publish_enabled?: boolean;
    external_research_enabled?: boolean;
    hermes_dispatch_enabled?: boolean;
  };
  stages?: JarvisAdaptiveProductStage[];
  differentiation_policy?: Record<string, boolean>;
  monetization_policy?: Record<string, boolean>;
  safety?: Record<string, boolean>;
  timeline?: JarvisDashboardTimelineEvent[];
  source_endpoint?: string;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisFrontendPilotReadinessCheck {
  name: string;
  status: "passed" | "preview" | "unknown" | "failed" | string;
  evidence: string;
  notes: string;
}

export interface JarvisFrontendPilot {
  state?: {
    mode?: string;
    dashboard_route?: string;
    backend_status_endpoint?: string;
    frontend_can_execute?: boolean;
    frontend_can_approve?: boolean;
    frontend_can_activate_sensors?: boolean;
    frontend_can_move_money?: boolean;
    frontend_can_deploy?: boolean;
    frontend_can_send_email?: boolean;
    sensor_activation_scope?: string;
  };
  readiness_checks?: JarvisFrontendPilotReadinessCheck[];
  hardening_notes?: {
    npm_audit_vulnerabilities_observed?: boolean | string;
    npm_audit_fix_not_run?: boolean;
    dependency_hardening_requires_separate_pr?: boolean;
    no_lockfile_changes_expected?: boolean;
    frontend_build_required_before_merge?: boolean;
    full_pytest_required_before_merge?: boolean;
  };
  pilot_limitations?: string[];
  timeline?: JarvisDashboardTimelineEvent[];
  source_endpoint?: string;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisVisualCommandCenterPilotPanel {
  name: string;
  expected: boolean;
  source: string;
  status: "ready" | "preview" | "disabled" | "unknown" | string;
  can_execute: boolean;
  notes: string;
}

export interface JarvisVisualCommandCenterPilotCheck {
  name: string;
  status: "passed" | "preview" | "unknown" | string;
  evidence: string;
  notes: string;
}

export interface JarvisVisualCommandCenterPilotStep {
  order: number;
  check: string;
  notes: string;
}

export interface JarvisVisualCommandCenterPilot {
  state?: {
    mode?: string;
    dashboard_route?: string;
    status_endpoint?: string;
    backend_read_model_connected?: boolean;
    frontend_execution_enabled?: boolean;
    approvals_real_enabled?: boolean;
    hermes_direct_execution_enabled?: boolean;
    voice_real_enabled?: boolean;
    browser_local_voice_loop_enabled?: boolean;
    camera_real_enabled?: boolean;
    raw_audio_recording_enabled?: boolean;
    vision_analysis_enabled?: boolean;
    mobile_runtime_enabled?: boolean;
    money_enabled?: boolean;
    deploy_enabled?: boolean;
    email_enabled?: boolean;
    credentials_enabled?: boolean;
  };
  required_panels?: JarvisVisualCommandCenterPilotPanel[];
  read_only_checks?: JarvisVisualCommandCenterPilotCheck[];
  operator_pilot_steps?: JarvisVisualCommandCenterPilotStep[];
  pilot_findings?: {
    findings?: string[];
    known_limitations?: string[];
  };
  safety?: {
    pilot_is_read_only?: boolean;
    dashboard_may_read_status_only?: boolean;
    no_side_effects?: boolean;
    no_real_world_actions?: boolean;
    no_background_workers?: boolean;
    no_sensors?: boolean;
    no_uncontrolled_sensors?: boolean;
    no_money?: boolean;
    no_production?: boolean;
    no_credentials?: boolean;
    restrictions_are_approval_gates_not_permanent_bans?: boolean;
  };
  timeline?: JarvisDashboardTimelineEvent[];
  source_endpoint?: string;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisLocalSystemContract {
  name?: string;
  presence_ui?: string;
  local_runtime_daemon_is_system?: boolean;
  web_route?: string;
  web_route_is_visual_interface_only?: boolean;
  frontend_executes_hermes_directly?: boolean;
  frontend_is_runtime?: boolean;
  frontend_can_activate_real_voice?: boolean;
  frontend_can_activate_real_camera?: boolean;
  frontend_can_record_raw_audio_locally?: boolean;
  frontend_can_record_video_locally?: boolean;
  mobile_and_vps_are_future_clients_or_bridges?: boolean;
  real_voice_camera_in_future_prs?: boolean;
  real_browser_voice_loop_in_this_pr?: boolean;
  real_browser_camera_preview_in_this_pr?: boolean;
  real_browser_raw_audio_recorder_in_this_pr?: boolean;
  real_browser_video_recorder_in_this_pr?: boolean;
  real_camera_in_future_prs?: boolean;
  real_vision_analysis_in_future_prs?: boolean;
  jarvis_governs?: boolean;
  hermes_executes?: boolean;
  no_duplicate_hermes_runtime?: boolean;
  visual_contract?: {
    primary_experience?: string;
    central_core_states?: string[];
    smart_bar?: string;
    camera_placeholder?: string;
    raw_audio_recorder?: string;
    folded_history?: string;
  };
  future_bridges?: {
    mobile?: string;
    vps?: string;
    voice_runtime?: string;
    camera_runtime?: string;
  };
  safety?: Record<string, boolean>;
  source_endpoint?: string;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisRawAudioRecording {
  state?: {
    mode?: string;
    available?: string | boolean;
    recording_active?: boolean;
    activation?: string;
    stop_control_required?: boolean;
    download_available_after_stop?: boolean;
    delete_available_after_stop?: boolean;
    backend_upload_enabled?: boolean;
    external_streaming_enabled?: boolean;
    hidden_recording_enabled?: boolean;
  };
  retention?: Record<string, string | boolean>;
  audit?: {
    metadata_only?: boolean;
    events?: string[];
    raw_audio_in_audit?: boolean;
    backend_audit_complete?: boolean;
    backend_audit_gap?: string;
  };
  privacy?: Record<string, boolean>;
  source_endpoint?: string;
  browser_source?: string;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisMemoryBrain {
  state?: Record<string, string | boolean>;
  entities?: Array<Record<string, unknown>>;
  preferences?: Array<Record<string, unknown>>;
  decisions?: Array<Record<string, unknown>>;
  contradictions?: Array<Record<string, unknown>>;
  counts?: {
    outcomes?: number | string;
    failures?: number | string;
    learning_proposals?: number | string;
    audit_events?: number | string;
  };
  why_jarvis_remembers?: string[];
  compaction?: Record<string, string | boolean>;
  forget_delete?: Record<string, string | boolean>;
  safety?: Record<string, boolean>;
  source_endpoints?: string[];
  source_status?: Record<string, unknown>;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisLocalDoctorCheck {
  name: string;
  status: string;
  evidence: string;
  read_only?: boolean;
}

export interface JarvisLocalDoctor {
  state?: Record<string, string | boolean | number>;
  checks?: JarvisLocalDoctorCheck[];
  optional_dependencies?: Record<string, { available?: boolean; source?: string; status?: string; version?: string }>;
  runtime?: Record<string, unknown>;
  ports?: Record<string, unknown>;
  browser_checks?: Record<string, unknown>;
  browser_only_capabilities?: Record<string, unknown>;
  safety?: Record<string, boolean>;
  source_endpoint?: string;
  preview_only?: boolean;
  read_only?: boolean;
  source_status?: Record<string, unknown>;
}

export interface JarvisSensorLedger {
  schema_version?: string;
  state?: Record<string, any>;
  events?: Array<Record<string, unknown>>;
  retention?: Record<string, unknown>;
  contracts?: Array<Record<string, unknown>>;
  safety?: Record<string, boolean>;
  source_endpoint?: string;
  read_only?: boolean;
}

export interface JarvisDashboardStatus {
  system?: {
    api_status?: string;
    local_first?: boolean;
    mode?: string;
    free_autonomy_enabled?: boolean;
    preview_first?: boolean;
    kill_switch_state?: string;
    generated_at?: string;
  };
  jarvis_hermes_contract?: {
    jarvis_role?: string;
    hermes_role?: string;
    no_duplicate_hermes_runtime?: boolean;
    frontend_direct_execution_allowed?: boolean;
    frontend_can_execute?: boolean;
    frontend_can_call_hermes_execute?: boolean;
  };
  local_system_contract?: JarvisLocalSystemContract;
  release_candidate?: {
    status?: string;
    readiness?: Record<string, string>;
    not_ready_for_free_autonomy?: boolean;
    restrictions_are_approval_gates_not_permanent_bans?: boolean;
    pilot_readiness?: string;
    pilot_executed?: boolean;
  };
  modules?: JarvisDashboardModule[];
  mission_control?: JarvisMissionControl;
  approvals?: {
    pending_count?: number | string;
    critical_count?: number | string;
    blocked_count?: number | string;
    expired_count?: number | string;
    preview_count?: number | string;
    action_buttons_enabled?: boolean;
    all_actions_read_only?: boolean;
    wake_phrase_can_approve?: boolean;
    frontend_can_approve?: boolean;
    frontend_can_reject?: boolean;
    frontend_can_modify_scope?: boolean;
    critical_actions_require_strong_approval?: boolean;
    cards?: JarvisApprovalCard[];
    cards_state?: string;
    preview_only?: boolean;
    readback_policy?: Record<string, boolean>;
  };
  hermes_execution?: JarvisHermesExecution;
  conversational_brain?: JarvisConversationalBrain;
  voice_session?: JarvisVoiceSession;
  wake_architecture?: Record<string, unknown>;
  voice_core?: JarvisVoiceCore;
  local_voice_loop?: JarvisLocalVoiceLoop;
  wake_word_flow?: JarvisWakeWordFlow;
  voice_wake?: {
    microphone_state?: string;
    wake_word_state?: string;
    wake_phrases?: string[];
    wake_phrase_can_approve?: boolean;
    wake_phrase_can_execute?: boolean;
    audio_recording?: boolean;
    raw_audio_stored?: boolean;
    external_provider_called?: boolean;
    source_endpoints?: string[];
  };
  camera_vision?: JarvisCameraVision;
  raw_audio_recording?: JarvisRawAudioRecording;
  sensor_ledger?: JarvisSensorLedger;
  event_bus?: Record<string, any>;
  policy_status?: Record<string, any>;
  memory_brain?: JarvisMemoryBrain;
  mobile_companion?: JarvisMobileCompanion;
  finance_roi?: JarvisFinanceRoi;
  adaptive_product_builder?: JarvisAdaptiveProductBuilder;
  frontend_pilot?: JarvisFrontendPilot;
  visual_command_center_pilot?: JarvisVisualCommandCenterPilot;
  mobile?: {
    companion_state?: string;
    direct_hermes_call_allowed?: boolean;
    remote_kill_switch_state?: string;
    approval_actions_enabled?: boolean;
    source_endpoints?: string[];
  };
  finance?: {
    actual_cost?: string;
    estimated_cost?: string;
    confirmed_revenue?: string;
    projected_revenue?: string;
    gross_revenue?: string;
    expenses?: string;
    net_revenue?: string;
    roi?: string;
    no_fake_metrics?: boolean;
  };
  product_builder?: {
    stages?: string[];
    deploy_requires_strong_approval?: boolean;
    stripe_checkout_requires_strong_approval?: boolean;
    real_revenue_must_be_confirmed?: boolean;
  };
  safety?: Record<string, boolean>;
  timeline?: JarvisDashboardTimelineEvent[];
  local_doctor?: JarvisLocalDoctor;
  read_only_contract?: {
    aggregated_endpoint?: string;
    allowed_http_methods_for_frontend?: string[];
    internal_sources_are_read_only_status_or_audit?: boolean;
    frontend_must_not_call_execute?: boolean;
    frontend_must_not_request_sensor_permissions?: boolean;
    frontend_sensor_permission_scope?: string;
    frontend_must_not_request_camera_permissions?: boolean;
    frontend_camera_permission_scope?: string;
  };
}

export interface StatusResponse {
  active_sessions: number;
  config_path: string;
  config_version: number;
  env_path: string;
  gateway_exit_reason: string | null;
  gateway_pid: number | null;
  gateway_platforms: Record<string, PlatformStatus>;
  gateway_running: boolean;
  gateway_state: string | null;
  gateway_updated_at: string | null;
  hermes_home: string;
  latest_config_version: number;
  release_date: string;
  version: string;
}

export interface SessionInfo {
  id: string;
  source: string | null;
  model: string | null;
  title: string | null;
  started_at: number;
  ended_at: number | null;
  last_active: number;
  is_active: boolean;
  message_count: number;
  tool_call_count: number;
  input_tokens: number;
  output_tokens: number;
  preview: string | null;
}

export interface PaginatedSessions {
  sessions: SessionInfo[];
  total: number;
  limit: number;
  offset: number;
}

export interface EnvVarInfo {
  is_set: boolean;
  redacted_value: string | null;
  description: string;
  url: string | null;
  category: string;
  is_password: boolean;
  tools: string[];
  advanced: boolean;
}

export interface SessionMessage {
  role: "user" | "assistant" | "system" | "tool";
  content: string | null;
  tool_calls?: Array<{
    id: string;
    function: { name: string; arguments: string };
  }>;
  tool_name?: string;
  tool_call_id?: string;
  timestamp?: number;
}

export interface SessionMessagesResponse {
  session_id: string;
  messages: SessionMessage[];
}

export interface LogsResponse {
  file: string;
  lines: string[];
}

export interface AnalyticsDailyEntry {
  day: string;
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  reasoning_tokens: number;
  estimated_cost: number;
  actual_cost: number;
  sessions: number;
}

export interface AnalyticsModelEntry {
  model: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
  sessions: number;
}

export interface AnalyticsResponse {
  daily: AnalyticsDailyEntry[];
  by_model: AnalyticsModelEntry[];
  totals: {
    total_input: number;
    total_output: number;
    total_cache_read: number;
    total_reasoning: number;
    total_estimated_cost: number;
    total_actual_cost: number;
    total_sessions: number;
  };
}

export interface CronJob {
  id: string;
  name?: string;
  prompt: string;
  schedule: { kind: string; expr: string; display: string };
  schedule_display: string;
  enabled: boolean;
  state: string;
  deliver?: string;
  last_run_at?: string | null;
  next_run_at?: string | null;
  last_error?: string | null;
}

export interface SkillInfo {
  name: string;
  description: string;
  category: string;
  enabled: boolean;
}

export interface ToolsetInfo {
  name: string;
  label: string;
  description: string;
  enabled: boolean;
  configured: boolean;
  tools: string[];
}

export interface SessionSearchResult {
  session_id: string;
  snippet: string;
  role: string | null;
  source: string | null;
  model: string | null;
  session_started: number | null;
}

export interface SessionSearchResponse {
  results: SessionSearchResult[];
}

// ── OAuth provider types ────────────────────────────────────────────────

export interface OAuthProviderStatus {
  logged_in: boolean;
  source?: string | null;
  source_label?: string | null;
  token_preview?: string | null;
  expires_at?: string | null;
  has_refresh_token?: boolean;
  last_refresh?: string | null;
  error?: string;
}

export interface OAuthProvider {
  id: string;
  name: string;
  /** "pkce" (browser redirect + paste code), "device_code" (show code + URL),
   *  or "external" (delegated to a separate CLI like Claude Code or Qwen). */
  flow: "pkce" | "device_code" | "external";
  cli_command: string;
  docs_url: string;
  status: OAuthProviderStatus;
}

export interface OAuthProvidersResponse {
  providers: OAuthProvider[];
}

/** Discriminated union — the shape of /start depends on the flow. */
export type OAuthStartResponse =
  | {
      session_id: string;
      flow: "pkce";
      auth_url: string;
      expires_in: number;
    }
  | {
      session_id: string;
      flow: "device_code";
      user_code: string;
      verification_url: string;
      expires_in: number;
      poll_interval: number;
    };

export interface OAuthSubmitResponse {
  ok: boolean;
  status: "approved" | "error";
  message?: string;
}

export interface OAuthPollResponse {
  session_id: string;
  status: "pending" | "approved" | "denied" | "expired" | "error";
  error_message?: string | null;
  expires_at?: number | null;
}
