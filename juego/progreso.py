"""Guarda estrellas, niveles desbloqueados y el cuaderno de errores en un JSON."""

import json
import os
from pathlib import Path

from .mundos import MUNDOS

REPASOS_PARA_SACAR = 2   # veces que hay que acertar un ejercicio del cuaderno


def _carpeta():
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    carpeta = base / "Derivia"
    carpeta.mkdir(parents=True, exist_ok=True)
    _migrar(base / "Calculandia" / "progreso.json", carpeta / "progreso.json")
    return carpeta


def _migrar(viejo, nuevo):
    """El juego antes se llamaba Calculandia: si hay progreso viejo y todavía no hay
    nuevo, se copia (el archivo viejo no se toca)."""
    if nuevo.exists() or not viejo.exists():
        return
    try:
        nuevo.write_bytes(viejo.read_bytes())
    except OSError:
        pass


def _clave_nivel(mundo_id, idx):
    return f"{mundo_id}-{idx}"


class Progreso:
    def __init__(self, archivo=None):
        self.archivo = Path(archivo) if archivo else _carpeta() / "progreso.json"
        self.niveles = {}          # "1-0": {"estrellas": 3, "puntos": 120}
        self.cuaderno = []         # [{"clave": {...}, "formula": "...", "repasos": 0}]
        self.todo_desbloqueado = False
        self.sonido = True               # efectos
        self.musica = True
        self.vol_efectos = 0.6
        self.vol_musica = 0.5
        self.pantalla_completa = False
        self.monedas = 0
        self.ropa_comprada = []          # ids de la tienda
        self.ropa_puesta = {}            # lugar -> id
        self.cargar()

    # ------------------------------------------------ disco
    def cargar(self):
        try:
            datos = json.loads(self.archivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self.niveles = datos.get("niveles", {})
        self.cuaderno = datos.get("cuaderno", [])
        self.todo_desbloqueado = datos.get("todo_desbloqueado", False)
        self.sonido = datos.get("sonido", True)
        self.musica = datos.get("musica", True)
        self.vol_efectos = datos.get("vol_efectos", 0.6)
        self.vol_musica = datos.get("vol_musica", 0.5)
        self.pantalla_completa = datos.get("pantalla_completa", False)
        if "monedas" in datos:
            self.monedas = datos["monedas"]
        else:
            # de regalo: lo que sumaste en tus mejores partidas antes de que existiera la tienda
            self.monedas = sum(n.get("puntos", 0) for n in self.niveles.values())
        self.ropa_comprada = datos.get("ropa_comprada", [])
        self.ropa_puesta = datos.get("ropa_puesta", {})

    def guardar(self):
        datos = {"niveles": self.niveles, "cuaderno": self.cuaderno,
                 "todo_desbloqueado": self.todo_desbloqueado, "sonido": self.sonido, "musica": self.musica,
                 "vol_efectos": self.vol_efectos, "vol_musica": self.vol_musica,
                 "pantalla_completa": self.pantalla_completa, "monedas": self.monedas,
                 "ropa_comprada": self.ropa_comprada, "ropa_puesta": self.ropa_puesta}
        tmp = self.archivo.with_suffix(".tmp")
        tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self.archivo)

    # ------------------------------------------------ niveles
    def estrellas(self, mundo_id, idx):
        return self.niveles.get(_clave_nivel(mundo_id, idx), {}).get("estrellas", 0)

    def aprobado(self, mundo_id, idx):
        return _clave_nivel(mundo_id, idx) in self.niveles

    def desbloqueado(self, mundo_id, idx):
        if self.todo_desbloqueado:
            return True
        pos = [m.id for m in MUNDOS].index(mundo_id)
        if idx > 0:
            return self.aprobado(mundo_id, idx - 1)
        if pos == 0:
            return True
        anterior = MUNDOS[pos - 1]
        return self.aprobado(anterior.id, len(anterior.niveles) - 1)

    def mundo_desbloqueado(self, mundo_id):
        return self.desbloqueado(mundo_id, 0)

    def estrellas_mundo(self, mundo_id):
        m = next(m for m in MUNDOS if m.id == mundo_id)
        return sum(self.estrellas(mundo_id, i) for i in range(len(m.niveles))), 3 * len(m.niveles)

    def registrar(self, mundo_id, idx, estrellas, puntos):
        k = _clave_nivel(mundo_id, idx)
        viejo = self.niveles.get(k, {"estrellas": 0, "puntos": 0})
        self.niveles[k] = {"estrellas": max(viejo["estrellas"], estrellas),
                           "puntos": max(viejo["puntos"], puntos)}
        self.guardar()

    # ------------------------------------------------ cuaderno de errores
    def _buscar(self, clave):
        for item in self.cuaderno:
            if item["clave"] == clave:
                return item
        return None

    def anotar_error(self, clave, formula):
        item = self._buscar(clave)
        if item:
            item["repasos"] = 0
        else:
            self.cuaderno.append({"clave": clave, "formula": formula, "repasos": 0})
        self.guardar()

    def anotar_acierto(self, clave):
        """Devuelve True si el ejercicio salió del cuaderno."""
        item = self._buscar(clave)
        if not item:
            return False
        item["repasos"] += 1
        salio = item["repasos"] >= REPASOS_PARA_SACAR
        if salio:
            self.cuaderno.remove(item)
        self.guardar()
        return salio

    def en_cuaderno(self, clave):
        return self._buscar(clave) is not None

    # ------------------------------------------------ monedas y tienda
    def sumar_monedas(self, n):
        self.monedas += max(0, int(n))
        self.guardar()

    def comprar(self, item_id, precio):
        if item_id in self.ropa_comprada or self.monedas < precio:
            return False
        self.monedas -= precio
        self.ropa_comprada.append(item_id)
        self.guardar()
        return True

    def poner(self, lugar, item_id):
        if item_id is None:
            self.ropa_puesta.pop(lugar, None)
        else:
            self.ropa_puesta[lugar] = item_id
        self.guardar()
