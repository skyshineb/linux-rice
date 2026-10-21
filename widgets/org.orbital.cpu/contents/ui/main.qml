// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

import QtQuick
import QtQuick.Layouts

import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.ksysguard.sensors as Sensors
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    Appearance {
        id: appearance
        configuration: Plasmoid.configuration
        theme: root.Kirigami.Theme
    }

    readonly property bool hovered: visible && fullRepresentationItem !== null
        && fullRepresentationItem.containsMouse
    readonly property real cpuPercent: sensorHasValue(cpuSensor)
        ? Math.max(0, Math.min(100, Number(cpuSensor.value))) : NaN

    function sensorHasValue(sensor) {
        return sensor.status === Sensors.Sensor.Ready
            && sensor.value !== null && sensor.value !== undefined
            && isFinite(Number(sensor.value)) && Number(sensor.value) >= 0
    }

    function detailText(sensor, divisor, decimals, unit) {
        // Detail sensors can report zero before their first real sample.
        if (!sensorHasValue(sensor) || Number(sensor.value) <= 0) {
            return "—"
        }
        return (Number(sensor.value) / divisor).toLocaleString(Qt.locale(), "f", decimals)
            + " " + unit
    }

    Plasmoid.title: "Orbital CPU"
    Plasmoid.icon: "utilities-system-monitor"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    // This gauge is the complete widget; Plasma requires a full representation
    // before it can select a separate compact representation.
    preferredRepresentation: fullRepresentation
    toolTipMainText: "Orbital CPU"
    toolTipTextFormat: Text.PlainText
    toolTipSubText: i18n("Usage: %1", isFinite(root.cpuPercent)
            ? root.cpuPercent.toLocaleString(Qt.locale(), "f", 0) + "%" : "—")
        + "\n" + i18n("Hottest core: %1", root.detailText(temperatureSensor, 1, 0, "°C"))
        + "\n" + i18n("Average frequency: %1", root.detailText(frequencySensor, 1000, 2, "GHz"))
        + "\n" + i18n("Open System Monitor")

    Sensors.Sensor {
        id: cpuSensor
        sensorId: "cpu/all/usage"
        updateRateLimit: 1000
    }

    // Subscribe to additional readings only while the widget is hovered.
    Sensors.Sensor {
        id: temperatureSensor
        sensorId: "cpu/all/maximumTemperature"
        enabled: root.hovered
        updateRateLimit: 1000
    }

    Sensors.Sensor {
        id: frequencySensor
        sensorId: "cpu/all/averageFrequency"
        enabled: root.hovered
        updateRateLimit: 1000
    }

    Plasma5Support.DataSource {
        id: applicationLauncher
        engine: "executable"
        connectedSources: []
        onNewData: disconnectSource(sourceName)
    }

    // Full panel representations need their own hover wrapper.
    fullRepresentation: PlasmaCore.ToolTipArea {
        id: gauge
        implicitWidth: indicator.implicitWidth
        implicitHeight: indicator.implicitHeight
        mainText: root.toolTipMainText
        subText: root.toolTipSubText
        textFormat: root.toolTipTextFormat
        location: Plasmoid.location
        active: true

        Layout.minimumWidth: implicitWidth
        Layout.preferredWidth: implicitWidth
        Layout.maximumWidth: implicitWidth
        Layout.minimumHeight: 40
        Layout.fillHeight: true

        CpuIndicator {
            id: indicator
            filledColor: appearance.filledColor
            emptyColor: appearance.emptyColor
            trackColor: appearance.trackColor
            textColor: appearance.textColor
            anchors.fill: parent
            cpuPercent: root.cpuPercent
            orbitStyle: Plasmoid.configuration.orbitStyle
            constellationReadoutPosition: Plasmoid.configuration.constellationReadoutPosition
            maxRpm: Plasmoid.configuration.maxRpm
            animationsEnabled: Kirigami.Units.longDuration > 0
            relativeSize: Plasmoid.configuration.indicatorScale
            horizontalPadding: Plasmoid.configuration.horizontalPadding
            verticalPadding: Plasmoid.configuration.verticalPadding
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: applicationLauncher.connectSource("plasma-systemmonitor")
        }
    }
}
