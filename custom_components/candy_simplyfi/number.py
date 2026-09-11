"""Delay-start (hours) — part of the staged recipe."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CandyConfigEntry
from .entity import CandyDesiredEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(hass: HomeAssistant, entry: CandyConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([CandyDelay(entry)])


class CandyDelay(CandyDesiredEntity, NumberEntity):
    _attr_name = "Delay start"
    _attr_native_min_value = 0
    _attr_native_max_value = 24
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "h"
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:clock-start"

    def __init__(self, entry: CandyConfigEntry) -> None:
        super().__init__(entry, "delay")

    @property
    def native_value(self) -> float:
        return float(self._desired.get("delay", 0))

    async def async_set_native_value(self, value: float) -> None:
        self._set_desired(int(value))

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state not in (None, "unknown", "unavailable"):
            try:
                self._desired["delay"] = int(float(last.state))
            except ValueError:
                pass
