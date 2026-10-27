// SPDX-License-Identifier: MIT
.pragma library

// Persist gallery IDs, never ComboBox indexes.
var styles = [2, 4, 13, 14, 16, 17, 18, 19, 20]
var styleNames = ["02 · Двойной контур", "04 · Спираль", "13 · Архив",
                  "14 · Пакеты", "16 · Радар", "17 · Турбина", "18 · Соты",
                  "19 · Терминал", "20 · Три канала"]

function style(value) { return styles.indexOf(value) >= 0 ? value : 19 }
function reading(value) {
    return value !== null && value !== undefined && typeof value !== "boolean"
        && String(value).trim() !== "" && isFinite(Number(value)) && Number(value) >= 0
        ? Number(value) : NaN
}
function clamp(value, low, high, fallback) {
    return isFinite(value) ? Math.max(low, Math.min(high, value)) : fallback
}
function fraction(index, count, percent) {
    return clamp(percent / 100 * count - index, 0, 1, 0)
}
function rateLevel(value, scale) {
    return clamp(reading(value) / (clamp(scale, 1, 100000, 400) * 1000000), 0, 1, 0)
}
function mountLabel(path) {
    if (path === "/") return "/"
    return String(path || "").replace(/\/+$/, "").split("/").pop() || "—"
}

function volumes(deviceData) {
    var result = []
    for (var udi in deviceData) {
        var data = deviceData[udi]
        if (!data || data.Accessible !== true || data.Ignored === true
                || !data["File Path"] || !String(data.Device || "").startsWith("/dev/")
                || !data["File System Type"]) continue
        // Filesystem type is machine-readable; Usage/Device Types can be localized.
        // Match ksystemstats VolumeObject::idHelper, including its non-UUID cases.
        var id = String(data.UUID || data.Label || String(data.Device).split("/").pop())
        result.push({ id: id, udi: udi, mountPath: String(data["File Path"]),
                      name: String(data.Label || data.Description || data.Device),
                      device: String(data.Device), sensorPrefix: "disk/" + id })
    }
    result.sort(function(a, b) {
        if (a.mountPath === "/" && b.mountPath !== "/") return -1
        if (b.mountPath === "/" && a.mountPath !== "/") return 1
        return a.mountPath.localeCompare(b.mountPath)
    })
    var seen = Object.create(null)
    return result.filter(function(volume) {
        if (seen[volume.id]) return false
        seen[volume.id] = true
        return true
    })
}
function selectedVolume(list, id) {
    for (var i = 0; i < list.length; ++i) {
        if (id ? list[i].id === id : list[i].mountPath === "/") return list[i]
    }
    return null
}

function point(radius, angle, cx, cy) {
    var radians = angle * Math.PI / 180
    return Qt.point((cx === undefined ? 32 : cx) + radius * Math.cos(radians),
                    (cy === undefined ? 32 : cy) + radius * Math.sin(radians))
}
function polygon(points) {
    return points.map(function(p, i) { return (i ? "L" : "M") + p.x + " " + p.y }).join(" ") + " Z"
}
function hexagon(x, y) {
    var points = []
    for (var i = 0; i < 6; ++i) points.push(point(5.5, -30 + i * 60, x, y))
    return polygon(points)
}
function honeycomb() {
    var cells = []
    for (var r = -2; r <= 2; ++r) for (var q = -2; q <= 2; ++q) {
        if (Math.abs(q + r) <= 2) cells.push({x: 32 + 10.7 * (q + r / 2), y: 26 + r * 9.3})
    }
    return cells.sort(function(a, b) { return b.y - a.y || a.x - b.x })
}
// A partial polyline for the spiral; lengths rather than opacity encode capacity.
var spiral = [[31, 25], [37, 25], [37, 34], [24, 34], [24, 18], [45, 18],
              [45, 42], [16, 42], [16, 10], [53, 10], [53, 49], [9, 49]]
function spiralPath(percent) {
    var length = 0
    for (var i = 1; i < spiral.length; ++i)
        length += Math.abs(spiral[i][0] - spiral[i-1][0]) + Math.abs(spiral[i][1] - spiral[i-1][1])
    var remaining = length * clamp(percent, 0, 100, 0) / 100
    var path = "M" + spiral[0][0] + " " + spiral[0][1]
    for (var j = 1; j < spiral.length && remaining > 0; ++j) {
        var a = spiral[j-1], b = spiral[j]
        var segment = Math.abs(b[0]-a[0]) + Math.abs(b[1]-a[1])
        var fraction = Math.min(1, remaining / segment)
        path += " L" + (a[0] + (b[0]-a[0])*fraction) + " " + (a[1] + (b[1]-a[1])*fraction)
        remaining -= segment
    }
    return path
}
