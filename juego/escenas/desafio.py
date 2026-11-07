"""La presentación del desafío del jefe."""


import pygame

from .. import escenas, ui
from ..fx import rebote
from ..lienzo import Lienzo
from ..mundos import VIDAS_DESAFIO, monedas_de_regalo
from ..sonido import sonidos
from ..ui import ANCHO, ARENA, CORAL, TINTA, Boton
from .base import CREMA, Escena, letrero


class DesafioIntro(Escena):
    """Explica el desafío (saltear el mundo peleando con el jefe) antes de empezar."""

    def __init__(self, app, previa, mundo):
        super().__init__(app)
        self.previa, self.mundo = previa, mundo
        self.musica = getattr(previa, "musica", "isla")
        self.foto = app.lienzo.copy()
        velo = Lienzo(*(self.foto.get_size()))
        velo.fill((40, 30, 40, 150))
        self.foto.blit(velo, (0, 0))
        self.t = 0.0
        self.panel = pygame.Rect(ANCHO // 2 - 330, 110, 660, 500)
        n = sum(1 for nv in mundo.niveles if not nv.jefe) + 3
        self.texto = ui.rico(
            f"**¿Te animás a saltear el {mundo.nombre}?**\n"
            f"Peleás directo contra el jefe: **{n} ejercicios** (uno de cada nivel y {3} del jefe), "
            f"**sin pistas**, sin saltear y con **solo {VIDAS_DESAFIO} vidas**.\n\n"
            f"Si ganás: todos los niveles quedan con **3 estrellas**, te llevás "
            f"**+{monedas_de_regalo(mundo, app.progreso)} monedas** de regalo y se abre el mundo siguiente.\n"
            "Si perdés, no perdés nada: podés volver a intentar o jugar el mundo normal.",
            21, TINTA, ancho=560, centrado=True, color_negrita=ui.CORAL_OSC)
        cx, y = self.panel.centerx, self.panel.bottom - 88
        self.botones = [Boton((cx - 250, y, 240, 60), "Mejor no", self.atras, ARENA, TINTA, tam=21,
                              tecla=[pygame.K_ESCAPE]),
                        Boton((cx + 10, y, 240, 60), "¡Vamos!", self.empezar, CORAL, CREMA, tam=23,
                              tecla=[pygame.K_RETURN, pygame.K_KP_ENTER])]

    def empezar(self):
        sonidos.tocar("jefe")
        self.app.cambiar(escenas.Juego(self.app, self.mundo.id, None, desafio=True), "ola")

    def atras(self):
        self.app.cambiar(self.previa, None)

    def actualizar(self, dt):
        self.t += dt

    def dibujar(self, sup):
        sup.blit(self.foto, (0, 0))
        k = rebote(min(1.0, self.t / 0.3))
        panel = self.panel.move(0, int((1 - k) * 60))
        ui.tarjeta(sup, panel, ui.PERGAMINO, 26, ui.ARENA_OSC, 8)
        letrero(sup, (panel.centerx - 200, panel.top - 26, 400, 64), "Desafío del jefe", 28)
        sup.blit(self.texto, self.texto.get_rect(midtop=(panel.centerx, panel.top + 70)))
        self.dibujar_botones(sup)
