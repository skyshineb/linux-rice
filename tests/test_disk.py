# SPDX-License-Identifier: MIT
"""Disk telemetry rules and actual native QML visuals, without desktop mutation."""
import json
import math
import os
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')

try:
    from PyQt6.QtCore import QUrl, QObject
    from PyQt6.QtQml import QQmlComponent, QQmlEngine
    from PyQt6.QtQuick import QQuickView
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication
    from test_qml import Translations
except ImportError:
    QApplication = None

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'widgets/org.orbital.disk'
UI = PACKAGE / 'contents/ui'
STYLES = [2, 4, 13, 14, 16, 17, 18, 19, 20]


def volume(uuid='root-uuid', path='/', **overrides):
    return {'Accessible': True, 'Ignored': False, 'File Path': path,
            'Device': '/dev/nvme0n1p2', 'Usage': 'File System', 'File System Type': 'ext4',
            'Device Types': ['Block', 'Storage Access', 'Storage Volume'],
            'UUID': uuid, 'Label': 'Linux', 'Description': 'Linux', **overrides}


@unittest.skipIf(QApplication is None, 'PyQt6 is required for disk QML checks')
class DiskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.engine = QQmlEngine()
        self.translations = Translations()
        self.engine.rootContext().setContextObject(self.translations)
        self.warnings = []
        self.views = []
        self.engine.warnings.connect(lambda warnings: self.warnings.extend(w.toString() for w in warnings))

    def tearDown(self):
        for view in self.views:
            view.close()
            view.deleteLater()
        self.app.processEvents()
        self.engine.deleteLater()
        self.app.processEvents()
        self.assertFalse(self.warnings, '\n'.join(self.warnings))

    def create(self, body):
        source = f'import QtQuick\nimport "{UI.as_uri()}" as Disk\n{body}'
        component = QQmlComponent(self.engine)
        component.setData(source.encode(), QUrl.fromLocalFile(str(ROOT / 'tests/disk-test.qml')))
        item = component.create()
        self.assertIsNotNone(item, '\n'.join(e.toString() for e in component.errors()))
        view = QQuickView(self.engine, None)
        view.setContent(QUrl(), component, item)
        view.resize(400, 200)
        view.show()
        self.views.append(view)
        self.app.processEvents()
        return item

    def logic(self, expression):
        source = (UI / 'DiskUtils.js').read_text().replace('.pragma library', '')
        result = self.engine.evaluate(source + '\nJSON.stringify(' + expression + ')')
        self.assertFalse(result.isError(), result.toString())
        return json.loads(result.toString())

    def test_defaults_keep_gallery_ids_and_all_config_properties_exist(self):
        entries = ET.parse(PACKAGE / 'contents/config/main.xml').findall('.//{*}entry')
        defaults = {e.attrib['name']: e.find('{*}default').text for e in entries}
        self.assertEqual(defaults['meterStyle'], '19')
        self.assertEqual(defaults['volumeId'], None)
        self.assertEqual(defaults['colorMode'], '0')
        self.assertEqual(self.logic('styles'), STYLES)
        self.assertEqual(self.logic('[style(0), style(1), style(19), style(20), style(99)]'), [19, 19, 19, 20, 19])
        root = self.create(f'''Item {{
            width: 600; height: 900
            property alias page: loader.item
            Loader {{ id: loader; anchors.fill: parent
                Component.onCompleted: setSource("{(UI / 'configGeneral.qml').as_uri()}", {{discoveryEnabled: false}})
            }}
        }}''')
        page = root.property('page')
        self.assertIsNotNone(page)
        for key in defaults:
            self.assertGreaterEqual(page.metaObject().indexOfProperty('cfg_' + key), 0, key)
        self.assertEqual(page.property('cfg_meterStyle'), 19)
        combo = page.findChild(QObject, 'diskStyleCombo')
        for index, style in enumerate(STYLES):
            combo.setProperty('currentIndex', index)
            combo.activated.emit(index)
            self.app.processEvents()
            self.assertEqual(page.property('cfg_meterStyle'), style)
        page.setProperty('cfg_meterStyle', 99)
        self.app.processEvents()
        self.assertEqual(combo.property('currentIndex'), STYLES.index(19))
        page.setProperty('cfg_volumeId', 'missing-volume')
        self.app.processEvents()
        self.assertEqual(page.property('cfg_volumeId'), 'missing-volume')
        self.assertIn('missing-volume', page.findChild(QObject, 'diskVolumeCombo').property('currentText'))

    def test_nonfinite_readings_zero_and_normalized_transfer_rates(self):
        self.assertEqual(self.logic('[reading(null), reading(undefined), reading(-1), reading(NaN), reading(Infinity), reading(""), reading(true)]'), [None] * 7)
        self.assertEqual(self.logic('[reading(0), reading("0"), reading(1.5)]'), [0, 0, 1.5])
        self.assertEqual(self.logic('[rateLevel(0,400), rateLevel(200000000,400), rateLevel(800000000,400), rateLevel(NaN,400)]'), [0, .5, 1, 0])
        self.assertEqual(self.logic('[fraction(0,6,0), fraction(0,6,1), fraction(5,6,100)]'), [0, .06, 1])
        self.assertEqual(self.logic('[mountLabel("/"), mountLabel("/mnt/data/"), mountLabel("")]'), ['/', 'data', '—'])

    def test_volume_identity_filtering_hotplug_and_root_selection(self):
        devices = {'root': volume(), 'data': volume('data-uuid', '/mnt/data'),
                   'loop': volume('loop', '/snap/example', Ignored=True),
                   'unmounted': volume('gone', '/mnt/gone', Accessible=False),
                   'network': volume('nfs', '/mnt/nfs', Device='host:/share'),
                   'raw': volume('raw', '/raw', **{'File System Type': ''})}
        expression = 'volumes(' + json.dumps(devices) + ')'
        self.assertEqual([v['id'] for v in self.logic(expression)], ['root-uuid', 'data-uuid'])
        self.assertEqual(self.logic('selectedVolume(' + expression + ', "").mountPath'), '/')
        self.assertIsNone(self.logic('selectedVolume(' + expression + ', "missing")'))
        devices['data']['File Path'] = '/media/renamed'
        expression = 'volumes(' + json.dumps(devices) + ')'
        self.assertEqual(self.logic('selectedVolume(' + expression + ', "data-uuid").mountPath'), '/media/renamed')
        devices.pop('data')
        expression = 'volumes(' + json.dumps(devices) + ')'
        self.assertIsNone(self.logic('selectedVolume(' + expression + ', "data-uuid")'))
        fallback = {'label': volume('', '/mnt/label'), 'device': volume('', '/mnt/device', Label='')}
        self.assertEqual({v['id'] for v in self.logic('volumes(' + json.dumps(fallback) + ')')}, {'Linux', 'nvme0n1p2'})
        localized = {'root': volume(Usage='Файловая система', **{'Device Types': ['Раздел диска']})}
        self.assertEqual(self.logic('volumes(' + json.dumps(localized) + ')')[0]['id'], 'root-uuid')

    def test_live_model_can_be_replaced_by_injected_metadata(self):
        model = self.create('Disk.VolumeModel { live: false }')
        model.setProperty('deviceData', {'root': volume()})
        self.app.processEvents()
        values = model.property('volumes').toVariant()
        self.assertEqual(values[0]['sensorPrefix'], 'disk/root-uuid')
        model.setProperty('deviceData', {})
        self.app.processEvents()
        self.assertEqual(model.property('volumes').toVariant(), [])

    def test_all_styles_capacity_extremes_and_io_modes_render(self):
        item = self.create('Disk.DiskVisual { width: 96; height: 96; animationsEnabled: false }')
        previous = None
        for style in STYLES:
            item.setProperty('meterStyle', style)
            self.app.processEvents()
            visual = item.property('visualItem')
            self.assertIsNotNone(visual)
            if previous is not None:
                self.assertIsNot(visual, previous)
            previous = visual
            for percent in (0, 1, 64, 90, 100, float('nan')):
                for read, write in ((0, 0), (280000000, 0), (0, 96000000), (280000000, 96000000)):
                    item.setProperty('usedPercent', percent)
                    item.setProperty('readBytesPerSecond', read)
                    item.setProperty('writeBytesPerSecond', write)
                    self.app.processEvents()
                    self.assertEqual(item.property('capacityReady'), not math.isnan(percent))
                    self.assertTrue(math.isfinite(item.property('usage')))
                    self.assertEqual(item.property('rotationRunning'), False)
            image = self.views[-1].grabWindow()
            self.assertFalse(image.isNull(), f'style {style}')
        item.setProperty('meterStyle', -1)
        self.app.processEvents()
        self.assertEqual(item.property('effectiveStyle'), 19)

    def test_scaling_and_percentage_changes_never_move_panel_slot(self):
        indicator = self.create('Disk.DiskIndicator { width: implicitWidth; height: 56; animationsEnabled: false }')
        self.assertAlmostEqual(indicator.property('indicatorSize'), 44)
        for style in STYLES:
            indicator.setProperty('meterStyle', style)
            for percent in (0, 1, 99.5, 100, float('nan')):
                indicator.setProperty('usedPercent', percent)
                self.app.processEvents()
                self.assertAlmostEqual(indicator.property('implicitWidth'), 48)
        indicator.setProperty('relativeSize', 150)
        indicator.setProperty('verticalPadding', 24)
        indicator.setProperty('horizontalPadding', 32)
        self.app.processEvents()
        self.assertLessEqual(indicator.property('indicatorSize'), 56)
        self.assertGreaterEqual(indicator.property('indicatorSize'), 24)

    def test_rotation_stops_for_idle_hidden_disabled_and_missing_io(self):
        item = self.create('Disk.DiskVisual { width: 64; height: 64; meterStyle: 16; usedPercent: 64; readBytesPerSecond: 0; writeBytesPerSecond: 0 }')
        QTest.qWait(60)
        self.assertEqual(item.property('angle'), 0)
        item.setProperty('readBytesPerSecond', 1000000)
        QTest.qWait(100)
        self.assertGreater(item.property('angle'), 0)
        item.setProperty('animationsEnabled', False)
        angle = item.property('angle')
        QTest.qWait(60)
        self.assertEqual(item.property('angle'), angle)
        self.assertEqual(item.property('readOpacity'), 1)
        item.setProperty('animationsEnabled', True)
        item.setVisible(False)
        self.assertFalse(item.property('rotationRunning'))
        item.setVisible(True)
        item.setProperty('readBytesPerSecond', float('nan'))
        item.setProperty('writeBytesPerSecond', float('nan'))
        self.assertFalse(item.property('rotationRunning'))

    def test_capacity_warning_does_not_recolor_read_write(self):
        item = self.create('Disk.DiskVisual { width: 64; height: 64; animationsEnabled: false; usedPercent: 89 }')
        normal = item.property('filledColor')
        self.assertEqual(item.property('capacityColor'), normal)
        item.setProperty('usedPercent', 90)
        self.assertEqual(item.property('capacityColor'), item.property('warningColor'))
        self.assertEqual(item.property('filledColor'), normal)

    def test_disk_follows_theme_changes_and_preserves_custom_colors(self):
        from test_qml import QmlTests
        themed = QmlTests.appearance(self, 'disk', mode=0)
        self.assertEqual(themed.property('activeColor').name(), '#006d87')
        themed.setProperty('accent', '#39B7E9')
        self.app.processEvents()
        self.assertEqual(themed.property('activeColor').name(), '#39b7e9')
        custom = QmlTests.appearance(self, 'disk', mode=1, custom=True)
        custom.setProperty('accent', '#006D87')
        self.app.processEvents()
        self.assertEqual(custom.property('activeColor').name(), '#ff00aa')

    def test_panel_recreation_preserves_every_disk_setting_and_order(self):
        entries = ET.parse(PACKAGE / 'contents/config/main.xml').findall('.//{*}entry')
        settings = {}
        for entry in entries:
            value = entry.find('{*}default').text
            settings[entry.attrib['name']] = int(value) if entry.attrib['type'] == 'Int' else value == 'true' if entry.attrib['type'] == 'Bool' else value or ''
        settings.update(meterStyle=18, volumeId='data-uuid', meterScale=125, horizontalPadding=12,
                        verticalPadding=7, ioScaleMBps=1200, animationsEnabled=False, colorMode=1,
                        filledColor='#123456', writeColor='#f0ba78')
        setup = '''
var created = [], identifier = 1;
function widget(type, config) {
    return {id: identifier++, type: type, config: config || {}, currentConfigGroup: [],
        readConfig: function(key) { return this.config[key]; },
        writeConfig: function(key, value) { this.config[key] = value; },
        remove: function() { this.removed = true; }};
}
var previous = [widget("org.kde.plasma.kickoff"), widget("org.kde.plasma.pager"),
    widget("org.kde.plasma.icontasks"), widget("org.orbital.cpu", {orbitStyle: 2}),
    widget("org.orbital.memory", {meterStyle: 1}), widget("org.orbital.disk", SETTINGS)];
var bottom = {id: 1, location: "bottom", screen: 0,
    widgets: function() { return previous; },
    addWidget: function(type) { var result = widget(type); created.push(result); return result; }};
var panelIds = [1];
function panelById(id) { return bottom; }
function screenGeometry(screen) { return {width: 1920}; }
function print(message) {}
'''.replace('SETTINGS', json.dumps(settings))
        script = (ROOT / 'scripts/plasma-layout.js').read_text()
        result = self.engine.evaluate(setup + script + '\nJSON.stringify(created.map(function(w) {return {type:w.type, config:w.config};}))')
        self.assertFalse(result.isError(), result.toString())
        created = json.loads(result.toString())
        self.assertEqual([w['type'] for w in created], [
            'org.kde.plasma.panelspacer', 'org.orbital.cpu', 'org.orbital.memory',
            'org.orbital.disk', 'org.kde.plasma.systemtray', 'org.kde.plasma.digitalclock'])
        self.assertEqual(created[3]['config'], settings)
        self.assertEqual(created[1]['config']['orbitStyle'], 2)
        self.assertEqual(created[2]['config']['meterStyle'], 1)


if __name__ == '__main__':
    unittest.main()
