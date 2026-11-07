"""Revisar los errores de un nivel al terminarlo."""


import pygame

from .. import lienzo as dibujo
from .. import paisaje, ui
from ..gato import Gato
from ..lienzo import Lienzo
from ..ui import ALTO, ANCHO, DURAZNO, MENTA_OSC, SUAVE, TARJETA, TINTA, Boton
from .base import Escena, letrero


class RevisarErrores(Escena):
    """Los errores del nivel que terminaste: qué pusiste, qué era y por qué."""

    def __init__(self, app, juego, volver):
        super().__init__(app)
        self.j = juego
        self.volver = volver
        self.scroll = 0.0
        self.objetivo = 0.0
        self.gato = Gato(110)
        self.gato.animo_base = "pensando"
        self.gato.animo = "pensando"
        self.tarjetas = [self._tarjeta(e) for e in juego.errores_log]
        self.alto_total = sum(t.get_height() + 16 for t in self.tarjetas)
        self.botones = [Boton((24, 22, 140, 50), "Volver", self.atras, DURAZNO, tam=22)]

    def _tarjeta(self, e):
        w = 980
        partes = [ui.rico(e["consigna"], 16, SUAVE, ancho=w - 40),
                  ui.escalar_a(ui.formula(e["formula"], 30).sup, w - 40),
                  ui.rico(f"**{e['titulo']}**", 20, ui.CORAL_OSC, ancho=w - 40, color_negrita=ui.CORAL_OSC)]
        if e["tuya"]:
            partes.append(ui.rico(f"Pusiste:  {e['tuya']}", 18, TINTA, ancho=w - 40))
        partes.append(ui.rico(f"Era:  {e['correcta']}", 18, MENTA_OSC, ancho=w - 40))
        explicacion = "\n".join(t for t in (e["cuerpo"], e["explicacion"]) if t)
        if explicacion:
            partes.append(ui.rico(explicacion, 16, SUAVE, ancho=w - 40))
        alto = sum(p.get_height() + 6 for p in partes) + 24
        s = Lienzo(*((w, alto)))
        dibujo.rect(s, (226, 210, 180), s.get_rect().move(0, 4), border_radius=16)
        dibujo.rect(s, TARJETA, s.get_rect().inflate(0, -4).move(0, -2), border_radius=16)
        dibujo.rect(s, ui.ARENA_OSC, s.get_rect().inflate(0, -4).move(0, -2), 2, border_radius=16)
        y = 12
        for p in partes:
            s.blit(p, (20, y))
            y += p.get_height() + 6
        return s

    def atras(self):
        self.app.cambiar(self.volver, "fundido")

    def evento(self, e):
        if e.type == pygame.MOUSEWHEEL:
            self.objetivo = max(0, min(max(0, self.alto_total - 520), self.objetivo - e.y * 60))
            return True
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_DOWN, pygame.K_UP):
            self.objetivo = max(0, min(max(0, self.alto_total - 520), self.objetivo + (60 if e.key == pygame.K_DOWN else -60)))
            return True
        return super().evento(e)

    def actualizar(self, dt):
        self.scroll += (self.objetivo - self.scroll) * min(1, dt * 10)
        self.gato.actualizar(dt)

    def dibujar(self, sup):
        sup.blit(paisaje.pergamino(), (0, 0))
        letrero(sup, (ANCHO // 2 - 230, 16, 460, 62), "Revisar errores", 30)
        clip = sup.get_clip()
        sup.set_clip(pygame.Rect(0, 96, ANCHO, ALTO - 96))
        y = 110 - self.scroll
        for t in self.tarjetas:
            sup.blit(t, (ANCHO // 2 - t.get_width() // 2 + 60, y))
            y += t.get_height() + 16
        sup.set_clip(clip)
        if self.alto_total > 560:
            sup.blit(ui.texto("Usá la ruedita del mouse (o las flechas) para ver más", 15, SUAVE, negrita=True),
                     (ANCHO - 450, 66))
        self.gato.dibujar(sup, (90, ALTO - 10))
        self.dibujar_botones(sup)
