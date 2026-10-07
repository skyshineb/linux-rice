/*
    SPDX-FileCopyrightText: 2011 Viranch Mehta <viranch.mehta@gmail.com>
    SPDX-FileCopyrightText: 2013-2016 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
    Orbital adaptation; publication notice added 2026-10-07.
    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.extras as PlasmaExtras

PlasmaExtras.Representation {
    id: dialog

    required property var batteryModel
    required property var profileControl
    required property var inhibitionBackend
    required property var screenBrightnessBackend
    required property var keyboardBrightnessBackend

    collapseMarginsHint: true

    contentItem: PlasmaComponents3.ScrollView {
        id: scrollView
        focus: false
        PlasmaComponents3.ScrollBar.horizontal.policy:
            PlasmaComponents3.ScrollBar.AlwaysOff

        ColumnLayout {
            width: scrollView.availableWidth
            spacing: Kirigami.Units.smallSpacing * 2

            PowerManagementItem {
                Layout.fillWidth: true
                control: dialog.inhibitionBackend
            }

            Repeater {
                model: dialog.screenBrightnessBackend.displays
                delegate: BrightnessItem {
                    required property string displayName
                    required property string label
                    required property int brightness
                    required property int maxBrightness

                    Layout.fillWidth: true
                    icon.name: "video-display-brightness"
                    text: label
                    value: brightness
                    maximumValue: maxBrightness
                    stepSize: Math.max(1, maxBrightness / 100)
                    onMoved: value =>
                        dialog.screenBrightnessBackend.setBrightness(displayName, value)
                }
            }

            BrightnessItem {
                Layout.fillWidth: true
                icon.name: "input-keyboard-brightness"
                text: i18n("Keyboard Brightness")
                value: dialog.keyboardBrightnessBackend.brightness
                maximumValue: dialog.keyboardBrightnessBackend.brightnessMax
                visible: dialog.keyboardBrightnessBackend.isBrightnessAvailable
                onMoved: value => dialog.keyboardBrightnessBackend.brightness = value
            }

            PowerProfileItem {
                Layout.fillWidth: true
                control: dialog.profileControl
            }

            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: !dialog.batteryModel.hasBatteries
                text: i18n("No Batteries Available")
            }

            Repeater {
                model: dialog.batteryModel
                delegate: BatteryItem {
                    Layout.fillWidth: true
                    batteryPercent: Percent
                    batteryCapacity: Capacity
                    batteryEnergy: Energy
                    batteryPluggedIn: PluggedIn
                    batteryIsPowerSupply: IsPowerSupply
                    batteryChargeState: ChargeState
                    batteryPrettyName: PrettyName
                    batteryType: Type
                    pluggedIn: dialog.batteryModel.pluggedIn
                    remainingTime: dialog.batteryModel.smoothedRemainingMsec
                    chargeStopThreshold: dialog.batteryModel.chargeStopThreshold
                }
            }
        }
    }
}
