#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT
set -eu

if ! command -v python3 >/dev/null 2>&1; then
    echo 'Orbital requires Python 3.10 or newer. Install python3 and retry.' >&2
    exit 1
fi
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$script_dir/install_app.py" "$@"
