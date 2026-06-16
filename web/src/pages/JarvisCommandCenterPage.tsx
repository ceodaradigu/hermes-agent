import {
  Activity,
  BadgeCheck,
  Camera,
  CircleDollarSign,
  Cpu,
  GitBranch,
  Lock,
  MicOff,
  Radar,
  ShieldAlert,
  ShieldCheck,
  Smartphone,
  Square,
  TerminalSquare,
  Workflow,
  ZapOff,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const voiceStates = [
  "offline",
  "online",
  "preview",
  "listening_wake_word",
  "listening_command",
  "thinking",
  "speaking",
  "approval_required",
  "hermes_executing",
  "paused",
  "blocked",
  "kill_switch",
] as const;

const missionFields = [
  ["intención detectada", "unknown"],
  ["plan", "unknown"],
  ["riesgo", "unknown"],
  ["permisos necesarios", "none/unknown"],
  ["estado", "ready for future wiring"],
] as const;

const approvalCards = [
  {
    accion: "Demo preview: preparar resumen de estado local",
    riesgo: "bajo / demo",
    coste: "unknown",
    afecta: "datos demo locales",
    rollback: "no aplica; no hay ejecución real",
  },
  {
    accion: "Demo preview: candidato de deploy",
    riesgo: "alto / strong approval futuro",
    coste: "unknown",
    afecta: "producción futura no conectada",
    rollback: "requerido antes de cualquier deploy real",
  },
] as const;

const modules = [
  ["Mission Loop", "preview"],
  ["Research", "prepare-only"],
  ["Product Revenue", "prepare-only"],
  ["Routine Ops", "prepare-only"],
  ["Moonshot Lab", "prepare-only"],
  ["Voice", "preview"],
  ["Wake Listener", "disabled"],
  ["Camera/Vision", "disabled"],
  ["Mobile Companion", "preview"],
  ["Memory/Learning", "prepare-only"],
  ["Hermes", "gated"],
] as const;

const privacyRows = [
  ["cámara", "off"],
  ["preview", "disabled"],
  ["recording", "off"],
  ["vision analysis", "disabled"],
  ["storage", "off"],
  ["scope", "none"],
] as const;

const mobileRows = [
  ["mobile companion", "preview"],
  ["approvals desde móvil", "future gated"],
  ["estado remoto", "unknown"],
  ["kill switch remoto", "future gated"],
  ["Hermes directo desde móvil", "forbidden"],
] as const;

const financeRows = [
  ["coste real", "unknown"],
  ["coste estimado", "unknown"],
  ["revenue confirmado", "unknown"],
  ["revenue proyectado", "unknown"],
  ["ROI", "unknown"],
] as const;

const productFlow = [
  "Idea",
  "Validación",
  "Blueprint",
  "Código",
  "Landing",
  "Deploy candidate",
  "Monetización",
] as const;

const timelineEvents = [
  "Dashboard shell loaded",
  "Runtime actions disabled",
  "Sensors disabled",
  "Hermes execution not active",
  "Metrics unknown until measured",
] as const;

const headerBadges = ["Estado: local", "Modo: preview-first", "Sin autonomía libre"] as const;

function StatusList({ items }: { items: readonly (readonly [string, string])[] }) {
  return (
    <dl className="grid gap-2">
      {items.map(([label, value]) => (
        <div key={label} className="flex items-center justify-between gap-4 border border-border/60 bg-background/30 px-3 py-2">
          <dt className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">{label}</dt>
          <dd className="font-mono-ui text-xs text-foreground">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function SafetyLine({ children }: { children: React.ReactNode }) {
  return (
    <p className="border-l-2 border-warning/70 bg-warning/10 px-3 py-2 font-display text-xs text-warning">
      {children}
    </p>
  );
}

export default function JarvisCommandCenterPage() {
  return (
    <div className="flex flex-col gap-6">
      <section className="border border-border bg-card/70 p-5">
        <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              {headerBadges.map((badge) => (
                <Badge key={badge} variant={badge === "Sin autonomía libre" ? "warning" : "outline"}>
                  {badge}
                </Badge>
              ))}
            </div>
            <div className="space-y-2">
              <h1 className="font-expanded text-3xl font-bold uppercase tracking-[0.08em] blend-lighter md:text-5xl">
                Centro de Mando JARVIS
              </h1>
              <p className="max-w-3xl font-display text-base text-muted-foreground">
                JARVIS gobierna. Hermes ejecuta.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">autonomía</p>
                <p className="mt-1 font-mono-ui text-sm">Sin autonomía libre</p>
              </div>
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">runtime</p>
                <p className="mt-1 font-mono-ui text-sm">read-only shell</p>
              </div>
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">sensores</p>
                <p className="mt-1 font-mono-ui text-sm">disabled</p>
              </div>
            </div>
          </div>

          <aside className="border border-destructive/50 bg-destructive/10 p-4">
            <div className="flex items-center gap-3">
              <ShieldAlert className="h-6 w-6 text-destructive" />
              <div>
                <h2 className="font-expanded text-sm font-bold uppercase tracking-[0.12em] text-destructive">
                  Kill Switch
                </h2>
                <p className="font-mono-ui text-xs text-destructive/80">not wired in this PR</p>
              </div>
            </div>
            <Button disabled type="button" variant="destructive" className="mt-4 w-full">
              KILL SWITCH
            </Button>
            <p className="mt-3 font-display text-xs text-destructive/80">
              No hay ejecución real que detener desde esta shell.
            </p>
          </aside>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-warning" />
              <CardTitle>Núcleo / Voice Core visual</CardTitle>
            </div>
            <CardDescription>Estado seguro actual: preview local.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 lg:grid-cols-[260px_1fr]">
            <div className="relative flex min-h-[260px] items-center justify-center border border-border/70 bg-background/40">
              <div className="absolute inset-6 border border-warning/20" />
              <div className="absolute inset-12 border border-emerald-400/20" />
              <div className="flex h-32 w-32 items-center justify-center border border-warning/80 bg-warning/10">
                <MicOff className="h-11 w-11 text-warning" />
              </div>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {voiceStates.map((state) => (
                  <Badge key={state} variant={state === "preview" ? "warning" : "outline"}>
                    {state}
                  </Badge>
                ))}
              </div>
              <div className="grid gap-2 sm:grid-cols-3">
                <div className="border border-border/70 p-3">
                  <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">micrófono real</p>
                  <p className="mt-1 font-mono-ui text-sm">no activo</p>
                </div>
                <div className="border border-border/70 p-3">
                  <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">wake word real</p>
                  <p className="mt-1 font-mono-ui text-sm">no activo</p>
                </div>
                <div className="border border-border/70 p-3">
                  <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">subtítulos</p>
                  <p className="mt-1 font-mono-ui text-sm">placeholder/local</p>
                </div>
              </div>
              <SafetyLine>La wake phrase nunca aprueba acciones.</SafetyLine>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Workflow className="h-5 w-5 text-success" />
              <CardTitle>Mission Control</CardTitle>
            </div>
            <CardDescription>Panel visual para futuras misiones; no crea misiones reales todavía.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <textarea
              disabled
              className="min-h-28 w-full resize-none border border-border bg-background/50 p-3 font-mono-ui text-xs text-muted-foreground disabled:opacity-70"
              value="Entrada preview deshabilitada. No hay planner ni ejecución conectados en PR #145."
              readOnly
            />
            <StatusList items={missionFields} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-warning" />
              <CardTitle>Consola de Aprobación</CardTitle>
            </div>
            <CardDescription>Tarjetas demo/preview; no datos reales, no approvals reales.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {approvalCards.map((card) => (
              <article key={card.accion} className="border border-border/70 bg-background/35 p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <Badge variant="warning">demo/preview</Badge>
                  <Badge variant="outline">preview-only</Badge>
                </div>
                <StatusList
                  items={[
                    ["acción", card.accion],
                    ["riesgo", card.riesgo],
                    ["coste", card.coste],
                    ["afecta", card.afecta],
                    ["rollback", card.rollback],
                  ]}
                />
                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  <Button disabled type="button" variant="outline">Aprobar · preview-only</Button>
                  <Button disabled type="button" variant="outline">Rechazar · preview-only</Button>
                  <Button disabled type="button" variant="outline">Modificar alcance · preview-only</Button>
                  <Button disabled type="button" variant="outline">Pedir explicación · preview-only</Button>
                </div>
              </article>
            ))}
            <div className="grid gap-2">
              <SafetyLine>La wake phrase nunca aprueba acciones.</SafetyLine>
              <SafetyLine>Las acciones sensibles requieren aprobación humana.</SafetyLine>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TerminalSquare className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Hermes Execution / Ejecución Hermes</CardTitle>
            </div>
            <CardDescription>Visibilidad del ejecutor interno; sin ejecución activa.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">JARVIS</p>
                <p className="mt-1 font-mono-ui text-sm">no ejecuta</p>
              </div>
              <div className="border border-border/70 bg-background/40 p-3">
                <p className="font-display text-xs uppercase tracking-[0.12em] text-muted-foreground">Hermes</p>
                <p className="mt-1 font-mono-ui text-sm">es el ejecutor</p>
              </div>
            </div>
            <StatusList
              items={[
                ["ejecución activa", "none"],
                ["última ejecución", "unknown"],
                ["coste", "unknown"],
                ["rollback", "unknown"],
              ]}
            />
            <SafetyLine>Hermes ejecuta solo bajo gates válidos.</SafetyLine>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Radar className="h-5 w-5 text-success" />
            <CardTitle>Agent / Module Radar</CardTitle>
          </div>
          <CardDescription>Estados declarativos; no inventan conexión real.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {modules.map(([name, state]) => (
              <div key={name} className="flex items-center justify-between gap-3 border border-border/70 bg-background/35 px-3 py-3">
                <span className="font-display text-sm">{name}</span>
                <Badge variant={state === "disabled" ? "destructive" : state === "gated" ? "warning" : "outline"}>
                  {state}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Camera className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Camera / Vision Privacy</CardTitle>
            </div>
            <CardDescription>Cámara real apagada; sin permisos del navegador.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatusList items={privacyRows} />
            <SafetyLine>La cámara no graba por defecto.</SafetyLine>
            <SafetyLine>La visión solo se activa con permiso explícito.</SafetyLine>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Smartphone className="h-5 w-5 text-success" />
              <CardTitle>Mobile Companion</CardTitle>
            </div>
            <CardDescription>Superficie futura, no runtime remoto.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatusList items={mobileRows} />
            <SafetyLine>Mobile es una interfaz, no un runtime.</SafetyLine>
            <SafetyLine>Mobile no llama a Hermes directamente.</SafetyLine>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <CircleDollarSign className="h-5 w-5 text-warning" />
              <CardTitle>Finance / ROI</CardTitle>
            </div>
            <CardDescription>Métricas financieras solo con evidencia.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <StatusList items={financeRows} />
            <SafetyLine>No fake metrics.</SafetyLine>
            <SafetyLine>Si no hay evidencia, mostrar unknown.</SafetyLine>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_0.85fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-success" />
              <CardTitle>Product Builder Adaptativo</CardTitle>
            </div>
            <CardDescription>Flujo visual de producto; sin deploy, Stripe ni revenue real.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-2 md:grid-cols-7">
              {productFlow.map((step) => (
                <div key={step} className="border border-border/70 bg-background/35 p-3 text-center">
                  <p className="font-display text-xs uppercase tracking-[0.1em]">{step}</p>
                  <Badge variant="outline" className="mt-2">preview</Badge>
                </div>
              ))}
            </div>
            <div className="grid gap-2 lg:grid-cols-3">
              <SafetyLine>Deploy real requiere approval fuerte.</SafetyLine>
              <SafetyLine>Stripe/checkout real requiere approval fuerte.</SafetyLine>
              <SafetyLine>Revenue real no se inventa.</SafetyLine>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Live Timeline / Audit Preview</CardTitle>
            </div>
            <CardDescription>Eventos locales/static de carga de la shell.</CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-3">
              {timelineEvents.map((event) => (
                <li key={event} className="grid grid-cols-[20px_1fr] gap-3">
                  <Square className="mt-0.5 h-3 w-3 text-warning" />
                  <span className="font-mono-ui text-xs text-foreground">{event}</span>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Lock className="h-5 w-5 text-warning" />
            <CardTitle>Separación JARVIS / Hermes</CardTitle>
          </div>
          <CardDescription>Contrato visible de esta shell local.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <div className="border border-border/70 bg-background/35 p-4">
            <BadgeCheck className="mb-3 h-5 w-5 text-success" />
            <p className="font-mono-ui text-sm">JARVIS gobierna intención, riesgo, policy, approval y auditoría.</p>
          </div>
          <div className="border border-border/70 bg-background/35 p-4">
            <TerminalSquare className="mb-3 h-5 w-5 text-muted-foreground" />
            <p className="font-mono-ui text-sm">Hermes ejecuta solo cuando JARVIS entrega gates válidos.</p>
          </div>
          <div className="border border-border/70 bg-background/35 p-4">
            <ZapOff className="mb-3 h-5 w-5 text-warning" />
            <p className="font-mono-ui text-sm">Esta pantalla no llama a Hermes, no aprueba y no ejecuta.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
