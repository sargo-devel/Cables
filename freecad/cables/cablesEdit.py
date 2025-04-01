"""Edit command used in Cables workbench.
This module is based on draftguitoos.gui_edit and adds some functionalities
needed by WireFlex class.
"""

import os
import FreeCAD
from FreeCAD import Gui
from draftguitools import gui_edit
from draftguitools import gui_edit_draft_objects
from freecad.cables import wireutils
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP

_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "resources/icons")
CMD_CABLESEDIT_ICON = os.path.join(iconPath, "cmdCablesEdit.svg")


class CablesEdit(gui_edit.Edit):
    """The Cables_Edit command definition.
    A tool to graphically edit WireFlex objects.
    """
    def __init__(self):
        super().__init__()
        self.gui_tools_repository.add('Wire', DraftWireFlexGuiTools())

    def Activated(self):
        FreeCAD.Console.PrintMessage("This is CablesEdit\n")
        if not hasattr(FreeCAD, 'activeDraftCommand'):
            wb_before_edit = Gui.activeWorkbench()
            Gui.activateWorkbench("DraftWorkbench")
            Gui.activateWorkbench(wb_before_edit.name())
        super().Activated()

    def GetResources(self):
        return {'Pixmap': CMD_CABLESEDIT_ICON,
                'Accel': "D, E",
                'MenuText': QT_TRANSLATE_NOOP("Cables_Edit", "Edit"),
                'ToolTip': QT_TRANSLATE_NOOP(
                    "Cables_Edit", "Edits the active object.\nPress E or "
                    "ALT + Left Click to display context menu\non supported " +
                    "nodes and on supported objects.")
                }


class DraftWireFlexGuiTools(gui_edit_draft_objects.DraftWireGuiTools):
    def __init__(self):
        super().__init__()
        # FreeCAD.Console.PrintMessage("This is DraftWireFlexGuiTools\n")

    def get_edit_point_context_menu(self, edit_command, obj, node_idx):
        if self.is_node_attached(obj, node_idx):
            return [
                (translate("Cables", "Delete point"),
                 lambda: self.delete_point(obj, node_idx)),
                (self.get_detach_menu_text(obj),
                 lambda: self.detach_point(obj, node_idx)),
            ]
        else:
            return [
                (translate("Cables", "Delete point"),
                 lambda: self.delete_point(obj, node_idx)),
                (self.get_attach_menu_text(obj),
                 lambda: self.attach_point(obj, node_idx)),
            ]

    def get_edit_obj_context_menu(self, edit_command, obj, position):
        return [
            (translate("Cables", "Add point"),
             lambda: self.add_point(edit_command, obj, position)),
            (self.get_reverse_menu_text(obj), lambda: self.reverse_wire(obj)),
            (self.get_horizontal_menu_text(obj),
             lambda: self.horizontal_wire_edge(edit_command, obj, position)),
            (self.get_vertical_menu_text(obj),
             lambda: self.vertical_wire_edge(edit_command, obj, position)),
        ]

    def get_attach_menu_text(self, obj):
        """This function is overridden in the DraftBSplineGuiTools class.
        """
        return translate("Cables", "Attach point")

    def get_detach_menu_text(self, obj):
        """This function is overridden in the DraftBSplineGuiTools class.
        """
        return translate("Cables", "Remove point attachment")

    def get_horizontal_menu_text(self, obj):
        """This function is overridden in the DraftBSplineGuiTools class.
        """
        return translate("Cables", "Make edge horizontal")

    def get_vertical_menu_text(self, obj):
        """This function is overridden in the DraftBSplineGuiTools class.
        """
        return translate("Cables", "Make edge vertical")

    def add_point(self, edit_command, obj, pos):
        # FreeCAD.Console.PrintMessage(f"edit_command={edit_command}\n")
        # FreeCAD.Console.PrintMessage(f"obj={obj}\n")
        # FreeCAD.Console.PrintMessage(f"pos={pos}\n")
        # FreeCAD.Console.PrintMessage(f"posxy={pos[0]},{pos[1]}\n")
        info, newPoint = edit_command.get_specific_object_info(obj, pos)
        # FreeCAD.Console.PrintMessage(f"info={info}\n")
        # FreeCAD.Console.PrintMessage(f"newPoint={newPoint}\n")
        wireutils.addPointToWire([(obj, info["Component"])], point=newPoint)
        obj.recompute(True)

    def delete_point(self, obj, node_idx):
        wireutils.delPointFromWire([(obj, None)], point_idx=node_idx)
        obj.recompute(True)

    def attach_point(self, obj, node_idx):
        wireutils.assignPointAttachment(plist=None, point_idx=node_idx,
                                        obj=obj)
        obj.recompute(True)

    def detach_point(self, obj, node_idx):
        wireutils.removePointAttachment(plist=None, point_idx=node_idx,
                                        obj=obj)
        obj.recompute(True)

    def reverse_wire(self, obj):
        wireutils.reverseWire(obj)
        obj.recompute(True)

    def horizontal_wire_edge(self, edit_command, obj, pos):
        info, newPoint = edit_command.get_specific_object_info(obj, pos)
        wireutils.modifyWireEdge([(obj, info["Component"])], point=newPoint,
                                 cmd='horizontal')
        obj.recompute(True)

    def vertical_wire_edge(self, edit_command, obj, pos):
        info, newPoint = edit_command.get_specific_object_info(obj, pos)
        wireutils.modifyWireEdge([(obj, info["Component"])], point=newPoint,
                                 cmd='vertical')
        obj.recompute(True)

    def is_node_attached(self, obj, node_idx):
        att_list = []
        att_list.append(1) if obj.Vrtx_start else None
        att_list.extend(obj.Vrtxs_mid_idx)
        att_list.append(len(obj.Points)) if obj.Vrtx_end else None
        is_attached = node_idx+1 in att_list
        return is_attached


Gui.addCommand('Cables_Edit', CablesEdit())
