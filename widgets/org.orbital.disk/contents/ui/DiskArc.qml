// SPDX-License-Identifier: MIT
import QtQuick
import QtQuick.Shapes

Shape {
    id: root
    width: 64; height: 64
    property real radius: 25
    property real startAngle: -90
    property real sweepAngle: 360
    property real lineWidth: 3
    property color lineColor: "transparent"
    ShapePath {
        fillColor: "transparent"
        strokeColor: root.sweepAngle > 0 ? root.lineColor : "transparent"
        strokeWidth: root.lineWidth
        capStyle: ShapePath.FlatCap
        PathAngleArc {
            centerX: 32; centerY: 32
            radiusX: root.radius; radiusY: root.radius
            startAngle: root.startAngle
            sweepAngle: root.sweepAngle
        }
    }
}
