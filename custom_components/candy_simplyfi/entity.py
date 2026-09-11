"""Shared base entity + desired-config helpers."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CandyConfigEntry
from .const import DOMAIN
from .coordinator import CandyCoordinator


def device_info(host: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, host)},
        name="Candy Washer",
        manufacturer="Candy",
        model="RapidÓ RO1496DWMCE",
        configuration_url=f"http://{host}/",
    )


class CandyEntity(CoordinatorEntity[CandyCoordinator]):
    """Base for status entities backed by the polling coordinator."""

    _attr_has_entity_name = True

    def __init__(self, entry: CandyConfigEntry, key: str) -> None:
        super().__init__(entry.runtime_data.coordinator)
        self._host = entry.data["host"]
        self._attr_unique_id = f"{self._host}_{key}"
        self._attr_device_info = device_info(self._host)

    @property
    def _status(self) -> dict:
        return self.coordinator.data or {}


class CandyDesiredEntity(RestoreEntity):
    """Base for 'desired configuration' controls: hold a local value (persisted), applied on Start.

    These do NOT poll or write to the machine on change — they stage the recipe that the Start
    button assembles into a single command. Available even when the machine is briefly offline.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = None

    def __init__(self, entry: CandyConfigEntry, key: str) -> None:
        self._entry = entry
        self._field = key
        self._host = entry.data["host"]
        self._attr_unique_id = f"{self._host}_cfg_{key}"
        self._attr_device_info = device_info(self._host)

    @property
    def _desired(self) -> dict:
        return self._entry.runtime_data.desired

    def _set_desired(self, value) -> None:
        self._desired[self._field] = value
        self.async_write_ha_state()
