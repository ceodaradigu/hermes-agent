import { useEffect, useMemo, useState } from "react";
import {
  JARVIS_EVENT_SNAPSHOT_ENDPOINT,
  JARVIS_EVENT_STREAM_ENDPOINT,
  previewVoiceSubtitle,
} from "@/components/jarvis/contracts";
import type { JarvisDashboardStatus } from "@/lib/api";
import type { JarvisEvent, JarvisEventSnapshot } from "@/components/jarvis/types";
import { valueText } from "@/components/jarvis/utils";
import type { JarvisCameraAuditEvent, JarvisCameraState, JarvisLocalVideoRecording, JarvisVideoRecordingState } from "./useJarvisCameraControl";
import type { JarvisLocalRecording, JarvisRecordingAuditEvent, JarvisRecordingState } from "./useJarvisAudioRecorder";

export interface LocalJarvisSensorState {
  camera?: {
    state: JarvisCameraState;
    active: boolean;
    auditEvents: JarvisCameraAuditEvent[];
    videoRecordingState?: JarvisVideoRecordingState;
    videoRecordingActive?: boolean;
    videoRecording?: JarvisLocalVideoRecording | null;
  };
  recording?: {
    state: JarvisRecordingState;
    active: boolean;
    recording: JarvisLocalRecording | null;
    auditEvents: JarvisRecordingAuditEvent[];
  };
}

function buildLocalSnapshot(status: JarvisDashboardStatus): JarvisEventSnapshot {
  const generatedAt = new Date().toISOString();
  const voiceState = status.voice_core?.state ?? {};
  const voiceRuntimePack = status.voice_runtime_pack ?? {};
  const voiceSessionState = status.voice_session?.state ?? {};
  const brainState = status.conversational_brain?.state ?? {};
  const brainPreview = status.conversational_brain?.sample_analysis;
  const ttsState = status.voice_core?.tts_state ?? {};
  const wakeState = status.wake_word_flow?.state ?? {};
  const cameraState = status.camera_vision?.state ?? {};
  const missionState = status.mission_control?.state ?? {};
  const approvals = status.approvals ?? {};
  const hermes = status.hermes_execution ?? {};
  const timeline = status.timeline ?? [];

  const event = (
    eventType: JarvisEvent["event_type"],
    source: string,
    state: string,
    payload: Record<string, unknown>,
  ): JarvisEvent => ({
    schema_version: "jarvis.dashboard.events.v1",
    event_id: `${eventType}-${generatedAt}`,
    id: `${eventType}-${generatedAt}`,
    event_type: eventType,
    type: eventType,
    created_at: generatedAt,
    timestamp: generatedAt,
    source,
    status: state,
    risk_level: eventType.includes("camera") || eventType.includes("recording") || eventType.includes("voice") || eventType.includes("wake") ? "sensor_privacy" : "low",
    read_only: true,
    can_execute: false,
    stream_can_execute: false,
    secret_free: true,
    raw_audio_included: false,
    camera_frames_included: false,
    payload,
  });

  return {
    schema_version: "jarvis.dashboard.events.v1",
    snapshot_id: `local-snapshot-${generatedAt}`,
    generated_at: generatedAt,
    created_at: generatedAt,
    stream: {
      endpoint: JARVIS_EVENT_SNAPSHOT_ENDPOINT,
      sse_endpoint: JARVIS_EVENT_STREAM_ENDPOINT,
      mode: "frontend_fallback_snapshot",
      schema_version: "jarvis.dashboard.events.v1",
      read_only: true,
      allowed_methods: ["GET"],
      required_event_fields: ["schema_version", "event_id", "event_type", "source", "created_at", "payload"],
      heartbeat_enabled: true,
      disconnect_safe: true,
      no_secrets: true,
      no_raw_audio: true,
      no_camera_frames: true,
      no_frontend_execution: true,
      stream_can_execute: false,
    },
    heartbeat: event("heartbeat", JARVIS_EVENT_STREAM_ENDPOINT, "local", {
      stream_alive: false,
      fallback_snapshot: true,
      disconnect_safe: true,
      can_execute: false,
    }),
    events: [
      event("brain_state", "/mark-3/conversational-brain/status", valueText(brainState.mode, "local_deterministic_bridge"), {
        llm_called: brainState.llm_called === true,
        external_provider_called: brainState.external_provider_called === true,
        memory_write: false,
        transcript_persistence: false,
        hermes_dispatch_allowed: false,
        sample_intent: valueText(brainPreview?.intent_detected),
        sample_risk_level: valueText(brainPreview?.risk_level),
      }),
      event("voice_state", "/voice-runtime/status", valueText(voiceState.current_state, "preview"), {
        microphone_enabled: voiceState.microphone_enabled === true,
        command_listening_enabled: voiceState.command_listening_enabled === true,
        approval_by_voice_enabled: voiceState.voice_approval_enabled === true,
      }),
      event("voice_runtime_state", "/mark-3/voice-runtime/status", valueText(voiceRuntimePack.current_state, "idle"), {
        schema_version: valueText(voiceRuntimePack.schema_version, "jarvis.voice_runtime_pack.v1"),
        mode: valueText(voiceRuntimePack.mode, "local_manual_browser_voice_control_plane"),
        manual_push_to_talk_enabled: voiceRuntimePack.manual_push_to_talk_enabled === true,
        browser_stt_available: valueText(voiceRuntimePack.browser_stt_available, "client_side_unknown"),
        browser_tts_available: valueText(voiceRuntimePack.browser_tts_available, "client_side_unknown"),
        raw_audio_sent_to_backend: false,
        transcript_persistence: false,
        voice_approval_enabled: false,
        wake_phrase_can_approve: false,
        wake_phrase_can_execute: false,
        hermes_dispatch_allowed: false,
      }),
      event("voice_session_state", "/voice-runtime/session-status", valueText(voiceSessionState.current_state, "idle"), {
        current_state: valueText(voiceSessionState.current_state, "idle"),
        wake_listening_state: valueText(voiceSessionState.wake_listening_state, "wake_listening_disabled"),
        conversation_active: voiceSessionState.conversation_active === true,
        raw_audio_sent_to_backend: false,
        transcript_persistence: false,
        background_transcription: false,
        always_on_stt: false,
        microphone_auto_start: false,
        voice_approval_enabled: false,
        hermes_dispatch_allowed: false,
      }),
      event("wake_state", "/mark-2/wake-listener/status", valueText(wakeState.mode, "preview"), {
        wake_runtime_enabled: wakeState.wake_runtime_enabled === true,
        wake_phrase_can_approve: false,
        supported_phrases: status.wake_word_flow?.supported_phrases ?? ["Hola Jarvis", "Jarvis"],
      }),
      event("tts_state", "/voice-runtime/status", valueText(ttsState.status, "preview"), {
        speaking: ttsState.speaking === true,
        preview_subtitle: valueText(ttsState.preview_subtitle, previewVoiceSubtitle),
        external_call: ttsState.external_call === true,
      }),
      event("hermes_state", "/mark-3/hermes-runtime/status", valueText(hermes.execution_mode, "read_only_visibility"), {
        active_execution: hermes.active_execution === true,
        frontend_can_execute: false,
      }),
      event("approval_state", "/approvals/status", valueText(approvals.cards_state, "preview/read-only"), {
        pending_count: approvals.pending_count ?? "unknown",
        action_buttons_enabled: false,
        wake_phrase_can_approve: false,
      }),
      event("mission_state", "/mark-3/dashboard/status", valueText(missionState.mode, "preview"), {
        execution_enabled: missionState.execution_enabled === true,
        hermes_dispatch_enabled: missionState.hermes_dispatch_enabled === true,
      }),
      event("camera_state", "/camera-control/status", valueText(cameraState.mode, "preview"), {
        camera_enabled: cameraState.camera_enabled === true,
        recording: cameraState.recording === true,
        video_recording_available: valueText(cameraState.video_recording_available, "browser_local_opt_in"),
        video_recording_active: cameraState.video_recording_active === true,
        video_recording_blob_ready: cameraState.video_recording_blob_ready === true,
        raw_video_sent_to_backend: false,
        streaming: cameraState.streaming === true,
        backend_upload: false,
        background_camera_access: cameraState.background_camera_access === true,
      }),
      event("recording_state", "/mark-3/dashboard/status", "disabled", {
        raw_audio_recording_enabled: status.raw_audio_recording?.state?.mode === "browser_local_recorder",
        recording_active: false,
        retention_policy: valueText(status.raw_audio_recording?.retention?.storage, "browser_memory_blob_until_download_or_delete"),
        delete_available: status.raw_audio_recording?.state?.delete_available_after_stop === true,
        raw_audio_sent_to_backend: false,
      }),
      event("memory_state", "/mark-3/outcomes + /mark-3/learning/proposals + /personal-memory/status", valueText(status.memory_brain?.state?.mode, "visible_read_only_brain"), {
        visible_brain: true,
        outcomes: status.memory_brain?.counts?.outcomes ?? 0,
        learning_proposals: status.memory_brain?.counts?.learning_proposals ?? 0,
        entities: status.memory_brain?.counts?.entities ?? status.memory_brain?.entities?.length ?? 0,
        facts: status.memory_brain?.counts?.facts ?? status.memory_brain?.facts?.length ?? 0,
        preferences: status.memory_brain?.counts?.preferences ?? status.memory_brain?.preferences?.length ?? 0,
        decisions: status.memory_brain?.counts?.decisions ?? status.memory_brain?.decisions?.length ?? 0,
        contradictions: status.memory_brain?.counts?.contradictions ?? status.memory_brain?.contradictions?.length ?? 0,
        active_memories: status.memory_brain?.counts?.active_memories ?? 0,
        pending_review: status.memory_brain?.counts?.pending_review ?? 0,
        forgotten_deleted: status.memory_brain?.counts?.forgotten_deleted ?? 0,
        memory_grants_permission: false,
      }),
      event("memory_brain_v2_state", "/mark-3/memory-brain/preview", valueText(status.memory_brain?.state?.memory_brain_v2_mode ?? status.memory_brain_v2?.state?.mode, "in_memory_explainable_memory_brain_v2"), {
        schema_version: "jarvis.memory_brain_v2.v1",
        persistent: status.memory_brain?.state?.persistent === true,
        entities: status.memory_brain?.counts?.entities ?? 0,
        facts: status.memory_brain?.counts?.facts ?? 0,
        preferences: status.memory_brain?.counts?.preferences ?? 0,
        decisions: status.memory_brain?.counts?.decisions ?? 0,
        contradictions: status.memory_brain?.counts?.contradictions ?? 0,
        active_memories: status.memory_brain?.counts?.active_memories ?? 0,
        pending_review: status.memory_brain?.counts?.pending_review ?? 0,
        forgotten_deleted: status.memory_brain?.counts?.forgotten_deleted ?? 0,
        memory_autoload_enabled: false,
        memory_grants_permission: false,
      }),
      event("risk_state", "/mark-3/dashboard/status", "preview", {
        current_risk: valueText(status.mission_control?.intent_preview?.risk_level),
        wake_phrase_is_permission: false,
      }),
      event("execution_state", "/mark-3/dashboard/status", "gated", {
        preview_required: true,
        approval_required: true,
        rollback_or_stop_plan_required: true,
        frontend_direct_execution_allowed: false,
      }),
      event("audit_event", "/mark-3/dashboard/status", "read_only", {
        recent_events: timeline.slice(0, 4).map((item) => item.event),
        raw_audio_logged: false,
        camera_frames_logged: false,
      }),
      event("persistent_audit_state", "/mark-3/audit/status", valueText(status.persistent_audit?.state?.mode, "in_memory_metadata_audit_ledger"), {
        schema_version: "jarvis.persistent_audit.v1",
        persistent: status.persistent_audit?.state?.persistent === true,
        event_count: status.persistent_audit?.state?.event_count ?? 0,
        tamper_evident: true,
        hash_chain_valid: status.persistent_audit?.chain?.valid !== false,
        metadata_only: true,
        contains_raw_audio: false,
        contains_camera_frame: false,
        contains_secret: false,
        contains_credential: false,
        contains_full_transcript: false,
        hermes_dispatch_allowed: false,
      }),
    ],
  };
}

function localEvent(
  generatedAt: string,
  eventType: JarvisEvent["event_type"],
  source: string,
  status: string,
  payload: Record<string, unknown>,
): JarvisEvent {
  return {
    schema_version: "jarvis.dashboard.events.v1",
    event_id: `${eventType}-local-${generatedAt}`,
    id: `${eventType}-local-${generatedAt}`,
    event_type: eventType,
    type: eventType,
    created_at: generatedAt,
    timestamp: generatedAt,
    source,
    status,
    risk_level: "sensor_privacy",
    read_only: true,
    can_execute: false,
    stream_can_execute: false,
    secret_free: true,
    raw_audio_included: false,
    camera_frames_included: false,
    payload,
  };
}

function applyLocalSensorOverlay(snapshot: JarvisEventSnapshot, localSensors?: LocalJarvisSensorState): JarvisEventSnapshot {
  if (!localSensors?.camera && !localSensors?.recording) return snapshot;

  const generatedAt = new Date().toISOString();
  const byType = new Map<string, JarvisEvent>();
  snapshot.events.forEach((event) => byType.set(event.event_type, event));
  const sensorLedgerEvents: Array<Record<string, unknown>> = [];

  if (localSensors.camera) {
    sensorLedgerEvents.push(
      ...localSensors.camera.auditEvents.slice(0, 3).map((event) => ({
        sensor_type: "camera",
        event_type: event.event,
        source: "/jarvis/browser-camera",
        created_at: event.at,
        metadata_only: true,
        raw_video_included: false,
        frames_included: false,
        backend_upload: false,
      })),
    );
    byType.set(
      "camera_state",
      localEvent(generatedAt, "camera_state", "/jarvis/browser-camera", localSensors.camera.state, {
        camera_enabled: localSensors.camera.active,
        permission_requested: localSensors.camera.state === "permission_requested",
        preview_enabled: localSensors.camera.active,
        recording: localSensors.camera.videoRecordingActive === true,
        video_recording_state: localSensors.camera.videoRecordingState ?? "idle",
        local_video_blob_ready: Boolean(localSensors.camera.videoRecording),
        local_video_blob_size_bytes: localSensors.camera.videoRecording?.sizeBytes ?? 0,
        streaming_external: false,
        backend_upload: false,
        raw_video_sent_to_backend: false,
        analysis_enabled: false,
        people_analysis_default: false,
        recent_audit_events: localSensors.camera.auditEvents.slice(0, 3).map((event) => event.event),
      }),
    );
  }

  if (localSensors.recording) {
    sensorLedgerEvents.push(
      ...localSensors.recording.auditEvents.slice(0, 3).map((event) => ({
        sensor_type: "recording",
        event_type: event.event,
        source: "/jarvis/browser-audio-recorder",
        created_at: event.at,
        metadata_only: true,
        raw_audio_included: false,
        backend_upload: false,
      })),
    );
    byType.set(
      "recording_state",
      localEvent(generatedAt, "recording_state", "/jarvis/browser-audio-recorder", localSensors.recording.state, {
        raw_audio_recording_enabled: true,
        recording_active: localSensors.recording.active,
        local_blob_ready: Boolean(localSensors.recording.recording),
        local_blob_size_bytes: localSensors.recording.recording?.sizeBytes ?? 0,
        raw_audio_sent_to_backend: false,
        external_streaming: false,
        hidden_recording: false,
        retention_policy: "browser_memory_blob_until_download_or_delete",
        recent_audit_events: localSensors.recording.auditEvents.slice(0, 3).map((event) => event.event),
      }),
    );
  }

  if (sensorLedgerEvents.length) {
    byType.set(
      "sensor_ledger_state",
      localEvent(generatedAt, "sensor_ledger_state", "/jarvis/browser-sensor-ledger-overlay", "metadata_only_local_overlay", {
        schema_version: "jarvis.sensor_ledger.v1",
        metadata_only: true,
        browser_local_only: true,
        backend_ingestion_enabled: false,
        event_count: sensorLedgerEvents.length,
        recent_sensor_events: sensorLedgerEvents,
        no_raw_audio: true,
        no_camera_frames: true,
        no_video_frames: true,
        no_credentials: true,
      }),
    );
  }

  return {
    ...snapshot,
    generated_at: generatedAt,
    events: Array.from(byType.values()),
  };
}

async function fetchEventSnapshot(): Promise<JarvisEventSnapshot> {
  const response = await fetch(JARVIS_EVENT_SNAPSHOT_ENDPOINT);
  if (!response.ok) throw new Error(`${response.status}: ${await response.text().catch(() => response.statusText)}`);
  return response.json() as Promise<JarvisEventSnapshot>;
}

export function useJarvisEventStream(status: JarvisDashboardStatus, localSensors?: LocalJarvisSensorState) {
  const [snapshot, setSnapshot] = useState<JarvisEventSnapshot>(() => buildLocalSnapshot(status));
  const [connectionState, setConnectionState] = useState<"local" | "snapshot" | "stream" | "offline">("local");

  useEffect(() => {
    setSnapshot((current) => (current.stream.mode === "frontend_fallback_snapshot" ? buildLocalSnapshot(status) : current));
  }, [status]);

  useEffect(() => {
    let active = true;
    fetchEventSnapshot()
      .then((payload) => {
        if (!active) return;
        setSnapshot(payload);
        setConnectionState("snapshot");
      })
      .catch(() => {
        if (!active) return;
        setSnapshot(buildLocalSnapshot(status));
        setConnectionState("local");
      });

    if (typeof window === "undefined" || !("EventSource" in window)) {
      return () => {
        active = false;
      };
    }

    const source = new EventSource(JARVIS_EVENT_STREAM_ENDPOINT);
    source.addEventListener("jarvis_event_snapshot", (event) => {
      if (!active) return;
      try {
        setSnapshot(JSON.parse(event.data) as JarvisEventSnapshot);
        setConnectionState("stream");
      } catch {
        setConnectionState("offline");
      }
    });
    source.onerror = () => {
      if (!active) return;
      setConnectionState((current) => (current === "stream" ? "snapshot" : current));
    };

    return () => {
      active = false;
      source.close();
    };
  }, [status]);

  const renderedSnapshot = useMemo(() => applyLocalSensorOverlay(snapshot, localSensors), [snapshot, localSensors]);

  const eventsByType = useMemo(() => {
    const byType = new Map<string, JarvisEvent>();
    renderedSnapshot.events.forEach((event) => byType.set(event.event_type, event));
    return byType;
  }, [renderedSnapshot.events]);

  return { snapshot: renderedSnapshot, events: renderedSnapshot.events, eventsByType, connectionState };
}
