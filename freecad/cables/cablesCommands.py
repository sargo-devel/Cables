"""commands used in Cables workbench
"""

import os
import FreeCAD
import FreeCADGui
from FreeCAD import Gui
import Part
from freecad.cables import wireutils
from freecad.cables import archCable
from freecad.cables import archCableBox
from freecad.cables import archCableConnector
from freecad.cables import archCableLightPoint
from freecad.cables import wireFlex
from freecad.cables import cableProfile
from freecad.cables import cableMaterial
from freecad.cables import cableSupport
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
CMD_SUPPORTPOINT_ICON = os.path.join(iconPath, "cmdNewSupportPoint.svg")
CMD_SUPPORTLINE_ICON = os.path.join(iconPath, "cmdNewSupportLine.svg")

keyShorts = {'WireFlex': 'W, F',
             'AddVertex': 'W, A',
             'DelVertex': 'W, D',
             'AttachVertex': 'W, T',
             'RemoveVertexAttachment': 'W, R',
             'CompoundPath': 'C, P',
             'Cable': 'C, B',
             'CableConduit': 'C, D',
             'CableBox': 'C, X',
             'CableConnector': 'C, N',
             'CableLightPoint': 'C, L',
             'SupportPoint': 'X, P',
             'SupportLine': 'X, L',
             }


class newWireFlexCommand:
    """Creates a WireFlex based on selected vertexes or objects
    """
    def Activated(self):
        sel = wireutils.processGuiSelection(False, Part.Vertex, None)
        s = wireutils.reprintSelection("doc", sel)
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "WireFlex"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.wireFlex.make_wireflex({s})")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Add Vertex"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.wireutils.addPointToWire({s})")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Delete Vertex"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.wireutils.delPointFromWire({s})")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Attach Vertex"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.wireutils.assignPointAttachment({s})")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Remove Vertex Attachment"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.wireutils.removePointAttachment({s})")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "CompoundPath"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.compoundPath.make_compoundpath({s})")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.archCable.makeCable(selectlist={s})")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "CableConduit"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand("doc = FreeCAD.ActiveDocument")
        FreeCADGui.doCommand(f"{c}.archCableConduit.makeCableConduit(" +
                             f"selectlist={s})")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Box"))
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand("pl = FreeCAD.Placement()")
            FreeCADGui.doCommand(f"pl.Base = FreeCAD.{pos_vect}")
            FreeCADGui.doCommand(f"{c}.archCableBox.makeCableBox(" +
                                 "placement=pl)")
        else:
            FreeCADGui.doCommand(f"{c}.archCableBox.makeCableBox()")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()

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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Connector"))
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand("pl = FreeCAD.Placement()")
            FreeCADGui.doCommand(f"pl.Base = FreeCAD.{pos_vect}")
            FreeCADGui.doCommand(
                f"{c}.archCableConnector.makeCableConnector(placement=pl)")
        else:
            FreeCADGui.doCommand(
                f"{c}.archCableConnector.makeCableConnector()")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()

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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Materials"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand(f"{c}.cableMaterial.makeCableMaterials()")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Light Point"))
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand("pl = FreeCAD.Placement()")
            FreeCADGui.doCommand(f"pl.Base = FreeCAD.{pos_vect}")
            FreeCADGui.doCommand(
                f"{c}.archCableLightPoint.makeCableLightPoint(placement=pl)")
        else:
            FreeCADGui.doCommand(
                f"{c}.archCableLightPoint.makeCableLightPoint()")
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


class newSupportPoint:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Support Point"))
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand("pl = FreeCAD.Placement()")
            FreeCADGui.doCommand(f"pl.Base = FreeCAD.{pos_vect}")
            FreeCADGui.doCommand(
                f"{c}.cableSupport.makeSupportPoint(placement=pl)")
        else:
            FreeCADGui.doCommand(f"{c}.cableSupport.makeSupportPoint()")
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
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Support Line"))
        FreeCADGui.addModule(f"{c}")
        if len(sel_obj) > 1:
            p1 = sel_obj[0].PickedPoints[0]
            p2 = sel_obj[1].PickedPoints[0]
            FreeCADGui.doCommand(f"{c}.cableSupport.makeSupportLine(" +
                                 f"FreeCAD.{p1}, FreeCAD.{p2})")
        elif len(sel_obj) == 1:
            p1 = sel_obj[0].PickedPoints[0]
            FreeCADGui.doCommand(
                f"{c}.cableSupport.makeSupportLine(FreeCAD.{p1})")
        else:
            FreeCADGui.doCommand(f"{c}.cableSupport.makeSupportLine()")
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
Gui.addCommand('Cables_SupportPoint', newSupportPoint())
Gui.addCommand('Cables_SupportLine', newSupportLine())
