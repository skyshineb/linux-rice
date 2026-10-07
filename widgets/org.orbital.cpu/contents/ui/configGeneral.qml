// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_orbitStyle: styleCombo.currentIndex
    property alias cfg_constellationReadoutPosition: constellationReadoutCombo.currentIndex
    property alias cfg_maxRpm: speedSpin.value
    property alias cfg_indicatorScale: sizeSpin.value
    property alias cfg_horizontalPadding: horizontalPaddingSpin.value
    property alias cfg_verticalPadding: verticalPaddingSpin.value

    Kirigami.FormLayout {
        QQC2.ComboBox {
            id: styleCombo
            Kirigami.FormData.label: i18n("Orbit style:")
            model: [i18n("Classic"), i18n("Constellation"), i18n("Pulsar")]
        }

        QQC2.ComboBox {
            id: constellationReadoutCombo
            visible: styleCombo.currentIndex === 1
            Kirigami.FormData.label: i18n("Percentage position:")
            implicitContentWidthPolicy: QQC2.ComboBox.WidestText
            model: [i18n("Beside the orbit"), i18n("Inside, behind the geometry")]
        }

        Rectangle {
            Kirigami.FormData.label: i18n("Panel preview at 50% CPU:")
            implicitWidth: Math.max(160, panelPreview.implicitWidth + 24)
            implicitHeight: 64
            color: "#101D2B"
            radius: 8

            CpuIndicator {
                id: panelPreview
                anchors.centerIn: parent
                width: implicitWidth
                height: 48
                cpuPercent: 50
                orbitStyle: styleCombo.currentIndex
                constellationReadoutPosition: constellationReadoutCombo.currentIndex
                maxRpm: speedSpin.value
                animationsEnabled: Kirigami.Units.longDuration > 0
                relativeSize: sizeSpin.value
                horizontalPadding: horizontalPaddingSpin.value
                verticalPadding: verticalPaddingSpin.value
            }
        }

        QQC2.SpinBox {
            id: sizeSpin
            Kirigami.FormData.label: i18n("Indicator size:")
            from: 60
            to: 150
            stepSize: 5
            editable: true
            value: 100
            validator: RegularExpressionValidator { regularExpression: /[0-9]{1,3}\s*%?/ }
            textFromValue: function(value) { return value + "%" }
            valueFromText: function(text) { return Number(text.replace(/\s*%\s*$/, "")) }
        }

        QQC2.SpinBox {
            id: horizontalPaddingSpin
            Kirigami.FormData.label: i18n("Horizontal padding on each side (px):")
            from: 0
            to: 32
            value: 4
            editable: true
        }

        QQC2.SpinBox {
            id: verticalPaddingSpin
            Kirigami.FormData.label: i18n("Vertical padding on each side (px):")
            from: 0
            to: 24
            value: 4
            editable: true
        }

        QQC2.Label {
            text: i18n("Size and padding apply to every style. The panel height limits the size and vertical padding.")
            wrapMode: Text.WordWrap
        }

        QQC2.SpinBox {
            id: speedSpin
            Kirigami.FormData.label: i18n("Maximum speed at 100% CPU (RPM):")
            from: 0
            to: 120
            stepSize: 1
            editable: true
        }
    }
}
