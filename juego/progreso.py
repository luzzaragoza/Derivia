"""Guarda estrellas, niveles desbloqueados y el cuaderno de errores en un JSON."""

import contextlib
import json
import logging
import time
from pathlib import Path

from .mundos import MUNDOS
from .rutas import carpeta_datos

log = logging.getLogger(__name__)

REPASOS_PARA_SACAR = 2   # veces que hay que acertar un ejercicio del cuaderno


def _carpeta():
    carpeta = carpeta_datos()
    _migrar(carpeta.parent / "Calculandia" / "progreso.json", carpeta / "progreso.json")
    return carpeta


def _migrar(viejo, nuevo):
    """El juego antes se llamaba Calculandia: si hay progreso viejo y todavía no hay
    nuevo, se copia (el archivo viejo no se toca)."""
    if nuevo.exists() or not viejo.exists():
        return
    with contextlib.suppress(OSError):     # si no se puede copiar, se empieza de cero
        nuevo.write_bytes(viejo.read_bytes())


def _clave_nivel(mundo_id, idx):
    return f"{mundo_id}-{idx}"


# Todo lo que se guarda, con su valor de entrada. Para guardar un dato nuevo alcanza con agregarlo acá
# (las listas y diccionarios van como list/dict para que cada Progreso tenga los suyos).
_CAMPOS = {
    "niveles": dict,               # "1-0": {"estrellas": 3, "puntos": 120}
    "cuaderno": list,              # [{"clave": {...}, "formula": "...", "repasos": 0}]
    "todo_desbloqueado": False,
    "monedas": 0,
    "ropa_comprada": list,         # ids de la tienda
    "ropa_puesta": dict,           # lugar -> id
    "nombre_gato": "",
    "repaso_mundos": list,         # mundos donde ya apareció un repaso del cuaderno
    # ajustes: se mantienen aunque se borre el progreso
    "sonido": True,                # efectos
    "musica": True,
    "vol_efectos": 0.6,
    "vol_musica": 0.5,
    "pantalla_completa": False,
    "teclado_numerico": False,
}
_AJUSTES = {"sonido", "musica", "vol_efectos", "vol_musica", "pantalla_completa", "teclado_numerico"}


def _por_defecto(campo):
    valor = _CAMPOS[campo]
    return valor() if callable(valor) else valor


def _tipo_valido(campo, valor):
    esperado = type(_por_defecto(campo))
    if esperado is float:
        return isinstance(valor, (int, float)) and not isinstance(valor, bool)
    if esperado is int:
        return isinstance(valor, int) and not isinstance(valor, bool)
    return isinstance(valor, esperado)


class Progreso:
    """Estrellas, monedas, ropa, cuaderno de errores y ajustes. Se guarda en un JSON cada vez que cambia."""

    def __init__(self, archivo=None):
        self.archivo = Path(archivo) if archivo else _carpeta() / "progreso.json"
        self.no_se_pudo_guardar = False
        for campo in _CAMPOS:
            setattr(self, campo, _por_defecto(campo))
        self.cargar()

    # ------------------------------------------------ disco
    def cargar(self):
        try:
            texto = self.archivo.read_text(encoding="utf-8")
        except OSError:          # todavía no hay progreso (o no se puede leer): se empieza de cero
            return
        try:
            datos = json.loads(texto)
            if not isinstance(datos, dict):
                raise ValueError("no es un diccionario")
        except ValueError:
            self._apartar_danado()
            return
        for campo in _CAMPOS:
            if campo in datos and _tipo_valido(campo, datos[campo]):
                setattr(self, campo, datos[campo])
        if "monedas" not in datos:
            # de regalo: lo que sumaste en tus mejores partidas antes de que existiera la tienda
            self.monedas = sum(n.get("puntos", 0) for n in self.niveles.values() if isinstance(n, dict))

    def _apartar_danado(self):
        """El archivo está roto (por ejemplo, se cortó la luz justo al guardar): se deja una copia
        aparte en vez de pisarlo, por si se puede rescatar algo a mano."""
        copia = self.archivo.with_name(f"progreso_danado_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json")
        try:
            self.archivo.replace(copia)
            log.warning("El progreso estaba dañado: quedó en %s y se empieza de cero", copia)
        except OSError:
            log.warning("El progreso estaba dañado y no se pudo apartar", exc_info=True)

    def guardar(self):
        """Guarda todo. Primero escribe un archivo aparte y después lo pone en lugar del viejo:
        si algo se corta a la mitad, el progreso anterior queda sano. Si no se puede escribir
        (disco lleno, carpeta sin permiso), el juego sigue andando y devuelve False."""
        datos = {campo: getattr(self, campo) for campo in _CAMPOS}
        tmp = self.archivo.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(self.archivo)
        except OSError:
            log.warning("No se pudo guardar el progreso en %s", self.archivo, exc_info=True)
            self.no_se_pudo_guardar = True
            return False
        self.no_se_pudo_guardar = False
        return True

    def borrar_todo(self):
        """Empieza de cero (niveles, cuaderno, monedas, ropa, nombre del gato). Los ajustes de sonido
        y pantalla se mantienen. Antes guarda una copia de respaldo al lado del archivo.
        Devuelve la ruta de la copia (o None si no había nada que copiar)."""
        respaldo = None
        if self.archivo.exists():
            respaldo = self.archivo.with_name(f"progreso_respaldo_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json")
            try:
                respaldo.write_bytes(self.archivo.read_bytes())
            except OSError:
                respaldo = None
        for campo in _CAMPOS:
            if campo not in _AJUSTES:
                setattr(self, campo, _por_defecto(campo))
        self.guardar()
        return respaldo

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

    def comprar_conjunto(self, piezas, precio):
        """Compra todas las piezas que falten de un conjunto (con descuento)."""
        faltan = [pid for pid in piezas if pid not in self.ropa_comprada]
        if not faltan:
            return True
        if self.monedas < precio:
            return False
        self.monedas -= precio
        self.ropa_comprada.extend(faltan)
        self.guardar()
        return True
