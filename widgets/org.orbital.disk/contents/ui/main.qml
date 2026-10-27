// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Layouts
import org.kde.kirigami as Kirigami
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as Plasma5Support
import "DiskUtils.js" as Utils

PlasmoidItem {
    id: root
    readonly property bool hovered: visible && fullRepresentationItem !== null && fullRepresentationItem.containsMouse
    Appearance { id: appearance; configuration: Plasmoid.configuration; theme: root.Kirigami.Theme }
    DiskData {
        id: diskData
        volumeId: Plasmoid.configuration.volumeId
        enabled: root.visible
        detailsEnabled: root.hovered
    }
    function amount(value, divisor, unit) {
        return isFinite(value) ? (value / divisor).toLocaleString(Qt.locale(), "f", 2) + " " + unit : "—"
    }
    Plasmoid.title: i18n("Orbital Disk")
    Plasmoid.icon: "drive-harddisk"
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    toolTipMainText: i18n("Orbital Disk") + (diskData.selection ? " · " + diskData.mountPath + " · " + diskData.volumeName : "")
    toolTipTextFormat: Text.PlainText
    toolTipSubText: (diskData.selection
        ? i18n("Used: %1 / %2 (%3)", amount(diskData.usedBytes, 1000000000, "GB"),
              amount(diskData.totalBytes, 1000000000, "GB"),
              isFinite(diskData.usedPercent) ? Math.round(diskData.usedPercent) + "%" : "—")
          + "\n" + i18n("Available: %1", amount(diskData.freeBytes, 1000000000, "GB"))
          + "\n" + i18n("Read: %1", amount(diskData.readBytesPerSecond, 1000000, "MB/s"))
          + "\n" + i18n("Write: %1", amount(diskData.writeBytesPerSecond, 1000000, "MB/s"))
          + (diskData.usedPercent >= 90 ? "\n" + i18n("Low disk space") : "")
        : i18n("Selected partition is unavailable")) + "\n" + i18n("Open System Monitor")

    Plasma5Support.DataSource {
        id: applicationLauncher
        engine: "executable"
        connectedSources: []
        onNewData: disconnectSource(sourceName)
    }
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
        DiskIndicator {
            id: indicator
            anchors.fill: parent
            meterStyle: Plasmoid.configuration.meterStyle
            usedPercent: diskData.usedPercent
            readBytesPerSecond: diskData.readBytesPerSecond
            writeBytesPerSecond: diskData.writeBytesPerSecond
            mountLabel: Utils.mountLabel(diskData.mountPath)
            ioScaleMBps: Plasmoid.configuration.ioScaleMBps
            animationsEnabled: Plasmoid.configuration.animationsEnabled && Kirigami.Units.longDuration > 0
            relativeSize: Plasmoid.configuration.meterScale
            horizontalPadding: Plasmoid.configuration.horizontalPadding
            verticalPadding: Plasmoid.configuration.verticalPadding
            filledColor: appearance.filledColor
            writeColor: appearance.writeColor
            emptyColor: appearance.emptyColor
            trackColor: appearance.trackColor
            textColor: appearance.textColor
            surfaceColor: appearance.surfaceColor
            warningColor: appearance.warningColor
        }
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: applicationLauncher.connectSource("plasma-systemmonitor")
        }
    }
}
