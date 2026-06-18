import { jarvisToneProfiles } from "@/components/jarvis/contracts";
import type { JarvisOrbVisualState, JarvisVoiceTone, LocalVoiceLoopState } from "@/components/jarvis/types";
import { localVoiceStateIsError, voiceMotionFor } from "@/components/jarvis/utils";

export function useJarvisOrbState({
  localVoiceState,
  visualState,
  jarvisTone,
  killSwitchState,
  conversationActive,
}: {
  localVoiceState: LocalVoiceLoopState;
  visualState: JarvisOrbVisualState;
  jarvisTone: JarvisVoiceTone;
  killSwitchState: string;
  conversationActive: boolean;
}) {
  const killSwitchActive = killSwitchState === "active";
  const isStopped = visualState === "stopped" || killSwitchActive;
  const isError = visualState === "error" || localVoiceStateIsError(localVoiceState);
  const isAlert = visualState === "alert";
  const isExecuting = visualState === "executing";
  const isListening = visualState === "listening" || visualState === "wake_listening";
  const isTranscribing = visualState === "transcribing";
  const isThinking = visualState === "thinking";
  const isSpeaking = visualState === "speaking";
  const isActive = conversationActive || isListening || isTranscribing || isThinking || isSpeaking || isAlert || isExecuting;
  const profile = jarvisToneProfiles[jarvisTone];
  const motionBase = voiceMotionFor(jarvisTone, localVoiceState);
  const accent = isStopped
    ? "#94a3b8"
    : isError
      ? "#f87171"
      : isAlert
        ? "#fb923c"
        : isExecuting
          ? "#38bdf8"
          : profile.accent;
  const glow = isStopped
    ? "rgba(148,163,184,0.28)"
    : isError
      ? "rgba(248,113,113,0.46)"
      : isAlert
        ? "rgba(251,146,60,0.46)"
        : "rgba(34,211,238,0.48)";
  const pulse =
    isStopped ? 0.72 : isError ? 1.08 : isAlert ? 1.22 : isExecuting ? 1.26 : isSpeaking ? 1.28 : isThinking ? 1.18 : isTranscribing ? 1.13 : isListening ? 1.12 : isActive ? 1.04 : 0.88;
  const wave =
    isStopped ? 0.16 : isError ? 0.78 : isAlert ? 1.08 : isExecuting ? 1.14 : isSpeaking ? 1.22 : isThinking ? 0.86 : isTranscribing ? 0.92 : isListening ? 1.0 : 0.36;
  const glitch = isError ? 0.75 : isAlert ? 0.22 : 0;
  const motion =
    motionBase *
    (isStopped ? 0.28 : isError ? 1.18 : isAlert ? 1.28 : isExecuting ? 1.42 : isSpeaking ? 1.26 : isThinking ? 1.12 : isTranscribing ? 1.06 : isListening ? 1.0 : 0.82);
  return {
    accent,
    glow,
    motion,
    pulse,
    wave,
    glitch,
    targetFrameMs: isStopped ? 90 : isActive ? 16 : 50,
    particleBudget: isStopped ? 620 : isActive ? 1320 : 880,
    isError,
    isStopped,
    isAlert,
    isExecuting,
    isListening,
    isTranscribing,
    isThinking,
    isSpeaking,
    isActive,
    visualState,
    label: profile.label,
  };
}
