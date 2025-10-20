'''
with open("example1.py", 'r') as f:
  code=f.read()

exec(code)
'''

import freecad.cables
import freecad.cables.wireFlex
import freecad.cables.cableProfile
import freecad.cables.archCable
import freecad.cables.cableMaterial


docname = "example1a"
App = FreeCAD
doc = App.newDocument(docname)
doc.FileName = docname + ".FCStd"
#doc = App.ActiveDocument
Vector = App.Vector

points = [Vector (0.0, 0.0, 0.0), Vector (50.0, 0.0, 0.0), Vector (75.0, 0.0, -15.0), Vector (100.0, -30.0, -30.0)]
w1 = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
w1.FilletRadius = 30.0
w1.Placement.Matrix.A = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -20.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
p1 = freecad.cables.cableProfile.makeCableProfile([1, 'YDYp', 'F', '750V', 1.45, 0.7, 0.1], 3, 1.5)
doc.recompute()
c1 = freecad.cables.archCable.makeCable(selectlist=[w1, p1])
doc.recompute()

c1.SubWires[3].Points = [Vector (0.0, 0.0, 0.0), Vector (2.9880715233359814, -3.5856858280031814, -1.7928429140015947), Vector (10.707472273665346, -8.313418731935748, -4.090873592470732), Vector (29.058563508602006, -4.420870352933726, -7.171371656006361)]
c1.SubWires[4].Points = [Vector (0.0, 0.0, 0.0), Vector (2.9880715233359845, -3.58568582800318, -1.792842914001592), Vector (11.952286093343943, -14.342743312012715, -7.171371656006368)]
c1.SubWires[5].Points = [Vector (0.0, 0.0, 0.0), Vector (2.9880715233359814, -3.5856858280031814, -1.7928429140015947), Vector (3.8249568182190927, -8.964214570007954, -4.6086808508886214), Vector (-6.723929981402662, -19.342743312012736, -5.373569614316356)]
doc.recompute()

c1.SubWires[3].PathType = 'BSpline_P'
c1.SubWires[5].PathType = 'BSpline_P'
doc.recompute()

c1.Placement.Matrix.A = (1.0, 0.0, 0.0, 24.1, 0.0, 1.0, 0.0, 29.5, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
doc.recompute()

points = [Vector (0.0, 0.0, 0.0), Vector (50.0, 0.0, 0.0), Vector (75.0, 0.0, 15.0), Vector (100.0, 30.0, 30.0)]
w2 = freecad.cables.wireFlex.make_wireflex_from_vectors(points)
w2.FilletRadius = 30.0
w2.Placement.Matrix.A = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 74.5, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
p2 = freecad.cables.cableProfile.makeCableProfile([2, 'YDY', 'R', '750V', 1.45, 0.7, 0.1], 5, 4.0)
doc.recompute()
c2 = freecad.cables.archCable.makeCable(selectlist=[w2, p2])
doc.recompute()
c2.SubWires[5].Points = [Vector (0.0, 0.0, 0.0), Vector (2.9880715233359822, 3.5856858280031823, 1.7928429140015911), Vector (-2.5298211916600337, 8.964214570007947, 9.482107285003977), Vector (11.952286093343943, 14.342743312012722, 27.171371656006365)]
c2.SubWires[5].FilletRadius = 4.0

freecad.cables.cableMaterial.makeCableMaterials()
c1.Material = doc.getObjectsByLabel('cableMultiMat3w')[0]
c2.Material = doc.getObjectsByLabel('cableMultiMat5w')[0]
doc.recompute()
doc.save()
#App.closeDocument(docname)
