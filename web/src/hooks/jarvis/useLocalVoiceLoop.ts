import { useEffect, useRef, useState } from "react";
import {
  LOCAL_VOICE_CONVERSATION_TIMEOUT_MS,
  LOCAL_VOICE_RESTART_DELAY_MS,
} from "./voiceLoopTiming";
import { jarvisToneProfiles, UNKNOWN } from "@/components/jarvis/contracts";
import type {
  BrowserCapabilityState,
  BrowserSpeechRecognition,
  JarvisIntentPreview,
  JarvisVoiceTone,
  LocalJarvisVoiceResponse,
  LocalVoiceLoopController,
  LocalVoiceLoopState,
} from "@/components/jarvis/types";
import { buildLocalJarvisResponse } from "@/components/jarvis/utils";
import { getBrowserSpeechRecognitionConstructor } from "./useJarvisSpeechRecognition";
import {
  browserTtsAvailable,
  selectedVoiceNotice,
  selectPreferredSpanishVoice,
} from "./useJarvisSpeechSynthesis";

interface LocalVoiceLoopOptions {
  onIntentSubmitted?: (text: string) => LocalJarvisVoiceResponse | null | void | Promise<LocalJarvisVoiceResponse | null | void>;
}

const VOICE_OUTPUT_STORAGE_KEY = "jarvis.voiceOutputEnabled";
const BROWSER_TTS_INTERACTION_PROMPT =
  "El navegador necesita una primera pulsación para desbloquear la voz. Pulsa aquí una vez y seguiré hablando automáticamente.";

function readVoiceOutputPreference(): boolean {
  if (typeof window === "undefined") return true;
  try {
    const stored = window.localStorage.getItem(VOICE_OUTPUT_STORAGE_KEY);
    if (stored === null) return true;
    return stored !== "false";
  } catch {
    return true;
  }
}

function writeVoiceOutputPreference(enabled: boolean) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(VOICE_OUTPUT_STORAGE_KEY, enabled ? "true" : "false");
  } catch {
    return;
  }
}

function normalizeVoiceControlPhrase(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLocaleLowerCase("es-ES");
}

function isStopVoicePhrase(value: string): boolean {
  return ["para", "jarvis para", "callate", "jarvis callate"].includes(normalizeVoiceControlPhrase(value));
}

export function useLocalVoiceLoop(options: LocalVoiceLoopOptions = {}): LocalVoiceLoopController {
  const initialVoiceOutputEnabledRef = useRef(readVoiceOutputPreference());
  const defaultIntentPreview: JarvisIntentPreview = {
    intent_detected: "idle",
    confidence: 0,
    risk_level: "none",
    approval_level: "direct",
    requires_approval: false,
    can_prepare_preview: false,
    cannot_execute_reason: "Sin petición activa.",
    suggested_next_action: "Habla con JARVIS o escribe una petición concreta.",
    hermes_dispatch_allowed: false,
  };
  const [localVoiceState, setLocalVoiceState] = useState<LocalVoiceLoopState>("idle");
  const [jarvisTone, setJarvisTone] = useState<JarvisVoiceTone>("calmado");
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [localVoiceResponse, setLocalVoiceResponse] = useState("Voz activa. Puedes hablar con JARVIS.");
  const [localVoiceIntent, setLocalVoiceIntent] = useState("idle");
  const [localVoiceRisk, setLocalVoiceRisk] = useState("none");
  const [intentPreview, setIntentPreview] = useState<JarvisIntentPreview>(defaultIntentPreview);
  const [sttSupport, setSttSupport] = useState<BrowserCapabilityState>("unknown");
  const [ttsSupport, setTtsSupport] = useState<BrowserCapabilityState>("unknown");
  const [capabilityNotice, setCapabilityNotice] = useState("Detectando soporte de voz del navegador.");
  const [conversationActive, setConversationActive] = useState(false);
  const [selectedVoiceName, setSelectedVoiceName] = useState("");
  const [voiceQualityNotice, setVoiceQualityNotice] = useState("Detectando voces del navegador.");
  // PR175 compatibility marker: const [voiceOutputEnabled, setVoiceOutputEnabledState] = useState(true)
  const [voiceOutputEnabled, setVoiceOutputEnabledState] = useState(initialVoiceOutputEnabledRef.current);
  const [browserVoiceUnlockRequired, setBrowserVoiceUnlockRequired] = useState(false);
  const [speechOutputActive, setSpeechOutputActive] = useState(false);
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const finalTranscriptRef = useRef("");
  const cancelledRef = useRef(false);
  const recoverableSpeechErrorRef = useRef(false);
  const conversationActiveRef = useRef(false);
  const conversationExpiresAtRef = useRef(0);
  const timersRef = useRef<number[]>([]);
  const selectedVoiceNameRef = useRef("");
  const ttsSupportRef = useRef<BrowserCapabilityState>("unknown");
  const speakingRef = useRef(false);
  const ttsQueueRef = useRef<Array<{ text: string; tone: JarvisVoiceTone }>>([]);
  const ttsTurnRef = useRef(0);
  const lastSpokenTextRef = useRef("");
  const blockedSpeechRef = useRef<Array<{ text: string; tone: JarvisVoiceTone }>>([]);
  // PR175 compatibility marker: const voiceOutputEnabledRef = useRef(true)
  const voiceOutputEnabledRef = useRef(initialVoiceOutputEnabledRef.current);
  const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const onIntentSubmittedRef = useRef(options.onIntentSubmitted);

  useEffect(() => {
    onIntentSubmittedRef.current = options.onIntentSubmitted;
  }, [options.onIntentSubmitted]);

  function setConversationActiveFlag(active: boolean) {
    conversationActiveRef.current = active;
    setConversationActive(active);
  }

  function clearLocalVoiceTimers() {
    timersRef.current.forEach((timerId) => window.clearTimeout(timerId));
    timersRef.current = [];
  }

  function scheduleLocalVoiceStep(callback: () => void, delay: number) {
    const timerId = window.setTimeout(() => {
      timersRef.current = timersRef.current.filter((item) => item !== timerId);
      callback();
    }, delay);
    timersRef.current.push(timerId);
  }

  function cancelBrowserSpeechOutput({ clearBlocked = true }: { clearBlocked?: boolean } = {}) {
    ttsQueueRef.current = [];
    speakingRef.current = false;
    currentUtteranceRef.current = null;
    if (clearBlocked) {
      blockedSpeechRef.current = [];
      setBrowserVoiceUnlockRequired(false);
    }
    setSpeechOutputActive(false);
    ttsTurnRef.current += 1;
    if (browserTtsAvailable()) {
      window.speechSynthesis.cancel();
    }
  }

  function refreshBrowserVoiceSelection() {
    if (!browserTtsAvailable()) {
      selectedVoiceNameRef.current = "";
      setSelectedVoiceName("");
      setVoiceQualityNotice("speechSynthesis no está disponible; JARVIS responderá solo en texto.");
      return;
    }
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = selectPreferredSpanishVoice(voices);
    selectedVoiceNameRef.current = preferredVoice?.name ?? "";
    setSelectedVoiceName(preferredVoice?.name ?? "");
    setVoiceQualityNotice(selectedVoiceNotice(preferredVoice, voices.length));
  }

  function getPreferredBrowserVoice(): SpeechSynthesisVoice | null {
    if (!browserTtsAvailable()) return null;
    const voices = window.speechSynthesis.getVoices();
    const selectedVoice = voices.find((voice) => voice.name === selectedVoiceNameRef.current);
    return selectedVoice ?? selectPreferredSpanishVoice(voices);
  }

  function isLikelyTtsEcho(candidate: string) {
    const normalizedCandidate = candidate.replace(/\s+/g, " ").trim().toLocaleLowerCase("es-ES");
    const normalizedLastSpoken = lastSpokenTextRef.current.replace(/\s+/g, " ").trim().toLocaleLowerCase("es-ES");
    if (!normalizedCandidate || !normalizedLastSpoken) return false;
    if (normalizedCandidate === normalizedLastSpoken) return true;
    return normalizedLastSpoken.length > 32 && normalizedLastSpoken.includes(normalizedCandidate);
  }

  function queueNextLocalVoiceTurn(message = "Listo. Te escucho de nuevo.", delay = LOCAL_VOICE_RESTART_DELAY_MS) {
    if (!conversationActiveRef.current || cancelledRef.current) {
      setLocalVoiceState("idle");
      return;
    }

    if (Date.now() > conversationExpiresAtRef.current) {
      setConversationActiveFlag(false);
      setLocalVoiceState("stopped");
      setJarvisTone("calmado");
      setLocalVoiceResponse("Pauso la conversación hablada por seguridad. Puedes escribir o volver a despertar a JARVIS cuando quieras.");
      setLocalVoiceIntent("voice_conversation_timeout");
      setLocalVoiceRisk("none");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "voice_conversation_timeout",
        suggested_next_action: "Escribe o vuelve a despertar a JARVIS cuando quieras.",
      });
      return;
    }

    setLocalVoiceResponse(message);
    scheduleLocalVoiceStep(() => {
      if (!conversationActiveRef.current || cancelledRef.current) return;
      startLocalVoiceRecognitionCycle({ continued: true });
    }, delay);
  }

  function drainLocalTtsQueue() {
    if (speakingRef.current) return;
    if (!browserTtsAvailable()) {
      setLocalVoiceState("not_supported");
      setCapabilityNotice("speechSynthesis no está disponible; dejo la respuesta visible y mantengo el modo hablado listo cuando el navegador lo permita.");
      queueNextLocalVoiceTurn("No tengo voz TTS disponible aquí, pero sigo listo para escucharte.", 900);
      return;
    }

    const next = ttsQueueRef.current.shift();
    if (!next) return;

    const turnId = ttsTurnRef.current + 1;
    ttsTurnRef.current = turnId;
    const utterance = new SpeechSynthesisUtterance(next.text);
    const profile = jarvisToneProfiles[next.tone];
    const preferredVoice = getPreferredBrowserVoice();
    currentUtteranceRef.current = utterance;
    lastSpokenTextRef.current = next.text;
    if (preferredVoice) {
      utterance.voice = preferredVoice;
      utterance.lang = preferredVoice.lang || "es-ES";
      selectedVoiceNameRef.current = preferredVoice.name;
      setSelectedVoiceName(preferredVoice.name);
      setVoiceQualityNotice(selectedVoiceNotice(preferredVoice, window.speechSynthesis.getVoices().length));
    } else {
      utterance.lang = "es-ES";
      setVoiceQualityNotice("No hay voz española clara; usando fallback del navegador.");
    }
    utterance.rate = profile.rate;
    utterance.pitch = profile.pitch;
    utterance.volume = profile.volume;
    const handleSpeechEnd = () => {
      if (turnId !== ttsTurnRef.current) return;
      speakingRef.current = false;
      currentUtteranceRef.current = null;
      setSpeechOutputActive(false);
      setBrowserVoiceUnlockRequired(false);
      blockedSpeechRef.current = blockedSpeechRef.current.filter((item) => item.text !== next.text);
      if (ttsQueueRef.current.length > 0) {
        drainLocalTtsQueue();
        return;
      }
      if (conversationActiveRef.current) {
        queueNextLocalVoiceTurn("Te escucho de nuevo. Habla cuando quieras o pulsa stop.", LOCAL_VOICE_RESTART_DELAY_MS);
        return;
      }
      setLocalVoiceState("idle");
    };
    const autoplayGuardTimer = window.setTimeout(() => {
      timersRef.current = timersRef.current.filter((item) => item !== autoplayGuardTimer);
      if (turnId !== ttsTurnRef.current || speakingRef.current || currentUtteranceRef.current !== utterance) return;
      blockedSpeechRef.current = [{ text: next.text, tone: next.tone }];
      setBrowserVoiceUnlockRequired(true);
      setCapabilityNotice(BROWSER_TTS_INTERACTION_PROMPT);
      setLocalVoiceResponse(BROWSER_TTS_INTERACTION_PROMPT);
    }, 1200);
    timersRef.current.push(autoplayGuardTimer);
    const clearAutoplayGuard = () => {
      window.clearTimeout(autoplayGuardTimer);
      timersRef.current = timersRef.current.filter((item) => item !== autoplayGuardTimer);
    };
    utterance.onstart = () => {
      if (turnId !== ttsTurnRef.current) return;
      clearAutoplayGuard();
      speakingRef.current = true;
      setSpeechOutputActive(true);
      setLocalVoiceState("speaking");
    };
    utterance.onerror = () => {
      if (turnId !== ttsTurnRef.current) return;
      clearAutoplayGuard();
      speakingRef.current = false;
      currentUtteranceRef.current = null;
      setSpeechOutputActive(false);
      blockedSpeechRef.current = [{ text: next.text, tone: next.tone }];
      setLocalVoiceResponse(BROWSER_TTS_INTERACTION_PROMPT);
      setBrowserVoiceUnlockRequired(true);
      setLocalVoiceState("error");
      setCapabilityNotice(BROWSER_TTS_INTERACTION_PROMPT);
      queueNextLocalVoiceTurn(BROWSER_TTS_INTERACTION_PROMPT, 1000);
    };
    utterance.onend = () => {
      clearAutoplayGuard();
      handleSpeechEnd();
    };
    setSpeechOutputActive(true);
    window.speechSynthesis.speak(utterance);
  }

  function speakLocalJarvisResponse(text: string, tone: JarvisVoiceTone) {
    cancelBrowserSpeechOutput();
    setBrowserVoiceUnlockRequired(false);
    ttsQueueRef.current = [{ text, tone }];
    drainLocalTtsQueue();
  }

  function speakResponseOrContinue(text: string, tone: JarvisVoiceTone) {
    if (voiceOutputEnabledRef.current && ttsSupportRef.current === "supported") {
      speakLocalJarvisResponse(text, tone);
      return;
    }
    setLocalVoiceState(ttsSupportRef.current === "not_supported" ? "not_supported" : "idle");
    setCapabilityNotice(
      voiceOutputEnabledRef.current
        ? "TTS no soportado o aún desconocido; dejo la respuesta visible y sigo en modo hablado cuando el navegador lo permita."
        : "Voz silenciada por David. Dejo la respuesta visible.",
    );
    queueNextLocalVoiceTurn(
      voiceOutputEnabledRef.current
        ? "No tengo TTS disponible aquí, pero sigo listo para escucharte."
        : "Voz silenciada por David. Te escucho de nuevo si la conversación sigue activa.",
      1000,
    );
  }

  function speakJarvisText(text: string, tone: JarvisVoiceTone = "calmado"): boolean {
    const trimmed = text.trim();
    if (!trimmed) return false;
    if (!voiceOutputEnabledRef.current) {
      setCapabilityNotice("Voz silenciada por David. Dejo la respuesta visible.");
      return false;
    }
    if (!browserTtsAvailable()) {
      setTtsSupport("not_supported");
      ttsSupportRef.current = "not_supported";
      setLocalVoiceState("not_supported");
      setCapabilityNotice("Voz no disponible en este navegador. Dejo la respuesta visible.");
      setLocalVoiceResponse("Voz no disponible en este navegador. Dejo la respuesta visible.");
      return false;
    }
    setTtsSupport("supported");
    ttsSupportRef.current = "supported";
    refreshBrowserVoiceSelection();
    setJarvisTone(tone);
    setLocalVoiceResponse(trimmed);
    speakLocalJarvisResponse(trimmed, tone);
    return true;
  }

  function stopJarvisSpeech() {
    cancelBrowserSpeechOutput();
    setLocalVoiceState("idle");
    setCapabilityNotice("Voz detenida. La respuesta completa sigue por escrito.");
  }

  function setVoiceOutputEnabled(enabled: boolean) {
    voiceOutputEnabledRef.current = enabled;
    setVoiceOutputEnabledState(enabled);
    writeVoiceOutputPreference(enabled);
    if (!enabled) {
      cancelBrowserSpeechOutput();
      setLocalVoiceState("stopped");
      setCapabilityNotice("Voz silenciada por David. Las respuestas quedan visibles hasta que vuelvas a activar voz.");
      return;
    }
    if (browserTtsAvailable()) {
      setTtsSupport("supported");
      ttsSupportRef.current = "supported";
      refreshBrowserVoiceSelection();
      setCapabilityNotice("Voz activa. JARVIS hablará por defecto cuando el navegador lo permita.");
      return;
    }
    setTtsSupport("not_supported");
    ttsSupportRef.current = "not_supported";
    setCapabilityNotice("Voz no disponible en este navegador. Dejo las respuestas visibles.");
  }

  function unlockBrowserVoice() {
    if (!browserTtsAvailable()) {
      setTtsSupport("not_supported");
      ttsSupportRef.current = "not_supported";
      setBrowserVoiceUnlockRequired(false);
      setCapabilityNotice("Voz no disponible en este navegador. Dejo las respuestas visibles.");
      return;
    }
    const retryQueue = blockedSpeechRef.current.length
      ? blockedSpeechRef.current
      : lastSpokenTextRef.current
        ? [{ text: lastSpokenTextRef.current, tone: jarvisTone }]
        : [];
    window.speechSynthesis.cancel();
    window.speechSynthesis.resume();
    speakingRef.current = false;
    currentUtteranceRef.current = null;
    setSpeechOutputActive(false);
    setBrowserVoiceUnlockRequired(false);
    setTtsSupport("supported");
    ttsSupportRef.current = "supported";
    refreshBrowserVoiceSelection();
    setCapabilityNotice("Voz desbloqueada. JARVIS seguirá hablando automáticamente.");
    if (retryQueue.length > 0) {
      blockedSpeechRef.current = [];
      ttsQueueRef.current = retryQueue;
      drainLocalTtsQueue();
    }
  }

  function handleWakeGreeting(text: string, tone: JarvisVoiceTone = "calmado"): boolean {
    const trimmed = text.trim();
    if (!trimmed) return false;
    clearLocalVoiceTimers();
    cancelledRef.current = false;
    setConversationActiveFlag(true);
    conversationExpiresAtRef.current = Date.now() + LOCAL_VOICE_CONVERSATION_TIMEOUT_MS;
    setTranscript("");
    setInterimTranscript("");
    setJarvisTone(tone);
    setLocalVoiceState("thinking");
    setLocalVoiceResponse(trimmed);
    setLocalVoiceIntent("wake_greeting");
    setLocalVoiceRisk("none");
    setIntentPreview({
      ...defaultIntentPreview,
      intent_detected: "wake_greeting",
      confidence: 1,
      risk_level: "none",
      cannot_execute_reason: "La frase de activación no aprueba ni ejecuta acciones.",
      suggested_next_action: "JARVIS ha despertado y espera la siguiente instrucción hablada.",
    });
    if (!voiceOutputEnabledRef.current) {
      setCapabilityNotice("Voz silenciada por David. El saludo queda visible.");
      return false;
    }
    if (!browserTtsAvailable()) {
      setTtsSupport("not_supported");
      ttsSupportRef.current = "not_supported";
      setLocalVoiceState("not_supported");
      setCapabilityNotice("Voz no disponible en este navegador. El saludo queda visible.");
      return false;
    }
    setTtsSupport("supported");
    ttsSupportRef.current = "supported";
    refreshBrowserVoiceSelection();
    speakLocalJarvisResponse(trimmed, tone);
    return true;
  }

  function finishLocalVoiceTranscript(finalText: string) {
    clearLocalVoiceTimers();
    if (isStopVoicePhrase(finalText)) {
      cancelLocalVoiceLoop();
      setTranscript(finalText);
      setLocalVoiceResponse("Escucha y voz detenidas por orden de David.");
      setLocalVoiceIntent("voice_stop_phrase");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "voice_stop_phrase",
        suggested_next_action: "Sesión de voz cerrada por frase de stop.",
      });
      return;
    }
    if (isLikelyTtsEcho(finalText)) {
      setLocalVoiceState("transcribing");
      setLocalVoiceResponse("He ignorado un posible eco de mi propia voz. Te escucho de nuevo.");
      setLocalVoiceIntent("ignored_possible_tts_echo");
      setLocalVoiceRisk("none");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "ignored_possible_tts_echo",
        suggested_next_action: "Repite tu petición si el navegador capturó la respuesta de JARVIS.",
      });
      queueNextLocalVoiceTurn("Te escucho de nuevo.", 700);
      return;
    }
    setLocalVoiceState("transcribing");
    let submittedResponse: ReturnType<NonNullable<LocalVoiceLoopOptions["onIntentSubmitted"]>> | undefined;
    try {
      submittedResponse = onIntentSubmittedRef.current?.(finalText);
    } catch {
      submittedResponse = undefined;
    }
    scheduleLocalVoiceStep(() => {
      if (cancelledRef.current) return;
      setLocalVoiceState("thinking");
      void Promise.resolve(submittedResponse)
        .then((externalResponse) => {
          if (cancelledRef.current) return;
          const response = externalResponse?.text ? externalResponse : buildLocalJarvisResponse(finalText);
          setJarvisTone(response.tone);
          setLocalVoiceResponse(response.text);
          setLocalVoiceIntent(response.intent);
          setLocalVoiceRisk(response.risk);
          setIntentPreview(response.intentPreview);
          scheduleLocalVoiceStep(() => {
            if (cancelledRef.current) return;
            if (response.suppressSpeech) {
              queueNextLocalVoiceTurn(response.text, 700);
              return;
            }
            speakResponseOrContinue(response.text, response.tone);
          }, 520);
        })
        .catch(() => {
          if (cancelledRef.current) return;
          const response = buildLocalJarvisResponse(finalText);
          setJarvisTone(response.tone);
          setLocalVoiceResponse(response.text);
          setLocalVoiceIntent(response.intent);
          setLocalVoiceRisk(response.risk);
          setIntentPreview(response.intentPreview);
          scheduleLocalVoiceStep(() => {
            if (cancelledRef.current) return;
            speakResponseOrContinue(response.text, response.tone);
          }, 520);
        });
    }, 320);
  }

  function startLocalVoiceRecognitionCycle({ continued = false }: { continued?: boolean } = {}) {
    const Recognition = getBrowserSpeechRecognitionConstructor();
    if (!Recognition) {
      setLocalVoiceState("not_supported");
      setJarvisTone("alerta");
      setSttSupport("not_supported");
      setCapabilityNotice("SpeechRecognition/webkitSpeechRecognition no está disponible en este navegador.");
      setLocalVoiceResponse("La entrada hablada del navegador no está disponible aquí. Escríbeme. No se fingió escucha ni se ejecutó nada.");
      setLocalVoiceIntent("stt_not_supported");
      setLocalVoiceRisk("none");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "stt_not_supported",
        cannot_execute_reason: "El navegador no soporta SpeechRecognition.",
        suggested_next_action: "Usa un navegador compatible o escribe la petición.",
      });
      setConversationActiveFlag(false);
      return;
    }

    recognitionRef.current?.abort();
    recognitionRef.current = null;
    finalTranscriptRef.current = "";
    recoverableSpeechErrorRef.current = false;
    setInterimTranscript("");
    setJarvisTone("concentrado");
    setLocalVoiceState("listening");
    setLocalVoiceResponse(
      continued
        ? "Te escucho de nuevo. La conversación hablada sigue activa."
        : "Conversación hablada activa. Habla de forma natural; no aprobaré ni ejecutaré acciones.",
    );
    setLocalVoiceIntent("listening");
    setLocalVoiceRisk("none");
    setIntentPreview({
      ...defaultIntentPreview,
      intent_detected: "listening",
      suggested_next_action: "Habla de forma natural; JARVIS clasificará la intención localmente.",
    });

    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "es-ES";
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setLocalVoiceState("listening");
    recognition.onspeechstart = () => setLocalVoiceState("listening");
    recognition.onspeechend = () => setLocalVoiceState("transcribing");
    recognition.onresult = (event) => {
      let interimText = "";
      let finalText = "";
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const alternative = result?.[0];
        if (!alternative?.transcript) continue;
        if (result.isFinal) {
          finalText += ` ${alternative.transcript}`;
        } else {
          interimText += ` ${alternative.transcript}`;
        }
      }
      const normalizedInterim = interimText.replace(/\s+/g, " ").trim();
      const normalizedFinal = finalText.replace(/\s+/g, " ").trim();
      setInterimTranscript(normalizedInterim);
      if (normalizedFinal) {
        finalTranscriptRef.current = normalizedFinal;
        setTranscript(normalizedFinal);
        setInterimTranscript("");
        recognition.stop();
        finishLocalVoiceTranscript(normalizedFinal);
      }
    };
    recognition.onerror = (event) => {
      if (event.error === "no-speech" && conversationActiveRef.current && !cancelledRef.current) {
        recoverableSpeechErrorRef.current = true;
        setLocalVoiceState("idle");
        setLocalVoiceResponse("Sigo en conversación hablada. Vuelve a hablar o pulsa stop para cerrar.");
        setLocalVoiceIntent("voice_conversation_waiting");
        setLocalVoiceRisk("none");
        setIntentPreview({
          ...defaultIntentPreview,
          intent_detected: "voice_conversation_waiting",
          suggested_next_action: "Habla otra vez o pulsa stop.",
        });
        queueNextLocalVoiceTurn("Sigo en conversación hablada. Vuelve a hablar o pulsa stop para cerrar.", 1200);
        return;
      }

      cancelledRef.current = true;
      const permissionDenied = event.error === "not-allowed" || event.error === "service-not-allowed";
      setLocalVoiceState(permissionDenied ? "unavailable" : "error");
      setJarvisTone("alerta");
      setConversationActiveFlag(false);
      setCapabilityNotice(
        permissionDenied
          ? "Permiso de micrófono denegado o no disponible para SpeechRecognition."
          : `Error de SpeechRecognition: ${event.error || event.message || UNKNOWN}.`,
      );
      setLocalVoiceResponse("No hay escucha disponible. No se guardó audio, no se envió audio al backend y no se ejecutó nada.");
      setLocalVoiceIntent(permissionDenied ? "microphone_permission_unavailable" : "stt_error");
      setLocalVoiceRisk("none");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: permissionDenied ? "microphone_permission_unavailable" : "stt_error",
        cannot_execute_reason: "No hay canal de voz disponible.",
        suggested_next_action: "Revisar permisos del navegador o usar otro canal.",
      });
    };
    recognition.onend = () => {
      recognitionRef.current = null;
      if (cancelledRef.current || finalTranscriptRef.current || recoverableSpeechErrorRef.current) return;
      if (conversationActiveRef.current) {
        setLocalVoiceState("idle");
        setLocalVoiceResponse("Sigo en conversación hablada. Vuelve a hablar o pulsa stop para cerrar.");
        setLocalVoiceIntent("voice_conversation_waiting");
        setLocalVoiceRisk("none");
        setIntentPreview({
          ...defaultIntentPreview,
          intent_detected: "voice_conversation_waiting",
          suggested_next_action: "Habla otra vez o pulsa stop.",
        });
        queueNextLocalVoiceTurn("Sigo en conversación hablada. Vuelve a hablar o pulsa stop para cerrar.", 1200);
        return;
      }
      setLocalVoiceState("idle");
      setLocalVoiceResponse("Escucha finalizada sin transcripción final. No se ejecutó nada.");
      setLocalVoiceIntent("no_final_transcript");
      setLocalVoiceRisk("none");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "no_final_transcript",
        cannot_execute_reason: "No hubo transcripción final.",
        suggested_next_action: "Repite la petición con una frase corta.",
      });
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch {
      recognitionRef.current = null;
      setLocalVoiceState("unavailable");
      setJarvisTone("alerta");
      setCapabilityNotice("El navegador rechazó iniciar SpeechRecognition en este contexto.");
      setLocalVoiceResponse("No se pudo iniciar la escucha. Escríbeme. No se fingió escucha ni se ejecutó nada.");
      setLocalVoiceIntent("stt_unavailable");
      setLocalVoiceRisk("none");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "stt_unavailable",
        cannot_execute_reason: "El navegador rechazó iniciar SpeechRecognition.",
        suggested_next_action: "Revisar permisos o recargar la página.",
      });
      setConversationActiveFlag(false);
    }
  }

  function beginLocalVoiceLoop() {
    clearLocalVoiceTimers();
    cancelBrowserSpeechOutput();
    refreshBrowserVoiceSelection();
    cancelledRef.current = false;
    setConversationActiveFlag(true);
    conversationExpiresAtRef.current = Date.now() + LOCAL_VOICE_CONVERSATION_TIMEOUT_MS;
    setTranscript("");
    setInterimTranscript("");
    startLocalVoiceRecognitionCycle();
  }

  function cancelLocalVoiceLoop() {
    cancelledRef.current = true;
    setConversationActiveFlag(false);
    conversationExpiresAtRef.current = 0;
    clearLocalVoiceTimers();
    recognitionRef.current?.abort();
    recognitionRef.current = null;
    cancelBrowserSpeechOutput();
    setInterimTranscript("");
    setLocalVoiceState("cancelled");
    setJarvisTone("calmado");
    setLocalVoiceResponse("Escucha y voz detenidas por David. No se ejecutó nada.");
    setLocalVoiceIntent("cancelled_by_operator");
    setLocalVoiceRisk("none");
    setIntentPreview({
      ...defaultIntentPreview,
      intent_detected: "cancelled_by_operator",
      suggested_next_action: "Escribe o vuelve a despertar a JARVIS cuando quieras.",
    });
  }

  useEffect(() => {
    const sttAvailable = Boolean(getBrowserSpeechRecognitionConstructor());
    const ttsAvailable = browserTtsAvailable();
    setSttSupport(sttAvailable ? "supported" : "not_supported");
    setTtsSupport(ttsAvailable ? "supported" : "not_supported");
    ttsSupportRef.current = ttsAvailable ? "supported" : "not_supported";
    refreshBrowserVoiceSelection();
    if (ttsAvailable) {
      window.speechSynthesis.onvoiceschanged = refreshBrowserVoiceSelection;
    }
    if (!sttAvailable) {
      setLocalVoiceState("not_supported");
      setJarvisTone("alerta");
      setCapabilityNotice("SpeechRecognition/webkitSpeechRecognition no está disponible en este navegador.");
      setLocalVoiceResponse("La entrada hablada del navegador no está disponible aquí. Puedes escribirme y seguiré respondiendo.");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "stt_not_supported",
        cannot_execute_reason: "SpeechRecognition/webkitSpeechRecognition no está disponible.",
      });
    } else if (!ttsAvailable) {
      setCapabilityNotice("STT está disponible; speechSynthesis no está disponible para TTS en este navegador.");
    } else {
      setCapabilityNotice("Voz activa. STT y TTS de navegador detectados; wake real llega desde el listener local.");
    }

    return () => {
      cancelledRef.current = true;
      conversationActiveRef.current = false;
      clearLocalVoiceTimers();
      recognitionRef.current?.abort();
      recognitionRef.current = null;
      if (browserTtsAvailable()) {
        window.speechSynthesis.onvoiceschanged = null;
      }
      cancelBrowserSpeechOutput();
    };
  }, []);

  useEffect(() => {
    ttsSupportRef.current = ttsSupport;
  }, [ttsSupport]);

  useEffect(() => {
    voiceOutputEnabledRef.current = voiceOutputEnabled;
  }, [voiceOutputEnabled]);

  return {
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
    voiceOutputEnabled,
    browserVoiceUnlockRequired,
    speechOutputActive,
    canInterrupt: speechOutputActive || currentUtteranceRef.current !== null || localVoiceState === "speaking",
    canCancel: conversationActive || localVoiceState === "listening" || localVoiceState === "transcribing" || localVoiceState === "thinking" || localVoiceState === "speaking",
    speakJarvisText,
    handleWakeGreeting,
    unlockBrowserVoice,
    stopJarvisSpeech,
    setVoiceOutputEnabled,
    beginLocalVoiceLoop,
    cancelLocalVoiceLoop,
  };
}
