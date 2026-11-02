"""Chequea que el detective de errores tenga sentido:
- hay una sola razón correcta,
- ninguna razón incorrecta es "de la misma familia" que la correcta (serían las dos ciertas),
- ninguna razón incorrecta explica también lo que escribió la persona,
- lo que escribió de verdad está mal (no es otra forma de escribir lo correcto),
- las razones tienen que ver con el ejercicio.

Correr con:  python tests/test_detective.py [cantidad por generador]"""

import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from juego import detective as dt  # noqa: E402
from juego.ejercicios import Ctx  # noqa: E402
from juego.mate import ERRORES  # noqa: E402

TITULO_A_CODIGOS = {}
for codigo, (titulo, _) in ERRORES.items():
    TITULO_A_CODIGOS.setdefault(titulo, set()).add(codigo)


def chequear(gen, semilla):
    ej = gen(Ctx(random.Random(semilla), "tipeo", False, 1))
    p1 = ej.pasos[0]
    assert sum(o.correcta for o in p1.opciones) == 1, "paso 1 sin una única correcta"
    if len(ej.pasos) == 1:
        return "bien"
    p2 = ej.pasos[1]
    correctas = [o for o in p2.opciones if o.correcta]
    assert len(correctas) == 1, f"{len(correctas)} razones correctas"
    assert len({o.texto for o in p2.opciones}) == len(p2.opciones), "razones repetidas"
    fam = lambda t: {dt.FAMILIA.get(c, c) for c in TITULO_A_CODIGOS[t]}  # noqa: E731
    fam_ok = fam(correctas[0].texto)
    for o in p2.opciones:
        if not o.correcta:
            assert not (fam(o.texto) & fam_ok), f"'{o.texto}' es de la misma familia que '{correctas[0].texto}'"
            assert any(dt._pega(c, ej.formula, getattr(ej, "base", "")) for c in TITULO_A_CODIGOS[o.texto]), \
                f"'{o.texto}' no tiene que ver con {ej.formula}"
    # lo mostrado tiene que estar mal
    mostrado = re.search(r"\$(.+?)\$", p1.pregunta).group(1)
    correcto = re.search(r"Lo correcto era: \$(.+?)\$", p2.explicacion).group(1)
    assert mostrado != correcto, "muestra la respuesta correcta como si estuviera mal"
    return "error"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    fallas = 0
    for gen in dt.GENERADORES_DETECTIVE:
        cuenta = {"bien": 0, "error": 0}
        for s in range(n):
            try:
                cuenta[chequear(gen, s)] += 1
            except AssertionError as e:
                fallas += 1
                if fallas <= 15:
                    print(f"FALLA {gen.__name__} semilla {s}: {e}")
        print(f"{gen.__name__}: {cuenta['error']} con error, {cuenta['bien']} que estaban bien")
    print("Todo OK" if not fallas else f"{fallas} fallas")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
