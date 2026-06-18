const preferredSpanishVoiceHints = [
  "natural",
  "neural",
  "premium",
  "microsoft",
  "google",
  "helena",
  "elvira",
  "dalia",
  "paulina",
  "monica",
  "mónica",
  "alvaro",
  "álvaro",
  "jorge",
];

export function browserTtsAvailable(): boolean {
  return (
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    "SpeechSynthesisUtterance" in window
  );
}

function voiceScore(voice: SpeechSynthesisVoice): number {
  const lang = voice.lang.toLocaleLowerCase("es-ES");
  const descriptor = `${voice.name} ${voice.voiceURI} ${voice.lang}`.toLocaleLowerCase("es-ES");
  let score = lang.startsWith("es") ? 20 : 0;
  if (lang === "es-es") score += 9;
  if (lang.startsWith("es-")) score += 4;
  preferredSpanishVoiceHints.forEach((hint, index) => {
    if (descriptor.includes(hint)) score += 12 - Math.min(index, 8);
  });
  if (voice.localService) score += 2;
  return score;
}

export function selectPreferredSpanishVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  const spanishVoices = voices.filter((voice) => voice.lang.toLocaleLowerCase("es-ES").startsWith("es"));
  if (!spanishVoices.length) return null;
  return [...spanishVoices].sort((left, right) => voiceScore(right) - voiceScore(left))[0] ?? null;
}

export function selectedVoiceNotice(voice: SpeechSynthesisVoice | null, voicesAvailable: number): string {
  if (voice) return `Voz española seleccionada: ${voice.name} (${voice.lang}).`;
  if (voicesAvailable > 0) return "No hay voz española clara; usaré la voz por defecto del navegador.";
  return "Esperando catálogo de voces del navegador.";
}
