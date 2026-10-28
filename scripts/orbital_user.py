# SPDX-License-Identifier: MIT
"""Reject elevated user installations before Qt or desktop settings are touched."""

import os
from pathlib import Path
import stat
import sys


def require_user():
    uids = os.getresuid()
    gids = os.getresgid()
    env = Path('/usr/bin/env')
    try:
        mode = env.stat().st_mode
        elevated_env = bool(mode & (stat.S_ISUID | stat.S_ISGID))
    except FileNotFoundError:
        elevated_env = False
    if 0 not in uids and len(set(uids)) == 1 and len(set(gids)) == 1 and not elevated_env:
        return
    details = f'UID (real, effective, saved): {uids}; GID: {gids}. Python: {sys.executable}.'
    if elevated_env:
        details += f' /usr/bin/env -> {env.resolve()} has special permission bits ({stat.S_IMODE(mode):04o}).'
    raise RuntimeError(
        'Orbital must run as your desktop user, without sudo or elevated IDs. '
        + details + ' Check the permissions of /usr/bin/env (including its symlink target) '
        'and the Python interpreter. Qt aborts when real and effective UIDs differ. '
        'See docs/reference.md#qdbus6-setuid-error.'
    )


if __name__ == '__main__':
    try:
        require_user()
    except RuntimeError as error:
        print(f'Orbital: {error}', file=sys.stderr)
        raise SystemExit(1)
