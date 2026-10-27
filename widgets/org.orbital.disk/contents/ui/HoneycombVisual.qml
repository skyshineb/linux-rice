// SPDX-License-Identifier: MIT
import QtQuick
import "DiskUtils.js" as Utils

Item {
    id: root
    required property var disk
    Repeater {
        model: Utils.honeycomb()
        Item {
            required property int index
            required property var modelData
            width: 64; height: 64
            DiskPath { pathData: Utils.hexagon(parent.modelData.x, parent.modelData.y); shapeColor: root.disk.emptyColor }
            DiskPath { pathData: Utils.hexagon(parent.modelData.x, parent.modelData.y); shapeColor: root.disk.capacityColor; opacity: Utils.fraction(parent.index, 19, root.disk.usage) }
        }
    }
    DiskPercent { disk: root.disk; baselineY: 62; pixelSize: 12 }
    DiskLeds { disk: root.disk; centerY: 59; leftX: 12; rightX: 52 }
}
