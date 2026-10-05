/*
    SPDX-FileCopyrightText: 2012-2013 Daniel Nicoletti <dantti12@gmail.com>
    SPDX-FileCopyrightText: 2013-2015 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.coreaddons as KCoreAddons
import org.kde.kirigami as Kirigami
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.workspace.components as WorkspaceComponents
import org.kde.plasma.private.battery

PlasmaComponents3.ItemDelegate {
    id: root
    property int batteryPercent: -1
    property int batteryCapacity: 0
    property real batteryEnergy: 0
    property bool batteryPluggedIn: false
    property bool batteryIsPowerSupply: false
    property int batteryChargeState: BatteryControlModel.NoCharge
    property string batteryPrettyName: ""
    property string batteryType: ""
    property bool pluggedIn: false
    property real remainingTime: 0
    property int chargeStopThreshold: 0

    readonly property bool percentKnown: batteryPercent >= 0
    readonly property bool atChargeLimit: pluggedIn && batteryIsPowerSupply
        && chargeStopThreshold > 0 && chargeStopThreshold < 100
        && Math.abs(batteryPercent - chargeStopThreshold) <= 1
        && (batteryChargeState === BatteryControlModel.NoCharge
            || batteryChargeState === BatteryControlModel.FullyCharged)
    readonly property string stateText: {
        if (!batteryPluggedIn) {
            return i18n("Not present");
        }
        if (atChargeLimit) {
            return i18n("Fully Charged");
        }
        switch (batteryChargeState) {
        case BatteryControlModel.Charging: return i18n("Charging");
        case BatteryControlModel.Discharging: return i18n("Discharging");
        case BatteryControlModel.FullyCharged: return i18n("Fully Charged");
        default: return i18n("Not Charging");
        }
    }

    text: batteryPrettyName
    background.visible: highlighted
    highlighted: activeFocus
    hoverEnabled: false

    contentItem: RowLayout {
        spacing: Kirigami.Units.gridUnit

        WorkspaceComponents.BatteryIcon {
            Layout.alignment: Qt.AlignTop
            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
            batteryType: root.batteryType
            percent: Math.max(0, root.batteryPercent)
            hasBattery: root.batteryPluggedIn && root.percentKnown
            pluggedIn: root.pluggedIn && root.batteryIsPowerSupply
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing

            RowLayout {
                Layout.fillWidth: true
                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    text: root.text
                    elide: Text.ElideRight
                }
                PlasmaComponents3.Label {
                    visible: root.batteryIsPowerSupply
                        || root.batteryChargeState !== BatteryControlModel.NoCharge
                    text: root.stateText
                    opacity: 0.75
                }
                PlasmaComponents3.Label {
                    visible: root.batteryPluggedIn
                    text: root.percentKnown
                        ? i18n("%1%", root.batteryPercent) : i18n("Unknown")
                }
            }

            PlasmaComponents3.ProgressBar {
                Layout.fillWidth: true
                from: 0
                to: 100
                value: Math.max(0, root.batteryPercent)
                visible: root.batteryPluggedIn && root.percentKnown
            }

            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: root.batteryIsPowerSupply && root.remainingTime > 0
                    && (root.batteryChargeState === BatteryControlModel.Charging
                        || root.batteryChargeState === BatteryControlModel.Discharging)
                text: root.batteryChargeState === BatteryControlModel.Charging
                    ? i18n("%1 until fully charged",
                           KCoreAddons.Format.formatDuration(
                               root.remainingTime, KCoreAddons.FormatTypes.HideSeconds))
                    : i18n("%1 remaining",
                           KCoreAddons.Format.formatDuration(
                               root.remainingTime, KCoreAddons.FormatTypes.HideSeconds))
                opacity: 0.75
            }
            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: root.batteryIsPowerSupply && root.batteryCapacity > 0
                text: i18n("Battery health: %1%", root.batteryCapacity)
                color: root.batteryCapacity < 50
                    ? Kirigami.Theme.neutralTextColor : Kirigami.Theme.textColor
                wrapMode: Text.WordWrap
            }
            InhibitionHint {
                Layout.fillWidth: true
                visible: root.pluggedIn && root.batteryIsPowerSupply
                    && root.chargeStopThreshold > 0 && root.chargeStopThreshold < 100
                iconSource: "kt-speed-limits"
                text: i18n("Battery is configured to charge up to approximately %1%.",
                           root.chargeStopThreshold)
            }
        }
    }
}
