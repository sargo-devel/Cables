from setuptools import setup
from freecad.cables.version import __version__

setup(name='freecad.cables',
      version=__version__,
      packages=['freecad',
                'freecad.cables'],
      maintainer="SargoDevel",
      maintainer_email="sargo-devel@o2.pl",
      url="https://github.com/sargo-devel/Cables",
      description="Electrical cables drawing tools workbench for FreeCAD",
      include_package_data=True)
