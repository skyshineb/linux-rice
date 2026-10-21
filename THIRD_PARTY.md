# License coverage and third-party credits

## Orbital-authored material

Copyright © 2026 Nikolay Skovorodin. The [MIT license](LICENSE) covers the original CPU and Memory packages, installation/development scripts, the palette editor's original SVG application icon, Konsole and Zsh settings, original SVG/PNG orbital wallpapers, documentation, and original elements in the preview images. Each CPU/Memory package contains its own copy of the license for standalone distribution.

The exceptions below retain their upstream licensing. The root MIT license does not replace those terms or license externally installed icons, fonts, KDE components, or application branding visible in the desktop screenshot.

## Orbital Battery — LGPL-2.0-or-later

The entire [Battery package](widgets/org.orbital.battery/) is distributed under [LGPL-2.0-or-later](LICENSES/LGPL-2.0-or-later.txt), including Orbital's visual and configuration additions. A license copy is also included in the applet package. Original KDE copyright and SPDX notices remain in the adapted files. Orbital adaptations are copyright © 2026 Nikolay Skovorodin; the publication notices were added on 2026-10-07.

The popup originated in the Plasma 5.27 battery applet. The current port uses PowerDevil 6.6.6's battery, power profile, inhibition, and brightness QML APIs. Sources:

- [PowerDevil source](https://invent.kde.org/plasma/powerdevil)
- [PowerDevil 6.6.6 release source](https://download.kde.org/stable/plasma/6.6.6/powerdevil-6.6.6.tar.xz)
- [Package source notes](widgets/org.orbital.battery/UPSTREAM.md)

The inherited notices identify Sebastian Kügler, Viranch Mehta, Kai Uwe Broulik, Daniel Nicoletti, David Redondo, and ivan tkachenko. Their notices are preserved in the corresponding QML files.

## KDE color schemes — GPL-2.0-or-later

`assets/kde/Orbital.colors` and `assets/kde/OrbitalLight.colors` are adapted from
KDE's `BreezeDark.colors` and `BreezeLight.colors`, using Orbital's own palettes.
They and the switcher's generated KDE color schemes are distributed under
[GPL-2.0-or-later](LICENSES/GPL-2.0-or-later.txt). Both renderers preserve that notice;
this exception applies to the generated KDE schemes, not to the independently
authored Python code, JSON palettes, Konsole settings, or wallpapers.

Source: [KDE Breeze](https://invent.kde.org/plasma/breeze), supplied by `kde-style-breeze-data` 4:6.6.5-0ubuntu0.1 in the preparation environment. The installed package's copyright manifest assigns GPL-2-or-later to files without a more specific exception. Its general notices credit David Edmundson, Hugo Pereira Da Costa, Jonathan Riddell, Marco Martin, the Free Software Foundation, KDE contributors, and Rosetta Contributors / Canonical. The source color file does not carry an individual author notice. Orbital palette changes are copyright © 2026 Nikolay Skovorodin.

## External dependencies

| Dependency | Source and use |
| --- | --- |
| Tela Circle Blue | [Official Tela Circle project](https://github.com/vinceliuice/Tela-circle-icon-theme), by vinceliuice and contributors. Downloaded separately by the icon installer at commit `ee3cf47bcb05c3d99a0860b54254d2ff3d1d2c69`; icon files are not bundled here. Their upstream terms are not replaced by the Orbital license. |
| IBM Plex Sans / Mono | [IBM Plex](https://github.com/IBM/plex), copyright © 2017 IBM Corp., under the [SIL Open Font License 1.1](https://github.com/IBM/plex/blob/master/LICENSE.txt), with Reserved Font Name “Plex”. Fonts are installed separately and are not bundled here. |
| KDE Plasma, Breeze, PowerDevil, Kirigami, and system sensors | System-installed KDE components; each retains its own upstream license. Only the adapted Battery sources and color scheme described above are included here. |
| Python and Qt / PyQt6 | System runtime; Qt/PyQt6 power the optional palette editor and asset/preview generation tools. They are not bundled with Orbital. |
| Matugen | Optional image/HEX palette generator used by CLI and editor, [upstream release 4.2.0](https://github.com/InioX/matugen/releases/tag/v4.2.0), GPL-2.0. Not bundled. The Linux x86_64 installer checks the upstream archive SHA-256 `a2e3b50e49ed6439999ba3c252ed04fabd98ee4e9d12e5e5dff2e66370569751`; existing user Matugen templates and hooks are not used by Orbital. |

The desktop image is a screenshot of an Orbital-configured Plasma session. Widget galleries render the actual QML visual components with fixed sample readings. Third-party icons, fonts, and application branding in the screenshot retain their respective rights and are not offered as standalone Orbital assets.
