#!/usr/bin/env python3
"""Record and restore user settings touched by Orbital."""
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
PATHS = [
    ".config/kdeglobals",
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


def snapshot() -> None:
    base = ROOT / "backups"
    base.mkdir(mode=0o700, exist_ok=True)
    target = base / datetime.now().strftime("%Y%m%d-%H%M%S")
    target.mkdir(mode=0o700)
    manifest = {}
    for rel in PATHS:
        source = HOME / rel
        manifest[rel] = source.exists() or source.is_symlink()
        if manifest[rel]:
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir() and not source.is_symlink():
                shutil.copytree(source, dest, symlinks=True)
            else:
                shutil.copy2(source, dest, follow_symlinks=False)
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    os.chmod(target / "manifest.json", 0o600)
    (base / "latest").unlink(missing_ok=True)
    (base / "latest").symlink_to(target.name)
    print(target)


def restore(target: Path) -> None:
    manifest = json.loads((target / "manifest.json").read_text())
    for rel, existed in manifest.items():
        dest = HOME / rel
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        else:
            dest.unlink(missing_ok=True)
        if existed:
            source = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir() and not source.is_symlink():
                shutil.copytree(source, dest, symlinks=True)
            else:
                shutil.copy2(source, dest, follow_symlinks=False)
    print(f"Restored {target}")


if __name__ == "__main__":
    if sys.argv[1:] == ["save"]:
        snapshot()
    elif len(sys.argv) == 3 and sys.argv[1] == "restore":
        restore(Path(sys.argv[2]).resolve())
    else:
        raise SystemExit("usage: snapshot.py save | restore BACKUP_DIR")
