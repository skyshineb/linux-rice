// Apply in a live Plasma 5.27 session using org.kde.PlasmaShell.evaluateScript.
// Preserve the user's launcher, pager and pinned task manager.
var wallpaperRoot = "HOME_PLACEHOLDER/.local/share/wallpapers/Orbital";
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
var keep = {"org.kde.plasma.kickoff": true,
            "org.kde.plasma.pager": true,
            "org.kde.plasma.icontasks": true};
for (var i = 0; i < existing.length; ++i) {
    if (!keep[existing[i].type]) { existing[i].remove(); }
}
bottom.location = "bottom";
bottom.hiding = "none";
bottom.height = 70;
bottom.alignment = "left";
bottom.offset = 0;
var width = screenGeometry(bottom.screen).width;
bottom.minimumLength = width;
bottom.maximumLength = width;
bottom.length = width;

bottom.addWidget("org.kde.plasma.panelspacer");
var load = bottom.addWidget("org.orbital.load");
if (!load || load.type !== "org.orbital.load") {
    throw new Error("Orbital Load widget was not available");
}
var tray = bottom.addWidget("org.kde.plasma.systemtray");
var clock = bottom.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", false);

// Remove the old monitor widgets and their panel only after the replacement exists.
if (top) { top.remove(); }

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
print("Orbital single panel applied: bottom=" + bottom.id + ", load=" + load.id + ", tray=" + tray.id);
