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
  type JarvisDashboardModule,
  type JarvisDashboardStatus,
  type JarvisHermesBlockedRoute,
  type JarvisHermesGovernedCapability,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const DASHBOARD_READ_MODEL_ENDPOINT = "/mark-3/dashboard/status";
const UNKNOWN = "unknown";

const voiceStates = [
  "offline",
  "online",
  "preview",
  "listening_wake_word",
  "listening_command",
  "thinking",
  "speaking",
  "approval_required",
  "hermes_executing",
  "paused",
  "blocked",
  "kill_switch",
] as const;

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

const fallbackStages = [
  "Idea",
  "Validación",
  "Blueprint",
  "Código",
  "Landing",
  "Deploy candidate",
  "Monetización",
] as const;

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
    voice_wake: {
      microphone_state: "disabled",
      wake_word_state: "unknown",
      wake_phrases: ["Hola Jarvis", "Jarvis"],
      wake_phrase_can_approve: false,
      audio_recording: false,
    },
    camera_vision: {
      camera_state: "disabled",
      preview_state: "disabled",
      recording: false,
      vision_analysis: "disabled",
      storage: false,
    },
    mobile: {
      companion_state: "not_connected",
      direct_hermes_call_allowed: false,
      remote_kill_switch_state: "future_gated",
      approval_actions_enabled: false,
    },
    finance: {
      actual_cost: UNKNOWN,
      estimated_cost: UNKNOWN,
      confirmed_revenue: UNKNOWN,
      projected_revenue: UNKNOWN,
      roi: UNKNOWN,
      no_fake_metrics: true,
    },
    product_builder: {
      stages: [...fallbackStages],
      deploy_requires_strong_approval: true,
      stripe_checkout_requires_strong_approval: true,
      real_revenue_must_be_confirmed: true,
    },
    safety: {
      frontend_can_execute: false,
      frontend_can_approve: false,
      no_duplicate_hermes_runtime: true,
      no_get_user_media: true,
      no_sensor_activation: true,
      no_frontend_tool_runner: true,
      no_frontend_hermes_execution: true,
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
  if (status === "gated" || status === "prepare-only" || status === "preview") return "warning";
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
  const release = dashboard.release_candidate ?? {};
  const approvals = dashboard.approvals ?? {};
  const approvalCards = approvals.cards?.length ? approvals.cards : fallbackApprovalCards;
  const hermes = dashboard.hermes_execution ?? {};
  const hermesContract = hermes.contract ?? contract;
  const hermesRuntime = hermes.runtime_status ?? hermes;
  const hermesCapabilities = readHermesCapabilities(hermes.governed_capabilities);
  const hermesBlockedRoutes = readHermesBlockedRoutes(hermes.blocked_routes);
  const voiceWake = dashboard.voice_wake ?? {};
  const cameraVision = dashboard.camera_vision ?? {};
  const mobile = dashboard.mobile ?? {};
  const finance = dashboard.finance ?? {};
  const productBuilder = dashboard.product_builder ?? {};
  const timeline = dashboard.timeline?.length ? dashboard.timeline : fallbackDashboard("error").timeline ?? [];
  const stages = productBuilder.stages?.length ? productBuilder.stages : [...fallbackStages];
  const readiness = release.readiness ?? {};

  const missionFields = [
    ["intención detectada", UNKNOWN],
    ["plan", valueText(readiness.mission_loop)],
    ["riesgo", "risk_scaled/unknown"],
    ["permisos necesarios", "none/unknown"],
    ["estado", valueText(release.status)],
  ] as const;

  const privacyRows = [
    ["cámara", valueText(cameraVision.camera_state)],
    ["preview", valueText(cameraVision.preview_state)],
    ["recording", yesNo(cameraVision.recording, "on", "off")],
    ["vision analysis", valueText(cameraVision.vision_analysis)],
    ["storage", yesNo(cameraVision.storage, "on", "off")],
    ["scope", "none"],
  ] as const;

  const mobileRows = [
    ["mobile companion", valueText(mobile.companion_state)],
    ["approvals desde móvil", yesNo(mobile.approval_actions_enabled, "enabled", "future gated")],
    ["estado remoto", UNKNOWN],
    ["kill switch remoto", valueText(mobile.remote_kill_switch_state)],
    ["Hermes directo desde móvil", yesNo(mobile.direct_hermes_call_allowed, "allowed", "forbidden")],
  ] as const;

  const financeRows = [
    ["coste real", valueText(finance.actual_cost)],
    ["coste estimado", valueText(finance.estimated_cost)],
    ["revenue confirmado", valueText(finance.confirmed_revenue)],
    ["revenue proyectado", valueText(finance.projected_revenue)],
    ["ROI", valueText(finance.roi)],
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

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-warning" />
              <CardTitle>Núcleo / Voice Core visual</CardTitle>
            </div>
            <CardDescription>Estado seguro actual leído desde el read model; fallback a unknown/offline.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-[260px_1fr]">
            <div className="relative flex min-h-[260px] items-center justify-center border border-border/70 bg-background/40">
              <div className="absolute inset-6 border border-warning/20" />
              <div className="absolute inset-12 border border-emerald-400/20" />
              <div className="flex h-32 w-32 items-center justify-center border border-warning/80 bg-warning/10">
                <MicOff className="h-11 w-11 text-warning" />
              </div>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {voiceStates.map((state) => (
                  <Badge key={state} variant={state === voiceWake.wake_word_state ? "warning" : "outline"}>
                    {state}
                  </Badge>
                ))}
              </div>
              <div className="grid gap-2 sm:grid-cols-3">
                <div className="border border-border/70 p-3">
                  <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">micrófono real</p>
                  <p className="mt-1 font-mono-ui text-sm">{valueText(voiceWake.microphone_state)}</p>
                </div>
                <div className="border border-border/70 p-3">
                  <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">wake word real</p>
                  <p className="mt-1 font-mono-ui text-sm">{valueText(voiceWake.wake_word_state)}</p>
                </div>
                <div className="border border-border/70 p-3">
                  <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">wake phrases</p>
                  <p className="mt-1 font-mono-ui text-sm">{voiceWake.wake_phrases?.join(", ") || "Hola Jarvis, Jarvis"}</p>
                </div>
              </div>
              <SafetyLine>La wake phrase nunca aprueba acciones.</SafetyLine>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Workflow className="h-5 w-5 text-success" />
              <CardTitle>Mission Control</CardTitle>
            </div>
            <CardDescription>Panel visual para futuras misiones; no crea misiones reales desde frontend.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <textarea
              disabled
              className="min-h-28 w-full resize-none border border-border bg-background/50 p-3 font-mono-ui text-xs text-muted-foreground disabled:opacity-70"
              value={`Entrada preview deshabilitada. Estado RC: ${valueText(release.status)}.`}
              readOnly
            />
            <StatusList items={missionFields} />
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

      <div className="grid gap-6 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Camera className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Camera / Vision Privacy</CardTitle>
            </div>
            <CardDescription>Cámara real apagada; sin permisos del navegador.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatusList items={privacyRows} />
            <SafetyLine>La cámara no graba por defecto.</SafetyLine>
            <SafetyLine>La visión solo se activa con permiso explícito.</SafetyLine>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Smartphone className="h-5 w-5 text-success" />
              <CardTitle>Mobile Companion</CardTitle>
            </div>
            <CardDescription>Superficie futura, no runtime remoto.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatusList items={mobileRows} />
            <SafetyLine>Mobile es una interfaz, no un runtime.</SafetyLine>
            <SafetyLine>Mobile no llama a Hermes directamente.</SafetyLine>
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
            <StatusList items={financeRows} />
            <SafetyLine>No fake metrics.</SafetyLine>
            <SafetyLine>Si no hay evidencia, mostrar unknown.</SafetyLine>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_0.85fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-success" />
              <CardTitle>Product Builder Adaptativo</CardTitle>
            </div>
            <CardDescription>Flujo visual de producto; sin deploy, Stripe ni revenue real.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2 md:grid-cols-7">
              {stages.map((step) => (
                <div key={step} className="border border-border/70 bg-background/35 p-3 text-center">
                  <p className="font-display text-xs uppercase tracking-[0.1em]">{step}</p>
                  <Badge variant="outline" className="mt-2">preview</Badge>
                </div>
              ))}
            </div>
            <div className="grid gap-2 lg:grid-cols-3">
              <SafetyLine>Deploy real requiere approval fuerte.</SafetyLine>
              <SafetyLine>Stripe/checkout real requiere approval fuerte.</SafetyLine>
              <SafetyLine>Revenue real no se inventa.</SafetyLine>
            </div>
          </CardContent>
        </Card>

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
