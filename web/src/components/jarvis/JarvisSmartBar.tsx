import { History, MessageSquare, Mic, MicOff, SendHorizontal, Square } from "lucide-react";
import type { JarvisDashboardStatus } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { localVoiceStateLabels, previewVoiceSubtitle, sampleMissionCommand } from "./contracts";
import type { BrowserCapabilityState, JarvisIntentPreview, JarvisVoiceTone, LocalVoiceLoopState } from "./types";
import { capabilityText, isLocalVoiceBusy, localVoiceStateIsError, valueText } from "./utils";

interface JarvisSmartBarProps {
  missionControl: NonNullable<JarvisDashboardStatus["mission_control"]>;
  voiceSession?: JarvisDashboardStatus["voice_session"];
  wakeWordFlow?: JarvisDashboardStatus["wake_word_flow"];
  localVoiceState: LocalVoiceLoopState;
  jarvisTone: JarvisVoiceTone;
  conversationActive: boolean;
  transcript: string;
  interimTranscript: string;
  localVoiceResponse: string;
  localVoiceIntent: string;
  localVoiceRisk: string;
  intentPreview: JarvisIntentPreview;
  sttSupport: BrowserCapabilityState;
  ttsSupport: BrowserCapabilityState;
  capabilityNotice: string;
  selectedVoiceName: string;
  voiceQualityNotice: string;
  onBegin: () => void;
  onCancel: () => void;
}

export function JarvisSmartBar({
  missionControl,
  voiceSession,
  wakeWordFlow,
  localVoiceState,
  jarvisTone,
  conversationActive,
  transcript,
  interimTranscript,
  localVoiceResponse,
  localVoiceIntent,
  localVoiceRisk,
  intentPreview,
  sttSupport,
  ttsSupport,
  capabilityNotice,
  selectedVoiceName,
  voiceQualityNotice,
  onBegin,
  onCancel,
}: JarvisSmartBarProps) {
  const messages = missionControl.conversation_preview?.messages ?? [];
  const lastResponse = messages.find((message) => message.speaker === "JARVIS")?.content ?? previewVoiceSubtitle;
  const localVoiceBusy = isLocalVoiceBusy(localVoiceState);
  const startDisabled = sttSupport !== "supported" || localVoiceBusy || conversationActive;
  const stopDisabled = !conversationActive && !localVoiceBusy && localVoiceState === "idle";
  const displayedTranscript = transcript || interimTranscript || valueText(missionControl.sample_command, sampleMissionCommand);
  const displayedResponse = localVoiceResponse || lastResponse;
  const stateLabel = localVoiceStateLabels[localVoiceState];
  const voiceSessionState = valueText(voiceSession?.state?.current_state ?? voiceSession?.current_state, "idle");
  const wakeListeningState = valueText(voiceSession?.state?.wake_listening_state ?? voiceSession?.wake_listening_state, "wake_listening_disabled");
  const wakeAvailable = wakeListeningState === "wake_listening_available";
  const wakeRuntimeEnabled = wakeWordFlow?.state?.wake_runtime_enabled === true;
  const statusBadgeVariant: "destructive" | "warning" | "success" = localVoiceStateIsError(localVoiceState)
    ? "destructive"
    : localVoiceBusy
      ? "warning"
      : "success";

  return (
    <section
      className="fixed bottom-3 left-1/2 z-50 w-[min(58rem,calc(100vw-2rem))] -translate-x-1/2"
      data-testid="jarvis-smart-bar"
      data-local-voice-loop="browser-controlled"
      data-local-voice-state={localVoiceState}
    >
      <div className="mb-3 grid gap-2">
        <div className="ml-auto max-w-[82%] rounded-[2px] border border-cyan-300/24 bg-[#031426]/82 px-4 py-2 shadow-[0_0_30px_rgba(34,211,238,0.10)] backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <p className="font-display text-[0.68rem] uppercase tracking-[0.16em] text-cyan-200">Tú</p>
            <p className="font-mono-ui text-[0.68rem] text-cyan-100/50">transcripción temporal local</p>
          </div>
          <p className="mt-1 truncate font-mono-ui text-xs text-cyan-50">{displayedTranscript}</p>
        </div>
        <div className="max-w-[82%] rounded-[2px] border border-cyan-300/24 bg-[#031426]/82 px-4 py-2 shadow-[0_0_30px_rgba(34,211,238,0.10)] backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <p className="font-display text-[0.68rem] uppercase tracking-[0.16em] text-cyan-200">JARVIS</p>
            <p className="font-mono-ui text-[0.68rem] text-cyan-100/50">respuesta temporal local controlada · tono {jarvisTone}</p>
          </div>
          <p className="mt-1 truncate font-mono-ui text-xs text-cyan-50">{displayedResponse}</p>
        </div>
      </div>

      <div className="relative rounded-full border border-cyan-300/35 bg-[#020b17]/95 p-2 shadow-[0_0_80px_rgba(34,211,238,0.24),inset_0_0_52px_rgba(34,211,238,0.06)] backdrop-blur-xl">
        <div className="absolute -inset-2 -z-10 rounded-full bg-cyan-300/10 blur-2xl" />
        <div className="flex min-w-0 items-center gap-3 rounded-full border border-cyan-300/18 bg-[#061629]/92 px-4 py-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-cyan-300/30 bg-cyan-300/10 shadow-[0_0_30px_rgba(34,211,238,0.22)]">
            <MessageSquare className="h-5 w-5 text-cyan-100" />
          </div>
          <input
            disabled
            readOnly
            aria-label="Barra inteligente inferior para escribir a JARVIS"
            value={interimTranscript || transcript}
            placeholder={conversationActive ? "Conversación manual activa. Habla cuando quieras o pulsa stop." : "Pulsa el micrófono una vez para abrir conversación manual local..."}
            className="min-w-0 flex-1 bg-transparent font-mono-ui text-lg text-cyan-50 outline-none placeholder:text-cyan-100/36 disabled:text-cyan-100/45"
          />
          <Button
            disabled={startDisabled}
            aria-disabled={startDisabled}
            aria-label="Activar conversación manual local de JARVIS"
            title="Conversación manual continua"
            type="button"
            variant="outline"
            size="icon"
            onClick={onBegin}
            className="rounded-full border-cyan-300/25 bg-cyan-300/[0.04] text-cyan-100 disabled:opacity-45"
          >
            {sttSupport === "supported" ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
          </Button>
          <Button
            disabled={stopDisabled}
            aria-disabled={stopDisabled}
            aria-label="Detener conversación manual, escucha o habla de JARVIS"
            title="Stop/cancel conversación manual"
            type="button"
            variant="outline"
            size="icon"
            onClick={onCancel}
            className="rounded-full border-red-300/35 bg-red-950/25 text-red-100 disabled:opacity-40"
          >
            <Square className="h-4 w-4" />
          </Button>
          <Button disabled aria-disabled="true" type="button" variant="outline" size="icon" className="rounded-full border-cyan-300/25 bg-cyan-300/[0.04] text-cyan-100">
            <SendHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="mx-auto mt-2 grid w-[min(56rem,calc(100vw-2rem))] gap-2 border border-cyan-300/16 bg-[#020b17]/82 px-4 py-2 backdrop-blur md:grid-cols-[auto_1fr_auto]">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={conversationActive ? "warning" : statusBadgeVariant}>
            Conversación manual {conversationActive ? "activa" : "en reposo"}
          </Badge>
          <Badge variant={conversationActive ? "warning" : "outline"}>sesión voz: {conversationActive ? "conversation_active" : voiceSessionState}</Badge>
          <Badge variant={wakeAvailable ? "success" : "outline"}>wake: {wakeListeningState}</Badge>
          <Badge variant={statusBadgeVariant}>estado: {stateLabel}</Badge>
          <Badge variant="outline">STT navegador: {capabilityText(sttSupport)}</Badge>
          <Badge variant="outline">voz: {selectedVoiceName || capabilityText(ttsSupport)}</Badge>
        </div>
        <p className="min-w-0 font-mono-ui text-[0.72rem] text-cyan-100/58">
          {conversationActive
            ? "JARVIS vuelve a escuchar al terminar de hablar mientras este modo siga activo. Stop/cancel cierra la conversación."
            : `Wake ${wakeAvailable ? "disponible por dependencia" : "desactivado/no disponible"} no equivale a conversación activa. Micrófono manual; no hay transcripción continua ni Hermes directo.`}
        </p>
        <details className="text-right">
          <summary className="cursor-pointer font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-100/60">
            intent preview
          </summary>
          <div className="mt-2 max-w-sm text-left font-mono-ui text-[0.68rem] text-cyan-100/52 md:text-right">
            <p>intent_detected {intentPreview.intent_detected}</p>
            <p>confidence {valueText(intentPreview.confidence)}</p>
            <p>risk_level {intentPreview.risk_level}</p>
            <p>approval_level {valueText(intentPreview.approval_level, "direct")}</p>
            <p>requires_approval {intentPreview.requires_approval ? "true" : "false"}</p>
            <p>can_prepare_preview {intentPreview.can_prepare_preview ? "true" : "false"}</p>
            <p>hermes_dispatch_allowed {intentPreview.hermes_dispatch_allowed === true ? "true" : "false"}</p>
            <p>cannot_execute_reason {intentPreview.cannot_execute_reason}</p>
            <p>suggested_next_action {intentPreview.suggested_next_action}</p>
            <p>{capabilityNotice}</p>
            <p>{voiceQualityNotice}</p>
            <p>intent {localVoiceIntent} · risk {localVoiceRisk}</p>
            <p>wake_runtime_enabled {wakeRuntimeEnabled ? "true" : "false"} · wake no aprueba · wake no ejecuta · voice approval disabled unless authenticated/gated/audited.</p>
            <p>Soporte depende del navegador; SpeechRecognition puede usar servicios del navegador. No se guarda audio bruto, no se envía audio al backend y no se transcribe todo.</p>
          </div>
        </details>
      </div>

      <details className="mx-auto mt-2 w-fit border border-cyan-300/16 bg-[#020b17]/80 px-5 py-2 backdrop-blur" data-testid="jarvis-folded-history">
        <summary className="flex cursor-pointer items-center gap-2 font-display text-xs uppercase tracking-[0.14em] text-cyan-100/64">
          <History className="h-4 w-4" />
          Historial plegado / folded history
        </summary>
        <div className="mt-3 grid max-h-40 w-[min(42rem,calc(100vw-3rem))] gap-2 overflow-auto">
          <div className="grid gap-2 border border-cyan-300/15 bg-[#071629]/55 p-3">
            <p className="font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-200/55">transcripción temporal local</p>
            <p className="truncate font-mono-ui text-xs text-cyan-50">{displayedTranscript}</p>
            <p className="font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-200/55">respuesta temporal local controlada</p>
            <p className="truncate font-mono-ui text-xs text-cyan-50">{displayedResponse}</p>
          </div>
          <div className="grid gap-2">
            {messages.map((message, index) => (
              <div key={`${message.speaker}-${index}`} className="border border-cyan-300/10 bg-[#020717]/70 p-2">
                <p className="font-display text-[0.68rem] uppercase tracking-[0.12em] text-cyan-200/50">{message.speaker}</p>
                <p className="font-mono-ui text-xs text-cyan-50/80">{message.content}</p>
              </div>
            ))}
          </div>
        </div>
      </details>
    </section>
  );
}
