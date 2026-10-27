// SPDX-License-Identifier: MIT
import QtQuick

Item {
    id: root
    required property var disk
    DiskArc { radius: 27; lineWidth: .7; lineColor: root.disk.trackColor }
    DiskArc { radius: 15; lineWidth: .5; lineColor: root.disk.trackColor }
    DiskPath { pathData: "M5 32H59M32 5V59"; lineColor: root.disk.trackColor; lineWidth: .5 }
    DiskArc { radius: 23; lineWidth: 2.3; lineColor: root.disk.emptyColor }
    DiskArc { radius: 23; lineWidth: 2.3; lineColor: root.disk.capacityColor; sweepAngle: root.disk.usage * 3.6 }
    Item {
        width: 64; height: 64; rotation: root.disk.angle
        DiskPath { pathData: "M32 32L32 7A25 25 0 0 1 55 22Z"; shapeColor: root.disk.filledColor; opacity: root.disk.ioActive ? .18 : .04 }
        DiskPath { pathData: "M32 32V7"; lineColor: root.disk.filledColor; lineWidth: 1.4; opacity: root.disk.ioActive ? 1 : .15 }
        Rectangle { x: 46.2; y: 16.2; width: 3.6; height: width; radius: width / 2; color: root.disk.filledColor; opacity: root.disk.readOpacity }
        Rectangle { x: 16.3; y: 43.3; width: 3.4; height: width; radius: width / 2; color: root.disk.writeColor; opacity: root.disk.writeOpacity }
    }
    Rectangle { x: 17; y: 24; width: 30; height: 16; radius: 4; color: root.disk.surfaceColor }
    DiskPercent { disk: root.disk; baselineY: 35.5; pixelSize: 12.5 }
}
