// SPDX-License-Identifier: MIT
import QtQuick
import org.kde.ksysguard.sensors as Sensors
import "DiskUtils.js" as Utils

Item {
    id: root
    required property string prefix
    property bool detailsEnabled: false
    function value(sensor) {
        return sensor.status === Sensors.Sensor.Ready ? Utils.reading(sensor.value) : NaN
    }
    readonly property real usedPercent: Utils.clamp(value(percentSensor), 0, 100, NaN)
    readonly property real readBytesPerSecond: value(readSensor)
    readonly property real writeBytesPerSecond: value(writeSensor)
    readonly property real usedBytes: value(usedSensor)
    readonly property real totalBytes: value(totalSensor)
    readonly property real freeBytes: value(freeSensor)

    Sensors.Sensor { id: percentSensor; sensorId: root.prefix + "/usedPercent"; updateRateLimit: 1000 }
    Sensors.Sensor { id: readSensor; sensorId: root.prefix + "/read"; updateRateLimit: 1000 }
    Sensors.Sensor { id: writeSensor; sensorId: root.prefix + "/write"; updateRateLimit: 1000 }
    Sensors.Sensor { id: usedSensor; sensorId: root.prefix + "/used"; enabled: root.detailsEnabled; updateRateLimit: 1000 }
    Sensors.Sensor { id: totalSensor; sensorId: root.prefix + "/total"; enabled: root.detailsEnabled; updateRateLimit: 1000 }
    Sensors.Sensor { id: freeSensor; sensorId: root.prefix + "/free"; enabled: root.detailsEnabled; updateRateLimit: 1000 }
}
