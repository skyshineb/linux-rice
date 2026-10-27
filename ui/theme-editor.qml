// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1120; height: 800
    minimumWidth: 900; minimumHeight: 640
    visible: true
    title: "Палитра Orbital"
    font.family: "IBM Plex Sans"
    onClosing: function(close) { close.accepted = editor.requestClose() }

    ColumnLayout {
        anchors.fill: parent; anchors.margins: 20; spacing: 14
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                spacing: 2
                Label { text: "Палитра Orbital"; font.pixelSize: 24; font.weight: Font.DemiBold }
                Label { text: "Настройте цвета и оцените результат перед применением"; opacity: 0.65 }
            }
            Item { Layout.fillWidth: true }
            BusyIndicator { running: editor.calculating || editor.working; visible: running; Layout.preferredWidth: 32; Layout.preferredHeight: 32 }
        }
        RowLayout {
            Layout.fillWidth: true; Layout.fillHeight: true; spacing: 20
            ScrollView {
                id: settingsScroll
                Layout.preferredWidth: 292; Layout.fillHeight: true
                contentWidth: availableWidth; clip: true
                enabled: !editor.working
                ColumnLayout {
                    width: settingsScroll.availableWidth; spacing: 12
                    Label { text: "ИСТОЧНИК"; font.pixelSize: 11; opacity: 0.6 }
                    ComboBox {
                        Layout.fillWidth: true; model: ["Изображение", "HEX-цвет"]
                        currentIndex: editor.settings.source_kind === "image" ? 0 : 1
                        onActivated: editor.setOption("source_kind", currentIndex === 0 ? "image" : "color")
                        Accessible.name: "Тип источника"
                    }
                    ColumnLayout {
                        visible: editor.settings.source_kind === "image"
                        Layout.fillWidth: true
                        Button { text: "Выбрать изображение…"; Layout.fillWidth: true; onClicked: editor.chooseImage() }
                        TextField {
                            Layout.fillWidth: true; placeholderText: "Путь к изображению"; text: editor.settings.image
                            Accessible.name: "Путь к изображению"
                            onEditingFinished: editor.setOption("image", text)
                        }
                    }
                    RowLayout {
                        visible: editor.settings.source_kind === "color"; Layout.fillWidth: true
                        TextField {
                            Layout.fillWidth: true; text: editor.settings.color; placeholderText: "#RRGGBB"
                            maximumLength: 7; font.family: "IBM Plex Mono"; Accessible.name: "HEX-цвет"
                            onTextEdited: editor.setOption("color", text)
                        }
                        Button { text: "Цвет…"; onClicked: editor.chooseColor() }
                    }
                    Label { text: "РЕЖИМ И ПАЛИТРА"; font.pixelSize: 11; opacity: 0.6; Layout.topMargin: 8 }
                    ComboBox {
                        Layout.fillWidth: true; model: ["Тёмная", "Светлая"]
                        currentIndex: editor.settings.mode === "dark" ? 0 : 1
                        Accessible.name: "Режим темы"
                        onActivated: editor.setOption("mode", currentIndex === 0 ? "dark" : "light")
                    }
                    ComboBox {
                        Layout.fillWidth: true
                        model: editor.schemeTypes.map(function(value) { return value.replace("scheme-", "").replace(/-/g, " ") })
                        currentIndex: editor.schemeTypes.indexOf(editor.settings.scheme_type)
                        Accessible.name: "Тип палитры Matugen"
                        onActivated: editor.setOption("scheme_type", editor.schemeTypes[currentIndex])
                    }
                    TuningSlider { label: "Контраст"; value: editor.settings.contrast; Layout.fillWidth: true; onEdited: function(value) { editor.setOption("contrast", value) } }
                    ColumnLayout {
                        visible: editor.settings.source_kind === "image"; Layout.fillWidth: true; spacing: 8
                        Label { text: "ИСХОДНЫЙ ЦВЕТ"; font.pixelSize: 11; opacity: 0.6 }
                        ComboBox {
                            id: sourceChoice
                            Layout.fillWidth: true
                            property var choices: ["index", "saturation", "lightness", "darkness"]
                            model: ["Выбрать из изображения", "Предпочесть насыщенный", "Предпочесть светлый", "Предпочесть тёмный"]
                            currentIndex: choices.indexOf(editor.settings.source_choice)
                            Accessible.name: "Выбор исходного цвета"
                            onActivated: editor.setOption("source_choice", choices[currentIndex])
                        }
                        Row {
                            spacing: 8
                            Repeater {
                                model: editor.sourceColors
                                Button {
                                    required property string modelData
                                    required property int index
                                    width: 42; height: 36
                                    Accessible.name: "Исходный цвет " + modelData
                                    ToolTip.visible: hovered; ToolTip.text: modelData
                                    background: Rectangle {
                                        color: parent.modelData; radius: 5
                                        border.width: editor.settings.source_choice === "index" && editor.settings.source_color_index === parent.index ? 3 : 1
                                        border.color: editor.settings.mode === "dark" ? "#ffffff" : "#172D3D"
                                    }
                                    onClicked: { editor.setOption("source_choice", "index"); editor.setOption("source_color_index", index) }
                                }
                            }
                        }
                    }
                    ToolButton { id: advanced; text: checked ? "▾ Дополнительные настройки" : "▸ Дополнительные настройки"; checkable: true; Layout.fillWidth: true }
                    ColumnLayout {
                        visible: advanced.checked; Layout.fillWidth: true
                        TuningSlider { label: "Светлота тёмной темы"; value: editor.settings.lightness_dark; Layout.fillWidth: true; onEdited: function(value) { editor.setOption("lightness_dark", value) } }
                        TuningSlider { label: "Светлота светлой темы"; value: editor.settings.lightness_light; Layout.fillWidth: true; onEdited: function(value) { editor.setOption("lightness_light", value) } }
                    }
                }
            }
            ColumnLayout {
                Layout.fillWidth: true; Layout.fillHeight: true; spacing: 10
                TabBar {
                    id: tabs
                    objectName: "previewTabs"
                    Layout.fillWidth: true
                    TabButton { text: "Интерфейс" }
                    TabButton { text: "Виджеты" }
                    TabButton { text: "Терминал" }
                }
                StackLayout {
                    Layout.fillWidth: true; Layout.fillHeight: true; currentIndex: tabs.currentIndex
                    ScrollView {
                        id: interfaceScroll; contentWidth: availableWidth; clip: true
                        PreviewInterface { width: interfaceScroll.availableWidth; height: Math.max(340, interfaceScroll.availableHeight); colors: editor.preview.colors }
                    }
                    ScrollView {
                        id: widgetsScroll; contentWidth: availableWidth; clip: true
                        PreviewWidgets { width: widgetsScroll.availableWidth; height: Math.max(implicitHeight, widgetsScroll.availableHeight); colors: editor.preview.colors; defaults: editor.widgetDefaults }
                    }
                    ScrollView {
                        id: terminalScroll; contentWidth: availableWidth; clip: true
                        PreviewTerminal { width: terminalScroll.availableWidth; height: Math.max(360, terminalScroll.availableHeight); terminal: editor.preview.terminal }
                    }
                }
                RowLayout {
                    Layout.fillWidth: true; spacing: 12
                    ColumnLayout {
                        visible: editor.settings.source_kind === "image" && editor.settings.image.trim().length > 0
                        Layout.minimumWidth: 144; Layout.preferredWidth: 144; Layout.maximumWidth: 144
                        Layout.alignment: Qt.AlignVCenter
                        spacing: 4
                        Rectangle {
                            Layout.fillWidth: true; implicitHeight: 108
                            color: root.palette.base; border.color: root.palette.mid; radius: 4
                            Image {
                                id: sourceThumbnail
                                objectName: "sourceThumbnail"
                                anchors.fill: parent; anchors.margins: 1
                                source: editor.sourceImageUrl
                                sourceSize.width: 288; sourceSize.height: 216
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true; autoTransform: true; smooth: true
                                visible: status === Image.Ready
                                Accessible.name: "Исходное изображение"
                            }
                            BusyIndicator {
                                anchors.centerIn: parent; width: 28; height: 28
                                running: sourceThumbnail.status === Image.Loading
                                visible: running
                            }
                            Label {
                                anchors.fill: parent; anchors.margins: 8
                                text: "Изображение недоступно"
                                wrapMode: Text.WordWrap
                                horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
                                visible: sourceThumbnail.status === Image.Error || sourceThumbnail.status === Image.Null
                            }
                        }
                        Label { text: "Исходное изображение"; font.pixelSize: 10; Layout.alignment: Qt.AlignHCenter }
                    }
                    GridLayout {
                        columns: 6; columnSpacing: 8; rowSpacing: 8; Layout.fillWidth: true
                        Repeater {
                            model: editor.swatches
                            Button {
                                required property var modelData
                                Layout.fillWidth: true; Layout.preferredHeight: 66
                                flat: true; padding: 4
                                Accessible.name: modelData.label + " " + modelData.color
                                ToolTip.visible: hovered; ToolTip.text: "Скопировать " + modelData.role + ": " + modelData.color
                                contentItem: Column {
                                    spacing: 3
                                    Rectangle { width: parent.width; height: 20; radius: 3; color: modelData.color; border.color: "#40808080" }
                                    Text { width: parent.width; text: modelData.label; font.pixelSize: 10; color: root.palette.text; elide: Text.ElideRight; horizontalAlignment: Text.AlignHCenter }
                                    Text { width: parent.width; text: modelData.color; font.family: "IBM Plex Mono"; font.pixelSize: 10; color: root.palette.text; horizontalAlignment: Text.AlignHCenter }
                                }
                                onClicked: editor.copyColor(modelData.color)
                            }
                        }
                    }
                }
            }
        }
        Label {
            Layout.fillWidth: true
            text: editor.error ? editor.status + ": " + editor.error : editor.status
            color: root.palette.text
            font.weight: editor.error ? Font.DemiBold : Font.Normal
            wrapMode: Text.WrapAnywhere; maximumLineCount: 4; elide: Text.ElideRight
            Accessible.role: Accessible.StaticText
        }
        RowLayout {
            Layout.fillWidth: true
            CheckBox {
                id: wallpaper
                text: "Использовать изображение как обои"
                checked: false
                enabled: editor.settings.source_kind === "image" && !editor.working
            }
            Item { Layout.fillWidth: true }
            Button { text: "Отменить применение"; enabled: editor.canUndo; onClicked: editor.undo() }
            Button { text: "Применить"; highlighted: true; enabled: editor.canApply; onClicked: editor.applyTheme(wallpaper.checked) }
        }
    }
}
