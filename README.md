# Orbital KDE rice

A restrained mission-control look for this Ubuntu 24.04 / Plasma 5.27 X11 system: dark navy surfaces, muted cyan and amber accents, original orbital wallpaper, full-width top telemetry and bottom app panels, IBM Plex typography, and Tela Circle Blue icons. It uses no NASA branding or copyrighted mission imagery.

## Apply

From this directory:

```bash
python3 scripts/build_assets.py
./scripts/install-icons.sh
./scripts/apply-user.sh
sudo ./scripts/apply-sddm.sh
```

`apply-user.sh` requires the active Plasma session. It saves a dated snapshot under `backups/` before changing user files and prints the exact restore command. The SDDM step copies a system-readable wallpaper, overrides the current Kubuntu login theme, and creates a separate root backup in `/var/backups/orbital-sddm/`.

## Restore

```bash
./scripts/restore-user.sh
sudo ./scripts/restore-sddm.sh
```

Sign out and back in after restoring to refresh all running applications. Backups are excluded from Git.

## Files

- `CURRENT_SYSTEM.md`: pre-rice system inventory.
- `assets/wallpaper/`: original 3000×2000 and 2560×1440 SVG/PNG wallpapers.
- `assets/kde/Orbital.colors`: KDE color palette based on Breeze Dark.
- `assets/konsole/` and `assets/zsh/`: terminal colors, IBM Plex Mono profile and single-line prompt.
- `scripts/plasma-layout.js`: preserves existing launcher, pager and pinned task manager while adding the top status panel.

The SDDM override is applied only by the `sudo` command. The user theme, including the lock screen, can be applied separately.
