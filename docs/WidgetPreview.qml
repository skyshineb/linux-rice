// SPDX-License-Identifier: MIT
// Battery visuals retain their LGPL-2.0-or-later license.
import QtQuick
import "../widgets/org.orbital.cpu/contents/ui" as CPU
import "../widgets/org.orbital.memory/contents/ui" as Memory
import "../widgets/org.orbital.disk/contents/ui" as Disk
import "../widgets/org.orbital.battery/contents/ui" as Battery

Rectangle {
    id: root
    required property string kind
    width: 960
    height: kind === "disk" ? 540 : 236
    color: "#101D2B"
    readonly property var examples: ({
        cpu: [{label: "Classic", style: 0}, {label: "Constellation", style: 1}, {label: "Pulsar", style: 2}],
        memory: [{label: "Fan · RAM 67% / swap 30%", style: 0}, {label: "Silicon · RAM 67%", style: 1}],
        disk: [{label: "02 · Double contour", style: 2}, {label: "04 · Spiral", style: 4},
               {label: "13 · Archive", style: 13}, {label: "14 · Packets", style: 14},
               {label: "16 · Radar", style: 16}, {label: "17 · Turbine", style: 17},
               {label: "18 · Honeycomb", style: 18}, {label: "19 · Terminal", style: 19},
               {label: "20 · Three channels", style: 20}],
        battery: [{label: "65% · on battery", charge: 65, charging: false},
                  {label: "47% · charging", charge: 47, charging: true},
                  {label: "20% · low charge", charge: 20, charging: false},
                  {label: "100% · full", charge: 100, charging: false}]
    })
    Text {
        x: 24; y: 18
        text: "ORBITAL " + root.kind.toUpperCase() + (root.kind === "disk" ? " / 9 STYLES" : "")
        font.family: "IBM Plex Mono"; font.pixelSize: 16; color: "#67C4DE"
    }
    Grid {
        x: 24; y: 54
        columns: root.kind === "memory" ? 2 : root.kind === "battery" ? 4 : 3
        spacing: 12
        Repeater {
            model: root.examples[root.kind]
            Rectangle {
                id: card
                required property var modelData
                width: (root.width - 48 - (parent.columns - 1) * parent.spacing) / parent.columns
                height: root.kind === "disk" ? 148 : 158
                radius: 8; color: "#152638"
                Text {
                    x: 16; y: 12
                    text: card.modelData.label
                    color: "#B8CAD4"; font.family: "IBM Plex Sans"; font.pixelSize: 15
                }
                Loader {
                    id: visual
                    anchors.horizontalCenter: parent.horizontalCenter; y: 40
                    width: 112; height: 102
                    sourceComponent: root.kind === "cpu" ? cpu : root.kind === "memory" ? memory : root.kind === "disk" ? disk : battery
                }
                Component {
                    id: cpu
                    CPU.CpuVisual { cpuPercent: 50; orbitStyle: card.modelData.style; orbitAngle: 32; animationsEnabled: false }
                }
                Component {
                    id: memory
                    Memory.MemoryVisual { ramPercent: 67; swapPercent: 30; meterStyle: card.modelData.style }
                }
                Component {
                    id: disk
                    Disk.DiskVisual {
                        meterStyle: card.modelData.style; usedPercent: 64
                        readBytesPerSecond: 280000000; writeBytesPerSecond: 96000000
                        animationsEnabled: false; surfaceColor: "#152638"
                    }
                }
                Component {
                    id: battery
                    Battery.BatteryVisual {
                        chargePercent: card.modelData.charge; charging: card.modelData.charging
                        alwaysShowPercent: true; animationsEnabled: false
                    }
                }
            }
        }
    }
}
