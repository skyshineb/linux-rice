// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kquickcontrols as KQC
import org.kde.kcmutils as KCM
import "DiskUtils.js" as Utils

KCM.SimpleKCM {
    id: root
    property int cfg_colorMode: 0
    property int cfg_meterStyle: 19
    property string cfg_volumeId: ""
    property alias cfg_meterScale: sizeSpin.value
    property alias cfg_horizontalPadding: horizontalSpin.value
    property alias cfg_verticalPadding: verticalSpin.value
    property alias cfg_ioScaleMBps: ioScaleSpin.value
    property alias cfg_animationsEnabled: animationCheck.checked
    property alias cfg_filledColor: filledButton.color
    property alias cfg_writeColor: writeButton.color
    property alias cfg_emptyColor: emptyButton.color
    property alias cfg_trackColor: trackButton.color
    property alias cfg_textColor: textButton.color
    property alias cfg_surfaceColor: surfaceButton.color
    property alias cfg_warningColor: warningButton.color
    // Allows isolated tests to load this page without accessing hardware.
    property bool discoveryEnabled: true

    VolumeModel { id: volumeModel; live: root.discoveryEnabled }
    readonly property var volumeChoices: {
        const choices = [{value: "", text: i18n("System (/) — automatic")}]
        for (const volume of volumeModel.volumes)
            choices.push({value: volume.id, text: volume.mountPath + " — " + volume.name})
        if (cfg_volumeId && !volumeModel.volumes.some(function(v) { return v.id === root.cfg_volumeId }))
            choices.push({value: cfg_volumeId, text: i18n("Unavailable partition") + " (" + cfg_volumeId + ")"})
        return choices
    }
    QtObject {
        id: previewConfiguration
        property int colorMode: root.cfg_colorMode
        property color filledColor: root.cfg_filledColor
        property color writeColor: root.cfg_writeColor
        property color emptyColor: root.cfg_emptyColor
        property color trackColor: root.cfg_trackColor
        property color textColor: root.cfg_textColor
        property color surfaceColor: root.cfg_surfaceColor
        property color warningColor: root.cfg_warningColor
    }
    Appearance { id: appearance; configuration: previewConfiguration; theme: root.Kirigami.Theme }

    Kirigami.FormLayout {
        QQC2.ComboBox {
            id: volumeCombo
            objectName: "diskVolumeCombo"
            Kirigami.FormData.label: i18n("Partition:")
            model: root.volumeChoices
            textRole: "text"
            currentIndex: Math.max(0, root.volumeChoices.findIndex(function(v) { return v.value === root.cfg_volumeId }))
            onActivated: root.cfg_volumeId = root.volumeChoices[currentIndex].value
        }
        QQC2.Label {
            text: i18n("Mounted local partitions only. An unavailable selection is kept until it returns.")
            wrapMode: Text.WordWrap
        }
        QQC2.ComboBox {
            objectName: "diskStyleCombo"
            Kirigami.FormData.label: i18n("Meter style:")
            model: Utils.styleNames
            currentIndex: Utils.styles.indexOf(Utils.style(root.cfg_meterStyle))
            onActivated: root.cfg_meterStyle = Utils.styles[currentIndex]
        }
        DiskVisual {
            objectName: "diskSettingsPreview"
            Kirigami.FormData.label: i18n("Preview:")
            implicitWidth: 112; implicitHeight: 112
            meterStyle: root.cfg_meterStyle
            usedPercent: 64; readBytesPerSecond: 280000000; writeBytesPerSecond: 96000000
            mountLabel: Utils.mountLabel(Utils.selectedVolume(volumeModel.volumes, root.cfg_volumeId)?.mountPath || (root.cfg_volumeId ? "" : "/"))
            ioScaleMBps: root.cfg_ioScaleMBps
            animationsEnabled: root.cfg_animationsEnabled && Kirigami.Units.longDuration > 0
            filledColor: appearance.filledColor; writeColor: appearance.writeColor
            emptyColor: appearance.emptyColor; trackColor: appearance.trackColor
            textColor: appearance.textColor; surfaceColor: appearance.surfaceColor; warningColor: appearance.warningColor
        }
        QQC2.Label { text: i18n("Demonstration: 64% used · read 280 MB/s · write 96 MB/s"); wrapMode: Text.WordWrap }
        QQC2.SpinBox {
            id: sizeSpin
            Kirigami.FormData.label: i18n("Relative size:")
            from: 60; to: 150; stepSize: 5; value: 100
            textFromValue: function(value) { return value + "%" }
        }
        QQC2.SpinBox { id: horizontalSpin; Kirigami.FormData.label: i18n("Horizontal padding:"); from: 0; to: 32; value: 0 }
        QQC2.SpinBox { id: verticalSpin; Kirigami.FormData.label: i18n("Vertical padding:"); from: 0; to: 24; value: 0 }
        QQC2.SpinBox {
            id: ioScaleSpin
            Kirigami.FormData.label: i18n("I/O scale (MB/s):")
            from: 1; to: 100000; value: 400; stepSize: 50; editable: true
        }
        QQC2.Label {
            text: i18n("Inner arc and R/W bars show transfer rates relative to this scale, not I/O busy time.")
            wrapMode: Text.WordWrap
        }
        QQC2.CheckBox { id: animationCheck; text: i18n("Animate disk activity"); checked: true }
        QQC2.ComboBox {
            Kirigami.FormData.label: i18n("Color source:")
            model: [i18n("KDE theme"), i18n("Custom colors")]
            currentIndex: root.cfg_colorMode === 1 ? 1 : 0
            onActivated: root.cfg_colorMode = currentIndex
        }
        KQC.ColorButton { id: filledButton; color: "#67C4DE"; enabled: root.cfg_colorMode === 1; Kirigami.FormData.label: i18n("Used space / read:"); dialogTitle: i18n("Used space and read color"); showAlphaChannel: true }
        KQC.ColorButton { id: writeButton; color: "#E6B96A"; enabled: root.cfg_colorMode === 1; Kirigami.FormData.label: i18n("Write:"); dialogTitle: i18n("Write color"); showAlphaChannel: true }
        KQC.ColorButton { id: emptyButton; color: "#335363"; enabled: root.cfg_colorMode === 1; Kirigami.FormData.label: i18n("Inactive elements:"); dialogTitle: i18n("Inactive color"); showAlphaChannel: true }
        KQC.ColorButton { id: trackButton; color: "#547C8C"; enabled: root.cfg_colorMode === 1; Kirigami.FormData.label: i18n("Structure / outlines:"); dialogTitle: i18n("Structure color"); showAlphaChannel: true }
        KQC.ColorButton { id: textButton; color: "#E7EEF2"; enabled: root.cfg_colorMode === 1; Kirigami.FormData.label: i18n("Percentage text:"); dialogTitle: i18n("Percentage color"); showAlphaChannel: true }
        KQC.ColorButton { id: surfaceButton; color: "#101D2B"; enabled: root.cfg_colorMode === 1; Kirigami.FormData.label: i18n("Center background:"); dialogTitle: i18n("Center background color"); showAlphaChannel: true }
        KQC.ColorButton { id: warningButton; color: "#E4818A"; enabled: root.cfg_colorMode === 1; Kirigami.FormData.label: i18n("Low space (90% used):"); dialogTitle: i18n("Low disk space color"); showAlphaChannel: true }
        QQC2.Button {
            text: i18n("Copy KDE colors to custom palette")
            onClicked: {
                const theme = root.Kirigami.Theme
                root.cfg_filledColor = theme.linkColor
                root.cfg_writeColor = theme.neutralTextColor
                root.cfg_emptyColor = appearance.blend(theme.backgroundColor, theme.linkColor, .24)
                root.cfg_trackColor = appearance.blend(theme.backgroundColor, theme.textColor, .35)
                root.cfg_textColor = theme.textColor
                root.cfg_surfaceColor = theme.backgroundColor
                root.cfg_warningColor = theme.negativeTextColor
                root.cfg_colorMode = 1
            }
        }
    }
}
