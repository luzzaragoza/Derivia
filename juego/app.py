"""El loop principal: maneja eventos y cambia de pantalla."""

import os

import pygame

from .escenas import Menu
from .progreso import Progreso


class App:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.reloj = pygame.time.Clock()
        self.progreso = Progreso()
        self.corriendo = True
        self.escena = Menu(self)

    def cambiar(self, escena):
        self.escena = escena

    def salir(self):
        self.corriendo = False

    def correr(self):
        # Solo para pruebas automáticas: guarda una captura del menú y se cierra.
        captura = os.environ.get("DERIVIA_CAPTURA")
        cuadros = 0
        while self.corriendo:
            cuadros += 1
            if captura and cuadros == 30:
                pygame.image.save(self.pantalla, captura)
                self.corriendo = False
            dt = min(self.reloj.tick(60) / 1000, 0.1)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.corriendo = False
                else:
                    self.escena.evento(e)
            self.escena.actualizar(dt)
            self.escena.dibujar(self.pantalla)
            pygame.display.flip()
