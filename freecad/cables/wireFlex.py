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
from freecad.cables import wireutils

_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "resources/icons")
CLASS_WIREFLEX_ICON = os.path.join(iconPath, "classWireFlex.svg")


class WireFlex(Draft.Wire):
    """The WireFlex class
    """
    def __init__(self, obj):
        """Add the properties"""
        obj.addProperty("App::PropertyLinkSub", "Vrtx_start", "WireFlex",
                        "First Vertex")
        obj.addProperty("App::PropertyLinkSub", "Vrtx_end", "WireFlex",
                        "Last Vertex")
        obj.addProperty("App::PropertyLinkSubList", "Vrtxs_mid", "WireFlex",
                        "List of middle vertices")
        obj.addProperty("App::PropertyIntegerList",
                        "Vrtxs_mid_idx", "WireFlex",
                        "Point indexes for list of middle vertices")
        pl = obj.PropertiesList
        proplist = ["Start", "End", "MakeFace", "ChamferSize", "Closed",
                    "Subdivisions", "FilletRadius"]
        for prop in proplist:
            if (prop in pl) and \
               (str(obj.getPropertyStatus(prop)[0]) != "Hidden"):
                obj.setPropertyStatus(prop, "Hidden")
        obj.Proxy = self
        self.Type = 'Wire'
        obj.Label = 'WireFlex'

    def get_vlist(self, obj):
        """It gets vector list of all attached wire points
        """
        vstart = wireutils.getVector(obj, "Vrtx_start", "Vertex")
        vend = wireutils.getVector(obj, "Vrtx_end", "Vertex")
        vmid_lst = wireutils.getVector(obj, "Vrtxs_mid", "Vertex")
        vlist = [None] * len(obj.Points)
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
        obj.Points = pts

    def execute(self, obj):
        # FreeCAD.Console.PrintMessage(f"Execute started({obj.Label})" + "\n")
        super().execute(obj)
        self.recalculate_points(obj)
        super().execute(obj)

    def onChanged(self, obj, prop):
        # FreeCAD.Console.PrintMessage(f"Changed property: {prop} \n")
        super().onChanged(obj, prop)


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
