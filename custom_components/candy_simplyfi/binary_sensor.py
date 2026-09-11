"""Running / problem binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CandyConfigEntry
from .const import RUNNING_MODES
from .entity import CandyEntity

PARALLEL_UPDATES = 1


def _int(status: dict, key: str) -> int | None:
    try:
        return int(str(status[key]).strip())
    except (KeyError, ValueError, TypeError):
        return None


async def async_setup_entry(hass: HomeAssistant, entry: CandyConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([CandyRunning(entry), CandyProblem(entry)])


class CandyRunning(CandyEntity, BinarySensorEntity):
    _attr_name = "Running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, entry: CandyConfigEntry) -> None:
        super().__init__(entry, "running")

    @property
    def is_on(self) -> bool:
        return _int(self._status, "MachMd") in RUNNING_MODES


class CandyProblem(CandyEntity, BinarySensorEntity):
    _attr_name = "Problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry: CandyConfigEntry) -> None:
        super().__init__(entry, "problem")

    @property
    def is_on(self) -> bool:
        return bool(_int(self._status, "Err"))
