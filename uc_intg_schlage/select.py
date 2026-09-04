"""Schlage auto-lock-time selector."""

import logging
from typing import Any

from ucapi import StatusCodes, select
from ucapi_framework import SelectEntity

from uc_intg_schlage.config import SchlageConfig
from uc_intg_schlage.const import AUTO_LOCK_PRESETS, STATE_ON
from uc_intg_schlage.device import SchlageDevice

_LOG = logging.getLogger(__name__)

_SECONDS_TO_LABEL = {secs: label for secs, label in AUTO_LOCK_PRESETS}
_LABEL_TO_SECONDS = {label: secs for secs, label in AUTO_LOCK_PRESETS}
_PRESET_LABELS = [label for _secs, label in AUTO_LOCK_PRESETS]


def _label_for(seconds: int) -> str:
    return _SECONDS_TO_LABEL.get(seconds, f"{seconds} seconds")


class AutoLockSelect(SelectEntity):
    """Sets the lock's auto-lock delay."""

    def __init__(self, device_config: SchlageConfig, device: SchlageDevice, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        super().__init__(
            f"select.{device_config.identifier}.{self._device_id}.auto_lock",
            f"{meta.get('name', 'Lock')} Auto-Lock",
            {
                select.Attributes.STATE: select.States.UNKNOWN,
                select.Attributes.OPTIONS: [],
                select.Attributes.CURRENT_OPTION: "",
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        lock = self._device.get_lock(self._device_id)
        if self._device.state != STATE_ON or lock is None or not getattr(lock, "connected", False):
            self.update({select.Attributes.STATE: select.States.UNAVAILABLE})
            return
        current_seconds = int(getattr(lock, "auto_lock_time", 0) or 0)
        current_label = _label_for(current_seconds)
        options = list(_PRESET_LABELS)
        if current_label not in options:
            options.append(current_label)
        self.update(
            {
                select.Attributes.STATE: select.States.ON,
                select.Attributes.OPTIONS: options,
                select.Attributes.CURRENT_OPTION: current_label,
            }
        )

    async def _handle_command(self, entity: Any, cmd_id: str, params: dict | None = None, *_a: Any) -> StatusCodes:
        if cmd_id == select.Commands.SELECT_OPTION:
            option = params.get("option", "") if params else ""
            seconds = _LABEL_TO_SECONDS.get(option)
            if seconds is None:
                return StatusCodes.BAD_REQUEST
            try:
                if await self._device.set_auto_lock_time(self._device_id, seconds):
                    return StatusCodes.OK
                return StatusCodes.SERVER_ERROR
            except Exception as err:  # pylint: disable=broad-exception-caught
                _LOG.error("[%s] Auto-lock select error: %s", entity.id, err)
                return StatusCodes.SERVER_ERROR
        return StatusCodes.NOT_IMPLEMENTED


def create_selects(device_config: SchlageConfig, device: SchlageDevice) -> list[SelectEntity]:
    return [AutoLockSelect(device_config, device, meta) for meta in device_config.locks]
