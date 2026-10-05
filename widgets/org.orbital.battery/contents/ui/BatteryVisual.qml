import QtQuick
import Qt5Compat.GraphicalEffects

Item {
    id: root
    implicitWidth: 44
    implicitHeight: 44
    readonly property real unit: height / 44

    property real chargePercent: NaN
    property bool charging: false
    property bool hovered: false
    property bool popupOpen: false
    property bool alwaysShowPercent: false
    property bool animationsEnabled: true
    property color filledColor: "#67C4DE"
    property color emptyColor: "#294357"
    property color chargingColor: "#91E4F7"
    property color badgeBaseColor: "#B0102B3B"
    property color badgeTintColor: "#681B5571"
    property color badgeTextColor: "#F2FAFD"
    readonly property bool chargeReady: isFinite(chargePercent)
    readonly property real charge: chargeReady ? Math.max(0, Math.min(100, chargePercent)) : 0
    readonly property int displayPercent: Math.round(charge)
    readonly property int solidCells: chargeReady ? (displayPercent >= 99 ? 20 : Math.floor(charge / 5)) : 0
    readonly property int nextCell: chargeReady && charging && displayPercent < 99 && solidCells < 20 ? solidCells : -1
    readonly property bool lowCharge: chargeReady && charge <= 20
    readonly property bool percentVisible: hovered || popupOpen || alwaysShowPercent || lowCharge

    Grid {
        id: batteryGrid
        anchors.centerIn: parent
        width: 30 * root.unit
        height: 38 * root.unit
        columns: 4
        rows: 5
        columnSpacing: 2 * root.unit
        rowSpacing: 2 * root.unit

        Repeater {
            model: 20
            Rectangle {
                width: 6 * root.unit
                height: width
                radius: root.unit
                // Fill each row left to right, starting with the bottom row.
                readonly property int fillOrder: (4 - Math.floor(index / 4)) * 4 + index % 4
                color: fillOrder < root.solidCells ? root.filledColor : root.emptyColor

                Behavior on color { ColorAnimation { duration: root.animationsEnabled ? 160 : 0 } }

                Rectangle {
                    id: chargingCell
                    anchors.fill: parent
                    radius: parent.radius
                    color: root.chargingColor
                    visible: parent.fillOrder === root.nextCell
                    opacity: root.animationsEnabled ? pulseStrength : 0.75
                    property real pulseStrength: 0.18

                    SequentialAnimation on pulseStrength {
                        running: chargingCell.visible && root.animationsEnabled
                        loops: Animation.Infinite
                        NumberAnimation { from: 0.18; to: 1; duration: 900; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 1; to: 0.18; duration: 900; easing.type: Easing.InOutSine }
                    }
                }
            }
        }
    }

    Item {
        id: percentBadge
        anchors.centerIn: batteryGrid
        width: percentText.implicitWidth + 4 * root.unit
        height: percentText.implicitHeight + 1.5 * root.unit
        opacity: root.percentVisible ? 1 : 0
        visible: opacity > 0

        Behavior on opacity { NumberAnimation { duration: root.animationsEnabled ? 160 : 0 } }
        Behavior on width { NumberAnimation { duration: root.animationsEnabled ? 120 : 0 } }

        Rectangle {
            anchors.fill: parent
            color: root.badgeBaseColor
        }

        ShaderEffectSource {
            id: gridCapture
            anchors.fill: parent
            sourceItem: batteryGrid
            sourceRect: Qt.rect((batteryGrid.width - percentBadge.width) / 2,
                                (batteryGrid.height - percentBadge.height) / 2,
                                percentBadge.width, percentBadge.height)
            visible: false
        }

        FastBlur {
            anchors.fill: parent
            source: gridCapture
            radius: 3 * root.unit
            cached: false
            visible: GraphicsInfo.api !== GraphicsInfo.Software
            opacity: 0.75
        }

        Rectangle {
            anchors.fill: parent
            color: root.badgeTintColor
        }

        Text {
            id: percentText
            anchors.centerIn: parent
            text: root.chargeReady ? root.displayPercent + "%" : "—"
            color: root.badgeTextColor
            font.family: "IBM Plex Mono"
            font.pixelSize: Math.max(8, Math.round(11 * root.unit))
            font.weight: Font.DemiBold
        }
    }
}
