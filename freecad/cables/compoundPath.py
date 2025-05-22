"""compoundPath
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
import Part
import DraftGeomUtils
from freecad.cables import wireutils
from freecad.cables import iconPath
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP


CLASS_COMPOUNDPATH_ICON = os.path.join(iconPath, "classCompoundPath.svg")
tol = 1e-6     # tolerance for isEqual() comparision


class CompoundPath:
    """The CompoundPath class
    """
    def __init__(self, obj):
        """Add the properties"""
        self.setProperties(obj)
        obj.Proxy = self

    def setProperties(self, obj):
        pl = obj.PropertiesList
        if "Links" not in pl:
            obj.addProperty("App::PropertyLinkList", "Links", "Base",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "List of objects added " +
                                "to the compound path"))
        if "PathType" not in pl:
            obj.addProperty("App::PropertyEnumeration", "PathType",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Type of compound shape"))
            obj.PathType = ['Complex', 'Wire', 'Simple']
        if "MinimumFilletRadius" not in pl:
            obj.addProperty("App::PropertyLength", "MinimumFilletRadius",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Minimum radius to use to " +
                                "fillet the corners"))
        if "SmallestBendingRadius" not in pl:
            obj.addProperty("App::PropertyLength", "SmallestBendingRadius",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Smallest detected radius " +
                                "across all edges"))
            obj.setPropertyStatus("SmallestBendingRadius", "ReadOnly")
        if "EdgeWithSmallestBendingRadius" not in pl:
            obj.addProperty("App::PropertyString",
                            "EdgeWithSmallestBendingRadius", "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Edge containing smallest " +
                                "radius or preceding smallest radius if " +
                                "radius is 0"))
            obj.setPropertyStatus("EdgeWithSmallestBendingRadius", "ReadOnly")
        if "Length" not in pl:
            obj.addProperty("App::PropertyLength", "Length",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The length of this path"))
            obj.setEditorMode("Length", 1)
        if "Points" not in pl:
            obj.addProperty("App::PropertyVectorList", "Points",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The points of the path"))
        if "ConnectionOffsetDist" not in pl:
            obj.addProperty("App::PropertyLength", "ConnectionOffsetDist",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Length of connection " +
                                "offset distance"))
        if "ConnectionOffsetAngle" not in pl:
            obj.addProperty("App::PropertyAngle", "ConnectionOffsetAngle",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Angle of connection " +
                                "offset distance"))
        if "ConnectionType" not in pl:
            obj.addProperty("App::PropertyEnumeration", "ConnectionType",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Type of added/modified " +
                                "connection curves between edges"))
            obj.ConnectionType = ['Arc', 'Bez']
        if "Ratio" not in pl:
            obj.addProperty("App::PropertyFloat", "Ratio",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The proportions of " +
                                "segments in the added base curve. " +
                                "Should be between 1 and 2."))
        if "Degree" not in pl:
            obj.addProperty("App::PropertyInteger", "Degree",
                            "CompoundPath",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The degree of the Bezier " +
                                "function. Best is 3"))
        self.Type = "Wire"

    def onDocumentRestored(self, obj):
        self.setProperties(obj)

    def onChanged(self, obj, prop):
        # FreeCAD.Console.PrintMessage(f"Changed property: {prop} \n")
        if prop == 'PathType':
            if obj.PathType == 'Simple':
                hide_list = ['ConnectionOffsetAngle', 'ConnectionOffsetDist',
                             'MinimumFilletRadius', 'SmallestBendingRadius',
                             'EdgeWithSmallestBendingRadius', 'ConnectionType',
                             'Ratio', 'Degree']
                unhide_list = []
            if obj.PathType == 'Wire':
                hide_list = []
                unhide_list = ['ConnectionOffsetAngle', 'ConnectionOffsetDist',
                               'MinimumFilletRadius', 'SmallestBendingRadius',
                               'EdgeWithSmallestBendingRadius']
            if obj.PathType == 'Complex':
                hide_list = []
                unhide_list = ['ConnectionOffsetAngle', 'ConnectionOffsetDist',
                               'MinimumFilletRadius', 'SmallestBendingRadius',
                               'EdgeWithSmallestBendingRadius',
                               'ConnectionType', 'Ratio', 'Degree']
            for element in hide_list:
                obj.setPropertyStatus(element, "Hidden")
            for element in unhide_list:
                obj.setPropertyStatus(element, "-Hidden")
        if prop == "Links" and hasattr(obj, prop):
            if FreeCAD.GuiUp:
                for o in getattr(obj, prop):
                    o.ViewObject.hide()
        if prop == "Shape":
            obj.Length = obj.Shape.Length
            if obj.PathType == 'Wire' or obj.PathType == 'Complex':
                self.Type = "Wire"
            if obj.PathType == 'Simple':
                self.Type = "Compound"
            if hasattr(obj, "SmallestBendingRadius") and \
                    hasattr(obj, "EdgeWithSmallestBendingRadius"):
                if obj.PathType != 'Simple':
                    r, nr = wireutils.getMinimumRadius(obj.Shape.Wires[0])
                    obj.SmallestBendingRadius = r
                    if r == 1e10 and nr == 0:
                        # Straight line with no radius
                        obj.EdgeWithSmallestBendingRadius = "None"
                    else:
                        obj.EdgeWithSmallestBendingRadius = f"Edge{nr}"
        if prop == "Degree":
            deg = 1 if obj.Degree < 1 else obj.Degree
            deg = 3 if deg > 3 else deg
            if deg != obj.Degree:
                obj.Degree = deg
        if prop == "Ratio":
            ratio = 0.1 if obj.Ratio < 0.1 else obj.Ratio
            ratio = 3.0 if ratio > 3.0 else ratio
            if ratio != obj.Ratio:
                obj.Ratio = ratio

    def execute(self, obj):
        # FreeCAD.Console.PrintMessage(f"Execute started({obj.Label})" + "\n")
        edg_cnt_old = len(obj.Shape.Edges) if hasattr(obj, "Shape") else 0

        shapes = []
        if obj.PathType == 'Simple':
            for element in obj.Links:
                shapes.append(element.Shape)
        elif obj.PathType == 'Complex':
            points, edges = self.getEdgesList(obj)
            if points is None or edges is None:
                return
            sh = Part.Wire(edges)
            shapes.append(sh)
            obj.Points = points
        elif obj.PathType == 'Wire':
            points, _ = self.getEdgesList(obj)
            if points is None:
                return
            sh = Part.makePolygon(points)
            if obj.MinimumFilletRadius.Value > 0:
                sh = DraftGeomUtils.filletWire(
                    sh, obj.MinimumFilletRadius.Value)
            shapes.append(sh)
            obj.Points = points
        shape = Part.makeCompound(shapes)

        edg_cnt_new = len(shape.Edges)
        if edg_cnt_new < edg_cnt_old:
            # fix potential attachment problem with parent's subprofile 2
            # due to non existent attachment edge:
            # "PositionBySupport: AttachEngine3D: subshape not found"
            for exists, parent in wireutils.isBaseWire(obj):
                if exists and hasattr(parent, "SubProfiles") and \
                        len(parent.SubProfiles) == 2:
                    # check if parent subprofiles need recompute
                    parent.SubProfiles[1].MapMode = "Deactivated"

        obj.Shape = shape
        # FreeCAD.Console.PrintMessage(f"Execute ended({obj.Label})" + "\n")

    def getPointsList(self, obj, groups=False):
        '''Returns list of points properly ordered.
        If groups=False it returns flat list, otherwise list of lists
        '''
        points = []
        gaps = []
        links_len = len(obj.Links)
        for i, link in enumerate(obj.Links):
            if not hasattr(link, 'Points'):
                FreeCAD.Console.PrintError(f"{link.Label}", translate(
                    "Cables", "link object has no Points" +
                    "property"))
                continue
            if i+1 < links_len:
                next_link = obj.Links[i+1]
                reverse_link, reverse_next_link = self.needsReverse(link,
                                                                    next_link)
                if i == 0:
                    pts = link.Points
                    if reverse_link:
                        pts.reverse()
                    pts_global = [link.Placement.multVec(v) for v in pts]
                    points.append(pts_global)
                pts = next_link.Points
                if reverse_next_link:
                    pts.reverse()
                pts_global = [next_link.Placement.multVec(v) for v in pts]
                if not points[-1][-1].isEqual(pts_global[0], tol):
                    gaps.append((i, (points[-1][-1], pts_global[0])))
                points.append(pts_global)
        if not groups:
            points = [p for group in points for p in group]
        return points, gaps

    def getEdgesList(self, obj):
        '''Returns list of points and edges properly ordered
        '''
        edges = []
        if not hasattr(obj, 'Links') or len(obj.Links) < 2:
            return [], []

        # get points
        points, gaps = self.getPointsList(obj, groups=True)

        # add offset to points
        for i, pts in enumerate(points):
            if i < len(points)-1:
                pts_nxt = points[i+1]
                if pts[-1].isEqual(pts_nxt[0], tol):
                    pts = self.addEndPointOffset(obj, pts)
                    pts_nxt = self.addStartPointOffset(obj, pts_nxt)
                    p1s, p1e = pts[-2], pts[-1]
                    p2s, p2e = pts_nxt[1], pts_nxt[0]
                    e1 = Part.Edge(Part.LineSegment(p1s, p1e))
                    e2 = Part.Edge(Part.LineSegment(p2s, p2e))
                    dist = e1.distToShape(e2)
                    if dist[0] < tol:
                        pts[-1] = dist[1][0][0]
                        pts_nxt[0] = pts[-1]
                    else:
                        p1e = e1.valueAt(e1.LastParameter*10)
                        p2e = e2.valueAt(e2.LastParameter*10)
                        e1 = Part.Edge(Part.LineSegment(p1s, p1e))
                        e2 = Part.Edge(Part.LineSegment(p2s, p2e))
                        dist = e1.distToShape(e2)
                        # set points independently of distance
                        pts[-1] = dist[1][0][0]
                        pts_nxt[0] = pts[-1]
                else:
                    pts = self.addEndPointOffset(obj, pts)
                    pts_nxt = self.addStartPointOffset(obj, pts_nxt)

        # get list of edges in groups
        edges_counter = []
        for i, link in enumerate(obj.Links):
            edges.append(link.Shape.Edges)
            edges_counter.append(len(link.Shape.Edges))

        # detect too short edges inside groups
        for i, edgs in enumerate(edges):
            for j, edge in enumerate(edgs):
                if edge.Length < tol:
                    FreeCAD.Console.PrintError(
                        f"{obj.Label}", f"Edge{j+1} of {obj.Links[i].Label} " +
                        "too short! " +
                        translate("Cables", "Unable to build compound path") +
                        "\n")
                    return None, None

        # add temporary gap connections and start connection
        ps = points[0][0]
        start_point = FreeCAD.Vector(ps.x-0.1, ps.y, ps.z)
        start_edge = Part.Edge(Part.LineSegment(start_point, points[0][0]))
        edges.insert(0, [start_edge])
        for g in gaps:
            gap_edge = Part.Edge(Part.LineSegment(g[1][0], g[1][1]))
            edges.append([gap_edge])

        # sort edges
        edges = [e for group in edges for e in group]
        edges = Part.sortEdges(edges)[0]

        # split edges back into groups
        edges.pop(0)        # remove temporary start_edge
        new_edges = []
        for i, counter in enumerate(edges_counter):
            new_edges.append(edges[:counter])
            if gaps and i == gaps[0][0]:
                edges.pop(0)    # remove temporary gap_edge
                gaps.pop(0)
            edges = edges[counter:]
        edges = new_edges
        # FreeCAD.Console.PrintMessage("edges after sort = " +
        #     f"{[e.Length for edgs in edges for e in edgs]} \n")

        # add offset to edges
        for i, edgs in enumerate(edges):
            if i < len(edges)-1:
                point_end = points[i][-1]
                point_nxt_start = points[i+1][0]
                edgs_nxt = edges[i+1]
                edge_end = Part.Edge(Part.LineSegment(
                    edgs[-1].Vertexes[0].Point, point_end))
                edge_nxt_start = Part.Edge(Part.LineSegment(
                    point_nxt_start, edgs_nxt[0].Vertexes[1].Point))
                edgs[-1] = edge_end
                edgs_nxt[0] = edge_nxt_start

        # make corrections of edges tangency inside groups
        for i, edgs in enumerate(edges):
            if len(edgs) > 2 and edgs[1].Curve.TypeId == 'Part::GeomCircle':
                # check tangency and apply corrections at the start
                # FreeCAD.Console.PrintMessage(f"[compPath] opt1, {i}\n")
                c_tan = edgs[1].tangentAt(edgs[1].FirstParameter)
                l_tan = edgs[0].tangentAt(edgs[0].LastParameter)
                if not l_tan.isEqual(c_tan, tol):
                    v1 = edgs[0].Vertexes[0].Point
                    vx = points[i][1]
                    v2 = edgs[2].Vertexes[1].Point
                    edge1 = Part.Edge(Part.LineSegment(v1, vx))
                    edge2 = Part.Edge(Part.LineSegment(vx, v2))
                    virtwire = wireutils.makeConnectionWith2Fillets(
                        edge1, edge2, ctype=obj.ConnectionType,
                        deg=obj.Degree, ratio=obj.Ratio,
                        radius=edgs[1].Curve.Radius)
                    del edgs[:3]
                    edgs[0:0] = virtwire.Edges
            if len(edgs) > 2 and edgs[-2].Curve.TypeId == 'Part::GeomCircle':
                # check tangency and apply corrections at the end
                # FreeCAD.Console.PrintMessage(f"[compPath] opt2, {i}\n")
                c_tan = edgs[-2].tangentAt(edgs[-2].LastParameter)
                l_tan = edgs[-1].tangentAt(edgs[-1].FirstParameter)
                if not l_tan.isEqual(c_tan, tol):
                    v1 = edgs[-3].Vertexes[0].Point
                    vx = points[i][-2]
                    v2 = edgs[-1].Vertexes[1].Point
                    edge1 = Part.Edge(Part.LineSegment(v1, vx))
                    edge2 = Part.Edge(Part.LineSegment(vx, v2))
                    virtwire = wireutils.makeConnectionWith2Fillets(
                        edge1, edge2, ctype=obj.ConnectionType,
                        deg=obj.Degree, ratio=obj.Ratio,
                        radius=edgs[-2].Curve.Radius)
                    del edgs[-3:]
                    edgs.extend(virtwire.Edges)
            if len(edgs) > 1 and edgs[1].Curve.TypeId == \
                    'Part::GeomBSplineCurve':
                # check tangency and apply corrections at the start
                # FreeCAD.Console.PrintMessage(f"[compPath] opt3, {i}\n")
                c_tan = edgs[1].tangentAt(edgs[1].FirstParameter)
                l_tan = edgs[0].tangentAt(edgs[0].LastParameter)
                if not l_tan.isEqual(c_tan, tol):
                    virtwire = wireutils.makeConnectionWith2Fillets(
                        edgs[0], edgs[1], ctype=obj.ConnectionType,
                        deg=obj.Degree, ratio=obj.Ratio,
                        radius=obj.MinimumFilletRadius.Value)
                    del edgs[:2]
                    edgs[0:0] = virtwire.Edges
            if len(edgs) > 1 and edgs[-2].Curve.TypeId == \
                    'Part::GeomBSplineCurve':
                # check tangecy and apply corrections at the end
                # FreeCAD.Console.PrintMessage(f"[compPath] opt4, {i}\n")
                c_tan = edgs[-2].tangentAt(edgs[-2].LastParameter)
                l_tan = edgs[-1].tangentAt(edgs[-1].FirstParameter)
                if not l_tan.isEqual(c_tan, tol):
                    virtwire = wireutils.makeConnectionWith2Fillets(
                        edgs[-2], edgs[-1], ctype=obj.ConnectionType,
                        deg=obj.Degree, ratio=obj.Ratio,
                        radius=obj.MinimumFilletRadius.Value)
                    del edgs[-2:]
                    edgs.extend(virtwire.Edges)

        # add tangent connections between groups
        # FreeCAD.Console.PrintMessage(
        #    "edges after tangency corrections inside groups=" +
        #    f"{[e.Length for edgs in edges for e in edgs]}\n")
        for i, edgs in enumerate(edges):
            if i < len(edges)-1:
                virtwire = wireutils.makeConnectionWith2Fillets(
                    edgs[-1], edges[i+1][0], ctype=obj.ConnectionType,
                    deg=obj.Degree, ratio=obj.Ratio,
                    radius=obj.MinimumFilletRadius.Value)
                edgs.pop()
                edgs.extend(virtwire.Edges[:-1])
                edges[i+1].pop(0)
                edges[i+1].insert(0, virtwire.Edges[-1])

        # FreeCAD.Console.PrintMessage(
        #    "edges after tangency corrections between groups=" +
        #    f"{[e.Length for edgs in edges for e in edgs]}\n")

        # remove duplicate points
        for i, pts in enumerate(points):
            if i < len(points)-1:
                if pts[-1].isEqual(points[i+1][0], tol):
                    pts.pop()

        points = [p for group in points for p in group]
        edges = [e for group in edges for e in group]

        # join tangent edges of type 'Part::GeomLine'
        new_edges = []
        e_curr = None
        for i, e in enumerate(edges):
            if e_curr is None:
                e_curr = e
                if e_curr.Curve.TypeId != 'Part::GeomLine':
                    new_edges.append(e_curr)
                    e_curr = None
            else:
                if e.Curve.TypeId == 'Part::GeomLine' and \
                        e_curr.tangentAt(0).isEqual(e.tangentAt(0), tol):
                    e_curr = Part.Edge(Part.LineSegment(
                        e_curr.Vertexes[0].Point, e.Vertexes[1].Point))
                else:
                    new_edges.append(e_curr)
                    new_edges.append(e)
                    e_curr = None
        if e_curr is not None:
            new_edges.append(e_curr)
        edges = new_edges

        # FreeCAD.Console.PrintMessage(
        #    f"edges final = {[e.Length for e in edges]}\n")
        return points, edges

    def needsReverse(self, last_link, link):
        '''Checks if argument lines need reverse
        '''
        dist_list = []
        v1 = last_link.Shape.Vertexes[0].Point
        v2 = last_link.Shape.Vertexes[-1].Point
        v3 = link.Shape.Vertexes[0].Point
        v4 = link.Shape.Vertexes[-1].Point
        dist_list = [v1.distanceToPoint(v3), v1.distanceToPoint(v4),
                     v2.distanceToPoint(v3), v2.distanceToPoint(v4)]
        idx = dist_list.index(min(dist_list))
        decisions = [(True, False), (True, True), (False, False),
                     (False, True)]
        return decisions[idx]

    def appendStartEndSegment(self, obj, points):
        r = obj.BoundarySegment.Value
        if r > 0:
            v0 = points[0]
            v1 = points[1]
            new_point = v0 + (v1-v0).normalize()*r
            points.insert(1, new_point)

            v0 = points[-2]
            v1 = points[-1]
            new_point = v1 - (v1-v0).normalize()*r
            points.insert(len(points)-1, new_point)
        return points

    def addEndPointOffset(self, obj, points):
        if obj.ConnectionOffsetDist.Value > 0:
            endedge = Part.Edge(Part.LineSegment(points[-1], points[-2]))
            vnorm = DraftGeomUtils.get_shape_normal(endedge)
            # prepare to rotation
            base = FreeCAD.Vector(0, 0, 0)
            direction = points[-1] - points[-2]
            edge = Part.Edge(Part.LineSegment(base, vnorm))
            # rotate
            edge.rotate(base, direction, obj.ConnectionOffsetAngle.Value)
            # get rotated point
            voffset = points[-1] + \
                edge.Vertexes[1].Point*obj.ConnectionOffsetDist.Value
            points.pop(-1)
            points.append(voffset)
        return points

    def addStartPointOffset(self, obj, points):
        if obj.ConnectionOffsetDist.Value > 0:
            startedge = Part.Edge(Part.LineSegment(points[0], points[1]))
            vnorm = DraftGeomUtils.get_shape_normal(startedge)
            # prepare to rotation
            base = FreeCAD.Vector(0, 0, 0)
            direction = points[1] - points[0]
            edge = Part.Edge(Part.LineSegment(base, vnorm))
            # rotate
            edge.rotate(base, direction, obj.ConnectionOffsetAngle.Value)
            # get rotated point
            voffset = points[0] + \
                edge.Vertexes[1].Point*obj.ConnectionOffsetDist.Value
            points.pop(0)
            points.insert(0, voffset)
        return points


class ViewProviderCompoundPath:
    """A base View Provider for the CompoundPath object.
    """
    def __init__(self, vobj):
        vobj.PointColor = (0, 200, 0)
        vobj.PointSize = 4
        vobj.LineColor = (0, 85, 0)
        vobj.LineWidth = 2
        vobj.Proxy = self

    def getIcon(self):
        return CLASS_COMPOUNDPATH_ICON

    def attach(self, vobj):
        self.Object = vobj.Object

    def claimChildren(self):
        children = self.Object.Links
        return children

    def dumps(self):
        return {"name": self.Object.Name}

    def loads(self, state):
        self.Object = FreeCAD.ActiveDocument.getObject(state["name"])
        return None

#    def updateData(self, obj, prop):
#        pass

#    def onChanged(self, vobj, prop):
#        pass


def make_compoundpath(plist=None):
    """
    It creates a new object of CompoundPath

    Parameters
    ----------
    plist : list
        List of type [obj, ...]
        If None, processGuiSelection function is used internally to create
        plist
    Returns
    -------
    CompoundPath object
    """
    if not plist:
        plist = wireutils.processGuiSelection(
            single=False, subshape_class=Part.Vertex, obj_proxy_class=None)
    if not plist:
        return None
    path = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                            "CompoundPath")
    CompoundPath(path)
    ViewProviderCompoundPath(path.ViewObject)
    path.Links = plist
    path.PathType = 'Complex'
    path.MinimumFilletRadius = 10.0
    path.ConnectionType = 'Arc'
    path.Ratio = 1.6
    path.Degree = 3
    return path
