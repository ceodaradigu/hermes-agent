import { Download, Mic2, Square, Trash2, Waves } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { JarvisLocalRecording, JarvisRecordingAuditEvent, JarvisRecordingState } from "@/hooks/jarvis/useJarvisAudioRecorder";
import { SafetyLine } from "./JarvisPanels";

interface JarvisRecordingPanelProps {
  recordingState: JarvisRecordingState;
  recordingError: string;
  recording: JarvisLocalRecording | null;
  auditEvents: JarvisRecordingAuditEvent[];
  onStart: () => void;
  onStop: () => void;
  onDelete: () => void;
}

function formatBytes(value: number) {
  if (!Number.isFinite(value) || value <= 0) return "0 B";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(ms: number) {
  if (!Number.isFinite(ms) || ms <= 0) return "0s";
  const seconds = Math.round(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return minutes ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`;
}

export function JarvisRecordingPanel({
  recordingState,
  recordingError,
  recording,
  auditEvents,
  onStart,
  onStop,
  onDelete,
}: JarvisRecordingPanelProps) {
  const recordingActive = recordingState === "recording" || recordingState === "permission_requested" || recordingState === "stopping";
  const startDisabled = recordingActive || recordingState === "not_supported";
  const stopDisabled = recordingState !== "recording" && recordingState !== "permission_requested";

  return (
    <article
      className="relative overflow-hidden rounded-[2px] border border-cyan-100/10 bg-[#000711]/52 p-3 backdrop-blur"
      data-testid="jarvis-local-audio-recorder"
      data-panel-style="folded-raw-audio-local-only"
    >
      <div className="mb-2 flex items-center justify-between gap-2 border-b border-cyan-100/9 pb-2">
        <div className="flex items-center gap-2">
          <Waves className="h-4 w-4 text-[#e6fbff]/52" />
          <h2 className="font-expanded text-xs font-bold uppercase tracking-[0.14em] text-cyan-50/80">Audio bruto local</h2>
        </div>
        <Badge className={recordingActive ? "border-red-300/50 bg-red-500/15 text-red-100" : "border-cyan-100/16 bg-[#e6fbff]/[0.04] text-cyan-100/70"} variant="outline">
          {recordingState}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Button
          disabled={startDisabled}
          aria-disabled={startDisabled}
          type="button"
          variant="outline"
          size="sm"
          onClick={onStart}
          className="border-cyan-100/18 bg-[#e6fbff]/[0.035] text-cyan-50"
        >
          <Mic2 className="mr-2 h-3.5 w-3.5" />
          Grabar
        </Button>
        <Button
          disabled={stopDisabled}
          aria-disabled={stopDisabled}
          type="button"
          variant="outline"
          size="sm"
          onClick={onStop}
          className="border-red-300/30 bg-red-500/[0.08] text-red-100"
        >
          <Square className="mr-2 h-3.5 w-3.5" />
          Stop
        </Button>
      </div>

      {recordingActive && (
        <div className="mt-3 flex items-center gap-2 border border-red-300/30 bg-red-500/10 p-2 font-mono-ui text-xs text-red-100">
          <span className="h-2 w-2 animate-pulse rounded-full bg-red-300" />
          Grabación local visible activa. No se sube al backend.
        </div>
      )}

      {recordingError && <p className="mt-2 font-mono-ui text-xs text-red-100/80">{recordingError}</p>}

      {recording && (
        <div className="mt-3 grid gap-2 border border-cyan-100/9 bg-[#000711]/48 p-2">
          <div className="grid grid-cols-2 gap-2 font-mono-ui text-[0.7rem] text-cyan-100/60">
            <span>tamaño {formatBytes(recording.sizeBytes)}</span>
            <span>duración {formatDuration(recording.durationMs)}</span>
            <span className="col-span-2 truncate">retención: blob local hasta descargar o borrar</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <a
              href={recording.url}
              download={recording.filename}
              className="inline-flex h-8 items-center justify-center gap-2 border border-cyan-100/18 bg-[#e6fbff]/[0.035] px-3 font-display text-[0.65rem] uppercase tracking-[0.1em] text-cyan-100 hover:bg-foreground/10"
            >
              <Download className="h-3.5 w-3.5" />
              Descargar
            </a>
            <Button type="button" variant="outline" size="sm" onClick={onDelete} className="border-red-300/25 bg-red-500/[0.06] text-red-100">
              <Trash2 className="mr-2 h-3.5 w-3.5" />
              Borrar
            </Button>
          </div>
        </div>
      )}

      <details className="mt-3 border border-cyan-100/9 bg-[#000711]/44 p-2">
        <summary className="cursor-pointer font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-100/70">privacidad audio bruto</summary>
        <div className="mt-2 grid gap-2">
          <SafetyLine>Botón explícito separado de hablar con JARVIS.</SafetyLine>
          <SafetyLine>No STT, no transcripción y no subida al backend.</SafetyLine>
          <SafetyLine>La retención es local: descargar o borrar revocando el blob.</SafetyLine>
          <SafetyLine>La auditoría backend completa queda pendiente; aquí solo hay metadata local visible.</SafetyLine>
        </div>
      </details>

      <div className="mt-2 max-h-16 overflow-auto border border-cyan-100/8 bg-[#000711]/54 p-2">
        {(auditEvents.length ? auditEvents : [{ event: "recorder_idle", at: "local", metadata: { local_only: true } }]).slice(0, 4).map((event) => (
          <p key={`${event.event}-${event.at}`} className="font-mono-ui text-[0.64rem] text-cyan-100/42">
            {event.event} · {event.at}
          </p>
        ))}
      </div>
    </article>
  );
}
