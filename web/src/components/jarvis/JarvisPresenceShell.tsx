import { useMemo, type RefObject } from "react";
import { ShieldAlert } from "lucide-react";
import type { JarvisDashboardStatus } from "@/lib/api";
import type { JarvisEvent, JarvisOrbVisualState, LocalVoiceLoopController } from "./types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DASHBOARD_READ_MODEL_ENDPOINT,
  fallbackApprovalCards,
  fallbackDashboard,
  previewVoiceSubtitle,
  type CommandCenterTabId,
} from "./contracts";
import { JarvisApprovalPanel } from "./JarvisApprovalPanel";
import { JarvisCameraPanel } from "./JarvisCameraPanel";
import { JarvisDebugDrawer } from "./JarvisDebugDrawer";
import { JarvisOrb3D } from "./JarvisOrb3D";
import { JarvisRecordingPanel } from "./JarvisRecordingPanel";
import { JarvisSideRail } from "./JarvisSideRail";
import { JarvisSmartBar } from "./JarvisSmartBar";
import { capabilityText, metricValue, readModules, valueText } from "./utils";
import type { JarvisCameraAuditEvent, JarvisCameraState } from "@/hooks/jarvis/useJarvisCameraControl";
import type { JarvisLocalVideoRecording, JarvisVideoRecordingState } from "@/hooks/jarvis/useJarvisCameraControl";
import type { JarvisLocalRecording, JarvisRecordingAuditEvent, JarvisRecordingState } from "@/hooks/jarvis/useJarvisAudioRecorder";

interface JarvisPresenceShellProps {
  dashboard: JarvisDashboardStatus;
  connectionState: "loading" | "online" | "offline";
  activeTab: CommandCenterTabId;
  onTabChange: (tab: CommandCenterTabId) => void;
  localVoice: LocalVoiceLoopController;
  cameraControl: {
    videoRef: RefObject<HTMLVideoElement | null>;
    cameraState: JarvisCameraState;
    cameraError: string;
    cameraActive: boolean;
    cameraAuditEvents: JarvisCameraAuditEvent[];
    videoRecordingState: JarvisVideoRecordingState;
    videoRecordingError: string;
    videoRecording: JarvisLocalVideoRecording | null;
    videoRecordingActive: boolean;
    startCameraPreview: () => void;
    stopCameraPreview: () => void;
    startVideoRecording: () => void;
    stopVideoRecording: () => void;
    deleteVideoRecording: () => void;
  };
  audioRecorder: {
    recordingState: JarvisRecordingState;
    recordingError: string;
    recording: JarvisLocalRecording | null;
    recordingActive: boolean;
    recordingAuditEvents: JarvisRecordingAuditEvent[];
    startRecording: () => void;
    stopRecording: () => void;
    deleteRecording: () => void;
  };
  events: JarvisEvent[];
  eventConnectionState: string;
}

export function JarvisPresenceShell({
  dashboard,
  connectionState,
  activeTab,
  onTabChange,
  localVoice,
  cameraControl,
  audioRecorder,
  events,
  eventConnectionState,
}: JarvisPresenceShellProps) {
  const fallbackOffline = useMemo(() => fallbackDashboard("offline"), []);
  const modules = useMemo(() => readModules(dashboard.modules), [dashboard.modules]);
  const system = dashboard.system ?? fallbackOffline.system ?? {};
  const localSystemContract = dashboard.local_system_contract ?? fallbackOffline.local_system_contract!;
  const approvals = dashboard.approvals ?? fallbackOffline.approvals ?? {};
  const approvalCards = approvals.cards?.length ? approvals.cards : fallbackApprovalCards;
  const missionControl = dashboard.mission_control ?? fallbackOffline.mission_control!;
  const missionIntent = missionControl.intent_preview ?? {};
  const conversationalIntake = dashboard.conversational_intake ?? fallbackOffline.conversational_intake!;
  const brainAdapter = dashboard.brain_adapter ?? fallbackOffline.brain_adapter!;
  const hermes = dashboard.hermes_execution ?? {};
  const hermesRuntime = hermes.runtime_status ?? hermes;
  const voiceCore = dashboard.voice_core ?? fallbackOffline.voice_core!;
  const voiceSession = dashboard.voice_session ?? fallbackOffline.voice_session;
  const wakeWordFlow = dashboard.wake_word_flow ?? fallbackOffline.wake_word_flow;
  const voiceCoreState = voiceCore.state ?? {};
  const ttsState = voiceCore.tts_state ?? {};
  const cameraVision = dashboard.camera_vision ?? fallbackOffline.camera_vision!;
  const cameraVisionState = cameraVision.state ?? {};
  const financeRoi = dashboard.finance_roi ?? fallbackOffline.finance_roi!;
  const financeMetrics = financeRoi.metrics ?? {};
  const localVoiceMicActive = localVoice.localVoiceState === "listening" || localVoice.localVoiceState === "transcribing";
  const localCameraActive = cameraControl.cameraActive;
  const localRecordingActive = audioRecorder.recordingActive;
  const sensorsDisabled =
    !localVoiceMicActive &&
    !voiceCoreState.microphone_enabled &&
    !cameraVisionState.camera_enabled &&
    !localCameraActive &&
    !localRecordingActive;
  const activeRisk = valueText(missionIntent.risk_level, cameraVisionState.camera_enabled || localCameraActive || localRecordingActive ? "sensor_privacy" : "none/unknown");
  const readModelVoiceState = valueText(voiceCoreState.current_state, "preview");
  const voiceState = localVoice.localVoiceState === "idle" ? readModelVoiceState : localVoice.localVoiceState;
  const coreSubtitle = localVoice.localVoiceResponse || valueText(ttsState.preview_subtitle || ttsState.last_utterance, previewVoiceSubtitle);
  const brainProvider = valueText(brainAdapter.state?.current_provider, "deterministic_local");
  const externalBrainCalled = brainAdapter.state?.external_provider_called === true;
  const intakeRisk = valueText(conversationalIntake.sample?.classification?.risk_level, "unknown");
  const latestWakeEvent = events.find((event) => event.event_type === "wake_state");
  const approvalsPending = typeof approvals.pending_count === "number" ? approvals.pending_count > 0 : false;
  const orbVisualState: JarvisOrbVisualState =
    valueText(system.kill_switch_state, "not_wired") === "active"
      ? "stopped"
      : localVoice.localVoiceState === "error" || localVoice.localVoiceState === "not_supported" || localVoice.localVoiceState === "unavailable"
        ? "error"
        : hermesRuntime.active_execution === true
          ? "executing"
          : localVoice.localVoiceState === "listening" ||
              localVoice.localVoiceState === "transcribing" ||
              localVoice.localVoiceState === "thinking" ||
              localVoice.localVoiceState === "speaking"
            ? localVoice.localVoiceState
            : latestWakeEvent?.payload?.wake_runtime_enabled === true
              ? "wake_listening"
              : approvalsPending
                ? "approval_required"
                : "idle";

  return (
    <div
      className="fixed inset-x-0 bottom-0 top-12 z-30 h-[calc(100dvh-3rem)] overflow-hidden bg-[#01050d] text-cyan-50"
      data-testid="jarvis-command-center-page"
      data-presence-layout="cinematic-orb-first"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_42%,rgba(34,211,238,0.24),transparent_42%),radial-gradient(circle_at_68%_46%,rgba(248,113,113,0.10),transparent_28%),radial-gradient(circle_at_34%_74%,rgba(250,204,21,0.08),transparent_32%),linear-gradient(180deg,rgba(1,5,13,0.22),rgba(1,5,13,0.96))]" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(90deg,rgba(34,211,238,0.030)_1px,transparent_1px),linear-gradient(0deg,rgba(34,211,238,0.020)_1px,transparent_1px)] bg-[length:112px_112px]" />
      <div className="pointer-events-none absolute inset-x-0 top-[4.2rem] h-px bg-cyan-300/46 shadow-[0_0_26px_rgba(34,211,238,0.76)]" />

      <header
        data-testid="jarvis-command-center-header"
        className="absolute inset-x-0 top-0 z-40 h-[4.25rem] border-b border-cyan-300/20 bg-[#01050d]/64 backdrop-blur-xl"
      >
        <div className="grid h-full grid-cols-[1fr_auto_1fr] items-center px-5 2xl:px-7">
          <div className="flex min-w-0 items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-cyan-200 shadow-[0_0_18px_rgba(125,211,252,0.9)]" />
            <div className="min-w-0">
              <p className="font-display text-[0.62rem] uppercase tracking-[0.18em] text-cyan-200/50">local presence</p>
              <p className="truncate font-mono-ui text-xs text-cyan-50/72">
                {connectionState === "online" ? "JARVIS operativo" : "JARVIS en fallback local"}
              </p>
            </div>
          </div>

          <div className="text-center">
            <p className="font-expanded text-2xl font-bold uppercase tracking-[0.34em] text-cyan-200 blend-lighter drop-shadow-[0_0_20px_rgba(34,211,238,0.82)]">JARVIS</p>
            <p className="mt-0.5 font-display text-[0.62rem] uppercase tracking-[0.24em] text-cyan-100/58">presence chamber</p>
            <span className="sr-only">Centro de Mando JARVIS</span>
            <span className="sr-only">JARVIS Presence UI + Local System Contract</span>
            <span className="sr-only">Visual Command Center GET {DASHBOARD_READ_MODEL_ENDPOINT}</span>
          </div>

          <div className="flex min-w-0 items-center justify-end gap-2">
            <Badge className="hidden border-cyan-300/22 bg-[#061526]/64 text-cyan-100/70 sm:inline-flex" variant="outline">
              {eventConnectionState}
            </Badge>
            <Badge className={approvalsPending ? "border-amber-300/40 bg-amber-400/12 text-amber-100" : "border-cyan-300/22 bg-[#061526]/64 text-cyan-100/70"} variant="outline">
              {approvalsPending ? "approval required" : "read-only"}
            </Badge>
            <Button disabled aria-disabled="true" type="button" variant="destructive" size="sm" className="h-8 border-red-400/40 bg-red-950/35 px-3 text-red-100" data-testid="jarvis-header-kill-switch">
              <ShieldAlert className="h-3.5 w-3.5" />
              KILL SWITCH
            </Button>
            <span className="sr-only">Kill Switch {valueText(system.kill_switch_state, "not_wired")}</span>
            <span className="sr-only">brain {brainProvider} · ext {externalBrainCalled ? "true" : "false"} · risk {intakeRisk} · modo preview/read-only · read-only</span>
            <span className="sr-only">No POST/PUT/DELETE. No execute. No sensores sin activación manual. No fake metrics.</span>
            <span className="sr-only">JARVIS gobierna. Hermes ejecuta. El dashboard mira, no toca.</span>
          </div>
        </div>
      </header>

      <section
        data-testid="jarvis-cockpit-layout"
        className="absolute inset-x-0 bottom-[8.7rem] top-[4.25rem] z-10 grid min-h-0 gap-3 px-4 py-3 lg:grid-cols-[minmax(160px,13vw)_minmax(0,1fr)] xl:grid-cols-[minmax(180px,13vw)_minmax(0,1fr)_minmax(270px,18vw)] 2xl:px-7"
      >
        <JarvisSideRail
          system={system}
          approvals={approvals}
          activeRisk={activeRisk}
          voiceState={voiceState}
          cameraEnabled={Boolean(cameraVisionState.camera_enabled) || localCameraActive}
          localSystemContract={localSystemContract}
        />

        <JarvisOrb3D
          voiceState={voiceState}
          subtitle={coreSubtitle}
          localVoiceState={localVoice.localVoiceState}
          visualState={orbVisualState}
          jarvisTone={localVoice.jarvisTone}
          conversationActive={localVoice.conversationActive}
          killSwitchState={valueText(system.kill_switch_state, "not_wired")}
        />

        <aside className="hidden min-h-0 content-start gap-3 overflow-auto pr-1 xl:grid" data-testid="jarvis-contextual-side-panel">
          <JarvisApprovalPanel cards={approvalCards} pendingCount={approvals.pending_count} />
          <JarvisCameraPanel
            cameraState={cameraControl.cameraState}
            cameraError={cameraControl.cameraError}
            cameraAuditEvents={cameraControl.cameraAuditEvents}
            cameraRisk={activeRisk}
            videoRecordingState={cameraControl.videoRecordingState}
            videoRecordingError={cameraControl.videoRecordingError}
            videoRecording={cameraControl.videoRecording}
            videoRef={cameraControl.videoRef}
            onStart={cameraControl.startCameraPreview}
            onStop={cameraControl.stopCameraPreview}
            onStartVideoRecording={cameraControl.startVideoRecording}
            onStopVideoRecording={cameraControl.stopVideoRecording}
            onDeleteVideoRecording={cameraControl.deleteVideoRecording}
          />
          <JarvisRecordingPanel
            recordingState={audioRecorder.recordingState}
            recordingError={audioRecorder.recordingError}
            recording={audioRecorder.recording}
            auditEvents={audioRecorder.recordingAuditEvents}
            onStart={audioRecorder.startRecording}
            onStop={audioRecorder.stopRecording}
            onDelete={audioRecorder.deleteRecording}
          />
          <details className="border border-cyan-300/12 bg-[#04101f]/52 p-3" data-testid="jarvis-finance-summary">
            <summary className="cursor-pointer font-expanded text-xs font-bold uppercase tracking-[0.12em] text-cyan-100/72">Finance / ROI</summary>
            <p className="mt-2 font-mono-ui text-xs text-cyan-100/50">No fake metrics. Si no hay evidencia, mostrar unknown.</p>
            <div className="mt-3 grid grid-cols-2 gap-2 font-mono-ui text-[0.7rem] text-cyan-100/65">
              <span>coste real {metricValue(financeMetrics.actual_cost)}</span>
              <span>ROI {metricValue(financeMetrics.roi)}</span>
              <span>Hermes {valueText(hermesRuntime.execution_mode, "read_only_visibility")}</span>
              <span>sensores {sensorsDisabled ? "apagados" : "revisar"}</span>
              <span>STT navegador {capabilityText(localVoice.sttSupport)}</span>
              <span>TTS navegador {capabilityText(localVoice.ttsSupport)}</span>
              <span>cámara {cameraControl.cameraState}</span>
              <span>audio bruto {audioRecorder.recordingState}</span>
            </div>
          </details>
        </aside>
      </section>

      <JarvisSmartBar
        missionControl={missionControl}
        voiceSession={voiceSession}
        wakeWordFlow={wakeWordFlow}
        localVoiceState={localVoice.localVoiceState}
        jarvisTone={localVoice.jarvisTone}
        conversationActive={localVoice.conversationActive}
        transcript={localVoice.transcript}
        interimTranscript={localVoice.interimTranscript}
        localVoiceResponse={localVoice.localVoiceResponse}
        localVoiceIntent={localVoice.localVoiceIntent}
        localVoiceRisk={localVoice.localVoiceRisk}
        intentPreview={localVoice.intentPreview}
        sttSupport={localVoice.sttSupport}
        ttsSupport={localVoice.ttsSupport}
        capabilityNotice={localVoice.capabilityNotice}
        selectedVoiceName={localVoice.selectedVoiceName}
        voiceQualityNotice={localVoice.voiceQualityNotice}
        onBegin={localVoice.beginLocalVoiceLoop}
        onCancel={localVoice.cancelLocalVoiceLoop}
      />

      <JarvisDebugDrawer
        dashboard={{ ...dashboard, modules }}
        activeTab={activeTab}
        onTabChange={onTabChange}
        events={events}
        eventConnectionState={eventConnectionState}
        connectionState={connectionState}
        conversationActive={localVoice.conversationActive}
        sttText={capabilityText(localVoice.sttSupport)}
        ttsText={capabilityText(localVoice.ttsSupport)}
        coreSubtitle={coreSubtitle}
      />
    </div>
  );
}
