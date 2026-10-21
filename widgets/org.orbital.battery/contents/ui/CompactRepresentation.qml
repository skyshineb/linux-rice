/*
    SPDX-FileCopyrightText: 2011 Sebastian Kügler <sebas@kde.org>
    SPDX-FileCopyrightText: 2011 Viranch Mehta <viranch.mehta@gmail.com>
    SPDX-FileCopyrightText: 2013 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
    Orbital adaptation; publication notice added 2026-10-07.
    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasmoid

MouseArea {
    id: root

    Appearance {
        id: appearance
        configuration: Plasmoid.configuration
        theme: root.Kirigami.Theme
    }

    required property var appletItem
    required property real chargePercent
    required property bool charging
    property bool wasExpanded: false

    readonly property real padding: Math.max(4, Math.round(height * 0.08))
    readonly property real visualHeight: height > 0
        ? Math.max(24, height - 2 * padding) : 44
    readonly property real slotWidth: visualHeight * 50 / 44

    Layout.minimumWidth: slotWidth
    Layout.preferredWidth: slotWidth
    Layout.maximumWidth: slotWidth
    Layout.minimumHeight: 40
    Layout.fillHeight: true

    activeFocusOnTab: true
    hoverEnabled: true
    cursorShape: Qt.PointingHandCursor
    Accessible.name: Plasmoid.title
    Accessible.description: root.appletItem.toolTipMainText + "; "
        + root.appletItem.toolTipSubText
    Accessible.role: Accessible.Button

    onPressed: wasExpanded = root.appletItem.expanded
    onClicked: root.appletItem.expanded = !wasExpanded

    BatteryVisual {
        anchors.centerIn: parent
        width: root.visualHeight
        height: root.visualHeight
        chargePercent: root.chargePercent
        charging: root.charging
        hovered: root.containsMouse
        popupOpen: root.appletItem.expanded
        alwaysShowPercent: Plasmoid.configuration.alwaysShowPercent
        animationsEnabled: Kirigami.Units.longDuration > 0
        filledColor: appearance.filledColor
        emptyColor: appearance.emptyColor
        chargingColor: appearance.chargingColor
        badgeBaseColor: appearance.badgeBaseColor
        badgeTintColor: appearance.badgeTintColor
        badgeTextColor: appearance.badgeTextColor
    }
}
