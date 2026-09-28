import QtQuick 2.15
import "contents/ui"

Rectangle {
    width: 300
    height: 280
    color: "#101D2B"

    Column {
        anchors.centerIn: parent
        spacing: 8
        Repeater {
            model: [
                { "height": 44, "percent": 0 },
                { "height": 72, "percent": 50 },
                { "height": 96, "percent": 100 }
            ]
            LoadVisual {
                width: height * 100 / 44
                height: modelData.height
                cpuPercent: modelData.percent
                ramPercent: modelData.percent
                animationsEnabled: false
            }
        }
    }
}
