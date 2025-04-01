"""wireFlex based on Draft.Wire
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
import FreeCAD
import Draft
import Part
from draftutils import utils
from freecad.cables import wireutils
from freecad.cables import iconPath
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP

if FreeCAD.GuiUp:
    import FreeCADGui as Gui

CLASS_WIREFLEX_ICON = os.path.join(iconPath, "classWireFlex.svg")
tol = 1e-6


class WireFlex(Draft.Wire):
    """The WireFlex class
    """
    def __init__(self, obj):
        """Add the properties"""
        self.setProperties(obj)
        obj.Proxy = self
        self.Type = 'Wire'
        obj.Label = 'WireFlex'

    def setProperties(self, obj):
        pl = obj.PropertiesList
        if "Vrtx_start" not in pl:
            obj.addProperty("App::PropertyLinkSub", "Vrtx_start", "WireFlex",
                            QT_TRANSLATE_NOOP("App::Property", "First Vertex"))
        if "Vrtx_end" not in pl:
            obj.addProperty("App::PropertyLinkSub", "Vrtx_end", "WireFlex",
                            QT_TRANSLATE_NOOP("App::Property", "Last Vertex"))
        if "Vrtxs_mid" not in pl:
            obj.addProperty("App::PropertyLinkSubList", "Vrtxs_mid",
                            "WireFlex",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "List of middle vertexes"))
        if "Vrtxs_mid_idx" not in pl:
            obj.addProperty("App::PropertyIntegerList", "Vrtxs_mid_idx",
                            "WireFlex",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Point indexes for list of " +
                                "middle vertexes"))
        if "PathType" not in pl:
            obj.addProperty("App::PropertyEnumeration", "PathType",
                            "WireFlexShape",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Type of wire shape"))
            obj.PathType = ['Wire', 'BSpline_P', 'BSpline_K']
        if "BoundarySegmentStart" not in pl:
            obj.addProperty("App::PropertyLength", "BoundarySegmentStart",
                            "WireFlexShape",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Length of boundary " +
                                "segment at the start of wire"))
        if "BoundarySegmentEnd" not in pl:
            obj.addProperty("App::PropertyLength", "BoundarySegmentEnd",
                            "WireFlexShape",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Length of boundary " +
                                "segment at the end of wire"))
        if "Parameterization" not in pl:
            obj.addProperty("App::PropertyFloat", "Parameterization",
                            "WireFlexShape",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Parameterization factor"))
        if "FilletRadius" in pl and \
                obj.getGroupOfProperty("FilletRadius") == "Draft":
            obj.setGroupOfProperty("FilletRadius", "WireFlexShape")
        if "Length" in pl and obj.getGroupOfProperty("Length") == "Draft":
            obj.setGroupOfProperty("Length", "WireFlexShape")

        pl = obj.PropertiesList
        proplist = ["Start", "End", "MakeFace", "ChamferSize", "Closed",
                    "Subdivisions"]
        for prop in proplist:
            if (prop in pl) and \
               (str(obj.getPropertyStatus(prop)[0]) != "Hidden"):
                obj.setPropertyStatus(prop, "Hidden")

    def onDocumentRestored(self, obj):
        super().onDocumentRestored(obj)
        self.setProperties(obj)

    def onChanged(self, obj, prop):
        # FreeCAD.Console.PrintMessage(f"Changed property: {prop} \n")
        super().onChanged(obj, prop)
        if prop == 'PathType':
            FreeCAD.Console.PrintMessage(f"pt={prop},{obj.PathType}\n")
            if obj.PathType == 'Wire':
                hide_list = ['BoundarySegmentStart', 'BoundarySegmentEnd',
                             'Parameterization']
                unhide_list = ['FilletRadius']
            if obj.PathType == 'BSpline_P':
                hide_list = ['FilletRadius', 'Parameterization']
                unhide_list = ['BoundarySegmentStart', 'BoundarySegmentEnd']
            if obj.PathType == 'BSpline_K':
                hide_list = ['FilletRadius']
                unhide_list = ['BoundarySegmentStart', 'BoundarySegmentEnd',
                               'Parameterization']
            for element in hide_list:
                obj.setPropertyStatus(element, "Hidden")
            for element in unhide_list:
                obj.setPropertyStatus(element, "-Hidden")

    def get_vlist(self, obj):
        """It gets vector list of all attached wire points
        """
        vlist = [None] * len(obj.Points)
        if len(obj.Points) > 1:
            vstart = wireutils.getVector(obj, "Vrtx_start", "Vertex")
            vend = wireutils.getVector(obj, "Vrtx_end", "Vertex")
            vmid_lst = wireutils.getVector(obj, "Vrtxs_mid", "Vertex")
            if vmid_lst:
                for element in zip(obj.Vrtxs_mid_idx, vmid_lst):
                    vlist[element[0]-1] = element[1]
            vlist[0] = vstart
            vlist[-1] = vend
        return vlist

    def update_vrtxs_mid(self, obj, vlist):
        """It recalculates Vrtxs_mid and Vrtxs_mid_idx lists
        after a point addition or deletion
        """
        new_vrtxs_mid_idx = []
        old_vrtxs_mid_idx = obj.Vrtxs_mid_idx
        for id, vect in enumerate(vlist[1:-1]):
            if vect:
                new_vrtxs_mid_idx.append(id+2)
        if len(old_vrtxs_mid_idx) > len(new_vrtxs_mid_idx):     # point deleted
            diff = [i for i in old_vrtxs_mid_idx if i not in new_vrtxs_mid_idx]
            # assumption len(diff) == 1
            idx = old_vrtxs_mid_idx.index(diff[0])
            vrtxs_mid = wireutils.getFlatLinkSubList(obj, 'Vrtxs_mid')
            vrtxs_mid.pop(idx)
            obj.Vrtxs_mid = vrtxs_mid
        obj.Vrtxs_mid_idx = new_vrtxs_mid_idx

    def recalculate_points(self, obj):
        """It recalculates all points from obj.Points
        """
        vlist = self.get_vlist(obj)
        pts = obj.Points
        for idx, vect in enumerate(vlist):
            if vect:
                pts[idx] = vect - obj.Placement.Base
        if pts != obj.Points:
            obj.Points = pts

    def execute(self, obj):
        # FreeCAD.Console.PrintMessage(f"Execute started({obj.Label})" + "\n")
        obj.positionBySupport()
        self.recalculate_points(obj)
        if obj.PathType == 'Wire':
            super().execute(obj)
        elif obj.PathType == 'BSpline_P':
            self.execute_bspline_p(obj)
        elif obj.PathType == 'BSpline_K':
            self.execute_bspline_k(obj)

    def execute_bspline_p(self, obj):
        points = obj.Points
        points, idxs, idxe = self.appendStartEndSegment(obj, points)
        edges = []
        if obj.BoundarySegmentStart > 0:
            edges.append(Part.LineSegment(points[0], points[1]).toShape())
        if obj.BoundarySegmentEnd > 0:
            edges.append(Part.LineSegment(points[-2], points[-1]).toShape())
        spline = Part.BSplineCurve()
        spline.buildFromPoles(points[idxs:idxe])
        edges.insert(idxs or 0, spline.toShape())
        try:
            shape = Part.Wire(edges)
        except Part.OCCError:
            FreeCAD.Console.PrintError(translate(
                "Cables", "Error wiring edges for BSpline_P") + "\n")
            shape = None
        if shape:
            obj.Shape = shape

    def execute_bspline_k(self, obj):
        points = obj.Points
        points, idxs, idxe = self.appendStartEndSegment(obj, points)
        edges = []
        if obj.BoundarySegmentStart > 0:
            edges.append(Part.LineSegment(points[0], points[1]).toShape())
        if obj.BoundarySegmentEnd > 0:
            edges.append(Part.LineSegment(points[-2], points[-1]).toShape())
        spline = Part.BSplineCurve()
        vinit = (points[1] - points[0]).normalize()
        vfinal = (points[-1] - points[-2]).normalize()
        knotSeq = self.parameterization(points[idxs:idxe],
                                        obj.Parameterization, False)
        spline.interpolate(points[idxs:idxe], Parameters=knotSeq,
                           InitialTangent=vinit, FinalTangent=vfinal)
        edges.insert(idxs or 0, spline.toShape())
        try:
            shape = Part.Wire(edges)
        except Part.OCCError:
            FreeCAD.Console.PrintError(translate(
                "Cables", "Error wiring edges for BSpline_K") + "\n")
            shape = None
        if shape:
            obj.Shape = shape

    def appendStartEndSegment(self, obj, points):
        rs = obj.BoundarySegmentStart.Value
        re = obj.BoundarySegmentEnd.Value
        idx_s = idx_e = None
        if rs > 0:
            idx_s = 1
            v0 = points[0]
            v1 = points[1]
            new_point = v0 + (v1-v0).normalize()*rs
            if (v1-v0).Length > (new_point-v0).Length:
                points.insert(1, new_point)
            else:
                points.insert(2, new_point)
        if re > 0:
            idx_e = -1
            v0 = points[-2]
            v1 = points[-1]
            new_point = v1 - (v1-v0).normalize()*re
            if (v1-v0).Length > (new_point-v1).Length:
                points.insert(len(points)-1, new_point)
            else:
                points.insert(len(points)-2, new_point)
        return points, idx_s, idx_e

    def parameterization(self, pts, a, closed):
        """Computes a knot Sequence for a set of points.
        fac (0-1) : parameterization factor
        fac = 0 -> Uniform / fac=0.5 -> Centripetal / fac=1.0 -> Chord-Length
        Function copied from Draft.bspline
        """
        if closed:
            # we need to add the first point as the end point
            pts.append(pts[0])
        params = [0]
        for i in range(1, len(pts)):
            p = pts[i].sub(pts[i-1])
            pl = pow(p.Length, a)
            params.append(params[-1] + pl)
        return params


class ViewProviderWireFlex(Draft.ViewProviderWire):
    """A base View Provider for the WireFlex object.
    """
    def __init__(self, vobj):
        super().__init__(vobj)
        vobj.PointColor = (0, 102, 0)
        vobj.PointSize = 8
        vobj.LineColor = (176, 176, 176)
        vobj.LineWidth = 2

    def getIcon(self):
        return CLASS_WIREFLEX_ICON

    def attach(self, vobj):
        super().attach(vobj)

    def updateData(self, obj, prop):
        super().updateData(obj, prop)

    def onChanged(self, vobj, prop):
        super().onChanged(vobj, prop)

    def setEdit(self, vobj, mode=0):
        if mode == 1 or mode == 2:
            return None

        if utils.get_type(vobj.Object) in ("Wire", "Circle", "Ellipse",
                                           "Rectangle", "Polygon",
                                           "BSpline", "BezCurve"):
            if ("Cables_Edit" not in Gui.listCommands()) \
                    or (not hasattr(FreeCAD, 'activeDraftCommand')):
                self.wb_before_edit = Gui.activeWorkbench()
                Gui.activateWorkbench("CablesWorkbench")
                Gui.activateWorkbench("DraftWorkbench")
            Gui.runCommand("Cables_Edit")
            return True

        return None


def make_wireflex(plist=None):
    """
    It creates a new object of WireFlex

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
    """
    if not plist:
        plist = wireutils.processGuiSelection(
            single=False, subshape_class=Part.Vertex, obj_proxy_class=None)
    if not plist:
        return None
    pl = FreeCAD.Placement()
    pl.Rotation.Q = (0.0, 0.0, 0.0, 1.0)
    pl.Base = wireutils.getVector(plist[0])
    vpoints = []
    for plink in plist:
        vpoints.append(wireutils.getVector(plink))
    base_wire = Draft.make_wire(vpoints, placement=pl, closed=False,
                                face=False, support=None)
    if plist[0][1]:
        base_wire.AttachmentSupport = [plist[0]]
        base_wire.MapMode = 'Translate'
    WireFlex(base_wire)
    ViewProviderWireFlex(base_wire.ViewObject)
    base_wire.PathType = 'Wire'
    base_wire.Parameterization = 1.0
    base_wire.BoundarySegmentStart = 10.0
    base_wire.BoundarySegmentEnd = 10.0
    base_wire.Vrtx_start = plist[0]
    base_wire.Vrtx_end = plist[-1]
    vrtxs_mid = wireutils.getFlatLinkSubList(base_wire, 'Vrtxs_mid')
    vrtxs_mid_idx = base_wire.Vrtxs_mid_idx
    for nr, vrtx_new in enumerate(plist[1:-1]):
        vrtxs_mid.append(vrtx_new)
        vrtxs_mid_idx.append(nr+2)
    base_wire.Vrtxs_mid = vrtxs_mid
    base_wire.Vrtxs_mid_idx = vrtxs_mid_idx
    return base_wire


def make_wireflex_from_vectors(vectorlist):
    """
    It creates a new object of WireFlex

    Parameters
    ----------
    vectorlist : list
        List of Vectors used to create WireFlex
        No attachments are made

    Returns
    -------
    WireFlex object
    """
    pl = FreeCAD.Placement()
    pl.Rotation.Q = (0.0, 0.0, 0.0, 1.0)
    pl.Base = vectorlist[0]
    vpoints = vectorlist
    base_wire = Draft.make_wire(vpoints, placement=pl, closed=False,
                                face=False, support=None)
    WireFlex(base_wire)
    ViewProviderWireFlex(base_wire.ViewObject)
    return base_wire
