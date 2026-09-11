"""Config-entry diagnostics (the encryption key is redacted)."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import CandyConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CandyConfigEntry
) -> dict[str, Any]:
    rd = entry.runtime_data
    return {
        "host": entry.data.get("host"),
        "key_present": bool(entry.data.get("key")),
        "status": rd.coordinator.data,
        "desired": {k: v for k, v in rd.desired.items() if k != "learn_name"},
        "learned": rd.learned,
        "last_update_success": rd.coordinator.last_update_success,
    }
