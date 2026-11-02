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
    carpeta = base / "Calculandia"
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def _clave_nivel(mundo_id, idx):
    return f"{mundo_id}-{idx}"


class Progreso:
    def __init__(self, archivo=None):
        self.archivo = Path(archivo) if archivo else _carpeta() / "progreso.json"
        self.niveles = {}          # "1-0": {"estrellas": 3, "puntos": 120}
        self.cuaderno = []         # [{"clave": {...}, "formula": "...", "repasos": 0}]
        self.todo_desbloqueado = False
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

    def guardar(self):
        datos = {"niveles": self.niveles, "cuaderno": self.cuaderno,
                 "todo_desbloqueado": self.todo_desbloqueado}
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
