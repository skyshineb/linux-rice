# SPDX-License-Identifier: MIT
import json


def material_output():
    values = {'surface': '#101418', 'on_surface': '#e0e3e8', 'on_surface_variant': '#c2c7cf',
              'primary': '#98ccf9', 'primary_container': '#094b71', 'error': '#ffb4ab',
              'tertiary': '#d1bfe7', 'surface_container': '#1c2024', 'surface_container_high': '#262a2e'}
    return json.dumps({'colors': {role: {'dark': color, 'light': color} for role, color in values.items()}})
