"""ArchCableBox
"""

import os
from math import pi
from math import sin
from math import cos
import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
import Part
from freecad.cables import archCableBaseElement
from freecad.cables import iconPath
from freecad.cables import presetsPath
from freecad.cables import uiPath
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP


CLASS_CABLEBOX_ICON = os.path.join(iconPath, "classArchCableBox.svg")
tol = 1e-6

# Presets in the form: Name, Profile Type, Box Class, [preset data]
# Search for boxpresets.csv in presets and in the user path
presetfiles = [os.path.join(presetsPath, "boxpresets.csv"),
               os.path.join(FreeCAD.getUserAppDataDir(), "Cables",
                            "boxpresets.csv")]
default_preset = "1G_FlushMnt_Round_D60_h62"

ui_box = os.path.join(uiPath, "box.ui")


class TaskPanelCableBox(archCableBaseElement.TaskPanelBaseElement):
    def __init__(self, obj, ui=ui_box):
        archCableBaseElement.TaskPanelBaseElement.__init__(self, obj, ui)
        self.profile_types = self.obj.getEnumerationsOfProperty("ProfileType")
        self.form.comboPreset.addItems(self.presetnames)
        self.form.comboProfileType.addItems(self.profile_types)
        self.connectEnumVar(self.form.comboPreset, "Preset",
                            self.updateVisibility)
        self.connectEnumVar(self.form.comboProfileType, "ProfileType",
                            self.updateVisibility)
        self.connectSpinVar(self.form.sWidth, "Width")
        self.connectSpinVar(self.form.sDepth, "Depth")
        self.connectSpinVar(self.form.sFilletRadius, "FilletRadius")
        self.connectSpinVar(self.form.sDiameter, "Diameter")
        self.connectSpinVar(self.form.sHeight, "Height")
        self.connectSpinVar(self.form.sThickness, "Thickness")
        self.connectSpinVar(self.form.sHoleDiameter, "HoleDiameter")
        self.connectSpinVar(self.form.sHolesDistance, "HolesDistance")
        self.reloadPropertiesFromObj()

    def accept(self):
        # prepare commands to track changes in console
        pnames = []
        pvalues = []
        if self.obj.Preset == "Customized":
            pnames = ["ProfileType", "Width", "Depth", "FilletRadius",
                      "Diameter", "Height", "Thickness", "HoleDiameter",
                      "HolesDistance"]
            pvalues.append(self.obj.ProfileType)
            pvalues.append(str(self.obj.Width))
            pvalues.append(str(self.obj.Depth))
            pvalues.append(str(self.obj.FilletRadius))
            pvalues.append(str(self.obj.Diameter))
            pvalues.append(str(self.obj.Height))
            pvalues.append(str(self.obj.Thickness))
            pvalues.append(str(self.obj.HoleDiameter))
            pvalues.append(str(self.obj.HolesDistance))
        FreeCADGui.doCommand("obj.Proxy.setPreset(obj, " +
                             f"'{self.obj.Preset}', {pnames}, {pvalues})")
        archCableBaseElement.TaskPanelBaseElement.accept(self)

    def updateVisibility(self, pname, pvalue):
        def _updateProfileTypeVisibility(pvalue):
            if self.profile_types[pvalue] == "Circle":
                self.form.sWidth.setVisible(False)
                self.form.sWidthLabel.setVisible(False)
                self.form.sDepth.setVisible(False)
                self.form.sDepthLabel.setVisible(False)
                self.form.sFilletRadius.setVisible(False)
                self.form.sFilletRadiusLabel.setVisible(False)
                self.form.sDiameter.setVisible(True)
                self.form.sDiameterLabel.setVisible(True)
                self.form.sHolesDistance.setVisible(False)
                self.form.sHolesDistanceLabel.setVisible(False)
            elif self.profile_types[pvalue] == "Rectangle":
                self.form.sWidth.setVisible(True)
                self.form.sWidthLabel.setVisible(True)
                self.form.sDepth.setVisible(True)
                self.form.sDepthLabel.setVisible(True)
                self.form.sFilletRadius.setVisible(True)
                self.form.sFilletRadiusLabel.setVisible(True)
                self.form.sDiameter.setVisible(False)
                self.form.sDiameterLabel.setVisible(False)
                self.form.sHolesDistance.setVisible(True)
                self.form.sHolesDistanceLabel.setVisible(True)
        if pname == "Preset":
            preset_name = self.obj.getEnumerationsOfProperty(pname)[pvalue]
            if preset_name == "Customized":
                self.form.customBox.setVisible(True)
            else:
                self.form.customBox.setVisible(False)
            if self.form.comboPreset.currentText() == "Customized":
                idx = self.profile_types.index(self.obj.ProfileType)
                _updateProfileTypeVisibility(idx)
                self.reloadPropertiesFromObj()
        if pname == "ProfileType":
            _updateProfileTypeVisibility(pvalue)

    def reloadPropertiesFromObj(self):
        archCableBaseElement.TaskPanelBaseElement.reloadPropertiesFromObj(self)
        self.form.comboProfileType.setCurrentText(self.obj.ProfileType)
        self.form.sWidth.setProperty("value", self.obj.Width)
        self.form.sDepth.setProperty("value", self.obj.Depth)
        self.form.sFilletRadius.setProperty("value", self.obj.FilletRadius)
        self.form.sDiameter.setProperty("value", self.obj.Diameter)
        self.form.sHeight.setProperty("value", self.obj.Height)
        self.form.sThickness.setProperty("value", self.obj.Thickness)
        self.form.sHoleDiameter.setProperty("value", self.obj.HoleDiameter)
        self.form.sHolesDistance.setProperty("value", self.obj.HolesDistance)


class ArchCableBox(archCableBaseElement.BaseElement):
    """The ArchCableBox object
    """
    def __init__(self, obj):
        eltype = "CableBox"
        archCableBaseElement.BaseElement.__init__(self, obj, eltype=eltype)
        self.setProperties(obj)
        from ArchIFC import IfcTypes
        if "Junction Box" in IfcTypes:
            obj.IfcType = "Junction Box"
            if hasattr(obj, "PredefinedType"):
                obj.PredefinedType = "POWER"
        else:
            # IFC2x3 does not know a Juction Box
            obj.IfcType = "Building Element Proxy"
        obj.addExtension('Part::AttachExtensionPython')

    def setProperties(self, obj):
        pl = obj.PropertiesList
        if "ProfileType" not in pl:
            obj.addProperty("App::PropertyEnumeration", "ProfileType",
                            "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The profile type of " +
                                "this box"))
            obj.ProfileType = ['Circle', 'Rectangle']
        if "Diameter" not in pl:
            obj.addProperty("App::PropertyLength", "Diameter", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The inner diameter of " +
                                "this box"))
        if "Thickness" not in pl:
            obj.addProperty("App::PropertyLength", "Thickness", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The wall thickness of " +
                                "this box"))
        if "Height" not in pl:
            obj.addProperty("App::PropertyLength", "Height", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The inner height of this " +
                                "box"))
        if "Width" not in pl:
            obj.addProperty("App::PropertyLength", "Width", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The inner width of this " +
                                "box"))
        if "Depth" not in pl:
            obj.addProperty("App::PropertyLength", "Depth", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The inner depth of this " +
                                "box"))
        if "FilletRadius" not in pl:
            obj.addProperty("App::PropertyLength", "FilletRadius", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The inner fillet radius " +
                                "of side walls of this box"))
        if "HolesDistance" not in pl:
            obj.addProperty("App::PropertyLength", "HolesDistance", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The distance between " +
                                "holes on a single wall"))
        if "HoleDiameter" not in pl:
            obj.addProperty("App::PropertyLength", "HoleDiameter", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The diameter of a single " +
                                "hole"))
        if "BoxBodyHidden" not in pl:
            obj.addProperty("App::PropertyBool", "BoxBodyHidden", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Hide the box body to have " +
                                "better access to helpers"))
        if "HelperRingsHidden" not in pl:
            obj.addProperty("App::PropertyBool", "HelperRingsHidden",
                            "CableBoxHelpers",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Hide the helper rings if " +
                                "they are not needed"))
        if "Ring1Diameter" not in pl:
            obj.addProperty("App::PropertyLength", "Ring1Diameter",
                            "CableBoxHelpers",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The diameter of helper " +
                                "ring 1"))
        if "Ring1Height" not in pl:
            obj.addProperty("App::PropertyLength", "Ring1Height",
                            "CableBoxHelpers",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The height below lid of " +
                                "helper ring 1"))
        if "Ring2Diameter" not in pl:
            obj.addProperty("App::PropertyLength", "Ring2Diameter",
                            "CableBoxHelpers",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The diameter of helper " +
                                "ring 2"))
        if "Ring2Height" not in pl:
            obj.addProperty("App::PropertyLength", "Ring2Height",
                            "CableBoxHelpers",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The height below lid of " +
                                "helper ring 2"))
        if "DinRails" not in pl:
            obj.addProperty("App::PropertyBool", "DinRails", "CableBox",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Enables auto creation of " +
                                "DIN TH35 rails inside box depending on box " +
                                "shape and dimensions"))
        if "Terminals" in pl:
            obj.removeProperty("Terminals")
        if "NumberOfTerminals" in pl:
            obj.removeProperty("NumberOfTerminals")
        if "NumberOfSuppLines" in pl:
            obj.setPropertyStatus("NumberOfSuppLines", "Hidden")
        self.Type = "Component"

    def onDocumentRestored(self, obj):
        eltype = "CableBox"
        archCableBaseElement.BaseElement.onDocumentRestored(self, obj, eltype)
        self.setProperties(obj)

    def onChanged(self, obj, prop):
        archCableBaseElement.BaseElement.onChanged(self, obj, prop)
        if prop == "ProfileType":
            if obj.ProfileType == "Circle":
                hide_list = ['FilletRadius', 'Width', 'Depth', 'HolesDistance']
                unhide_list = ['Diameter']
            if obj.ProfileType == "Rectangle":
                hide_list = ['Diameter']
                unhide_list = ['FilletRadius', 'Width', 'Depth',
                               'HolesDistance']
            for element in hide_list:
                if hasattr(obj, element):
                    obj.setPropertyStatus(element, "Hidden")
            for element in unhide_list:
                if hasattr(obj, element):
                    obj.setPropertyStatus(element, "-Hidden")
            self.setHelperRingsDefaults(obj)

    def execute(self, obj):
        # FreeCAD.Console.PrintMessage(obj.Label, "execute start\n")
        archCableBaseElement.BaseElement.execute(self, obj)
        pl = obj.Placement
        shapes = []
        if (not hasattr(obj, "ExtShapeSolids") or obj.ExtShapeSolids == 0) and \
           (not hasattr(obj, "Base") or obj.Base is None):
            if not obj.BoxBodyHidden:
                # make main body
                if obj.ProfileType == "Circle":
                    shapes.append(self.makeRoundBox(obj))
                else:
                    shapes.append(self.makeRectangularBox(obj))
            if obj.ProfileType == "Rectangle" and obj.DinRails:
                # make DIN rails
                offsets = self.calculateDinRailsOffset(obj)
                if offsets is not None:
                    xs = obj.Width/2
                    din = self.makeDinRail(-xs, xs)
                    for offset in offsets:
                        sh = din.copy()
                        sh.Placement = sh.Placement.multiply(offset)
                        shapes.append(sh)
            if not obj.HelperRingsHidden:
                # make helper rings
                shapes.append(self.makeHelperRings(obj))
            sh = Part.makeCompound(shapes) if shapes else Part.Shape()
            if obj.Additions or obj.Subtractions:
                sh = self.processSubShapes(obj, sh, pl)
            # if not self.sameShapes(sh, obj.Shape):
            obj.Shape = sh
            # obj.Placement = pl
        # FreeCAD.Console.PrintMessage(obj.Label, "execute: end\n")

    def getPresets(self, obj):
        pr = archCableBaseElement.BaseElement.getPresets(self, obj,
                                                         presetfiles)
        return pr

    def makeSupportLines(self, obj):
        # support crosses
        t = obj.Thickness.Value
        d = obj.Depth.Value + 2*t
        w = obj.Width.Value + 2*t
        hole_dist = obj.HolesDistance.Value
        if obj.ProfileType == 'Circle':
            x0base = obj.Diameter.Value/2.0
            y0base = obj.Diameter.Value/2.0
            nr_of_holes_x = 1
            nr_of_holes_y = 1
        else:
            x0base = obj.Width.Value/2.0
            y0base = obj.Depth.Value/2.0
            nr_of_holes_x = int(w//hole_dist)
            nr_of_holes_y = int(d//hole_dist)
        z0 = -2.0/3.0*obj.Height.Value
        x = y = z = 0.3*obj.HoleDiameter.Value
        xoffset = -hole_dist*(nr_of_holes_x-1)/2.0
        yoffset = -hole_dist*(nr_of_holes_y-1)/2.0
        crosses1 = []
        crosses2 = []
        crosses3 = []
        crosses4 = []
        x0 = x0base
        for nr in range(nr_of_holes_y):
            y0 = yoffset + nr*hole_dist
            cross2 = [(x0, y0, z0),
                      (x0, y0-y, z0),
                      (x0, y0+y, z0),
                      (x0, y0, z0+z),
                      (x0, y0, z0-z)]
            cross4 = [(-x0, y0, z0),
                      (-x0, y0+y, z0),
                      (-x0, y0-y, z0),
                      (-x0, y0, z0+z),
                      (-x0, y0, z0-z)]
            crosses2.append(cross2)
            crosses4.append(cross4)
        y0 = y0base
        for nr in range(nr_of_holes_x):
            x0 = xoffset + nr*hole_dist
            cross1 = [(x0, y0, z0),
                      (x0+x, y0, z0),
                      (x0-x, y0, z0),
                      (x0, y0, z0+z),
                      (x0, y0, z0-z)]
            cross3 = [(x0, -y0, z0),
                      (x0-x, -y0, z0),
                      (x0+x, -y0, z0),
                      (x0, -y0, z0+z),
                      (x0, -y0, z0-z)]
            crosses1.append(cross1)
            crosses3.append(cross3)
        crosses2.reverse()
        crosses3.reverse()
        crosses = [*crosses1, *crosses2, *crosses3, *crosses4]
        lines = []
        for cross in crosses:
            v = []
            for c in cross:
                v.append(FreeCAD.Vector(*c))
            lines.append(Part.LineSegment(v[0], v[3]))
            lines.append(Part.LineSegment(v[0], v[2]))
            lines.append(Part.LineSegment(v[0], v[4]))
            lines.append(Part.LineSegment(v[0], v[1]))
        s = Part.Shape(lines)
        return s

    def makeHelperRings(self, obj):
        # helper rings
        lines = []
        v1 = FreeCAD.Vector(obj.Ring1Diameter.Value/2.0, 0,
                            -obj.Ring1Height.Value)
        v2 = FreeCAD.Vector(obj.Ring2Diameter.Value/2.0, 0,
                            -obj.Ring2Height.Value)
        vh = [v1, v2]
        # a: semi-major axis, b: semi-minor axis of ellipsis
        if obj.ProfileType == "Circle":
            a = b = 1
        else:
            a = 1
            b = obj.Depth.Value/obj.Width.Value
        for nr in range(len(vh)):
            v = []
            d = vh[nr].x
            for i in range(12):
                angle = i*2*pi/12
                x = a*cos(angle)
                y = b*sin(angle)
                vn = FreeCAD.Vector(x*d, y*d, vh[nr].z)
                v.append(vn)
            v.append(vh[nr])
            poly = Part.makePolygon(v)
            lines.append(poly)
        s = Part.Shape(lines)
        return s

    def setHelperRingsDefaults(self, obj):
        paramlist = ["Diameter", "Width", "Height"]
        for param in paramlist:
            if not hasattr(obj, param) or getattr(obj, param) == 0:
                return
        if obj.ProfileType == "Circle":
            obj.Ring1Diameter = 0.75*obj.Diameter.Value
            obj.Ring2Diameter = 0.5*obj.Diameter.Value
        else:
            obj.Ring1Diameter = 0.75*obj.Width.Value
            obj.Ring2Diameter = 0.5*obj.Width.Value
        obj.Ring1Height = 2.0/3.0*obj.Height.Value
        obj.Ring2Height = 1.0/3.0*obj.Height.Value

    def makeRoundBox(self, obj):
        vc = FreeCAD.Vector(0, 0, 0)
        vn = FreeCAD.Vector(0, 0, -1)
        ext_diameter = obj.Diameter.Value + 2*obj.Thickness.Value
        ext_height = obj.Height.Value + obj.Thickness.Value
        box = Part.makeCylinder(ext_diameter/2, ext_height, vc, vn)
        box = box.makeThickness(box.Faces[2], -obj.Thickness.Value, tol)
        vn_list = [FreeCAD.Vector(1, 0, 0), FreeCAD.Vector(-1, 0, 0),
                   FreeCAD.Vector(0, 1, 0), FreeCAD.Vector(0, -1, 0)]
        vc = FreeCAD.Vector(0, 0, -2.0/3.001*obj.Height.Value)
        hole_radius = obj.HoleDiameter.Value/2.0
        hole_hight = ext_diameter/2
        for vn in vn_list:
            hole = Part.makeCylinder(hole_radius, hole_hight, vc, vn)
            box = box.cut(hole)
        return box

    def makeRectangularBox(self, obj):
        t = obj.Thickness.Value
        w = obj.Width.Value + 2*t
        d = obj.Depth.Value + 2*t
        h = obj.Height.Value + t
        f = obj.FilletRadius.Value
        hole_dist = obj.HolesDistance.Value
        hole_radius = obj.HoleDiameter.Value/2.0
        tol = 0.0001
        # make box with fillets
        vc = FreeCAD.Vector(w/2.0, -d/2.0, 0)
        vn = FreeCAD.Vector(0, 0, -1)
        box = Part.makeBox(w, d, h, vc, vn)
        box = box.makeThickness(box.Faces[4], -t, tol)
        if f > 0:
            inner_side_edges = [box.Edges[i] for i in [16, 18, 20, 22]]
            box = box.makeFillet(f, inner_side_edges)
            outer_side_edges = [box.Edges[i] for i in [28, 30, 31, 34]]
            box = box.makeFillet(f+t, outer_side_edges)
        # make holes
        vnx_list = [FreeCAD.Vector(1, 0, 0), FreeCAD.Vector(-1, 0, 0)]
        vny_list = [FreeCAD.Vector(0, 1, 0), FreeCAD.Vector(0, -1, 0)]
        vc = FreeCAD.Vector(0, 0, -2.0/3.001*obj.Height.Value)
        hole_hight_x = w/2
        hole_hight_y = d/2
        nr_of_holes_x = int(w//hole_dist)
        nr_of_holes_y = int(d//hole_dist)
        for vn in vny_list:
            xoffset = -hole_dist*(nr_of_holes_x-1)/2.0
            for nr in range(nr_of_holes_x):
                vc = FreeCAD.Vector(xoffset+nr*hole_dist, 0,
                                    -2.0/3.001*obj.Height.Value)
                hole = Part.makeCylinder(hole_radius, hole_hight_y, vc, vn)
                box = box.cut(hole)
        for vn in vnx_list:
            yoffset = -hole_dist*(nr_of_holes_y-1)/2.0
            for nr in range(nr_of_holes_y):
                vc = FreeCAD.Vector(0, yoffset+nr*hole_dist,
                                    -2.0/3.001*obj.Height.Value)
                hole = Part.makeCylinder(hole_radius, hole_hight_x, vc, vn)
                box = box.cut(hole)
        return box

    def makeDinRail(self, xstart, xend, offset=None):
        # rail DIN TH35
        elist = []
        v = FreeCAD.Vector
        elist.append(Part.makeLine(v(0, 0, 0), v(0, -11.5, 0)))
        elist.append(Part.makeCircle(2, v(0, -11.5, 2), v(-1, 0, 0), 180, 270))
        elist.append(Part.makeLine(v(0, -13.5, 2), v(0, -13.5, 5)))
        elist.append(Part.makeCircle(1, v(0, -14.5, 5), v(1, 0, 0), 0, 90))
        elist.append(Part.makeLine(v(0, -14.5, 6), v(0, -17.5, 6)))
        elist.append(Part.makeLine(v(0, -17.5, 6), v(0, -17.5, 7)))

        elist.append(Part.makeLine(v(0, -17.5, 7), v(0, -14.5, 7)))
        elist.append(Part.makeCircle(2, v(0, -14.5, 5), v(-1, 0, 0), 0, 90))
        elist.append(Part.makeLine(v(0, -12.5, 5), v(0, -12.5, 2)))
        elist.append(Part.makeCircle(1, v(0, -11.5, 2), v(1, 0, 0), 180, 270))
        elist.append(Part.makeLine(v(0, -11.5, 1), v(0, 0, 1)))

        w1 = Part.Wire(elist)
        w2 = w1.mirror(v(0, 0, 0), v(0, 1, 0))
        w = Part.Wire(w1.Edges + w2.Edges)
        f = Part.Face(w)
        solid1 = f.extrude(v(xend, 0, 0))
        solid2 = f.extrude(v(xstart, 0, 0))
        solid = Part.makeSolid(solid1.fuse(solid2))
        if offset:
            solid.Placement = solid.Placement.multiply(offset)
        return solid

    def calculateDinRailsOffset(self, obj):
        zpos = -50.0
        ydist = 125.0
        vcz = -2.0/3.001*obj.Height.Value
        zdist = vcz + obj.HoleDiameter.Value/2
        if zdist > zpos:
            # box is not high enough for DIN rail
            return None
        if ydist > obj.Depth.Value:
            # box is not deep enough for DIN rail
            return None
        nr_of_rails = int(obj.Depth.Value//ydist)
        ystart = ydist*(nr_of_rails - 1)/2
        plist = []
        for i in range(nr_of_rails):
            pl = FreeCAD.Placement()
            pl.Base.z = zpos
            pl.Base.y = ystart - i*ydist
            plist.append(pl)
        return plist

    def updatePropertiesFromPreset(self, obj, presets):
        paramlist = ["Diameter", "Width", "Depth", "Height", "Thickness",
                     "FilletRadius", "HoleDiameter", "HolesDistance"]
        for param in paramlist:
            if not hasattr(obj, param):
                return

        if obj.Base is not None:
            return

        name = obj.Preset
        if name == "Customized":
            return
        preset = None
        for p in presets:
            p_name = f"{p[3]}_{p[1]}"
            if name == p_name:
                preset = p
                break
        if preset is not None:
            try:
                if preset[2] == "Circle":
                    obj.Diameter.Value = preset[4]
                    obj.Height.Value = preset[5]
                    obj.Thickness.Value = preset[6]
                    obj.HoleDiameter.Value = preset[7]
                if preset[2] == "Rectangle":
                    obj.Width.Value = preset[4]
                    obj.Depth.Value = preset[5]
                    obj.Height.Value = preset[6]
                    obj.Thickness.Value = preset[7]
                    obj.FilletRadius.Value = preset[8]
                    obj.HoleDiameter.Value = preset[9]
                    obj.HolesDistance.Value = preset[10]
                obj.ProfileType = preset[2]
                self.setHelperRingsDefaults(obj)
            except ValueError:
                FreeCAD.Console.PrintError(
                    f"Preset loading error for preset name '{name}'. Wrong " +
                    "value assignment!\n")
        else:
            FreeCAD.Console.PrintError(
                f"Preset loading error for preset name '{name}'. Preset " +
                "does not exist!\n")


class ViewProviderCableBox(archCableBaseElement.ViewProviderBaseElement):
    """A View Provider for the ArchCableBox object
    """

    def __init__(self, vobj):
        archCableBaseElement.ViewProviderBaseElement.__init__(self, vobj)

    def getIcon(self):
        return CLASS_CABLEBOX_ICON

    def setEdit(self, vobj, mode):
        return archCableBaseElement.ViewProviderBaseElement.setEditBase(
            self, vobj, mode, TaskPanelCableBox,
            translate("Cables", "edit Cable Box"))


def makeCableBox(baseobj=None, diameter=0, width=0, depth=0, height=0,
                 thickness=0, filletradius=0, holediameter=0, holesdistance=0,
                 profiletype=None, preset=None, placement=None, name=None):
    """Creates a cable box object from the given base object
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No active document. Aborting") + "\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "CableBox")
    obj.Label = name if name else translate("Cables", "CableBox")
    ArchCableBox(obj)
    obj.ProfileType = profiletype if profiletype else 'Circle'
    if FreeCAD.GuiUp:
        ViewProviderCableBox(obj.ViewObject)
        if baseobj:
            baseobj.ViewObject.hide()
    if baseobj:
        obj.Base = baseobj
    else:
        obj.Thickness = thickness if thickness else 2
        obj.Diameter = diameter if diameter else 60
        obj.Height = height if height else 62
        obj.Width = width if width else 74
        obj.Depth = depth if depth else 74
        obj.FilletRadius = filletradius if filletradius else 12
        obj.HoleDiameter = holediameter if holediameter else 20
        obj.HolesDistance = holesdistance if holesdistance else 40
    if preset is not None:
        obj.Proxy.setPreset(obj, preset)
    else:
        obj.Proxy.setPreset(obj, default_preset)
    obj.Proxy.setHelperRingsDefaults(obj)
    obj.BoxBodyHidden = False
    obj.DinRails = True
    obj.HelperRingsHidden = True
    if placement:
        obj.Placement = placement
    if hasattr(obj, "NumberOfSuppLines"):
        obj.NumberOfSuppLines = 1
    if hasattr(obj, "SuppLines") and not obj.SuppLines:
        obj.Proxy.makeSupportLinesChildObjects(obj)
    return obj
