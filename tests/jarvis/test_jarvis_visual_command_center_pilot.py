from pathlib import Path


DOC = Path("docs/jarvis-visual-command-center-pilot.md")


def test_visual_command_center_pilot_runbook_exists_and_documents_read_only_scope():
    assert DOC.exists()
    content = DOC.read_text(encoding="utf-8")
    serialized = content.lower()

    for text in (
        "/jarvis",
        "/mark-3/dashboard/status",
        "read-only",
        "no hermes execution",
        "no sensors",
        "no fake metrics",
        "dependency hardening separate pr",
    ):
        assert text in serialized


def test_visual_command_center_pilot_runbook_documents_manual_and_safety_checklists():
    content = DOC.read_text(encoding="utf-8").lower()

    for text in (
        "que valida este piloto",
        "que no valida",
        "como arrancar backend",
        "como abrir `/jarvis`",
        "checklist manual",
        "checklist de seguridad",
        "criterio de exito",
        "criterio de fallo",
        "findings que deben abrir pr",
        "fuera de alcance",
        "approvals reales",
        "ejecucion hermes",
        "voz real",
        "camara real",
        "movil real",
        "dinero, deploy, email o credenciales",
    ):
        assert text in content
