// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Shapes

Shape {
    id: root
    width: 64; height: 64
    property string pathData: ""
    property color lineColor: "transparent"
    property color shapeColor: "transparent"
    property real lineWidth: 1
    ShapePath {
        fillColor: root.shapeColor
        strokeColor: root.lineColor
        strokeWidth: root.lineWidth
        capStyle: ShapePath.RoundCap
        joinStyle: ShapePath.RoundJoin
        PathSvg { path: root.pathData }
    }
}
