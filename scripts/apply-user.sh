#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
theme_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --theme)
      [[ $# -ge 2 ]] || { echo 'Missing --theme value.' >&2; exit 1; }
      theme_args=("$2")
      shift 2
      ;;
    --help|-h) echo 'Usage: apply-user.sh [--theme THEME_ID]'; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
# Validate the selection before installing packages or taking a full snapshot.
python3 "$root/scripts/orbital-theme" apply "${theme_args[@]}" --dry-run >/dev/null
wallpaper_args=()
if [[ ! -f "${XDG_DATA_HOME:-$HOME/.local/share}/orbital/active.json" ]]; then
  wallpaper_args=(--wallpaper)
fi

if ! qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print("ready")' >/dev/null; then
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
    kpackagetool6 --type Plasma/Applet --upgrade "$root/widgets/$widget"
  else
    kpackagetool6 --type Plasma/Applet --install "$root/widgets/$widget"
  fi
  [[ -f "$HOME/.local/share/plasma/plasmoids/$widget/contents/ui/main.qml" ]]
done

mkdir -p "$HOME/.local/share/color-schemes" "$HOME/.local/share/konsole" \
  "$HOME/.local/share/wallpapers/Orbital" "$HOME/.oh-my-zsh/custom/themes"
if [[ ! -f "$HOME/.local/share/konsole/Orbital.profile" ]]; then
  cp "$root/assets/konsole/Orbital.profile" "$HOME/.local/share/konsole/Orbital.profile"
fi
cp "$root/assets/zsh/Orbital.zsh-theme" "$HOME/.oh-my-zsh/custom/themes/Orbital.zsh-theme"
cp "$root/assets/wallpaper/orbital-3000x2000.png" "$root/assets/wallpaper/orbital-2560x1440.png" "$HOME/.local/share/wallpapers/Orbital/"

kwriteconfig6 --file "$HOME/.config/kdeglobals" --group Icons --key Theme Tela-circle-blue
kwriteconfig6 --file "$HOME/.config/kdeglobals" --group General --key font 'IBM Plex Sans,10,-1,5,50,0,0,0,0,0'
kwriteconfig6 --file "$HOME/.config/kdeglobals" --group General --key menuFont 'IBM Plex Sans,10,-1,5,50,0,0,0,0,0'
kwriteconfig6 --file "$HOME/.config/kdeglobals" --group General --key toolBarFont 'IBM Plex Sans,10,-1,5,50,0,0,0,0,0'
kwriteconfig6 --file "$HOME/.config/kdeglobals" --group General --key smallestReadableFont 'IBM Plex Sans,9,-1,5,50,0,0,0,0,0'
kwriteconfig6 --file "$HOME/.config/kdeglobals" --group General --key fixed 'IBM Plex Mono,10,-1,5,50,0,0,0,0,0'
kwriteconfig6 --file "$HOME/.config/kdeglobals" --group WM --key activeFont 'IBM Plex Sans,10,-1,5,50,0,0,0,0,0'

python3 - "$root/scripts" <<'PY'
from pathlib import Path
import re
import sys
sys.path.insert(0, sys.argv[1])
from orbital_themes import read_ini, ini_text
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
    config = read_ini(p)
    if 'Settings' not in config:
        config['Settings'] = {}
    config['Settings']['gtk-icon-theme-name'] = 'Tela-circle-blue'
    config['Settings']['gtk-font-name'] = 'IBM Plex Sans 10'
    p.write_text(ini_text(config))
PY

layout="$(sed "s|HOME_PLACEHOLDER|$HOME|g" "$root/scripts/plasma-layout.js")"
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$layout"

# Panel opacity and system tray settings are stored outside the scripting API.
bottom_id="$(qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print(panelIds.filter(function(id){return panelById(id).location === "bottom"})[0])')"
tray_applet_id="$(qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'var p=panelById(panelIds.filter(function(id){return panelById(id).location === "bottom"})[0]);print(p.widgets().filter(function(w){return w.type === "org.kde.plasma.systemtray"})[0].id)')"
tray_id="$(qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'var p=panelById(panelIds.filter(function(id){return panelById(id).location === "bottom"})[0]);var t=p.widgets().filter(function(w){return w.type === "org.kde.plasma.systemtray"})[0];t.currentConfigGroup=[];print(t.readConfig("SystrayContainmentId"))')"
order="$(qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'var p=panelById(panelIds.filter(function(id){return panelById(id).location === "bottom"})[0]);var names=["org.kde.plasma.kickoff","org.kde.plasma.pager","org.kde.plasma.icontasks","org.kde.plasma.panelspacer","org.orbital.cpu","org.orbital.memory","org.kde.plasma.systemtray","org.kde.plasma.digitalclock"];var ws=p.widgets();print(names.map(function(name){return ws.filter(function(w){return w.type===name})[0].id}).join(";"))')"
order_pattern='^[0-9]+(;[0-9]+){7}$'
[[ "$bottom_id" =~ ^[0-9]+$ && "$tray_applet_id" =~ ^[0-9]+$ && "$order" =~ $order_pattern ]]
if [[ "$tray_id" =~ ^[0-9]+$ ]]; then
  tray_groups=(--group Containments --group "$tray_id" --group General)
elif [[ -z "$tray_id" ]]; then
  # Plasma 6.6 embeds the tray containment directly in the panel's applet group.
  tray_groups=(--group Containments --group "$bottom_id" --group Applets --group "$tray_applet_id" --group General)
else
  echo "Invalid system tray containment ID: $tray_id" >&2
  false
fi
sni_ids="$(qdbus6 org.kde.StatusNotifierWatcher /StatusNotifierWatcher org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems | while IFS= read -r item; do
  [[ "$item" == */* ]] || continue
  qdbus6 "${item%%/*}" "/${item#*/}" org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierItem Id 2>/dev/null || true
done | paste -sd, -)"

systemctl --user stop plasma-plasmashell.service
kwriteconfig6 --file "$HOME/.config/plasmashellrc" --group PlasmaViews --group "Panel $bottom_id" --key panelOpacity 1
kwriteconfig6 --file "$HOME/.config/plasmashellrc" --group PlasmaViews --group "Panel $bottom_id" --key floating 0
kwriteconfig6 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" --group Containments --group "$bottom_id" --group General --key AppletOrder "$order"
shown='org.kde.plasma.networkmanagement,org.kde.plasma.volume'
known="$(kreadconfig6 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" "${tray_groups[@]}" --key knownItems)"
hidden="$(python3 - "$known" "$shown" "$sni_ids" <<'PY'
import re
import sys
known = [item for item in sys.argv[1].split(',') if item]
shown = set(sys.argv[2].split(','))
app_ids = [re.sub(r'^dropbox-client-\d+$', 'dropbox-client-PID', item)
           for item in sys.argv[3].split(',') if item]
print(','.join(dict.fromkeys([item for item in known if item not in shown] + ['org.kde.plasma.battery'] + app_ids)))
PY
)"
kwriteconfig6 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" "${tray_groups[@]}" --key shownItems "$shown"
kwriteconfig6 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" "${tray_groups[@]}" --key hiddenItems "$hidden"
kwriteconfig6 --file "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc" "${tray_groups[@]}" --key showAllItems false
if [[ -d "$HOME/.local/share/plasma/plasmoids/org.orbital.load" ]]; then
  kpackagetool6 --type Plasma/Applet --remove org.orbital.load
fi
systemctl --user start plasma-plasmashell.service
ready=false
for attempt in {1..30}; do
  if qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print("ready")' >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 0.2
done
[[ "$ready" == true ]]
python3 "$root/scripts/orbital-theme" apply "${theme_args[@]}" "${wallpaper_args[@]}"
trap - ERR
echo "Orbital applied. Restore with: $root/scripts/restore-user.sh $backup"
