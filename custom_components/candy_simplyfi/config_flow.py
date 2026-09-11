"""Config flow: enter the washer's IP; the key is auto-recovered from a live read."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .api import CandyWasher, CandyWasherError
from .const import CONF_HOST, CONF_KEY, DOMAIN


class CandyConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, host: str) -> tuple[str | None, str | None]:
        """Return (key, error). One gentle read: recover the key and confirm it decrypts a status."""
        client = CandyWasher(host, retries=6, retry_delay=1.0)
        try:
            key = await self.hass.async_add_executor_job(client.probe)
        except CandyWasherError:
            return None, "cannot_connect"
        except Exception:  # noqa: BLE001  (bad key -> decode/JSON failure)
            return None, "cannot_decrypt"
        return key, None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()
            key, err = await self._validate(host)
            if err:
                errors["base"] = err
            else:
                return self.async_create_entry(
                    title=f"Candy Washer ({host})",
                    data={CONF_HOST: host, CONF_KEY: key},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
            description_placeholders={"example": "192.168.1.50"},
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            key, err = await self._validate(host)
            if err:
                errors["base"] = err
            else:
                return self.async_update_reload_and_abort(
                    entry, data={CONF_HOST: host, CONF_KEY: key}
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {vol.Required(CONF_HOST, default=entry.data[CONF_HOST]): str}
            ),
            errors=errors,
        )
