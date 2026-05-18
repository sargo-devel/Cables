"""Layers Extended
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
import Draft
from draftobjects import layer
from draftviewproviders import view_layer
from draftutils import params
from freecad.cables import QT_TRANSLATE_NOOP

# Layer presets
layer_wireflex = {
    "obj": {
        "Label": "WireFlex lines"
    },
    "vobj": {
        "LineColor": (176, 176, 176),
        "LineWidth": 2.0,
        "OverrideLineColorChildren": True,
        "PointColor": (0, 102, 0),
        "PointSize": 8.0
    }
}

layer_supportlines = {
    "obj": {
        "Label": "Support Lines"
    },
    "vobj": {
        "LineColor": (255, 170, 127),
        "LineWidth": 2.0,
        "OverrideLineColorChildren": True,
        "PointColor": (255, 85, 0),
        "PointSize": 8.0
    }
}

layer_snaplines = {
    "obj": {
        "Label": "Snap Lines"
    },
    "vobj": {
        "LineColor": (255, 170, 127),
        "LineWidth": 1.0,
        "OverrideLineColorChildren": True,
        "PointColor": (255, 85, 0),
        "PointSize": 4.0
    }
}

layer_terminals = {
    "obj": {
        "Label": "Terminals"
    },
    "vobj": {
        "LineColor": (170, 0, 0),
        "LineWidth": 3.0,
        "OverrideLineColorChildren": True,
        "PointColor": (0, 0, 255),
        "PointSize": 6.0
    }
}

# Layer presets dict for AutoMemberType
layer_presets = {
    "None": None,
    "WireFlex": layer_wireflex,
    "SupportLines": layer_supportlines,
    "ExtSnapLines": layer_snaplines,
    "CableTerminal": layer_terminals
}


class LayerExtended(layer.Layer):
    """The Layer extended object.

    This class extends core Layer class with additional properties.
    """

    def __init__(self, obj):
        layer.Layer.__init__(self, obj)

    def set_properties(self, obj):
        layer.Layer.set_properties(self, obj)
        if "AutoMemberType" not in obj.PropertiesList:
            obj.addProperty("App::PropertyEnumeration", "AutoMemberType",
                            "Layer",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "Type of object which will " +
                                "be automatically assigned to this layer on " +
                                "layer recompute"))
            obj.AutoMemberType = list(layer_presets.keys())

    def onChanged(self, obj, prop):
        if "onChanged" in dir(layer.Layer):
            layer.Layer.onChanged(self, obj, prop)

        if prop != "Group":
            if prop == "AutoMemberType":
                preset = layer_presets.get(obj.AutoMemberType)
                if preset not in [None, "None"]:
                    self.set_parameters(obj, preset.get("obj"))
                new_members = self.get_new_members(obj)
                self.set_members(obj, new_members)
            return
        vobj = getattr(obj, "ViewObject", None)
        old_grp = getattr(self, "oldGroup", [])
        for child in obj.Group:
            if child in old_grp:
                continue
            if vobj is None:
                continue
            for prop in ("PointSize", "PointColor"):
                vobj.Proxy.change_view_properties(
                    vobj, prop, old_prop=None, targets=[child])

    def execute(self, obj):
        if "execute" in dir(layer.Layer):
            layer.Layer.execute(self, obj)
        if obj.AutoMemberType != "None":
            new_members = self.get_new_members(obj)
            if new_members:
                current_members = obj.Group
                self.set_members(obj, current_members + new_members)

    def set_members(self, obj, members):
        visibility = [m.ViewObject.Visibility for m in members]
        obj.Group = members
        self.set_members_visibility(members, visibility)

    def get_new_members(self, obj):
        new_members = []
        if obj.AutoMemberType == "None":
            return new_members
        for member in FreeCAD.ActiveDocument.Objects:
            if self.recognized_by_type(obj, member) or \
               self.recognized_by_view_properties(obj, member):
                new_members.append(member)
        return new_members

    def set_members_visibility(self, members, visibility):
        for m, v in zip(members, visibility):
            if m.ViewObject.Visibility != v:
                m.ViewObject.Visibility = v

    def set_parameters(self, obj, preset_dict):
        obj_params_list = preset_dict.keys()
        for p in obj_params_list:
            value = preset_dict.get(p)
            if value is not None and hasattr(obj, p):
                setattr(obj, p, value)

    def get_current_member_layer(self, obj, member):
        ver = FreeCAD.Version()
        fc_ver = f"{ver[0]}.{ver[1]}"
        if fc_ver == "1.0":
            # FreeCAD v1.0.x
            member_layer = obj.ViewObject.Proxy._get_layer(member)
        else:
            # FreeCAD newer then v1.0.x
            member_layer = layer.get_layer(member)
        return member_layer

    def recognized_by_type(self, obj, member):
        """ It returns True if a member object's Proxy class
        matches obj.AutoMemberType. Otherwise it returns False.
        False is returned also if the member belongs to any other Layer.
        """
        current_member_layer = self.get_current_member_layer(obj, member)
        if current_member_layer is None:
            try:
                member_type = type(member.Proxy).__name__
            except AttributeError:
                member_type = None
            if obj.AutoMemberType == member_type:
                return True
        return False

    def recognized_by_view_properties(self, obj, member):
        """ It returns True if a member object's View Provider properties
        match obj's View Provider properties. Otherwise it returns False.
        False is returned also if the member belongs to any other Layer.
        Properties to check: LineWidth, LineColor, PointSize, PointColor.
        Additionally member's Proxy class has to be: Wire or Point
        """
        current_member_layer = self.get_current_member_layer(obj, member)
        member_match = False
        if current_member_layer is None:
            props = ["LineWidth", "LineColor", "PointSize", "PointColor"]
            try:
                member_match = True
                if type(member.Proxy).__name__ == "Point":
                    props = props[2:]
                elif type(member.Proxy).__name__ != "Wire":
                    return False
                preset = layer_presets.get(obj.AutoMemberType)
                if preset not in [None, "None"]:
                    for prop in props:
                        mp_id = member.ViewObject.getTypeIdOfProperty(prop)
                        mp_val = getattr(member.ViewObject, prop)
                        if mp_id == "App::PropertyColor":
                            mp_val = tuple([int(c * 255) for c in mp_val][:3])
                        if mp_val != preset.get("vobj").get(prop):
                            member_match = False
            except AttributeError:
                member_match = False
        return member_match


class ViewProviderLayerExtended(view_layer.ViewProviderLayer):
    """The viewprovider for the LayerExtended object."""

    def __init__(self, vobj):
        view_layer.ViewProviderLayer.__init__(self, vobj)

    def onBeforeChange(self, vobj, prop):
        view_layer.ViewProviderLayer.onBeforeChange(self, vobj, prop)
        if prop in ("PointSize", "PointColor"):
            setattr(self, "old" + prop, getattr(vobj, prop))

    def set_visual_properties(self, vobj, properties):
        view_layer.ViewProviderLayer.set_visual_properties(
            self, vobj, properties)
        if "PointColor" not in properties:
            vobj.addProperty("App::PropertyColor", "PointColor", "Layer",
                             QT_TRANSLATE_NOOP(
                                "App::Property", "The point color of the " +
                                "objects contained within this layer"))
            color = params.get_param_view("DefaultShapeLineColor") | 0x000000FF
            vobj.PointColor = color
        if "PointSize" not in properties:
            vobj.addProperty("App::PropertyFloat", "PointSize", "Layer",
                             QT_TRANSLATE_NOOP(
                                "App::Property", "The point size of the " +
                                "objects contained within this layer"))
            vobj.PointSize = params.get_param_view("DefaultShapeLineWidth")

    def change_view_properties(self, vobj, prop, old_prop=None, targets=None):
        if prop == "PointColor" and not vobj.OverrideLineColorChildren:
            return
        ver = FreeCAD.Version()
        fc_ver = f"{ver[0]}.{ver[1]}"
        if fc_ver == "1.0":
            # FreeCAD v1.0.x
            params = []
        else:
            # FreeCAD newer then v1.0.x
            params = [old_prop, targets]
        view_layer.ViewProviderLayer.change_view_properties(
            self, vobj, prop, *params)
        if prop == "LineWidth":
            view_layer.ViewProviderLayer.change_view_properties(
                self, vobj, "PointSize", *params)
        if prop == "LineColor" and vobj.OverrideLineColorChildren:
            view_layer.ViewProviderLayer.change_view_properties(
                self, vobj, "PointColor", *params)

    def onChanged(self, vobj, prop):
        view_layer.ViewProviderLayer.onChanged(self, vobj, prop)
        if (
                prop in ("PointSize", "PointColor")
                and hasattr(vobj, "OverrideLineColorChildren")
                and hasattr(vobj, "OverrideShapeAppearanceChildren")
        ):
            old_prop = getattr(self, "old" + prop, None)
            self.change_view_properties(vobj, prop, old_prop)
            if hasattr(self, "old" + prop):
                delattr(self, "old" + prop)

    def updateData(self, obj, prop):
        view_layer.ViewProviderLayer.updateData(self, obj, prop)
        if prop == "Group":
            for _prop in ("PointSize", "PointColor"):
                self.onChanged(obj.ViewObject, _prop)
        if prop == "AutoMemberType":
            preset = layer_presets.get(obj.AutoMemberType)
            if preset not in [None, "None"]:
                self.set_parameters(obj.ViewObject, preset.get("vobj"))

    def set_parameters(self, vobj, preset_dict):
        vobj_params_list = preset_dict.keys()
        for p in vobj_params_list:
            value = preset_dict.get(p)
            if value is not None and hasattr(vobj, p):
                setattr(vobj, p, value)

    # def reassign_props(self):
    #     view_layer.ViewProviderLayer.reassign_props(self)
    #     for prop in ("PointSize", "PointColor"):
    #         self.onChanged(self.Object.ViewObject, prop)


def make_extended_layer(preset_name):
    if preset_name in layer_presets.keys():
        obj = Draft.make_layer()
        LayerExtended(obj)
        ViewProviderLayerExtended(obj.ViewObject)
        obj.AutoMemberType = preset_name
        # if preset_name == "None":
        #    obj.Label = "Layer Extended"


def make_layers(presets=layer_presets):
    layers = FreeCAD.ActiveDocument.findObjects(Name="Layer")
    member_types = set()
    for obj in layers:
        if hasattr(obj, "AutoMemberType"):
            if obj.AutoMemberType != "None":
                member_types.add(obj.AutoMemberType)
    for preset_name in presets.keys():
        if preset_name not in member_types:
            make_extended_layer(preset_name)
