"""El cuaderno de errores."""

import random

import pygame

from .. import escenas, paisaje, ui
from ..gato import Gato
from ..mundos import mundo_por_id
from ..ui import (
    ALTO,
    ANCHO,
    BORDE,
    CORAL,
    DURAZNO,
    SOL,
    SUAVE,
    TARJETA,
    Boton,
)
from .base import CREMA, Escena, centrar, letrero


class Cuaderno(Escena):
    MAX = 8

    def __init__(self, app):
        super().__init__(app)
        self.items = list(app.progreso.cuaderno)
        self.gato = Gato(120)
        self.gato.animo_base = "normal" if self.items else "dormido"
        self.gato.animo = self.gato.animo_base
        self.botones = [Boton((24, 22, 128, 50), "Menú", self.atras, DURAZNO, tam=22)]
        if self.items:
            self.botones.append(Boton((ANCHO - 330, 640, 300, 60), f"Practicar ({min(len(self.items), self.MAX)})",
                                      self.practicar, CORAL, CREMA, tam=24, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER]))

    def atras(self):
        self.app.cambiar(escenas.Menu(self.app))

    def practicar(self):
        claves = [c["clave"] for c in self.items[:self.MAX]]
        random.shuffle(claves)
        self.app.cambiar(escenas.Juego(self.app, None, None, practica=claves), "ola")

    def actualizar(self, dt):
        self.gato.actualizar(dt)

    def dibujar(self, sup):
        sup.blit(paisaje.pergamino(), (0, 0))
        letrero(sup, (ANCHO // 2 - 230, 16, 460, 62), "Cuaderno de errores", 30)
        sup.blit(ui.rico("Los ejercicios en los que te equivocaste. Cada uno sale cuando lo resolvés **2 veces sin errores** "
                         "(acá o cuando te aparece de repaso en un nivel).", 18, SUAVE, ancho=1180, color_negrita=ui.CORAL_OSC),
                 (40, 90))
        if not self.items:
            s = ui.rico("¡Está vacío! Cuando te equivoques en un ejercicio, va a aparecer acá para que lo repases.",
                        24, SUAVE, ancho=700, centrado=True)
            centrar(sup, s, 260)
            self.gato.dibujar(sup, (ANCHO // 2, 520))
        y = 140
        for item in self.items[:self.MAX]:
            r = pygame.Rect(40, y, ANCHO - 80, 50)
            ui.tarjeta(sup, r, TARJETA, 14, ui.ARENA_OSC, 4)
            c = item["clave"]
            try:
                m = mundo_por_id(c["mundo"])
                lugar = f"{m.nombre} · {m.niveles[c['nivel']].nombre}"
            except (KeyError, IndexError):
                lugar = ""
            sup.blit(ui.texto(lugar, 16, SUAVE, negrita=True), (r.left + 18, r.centery - 10))
            f = ui.escalar_a(ui.formula(item["formula"], 24).sup, 620)
            sup.blit(f, f.get_rect(midleft=(r.left + 380, r.centery)))
            for k in range(2):
                ui.estrella(sup, (r.right - 60 + k * 28, r.centery), 11,
                            SOL if k < item["repasos"] else (232, 222, 200), BORDE, brillo=False)
            y += 60
        if len(self.items) > self.MAX:
            sup.blit(ui.texto(f"…y {len(self.items) - self.MAX} más", 18, SUAVE, negrita=True), (40, 660))
        if self.items:
            self.gato.dibujar(sup, (ANCHO - 420, ALTO - 6), 100)
        self.dibujar_botones(sup)
