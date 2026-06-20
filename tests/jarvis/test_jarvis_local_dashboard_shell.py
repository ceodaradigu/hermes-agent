from pathlib import Path

import pytest

from jarvis.api.app import create_app


PAGE = Path("web/src/pages/JarvisCommandCenterPage.tsx")
APP = Path("web/src/App.tsx")
API = Path("web/src/lib/api.ts")
VITE_CONFIG = Path("web/vite.config.ts")
JARVIS_COMPONENT_DIR = Path("web/src/components/jarvis")
JARVIS_HOOK_DIR = Path("web/src/hooks/jarvis")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _jarvis_sources() -> str:
    paths = [PAGE]
    paths.extend(sorted(JARVIS_COMPONENT_DIR.glob("*.ts")))
    paths.extend(sorted(JARVIS_COMPONENT_DIR.glob("*.tsx")))
    paths.extend(sorted(JARVIS_HOOK_DIR.glob("*.ts")))
    return "\n".join(_read(path) for path in paths)


def test_jarvis_dashboard_shell_file_and_local_route_exist():
    assert PAGE.exists()
    app_source = _read(APP)
    vite_source = _read(VITE_CONFIG)

    assert "JarvisCommandCenterPage" in app_source
    assert '{ id: "jarvis", label: "JARVIS"' in app_source
    assert '"/jarvis": "jarvis"' in app_source
    assert '"/mark-3": "http://127.0.0.1:9119"' in vite_source


def test_jarvis_dashboard_shell_contains_required_read_only_content():
    content = _jarvis_sources()

    for text in (
        "Centro de Mando JARVIS",
        "Núcleo de Voz JARVIS",
        "Control de Misión",
        "preview-only",
        "En esta fase no se ejecuta nada",
        "Conversation Preview",
        "Preview conversation",
        "Intent / Risk Preview",
        "Mission Lifecycle",
        "Safety Banner",
        "No auto execute",
        "No Hermes dispatch",
        "No tool call",
        "No file write",
        "No network",
        "No hidden voice recording",
        "No camera auto capture",
        "Wake phrase is not permission",
        "Si una misión necesita algo sensible, aparecerá en Approval Console",
        "Hermes solo ejecutará después de approval válido",
        "El frontend no puede saltarse gates",
        "JARVIS gobierna",
        "Hermes ejecuta",
        "Consola de Aprobación",
        "Hermes Execution",
        "Ejecución Hermes",
        "El frontend no puede ejecutar Hermes directamente",
        "Sin ejecución activa",
        "Capacidades gobernadas",
        "Rutas bloqueadas",
        "Requisitos antes de ejecución futura",
        "approval válido",
        "scope exacto",
        "coste/impacto",
        "operador humano",
        "Kill Switch",
        "KILL SWITCH",
        "No fake metrics",
        "unknown",
        "La cámara no graba por defecto",
        "Mobile es una interfaz, no un runtime",
        "La wake phrase nunca aprueba acciones",
        "La voz puede ser canal de aprobación solo si está autenticada, gateada y auditada",
        "Las acciones sensibles requieren aprobación humana",
        "Las acciones críticas requieren confirmación fuerte",
        "Hermes ejecuta solo bajo gates válidos",
        "Stop/cancel pasan por /mark-3/execution/stop y /mark-3/execution/cancel",
        "La shell no ejecuta Hermes directo; solicita dispatch gobernado",
        "Backend-gated: approval execution is wired through /mark-3/execution",
        "Leyenda de riesgo",
        "Nivel 0-1",
        "Nivel 5",
        "Readback / confirmación fuerte",
        "Cámara / Visión",
        "Preview local con botón explícito",
        "No se sube vídeo al backend",
        "No hay proveedor externo de visión",
        "La visión futura requerirá permiso explícito y auditoría",
        "Mobile no ejecuta acciones",
        "Approvals reales desde móvil quedan future-gated",
        "No se guardan credenciales ni tokens",
        "Sensor Ledger",
        "metadata-only",
        "No guarda audio bruto, frames, vídeo, imágenes, tokens ni credenciales",
        "requested / started / stopped / cancelled / failed / deleted / retention_updated",
        "Sensores requieren opt-in, indicador visible, stop/cancel y auditoría",
        "Event Stream Health",
        "schema_version / event_id / heartbeat",
        "El stream no ejecuta comandos",
        "No transporta secretos, audio bruto ni frames",
        "Heartbeat y snapshot son seguros ante desconexión",
        "Policy Status",
        "Wake phrase never approves",
        "Frontend never executes Hermes directly",
        "Dangerous execution requires ApprovalGateway, risk classification, audit and rollback/stop plan",
    ):
        assert text in content

    for state in (
        "idle",
        "listening",
        "transcribing",
        "not_supported",
        "unavailable",
        "offline",
        "online",
        "preview",
        "dormant",
        "dormido",
        "listening_wake_word",
        "listening_command",
        "thinking",
        "speaking",
        "approval_required",
        "hermes_executing",
        "paused",
        "blocked",
        "error",
        "kill_switch",
    ):
        assert state in content


def test_jarvis_dashboard_shell_contains_voice_core_tts_preview_contract():
    content = _jarvis_sources()

    for text in (
        "Núcleo de Voz JARVIS",
        "No estoy escuchando ni grabando audio",
        "Local Voice Loop",
        "Conversación manual continua",
        "SpeechRecognition / webkitSpeechRecognition",
        "speechSynthesis",
        "selección preferente de voz española",
        "Soporte dependiente del navegador",
        "No always-listening",
        "No wake listener persistente",
        "No audio bruto almacenado",
        "No audio bruto enviado al backend",
        "raw_audio_sent_to_backend=false",
        "approval_by_voice_enabled=false",
        "wake_phrase_approval=false",
        "tono calmado",
        "tono concentrado",
        "tono alerta",
        "tono intenso",
        "Política wake word",
        "Frases soportadas futuras: Hola Jarvis, Jarvis.",
        "La wake phrase nunca aprueba acciones",
        "La wake phrase no ejecuta acciones",
        "Las acciones críticas requieren readback y confirmación fuerte",
        "Privacidad voz",
        "micrófono: manual bajo botón explícito",
        "conversation_active",
        "wake_listening",
        "raw recorder",
        "grabación: false",
        "audio bruto almacenado: false",
        "proveedor de navegador puede variar",
        "background listening",
        "voice approval",
        "La voz puede preparar una intención futura",
        "Si requiere aprobación, aparecerá en Approval Console",
        "Frontend/voice no llama Hermes directamente",
        "Kill Switch voz",
        "Stop cancela escucha y speechSynthesis",
        "JARVIS aún no tiene wake listener persistente real en esta PR; la conversación se activa manualmente. Arquitectura preparada para wake phrase sin grabar ni transcribir todo.",
        "La integración futura deberá cortar wake runtime y ejecución gobernada",
    ):
        assert text in content


def test_jarvis_dashboard_shell_contains_wake_word_local_safe_flow_contract():
    content = _jarvis_sources()

    for text in (
        "Wake Word Local Safe Flow",
        "wake listening sin grabación ni transcripción continua",
        "micrófono hard-off",
        "Hola Jarvis",
        "Jarvis",
        "Stop phrases",
        "Mic hard-off",
        "Wake-word-only",
        "Command listening",
        "Push-to-talk",
        "Typed preview",
        "Hola Jarvis, revisa el estado del proyecto",
        "wake phrase detectada",
        "comando restante",
        "abriría ventana de comando",
        "ejecutaría",
        "aprobaría",
        "llamaría Hermes",
        "La wake phrase nunca aprueba acciones",
        "La wake phrase no ejecuta acciones",
        "La wake phrase solo puede abrir una ventana de comando futura",
        "La aprobación por voz requiere canal autenticado, readback y auditoría",
        "Las acciones críticas requieren doble o triple confirmación",
        "no micrófono always-on",
        "no grabación",
        "no STT persistente",
        "no TTS como approval",
        "no provider backend de audio",
        "no background listener",
        "no Hermes dispatch",
        "no auto execute",
    ):
        assert text in content


def test_jarvis_dashboard_shell_uses_only_browser_speech_api_without_raw_capture():
    content = _jarvis_sources()

    for required in (
        "SpeechRecognition",
        "webkitSpeechRecognition",
        "speechSynthesis",
        "SpeechSynthesisUtterance",
        "onBegin={localVoice.beginLocalVoiceLoop}",
        "onCancel={localVoice.cancelLocalVoiceLoop}",
        "queueNextLocalVoiceTurn",
        "selectPreferredSpanishVoice",
        "conversationActive",
        "No audio bruto enviado al backend",
        "No always-listening",
    ):
        assert required in content

    for forbidden in (
        "AudioContext",
        "webkitAudioContext",
        "navigator.permissions",
        "recordedChunks",
        "startListening",
        "stopListening",
        "recordAudio",
        "listenForWakeWord",
        "wakeWordListener",
        "captureImage",
        "captureFrame",
        "takeSnapshot",
        "saveSnapshot",
        "streamCamera",
        "analyzeVision",
        "analyzeImage",
        "navigator.serviceWorker",
        "serviceWorker.register",
        "ServiceWorkerRegistration",
        "PushManager",
        "Notification.requestPermission",
        "sync.register",
        "periodicSync",
        "BackgroundSync",
    ):
        assert forbidden not in content

    sensor_hooks = _read(JARVIS_HOOK_DIR / "useJarvisCameraControl.ts") + _read(JARVIS_HOOK_DIR / "useJarvisAudioRecorder.ts")
    page_and_shell = _read(PAGE) + _read(JARVIS_COMPONENT_DIR / "JarvisPresenceShell.tsx")
    assert "navigator.mediaDevices.getUserMedia" in sensor_hooks
    assert "MediaRecorder" in sensor_hooks
    assert "raw_audio_sent_to_backend: false" in sensor_hooks
    assert ".getUserMedia(" not in page_and_shell
    assert "new MediaRecorder" not in page_and_shell


def test_jarvis_local_voice_loop_has_conversational_brain_not_transcript_echo():
    content = _read(JARVIS_COMPONENT_DIR / "utils.ts") + _read(JARVIS_HOOK_DIR / "useLocalVoiceLoop.ts")
    smart_bar = _read(JARVIS_COMPONENT_DIR / "JarvisSmartBar.tsx")

    for text in (
        "buildLocalJarvisResponse",
        "Sí, David. Estoy contigo en modo local.",
        "Ahora puedo conversar contigo, mostrar el estado visible de JARVIS",
        "esa misión",
        "Puedo preparar ${noun} como vista previa",
        "No puedo hacer eso, David. Las credenciales y secretos están protegidos.",
        "No aprobaré ni ejecutaré por voz",
        "La frase de activación no es permiso",
        "intent_detected",
        "risk_level",
        "requires_approval",
        "can_prepare_preview",
        "cannot_execute_reason",
        "suggested_next_action",
    ):
        assert text in content or text in smart_bar

    for forbidden in (
        'Te escuché: "${normalized}"',
        "he escuchado lo que has dicho",
        "solo repite",
        "dispatchHermes",
        '"/execute"',
        "/execute",
    ):
        assert forbidden not in content


def test_jarvis_dashboard_shell_contains_camera_vision_privacy_panel_contract():
    content = _jarvis_sources()

    for text in (
        "Cámara / Visión",
        "preview-only",
        "La cámara no graba por defecto.",
        "La visión solo se activa con permiso explícito.",
        "Estado actual",
        "permiso solicitado",
        "recording",
        "Grabar vídeo",
        "Stop vídeo",
        "Descargar vídeo",
        "Borrar vídeo",
        "REC local",
        "El navegador no soporta grabación de vídeo local.",
        "browser-sensor-ledger-overlay",
        "recent_sensor_events",
        "backend_ingestion_enabled: false",
        "no_video_frames: true",
        "streaming",
        "snapshot",
        "vision analysis",
        "provider externo",
        "Privacidad",
        "no camera activation on load",
        "manual getUserMedia only",
        "no recording",
        "no snapshot",
        "no image/video storage",
        "explicit operator permission required",
        "visual indicator required",
        "audit required",
        "cámara apagada",
        "permiso requerido",
        "preview futuro",
        "análisis futuro",
        "grabación desactivada",
        "almacenamiento desactivado",
        "kill switch",
        "Botón explícito, permiso del navegador e indicador visible.",
        "No se captura snapshot, no se almacena vídeo y no se sube streaming.",
        "La grabación de vídeo es local, descargable y borrable.",
        "No se sube vídeo al backend.",
        "No hay proveedor externo de visión.",
        "Stop corta tracks locales",
    ):
        assert text in content


def test_jarvis_dashboard_shell_contains_mobile_companion_preview_contract():
    content = _jarvis_sources()

    for text in (
        "Mobile Companion",
        "preview-only",
        "Mobile es una interfaz, no un runtime.",
        "Mobile no llama a Hermes directamente.",
        "PWA baseline",
        "mobile runtime",
        "approvals reales desde móvil",
        "remote kill switch",
        "mobile camera",
        "mobile microphone",
        "notifications",
        "offline cache",
        "service worker",
        "push",
        "background sync",
        "Estado",
        "Approvals preview",
        "Mission preview",
        "Hermes visibility",
        "Voice status",
        "Camera status",
        "Finance summary",
        "Kill switch preview",
        "no execute",
        "no Hermes direct",
        "no mobile execute",
        "no direct Hermes call",
        "no mobile sensor activation",
        "no real mobile approvals in this PR",
        "approval requires backend gate",
        "critical approval requires strong confirmation",
        "No se guardan credenciales ni tokens.",
    ):
        assert text in content


def test_jarvis_dashboard_shell_contains_product_finance_pilot_hardening_contract():
    content = _jarvis_sources()

    for text in (
        "Finance / ROI",
        "No fake metrics.",
        "Si no hay evidencia, mostrar unknown.",
        "Revenue confirmado requiere evidencia.",
        "ROI queda unknown sin revenue y costes reales.",
        "No se mueve dinero desde este panel.",
        "Stripe live requiere aprobación fuerte.",
        "coste real",
        "coste estimado",
        "revenue confirmado",
        "revenue proyectado",
        "gross revenue",
        "expenses",
        "net revenue",
        "budget",
        "Product Builder Adaptativo",
        "No es un Template Builder.",
        "Si dos productos parecen clones, el builder ha fallado.",
        "Deploy real requiere aprobación fuerte.",
        "Stripe/checkout real requiere aprobación fuerte.",
        "Revenue real requiere confirmación.",
        "Idea",
        "Validación",
        "Blueprint",
        "Código",
        "Landing",
        "Deploy candidate",
        "Monetización",
        "Medición",
        "preview / future-gated / disabled",
        "Pilot backend-gated",
        "Frontend Pilot / Hardening",
        "El dashboard no ejecuta Hermes directo.",
        "POST solo a endpoints gobernados.",
        "No execute.",
        "No sensores sin activación manual.",
        "Dependency hardening queda para una PR separada.",
        "/jarvis",
        "/mark-3/dashboard/status",
        "finance_roi_visible",
        "product_builder_visible",
        "no_frontend_execute",
        "no_uncontrolled_sensor_activation",
        "npm audit vulnerabilities observed",
        "full pytest required before merge",
    ):
        assert text in content


def test_jarvis_dashboard_shell_contains_visual_command_center_pilot_contract():
    content = _jarvis_sources()

    for text in (
        "Visual Command Center Pilot",
        "/jarvis",
        "/mark-3/dashboard/status",
        "governed pilot",
        "El dashboard no ejecuta Hermes directo",
        "No se ejecuta Hermes desde el frontend",
        "No se activan sensores sin control manual explícito",
        "Approvals reales pasan por backend gobernado",
        "No hay métricas falsas",
        "Los valores sin evidencia se muestran como unknown",
        "Dependency hardening queda para una PR separada",
        "Checklist de panels",
        "Checklist de seguridad",
        "Estado de botones críticos",
        "Pasos para el operador",
        "Limitaciones conocidas",
        "Header",
        "Voice Core",
        "Local Voice Loop",
        "Wake Word Local Safe Flow",
        "Mission Control",
        "Approval Console",
        "Hermes Execution",
        "Agent / Module Radar",
        "Camera / Vision",
        "Mobile Companion",
        "Finance / ROI",
        "Product Builder Adaptativo",
        "Frontend Pilot / Hardening",
        "Live Timeline / Audit",
        "Kill Switch",
        "no_post_put_delete",
        "no_execute_route",
        "manual_get_user_media_only",
        "manual_media_recorder_only",
        "no_money_movement",
        "no_fake_metrics",
        "unknown",
    ):
        assert text in content

    for text in (
        "Cockpit",
        "Approvals",
        "Hermes",
        "Voice / Wake",
        "Vision / Mobile",
        "Finance / Product",
        "Pilot / Audit",
        "Visual Command Center",
        "Detalles en pestañas",
        'data-testid="jarvis-cockpit-layout"',
        'data-testid="jarvis-command-center-header"',
        'data-testid="jarvis-tab-detail-panel"',
        "modo approval backend-gated",
        "max-h-[64vh] overflow-auto",
    ):
        assert text in content

    api_content = _read(API)
    assert 'method: "POST"' in api_content
    for governed_endpoint in (
        "/mark-3/execution/preview",
        "/mark-3/execution/request-approval",
        "/mark-3/execution/approval-decision",
        "/mark-3/execution/dispatch",
        "/mark-3/execution/cancel",
        "/mark-3/execution/stop",
    ):
        assert governed_endpoint in api_content

    for forbidden in (
        'method: "PUT"',
        'method: "DELETE"',
        '"/execute"',
        "/execute",
        "checkout.sessions.create",
        "createCheckout",
        "paymentIntent",
        "moveMoney",
        "transfer.create",
    ):
        assert forbidden not in content


def test_jarvis_dashboard_shell_contains_presence_ui_local_system_contract():
    content = _jarvis_sources()

    for text in (
        "Presence UI",
        "Local System Contract",
        "JARVIS Presence UI + Local System Contract",
        "reactor/orbe cinematográfico",
        "orbe 3D real / HUD cinematográfico",
        "partículas",
        "HUD futurista",
        "JARVIS runtime/daemon local es el sistema",
        "/jarvis es solo la interfaz visual",
        "móvil y VPS serán clientes/puentes futuros",
        "frontend no ejecuta directamente Hermes",
        "voz local controlada disponible en esta PR",
        "cámara preview y grabación local bajo botón explícito",
        "idle/calmado",
        "escuchando",
        "transcribiendo",
        "pensando",
        "hablando",
        "error/no disponible",
        "smart bar",
        "barra inteligente inferior",
        "transcripción temporal local",
        "respuesta temporal local controlada",
        "reactor de presencia",
        "Historial plegado / folded history",
        "camera preview",
        "Preview local",
        "raw audio recorder",
        'data-testid="jarvis-smart-bar"',
        'data-testid="jarvis-camera-preview-panel"',
        'data-testid="jarvis-local-audio-recorder"',
        'data-testid="jarvis-folded-history"',
        'data-testid="jarvis-local-system-contract"',
    ):
        assert text in content


def test_jarvis_dashboard_shell_contains_phase_2_cinematic_orb_and_fallback_contract():
    content = _jarvis_sources()
    orb_source = _read(JARVIS_COMPONENT_DIR / "JarvisOrb3D.tsx")

    for text in (
        'data-testid="jarvis-cinematic-orb-hud"',
        'data-testid="jarvis-holographic-radial-marks"',
        'data-testid="jarvis-state-wave-rings"',
        'data-testid="jarvis-orb-webgl-fallback"',
        "reactor/orbe cinematográfico WebGL con bloom, profundidad, partículas, anillos y HUD futurista",
        "fallback sin WebGL",
        "fallback si canvas falla",
        "FPS budget",
        "particle budget",
        "power save",
        "idle wake_listening listening transcribing thinking speaking alert error stopped executing",
        "Fallback visual seguro sin WebGL",
        "orbe 3D real / HUD cinematográfico",
        "marcas holográficas",
        "partículas orbitando",
        "HUD agresivo futurista",
    ):
        assert text in content

    for state in (
        "idle",
        "wake_listening",
        "listening",
        "transcribing",
        "thinking",
        "speaking",
        "alert",
        "error",
        "stopped",
        "executing",
    ):
        assert state in orb_source

    for performance_marker in (
        "targetFrameMs",
        "particleBudget",
        "prefers-reduced-motion",
        "webglcontextlost",
        "powerPreference",
        "maxParticles",
    ):
        assert performance_marker in orb_source


def test_phase_2_orb_does_not_add_sensor_or_execution_apis():
    orb_source = _read(JARVIS_COMPONENT_DIR / "JarvisOrb3D.tsx")
    shell_source = _read(JARVIS_COMPONENT_DIR / "JarvisPresenceShell.tsx")

    for forbidden in (
        "navigator.mediaDevices",
        ".getUserMedia(",
        "getUserMedia(",
        "MediaRecorder",
        "AudioContext",
        "webkitAudioContext",
        "new EventSource",
        "fetch(",
        'method: "POST"',
        'method: "PUT"',
        'method: "DELETE"',
        '"/execute"',
        "/execute",
        "HermesRuntimeAdapter",
        "AIAgent",
    ):
        assert forbidden not in orb_source

    assert "hermesRuntime.active_execution === true" in shell_source
    assert "latestWakeEvent?.payload?.wake_runtime_enabled === true" in shell_source
    assert "approvalsPending" in shell_source


def test_jarvis_dashboard_shell_does_not_call_hermes_or_runtime_from_frontend():
    content = _jarvis_sources()
    api_source = _read(API)

    assert "api.getJarvisDashboardStatus()" in content
    assert '"/mark-3/dashboard/status"' in content
    assert 'getJarvisDashboardStatus: () => fetchJSON<JarvisDashboardStatus>("/mark-3/dashboard/status")' in api_source

    for forbidden in (
        "method:",
        '"POST"',
        '"PUT"',
        '"DELETE"',
        '"/approve"',
        '"/reject"',
        '"/execute"',
        "/execute",
        "tool runner frontend",
        "AIAgent",
        "HermesRuntimeAdapter",
        "/mark-3/hermes-runtime/execute-read",
        "/mark-3/hermes-runtime/sessions",
        "/tasks",
        "/missions",
    ):
        assert forbidden not in content

    for forbidden in (
        'method: "POST"',
        'method: "PUT"',
        'method: "DELETE"',
        "createCheckout",
        "checkout.sessions.create",
        "paymentIntent",
        "invoice.create",
        "moveMoney",
        "transfer.create",
        "fakeRevenue",
        "fakeCost",
        "fakeRoi",
    ):
        assert forbidden not in content


def test_jarvis_mission_control_preview_has_no_submit_or_sensor_handler():
    content = _read(JARVIS_COMPONENT_DIR / "JarvisDebugDrawer.tsx")

    for required in (
        "Control de Misión",
        "Preparar preview",
        "Enviar a JARVIS",
        'aria-disabled="true"',
        "placeholder={valueText(missionControl.sample_command, sampleMissionCommand)}",
    ):
        assert required in content

    for forbidden in (
        "<form",
        "onSubmit",
        "handleSubmit",
        "submitMission",
        "createMission",
        "runMission",
        "dispatchHermes",
        "startListening",
        "startRecording",
        "listenForWakeWord",
        "navigator.mediaDevices",
        ".getUserMedia(",
        "getUserMedia(",
    ):
        assert forbidden not in content


def test_approval_controls_are_functional_but_backend_gated():
    content = _jarvis_sources()
    api_content = _read(API)

    for label in (
        "Crear preview",
        "Pedir approval",
        "Aprobar",
        "Rechazar",
        "Cancelar",
        "Aclarar",
        "Stop",
        "Dispatch gobernado",
        "Backend-gated",
        "no Hermes directo",
    ):
        assert label in content

    assert "onClick={() => onTabChange(tab.id)}" in content
    for endpoint in (
        "/mark-3/execution/preview",
        "/mark-3/execution/request-approval",
        "/mark-3/execution/approval-decision",
        "/mark-3/execution/dispatch",
        "/mark-3/execution/cancel",
        "/mark-3/execution/stop",
    ):
        assert endpoint in api_content
    for forbidden in (
        "mark_3_hermes_runtime_bridge.execute",
        "HermesRuntimeAdapter",
        "callHermes",
        "dispatchHermes",
        '"/execute"',
    ):
        assert forbidden not in content + api_content
    assert content.count("disabled") >= 5


def test_no_new_dangerous_jarvis_dashboard_backend_endpoints_exist():
    app = create_app(adapter_factory=lambda: pytest.fail("Hermes must not be called"))
    routes = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }

    for route in (
        ("/jarvis/execute", "POST"),
        ("/jarvis/approve", "POST"),
        ("/jarvis/reject", "POST"),
        ("/jarvis/hermes/execute", "POST"),
        ("/command-center/execute", "POST"),
        ("/command-center/approve", "POST"),
        ("/command-center/reject", "POST"),
        ("/hermes/execute", "POST"),
        ("/mobile/hermes/execute", "POST"),
        ("/camera/start", "POST"),
        ("/microphone/start", "POST"),
    ):
        assert route not in routes
