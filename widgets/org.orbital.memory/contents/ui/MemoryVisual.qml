import QtQuick

Item {
    id: root
    implicitWidth: 44
    implicitHeight: 44

    property real ramPercent: NaN
    property real swapPercent: NaN
    property bool showSwapGauge: true
    property color swapColor: "#E6B96A"
    // 0 = Fan, 1 = Silicon. Invalid saved values fall back to Fan.
    property int meterStyle: 0
    property color filledColor: "#70D4E8"
    property color emptyColor: "#315262"
    property color textColor: "#E9F6F8"
    property color chipBodyColor: "#183646"
    property color chipOutlineColor: "#799BA9"

    FanMemoryVisual {
        anchors.fill: parent
        ramPercent: root.ramPercent
        swapPercent: root.swapPercent
        showSwapGauge: root.showSwapGauge
        swapColor: root.swapColor
        filledColor: root.filledColor
        emptyColor: root.emptyColor
        textColor: root.textColor
        visible: root.meterStyle !== 1
    }

    SiliconMemoryVisual {
        anchors.fill: parent
        ramPercent: root.ramPercent
        filledColor: root.filledColor
        emptyColor: root.emptyColor
        textColor: root.textColor
        chipBodyColor: root.chipBodyColor
        chipOutlineColor: root.chipOutlineColor
        visible: root.meterStyle === 1
    }
}
