# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller para armar Derivia.exe (un solo archivo, sin consola).

from PyInstaller.utils.hooks import collect_data_files

datos = collect_data_files("matplotlib", subdir="mpl-data/fonts")
datos += [("juego/assets", "juego/assets")]   # tipografía Fredoka One

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datos,
    hiddenimports=["mpmath", "juego.app"],
    excludes=["tkinter", "IPython", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx", "pytest",
              "notebook", "jupyter", "pandas", "scipy"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Derivia",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
