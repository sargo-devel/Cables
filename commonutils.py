import os
import FreeCADGui

_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "Resources/icons")
uiPath = os.path.join(_dir, "Resources/ui")
presetsPath = os.path.join(_dir, "Resources/presets")
languagePath = os.path.join(_dir, "Resources", "translations")


def QT_TRANSLATE_NOOP(context, text):
    return text
