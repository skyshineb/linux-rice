import QtQuick 2.15

Item {
    id: root
    implicitWidth: 44
    implicitHeight: 44
    readonly property real unit: height / 44

    property real cpuPercent: NaN
    property real maxRpm: 30
    property bool animationsEnabled: true
    readonly property bool cpuReady: isFinite(cpuPercent)
    readonly property real orbitRpm: cpuReady && isFinite(maxRpm)
        ? Math.max(0, Math.min(120, maxRpm)) * Math.max(0, Math.min(100, cpuPercent)) / 100
        : 0

    // Scale geometry and fonts from the available height, avoiding a stretched texture.
    Item {
        id: cpuGauge
        width: 42 * root.unit
        height: 42 * root.unit
        x: root.unit
        anchors.verticalCenter: parent.verticalCenter

        Rectangle {
            anchors.centerIn: parent
            width: 36 * root.unit
            height: 36 * root.unit
            radius: 18 * root.unit
            color: "transparent"
            border.width: Math.max(1, Math.round(root.unit))
            border.color: "#547C8C"
        }

        Item {
            id: orbit
            anchors.fill: parent
            Rectangle {
                width: 6 * root.unit
                height: 6 * root.unit
                radius: 3 * root.unit
                x: (parent.width - width) / 2
                y: 0
                color: root.cpuReady ? "#67C4DE" : "#547C8C"
                Rectangle {
                    width: 2 * root.unit
                    height: 2 * root.unit
                    radius: root.unit
                    x: root.unit
                    y: root.unit
                    color: "#E7EEF2"
                    opacity: 0.8
                }
            }
        }

        Text {
            anchors.centerIn: parent
            text: root.cpuReady ? Math.round(Math.max(0, Math.min(100, root.cpuPercent))) + "%" : "—"
            color: "#E7EEF2"
            font.family: "IBM Plex Mono"
            font.pixelSize: Math.max(8, Math.round(11 * root.unit))
            font.weight: Font.Medium
        }
    }

    Timer {
        id: orbitTimer
        interval: 16
        repeat: true
        running: root.visible && root.animationsEnabled && root.orbitRpm > 0
        property double lastTick: 0
        onRunningChanged: lastTick = Date.now()
        onTriggered: {
            var now = Date.now()
            var elapsed = Math.max(0, Math.min(250, now - lastTick))
            lastTick = now
            orbit.rotation = (orbit.rotation + 6 * root.orbitRpm * elapsed / 1000) % 360
        }
    }
}
