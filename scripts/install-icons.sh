#!/usr/bin/env bash
set -euo pipefail
# Pinned official Tela Circle source, reviewed for this setup.
source_url='https://github.com/vinceliuice/Tela-circle-icon-theme.git'
source_commit='ee3cf47bcb05c3d99a0860b54254d2ff3d1d2c69'
if [[ -f "$HOME/.local/share/icons/Tela-circle-blue/index.theme" ]]; then
  echo 'Tela-circle-blue is already installed.'
  exit 0
fi
checkout="$(mktemp -d)"
trap 'rm -rf -- "$checkout"' EXIT
git -C "$checkout" init -q
git -C "$checkout" remote add origin "$source_url"
git -C "$checkout" fetch --depth 1 origin "$source_commit"
git -C "$checkout" checkout -q --detach FETCH_HEAD
[[ "$(git -C "$checkout" rev-parse HEAD)" == "$source_commit" ]]
(cd "$checkout" && ./install.sh -c -d "$HOME/.local/share/icons" blue)
