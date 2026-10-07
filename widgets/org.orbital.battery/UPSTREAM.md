# Plasma battery applet source

The original Orbital popup and power data code came from the Plasma 5.27
battery applet. The Plasma 6 port uses the battery, profile, inhibition, and
brightness QML controls shipped by PowerDevil 6.6.6. Its popup components
remain adapted from KDE's LGPL-2.0-or-later applets, with SPDX headers
retained. The matching upstream release is
https://download.kde.org/stable/plasma/6.6.6/powerdevil-6.6.6.tar.xz.

`CompactRepresentation.qml` and `BatteryVisual.qml` implement the
Orbital panel design and its existing configuration keys. The custom popup
keeps battery details, brightness adjustment, power profiles, and sleep
inhibition in one place.

The entire Orbital Battery package, including its custom visuals and
configuration, is distributed under [LGPL-2.0-or-later](LICENSE). Original
KDE notices are preserved. Orbital adaptations are copyright © 2026
Nikolay Skovorodin; publication notices were added on 2026-10-07.
See [project credits](../../THIRD_PARTY.md) for license coverage and attribution.
