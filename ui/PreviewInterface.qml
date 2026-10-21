// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    required property var colors
    color: colors.canvas
    radius: 10
    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 18
        RowLayout {
            spacing: 8
            Repeater {
                model: [root.colors.red, root.colors.amber, root.colors.green]
                Rectangle { required property var modelData; width: 8; height: 8; radius: 4; color: modelData }
            }
            Text { text: "ORBITAL / ОБЗОР"; color: root.colors.muted; font.family: "IBM Plex Mono"; font.pixelSize: 12; Layout.leftMargin: 8 }
        }
        RowLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 18
            Rectangle {
                color: root.colors.panel; radius: 8
                Layout.preferredWidth: 140; Layout.fillHeight: true
                Column {
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 10 }
                    spacing: 6
                    Repeater {
                        model: ["Сводка", "События", "Настройки"]
                        Rectangle {
                            required property string modelData
                            required property int index
                            width: parent.width; height: 38; radius: 5
                            color: index === 0 ? root.colors.selected : "transparent"
                            Text { anchors.centerIn: parent; text: parent.modelData; color: parent.index === 0 ? root.colors.text : root.colors.muted }
                        }
                    }
                }
            }
            Rectangle {
                color: root.colors.window; radius: 8
                Layout.fillWidth: true; Layout.fillHeight: true
                ColumnLayout {
                    anchors { fill: parent; margins: 18 }
                    spacing: 12
                    Text { text: "Всё под контролем"; color: root.colors.text; font.pixelSize: 22; font.weight: Font.Medium; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                    Text { text: "Основной текст на поверхности окна.\nВторичные детали помогают сохранить иерархию."; color: root.colors.muted; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    Rectangle {
                        color: root.colors.button; radius: 6; Layout.fillWidth: true; implicitHeight: 42
                        Text { anchors.centerIn: parent; text: "Продолжить"; color: root.colors.text }
                    }
                    Text { text: "Открыть подробности →"; color: root.colors.cyan }
                    Item { Layout.fillHeight: true }
                    Flow {
                        Layout.fillWidth: true; spacing: 10
                        Repeater {
                            model: [{text: "Готово", color: root.colors.green}, {text: "Внимание", color: root.colors.amber}, {text: "Ошибка", color: root.colors.red}]
                            Text { required property var modelData; text: "● " + modelData.text; color: modelData.color; font.pixelSize: 12 }
                        }
                    }
                }
            }
        }
    }
}
