from __future__ import annotations

import re
from typing import Any, Iterable, List

from jarvis.approval_audit import redact_sensitive_data


DEFENSIVE_FIELD_NAMES = {
    "assumptions",
    "audit",
    "audit_summary",
    "blocked_actions",
    "blocked_reasons",
    "constraints",
    "disallowed_tools",
    "evidence_required",
    "expected_evidence",
    "failure_criteria",
    "guardrails",
    "invariants",
    "known_constraints",
    "legal_safety_review",
    "limitations",
    "limits",
    "missing_requirements",
    "no_auto_actions",
    "non_goals",
    "out_of_scope",
    "policy",
    "prohibited_tools",
    "reproducibility_checklist",
    "risks",
    "rollback_or_stop_plan",
    "rollback_plan",
    "stop_conditions",
    "stop_plan",
    "success_criteria",
    "trust_requirements",
    "unknowns",
}

_FALSEY_STRINGS = {"", "0", "false", "no", "n", "off", "none", "null"}
_SAFE_FALSE_KEY_MARKERS = (
    "account_access",
    "authorization",
    "background_worker",
    "calendar",
    "checkout",
    "credential",
    "deploy",
    "email",
    "env",
    "execute",
    "external",
    "github",
    "gmail",
    "identity",
    "install",
    "money",
    "network",
    "password",
    "payment",
    "production",
    "provider",
    "publish",
    "schedule",
    "secret",
    "send",
    "session",
    "stripe",
    "token",
    "web",
    "worker",
)
_NEGATION_RE = re.compile(
    r"(?:^|\b)(?:"
    r"no|not|without|do\s+not|don't|never|avoid|deny|denies|block|blocked|"
    r"prohibit|prohibited|disallow|disallowed|forbid|forbidden|must\s+not|"
    r"should\s+not|cannot|can't|stop\s+if|stop\s+when|stop\s+before|"
    r"sin|evitar|bloquear|denegar|prohibir|no\s+usar|no\s+leer"
    r")\b[\w\s./:-]{0,45}$",
    re.IGNORECASE,
)
_SAFE_SUFFIX_RE = re.compile(
    r"^\s*(?:false|is\s+false|are\s+false|requested\s+false|"
    r"is\s+blocked|are\s+blocked|blocked|denied|prohibited|disallowed|"
    r"not\s+requested|not\s+allowed|must\s+stop)\b",
    re.IGNORECASE,
)
_SAFE_PREFIX_RE = re.compile(
    r"(?:^|[\s,;:([{/])(?:no|non|without|sin)(?:[_\-\s/]+[\w./:-]+){0,6}[_\-\s/]+$",
    re.IGNORECASE,
)
_STOP_CONDITION_RE = re.compile(
    r"(?:^|\b)(?:"
    r"stop(?:\s+conditions?)?|stop\s+if|stop\s+when|stop\s+on|stop\s+before|"
    r"halt\s+if|halt\s+when|abort\s+if|abort\s+when|"
    r"prohibited[_\s-]*tools?|prohibited[_\s-]*actions?|"
    r"forbidden[_\s-]*tools?|disallowed[_\s-]*tools?|blocked[_\s-]*actions?|"
    r"constraints?|guardrails?|limits?|out[_\s-]*of[_\s-]*scope|non[_\s-]*goals?|"
    r"any\s+action\s+(?:requests?|attempts?|requires?|uses?|reads?|accesses?|claims?)|"
    r"any\s+result\s+(?:claims?|reports?|asserts?)|"
    r"any\s+output\s+(?:claims?|reports?|asserts?|attempts?)|"
    r"si\s+cualquier\s+accion|si\s+alguna\s+accion|"
    r"cualquier\s+accion\s+(?:pide|solicita|intenta|usa|lee|accede|afirma)|"
    r"cualquier\s+resultado\s+(?:afirma|declara|finge)"
    r")\b",
    re.IGNORECASE,
)
_ACTION_TRANSITION_RE = re.compile(r"\b(?:then|but|however|anyway|now|please|go\s+ahead)\b", re.IGNORECASE)
_UNAUTHORIZED_ACTION_RE = re.compile(
    r"\b(?:access|login|log\s+in|enter|use|acceder|entrar|usar)\b"
    r"[\w\s./:-]{0,60}\b(?:without\s+authorization|without\s+authorisation|sin\s+autorizaci[oó]n)\b",
    re.IGNORECASE,
)
_SECRET_VALUE_RE = re.compile(
    r"(?i)\b(?:api[_ -]?key|apikey|authorization|bearer|credential|credentials|"
    r"password|private[_ -]?key|privatekey|secret|token)\b['\"]?\s*[:=]"
    r"|\bbearer\s+[A-Za-z0-9._~+/=-]{6,}"
)


def redact_mark_3_payload(value: Any) -> tuple[Any, List[str]]:
    """Redact real secrets without treating explicit false safety flags as secrets."""

    safe, redacted = redact_sensitive_data(value)
    kept: List[str] = []
    for path in redacted:
        original = _get_path(value, path)
        if _is_safe_false_path(path, original):
            _set_path(safe, path, original)
        else:
            kept.append(path)
    safe = _restore_defensive_strings(value, safe)
    return safe, kept


def payload_text(values: Any, *, ignored_fields: Iterable[str] = DEFENSIVE_FIELD_NAMES) -> str:
    return " ".join(payload_text_segments(values, ignored_fields=ignored_fields)).lower()


def payload_text_segments(values: Any, *, ignored_fields: Iterable[str] = DEFENSIVE_FIELD_NAMES) -> List[str]:
    ignored = {_normalize_key(item) for item in ignored_fields}
    return [
        segment
        for segment in _segments(values, ignored_fields=ignored, current_key="")
        if segment
    ]


def payload_has_actionable_marker(
    values: Any,
    markers: Iterable[str],
    *,
    ignored_fields: Iterable[str] = DEFENSIVE_FIELD_NAMES,
) -> bool:
    return any(
        contains_actionable_marker(segment, markers)
        for segment in payload_text_segments(values, ignored_fields=ignored_fields)
    )


def contains_actionable_marker(text: str, markers: Iterable[str]) -> bool:
    lowered = _clean_text(text).lower()
    if not lowered:
        return False
    normalized_markers = tuple(_clean_text(marker).lower() for marker in markers if _clean_text(marker))
    for marker in normalized_markers:
        start = 0
        while True:
            index = lowered.find(marker, start)
            if index < 0:
                break
            if _marker_has_boundaries(lowered, index, marker) and not _marker_is_defensive(lowered, index, marker):
                return True
            start = index + max(1, len(marker))
    return False


def actionable_markers(text: str, markers: Iterable[str]) -> List[str]:
    return [
        marker
        for marker in markers
        if contains_actionable_marker(text, (marker,))
    ]


def _segments(value: Any, *, ignored_fields: set[str], current_key: str) -> List[str]:
    if isinstance(value, dict):
        result: List[str] = []
        for key, item in value.items():
            key_text = _normalize_key(key)
            if key_text in ignored_fields:
                continue
            if _is_safe_false_path(str(key), item):
                continue
            result.extend(_segments(item, ignored_fields=ignored_fields, current_key=key_text))
        return result
    if isinstance(value, (list, tuple, set)):
        result: List[str] = []
        for item in value:
            result.extend(_segments(item, ignored_fields=ignored_fields, current_key=current_key))
        return result
    if _is_explicit_false(value) and any(marker in current_key for marker in _SAFE_FALSE_KEY_MARKERS):
        return []
    text = _clean_text(value)
    return [text] if text else []


def _marker_is_defensive(text: str, index: int, marker: str) -> bool:
    statement_start = max(text.rfind("\n", 0, index), text.rfind(";", 0, index)) + 1
    line_start = max(statement_start - 1, text.rfind(",", 0, index)) + 1
    line_end_candidates = [pos for pos in (text.find("\n", index), text.find(";", index), text.find(",", index)) if pos >= 0]
    line_end = min(line_end_candidates) if line_end_candidates else len(text)
    line = text[line_start:line_end]
    if marker in {"authorization", "authorisation", "unauthorized", "unauthorised", "sin autorizacion", "sin autorización"}:
        if _UNAUTHORIZED_ACTION_RE.search(line):
            return False
    before = text[max(line_start, index - 70):index]
    after = text[index + len(marker): min(line_end, index + len(marker) + 70)]
    statement_before = text[statement_start:index]
    return bool(
        _SAFE_PREFIX_RE.search(before)
        or _NEGATION_RE.search(before)
        or _SAFE_SUFFIX_RE.search(after)
        or _STOP_CONDITION_RE.search(line[: index - line_start])
        or (
            _STOP_CONDITION_RE.search(statement_before)
            and not _ACTION_TRANSITION_RE.search(before)
        )
    )


def _marker_has_boundaries(text: str, index: int, marker: str) -> bool:
    if not marker:
        return False
    before = text[index - 1] if index > 0 else ""
    after_index = index + len(marker)
    after = text[after_index] if after_index < len(text) else ""
    if marker[0].isalnum() and (before.isalnum() or before == "_"):
        return False
    if marker[-1].isalnum() and (after.isalnum() or after == "_"):
        return False
    return True


def _restore_defensive_strings(original: Any, safe: Any) -> Any:
    if isinstance(original, dict) and isinstance(safe, dict):
        return {
            key: _restore_defensive_strings(original.get(key), safe.get(key))
            for key in safe
        }
    if isinstance(original, list) and isinstance(safe, list):
        return [
            _restore_defensive_strings(original[index], item) if index < len(original) else item
            for index, item in enumerate(safe)
        ]
    if safe == "[redacted sensitive text]" and isinstance(original, str):
        text = _clean_text(original)
        if text and not _SECRET_VALUE_RE.search(text) and _looks_defensive_sensitive_text(text):
            return text
    return safe


def _looks_defensive_sensitive_text(text: str) -> bool:
    sensitive_markers = (
        ".env",
        "api key",
        "api-key",
        "api_key",
        "apikey",
        "authorization:",
        "bearer ",
        "credential",
        "credentials",
        "password",
        "private key",
        "private-key",
        "private_key",
        "privatekey",
        "secret",
        "token",
    )
    return any(marker in text.lower() for marker in sensitive_markers) and not contains_actionable_marker(
        text,
        sensitive_markers,
    )


def _is_safe_false_path(path: str, value: Any) -> bool:
    normalized = _normalize_key(path)
    return _is_explicit_false(value) and any(marker in normalized for marker in _SAFE_FALSE_KEY_MARKERS)


def _is_explicit_false(value: Any) -> bool:
    if value is False or value is None:
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value == 0
    if isinstance(value, str):
        return value.strip().lower() in _FALSEY_STRINGS
    return False


def _get_path(value: Any, path: str) -> Any:
    current = value
    for token in _path_tokens(path):
        try:
            if isinstance(token, int):
                current = current[token]
            else:
                current = current[token]
        except (KeyError, IndexError, TypeError):
            return None
    return current


def _set_path(value: Any, path: str, replacement: Any) -> None:
    current = value
    tokens = _path_tokens(path)
    for token in tokens[:-1]:
        try:
            current = current[token]
        except (KeyError, IndexError, TypeError):
            return
    if not tokens:
        return
    last = tokens[-1]
    try:
        current[last] = replacement
    except (KeyError, IndexError, TypeError):
        return


def _path_tokens(path: str) -> List[Any]:
    tokens: List[Any] = []
    for part in path.split("."):
        if not part:
            continue
        head = part.split("[", 1)[0]
        if head:
            tokens.append(head)
        for index in re.findall(r"\[(\d+)\]", part):
            tokens.append(int(index))
    return tokens


def _normalize_key(value: Any) -> str:
    return str(value or "").lower().replace("-", "_").replace(" ", "_")


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())
