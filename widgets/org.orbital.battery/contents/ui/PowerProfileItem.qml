/*
    SPDX-FileCopyrightText: 2021 Kai Uwe Broulik <kde@broulik.de>
    SPDX-FileCopyrightText: 2021 David Redondo <kde@david-redondo.de>
    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents3

ColumnLayout {
    id: root
    required property var control

    function labelFor(profile) {
        switch (profile) {
        case "power-saver": return i18n("Power Save");
        case "balanced": return i18n("Balanced");
        case "performance": return i18n("Performance");
        default: return profile;
        }
    }

    readonly property var options: control.profiles.map(profile => ({
        "text": labelFor(profile), "value": profile
    }))

    visible: control.isPowerProfileDaemonInstalled && options.length > 0
    spacing: Kirigami.Units.smallSpacing

    PlasmaComponents3.Label {
        Layout.fillWidth: true
        text: i18n("Power Profile")
    }
    PlasmaComponents3.ComboBox {
        Layout.fillWidth: true
        model: root.options
        textRole: "text"
        valueRole: "value"
        currentIndex: root.options.findIndex(
            option => option.value === root.control.activeProfile)
        onActivated: index => root.control.setProfile(root.options[index].value)
    }
    InhibitionHint {
        Layout.fillWidth: true
        visible: root.control.profileError.length > 0
        iconSource: "dialog-error"
        text: root.control.profileError
    }
    InhibitionHint {
        Layout.fillWidth: true
        visible: root.control.inhibitionReason.length > 0
        iconSource: "dialog-information"
        text: i18n("Performance mode is unavailable: %1",
                   root.control.inhibitionReason)
    }
    InhibitionHint {
        Layout.fillWidth: true
        visible: root.control.degradationReason.length > 0
        iconSource: "dialog-information"
        text: i18n("Performance may be reduced: %1",
                   root.control.degradationReason)
    }
    Repeater {
        model: root.control.profileHolds
        delegate: InhibitionHint {
            Layout.fillWidth: true
            iconSource: modelData.Icon || "dialog-information"
            text: modelData.Reason
                ? i18n("%1 requested %2: %3", modelData.Name,
                       root.labelFor(modelData.Profile), modelData.Reason)
                : i18n("%1 requested %2", modelData.Name,
                       root.labelFor(modelData.Profile))
        }
    }
}
