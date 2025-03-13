"""ArchCable based on ArchPipe
ArchCable is inspired by ArchWindow class.
Some parts of code are taken from there
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


import FreeCAD
import ArchComponent
import Arch
import ArchPipe
import os
import Draft
import DraftGeomUtils
import math
import wireFlex
import wireutils
import Part
from commonutils import QT_TRANSLATE_NOOP


translate = FreeCAD.Qt.translate
_dir = os.path.dirname(__file__)
iconPath = os.path.join(_dir, "Resources/icons")
CLASS_CABLE_ICON = os.path.join(iconPath, "classArchCable.svg")
tol = 1e-6     # tolerance for isEqual() comparision


class ArchCable(ArchPipe._ArchPipe):
    """The ArchCable class
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
        if "SubProfiles" not in pl:
            obj.addProperty("App::PropertyLinkList", "SubProfiles", "Cable",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "List of Sub Profiles on " +
                                "both ends of the cable"))
        if "SubWires" not in pl:
            obj.addProperty("App::PropertyLinkList", "SubWires", "Cable",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "List of Sub Wires on both " +
                                "ends of the cable"))
        if "SubColors" not in pl:
            obj.addProperty("App::PropertyStringList", "SubColors", "Cable",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "List of Sub Cable Colors " +
                                "on both ends of the cable. Example: " +
                                "['J:0', 'L1:1', 'N:2', 'PE:3', 'CU:-1']"))
        if "ShowSubLines" not in pl:
            obj.addProperty("App::PropertyBool", "ShowSubLines", "Cable",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Shows/hides all sub " +
                                "lines: base wire, sub profiles, sub wires"))
        if "StrippedWireLength" not in pl:
            obj.addProperty("App::PropertyLength", "StrippedWireLength",
                            "Cable",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Offset from the " +
                                "bare subwire end to its insulation"))
        if "AutoLabelSubLines" not in pl:
            obj.addProperty("App::PropertyBool", "AutoLabelSubLines", "Cable",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Automatically " +
                                "change labels of all sub lines: base wire, " +
                                "sub profiles, sub wires"))
        if "BaseWireFilletRadius" not in pl:
            obj.addProperty("App::PropertyLength", "BaseWireFilletRadius",
                            "Cable",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Changes fillet " +
                                "radius of base object which finally " +
                                "changes fillet radius of a cable"))
        if "SubWiresFilletRadius" not in pl:
            obj.addProperty("App::PropertyLength", "SubWiresFilletRadius",
                            "Cable",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Changes fillet " +
                                "radius of all sub wires objects"))
        if "CableRotation" not in pl:
            obj.addProperty("App::PropertyAngle", "CableRotation", "Cable",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Changes rotation " +
                                "of a cable by changing cable profile " +
                                "attachment offset angle"))
        if "ConductorGauge" not in pl:
            obj.addProperty("App::PropertyFloat", "ConductorGauge",
                            "CableDimensions",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Gauge [mm^2] of conductor " +
                                "wire if profile not used"))
        if "InsulationThickness" not in pl:
            obj.addProperty("App::PropertyLength", "InsulationThickness",
                            "CableDimensions",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Thickness of single " +
                                "insulation if profile not used"))
        if "Profile" in pl and obj.getGroupOfProperty("Profile") == "Pipe":
            obj.setGroupOfProperty("Profile", "Cable")
            obj.setDocumentationOfProperty("Profile", QT_TRANSLATE_NOOP(
                "App::Property", "An optional closed profile to base this " +
                "cable on"))
        if "Length" in pl and obj.getGroupOfProperty("Length") == "Pipe":
            obj.setGroupOfProperty("Length", "CableDimensions")
            obj.setDocumentationOfProperty("Length", QT_TRANSLATE_NOOP(
                "App::Property", "The length of this cable"))

        proplist = ["Diameter", "OffsetStart", "OffsetEnd", "ProfileType",
                    "WallThickness"]
        for prop in proplist:
            if (prop in pl) and \
               (str(obj.getPropertyStatus(prop)[0]) != "Hidden"):
                obj.setPropertyStatus(prop, "Hidden")

        self.Type = "Pipe"

    def onChanged(self, obj, prop):
        # FreeCAD.Console.PrintMessage(f"ArchCable.onChanged(start): {prop}\n")
        ArchPipe._ArchPipe.onChanged(self, obj, prop)
        if prop == "ShowSubLines" and hasattr(obj, "SubProfiles") \
           and hasattr(obj, "SubWires"):
            if obj.SubProfiles:
                for p in obj.SubProfiles:
                    p.ViewObject.show() if obj.ShowSubLines \
                        else p.ViewObject.hide()
            if obj.SubWires:
                for w in obj.SubWires:
                    w.ViewObject.show() if obj.ShowSubLines \
                        else w.ViewObject.hide()
            if obj.Base:
                obj.Base.ViewObject.show() if obj.ShowSubLines \
                    else obj.Base.ViewObject.hide()
        if prop == "AutoLabelSubLines" and obj.AutoLabelSubLines:
            self.setSubLinesLabels(obj)
        if prop == "Label" and obj.AutoLabelSubLines:
            self.setSubLinesLabels(obj)
        if prop == "Shape":
            obj.Length = self.calculateCableLength(obj)
        if prop == "BaseWireFilletRadius":
            if hasattr(obj.Base, 'Links') and len(obj.Base.Shape.Wires) > 1:
                obj.Base.Links[0].FilletRadius = obj.BaseWireFilletRadius
                obj.Base.Links[-1].FilletRadius = obj.BaseWireFilletRadius
            else:
                obj.Base.FilletRadius = obj.BaseWireFilletRadius
        if prop == "SubWiresFilletRadius":
            if obj.SubWires:
                for subw in obj.SubWires:
                    if hasattr(subw, "FilletRadius"):
                        subw.FilletRadius = obj.SubWiresFilletRadius
        if prop == "CableRotation":
            obj.Profile.AttachmentOffset.Rotation.Angle = \
                math.radians(obj.CableRotation)
        if prop == "ConductorGauge" or prop == "InsulationThickness":
            obj.Diameter = math.sqrt(obj.ConductorGauge/math.pi)*2 + \
                obj.InsulationThickness.Value*2
        if prop == "StrippedWireLength":
            obj.OffsetStart = obj.StrippedWireLength
            obj.OffsetEnd = obj.StrippedWireLength
        if prop == "Profile":
            if obj.Profile:
                obj.setPropertyStatus("ConductorGauge", "Hidden")
                obj.setPropertyStatus("InsulationThickness", "Hidden")
            else:
                obj.setPropertyStatus("ConductorGauge", "-Hidden")
                obj.setPropertyStatus("InsulationThickness", "-Hidden")

    def onBeforeChange(self, obj, prop):
        # FreeCAD.Console.PrintMessage(f"WireFlex.onBeforeChange: {prop} \n")
        super().onBeforeChange(obj, prop)
        if prop == "BaseWireFilletRadius" and obj.SubProfiles:
            obj.SubProfiles[1].MapMode = "Deactivated"

    def execute(self, obj):
        # FreeCAD.Console.PrintMessage("ArchCable.execute: start\n")
        if not obj.SubProfiles:
            ArchPipe._ArchPipe.execute(self, obj)
            pl = obj.Placement
            main_shape = obj.Shape
            if not obj.Shape.Wires:
                return
            shapes = []
            shapes.append(main_shape)
            shapes += self.buildStrips(obj)
            sh = Part.makeCompound(shapes)
            obj.Shape = self.processSubShapes(obj, sh, pl)
        else:
            pl = obj.Placement
            main_shape = self.makeMainShape(obj)
            if not main_shape:
                return
            shapes = []
            shapes.append(main_shape)
            if obj.SubProfiles and obj.SubWires:
                shapes += self.buildSubCables(obj)
            sh = Part.makeCompound(shapes)
            obj.Shape = self.processSubShapes(obj, sh, pl)
            self.readjustEndProfile(obj)
            self.rotateEndProfile(obj)
            self.readjustSubWires(obj)
        # FreeCAD.Console.PrintMessage("ArchCable.execute: end\n")

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
        last_vertex = None
        for wire in obj.Base.Shape.Wires:
            if last_vertex:
                if last_vertex.Point.isEqual(wire.Vertexes[0].Point, tol):
                    last_vertex = wire.Vertexes[-1]
                elif last_vertex.Point.isEqual(
                        wire.Vertexes[-1].Point, tol):
                    last_vertex = wire.Vertexes[0]
                else:
                    FreeCAD.Console.PrintError(translate(
                        "Cables", "Base compound object not continous or " +
                        "wrong direction of first wire in compound")
                        + "\n")
                    return False
            else:
                last_vertex = wire.Vertexes[-1]
        if last_vertex.Point.isEqual(wire.Vertexes[0].Point, tol):
            FreeCAD.Console.PrintError(translate(
                "Cables", "Base compound has wrong direction of last wire")
                + "\n")
            return False
        return True

    def buildStrips(self, obj):
        radius = math.sqrt(obj.ConductorGauge/math.pi)
        shapes = []
        for i in [-2, -1]:
            prof = obj.Shape.Wires[i]
            norm = DraftGeomUtils.get_shape_normal(prof)
            v1 = prof.CenterOfMass
            if i == -2:
                v2 = obj.Base.Shape.Vertexes[0].Point
            else:
                v2 = obj.Base.Shape.Vertexes[i].Point
            edge = Part.LineSegment(v1, v2).toShape()
            circle = Part.Circle(v1, norm, radius)
            cprof = Part.Wire([Part.Edge(circle)])
            wire = Part.Wire([edge])
            shape = wire.makePipeShell([cprof], True, False, 2)
            shapes.append(shape)
        return shapes

    def calculateCableLength(self, obj):
        if obj.SubWires:
            nr_subw = int(len(obj.SubWires)/2)
            slist = []
            elist = []
            for i in range(nr_subw):
                slist.append(obj.SubWires[i].Length)
                elist.append(obj.SubWires[nr_subw+i].Length)
            slen = max(slist)
            elen = max(elist)
            if len(obj.Base.Shape.Wires) > 1:
                length = 0.0
                for w in obj.Base.Shape.Wires:
                    length += w.Length
                length = length + slen.Value + elen.Value
            else:
                length = obj.Base.Length.Value + slen.Value + elen.Value
        else:
            if len(obj.Base.Shape.Wires) > 1:
                length = 0.0
                for w in obj.Base.Shape.Wires:
                    length += w.Length
            else:
                length = obj.Base.Length.Value
        return length

    def makeMainShape(self, obj):
        w = self.getWire(obj)
        if not w:
            FreeCAD.Console.PrintError(translate(
                "Cables", "Unable to build the base path")+"\n")
            return None
        p = obj.SubProfiles[0].Shape.Wires[0]
        sh = w.makePipeShell([p], True, False, 2)
        return sh

    def makeSubProfiles(self, obj):
        profiles = []
        if obj.Profile:
            cl = Draft.make_clone(obj.Profile)
            cl.AttachmentSupport = [(obj.Base, 'Vertex1'), (obj.Base, 'Edge1')]
            cl.MapMode = 'NormalToEdge'
            cl.MapReversed = False
            pl = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0),
                                   FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1),
                                   0))
            cl.AttachmentOffset = pl
            profiles.append(cl)
            cl = Draft.make_clone(obj.Profile)
            v_last = len(obj.Base.Shape.Vertexes)
            e_last = len(obj.Base.Shape.Edges)
            cl.AttachmentSupport = [(obj.Base, 'Vertex'+str(v_last)),
                                    (obj.Base, 'Edge'+str(e_last))]
            cl.MapMode = 'NormalToEdge'
            cl.MapReversed = False
            cl.AttachmentOffset = pl
            profiles.append(cl)
            Arch.addComponents(profiles, obj)
            obj.SubProfiles = profiles
            obj.Profile = obj.SubProfiles[0]
        return profiles

    def makeSubWires(self, obj):
        wires = []
        for i, profile in enumerate(obj.SubProfiles):
            norm = DraftGeomUtils.get_shape_normal(profile.Shape)
            if i == 1:
                norm = norm.negative()
            v_max = len(profile.Shape.Vertexes)
            nr_pts = int((len(profile.Shape.Wires) - 1)/2)
            for i in range(v_max-nr_pts, v_max):
                v1 = profile.Shape.Vertexes[i]
                v2_p = v1.Point + norm * 5
                v3_p = v1.Point + norm * 20
                w = wireFlex.make_wireflex_from_vectors([v1.Point, v2_p, v3_p])
                w.AttachmentSupport = [(profile, 'Vertex'+str(i+1))]
                w.MapMode = 'Translate'
                w.Vrtx_start = (profile, 'Vertex'+str(i+1))
                wires.append(w)
        Arch.addComponents(wires, obj)
        obj.SubWires = wires
        return wires

    def buildSubCables(self, obj):
        shapes = []
        for idxp, subprofile in enumerate(obj.SubProfiles):
            sub_qty = int((len(subprofile.Shape.Wires)-1)/2)
            shapes1 = []
            shapes2 = []
            for idxw, p in enumerate(subprofile.Shape.Wires[1:sub_qty+1]):
                if obj.SubWires[idxw+sub_qty*idxp].Shape.Wires:
                    w = obj.SubWires[idxw+sub_qty*idxp].Shape.Wires[0]
                    p_in = subprofile.Shape.Wires[1+idxw+sub_qty]
                    # subwire insulation
                    shapes1.append(self.buildSingleSubShape(obj, p, p_in, w))
                    # bare subwire
                    shapes2.append(self.buildSingleSubShape(obj, p_in, None,
                                                            w))
            shapes.extend(shapes1 + shapes2)
        return shapes

    def buildSingleSubShape(self, obj, profile_out, profile_in, wire):
        if profile_in:
            wire = self.addOffsetToWire(obj, wire)
            shape = wire.makePipeShell([profile_out], True, False, 2)
            shape_in = wire.makePipeShell([profile_in], True, False, 2)
            shape = shape.cut(shape_in)
        else:
            shape = wire.makePipeShell([profile_out], True, False, 2)
        return shape

    def addOffsetToWire(self, obj, w):
        e = w.Edges[-1]
        v1 = e.Vertexes[0].Point
        v2 = e.Vertexes[-1].Point
        v = v1.sub(v2).normalize()
        if e.Length > obj.StrippedWireLength.Value:
            v.multiply(obj.StrippedWireLength.Value)
        else:
            v.multiply(e.Length-0.1)
        vx = v2.add(v)
        if (vx-v1).Length+(vx-v2).Length > (v1-v2).Length+0.01 \
           or vx == v1 or vx == v2:
            # vx too short or in wrong direction
            w = Part.Wire(w.Edges[:-1]) if len(w.Edges) > 2 else w
        else:
            e = Part.LineSegment(vx, v1).toShape()
            w = Part.Wire(w.Edges[:-1]+[e])
        return w

    def readjustEndProfile(self, obj):
        end_prof = obj.SubProfiles[1]
        old_pair = end_prof.AttachmentSupport[0][1]
        # e.g. old_pair = ('Vertex4','Edge3')
        v_last = len(obj.Base.Shape.Vertexes)
        e_last = len(obj.Base.Shape.Edges)
        base_end_changed = False
        for i, name in enumerate(old_pair):
            if 'Vertex' in name:
                if int(name.split('Vertex')[1]) != v_last:
                    base_end_changed = True
            if 'Edge' in name:
                if int(name.split('Edge')[1]) != e_last:
                    base_end_changed = True
        if base_end_changed:
            end_prof.AttachmentSupport = [(obj.Base, 'Vertex'+str(v_last)),
                                          (obj.Base, 'Edge'+str(e_last))]
            end_prof.MapReversed = False
        if end_prof.MapMode != "NormalToEdge":
            end_prof.MapMode = "NormalToEdge"

    def getEndProfileAngleDiff(self, obj):
        # End face of cable main body (jacket):
        cable_wire_end = obj.Shape.Solids[0].Wires[-1]
        v1_cable_end = cable_wire_end.Edges[0].Vertexes[0].Point
        angle = None
        if obj.SubProfiles:
            end_prof = obj.SubProfiles[1]
            if end_prof.Shape.Wires:
                norm = DraftGeomUtils.get_shape_normal(end_prof.Shape)
                v1_profile = end_prof.Shape.Wires[0].Vertexes[0].Point
                v0 = end_prof.Shape.BoundBox.Center
                v1_cable_end_diff = v1_cable_end - v0
                v1_profile_diff = v1_profile - v0
                angle = v1_cable_end_diff.getAngle(v1_profile_diff)
                if v1_profile_diff.cross(v1_cable_end_diff).dot(norm) < 0:
                    angle = -angle
        return angle

    def rotateEndProfile(self, obj):
        angle = self.getEndProfileAngleDiff(obj)
        prof = obj.SubProfiles[1]
        if abs(angle) > 0.001:
            angle_deg = math.degrees(angle)
            old_angle_deg = math.degrees(prof.AttachmentOffset.Rotation.Angle)
            new_angle_deg = (old_angle_deg + angle_deg) % 360
            prof.AttachmentOffset = FreeCAD.Placement(
                FreeCAD.Vector(0, 0, 0),
                FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), new_angle_deg))

    def readjustSubWires(self, obj):
        """It keeps the first edge of subwire normal to cable start/end face
        Additionally it sets this edge length to 5mm
        """
        nr_subw = int(len(obj.SubWires)/2)
        for i, subw in enumerate(obj.SubWires):
            subp = obj.SubProfiles[0] if i < nr_subw else obj.SubProfiles[1]
            norm = DraftGeomUtils.get_shape_normal(subp.Shape)
            if i >= nr_subw:
                norm = norm.negative()
            pts = subw.Points
            pts[1] = pts[0] + norm*5
            if (subw.Points[1] != pts[1]) or (2 in subw.Vrtxs_mid_idx):
                wireutils.removePointAttachment([(subw, 'Vertex2')])
                subw.Points = pts

    def setSubLinesLabels(self, obj):
        prefix = obj.Label
        tieA = '_A_'
        tieB = '_B_'
        suffixA = '_A'
        suffixB = '_B'
        prof = 'Profile'
        base = '_Base'
        nr = int(len(obj.SubWires)/2)
        for i in range(nr):
            suffix = obj.ViewObject.Proxy.getSolidName(obj, i+1)
            obj.SubWires[i].Label = prefix + tieA + suffix
            obj.SubWires[i+nr].Label = prefix + tieB + suffix
        if len(obj.SubProfiles) == 2:
            obj.SubProfiles[0].Label = prefix + tieA + prof
            obj.SubProfiles[1].Label = prefix + tieB + prof
        if obj.Base:
            obj.Base.Label = prefix + base
            if hasattr(obj.Base, 'Links') and len(obj.Base.Shape.Wires) > 1:
                obj.Base.Links[0].Label = obj.Base.Label + suffixA
                obj.Base.Links[-1].Label = obj.Base.Label + suffixB


class ViewProviderCable(ArchComponent.ViewProviderComponent):
    """A View Provider for the ArchCable object
    """

    def __init__(self, vobj):
        ArchComponent.ViewProviderComponent.__init__(self, vobj)

    def getIcon(self):
        return CLASS_CABLE_ICON

    def updateData(self, obj, prop):
        ArchComponent.ViewProviderComponent.updateData(self, obj, prop)
        if prop == "Shape" and hasattr(obj.ViewObject, "UseMaterialColor"):
            if obj.ViewObject.UseMaterialColor:
                self.colorize(obj)

    def onChanged(self, vobj, prop):
        # FreeCAD.Console.PrintMessage(f"ViewProviderCable: {prop}\n")
        if prop == "ShapeAppearance" and hasattr(vobj, "UseMaterialColor"):
            if vobj.UseMaterialColor:
                self.colorize(vobj.Object)
        if prop == "UseMaterialColor" and vobj.UseMaterialColor:
            self.colorize(vobj.Object)
        ArchComponent.ViewProviderComponent.onChanged(self, vobj, prop)

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

        # setting different part colors
        if hasattr(obj, "CloneOf") and obj.CloneOf:
            obj, clone = obj.CloneOf, obj
            base_sapp_mat = clone.ViewObject.ShapeAppearance[0]
            arch_mat = getattr(clone, "Material", None)
        else:
            clone = None
            base_sapp_mat = obj.ViewObject.ShapeAppearance[0]
            arch_mat = getattr(obj, "Material", None)

        solids = obj.Shape.copy().Solids
        sapp = []
        base_sapp_mat = obj.ViewObject.ShapeAppearance[0]
        arch_mat = getattr(obj, "Material", None)
        # sub_qty = int((len(obj.Profile.Shape.Wires)-1)/2)
        for i in range(len(solids)):
            color = None
            mat_name = self.getSolidName(obj, i)
            # FreeCAD.Console.PrintMessage(f"mat_name: {mat_name}\n")
            color = self.getSolidMaterial(obj, arch_mat, mat_name)
            if color is None:
                sapp_mat = base_sapp_mat
            else:
                sapp_mat = FreeCAD.Material()
                sapp_mat.DiffuseColor = color[:3] + (0.0, )
                sapp_mat.Transparency = color[3]
            sapp.extend((sapp_mat, ) * len(solids[i].Faces))

        if clone is not None:
            obj = clone
        if not _shapeAppearanceIsSame(obj.ViewObject.ShapeAppearance, sapp):
            obj.ViewObject.ShapeAppearance = sapp

    def getSolidName(self, obj, idx):
        """It gets solid name based on SubColors pattern
        SubColors pattern example:
        ['J:0', 'L1:1,7', 'N:2,8', 'PE:3,9', 'CU:-1']
        It it also possible to skip indexes for second end of cable.
        They will be counted automatically by idx_norm
        Example:
        ['J:0', 'L1:1', 'N:2', 'PE:3', 'CU:-1']
        """
        name = None
        if len(obj.SubProfiles) > 0:
            nr_of_wires = int((len(obj.SubProfiles[0].Shape.Wires)-1)/2)
            if idx > 2*nr_of_wires and idx <= 3*nr_of_wires:
                idx_norm = idx - 2*nr_of_wires
            else:
                idx_norm = idx
        else:
            # single wire
            idx_norm = 1 if idx > 1 else idx
        if hasattr(obj, "SubColors"):
            for elm in obj.SubColors:
                pair = elm.split(':')
                name = pair[0] if (str(idx) in pair[1].split(',')) \
                    or ('-1' in pair[1].split(',')) \
                    else None
                if not name:
                    name = pair[0] if (str(idx_norm) in pair[1].split(',')) \
                        or ('-1' in pair[1].split(',')) \
                        else None
                if name:
                    break
        return name

    def getSolidMaterial(self, obj, arch_mat, mat_name):
        color = None
        if arch_mat is not None and hasattr(arch_mat, "Materials"):
            if mat_name in arch_mat.Names:
                mat_idx = arch_mat.Names.index(mat_name)
                mat = arch_mat.Materials[mat_idx]
                if mat:
                    if 'DiffuseColor' in mat.Material:
                        diff_col = mat.Material['DiffuseColor']
                        if "(" in diff_col:
                            col_str_lst = diff_col.strip("()").split(",")
                            color = tuple([float(f) for f in col_str_lst])
                    if color and ('Transparency' in mat.Material):
                        t = float(mat.Material['Transparency'])/100.0
                        color = color[:3] + (t, )
        return color


def makeCable(baseobj=None, profileobj=None, gauge=0, length=0,
              placement=None, name=None):
    "Creates a cable object from the given base object"
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No active document. Aborting") + "\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython", "Cable")
    obj.Label = name if name else translate("Cables", "Cable")
    ArchCable(obj)
    if FreeCAD.GuiUp:
        ViewProviderCable(obj.ViewObject)
        if baseobj:
            baseobj.ViewObject.hide()
        if profileobj:
            profileobj.ViewObject.hide()
    if baseobj:
        obj.Base = baseobj
    else:
        if length:
            obj.Length = length
        else:
            obj.Length = 1000
    if profileobj:
        obj.Profile = profileobj
    else:
        if gauge:
            obj.ConductorGauge = gauge
        else:
            obj.ConductorGauge = 2.0
        obj.StrippedWireLength = 8
        obj.InsulationThickness.Value = 0.7
        obj.Width = obj.Diameter
        obj.Height = obj.Diameter
        obj.SubColors = createSubColorsList(0)
    if placement:
        obj.Placement = placement
    # SubProfiles
    if obj.Profile and not obj.SubProfiles:
        obj.Proxy.makeSubProfiles(obj)
        FreeCAD.ActiveDocument.recompute()
        obj.SubColors = createSubColorsList(
            int(len(obj.Profile.Shape.Wires)-1)/2)
        # Subwires
        obj.Proxy.makeSubWires(obj)
        obj.ShowSubLines = True
        if obj.SubColors:
            obj.AutoLabelSubLines = True
        obj.StrippedWireLength = 8
        # FreeCAD.ActiveDocument.recompute()
    return obj


def createSubColorsList(nr_of_wires):
    sub_colors = []
    if nr_of_wires == 0:
        sub_colors = ['L1:0', 'CU:-1']
    if nr_of_wires == 1:
        sub_colors = ['J:0', 'L1:1', 'CU:-1']
    if nr_of_wires == 2:
        sub_colors = ['J:0', 'L1:1', 'N:2', 'CU:-1']
    if nr_of_wires == 3:
        sub_colors = ['J:0', 'L1:1', 'N:2', 'PE:3', 'CU:-1']
    if nr_of_wires == 4:
        sub_colors = ['J:0', 'L1:1', 'L2:2', 'L3:3', 'PE:4', 'CU:-1']
    if nr_of_wires == 5:
        sub_colors = ['J:0', 'L1:1', 'L2:2', 'L3:3', 'N:4', 'PE:5',
                      'CU:-1']
    if nr_of_wires == 8:
        sub_colors = ['J:0', 'P1A:1', 'P1B:2', 'P2A:3', 'P2B:4',
                      'P3A:5', 'P3B:6', 'P4A:7', 'P4B:8', 'CU:-1']
    return sub_colors
