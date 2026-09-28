import QtQuick 2.15

Item {
    id: root
    implicitWidth: 44
    implicitHeight: 44
    readonly property real unit: height / 44

    property real ramPercent: NaN
    readonly property bool ramReady: isFinite(ramPercent)
    readonly property int ramBlocks: ramReady ? Math.round(Math.max(0, Math.min(100, ramPercent)) / 10) : 0

    Item {
        id: ramGauge
        width: 43 * root.unit
        height: 42 * root.unit
        x: 0.5 * root.unit
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
