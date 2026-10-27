// SPDX-License-Identifier: MIT
import QtQuick
import "DiskUtils.js" as Utils

Item {
    id: root
    required property var disk
    Repeater {
        model: 6
        Rectangle {
            required property int index
            x: 11; y: 43 - index * 7; width: 42; height: 4.3; radius: 1.1
            color: root.disk.emptyColor
            Rectangle {
                width: parent.width * Utils.fraction(parent.index, 6, root.disk.usage)
                height: parent.height; radius: parent.radius; color: root.disk.capacityColor
            }
        }
    }
    DiskPercent { disk: root.disk; baselineY: 62; pixelSize: 12 }
    DiskLeds { disk: root.disk; centerY: 59; leftX: 12; rightX: 52 }
}
