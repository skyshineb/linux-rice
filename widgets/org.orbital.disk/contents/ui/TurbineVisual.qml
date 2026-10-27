// SPDX-License-Identifier: MIT
import QtQuick
import "DiskUtils.js" as Utils

Item {
    id: root
    required property var disk
    Item {
        width: 64; height: 64; rotation: root.disk.angle
        Repeater {
            model: 8
            Item {
                required property int index
                width: 64; height: 64; rotation: index * 45
                DiskPath { pathData: "M28 18L30 5Q41 4 45 11L36 22Z"; shapeColor: root.disk.emptyColor }
                DiskPath { pathData: "M28 18L30 5Q41 4 45 11L36 22Z"; shapeColor: root.disk.capacityColor; opacity: Utils.fraction(parent.index, 8, root.disk.usage) }
            }
        }
    }
    Rectangle { x: 18; y: 18; width: 28; height: width; radius: width / 2; color: root.disk.surfaceColor }
    DiskPercent { disk: root.disk; baselineY: 36; pixelSize: 11.5 }
    Rectangle { x: 30.7; y: 41.7; width: 2.6; height: width; radius: width / 2; color: root.disk.writeColor; opacity: root.disk.writeOpacity }
}
