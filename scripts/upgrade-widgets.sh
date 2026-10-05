#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if ! qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print("ready")' >/dev/null; then
  echo 'A running Plasma 6 session is required.' >&2
  exit 1
fi

backup="$(python3 "$root/scripts/snapshot.py" save)"
echo "Snapshot: $backup"

restore_on_error() {
  local status=$?
  trap - ERR
  echo "Widget upgrade failed; restoring $backup" >&2
  systemctl --user stop plasma-plasmashell.service || true
  python3 "$root/scripts/snapshot.py" restore "$backup" || true
  systemctl --user start plasma-plasmashell.service || true
  exit "$status"
}
trap restore_on_error ERR

for widget in org.orbital.cpu org.orbital.memory org.orbital.battery; do
  if [[ -d "$HOME/.local/share/plasma/plasmoids/$widget" ]]; then
    kpackagetool6 --type Plasma/Applet --upgrade "$root/widgets/$widget"
  else
    kpackagetool6 --type Plasma/Applet --install "$root/widgets/$widget"
  fi
  [[ -f "$HOME/.local/share/plasma/plasmoids/$widget/contents/ui/main.qml" ]]
done

systemctl --user restart plasma-plasmashell.service
for attempt in {1..20}; do
  if qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'print("ready")' >/dev/null 2>&1; then
    trap - ERR
    echo "Orbital widgets upgraded. Restore with: $root/scripts/restore-user.sh $backup"
    exit 0
  fi
  sleep 1
done
echo 'Plasma Shell did not become ready after the widget upgrade.' >&2
false
