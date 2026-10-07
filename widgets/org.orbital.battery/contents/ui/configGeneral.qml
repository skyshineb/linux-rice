// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: LGPL-2.0-or-later

import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kquickcontrols as KQC
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    id: root

    property alias cfg_alwaysShowPercent: alwaysPercent.checked
    property alias cfg_filledColor: filledColorButton.color
    property alias cfg_emptyColor: emptyColorButton.color
    property alias cfg_chargingColor: chargingColorButton.color
    property alias cfg_badgeBaseColor: badgeBaseColorButton.color
    property alias cfg_badgeTintColor: badgeTintColorButton.color
    property alias cfg_badgeTextColor: badgeTextColorButton.color

    function blend(first, second, amount) {
        return Qt.rgba(first.r + (second.r - first.r) * amount,
                       first.g + (second.g - first.g) * amount,
                       first.b + (second.b - first.b) * amount, 1)
    }

    Kirigami.FormLayout {
        QQC2.CheckBox {
            id: alwaysPercent
            text: i18n("Always show percentage")
        }

        KQC.ColorButton {
            id: filledColorButton
            Kirigami.FormData.label: i18n("Filled cells:")
            dialogTitle: i18n("Filled cell color")
            showAlphaChannel: true
        }

        KQC.ColorButton {
            id: emptyColorButton
            Kirigami.FormData.label: i18n("Empty cells:")
            dialogTitle: i18n("Empty cell color")
            showAlphaChannel: true
        }

        KQC.ColorButton {
            id: chargingColorButton
            Kirigami.FormData.label: i18n("Charging pulse:")
            dialogTitle: i18n("Charging pulse color")
            showAlphaChannel: true
        }

        KQC.ColorButton {
            id: badgeBaseColorButton
            Kirigami.FormData.label: i18n("Badge background:")
            dialogTitle: i18n("Badge background color")
            showAlphaChannel: true
        }

        KQC.ColorButton {
            id: badgeTintColorButton
            Kirigami.FormData.label: i18n("Badge tint:")
            dialogTitle: i18n("Badge tint color")
            showAlphaChannel: true
        }

        KQC.ColorButton {
            id: badgeTextColorButton
            Kirigami.FormData.label: i18n("Percentage text:")
            dialogTitle: i18n("Percentage text color")
            showAlphaChannel: true
        }

        QQC2.Button {
            text: i18n("Use current KDE theme colors")
            onClicked: {
                const background = Kirigami.Theme.backgroundColor
                const accent = Kirigami.Theme.linkColor
                const selection = Kirigami.Theme.highlightColor
                const textColor = Kirigami.Theme.textColor
                filledColorButton.color = accent
                emptyColorButton.color = root.blend(background, accent, 0.24)
                chargingColorButton.color = root.blend(accent, textColor, 0.4)
                badgeBaseColorButton.color = Qt.rgba(background.r, background.g, background.b, 0.69)
                badgeTintColorButton.color = Qt.rgba(selection.r, selection.g, selection.b, 0.41)
                badgeTextColorButton.color = textColor
            }
        }
    }
}
