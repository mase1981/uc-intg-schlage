"""Schlage sensors - battery, lock status, last operated by, firmware."""

import logging

from ucapi import sensor
from ucapi_framework import SensorEntity

from uc_intg_schlage.config import SchlageConfig
from uc_intg_schlage.const import (
    STATE_ON,
    STATUS_JAMMED,
    STATUS_LOCKED,
    STATUS_UNKNOWN,
    STATUS_UNLOCKED,
)
from uc_intg_schlage.device import SchlageDevice

_LOG = logging.getLogger(__name__)


class BatterySensor(SensorEntity):
    """Lock battery level."""

    def __init__(self, device_config: SchlageConfig, device: SchlageDevice, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        super().__init__(
            f"sensor.{device_config.identifier}.{self._device_id}.battery",
            f"{meta.get('name', 'Lock')} Battery",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: -1},
            device_class=sensor.DeviceClasses.BATTERY,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        lock = self._device.get_lock(self._device_id)
        if self._device.state != STATE_ON or lock is None:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        level = getattr(lock, "battery_level", None)
        if level is None:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update({sensor.Attributes.STATE: sensor.States.ON, sensor.Attributes.VALUE: int(level)})


class StatusSensor(SensorEntity):
    """Lock status - Locked, Unlocked, or Jammed."""

    def __init__(self, device_config: SchlageConfig, device: SchlageDevice, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        super().__init__(
            f"sensor.{device_config.identifier}.{self._device_id}.status",
            f"{meta.get('name', 'Lock')} Status",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        lock = self._device.get_lock(self._device_id)
        if self._device.state != STATE_ON or lock is None or not getattr(lock, "connected", False):
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        if getattr(lock, "is_jammed", False):
            value = STATUS_JAMMED
        else:
            is_locked = getattr(lock, "is_locked", None)
            value = STATUS_UNKNOWN if is_locked is None else (STATUS_LOCKED if is_locked else STATUS_UNLOCKED)
        self.update({sensor.Attributes.STATE: sensor.States.ON, sensor.Attributes.VALUE: value})


class ChangedBySensor(SensorEntity):
    """Who or what last operated the lock."""

    def __init__(self, device_config: SchlageConfig, device: SchlageDevice, meta: dict) -> None:
        self._device = device
        self._device_id = meta["device_id"]
        super().__init__(
            f"sensor.{device_config.identifier}.{self._device_id}.changed_by",
            f"{meta.get('name', 'Lock')} Last Operated By",
            [],
            {sensor.Attributes.STATE: sensor.States.UNKNOWN, sensor.Attributes.VALUE: ""},
            device_class=sensor.DeviceClasses.CUSTOM,
            options={sensor.Options.CUSTOM_UNIT: ""},
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state != STATE_ON:
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        self.update(
            {
                sensor.Attributes.STATE: sensor.States.ON,
                sensor.Attributes.VALUE: self._device.last_changed_by(self._device_id) or "Unknown",
            }
        )


def create_sensors(device_config: SchlageConfig, device: SchlageDevice) -> list[SensorEntity]:
    entities: list[SensorEntity] = []
    for meta in device_config.locks:
        entities.append(BatterySensor(device_config, device, meta))
        entities.append(StatusSensor(device_config, device, meta))
        entities.append(ChangedBySensor(device_config, device, meta))
    return entities
