from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Pattern


class PolicyDecision(str, Enum):
    ALLOWED = "allowed"
    REQUIRES_APPROVAL = "requires_approval"
    DENIED = "denied"


@dataclass(frozen=True)
class PolicyResult:
    decision: PolicyDecision
    reason: str


class PolicyEngine:
    """Deterministic regex-based policy classifier for JARVIS MVP."""

    _REQUIRES_APPROVAL_PATTERNS: tuple[Pattern[str], ...] = (
        re.compile(r"\b(usar|use)\s+(credenciales|credentials|token|api\s*key)\b", re.IGNORECASE),
        re.compile(r"\.env\b", re.IGNORECASE),
        re.compile(r"\b(cat|type|more|less)\s+\.env\b", re.IGNORECASE),
        re.compile(r"\b(abre|abrir|open|read|leer|muestra|show)\b.*\b(\.env|variables?\s+de\s+entorno|env\s*vars?|secretos|secrets?)\b", re.IGNORECASE),
        re.compile(r"\b(delete|del|rm|remove|erase|borrar)\b", re.IGNORECASE),
        re.compile(r"\b(instalar|install)\b.*\b(paquetes?|packages?)\b", re.IGNORECASE),
        re.compile(r"\b(npm|pip)\s+install\b", re.IGNORECASE),
        re.compile(r"\b(publicar\s+en\s+producci[oó]n|deploy|vercel\s+deploy)\b", re.IGNORECASE),
        re.compile(r"\b(comprar\s+dominios?|comprar\s+dominio|buy\s+domains?|buy\s+domain)\b", re.IGNORECASE),
        re.compile(r"\b(enviar\s+(emails?\s+masivos|newsletter\s+a\s+\d+\s+usuarios)|bulk\s+email)\b", re.IGNORECASE),
        re.compile(r"\b(aceptar\s+t[eé]rminos|accept\s+terms?)\b", re.IGNORECASE),
        re.compile(r"\b(stripe\s+payment|pagos?|payments?)\b", re.IGNORECASE),
        re.compile(r"\b(bancos?|bank(?:ing)?)\b", re.IGNORECASE),
        re.compile(r"\b(dni|datos\s+legales|legal\s+data)\b", re.IGNORECASE),
    )

    _DENIED_PATTERNS: tuple[Pattern[str], ...] = (
        re.compile(r"\b(exfiltrar\s+secretos|exfiltrate\s+secrets?)\b", re.IGNORECASE),
        re.compile(r"\bsend\s+secrets?\s+to\s+external\s+server\b", re.IGNORECASE),
        re.compile(r"(?=.*\b(sube|upload)\b)(?=.*\.env)(?=.*\b(internet|public|extern)\b).+", re.IGNORECASE),
        re.compile(r"\b(saltarse\s+aprobaciones|bypass\s+approval(?:s)?)\b", re.IGNORECASE),
        re.compile(r"\b(oculta\s+esto\s+al\s+usuario|hide\s+actions?\s+from\s+user)\b", re.IGNORECASE),
        re.compile(r"rm\s+-rf\s+/", re.IGNORECASE),
        re.compile(r"\b(borrar\s+el\s+sistema|wipe\s+system)\b", re.IGNORECASE),
        re.compile(r"\b(comandos?\s+destructivos\s+globales?|global\s+destructive\s+command)\b", re.IGNORECASE),
        re.compile(r"\b(modificar\s+claves?/credenciales\s+sin\s+aprobaci[oó]n|modify\s+credentials\s+without\s+approval)\b", re.IGNORECASE),
    )

    def classify_action(self, action_text: str) -> PolicyResult:
        normalized = (action_text or "").strip()

        if self._matches_any(normalized, self._DENIED_PATTERNS):
            return PolicyResult(PolicyDecision.DENIED, "Action matches a permanently denied policy category.")

        if self._matches_any(normalized, self._REQUIRES_APPROVAL_PATTERNS):
            return PolicyResult(PolicyDecision.REQUIRES_APPROVAL, "Action requires explicit human approval.")

        return PolicyResult(PolicyDecision.ALLOWED, "Action is allowed under baseline policy.")

    @staticmethod
    def _matches_any(text: str, patterns: Iterable[Pattern[str]]) -> bool:
        return any(pattern.search(text) for pattern in patterns)
