"""El mapa de islas no se traba al pasar de una isla a otra.

- Con el mapa quieto, las islas abiertas quedan preparadas de antemano (dibujo, cielo, mar y foto).
- Al deslizarse a una isla preparada no se arma nada nuevo: no se dibuja ninguna isla y se dibuja un
  solo fondo (el de la isla que se deja, para que no salten las nubes).
- Si cambia el progreso en una isla (estrellas, niveles abiertos), su dibujo se rearma.

Correr con:  python tests/test_mapa.py"""

import os
import sys
import tempfile

CARPETA = tempfile.mkdtemp(prefix="derivia_mapa_")
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["APPDATA"] = os.environ["XDG_DATA_HOME"] = CARPETA
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((1280, 720))

from juego import escenas as E  # noqa: E402
from juego.app import App  # noqa: E402
from juego.escenas import mapa as modulo_mapa  # noqa: E402
from juego.mundos import MUNDOS  # noqa: E402


def cuadros(m, n):
    for _ in range(n):
        m.actualizar(1 / 60)
        m.dibujar(m.app.lienzo)


def test_islas_preparadas_y_deslizamiento_sin_armar_nada():
    app = App(pygame.display.get_surface())
    app.progreso.todo_desbloqueado = True
    m = E.Mapa(app, MUNDOS[0].id)
    cuadros(m, 3 * len(MUNDOS) + 40)          # quieto: un pedacito por cuadro
    for i in range(len(MUNDOS)):
        assert m._firma(i) in modulo_mapa._CAPAS, f"la isla {MUNDOS[i].nombre} no quedó preparada"
    armadas, fondos = [], []
    armar, fondo = m._armar_capa, m._dibujar_fondo
    m._armar_capa = lambda idx: armadas.append(idx) or armar(idx)
    m._dibujar_fondo = lambda sup, idx: (fondos.append(idx) if m.desliz else None) or fondo(sup, idx)
    for destino in (1, 2, 3):
        fondos.clear()
        m.ir(destino)
        while m.desliz:
            cuadros(m, 1)
        assert len(fondos) == 1, f"al ir a la isla {destino} se dibujaron {len(fondos)} fondos (debería ser 1)"
    assert not armadas, f"se armaron islas durante el deslizamiento: {armadas}"


def test_el_progreso_cambia_el_dibujo_de_la_isla():
    app = App(pygame.display.get_surface())
    m = E.Mapa(app, MUNDOS[0].id)
    antes = m._capa(0)
    app.progreso.registrar(MUNDOS[0].id, 0, 3, 100)
    assert m._capa(0) is not antes, "ganar un nivel no actualizó el dibujo de la isla"
    assert m._capa(0) is m._capa(0)


def main():
    pruebas = [f for nombre, f in sorted(globals().items()) if nombre.startswith("test_")]
    for f in pruebas:
        f()
        print("  ok", f.__name__)
    print(f"Todo OK ({len(pruebas)} pruebas)")


if __name__ == "__main__":
    main()
