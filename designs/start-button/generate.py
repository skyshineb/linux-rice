#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate launcher studies, selected production icons, and eight Moon phases.

Run from any directory: python3 designs/start-button/generate.py
Requires PyQt6 and Qt's SVG image plugin; does not change desktop settings.
The adjacent palette.json is a portable snapshot, not a live system dependency.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QGuiApplication, QImage, QImageReader, QPainter, QPainterPath, QPen

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / 'scripts'))
from orbital_moon import moon_body, moon_lit_shape

ASSETS = ROOT.parents[1] / 'assets' / 'icons'
WIDTH, MARGIN, GAP, CARD_H = 1600, 40, 20, 340
GRID_Y, HEIGHT = 168, 964


@dataclass(frozen=True)
class Icon:
    number: int
    slug: str
    title: str
    body: str
    prefix: str = ''

    @property
    def code(self) -> str:
        return f"{self.prefix}{self.number:02}"

    @property
    def filename(self) -> str:
        return f"{self.code.lower()}-{self.slug}.svg"


def point(radius: float, angle: float) -> tuple[float, float]:
    a = math.radians(angle)
    return 32 + radius * math.cos(a), 32 + radius * math.sin(a)


def arc(radius: float, start: float, end: float) -> str:
    x1, y1 = point(radius, start)
    x2, y2 = point(radius, end)
    large = int(end - start > 180)
    return f"M{x1:.3f} {y1:.3f} A{radius} {radius} 0 {large} 1 {x2:.3f} {y2:.3f}"


def collection(colors: dict[str, str]) -> list[Icon]:
    fg, accent = colors["text"], colors["cyan"]

    def stroke(d: str, color: str = fg, width: float = 2.8) -> str:
        return f'<path d="{d}" stroke="{color}" stroke-width="{width}"/>'

    def dot(x: float, y: float, r: float, color: str = fg) -> str:
        return f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r}" fill="{color}" stroke="none"/>'

    def ring(r: float, color: str = fg) -> str:
        return f'<circle cx="32" cy="32" r="{r}" stroke="{color}"/>'

    def tile(x: float, y: float, size: float, color: str = fg, radius: float = 2) -> str:
        return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{radius}" fill="{color}" stroke="none"/>'

    sectors = []
    for i in range(4):
        start, end = -85 + i * 90, -5 + i * 90
        outer1, outer2 = point(23, start), point(23, end)
        inner1, inner2 = point(12, end), point(12, start)
        d = (f"M{outer1[0]:.3f} {outer1[1]:.3f} A23 23 0 0 1 {outer2[0]:.3f} {outer2[1]:.3f} "
             f"L{inner1[0]:.3f} {inner1[1]:.3f} A12 12 0 0 0 {inner2[0]:.3f} {inner2[1]:.3f} Z")
        sectors.append(f'<path d="{d}" fill="{accent if i == 0 else fg}" stroke="none"/>')

    dot_circle = ''.join(dot(*point(22, -90 + i * 30), 2.8, accent if i == 0 else fg) for i in range(12))
    dot_square = ''.join(dot(x, y, 2.8, accent if x == 12 and y == 12 else fg)
                         for x in (12, 25.333, 38.667, 52) for y in (12, 25.333, 38.667, 52)
                         if x in (12, 52) or y in (12, 52))
    square_corners = ''.join(
        f'<path transform="rotate({i * 90} 32 32)" d="M11 26 V11 H26 V17 H17 V26 Z" '
        f'fill="{accent if i == 0 else fg}" stroke="none"/>' for i in range(4))
    hex_points = ' '.join(f'{x:.3f},{y:.3f}' for x, y in (point(25, -90 + i * 60) for i in range(6)))
    rays = ''.join(stroke(f'M{point(10, a)[0]:.3f} {point(10, a)[1]:.3f} '
                          f'L{point(25, a)[0]:.3f} {point(25, a)[1]:.3f}', width=4)
                   for a in (-90, 30, 150))
    constellation = stroke('M10 44 L23 11 L50 22 L31 36 L54 50', width=2.5)
    constellation += ''.join(dot(x, y, 3.7, accent if i == 1 else fg)
                             for i, (x, y) in enumerate(((10, 44), (23, 11), (50, 22), (31, 36), (54, 50))))

    return [
        Icon(1, 'satellite', 'Спутник', stroke(arc(21, -29, 299)) + dot(*point(21, -45), 4.3, accent)),
        Icon(2, 'open-orbit', 'Открытая орбита', stroke(arc(23, -2, 254)) + stroke(arc(23, 280, 320), accent)),
        Icon(3, 'eclipse', 'Затмение', f'<path d="M42 11.287 A23 23 0 1 0 42 52.713 A24 24 0 0 1 42 11.287 Z" fill="{fg}" stroke="none"/>' + stroke(arc(23, -40, 40), accent)),
        Icon(4, 'concentric', 'Концентрик', ring(23) + ring(12, accent)),
        Icon(5, 'three-arcs', 'Три дуги', ''.join(stroke(arc(23, -84 + i * 120, 20 + i * 120), accent if i == 0 else fg, 3.4) for i in range(3))),
        Icon(6, 'dot-orbit', 'Пунктир', dot_circle),
        Icon(7, 'horizon', 'Горизонт', ring(23) + stroke('M11 39 Q32 27 53 39', accent)),
        Icon(8, 'cross-orbits', 'Пересечение', f'<ellipse cx="32" cy="32" rx="26" ry="12" transform="rotate(45 32 32)" stroke="{fg}"/><ellipse cx="32" cy="32" rx="26" ry="12" transform="rotate(-45 32 32)" stroke="{accent}"/>'),
        Icon(9, 'core', 'Ядро', ring(23) + dot(32, 32, 6, accent)),
        Icon(10, 'four-sectors', 'Четыре сектора', ''.join(sectors)),
        Icon(11, 'four-tiles', 'Плитки', ''.join(tile(x, y, 18, accent if x == 35 and y == 11 else fg, 3) for y in (11, 35) for x in (11, 35))),
        Icon(12, 'app-grid', 'Матрица', ''.join(tile(x, y, 10, accent if x == 27 and y == 27 else fg) for y in (11, 27, 43) for x in (11, 27, 43))),
        Icon(13, 'square-core', 'Контур и ядро', f'<rect x="11" y="11" width="42" height="42" rx="3" stroke="{fg}"/>' + tile(27, 27, 10, accent, 1.5)),
        Icon(14, 'corner-frame', 'Скобки', stroke('M10 23 V10 H23 M41 10 H54 V23 M54 41 V54 H41 M23 54 H10 V41') + stroke('M10 23 V10 H23', accent)),
        Icon(15, 'square-spiral', 'Спираль', stroke('M53 11 H11 V53 H53 V23 H23 V41 H41 V32') + stroke('M41 32 H32', accent)),
        Icon(16, 'diagonal-split', 'Диагональ', f'<path d="M11 11 H48 L11 48 Z" fill="{fg}" stroke="none"/><path d="M53 16 V53 H16 Z" fill="{accent}" stroke="none"/>'),
        Icon(17, 'offset-squares', 'Смещение', f'<rect x="11" y="11" width="33" height="33" rx="2" stroke="{fg}"/><rect x="20" y="20" width="33" height="33" rx="2" stroke="{accent}"/>'),
        Icon(18, 'dot-frame', 'Точечная рамка', dot_square),
        Icon(19, 'four-corners', 'Четыре уголка', square_corners),
        Icon(20, 'vertical-bars', 'Три полосы', ''.join(f'<rect x="{x}" y="11" width="10" height="42" rx="2" fill="{accent if i == 0 else fg}" stroke="none"/>' for i, x in enumerate((11, 27, 43)))),
        Icon(21, 'hex-core', 'Гексагон', f'<polygon points="{hex_points}" stroke="{fg}"/>' + dot(32, 32, 4.5, accent)),
        Icon(22, 'triangle', 'Вектор', stroke('M32 8 L56 51 H8 Z', width=3) + dot(32, 36, 3.4, accent)),
        Icon(23, 'open-diamond', 'Разомкнутый ромб', stroke('M46 21 L57 32 L32 57 L7 32 L32 7 L39 14', accent, 3)),
        Icon(24, 'ellipse', 'Эллипс', f'<g transform="rotate(-28 32 32)"><ellipse cx="32" cy="32" rx="27" ry="13" stroke="{fg}"/>' + stroke('M57.372 36.446 A27 13 0 0 1 41.235 44.216', accent, 3.2) + '</g>'),
        Icon(25, 'three-rays', 'Три луча', rays + dot(32, 32, 4, accent)),
        Icon(26, 'four-ray-star', 'Звезда', f'<path d="M32 6 L37 26 L58 32 L37 38 L32 58 L27 38 L6 32 L27 26 Z" fill="{fg}" stroke="none"/><path d="M32 28 L36 32 L32 36 L28 32 Z" fill="{accent}" stroke="none"/>'),
        Icon(27, 'constellation', 'Созвездие', constellation),
        Icon(28, 'stepped-bars', 'Ступени', ''.join(f'<rect x="{x}" y="{y}" width="29" height="7" rx="3.5" fill="{accent if i == 2 else fg}" stroke="none"/>' for i, (x, y) in enumerate(((9, 13), (17, 28.5), (25, 44))))),
        Icon(29, 'chevrons', 'Навстречу', stroke('M24 12 L10 32 L24 52', width=3.2) + stroke('M40 12 L54 32 L40 52', accent, 3.2)),
        Icon(30, 'linked-loops', 'Связь', '<g transform="rotate(-32 32 32)">' + stroke('M29 43 H19 A11 11 0 0 1 19 21 H29 A11 11 0 0 1 40 32', width=3) + stroke('M35 21 H45 A11 11 0 0 1 45 43 H35 A11 11 0 0 1 24 32', accent, 3) + '</g>'),
    ]


def moon_collection(colors: dict[str, str]) -> list[Icon]:
    phases = (
        ('new-moon', 'Новолуние'),
        ('waxing-crescent', 'Растущий серп'),
        ('first-quarter', 'Первая четверть'),
        ('waxing-gibbous', 'Растущая Луна'),
        ('full-moon', 'Полнолуние'),
        ('waning-gibbous', 'Убывающая Луна'),
        ('last-quarter', 'Последняя четверть'),
        ('waning-crescent', 'Убывающий серп'),
    )
    icons = []
    for i, (slug, title) in enumerate(phases):
        body = moon_body((1 - math.cos(i * math.pi / 4)) / 2, i < 4, colors)
        icons.append(Icon(i + 1, slug, title, body, prefix='M'))
    return icons


def svg(icon: Icon) -> str:
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!-- SPDX-License-Identifier: MIT -->\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" '
            'fill="none" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" '
            'role="img" aria-labelledby="title">\n'
            f'  <title id="title">Orbital Start {icon.code} — {escape(icon.title)}</title>\n'
            f'  {icon.body}\n</svg>\n')


def raster(source: str, size: int) -> QImage:
    buffer = QBuffer()
    buffer.setData(QByteArray(source.encode('utf-8')))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader = QImageReader(buffer, b'svg')
    reader.setScaledSize(QSize(size, size))
    result = reader.read()
    if result.isNull():
        raise RuntimeError(f'SVG render failed: {reader.errorString()}')
    return result.convertToFormat(QImage.Format.Format_ARGB32)


def font(size: int, mono: bool = False, medium: bool = False) -> QFont:
    result = QFont('IBM Plex Mono' if mono else 'IBM Plex Sans')
    result.setPixelSize(size)
    result.setWeight(QFont.Weight.Medium if medium else QFont.Weight.Normal)
    return result


def text(p: QPainter, x: float, y: float, value: str, color: QColor | str,
         size: int = 16, mono: bool = False, medium: bool = False) -> None:
    p.setFont(font(size, mono, medium))
    p.setPen(QColor(color))
    p.drawText(QPointF(x, y), value)


def panel(p: QPainter, x: float, y: float, icon: QImage, colors: dict[str, str], height: int) -> None:
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(colors['panel']))
    p.drawRoundedRect(QRectF(x, y, 264, height), 8, 8)
    p.drawImage(QPointF(x + 12, y + (height - 40) / 2), icon)
    muted = QColor(colors['muted'])
    muted.setAlpha(95)
    p.setPen(QPen(muted, 1))
    p.drawLine(QPointF(x + 64, y + 14), QPointF(x + 64, y + height - 14))
    p.setPen(QPen(QColor(colors['muted']), 1.5, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Quiet neighboring task symbols keep the launcher sample in panel context.
    cy = y + height / 2
    folder = QPainterPath()
    folder.moveTo(x + 83, cy - 7)
    folder.lineTo(x + 90, cy - 7)
    folder.lineTo(x + 93, cy - 4)
    folder.lineTo(x + 103, cy - 4)
    folder.lineTo(x + 103, cy + 8)
    folder.lineTo(x + 83, cy + 8)
    folder.closeSubpath()
    p.drawPath(folder)
    p.drawRoundedRect(QRectF(x + 122, cy - 9, 22, 18), 3, 3)
    terminal = QPainterPath()
    terminal.moveTo(x + 128, cy - 4)
    terminal.lineTo(x + 132, cy)
    terminal.lineTo(x + 128, cy + 4)
    terminal.moveTo(x + 135, cy + 4)
    terminal.lineTo(x + 139, cy + 4)
    p.drawPath(terminal)
    text(p, x + 200, cy + 4, '40 px', colors['muted'], 12, mono=True)


def sheet(icons: list[Icon], title: str, subtitle: str, colors: dict[str, str],
          panel_height: int, destination: Path, columns: int = 5) -> None:
    if columns not in (4, 5) or len(icons) > columns * 2:
        raise ValueError('Contact sheets support two rows of four or five columns')
    card_w = (WIDTH - 2 * MARGIN - GAP * (columns - 1)) / columns
    image = QImage(WIDTH, HEIGHT, QImage.Format.Format_ARGB32)
    image.fill(QColor(colors['canvas']))
    p = QPainter(image)
    p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
    text(p, MARGIN, 55, 'ORBITAL  /  START STUDIES', colors['cyan'], 14, mono=True)
    text(p, MARGIN, 108, title, colors['text'], 38, medium=True)
    text(p, MARGIN + 2, 139, subtitle, colors['muted'], 16)
    text(p, 1390, 106, f'{icons[0].code} — {icons[-1].code}', colors['text'], 23, mono=True)

    canvas, surface = QColor(colors['canvas']), QColor(colors['panel'])
    tile_color = QColor.fromRgbF(
        canvas.redF() * .68 + surface.redF() * .32,
        canvas.greenF() * .68 + surface.greenF() * .32,
        canvas.blueF() * .68 + surface.blueF() * .32,
    )
    for i, icon in enumerate(icons):
        x = MARGIN + (i % columns) * (card_w + GAP)
        y = GRID_Y + (i // columns) * (CARD_H + GAP)
        center = x + card_w / 2
        p.setPen(QPen(QColor(colors['button']), 1))
        p.setBrush(tile_color)
        p.drawRoundedRect(QRectF(x + .5, y + .5, card_w - 1, CARD_H - 1), 14, 14)
        text(p, x + 18, y + 33, icon.code, colors['cyan'], 21, mono=True)
        text(p, x + (72 if icon.prefix else 58), y + 32, icon.title, colors['text'], 16, medium=True)
        source = svg(icon)
        p.drawImage(QPointF(center - 64, y + 65), raster(source, 128))
        p.drawImage(QPointF(center - 53, y + 215), raster(source, 24))
        p.drawImage(QPointF(center + 19, y + 211), raster(source, 32))
        text(p, center - 55, y + 259, '24 px', colors['muted'], 11, mono=True)
        text(p, center + 17, y + 259, '32 px', colors['muted'], 11, mono=True)
        panel(p, center - 132, y + 272, raster(source, 40), colors, panel_height)

    text(p, MARGIN, 925, f'ПРОЗРАЧНЫЙ ФОН  /  24 · 32 · 40 px  /  ПАНЕЛЬ {panel_height} px', colors['muted'], 13, mono=True)
    p.end()
    if not image.save(str(destination), 'PNG'):
        raise RuntimeError(f'Could not save {destination}')


def validate(icons: list[Icon], directory: Path, expected_count: int) -> None:
    if len(icons) != expected_count or [icon.number for icon in icons] != list(range(1, expected_count + 1)):
        raise RuntimeError(f'Expected exactly {expected_count} consecutively numbered designs')
    paths = sorted(directory.glob('*.svg'))
    if {p.name for p in paths} != {icon.filename for icon in icons}:
        raise RuntimeError(f'SVG output set differs from the catalog: {directory}')
    digests = set()
    for icon in icons:
        source = (directory / icon.filename).read_text(encoding='utf-8')
        xml = ET.fromstring(source)
        if xml.attrib.get('viewBox') != '0 0 64 64':
            raise RuntimeError(f'Unexpected SVG viewBox: {icon.filename}')
        digests.add(hashlib.sha256(icon.body.encode()).hexdigest())
        for size in (24, 32, 40):
            image = raster(source, size)
            occupied = [(x, y) for y in range(size) for x in range(size) if image.pixelColor(x, y).alpha() > 20]
            if not occupied:
                raise RuntimeError(f'Empty {size}px render: {icon.filename}')
            if any(x in (0, size - 1) or y in (0, size - 1) for x, y in occupied):
                raise RuntimeError(f'Artwork touches the canvas edge at {size}px: {icon.filename}')
            if any(image.pixelColor(x, y).alpha() for x, y in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1))):
                raise RuntimeError(f'Nontransparent corners: {icon.filename}')
    if len(digests) != expected_count:
        raise RuntimeError('Duplicate design geometry')


def main() -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    palette = json.loads((ROOT / 'palette.json').read_text(encoding='utf-8'))
    icons = collection(palette['colors'])
    for directory in ('icons', 'moon-phases', 'previews'):
        (ROOT / directory).mkdir(exist_ok=True)
    for icon in icons:
        (ROOT / 'icons' / icon.filename).write_text(svg(icon), encoding='utf-8')
    validate(icons, ROOT / 'icons', 30)
    ASSETS.mkdir(parents=True, exist_ok=True)
    for icon in icons[2:4]:
        selected = ASSETS / f'orbital-start-{icon.slug}.svg'
        selected.write_bytes((ROOT / 'icons' / icon.filename).read_bytes())
        print(selected.relative_to(ROOT.parents[1]))

    moons = moon_collection(palette['colors'])
    for icon in moons:
        (ROOT / 'moon-phases' / icon.filename).write_text(svg(icon), encoding='utf-8')
    validate(moons, ROOT / 'moon-phases', 8)
    groups = (
        (icons[:10], 'Круглые', 'Орбиты, дуги и сектора', '01-round.png'),
        (icons[10:20], 'Квадратные', 'Сетки, рамки и модульная геометрия', '02-square.png'),
        (icons[20:], 'Свободная форма', 'Знаки с собственным силуэтом', '03-other.png'),
    )
    for group, title, subtitle, filename in groups:
        destination = ROOT / 'previews' / filename
        sheet(group, title, subtitle, palette['colors'], palette['panel_height'], destination)
        print(destination.relative_to(ROOT))
    moon_preview = ROOT / 'previews' / '04-moon-phases.png'
    sheet(moons, 'Фазы Луны', 'В стиле «Затмение» · Северное полушарие',
          palette['colors'], palette['panel_height'], moon_preview, columns=4)
    print(moon_preview.relative_to(ROOT))
    print('Verified: 30 launcher studies + 8 Moon phases; transparent, unclipped at 24/32/40 px.')
    del app


if __name__ == '__main__':
    main()
