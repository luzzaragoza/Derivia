"""La tienda del michi: ropa y conjuntos."""

import math

import pygame

from .. import escenas, paisaje, pincel, ropa, ui
from .. import gato as modulo_gato
from .. import lienzo as dibujo
from ..fx import Efectos
from ..gato import Gato
from ..lienzo import Lienzo
from ..sonido import sonidos
from ..ui import (
    ALTO,
    ANCHO,
    ARENA,
    BORDE,
    CORAL,
    DURAZNO,
    MENTA_OSC,
    SOL,
    SUAVE,
    TARJETA,
    TINTA,
    Boton,
)
from .base import CREMA, Escena, dibujar_monedero, letrero


class Tienda(Escena):
    COLS, FILAS = 5, 4

    def __init__(self, app):
        super().__init__(app)
        self.cielo = paisaje.Cielo(semilla=8, nubes=4)
        self.mar = paisaje.Mar(400)
        self.gato = Gato(250)
        self.gato.reaccionar("feliz", 1.2)
        self.fx = Efectos()
        self.lugar = "conjuntos"
        self.sel = None              # id de prenda o de conjunto que se está probando
        self.t = 0.0
        self.mensaje = "¡Elegí algo para probarle!"
        self.armar()

    @property
    def prog(self):
        return self.app.progreso

    def atras(self):
        self.app.cambiar(escenas.Menu(self.app), "ola")

    def _sincronizar(self):
        modulo_gato.ROPA = tuple(self.prog.ropa_puesta.values())

    # ---- conjuntos y prendas con la misma interfaz
    def _piezas(self, item_id):
        c = ropa.CONJUNTO_POR_ID.get(item_id)
        return c.piezas if c else (item_id,)

    def _precio(self, item_id):
        c = ropa.CONJUNTO_POR_ID.get(item_id)
        return c.precio if c else ropa.POR_ID[item_id].precio

    def _nombre(self, item_id):
        c = ropa.CONJUNTO_POR_ID.get(item_id)
        return c.nombre if c else ropa.POR_ID[item_id].nombre

    def _tiene(self, item_id):
        return all(p in self.prog.ropa_comprada for p in self._piezas(item_id))

    def _puesto(self, item_id):
        return all(self.prog.ropa_puesta.get(ropa.POR_ID[p].lugar) == p for p in self._piezas(item_id))

    def _probando(self):
        puesta = dict(self.prog.ropa_puesta)
        if self.sel:
            for p in self._piezas(self.sel):
                puesta[ropa.POR_ID[p].lugar] = p
        return tuple(puesta.values())

    def _items(self):
        if self.lugar == "conjuntos":
            return [c.id for c in ropa.CONJUNTOS]
        return [p.id for p in ropa.CATALOGO if p.lugar == self.lugar]

    def _tarjeta(self, item_id, w, h):
        s = Lienzo(*((w, h)))
        img = modulo_gato.superficie(66, "normal", ropa=self._piezas(item_id))
        s.blit(img, img.get_rect(midtop=(w // 2, -10)))
        nombre = ui.escalar_a(ui.texto(self._nombre(item_id), 13, TINTA, negrita=True), w - 6)
        s.blit(nombre, nombre.get_rect(midtop=(w // 2, h - 38)))
        if self._puesto(item_id):
            et = ui.texto("¡Puesto!", 14, MENTA_OSC, negrita=True)
            s.blit(et, et.get_rect(midtop=(w // 2, h - 20)))
        elif self._tiene(item_id):
            et = ui.texto("Es tuyo", 14, ui.LAVANDA_OSC, negrita=True)
            s.blit(et, et.get_rect(midtop=(w // 2, h - 20)))
        else:
            precio = self._precio(item_id)
            et = ui.texto(str(precio), 15, ui.SOL_OSC if self.prog.monedas >= precio else SUAVE, negrita=True)
            ancho = et.get_width() + 20
            x = w // 2 - ancho // 2
            ui.moneda(s, (x + 7, h - 11), 8)
            s.blit(et, (x + 18, h - 20))
        return s

    def armar(self):
        self.botones = [Boton((24, 22, 128, 50), "Menú", self.atras, DURAZNO, tam=22),
                        self.boton_opciones((ANCHO - 76, 22, 56, 50))]
        pestañas = [("conjuntos", "Conjuntos")] + ropa.LUGARES
        x0, ancho_p = 566, 82
        for k, (clave, nombre) in enumerate(pestañas):
            self.botones.append(Boton((x0 + k * (ancho_p + 4), 110, ancho_p, 42), nombre,
                                      (lambda c=clave: self.elegir_lugar(c)),
                                      SOL if clave == self.lugar else ARENA, tam=13, relieve=4, sonido="tecla", radio=12))
        w, h = 128, 116
        for k, item in enumerate(self._items()[:self.COLS * self.FILAS]):
            fila, col = divmod(k, self.COLS)
            rect = (x0 + col * (w + 8), 166 + fila * (h + 10), w, h)
            color = (226, 246, 210) if self._puesto(item) else ((255, 236, 196) if item == self.sel else TARJETA)
            self.botones.append(Boton(rect, self._tarjeta(item, w - 10, h - 8), (lambda i=item: self.tocar(i)), color,
                                      radio=14, relieve=4, sonido="tecla"))
        if self.sel and not self._tiene(self.sel):
            alcanza = self.prog.monedas >= self._precio(self.sel)
            self.botones.append(Boton((90, 602, 380, 64), f"Comprar · {self._precio(self.sel)}", self.comprar, CORAL,
                                      CREMA, tam=26, habilitado=alcanza, sonido=None))
        if self.prog.ropa_puesta:
            self.botones.append(Boton((180, 676, 200, 38), "Sacarle todo", self.sacar_todo, ARENA, tam=16, relieve=4))

    def elegir_lugar(self, clave):
        self.lugar = clave
        self.armar()

    def tocar(self, item_id):
        nombre = self._nombre(item_id)
        if self._tiene(item_id):
            if self._puesto(item_id):
                for p in self._piezas(item_id):
                    self.prog.poner(ropa.POR_ID[p].lugar, None)
                self.mensaje = f"Le sacaste: {nombre}"
                self.gato.reaccionar("sorpresa", 0.8, saltar=False)
            else:
                for p in self._piezas(item_id):
                    self.prog.poner(ropa.POR_ID[p].lugar, p)
                self.mensaje = f"¡Le pusiste: {nombre}!"
                self.gato.reaccionar("feliz", 1.0)
                sonidos.tocar("estrella", 0.6)
            self.sel = None
            self._sincronizar()
        else:
            self.sel = item_id
            faltan = self._precio(item_id) - self.prog.monedas
            self.mensaje = (f"Probándose: {nombre}" if faltan <= 0 else f"Te faltan {faltan} monedas para: {nombre}")
            self.gato.reaccionar("sorpresa" if faltan > 0 else "feliz", 0.9, saltar=faltan <= 0)
        self.armar()

    def comprar(self):
        item = self.sel
        ok = self.prog.comprar_conjunto(self._piezas(item), self._precio(item))
        if ok:
            for p in self._piezas(item):
                self.prog.poner(ropa.POR_ID[p].lugar, p)
            self._sincronizar()
            sonidos.tocar("desbloqueo")
            sonidos.tocar("miau")
            sonidos.agachar(1.2)
            self.fx.confeti(270, 420, 60, 1.0)
            self.fx.chispas(270, 460, 24, ui.SOL, 300)
            self.fx.texto(270, 330, f"−{self._precio(item)}", ui.SOL, 40, sube=30, dur=1.5)
            self.gato.reaccionar("festejo", 2.0)
            self.mensaje = f"¡Compraste: {self._nombre(item)}!"
            self.sel = None
        else:
            sonidos.tocar("mal")
        self.armar()

    def sacar_todo(self):
        for lugar in list(self.prog.ropa_puesta):
            self.prog.poner(lugar, None)
        self.sel = None
        self._sincronizar()
        self.mensaje = "¡Al natural!"
        self.armar()

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.gato.actualizar(dt)
        self.fx.actualizar(dt)
        self.gato.ropa = self._probando() if self.sel else None

    def dibujar(self, sup):
        self.cielo.dibujar(sup, sol=False)
        self.mar.dibujar(sup)
        pts = [(0, ALTO)] + [(x, 520 + 10 * math.sin(x / 70 + 1)) for x in range(0, 561, 20)] + [(560, ALTO)]
        dibujo.polygon(sup, ui.ARENA, pts)
        dibujo.lines(sup, ui.ESPUMA, False, pts[1:-1], 5)
        pieza, m = pincel.pedestal(300, 84, CORAL) if pincel.HAY_SKIA else (None, 0)
        if pieza is not None:
            sup.blit(pieza, (120 - m, 528 - m))
        else:
            dibujo.ellipse(sup, BORDE, (120, 528, 300, 70))
            dibujo.ellipse(sup, CORAL, (124, 528, 292, 62))
            dibujo.ellipse(sup, (255, 170, 150), (150, 538, 240, 42), 4)
        self.gato.dibujar(sup, (270, 566))
        nombre = self.app.progreso.nombre_gato
        letrero(sup, (ANCHO // 2 - 250, 16, 500, 64), f"Tienda de {nombre}" if nombre else "Tienda del michi", 30)
        dibujar_monedero(sup, self.prog.monedas, (ANCHO - 92, 22))
        msg = ui.rico(self.mensaje, 20, TINTA, ancho=380, centrado=True)
        caja = pygame.Rect(0, 0, 420, msg.get_height() + 28)
        caja.midtop = (270, 100)
        ui.globo(sup, caja, (330, 200), TARJETA)
        sup.blit(msg, msg.get_rect(center=caja.center))
        panel = pygame.Rect(552, 96, 708, 610)
        ui.tarjeta(sup, panel, ui.PERGAMINO, 24, ui.ARENA_OSC, 6)
        if self.lugar == "conjuntos":
            nota = ui.texto("Los conjuntos traen varias prendas juntas, más baratas que por separado.", 14, SUAVE)
            sup.blit(nota, (566, 684))
        self.dibujar_botones(sup)
        self.fx.dibujar(sup)
