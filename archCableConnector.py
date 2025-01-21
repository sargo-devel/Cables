"""ArchCableConnector
"""

import FreeCAD
import ArchComponent
import os
import Part


_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "Resources/icons")
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
        if "HoleDiameter" not in pl:
            obj.addProperty("App::PropertyLength", "HoleDiameter",
                            "CableConnector", "The diameter of single hole")
        if "Thickness" not in pl:
            obj.addProperty("App::PropertyLength", "Thickness",
                            "CableConnector", "The wall thickness")
        if "Height" not in pl:
            obj.addProperty("App::PropertyLength", "Height", "CableConnector",
                            "The height of this connector")
        if "NumberOfHoles" not in pl:
            obj.addProperty("App::PropertyInteger", "NumberOfHoles",
                            "CableConnector", "The nomber of holes for cables")
        self.Type = "CableConnector"

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
        FreeCAD.Console.PrintMessage("ArchBox.execute: end\n")

    def makeHelperLines(self, obj):
        ln = obj.NumberOfHoles * \
            (obj.HoleDiameter.Value + obj.Thickness.Value) + \
            obj.Thickness.Value
        z = 2
        y = 0
        vertexes1 = []
        vertexes2 = []
        for i in range(obj.NumberOfHoles):
            x = -ln/2 + obj.Thickness.Value + obj.HoleDiameter.Value/2 + \
                i*(obj.HoleDiameter.Value + obj.Thickness.Value)
            vertexes1.append(Part.Vertex(x, y, z))
            vertexes2.append(Part.Vertex(x, y, -obj.Height.Value-z))
        s = Part.Shape(vertexes1 + vertexes2)
        return s

    def makeBox(self, obj):
        vc = FreeCAD.Vector(0, 0, 0)
        vn = FreeCAD.Vector(0, 0, -1)
        ln = obj.NumberOfHoles * \
            (obj.HoleDiameter.Value + obj.Thickness.Value) + \
            obj.Thickness.Value
        w = obj.HoleDiameter.Value + 2*obj.Thickness.Value
        h = obj.Height
        vb = vc + FreeCAD.Vector(ln/2, -w/2, 0)
        box = Part.makeBox(ln, w, h, vb, vn)
        for i in range(obj.NumberOfHoles):
            x = -ln/2 + obj.Thickness.Value + obj.HoleDiameter.Value/2 + \
                i*(obj.HoleDiameter.Value + obj.Thickness.Value)
            hc = vc + FreeCAD.Vector(x, 0, 0)
            hn = vn
            hole = Part.makeCylinder(obj.HoleDiameter/2, obj.Height, hc, hn)
            box = box.cut(hole)
        return box


class ViewProviderCableConnector(ArchComponent.ViewProviderComponent):
    """A View Provider for the ArchCableBox object
    """
    def __init__(self, vobj):
        ArchComponent.ViewProviderComponent.__init__(self, vobj)

    def getIcon(self):
        return CLASS_CABLECONNECTOR_ICON


def makeCableConnector(baseobj=None, nrofholes=0, holediameter=0, thickness=0,
                       height=0, placement=None, name=None):
    """makeCableConnector([baseobj],[nrofholes],[holediameter],[thickness],
    [height],[placement],[name]):
    creates a cable connector object from the given base object
    or from scratch"""
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                           "CableConnector")
    obj.Label = name if name else "CableConnector"
    ArchCableConnector(obj)
    if FreeCAD.GuiUp:
        ViewProviderCableConnector(obj.ViewObject)
        if baseobj:
            baseobj.ViewObject.hide()
    if baseobj:
        obj.Base = baseobj
    else:
        obj.NumberOfHoles = nrofholes if nrofholes else 3
        obj.HoleDiameter = holediameter if holediameter else 2
        obj.Thickness = thickness if thickness else 1
        obj.Height = height if height else 5
    if placement:
        obj.Placement = placement
    return obj
