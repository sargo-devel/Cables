"""ArchCableBaseElement
"""

import os
import math
import FreeCAD
import ArchComponent
import Part
import Import
from freecad.cables import cableTerminal
from freecad.cables import cableSupport
from freecad.cables import cableProfile
from freecad.cables import libPath
from freecad.cables import presetsPath
from freecad.cables import translate
from freecad.cables import QT_TRANSLATE_NOOP
if FreeCAD.GuiUp:
    import FreeCADGui

presetfiles = [os.path.join(presetsPath, "presets.csv"),
               os.path.join(FreeCAD.getUserAppDataDir(), "Cables",
                            "presets.csv")]
libdirs = [libPath, os.path.join(FreeCAD.getUserAppDataDir(), "Cables", "lib")]
unit_schema_m2 = [4, 9]


class TaskPanelBaseElement:
    """This class shouldn't be used directly, it can be the base class only.
    The child class should have ui form.comboPreset QComboBox"""
    def __init__(self, obj, ui):
        self.form = FreeCADGui.PySideUic.loadUi(ui)
        self.obj = obj
        self.presetnames, _ = obj.Proxy.getPresets(obj)
        self.invalidpreset = False
        self.invalidpresetname = None
        self.oldSchema = FreeCAD.Units.getSchema()
        if self.oldSchema in unit_schema_m2:
            self.newSchema = 0
        else:
            self.newSchema = self.oldSchema

    def accept(self):
        # execute this code after child class accept method
        FreeCAD.ActiveDocument.commitTransaction()
        FreeCADGui.Control.closeDialog()
        FreeCAD.Units.setSchema(self.oldSchema)
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.ActiveDocument.resetEdit()

    def reject(self):
        FreeCAD.ActiveDocument.abortTransaction()
        FreeCADGui.Control.closeDialog()
        FreeCAD.Units.setSchema(self.oldSchema)
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.ActiveDocument.resetEdit()

    def updateProperty(self, pname, pvalue, callback):
        ptype = self.obj.getTypeIdOfProperty(pname)
        try:
            prop = getattr(self.obj, pname)
            if ptype == "App::PropertyEnumeration":
                if self.obj.getEnumerationsOfProperty(pname)[pvalue] != prop:
                    setattr(self.obj, pname, pvalue)
            elif ptype == "App::PropertyFloat" and pvalue != "custom":
                if type(pvalue).__name__ == "Quantity":
                    setattr(self.obj, pname, pvalue.Value)
                else:
                    if not math.isclose(float(pvalue), prop):
                        setattr(self.obj, pname, float(pvalue))
            elif ptype == "App::PropertyInteger":
                if int(pvalue) != prop:
                    setattr(self.obj, pname, int(pvalue))
            elif pvalue != "custom":
                if pvalue != prop:
                    setattr(self.obj, pname, pvalue)
            if hasattr(self.obj, "recompute"):
                self.obj.recompute(True)
        except (AttributeError, ValueError):
            FreeCAD.Console.PrintError(
                self.obj, f"Can't set {pname} with value: {pvalue}")
        if callback is not None:
            callback(pname, pvalue)

    def connectEnumVar(self, element, pname, callback=None):
        enumlist = self.obj.getEnumerationsOfProperty(pname)
        if enumlist is None:
            element.currentTextChanged.connect(
                lambda txtval: self.updateProperty(pname, txtval, callback))
        else:
            element.currentIndexChanged.connect(
                lambda idx: self.updateProperty(pname, idx, callback))

    def connectSpinVar(self, element, pname, callback=None):
        # disable recompute on every key press
        element.setProperty("keyboardTracking", False)
        element.valueChanged.connect(
            lambda value: self.updateProperty(pname, value, callback))

    def reloadPropertiesFromObj(self):
        if self.obj.Preset in self.presetnames:
            self.form.comboPreset.setCurrentText(self.obj.Preset)
        else:
            self.form.comboPreset.setCurrentIndex(0)
            self.invalidpreset = True
            self.invalidpresetname = self.obj.Preset
            setattr(self.obj, "Preset", 0)
            self.updateVisibility("Preset", 0)
            FreeCAD.Console.PrintError(
                self.obj.Label, f"{self.invalidpresetname} preset not found " +
                "in library.")


class BaseElement(ArchComponent.Component):
    """The ArchCableBaseElement object
    """
    def __init__(self, obj, eltype="CableBaseElement"):
        ArchComponent.Component.__init__(self, obj)
        BaseElement.setProperties(self, obj, eltype)
        self.ExtShape = None
        self.Terminals = self.findTerminals(obj)
        self.SuppLines = self.findSuppLines(obj)

    def setProperties(self, obj, eltype):
        pl = obj.PropertiesList
        if "Preset" not in pl:
            obj.addProperty("App::PropertyEnumeration", "Preset",
                            eltype,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The predefined set of " +
                                "parameters for this object"))
            obj.Preset, _ = self.getPresets(obj)
        if "NumberOfTerminals" not in pl:
            obj.addProperty("App::PropertyInteger", "NumberOfTerminals",
                            eltype,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The number of Terminals " +
                                "in this object"))
            obj.setPropertyStatus("NumberOfTerminals", "ReadOnly")
        if "NumberOfSuppLines" not in pl:
            obj.addProperty("App::PropertyInteger", "NumberOfSuppLines",
                            eltype,
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The number of Support " +
                                "Lines in this object"))
            obj.setPropertyStatus("NumberOfSuppLines", "ReadOnly")
        if "ExtShapeSolids" not in pl:
            obj.addProperty("App::PropertyInteger", "ExtShapeSolids",
                            "Ext",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The number of solids in " +
                                "an external shape loaded from file"))
            obj.setPropertyStatus("ExtShapeSolids", ["ReadOnly", "Hidden"])
        if "ExtColor" not in pl:
            obj.addProperty("App::PropertyColorList", "ExtColor",
                            "Ext",
                            QT_TRANSLATE_NOOP(
                                "App::Property", "The colors of external " +
                                "shape loaded from file"))
            obj.setPropertyStatus("ExtColor", ["ReadOnly", "Hidden"])
        self.Type = "Component"

    def onDocumentRestored(self, obj, eltype="CableBaseElement"):
        ArchComponent.Component.onDocumentRestored(self, obj)
        BaseElement.setProperties(self, obj, eltype)
        self.ExtShape = None
        self.Terminals = self.findTerminals(obj)
        self.SuppLines = self.findSuppLines(obj)

    def onChanged(self, obj, prop):
        # FreeCAD.Console.PrintMessage(obj.Label, f"onChanged start: {prop}\n")
        undoredo = FreeCAD.ActiveDocument.Transacting
        ArchComponent.Component.onChanged(self, obj, prop)
        if prop == "Label" and not undoredo:
            self.Terminals = self.findTerminals(obj)
            self.SuppLines = self.findSuppLines(obj)
            if self.Terminals:
                for nr, t in enumerate(self.Terminals):
                    label = f"{obj.Label}_Term{nr+1:03}"
                    if not label == t.Label:
                        t.Label = label
            if self.SuppLines:
                for nr, s in enumerate(self.SuppLines):
                    label = f"{obj.Label}_SuppLines{nr+1:03}"
                    if not label == s.Label:
                        s.Label = label
        if prop == "NumberOfTerminals" and not undoredo:
            self.Terminals = self.findTerminals(obj)
            if len(self.Terminals) != obj.NumberOfTerminals:
                self.updateNumberOfTerminals(obj)
        if prop == "NumberOfSuppLines" and not undoredo:
            self.SuppLines = self.findSuppLines(obj)
            if len(self.SuppLines) != obj.NumberOfSuppLines:
                self.updateNumberOfSuppLines(obj)
        if prop == "Preset" and not undoredo:
            # refresh presets names:
            presetnames, presets = self.getPresets(obj)
            if presetnames != obj.getEnumerationsOfProperty("Preset"):
                obj.Preset = presetnames
            self.updatePropertiesFromPreset(obj, presets)
        if prop == "Base" and not undoredo:
            self.updatePropertyStatusForBase(
                obj, ["NumberOfTerminals", "NumberOfSuppLines"], "ReadOnly")
            self.updatePropertyStatusForBase(
                obj, ["NumberOfTerminals", "NumberOfSuppLines"], "Hidden")
            if obj.Base is not None:
                self.updatePropertyStatusForBase(obj, ["Preset"], "Hidden", 0)
                self.Terminals = self.findTerminals(obj)
                if self.Terminals:
                    for t in self.Terminals:
                        t.Proxy.setPropertiesReadWrite(t)
            obj.ExtColor = obj.ExtColor

    def execute(self, obj):
        terminals = self.findTerminals(obj)
        if len(terminals) != len(self.Terminals):
            obj.NumberOfTerminals = len(terminals)
        supplines = self.findSuppLines(obj)
        if len(supplines) != len(self.SuppLines):
            obj.NumberOfSuppLines = len(supplines)

        if hasattr(obj, "Base") and obj.Base is None and \
           "Hidden" in obj.getPropertyStatus("Preset"):
            self.updatePropertyStatusForBase(obj, ["Preset"], "Hidden", 0)
            obj.Preset = obj.Preset

        pl = obj.Placement
        shapes = []
        if (hasattr(obj, "Base") and obj.Base is not None):
            # Shape taken from BaseElement
            ArchComponent.Component.execute(self, obj)
        elif hasattr(obj, "ExtShapeSolids") and obj.ExtShapeSolids > 0:
            if self.ExtShape is not None:
                # Shape type: Fixed, new shape
                shapes.extend(self.ExtShape.Solids)
                self.ExtShape = None
            else:
                # Shape type: Fixed
                shapes.extend(obj.Shape.Solids[:obj.ExtShapeSolids])
            sh = Part.makeCompound(shapes)
            if obj.Additions or obj.Subtractions:
                sh = self.processSubShapes(obj, sh, pl)
            if not self.sameShapes(sh, obj.Shape):
                obj.Shape = sh
            elif obj.Material:
                # refresh colors
                obj.Material = obj.Material
        if self.Terminals:
            self.adjustTerminals(obj)
        if self.SuppLines:
            self.adjustSuppLines(obj)

    def getPresets(self, obj, presetfiles=presetfiles):
        presets = cableProfile.readCablePresets(presetfiles)
        presetnames = []
        for p in presets:
            presetnames.append(f"{p[3]}_{p[1]}")
        presetnames.sort()
        presetnames = ["Customized"] + presetnames
        return presetnames, presets

    def setPreset(self, obj, preset, pnames=[], pvalues=[]):
        try:
            if preset != obj.Preset:
                obj.Preset = preset
        except ValueError:
            FreeCAD.Console.PrintError(obj.Label,
                                       f"Preset {preset} does not exist!\n")
            if obj.Preset is None:
                obj.Preset = "Customized"
        if preset == "Customized" and len(pnames) == len(pvalues):
            try:
                for p in zip(pnames, pvalues):
                    if getattr(obj, p[0]) != p[1]:
                        setattr(obj, p[0], p[1])
            except (AttributeError, ValueError):
                FreeCAD.Console.PrintError(
                    obj, f"Can't set {p[0]} with value: {p[1]}")

    def updatePropertiesFromPreset(self, obj, presets):
        return

    def process_multishape_STEP(self, data):
        """Function processes list of tuples (shape, colors) obtained from
        step file. It makes single compound of all shapes and  puts all colors
        into single list.
        Returns tuple (shape, list of colors)
        """
        shapes = []
        colors = []
        for pair in data:
            shape = pair[0].Shape.copy()
            if len(pair[1]) == 1:
                color = len(shape.Faces)*pair[1]
            else:
                color = pair[1]
            shapes.extend(shape.Solids)
            colors.extend(color)
        return Part.makeCompound(shapes), colors

    def readExtShape(self, obj, filename, libdirs=libdirs):
        """Function reads object shape and colors from step file.
        Returns tuple (shape, list of colors)
        """
        fullname = None
        for libdir in libdirs:
            fullpath = os.path.join(libdir, filename)
            if os.path.exists(fullpath):
                fullname = fullpath
                break
        if fullname is None:
            FreeCAD.Console.PrintError(
                obj.Label, f"File loading error {filename}. " +
                "File not found in library\n")
            return Part.Shape(), []
        # ImportGui.insert(fullname, FreeCAD.ActiveDocument.Name)
        # objlist = App.ActiveDocument.findObjects(Label='...')
        oldobjlst = FreeCAD.ActiveDocument.Objects
        data = Import.insert(fullname, FreeCAD.ActiveDocument.Name)
        if data is not None:
            # imported STEP has colors
            if len(data) == 1:
                # STEP is a single shape
                sh = data[0][0].Shape.copy()
                sh_colors = data[0][1]
            else:
                # STEP is a group of shapes
                sh, sh_colors = self.process_multishape_STEP(data)
        else:
            # imported STEP has no colors
            sh = Part.read(fullname)
            sh_colors = []
        newobjlst = FreeCAD.ActiveDocument.Objects
        dellist = [n for n in set(newobjlst)-set(oldobjlst)
                   if n.TypeId in ['Part::Feature', 'App::Part']]
        for el in dellist:
            FreeCAD.ActiveDocument.removeObject(el.Name)
        return sh, sh_colors

    def readExtData(self, obj, filename, libdirs=libdirs):
        """Function reads data: shape offset, terminals, support lines
        from csv file.
        Returns dict
        """
        fullname = None
        for libdir in libdirs:
            fullpath = os.path.join(libdir, filename)
            if os.path.exists(fullpath):
                fullname = fullpath
                break
        if fullname is None:
            FreeCAD.Console.PrintError(
                obj.Label, f"File loading error {filename}. " +
                "File not found in library\n")
            return {}
        rawdata = cableProfile.readCablePresets([fullname])
        terminals = []
        extshape = []
        supplines = []
        for d in rawdata:
            if d[2] == "ExtShape":
                offset = FreeCAD.Vector(d[4], d[5], d[6])
                rotation = FreeCAD.Rotation(d[7], d[8], d[9])
                pl = FreeCAD.Placement(offset, rotation)
                extshape.append((pl,))
            elif d[2] == "Terminal":
                offset = FreeCAD.Vector(d[4], d[5], d[6])
                rotation = FreeCAD.Rotation(d[7], d[8], d[9])
                pl = FreeCAD.Placement(offset, rotation)
                terminals.append((pl, d[10], d[11], d[12], d[1]))
            elif d[2] == "SupportLines":
                offset = FreeCAD.Vector(d[4], d[5], d[6])
                rotation = FreeCAD.Rotation(d[7], d[8], d[9])
                pl = FreeCAD.Placement(offset, rotation)
                supplines.append((pl,))
        data = {"ExtShape": extshape, "Terminal": terminals,
                "SupportLines": supplines}
        return data

    def makeTerminalChildObjects(self, obj):
        terminals = self.findTerminals(obj)
        nr = obj.NumberOfTerminals
        if terminals:
            for t in terminals:
                FreeCAD.ActiveDocument.removeObject(t.Name)
        terminals = []
        for i in range(nr):
            child_obj = cableTerminal.makeCableTerminal()
            child_obj.Label = f"{obj.Label}_Term{i+1:03}"
            child_obj.ParentName = obj.Name
            child_obj.AttachmentSupport = [(obj, ('',))]
            terminals.append(child_obj)
        self.Terminals = terminals
        self.adjustTerminals(obj)

    def updateNumberOfTerminals(self, obj):
        self.Terminals = self.findTerminals(obj)
        if hasattr(obj, "NumberOfTerminals") \
           and len(self.Terminals) != obj.NumberOfTerminals:
            terminals = self.Terminals
            nr = obj.NumberOfTerminals
            if len(terminals) > nr:
                for t in terminals[nr:]:
                    FreeCAD.ActiveDocument.removeObject(t.Name)
                terminals = terminals[:nr]
            elif len(terminals) < nr:
                for i in range(len(terminals), nr):
                    child_obj = cableTerminal.makeCableTerminal()
                    child_obj.Label = f"{obj.Label}_Term{i+1:03}"
                    child_obj.ParentName = obj.Name
                    child_obj.AttachmentSupport = [(obj, ('',))]
            self.Terminals = self.findTerminals(obj)
            self.adjustTerminals(obj)

    def adjustTerminals(self, obj):
        self.updateTerminalsParameters(obj)

    def updateTerminalsParameters(self, obj):
        # Default terminal update. Can be overwritten by child class
        return

    def makeSupportLinesChildObjects(self, obj):
        supplines = self.findSuppLines(obj)
        nr = obj.NumberOfSuppLines
        if supplines:
            for supp in supplines:
                FreeCAD.ActiveDocument.removeObject(supp.Name)
        supplines = []
        for i in range(nr):
            child_obj = FreeCAD.ActiveDocument.addObject(
                "Part::FeaturePython", "CableSuppLines")
            cableSupport.ExtSuppLines(child_obj)
            if FreeCAD.GuiUp:
                cableSupport.ViewProviderExtSuppLines(child_obj.ViewObject)
            child_obj.Label = f"{obj.Label}_SuppLines{i+1:03}"
            child_obj.ParentName = obj.Name
            child_obj.Lines = Part.Shape()
            child_obj.AttachmentSupport = [(obj, ('',))]
            supplines.append(child_obj)
        self.SuppLines = supplines
        self.adjustSuppLines(obj)

    def updateNumberOfSuppLines(self, obj):
        self.SuppLines = self.findSuppLines(obj)
        if hasattr(obj, "NumberOfSuppLines") \
           and len(self.SuppLines) != obj.NumberOfSuppLines:
            supplines = self.SuppLines
            nr = obj.NumberOfSuppLines
            if len(supplines) > nr:
                for s in supplines[nr:]:
                    FreeCAD.ActiveDocument.removeObject(s.Name)
            elif len(supplines) < nr:
                for i in range(len(supplines), nr):
                    child_obj = FreeCAD.ActiveDocument.addObject(
                        "Part::FeaturePython", "CableSuppLines")
                    cableSupport.ExtSuppLines(child_obj)
                    if FreeCAD.GuiUp:
                        cableSupport.ViewProviderExtSuppLines(
                            child_obj.ViewObject)
                    child_obj.Label = f"{obj.Label}_SuppLines{i+1:03}"
                    child_obj.ParentName = obj.Name
                    child_obj.Lines = Part.Shape()
                    child_obj.AttachmentSupport = [(obj, ('',))]
            self.SuppLines = self.findSuppLines(obj)
            self.adjustSuppLines(obj)

    def adjustSuppLines(self, obj):
        self.SuppLines = self.findSuppLines(obj)
        for supp in self.SuppLines:
            supp_lines = self.makeSupportLines(obj)
            if not self.sameShapes(supp_lines, supp.Lines) \
               or len(supp_lines.Edges) > 4:
                supp.Lines = supp_lines

    def makeSupportLines(self, obj):
        # default support lines cross. Can be overwritten by child class
        x0 = 0
        y0 = 0
        z0 = 0
        x = y = 5.0
        cross = [(x0, y0, z0),
                 (x0+x, y0, z0),
                 (x0-x, y0, z0),
                 (x0, y0+y, z0),
                 (x0, y0-y, z0)]
        v = []
        for c in cross:
            v.append(FreeCAD.Vector(*c))
        lines = []
        lines.append(Part.LineSegment(v[0], v[3]))
        lines.append(Part.LineSegment(v[0], v[2]))
        lines.append(Part.LineSegment(v[0], v[4]))
        lines.append(Part.LineSegment(v[0], v[1]))
        s = Part.Shape(lines)
        return s

    def updatePropertyStatusForBase(self, obj, plist, param, mode=1):
        if obj.Base is not None:
            switch = "-" if mode == 1 else ""
        else:
            switch = "" if mode == 1 else "-"
        for p in plist:
            if hasattr(obj, p):
                obj.setPropertyStatus(p, switch + param)

    def findTerminals(self, obj):
        tlist = []
        for p in obj.InList:
            if hasattr(p, "Proxy") and \
               type(p.Proxy).__name__ == "CableTerminal":
                tlist.append(p)
        return tlist

    def findSuppLines(self, obj):
        tlist = []
        for p in obj.InList:
            if hasattr(p, "Proxy") and \
               type(p.Proxy).__name__ == "ExtSuppLines":
                tlist.append(p)
        return tlist

    def sameShapes(self, sh1, sh2):
        """Compares shapes for equality.
        Returns True if shapes are equal, False otherwise.
        Warning: comparison is not 100% effective
        """
        if len(sh1.Solids) != len(sh2.Solids):
            return False
        nr_of_solids = len(sh1.Solids)
        if nr_of_solids < 1:
            if sh1.dumps() == sh2.dumps():
                return True
            sign1 = (sh1.MemSize, round(sh1.Length, 5) if not sh1.isNull()
                     else 0)
            sign2 = (sh2.MemSize, round(sh2.Length, 5) if not sh2.isNull()
                     else 0)
            if not sign1 == sign2:
                return False
        for i in ["Faces", "Edges", "Vertexes"]:
            if len(getattr(sh1, i)) != len(getattr(sh2, i)):
                return False
        for i in range(nr_of_solids):
            s1 = sh1.Solids[i]
            s2 = sh2.Solids[i]
            sign1 = (s1.ShapeType, round(s1.Volume, 5), round(s1.Area, 5),
                     round(s1.Length, 5))
            sign2 = (s2.ShapeType, round(s2.Volume, 5), round(s2.Area, 5),
                     round(s2.Length, 5))
            if not sign1 == sign2:
                return False
        return True


class ViewProviderBaseElement(ArchComponent.ViewProviderComponent):
    """A View Provider for the ArchCableBaseElement object
    """
    def __init__(self, vobj):
        ArchComponent.ViewProviderComponent.__init__(self, vobj)

    def claimChildren(self):
        c = ArchComponent.ViewProviderComponent.claimChildren(self)
        terminals = self.Object.Proxy.findTerminals(self.Object)
        supplines = self.Object.Proxy.findSuppLines(self.Object)
        if terminals:
            c.extend(terminals)
        if supplines:
            c.extend(supplines)
        return c

    def updateData(self, obj, prop):
        # FreeCAD.Console.PrintMessage(obj.Label, f"vobj updateData: {prop}\n")
        ArchComponent.ViewProviderComponent.updateData(self, obj, prop)
        if prop == "ExtColor":
            if (hasattr(obj.ViewObject, "UseMaterialColor") and not
               obj.ViewObject.UseMaterialColor) \
               or \
               (hasattr(obj.ViewObject, "UseMaterialColor") and
               obj.ViewObject.UseMaterialColor and not obj.Material):
                # process colors without Materials directly from obj.ExtColor
                self.colorize_without_material(obj)
            else:
                # process colors with Materials from obj.ExtColor
                self.colorize(obj)
        if prop in ["Shape", "Material"]:
            if hasattr(obj.ViewObject, "UseMaterialColor") and \
               obj.ViewObject.UseMaterialColor:
                self.colorize(obj)

    def onChanged(self, vobj, prop):
        if prop == "UseMaterialColor":
            if vobj.UseMaterialColor and vobj.Object.Material:
                # clear Shape Apperiance reload Material
                vobj.ShapeAppearance = (FreeCAD.Material(),)
                m = vobj.Object.Material
                vobj.Object.Material = m
                self.colorize(vobj.Object)
            if not vobj.UseMaterialColor or not vobj.Object.Material:
                self.colorize_without_material(vobj.Object)
        ArchComponent.ViewProviderComponent.onChanged(self, vobj, prop)

    def colorize(self, obj, force=False):
        def _sort_mat(col_list):
            l_cols = list(set(col_list))
            v = [col_list.count(i) for i in l_cols]
            p = sorted(zip(l_cols, v), key=lambda x: x[1], reverse=True)
            return [i[0] for i in p]

        def _get_mat_assignments(col_list):
            sorted_cols = _sort_mat(col_list)
            m_as = []
            for a in sorted_cols:
                idxs = [i for i, val in enumerate(col_list) if val == a]
                m_as.append(idxs)
            return m_as

        def _get_flat_list(obj, mat, m_as):
            if len(mat) != len(m_as):
                FreeCAD.Console.PrintError(
                    obj.Label, f"The MultiMaterial <{obj.Material.Label}> " +
                    f"should have {len(m_as)} materials, not {len(mat)}\n")
                return None
            lmax = sum([len(i) for i in m_as])
            matlist = [mat[0]]*lmax
            for midx, m in enumerate(mat[1:]):
                for f in m_as[midx]:
                    matlist[f] = m
            return matlist

        def _convert_materials(matlist):
            new_mlist = []
            for m in matlist:
                new_m = FreeCAD.Material()
                if "DiffuseColor" in m.Material:
                    diff_col = m.Material["DiffuseColor"]
                    if "(" in diff_col:
                        col_str_lst = diff_col.strip("()").split(",")
                        color = tuple([float(f) for f in col_str_lst])
                    if color and ('Transparency' in m.Material):
                        t = float(m.Material['Transparency'])/100.0
                        color = color[:3] + (t, )
                new_m.DiffuseColor = color[:3] + (0.0, )
                new_m.Transparency = color[3]
                new_mlist.append(new_m)
            return new_mlist

        # FreeCAD.Console.PrintMessage(obj.Label, "BE vobj colorize\n")

        # colorize with single material
        ArchComponent.ViewProviderComponent.colorize(self, obj, force)

        # colorize according to ExtColor schema
        if hasattr(obj, "ExtColor") and obj.ExtColor and \
           hasattr(obj, "Material") and hasattr(obj.Material, "Materials"):
            mat_assign = _get_mat_assignments(obj.ExtColor)
            mats = _convert_materials(obj.Material.Materials)
            sapp = _get_flat_list(obj, mats, mat_assign)
            if sapp is not None:
                if not self.shapeAppearanceIsSame(
                   obj.ViewObject.ShapeAppearance, sapp):
                    obj.ViewObject.ShapeAppearance = sapp

        # colorize first solid with 1 material, the rest with 2 material
        elif hasattr(obj, "Material") and hasattr(obj.Material, "Materials"):
            mats = _convert_materials(obj.Material.Materials)
            nr_of_s1_faces = len(obj.Shape.Solids[0].Faces)
            nr_of_all_faces = len(obj.Shape.Faces)
            sapp = []
            for i in range(nr_of_s1_faces):
                sapp.append(mats[0])
            for i in range(nr_of_s1_faces, nr_of_all_faces):
                sapp.append(mats[1])
            if sapp is not None:
                if not self.shapeAppearanceIsSame(
                   obj.ViewObject.ShapeAppearance, sapp):
                    obj.ViewObject.ShapeAppearance = sapp

    def colorize_without_material(self, obj):
        if obj.Base is not None:
            if hasattr(obj.Base.ViewObject, "ShapeAppearance"):
                sapp = obj.Base.ViewObject.ShapeAppearance
        elif hasattr(obj, "ExtColor") and obj.ExtColor:
            # FreeCAD.Console.PrintMessage(obj.Label, f"BE color w/o mat.\n")
            # obsolete: obj.ViewObject.DiffuseColor = obj.ExtColor
            colors_set = set(obj.ExtColor)
            materials = []
            for c in colors_set:
                m = FreeCAD.Material()
                m.DiffuseColor = c
                materials.append(m)
            sapp = []
            palette = [m.DiffuseColor for m in materials]
            for color in obj.ExtColor:
                i = palette.index(color)
                sapp.append(materials[i])
        else:
            # FreeCAD.Console.PrintMessage("color w/o mat. w/o ExtColor\n")
            sapp = (FreeCAD.Material(),)
        if not self.shapeAppearanceIsSame(obj.ViewObject.ShapeAppearance,
                                          sapp):
            obj.ViewObject.ShapeAppearance = sapp

    def shapeAppearanceIsSame(self, sapp1, sapp2):
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

        if len(sapp1) != len(sapp2):
            return False
        for sapp_mat1, sapp_mat2 in zip(sapp1, sapp2):
            if not _shapeAppearanceMaterialIsSame(sapp_mat1, sapp_mat2):
                return False
        return True

    def setEditBase(self, vobj, mode, task_panel=None, undo_text=""):
        # this is a base for child class setEdit method
        if mode != 0:
            return None
        panel = task_panel(vobj.Object)
        FreeCADGui.Selection.clearSelection()
        FreeCAD.ActiveDocument.openTransaction(
            translate("Cables", undo_text))
        FreeCADGui.doCommand(
            f"obj = FreeCAD.activeDocument().getObject('{vobj.Object.Name}')")
        FreeCADGui.Control.showDialog(panel)
        return True

    def unsetEdit(self, vobj, mode):
        if mode != 0:
            return None
        FreeCADGui.Control.closeDialog()
        return True


def makeBaseElement(name=None):
    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError(translate(
            "Cables", "No active document. Aborting") + "\n")
        return
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython",
                                           "CableBaseElement")
    obj.Label = name if name else translate("Cables", "CableBaseElement")
    BaseElement(obj)
    if FreeCAD.GuiUp:
        ViewProviderBaseElement(obj.ViewObject)
