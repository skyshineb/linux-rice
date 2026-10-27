// SPDX-License-Identifier: MIT
import QtQuick
import org.kde.plasma.plasma5support as Plasma5Support
import "DiskUtils.js" as Utils

Item {
    id: root
    // Tests can inject Solid metadata without contacting a real desktop.
    property bool live: true
    property var deviceData: ({})
    readonly property var volumes: Utils.volumes(deviceData)
    readonly property string predicate: "IS StorageAccess"

    function refresh() {
        if (!sourceLoader.item) return
        const source = sourceLoader.item
        const queryData = source.data[predicate]
        const udis = queryData && queryData[predicate] ? Array.from(queryData[predicate]) : []
        const sources = [predicate].concat(udis)
        if (JSON.stringify(source.connectedSources) !== JSON.stringify(sources)) source.connectedSources = sources
        const snapshot = {}
        for (const udi of udis) if (source.data[udi]) snapshot[udi] = source.data[udi]
        // Only copy the fields we use; free-space updates are handled by Sensor.
        const rows = {}
        for (const udi in snapshot) {
            const data = snapshot[udi]
            rows[udi] = {}
            for (const key of ["Accessible", "Ignored", "File Path", "Device", "File System Type",
                               "UUID", "Label", "Description"]) rows[udi][key] = data[key]
        }
        if (JSON.stringify(deviceData) !== JSON.stringify(rows)) deviceData = rows
    }

    Loader {
        id: sourceLoader
        active: root.live
        sourceComponent: Component {
            Plasma5Support.DataSource {
                engine: "soliddevice"
                connectedSources: [root.predicate]
                onDataChanged: Qt.callLater(root.refresh)
                onSourcesChanged: Qt.callLater(root.refresh)
                onSourceRemoved: Qt.callLater(root.refresh)
            }
        }
        onLoaded: Qt.callLater(root.refresh)
    }
}
