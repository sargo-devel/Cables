"""cableProfile
"""

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
import csv
import math
import FreeCAD
import FreeCADGui
import Part
import Sketcher
import Show
import ProfileLib.RegularPolygon
from PySide import QtGui
from freecad.cables import uiPath, presetsPath


translate = FreeCAD.Qt.translate
ui_profile = os.path.join(uiPath, "profile.ui")
svg_img = {"R": (os.path.join(uiPath, "profile-simple-r.svg"), 64, 64),
           "F": (os.path.join(uiPath, "profile-simple-f.svg"), 64, 64),
           "Rf": (os.path.join(uiPath, "profile-full-r.svg"), 90, 90),
           "Ff": (os.path.join(uiPath, "profile-full-f.svg"), 90, 90)
           }
gauge_mm2_list = ['custom', '0.2', '0.5', '0.75', '1', '1.5', '2.5', '4', '6',
                  '10', '16', '25', '35', '50', '70', '95', '120']

# Presets in the form: Name, Profile class, Voltage Class, [profile data]
# Search for profiles.csv in presets and in the user path
profilefiles = [os.path.join(presetsPath, "profiles.csv"),
                os.path.join(FreeCAD.getUserAppDataDir(), "Cables",
                             "profiles.csv")]
default_preset = "YDY_3x1.5_750V"
prof_class_list = ["Round", "Flat"]
prof_class = {prof_class_list[0]: "R", prof_class_list[1]: "F"}
prof_class_r = {"R": prof_class_list[0], "F": prof_class_list[1]}
unit_schema_m2 = [4, 9]


class TaskPanelProfile:
    def __init__(self, obj, presetname=default_preset,
                 gauge_list=gauge_mm2_list):
        self.obj = obj
        self.reload_counter = 0
        self.table = {"ShowDetails": 0}
        self.form = FreeCADGui.PySideUic.loadUi(ui_profile)
        self.presetnames, self.presets = getPresets()
        self.oldSchema = FreeCAD.Units.getSchema()
        if self.oldSchema in unit_schema_m2:
            self.newSchema = 0
        else:
            self.newSchema = self.oldSchema
        self.gauge_list = [round(float(val), 4) for val in gauge_list[1:]]
        self.form.comboPreset.addItems(self.presetnames)
        profile_list = list(set([i[1]+'_'+i[3] for i in self.presets]))
        profile_list.sort()
        profile_list = ['custom'] + profile_list
        self.form.comboProfileType.addItems(profile_list)
        self.form.comboWireGauge.addItems(gauge_list)
        self.form.comboProfClass.addItems(prof_class_list)
        self.setLabelProfileType(svg_img["R"])
        self.form.customWireGauge.setProperty("rawValue", 0.05)
        self.setTable(presetname)
        self.reloadPropertiesFromTable()
        signal_list = [
            (self.connectEnumVar, self.form.comboPreset, "Preset"),
            (self.connectEnumVar, self.form.comboProfileType, "ProfileType"),
            (self.connectEnumVar, self.form.comboProfClass, "ProfileClass"),
            (self.connectStateVar, self.form.detailsCheckBox, "ShowDetails"),
            (self.connectSpinVar, self.form.sJacketThick, "JacketThick"),
            (self.connectSpinVar, self.form.sSingleInsul, "SingleInsulThick"),
            (self.connectSpinVar, self.form.sInsulDist, "InsulDist"),
            (self.connectSpinVar, self.form.NumberOfWires, "NrOfWires"),
            (self.connectEnumVar, self.form.comboWireGauge, "WireGauge"),
            (self.connectSpinVar, self.form.customWireGauge, "WireGauge")]
        for element in signal_list:
            element[0](element[1], element[2], self.updateVisibility)
        self.updateVisibility("", "")
        self.addTempoVis()
        self.setTopCameraView()

    def accept(self):
        profile, wireparams = self.getDataToBuildProfile()
        if hasattr(self.obj, "Name"):
            FreeCAD.ActiveDocument.removeObject(self.obj.Name)
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Profile"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand(f"{c}.cableProfile.makeCableProfile(" +
                             f"{profile}, {wireparams[0]}, {wireparams[1]})")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()
        self.removeTempoVis()
        FreeCADGui.Control.closeDialog()
        FreeCAD.Units.setSchema(self.oldSchema)

    def reject(self):
        if hasattr(self.obj, "Name"):
            FreeCAD.ActiveDocument.removeObject(self.obj.Name)
        self.removeTempoVis()
        FreeCADGui.Control.closeDialog()
        FreeCAD.Units.setSchema(self.oldSchema)
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.ActiveDocument.resetEdit()

    def updateVisibility(self, pname, pvalue):
        FreeCAD.Units.setSchema(self.newSchema)
        self.reloadPropertiesFromTable()
        if self.form.detailsCheckBox.isChecked():
            self.form.profileTypeDetailsBox.setVisible(True)
            suffix = "f"
        else:
            self.form.profileTypeDetailsBox.setVisible(False)
            suffix = ""
        img_type = prof_class[self.table["ProfileClass"]] + suffix
        self.setLabelProfileType(svg_img[img_type])

        switch = False if self.table["WireGauge"] in self.gauge_list else True
        self.form.customWireGauge.setVisible(switch)
        self.form.labelCustomWireGauge.setVisible(switch)

        if self.reload_counter == 0 and pname != "ShowDetails":
            if hasattr(self.obj, "Name"):
                FreeCAD.ActiveDocument.removeObject(self.obj.Name)
            profile, wireparams = self.getDataToBuildProfile()
            self.obj = makeCableProfile(profile, *wireparams)
            FreeCAD.ActiveDocument.recompute()
            FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name,
                                              self.obj.Name)

    def setLabelProfileType(self, img_element):
        pic = QtGui.QPixmap(img_element[0])
        self.form.labelProfileType.setPixmap(pic)
        self.form.labelProfileType.setFixedSize(img_element[1], img_element[2])

    def connectEnumVar(self, element, pname, callback=None):
        element.currentTextChanged.connect(
                lambda txtval: self.updateProperty(pname, txtval, callback))

    def connectStateVar(self, element, pname, callback=None):
        element.stateChanged.connect(
                lambda intval: self.updateProperty(pname, intval, callback))

    def connectSpinVar(self, element, pname, callback=None):
        # disable recompute on every key press
        element.setProperty("keyboardTracking", False)
        element.valueChanged.connect(
            lambda value: self.updateProperty(pname, value, callback))

    def updateProperty(self, pname, pvalue, callback):
        ptype = type(self.table[pname]).__name__
        try:
            if ptype == "str":
                if pname == "Preset":
                    self.setTable(pvalue)
                else:
                    self.table[pname] = pvalue
            if ptype == "int":
                self.table[pname] = int(pvalue)
            if ptype in ["float", "Quantity"]:
                if pname == "WireGauge":
                    self.updateWireGauge(pvalue)
                else:
                    self.table[pname] = round(float(pvalue), 4)
        except (AttributeError, ValueError):
            FreeCAD.Console.PrintError(
                "Profile", f"Can't set {pname} with value: {pvalue}")
        if pname in ["ProfileClass", "JacketThick", "SingleInsulThick",
                     "InsulDist"]:
            self.setProfileTypeFromDetails()
        if pname == "ProfileType":
            self.setTableFromProfileType()
        if pname in ["NrOfWires", "WireGauge"]:
            self.setTableFromWires()
        if callback is not None:
            callback(pname, pvalue)

    def updateWireGauge(self, pvalue):
        vtype = type(pvalue).__name__
        if vtype == "Quantity":
            pvalue = pvalue.Value
            vtype = "float"
        if vtype == "float":
            if pvalue in self.gauge_list:
                if pvalue > self.table["WireGauge"]:
                    pvalue += 0.05
                else:
                    pvalue -= 0.05
        if pvalue != "custom":
            self.table["WireGauge"] = round(float(pvalue), 4)
        else:
            self.table["WireGauge"] = self.form.customWireGauge.property("rawValue")

    def getDataToBuildProfile(self):
        profile = [1, self.table["Name"],
                   prof_class[self.table["ProfileClass"]],
                   self.table["VoltageClass"],
                   self.table["JacketThick"],
                   self.table["SingleInsulThick"],
                   self.table["InsulDist"]]
        wireparams = [self.table["NrOfWires"], self.table["WireGauge"]]
        return profile, wireparams

    def setTable(self, presetname):
        preset = None
        for p in self.presets:
            p_name = f"{p[1]}_{p[7]}x{p[8]:g}_{p[3]}"
            if presetname == p_name:
                preset = p
                break
        if preset is None:
            self.table["Preset"] = presetname
            if "ProfileType" not in self.table.keys():
                preset = [1, "Round", "R", "Custom", 1.2, 0.8, 0.1, 2, 1.0]
            else:
                return
        self.table["Preset"] = presetname
        self.table["ProfileType"] = f"{preset[1]}_{preset[3]}"
        self.table["Name"] = preset[1]
        self.table["ProfileClass"] = prof_class_r[f"{preset[2]}"]
        self.table["VoltageClass"] = preset[3]
        self.table["JacketThick"] = preset[4]
        self.table["SingleInsulThick"] = preset[5]
        self.table["InsulDist"] = preset[6]
        self.table["NrOfWires"] = preset[7]
        self.table["WireGauge"] = preset[8]

    def setTableFromWires(self):
        presetname = None
        pname = f'{self.table["Name"]}_{self.table["NrOfWires"]}x' + \
                f'{self.table["WireGauge"]:g}_{self.table["VoltageClass"]}'
        for p in self.presetnames:
            if pname == p:
                presetname = p
                break
        if presetname is None:
            self.table["Preset"] = "Customized"
        else:
            self.table["Preset"] = presetname

    def setTableFromProfileType(self):
        preset = None
        for p in self.presets:
            p_name = f"{p[1]}_{p[3]}"
            if self.table["ProfileType"] == p_name:
                preset = p
                break
        if preset is None:
            self.table["Preset"] = "Customized"
        else:
            self.table["Name"] = preset[1]
            self.table["ProfileClass"] = prof_class_r[f"{preset[2]}"]
            self.table["VoltageClass"] = preset[3]
            self.table["JacketThick"] = preset[4]
            self.table["SingleInsulThick"] = preset[5]
            self.table["InsulDist"] = preset[6]
            self.setTableFromWires()

    def setProfileTypeFromDetails(self):
        preset = None
        pclass_lst = [
            prof_class[self.table["ProfileClass"]],
            self.table["JacketThick"],
            self.table["SingleInsulThick"],
            self.table["InsulDist"]
            ]
        for p in self.presets:
            if pclass_lst == [p[2], p[4], p[5], p[6]]:
                preset = p
                break
        if preset is None:
            self.table["ProfileType"] = "custom"
            self.table["Name"] = self.table["ProfileClass"]
            self.table["VoltageClass"] = "Custom"
        else:
            self.table["ProfileType"] = f"{p[1]}_{p[3]}"

    def reloadPropertiesFromTable(self):
        self.reload_counter += 1
        self.form.comboPreset.setCurrentText(self.table["Preset"])
        self.form.comboProfileType.setCurrentText(self.table["ProfileType"])
        self.form.detailsCheckBox.setChecked(self.table["ShowDetails"])
        self.form.comboProfClass.setCurrentText(self.table["ProfileClass"])
        self.form.sJacketThick.setProperty("rawValue",
                                           self.table["JacketThick"])
        self.form.sSingleInsul.setProperty("rawValue",
                                           self.table["SingleInsulThick"])
        self.form.sInsulDist.setProperty("rawValue", self.table["InsulDist"])
        self.form.NumberOfWires.setProperty("value", self.table["NrOfWires"])
        if self.table["WireGauge"] in self.gauge_list:
            self.form.comboWireGauge.setCurrentText(
                f"{self.table['WireGauge']:g}")
        else:
            self.form.comboWireGauge.setCurrentText("custom")
            gauge = FreeCAD.Units.Quantity(f"{self.table['WireGauge']} mm^2")
            self.form.customWireGauge.setProperty("value", gauge)
        self.reload_counter -= 1
        self.reloading = False

    def addTempoVis(self):
        self.tv = Show.TempoVis(FreeCAD.ActiveDocument)
        self.tv.sketchClipPlane(self.obj, None, False)
        self.tv.saveCamera()

    def removeTempoVis(self):
        self.tv.restore()
        del self.tv

    def setTopCameraView(self):
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name,
                                          self.obj.Name)
        FreeCADGui.SendMsgToActiveView("ViewSelection")
        FreeCADGui.activeView().setCameraOrientation((0.0, 0.0, 0.0, 1.0))


def makeCableProfile(profile=[1, 'YDYp', 'F', '750V', 1.2, 0.8, 0.1],
                     nr_of_wires=3, wire_gauge_mm2=1.5):
    """Makes cable profile
    profile=[idx,name,profile_class,voltage_class,jacket_thickness,
             single_insulation_thickness,insul_dist]
    """
    label = f"{profile[1]}_{nr_of_wires}x{wire_gauge_mm2:g}_{profile[3]}"
    # FreeCAD.Console.PrintMessage(f"Label: {label}\n")
    if nr_of_wires < 1 or wire_gauge_mm2 == 0:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Cable needs to have number of wires > 0 and nonzero " +
            "wire gauge") + "\n")
        return None
    p = None
    if profile[2] == 'F':
        p = makeCableProfileF(label, profile[4:], nr_of_wires, wire_gauge_mm2)
    if profile[2] == 'R':
        p = makeCableProfileR(label, profile[4:], nr_of_wires, wire_gauge_mm2)
    return p


def makeCableProfileF(label, insul=[1.2, 0.8, 0.1], nr_of_wires=3,
                      wire_gauge_mm2=1.5):
    """Profile for flat cable
    insul=[jacket_thickness,single_insulation_thickness,insul_dist]
    """
    if nr_of_wires < 2:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Flat cable needs to have at least 2 wires")
            + "\n")
        return None
    profile = FreeCAD.activeDocument().addObject('Sketcher::SketchObject',
                                                 'Sketch')
    profile.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0),
                                          FreeCAD.Rotation(0, 0, 0, 1))
    profile.MapMode = "Deactivated"
    profile.Label = label
    App = FreeCAD
    v1 = App.Vector(-20, 10, 0)
    v2 = App.Vector(20, 10, 0)
    v3 = App.Vector(20, -10, 0)
    v4 = App.Vector(-20, -10, 0)
    vc1 = App.Vector(-30, 0, 0)
    vc2 = App.Vector(30, 0, 0)

    # Create Wire0 (cable jacket)
    geoList = []
    geoList.append(Part.LineSegment(v1, v2))
    geoList.append(Part.Arc(v2, vc2, v3))
    geoList.append(Part.LineSegment(v3, v4))
    geoList.append(Part.Arc(v4, vc1, v1))
    profile.addGeometry(geoList, False)
    constraintList = []
    constraintList.append(Sketcher.Constraint('Tangent', 0, 2, 1, 2))
    constraintList.append(Sketcher.Constraint('Tangent', 1, 1, 2, 1))
    constraintList.append(Sketcher.Constraint('Tangent', 2, 2, 3, 2))
    constraintList.append(Sketcher.Constraint('Tangent', 3, 1, 0, 1))
    constraintList.append(Sketcher.Constraint('Horizontal', 0))
    constraintList.append(Sketcher.Constraint('Equal', 1, 3))
    constraintList.append(Sketcher.Constraint('Symmetric', 3, 3, 1, 3, -1, 1))
    profile.addConstraint(constraintList)
    # Create inner wires
    norm = App.Vector(0, 0, 1)
    wo, wi, p, nr = createProfileSubWires(profile, norm, nr_of_wires, 4)

    # Calculate base dimensions
    wire_diameter = math.sqrt(wire_gauge_mm2/math.pi)*2
    # distance between centers of adjacent wires:
    p_dist = wire_diameter + 2*insul[1] + insul[2]
    # x position of 1st point:
    p1_xpos = -(nr_of_wires-1)*p_dist/2
    # single insulation diameter (outer ring):
    wo_d = wire_diameter + 2*insul[1]
    # wire diameter (inner ring):
    wi_d = wire_diameter
    # jacket arc diameter:
    j_d = wo_d + 2*insul[0]
    # FreeCAD.Console.PrintMessage(f"nr,wo,wi,p({nr},{wo},{wi},{p})\n")
    constraintList = []
    # 1st point placement:
    constraintList.append(
        Sketcher.Constraint('DistanceX', p, 1, -1, 1, -p1_xpos))
    constraintList.append(Sketcher.Constraint('Diameter', 3, j_d))
    constraintList.append(Sketcher.Constraint('Diameter', wo, wo_d))
    constraintList.append(Sketcher.Constraint('Diameter', wi, wi_d))
    for i in range(nr-1):
        # nth point distance:
        constraintList.append(
            Sketcher.Constraint('DistanceX', p+i, 1, p+i+1, 1, p_dist))
        # points on x axis (except 1st to avoid redundancy later):
        constraintList.append(
            Sketcher.Constraint('PointOnObject', p+i+1, 1, -1))
        # insulations equality:
        constraintList.append(Sketcher.Constraint('Equal', wo, wo+i+1))
        # wires equality:
        constraintList.append(Sketcher.Constraint('Equal', wi, wi+i+1))
    for i in range(nr):
        # insulation (outer ring) on point:
        constraintList.append(
            Sketcher.Constraint('Coincident', p+i, 1, wo+i, 3))
        # wire (inner ring) on point:
        constraintList.append(
            Sketcher.Constraint('Coincident', p+i, 1, wi+i, 3))
    # jacket on 1st point (1st point is not on x-axis to avoid redundancy):
    constraintList.append(Sketcher.Constraint('Coincident', p, 1, 3, 3))
    profile.addConstraint(constraintList)
    return profile


def makeCableProfileR(label, insul=[1.2, 0.8, 0.1], nr_of_wires=3,
                      wire_gauge_mm2=1.5):
    """Profile for round cable
    insul=[jacket_thickness,single_insulation_thickness,insul_dist]
    """
    if nr_of_wires < 1:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Round cable needs to have at least 1 wire")
            + "\n")
        return None
    profile = FreeCAD.activeDocument().addObject('Sketcher::SketchObject',
                                                 'Sketch')
    profile.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0),
                                          FreeCAD.Rotation(0, 0, 0, 1))
    profile.MapMode = "Deactivated"
    profile.Label = label
    App = FreeCAD
    # Create Wire0 (cable jacket)
    norm = App.Vector(0, 0, 1)
    geoList = []
    geoList.append(Part.Circle(App.Vector(0, 0, 0), norm, 30))
    profile.addGeometry(geoList, False)
    constraintList = []
    constraintList.append(Sketcher.Constraint('Coincident', 0, 3, -1, 1))
    profile.addConstraint(constraintList)
    # Create inner wires
    wo, wi, p, nr = createProfileSubWires(profile, norm, nr_of_wires, 1)

    # Calculate base dimensions
    wire_diameter = math.sqrt(wire_gauge_mm2/math.pi)*2
    # distance between centers of adjacent wires:
    p_dist = wire_diameter + 2*insul[1] + insul[2]
    # y position of 1st point (radius of construction circle):
    if nr > 2:
        p1_ypos = p_dist/(2*math.sin(math.pi/nr))
    elif nr == 2:
        p1_ypos = 0.5*wire_diameter + insul[1] + 0.5*insul[2]
    elif nr == 1:
        p1_ypos = 0
    # single insulation diameter (outer ring):
    wo_d = wire_diameter + 2*insul[1]
    # wire diameter (inner ring):
    wi_d = wire_diameter
    # jacket ring diameter:
    j_d = 2*p1_ypos + wo_d + 2*insul[0]

    # Create construction polygon
    cl = p + nr     # number of 1st polygon line
    cc = cl + nr    # number of polygon circle
    if nr > 2:
        ProfileLib.RegularPolygon.makeRegularPolygon(
            profile, nr, App.Vector(0, 0, 0), App.Vector(0, p1_ypos, 0), True)
    elif nr == 2:
        geoList = []
        v1 = App.Vector(0, p1_ypos, 0)
        v2 = App.Vector(0, -p1_ypos, 0)
        v0 = App.Vector(0, 0, 0)
        geoList.append(Part.LineSegment(v1, v0))
        geoList.append(Part.LineSegment(v2, v0))
        profile.addGeometry(geoList, True)
    elif nr == 1:
        geoList = []
        geoList.append(Part.Point(App.Vector(0, 0, 0)))
        profile.addGeometry(geoList, True)

    constraintList = []
    if nr > 2:
        constraintList.append(Sketcher.Constraint('Coincident', -1, 1, cc, 3))
    elif nr == 2:
        constraintList.append(
            Sketcher.Constraint('PointOnObject', cl+1, 1, -2))
        constraintList.append(
            Sketcher.Constraint('DistanceY', cl+1, 1, -1, 1, p1_ypos))
        constraintList.append(
            Sketcher.Constraint('Coincident', -1, 1, cl, 2))
        constraintList.append(
            Sketcher.Constraint('Coincident', -1, 1, cl+1, 2))
    elif nr == 1:
        constraintList.append(Sketcher.Constraint('Coincident', -1, 1, cl, 1))
    constraintList.append(Sketcher.Constraint('Diameter', 0, j_d))
    constraintList.append(Sketcher.Constraint('Diameter', wo, wo_d))
    constraintList.append(Sketcher.Constraint('Diameter', wi, wi_d))
    if nr > 1:
        constraintList.append(
            Sketcher.Constraint('DistanceY', -1, 1, cl, 1, p1_ypos))
        constraintList.append(Sketcher.Constraint('PointOnObject', cl, 1, -2))
    for i in range(nr-1):
        # insulations equality:
        constraintList.append(Sketcher.Constraint('Equal', wo, wo+i+1))
        # wires equality:
        constraintList.append(Sketcher.Constraint('Equal', wi, wi+i+1))
    for i in range(nr):
        # insulation (outer ring) on point:
        constraintList.append(
            Sketcher.Constraint('Coincident', p+i, 1, wo+i, 3))
        # wire (inner ring) on point:
        constraintList.append(
            Sketcher.Constraint('Coincident', p+i, 1, wi+i, 3))
        # point on construction vertex:
        constraintList.append(
            Sketcher.Constraint('Coincident', cl+i, 1, p+i, 1))
    profile.addConstraint(constraintList)
    return profile


def createProfileSubWires(profile, norm, nr_of_wires, wo_nr):
    App = FreeCAD
    # Create Wire1, Wire2, Wire3, ... WireNr (single insulations)
    nr = nr_of_wires
    wo = wo_nr  # number of 1st single wire insulation (outer ring)
    geoList = []
    for i in range(nr):
        geoList.append(Part.Circle(App.Vector(i, 0, 0), norm, 2))
    profile.addGeometry(geoList, False)

    # Create WireNr+1, WireNr+2, WireNr+3, ... WireNr+Nr (single wire)
    wi = wo + nr    # number of 1st single wire (inner ring)
    geoList = []
    for i in range(nr):
        geoList.append(Part.Circle(App.Vector(i, 0, 0), norm, 1))
    profile.addGeometry(geoList, False)

    # Create Point1, Point2, Point3, PointNr (centers of single wires)
    p = wi + nr    # number of 1st point
    geoList = []
    for i in range(nr):
        geoList.append(Part.Point(App.Vector(i, 0, 0)))
    profile.addGeometry(geoList, False)
    return wo, wi, p, nr


def getPresets(presetfiles=profilefiles):
    list_all = readCablePresets(presetfiles)
    profiles = []
    presets = []
    presetnames = []
    for p in list_all:
        try:
            if p[2] in prof_class.values() and p[6] is not None:
                profiles.append(p)
            if p[2] == "PRESET" and p[5] is not None:
                presets.append(p)
                presetnames.append(f"{p[1]}_{int(p[4])}x{p[5]:g}_{p[3]}")
        except (IndexError, ValueError):
            FreeCAD.Console.PrintError(translate(
                "Cables", "Skipping bad profile or preset:") + f"{p}\n")

    presets_ext = []
    buf = []
    for i, pres in enumerate(presets):
        for prof in profiles:
            try:
                if pres[1] == prof[1] and pres[3] == prof[3]:
                    presets_ext.append(prof + [int(pres[4]), pres[5]])
                elif f"{prof[1]}_{prof[3]}" not in buf:
                    presets_ext.append(prof + [0, 0.0])
                buf.append(f"{prof[1]}_{prof[3]}")
            except (IndexError, ValueError):
                FreeCAD.Console.PrintError(translate(
                    "Cables", "Skipping bad profile or preset:") +
                        f"{prof}, {pres}\n")

    presetnames.sort()
    presetnames = ["Customized"] + presetnames
    return presetnames, presets_ext


# function copied from archProfile.py and adopted
def readCablePresets(pfiles=profilefiles):
    # When special type is detected on position row[1], the row[3] and higher
    # are treated as strings
    special_types = ["Fixed"]
    Presets = []
    bid = 1     # Unique index
    for profilefile in pfiles:
        if os.path.exists(profilefile):
            try:
                with open(profilefile, "r") as csvfile:
                    beamreader = csv.reader(csvfile)
                    for row in beamreader:
                        if (not row) or row[0].startswith("#"):
                            continue
                        try:
                            r = [bid, row[0], row[1], row[2]]
                            for i in range(3, len(row)):
                                if row[1] in special_types:
                                    r = r + [str(row[i])]
                                else:
                                    r = r + [float(row[i])]
                            if r not in Presets:
                                Presets.append(r)
                            bid = bid + 1
                        except (IndexError, ValueError):
                            FreeCAD.Console.PrintError(translate(
                                "Cables", "Skipping bad line:")
                                + " " + str(row) + f", [{csvfile.name}]\n")
            except IOError:
                FreeCAD.Console.PrintError(translate(
                    "Cables", "Could not open"), profilefile, "\n")
    return Presets
