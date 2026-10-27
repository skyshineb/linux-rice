// SPDX-License-Identifier: MIT
import QtQuick
import "DiskUtils.js" as Utils

Item {
    id: root
    property string volumeId: ""
    property bool detailsEnabled: false
    property bool discoveryEnabled: true
    readonly property var volumes: volumeModel.volumes
    readonly property var selection: Utils.selectedVolume(volumes, volumeId)
    readonly property string prefix: selection ? selection.sensorPrefix : ""
    readonly property string mountPath: selection ? selection.mountPath : ""
    readonly property string volumeName: selection ? selection.name : ""
    readonly property real usedPercent: sensorLoader.item ? sensorLoader.item.usedPercent : NaN
    readonly property real readBytesPerSecond: sensorLoader.item ? sensorLoader.item.readBytesPerSecond : NaN
    readonly property real writeBytesPerSecond: sensorLoader.item ? sensorLoader.item.writeBytesPerSecond : NaN
    readonly property real usedBytes: sensorLoader.item ? sensorLoader.item.usedBytes : NaN
    readonly property real totalBytes: sensorLoader.item ? sensorLoader.item.totalBytes : NaN
    readonly property real freeBytes: sensorLoader.item ? sensorLoader.item.freeBytes : NaN

    VolumeModel { id: volumeModel; live: root.discoveryEnabled }
    Loader { id: sensorLoader }
    function reload() {
        // Recreate the subscription group so a new UUID can never display an old value.
        sensorLoader.source = ""
        if (enabled && prefix) sensorLoader.setSource(Qt.resolvedUrl("DiskSensors.qml"),
            {prefix: prefix, detailsEnabled: detailsEnabled})
    }
    onPrefixChanged: reload()
    onEnabledChanged: reload()
    onDetailsEnabledChanged: if (sensorLoader.item) sensorLoader.item.detailsEnabled = detailsEnabled
    Component.onCompleted: reload()
}
