#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
backup="${1:-$root/backups/latest}"
systemctl --user stop plasma-plasmashell.service
python3 "$root/scripts/snapshot.py" restore "$backup"
systemctl --user start plasma-plasmashell.service
echo 'User theme restored. Sign out and back in to refresh all application fonts and icons.'
