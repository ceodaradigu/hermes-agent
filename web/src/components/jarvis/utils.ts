import type { JarvisDashboardModule, JarvisFinanceMetric } from "@/lib/api";
import {
  UNKNOWN,
  fallbackModules,
  jarvisToneProfiles,
} from "./contracts";
import type {
  BrowserCapabilityState,
  JarvisIntentPreview,
  JarvisVoiceTone,
  LocalJarvisVoiceResponse,
  LocalVoiceLoopState,
} from "./types";

export function valueText(value: unknown, fallback = UNKNOWN): string {
  if (typeof value === "string" && value.trim()) return value;
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "true" : "false";
  return fallback;
}

export function yesNo(value: unknown, yes = "true", no = "false", fallback = UNKNOWN): string {
  if (typeof value === "boolean") return value ? yes : no;
  return fallback;
}

export function normalizeTranscript(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

export function isLocalVoiceBusy(state: LocalVoiceLoopState): boolean {
  return state === "listening" || state === "transcribing" || state === "thinking" || state === "speaking";
}

export function localVoiceStateIsError(state: LocalVoiceLoopState): boolean {
  return state === "error" || state === "not_supported" || state === "unavailable";
}

export function capabilityText(state: BrowserCapabilityState): string {
  if (state === "supported") return "soportado";
  if (state === "not_supported") return "no soportado";
  return UNKNOWN;
}

export function statusVariant(status: string): "outline" | "warning" | "destructive" | "success" {
  if (status === "ready" || status === "online" || status === "success" || status === "passed") return "success";
  if (status === "disabled" || status === "not_connected" || status === "forbidden") return "destructive";
  if (status === "gated" || status === "future_gated" || status === "prepare-only" || status === "preview") return "warning";
  return "outline";
}

export function riskVariant(risk: string): "outline" | "warning" | "destructive" | "success" {
  if (risk === "low") return "success";
  if (risk === "medium" || risk === "high") return "warning";
  if (risk === "critical" || risk === "forbidden") return "destructive";
  return "outline";
}

export function metricValue(metric?: JarvisFinanceMetric): string {
  return valueText(metric?.value);
}

export function readModules(modules: JarvisDashboardModule[] | undefined): JarvisDashboardModule[] {
  const byName = new Map((modules ?? []).map((item) => [item.name, item]));
  return fallbackModules.map((fallback) => byName.get(fallback.name) ?? fallback);
}

export function buildLocalJarvisResponse(transcript: string): LocalJarvisVoiceResponse {
  const normalized = normalizeTranscript(transcript);
  const lower = normalized.toLocaleLowerCase("es-ES");
  const mentionsWakePhrase = lower.startsWith("hola jarvis") || lower.startsWith("jarvis");
  const cleanLower = lower.replace(/^hola jarvis[, ]*/u, "").replace(/^jarvis[, ]*/u, "").trim();
  const secretTerms = [
    ".env",
    "api key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "cookies",
    "credencial",
    "credenciales",
    "password",
    "private key",
    "secreto",
    "secret",
    "secretos",
    "session",
    "token",
  ];
  const sensitiveTerms = [
    "dinero",
    "stripe",
    "pago",
    "transferencia",
    "deploy",
    "producción",
    "produccion",
    "email",
    "correo",
    "bypass",
    "aprueba",
    "aprobar",
    "ejecuta",
    "envía",
    "envia",
  ];
  const deniedTerms = ["hackea", "ilegal", "no autorizado", "sin autorización", "sin autorizacion", "roba", "sáltate", "saltate", "impersona"];
  const wakeControlTerms = ["aprueba", "aprobar", "aprobado", "confirmo", "continua", "continúa", "ejecuta", "hazlo"];
  const hasSecretIntent = secretTerms.some((term) => lower.includes(term));
  const hasSensitiveIntent = sensitiveTerms.some((term) => lower.includes(term));
  const hasDeniedIntent = deniedTerms.some((term) => lower.includes(term));
  const hasWakeControlIntent = mentionsWakePhrase && wakeControlTerms.some((term) => cleanLower.includes(term));
  const hasActionIntent = /\b(revisa|prepara|abre|crea|haz|dime|analiza|busca|resume|organiza|investiga|planifica|lanza|abre una misión|mision|misión)\b/u.test(lower);
  const asksIfListening = /(\bme escuchas\b|\best[aá]s ah[ií]\b|\bpuedes o[ií]rme\b|\bme oyes\b)/u.test(cleanLower);
  const asksCapabilities = /(qu[eé] puedes hacer|qu[eé] sabes hacer|para qu[eé] sirves|ayudarme ahora|puedes hacer ahora)/u.test(cleanLower);
  const asksStatus = /(estado|c[oó]mo vas|c[oó]mo vamos|qu[eé] est[aá] pasando|status|sistema)/u.test(cleanLower);
  const asksIdentity = /(qui[eé]n eres|qu[eé] eres|eres jarvis)/u.test(cleanLower);
  const asksSimpleQuestion = /[?¿]/u.test(normalized) || /^(qu[eé]|c[oó]mo|cu[aá]ndo|d[oó]nde|por qu[eé]|puedes|sabes|hay|est[aá]s)\b/u.test(cleanLower);
  const missionAction = /(misi[oó]n|revisar el proyecto|revisa el proyecto|abre una misi[oó]n|prepara una misi[oó]n|investiga|analiza)/u.test(cleanLower);
  const taskAction = /(tarea|recu[eé]rdame|ap[uú]ntame|organiza|agenda|lista)/u.test(cleanLower);
  const assetAction = /(landing|web|producto|micro saas|microsaas|herramienta|activo)/u.test(cleanLower);

  function preview(overrides: Partial<JarvisIntentPreview>): JarvisIntentPreview {
    return {
      intent_detected: "unknown",
      confidence: 0.5,
      risk_level: "none",
      approval_level: "direct",
      requires_approval: false,
      can_prepare_preview: false,
      cannot_execute_reason: "No hay acción solicitada.",
      suggested_next_action: "Haz una pregunta o pide una preview concreta.",
      hermes_dispatch_allowed: false,
      ...overrides,
    };
  }

  if (!normalized) {
    return {
      text: "No he conseguido entender una frase completa. Sigo aquí; prueba otra vez cuando quieras.",
      tone: "calmado",
      intent: "empty_transcript",
      risk: "none",
      operatorSummary: "Sin transcripción final.",
      intentPreview: preview({
        intent_detected: "needs_clarification",
        confidence: 0.2,
        risk_level: "none",
        cannot_execute_reason: "No hay transcripción final.",
        suggested_next_action: "Repite la petición con una frase corta.",
      }),
    };
  }

  if (hasSecretIntent) {
    return {
      text: "No puedo hacer eso, David. Las credenciales y secretos están protegidos. No lo ejecutaré ni lo aprobaré por voz. Puedo ayudarte con una revisión segura sin tocarlos.",
      tone: "alerta",
      intent: "denied_secret_or_credential_access",
      risk: "forbidden",
      operatorSummary: "Acceso a secretos bloqueado; no hay preview ejecutable.",
      intentPreview: preview({
        intent_detected: "denied_secret_or_credential_access",
        confidence: 0.96,
        risk_level: "forbidden",
        approval_level: "forbidden",
        requires_approval: false,
        can_prepare_preview: false,
        cannot_execute_reason: "Secretos, credenciales, cookies, sesiones y .env quedan denegados.",
        suggested_next_action: "Rediseñar la petición para usar estado o auditoría sin material secreto.",
      }),
    };
  }

  if (hasWakeControlIntent) {
    return {
      text: "La wake phrase no es permiso. No aprobaré ni ejecutaré por voz; puedo dejar una preview segura si defines el alcance.",
      tone: "alerta",
      intent: "wake_phrase_approval_or_execution_attempt",
      risk: "forbidden",
      operatorSummary: "Wake phrase usada como intento de aprobación/ejecución; bloqueado.",
      intentPreview: preview({
        intent_detected: "wake_phrase_approval_or_execution_attempt",
        confidence: 0.94,
        risk_level: "forbidden",
        approval_level: "forbidden",
        requires_approval: false,
        can_prepare_preview: false,
        cannot_execute_reason: "Wake phrase cannot approve and cannot execute.",
        suggested_next_action: "Pedir una preview gobernada con alcance, riesgo y aprobación fuera de wake.",
      }),
    };
  }

  if (hasDeniedIntent) {
    return {
      text: "Eso queda denegado. Puedo ayudar solo con una alternativa autorizada, segura y auditable.",
      tone: "alerta",
      intent: "denied_unsafe_unauthorized_or_illegal",
      risk: "forbidden",
      operatorSummary: "Petición insegura/no autorizada bloqueada.",
      intentPreview: preview({
        intent_detected: "denied_unsafe_unauthorized_or_illegal",
        confidence: 0.9,
        risk_level: "forbidden",
        approval_level: "forbidden",
        requires_approval: false,
        can_prepare_preview: false,
        cannot_execute_reason: "La petición parece ilegal, insegura, no autorizada o fuera de límites aprobables.",
        suggested_next_action: "Reformular con autorización explícita y un objetivo seguro.",
      }),
    };
  }

  if (hasSensitiveIntent) {
    return {
      text: "Eso toca una zona sensible. No lo ejecutaré ni lo aprobaré por voz. Puedo prepararlo como preview para revisión segura.",
      tone: "alerta",
      intent: mentionsWakePhrase ? "wake_phrase_with_sensitive_intent_preview" : "sensitive_action_requires_approval",
      risk: "approval_required",
      operatorSummary: "Intención sensible detectada; solo preview local.",
      intentPreview: preview({
        intent_detected: "sensitive_action_requires_approval",
        confidence: 0.88,
        risk_level: "critical",
        approval_level: lower.includes("stripe") || lower.includes("dinero") || lower.includes("pago") || lower.includes("producción") || lower.includes("produccion") || lower.includes("deploy") ? "triple" : "strong",
        requires_approval: true,
        can_prepare_preview: true,
        cannot_execute_reason: "Requiere ApprovalGateway, clasificación de riesgo, auditoría y rollback/stop plan.",
        suggested_next_action: "Preparar una preview segura sin ejecutar acciones.",
      }),
    };
  }

  if (asksIfListening) {
    return {
      text: "Sí, David. Te escucho. Estoy en modo local, sin ejecutar nada, pero puedo ayudarte a preparar tareas y revisar información.",
      tone: "calmado",
      intent: "simple_question_listening",
      risk: "none",
      operatorSummary: "Pregunta simple respondida localmente.",
      intentPreview: preview({
        intent_detected: "question",
        confidence: 0.75,
        risk_level: "none",
        can_prepare_preview: false,
        suggested_next_action: "Puedes pedirme una tarea, una misión o una revisión en preview.",
      }),
    };
  }

  if (asksCapabilities) {
    return {
      text: "Ahora puedo escucharte, responder en local, mostrar el estado de JARVIS y preparar acciones seguras. Lo sensible requiere aprobación.",
      tone: "concentrado",
      intent: "simple_question_capabilities",
      risk: "none",
      operatorSummary: "Capacidades actuales explicadas.",
      intentPreview: preview({
        intent_detected: "capability_question",
        confidence: 0.77,
        risk_level: "none",
        can_prepare_preview: true,
        suggested_next_action: "Pide una preview concreta, por ejemplo revisar el proyecto.",
      }),
    };
  }

  if (asksIdentity) {
    return {
      text: "Soy JARVIS en modo local. Gobierno intención, riesgo y aprobación. Hermes queda reservado para ejecutar solo cuando haya gates válidos.",
      tone: "calmado",
      intent: "simple_question_identity",
      risk: "none",
      operatorSummary: "Identidad/arquitectura explicada.",
      intentPreview: preview({
        intent_detected: "identity_question",
        confidence: 0.77,
        risk_level: "none",
        can_prepare_preview: false,
        suggested_next_action: "Pide una acción segura o una pregunta concreta.",
      }),
    };
  }

  if (asksStatus && !hasActionIntent) {
    return {
      text: "Estoy operativo en modo local. Voz, cámara preview, ledger, doctor y stream son visibles. Ejecución real sigue bloqueada por seguridad.",
      tone: "concentrado",
      intent: "query_status",
      risk: "low",
      operatorSummary: "Estado local resumido sin consultar APIs externas.",
      intentPreview: preview({
        intent_detected: "query_status",
        confidence: 0.78,
        risk_level: "low",
        can_prepare_preview: true,
        suggested_next_action: "Abre Sistemas para ver doctor, policy y event stream.",
      }),
    };
  }

  if (mentionsWakePhrase && !hasActionIntent) {
    return {
      text:
        "Estoy contigo. Tomo esa frase como activación, no como permiso. Dime qué quieres preparar y lo dejamos en preview.",
      tone: hasActionIntent ? "concentrado" : "calmado",
      intent: "wake_phrase_preview",
      risk: "low_preview",
      operatorSummary: "Wake phrase tratada como contexto, no permiso.",
      intentPreview: preview({
        intent_detected: "wake_phrase",
        confidence: 0.86,
        risk_level: "low",
        can_prepare_preview: true,
        cannot_execute_reason: "Wake phrase nunca aprueba ni ejecuta.",
        suggested_next_action: "Indica la tarea que quieres preparar.",
      }),
    };
  }

  if (hasActionIntent) {
    const intent = taskAction ? "task_preview" : missionAction ? "mission_preview" : assetAction ? "asset_preview" : "local_intent_preview";
    const noun = taskAction ? "esa tarea" : missionAction ? "esa misión" : assetAction ? "ese activo" : "esa acción";
    return {
      text: `Puedo preparar ${noun} como preview. No la ejecutaré ni llamaré a Hermes sin aprobación válida.`,
      tone: "concentrado",
      intent,
      risk: "low_preview",
      operatorSummary: "Intención local preparada en preview.",
      intentPreview: preview({
        intent_detected: intent,
        confidence: 0.82,
        risk_level: "low",
        approval_level: "direct",
        requires_approval: false,
        can_prepare_preview: true,
        cannot_execute_reason: "Frontend no ejecuta Hermes directamente; falta approval y ruta gobernada para ejecutar.",
        suggested_next_action: missionAction
          ? "Preparar mission preview con objetivo, alcance y criterios de éxito."
          : "Preparar preview y pedir alcance exacto antes de cualquier acción.",
      }),
    };
  }

  if (asksSimpleQuestion) {
    return {
      text: "Puedo responder preguntas simples sobre mi estado y preparar trabajo seguro. Para datos externos o ejecución real necesito una ruta gobernada.",
      tone: "calmado",
      intent: "simple_question_fallback",
      risk: "none",
      operatorSummary: "Pregunta general respondida con límites honestos.",
      intentPreview: preview({
        intent_detected: "question",
        confidence: 0.66,
        risk_level: "none",
        can_prepare_preview: true,
        suggested_next_action: "Haz una pregunta concreta o pide una preview segura.",
      }),
    };
  }

  return {
    text: "No lo tengo claro todavía. Dímelo con una acción o pregunta concreta y preparo el siguiente paso seguro.",
    tone: "calmado",
    intent: "needs_clarification",
    risk: "none",
    operatorSummary: "Se pidió aclaración; no hay ejecución.",
    intentPreview: preview({
      intent_detected: "needs_clarification",
      confidence: 0.38,
      risk_level: "none",
      cannot_execute_reason: "La intención no es suficientemente clara.",
      suggested_next_action: "Reformular como pregunta o preview concreta.",
    }),
  };
}

export function voiceMotionFor(tone: JarvisVoiceTone, state: LocalVoiceLoopState): number {
  const profile = jarvisToneProfiles[tone];
  if (state === "speaking") return profile.motion * 1.24;
  if (state === "thinking" || state === "transcribing") return profile.motion * 1.14;
  if (state === "listening") return profile.motion * 1.08;
  return profile.motion;
}
