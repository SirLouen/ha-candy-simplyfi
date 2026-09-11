"""Desired-configuration selects (program / temperature / spin / soil / extra-rinse).

These stage the recipe; nothing is sent to the machine until the Start button is pressed.
"""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CandyConfigEntry
from .api import PROGRAM_NAMES
from .const import EXTRA_RINSE, SOIL_LEVELS, SPIN_SPEEDS, TEMPERATURES
from .entity import CandyDesiredEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(hass: HomeAssistant, entry: CandyConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    program_options = PROGRAM_NAMES + list(entry.runtime_data.learned)
    async_add_entities([
        CandySelect(entry, "program", "Program", program_options, str, str),
        CandySelect(entry, "temp", "Target temperature", [str(t) for t in TEMPERATURES],
                    to_opt=str, from_opt=int),
        CandySelect(entry, "spin", "Spin speed", [str(s) for s in SPIN_SPEEDS],
                    to_opt=str, from_opt=int),
        CandySelect(entry, "soil", "Soil level", list(SOIL_LEVELS),
                    to_opt=lambda v: {n: k for k, n in SOIL_LEVELS.items()}[v],
                    from_opt=lambda o: SOIL_LEVELS[o]),
        CandySelect(entry, "extra_rinse", "Extra rinses", list(EXTRA_RINSE),
                    to_opt=str, from_opt=str),
    ])


class CandySelect(CandyDesiredEntity, SelectEntity):
    def __init__(self, entry: CandyConfigEntry, field: str, name: str, options: list[str],
                 to_opt: Callable[[object], str], from_opt: Callable[[str], object]) -> None:
        super().__init__(entry, field)
        self._attr_name = name
        self._attr_options = options
        self._to_opt = to_opt
        self._from_opt = from_opt

    @property
    def current_option(self) -> str | None:
        opt = self._to_opt(self._desired.get(self._field))
        return opt if opt in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        self._set_desired(self._from_opt(option))

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) and last.state in self._attr_options:
            self._desired[self._field] = self._from_opt(last.state)
