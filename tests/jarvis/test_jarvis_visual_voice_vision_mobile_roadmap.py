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
    ):
        assert text in serialized

    assert "camera/vision" in serialized or "camara/vision" in serialized
    assert "no raw audio storage by default" in serialized
    assert "no frontend directo a hermes" in serialized
