import QtQuick
import "contents/ui"

Rectangle {
    width: 450
    height: 700
    color: "#101D2B"

    Column {
        anchors.centerIn: parent
        spacing: 8

        Row {
            spacing: 20
            Text {
                width: 200
                text: "RAM / Swap"
                color: "#799BA9"
                font.family: "IBM Plex Mono"
            }
            Text {
                width: 80
                text: "Fan"
                color: "#E9F6F8"
                font.family: "IBM Plex Mono"
            }
            Text {
                text: "Silicon"
                color: "#E9F6F8"
                font.family: "IBM Plex Mono"
            }
        }

        Repeater {
            model: [
                { "label": "0% / 0%", "percent": 0, "swap": 0, "size": 44 },
                { "label": "67% / 1%", "percent": 67, "swap": 1, "size": 44 },
                { "label": "67% / 50%", "percent": 67, "swap": 50, "size": 44 },
                { "label": "100% / 100%", "percent": 100, "swap": 100, "size": 44 },
                { "label": "Swap disabled", "percent": 67, "swap": 0, "size": 44 },
                { "label": "Swap unavailable", "percent": 67, "swap": -1, "size": 44 },
                { "label": "RAM unavailable / 50%", "percent": -1, "swap": 50, "size": 44 },
                { "label": "Both unavailable", "percent": -1, "swap": -1, "size": 44 },
                { "label": "Swap gauge off", "percent": 67, "swap": 50, "showSwap": false, "size": 44 },
                { "label": "67% / 50% small", "percent": 67, "swap": 50, "size": 24 },
                { "label": "67% / 50% large", "percent": 67, "swap": 50, "size": 72 }
            ]

            Row {
                spacing: 20
                Text {
                    width: 200
                    height: modelData.size
                    verticalAlignment: Text.AlignVCenter
                    text: modelData.label
                    color: "#799BA9"
                    font.family: "IBM Plex Mono"
                    font.pixelSize: 10
                }
                Item {
                    width: 80
                    height: modelData.size
                    MemoryVisual {
                        anchors.centerIn: parent
                        width: modelData.size
                        height: modelData.size
                        ramPercent: modelData.percent < 0 ? NaN : modelData.percent
                        swapPercent: modelData.swap < 0 ? NaN : modelData.swap
                        showSwapGauge: modelData.showSwap !== false
                        meterStyle: 0
                    }
                }
                Item {
                    width: 80
                    height: modelData.size
                    MemoryVisual {
                        anchors.centerIn: parent
                        width: modelData.size
                        height: modelData.size
                        ramPercent: modelData.percent < 0 ? NaN : modelData.percent
                        meterStyle: 1
                    }
                }
            }
        }
    }
}
