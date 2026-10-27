// SPDX-License-Identifier: MIT
import QtQuick

Item {
    required property var disk
    x: 10; y: 55; width: 44; height: 2.5
    Rectangle { anchors.fill: parent; radius: height / 2; color: parent.disk.emptyColor }
    Rectangle {
        width: parent.disk.usage / 100 * parent.width; height: parent.height
        radius: height / 2; color: parent.disk.capacityColor
        visible: parent.disk.capacityReady
    }
}
