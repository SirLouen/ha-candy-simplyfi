"""Polling coordinator for the Candy washer."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CandyWasher, CandyWasherError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CandyCoordinator(DataUpdateCoordinator[dict]):
    """Fetches the decrypted washer status on a gentle interval."""

    def __init__(self, hass: HomeAssistant, client: CandyWasher) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self.client.status)
        except CandyWasherError as err:
            raise UpdateFailed(str(err)) from err
