import QtQuick 2.15
import "contents/ui"

Rectangle {
    width: 200
    height: 200
    color: "#101D2B"

    Column {
        anchors.centerIn: parent
        spacing: 8
        Repeater {
            model: [0, 50, 100]
            LoadVisual {
                width: 100
                height: 48
                cpuPercent: modelData
                ramPercent: modelData
                animationsEnabled: false
            }
        }
    }
}
