import { useCallback, useEffect, useMemo, useState, type RefObject } from "react";
import { ShieldAlert } from "lucide-react";
import type {
  JarvisDashboardStatus,
  JarvisExecutionApprovalEnvelope,
  JarvisExecutionDispatchResult,
  JarvisExecutionPreview,
} from "@/lib/api";
import type { JarvisEvent, JarvisOrbVisualState, LocalVoiceLoopController } from "./types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DASHBOARD_READ_MODEL_ENDPOINT,
  fallbackApprovalCards,
  fallbackDashboard,
  previewVoiceSubtitle,
  visualQaPreviewStates,
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

function readInitialVisualQaPreviewState(): JarvisOrbVisualState | null {
  if (typeof window === "undefined") return null;
  const raw = new URLSearchParams(window.location.search).get("jarvisVisualPreview");
  if (!raw) return null;
  return visualQaPreviewStates.some(([state]) => state === raw) ? (raw as JarvisOrbVisualState) : null;
}

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
  executionPreview?: JarvisExecutionPreview | null;
  executionApprovalEnvelope?: JarvisExecutionApprovalEnvelope | null;
  executionDispatchResult?: JarvisExecutionDispatchResult | null;
  executionBusy?: boolean;
  executionError?: string;
  onCreateExecutionPreview?: (payload: { intent: string; targetPath?: string }) => void;
  onRequestExecutionApproval?: () => void;
  onApproveExecution?: (payload: { confirmationPhrase?: string; readbackText?: string }) => void;
  onRejectExecution?: (reason?: string) => void;
  onCancelExecution?: (reason?: string) => void;
  onStopExecution?: (reason?: string) => void;
  onClarifyExecution?: (reason?: string) => void;
  onDispatchExecution?: () => void;
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
  executionPreview,
  executionApprovalEnvelope,
  executionDispatchResult,
  executionBusy,
  executionError,
  onCreateExecutionPreview,
  onRequestExecutionApproval,
  onApproveExecution,
  onRejectExecution,
  onCancelExecution,
  onStopExecution,
  onClarifyExecution,
  onDispatchExecution,
}: JarvisPresenceShellProps) {
  const fallbackOffline = useMemo(() => fallbackDashboard("offline"), []);
  const [smartBarTextPulse, setSmartBarTextPulse] = useState(false);
  const [smartBarTextSignal, setSmartBarTextSignal] = useState("");
  const [visualQaPreviewState, setVisualQaPreviewState] = useState<JarvisOrbVisualState | null>(() => readInitialVisualQaPreviewState());
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
  const governedExecution = dashboard.governed_execution;
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
  const handleSmartBarDraftActivity = useCallback((draft: string) => {
    setSmartBarTextSignal(draft);
    setSmartBarTextPulse(draft.trim().length > 0);
  }, []);
  useEffect(() => {
    if (!smartBarTextPulse) return;
    const timeout = window.setTimeout(() => setSmartBarTextPulse(false), 2400);
    return () => window.clearTimeout(timeout);
  }, [smartBarTextPulse, smartBarTextSignal]);
  const textReactive =
    smartBarTextPulse ||
    Boolean(localVoice.interimTranscript.trim() || localVoice.transcript.trim() || localVoice.localVoiceResponse.trim());
  const orbVisualState: JarvisOrbVisualState =
    valueText(system.kill_switch_state, "not_wired") === "active"
      ? "stopped"
      : localVoice.localVoiceState === "cancelled" || localVoice.localVoiceState === "stopped"
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
  const resolvedOrbVisualState = visualQaPreviewState ?? orbVisualState;

  return (
    <div
      className="fixed inset-x-0 bottom-0 top-12 z-30 h-[calc(100dvh-3rem)] overflow-hidden bg-[#00030a] text-cyan-50"
      data-testid="jarvis-command-center-page"
      data-presence-layout="cinematic-orb-first"
      data-visual-direction="dark-background-distinct-blue-white-core-clean-side-rails"
      data-visual-qa-preview-mode={visualQaPreviewState ? "forced-local-preview" : "auto"}
      data-visual-qa-preview-state={visualQaPreviewState ?? "auto"}
      data-visual-qa-no-hermes="true"
      data-visual-qa-no-sensors="true"
      data-visual-qa-approval="backend-gated"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_46%,rgba(6,182,212,0.105),transparent_35%),radial-gradient(circle_at_68%_48%,rgba(248,113,113,0.045),transparent_24%),radial-gradient(circle_at_35%_75%,rgba(250,204,21,0.025),transparent_29%),linear-gradient(180deg,rgba(0,3,10,0.08),rgba(0,3,10,0.98))]" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(90deg,rgba(103,232,249,0.016)_1px,transparent_1px),linear-gradient(0deg,rgba(125,211,252,0.012)_1px,transparent_1px)] bg-[length:128px_128px]" />
      <div className="pointer-events-none absolute inset-x-0 top-[4.2rem] h-px bg-cyan-300/22 shadow-[0_0_18px_rgba(34,211,238,0.34)]" />

      <header
        data-testid="jarvis-command-center-header"
        className="absolute inset-x-0 top-0 z-40 h-[4.25rem] border-b border-cyan-100/12 bg-[#00030a]/76 backdrop-blur-xl"
      >
        <div className="grid h-full grid-cols-[1fr_auto_1fr] items-center px-5 2xl:px-7">
          <div className="flex min-w-0 items-center gap-3">
            <span className="h-2 w-2 rounded-full bg-[#e6fbff] shadow-[0_0_18px_rgba(230,251,255,0.82)]" />
            <div className="min-w-0">
              <p className="font-display text-[0.62rem] uppercase tracking-[0.18em] text-cyan-200/50">local presence</p>
              <p className="truncate font-mono-ui text-xs text-cyan-50/72">
                {connectionState === "online" ? "JARVIS operativo" : "JARVIS en fallback local"}
              </p>
            </div>
          </div>

          <div className="text-center">
            <p className="font-expanded text-2xl font-bold uppercase tracking-[0.34em] text-[#e6fbff] blend-lighter drop-shadow-[0_0_22px_rgba(230,251,255,0.76)]">JARVIS</p>
            <p className="mt-0.5 font-display text-[0.62rem] uppercase tracking-[0.24em] text-cyan-100/46">presence chamber</p>
            <span className="sr-only">Centro de Mando JARVIS</span>
            <span className="sr-only">JARVIS Presence UI + Local System Contract</span>
            <span className="sr-only">Visual Command Center GET {DASHBOARD_READ_MODEL_ENDPOINT}</span>
          </div>

          <div className="flex min-w-0 items-center justify-end gap-2">
            <Badge className="hidden border-cyan-100/14 bg-[#000711]/66 text-cyan-100/60 sm:inline-flex" variant="outline">
              {eventConnectionState}
            </Badge>
            <Badge className={approvalsPending ? "border-amber-300/40 bg-amber-400/12 text-amber-100" : "border-cyan-100/14 bg-[#000711]/66 text-cyan-100/60"} variant="outline">
              {approvalsPending ? "approval required" : "backend-gated"}
            </Badge>
            <Button disabled aria-disabled="true" type="button" variant="destructive" size="sm" className="h-8 border-red-300/34 bg-red-950/28 px-3 text-red-100" data-testid="jarvis-header-kill-switch">
              <ShieldAlert className="h-3.5 w-3.5" />
              KILL SWITCH
            </Button>
            <span className="sr-only">Kill Switch {valueText(system.kill_switch_state, "not_wired")}</span>
            <span className="sr-only">brain {brainProvider} · ext {externalBrainCalled ? "true" : "false"} · risk {intakeRisk} · modo approval backend-gated</span>
            <span className="sr-only">POST solo a endpoints gobernados de execution. No execute. No sensores sin activación manual. No fake metrics.</span>
            <span className="sr-only">JARVIS gobierna. Hermes ejecuta solo por dispatch gobernado. El frontend no llama Hermes directo.</span>
          </div>
        </div>
      </header>

      <section
        data-testid="jarvis-cockpit-layout"
        className="absolute inset-x-0 bottom-[8.7rem] top-[4.25rem] z-10 grid min-h-0 gap-3 px-4 py-3 lg:grid-cols-[minmax(150px,12vw)_minmax(0,1fr)] xl:grid-cols-[minmax(170px,12vw)_minmax(0,1fr)_minmax(266px,17vw)] 2xl:px-7"
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
          visualState={resolvedOrbVisualState}
          jarvisTone={localVoice.jarvisTone}
          conversationActive={localVoice.conversationActive}
          killSwitchState={valueText(system.kill_switch_state, "not_wired")}
          textReactive={textReactive}
          textSignal={smartBarTextSignal || localVoice.interimTranscript || localVoice.transcript || localVoice.localVoiceResponse}
          visualQaPreviewState={visualQaPreviewState}
        />

        <aside className="hidden min-h-0 content-start gap-3 overflow-auto pr-1 xl:grid" data-testid="jarvis-contextual-side-panel" data-side-panel-style="premium-quiet-not-dashboard">
          <JarvisApprovalPanel
            cards={approvalCards}
            pendingCount={approvals.pending_count}
            executionStatus={governedExecution}
            activePreview={executionPreview}
            activeEnvelope={executionApprovalEnvelope}
            dispatchResult={executionDispatchResult}
            busy={executionBusy}
            error={executionError}
            onCreatePreview={onCreateExecutionPreview}
            onRequestApproval={onRequestExecutionApproval}
            onApprove={onApproveExecution}
            onReject={onRejectExecution}
            onCancel={onCancelExecution}
            onStop={onStopExecution}
            onClarify={onClarifyExecution}
            onDispatch={onDispatchExecution}
          />
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
          <details className="border border-cyan-100/10 bg-[#000711]/52 p-3 backdrop-blur" data-testid="jarvis-finance-summary">
            <summary className="cursor-pointer font-expanded text-xs font-bold uppercase tracking-[0.12em] text-cyan-100/58">Finance / ROI</summary>
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
        canInterrupt={localVoice.canInterrupt}
        canCancel={localVoice.canCancel}
        onBegin={localVoice.beginLocalVoiceLoop}
        onCancel={localVoice.cancelLocalVoiceLoop}
        onDraftActivity={handleSmartBarDraftActivity}
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
        visualPreviewState={visualQaPreviewState}
        resolvedVisualState={resolvedOrbVisualState}
        onVisualPreviewStateChange={setVisualQaPreviewState}
      />
    </div>
  );
}
