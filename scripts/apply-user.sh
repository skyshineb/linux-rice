#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

if ! qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print("ready")' >/dev/null; then
  echo 'A running Plasma session is required.' >&2
  exit 1
fi
if [[ ! -f "$HOME/.local/share/icons/Tela-circle-blue/index.theme" ]]; then
  echo 'Install Tela Circle Blue with scripts/install-icons.sh first.' >&2
  exit 1
fi

backup="$(python3 "$root/scripts/snapshot.py" save)"
echo "Snapshot: $backup"
mkdir -p "$HOME/.local/share/color-schemes" "$HOME/.local/share/konsole" \
  "$HOME/.local/share/wallpapers/Orbital" "$HOME/.oh-my-zsh/custom/themes"
cp "$root/assets/kde/Orbital.colors" "$HOME/.local/share/color-schemes/Orbital.colors"
cp "$root/assets/konsole/Orbital.colorscheme" "$HOME/.local/share/konsole/Orbital.colorscheme"
cp "$root/assets/konsole/Orbital.profile" "$HOME/.local/share/konsole/Orbital.profile"
cp "$root/assets/zsh/Orbital.zsh-theme" "$HOME/.oh-my-zsh/custom/themes/Orbital.zsh-theme"
cp "$root"/assets/wallpaper/*.png "$HOME/.local/share/wallpapers/Orbital/"

plasma-apply-colorscheme Orbital
kwriteconfig5 --file "$HOME/.config/kdeglobals" --group Icons --key Theme Tela-circle-blue
kwriteconfig5 --file "$HOME/.config/kdeglobals" --group General --key font 'IBM Plex Sans,10,-1,5,50,0,0,0,0,0'
kwriteconfig5 --file "$HOME/.config/kdeglobals" --group General --key menuFont 'IBM Plex Sans,10,-1,5,50,0,0,0,0,0'
kwriteconfig5 --file "$HOME/.config/kdeglobals" --group General --key toolBarFont 'IBM Plex Sans,10,-1,5,50,0,0,0,0,0'
kwriteconfig5 --file "$HOME/.config/kdeglobals" --group General --key smallestReadableFont 'IBM Plex Sans,9,-1,5,50,0,0,0,0,0'
kwriteconfig5 --file "$HOME/.config/kdeglobals" --group General --key fixed 'IBM Plex Mono,10,-1,5,50,0,0,0,0,0'
kwriteconfig5 --file "$HOME/.config/kdeglobals" --group WM --key activeFont 'IBM Plex Sans,10,-1,5,50,0,0,0,0,0'
kwriteconfig5 --file "$HOME/.config/konsolerc" --group 'Desktop Entry' --key DefaultProfile Orbital.profile
kwriteconfig5 --file "$HOME/.config/kscreenlockerrc" --group Greeter --key WallpaperPlugin org.kde.image
kwriteconfig5 --file "$HOME/.config/kscreenlockerrc" --group Greeter --group Wallpaper --group org.kde.image --group General --key Image "$HOME/.local/share/wallpapers/Orbital/orbital-3000x2000.png"

python3 - <<'PY'
from pathlib import Path
import re
home = Path.home()
path = home / '.zshrc'
source = path.read_text()
updated, count = re.subn(r'(?m)^ZSH_THEME=.*$', 'ZSH_THEME="Orbital"', source, count=1)
if count != 1:
    raise SystemExit('Could not find ZSH_THEME in ~/.zshrc')
path.write_text(updated)
for rel in ('.config/gtk-3.0/settings.ini', '.config/gtk-4.0/settings.ini'):
    p = home / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    text = p.read_text() if p.exists() else '[Settings]\n'
    for key, value in [('gtk-theme-name', 'Breeze-Dark'),
                       ('gtk-icon-theme-name', 'Tela-circle-blue'),
                       ('gtk-font-name', 'IBM Plex Sans 10'),
                       ('gtk-application-prefer-dark-theme', 'true')]:
        pat = r'(?m)^' + re.escape(key) + r'=.*$'
        if re.search(pat, text):
            text = re.sub(pat, key + '=' + value, text)
        else:
            text += key + '=' + value + '\n'
    p.write_text(text)
PY

layout="$(sed "s|HOME_PLACEHOLDER|$HOME|g" "$root/scripts/plasma-layout.js")"
qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$layout"

# Panel opacity is stored in plasmashellrc outside the Plasma scripting API.
bottom_id="$(qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print(panelIds.filter(function(id){return panelById(id).location === "bottom"})[0])')"
top_id="$(qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print(panelIds.filter(function(id){return panelById(id).location === "top"})[0])')"
for id in "$bottom_id" "$top_id"; do
  kwriteconfig5 --file "$HOME/.config/plasmashellrc" --group PlasmaViews --group "Panel $id" --key panelOpacity 1
  kwriteconfig5 --file "$HOME/.config/plasmashellrc" --group PlasmaViews --group "Panel $id" --key floating 0
done
systemctl --user restart plasma-plasmashell.service
echo "Orbital applied. Restore with: $root/scripts/restore-user.sh $backup"
