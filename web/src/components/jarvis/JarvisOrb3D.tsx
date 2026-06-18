import { useEffect, useMemo, useRef, useState } from "react";
import { Mic, MicOff, ShieldAlert, Volume2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { jarvisToneProfiles, localVoiceStateLabels, presenceStates } from "./contracts";
import type { JarvisOrbVisualState, JarvisVoiceTone, LocalVoiceLoopState } from "./types";
import { localVoiceStateIsError } from "./utils";
import { useJarvisOrbState } from "@/hooks/jarvis/useJarvisOrbState";

interface JarvisOrb3DProps {
  voiceState: string;
  subtitle: string;
  localVoiceState: LocalVoiceLoopState;
  visualState: JarvisOrbVisualState;
  jarvisTone: JarvisVoiceTone;
  conversationActive: boolean;
  killSwitchState: string;
}

interface Particle {
  x: number;
  y: number;
  z: number;
  size: number;
  color: [number, number, number];
  seed: number;
  lane: number;
}

function seeded(index: number) {
  return Math.abs(Math.sin(index * 12.9898 + 78.233) * 43758.5453) % 1;
}

function makeParticles(): Float32Array {
  const particles: Particle[] = [];
  for (let index = 0; index < 920; index += 1) {
    const u = seeded(index) * 2 - 1;
    const theta = seeded(index + 1000) * Math.PI * 2;
    const radius = 0.46 + seeded(index + 2000) * 0.62;
    const ringBias = index % 7 === 0 ? 0.14 : 1;
    const xy = Math.sqrt(1 - u * u);
    particles.push({
      x: Math.cos(theta) * xy * radius,
      y: u * radius * ringBias,
      z: Math.sin(theta) * xy * radius,
      size: 1.9 + seeded(index + 3000) * 4.9,
      color: index % 17 === 0 ? [1.0, 0.72, 0.28] : index % 11 === 0 ? [0.82, 0.96, 1.0] : [0.36, 0.9, 1.0],
      seed: seeded(index + 4000),
      lane: index % 4,
    });
  }

  const ringCounts = [180, 220, 260, 300, 340];
  ringCounts.forEach((count, ringIndex) => {
    for (let index = 0; index < count; index += 1) {
      const theta = (index / count) * Math.PI * 2;
      const radius = 0.62 + ringIndex * 0.145;
      const wobble = Math.sin(theta * 6 + ringIndex) * 0.025;
      const axis = ringIndex % 3;
      const base = {
        x: Math.cos(theta) * radius,
        y: Math.sin(theta) * radius,
        z: wobble,
      };
      particles.push({
        x: axis === 0 ? base.x : axis === 1 ? base.x : base.z,
        y: axis === 0 ? base.y : axis === 1 ? base.z : base.x,
        z: axis === 0 ? base.z : axis === 1 ? base.y : base.y,
        size: ringIndex === 0 ? 3.8 : 2.8,
        color: ringIndex === 3 ? [0.88, 0.98, 1.0] : ringIndex === 4 ? [1.0, 0.78, 0.34] : [0.28, 0.86, 1.0],
        seed: seeded(index + ringIndex * 5000),
        lane: ringIndex,
      });
    }
  });

  const packed = new Float32Array(particles.length * 9);
  particles.forEach((particle, index) => {
    const offset = index * 9;
    packed[offset] = particle.x;
    packed[offset + 1] = particle.y;
    packed[offset + 2] = particle.z;
    packed[offset + 3] = particle.size;
    packed[offset + 4] = particle.color[0];
    packed[offset + 5] = particle.color[1];
    packed[offset + 6] = particle.color[2];
    packed[offset + 7] = particle.seed;
    packed[offset + 8] = particle.lane;
  });
  return packed;
}

function compileShader(gl: WebGLRenderingContext, type: number, source: string) {
  const shader = gl.createShader(type);
  if (!shader) return null;
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    gl.deleteShader(shader);
    return null;
  }
  return shader;
}

function createProgram(gl: WebGLRenderingContext) {
  const vertex = compileShader(
    gl,
    gl.VERTEX_SHADER,
    `
      attribute vec3 a_position;
      attribute float a_size;
      attribute vec3 a_color;
      attribute float a_seed;
      attribute float a_lane;
      uniform mat4 u_matrix;
      uniform float u_time;
      uniform float u_intensity;
      uniform float u_wave;
      uniform float u_glitch;
      uniform vec3 u_accent;
      varying vec3 v_color;
      varying float v_core;
      void main() {
        float laneSpeed = 0.18 + a_lane * 0.065;
        float spin = u_time * laneSpeed * (0.72 + a_seed * 0.55);
        float c = cos(spin);
        float s = sin(spin);
        vec3 p = a_position;
        if (mod(a_lane, 2.0) < 1.0) {
          p.xz = mat2(c, -s, s, c) * p.xz;
        } else {
          p.xy = mat2(c, -s, s, c) * p.xy;
        }
        float wave = sin(u_time * (1.35 + a_seed) + length(a_position) * 13.5 + a_seed * 12.0);
        float breath = 1.0 + wave * 0.035 * u_wave + sin(u_time * 0.65) * 0.018 * u_intensity;
        float glitch = (step(0.88, fract(sin(a_seed * 91.7 + u_time * 8.0) * 43758.5453)) - 0.5) * u_glitch * 0.085;
        p *= breath + glitch;
        p.z += sin(u_time * 0.9 + a_seed * 19.0) * 0.028 * u_wave;
        vec4 projected = u_matrix * vec4(p, 1.0);
        gl_Position = projected;
        gl_PointSize = a_size * (1.2 + u_intensity * 1.35 + u_wave * 0.38) * (1.0 + (1.0 - projected.z) * 0.26);
        v_color = mix(a_color, u_accent, 0.18 + u_wave * 0.12 + u_glitch * 0.18);
        v_core = smoothstep(1.15, 0.10, length(p));
      }
    `,
  );
  const fragment = compileShader(
    gl,
    gl.FRAGMENT_SHADER,
    `
      precision mediump float;
      varying vec3 v_color;
      varying float v_core;
      uniform float u_alpha;
      void main() {
        vec2 uv = gl_PointCoord - vec2(0.5);
        float d = length(uv);
        float glow = smoothstep(0.5, 0.0, d);
        float core = smoothstep(0.18, 0.0, d);
        vec3 color = v_color * (0.58 + core * 0.82 + v_core * 0.34);
        gl_FragColor = vec4(color, (glow * 0.72 + core * 0.30) * u_alpha);
      }
    `,
  );
  if (!vertex || !fragment) return null;
  const program = gl.createProgram();
  if (!program) return null;
  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    gl.deleteProgram(program);
    return null;
  }
  return program;
}

function perspective(aspect: number) {
  const fov = Math.PI / 3.2;
  const near = 0.1;
  const far = 10;
  const f = 1 / Math.tan(fov / 2);
  return new Float32Array([
    f / aspect,
    0,
    0,
    0,
    0,
    f,
    0,
    0,
    0,
    0,
    (far + near) / (near - far),
    -1,
    0,
    0,
    (2 * far * near) / (near - far),
    0,
  ]);
}

function multiply(left: Float32Array, right: Float32Array) {
  const out = new Float32Array(16);
  for (let row = 0; row < 4; row += 1) {
    for (let col = 0; col < 4; col += 1) {
      out[col * 4 + row] =
        left[0 * 4 + row] * right[col * 4 + 0] +
        left[1 * 4 + row] * right[col * 4 + 1] +
        left[2 * 4 + row] * right[col * 4 + 2] +
        left[3 * 4 + row] * right[col * 4 + 3];
    }
  }
  return out;
}

function modelMatrix(time: number, motion: number, pulse: number) {
  const y = time * 0.00023 * motion;
  const x = Math.sin(time * 0.00018) * 0.28;
  const cy = Math.cos(y);
  const sy = Math.sin(y);
  const cx = Math.cos(x);
  const sx = Math.sin(x);
  const scale = 1.0 + (pulse - 1) * 0.12;
  return new Float32Array([
    cy * scale,
    sx * sy * scale,
    -cx * sy * scale,
    0,
    0,
    cx * scale,
    sx * scale,
    0,
    sy * scale,
    -sx * cy * scale,
    cx * cy * scale,
    0,
    0,
    0,
    -2.45,
    1,
  ]);
}

function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace("#", "");
  const value = Number.parseInt(clean.length === 3 ? clean.split("").map((char) => char + char).join("") : clean, 16);
  if (Number.isNaN(value)) return [0.2, 0.85, 1.0];
  return [((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255];
}

export function JarvisOrb3D({
  voiceState,
  subtitle,
  localVoiceState,
  visualState,
  jarvisTone,
  conversationActive,
  killSwitchState,
}: JarvisOrb3DProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [webglReady, setWebglReady] = useState(true);
  const [webglError, setWebglError] = useState("");
  const particles = useMemo(() => makeParticles(), []);
  const hudTicks = useMemo(() => Array.from({ length: 72 }, (_, index) => index), []);
  const waveRings = useMemo(() => Array.from({ length: 6 }, (_, index) => index), []);
  const orb = useJarvisOrbState({ localVoiceState, visualState, jarvisTone, killSwitchState, conversationActive });
  const orbRef = useRef(orb);
  orbRef.current = orb;
  const profile = jarvisToneProfiles[jarvisTone];
  const StateIcon = killSwitchState === "active" ? ShieldAlert : localVoiceState === "speaking" ? Volume2 : localVoiceStateIsError(localVoiceState) ? MicOff : Mic;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const gl = canvas.getContext("webgl", {
      alpha: true,
      antialias: true,
      depth: true,
      premultipliedAlpha: true,
      powerPreference: "high-performance",
    });
    if (!gl) {
      setWebglReady(false);
      setWebglError("WebGL no disponible; usando fallback CSS seguro.");
      return;
    }
    setWebglReady(true);
    setWebglError("");
    const canvasEl = canvas;
    const webgl = gl;
    const program = createProgram(webgl);
    const buffer = webgl.createBuffer();
    if (!program || !buffer) {
      setWebglReady(false);
      setWebglError("No se pudo inicializar el shader del orbe; usando fallback CSS seguro.");
      return;
    }

    const position = webgl.getAttribLocation(program, "a_position");
    const size = webgl.getAttribLocation(program, "a_size");
    const color = webgl.getAttribLocation(program, "a_color");
    const seed = webgl.getAttribLocation(program, "a_seed");
    const lane = webgl.getAttribLocation(program, "a_lane");
    const matrix = webgl.getUniformLocation(program, "u_matrix");
    const timeUniform = webgl.getUniformLocation(program, "u_time");
    const intensity = webgl.getUniformLocation(program, "u_intensity");
    const wave = webgl.getUniformLocation(program, "u_wave");
    const glitch = webgl.getUniformLocation(program, "u_glitch");
    const accent = webgl.getUniformLocation(program, "u_accent");
    const alpha = webgl.getUniformLocation(program, "u_alpha");
    let animationId = 0;
    let lastDraw = 0;
    let contextLost = false;

    webgl.bindBuffer(webgl.ARRAY_BUFFER, buffer);
    webgl.bufferData(webgl.ARRAY_BUFFER, particles, webgl.STATIC_DRAW);

    const handleContextLost = (event: Event) => {
      event.preventDefault();
      contextLost = true;
      setWebglReady(false);
      setWebglError("WebGL se perdió; fallback visual seguro activo.");
    };
    canvasEl.addEventListener("webglcontextlost", handleContextLost, false);

    function resize() {
      const sizePx = Math.max(260, Math.floor(canvasEl.getBoundingClientRect().width));
      const currentOrb = orbRef.current;
      const pixelRatio = Math.min(window.devicePixelRatio || 1, currentOrb.isActive ? 1.75 : 1.35);
      const width = Math.floor(sizePx * pixelRatio);
      const height = Math.floor(sizePx * pixelRatio);
      if (canvasEl.width !== width || canvasEl.height !== height) {
        canvasEl.width = width;
        canvasEl.height = height;
      }
    }

    function draw(time: number) {
      if (contextLost) return;
      resize();
      const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
      const currentOrb = orbRef.current;
      const targetFrameMs = reducedMotion ? 120 : currentOrb.targetFrameMs;
      if (time - lastDraw < targetFrameMs) {
        animationId = window.requestAnimationFrame(draw);
        return;
      }
      lastDraw = time;
      try {
        webgl.viewport(0, 0, canvasEl.width, canvasEl.height);
        webgl.clearColor(0, 0, 0, 0);
        webgl.clear(webgl.COLOR_BUFFER_BIT | webgl.DEPTH_BUFFER_BIT);
        webgl.enable(webgl.BLEND);
        webgl.blendFunc(webgl.SRC_ALPHA, webgl.ONE);
        webgl.disable(webgl.CULL_FACE);
        webgl.useProgram(program);
        webgl.bindBuffer(webgl.ARRAY_BUFFER, buffer);
        const stride = 9 * Float32Array.BYTES_PER_ELEMENT;
        webgl.enableVertexAttribArray(position);
        webgl.vertexAttribPointer(position, 3, webgl.FLOAT, false, stride, 0);
        webgl.enableVertexAttribArray(size);
        webgl.vertexAttribPointer(size, 1, webgl.FLOAT, false, stride, 3 * Float32Array.BYTES_PER_ELEMENT);
        webgl.enableVertexAttribArray(color);
        webgl.vertexAttribPointer(color, 3, webgl.FLOAT, false, stride, 4 * Float32Array.BYTES_PER_ELEMENT);
        webgl.enableVertexAttribArray(seed);
        webgl.vertexAttribPointer(seed, 1, webgl.FLOAT, false, stride, 7 * Float32Array.BYTES_PER_ELEMENT);
        webgl.enableVertexAttribArray(lane);
        webgl.vertexAttribPointer(lane, 1, webgl.FLOAT, false, stride, 8 * Float32Array.BYTES_PER_ELEMENT);
        const aspect = canvasEl.width / Math.max(canvasEl.height, 1);
        const accentColor = hexToRgb(currentOrb.accent);
        webgl.uniformMatrix4fv(matrix, false, multiply(perspective(aspect), modelMatrix(time, currentOrb.motion, currentOrb.pulse)));
        webgl.uniform1f(timeUniform, time * 0.001);
        webgl.uniform1f(intensity, currentOrb.pulse);
        webgl.uniform1f(wave, reducedMotion ? currentOrb.wave * 0.35 : currentOrb.wave);
        webgl.uniform1f(glitch, reducedMotion ? 0 : currentOrb.glitch);
        webgl.uniform3f(accent, accentColor[0], accentColor[1], accentColor[2]);
        webgl.uniform1f(alpha, currentOrb.isError ? 0.88 : currentOrb.isStopped ? 0.42 : 0.76);
        const maxParticles = Math.min(particles.length / 9, reducedMotion ? 520 : currentOrb.particleBudget);
        webgl.drawArrays(webgl.POINTS, 0, maxParticles);
      } catch {
        setWebglReady(false);
        setWebglError("Canvas WebGL falló durante el render; fallback visual seguro activo.");
        return;
      }
      animationId = window.requestAnimationFrame(draw);
    }

    animationId = window.requestAnimationFrame(draw);
    return () => {
      window.cancelAnimationFrame(animationId);
      canvasEl.removeEventListener("webglcontextlost", handleContextLost, false);
      webgl.deleteBuffer(buffer);
      webgl.deleteProgram(program);
    };
  }, [particles]);

  return (
    <article
      className="relative h-full min-h-0 overflow-hidden"
      data-testid="jarvis-central-core"
      data-local-voice-state={localVoiceState}
      data-orb-visual-state={visualState}
      data-jarvis-tone={jarvisTone}
      data-conversation-active={conversationActive ? "true" : "false"}
      data-kill-switch-state={killSwitchState}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,rgba(34,211,238,0.22)_0%,rgba(14,165,233,0.08)_35%,rgba(2,6,23,0)_68%),radial-gradient(circle_at_50%_82%,rgba(249,115,22,0.10),transparent_38%),linear-gradient(90deg,rgba(34,211,238,0.035)_1px,transparent_1px),linear-gradient(0deg,rgba(125,211,252,0.028)_1px,transparent_1px)] bg-[length:100%_100%,100%_100%,64px_64px,64px_64px]" />
      <div className="absolute left-0 right-0 top-1/2 h-px bg-cyan-300/35 shadow-[0_0_30px_rgba(34,211,238,0.55)]" />
      <div className="absolute left-1/2 top-[8%] h-[84%] w-px -translate-x-1/2 bg-cyan-300/18" />
      <div className="relative flex h-full min-h-0 flex-col items-center justify-center">
        <div className="absolute top-4 flex flex-wrap items-center justify-center gap-2 px-4">
          <Badge className="border-cyan-300/35 bg-cyan-300/10 text-cyan-100" variant="outline">Presence UI</Badge>
          <Badge className="border-cyan-100/20 bg-[#071629]/75 text-cyan-50" variant="outline">Núcleo de Voz JARVIS</Badge>
          <Badge className="border-cyan-300/35 bg-cyan-300/10 text-cyan-100" variant="outline">orbe 3D real / HUD cinematográfico</Badge>
          <Badge className="border-cyan-300/35 bg-cyan-300/10 text-cyan-100" variant="outline">tono {profile.label}</Badge>
          <Badge className="border-cyan-300/35 bg-cyan-300/10 text-cyan-100" variant="outline">estado {visualState}</Badge>
        </div>

        <div className="relative flex aspect-square w-[min(84dvh,62rem)] max-h-[calc(100dvh-12rem)] max-w-[min(92vw,62rem)] items-center justify-center xl:max-w-[min(66vw,62rem)]" data-testid="jarvis-cinematic-orb-hud">
          <div className="absolute inset-[-10%] rounded-full blur-3xl" style={{ backgroundColor: orb.glow }} />
          <div className="absolute inset-[-6%] rounded-full border border-cyan-200/8 shadow-[0_0_240px_rgba(34,211,238,0.34),inset_0_0_110px_rgba(14,165,233,0.10)]" />
          <div className="absolute inset-0 rounded-full border border-cyan-200/12 bg-[radial-gradient(circle_at_48%_38%,rgba(125,211,252,0.16),transparent_22%),radial-gradient(circle_at_52%_58%,rgba(14,165,233,0.12),transparent_42%)] shadow-[0_0_210px_rgba(34,211,238,0.30)]" />
          <div className="absolute inset-[4%] rounded-full border border-cyan-100/20 bg-[conic-gradient(from_0deg,transparent_0deg,rgba(125,211,252,0.34)_18deg,transparent_42deg,transparent_84deg,rgba(34,211,238,0.18)_112deg,transparent_138deg,transparent_360deg)] opacity-85 animate-spin" style={{ animationDuration: `${24 / orb.motion}s` }} />
          <div className="absolute inset-[11%] rounded-full border border-cyan-100/16 bg-[conic-gradient(from_90deg,transparent_0deg,rgba(56,189,248,0.28)_12deg,transparent_28deg,transparent_152deg,rgba(125,211,252,0.22)_166deg,transparent_188deg,transparent_360deg)] opacity-70 animate-spin" style={{ animationDuration: `${31 / orb.motion}s`, animationDirection: "reverse" }} />
          <div className="absolute inset-[20%] rounded-full border border-cyan-100/30 shadow-[0_0_120px_rgba(34,211,238,0.30),inset_0_0_92px_rgba(34,211,238,0.14)]" />
          <div className="absolute inset-[28%] rounded-full border border-sky-200/18 opacity-75 shadow-[inset_0_0_50px_rgba(125,211,252,0.12)]" />
          <div className="absolute inset-[2%] rounded-full" data-testid="jarvis-holographic-radial-marks">
            {hudTicks.map((tick) => (
              <span
                key={tick}
                className={
                  "absolute left-1/2 top-1/2 block border-cyan-200/55 bg-cyan-100/65 shadow-[0_0_14px_rgba(125,211,252,0.55)] " +
                  (tick % 6 === 0 ? "h-5 w-px" : tick % 3 === 0 ? "h-3 w-px opacity-80" : "h-2 w-px opacity-45")
                }
                style={{ transform: `translate(-50%, -50%) rotate(${tick * 5}deg) translateY(calc(-1 * min(39dvh, 28rem)))` }}
              />
            ))}
          </div>
          <div className="absolute inset-[14%] rounded-full pointer-events-none" data-testid="jarvis-state-wave-rings">
            {waveRings.map((ring) => (
              <span
                key={ring}
                className="absolute inset-0 rounded-full border border-cyan-200/20"
                style={{
                  animation: `jarvis-orb-wave ${Math.max(1.8, 5.8 - orb.wave * 1.8)}s ease-out ${ring * 0.34}s infinite`,
                  opacity: orb.isStopped ? 0.12 : 0.24 + orb.wave * 0.08,
                  transform: `scale(${0.58 + ring * 0.075})`,
                }}
              />
            ))}
          </div>
          <canvas
            ref={canvasRef}
            aria-label="reactor/orbe cinematográfico WebGL con bloom, profundidad, partículas, anillos y HUD futurista"
            className="absolute inset-[2%] h-[96%] w-[96%] rounded-full opacity-95 [filter:drop-shadow(0_0_40px_rgba(34,211,238,0.78))]"
          />
          {!webglReady && (
            <div className="absolute inset-[8%] rounded-full border border-cyan-300/35 bg-[radial-gradient(circle_at_50%_50%,rgba(34,211,238,0.36),rgba(14,165,233,0.10)_42%,transparent_68%)] shadow-[0_0_140px_rgba(34,211,238,0.46)]" data-testid="jarvis-orb-webgl-fallback">
              <div className="absolute inset-[8%] rounded-full border border-cyan-100/30 animate-spin" />
              <div className="absolute inset-[18%] rounded-full border border-sky-300/24 animate-ping" />
              <div className="absolute inset-[32%] grid place-items-center rounded-full border border-cyan-200/30 bg-[#03192a]/84 text-center">
                <p className="px-4 font-display text-xs uppercase tracking-[0.18em] text-cyan-50">Fallback visual seguro sin WebGL</p>
                <p className="mt-2 px-6 font-mono-ui text-[0.68rem] text-cyan-100/58">{webglError || "Canvas no disponible; no se activan sensores."}</p>
              </div>
            </div>
          )}
          <div className="absolute h-px w-[122%] bg-cyan-300/38 shadow-[0_0_32px_rgba(34,211,238,0.86)]" />
          <div className="absolute h-[122%] w-px bg-cyan-300/24" />
          <div className="relative flex h-[34%] min-h-44 w-[34%] min-w-44 items-center justify-center rounded-full border border-cyan-100/65 bg-[#03192a]/88 shadow-[0_0_130px_rgba(34,211,238,0.56),inset_0_0_90px_rgba(34,211,238,0.23)]">
            <div className="absolute inset-[-14%] rounded-full blur-2xl" style={{ backgroundColor: orb.glow }} />
            <div className="absolute inset-3 rounded-full border border-cyan-300/30 bg-[conic-gradient(from_0deg,rgba(34,211,238,0.18),transparent_22%,rgba(125,211,252,0.24),transparent_58%,rgba(34,211,238,0.20),transparent_100%)] animate-spin" style={{ animationDuration: `${12 / orb.motion}s` }} />
            <div className="relative text-center">
              <h1 className="font-expanded text-[clamp(2.1rem,4.2vw,5.4rem)] font-bold uppercase tracking-[0.14em] text-cyan-50 blend-lighter drop-shadow-[0_0_28px_rgba(125,211,252,0.9)]">
                JARVIS
              </h1>
              <p className="mt-1 font-display text-[0.62rem] uppercase tracking-[0.28em] text-cyan-100/72">
                reactor de presencia
              </p>
              <StateIcon className="mx-auto mt-4 h-8 w-8 text-cyan-100/80 drop-shadow-[0_0_18px_rgba(125,211,252,0.9)]" />
            </div>
          </div>
        </div>

        <div className="absolute bottom-4 left-1/2 flex w-[min(52rem,calc(100vw-3rem))] -translate-x-1/2 flex-wrap justify-center gap-2">
          {presenceStates.map(([id, label, description]) => (
            <div
              key={id}
              className={
                "border px-3 py-1.5 shadow-[0_0_24px_rgba(34,211,238,0.08)] backdrop-blur " +
                (id === visualState || (id === "error" && localVoiceStateIsError(localVoiceState))
                  ? "border-cyan-200/70 bg-cyan-300/18 text-cyan-50 shadow-[0_0_34px_rgba(34,211,238,0.24)]"
                  : "border-cyan-300/18 bg-[#031426]/70 text-cyan-100")
              }
              title={description}
            >
              <p className="font-display text-[0.68rem] uppercase tracking-[0.14em]">{label}</p>
            </div>
          ))}
        </div>

        <div className="absolute bottom-[4.25rem] left-1/2 w-[min(42rem,calc(100vw-4rem))] -translate-x-1/2 text-center">
          <p className="font-display text-sm uppercase tracking-[0.22em] text-cyan-200">
            {voiceState} / visual {visualState} / {localVoiceStateLabels[localVoiceState]} / {profile.label}
          </p>
          <p className="mt-2 line-clamp-2 font-mono-ui text-sm text-cyan-50/78">{subtitle}</p>
          <p className="sr-only">reactor/orbe cinematográfico con bloom/glow simulado, profundidad, capas, anillos radiales, marcas holográficas, partículas orbitando y HUD agresivo futurista</p>
          <p className="sr-only">fallback sin WebGL, fallback si canvas falla, FPS budget, particle budget y power save se controlan sin bloquear UI</p>
          <p className="sr-only">idle wake_listening listening transcribing thinking speaking alert error stopped executing</p>
          <p className="sr-only">wake_listening futuro sin grabación ni transcripción continua; conversation_active manual; recording=false; no captura Web Audio; no sensores nuevos</p>
        </div>
      </div>
    </article>
  );
}
