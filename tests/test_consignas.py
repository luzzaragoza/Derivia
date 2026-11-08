"""Las consignas dicen lo que corresponde según el tipo de pregunta.

- El aviso "(podés agregar + C o no)" va solo cuando hay que tipear la integral: en las opciones el
  + C ya viene escrito.

Correr con:  python tests/test_consignas.py"""

import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from juego.ejercicios import AVISO_C  # noqa: E402
from juego.mundos import MUNDOS, generar_nivel  # noqa: E402


def test_aviso_de_c_solo_al_tipear():
    vistos = {"opcion": 0, "expresion": 0}
    for m in MUNDOS:
        for i, _nivel in enumerate(m.niveles):
            for semilla in range(3):
                for ej in generar_nivel(m.id, i, rng=random.Random(semilla)):
                    for p in ej.pasos:
                        if AVISO_C in p.pregunta:
                            assert p.tipo == "expresion", f"{m.nombre} nivel {i + 1}: aviso de + C con opciones"
                            vistos["expresion"] += 1
                        elif p.chequeo == "primitiva" and p.tipo == "opcion":
                            vistos["opcion"] += 1
    assert vistos["expresion"] and vistos["opcion"], vistos


def main():
    test_aviso_de_c_solo_al_tipear()
    print("Todo OK")


if __name__ == "__main__":
    main()
