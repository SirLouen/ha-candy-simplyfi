"""Desired-configuration option switches (steam + wash options)."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CandyConfigEntry
from .entity import CandyDesiredEntity

PARALLEL_UPDATES = 1

# field -> (display name, icon)
SWITCHES = {
    "steam": ("Steam", "mdi:weather-fog"),
    "prewash": ("Pre-wash", "mdi:water-plus"),
    "hygiene": ("Hygiene+", "mdi:bacteria-outline"),
    "good_night": ("Good Night", "mdi:weather-night"),
    "aquaplus": ("Aquaplus", "mdi:water"),
}


async def async_setup_entry(hass: HomeAssistant, entry: CandyConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(CandyOptionSwitch(entry, f, name, icon)
                       for f, (name, icon) in SWITCHES.items())


class CandyOptionSwitch(CandyDesiredEntity, SwitchEntity):
    def __init__(self, entry: CandyConfigEntry, field: str, name: str, icon: str) -> None:
        super().__init__(entry, field)
        self._attr_name = name
        self._attr_icon = icon

    @property
    def is_on(self) -> bool:
        return bool(self._desired.get(self._field))

    async def async_turn_on(self, **kwargs) -> None:
        self._set_desired(True)

    async def async_turn_off(self, **kwargs) -> None:
        self._set_desired(False)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self._desired[self._field] = last.state == "on"
