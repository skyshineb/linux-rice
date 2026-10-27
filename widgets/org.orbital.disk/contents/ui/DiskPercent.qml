// SPDX-License-Identifier: MIT
import QtQuick

Text {
    id: root
    required property var disk
    property real centerX: 32
    property real baselineY: 36.5
    property real pixelSize: 13.5
    x: centerX - width / 2
    y: baselineY - baselineOffset
    text: disk.capacityReady ? Math.round(disk.usage) + '<span style="font-size:' + pixelSize * .66 + 'px">%</span>' : "—"
    textFormat: Text.RichText
    color: disk.textColor
    font.family: "IBM Plex Mono"
    font.pixelSize: pixelSize
    font.weight: Font.Medium
    font.letterSpacing: -.7
}
