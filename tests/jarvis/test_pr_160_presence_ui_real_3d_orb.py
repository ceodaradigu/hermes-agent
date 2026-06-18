import json
import re
from pathlib import Path

import pytest

from jarvis.api.app import create_app


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "web/src/pages/JarvisCommandCenterPage.tsx"
APP = ROOT / "web/src/App.tsx"
PACKAGE = ROOT / "web/package.json"
JARVIS_COMPONENT_DIR = ROOT / "web/src/components/jarvis"
JARVIS_HOOK_DIR = ROOT / "web/src/hooks/jarvis"
PR_DOC = ROOT / "docs/jarvis-pr-160-presence-ui-real-3d-orb-hud-adoption.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontend_sources() -> str:
    paths = [PAGE, APP]
    paths.extend(sorted(JARVIS_COMPONENT_DIR.glob("*.ts")))
    paths.extend(sorted(JARVIS_COMPONENT_DIR.glob("*.tsx")))
    paths.extend(sorted(JARVIS_HOOK_DIR.glob("*.ts")))
    return "\n".join(_read(path) for path in paths)


def test_pr_160_jarvis_route_remains_read_only_and_has_no_execute_surface():
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
        "callHermes",
        "dispatchHermes",
        "HermesRuntimeAdapter",
        "AIAgent",
    ):
        assert fragment not in source

    for fragment in ("method: 'POST'", 'method: "POST"', "method: 'PUT'", 'method: "PUT"', "method: 'DELETE'", 'method: "DELETE"'):
        assert fragment not in source

    for route in (
        ("/jarvis/execute", "POST"),
        ("/jarvis/approve", "POST"),
        ("/jarvis/reject", "POST"),
        ("/jarvis/hermes/execute", "POST"),
    ):
        assert route not in routes


def test_pr_160_camera_and_microphone_are_still_manual_opt_in():
    page = _read(PAGE)
    shell = _read(JARVIS_COMPONENT_DIR / "JarvisPresenceShell.tsx")
    local_voice = _read(JARVIS_HOOK_DIR / "useLocalVoiceLoop.ts")
    camera = _read(JARVIS_HOOK_DIR / "useJarvisCameraControl.ts")
    recorder = _read(JARVIS_HOOK_DIR / "useJarvisAudioRecorder.ts")

    assert "getUserMedia" not in local_voice
    assert "startCameraPreview()" not in page
    assert "startRecording()" not in page
    assert "startVideoRecording()" not in page
    assert "beginLocalVoiceLoop()" not in page
    assert "onBegin={localVoice.beginLocalVoiceLoop}" in shell
    assert "onStart={cameraControl.startCameraPreview}" in shell
    assert "onStart={audioRecorder.startRecording}" in shell
    assert "onStartVideoRecording={cameraControl.startVideoRecording}" in shell

    for source in (camera, recorder):
        for block in re.findall(r"useEffect\(\(\) => \{.*?\n  \}, \[[^\]]*\]\);", source, flags=re.S):
            assert ".getUserMedia(" not in block
            assert ".start()" not in block


def test_pr_160_visual_states_webgl_fallback_and_reduced_motion_are_present():
    source = _frontend_sources()
    orb = _read(JARVIS_COMPONENT_DIR / "JarvisOrb3D.tsx")
    state_hook = _read(JARVIS_HOOK_DIR / "useJarvisOrbState.ts")

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
        assert state in source

    for marker in (
        'data-testid="jarvis-orb-webgl-fallback"',
        "Fallback visual seguro sin WebGL",
        "webglcontextlost",
        "prefers-reduced-motion",
        "motion-reduce:animate-none",
        "targetFrameMs",
        "particleBudget",
        "pixelRatio",
        "maxParticles",
        "bg-[#01050d]/10",
    ):
        assert marker in orb or marker in state_hook


def test_pr_160_technical_details_are_folded_and_smart_bar_is_human_first():
    source = _frontend_sources()
    smart_bar = _read(JARVIS_COMPONENT_DIR / "JarvisSmartBar.tsx")
    debug_drawer = _read(JARVIS_COMPONENT_DIR / "JarvisDebugDrawer.tsx")

    for marker in (
        'data-testid="jarvis-command-center-tabs"',
        'data-testid="jarvis-tab-detail-panel"',
        "Detalles en pestañas",
        "estado técnico plegado",
        "state map",
        "details",
        "summary",
        "Sensor Ledger",
        "Policy Status",
        "Doctor Local",
        "Event Stream Health",
    ):
        assert marker in source

    for marker in (
        "respuesta humana corta",
        "transcripción temporal local",
        "intent_detected",
        "risk_level",
        "requires_approval",
        "cannot_execute_reason",
        "suggested_next_action",
        "borrador local",
        "No puedo hacer eso, David. Las credenciales y secretos están protegidos.",
    ):
        assert marker in smart_bar

    assert "La experiencia principal es la presencia" in debug_drawer


def test_pr_160_wake_phrase_cannot_approve_or_execute():
    source = _frontend_sources()
    utils = _read(JARVIS_COMPONENT_DIR / "utils.ts")

    for marker in (
        "Wake phrase cannot approve and cannot execute.",
        "Wake phrase nunca aprueba ni ejecuta.",
        "wake no aprueba",
        "wake no ejecuta",
        "wake_phrase_can_approve: false",
        "wake_phrase_is_permission: false",
        "wake_phrase_approval=false",
    ):
        assert marker in source or marker in utils

    assert "approval_by_voice_enabled=false" in source
    assert "hermes_dispatch_allowed: false" in utils


def test_pr_160_visual_dependencies_are_intentional_and_sensor_deps_are_absent():
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
    if all_deps & allowed_3d:
        assert PR_DOC.exists()
        doc = _read(PR_DOC)
        for dep in all_deps & allowed_3d:
            assert dep in doc
