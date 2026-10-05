/*
    SPDX-FileCopyrightText: 2011 Sebastian Kügler <sebas@kde.org>
    SPDX-FileCopyrightText: 2011 Viranch Mehta <viranch.mehta@gmail.com>
    SPDX-FileCopyrightText: 2013-2015 Kai Uwe Broulik <kde@privat.broulik.de>
    SPDX-FileCopyrightText: 2021-2022 ivan tkachenko <me@ratijas.tk>
    SPDX-License-Identifier: LGPL-2.0-or-later
*/

import QtQuick
import QtQuick.Layouts

import org.kde.config as KConfig
import org.kde.coreaddons as KCoreAddons
import org.kde.kcmutils as KCMUtils
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid

import org.kde.plasma.private.battery
import org.kde.plasma.private.batterymonitor
import org.kde.plasma.private.brightnesscontrolplugin

PlasmoidItem {
    id: batterymonitor

    BatteryControlModel {
        id: batteryControl
    }
    PowerProfilesControl {
        id: powerProfilesControl
        isSilent: batterymonitor.expanded
    }
    InhibitionControl {
        id: inhibitionControl
        isSilent: batterymonitor.expanded
    }
    ScreenBrightnessControl {
        id: screenBrightnessControl
        isSilent: batterymonitor.expanded
    }
    KeyboardBrightnessControl {
        id: keyboardBrightnessControl
        isSilent: batterymonitor.expanded
    }

    readonly property bool fullyCharged: batteryControl.pluggedIn
        && batteryControl.state === BatteryControlModel.FullyCharged
    readonly property string defaultProfile: powerProfilesControl.configuredProfile
        || "balanced"

    switchWidth: Kirigami.Units.gridUnit * 10
    switchHeight: Kirigami.Units.gridUnit * 10
    preferredRepresentation: compactRepresentation

    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.title: batteryControl.hasBatteries
        ? i18n("Battery and Brightness") : i18n("Power Management")
    Plasmoid.icon: batteryControl.hasBatteries ? "battery" : "video-display-brightness"
    Plasmoid.status: {
        if (inhibitionControl.isManuallyInhibited
                || (powerProfilesControl.activeProfile
                    && powerProfilesControl.activeProfile !== defaultProfile)) {
            return PlasmaCore.Types.ActiveStatus;
        }
        if (batteryControl.hasCumulative
                && (batteryControl.state === BatteryControlModel.Charging
                    || batteryControl.state === BatteryControlModel.Discharging)) {
            return PlasmaCore.Types.ActiveStatus;
        }
        return PlasmaCore.Types.PassiveStatus;
    }

    toolTipMainText: {
        if (!batteryControl.hasCumulative) {
            return Plasmoid.title;
        }
        if (fullyCharged) {
            return i18n("Fully Charged");
        }
        const percent = batteryControl.percent;
        if (batteryControl.pluggedIn) {
            if (batteryControl.state === BatteryControlModel.Charging) {
                return i18n("Battery at %1%, Charging", percent);
            }
            if (batteryControl.state === BatteryControlModel.Discharging) {
                return i18n("Battery at %1%, plugged in but still discharging", percent);
            }
            return i18n("Battery at %1%, not Charging", percent);
        }
        return i18n("Battery at %1%", percent);
    }
    toolTipSubText: {
        const parts = [];
        if (!batteryControl.hasBatteries) {
            parts.push(i18n("No Batteries Available"));
        }
        if (batteryControl.hasCumulative && batteryControl.smoothedRemainingMsec > 0
                && !fullyCharged) {
            const duration = KCoreAddons.Format.formatDuration(
                batteryControl.smoothedRemainingMsec, KCoreAddons.FormatTypes.HideSeconds);
            parts.push(batteryControl.state === BatteryControlModel.Charging
                ? i18n("%1 until fully charged", duration)
                : i18n("%1 remaining", duration));
        }
        if (inhibitionControl.isManuallyInhibited) {
            parts.push(i18n("Automatic sleep and screen locking are disabled"));
        }
        if (screenBrightnessControl.isBrightnessAvailable) {
            parts.push(i18n("Scroll to adjust screen brightness"));
        }
        return parts.join("\n");
    }

    compactRepresentation: CompactRepresentation {
        appletItem: batterymonitor
        chargePercent: batteryControl.hasCumulative ? batteryControl.percent : NaN
        charging: batteryControl.hasCumulative
            && batteryControl.state === BatteryControlModel.Charging

        onWheel: wheel => {
            if (!screenBrightnessControl.isBrightnessAvailable) {
                return;
            }
            const delta = (wheel.inverted ? -1 : 1)
                * (wheel.angleDelta.y ? wheel.angleDelta.y : -wheel.angleDelta.x);
            if (Math.abs(delta) < 120) {
                screenBrightnessControl.adjustBrightnessRatio((delta / 120) * 0.05);
            } else if (wheel.modifiers & Qt.ShiftModifier) {
                screenBrightnessControl.adjustBrightnessStep(delta < 0
                    ? ScreenBrightnessControl.DecreaseSmall
                    : ScreenBrightnessControl.IncreaseSmall);
            } else {
                screenBrightnessControl.adjustBrightnessStep(delta < 0
                    ? ScreenBrightnessControl.Decrease
                    : ScreenBrightnessControl.Increase);
            }
        }
    }

    fullRepresentation: PopupDialog {
        batteryModel: batteryControl
        profileControl: powerProfilesControl
        inhibitionBackend: inhibitionControl
        screenBrightnessBackend: screenBrightnessControl
        keyboardBrightnessBackend: keyboardBrightnessControl

        Layout.minimumWidth: Kirigami.Units.gridUnit * 10
        Layout.maximumWidth: Kirigami.Units.gridUnit * 80
        Layout.preferredWidth: Kirigami.Units.gridUnit * 20
        Layout.minimumHeight: Kirigami.Units.gridUnit * 10
        Layout.maximumHeight: Kirigami.Units.gridUnit * 40
        Layout.preferredHeight: implicitHeight
    }

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: i18n("&Show Energy Information…")
            icon.name: "documentinfo"
            visible: KConfig.KAuthorized.authorizeControlModule("kcm_energyinfo")
            onTriggered: KCMUtils.KCMLauncher.openInfoCenter("kcm_energyinfo")
        },
        PlasmaCore.Action {
            text: i18n("&Configure Energy Saving…")
            icon.name: "configure"
            visible: KConfig.KAuthorized.authorizeControlModule("kcm_powerdevilprofilesconfig")
            onTriggered: KCMUtils.KCMLauncher.openSystemSettings(
                "kcm_powerdevilprofilesconfig")
        }
    ]
}
