// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

import QtQuick

Item {
    id: root
    property color filledColor: "#67C4DE"
    property color emptyColor: "#547C8C"
    property color trackColor: "#2F4D60"
    property color textColor: "#E7EEF2"
    implicitWidth: visual.implicitWidth + 2 * effectiveHorizontalPadding
    implicitHeight: 48

    property real cpuPercent: NaN
    property int orbitStyle: 1
    property int constellationReadoutPosition: 1
    property real maxRpm: 120
    property bool animationsEnabled: true
    property real relativeSize: 110
    property real horizontalPadding: 0
    property real verticalPadding: 0

    readonly property real effectiveScale: isFinite(relativeSize)
        ? Math.max(60, Math.min(150, relativeSize)) / 100 : 1.1
    readonly property real effectiveHorizontalPadding: isFinite(horizontalPadding)
        ? Math.max(0, Math.min(32, horizontalPadding)) : 0
    readonly property real effectiveVerticalPadding: Math.min(
        isFinite(verticalPadding) ? Math.max(0, Math.min(24, verticalPadding)) : 0,
        Math.max(0, (height - 24) / 2))
    // The original gauge occupied 40 px in a 48 px panel slot. Scale from
    // that baseline, keeping all graphics inside the available panel height.
    readonly property real indicatorSize: Math.max(0, Math.min(
        height - 2 * effectiveVerticalPadding,
        Math.max(24, height * 5 / 6 * effectiveScale)))

    CpuVisual {
        filledColor: root.filledColor
        emptyColor: root.emptyColor
        trackColor: root.trackColor
        textColor: root.textColor
        id: visual
        anchors.centerIn: parent
        width: implicitWidth
        height: root.indicatorSize
        cpuPercent: root.cpuPercent
        orbitStyle: root.orbitStyle
        constellationReadoutPosition: root.constellationReadoutPosition
        maxRpm: root.maxRpm
        animationsEnabled: root.animationsEnabled
    }
}
