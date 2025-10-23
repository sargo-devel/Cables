"""commands used in Cables workbench
"""

import os
import FreeCAD
import FreeCADGui
from FreeCAD import Gui
import Part
from freecad.cables import wireutils
from freecad.cables import wireFlex
from freecad.cables import cableProfile
from freecad.cables import archCableConnector
from freecad.cables import archCableBox
from freecad.cables import archElectricalDevice
from freecad.cables import cableutils
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP


_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "resources/icons")
CMD_NEW_WIRE_ICON = os.path.join(iconPath, "cmdNewWire.svg")
CMD_ADD_VERTEX_ICON = os.path.join(iconPath, "cmdAddVertex.svg")
CMD_DEL_VERTEX_ICON = os.path.join(iconPath, "cmdDelVertex.svg")
CMD_ATT_VERTEX_ICON = os.path.join(iconPath, "cmdAttVertex.svg")
CMD_RM_ATT_VERTEX_ICON = os.path.join(iconPath, "cmdRmAttVertex.svg")
CMD_COMPOUNDPATH_ICON = os.path.join(iconPath, "cmdNewCompoundPath.svg")
CMD_CABLE_ICON = os.path.join(iconPath, "cmdNewCable.svg")
CMD_CABLECONDUIT_ICON = os.path.join(iconPath, "cmdNewCableConduit.svg")
CMD_CABLEBOX_ICON = os.path.join(iconPath, "cmdNewCableBox.svg")
CMD_CABLECONNECTOR_ICON = os.path.join(iconPath, "cmdNewCableConnector.svg")
CMD_CABLEPROFILE_ICON = os.path.join(iconPath, "cmdNewCableProfile.svg")
CMD_CABLEMATERIAL_ICON = os.path.join(iconPath, "cmdNewCableMaterial.svg")
CMD_CABLELIGHTPOINT_ICON = os.path.join(iconPath, "cmdNewCableLightPoint.svg")
CMD_ELECTRICALDEVICE_ICON = os.path.join(iconPath,
                                         "cmdNewElectricalDevice.svg")
CMD_SUPPORTPOINT_ICON = os.path.join(iconPath, "cmdNewSupportPoint.svg")
CMD_SUPPORTLINE_ICON = os.path.join(iconPath, "cmdNewSupportLine.svg")
CMD_ATTACHINPLACE_ICON = os.path.join(iconPath, "cmdAttachInPlace.svg")
CMD_DEACTIVATEATTACHMENT_ICON = os.path.join(iconPath,
                                             "cmdDeactivateAttachment.svg")
CMD_ATTWIRETOTERMINAL_ICON = os.path.join(iconPath, "cmdAttWireToTerminal.svg")
CMD_DETWIREFROMTERMINAL_ICON = os.path.join(iconPath,
                                            "cmdDetWireFromTerminal.svg")

keyShorts = {'WireFlex': 'W, F',
             'AddVertex': 'W, A',
             'DelVertex': 'W, D',
             'AttachVertex': 'W, T',
             'RemoveVertexAttachment': 'W, R',
             'AttachWireToTerminal': 'T, A',
             'DetachWireFromTerminal': 'T, R',
             'CompoundPath': 'C, P',
             'Cable': 'C, B',
             'CableConduit': 'C, D',
             'CableBox': 'C, X',
             'CableConnector': 'C, N',
             'CableLightPoint': 'C, L',
             'ElectricalDevice': 'C, E',
             'SupportPoint': 'X, P',
             'SupportLine': 'X, L',
             'AttachInPlace': 'X, A',
             'DeactivateAttachment': 'X, D'
             }


class newWireFlexCommand:
    """Creates a WireFlex based on selected vertexes or objects
    """
    def Activated(self):
        sel = wireutils.processGuiSelection(False, Part.Vertex, None)
        s = wireutils.reprintSelection("doc", sel)
        c = "freecad.cables.wireFlex"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "WireFlex"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        if s is not None:
            FreeCADGui.doCommand(f"{c}.make_wireflex({s})")
        else:
            vlist = "[FreeCAD.Vector(0,0,0), FreeCAD.Vector(50,0,0)]"
            FreeCADGui.doCommand(f"{c}.make_wireflex_from_vectors({vlist})")
            FreeCAD.Console.PrintWarning(
                translate("Cables", "Default wireFlex object created."))
        FreeCADGui.doCommand("doc.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_NEW_WIRE_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_WireFlex",
                                              "WireFlex"),
                "Accel": keyShorts['WireFlex'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_WireFlex", "It creates a new line based on " +
                    "selected vertexes/objects. At least two vertexes" +
                    "/objects have to be selected first. If only one object " +
                    "is selected, a copy of it will be created.")}


class addVertexCommand:
    """Creates a new vertex in the middle of selected WireFlex edge
    """
    def Activated(self):
        sel = wireutils.processGuiSelection(True, Part.Edge, wireFlex.WireFlex)
        s = wireutils.reprintSelection("doc", sel)
        c = "freecad.cables.wireutils"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Add Vertex"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.addPointToWire({s})")
        FreeCADGui.doCommand("doc.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_ADD_VERTEX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_AddVertex",
                                              "Add Vertex"),
                "Accel": keyShorts['AddVertex'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_AddVertex", "It adds a new vertex to selected " +
                    "edge of Wire Flex")}


class delVertexCommand:
    """Deletes selected vertex from WireFlex
    """
    def Activated(self):
        sel = wireutils.processGuiSelection(True, Part.Vertex,
                                            wireFlex.WireFlex)
        s = wireutils.reprintSelection("doc", sel)
        c = "freecad.cables.wireutils"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Delete Vertex"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.delPointFromWire({s})")
        FreeCADGui.doCommand("doc.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_DEL_VERTEX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_DelVertex",
                                              "Delete Vertex"),
                "Accel": keyShorts['DelVertex'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_DelVertex", "It deletes selected vertex from " +
                    "Wire Flex")}


class assignAttachmentCommand:
    """Makes an attachment of selected WireFlex vertex to external vertex
    or object
    """
    def Activated(self):
        sel = wireutils.processGuiSelection(False, Part.Vertex,
                                            wireFlex.WireFlex)
        s = wireutils.reprintSelection("doc", sel)
        c = "freecad.cables.wireutils"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Attach Vertex"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.assignPointAttachment({s})")
        FreeCADGui.doCommand("doc.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_ATT_VERTEX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_AttachVertex",
                                              "Attach Vertex"),
                "Accel": keyShorts['AttachVertex'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_AttachVertex", "It attaches a Wire Flex vertex " +
                    "to external vertex or object. Select Wire Flex vertex " +
                    "first then ext. vertex (or entire object)")}


class removeAttachmentCommand:
    """Removes attachment from selected WireFlex vertex
    """
    def Activated(self):
        sel = wireutils.processGuiSelection(True, Part.Vertex,
                                            wireFlex.WireFlex)
        s = wireutils.reprintSelection("doc", sel)
        c = "freecad.cables.wireutils"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Remove Vertex Attachment"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.removePointAttachment({s})")
        FreeCADGui.doCommand("doc.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_RM_ATT_VERTEX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_RemoveVertexAttachment",
                                              "Remove Vertex Attachment"),
                "Accel": keyShorts['RemoveVertexAttachment'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_RemoveVertexAttachment", "It removes an " +
                    "attachment of external vertex or object from selected " +
                    "Wire Flex vertex")}


class newCompoundPathCommand:
    """Creates a CompoundPath based on selected objects
    """
    def Activated(self):
        sel_obj = Gui.Selection.getSelection()
        s = wireutils.reprintSelection("doc", sel_obj)
        c = "freecad.cables.compoundPath"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "CompoundPath"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.make_compoundpath({s})")
        FreeCADGui.doCommand("doc.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_COMPOUNDPATH_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_CompoundPath",
                                              "CompoundPath"),
                "Accel": keyShorts['CompoundPath'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_CompoundPath", "It creates a new compound path " +
                    "based on selected objects. At least two objects have " +
                    "to be selected first")}


class newCableCommand:
    def Activated(self):
        sel_obj = Gui.Selection.getSelection()
        s = wireutils.reprintSelection("doc", sel_obj)
        c = "freecad.cables.archCable"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.makeCable(selectlist={s})")
        FreeCADGui.doCommand("doc.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLE_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_Cable",
                                              "Cable"),
                "Accel": keyShorts['Cable'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_Cable", "It adds a new cable object from " +
                    "WireFlex and a profile. Select WireFlex object first " +
                    "(or sequence of wires, cables or conduits) then " +
                    "optionally a profile at the end")}


class newCableConduitCommand:
    def Activated(self):
        sel_obj = Gui.Selection.getSelection()
        s = wireutils.reprintSelection("doc", sel_obj)
        c = "freecad.cables.archCableConduit"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "CableConduit"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.makeCableConduit(selectlist={s})")
        FreeCADGui.doCommand("doc.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLECONDUIT_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_CableConduit",
                                              "CableConduit"),
                "Accel": keyShorts['CableConduit'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_CableConduit", "It adds a new cable conduit " +
                    "object from single WireFlex or sequence of wires " +
                    "(and optionally profile). Select single " +
                    "WireFlex object (or sequence of wires, cables or " +
                    "conduits) then optionally a profile at the end")}


class newCableBoxCommand:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        c = "freecad.cables.archCableBox"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Box"))
        lst_before = doc.findObjects(Name="CableBox")
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand("pl = FreeCAD.Placement()")
            FreeCADGui.doCommand(f"pl.Base = FreeCAD.{pos_vect}")
            FreeCADGui.doCommand(f"obj = {c}.makeCableBox(placement=pl)")
        else:
            FreeCADGui.doCommand(f"obj = {c}.makeCableBox()")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        lst_after = doc.findObjects(Name="CableBox")
        obj = list(set(lst_after)-set(lst_before))[0]
        panel = archCableBox.TaskPanelCableBox(obj)
        FreeCADGui.Control.showDialog(panel)
        # the below commitTransaction is made inside panel
        # doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLEBOX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_CableBox",
                                              "Cable Box"),
                "Accel": keyShorts['CableBox'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_CableBox", "It adds a new cable box object. " +
                    "Select any point in 3D view first, then add the box")}


class newCableConnectorCommand:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        c = "freecad.cables.archCableConnector"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Connector"))
        lst_before = doc.findObjects(Name="CableConnector")
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand("pl = FreeCAD.Placement()")
            FreeCADGui.doCommand(f"pl.Base = FreeCAD.{pos_vect}")
            FreeCADGui.doCommand(f"obj = {c}.makeCableConnector(placement=pl)")
        else:
            FreeCADGui.doCommand(f"obj = {c}.makeCableConnector()")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        lst_after = doc.findObjects(Name="CableConnector")
        obj = list(set(lst_after)-set(lst_before))[0]
        panel = archCableConnector.TaskPanelCableConnector(obj)
        FreeCADGui.Control.showDialog(panel)
        # the below commitTransaction is made inside panel
        # doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLECONNECTOR_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_CableConnector",
                                              "Cable Connector"),
                "Accel": keyShorts['CableConnector'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_CableConnector", "It adds a new cable " +
                    "connector object. Select any point in 3D view first, " +
                    "then add the connector")}


class newProfileCommand:
    def Activated(self):
        panel = cableProfile.TaskPanelProfile()
        FreeCADGui.Control.showDialog(panel)
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLEPROFILE_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_Profile",
                                              "Cable Profile"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_Profile", "It adds a new cable profile")}


class newMaterialCommand:
    def Activated(self):
        c = "freecad.cables.cableMaterial"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Materials"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand(f"{c}.makeCableMaterials()")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLEMATERIAL_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_Material",
                                              "Cable Materials"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_Material", "It adds new multimaterials for " +
                    "cables")}


class newCableLightPoint:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        c = "freecad.cables.archCableLightPoint"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Light Point"))
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand("pl = FreeCAD.Placement()")
            FreeCADGui.doCommand(f"pl.Base = FreeCAD.{pos_vect}")
            FreeCADGui.doCommand(f"{c}.makeCableLightPoint(placement=pl)")
        else:
            FreeCADGui.doCommand(f"{c}.makeCableLightPoint()")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLELIGHTPOINT_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_CableLightPoint",
                                              "Cable Light Point"),
                "Accel": keyShorts['CableLightPoint'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_CableLightPoint", "It adds a new light point " +
                    "for cable. Select any point in 3D view first, then add " +
                    "the light point")}


class newElectricalDevice:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        c = "freecad.cables.archElectricalDevice"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Electrical Device"))
        lst_before = doc.findObjects(Name="ElectricalDevice")
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand("pl = FreeCAD.Placement()")
            FreeCADGui.doCommand(f"pl.Base = FreeCAD.{pos_vect}")
            FreeCADGui.doCommand("obj = " +
                                 f"{c}.makeElectricalDevice(placement=pl)")
        else:
            FreeCADGui.doCommand(f"obj = {c}.makeElectricalDevice()")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        lst_after = doc.findObjects(Name="ElectricalDevice")
        obj = list(set(lst_after)-set(lst_before))[0]
        panel = archElectricalDevice.TaskPanelElectricalDevice(obj)
        FreeCADGui.Control.showDialog(panel)
        # the below commitTransaction is made inside panel
        # doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_ELECTRICALDEVICE_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_ElectricalDevice",
                                              "Electrical Device"),
                "Accel": keyShorts['ElectricalDevice'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_ElectricalDevice", "It adds a new electrical " +
                    "device. Select any point in 3D view first, then add " +
                    "the device")}


class newSupportPoint:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        c = "freecad.cables.cableSupport"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Support Point"))
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand("pl = FreeCAD.Placement()")
            FreeCADGui.doCommand(f"pl.Base = FreeCAD.{pos_vect}")
            FreeCADGui.doCommand(f"{c}.makeSupportPoint(placement=pl)")
        else:
            FreeCADGui.doCommand(f"{c}.makeSupportPoint()")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_SUPPORTPOINT_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_SupportPoint",
                                              "Support Point"),
                "Accel": keyShorts['SupportPoint'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_SupportPoint", "It adds a new support point " +
                    "to which a cable or other element can be attached")}


class newSupportLine:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        c = "freecad.cables.cableSupport"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Support Line"))
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 1:
            p1 = sel_obj[0].PickedPoints[0]
            p2 = sel_obj[1].PickedPoints[0]
            FreeCADGui.doCommand(f"{c}.makeSupportLine(" +
                                 f"FreeCAD.{p1}, FreeCAD.{p2})")
        elif len(sel_obj) == 1:
            p1 = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand(
                f"{c}.makeSupportLine(FreeCAD.{p1})")
        else:
            FreeCADGui.doCommand(f"{c}.makeSupportLine()")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_SUPPORTLINE_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_SupportLine",
                                              "Support Line"),
                "Accel": keyShorts['SupportLine'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_SupportLine", "It adds a new support line to " +
                    "which a cable or other element can be attached. Select " +
                    "at least one point first")}


class attachInPlace:
    def Activated(self):
        sel_obj = Gui.Selection.getSelection()
        s = wireutils.reprintSelection("doc", sel_obj)
        c = "freecad.cables.cableutils"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Attach In Place"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.attach_in_place({s})")
        #FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_ATTACHINPLACE_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_AttachInPlace",
                                              "Attach In Place"),
                "Accel": keyShorts['AttachInPlace'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_AttachInPlace", "It makes attachment without " +
                    "changing global placement of an object. Select " +
                    "objects to attach then at the end the object which " +
                    "will be the attachment support for them")}


class deactivateAttachment:
    def Activated(self):
        sel_obj = Gui.Selection.getSelection()
        s = wireutils.reprintSelection("doc", sel_obj)
        c = "freecad.cables.cableutils"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Deactivate Attachment"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.deactivate_attachment({s})")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_DEACTIVATEATTACHMENT_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_DeactivateAttachment",
                                              "Deactivate Attachment"),
                "Accel": keyShorts['DeactivateAttachment'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_DeactivateAttachment", "It daeactivates " +
                    "attachment of selected objects")}


class attachWireToTerminal:
    def Activated(self):
        sel = wireutils.processGuiSelection(False, Part.Vertex,
                                            wireFlex.WireFlex)
        try:
            vec = Gui.Selection.getSelectionEx()[0].PickedPoints[0]
            side = cableutils.detect_selected_wire_side(sel, vec)
        except (IndexError, ValueError):
            FreeCAD.Console.PrintError("attach_wire_to_terminal",
                                       "Selected object side not detected. " +
                                       "Please select vertex or edge of " +
                                       "wireFlex object in 3D view.\n")
            side = None
        if side is not None:
            s = wireutils.reprintSelection("doc", sel)
            c = "freecad.cables.cableutils"
            doc = FreeCAD.ActiveDocument
            doc.openTransaction(translate("Cables", "Attach Wire To Terminal"))
            FreeCADGui.addModule(f"{c}")
            FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
            FreeCADGui.doCommand(f"{c}.attach_wire_to_terminal({s}, '{side}')")
            FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
            doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_ATTWIRETOTERMINAL_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_AttachWireToTerminal",
                                              "Attach Wire To Terminal"),
                "Accel": keyShorts['AttachWireToTerminal'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_AttachWireToTerminal", "It makes attachment of " +
                    "wire end to the terminal. Select vertex or edge of " +
                    "WireFlex object in 3D view then select the Terminal or " +
                    "its vertex")}


class detachWireFromTerminal:
    def Activated(self):
        sel_obj = Gui.Selection.getSelection()
        s = wireutils.reprintSelection("doc", sel_obj)
        c = "freecad.cables.cableutils"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Detach Wire From Terminal"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.detach_wire_from_terminal({s})")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_DETWIREFROMTERMINAL_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_DetachWireFromTerminal",
                                              "Detach Wire From Terminal"),
                "Accel": keyShorts['DetachWireFromTerminal'],
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_AttachWireToTerminal", "It removes wire end " +
                    "attachment from the terminal. Select WireFlex then " +
                    "Terminal")}


Gui.addCommand('Cables_WireFlex', newWireFlexCommand())
Gui.addCommand('Cables_AddVertex', addVertexCommand())
Gui.addCommand('Cables_DelVertex', delVertexCommand())
Gui.addCommand('Cables_AttachVertex', assignAttachmentCommand())
Gui.addCommand('Cables_RemoveVertexAttachment', removeAttachmentCommand())
Gui.addCommand('Cables_CompoundPath', newCompoundPathCommand())
Gui.addCommand('Cables_Cable', newCableCommand())
Gui.addCommand('Cables_CableConduit', newCableConduitCommand())
Gui.addCommand('Cables_CableBox', newCableBoxCommand())
Gui.addCommand('Cables_CableConnector', newCableConnectorCommand())
Gui.addCommand('Cables_Profile', newProfileCommand())
Gui.addCommand('Cables_Material', newMaterialCommand())
Gui.addCommand('Cables_CableLightPoint', newCableLightPoint())
Gui.addCommand('Cables_ElectricalDevice', newElectricalDevice())
Gui.addCommand('Cables_SupportPoint', newSupportPoint())
Gui.addCommand('Cables_SupportLine', newSupportLine())
Gui.addCommand('Cables_AttachInPlace', attachInPlace())
Gui.addCommand('Cables_DeactivateAttachment', deactivateAttachment())
Gui.addCommand('Cables_AttachWireToTerminal', attachWireToTerminal())
Gui.addCommand('Cables_DetachWireFromTerminal', detachWireFromTerminal())
