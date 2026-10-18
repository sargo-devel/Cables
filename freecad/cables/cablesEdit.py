"""Edit command used in Cables workbench.
This module is based on draftguitoos.gui_edit and adds some functionalities
needed by WireFlex class.
"""

# ***************************************************************************
# *   Copyright 2025 SargoDevel <sargo-devel at o2 dot pl>                  *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENSE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Lesser General Public License for more details.                   *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************/


import os
import FreeCAD
from FreeCAD import Gui
from draftutils import utils
from draftguitools import gui_edit
from draftguitools import gui_edit_draft_objects
from freecad.cables import wireutils
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP
from freecad.cables.archCable import ArchCable

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
        self.gui_tools_repository.add('Pipe', CableFlexGuiTools())

    def Activated(self):
        # FreeCAD.Console.PrintMessage("This is CablesEdit\n")
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
                    "ALT + Left Click or ALT + Left DubleClick\nto display " +
                    "context menu on supported nodes\nand on supported " +
                    "objects.")
                }

    def get_selected_obj_at_position(self, pos):
        """This is a copy of the super-class method, except that it will also
        match an edited Cable if the selected object is the base Wire.
        """
        selobjs = self.view.getObjectsInfo(tuple(pos))
        if not selobjs:
            return
        for info in selobjs:
            name = info["Object"]
            if not info:
                return
            for obj in self.edited_objects:
                if obj.Name == name or (hasattr(obj, "Base") and obj.Base.Name == name):
                    return obj

    def getObjsFromSelection(self):
        edit_objects = super().getObjsFromSelection()
        # Since both Cables and Pipes have a type of "Pipe", the above call will
        # return both types of objects.  We need to filter out the non-Cable
        # Pipes here.
        self.edited_objects = []
        for obj in edit_objects:
            if utils.get_type(obj) == "Pipe" and not isinstance(obj.Proxy, ArchCable):
                _wrn = translate("draft", ": this object is not editable")
                FreeCAD.Console.PrintWarning(obj.Name + _wrn + "\n")
            else:
                self.edited_objects.append(obj)
        return self.edited_objects

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
            (self.get_coaxial_menu_text(obj),
             lambda: self.coaxial_wire_edge(edit_command, obj, position)),
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

    def get_coaxial_menu_text(self, obj):
        """This function is overridden in the DraftBSplineGuiTools class.
        """
        return translate("Cables", "Make edge coaxial")

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

    def coaxial_wire_edge(self, edit_command, obj, pos):
        info, newPoint = edit_command.get_specific_object_info(obj, pos)
        wireutils.modifyWireEdge([(obj, info["Component"])], point=newPoint,
                                 cmd='coaxial')
        obj.recompute(True)

    def is_node_attached(self, obj, node_idx):
        att_list = []
        att_list.append(1) if obj.Vrtx_start else None
        att_list.extend(obj.Vrtxs_mid_idx)
        att_list.append(len(obj.Points)) if obj.Vrtx_end else None
        is_attached = node_idx+1 in att_list
        return is_attached

class CableFlexGuiTools(DraftWireFlexGuiTools):
    """This wraps the external methods of GuiTools so that they call the super
    class methods with obj → obj.Base.  Effectively, they act on the ArchWire that
    is the base of the Cable. 
    The editing style of the Cable is set to be transparent and non-selectable,
    so the Wire inside it can be seen and selected.
    """

    def get_edit_points(self, obj):
        return super().get_edit_points(obj.Base)

    def update_object_from_edit_points(self, obj, node_idx, v, alt_edit_mode=0):
        super().update_object_from_edit_points(obj.Base, node_idx, v, alt_edit_mode)
        # Draft edit tool will recompute obj, but not obj.Base
        obj.Base.recompute()

    def get_edit_point_context_menu(self, edit_command, obj, node_idx):
        return super().get_edit_point_context_menu(edit_command, obj.Base, node_idx)

    def get_edit_obj_context_menu(self, edit_command, obj, position):
        return super().get_edit_obj_context_menu(edit_command, obj.Base, position)

    def get_object_style(self, obj):
        return (obj.ViewObject.Transparency, obj.ViewObject.DrawStyle, obj.ViewObject.Selectable)

    def restore_object_style(self, obj, modes):
        obj.ViewObject.Transparency, obj.ViewObject.DrawStyle, obj.ViewObject.Selectable = modes

    def set_object_editing_style(self, obj):
        obj.ViewObject.Transparency = 80
        obj.ViewObject.DrawStyle = "Dotted"
        obj.ViewObject.Selectable = False

    def init_preview_object(self, obj):
        return super().init_preview_object(obj.Base)

    def update_preview_object(self, edit_command, obj, node_idx, v):
        super().update_preview_object(edit_command, obj.Base, node_idx, v)

Gui.addCommand('Cables_Edit', CablesEdit())
