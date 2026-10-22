# SPDX-License-Identifier: MIT
"""Lunar accuracy, geometry, palette updates, and isolated launcher lifecycle."""

from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import orbital_moon as moon
import orbital_moon_launcher as launcher


class MoonTests(unittest.TestCase):
    def test_usno_reference_phases(self):
        # UTC primary phases, USNO API /moon/phases/year?year=2026, retrieved
        # 2026-10-22. 0.1 degree allows the reference's whole-minute rounding.
        for timestamp, expected in [('2026-01-03T10:03:00Z', .5),
                                    ('2026-01-10T15:48:00Z', .75),
                                    ('2026-01-18T19:52:00Z', 0),
                                    ('2026-01-26T04:47:00Z', .25)]:
            with self.subTest(timestamp=timestamp):
                state = moon.moon_state(datetime.fromisoformat(timestamp.replace('Z', '+00:00')))
                error = abs((state.phase - expected + .5) % 1 - .5) * 360
                self.assertLess(error, .1)
                self.assertAlmostEqual(state.illumination, (1 if expected == .5 else 0)
                                       if expected in (0, .5) else .5, delta=.01)

    def test_timezone_invariance_and_aware_time_required(self):
        utc = moon.moon_state(datetime.fromisoformat('2026-10-22T12:00:00+00:00'))
        local = moon.moon_state(datetime.fromisoformat('2026-10-22T19:00:00+07:00'))
        self.assertEqual(utc, local)
        with self.assertRaises(ValueError):
            moon.moon_state(datetime(2026, 10, 22))

    def test_disc_geometry_and_transparency(self):
        # Pixel area is an independent check of the SVG terminator construction.
        try:
            from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, QSize
            from PyQt6.QtGui import QImage, QImageReader
            from PIL import Image, ImageChops, ImageOps, ImageStat
        except ImportError:
            self.skipTest('PyQt6 and Pillow are needed for visual checks')

        def alpha(fraction, waxing, size=256):
            body = moon.lit_shape(fraction, waxing, '#FFFFFF')
            source = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{body}</svg>'
            buffer = QBuffer()
            buffer.setData(QByteArray(source.encode()))
            buffer.open(QIODevice.OpenModeFlag.ReadOnly)
            reader = QImageReader(buffer, b'svg')
            reader.setScaledSize(QSize(size, size))
            image = reader.read().convertToFormat(QImage.Format.Format_RGBA8888)
            self.assertFalse(image.isNull())
            return Image.frombytes('RGBA', (size, size), image.constBits().asstring(image.sizeInBytes())).getchannel('A')

        mass = lambda image: ImageStat.Stat(image).sum[0]
        full = mass(alpha(1, True))
        for fraction in (0, .0001, .01, .1464466, .5, .8535534, .9999, 1):
            right, left = alpha(fraction, True), alpha(fraction, False)
            self.assertAlmostEqual(mass(right) / full, fraction, delta=.001)
            difference = ImageChops.difference(right, ImageOps.mirror(left))
            self.assertLess(mass(difference) / (255 * 256 * 256), 1e-4)
        self.assertEqual(mass(alpha(.5, True).crop((0, 0, 128, 256))), 0)
        self.assertEqual(mass(alpha(.5, False).crop((128, 0, 256, 256))), 0)
        state = moon.MoonState('2026-01-01T00:00:00Z', 0, 0, True)
        for fraction in (0, .005, .1464, .5, 1):
            state = moon.MoonState(state.utc, state.phase, fraction, True)
            for size in (24, 32, 40):
                buffer = QBuffer()
                buffer.setData(QByteArray(moon.moon_svg(state, moon.DEFAULT_COLORS).encode()))
                buffer.open(QIODevice.OpenModeFlag.ReadOnly)
                reader = QImageReader(buffer, b'svg')
                reader.setScaledSize(QSize(size, size))
                image = reader.read()
                self.assertFalse(image.isNull())
                self.assertTrue(any(image.pixelColor(x, y).alpha() for y in range(size) for x in range(size)))
                self.assertTrue(all(image.pixelColor(x, y).alpha() == 0
                                    for x, y in ((0, 0), (0, size-1), (size-1, 0), (size-1, size-1))))


class LauncherTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='orbital-moon-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'Луна $rice%'
        self.paths = launcher.Locations(self.root / 'user', self.root / 'config',
                                        self.root / 'data', self.root / 'state')
        self.current = {'panel': 2, 'applet': 3, 'location': 'bottom', 'icon': 'digikam'}
        self.other = {'panel': 4, 'applet': 8, 'location': 'top', 'icon': 'another-launcher'}
        self.units = {s: {'enabled': False, 'active': False} for s in ('timer', 'path')}
        self.instant = moon.moon_state(datetime.fromisoformat('2026-10-22T12:00:00+00:00'))
        self.calls = []
        for replacement in (
            patch.object(launcher, 'targets', side_effect=lambda: [dict(self.current), dict(self.other)]),
            patch.object(launcher, 'set_icon', side_effect=self.set_icon),
            patch.object(launcher, 'systemctl', side_effect=self.systemctl),
            patch.object(launcher, 'moon_state', side_effect=lambda: self.instant),
        ):
            replacement.start()
            self.addCleanup(replacement.stop)

    def set_icon(self, target, icon, expected):
        self.assertEqual(target, {'panel': 2, 'applet': 3})
        if expected != self.current['icon']:
            raise RuntimeError('Icon changed during update')
        self.current['icon'] = icon

    def systemctl(self, *args, check=True):
        self.calls.append(args)
        command = args[0]
        names = [a for a in args[1:] if a.startswith('orbital-moon.')]
        for name in names:
            suffix = name.rsplit('.', 1)[1]
            if suffix not in self.units:
                continue
            state = self.units[suffix]
            if command == 'is-enabled':
                return subprocess.CompletedProcess(args, 0 if state['enabled'] else 1,
                                                    'enabled\n' if state['enabled'] else 'disabled\n', '')
            if command == 'is-active':
                return subprocess.CompletedProcess(args, 0 if state['active'] else 1,
                                                    'active\n' if state['active'] else 'inactive\n', '')
            if command in ('enable', 'disable'):
                state['enabled'] = command == 'enable'
                if '--now' in args:
                    state['active'] = state['enabled']
            if command in ('stop', 'start'):
                state['active'] = command == 'start'
        return subprocess.CompletedProcess(args, 0, '', '')

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*')
                if p.is_file() and p.name != '.lock'}

    def test_install_update_independent_bundle_and_restore(self):
        state = launcher.install(self.paths)
        self.assertEqual(state['original_icon'], 'digikam')
        self.assertEqual(self.other['icon'], 'another-launcher')
        self.assertTrue(all(s['enabled'] and s['active'] for s in self.units.values()))
        first = self.current['icon']
        self.instant = moon.moon_state(datetime.fromisoformat('2026-10-23T12:00:00+00:00'))
        launcher.update(self.paths)
        self.assertNotEqual(self.current['icon'], first)
        self.assertEqual(len(list(self.paths.icons.glob('*.svg'))), 2)
        launcher.update(self.paths)
        self.assertEqual(len(list(self.paths.icons.glob('*.svg'))), 2)
        second = self.current['icon']
        self.instant = moon.moon_state(datetime.fromisoformat('2026-10-24T12:00:00+00:00'))
        launcher.install(self.paths)
        self.assertEqual(launcher.read_state(self.paths)['original_icon'], 'digikam')
        self.assertEqual(len(list(self.paths.icons.glob('*.svg'))), 2)
        self.assertTrue(Path(second).exists())
        result = subprocess.run([str(self.paths.command), 'render', '--at', '2026-10-22T12:00:00Z',
                                 '--output', str(self.root / 'render.svg')], cwd='/tmp',
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertAlmostEqual(json.loads(result.stdout)['illumination'], .84371484)
        unrelated = self.paths.icons / 'personal.svg'
        unrelated.write_text('unrelated')
        launcher.uninstall(self.paths)
        self.assertEqual(self.current['icon'], 'digikam')
        self.assertFalse(self.paths.bundle.exists())
        self.assertFalse(self.paths.command.exists())
        self.assertFalse(self.paths.state.exists())
        self.assertEqual(unrelated.read_text(), 'unrelated')
        self.assertTrue(all(not s['enabled'] and not s['active'] for s in self.units.values()))

    def test_manual_selection_pauses_updates_and_survives_uninstall(self):
        launcher.install(self.paths)
        self.current['icon'] = 'my-static-icon'
        self.assertTrue(launcher.update(self.paths)['paused'])
        self.assertEqual(self.current['icon'], 'my-static-icon')
        launcher.uninstall(self.paths)
        self.assertEqual(self.current['icon'], 'my-static-icon')

    def test_reinstall_resumes_after_manual_selection(self):
        launcher.install(self.paths)
        self.current['icon'] = 'my-static-icon'
        launcher.update(self.paths)
        self.assertFalse(launcher.install(self.paths)['paused'])
        self.assertTrue(launcher.owned_icon(self.paths, self.current['icon']))
        self.assertEqual(launcher.read_state(self.paths)['original_icon'], 'digikam')

    def test_dbus_failure_retains_state_and_current_icon(self):
        launcher.install(self.paths)
        before, icon = self.paths.state.read_bytes(), self.current['icon']
        self.instant = moon.moon_state(datetime.fromisoformat('2026-10-23T12:00:00+00:00'))
        with patch.object(launcher, 'set_icon', side_effect=RuntimeError('D-Bus unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'D-Bus'):
                launcher.update(self.paths)
        self.assertEqual(self.paths.state.read_bytes(), before)
        self.assertEqual(self.current['icon'], icon)

    def test_state_write_failure_rolls_back_the_live_icon(self):
        launcher.install(self.paths)
        before, icon = self.paths.state.read_bytes(), self.current['icon']
        self.instant = moon.moon_state(datetime.fromisoformat('2026-10-23T12:00:00+00:00'))
        original = launcher.atomic_write

        def fail_state(path, data, mode=0o644):
            if path == self.paths.state:
                raise OSError('disk full')
            original(path, data, mode)

        with patch.object(launcher, 'atomic_write', side_effect=fail_state):
            with self.assertRaisesRegex(OSError, 'disk full'):
                launcher.update(self.paths)
        self.assertEqual(self.paths.state.read_bytes(), before)
        self.assertEqual(self.current['icon'], icon)

    def test_install_failure_restores_previous_files_and_units(self):
        launcher.install(self.paths)
        before, icon = self.snapshot(), self.current['icon']
        with patch.object(launcher, 'update_locked', side_effect=RuntimeError('late failure')):
            with self.assertRaisesRegex(RuntimeError, 'late failure'):
                launcher.install(self.paths)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.current['icon'], icon)
        self.assertTrue(all(s['enabled'] and s['active'] for s in self.units.values()))

    def test_staging_failure_does_not_stop_an_existing_install(self):
        launcher.install(self.paths)
        before = self.snapshot()
        with patch.object(launcher.shutil, 'copytree', side_effect=OSError('staging failed')):
            with self.assertRaisesRegex(OSError, 'staging failed'):
                launcher.install(self.paths)
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(all(s['enabled'] and s['active'] for s in self.units.values()))

    def test_failed_first_install_removes_partial_files(self):
        with patch.object(launcher, 'update_locked', side_effect=RuntimeError('late failure')):
            with self.assertRaisesRegex(RuntimeError, 'late failure'):
                launcher.install(self.paths)
        self.assertEqual(self.current['icon'], 'digikam')
        for path in [self.paths.bundle, self.paths.command, self.paths.state, *self.paths.units.values()]:
            self.assertFalse(path.exists())
        self.assertTrue(all(not s['enabled'] and not s['active'] for s in self.units.values()))

    def test_foreign_and_modified_install_files_are_preserved(self):
        self.paths.command.parent.mkdir(parents=True)
        self.paths.command.write_text('another program')
        with self.assertRaisesRegex(RuntimeError, 'unrelated'):
            launcher.install(self.paths)
        self.assertEqual(self.paths.command.read_text(), 'another program')
        self.paths.command.unlink()
        launcher.install(self.paths)
        self.paths.units['timer'].write_text('my modified schedule')
        for action in (launcher.install, launcher.uninstall):
            with self.assertRaisesRegex(RuntimeError, 'modified'):
                action(self.paths)
        self.assertEqual(self.paths.units['timer'].read_text(), 'my modified schedule')

    def test_scheme_fallback_and_live_palette_changes(self):
        scheme = self.paths.data / 'color-schemes/Test.colors'
        scheme.parent.mkdir(parents=True)
        scheme.write_text('[Colors:Complementary]\nForegroundNormal=20,40,60\n'
                          'ForegroundLink=0,100,130\nForegroundInactive=80,90,100\n')
        config = self.paths.config / 'kdeglobals'
        config.parent.mkdir(parents=True)
        config.write_text('[General]\nColorScheme=Test\n')
        state = launcher.install(self.paths)
        source = Path(state['last_icon']).read_text()
        self.assertIn('#14283C', source)
        self.assertIn('#006482', source)
        config.write_text('[General]\nColorScheme=Test\n[Colors:Complementary]\nForegroundNormal=240,230,220\n')
        launcher.update(self.paths)
        source = Path(self.current['icon']).read_text()
        self.assertIn('#F0E6DC', source)
        self.assertIn('#006482', source)
        prepared = config.with_suffix('.new')
        prepared.write_text('[Colors:Complementary]\nForegroundNormal=10,20,30\nForegroundLink=50,60,70\n')
        prepared.replace(config)
        launcher.update(self.paths)
        source = Path(self.current['icon']).read_text()
        self.assertIn('#0A141E', source)
        self.assertIn('#323C46', source)

    def test_generated_units_and_pinned_dependency(self):
        launcher.install(self.paths)
        result = subprocess.run(['systemd-analyze', '--user', 'verify',
                                 *(str(p) for p in self.paths.units.values())],
                                capture_output=True, text=True, timeout=15)
        if result.returncode and 'SO_PASS' in result.stderr and 'Operation not permitted' in result.stderr:
            self.skipTest('systemd verification needs access to user lookup sockets outside the sandbox')
        self.assertEqual(result.returncode, 0, result.stderr)
        digest = hashlib.sha256((launcher.SOURCE / 'vendor/astronomy.py').read_bytes()).hexdigest()
        self.assertEqual(digest, launcher.ASTRONOMY_SHA256)


if __name__ == '__main__':
    unittest.main()
