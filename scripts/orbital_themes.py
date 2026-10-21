# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

"""Palette rendering and transactional application; no Qt dependency."""

from __future__ import annotations

import argparse
import configparser
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime
from dataclasses import asdict, dataclass

ROOT = Path(__file__).resolve().parent.parent
COLOR_KEYS = ('canvas', 'panel', 'window', 'button', 'selected', 'text', 'muted',
              'cyan', 'amber', 'red', 'green', 'violet')
TERMINAL_KEYS = ('Background', 'BackgroundFaint', 'BackgroundIntense',
                 'Foreground', 'ForegroundFaint', 'ForegroundIntense') + tuple(
                     f'Color{i}{suffix}' for i in range(8) for suffix in ('', 'Intense'))
HEX = re.compile(r'#[0-9a-fA-F]{6}\Z')
IDENTIFIER = re.compile(r'[a-z0-9][a-z0-9-]{0,79}\Z')
ARTIFACT = re.compile(r'Orbital-[a-z0-9][a-z0-9-]{0,79}-[0-9a-f]{12}\.(colors|profile|colorscheme)\Z')
SCHEME_NOTICE = ('# SPDX-License-Identifier: GPL-2.0-or-later\n'
                 '# Derived from KDE Breeze; see THIRD_PARTY.md.\n'
                 '# Orbital palette: Copyright (c) 2026 Nikolay Skovorodin.\n\n')
NOTICE = '# SPDX-License-Identifier: MIT\n# Copyright (c) 2026 Nikolay Skovorodin.\n\n'
SCHEME_TYPES = tuple('scheme-' + name for name in (
    'content', 'expressive', 'fidelity', 'fruit-salad', 'monochrome', 'neutral',
    'rainbow', 'tonal-spot', 'vibrant', 'smart'))
SOURCE_PREFERENCES = ('saturation', 'lightness', 'darkness')


@dataclass(frozen=True)
class GenerationOptions:
    scheme_type: str = 'scheme-tonal-spot'
    contrast: float = 0.0
    source_color_index: int | None = None
    prefer: str | None = None
    lightness_dark: float = 0.0
    lightness_light: float = 0.0

    def __post_init__(self):
        if self.scheme_type not in SCHEME_TYPES:
            raise ValueError('Unsupported Matugen scheme type')
        for key in ('contrast', 'lightness_dark', 'lightness_light'):
            value = float(getattr(self, key))
            if not math.isfinite(value) or not -1 <= value <= 1:
                raise ValueError(f'{key} must be a finite number from -1 to 1')
            object.__setattr__(self, key, round(value, 6) or 0.0)
        if self.prefer is not None and self.prefer not in SOURCE_PREFERENCES:
            raise ValueError('Unsupported source color preference')
        if self.prefer is not None and self.source_color_index is not None:
            raise ValueError('Choose either a source color index or a preference')
        if self.source_color_index is None and self.prefer is None:
            object.__setattr__(self, 'source_color_index', 0)
        index = self.source_color_index
        if index is not None and (type(index) is not int or not 0 <= index <= 4):
            raise ValueError('Source color index must be from 0 to 4')


def generation_source(value: Path | str, kind: str = 'image') -> dict:
    if kind == 'color':
        color = str(value).upper()
        if not HEX.fullmatch(color):
            raise ValueError('Color must use #RRGGBB format')
        return {'kind': kind, 'value': color, 'hash': hashlib.sha256(color.encode()).hexdigest(),
                'label': color}
    if kind != 'image':
        raise ValueError('Source must be an image or color')
    image = Path(value).expanduser().resolve()
    if not image.is_file():
        raise ValueError(f'Wallpaper does not exist: {image}')
    label = ''.join(char if ord(char) >= 32 and ord(char) != 127 else ' ' for char in image.stem)
    return {'kind': kind, 'value': str(image), 'hash': hashlib.sha256(image.read_bytes()).hexdigest(),
            'label': label}


def matugen_config(directory: Path) -> Path:
    path = directory / 'config.toml'
    path.write_text('[config]\ncaching = false\nversion_check = false\n[templates]\n')
    return path


def matugen_arguments(source: dict, mode: str, options: GenerationOptions,
                      config: Path, source_colors: bool = False) -> list[str]:
    if mode not in ('dark', 'light'):
        raise ValueError('Mode must be dark or light')
    args = ['matugen', 'image', source['value']] if source['kind'] == 'image' else [
        'matugen', 'color', 'hex', source['value']]
    args += ['--config', str(config), '--dry-run']
    if source_colors:
        if source['kind'] != 'image':
            raise ValueError('Source color extraction requires an image')
        return args + ['--show-source-colors']
    args += ['--mode', mode, '--type', options.scheme_type, '--contrast', str(options.contrast),
             '--lightness-dark', str(options.lightness_dark), '--lightness-light', str(options.lightness_light),
             '--json', 'hex', '--old-json-output']
    if source['kind'] == 'image':
        args += ['--prefer', options.prefer] if options.prefer else [
            '--source-color-index', str(options.source_color_index)]
    return args


def palette_from_generation(output: str, source: dict, mode: str,
                            options: GenerationOptions, version: str) -> dict:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as error:
        raise ValueError('Matugen did not return valid JSON; no desktop settings changed') from error
    palette = palette_from_material(payload, mode, source['hash'])
    identity = {'kind': source['kind'], 'hash': source['hash'], 'label': source['label']}
    if source['kind'] == 'color':
        identity['value'] = source['value']
    metadata = {'source': identity, 'options': asdict(options), 'version': version}
    # Paths stay in the wallpaper sidecar. Moving the managed source must not
    # change the palette digest or the Konsole/KDE artifact names.
    key = {'source': {key: value for key, value in identity.items() if key != 'label'},
           'mode': mode, 'options': asdict(options), 'version': version}
    variant = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:10]
    prefix = 'wallpaper' if source['kind'] == 'image' else 'color'
    palette['id'] = f'{prefix}-{source["hash"][:12]}-{mode}-{variant}'
    palette['name'] = (f'Orbital {source["label"]} ({mode}, {options.scheme_type.removeprefix("scheme-")}, '
                       f'{options.contrast:+g})')
    palette['generation'] = metadata
    return validate_palette(palette)


def ini(text: str = '') -> configparser.ConfigParser:
    result = configparser.ConfigParser(interpolation=None, strict=False)
    result.optionxform = str
    if text:
        result.read_string(text)
    return result


def ini_text(config: configparser.ConfigParser) -> str:
    output = io.StringIO()
    config.write(output, space_around_delimiters=False)
    return output.getvalue().rstrip() + '\n'


def read_ini(path: Path) -> configparser.ConfigParser:
    return ini(path.read_text() if path.exists() else '')


def validate_palette(palette: dict) -> dict:
    if (not isinstance(palette, dict) or not isinstance(palette.get('id'), str)
            or not IDENTIFIER.fullmatch(palette['id'])):
        raise ValueError('Invalid palette identifier')
    if palette.get('mode') not in ('dark', 'light'):
        raise ValueError('Palette mode must be dark or light')
    if (not isinstance(palette.get('name'), str) or not palette['name'].strip()
            or any(ord(char) < 32 or ord(char) == 127 for char in palette['name'])):
        raise ValueError('Palette needs a single-line name')
    for group, keys in (('colors', COLOR_KEYS), ('terminal', TERMINAL_KEYS)):
        values = palette.get(group)
        if not isinstance(values, dict):
            raise ValueError(f'Missing {group} palette')
        for key in keys:
            if not isinstance(values.get(key), str) or not HEX.fullmatch(values[key]):
                raise ValueError(f'Invalid or missing {group}.{key}')
    artwork = palette.get('wallpaper', {})
    if not isinstance(artwork, dict):
        raise ValueError('Invalid wallpaper palette')
    for value in artwork.values():
        if not isinstance(value, str) or not HEX.fullmatch(value):
            raise ValueError('Invalid wallpaper color')
    return palette


def builtin(name: str) -> dict:
    if name == 'Orbital':
        name = 'orbital-dark'
    if not IDENTIFIER.fullmatch(name):
        raise ValueError('Invalid theme identifier')
    return validate_palette(json.loads((ROOT / 'assets/palettes' / f'{name}.json').read_text()))


def digest(palette: dict) -> str:
    return hashlib.sha256(json.dumps(palette, sort_keys=True).encode()).hexdigest()[:12]


def scheme_id(palette: dict) -> str:
    return f"Orbital-{palette['id']}-{digest(palette)}"


def rgb(value: str) -> str:
    return ','.join(str(int(value[i:i + 2], 16)) for i in (1, 3, 5))


def is_theme_artifact(path: Path, data: Path) -> bool:
    match = ARTIFACT.fullmatch(path.name)
    return bool(match and path.parent == data / ('color-schemes' if match[1] == 'colors' else 'konsole'))


def render_scheme(palette: dict, template: Path | None = None, name: str | None = None) -> str:
    validate_palette(palette)
    if template is None:
        template = ROOT / 'assets/kde' / ('Orbital.colors' if palette['mode'] == 'dark' else 'OrbitalLight.colors')
    config = read_ini(template)
    if 'Colors:Window' not in config:
        raise ValueError(f'Invalid KDE color template: {template}')
    colors = palette['colors']
    backgrounds = {
        'Colors:Window': ('window', 'panel'), 'Colors:View': ('canvas', 'window'),
        'Colors:Button': ('button', 'window'), 'Colors:Header': ('panel', 'window'),
        'Colors:Header][Inactive': ('canvas', 'panel'), 'Colors:Complementary': ('panel', 'canvas'),
        'Colors:Selection': ('selected', 'button'), 'Colors:Tooltip': ('button', 'window'),
    }
    foregrounds = {'DecorationFocus': 'cyan', 'DecorationHover': 'cyan', 'ForegroundActive': 'cyan',
                   'ForegroundInactive': 'muted', 'ForegroundLink': 'cyan', 'ForegroundNegative': 'red',
                   'ForegroundNeutral': 'amber', 'ForegroundNormal': 'text', 'ForegroundPositive': 'green',
                   'ForegroundVisited': 'violet'}
    for section in config.sections():
        if not section.startswith('Colors:'):
            continue
        normal, alternate = backgrounds.get(section, ('window', 'panel'))
        for key, role in {'BackgroundNormal': normal, 'BackgroundAlternate': alternate, **foregrounds}.items():
            if key in config[section]:
                config[section][key] = rgb(colors[role])
    general = config['General']
    for key in list(general):
        if key.startswith('Name['):
            del general[key]
    general['Name'] = palette['name']
    general['ColorScheme'] = name or scheme_id(palette)
    # An inherited accent tint must not change the explicit palette surfaces.
    if 'TintFactor' in general:
        general['TintFactor'] = '0'
    for state, bg, fg in (('active', 'panel', 'text'), ('inactive', 'canvas', 'muted')):
        for suffix, role in (('Background', bg), ('Blend', fg), ('Foreground', fg)):
            config['WM'][state + suffix] = rgb(colors[role])
    return SCHEME_NOTICE + ini_text(config)


def render_terminal(palette: dict) -> str:
    validate_palette(palette)
    config = ini()
    for key, value in palette['terminal'].items():
        config[key] = {'Color': rgb(value)}
    config['General'] = {'Description': palette['name'], 'Opacity': '1'}
    return NOTICE + ini_text(config)


def palette_from_material(payload: dict, mode: str, image_hash: str) -> dict:
    """Use Material surfaces/accents, retaining readable warning/success ANSI hues."""
    if not isinstance(payload, dict):
        raise ValueError('Unsupported Matugen JSON object')
    palette = builtin(f'orbital-{mode}')
    values = payload.get('colors', {})
    if not isinstance(values, dict):
        raise ValueError('Unsupported Matugen colors object')
    source = {role: variants.get(mode) for role, variants in values.items() if isinstance(variants, dict)}
    required = ('surface', 'on_surface', 'on_surface_variant', 'primary', 'primary_container', 'error', 'tertiary')
    if any(not isinstance(source.get(key), str) or not HEX.fullmatch(source[key]) for key in required):
        raise ValueError('Unsupported Matugen JSON; expected --json hex --old-json-output (tested with 4.2.0)')
    roles = {'canvas': 'surface', 'window': 'surface', 'panel': 'surface_container',
             'button': 'surface_container_high', 'selected': 'primary_container', 'text': 'on_surface',
             'muted': 'on_surface_variant', 'cyan': 'primary', 'red': 'error', 'violet': 'tertiary'}
    for role, key in roles.items():
        value = source.get(key, source['surface'])
        if not isinstance(value, str) or not HEX.fullmatch(value):
            raise ValueError(f'Invalid Matugen color: {key}')
        palette['colors'][role] = value.upper()
    colors = palette['colors']
    terminal = palette['terminal']
    terminal.update({'Background': colors['canvas'], 'BackgroundFaint': colors['panel'],
                     'BackgroundIntense': colors['window'], 'Foreground': colors['text'],
                     'ForegroundFaint': colors['muted'], 'ForegroundIntense': colors['text']})
    for index, role in ((1, 'red'), (4, 'cyan'), (5, 'violet'), (6, 'cyan')):
        for suffix in ('', 'Intense'):
            terminal[f'Color{index}{suffix}'] = colors[role]
    terminal['Color0'] = colors['canvas'] if mode == 'dark' else colors['text']
    terminal['Color0Intense'] = colors['muted']
    terminal['Color7'] = colors['text']
    terminal['Color7Intense'] = colors['text']
    palette['id'] = f'wallpaper-{image_hash[:12]}-{mode}'
    palette['name'] = f'Orbital Wallpaper {image_hash[:8]} ({mode})'
    palette.pop('wallpaper', None)
    return validate_palette(palette)


class Runner:
    def run(self, *args: str, check: bool = True) -> str:
        result = subprocess.run([str(arg) for arg in args], capture_output=True, text=True, timeout=30)
        if check and result.returncode:
            raise RuntimeError(f'{args[0]} failed: {(result.stderr or result.stdout).strip()}')
        return result.stdout.strip() if result.returncode == 0 else ''


class Themes:
    def __init__(self, home: Path | None = None, runner: Runner | None = None,
                 config_root: Path | None = None, data_root: Path | None = None,
                 terminal_writer=None):
        self.home = home or Path.home()
        self.config = config_root or Path(os.environ.get('XDG_CONFIG_HOME', self.home / '.config'))
        self.data = data_root or Path(os.environ.get('XDG_DATA_HOME', self.home / '.local/share'))
        self.store = self.data / 'orbital'
        self.runner = runner or Runner()
        self.terminal_writer = terminal_writer or set_terminal_scheme
        self.known_profiles = {'Orbital'}

    def active(self) -> dict:
        path = self.store / 'active.json'
        return json.loads(path.read_text()) if path.exists() else {}

    def load(self, name: str | None) -> dict:
        name = name or self.active().get('id', 'orbital-dark')
        if not IDENTIFIER.fullmatch(name):
            raise ValueError('Invalid theme identifier')
        path = ROOT / 'assets/palettes' / f'{name}.json'
        if not path.exists():
            path = self.store / 'themes' / f'{name}.json'
        return validate_palette(json.loads(path.read_text()))

    def list(self) -> list[dict]:
        palettes = {}
        for directory in (self.store / 'themes', ROOT / 'assets/palettes'):
            for path in sorted(directory.glob('*.json')):
                palette = validate_palette(json.loads(path.read_text()))
                palettes[palette['id']] = palette
        return list(palettes.values())

    def preflight(self) -> None:
        for command in ('qdbus6', 'plasma-apply-colorscheme', 'plasma-apply-desktoptheme',
                        'kwriteconfig6', 'systemctl'):
            if shutil.which(command) is None:
                raise RuntimeError(f'Required command not found: {command}')
        if self.plasma('print("ready")') != 'ready':
            raise RuntimeError('A running Plasma 6 session is required')

    def plasma(self, script: str) -> str:
        return self.runner.run('qdbus6', 'org.kde.plasmashell', '/PlasmaShell',
                               'org.kde.PlasmaShell.evaluateScript', script)

    def write_config(self, file: str, groups: tuple[str, ...], key: str, value: str) -> None:
        args = ['kwriteconfig6', '--file', str(self.config / file)]
        for group in groups:
            args.extend(('--group', group))
        self.runner.run(*args, '--key', key, value)

    def sessions(self) -> list[dict]:
        sessions = []
        for service in self.runner.run('qdbus6').splitlines():
            service = service.strip()
            if not re.fullmatch(r'org\.kde\.konsole(?:-[0-9]+)?', service):
                continue
            for path in self.runner.run('qdbus6', service, check=False).splitlines():
                path = path.strip()
                if not re.fullmatch(r'/Sessions/[0-9]+', path):
                    continue
                profile = self.runner.run('qdbus6', service, path, 'org.kde.konsole.Session.profile', check=False)
                if self.managed_profile(profile):
                    filename = self.profile_files().get(profile, 'Orbital.profile')
                    settings = read_ini(self.data / 'konsole' / filename)
                    scheme = self.active().get('scheme') or settings.get(
                        'Appearance', 'ColorScheme', fallback='Orbital')
                    sessions.append({'service': service, 'path': path, 'profile': profile, 'scheme': scheme})
        return sessions

    def managed_profile(self, profile: str) -> bool:
        self.known_profiles.update(self.profile_files())
        return profile in self.known_profiles

    def profile_files(self) -> dict[str, str]:
        profiles = {'Orbital': 'Orbital.profile'}
        for path in sorted((self.data / 'konsole').glob('Orbital-*.profile')):
            config = read_ini(path)
            if config.get('General', 'X-Orbital-Managed', fallback='') == 'true':
                profiles[config.get('General', 'Name')] = path.name
        return profiles

    def update_sessions(self, sessions: list[dict], scheme: str | None = None) -> None:
        for session in sessions:
            # A tab can close while switching themes; do not fail the entire transaction.
            current = self.runner.run('qdbus6', session['service'], session['path'],
                                      'org.kde.konsole.Session.profile', check=False)
            if not current or not self.managed_profile(current):
                continue
            pid = self.runner.run('qdbus6', session['service'], session['path'],
                                  'org.kde.konsole.Session.processId', check=False)
            if not pid.isdigit() or int(pid) <= 0:
                continue
            try:
                self.terminal_writer(int(pid), scheme or session['scheme'])
            except FileNotFoundError:
                continue  # The shell/tab exited between the D-Bus query and opening its PTY.

    def paths(self, additional: list[Path] = ()) -> list[Path]:
        paths = [self.config / name for name in ('kdeglobals', 'plasmarc', 'konsolerc',
                 'kscreenlockerrc', 'plasma-org.kde.plasma.desktop-appletsrc', 'gtk-3.0', 'gtk-4.0',
                 'gtkrc', 'gtkrc-2.0', 'Trolltech.conf')]
        paths += [self.store / name for name in ('active.json', 'themes', 'wallpapers')]
        paths += [self.data / 'konsole/Orbital.profile']
        for directory, pattern in (('color-schemes', 'Orbital-*.colors'), ('konsole', 'Orbital-*.profile'),
                                   ('konsole', 'Orbital-*.colorscheme')):
            paths += sorted(path for path in (self.data / directory).glob(pattern)
                            if is_theme_artifact(path, self.data))
        return list(dict.fromkeys(paths + list(additional)))

    def save_snapshot(self, paths: list[Path], sessions: list[dict]) -> Path:
        backup = self.store / 'backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup.mkdir(parents=True, mode=0o700)
        manifest = []
        for index, path in enumerate(paths):
            exists = path.exists() or path.is_symlink()
            manifest.append({'path': str(path), 'existed': exists, 'file': str(index)})
            if exists:
                copy_path(path, backup / str(index))
        (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        (backup / 'sessions.json').write_text(json.dumps(sessions, indent=2) + '\n')
        latest = backup.parent / 'latest'
        latest.unlink(missing_ok=True)
        latest.symlink_to(backup.name)
        return backup

    def restore(self, backup: Path | None = None) -> None:
        self.preflight()
        backup = (backup or self.store / 'backups/latest').resolve()
        manifest = json.loads((backup / 'manifest.json').read_text())
        allowed = set(self.paths())
        for item in manifest:
            path = Path(item['path'])
            if not re.fullmatch(r'[0-9]+', str(item.get('file', ''))):
                raise ValueError('Invalid snapshot file entry')
            if path not in allowed and not is_theme_artifact(path, self.data):
                raise ValueError(f'Snapshot path is outside Orbital settings: {path}')
            source = backup / item['file']
            if item['existed'] and not (source.exists() or source.is_symlink()):
                raise ValueError('Incomplete snapshot')
        before_applets = (self.config / 'plasma-org.kde.plasma.desktop-appletsrc').read_bytes() if (self.config / 'plasma-org.kde.plasma.desktop-appletsrc').exists() else b''
        before_style = read_ini(self.config / 'plasmarc').get('Theme', 'name', fallback='default')
        old_sessions = json.loads((backup / 'sessions.json').read_text())
        current_sessions = self.sessions()
        saved = {Path(item['path']) for item in manifest}
        # Undo every file first; the native color tool then broadcasts the restored palette.
        def restore_files():
            for directory, pattern in (('color-schemes', 'Orbital-*.colors'),
                                       ('konsole', 'Orbital-*.profile'), ('konsole', 'Orbital-*.colorscheme')):
                for path in (self.data / directory).glob(pattern):
                    if path not in saved and is_theme_artifact(path, self.data):
                        remove_path(path)
            for item in manifest:
                path = Path(item['path'])
                remove_path(path)
                if item['existed']:
                    copy_path(backup / item['file'], path)
        restore_files()
        saved_globals = read_ini(self.config / 'kdeglobals')
        name = saved_globals.get('General', 'ColorScheme', fallback='')
        temporary = None
        if not name or not any((directory / f'{name}.colors').exists() for directory in (
                self.data / 'color-schemes', Path('/usr/share/color-schemes'))):
            if 'Colors:Window' not in saved_globals:
                name = 'BreezeLight'
            else:
                name = f'Orbital-Restore-{backup.name}'
                colors = ini()
                for section in saved_globals.sections():
                    if section.startswith(('Colors:', 'ColorEffects:')) or section == 'WM':
                        colors[section] = dict(saved_globals[section])
                colors['General'] = {'Name': 'Restored Orbital snapshot', 'ColorScheme': name}
                temporary = self.data / 'color-schemes' / f'{name}.colors'
                write_text(temporary, SCHEME_NOTICE + ini_text(colors))
        try:
            if temporary:
                # These colors already include the saved accent; do not tint them twice.
                self.write_config('kdeglobals', ('General',), 'AccentColor', '0,0,0,0')
            self.write_config('kdeglobals', ('General',), 'ColorScheme', 'OrbitalPendingRestore')
            self.runner.run('plasma-apply-colorscheme', name)
        finally:
            restore_files()  # Retain the original config bytes, including absent settings.
            if temporary:
                temporary.unlink(missing_ok=True)
        after_applets = (self.config / 'plasma-org.kde.plasma.desktop-appletsrc').read_bytes() if (self.config / 'plasma-org.kde.plasma.desktop-appletsrc').exists() else b''
        after_style = read_ini(self.config / 'plasmarc').get('Theme', 'name', fallback='default')
        if before_applets != after_applets or before_style != after_style:
            self.runner.run('systemctl', '--user', 'restart', 'plasma-plasmashell.service')
        self.update_sessions(old_sessions)
        previous = self.active().get('scheme') or read_ini(self.data / 'konsole/Orbital.profile').get(
            'Appearance', 'ColorScheme', fallback='Orbital')
        original_tabs = {(session['service'], session['path']) for session in old_sessions}
        self.update_sessions([session for session in current_sessions
                              if (session['service'], session['path']) not in original_tabs], previous)

    def apply(self, palette: dict, wallpaper: Path | None = None, dry_run: bool = False,
              small_wallpaper: Path | None = None, source_image: Path | None = None) -> Path | None:
        validate_palette(palette)
        source_image = source_image or wallpaper
        for image in (wallpaper, small_wallpaper, source_image):
            if image is not None and not image.is_file():
                raise ValueError(f'Wallpaper does not exist: {image}')
        if source_image and palette.get('generation', {}).get('source', {}).get('kind') == 'image':
            expected = palette['generation']['source']['hash']
            if hashlib.sha256(source_image.read_bytes()).hexdigest() != expected:
                raise ValueError('Source image changed; regenerate the preview before applying')
        name = scheme_id(palette)
        scheme = render_scheme(palette)
        terminal = render_terminal(palette)
        profile_path = self.data / 'konsole' / f'{name}.profile'
        source = self.data / 'konsole' / self.active().get('profile', 'Orbital.profile')
        profile = read_ini(source if source.exists() else ROOT / 'assets/konsole/Orbital.profile')
        for section in ('Appearance', 'General'):
            if section not in profile:
                profile[section] = {}
        profile['Appearance']['ColorScheme'] = name
        profile['General']['Name'] = palette['name']
        profile['General']['X-Orbital-Managed'] = 'true'
        artifacts = {self.data / 'color-schemes' / f'{name}.colors': scheme,
                     self.data / 'konsole' / f'{name}.colorscheme': terminal,
                     profile_path: NOTICE + ini_text(profile)}
        image_target = None
        if wallpaper:
            image_hash = hashlib.sha256(wallpaper.read_bytes()).hexdigest()[:16]
            image_target = self.store / 'wallpapers' / f'{image_hash}{wallpaper.suffix.lower()}'
        source_target = None
        if source_image:
            image_hash = hashlib.sha256(source_image.read_bytes()).hexdigest()[:16]
            source_target = self.store / 'wallpapers' / f'{image_hash}{source_image.suffix.lower()}'
        small_target = None
        if small_wallpaper:
            image_hash = hashlib.sha256(small_wallpaper.read_bytes()).hexdigest()[:16]
            small_target = self.store / 'wallpapers' / f'{image_hash}{small_wallpaper.suffix.lower()}'
        if dry_run:
            print(f"Would apply {palette['name']} ({name})" + (f' with wallpaper {wallpaper}' if wallpaper else '; keep current wallpapers'))
            return None
        self.preflight()
        sessions = self.sessions()
        backup = self.save_snapshot(self.paths(list(artifacts)), sessions)
        print(f'Snapshot: {backup}', flush=True)
        try:
            for path, content in artifacts.items():
                write_text(path, content)
            for original, target in ((source_image, source_target), (wallpaper, image_target)):
                if original and target:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if original.resolve() != target.resolve():
                        shutil.copy2(original, target)
            if source_target:
                write_text(self.store / 'themes' / f"{palette['id']}.wallpaper", str(source_target) + '\n')
            if small_target and small_wallpaper:
                if small_wallpaper.resolve() != small_target.resolve():
                    shutil.copy2(small_wallpaper, small_target)
            write_text(self.store / 'themes' / f"{palette['id']}.json", json.dumps(palette, indent=2) + '\n')
            self.runner.run('plasma-apply-desktoptheme', 'default')
            # The native CLI treats --accent-color and a scheme as separate modes.
            # Store a transparent override first, then load the actual scheme.
            self.write_config('kdeglobals', ('General',), 'AccentColor', '0,0,0,0')
            self.write_config('kdeglobals', ('General',), 'accentColorFromWallpaper', 'false')
            self.write_config('kdeglobals', ('General',), 'ColorScheme', 'OrbitalPendingApply')
            self.runner.run('plasma-apply-colorscheme', name)
            self.write_config('konsolerc', ('Desktop Entry',), 'DefaultProfile', profile_path.name)
            self.update_gtk(palette['mode'])
            if image_target:
                image = json.dumps(str(image_target))
                small_image = json.dumps(str(small_target or image_target))
                self.plasma('var ds=desktops(); for(var i=0;i<ds.length;++i){'
                            'ds[i].wallpaperPlugin="org.kde.image";'
                            'ds[i].currentConfigGroup=["Wallpaper","org.kde.image","General"];'
                            f'var image=(ds[i].screen>=0 && screenGeometry(ds[i].screen).width>=2800)?{image}:{small_image};'
                            'ds[i].writeConfig("Image",image);' + '}')
                self.write_config('kscreenlockerrc', ('Greeter',), 'WallpaperPlugin', 'org.kde.image')
                self.write_config('kscreenlockerrc', ('Greeter', 'Wallpaper', 'org.kde.image', 'General'), 'Image', str(image_target))
            self.update_sessions(sessions, name)
            write_text(self.store / 'active.json', json.dumps({'id': palette['id'], 'mode': palette['mode'],
                       'scheme': name, 'profile': profile_path.name,
                       'wallpaper': str(image_target) if image_target else self.active().get('wallpaper')}, indent=2) + '\n')
        except Exception as error:
            try:
                self.restore(backup)
            except Exception as rollback:
                raise RuntimeError(f'{error}; rollback failed: {rollback}. Restore with orbital-theme restore {backup}') from error
            raise RuntimeError(f'{error}; previous theme restored') from error
        print(f"Applied {palette['name']}. Restore with: {ROOT / 'scripts/orbital-theme'} restore {backup}")
        return backup

    def update_gtk(self, mode: str) -> None:
        for version in ('gtk-3.0', 'gtk-4.0'):
            path = self.config / version / 'settings.ini'
            config = read_ini(path)
            if 'Settings' not in config:
                config['Settings'] = {}
            for key, value in (('gtk-theme-name', 'Breeze-Dark' if mode == 'dark' else 'Breeze'),
                               ('gtk-application-prefer-dark-theme', 'true' if mode == 'dark' else 'false')):
                config['Settings'][key] = value
            write_text(path, ini_text(config))


def remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def set_terminal_scheme(pid: int, scheme: str) -> None:
    """Konsole's OSC 50 interface changes output properties, never shell input.

    setProfile only accepts already cached profiles. D-Bus locates each managed
    shell; the same output escape used by konsoleprofile loads a new color scheme
    while retaining the tab's font, command, scrollback and other properties.
    """
    if not scheme or any(ord(char) < 32 or char in ';\x7f' for char in scheme):
        raise ValueError('Invalid terminal color scheme name')
    process = Path('/proc') / str(pid)
    if process.stat().st_uid != os.getuid():
        raise RuntimeError('Konsole shell belongs to another user')
    terminal = os.readlink(process / 'fd/0')
    if not re.fullmatch(r'/dev/pts/[0-9]+', terminal):
        raise RuntimeError('Konsole shell does not have a local PTY')
    fd = os.open(terminal, os.O_WRONLY | os.O_NOCTTY | os.O_NONBLOCK | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or not stat.S_ISCHR(info.st_mode):
            raise RuntimeError('Invalid Konsole PTY')
        # OSC changes create an unnamed runtime profile. Keep its ownership
        # recognizable through D-Bus on the next invocation of the switcher.
        os.write(fd, f'\x1b]50;ColorScheme={scheme};Name=Orbital\x07'.encode())
    finally:
        os.close(fd)


def copy_path(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir() and not source.is_symlink():
        shutil.copytree(source, dest, symlinks=True)
    else:
        shutil.copy2(source, dest, follow_symlinks=False)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        try:
            handle.write(text)
            handle.flush()
            os.fchmod(handle.fileno(), 0o644)
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)


def generate(image: Path | str, mode: str, runner: Runner | None = None,
             options: GenerationOptions | None = None, kind: str = 'image') -> dict:
    source = generation_source(image, kind)
    if shutil.which('matugen') is None:
        raise RuntimeError('Matugen is required for generation; install Matugen 4.2.0 (see README.md)')
    options = options or GenerationOptions()
    runner = runner or Runner()
    version = runner.run('matugen', '--version')
    with tempfile.TemporaryDirectory(prefix='orbital-matugen-') as temp:
        output = runner.run(*matugen_arguments(source, mode, options, matugen_config(Path(temp))))
    return palette_from_generation(output, source, mode, options, version)


def generation_flags(parser: argparse.ArgumentParser, image: bool = False) -> None:
    parser.add_argument('--mode', choices=('dark', 'light'), default='dark')
    parser.add_argument('--type', dest='scheme_type', choices=SCHEME_TYPES, default='scheme-tonal-spot')
    parser.add_argument('--contrast', type=float, default=0.0)
    parser.add_argument('--lightness-dark', type=float, default=0.0)
    parser.add_argument('--lightness-light', type=float, default=0.0)
    parser.add_argument('--dry-run', action='store_true')
    if image:
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--source-color-index', type=int)
        group.add_argument('--prefer', choices=SOURCE_PREFERENCES)


def main() -> int:
    parser = argparse.ArgumentParser(description='Switch Orbital palettes or create one from a local wallpaper.')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='List built-in and saved palettes')
    apply = sub.add_parser('apply', help='Apply a palette; no name keeps the saved active palette')
    apply.add_argument('theme', nargs='?')
    apply.add_argument('--wallpaper', action='store_true', help='Also set the associated wallpaper')
    apply.add_argument('--dry-run', action='store_true')
    image = sub.add_parser('from-wallpaper', help='Generate a palette with Matugen and set the picture as wallpaper')
    image.add_argument('image', type=Path)
    generation_flags(image, image=True)
    color = sub.add_parser('from-color', help='Generate a palette from #RRGGBB; keep current wallpapers')
    color.add_argument('color')
    generation_flags(color)
    edit = sub.add_parser('edit', help='Open the Qt palette editor with isolated live previews')
    edit.add_argument('image', nargs='?', type=Path)
    restore = sub.add_parser('restore', help='Restore a color-switch snapshot')
    restore.add_argument('snapshot', nargs='?', type=Path)
    args = parser.parse_args()
    themes = Themes()
    try:
        if args.command == 'edit':
            try:
                from orbital_theme_editor import launch
            except ImportError as error:
                raise RuntimeError('The editor requires PyQt6 and KDE QML modules (see README.md)') from error
            return launch(args.image)
        elif args.command == 'list':
            active = themes.active().get('id')
            for palette in themes.list():
                print(f"{'*' if palette['id'] == active else ' '} {palette['id']:<40} {palette['name']}")
        elif args.command == 'restore':
            themes.restore(args.snapshot)
            print('Previous theme restored.')
        else:
            small_wallpaper = None
            if args.command in ('from-wallpaper', 'from-color'):
                options = GenerationOptions(**{key: getattr(args, key, None) for key in (
                    'scheme_type', 'contrast', 'source_color_index', 'prefer', 'lightness_dark', 'lightness_light')})
                is_image = args.command == 'from-wallpaper'
                palette = generate(args.image if is_image else args.color, args.mode,
                                   options=options, kind='image' if is_image else 'color')
                wallpaper = args.image if is_image else None
            else:
                palette = themes.load(args.theme)
                wallpaper = None
                if args.wallpaper:
                    if palette['id'].startswith('orbital-'):
                        prefix = 'orbital' if palette['mode'] == 'dark' else 'orbital-light'
                        wallpaper = ROOT / 'assets/wallpaper' / f'{prefix}-3000x2000.png'
                        small_wallpaper = ROOT / 'assets/wallpaper' / f'{prefix}-2560x1440.png'
                    else:
                        saved = themes.store / 'themes' / f"{palette['id']}.wallpaper"
                        if not saved.exists():
                            raise ValueError('This palette has no saved wallpaper')
                        wallpaper = Path(saved.read_text().strip())
            themes.apply(palette, wallpaper, args.dry_run, small_wallpaper)
    except (ValueError, OSError, RuntimeError, configparser.Error, subprocess.TimeoutExpired) as error:
        print(f'orbital-theme: {error}', file=sys.stderr)
        return 1
    return 0
