"""Self-contained local client for a Candy simply-Fi washer (RO1496DWMCE / Bianca family).

No external dependencies (stdlib only) so the integration installs cleanly via HACS.
  GET http://<ip>/http-read.json?encrypted=1  -> uppercase-hex repeating-XOR of the status JSON
  GET http://<ip>/http-write.json?encrypted=1&data=<hex>  -> command (hex = xor_encrypt(param_string))
Key = 16 ASCII chars per appliance; recoverable from one status read via known-plaintext.
"""
from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass

READ_PATH = "/http-read.json?encrypted=1"
WRITE_PATH = "/http-write.json?encrypted=1&data="
STATUS_ROOT = "statusLavatrice"

# ---------------- crypto ----------------
_OK = set(range(32, 127)) | {0, 9, 10, 13}


def xor_encrypt(message: str, key: str) -> str:
    m, k = message.encode(), key.encode()
    return bytes(m[i] ^ k[i % len(k)] for i in range(len(m))).hex().upper()


def xor_decrypt(hexstr: str, key: str) -> str:
    ct = bytes.fromhex("".join(hexstr.split()))
    k = key.encode()
    return bytes(ct[i] ^ k[i % len(k)] for i in range(len(ct))).decode("utf-8", "replace")


def recover_key(hexstr: str, keylen: int = 16) -> str:
    """Recover the per-appliance key from one captured status body (known-plaintext crack)."""
    ct = bytes.fromhex("".join(hexstr.split()))
    weight = {0x22: 8, 0x3A: 5, 0x2C: 5, 0x7B: 3, 0x7D: 3}
    for d in range(0x30, 0x3A):
        weight[d] = 3
    for d in list(range(0x41, 0x5B)) + list(range(0x61, 0x7B)):
        weight.setdefault(d, 1)
    key = bytearray(keylen)
    for i in range(keylen):
        col = ct[i::keylen]
        cands = [c for c in range(256) if all((b ^ c) in _OK for b in col)]
        if not cands:
            raise ValueError(f"no printable key byte for column {i}")
        key[i] = max(cands, key=lambda c: sum(weight.get(b ^ c, 0) for b in col))
    return key.decode("latin1")


# ---------------- program map (RO1496 Standard 21) ----------------
@dataclass(frozen=True)
class Program:
    name: str
    prnm: int
    prcode: int
    temp: int | None
    spin: int | None
    soil: int
    steam: int


_P = [
    ("Special 39'", 1, 136, 40, 1000, 0, 5),
    ("Mixed and Coloured 59'", 2, 135, 40, 1000, 0, 5),
    ("Perfect Cotton 59'", 3, 8, 40, 1000, 0, 5),
    ("Hygiene Plus 59'", 4, 40, 60, 1000, 0, 0),
    ("Sport Plus 29'", 5, 72, 30, 1000, 0, 0),
    ("Delicate 59'", 6, 4, 30, 400, 0, 5),
    ("Rapid 14 Min.", 7, 39, 30, 1000, 1, 0),
    ("Rapid 30 Min.", 7, 71, 30, 1000, 2, 0),
    ("Rapid 44 Min.", 7, 103, 40, 1000, 3, 0),
    ("Rinse", 8, 35, None, 1000, 0, 0),
    ("Drain + Spin", 9, 129, None, 1000, 0, 0),
    ("Hand Wash + Wool", 10, 5, 30, 800, 0, 0),
    ("Synthetic and Coloured", 11, 3, 40, 1000, 3, 5),
    ("20 ºC", 12, 11, 20, 1000, 2, 5),
    ("Eco 40-60", 13, 2, 40, 1400, 3, 5),
    ("Whites", 14, 65, 60, 1000, 3, 5),
    ("Refresh Touch", 16, 41, None, None, 0, 0),
    ("Hygiene 60º", 17, 161, 60, 1000, 0, 0),
    ("Baby 60º", 18, 43, 60, 1000, 2, 5),
    ("Jeans", 19, 8, 40, 1000, 0, 0),
    ("Intensive 40º", 20, 11, 40, 1000, 2, 5),
]
STANDARD_PROGRAMS = [Program(*r) for r in _P]
PROGRAMS_BY_NAME = {p.name: p for p in STANDARD_PROGRAMS}
PROGRAM_NAMES = [p.name for p in STANDARD_PROGRAMS]


def program_name_for(prnm: int | None, prcode: int | None) -> str | None:
    """Reverse-lookup a current program from the machine's reported Pr/PrCode."""
    for p in STANDARD_PROGRAMS:
        if p.prnm == prnm and p.prcode == prcode:
            return p.name
    for p in STANDARD_PROGRAMS:  # fall back to PrCode alone
        if p.prcode == prcode:
            return p.name
    return None


class CandyWasherError(Exception):
    pass


class CandyWasher:
    """Blocking client; the HA coordinator calls it via the executor."""

    def __init__(self, host: str, key: str | None = None, timeout: int = 12,
                 retries: int = 4, retry_delay: float = 0.6):
        self.host = host
        self.key = key
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

    def _get(self, path: str) -> str:
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(f"http://{self.host}{path}", timeout=self.timeout) as r:
                    return r.read().decode("ascii", "replace").strip()
            except OSError as err:  # URLError/timeout/RemoteDisconnected all subclass OSError
                last = err
                if attempt < self.retries - 1:
                    time.sleep(self.retry_delay)
        raise CandyWasherError(f"GET {path} failed: {last}") from last

    def ensure_key(self) -> str:
        if not self.key:
            self.key = recover_key(self._get(READ_PATH))
        return self.key

    def status(self) -> dict:
        self.ensure_key()
        doc = json.loads(xor_decrypt(self._get(READ_PATH), self.key))
        return doc.get(STATUS_ROOT, doc)

    def probe(self) -> str:
        """Single-read connectivity + key check for the config flow (one HTTP hit, gentle on the
        single-connection module). Returns the recovered key; raises on unreachable/undecryptable."""
        body = self._get(READ_PATH)
        key = recover_key(body)
        json.loads(xor_decrypt(body, key))  # confirm the key decrypts to valid status JSON
        self.key = key
        return key

    def _write(self, param_string: str) -> str:
        self.ensure_key()
        data = xor_encrypt(param_string, self.key)
        resp = self._get(f"{WRITE_PATH}{data}")
        try:
            return xor_decrypt(resp, self.key)
        except Exception:
            return resp

    def start(self, program: int, *, prog_code: int, prog_name: str = "", temp: int = 40,
              soil: int = 0, spin: int = 1000, opt_mask1: int = 0, delay_h: int = 0,
              steam: int = 0, recipe_id: int = 0) -> str:
        ps = (f"Write=1&StSt=1&DelVl={delay_h}&PrNm={program}&PrCode={prog_code}"
              f"&PrStr={prog_name}&TmpTgt={temp}&SLevTgt={soil}&SpdTgt={spin}"
              f"&OptMsk1={opt_mask1}&OptMsk2=0&Stm={steam}&Dry=0&ED=0&RecipeId={recipe_id}&DispTestOn=1")
        return self._write(ps)

    def stop(self, program: int = 0) -> str:
        return self._write(f"Write=1&StSt=0&PrNm={program}&DelVl=0")

    def pause(self, program: int = 0) -> str:
        return self._write(f"Write=1&Pa=1&PrNm={program}")
