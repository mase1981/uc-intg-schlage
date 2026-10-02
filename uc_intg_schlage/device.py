"""Schlage device - one cloud account exposing all its locks."""

import asyncio
import logging
import time
from typing import Any

from ucapi_framework import DeviceEvents, PollingDevice

from uc_intg_schlage.client import SchlageClient
from uc_intg_schlage.config import SchlageConfig
from uc_intg_schlage.const import POLL_INTERVAL, STATE_ON, STATE_UNAVAILABLE

_LOG = logging.getLogger(__name__)

# Cloud login retry backoff (seconds). Retrying a failed login on every poll
# could get the account rate-limited, so the wait doubles up to 15 minutes.
_LOGIN_RETRY_MIN = 30
_LOGIN_RETRY_MAX = 900


class SchlageDevice(PollingDevice):
    """One Schlage account."""

    def __init__(self, device_config: SchlageConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=POLL_INTERVAL, **kwargs)
        self._device_config = device_config
        self._client: SchlageClient | None = None
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._state: str = STATE_UNAVAILABLE
        self._locks: dict[str, Any] = {}
        self._changed_by: dict[str, str] = {}
        self._login_retry_delay: float = _LOGIN_RETRY_MIN
        self._next_login_at: float = 0.0

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return "schlage-cloud"

    @property
    def log_id(self) -> str:
        return f"{self.name} (Schlage)"

    @property
    def state(self) -> str:
        return self._state

    def get_lock(self, device_id: str) -> Any:
        return self._locks.get(device_id)

    def last_changed_by(self, device_id: str) -> str:
        return self._changed_by.get(device_id, "")

    async def establish_connection(self) -> SchlageClient | None:
        # Never raise when the cloud is unreachable: the framework does not retry
        # a failed connect, which would leave entities unavailable until the
        # Remote reconnects. Polling keeps running and logs in again instead.
        async with self._connect_lock:
            self._next_login_at = 0.0
            if not await self._ensure_client_locked():
                _LOG.warning("[%s] Schlage login failed, will keep retrying", self.log_id)
                self._state = STATE_UNAVAILABLE
                return self._client
            try:
                await self._load_locks()
                self._state = STATE_ON
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.warning("[%s] Initial lock query failed, will keep retrying: %s", self.log_id, err)
                self._state = STATE_UNAVAILABLE
            return self._client

    async def _ensure_client_locked(self) -> bool:
        """Log in if needed, with backoff. Caller MUST hold ``self._connect_lock``."""
        if self._client is not None:
            return True
        if time.monotonic() < self._next_login_at:
            return False
        client = SchlageClient(self._device_config.username, self._device_config.password)
        try:
            await client.connect()
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Login failed: %s", self.log_id, err)
            self._next_login_at = time.monotonic() + self._login_retry_delay
            self._login_retry_delay = min(self._login_retry_delay * 2, _LOGIN_RETRY_MAX)
            return False
        self._client = client
        self._login_retry_delay = _LOGIN_RETRY_MIN
        return True

    async def _load_locks(self) -> None:
        assert self._client is not None
        locks = await self._client.get_locks()
        self._locks = {lock.device_id: lock for lock in locks}
        for device_id, lock in self._locks.items():
            changed = await self._client.get_last_changed_by(lock)
            if changed:
                self._changed_by[device_id] = changed

    async def poll_device(self) -> None:
        try:
            async with self._connect_lock:
                if not await self._ensure_client_locked():
                    raise ConnectionError("Not logged in to Schlage")
                await self._load_locks()
            # A successful poll always restores availability after an error.
            self._state = STATE_ON
            self.push_update()
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Poll error: %s", self.log_id, err)
            if self._state != STATE_UNAVAILABLE:
                self._state = STATE_UNAVAILABLE
                self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def disconnect(self) -> None:
        async with self._connect_lock:
            if self._client is not None:
                self._client.close()
                self._client = None
        self._state = STATE_UNAVAILABLE
        await super().disconnect()

    async def _after_command(self, lock: Any) -> None:
        try:
            await self._client.refresh_lock(lock)
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.debug("[%s] Refresh after command failed: %s", self.log_id, err)
        self.push_update()

    async def lock(self, device_id: str) -> bool:
        lock = self.get_lock(device_id)
        if lock is None or self._client is None:
            return False
        await self._client.do_lock(lock)
        await self._after_command(lock)
        return True

    async def unlock(self, device_id: str) -> bool:
        lock = self.get_lock(device_id)
        if lock is None or self._client is None:
            return False
        await self._client.do_unlock(lock)
        await self._after_command(lock)
        return True

    async def set_beeper(self, device_id: str, enabled: bool) -> bool:
        lock = self.get_lock(device_id)
        if lock is None or self._client is None:
            return False
        await self._client.set_beeper(lock, enabled)
        await self._after_command(lock)
        return True

    async def set_lock_and_leave(self, device_id: str, enabled: bool) -> bool:
        lock = self.get_lock(device_id)
        if lock is None or self._client is None:
            return False
        await self._client.set_lock_and_leave(lock, enabled)
        await self._after_command(lock)
        return True

    async def set_auto_lock_time(self, device_id: str, seconds: int) -> bool:
        lock = self.get_lock(device_id)
        if lock is None or self._client is None:
            return False
        await self._client.set_auto_lock_time(lock, seconds)
        await self._after_command(lock)
        return True
