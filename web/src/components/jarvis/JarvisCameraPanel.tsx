import { useState, type RefObject } from "react";
import { Camera, Download, Grip, Maximize2, Minimize2, Play, Square, Trash2, Video } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { JarvisCameraAuditEvent, JarvisCameraState, JarvisLocalVideoRecording, JarvisVideoRecordingState } from "@/hooks/jarvis/useJarvisCameraControl";
import { SafetyLine } from "./JarvisPanels";

export function JarvisCameraPanel({
  cameraState,
  cameraError,
  cameraAuditEvents,
  cameraRisk,
  videoRecordingState,
  videoRecordingError,
  videoRecording,
  videoRef,
  onStart,
  onStop,
  onStartVideoRecording,
  onStopVideoRecording,
  onDeleteVideoRecording,
}: {
  cameraState: JarvisCameraState;
  cameraError: string;
  cameraAuditEvents: JarvisCameraAuditEvent[];
  cameraRisk: string;
  videoRecordingState: JarvisVideoRecordingState;
  videoRecordingError: string;
  videoRecording: JarvisLocalVideoRecording | null;
  videoRef: RefObject<HTMLVideoElement | null>;
  onStart: () => void | Promise<void>;
  onStop: () => void;
  onStartVideoRecording: () => void | Promise<void>;
  onStopVideoRecording: () => void;
  onDeleteVideoRecording: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const cameraEnabled = cameraState === "active";
  const videoRecordingActive = videoRecordingState === "recording";
  const startDisabled = cameraEnabled || cameraState === "permission_requested" || cameraState === "not_supported";
  const stopDisabled = !cameraEnabled && cameraState !== "permission_requested";
  const recordVideoDisabled = videoRecordingActive || videoRecordingState === "permission_requested" || videoRecordingState === "not_supported";
  const stopVideoDisabled = !videoRecordingActive && videoRecordingState !== "permission_requested";

  return (
    <article
      className={
        "relative overflow-hidden rounded-[2px] border border-cyan-300/45 bg-[#03101f]/78 p-3 shadow-[0_0_70px_rgba(34,211,238,0.18)] backdrop-blur-md " +
        (expanded ? "xl:fixed xl:bottom-32 xl:right-6 xl:top-24 xl:z-[60] xl:w-[min(36rem,calc(100vw-3rem))] xl:resize-y xl:overflow-auto" : "")
      }
      data-testid="jarvis-camera-preview-panel"
      data-camera-panel-mode={expanded ? "expanded-local-preview" : "side-dock-local-preview"}
    >
      <div className="mb-2 flex items-center justify-between gap-2 border-b border-cyan-300/18 pb-2">
        <div className="flex items-center gap-2">
          <Grip className="h-4 w-4 text-cyan-200/55" />
          <h2 className="font-expanded text-xs font-bold uppercase tracking-[0.16em] text-cyan-50">Cámara · Preview local</h2>
        </div>
        <Button
          type="button"
          variant="outline"
          size="icon"
          aria-label={expanded ? "Contraer cámara lateral" : "Ampliar cámara lateral"}
          title={expanded ? "Contraer cámara lateral" : "Ampliar cámara lateral"}
          onClick={() => setExpanded((value) => !value)}
          className="h-7 w-7 border-cyan-300/20 bg-cyan-300/[0.04] text-cyan-100"
        >
          {expanded ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
        </Button>
        <Badge className={cameraEnabled ? "" : "border-cyan-300/30 bg-cyan-300/10 text-cyan-100"} variant={cameraEnabled ? "destructive" : "outline"}>
          {cameraEnabled ? "active" : cameraState}
        </Badge>
        <Badge className={videoRecordingActive ? "border-red-300/40 bg-red-500/15 text-red-100" : "border-cyan-300/30 bg-cyan-300/10 text-cyan-100"} variant={videoRecordingActive ? "destructive" : "outline"}>
          vídeo {videoRecordingState}
        </Badge>
      </div>
      <div className="relative aspect-[16/10] overflow-hidden rounded-[1px] border border-cyan-300/35 bg-[#010816] shadow-[inset_0_0_70px_rgba(14,165,233,0.18)]">
        <video ref={videoRef} aria-label="Preview local de cámara JARVIS" className={"absolute inset-0 h-full w-full object-cover " + (cameraEnabled ? "opacity-85" : "opacity-0")} playsInline muted />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_42%,rgba(34,211,238,0.24),transparent_38%),radial-gradient(ellipse_at_50%_85%,rgba(249,115,22,0.08),transparent_38%),linear-gradient(90deg,rgba(34,211,238,0.08)_1px,transparent_1px),linear-gradient(0deg,rgba(125,211,252,0.06)_1px,transparent_1px)] bg-[length:100%_100%,100%_100%,28px_28px,28px_28px]" />
        <div className="absolute inset-x-0 top-1/2 h-px bg-cyan-300/35 shadow-[0_0_18px_rgba(34,211,238,0.6)]" />
        <div className="absolute inset-y-0 left-1/2 w-px bg-cyan-300/18" />
        <div className="absolute inset-4 border border-cyan-200/15" />
        <div className="absolute left-4 top-4 h-7 w-12 border-l border-t border-cyan-200/35" />
        <div className="absolute right-4 top-4 h-7 w-12 border-r border-t border-cyan-200/35" />
        <div className="absolute bottom-4 left-4 h-7 w-12 border-b border-l border-cyan-200/35" />
        <div className="absolute bottom-4 right-4 h-7 w-12 border-b border-r border-cyan-200/35" />
        <div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-200/40 shadow-[0_0_48px_rgba(34,211,238,0.22)]" />
        <Camera className="absolute left-1/2 top-1/2 h-9 w-9 -translate-x-1/2 -translate-y-1/2 text-cyan-100/72 drop-shadow-[0_0_18px_rgba(125,211,252,0.55)]" />
        <div className="absolute inset-x-4 bottom-4 flex items-center justify-between gap-2">
          <Badge className="border-cyan-300/25 bg-[#041728]/80 text-cyan-100" variant="outline">local only</Badge>
          <Badge className="border-cyan-300/25 bg-cyan-300/10 text-cyan-100" variant="outline">{videoRecordingActive ? "grabando vídeo local" : "sin análisis"}</Badge>
        </div>
        {!cameraEnabled && (
          <div className="absolute left-4 right-4 top-4 border border-cyan-300/18 bg-[#010816]/72 px-3 py-2 font-mono-ui text-[0.68rem] text-cyan-100/58">
            cámara apagada · permiso requerido · no backend upload · no frames event stream
          </div>
        )}
        {videoRecordingActive && (
          <div className="absolute right-4 top-4 flex items-center gap-2 border border-red-300/35 bg-red-950/55 px-2 py-1 font-mono-ui text-[0.65rem] uppercase tracking-[0.12em] text-red-100">
            <span className="h-2 w-2 animate-pulse rounded-full bg-red-300" />
            REC local
          </div>
        )}
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2">
        <Button disabled={startDisabled} aria-disabled={startDisabled} type="button" variant="outline" size="sm" onClick={onStart} className="border-cyan-300/20 bg-cyan-300/[0.035] text-cyan-100">
          <Play className="mr-2 h-3.5 w-3.5" />
          Abrir
        </Button>
        <Button disabled={stopDisabled} aria-disabled={stopDisabled} type="button" variant="outline" size="sm" onClick={onStop} className="border-red-300/25 bg-red-500/[0.06] text-red-100">
          <Square className="mr-2 h-3.5 w-3.5" />
          Stop
        </Button>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2">
        <Button disabled={recordVideoDisabled} aria-disabled={recordVideoDisabled} type="button" variant="outline" size="sm" onClick={onStartVideoRecording} className="border-cyan-300/20 bg-cyan-300/[0.035] text-cyan-100">
          <Video className="mr-2 h-3.5 w-3.5" />
          Grabar vídeo
        </Button>
        <Button disabled={stopVideoDisabled} aria-disabled={stopVideoDisabled} type="button" variant="outline" size="sm" onClick={onStopVideoRecording} className="border-red-300/25 bg-red-500/[0.06] text-red-100">
          <Square className="mr-2 h-3.5 w-3.5" />
          Stop vídeo
        </Button>
      </div>
      {videoRecording && (
        <div className="mt-2 grid grid-cols-2 gap-2">
          <a href={videoRecording.url} download={videoRecording.filename} className="inline-flex h-8 items-center justify-center border border-cyan-300/20 bg-cyan-300/[0.035] px-3 font-display text-xs uppercase tracking-[0.12em] text-cyan-100">
            <Download className="mr-2 h-3.5 w-3.5" />
            Descargar vídeo
          </a>
          <Button type="button" variant="outline" size="sm" onClick={onDeleteVideoRecording} className="border-red-300/25 bg-red-500/[0.06] text-red-100">
            <Trash2 className="mr-2 h-3.5 w-3.5" />
            Borrar vídeo
          </Button>
        </div>
      )}
      {cameraError && <p className="mt-2 font-mono-ui text-xs text-red-100/80">{cameraError}</p>}
      {videoRecordingError && <p className="mt-2 font-mono-ui text-xs text-red-100/80">{videoRecordingError}</p>}
      {cameraEnabled && (
        <div className="mt-2 flex items-center gap-2 border border-cyan-300/18 bg-cyan-300/10 p-2 font-mono-ui text-xs text-cyan-100">
          <span className="h-2 w-2 animate-pulse rounded-full bg-cyan-200" />
          Cámara activa solo en preview local. No hay streaming externo.
        </div>
      )}
      <details className="mt-3 border border-cyan-300/10 bg-[#071629]/45 p-2">
        <summary className="cursor-pointer font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-100/70">Privacidad cámara</summary>
        <div className="mt-2 grid gap-2">
          <SafetyLine>Módulo lateral premium ampliable; no mueve runtime ni permisos.</SafetyLine>
          <SafetyLine>La cámara no graba por defecto.</SafetyLine>
          <SafetyLine>Grabar vídeo requiere botón explícito separado.</SafetyLine>
          <SafetyLine>La grabación de vídeo es local, descargable y borrable.</SafetyLine>
          <SafetyLine>Botón explícito, permiso del navegador e indicador visible.</SafetyLine>
          <SafetyLine>No se captura snapshot, no se almacena vídeo y no se sube streaming.</SafetyLine>
          <SafetyLine>No se sube vídeo al backend.</SafetyLine>
          <SafetyLine>No hay proveedor externo de visión.</SafetyLine>
          <SafetyLine>No hay análisis de personas ni identidad.</SafetyLine>
          <SafetyLine>Stop corta tracks locales y borra el preview del elemento video.</SafetyLine>
        </div>
      </details>
      <div className="mt-2 max-h-16 overflow-auto border border-cyan-300/10 bg-[#020b17]/60 p-2">
        {(cameraAuditEvents.length ? cameraAuditEvents : [{ event: "camera_idle", at: "local", metadata: { local_only: true } }]).slice(0, 4).map((event) => (
          <p key={`${event.event}-${event.at}`} className="font-mono-ui text-[0.64rem] text-cyan-100/42">
            {event.event} · {event.at}
          </p>
        ))}
      </div>
      <p className="mt-2 font-mono-ui text-xs text-cyan-100/45">riesgo actual: {cameraRisk}</p>
    </article>
  );
}
