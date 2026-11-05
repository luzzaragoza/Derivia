"""Ponerle (o cambiarle) el nombre al gato."""

import math

import pygame

from .. import escenas, paisaje, ui
from ..fx import Efectos
from ..gato import Gato
from ..sonido import sonidos
from ..ui import (
    ARENA,
    BORDE,
    CORAL,
    DURAZNO,
    SOL,
    SUAVE,
    Boton,
    CampoTexto,
)
from .base import CREMA, Escena


class NombreGato(Escena):
    permite_m = False
    SUGERENCIA = "Derivia"

    def __init__(self, app, primera_vez=False):
        super().__init__(app)
        self.primera_vez = primera_vez
        self.cielo = paisaje.Cielo(semilla=11)
        self.mar = paisaje.Mar(470)
        self.gato = Gato(220)
        self.gato.reaccionar("sorpresa" if primera_vez else "feliz", 1.5)
        self.fx = Efectos()
        self.t = 0.0
        self.saliendo = None
        self.campo = CampoTexto((560, 300, 520, 62), al_enter=self.listo, al_cambiar=self._cambio,
                                placeholder="Nombre del michi", largo_max=14)
        self.campo.fredoka = True
        self.campo.poner(app.progreso.nombre_gato or "")
        pygame.key.start_text_input()
        self.armar()

    def armar(self):
        self.botones = []
        if not self.primera_vez:
            self.botones.append(Boton((24, 22, 128, 50), "Volver", self.atras, DURAZNO, tam=22))
        x0 = 560
        self.botones.append(Boton((x0 + 176, 410, 164, 50), self.SUGERENCIA,
                                  (lambda: self.campo.poner(self.SUGERENCIA)), ARENA, tam=20, relieve=4, sonido="tecla"))
        self.boton_listo = Boton((x0 + 90, 548, 340, 66), "¡Listo!", self.listo, CORAL, CREMA, tam=28,
                                 habilitado=bool(self.campo.texto.strip()))
        self.botones.append(self.boton_listo)

    def _cambio(self, texto):
        if hasattr(self, "boton_listo"):
            self.boton_listo.habilitado = bool(texto.strip())
        if texto and self.gato.animo == "normal":
            self.gato.reaccionar("feliz", 0.6, saltar=False)

    def atras(self):
        if not self.primera_vez:
            self.app.cambiar(escenas.Menu(self.app), "fundido")

    def listo(self):
        nombre = " ".join(self.campo.texto.split())[:14]
        if not nombre or self.saliendo is not None:
            return
        self.app.progreso.nombre_gato = nombre
        self.app.progreso.guardar()
        sonidos.tocar("miau")
        sonidos.tocar("estrella", 0.6)
        self.gato.reaccionar("festejo", 2)
        self.fx.confeti(300, 420, 60, 1.0)
        self.fx.texto(300, 230, f"¡Hola, {nombre}!", ui.SOL, 40, sube=30, dur=1.6)
        self.saliendo = 1.4

    def evento(self, e):
        if self.saliendo is None and self.campo.evento(e):
            return True
        return super().evento(e)

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.gato.actualizar(dt)
        self.fx.actualizar(dt)
        self.campo.actualizar(dt)
        if self.saliendo is not None:
            self.saliendo -= dt
            if self.saliendo <= 0:
                self.saliendo = None
                self.app.cambiar(escenas.Menu(self.app), "ola")

    def dibujar(self, sup):
        self.cielo.dibujar(sup)
        self.mar.dibujar(sup)
        paisaje.dibujar_isla(sup, (40, 500), 520, 210, ui.PASTO, semilla=5, palmeras=2)
        self.gato.dibujar(sup, (300, 640))
        titulo = "¡Hola! ¿Cómo se llama tu michi?" if self.primera_vez else "¿Cómo se llama tu michi?"
        t = ui.texto_borde(titulo, 40, SOL, BORDE, 4)
        sup.blit(t, t.get_rect(midtop=(820, 120 + math.sin(self.t * 1.6) * 4)))
        sub = ui.texto_borde("Te va a acompañar en todas las islas.", 22, CREMA, BORDE, 2)
        sup.blit(sub, sub.get_rect(midtop=(820, 186)))
        rect = pygame.Rect(530, 270, 580, 370)
        ui.tarjeta(sup, rect, ui.PERGAMINO, 24, ui.ARENA_OSC, 6)
        self.campo.dibujar(sup)
        sup.blit(ui.texto("Sugerencia:", 18, SUAVE, negrita=True), (560, 422))
        self.dibujar_botones(sup)
        self.fx.dibujar(sup)
