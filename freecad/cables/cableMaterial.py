"""cableMaterial
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

multi_names2 = [('Box', 'InsulWhite'), ('Rail', "RailSteel")]

multi_names3 = [('J', 'InsulJacket'), ('L1', 'InsulBlack'), ('N', 'InsulBlue'),
                ('PE', 'InsulYellow'), ('PE', 'InsulGreen'), ('CU', 'Cu')]

multi_names5 = [('J', 'InsulJacket'), ('L1', 'InsulBrown'),
                ('L2', 'InsulBlack'), ('L3', 'InsulGray'), ('N', 'InsulBlue'),
                ('PE', 'InsulYellow'), ('PE', 'InsulGreen'), ('CU', 'Cu')]

multi_names8 = [('J', 'InsulJacket'), ('P1A', 'InsulOrange'),
                ('P1B', 'InsulWhite'), ('P1B', 'InsulOrange'),
                ('P2A', 'InsulBrown'), ('P2B', 'InsulWhite'),
                ('P2B', 'InsulBrown'), ('P3A', 'InsulGreen'),
                ('P3B', 'InsulWhite'), ('P3B', 'InsulGreen'),
                ('P4A', 'InsulBlue'), ('P4B', 'InsulWhite'),
                ('P4B', 'InsulBlue'), ('CU', 'Cu')]

multi_list = {'boxMultiMat2m': multi_names2, 'cableMultiMat3w': multi_names3,
              'cableMultiMat5w': multi_names5, 'cableMultiMat8w': multi_names8}

mat_table = {
    'InsulJacket': {
        'mat_name': 'PVC-Generic',
        'color': (215, 251, 255)
    },
    'Cu': {
        'mat_name': 'Copper-Generic',
        'color': (184, 115, 51)
    },
    'InsulYellow': {
        'mat_name': 'PVC-Generic',
        'color': (255, 255, 0)
    },
    'InsulBlack': {
        'mat_name': 'PVC-Generic',
        'color': (54, 54, 54)
    },
    'InsulGray': {
        'mat_name': 'PVC-Generic',
        'color': (160, 160, 160)
    },
    'InsulBrown': {
        'mat_name': 'PVC-Generic',
        'color': (80, 40, 0)
    },
    'InsulLightBrown': {
        'mat_name': 'PVC-Generic',
        'color': (136, 97, 58)
    },
    'InsulBlue': {
        'mat_name': 'PVC-Generic',
        'color': (0, 85, 255)
    },
    'InsulLightBlue': {
        'mat_name': 'PVC-Generic',
        'color': (135, 197, 255)
    },
    'InsulGreen': {
        'mat_name': 'PVC-Generic',
        'color': (47, 205, 102)
    },
    'InsulLightGreen': {
        'mat_name': 'PVC-Generic',
        'color': (167, 243, 190)
    },
    'InsulOrange': {
        'mat_name': 'PVC-Generic',
        'color': (243, 112, 66)
    },
    'InsulLightOrange': {
        'mat_name': 'PVC-Generic',
        'color': (254, 216, 177)
    },
    'InsulWhite': {
        'mat_name': 'PVC-Generic',
        'color': (250, 250, 250)
    },
    'RailSteel': {
        'mat_name': 'Steel-Generic',
        'color': (204, 204, 230)
    }
}


def get_material_from_lib(name):
    path = os.path.join(FreeCAD.getResourceDir(), "Mod", "Material")
    result = []
    for current_folder, subfolders, files in os.walk(path):
        for f in files:
            if f.endswith('.FCMat') or f.endswith('.FCMAT'):
                if name in f:
                    result.append(current_folder+os.sep+f)
    return result


def makeMaterial(name, mat_name, color):
    import importFCMat
    import Arch

    result = get_material_from_lib(mat_name)
    mat = importFCMat.read(result[0]) if result else None
    material = Arch.makeMaterial()
    if mat:
        material.Material = mat
    material.Label = name
    material.Color = color
    material.Transparency = 0
    return material


def makeCableMaterials(table=mat_table, multi_list=multi_list):
    import Arch

    materials = []
    for key in table.keys():
        materials.append(makeMaterial(key, table[key]['mat_name'],
                                      table[key]['color']))
    mat_labels = [m.Label for m in materials]
    for multi_names in multi_list.items():
        multi = Arch.makeMultiMaterial()
        lmat = []
        lnames = []
        for item in multi_names[1]:
            idx = mat_labels.index(item[1])
            lmat.append(materials[idx])
            lnames.append(item[0])
        multi.Materials = lmat
        multi.Names = lnames
        thickness = [0.0] * len(multi.Names)
        multi.Thicknesses = thickness
        multi.Label = multi_names[0]
    return materials
