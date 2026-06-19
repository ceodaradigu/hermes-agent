import { useMemo, useState } from "react";
import {
  CheckCircle2,
  FileText,
  MessageSquare,
  OctagonX,
  Play,
  ShieldCheck,
  Square,
  XCircle,
} from "lucide-react";
import type {
  JarvisApprovalCard,
  JarvisExecutionApprovalEnvelope,
  JarvisExecutionDispatchResult,
  JarvisExecutionPreview,
  JarvisGovernedExecutionStatus,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { valueText } from "./utils";

interface JarvisApprovalPanelProps {
  cards: JarvisApprovalCard[];
  pendingCount: unknown;
  executionStatus?: JarvisGovernedExecutionStatus;
  activePreview?: JarvisExecutionPreview | null;
  activeEnvelope?: JarvisExecutionApprovalEnvelope | null;
  dispatchResult?: JarvisExecutionDispatchResult | null;
  busy?: boolean;
  error?: string;
  onCreatePreview?: (payload: { intent: string; targetPath?: string }) => void;
  onRequestApproval?: () => void;
  onApprove?: (payload: { confirmationPhrase?: string; readbackText?: string }) => void;
  onReject?: (reason?: string) => void;
  onCancel?: (reason?: string) => void;
  onStop?: (reason?: string) => void;
  onClarify?: (reason?: string) => void;
  onDispatch?: () => void;
}

function actionList(items?: string[]) {
  if (!items?.length) return ["Sin datos adicionales."];
  return items.slice(0, 3);
}

export function JarvisApprovalPanel({
  cards,
  pendingCount,
  executionStatus,
  activePreview,
  activeEnvelope,
  dispatchResult,
  busy = false,
  error,
  onCreatePreview,
  onRequestApproval,
  onApprove,
  onReject,
  onCancel,
  onStop,
  onClarify,
  onDispatch,
}: JarvisApprovalPanelProps) {
  const [intent, setIntent] = useState("Revisa el estado local de JARVIS y prepara el siguiente paso seguro.");
  const [targetPath, setTargetPath] = useState("");
  const [confirmationPhrase, setConfirmationPhrase] = useState("");
  const [readbackText, setReadbackText] = useState("");
  const [reason, setReason] = useState("");
  const primaryCard = cards[0];
  const previewAction = activePreview?.action;
  const previewBody = activePreview?.preview;
  const risk = valueText(activePreview?.risk_level ?? activeEnvelope?.risk_level ?? primaryCard?.risk_level);
  const approvalLevel = valueText(activePreview?.approval_level ?? activeEnvelope?.approval_level ?? primaryCard?.approval_level);
  const requiresApproval = activePreview?.requires_approval === true || activePreview?.decision === "requires_approval";
  const approvalPending = activeEnvelope?.status === "pending";
  const approvalApproved = activeEnvelope?.status === "approved";
  const canRequestApproval = Boolean(activePreview && requiresApproval && !activeEnvelope && !busy && onRequestApproval);
  const canApprove = Boolean(activeEnvelope && approvalPending && !busy && onApprove);
  const canDispatch = Boolean(activePreview && !busy && onDispatch && (activePreview.decision === "allowed" || approvalApproved));
  const needsReadback = activeEnvelope?.readback_required === true || previewAction?.requires_readback === true;
  const expectedPhrase = valueText(activeEnvelope?.confirmation_phrase, "");
  const influenceCount = activePreview?.preview?.memory_influence?.length ?? 0;
  const dispatchState = valueText(dispatchResult?.state ?? activePreview?.state, "preview");
  const willDo = useMemo(() => actionList(previewBody?.will_do ?? previewAction?.will_do), [previewBody?.will_do, previewAction?.will_do]);
  const willNotDo = useMemo(() => actionList(previewBody?.will_not_do ?? previewAction?.will_not_do), [previewBody?.will_not_do, previewAction?.will_not_do]);

  return (
    <article className="relative overflow-hidden rounded-[2px] border border-cyan-100/12 bg-[#000711]/66 p-3 shadow-[0_0_42px_rgba(34,211,238,0.06)] backdrop-blur-md" data-testid="jarvis-approval-summary" data-panel-style="compact-governed-approval-not-dashboard">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-amber-200" />
          <h2 className="font-expanded text-xs font-bold uppercase tracking-[0.16em] text-cyan-50/88">Approvals · Consola Gobernada</h2>
        </div>
        <Badge className="border-amber-300/40 bg-amber-400/12 text-amber-100" variant="outline">
          {valueText(pendingCount)} pendientes
        </Badge>
      </div>

      <div className="grid gap-2">
        <label className="grid gap-1 font-mono-ui text-[0.68rem] text-cyan-100/62">
          intención
          <textarea
            className="min-h-[4.25rem] resize-none rounded-[2px] border border-cyan-100/12 bg-[#020811]/78 px-2 py-2 text-[0.72rem] text-cyan-50 outline-none focus:border-cyan-200/45"
            value={intent}
            onChange={(event) => setIntent(event.target.value)}
            spellCheck={false}
          />
        </label>
        <label className="grid gap-1 font-mono-ui text-[0.68rem] text-cyan-100/62">
          ruta exacta opcional
          <input
            className="h-8 rounded-[2px] border border-cyan-100/12 bg-[#020811]/78 px-2 text-[0.72rem] text-cyan-50 outline-none focus:border-cyan-200/45"
            value={targetPath}
            onChange={(event) => setTargetPath(event.target.value)}
            placeholder="docs/archivo.md"
          />
        </label>
        <Button
          type="button"
          size="sm"
          disabled={busy || !intent.trim() || !onCreatePreview}
          onClick={() => onCreatePreview?.({ intent, targetPath: targetPath.trim() || undefined })}
          className="h-8 border-cyan-200/28 bg-cyan-200/12 text-cyan-50 hover:bg-cyan-200/18"
          variant="outline"
        >
          <FileText className="h-3.5 w-3.5" />
          Crear preview
        </Button>
      </div>

      <div className="mt-3 border border-amber-300/24 bg-[#070b12]/76 p-3 shadow-[0_0_30px_rgba(250,204,21,0.07),inset_0_0_32px_rgba(230,251,255,0.018)]">
        <div className="flex items-start justify-between gap-3">
          <p className="line-clamp-2 font-display text-[0.72rem] uppercase tracking-[0.12em] text-cyan-50">
            {valueText(previewAction?.title ?? previewBody?.title ?? primaryCard?.title, "Sin preview activo")}
          </p>
          <span className="font-display text-[0.62rem] uppercase tracking-[0.16em] text-amber-200">{risk}</span>
        </div>
        <p className="mt-2 line-clamp-3 font-mono-ui text-[0.7rem] text-cyan-100/60">
          {valueText(previewAction?.summary ?? previewBody?.summary ?? primaryCard?.action)}
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2 font-mono-ui text-[0.66rem] text-cyan-100/62">
          <span>decision {valueText(activePreview?.decision ?? primaryCard?.status)}</span>
          <span>approval {approvalLevel}</span>
          <span>estado {dispatchState}</span>
          <span>memoria {influenceCount}</span>
        </div>
        {activePreview?.protected_message && (
          <p className="mt-3 border border-red-300/24 bg-red-950/20 p-2 font-mono-ui text-[0.68rem] text-red-100">
            {activePreview.protected_message}
          </p>
        )}
      </div>

      <details className="mt-3 border border-cyan-100/8 bg-[#000711]/42 p-2" open={Boolean(activePreview)}>
        <summary className="cursor-pointer font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-100/58">preview / risk / audit</summary>
        <div className="mt-2 grid gap-2 font-mono-ui text-[0.68rem] text-cyan-100/56">
          <p>audit: {valueText(previewBody?.audit_destination, "PersistentAuditLedger metadata-only")}</p>
          <p>motivo approval: {valueText(primaryCard?.reason ?? activePreview?.denied_reason ?? activePreview?.unsupported_reason)}</p>
          <p>stop plan: {valueText(previewBody?.stop_plan ?? previewAction?.stop_plan ?? primaryCard?.stop_plan)}</p>
          <p>rollback: {valueText(previewBody?.rollback_plan ?? previewAction?.rollback_plan ?? primaryCard?.rollback_plan)}</p>
          <div className="grid grid-cols-2 gap-2">
            <div className="border border-cyan-100/9 bg-[#050b13]/70 p-2">
              <p className="mb-1 font-display uppercase tracking-[0.12em] text-cyan-50/80">hará</p>
              {willDo.map((item) => <p key={item}>- {item}</p>)}
            </div>
            <div className="border border-cyan-100/9 bg-[#050b13]/70 p-2">
              <p className="mb-1 font-display uppercase tracking-[0.12em] text-cyan-50/80">no hará</p>
              {willNotDo.map((item) => <p key={item}>- {item}</p>)}
            </div>
          </div>
        </div>
      </details>

      <div className="mt-3 grid gap-2">
        {expectedPhrase && (
          <label className="grid gap-1 font-mono-ui text-[0.68rem] text-cyan-100/62">
            confirmación fuerte
            <input
              className="h-8 rounded-[2px] border border-amber-300/20 bg-[#020811]/78 px-2 text-[0.72rem] text-cyan-50 outline-none focus:border-amber-200/55"
              value={confirmationPhrase}
              onChange={(event) => setConfirmationPhrase(event.target.value)}
              placeholder={expectedPhrase}
            />
          </label>
        )}
        {needsReadback && (
          <label className="grid gap-1 font-mono-ui text-[0.68rem] text-cyan-100/62">
            readback
            <input
              className="h-8 rounded-[2px] border border-amber-300/20 bg-[#020811]/78 px-2 text-[0.72rem] text-cyan-50 outline-none focus:border-amber-200/55"
              value={readbackText}
              onChange={(event) => setReadbackText(event.target.value)}
              placeholder={valueText(activeEnvelope?.readback_text, "Repite alcance, riesgo y stop plan.")}
            />
          </label>
        )}
        <label className="grid gap-1 font-mono-ui text-[0.68rem] text-cyan-100/62">
          razón / aclaración
          <input
            className="h-8 rounded-[2px] border border-cyan-100/12 bg-[#020811]/78 px-2 text-[0.72rem] text-cyan-50 outline-none focus:border-cyan-200/45"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="scope, rechazo, cancelación o stop"
          />
        </label>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <Button type="button" disabled={!canRequestApproval} onClick={onRequestApproval} variant="outline" size="sm">
          <ShieldCheck className="h-3.5 w-3.5" />
          Pedir approval
        </Button>
        <Button
          type="button"
          disabled={!canApprove}
          onClick={() => onApprove?.({ confirmationPhrase, readbackText })}
          variant="outline"
          size="sm"
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          Aprobar
        </Button>
        <Button type="button" disabled={!activeEnvelope || !onReject || busy} onClick={() => onReject?.(reason)} variant="outline" size="sm">
          <XCircle className="h-3.5 w-3.5" />
          Rechazar
        </Button>
        <Button type="button" disabled={!onCancel || busy || !activePreview} onClick={() => onCancel?.(reason)} variant="outline" size="sm">
          <OctagonX className="h-3.5 w-3.5" />
          Cancelar
        </Button>
        <Button type="button" disabled={!onClarify || busy || !activeEnvelope} onClick={() => onClarify?.(reason)} variant="outline" size="sm">
          <MessageSquare className="h-3.5 w-3.5" />
          Aclarar
        </Button>
        <Button type="button" disabled={!onStop || busy} onClick={() => onStop?.(reason)} variant="outline" size="sm">
          <Square className="h-3.5 w-3.5" />
          Stop
        </Button>
      </div>

      <Button
        type="button"
        disabled={!canDispatch}
        onClick={onDispatch}
        className="mt-2 h-8 w-full border-emerald-300/24 bg-emerald-300/12 text-emerald-50 hover:bg-emerald-300/18"
        variant="outline"
        size="sm"
      >
        <Play className="h-3.5 w-3.5" />
        Dispatch gobernado
      </Button>

      {error && <p className="mt-3 border-t border-red-300/18 pt-3 font-mono-ui text-[0.68rem] text-red-100">{error}</p>}
      <p className="mt-3 border-t border-cyan-300/12 pt-3 text-center font-display text-[0.66rem] uppercase tracking-[0.14em] text-cyan-100/50">
        Backend-gated · no Hermes directo · no wake approval · no shell libre
      </p>
      <span className="sr-only">execution status source {valueText(executionStatus?.source_endpoint, "/mark-3/execution/status")}</span>
    </article>
  );
}
