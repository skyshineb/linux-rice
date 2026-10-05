/*
    SPDX-FileCopyrightText: 2012-2013 Daniel Nicoletti <dantti12@gmail.com>
    SPDX-FileCopyrightText: 2013, 2015 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents3

ColumnLayout {
    id: root
    required property var control
    spacing: Kirigami.Units.smallSpacing

    PlasmaComponents3.CheckBox {
        id: manualSwitch
        Layout.fillWidth: true
        text: i18n("Manually block sleep and screen locking")
        onClicked: {
            if (checked) {
                root.control.inhibit(
                    i18n("The battery applet has enabled suppressing sleep and screen locking"));
            } else {
                root.control.uninhibit();
            }
        }
        Binding {
            target: manualSwitch
            property: "checked"
            value: root.control.isManuallyInhibited
        }
    }

    InhibitionHint {
        Layout.fillWidth: true
        visible: root.control.isManuallyInhibitedError
        iconSource: "dialog-error"
        text: i18n("Could not change sleep and screen locking inhibition.")
    }

    InhibitionHint {
        Layout.fillWidth: true
        visible: root.control.isLidPresent && !root.control.triggersLidAction
        iconSource: "computer-laptop"
        text: i18n("Closing the lid will not put this computer to sleep.")
    }

    PlasmaComponents3.Label {
        Layout.fillWidth: true
        visible: root.control.hasInhibition && !root.control.isManuallyInhibited
        text: i18n("Applications blocking sleep or screen locking:")
        wrapMode: Text.WordWrap
    }

    Repeater {
        model: root.control.requestedInhibitions
        delegate: InhibitionHint {
            Layout.fillWidth: true
            visible: modelData.active && !root.control.isManuallyInhibited
            iconSource: modelData.icon || "dialog-information"
            text: modelData.reason
                ? i18n("%1: %2", modelData.prettyName || modelData.appName,
                       modelData.reason)
                : (modelData.prettyName || modelData.appName)
        }
    }
}
