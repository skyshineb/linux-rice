/*
    SPDX-FileCopyrightText: 2012-2013 Daniel Nicoletti <dantti12@gmail.com>
    SPDX-FileCopyrightText: 2013, 2015 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
    Orbital adaptation; publication notice added 2026-10-07.
    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents3

PlasmaComponents3.ItemDelegate {
    id: root
    property real value: 0
    property alias maximumValue: slider.to
    property alias stepSize: slider.stepSize
    signal moved(real value)

    readonly property int percentage: maximumValue > 0
        ? Math.round(100 * slider.value / maximumValue) : 0

    background.visible: highlighted
    highlighted: activeFocus
    hoverEnabled: false
    Keys.forwardTo: [slider]

    contentItem: RowLayout {
        spacing: Kirigami.Units.gridUnit

        Kirigami.Icon {
            source: root.icon.name
            Layout.alignment: Qt.AlignTop
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    text: root.text
                    elide: Text.ElideRight
                }
                PlasmaComponents3.Label {
                    text: i18n("%1%", root.percentage)
                }
            }
            PlasmaComponents3.Slider {
                id: slider
                Layout.fillWidth: true
                activeFocusOnTab: false
                from: to > 100 ? 1 : 0
                stepSize: 1
                value: root.value
                Accessible.name: root.text
                Accessible.description: i18n("%1%", root.percentage)
                onPressedChanged: {
                    if (!pressed) {
                        value = Qt.binding(() => root.value);
                    }
                }
                onMoved: root.moved(value)
            }
        }
    }
}
