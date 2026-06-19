import { jarvisToneProfiles } from "@/components/jarvis/contracts";
import type { JarvisOrbVisualState, JarvisVoiceTone, LocalVoiceLoopState } from "@/components/jarvis/types";
import { localVoiceStateIsError, voiceMotionFor } from "@/components/jarvis/utils";

export function useJarvisOrbState({
  localVoiceState,
  visualState,
  jarvisTone,
  killSwitchState,
  conversationActive,
  textReactive = false,
}: {
  localVoiceState: LocalVoiceLoopState;
  visualState: JarvisOrbVisualState;
  jarvisTone: JarvisVoiceTone;
  killSwitchState: string;
  conversationActive: boolean;
  textReactive?: boolean;
}) {
  const killSwitchActive = killSwitchState === "active";
  const isStopped = visualState === "stopped" || killSwitchActive;
  const isError = visualState === "error" || localVoiceStateIsError(localVoiceState);
  const isApprovalRequired = visualState === "approval_required";
  const isAlert = visualState === "alert" || isApprovalRequired;
  const isExecuting = visualState === "executing";
  const isListening = visualState === "listening" || visualState === "wake_listening";
  const isTranscribing = visualState === "transcribing";
  const isThinking = visualState === "thinking";
  const isSpeaking = visualState === "speaking";
  const textReactiveActive = textReactive && !isStopped;
  const isActive = conversationActive || textReactiveActive || isListening || isTranscribing || isThinking || isSpeaking || isAlert || isExecuting;
  const profile = jarvisToneProfiles[jarvisTone];
  const motionBase = voiceMotionFor(jarvisTone, localVoiceState);
  const coreColor = isStopped
    ? "#cbd5e1"
    : isError
      ? "#ffe4e6"
      : isAlert
        ? isApprovalRequired ? "#fff7bf" : "#ffedd5"
        : "#e6fbff";
  const coreGlow = isStopped
    ? "rgba(148,163,184,0.28)"
    : isError
      ? "rgba(255,228,230,0.68)"
      : isAlert
        ? isApprovalRequired ? "rgba(254,240,138,0.74)" : "rgba(255,237,213,0.68)"
        : "rgba(230,251,255,0.84)";
  const outerGlow = isStopped
    ? "rgba(15,23,42,0.18)"
    : isError
      ? "rgba(248,113,113,0.30)"
      : isAlert
        ? isApprovalRequired ? "rgba(250,204,21,0.32)" : "rgba(251,146,60,0.28)"
        : "rgba(34,211,238,0.18)";
  const accent = isStopped
    ? "#94a3b8"
    : isError
      ? "#f87171"
      : isAlert
      ? isApprovalRequired ? "#facc15" : "#fb923c"
        : isExecuting
          ? "#38bdf8"
          : profile.accent;
  const glow = isStopped
    ? "rgba(148,163,184,0.28)"
    : isError
      ? "rgba(248,113,113,0.46)"
      : isAlert
      ? isApprovalRequired ? "rgba(250,204,21,0.50)" : "rgba(251,146,60,0.46)"
        : "rgba(34,211,238,0.48)";
  const pulse =
    isStopped ? 0.72 : isError ? 1.08 : isAlert ? 1.22 : isExecuting ? 1.26 : isSpeaking ? 1.30 : isThinking ? 1.18 : isTranscribing ? 1.16 : visualState === "listening" ? 1.18 : visualState === "wake_listening" ? 1.08 : textReactiveActive ? 1.10 : isActive ? 1.06 : 0.94;
  const wave =
    isStopped ? 0.16 : isError ? 0.78 : isAlert ? 1.08 : isExecuting ? 1.14 : isSpeaking ? 1.28 : isThinking ? 0.90 : isTranscribing ? 1.02 : visualState === "listening" ? 1.12 : visualState === "wake_listening" ? 0.62 : textReactiveActive ? 0.78 : 0.44;
  const glitch = isError ? 0.75 : isAlert ? 0.22 : 0;
  const motion =
    motionBase *
    (isStopped ? 0.28 : isError ? 1.18 : isAlert ? 1.28 : isExecuting ? 1.42 : isSpeaking ? 1.32 : isThinking ? 1.14 : isTranscribing ? 1.12 : visualState === "listening" ? 1.08 : visualState === "wake_listening" ? 0.92 : textReactiveActive ? 0.98 : 0.86);
  const baseReactiveEnergy =
    isStopped ? 0.06 : isError ? 0.88 : isAlert ? 0.82 : isExecuting ? 0.92 : isSpeaking ? 1 : isThinking ? 0.76 : isTranscribing ? 0.74 : visualState === "listening" ? 0.82 : visualState === "wake_listening" ? 0.50 : 0.30;
  const stateReactiveEnergy = Math.min(1, baseReactiveEnergy + (textReactiveActive ? 0.24 : 0));
  const speakingSpikeEnergy = isStopped ? 0 : isSpeaking ? 1 : textReactiveActive ? 0.46 : 0;
  const radialSpikeEnergy = isStopped ? 0 : isError ? 1.05 : isAlert ? 0.84 : isSpeaking ? 1 : textReactiveActive ? 0.46 : 0;
  const thinkingTurbulence = isStopped ? 0 : isThinking ? 1 : isTranscribing ? 0.30 : 0;
  const listeningFocus = isStopped ? 0 : visualState === "listening" ? 1 : visualState === "wake_listening" ? 0.42 : 0;
  const transcribingReflow = isStopped ? 0 : isTranscribing ? 1 : 0;
  const spherePressure = isStopped ? 0.08 : isError ? 0.92 : isAlert ? 0.78 : isSpeaking ? 1 : isThinking ? 0.62 : isTranscribing ? 0.52 : visualState === "listening" ? 0.44 : visualState === "wake_listening" ? 0.28 : textReactiveActive ? 0.50 : 0.18;
  const emergentCoreConcentration = isStopped
    ? 0.02
    : isError
      ? 0.70
      : isAlert
        ? 0.62
        : isSpeaking
          ? 0.78
          : isThinking
            ? 0.58
            : isTranscribing
              ? 0.46
              : visualState === "listening"
                ? 0.52
                : visualState === "wake_listening"
                  ? 0.34
                  : textReactiveActive
                    ? 0.50
                    : 0.06;
  const sphereScaleMin =
    isStopped ? 0.60 : isError ? 0.82 : isAlert ? 0.84 : isSpeaking ? 0.76 : isThinking ? 0.70 : isTranscribing ? 0.82 : visualState === "listening" ? 0.74 : visualState === "wake_listening" ? 0.82 : 0.92;
  const sphereScaleMid =
    isStopped ? 0.66 : isError ? 1.06 : isAlert ? 1.02 : isSpeaking ? 0.96 : isThinking ? 0.94 : isTranscribing ? 0.95 : visualState === "listening" ? 0.86 : visualState === "wake_listening" ? 0.90 : 0.98;
  const sphereScaleMax =
    isStopped ? 0.72 : isError ? 1.28 : isAlert ? 1.18 : isSpeaking ? 1.22 : isThinking ? 1.13 : isTranscribing ? 1.04 : visualState === "listening" ? 0.96 : visualState === "wake_listening" ? 1.00 : textReactiveActive ? 1.08 : 1.03;
  const sphereAnimationSeconds =
    isStopped ? 8.5 : isError ? 1.15 : isAlert ? 1.55 : isSpeaking ? 1.45 : isThinking ? 2.1 : isTranscribing ? 2.7 : visualState === "listening" ? 2.35 : visualState === "wake_listening" ? 3.2 : 5.8;
  return {
    accent,
    coreColor,
    coreGlow,
    glow,
    outerGlow,
    motion,
    pulse,
    wave,
    glitch,
    stateReactiveEnergy,
    speakingSpikeEnergy,
    radialSpikeEnergy,
    thinkingTurbulence,
    listeningFocus,
    transcribingReflow,
    spherePressure,
    emergentCoreConcentration,
    sphereScaleMin,
    sphereScaleMid,
    sphereScaleMax,
    sphereAnimationSeconds,
    targetFrameMs: isStopped ? 90 : isActive ? 16 : 42,
    particleBudget: isStopped ? 900 : isSpeaking ? 3800 : isThinking ? 3500 : visualState === "listening" ? 3200 : isTranscribing ? 3200 : textReactiveActive ? 3000 : isActive ? 2900 : 2400,
    textReactiveActive,
    isError,
    isApprovalRequired,
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
