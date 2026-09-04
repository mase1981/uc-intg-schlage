"""Configuration dataclass and manager for the Schlage integration.

One config entry represents a single Schlage account. The locks discovered
during setup are cached so entities can be built without a live cloud connection
(reboot-safe); live values flow in through the device on connect.
"""

from dataclasses import dataclass, field

from ucapi_framework import BaseConfigManager


@dataclass
class SchlageConfig:
    """Configuration for a single Schlage account."""

    identifier: str = ""
    name: str = ""
    username: str = ""
    password: str = ""
    locks: list[dict] = field(default_factory=list)


class SchlageConfigManager(BaseConfigManager[SchlageConfig]):
    """Config manager bound to :class:`SchlageConfig`."""
