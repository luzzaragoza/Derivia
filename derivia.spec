# -*- mode: python ; coding: utf-8 -*-
# Receta de PyInstaller para armar Derivia (sin consola).
#
# Arma una CARPETA, dist/Derivia/, con Derivia.exe y todo lo que necesita al lado.
# Abre mucho más rápido que un .exe de un solo archivo (no tiene que descomprimirse cada vez)
# y los antivirus lo marcan menos. Para repartirlo, instalador.iss lo empaqueta en un Setup.

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("juego/assets", "juego/assets")],   # tipografía Fredoka One e ícono
    # las pantallas y los generadores se cargan recién al usarlos: hay que avisarle que existen
    hiddenimports=["mpmath", "skia", "juego.app", "juego.autoprueba", "juego.escenas.ayuda", "juego.escenas.base",
                   "juego.escenas.cuaderno", "juego.escenas.desafio", "juego.escenas.fin_nivel",
                   "juego.escenas.mapa", "juego.escenas.menu", "juego.escenas.nivel", "juego.escenas.nivel_pantalla",
                   "juego.escenas.nombre_gato", "juego.escenas.opciones", "juego.escenas.revisar_errores",
                   "juego.escenas.tienda", "juego.ejercicios", "juego.detective", "juego.gen_integrales",
                   "juego.gen_multiples", "matplotlib.backends.backend_agg"],
    excludes=["tkinter", "IPython", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx", "pytest",
              "notebook", "jupyter", "pandas", "scipy"],
    noarchive=False,
)


# De los datos de matplotlib solo hacen falta las fuentes TrueType (DejaVu Sans, Computer Modern y
# STIX, que usa de respaldo para las fórmulas) y el archivo de configuración.
def _no_hace_falta(destino):
    d = destino.replace("\\", "/")
    return d.startswith(("matplotlib/mpl-data/sample_data/", "matplotlib/mpl-data/images/",
                         "matplotlib/mpl-data/fonts/afm/", "matplotlib/mpl-data/fonts/pdfcorefonts/",
                         "matplotlib/mpl-data/stylelib/", "matplotlib/mpl-data/plot_directive/")) \
        or d.startswith("matplotlib/mpl-data/fonts/ttf/DejaVuSerif")


a.datas = [d for d in a.datas if not _no_hace_falta(d[0])]

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
