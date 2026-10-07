// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: LGPL-2.0-or-later

import QtQuick
import "contents/ui"

Rectangle {
    width: 532
    height: 112
    color: "#152638"

    Row {
        anchors.centerIn: parent
        spacing: 12

        BatteryVisual {
            width: 72
            height: 72
            chargePercent: 47
        }
        BatteryVisual {
            width: 72
            height: 72
            chargePercent: 47
            hovered: true
        }
        BatteryVisual {
            width: 72
            height: 72
            chargePercent: 47
            charging: true
            alwaysShowPercent: true
        }
        BatteryVisual {
            width: 72
            height: 72
            chargePercent: 20
        }
        BatteryVisual {
            width: 72
            height: 72
            chargePercent: 99
            charging: true
            alwaysShowPercent: true
        }
        BatteryVisual {
            width: 72
            height: 72
            chargePercent: 100
        }
    }
}
