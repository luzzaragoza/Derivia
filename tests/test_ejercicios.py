"""Genera muchos ejercicios de cada nivel y chequea que todo sea correcto:
- la respuesta esperada es de verdad la derivada,
- ningún "error típico" ni distractor da bien por casualidad,
- todas las fórmulas se pueden dibujar.

Correr con:  python tests/test_ejercicios.py"""

import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import sympy as sp  # noqa: E402
from matplotlib.mathtext import MathTextParser  # noqa: E402

from juego import ejercicios as ej  # noqa: E402
from juego.mate import ERRORES, equivalentes, parsear, x  # noqa: E402

_parser = MathTextParser("path")
_vistos = set()


def _chequear_tex(texto):
    trozos = re.findall(r"\$(.+?)\$", texto) if "$" in texto else [texto]
    for trozo in trozos:
        if trozo not in _vistos:
            _parser.parse(f"${trozo}$", dpi=72)
            _vistos.add(trozo)


def _chequear_ejercicio(e):
    _chequear_tex(e.formula)
    for p in e.pasos:
        for t in [p.pregunta, p.explicacion, p.resumen, p.prefijo, *p.pistas]:
            if t:
                _chequear_tex(t)
        if p.original is not None and p.esperado is not None:
            assert equivalentes(p.esperado, sp.diff(p.original, x)), (e.formula, p.pregunta)
        if p.tipo == "opcion":
            assert sum(o.correcta for o in p.opciones) == 1, e.formula
            assert len(p.opciones) >= 3, (e.formula, p.pregunta)
            for o in p.opciones:
                _chequear_tex(o.tex or o.texto)
                if not o.correcta:
                    assert o.error in ERRORES, o.error
        for malo, cod in p.errores:
            assert cod in ERRORES, cod
            assert not equivalentes(malo, p.esperado), (e.formula, cod)


def test_todos_los_niveles(n=60):
    rng = random.Random(1234)
    for m in ej.MUNDOS:
        for i, nivel in enumerate(m.niveles):
            for _ in range(n):
                for gen in nivel.generadores:
                    _chequear_ejercicio(ej.generar(m.id, i, gen.__name__, rng.randrange(10**9)))
            assert len(ej.generar_nivel(m.id, i, rng)) == nivel.cantidad, (m.id, i)


def test_misma_semilla_mismo_ejercicio():
    a = ej.generar("3", 1, "g_cadena", 42)
    b = ej.generar("3", 1, "g_cadena", 42)
    assert a.formula == b.formula


def test_parser():
    casos = {
        "2xcos(x^2)": 2 * x * sp.cos(x**2),
        "sen^2(x)": sp.sin(x)**2,
        "xsen(x)": x * sp.sin(x),
        "e^(2x)": sp.exp(2 * x),
        "3x²-2cos x": 3 * x**2 - 2 * sp.cos(x),
        "ln(x)/x": sp.log(x) / x,
        "raiz(x)": sp.sqrt(x),
        "0,5x": x / 2,
        "-sen(x)": -sp.sin(x),
        "1/(2raiz(x))": 1 / (2 * sp.sqrt(x)),
        "(x^2+1)^3": (x**2 + 1)**3,
        "x^(-2)": x**-2,
        "e^x": sp.exp(x),
        "2e^(3x)sen(x)": 2 * sp.exp(3 * x) * sp.sin(x),
        "cos(x^2)·2x": 2 * x * sp.cos(x**2),
    }
    for texto, esperado in casos.items():
        assert equivalentes(parsear(texto), esperado), texto


if __name__ == "__main__":
    test_parser()
    test_misma_semilla_mismo_ejercicio()
    test_todos_los_niveles()
    print("Todo OK")
