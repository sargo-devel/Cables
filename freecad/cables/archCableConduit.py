"""ArchCableConduit based on ArchPipe
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
import math
import FreeCAD
import ArchComponent
import ArchPipe
import Part
from freecad.cables import iconPath
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP


CLASS_CABLE_CONDUIT_ICON = os.path.join(iconPath, "classArchCableConduit.svg")
tol = 1e-6     # tolerance for isEqual() comparision


class ArchCableConduit(ArchPipe._ArchPipe):
    """The ArchCableConduit class
    """
    def __init__(self, obj):
        # super().__init__(obj)
        ArchPipe._ArchPipe.__init__(self, obj)
        from ArchIFC import IfcTypes
        if "Cable Segment" in IfcTypes:
            obj.IfcType = "Cable Segment"
        else:
            # IFC2x3 does not know a Cable Segment
            obj.IfcType = "Building Element Proxy"

    def setProperties(self, obj):
        ArchPipe._ArchPipe.setProperties(self, obj)
        pl = obj.PropertiesList
        if "SubConduits" not in pl:
            obj.addProperty("App::PropertyLinkList", "SubConduits", "Conduit",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "List of coduits belonging " +
                                "to the bundle"))
        if "AutoLabelBase" not in pl:
            obj.addProperty("App::PropertyBool", "AutoLabelBase", "Conduit",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Automatically " +
                                "change label of base object"))
        if "ShowSubConduits" not in pl:
            obj.addProperty("App::PropertyBool", "ShowSubConduits", "Conduit",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Shows/hides all sub " +
                                "conduits"))
        if "ShowBaseSingleWires" not in pl:
            obj.addProperty("App::PropertyBool", "ShowBaseSingleWires",
                            "Conduit",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Shows/hides all single " +
                                "base wires/subwires"))
        if "ShowBaseCompoundPaths" not in pl:
            obj.addProperty("App::PropertyBool", "ShowBaseCompoundPaths",
                            "Conduit",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Shows/hides all compound " +
                                "base paths"))
        if "Gauge" not in pl:
            obj.addProperty("App::PropertyFloat", "Gauge", "ConduitDimensions",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Outer gauge [mm^2] of " +
                                "the conduit"))
        if "InsulationThickness" not in pl:
            obj.addProperty("App::PropertyLength", "InsulationThickness",
                            "ConduitDimensions",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Thickness of insulation " +
                                "if profile not used"))

        self.Type = "Pipe"

    def onChanged(self, obj, prop):
        ArchPipe._ArchPipe.onChanged(self, obj, prop)
        if prop == "Gauge":
            obj.Diameter = math.sqrt(obj.Gauge/math.pi)*2
        if prop == "InsulationThickness":
            obj.WallThickness = obj.InsulationThickness
        if prop == "AutoLabelBase" and obj.AutoLabelBase:
            self.setBaseLabel(obj)
        if prop == "ShowSubConduits" and hasattr(obj, "SubConduits"):
            if obj.SubConduits:
                for s in obj.SubConduits:
                    s.ViewObject.show() if obj.ShowSubConduits \
                        else s.ViewObject.hide()
                    if hasattr(s, prop):
                        s.ShowSubConduits = True if obj.ShowSubConduits \
                            else False
        if prop == "ShowBaseSingleWires" and hasattr(obj, "Base"):
            if obj.Base and obj.Base.TypeId == 'Part::Compound':
                for p in obj.Base.Links:
                    p.ViewObject.show() if getattr(obj, prop) \
                        else p.ViewObject.hide()
            else:
                obj.Base.ViewObject.show() if getattr(obj, prop) \
                        else obj.Base.ViewObject.hide()
            self.switchSubConduits(obj, prop)
        if prop == "ShowBaseCompoundPaths" and hasattr(obj, "Base"):
            if obj.Base and obj.Base.TypeId == 'Part::Compound':
                obj.Base.ViewObject.show() if getattr(obj, prop) \
                        else obj.Base.ViewObject.hide()
            self.switchSubConduits(obj, prop)

        if prop == "Label" and obj.AutoLabelBase:
            self.setBaseLabel(obj)

    def switchSubConduits(self, obj, prop):
        '''It switches properties of sub conduits
        Function used for switching ShowBaseSingleWires, ShowBaseCompoundPaths
        '''
        if hasattr(obj, "SubConduits"):
            if obj.SubConduits:
                for s in obj.SubConduits:
                    if hasattr(s, prop):
                        setattr(s, prop, True) if getattr(obj, prop) \
                            else setattr(s, prop, False)
                    elif prop == "ShowBaseSingleWires":
                        if s.Base and s.Base.TypeId == 'Part::Compound':
                            for p in s.Base.Links:
                                p.ViewObject.show() if getattr(obj, prop) \
                                    else p.ViewObject.hide()
                        else:
                            s.Base.ViewObject.show() if getattr(obj, prop) \
                                else s.Base.ViewObject.hide()
                    elif prop == "ShowBaseCompoundPaths":
                        if s.Base and s.Base.TypeId == 'Part::Compound':
                            s.Base.ViewObject.show() if getattr(obj, prop) \
                                else s.Base.ViewObject.hide()

    def execute(self, obj):
        ArchPipe._ArchPipe.execute(self, obj)

    def getWire(self, obj):
        if hasattr(obj.Base, 'Shape') and len(obj.Base.Shape.Wires) > 1:
            if self.isBasePathContinuous(obj):
                edges = []
                last_vertex = None
                for wire in obj.Base.Shape.Wires:
                    if last_vertex:
                        if last_vertex.Point.isEqual(
                                wire.Vertexes[0].Point, tol):
                            edges.extend(wire.Edges)
                            last_vertex = wire.Vertexes[-1]
                        else:
                            rev_edges = wire.Edges
                            rev_edges.reverse()
                            edges.extend(rev_edges)
                            last_vertex = wire.Vertexes[0]
                    else:
                        edges.extend(wire.Edges)
                        last_vertex = wire.Vertexes[-1]
                w = Part.Wire(edges)
            else:
                return None
        else:
            w = ArchPipe._ArchPipe.getWire(self, obj)
        return w

    def isBasePathContinuous(self, obj):
        '''Checks if base path (compound of many wires) is properly constructed
        It checks if:
        1. the path is continous
        2. the first vertex of first wire is at the begining of path
        3. the last vertex of last wire is at the end of path
        '''
        last_wire = None
        for wire in obj.Base.Shape.Wires:
            if last_wire:
                if last_wire.Vertexes[-1].Point.isEqual(
                        wire.Vertexes[0].Point, tol) or \
                        last_wire.Vertexes[-1].Point.isEqual(
                        wire.Vertexes[-1].Point, tol) or \
                        last_wire.Vertexes[0].Point.isEqual(
                        wire.Vertexes[0].Point, tol) or \
                        last_wire.Vertexes[0].Point.isEqual(
                        wire.Vertexes[-1].Point, tol):
                    last_wire = wire
                else:
                    FreeCAD.Console.PrintError(translate(
                        "Cables", "Base compound object not continous")
                        + "\n")
                    return False
            else:
                last_wire = wire
        return True

    def setBaseLabel(self, obj):
        prefix = obj.Label
        base = '_Base'
        if obj.Base:
            obj.Base.Label = prefix + base


class ViewProviderCableConduit(ArchComponent.ViewProviderComponent):
    """A View Provider for the ArchCableConduit object
    """

    def __init__(self, vobj):
        ArchComponent.ViewProviderComponent.__init__(self, vobj)

    def getIcon(self):
        return CLASS_CABLE_CONDUIT_ICON

    def claimChildren(self):
        c = ArchComponent.ViewProviderComponent.claimChildren(self)
        if hasattr(self.Object, "SubConduits"):
            c.extend(self.Object.SubConduits)
        return c


def getObjectsForCableConduit(selectlist):
    """Gets selection list, preferably made by Gui.Selection.getSelection().
    It checks preconditions, groups objects, creates base compound if needed,
    and returns selected objects if preconditions are met

    Parameters
    ----------
    selectlist : selected objects list
        List of objects

    Returns
    -------
    tuple (baseobj, subobj_list, profileobj)
    """
    baseobj = None
    subobj_list = []
    profileobj = None

    baselist = []
    for sel in selectlist:
        if sel.TypeId == 'Part::Part2DObjectPython':
            if sel.Proxy.Type == 'Wire':
                baselist.append(sel)
        elif sel.TypeId == 'Part::FeaturePython':
            if sel.Proxy.Type == 'Pipe':
                subobj_list.append(sel)
        elif sel.TypeId == 'Part::Compound':
            for sub_el in sel.Links:
                if sub_el.TypeId == 'Part::Part2DObjectPython':
                    if sub_el.Proxy.Type == 'Wire':
                        baselist.append(sub_el)
    if len(baselist) > 1:
        baseobj = FreeCAD.ActiveDocument.addObject("Part::Compound",
                                                   "Compound")
        baseobj.Links = baselist
    elif len(baselist) == 1:
        baseobj = baselist[0]

    if hasattr(selectlist[-1], "Proxy"):
        if selectlist[-1].Proxy.Type == 'Profile':
            profileobj = selectlist[-1]

    return baseobj, subobj_list, profileobj


def makeCableConduit(selectlist=None, gauge=0, length=0, placement=None,
                     name=None):
    "Creates a cable bundle object from the given base object"
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No active document. Aborting") + "\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                           "CableConduit")
    obj.Label = name if name else translate("Cables", "Cable Conduit")
    ArchCableConduit(obj)

    if selectlist:
        baseobj, subobj_list, profileobj = \
            getObjectsForCableConduit(selectlist)
    else:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No base objects for Cable Conduit. Aborting") + "\n")
        return

    if FreeCAD.GuiUp:
        ViewProviderCableConduit(obj.ViewObject)
        if baseobj:
            baseobj.ViewObject.hide()
        if profileobj:
            profileobj.ViewObject.hide()
    if baseobj:
        obj.Base = baseobj
        obj.AutoLabelBase = True
    else:
        if length:
            obj.Length = length
        else:
            obj.Length = 1000
    if subobj_list:
        obj.SubConduits = subobj_list
    obj.ShowSubConduits = True
    if profileobj:
        obj.Profile = profileobj
    else:
        if gauge:
            obj.Gauge = gauge
        else:
            obj.Gauge = 20.0
    if placement:
        obj.Placement = placement
    return obj
