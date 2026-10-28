# SPDX-License-Identifier: MIT
"""Component-aware orchestration of the existing Orbital installers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import sysconfig

import install_app
import orbital_moon_launcher as moon
from orbital_themes import Themes
from orbital_user import require_user

ROOT = Path(__file__).resolve().parent.parent
WIDGETS = ('cpu', 'memory', 'disk', 'battery')
TARGETS = ('all', 'desktop', 'widgets', *WIDGETS, 'moon', 'palette', 'icons', 'matugen')


@dataclass(frozen=True)
class Step:
    name: str
    command: tuple[str, ...]


def steps_for(target, theme=None):
    names = {'all': ('matugen', 'palette', 'icons', 'desktop', 'moon'),
             'desktop': ('icons', 'desktop'), 'palette': ('matugen', 'palette')}.get(target, (target,))
    result = []
    for name in names:
        if name in WIDGETS or name == 'widgets':
            command = (str(ROOT / 'scripts/upgrade-widgets.sh'),) + (() if name == 'widgets' else (name,))
        elif name == 'moon':
            command = (sys.executable, str(ROOT / 'scripts/orbital-moon'), 'install')
        else:
            script = {'desktop': 'apply-user.sh', 'palette': 'install-app.sh',
                      'icons': 'install-icons.sh', 'matugen': 'install-matugen.sh'}[name]
            command = (str(ROOT / 'scripts' / script),)
            if name == 'desktop' and theme:
                command += ('--theme', theme)
        result.append(Step(name, command))
    return result


def require_commands(*commands):
    missing = [command for command in commands if shutil.which(command) is None]
    if missing:
        raise RuntimeError('Required commands not found: ' + ', '.join(missing)
                           + '. See README prerequisites.')


def output(*command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError(f'{command[0]} failed: {(result.stderr or result.stdout).strip()}')
    return result.stdout.strip()


def matugen_ready():
    executable = shutil.which('matugen')
    if not executable:
        return False
    try:
        result = subprocess.run([executable, '--version'], capture_output=True, text=True, timeout=10)
        return result.returncode == 0 and result.stdout.strip() == 'matugen 4.2.0'
    except (OSError, subprocess.SubprocessError):
        return False


def require_qml(modules):
    roots = [Path(path) for variable in ('QML_IMPORT_PATH', 'QML2_IMPORT_PATH')
             for path in os.environ.get(variable, '').split(os.pathsep) if path]
    if shutil.which('qtpaths6'):
        roots.append(Path(output('qtpaths6', '--query', 'QT_INSTALL_QML')))
    roots += [Path('/usr/lib/qt6/qml'), Path('/usr/lib64/qt6/qml'),
              Path('/usr/lib') / str(sysconfig.get_config_var('MULTIARCH')) / 'qt6/qml']
    missing = [module for module in sorted(modules)
               if not any((root / module.replace('.', '/') / 'qmldir').is_file() for root in roots)]
    if missing:
        raise RuntimeError('Required QML modules not found: ' + ', '.join(missing)
                           + '. Install their system packages; see README prerequisites.')


def panel_inventory():
    script = ('print(JSON.stringify(panels().map(function(p){p.currentConfigGroup=["General"];'
              'return {location:p.location,managed:String(p.readConfig("OrbitalManaged","false")),'
              'widgets:p.widgets().map(function(w){return w.type;})};})));')
    return json.loads(output('qdbus6', 'org.kde.plasmashell', '/PlasmaShell',
                             'org.kde.PlasmaShell.evaluateScript', script))


def preflight(steps, theme=None):
    require_user()
    names = {step.name for step in steps}
    selected = names.intersection(WIDGETS)
    if 'desktop' in names or 'widgets' in names:
        selected.update(('cpu', 'memory', 'disk'))
    if 'widgets' in names and (Path.home() / '.local/share/plasma/plasmoids/org.orbital.battery').is_dir():
        selected.add('battery')
    if selected or names.intersection(('desktop', 'moon')):
        require_commands('qdbus6', 'systemctl')
        if output('qdbus6', 'org.kde.plasmashell', '/PlasmaShell',
                  'org.kde.PlasmaShell.evaluateScript', 'print("ready")') != 'ready':
            raise RuntimeError('A running Plasma 6 session is required.')
        output('systemctl', '--user', 'is-active', 'plasma-plasmashell.service')
    if selected:
        require_commands('kpackagetool6', 'bash')
        modules = {'QtQuick', 'org.kde.kirigami', 'org.kde.plasma.plasmoid',
                   'org.kde.plasma.core', 'org.kde.plasma.plasma5support'}
        if selected.intersection(('cpu', 'memory', 'disk')):
            modules.add('org.kde.ksysguard.sensors')
        if 'disk' in selected:
            modules.add('QtQuick.Shapes')
        if 'battery' in selected:
            modules.update(('Qt5Compat.GraphicalEffects', 'org.kde.plasma.private.battery',
                            'org.kde.plasma.private.batterymonitor',
                            'org.kde.plasma.private.brightnesscontrolplugin'))
        require_qml(modules)
    if 'desktop' in names:
        require_commands('kwriteconfig6', 'kreadconfig6', 'plasma-apply-colorscheme',
                         'plasma-apply-desktoptheme', 'fc-match')
        Themes().apply(Themes().load(theme), dry_run=True)
        for family in ('IBM Plex Sans', 'IBM Plex Mono'):
            if family not in [item.strip() for item in output('fc-match', '-f', '%{family}', family).split(',')]:
                raise RuntimeError(f'Install {family} first (fonts-ibm-plex on Ubuntu).')
        for name in ('Breeze', 'Breeze-Dark'):
            if not any((directory / name / 'gtk-3.0/gtk.css').is_file() for directory in
                       (Path.home() / '.themes', Path.home() / '.local/share/themes', Path('/usr/share/themes'))):
                raise RuntimeError(f'Install the {name} GTK theme first.')
        zshrc = Path.home() / '.zshrc'
        if (not (Path.home() / '.oh-my-zsh/oh-my-zsh.sh').is_file() or not zshrc.is_file()
                or not re.search(r'^ZSH_THEME=', zshrc.read_text(), re.M)):
            raise RuntimeError('Oh My Zsh and a ~/.zshrc with a ZSH_THEME= assignment are required.')
        panels = panel_inventory()
        bottom = [panel for panel in panels if panel['location'] == 'bottom']
        if len(bottom) != 1 or not {'org.kde.plasma.kickoff', 'org.kde.plasma.pager',
                                  'org.kde.plasma.icontasks'}.issubset(bottom[0]['widgets']):
            raise RuntimeError('Expected one bottom panel with Kickoff, Pager and Icons-only Task Manager.')
        if any(panel['location'] == 'top' and panel['managed'] != 'true' for panel in panels):
            raise RuntimeError('Refusing to replace an unmanaged top panel.')
    if 'moon' in names:
        output('systemctl', '--user', 'is-active', 'graphical-session.target')
        paths = moon.Locations.current()
        moon.check_ownership(paths)
        available = moon.targets()
        if paths.state.exists():
            if moon.target_from(moon.read_state(paths), available) is None:
                raise RuntimeError('The saved Kickoff no longer exists; uninstall Moon before selecting another.')
        elif sum(item['location'] == 'bottom' for item in available) != 1:
            raise RuntimeError('Expected one Kickoff launcher on the bottom panel.')
    if 'palette' in names:
        install_app.check_ownership(install_app.locations())
        install_app.check_runtime(ROOT)
    if 'icons' in names and not (Path.home() / '.local/share/icons/Tela-circle-blue/index.theme').is_file():
        require_commands('git', 'bash')
    if 'matugen' in names and not matugen_ready():
        if platform.system() != 'Linux' or platform.machine() != 'x86_64':
            raise RuntimeError('Install Matugen 4.2.0 from upstream for this architecture first.')
        require_commands('curl', 'sha256sum', 'tar', 'install', 'bash')


def recovery(step, log):
    commands = [line.split('Restore with: ', 1)[1] for line in log.splitlines() if 'Restore with: ' in line]
    if step.name == 'palette':
        commands.append(shlex.join((str(ROOT / 'scripts/install-app.sh'), '--uninstall')))
    elif step.name == 'moon':
        commands.append(shlex.join((str(Path.home() / '.local/bin/orbital-moon'), 'uninstall')))
    return commands


def execute(steps):
    completed = []
    for step in steps:
        print(f'Installing {step.name}…', flush=True)
        if step.name == 'matugen' and matugen_ready():
            print('Matugen 4.2.0 is already available.', flush=True)
            completed.append((step, ''))
            continue
        # Stream progress and retain only the recovery instructions, not an entire
        # potentially large upstream build log.
        log = []
        try:
            with subprocess.Popen(step.command, cwd=ROOT, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True) as process:
                for line in process.stdout:
                    print(line, end='', flush=True)
                    if 'Restore with: ' in line:
                        log.append(line)
                code = process.wait()
        except OSError as error:
            print(str(error), file=sys.stderr)
            code = 1
        if code:
            print(f'Installation stopped at {step.name} (exit {code}). The component reports its own rollback above.',
                  file=sys.stderr)
            if completed:
                print('Completed steps: ' + ', '.join(item.name for item, _ in completed) + '.', file=sys.stderr)
                for item, saved in completed:
                    for command in recovery(item, saved):
                        print(f'Recovery/removal for {item.name}: {command}', file=sys.stderr)
                print('Completed components and downloaded dependencies remain installed.', file=sys.stderr)
            return 1
        completed.append((step, ''.join(log)))
    print('Orbital installation complete. Standalone widgets can be added through Plasma’s Add Widgets menu.')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog='install.sh', description=__doc__)
    parser.add_argument('component', nargs='?', choices=TARGETS,
                        help='all = desktop + CPU/Memory/Disk + Moon + Palette; Battery and SDDM stay separate')
    parser.add_argument('--theme', metavar='THEME_ID', help='Initial palette for desktop or all')
    args = parser.parse_args(argv)
    if args.component is None:
        parser.print_help()
        return 0
    if args.theme and args.component not in ('all', 'desktop'):
        parser.error('--theme is only available for desktop and all')
    try:
        require_user()
        if sys.version_info < (3, 10):
            raise RuntimeError('Python 3.10 or newer is required.')
        os.environ['PATH'] = install_app.search_path(Path.home() / '.local/bin')
        steps = steps_for(args.component, args.theme)
        print('Checking prerequisites…', flush=True)
        preflight(steps, args.theme)
        return execute(steps)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'install: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
