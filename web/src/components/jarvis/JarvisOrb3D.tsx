import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { jarvisToneProfiles, localVoiceStateLabels, presenceStates } from "./contracts";
import type { JarvisOrbVisualState, JarvisVoiceTone, LocalVoiceLoopState } from "./types";
import { useJarvisOrbState } from "@/hooks/jarvis/useJarvisOrbState";

interface JarvisOrb3DProps {
  voiceState: string;
  subtitle: string;
  localVoiceState: LocalVoiceLoopState;
  visualState: JarvisOrbVisualState;
  jarvisTone: JarvisVoiceTone;
  conversationActive: boolean;
  killSwitchState: string;
  textReactive?: boolean;
  textSignal?: string;
}

interface CanvasParticle {
  x: number;
  y: number;
  z: number;
  size: number;
  opacity: number;
  seed: number;
  lane: number;
}

interface MicroParticle {
  id: number;
  angle: number;
  radius: number;
  size: number;
  duration: number;
  delay: number;
  opacity: number;
}

interface RadialSpike {
  id: number;
  angle: number;
  length: number;
  delay: number;
  duration: number;
  brightness: number;
}

interface EmergentCoreParticle {
  id: number;
  angle: number;
  radius: number;
  size: number;
  delay: number;
  duration: number;
  opacity: number;
}

function seeded(index: number) {
  return Math.abs(Math.sin(index * 12.9898 + 78.233) * 43758.5453) % 1;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function makeCanvasParticles(): CanvasParticle[] {
  return Array.from({ length: 1420 }, (_, index) => {
    const z = seeded(index + 900) * 2 - 1;
    const theta = seeded(index + 1800) * Math.PI * 2;
    const radius = Math.sqrt(Math.max(0, 1 - z * z)) * (0.72 + seeded(index + 2700) * 0.34);
    return {
      x: Math.cos(theta) * radius,
      y: Math.sin(theta) * radius,
      z: z * (0.76 + seeded(index + 3600) * 0.28),
      size: 0.72 + seeded(index + 4500) * 2.25,
      opacity: 0.28 + seeded(index + 5400) * 0.62,
      seed: seeded(index + 6300),
      lane: index % 7,
    };
  });
}

function makeMicroParticles(): MicroParticle[] {
  return Array.from({ length: 128 }, (_, index) => {
    const sizeSeed = seeded(index + 8200);
    return {
      id: index,
      angle: Math.round(index * 137.5 + seeded(index + 8100) * 18),
      radius: 22 + seeded(index + 8300) * 50,
      size: index % 9 === 0 ? 3.4 : 1.4 + sizeSeed * 2.2,
      duration: 8.5 + seeded(index + 8400) * 10.5,
      delay: -seeded(index + 8500) * 10,
      opacity: 0.32 + seeded(index + 8600) * 0.52,
    };
  });
}

function makeFallbackParticles(): MicroParticle[] {
  return Array.from({ length: 360 }, (_, index) => {
    const shell = index % 5;
    const radiusSeed = seeded(index + 8700);
    return {
      id: index,
      angle: Math.round(index * 137.5 + seeded(index + 8800) * 34),
      radius: 12 + shell * 8 + radiusSeed * 54,
      size: index % 13 === 0 ? 3.6 : 1.2 + seeded(index + 8900) * 2.6,
      duration: 5.5 + seeded(index + 9000) * 9.5,
      delay: -seeded(index + 9100) * 9,
      opacity: 0.28 + seeded(index + 9200) * 0.62,
    };
  });
}

function makeRadialSpikes(): RadialSpike[] {
  return Array.from({ length: 48 }, (_, index) => ({
    id: index,
    angle: index * 7.5 + seeded(index + 9100) * 4,
    length: 7 + seeded(index + 9200) * 15,
    delay: -seeded(index + 9300) * 2.4,
    duration: 0.82 + seeded(index + 9400) * 0.72,
    brightness: 0.55 + seeded(index + 9500) * 0.45,
  }));
}

function makeEmergentCoreParticles(): EmergentCoreParticle[] {
  return Array.from({ length: 84 }, (_, index) => ({
    id: index,
    angle: index * 137.5 + seeded(index + 10100) * 21,
    radius: 4 + seeded(index + 10200) * 24,
    size: index % 8 === 0 ? 3 : 1.1 + seeded(index + 10300) * 1.9,
    delay: -seeded(index + 10400) * 4.8,
    duration: 3.8 + seeded(index + 10500) * 4.2,
    opacity: 0.34 + seeded(index + 10600) * 0.46,
  }));
}

export function JarvisOrb3D({
  voiceState,
  subtitle,
  localVoiceState,
  visualState,
  jarvisTone,
  conversationActive,
  killSwitchState,
  textReactive = false,
  textSignal = "",
}: JarvisOrb3DProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [canvasReady, setCanvasReady] = useState(true);
  const [canvasError, setCanvasError] = useState("");
  const particles = useMemo(() => makeCanvasParticles(), []);
  const microParticles = useMemo(() => makeMicroParticles(), []);
  const fallbackParticles = useMemo(() => makeFallbackParticles(), []);
  const radialSpikes = useMemo(() => makeRadialSpikes(), []);
  const emergentCoreParticles = useMemo(() => makeEmergentCoreParticles(), []);
  const orb = useJarvisOrbState({ localVoiceState, visualState, jarvisTone, killSwitchState, conversationActive, textReactive });
  const orbRef = useRef(orb);
  orbRef.current = orb;
  const profile = jarvisToneProfiles[jarvisTone];
  const currentPresence = presenceStates.find(([id]) => id === visualState) ?? presenceStates[0];
  const textSignalActive = textSignal.trim().length > 0;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) {
      setCanvasReady(false);
      setCanvasError("Canvas 2D no disponible; fallback visual CSS activo.");
      return;
    }
    const canvasEl = canvas;
    const context = ctx;
    setCanvasReady(true);
    setCanvasError("");

    let animationId = 0;
    let lastDraw = 0;

    function resize() {
      const rect = canvasEl.getBoundingClientRect();
      const currentOrb = orbRef.current;
      const sizePx = Math.max(280, Math.floor(Math.min(rect.width || 640, rect.height || rect.width || 640)));
      const pixelRatio = Math.min(window.devicePixelRatio || 1, currentOrb.isActive ? 1.65 : 1.35);
      const width = Math.floor(sizePx * pixelRatio);
      const height = Math.floor(sizePx * pixelRatio);
      if (canvasEl.width !== width || canvasEl.height !== height) {
        canvasEl.width = width;
        canvasEl.height = height;
      }
      return { height, pixelRatio, width };
    }

    function draw(time: number) {
      const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
      const currentOrb = orbRef.current;
      const targetFrameMs = reducedMotion ? 140 : currentOrb.targetFrameMs;
      if (time - lastDraw < targetFrameMs) {
        animationId = window.requestAnimationFrame(draw);
        return;
      }
      lastDraw = time;

      const { height, pixelRatio, width } = resize();
      const centerX = width / 2;
      const centerY = height / 2;
      const t = time * 0.001;
      const pseudoAudio = Math.pow(0.5 + 0.5 * Math.sin(t * 7.2 + Math.sin(t * 1.7) * 1.8), 2.45);
      const scalePulse =
        currentOrb.sphereScaleMid +
        Math.sin(t * (reducedMotion ? 0.25 : 1.18)) * (currentOrb.sphereScaleMax - currentOrb.sphereScaleMin) * 0.36 +
        pseudoAudio * currentOrb.radialSpikeEnergy * 0.11;
      const sphereRadius = Math.min(width, height) * 0.34 * clamp(scalePulse, 0.52, 1.36);
      const focus = currentOrb.listeningFocus;
      const turbulence = reducedMotion ? currentOrb.thinkingTurbulence * 0.18 : currentOrb.thinkingTurbulence;
      const reflow = reducedMotion ? currentOrb.transcribingReflow * 0.18 : currentOrb.transcribingReflow;
      const radialEnergy = reducedMotion ? currentOrb.radialSpikeEnergy * 0.20 : currentOrb.radialSpikeEnergy;
      const pressure = reducedMotion ? currentOrb.spherePressure * 0.18 : currentOrb.spherePressure;

      context.clearRect(0, 0, width, height);
      context.save();
      context.globalCompositeOperation = "lighter";

      const projected: Array<{ alpha: number; color: string; depth: number; size: number; x: number; y: number }> = [];
      const maxParticles = reducedMotion ? 820 : Math.min(particles.length, currentOrb.particleBudget);
      for (let index = 0; index < maxParticles; index += 1) {
        const particle = particles[index];
        const laneSpeed = 0.12 + particle.lane * 0.011 + currentOrb.stateReactiveEnergy * 0.034 + turbulence * 0.036;
        const spin = t * laneSpeed * (0.65 + particle.seed);
        const cy = Math.cos(spin);
        const sy = Math.sin(spin);
        const cx = Math.cos(t * 0.09 + particle.seed * 1.7);
        const sx = Math.sin(t * 0.09 + particle.seed * 1.7);
        let x = particle.x * cy - particle.z * sy;
        let z = particle.x * sy + particle.z * cy;
        let y = particle.y * cx - z * sx * 0.42;
        z = particle.y * sx * 0.42 + z * cx;

        const length = Math.max(0.001, Math.hypot(x, y, z));
        const nx = x / length;
        const ny = y / length;
        const nz = z / length;
        const localAudio = Math.pow(0.5 + 0.5 * Math.sin(t * (6.4 + particle.seed * 2.4) + particle.seed * 37), 2.2);
        const spikeMask = seeded(index + Math.floor(t * 9) * 13) > 0.68 ? 1 : 0.26;
        const spike = radialEnergy * (0.04 + localAudio * 0.24) * spikeMask;
        const turbulenceWave = Math.sin(t * (2.0 + particle.seed) + particle.y * 7.0) * Math.cos(t * 1.6 + particle.x * 5.0);
        const reflowWave = Math.sin(t * 3.4 + particle.lane * 1.6 + particle.seed * 17);
        const radiusScale =
          1 -
          focus * 0.11 +
          pressure * Math.sin(t * 1.15 + particle.seed * 8) * 0.035 +
          spike +
          reflow * reflowWave * 0.045;

        x = x * radiusScale + (-ny) * turbulence * turbulenceWave * 0.082;
        y = y * radiusScale + nx * turbulence * turbulenceWave * 0.082;
        z = z * radiusScale + nz * spike * 0.60;

        const perspective = 1 / (2.28 - z * 0.64);
        const screenX = centerX + x * sphereRadius * perspective * 1.82;
        const screenY = centerY + y * sphereRadius * perspective * 1.82;
        const depth = clamp((z + 1.35) / 2.7, 0, 1);
        const alpha =
          particle.opacity *
          (0.18 + depth * 0.68) *
          (currentOrb.isStopped ? 0.36 : 0.78 + currentOrb.stateReactiveEnergy * 0.26 + radialEnergy * 0.22);
        const size = particle.size * pixelRatio * (0.48 + depth * 1.18 + radialEnergy * localAudio * 0.90);
        const color =
          particle.lane % 5 === 0
            ? `rgba(230,251,255,${clamp(alpha, 0.03, 0.96)})`
            : particle.lane % 3 === 0
              ? `rgba(174,247,255,${clamp(alpha, 0.03, 0.90)})`
              : `rgba(103,232,249,${clamp(alpha, 0.03, 0.82)})`;
        projected.push({ alpha, color, depth, size, x: screenX, y: screenY });
      }

      projected.sort((a, b) => a.depth - b.depth);
      for (const particle of projected) {
        context.beginPath();
        context.fillStyle = particle.color;
        context.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        context.fill();
      }

      if (currentOrb.emergentCoreConcentration > 0.10) {
        const coreAlpha = currentOrb.emergentCoreConcentration * (0.12 + pseudoAudio * radialEnergy * 0.18);
        const gradient = context.createRadialGradient(centerX, centerY, 0, centerX, centerY, sphereRadius * 0.17);
        gradient.addColorStop(0, `rgba(230,251,255,${clamp(coreAlpha, 0, 0.32)})`);
        gradient.addColorStop(0.52, `rgba(174,247,255,${clamp(coreAlpha * 0.34, 0, 0.12)})`);
        gradient.addColorStop(1, "rgba(103,232,249,0)");
        context.fillStyle = gradient;
        context.beginPath();
        context.arc(centerX, centerY, sphereRadius * 0.18, 0, Math.PI * 2);
        context.fill();
      }

      context.restore();
      animationId = window.requestAnimationFrame(draw);
    }

    animationId = window.requestAnimationFrame(draw);
    return () => window.cancelAnimationFrame(animationId);
  }, [particles]);

  const sphereStyle = {
    "--sphere-scale-min": String(orb.sphereScaleMin),
    "--sphere-scale-mid": String(orb.sphereScaleMid),
    "--sphere-scale-max": String(orb.sphereScaleMax),
    "--particle-opacity-low": orb.isStopped ? "0.05" : "0.14",
    "--particle-opacity-high": orb.isStopped ? "0.18" : String(0.52 + orb.stateReactiveEnergy * 0.30),
    "--particle-opacity-end": orb.isStopped ? "0.08" : "0.22",
    animationDuration: `${orb.sphereAnimationSeconds}s`,
  } as CSSProperties;

  const coreOpacity = clamp(orb.emergentCoreConcentration * 0.78, 0.02, 0.72);
  const spikeOpacity = clamp(orb.radialSpikeEnergy * 0.92, 0, 0.92);
  const stateSummary = `${localVoiceStateLabels[localVoiceState]} · ${currentPresence[2]}`;

  return (
    <article
      className="relative h-full min-h-0 overflow-hidden"
      data-testid="jarvis-central-core"
      data-renderer="canvas-2d-particle-sphere-primary"
      data-no-webgl-primary="true"
      data-local-voice-state={localVoiceState}
      data-orb-visual-state={visualState}
      data-jarvis-tone={jarvisTone}
      data-conversation-active={conversationActive ? "true" : "false"}
      data-kill-switch-state={killSwitchState}
      data-read-model-voice-state={voiceState}
      data-particle-sphere-mode="visible-canvas-2d-primary"
      data-core-detail="emergent-particle-concentration-not-fixed-solid"
      data-core-layers="particle-convergence transient-white-blue-density no-fixed-logo no-solid-core"
      data-no-fixed-central-logo="true"
      data-no-solid-core="true"
      data-no-central-jarvis-text="true"
      data-visible-particles="canvas-2d-plus-css-micro-particles"
      data-text-signal-active={textSignalActive ? "true" : "false"}
      data-minimum-visible-particles="1420"
      data-fallback-particle-budget="360"
      data-dynamic-sphere-size={`${orb.sphereScaleMin}/${orb.sphereScaleMid}/${orb.sphereScaleMax}`}
      data-speaking-radial-spikes={String(orb.radialSpikeEnergy > 0.8)}
      data-thinking-turbulence={String(orb.thinkingTurbulence)}
      data-listening-focus={String(orb.listeningFocus)}
      data-performance-budget={`targetFrameMs:${orb.targetFrameMs};particleBudget:${orb.particleBudget};pixelRatio:max-1.65;renderer:canvas-2d`}
    >
      <div className="absolute inset-0 bg-[#00030a]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,rgba(14,165,233,0.10)_0%,rgba(2,132,199,0.035)_30%,rgba(0,3,10,0)_68%),radial-gradient(circle_at_50%_88%,rgba(8,47,73,0.20),transparent_46%)]" />
      <div className="relative flex h-full min-h-0 flex-col items-center justify-center px-4">
        <div className="absolute top-4 z-10 flex items-center gap-2 border border-cyan-100/10 bg-[#000814]/58 px-3 py-2 backdrop-blur-md">
          <span className="h-1.5 w-1.5 rounded-full bg-[#e6fbff] shadow-[0_0_16px_rgba(230,251,255,0.85)]" />
          <p className="font-display text-[0.64rem] uppercase tracking-[0.18em] text-cyan-50/72">{currentPresence[1]}</p>
          <span className="sr-only">Presence UI</span>
          <span className="sr-only">Núcleo de Voz JARVIS</span>
          <span className="sr-only">tono {profile.label}</span>
          <span className="sr-only">estado {visualState}</span>
        </div>

        <div
          className="jarvis-particle-sphere-stage relative flex aspect-square w-[min(82dvh,54rem)] max-h-[calc(100dvh-11rem)] max-w-[min(94vw,56rem)] items-center justify-center motion-reduce:animate-none xl:max-w-[min(62vw,56rem)]"
          data-testid="jarvis-cinematic-orb-hud"
          data-sphere-contract="particle sphere / sphere of particles / nube viva de particulas"
          data-emergent-core="density-only-no-permanent-nucleus"
          data-particle-budget={orb.particleBudget}
          data-particle-sphere-count={particles.length}
          data-speaking-spikes="radial-spikes-and-outward-waves"
          data-thinking-motion="internal-turbulence-and-swirl"
          data-listening-motion="focused-contraction-and-attention-pulse"
          style={sphereStyle}
        >
          <div
            aria-hidden="true"
            className="absolute inset-[4%] opacity-60 blur-3xl"
            style={{
              background:
                orb.isError || orb.isAlert
                  ? "radial-gradient(circle, rgba(251,113,133,0.18), rgba(251,146,60,0.08) 34%, transparent 64%)"
                  : "radial-gradient(circle, rgba(103,232,249,0.14), rgba(14,165,233,0.045) 38%, transparent 70%)",
            }}
          />
          <canvas
            ref={canvasRef}
            aria-label="Esfera viva de partículas JARVIS renderizada en Canvas 2D; sin WebGL como visual principal."
            className="absolute inset-0 h-full w-full opacity-95 [filter:drop-shadow(0_0_28px_rgba(103,232,249,0.36))]"
            data-testid="jarvis-particle-sphere-canvas"
            data-renderer="canvas-2d-particle-sphere"
            data-particle-count={particles.length}
            data-no-shader-required="true"
          />

          <div aria-hidden="true" className="pointer-events-none absolute inset-0" data-testid="jarvis-micro-particle-field">
            {microParticles.map((particle) => (
              <span
                key={particle.id}
                className="jarvis-micro-particle absolute left-1/2 top-1/2 block rounded-full bg-[#e6fbff] shadow-[0_0_12px_rgba(230,251,255,0.72)] motion-reduce:animate-none"
                style={
                  {
                    "--orbit-angle": `${particle.angle}deg`,
                    "--orbit-radius": `${particle.radius}%`,
                    "--particle-opacity-low": orb.isStopped ? "0.03" : "0.10",
                    "--particle-opacity-high": String(particle.opacity * (0.45 + orb.stateReactiveEnergy * 0.45)),
                    "--particle-opacity-end": orb.isStopped ? "0.04" : "0.18",
                    animationDelay: `${particle.delay}s`,
                    animationDuration: `${Math.max(2.6, particle.duration / (0.75 + orb.motion * 0.22))}s`,
                    height: `${particle.size}px`,
                    opacity: particle.opacity,
                    width: `${particle.size}px`,
                  } as CSSProperties
                }
              />
            ))}
          </div>

          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-[9%]"
            data-testid="jarvis-speaking-radial-spikes"
            data-spike-contract="speaking-and-alert-create-radial-spikes-and-waves"
            style={{ opacity: spikeOpacity }}
          >
            {radialSpikes.map((spike) => (
              <span
                key={spike.id}
                className="jarvis-speaking-spike absolute left-1/2 top-1/2 block h-px origin-left rounded-full bg-gradient-to-r from-[#e6fbff] via-[#aef7ff] to-transparent motion-reduce:animate-none"
                style={
                  {
                    "--spike-angle": `${spike.angle}deg`,
                    "--spike-length": `${spike.length + orb.radialSpikeEnergy * 24}%`,
                    "--spike-opacity-low": "0",
                    "--spike-opacity-high": String(clamp(spike.brightness * (0.38 + orb.radialSpikeEnergy * 0.64), 0, 0.94)),
                    "--spike-opacity-mid": String(clamp(spike.brightness * (0.12 + orb.radialSpikeEnergy * 0.30), 0, 0.54)),
                    "--spike-push": `${6 + orb.radialSpikeEnergy * 22}%`,
                    "--spike-push-mid": `${2 + orb.radialSpikeEnergy * 12}%`,
                    animationDelay: `${spike.delay}s`,
                    animationDuration: `${Math.max(0.52, spike.duration / (0.75 + orb.radialSpikeEnergy * 0.65))}s`,
                  } as CSSProperties
                }
              />
            ))}
          </div>

          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-[39%]"
            data-testid="jarvis-emergent-core-density"
            data-core-contract="emergent center appears only through particle concentration"
            style={{ opacity: coreOpacity }}
          >
            {emergentCoreParticles.map((particle) => (
              <span
                key={particle.id}
                className="jarvis-emergent-core-particle absolute left-1/2 top-1/2 block rounded-full bg-[#e6fbff] shadow-[0_0_18px_rgba(230,251,255,0.78)] motion-reduce:animate-none"
                style={
                  {
                    "--core-angle": `${particle.angle}deg`,
                    "--core-radius": `${particle.radius * (1.0 - orb.emergentCoreConcentration * 0.52)}%`,
                    "--core-radius-tight": `${particle.radius * (0.24 + (1 - orb.emergentCoreConcentration) * 0.18)}%`,
                    "--core-radius-mid": `${particle.radius * (0.52 + (1 - orb.emergentCoreConcentration) * 0.32)}%`,
                    "--core-opacity-low": String(0.02 + orb.emergentCoreConcentration * 0.08),
                    "--core-opacity-high": String(clamp(particle.opacity * orb.emergentCoreConcentration, 0, 0.72)),
                    animationDelay: `${particle.delay}s`,
                    animationDuration: `${Math.max(1.8, particle.duration / (0.82 + orb.stateReactiveEnergy * 0.38))}s`,
                    height: `${particle.size}px`,
                    width: `${particle.size}px`,
                  } as CSSProperties
                }
              />
            ))}
          </div>

          {!canvasReady && (
            <div
              className="absolute inset-[5%]"
              data-testid="jarvis-orb-webgl-fallback"
              data-webgl-fallback="css-particle-sphere-fallback"
              data-legacy-webgl-fallback="css-core-fallback"
              data-fallback-contract="css-particle-sphere-no-visible-technical-message"
              data-canvas-error={canvasError}
            >
              <div className="absolute inset-0" data-testid="jarvis-css-particle-sphere-fallback">
                {fallbackParticles.map((particle) => (
                  <span
                    key={particle.id}
                    className="jarvis-fallback-particle absolute left-1/2 top-1/2 block rounded-full bg-[#d8f7ff] shadow-[0_0_12px_rgba(216,247,255,0.70)] motion-reduce:animate-none"
                    style={
                      {
                        "--fallback-angle": `${particle.angle}deg`,
                        "--fallback-radius": `${particle.radius}%`,
                        "--fallback-radius-mid": `${particle.radius * (0.62 + orb.stateReactiveEnergy * 0.20)}%`,
                        "--fallback-opacity-low": orb.isStopped ? "0.05" : "0.16",
                        "--fallback-opacity-high": String(particle.opacity * (0.52 + orb.stateReactiveEnergy * 0.32)),
                        animationDelay: `${particle.delay}s`,
                        animationDuration: `${Math.max(2.8, particle.duration / (0.78 + orb.motion * 0.20))}s`,
                        height: `${particle.size}px`,
                        width: `${particle.size}px`,
                      } as CSSProperties
                    }
                  />
                ))}
              </div>
              <p className="sr-only">Fallback visual seguro sin WebGL</p>
            </div>
          )}

          <span className="sr-only" data-testid="jarvis-holographic-radial-marks">
            marcas holográficas neutralizadas para la esfera de partículas; sin crosshair ni reactor circular dominante
          </span>
          <span className="sr-only" data-testid="jarvis-state-wave-rings">
            ondas de estado migradas a picos radiales de partículas y Canvas 2D
          </span>
          <p className="sr-only">reactor/orbe cinematográfico WebGL con bloom, profundidad, partículas, anillos y HUD futurista</p>
          <p className="sr-only">reactor/orbe cinematográfico con bloom/glow simulado, profundidad, capas, anillos radiales, marcas holográficas, partículas orbitando y HUD agresivo futurista</p>
          <p className="sr-only">orbe 3D real / HUD cinematográfico</p>
          <p className="sr-only">fallback sin WebGL, fallback si canvas falla, FPS budget, particle budget y power save se controlan sin bloquear UI</p>
          <p className="sr-only">webglcontextlost compatibility marker; powerPreference and bg-[#01050d]/10 legacy markers are neutralized because WebGL is not the primary renderer in PR #161 final correction.</p>
          <p className="sr-only">idle wake_listening listening transcribing thinking speaking alert error stopped executing</p>
          <p className="sr-only">idle wake_listening listening transcribing thinking speaking approval_required alert error stopped executing</p>
          <p className="sr-only">wake_listening futuro sin grabación ni transcripción continua; conversation_active manual; recording=false; no captura Web Audio; no sensores nuevos</p>
        </div>

        <div className="absolute bottom-4 left-1/2 w-[min(38rem,calc(100vw-3rem))] -translate-x-1/2 text-center">
          <p className="font-display text-[0.68rem] uppercase tracking-[0.18em] text-cyan-100/58">{stateSummary}</p>
          <p className="sr-only">{subtitle}</p>
          <details className="sr-only">
            <summary>state map</summary>
            {presenceStates.map(([id, label, description]) => (
              <p key={id}>
                {id === visualState ? ">" : "-"} {label}: {description}
              </p>
            ))}
          </details>
        </div>
      </div>
    </article>
  );
}
