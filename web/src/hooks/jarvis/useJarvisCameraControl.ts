import { useEffect, useRef, useState } from "react";

export type JarvisCameraState = "unknown" | "idle" | "permission_requested" | "active" | "stopping" | "error" | "not_supported";
export type JarvisVideoRecordingState = "unknown" | "idle" | "permission_requested" | "recording" | "stopping" | "ready" | "error" | "not_supported";

export interface JarvisCameraAuditEvent {
  event: string;
  at: string;
  metadata: Record<string, string | boolean | number>;
}

export interface JarvisLocalVideoRecording {
  url: string;
  filename: string;
  mimeType: string;
  sizeBytes: number;
  durationMs: number;
  createdAt: string;
}

function selectVideoMimeType() {
  if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) return "";
  for (const mimeType of ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm", "video/mp4"]) {
    if (MediaRecorder.isTypeSupported(mimeType)) return mimeType;
  }
  return "";
}

export function useJarvisCameraControl() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const videoRecorderRef = useRef<MediaRecorder | null>(null);
  const videoChunksRef = useRef<BlobPart[]>([]);
  const videoStartedAtRef = useRef<number | null>(null);
  const videoRecordingUrlRef = useRef("");
  const [cameraState, setCameraState] = useState<JarvisCameraState>("unknown");
  const [videoRecordingState, setVideoRecordingState] = useState<JarvisVideoRecordingState>("unknown");
  const [cameraError, setCameraError] = useState("");
  const [videoRecordingError, setVideoRecordingError] = useState("");
  const [videoRecording, setVideoRecording] = useState<JarvisLocalVideoRecording | null>(null);
  const [auditEvents, setAuditEvents] = useState<JarvisCameraAuditEvent[]>([]);

  function audit(event: string, metadata: Record<string, string | boolean | number> = {}) {
    setAuditEvents((items) => [
      {
        event,
        at: new Date().toISOString(),
        metadata: {
          local_only: true,
          no_recording_on_load: true,
          no_hidden_recording: true,
          no_external_streaming: true,
          no_backend_upload: true,
          raw_video_sent_to_backend: false,
          no_person_identity_analysis: true,
          ...metadata,
        },
      },
      ...items,
    ].slice(0, 12));
  }

  function attachStream(stream: MediaStream) {
    if (!videoRef.current) return;
    videoRef.current.srcObject = stream;
    videoRef.current.muted = true;
    videoRef.current.playsInline = true;
    void videoRef.current.play().catch(() => {
      setCameraError("El navegador bloqueó la reproducción del preview local.");
    });
  }

  async function ensureCameraStream(): Promise<MediaStream | null> {
    if (streamRef.current) {
      attachStream(streamRef.current);
      setCameraState("active");
      return streamRef.current;
    }
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setCameraState("not_supported");
      setCameraError("Este navegador no expone cámara mediante mediaDevices.");
      audit("camera_not_supported");
      return null;
    }
    setCameraError("");
    setCameraState("permission_requested");
    audit("camera_permission_requested");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      streamRef.current = stream;
      attachStream(stream);
      setCameraState("active");
      audit("camera_preview_started", {
        track_count: stream.getVideoTracks().length,
      });
      return stream;
    } catch (error) {
      setCameraState("error");
      setCameraError(error instanceof Error ? error.message : "No se pudo abrir la cámara.");
      audit("camera_permission_failed");
      return null;
    }
  }

  function revokeVideoRecording() {
    if (videoRecordingUrlRef.current) {
      URL.revokeObjectURL(videoRecordingUrlRef.current);
      videoRecordingUrlRef.current = "";
    }
  }

  async function startCameraPreview() {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setCameraState("not_supported");
      setCameraError("Este navegador no expone cámara mediante mediaDevices.");
      audit("camera_not_supported");
      return;
    }
    await ensureCameraStream();
  }

  async function startVideoRecording() {
    if (typeof MediaRecorder === "undefined") {
      setVideoRecordingState("not_supported");
      setVideoRecordingError("El navegador no soporta grabación de vídeo local.");
      audit("video_recording_not_supported");
      return;
    }
    if (videoRecordingState === "recording" || videoRecordingState === "permission_requested") return;

    setVideoRecordingError("");
    setVideoRecordingState("permission_requested");
    audit("video_recording_requested", {
      audio: false,
      backend_upload: false,
    });
    revokeVideoRecording();
    setVideoRecording(null);

    const stream = await ensureCameraStream();
    if (!stream) {
      setVideoRecordingState("error");
      setVideoRecordingError("No hay stream de cámara local para grabar vídeo.");
      audit("video_recording_failed");
      return;
    }
    if (!stream.getVideoTracks().length) {
      setVideoRecordingState("not_supported");
      setVideoRecordingError("El navegador no entregó una pista de vídeo grabable.");
      audit("video_recording_not_supported");
      return;
    }

    try {
      const videoOnlyStream = new MediaStream(stream.getVideoTracks());
      const mimeType = selectVideoMimeType();
      const recorder = new MediaRecorder(videoOnlyStream, mimeType ? { mimeType } : undefined);
      videoChunksRef.current = [];
      videoRecorderRef.current = recorder;
      videoStartedAtRef.current = Date.now();
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) videoChunksRef.current.push(event.data);
      };
      recorder.onerror = (event) => {
        setVideoRecordingError(event instanceof ErrorEvent ? event.message : "Error de MediaRecorder de vídeo.");
        setVideoRecordingState("error");
        audit("video_recording_failed");
      };
      recorder.onstop = () => {
        const durationMs = videoStartedAtRef.current ? Date.now() - videoStartedAtRef.current : 0;
        const blob = new Blob(videoChunksRef.current, { type: recorder.mimeType || "video/webm" });
        const url = URL.createObjectURL(blob);
        videoRecordingUrlRef.current = url;
        const createdAt = new Date().toISOString();
        setVideoRecording({
          url,
          filename: `jarvis-local-video-${createdAt.replace(/[:.]/g, "-")}.webm`,
          mimeType: blob.type || "video/webm",
          sizeBytes: blob.size,
          durationMs,
          createdAt,
        });
        setVideoRecordingState("ready");
        audit("video_recording_stopped", {
          size_bytes: blob.size,
          duration_ms: durationMs,
          raw_video_sent_to_backend: false,
        });
      };
      recorder.start();
      setVideoRecordingState("recording");
      audit("video_recording_started", {
        track_count: stream.getVideoTracks().length,
        audio_track_count: 0,
        backend_upload: false,
      });
    } catch (error) {
      setVideoRecordingState("error");
      setVideoRecordingError(error instanceof Error ? error.message : "El navegador no soporta grabación de vídeo local.");
      audit("video_recording_failed");
    }
  }

  function stopVideoRecording() {
    if (videoRecorderRef.current && videoRecorderRef.current.state !== "inactive") {
      setVideoRecordingState("stopping");
      videoRecorderRef.current.stop();
      return;
    }
    setVideoRecordingState("idle");
  }

  function deleteVideoRecording() {
    revokeVideoRecording();
    setVideoRecording(null);
    videoChunksRef.current = [];
    videoStartedAtRef.current = null;
    setVideoRecordingState("idle");
    audit("video_recording_deleted");
  }

  function stopCameraPreview() {
    if (videoRecorderRef.current && videoRecorderRef.current.state !== "inactive") {
      stopVideoRecording();
    }
    setCameraState((current) => (current === "active" ? "stopping" : current));
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.srcObject = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraState("idle");
    audit("camera_preview_stopped");
  }

  useEffect(() => {
    const supported = typeof navigator !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia);
    setCameraState(supported ? "idle" : "not_supported");
    setVideoRecordingState(supported && typeof MediaRecorder !== "undefined" ? "idle" : "not_supported");
    return () => {
      if (videoRecorderRef.current && videoRecorderRef.current.state !== "inactive") {
        videoRecorderRef.current.stop();
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      revokeVideoRecording();
    };
  }, []);

  return {
    videoRef,
    cameraState,
    cameraError,
    cameraActive: cameraState === "active",
    cameraAuditEvents: auditEvents,
    videoRecordingState,
    videoRecordingError,
    videoRecording,
    videoRecordingActive: videoRecordingState === "recording",
    startCameraPreview,
    stopCameraPreview,
    startVideoRecording,
    stopVideoRecording,
    deleteVideoRecording,
  };
}
