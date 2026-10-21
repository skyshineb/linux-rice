# SPDX-License-Identifier: MIT
"""Application lifecycle checks use only temporary prefixes and isolated Qt state."""

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
import install_app as installer
from theme_fixtures import material_output


class AppInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='orbital-install-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.prefix = self.root / 'Палитра Orbital'
        self.paths = installer.locations(self.prefix)
        self.bundle, self.command, self.desktop, self.icon = self.paths
        self.command.parent.mkdir(parents=True)
        matugen = self.command.parent / 'matugen'
        matugen.write_text(f'#!{sys.executable}\nimport sys\n'
                           f'print("matugen 4.2.0" if "--version" in sys.argv else {material_output()!r})\n')
        matugen.chmod(0o755)
        self.environment = dict(os.environ, PATH='/usr/bin:/bin',
                                XDG_DATA_HOME=str(self.prefix / 'share'),
                                XDG_CONFIG_HOME=str(self.root / 'config'),
                                XDG_CACHE_HOME=str(self.root / 'cache'),
                                QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                QT_NO_XDG_DESKTOP_PORTAL='1', QT_ACCESSIBILITY='0')
        environment = patch.dict(os.environ, self.environment)
        environment.start()
        self.addCleanup(environment.stop)

    def invoke(self, *arguments, runtime=False):
        with contextlib.ExitStack() as stack:
            if not runtime:
                stack.enter_context(patch.object(installer, 'check_runtime'))
            stack.enter_context(patch.object(installer, 'refresh_menu'))
            output = stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            errors = stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            code = installer.main(['--prefix', str(self.prefix), *arguments])
        return code, output.getvalue() + errors.getvalue()

    def install(self):
        code, output = self.invoke()
        self.assertEqual(code, 0, output)

    def snapshot(self):
        return {str(path.relative_to(self.prefix)): path.read_bytes()
                for path in self.prefix.rglob('*') if path.is_file()}

    def test_default_locations_honor_xdg_without_changing_the_user_bin(self):
        with patch.object(Path, 'home', return_value=self.root / 'user'):
            bundle, command, desktop, icon = installer.locations()
        self.assertEqual(bundle, self.prefix / 'share/orbital-theme-editor')
        self.assertEqual(command, self.root / 'user/.local/bin/orbital-theme')
        self.assertEqual(desktop.parent, self.prefix / 'share/applications')
        self.assertEqual(icon.name, f'{installer.APP_ID}.svg')

    def test_update_and_uninstall_preserve_saved_themes_and_other_files(self):
        saved = self.prefix / 'share/orbital/themes/personal.json'
        saved.parent.mkdir(parents=True)
        saved.write_text('keep my palette and backups')
        unrelated = self.desktop.parent / 'unrelated.desktop'
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text('keep another application')
        self.install()
        self.assertTrue(os.access(self.command, os.X_OK))
        (self.bundle / 'obsolete-version.txt').write_text('old resource')
        self.install()
        self.assertFalse((self.bundle / 'obsolete-version.txt').exists())
        self.assertEqual(saved.read_text(), 'keep my palette and backups')
        # The installed copy also contains its uninstaller; no Qt or Matugen is
        # required to remove it, and the project is not involved in this command.
        result = subprocess.run([str(self.bundle / 'scripts/install-app.sh'),
                                 '--prefix', str(self.prefix), '--uninstall'],
                                capture_output=True, text=True, timeout=15, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(all(not path.exists() for path in self.paths))
        self.assertEqual(saved.read_text(), 'keep my palette and backups')
        self.assertEqual(unrelated.read_text(), 'keep another application')
        self.assertTrue((self.command.parent / 'matugen').exists())
        self.assertEqual(self.invoke('--uninstall')[0], 0)

    def test_foreign_files_directories_and_symlinks_are_never_replaced(self):
        for target in self.paths:
            with self.subTest(target=target):
                target.parent.mkdir(parents=True, exist_ok=True)
                if target == self.bundle:
                    target.mkdir()
                else:
                    target.write_text('another application')
                code, output = self.invoke()
                self.assertEqual(code, 1, output)
                self.assertIn('Refusing', output)
                if target == self.bundle:
                    self.assertEqual(list(target.iterdir()), [])
                    target.rmdir()
                else:
                    self.assertEqual(target.read_text(), 'another application')
                    target.unlink()
        external = self.root / 'external'
        external.write_text('outside installation')
        self.command.symlink_to(external)
        self.assertEqual(self.invoke()[0], 1)
        self.assertTrue(self.command.is_symlink())
        self.assertEqual(external.read_text(), 'outside installation')

    def test_manually_modified_launcher_is_preserved_on_update_and_removal(self):
        self.install()
        self.desktop.write_text(self.desktop.read_text() + '# my menu customization\n')
        before = self.snapshot()
        for arguments in ((), ('--uninstall',)):
            self.assertEqual(self.invoke(*arguments)[0], 1)
            self.assertEqual(self.snapshot(), before)

    def test_dependency_failure_keeps_the_previous_installation(self):
        self.install()
        before = self.snapshot()
        with patch.object(installer, 'check_runtime', side_effect=RuntimeError('Missing Kirigami')):
            code, output = self.invoke(runtime=True)
        self.assertEqual(code, 1)
        self.assertIn('Missing Kirigami', output)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(list(self.bundle.parent.glob('.orbital-install-*')), [])

    def test_missing_matugen_reports_install_command_without_creating_app(self):
        (self.command.parent / 'matugen').unlink()
        with patch.object(Path, 'home', return_value=self.root / 'user'):
            code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn('install-matugen.sh', output)
        self.assertFalse(self.bundle.exists())

    def test_late_commit_failure_restores_every_previous_file(self):
        self.install()
        (self.bundle / 'previous-version.txt').write_text('restore this too')
        before = self.snapshot()
        rename = Path.rename

        def fail_on_new_menu(path, target):
            if target == self.desktop and path.name.startswith(f'.{installer.APP_ID}-'):
                raise OSError('simulated final rename failure')
            return rename(path, target)

        with patch.object(Path, 'rename', fail_on_new_menu):
            code, output = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn('simulated final rename failure', output)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(any('backup-' in path.name for path in self.prefix.rglob('*')))

    def test_actual_installed_gui_and_cli_work_after_source_is_deleted(self):
        try:
            from PyQt6.QtQuick import QQuickWindow
        except ImportError:
            self.skipTest('PyQt6 is required for the installed GUI smoke test')
        source = self.root / 'source checkout'
        source.mkdir()
        installer.copy_bundle(source)
        result = subprocess.run([str(source / 'scripts/install-app.sh'), '--prefix', str(self.prefix)],
                                capture_output=True, text=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        shutil.rmtree(source)
        listed = subprocess.run([str(self.command), 'list'], capture_output=True, text=True,
                                timeout=10, cwd=self.root)
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertIn('orbital-dark', listed.stdout)
        self.assertIn('orbital-light', listed.stdout)
        manifest = json.loads((self.bundle / installer.MANIFEST).read_text())
        self.assertEqual(manifest['application'], installer.APP_ID)
        if shutil.which('desktop-file-validate'):
            validated = subprocess.run(['desktop-file-validate', str(self.desktop)],
                                       capture_output=True, text=True, timeout=5)
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)

        # A startup hook exercises the real installed entry point and closes its
        # offscreen window after checking the previews and asynchronous Matugen.
        hook = self.root / 'startup-hook'
        hook.mkdir()
        report = self.root / 'gui-result.json'
        (hook / 'sitecustomize.py').write_text('''
import json, os, time, traceback
from pathlib import Path
from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtQml import QQmlEngine
from PyQt6.QtWidgets import QApplication
original = QApplication.exec
def checked_exec(app):
    deadline = time.monotonic() + 10
    def finish():
        try:
            assert app.desktopFileName() == 'org.orbital.ThemeEditor'
            assert not app.windowIcon().pixmap(32, 32).isNull()
            window = next(w for w in app.allWindows() if w.isVisible())
            tabs = window.findChild(QObject, 'previewTabs')
            assert tabs.property('count') == 3
            for index in range(3):
                assert tabs.setProperty('currentIndex', index)
                app.processEvents()
            editor = QQmlEngine.contextForObject(window).engine().rootContext().contextProperty('editor')
            if not editor.canApply and not editor.error and time.monotonic() < deadline:
                QTimer.singleShot(50, finish)
                return
            assert editor.canApply, editor.error
            outcome = {'ok': True, 'tabs': 3}
        except BaseException:
            outcome = {'ok': False, 'error': traceback.format_exc()}
        Path(os.environ['ORBITAL_TEST_REPORT']).write_text(json.dumps(outcome))
        app.quit()
    def generate():
        window = next(w for w in app.allWindows() if w.isVisible())
        editor = QQmlEngine.contextForObject(window).engine().rootContext().contextProperty('editor')
        editor.setOption('source_kind', 'color')
        editor.setOption('color', '#67C4DE')
    QTimer.singleShot(0, generate)
    QTimer.singleShot(100, finish)
    return original()
QApplication.exec = checked_exec
''')
        environment = dict(self.environment, PYTHONPATH=str(hook), ORBITAL_TEST_REPORT=str(report))
        launch = ([shutil.which('gio'), 'launch', str(self.desktop)] if shutil.which('gio')
                  else [str(self.command), 'edit'])
        launched = subprocess.run(launch, env=environment,
                                  capture_output=True, text=True, timeout=15, cwd=self.root)
        self.assertEqual(launched.returncode, 0, launched.stdout + launched.stderr)
        self.assertTrue(report.exists(), launched.stderr)
        self.assertEqual(json.loads(report.read_text()), {'ok': True, 'tabs': 3}, launched.stderr)
        for warning in ('ReferenceError', 'TypeError', 'is not installed', 'is not a type'):
            self.assertNotIn(warning, launched.stderr)


if __name__ == '__main__':
    unittest.main()
