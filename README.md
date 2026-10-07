# Orbital KDE rice

A restrained mission-control look for Plasma 6.6 on Wayland: dark navy surfaces, muted cyan and amber accents, original orbital wallpaper, one full-width bottom panel, IBM Plex typography, and Tela Circle Blue icons. It uses no NASA branding or copyrighted mission imagery.

## Apply

From this directory:

```bash
python3 scripts/build_assets.py
./scripts/install-icons.sh
./scripts/apply-user.sh
sudo ./scripts/apply-sddm.sh
```

On a desktop where Orbital is already applied, upgrade only the three widgets with:

```bash
./scripts/upgrade-widgets.sh
```

This keeps the existing panel layout and widget settings. The script takes a snapshot, upgrades the packages with `kpackagetool6`, and restarts Plasma Shell once.

`apply-user.sh` requires the active Plasma session. It saves a dated snapshot under `backups/` before changing user files and prints the exact restore command. The SDDM step copies a system-readable wallpaper, overrides the current Kubuntu login theme, and creates a separate root backup in `/var/backups/orbital-sddm/`.

Reapplying the user theme preserves the bottom panel's current height; all three indicators resize with it. It also preserves the existing Start launcher and its selected icon.

To adjust the CPU orbit, right-click Orbital CPU and open its settings. Choose Classic (the original single satellite), Constellation (three linked satellites, prototype 6), or Pulsar (a dotted orbit with a beacon and pulsing inner rings, prototype 8). Classic remains the default. Constellation offers a percentage position choice: beside the orbit (the default), or inside with the lines and satellites drawn over the digits. Set the indicator size to 60–150% of its panel-relative baseline, horizontal padding to 0–32 px per side, and vertical padding to 0–24 px per side. These controls apply to every style; the panel height limits the effective size and vertical padding. The settings show an animated panel preview at 50% CPU. Set the maximum speed at 100% CPU from 0 to 120 RPM (30 by default). Orbit speed follows CPU usage linearly, and 0% CPU stops all motion. Reapplying the user theme keeps the chosen style, Constellation percentage position, size, padding, and speed.

Hover anywhere over any CPU style, including its padding and percentage, for usage, hottest-core temperature in °C, and average frequency in GHz (two decimal places). Usage reuses the meter's existing once-per-second reading. Temperature and frequency subscriptions are enabled only while hovering, with value updates limited to once per second and no shell polling. Loading or unavailable readings show a dash, including the temperature sensor's initial zero reading. Click the meter to open Plasma System Monitor.

The RAM indicator has two selectable styles: Fan (17 radial ticks) and Silicon (eight chip banks). Both read physical RAM usage once per second and keep the exact percentage visible in the center. Fan is the default. Fan also shows used swap as five amber ticks in its lower arc, enabled by default; even a small nonzero amount lights one tick. Hover anywhere over Fan, with the swap gauge on or off, for separate RAM and swap lines showing used/total GB (two decimal places) and percentages. No configured swap is labeled disabled, and unavailable readings show a dash. Right-click Orbital Memory and choose **Configure Orbital Memory** to switch styles, set the size to 60–110% of its panel-relative fit, and customize the active, inactive, text, chip body, and chip outline colors. In Fan settings, toggle **Show swap gauge** or customize **Swap color**. Turning the gauge off restores the original Fan appearance while retaining swap in the tooltip. The theme button copies current KDE colors into the editable settings, using the neutral color for swap. Reapplying the user theme preserves the selection, size, swap toggle, and colors.

Orbital Battery uses a 20-cell grid and cyan palette. Each solid cell represents a completed 5% of charge, filling from bottom to top, and all 20 cells light up at 99%. While charging below 99%, the next empty cell pulses; at 99% or above, or when charging stops, the pulse stops. Hover to see the percentage on a frosted blue badge; it also appears automatically at 20% charge or below. Right-click Orbital Battery and open its settings to show the percentage all the time, customize each grid and badge color, or copy colors from the current KDE theme. The theme button copies the colors into the settings so they can be adjusted before applying. Reapplying the user theme preserves these choices. The grid keeps a fixed panel width. Click for the familiar Plasma battery menu with brightness and power profiles, or scroll over the widget to adjust screen brightness. The stock battery icon remains available in the tray overflow.

## Restore

```bash
./scripts/restore-user.sh
sudo ./scripts/restore-sddm.sh
```

Sign out and back in after restoring to refresh all running applications. Backups are excluded from Git.

## Files

- `CURRENT_SYSTEM.md`: historical pre-rice system inventory.
- `assets/wallpaper/`: original 3000×2000 and 2560×1440 SVG/PNG wallpapers.
- `assets/kde/Orbital.colors`: KDE color palette based on Breeze Dark.
- `assets/konsole/` and `assets/zsh/`: terminal colors, IBM Plex Mono profile and single-line prompt.
- `widgets/org.orbital.cpu/` and `widgets/org.orbital.memory/`: separate CPU orbit and switchable Fan/Silicon RAM indicators that scale with panel height. Click either to open Plasma System Monitor.
- `widgets/org.orbital.battery/`: 4×5 battery grid with Plasma 6 battery, brightness, power profile, and inhibition controls.
- `scripts/plasma-layout.js`: preserves the existing launcher, pager and pinned task manager, moves the tray and clock to the bottom, and removes the old top panel.

The SDDM override is applied only by the `sudo` command. The user theme, including the lock screen, can be applied separately.
