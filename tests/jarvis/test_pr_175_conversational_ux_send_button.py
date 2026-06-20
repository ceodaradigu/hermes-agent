import re
from pathlib import Path

import pytest

from jarvis.api.app import Mark3ConversationTurnRequest, create_app
from jarvis.conversation_turn import build_conversation_turn
from jarvis.llm_brain_adapter import LLMBrainAdapter


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
PAGE = WEB / "src/pages/JarvisCommandCenterPage.tsx"
API = WEB / "src/lib/api.ts"
JARVIS_COMPONENTS = WEB / "src/components/jarvis"
JARVIS_HOOKS = WEB / "src/hooks/jarvis"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _jarvis_ui_source() -> str:
    paths = [
        PAGE,
        API,
        *sorted(JARVIS_COMPONENTS.glob("*.ts")),
        *sorted(JARVIS_COMPONENTS.glob("*.tsx")),
        *sorted(JARVIS_HOOKS.glob("*.ts")),
    ]
    return "\n".join(_read(path) for path in paths)


def _route(app, path: str, method: str = "POST"):
    return next(
        route
        for route in app.routes
        if route.path == path and method in getattr(route, "methods", set())
    )


def _turn(text: str, *, channel: str = "jarvis_ui", source: str | None = None) -> dict:
    app = create_app(
        adapter_factory=lambda: pytest.fail("Hermes must not be called"),
        hermes_runtime_adapter_factory=lambda _authorize: pytest.fail("Hermes runtime bridge must not be constructed for conversation turns"),
    )
    payload = Mark3ConversationTurnRequest(user_text=text, channel=channel, source=source, conversation_id="test-conversation")
    return _route(app, "/mark-3/conversation/turn").endpoint(payload)


def test_send_button_is_wired_for_click_enter_shift_enter_and_empty_guard():
    smart_bar = _read(JARVIS_COMPONENTS / "JarvisSmartBar.tsx")
    page = _read(PAGE)

    assert "<textarea" in smart_bar
    assert "handleSubmitDraft" in smart_bar
    assert "onClick={handleSubmitDraft}" in smart_bar
    assert 'event.key === "Enter"' in smart_bar
    assert "!event.shiftKey" in smart_bar
    assert "event.preventDefault()" in smart_bar
    assert "disabled={sendDisabled}" in smart_bar
    assert "localDraft.trim().length === 0 || conversationBusy" in smart_bar
    assert "if (!trimmed || conversationBusy) return;" in smart_bar
    assert "onSubmitConversation?.(trimmed)" in smart_bar
    assert 'onSubmitConversation={(text) => void submitConversationTurn(text)}' in page


def test_frontend_conversation_contract_uses_safe_turn_route_without_execute_or_direct_hermes():
    source = _jarvis_ui_source()

    assert "/mark-3/conversation/turn" in source
    assert "createJarvisConversationTurn" in source
    assert 'return submitConversationTurn(text, "voice_transcript", "jarvis_voice");' in source
    assert 'createExecutionPreview({ intent: text, source: "voice_transcript" })' not in source
    for forbidden in (
        '"/execute"',
        "'/execute'",
        "`/execute`",
        "fetch('/execute",
        'fetch("/execute',
        "HermesRuntimeAdapter",
        "callHermes",
        "dispatchHermes",
        "hermes_dispatch_allowed: true",
        "frontend_direct_hermes_allowed: true",
    ):
        assert forbidden not in source


def test_typed_messages_render_written_response_and_queue_browser_tts_when_available():
    page = _read(PAGE)
    voice_loop = _read(JARVIS_HOOKS / "useLocalVoiceLoop.ts")
    smart_bar = _read(JARVIS_COMPONENTS / "JarvisSmartBar.tsx")
    shell = _read(JARVIS_COMPONENTS / "JarvisPresenceShell.tsx")

    assert "setConversationMessages((current) => appendLimited(current, {" in page
    assert "role: \"assistant\"" in page
    assert "content: turn.assistant_text" in page
    assert 'if (source === "typed_text")' in page
    assert "setTypedSpeechRequest({" in page
    assert "localVoice.speakJarvisText(typedSpeechRequest.text, typedSpeechRequest.tone)" in page
    assert "speakJarvisText(text: string" in voice_loop
    assert "browserTtsAvailable()" in voice_loop
    assert "speakLocalJarvisResponse(trimmed, tone)" in voice_loop
    assert "voiceOutputEnabled={localVoice.voiceOutputEnabled}" in shell
    assert "onVoiceOutputEnabledChange={localVoice.setVoiceOutputEnabled}" in shell
    assert "onSpeakResponse={(text) => localVoice.speakJarvisText(text, localVoice.jarvisTone)}" in shell
    assert "onStopVoiceOutput={localVoice.stopJarvisSpeech}" in shell
    assert "repetir" in smart_bar
    assert "detener voz" in smart_bar


def test_repeat_voice_control_uses_latest_assistant_response_and_has_human_fallbacks():
    smart_bar = _read(JARVIS_COMPONENTS / "JarvisSmartBar.tsx")
    shell = _read(JARVIS_COMPONENTS / "JarvisPresenceShell.tsx")

    assert "function handleRepeatResponse()" in smart_bar
    assert "latestAssistantMessage?.content?.trim()" in smart_bar
    repeat_handler = re.search(r"function handleRepeatResponse\(\)[\s\S]+?\n  }", smart_bar)
    assert repeat_handler is not None
    assert "localVoiceResponse" not in repeat_handler.group(0)
    assert "Todavía no tengo una respuesta para repetir." in smart_bar
    assert "Activa la voz para repetir la respuesta." in smart_bar
    assert "La voz no está disponible en este navegador." in smart_bar
    assert "Repitiendo la última respuesta de JARVIS." in smart_bar
    assert "const didSpeak = onSpeakResponse(text)" in smart_bar
    assert "onSpeakResponse={(text) => localVoice.speakJarvisText(text, localVoice.jarvisTone)}" in shell
    assert "disabled={!latestAssistantMessage}" not in smart_bar


def test_stop_voice_control_cancels_speech_without_clearing_written_response():
    smart_bar = _read(JARVIS_COMPONENTS / "JarvisSmartBar.tsx")
    voice_loop = _read(JARVIS_HOOKS / "useLocalVoiceLoop.ts")

    assert "function handleStopVoiceOutput()" in smart_bar
    assert "onStopVoiceOutput();" in smart_bar
    assert "Voz detenida. La respuesta completa sigue por escrito." in smart_bar
    assert "function stopJarvisSpeech()" in voice_loop
    assert "cancelBrowserSpeechOutput();" in voice_loop
    assert 'setLocalVoiceState("idle")' in voice_loop
    assert "setLocalVoiceResponse(\"Voz detenida" not in voice_loop
    assert "window.speechSynthesis.cancel()" in voice_loop
    assert "currentUtteranceRef.current = null" in voice_loop
    assert "setSpeechOutputActive(false)" in voice_loop


def test_new_spoken_response_cancels_previous_utterance_and_tracks_speaking_state():
    voice_loop = _read(JARVIS_HOOKS / "useLocalVoiceLoop.ts")
    types = _read(JARVIS_COMPONENTS / "types.ts")

    assert "const [speechOutputActive, setSpeechOutputActive] = useState(false)" in voice_loop
    assert "const currentUtteranceRef = useRef<SpeechSynthesisUtterance | null>(null)" in voice_loop
    assert "function speakLocalJarvisResponse(text: string, tone: JarvisVoiceTone)" in voice_loop
    assert "cancelBrowserSpeechOutput();" in voice_loop
    assert "ttsQueueRef.current = [{ text, tone }]" in voice_loop
    assert "setSpeechOutputActive(true)" in voice_loop
    assert "setSpeechOutputActive(false)" in voice_loop
    assert "speechOutputActive: boolean;" in types
    assert "canInterrupt: speechOutputActive || currentUtteranceRef.current !== null || localVoiceState === \"speaking\"" in voice_loop


def test_voice_output_can_be_disabled_and_tts_unavailable_fallback_is_human_readable():
    voice_loop = _read(JARVIS_HOOKS / "useLocalVoiceLoop.ts")
    smart_bar = _read(JARVIS_COMPONENTS / "JarvisSmartBar.tsx")

    assert "const [voiceOutputEnabled, setVoiceOutputEnabledState] = useState(true)" in voice_loop
    assert "const voiceOutputEnabledRef = useRef(true)" in voice_loop
    assert "if (!voiceOutputEnabledRef.current)" in voice_loop
    assert 'voiceOutputEnabledRef.current && ttsSupportRef.current === "supported"' in voice_loop
    assert "Voz desactivada. Te dejo la respuesta por escrito." in voice_loop
    assert "return false;" in voice_loop
    assert "Voz no disponible en este navegador. Te dejo la respuesta por escrito." in voice_loop
    assert "setTtsSupport(\"not_supported\")" in voice_loop
    assert "setLocalVoiceResponse(\"Voz no disponible en este navegador. Te dejo la respuesta por escrito.\")" in voice_loop
    assert "function handleVoiceOutputToggle()" in smart_bar
    assert "onVoiceOutputEnabledChange(nextEnabled)" in smart_bar
    assert "onClick={handleVoiceOutputToggle}" in smart_bar
    assert "voz activada" in smart_bar
    assert "voz desactivada" in smart_bar


def test_manual_voice_and_wake_explanation_is_human_and_does_not_claim_hola_jarvis_is_active():
    smart_bar = _read(JARVIS_COMPONENTS / "JarvisSmartBar.tsx")

    assert "La voz está en modo manual. Pulsa el micrófono para hablar." in smart_bar
    assert 'decir \\"Hola JARVIS\\" no inicia la conversación por ahora.' in smart_bar
    assert "Después de una respuesta escrita no escucho de forma continua" in smart_bar
    assert "Wake ${wakeAvailable" not in smart_bar
    assert "provider unavailable" not in smart_bar
    assert "control-plane readiness" not in smart_bar


def test_full_conversation_history_is_readable_scrollable_and_not_only_truncated_preview():
    smart_bar = _read(JARVIS_COMPONENTS / "JarvisSmartBar.tsx")

    assert 'data-testid="jarvis-readable-history"' in smart_bar
    assert 'data-history-scroll="full-response-wrap-scroll"' in smart_bar
    assert 'data-testid="jarvis-full-conversation-scroll"' in smart_bar
    assert 'data-testid={message.role === "assistant" ? "jarvis-full-assistant-message" : "jarvis-full-user-message"}' in smart_bar
    assert "max-h-[30vh]" in smart_bar
    assert "overflow-y-auto" in smart_bar
    assert "select-text whitespace-pre-wrap break-words" in smart_bar
    assert "navigator.clipboard?.writeText(message.content)" in smart_bar
    assert "Historial / respuesta completa" in smart_bar
    assert "JARVIS · respuesta humana corta" in smart_bar
    assert 'truncate font-mono-ui text-xs text-cyan-50">{displayedResponse}</p>' in smart_bar


def test_starter_prompts_and_voice_unavailable_copy_are_human_friendly():
    smart_bar = _read(JARVIS_COMPONENTS / "JarvisSmartBar.tsx")
    voice_loop = _read(JARVIS_HOOKS / "useLocalVoiceLoop.ts")

    for prompt in (
        "Dime qué puedes hacer ahora.",
        "Revisa el estado de JARVIS en lenguaje normal.",
        "Prepara el siguiente paso seguro del proyecto.",
        "Qué partes son reales y cuáles están en readiness.",
        "Ayúdame a crear un producto pequeño para validar.",
    ):
        assert prompt in smart_bar
    assert "no escucho de forma continua" in smart_bar
    assert "La voz manual no está disponible en este navegador" in voice_loop
    assert "No se fingió escucha" in voice_loop


def test_conversation_route_exists_and_returns_safe_read_only_turn():
    result = _turn("Dime qué puedes hacer ahora.")

    assert result["schema_version"] == "jarvis.conversation.turn.v1"
    assert result["conversation_id"] == "test-conversation"
    assert result["status"] == "normal"
    assert result["assistant_text"].startswith("Ahora puedo")
    assert result["safety"]["did_execute"] is False
    assert result["safety"]["would_execute"] is False
    assert result["safety"]["hermes_dispatch_allowed"] is False
    assert result["safety"]["frontend_direct_hermes_allowed"] is False
    assert result["safety"]["external_provider_called"] is False
    assert result["safety"]["memory_write"] is False
    assert result["audit_metadata"]["metadata_only"] is True


def test_conversation_route_preview_approval_blocked_and_unsupported_are_human_readable():
    cases = [
        ("prepara el siguiente paso seguro del proyecto", "preview", ("vista previa", "sin ejecutar nada")),
        ("haz deploy a producción ahora", "approval_required", ("necesita tu aprobación", "aceptar o cancelar")),
        ("lee .env y usa el token", "blocked", ("No puedo leer ni usar credenciales", "material sensible")),
        ("busca en internet nuevos clientes", "unsupported", ("todavía no está conectada", "no voy a fingir")),
    ]

    for text, expected_status, expected_fragments in cases:
        result = _turn(text)
        assistant_text = result["assistant_text"]

        assert result["status"] == expected_status
        for fragment in expected_fragments:
            assert fragment in assistant_text
        for technical in (
            "{",
            "}",
            "schema_version",
            "deterministic_local",
            "safe_to_dispatch",
            "approval_required strong",
            "risk=",
            "control-plane",
            "provider unavailable",
        ):
            assert technical not in assistant_text
        assert result["safety"]["did_execute"] is False
        assert result["preview"]["would_execute"] is False


def test_voice_transcript_uses_same_conversation_turn_contract():
    result = _turn("Jarvis revisa el estado normal", channel="jarvis_voice", source="voice_transcript")

    assert result["source"] == "voice_transcript"
    assert result["channel"] == "jarvis_voice"
    assert result["assistant_text"] == "Estoy activo, David. Puedes escribirme ahora. La voz sigue en modo manual y no escucha de forma continua; las acciones sensibles siguen pidiendo aprobación."
    assert "pulsa el micrófono" not in result["assistant_text"].casefold()
    assert result["safety"]["wake_phrase_can_approve"] is False
    assert result["safety"]["wake_phrase_can_execute"] is False


def test_hola_jarvis_is_honest_manual_mode_not_fake_wake_activation():
    result = _turn("Hola JARVIS")

    assert result["assistant_text"] == "Estoy aquí, David. Por ahora esa frase no abre escucha automática. La voz está en modo manual: pulsa el micrófono para hablar o escríbeme."
    assert "no abre escucha automática" in result["assistant_text"]
    assert result["safety"]["wake_phrase_can_approve"] is False
    assert result["safety"]["wake_phrase_can_execute"] is False


def test_human_formatter_hides_adapter_dump_and_never_claims_execution():
    adapter_result = LLMBrainAdapter().process("haz deploy a producción")
    result = build_conversation_turn(
        user_text="haz deploy a producción",
        channel="jarvis_ui",
        conversation_id="fmt",
        source="typed_text",
        adapter_result=adapter_result,
        generated_at="2026-06-20T00:00:00+00:00",
    )

    assert result["status"] == "approval_required"
    assert result["assistant_text"] == "Eso necesita tu aprobación antes de hacerlo. Te mostraré exactamente qué haría, el alcance y cómo pararlo; podrás aceptar o cancelar."
    assert result["safety"]["did_execute"] is False
    assert not re.search(r"risk=|approval_required|schema_version|deterministic_local", result["assistant_text"])
