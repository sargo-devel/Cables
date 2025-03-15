import os
import FreeCADGui

_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "resources/icons")
uiPath = os.path.join(_dir, "resources/ui")
presetsPath = os.path.join(_dir, "resources/presets")
languagePath = os.path.join(_dir, "resources", "translations")


def QT_TRANSLATE_NOOP(context, text):
    return text
