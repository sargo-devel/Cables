"""utilities for Wire WireFlex
"""

import math
import FreeCAD
import Part
import DraftGeomUtils
from freecad.cables import wireFlex
from freecad.cables import translate

tol = 1e-4      # tolerance for isEqual() comparision


def getVector(obj, prop='Vrtx_start', shape_type='Vertex'):
    """ Gets single vector or vector list from a given property.

    Parameters
    ----------
    obj :
        The scripted object (e.g. `Part::FeaturePython`)
        or a tuple with a `App::PropertyLinkSub` structure like:
            (obj, ('Vertex1',))
         or (obj, 'Vertex1')

    prop : str
        Name of the property to process
        (type `App::PropertyLinkSub` or `App::PropertyLinkSubList`)
        If obj is a tuple, prop is not used

    shape_type : str
        Element type in prop list. So far shape_type can be `Vertex`

    Returns
    -------
    Single Vector or Vector list (depending on prop type)
    """
    if shape_type == 'Vertex':
        if hasattr(obj, prop):
            if obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSub":
                plink = obj.getPropertyByName(prop)
                if plink:
                    try:
                        return plink[0].getSubObject(plink[1][0]).Point
                    except (AttributeError, IndexError):
                        return plink[0].Placement.Base
                else:
                    return None
            elif obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSubList":
                plink = getFlatLinkSubList(obj, prop)
                vlist = []
                if plink:
                    for p in plink:
                        try:
                            vlist.append(p[0].getSubObject(p[1][0]).Point)
                        except (AttributeError, IndexError):
                            vlist.append(p[0].Placement.Base)
                    return vlist
                else:
                    return None
            else:
                FreeCAD.Console.PrintError(translate(
                    "Cables", "Cables.wireutils.getVector: wrong property " +
                    "type.") + "\n")
                return None
        elif type(obj) is tuple:
            try:
                if isinstance(obj[1], str):
                    return obj[0].getSubObject(obj[1]).Point
                if isinstance(obj[1], tuple) or isinstance(obj[1], list):
                    return obj[0].getSubObject(obj[1][0]).Point
            except (AttributeError, IndexError):
                return obj[0].Placement.Base
        else:
            FreeCAD.Console.PrintError(translate(
                "Cables", "Cables.wireutils.getVector: wrong object.") + "\n")
            return None
    else:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Cables.wireutils.getVector: wrong shape type.") + "\n")
        return None


def getFlatLinkSubList(obj, prop):
    """ Gets flat PropertyLinkSubList from App::PropertyLinkSubList
    Flat means that in one element there is only one subelement, if any

    Parameters
    ----------
    obj :
        The scripted object (e.g. `Part::FeaturePython`)

    prop : str
        Name of the property to process

    Returns
    -------
    App::PropertyLinkSubList (flat)
    """
    if obj.getTypeIdOfProperty(prop) == "App::PropertyLinkSubList":
        sub_list = obj.getPropertyByName(prop)
        flat_sub_list = []
        for element in sub_list:
            for sub_element in element[1]:
                flat_sub_list.append((element[0], (sub_element,)))
        return flat_sub_list
    else:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Cables.wireutils.getFlatLinkSubList: wrong property " +
            "type.") + f"{obj.getTypeIdOfProperty(prop)}\n")
    return None


def processGuiSelection(single=False, subshape_class=Part.Vertex,
                        obj_proxy_class=None, preserve_sel_ord=True):
    """Gets selection, checks preconditions and returns selection list if
    preconditions are met

    Parameters
    ----------
    single : bool
        Type of selection. If True, only one element can be selected

    subshape_class : class
        Class of shape valid in selection.
        Can be: Part.Vertex, Part.Edge (default: Part.Vertex)
        If subshape_class does not match, the complete object is returned

    obj_proxy_class : class
        Valid proxy class of object which owns first selected shape.
        None means any.
        Example: wireFlex.WireFlex (default: None, means not checked)
        If obj_proxy_class does not match, None is returned

    Returns
    -------
    List of type [(obj, subelement_name), ...]
    """
    if single or not preserve_sel_ord:
        slist = FreeCAD.Gui.Selection.getSelectionEx('', 1, single)
    else:
        slist = FreeCAD.Gui.Selection.getCompleteSelection()
    retlist = None
    if not slist and single:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Wrong selection. Please select only one") +
            f" {subshape_class}\n")
        return None
    if not slist:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Nothing selected!") + "\n")
        return None
    if obj_proxy_class:
        obj = slist[0].Object
        if not isinstance(obj.Proxy, obj_proxy_class):
            FreeCAD.Console.PrintError(translate(
                "Cables", "Wrong selection. Please select") +
                f" object of {obj_proxy_class} type\n")
            return None
    retlist = []
    # FreeCAD.Console.PrintMessage(f"slist= {slist}\n")
    for sel in slist:
        obj = sel.Object
        if sel.HasSubObjects:
            for idx in range(len(sel.SubObjects)):
                if isinstance(sel.SubObjects[idx], subshape_class):
                    subelement_name = sel.SubElementNames[idx]
                else:
                    subelement_name = ''
                retlist.append((obj, subelement_name))
        else:
            subelement_name = ''
            retlist.append((obj, subelement_name))
    return retlist


def reprintSelection(prefix, slist):
    """Converts selection list to string.
    Selection list produced by processGuiSelection is converted to its string
    representation. Equivalent of repr()

    Parameters
    ----------
    prefix : str
        Prefix representing current document,
        examples: "doc", "FreeCAD.ActiveDocument"
    slist : list
        Supported list types:
            [(obj, subelement_name), ...]
            [obj, ...]

    Returns
    -------
    str
    """
    if not slist:
        return None
    s = '['
    for i in slist:
        if type(i) == tuple:
            s += f"({prefix}.{i[0].Name}, {repr(i[1])}), "
        else:
            s += f"{prefix}.{i.Name}, "
    return s[:-2] + ']'


def getCurveParameter(curve, point):
    """It returns curve parameter for point
    For bsplines: the nearest point parameter is returned or None
    For other curves: point has to lie on curve, otherwise it returns None
    """
    par = curve.parameter(point)
    v = curve.value(par)
    tol_b = 1e-1    # increased tolerance for BSplines
    if curve.TypeId == 'Part::GeomBSplineCurve':
        if v.isEqual(point, tol_b):
            return par
        elif par in curve.getKnots() and par != 0:
            # this is true for obj.Points in BSpline_K (point -> Knot)
            return par
        elif par in [curve.parameter(i) for i in curve.getPoles()] and \
                par != 0:
            # this is true for obj.Points in BSpline_P (point -> Pole)
            return par
    elif v.isEqual(point, tol):
        return par
    else:
        return None


def getIndexForNewPoint(obj, edgename, vector):
    """It calculates a new index in obj.Points for a given vector.
    The fuction is designed to work with obj wires with Fillets or bsplines.
    The vector should belong to object edge.
    The obj should have Points property.
    Function does not modify any obj property, it just returns index
    which should be assigned if vector was added to obj.Points.
    Index counts from 0.

    Parameters
    ----------
    obj : object
        Any object having Points property
    edgename : str
        edge name on which the vertex lies
    vector : Vector
        The vector to check

    Returns
    -------
    int
    New vector index for obj.Points.
    it can be used e.g. as: points.insert(idx, vector)
    Returns None if no index found
    """
    try:
        points = obj.Points
        nr = int(edgename.split('Edge')[1])
        edge = obj.Shape.Edges[nr-1]
    except (ValueError, IndexError, AttributeError, TypeError):
        FreeCAD.Console.PrintError(translate(
            "Cables", "Selection is not an edge or obj has no Points "
            "property") + "\n")
        return None
    if edge.Curve.TypeId == 'Part::GeomLine' or \
            edge.Curve.TypeId == 'Part::GeomBSplineCurve':
        p = getCurveParameter(edge.Curve, vector)
        if p is None:
            FreeCAD.Console.PrintError(translate(
                "Cables", "The new point is not lying on edge") + "\n")
            return None
        min_diff = None
        min_idx = 0
        for i, pt in enumerate(points):
            pe = getCurveParameter(edge.Curve, obj.Placement.multVec(pt))
            if pe is None:
                continue
            if (p-pe > 0) and not min_diff:
                min_diff = p - pe
                min_idx = i
            elif (p-pe > 0) and (p-pe < min_diff):
                min_diff = p - pe
                min_idx = i
        return min_idx+1
    else:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Selected edge is not supported:") +
            f" {edge.Curve.TypeId}\n")
    return None


def getIndexForPointToEdit(obj, vector):
    """It calculates an index of corresponding point in obj.Points
    for a given vector.
    The fuction is designed to work with obj wires with Fillets.
    The vector should belong to one of object edges.
    The obj should have Points property.
    Function does not modify any obj property, it just returns index
    which should be used to delete o modify one of obj.Points.
    Index counts from 0.

    Parameters
    ----------
    obj : object
        Any object having Points property
    vector : Vector
        The vector to check

    Returns
    -------
    int
    index of point to delete or modify in obj.Points.
    it can be used e.g. as: points.pop(idx)
    Returns None if no index found
    """
    try:
        points = obj.Points
        for i, pt in enumerate(points):
            pt = obj.Placement.multVec(pt)
            if pt.isEqual(vector, tol):
                return i
        edges = []
        for e in obj.Shape.Edges:
            for v in e.Vertexes:
                if v.Point.isEqual(vector, tol):
                    if e.Curve.TypeId == 'Part::GeomLine':
                        edges.append(e)
    except (ValueError, IndexError, AttributeError, TypeError):
        FreeCAD.Console.PrintError(translate(
            "Cables", "Wrong selection or obj has no Points property") + "\n")
        return None
    if not edges:
        FreeCAD.Console.PrintError(translate(
            "Cables", "The given vector does not belong to obj") + "\n")
    for e in edges:
        p = getCurveParameter(e.Curve, vector)
        if p is not None:       # vector lies on edge
            pts_on_edge = []
            for i, pt in enumerate(points):
                pt = obj.Placement.multVec(pt)
                pe = getCurveParameter(e.Curve, pt)
                if pe is not None:
                    pts_on_edge.append(i)
            v = obj.Placement.inverse().multVec(vector)
            if pts_on_edge:
                p1_idx = DraftGeomUtils.findClosest(
                    v, [points[n] for n in pts_on_edge])
                return pts_on_edge[p1_idx]
    FreeCAD.Console.PrintError(translate(
         "Cables", "Proper point not found" + "\n"))
    return None


def addPointToWire(plist=None, point=None):
    """
    Adds a new point to WireFlex

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
    point : Vector
        Optional point to add instead of half the edge
    """
    if not plist:
        plist = processGuiSelection(single=True, subshape_class=Part.Edge,
                                    obj_proxy_class=wireFlex.WireFlex)
    if not plist:
        return None
    try:
        obj = plist[0][0]
        edge_name = plist[0][1]
        nr = int(edge_name.split('Edge')[1])
        edge = obj.Shape.Edges[nr-1]
        if edge.Curve.TypeId == 'Part::GeomCircle':
            FreeCAD.Console.PrintError(translate(
                "Cables", "Wrong edge type selected") + "\n")
            return None    # wrong edge
        v2 = edge.Vertexes[1].Point
        midparam = edge.Curve.parameter(v2)/2
        newVector = point or edge.Curve.value(midparam)
    except (ValueError, IndexError, AttributeError, TypeError):
        FreeCAD.Console.PrintError(translate(
            "Cables", "Selection is not an edge") + "\n")
        return None    # not an edge
    idx = getIndexForNewPoint(obj, edge_name, newVector)
    if not idx:
        return None
    vlist = obj.Proxy.get_vlist(obj)
    pts = obj.Points
    pts.insert(idx, obj.Placement.inverse().multVec(newVector))
    vlist.insert(idx, None)
    obj.Points = pts
    obj.Proxy.update_vrtxs_mid(obj, vlist)
    return None


def delPointFromWire(plist=None, point_idx=None):
    """
    Deletes a point from WireFlex

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
    point_idx: int
        Optional point idx to delete (counted from 0)
    """
    if not plist:
        plist = processGuiSelection(single=True, subshape_class=Part.Vertex,
                                    obj_proxy_class=wireFlex.WireFlex)
    if not plist:
        return None
    try:
        obj = plist[0][0]
        if point_idx is not None:
            nr = point_idx + 1
        else:
            name = plist[0][1]
            nr = int(name.split('Vertex')[1])
            idx = getIndexForPointToEdit(obj, obj.Shape.Vertexes[nr-1].Point)
            nr = idx+1 if idx is not None else 0
        if not 1 < nr < len(obj.Points):
            FreeCAD.Console.PrintError(translate(
                "Cables", "Selection is not a mid Vertex") + "\n")
            return None
    except (ValueError, IndexError, AttributeError, TypeError):
        FreeCAD.Console.PrintError(translate(
            "Cables", "Selection is not a Vertex") + "\n")
        return None    # not a Vertex
    vlist = obj.Proxy.get_vlist(obj)
    pts = obj.Points
    pts.pop(nr-1)
    vlist.pop(nr-1)
    obj.Points = pts
    obj.Proxy.update_vrtxs_mid(obj, vlist)
    return None


def assignPointAttachment(plist=None, point_idx=None, obj=None):
    """
    Attaches one selected point of WireFlex to external vertex or object's Base

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
        If subelement_name in plist is '' then obj.Placement.Base is taken
    point_idx: int
        Optional point idx to attach (counted from 0)
    obj: object
        Optional direct object instead of plist, then second object is taken
        internally from GuiSelection
    """
    if not plist:
        if obj and (point_idx is not None):
            plist = processGuiSelection(single=False,
                                        subshape_class=Part.Vertex)
        else:
            plist = processGuiSelection(single=False,
                                        subshape_class=Part.Vertex,
                                        obj_proxy_class=wireFlex.WireFlex)
    if not plist:
        return None
    if (len(plist) < 2) and (point_idx is None) and (obj is None):
        FreeCAD.Console.PrintError(translate(
            "Cables", "Wrong selection. Please select two vertexes. First " +
            "vertex has to belong to WireFlex, second to an external object") +
            "\n")
        return None
    try:
        if point_idx is not None and obj is not None:
            nr = point_idx + 1
            sel_ext = plist[0]
        else:
            obj = plist[0][0]
            name = plist[0][1]
            nr = int(name.split('Vertex')[1])
            idx = getIndexForPointToEdit(obj, obj.Shape.Vertexes[nr-1].Point)
            nr = idx+1 if idx is not None else 0
            sel_ext = plist[1]
    except (ValueError, IndexError, AttributeError, TypeError):
        FreeCAD.Console.PrintError(translate(
            "Cables", "First selection is not a Vertex") + "\n")
        return None    # not a Vertex
    if 1 < nr < len(obj.Points):
        vrtxs_mid = getFlatLinkSubList(obj, 'Vrtxs_mid')
        vrtxs_mid_idx = obj.Vrtxs_mid_idx
        if vrtxs_mid_idx.count(nr):         # replace assignment
            vrtxs_mid.pop(vrtxs_mid_idx.index(nr))
            vrtxs_mid_idx.pop(vrtxs_mid_idx.index(nr))
        if len(vrtxs_mid_idx) == 0:         # first assignment
            idx = 0
        elif vrtxs_mid_idx[-1] < nr:        # assignment at the end
            idx = len(vrtxs_mid_idx)+1
        else:
            for idx, i in enumerate(vrtxs_mid_idx):
                if i > nr:
                    break
        if sel_ext[0]:      # ext Vertex selected
            vrtxs_mid.insert(idx, (sel_ext[0], [sel_ext[1]]))
        else:               # ext object selected
            vrtxs_mid.insert(idx, (sel_ext[0], []))
        vrtxs_mid_idx.insert(idx, nr)
        obj.Vrtxs_mid = vrtxs_mid
        obj.Vrtxs_mid_idx = vrtxs_mid_idx
    else:
        p = (sel_ext[0], [sel_ext[1]]) if sel_ext[1] else (sel_ext[0], [])
        if nr == 1:
            obj.Vrtx_start = p
            obj.AttachmentSupport = [p]
            obj.MapMode = 'Translate'
        elif nr == len(obj.Points):
            obj.Vrtx_end = p
        else:
            FreeCAD.Console.PrintError(translate(
                "Cables", "Point attachment not assigned") + "\n")
    return None


def removePointAttachment(plist=None, point_idx=None, obj=None):
    """
    It removes external attachment from selected point of WireFlex

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
    point_idx: int
        Optional point idx to detach (counted from 0)
    obj: object
        Optional direct object instead of plist, then second object is taken
        internally from GuiSelection
    """
    if point_idx is None and obj is None:
        if not plist:
            plist = processGuiSelection(single=True,
                                        subshape_class=Part.Vertex,
                                        obj_proxy_class=wireFlex.WireFlex)
        if not plist:
            return None
    try:
        if point_idx is not None and obj is not None:
            nr = point_idx + 1
        else:
            obj = plist[0][0]
            name = plist[0][1]
            nr = int(name.split('Vertex')[1])
            idx = getIndexForPointToEdit(obj, obj.Shape.Vertexes[nr-1].Point)
            nr = idx+1 if idx is not None else 0
    except (ValueError, IndexError, AttributeError, TypeError):
        FreeCAD.Console.PrintError(translate(
            "Cables", "Selection is not a Vertex") + "\n")
        return None    # not an vertex
    vrtxs_mid = getFlatLinkSubList(obj, 'Vrtxs_mid')
    vrtxs_mid_idx = obj.Vrtxs_mid_idx
    if nr in vrtxs_mid_idx:
        idx = vrtxs_mid_idx.index(nr)
        vrtxs_mid.pop(idx)
        vrtxs_mid_idx.pop(idx)
        obj.Vrtxs_mid = vrtxs_mid
        obj.Vrtxs_mid_idx = vrtxs_mid_idx
    elif nr == 1:
        obj.Vrtx_start = None
        obj.AttachmentSupport = None
        obj.MapMode = 'Deactivated'
    elif nr == len(obj.Points):
        obj.Vrtx_end = None
    return None


def reverseWire(obj):
    """
    It reverses direction of WireFlex

    Parameters
    ----------
    obj : object
        WireFlex object
    """
    old_map_mode = obj.MapMode
    obj.MapMode = 'Deactivated'
    max = len(obj.Points)
    new_points = obj.Points
    new_points.reverse()
    obj.Points = new_points

    new_Vrtxs_mid = obj.Vrtxs_mid
    new_Vrtxs_mid.reverse()
    obj.Vrtxs_mid = new_Vrtxs_mid

    new_Vrtxs_mid_idx = []
    for idx in obj.Vrtxs_mid_idx:
        new_Vrtxs_mid_idx.append(max-idx+1)
    new_Vrtxs_mid_idx.sort()
    obj.Vrtxs_mid_idx = new_Vrtxs_mid_idx
    start = obj.Vrtx_start
    obj.Vrtx_start = obj.Vrtx_end
    obj.Vrtx_end = start
    # obj.AttachmentSupport = obj.Vrtx_start
    obj.MapMode = old_map_mode


def modifyWireEdge(plist=None, point=None, cmd=None):
    """
    Modifies an edge of WireFlex

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
        If edge selected: second vertex of the edge is moved
        If edge and vertex selected: given vertex of the edge is moved
    point : Vector
        Optional point selecting which vertex of edge should be moved
    cmd : str
        Command to execute
        'vertical' - set edge vertical
        'horizontal' - set edge vertical
    """
    if not plist:
        plist = processGuiSelection(single=False, subshape_class=Part.Edge,
                                    obj_proxy_class=wireFlex.WireFlex)
    plist2 = None
    if len(plist) > 1:
        plist2 = processGuiSelection(single=False, subshape_class=Part.Vertex,
                                     obj_proxy_class=wireFlex.WireFlex)
    try:
        obj = plist[0][0]
        edge_name = plist[0][1]
        idx = int(edge_name.split('Edge')[1])
        edge = obj.Shape.Edges[idx-1]
        if edge.Curve.TypeId == 'Part::GeomCircle':
            FreeCAD.Console.PrintError(translate(
                "Cables", "Wrong edge type selected") + "\n")
            return None    # wrong edge
        v2 = edge.Vertexes[1].Point
        midparam = edge.Curve.parameter(v2)/2
        newVector = point or edge.Curve.value(midparam)
        nr = getIndexForNewPoint(obj, edge_name, newVector)
    except (ValueError, IndexError, AttributeError, TypeError):
        FreeCAD.Console.PrintError(translate(
            "Cables", "First selection is not an edge") + "\n")
        return None    # not an edge
    if plist2 or point:
        try:
            if plist2:
                obj2 = plist2[1][0]
                name2 = plist2[1][1]
                idx = int(name2.split('Vertex')[1])
                vnr = getIndexForPointToEdit(obj, obj.Shape.Vertexes[idx-1])
            else:
                vnr = getIndexForNewPoint(obj, edge_name, point)
                if edge.Curve.parameter(point) > midparam:
                    vnr += 1
                obj2 = obj
            if vnr is None:
                raise IndexError
        except (ValueError, IndexError, AttributeError, TypeError):
            FreeCAD.Console.PrintError(translate(
                "Cables", "Second selection is not a proper vertex") + "\n")
            return None    # not a vertex
        if not ((obj2 == obj) or (0 <= vnr-nr <= 1)):
            FreeCAD.Console.PrintError(translate(
                "Cables", "Selected vertex does not belong to selected edge") +
                "\n")
            return None    # wrong vertex
    else:
        vnr = nr + 1    # second vertex of selected edge
    vlist = obj.Proxy.get_vlist(obj)
    if vlist[vnr-1]:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Vertex") + f" {vnr} " + translate(
            "Cables", "is attached and can't be moved") + "\n")
        return None
    pts = obj.Points
    if cmd == 'vertical':
        z = pts[nr-1].z+10 if pts[nr].z == pts[nr-1].z else pts[vnr-1].z
        vect = FreeCAD.Vector(pts[2*nr-vnr].x, pts[2*nr-vnr].y, z)
        pts[vnr-1] = vect
        obj.Points = pts
    if cmd == 'horizontal':
        if (pts[nr-1].x == pts[nr].x) and (pts[nr-1].y == pts[nr].y):
            vect = FreeCAD.Vector(pts[nr].x+10, pts[nr].y, pts[2*nr-vnr].z)
        else:
            vect = FreeCAD.Vector(pts[vnr-1].x, pts[vnr-1].y, pts[2*nr-vnr].z)
        pts[vnr-1] = vect
        obj.Points = pts
    return None


def getAttachedPointsCoordList(obj):
    """
    Returns coordinates list of wire attached points

    Parameters
    ----------
    obj : obj
        WireFlex object

    Returns
    -------
    tuple
    Tuple of coordinate tuples: ((x1,y1,z1), (x2,y2,z2), ...)
    """
    coords = []
    for v in obj.Proxy.get_vlist(obj):
        if v:
            vect = obj.Placement.inverse().multVec(v)
            coords.append((vect.x, vect.y, vect.z))
    return tuple(coords)


def getBoundarySegCoordList(obj):
    """
    Returns coordinates list of boundary segment points
    (for BoundarySegmentStart, BoundarySegmentEnd)

    Parameters
    ----------
    obj : obj
        WireFlex object

    Returns
    -------
    tuple
    Tuple of coordinate tuples: ((x1,y1,z1), (x2,y2,z2))
    """
    coords = []
    for i in [(obj.BoundarySegmentStart.Value, 0, 1),
              (obj.BoundarySegmentEnd.Value, -1, -2)]:
        i1 = i[1]
        i2 = i[2]
        if i[0] > 0 and obj.PathType != 'Wire':
            vrtxs = obj.Shape.Vertexes
            if abs((vrtxs[i1].Point-vrtxs[i2].Point).Length - i[0]) < tol:
                vect = obj.Placement.inverse().multVec(vrtxs[i2].Point)
            else:
                v0 = obj.Points[i1]
                v1 = obj.Points[i2]
                vect = v0 + (v1-v0).normalize()*i[0]
            coords.append((vect.x, vect.y, vect.z))
    return tuple(coords)


def makeConnectionWith2Fillets(edge1, edge2, ctype="Arc", radius=None, deg=3,
                               ratio=1.6):
    """
    It creates a new wire with 2 fillets or one Bezier curve between two edges.
    The edge direction is important. Wire will be created between vertex2
    of edge1 and vertex1 of edge2. Wire ends are tangent to edges and fillet
    radius or Bezier curve is calculatad automatically.
    If radius is given, it is compared to calculated one and longer is taken.

    Parameters
    ----------
    edge1, edge2 : edge objects
    ctype : type of output connection (supported types: 'Arc', 'Bez')
    radius : float
    deg: int
        Bezier curve degree
    ratio: float
        The proportions of the segments in the added base curve.
        Should be between 1 and 2.

    Returns
    -------
    Wire object
        The wire gets 5 edges
    """
    defaultradius = 5.0     # if radius == None the defaultradius is taken

    def _getCrossPointVectors():
        vstart = edge1.Vertexes[1].Point
        vend = edge2.Vertexes[0].Point
        v1norm = edge1.tangentAt(edge1.LastParameter)
        v2norm = edge2.tangentAt(edge2.FirstParameter)
        ang = v1norm.getAngle(v2norm)
        coef = 1 if ang < math.pi/12.0 else 2.0

        v1e_tmp = v1norm * dist * coef
        # temporary edge tangent to edge1:
        e1_tmp = Part.Edge(Part.LineSegment(vstart, vstart+v1e_tmp))

        v2e_tmp = v2norm * dist * coef
        # temporary edge tangent to edge2:
        e2_tmp = Part.Edge(Part.LineSegment(vend, vend-v2e_tmp))

        # shortest distance between tmp edges (in the "cross point"):
        dist_tmp = e1_tmp.distToShape(e2_tmp)
        # new edges e1, e2 to "cross point"
        if dist_tmp[0] < tol and v1norm.isEqual(v2norm, tol):
            # edge1 and edge2 form single line
            v1e = v2e = (vstart+vend)/2
        else:
            v1e = dist_tmp[1][0][0]
            v2e = dist_tmp[1][0][1]
            if vstart.isEqual(v1e, tol) or vend.isEqual(v2e, tol):
                v1e = e1_tmp.CenterOfMass
                v2e = e2_tmp.CenterOfMass
        return vstart, v1e, v2e, vend

    def _getNewFilletWire(edge):
        c_tmp = e_tmp.Curve
        # get 1/4 edge to perpendicular cross point
        # TODO: find better algorithm for crosspoint
        endpar = c_tmp.parameter(vend)
        startpar = c_tmp.parameter(vstart)
        if edge.isSame(edge2):
            x = c_tmp.value((startpar+endpar)/4.0)
        else:
            x = c_tmp.value((startpar+endpar)*3.0/4.0)
        e1 = Part.Edge(Part.LineSegment(vstart, x))
        e2 = Part.Edge(Part.LineSegment(x, vend))
        # get temp wire
        if edge.isSame(edge2):
            wire = Part.Wire([e1, e2, edge2])
        else:
            wire = Part.Wire([edge1, e1, e2])
        r = getMaximumRadius(wire)
        r = radius if radius and radius > r else r
        wire = Part.Wire([e1, e2])
        wire = DraftGeomUtils.filletWire(wire, r)
        wire = _cleanWire(wire)
        return wire

    def _cleanWire(wire):
        edges = wire.Edges
        for i, e in enumerate(edges):
            if e.Closed:
                # drop very short edge with one vertex
                edges.pop(i)
        return Part.Wire(edges)

    dist = edge1.distToShape(edge2)[0]

    # edge1 and edge2 have common vertex:
    if edge1.Vertexes[-1].Point.isEqual(edge2.Vertexes[0].Point, tol):
        if edge1.Curve.TypeId == edge2.Curve.TypeId == 'Part::GeomLine':
            # FreeCAD.Console.PrintMessage("[conn2fil] line+line\n")
            wire = Part.Wire([edge1, edge2])
            r_max = getMaximumRadius(wire)
            r_min = radius if not None else defaultradius
            r = r_min if r_min < r_max else r_max
            wire = DraftGeomUtils.filletWire(wire, r)
            wire = _cleanWire(wire)
            return wire
        elif edge1.Curve.TypeId == 'Part::GeomBSplineCurve' and \
                edge2.Curve.TypeId == 'Part::GeomLine':
            # FreeCAD.Console.PrintMessage("[conn2fil] spline+line\n")
            dist = edge2.Length
            vstart = edge1.Vertexes[1].Point
            vend = edge2.Vertexes[1].Point
            v1norm = edge1.tangentAt(edge1.LastParameter)
            v1e_tmp = v1norm * dist
            # temporary edge tangent to edge1:
            e_tmp = Part.Edge(Part.LineSegment(vstart, vstart+v1e_tmp))
            wire = _getNewFilletWire(edge2)
            wire = Part.Wire([edge1]+wire.Edges)
            return wire
        elif edge1.Curve.TypeId == 'Part::GeomLine' and \
                edge2.Curve.TypeId == 'Part::GeomBSplineCurve':
            # FreeCAD.Console.PrintMessage("[conn2fil] line+spline\n")
            dist = edge1.Length
            vstart = edge1.Vertexes[0].Point
            vend = edge2.Vertexes[0].Point
            v1norm = edge2.tangentAt(edge2.FirstParameter)
            v1e_tmp = v1norm * dist
            # temporary edge tangent to edge2:
            e_tmp = Part.Edge(Part.LineSegment(vend-v1e_tmp, vend))
            wire = _getNewFilletWire(edge1)
            wire = Part.Wire(wire.Edges + [edge2])
            return wire
        else:
            FreeCAD.Console.PrintMessage("[conn2fil] other:\n")
            FreeCAD.Console.PrintMessage(f"{edge1.Curve.TypeId}, " +
                                         f"{edge2.Curve.TypeId}\n")

    # continue without common vertex
    vstart, v1e, v2e, vend = _getCrossPointVectors()
    # FreeCAD.Console.PrintMessage("[conn2fil] No common vertex\n")
    e1 = Part.Edge(Part.LineSegment(vstart, v1e))
    # e2 is reversed
    e2 = Part.Edge(Part.LineSegment(vend, v2e))

    if v1e.isEqual(v2e, tol):
        # no need to make 2 fillets (v1e is equal v2e)
        # FreeCAD.Console.PrintMessage("[conn2fil] v1e is equal v2e\n")
        e2 = Part.Edge(Part.LineSegment(v1e, vend))
        wire = Part.Wire([e1, e2])
        if ctype == 'Arc':
            r_max = getMaximumRadius(wire)
            r_min = radius if not None else defaultradius
            r = r_max if r_max > r_min else r_min
            wire = DraftGeomUtils.filletWire(wire, r)
        else:
            wire = getBezCurve(wire, deg)
        wire = Part.Wire([edge1]+wire.Edges+[edge2])
        wire = _cleanWire(wire)
        return wire
    else:
        ex = Part.Edge(Part.LineSegment(v1e, v2e))

    # get x = a*b/(n*a+b) for edge dividing point (works for 2d space)
    '''
    a - len of shortest arm (e1 or e2)
    b - dist between e1, e2
    x - dividing point of a arm
    n*x - dist e1,e2 at x

    b/a = n*x/(a-x)
    x = a*b/(n*a+b)
    '''
    # TODO: find algorithm to determine n (1<n<2)
    n = ratio
    a = min(e1.Length, e2.Length)
    b = (vstart-vend).Length
    xnorm = (a*b/(n*a+b))/a

    # get dividing points vx_e1 and vx_e2 based on x
    ps = e1.Curve.parameter(vstart)
    pe = e1.Curve.parameter(v1e)
    xe = (pe-ps)*xnorm + ps
    vx_e1 = e1.Curve.value(xe)
    ps = e2.Curve.parameter(vend)
    pe = e2.Curve.parameter(v2e)
    xe = (pe-ps)*xnorm + ps
    vx_e2 = e2.Curve.value(xe)

    # new edges based on dividing points
    e1 = Part.Edge(Part.LineSegment(vstart, vx_e1))
    ex = Part.Edge(Part.LineSegment(vx_e1, vx_e2))
    e2 = Part.Edge(Part.LineSegment(vx_e2, vend))

    # create final wire with fillets
    wire = Part.Wire([e1, ex, e2])
    if ctype == "Arc":
        r_max = getMaximumRadius(wire)
        r_min = radius if not None else defaultradius
        r = r_max if r_max > r_min else r_min
        wire = DraftGeomUtils.filletWire(wire, r)
    else:
        wire = getBezCurve(wire, deg)
    wire = Part.Wire([edge1]+wire.Edges+[edge2])
    wire = _cleanWire(wire)
    return wire


def getBezCurve(wire, deg):
    """
    It returns Bezier Curve created from input wire points.
    For the simplicity it is assumed that input wire has 4 points and 3 edges.

    Parameters
    ----------
    wire : Wire object
    deg : int
        curve degree. Restricted to range: 1 to 3

    Returns
    -------
    curve : Curve objecy (Bezier Curve)
    """
    deg = 1 if deg < 1 else deg
    deg = 3 if deg > 3 else deg
    points = [v.Point for v in wire.Vertexes]
    poles = points[1:]
    segpoles_lst = [poles[x:x+deg] for x in range(0, len(poles), deg)]
    startpoint = points[0]
    edges = []
    for segpoles in segpoles_lst:
        c = Part.BezierCurve()
        c.increase(len(segpoles))
        c.setPoles([startpoint]+segpoles)
        edges.append(Part.Edge(c))
        startpoint = segpoles[-1]
    wire = Part.Wire(edges)
    return wire


def getMinimumRadius(wire):
    """
    It calculates minimum radius which appears in a wire

    Parameters
    ----------
    wire : Wire object

    Returns
    -------
    (float, int)
        The tuple: The minimum radius in a wire, the edge number
        Edge is counted from 1
        The edge number indicates an edge with the minimum radius
        or if the radius is 0, an edge before the minimum radius
    """
    bspline_t = 'Part::GeomBSplineCurve'
    circle_t = 'Part::GeomCircle'
    bezier_t = 'Part::GeomBezierCurve'
    bspline_approx_tol = 0.5
    i_max = len(wire.Edges)-1
    rlist = []
    idxlist = []
    for i, e in enumerate(wire.Edges):
        e_nxt = wire.Edges[i+1] if i < i_max else None
        etype = e.Curve.TypeId
        # check tangency between two edges
        t1 = e.tangentAt(e.parameterAt(e.Vertexes[1]))
        t2 = e_nxt.tangentAt(e_nxt.parameterAt(e_nxt.Vertexes[0])) \
            if e_nxt else None
        if t2 and not t1.isEqual(t2, tol):
            return 0.0, i+1
        # get minimum radius from bspline or bezier curve
        if etype == bspline_t:
            arcslist = e.Curve.toBiArcs(bspline_approx_tol)
            rmin = min([a.Radius for a in arcslist])
            rlist.append(rmin)
            idxlist.append(i+1)
        if etype == bezier_t:
            c = e.Curve.toBSpline()
            arcslist = c.toBiArcs(bspline_approx_tol)
            rmin = min([a.Radius for a in arcslist])
            rlist.append(rmin)
            idxlist.append(i+1)
        # get radius from arc
        if etype == circle_t:
            rlist.append(e.Curve.Radius)
            idxlist.append(i+1)
    if rlist:
        min_radius = min(rlist)
        idx = idxlist[rlist.index(min_radius)]
    else:
        min_radius, idx = 1e10, 0   # straight line, radius=infinity
    return min_radius, idx


def getMaximumRadius(wire):
    """
    It calculates possible maximum radius which can be applied as FilletRadius
    in a wire. Wire has to be a polyline. Wire must not have fillet radius.
    Wire has to have at least 2 edges.
    Warning: After applying calculated radius to wire some edges can have very
    short length and only one vertex.

    Parameters
    ----------
    wire : Wire object (minimum 2 edges, no fillets)

    Returns
    -------
    float: The maximum possible fillet radius in a wire
        Returns 0 if wire contains only 1 edge or fillet detected
        or very long radius calculated
    """
    # get shortest edge
    very_long_r = 1e10      # very long radius to drop

    def _max_radius_for_3edges(e1, e2, e3):
        e1tan = e1.tangentAt(0)
        e2tan = e2.tangentAt(0)
        angle_a = (math.pi-e1tan.getAngle(e2tan))/2.0
        if e3 is None:
            dist_min = min(e1.Length, e2.Length)
            rx = math.tan(angle_a)*dist_min
            r3 = very_long_r
        else:
            e3tan = e3.tangentAt(0)
            angle_b = (math.pi-e2tan.getAngle(e3tan))/2.0
            x = e2.Length*math.tan(angle_b)/(math.tan(angle_a) +
                                             math.tan(angle_b))
            rx = math.tan(angle_a)*x
            r3 = math.tan(angle_b)*e3.Length
        r1 = math.tan(angle_a)*e1.Length
        r_max = min(r1, rx, r3)
        r_max = r_max - r_max*1e-12         # rounding correction
        return r_max

    # detect nr of edges
    if len(wire.Edges) < 2:
        return 0
    # detect type of edges
    for e in wire.Edges:
        if e.Curve.TypeId != 'Part::GeomLine':
            return 0

    max_cnt = len(wire.Edges)-2 if len(wire.Edges) > 2 else 1
    rlist = []
    for i in range(max_cnt):
        e1 = wire.Edges[i]
        e2 = wire.Edges[i+1]
        e3 = wire.Edges[i+2] if len(wire.Edges) > 2 else None
        r_max = _max_radius_for_3edges(e1, e2, e3)
        rlist.append(r_max)
    r = min(rlist)
    return r if r < very_long_r else 0


def isBaseWire(obj):
    """
    It checks if obj is a base wire of a 'Pipe' object.
    'Pipe' object includes: ArchPipe, ArchCable, ArchCableConduit.
    If true it also returns the parent object of a base wire.

    Parameters
    ----------
    obj : object

    Returns
    -------
    list of tuples:
        [(True, parentobj), ...] if obj is a base wire of parentobj,
        otherwise [(False, None)]
    """
    plist = []
    for p in obj.InList:
        if hasattr(p, "TypeId") and p.TypeId == "Part::FeaturePython" and \
                hasattr(p, "Proxy") and hasattr(p.Proxy, "Type") and \
                p.Proxy.Type == "Pipe":
            if hasattr(p, "Base") and p.Base == obj:
                plist.append((True, p))
    if not plist:
        plist = [(False, None)]
    return plist
