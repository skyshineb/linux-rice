// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kquickcontrols as KQC
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    id: root

    property int cfg_colorMode: -1

    readonly property bool legacyCustomColors: {
        if (!Qt.colorEqual(root.cfg_filledColor, "#70D4E8")) return true
        if (!Qt.colorEqual(root.cfg_emptyColor, "#315262")) return true
        if (!Qt.colorEqual(root.cfg_textColor, "#E9F6F8")) return true
        if (!Qt.colorEqual(root.cfg_chipBodyColor, "#183646")) return true
        if (!Qt.colorEqual(root.cfg_chipOutlineColor, "#799BA9")) return true
        if (!Qt.colorEqual(root.cfg_swapColor, "#E6B96A")) return true
        return false
    }


    property alias cfg_meterStyle: styleCombo.currentIndex
    property alias cfg_meterScale: sizeSpin.value
    property alias cfg_showSwapGauge: showSwapCheck.checked
    property alias cfg_swapColor: swapColorButton.color
    property alias cfg_filledColor: filledColorButton.color
    property alias cfg_emptyColor: emptyColorButton.color
    property alias cfg_textColor: textColorButton.color
    property alias cfg_chipBodyColor: chipBodyColorButton.color
    property alias cfg_chipOutlineColor: chipOutlineColorButton.color

    function blend(first, second, amount) {
        return Qt.rgba(first.r + (second.r - first.r) * amount,
                       first.g + (second.g - first.g) * amount,
                       first.b + (second.b - first.b) * amount, 1)
    }

    Kirigami.FormLayout {
        QQC2.ComboBox {
            id: colorModeCombo
            Kirigami.FormData.label: i18n("Color source:")
            model: [i18n("KDE theme"), i18n("Custom colors")]
            currentIndex: root.cfg_colorMode < 0 ? (root.legacyCustomColors ? 1 : 0) : root.cfg_colorMode
            onActivated: root.cfg_colorMode = currentIndex
        }

        QQC2.ComboBox {
            id: styleCombo
            Kirigami.FormData.label: i18n("Meter style:")
            model: [i18n("Fan"), i18n("Silicon")]
        }

        QQC2.SpinBox {
            id: sizeSpin
            Kirigami.FormData.label: i18n("Relative size:")
            from: 60
            to: 110
            stepSize: 5
            editable: false
            textFromValue: function(value) { return value + "%" }
        }

        QQC2.Label {
            text: i18n("100% follows the panel height; increase or decrease to adjust the meter.")
            wrapMode: Text.WordWrap
        }

        QQC2.CheckBox {
            id: showSwapCheck
            text: i18n("Show swap gauge")
            visible: styleCombo.currentIndex !== 1
        }

        KQC.ColorButton {
            id: swapColorButton
            Kirigami.FormData.label: i18n("Swap color:")
            dialogTitle: i18n("Swap gauge color")
            showAlphaChannel: true
            visible: styleCombo.currentIndex !== 1
            enabled: colorModeCombo.currentIndex === 1 && showSwapCheck.checked
        }

        KQC.ColorButton {
            id: filledColorButton
            enabled: colorModeCombo.currentIndex === 1
            Kirigami.FormData.label: i18n("Active ticks / banks:")
            dialogTitle: i18n("Active meter color")
            showAlphaChannel: true
        }

        KQC.ColorButton {
            id: emptyColorButton
            enabled: colorModeCombo.currentIndex === 1
            Kirigami.FormData.label: i18n("Inactive ticks / banks:")
            dialogTitle: i18n("Inactive meter color")
            showAlphaChannel: true
        }

        KQC.ColorButton {
            id: textColorButton
            enabled: colorModeCombo.currentIndex === 1
            Kirigami.FormData.label: i18n("Percentage text:")
            dialogTitle: i18n("Percentage text color")
            showAlphaChannel: true
        }

        KQC.ColorButton {
            id: chipBodyColorButton
            enabled: colorModeCombo.currentIndex === 1
            Kirigami.FormData.label: i18n("Chip body:")
            dialogTitle: i18n("Chip body color")
            showAlphaChannel: true
        }

        KQC.ColorButton {
            id: chipOutlineColorButton
            enabled: colorModeCombo.currentIndex === 1
            Kirigami.FormData.label: i18n("Chip outline / pins:")
            dialogTitle: i18n("Chip outline and pin color")
            showAlphaChannel: true
        }

        QQC2.Button {
            text: i18n("Copy KDE colors to custom palette")
            onClicked: {
                root.cfg_colorMode = 1
                const background = Kirigami.Theme.backgroundColor
                const accent = Kirigami.Theme.linkColor
                const textColor = Kirigami.Theme.textColor
                filledColorButton.color = accent
                swapColorButton.color = Kirigami.Theme.neutralTextColor
                emptyColorButton.color = root.blend(background, accent, 0.24)
                textColorButton.color = textColor
                chipBodyColorButton.color = root.blend(background, accent, 0.13)
                chipOutlineColorButton.color = root.blend(textColor, accent, 0.35)
            }
        }
    }
}
