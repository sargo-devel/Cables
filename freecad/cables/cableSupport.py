"""cableSupport
"""

# ***************************************************************************
# *   Copyright 2025 SargoDevel <sargo-devel at o2 dot pl>                  *
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
from freecad.cables import translate
from freecad.cables import iconPath
from freecad.cables import QT_TRANSLATE_NOOP


CLASS_EXTSUPPLINES_ICON = os.path.join(iconPath, "classExtSuppLines.svg")
SuppPointColor = (255, 85, 0)
SuppLineColor = (255, 170, 127)


def makeSupportPoint(placement=None, name=None):
    """creates a support point
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No active document. Aborting") + "\n")
        return
    if placement:
        point = Draft.make_point(placement.Base)
    else:
        point = Draft.make_point(0.0, 0.0, 0.0)
    point.Label = name if name else translate("Cables", "SupportPoint")
    point.ViewObject.PointSize = 8
    point.ViewObject.PointColor = SuppPointColor
    Draft.autogroup(point)
    point.addExtension('Part::AttachExtensionPython')
    return point


def makeSupportLine(p1=None, p2=None, name=None):
    """creates a support line
    """
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No active document. Aborting") + "\n")
        return
    pl = FreeCAD.Placement()
    dist = 30.0
    if p1 and p2:
        pl.Base = (p1+p2)/2
    elif p1:
        center = p1
        p1 = center + FreeCAD.Vector(-dist, 0.0, 0.0)
        p2 = center + FreeCAD.Vector(dist, 0.0, 0.0)
        pl.Base = center
    else:
        p1 = FreeCAD.Vector(-dist, 0.0, 0.0)
        p2 = FreeCAD.Vector(dist, 0.0, 0.0)
        pl.Base = (p1+p2)/2
    line = Draft.make_wire([p1, p2], placement=pl, closed=False,
                           face=False, support=None)
    line.Label = name if name else translate("Cables", "SupportLine")
    line.Subdivisions = 1
    line.ViewObject.PointSize = 8
    line.ViewObject.PointColor = SuppPointColor
    line.ViewObject.LineColor = SuppLineColor
    Draft.autogroup(line)
    return line


class ExtSuppLines:
    """The ExtSuppLines object
    """
    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "SuppLines"
        self.setProperties(obj)
        obj.addExtension('Part::AttachExtensionPython')

    def setProperties(self, obj):
        pl = obj.PropertiesList
        if "Lines" not in pl:
            obj.addProperty("Part::PropertyPartShape", "Lines",
                            "SnapLines",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The shape containing " +
                                "support lines"))
        if "ParentElement" not in pl:
            obj.addProperty("App::PropertyLink", "ParentElement",
                            "SnapLines",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The parent element object"))
            obj.setPropertyStatus("ParentElement", ["ReadOnly", "Hidden"])

    def onChanged(self, obj, prop):
        # FreeCAD.Console.PrintMessage(obj.Label, f"onChanged: {prop}\n")
        return

    def execute(self, obj):
        # FreeCAD.Console.PrintMessage(obj.Label, "execute started\n")
        if hasattr(obj, "Lines") and obj.Lines:
            if not obj.Shape.isPartner(obj.Lines):
                obj.Shape = obj.Lines
        self.findParent(obj)
        if obj.AttachmentSupport and obj.MapMode == "Deactivated":
            obj.MapMode = "ObjectXY"

    def findParent(self, obj):
        valid_parent_list = ["ArchCableConnector", "ArchElectricalDevice",
                             "ArchCableBox", "ArchCableLightPoint"]
        try:
            p = obj.AttachmentSupport[0][0]
        except (TypeError, IndexError):
            p = None
        if p is not None and hasattr(p, "Proxy") and \
           type(p.Proxy).__name__ in valid_parent_list:
            if p != obj.ParentElement:
                obj.ParentElement = p
        return


class ViewProviderExtSuppLines:
    """A View Provider for the ExtSuppLines object
    """
    def __init__(self, vobj):
        vobj.Proxy = self
        vobj.PointSize = 4
        vobj.LineWidth = 1
        vobj.PointColor = SuppPointColor
        vobj.LineColor = SuppLineColor

    def getIcon(self):
        return CLASS_EXTSUPPLINES_ICON

    def attach(self, obj):
        return

    def updateData(self, fp, prop):
        return

    def getDisplayModes(self, obj):
        return []

#    def getDefaultDisplayMode(self):
#        return "Shaded"

    def onChanged(self, vobj, prop):
        pass
