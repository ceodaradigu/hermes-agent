import { useEffect, useRef, useState } from "react";

export type JarvisRecordingState =
  | "unknown"
  | "idle"
  | "permission_requested"
  | "recording"
  | "stopping"
  | "ready"
  | "error"
  | "not_supported";

export interface JarvisRecordingAuditEvent {
  event: string;
  at: string;
  metadata: Record<string, string | boolean | number>;
}

export interface JarvisLocalRecording {
  url: string;
  filename: string;
  mimeType: string;
  sizeBytes: number;
  durationMs: number;
  createdAt: string;
}

function selectMimeType() {
  if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) return "";
  for (const mimeType of ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus", "audio/mp4"]) {
    if (MediaRecorder.isTypeSupported(mimeType)) return mimeType;
  }
  return "";
}

export function useJarvisAudioRecorder() {
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedAtRef = useRef<number | null>(null);
  const [recordingState, setRecordingState] = useState<JarvisRecordingState>("unknown");
  const [recordingError, setRecordingError] = useState("");
  const [recording, setRecording] = useState<JarvisLocalRecording | null>(null);
  const [auditEvents, setAuditEvents] = useState<JarvisRecordingAuditEvent[]>([]);

  function audit(event: string, metadata: Record<string, string | boolean | number> = {}) {
    setAuditEvents((items) => [
      {
        event,
        at: new Date().toISOString(),
        metadata: {
          local_only: true,
          raw_audio_sent_to_backend: false,
          external_streaming: false,
          hidden_recording: false,
          ...metadata,
        },
      },
      ...items,
    ].slice(0, 16));
  }

  function cleanupStream() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  function revokeRecording() {
    if (recording?.url) URL.revokeObjectURL(recording.url);
  }

  async function startRecording() {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setRecordingState("not_supported");
      setRecordingError("Este navegador no soporta grabación local con MediaRecorder.");
      audit("recording_not_supported");
      return;
    }
    if (recordingState === "recording" || recordingState === "permission_requested") return;

    revokeRecording();
    setRecording(null);
    setRecordingError("");
    setRecordingState("permission_requested");
    audit("recording_permission_requested");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      const mimeType = selectMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];
      streamRef.current = stream;
      recorderRef.current = recorder;
      startedAtRef.current = Date.now();

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onerror = (event) => {
        setRecordingError(event instanceof ErrorEvent ? event.message : "Error de MediaRecorder.");
        setRecordingState("error");
        audit("recording_error");
        cleanupStream();
      };
      recorder.onstop = () => {
        const durationMs = startedAtRef.current ? Date.now() - startedAtRef.current : 0;
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        const url = URL.createObjectURL(blob);
        const createdAt = new Date().toISOString();
        setRecording({
          url,
          filename: `jarvis-local-audio-${createdAt.replace(/[:.]/g, "-")}.webm`,
          mimeType: blob.type || "audio/webm",
          sizeBytes: blob.size,
          durationMs,
          createdAt,
        });
        setRecordingState("ready");
        audit("recording_stopped", {
          size_bytes: blob.size,
          duration_ms: durationMs,
        });
        cleanupStream();
      };

      recorder.start();
      setRecordingState("recording");
      audit("recording_started", {
        track_count: stream.getAudioTracks().length,
      });
    } catch (error) {
      setRecordingState("error");
      setRecordingError(error instanceof Error ? error.message : "No se pudo abrir el micrófono para grabación local.");
      audit("recording_permission_failed");
      cleanupStream();
    }
  }

  function stopRecording() {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      setRecordingState("stopping");
      recorderRef.current.stop();
      return;
    }
    cleanupStream();
    setRecordingState("idle");
  }

  function deleteRecording() {
    revokeRecording();
    setRecording(null);
    chunksRef.current = [];
    startedAtRef.current = null;
    setRecordingState("idle");
    audit("recording_deleted");
  }

  useEffect(() => {
    const supported = typeof navigator !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia) && typeof MediaRecorder !== "undefined";
    setRecordingState(supported ? "idle" : "not_supported");
    return () => {
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.stop();
      }
      cleanupStream();
      if (recording?.url) URL.revokeObjectURL(recording.url);
    };
  }, [recording?.url]);

  return {
    recordingState,
    recordingError,
    recording,
    recordingActive: recordingState === "recording",
    recordingAuditEvents: auditEvents,
    startRecording,
    stopRecording,
    deleteRecording,
  };
}
