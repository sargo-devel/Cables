"""cableReports
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
import FreeCAD
import FreeCADGui
import PySide
from FreeCAD import Units

from freecad.cables import uiPath
from freecad.cables.cableutils import logmsg
from freecad.cables import translate

ModuleName = __name__.split('.')[-1]
ui_reports = os.path.join(uiPath, "reports.ui")

# collection of reports

# reports_collection_2 = [
#     {"name": "Report on placement", "definition": "report_placement"},
#     {"name": "Report on elements", "definition": "report_elements"},
#     {"name": "Report on quantities", "definition": "report_quantities"}
#     ]


# report definitions

report_placements_def = {
    "name": translate("Cables", "Report on placements"),
    "content": "report_placement",
    "titles": [translate("Cables", "Label"),
               "Id Qet",
               translate("Cables", "Attachment Support"),
               translate("Cables", "Map Mode"),
               translate("Cables", "Attachment Offset"),
               translate("Cables", "Placement")],
    "column_widths": (200, 90, 200, 105, 170, 170),     # max 950
    "column_flat_nr": None
    }

report_elements_def = {
    "name": translate("Cables", "Report on elements"),
    "content": "report_elements",
    "titles": [translate("Cables", "Label"),
               "Id Qet",
               translate("Cables", "Cable profile/Element preset"),
               translate("Cables", "Length/Quantity"),
               "Ifc Type",
               "Ifc Tag (" + translate("Cables", "e.g. Product ID") + ")",
               "Ifc Object Type (" + translate("Cables", "e.g. Product name") +
               ")"],
    "column_widths": (200, 90, 320, 160, 160, 180, 250),      # max 950
    "column_flat_nr": 2
    }

report_quantities_def = {
    "name": translate("Cables", "Report on quantities"),
    "content": "report_quantities",
    "titles": [translate("Cables", "Cable profile/Element preset") +
               " | IFC Tag | IFC Object Type",
               translate("Cables", "Length/Quantity"),
               translate("Cables", "Label"),
               "Ifc Type"],
    "column_widths": (400, 160, 295, 160),      # max 950
    "column_flat_nr": 0
    }

report_simplebom_def = {
    "name": translate("Cables", "Simple BOM"),
    "content": "report_simplebom",
    "titles": [translate("Cables", "Cable profile/Element preset") +
               " | IFC Tag | IFC Object Type",
               translate("Cables", "Length/Quantity")],
    "column_widths": (600, 220),      # max 950
    "column_flat_nr": 0
    }

reports_collection = [
    report_elements_def,
    report_quantities_def,
    report_placements_def,
    report_simplebom_def
    ]


class ReportsDialog:
    def __init__(self, ui_reports=ui_reports):
        self.separator = ", "
        self.path_pdf = None
        self.form = FreeCADGui.PySideUic.loadUi(ui_reports)
        for i, btn in enumerate(self.form.reportButtonsGroup.buttons()):
            self.form.reportButtonsGroup.setId(btn, i+1)
            self.form.reportButtonsGroup.button(i+1).setText(
                reports_collection[i]["name"])
        for report in reports_collection:
            self.form.reportComboBox.addItem(report["name"])
        self.form.waitMessage.hide()

        self.form.reportButton.setDefault(True)
        self.form.reportButton.setEnabled(True)
        self.form.reportButton.clicked.connect(self.reportButtonClicked)
        self.form.cancelButton.clicked.connect(self.cancelButtonClicked)

        # Reserved for future use
        self.form.report1Radio.clicked.connect(self.reportSelected)
        self.form.report2Radio.clicked.connect(self.reportSelected)
        self.form.report3Radio.clicked.connect(self.reportSelected)
        self.form.report1Radio.hide()
        self.form.report2Radio.hide()
        self.form.report3Radio.hide()
        # -----------------------

        self.form.pathButton.hide()
        self.form.pathEdit.hide()
        self.form.checkBoxPdf.clicked.connect(self.pdfSelected)
        self.form.pathButton.clicked.connect(self.pathSelected)

        self.form.reportComboBox.currentIndexChanged.connect(
            self.reportSelected)
        self.form.expandButton.clicked.connect(self.expandButtonClicked)
        self.form.collapseButton.clicked.connect(self.collapseButtonClicked)
        self.form.refreshButton.clicked.connect(self.refreshButtonClicked)

        # data view
        self.qmodel = PySide.QtGui.QStandardItemModel()
        self.form.tree.setModel(self.qmodel)
        self.form.tree.setUniformRowHeights(True)
        self.form.tree.setSelectionMode(
            self.form.tree.selectionMode().ExtendedSelection)

        self.form.tree.clicked.connect(self.onClickTree)

        self.setWindow()
        self.reportData = self.displayReport()
        self.form.show()

    def reportSelected(self):
        report_nr = self.form.reportComboBox.currentIndex()
        self.reportData = self.displayReport(report_nr)

    def pdfSelected(self):
        if self.form.checkBoxPdf.isChecked():
            self.form.pathButton.show()
            self.form.pathEdit.show()
        else:
            self.form.pathButton.hide()
            self.form.pathEdit.hide()

    def pathSelected(self):
        path = PySide.QtWidgets.QFileDialog.getExistingDirectory(
            None, translate("Cables", "Select folder"),  '')
        self.form.pathEdit.setText(path)
        if path:
            self.path_pdf = path

    def reportButtonClicked(self):
        self.form.waitMessage.show()
        self.disableAll()
        PySide.QtWidgets.QApplication.processEvents()

        report_nr = self.form.reportComboBox.currentIndex()
        flat_list = self.form.checkBoxFlatList.isChecked()
        for_pdf = True if self.path_pdf is not None else False

        sheet = self.make_report(
            reports_collection[report_nr], flat_list, for_pdf)
        self.form.close()

        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.ActiveDocument.setEdit(sheet.Name, 0)
        self.forceActivateLastTab()

        if for_pdf:
            self.make_pdf(sheet, reports_collection[report_nr], flat_list)
            FreeCAD.ActiveDocument.recompute()

        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(sheet)

    def forceActivateLastTab(self):
        main_window = FreeCADGui.getMainWindow()
        if not main_window:
            return
        mdi_area = main_window.findChild(PySide.QtWidgets.QMdiArea)
        if not mdi_area:
            return
        windows_lst = mdi_area.subWindowList()
        if windows_lst:
            last_window = windows_lst[-1]
            mdi_area.setActiveSubWindow(last_window)
            last_window.setFocus()

    def disableAll(self):
        self.form.modeBox.setEnabled(False)
        self.form.optionsBox.setEnabled(False)
        self.form.cancelButton.setEnabled(False)
        self.form.reportButton.setEnabled(False)

    def expandButtonClicked(self):
        self.form.tree.expandAll()

    def collapseButtonClicked(self):
        self.form.tree.collapseAll()

    def refreshButtonClicked(self):
        self.reportSelected()

    def cancelButtonClicked(self):
        self.form.close()

    def onClickTree(self, index=None):
        report_nr = self.form.reportComboBox.currentIndex()
        report_content = reports_collection[report_nr]["content"]
        FreeCADGui.Selection.clearSelection()
        sel = self.form.tree.selectedIndexes()
        for idx in sel:
            if report_content in ["report_placement", "report_elements"]:
                if idx.column() == 0:
                    obj = FreeCAD.ActiveDocument.getObject(
                        self.qmodel.itemFromIndex(idx).toolTip())
                    if obj:
                        FreeCADGui.Selection.addSelection(obj)
            if report_content == "report_quantities":
                if idx.column() == 0:
                    labels_txt = self.qmodel.itemFromIndex(
                        idx.siblingAtColumn(2)).text()
                    labels = labels_txt.split(self.separator)
                    for label in labels:
                        obj = FreeCAD.ActiveDocument.getObjectsByLabel(label)
                        if obj:
                            FreeCADGui.Selection.addSelection(obj[0])

    def setWindow(self):
        w = 1000
        h = 600
        self.form.resize(w, h)
        # center the dialog over FreeCAD window
        mw = FreeCADGui.getMainWindow()
        self.form.move(mw.frameGeometry().topLeft() + mw.rect().center()
                       - self.form.rect().center())

    def displayReport(self, report_nr=0):
        # get report details
        report_def = reports_collection[report_nr]
        report_content_func = getattr(self, report_def["content"])

        # set table
        self.qmodel.clear()
        self.qmodel.setHorizontalHeaderLabels(report_def["titles"])
        for col, width in enumerate(report_def["column_widths"]):
            self.form.tree.setColumnWidth(col, width)

        # populate data
        objdict = report_content_func(report_def)
        for i, key in enumerate(objdict.keys()):
            group = PySide.QtGui.QStandardItem(f"Group: {key}")
            group.setEditable(False)
            for row in objdict[key]:
                items = []
                for nr, col in enumerate(row):
                    if nr == 0:
                        if hasattr(col, "Label"):
                            item = PySide.QtGui.QStandardItem(col.Label)
                            item.setToolTip(col.Name)
                            item.setIcon(col.ViewObject.Icon)
                        else:
                            item = PySide.QtGui.QStandardItem(str(col))
                            item.setToolTip(col)
                    else:
                        if isinstance(col, list):
                            colstr = self.separator.join(col)
                            item = PySide.QtGui.QStandardItem(colstr)
                            if len(col) > 1:
                                item.setToolTip(colstr)
                        else:
                            item = PySide.QtGui.QStandardItem(col)
                    item.setEditable(False)
                    items.append(item)
                group.appendRow(items)
            self.qmodel.appendRow(group)
            self.form.tree.setFirstColumnSpanned(
                i, self.form.tree.rootIndex(), True)
            # expand container
            index = self.qmodel.indexFromItem(group)
            self.form.tree.expand(index)
        return objdict

    def report_placement(self, report_def):

        def _is_subwire(wire):
            if len(wire.InList) > 0 and hasattr(wire.InList[0], "Proxy"):
                if type(wire.InList[0].Proxy).__name__ == "ArchCable":
                    cable_subwires = wire.InList[0].SubWires
                    if wire in cable_subwires:
                        return True
            return False

        doc = FreeCAD.ActiveDocument
        plist = [ob for ob in doc.Objects if hasattr(ob, "Proxy")]
        obj_list = ["ArchCable", "ArchCableConduit", "ArchCableBox",
                    "ArchCableConnector", "ArchCableLightPoint",
                    "ArchElectricalDevice", "WireFlex", "CompoundPath",
                    "SupportLine", "Wire", "Point"]
        groupped_objects = {}
        for item in obj_list:
            objects = [c for c in plist if type(c.Proxy).__name__ == item]
            objects = sorted(objects, key=lambda obj: obj.Label)
            groupped_objects[item] = objects

        # Drop WireFlex objects which are SubWires
        if "WireFlex" in groupped_objects.keys():
            wire_lst = []
            for idx, wire in enumerate(groupped_objects["WireFlex"]):
                if not _is_subwire(wire):
                    wire_lst.append(wire)
            groupped_objects["WireFlex"] = wire_lst

        objdict = {}
        for group in groupped_objects.keys():
            objdict[group] = []
            for obj in groupped_objects[group]:
                col1 = obj
                col2 = obj.IdQet if hasattr(obj, "IdQet") else ""
                col3 = "none"
                if hasattr(obj, "AttachmentSupport"):
                    if obj.AttachmentSupport:
                        supp = obj.AttachmentSupport[0][0].Label
                        ref1 = obj.AttachmentSupport[0][1][0]
                        col3 = f"({supp}, ({ref1}))"
                col4 = obj.MapMode if hasattr(obj, "MapMode") else "none"
                col5 = repr(obj.AttachmentOffset).split("Placement ")[1] \
                    if hasattr(obj, "AttachmentOffset") else "none"
                col6 = repr(obj.Placement).split("Placement ")[1] \
                    if hasattr(obj, "Placement") else "none"
                objdict[group].append([col1, col2, col3, col4, col5, col6])
            if not objdict[group]:
                objdict.pop(group)

        return objdict

    def report_elements(self, report_def):

        def _get_str_value(length, prec=1):
            unit = length.getUserPreferred()[2]
            if unit in ['"', 'in', 'thou']:
                val = length.Value/length.getUserPreferred()[1]
                str_length = f"{val:.{prec+1}f} {unit}"
            else:
                val = length.Value
                str_length = f"{val:.{prec}f}"
            return str_length

        def _get_conduit_name(obj):
            if hasattr(obj, "ProfileType"):
                name = type_tr[obj.ProfileType]
                t = obj.WallThickness
                thick_txt = "" if t.Value == 0 else f"/{_get_str_value(t)}"
                if obj.ProfileType == "Circle":
                    d_txt = _get_str_value(obj.Diameter)
                    suffix = f"D{d_txt}{thick_txt}"
                if obj.ProfileType == "Square":
                    w_txt = _get_str_value(obj.Width)
                    suffix = f"W{w_txt}{thick_txt}"
                if obj.ProfileType == "Rectangle":
                    w_txt = _get_str_value(obj.Width)
                    h_txt = _get_str_value(obj.Height)
                    suffix = f"{w_txt} x {h_txt}{thick_txt}"
                suffix = suffix.replace(',', '.')
                name = name + " " + suffix
            else:
                diameter = translate("Cables", "diameter")
                name = f"{diameter} {obj.Diameter.UserString}"
            return name

        def _get_box_name(obj):
            square = False
            h_txt = _get_str_value(obj.Height, 0)
            if obj.ProfileType == "Circle":
                d_txt = _get_str_value(obj.Diameter, 0)
                suffix = f"D{d_txt} h{h_txt}"
            if obj.ProfileType == "Rectangle":
                w_txt = _get_str_value(obj.Width, 0)
                dp_txt = _get_str_value(obj.Depth, 0)
                if w_txt == dp_txt:
                    square = True
                suffix = f"{w_txt} x {dp_txt} h{h_txt}"
            suffix = suffix.replace(',', '.')
            if square:
                name = type_tr["Square"]
            else:
                name = type_tr[obj.ProfileType]
            return "Custom " + name + " " + suffix

        def _get_connector_name(connector):
            if hasattr(connector, "NumberOfHoles"):
                holes_nb = connector.NumberOfHoles
            else:
                holes_nb = ""
            if hasattr(connector, "HoleSize"):
                hole_size = f"{connector.HoleSize.Value:.1f}mm2"
            else:
                hole_size = ""
            name = f"Custom TerminalStrip_{hole_size}_x{holes_nb}"
            return name

        type_tr = {
            "Circle": translate("Cables", "round"),
            "Square": translate("Cables", "square"),
            "Rectangle": translate("Cables", "rectangular")
            }
        doc = FreeCAD.ActiveDocument
        plist = [ob for ob in doc.Objects if hasattr(ob, "Proxy")]
        obj_list = ["ArchCable", "ArchCableConduit", "ArchCableBox",
                    "ArchCableConnector", "ArchCableLightPoint",
                    "ArchElectricalDevice"]
        groupped_objects = {}
        for item in obj_list:
            objects = [c for c in plist if type(c.Proxy).__name__ == item]
            objects = sorted(objects, key=lambda obj: obj.Label)
            groupped_objects[item] = objects

        objdict = {}
        for group in groupped_objects.keys():
            objdict[group] = []
            for obj in groupped_objects[group]:
                col1 = obj
                col2 = obj.IdQet if hasattr(obj, "IdQet") else ""
                col3 = "none"
                if hasattr(obj, "Profile"):
                    # Profile is related to cables and conduits
                    if obj.Profile is not None:
                        if hasattr(obj.Profile, "Objects"):
                            # obj.Profile is a clone
                            col3 = obj.Profile.Objects[0].Label
                        else:
                            # obj.Profile is a regular object
                            col3 = obj.Profile.Label
                    elif hasattr(obj, "ConductorGauge") and \
                            hasattr(obj, "InsulationThickness"):
                        # Single wire cable
                        wname = translate("Cables", "single wire")
                        col3 = f"{wname} {obj.ConductorGauge} mm²" + \
                            f"/{obj.InsulationThickness}"
                    elif hasattr(obj, "Diameter"):
                        # Conduit
                        col3 = _get_conduit_name(obj)
                elif hasattr(obj, "Preset"):
                    # Preset is related to connectors, boxes, devices
                    # and light points
                    if obj.Preset is not None and obj.Preset != "Customized":
                        col3 = f"{obj.Preset}"
                    elif type(obj.Proxy).__name__ == "ArchCableConnector":
                        col3 = _get_connector_name(obj)
                    elif type(obj.Proxy).__name__ == "ArchCableBox":
                        col3 = _get_box_name(obj)
                    elif type(obj.Proxy).__name__ == "ArchElectricalDevice":
                        col3 = translate("Cables", "Customized")
                    elif type(obj.Proxy).__name__ == "ArchCableLightPoint":
                        name = translate("Cables", "Light point")
                        col3 = f"{name} D{_get_str_value(obj.Diameter)}"
                    else:
                        col3 = translate("Cables", "Unknown")
                col4 = f"{obj.Length}" if hasattr(obj, "Length") else "1"
                if hasattr(obj, "Length"):
                    col4 = obj.Length.UserString
                else:
                    col4 = "1"
                col5 = f"{obj.IfcType}" if hasattr(obj, "IfcType") else "none"
                col6 = f"{obj.Tag}" if hasattr(obj, "Tag") else ""
                col7 = f"{obj.ObjectType}" if hasattr(obj, "ObjectType") else ""
                objdict[group].append([col1, col2, col3, col4, col5, col6, col7])
            if not objdict[group]:
                objdict.pop(group)

        return objdict

    def report_quantities(self, report_def):
        objdict = self.report_elements(report_def)
        type_pos = 2    # list index of profile/preset name
        idx_obj = 0     # list index of object

        # additional info for type_pos column
        for key in objdict.keys():
            for item in objdict[key]:
                obj = item[idx_obj]
                tag = ""
                obj_type = ""
                if hasattr(obj, "Tag") and obj.Tag:
                    tag = f" | {obj.Tag}"
                if hasattr(obj, "ObjectType") and obj.ObjectType:
                    empty_tag = " | " if not tag else ""
                    obj_type = f"{empty_tag} | {obj.ObjectType}"
                mixed_name = f"{item[type_pos]}{tag}{obj_type}"
                item[type_pos] = mixed_name

        groupped_objects = {}
        for group in objdict.keys():
            types_set = set()

            # get element types for counting
            for item in objdict[group]:
                # item example:
                # [<Part::PartFeature>, '', '1G_FlushMnt_Round_D60_h62', '1', 'Junction Box']
                types_set.add(item[type_pos])

            # count elements
            counted_elements = dict.fromkeys(types_set)
            groupped_objects[group] = []
            for i, element_type in enumerate(counted_elements):
                # single item:
                # [element_type, nr_of_elements, [obj labels], [obj Ifctypes]]
                groupped_objects[group].append([element_type, 0, [], set()])
                for item in objdict[group]:
                    if item[type_pos] == element_type:
                        if hasattr(item[idx_obj], "Length"):
                            groupped_objects[group][i][1] += \
                                item[idx_obj].Length.Value
                        else:
                            groupped_objects[group][i][1] += 1
                        groupped_objects[group][i][2].append(
                            item[idx_obj].Label)
                        groupped_objects[group][i][3].add(
                            item[idx_obj].IfcType)
                groupped_objects[group][i][3] = \
                    list(groupped_objects[group][i][3])

        for group in groupped_objects.keys():
            objdict[group] = []
            for item in groupped_objects[group]:
                col1 = item[0]
                if isinstance(item[1], int):
                    col2 = str(item[1])
                else:
                    col2 = Units.Quantity(item[1], Units.Unit(1)).UserString
                col3 = item[2]
                col4 = item[3]
                objdict[group].append([col1, col2, col3, col4])
            if not objdict[group]:
                objdict.pop(group)
        # sort results
        for key in objdict.keys():
            objdict[key].sort()

        return objdict

    def report_simplebom(self, report_def):
        objdict = self.report_quantities(report_def)
        max_row = len(report_def["titles"])
        for key in objdict.keys():
            for i, row in enumerate(objdict[key]):
                objdict[key][i] = row[:max_row]
        return objdict

    def make_report(self, report_def, flat_list=False, for_pdf=False):
        sheet, _ = self.prepare_sheet(report_def, flat_list, for_pdf)
        if flat_list:
            key_subst = {
                "ArchCable": translate("Cables", "Cable"),
                "ArchCableConduit": translate("Cables", "Cable conduit"),
                "ArchCableBox": translate("Cables", "Cable box"),
                "ArchCableConnector": translate("Cables", "Connector"),
                "ArchCableLightPoint": "",
                "ArchElectricalDevice": translate("Cables", "Device"),
                }
            column_flat_nr = report_def["column_flat_nr"]
            for key in self.reportData.keys():
                for row in self.reportData[key]:
                    if column_flat_nr is not None:
                        new_val = f"{key_subst[key]} {row[column_flat_nr]}"
                        row[column_flat_nr] = new_val
        self.fill_sheet(sheet, self.reportData, flat_list, for_pdf)
        return sheet

    def prepare_sheet(self, report_def, flat_list=False, for_pdf=False):
        doc = FreeCAD.ActiveDocument
        sheet = doc.addObject('Spreadsheet::Sheet', "Sheet")
        pdf_ext = " " + translate("Cables", "for PDF") if for_pdf else ""
        sheet.Label = report_def.get("name") + pdf_ext
        start_row = 1
        start_column = "A" if flat_list else "B"
        width_first_col = 140
        gray = (0.75, 0.75, 0.75)

        # make title row
        titles = report_def.get("titles")
        row = start_row
        if not flat_list:
            sheet.set(f"A{row}", translate("Cables", "Group"))
        for nr, title in enumerate(titles):
            column = chr(ord(start_column)+nr)
            sheet.set(f"{column}{row}", f"{title}")

        # set title row bold
        last_col = chr(ord(start_column)+len(titles)-1)
        cell_range = f"A{row}:{last_col}{row}"
        sheet.setStyle(cell_range, 'bold')
        sheet.setBackground(cell_range, gray)

        # set column widths
        if not flat_list:
            sheet.setColumnWidth("A", width_first_col)
        widths = report_def.get("column_widths")
        for nr, width in enumerate(widths):
            column = chr(ord(start_column)+nr)
            sheet.setColumnWidth(f"{column}", width)
        sheet.recompute()

        # get list of objects
        plist = [ob for ob in doc.Objects if hasattr(ob, "Proxy")]
        obj_list = ["ArchCable", "ArchCableConduit", "ArchCableBox",
                    "ArchCableConnector", "ArchCableLightPoint",
                    "ArchElectricalDevice"]
        objects = [c for c in plist if type(c.Proxy).__name__ in obj_list]
        objects = sorted(objects, key=lambda obj: obj.Label)
        return sheet, objects

    def fill_sheet(self, sheet, data, flat_list=False, for_pdf=False):

        def _max_txt(cell_content, width_px, fm):
            # binary search of max text length
            text = str(cell_content)
            if fm.horizontalAdvance(text) <= width_px:
                return cell_content
            dots = "..."
            space = 10
            dots_width = fm.horizontalAdvance(dots)
            max_width_px = width_px - dots_width - space
            if max_width_px < 0:
                return ""
            min = 0
            max = len(text)
            opt_idx = 0
            iter = 0

            while min <= max:
                iter += 1
                mid = (min + max) // 2
                test_txt = text[:mid]
                test_width_px = fm.horizontalAdvance(test_txt)

                if test_width_px <= max_width_px:
                    opt_idx = mid
                    min = mid + 1
                else:
                    max = mid - 1
            return text[:opt_idx] + dots

        if for_pdf:
            from PySide.QtGui import QFontMetrics
            from PySide.QtWidgets import QApplication
            fm = QFontMetrics(QApplication.font())
        start_row = 2
        start_column = "A" if flat_list else "B"
        light_gray = (0.9, 0.9, 0.9)
        white = (1.0, 1.0, 1.0)
        for key in data.keys():
            last_column = chr(ord(start_column)+len(data[key][0])-1)
            if not flat_list:
                sheet.set(f"A{start_row}", f"{key}")
                start_row += 1
                cell_range = f"A{start_row-1}:{last_column}{start_row-1}"
                sheet.setBackground(cell_range, light_gray)
            for i, row in enumerate(data[key]):
                for col_id, col in enumerate(row):
                    verify_enable = True
                    column = f"{chr(ord(start_column)+col_id)}"
                    cell = f"{column}{i+start_row}"
                    content = row[col_id]
                    if hasattr(content, "Label"):
                        content = f"'{content.Label}"
                        verify_enable = False
                    elif isinstance(content, list):
                        content = f"'{self.separator.join(content)}"
                        verify_enable = False
                    else:
                        content = f"{content}"
                    if for_pdf:
                        content = _max_txt(
                            content, sheet.getColumnWidth(column), fm)
                    try:
                        sheet.set(cell, content)
                        sheet.recompute()
                        if verify_enable and hasattr(sheet, cell):
                            verify = sheet.get(cell)
                            if hasattr(verify, "UserString"):
                                verify = verify.UserString
                            else:
                                verify = (str(verify))
                            if content != verify:
                                sheet.set(cell, f"'{content}")
                    except Exception:
                        sheet.set(cell, f"'{content}")
                # Set white cell background twice due to FreeCAD 1.1 bug
                # White background is needed in FreeCAD 1.1 dark mode
                cell_range = f"A{start_row+i}:{last_column}{start_row+i}"
                sheet.setBackground(cell_range, light_gray)
                sheet.setBackground(cell_range, white)

            start_row = start_row + i + 1

    def make_pdf(self, sheet, report_def, flat_list):
        # get number of sheet rows
        nr_rows = 1
        for key in self.reportData.keys():
            nr_rows += len(self.reportData[key])
            if not flat_list:
                nr_rows += 1

        start_row = 1
        nr = 1
        for i in range(nr_rows):
            start_row = self.make_single_pdf_page(sheet, report_def,
                                                  flat_list, nr, start_row)
            if start_row >= nr_rows:
                break
            nr += 1

    def make_single_pdf_page(self, sheet, report_def, flat_list, nr,
                             start_row):
        import TechDrawGui
        doc = FreeCAD.ActiveDocument
        name = f"{sheet.Label} {translate('Cables', 'Page')} {nr:03n}"

        template_path = os.path.join(
            FreeCAD.getResourceDir(),
            "Mod", "TechDraw", "Templates", "A4_Portrait_blank.svg")
        if not os.path.isfile(template_path):
            template_path = os.path.join(
                FreeCAD.getResourceDir(),
                "Mod", "TechDraw", "Templates", "ISO", "A4_Portrait_blank.svg")
        template = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
        template.Template = template_path

        page = doc.addObject("TechDraw::DrawPage", "Page")
        page.Label = name
        page.Template = template

        sheet_view = doc.addObject("TechDraw::DrawViewSpreadsheet",
                                   f"Sheet{nr:03n}")
        sheet_view.Source = sheet
        page.addView(sheet_view)
        page.ViewObject.ShowFrames = False

        dpi_factor = 25.4/96.0
        top_marg = 15
        bottom_marg = 20
        available_width_mm = page.Template.Width.Value - 2*top_marg
        available_height_mm = page.Template.Height.Value - top_marg - bottom_marg
        available_width = available_width_mm/dpi_factor
        available_height = available_height_mm/dpi_factor
        sheet_view.LineWidth = 0

        # get number of sheet columns
        if flat_list:
            nr_col = len(report_def.get("titles"))
        else:
            nr_col = len(report_def.get("titles")) + 1
        # get number of sheet rows
        nr_rows = 1
        for key in self.reportData.keys():
            nr_rows += len(self.reportData[key])
            if not flat_list:
                nr_rows += 1
        # get sheet width in pts
        sheet_width = 0
        for i in range(nr_col):
            col = chr(ord('A') + i)
            sheet_width += sheet.getColumnWidth(col)
        last_col = col

        # set scale
        sheet_view.Scale = available_width/sheet_width
        available_height = available_height/sheet_view.Scale

        # get sheet height in pts
        sheet_height = 0
        for i in range(start_row, nr_rows):
            row = i + 1
            sheet_height += sheet.getRowHeight(str(row))
            if sheet_height > available_height:
                row -= 1
                break
        last_row = row
        sheet_view.CellStart = f"A{str(start_row)}"
        sheet_view.CellEnd = last_col + str(last_row)

        offset = (available_height-(sheet_height/2))*dpi_factor
        sheet_view.Y = offset*sheet_view.Scale + bottom_marg

        page.ViewObject.show()
        doc.recompute()

        pdf_fullname = os.path.join(self.path_pdf, f"{doc.Label} {name}.pdf")
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(page)
        FreeCADGui.activateWorkbench("CablesWorkbench")
        try:
            TechDrawGui.exportPageAsPdf(page, pdf_fullname)
            # Gui.runCommand("TechDraw_PrintAll")
        except Exception as err:
            logmsg(translate("Cables", "Error creating PDF"),
                   "E", ModuleName, err)
        return last_row + 1
