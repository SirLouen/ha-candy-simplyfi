"""The Candy simply-Fi (local) integration."""
from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import CandyWasher
from .const import CONF_HOST, CONF_KEY, DEFAULT_DESIRED, PLATFORMS
from .coordinator import CandyCoordinator


@dataclass
class RuntimeData:
    coordinator: CandyCoordinator
    client: CandyWasher
    desired: dict = field(default_factory=lambda: dict(DEFAULT_DESIRED))
    learned: dict = field(default_factory=dict)  # name -> {prnm, prcode, recipe_id}


type CandyConfigEntry = ConfigEntry[RuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: CandyConfigEntry) -> bool:
    client = CandyWasher(entry.data[CONF_HOST], key=entry.data.get(CONF_KEY))
    coordinator = CandyCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = RuntimeData(
        coordinator=coordinator,
        client=client,
        learned=dict(entry.options.get("learned", {})),
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload_on_update))
    return True


async def _reload_on_update(hass: HomeAssistant, entry: CandyConfigEntry) -> None:
    """Reload when options change (e.g. a program was learned) so entities pick it up."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: CandyConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
