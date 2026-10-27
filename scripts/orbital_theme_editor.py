# SPDX-FileCopyrightText: 2026 Nikolay Skovorodin
# SPDX-License-Identifier: MIT

"""Qt editor. Only explicit Apply/Undo actions touch desktop configuration."""

from collections import OrderedDict
import copy
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET

from PyQt6.QtCore import QObject, QProcess, QThread, QTimer, QUrl, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QGuiApplication, QIcon
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickWindow  # Register the concrete window wrapper for QML roots.
from PyQt6.QtWidgets import QApplication, QColorDialog, QFileDialog

from orbital_themes import (ROOT, COLOR_KEYS, HEX, SCHEME_TYPES, GenerationOptions, Themes,
                            builtin, generation_source, matugen_arguments, matugen_config,
                            palette_from_generation)

ROLE_LABELS = ('Холст', 'Панель', 'Окно', 'Кнопка', 'Выделение', 'Текст', 'Вторичный',
               'Акцент', 'Внимание', 'Ошибка', 'Успех', 'Посещённая ссылка')


class Operation(QThread):
    resultReady = pyqtSignal(object, str)

    def __init__(self, work, parent):
        super().__init__(parent)
        self.work = work

    def run(self):
        try:
            result = self.work()
        except Exception as error:
            self.resultReady.emit(None, str(error))
        else:
            self.resultReady.emit(result, '')


class Editor(QObject):
    settingsChanged = pyqtSignal()
    previewChanged = pyqtSignal()
    stateChanged = pyqtSignal()
    closeReady = pyqtSignal()

    def __init__(self, manager=None, image=None, parent=None):
        super().__init__(parent)
        self.manager = manager or Themes()
        self._temporary = tempfile.TemporaryDirectory(prefix='orbital-editor-')
        self._config = matugen_config(Path(self._temporary.name))
        self._processes = set()
        self._process = None
        self._extract = None
        self._extract_key = None
        self._cache = OrderedDict()
        self._color_cache = OrderedDict()
        self._source_colors = []
        self._image_label = None
        self._revision = 0
        self._accepted = -1
        self._request = None
        self._calculating = False
        self._working = False
        self._worker = None
        self._backup = None
        self._close_after = False
        self._closed = False
        self._error = ''
        self._status = 'Выберите изображение или задайте цвет'
        self._version = ''
        try:
            self._preview = self.manager.load(None)
        except (OSError, ValueError):
            self._preview = builtin('orbital-dark')
        self._settings = {'source_kind': 'image', 'image': '', 'color': self._preview['colors']['cyan'],
                          'mode': self._preview['mode'], **asdict(GenerationOptions()), 'source_choice': 'index'}
        generation = self._preview.get('generation', {})
        if generation:
            try:
                options = GenerationOptions(**generation['options'])
                self._settings.update(asdict(options))
                self._settings['source_choice'] = options.prefer or 'index'
                source = generation['source']
                if source['kind'] == 'color':
                    self._settings.update(source_kind='color', color=source['value'])
                else:
                    sidecar = self.manager.store / 'themes' / f"{self._preview['id']}.wallpaper"
                    if sidecar.exists():
                        self._settings['image'] = sidecar.read_text().strip()
                        self._image_label = source.get('label')
            except (KeyError, TypeError, ValueError, OSError):
                self._status = 'Выберите источник для новой палитры'
        if image is not None:
            self._settings.update(source_kind='image', image=str(Path(image).expanduser().absolute()),
                                  source_color_index=0, source_choice='index', prefer=None)
            self._image_label = None
        self._widget_defaults = {}
        for widget in ('cpu', 'memory', 'battery', 'disk'):
            xml = ROOT / 'widgets' / f'org.orbital.{widget}' / 'contents/config/main.xml'
            entries = ET.parse(xml).findall('.//{*}entry')
            self._widget_defaults[widget] = {'colorMode': 0, **{
                entry.attrib['name']: entry.find('{*}default').text
                for entry in entries if entry.attrib['type'] == 'Color'}}
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._generate)

    @pyqtProperty('QVariantMap', notify=settingsChanged)
    def settings(self):
        return self._settings

    @pyqtProperty(QUrl, notify=settingsChanged)
    def sourceImageUrl(self):
        if self._settings['source_kind'] != 'image' or not self._settings['image'].strip():
            return QUrl()
        try:
            path = Path(self._settings['image']).expanduser().resolve()
            return QUrl.fromLocalFile(str(path)) if path.is_file() else QUrl()
        except (OSError, RuntimeError, ValueError):
            return QUrl()

    @pyqtProperty('QVariantMap', notify=previewChanged)
    def preview(self):
        return self._preview

    @pyqtProperty('QVariantList', notify=previewChanged)
    def swatches(self):
        return [{'role': key, 'label': label, 'color': self._preview['colors'][key]}
                for key, label in zip(COLOR_KEYS, ROLE_LABELS)]

    @pyqtProperty('QVariantList', notify=stateChanged)
    def sourceColors(self):
        return self._source_colors

    @pyqtProperty('QVariantList', constant=True)
    def schemeTypes(self):
        return list(SCHEME_TYPES)

    @pyqtProperty('QVariantMap', constant=True)
    def widgetDefaults(self):
        return self._widget_defaults

    @pyqtProperty(str, notify=stateChanged)
    def status(self):
        return self._status

    @pyqtProperty(str, notify=stateChanged)
    def error(self):
        return self._error

    @pyqtProperty(bool, notify=stateChanged)
    def calculating(self):
        return self._calculating

    @pyqtProperty(bool, notify=stateChanged)
    def working(self):
        return self._working

    @pyqtProperty(bool, notify=stateChanged)
    def canApply(self):
        return self._accepted == self._revision and not self._working and not self._calculating

    @pyqtProperty(bool, notify=stateChanged)
    def canUndo(self):
        return self._backup is not None and not self._working

    @pyqtSlot()
    def start(self):
        if self._settings['source_kind'] == 'color' or self._settings['image']:
            self._invalidate()

    @pyqtSlot(str, 'QVariant')
    def setOption(self, key, value):
        if self._working or key not in self._settings or self._settings[key] == value:
            return
        self._settings[key] = value
        if key == 'source_choice' and value == 'index' and self._settings['source_color_index'] is None:
            self._settings['source_color_index'] = 0
        if key == 'image':
            self._image_label = None
            self._settings.update(source_color_index=0, source_kind='image')
            self._source_colors = []
        if key == 'source_kind' and value == 'color':
            self._source_colors = []
        self.settingsChanged.emit()
        self._invalidate()

    def _invalidate(self):
        self._revision += 1
        if self._process is not None:
            self._process.kill()
            self._process = None
        self._error = ''
        self._status = 'Рассчитываю палитру…'
        self._calculating = True
        self.stateChanged.emit()
        self._timer.start()

    def _source(self):
        kind = self._settings['source_kind']
        source = generation_source(self._settings['image'] if kind == 'image' else self._settings['color'], kind)
        if kind == 'image' and self._image_label:
            source['label'] = self._image_label
        return source

    def _options(self):
        choice = self._settings['source_choice'] if self._settings['source_kind'] == 'image' else 'index'
        return GenerationOptions(
            scheme_type=self._settings['scheme_type'], contrast=self._settings['contrast'],
            lightness_dark=self._settings['lightness_dark'], lightness_light=self._settings['lightness_light'],
            source_color_index=int(self._settings['source_color_index'] or 0) if choice == 'index' else None,
            prefer=None if choice == 'index' else choice)

    def _fail(self, error, revision):
        if revision != self._revision or self._closed:
            return
        self._error = str(error)
        self._accepted = -1
        self._status = 'Превью не обновлено'
        self._calculating = False
        self.stateChanged.emit()

    def _run_process(self, args, success, failure):
        process = QProcess(self)
        self._processes.add(process)
        deadline = QTimer(process)
        deadline.setSingleShot(True)
        completed = False

        def finish(code=0, *_):
            nonlocal completed
            if completed:
                return
            completed = True
            deadline.stop()
            if self._process is process:
                self._process = None
            if self._extract is process:
                self._extract = None
            output = bytes(process.readAllStandardOutput()).decode('utf-8', 'replace')
            error = bytes(process.readAllStandardError()).decode('utf-8', 'replace').strip()
            self._processes.discard(process)
            if not self._closed:
                if code == 0:
                    success(output)
                else:
                    failure(error or process.errorString())
            process.deleteLater()

        def timeout():
            process.kill()

        def process_error(error):
            if error == QProcess.ProcessError.FailedToStart:
                finish(-1)

        process.finished.connect(finish)
        process.errorOccurred.connect(process_error)
        deadline.timeout.connect(timeout)
        process.start(args[0], args[1:])
        deadline.start(30000)
        return process

    def _extract_colors(self, source):
        key = source['hash']
        if self._extract_key != key and self._extract is not None:
            self._extract.kill()
            self._extract = None
        if key in self._color_cache:
            self._extract_key = key
            self._color_cache.move_to_end(key)
            self._source_colors = self._color_cache[key]
            self.stateChanged.emit()
            return
        if self._extract_key == key and self._extract is not None:
            return
        self._extract_key = key

        def extracted(output):
            colors = [line.strip().upper() for line in output.splitlines() if HEX.fullmatch(line.strip())][:5]
            self._color_cache[key] = colors
            while len(self._color_cache) > 32:
                self._color_cache.popitem(last=False)
            if self._extract_key == key and self._settings['source_kind'] == 'image':
                self._source_colors = colors
                self.stateChanged.emit()

        args = matugen_arguments(source, self._settings['mode'], self._options(), self._config, source_colors=True)
        def failed(_):
            if self._extract_key == key:
                self._extract_key = None
        self._extract = self._run_process(args, extracted, failed)

    def _generate(self):
        revision = self._revision
        if self._settings['source_kind'] == 'image' and not self._settings['image'].strip():
            self._calculating = False
            self._accepted = -1
            self._error = ''
            self._status = 'Выберите изображение или задайте цвет'
            self.stateChanged.emit()
            return
        try:
            source = self._source()
            options = self._options()
            mode = self._settings['mode']
            if shutil.which('matugen') is None:
                raise RuntimeError('Установите Matugen: ./scripts/install-matugen.sh')
            if not self._version:
                def version_ready(output):
                    if revision != self._revision:
                        return
                    self._version = output.strip()
                    if not self._version:
                        self._fail('Matugen не сообщил свою версию', revision)
                        return
                    self._generate()
                self._process = self._run_process(['matugen', '--version'], version_ready,
                                                 lambda error: self._fail(error, revision))
                return
            if source['kind'] == 'image':
                self._extract_colors(source)
            key = json.dumps([source, mode, asdict(options), self._version], sort_keys=True)
            request = (source, mode, options)
            if key in self._cache:
                self._cache.move_to_end(key)
                self._accept(self._cache[key], request, revision)
                return
            args = matugen_arguments(source, mode, options, self._config)
        except (ValueError, OSError, RuntimeError, TypeError) as error:
            self._fail(error, revision)
            return

        def generated(output):
            if revision != self._revision:
                return
            try:
                palette = palette_from_generation(output, source, mode, options, self._version)
            except ValueError as error:
                self._fail(error, revision)
                return
            self._cache[key] = palette
            while len(self._cache) > 32:
                self._cache.popitem(last=False)
            self._accept(palette, request, revision)

        self._process = self._run_process(args, generated, lambda error: self._fail(error, revision))

    def _accept(self, palette, request, revision):
        if revision != self._revision or self._closed:
            return
        self._process = None
        self._preview = palette
        self._request = request
        self._accepted = revision
        self._calculating = False
        self._error = ''
        self._status = 'Превью готово · рабочий стол не изменён'
        self.previewChanged.emit()
        self.stateChanged.emit()

    @pyqtSlot()
    def chooseImage(self):
        value, _ = QFileDialog.getOpenFileName(None, 'Выберите изображение', '',
            'Изображения (*.png *.jpg *.jpeg *.webp *.bmp *.avif *.jxl);;Все файлы (*)')
        if value:
            self.setOption('image', value)

    @pyqtSlot()
    def chooseColor(self):
        value = QColorDialog.getColor(QColor(self._settings['color']), None, 'Исходный цвет')
        if value.isValid():
            self.setOption('color', value.name().upper())

    @pyqtSlot(str)
    def copyColor(self, value):
        QGuiApplication.clipboard().setText(value)
        self._status = f'Скопировано {value}'
        self.stateChanged.emit()

    def _operate(self, work, action):
        self._working = True
        self._error = ''
        self._status = 'Применяю тему…' if action == 'apply' else 'Восстанавливаю снимок…'
        self.stateChanged.emit()
        worker = Operation(work, self)
        self._worker = worker

        def result(value, error):
            self._error = error
            if error:
                self._status = 'Операция не выполнена'
            elif action == 'apply':
                self._backup = value
                self._status = 'Тема применена · доступен откат'
            else:
                self._backup = None
                self._status = 'Предыдущая тема восстановлена'

        def finished():
            self._working = False
            self._worker = None
            worker.deleteLater()
            self.stateChanged.emit()
            if self._close_after:
                self.closeReady.emit()

        worker.resultReady.connect(result)
        worker.finished.connect(finished)
        worker.start()

    @pyqtSlot(bool)
    def applyTheme(self, use_wallpaper=False):
        if not self.canApply or self._request is None:
            return
        source, _, _ = self._request
        try:
            if self._source()['hash'] != source['hash']:
                self._invalidate()
                return
        except (OSError, ValueError) as error:
            self._fail(error, self._revision)
            return
        palette = copy.deepcopy(self._preview)
        image = Path(source['value']) if source['kind'] == 'image' else None
        self._operate(lambda: self.manager.apply(palette, image if use_wallpaper else None,
                                                source_image=image), 'apply')

    @pyqtSlot()
    def undo(self):
        if self.canUndo:
            backup = self._backup
            self._operate(lambda: self.manager.restore(backup), 'restore')

    @pyqtSlot(result=bool)
    def requestClose(self):
        if self._working:
            self._close_after = True
            self._status = 'Закрою окно после завершения операции…'
            self.stateChanged.emit()
            return False
        self.shutdown()
        return True

    def shutdown(self):
        if self._working:
            return
        self._closed = True
        self._timer.stop()
        for process in list(self._processes):
            process.kill()
            process.waitForFinished(1000)
        self._temporary.cleanup()


def launch(image=None):
    app = QApplication.instance() or QApplication([sys.argv[0]])
    app.setApplicationName('orbital-theme-editor')
    app.setOrganizationName('Orbital')
    app.setApplicationDisplayName('Палитра Orbital')
    app.setDesktopFileName('org.orbital.ThemeEditor')
    app.setWindowIcon(QIcon.fromTheme('org.orbital.ThemeEditor',
                                     QIcon(str(ROOT / 'assets/icons/org.orbital.ThemeEditor.svg'))))
    editor = Editor(image=image)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('editor', editor)
    engine.load(QUrl.fromLocalFile(str(ROOT / 'ui/theme-editor.qml')))
    if not engine.rootObjects():
        editor.shutdown()
        raise RuntimeError('Could not load the editor; install Qt Quick Controls and Kirigami QML modules')
    editor.closeReady.connect(engine.rootObjects()[0].close)
    QTimer.singleShot(0, editor.start)
    try:
        return app.exec()
    finally:
        editor.shutdown()
        # The event loop has stopped: destroy QML while its controller is still
        # alive, rather than leaving a deferred deletion until Python shutdown.
        del engine
