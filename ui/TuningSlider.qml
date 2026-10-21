// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    required property string label
    required property real value
    signal edited(real newValue)
    spacing: 2
    RowLayout {
        Layout.fillWidth: true
        Label { text: root.label; Layout.fillWidth: true }
        Label { text: root.value.toFixed(2); font.family: "IBM Plex Mono" }
        ToolButton { text: "↺"; Accessible.name: "Сбросить " + root.label; onClicked: root.edited(0) }
    }
    Slider {
        Layout.fillWidth: true
        from: -1; to: 1; stepSize: 0.05
        snapMode: Slider.SnapAlways
        value: root.value
        Accessible.name: root.label
        onMoved: root.edited(value)
    }
}
