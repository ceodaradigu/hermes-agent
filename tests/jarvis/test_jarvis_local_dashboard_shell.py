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
    ):
        assert text in content

    for state in (
        "offline",
        "online",
        "preview",
        "listening_wake_word",
        "listening_command",
        "thinking",
        "speaking",
        "approval_required",
        "hermes_executing",
        "paused",
        "blocked",
        "kill_switch",
    ):
        assert state in content


def test_jarvis_dashboard_shell_does_not_use_browser_sensor_apis_or_recording():
    content = _read(PAGE)

    for forbidden in (
        "getUserMedia",
        "mediaDevices",
        "MediaRecorder",
        "AudioContext",
        "webkitAudioContext",
        "navigator.permissions",
        "recordedChunks",
    ):
        assert forbidden not in content


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

    assert "onClick" not in content
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
