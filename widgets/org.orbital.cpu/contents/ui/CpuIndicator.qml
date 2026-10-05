import QtQuick

Item {
    id: root
    implicitWidth: visual.implicitWidth + 2 * effectiveHorizontalPadding
    implicitHeight: 48

    property real cpuPercent: NaN
    property int orbitStyle: 0
    property int constellationReadoutPosition: 0
    property real maxRpm: 30
    property bool animationsEnabled: true
    property real relativeSize: 100
    property real horizontalPadding: 4
    property real verticalPadding: 4

    readonly property real effectiveScale: isFinite(relativeSize)
        ? Math.max(60, Math.min(150, relativeSize)) / 100 : 1
    readonly property real effectiveHorizontalPadding: isFinite(horizontalPadding)
        ? Math.max(0, Math.min(32, horizontalPadding)) : 4
    readonly property real effectiveVerticalPadding: Math.min(
        isFinite(verticalPadding) ? Math.max(0, Math.min(24, verticalPadding)) : 4,
        Math.max(0, (height - 24) / 2))
    // The original gauge occupied 40 px in a 48 px panel slot. Scale from
    // that baseline, keeping all graphics inside the available panel height.
    readonly property real indicatorSize: Math.max(0, Math.min(
        height - 2 * effectiveVerticalPadding,
        Math.max(24, height * 5 / 6 * effectiveScale)))

    CpuVisual {
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
