from setuptools import setup
import os

version_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            "freecad", "cables", "version.py")
with open(version_path) as fp:
    exec(fp.read())

setup(name='freecad.cables',
      version=str(__version__),
      packages=['freecad',
                'freecad.cables'],
      maintainer="SargoDevel",
      maintainer_email="sargo-devel@o2.pl",
      url="https://github.com/sargo-devel/Cables",
      description="Electrical cables drawing tools workbench for FreeCAD",
      include_package_data=True)
