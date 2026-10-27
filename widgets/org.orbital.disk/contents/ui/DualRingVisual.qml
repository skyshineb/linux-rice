// SPDX-License-Identifier: MIT
import QtQuick

Item {
    id: root
    required property var disk
    DiskArc { radius: 26; lineWidth: 3.5; lineColor: root.disk.emptyColor }
    DiskArc { radius: 26; lineWidth: 3.5; lineColor: root.disk.capacityColor; sweepAngle: root.disk.usage * 3.6 }
    DiskArc { radius: 19.5; lineWidth: 2; lineColor: root.disk.emptyColor }
    DiskArc { radius: 19.5; lineWidth: 2; lineColor: root.disk.filledColor; startAngle: 30; sweepAngle: root.disk.activityLevel * 360 }
    DiskPercent { disk: root.disk; pixelSize: 12.5 }
    DiskLeds { disk: root.disk; centerY: 44.5; leftX: 28; rightX: 36 }
}
