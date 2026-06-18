import { ShieldCheck } from "lucide-react";
import type { JarvisApprovalCard } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { valueText } from "./utils";

export function JarvisApprovalPanel({
  cards,
  pendingCount,
}: {
  cards: JarvisApprovalCard[];
  pendingCount: unknown;
}) {
  return (
    <article className="relative overflow-hidden rounded-[2px] border border-cyan-300/18 bg-[#03101f]/76 p-4 shadow-[0_0_58px_rgba(34,211,238,0.11)] backdrop-blur-md" data-testid="jarvis-approval-summary">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-red-200" />
          <h2 className="font-expanded text-xs font-bold uppercase tracking-[0.16em] text-cyan-50">Approvals · Consola de Aprobación</h2>
        </div>
        <Badge className="border-red-400/40 bg-red-950/30 text-red-100" variant="outline">{valueText(pendingCount)} pendientes</Badge>
      </div>
      <div className="grid gap-3">
        {cards.slice(0, 3).map((card, index) => (
          <div
            key={card.id}
            className={
              "border bg-[#07111d]/76 p-3 shadow-[inset_0_0_38px_rgba(34,211,238,0.025)] " +
              (index === 0 ? "border-red-400/35 shadow-[0_0_36px_rgba(248,113,113,0.12)]" : "border-cyan-300/18")
            }
          >
            <div className="flex items-start justify-between gap-3">
              <p className="line-clamp-1 font-display text-[0.72rem] uppercase tracking-[0.14em] text-cyan-50">{valueText(card.title)}</p>
              <span className={index === 0 ? "font-display text-[0.62rem] uppercase tracking-[0.16em] text-red-300" : "font-display text-[0.62rem] uppercase tracking-[0.16em] text-cyan-200/75"}>
                {valueText(card.risk_level)}
              </span>
            </div>
            <p className="mt-2 line-clamp-1 font-mono-ui text-[0.7rem] text-cyan-100/48">{valueText(card.action)}</p>
            <p className="mt-2 font-mono-ui text-[0.68rem] text-cyan-100/55">coste est. {valueText(card.estimated_cost)}</p>
          </div>
        ))}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        {["Aprobar", "Rechazar", "Modificar alcance", "Pedir explicación"].map((label) => (
          <Button key={label} disabled aria-disabled="true" type="button" variant="outline" size="sm">
            {label}
          </Button>
        ))}
      </div>
      <p className="mt-3 border-t border-cyan-300/12 pt-3 text-center font-display text-[0.68rem] uppercase tracking-[0.16em] text-cyan-100/50">
        Preview-only: approval execution is not wired in this PR
      </p>
    </article>
  );
}
