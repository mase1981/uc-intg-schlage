"""Setup flow: log in to a Schlage account and cache its locks."""

import logging
import re
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_schlage.client import SchlageClient
from uc_intg_schlage.config import SchlageConfig

_LOG = logging.getLogger(__name__)


class SchlageSetupFlow(BaseSetupFlow[SchlageConfig]):
    """Collect Schlage account credentials, validate, and store discovered locks."""

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "Schlage Account"},
            [
                {
                    "id": "info",
                    "label": {"en": "Schlage Account"},
                    "field": {"label": {"value": {"en": (
                        "Enter the username (email) and password for your Schlage Home account "
                        "(the same credentials you use in the Schlage Home app). All locks on the "
                        "account will be added."
                    )}}},
                },
                {"id": "username", "label": {"en": "Username (email)"}, "field": {"text": {"value": ""}}},
                {"id": "password", "label": {"en": "Password"}, "field": {"password": {"value": ""}}},
            ],
        )

    async def query_device(self, input_values: dict[str, Any]) -> SchlageConfig:
        username = input_values.get("username", "").strip()
        password = input_values.get("password", "").strip()
        if not username:
            raise ValueError("Username is required")
        if not password:
            raise ValueError("Password is required")

        client = SchlageClient(username, password)
        try:
            await client.connect()
            locks = await client.get_locks()
        except Exception as err:  # pylint: disable=broad-exception-caught
            raise ValueError(
                f"Could not sign in to Schlage. Check the username and password. ({err})"
            ) from err
        finally:
            client.close()

        meta = [
            {
                "device_id": lock.device_id,
                "name": lock.name or "Lock",
                "model": getattr(lock, "model_name", "") or "",
            }
            for lock in locks
        ]
        if not meta:
            raise ValueError("No locks were found on this Schlage account.")

        identifier = f"schlage_{re.sub(r'[^A-Za-z0-9]', '_', username.lower())}"
        return SchlageConfig(
            identifier=identifier,
            name="Schlage",
            username=username,
            password=password,
            locks=meta,
        )
