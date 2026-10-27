# SPDX-License-Identifier: MIT
"""Run with python3 -m unittest discover -s tests."""

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import orbital_themes as themes
import snapshot


class Desktop:
    """Model native commands against an isolated XDG tree, never the desktop."""
    def __init__(self, root):
        self.root = root
        self.calls = []
        self.fail = None
        self.profiles = {'/Sessions/1': 'Orbital', '/Sessions/2': 'Unrelated'}
        self.terminal_changes = []

    def run(self, *args, check=True):
        args = tuple(str(arg) for arg in args)
        self.calls.append(args)
        if self.fail and self.fail in args:
            self.fail = None
            raise RuntimeError('Injected apply failure')
        if args[0] == 'qdbus6':
            if len(args) == 1:
                return 'org.kde.konsole-42'
            if len(args) == 2:
                return '\n'.join(self.profiles)
            if args[-1] == 'print("ready")':
                return 'ready'
            if args[-1] == 'org.kde.konsole.Session.profile':
                return self.profiles.get(args[2], '')
            if args[-1] == 'org.kde.konsole.Session.processId':
                return '42'
            return ''
        if args[0] == 'kwriteconfig6':
            path = Path(args[args.index('--file') + 1])
            config = themes.read_ini(path)
            group = ']['.join(args[i + 1] for i, arg in enumerate(args) if arg == '--group')
            if group not in config:
                config[group] = {}
            config[group][args[args.index('--key') + 1]] = args[-1]
            themes.write_text(path, themes.ini_text(config))
        if args[0] == 'plasma-apply-desktoptheme':
            themes.write_text(self.root / 'config/plasmarc', '[Theme]\nname=default\n')
        if args[0] == 'plasma-apply-colorscheme':
            path = self.root / 'config/kdeglobals'
            config = themes.read_ini(path)
            if 'General' not in config:
                config['General'] = {}
            # Native Plasma 6 uses exclusive scheme/accent CLI modes.
            if '--accent-color' not in args:
                config['General']['ColorScheme'] = args[-1]
                scheme = self.root / 'data/color-schemes' / f'{args[-1]}.colors'
                if scheme.exists():
                    for section, values in themes.read_ini(scheme).items():
                        if section.startswith('Colors:') or section == 'WM':
                            config[section] = dict(values)
            themes.write_text(path, themes.ini_text(config))
        return ''

    def terminal_writer(self, pid, scheme):
        self.terminal_changes.append((pid, scheme))


class ThemeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='orbital-tests-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.desktop = Desktop(self.root)
        self.manager = themes.Themes(self.root, self.desktop, self.root / 'config', self.root / 'data',
                                     self.desktop.terminal_writer)
        self.addCleanup(patch.stopall)
        patch('orbital_themes.shutil.which', return_value='/test/native-command').start()
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        themes.write_text(self.root / 'config/kdeglobals', '[General]\nColorScheme=BreezeLight\nfont=Keep Me\n')
        themes.write_text(self.root / 'config/plasmarc', '[Theme]\nname=default\n')
        themes.write_text(self.root / 'config/plasma-org.kde.plasma.desktop-appletsrc', '[Panel]\nLayout=keep\n')
        themes.write_text(self.root / 'data/konsole/Orbital.profile',
                           '[Appearance]\nColorScheme=Orbital\nFont=My Font,13\n[General]\nName=Orbital\nCommand=/bin/zsh\n')

    def file_state(self):
        result = {}
        for directory in (self.root / 'config', self.root / 'data'):
            for path in directory.rglob('*'):
                if path.is_file() and 'backups' not in path.parts:
                    result[str(path.relative_to(self.root))] = path.read_bytes()
        return result

    def test_presets_and_light_text_contrast(self):
        for mode in ('dark', 'light'):
            palette = themes.builtin(f'orbital-{mode}')
            scheme = themes.ini(themes.render_scheme(palette))
            self.assertEqual(scheme['Colors:Window']['ForegroundNormal'], themes.rgb(palette['colors']['text']))
            foreground = luminance(palette['colors']['text'])
            for role in ('canvas', 'panel', 'window', 'button', 'selected'):
                background = luminance(palette['colors'][role])
                self.assertGreaterEqual((max(foreground, background) + .05) / (min(foreground, background) + .05), 4.5)

    def test_apply_preserves_layout_fonts_wallpaper_and_unrelated_sessions(self):
        before_panel = (self.root / 'config/plasma-org.kde.plasma.desktop-appletsrc').read_bytes()
        self.manager.apply(themes.builtin('orbital-light'))
        self.assertEqual(self.manager.active()['id'], 'orbital-light')
        profile = themes.read_ini(self.root / 'data/konsole' / self.manager.active()['profile'])
        self.assertEqual(profile['Appearance']['Font'], 'My Font,13')
        self.assertEqual(profile['General']['Command'], '/bin/zsh')
        self.assertEqual((self.root / 'config/plasma-org.kde.plasma.desktop-appletsrc').read_bytes(), before_panel)
        self.assertEqual(self.desktop.profiles['/Sessions/2'], 'Unrelated')
        self.assertEqual(len(self.desktop.terminal_changes), 1)
        self.assertFalse(any(call[0] == 'systemctl' or 'writeConfig("Image"' in call[-1] for call in self.desktop.calls))
        self.assertEqual(themes.read_ini(self.root / 'config/gtk-4.0/settings.ini')['Settings']['gtk-theme-name'], 'Breeze')
        globals = themes.read_ini(self.root / 'config/kdeglobals')
        self.assertEqual(globals['General']['ColorScheme'], self.manager.active()['scheme'])
        self.assertEqual(globals['General']['AccentColor'], '0,0,0,0')
        self.assertEqual(globals['Colors:Window']['ForegroundNormal'], '23,45,61')

    def test_snapshot_restores_exact_files_and_removes_new_artifacts(self):
        before = self.file_state()
        backup = self.manager.apply(themes.builtin('orbital-light'))
        self.manager.restore(backup)
        self.assertEqual(self.file_state(), before)
        self.assertEqual(self.desktop.terminal_changes[-1][1], 'Orbital')

    def test_failure_after_color_change_rolls_back(self):
        before = self.file_state()
        self.desktop.fail = 'DefaultProfile'
        with self.assertRaisesRegex(RuntimeError, 'previous theme restored'):
            self.manager.apply(themes.builtin('orbital-dark'))
        self.assertEqual(self.file_state(), before)

    def test_switch_back_and_reapply_active_palette(self):
        self.manager.apply(themes.builtin('orbital-dark'))
        dark = self.file_state()
        backup = self.manager.apply(themes.builtin('orbital-light'))
        self.manager.restore(backup)
        self.assertEqual(self.file_state(), dark)
        self.assertEqual(self.manager.load(None)['id'], 'orbital-dark')

    def test_wallpaper_copy_handles_spaces_and_rollback(self):
        image = self.root / 'picture with spaces "quote".png'
        image.write_bytes(b'fixture image bytes')
        before = self.file_state()
        backup = self.manager.apply(themes.builtin('orbital-dark'), image)
        target = Path(self.manager.active()['wallpaper'])
        self.assertEqual(target.read_bytes(), image.read_bytes())
        self.assertTrue((self.manager.store / 'themes/orbital-dark.wallpaper').exists())
        scripts = [call[-1] for call in self.desktop.calls if 'writeConfig("Image"' in call[-1]]
        self.assertEqual(len(scripts), 1)
        self.assertIn(json.dumps(str(target)), scripts[0])
        self.manager.restore(backup)
        self.assertEqual(self.file_state(), before)

    def test_source_image_is_saved_without_changing_wallpaper_and_restores(self):
        from theme_fixtures import material_output
        image = self.root / 'source image.png'
        image.write_bytes(b'fixture image')
        source = themes.generation_source(image)
        palette = themes.palette_from_generation(material_output(), source, 'dark',
                                                 themes.GenerationOptions(contrast=.25), 'matugen 4.2.0')
        before = self.file_state()
        backup = self.manager.apply(palette, source_image=image)
        saved = Path((self.manager.store / 'themes' / f"{palette['id']}.wallpaper").read_text().strip())
        self.assertEqual(saved.read_bytes(), image.read_bytes())
        self.assertIsNone(self.manager.active()['wallpaper'])
        self.assertEqual(self.manager.load(None), palette)
        self.assertFalse(any('writeConfig("Image"' in call[-1] for call in self.desktop.calls))
        self.manager.restore(backup)
        self.assertEqual(self.file_state(), before)
        image.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Source image changed'):
            self.manager.apply(palette, source_image=image)

    def test_dry_run_does_not_create_state_or_require_plasma(self):
        before = self.file_state()
        self.manager.apply(themes.builtin('orbital-light'), dry_run=True)
        self.assertEqual(self.file_state(), before)
        self.assertEqual(self.desktop.calls, [])

    def test_invalid_palette_or_missing_wallpaper_fails_before_snapshot(self):
        palette = themes.builtin('orbital-dark')
        palette['colors']['text'] = 'not a color'
        for candidate, image in ((palette, None), (themes.builtin('orbital-dark'), self.root / 'missing.png')):
            with self.assertRaises(ValueError):
                self.manager.apply(candidate, image)
        self.assertFalse((self.manager.store / 'backups').exists())

    def test_snapshot_rejects_escape_before_any_mutation(self):
        backup = self.manager.save_snapshot(self.manager.paths(), [])
        manifest = json.loads((backup / 'manifest.json').read_text())
        manifest[0]['file'] = '../outside'
        (backup / 'manifest.json').write_text(json.dumps(manifest))
        before = self.file_state()
        with self.assertRaisesRegex(ValueError, 'Invalid snapshot'):
            self.manager.restore(backup)
        self.assertEqual(self.file_state(), before)

    def test_material_adapter_real_format_and_invalid_json(self):
        data = {'colors': {role: {'dark': value, 'light': value} for role, value in {
            'surface': '#101418', 'on_surface': '#e0e3e8', 'on_surface_variant': '#c2c7cf',
            'primary': '#98ccf9', 'primary_container': '#094b71', 'error': '#ffb4ab',
            'tertiary': '#d1bfe7', 'surface_container': '#1c2024', 'surface_container_high': '#262a2e'}.items()}}
        palette = themes.palette_from_material(data, 'dark', '0123456789abcdef')
        self.assertEqual(palette['colors']['panel'], '#1C2024')
        self.assertEqual(palette['terminal']['Color4'], '#98CCF9')
        self.assertNotEqual(themes.scheme_id(palette), themes.scheme_id(themes.builtin('orbital-dark')))
        bad = copy.deepcopy(data)
        del bad['colors']['on_surface']
        with self.assertRaises(ValueError):
            themes.palette_from_material(bad, 'dark', 'hash')

    def test_generator_isolated_config_and_no_user_hooks(self):
        image = self.root / 'image.png'
        image.write_bytes(b'fixture')
        class Matugen:
            def run(inner, *args):
                if args[-1] == '--version':
                    return 'matugen 4.2.0'
                config = Path(args[args.index('--config') + 1]).read_text()
                self.assertIn('caching = false', config)
                self.assertIn('--dry-run', args)
                self.assertIn('--source-color-index', args)
                return '{}'
        with self.assertRaisesRegex(ValueError, 'Unsupported Matugen'):
            themes.generate(image, 'dark', Matugen())
        self.assertFalse((self.manager.store / 'backups').exists())
        with patch('orbital_themes.shutil.which', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'Matugen is required'):
                themes.generate(image, 'dark')

    def test_full_snapshot_restores_state_and_cleans_only_managed_artifacts(self):
        self.manager.apply(themes.builtin('orbital-dark'))
        before = self.file_state()
        backup = snapshot.snapshot(self.manager, self.root / 'full-backups')
        self.manager.apply(themes.builtin('orbital-light'))
        unrelated = self.root / 'data/konsole/Orbital-Unrelated.profile'
        themes.write_text(unrelated, '[General]\nName=Unrelated\n')
        snapshot.restore(backup, self.manager)
        after = self.file_state()
        after.pop('data/konsole/Orbital-Unrelated.profile')
        self.assertEqual(after, before)
        self.assertTrue(unrelated.exists())

    def test_full_snapshot_removes_disk_installed_after_snapshot(self):
        widget = self.manager.home / '.local/share/plasma/plasmoids/org.orbital.disk'
        backup = snapshot.snapshot(self.manager, self.root / 'full-backups')
        themes.write_text(widget / 'contents/ui/main.qml', 'new disk widget')
        snapshot.restore(backup, self.manager)
        self.assertFalse(widget.exists())

    def test_full_snapshot_restores_disk_package_and_panel_configuration(self):
        widget = self.manager.home / '.local/share/plasma/plasmoids/org.orbital.disk/contents/ui/main.qml'
        panel = self.manager.home / '.config/plasma-org.kde.plasma.desktop-appletsrc'
        configuration = '[General]\nmeterStyle=18\nvolumeId=data-uuid\nioScaleMBps=1200\n'
        themes.write_text(widget, 'disk version one')
        themes.write_text(panel, configuration)
        backup = snapshot.snapshot(self.manager, self.root / 'full-backups')
        themes.write_text(widget, 'disk version two')
        themes.write_text(panel, '[General]\nmeterStyle=19\n')
        snapshot.restore(backup, self.manager)
        self.assertEqual(widget.read_text(), 'disk version one')
        self.assertEqual(panel.read_text(), configuration)

    def test_restore_legacy_full_snapshot(self):
        backup = self.root / 'legacy-backup'
        path = '.config/kdeglobals'
        themes.write_text(backup / path, '[General]\nColorScheme=Legacy\n')
        (backup / 'manifest.json').write_text(json.dumps({path: True, '.config/konsolerc': False}))
        themes.write_text(self.root / '.config/konsolerc', '[Desktop Entry]\nDefaultProfile=Changed\n')
        snapshot.restore(backup, self.manager)
        self.assertEqual((self.root / path).read_text(), '[General]\nColorScheme=Legacy\n')
        self.assertFalse((self.root / '.config/konsolerc').exists())

    def test_terminal_escape_rejects_injected_properties(self):
        for scheme in ('Orbital;Command=unexpected', 'Orbital\n', 'Orbital\x1b[2J'):
            with self.assertRaises(ValueError):
                themes.set_terminal_scheme(os.getpid(), scheme)

    def test_indented_dbus_output_detects_only_managed_tabs(self):
        original = self.desktop.run
        def indented(*args, **kwargs):
            result = original(*args, **kwargs)
            if args[0] == 'qdbus6' and len(args) <= 2:
                return '\n'.join('  ' + line for line in result.splitlines())
            return result
        self.desktop.run = indented
        sessions = self.manager.sessions()
        self.assertEqual([session['path'] for session in sessions], ['/Sessions/1'])

    def test_gtk_updates_settings_section_and_retains_other_values(self):
        path = self.root / 'config/gtk-3.0/settings.ini'
        themes.write_text(path, '[Settings]\ngtk-font-name = My Font 14\n'
                          '[Other]\ngtk-theme-name=Unrelated\nKeepThis=yes\n')
        self.manager.apply(themes.builtin('orbital-light'))
        config = themes.read_ini(path)
        self.assertEqual(config['Settings']['gtk-theme-name'], 'Breeze')
        self.assertEqual(config['Settings']['gtk-application-prefer-dark-theme'], 'false')
        self.assertEqual(config['Settings']['gtk-font-name'], 'My Font 14')
        self.assertEqual(config['Other']['gtk-theme-name'], 'Unrelated')
        self.assertEqual(config['Other']['KeepThis'], 'yes')

    def test_restore_older_snapshot_cleans_later_artifacts_and_updates_new_tabs(self):
        before = self.file_state()
        backup = self.manager.apply(themes.builtin('orbital-dark'))
        self.manager.apply(themes.builtin('orbital-light'))
        self.desktop.profiles['/Sessions/3'] = 'Orbital Light'
        unrelated = self.root / 'data/konsole/Orbital-Personal.profile'
        themes.write_text(unrelated, '[General]\nName=Personal\n')
        self.manager.restore(backup)
        after = self.file_state()
        after.pop('data/konsole/Orbital-Personal.profile')
        self.assertEqual(after, before)
        self.assertTrue(unrelated.exists())
        self.assertEqual(self.desktop.terminal_changes[-1], (42, 'Orbital'))

    def test_incomplete_legacy_snapshot_rejected_before_any_mutation(self):
        backup = self.root / 'incomplete-backup'
        themes.write_text(backup / 'manifest.json', json.dumps({'.config/kdeglobals': True}))
        path = self.root / '.config/kdeglobals'
        themes.write_text(path, '[General]\nColorScheme=Keep\n')
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            snapshot.restore(backup, self.manager)
        self.assertEqual(path.read_text(), '[General]\nColorScheme=Keep\n')

    def test_terminal_update_writes_output_escape_to_owned_pty(self):
        master, slave = pty.openpty()
        process = subprocess.Popen(['/usr/bin/sleep', '30'], stdin=slave, stdout=slave, stderr=slave)
        try:
            themes.set_terminal_scheme(process.pid, 'Orbital-Test')
            ready, _, _ = select.select([master], [], [], 2)
            self.assertTrue(ready, 'The terminal output was not delivered')
            self.assertEqual(os.read(master, 1024), b'\x1b]50;ColorScheme=Orbital-Test;Name=Orbital\x07')
        finally:
            process.terminate()
            process.wait(timeout=5)
            os.close(master)
            os.close(slave)


def luminance(hex_color):
    channels = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in channels]
    return sum(value * weight for value, weight in zip(linear, (.2126, .7152, .0722)))


if __name__ == '__main__':
    unittest.main()
