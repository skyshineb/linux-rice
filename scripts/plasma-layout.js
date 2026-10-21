// SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
// SPDX-License-Identifier: MIT

// Apply in a live Plasma 6.6 session using org.kde.PlasmaShell.evaluateScript.
// Preserve the user's launcher, pager and pinned task manager.
var panels = panelIds.map(function (id) { return panelById(id); });
var bottom = panels.filter(function (p) { return p.location === "bottom"; })[0];
if (!bottom) { throw new Error("No existing bottom panel was found"); }
var top = panels.filter(function (p) { return p.location === "top"; })[0];
if (top) {
    top.currentConfigGroup = ["General"];
    if (top.readConfig("OrbitalManaged") !== "true") {
        throw new Error("Refusing to remove an unmanaged top panel");
    }
}

var existing = bottom.widgets();
var savedMaxRpm = null;
var savedOrbitStyle = null;
var savedConstellationReadoutPosition = null;
var cpuSizeKeys = ["indicatorScale", "horizontalPadding", "verticalPadding"];
var cpuSizeRanges = {"indicatorScale": [60, 150], "horizontalPadding": [0, 32], "verticalPadding": [0, 24]};
var savedCpuSize = {};
var savedMeterStyle = null;
var savedMeterScale = null;
var savedShowSwapGauge = null;
var memoryColorKeys = ["filledColor", "emptyColor", "textColor",
                       "chipBodyColor", "chipOutlineColor", "swapColor"];
var savedMemoryColors = {};
var savedAppearance = {};
var appearanceKeys = {
    "org.orbital.cpu": ["colorMode", "filledColor", "emptyColor", "trackColor", "textColor"],
    "org.orbital.memory": ["colorMode"]
};
for (var i = 0; i < existing.length; ++i) {
    var appearanceType = existing[i].type;
    if (appearanceKeys[appearanceType]) {
        existing[i].currentConfigGroup = ["General"];
        savedAppearance[appearanceType] = {};
        for (var appearanceIndex = 0; appearanceIndex < appearanceKeys[appearanceType].length; ++appearanceIndex) {
            var appearanceKey = appearanceKeys[appearanceType][appearanceIndex];
            var appearanceValue = existing[i].readConfig(appearanceKey);
            if (appearanceValue !== undefined && appearanceValue !== null && String(appearanceValue) !== "") {
                savedAppearance[appearanceType][appearanceKey] = appearanceValue;
            }
        }
    }
    if (existing[i].type === "org.orbital.cpu") {
        existing[i].currentConfigGroup = ["General"];
        var rawOrbitStyle = String(existing[i].readConfig("orbitStyle"));
        if (rawOrbitStyle === "0" || rawOrbitStyle === "1" || rawOrbitStyle === "2") {
            savedOrbitStyle = Number(rawOrbitStyle);
        }
        var rawConstellationReadoutPosition = String(existing[i].readConfig("constellationReadoutPosition"));
        if (rawConstellationReadoutPosition === "0" || rawConstellationReadoutPosition === "1") {
            savedConstellationReadoutPosition = Number(rawConstellationReadoutPosition);
        }
        for (var cpuSizeIndex = 0; cpuSizeIndex < cpuSizeKeys.length; ++cpuSizeIndex) {
            var cpuSizeKey = cpuSizeKeys[cpuSizeIndex];
            var rawCpuSize = existing[i].readConfig(cpuSizeKey);
            if (rawCpuSize !== undefined && rawCpuSize !== null && String(rawCpuSize) !== "") {
                var parsedCpuSize = Number(rawCpuSize);
                var cpuSizeRange = cpuSizeRanges[cpuSizeKey];
                if (isFinite(parsedCpuSize)) {
                    savedCpuSize[cpuSizeKey] = Math.round(Math.max(cpuSizeRange[0], Math.min(cpuSizeRange[1], parsedCpuSize)));
                }
            }
        }
        var rawMaxRpm = existing[i].readConfig("maxRpm");
        if (rawMaxRpm !== undefined && rawMaxRpm !== null && String(rawMaxRpm) !== "") {
            var parsedMaxRpm = Number(rawMaxRpm);
            if (isFinite(parsedMaxRpm)) {
                savedMaxRpm = Math.round(Math.max(0, Math.min(120, parsedMaxRpm)));
            }
        }
    } else if (existing[i].type === "org.orbital.memory") {
        existing[i].currentConfigGroup = ["General"];
        var rawMeterStyle = String(existing[i].readConfig("meterStyle"));
        if (rawMeterStyle === "0" || rawMeterStyle === "1") {
            savedMeterStyle = Number(rawMeterStyle);
        }
        var rawMeterScale = existing[i].readConfig("meterScale");
        if (rawMeterScale !== undefined && rawMeterScale !== null && String(rawMeterScale) !== "") {
            var parsedMeterScale = Number(rawMeterScale);
            if (isFinite(parsedMeterScale)) {
                savedMeterScale = Math.round(Math.max(60, Math.min(110, parsedMeterScale)));
            }
        }
        var rawShowSwapGauge = String(existing[i].readConfig("showSwapGauge")).toLowerCase();
        if (rawShowSwapGauge === "true" || rawShowSwapGauge === "1") {
            savedShowSwapGauge = true;
        } else if (rawShowSwapGauge === "false" || rawShowSwapGauge === "0") {
            savedShowSwapGauge = false;
        }
        for (var memoryColorIndex = 0; memoryColorIndex < memoryColorKeys.length; ++memoryColorIndex) {
            var memoryColorKey = memoryColorKeys[memoryColorIndex];
            var savedMemoryColor = existing[i].readConfig(memoryColorKey);
            if (savedMemoryColor !== undefined && savedMemoryColor !== null && String(savedMemoryColor) !== "") {
                savedMemoryColors[memoryColorKey] = savedMemoryColor;
            }
        }
    }
}
var keep = {"org.kde.plasma.kickoff": true,
            "org.kde.plasma.pager": true,
            "org.kde.plasma.icontasks": true};
var kickoff = existing.filter(function (w) { return w.type === "org.kde.plasma.kickoff"; })[0];
if (!kickoff) { throw new Error("No existing Kickoff launcher was found"); }
for (var i = 0; i < existing.length; ++i) {
    if (!keep[existing[i].type]) { existing[i].remove(); }
}
bottom.location = "bottom";
bottom.hiding = "none";
bottom.alignment = "left";
bottom.offset = 0;
var width = screenGeometry(bottom.screen).width;
bottom.minimumLength = width;
bottom.maximumLength = width;
bottom.length = width;

bottom.addWidget("org.kde.plasma.panelspacer");
var cpu = bottom.addWidget("org.orbital.cpu");
var memory = bottom.addWidget("org.orbital.memory");
if (!cpu || cpu.type !== "org.orbital.cpu" || !memory || memory.type !== "org.orbital.memory") {
    throw new Error("An Orbital CPU or Memory widget was not available");
}
var appearanceWidgets = [cpu, memory];
for (var widgetIndex = 0; widgetIndex < appearanceWidgets.length; ++widgetIndex) {
    var appearanceWidget = appearanceWidgets[widgetIndex];
    var appearanceSettings = savedAppearance[appearanceWidget.type] || {};
    appearanceWidget.currentConfigGroup = ["General"];
    for (var appearanceKey in appearanceSettings) {
        appearanceWidget.writeConfig(appearanceKey, appearanceSettings[appearanceKey]);
    }
}
if (savedMaxRpm !== null) {
    cpu.currentConfigGroup = ["General"];
    cpu.writeConfig("maxRpm", savedMaxRpm);
}
if (savedOrbitStyle !== null) {
    cpu.currentConfigGroup = ["General"];
    cpu.writeConfig("orbitStyle", savedOrbitStyle);
}
if (savedConstellationReadoutPosition !== null) {
    cpu.currentConfigGroup = ["General"];
    cpu.writeConfig("constellationReadoutPosition", savedConstellationReadoutPosition);
}
for (var cpuSizeIndex = 0; cpuSizeIndex < cpuSizeKeys.length; ++cpuSizeIndex) {
    var cpuSizeKey = cpuSizeKeys[cpuSizeIndex];
    if (savedCpuSize[cpuSizeKey] !== undefined) {
        cpu.currentConfigGroup = ["General"];
        cpu.writeConfig(cpuSizeKey, savedCpuSize[cpuSizeKey]);
    }
}
if (savedMeterStyle !== null) {
    memory.currentConfigGroup = ["General"];
    memory.writeConfig("meterStyle", savedMeterStyle);
}
if (savedMeterScale !== null) {
    memory.currentConfigGroup = ["General"];
    memory.writeConfig("meterScale", savedMeterScale);
}
if (savedShowSwapGauge !== null) {
    memory.currentConfigGroup = ["General"];
    memory.writeConfig("showSwapGauge", savedShowSwapGauge);
}
for (var memoryColorIndex = 0; memoryColorIndex < memoryColorKeys.length; ++memoryColorIndex) {
    var memoryColorKey = memoryColorKeys[memoryColorIndex];
    if (savedMemoryColors[memoryColorKey] !== undefined) {
        memory.currentConfigGroup = ["General"];
        memory.writeConfig(memoryColorKey, savedMemoryColors[memoryColorKey]);
    }
}
var tray = bottom.addWidget("org.kde.plasma.systemtray");
var clock = bottom.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", false);

// Remove the old monitor widgets and their panel only after the replacement exists.
if (top) { top.remove(); }

// Wallpaper and colors are applied separately by orbital-theme.
print("Orbital single panel applied: bottom=" + bottom.id + ", cpu=" + cpu.id + ", memory=" + memory.id + ", tray=" + tray.id);
