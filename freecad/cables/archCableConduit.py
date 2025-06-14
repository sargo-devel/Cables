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
from freecad.cables import compoundPath
from freecad.cables import iconPath
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP


CLASS_CABLE_CONDUIT_ICON = os.path.join(iconPath, "classArchCableConduit.svg")
tol = 1e-6     # tolerance for isEqual() comparison


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
                                "App::Property", "List of conduits " +
                                "belonging to the bundle"))
        if "MergeSubConduits" not in pl:
            obj.addProperty("App::PropertyBool", "MergeSubConduits",
                            "Conduit",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Merge all subconduits " +
                                "into one shape"))
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
            if hasattr(obj, "Profile") and not obj.Profile:
                self.setNewDimensions(obj)
        if prop in ["Diameter", "Width", "Height", "ProfileType"] \
                and hasattr(obj, "Gauge"):
            self.setNewGauge(obj)
        if prop == "InsulationThickness":
            if obj.WallThickness != obj.InsulationThickness:
                obj.WallThickness = obj.InsulationThickness
        if prop == "WallThickness":
            if obj.InsulationThickness != obj.WallThickness:
                obj.InsulationThickness = obj.WallThickness
        if prop == "AutoLabelBase" and obj.AutoLabelBase:
            self.setBaseLabel(obj)
        if prop == "ShowSubConduits":
            if hasattr(obj, "SubConduits") and obj.SubConduits:
                self.setSubConduitsVisibility(obj, prop)
        if prop == "MergeSubConduits" and hasattr(obj, "MergeSubConduits"):
            self.mergeSubConduitShapes(obj)
        if prop == "Label" and obj.AutoLabelBase:
            self.setBaseLabel(obj)
            self.setCompoundLabel(obj)

    def execute(self, obj):
        ArchPipe._ArchPipe.execute(self, obj)
        if hasattr(obj, 'SubConduits') and len(obj.SubConduits) > 0 and \
                obj.SubConduits[0].TypeId == 'Part::Compound':
            ownshape = obj.Shape.copy()
            subshape = obj.SubConduits[0].Shape.copy()
            sh = Part.makeCompound([ownshape, subshape])
            obj.Shape = sh

    def mergeSubConduitShapes(self, obj):
        if hasattr(obj, 'MergeSubConduits') and obj.MergeSubConduits and \
                hasattr(obj, 'SubConduits') and obj.SubConduits:
            # FreeCAD.Console.PrintMessage("Create compound\n")
            if obj.SubConduits[0].TypeId == 'Part::Compound':
                return
            slist = []
            for s in obj.SubConduits:
                slist.append(s)
            cmpobj = FreeCAD.ActiveDocument.addObject('Part::Compound',
                                                      'Compound')
            cmpobj.Links = slist
            obj.SubConduits = cmpobj
            obj.ShowSubConduits = False
            cmpobj.ViewObject.hide()
            self.setCompoundLabel(obj)
        if hasattr(obj, 'MergeSubConduits') and not obj.MergeSubConduits and \
                hasattr(obj, 'SubConduits') and obj.SubConduits:
            # FreeCAD.Console.PrintMessage("Delete compound\n")
            if obj.SubConduits[0].TypeId != 'Part::Compound':
                return
            cmpobj = obj.SubConduits[0]
            obj.SubConduits = cmpobj.Links
            obj.ShowSubConduits = True
            FreeCAD.ActiveDocument.removeObject(cmpobj.Name)

    def getWire(self, obj):
        if hasattr(obj.Base, 'Shape') and len(obj.Base.Shape.Wires) > 1:
            path_type = self.isBasePathContinuous(obj)
            if path_type == 'Edges':
                edges = []
                last_vertex = None
                for edge in obj.Base.Shape.Edges:
                    if last_vertex:
                        if last_vertex.Point.isEqual(
                                edge.Vertexes[0].Point, tol):
                            edges.append(edge)
                            last_vertex = edge.Vertexes[-1]
                        else:
                            last_vertex = edge.Vertexes[0]
                    else:
                        edges.append(edge)
                        last_vertex = edge.Vertexes[-1]
                w = Part.Wire(edges)
            elif path_type == 'Wires':
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
        '''Checks if base path (compound of many wires or edges) is properly
        constructed
        It checks if:
        1. the path is continuous
        2. the first vertex of first edge is at the beginning of path
        3. the last vertex of last edge is at the end of path
        '''
        last_edge = None
        last_wire = None
        path_type = None
        if len(obj.Base.Shape.Wires) < len(obj.Base.Links):
            # Some of links are not 'Wire' Type, so check edges
            for edge in obj.Base.Shape.Edges:
                if last_edge:
                    if last_edge.Vertexes[-1].Point.isEqual(
                            edge.Vertexes[0].Point, tol) or \
                            last_edge.Vertexes[-1].Point.isEqual(
                            edge.Vertexes[-1].Point, tol) or \
                            last_edge.Vertexes[0].Point.isEqual(
                            edge.Vertexes[0].Point, tol) or \
                            last_edge.Vertexes[0].Point.isEqual(
                            edge.Vertexes[-1].Point, tol):
                        last_edge = edge
                    else:
                        FreeCAD.Console.PrintError(translate(
                            "Cables", "Conduit: Base compound object not" +
                            "continuous\n"))
                        Part.show(last_edge)
                        Part.show(edge)
                        return path_type
                else:
                    last_edge = edge
            path_type = 'Edges'
        else:
            # Assumed all links are 'Wire' Type
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
                            "Cables", "Conduit: Base compound object not" +
                            "continuous\n"))
                        Part.show(last_wire)
                        Part.show(wire)
                        return path_type
                else:
                    last_wire = wire
            path_type = 'Wires'
        return path_type

    def setBaseLabel(self, obj):
        prefix = obj.Label
        base = '_Base'
        if obj.Base:
            obj.Base.Label = prefix + base

    def setCompoundLabel(self, obj):
        prefix = obj.Label
        base = '_Comp'
        if hasattr(obj, 'SubConduits') and len(obj.SubConduits) > 0 and \
                obj.SubConduits[0].TypeId == 'Part::Compound':
            obj.SubConduits[0].Label = prefix + base

    def setSubConduitsVisibility(self, obj, prop):
        for s in obj.SubConduits:
            if s.TypeId != 'Part::Compound':
                s.ViewObject.show() if obj.ShowSubConduits \
                    else s.ViewObject.hide()
                if hasattr(s, prop):
                    s.ShowSubConduits = True if obj.ShowSubConduits \
                        else False
            else:
                if hasattr(s, "Links") and s.Links:
                    for link in s.Links:
                        if hasattr(link, prop):
                            link.ShowSubConduits = True \
                                if obj.ShowSubConduits else False

    def setNewDimensions(self, obj):
        # Set new dimensions on gauge changed
        if hasattr(obj, "ProfileType") and obj.ProfileType == "Circle":
            new_diameter = math.sqrt(obj.Gauge/math.pi)*2.0
            if obj.Diameter.Value != new_diameter:
                obj.Diameter.Value = new_diameter
        if hasattr(obj, "ProfileType") and obj.ProfileType == "Square":
            new_width = math.sqrt(obj.Gauge)
            if obj.Width.Value != new_width:
                obj.Width = new_width
        if hasattr(obj, "ProfileType") and obj.ProfileType == "Rectangle":
            new_width = obj.Gauge/obj.Height
            if obj.Width.Value != new_width:
                obj.Width.Value = new_width

    def setNewGauge(self, obj):
        # Set new Gauge on dimensions changed
        if hasattr(obj, "Gauge"):
            new_gauge = None
            if hasattr(obj, "ProfileType") and obj.ProfileType == "Circle":
                new_gauge = math.pi*pow(obj.Diameter.Value/2.0, 2)
            if hasattr(obj, "ProfileType") and obj.ProfileType == "Square":
                if obj.Width.Value > 0:
                    new_gauge = obj.Width.Value * obj.Width.Value
            if hasattr(obj, "ProfileType") and obj.ProfileType == "Rectangle":
                if obj.Width.Value > 0 and obj.Height.Value > 0:
                    new_gauge = obj.Width.Value * obj.Height.Value
            if new_gauge is not None and obj.Gauge != new_gauge:
                obj.Gauge = new_gauge


class ViewProviderCableConduit(ArchComponent.ViewProviderComponent):
    """A View Provider for the ArchCableConduit object
    """

    def __init__(self, vobj):
        ArchComponent.ViewProviderComponent.__init__(self, vobj)

    def getIcon(self):
        return CLASS_CABLE_CONDUIT_ICON

    def updateData(self, obj, prop):
        ArchComponent.ViewProviderComponent.updateData(self, obj, prop)
        if prop == "Shape":
            self.colorize(obj)

    def onChanged(self, vobj, prop):
        ArchComponent.ViewProviderComponent.onChanged(self, vobj, prop)

    def claimChildren(self):
        c = ArchComponent.ViewProviderComponent.claimChildren(self)
        if hasattr(self.Object, "SubConduits"):
            c.extend(self.Object.SubConduits)
        return c

    def canDragObjects(self):
        return True

    def canDropObjects(self):
        return True

    def canDragObject(self, dragged_object):
        return True

    def canDropObject(self, incoming_object):
        if hasattr(incoming_object, 'Proxy'):
            return incoming_object.Proxy.Type == 'Pipe'
        return False

    def dragObject(self, vobj, dragged_object):
        lst = self.Object.SubConduits
        lst.remove(dragged_object)
        self.Object.SubConduits = lst

    def dropObject(self, vobj, incoming_object):
        self.Object.SubConduits = self.Object.SubConduits + [incoming_object]

    def colorize(self, obj):

        def _shapeAppearanceMaterialIsSame(sapp_mat1, sapp_mat2):
            for prop in (
                "AmbientColor",
                "DiffuseColor",
                "EmissiveColor",
                "Shininess",
                "SpecularColor",
                "Transparency",
            ):
                if getattr(sapp_mat1, prop) != getattr(sapp_mat2, prop):
                    return False
            return True

        def _shapeAppearanceIsSame(sapp1, sapp2):
            if len(sapp1) != len(sapp2):
                return False
            for sapp_mat1, sapp_mat2 in zip(sapp1, sapp2):
                if not _shapeAppearanceMaterialIsSame(sapp_mat1, sapp_mat2):
                    return False
            return True

        if not obj.Shape:
            return
        if not obj.Shape.Solids:
            return

        if hasattr(obj, 'SubConduits') and len(obj.SubConduits) > 0 and \
                obj.SubConduits[0].TypeId == 'Part::Compound':
            self_mat = self.setMaterial(obj.Material) if obj.Material else \
                obj.ViewObject.ShapeAppearance[0]
            sub_sapp = self.getMaterialsFromCompound(obj.SubConduits[0])
            if len(obj.Shape.Faces) != len(obj.ViewObject.ShapeAppearance):
                self_sapp_len = len(obj.Shape.Solids[0].Faces)
                self_sapp = tuple(self_mat for i in range(self_sapp_len))
                obj.ViewObject.ShapeAppearance = self_sapp + sub_sapp
            if not _shapeAppearanceIsSame(
                    obj.ViewObject.ShapeAppearance[-len(sub_sapp):], sub_sapp):
                self_sapp_len = len(obj.Shape.Solids[0].Faces)
                self_sapp = tuple(self_mat for i in range(self_sapp_len))
                obj.ViewObject.ShapeAppearance = self_sapp + sub_sapp

    def getMaterialsFromCompound(self, cmpobj):
        materials = []
        for s in cmpobj.Links:
            sapp = s.ViewObject.ShapeAppearance
            if len(sapp) == len(s.Shape.Faces):
                materials.extend(list(sapp))
            else:
                smat = [sapp[0] for i in range(len(s.Shape.Faces))]
                materials.extend(smat)
        return tuple(materials)

    def setMaterial(self, material):
        m = FreeCAD.Material()
        m.set(material.Material['CardName'])
        m.DiffuseColor = material.Color
        m.Transparency = material.Transparency
        return m


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
            if sel.Proxy.Type in ['Wire', 'BSpline']:
                baselist.append(sel)
        elif sel.TypeId == 'Part::FeaturePython':
            if sel.Proxy.Type == 'Pipe':
                baselist.append(sel.Base)
            if sel.Proxy.Type in ['Wire', 'Compound']:
                baselist.append(sel)
        elif sel.TypeId == 'Part::Compound':
            baselist.append(sel)
    if len(baselist) > 1:
        baseobj = compoundPath.make_compoundpath(baselist)
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
    obj.MergeSubConduits = False
    if profileobj:
        obj.Profile = profileobj
    else:
        obj.Width.Value = 10.0
        obj.Height.Value = 10.0
        if gauge:
            obj.Gauge = gauge
        else:
            obj.Gauge = 20.0
    if placement:
        obj.Placement = placement
    return obj
