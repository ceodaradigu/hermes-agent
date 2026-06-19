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
  const primaryCard = cards[0];
  return (
    <article className="relative overflow-hidden rounded-[2px] border border-cyan-100/12 bg-[#000711]/66 p-3 shadow-[0_0_42px_rgba(34,211,238,0.06)] backdrop-blur-md" data-testid="jarvis-approval-summary" data-panel-style="compact-approval-not-dashboard">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-red-200" />
          <h2 className="font-expanded text-xs font-bold uppercase tracking-[0.16em] text-cyan-50/88">Approvals · Consola de Aprobación</h2>
        </div>
        <Badge className="border-red-400/40 bg-red-950/30 text-red-100" variant="outline">{valueText(pendingCount)} pendientes</Badge>
      </div>
      {primaryCard && (
        <div className="border border-amber-300/24 bg-[#070b12]/76 p-3 shadow-[0_0_30px_rgba(250,204,21,0.07),inset_0_0_32px_rgba(230,251,255,0.018)]">
          <div className="flex items-start justify-between gap-3">
            <p className="line-clamp-1 font-display text-[0.72rem] uppercase tracking-[0.14em] text-cyan-50">{valueText(primaryCard.title)}</p>
            <span className="font-display text-[0.62rem] uppercase tracking-[0.16em] text-amber-200">
              {valueText(primaryCard.risk_level)}
            </span>
          </div>
          <p className="mt-2 line-clamp-2 font-mono-ui text-[0.7rem] text-cyan-100/58">{valueText(primaryCard.action)}</p>
          <p className="mt-2 font-mono-ui text-[0.68rem] text-cyan-100/52">esperando revisión humana; coste est. {valueText(primaryCard.estimated_cost)}</p>
        </div>
      )}
      <details className="mt-3 border border-cyan-100/8 bg-[#000711]/42 p-2">
        <summary className="cursor-pointer font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-100/58">approval details</summary>
        <div className="mt-2 grid gap-2">
          {cards.slice(0, 3).map((card) => (
            <div key={card.id} className="border border-cyan-100/9 bg-[#050b13]/70 p-2">
              <div className="flex items-start justify-between gap-3">
                <p className="line-clamp-1 font-display text-[0.68rem] uppercase tracking-[0.12em] text-cyan-50">{valueText(card.title)}</p>
                <span className="font-display text-[0.62rem] uppercase tracking-[0.14em] text-cyan-200/75">
                  {valueText(card.risk_level)}
                </span>
              </div>
              <p className="mt-1 line-clamp-1 font-mono-ui text-[0.68rem] text-cyan-100/48">{valueText(card.action)}</p>
            </div>
          ))}
        </div>
      </details>
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
