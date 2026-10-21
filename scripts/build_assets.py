#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

"""Build the Orbital color scheme and two resolution-matched wallpapers."""

from __future__ import annotations

import argparse
import os
import random
from pathlib import Path

from orbital_themes import ROOT, builtin, render_scheme, render_terminal


WALLPAPER_DIR = ROOT / "assets" / "wallpaper"


def build_scheme(palette: dict) -> None:
    light = palette["mode"] == "light"
    source = Path("/usr/share/color-schemes") / ("BreezeLight.colors" if light else "BreezeDark.colors")
    filename = "OrbitalLight" if light else "Orbital"
    (ROOT / "assets/kde" / f"{filename}.colors").write_text(
        render_scheme(palette, source, filename), encoding="utf-8")
    (ROOT / "assets/konsole" / f"{filename}.colorscheme").write_text(
        render_terminal(palette), encoding="utf-8")


def wallpaper_svg(width: int, height: int, palette: dict | None = None) -> str:
    w, h = width, height
    palette = palette or builtin("orbital-dark")
    colors = palette["colors"]
    artwork = palette["wallpaper"]
    rng = random.Random(27)
    stars = []
    for _ in range(95):
        x, y = rng.uniform(0.03, 0.97) * w, rng.uniform(0.11, 0.72) * h
        radius = rng.choice((0.7, 1.0, 1.3, 1.8)) * w / 3000
        opacity = rng.uniform(0.10, 0.34)
        stars.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.2f}" fill="{artwork['stars']}" opacity="{opacity:.2f}"/>')
    grid = []
    for i in range(1, 16):
        x = w * i / 16
        grid.append(f'<path d="M{x:.1f},0 V{h}" stroke="{artwork['grid']}" opacity="0.045"/>')
    for i in range(1, 10):
        y = h * i / 10
        grid.append(f'<path d="M0,{y:.1f} H{w}" stroke="{artwork['grid']}" opacity="0.045"/>')

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
      <stop offset="0" stop-color="{artwork['spaceTop']}"/>
      <stop offset="0.65" stop-color="{colors['canvas']}"/>
      <stop offset="1" stop-color="{artwork['spaceBottom']}"/>
    </linearGradient>
    <linearGradient id="earth" x1="0" y1="0" x2="0.15" y2="1">
      <stop offset="0" stop-color="{artwork['earthTop']}"/>
      <stop offset="0.18" stop-color="{artwork['earthMid']}"/>
      <stop offset="1" stop-color="{artwork['earthBottom']}"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#space)"/>
  <g fill="none" stroke-width="1">{grid_xml}</g>
  <g>{stars_xml}</g>
  <g fill="none" stroke="{colors['cyan']}">
    <ellipse cx="{0.50*w:.1f}" cy="{0.56*h:.1f}" rx="{0.57*w:.1f}" ry="{0.36*h:.1f}" opacity="0.10" stroke-width="2"/>
    <ellipse cx="{0.51*w:.1f}" cy="{0.58*h:.1f}" rx="{0.65*w:.1f}" ry="{0.41*h:.1f}" opacity="0.07" stroke-width="1.5"/>
    <path d="M {0.05*w:.1f},{0.31*h:.1f} H {0.12*w:.1f} M {0.08*w:.1f},{0.28*h:.1f} V {0.34*h:.1f}" opacity="0.27" stroke-width="2"/>
    <circle cx="{0.79*w:.1f}" cy="{0.34*h:.1f}" r="{0.009*w:.1f}" opacity="0.35" stroke-width="2"/>
    <path d="M {0.79*w:.1f},{0.30*h:.1f} V {0.38*h:.1f} M {0.77*w:.1f},{0.34*h:.1f} H {0.81*w:.1f}" opacity="0.16" stroke-width="1"/>
  </g>
  <path d="{earth}" fill="url(#earth)"/>
  <path d="{horizon}" fill="none" stroke="{colors['cyan']}" stroke-width="{0.018*w:.1f}" opacity="0.045"/>
  <path d="{horizon}" fill="none" stroke="{colors['cyan']}" stroke-width="{0.006*w:.1f}" opacity="0.14"/>
  <path d="{horizon}" fill="none" stroke="{artwork['horizon']}" stroke-width="{0.0009*w:.1f}" opacity="0.47"/>
  <g fill="{colors['muted']}" opacity="0.32" font-family="IBM Plex Mono, monospace" font-size="{label_size}" letter-spacing="3">
    <text x="{0.054*w:.1f}" y="{0.105*h:.1f}">ORBITAL / 001</text>
    <text x="{0.79*w:.1f}" y="{0.105*h:.1f}">EARTH REFERENCE</text>
  </g>
  <g fill="none" stroke="{colors['cyan']}" opacity="0.22" stroke-width="2">
    <path d="M {0.054*w:.1f},{0.12*h:.1f} H {0.15*w:.1f}"/>
    <path d="M {0.79*w:.1f},{0.12*h:.1f} H {0.945*w:.1f}"/>
  </g>
</svg>
'''


def build_wallpaper(width: int, height: int, palette: dict) -> None:
    from PyQt6.QtGui import QImageReader
    prefix = "orbital-light" if palette["mode"] == "light" else "orbital"
    stem = f"{prefix}-{width}x{height}"
    svg_path = WALLPAPER_DIR / f"{stem}.svg"
    png_path = WALLPAPER_DIR / f"{stem}.png"
    svg_path.write_text(wallpaper_svg(width, height, palette), encoding="utf-8")
    reader = QImageReader(str(svg_path), b"svg")
    image = reader.read()
    if image.isNull() or image.width() != width or image.height() != height:
        raise RuntimeError(f"Could not render {svg_path}: {reader.errorString()}")
    if not image.save(str(png_path), "PNG"):
        raise RuntimeError(f"Could not save {png_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("orbital-dark", "orbital-light"), default="orbital-dark")
    parser.add_argument("--all", action="store_true", help="Build both bundled palettes")
    args = parser.parse_args()
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PyQt6.QtGui import QGuiApplication
    app = QGuiApplication([])
    WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("orbital-dark", "orbital-light") if args.all else (args.theme,):
        palette = builtin(name)
        build_scheme(palette)
        for size in ((3000, 2000), (2560, 1440)):
            build_wallpaper(*size, palette)
        print(f"Built {palette['name']} color schemes and wallpapers.")
    del app


if __name__ == "__main__":
    main()
