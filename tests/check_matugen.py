# SPDX-License-Identifier: MIT
"""Optional real Matugen checks. All generation uses isolated dry-run config."""
from pathlib import Path
import shutil
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from orbital_themes import ROOT, SCHEME_TYPES, GenerationOptions, generate


@unittest.skipIf(shutil.which('matugen') is None, 'Matugen 4.2.0 required')
class MatugenTests(unittest.TestCase):
    def test_every_scheme_type_and_mode_with_hex(self):
        ids = set()
        for scheme in SCHEME_TYPES:
            for mode in ('dark', 'light'):
                with self.subTest(scheme=scheme, mode=mode):
                    palette = generate('#67C4DE', mode, options=GenerationOptions(scheme_type=scheme), kind='color')
                    self.assertEqual(palette['mode'], mode)
                    self.assertEqual(palette['generation']['options']['scheme_type'], scheme)
                    ids.add(palette['id'])
        self.assertEqual(len(ids), len(SCHEME_TYPES) * 2)

    def test_image_source_selection_preferences(self):
        image = ROOT / 'assets/wallpaper/orbital-2560x1440.png'
        ids = set()
        for prefer in (None, 'saturation', 'lightness', 'darkness'):
            palette = generate(image, 'dark', options=GenerationOptions(prefer=prefer))
            self.assertEqual(palette['generation']['source']['kind'], 'image')
            ids.add(palette['id'])
        self.assertEqual(len(ids), 4)

    def test_numeric_limits_return_valid_palettes(self):
        for mode in ('dark', 'light'):
            for contrast in (-1, 1):
                palette = generate('#67C4DE', mode, options=GenerationOptions(contrast=contrast), kind='color')
                self.assertEqual(palette['generation']['options']['contrast'], contrast)
            for lightness in (-1, 1):
                options = GenerationOptions(**{f'lightness_{mode}': lightness})
                palette = generate('#67C4DE', mode, options=options, kind='color')
                self.assertEqual(palette['generation']['options'][f'lightness_{mode}'], lightness)


if __name__ == '__main__':
    unittest.main(verbosity=2)
