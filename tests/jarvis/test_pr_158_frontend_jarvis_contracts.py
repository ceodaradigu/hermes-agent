import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JARVIS_FRONTEND_PATHS = [
    ROOT / "web/src/pages/JarvisCommandCenterPage.tsx",
    *sorted((ROOT / "web/src/components/jarvis").glob("*.tsx")),
    *sorted((ROOT / "web/src/components/jarvis").glob("*.ts")),
    *sorted((ROOT / "web/src/hooks/jarvis").glob("*.ts")),
]


def _combined_jarvis_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in JARVIS_FRONTEND_PATHS)


def test_jarvis_frontend_does_not_introduce_execute_or_dangerous_mutations():
    source = _combined_jarvis_source()

    forbidden = (
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
        "approve/reject real",
        "HermesRuntimeAdapter",
    )
    for fragment in forbidden:
        assert fragment not in source


def test_jarvis_frontend_does_not_call_hermes_directly_from_presence_ui():
    source = _combined_jarvis_source()

    direct_call_fragments = (
        "mark_3_hermes_runtime_bridge.execute",
        "hermes_runtime.execute",
        "callHermes",
        "dispatchHermes",
        "frontend_can_call_hermes_execute: true",
        "frontend_direct_execution_allowed: true",
        "hermes_dispatch_allowed: true",
    )
    for fragment in direct_call_fragments:
        assert fragment not in source


def test_jarvis_frontend_does_not_auto_start_get_user_media():
    local_voice = (ROOT / "web/src/hooks/jarvis/useLocalVoiceLoop.ts").read_text(encoding="utf-8")
    camera = (ROOT / "web/src/hooks/jarvis/useJarvisCameraControl.ts").read_text(encoding="utf-8")
    recorder = (ROOT / "web/src/hooks/jarvis/useJarvisAudioRecorder.ts").read_text(encoding="utf-8")
    page = (ROOT / "web/src/pages/JarvisCommandCenterPage.tsx").read_text(encoding="utf-8")

    assert "getUserMedia" not in local_voice
    assert "beginLocalVoiceLoop()" not in page
    assert "startCameraPreview()" not in page
    assert "startRecording()" not in page
    assert "startVideoRecording()" not in page

    for source in (camera, recorder):
        for block in re.findall(r"useEffect\(\(\) => \{.*?\n  \}, \[[^\]]*\]\);", source, flags=re.S):
            assert ".getUserMedia(" not in block
            assert ".start()" not in block


def test_jarvis_frontend_bridge_contract_exposes_v2_fields_and_safe_defaults():
    types = (ROOT / "web/src/components/jarvis/types.ts").read_text(encoding="utf-8")
    utils = (ROOT / "web/src/components/jarvis/utils.ts").read_text(encoding="utf-8")
    smart_bar = (ROOT / "web/src/components/jarvis/JarvisSmartBar.tsx").read_text(encoding="utf-8")

    for field in (
        "confidence",
        "approval_level",
        "hermes_dispatch_allowed",
        "cannot_execute_reason",
        "suggested_next_action",
    ):
        assert field in types
        assert field in smart_bar
    assert "denied_secret_or_credential_access" in utils
    assert "wake_phrase_approval_or_execution_attempt" in utils
    assert "Wake phrase cannot approve and cannot execute." in utils
    assert "No LLM real" in (ROOT / "web/src/components/jarvis/JarvisDebugDrawer.tsx").read_text(encoding="utf-8")
