import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.plasma.plasmoid 2.0
import org.kde.ksysguard.sensors 1.0 as Sensors

Item {
    id: root
    Plasmoid.title: "Orbital Load"
    Plasmoid.icon: "utilities-system-monitor"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.preferredRepresentation: Plasmoid.compactRepresentation
    Plasmoid.toolTipMainText: "Orbital Load"
    Plasmoid.toolTipSubText: "CPU " + (cpuSensor.status === Sensors.Sensor.Ready ? Math.round(cpuSensor.value) + "%" : "—")
        + "  ·  RAM " + (ramSensor.status === Sensors.Sensor.Ready ? Math.round(ramSensor.value) + "%" : "—")
        + "  ·  Open System Monitor"

    Sensors.Sensor {
        id: cpuSensor
        sensorId: "cpu/all/usage"
        updateRateLimit: 1000
    }
    Sensors.Sensor {
        id: ramSensor
        sensorId: "memory/physical/usedPercent"
        updateRateLimit: 1000
    }

    // Plasma 5's executable engine keeps the app alive until it exits.
    PlasmaCore.DataSource {
        id: applicationLauncher
        engine: "executable"
        connectedSources: []
        onNewData: disconnectSource(sourceName)
    }

    Plasmoid.compactRepresentation: Item {
        Layout.minimumWidth: 100
        Layout.preferredWidth: 100
        Layout.maximumWidth: 100
        Layout.minimumHeight: 44
        Layout.preferredHeight: 44

        LoadVisual {
            anchors.centerIn: parent
            cpuPercent: cpuSensor.status === Sensors.Sensor.Ready ? Number(cpuSensor.value) : NaN
            ramPercent: ramSensor.status === Sensors.Sensor.Ready ? Number(ramSensor.value) : NaN
            animationsEnabled: PlasmaCore.Units.longDuration > 0
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: applicationLauncher.connectSource("plasma-systemmonitor")
        }
    }
}
