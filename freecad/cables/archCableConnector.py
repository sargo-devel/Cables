"""ArchCableConnector
"""

import os
import math
import FreeCAD
if FreeCAD.GuiUp:
    import FreeCADGui
import Part
from freecad.cables import archCableBaseElement
from freecad.cables import cableProfile
from freecad.cables import iconPath
from freecad.cables import presetsPath
from freecad.cables import uiPath
from freecad.cables import libPath
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP


CLASS_CABLECONNECTOR_ICON = os.path.join(iconPath,
                                         "classArchCableConnector.svg")
tol = 1e-6

# Presets in the form: Name, Shape Type, Connector Class, [preset data]
# Search for connector presets in presets and in the user path
presetfiles = [os.path.join(presetsPath, "connectorpresets.csv"),
               os.path.join(FreeCAD.getUserAppDataDir(), "Cables",
                            "connectorpresets.csv")]
libdirs = [libPath, os.path.join(FreeCAD.getUserAppDataDir(), "Cables", "lib")]
default_preset = "TerminalStrip_2.5mm2_x3"

ui_connector = os.path.join(uiPath, "connector.ui")
gauge_mm2_list = cableProfile.gauge_mm2_list


class TaskPanelCableConnector(archCableBaseElement.TaskPanelBaseElement):
    def __init__(self, obj, ui=ui_connector, gauge_list=gauge_mm2_list):
        archCableBaseElement.TaskPanelBaseElement.__init__(self, obj, ui)
        self.gauge_list = gauge_list
        self.form.comboPreset.addItems(self.presetnames)
        self.form.comboHoleSize.addItems(gauge_list)
        self.connectEnumVar(self.form.comboPreset, "Preset",
                            self.updateVisibility)
        self.connectEnumVar(self.form.comboHoleSize, "HoleSize",
                            self.updateVisibility)
        self.connectSpinVar(self.form.customHoleSize, "HoleSize",
                            self.updateVisibility)
        self.connectSpinVar(self.form.nrOfHoles, "NumberOfHoles")
        self.connectSpinVar(self.form.sHeight, "Height")
        self.connectSpinVar(self.form.sThickness, "Thickness")
        self.reloadPropertiesFromObj()

    def accept(self):
        # prepare commands to track changes in console
        pnames = []
        pvalues = []
        if self.obj.Preset == "Customized":
            pnames = ["NumberOfHoles", "Height", "HoleSize", "Thickness"]
            pvalues.append(self.obj.NumberOfHoles)
            pvalues.append(str(self.obj.Height))
            pvalues.append(self.obj.HoleSize)
            pvalues.append(str(self.obj.Thickness))
        # FreeCADGui.doCommand(
        #     f"obj = FreeCAD.activeDocument().getObject('{self.obj.Name}')")
        FreeCADGui.doCommand("obj.Proxy.setPreset(obj, " +
                             f"'{self.obj.Preset}', {pnames}, {pvalues})")
        archCableBaseElement.TaskPanelBaseElement.accept(self)

    def updateVisibility(self, pname, pvalue):
        #FreeCAD.Console.PrintMessage(f"pvalue={pvalue}, pname={pname}\n")
        if pname == "Preset":
            #FreeCAD.Console.PrintMessage(f"object={self.obj.Label}\n")
            preset_name = self.obj.getEnumerationsOfProperty(pname)[pvalue]
            if preset_name == "Customized":
                self.form.customBox.setVisible(True)
            else:
                self.form.customBox.setVisible(False)
            if self.form.comboPreset.currentText() == "Customized":
                self.reloadPropertiesFromObj()
        if pname == "HoleSize":
            if pvalue == "custom":
                self.form.customHoleSize.setVisible(True)
                self.form.customHoleSizeLabel.setVisible(True)
                self.form.customHoleSize.setValue(self.obj.HoleSize)
            elif isinstance(pvalue, str):
                self.form.customHoleSize.setVisible(False)
                self.form.customHoleSizeLabel.setVisible(False)

    def updateProperty(self, pname, pvalue, callback):
        ptype = self.obj.getTypeIdOfProperty(pname)
        #FreeCAD.Console.PrintMessage(f"ptype={ptype}, pvalue={pvalue}, pname={pname}\n")
        try:
            if ptype == "App::PropertyEnumeration":
                setattr(self.obj, pname, pvalue)
            elif ptype == "App::PropertyFloat" and pvalue != "custom":
                setattr(self.obj, pname, float(pvalue))
            elif ptype == "App::PropertyInteger":
                setattr(self.obj, pname, int(pvalue))
            elif pvalue != "custom":
                setattr(self.obj, pname, pvalue)
            if hasattr(self.obj, "recompute"):
                self.obj.recompute(True)
        except (AttributeError, ValueError):
            FreeCAD.Console.PrintError(
                self.obj, f"Can't set {pname} with value: {pvalue}")
        if callback is not None:
            callback(pname, pvalue)

    def reloadPropertiesFromObj(self):
        archCableBaseElement.TaskPanelBaseElement.reloadPropertiesFromObj(self)
        self.form.nrOfHoles.setValue(self.obj.NumberOfHoles)
        if f"{self.obj.HoleSize:g}" in self.gauge_list:
            self.form.comboHoleSize.setCurrentText(f"{self.obj.HoleSize:g}")
        else:
            self.form.comboHoleSize.setCurrentText("custom")
            self.form.customHoleSize.setValue(self.obj.HoleSize)
        self.form.sHeight.setProperty("value", self.obj.Height)
        self.form.sThickness.setProperty("value", self.obj.Thickness)


class ArchCableConnector(archCableBaseElement.BaseElement):
    """The ArchCableConnector object
    """
    def __init__(self, obj):
        eltype = "CableConnector"
        archCableBaseElement.BaseElement.__init__(self, obj, eltype=eltype)
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
        self.Type = "Component"

    def onDocumentRestored(self, obj):
        eltype = "CableConnector"
        archCableBaseElement.BaseElement.onDocumentRestored(self, obj, eltype)
        self.setProperties(obj)

    def onChanged(self, obj, prop):
        archCableBaseElement.BaseElement.onChanged(self, obj, prop)
        if prop == "Preset":
            if hasattr(obj, "ExtShape") and not obj.ExtShape.isNull():
                hide_list = ["Height", "HoleSize", "NumberOfHoles",
                             "Thickness"]
                unhide_list = ["NumberOfTerminals", "NumberOfSuppLines",
                               "SuppLines"]
            else:
                hide_list = ["NumberOfTerminals", "NumberOfSuppLines",
                             "SuppLines"]
                unhide_list = ["Height", "HoleSize", "NumberOfHoles",
                               "Thickness"]
            for element in hide_list:
                if hasattr(obj, element):
                    obj.setPropertyStatus(element, "Hidden")
            for element in unhide_list:
                if hasattr(obj, element):
                    obj.setPropertyStatus(element, "-Hidden")

    def execute(self, obj):
        # FreeCAD.Console.PrintMessage(obj.Label, "execute: start\n")
        archCableBaseElement.BaseElement.execute(self, obj)
        pl = obj.Placement
        shapes = []
        if not hasattr(obj, "ExtShape") or obj.ExtShape.isNull():
            shapes.append(self.makeBox(obj))
            sh = Part.makeCompound(shapes)
            if obj.Additions or obj.Subtractions:
                sh = self.processSubShapes(obj, sh, pl)
            if not self.sameShapes(sh, obj.Shape):
                obj.Shape = sh
                # obj.Placement = pl
            elif obj.Material:
                # refresh colors
                obj.Material = obj.Material
        # FreeCAD.Console.PrintMessage(obj.Label, "execute: end\n")

    def getPresets(self, obj):
        pr = archCableBaseElement.BaseElement.getPresets(self, obj,
                                                         presetfiles)
        return pr

    def updateTerminalsParameters(self, obj):
        z = 2
        if not hasattr(obj, "ExtShape") or obj.ExtShape.isNull():
            # Shape type: ParametricTerminal
            if hasattr(obj, "Terminals") and obj.Terminals:
                for t in obj.Terminals:
                    length = obj.Height.Value + 2*z
                    # set terminal length
                    if t.Length.Value != length:
                        t.Length = length
                    # set terminal spacing
                    hole_diameter = math.sqrt(obj.HoleSize/math.pi)*2
                    spacing = hole_diameter + obj.Thickness.Value
                    if t.Spacing.Value != spacing:
                        t.Spacing = spacing
                    # set terminal connections
                    if t.NumberOfConnections != obj.NumberOfHoles:
                        t.NumberOfConnections = obj.NumberOfHoles
                    # set terminal placement
                    b = FreeCAD.Vector(0, 0, -obj.Height/2.0)
                    r = FreeCAD.Rotation("XYZ", 90, 0, 0)
                    base_pl = FreeCAD.Placement(b, r)
                    if base_pl != t.Offset:
                        t.Offset = base_pl

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

    def updatePropertiesFromPreset(self, obj, presets):
        paramlist = ["NumberOfHoles", "NumberOfTerminals", "Height",
                     "HoleSize", "Thickness"]
        for param in paramlist:
            if not hasattr(obj, param):
                return

        name = obj.Preset
        if name == "Customized":
            obj.ExtShape = Part.Shape()
            nr_of_term = 1
            nr_of_supp = 0
            if obj.NumberOfTerminals != nr_of_term:
                obj.NumberOfTerminals = nr_of_term
                self.makeTerminalChildObjects(obj)
            if obj.NumberOfSuppLines != nr_of_supp:
                obj.NumberOfSuppLines = nr_of_supp
                self.makeSupportLinesChildObjects(obj)
            return
        preset = None
        for p in presets:
            p_name = f"{p[3]}_{p[1]}"
            if name == p_name:
                preset = p
                break
        if preset is not None:
            try:
                if preset[2] == "ParametricTerminal":
                    obj.NumberOfHoles = int(preset[4])
                    nr_of_term = int(preset[5])
                    nr_of_supp = 0
                    obj.Height.Value = preset[6]
                    obj.HoleSize = preset[7]
                    obj.Thickness.Value = preset[8]
                    obj.ExtShape = Part.Shape()
                    obj.ExtColor = []
                    if obj.NumberOfTerminals != nr_of_term:
                        obj.NumberOfTerminals = nr_of_term
                        self.makeTerminalChildObjects(obj)
                    if obj.NumberOfSuppLines != nr_of_supp:
                        obj.NumberOfSuppLines = nr_of_supp
                        self.makeSupportLinesChildObjects(obj)
                    for t in obj.Terminals:
                        t.Proxy.setPropertiesReadOnly(t)
                if preset[2] == "Fixed":
                    ext_shape, ext_color = self.readExtShape(obj, preset[4])
                    nr_of_term = int(preset[5])
                    nr_of_supp = int(preset[6])
                    ext_data = self.readExtData(
                        obj, f"{preset[3]}_{preset[1]}.csv")
                    if obj.NumberOfTerminals != nr_of_term or \
                       len(obj.Terminals) != nr_of_term:
                        obj.NumberOfTerminals = nr_of_term
                        self.makeTerminalChildObjects(obj)
                    if obj.NumberOfSuppLines != nr_of_supp or \
                       len(obj.SuppLines) != nr_of_supp:
                        obj.NumberOfSuppLines = nr_of_supp
                        self.makeSupportLinesChildObjects(obj)
                    if ext_data:
                        sh_offset = ext_data["ExtShape"][0][0]
                        ext_shape.Placement = sh_offset
                        for i, t in enumerate(obj.Terminals):
                            t.Offset = ext_data["Terminal"][i][0]
                            t.NumberOfConnections = int(
                                ext_data["Terminal"][i][1])
                            t.Length = ext_data["Terminal"][i][2]
                            t.Spacing = ext_data["Terminal"][i][3]
                        # update SupportLines
                        if obj.SuppLines and ext_data["SupportLines"]:
                            for i, s in enumerate(obj.SuppLines):
                                s.Offset = ext_data["SupportLines"][i][0]
                    obj.ExtShape = ext_shape
                    obj.ExtColor = ext_color
            except ValueError:
                FreeCAD.Console.PrintError(
                    f"Preset loading error for preset name '{name}'. Wrong " +
                    "value assignment!\n")
            except IndexError:
                FreeCAD.Console.PrintError(
                    f"Preset loading error for preset name '{name}'. Wrong " +
                    "number of Terminals or SupportLines\n")
        else:
            FreeCAD.Console.PrintError(
                f"Preset loading error for preset name '{name}'. Preset " +
                "does not exist!\n")

    def readExtShape(self, obj, filename, libdirs=libdirs):
        """Function reads object shape and colors from step file.
        Returns tuple (shape, list of colors)
        """
        sh_col = archCableBaseElement.BaseElement.readExtShape(
            self, obj, filename, libdirs=libdirs)
        return sh_col

    def readExtData(self, obj, filename, libdirs=libdirs):
        """Function reads data: shape offset, terminals, support lines
        from csv file.
        Returns dict
        """
        data = archCableBaseElement.BaseElement.readExtData(
            self, obj, filename, libdirs=libdirs)
        return data


class ViewProviderCableConnector(archCableBaseElement.ViewProviderBaseElement):
    """A View Provider for the ArchCableBox object
    """
    def __init__(self, vobj):
        archCableBaseElement.ViewProviderBaseElement.__init__(self, vobj)

    def getIcon(self):
        return CLASS_CABLECONNECTOR_ICON

    def setEdit(self, vobj, mode):
        return archCableBaseElement.ViewProviderBaseElement.setEditBase(
            self, vobj, mode, TaskPanelCableConnector,
            translate("Cables", "edit Cable Connector"))


def makeCableConnector(baseobj=None, nrofholes=0, holesize=0, thickness=0,
                       height=0, preset=None, placement=None, name=None):
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
    if preset is not None:
        obj.Proxy.setPreset(obj, preset)
    else:
        obj.Proxy.setPreset(obj, default_preset)
    if placement:
        obj.Placement = placement
    if hasattr(obj, "Terminals") and not obj.Terminals:
        obj.Proxy.makeTerminalChildObjects(obj)
    return obj
