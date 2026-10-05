import QtQuick

Item {
    id: root
    readonly property real unit: Math.min(width, height) / 44
    property bool cpuReady: false
    property real orbitAngle: 0

    Item {
        width: 42 * root.unit
        height: 42 * root.unit
        anchors.centerIn: parent

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
            anchors.fill: parent
            rotation: root.orbitAngle

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
    }
}
