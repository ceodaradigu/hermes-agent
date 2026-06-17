from pathlib import Path

import pytest

from jarvis.api.app import create_app


PAGE = Path("web/src/pages/JarvisCommandCenterPage.tsx")
APP = Path("web/src/App.tsx")
API = Path("web/src/lib/api.ts")
VITE_CONFIG = Path("web/vite.config.ts")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_jarvis_dashboard_shell_file_and_local_route_exist():
    assert PAGE.exists()
    app_source = _read(APP)
    vite_source = _read(VITE_CONFIG)

    assert "JarvisCommandCenterPage" in app_source
    assert '{ id: "jarvis", label: "JARVIS"' in app_source
    assert '"/jarvis": "jarvis"' in app_source
    assert '"/mark-3": "http://127.0.0.1:9119"' in vite_source


def test_jarvis_dashboard_shell_contains_required_read_only_content():
    content = _read(PAGE)

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
        "No voice recording",
        "No camera capture",
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
        "No hay ejecución real que detener desde este panel",
        "No hay ejecución real que detener desde esta shell",
        "Preview-only: approval execution is not wired in this PR",
        "Leyenda de riesgo",
        "Nivel 0-1",
        "Nivel 5",
        "Readback / confirmación fuerte",
        "Cámara / Visión",
        "No se captura imagen ni vídeo en esta PR",
        "No se usa getUserMedia",
        "No hay proveedor externo de visión",
        "La visión futura requerirá permiso explícito y auditoría",
        "Mobile no ejecuta acciones",
        "Approvals reales desde móvil quedan future-gated",
        "No se guardan credenciales ni tokens",
    ):
        assert text in content

    for state in (
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
    content = _read(PAGE)

    for text in (
        "Núcleo de Voz JARVIS",
        "No estoy escuchando ni grabando audio",
        "Subtítulos preview",
        "Subtítulos preview - sin TTS real, sin STT real, sin provider externo.",
        "Política wake word",
        "Frases soportadas futuras: Hola Jarvis, Jarvis.",
        "La wake phrase nunca aprueba acciones",
        "La wake phrase no ejecuta acciones",
        "Las acciones críticas requieren readback y confirmación fuerte",
        "Privacidad voz",
        "micrófono: disabled",
        "grabación: false",
        "audio bruto almacenado: false",
        "proveedor externo",
        "background listening",
        "voice approval",
        "La voz puede preparar una intención futura",
        "Si requiere aprobación, aparecerá en Approval Console",
        "Frontend/voice no llama Hermes directamente",
        "Kill Switch voz",
        "En esta PR no hay audio real que parar",
        "Una integración futura deberá cortar escucha, TTS y ejecución gobernada",
    ):
        assert text in content


def test_jarvis_dashboard_shell_contains_wake_word_local_safe_flow_contract():
    content = _read(PAGE)

    for text in (
        "Wake Word Local Safe Flow",
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
        "no micrófono",
        "no grabación",
        "no STT",
        "no TTS real",
        "no provider externo",
        "no background listener",
        "no Hermes dispatch",
        "no auto execute",
    ):
        assert text in content


def test_jarvis_dashboard_shell_does_not_use_browser_sensor_apis_or_recording():
    content = _read(PAGE)

    for forbidden in (
        "navigator.mediaDevices",
        ".getUserMedia(",
        "getUserMedia(",
        "await getUserMedia",
        "mediaDevices",
        "MediaStream",
        "MediaRecorder",
        "AudioContext",
        "webkitAudioContext",
        "navigator.permissions",
        "recordedChunks",
        "startListening",
        "stopListening",
        "startRecording",
        "stopRecording",
        "recordAudio",
        "listenForWakeWord",
        "wakeWordListener",
        "captureImage",
        "captureFrame",
        "takeSnapshot",
        "saveSnapshot",
        "startCamera",
        "stopCamera",
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

    assert "No se usa getUserMedia." in content


def test_jarvis_dashboard_shell_contains_camera_vision_privacy_panel_contract():
    content = _read(PAGE)

    for text in (
        "Cámara / Visión",
        "preview-only",
        "La cámara no graba por defecto.",
        "La visión solo se activa con permiso explícito.",
        "Estado actual",
        "permiso solicitado",
        "recording",
        "streaming",
        "snapshot",
        "vision analysis",
        "provider externo",
        "Privacidad",
        "no camera activation",
        "no getUserMedia",
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
        "No se captura imagen ni vídeo en esta PR.",
        "No se usa getUserMedia.",
        "No hay proveedor externo de visión.",
        "La visión futura requerirá permiso explícito y auditoría.",
    ):
        assert text in content


def test_jarvis_dashboard_shell_contains_mobile_companion_preview_contract():
    content = _read(PAGE)

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
    content = _read(PAGE)

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
        "Pilot read-only",
        "Frontend Pilot / Hardening",
        "El dashboard mira, no toca.",
        "No POST/PUT/DELETE.",
        "No execute.",
        "No sensores.",
        "Dependency hardening queda para una PR separada.",
        "/jarvis",
        "/mark-3/dashboard/status",
        "finance_roi_visible",
        "product_builder_visible",
        "no_frontend_execute",
        "no_sensor_activation",
        "npm audit vulnerabilities observed",
        "full pytest required before merge",
    ):
        assert text in content


def test_jarvis_dashboard_shell_contains_visual_command_center_pilot_contract():
    content = _read(PAGE)

    for text in (
        "Visual Command Center Pilot",
        "/jarvis",
        "/mark-3/dashboard/status",
        "read-only pilot",
        "El dashboard mira, no toca",
        "No se ejecuta Hermes desde el frontend",
        "No se activan sensores",
        "No hay approvals reales en esta fase",
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
        "no_get_user_media",
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
        "modo preview/read-only",
        "max-h-[64vh] overflow-auto",
    ):
        assert text in content

    for forbidden in (
        'method: "POST"',
        'method: "PUT"',
        'method: "DELETE"',
        '"/execute"',
        "/execute",
        "getUserMedia(",
        ".getUserMedia(",
        "MediaRecorder",
        "checkout.sessions.create",
        "createCheckout",
        "paymentIntent",
        "moveMoney",
        "transfer.create",
    ):
        assert forbidden not in content


def test_jarvis_dashboard_shell_contains_presence_ui_local_system_contract():
    content = _read(PAGE)

    for text in (
        "Presence UI",
        "Local System Contract",
        "JARVIS Presence UI + Local System Contract",
        "JARVIS runtime/daemon local es el sistema",
        "/jarvis es solo la interfaz visual",
        "móvil y VPS serán clientes/puentes futuros",
        "frontend no ejecuta directamente Hermes",
        "voz/cámara reales vendrán en PRs posteriores",
        "idle/calmado",
        "escuchando",
        "pensando",
        "hablando",
        "alerta/riesgo",
        "smart bar",
        "barra inteligente inferior",
        "transcripción temporal preview",
        "respuesta temporal preview",
        "Historial plegado / folded history",
        "camera placeholder",
        "Camera Placeholder",
        "movible/ampliable",
        'data-testid="jarvis-smart-bar"',
        'data-testid="jarvis-camera-placeholder"',
        'data-testid="jarvis-folded-history"',
        'data-testid="jarvis-local-system-contract"',
    ):
        assert text in content


def test_jarvis_dashboard_shell_does_not_call_hermes_or_runtime_from_frontend():
    content = _read(PAGE)
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
    content = _read(PAGE)

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


def test_approval_controls_are_preview_only_and_not_functional():
    content = _read(PAGE)

    for label in (
        "Aprobar",
        "Rechazar",
        "Modificar alcance",
        "Pedir explicación",
        "preview-only",
        'aria-disabled="true"',
    ):
        assert label in content

    assert "onClick={() => setActiveTab(tab.id)}" in content
    for forbidden in (
        "onClick={approve",
        "onClick={reject",
        "onClick={execute",
        "onClick={dispatch",
        "onClick={start",
        "onClick={stop",
        "onClick={() => approve",
        "onClick={() => reject",
        "onClick={() => execute",
        "onClick={() => dispatch",
        "onClick={() => start",
        "onClick={() => stop",
    ):
        assert forbidden not in content
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
