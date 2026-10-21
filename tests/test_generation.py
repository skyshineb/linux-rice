# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import sys
import tempfile
import unittest
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from orbital_themes import (GenerationOptions, generation_source, matugen_arguments, matugen_config,
                            palette_from_generation, scheme_id)
from theme_fixtures import material_output


class GenerationTests(unittest.TestCase):
    def test_options_reject_invalid_ranges_and_ambiguous_selection(self):
        for settings in ({'contrast': float('nan')}, {'contrast': float('inf')}, {'contrast': -1.01},
                         {'lightness_dark': 1.01}, {'lightness_light': -1.01}, {'source_color_index': 5},
                         {'source_color_index': 1.5}, {'source_color_index': True}, {'scheme_type': 'unknown'},
                         {'prefer': 'unknown'}, {'prefer': 'saturation', 'source_color_index': 0}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                GenerationOptions(**settings)
        self.assertEqual(asdict(GenerationOptions(contrast=-0.0)), asdict(GenerationOptions()))

    def test_shared_arguments_keep_isolation_and_select_one_source_strategy(self):
        source = {'kind': 'image', 'value': '/tmp/a picture "quoted".png'}
        options = GenerationOptions(scheme_type='scheme-vibrant', contrast=.25, prefer='saturation', lightness_dark=.1)
        args = matugen_arguments(source, 'dark', options, Path('/tmp/isolated.toml'))
        self.assertIn(source['value'], args)
        self.assertIn('--dry-run', args)
        self.assertIn('--old-json-output', args)
        self.assertNotIn('--source-color-index', args)
        self.assertEqual(args[args.index('--prefer') + 1], 'saturation')
        for flag, value in (('--contrast', '0.25'), ('--type', 'scheme-vibrant'), ('--lightness-dark', '0.1')):
            self.assertEqual(args[args.index(flag) + 1], value)
        color = generation_source('#67c4de', 'color')
        args = matugen_arguments(color, 'light', GenerationOptions(), Path('/tmp/config'))
        self.assertEqual(args[:4], ['matugen', 'color', 'hex', '#67C4DE'])
        self.assertNotIn('--source-color-index', args)

    def test_variants_and_modes_have_distinct_stable_ids(self):
        source = generation_source('#67C4DE', 'color')
        palettes = [palette_from_generation(material_output(), source, mode, options, 'matugen 4.2.0')
                    for mode in ('dark', 'light') for options in (
                        GenerationOptions(), GenerationOptions(contrast=.25),
                        GenerationOptions(scheme_type='scheme-vibrant'), GenerationOptions(lightness_dark=.1))]
        self.assertEqual(len({palette['id'] for palette in palettes}), len(palettes))
        self.assertEqual(len({scheme_id(palette) for palette in palettes}), len(palettes))
        same = palette_from_generation(material_output(), source, 'dark', GenerationOptions(contrast=-0.0), 'matugen 4.2.0')
        self.assertEqual(same, palettes[0])

    def test_source_metadata_does_not_embed_a_transient_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            source_path = Path(temporary) / 'source image.png'
            source_path.write_bytes(b'image fixture')
            source = generation_source(source_path)
            palette = palette_from_generation(material_output(), source, 'dark', GenerationOptions(), 'matugen 4.2.0')
            self.assertNotIn(temporary, json.dumps(palette))
            self.assertEqual(palette['generation']['source']['hash'], source['hash'])
            config = matugen_config(Path(temporary))
            self.assertIn('caching = false', config.read_text())
            self.assertIn('[templates]', config.read_text())

    def test_invalid_hex_and_generator_output_are_reported(self):
        for color in ('#fff', 'blue', '#000000;Name=Bad'):
            with self.assertRaises(ValueError):
                generation_source(color, 'color')
        with self.assertRaisesRegex(ValueError, 'valid JSON'):
            palette_from_generation('not json', generation_source('#67C4DE', 'color'), 'dark', GenerationOptions(), '4.2.0')
