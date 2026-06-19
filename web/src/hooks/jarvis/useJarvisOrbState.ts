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
  const visualMotionActive = isListening || isTranscribing || isThinking || isSpeaking || isAlert || isExecuting;
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
    isStopped ? 0.72 : isError ? 1.08 : isAlert ? 1.22 : isExecuting ? 1.26 : isSpeaking ? 1.30 : isThinking ? 1.08 : isTranscribing ? 1.04 : visualState === "listening" ? 0.96 : visualState === "wake_listening" ? 0.82 : textReactiveActive ? 0.80 : isActive ? 0.76 : 0.70;
  const wave =
    isStopped ? 0.16 : isError ? 0.78 : isAlert ? 1.08 : isExecuting ? 1.14 : isSpeaking ? 1.28 : isThinking ? 0.58 : isTranscribing ? 0.54 : visualState === "listening" ? 0.28 : visualState === "wake_listening" ? 0.12 : textReactiveActive ? 0.14 : 0.035;
  const glitch = isError ? 0.75 : isAlert ? 0.22 : 0;
  const motion =
    motionBase *
    (isStopped ? 0.28 : isError ? 1.18 : isAlert ? 1.28 : isExecuting ? 1.42 : isSpeaking ? 1.32 : isThinking ? 0.82 : isTranscribing ? 0.72 : visualState === "listening" ? 0.42 : visualState === "wake_listening" ? 0.22 : textReactiveActive ? 0.24 : 0.10);
  const baseReactiveEnergy =
    isStopped ? 0.04 : isError ? 0.96 : isAlert ? 0.90 : isExecuting ? 0.86 : isSpeaking ? 1 : isThinking ? 0.46 : isTranscribing ? 0.36 : visualState === "listening" ? 0.18 : visualState === "wake_listening" ? 0.08 : 0.012;
  const stateReactiveEnergy = Math.min(1, baseReactiveEnergy + (textReactiveActive ? 0.08 : 0));
  const speakingSpikeEnergy = isStopped ? 0 : isSpeaking ? 1 : 0;
  const radialSpikeEnergy = isStopped ? 0 : isError ? 1.22 : isAlert ? 1.08 : isSpeaking ? 1 : 0;
  const thinkingTurbulence = isStopped ? 0 : isThinking ? 0.58 : isTranscribing ? 0.14 : 0;
  const listeningFocus = isStopped ? 0 : visualState === "listening" ? 0.24 : visualState === "wake_listening" ? 0.10 : 0;
  const transcribingReflow = isStopped ? 0 : isTranscribing ? 1 : 0;
  const spherePressure = isStopped ? 0.05 : isError ? 1.04 : isAlert ? 0.94 : isSpeaking ? 1 : isThinking ? 0.32 : isTranscribing ? 0.24 : visualState === "listening" ? 0.12 : visualState === "wake_listening" ? 0.04 : textReactiveActive ? 0.06 : 0.003;
  const emergentCoreConcentration = isStopped
    ? 0.01
    : isError
      ? 0.62
      : isAlert
        ? 0.56
        : isSpeaking
          ? 0.52
          : isThinking
            ? 0.32
            : isTranscribing
              ? 0.28
              : visualState === "listening"
                ? 0.20
                : visualState === "wake_listening"
                  ? 0.05
                  : textReactiveActive
                    ? 0.08
                    : 0.006;
  const sphereScaleMin =
    isStopped ? 0.48 : isError ? 0.88 : isAlert ? 0.82 : isSpeaking ? 0.86 : isThinking ? 0.90 : isTranscribing ? 0.86 : visualState === "listening" ? 0.94 : visualState === "wake_listening" ? 0.985 : 0.997;
  const sphereScaleMid =
    isStopped ? 0.56 : isError ? 1.18 : isAlert ? 1.08 : isSpeaking ? 1.08 : isThinking ? 0.985 : isTranscribing ? 0.94 : visualState === "listening" ? 0.965 : visualState === "wake_listening" ? 0.995 : 1.00;
  const sphereScaleMax =
    isStopped ? 0.64 : isError ? 1.56 : isAlert ? 1.42 : isSpeaking ? 1.48 : isThinking ? 1.08 : isTranscribing ? 1.02 : visualState === "listening" ? 0.988 : visualState === "wake_listening" ? 1.005 : textReactiveActive ? 1.012 : 1.003;
  const sphereAnimationSeconds =
    isStopped ? 9.5 : isError ? 0.92 : isAlert ? 1.18 : isSpeaking ? 1.10 : isThinking ? 4.2 : isTranscribing ? 3.6 : visualState === "listening" ? 8.5 : visualState === "wake_listening" ? 14.0 : 22.0;
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
    targetFrameMs: isStopped ? 90 : isError ? 42 : visualMotionActive ? 16 : textReactiveActive ? 42 : 80,
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
