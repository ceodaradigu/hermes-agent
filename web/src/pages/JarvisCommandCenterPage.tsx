import { useCallback, useEffect, useMemo, useState } from "react";
import {
  api,
  type JarvisDashboardStatus,
  type JarvisExecutionApprovalEnvelope,
  type JarvisExecutionDispatchResult,
  type JarvisExecutionPreview,
} from "@/lib/api";
import { fallbackDashboard, type CommandCenterTabId } from "@/components/jarvis/contracts";
import { JarvisPresenceShell } from "@/components/jarvis/JarvisPresenceShell";
import { useJarvisAudioRecorder } from "@/hooks/jarvis/useJarvisAudioRecorder";
import { useJarvisCameraControl } from "@/hooks/jarvis/useJarvisCameraControl";
import { useJarvisEventStream } from "@/hooks/jarvis/useJarvisEventStream";
import { useLocalVoiceLoop } from "@/hooks/jarvis/useLocalVoiceLoop";

export default function JarvisCommandCenterPage() {
  const [dashboard, setDashboard] = useState<JarvisDashboardStatus>(() => fallbackDashboard("loading"));
  const [connectionState, setConnectionState] = useState<"loading" | "online" | "offline">("loading");
  const [activeTab, setActiveTab] = useState<CommandCenterTabId>("cockpit");
  const [executionPreview, setExecutionPreview] = useState<JarvisExecutionPreview | null>(null);
  const [executionApprovalEnvelope, setExecutionApprovalEnvelope] = useState<JarvisExecutionApprovalEnvelope | null>(null);
  const [executionDispatchResult, setExecutionDispatchResult] = useState<JarvisExecutionDispatchResult | null>(null);
  const [executionBusy, setExecutionBusy] = useState(false);
  const [executionError, setExecutionError] = useState("");

  const refreshDashboard = useCallback(async () => {
    const payload = await api.getJarvisDashboardStatus();
    setDashboard(payload);
    setConnectionState("online");
    return payload;
  }, []);

  const createExecutionPreview = useCallback(async ({
    intent,
    targetPath,
    source = "typed_text",
  }: {
    intent: string;
    targetPath?: string;
    source?: string;
  }) => {
    setExecutionBusy(true);
    setExecutionError("");
    try {
      const preview = await api.createJarvisExecutionPreview({
        intent,
        source,
        operator: "David",
        target_path: targetPath || null,
      });
      setExecutionPreview(preview);
      setExecutionApprovalEnvelope(preview.approval_envelope ?? null);
      setExecutionDispatchResult(null);
      await refreshDashboard();
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : "No se pudo crear la preview gobernada.");
    } finally {
      setExecutionBusy(false);
    }
  }, [refreshDashboard]);

  const localVoice = useLocalVoiceLoop({
    onIntentSubmitted: (text) => {
      void createExecutionPreview({ intent: text, source: "voice_transcript" });
    },
  });
  const cameraControl = useJarvisCameraControl();
  const audioRecorder = useJarvisAudioRecorder();
  const localSensors = useMemo(() => ({
    camera: {
      state: cameraControl.cameraState,
      active: cameraControl.cameraActive,
      auditEvents: cameraControl.cameraAuditEvents,
      videoRecordingState: cameraControl.videoRecordingState,
      videoRecordingActive: cameraControl.videoRecordingActive,
      videoRecording: cameraControl.videoRecording,
    },
    recording: {
      state: audioRecorder.recordingState,
      active: audioRecorder.recordingActive,
      recording: audioRecorder.recording,
      auditEvents: audioRecorder.recordingAuditEvents,
    },
  }), [
    audioRecorder.recording,
    audioRecorder.recordingActive,
    audioRecorder.recordingAuditEvents,
    audioRecorder.recordingState,
    cameraControl.cameraActive,
    cameraControl.cameraAuditEvents,
    cameraControl.cameraState,
    cameraControl.videoRecording,
    cameraControl.videoRecordingActive,
    cameraControl.videoRecordingState,
  ]);
  const eventStream = useJarvisEventStream(dashboard, localSensors);

  const requestExecutionApproval = useCallback(async () => {
    if (!executionPreview) return;
    setExecutionBusy(true);
    setExecutionError("");
    try {
      const envelope = await api.requestJarvisExecutionApproval({
        preview_id: executionPreview.preview_id,
        actor: "David",
      });
      setExecutionApprovalEnvelope(envelope);
      await refreshDashboard();
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : "No se pudo pedir approval.");
    } finally {
      setExecutionBusy(false);
    }
  }, [executionPreview, refreshDashboard]);

  const decideExecutionApproval = useCallback(async ({
    decision,
    confirmationPhrase,
    readbackText,
    reason,
  }: {
    decision: "approve" | "reject" | "cancel" | "request_clarification";
    confirmationPhrase?: string;
    readbackText?: string;
    reason?: string;
  }) => {
    if (!executionApprovalEnvelope) return;
    setExecutionBusy(true);
    setExecutionError("");
    try {
      const envelope = await api.decideJarvisExecutionApproval({
        approval_id: executionApprovalEnvelope.approval_id,
        decision,
        actor: "David",
        confirmation_phrase: confirmationPhrase || null,
        readback_text: readbackText || null,
        reason,
      });
      setExecutionApprovalEnvelope(envelope);
      await refreshDashboard();
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : "Approval inválido o estado no permitido.");
    } finally {
      setExecutionBusy(false);
    }
  }, [executionApprovalEnvelope, refreshDashboard]);

  const dispatchExecution = useCallback(async () => {
    if (!executionPreview) return;
    setExecutionBusy(true);
    setExecutionError("");
    try {
      const result = await api.dispatchJarvisExecution({
        preview_id: executionPreview.preview_id,
        approval_id: executionApprovalEnvelope?.approval_id ?? null,
        actor: "David",
      });
      setExecutionDispatchResult(result);
      setExecutionPreview((current) => current ? { ...current, state: result.state ?? current.state, dispatch: result.dispatch ?? current.dispatch } : current);
      await refreshDashboard();
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : "Dispatch gobernado bloqueado.");
    } finally {
      setExecutionBusy(false);
    }
  }, [executionApprovalEnvelope?.approval_id, executionPreview, refreshDashboard]);

  const cancelExecution = useCallback(async (reason?: string) => {
    if (!executionPreview) return;
    setExecutionBusy(true);
    setExecutionError("");
    try {
      const preview = await api.cancelJarvisExecution({
        preview_id: executionPreview.preview_id,
        actor: "David",
        reason,
      });
      setExecutionPreview(preview);
      await refreshDashboard();
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : "No se pudo cancelar la preview.");
    } finally {
      setExecutionBusy(false);
    }
  }, [executionPreview, refreshDashboard]);

  const stopExecution = useCallback(async (reason?: string) => {
    setExecutionBusy(true);
    setExecutionError("");
    try {
      await api.stopJarvisExecution({
        preview_id: executionPreview?.preview_id ?? null,
        reason,
      });
      await refreshDashboard();
    } catch (err) {
      setExecutionError(err instanceof Error ? err.message : "Stop no soportado o no hay sesión activa.");
    } finally {
      setExecutionBusy(false);
    }
  }, [executionPreview?.preview_id, refreshDashboard]);

  useEffect(() => {
    let active = true;
    refreshDashboard()
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
  }, [refreshDashboard]);

  return (
    <JarvisPresenceShell
      dashboard={dashboard}
      connectionState={connectionState}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      localVoice={localVoice}
      cameraControl={cameraControl}
      audioRecorder={audioRecorder}
      events={eventStream.events}
      eventConnectionState={eventStream.connectionState}
      executionPreview={executionPreview}
      executionApprovalEnvelope={executionApprovalEnvelope}
      executionDispatchResult={executionDispatchResult}
      executionBusy={executionBusy}
      executionError={executionError}
      onCreateExecutionPreview={(payload) => void createExecutionPreview(payload)}
      onRequestExecutionApproval={() => void requestExecutionApproval()}
      onApproveExecution={(payload) => void decideExecutionApproval({
        decision: "approve",
        confirmationPhrase: payload.confirmationPhrase,
        readbackText: payload.readbackText,
      })}
      onRejectExecution={(reason) => void decideExecutionApproval({ decision: "reject", reason })}
      onCancelExecution={(reason) => {
        if (executionApprovalEnvelope?.status === "pending") {
          void decideExecutionApproval({ decision: "cancel", reason });
        }
        void cancelExecution(reason);
      }}
      onStopExecution={(reason) => void stopExecution(reason)}
      onClarifyExecution={(reason) => void decideExecutionApproval({ decision: "request_clarification", reason })}
      onDispatchExecution={() => void dispatchExecution()}
    />
  );
}
