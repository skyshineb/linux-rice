import QtQuick 2.15
import QtQuick.Layouts 1.15

import org.kde.plasma.core 2.0 as PlasmaCore
import org.kde.plasma.plasmoid 2.0
import org.kde.ksysguard.sensors 1.0 as Sensors

Item {
    Plasmoid.title: "Orbital Memory"
    Plasmoid.icon: "utilities-system-monitor"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    Plasmoid.preferredRepresentation: Plasmoid.compactRepresentation
    Plasmoid.toolTipMainText: "Orbital Memory"
    Plasmoid.toolTipSubText: "RAM " + (memorySensor.status === Sensors.Sensor.Ready ? Math.round(memorySensor.value) + "%" : "—")
        + "  ·  Open System Monitor"

    Sensors.Sensor {
        id: memorySensor
        sensorId: "memory/physical/usedPercent"
        updateRateLimit: 1000
    }

    PlasmaCore.DataSource {
        id: applicationLauncher
        engine: "executable"
        connectedSources: []
        onNewData: disconnectSource(sourceName)
    }

    Plasmoid.compactRepresentation: Item {
        id: compact
        readonly property real padding: Math.max(4, Math.round(height * 0.08))
        readonly property real visualHeight: height > 0 ? Math.max(24, height - 2 * padding) : 44
        readonly property real slotWidth: visualHeight * 50 / 44

        Layout.minimumWidth: slotWidth
        Layout.preferredWidth: slotWidth
        Layout.maximumWidth: slotWidth
        Layout.minimumHeight: 40
        Layout.fillHeight: true

        MemoryVisual {
            anchors.centerIn: parent
            width: compact.visualHeight
            height: compact.visualHeight
            ramPercent: memorySensor.status === Sensors.Sensor.Ready ? Number(memorySensor.value) : NaN
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: applicationLauncher.connectSource("plasma-systemmonitor")
        }
    }
}
