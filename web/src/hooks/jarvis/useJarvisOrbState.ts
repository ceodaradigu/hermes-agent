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
    isStopped ? 0.72 : isError ? 1.08 : isAlert ? 1.22 : isExecuting ? 1.26 : isSpeaking ? 1.30 : isThinking ? 1.18 : isTranscribing ? 1.16 : visualState === "listening" ? 1.18 : visualState === "wake_listening" ? 1.08 : textReactiveActive ? 1.10 : isActive ? 1.06 : 0.88;
  const wave =
    isStopped ? 0.16 : isError ? 0.78 : isAlert ? 1.08 : isExecuting ? 1.14 : isSpeaking ? 1.28 : isThinking ? 0.90 : isTranscribing ? 1.02 : visualState === "listening" ? 1.12 : visualState === "wake_listening" ? 0.62 : textReactiveActive ? 0.78 : 0.16;
  const glitch = isError ? 0.75 : isAlert ? 0.22 : 0;
  const motion =
    motionBase *
    (isStopped ? 0.28 : isError ? 1.18 : isAlert ? 1.28 : isExecuting ? 1.42 : isSpeaking ? 1.32 : isThinking ? 1.14 : isTranscribing ? 1.12 : visualState === "listening" ? 1.08 : visualState === "wake_listening" ? 0.92 : textReactiveActive ? 0.98 : 0.38);
  const baseReactiveEnergy =
    isStopped ? 0.04 : isError ? 0.96 : isAlert ? 0.90 : isExecuting ? 0.86 : isSpeaking ? 1 : isThinking ? 0.80 : isTranscribing ? 0.58 : visualState === "listening" ? 0.62 : visualState === "wake_listening" ? 0.42 : 0.055;
  const stateReactiveEnergy = Math.min(1, baseReactiveEnergy + (textReactiveActive ? 0.24 : 0));
  const speakingSpikeEnergy = isStopped ? 0 : isSpeaking ? 1 : textReactiveActive ? 0.46 : 0;
  const radialSpikeEnergy = isStopped ? 0 : isError ? 1.22 : isAlert ? 1.08 : isSpeaking ? 1 : textReactiveActive ? 0.46 : 0;
  const thinkingTurbulence = isStopped ? 0 : isThinking ? 1 : isTranscribing ? 0.18 : 0;
  const listeningFocus = isStopped ? 0 : visualState === "listening" ? 1 : visualState === "wake_listening" ? 0.42 : 0;
  const transcribingReflow = isStopped ? 0 : isTranscribing ? 1 : 0;
  const spherePressure = isStopped ? 0.05 : isError ? 1.04 : isAlert ? 0.94 : isSpeaking ? 1 : isThinking ? 0.68 : isTranscribing ? 0.36 : visualState === "listening" ? 0.58 : visualState === "wake_listening" ? 0.30 : textReactiveActive ? 0.50 : 0.025;
  const emergentCoreConcentration = isStopped
    ? 0.01
    : isError
      ? 0.62
      : isAlert
        ? 0.56
        : isSpeaking
          ? 0.52
          : isThinking
            ? 0.42
            : isTranscribing
              ? 0.34
              : visualState === "listening"
                ? 0.48
                : visualState === "wake_listening"
                  ? 0.26
                  : textReactiveActive
                    ? 0.34
                    : 0.008;
  const sphereScaleMin =
    isStopped ? 0.48 : isError ? 0.88 : isAlert ? 0.82 : isSpeaking ? 0.86 : isThinking ? 0.80 : isTranscribing ? 0.76 : visualState === "listening" ? 0.62 : visualState === "wake_listening" ? 0.74 : 0.985;
  const sphereScaleMid =
    isStopped ? 0.56 : isError ? 1.18 : isAlert ? 1.08 : isSpeaking ? 1.08 : isThinking ? 0.98 : isTranscribing ? 0.88 : visualState === "listening" ? 0.74 : visualState === "wake_listening" ? 0.82 : 1.00;
  const sphereScaleMax =
    isStopped ? 0.64 : isError ? 1.56 : isAlert ? 1.42 : isSpeaking ? 1.48 : isThinking ? 1.24 : isTranscribing ? 1.02 : visualState === "listening" ? 0.88 : visualState === "wake_listening" ? 0.94 : textReactiveActive ? 1.12 : 1.018;
  const sphereAnimationSeconds =
    isStopped ? 9.5 : isError ? 0.92 : isAlert ? 1.18 : isSpeaking ? 1.10 : isThinking ? 1.85 : isTranscribing ? 2.35 : visualState === "listening" ? 2.05 : visualState === "wake_listening" ? 3.0 : 10.5;
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
    particleBudget: isStopped ? 760 : isSpeaking ? 2600 : isThinking ? 2460 : visualState === "listening" ? 2240 : isTranscribing ? 2300 : textReactiveActive ? 2200 : isActive ? 2100 : 1500,
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
