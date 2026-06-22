from __future__ import annotations

from urllib.parse import urlparse


BACKEND_HOST = "127.0.0.1"
FRONTEND_HOST = "127.0.0.1"
BACKEND_PORT = 9119
FRONTEND_PORT = 5173

BACKEND_BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
FRONTEND_BASE_URL = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"
JARVIS_FRONTEND_URL = f"{FRONTEND_BASE_URL}/jarvis"
MOBILE_FRONTEND_URL = f"{FRONTEND_BASE_URL}/mobile"


def frontend_url(path: str = "/jarvis", *, host: str = FRONTEND_HOST) -> str:
    route = str(path or "/").strip()
    if not route.startswith("/"):
        route = f"/{route}"
    return f"http://{host}:{FRONTEND_PORT}{route}"


def backend_url(path: str = "", *, host: str = BACKEND_HOST) -> str:
    route = str(path or "").strip()
    if route and not route.startswith("/"):
        route = f"/{route}"
    return f"http://{host}:{BACKEND_PORT}{route}"


def url_uses_frontend_port(raw: str) -> bool:
    parsed = urlparse(str(raw or ""))
    try:
        return parsed.port == FRONTEND_PORT
    except ValueError:
        return False
