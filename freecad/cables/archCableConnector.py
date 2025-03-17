"""ArchCableConnector
"""

import os
import math
import FreeCAD
import ArchComponent
import Part
from freecad.cables import iconPath
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP


CLASS_CABLECONNECTOR_ICON = os.path.join(iconPath,
                                         "classArchCableConnector.svg")


class ArchCableConnector(ArchComponent.Component):
    """The ArchCableConnector object
    """
    def __init__(self, obj):
        ArchComponent.Component.__init__(self, obj)
        self.setProperties(obj)
        from ArchIFC import IfcTypes
        if "Cable Fitting" in IfcTypes:
            obj.IfcType = "Cable Fitting"
        else:
            # IFC2x3 does not know a Cable Fitting
            obj.IfcType = "Building Element Proxy"
        obj.addExtension('Part::AttachExtensionPython')

    def setProperties(self, obj):
        pl = obj.PropertiesList
        if "HoleSize" not in pl:
            obj.addProperty("App::PropertyFloat", "HoleSize",
                            "CableConnector",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The size of single " +
                                "hole in [mm2]"))
        if "Thickness" not in pl:
            obj.addProperty("App::PropertyLength", "Thickness",
                            "CableConnector",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The wall thickness"))
        if "Height" not in pl:
            obj.addProperty("App::PropertyLength", "Height", "CableConnector",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The height of this " +
                                "connector"))
        if "NumberOfHoles" not in pl:
            obj.addProperty("App::PropertyInteger", "NumberOfHoles",
                            "CableConnector",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The number of holes for " +
                                "cables"))
        self.Type = "CableConnector"

    def onDocumentRestored(self, obj):
        ArchComponent.Component.onDocumentRestored(self, obj)
        self.setProperties(obj)

    def onChanged(self, obj, prop):
        ArchComponent.Component.onChanged(self, obj, prop)

    def execute(self, obj):
        pl = obj.Placement
        shapes = []
        shapes.append(self.makeSupportPoints(obj))
        shapes.append(self.makeBox(obj))
        sh = Part.makeCompound(shapes)
        obj.Shape = self.processSubShapes(obj, sh, pl)
        obj.Placement = pl
        # FreeCAD.Console.PrintMessage("ArchCableConnector.execute: end\n")

    def makeSupportPoints(self, obj):
        hole_diameter = math.sqrt(obj.HoleSize/math.pi)*2
        ln = obj.NumberOfHoles * \
            (hole_diameter + obj.Thickness.Value) + \
            obj.Thickness.Value
        z = 2
        y = 0
        vertexes1 = []
        vertexes2 = []
        for i in range(obj.NumberOfHoles):
            x = -ln/2 + obj.Thickness.Value + hole_diameter/2 + \
                i*(hole_diameter + obj.Thickness.Value)
            vertexes1.append(Part.Vertex(x, y, z))
            vertexes2.append(Part.Vertex(x, y, -obj.Height.Value-z))
        s = Part.Shape(vertexes1 + vertexes2)
        return s

    def makeBox(self, obj):
        hole_diameter = math.sqrt(obj.HoleSize/math.pi)*2
        vc = FreeCAD.Vector(0, 0, 0)
        vn = FreeCAD.Vector(0, 0, -1)
        ln = obj.NumberOfHoles * \
            (hole_diameter + obj.Thickness.Value) + \
            obj.Thickness.Value
        w = hole_diameter + 2*obj.Thickness.Value
        h = obj.Height
        vb = vc + FreeCAD.Vector(ln/2, -w/2, 0)
        box = Part.makeBox(ln, w, h, vb, vn)
        for i in range(obj.NumberOfHoles):
            x = -ln/2 + obj.Thickness.Value + hole_diameter/2 + \
                i*(hole_diameter + obj.Thickness.Value)
            hc = vc + FreeCAD.Vector(x, 0, 0)
            hn = vn
            hole = Part.makeCylinder(hole_diameter/2, obj.Height, hc, hn)
            box = box.cut(hole)
        return box


class ViewProviderCableConnector(ArchComponent.ViewProviderComponent):
    """A View Provider for the ArchCableBox object
    """
    def __init__(self, vobj):
        ArchComponent.ViewProviderComponent.__init__(self, vobj)

    def getIcon(self):
        return CLASS_CABLECONNECTOR_ICON


def makeCableConnector(baseobj=None, nrofholes=0, holesize=0, thickness=0,
                       height=0, placement=None, name=None):
    """makeCableConnector([baseobj],[nrofholes],[holesize],[thickness],
    [height],[placement],[name]):
    creates a cable connector object from the given base object
    or from scratch"""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No active document. Aborting") + "\n")
        return
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                           "CableConnector")
    obj.Label = name if name else translate("Cables", "CableConnector")
    ArchCableConnector(obj)
    if FreeCAD.GuiUp:
        ViewProviderCableConnector(obj.ViewObject)
        if baseobj:
            baseobj.ViewObject.hide()
    if baseobj:
        obj.Base = baseobj
    else:
        obj.NumberOfHoles = nrofholes if nrofholes else 3
        obj.HoleSize = holesize if holesize else 2.0
        obj.Thickness = thickness if thickness else 1.0
        obj.Height = height if height else 5.0
    if placement:
        obj.Placement = placement
    return obj
