import type { BrowserSpeechRecognitionConstructor } from "@/components/jarvis/types";

export function getBrowserSpeechRecognitionConstructor(): BrowserSpeechRecognitionConstructor | null {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null;
}

export function browserSpeechRecognitionAvailable(): boolean {
  return Boolean(getBrowserSpeechRecognitionConstructor());
}
