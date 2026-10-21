// SPDX-License-Identifier: MIT
// The Battery components imported below retain LGPL-2.0-or-later licensing.
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import "../widgets/org.orbital.cpu/contents/ui" as CPU
import "../widgets/org.orbital.memory/contents/ui" as Memory
import "../widgets/org.orbital.battery/contents/ui" as Battery

Rectangle {
    id: root
    required property var colors
    required property var defaults
    color: colors.panel
    radius: 10
    Kirigami.Theme.inherit: false
    Kirigami.Theme.backgroundColor: colors.panel
    Kirigami.Theme.linkColor: colors.cyan
    Kirigami.Theme.textColor: colors.text
    Kirigami.Theme.highlightColor: colors.selected
    Kirigami.Theme.neutralTextColor: colors.amber
    CPU.Appearance { id: cpu; configuration: root.defaults.cpu; theme: root.Kirigami.Theme; migrate: false }
    Memory.Appearance { id: memory; configuration: root.defaults.memory; theme: root.Kirigami.Theme; migrate: false }
    Battery.Appearance { id: battery; configuration: root.defaults.battery; theme: root.Kirigami.Theme; migrate: false }

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 16
        Text { text: "ПАНЕЛЬ ORBITAL"; color: root.colors.muted; font.family: "IBM Plex Mono"; font.pixelSize: 12 }
        RowLayout {
            Layout.fillWidth: true; spacing: 12
            Repeater {
                model: 3
                ColumnLayout {
                    required property int index
                    Layout.fillWidth: true
                    CPU.CpuIndicator {
                        Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 100; Layout.preferredHeight: 64
                        orbitStyle: parent.index; cpuPercent: 50; animationsEnabled: false
                        filledColor: cpu.filledColor; emptyColor: cpu.emptyColor; trackColor: cpu.trackColor; textColor: cpu.textColor
                    }
                    Text { Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; text: ["Classic", "Constellation", "Pulsar"][parent.index]; color: root.colors.muted; font.pixelSize: 12 }
                }
            }
        }
        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: root.colors.button }
        RowLayout {
            Layout.fillWidth: true
            Repeater {
                model: 2
                ColumnLayout {
                    required property int index
                    Layout.fillWidth: true
                    Memory.MemoryVisual {
                        Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 62; Layout.preferredHeight: 62
                        meterStyle: parent.index; ramPercent: 67; swapPercent: 30
                        filledColor: memory.filledColor; emptyColor: memory.emptyColor; textColor: memory.textColor
                        chipBodyColor: memory.chipBodyColor; chipOutlineColor: memory.chipOutlineColor; swapColor: memory.swapColor
                    }
                    Text { Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; text: ["RAM / Fan", "RAM / Silicon"][parent.index]; color: root.colors.muted; font.pixelSize: 12 }
                }
            }
            Repeater {
                model: 2
                ColumnLayout {
                    required property int index
                    Layout.fillWidth: true
                    Battery.BatteryVisual {
                        Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 60; Layout.preferredHeight: 60
                        chargePercent: parent.index === 0 ? 65 : 15; alwaysShowPercent: true; animationsEnabled: false
                        filledColor: battery.filledColor; emptyColor: battery.emptyColor; chargingColor: battery.chargingColor
                        badgeBaseColor: battery.badgeBaseColor; badgeTintColor: battery.badgeTintColor; badgeTextColor: battery.badgeTextColor
                    }
                    Text { Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter; text: ["Заряд 65%", "Заряд 15%"][parent.index]; color: root.colors.muted; font.pixelSize: 12 }
                }
            }
        }
        Item { Layout.fillHeight: true }
        Text { text: "Демонстрационные значения · цвета следуют палитре"; color: root.colors.muted; font.pixelSize: 12; Layout.fillWidth: true; wrapMode: Text.WordWrap }
    }
}
