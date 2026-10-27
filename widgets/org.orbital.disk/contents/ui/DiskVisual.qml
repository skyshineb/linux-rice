// SPDX-License-Identifier: MIT
import QtQuick
import "DiskUtils.js" as Utils

Item {
    id: root
    implicitWidth: 44; implicitHeight: 44
    property int meterStyle: 19
    property real usedPercent: NaN
    property real readBytesPerSecond: NaN
    property real writeBytesPerSecond: NaN
    property string mountLabel: "/"
    property real ioScaleMBps: 400
    property bool animationsEnabled: true
    property color filledColor: "#67C4DE"
    property color writeColor: "#E6B96A"
    property color emptyColor: "#335363"
    property color trackColor: "#547C8C"
    property color textColor: "#E7EEF2"
    property color surfaceColor: "#101D2B"
    property color warningColor: "#E4818A"

    readonly property int effectiveStyle: Utils.style(meterStyle)
    readonly property bool capacityReady: isFinite(Utils.reading(usedPercent))
    readonly property real usage: Utils.clamp(Utils.reading(usedPercent), 0, 100, 0)
    readonly property color capacityColor: capacityReady && usage >= 90 ? warningColor : filledColor
    readonly property bool readReady: isFinite(Utils.reading(readBytesPerSecond))
    readonly property bool writeReady: isFinite(Utils.reading(writeBytesPerSecond))
    readonly property real readLevel: Utils.rateLevel(readBytesPerSecond, ioScaleMBps)
    readonly property real writeLevel: Utils.rateLevel(writeBytesPerSecond, ioScaleMBps)
    readonly property real activityLevel: readReady && writeReady ? Utils.rateLevel(readBytesPerSecond + writeBytesPerSecond, ioScaleMBps) : 0
    readonly property bool ioActive: (readReady && readBytesPerSecond > 0) || (writeReady && writeBytesPerSecond > 0)
    readonly property real readOpacity: readReady && readBytesPerSecond > 0 ? readPulse : .15
    readonly property real writeOpacity: writeReady && writeBytesPerSecond > 0 ? writePulse : .15
    readonly property real rpm: ioActive ? 4 + 26 * Math.min(1, readLevel + writeLevel) : 0
    readonly property bool rotationRunning: visible && animationsEnabled && ioActive && (effectiveStyle === 16 || effectiveStyle === 17)
    readonly property var visualItem: styleLoader.item
    property real angle: 0
    property real readPulse: 1
    property real writePulse: 1
    readonly property var styleSources: ({2: "DualRingVisual.qml", 4: "SpiralVisual.qml", 13: "ArchiveVisual.qml",
        14: "PacketsVisual.qml", 16: "RadarVisual.qml", 17: "TurbineVisual.qml", 18: "HoneycombVisual.qml",
        19: "TerminalVisual.qml", 20: "ChannelsVisual.qml"})

    Accessible.role: Accessible.Indicator
    Accessible.name: "Disk " + mountLabel
    Accessible.description: (capacityReady ? Math.round(usage) + "%" : "—")

    Item {
        width: 64; height: 64; anchors.centerIn: parent
        scale: Math.max(0, Math.min(root.width, root.height)) / 64
        Loader { id: styleLoader; anchors.fill: parent }
    }
    function loadStyle() { styleLoader.setSource(Qt.resolvedUrl(styleSources[effectiveStyle]), {disk: root}) }
    onEffectiveStyleChanged: loadStyle()
    Component.onCompleted: loadStyle()

    SequentialAnimation {
        running: root.visible && root.animationsEnabled && root.readReady && root.readBytesPerSecond > 0
        loops: Animation.Infinite
        onRunningChanged: if (!running) root.readPulse = 1
        NumberAnimation { target: root; property: "readPulse"; from: 1; to: .35; duration: 850; easing.type: Easing.InOutSine }
        NumberAnimation { target: root; property: "readPulse"; from: .35; to: 1; duration: 850; easing.type: Easing.InOutSine }
    }
    SequentialAnimation {
        running: root.visible && root.animationsEnabled && root.writeReady && root.writeBytesPerSecond > 0
        loops: Animation.Infinite
        onRunningChanged: if (!running) root.writePulse = 1
        NumberAnimation { target: root; property: "writePulse"; from: 1; to: .3; duration: 600; easing.type: Easing.InOutSine }
        NumberAnimation { target: root; property: "writePulse"; from: .3; to: 1; duration: 600; easing.type: Easing.InOutSine }
    }
    Timer {
        interval: 16; repeat: true; running: root.rotationRunning
        property double lastTick: 0
        onRunningChanged: lastTick = Date.now()
        onTriggered: {
            const now = Date.now()
            root.angle = (root.angle + 6 * root.rpm * Math.max(0, Math.min(250, now - lastTick)) / 1000) % 360
            lastTick = now
        }
    }
}
