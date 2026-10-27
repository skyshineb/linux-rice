// SPDX-License-Identifier: MIT
import QtQuick

Item {
    id: root
    required property var disk
    DiskPercent { disk: root.disk; baselineY: 18; pixelSize: 15 }
    DiskPath { pathData: "M6 35H58"; lineColor: root.disk.trackColor; lineWidth: .6 }
    DiskPath { pathData: "M14 27L22 35L14 43M26 27L34 35L26 43"; lineColor: root.disk.filledColor; lineWidth: 2.5; opacity: root.disk.readOpacity }
    DiskPath { pathData: "M50 27L42 35L50 43M38 27L30 35L38 43"; lineColor: root.disk.writeColor; lineWidth: 2.5; opacity: root.disk.writeOpacity }
    DiskBar { disk: root.disk; x: 9; y: 54; width: 46; height: 3 }
}
