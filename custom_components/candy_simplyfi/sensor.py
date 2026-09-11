"""Read-only status sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CandyConfigEntry
from .api import program_name_for
from .const import MACH_MODE, PHASE
from .entity import CandyEntity

PARALLEL_UPDATES = 1


def _int(status: dict, key: str) -> int | None:
    try:
        return int(str(status[key]).strip())
    except (KeyError, ValueError, TypeError):
        return None


@dataclass(frozen=True, kw_only=True)
class CandySensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], object]


SENSORS: tuple[CandySensorDescription, ...] = (
    CandySensorDescription(
        key="state", name="State", icon="mdi:washing-machine",
        device_class=SensorDeviceClass.ENUM,
        options=sorted(set(MACH_MODE.values())),
        value_fn=lambda s: MACH_MODE.get(_int(s, "MachMd")),
    ),
    CandySensorDescription(
        key="program", name="Program", icon="mdi:playlist-check",
        value_fn=lambda s: program_name_for(_int(s, "Pr"), _int(s, "PrCode")) or f"code {s.get('PrCode')}",
    ),
    CandySensorDescription(
        key="phase", name="Phase", icon="mdi:progress-clock",
        device_class=SensorDeviceClass.ENUM, options=sorted(set(PHASE.values())),
        value_fn=lambda s: PHASE.get(_int(s, "PrPh")),
    ),
    CandySensorDescription(
        key="remaining", name="Remaining", icon="mdi:timer-sand",
        native_unit_of_measurement="min",
        value_fn=lambda s: _int(s, "RemTime"),
    ),
    CandySensorDescription(
        key="target_temperature", name="Target temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda s: (t if (t := _int(s, "Temp")) not in (None, 255) else None),
    ),
    CandySensorDescription(
        key="spin", name="Spin speed", icon="mdi:rotate-3d-variant",
        native_unit_of_measurement="rpm",
        value_fn=lambda s: (sp * 100 if (sp := _int(s, "SpinSp")) not in (None, 255) else None),
    ),
    CandySensorDescription(
        key="error", name="Error code", icon="mdi:alert-circle-outline",
        value_fn=lambda s: _int(s, "Err"),
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: CandyConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(CandySensor(entry, d) for d in SENSORS)


class CandySensor(CandyEntity, SensorEntity):
    entity_description: CandySensorDescription

    def __init__(self, entry: CandyConfigEntry, description: CandySensorDescription) -> None:
        super().__init__(entry, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        return self.entity_description.value_fn(self._status)
