# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

"""Install a self-contained user application without applying a desktop theme."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
APP_ID = 'org.orbital.ThemeEditor'
MANIFEST = '.orbital-install.json'


def locations(prefix=None):
    if prefix is not None:
        prefix = Path(prefix).expanduser().resolve()
        data, binaries = prefix / 'share', prefix / 'bin'
    else:
        data = Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share').expanduser().resolve()
        binaries = Path.home() / '.local/bin'
    return (data / 'orbital-theme-editor', binaries / 'orbital-theme',
            data / 'applications' / f'{APP_ID}.desktop',
            data / 'icons/hicolor/scalable/apps' / f'{APP_ID}.svg')


def fingerprint(contents):
    return hashlib.sha256(contents).hexdigest()


def exists(path):
    return path.exists() or path.is_symlink()


def check_ownership(paths):
    bundle, *files = paths
    manifest = None
    if exists(bundle):
        marker = bundle / MANIFEST
        if bundle.is_symlink() or not bundle.is_dir() or marker.is_symlink() or not marker.is_file():
            raise RuntimeError(f'Refusing to replace an unrecognized application directory: {bundle}')
        try:
            manifest = json.loads(marker.read_text())
            if (manifest['application'] != APP_ID or manifest['version'] != 1 or
                    not isinstance(manifest['files'], dict) or
                    set(manifest['files']) != {str(path) for path in files}):
                raise ValueError('Unexpected installation manifest')
        except (ValueError, KeyError, TypeError) as error:
            raise RuntimeError(f'Invalid Orbital installation manifest: {marker}') from error
    for path in files:
        if exists(path) and (path.is_symlink() or not path.is_file() or manifest is None or
                             fingerprint(path.read_bytes()) != manifest['files'][str(path)]):
            raise RuntimeError(f'Refusing to replace or remove an unrelated or modified file: {path}')


def search_path(binaries):
    return os.pathsep.join((str(binaries), str(Path.home() / '.local/bin'),
                            os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin')))


def check_matugen(binaries):
    executable = shutil.which('matugen', path=search_path(binaries))
    hint = f'Install Matugen 4.2.0 first: {shlex.quote(str(ROOT / "scripts/install-matugen.sh"))}'
    if not executable:
        raise RuntimeError(hint)
    result = subprocess.run([executable, '--version'], capture_output=True, text=True, timeout=10)
    if result.returncode or result.stdout.strip() != 'matugen 4.2.0':
        raise RuntimeError(f'Matugen 4.2.0 is required (found {result.stdout.strip() or executable}). {hint}')


def check_runtime(bundle):
    # Load the actual installed QML tree, including all widget previews. No start(),
    # generation, Apply or Undo is called. Qt uses isolated settings and caches.
    probe = '''
import sys
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtWidgets import QApplication
sys.path.insert(0, str(Path(sys.argv[1]) / 'scripts'))
from orbital_theme_editor import Editor
app = QApplication([])
editor = Editor()
engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty('editor', editor)
engine.load(QUrl.fromLocalFile(str(Path(sys.argv[1]) / 'ui/theme-editor.qml')))
loaded = bool(engine.rootObjects())
for window in engine.rootObjects():
    window.close()
editor.shutdown()
del engine
sys.exit(0 if loaded else 1)
'''
    with tempfile.TemporaryDirectory(prefix='orbital-runtime-check-') as temporary:
        environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                           PYTHONDONTWRITEBYTECODE='1',
                           QT_NO_XDG_DESKTOP_PORTAL='1', QT_ACCESSIBILITY='0',
                           XDG_CONFIG_HOME=f'{temporary}/config', XDG_DATA_HOME=f'{temporary}/data',
                           XDG_CACHE_HOME=f'{temporary}/cache')
        result = subprocess.run([sys.executable, '-c', probe, str(bundle)], env=environment,
                                capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError('The editor could not load. Install system PyQt6 with QtQml/QtQuick/QtWidgets, '
                           'Qt Quick Controls/Layouts, Kirigami and Qt5Compat.GraphicalEffects '
                           '(see README.md).\n' + result.stderr.strip())


def desktop_string(value):
    return value.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')


def desktop_command(path):
    # Desktop entry quoting is different from shell quoting; the string escape
    # layer is decoded before Exec quoting and percent field-code expansion.
    text = str(path)
    if '=' in text:
        raise ValueError('The executable installation path cannot contain "=" (Desktop Entry specification).')
    text = text.replace('%', '%%')
    for character in ('\\', '"', '`', '$'):
        text = text.replace(character, '\\' + character)
    return desktop_string(f'"{text}"')


def launchers(paths):
    bundle, command, desktop, icon = paths
    wrapper = (f'#!/bin/sh\n# SPDX-License-Identifier: MIT\n# Installed by {APP_ID}\n'
               f'PATH={shlex.quote(str(command.parent) + ":" + str(Path.home() / ".local/bin"))}'
               ':"${PATH:-/usr/local/bin:/usr/bin:/bin}"\nexport PATH\n'
               f'exec {shlex.quote(sys.executable)} '
               f'{shlex.quote(str(bundle / "scripts/orbital-theme"))} "$@"\n')
    entry = (f'[Desktop Entry]\nType=Application\nVersion=1.0\n'
             'Name=Orbital Palette\nName[ru]=Палитра Orbital\n'
             'Comment=Tune and preview desktop colors with Matugen\n'
             'Comment[ru]=Настройка и предпросмотр цветов рабочего стола\n'
             f'Exec={desktop_command(command)} edit\n'
             f'TryExec={desktop_string(str(command))}\nIcon={APP_ID}\n'
             'Terminal=false\nStartupNotify=true\nCategories=Settings;DesktopSettings;Qt;\n'
             'Keywords=Orbital;Matugen;palette;theme;colors;\n'
             'Keywords[ru]=Orbital;Matugen;палитра;тема;цвета;\n')
    return {command: (wrapper.encode(), 0o755), desktop: (entry.encode(), 0o644),
            icon: ((ROOT / 'assets/icons' / f'{APP_ID}.svg').read_bytes(), 0o644)}


def copy_bundle(destination):
    for directory in ('ui', 'assets/palettes', 'assets/kde', 'assets/konsole', 'LICENSES', 'widgets'):
        shutil.copytree(ROOT / directory, destination / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in ('LICENSE', 'THIRD_PARTY.md', 'README.md'):
        shutil.copy2(ROOT / name, destination / name)
    scripts = destination / 'scripts'
    scripts.mkdir()
    for name in ('orbital-theme', 'orbital_themes.py', 'orbital_theme_editor.py',
                 'install-app.sh', 'install_app.py', 'install-matugen.sh'):
        shutil.copy2(ROOT / 'scripts' / name, scripts / name)
    (destination / 'assets/icons').mkdir()
    shutil.copy2(ROOT / 'assets/icons' / f'{APP_ID}.svg', destination / 'assets/icons' / f'{APP_ID}.svg')
    (destination / 'assets/wallpaper').mkdir()
    for theme in ('orbital', 'orbital-light'):
        for resolution in ('3000x2000', '2560x1440'):
            name = f'{theme}-{resolution}.png'
            shutil.copy2(ROOT / 'assets/wallpaper' / name, destination / 'assets/wallpaper' / name)


def remove(path):
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def commit(changes):
    """Rename on each target's filesystem, retaining originals until all succeed."""
    backups = []
    try:
        for target, source in changes:
            target.parent.mkdir(parents=True, exist_ok=True)
            backup_dir = Path(tempfile.mkdtemp(prefix=f'.{target.name}-backup-', dir=target.parent))
            previous = backup_dir / 'previous'
            try:
                if exists(target):
                    target.rename(previous)
            except BaseException:
                backup_dir.rmdir()
                raise
            backups.append((target, previous, backup_dir))
            if source is not None:
                source.rename(target)
    except BaseException:
        # If restoration itself fails, leave backups available for recovery.
        for target, previous, backup_dir in reversed(backups):
            remove(target)
            if exists(previous):
                previous.rename(target)
            backup_dir.rmdir()
        raise
    for _, _, backup_dir in backups:
        shutil.rmtree(backup_dir)


def refresh_menu(desktop, kde=True):
    commands = [('update-desktop-database', str(desktop.parent))]
    if kde:
        commands.append(('kbuildsycoca6',))
        # KIconLoader keeps icons in running applications cached by name. Notify
        # Desktop and Panel listeners after replacing an icon with the same ID.
        for group in (0, 4):
            commands.append(('dbus-send', '--session', '--type=signal', '/KIconLoader',
                             'org.kde.KIconLoader.iconChanged', f'int32:{group}'))
    for command in commands:
        if shutil.which(command[0]):
            try:
                subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
            except (OSError, subprocess.SubprocessError) as error:
                print(f'Warning: menu cache refresh failed ({command[0]}): {error}', file=sys.stderr)


def install(paths):
    bundle, command, desktop, _ = paths
    check_ownership(paths)
    files = launchers(paths)
    check_matugen(command.parent)
    bundle.parent.mkdir(parents=True, exist_ok=True)
    staged_files = []
    try:
        with tempfile.TemporaryDirectory(prefix='.orbital-install-', dir=bundle.parent) as temporary:
            candidate = Path(temporary) / 'app'
            candidate.mkdir()
            copy_bundle(candidate)
            check_runtime(candidate)
            (candidate / MANIFEST).write_text(json.dumps({
                'application': APP_ID, 'version': 1,
                'files': {str(path): fingerprint(contents) for path, (contents, _) in files.items()},
            }, indent=2) + '\n')
            for path, (contents, mode) in files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(prefix=f'.{path.stem}-', suffix=path.suffix,
                                                 dir=path.parent, delete=False) as handle:
                    prepared = Path(handle.name)
                    staged_files.append((path, prepared))
                    handle.write(contents)
                    os.fchmod(handle.fileno(), mode)
            if shutil.which('desktop-file-validate'):
                validation = subprocess.run(['desktop-file-validate', str(dict(staged_files)[desktop])],
                                            capture_output=True, text=True, timeout=10)
                if validation.returncode:
                    raise RuntimeError('Invalid desktop entry:\n' + validation.stdout + validation.stderr)
            # Recheck just before replacing the live installation.
            check_ownership(paths)
            commit([(bundle, candidate), *staged_files])
    finally:
        for _, prepared in staged_files:
            prepared.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='install-app.sh',
                                     description='Install Orbital Palette for the current user, without sudo.')
    parser.add_argument('--prefix', type=Path, help='Use DIR/bin and DIR/share instead of the default user directories')
    parser.add_argument('--uninstall', action='store_true', help='Remove the app; keep saved themes, images and backups')
    args = parser.parse_args(argv)
    if sys.version_info < (3, 10):
        parser.exit(1, 'Orbital requires Python 3.10 or newer.\n')
    try:
        paths = locations(args.prefix)
        if args.uninstall:
            check_ownership(paths)
            commit([(path, None) for path in reversed(paths) if exists(path)])
            print('Orbital Palette removed. Saved themes, images and backups were preserved.')
        else:
            install(paths)
            print(f'Installed Orbital Palette (Палитра Orbital): {paths[0]}')
            print(f'Launch: {shlex.quote(str(paths[1]))} edit')
        refresh_menu(paths[2], kde=args.prefix is None)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        details = getattr(error, 'stderr', None)
        print(f'install-app: {error}' + (f'\n{details.strip()}' if details else ''), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
