// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

import QtQuick

Item {
    id: root
    property color filledColor: "#67C4DE"
    property color emptyColor: "#547C8C"
    property color trackColor: "#2F4D60"
    property color textColor: "#E7EEF2"
    readonly property real unit: Math.min(width, height) / 120
    property bool cpuReady: false
    property real orbitAngle: 0

    Item {
        id: gauge
        width: 120 * root.unit
        height: width
        anchors.centerIn: parent

        Repeater {
            model: 33
            Rectangle {
                required property int index
                readonly property real angle: index * Math.PI * 2 / 33
                width: 1.8 * root.unit
                height: width
                radius: width / 2
                x: (60 + Math.cos(angle) * 47) * root.unit - width / 2
                y: (60 + Math.sin(angle) * 47) * root.unit - height / 2
                color: root.trackColor
                antialiasing: true
            }
        }

        Item {
            anchors.fill: parent
            rotation: root.orbitAngle

            Repeater {
                model: 3
                Rectangle {
                    id: linkSegment
                    required property int index
                    readonly property real firstAngle: (-90 + index * 120) * Math.PI / 180
                    readonly property real secondAngle: firstAngle + Math.PI * 2 / 3
                    readonly property real firstX: (60 + Math.cos(firstAngle) * 47) * root.unit
                    readonly property real firstY: (60 + Math.sin(firstAngle) * 47) * root.unit
                    readonly property real dx: (Math.cos(secondAngle) - Math.cos(firstAngle)) * 47 * root.unit
                    readonly property real dy: (Math.sin(secondAngle) - Math.sin(firstAngle)) * 47 * root.unit
                    x: firstX
                    y: firstY - height / 2
                    width: Math.sqrt(dx * dx + dy * dy)
                    height: Math.max(0.5, 1.3 * root.unit)
                    color: root.cpuReady ? root.filledColor : root.emptyColor
                    opacity: 0.45
                    antialiasing: true
                    transform: Rotation {
                        origin.x: 0
                        origin.y: linkSegment.height / 2
                        angle: Math.atan2(linkSegment.dy, linkSegment.dx) * 180 / Math.PI
                    }
                }
            }

            Repeater {
                model: [6, 4.5, 3.5]
                Item {
                    required property int index
                    required property real modelData
                    readonly property real angle: (-90 + index * 120) * Math.PI / 180
                    readonly property real dotRadius: modelData * root.unit
                    x: (60 + Math.cos(angle) * 47) * root.unit
                    y: (60 + Math.sin(angle) * 47) * root.unit

                    Rectangle {
                        x: -dotRadius
                        y: -dotRadius
                        width: 2 * dotRadius
                        height: width
                        radius: dotRadius
                        color: root.cpuReady ? root.filledColor : root.emptyColor
                        antialiasing: true
                    }

                    Rectangle {
                        x: -0.47 * dotRadius
                        y: -0.51 * dotRadius
                        width: 0.5 * dotRadius
                        height: width
                        radius: width / 2
                        color: root.textColor
                        antialiasing: true
                    }
                }
            }
        }
    }
}
