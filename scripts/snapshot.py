#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

"""Record and restore user settings touched by Orbital."""
import json
import os
import sys

from orbital_themes import Themes, copy_path, remove_path, is_theme_artifact
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATHS = [
    ".config/kdeglobals",
    ".config/plasmarc",
    ".config/plasmashellrc",
    ".config/plasma-org.kde.plasma.desktop-appletsrc",
    ".config/konsolerc",
    ".config/kscreenlockerrc",
    ".config/gtk-3.0/settings.ini",
    ".config/gtk-4.0/settings.ini",
    ".zshrc",
    ".local/share/color-schemes/Orbital.colors",
    ".local/share/konsole/Orbital.colorscheme",
    ".local/share/konsole/Orbital.profile",
    ".oh-my-zsh/custom/themes/Orbital.zsh-theme",
    ".local/share/wallpapers/Orbital",
    ".local/share/plasma/plasmoids/org.orbital.load",
    ".local/share/plasma/plasmoids/org.orbital.cpu",
    ".local/share/plasma/plasmoids/org.orbital.memory",
    ".local/share/plasma/plasmoids/org.orbital.battery",
]


def managed_patterns(manager: Themes | None = None):
    data = (manager or Themes()).data
    return [(data / "color-schemes", "Orbital-*.colors"),
            (data / "konsole", "Orbital-*.profile"),
            (data / "konsole", "Orbital-*.colorscheme")]


def snapshot(manager: Themes | None = None, backup_root: Path | None = None) -> Path:
    manager = manager or Themes()
    base = backup_root or ROOT / "backups"
    base.mkdir(mode=0o700, exist_ok=True)
    target = base / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    target.mkdir(mode=0o700)
    paths = list(dict.fromkeys([manager.home / rel for rel in PATHS] + manager.paths()))
    # GTK directories cover settings.ini and the colors exported by KDE.
    paths = [path for path in paths if not any(parent in paths for parent in path.parents)]
    manifest = []
    for index, source in enumerate(paths):
        exists = source.exists() or source.is_symlink()
        manifest.append({"path": str(source), "existed": exists, "file": str(index)})
        if exists:
            copy_path(source, target / str(index))
    metadata = {"version": 2, "paths": manifest,
                "managed_patterns": [[str(path), pattern] for path, pattern in managed_patterns(manager)]}
    (target / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    os.chmod(target / "manifest.json", 0o600)
    (base / "latest").unlink(missing_ok=True)
    (base / "latest").symlink_to(target.name)
    print(target)
    return target


def restore(target: Path, manager: Themes | None = None) -> None:
    manager = manager or Themes()
    manifest = json.loads((target / "manifest.json").read_text())
    if manifest.get("version") == 2:
        entries = manifest["paths"]
        allowed = {manager.home / rel for rel in PATHS} | set(manager.paths())
        patterns = managed_patterns(manager)
        for item in entries:
            path = Path(item["path"])
            owned = is_theme_artifact(path, manager.data)
            if path not in allowed and not owned:
                raise ValueError(f"Snapshot path outside Orbital settings: {path}")
            if not str(item["file"]).isdigit():
                raise ValueError("Invalid snapshot file entry")
            source = target / item["file"]
            if item["existed"] and not (source.exists() or source.is_symlink()):
                raise ValueError("Incomplete snapshot")
        saved = {Path(item["path"]) for item in entries}
        for directory, pattern in patterns:
            for path in directory.glob(pattern):
                if path not in saved and is_theme_artifact(path, manager.data):
                    remove_path(path)
    else:
        # Backwards compatibility with snapshots produced before palette support.
        entries = [{"path": str(manager.home / rel), "existed": existed, "file": rel}
                   for rel, existed in manifest.items()]
        if any(item["file"] not in PATHS for item in entries):
            raise ValueError("Snapshot contains an unknown settings path")
        if any(item['existed'] and not ((target / item['file']).exists()
                                       or (target / item['file']).is_symlink()) for item in entries):
            raise ValueError("Incomplete snapshot")
    for item in entries:
        dest = Path(item["path"])
        remove_path(dest)
        if item["existed"]:
            copy_path(target / item["file"], dest)
    print(f"Restored {target}")


if __name__ == "__main__":
    if sys.argv[1:] == ["save"]:
        snapshot()
    elif len(sys.argv) == 3 and sys.argv[1] == "restore":
        restore(Path(sys.argv[2]).resolve())
    else:
        raise SystemExit("usage: snapshot.py save | restore BACKUP_DIR")
