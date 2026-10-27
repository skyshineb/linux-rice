// SPDX-License-Identifier: MIT
import QtQuick

Item {
    id: root
    required property var disk
    DiskPath { pathData: "M13 9H7V55H13M51 9H57V55H51"; lineColor: root.disk.trackColor; lineWidth: 1.2 }
    Text {
        x: 14; y: 8; width: 35; height: 15
        text: root.disk.mountLabel; elide: Text.ElideRight
        font.family: "IBM Plex Mono"; font.pixelSize: 11
        color: root.disk.textColor
    }
    DiskPercent { disk: root.disk; baselineY: 43; pixelSize: root.disk.usage >= 99.5 ? 19 : 23 }
    DiskBar { disk: root.disk; x: 16; y: 51; width: 32; height: 2 }
    Rectangle { x: 52; y: 15; width: 2; height: 5; radius: 1; color: root.disk.filledColor; opacity: root.disk.readOpacity }
    Rectangle { x: 52; y: 24; width: 2; height: 5; radius: 1; color: root.disk.writeColor; opacity: root.disk.writeOpacity }
}
