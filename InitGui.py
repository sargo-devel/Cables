# ***************************************************************************
# *   Copyright 2024 SargoDevel <sargo-devel at o2 dot pl>                  *
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
from draftguitools import gui_grid
from draftguitools import gui_selectplane

# Add translations path
import FreeCADGui
from commonutils import languagePath
FreeCADGui.addLanguagePath(languagePath)
FreeCADGui.updateLocale()


class CablesWorkbench (Workbench):

    MenuText = "Cables"
    ToolTip = "Create cable connections"
    from commonutils import iconPath
    Icon = os.path.join(iconPath, "CablesLogo.svg")

    def Initialize(self):
        """This function is executed when the workbench is first activated.
        It is executed once in a FreeCAD sessionfollowed by the Activated
        function.
        """
        import commands
        from commonutils import QT_TRANSLATE_NOOP
        self.list_wires = ["Cables_NewWireFlex",
                           "Cables_AddVertex",
                           "Cables_DelVertex",
                           "Cables_AttachVertex",
                           "Cables_RemoveVertexAttachment"]
        self.list_cables = ["Cables_NewProfile",
                            "Cables_NewCable",
                            "Cables_NewCableBox",
                            "Cables_NewCableConnector",
                            "Cables_NewCableLightPoint",
                            "Cables_NewMaterial"]
        self.list_support = ["Cables_NewSupportPoint",
                             "Cables_NewSupportLine"]
        self.list_draft = ["Draft_ToggleGrid",
                           # "Draft_SelectPlane"]
                           ]
        self.appendToolbar(QT_TRANSLATE_NOOP("Workbench", "Cable Wires"),
                           self.list_wires)
        self.appendToolbar(QT_TRANSLATE_NOOP("Workbench", "Cables"),
                           self.list_cables)
        self.appendToolbar(QT_TRANSLATE_NOOP("Workbench", "Cable Support"),
                           self.list_support)
        self.appendToolbar(QT_TRANSLATE_NOOP("Workbench", "Draft Tools"),
                           self.list_draft)
        self.appendMenu(QT_TRANSLATE_NOOP("Workbench", "Cable Wires"),
                        self.list_wires)
        self.appendMenu(QT_TRANSLATE_NOOP("Workbench", "Cables"),
                        self.list_cables)
        self.appendMenu(QT_TRANSLATE_NOOP("Workbench", "Cable Support"),
                        self.list_support)
        # self.appendMenu(["An existing Menu", "My submenu"], self.list) # appends a submenu to an existing menu

    def Activated(self):
        """This function is executed whenever the workbench is activated"""
        import WorkingPlane
        WorkingPlane.get_working_plane()
        return

    def Deactivated(self):
        """This function is executed whenever the workbench is deactivated"""
        return

    def ContextMenu(self, recipient):
        """This function is executed whenever the user right-clicks on screen
        """
        # "recipient" will be either "view" or "tree"
        from commonutils import QT_TRANSLATE_NOOP
        self.appendContextMenu(QT_TRANSLATE_NOOP("Workbench", "Cable Wires"),
                               self.list_wires)
        self.appendContextMenu(QT_TRANSLATE_NOOP("Workbench", "Cables"),
                               self.list_cables)
        self.appendContextMenu(QT_TRANSLATE_NOOP("Workbench", "Cable Support"),
                               self.list_support)

    def GetClassName(self):
        # This function is mandatory if this is a full Python workbench
        # This is not a template,
        # the returned string should be exactly "Gui::PythonWorkbench"
        return "Gui::PythonWorkbench"


Gui.addWorkbench(CablesWorkbench())
