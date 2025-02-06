"""ArchCableLightPoint
"""

import FreeCAD
import ArchComponent
import os
import Part
from commonutils import QT_TRANSLATE_NOOP


translate = FreeCAD.Qt.translate
_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "Resources/icons")
CLASS_CABLELIGHTPOINT_ICON = os.path.join(iconPath,
                                          "classArchCableLightPoint.svg")


class ArchCableLightPoint(ArchComponent.Component):
    """The ArchCableLightPoint object
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
        self.Type = "LightPoint"

    def onChanged(self, obj, prop):
        pass

    def execute(self, obj):
        pl = obj.Placement
        shapes = []
        shapes.append(self.makeHelperLines(obj))
        shapes.append(self.makeBox(obj))
        sh = Part.makeCompound(shapes)
        obj.Shape = self.processSubShapes(obj, sh, pl)
        obj.Placement = pl

    def makeHelperLines(self, obj):
        z = 2
        y = 0
        vertexes1 = []
        vertexes2 = []
        x = 0
        vertexes1.append(Part.Vertex(x, y, z))
        vertexes2.append(Part.Vertex(x, y, -obj.Height.Value-z))
        s = Part.Shape(vertexes1 + vertexes2)
        return s

    def makeBox(self, obj):
        vc = FreeCAD.Vector(0, 0, 0)
        vn = FreeCAD.Vector(0, 0, -1)
        cyl1 = Part.makeCylinder(obj.Diameter/2, obj.Height, vc, vn)
        cyl2 = Part.makeCylinder(obj.Diameter/2-obj.Thickness, obj.Height,
                                 vc, vn)
        box = cyl1.cut(cyl2)
        return box


class ViewProviderCableLightPoint(ArchComponent.ViewProviderComponent):
    """A View Provider for the ArchCableBox object
    """
    def __init__(self, vobj):
        ArchComponent.ViewProviderComponent.__init__(self, vobj)

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
    return obj
