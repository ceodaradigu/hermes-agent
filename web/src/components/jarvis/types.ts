export type LocalVoiceLoopState =
  | "idle"
  | "listening"
  | "transcribing"
  | "thinking"
  | "speaking"
  | "error"
  | "not_supported"
  | "unavailable";

export type JarvisVoiceTone = "calmado" | "concentrado" | "alerta" | "intenso";

export type JarvisOrbVisualState =
  | "idle"
  | "wake_listening"
  | "listening"
  | "transcribing"
  | "thinking"
  | "speaking"
  | "alert"
  | "error"
  | "stopped"
  | "executing";

export type BrowserCapabilityState = "unknown" | "supported" | "not_supported";

export interface LocalJarvisVoiceResponse {
  text: string;
  tone: JarvisVoiceTone;
  intent: string;
  risk: string;
  operatorSummary: string;
  intentPreview: JarvisIntentPreview;
}

export interface JarvisIntentPreview {
  intent_detected: string;
  confidence?: number | string;
  risk_level: string;
  approval_level?: string;
  requires_approval: boolean;
  can_prepare_preview: boolean;
  cannot_execute_reason: string;
  suggested_next_action: string;
  hermes_dispatch_allowed?: boolean;
}

export interface BrowserSpeechRecognitionAlternative {
  transcript: string;
  confidence?: number;
}

export interface BrowserSpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  [index: number]: BrowserSpeechRecognitionAlternative;
}

export interface BrowserSpeechRecognitionResultList {
  length: number;
  [index: number]: BrowserSpeechRecognitionResult;
}

export interface BrowserSpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: BrowserSpeechRecognitionResultList;
}

export interface BrowserSpeechRecognitionErrorEvent extends Event {
  error?: string;
  message?: string;
}

export interface BrowserSpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onstart: ((event: Event) => void) | null;
  onend: ((event: Event) => void) | null;
  onresult: ((event: BrowserSpeechRecognitionEvent) => void) | null;
  onerror: ((event: BrowserSpeechRecognitionErrorEvent) => void) | null;
  onspeechstart: ((event: Event) => void) | null;
  onspeechend: ((event: Event) => void) | null;
}

export interface BrowserSpeechRecognitionConstructor {
  new (): BrowserSpeechRecognition;
}

declare global {
  interface Window {
    SpeechRecognition?: BrowserSpeechRecognitionConstructor;
    webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor;
  }
}

export type JarvisEventType =
  | "intake_state"
  | "brain_adapter_state"
  | "brain_state"
  | "voice_state"
  | "voice_session_state"
  | "wake_state"
  | "tts_state"
  | "hermes_state"
  | "approval_state"
  | "mission_state"
  | "camera_state"
  | "recording_state"
  | "memory_state"
  | "risk_state"
  | "execution_state"
  | "audit_event"
  | "remote_state"
  | "doctor_state"
  | "performance_state"
  | "sensor_ledger_state"
  | "policy_state"
  | "heartbeat";

export interface JarvisEvent {
  schema_version?: string;
  event_id?: string;
  id: string;
  event_type: JarvisEventType | string;
  type?: JarvisEventType | string;
  created_at?: string;
  timestamp: string;
  source: string;
  status: string;
  risk_level?: string;
  read_only: boolean;
  can_execute: boolean;
  stream_can_execute?: boolean;
  secret_free: boolean;
  raw_audio_included: boolean;
  camera_frames_included: boolean;
  payload: Record<string, unknown>;
}

export interface JarvisEventSnapshot {
  schema_version?: string;
  snapshot_id?: string;
  generated_at: string;
  created_at?: string;
  stream: {
    endpoint: string;
    sse_endpoint: string;
    mode: string;
    schema_version?: string;
    read_only: boolean;
    allowed_methods: string[];
    required_event_fields?: string[];
    heartbeat_enabled?: boolean;
    disconnect_safe?: boolean;
    no_secrets: boolean;
    no_raw_audio: boolean;
    no_camera_frames: boolean;
    no_frontend_execution: boolean;
    stream_can_execute?: boolean;
  };
  heartbeat?: JarvisEvent;
  events: JarvisEvent[];
}

export interface LocalVoiceLoopController {
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
  beginLocalVoiceLoop: () => void;
  cancelLocalVoiceLoop: () => void;
}
