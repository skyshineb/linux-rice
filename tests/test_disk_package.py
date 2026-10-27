# SPDX-License-Identifier: MIT
"""Exercise KPackage installation in a temporary package root only."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('kpackagetool6'), 'KPackage tool is required')
class DiskPackageTests(unittest.TestCase):
    def test_install_upgrade_and_remove_in_isolated_package_root(self):
        with tempfile.TemporaryDirectory(prefix='orbital-disk-package-') as temporary:
            base = Path(temporary)
            packages = base / 'data/plasma/plasmoids'
            packages.mkdir(parents=True)
            environment = dict(os.environ, XDG_CONFIG_HOME=str(base / 'config'),
                               XDG_DATA_HOME=str(base / 'data'), XDG_CACHE_HOME=str(base / 'cache'),
                               QT_QPA_PLATFORM='offscreen')

            def invoke(*args):
                result = subprocess.run(['kpackagetool6', '--type', 'Plasma/Applet',
                                         '--packageroot', str(packages), *args],
                                        env=environment, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            source = ROOT / 'widgets/org.orbital.disk'
            installed = packages / 'org.orbital.disk'
            invoke('--install', str(source))
            self.assertTrue((installed / 'contents/ui/main.qml').is_file())
            self.assertEqual((installed / 'LICENSE').read_bytes(), (ROOT / 'LICENSE').read_bytes())
            defaults = ET.parse(installed / 'contents/config/main.xml').findall('.//{*}entry')
            self.assertEqual(next(e.find('{*}default').text for e in defaults if e.attrib['name'] == 'meterStyle'), '19')
            invoke('--upgrade', str(source))
            self.assertTrue((installed / 'contents/ui/DiskVisual.qml').is_file())
            invoke('--remove', 'org.orbital.disk')
            self.assertFalse(installed.exists())
