import QtQuick

Item {
    id: root
    implicitWidth: height + (readoutBesideOrbit ? measuredReadout.implicitWidth + readoutGap : 0)
    implicitHeight: 44
    readonly property real unit: height / 44
    readonly property real readoutGap: Math.max(4, Math.round(6 * unit))

    property real cpuPercent: NaN
    // 0 = original orbit, 1 = Constellation, 2 = Pulsar.
    property int orbitStyle: 0
    // Constellation only: 0 = beside the orbit, 1 = inside, behind the geometry.
    property int constellationReadoutPosition: 0
    property real maxRpm: 30
    property bool animationsEnabled: true
    readonly property int effectiveStyle: orbitStyle === 1 || orbitStyle === 2 ? orbitStyle : 0
    readonly property bool readoutBesideOrbit: effectiveStyle === 1 && constellationReadoutPosition !== 1
    readonly property bool cpuReady: isFinite(cpuPercent)
    readonly property real clampedPercent: cpuReady ? Math.max(0, Math.min(100, cpuPercent)) : 0
    readonly property real orbitRpm: cpuReady && isFinite(maxRpm)
        ? Math.max(0, Math.min(120, maxRpm)) * clampedPercent / 100
        : 0
    property real orbitAngle: 0

    Loader {
        anchors.verticalCenter: parent.verticalCenter
        x: root.readoutBesideOrbit ? 0 : (parent.width - width) / 2
        width: root.height
        height: root.height
        // Paint Constellation over its central percentage without a text backdrop.
        z: root.effectiveStyle === 1 && !root.readoutBesideOrbit ? 1 : 0
        sourceComponent: root.effectiveStyle === 1 ? constellation
            : root.effectiveStyle === 2 ? pulsar : classic
    }

    Component {
        id: classic
        ClassicCpuVisual {
            cpuReady: root.cpuReady
            orbitAngle: root.orbitAngle
        }
    }

    Component {
        id: constellation
        ConstellationCpuVisual {
            cpuReady: root.cpuReady
            orbitAngle: root.orbitAngle
        }
    }

    Component {
        id: pulsar
        PulsarCpuVisual {
            cpuReady: root.cpuReady
            cpuPercent: root.clampedPercent
            orbitAngle: root.orbitAngle
        }
    }

    // Reserve the widest percentage so changing CPU load never shifts the panel.
    Text {
        id: measuredReadout
        text: "100%"
        font: readout.font
        visible: false
    }

    Text {
        id: readout
        anchors.verticalCenter: parent.verticalCenter
        x: root.readoutBesideOrbit ? root.height + root.readoutGap : Math.round((parent.width - width) / 2)
        width: root.readoutBesideOrbit ? measuredReadout.implicitWidth : implicitWidth
        horizontalAlignment: Text.AlignHCenter
        text: root.cpuReady ? Math.round(root.clampedPercent) + "%" : "—"
        color: "#E7EEF2"
        font.family: "IBM Plex Mono"
        font.pixelSize: Math.max(8, Math.round(11 * root.unit))
        font.weight: Font.Medium
    }

    Timer {
        id: orbitTimer
        interval: 16
        repeat: true
        running: root.visible && root.animationsEnabled && root.orbitRpm > 0
        property double lastTick: 0
        onRunningChanged: lastTick = Date.now()
        onTriggered: {
            var now = Date.now()
            var elapsed = Math.max(0, Math.min(250, now - lastTick))
            lastTick = now
            root.orbitAngle = (root.orbitAngle + 6 * root.orbitRpm * elapsed / 1000) % 360
        }
    }
}
