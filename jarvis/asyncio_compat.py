"""AsyncIO runtime compatibility helpers for local JARVIS tests."""

from __future__ import annotations

import os
import socket
import sys
from typing import Any


def _socketpair_send_allowed() -> bool:
    try:
        read_socket, write_socket = socket.socketpair()
    except OSError:
        return False

    try:
        write_socket.setblocking(False)
        read_socket.setblocking(False)
        write_socket.send(b"\0")
        read_socket.recv(1)
        return True
    except OSError:
        return False
    finally:
        read_socket.close()
        write_socket.close()


class _PipeReader:
    def __init__(self, fd: int) -> None:
        self._fd = fd

    def fileno(self) -> int:
        return self._fd

    def recv(self, size: int) -> bytes:
        return os.read(self._fd, size)

    def close(self) -> None:
        os.close(self._fd)


class _PipeWriter:
    def __init__(self, fd: int) -> None:
        self._fd = fd

    def fileno(self) -> int:
        return self._fd

    def send(self, data: bytes) -> int:
        return os.write(self._fd, data)

    def close(self) -> None:
        os.close(self._fd)


def ensure_asyncio_self_pipe_compat() -> None:
    """Use an OS pipe when Unix socket self-wakeup is denied.

    Starlette's TestClient relies on AnyIO's blocking portal, which relies on
    ``asyncio.call_soon_threadsafe`` waking the loop via the selector self-pipe.
    Some sandboxed Linux runtimes deny ``socketpair().send()`` with EPERM while
    still permitting ``os.pipe()``. Python swallows that OSError in
    ``_write_to_self()``, leaving callers blocked forever. This compatibility
    hook only patches that detected runtime shape.
    """

    if not sys.platform.startswith("linux"):
        return
    if _socketpair_send_allowed():
        return

    try:
        import asyncio.unix_events as unix_events
    except ImportError:
        return

    loop_cls = unix_events._UnixSelectorEventLoop
    if getattr(loop_cls, "_jarvis_pipe_self_pipe", False):
        return

    def _make_self_pipe(self: Any) -> None:
        read_fd, write_fd = os.pipe()
        os.set_blocking(read_fd, False)
        os.set_blocking(write_fd, False)
        self._ssock = _PipeReader(read_fd)
        self._csock = _PipeWriter(write_fd)
        self._internal_fds += 1
        self._add_reader(self._ssock.fileno(), self._read_from_self)

    loop_cls._make_self_pipe = _make_self_pipe
    loop_cls._jarvis_pipe_self_pipe = True
