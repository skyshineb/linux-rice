# SPDX-License-Identifier: MIT
"""Qt controller/QML integration without touching the user's desktop."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')

from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import orbital_themes as themes
from theme_fixtures import material_output
from test_themes import Desktop
try:
    from PyQt6.QtCore import QUrl
    from PyQt6.QtQml import QQmlApplicationEngine
    from PyQt6.QtTest import QTest, QSignalSpy
    from PyQt6.QtWidgets import QApplication
    from orbital_theme_editor import Editor
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, 'PyQt6 is required for editor tests')
class EditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='orbital-editor-test-')
        self.root = Path(self.temporary.name)
        self.desktop = Desktop(self.root)
        self.manager = themes.Themes(self.root, self.desktop, self.root / 'config', self.root / 'data',
                                     self.desktop.terminal_writer)
        self.editor = Editor(self.manager)
        self.editor._version = 'matugen 4.2.0'
        self.jobs = []
        self.patch_process = patch.object(self.editor, '_run_process', side_effect=self.fake_process)
        self.patch_process.start()
        self.patch_which = patch('orbital_themes.shutil.which', return_value='/test/matugen')
        self.patch_which.start()
        self.editors = [self.editor]

    def tearDown(self):
        for editor in self.editors:
            if editor._worker:
                editor._worker.wait(3000)
                self.app.processEvents()
            editor.shutdown()
            editor.deleteLater()
        self.app.processEvents()
        self.patch_which.stop()
        self.patch_process.stop()
        self.temporary.cleanup()

    def fake_process(self, args, success, failure):
        class Process:
            killed = False
            def kill(self):
                self.killed = True
        process = Process()
        self.jobs.append((args, success, failure, process))
        return process

    def flush(self):
        self.editor._timer.stop()
        self.editor._generate()

    def ready(self):
        self.editor.setOption('source_kind', 'color')
        self.flush()
        self.jobs[-1][1](material_output())
        self.assertTrue(self.editor.canApply)

    def wait_for(self, predicate, timeout=3000):
        deadline = time.monotonic() + timeout / 1000
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(predicate())

    def test_preview_is_isolated_and_parameter_changes_are_debounced(self):
        spy = QSignalSpy(self.editor.previewChanged)
        self.editor.setOption('source_kind', 'color')
        for value in (.1, .2, .25):
            self.editor.setOption('contrast', value)
        QTest.qWait(300)
        self.assertEqual(len(self.jobs), 1)
        self.jobs[0][1](material_output())
        self.assertEqual(len(spy), 1)
        self.assertEqual(self.editor.preview['generation']['options']['contrast'], .25)
        self.assertEqual(list(self.root.rglob('*')), [])
        self.assertEqual(self.desktop.calls, [])

    def test_stale_results_and_errors_cannot_apply_the_wrong_palette(self):
        self.editor.setOption('source_kind', 'color')
        self.flush()
        old = self.jobs[-1]
        self.editor.setOption('contrast', .5)
        self.flush()
        latest = self.jobs[-1]
        self.assertTrue(old[3].killed)
        old[1](material_output())
        self.assertFalse(self.editor.canApply)
        latest[1](material_output())
        good = self.editor.preview
        self.assertEqual(good['generation']['options']['contrast'], .5)
        self.editor.setOption('color', '#bad')
        self.flush()
        self.assertFalse(self.editor.canApply)
        self.assertEqual(self.editor.preview, good)
        self.assertIn('#RRGGBB', self.editor.error)
        self.editor.applyTheme(False)
        self.assertEqual(self.desktop.calls, [])

    def test_revisiting_parameters_uses_the_cached_palette(self):
        self.ready()
        initial = self.editor.preview
        self.editor.setOption('contrast', .25)
        self.flush()
        self.jobs[-1][1](material_output())
        jobs = len(self.jobs)
        self.editor.setOption('contrast', 0)
        self.flush()
        self.assertEqual(len(self.jobs), jobs)
        self.assertEqual(self.editor.preview, initial)

    def test_apply_and_undo_use_the_transaction_and_reopen_color_settings(self):
        self.ready()
        expected = self.editor.preview
        self.editor.applyTheme(False)
        self.wait_for(lambda: not self.editor.working)
        self.assertEqual(self.manager.load(None), expected)
        self.assertTrue(self.editor.canUndo)
        reopened = Editor(self.manager)
        self.editors.append(reopened)
        self.assertEqual(reopened.settings['source_kind'], 'color')
        self.assertEqual(reopened.settings['color'], self.editor.settings['color'])
        self.assertEqual(reopened.preview, expected)
        self.editor.undo()
        self.wait_for(lambda: not self.editor.working)
        self.assertFalse(self.editor.canUndo)
        self.assertFalse((self.manager.store / 'active.json').exists())

    def test_image_source_is_reopened_from_managed_copy_with_original_label(self):
        image = self.root / 'image with spaces.png'
        image.write_bytes(b'image fixture')
        self.editor.setOption('image', str(image))
        self.flush()
        extraction, generation = self.jobs[-2:]
        extraction[1]('#123456\n#ABCDEF\n')
        generation[1](material_output())
        self.assertEqual(self.editor.sourceColors, ['#123456', '#ABCDEF'])
        expected = self.editor.preview
        self.editor.applyTheme(False)
        self.wait_for(lambda: not self.editor.working)
        self.assertFalse(any('writeConfig("Image"' in call[-1] for call in self.desktop.calls))
        image.unlink()
        reopened = Editor(self.manager)
        self.editors.append(reopened)
        self.assertTrue(Path(reopened.settings['image']).is_file())
        self.assertEqual(reopened._source()['label'], 'image with spaces')
        self.assertEqual(reopened.preview, expected)

    def test_apply_failure_rolls_back_and_allows_retrying_the_valid_preview(self):
        self.ready()
        self.desktop.fail = 'DefaultProfile'
        self.editor.applyTheme(False)
        self.wait_for(lambda: not self.editor.working)
        self.assertIn('previous theme restored', self.editor.error)
        self.assertFalse((self.manager.store / 'active.json').exists())
        self.assertTrue(self.editor.canApply)
        self.editor.applyTheme(False)
        self.wait_for(lambda: not self.editor.working)
        self.assertEqual(self.manager.active()['id'], self.editor.preview['id'])
        self.assertFalse(self.editor.error)

    def test_missing_generator_preserves_preview_and_disables_apply(self):
        self.ready()
        previous = self.editor.preview
        with patch('orbital_themes.shutil.which', return_value=None):
            self.editor.setOption('contrast', .25)
            self.flush()
        self.assertEqual(self.editor.preview, previous)
        self.assertFalse(self.editor.canApply)
        self.assertIn('install-matugen.sh', self.editor.error)

    def test_cached_image_does_not_receive_stale_source_colors(self):
        first = self.root / 'first.png'
        second = self.root / 'second.png'
        first.write_bytes(b'first image')
        second.write_bytes(b'second image')
        self.editor.setOption('image', str(first))
        self.flush()
        self.jobs[-2][1]('#123456\n')
        self.jobs[-1][1](material_output())
        self.editor.setOption('image', str(second))
        self.flush()
        pending = self.jobs[-2]
        self.editor.setOption('image', str(first))
        self.flush()
        pending[1]('#ABCDEF\n')
        self.assertEqual(self.editor.sourceColors, ['#123456'])
        self.assertTrue(self.editor.canApply)

    def test_settings_without_a_source_wait_instead_of_showing_an_error(self):
        self.editor.setOption('mode', 'light')
        self.flush()
        self.assertFalse(self.editor.error)
        self.assertFalse(self.editor.canApply)
        self.assertFalse(self.jobs)

    def test_close_waits_for_apply_to_finish(self):
        self.ready()
        release = threading.Event()
        self.addCleanup(release.set)
        self.editor._operate(lambda: release.wait(2), 'restore')
        close = QSignalSpy(self.editor.closeReady)
        self.assertFalse(self.editor.requestClose())
        self.assertTrue(self.editor.working)
        release.set()
        self.wait_for(lambda: len(close) == 1)
        self.assertFalse(self.editor.working)

    def test_all_preview_tabs_load_and_resize_in_both_modes(self):
        engine = QQmlApplicationEngine()
        warnings = []
        engine.warnings.connect(lambda values: warnings.extend(value.toString() for value in values))
        engine.rootContext().setContextProperty('editor', self.editor)
        engine.load(QUrl.fromLocalFile(str(themes.ROOT / 'ui/theme-editor.qml')))
        self.assertTrue(engine.rootObjects())
        window = engine.rootObjects()[0]
        try:
            tabs = window.findChild(object, 'previewTabs')
            self.assertIsNotNone(tabs)
            for mode in ('dark', 'light'):
                self.editor._preview = themes.builtin(f'orbital-{mode}')
                self.editor.previewChanged.emit()
                for tab in range(3):
                    tabs.setProperty('currentIndex', tab)
                    window.resize(900, 640)
                    self.app.processEvents()
                    self.assertEqual(window.width(), 900)
                    self.assertEqual(window.height(), 640)
                    self.assertFalse(window.grabWindow().isNull())
            self.assertEqual(warnings, [])
        finally:
            window.close()
            del engine
            self.app.processEvents()


@unittest.skipIf(QApplication is None or shutil.which('matugen') is None, 'PyQt6 and Matugen required')
class NativePreviewTests(unittest.TestCase):
    def test_real_async_generation_and_cancellation_are_isolated(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory(prefix='orbital-real-preview-') as temporary:
            root = Path(temporary)
            manager = themes.Themes(root, config_root=root/'config', data_root=root/'data')
            editor = Editor(manager, image=themes.ROOT/'assets/wallpaper/orbital-2560x1440.png')
            try:
                editor.start()
                deadline = time.monotonic() + 8
                while not editor.canApply and time.monotonic() < deadline:
                    QTest.qWait(20)
                self.assertTrue(editor.canApply, editor.error)
                self.assertTrue(editor.sourceColors)
                editor.setOption('contrast', .25)
                QTest.qWait(270)
                editor.setOption('contrast', .5)
                deadline = time.monotonic() + 8
                while not editor.canApply and time.monotonic() < deadline:
                    QTest.qWait(20)
                self.assertTrue(editor.canApply, editor.error)
                self.assertEqual(editor.preview['generation']['options']['contrast'], .5)
                editor.setOption('source_kind', 'color')
                editor.setOption('mode', 'light')
                deadline = time.monotonic() + 8
                while not editor.canApply and time.monotonic() < deadline:
                    QTest.qWait(20)
                self.assertTrue(editor.canApply, editor.error)
                self.assertEqual(editor.preview['mode'], 'light')
                self.assertEqual(list(root.rglob('*')), [])
            finally:
                editor.shutdown()
                editor.deleteLater()
                app.processEvents()
