/*
    SPDX-FileCopyrightText: 2013 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
    Orbital adaptation; publication notice added 2026-10-07.
    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents3

RowLayout {
    id: root
    property string iconSource: "dialog-information"
    property string text: ""
    spacing: Kirigami.Units.smallSpacing

    Kirigami.Icon {
        source: root.iconSource
        Layout.preferredWidth: Kirigami.Units.iconSizes.small
        Layout.preferredHeight: Kirigami.Units.iconSizes.small
    }
    PlasmaComponents3.Label {
        Layout.fillWidth: true
        text: root.text
        wrapMode: Text.WordWrap
    }
}
