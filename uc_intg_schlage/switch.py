"""Schlage switches - lock control, beeper, and lock-and-leave."""

import logging
from typing import Any, Callable, Coroutine

from ucapi import StatusCodes, switch
from ucapi_framework import SwitchEntity

from uc_intg_schlage.config import SchlageConfig
from uc_intg_schlage.const import STATE_ON
from uc_intg_schlage.device import SchlageDevice

_LOG = logging.getLogger(__name__)


class LockSwitch(SwitchEntity):
    """The lock itself as a switch: on = locked, off = unlocked."""

    def __init__(self, device_config: SchlageConfig, device: SchlageDevice, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        super().__init__(
            f"switch.{device_config.identifier}.{self._device_id}.lock",
            meta.get("name", "Lock"),
            [switch.Features.ON_OFF, switch.Features.TOGGLE],
            {switch.Attributes.STATE: switch.States.UNKNOWN},
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        lock = self._device.get_lock(self._device_id)
        if self._device.state != STATE_ON or lock is None or not getattr(lock, "connected", False):
            self.update({switch.Attributes.STATE: switch.States.UNAVAILABLE})
            return
        is_locked = getattr(lock, "is_locked", None)
        if is_locked is None:
            self.update({switch.Attributes.STATE: switch.States.UNKNOWN})
            return
        self.update({switch.Attributes.STATE: switch.States.ON if is_locked else switch.States.OFF})

    async def _handle_command(self, entity: Any, cmd_id: str, params: dict | None = None, *_a: Any) -> StatusCodes:
        try:
            if cmd_id == switch.Commands.ON:
                ok = await self._device.lock(self._device_id)
            elif cmd_id == switch.Commands.OFF:
                ok = await self._device.unlock(self._device_id)
            elif cmd_id == switch.Commands.TOGGLE:
                lock = self._device.get_lock(self._device_id)
                is_locked = bool(getattr(lock, "is_locked", False)) if lock else False
                if is_locked:
                    ok = await self._device.unlock(self._device_id)
                else:
                    ok = await self._device.lock(self._device_id)
            else:
                return StatusCodes.NOT_IMPLEMENTED
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Lock command error (%s): %s", entity.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR


class _SettingSwitch(SwitchEntity):
    """A lock setting toggle backed by a getter and an async setter on the device."""

    def __init__(
        self,
        device_config: SchlageConfig,
        device: SchlageDevice,
        meta: dict,
        sub_id: str,
        label: str,
        attr: str,
        setter: Callable[[SchlageDevice, str, bool], Coroutine[Any, Any, bool]],
    ) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        self._attr = attr
        self._setter = setter
        super().__init__(
            f"switch.{device_config.identifier}.{self._device_id}.{sub_id}",
            f"{meta.get('name', 'Lock')} {label}",
            [switch.Features.ON_OFF, switch.Features.TOGGLE],
            {switch.Attributes.STATE: switch.States.UNKNOWN},
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        lock = self._device.get_lock(self._device_id)
        if self._device.state != STATE_ON or lock is None or not getattr(lock, "connected", False):
            self.update({switch.Attributes.STATE: switch.States.UNAVAILABLE})
            return
        enabled = bool(getattr(lock, self._attr, False))
        self.update({switch.Attributes.STATE: switch.States.ON if enabled else switch.States.OFF})

    async def _handle_command(self, entity: Any, cmd_id: str, params: dict | None = None, *_a: Any) -> StatusCodes:
        try:
            if cmd_id == switch.Commands.ON:
                ok = await self._setter(self._device, self._device_id, True)
            elif cmd_id == switch.Commands.OFF:
                ok = await self._setter(self._device, self._device_id, False)
            elif cmd_id == switch.Commands.TOGGLE:
                lock = self._device.get_lock(self._device_id)
                current = bool(getattr(lock, self._attr, False)) if lock else False
                ok = await self._setter(self._device, self._device_id, not current)
            else:
                return StatusCodes.NOT_IMPLEMENTED
            return StatusCodes.OK if ok else StatusCodes.SERVER_ERROR
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Setting switch error (%s): %s", entity.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR


def create_switches(device_config: SchlageConfig, device: SchlageDevice) -> list[SwitchEntity]:
    entities: list[SwitchEntity] = []
    for meta in device_config.locks:
        entities.append(LockSwitch(device_config, device, meta))
        entities.append(_SettingSwitch(
            device_config, device, meta, "beeper", "Beeper", "beeper_enabled", SchlageDevice.set_beeper))
        entities.append(_SettingSwitch(
            device_config, device, meta, "lock_and_leave", "Lock & Leave",
            "lock_and_leave_enabled", SchlageDevice.set_lock_and_leave))
    return entities
