"""Text field: the name to assign when pressing 'Learn current program'."""
from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CandyConfigEntry
from .entity import CandyDesiredEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(hass: HomeAssistant, entry: CandyConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([CandyLearnName(entry)])


class CandyLearnName(CandyDesiredEntity, TextEntity):
    _attr_name = "Learn as"
    _attr_icon = "mdi:rename-box"
    _attr_native_max = 40
    _attr_mode = "text"

    def __init__(self, entry: CandyConfigEntry) -> None:
        super().__init__(entry, "learn_name")

    @property
    def native_value(self) -> str:
        return str(self._desired.get("learn_name", "") or "")

    async def async_set_value(self, value: str) -> None:
        self._set_desired(value)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state not in (None, "unknown", "unavailable"):
            self._desired["learn_name"] = last.state
