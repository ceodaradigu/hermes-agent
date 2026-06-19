import { Activity, Lock } from "lucide-react";
import type { JarvisDashboardStatus } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { SafetyLine, StatusList } from "./JarvisPanels";
import { UNKNOWN } from "./contracts";
import { valueText, yesNo } from "./utils";

export function JarvisSideRail({
  system,
  approvals,
  activeRisk,
  voiceState,
  cameraEnabled,
  localSystemContract,
  phase6Status,
  voiceProviderRegistry,
  voiceSessionV2,
  wakeRuntime,
  sensorRuntime,
  memoryBrainV3,
}: {
  system: NonNullable<JarvisDashboardStatus["system"]>;
  approvals: NonNullable<JarvisDashboardStatus["approvals"]>;
  activeRisk: string;
  voiceState: string;
  cameraEnabled: boolean;
  localSystemContract: NonNullable<JarvisDashboardStatus["local_system_contract"]>;
  phase6Status?: Record<string, any>;
  voiceProviderRegistry?: Record<string, any>;
  voiceSessionV2?: Record<string, any>;
  wakeRuntime?: Record<string, any>;
  sensorRuntime?: Record<string, any>;
  memoryBrainV3?: Record<string, any>;
}) {
  const providerDiagnostics = voiceProviderRegistry?.diagnostics ?? {};
  const voiceSessionV2State = voiceSessionV2?.state ?? {};
  const wakeRuntimeState = wakeRuntime?.state ?? {};
  const sensorRuntimeState = sensorRuntime?.state ?? {};
  const memoryBrainV3State = memoryBrainV3?.state ?? {};
  const essentialRows = [
    ["estado general", valueText(system.api_status, UNKNOWN)],
    ["approvals pendientes", valueText(approvals.pending_count)],
    ["escucha/piensa/habla", voiceState],
    ["coste/dinero", "unknown"],
    ["cámara activa", cameraEnabled ? "sí" : "no"],
    ["riesgo actual", activeRisk],
  ] as const;

  const localContractRows = [
    ["runtime", localSystemContract.local_runtime_daemon_is_system ? "local daemon is system" : UNKNOWN],
    ["web", localSystemContract.web_route_is_visual_interface_only ? "/jarvis visual interface only" : UNKNOWN],
    ["mobile/VPS", localSystemContract.mobile_and_vps_are_future_clients_or_bridges ? "future clients/bridges" : UNKNOWN],
    ["Hermes direct", localSystemContract.frontend_executes_hermes_directly ? "unexpected allowed" : "false"],
    ["voice", localSystemContract.real_browser_voice_loop_in_this_pr ? "local loop manual" : UNKNOWN],
    ["camera", localSystemContract.frontend_can_activate_real_camera ? "preview local manual" : UNKNOWN],
  ] as const;

  const phase6Rows = [
    ["fase", valueText(phase6Status?.status, UNKNOWN)],
    ["providers ready", valueText(providerDiagnostics.ready_provider_count, "0")],
    ["session v2", valueText(voiceSessionV2State.current_state, "idle")],
    ["wake opt-in", yesNo(wakeRuntimeState.enabled, "on", "off")],
    ["sensors active", valueText(sensorRuntimeState.active_sensor_count, "0")],
    ["memory v3", valueText(memoryBrainV3State.mode, UNKNOWN)],
  ] as const;

  return (
    <aside className="hidden min-h-0 content-center gap-4 lg:grid" data-testid="jarvis-quiet-side-rail">
      <article className="relative border-l border-cyan-100/12 bg-gradient-to-r from-[#000711]/58 to-transparent py-2 pl-4 pr-1" data-testid="jarvis-essential-status" data-panel-style="premium-minimal-presence">
        <div className="mb-4 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-full border border-[#e6fbff]/18 bg-[#e6fbff]/[0.045] shadow-[0_0_30px_rgba(230,251,255,0.11)]">
            <Activity className="h-5 w-5 text-[#e6fbff]/78" />
          </div>
          <div>
            <p className="font-display text-[0.68rem] uppercase tracking-[0.18em] text-cyan-100/48">Estado general</p>
            <p className="font-expanded text-lg font-bold uppercase tracking-[0.08em] text-[#e6fbff]/88">
              {valueText(system.api_status, UNKNOWN) === "offline" ? "fallback" : "presente"}
            </p>
          </div>
        </div>
        <div className="grid gap-2">
          <div>
            <p className="font-display text-[0.62rem] uppercase tracking-[0.16em] text-cyan-200/48">JARVIS ahora</p>
            <p className="font-mono-ui text-xs text-cyan-50/70">{voiceState}</p>
          </div>
          <div>
            <p className="font-display text-[0.62rem] uppercase tracking-[0.16em] text-cyan-200/48">Puede hacer</p>
            <p className="font-mono-ui text-xs text-cyan-50/70">responder, preparar preview, pedir approval</p>
          </div>
          <div>
            <p className="font-display text-[0.62rem] uppercase tracking-[0.16em] text-cyan-200/48">Gates</p>
            <p className="font-mono-ui text-xs text-cyan-50/70">Hermes gated · wake no aprueba · sensores opt-in</p>
          </div>
        </div>
        <details className="mt-4 border-t border-cyan-100/10 pt-3">
          <summary className="cursor-pointer font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-100/54">estado técnico plegado</summary>
          <div className="mt-3">
            <StatusList items={essentialRows} />
          </div>
        </details>
        <div className="mt-4 grid gap-2">
          <SafetyLine>JARVIS gobierna. Hermes ejecuta.</SafetyLine>
          <SafetyLine>El dashboard mira, no toca.</SafetyLine>
        </div>
      </article>

      <details className="border border-cyan-100/10 bg-[#000711]/44 p-3 backdrop-blur" data-testid="jarvis-phase-6-runtime">
        <summary className="cursor-pointer font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-100/54">Phase 6 runtime</summary>
        <div className="mt-3">
          <StatusList items={phase6Rows} />
        </div>
        <div className="mt-3 grid gap-2">
          <SafetyLine>Providers report readiness honestly.</SafetyLine>
          <SafetyLine>Wake starts sessions; wake never approves.</SafetyLine>
          <SafetyLine>Memory never grants permission.</SafetyLine>
        </div>
      </details>

      <details className="border border-cyan-100/10 bg-[#000711]/48 p-3 backdrop-blur" data-testid="jarvis-local-system-contract" data-panel-style="contract-folded-premium">
        <summary className="flex cursor-pointer items-center gap-2 font-expanded text-xs font-bold uppercase tracking-[0.16em] text-cyan-100/76">
          <Lock className="h-4 w-4 text-[#e6fbff]/70" />
          Local System Contract
        </summary>
        <div className="grid gap-2">
          <SafetyLine>JARVIS runtime/daemon local es el sistema.</SafetyLine>
          <SafetyLine>/jarvis es solo la interfaz visual.</SafetyLine>
          <SafetyLine>móvil y VPS serán clientes/puentes futuros.</SafetyLine>
          <SafetyLine>frontend no ejecuta directamente Hermes.</SafetyLine>
          <SafetyLine>voz local, cámara preview y grabación local disponibles solo con botón explícito.</SafetyLine>
          <SafetyLine>Hermes directo: {yesNo(localSystemContract.frontend_executes_hermes_directly, "unexpected", "false")}</SafetyLine>
        </div>
        <div className="mt-3">
          <StatusList items={localContractRows} />
        </div>
        <Badge className="mt-3 border-cyan-100/18 bg-[#e6fbff]/[0.045] text-cyan-100/72" variant="outline">
          JARVIS Presence UI + Local System Contract
        </Badge>
      </details>
    </aside>
  );
}
