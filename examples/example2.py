'''
with open("example2.py", 'r') as f:
    code=f.read()

exec(code)
'''

import Draft
import Arch
import freecad.cables
import freecad.cables.wireFlex
import freecad.cables.cableProfile
import freecad.cables.archCable
import freecad.cables.cableMaterial
import freecad.cables.archCableBox
import freecad.cables.archCableLightPoint
import freecad.cables.cableSupport
import freecad.cables.archCableConnector


docname = "example2a"
App = FreeCAD
doc = App.newDocument(docname)
doc.FileName = docname + ".FCStd"
#doc = App.ActiveDocument
Vector = App.Vector

w1 = Draft.makeWire([Vector (0.0, 0.0, 0.0), Vector (0.0, 5000.0, 0.0), Vector (3000.0, 5000.0, 0.0)])
w1.Placement.Matrix.A = (1.0, 0.0, 0.0, -1000.0, 0.0, 1.0, 0.0, -4000.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
wall = Arch.makeWall(w1)
wall.Height = 2600.0
wall.Align = "Right"
wall.ViewObject.Transparency = 80

box1 = freecad.cables.archCableBox.makeCableBox()
box1.Placement.Matrix.A = (0.0, 0.0, 1.0, -1000.0, 1.0, 0.0, 0.0, -1500.0, 0.0, 1.0, 0.0, 1200.0, 0.0, 0.0, 0.0, 1.0)
box1.Label = "BoxSW1"
box2 = freecad.cables.archCableBox.makeCableBox()
box2.Placement.Matrix.A = (1.0, 0.0, 0.0, 246.3, 0.0, 0.0, -1.0, 1000.0, 0.0, 1.0, 0.0, 1200.0, 0.0, 0.0, 0.0, 1.0)
box2.Label = "BoxSW2"
doc.recompute()

lp = freecad.cables.archCableLightPoint.makeCableLightPoint()
lp.Placement.Matrix.A = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2600.0, 0.0, 0.0, 0.0, 1.0)


support_lines = []
support_matrix = [
    (0.0, 0.0, 1.0, -1020.0, 1.0, 0.0, 0.0, -1500.0, 0.0, 1.0, 0.0, 1300.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, -1020.0, 1.0, 0.0, 0.0, -1500.0, 0.0, 1.0, 0.0, 2200.0, 0.0, 0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, 246.3, 0.0, 0.0, -1.0, 1020.0, 0.0, 1.0, 0.0, 1450.0, 0.0, 0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, -1020.0, 0.0, 1.0, 0.0, 1020.0, 0.0, 0.0, 1.0, 2200.0, 0.0, 0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, -1000.0, 0.0, 1.0, 0.0, -1526.9891357421875, 0.0, 0.0, 1.0, 3000.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, -1500.0, 0.0, 1.0, 0.0, 2600.0, 0.0, 0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, -1020.0, 0.0, 1.0, 0.0, -3000.0, 0.0, 0.0, 1.0, 2200.0, 0.0, 0.0, 0.0, 1.0) ]
points = [
    [Vector (-15.0, 0.0, 0.0), Vector (15.0, 0.0, 0.0)],
    [Vector (-15.0, 0.0, 0.0), Vector (15.0, 0.0, 0.0)],
    [Vector (-15.0, -170.0, 0.0), Vector (15.0, -170.0, 0.0)],
    [Vector (-30.0, 0.0, 0.0), Vector (30.0, 0.0, 0.0)],
    [Vector (-30.0, 0.0, 0.0), Vector (30.0, 0.0, 0.0)],
    [Vector (-30.0, 0.0, 0.0), Vector (30.0, 0.0, 0.0)],
    [Vector (-30.0, 0.0, 0.0), Vector (30.0, 0.0, 0.0)] ]
att_supp = [box1, box1, box2, w1, None, box1, None]
for i in range(7):
    s = freecad.cables.cableSupport.makeSupportLine()
    s.Placement.Matrix.A = support_matrix[i]
    s.Points = points[i]
    if att_supp[i] is not None:
        freecad.cables.cableutils.attach_in_place([s, att_supp[i]])
    support_lines.append(s)

spoint = freecad.cables.cableSupport.makeSupportPoint()
spoint.Placement.Matrix.A = (1.0, 0.0, 0.0, 246.3, 0.0, 0, -1.0, 1020.0, 0.0, 1.0, 0, 2200.0, 0.0, 0.0, 0.0, 1.0)
freecad.cables.cableutils.attach_in_place([spoint, box2])
doc.recompute()

supports = doc.addObject("App::DocumentObjectGroup", "Supports")
supports.addObjects(support_lines)
supports.addObjects([spoint])
doc.recompute()

profile = freecad.cables.cableProfile.makeCableProfile([1, 'YDYp', 'F', '750V', 1.45, 0.7, 0.1], 3, 1.5)


c1_base_points = [Vector (0.0, 0.0, 0.0), Vector (0.0, -15.353569087401638, 4.7362429284994505), Vector (11.0, -12.5864762445226, 33.11433649766491), Vector (21.333333333333258, 15.0, 100.00000000000023), Vector (21.333333333333258, 15.0, 1000.0), Vector (21.333333333333258, -1470.0, 1000.0)]
c1_base = freecad.cables.wireFlex.make_wireflex_from_vectors(c1_base_points)
doc.recompute()

supplines1 = doc.getObjectsByLabel('BoxSW1_SuppLines001')[0]
freecad.cables.wireutils.assignPointAttachment([(c1_base, 'Vertex1'), (supplines1, 'Vertex16')])
slines = support_lines
c1_base.Vrtxs_mid = [(slines[0], ('Vertex1',)), (slines[1], ('Vertex1',))]
c1_base.Vrtxs_mid_idx = [4, 5]
c1_base.Vrtx_end = (slines[6], ['Vertex2'])
doc.recompute()


c2_base_points = [Vector (0.0, 0.0, 0.0), Vector (21.333333333333258, 0.0, 70.00000000000023), Vector (21.333333333333258, 0.0, 970.0), Vector (22.0, 0.0, 1368.5), Vector (1041.3333333333333, 0.0, 1370.0), Vector (1041.3333333333333, 1500.0, 1372.0), Vector (1041.3333333333333, 1500.0, 1363.0)]
c2_base = freecad.cables.wireFlex.make_wireflex_from_vectors(c2_base_points)
doc.recompute()

supplines3 = doc.getObjectsByLabel('CableLightPoint_SuppLines001')[0]
freecad.cables.wireutils.assignPointAttachment([(c2_base, 'Vertex1'), (supplines1, 'Vertex1')])
c2_base.Vrtxs_mid = [(slines[0], ('Vertex2',)), (slines[1], ('Vertex2',)), (slines[5], ('Vertex2',)), (supplines3, ('Vertex1',))]
c2_base.Vrtxs_mid_idx = [2, 3, 5, 6]
c2_base.Vrtx_end = (supplines3, ['Vertex6'])
doc.recompute()


c3_base_points = [Vector (0.0, 0.0, 0.0), Vector (0.0, 15.769507206992557, 6.465385711417866), Vector (11.0, 13.56293353379624, 34.081), Vector (21.333333333333258, -15.0, 100.0), Vector (21.333333333333258, -15.0, 1000.0), Vector (21.333333333333258, 2490.0, 1000.0), Vector (1287.6333333333332, 2490.0, 1000.0), Vector (1287.6333333333332, 2490.0, 80.0), Vector (1287.6333333333332, 2511.333333333333, 30.0)]
c3_base = freecad.cables.wireFlex.make_wireflex_from_vectors(c3_base_points)
doc.recompute()

supplines2 = doc.getObjectsByLabel('BoxSW2_SuppLines001')[0]
freecad.cables.wireutils.assignPointAttachment([(c3_base, 'Vertex1'), (supplines1, 'Vertex6')])
c3_base.Vrtxs_mid = [(slines[0], ('Vertex3',)), (slines[1], ('Vertex3',)), (slines[3], ('Vertex2',)),  (spoint, ('Vertex1',)), (slines[2], ('Vertex2',))]
c3_base.Vrtxs_mid_idx = [4, 5, 6, 7, 8]
c3_base.Vrtx_end = (supplines2, ['Vertex1'])
doc.recompute()

c1_base.FilletRadius = 10.0
c2_base.FilletRadius = 20.0
c3_base.FilletRadius = 10.0
doc.recompute()


c1 = freecad.cables.archCable.makeCable(selectlist=[c1_base, profile])
c2 = freecad.cables.archCable.makeCable(selectlist=[c2_base, profile])
c3 = freecad.cables.archCable.makeCable(selectlist=[c3_base, profile])
c1.Label = 'Cable_INSW1'
c2.Label = 'Cable_SW1LP1'
c3.Label = 'Cable_SW1SW2'
c3.CableRotation=180.0
doc.recompute()

preset_x2 = ['Customized', ['NumberOfHoles', 'Height', 'HoleSize', 'Thickness'], [2, '5.0 mm', 1.5, '1.0 mm']]
preset_x3 = ['TerminalStrip_1.5mm2_x3', [], []]
presets = [preset_x2, preset_x2, preset_x2, preset_x3, preset_x3, preset_x3, preset_x2, preset_x2, preset_x2]
placements = [
    (0.0, 0.0, 1.0, -1000.0, 0.0, -1.0, 0.0, -1490.0, 1.0, 0.0, 0.0, 1180.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 1.02, -1000.0, 0.0, -1.0, 0.0, -1515.0, 1.0, 0.0, 0.0, 1200.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, -1000.0, 0.0, -1.0, 0.0, -1490.0, 1.0, 0.0, 0.0, 1200.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, -1030.0, 1.0, 0.0, 0.0, -1480.0, 0.0, 1.0, 0.0, 1210.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, -1030.0, 1.0, 0.0, 0.0, -1515.0, 0.0, 1.0, 0.0, 1215.0, 0.0, 0.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, -1030.0, 1.0, 0.0, 0.0, -1500.0, 0.0, 1.0, 0.0, 1210.0, 0.0, 0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, 226.3, 0.0, 0.0, -1.0, 1000.0, 0.0, 1.0, 0.0, 1190.0, 0.0, 0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, 246.3, 0.0, 0.0, -1.0, 1000.0, 0.0, 1.0, 0.0, 1210.0, 0.0, 0.0, 0.0, 1.0),
    (1.0, 0.0, 0.0, 266.3, 0.0, 0.0, -1.0, 1000.0, 0.0, 1.0, 0.0, 1190.0, 0.0, 0.0, 0.0, 1.0) ]
att_suppc = [box1, box1, box1, box1, box1, box1, box2, box2, box2]
clabels = ['CableConnectorL1A', 'CableConnectorINL1', 'CableConnectorL1B', 'CableConnectorL1', 'CableConnectorPE', 'CableConnectorN', 'CableConnectorL1ASW2', 'CableConnectorL1BSW2', 'CableConnectorL1SW2']

conns = []
for i in range(9):
    con = freecad.cables.archCableConnector.makeCableConnector()
    con.Proxy.setPreset(con, *presets[i])
    con.Placement.Matrix.A = placements[i]
    con.Label = clabels[i]
    conns.append(con)
    if att_suppc[i] is not None:
        freecad.cables.cableutils.attach_in_place([con, att_suppc[i]])

connectors = doc.addObject("App::DocumentObjectGroup", "Connectors")
connectors.addObjects(conns)
doc.recompute()

subw_pts = [
    [Vector (0.0, 0.0, 0.0), Vector (0.0, 4.777838252816869, -1.4738594335688393), Vector (1.9500000000000455, 12.014428414850045, -11.25), Vector (14.950000000000045, 18.509618943233363, -7.5), Vector (37.2833333333333, 15.0, 1.2978845608031406), Vector (46.2833333333333, 15.0, 1.2978845608031406)],
    [Vector (0.0, 0.0, 0.0), Vector (0.0, 4.777838252816869, -1.4738594335688393), Vector (2.0, 21.5, 0.0), Vector (4.3333333333332575, 27.404230878394173, 10.000000000000227), Vector (13.333333333333258, 27.404230878394173, 10.000000000000227)],
    [Vector (0.0, 0.0, 0.0), Vector (0.0, 4.777838252816869, -1.4738594335688393), Vector (-0.9500000000000455, 12.014428414850045, 11.25), Vector (1.383333333333212, 12.404230878394173, 15.000000000000227), Vector (10.383333333333212, 12.404230878394173, 15.000000000000227)] ]
terminals = ['CableConnectorINL1_Term001', 'CableConnectorN_Term001', 'CableConnectorPE_Term001']
for i in range(3):
    c1.SubWires[i].Points = subw_pts[i]

doc.recompute()
for i in range(3):
    freecad.cables.cableutils.attach_wire_to_terminal([(c1.SubWires[i], ''), (doc.getObjectsByLabel(terminals[i])[0], 'Vertex2')], 'end')

doc.recompute()

subw_pts = [
    [Vector (0.0, 0.0, 0.0), Vector (-1.4576205431927425, 0.0, -4.782817407351288), Vector (2.0000000000002274, 8.299999999999955, -12.014428414850272), Vector (22.000000000000227, 4.5499999999999545, -18.50961894323359), Vector (13.333333333333258, 14.454230878394128, -19.999999999999773), Vector (4.3333333333332575, 14.454230878394128, -19.999999999999773)],
    [Vector (0.0, 0.0, 0.0), Vector (-1.4576205431927425, 0.0, -4.782817407351288), Vector (2.0000000000002274, 0.0, -9.000000000000227), Vector (4.3333333333332575, 0.0, -19.999999999999773), Vector (13.333333333333258, 0.0, -19.999999999999773)],
    [Vector (0.0, 0.0, 0.0), Vector (-1.4576205431927425, 0.0, -4.782817407351288), Vector (2.0000000000002274, -2.6749999999999545, -10.50721420742525), Vector (4.3333333333332575, -9.454230878394128, -14.999999999999773), Vector (13.333333333333258, -9.454230878394128, -14.999999999999773)] ]
terminals = ['CableConnectorL1_Term001',  'CableConnectorN_Term001', 'CableConnectorPE_Term001']
term_vertices = ['Vertex1', 'Vertex4', 'Vertex6']
for i in range(3):
    c2.SubWires[i].Points = subw_pts[i]

doc.recompute()
for i in range(3):
    freecad.cables.cableutils.attach_wire_to_terminal([(c2.SubWires[i], ''), (doc.getObjectsByLabel(terminals[i])[0], term_vertices[i])], 'end')

doc.recompute()

subw_pts = [
    [Vector (0.0, 0.0, 0.0), Vector (0.0, -4.626271083825734, -1.896738215716093), Vector (-0.9500000000000455, -12.014428414850045, -11.25), Vector (9.049999999999955, -24.0, -12.990381056766637), Vector (31.383333333333212, -20.0, -18.70211543919686), Vector (40.38333333333321, -20.0, -18.70211543919686)],
    [Vector (0.0, 0.0, 0.0), Vector (0.0, -4.626271083825734, -1.896738215716093), Vector (2.0, -9.0, 0.0), Vector (12.0, -16.5, 0.0), Vector (34.33333333333326, -20.0, -1.2978845608026859), Vector (43.33333333333326, -20.0, -1.2978845608026859)],
    [Vector (0.0, 0.0, 0.0), Vector (0.0, -4.626271083825734, -1.896738215716093), Vector (4.9500000000000455, -10.507214207425022, 5.625), Vector (7.283333333333303, -7.4042308783941735, 10.000000000000227), Vector (16.283333333333303, -7.4042308783941735, 10.000000000000227)],
    [Vector (0.0, 0.0, 0.0), Vector (-2.853915639453402e-14, 1.9621934252388882, -4.598890840403725), Vector (12.014502398234171, -19.464726353658307, -37.84997896454615), Vector (20.330986978874506, -31.769871965361972, -38.9062564829992), Vector (20.330986978874506, -40.76987196536197, -38.9062564829992)],
    [Vector (0.0, 0.0, 0.0), Vector (-2.853915639453402e-14, 1.9621934252388882, -4.598890840403725), Vector (4.1458190225536726e-14, -8.95089200946842, -50.04007897912638), Vector (-18.702115439197087, -34.33333333333303, -40.00000000000023), Vector (-18.702115439197087, -43.33333333333303, -40.00000000000023)],
    [Vector (0.0, 0.0, 0.0), Vector (-2.853915639453402e-14, 1.9621934252388882, -4.598890840403725), Vector (-1.753015167683526, -3.774027853952487, -8.028168315704882), Vector (-3.5060303353670976, -9.613533028613746, -11.502897992574526), Vector (-0.33098697887439243, -36.89679470130409, -21.093743517001258), Vector (-0.33098697887439243, -45.89679470130409, -21.093743517001258)] ]
terminals = ['CableConnectorL1A_Term001',  'CableConnectorL1B_Term001', 'CableConnectorL1_Term001']
term_vertices = ['Vertex4', 'Vertex2', 'Vertex6']
for i in range(3):
    c3.SubWires[i].Points = subw_pts[i]

doc.recompute()
for i in range(3):
    freecad.cables.cableutils.attach_wire_to_terminal([(c3.SubWires[i], ''), (doc.getObjectsByLabel(terminals[i])[0], term_vertices[i])], 'end')



subw_pts = [
    [Vector (0.0, 0.0, 0.0), Vector (-2.853915639453402e-14, 1.9621934252388882, -4.598890840403725), Vector (12.014502398234171, -19.464726353658307, -37.84997896454615), Vector (20.330986978874506, -31.769871965361972, -38.9062564829992), Vector (20.330986978874506, -40.76987196536197, -38.9062564829992)],
    [Vector (0.0, 0.0, 0.0), Vector (-2.853915639453402e-14, 1.9621934252388882, -4.598890840403725), Vector (4.1458190225536726e-14, -8.95089200946842, -50.04007897912638), Vector (-18.702115439197087, -34.33333333333303, -40.00000000000023), Vector (-18.702115439197087, -43.33333333333303, -40.00000000000023)],
    [Vector (0.0, 0.0, 0.0), Vector (-2.853915639453402e-14, 1.9621934252388882, -4.598890840403725), Vector (-1.753015167683526, -3.774027853952487, -8.028168315704882), Vector (-3.5060303353670976, -9.613533028613746, -11.502897992574526), Vector (-0.33098697887439243, -36.89679470130409, -21.093743517001258), Vector (-0.33098697887439243, -45.89679470130409, -21.093743517001258)] ]
terminals = ['CableConnectorL1SW2_Term001',  'CableConnectorL1ASW2_Term001', 'CableConnectorL1BSW2_Term001']
term_vertices = ['Vertex2', 'Vertex2', 'Vertex2']
for i in range(3,6):
    c3.SubWires[i].Points = subw_pts[i-3]

doc.recompute()
for i in range(3,6):
    freecad.cables.cableutils.attach_wire_to_terminal([(c3.SubWires[i], ''), (doc.getObjectsByLabel(terminals[i-3])[0], term_vertices[i-3])], 'end')

for c in [c1, c2, c3]:
    c.SubWiresFilletRadius = 4.0

doc.recompute()

freecad.cables.cableMaterial.makeCableMaterials()
mat_3w = doc.getObjectsByLabel('cableMultiMat3w')[0]
c1.Material = mat_3w
c2.Material = mat_3w
doc.recompute()
multi_names3 = [('J', 'InsulJacket'), ('L1A', 'InsulBlack'), ('L1B', 'InsulBlack'), ('L1', 'InsulBrown'), ('CU', 'Cu')]
multi_label = 'cableMultiMat3wB'
multi = Arch.makeMultiMaterial()
lmat = []
lnames = []
for item in multi_names3:
    mat = doc.getObjectsByLabel(item[1])[0]
    lmat.append(mat)

for item in multi_names3:
    lnames.append(item[0])

multi.Materials = lmat
multi.Names = lnames
multi.Label = multi_label
c3.SubColors = ['J:0', 'L1A:1', 'L1B:2', 'L1:3', 'CU:-1']
c3.Material = multi
doc.recompute()



doc.addObject("App::TextDocument","Text document").Label="Info"
info = doc.getObjectsByLabel("Info")[0]
info.Text = """
This is demo example of Cables Workbench

To see Wire Flex in action you can zoom out to see the whole scene and change BoxSW1 Placement.Positon.y e.g. to -100cm

To enable/disable cable sublines visibility with one click you can change the cable property:
ShowSubLines = True/False

"""

doc.recompute()
doc.save()
#App.closeDocument(docname)
