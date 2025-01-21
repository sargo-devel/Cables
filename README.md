# FreeCAD Cables Workbench

Electrical cables drawing tools workbench for [FreeCAD](https://freecad.org)

![Cable](doc/cable.png) ![Box](doc/box.png)
![ElectricInst](doc/electric_inst.png)

## The goal and idea
The Cables Workbench has the following goals:

1. Creation and use of ready-made elements and cable profiles for modeling electrical installations in architectural design projects
2. Simplification of cable drawing in architectural models with the possibility of easy changes (like repositioning wall sockets or ligt switches with cables attached to them)
3. Enable quick and easy connection of single wires if that detail level is needed (e.g. connecting wires to connectors in electrical boxes or swichboards)
4. To be compatible with [BIM Workbench](https://wiki.freecad.org/BIM_Workbench)

The main idea of modeling cables (which are flexible in nature) as a static 3D elements is based on Wire Flex objects.
These objects are modified  [Draft Wire](https://wiki.freecad.org/Draft_Wire) objects with additional features like the possibility of attaching any Wire Flex vertices to external objects. This allows to automatically change the cable shape and length while changing the placement of external elements like boxes, switches, ligth points, walls, ceilings etc.

All elements (cables, boxes, connectors etc.) in this workbench are  [Arch Component](https://wiki.freecad.org/Arch_Component) elements. The cable element is based on [Arch Pipe](https://wiki.freecad.org/Arch_Pipe) class.

## Wiki
This workbench does not have any FreeCAD Wiki page yet. This is planned soon.
You can install the workbench and see [examples](https://github.com/sargo-devel/Cables/examples) to have a closer look into details. These files contain Info text with some additional hints.

## Installation
Currently the only method to install this workbench is to copy its entire `Cables/` folder to the FreeCAD local `Mod/` folder. Details: [Installing more workbenches](https://wiki.freecad.org/Installing_more_workbenches).

It is also planned to make it possible to install this workbench via the [Addon Manager](https://github.com/FreeCAD/FreeCAD-addons) (from Tools menu).

### Note
This workbench is currently at the alpha stage. You can expect some bugs which can make your model broken.
Some properties of models can change in the future and break models created with current version.

### Compatibility
Cables Workbench was created for [FreeCAD](https://freecad.org) version 1.0.0. No compatibility checks with previuos versions were made.

### References
* Development repo: https://github.com/sargo-devel/Cables
* FreeCAD Forum announcement/discussion [thread](https://forum.freecadweb.org/...) 
* Authors: [@SargoDevel](https://github.com/sargo-devel)

### Release notes:
* v0.1.01  21 Jan 2025:  Initial version

## License
LGPLv3 (see [LICENSE](LICENSE))
