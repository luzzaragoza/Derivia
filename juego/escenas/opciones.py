"""Opciones: sonido, música, pantalla completa y borrar progreso."""


import pygame

from .. import escenas, ui
from .. import gato as modulo_gato
from ..fx import rebote
from ..lienzo import Lienzo
from ..sonido import sonidos
from ..ui import ANCHO, CORAL, SUAVE, TARJETA, TINTA, Boton
from .base import CREMA, Escena, letrero


class Opciones(Escena):
    """Se abre encima de la pantalla en la que estabas (la deja en pausa)."""

    def __init__(self, app, previa):
        super().__init__(app)
        self.previa = previa
        self.musica = getattr(previa, "musica", "isla")
        self.foto = app.lienzo.copy()
        velo = Lienzo(*(self.foto.get_size()))
        velo.fill((40, 30, 40, 140))
        self.foto.blit(velo, (0, 0))
        self.t = 0.0
        p = app.progreso
        self.panel = pygame.Rect(ANCHO // 2 - 300, 96, 600, 540)
        x, y = self.panel.left + 50, self.panel.top + 110
        self.controles = [
            ui.Interruptor((x + 380, y, 110, 40), p.musica, self.poner_musica),
            ui.Deslizador((x + 20, y + 66, 470, 14), p.vol_musica, self.vol_musica),
            ui.Interruptor((x + 380, y + 120, 110, 40), p.sonido, self.poner_efectos),
            ui.Deslizador((x + 20, y + 186, 470, 14), p.vol_efectos, self.vol_efectos),
            ui.Interruptor((x + 380, y + 240, 110, 40), p.pantalla_completa, self.poner_pantalla),
        ]
        self.confirmando = False
        self._botones_normales()
        self._habilitar()

    def _botones_normales(self):
        self.confirmando = False
        self.botones = [Boton((self.panel.left + 50, self.panel.bottom - 80, 210, 46), "Borrar progreso",
                              self.preguntar_borrar, (236, 224, 214), ui.ROSA_OSC, tam=17, relieve=4),
                        Boton((self.panel.right - 50 - 220, self.panel.bottom - 86, 220, 58), "Listo", self.atras,
                              CORAL, CREMA, tam=24, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER])]

    def preguntar_borrar(self):
        self.confirmando = True
        cx, y = self.panel.centerx, self.panel.top + 330
        self.botones = [Boton((cx - 250, y, 240, 56), "No, dejalo", self._botones_normales, ui.MENTA, TINTA, tam=21,
                              tecla=[pygame.K_ESCAPE]),
                        Boton((cx + 10, y, 240, 56), "Sí, borrar todo", self.borrar, ui.ROSA, ui.ROSA_OSC, tam=21)]

    def borrar(self):
        self.app.progreso.borrar_todo()
        modulo_gato.ROPA = ()
        modulo_gato._CACHE.clear()
        self.app.cambiar(escenas.NombreGato(self.app, primera_vez=True), "ola")

    def _habilitar(self):
        self.controles[1].habilitado = self.app.progreso.musica
        self.controles[3].habilitado = self.app.progreso.sonido

    def poner_musica(self, v):
        self.app.progreso.musica = v
        sonidos.poner_musica(v)
        self.app.progreso.guardar()
        self._habilitar()

    def poner_efectos(self, v):
        self.app.progreso.sonido = v
        sonidos.poner_efectos(v)
        self.app.progreso.guardar()
        self._habilitar()

    def vol_musica(self, v):
        self.app.progreso.vol_musica = v
        sonidos.poner_volumenes(musica=v)
        self.app.progreso.guardar()

    def vol_efectos(self, v):
        self.app.progreso.vol_efectos = v
        sonidos.poner_volumenes(efectos=v)
        self.app.progreso.guardar()

    def poner_pantalla(self, v):
        self.app.poner_pantalla_completa(v)

    def atras(self):
        self.app.cambiar(self.previa, None)

    def evento(self, e):
        if not self.confirmando:
            for c in self.controles:
                if c.evento(e):
                    return True
        return super().evento(e)

    def actualizar(self, dt):
        self.t += dt

    def dibujar(self, sup):
        sup.blit(self.foto, (0, 0))
        k = rebote(min(1.0, self.t / 0.3))
        panel = self.panel.move(0, int((1 - k) * 60))
        ui.tarjeta(sup, panel, ui.PERGAMINO, 26, ui.ARENA_OSC, 8)
        letrero(sup, (panel.centerx - 160, panel.top - 26, 320, 64), "Opciones", 30)
        x, y = panel.left + 50, panel.top + 110
        filas = [("Música", y), ("Efectos de sonido", y + 120), ("Pantalla completa  (F11)", y + 240)]
        for txt, yy in filas:
            sup.blit(ui.texto(txt, 26, TINTA, negrita=True), (x, yy + 4))
        icono_m = pygame.Rect(x + 300, y + 2, 36, 36)
        ui.parlante(sup, (icono_m.centerx, icono_m.centery), 30, SUAVE, self.app.progreso.musica)
        sup.blit(ui.texto("La tecla M silencia todo de una.", 17, SUAVE), (x, y + 300))
        if self.confirmando:
            ui.tarjeta(sup, panel.inflate(-40, -150).move(0, 30), TARJETA, 22, ui.ROSA_OSC, 6)
            msg = ui.rico("**¿Borrar todo el progreso?**\nSe pierden las estrellas, el cuaderno, las monedas, la ropa "
                          "y el nombre del michi. (Igual queda una copia de respaldo guardada.)",
                          21, TINTA, ancho=460, centrado=True, color_negrita=ui.ROSA_OSC)
            sup.blit(msg, msg.get_rect(midtop=(panel.centerx, panel.top + 130)))
            self.dibujar_botones(sup)
            return
        dy = int((1 - k) * 60)
        for c in self.controles:
            c.rect.move_ip(0, dy)
            c.dibujar(sup)
            c.rect.move_ip(0, -dy)
        self.dibujar_botones(sup)
