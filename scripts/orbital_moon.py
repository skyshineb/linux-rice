# SPDX-License-Identifier: MIT
"""Offline lunar ephemeris, theme colors, and reusable north-up SVG geometry."""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
import math
import os
from pathlib import Path
import re

DEFAULT_COLORS = {'text': '#CCCCCC', 'cyan': '#39B7E9', 'muted': '#A9A9A9'}


@dataclass(frozen=True)
class MoonState:
    utc: str
    phase: float
    illumination: float
    waxing: bool


def moon_state(moment: datetime | None = None) -> MoonState:
    from vendor import astronomy

    moment = moment or datetime.now(timezone.utc)
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError('Specify a timezone, for example 2026-10-22T12:00:00Z')
    moment = moment.astimezone(timezone.utc)
    time = astronomy.Time.Make(moment.year, moment.month, moment.day, moment.hour,
                               moment.minute, moment.second + moment.microsecond / 1e6)
    angle = astronomy.MoonPhase(time)
    illuminated = astronomy.Illumination(astronomy.Body.Moon, time).phase_fraction
    return MoonState(moment.isoformat(), angle / 360, illuminated, angle < 180)


def lit_shape(illumination: float, waxing: bool, color: str) -> str:
    """Enclose the illuminated projection between a limb and a terminator."""
    if not math.isfinite(illumination) or not 0 <= illumination <= 1:
        raise ValueError('Illumination must be between 0 and 1')
    if illumination < 1e-12:
        return ''
    if 1 - illumination < 1e-12:
        return f'<circle cx="32" cy="32" r="23" fill="{color}" stroke="none"/>'
    cosine = 1 - 2 * illumination
    d = f'M32 9 A23 23 0 0 {1 if waxing else 0} 32 55 '
    if abs(cosine) < 1e-12:
        d += 'L32 9 Z'
    else:
        on_right = cosine > 0 if waxing else cosine < 0
        d += f'A{23 * abs(cosine):.6f} 23 0 0 {0 if on_right else 1} 32 9 Z'
    return f'<path d="{d}" fill="{color}" stroke="none"/>'


def moon_lit_shape(phase: float, color: str) -> str:
    """Idealized phase geometry for the eight evenly spaced design studies."""
    if not math.isfinite(phase):
        raise ValueError('Moon phase must be finite')
    phase %= 1
    return lit_shape((1 - math.cos(2 * math.pi * phase)) / 2, phase < .5, color)


def moon_body(illumination: float, waxing: bool, colors: dict[str, str]) -> str:
    for key in DEFAULT_COLORS:
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', colors[key]):
            raise ValueError(f'Invalid {key} color')
    body = lit_shape(illumination, waxing, colors['text'])
    if illumination < .01:
        body += (f'<circle cx="32" cy="32" r="23" stroke="{colors["muted"]}" '
                 'stroke-opacity="0.45" stroke-width="1.5"/>')
    # Same constant 80-degree accent arc as the approved Eclipse launcher.
    body += ('<path d="M49.619 17.216 A23 23 0 0 1 49.619 46.784" '
             f'stroke="{colors["cyan"]}" stroke-width="2.8"/>')
    return body


def moon_svg(state: MoonState, colors: dict[str, str]) -> str:
    direction = 'waxing' if state.waxing else 'waning'
    title = escape(f'Orbital Moon — {state.illumination:.1%} illuminated, {direction}')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!-- SPDX-License-Identifier: MIT -->\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" '
            'fill="none" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" '
            'role="img" aria-labelledby="title">\n'
            f'  <title id="title">{title}</title>\n'
            f'  {moon_body(state.illumination, state.waxing, colors)}\n</svg>\n')


def ini(path: Path | None = None) -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    if path is not None:
        parser.read(path, encoding='utf-8')
    return parser


def color_hex(value: str) -> str:
    if re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        return value.upper()
    parts = value.split(',')
    if len(parts) not in (3, 4) or any(not p.strip().isdigit() for p in parts):
        raise ValueError(f'Invalid KDE color: {value!r}')
    numbers = [int(part) for part in parts]
    if any(not 0 <= number <= 255 for number in numbers):
        raise ValueError('KDE color component outside 0–255')
    return '#' + ''.join(f'{number:02X}' for number in numbers[:3])


def theme_colors(config: Path, data: Path) -> dict[str, str]:
    globals_path = config / 'kdeglobals'
    overrides = ini(globals_path)
    palette = ini()
    scheme = overrides.get('General', 'ColorScheme', fallback='')
    if scheme and Path(scheme).name == scheme:
        roots = [data, *(Path(p) for p in os.environ.get(
            'XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(os.pathsep) if p)]
        for root in roots:
            source = root / 'color-schemes' / f'{scheme}.colors'
            if source.is_file():
                palette.read(source, encoding='utf-8')
                break
    palette.read(globals_path, encoding='utf-8')
    result = {}
    for role, key in [('text', 'ForegroundNormal'), ('cyan', 'ForegroundLink'),
                      ('muted', 'ForegroundInactive')]:
        value = next((palette.get(section, key) for section in
                      ('Colors:Complementary', 'Colors:Window') if palette.has_option(section, key)), None)
        result[role] = color_hex(value) if value is not None else DEFAULT_COLORS[role]
    return result
