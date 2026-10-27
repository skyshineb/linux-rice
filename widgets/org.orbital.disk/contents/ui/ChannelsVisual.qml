// SPDX-License-Identifier: MIT
import QtQuick

Item {
    id: root
    required property var disk
    DiskPercent { disk: root.disk; baselineY: 17; pixelSize: 14 }
    Repeater {
        model: 3
        Item {
            id: channel
            required property int index
            readonly property real level: index === 0 ? root.disk.usage / 100 : index === 1 ? root.disk.readLevel : root.disk.writeLevel
            readonly property color activeColor: index === 0 ? root.disk.capacityColor : index === 1 ? root.disk.filledColor : root.disk.writeColor
            x: 12 + index * 16; width: 9; height: 64
            Rectangle { y: 24; width: 9; height: 27; radius: 1.2; color: root.disk.emptyColor }
            Rectangle { y: 51 - height; width: 9; height: 27 * channel.level; radius: 1.2; color: channel.activeColor }
            Text { y: 52; width: 9; height: 12; text: ["C", "R", "W"][channel.index]; color: root.disk.textColor; horizontalAlignment: Text.AlignHCenter; font.family: "IBM Plex Mono"; font.pixelSize: 9 }
        }
    }
}
