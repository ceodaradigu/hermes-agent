import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "web/src/pages/JarvisCommandCenterPage.tsx"
PACKAGE = ROOT / "web/package.json"
INDEX_CSS = ROOT / "web/src/index.css"
JARVIS_COMPONENT_DIR = ROOT / "web/src/components/jarvis"
JARVIS_HOOK_DIR = ROOT / "web/src/hooks/jarvis"
PR_DOC = ROOT / "docs/jarvis-pr-162-particle-sphere-motion-polish-visual-qa.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _jarvis_ui_sources() -> str:
    paths = [PAGE, INDEX_CSS]
    paths.extend(sorted(JARVIS_COMPONENT_DIR.glob("*.ts")))
    paths.extend(sorted(JARVIS_COMPONENT_DIR.glob("*.tsx")))
    paths.extend(sorted(JARVIS_HOOK_DIR.glob("*.ts")))
    return "\n".join(_read(path) for path in paths)


def _qa_controls_section() -> str:
    drawer = _read(JARVIS_COMPONENT_DIR / "JarvisDebugDrawer.tsx")
    start = drawer.index('data-testid="jarvis-visual-qa-preview-controls"')
    end = drawer.index('data-testid="jarvis-hermes-timeline-summary"')
    return drawer[start:end]


def test_pr_162_particle_sphere_is_the_main_center_visual_without_logo_or_fixed_core():
    orb = _read(JARVIS_COMPONENT_DIR / "JarvisOrb3D.tsx")

    for marker in (
        'data-testid="jarvis-particle-sphere-presence"',
        'data-testid="jarvis-particle-sphere-canvas"',
        'data-particle-cloud-mode="living-volumetric-canvas-2d-primary"',
        "alive volumetric particle cloud with air gaps",
        "cold-white/ice-blue particles",
        "no solid mass",
        "data-center-emergence=\"idle-nearly-none compression-only dissolves-on-expansion\"",
        'data-no-fixed-central-logo="true"',
        'data-no-solid-core="true"',
        'data-no-central-jarvis-text="true"',
        'data-testid="jarvis-emergent-core-density"',
        'data-no-permanent-nucleus="true"',
        'data-idle-core-opacity="near-zero"',
        "Array.from({ length: 2600 }",
        'data-volumetric-particle-count="2600"',
        "shellBias",
        "innerDust",
    ):
        assert marker in orb

    for forbidden in (
        ">JARVIS</",
        "jarvis-distinct-core",
        "layered-inner-ring-not-flat-white",
        "grid place-items-center rounded-full",
        "data-core-detail=\"layered-inner-ring",
        "reactor de presencia",
    ):
        assert forbidden not in orb


def test_pr_162_states_have_distinct_motion_energy_center_and_size_contracts():
    orb = _read(JARVIS_COMPONENT_DIR / "JarvisOrb3D.tsx")
    state_hook = _read(JARVIS_HOOK_DIR / "useJarvisOrbState.ts")
    contracts = _read(JARVIS_COMPONENT_DIR / "contracts.ts")

    for state in ("idle", "listening", "transcribing", "thinking", "speaking", "alert", "error", "stopped"):
        assert state in contracts
        assert state in state_hook or state in orb

    for marker in (
        "isSpeaking ? 1.48",
        "isError ? 1.56",
        "isAlert ? 1.42",
        'visualState === "listening" ? 0.62',
        "isStopped ? 0.48",
        ": 0.008;",
        "radialSpikeEnergy = isStopped ? 0 : isError ? 1.22 : isAlert ? 1.08 : isSpeaking ? 1",
        "thinkingTurbulence = isStopped ? 0 : isThinking ? 1",
        'listeningFocus = isStopped ? 0 : visualState === "listening" ? 1',
        "transcribingReflow = isStopped ? 0 : isTranscribing ? 1 : 0",
        "particleBudget: isStopped ? 760 : isSpeaking ? 2600",
        "isThinking ? 2460",
        'visualState === "listening" ? 2240',
        "isThinking ? 0.80",
        'visualState === "listening" ? 0.62',
        ": 0.055;",
        "spherePressure = isStopped ? 0.05",
        ": 0.025;",
        "visualState === \"listening\" ? 0.62",
        ": 0.985;",
        ": 1.00;",
        ": 1.018;",
        ": 10.5;",
        ": 1500,",
    ):
        assert marker in state_hook

    for marker in (
        "pseudoAudio",
        "breathingCycle",
        "angularWave",
        "outwardWave",
        "spikeMask",
        "swirl",
        "const laneSpeed = (0.030",
        'data-speaking-motion="pseudo-audio-deterministic-radial-push-spikes-outward-waves"',
        'data-thinking-motion-signature="curl-swirl-internal-redistribution-not-speaking-spikes"',
        'data-listening-motion-signature="contracted-tense-fine-pulse-smaller-sphere"',
        "data-dynamic-sphere-size=",
    ):
        assert marker in orb


def test_pr_162_idle_is_the_calmest_motion_state():
    state_hook = _read(JARVIS_HOOK_DIR / "useJarvisOrbState.ts")

    for marker in (
        "baseReactiveEnergy =",
        ": 0.055;",
        'visualState === "listening" ? 0.62',
        "isThinking ? 0.80",
        "isSpeaking ? 1",
        "radialSpikeEnergy = isStopped ? 0 : isError ? 1.22 : isAlert ? 1.08 : isSpeaking ? 1 : textReactiveActive ? 0.46 : 0",
        "thinkingTurbulence = isStopped ? 0 : isThinking ? 1 : isTranscribing ? 0.18 : 0",
        "spherePressure = isStopped ? 0.05",
        ": 0.025;",
        ": 0.008;",
        "sphereAnimationSeconds =",
        ": 10.5;",
        "particleBudget: isStopped ? 760 : isSpeaking ? 2600",
        ": 1500,",
    ):
        assert marker in state_hook

    assert state_hook.index(": 0.055;") > state_hook.index('visualState === "listening" ? 0.62')
    assert state_hook.index(": 0.055;") > state_hook.index("isThinking ? 0.80")
    assert state_hook.index("isSpeaking ? 1") < state_hook.index("isThinking ? 0.80")


def test_pr_162_visual_qa_preview_is_local_safe_and_state_complete():
    source = _jarvis_ui_sources()
    shell = _read(JARVIS_COMPONENT_DIR / "JarvisPresenceShell.tsx")
    qa = _qa_controls_section()

    for marker in (
        "visualQaPreviewStates",
        "jarvisVisualPreview",
        "readInitialVisualQaPreviewState",
        "resolvedOrbVisualState = visualQaPreviewState ?? orbVisualState",
        'data-visual-qa-preview-mode={visualQaPreviewState ? "forced-local-preview" : "auto"}',
        'data-testid="jarvis-visual-qa-preview-controls"',
        'data-visual-qa-preview="local-front-end-only"',
        'data-visual-qa-no-hermes="true"',
        'data-visual-qa-no-sensors="true"',
        'data-visual-qa-no-direct-approval="true"',
        'data-visual-qa-no-backend-execution="true"',
        'data-visual-qa-query-param="jarvisVisualPreview"',
        "onVisualPreviewStateChange(null)",
        "onVisualPreviewStateChange(state)",
    ):
        assert marker in source

    for state in ("idle", "listening", "transcribing", "thinking", "speaking", "alert", "stopped"):
        assert f'["{state}",' in source

    for forbidden in (
        "fetch(",
        "api.",
        "beginLocalVoiceLoop",
        "startCameraPreview",
        "startRecording",
        "startVideoRecording",
        "navigator.mediaDevices",
        "getUserMedia",
        "MediaRecorder",
        "AudioContext",
        "HermesRuntimeAdapter",
        "AIAgent",
        "ApprovalGateway",
    ):
        assert forbidden not in qa

    assert "setVisualQaPreviewState" in shell


def test_pr_162_fallback_reduced_motion_and_runtime_boundaries_remain_intact():
    orb = _read(JARVIS_COMPONENT_DIR / "JarvisOrb3D.tsx")
    source = "\n".join(
        _read(path)
        for path in (
            PAGE,
            JARVIS_COMPONENT_DIR / "JarvisPresenceShell.tsx",
            JARVIS_COMPONENT_DIR / "JarvisOrb3D.tsx",
            JARVIS_COMPONENT_DIR / "JarvisDebugDrawer.tsx",
            JARVIS_COMPONENT_DIR / "JarvisSmartBar.tsx",
            JARVIS_COMPONENT_DIR / "contracts.ts",
        )
    )

    for marker in (
        'data-testid="jarvis-orb-webgl-fallback"',
        'data-webgl-fallback="css-particle-sphere-fallback"',
        'data-testid="jarvis-css-particle-sphere-fallback"',
        'data-fallback-contract="css-particle-sphere-no-visible-technical-message"',
        'data-canvas-error={canvasError}',
        'className="sr-only">Fallback visual seguro sin WebGL</p>',
        "prefers-reduced-motion",
        "motion-reduce:animate-none",
        "targetFrameMs",
        "particleBudget",
    ):
        assert marker in orb

    for forbidden in (
        "círculo negro",
        "black circle",
        'text-cyan-50">Fallback visual seguro sin WebGL</p>',
        'text-[#e6fbff]">Fallback visual seguro sin WebGL</p>',
        '"/execute"',
        "'/execute'",
        "`/execute`",
        "fetch('/execute",
        'fetch("/execute',
        "HermesRuntimeAdapter",
        "AIAgent",
    ):
        assert forbidden not in source

    camera = _read(JARVIS_HOOK_DIR / "useJarvisCameraControl.ts")
    recorder = _read(JARVIS_HOOK_DIR / "useJarvisAudioRecorder.ts")
    for hook_source in (camera, recorder):
        for block in re.findall(r"useEffect\(\(\) => \{.*?\n  \}, \[[^\]]*\]\);", hook_source, flags=re.S):
            assert ".getUserMedia(" not in block
            assert ".start()" not in block


def test_pr_162_no_new_visual_dependencies_or_forbidden_sensor_runtime_packages():
    package = json.loads(_read(PACKAGE))
    all_deps = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))

    assert all_deps.isdisjoint(
        {
            "three",
            "@react-three/fiber",
            "@react-three/drei",
            "@react-three/postprocessing",
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
    )


def test_pr_162_credentials_phrase_and_documentation_contract_are_present():
    smart_bar = _read(JARVIS_COMPONENT_DIR / "JarvisSmartBar.tsx")

    assert "No puedo hacer eso, David. Las credenciales y secretos están protegidos." in smart_bar
    assert PR_DOC.exists()
    doc = _read(PR_DOC)

    for marker in (
        "PR #162",
        "Fase 1",
        "JARVIS gobierna. Hermes ejecuta.",
        "idle",
        "listening",
        "thinking",
        "speaking",
        "alert",
        "stopped",
        "jarvisVisualPreview",
        "Visual QA",
        "No se copio codigo externo",
        "Ninguna dependencia nueva",
        "No se implemento",
        "Riesgos pendientes",
        "Siguiente PR recomendada",
    ):
        assert marker in doc
