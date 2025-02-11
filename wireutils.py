"""utilities for Wire WireFlex
"""

import FreeCAD
import wireFlex
import Part


translate = FreeCAD.Qt.translate


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
        if isinstance(obj.Proxy, wireFlex.WireFlex):
            if obj.ChamferSize > 0 or obj.FilletRadius > 0 \
                    or obj.Subdivisions > 0:
                FreeCAD.Console.PrintError(
                    f"Not possible to modify {str(obj.Label)} due to " +
                    "non zero Chamfer or Fillet or Subdivision\n")
                FreeCAD.Console.PrintError(
                    translate("Cables", "Not possible to modify") +
                    f" {str(obj.Label)} " +
                    translate("Cables", "due to non zero Chamfer or Fillet " +
                              "or Subdivision") + "\n")
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


def addPointToWire(plist=None):
    """
    Adds a new point to WireFlex

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
    """
    if not plist:
        plist = processGuiSelection(single=True, subshape_class=Part.Edge,
                                    obj_proxy_class=wireFlex.WireFlex)
    if not plist:
        return None
    try:
        obj = plist[0][0]
        name = plist[0][1]
        nr = int(name.split('Edge')[1])
    except (ValueError, IndexError, AttributeError, TypeError):
        FreeCAD.Console.PrintError(translate(
            "Cables", "Selection is not an edge") + "\n")
        return None    # not an edge
    vlist = obj.Proxy.get_vlist(obj)
    pts = obj.Points
    pts.insert(nr, (pts[nr]+pts[nr-1])/2)
    vlist.insert(nr, None)
    obj.Points = pts
    obj.Proxy.update_vrtxs_mid(obj, vlist)
    return None


def delPointFromWire(plist=None):
    """
    Deletes a point from WireFlex

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
    """
    if not plist:
        plist = processGuiSelection(single=True, subshape_class=Part.Vertex,
                                    obj_proxy_class=wireFlex.WireFlex)
    if not plist:
        return None
    try:
        obj = plist[0][0]
        name = plist[0][1]
        nr = int(name.split('Vertex')[1])
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


def assignPointAttachment(plist=None):
    """
    Attaches one selected point of WireFlex to external vertex or object's Base

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
        If subelement_name in plist is '' then obj.Placement.Base is taken
    """
    if not plist:
        plist = processGuiSelection(single=False, subshape_class=Part.Vertex,
                                    obj_proxy_class=wireFlex.WireFlex)
    if not plist:
        return None
    if len(plist) < 2:
        FreeCAD.Console.PrintError(translate(
            "Cables", "Wrong selection. Please select two vertexes. First " +
            "vertex has to belong to WireFlex, second to an external object") +
            "\n")
        
        return None
    try:
        obj = plist[0][0]
        name = plist[0][1]
        nr = int(name.split('Vertex')[1])
        sel_ext = plist[1]
    except (ValueError, IndexError, AttributeError, TypeError):
        FreeCAD.Console.PrintError(translate(
            "Cables", "First selection is not a Vertex") + "\n")
        return None    # not a Vertex
    if 1 < nr < len(obj.Shape.Vertexes):
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
        elif nr == len(obj.Shape.Vertexes):
            obj.Vrtx_end = p
    return None


def removePointAttachment(plist=None):
    """
    It removes external attachment from selected point of WireFlex

    Parameters
    ----------
    plist : list
        List of type [(obj, subelement_name), ...]
        If None, processGuiSelection function is used internally to create
        plist
    """
    if not plist:
        plist = processGuiSelection(single=True, subshape_class=Part.Vertex,
                                    obj_proxy_class=wireFlex.WireFlex)
    if not plist:
        return None
    try:
        obj = plist[0][0]
        name = plist[0][1]
        nr = int(name.split('Vertex')[1])
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
    elif nr == len(obj.Shape.Vertexes):
        obj.Vrtx_end = None
    return None
