// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

import QtQuick

QtObject {
    id: root
    required property var configuration
    required property var theme
    // Configuration dialogs preview the palette without persisting migration.
    property bool migrate: true
    readonly property var defaults: ({"filledColor": "#70D4E8", "emptyColor": "#315262", "textColor": "#E9F6F8", "chipBodyColor": "#183646", "chipOutlineColor": "#799BA9", "swapColor": "#E6B96A"})
    readonly property bool hasCustomColors: {
        for (const key in defaults) {
            if (!Qt.colorEqual(configuration[key], defaults[key])) return true
        }
        return false
    }
    readonly property bool useThemeColors: configuration.colorMode === 0
        || (configuration.colorMode !== 1 && !hasCustomColors)

    Component.onCompleted: {
        if (migrate && configuration.colorMode !== 0 && configuration.colorMode !== 1) {
            configuration.colorMode = hasCustomColors ? 1 : 0
        }
    }

    function blend(first, second, amount) {
        return Qt.rgba(first.r + (second.r - first.r) * amount,
                       first.g + (second.g - first.g) * amount,
                       first.b + (second.b - first.b) * amount, 1)
    }

    function alpha(color, amount) {
        return Qt.rgba(color.r, color.g, color.b, amount)
    }

    readonly property color filledColor: useThemeColors
        ? root.theme.linkColor : configuration.filledColor
    readonly property color emptyColor: useThemeColors
        ? blend(root.theme.backgroundColor, root.theme.linkColor, 0.24) : configuration.emptyColor
    readonly property color textColor: useThemeColors
        ? root.theme.textColor : configuration.textColor
    readonly property color chipBodyColor: useThemeColors
        ? blend(root.theme.backgroundColor, root.theme.linkColor, 0.13) : configuration.chipBodyColor
    readonly property color chipOutlineColor: useThemeColors
        ? blend(root.theme.textColor, root.theme.linkColor, 0.35) : configuration.chipOutlineColor
    readonly property color swapColor: useThemeColors
        ? root.theme.neutralTextColor : configuration.swapColor
}
