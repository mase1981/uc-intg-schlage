"""Synchronous Schlage cloud client wrapped for asyncio.

The :mod:`pyschlage` library is fully synchronous (requests + AWS Cognito), so
every call is dispatched to a worker thread with ``asyncio.to_thread`` to avoid
blocking the integration's event loop.
"""

import asyncio
import logging
from typing import Any

import pyschlage

_LOG = logging.getLogger(__name__)


class SchlageClient:
    """Cloud client for one Schlage account."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username.lower()
        self._password = password
        self._schlage: pyschlage.Schlage | None = None

    @property
    def is_connected(self) -> bool:
        return self._schlage is not None

    def _login(self) -> pyschlage.Schlage:
        auth = pyschlage.Auth(self._username, self._password)
        auth.authenticate()
        return pyschlage.Schlage(auth)

    async def connect(self) -> None:
        self._schlage = await asyncio.to_thread(self._login)

    async def get_locks(self) -> list[Any]:
        if self._schlage is None:
            raise ConnectionError("Schlage client is not connected")
        return await asyncio.to_thread(self._schlage.locks)

    async def refresh_lock(self, lock: Any) -> None:
        await asyncio.to_thread(lock.refresh)

    async def get_last_changed_by(self, lock: Any) -> str | None:
        def _read() -> str | None:
            try:
                return lock.last_changed_by()
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.debug("last_changed_by failed: %s", err)
                return None

        return await asyncio.to_thread(_read)

    async def do_lock(self, lock: Any) -> None:
        await asyncio.to_thread(lock.lock)

    async def do_unlock(self, lock: Any) -> None:
        await asyncio.to_thread(lock.unlock)

    async def set_beeper(self, lock: Any, enabled: bool) -> None:
        await asyncio.to_thread(lock.set_beeper, enabled)

    async def set_lock_and_leave(self, lock: Any, enabled: bool) -> None:
        await asyncio.to_thread(lock.set_lock_and_leave, enabled)

    async def set_auto_lock_time(self, lock: Any, seconds: int) -> None:
        await asyncio.to_thread(lock.set_auto_lock_time, seconds)

    def close(self) -> None:
        self._schlage = None
