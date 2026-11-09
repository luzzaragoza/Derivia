"""El teclado de fórmulas (tipo calculadora) escribe cosas que el juego entiende.

- Cada tecla de función deja el cursor en su casillero y, al completarla, la fórmula se entiende.
- En una fracción (tecla □/□), → pasa del numerador al denominador y ← vuelve, como en la calculadora.

Correr con:  python tests/test_teclado.py"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame  # noqa: E402

pygame.init()
pygame.display.set_mode((64, 64))

from juego.escenas.nivel_pantalla import TECLAS_FUNCIONES, TECLAS_OPERACIONES  # noqa: E402
from juego.mate import parsear, x  # noqa: E402
from juego.ui import CampoTexto  # noqa: E402


def campo():
    return CampoTexto((0, 0, 400, 58))


def test_cada_tecla_de_funcion_se_entiende():
    for tecla in TECLAS_FUNCIONES + TECLAS_OPERACIONES:
        c = campo()
        c.insertar("2")
        c.insertar(tecla.texto, tecla.retroceso)
        if tecla.texto == "raiz[]()":          # raíz enésima: primero el índice, → y adentro
            c.insertar("3")
            c.derecha()
        if tecla.texto == "()/()":             # fracción: numerador, → y denominador
            c.insertar("1")
            c.derecha()
        if tecla.texto != ")":
            c.insertar("x")
        if tecla.texto == "(":
            c.insertar(")")
        if tecla.texto == ")":
            c.poner("(2x)")
        parsear(c.texto, (x,))                 # no tiene que tirar ErrorEntrada


def test_flechas_en_la_fraccion():
    c = campo()
    c.insertar("()/()", 4)
    c.insertar("x+1")
    c.derecha()
    c.insertar("x")
    assert c.texto == "(x+1)/(x)", c.texto
    c.izquierda()                              # vuelve a antes de la x del denominador...
    c.izquierda()                              # ...y de ahí directo al final del numerador
    c.insertar("2")
    assert c.texto == "(x+12)/(x)", c.texto


def main():
    pruebas = [f for nombre, f in sorted(globals().items()) if nombre.startswith("test_")]
    for f in pruebas:
        f()
        print("  ok", f.__name__)
    print(f"Todo OK ({len(pruebas)} pruebas)")


if __name__ == "__main__":
    main()
