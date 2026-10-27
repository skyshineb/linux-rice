// SPDX-License-Identifier: MIT
import QtQuick
import "contents/ui"
import "contents/ui/DiskUtils.js" as Utils

Rectangle {
    width: 1080; height: 1140; color: "#101D2B"
    Column {
        anchors.centerIn: parent
        spacing: 15
        Text { text: "ORBITAL DISK / 9 STYLES"; color: "#67C4DE"; font.family: "IBM Plex Mono"; font.pixelSize: 20 }
        Text { text: "Демонстрационные показания · заполнение / чтение / запись"; color: "#A5B5C4"; font.pixelSize: 14 }
        Grid {
            columns: 3; spacing: 18
            Repeater {
                model: Utils.styles
                Rectangle {
                    required property int index
                    required property int modelData
                    width: 330; height: 326; radius: 8; color: "#152638"
                    Text { x: 20; y: 16; text: Utils.styleNames[parent.index]; color: "#E7EEF2"; font.family: "IBM Plex Sans"; font.pixelSize: 16 }
                    DiskVisual {
                        anchors.horizontalCenter: parent.horizontalCenter; y: 48; width: 122; height: 122
                        meterStyle: parent.modelData; usedPercent: 64; readBytesPerSecond: 280000000; writeBytesPerSecond: 96000000
                        animationsEnabled: false; surfaceColor: parent.color
                    }
                    Row {
                        x: 16; y: 192; spacing: 8
                        Repeater {
                            model: [0, 1, 90, 100, -1]
                            Column {
                                required property int modelData
                                required property int index
                                spacing: 6
                                DiskVisual {
                                    width: 52; height: 52; meterStyle: parent.parent.parent.modelData
                                    usedPercent: parent.modelData < 0 ? NaN : parent.modelData
                                    readBytesPerSecond: 0; writeBytesPerSecond: 0; animationsEnabled: false
                                    surfaceColor: "#152638"
                                }
                                Text { width: 52; text: parent.modelData < 0 ? "—" : parent.modelData + "%"; horizontalAlignment: Text.AlignHCenter; color: "#A5B5C4"; font.pixelSize: 11 }
                            }
                        }
                    }
                    DiskIndicator {
                        anchors.horizontalCenter: parent.horizontalCenter; y: 270; height: 56; width: implicitWidth
                        meterStyle: parent.modelData; usedPercent: 64; readBytesPerSecond: 280000000; writeBytesPerSecond: 96000000
                        animationsEnabled: false; surfaceColor: parent.color
                    }
                }
            }
        }
    }
}
