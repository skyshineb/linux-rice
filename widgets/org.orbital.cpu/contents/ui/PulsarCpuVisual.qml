// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

import QtQuick

Item {
    id: root
    readonly property real unit: Math.min(width, height) / 120
    property bool cpuReady: false
    property real cpuPercent: 0
    property real orbitAngle: 0

    Item {
        width: 120 * root.unit
        height: width
        anchors.centerIn: parent

        Repeater {
            model: 38
            Rectangle {
                required property int index
                readonly property real angle: index * Math.PI * 2 / 38
                width: 2 * root.unit
                height: width
                radius: width / 2
                x: (60 + Math.cos(angle) * 48) * root.unit - width / 2
                y: (60 + Math.sin(angle) * 48) * root.unit - height / 2
                color: "#547C8C"
                antialiasing: true
            }
        }

        Repeater {
            model: 2
            Rectangle {
                required property int index
                readonly property real wave: (Math.sin((root.orbitAngle * 2 + index * 180) * Math.PI / 180) + 1) / 2
                width: (35 + wave * 8) * 2 * root.unit
                height: width
                radius: width / 2
                anchors.centerIn: parent
                color: "transparent"
                border.color: "#67C4DE"
                border.width: 1.5 * root.unit
                opacity: 0.08 + wave * root.cpuPercent / 100 * 0.45
                antialiasing: true
            }
        }

        Item {
            anchors.fill: parent
            rotation: root.orbitAngle

            Rectangle {
                width: Math.sqrt(2) * 7 * root.unit
                height: width
                x: 60 * root.unit - width / 2
                y: 12 * root.unit - height / 2
                rotation: 45
                color: root.cpuReady ? "#67C4DE" : "#547C8C"
                antialiasing: true
            }

            Rectangle {
                width: 4.4 * root.unit
                height: width
                radius: width / 2
                x: 60 * root.unit - width / 2
                y: 12 * root.unit - height / 2
                color: "#E7EEF2"
                antialiasing: true
            }
        }
    }
}
