# SPDX-License-Identifier: MIT
"""Optional native integration checks; always launch on a private D-Bus session."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from orbital_themes import Themes, Runner, builtin, rgb, read_ini, render_terminal, scheme_id, write_text


class IsolatedRunner(Runner):
    def run(self, *args, check=True):
        # No Plasma Shell or user systemd runs on this private bus. All color,
        # desktop-style and config tools below are the actual installed programs.
        if args[0] == 'qdbus6' and len(args) > 1 and args[1] == 'org.kde.plasmashell':
            return 'ready' if args[-1] == 'print("ready")' else ''
        if args[0] == 'systemctl':
            return ''
        return super().run(*args, check=check)


class NativeKdeTests(unittest.TestCase):
    def setUp(self):
        if not os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
            self.fail('A private D-Bus session is required')
        for command in ('qdbus6', 'konsole', 'kwriteconfig6', 'plasma-apply-colorscheme',
                        'plasma-apply-desktoptheme', 'systemctl'):
            if not shutil.which(command):
                self.skipTest(f'Native KDE command not installed: {command}')
        temporary = tempfile.TemporaryDirectory(prefix='orbital-native-tests-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        environment = patch.dict(os.environ, {
            'XDG_CONFIG_HOME': str(self.root / 'config'),
            'XDG_DATA_HOME': str(self.root / 'data'),
            'XDG_CACHE_HOME': str(self.root / 'cache'),
            'QT_QPA_PLATFORM': 'offscreen', 'DISPLAY': '', 'WAYLAND_DISPLAY': '',
            'QT_NO_XDG_DESKTOP_PORTAL': '1', 'QT_ACCESSIBILITY': '0',
        })
        environment.start()
        self.addCleanup(environment.stop)

    def test_native_palettes_reapply_and_exact_rollback(self):
        manager = Themes(runner=IsolatedRunner())
        write_text(manager.config / 'kdeglobals',
                   '[General]\nColorScheme=BreezeLight\nAccentColor=103,196,222\nfont=Keep Me\n')
        write_text(manager.config / 'plasmarc', '[Theme]\nname=default\n')
        def state():
            return {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*')
                    if path.is_file() and 'backups' not in path.parts}
        before = state()
        first = None
        for mode in ('dark', 'light', 'light'):
            palette = builtin(f'orbital-{mode}')
            backup = manager.apply(palette)
            first = first or backup
            config = read_ini(manager.config / 'kdeglobals')
            self.assertEqual(config['General']['ColorScheme'], manager.active()['scheme'])
            for section, background in (('Colors:Window', 'window'), ('Colors:View', 'canvas'),
                                        ('Colors:Selection', 'selected')):
                self.assertEqual(config[section]['ForegroundNormal'], rgb(palette['colors']['text']))
                self.assertEqual(config[section]['BackgroundNormal'], rgb(palette['colors'][background]))
            self.assertEqual(config['General']['font'], 'Keep Me')
        manager.restore(first)
        self.assertEqual(state(), before)

    def test_konsole_tabs_remain_managed_after_consecutive_updates(self):
        manager = Themes()
        profile = manager.data / 'konsole/Orbital-Test.profile'
        write_text(profile, '[General]\nName=Orbital Test\nX-Orbital-Managed=true\n'
                   'Command=/usr/bin/sleep 30\n[Appearance]\nColorScheme=Breeze\nFont=Monospace,11\n')
        original = profile.read_bytes()
        with tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(['konsole', '--separate', '--profile', str(profile)],
                                       stdout=subprocess.DEVNULL, stderr=errors)
            try:
                sessions = []
                for _ in range(50):
                    self.assertIsNone(process.poll(), 'Konsole exited before registering its tab')
                    sessions = manager.sessions()
                    if sessions:
                        break
                    time.sleep(.1)
                self.assertEqual(len(sessions), 1)
                session = sessions[0]
                runner = Runner()
                def query(method):
                    return runner.run('qdbus6', session['service'], session['path'],
                                      f'org.kde.konsole.Session.{method}')
                shell = query('processId')
                self.assertTrue(shell.isdigit())
                for mode in ('light', 'dark'):
                    palette = builtin(f'orbital-{mode}')
                    name = scheme_id(palette)
                    # Konsole started before these new schemes existed.
                    write_text(manager.data / 'konsole' / f'{name}.colorscheme', render_terminal(palette))
                    sessions = Themes().sessions()
                    self.assertEqual(len(sessions), 1)
                    manager.update_sessions(sessions, name)
                    for _ in range(20):
                        if query('profile') == 'Orbital':
                            break
                        time.sleep(.05)
                    self.assertEqual(query('profile'), 'Orbital')
                    self.assertEqual(query('processId'), shell)
                self.assertEqual(profile.read_bytes(), original)
            finally:
                process.terminate()
                process.wait(timeout=5)


if __name__ == '__main__':
    if sys.argv[1:] == ['--private-bus']:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        if not shutil.which('dbus-run-session'):
            raise SystemExit('dbus-run-session is required for native integration checks')
        raise SystemExit(subprocess.call(['dbus-run-session', '--', sys.executable,
                                         str(Path(__file__).resolve()), '--private-bus']))
