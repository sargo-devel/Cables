"""cableProfile
"""

import FreeCAD
import Part
import Sketcher


def makeCableProfile():
    """
    Example profile for cable YDYp 3x1.5
    """
    # Cable dimensions [mm]
    w = 11.3
    h = 5.4
    d_in1 = 2.8
    d_in2 = 1.4
    label = "ProfileYDYp3x1.5"

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

    # Create Wire0
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

    # Create Wire1, Wire2, Wire3
    v5 = App.Vector(-20, 0, 0)
    v6 = App.Vector(0, 0, 0)
    v7 = App.Vector(20, 0, 0)
    d1 = 5
    vlist = [v5, v6, v7]
    geoList = []
    for v in vlist:
        geoList.append(Part.Circle(v, App.Vector(0, 0, 1), d1))
    profile.addGeometry(geoList, False)
    constraintList = []
    constraintList.append(Sketcher.Constraint('Coincident', 4, 3, 3, 3))
    constraintList.append(Sketcher.Constraint('Coincident', 5, 3, -1, 1))
    constraintList.append(Sketcher.Constraint('Coincident', 6, 3, 1, 3))
    constraintList.append(Sketcher.Constraint('Equal', 4, 5))
    constraintList.append(Sketcher.Constraint('Equal', 5, 6))
    profile.addConstraint(constraintList)

    # Create Wire4, Wire5, Wire6
    d2 = 2
    geoList = []
    for v in vlist:
        geoList.append(Part.Circle(v, App.Vector(0, 0, 1), d2))
    profile.addGeometry(geoList, False)
    constraintList = []
    constraintList.append(Sketcher.Constraint('Coincident', 7, 3, 3, 3))
    constraintList.append(Sketcher.Constraint('Coincident', 8, 3, -1, 1))
    constraintList.append(Sketcher.Constraint('Coincident', 9, 3, 1, 3))
    constraintList.append(Sketcher.Constraint('Equal', 7, 8))
    constraintList.append(Sketcher.Constraint('Equal', 8, 9))
    profile.addConstraint(constraintList)

    # Create Point1, Point2, Point3
    geoList = []
    for v in vlist:
        geoList.append(Part.Point(v))
    profile.addGeometry(geoList, False)
    constraintList = []
    constraintList.append(Sketcher.Constraint('Coincident', 10, 1, 3, 3))
    constraintList.append(Sketcher.Constraint('Coincident', 11, 1, -1, 1))
    constraintList.append(Sketcher.Constraint('Coincident', 12, 1, 1, 3))
    profile.addConstraint(constraintList)

    # Add final dimensions
    d_ext = h
    x = w - d_ext
    constraintList = []
    constraintList.append(Sketcher.Constraint('DistanceX', 3, 3, 1, 3, x))
    constraintList.append(Sketcher.Constraint('Diameter', 3, d_ext))
    constraintList.append(Sketcher.Constraint('Diameter', 4, d_in1))
    constraintList.append(Sketcher.Constraint('Diameter', 7, d_in2))
    profile.addConstraint(constraintList)

    return profile
