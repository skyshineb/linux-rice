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
restore_on_error() {
  trap - ERR
  echo "Apply failed; restoring $backup" >&2
  "$root/scripts/restore-user.sh" "$backup" >&2
}
trap restore_on_error ERR

for widget in org.orbital.cpu org.orbital.memory; do
  if [[ -d "$HOME/.local/share/plasma/plasmoids/$widget" ]]; then
    kpackagetool5 --type Plasma/Applet --upgrade "$root/widgets/$widget"
  else
    kpackagetool5 --type Plasma/Applet --install "$root/widgets/$widget"
  fi
  [[ -f "$HOME/.local/share/plasma/plasmoids/$widget/contents/ui/main.qml" ]]
done

mkdir -p "$HOME/.local/share/color-schemes" "$HOME/.local/share/konsole" \
  "$HOME/.local/share/wallpapers/Orbital" "$HOME/.oh-my-zsh/custom/themes"
cp "$root/assets/kde/Orbital.colors" "$HOME/.local/share/color-schemes/Orbital.colors"
cp "$root/assets/konsole/Orbital.colorscheme" "$HOME/.local/share/konsole/Orbital.colorscheme"
cp "$root/assets/konsole/Orbital.profile" "$HOME/.local/share/konsole/Orbital.profile"
cp "$root/assets/zsh/Orbital.zsh-theme" "$HOME/.oh-my-zsh/custom/themes/Orbital.zsh-theme"
cp "$root/assets/wallpaper/orbital-3000x2000.png" "$root/assets/wallpaper/orbital-2560x1440.png" "$HOME/.local/share/wallpapers/Orbital/"

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

# Panel opacity and the private system tray are stored outside the scripting API.
bottom_id="$(qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print(panelIds.filter(function(id){return panelById(id).location === "bottom"})[0])')"
tray_id="$(qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'var p=panelById(panelIds.filter(function(id){return panelById(id).location === "bottom"})[0]);var t=p.widgets().filter(function(w){return w.type === "org.kde.plasma.systemtray"})[0];t.currentConfigGroup=[];print(t.readConfig("SystrayContainmentId"))')"
order="$(qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'var p=panelById(panelIds.filter(function(id){return panelById(id).location === "bottom"})[0]);var names=["org.kde.plasma.kickoff","org.kde.plasma.pager","org.kde.plasma.icontasks","org.kde.plasma.panelspacer","org.orbital.cpu","org.orbital.memory","org.kde.plasma.systemtray","org.kde.plasma.digitalclock"];var ws=p.widgets();print(names.map(function(name){return ws.filter(function(w){return w.type===name})[0].id}).join(";"))')"
order_pattern='^[0-9]+(;[0-9]+){7}$'
[[ "$bottom_id" =~ ^[0-9]+$ && "$tray_id" =~ ^[0-9]+$ && "$order" =~ $order_pattern ]]
sni_ids="$(qdbus org.kde.StatusNotifierWatcher /StatusNotifierWatcher org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems | while IFS= read -r item; do
  [[ "$item" == */* ]] || continue
  qdbus "${item%%/*}" "/${item#*/}" org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierItem Id 2>/dev/null || true
done | paste -sd, -)"

systemctl --user stop plasma-plasmashell.service
kwriteconfig5 --file "$HOME/.config/plasmashellrc" --group PlasmaViews --group "Panel $bottom_id" --key panelOpacity 1
kwriteconfig5 --file "$HOME/.config/plasmashellrc" --group PlasmaViews --group "Panel $bottom_id" --key floating 0
kwriteconfig5 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" --group Containments --group "$bottom_id" --group General --key AppletOrder "$order"
shown='org.kde.plasma.battery,org.kde.plasma.networkmanagement,org.kde.plasma.volume'
known="$(kreadconfig5 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" --group Containments --group "$tray_id" --group General --key knownItems)"
hidden="$(python3 - "$known" "$shown" "$sni_ids" <<'PY'
import re
import sys
known = [item for item in sys.argv[1].split(',') if item]
shown = set(sys.argv[2].split(','))
app_ids = [re.sub(r'^dropbox-client-\d+$', 'dropbox-client-PID', item)
           for item in sys.argv[3].split(',') if item]
print(','.join(dict.fromkeys([item for item in known if item not in shown] + app_ids)))
PY
)"
kwriteconfig5 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" --group Containments --group "$tray_id" --group General --key shownItems "$shown"
kwriteconfig5 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" --group Containments --group "$tray_id" --group General --key hiddenItems "$hidden"
kwriteconfig5 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" --group Containments --group "$tray_id" --group General --key showAllItems false
if [[ -d "$HOME/.local/share/plasma/plasmoids/org.orbital.load" ]]; then
  kpackagetool5 --type Plasma/Applet --remove org.orbital.load
fi
systemctl --user start plasma-plasmashell.service
trap - ERR
echo "Orbital applied. Restore with: $root/scripts/restore-user.sh $backup"
