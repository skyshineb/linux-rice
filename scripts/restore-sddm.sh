#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
  echo 'Run with sudo: sudo ./scripts/restore-sddm.sh [BACKUP_DIR]' >&2
  exit 1
fi
backup="${1:-/var/backups/orbital-sddm/latest}"
[[ -f "$backup/theme" || -f "$backup/theme.absent" ]] || { echo 'Invalid SDDM backup' >&2; exit 1; }
theme='/usr/share/sddm/themes/kubuntu/theme.conf.user'
config='/etc/sddm.conf.d/90-orbital.conf'
wallpaper='/usr/local/share/wallpapers/Orbital/orbital-3000x2000.png'
for name in theme config wallpaper; do
  path="${!name}"
  if [[ -f "$backup/$name.absent" ]]; then
    rm -f -- "$path"
  else
    cp -a "$backup/$name" "$path"
  fi
done
echo "SDDM restored from $backup. Sign out or reboot to see the result."
