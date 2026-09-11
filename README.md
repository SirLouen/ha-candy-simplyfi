# Candy simply-Fi (local) — Home Assistant integration

Control a Candy / Hoover **simply-Fi** washing machine (RapidÓ *Bianca* family, e.g. **RO1496DWMCE**)
**entirely over your LAN**, with **no cloud** — bypassing the flaky `simply-fi.herokuapp.com` backend the
official app depends on.

It talks directly to the appliance's ESP Wi-Fi module (`http-read.json` / `http-write.json`, XOR-hex
encrypted) and **recovers the per-appliance encryption key automatically** from a single status read —
you only enter the washer's IP.

## Features
- **Status** (polled every 30 s): state, current program, phase, remaining, target temperature, spin, error.
- **Binary sensors**: running, problem.
- **Staged "recipe" controls** — set these, then press **Start**:
  - `select`: Program (21 standard programs), Target temperature (0/20/30/40/60/90 °C), Spin (0/400/800/1000/1400 rpm), Soil level (Little/Normal/Very), Extra rinses (None/+1/+2/+3).
  - `switch`: Steam, Pre-wash, Hygiene+, Good Night, Aquaplus.
  - `number`: Delay start (h).
  - `button`: **Start**, Stop, Pause.
- **Learn themed programs**: type a name in `Learn as`, select a downloadable program in the official
  app, then press **Learn current program** — it captures that program's `PrNm`/`PrCode`/`RecipeId`
  and adds it to the Program `select`. (Lets you reach the ~50 cloud-only programs the APK doesn't define.)
- **Diagnostics** (Settings → device → ⋮ → Download diagnostics; key redacted) and a **Reconfigure**
  step to change the IP later.

Defaults are pre-filled to a common setup (**Whites, 90 °C, steam, Very soil, pre-wash**) — change any control, and it's remembered.

## Dashboard
A ready-to-paste home-panel card (core cards, no custom components) is in
[`dashboard-card.yaml`](dashboard-card.yaml): status + the full wash setup + Start/Stop/Pause + the learn box.

> **Nothing auto-starts.** A wash only begins when you press **Start**. The controls stage a recipe
> locally; Start sends one command. This suits the module, whose single-connection HTTP server is
> polled gently to avoid wedging.

## Requirements
- The washer must be enrolled on your Wi-Fi and reachable on port 80. It **does not answer ping** — that's normal.
- Home Assistant 2024.12 or newer.

## Install
### Via HACS (custom repository)
1. HACS → ⋮ → *Custom repositories* → add your fork's URL, category **Integration**.
2. Install **Candy simply-Fi (local)**, then restart Home Assistant.

### Manual
Copy `custom_components/candy_simplyfi/` into your HA `config/custom_components/` and restart.

## Setup
**Settings → Devices & Services → Add Integration → “Candy simply-Fi”**, then enter the washer's IP
(e.g. `192.168.1.50`). The key is recovered automatically.

## Notes & limits
- **Program map**: the 21 standard programs are resolved (`PrNm`+`PrCode`) from the app's own data and
  anchored to a live machine. The ~50 "themed/downloadable" programs (Stains, Special Care, …) are
  **cloud-downloaded and not in the APK** — add the ones you use via the **Learn** flow (above).
- Spin/temperature values outside a program's allowed range are clamped by the machine.
- `Remaining` is reported by the machine in a model-dependent unit; treat it as approximate.

## Before publishing
`manifest.json` is set to owner **`SirLouen`** and repo **`ha-candy-simplyfi`** — edit those two URLs and
`codeowners` if your GitHub handle or repo name differ.

## Credits
Protocol reverse-engineered from the `it.candy.simplyfi` APK — see the companion analysis
(`docs/ANALYSIS.md`, `docs/PROGRAMS.md`). Local, cloud-free, and yours to extend.
