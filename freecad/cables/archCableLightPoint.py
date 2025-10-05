"""ArchCableLightPoint
"""

import os
import FreeCAD
import Part
from freecad.cables import archCableBaseElement
from freecad.cables import iconPath
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP


CLASS_CABLELIGHTPOINT_ICON = os.path.join(iconPath,
                                          "classArchCableLightPoint.svg")


class ArchCableLightPoint(archCableBaseElement.BaseElement):
    """The ArchCableLightPoint object
    """
    def __init__(self, obj):
        eltype = "CableLightPoint"
        archCableBaseElement.BaseElement.__init__(self, obj, eltype=eltype)
        self.setProperties(obj)
        from ArchIFC import IfcTypes
        if "Cable Fitting" in IfcTypes:
            obj.IfcType = "Cable Fitting"
            if hasattr(obj, "PredefinedType"):
                obj.PredefinedType = "TRANSITION"
        else:
            # IFC2x3 does not know a Cable Fitting
            obj.IfcType = "Building Element Proxy"
        obj.addExtension('Part::AttachExtensionPython')

    def setProperties(self, obj):
        pl = obj.PropertiesList
        if "Diameter" not in pl:
            obj.addProperty("App::PropertyLength", "Diameter",
                            "CableLightPoint",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The diameter of the light " +
                                "point fitting"))
        if "Thickness" not in pl:
            obj.addProperty("App::PropertyLength", "Thickness",
                            "CableLightPoint",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The wall thickness of the " +
                                "light point fitting"))
        if "Height" not in pl:
            obj.addProperty("App::PropertyLength", "Height", "CableLightPoint",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The height of the light " +
                                "point fitting"))
        if "Terminals" in pl:
            obj.removeProperty("Terminals")
        if "NumberOfTerminals" in pl:
            obj.removeProperty("NumberOfTerminals")
        if "NumberOfSuppLines" in pl:
            obj.setPropertyStatus("NumberOfSuppLines", "Hidden")
        if "Preset" in pl:
            obj.setPropertyStatus("Preset", "Hidden")
        self.Type = "Component"

    def onDocumentRestored(self, obj):
        eltype = "CableLightPoint"
        archCableBaseElement.BaseElement.onDocumentRestored(self, obj, eltype)
        self.setProperties(obj)

    def onChanged(self, obj, prop):
        archCableBaseElement.BaseElement.onChanged(self, obj, prop)

    def execute(self, obj):
        archCableBaseElement.BaseElement.execute(self, obj)
        pl = obj.Placement
        shapes = []
        if not hasattr(obj, "ExtShape") or obj.ExtShape.isNull():
            shapes.append(self.makeBox(obj))
            sh = Part.makeCompound(shapes)
            if obj.Additions or obj.Subtractions:
                sh = self.processSubShapes(obj, sh, pl)
            obj.Shape = sh
            # obj.Placement = pl

    def makeSupportLines(self, obj):
        z = 2
        s1 = archCableBaseElement.BaseElement.makeSupportLines(self, obj)
        s2 = archCableBaseElement.BaseElement.makeSupportLines(self, obj)
        s1.Placement.Base.z = z
        s2.Placement.Base.z = -obj.Height.Value-z
        s = Part.Shape(s1.Edges + s2.Edges)
        return s

    def makeBox(self, obj):
        vc = FreeCAD.Vector(0, 0, 0)
        vn = FreeCAD.Vector(0, 0, -1)
        cyl1 = Part.makeCylinder(obj.Diameter/2, obj.Height, vc, vn)
        cyl2 = Part.makeCylinder(obj.Diameter/2-obj.Thickness, obj.Height,
                                 vc, vn)
        box = cyl1.cut(cyl2)
        return box


class ViewProviderCableLightPoint(
     archCableBaseElement.ViewProviderBaseElement):
    """A View Provider for the ArchCableBox object
    """
    def __init__(self, vobj):
        archCableBaseElement.ViewProviderBaseElement.__init__(self, vobj)

    def getIcon(self):
        return CLASS_CABLELIGHTPOINT_ICON


def makeCableLightPoint(baseobj=None, diameter=0, thickness=0, height=0,
                        placement=None, name=None):
    """creates a cable light point object from the given base object
    or from scratch"""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No active document. Aborting") + "\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                           "CableLightPoint")
    obj.Label = name if name else translate("Cables", "CableLightPoint")
    ArchCableLightPoint(obj)
    if FreeCAD.GuiUp:
        ViewProviderCableLightPoint(obj.ViewObject)
        if baseobj:
            baseobj.ViewObject.hide()
    if baseobj:
        obj.Base = baseobj
    else:
        obj.Diameter = diameter if diameter else 20
        obj.Thickness = thickness if thickness else 2
        obj.Height = height if height else 5
    if placement:
        obj.Placement = placement
    if hasattr(obj, "NumberOfSuppLines"):
        obj.NumberOfSuppLines = 1
    obj.Proxy.SuppLines = obj.Proxy.findSuppLines(obj)
    if not obj.Proxy.SuppLines:
        obj.Proxy.makeSupportLinesChildObjects(obj)
    return obj
