# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller para armar Derivia (sin consola).
#
# Arma una CARPETA, dist/Derivia/, con Derivia.exe y todo lo que necesita al lado.
# Abre mucho más rápido que un .exe de un solo archivo (no tiene que descomprimirse cada vez)
# y los antivirus lo marcan menos. Para repartirlo, instalador.iss lo empaqueta en un Setup.

from PyInstaller.utils.hooks import collect_data_files

datos = collect_data_files("matplotlib", subdir="mpl-data/fonts")
datos += [("juego/assets", "juego/assets")]   # tipografía Fredoka One e ícono

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datos,
    hiddenimports=["mpmath", "juego.app", "skia"],
    excludes=["tkinter", "IPython", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx", "pytest",
              "notebook", "jupyter", "pandas", "scipy"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Derivia",
    icon="juego/assets/derivia.ico",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Derivia",
)
