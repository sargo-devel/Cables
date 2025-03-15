import os
import FreeCAD as App

translate=App.Qt.translate
QT_TRANSLATE_NOOP=App.Qt.QT_TRANSLATE_NOOP

_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "resources/icons")
uiPath = os.path.join(_dir, "resources/ui")
presetsPath = os.path.join(_dir, "resources/presets")
languagePath = os.path.join(_dir, "resources", "translations")
