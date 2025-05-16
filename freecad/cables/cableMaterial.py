"""cableMaterial
"""

import os
import FreeCAD
import importFCMat
import Arch

multi_names3 = {'J': 0, 'L1': 2, 'N': 4, 'PE': 5, 'CU': 6}
multi_names5 = {'J': 0, 'L1': 1, 'L2': 2, 'L3': 3, 'N': 4, 'PE': 5, 'CU': 6}
multi_names8 = {'J': 0, 'P1A': 9, 'P1B': 10, 'P2A': 1, 'P2B': 7, 'P3A': 11,
                'P3B': 12, 'P4A': 4, 'P4B': 8, 'CU': 6}
multi_list = {'cableMultiMat3w': multi_names3, 'cableMultiMat5w': multi_names5,
              'cableMultiMat8w': multi_names8}
mat_table = [
    {'name': 'InsulJacket',
     'mat_name': 'PVC-Generic',
     'color': (215, 251, 255)
     },
    {'name': 'InsulBrown',
     'mat_name': 'PVC-Generic',
     'color': (80, 40, 0)
     },
    {'name': 'InsulBlack',
     'mat_name': 'PVC-Generic',
     'color': (54, 54, 54)
     },
    {'name': 'InsulGray',
     'mat_name': 'PVC-Generic',
     'color': (160, 160, 160)
     },
    {'name': 'InsulBlue',
     'mat_name': 'PVC-Generic',
     'color': (0, 85, 255)
     },
    {'name': 'InsulYellow',
     'mat_name': 'PVC-Generic',
     'color': (255, 255, 0)
     },
    {'name': 'Cu',
     'mat_name': 'Copper-Generic',
     'color': (184, 115, 51)
     },
    {'name': 'InsulLightBrown',
     'mat_name': 'PVC-Generic',
     'color': (136, 97, 58)
     },
    {'name': 'InsulLightBlue',
     'mat_name': 'PVC-Generic',
     'color': (135, 197, 255)
     },
    {'name': 'InsulOrange',
     'mat_name': 'PVC-Generic',
     'color': (243, 112, 66)
     },
    {'name': 'InsulLightOrange',
     'mat_name': 'PVC-Generic',
     'color': (254, 216, 177)
     },
    {'name': 'InsulGreen',
     'mat_name': 'PVC-Generic',
     'color': (47, 205, 102)
     },
    {'name': 'InsulLightGreen',
     'mat_name': 'PVC-Generic',
     'color': (167, 243, 190)
     }
    ]


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
    materials = []
    for m in table:
        materials.append(makeMaterial(m['name'], m['mat_name'], m['color']))
    multi_names = multi_names3
    for multi_names in multi_list.items():
        multi = Arch.makeMultiMaterial()
        lmat = []
        for i in multi_names[1].values():
            lmat.append(materials[i])
        multi.Materials = lmat
        multi.Names = list(multi_names[1].keys())
        thickness = [0.0] * len(multi.Names)
        multi.Thicknesses = thickness
        multi.Label = multi_names[0]
    return materials
