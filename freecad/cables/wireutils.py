"""utilities for Wire WireFlex
"""

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
            pe = getCurveParameter(edge.Curve, pt+obj.Placement.Base)
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
            pt = pt + obj.Placement.Base
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
                pt = pt + obj.Placement.Base
                pe = getCurveParameter(e.Curve, pt)
                if pe is not None:
                    pts_on_edge.append(i)
            v = vector - obj.Placement.Base
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
    pts.insert(idx, newVector-obj.Placement.Base)
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
