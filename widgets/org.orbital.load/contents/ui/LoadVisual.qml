import QtQuick 2.15

Item {
    id: root
    implicitWidth: 100
    implicitHeight: 44
    readonly property real unit: height / 44

    property real cpuPercent: NaN
    property real ramPercent: NaN
    property bool animationsEnabled: true
    readonly property bool cpuReady: isFinite(cpuPercent)
    readonly property bool ramReady: isFinite(ramPercent)
    readonly property int ramBlocks: ramReady ? Math.round(Math.max(0, Math.min(100, ramPercent)) / 10) : 0

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
        interval: 50
        repeat: true
        running: root.visible && root.cpuReady && root.animationsEnabled
        property double lastTick: 0
        onRunningChanged: lastTick = Date.now()
        onTriggered: {
            var now = Date.now()
            var elapsed = Math.max(0, Math.min(250, now - lastTick))
            lastTick = now
            var usage = Math.max(0, Math.min(100, root.cpuPercent))
            var period = 16000 - 140 * usage
            orbit.rotation = (orbit.rotation + 360 * elapsed / period) % 360
        }
    }

    Item {
        id: ramGauge
        width: 43 * root.unit
        height: 42 * root.unit
        x: 50 * root.unit
        anchors.verticalCenter: parent.verticalCenter

        Text {
            id: ramLabel
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            height: 12 * root.unit
            verticalAlignment: Text.AlignVCenter
            text: root.ramReady ? Math.round(Math.max(0, Math.min(100, root.ramPercent))) + "%" : "—"
            color: root.ramReady ? "#E6B96A" : "#A5B5C4"
            font.family: "IBM Plex Mono"
            font.pixelSize: Math.max(7, Math.round(10 * root.unit))
            font.weight: Font.Medium
        }

        Rectangle {
            width: 34 * root.unit
            height: 29 * root.unit
            radius: 2 * root.unit
            anchors.top: ramLabel.bottom
            anchors.topMargin: root.unit
            anchors.horizontalCenter: parent.horizontalCenter
            color: "transparent"
            border.width: Math.max(1, Math.round(root.unit))
            border.color: "#547C8C"

            Grid {
                anchors.centerIn: parent
                columns: 2
                rows: 5
                columnSpacing: 2 * root.unit
                rowSpacing: root.unit

                Repeater {
                    model: 10
                    Rectangle {
                        width: 13 * root.unit
                        height: 4 * root.unit
                        radius: root.unit
                        // Index 8 is bottom-left; index 9 is bottom-right.
                        readonly property int fillOrder: (4 - Math.floor(index / 2)) * 2 + (index % 2)
                        color: root.ramReady && fillOrder < root.ramBlocks ? "#E6B96A" : "#1C3144"
                        border.width: Math.max(1, Math.round(root.unit))
                        border.color: root.ramReady && fillOrder < root.ramBlocks ? "#E6B96A" : "#547C8C"
                    }
                }
            }
        }
    }
}
