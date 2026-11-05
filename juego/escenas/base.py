"""La clase base de las pantallas y piezas de dibujo que usan varias."""


import pygame

from .. import escenas, ui
from ..lienzo import Lienzo
from ..ui import ANCHO, ARENA, BORDE, MADERA_OSC, Boton

CREMA = (255, 248, 230)


def centrar(sup, s, y, x=None):
    r = s.get_rect(midtop=(x if x is not None else ANCHO // 2, y))
    sup.blit(s, r)
    return r


def letrero(sup, rect, texto_s, tam=26):
    """Cartel de madera con un título."""
    rect = pygame.Rect(rect)
    ui.tabla_madera(sup, rect)
    t = ui.texto_borde(texto_s, tam, CREMA, MADERA_OSC, 2)
    sup.blit(t, t.get_rect(center=rect.center))


def dibujar_monedero(sup, monedas, arriba_derecha):
    """Cartelito de madera con las monedas que tenés."""
    t = ui.texto_borde(str(monedas), 24, CREMA, MADERA_OSC, 2)
    r = pygame.Rect(0, 0, t.get_width() + 70, 50)
    r.topright = arriba_derecha
    ui.tabla_madera(sup, r, radio=14)
    ui.moneda(sup, (r.left + 28, r.centery), 15)
    sup.blit(t, t.get_rect(midleft=(r.left + 50, r.centery)))
    return r


class Escena:
    permite_m = True
    musica = "isla"

    def __init__(self, app):
        self.app = app
        self.botones = []

    def evento(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.atras()
            return True
        # list(): un botón puede cambiar la lista al apretarlo (por ejemplo, rearmando la pantalla)
        return any(b.evento(e) for b in list(self.botones))

    def atras(self):
        pass

    def actualizar(self, dt):
        pass

    def dibujar(self, sup):
        pass

    def dibujar_botones(self, sup):
        for b in self.botones:
            b.dibujar(sup)

    def boton_opciones(self, rect):
        icono = Lienzo(*((40, 40)))
        ui.engranaje(icono, (20, 20), 32, BORDE)
        return Boton(rect, icono, self.abrir_opciones, ARENA, relieve=4)

    def abrir_opciones(self):
        self.app.cambiar(escenas.Opciones(self.app, self), None)

    def armar(self):
        pass
