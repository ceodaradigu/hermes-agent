import { useState } from "react";
import { Copy, History, MessageSquare, Mic, MicOff, RotateCcw, SendHorizontal, Square, Volume2, VolumeX } from "lucide-react";
import type { JarvisDashboardStatus } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { localVoiceStateLabels, previewVoiceSubtitle, sampleMissionCommand } from "./contracts";
import type { BrowserCapabilityState, JarvisConversationMessage, JarvisConversationMessageStatus, JarvisIntentPreview, JarvisVoiceTone, LocalVoiceLoopState } from "./types";
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
  browserVoiceUnlockRequired: boolean;
  phase12WakeState?: string;
  phase12WakeBackend?: string;
  phase12WakeActive?: boolean;
  canInterrupt: boolean;
  canCancel: boolean;
  onBegin: () => void;
  onCancel: () => void;
  onDraftActivity?: (draft: string) => void;
  voiceOutputEnabled: boolean;
  onVoiceOutputEnabledChange: (enabled: boolean) => void;
  onSpeakResponse: (text: string) => boolean;
  onUnlockBrowserVoice: () => void;
  onStopVoiceOutput: () => void;
  conversationMessages: JarvisConversationMessage[];
  conversationBusy?: boolean;
  conversationError?: string;
  onSubmitConversation?: (text: string) => void;
}

const starterPrompts = [
  "Dime qué puedes hacer ahora.",
  "Revisa el estado de JARVIS en lenguaje normal.",
  "Prepara el siguiente paso seguro del proyecto.",
  "Qué partes son reales y cuáles están en readiness.",
  "Ayúdame a crear un producto pequeño para validar.",
];

const statusLabels: Record<JarvisConversationMessageStatus, string> = {
  normal: "respuesta",
  preview: "vista previa",
  approval_required: "necesita aprobación",
  blocked: "bloqueado",
  unsupported: "no conectado",
  error: "error",
};

function conversationStatusVariant(status: JarvisConversationMessageStatus): "outline" | "warning" | "destructive" | "success" {
  if (status === "normal") return "success";
  if (status === "preview" || status === "approval_required") return "warning";
  if (status === "blocked" || status === "unsupported" || status === "error") return "destructive";
  return "outline";
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
  browserVoiceUnlockRequired,
  phase12WakeState = "",
  phase12WakeBackend = "",
  phase12WakeActive = false,
  canInterrupt,
  canCancel,
  onBegin,
  onCancel,
  onDraftActivity,
  voiceOutputEnabled,
  onVoiceOutputEnabledChange,
  onSpeakResponse,
  onUnlockBrowserVoice,
  onStopVoiceOutput,
  conversationMessages,
  conversationBusy = false,
  conversationError = "",
  onSubmitConversation,
}: JarvisSmartBarProps) {
  const [localDraft, setLocalDraft] = useState("");
  const [copiedMessageId, setCopiedMessageId] = useState("");
  const [voiceControlNotice, setVoiceControlNotice] = useState("");
  const messages = missionControl.conversation_preview?.messages ?? [];
  const lastResponse = messages.find((message) => message.speaker === "JARVIS")?.content ?? previewVoiceSubtitle;
  const latestUserMessage = [...conversationMessages].reverse().find((message) => message.role === "user");
  const latestAssistantMessage = [...conversationMessages].reverse().find((message) => message.role === "assistant");
  const visibleHistory = conversationMessages.length
    ? conversationMessages
    : messages.map((message, index) => ({
        id: `preview-${message.speaker}-${index}`,
        role: message.speaker === "David" ? "user" as const : "assistant" as const,
        content: message.content,
        status: "preview" as const,
        timestamp: "",
        source: "system" as const,
      }));
  const localVoiceBusy = isLocalVoiceBusy(localVoiceState);
  const startDisabled = sttSupport !== "supported" || localVoiceBusy || conversationActive;
  const stopDisabled = !canCancel;
  const sendDisabled = localDraft.trim().length === 0 || conversationBusy;
  const displayedTranscript = localDraft || latestUserMessage?.content || transcript || interimTranscript || valueText(missionControl.sample_command, sampleMissionCommand);
  const displayedResponse = conversationBusy
    ? "Estoy pensando y preparando una respuesta segura..."
    : latestAssistantMessage?.content || localVoiceResponse || lastResponse;
  const latestStatus: JarvisConversationMessageStatus = latestAssistantMessage?.status ?? (conversationBusy ? "preview" : "normal");
  const voiceOutputLabel = voiceOutputEnabled
    ? ttsSupport === "supported"
      ? "voz activa"
      : "voz pendiente"
    : "voz silenciada";
  const voiceOutputNotice = voiceOutputEnabled
    ? browserVoiceUnlockRequired
      ? "La voz del navegador está bloqueada hasta una primera pulsación."
      : ttsSupport === "supported"
        ? "Voz activa. JARVIS hablará por defecto."
        : "Voz activa, pero este navegador todavía no expone TTS."
    : "Voz silenciada por David. Las respuestas quedan visibles.";
  const stateLabel = localVoiceStateLabels[localVoiceState];
  const voiceSessionState = valueText(voiceSession?.state?.current_state ?? voiceSession?.current_state, "idle");
  const wakeListeningState = valueText(voiceSession?.state?.wake_listening_state ?? voiceSession?.wake_listening_state, "wake_listening_disabled");
  const wakeRuntimeEnabled = phase12WakeActive || wakeWordFlow?.state?.wake_runtime_enabled === true;
  const wakeBackendLabel = phase12WakeBackend && phase12WakeBackend !== "unavailable" ? phase12WakeBackend : "Vosk";
  const voiceModeExplanation = browserVoiceUnlockRequired
    ? "El navegador necesita una primera pulsación para desbloquear la voz. Pulsa aquí una vez y seguiré hablando automáticamente."
      : conversationActive
        ? "Conversación hablada activa: después de responder vuelvo a escucharte hasta que digas para, cállate o pulses stop. Wake no aprueba ni ejecuta acciones."
      : wakeRuntimeEnabled
        ? `Wake activo con ${wakeBackendLabel}. Di "JARVIS". "Hola JARVIS" queda como alias experimental según reconocimiento local. Estoy escuchando la frase de activación. No guardo audio bruto.`
        : phase12WakeState
          ? "Voz activa. Puedes hablar con JARVIS; si el wake local no está activo, el estado lo mostrará aquí."
          : "Voz activa. Puedes hablar con JARVIS.";
  const statusBadgeVariant: "destructive" | "warning" | "success" = localVoiceStateIsError(localVoiceState)
    ? "destructive"
    : localVoiceBusy
      ? "warning"
      : "success";

  function handleDraftChange(nextDraft: string) {
    setVoiceControlNotice("");
    setLocalDraft(nextDraft);
    onDraftActivity?.(nextDraft);
  }

  function handleSubmitDraft() {
    const trimmed = localDraft.trim();
    if (!trimmed || conversationBusy) return;
    setVoiceControlNotice("");
    onSubmitConversation?.(trimmed);
    setLocalDraft("");
    onDraftActivity?.("");
  }

  function handleRepeatResponse() {
    const text = latestAssistantMessage?.content?.trim() ?? "";
    if (!text) {
      setVoiceControlNotice("Todavía no tengo una respuesta para repetir.");
      return;
    }
    if (!voiceOutputEnabled) {
      setVoiceControlNotice("Activa la voz para repetir la respuesta.");
      return;
    }
    if (ttsSupport !== "supported") {
      setVoiceControlNotice("La voz no está disponible en este navegador.");
      return;
    }
    const didSpeak = onSpeakResponse(text);
    setVoiceControlNotice(didSpeak ? "Repitiendo la última respuesta de JARVIS." : "La voz no está disponible en este navegador.");
  }

  function handleStopVoiceOutput() {
    if (!canInterrupt) {
      setVoiceControlNotice("No hay voz reproduciéndose ahora.");
      return;
    }
    onStopVoiceOutput();
    setVoiceControlNotice("Voz detenida. La respuesta completa sigue por escrito.");
  }

  function handleVoiceOutputToggle() {
    const nextEnabled = !voiceOutputEnabled;
    onVoiceOutputEnabledChange(nextEnabled);
    setVoiceControlNotice(
      nextEnabled
        ? "Voz activa. JARVIS volverá a hablar por defecto cuando el navegador lo permita."
        : "Voz silenciada por David. Las respuestas quedan visibles.",
    );
  }

  async function handleCopyMessage(message: JarvisConversationMessage) {
    try {
      await navigator.clipboard?.writeText(message.content);
      setCopiedMessageId(message.id);
    } catch {
      setCopiedMessageId("");
    }
  }

  return (
    <section
      className="fixed bottom-3 left-1/2 z-50 w-[min(64rem,calc(100vw-1.25rem))] -translate-x-1/2"
      data-testid="jarvis-smart-bar"
      data-local-voice-loop="browser-controlled"
      data-local-voice-state={localVoiceState}
      data-smart-bar-mode="wake-first-voice-primary"
      data-smart-bar-contract="human-response-visible-details-folded-send-enabled"
    >
      {visibleHistory.length > 0 && (
        <details
          open
          className="mx-auto mb-2 w-[min(60rem,calc(100vw-1.5rem))] border border-[#e6fbff]/18 bg-[#000711]/84 px-4 py-3 shadow-[0_0_42px_rgba(230,251,255,0.08)] backdrop-blur"
          data-testid="jarvis-readable-history"
          data-history-scroll="full-response-wrap-scroll"
        >
          <summary className="flex cursor-pointer items-center justify-between gap-3 font-display text-xs uppercase tracking-[0.14em] text-cyan-100/70">
            <span className="flex items-center gap-2">
              <History className="h-4 w-4" />
              Historial / respuesta completa
            </span>
            <Badge variant={conversationBusy ? "warning" : conversationStatusVariant(latestStatus)}>
              {visibleHistory.length} turnos
            </Badge>
          </summary>
          <div className="mt-3 grid max-h-[30vh] gap-2 overflow-y-auto pr-1" data-testid="jarvis-full-conversation-scroll">
            {visibleHistory.map((message) => (
              <article
                key={message.id}
                className={message.role === "assistant" ? "border border-cyan-100/12 bg-[#00101b]/78 p-3" : "border border-cyan-100/8 bg-[#000711]/72 p-3"}
                data-testid={message.role === "assistant" ? "jarvis-full-assistant-message" : "jarvis-full-user-message"}
              >
                <div className="mb-2 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <p className="font-display text-[0.68rem] uppercase tracking-[0.12em] text-cyan-200/62">{message.role === "user" ? "David" : "JARVIS"}</p>
                    <Badge variant={conversationStatusVariant(message.status)}>{statusLabels[message.status]}</Badge>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => void handleCopyMessage(message)}
                    className="h-7 rounded-full border-cyan-100/14 bg-cyan-300/[0.025] px-2 text-[0.68rem] text-cyan-50/72"
                  >
                    <Copy className="h-3.5 w-3.5" />
                    {copiedMessageId === message.id ? "copiado" : "copiar"}
                  </Button>
                </div>
                <p className="select-text whitespace-pre-wrap break-words font-mono-ui text-sm leading-6 text-cyan-50/88">{message.content}</p>
              </article>
            ))}
          </div>
        </details>
      )}

      <div className="mx-auto mb-2 grid w-[min(58rem,calc(100vw-1.5rem))] gap-2 md:grid-cols-[0.9fr_1.1fr]">
        <div className="min-w-0 border border-cyan-100/12 bg-[#000711]/76 px-3 py-2 shadow-[0_0_22px_rgba(230,251,255,0.05)] backdrop-blur">
          <p className="font-display text-[0.64rem] uppercase tracking-[0.16em] text-cyan-100/52">Tú · transcripción temporal local</p>
          <p className="mt-1 truncate font-mono-ui text-xs text-cyan-50">{displayedTranscript}</p>
        </div>
        <div className="min-w-0 border border-[#e6fbff]/22 bg-[#000711]/84 px-3 py-2 shadow-[0_0_34px_rgba(230,251,255,0.10)] backdrop-blur">
          <p className="font-display text-[0.64rem] uppercase tracking-[0.16em] text-[#e6fbff]/66">JARVIS · respuesta humana corta</p>
          <p className="mt-1 truncate font-mono-ui text-xs text-cyan-50">{displayedResponse}</p>
          <p className="sr-only">respuesta temporal local controlada · tono {jarvisTone}</p>
        </div>
      </div>

      <div className="relative rounded-full border border-[#e6fbff]/34 bg-[#00030a]/96 p-2 shadow-[0_0_88px_rgba(230,251,255,0.18),inset_0_0_52px_rgba(230,251,255,0.055)] backdrop-blur-xl">
        <div className="absolute -inset-2 -z-10 rounded-full bg-[#e6fbff]/10 blur-2xl" />
        <div className="flex min-w-0 items-center gap-3 rounded-full border border-[#e6fbff]/18 bg-[#000711]/94 px-4 py-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-[#e6fbff]/30 bg-[#e6fbff]/[0.07] shadow-[0_0_32px_rgba(230,251,255,0.22)]">
            <MessageSquare className="h-5 w-5 text-[#e6fbff]" />
          </div>
          <textarea
            aria-label="Barra inteligente inferior para escribir a JARVIS"
            value={localDraft}
            onChange={(event) => {
              handleDraftChange(event.target.value);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleSubmitDraft();
              }
            }}
            rows={1}
            placeholder={conversationActive ? "Conversación hablada activa. También puedes escribir aquí." : "Escribe a JARVIS..."}
            className="max-h-24 min-h-10 min-w-0 flex-1 resize-none bg-transparent py-2 font-mono-ui text-base leading-6 text-cyan-50 outline-none placeholder:text-cyan-100/36 sm:text-lg"
          />
          <Button
            disabled={startDisabled}
            aria-disabled={startDisabled}
            aria-label="Hablar ahora con JARVIS desde el navegador"
            title="Hablar ahora"
            type="button"
            variant="outline"
            size="icon"
            onClick={onBegin}
            className="rounded-full border-[#e6fbff]/24 bg-[#e6fbff]/[0.045] text-[#e6fbff] disabled:opacity-45"
          >
            {sttSupport === "supported" ? <Mic className="h-4 w-4" /> : <MicOff className="h-4 w-4" />}
          </Button>
          <Button
            disabled={stopDisabled}
            aria-disabled={stopDisabled}
            aria-label={canInterrupt ? "Interrumpir voz de JARVIS y cerrar conversación hablada" : "Detener conversación, escucha o habla de JARVIS"}
            title={canInterrupt ? "Interrumpir voz" : "Stop/cancel conversación"}
            type="button"
            variant="outline"
            size="icon"
            onClick={onCancel}
            className="rounded-full border-red-300/35 bg-red-950/25 text-red-100 disabled:opacity-40"
          >
            <Square className="h-4 w-4" />
          </Button>
          <Button
            disabled={sendDisabled}
            aria-disabled={sendDisabled}
            aria-label={conversationBusy ? "JARVIS está pensando" : "Enviar mensaje a JARVIS"}
            title={conversationBusy ? "Pensando" : "Enviar"}
            type="button"
            variant="outline"
            size="icon"
            onClick={handleSubmitDraft}
            className="rounded-full border-cyan-100/28 bg-cyan-300/[0.06] text-cyan-50 disabled:opacity-40"
          >
            <SendHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="mx-auto mt-2 grid w-[min(60rem,calc(100vw-1.5rem))] gap-2 border border-cyan-100/10 bg-[#000711]/74 px-4 py-2 backdrop-blur md:grid-cols-[auto_1fr_auto]">
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant={conversationStatusVariant(latestStatus)}>{conversationBusy ? "pensando..." : statusLabels[latestStatus]}</Badge>
          <Badge variant={conversationActive ? "warning" : statusBadgeVariant}>
            voz {conversationActive ? "hablada activa" : "principal"}
          </Badge>
          <Badge variant={voiceOutputEnabled && ttsSupport === "supported" ? "success" : voiceOutputEnabled ? "warning" : "outline"}>
            {voiceOutputLabel}
          </Badge>
          <Badge variant={statusBadgeVariant}>{stateLabel}</Badge>
        </div>
        <p className="min-w-0 font-mono-ui text-[0.72rem] text-cyan-100/54">
          {conversationError ||
            voiceControlNotice ||
            (conversationActive
              ? voiceModeExplanation
              : `${voiceOutputNotice} ${voiceModeExplanation}`)}
        </p>
        <div className="flex items-center justify-end gap-1.5">
          {browserVoiceUnlockRequired && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onUnlockBrowserVoice}
              className="h-8 rounded-full border-amber-200/34 bg-amber-300/[0.08] px-2 text-amber-50"
            >
              <Volume2 className="h-3.5 w-3.5" />
              desbloquear voz
            </Button>
          )}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleVoiceOutputToggle}
            className="h-8 rounded-full border-cyan-100/14 bg-cyan-300/[0.025] px-2 text-cyan-50/72"
          >
            {voiceOutputEnabled ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
            {voiceOutputEnabled ? "mutear" : "activar voz"}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleRepeatResponse}
            className="h-8 rounded-full border-cyan-100/14 bg-cyan-300/[0.025] px-2 text-cyan-50/72"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            repetir
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleStopVoiceOutput}
            className="h-8 rounded-full border-red-300/24 bg-red-950/20 px-2 text-red-100/78"
          >
            <Square className="h-3.5 w-3.5" />
            detener voz
          </Button>
        </div>
        <details className="text-right md:col-span-3">
          <summary className="cursor-pointer font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-100/60">
            detalles
          </summary>
          <div className="mt-2 max-w-sm text-left font-mono-ui text-[0.68rem] text-cyan-100/52 md:text-right">
            <p>sesión voz {conversationActive ? "conversation_active" : voiceSessionState}</p>
            <p>wake {wakeListeningState}</p>
            <p>STT navegador {capabilityText(sttSupport)}</p>
            <p>voz {selectedVoiceName || capabilityText(ttsSupport)}</p>
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
            <p>can_interrupt {canInterrupt ? "true" : "false"} · can_cancel {canCancel ? "true" : "false"}</p>
            <p>borrador local {localDraft ? "presente/no enviado" : "vacío"}</p>
            <p>No puedo hacer eso, David. Las credenciales y secretos están protegidos.</p>
            <p>wake_runtime_enabled {wakeRuntimeEnabled ? "true" : "false"} · wake no aprueba · wake no ejecuta · voice approval disabled unless authenticated/gated/audited.</p>
            <p>Soporte depende del navegador; SpeechRecognition puede usar servicios del navegador. No se guarda audio bruto, no se envía audio al backend y no se transcribe todo.</p>
          </div>
        </details>
      </div>

      <div className="mx-auto mt-2 flex w-[min(60rem,calc(100vw-1.5rem))] gap-2 overflow-x-auto pb-1">
        {starterPrompts.map((prompt) => (
          <Button
            key={prompt}
            disabled={conversationBusy}
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handleDraftChange(prompt)}
            className="h-8 shrink-0 rounded-full border-cyan-100/14 bg-[#000711]/76 px-3 text-xs text-cyan-50/78 disabled:opacity-40"
          >
            {prompt}
          </Button>
        ))}
      </div>

      <details className="mx-auto mt-2 w-fit border border-cyan-100/10 bg-[#000711]/76 px-5 py-2 backdrop-blur" data-testid="jarvis-folded-history">
        <summary className="flex cursor-pointer items-center gap-2 font-display text-xs uppercase tracking-[0.14em] text-cyan-100/64">
          <History className="h-4 w-4" />
          Historial plegado / folded history
        </summary>
        <div className="mt-3 grid max-h-40 w-[min(42rem,calc(100vw-3rem))] gap-2 overflow-auto">
          <div className="grid gap-2 border border-cyan-100/9 bg-[#000711]/55 p-3">
            <p className="font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-200/55">transcripción temporal local</p>
            <p className="truncate font-mono-ui text-xs text-cyan-50">{displayedTranscript}</p>
            <p className="font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-200/55">respuesta temporal local controlada</p>
            <p className="truncate font-mono-ui text-xs text-cyan-50">{displayedResponse}</p>
          </div>
          <div className="grid gap-2">
            {visibleHistory.map((message) => (
              <div key={message.id} className="border border-cyan-100/8 bg-[#000711]/70 p-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-display text-[0.68rem] uppercase tracking-[0.12em] text-cyan-200/50">{message.role === "user" ? "David" : "JARVIS"}</p>
                  <Badge variant={conversationStatusVariant(message.status)}>{statusLabels[message.status]}</Badge>
                </div>
                <p className="mt-1 whitespace-pre-wrap font-mono-ui text-xs text-cyan-50/80">{message.content}</p>
              </div>
            ))}
          </div>
        </div>
      </details>
    </section>
  );
}
