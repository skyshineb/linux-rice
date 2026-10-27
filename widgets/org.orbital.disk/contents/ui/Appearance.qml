// SPDX-License-Identifier: MIT
import QtQuick

QtObject {
    id: root
    required property var configuration
    required property var theme
    readonly property bool useThemeColors: configuration.colorMode !== 1
    function blend(a, b, amount) {
        return Qt.rgba(a.r + (b.r-a.r)*amount, a.g + (b.g-a.g)*amount, a.b + (b.b-a.b)*amount, 1)
    }
    readonly property color filledColor: useThemeColors ? theme.linkColor : configuration.filledColor
    readonly property color writeColor: useThemeColors ? theme.neutralTextColor : configuration.writeColor
    readonly property color emptyColor: useThemeColors ? blend(theme.backgroundColor, theme.linkColor, .24) : configuration.emptyColor
    readonly property color trackColor: useThemeColors ? blend(theme.backgroundColor, theme.textColor, .35) : configuration.trackColor
    readonly property color textColor: useThemeColors ? theme.textColor : configuration.textColor
    readonly property color surfaceColor: useThemeColors ? theme.backgroundColor : configuration.surfaceColor
    readonly property color warningColor: useThemeColors ? theme.negativeTextColor : configuration.warningColor
}
