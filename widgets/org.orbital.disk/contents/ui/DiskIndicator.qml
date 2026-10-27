// SPDX-License-Identifier: MIT
import QtQuick
import "DiskUtils.js" as Utils

Item {
    id: root
    implicitWidth: indicatorSize * 48 / 44 + 2 * effectiveHorizontalPadding
    implicitHeight: 56
    property real relativeSize: 100
    property real horizontalPadding: 0
    property real verticalPadding: 0
    property alias meterStyle: visual.meterStyle
    property alias usedPercent: visual.usedPercent
    property alias readBytesPerSecond: visual.readBytesPerSecond
    property alias writeBytesPerSecond: visual.writeBytesPerSecond
    property alias ioScaleMBps: visual.ioScaleMBps
    property alias mountLabel: visual.mountLabel
    property alias animationsEnabled: visual.animationsEnabled
    property alias filledColor: visual.filledColor
    property alias writeColor: visual.writeColor
    property alias emptyColor: visual.emptyColor
    property alias trackColor: visual.trackColor
    property alias textColor: visual.textColor
    property alias surfaceColor: visual.surfaceColor
    property alias warningColor: visual.warningColor
    readonly property real effectiveHorizontalPadding: Utils.clamp(horizontalPadding, 0, 32, 0)
    readonly property real effectiveVerticalPadding: Math.min(Utils.clamp(verticalPadding, 0, 24, 0), Math.max(0, (height - 24) / 2))
    readonly property real indicatorSize: Math.max(0, Math.min(height - 2 * effectiveVerticalPadding,
        Math.max(24, height * 44 / 56 * Utils.clamp(relativeSize, 60, 150, 100) / 100)))
    DiskVisual { id: visual; anchors.centerIn: parent; width: root.indicatorSize; height: width }
}
