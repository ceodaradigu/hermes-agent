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
}: {
  system: NonNullable<JarvisDashboardStatus["system"]>;
  approvals: NonNullable<JarvisDashboardStatus["approvals"]>;
  activeRisk: string;
  voiceState: string;
  cameraEnabled: boolean;
  localSystemContract: NonNullable<JarvisDashboardStatus["local_system_contract"]>;
}) {
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

  return (
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
          <SafetyLine>voz local, cámara preview y grabación local disponibles solo con botón explícito.</SafetyLine>
          <SafetyLine>Hermes directo: {yesNo(localSystemContract.frontend_executes_hermes_directly, "unexpected", "false")}</SafetyLine>
        </div>
        <div className="mt-3">
          <StatusList items={localContractRows} />
        </div>
        <Badge className="mt-3 border-cyan-300/25 bg-cyan-300/10 text-cyan-100" variant="outline">
          JARVIS Presence UI + Local System Contract
        </Badge>
      </details>
    </aside>
  );
}
