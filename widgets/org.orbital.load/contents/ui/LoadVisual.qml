import QtQuick 2.15

Item {
    id: root
    implicitWidth: 100
    implicitHeight: 44

    property real cpuPercent: NaN
    property real ramPercent: NaN
    property bool animationsEnabled: true
    readonly property bool cpuReady: isFinite(cpuPercent)
    readonly property bool ramReady: isFinite(ramPercent)
    readonly property int ramBlocks: ramReady ? Math.round(Math.max(0, Math.min(100, ramPercent)) / 10) : 0

    // The compact shape is drawn in QML so it stays sharp at either display scale.
    Item {
        id: cpuGauge
        width: 38
        height: 38
        x: 3
        anchors.verticalCenter: parent.verticalCenter

        Rectangle {
            anchors.centerIn: parent
            width: 32
            height: 32
            radius: 16
            color: "transparent"
            border.width: 1
            border.color: "#547C8C"
        }

        Item {
            id: orbit
            anchors.fill: parent
            Rectangle {
                width: 6
                height: 6
                radius: 3
                x: (parent.width - width) / 2
                y: 0
                color: root.cpuReady ? "#67C4DE" : "#547C8C"
                Rectangle {
                    width: 2
                    height: 2
                    radius: 1
                    x: 1
                    y: 1
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
            font.pixelSize: 10
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
        width: 43
        height: 42
        x: 50
        anchors.verticalCenter: parent.verticalCenter

        Text {
            id: ramLabel
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.ramReady ? Math.round(Math.max(0, Math.min(100, root.ramPercent))) + "%" : "—"
            color: root.ramReady ? "#E6B96A" : "#A5B5C4"
            font.family: "IBM Plex Mono"
            font.pixelSize: 10
            font.weight: Font.Medium
        }

        Rectangle {
            width: 34
            height: 29
            radius: 2
            anchors.top: ramLabel.bottom
            anchors.topMargin: 1
            anchors.horizontalCenter: parent.horizontalCenter
            color: "transparent"
            border.width: 1
            border.color: "#547C8C"

            Grid {
                anchors.centerIn: parent
                columns: 2
                rows: 5
                columnSpacing: 2
                rowSpacing: 1

                Repeater {
                    model: 10
                    Rectangle {
                        width: 13
                        height: 4
                        radius: 1
                        // Index 8 is bottom-left; index 9 is bottom-right.
                        readonly property int fillOrder: (4 - Math.floor(index / 2)) * 2 + (index % 2)
                        color: root.ramReady && fillOrder < root.ramBlocks ? "#E6B96A" : "#1C3144"
                        border.width: 1
                        border.color: root.ramReady && fillOrder < root.ramBlocks ? "#E6B96A" : "#547C8C"
                    }
                }
            }
        }
    }
}
