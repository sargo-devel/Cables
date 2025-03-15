"""commands used in Cables workbench
"""

import os
import FreeCAD
import FreeCADGui
from FreeCAD import Gui
import Part
import wireutils
import archCable
import archCableBox
import archCableConnector
import archCableLightPoint
import wireFlex
import cableProfile
import cableMaterial
import cableSupport
from commonutils import QT_TRANSLATE_NOOP


_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "resources/icons")
CMD_NEW_WIRE_ICON = os.path.join(iconPath, "cmdNewWire.svg")
CMD_ADD_VERTEX_ICON = os.path.join(iconPath, "cmdAddVertex.svg")
CMD_DEL_VERTEX_ICON = os.path.join(iconPath, "cmdDelVertex.svg")
CMD_ATT_VERTEX_ICON = os.path.join(iconPath, "cmdAttVertex.svg")
CMD_RM_ATT_VERTEX_ICON = os.path.join(iconPath, "cmdRmAttVertex.svg")
CMD_CABLE_ICON = os.path.join(iconPath, "cmdNewCable.svg")
CMD_CABLEBOX_ICON = os.path.join(iconPath, "cmdNewCableBox.svg")
CMD_CABLECONNECTOR_ICON = os.path.join(iconPath, "cmdNewCableConnector.svg")
CMD_CABLEPROFILE_ICON = os.path.join(iconPath, "cmdNewCableProfile.svg")
CMD_CABLEMATERIAL_ICON = os.path.join(iconPath, "cmdNewCableMaterial.svg")
CMD_CABLELIGHTPOINT_ICON = os.path.join(iconPath, "cmdNewCableLightPoint.svg")
CMD_SUPPORTPOINT_ICON = os.path.join(iconPath, "cmdNewSupportPoint.svg")
CMD_SUPPORTLINE_ICON = os.path.join(iconPath, "cmdNewSupportLine.svg")


class newWireFlexCommand:
    """Creates a WireFlex based on selected vertexes or objects
    """
    def Activated(self):
        sel = wireutils.processGuiSelection(False, Part.Vertex, None)
        wireFlex.make_wireflex(sel)
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_NEW_WIRE_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_WireFlex",
                                              "WireFlex"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_WireFlex", "It creates a new line based on " +
                    "selected vertexes/objects. At least two vertexes" +
                    "/objects have to be selected first")}


class addVertexCommand:
    """Creates a new vertex in the middle of selected WireFlex edge
    """
    def Activated(self):
        sel = wireutils.processGuiSelection(True, Part.Edge, wireFlex.WireFlex)
        wireutils.addPointToWire(sel)
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_ADD_VERTEX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_AddVertex",
                                              "Add Vertex"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_AddVertex", "It adds a new vertex to selected " +
                    "edge of Wire Flex")}


class delVertexCommand:
    """Deletes selected vertex from WireFlex
    """
    def Activated(self):
        sel = wireutils.processGuiSelection(True, Part.Vertex,
                                            wireFlex.WireFlex)
        wireutils.delPointFromWire(sel)
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_DEL_VERTEX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_DelVertex",
                                              "Delete Vertex"),
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
        wireutils.assignPointAttachment(sel)
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_ATT_VERTEX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_AttachVertex",
                                              "Attach Vertex"),
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
        wireutils.removePointAttachment(sel)
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_RM_ATT_VERTEX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_RemoveVertexAttachment",
                                              "Remove Vertex Attachment"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_RemoveVertexAttachment", "It removes an " +
                    "attachment of external vertex or object from selected " +
                    "Wire Flex vertex")}


class newCableCommand:
    def Activated(self):
        sel_obj = Gui.Selection.getSelection()
        if len(sel_obj) > 1:
            archCable.makeCable(sel_obj[0], sel_obj[1])
        else:
            archCable.makeCable(sel_obj[0])
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLE_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_Cable",
                                              "Cable"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_Cable", "It adds a new cable object from " +
                    "WireFlex and profile. Select WireFlex object first " +
                    "then a profile")}


class newCableBoxCommand:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            pl = FreeCAD.Placement()
            pl.Base = pos_vect
            archCableBox.makeCableBox(placement=pl)
        else:
            archCableBox.makeCableBox()
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLEBOX_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_CableBox",
                                              "Cable Box"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_CableBox", "It adds a new cable box object. " +
                    "Select any point in 3D view first, then add the box")}


class newCableConnectorCommand:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            pl = FreeCAD.Placement()
            pl.Base = pos_vect
            archCableConnector.makeCableConnector(placement=pl)
        else:
            archCableConnector.makeCableConnector()
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLECONNECTOR_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_CableConnector",
                                              "Cable Connector"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_CableConnector", "It adds a new cable " +
                    "connector object. Select any point in 3D view first, " +
                    "then add the connector")}


class newProfileCommand:
    def Activated(self):
        #cableProfile.makeCableProfile()
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
        cableMaterial.makeCableMaterials()
        FreeCAD.ActiveDocument.recompute()

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
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            pl = FreeCAD.Placement()
            pl.Base = pos_vect
            archCableLightPoint.makeCableLightPoint(placement=pl)
        else:
            archCableLightPoint.makeCableLightPoint()
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_CABLELIGHTPOINT_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_CableLightPoint",
                                              "Cable Light Point"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_CableLightPoint", "It adds a new light point " +
                    "for cable. Select any point in 3D view first, then add " +
                    "the light point")}


class newSupportPoint:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        if len(sel_obj) > 0:
            pos_vect = sel_obj[0].PickedPoints[0]
            pl = FreeCAD.Placement()
            pl.Base = pos_vect
            cableSupport.makeSupportPoint(placement=pl)
        else:
            cableSupport.makeSupportPoint()
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_SUPPORTPOINT_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_SupportPoint",
                                              "Support Point"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_SupportPoint", "It adds a new support point " +
                    "to which a cable or other element can be attached")}


class newSupportLine:
    def Activated(self):
        sel_obj = Gui.Selection.getCompleteSelection()
        if len(sel_obj) > 1:
            p1 = sel_obj[0].PickedPoints[0]
            p2 = sel_obj[1].PickedPoints[0]
            cableSupport.makeSupportLine(p1, p2)
        elif len(sel_obj) == 1:
            p1 = sel_obj[0].PickedPoints[0]
            cableSupport.makeSupportLine(p1)
        else:
            cableSupport.makeSupportLine()
        FreeCAD.ActiveDocument.recompute()

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def GetResources(self):
        return {'Pixmap': CMD_SUPPORTLINE_ICON,
                'MenuText': QT_TRANSLATE_NOOP("Cables_SupportLine",
                                              "Support Line"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_SupportLine", "It adds a new support line to " +
                    "which a cable or other element can be attached. Select " +
                    "at least one point first")}


Gui.addCommand('Cables_WireFlex', newWireFlexCommand())
Gui.addCommand('Cables_AddVertex', addVertexCommand())
Gui.addCommand('Cables_DelVertex', delVertexCommand())
Gui.addCommand('Cables_AttachVertex', assignAttachmentCommand())
Gui.addCommand('Cables_RemoveVertexAttachment', removeAttachmentCommand())
Gui.addCommand('Cables_Cable', newCableCommand())
Gui.addCommand('Cables_CableBox', newCableBoxCommand())
Gui.addCommand('Cables_CableConnector', newCableConnectorCommand())
Gui.addCommand('Cables_Profile', newProfileCommand())
Gui.addCommand('Cables_Material', newMaterialCommand())
Gui.addCommand('Cables_CableLightPoint', newCableLightPoint())
Gui.addCommand('Cables_SupportPoint', newSupportPoint())
Gui.addCommand('Cables_SupportLine', newSupportLine())
