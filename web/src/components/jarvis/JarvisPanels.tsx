import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";

export function MiniStat({
  label,
  value,
  variant = "outline",
}: {
  label: string;
  value: string;
  variant?: "outline" | "warning" | "destructive" | "success";
}) {
  return (
    <div className="min-w-0 border border-cyan-300/15 bg-[#061526]/55 px-3 py-2 shadow-[inset_0_0_24px_rgba(34,211,238,0.04)]">
      <p className="font-display text-[0.68rem] uppercase tracking-[0.12em] text-cyan-200/55">{label}</p>
      <div className="mt-1 flex items-center justify-between gap-2">
        <p className="truncate font-mono-ui text-xs text-cyan-50">{value}</p>
        <Badge className={variant === "destructive" ? "" : "border-cyan-300/25 bg-cyan-300/10 text-cyan-100"} variant={variant}>
          {variant}
        </Badge>
      </div>
    </div>
  );
}

export function StatusList({ items }: { items: readonly (readonly [string, string])[] }) {
  return (
    <dl className="grid gap-1">
      {items.map(([label, value]) => (
        <div key={`${label}-${value}`} className="flex items-center justify-between gap-4 border-b border-cyan-300/10 px-2 py-2 last:border-b-0">
          <dt className="font-display text-[0.68rem] uppercase tracking-[0.14em] text-cyan-200/55">{label}</dt>
          <dd className="max-w-[62%] break-words text-right font-mono-ui text-xs text-cyan-50/90">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function SafetyLine({ children }: { children: ReactNode }) {
  return (
    <p className="border-l-2 border-cyan-300/55 bg-cyan-300/[0.055] px-3 py-2 font-display text-xs text-cyan-100/82">
      {children}
    </p>
  );
}

export function ContractVault({ groups }: { groups: readonly (readonly [string, readonly string[]])[] }) {
  return (
    <div className="grid gap-3">
      {groups.map(([title, items]) => (
        <details key={title} className="border border-cyan-300/15 bg-[#05111f]/55 p-3">
          <summary className="cursor-pointer font-expanded text-xs font-bold uppercase tracking-[0.12em] text-cyan-100">
            {title}
          </summary>
          <div className="mt-3 flex flex-wrap gap-2">
            {items.map((item) => (
              <Badge key={`${title}-${item}`} variant="outline">
                {item}
              </Badge>
            ))}
          </div>
        </details>
      ))}
    </div>
  );
}
