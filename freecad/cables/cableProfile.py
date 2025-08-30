"""cableProfile
"""

import os
import csv
import math
import FreeCAD
import FreeCADGui
import Part
import Sketcher
import ProfileLib.RegularPolygon
from freecad.cables import uiPath, presetsPath


translate = FreeCAD.Qt.translate
ui_profile = os.path.join(uiPath, "profile.ui")
gauge_mm2_list = ['custom', '0.2', '0.5', '0.75', '1', '1.5', '2.5', '4', '6',
                  '10', '16', '25', '35', '50', '70', '95', '120']

# Presets in the form: Name, Profile class, Voltage Class, [profile data]
# Search for profiles.csv in presets and in the user path
profilefiles = [os.path.join(presetsPath, "profiles.csv"),
                os.path.join(FreeCAD.getUserAppDataDir(), "Cables",
                             "profiles.csv")]


class TaskPanelProfile:
    def __init__(self, gauge_list=gauge_mm2_list):
        self.form = FreeCADGui.PySideUic.loadUi(ui_profile)
        self.presets = readCablePresets()
        profile_list = [i[1]+'_'+i[3] for i in self.presets]
        self.form.comboProfile.addItems(profile_list)
        self.form.comboWireGauge.addItems(gauge_list)

    def accept(self):
        idx = self.form.comboProfile.currentIndex()
        profile = self.presets[idx]
        nr_of_wires = self.form.NumberOfWires.value()
        try:
            wire_gauge_mm2 = float(
                self.form.comboWireGauge.currentText())
        except ValueError:
            wire_gauge_mm2 = self.form.customWireGauge.value()
        c = "freecad.cables"
        doc = FreeCAD.ActiveDocument
        doc.openTransaction(translate("Cables", "Cable Profile"))
        FreeCADGui.addModule(f"{c}")
        FreeCADGui.doCommand(f"{c}.cableProfile.makeCableProfile(" +
                             f"{profile}, {nr_of_wires}, {wire_gauge_mm2})")
        FreeCADGui.doCommand("FreeCAD.ActiveDocument.recompute()")
        doc.commitTransaction()
        FreeCADGui.Control.closeDialog()


def makeCableProfile(profile=[1, 'YDYp', 'F', '750V', 1.45, 0.7, 0.1],
                     nr_of_wires=3, wire_gauge_mm2=1.5):
    """Makes cable profile
    profile=[idx,name,profile_class,voltage_class,jacket_thickness,
             single_insulation_thickness,insul_dist]
    """
    label = f"{profile[1]}{nr_of_wires}x{wire_gauge_mm2}_{profile[3]}"
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


def makeCableProfileF(label, insul=[1.45, 0.7, 0.1], nr_of_wires=3,
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


def makeCableProfileR(label, insul=[1.45, 0.7, 0.1], nr_of_wires=3,
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
                        except ValueError:
                            FreeCAD.Console.PrintError(translate(
                                "Cables", "Skipping bad line:")
                                + " " + str(row) + "\n")
            except IOError:
                FreeCAD.Console.PrintError(translate(
                    "Cables", "Could not open"), profilefile, "\n")
    return Presets
