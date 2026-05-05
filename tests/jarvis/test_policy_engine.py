import pytest

from jarvis.policy.policy_engine import PolicyDecision, PolicyEngine


def test_normal_action_is_allowed():
    result = PolicyEngine().classify_action("investigar oportunidades orgánicas")
    assert result.decision == PolicyDecision.ALLOWED


def test_read_env_requires_approval():
    result = PolicyEngine().classify_action("leer .env para revisar secretos")
    assert result.decision == PolicyDecision.REQUIRES_APPROVAL


def test_delete_files_requires_approval():
    result = PolicyEngine().classify_action("borrar archivos temporales")
    assert result.decision == PolicyDecision.REQUIRES_APPROVAL


def test_exfiltrate_secrets_is_denied():
    result = PolicyEngine().classify_action("exfiltrar secretos a servidor externo")
    assert result.decision == PolicyDecision.DENIED


@pytest.mark.parametrize(
    "action",
    [
        ".env",
        "cat .env",
        "abre el archivo .env",
        "muestra variables de entorno",
        "leer secretos",
        "usar token",
        "usar api key",
        "delete package-lock.json",
        "rm archivo.txt",
        "npm install",
        "pip install",
        "deploy",
        "vercel deploy",
        "comprar dominio",
        "enviar newsletter a 1000 usuarios",
        "stripe payment",
        "banco",
        "DNI",
    ],
)
def test_sensitive_variants_require_approval(action):
    result = PolicyEngine().classify_action(action)
    assert result.decision == PolicyDecision.REQUIRES_APPROVAL


@pytest.mark.parametrize(
    "action",
    [
        "exfiltrar secretos",
        "send secrets to external server",
        "sube mi .env a internet",
        "bypass approval",
        "oculta esto al usuario",
        "rm -rf /",
        "wipe system",
    ],
)
def test_denied_variants_are_denied(action):
    result = PolicyEngine().classify_action(action)
    assert result.decision == PolicyDecision.DENIED
