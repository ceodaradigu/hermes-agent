import json
import re
from pathlib import Path

import pytest

from jarvis.api.app import create_app


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "web/src/pages/JarvisCommandCenterPage.tsx"
APP = ROOT / "web/src/App.tsx"
PACKAGE = ROOT / "web/package.json"
INDEX_CSS = ROOT / "web/src/index.css"
JARVIS_COMPONENT_DIR = ROOT / "web/src/components/jarvis"
JARVIS_HOOK_DIR = ROOT / "web/src/hooks/jarvis"
PR_DOC = ROOT / "docs/jarvis-pr-161-presence-ui-visual-overhaul-v2-audio-reactive-orb.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontend_sources() -> str:
    paths = [PAGE, APP, INDEX_CSS]
    paths.extend(sorted(JARVIS_COMPONENT_DIR.glob("*.ts")))
    paths.extend(sorted(JARVIS_COMPONENT_DIR.glob("*.tsx")))
    paths.extend(sorted(JARVIS_HOOK_DIR.glob("*.ts")))
    return "\n".join(_read(path) for path in paths)


def test_pr_161_jarvis_route_stays_read_only_and_has_no_dangerous_surface():
    source = _frontend_sources()
    routes = {
        (route.path, method)
        for route in create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called")).routes
        for method in getattr(route, "methods", set())
    }

    for fragment in (
        '"/execute"',
        "'/execute'",
        "`/execute`",
        "fetch('/execute",
        'fetch("/execute',
        "method: 'POST'",
        'method: "POST"',
        "method: 'PUT'",
        'method: "PUT"',
        "method: 'DELETE'",
        'method: "DELETE"',
        "callHermes",
        "dispatchHermes",
        "HermesRuntimeAdapter",
        "AIAgent",
    ):
        assert fragment not in source

    for route in (
        ("/jarvis/execute", "POST"),
        ("/jarvis/approve", "POST"),
        ("/jarvis/reject", "POST"),
        ("/jarvis/hermes/execute", "POST"),
    ):
        assert route not in routes


def test_pr_161_camera_microphone_and_wake_phrase_remain_opt_in_and_non_executing():
    page = _read(PAGE)
    shell = _read(JARVIS_COMPONENT_DIR / "JarvisPresenceShell.tsx")
    smart_bar = _read(JARVIS_COMPONENT_DIR / "JarvisSmartBar.tsx")
    utils = _read(JARVIS_COMPONENT_DIR / "utils.ts")
    local_voice = _read(JARVIS_HOOK_DIR / "useLocalVoiceLoop.ts")
    camera = _read(JARVIS_HOOK_DIR / "useJarvisCameraControl.ts")
    recorder = _read(JARVIS_HOOK_DIR / "useJarvisAudioRecorder.ts")

    assert "getUserMedia" not in local_voice
    assert "beginLocalVoiceLoop()" not in page
    assert "startCameraPreview()" not in page
    assert "startRecording()" not in page
    assert "startVideoRecording()" not in page
    assert "onBegin={localVoice.beginLocalVoiceLoop}" in shell
    assert "onStart={cameraControl.startCameraPreview}" in shell
    assert "onStart={audioRecorder.startRecording}" in shell

    for source in (camera, recorder):
        for block in re.findall(r"useEffect\(\(\) => \{.*?\n  \}, \[[^\]]*\]\);", source, flags=re.S):
            assert ".getUserMedia(" not in block
            assert ".start()" not in block

    assert "Wake phrase cannot approve and cannot execute." in utils
    assert "wake no aprueba" in smart_bar
    assert "wake no ejecuta" in smart_bar


def test_pr_161_orb_is_reliable_canvas_particle_sphere_with_emergent_core_and_reactivity():
    source = _frontend_sources()
    orb = _read(JARVIS_COMPONENT_DIR / "JarvisOrb3D.tsx")
    contracts = _read(JARVIS_COMPONENT_DIR / "contracts.ts")
    state_hook = _read(JARVIS_HOOK_DIR / "useJarvisOrbState.ts")

    for marker in (
        "data-renderer=\"canvas-2d-particle-sphere-primary\"",
        "data-no-webgl-primary=\"true\"",
        "data-testid=\"jarvis-particle-sphere-canvas\"",
        "data-renderer=\"canvas-2d-particle-sphere\"",
        "data-no-shader-required=\"true\"",
        "canvas.getContext(\"2d\"",
        "function makeCanvasParticles()",
        "Array.from({ length: 2600 }",
        "data-minimum-visible-particles=\"1420\"",
        "data-fallback-particle-budget=\"360\"",
        "data-visible-particles=\"canvas-2d-plus-css-micro-particles\"",
        "data-particle-sphere-mode=\"visible-canvas-2d-primary\"",
        "data-sphere-contract=\"particle sphere / sphere of particles / nube viva de particulas / volumetric living cloud\"",
        "data-emergent-core=\"density-only-no-permanent-nucleus\"",
        "data-core-detail=\"emergent-particle-concentration-not-fixed-solid\"",
        "data-core-layers=\"particle-convergence transient-white-blue-density no-fixed-logo no-solid-core\"",
        "data-no-fixed-central-logo=\"true\"",
        "data-no-solid-core=\"true\"",
        "data-no-central-jarvis-text=\"true\"",
        "data-testid=\"jarvis-micro-particle-field\"",
        "data-testid=\"jarvis-emergent-core-density\"",
        "data-core-contract=\"emergent center appears only through particle concentration\"",
        "data-testid=\"jarvis-speaking-radial-spikes\"",
        "data-speaking-spikes=\"radial-spikes-and-outward-waves\"",
        "data-spike-contract=\"speaking-and-alert-create-radial-spikes-and-waves\"",
        "data-thinking-motion=\"internal-turbulence-and-swirl\"",
        "data-listening-motion=\"focused-contraction-and-attention-pulse\"",
        "data-dynamic-sphere-size=",
        "stateReactiveEnergy",
        "speakingSpikeEnergy",
        "radialSpikeEnergy",
        "thinkingTurbulence",
        "listeningFocus",
        "transcribingReflow",
        "spherePressure",
        "emergentCoreConcentration",
        "sphereScaleMin",
        "sphereScaleMid",
        "sphereScaleMax",
        "sphereAnimationSeconds",
        "textReactiveActive",
        "jarvis-micro-orbit",
        "jarvis-micro-particle",
        "jarvis-particle-sphere-stage",
        "jarvis-sphere-size-breathe",
        "jarvis-emergent-core",
        "jarvis-emergent-core-particle",
        "jarvis-speaking-spike",
        "jarvis-fallback-particle",
        "data-webgl-fallback=\"css-particle-sphere-fallback\"",
        "data-testid=\"jarvis-css-particle-sphere-fallback\"",
        "data-fallback-contract=\"css-particle-sphere-no-visible-technical-message\"",
        "className=\"sr-only\">Fallback visual seguro sin WebGL</p>",
        "onDraftActivity={handleSmartBarDraftActivity}",
        "jarvisPresenceVisualLayers",
        "dark-background-distinct-blue-white-core-clean-side-rails",
    ):
        assert marker in source

    for marker in (
        "particleBudget: isStopped ? 760 : isSpeaking ? 2600",
        "isThinking ? 2460",
        'visualState === "listening" ? 2240',
        "isTranscribing ? 2300",
        "textReactiveActive ? 2200",
        "speakingSpikeEnergy = isStopped ? 0 : isSpeaking ? 1",
        "radialSpikeEnergy = isStopped ? 0 : isError ? 1.22 : isAlert ? 1.08",
        "thinkingTurbulence = isStopped ? 0 : isThinking ? 1",
        'listeningFocus = isStopped ? 0 : visualState === "listening" ? 1',
        "emergentCoreConcentration = isStopped",
        ": 0.008;",
        "sphereScaleMin",
        "sphereScaleMax",
        "isError ? 1.56 : isAlert ? 1.42",
        "isSpeaking ? 1.48",
        "pseudoAudio",
        "currentOrb.radialSpikeEnergy",
        "currentOrb.thinkingTurbulence",
        "currentOrb.listeningFocus",
    ):
        assert marker in state_hook or marker in orb

    for removed_marker in (
        "getContext(\"webgl\"",
        "getContext(\"experimental-webgl\"",
        "compileShader(",
        "createProgram(",
        "shaderSource",
        "gl_Point",
        "<h1",
        ">JARVIS</h1>",
        "reactor de presencia",
        "font-expanded text-[clamp(1.35rem,2.25vw,3.2rem)]",
        "data-core-detail=\"layered-inner-ring-not-flat-white\"",
        "outer-sheen inner-ring dark-reading-plate white-blue-core",
        "grid place-items-center rounded-full",
        "text-[#e6fbff]\">Fallback visual seguro sin WebGL</p>",
        "absolute left-0 right-0 top-1/2 h-px",
        "top-[10%] h-[80%] w-px",
        "absolute h-px w-[104%]",
        "absolute h-[104%] w-px",
    ):
        assert removed_marker not in orb

    for state in (
        "idle",
        "wake_listening",
        "listening",
        "transcribing",
        "thinking",
        "speaking",
        "approval_required",
        "alert",
        "error",
        "stopped",
        "executing",
    ):
        assert state in orb
        assert state in contracts

    for marker in (
        'data-testid="jarvis-orb-webgl-fallback"',
        'data-webgl-fallback="css-particle-sphere-fallback"',
        'data-legacy-webgl-fallback="css-core-fallback"',
        "webglcontextlost",
        "prefers-reduced-motion",
        "motion-reduce:animate-none",
        "targetFrameMs",
        "particleBudget",
        "pixelRatio",
        "maxParticles",
    ):
        assert marker in orb or marker in state_hook

    assert 'className="sr-only">Fallback visual seguro sin WebGL</p>' in orb
    assert 'text-cyan-50">Fallback visual seguro sin WebGL</p>' not in orb

    assert "#00030a" in contracts
    assert "#0ea5e9" in contracts
    assert "#67e8f9" in contracts
    assert "#e6fbff" in contracts


def test_pr_161_smart_bar_human_first_and_panels_are_folded_premium_not_dashboard():
    source = _frontend_sources()
    smart_bar = _read(JARVIS_COMPONENT_DIR / "JarvisSmartBar.tsx")

    for marker in (
        'data-smart-bar-contract="human-response-visible-details-folded-send-disabled"',
        "respuesta humana corta",
        "transcripción temporal local",
        "details",
        "summary",
        "intent_detected",
        "risk_level",
        "requires_approval",
        "cannot_execute_reason",
        "suggested_next_action",
        "borrador local",
        "No puedo hacer eso, David. Las credenciales y secretos están protegidos.",
    ):
        assert marker in smart_bar

    for marker in (
        'data-panel-style="premium-minimal-presence"',
        'data-panel-style="contract-folded-premium"',
        'data-panel-style="compact-governed-approval-not-dashboard"',
        'data-side-panel-style="premium-quiet-not-dashboard"',
        'data-panel-style="premium-camera-opt-in-no-upload"',
        'data-panel-style="folded-raw-audio-local-only"',
    ):
        assert marker in source


def test_pr_161_visual_dependencies_and_documentation_contract_are_intentional():
    package = json.loads(_read(PACKAGE))
    deps = package.get("dependencies", {})
    dev_deps = package.get("devDependencies", {})
    all_deps = set(deps) | set(dev_deps)
    allowed_3d = {"three", "@react-three/fiber", "@react-three/drei", "@react-three/postprocessing"}
    forbidden_sensor_or_runtime = {
        "@mediapipe/tasks-vision",
        "@tensorflow/tfjs",
        "media-pipe",
        "tone",
        "react-ai-voice-visualizer",
        "edge-tts",
        "openai",
        "@google/generative-ai",
        "stripe",
    }

    assert all_deps.isdisjoint(forbidden_sensor_or_runtime)
    assert (all_deps & allowed_3d) == set()
    assert PR_DOC.exists()

    doc = _read(PR_DOC)
    for marker in (
        "PR #161",
        "fondo mucho mas oscuro",
        "nucleo azul-blanco",
        "Audio-reactive / voice-reactive",
        "No se copio codigo externo",
        "Ninguna dependencia nueva",
        "JARVIS gobierna. Hermes ejecuta.",
    ):
        assert marker in doc
