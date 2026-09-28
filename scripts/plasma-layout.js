// Apply in a live Plasma 5.27 session using org.kde.PlasmaShell.evaluateScript.
// Keep the existing launcher, pager and task manager, including pinned apps.
var wallpaperRoot = "HOME_PLACEHOLDER/.local/share/wallpapers/Orbital";
var panels = panelIds.map(function (id) { return panelById(id); });
var bottom = panels.filter(function (p) { return p.location === "bottom"; })[0];
if (!bottom) { throw new Error("No existing bottom panel was found"); }
var top = panels.filter(function (p) { return p.location === "top"; })[0];
if (top) {
    top.currentConfigGroup = ["General"];
    if (top.readConfig("OrbitalManaged") !== "true") {
        throw new Error("An unmanaged top panel already exists; restore the snapshot before retrying");
    }
}

var existing = bottom.widgets();
var keep = {"org.kde.plasma.kickoff": true,
            "org.kde.plasma.pager": true,
            "org.kde.plasma.icontasks": true};
for (var i = 0; i < existing.length; ++i) {
    if (!keep[existing[i].type]) { existing[i].remove(); }
}
bottom.location = "bottom";
bottom.hiding = "none";
bottom.height = 54;
bottom.alignment = "left";
bottom.offset = 0;
var width = screenGeometry(bottom.screen).width;
bottom.minimumLength = width;
bottom.maximumLength = width;
bottom.length = width;
bottom.addWidget("org.kde.plasma.panelspacer");
bottom.addWidget("org.kde.plasma.minimizeall");

if (top) {
    // Keep a pre-existing top panel instead of deleting the user's widgets.
    var old = top.widgets();
    for (var j = 0; j < old.length; ++j) { old[j].remove(); }
} else {
    top = new Panel;
}
top.location = "top";
top.hiding = "none";
top.height = 38;
top.alignment = "left";
top.offset = 0;
top.minimumLength = width;
top.maximumLength = width;
top.length = width;
top.currentConfigGroup = ["General"];
top.writeConfig("OrbitalManaged", "true");

function monitor(plugin, title, sensors) {
    var widget = top.addWidget(plugin);
    widget.currentConfigGroup = ["Appearance"];
    widget.writeConfig("chartFace", "org.kde.ksysguard.textonly");
    widget.writeConfig("title", title);
    widget.currentConfigGroup = ["SensorColors"];
    for (var i = 0; i < sensors.length; ++i) {
        widget.writeConfig(sensors[i], i === 0 ? "103,196,222" : "230,185,106");
    }
    return widget;
}
monitor("org.kde.plasma.systemmonitor.cpu", "CPU", ["cpu/all/usage"]);
monitor("org.kde.plasma.systemmonitor.memory", "MEM", ["memory/physical/used"]);
monitor("org.kde.plasma.systemmonitor.net", "NET", ["network/all/download", "network/all/upload"]);
monitor("org.kde.plasma.systemmonitor.diskactivity", "DISK", ["disk/all/write", "disk/all/read"]);
top.addWidget("org.kde.plasma.panelspacer");
var battery = top.addWidget("org.kde.plasma.battery");
battery.currentConfigGroup = ["General"];
battery.writeConfig("showPercentage", true);
top.addWidget("org.kde.plasma.systemtray");
var clock = top.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", false);

var ds = desktops();
for (var d = 0; d < ds.length; ++d) {
    var desktop = ds[d];
    var geo = desktop.screen >= 0 ? screenGeometry(desktop.screen) : screenGeometry(bottom.screen);
    var image = desktop.screen < 0 ? "orbital-2560x1440.png" :
        (geo.width >= 2800 ? "orbital-3000x2000.png" : "orbital-2560x1440.png");
    desktop.wallpaperPlugin = "org.kde.image";
    desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    desktop.writeConfig("Image", wallpaperRoot + "/" + image);
}
print("Orbital panels applied: bottom=" + bottom.id + ", top=" + top.id + ", screen=" + bottom.screen);
