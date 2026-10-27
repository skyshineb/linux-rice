// SPDX-License-Identifier: MIT
import QtQuick
import "DiskUtils.js" as Utils

Item {
    id: root
    required property var disk
    DiskPath { pathData: Utils.spiralPath(100); lineWidth: 3.2; lineColor: root.disk.emptyColor }
    DiskPath { pathData: Utils.spiralPath(root.disk.usage); lineWidth: 3.2; lineColor: root.disk.capacityColor; visible: root.disk.usage > 0 }
    DiskPercent { disk: root.disk; baselineY: 62; pixelSize: 11.5 }
    DiskLeds { disk: root.disk; centerY: 60; leftX: 12; rightX: 52 }
}
