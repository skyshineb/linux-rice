# SPDX-License-Identifier: MIT
"""Installer orchestration and widget transactions in temporary homes only."""

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import install as installer
from orbital_user import require_user

ROOT = Path(__file__).resolve().parents[1]


class UserContextTests(unittest.TestCase):
    def test_elevated_or_saved_ids_are_rejected_before_installation(self):
        for uids, gids in (((1001, 0, 0), (1001, 1001, 1001)),
                           ((0, 0, 0), (0, 0, 0)),
                           ((1001, 1001, 0), (1001, 1001, 1001)),
                           ((1001, 1001, 1001), (1001, 0, 0))):
            with self.subTest(uids=uids, gids=gids), \
                    patch('orbital_user.os.getresuid', return_value=uids), \
                    patch('orbital_user.os.getresgid', return_value=gids), \
                    patch.object(installer, 'preflight') as preflight, \
                    patch.object(installer, 'execute') as execute, \
                    contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(installer.main(['all']), 1)
                self.assertIn(str(uids), errors.getvalue())
                self.assertIn('/usr/bin/env', errors.getvalue())
                preflight.assert_not_called()
                execute.assert_not_called()

    def test_setuid_env_is_detected_even_when_python_was_called_directly(self):
        with patch('orbital_user.os.getresuid', return_value=(1001, 1001, 1001)), \
                patch('orbital_user.os.getresgid', return_value=(1001, 1001, 1001)), \
                patch('orbital_user.Path.stat', return_value=os.stat_result((0o104755,) + (0,) * 9)):
            with self.assertRaisesRegex(RuntimeError, 'special permission bits .*4755'):
                require_user()

    def test_moon_refuses_elevated_install_before_any_state_or_units(self):
        import orbital_moon_launcher as moon
        with tempfile.TemporaryDirectory() as temporary, \
                patch('orbital_user.os.getresuid', return_value=(1001, 0, 0)), \
                patch.object(moon, 'targets') as targets, patch.object(moon, 'systemctl') as systemctl:
            root = Path(temporary)
            paths = moon.Locations(root / 'user', root / 'config', root / 'data', root / 'state')
            for action in (moon.install, moon.update, moon.uninstall):
                with self.assertRaisesRegex(RuntimeError, 'UID .*1001, 0, 0'):
                    action(paths)
            self.assertEqual(list(root.iterdir()), [])
            targets.assert_not_called()
            systemctl.assert_not_called()


class InstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='orbital-components-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.scripts = self.root / 'scripts'
        self.scripts.mkdir()
        self.log = self.root / 'calls.jsonl'
        stub = (f'#!{sys.executable}\nimport json, os, pathlib, sys\n'
                'name = pathlib.Path(sys.argv[0]).name\n'
                'with open(os.environ["ORBITAL_TEST_LOG"], "a") as f: f.write(json.dumps([name, *sys.argv[1:]]) + "\\n")\n'
                'if name == os.environ.get("ORBITAL_FAIL_STEP"): sys.exit(7)\n'
                'if name in ("apply-user.sh", "upgrade-widgets.sh"): print("Restore with: restore-test snapshot-test")\n')
        for name in ('install-matugen.sh', 'install-app.sh', 'install-icons.sh',
                     'apply-user.sh', 'upgrade-widgets.sh', 'orbital-moon'):
            path = self.scripts / name
            path.write_text(stub)
            path.chmod(0o755)
        for replacement in (patch.object(installer, 'ROOT', self.root),
                            patch.object(installer, 'matugen_ready', return_value=False),
                            patch.dict(os.environ, ORBITAL_TEST_LOG=str(self.log))):
            replacement.start()
            self.addCleanup(replacement.stop)

    def invoke(self, *arguments, prerequisites=True):
        with contextlib.ExitStack() as stack:
            if prerequisites:
                stack.enter_context(patch.object(installer, 'preflight'))
            stdout = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stderr = stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            code = installer.main(list(arguments))
        calls = [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []
        return code, calls, stdout.getvalue() + stderr.getvalue()

    def test_all_installs_dependencies_once_and_moon_after_the_desktop(self):
        code, calls, text = self.invoke('all', '--theme', 'orbital-light')
        self.assertEqual(code, 0, text)
        self.assertEqual(calls, [['install-matugen.sh'], ['install-app.sh'], ['install-icons.sh'],
                                 ['apply-user.sh', '--theme', 'orbital-light'], ['orbital-moon', 'install']])
        self.assertNotIn('battery', str(calls))
        self.assertNotIn('sddm', str(calls))

    def test_individual_widgets_are_forwarded_without_theme_or_other_packages(self):
        for name in installer.WIDGETS:
            with self.subTest(name=name):
                self.log.unlink(missing_ok=True)
                code, calls, text = self.invoke(name)
                self.assertEqual(code, 0, text)
                self.assertEqual(calls, [['upgrade-widgets.sh', name]])

    def test_palette_dependency_failure_happens_before_any_installer_runs(self):
        with patch.object(installer.install_app, 'check_ownership'), \
                patch.object(installer.install_app, 'check_runtime', side_effect=RuntimeError('Missing Kirigami')):
            code, calls, text = self.invoke('palette', prerequisites=False)
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        self.assertIn('Missing Kirigami', text)

    def test_missing_desktop_font_is_reported_before_downloading_icons(self):
        def result(*command):
            return 'Noto Sans' if command[0] == 'fc-match' else 'ready'
        with patch.object(installer, 'require_commands'), patch.object(installer, 'require_qml'), \
                patch.object(installer, 'output', side_effect=result):
            code, calls, text = self.invoke('desktop', prerequisites=False)
        self.assertEqual(code, 1)
        self.assertEqual(calls, [])
        self.assertIn('IBM Plex Sans', text)

    def test_moon_does_not_require_palette_or_widget_dependencies(self):
        with patch.object(installer, 'output', return_value='ready'), \
                patch.object(installer, 'require_commands'), \
                patch.object(installer.moon, 'check_ownership'), \
                patch.object(installer.moon, 'targets', return_value=[{'location': 'bottom'}]), \
                patch.object(installer.moon.Locations, 'current', return_value=installer.moon.Locations(
                    self.root, self.root / 'config', self.root / 'data', self.root / 'state')), \
                patch.object(installer.install_app, 'check_runtime') as runtime, \
                patch.object(installer, 'require_qml') as qml:
            installer.preflight(installer.steps_for('moon'))
            runtime.assert_not_called()
            qml.assert_not_called()

    def test_late_failure_stops_and_reports_completed_steps_and_recovery(self):
        with patch.dict(os.environ, ORBITAL_FAIL_STEP='orbital-moon'):
            code, calls, text = self.invoke('all')
        self.assertEqual(code, 1)
        self.assertEqual(calls[-1], ['orbital-moon', 'install'])
        self.assertIn('stopped at moon', text)
        self.assertIn('Completed steps: matugen, palette, icons, desktop', text)
        self.assertIn('restore-test snapshot-test', text)
        self.assertIn('--uninstall', text)

    def test_start_failure_also_reports_completed_components(self):
        (self.scripts / 'orbital-moon').unlink()
        # The interpreter starts successfully but cannot open the missing file.
        code, _, text = self.invoke('all')
        self.assertEqual(code, 1)
        self.assertIn('Completed steps: matugen, palette, icons, desktop', text)
        (self.scripts / 'install-icons.sh').unlink()
        self.log.unlink()
        code, calls, text = self.invoke('all')
        self.assertEqual(code, 1)
        self.assertEqual(calls, [['install-matugen.sh'], ['install-app.sh']])
        self.assertIn('stopped at icons', text)
        self.assertIn('--uninstall', text)

    def test_help_and_invalid_options_do_not_start_installation(self):
        code, calls, _ = self.invoke()
        self.assertEqual((code, calls), (0, []))
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            installer.main(['cpu', '--theme', 'orbital-light'])
        self.assertEqual(error.exception.code, 2)
        self.assertFalse(self.log.exists())


class WidgetUpgradeTests(unittest.TestCase):
    def test_selected_widget_upgrade_and_failure_restore_real_snapshots(self):
        with tempfile.TemporaryDirectory(prefix='orbital-widget-upgrade-test-') as temporary:
            root = Path(temporary)
            scripts = root / 'scripts'
            scripts.mkdir()
            for name in ('upgrade-widgets.sh', 'snapshot.py', 'orbital_themes.py', 'orbital_user.py'):
                shutil.copy2(ROOT / 'scripts' / name, scripts / name)
            binaries = root / 'bin'
            binaries.mkdir()
            home = root / 'home'
            home.mkdir()
            environment = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
                               XDG_DATA_HOME=str(home / '.local/share'),
                               PATH=str(binaries) + os.pathsep + os.environ['PATH'],
                               ORBITAL_TEST_LOG=str(root / 'calls.jsonl'))
            packages = home / '.local/share/plasma/plasmoids'
            for name in ('cpu', 'memory'):
                path = packages / f'org.orbital.{name}/contents/ui/main.qml'
                path.parent.mkdir(parents=True)
                path.write_text('previous ' + name)
            config = home / '.config/plasma-org.kde.plasma.desktop-appletsrc'
            config.parent.mkdir()
            config.write_text('my panel and settings')
            stub = (f'#!{sys.executable}\nimport json, os, pathlib, sys\n'
                    'name = pathlib.Path(sys.argv[0]).name\n'
                    'with open(os.environ["ORBITAL_TEST_LOG"], "a") as f: f.write(json.dumps([name, *sys.argv[1:]]) + "\\n")\n'
                    'if name == "qdbus6": print("ready")\n'
                    'if name == "kpackagetool6":\n'
                    '    widget = pathlib.Path(sys.argv[-1]).name\n'
                    '    p = pathlib.Path(os.environ["HOME"]) / ".local/share/plasma/plasmoids" / widget / "contents/ui/main.qml"\n'
                    '    p.parent.mkdir(parents=True, exist_ok=True)\n'
                    '    p.write_text("new " + widget)\n'
                    '    if os.environ.get("ORBITAL_FAIL_STEP"): sys.exit(7)\n')
            for name in ('qdbus6', 'systemctl', 'kpackagetool6'):
                (binaries / name).write_text(stub)
                (binaries / name).chmod(0o755)

            def invoke(widget):
                return subprocess.run([str(scripts / 'upgrade-widgets.sh'), widget], env=environment,
                                      capture_output=True, text=True, timeout=15)

            for _ in range(2):
                result = invoke('cpu')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((packages / 'org.orbital.memory/contents/ui/main.qml').read_text(), 'previous memory')
            self.assertEqual(config.read_text(), 'my panel and settings')
            calls = [json.loads(line) for line in (root / 'calls.jsonl').read_text().splitlines()]
            upgrades = [call for call in calls if call[0] == 'kpackagetool6']
            self.assertEqual(len(upgrades), 2)
            self.assertTrue(all('--upgrade' in call and call[-1].endswith('org.orbital.cpu') for call in upgrades))
            self.assertEqual(calls.count(['systemctl', '--user', 'restart', 'plasma-plasmashell.service']), 2)
            environment['ORBITAL_FAIL_STEP'] = 'package'
            result = invoke('battery')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((packages / 'org.orbital.battery').exists())
            self.assertEqual(config.read_text(), 'my panel and settings')
            self.assertEqual((packages / 'org.orbital.cpu/contents/ui/main.qml').read_text(), 'new org.orbital.cpu')
