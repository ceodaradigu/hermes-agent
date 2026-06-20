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
  getJarvisExecutionStatus: () => fetchJSON<JarvisGovernedExecutionStatus>("/mark-3/execution/status"),
  getJarvisPhase1Status: () => fetchJSON<JarvisPhase1Status>("/mark-3/phase-1/status"),
  getJarvisPhase2Status: () => fetchJSON<Record<string, unknown>>("/mark-3/phase-2/status"),
  getJarvisPhase3Status: () => fetchJSON<Record<string, unknown>>("/mark-3/phase-3/status"),
  getJarvisPhase4Status: () => fetchJSON<Record<string, unknown>>("/mark-3/phase-4/status"),
  getJarvisPhase5Status: () => fetchJSON<Record<string, unknown>>("/mark-3/phase-5/status"),
  getJarvisPhase7Status: () => fetchJSON<Record<string, unknown>>("/mark-3/phase-7/status"),
  getJarvisLocalDaemonStatus: () => fetchJSON<Record<string, unknown>>("/mark-3/local-daemon/status"),
  getJarvisLocalControllerStatus: () => fetchJSON<Record<string, unknown>>("/mark-3/local-controller/status"),
  getJarvisLocalDaemonHealth: () => fetchJSON<Record<string, unknown>>("/mark-3/local-daemon/health"),
  getJarvisLocalDoctorStatus: () => fetchJSON<Record<string, unknown>>("/mark-3/local-doctor/status"),
  getJarvisTrustedApprovalChannels: () => fetchJSON<Record<string, unknown>>("/mark-3/trusted-approval-channels/status"),
  getJarvisTrustedDevices: () => fetchJSON<Record<string, unknown>>("/mark-3/trusted-devices/status"),
  getJarvisLocalPairingStatus: () => fetchJSON<Record<string, unknown>>("/mark-3/local-pairing/status"),
  getJarvisVoiceApprovalStatus: () => fetchJSON<Record<string, unknown>>("/mark-3/voice-approval/status"),
  getJarvisNotificationsStatus: () => fetchJSON<Record<string, unknown>>("/mark-3/notifications/status"),
  getJarvisRemotePairingStatus: () => fetchJSON<Record<string, unknown>>("/mark-3/remote-pairing/status"),
  getJarvisTelegramBridgeStatus: () => fetchJSON<Record<string, unknown>>("/mark-3/telegram-bridge/status"),
  getJarvisStopRollbackStatus: () => fetchJSON<Record<string, unknown>>("/mark-3/stop-rollback/status"),
  getJarvisActionCatalog: () => fetchJSON<{ actions?: JarvisActionContract[] }>("/mark-3/execution/action-catalog"),
  getJarvisExecutionHistory: (limit = 25) =>
    fetchJSON<JarvisExecutionHistoryResponse>(`/mark-3/execution/history?limit=${limit}`),
  createJarvisExecutionPreview: (payload: JarvisExecutionPreviewRequest) =>
    fetchJSON<JarvisExecutionPreview>("/mark-3/execution/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  requestJarvisExecutionApproval: (payload: JarvisExecutionRequestApprovalRequest) =>
    fetchJSON<JarvisExecutionApprovalEnvelope>("/mark-3/execution/request-approval", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  decideJarvisExecutionApproval: (payload: JarvisExecutionApprovalDecisionRequest) =>
    fetchJSON<JarvisExecutionApprovalEnvelope>("/mark-3/execution/approval-decision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  dispatchJarvisExecution: (payload: JarvisExecutionDispatchRequest) =>
    fetchJSON<JarvisExecutionDispatchResult>("/mark-3/execution/dispatch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  cancelJarvisExecution: (payload: JarvisExecutionCancelRequest) =>
    fetchJSON<JarvisExecutionPreview>("/mark-3/execution/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  stopJarvisExecution: (payload: JarvisExecutionStopRequest) =>
    fetchJSON<JarvisExecutionStopResult>("/mark-3/execution/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
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
  | "none"
  | "soft"
  | "normal"
  | "direct"
  | "simple"
  | "strong"
  | "double"
  | "triple"
  | "blocked"
  | "unsupported"
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

export interface JarvisExecutionPreviewRequest {
  intent: string;
  source?: "typed_text" | "voice_transcript" | "wake_phrase_command" | "remote_input" | "unknown" | string;
  operator?: string;
  session_id?: string | null;
  target_path?: string | null;
  command?: string | null;
  requested_action_type?: string | null;
  action_key?: string | null;
  inputs?: Record<string, unknown> | null;
  transcript_confidence?: number;
  voice_session_state?: string;
}

export interface JarvisExecutionRequestApprovalRequest {
  preview_id: string;
  actor?: string;
}

export interface JarvisExecutionApprovalDecisionRequest {
  approval_id: string;
  decision: "approve" | "reject" | "cancel" | "request_clarification" | string;
  actor?: string;
  confirmation_phrase?: string | null;
  readback_text?: string | null;
  reason?: string;
  decision_source?: string;
  channel?: string;
}

export interface JarvisExecutionDispatchRequest {
  preview_id: string;
  approval_id?: string | null;
  actor?: string;
}

export interface JarvisExecutionCancelRequest {
  preview_id: string;
  reason?: string;
  actor?: string;
}

export interface JarvisExecutionStopRequest {
  preview_id?: string | null;
  session_id?: string | null;
  reason?: string;
}

export interface JarvisExecutionApprovalEnvelope {
  schema_version?: string;
  approval_id: string;
  preview_id: string;
  correlation_id?: string;
  created_at?: string;
  expires_at?: string;
  status: JarvisApprovalStatus | string;
  action_id?: string;
  action_key?: string;
  action_type?: string;
  risk_level?: JarvisRiskLevel;
  approval_level?: JarvisApprovalLevel;
  approval_level_required?: JarvisApprovalLevel;
  requester?: string;
  reason?: string;
  preview?: Record<string, unknown>;
  challenge?: string;
  second_confirmation_required?: boolean;
  third_confirmation_required?: boolean;
  decided_at?: string | null;
  rejection_reason?: string;
  audit_id?: string;
  used_at?: string | null;
  confirmation_level_required?: string;
  confirmation_phrase?: string | null;
  readback_required?: boolean;
  readback_text?: string;
  requires_strong_confirmation?: boolean;
  requires_double_confirmation?: boolean;
  requires_triple_confirmation?: boolean;
  stronger_approval_configured?: boolean;
  can_approve?: boolean;
  can_dispatch_after_approval?: boolean;
  requested_by?: string;
  decision_reason?: string;
}

export interface JarvisExecutionPreview {
  schema_version?: string;
  preview_id: string;
  correlation_id?: string;
  created_at?: string;
  updated_at?: string;
  state: string;
  source?: string;
  operator?: string;
  decision: "allowed" | "requires_approval" | "denied" | "unsupported" | string;
  risk_level: JarvisRiskLevel;
  approval_level: JarvisApprovalLevel;
  approval_level_required?: JarvisApprovalLevel;
  requires_approval: boolean;
  inputs?: Record<string, unknown>;
  action: {
    action_id?: string;
    action_key?: string;
    title?: string;
    summary?: string;
    decision?: string;
    action_type?: string;
    risk_level?: string;
    approval_level?: string;
    approval_level_required?: string;
    requires_approval?: boolean;
    requires_readback?: boolean;
    requires_strong_confirmation?: boolean;
    requires_double_confirmation?: boolean;
    requires_triple_confirmation?: boolean;
    denied_reason?: string;
    unsupported_reason?: string;
    target_path_display?: string;
    target_path_fingerprint?: string;
    scope?: string[];
    will_do?: string[];
    will_not_do?: string[];
    rollback_plan?: string;
    stop_plan?: string;
    command_allowlisted?: boolean;
    stop_supported?: boolean;
    rollback_supported?: boolean;
    rollback_status?: string;
    network_allowed?: boolean;
    external_side_effects?: boolean;
    secrets_policy?: string;
  };
  preview?: {
    title?: string;
    summary?: string;
    will_do?: string[];
    will_not_do?: string[];
    rollback_plan?: string;
    stop_plan?: string;
    audit_destination?: string;
    memory_influence?: Array<Record<string, unknown>>;
  };
  approval_envelope?: JarvisExecutionApprovalEnvelope | null;
  dispatch?: Record<string, unknown> | null;
  unsupported_reason?: string | null;
  denied_reason?: string | null;
  protected_message?: string;
  hermes_dispatch_allowed?: boolean;
  frontend_direct_hermes_allowed?: boolean;
  memory_grants_permission?: boolean;
}

export interface JarvisExecutionDispatchResult {
  schema_version?: string;
  preview_id?: string;
  state?: string;
  decision?: string;
  risk_level?: string;
  approval_level?: string;
  dispatch?: Record<string, unknown>;
  hermes_dispatch_allowed?: boolean;
  frontend_direct_hermes_allowed?: boolean;
  memory_grants_permission?: boolean;
}

export interface JarvisExecutionStopResult {
  status: string;
  reason?: string;
  preview_id?: string | null;
  session_id?: string | null;
  session?: Record<string, unknown>;
}

export interface JarvisGovernedExecutionStatus {
  schema_version?: string;
  state?: Record<string, unknown>;
  counts?: Record<string, number | string>;
  recent_previews?: JarvisExecutionPreview[];
  recent_approval_envelopes?: JarvisExecutionApprovalEnvelope[];
  approval_levels?: string[];
  action_catalog?: JarvisActionContract[];
  execution_history?: JarvisExecutionHistoryStatus;
  stop_rollback_contracts?: Record<string, unknown>;
  approval_v2?: Record<string, unknown>;
  local_runtime?: JarvisLocalRuntimeStatus;
  browser_verification?: JarvisBrowserVerificationStatus;
  safety?: Record<string, boolean>;
  source_endpoint?: string;
}

export interface JarvisActionContract {
  action_id?: string;
  action_key: string;
  title?: string;
  category?: string;
  description: string;
  allowed_inputs_schema?: Record<string, unknown>;
  risk_level: string;
  approval_required: string;
  approval_level_required?: string;
  timeout_seconds?: number;
  stop_supported?: boolean;
  rollback_supported?: boolean;
  audit_event_types?: string[];
  output_redaction?: string;
  filesystem_scope?: string;
  network_allowed?: boolean;
  external_side_effects?: boolean;
  secrets_policy?: string;
  stop_method?: string;
  rollback_plan?: string;
  rollback_risk?: string;
  rollback_requires_approval?: boolean;
  rollback_status?: string;
  rollback_limitations?: string[];
  execution_backend?: string;
  side_effects?: string[];
  flags?: {
    filesystem?: boolean;
    network?: boolean;
    github?: boolean;
    browser?: boolean;
    sandbox?: boolean;
  };
  dry_run_available?: boolean;
  audit_requirements?: Record<string, unknown>;
  voice_approval_eligible?: boolean;
  default_state?: {
    enabled?: boolean;
    disabled_reason?: string;
  };
  contract?: Record<string, unknown>;
}

export interface JarvisExecutionHistoryItem {
  execution_id: string;
  action_id?: string;
  approval_id?: string;
  intent_summary?: string;
  action_key?: string;
  status?: string;
  risk_level?: string;
  approval_level?: string;
  started_at?: string;
  finished_at?: string;
  duration_ms?: number;
  result_summary?: string;
  error_summary?: string;
  stop_requested?: boolean;
  rollback_requested?: boolean;
  rollback_status?: string;
  audit_ids?: string[];
  memory_influence_ids?: string[];
  redaction_summary?: Record<string, unknown>;
  contains_secret?: boolean;
  contains_credential?: boolean;
  contains_raw_audio?: boolean;
  contains_camera_frame?: boolean;
}

export interface JarvisExecutionHistoryStatus {
  available?: boolean;
  persistent?: boolean;
  local_only?: boolean;
  metadata_only?: boolean;
  record_count?: number;
  storage_path?: string;
  storage_configured?: boolean;
  contains_secret?: boolean;
  contains_credential?: boolean;
  contains_raw_audio?: boolean;
  contains_camera_frame?: boolean;
  recent?: JarvisExecutionHistoryItem[];
}

export interface JarvisExecutionHistoryResponse {
  items?: JarvisExecutionHistoryItem[];
  status?: JarvisExecutionHistoryStatus;
  read_only?: boolean;
  source_endpoint?: string;
}

export interface JarvisLocalRuntimeStatus {
  schema_version?: string;
  daemon_status?: string;
  tray_status?: string;
  local_runtime_ready?: boolean;
  phase_3_ready?: boolean;
  local_only?: boolean;
  bind_host?: string;
  bind_port?: number;
  startup_mode?: string;
  background_listening_enabled?: boolean;
  auto_start_enabled?: boolean;
  camera_auto_start?: boolean;
  mic_auto_start?: boolean;
  wake_auto_start?: boolean;
  user_opt_in_required?: boolean;
  local_only_binding?: Record<string, unknown>;
  privacy_contract?: Record<string, boolean>;
  state_dir_contract?: Record<string, unknown>;
  daemon?: Record<string, unknown>;
  tray?: Record<string, unknown>;
  trusted_approval_channels?: Record<string, unknown>;
  remote_bridge_future?: Record<string, unknown>;
  failure_modes?: string[];
  source_endpoint?: string;
}

export interface JarvisBrowserVerificationCheck {
  name: string;
  passed?: boolean;
  status?: string;
  notes?: string;
  description?: string;
}

export interface JarvisBrowserVerificationStatus {
  status?: string;
  route?: string;
  playwright_required?: boolean;
  playwright_status?: string;
  static_plus_manual_checklist?: boolean;
  check_count?: number;
  checks?: JarvisBrowserVerificationCheck[];
  all_static_checks_passed?: boolean;
  no_auto_get_user_media?: boolean;
  no_execute_route?: boolean;
  no_direct_hermes_frontend?: boolean;
  phase_3_pilot?: Record<string, unknown>;
  phase_4_pilot?: Record<string, unknown>;
  source_endpoint?: string;
}

export interface JarvisPhase1Status {
  schema_version?: string;
  phase?: string;
  status?: string;
  flow?: string[];
  capabilities?: Record<string, string>;
  risks?: Record<string, string>;
  known_limitations?: string[];
  route_readiness?: Record<string, boolean>;
  pilot_checklist?: Array<Record<string, unknown>>;
  execution_status?: JarvisGovernedExecutionStatus;
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

export interface JarvisConversationalIntake {
  schema_version?: string;
  state?: Record<string, string | boolean | number | string[]>;
  sample?: {
    intake?: {
      schema_version?: string;
      intake_id?: string;
      created_at?: string;
      source?: string;
      raw_text?: string;
      normalized_text?: string;
      language?: string;
      wake_phrase_detected?: boolean;
      wake_phrase_used?: string | null;
      remaining_command?: string;
      operator?: string;
      session_id?: string | null;
      voice_session_state?: string;
      transcript_confidence?: number;
      contains_sensitive_request?: boolean;
      sensitive_reasons?: string[];
      requires_clarification?: boolean;
      safe_to_classify?: boolean;
      safe_to_prepare_preview?: boolean;
      safe_to_dispatch_to_hermes?: boolean;
    };
    classification?: {
      intent_detected?: string;
      confidence?: number;
      risk_level?: string;
      approval_level?: string;
      requires_approval?: boolean;
      can_prepare_preview?: boolean;
      requires_clarification?: boolean;
      denied?: boolean;
      blocked_reasons?: string[];
      sensitive_reasons?: string[];
      next_safe_action?: string;
      safe_to_dispatch_to_hermes?: boolean;
    };
    preview_candidate?: Record<string, unknown> | null;
  };
  output_contract?: string[];
  safety?: Record<string, boolean>;
  source_endpoint?: string;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisBrainProviderStatus {
  schema_version?: string;
  provider_name?: string;
  provider_mode?: string;
  available?: boolean;
  default_provider?: string;
  external_llm_enabled?: boolean;
  external_provider_called?: boolean;
  api_key_required?: boolean;
  api_key_loaded?: boolean;
  reads_env?: boolean;
  network_allowed?: boolean;
  honest_status?: string;
  missing_configuration?: string[];
  safety?: Record<string, boolean>;
}

export interface JarvisBrainAdapter {
  schema_version?: string;
  state?: Record<string, string | boolean | number>;
  providers?: Record<string, JarvisBrainProviderStatus>;
  sample?: {
    brain_request?: Record<string, unknown>;
    brain_response?: {
      human_response?: string;
      intent_detected?: string;
      confidence?: number;
      risk_level?: string;
      approval_level?: string;
      requires_approval?: boolean;
      can_prepare_preview?: boolean;
      preview_candidate?: Record<string, unknown> | null;
      cannot_execute_reason?: string;
      suggested_next_action?: string;
      clarification_question?: string | null;
      memory_write_proposal?: Record<string, unknown> | null;
      hermes_candidate?: Record<string, unknown> | null;
      hermes_dispatch_allowed?: boolean;
      external_provider_called?: boolean;
      provider_name?: string;
      provider_mode?: string;
      evidence?: string[];
      uncertainty?: string[];
      audit_summary?: Record<string, unknown>;
    };
    provider_status?: JarvisBrainProviderStatus;
    disabled_external_provider_status?: JarvisBrainProviderStatus;
  };
  contracts?: Record<string, string | boolean>;
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

export interface JarvisVoiceProviderContract {
  provider_name?: string;
  mode?: string;
  installed?: boolean | string;
  detected?: boolean | string;
  enabled?: boolean;
  requires_model?: boolean;
  model_path?: string | null;
  model_available?: boolean;
  local_only?: boolean;
  network_required?: boolean;
  external_provider?: boolean;
  raw_audio_persistence?: boolean;
  voice_name?: string | null;
  voice_quality?: string;
  status?: string;
  unavailable_reason?: string;
  browser_client_side?: boolean;
  detection_location?: string;
}

export interface JarvisPhase2VoiceRuntime {
  schema_version?: string;
  voice_runtime_diagnostics?: {
    browser_stt_capability?: string;
    browser_tts_capability?: string;
    selected_voice_metadata?: string;
    selected_voice_name?: string;
    tts_interrupt_stop?: string;
    low_confidence_clarification_threshold?: number;
    low_confidence_behavior?: string;
    voice_intent_submitted_to_preview?: boolean;
    voice_intent_submitted_behavior?: string;
    voice_can_read_readback?: boolean;
    voice_can_cancel_or_stop?: boolean;
    voice_can_approve?: boolean;
    voice_can_execute_without_approval?: boolean;
    raw_audio_sent_to_backend?: boolean;
    raw_audio_persisted_backend?: boolean;
  };
  wake_runtime_readiness?: {
    provider_status?: string;
    wake_always_on_real?: boolean;
    always_on_enabled?: boolean;
    openwakeword_active?: boolean;
    auto_mic?: boolean;
    wake_phrase_can_approve?: boolean;
    wake_phrase_can_execute?: boolean;
    readiness_contract_only?: boolean;
  };
  privacy_status?: Record<string, boolean>;
  source_endpoint?: string;
  base_voice_runtime_pack?: Record<string, unknown>;
  base_voice_session?: Record<string, unknown>;
}

export interface JarvisVoiceRuntimePack {
  schema_version?: string;
  runtime_id?: string;
  mode?: string;
  enabled?: boolean;
  manual_push_to_talk_enabled?: boolean;
  browser_stt_available?: string;
  browser_tts_available?: string;
  local_stt_provider_status?: Record<string, JarvisVoiceProviderContract>;
  local_tts_provider_status?: Record<string, JarvisVoiceProviderContract>;
  wake_runtime_status?: Record<string, unknown>;
  active_session?: Record<string, unknown>;
  last_transcript_summary?: Record<string, unknown>;
  last_response_summary?: Record<string, unknown>;
  current_state?: string;
  supported_states?: string[];
  can_interrupt?: boolean;
  can_cancel?: boolean;
  raw_audio_sent_to_backend?: boolean;
  transcript_persistence?: boolean;
  voice_approval_enabled?: boolean;
  wake_phrase_can_approve?: boolean;
  wake_phrase_can_execute?: boolean;
  hermes_dispatch_allowed?: boolean;
  provider_architecture?: {
    stt_providers?: Record<string, JarvisVoiceProviderContract>;
    tts_providers?: Record<string, JarvisVoiceProviderContract>;
    no_provider_install_performed?: boolean;
    no_model_download_performed?: boolean;
    browser_detection_location?: string;
    backend_detection_location?: string;
  };
  transcript_lifecycle?: Record<string, unknown>;
  tts_lifecycle?: Record<string, unknown>;
  visual_state_mapping?: Record<string, string>;
  safety?: Record<string, boolean>;
  phase_2_runtime?: JarvisPhase2VoiceRuntime;
  source_endpoint?: string;
  source_endpoints?: string[];
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
    governed_execution_enabled?: boolean;
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
  state?: Record<string, string | boolean | number>;
  entities?: Array<Record<string, unknown>>;
  facts?: Array<Record<string, unknown>>;
  preferences?: Array<Record<string, unknown>>;
  decisions?: Array<Record<string, unknown>>;
  projects?: Array<Record<string, unknown>>;
  contradictions?: Array<Record<string, unknown>>;
  active_memories?: Array<Record<string, unknown>>;
  pending_review?: Array<Record<string, unknown>>;
  forgotten_deleted?: Array<Record<string, unknown>>;
  counts?: {
    outcomes?: number | string;
    failures?: number | string;
    learning_proposals?: number | string;
    audit_events?: number | string;
    entities?: number | string;
    facts?: number | string;
    preferences?: number | string;
    decisions?: number | string;
    projects?: number | string;
    contradictions?: number | string;
    active_memories?: number | string;
    pending_review?: number | string;
    forgotten_deleted?: number | string;
  };
  why_jarvis_remembers?: string[];
  explanation_preview?: {
    why_jarvis_remembers?: string[];
    what_memory_influenced?: string[];
    pending_approval?: Array<Record<string, unknown>>;
  };
  compaction?: Record<string, string | boolean>;
  forget_delete?: Record<string, string | boolean>;
  safety?: Record<string, boolean>;
  source_endpoints?: string[];
  source_status?: Record<string, unknown>;
  preview_only?: boolean;
  read_only?: boolean;
}

export interface JarvisPersistentAudit {
  schema_version?: string;
  state?: Record<string, string | boolean | number | null>;
  chain?: {
    valid?: boolean;
    checked_count?: number | string;
    first_invalid_audit_id?: string | null;
    first_invalid_reason?: string | null;
    last_entry_hash?: string | null;
  };
  supported_event_types?: string[];
  recent_entries?: Array<Record<string, unknown>>;
  retention?: Record<string, string | boolean>;
  safety?: Record<string, boolean>;
  source_endpoint?: string;
  read_only?: boolean;
}

export interface JarvisLocalDoctorCheck {
  name: string;
  status: string;
  evidence?: string;
  detail?: string;
  read_only?: boolean;
  metadata_only?: boolean;
}

export interface JarvisLocalDoctor {
  schema_version?: string;
  state?: Record<string, string | boolean | number>;
  checks?: JarvisLocalDoctorCheck[];
  optional_dependencies?: Record<string, { available?: boolean; source?: string; status?: string; version?: string }>;
  runtime?: Record<string, unknown>;
  storage?: Record<string, unknown>;
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
  governed_execution?: JarvisGovernedExecutionStatus;
  phase_1_completion?: JarvisPhase1Status;
  phase_2_status?: Record<string, unknown>;
  phase_3_status?: Record<string, unknown>;
  phase_4_status?: Record<string, unknown>;
  phase_5_status?: Record<string, unknown>;
  phase_6_status?: Record<string, any>;
  phase_7_status?: Record<string, any>;
  phase_7_adapters?: Record<string, any>;
  filesystem_adapter?: Record<string, unknown>;
  github_worktree_adapter?: Record<string, unknown>;
  browser_automation?: Record<string, unknown>;
  sandbox_execution?: Record<string, unknown>;
  preflight?: Record<string, unknown>;
  action_catalog?: { actions?: JarvisActionContract[]; denied_actions?: string[]; allowlist_only?: boolean; catalog_version?: number; categories?: Record<string, number>; source_endpoint?: string };
  execution_history?: JarvisExecutionHistoryResponse;
  stop_rollback_contracts?: Record<string, unknown>;
  stop_rollback_v2?: Record<string, unknown>;
  local_runtime?: JarvisLocalRuntimeStatus;
  local_daemon?: Record<string, unknown>;
  local_controller?: Record<string, unknown>;
  tray_readiness?: Record<string, unknown>;
  trusted_approval_channels?: Record<string, unknown>;
  trusted_devices?: Record<string, unknown>;
  local_pairing?: Record<string, unknown>;
  voice_approval?: Record<string, unknown>;
  voice_provider_registry?: Record<string, any>;
  voice_session_v2?: Record<string, any>;
  wake_runtime?: Record<string, any>;
  sensor_runtime?: Record<string, any>;
  notifications?: Record<string, unknown>;
  remote_pairing?: Record<string, unknown>;
  telegram_bridge?: Record<string, unknown>;
  browser_verification?: JarvisBrowserVerificationStatus;
  conversational_brain?: JarvisConversationalBrain;
  conversational_intake?: JarvisConversationalIntake;
  brain_adapter?: JarvisBrainAdapter;
  voice_session?: JarvisVoiceSession;
  wake_architecture?: Record<string, unknown>;
  voice_runtime_pack?: JarvisVoiceRuntimePack;
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
  persistent_audit?: JarvisPersistentAudit;
  sensor_ledger?: JarvisSensorLedger;
  event_bus?: Record<string, any>;
  policy_status?: Record<string, any>;
  memory_brain_v2?: Record<string, any>;
  memory_brain_v3?: Record<string, any>;
  memory_brain_v3_compaction?: Record<string, any>;
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
