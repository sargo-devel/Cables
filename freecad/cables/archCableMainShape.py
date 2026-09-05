"""ArchCableMainShape based on ArchPipe.
Some parts of code are taken from there.
"""

# ***************************************************************************
# *   Copyright 2026 SargoDevel <sargo-devel at o2 dot pl>                  *
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
import ArchPipe
import Part
from freecad.cables import wireFlex
from freecad.cables import wireutils
from freecad.cables import cableutils
from freecad.cables.cableutils import logmsg
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP

ModuleName = __name__.split('.')[-1]


class ArchCableMainShape(ArchPipe._ArchPipe):
    """The ArchCableMainShape class
    """

    def __init__(self, obj):
        ArchPipe._ArchPipe.__init__(self, obj)

    def setDefaultShapeParameters(self, obj):
        obj.BiNormalVector = FreeCAD.Vector(0, 0, 1)
        self.setAutoTroubleshootingProperties(obj)
        obj.AutoTroubleshooting = True

    def setAutoTroubleshootingProperties(self, obj):
        obj.BiArcsApproxTolerance = 0.5
        obj.Frenet = False
        obj.MainShapeIfError = "BiArcs"
        obj.SurfaceMaxDegree = 5
        obj.SurfaceMaxSegments = 99
        obj.NumberOfAuxPoints = 0
        obj.TransitionMode = "RoundCorners"

    def setProperties(self, obj):
        ArchPipe._ArchPipe.setProperties(self, obj)
        pl = obj.PropertiesList
        class_name = type(obj.Proxy).__name__
        if class_name == "ArchCableConduit":
            prop_group = "ConduitShapeTroubleshooting"
        else:
            prop_group = "CableShapeTroubleshooting"
        if "MainShapeStatus" not in pl:
            obj.addProperty("App::PropertyString", "MainShapeStatus",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Build status of cable " +
                                "main shape\n(main shape = shape of " +
                                "insulation jacket)"))
            obj.setPropertyStatus("MainShapeStatus", "ReadOnly")
        if "MainShapeIfError" not in pl:
            obj.addProperty("App::PropertyEnumeration", "MainShapeIfError",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Method for creating a " +
                                "main shape when an error occurs"))
            obj.MainShapeIfError = ['Partial', 'BiArcs']
        if "MainShapeBuildMode" not in pl:
            obj.addProperty("App::PropertyEnumeration", "MainShapeBuildMode",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Build mode of main shape"))
            obj.MainShapeBuildMode = ['Standard', 'AuxiliarySpine', 'BiNormal',
                                      'BiArcsApprox']
        if "Frenet" not in pl:
            obj.addProperty("App::PropertyBool", "Frenet",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Frenet mode"))
        if "NumberOfAuxPoints" not in pl:
            obj.addProperty("App::PropertyInteger", "NumberOfAuxPoints",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Number of points for the " +
                                "construction of a new auxiliary spine"))
        if "AuxSpine" not in pl:
            obj.addProperty("App::PropertyLink", "AuxSpine",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Auxiliary spine"))
        if "BiArcsApproxTolerance" not in pl:
            obj.addProperty("App::PropertyLength", "BiArcsApproxTolerance",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Tolerance of BiArcs " +
                                "approximation of main shape if enabled"))
        if "BiNormalVector" not in pl:
            obj.addProperty("App::PropertyVector", "BiNormalVector",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Binormal vector for " +
                                "BiNormal mode"))
        if "SurfaceMaxSegments" not in pl:
            obj.addProperty("App::PropertyInteger", "SurfaceMaxSegments",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Maximum allowed number " +
                                "of segments that can be used to construct " +
                                "a pipe surface along its guide path"))
        if "SurfaceMaxDegree" not in pl:
            obj.addProperty("App::PropertyInteger", "SurfaceMaxDegree",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Maximum degree of the " +
                                "polynomial describing the curvature of " +
                                "the pipe's surface."))
        if "ShapeMemSize" not in pl:
            obj.addProperty("App::PropertyInteger", "ShapeMemSize",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Amount of memory used to " +
                                "store the shape, in KiB"))
        if "TransitionMode" not in pl:
            obj.addProperty("App::PropertyEnumeration", "TransitionMode",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Handling shape corners: " +
                                "transformed, right corners, round corners"))
            obj.TransitionMode = [
                "Transformed", "RightCorners", "RoundCorners"]
        if "AutoTroubleshooting" not in pl:
            obj.addProperty("App::PropertyBool", "AutoTroubleshooting",
                            prop_group,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Automatic detection and " +
                                "resolution of shape-related issues"))

    def onDocumentRestored(self, obj):
        ArchPipe._ArchPipe.onDocumentRestored(self, obj)
        if obj.BiArcsApproxTolerance == 0:
            obj.AutoTroubleshooting = True

    def onChanged(self, obj, prop):
        ArchComponent.Component.onChanged(self, obj, prop)
        ArchPipe._ArchPipe.onChanged(self, obj, prop)
        if prop == 'AutoTroubleshooting':
            auto_hide_list = ["AuxSpine", "BiArcsApproxTolerance",
                              "BiNormalVector", "Frenet", "MainShapeIfError",
                              "NumberOfAuxPoints", "ShapeMemSize",
                              "SurfaceMaxDegree", "SurfaceMaxSegments",
                              "TransitionMode"]
            if obj.AutoTroubleshooting:
                self.setAutoTroubleshootingProperties(obj)
                for element in auto_hide_list:
                    obj.setPropertyStatus(element, "Hidden")
            else:
                for element in auto_hide_list:
                    obj.setPropertyStatus(element, "-Hidden")

    def execute(self, obj):
        # copy of _ArchPipe.execute
        # from FreeCAD main branch, commit 14ac516, 2026-08-12
        # with changed references to makePipeShell
        # and modified error messages

        def _get_profile_center(prof):

            if hasattr(prof, "CenterOfMass"):
                return prof.CenterOfMass
            return prof.BoundBox.Center

        def _rotate_profile(prof, pt, vec):

            if vec.getAngle(FreeCAD.Vector(0, 0, 1)) > 0.01:
                up = FreeCAD.Vector(0, 0, 1)
            else:
                up = FreeCAD.Vector(0, 1, 0)
            vec_x = up.cross(vec)
            vec_y = vec.cross(vec_x)
            rot = FreeCAD.Rotation(vec_x, vec_y, vec, "ZYX")
            prof.rotate(pt, rot.Axis, math.degrees(rot.Angle))

        import math
        import Part

        if self.clone(obj):
            return
        pl = obj.Placement
        w = self.getWire(obj)
        if not w:
            #FreeCAD.Console.PrintError(translate("Arch", "Unable to build the base path") + "\n")
            logmsg(translate(
                "Cables", "Unable to build the cable base path"),
                "E", ModuleName, None, obj.Label)
            return
        if obj.OffsetStart.Value:
            e = w.Edges[0]
            v = e.Vertexes[-1].Point.sub(e.Vertexes[0].Point).normalize()
            v.multiply(obj.OffsetStart.Value)
            e = Part.LineSegment(e.Vertexes[0].Point.add(v), e.Vertexes[-1].Point).toShape()
            w = Part.Wire([e] + w.Edges[1:])
        if obj.OffsetEnd.Value:
            e = w.Edges[-1]
            v = e.Vertexes[0].Point.sub(e.Vertexes[-1].Point).normalize()
            v.multiply(obj.OffsetEnd.Value)
            e = Part.LineSegment(e.Vertexes[-1].Point.add(v), e.Vertexes[0].Point).toShape()
            w = Part.Wire(w.Edges[:-1] + [e])
        p = self.getProfile(obj)
        if not p:
            #FreeCAD.Console.PrintError(translate("Arch", "Unable to build the profile") + "\n")
            logmsg(translate(
                "Cables", "Unable to build the cable profile"),
                "E", ModuleName, None, obj.Label)
            return
        # move and rotate the profile to the first point
        delta = w.Vertexes[0].Point - _get_profile_center(p)
        p.translate(delta)
        import Draft

        if Draft.getType(obj.Base) == "BezCurve":
            v1 = obj.Base.Placement.multVec(obj.Base.Points[1]) - w.Vertexes[0].Point
        else:
            v1 = w.Vertexes[1].Point - w.Vertexes[0].Point
        _rotate_profile(p, w.Vertexes[0].Point, v1)

        shapes = []
        try:
            if p.Faces:
                for f in p.Faces:
                    #sh = w.makePipeShell([f.OuterWire], True, False, 2)
                    sh = self.makeMainShape(obj, w, f.OuterWire)
                    for shw in f.Wires:
                        if shw.hashCode() != f.OuterWire.hashCode():
                            #sh2 = w.makePipeShell([shw], True, False, 2)
                            sh2 = self.makeMainShape(obj, w, shw)
                            sh = sh.cut(sh2)
                    shapes.append(sh)
            elif p.Wires:
                for pw in p.Wires:
                    #sh = w.makePipeShell([pw], True, False, 2)
                    sh = self.makeMainShape(obj, w, pw)
                    shapes.append(sh)
        except Exception:
            #FreeCAD.Console.PrintError(translate("Arch", "Unable to build the pipe") + "\n")
            logmsg(translate(
                "Cables", "Unable to build the main shape"),
                "E", ModuleName, None, obj.Label)
        else:
            if len(shapes) == 0:
                return
            elif len(shapes) == 1:
                sh = shapes[0]
            else:
                sh = Part.makeCompound(shapes)
            obj.Shape = self.processSubShapes(obj, sh, pl)
            if obj.Base:
                obj.Length = w.Length
            else:
                obj.Placement = pl

    def calculateShapeMemSize(self, obj):
        return int(obj.Shape.MemSize/1024)

    def makeMainShape(self, obj, w=None, p=None):
        if w is None:
            w = self.getWire(obj)
        if not w:
            logmsg(translate(
                "Cables", "Unable to build the cable base path"),
                "E", ModuleName, None, obj.Label)
            return None
        if p is None:
            p = obj.SubProfiles[0].Shape.Wires[0]

        if obj.NumberOfAuxPoints == 0:
            # default number of points for building aux_wire
            obj.NumberOfAuxPoints = len(obj.Base.Points)*2

        try:
            if obj.MainShapeBuildMode == "BiArcsApprox":
                sh = self.tryBiArcsShape(obj, w, p)
            else:
                sh = self.makePipeShell(obj, w, p, obj.MainShapeBuildMode)
            obj.MainShapeStatus = "Ok"
        except Exception as err:
            sh = None
            obj.MainShapeStatus = "Error"
            if obj.MainShapeIfError == "Partial":
                logmsg(translate(
                    "Cables", "Unable to build main shape in mode:") +
                    f" {obj.MainShapeBuildMode}",
                    "E", ModuleName, err, obj.Label)
                sh = self.tryPartialShape(obj, w, p)
            else:
                sh = self.tryBiArcsShape(obj, w, p)
            if sh is None:
                logmsg(translate(
                    "Cables", "Building shape in error mode failed " +
                    "(shape is None)!"),
                    "E", ModuleName, None, obj.Label)
        return sh

    def tryPartialShape(self, obj, w, p):
        bspline_t = 'Part::GeomBSplineCurve'
        best_shape = None
        edges = []
        for e in w.Edges:
            if e.Curve.TypeId == bspline_t:
                c_main = e.Curve
                low = c_main.FirstParameter
                high = c_main.LastParameter
                max_iter = 50
                tolerance = (high-low)/100.0
                logmsg("Trying to build partial shape",
                       "M", ModuleName, None, obj.Label)
                for i in range(max_iter):
                    mid = (low + high) / 2.0

                    try:
                        c = c_main.clone()
                        u0 = c.FirstParameter
                        u1 = mid
                        c.segment(u0, u1)
                        test_wire = Part.Wire(edges + [c.toShape()])
                        # sh = test_wire.makePipeShell([p], True, False, 2)
                        sh = self.makePipeShell(
                            obj, test_wire, p, obj.MainShapeBuildMode)
                        if sh and sh.isValid():
                            low = mid
                            best_shape = sh
                        else:
                            high = mid
                    except Part.OCCError:
                        high = mid

                    if (high - low) <= tolerance:
                        logmsg("Shape build error found at parameter: " +
                               f"{mid} after {i+1} iterations",
                               "DW", ModuleName, None, obj.Label)
                        err_status = obj.MainShapeStatus
                        first = c_main.FirstParameter
                        last = c_main.LastParameter
                        param = 100.0*(mid - first)/(last - first)
                        obj.MainShapeStatus = err_status + \
                            f" ({param:.2f}% made, {i+1}iter.)"
                        break
                return best_shape
            else:
                edges.append(e)
        return best_shape

    def tryBiArcsShape(self, obj, w, p):
        tolerance = obj.BiArcsApproxTolerance.Value
        w_arcs = wireutils.getBiArcsApprox(w, tolerance)
        logmsg(f"w_arc Len = {w_arcs.Length}, nr of segs={len(w_arcs.Edges)}",
               "DW", ModuleName, None, obj.Label)
        try:
            # sh = w_arcs.makePipeShell([p], True, False, 2)
            sh = self.makePipeShell(obj, w_arcs, p, obj.MainShapeBuildMode)
            diff = 100.0*(w_arcs.Length - w.Length)/w.Length
            obj.MainShapeStatus = \
                f"BiArcsApprox (diff={diff:.2f}%, {len(w_arcs.Edges)}segs)"
            if abs(diff) > 1.0:
                logmsg(translate(
                    "Cables", "The length of the BiArcs approximated main " +
                    "shape differs by more than 1% from the target. Check " +
                    "properties from 'Cable Shape Troubleshooting' group"),
                    "W", ModuleName, None, obj.Label)
            else:
                logmsg(translate(
                    "Cables", "A shape approximation was built from BiArcs"),
                    "N", ModuleName, None, obj.Label)
        except Part.OCCError as err:
            logmsg(translate(
                "Cables", "BiArcs main shape approximation failed in mode:") +
                f" {obj.MainShapeBuildMode}",
                "E", ModuleName, err, obj.Label)
            sh = None
        return sh

    def makePipeShell(self, obj, w, p, mode, isSolid=True):
        """Modificaton of build in makePipeShell function
        obj - object (all setting are taken from obj parameters)
        w - spine of type wire
        p - profile of type wire
        mode - build mode, options: 'Standard', 'AuxiliarySpine', 'BiNormal'
        isSolid - shape type (default True)
        """
        frenet = obj.Frenet
        max_seg = obj.SurfaceMaxSegments
        max_deg = obj.SurfaceMaxDegree
        transition = obj.getEnumerationsOfProperty(
            'TransitionMode').index(obj.TransitionMode)
        nb_aux_pts = obj.NumberOfAuxPoints
        bi_norm_vect = obj.BiNormalVector

        ps = Part.BRepOffsetAPI.MakePipeShell(w)
        ps.setMaxDegree(max_deg)
        ps.setMaxSegments(max_seg)
        ps.setTransitionMode(transition)
        t_3d = 1.0e-2       # default = 1.0e-4
        t_bound = 1.0e-3    # default = 1.0e-4
        t_angul = 1.0e-1    # default = 1.0e-2
        ps.setTolerance(t_3d, t_bound, t_angul)
        if frenet:
            ps.setFrenetMode(True)

        ps.add(p)

        if mode == "AuxiliarySpine":
            # Try Auxiliary spine mode
            aux_wire = None
            # 1. create auxiliary wire
            profiles = ps.simulate(nb_aux_pts)
            aux_pts = [p.Vertexes[0].Point for p in profiles]
            if obj.AuxSpine is not None:
                if len(obj.AuxSpine.Shape.Wires) > 0:
                    aux_wire = obj.AuxSpine.Shape.Wires[0]
            else:
                aux_obj = wireFlex.make_wireflex_from_vectors(aux_pts)
                obj.AuxSpine = aux_obj
                if obj.AutoLabelSubLines:
                    self.setSubLinesLabels(obj)
                cableutils.attach_in_place([obj.AuxSpine, obj.Base])
                aux_wire = Part.makePolygon(aux_pts)
            # 2. Add auxiliary wire to Pipe shell
            if aux_wire is not None:
                ps.setAuxiliarySpine(
                    aux_wire,
                    False,          # curvilinear equivalence
                    0               # contact type
                )

        if mode == "BiNormal":
            ps.setBiNormalMode(bi_norm_vect)

        if ps.isReady():
            ps.build()
            ps.makeSolid()
        else:
            raise Part.OCCError("Shape not ready")
        sh = ps.shape()
        if not sh.isValid():
            raise Part.OCCError("Shape invalid")
        return sh

    def setSubLinesLabels(self, obj):
        prefix = obj.Label
        aux = '_Aux'
        if hasattr(obj, "AuxSpine") and obj.AuxSpine:
            aux_l = prefix + aux
            if obj.AuxSpine.Label != aux_l:
                obj.AuxSpine.Label = aux_l


class ViewProviderCableMainShape(ArchPipe._ViewProviderPipe):
    """A View Provider for the ArchCableMainShape object
    """

    def __init__(self, vobj):
        ArchPipe._ViewProviderPipe.__init__(self, vobj)

    def updateData(self, obj, prop):
        ArchPipe._ViewProviderPipe.updateData(self, obj, prop)

        if prop == "AuxSpine" and obj.AuxSpine is not None:
            obj.AuxSpine.ViewObject.DrawStyle = "Dotted"

    def claimChildren(self):
        children = ArchPipe._ViewProviderPipe.claimChildren(self)
        if hasattr(self, "Object"):
            if hasattr(self.Object, "AuxSpine"):
                children.append(self.Object.AuxSpine)
        return children
