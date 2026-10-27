"""partsLibrary
"""

# ***************************************************************************
# *   Copyright 2026 SargoDevel <sargo-devel at o2 dot pl>                  *
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
import shutil
from pathlib import Path
import csv
import FreeCAD
import FreeCADGui
import ImportGui
import Import
import PySide

from freecad.cables import uiPath
from freecad.cables import libPath
from freecad.cables import presetsPath
from freecad.cables import archCableBaseElement
from freecad.cables import archCableBox
from freecad.cables import archCableConnector
from freecad.cables import archElectricalDevice
from freecad.cables import cableProfile
from freecad.cables.cableutils import logmsg
from freecad.cables import translate

ModuleName = __name__.split('.')[-1]
ui_library_part = os.path.join(uiPath, "library-part.ui")
ui_library_list = os.path.join(uiPath, "library-list.ui")


part_groups_tr_min = [
    translate("Cables", "Cable Connector"),
    translate("Cables", "Electrical Device"),
    translate("Cables", "Unknown")
    ]

step_options_tr = [
    translate("Cables", "Create from selected solid object"),
    translate("Cables", "Copy from source STEP file")]

tree_settings_lib_part = {
        "titles": [
            translate("Cables", "Name"),
            translate("Cables", "Element Type"),
            translate("Cables", "Class"),
            translate("Cables", "Parameters")],
        "column_widths": (200, 150, 100, 270)}

tree_settings_lib = {
        "titles": [
            translate("Cables", "Preset Full Name"),
            translate("Cables", "Element Type"),
            translate("Cables", "Parameters")],
        "column_widths": (300, 150, 400)}


class LibraryPartDialog:
    def __init__(self, selection, ui_library=ui_library_part):
        archCableBaseElement.lib_cache.reset()
        self.partData = PartData(selection)
        self.form = FreeCADGui.PySideUic.loadUi(ui_library)

        # default settings
        self.form.groupComboBox.addItems(self.partData.groups())
        self.form.stepComboBox.addItems(step_options_tr)
        self.form.overwriteButton.hide()
        self.form.detailsBox.hide()
        self.form.ignorePlacementCheckBox.hide()
        self.form.fileButton.setEnabled(False)
        self.form.fileButton.setDefault(False)
        self.form.fileEdit.setEnabled(False)
        self.form.runButton.setEnabled(True)
        self.form.ignorePlacementCheckBox.setChecked(
            self.partData.getIgnorePlacement())

        # tree view
        self.tree_model = PySide.QtGui.QStandardItemModel()
        self.form.tree.setModel(self.tree_model)
        self.form.tree.setUniformRowHeights(True)
        self.form.tree.setSelectionMode(
            self.form.tree.selectionMode().ExtendedSelection)
        # fileList view
        self.list_model = PySide.QtCore.QStringListModel()
        self.form.fileList.setModel(self.list_model)

        self.displayTreeAndList()

        # connect signals
        self.form.runButton.clicked.connect(self.runButtonClicked)
        self.form.cancelButton.clicked.connect(self.cancelButtonClicked)
        self.form.nameEdit.textChanged.connect(self.nameclassEditChanged)
        self.form.classEdit.textChanged.connect(self.nameclassEditChanged)
        self.form.detailsCheckBox.clicked.connect(self.detailsClicked)
        self.form.groupComboBox.currentIndexChanged.connect(self.groupChanged)
        self.form.stepComboBox.currentIndexChanged.connect(
            self.stepSourceChanged)
        self.form.ignorePlacementCheckBox.clicked.connect(
            self.ignorePlacementClicked)
        self.form.fileButton.clicked.connect(self.fileButtonSelected)
        self.form.fileEdit.textChanged.connect(self.fileEditChanged)
        self.form.overwriteButton.clicked.connect(
            lambda _: self.runButtonClicked(True))

        # icons
        style = self.form.style()
        std_pixmap = PySide.QtWidgets.QStyle.StandardPixmap
        self.icon_ok = style.standardIcon(std_pixmap.SP_DialogApplyButton)
        self.icon_error = style.standardIcon(std_pixmap.SP_MessageBoxCritical)
        pos = PySide.QtWidgets.QLineEdit.ActionPosition.TrailingPosition
        self.fileEditIcon = self.form.fileEdit.addAction(self.icon_error, pos)

        self.setDialogData()
        self.setWindow()
        self.form.show()

    def setWindow(self, w=720, h=200):
        self.form.layout().invalidate()
        self.form.layout().activate()
        self.form.adjustSize()
        self.form.resize(w, h)
        # center the dialog over FreeCAD window
        mw = FreeCADGui.getMainWindow()
        self.form.move(mw.frameGeometry().topLeft() + mw.rect().center()
                       - self.form.rect().center())

    def setDialogData(self):
        # Set part group
        if self.partData.data is None:
            message = translate("Cables", "Nothing was selected.")
            self.form.infoMessage.setText(message)
            self.disableAll()
            return
        else:
            group, group_tr = self.partData.getGroup()
            self.form.groupComboBox.setCurrentText(group_tr)
            if group == "Unknown":
                self.form.runButton.setEnabled(False)
                self.form.presetBox.setEnabled(False)
                self.form.detailsBox.setEnabled(False)
            else:
                self.form.runButton.setEnabled(True)
                self.form.presetBox.setEnabled(True)
                self.form.detailsBox.setEnabled(True)

        # Set ignorePlacementCheckBox visibility
        self.stepSourceChanged()

        # Set message and lock the part addidition
        if self.partData.data.get("ExtShape") is None:
            message = translate("Cables", "No object containing a solid " +
                                "shape was selected. The entry cannot be " +
                                "added to the library.")
            self.form.infoMessage.setText(message)
            self.disableAll()
            return

        # Set preset
        preset = self.partData.data.get("Preset")
        if preset is not None:
            el_class = preset[2]
            el_name = preset[0]
            self.form.classEdit.setText(el_class)
            self.form.nameEdit.setText(el_name)
            self.form.presetFullName.setText(f"{el_class}_{el_name}")

        # Set Step file options
        if not self.partData.isStepNeeded():
            self.form.stepGroupBox.hide()
        else:
            stepfile = self.partData.getStepFile()
            if stepfile is not None:
                self.form.stepComboBox.setCurrentIndex(1)
                self.form.fileEdit.setText(stepfile)
        return

    def cancelButtonClicked(self):
        self.form.close()

    def runButtonClicked(self, force=False):
        self.part = LibraryPart(self.partData.data)
        exists, libType = self.part.existsInLibrary()
        if exists:
            if libType == 0:
                message = translate("Cables", "Element already exists in " +
                                    "the built-in library. Please change " +
                                    "its name or class.")
            else:
                if force:
                    message = translate("Cables", "Element will be " +
                                        "overwritten in the local " +
                                        "library.")
                    self.form.overwriteButton.hide()
                else:
                    message = translate("Cables", "Element already exists " +
                                        "in the local library.")
                    self.form.overwriteButton.show()
            self.form.infoMessage.setText(message)
            if not force:
                return
        self.form.close()
        logmsg(f"Update cables local library:\n{self.partData.data}")
        self.part.updateLibrary()

    def nameclassEditChanged(self):
        el_class = self.form.classEdit.text()
        el_name = self.form.nameEdit.text()
        self.form.presetFullName.setText(f"{el_class}_{el_name}")
        self.partData.updatePreset(el_class, el_name)
        self.displayTreeAndList()
        self.form.overwriteButton.hide()
        self.form.infoMessage.setText("")

    def disableAll(self):
        self.form.groupComboBox.setEnabled(False)
        self.form.runButton.setEnabled(False)
        self.form.presetBox.setEnabled(False)
        self.form.detailsBox.hide()

    def detailsClicked(self):
        if self.form.detailsCheckBox.isChecked():
            self.form.detailsBox.show()
            self.setWindow(w=800)
        else:
            self.form.detailsBox.hide()
            self.form.layout().invalidate()
            self.form.layout().activate()
            self.form.resize(self.form.width(), 1)
            self.form.adjustSize()
            self.setWindow(w=720, h=100)

    def ignorePlacementClicked(self):
        ignore = self.form.ignorePlacementCheckBox.isChecked()
        self.partData.setIgnorePlacement(ignore)
        self.displayTreeAndList()

    def stepSourceChanged(self):
        idx = self.form.stepComboBox.currentIndex()

        # external source
        if idx == 1:
            self.form.fileButton.setEnabled(True)
            self.form.fileEdit.setEnabled(True)
            self.fileEditChanged()
            self.form.ignorePlacementCheckBox.setChecked(False)
            self.ignorePlacementClicked()
            self.form.ignorePlacementCheckBox.hide()
        # shape from document
        else:
            self.form.fileButton.setEnabled(False)
            self.form.fileEdit.setEnabled(False)
            self.form.ignorePlacementCheckBox.show()
            self.partData.setStepFile(None)
            self.form.runButton.setEnabled(True)

    def groupChanged(self):
        self.partData.setGroup(self.form.groupComboBox.currentText())
        group, _ = self.partData.getGroup()
        if group == "Unknown":
            self.form.runButton.setEnabled(False)
            self.form.presetBox.setEnabled(False)
            self.form.detailsBox.setEnabled(False)
        else:
            self.form.runButton.setEnabled(True)
            self.form.presetBox.setEnabled(True)
            self.form.detailsBox.setEnabled(True)
            if not self.partData.isStepNeeded():
                self.form.stepGroupBox.hide()
            self.displayTreeAndList()
        return

    def fileButtonSelected(self):
        startdir, _ = os.path.split(self.form.fileEdit.text())
        filename, _ = PySide.QtWidgets.QFileDialog.getOpenFileName(
            None, translate("Cables", "Select folder"),  startdir)
        if filename:
            self.form.fileEdit.setText(filename)

    def fileEditChanged(self):
        result = self.partData.setStepFile(self.form.fileEdit.text())
        if result is None:
            self.form.runButton.setEnabled(False)
            self.fileEditIcon.setIcon(self.icon_error)
            self.form.fileEdit.setToolTip(
                translate("Cables", "File does not exist!"))
        else:
            self.form.runButton.setEnabled(True)
            self.fileEditIcon.setIcon(self.icon_ok)
            self.form.fileEdit.setToolTip("")

    def displayTreeAndList(self):
        # set tree table
        self.tree_model.clear()
        self.tree_model.setHorizontalHeaderLabels(
            tree_settings_lib_part["titles"])
        for col, width in enumerate(tree_settings_lib_part["column_widths"]):
            self.form.tree.setColumnWidth(col, width)

        # populate tree data
        objdict = self.updateTreeData()
        for i, key in enumerate(objdict.keys()):
            group = PySide.QtGui.QStandardItem(f"{key}")
            group.setEditable(False)
            for row in objdict[key]:
                items = []
                for nr, col in enumerate(row):
                    item = PySide.QtGui.QStandardItem(str(col))
                    item.setEditable(False)
                    items.append(item)
                group.appendRow(items)
            self.tree_model.appendRow(group)
            self.form.tree.setFirstColumnSpanned(
                i, self.form.tree.rootIndex(), True)
            # expand container
            index = self.tree_model.indexFromItem(group)
            self.form.tree.expand(index)

        # set list model
        str_list = self.partData.getDestinationFileNames()
        if str_list is not None:
            self.list_model.setStringList(str_list)

    def updateTreeData(self):
        objdict = {}
        if self.partData.data is None:
            return objdict
        preset = self.partData.data.get("Preset")
        if preset is None:
            return objdict
        preset_type = preset[1]
        for key in ["ExtShape", "Terminal", "SnapLines", "Preset"]:
            if key in self.partData.data.keys():
                if preset_type != "Fixed" and key != "Preset":
                    # skip unneeded data for tree
                    continue
                if isinstance(self.partData.data[key][0], list):
                    objdict[key] = self.partData.data[key]
                else:
                    objdict[key] = [self.partData.data[key]]
                items = []
                ignore = self.form.ignorePlacementCheckBox.isChecked()
                for item in objdict[key]:
                    if key == "ExtShape" and ignore:
                        params = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                    else:
                        params = item[3:]
                    item = item[:4]
                    item[3] = params
                    items.append(item)
                objdict[key] = items
        return objdict


class LibraryDialog:

    def __init__(self, ui_library=ui_library_list):
        archCableBaseElement.lib_cache.reset()
        self.lib = LibraryLocal()
        self.form = FreeCADGui.PySideUic.loadUi(ui_library)

        # default settings
        self.form.overwriteButton.hide()
        self.form.runButton.setEnabled(True)

        # tree view
        self.tree_model = PySide.QtGui.QStandardItemModel()
        self.form.tree.setModel(self.tree_model)
        self.form.tree.setUniformRowHeights(True)
        self.form.tree.setSelectionMode(
            self.form.tree.selectionMode().ExtendedSelection)
        # fileList view
        self.list_model = PySide.QtCore.QStringListModel()
        self.form.fileList.setModel(self.list_model)

        self.displayTreeAndList()

        # connect signals
        self.form.runButton.clicked.connect(self.runButtonClicked)
        self.form.cancelButton.clicked.connect(self.cancelButtonClicked)
        self.form.overwriteButton.clicked.connect(
            lambda _: self.runButtonClicked(True))
        self.form.tree.clicked.connect(self.onClickTree)

        self.setWindow(w=1100)
        self.form.show()

    def setWindow(self, w=640, h=200):
        self.form.layout().invalidate()
        self.form.layout().activate()
        self.form.adjustSize()
        self.form.resize(w, h)
        # center the dialog over FreeCAD window
        mw = FreeCADGui.getMainWindow()
        self.form.move(mw.frameGeometry().topLeft() + mw.rect().center()
                       - self.form.rect().center())

    def cancelButtonClicked(self):
        self.form.close()

    def runButtonClicked(self, force=False):
        self.form.fileList.selectionModel().clearSelection()
        str_list = self.lib.getFilesToModify()
        if str_list is None:
            message = translate("Cables", "Nothing is selected")
            self.form.infoMessage.setText(message)
            return
        if force:
            message = ""
            self.form.overwriteButton.hide()
        else:
            message = translate("Cables", "The selected items will be " +
                                "permanently deleted from the local " +
                                "library!")
            self.form.overwriteButton.show()
        self.form.infoMessage.setText(message)
        if not force:
            return

        self.lib.deleteSelected()
        self.displayTreeAndList()

    def displayTreeAndList(self):
        # set tree table
        self.tree_model.clear()
        self.tree_model.setHorizontalHeaderLabels(tree_settings_lib["titles"])
        for col, width in enumerate(tree_settings_lib["column_widths"]):
            self.form.tree.setColumnWidth(col, width)

        # populate tree data
        objdict = self.lib.data
        role = PySide.QtCore.Qt.ItemDataRole.UserRole
        for i, key in enumerate(objdict.keys()):
            group = PySide.QtGui.QStandardItem(f"{key}")
            group.setEditable(False)
            for row in objdict[key]:
                items = []
                for nr, col in enumerate(row):
                    item = PySide.QtGui.QStandardItem(str(col))
                    if nr == 0:
                        item.setData(row[2], role)
                    item.setEditable(False)
                    items.append(item)
                group.appendRow(items)
            self.tree_model.appendRow(group)
            self.form.tree.setFirstColumnSpanned(
                i, self.form.tree.rootIndex(), True)
            # expand container
            index = self.tree_model.indexFromItem(group)
            self.form.tree.expand(index)

        # set list model
        self.list_model.setStringList([])

    def onClickTree(self, index=None):
        self.form.infoMessage.setText("")
        self.form.overwriteButton.hide()
        sel = self.form.tree.selectedIndexes()
        presets = {}
        role = PySide.QtCore.Qt.ItemDataRole.UserRole
        for idx in sel:
            if idx.column() == 0:
                preset = self.tree_model.itemFromIndex(idx).data(role)
                parent_idx = idx.parent()
                if parent_idx.isValid():
                    group = parent_idx.data()
                    if group not in presets.keys():
                        presets[group] = []
                    presets[group].append(preset)
        self.lib.setSelection(presets)

        # set list model
        f_list = self.lib.getFilesToModify()
        str_list = f_list if f_list is not None else []
        self.list_model.setStringList(str_list)


class PartData:

    PartGroups = ["Box", "Connector", "Device", "Unknown"]
    PartGroupsTr = [
        translate("Cables", "Cable Box"),
        translate("Cables", "Cable Connector"),
        translate("Cables", "Electrical Device"),
        translate("Cables", "Unknown")
    ]

    def __init__(self, selection):
        data = self.prepare_part_data(selection)
        preset = self.prepare_preset_entry(data)
        if data is not None:
            data["Preset"] = preset
        self.data = data

    def groups(self):
        def _get_tr(group):
            gr_idx = self.PartGroups.index(group)
            return self.PartGroupsTr[gr_idx]
        groups = []
        if self.data is not None:
            group = self.data.get("PartGroup")
            if group is not None:
                if group == "Unknown":
                    groups.append(_get_tr(group))
                    groups.append(_get_tr("Connector"))
                    groups.append(_get_tr("Device"))
                else:
                    groups.append(_get_tr(group))
        return groups

    def getGroup(self):
        group = self.data.get("PartGroup")
        gr_idx = self.PartGroups.index(group)
        return group, self.PartGroupsTr[gr_idx]

    def setGroup(self, group_tr):
        gr_idx = self.PartGroupsTr.index(group_tr)
        self.data["PartGroup"] = self.PartGroups[gr_idx]

    def isStepNeeded(self):
        step = True
        if self.data.get("PartGroup") == "Box":
            step = False
        if self.data.get("PartGroup") == "Connector":
            preset = self.data.get("Preset")
            if preset is not None and preset[1] != "Fixed":
                step = False
        return step

    def setStepFile(self, filename):
        if filename is not None:
            if os.path.isfile(filename):
                libstep, placement = self.find_stepfile_in_library()
                if libstep != filename:
                    placement = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                obj = self.data["ExtShapeObj"]
                if not isProxyBase(obj, "BaseElement"):
                    placement = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                self.data["ExtShapeFile"] = [filename, placement]
                return filename
        if self.data is not None and "ExtShapeFile" in self.data.keys():
            self.data.pop("ExtShapeFile")
        return None

    def getStepFile(self):
        stepfile = None
        if self.isStepNeeded():
            stepfile, _ = self.find_stepfile_in_library()
        return stepfile

    def getDestinationFileNames(self):
        if self.data is None:
            return None
        file_list = []

        # local library preset file
        preset = self.data.get("Preset")
        if preset is None:
            return None
        f_presets = LibraryPart.PresetFiles.get(self.data["PartGroup"])
        if f_presets is None:
            return None
        preset_file = next(
            (f for f in f_presets if presetsPath not in f), None)
        file_list.append(str(Path(preset_file)))

        if preset[1] != "Fixed":
            return file_list

        # local library definition file and step file
        lib_dirs = LibraryPart.LibDirs
        l_path = next((p for p in lib_dirs if libPath not in p), None)
        for ext in ["csv", "step"]:
            lib_file = Path(l_path) / f"{preset[2]}_{preset[0]}.{ext}"
            file_list.append(str(lib_file))
        return file_list

    def updatePreset(self, el_class, el_name):
        if self.data.get("ExtShape") is not None:
            self.data["ExtShape"][0] = el_name
            self.data["ExtShape"][2] = el_class
        if self.data["Preset"] is not None:
            self.data["Preset"][0] = el_name
            self.data["Preset"][2] = el_class
            if self.data["Preset"][1] == "Fixed":
                self.data["Preset"][3] = f"{el_class}_{el_name}.step"

    def setIgnorePlacement(self, ignore):
        self.data["IgnorePlacement"] = ignore

    def getIgnorePlacement(self):
        return self.data.get("IgnorePlacement")

    def prepare_part_data(self, selection):
        data = {}
        if not selection:
            return None

        data["PartGroup"] = "Unknown"
        for obj in selection:
            element_type, part_group = self.clasify_obj(obj)
            if part_group is not None:
                data["PartGroup"] = part_group
            el_class, el_name = self.get_class_and_name(obj, element_type)
            if element_type == "ExtShape":
                yaw, pitch, roll = obj.Placement.Rotation.getYawPitchRoll()
                base_vec = obj.Placement.Base
                data["ExtShapeObj"] = obj
                data["ExtShape"] = [
                    el_name,                # Name
                    "ExtShape",             # ExtShape
                    el_class,               # Class
                    round(base_vec.x, 6),   # Offset X
                    round(base_vec.y, 6),   # Offset Y
                    round(base_vec.z, 6),   # Offset Z
                    round(yaw, 6),          # Rotation Yaw(Z)
                    round(pitch, 6),        # Rotation Pitch(Y)
                    round(roll, 6)          # Roll(X)
                    ]
            if element_type == "Terminal":
                if data.get("Terminal") is None:
                    data["Terminal"] = []
                if not el_name:
                    el_idx = f"{len(data['Terminal'])+1:03n}"
                    el_name = "Pin" + el_idx
                yaw, pitch, roll = obj.Placement.Rotation.getYawPitchRoll()
                base_vec = obj.Placement.Base
                data["Terminal"].append([
                    el_name,                # Name
                    "Terminal",             # ExtShape
                    el_class,               # Class
                    round(base_vec.x, 6),   # Offset X
                    round(base_vec.y, 6),   # Offset Y
                    round(base_vec.z, 6),   # Offset Z
                    round(yaw, 6),          # Rotation Yaw(Z)
                    round(pitch, 6),        # Rotation Pitch(Y)
                    round(roll, 6),         # Roll(X)
                    obj.NumberOfConnections,        # NrOfConnections
                    round(obj.Length.Value, 6),     # Length
                    round(obj.Spacing.Value, 6)     # Spacing
                    ])
            if element_type == "SnapLines":
                if data.get("SnapLines") is None:
                    data["SnapLines"] = []
                if not el_name:
                    el_idx = f"{len(data['SnapLines'])+1:03n}"
                    el_name = "Snap" + el_idx
                yaw, pitch, roll = obj.Placement.Rotation.getYawPitchRoll()
                base_vec = obj.Placement.Base
                data["SnapLines"].append([
                    el_name,                # Name
                    "SnapLines",            # ExtShape
                    el_class,               # Class
                    round(base_vec.x, 6),   # Offset X
                    round(base_vec.y, 6),   # Offset Y
                    round(base_vec.z, 6),   # Offset Z
                    round(yaw, 6),          # Rotation Yaw(Z)
                    round(pitch, 6),        # Rotation Pitch(Y)
                    round(roll, 6),         # Roll(X)
                    ])
            data["IgnorePlacement"] = False
        return data

    def prepare_preset_entry(self, data):
        if data is None:
            return None
        ext_shape = data.get("ExtShape")
        if not isinstance(ext_shape, list):
            return None
        if len(ext_shape) != 9:
            return None
        el_name = ext_shape[0]
        el_class = ext_shape[2]

        # determine preset type
        preset_type = "Fixed"
        obj = data.get("ExtShapeObj")
        part_group = data.get("PartGroup")
        if part_group == "Connector" and obj is not None:
            if hasattr(obj, "NumberOfHoles") and obj.NumberOfHoles > 0:
                preset_type = "ParametricTerminal"
        if part_group == "Box" and obj is not None:
            preset_type = obj.ProfileType

        if part_group == "Connector" and preset_type == "ParametricTerminal":
            el_name = f"{round(obj.HoleSize.Value, 2):g}mm2_x" + \
                      f"{obj.NumberOfHoles}"
            el_class = "TerminalStrip"
            preset = [
                el_name,                        # Name
                preset_type,                    # ParametricTerminal
                el_class,                       # Connector Class
                obj.NumberOfHoles,              # NrOfHoles
                obj.NumberOfTerminals,          # NrOfTerminals
                round(obj.Height.Value, 6),     # Height
                round(obj.HoleSize.Value, 6),   # HoleSize
                round(obj.Thickness.Value, 6),  # Thickness
                ]
        if part_group == "Box" and preset_type != "Fixed":
            height = round(obj.Height.Value, None)
            if preset_type == "Circle":
                el_name = f"Round_D{round(obj.Diameter.Value, 1):g}_h{height}"
            elif preset_type == "Rectangle" and obj.Depth == obj.Width:
                side = round(obj.Width.Value, None)
                el_name = f"Square_{side}x{side}_h{height}"
            elif preset_type == "Rectangle" and obj.Depth != obj.Width:
                width = round(obj.Width.Value, None)
                depth = round(obj.Depth.Value, None)
                el_name = f"Rectangle_{width}x{depth}_h{height}"
            el_class = "1G_FlushMnt"
            if preset_type == "Circle":
                preset = [
                    el_name,                        # Name
                    preset_type,                    # Circle
                    el_class,                       # Connector Class
                    round(obj.Diameter.Value, 6),   # diameter
                    round(obj.Height.Value, 6),     # height
                    round(obj.Thickness.Value, 6),  # thickness
                    round(obj.HoleDiameter.Value, 6),   # holediameter
                    ]
            if preset_type == "Rectangle":
                preset = [
                    el_name,                        # Name
                    preset_type,                    # Rectangle
                    el_class,                       # Connector Class
                    round(obj.Width.Value, 6),      # width
                    round(obj.Depth.Value, 6),      # depth
                    round(obj.Height.Value, 6),     # height
                    round(obj.Thickness.Value, 6),  # thickness
                    round(obj.FilletRadius.Value, 6),   # filletradius
                    round(obj.HoleDiameter.Value, 6),   # holediameter
                    round(obj.HolesDistance.Value, 6)   # holesdistance
                    ]
        if preset_type == "Fixed":
            terminals = data.get("Terminal")
            nr_of_terminals = len(terminals) if terminals is not None else 0
            snaplines = data.get("SnapLines")
            nr_of_snaplines = len(snaplines) if snaplines is not None else 0
            preset = [
                el_name,                        # Name
                preset_type,                    # Fixed
                el_class,                       # Connector Class
                f"{el_class}_{el_name}.step",   # StepFileName
                nr_of_terminals,                # NrOfTerminals
                nr_of_snaplines                 # NrOfSnapLines
                ]
        return preset

    def clasify_obj(self, obj):
        if hasattr(obj, 'Proxy') and \
                type(obj.Proxy).__name__ == "ArchCableConnector":
            return "ExtShape", "Connector"
        if hasattr(obj, 'Proxy') and \
                type(obj.Proxy).__name__ == "ArchElectricalDevice":
            return "ExtShape", "Device"
        if hasattr(obj, 'Proxy') and \
                type(obj.Proxy).__name__ == "ArchCableBox":
            return "ExtShape", "Box"
        if hasattr(obj, "Shape") and obj.Shape.Solids:
            return "ExtShape", "Unknown"
        if hasattr(obj, 'Proxy') and \
                type(obj.Proxy).__name__ == "CableTerminal":
            return "Terminal", None
        if hasattr(obj, 'Proxy') and \
                type(obj.Proxy).__name__ == "ExtSnapLines":
            return "SnapLines", None
        return "Unknown", None

    def get_class_and_name(self, obj, element_type):
        el_class, el_name = "", ""
        if element_type == "ExtShape":
            raw_name = obj.Preset if hasattr(obj, "Preset") else obj.Label
            el_class, _, el_name = raw_name.partition("_")
        if element_type == "Terminal":
            el_class = "Terminal"
            el_name = obj.PinName
        if element_type == "SnapLines":
            el_class = "SnapLines"
            el_name = obj.SnapName
        return el_class, el_name

    def find_stepfile_in_library(self):
        # It tries to find step file in library based on preset data
        stepfile = None
        deffile = None
        preset = self.data.get("Preset")
        if preset is not None and preset[1] == "Fixed":
            filename_step = preset[3]
            filename_def = f"{preset[2]}_{preset[0]}.csv"
        else:
            return None
        for libdir in archCableBaseElement.libdirs:
            fullname_step = os.path.join(libdir, filename_step)
            fullname_def = os.path.join(libdir, filename_def)
            if os.path.isfile(fullname_step):
                stepfile = fullname_step
            if os.path.isfile(fullname_def):
                deffile = fullname_def
        placement = self.find_placement_for_step(deffile)
        return stepfile, placement

    def find_placement_for_step(self, deffile):
        if deffile is None:
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        presets = cableProfile.readCablePresets([deffile])
        for preset in presets:
            if "ExtShape" in preset:
                placement = preset[4:]
                break
        return placement


class LibraryPart:
    PresetFiles = {
        "Box": archCableBox.presetfiles,
        "Connector": archCableConnector.presetfiles,
        "Device": archElectricalDevice.presetfiles
        }
    LibDirs = archCableBaseElement.libdirs

    def __init__(self, data):
        self.data = data

    def updateLibrary(self):
        self.update_presets_file()
        self.update_part_def_file()
        self.update_part_step_file()

    def existsInLibrary(self):
        exists = False
        libType = None          # 0: built-in library, 1: local library
        preset = self.data.get("Preset")
        part_preset_name = None
        if preset is not None:
            part_preset_name = f"{preset[2]}_{preset[0]}"
        preset_files = self.PresetFiles.get(self.data["PartGroup"])
        if preset_files is None:
            return exists, libType

        for preset_file in preset_files:
            if presetsPath in preset_file:
                libType = 0
            lib_presets = cableProfile.readCablePresets([preset_file])
            for lib_preset in lib_presets:
                lib_preset_name = f"{lib_preset[3]}_{lib_preset[1]}"
                if lib_preset_name == part_preset_name:
                    libType = 0 if presetsPath in preset_file else 1
                    exists = True
                    break
        return exists, libType

    def getPresetsFileName(self, local=True):
        # returns full file name of local/built-in library presets
        preset = self.data.get("Preset")
        if preset is None:
            return None
        f_presets = self.PresetFiles.get(self.data["PartGroup"])
        if local:
            f_preset = next(
                (f for f in f_presets if presetsPath not in f), None)
        else:
            f_preset = next(
                (f for f in f_presets if presetsPath in f), None)
        return Path(f_preset)

    def getPartDefinitionFileName(self, local=True, ext="csv"):
        # returns full file name of local/built-in library part definition
        preset = self.data.get("Preset")
        if preset is None:
            return None
        if preset[1] != "Fixed":
            return None

        lib_dirs = self.LibDirs
        if local:
            p_path = next((p for p in lib_dirs if libPath not in p), None)
        else:
            p_path = next((p for p in lib_dirs if libPath in p), None)
        if ext == "step":
            p_file = Path(p_path) / preset[3]
        else:
            p_file = Path(p_path) / f"{preset[2]}_{preset[0]}.{ext}"
        return p_file

    def read_csv_content(self, filename):
        content = []
        try:
            with open(filename, mode="r") as csv_file:
                for line in csv_file:
                    if line.startswith("#") or not line.strip():
                        content.append(line.strip())
                    else:
                        reader = csv.reader([line])
                        content.extend(list(reader))
        except Exception as err:
            logmsg(translate("Cables", "Error while reading from the "
                             "library file:") + f" {filename}",
                   "E", ModuleName, err)
            return None
        return content

    def write_csv_content(self, filename, content):
        try:
            with open(filename, mode='w', encoding='utf-8') as csv_file:
                for row in content:
                    if not isinstance(row, list):
                        csv_file.write(row + "\n")
                    else:
                        writer = csv.writer(
                            csv_file, lineterminator=os.linesep)
                        writer.writerow(row)
        except Exception as err:
            logmsg(translate("Cables", "Error while writing to the library " +
                             "file:") + f" {filename}",
                   "E", ModuleName, err)
            return None
        return filename

    def create_empty_presets_file(self):
        p_file_local = Path(self.getPresetsFileName(local=True))
        if p_file_local.is_file():
            return p_file_local

        # create local path
        try:
            p_file_local.parent.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            logmsg(translate("Cables", "Error while creating a path to " +
                             "the library file:") + f" {p_file_local}",
                   "E", ModuleName, err)
            return None

        # create template from built-in preset file
        p_file_global = Path(self.getPresetsFileName(local=False))
        content = self.read_csv_content(p_file_global)
        content = [row for row in content if isinstance(row, str)]
        p_file = self.write_csv_content(p_file_local, content)
        return p_file

    def create_empty_part_def_file(self):
        templates = {
            "Device": "Device_Dummy.csv",
            "Connector": "Connector_Dummy.csv"}
        p_file_local = self.getPartDefinitionFileName(local=True)
        if p_file_local is None:
            # Part definition file is not needed
            return None

        # create local path
        try:
            p_file_local.parent.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            logmsg(translate("Cables", "Error while creating a path to " +
                             "the library file:") + f" {p_file_local}",
                   "E", ModuleName, err)
            return None

        # create template from built-in preset file
        p_file_global = Path(self.getPartDefinitionFileName(local=False))
        template_name = Path(templates[self.data["PartGroup"]])
        template_file = p_file_global.parent / template_name
        content = self.read_csv_content(template_file)
        content = [row for row in content if isinstance(row, str)]
        p_file = self.write_csv_content(p_file_local, content)
        return p_file

    def update_presets_file(self):
        signatures = {
            "Box": [
                "# Name,Circle,BoxClass",
                "# Name,Rectangle,BoxClass"],
            "Connector": [
                "# Name,ParametricTerminal,ConnectorClass",
                "# Name,Fixed,ConnectorClass"],
            "Device": [
                "# Name,Fixed,DeviceClass"]}
        p_file = Path(self.getPresetsFileName())
        if not p_file.is_file():
            p_file = self.create_empty_presets_file()

        # read file content
        content = self.read_csv_content(p_file)
        if content is None:
            return

        preset = self.data["Preset"]

        # select signature
        try:
            sig_group = signatures.get(self.data["PartGroup"])
            sig = [s for s in sig_group if preset[1] in s][0]
        except Exception as err:
            logmsg(translate("Cables", "Error while writing new element to " +
                             "local library") + f": preset={preset}",
                   "E", ModuleName, err)
            return

        # search for signature index, nr of existing entries
        sig_idx = -1
        existing_entries = 0
        duplicate_idx = None
        counting = False
        for idx, row in enumerate(content):
            if sig in row:
                sig_idx = idx
                counting = True
                continue
            if counting and isinstance(row, list):
                existing_entries += 1
            else:
                counting = False

        # search for 1st occurrence of duplicate
        for idx, row in enumerate(content):
            if isinstance(row, list):
                if row[:3] == preset[:3]:
                    duplicate_idx = idx
                    break

        # insert or replace entry
        if duplicate_idx is None:
            if sig_idx == -1:
                content.append(preset)
            else:
                content.insert(sig_idx+existing_entries+1, preset)
        else:
            content[duplicate_idx] = preset

        # write to file
        self.write_csv_content(p_file, content)

    def update_part_def_file(self):
        signatures = {
            "Connector": [
                "# Name,ExtShape,Class",
                "# Name,Terminal,Class",
                "# Name,SnapLines,Class"],
            "Device": [
                "# Name,ExtShape,Class",
                "# Name,Terminal,Class",
                "# Name,SnapLines,Class"]}
        p_file = self.create_empty_part_def_file()
        if p_file is None:
            # Part definition file is not needed
            return

        # read file content
        content = self.read_csv_content(p_file)
        if content is None:
            return
        extshape_def = self.recompute_extshape_placement()
        terminal_lst, snaplines_lst = self.recompute_children_placement()
        if extshape_def is None:
            return
        entries = [extshape_def]
        if terminal_lst is not None:
            entries.extend(terminal_lst)
        if snaplines_lst is not None:
            entries.extend(snaplines_lst)

        for entry in entries:
            # select entry signature
            try:
                sig_group = signatures.get(self.data["PartGroup"])
                sig = [s for s in sig_group if entry[1] in s][0]
            except Exception as err:
                logmsg(translate("Cables", "Error while writing new element " +
                                 "to local library") + f": entry={entry}",
                       "E", ModuleName, err)
                return
            # search for signature index, nr of existing entries
            sig_idx = -1
            existing_entries = 0
            counting = False
            for idx, row in enumerate(content):
                if sig in row:
                    sig_idx = idx
                    counting = True
                    continue
                if counting and isinstance(row, list):
                    existing_entries += 1
                else:
                    counting = False

            # insert entry
            if sig_idx == -1:
                content.append(entry)
            else:
                content.insert(sig_idx+existing_entries+1, entry)

        # write to file
        self.write_csv_content(p_file, content)

    def recompute_extshape_placement(self):
        extshape_def = self.data.get("ExtShape")
        extshapefile = self.data.get("ExtShapeFile")
        obj = self.data.get("ExtShapeObj")
        if obj is None:
            return extshape_def
        extpl = FreeCAD.Placement()
        if extshapefile is not None:
            extpl.Base = FreeCAD.Vector(extshapefile[1][:3])
            extpl.Rotation = FreeCAD.Rotation(*extshapefile[1][3:])
        if self.data.get("IgnorePlacement"):
            newpl = extpl
        else:
            newpl = obj.Placement.multiply(extpl)
        newpl_lst = list(newpl.Base) + list(newpl.Rotation.getYawPitchRoll())
        newpl_lst_round = []
        for el in newpl_lst:
            newpl_lst_round.append(round(el, 6))
        newextshape_def = extshape_def[:3] + newpl_lst_round
        return newextshape_def

    def recompute_children_placement(self):
        if not self.data.get("IgnorePlacement"):
            return self.data.get("Terminal"), self.data.get("SnapLines")
        terminals = None
        snaps = None
        mainobj = self.data.get("ExtShapeObj")
        mainpl = mainobj.Placement
        if self.data.get("Terminal") is not None:
            terminals = []
            for terminal in self.data["Terminal"]:
                pl = FreeCAD.Placement()
                pl.Base = FreeCAD.Vector(terminal[3:6])
                pl.Rotation = FreeCAD.Rotation(*terminal[6:9])
                new_pl = mainpl.inverse().multiply(pl)
                base_vec = new_pl.Base
                yaw, pitch, roll = new_pl.Rotation.getYawPitchRoll()
                terminals.append(
                    terminal[0:3] +         # Name, ExtShape, Class
                    [round(base_vec.x, 6),  # Offset X
                     round(base_vec.y, 6),  # Offset Y
                     round(base_vec.z, 6),  # Offset Z
                     round(yaw, 6),         # Rotation Yaw(Z)
                     round(pitch, 6),       # Rotation Pitch(Y)
                     round(roll, 6)] +      # Roll(X)
                    terminal[9:])       # NrOfConnections, Length, Spacing
        if self.data.get("SnapLines") is not None:
            snaps = []
            for snap in self.data["SnapLines"]:
                pl = FreeCAD.Placement()
                pl.Base = FreeCAD.Vector(snap[3:6])
                pl.Rotation = FreeCAD.Rotation(*snap[6:9])
                new_pl = mainpl.inverse().multiply(pl)
                base_vec = new_pl.Base
                yaw, pitch, roll = new_pl.Rotation.getYawPitchRoll()
                snaps.append(
                    snap[0:3] +             # Name, ExtShape, Class
                    [round(base_vec.x, 6),  # Offset X
                     round(base_vec.y, 6),  # Offset Y
                     round(base_vec.z, 6),  # Offset Z
                     round(yaw, 6),         # Rotation Yaw(Z)
                     round(pitch, 6),       # Rotation Pitch(Y)
                     round(roll, 6)])       # Roll(X)
        return terminals, snaps

    def update_part_step_file(self):
        step_file = self.getPartDefinitionFileName(local=True, ext="step")
        if step_file is None:
            # STEP file is not needed
            return
        obj = self.data.get("ExtShapeObj")
        extsh_file = self.data.get("ExtShapeFile")
        source_file = Path(extsh_file[0]) if extsh_file is not None else None
        if source_file is None:
            options = {'exportHidden': True, 'keepPlacement': True,
                       'legacy': False}
            if isProxyBase(obj, "BaseElement"):
                # special export for existing Connector or Device objects
                doc = FreeCAD.ActiveDocument
                export_lst, tmp_obj_lst = self.get_export_shape_list(doc, obj)
                try:
                    Import.export(export_lst, str(step_file), **options)
                finally:
                    for tmp_obj in tmp_obj_lst:
                        doc.removeObject(tmp_obj.Name)
                    FreeCAD.ActiveDocument.recompute()
            else:
                # standard export for other objects
                ImportGui.export([obj], str(step_file), options)
        else:
            if source_file != step_file:
                try:
                    shutil.copy(source_file, step_file)
                except Exception as err:
                    logmsg(translate("Cables", "Error while copying STEP " +
                                     "file") +
                           f": STEP={source_file}",
                           "E", ModuleName, err)
                    return

    def get_export_shape_list(self, doc, obj):
        """
        It prepares list of tuples:  [ (obj1, [col1, col2, ...]), ... ]
        for proper export to STEP.
        It is assumed that obj.Proxy exists and is derived
        from BaseElement class.
        """
        sh_col_lst = []
        tmp_obj_lst = []
        pl_inversed = obj.Placement.inverse()
        colors = obj.ExtColor.copy()
        if obj.Shape.ShapeType == "Compound":
            for n, shape in enumerate(obj.Shape.SubShapes):
                nr_faces = len(shape.Faces)
                tmp_obj_label = f"{self.data.get('ExtShape')[2]}_" + \
                    f"{self.data.get('ExtShape')[0]}_shape{n+1:02d}"
                tmp_obj = doc.addObject("Part::Feature", "Part_Feature")
                tmp_obj.Label = tmp_obj_label
                tmp_obj.Shape = shape
                tmp_obj.Placement = pl_inversed.multiply(tmp_obj.Placement)
                sh_col_lst.append((tmp_obj, colors[:nr_faces]))
                tmp_obj_lst.append(tmp_obj)
                del colors[:nr_faces]
        else:
            # Assuming single solid
            sh_col_lst.append((obj, colors))
        return sh_col_lst, tmp_obj_lst


class LibraryLocal:
    def __init__(self):
        # p_files_local = []
        # p_dict = {}
        # for key in LibraryPart.PresetFiles.keys():
        #     p_files = LibraryPart.PresetFiles.get(key)
        #     p_file = next((f for f in p_files if presetsPath not in f), None)
        #     p_dict[key] = p_file
        #     p_files_local.append(p_file)
        # #print("p_files_local", p_files_local)
        # self.preset_files_dict = p_dict
        # self.preset_lst = cableProfile.readCablePresets(p_files_local)
        self.preset_files_dict, self.preset_lst = self.load_lib_data()
        self.data = self.getTreeData()
        self.selection = None

    def getTreeData(self):
        objdict = {}
        for key in self.preset_files_dict.keys():
            f_preset = self.preset_files_dict[key]
            presets = cableProfile.readCablePresets([f_preset], allstr=True)
            key_tr = PartData.PartGroupsTr[PartData.PartGroups.index(key)]
            objdict[key_tr] = presets
            items = []
            for item in objdict[key_tr]:
                params = item[1:]
                row = [f"{item[3]}_{item[1]}", item[2], params]
                items.append(row)
            objdict[key_tr] = items
        for key in objdict.keys():
            objdict[key].sort()
        return objdict

    def setSelection(self, objdict):
        self.selection = {}
        for key_tr in objdict.keys():
            key = PartData.PartGroups[PartData.PartGroupsTr.index(key_tr)]
            self.selection[key] = objdict[key_tr]

    def getFilesToModify(self):
        if self.selection is None:
            return None
        file_list = []
        for key in self.selection.keys():
            for preset in self.selection[key]:
                part = LibraryPart(None)
                part.data = {}
                part.data["PartGroup"] = key
                part.data["Preset"] = preset
                f_preset = part.getPresetsFileName()
                f_def = part.getPartDefinitionFileName(ext="csv")
                f_step = part.getPartDefinitionFileName(ext="step")

                # check if step file is used by more then one preset
                if f_step is not None:
                    stepname = f_step.name
                    counter = 0
                    for row in self.preset_lst:
                        if stepname in row:
                            counter += 1
                    if counter > 1:
                        f_step = None

                for f in [f_preset, f_def, f_step]:
                    if f is not None:
                        file_list.append(str(f))
        filtered_list = list(dict.fromkeys(file_list))
        if not filtered_list:
            filtered_list = None
        return filtered_list

    def deleteSelected(self):
        for key in self.selection.keys():
            for preset in self.selection[key]:
                part = LibraryPart(None)
                part.data = {}
                part.data["PartGroup"] = key
                part.data["Preset"] = preset
                self.remove_part(part)
        self.selection = None

        # reload library data
        self.preset_files_dict, self.preset_lst = self.load_lib_data()
        self.data = self.getTreeData()
        return

    def load_lib_data(self):
        p_dict = {}

        # load full filenames of local lib presets files
        for key in LibraryPart.PresetFiles.keys():
            p_files = LibraryPart.PresetFiles.get(key)
            p_file = next((f for f in p_files if presetsPath not in f), None)
            p_dict[key] = p_file
        preset_files_dict = p_dict

        # read all preset entries from all local lib presets files
        presets_lst = cableProfile.readCablePresets(
            list(p_dict.values()), allstr=True)

        return preset_files_dict, presets_lst

    def remove_part(self, part):
        f_preset = part.getPresetsFileName()

        # remove entry from presets file
        content = part.read_csv_content(f_preset)
        preset = part.data.get("Preset")
        if preset in content:
            idx = content.index(preset)
            content.pop(idx)
        part.write_csv_content(f_preset, content)
        logmsg(translate("Cables", "Library file modified:") +
               f" {str(f_preset)}", "M")
        if preset[1] != "Fixed":
            return

        p_csv = part.getPartDefinitionFileName(ext="csv")
        p_step = part.getPartDefinitionFileName(ext="step")

        # check if step file is used by more then one preset
        stepname = p_step.name
        counter = 0
        for row in self.preset_lst:
            if stepname in row:
                counter += 1

        # delete step file
        if counter < 2 and p_step.exists():
            p_step.unlink()
            logmsg(translate("Cables", "Library file deleted:") +
                   f" {str(p_step)}", "M")
            pass

        # delete csv def file
        if p_csv.exists():
            p_csv.unlink()
            logmsg(translate("Cables", "Library file deleted:") +
                   f" {str(p_csv)}", "M")


def isProxyBase(obj, name):
    if hasattr(obj, "Proxy"):
        if len(obj.Proxy.__class__.__bases__) > 0:
            if obj.Proxy.__class__.__bases__[0].__name__ == name:
                return True
    return False


def run():
    selection = FreeCADGui.Selection.getSelection()
    part_data = PartData(selection)
    if selection:
        qgui = LibraryPartDialog(selection)
    else:
        qgui = LibraryDialog()
    return part_data.data, qgui
