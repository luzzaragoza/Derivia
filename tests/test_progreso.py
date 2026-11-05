"""Pruebas del guardado del progreso.

Correr con:  python tests/test_progreso.py"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from juego.progreso import Progreso  # noqa: E402


def _archivo():
    return Path(tempfile.mkdtemp(prefix="derivia_prog_")) / "progreso.json"


def test_primera_vez_valores_de_entrada():
    p = Progreso(_archivo())
    assert p.niveles == {} and p.cuaderno == [] and p.monedas == 0 and p.nombre_gato == ""
    assert p.sonido is True and p.vol_musica == 0.5


def test_las_listas_no_se_comparten_entre_progresos():
    a, b = Progreso(_archivo()), Progreso(_archivo())
    a.ropa_comprada.append("sombrero")
    assert b.ropa_comprada == []


def test_guardar_y_volver_a_cargar():
    arch = _archivo()
    p = Progreso(arch)
    p.registrar("1", 0, 3, 120)
    p.anotar_error({"mundo": "1", "nivel": 0, "gen": "g_potencia", "semilla": 5}, "x^2")
    p.sumar_monedas(40)
    p.nombre_gato = "Miguelona"
    p.vol_efectos = 0.3
    assert p.guardar()
    q = Progreso(arch)
    assert q.estrellas("1", 0) == 3
    assert q.en_cuaderno({"mundo": "1", "nivel": 0, "gen": "g_potencia", "semilla": 5})
    assert q.monedas == 40 and q.nombre_gato == "Miguelona" and q.vol_efectos == 0.3
    assert not arch.with_suffix(".tmp").exists()


def test_datos_con_tipo_raro_se_ignoran():
    arch = _archivo()
    arch.write_text(json.dumps({"monedas": "muchas", "niveles": [], "sonido": 1, "vol_musica": 1,
                                "nombre_gato": "Tito"}), encoding="utf-8")
    p = Progreso(arch)
    assert p.monedas == 0 and p.niveles == {} and p.sonido is True
    assert p.vol_musica == 1 and p.nombre_gato == "Tito"      # un entero sirve como volumen


def test_archivo_danado_queda_aparte():
    arch = _archivo()
    arch.write_text('{"niveles": {"1-0": {"estrell', encoding="utf-8")
    p = Progreso(arch)
    assert p.niveles == {}
    copias = list(arch.parent.glob("progreso_danado_*.json"))
    assert len(copias) == 1 and copias[0].read_text(encoding="utf-8").startswith('{"niveles"')
    assert p.guardar() and json.loads(arch.read_text(encoding="utf-8"))["niveles"] == {}


def test_monedas_de_regalo_si_el_progreso_es_viejo():
    arch = _archivo()
    arch.write_text(json.dumps({"niveles": {"1-0": {"estrellas": 3, "puntos": 100},
                                            "1-1": {"estrellas": 2, "puntos": 50}}}), encoding="utf-8")
    assert Progreso(arch).monedas == 150


def test_borrar_todo_deja_copia_y_mantiene_los_ajustes():
    arch = _archivo()
    p = Progreso(arch)
    p.registrar("1", 0, 3, 120)
    p.sonido, p.teclado_numerico = False, True
    p.guardar()
    respaldo = p.borrar_todo()
    assert respaldo is not None and json.loads(respaldo.read_text(encoding="utf-8"))["niveles"]
    q = Progreso(arch)
    assert q.niveles == {} and q.monedas == 0
    assert q.sonido is False and q.teclado_numerico is True


def test_si_no_se_puede_guardar_el_juego_sigue():
    carpeta = Path(tempfile.mkdtemp(prefix="derivia_prog_"))
    p = Progreso(carpeta / "no_existe" / "progreso.json")      # la carpeta no existe: no se puede escribir
    p.sumar_monedas(10)                                         # no tiene que romper
    assert p.no_se_pudo_guardar and not p.guardar()


def main():
    logging.disable(logging.WARNING)      # los avisos de los casos con error son esperados
    pruebas = [f for nombre, f in sorted(globals().items()) if nombre.startswith("test_")]
    for f in pruebas:
        f()
        print("  ok", f.__name__)
    print(f"Todo OK ({len(pruebas)} pruebas)")


if __name__ == "__main__":
    main()
