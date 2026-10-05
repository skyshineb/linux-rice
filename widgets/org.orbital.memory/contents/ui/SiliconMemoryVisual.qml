import QtQuick

Item {
    id: root
    implicitWidth: 44
    implicitHeight: 44

    property real ramPercent: NaN
    property color filledColor: "#70D4E8"
    property color emptyColor: "#315262"
    property color textColor: "#E9F6F8"
    property color chipBodyColor: "#183646"
    property color chipOutlineColor: "#799BA9"
    readonly property real unit: Math.min(width, height) / 36
    readonly property bool ramReady: isFinite(ramPercent)
    readonly property real clampedPercent: ramReady ? Math.max(0, Math.min(100, ramPercent)) : 0
    readonly property int displayPercent: Math.round(clampedPercent)
    readonly property int filledBanks: ramReady ? Math.round(clampedPercent * 8 / 100) : 0

    Item {
        id: chip
        width: 44 * root.unit
        height: width
        anchors.centerIn: parent

        Repeater {
            model: 8
            Rectangle {
                x: (index < 4 ? 7 : 33.5) * root.unit
                y: (14 + index % 4 * 4.7) * root.unit
                width: 3.5 * root.unit
                height: 1.8 * root.unit
                radius: 0.5 * root.unit
                color: root.chipOutlineColor
            }
        }

        Rectangle {
            x: 10 * root.unit
            y: 10 * root.unit
            width: 24 * root.unit
            height: width
            radius: 3.3 * root.unit
            color: root.chipBodyColor
            border.color: root.chipOutlineColor
            border.width: Math.max(1, root.unit)

            Rectangle {
                anchors.fill: parent
                anchors.margins: 2 * root.unit
                radius: 2 * root.unit
                color: "transparent"
                border.color: root.emptyColor
                border.width: Math.max(1, root.unit * 0.7)
            }
        }

        Repeater {
            model: 8
            Rectangle {
                x: (13.5 + index % 4 * 4.45) * root.unit
                y: (14.2 + Math.floor(index / 4) * 5.1) * root.unit
                width: 3.1 * root.unit
                height: 3.3 * root.unit
                radius: 0.6 * root.unit
                color: root.ramReady && index < root.filledBanks ? root.filledColor : root.emptyColor
                Behavior on color { ColorAnimation { duration: 160 } }
            }
        }

        Text {
            x: 11 * root.unit
            y: 24.7 * root.unit
            width: 22 * root.unit
            height: 8.5 * root.unit
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            text: root.ramReady ? root.displayPercent + "%" : "—"
            color: root.ramReady ? root.textColor : root.emptyColor
            font.family: "IBM Plex Mono"
            font.pixelSize: Math.max(7, Math.round(8 * root.unit))
            font.weight: Font.DemiBold
            minimumPixelSize: 7
            fontSizeMode: Text.Fit
        }
    }
}
