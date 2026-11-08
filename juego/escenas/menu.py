"""El menú principal."""

import math
import random

import pygame

from .. import escenas, paisaje, ui
from .. import lienzo as dibujo
from ..gato import Gato
from ..sonido import sonidos
from ..ui import (
    ANCHO,
    ARENA,
    BORDE,
    CORAL,
    LAVANDA,
    MADERA_OSC,
    SOL,
    Boton,
)
from .base import CREMA, Escena, dibujar_monedero


class Menu(Escena):
    def __init__(self, app):
        super().__init__(app)
        self.cielo = paisaje.Cielo(semilla=2)
        self.mar = paisaje.Mar(470)
        self.gato = Gato(170)
        self.gato.reaccionar("feliz", 1.2)
        self.t = 0.0
        self.armar()

    def armar(self):
        app = self.app
        n = len(app.progreso.cuaderno)
        x, y = 690, 236
        self.botones = [
            Boton((x, y, 400, 74), "¡Jugar!", self.jugar, CORAL, CREMA, tam=34, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER]),
            Boton((x, y + 92, 400, 56), f"Tienda de {app.progreso.nombre_gato}" if app.progreso.nombre_gato
                  else "Tienda del michi", lambda: app.cambiar(escenas.Tienda(app), "ola"), (255, 170, 200), tam=24),
            Boton((x, y + 162, 400, 56), f"Cuaderno de errores ({n})", lambda: app.cambiar(escenas.Cuaderno(app)), SOL, tam=23),
            Boton((x, y + 232, 400, 56), "Cómo escribir fórmulas", lambda: app.cambiar(escenas.Ayuda(app)), LAVANDA, tam=23),
            Boton((x, y + 302, 193, 56), "Opciones", self.abrir_opciones, ARENA, tam=22),
            Boton((x + 207, y + 302, 193, 56), "Salir", app.salir, ARENA, tam=22),
        ]

    def _preparar_mapa(self):
        """Cuando terminó la precarga (para no juntar las dos cosas), deja lista la isla del mapa,
        de a un pedacito por cuadro."""
        from ..app import precarga_lista
        if self.t < 1.0 or not precarga_lista():
            return
        if not hasattr(self, "_pasos_mapa"):
            self._pasos_mapa = escenas.Mapa.pasos_para_abrir(self.app)
        if self._pasos_mapa:
            self._pasos_mapa.pop(0)()

    def jugar(self):
        self.app.cambiar(escenas.Mapa(self.app), "ola")

    def atras(self):
        self.app.salir()

    def evento(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect_nombre.collidepoint(e.pos):
            sonidos.tocar("click")
            self.app.cambiar(escenas.NombreGato(self.app), "fundido")
            return True
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect_gato.collidepoint(e.pos):
            sonidos.tocar("miau")
            self.gato.reaccionar(random.choice(["feliz", "sorpresa", "festejo"]), 1.2)
            return True
        return super().evento(e)

    rect_gato = pygame.Rect(150, 420, 220, 240)
    rect_nombre = pygame.Rect(0, 0, 0, 0)

    def actualizar(self, dt):
        self.t += dt
        self._preparar_mapa()
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.gato.actualizar(dt)
        if self.botones[0].rect.collidepoint(dibujo.raton()) and self.gato.animo == "normal":
            self.gato.reaccionar("feliz", 0.8, saltar=False)

    def dibujar(self, sup):
        self.cielo.dibujar(sup)
        self.mar.dibujar(sup)
        paisaje.dibujar_isla(sup, (math.sin(self.t * 0.8) * 2, 470), 520, 230, ui.PASTO, semilla=5, palmeras=2)
        paisaje.dibujar_isla(sup, (1040, 610), 220, 110, ui.PASTO, semilla=9, palmeras=1)
        self.gato.dibujar(sup, (260, 640))
        nombre = self.app.progreso.nombre_gato or "¿Nombre?"
        t = ui.texto_borde(nombre, 22, CREMA, MADERA_OSC, 2)
        self.rect_nombre = pygame.Rect(0, 0, t.get_width() + 40, 42)
        self.rect_nombre.midtop = (260, 666)
        encima = self.rect_nombre.collidepoint(dibujo.raton())
        ui.tabla_madera(sup, self.rect_nombre.move(0, -2 if encima else 0), radio=12)
        sup.blit(t, t.get_rect(center=self.rect_nombre.move(0, -2 if encima else 0).center))
        # título
        titulo = ui.texto_borde("Derivia", 128, SOL, BORDE, 6)
        y = 40 + math.sin(self.t * 1.6) * 6
        sup.blit(titulo, titulo.get_rect(midtop=(430, y)))
        sub = ui.texto_borde("Derivadas e integrales, isla por isla", 26, CREMA, BORDE, 3)
        sup.blit(sub, sub.get_rect(midtop=(430, y + 168)))
        dibujar_monedero(sup, self.app.progreso.monedas, (ANCHO - 24, 24))
        self.dibujar_botones(sup)
