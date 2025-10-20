'''
with open("example3.py", 'r') as f:
    code=f.read()

exec(code)
'''

import freecad.cables
import freecad.cables.wireFlex
import freecad.cables.cableProfile
import freecad.cables.archCable
import freecad.cables.cableMaterial
import freecad.cables.archCableBox
import freecad.cables.archCableLightPoint
import freecad.cables.cableSupport
import freecad.cables.archCableConnector


docname = "example3a"
App = FreeCAD
doc = App.newDocument(docname)
doc.FileName = docname + ".FCStd"
#doc = App.ActiveDocument
Vector = App.Vector

support_lines = []
support_matrix = [
    (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 50.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -50.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0) ]
points = [
    [Vector (-100.0, 0.0, 0.0), Vector (100.0, 0.0, 0.0)],
    [Vector (-100.0, 0.0, 0.0), Vector (100.0, 0.0, 0.0)] ]
for i in range(2):
    s = freecad.cables.cableSupport.makeSupportLine()
    s.Placement.Matrix.A = support_matrix[i]
    s.Points = points[i]
    s.Subdivisions = 10
    support_lines.append(s)

doc.recompute()

supports = doc.addObject("App::DocumentObjectGroup", "Supports")
supports.addObjects(support_lines)
doc.recompute()

prof_defs = [
    ([1, 'YDY', 'R', '750V', 1.45, 0.7, 0.1], 1, 1.5),
    ([2, 'YDY', 'R', '750V', 1.45, 0.7, 0.1], 2, 1.0),
    ([2, 'YDY', 'R', '750V', 1.45, 0.7, 0.1], 3, 2.5),
    ([2, 'YDY', 'R', '750V', 1.45, 0.7, 0.1], 4, 0.5),
    ([2, 'YDY', 'R', '750V', 1.45, 0.7, 0.1], 5, 6.0),
    ([1, 'YDYp', 'F', '750V', 1.45, 0.7, 0.1], 5, 1.5),
    ([1, 'YDYp', 'F', '750V', 1.45, 0.7, 0.1], 2, 0.5),
    ([1, 'YDYp', 'F', '750V', 1.45, 0.7, 0.1], 3, 2.5),
    ([3, 'UTP5e', 'R', 'LAN', 0.7, 0.3, 0.05], 8, 0.2)
    ]
plist = []
for prof in prof_defs:
    p = freecad.cables.cableProfile.makeCableProfile(*prof)
    plist.append(p)

supports = doc.addObject("App::DocumentObjectGroup", "Profiles")
supports.addObjects(plist)
doc.recompute()
slines = support_lines
blist = []
for i in range(10):
    w = freecad.cables.wireFlex.make_wireflex([(slines[0], f'Vertex{i+1}'), (slines[1], f'Vertex{i+1}')])
    blist.append(w)

doc.recompute()
clist = []
for el in zip(blist, plist):
    c = freecad.cables.archCable.makeCable(selectlist=[el[0], el[1]])
    c.ShowSubLines = False
    clist.append(c)

c = freecad.cables.archCable.makeCable(selectlist=[blist[9]])
clist.append(c)
doc.recompute()


freecad.cables.cableMaterial.makeCableMaterials()
mat_3w = doc.getObjectsByLabel('cableMultiMat3w')[0]
mat_5w = doc.getObjectsByLabel('cableMultiMat5w')[0]
mat_8w = doc.getObjectsByLabel('cableMultiMat8w')[0]
mlist = [mat_3w, mat_3w, mat_3w, mat_5w, mat_5w, mat_5w, mat_3w, mat_3w, mat_8w, mat_3w]
for m in zip(clist,mlist):
    m[0].Material = m[1]

doc.recompute()

doc.save()
#App.closeDocument(docname)
