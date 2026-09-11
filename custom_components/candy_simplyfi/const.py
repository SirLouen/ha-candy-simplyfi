"""Constants for the Candy simply-Fi integration."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "candy_simplyfi"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.TEXT,
]

CONF_HOST = "host"
CONF_KEY = "key"

# Gentle polling: the ESP module is single-connection and wedges under concurrent load.
DEFAULT_SCAN_INTERVAL = 30  # seconds

# Adjustable domains for this model (from the app UI).
TEMPERATURES = [0, 20, 30, 40, 60, 90]
SPIN_SPEEDS = [0, 400, 800, 1000, 1400]
SOIL_LEVELS = {"Little": 1, "Normal": 2, "Very": 3}
SOIL_BY_VALUE = {v: k for k, v in SOIL_LEVELS.items()}
EXTRA_RINSE = {"None": 0, "+1": 16, "+2": 32, "+3": 64}  # OptMsk1 bits (mutually exclusive)

# Option -> OptMsk1 bit (the 7 exposed by this model; +1/+2/+3 handled by EXTRA_RINSE select)
OPT_PREWASH = 1
OPT_HYGIENE = 2
OPT_GOOD_NIGHT = 8
OPT_AQUAPLUS = 128

# Machine-mode decode (MachMd)
MACH_MODE = {
    0: "off", 1: "ready", 2: "running", 3: "running", 4: "running",
    5: "running", 6: "paused", 7: "finished",
}
RUNNING_MODES = {2, 3, 4, 5}

PHASE = {0: "idle", 1: "prewash", 2: "wash", 3: "rinse", 4: "last_rinse", 5: "spin", 6: "drying"}

# Default desired configuration = the owner's usual setup (Whites 90°, steam, Very, prewash).
DEFAULT_DESIRED = {
    "program": "Whites",
    "temp": 90,
    "spin": 1000,
    "soil": 3,
    "steam": True,
    "prewash": True,
    "hygiene": False,
    "good_night": False,
    "aquaplus": False,
    "extra_rinse": "None",
    "delay": 0,
}
