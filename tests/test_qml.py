# SPDX-License-Identifier: MIT
"""Offscreen integration checks for actual QML palette bindings and migration."""

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ.setdefault('QT_QUICK_BACKEND', 'software')

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

try:
    from PyQt6.QtCore import QUrl, QObject, pyqtSlot
    from PyQt6.QtQml import QQmlComponent, QQmlEngine
    from PyQt6.QtQuick import QQuickView
    from PyQt6.QtWidgets import QApplication
except ImportError:
    QApplication = None

ROOT = Path(__file__).resolve().parents[1]

if QApplication is not None:
    class Translations(QObject):
        @pyqtSlot(str, result=str)
        def i18n(self, value):
            return value

        @pyqtSlot(str, str, result=str)
        @pyqtSlot(str, str, str, result=str)
        def i18nc(self, context, value, argument=None):
            return value if argument is None else value.replace('%1', argument)


@unittest.skipIf(QApplication is None, 'PyQt6 is required for offscreen QML validation')
class QmlTests(unittest.TestCase):
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
        self.assertFalse(self.warnings, '\n'.join(self.warnings))
        for view in self.views:
            view.close()
            view.deleteLater()
        self.app.processEvents()
        self.engine.deleteLater()
        self.app.processEvents()

    def create(self, source):
        component = QQmlComponent(self.engine)
        component.setData(source.encode(), QUrl.fromLocalFile(str(ROOT / 'tests/test.qml')))
        result = component.create()
        self.assertIsNotNone(result, '\n'.join(error.toString() for error in component.errors()))
        view = QQuickView(self.engine, None)
        view.setContent(QUrl(), component, result)
        view.resize(600, 120)
        view.show()
        self.views.append(view)
        self.app.processEvents()
        return result

    def appearance(self, widget, mode=-1, custom=False):
        path = ROOT / 'widgets' / f'org.orbital.{widget}' / 'contents'
        entries = ET.parse(path / 'config/main.xml').findall('.//{*}entry')
        colors = {e.attrib['name']: e.find('{*}default').text for e in entries if e.attrib['type'] == 'Color'}
        if custom:
            colors['filledColor'] = '#FF00AA'
        properties = '\n'.join(f'property color {key}: "{value}"' for key, value in colors.items())
        return self.create(f'''
import QtQuick
import org.kde.kirigami as Kirigami
import "{(path / 'ui').as_uri()}" as Widget
Item {{
    id: root
    property color accent: "#006D87"
    property color surface: "#F1F5F8"
    property color foreground: "#172D3D"
    property alias mode: config.colorMode
    property alias activeColor: appearance.filledColor
    Kirigami.Theme.inherit: false
    Kirigami.Theme.linkColor: accent
    Kirigami.Theme.backgroundColor: surface
    Kirigami.Theme.textColor: foreground
    QtObject {{ id: config; property int colorMode: {mode}; {properties} }}
    Widget.Appearance {{ id: appearance; configuration: config; theme: root.Kirigami.Theme }}
}}
''')

    def test_fresh_widgets_follow_palette_changes_without_recreation(self):
        for widget in ('cpu', 'memory', 'battery'):
            with self.subTest(widget=widget):
                root = self.appearance(widget)
                self.assertEqual(root.property('mode'), 0)
                self.assertEqual(root.property('activeColor').name(), '#006d87')
                root.setProperty('accent', '#67C4DE')
                root.setProperty('surface', '#101D2B')
                self.app.processEvents()
                self.assertEqual(root.property('activeColor').name(), '#67c4de')

    def test_legacy_custom_and_explicit_custom_colors_survive(self):
        for widget in ('cpu', 'memory', 'battery'):
            with self.subTest(widget=widget):
                root = self.appearance(widget, custom=True)
                self.assertEqual(root.property('mode'), 1)
                root.setProperty('accent', '#123456')
                self.app.processEvents()
                self.assertEqual(root.property('activeColor').name(), '#ff00aa')
                fixed = self.appearance(widget, mode=1)
                self.assertEqual(fixed.property('mode'), 1)
                self.assertNotEqual(fixed.property('activeColor').name(), '#006d87')

    def test_all_visual_variants_accept_live_colors(self):
        cpu = (ROOT / 'widgets/org.orbital.cpu/contents/ui').as_uri()
        memory = (ROOT / 'widgets/org.orbital.memory/contents/ui').as_uri()
        battery = (ROOT / 'widgets/org.orbital.battery/contents/ui').as_uri()
        self.create(f'''
import QtQuick
import "{cpu}" as CPU
import "{memory}" as Memory
import "{battery}" as Battery
Item {{
    width: 600; height: 120
    property color accent: "#006D87"
    CPU.CpuIndicator {{ width: 60; height: 48; orbitStyle: 0; cpuPercent: 50; filledColor: parent.accent; animationsEnabled: false }}
    CPU.CpuIndicator {{ width: 60; height: 48; orbitStyle: 1; cpuPercent: 50; filledColor: parent.accent; animationsEnabled: false }}
    CPU.CpuIndicator {{ width: 60; height: 48; orbitStyle: 2; cpuPercent: 50; filledColor: parent.accent; animationsEnabled: false }}
    Memory.MemoryVisual {{ width: 48; height: 44; meterStyle: 0; ramPercent: 50; swapPercent: 10; filledColor: parent.accent }}
    Memory.MemoryVisual {{ width: 48; height: 44; meterStyle: 1; ramPercent: 50; filledColor: parent.accent }}
    Battery.BatteryVisual {{ width: 44; height: 44; chargePercent: 50; charging: true; filledColor: parent.accent; animationsEnabled: false }}
    Battery.BatteryVisual {{ width: 44; height: 44; chargePercent: 15; filledColor: parent.accent; animationsEnabled: false }}
}}
''')

    def test_configuration_pages_load(self):
        for widget in ('cpu', 'memory', 'battery'):
            with self.subTest(widget=widget):
                source = (ROOT / 'widgets' / f'org.orbital.{widget}' / 'contents/ui/configGeneral.qml').as_uri()
                root = self.create(f'''
import QtQuick
Item {{
    width: 600; height: 120
    property alias configuration: loader.item
    Loader {{ id: loader; anchors.fill: parent; source: "{source}" }}
}}
''')
                configuration = root.property('configuration')
                self.assertIsNotNone(configuration)
                configuration.setProperty('cfg_colorMode', 0)
                self.app.processEvents()


if __name__ == '__main__':
    unittest.main()
