#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render native QML documentation previews without applying a desktop theme."""

import argparse
import os
from pathlib import Path
import shutil
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wallpaper', type=Path,
                        default=Path('/usr/share/wallpapers/ScarletTree/contents/images/5120x2880.png'))
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'docs/images')
    args = parser.parse_args()
    if not args.wallpaper.is_file():
        parser.error('Scarlet Tree is not installed. Supply its image with --wallpaper PATH; see THIRD_PARTY.md.')
    os.environ['PATH'] = str(Path.home() / '.local/bin') + os.pathsep + os.environ.get('PATH', '')
    if not shutil.which('matugen'):
        parser.error('Matugen 4.2.0 is required for the real palette preview.')
    with tempfile.TemporaryDirectory(prefix='orbital-docs-') as temporary:
        base = Path(temporary)
        os.environ.update(QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                          QT_QUICK_CONTROLS_STYLE='Fusion', QT_SCALE_FACTOR='1',
                          QT_NO_XDG_DESKTOP_PORTAL='1', QT_ACCESSIBILITY='0',
                          XDG_CONFIG_HOME=str(base / 'config'), XDG_DATA_HOME=str(base / 'data'),
                          XDG_CACHE_HOME=str(base / 'cache'))
        from PyQt6.QtCore import QUrl
        from PyQt6.QtQml import QQmlApplicationEngine
        from PyQt6.QtQuick import QQuickView, QQuickWindow
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QApplication
        from orbital_theme_editor import Editor
        from orbital_themes import Themes

        app = QApplication([])
        args.output_dir.mkdir(parents=True, exist_ok=True)
        warnings = []

        def save(window, name):
            QTest.qWait(150)
            image = window.grabWindow()
            if image.isNull() or not image.save(str(args.output_dir / name)):
                raise RuntimeError(f'Could not capture {name}')
            print(f'{name}: {image.width()}×{image.height()}')

        for kind in ('cpu', 'memory', 'disk', 'battery'):
            view = QQuickView()
            view.engine().warnings.connect(lambda values: warnings.extend(value.toString() for value in values))
            view.setInitialProperties({'kind': kind})
            view.setSource(QUrl.fromLocalFile(str(ROOT / 'docs/WidgetPreview.qml')))
            if view.status() == QQuickView.Status.Error:
                raise RuntimeError('\n'.join(error.toString() for error in view.errors()))
            view.show()
            save(view, f'{kind}-overview.png')
            view.close()
            del view
            app.processEvents()

        manager = Themes(base / 'home', config_root=base / 'config', data_root=base / 'data')
        editor = Editor(manager, args.wallpaper)
        engine = QQmlApplicationEngine()
        engine.warnings.connect(lambda values: warnings.extend(value.toString() for value in values))
        engine.rootContext().setContextProperty('editor', editor)
        engine.load(QUrl.fromLocalFile(str(ROOT / 'ui/theme-editor.qml')))
        if not engine.rootObjects():
            raise RuntimeError('The palette editor could not load.')
        window = engine.rootObjects()[0]
        try:
            window.resize(1000, 720)
            for key, value in (('mode', 'light'), ('scheme_type', 'scheme-vibrant'),
                               ('contrast', .25), ('source_choice', 'saturation')):
                editor.setOption(key, value)
            editor.start()
            deadline = time.monotonic() + 45
            while not editor.canApply and time.monotonic() < deadline:
                QTest.qWait(25)
                if editor.error:
                    raise RuntimeError(editor.error)
            if not editor.canApply:
                raise RuntimeError('Timed out waiting for the real Matugen preview.')
            # Include the asynchronous source-color extraction and thumbnail.
            QTest.qWait(500)
            save(window, 'theme-editor.png')
            if manager.store.exists():
                raise RuntimeError('Preview generation unexpectedly wrote theme state.')
        finally:
            window.close()
            editor.shutdown()
            del engine
            app.processEvents()
        if warnings:
            raise RuntimeError('\n'.join(warnings))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
