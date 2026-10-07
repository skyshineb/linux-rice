// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

import QtQuick

Item {
    id: root
    implicitWidth: 44
    implicitHeight: 44

    property real ramPercent: NaN
    property real swapPercent: NaN
    property bool showSwapGauge: true
    property color swapColor: "#E6B96A"
    property color filledColor: "#70D4E8"
    property color emptyColor: "#315262"
    property color textColor: "#E9F6F8"
    readonly property real unit: Math.min(width, height) / 40
    readonly property bool ramReady: isFinite(ramPercent)
    readonly property real clampedPercent: ramReady ? Math.max(0, Math.min(100, ramPercent)) : 0
    readonly property int displayPercent: Math.round(clampedPercent)
    readonly property int filledTicks: ramReady ? Math.round(clampedPercent * 17 / 100) : 0
    readonly property real clampedSwapPercent: isFinite(swapPercent) ? Math.max(0, Math.min(100, swapPercent)) : 0
    readonly property int filledSwapTicks: clampedSwapPercent > 0
        ? Math.max(1, Math.round(clampedSwapPercent * 5 / 100)) : 0

    Item {
        id: dial
        width: 44 * root.unit
        height: width
        anchors.centerIn: parent
        // Restore the original top-heavy dial's alignment when swap is hidden.
        anchors.verticalCenterOffset: root.showSwapGauge ? 0 : 4 * root.unit

        Repeater {
            model: 17
            Rectangle {
                readonly property real angle: (-210 + index * 15) * Math.PI / 180
                width: 1.8 * root.unit
                height: 4 * root.unit
                radius: width / 2
                x: dial.width / 2 + Math.cos(angle) * 15.8 * root.unit - width / 2
                y: dial.height / 2 + Math.sin(angle) * 15.8 * root.unit - height / 2
                rotation: -120 + index * 15
                color: root.ramReady && index < root.filledTicks ? root.filledColor : root.emptyColor
                Behavior on color { ColorAnimation { duration: 160 } }
            }
        }

        Repeater {
            model: root.showSwapGauge ? 5 : 0
            Rectangle {
                readonly property real angle: (120 - index * 15) * Math.PI / 180
                width: 1.8 * root.unit
                height: 4 * root.unit
                radius: width / 2
                x: dial.width / 2 + Math.cos(angle) * 15.8 * root.unit - width / 2
                y: dial.height / 2 + Math.sin(angle) * 15.8 * root.unit - height / 2
                rotation: 210 - index * 15
                color: root.swapColor
                opacity: index < root.filledSwapTicks ? 1 : 0.25
                Behavior on opacity { NumberAnimation { duration: 160 } }
            }
        }

        Text {
            anchors.centerIn: parent
            text: root.ramReady ? root.displayPercent + "%" : "—"
            color: root.ramReady ? root.textColor : root.emptyColor
            font.family: "IBM Plex Mono"
            font.pixelSize: Math.max(8, Math.round(10 * root.unit))
            font.weight: Font.DemiBold
        }
    }
}
