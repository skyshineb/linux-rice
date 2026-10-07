#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

set -euo pipefail
if [[ $EUID -ne 0 ]]; then
  echo 'Run with sudo: sudo ./scripts/apply-sddm.sh' >&2
  exit 1
fi
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
theme='/usr/share/sddm/themes/kubuntu/theme.conf.user'
config='/etc/sddm.conf.d/90-orbital.conf'
wallpaper='/usr/local/share/wallpapers/Orbital/orbital-3000x2000.png'
backup="/var/backups/orbital-sddm/$(date +%Y%m%d-%H%M%S)"
install -d -m 700 "$backup"
for name in theme config wallpaper; do
  path="${!name}"
  if [[ -e "$path" ]]; then
    cp -a "$path" "$backup/$name"
  else
    touch "$backup/$name.absent"
  fi
done
install -d -m 755 "$(dirname "$wallpaper")"
install -m 644 "$root/assets/wallpaper/orbital-3000x2000.png" "$wallpaper"
cat > "$theme" <<EOF
[General]
background=$wallpaper
color=#67C4DE
fontSize=10
type=image
showlogo=hidden
EOF
chmod 644 "$theme"
cat > "$config" <<'EOF'
[Theme]
Font=IBM Plex Sans,10
EOF
chmod 644 "$config"
install -d -m 755 /var/backups/orbital-sddm
ln -sfn "$backup" /var/backups/orbital-sddm/latest
echo "SDDM theme staged. Backup: $backup"
echo 'The new login screen will appear after sign out or reboot.'
