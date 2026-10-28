#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

set -euo pipefail
destination="$HOME/.local/bin"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      [[ $# -ge 2 ]] || { echo 'Missing --dest directory.' >&2; exit 1; }
      destination="$2"; shift 2 ;;
    --help|-h) echo 'Usage: install-matugen.sh [--dest DIRECTORY]'; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python3 "$script_dir/orbital_user.py"
if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
  echo 'The pinned upstream binary supports Linux x86_64. Install Matugen 4.2.0 from source on other architectures.' >&2
  exit 1
fi
version=4.2.0
checksum=a2e3b50e49ed6439999ba3c252ed04fabd98ee4e9d12e5e5dff2e66370569751
if [[ -x "$destination/matugen" ]] && [[ "$("$destination/matugen" --version)" == "matugen $version" ]]; then
  echo "Matugen $version is already installed at $destination/matugen"
  exit 0
fi
temporary="$(mktemp -d)"
trap 'rm -rf -- "$temporary"' EXIT
curl --fail --location --silent --show-error \
  "https://github.com/InioX/matugen/releases/download/v$version/matugen-$version-x86_64.tar.gz" \
  --output "$temporary/matugen.tar.gz"
printf '%s  %s\n' "$checksum" "$temporary/matugen.tar.gz" | sha256sum --check --status
tar -xzf "$temporary/matugen.tar.gz" -C "$temporary" -- matugen
[[ "$("$temporary/matugen" --version)" == "matugen $version" ]]
install -d "$destination"
install -m 755 "$temporary/matugen" "$destination/matugen"
echo "Installed Matugen $version at $destination/matugen. Ensure $destination is on PATH."
