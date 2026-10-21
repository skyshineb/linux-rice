// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    required property var terminal
    color: terminal.Background
    radius: 10
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 22; spacing: 14
        Text { text: "KONSOLE / ANSI"; color: root.terminal.ForegroundFaint; font.family: "IBM Plex Mono"; font.pixelSize: 12 }
        Row {
            Text { text: "orbital"; color: root.terminal.Color2; font.family: "IBM Plex Mono" }
            Text { text: "  ~/projects  "; color: root.terminal.Color4; font.family: "IBM Plex Mono" }
            Text { text: "❯ git status"; color: root.terminal.Foreground; font.family: "IBM Plex Mono" }
        }
        Text { text: "On branch main\nYour branch is up to date.\n\nChanges to be committed:"; color: root.terminal.Foreground; font.family: "IBM Plex Mono"; lineHeight: 1.4 }
        Text { text: "  new file:   orbital.colorscheme"; color: root.terminal.Color2; font.family: "IBM Plex Mono"; Layout.fillWidth: true; elide: Text.ElideRight }
        Text { text: "  modified:   theme.json"; color: root.terminal.Color3; font.family: "IBM Plex Mono" }
        Text { text: "  deleted:    obsolete.conf"; color: root.terminal.Color1; font.family: "IBM Plex Mono" }
        Item { Layout.fillHeight: true }
        Text { text: "Обычные и яркие ANSI-цвета"; color: root.terminal.ForegroundFaint; font.pixelSize: 12 }
        GridLayout {
            columns: 8; columnSpacing: 6; rowSpacing: 6; Layout.fillWidth: true
            Repeater {
                model: 16
                Rectangle {
                    required property int index
                    Layout.fillWidth: true; Layout.minimumWidth: 22; implicitHeight: 30; radius: 3
                    color: root.terminal["Color" + (index % 8) + (index >= 8 ? "Intense" : "")]
                }
            }
        }
    }
}
