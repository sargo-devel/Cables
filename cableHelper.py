"""cableHelper
"""

import FreeCAD
import Draft


def makeHelperPoint(placement=None, name=None):
    """creates a helper point
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    if placement:
        point = Draft.make_point(placement.Base)
    else:
        point = Draft.make_point(0.0, 0.0, 0.0)
    point.Label = name if name else "HelperPoint"
    point.ViewObject.PointSize = 8
    point.ViewObject.PointColor = (255, 85, 0)
    Draft.autogroup(point)
    point.addExtension('Part::AttachExtensionPython')
    return point


def makeHelperLine(p1=None, p2=None, name=None):
    """creates a helper line
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    pl = FreeCAD.Placement()
    dist = 30.0
    if p1 and p2:
        pl.Base = (p1+p2)/2
    elif p1:
        center = p1
        p1 = center + FreeCAD.Vector(-dist, 0.0, 0.0)
        p2 = center + FreeCAD.Vector(dist, 0.0, 0.0)
        pl.Base = center
    else:
        p1 = FreeCAD.Vector(-dist, 0.0, 0.0)
        p2 = FreeCAD.Vector(dist, 0.0, 0.0)
        pl.Base = (p1+p2)/2
    line = Draft.make_wire([p1, p2], placement=pl, closed=False,
                           face=False, support=None)
    line.Label = name if name else "HelperLine"
    #line.addExtension('Part::AttachExtensionPython')
    line.Subdivisions = 1
    line.ViewObject.PointSize = 8
    line.ViewObject.PointColor = (255, 85, 0)
    line.ViewObject.LineColor = (255, 170, 127)
    Draft.autogroup(line)
    return line
