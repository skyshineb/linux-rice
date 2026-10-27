// SPDX-License-Identifier: MIT
import QtQuick

Item {
    required property var disk
    property real leftX: 24
    property real rightX: 40
    property real centerY: 59
    property real dotRadius: 1.35
    width: 64; height: 64
    Rectangle {
        x: parent.leftX - parent.dotRadius; y: parent.centerY - parent.dotRadius
        width: parent.dotRadius * 2; height: width; radius: width / 2
        color: parent.disk.filledColor; opacity: parent.disk.readOpacity
    }
    Rectangle {
        x: parent.rightX - parent.dotRadius; y: parent.centerY - parent.dotRadius
        width: parent.dotRadius * 2; height: width; radius: width / 2
        color: parent.disk.writeColor; opacity: parent.disk.writeOpacity
    }
}
