import { useCallback, useEffect, useMemo, useState } from "react";
import {
  api,
  type JarvisDashboardStatus,
  type JarvisConversationTurnResponse,
  type JarvisExecutionApprovalEnvelope,
  type JarvisExecutionDispatchResult,
  type JarvisExecutionPreview,
} from "@/lib/api";
import { fallbackDashboard, type CommandCenterTabId } from "@/components/jarvis/contracts";
import type { JarvisConversationMessage, JarvisConversationMessageStatus, LocalJarvisVoiceResponse } from "@/components/jarvis/types";
import { JarvisPresenceShell } from "@/components/jarvis/JarvisPresenceShell";
import { useJarvisAudioRecorder } from "@/hooks/jarvis/useJarvisAudioRecorder";
import { useJarvisCameraControl } from "@/hooks/jarvis/useJarvisCameraControl";
import { useJarvisEventStream } from "@/hooks/jarvis/useJarvisEventStream";
import { useLocalVoiceLoop } from "@/hooks/jarvis/useLocalVoiceLoop";

const CONVERSATION_HISTORY_LIMIT = 18;

function newId(prefix: string): string {
  return `${prefix}_${globalThis.crypto?.randomUUID?.() ?? `${Date.now()}_${Math.random().toString(16).slice(2)}`}`;
}

function conversationStatus(value: string | undefined): JarvisConversationMessageStatus {
  if (value === "preview" || value === "approval_required" || value === "blocked" || value === "unsupported" || value === "error") {
    return value;
  }
  return "normal";
}

function appendLimited(messages: JarvisConversationMessage[], next: JarvisConversationMessage): JarvisConversationMessage[] {
  return [...messages, next].slice(-CONVERSATION_HISTORY_LIMIT);
}

function turnToVoiceResponse(turn: JarvisConversationTurnResponse): LocalJarvisVoiceResponse {
  const status = conversationStatus(turn.status);
  const tone = status === "blocked" || status === "unsupported" || status === "approval_required" || status === "error" ? "alerta" : status === "preview" ? "concentrado" : "calmado";
  return {
    text: turn.assistant_text,
    tone,
    intent: turn.intent?.intent_detected ?? status,
    risk: turn.intent?.risk_level ?? (status === "blocked" ? "forbidden" : "none"),
    operatorSummary: turn.display?.summary ?? "Respuesta conversacional segura.",
    intentPreview: {
      intent_detected: turn.intent?.intent_detected ?? status,
      confidence: turn.intent?.confidence ?? 0.5,
      risk_level: turn.intent?.risk_level ?? "none",
      approval_level: turn.intent?.approval_level ?? "direct",
      requires_approval: turn.intent?.requires_approval === true,
      can_prepare_preview: turn.intent?.can_prepare_preview === true,
      cannot_execute_reason: turn.preview?.next_safe_action ?? "No se ejecutó nada desde la conversación.",
      suggested_next_action: turn.preview?.next_safe_action ?? turn.display?.summary ?? "Seguir en conversación segura.",
      hermes_dispatch_allowed: false,
    },
  };
}

export default function JarvisCommandCenterPage() {
  const [dashboard, setDashboard] = useState<JarvisDashboardStatus>(() => fallbackDashboard("loading"));
  const [connectionState, setConnectionState] = useState<"loading" | "online" | "offline">("loading");
  const [activeTab, setActiveTab] = useState<CommandCenterTabId>("cockpit");
  const [conversationId] = useState(() => newId("jarvis_conversation"));
  const [conversationMessages, setConversationMessages] = useState<JarvisConversationMessage[]>([]);
  const [conversationBusy, setConversationBusy] = useState(false);
  const [conversationError, setConversationError] = useState("");
  const [typedSpeechRequest, setTypedSpeechRequest] = useState<{ id: string; text: string; tone: LocalJarvisVoiceResponse["tone"] } | null>(null);
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

  const submitConversationTurn = useCallback(async (
    text: string,
    source: "typed_text" | "voice_transcript" = "typed_text",
    channel = "jarvis_ui",
  ): Promise<LocalJarvisVoiceResponse | null> => {
    const trimmed = text.trim();
    if (!trimmed || conversationBusy) return null;

    const timestamp = new Date().toISOString();
    setConversationError("");
    setConversationMessages((current) => appendLimited(current, {
      id: newId("user"),
      role: "user",
      content: trimmed,
      status: "normal",
      timestamp,
      source,
    }));
    setConversationBusy(true);

    try {
      const turn = await api.createJarvisConversationTurn({
        user_text: trimmed,
        channel,
        conversation_id: conversationId,
        source,
        operator: "David",
        voice_session_state: source === "voice_transcript" ? "conversation_active" : "idle",
        transcript_confidence: 1,
        context_flags: {
          frontend_direct_hermes_allowed: false,
          preview_only: true,
        },
      });
      const status = conversationStatus(turn.status);
      const voiceResponse = turnToVoiceResponse(turn);
      setConversationMessages((current) => appendLimited(current, {
        id: turn.turn_id || newId("jarvis"),
        role: "assistant",
        content: turn.assistant_text,
        status,
        timestamp: turn.created_at || new Date().toISOString(),
        source: "system",
      }));
      if (source === "typed_text") {
        setTypedSpeechRequest({
          id: turn.turn_id || newId("speech"),
          text: turn.assistant_text,
          tone: voiceResponse.tone,
        });
      }
      return voiceResponse;
    } catch {
      const message = "No pude responder ahora. El servicio local de conversación no aceptó el turno; prueba otra vez en unos segundos.";
      setConversationError(message);
      setConversationMessages((current) => appendLimited(current, {
        id: newId("jarvis_error"),
        role: "assistant",
        content: message,
        status: "error",
        timestamp: new Date().toISOString(),
        source: "system",
      }));
      return {
        text: message,
        tone: "alerta",
        intent: "conversation_turn_error",
        risk: "none",
        operatorSummary: "Error local de conversación; no hubo ejecución.",
        intentPreview: {
          intent_detected: "conversation_turn_error",
          confidence: 0,
          risk_level: "none",
          approval_level: "direct",
          requires_approval: false,
          can_prepare_preview: false,
          cannot_execute_reason: "El turno conversacional falló antes de cualquier acción.",
          suggested_next_action: "Reintentar desde texto.",
          hermes_dispatch_allowed: false,
        },
      };
    } finally {
      setConversationBusy(false);
    }
  }, [conversationBusy, conversationId]);

  const localVoice = useLocalVoiceLoop({
    onIntentSubmitted: (text) => {
      return submitConversationTurn(text, "voice_transcript", "jarvis_voice");
    },
  });

  useEffect(() => {
    if (!typedSpeechRequest) return;
    localVoice.speakJarvisText(typedSpeechRequest.text, typedSpeechRequest.tone);
    setTypedSpeechRequest(null);
  }, [localVoice, typedSpeechRequest]);
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
      conversationMessages={conversationMessages}
      conversationBusy={conversationBusy}
      conversationError={conversationError}
      onSubmitConversation={(text) => void submitConversationTurn(text)}
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
