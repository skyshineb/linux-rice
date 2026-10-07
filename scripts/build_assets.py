#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

"""Build the Orbital color scheme and two resolution-matched wallpapers."""

from __future__ import annotations

import configparser
import os
import random
from pathlib import Path

from PyQt6.QtGui import QGuiApplication, QImageReader


ROOT = Path(__file__).resolve().parent.parent
WALLPAPER_DIR = ROOT / "assets" / "wallpaper"
SCHEME_PATH = ROOT / "assets" / "kde" / "Orbital.colors"
SOURCE_SCHEME = Path("/usr/share/color-schemes/BreezeDark.colors")

SCHEME_NOTICE = """# SPDX-License-Identifier: GPL-2.0-or-later
# Derived from KDE Breeze Dark; see THIRD_PARTY.md.
# Orbital palette: Copyright (c) 2026 Nikolay Skovorodin.
# Publication notice added 2026-10-07.

"""

COLORS = {
    "canvas": "#0B1420",
    "panel": "#101D2B",
    "window": "#152638",
    "button": "#1C3144",
    "selected": "#20566E",
    "text": "#E7EEF2",
    "muted": "#A5B5C4",
    "cyan": "#67C4DE",
    "amber": "#E6B96A",
    "red": "#E4818A",
    "green": "#74C69D",
    "violet": "#A998D8",
}


def rgb(value: str) -> str:
    return ",".join(str(int(value[i : i + 2], 16)) for i in (1, 3, 5))


def build_scheme() -> None:
    scheme = configparser.ConfigParser(interpolation=None, strict=False)
    scheme.optionxform = str
    with SOURCE_SCHEME.open(encoding="utf-8") as handle:
        scheme.read_file(handle)

    backgrounds = {
        "Colors:Window": ("window", "panel"),
        "Colors:View": ("canvas", "window"),
        "Colors:Button": ("button", "window"),
        "Colors:Header": ("panel", "window"),
        "Colors:Header][Inactive": ("canvas", "panel"),
        "Colors:Complementary": ("panel", "canvas"),
        "Colors:Selection": ("selected", "button"),
        "Colors:Tooltip": ("button", "window"),
    }
    roles = {
        "DecorationFocus": "cyan",
        "DecorationHover": "cyan",
        "ForegroundActive": "cyan",
        "ForegroundInactive": "muted",
        "ForegroundLink": "cyan",
        "ForegroundNegative": "red",
        "ForegroundNeutral": "amber",
        "ForegroundNormal": "text",
        "ForegroundPositive": "green",
        "ForegroundVisited": "violet",
    }
    for section in scheme.sections():
        if not section.startswith("Colors:"):
            continue
        background, alternate = backgrounds.get(section, ("window", "panel"))
        for key, color in (("BackgroundNormal", background), ("BackgroundAlternate", alternate)):
            if key in scheme[section]:
                scheme[section][key] = rgb(COLORS[color])
        for key, color in roles.items():
            if key in scheme[section]:
                scheme[section][key] = rgb(COLORS[color])

    general = scheme["General"]
    for key in list(general):
        if key.startswith("Name["):
            del general[key]
    general["ColorScheme"] = "Orbital"
    general["Name"] = "Orbital"
    wm = scheme["WM"]
    wm["activeBackground"] = rgb(COLORS["panel"])
    wm["activeBlend"] = rgb(COLORS["text"])
    wm["activeForeground"] = rgb(COLORS["text"])
    wm["inactiveBackground"] = rgb(COLORS["canvas"])
    wm["inactiveBlend"] = rgb(COLORS["muted"])
    wm["inactiveForeground"] = rgb(COLORS["muted"])

    SCHEME_PATH.parent.mkdir(parents=True, exist_ok=True)
    from io import StringIO

    output = StringIO()
    scheme.write(output, space_around_delimiters=False)
    SCHEME_PATH.write_text(SCHEME_NOTICE + output.getvalue().rstrip() + "\n", encoding="utf-8")


def wallpaper_svg(width: int, height: int) -> str:
    w, h = width, height
    rng = random.Random(27)
    stars = []
    for _ in range(95):
        x, y = rng.uniform(0.03, 0.97) * w, rng.uniform(0.11, 0.72) * h
        radius = rng.choice((0.7, 1.0, 1.3, 1.8)) * w / 3000
        opacity = rng.uniform(0.10, 0.34)
        stars.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.2f}" fill="#D9EAF1" opacity="{opacity:.2f}"/>')
    grid = []
    for i in range(1, 16):
        x = w * i / 16
        grid.append(f'<path d="M{x:.1f},0 V{h}" stroke="#86B5C5" opacity="0.045"/>')
    for i in range(1, 10):
        y = h * i / 10
        grid.append(f'<path d="M0,{y:.1f} H{w}" stroke="#86B5C5" opacity="0.045"/>')

    earth = (
        f"M {-0.12*w:.1f},{1.06*h:.1f} "
        f"C {0.17*w:.1f},{0.62*h:.1f} {0.83*w:.1f},{0.62*h:.1f} "
        f"{1.12*w:.1f},{1.06*h:.1f} "
        f"L {1.12*w:.1f},{1.3*h:.1f} L {-0.12*w:.1f},{1.3*h:.1f} Z"
    )
    horizon = (
        f"M {-0.12*w:.1f},{1.06*h:.1f} "
        f"C {0.17*w:.1f},{0.62*h:.1f} {0.83*w:.1f},{0.62*h:.1f} "
        f"{1.12*w:.1f},{1.06*h:.1f}"
    )
    label_size = max(16, round(w / 145))
    stars_xml = "\n    ".join(stars)
    grid_xml = "\n    ".join(grid)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="space" x1="0" y1="0" x2="0.55" y2="1">
      <stop offset="0" stop-color="#07111D"/>
      <stop offset="0.65" stop-color="{COLORS['canvas']}"/>
      <stop offset="1" stop-color="#153047"/>
    </linearGradient>
    <linearGradient id="earth" x1="0" y1="0" x2="0.15" y2="1">
      <stop offset="0" stop-color="#254457"/>
      <stop offset="0.18" stop-color="#172E40"/>
      <stop offset="1" stop-color="#060D16"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#space)"/>
  <g fill="none" stroke-width="1">{grid_xml}</g>
  <g>{stars_xml}</g>
  <g fill="none" stroke="{COLORS['cyan']}">
    <ellipse cx="{0.50*w:.1f}" cy="{0.56*h:.1f}" rx="{0.57*w:.1f}" ry="{0.36*h:.1f}" opacity="0.10" stroke-width="2"/>
    <ellipse cx="{0.51*w:.1f}" cy="{0.58*h:.1f}" rx="{0.65*w:.1f}" ry="{0.41*h:.1f}" opacity="0.07" stroke-width="1.5"/>
    <path d="M {0.05*w:.1f},{0.31*h:.1f} H {0.12*w:.1f} M {0.08*w:.1f},{0.28*h:.1f} V {0.34*h:.1f}" opacity="0.27" stroke-width="2"/>
    <circle cx="{0.79*w:.1f}" cy="{0.34*h:.1f}" r="{0.009*w:.1f}" opacity="0.35" stroke-width="2"/>
    <path d="M {0.79*w:.1f},{0.30*h:.1f} V {0.38*h:.1f} M {0.77*w:.1f},{0.34*h:.1f} H {0.81*w:.1f}" opacity="0.16" stroke-width="1"/>
  </g>
  <path d="{earth}" fill="url(#earth)"/>
  <path d="{horizon}" fill="none" stroke="{COLORS['cyan']}" stroke-width="{0.018*w:.1f}" opacity="0.045"/>
  <path d="{horizon}" fill="none" stroke="{COLORS['cyan']}" stroke-width="{0.006*w:.1f}" opacity="0.14"/>
  <path d="{horizon}" fill="none" stroke="#B7E2EA" stroke-width="{0.0009*w:.1f}" opacity="0.47"/>
  <g fill="{COLORS['muted']}" opacity="0.32" font-family="IBM Plex Mono, monospace" font-size="{label_size}" letter-spacing="3">
    <text x="{0.054*w:.1f}" y="{0.105*h:.1f}">ORBITAL / 001</text>
    <text x="{0.79*w:.1f}" y="{0.105*h:.1f}">EARTH REFERENCE</text>
  </g>
  <g fill="none" stroke="{COLORS['cyan']}" opacity="0.22" stroke-width="2">
    <path d="M {0.054*w:.1f},{0.12*h:.1f} H {0.15*w:.1f}"/>
    <path d="M {0.79*w:.1f},{0.12*h:.1f} H {0.945*w:.1f}"/>
  </g>
</svg>
'''


def build_wallpaper(width: int, height: int) -> None:
    stem = f"orbital-{width}x{height}"
    svg_path = WALLPAPER_DIR / f"{stem}.svg"
    png_path = WALLPAPER_DIR / f"{stem}.png"
    svg_path.write_text(wallpaper_svg(width, height), encoding="utf-8")
    reader = QImageReader(str(svg_path), b"svg")
    image = reader.read()
    if image.isNull() or image.width() != width or image.height() != height:
        raise RuntimeError(f"Could not render {svg_path}: {reader.errorString()}")
    if not image.save(str(png_path), "PNG"):
        raise RuntimeError(f"Could not save {png_path}")


def main() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication([])
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    build_scheme()
    for size in ((3000, 2000), (2560, 1440)):
        build_wallpaper(*size)
    del app
    print("Built Orbital color scheme and wallpapers.")


if __name__ == "__main__":
    main()
