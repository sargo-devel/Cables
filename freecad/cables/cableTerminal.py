"""CableTerminal
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
import Part
from freecad.cables import cableutils
from freecad.cables import iconPath
from freecad.cables import QT_TRANSLATE_NOOP


CLASS_CABLETERMINAL_ICON = os.path.join(iconPath, "classCableTerminal.svg")
TermPointColor = (0, 0, 255)
TermLineColor = (170, 0, 0)


class CableTerminal:
    """The ExtSuppLines object
    """
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "Terminal"
        self.setProperties(obj)

    def setProperties(self, obj):
        pl = obj.PropertiesList
        if "NumberOfConnections" not in pl:
            obj.addProperty("App::PropertyInteger", "NumberOfConnections",
                            "Terminal",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The number of connection " +
                                "segments in a single node"))
        if "Length" not in pl:
            obj.addProperty("App::PropertyLength", "Length",
                            "Terminal",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The length of the terminal"))
        if "Spacing" not in pl:
            obj.addProperty("App::PropertyLength", "Spacing",
                            "Terminal",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The spacing between " +
                                "connection segments"))
        if "ParentName" not in pl:
            obj.addProperty("App::PropertyString", "ParentName",
                            "Terminal",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The name of parent object"))
            obj.setPropertyStatus("ParentName", ["ReadOnly", "Hidden"])
        if "ConnectedWires" not in pl:
            obj.addProperty("App::PropertyStringList", "ConnectedWires",
                            "Net",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "List of names of " +
                                "connected wires with number of connection"))
            obj.setPropertyStatus("ConnectedWires", ["ReadOnly"])
        if "Offset" not in pl:
            obj.addProperty("App::PropertyPlacement", "Offset",
                            "Terminal",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The Terminal placement " +
                                "offset relative to parent placement. It is " +
                                "up to the parent to decide whether to use " +
                                "this parameter"))

    def onDocumentRestored(self, obj):
        self.setProperties(obj)

    def onChanged(self, obj, prop):
        # FreeCAD.Console.PrintMessage(obj.Label, f"onChanged: {prop}\n")
        if prop == "Offset":
            # set own placement relative to parent placement.
            self.findParent(obj)
            if obj.ParentName:
                parent = FreeCAD.ActiveDocument.getObject(obj.ParentName)
                pl = parent.Placement.multiply(obj.Offset)
                if pl != obj.Placement:
                    obj.Placement = pl

    def execute(self, obj):
        obj.Shape = self.makeTerminalLines(obj)
        # forcing to recalculate offset
        obj.Offset = obj.Offset
        # forcing to recalculate list of connected wires
        self.updateConnectedWires(obj)

    def makeTerminalLines(self, obj):
        # make terminal lines
        nr_con = obj.NumberOfConnections if obj.NumberOfConnections > 0 else 1
        x_dist = obj.Spacing
        z0 = 0
        y0 = 0
        y1 = obj.Length.Value/2.0
        y2 = -y1
        max_x_dist = x_dist*(nr_con-1)/2.0
        v_vectors = []
        h_vectors = []
        for nr in range(nr_con):
            x = -max_x_dist + nr*x_dist
            v0 = FreeCAD.Vector(x, y1, z0)
            v1 = FreeCAD.Vector(x, y2, z0)
            v2 = FreeCAD.Vector(x, y0, z0)
            v_vectors.append((v0, v1))
            h_vectors.append(v2)
        lines = []
        for v in v_vectors:
            lines.append(Part.LineSegment(v[0], v[1]).toShape())
        if nr_con > 1:
            lines.append(Part.makePolygon(h_vectors))

        s = Part.Compound(lines)
        return s

    def setPropertiesReadOnly(self, obj):
        pl = obj.PropertiesList
        proplist = ["Placement", "NumberOfConnections", "Length", "Spacing"]
        for prop in proplist:
            if (prop in pl) and \
               ("ReadOnly" not in obj.getPropertyStatus(prop)):
                obj.setPropertyStatus(prop, "ReadOnly")

    def setPropertiesReadWrite(self, obj):
        pl = obj.PropertiesList
        proplist = ["Placement", "NumberOfConnections", "Length", "Spacing"]
        FreeCAD.Console.PrintMessage("setPropertiesReadWrite\n")
        for prop in proplist:
            if (prop in pl) and \
               ("ReadOnly" in obj.getPropertyStatus(prop)):
                obj.setPropertyStatus(prop, "-ReadOnly")

    def findParent(self, obj):
        valid_parent_list = ["ArchCableConnector", "ArchElectricalDevice",
                             "ArchCableBox", "ArchCableLightPoint"]
        for p in obj.InList:
            if type(p.Proxy).__name__ in valid_parent_list:
                if p.Name != obj.ParentName:
                    obj.ParentName = p.Name
                return
        obj.ParentName = ""

    def updateConnectedWires(self, obj):
        conn_list = []
        for p in obj.InList:
            if type(p.Proxy).__name__ == "WireFlex":
                conn_list.append(p)
        conn_wires = []
        for wire in conn_list:
            vstr_lst = []
            if wire.Vrtx_start and wire.Vrtx_start[0] == obj:
                vstr_lst.append(wire.Vrtx_start[1][0])
            if wire.Vrtx_end and wire.Vrtx_end[0] == obj:
                vstr_lst.append(wire.Vrtx_end[1][0])
            for vstr in vstr_lst:
                vnr = int(vstr.strip('Vertx'))
                conn_nr = vnr//2 + vnr % 2
                conn_wires.append(f"{conn_nr}:{wire.Name}")
        conn_wires = sorted(set(conn_wires))

        # remove duplicate connections in a single pin
        occupied_lst = [int(c.split(":")[0]) for c in conn_wires]
        if occupied_lst:
            prev = occupied_lst[0]
            conn_wires_ok = [conn_wires[0]]
            conn_wires_bad = []
            for i, curr in enumerate(occupied_lst[1:]):
                if curr != prev:
                    conn_wires_ok.append(conn_wires[i+1])
                else:
                    conn_wires_bad.append(conn_wires[i+1])
                prev = curr
            if conn_wires_bad:
                blist = [FreeCAD.ActiveDocument.getObject(w.split(":")[1])
                         for w in conn_wires_bad] + [obj]
                cableutils.detach_wire_from_terminal(blist, verbose=True)
            conn_wires = conn_wires_ok

        if conn_wires != obj.ConnectedWires:
            obj.ConnectedWires = conn_wires


class ViewProviderCableTerminal:
    """A View Provider for the ExtSuppLines object
    """
    def __init__(self, vobj):
        self.Object = vobj.Object
        vobj.Proxy = self
        vobj.PointSize = 6
        vobj.LineWidth = 3
        vobj.PointColor = TermPointColor
        vobj.LineColor = TermLineColor

    def getIcon(self):
        return CLASS_CABLETERMINAL_ICON

    def claimChildren(self):
        children = []
        if hasattr(self, "Object"):
            for w in self.Object.ConnectedWires:
                wobj = FreeCAD.ActiveDocument.getObject(w.split(":")[1])
                if wobj is not None:
                    children.append(wobj)
        children = list(set(children))
        return children

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def attach(self, vobj):
        self.Object = vobj.Object
        return

    def updateData(self, obj, prop):
        return

    def getDisplayModes(self, obj):
        return []

#    def getDefaultDisplayMode(self):
#        return "Shaded"

    def onChanged(self, vobj, prop):
        return


def makeCableTerminal():
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                           "CableTerminal")
    CableTerminal(obj)
    if FreeCAD.GuiUp:
        ViewProviderCableTerminal(obj.ViewObject)
    obj.NumberOfConnections = 1
    obj.Length = 10.0
    obj.Spacing = 5.0
    return obj
