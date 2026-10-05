import QtQuick
import QtQuick.Layouts

import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support
import org.kde.ksysguard.sensors as Sensors

PlasmoidItem {
    id: root

    readonly property bool fanStyle: Plasmoid.configuration.meterStyle !== 1
    readonly property real ramPercent: sensorHasValue(memorySensor)
        ? Math.max(0, Math.min(100, Number(memorySensor.value))) : NaN
    readonly property bool swapDisabled: sensorHasValue(swapTotalSensor) && Number(swapTotalSensor.value) === 0
    readonly property real swapPercent: swapDisabled ? 0
        : sensorHasValue(swapUsedSensor) && sensorHasValue(swapTotalSensor)
            ? Math.max(0, Math.min(100, Number(swapUsedSensor.value) / Number(swapTotalSensor.value) * 100)) : NaN

    function sensorHasValue(sensor) {
        return sensor.status === Sensors.Sensor.Ready
            && sensor.value !== null && sensor.value !== undefined
            && isFinite(Number(sensor.value)) && Number(sensor.value) >= 0
    }

    function usageText(label, usedSensor, totalSensor, percent) {
        const percentText = isFinite(percent) ? Math.round(percent) + "%" : "—"
        if (!sensorHasValue(usedSensor) || !sensorHasValue(totalSensor) || Number(totalSensor.value) <= 0) {
            return i18n("%1: %2", label, percentText)
        }
        // Memory sensors report bytes; keep both readings in decimal GB.
        const usedGB = (Number(usedSensor.value) / 1000000000).toLocaleString(Qt.locale(), "f", 2)
        const totalGB = (Number(totalSensor.value) / 1000000000).toLocaleString(Qt.locale(), "f", 2)
        return i18n("%1: %2 / %3 GB (%4)", label, usedGB, totalGB, percentText)
    }

    Plasmoid.title: "Orbital Memory"
    Plasmoid.icon: "utilities-system-monitor"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    // This gauge is the complete widget; Plasma requires a full representation
    // before it can select a separate compact representation.
    preferredRepresentation: fullRepresentation
    toolTipMainText: "Orbital Memory"
    toolTipTextFormat: Text.PlainText
    toolTipSubText: root.fanStyle
        ? root.usageText(i18n("RAM"), ramUsedSensor, ramTotalSensor, root.ramPercent) + "\n"
            + (root.swapDisabled ? i18n("Swap: disabled")
                : root.usageText(i18n("Swap"), swapUsedSensor, swapTotalSensor, root.swapPercent))
            + "\n" + i18n("Open System Monitor")
        : "RAM " + (isFinite(root.ramPercent) ? Math.round(root.ramPercent) + "%" : "—")
            + "  ·  Open System Monitor"

    Sensors.Sensor {
        id: memorySensor
        sensorId: "memory/physical/usedPercent"
        updateRateLimit: 1000
    }

    // Fan's tooltip includes amounts even when its swap arc is hidden.
    Sensors.Sensor {
        id: ramUsedSensor
        sensorId: "memory/physical/used"
        enabled: root.fanStyle
        updateRateLimit: 1000
    }

    Sensors.Sensor {
        id: ramTotalSensor
        sensorId: "memory/physical/total"
        enabled: root.fanStyle
        updateRateLimit: 1000
    }

    Sensors.Sensor {
        id: swapUsedSensor
        sensorId: "memory/swap/used"
        enabled: root.fanStyle
        updateRateLimit: 1000
    }

    Sensors.Sensor {
        id: swapTotalSensor
        sensorId: "memory/swap/total"
        enabled: root.fanStyle
        updateRateLimit: 1000
    }

    Plasma5Support.DataSource {
        id: applicationLauncher
        engine: "executable"
        connectedSources: []
        onNewData: disconnectSource(sourceName)
    }

    // A full panel representation does not get Plasma's compact hover wrapper.
    // Keep this area active independently of the optional swap arc.
    fullRepresentation: PlasmaCore.ToolTipArea {
        id: gauge
        mainText: root.toolTipMainText
        subText: root.toolTipSubText
        textFormat: root.toolTipTextFormat
        location: Plasmoid.location
        active: true

        readonly property real padding: Math.max(2, Math.round(height * 0.05))
        readonly property real configuredScale: Number(Plasmoid.configuration.meterScale)
        readonly property real meterScale: isFinite(configuredScale)
            ? Math.max(60, Math.min(110, configuredScale)) : 100
        readonly property real visualHeight: height > 0
            ? Math.min(height, Math.max(24, (height - 2 * padding) * meterScale / 100)) : 44
        readonly property real slotWidth: visualHeight * 48 / 44

        Layout.minimumWidth: slotWidth
        Layout.preferredWidth: slotWidth
        Layout.maximumWidth: slotWidth
        Layout.minimumHeight: 40
        Layout.fillHeight: true

        MemoryVisual {
            anchors.centerIn: parent
            width: gauge.visualHeight
            height: gauge.visualHeight
            ramPercent: root.ramPercent
            swapPercent: root.swapPercent
            showSwapGauge: Plasmoid.configuration.showSwapGauge
            swapColor: Plasmoid.configuration.swapColor
            meterStyle: Plasmoid.configuration.meterStyle
            filledColor: Plasmoid.configuration.filledColor
            emptyColor: Plasmoid.configuration.emptyColor
            textColor: Plasmoid.configuration.textColor
            chipBodyColor: Plasmoid.configuration.chipBodyColor
            chipOutlineColor: Plasmoid.configuration.chipOutlineColor
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: applicationLauncher.connectSource("plasma-systemmonitor")
        }
    }
}
