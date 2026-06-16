from pathlib import Path


DOC = Path("docs/jarvis-visual-voice-vision-mobile-roadmap.md")


def test_visual_voice_vision_mobile_roadmap_exists_and_covers_required_contracts():
    assert DOC.exists()
    content = DOC.read_text(encoding="utf-8")
    serialized = content.lower()

    for text in (
        "jarvis gobierna",
        "hermes ejecuta",
        "wake word",
        "no recording by default",
        "mobile companion",
        "approval console",
        "pr #147 - approval console visual",
        "preview-only",
        "no approve/reject/execute",
        "risk level",
        "rollback/stop plan",
        "kill switch",
        "no duplicate hermes",
        "unknown/no fake metrics",
        "pr #151 - vision + mobile companion layer",
        "camera / vision privacy panel",
        "mobile companion / pwa baseline preview",
        "no service worker",
        "no token storage",
        "pr #152 - product finance pilot hardening",
        "finance / roi panel realista",
        "product builder adaptativo",
        "frontend pilot / hardening",
        "no fake revenue",
        "no fake costs",
        "no fake roi",
        "dependency hardening queda para una pr separada",
        "pr #153 - visual command center pilot",
        "visual_command_center_pilot",
        "read_only_pilot",
        "no frontend hermes call",
        "no getusermedia",
        "no fake metrics",
    ):
        assert text in serialized

    assert "camera/vision" in serialized or "camara/vision" in serialized
    assert "no raw audio storage by default" in serialized
    assert "no frontend directo a hermes" in serialized
