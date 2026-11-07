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

from juego import mundos as mu  # noqa: E402
from juego.mate import ERRORES, C, equivalentes, parsear, x, y  # noqa: E402
from juego.ui import espaciar_integrales  # noqa: E402

_parser = MathTextParser("path")
_vistos = set()


def _chequear_tex(texto):
    trozos = re.findall(r"\$(.+?)\$", texto) if "$" in texto else [texto]
    for trozo in trozos:
        if trozo not in _vistos:
            _parser.parse(f"${espaciar_integrales(trozo)}$", dpi=72)
            _vistos.add(trozo)


def _iguales(paso, a, b):
    if paso.chequeo == "primitiva":
        v = paso.var or x
        return equivalentes(sp.diff(a, v), sp.diff(b, v))
    return equivalentes(a, b)


def _chequear_ejercicio(e):
    _chequear_tex(e.formula)
    for p in e.pasos:
        for t in [p.pregunta, p.explicacion, p.resumen, p.prefijo, p.mostrar, *p.pistas]:
            if t:
                _chequear_tex(t)
        v = p.var or x
        if p.chequeo == "igual" and p.original is not None and p.esperado is not None:
            assert equivalentes(p.esperado, sp.diff(p.original, v)), (e.formula, p.pregunta)
        if p.chequeo == "primitiva":
            assert equivalentes(sp.diff(p.esperado, v), p.integrando), (e.formula, p.pregunta)
        if p.chequeo == "numero":
            assert not sp.sympify(p.esperado).free_symbols, (e.formula, p.esperado)
        if p.tipo == "opcion":
            assert sum(o.correcta for o in p.opciones) == 1, e.formula
            assert len(p.opciones) >= 3 or all(o.texto for o in p.opciones), (e.formula, p.pregunta)
            for o in p.opciones:
                _chequear_tex(o.tex or o.texto)
                if not o.correcta:
                    assert o.error in ERRORES, o.error
        for malo, cod in p.errores:
            assert cod in ERRORES, cod
            assert not _iguales(p, malo, p.esperado), (e.formula, cod)
    verificar = getattr(e, "verificar", None)
    if verificar is not None:
        numerico = complex(verificar())
        final = complex(sp.N(e.pasos[-1].esperado))
        assert abs(numerico - final) < 1e-6 * (1 + abs(final)), (e.formula, numerico, final)


def test_todos_los_niveles(n=60, solo=None):
    rng = random.Random(1234)
    for m in mu.MUNDOS:
        if solo and m.id not in solo:
            continue
        for i, nivel in enumerate(m.niveles):
            for _ in range(n):
                for gen in nivel.generadores:
                    semilla = rng.randrange(10**9)
                    try:
                        _chequear_ejercicio(mu.generar(m.id, i, gen, semilla))
                    except Exception:
                        print("FALLA en", m.id, i, gen, semilla)
                        raise
            assert len(mu.generar_nivel(m.id, i, rng)) == nivel.cantidad, (m.id, i)


def test_misma_semilla_mismo_ejercicio():
    a = mu.generar("3", 1, "g_cadena", 42)
    b = mu.generar("3", 1, "g_cadena", 42)
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
    assert equivalentes(parsear("3x^2y + sen(y)", (x, y)), 3 * x**2 * y + sp.sin(y))
    assert parsear("x^3/3 + C", (x,), True).has(C)
    assert equivalentes(parsear("8pi/3", ()), 8 * sp.pi / 3)


if __name__ == "__main__":
    test_parser()
    test_misma_semilla_mismo_ejercicio()
    test_todos_los_niveles(int(sys.argv[1]) if len(sys.argv) > 1 else 60, sys.argv[2:] or None)
    print("Todo OK")
