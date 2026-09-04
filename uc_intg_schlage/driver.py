"""Integration driver for Schlage accounts."""

from ucapi_framework import BaseIntegrationDriver

from uc_intg_schlage.config import SchlageConfig
from uc_intg_schlage.device import SchlageDevice
from uc_intg_schlage.select import create_selects
from uc_intg_schlage.sensor import create_sensors
from uc_intg_schlage.switch import create_switches


class SchlageDriver(BaseIntegrationDriver[SchlageDevice, SchlageConfig]):
    """Builds the entity set for each Schlage account."""

    def __init__(self) -> None:
        super().__init__(
            device_class=SchlageDevice,
            entity_classes=[
                create_switches,
                create_selects,
                create_sensors,
            ],
            driver_id="uc_intg_schlage",
        )
