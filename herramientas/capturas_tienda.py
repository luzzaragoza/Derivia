"""Saca capturas de pantalla de Derivia para la ficha de la Microsoft Store (1920×1080).

    python herramientas/capturas_tienda.py

Las deja en tienda/capturas/. Usa un progreso de mentira (en una carpeta temporal):
no toca tu progreso de verdad."""

import os
import random
import sys
import tempfile

CARPETA = tempfile.mkdtemp(prefix="derivia_capturas_")
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["APPDATA"] = CARPETA
os.environ["XDG_DATA_HOME"] = CARPETA
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

TAM = (1920, 1080)
pygame.init()
pygame.display.set_mode(TAM)

from juego import escenas as E  # noqa: E402
from juego.app import App  # noqa: E402
from juego.mundos import MUNDOS  # noqa: E402

SALIDA = os.path.join(RAIZ, "tienda", "capturas")


def foto(app, escena, nombre, preparar=None):
    app.escena = escena
    app.transicion = None
    for _ in range(40):                       # que terminen las animaciones de entrada
        escena.actualizar(1 / 30)
    if preparar:
        preparar(escena)
    if hasattr(escena, "cartel"):
        escena.cartel, escena.t_cartel = None, 99
    escena.dibujar(app.lienzo)
    app._componer(1 / 60)
    pygame.image.save(pygame.display.get_surface(), os.path.join(SALIDA, nombre))
    print("  ", nombre)


def nivel(app, mundo, idx, paso=0, semilla=1):
    random.seed(semilla)
    m = MUNDOS[mundo]
    j = E.Juego(app, m.id, idx)
    for i, ej in enumerate(j.ejercicios):     # un ejercicio que tenga ese paso
        if len(ej.pasos) > paso:
            j.i = i
            break
    j.empezar_ejercicio()
    j.paso_i = paso
    j.empezar_paso()
    j.charla = None
    j.armar()
    return j


def main():
    os.makedirs(SALIDA, exist_ok=True)
    app = App(pygame.display.get_surface())
    p = app.progreso
    p.nombre_gato = "Miguelona"
    p.monedas = 340
    for m in MUNDOS[:3]:                      # algo de progreso: los primeros mundos con estrellas
        for i in range(len(m.niveles) - (1 if m is MUNDOS[2] else 0)):
            p.registrar(m.id, i, 3 if (i + len(m.id)) % 3 else 2, 100)
    app.cambiar = lambda *a, **k: None
    print("Capturas en", SALIDA)
    foto(app, E.Menu(app), "1-menu.png")
    foto(app, E.Mapa(app, MUNDOS[2].id), "2-mapa.png")

    def con_error(j):
        j.feedback = dict(tipo="mal", titulo="Uy, casi. Te faltó la derivada de adentro.",
                          cuerpo="En la regla de la cadena se multiplica por la derivada de lo de adentro. "
                                 "**¡Probá de nuevo!**")
        j.armar()
    foto(app, nivel(app, 2, 0, paso=2, semilla=4), "3-cadena-paso-a-paso.png", con_error)
    j = nivel(app, 7, 1, paso=3, semilla=1)
    # escribe la respuesta correcta, como la tipearía alguien
    respuesta = str(j.paso.esperado).replace("**", "^").replace("exp(x)", "e^x").replace("*", "")
    foto(app, j, "4-integral-por-partes.png", lambda j: j.campo.poner(respuesta))
    foto(app, nivel(app, 8, 2, semilla=3), "5-integral-doble.png")
    foto(app, E.Tienda(app), "6-tienda-del-michi.png")


if __name__ == "__main__":
    main()
