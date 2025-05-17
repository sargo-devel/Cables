# Test harness for Cables workbench

import FreeCAD
import freecad.cables

#from freecad.cables import archCable
#from freecad.cables import archCableConduit
#from freecad.cables import archCableBox
#from freecad.cables import archCableConnector
#from freecad.cables import archCableLightPoint
#from freecad.cables import wireFlex
#from freecad.cables import cableProfile
#from freecad.cables import cableMaterial
import freecad.cables.cableSupport
import freecad.cables.cableProfile

App = FreeCAD
Vector = FreeCAD.Vector
doc = App.ActiveDocument

#con1_base
points = [FreeCAD.Vector(0.0, 200.0, 0.0), FreeCAD.Vector(0.0, 380.0, 0.0)]
c1_base = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
#con2_base
points = [FreeCAD.Vector(0.0, 600.0, 0.0), FreeCAD.Vector(0.0, 420.0, 0.0)]
c2_base = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
#con3_base
points = [FreeCAD.Vector(20.0, 400.0, 0.0), FreeCAD.Vector(200.0, 400.0, 0.0)]
c3_base = freecad.cables.wireFlex.make_wireflex_from_vectors(points)

#cable x3 base A
points = [Vector (0.0, 0.0, 0.0), Vector (-20.179534912109375, 72.73262786865234, 0.0), Vector (-70.17953491210938, 112.73262786865234, 0.0), Vector (-100.17953491210938, 152.73262786865234, 0.0)]
[Vector (0.0, 0.0, 0.0), Vector (-20.179534912109375, 72.73262786865234, 0.0), Vector (-70.17953491210938, 112.73262786865234, 0.0), Vector (-100.17953491210938, 152.73262786865234, 0.0)]
cx3_baseA = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(100.18,47.2674,0), (0,0,0,1)]
pl = FreeCAD.Placement()
pl.Base = p[0]
pl.Rotation = p[1]
cx3_baseA.Placement = pl
cx3_baseA.FilletRadius.Value = 30.0
cx3_baseA.Parameterization = 0.8
cx3_baseA.BoundarySegmentStart.Value = 10.0
cx3_baseA.BoundarySegmentEnd.Value = 30.0
cx3_baseA.PathType = "BSpline_K"

#cable x3 base B
points = [Vector (0.0, 0.0, 0.0), Vector (40.0, -10.0, 0.0), Vector (100.0, 100.0, 0.0)]
cx3_baseB = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(200,400,0), (0,0,0,1)]
pl = FreeCAD.Placement()
pl.Base = p[0]
pl.Rotation = p[1]
cx3_baseB.Placement = pl
cx3_baseB.FilletRadius.Value = 30.0
cx3_baseB.PathType = "Wire"

#cond_b1
points = [Vector (0.0, 0.0, 0.0), Vector (-0.5721274018287659, 143.9613494873047, 0.0)]
cond_b1 = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(0.572127,56.0387,0), (0,0,0,1)]
pl.Base = p[0]
pl.Rotation = p[1]
cond_b1.Placement = pl
cond_b1.PathType = "Wire"

#cond_b2
points = [Vector (0.0, 0.0, 0.0), Vector (-0.140807194616425, 23.72398472306645, 0.0)]
cond_b2 = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(0,600,0), (0,0,0,1)]
pl.Base = p[0]
pl.Rotation = p[1]
cond_b2.Placement = pl
cond_b2.PathType = "Wire"

#cond_b3
points = [Vector (9.197133802317644, 54.224657374410526, 0.0), Vector (60.0, 100.0, 0.0)]
cond_b3 = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(0,600,0), (0,0,0,1)]
pl.Base = p[0]
pl.Rotation = p[1]
cond_b3.Placement = pl
cond_b3.Points = points
cond_b3.PathType = "Wire"

# c_single_1A
points = [Vector (15.236785638414581, -0.8958652578912449, 0.0), Vector (15.286063700914383, 28.019325256347656, 0.0), Vector (30.572127401828766, 56.03865051269531, 0.0)]
c_single_1A = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(-30,0,0), (0,0,0,1)]
pl.Base = p[0]
pl.Rotation = p[1]
c_single_1A.Placement = pl
c_single_1A.Points = points
c_single_1A.FilletRadius.Value = 30.0
c_single_1A.PathType = "Wire"

# c_single_2A
points = [Vector (0.0, 0.0, 0.0), Vector (0.572127401828766, 56.03865051269531, 0.0)]
c_single_2A = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(0,0,0), (0,0,0,1)]
pl.Base = p[0]
pl.Rotation = p[1]
c_single_2A.Placement = pl
c_single_2A.Points = points
c_single_2A.FilletRadius.Value = 30.0
c_single_2A.PathType = "Wire"

# c_single_3A
points = [Vector (-13.32368988180103, -0.5522089689269478, 0.0), Vector (-14.713936299085617, 28.019325256347656, 0.0), Vector (-29.427872598171234, 56.03865051269531, 0.0)]
c_single_3A = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(30,0,0), (0,0,0,1)]
pl.Base = p[0]
pl.Rotation = p[1]
c_single_3A.Placement = pl
c_single_3A.Points = points
c_single_3A.FilletRadius.Value = 30.0
c_single_3A.PathType = "Wire"

# c_single_1B
points = [Vector (-0.140807194616425, 23.72398472306645, 0.0), Vector (-9.872132214007662, 46.46520478270554, 0.0), Vector (-42.80100497191738, 70.26594642730674, 0.0), Vector (-30.0, 100.0, 0.0)]
c_single_1B = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(0,600,0), (0,0,0,1)]
pl.Base = p[0]
pl.Rotation = p[1]
c_single_1B.Placement = pl
c_single_1B.Points = points
c_single_1B.FilletRadius.Value = 30.0
c_single_1B.BoundarySegmentStart.Value = 10.0
c_single_1B.BoundarySegmentEnd.Value = 10.0
c_single_1B.PathType = "BSpline_P"

# c_single_2B
points = [Vector (0.0, 0.0, 0.0), Vector (21.43809557804351, 39.0432596414048, 0.0), Vector (94.02518949323044, 111.21649430147806, 0.0)]
c_single_2B = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(60,700,0), (0,0,0,1)]
pl.Base = p[0]
pl.Rotation = p[1]
c_single_2B.Placement = pl
c_single_2B.Points = points
c_single_2B.FilletRadius.Value = 30.0
c_single_2B.BoundarySegmentStart.Value = 10.0
c_single_2B.BoundarySegmentEnd.Value = 10.0
c_single_2B.PathType = "Wire"

# c_single_3B
points = [Vector (0.0, 0.0, 0.0), Vector (38.33040453854406, 13.344448369664633, 0.0), Vector (78.96268824053735, 70.76819619040941, 0.0)]
c_single_3B = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
p = [(60,700,0), (0,0,0,1)]
pl.Base = p[0]
pl.Rotation = p[1]
c_single_3B.Placement = pl
c_single_3B.Points = points
c_single_3B.FilletRadius.Value = 30.0
c_single_3B.BoundarySegmentStart.Value = 10.0
c_single_3B.BoundarySegmentEnd.Value = 10.0
c_single_3B.PathType = "Wire"

skeleton_wires = [c1_base, c2_base, c3_base, cx3_baseA, cx3_baseB, cond_b1, cond_b2, cond_b3, c_single_1A, c_single_1B, c_single_2A, c_single_2B, c_single_3A, c_single_3B]

# Make skeleton group and add above wires
group_skel = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Group")
group_skel.Label = "Skeleton"
group_skel.addObjects(skeleton_wires)
App.ActiveDocument.recompute()


# Make support lines
sup1 = freecad.cables.cableSupport.makeSupportLine(FreeCAD.Vector (0.0, 200.0, 0.0))
sup1.Label = "sup1"
sup2 = freecad.cables.cableSupport.makeSupportLine(FreeCAD.Vector (0.0, 600.0, 0.0))
sup2.Label = "sup2"
sup3 = freecad.cables.cableSupport.makeSupportLine(FreeCAD.Vector (200.0, 400.0, 0.0))
sup3.Label = "sup3"
sup3.Placement.Rotation = App.Rotation(App.Vector(0,0,1), 90)
sup4 = freecad.cables.cableSupport.makeSupportLine(FreeCAD.Vector (0.5, 56.0, 0.0))
sup4.Label = "sup4"
sup5 = freecad.cables.cableSupport.makeSupportLine(FreeCAD.Vector (-0.15, 623.7, 0.0))
sup5.Label = "sup5"
sup6 = freecad.cables.cableSupport.makeSupportLine(FreeCAD.Vector (60.0, 700.0, 0.0))
sup6.Label = "sup6"
sup6.Placement.Rotation = App.Rotation(App.Vector(0,0,1), 90)

sup = [sup1, sup2, sup3, sup4, sup5, sup6]

group_sup = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Group")
group_sup.Label = "Support"
group_sup.addObjects(sup)
App.ActiveDocument.recompute()

# Attach base wires to support lines
freecad.cables.wireutils.assignPointAttachment([(c1_base, 'Vertex1'), (sup1, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(c2_base, 'Vertex1'), (sup2, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(c3_base, 'Vertex2'), (sup3, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(cond_b1, 'Vertex1'), (sup4, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(cond_b1, 'Vertex2'), (sup1, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(cond_b2, 'Vertex1'), (sup2, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(cond_b2, 'Vertex2'), (sup5, 'Vertex2')])

freecad.cables.wireutils.assignPointAttachment([(c_single_1A, 'Vertex4'), (sup4, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(c_single_2A, 'Vertex2'), (sup4, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(c_single_3A, 'Vertex4'), (sup4, 'Vertex2')])

freecad.cables.wireutils.assignPointAttachment([(c_single_1B, 'Vertex1'), (sup5, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(cond_b3, 'Vertex2'), (sup6, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(c_single_2B, 'Vertex1'), (sup6, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(c_single_3B, 'Vertex1'), (sup6, 'Vertex2')])

freecad.cables.wireutils.assignPointAttachment([(cx3_baseA, 'Vertex4'), (sup1, 'Vertex2')])
freecad.cables.wireutils.assignPointAttachment([(cx3_baseB, 'Vertex1'), (sup3, 'Vertex2')])

App.ActiveDocument.recompute()

# Make ducts (cable conduits)
duct1 = freecad.cables.archCableConduit.makeCableConduit(selectlist=[c1_base])
duct1.Diameter.Value = 20.0
duct1.WallThickness.Value = 0.5
duct1.Label = "duct1"

duct2 = freecad.cables.archCableConduit.makeCableConduit(selectlist=[c2_base])
duct2.Diameter.Value = 20.0
duct2.WallThickness.Value = 0.5
duct2.Label = "duct2"

duct3 = freecad.cables.archCableConduit.makeCableConduit(selectlist=[c3_base])
duct3.Diameter.Value = 20.0
duct3.WallThickness.Value = 0.5
duct3.Label = "duct3"

ducts = [duct1, duct2, duct3]

group_ducts = App.ActiveDocument.addObject("App::DocumentObjectGroup", "Group")
group_ducts.Label = "Ducts"
group_ducts.addObjects(ducts)
App.ActiveDocument.recompute()

# Make cable conduits
black_cond_main = freecad.cables.archCableConduit.makeCableConduit(selectlist=[cond_b1, duct1, duct2, cond_b2])
black_cond_main.Gauge = 50.0
black_cond_main.Base.ConnectionOffsetAngle = '270 deg'
black_cond_main.Base.ConnectionOffsetDist.Value = 3.01      # Note: value 3.0 gives very short edge leading to an error
                                                            # Changing Ratio from 1.6 to e.g. 1.59 helps as well
black_cond_main.Base.MinimumFilletRadius.Value = 10.0
black_cond_main.Label = "black_cond_main"
App.ActiveDocument.recompute()

black_cond_inner = freecad.cables.archCableConduit.makeCableConduit(selectlist=[black_cond_main, cond_b3])
black_cond_inner.Gauge = 30.0
black_cond_inner.Base.MinimumFilletRadius.Value = 10.0
black_cond_inner.Label = "black_cond_inner"
App.ActiveDocument.recompute()

#freecad.cables.cableMaterial.makeCableMaterials()
#FreeCAD.ActiveDocument.recompute()
mat_black = App.ActiveDocument.findObjects(Label="InsulBlack$")[0]
black_cond_main.Material = mat_black
black_cond_inner.Material = mat_black

# Make cables single-wire
cable_brown = freecad.cables.archCable.makeCable(selectlist=[c_single_1A, black_cond_main, c_single_1B])
cable_brown.Label = "cable_brown"
cable_green = freecad.cables.archCable.makeCable(selectlist=[c_single_2A, black_cond_main, cond_b3, c_single_2B])
cable_green.Label = "cable_green"
cable_red = freecad.cables.archCable.makeCable(selectlist=[c_single_3A, black_cond_main, cond_b3, c_single_3B])
cable_red.Label = "cable_red"
App.ActiveDocument.recompute()

mmat_red = App.ActiveDocument.findObjects(Label="cableMultiMat1wRed$")[0]
mmat_green = App.ActiveDocument.findObjects(Label="cableMultiMat1wGreen$")[0]
mmat_brown = App.ActiveDocument.findObjects(Label="cableMultiMat1wBrown$")[0]
cable_red.Material = mmat_red
cable_green.Material = mmat_green
cable_brown.Material = mmat_brown
App.ActiveDocument.recompute()

# Make cable 3-wire
profile = freecad.cables.cableProfile.makeCableProfile([2, 'YDY', 'R', '750V', 1.45, 0.7, 0.1], 3, 1.5)
App.ActiveDocument.recompute()
cable_x3 = freecad.cables.archCable.makeCable(selectlist=[cx3_baseA, duct1, duct3, cx3_baseB, profile])
cable_x3.Base.ConnectionOffsetAngle = '90 deg'
cable_x3.Base.ConnectionOffsetDist.Value = 4.0
App.ActiveDocument.recompute()
multimat_3w = App.ActiveDocument.findObjects(Label="cableMultiMat3w$")[0]
cable_x3.Material = multimat_3w
cable_x3.ShowSubLines = False
cable_x3.Label = "cable_x3"
App.ActiveDocument.recompute()

group_sup.ViewObject.hide()

black_cond_inner.SubConduits = [cable_green, cable_red]
black_cond_main.SubConduits = [black_cond_inner, cable_brown]
App.ActiveDocument.recompute()
black_cond_inner.MergeSubConduits = True
App.ActiveDocument.recompute()
black_cond_main.MergeSubConduits = True
App.ActiveDocument.recompute()


