# FreeCAD Cables Workbench

Electric cables drawing tools workbench for [FreeCAD](https://freecad.org)

![Cable](doc/cable.png) ![Box](doc/box.png)
![ElectricInst](doc/electric_inst.png)
![Harness](doc/harness_example_new.png)
![Connectors](doc/connectors.png) ![Box_MCB](doc/box_and_MCB.png)

## The goal and idea
The Cables Workbench has the following goals:

1. Creation and use of ready-made elements and cable profiles for modeling electrical installations in architectural designs and beyond. Other application areas, such as modeling connections inside electrical devices, can also be supported.
2. Simplification of cable drawing in architectural models with the possibility of easy changes (like repositioning wall sockets or ligt switches with cables attached to them).
3. Enable quick and easy connection of single wires if that detail level is needed (e.g. connecting wires to connectors in electrical boxes or swichboards).
4. To be compatible with [BIM Workbench](https://wiki.freecad.org/BIM_Workbench) (objects should have the same base attributes and properties as other BIM objects: materials, IFC type and IFC attributes etc.).

The main idea of modeling cables (which are flexible in nature) as a static 3D elements is based on Wire Flex objects.
These objects are modified  [Draft Wire](https://wiki.freecad.org/Draft_Wire) objects with additional features like the possibility of attaching any Wire Flex vertices to external objects. This allows to automatically change the cable shape and length while changing the placement of external elements like boxes, switches, light points, walls, ceilings etc.

All solid elements (cables, boxes, connectors etc.) in this workbench are [Arch Component](https://wiki.freecad.org/Arch_Component) elements. The cable element is based on [Arch Pipe](https://wiki.freecad.org/Arch_Pipe) class.

## Wiki
This workbench has a documentation which is a part of FreeCAD Wiki: [Cables Workbench Wiki](https://wiki.freecad.org/Cables_Workbench).

You can also install the workbench and see [examples](https://github.com/sargo-devel/Cables/tree/master/examples) to have a closer look into details. These files contain Info text with some additional hints.

## Installation
This workbench can be installed via the [Addon Manager](https://github.com/FreeCAD/FreeCAD-addons) (for details see [Addon Manager Wiki](https://wiki.freecad.org/Std_AddonMgr)).

It can also be installed manually by copying its entire `Cables/` folder to the FreeCAD local `Mod/` folder. Details: [Installing more workbenches](https://wiki.freecad.org/Installing_more_workbenches).

### Note
This workbench is currently at the alpha stage. You can expect some bugs which can make your model broken.
Some properties of models can change in the future and break models created with current version.

### Compatibility
Cables Workbench was created for [FreeCAD](https://freecad.org) version 1.0.0. No compatibility checks with previous versions were made.

### Contributions
Any code contributions are welcome. Please add all of your pull requests to the dev branch.

### References
* Development repo: https://github.com/sargo-devel/Cables
* FreeCAD Forum announcement/discussion [thread](https://forum.freecad.org/viewtopic.php?t=94090)
* Author: [@SargoDevel](https://github.com/sargo-devel)

### Translations
It is possible to translate Cables Workbench. See [here](https://github.com/sargo-devel/Cables/tree/master/freecad/cables/resources/translations/README.md) for details.

Available translations:

* Belarusian
  * translators: @lidacity
* Chinese Traditional
  * translators: @DrBenson
* German
  * translators: @FBXL5, [@maxwxyz](https://github.com/maxwxyz), [@ryanthara](https://github.com/ryanthara)
* Polish
  * translators: @kaktus, @mgr_wojtal, @Piter
* Spanish
  * translators: [@hasecilu](https://github.com/hasecilu)
* Swedish
  * translators: @yeager74

Big thanks to the translators for their work!

### Release notes
* v0.3.2  11 Nov 2025
  * fixed problem with loading STEP file without colors or multishape into CableConnector or ElectricalDevice
  * updated translations
* v0.3.1  07 Nov 2025
  * Updated task panel for cable profile.
  * Updated predefined profiles and presets.
  * Added translation: Belarusian.
  * Minor UI changes and fixes.
* v0.3.0  23 Oct 2025
  * New elements introduced: Electrical Device, CableTerminal, SuppLines.
  * Changed concept for: Cable Box, Cable Connector, Cable Light Point. Introduced presets, support for CableTerminal, SuppLines and non parametric shapes imported from STEP files.
  * New commands for wires introduced: Attach Wire to Terminal, Detach Wire From Terminal.
  * New support commands introduced: Attach In Place, Deactivate Atttachment.
  * Added support for two-color insulation.
  * Added command 'coaxial' in CablesEdit.
  * Added translations: Chinese, Swedish.
* v0.2.1  30 Jun 2025
  * Fixed bug with DraftTools import
  * Updated German translation
  * Updated IFC types
* v0.2.0  14 Jun 2025
  * WireFlex can now take the shape of polyline or bspline.
  * Added option of WireFlex creation from the vertices of another object.
  * Introduced special Edit Mode for WireFlex allowing to add, delete, modify, attach, detach its points preserving all properties. Additionally it is possible to make edges vertical or horizontal with one click in Edit Mode.
  * Introduced colored markings of attached vertices in WireFlex.
  * Added CompoundPath and CableConduit objects which enable the creation of complex bundles.
  * Added undo/redo support.
  * Added commands visibility in console.
  * Added shortcut keys.
  * A few minor bug fixes and improvements.
* v0.1.4  15 Mar 2025
  * Added translations: German, Polish, Spanish
  * ArchCable class: added option to create cable without profile (single wire cable)
  * Workbench files structure has been migrated to "namespaced workbench" new style
  * Some minor fixes and corrections
* v0.1.3  27 Feb 2025
  * Minor fixes and corrections, code prepared for translation
* v0.1.2  25 Jan 2025
  * Added profile selection
* v0.1.1  21 Jan 2025
  * Fixed cable rotation problem
* v0.1.0  21 Jan 2025
  * Initial version

## Donate
If you appreciate my work and would like me to spend more time creating new tools, you can help me increasing my powers by contributing via [github](https://github.com/sponsors/sargo-devel) or [ko-fi](https://ko-fi.com/sargodevel).

## License
LGPLv3 (see [LICENSE](LICENSE))
