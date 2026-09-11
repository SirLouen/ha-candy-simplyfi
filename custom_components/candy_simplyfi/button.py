"""Start / Stop / Pause + Learn buttons.

Start assembles the staged desired-config into a single /http-write command. Nothing auto-fires.
Learn snapshots the machine's currently-selected program (Pr/PrCode/RecipeId) as a reusable recipe,
so the cloud-only "themed" programs can be added by selecting one in the app and pressing Learn once.
"""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CandyConfigEntry
from .api import PROGRAMS_BY_NAME, CandyWasherError
from .const import (
    EXTRA_RINSE,
    OPT_AQUAPLUS,
    OPT_GOOD_NIGHT,
    OPT_HYGIENE,
    OPT_PREWASH,
)
from .entity import CandyEntity

_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 1


async def async_setup_entry(hass: HomeAssistant, entry: CandyConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([
        CandyStart(entry), CandyStop(entry), CandyPause(entry), CandyLearn(entry),
    ])


class _CandyButton(CandyEntity, ButtonEntity):
    def __init__(self, entry: CandyConfigEntry, key: str, name: str, icon: str) -> None:
        super().__init__(entry, key)
        self._attr_name = name
        self._attr_icon = icon
        self._entry = entry

    # Actions stay usable even if the last poll failed, so the user can retry.
    @property
    def available(self) -> bool:
        return True

    @property
    def _client(self):
        return self._entry.runtime_data.client

    async def _refresh(self) -> None:
        await self.coordinator.async_request_refresh()


class CandyStart(_CandyButton):
    def __init__(self, entry: CandyConfigEntry) -> None:
        super().__init__(entry, "start", "Start", "mdi:play")

    async def async_press(self) -> None:
        d = self._entry.runtime_data.desired
        learned = self._entry.runtime_data.learned
        name = d["program"]
        if name in PROGRAMS_BY_NAME:
            p = PROGRAMS_BY_NAME[name]
            prnm, prcode, recipe_id = p.prnm, p.prcode, 0
        elif name in learned:
            r = learned[name]
            prnm, prcode, recipe_id = r["prnm"], r["prcode"], r.get("recipe_id", 0)
        else:
            raise HomeAssistantError(f"Unknown program: {name}")

        mask = (
            (OPT_PREWASH if d["prewash"] else 0)
            | (OPT_HYGIENE if d["hygiene"] else 0)
            | (OPT_GOOD_NIGHT if d["good_night"] else 0)
            | (OPT_AQUAPLUS if d["aquaplus"] else 0)
            | EXTRA_RINSE.get(d["extra_rinse"], 0)
        )
        steam = 5 if d["steam"] else 0
        _LOGGER.info("Start %s: PrNm=%s PrCode=%s temp=%s spin=%s soil=%s steam=%s opt=%s delay=%s recipe=%s",
                     name, prnm, prcode, d["temp"], d["spin"], d["soil"], steam, mask, d["delay"], recipe_id)
        try:
            resp = await self.hass.async_add_executor_job(
                lambda: self._client.start(
                    prnm, prog_code=prcode, prog_name=name, temp=int(d["temp"]),
                    soil=int(d["soil"]), spin=int(d["spin"]), opt_mask1=mask,
                    delay_h=int(d["delay"]), steam=steam, recipe_id=recipe_id,
                )
            )
        except CandyWasherError as err:
            raise HomeAssistantError(f"Failed to start washer: {err}") from err
        _LOGGER.debug("Start response: %s", resp)
        await self._refresh()


class CandyStop(_CandyButton):
    def __init__(self, entry: CandyConfigEntry) -> None:
        super().__init__(entry, "stop", "Stop", "mdi:stop")

    async def async_press(self) -> None:
        try:
            await self.hass.async_add_executor_job(self._client.stop)
        except CandyWasherError as err:
            raise HomeAssistantError(f"Failed to stop washer: {err}") from err
        await self._refresh()


class CandyPause(_CandyButton):
    def __init__(self, entry: CandyConfigEntry) -> None:
        super().__init__(entry, "pause", "Pause", "mdi:pause")

    async def async_press(self) -> None:
        try:
            await self.hass.async_add_executor_job(self._client.pause)
        except CandyWasherError as err:
            raise HomeAssistantError(f"Failed to pause washer: {err}") from err
        await self._refresh()


class CandyLearn(_CandyButton):
    """Capture the machine's current program as a reusable recipe (for the downloadable programs)."""

    _attr_entity_category = None

    def __init__(self, entry: CandyConfigEntry) -> None:
        super().__init__(entry, "learn", "Learn current program", "mdi:content-save-cog")

    async def async_press(self) -> None:
        try:
            status = await self.hass.async_add_executor_job(self._client.status)
        except CandyWasherError as err:
            raise HomeAssistantError(f"Could not read the machine to learn: {err}") from err

        def _i(key: str) -> int:
            try:
                return int(str(status[key]).strip())
            except (KeyError, ValueError, TypeError):
                return 0

        name = (self._entry.runtime_data.desired.get("learn_name") or "").strip()
        if not name:
            name = f"Learned {_i('PrCode')}"
        learned = dict(self._entry.runtime_data.learned)
        learned[name] = {"prnm": _i("Pr"), "prcode": _i("PrCode"), "recipe_id": _i("RecipeId")}
        _LOGGER.info("Learned program %r -> %s", name, learned[name])
        # Persist to options; the update-listener reloads so the program select picks it up.
        self.hass.config_entries.async_update_entry(
            self._entry, options={**self._entry.options, "learned": learned}
        )
