// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

import QtQuick
import "contents/ui"

Rectangle {
    width: 540
    height: 320
    color: "#101D2B"

    Row {
        anchors.centerIn: parent
        spacing: 24
        Repeater {
            model: 3
            Column {
                id: styleColumn
                required property int index
                width: 148
                spacing: 10

                Text {
                    width: parent.width
                    text: ["Classic", "Constellation", "Pulsar"][styleColumn.index]
                    horizontalAlignment: Text.AlignHCenter
                    color: "#E7EEF2"
                    font.family: "IBM Plex Mono"
                    font.pixelSize: 11
                }

                Repeater {
                    model: [
                        { "height": 44, "percent": 0 },
                        { "height": 72, "percent": 50 },
                        { "height": 96, "percent": 100 }
                    ]
                    CpuVisual {
                        required property var modelData
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: implicitWidth
                        height: modelData.height
                        cpuPercent: modelData.percent
                        orbitStyle: styleColumn.index
                        orbitAngle: 32
                        animationsEnabled: false
                    }
                }
            }
        }
    }
}
