import QtQuick
import QtQuick.Layouts

import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.ksysguard.sensors as Sensors
import org.kde.kirigami as Kirigami

PlasmoidItem {
    Plasmoid.title: "Orbital CPU"
    Plasmoid.icon: "utilities-system-monitor"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    // This gauge is the complete widget; Plasma requires a full representation
    // before it can select a separate compact representation.
    preferredRepresentation: fullRepresentation
    toolTipMainText: "Orbital CPU"
    toolTipSubText: "CPU " + (cpuSensor.status === Sensors.Sensor.Ready ? Math.round(cpuSensor.value) + "%" : "—")
        + "  ·  Open System Monitor"

    Sensors.Sensor {
        id: cpuSensor
        sensorId: "cpu/all/usage"
        updateRateLimit: 1000
    }

    Plasma5Support.DataSource {
        id: applicationLauncher
        engine: "executable"
        connectedSources: []
        onNewData: disconnectSource(sourceName)
    }

    fullRepresentation: CpuIndicator {
        id: gauge

        Layout.minimumWidth: implicitWidth
        Layout.preferredWidth: implicitWidth
        Layout.maximumWidth: implicitWidth
        Layout.minimumHeight: 40
        Layout.fillHeight: true

        cpuPercent: cpuSensor.status === Sensors.Sensor.Ready ? Number(cpuSensor.value) : NaN
        orbitStyle: Plasmoid.configuration.orbitStyle
        constellationReadoutPosition: Plasmoid.configuration.constellationReadoutPosition
        maxRpm: Plasmoid.configuration.maxRpm
        animationsEnabled: Kirigami.Units.longDuration > 0
        relativeSize: Plasmoid.configuration.indicatorScale
        horizontalPadding: Plasmoid.configuration.horizontalPadding
        verticalPadding: Plasmoid.configuration.verticalPadding

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: applicationLauncher.connectSource("plasma-systemmonitor")
        }
    }
}
