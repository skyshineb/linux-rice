# SPDX-License-Identifier: MIT
"""Install and update a lunar icon on an existing Plasma Kickoff launcher."""

from __future__ import annotations

import argparse
import configparser
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

from orbital_moon import moon_state, moon_svg, theme_colors

SOURCE = Path(__file__).resolve().parent
APP_ID = 'org.orbital.MoonLauncher'
MANIFEST = '.orbital-install.json'
UNIT = 'orbital-moon'
ASTRONOMY_SHA256 = '5f3a17c0b14290d084eeb0d29b00b3139cd1703a8d30fa5eb141398a24719261'
ICON_NAME = re.compile(r'moon-[0-9a-f]{16}\.svg\Z')


@dataclass(frozen=True)
class Locations:
    home: Path
    config: Path
    data: Path
    state_root: Path

    @classmethod
    def current(cls):
        home = Path.home()
        roots = [Path(os.environ.get(key) or default).expanduser().resolve() for key, default in (
            ('XDG_CONFIG_HOME', home / '.config'), ('XDG_DATA_HOME', home / '.local/share'),
            ('XDG_STATE_HOME', home / '.local/state'))]
        return cls(home, *roots)

    @property
    def bundle(self):
        return self.data / 'orbital-moon-launcher'

    @property
    def command(self):
        return self.home / '.local/bin/orbital-moon'

    @property
    def icons(self):
        return self.data / 'orbital/moon-launcher/icons'

    @property
    def state(self):
        return self.state_root / 'orbital/moon-launcher/state.json'

    @property
    def units(self):
        return {suffix: self.config / 'systemd/user' / f'{UNIT}.{suffix}'
                for suffix in ('service', 'timer', 'path')}


def run(*args, check=True, timeout=30):
    result = subprocess.run([str(arg) for arg in args], capture_output=True, text=True, timeout=timeout)
    if check and result.returncode:
        raise RuntimeError(f'{args[0]} failed: {(result.stderr or result.stdout).strip()}')
    return result


def systemctl(*args, check=True):
    return run('systemctl', '--user', *args, check=check, timeout=60)


def plasma(script):
    result = run('qdbus6', 'org.kde.plasmashell', '/PlasmaShell',
                 'org.kde.PlasmaShell.evaluateScript', script, timeout=10)
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise RuntimeError(f'Plasma returned an invalid response: {result.stdout.strip()}') from error


def targets():
    return plasma('var result=[]; panels().forEach(function(p){p.widgets().forEach(function(w){'
                  'if(w.type==="org.kde.plasma.kickoff"){w.currentConfigGroup=["General"];'
                  'result.push({panel:p.id,applet:w.id,location:p.location,icon:w.readConfig("icon","")});}'
                  '});});print(JSON.stringify(result));')


def target_from(state, available):
    return next((item for item in available if
                 all(item[key] == state['target'][key] for key in ('panel', 'applet'))), None)


def set_icon(target, icon, expected):
    # All strings are JSON encoded and passed as an argv item, never through a shell.
    arguments = json.dumps({'target': target, 'icon': icon, 'expected': expected})
    script = ('var a=' + arguments + ';var p=panelById(a.target.panel);'
              'if(!p){throw new Error("Kickoff panel is missing");}'
              'var w=p.widgets().filter(function(w){return w.id===a.target.applet '
              '&& w.type==="org.kde.plasma.kickoff";})[0];'
              'if(!w){throw new Error("Kickoff is missing");}'
              'w.currentConfigGroup=["General"];'
              'if(w.readConfig("icon","")!==a.expected){throw new Error("Icon changed during update");}'
              'w.writeConfig("icon",a.icon);w.reloadConfig();'
              'print(JSON.stringify({icon:w.readConfig("icon","")}));')
    if plasma(script).get('icon') != icon:
        raise RuntimeError('Plasma did not accept the lunar icon')


def atomic_write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f'.{path.name}-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def read_state(paths):
    state = json.loads(paths.state.read_text())
    if (state.get('version') != 1 or not isinstance(state.get('original_icon'), str)
            or not isinstance(state.get('target'), dict)
            or any(type(state['target'].get(key)) is not int for key in ('panel', 'applet'))
            or not (state.get('last_icon') is None or isinstance(state['last_icon'], str))):
        raise RuntimeError('Invalid lunar launcher state')
    return state


@contextmanager
def locked(paths):
    paths.state.parent.mkdir(parents=True, exist_ok=True)
    with (paths.state.parent / '.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def owned_icon(paths, value):
    path = Path(value)
    return path.parent == paths.icons and ICON_NAME.fullmatch(path.name) is not None


def clean_icons(paths, keep):
    if paths.icons.exists():
        for path in paths.icons.iterdir():
            if ICON_NAME.fullmatch(path.name) and str(path) not in keep and path.is_file():
                path.unlink()


def update_locked(paths, force=False):
    state = read_state(paths)
    current = target_from(state, targets())
    detached = current is not None and current['icon'] != state.get('last_icon') and not owned_icon(paths, current['icon'])
    if current is None or (not force and (state.get('paused') or detached)):
        state['paused'] = True
        state['reason'] = 'Kickoff missing' if current is None else 'Manual icon selection; run install to resume'
        atomic_write(paths.state, json_bytes(state), 0o600)
        return state
    moon = moon_state()
    source = moon_svg(moon, theme_colors(paths.config, paths.data)).encode()
    destination = paths.icons / f'moon-{hashlib.sha256(source).hexdigest()[:16]}.svg'
    previous = current['icon']
    if not destination.exists():
        atomic_write(destination, source)
    if previous != str(destination):
        set_icon(state['target'], str(destination), previous)
    # Commit state only after Plasma acknowledges the change. Roll back the icon
    # if saving state fails, keeping both files available throughout the operation.
    previous_icon = previous if previous != str(destination) else state.get('previous_icon', previous)
    updated = dict(state, last_icon=str(destination), previous_icon=previous_icon,
                   last_update=moon.utc, moon=asdict(moon), paused=False)
    updated.pop('reason', None)
    try:
        atomic_write(paths.state, json_bytes(updated), 0o600)
    except OSError:
        if previous != str(destination):
            set_icon(state['target'], previous, str(destination))
        raise
    clean_icons(paths, {str(destination), previous_icon})
    return updated


def update(paths):
    with locked(paths):
        return update_locked(paths)


def unit_quote(value):
    value = str(value)
    if any(char in value for char in ('\n', '\r', '\0')):
        raise ValueError('Installation paths cannot contain newlines or NUL')
    value = value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%')
    return f'"{value}"'


def unit_path(value):
    # PathChanged takes one literal path, unlike ExecStart's quoted argv syntax.
    value = str(value)
    if any(char in value for char in ('\n', '\r', '\0')):
        raise ValueError('Installation paths cannot contain newlines or NUL')
    return value.replace('%', '%%')


def managed_files(paths):
    wrapper = ('#!/bin/sh\n# Installed by ' + APP_ID + '\n'
               + ''.join(f'export {key}={shlex.quote(str(value))}\n' for key, value in (
                   ('XDG_CONFIG_HOME', paths.config), ('XDG_DATA_HOME', paths.data),
                   ('XDG_STATE_HOME', paths.state_root)))
               + f'exec {shlex.quote(sys.executable)} '
               + f'{shlex.quote(str(paths.bundle / "scripts/orbital-moon"))} "$@"\n')
    common = '[Unit]\nDescription=Orbital lunar launcher\nPartOf=graphical-session.target\n'
    service = (common + 'After=plasma-plasmashell.service\nStartLimitIntervalSec=0\n'
               'Requisite=graphical-session.target\n\n[Service]\nType=oneshot\n'
               f'ExecStart={unit_quote(paths.command)} update\nTimeoutStartSec=45\n')
    timer = (common + '\n[Timer]\nOnActiveSec=15s\nOnCalendar=*-*-* *:00/15:00\n'
             'OnClockChange=true\nOnTimezoneChange=true\nPersistent=true\nAccuracySec=10s\n'
             '\n[Install]\nWantedBy=graphical-session.target\n')
    path_unit = (common + '\n[Path]\n'
                 f'PathChanged={unit_path(paths.config / "kdeglobals")}\n'
                 '\n[Install]\nWantedBy=graphical-session.target\n')
    return {paths.command: (wrapper.encode(), 0o755),
            paths.units['service']: (service.encode(), 0o644),
            paths.units['timer']: (timer.encode(), 0o644),
            paths.units['path']: (path_unit.encode(), 0o644)}


def exists(path):
    return path.exists() or path.is_symlink()


def check_ownership(paths):
    manifest = None
    if exists(paths.bundle):
        marker = paths.bundle / MANIFEST
        if paths.bundle.is_symlink() or not marker.is_file() or marker.is_symlink():
            raise RuntimeError(f'Refusing to replace an unrecognized installation: {paths.bundle}')
        manifest = json.loads(marker.read_text())
        if (manifest.get('application') != APP_ID or manifest.get('version') != 1
                or set(manifest.get('files', {})) != {str(p) for p in managed_files(paths)}):
            raise RuntimeError('Invalid lunar launcher installation manifest')
    for path in managed_files(paths):
        if exists(path) and (path.is_symlink() or not path.is_file() or manifest is None
                or hashlib.sha256(path.read_bytes()).hexdigest() != manifest['files'][str(path)]):
            raise RuntimeError(f'Refusing to replace an unrelated or modified file: {path}')


def unit_states():
    return {suffix: {
        'enabled': systemctl('is-enabled', f'{UNIT}.{suffix}', check=False).stdout.strip() == 'enabled',
        'active': systemctl('is-active', f'{UNIT}.{suffix}', check=False).stdout.strip() == 'active',
    } for suffix in ('timer', 'path')}


def stop_units(disable=False):
    if disable:
        systemctl('disable', '--now', f'{UNIT}.timer', f'{UNIT}.path', check=False)
    else:
        systemctl('stop', f'{UNIT}.timer', f'{UNIT}.path', check=False)
    systemctl('stop', f'{UNIT}.service', check=False)


def restore_units(states):
    systemctl('daemon-reload')
    for suffix, state in states.items():
        systemctl('enable' if state['enabled'] else 'disable', f'{UNIT}.{suffix}', check=False)
        if state['active']:
            systemctl('start', f'{UNIT}.{suffix}')


def remove(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


@contextmanager
def replacements(changes):
    """Retain each previous path on its own filesystem until commit succeeds."""
    backups = []
    safe_to_clean = False
    try:
        for target, prepared in changes:
            target.parent.mkdir(parents=True, exist_ok=True)
            container = Path(tempfile.mkdtemp(prefix=f'.{target.name}-backup-', dir=target.parent))
            previous = container / 'previous'
            existed = exists(target)
            try:
                if existed:
                    target.rename(previous)
            except BaseException:
                container.rmdir()
                raise
            backups.append((target, previous, container, existed))
            if prepared is not None:
                prepared.rename(target)
        yield
        safe_to_clean = True
    except BaseException:
        for target, previous, _, existed in reversed(backups):
            remove(target)
            if existed:
                previous.rename(target)
        safe_to_clean = True
        raise
    finally:
        if safe_to_clean:
            for _, _, container, _ in backups:
                shutil.rmtree(container)


def prepare_file(target, contents, mode):
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f'.{target.name}-new-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(contents)
        os.chmod(temporary, mode)
        return Path(temporary)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def install(paths):
    check_ownership(paths)
    for executable in ('qdbus6', 'systemctl'):
        if shutil.which(executable) is None:
            raise RuntimeError(f'Required command not found: {executable}')
    if hashlib.sha256((SOURCE / 'vendor/astronomy.py').read_bytes()).hexdigest() != ASTRONOMY_SHA256:
        raise RuntimeError('Astronomy Engine 2.1.19 checksum mismatch')
    available = targets()
    if paths.state.exists():
        state = read_state(paths)
        current = target_from(state, available)
        if current is None:
            raise RuntimeError('The saved Kickoff no longer exists; uninstall before selecting another')
    else:
        candidates = [item for item in available if item['location'] == 'bottom']
        if len(candidates) != 1:
            raise RuntimeError('Expected one Kickoff launcher on the bottom panel')
        current = candidates[0]
        state = {'version': 1, 'target': {key: current[key] for key in ('panel', 'applet')},
                 'original_icon': current['icon'], 'last_icon': None, 'paused': False}
    previous_units = unit_states()
    prepared_files = []
    paths.bundle.parent.mkdir(parents=True, exist_ok=True)
    with locked(paths), tempfile.TemporaryDirectory(prefix='.orbital-moon-stage-', dir=paths.bundle.parent) as temporary:
        staged = Path(temporary) / 'bundle'
        scripts = staged / 'scripts'
        scripts.mkdir(parents=True)
        for name in ('orbital-moon', 'orbital_moon.py', 'orbital_moon_launcher.py'):
            shutil.copy2(SOURCE / name, scripts / name)
        shutil.copytree(SOURCE / 'vendor', scripts / 'vendor',
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        files = managed_files(paths)
        manifest = {'application': APP_ID, 'version': 1,
                    'files': {str(p): hashlib.sha256(content).hexdigest() for p, (content, _) in files.items()}}
        (staged / MANIFEST).write_bytes(json_bytes(manifest))
        try:
            changes = [(paths.bundle, staged)]
            for path, (contents, mode) in {**files, paths.state: (json_bytes(state), 0o600)}.items():
                prepared = prepare_file(path, contents, mode)
                prepared_files.append(prepared)
                changes.append((path, prepared))
            if exists(paths.bundle):
                stop_units()
            with replacements(changes):
                try:
                    systemctl('daemon-reload')
                    systemctl('enable', '--now', f'{UNIT}.timer', f'{UNIT}.path')
                    updated = update_locked(paths, force=True)
                    if updated['paused']:
                        raise RuntimeError('Kickoff disappeared during installation')
                except BaseException:
                    stop_units(disable=True)
                    live = target_from(state, targets())
                    if live is not None and owned_icon(paths, live['icon']):
                        set_icon(state['target'], current['icon'], live['icon'])
                    raise
            return updated
        except BaseException:
            restore_units(previous_units)
            raise
        finally:
            for path in prepared_files:
                path.unlink(missing_ok=True)


def uninstall(paths):
    check_ownership(paths)
    if not paths.bundle.exists() and not paths.state.exists():
        return
    state = read_state(paths)
    # Read before stopping anything: an unavailable session leaves the install intact.
    current = target_from(state, targets())
    previous_units = unit_states()
    stop_units(disable=True)
    systemctl('clean', '--what=state', f'{UNIT}.timer', check=False)
    restored = False
    try:
        with locked(paths):
            state = read_state(paths)
            current = target_from(state, targets())
            if current is not None and owned_icon(paths, current['icon']):
                set_icon(state['target'], state['original_icon'], current['icon'])
                restored = True
            changes = [(path, None) for path in [*managed_files(paths), paths.bundle, paths.state]
                       if exists(path)]
            with replacements(changes):
                systemctl('daemon-reload')
    except BaseException:
        if restored:
            set_icon(state['target'], current['icon'], state['original_icon'])
        restore_units(previous_units)
        raise
    clean_icons(paths, set())
    if paths.icons.exists() and not any(paths.icons.iterdir()):
        paths.icons.rmdir()


def status(paths):
    if not paths.state.exists():
        return {'installed': False}
    state = read_state(paths)
    result = dict(state, installed=paths.bundle.is_dir(), units=unit_states())
    try:
        result['live'] = target_from(state, targets())
    except RuntimeError as error:
        result['session_error'] = str(error)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(prog='orbital-moon', description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('install', 'update', 'status', 'uninstall'):
        sub.add_parser(name)
    render = sub.add_parser('render', help='Render an SVG without changing the launcher')
    render.add_argument('--at', help='ISO 8601 date/time including timezone; defaults to now')
    render.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    paths = Locations.current()
    try:
        if args.command == 'render':
            moment = datetime.fromisoformat(args.at.replace('Z', '+00:00')) if args.at else None
            moon = moon_state(moment)
            atomic_write(args.output, moon_svg(moon, theme_colors(paths.config, paths.data)).encode())
            print(json.dumps(asdict(moon), indent=2))
        elif args.command == 'install':
            print(json.dumps(install(paths), indent=2))
        elif args.command == 'update':
            print(json.dumps(update(paths), indent=2))
        elif args.command == 'status':
            print(json.dumps(status(paths), indent=2))
        elif args.command == 'uninstall':
            uninstall(paths)
            print('Lunar launcher removed; the original icon was restored when still managed.')
    except (OSError, ValueError, KeyError, RuntimeError, configparser.Error, subprocess.SubprocessError) as error:
        print(f'orbital-moon: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
