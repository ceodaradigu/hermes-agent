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

export function useLocalVoiceLoop(): LocalVoiceLoopController {
  const defaultIntentPreview: JarvisIntentPreview = {
    intent_detected: "idle",
    risk_level: "none",
    requires_approval: false,
    can_prepare_preview: false,
    cannot_execute_reason: "Sin petición activa.",
    suggested_next_action: "Pulsa el micrófono y pregunta algo concreto.",
  };
  const [localVoiceState, setLocalVoiceState] = useState<LocalVoiceLoopState>("idle");
  const [jarvisTone, setJarvisTone] = useState<JarvisVoiceTone>("calmado");
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [localVoiceResponse, setLocalVoiceResponse] = useState("Pulsa el micrófono una vez para abrir conversación manual local.");
  const [localVoiceIntent, setLocalVoiceIntent] = useState("idle");
  const [localVoiceRisk, setLocalVoiceRisk] = useState("none");
  const [intentPreview, setIntentPreview] = useState<JarvisIntentPreview>(defaultIntentPreview);
  const [sttSupport, setSttSupport] = useState<BrowserCapabilityState>("unknown");
  const [ttsSupport, setTtsSupport] = useState<BrowserCapabilityState>("unknown");
  const [capabilityNotice, setCapabilityNotice] = useState("Detectando soporte de voz del navegador.");
  const [conversationActive, setConversationActive] = useState(false);
  const [selectedVoiceName, setSelectedVoiceName] = useState("");
  const [voiceQualityNotice, setVoiceQualityNotice] = useState("Detectando voces del navegador.");
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const finalTranscriptRef = useRef("");
  const cancelledRef = useRef(false);
  const recoverableSpeechErrorRef = useRef(false);
  const conversationActiveRef = useRef(false);
  const conversationExpiresAtRef = useRef(0);
  const timersRef = useRef<number[]>([]);
  const selectedVoiceNameRef = useRef("");
  const ttsSupportRef = useRef<BrowserCapabilityState>("unknown");

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

  function queueNextLocalVoiceTurn(message = "Listo. Te escucho de nuevo.", delay = LOCAL_VOICE_RESTART_DELAY_MS) {
    if (!conversationActiveRef.current || cancelledRef.current) {
      setLocalVoiceState("idle");
      return;
    }

    if (Date.now() > conversationExpiresAtRef.current) {
      setConversationActiveFlag(false);
      setLocalVoiceState("idle");
      setJarvisTone("calmado");
      setLocalVoiceResponse("Pauso la conversación manual por seguridad. Pulsa el micrófono para abrir otra ventana.");
      setLocalVoiceIntent("manual_conversation_timeout");
      setLocalVoiceRisk("none");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "manual_conversation_timeout",
        suggested_next_action: "Pulsa el micrófono para abrir otra conversación.",
      });
      return;
    }

    setLocalVoiceResponse(message);
    scheduleLocalVoiceStep(() => {
      if (!conversationActiveRef.current || cancelledRef.current) return;
      startLocalVoiceRecognitionCycle({ continued: true });
    }, delay);
  }

  function speakLocalJarvisResponse(text: string, tone: JarvisVoiceTone) {
    if (!browserTtsAvailable()) {
      setLocalVoiceState("not_supported");
      setCapabilityNotice("speechSynthesis no está disponible en este navegador; respuesta visible sin audio.");
      queueNextLocalVoiceTurn("No tengo voz TTS disponible aquí, pero sigo listo para escucharte en texto.", 900);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const profile = jarvisToneProfiles[tone];
    const preferredVoice = getPreferredBrowserVoice();
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
    utterance.onstart = () => setLocalVoiceState("speaking");
    utterance.onend = () => {
      if (conversationActiveRef.current) {
        queueNextLocalVoiceTurn("Te escucho de nuevo. Habla cuando quieras o pulsa stop.", LOCAL_VOICE_RESTART_DELAY_MS);
        return;
      }
      setLocalVoiceState("idle");
    };
    utterance.onerror = () => {
      setLocalVoiceState("error");
      setCapabilityNotice("El navegador no pudo reproducir TTS; la respuesta queda visible en la smart bar.");
      queueNextLocalVoiceTurn("No pude reproducir la voz, pero la conversación manual sigue disponible.", 1000);
    };
    window.speechSynthesis.speak(utterance);
  }

  function finishLocalVoiceTranscript(finalText: string) {
    clearLocalVoiceTimers();
    setLocalVoiceState("transcribing");
    scheduleLocalVoiceStep(() => {
      const response = buildLocalJarvisResponse(finalText);
      setLocalVoiceState("thinking");
      setJarvisTone(response.tone);
      setLocalVoiceResponse(response.text);
      setLocalVoiceIntent(response.intent);
      setLocalVoiceRisk(response.risk);
      setIntentPreview(response.intentPreview);
      scheduleLocalVoiceStep(() => {
        if (ttsSupportRef.current === "supported") {
          speakLocalJarvisResponse(response.text, response.tone);
          return;
        }
        setLocalVoiceState(ttsSupportRef.current === "not_supported" ? "not_supported" : "idle");
        setCapabilityNotice("TTS no soportado o aún desconocido; respuesta visible sin audio.");
        queueNextLocalVoiceTurn("No tengo TTS disponible aquí, pero sigo listo para escucharte.", 1000);
      }, 520);
    }, 320);
  }

  function startLocalVoiceRecognitionCycle({ continued = false }: { continued?: boolean } = {}) {
    const Recognition = getBrowserSpeechRecognitionConstructor();
    if (!Recognition) {
      setLocalVoiceState("not_supported");
      setJarvisTone("alerta");
      setSttSupport("not_supported");
      setCapabilityNotice("SpeechRecognition/webkitSpeechRecognition no está disponible en este navegador.");
      setLocalVoiceResponse("No puedo escuchar en este navegador. No se fingió escucha ni se ejecutó nada.");
      setLocalVoiceIntent("stt_not_supported");
      setLocalVoiceRisk("none");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "stt_not_supported",
        cannot_execute_reason: "El navegador no soporta SpeechRecognition.",
        suggested_next_action: "Usa un navegador compatible o texto manual en una fase futura.",
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
        ? "Te escucho de nuevo. La conversación manual sigue activa."
        : "Conversación manual activa. Habla de forma natural; no aprobaré ni ejecutaré acciones.",
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
        setLocalVoiceResponse("Sigo en conversación manual. Vuelve a hablar o pulsa stop para cerrar.");
        setLocalVoiceIntent("manual_conversation_waiting");
        setLocalVoiceRisk("none");
        setIntentPreview({
          ...defaultIntentPreview,
          intent_detected: "manual_conversation_waiting",
          suggested_next_action: "Habla otra vez o pulsa stop.",
        });
        queueNextLocalVoiceTurn("Sigo en conversación manual. Vuelve a hablar o pulsa stop para cerrar.", 1200);
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
        setLocalVoiceResponse("Sigo en conversación manual. Vuelve a hablar o pulsa stop para cerrar.");
        setLocalVoiceIntent("manual_conversation_waiting");
        setLocalVoiceRisk("none");
        setIntentPreview({
          ...defaultIntentPreview,
          intent_detected: "manual_conversation_waiting",
          suggested_next_action: "Habla otra vez o pulsa stop.",
        });
        queueNextLocalVoiceTurn("Sigo en conversación manual. Vuelve a hablar o pulsa stop para cerrar.", 1200);
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
      setLocalVoiceResponse("No se pudo iniciar la escucha. No se fingió soporte ni se ejecutó nada.");
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
    if (browserTtsAvailable()) {
      window.speechSynthesis.cancel();
      refreshBrowserVoiceSelection();
    }
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
    if (browserTtsAvailable()) {
      window.speechSynthesis.cancel();
    }
    setInterimTranscript("");
    setLocalVoiceState("idle");
    setJarvisTone("calmado");
    setLocalVoiceResponse("Escucha/habla detenida por David. No se ejecutó nada.");
    setLocalVoiceIntent("cancelled_by_operator");
    setLocalVoiceRisk("none");
    setIntentPreview({
      ...defaultIntentPreview,
      intent_detected: "cancelled_by_operator",
      suggested_next_action: "Pulsa el micrófono para iniciar otra conversación.",
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
      setLocalVoiceResponse("STT no está soportado aquí. La UI lo declara; no simula escucha.");
      setIntentPreview({
        ...defaultIntentPreview,
        intent_detected: "stt_not_supported",
        cannot_execute_reason: "SpeechRecognition/webkitSpeechRecognition no está disponible.",
      });
    } else if (!ttsAvailable) {
      setCapabilityNotice("STT está disponible; speechSynthesis no está disponible para TTS en este navegador.");
    } else {
      setCapabilityNotice("STT y TTS de navegador detectados. Activación siempre manual; soporte depende del navegador.");
    }

    return () => {
      cancelledRef.current = true;
      conversationActiveRef.current = false;
      clearLocalVoiceTimers();
      recognitionRef.current?.abort();
      recognitionRef.current = null;
      if (browserTtsAvailable()) {
        window.speechSynthesis.onvoiceschanged = null;
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  useEffect(() => {
    ttsSupportRef.current = ttsSupport;
  }, [ttsSupport]);

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
    beginLocalVoiceLoop,
    cancelLocalVoiceLoop,
  };
}
