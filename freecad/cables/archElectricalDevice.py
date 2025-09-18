"""ArchElectricalDevice
"""

import os
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


CLASS_ELECTRICALDEVICE_ICON = os.path.join(iconPath,
                                           "classArchElectricalDevice.svg")
tol = 1e-6

# Presets in the form: Name, Profile Type, Box Class, [preset data]
# Search for boxpresets.csv in presets and in the user path
presetfiles = [os.path.join(presetsPath, "devicepresets.csv"),
               os.path.join(FreeCAD.getUserAppDataDir(), "Cables",
                            "devicepresets.csv")]
default_preset = "MCB_1-Pole"

ui_device = os.path.join(uiPath, "device.ui")


class TaskPanelElectricalDevice(archCableBaseElement.TaskPanelBaseElement):
    def __init__(self, obj, ui=ui_device):
        archCableBaseElement.TaskPanelBaseElement.__init__(self, obj, ui)
        self.form.comboPreset.addItems(self.presetnames)
        self.connectEnumVar(self.form.comboPreset, "Preset",
                            self.updateVisibility)
        self.reloadPropertiesFromObj()

    def accept(self):
        # prepare commands to track changes in console
        pnames = []
        pvalues = []
        FreeCADGui.doCommand("obj.Proxy.setPreset(obj, " +
                             f"'{self.obj.Preset}', {pnames}, {pvalues})")
        archCableBaseElement.TaskPanelBaseElement.accept(self)

    def updateVisibility(self, pname, pvalue):
        if pname == "Preset":
            preset_name = self.obj.getEnumerationsOfProperty(pname)[pvalue]
            if preset_name == "Customized":
                self.form.customBox.setVisible(True)
            else:
                self.form.customBox.setVisible(False)
            if self.form.comboPreset.currentText() == "Customized":
                self.reloadPropertiesFromObj()

    def reloadPropertiesFromObj(self):
        archCableBaseElement.TaskPanelBaseElement.reloadPropertiesFromObj(self)


class ArchElectricalDevice(archCableBaseElement.BaseElement):
    """The ArchElectricalDevice object
    """
    def __init__(self, obj):
        eltype = "ElectricalDevice"
        archCableBaseElement.BaseElement.__init__(self, obj, eltype=eltype)
        self.setProperties(obj)
        from ArchIFC import IfcTypes
        if "Actuator" in IfcTypes:
            obj.IfcType = "Actuator"
            if hasattr(obj, "PredefinedType"):
                obj.PredefinedType = "ELECTRICACTUATOR"
        else:
            # IFC2x3 does not know a Juction Box
            obj.IfcType = "Building Element Proxy"
        obj.addExtension('Part::AttachExtensionPython')

    def setProperties(self, obj):
        self.Type = "Component"

    def onDocumentRestored(self, obj):
        eltype = "ElectricalDevice"
        archCableBaseElement.BaseElement.onDocumentRestored(self, obj, eltype)
        self.setProperties(obj)

    def onChanged(self, obj, prop):
        archCableBaseElement.BaseElement.onChanged(self, obj, prop)

    def execute(self, obj):
        archCableBaseElement.BaseElement.execute(self, obj)

    def getPresets(self, obj):
        pr = archCableBaseElement.BaseElement.getPresets(self, obj,
                                                         presetfiles)
        return pr

    def updatePropertiesFromPreset(self, obj, presets):
        paramlist = ["NumberOfTerminals", "NumberOfSuppLines"]
        for param in paramlist:
            if not hasattr(obj, param):
                return

        name = obj.Preset
        if name == "Customized":
            obj.ExtShape = Part.Shape()
            nr_of_term = 0
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
                        # Update Terminals
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


class ViewProviderElectricalDevice(
   archCableBaseElement.ViewProviderBaseElement):
    """A View Provider for the ArchElectricalDevice object
    """

    def __init__(self, vobj):
        archCableBaseElement.ViewProviderBaseElement.__init__(self, vobj)

    def getIcon(self):
        return CLASS_ELECTRICALDEVICE_ICON

    def setEdit(self, vobj, mode):
        return archCableBaseElement.ViewProviderBaseElement.setEditBase(
            self, vobj, mode, TaskPanelElectricalDevice,
            translate("Cables", "edit Electrical Device"))


def makeElectricalDevice(baseobj=None, preset=None, placement=None, name=None):
    """Creates an electrical device object from the given base object
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No active document. Aborting") + "\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                           "ElectricalDevice")
    obj.Label = name if name else translate("Cables", "ElectricalDevice")
    ArchElectricalDevice(obj)
    if FreeCAD.GuiUp:
        ViewProviderElectricalDevice(obj.ViewObject)
        if baseobj:
            baseobj.ViewObject.hide()
    if baseobj:
        obj.Base = baseobj
    if preset is not None:
        obj.Proxy.setPreset(obj, preset)
    else:
        obj.Proxy.setPreset(obj, default_preset)
    if placement:
        obj.Placement = placement
    return obj
