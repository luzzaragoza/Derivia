"""El loop principal: eventos, transiciones entre pantallas, sacudidas y sonido."""

import math
import os
import random

import pygame

from . import gato, ui
from .escenas import Menu, NombreGato
from .fx import suave
from .progreso import Progreso
from .sonido import sonidos


class App:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.lienzo = pygame.Surface(pantalla.get_size())
        self.reloj = pygame.time.Clock()
        self.progreso = Progreso()
        p = self.progreso
        sonidos.iniciar()
        sonidos.poner_efectos(p.sonido)
        sonidos.musica_activa = p.musica
        sonidos.poner_volumenes(p.vol_efectos, p.vol_musica)
        gato.ROPA = tuple(p.ropa_puesta.values())
        if p.pantalla_completa:
            self.poner_pantalla_completa(True, guardar=False)
        self.corriendo = True
        self.transicion = None      # (tipo, foto_vieja, t, duración)
        self.sacudida = 0.0
        self.escena = Menu(self) if p.nombre_gato else NombreGato(self, primera_vez=True)
        sonidos.musica(self.escena.musica)

    # ------------------------------------------------ transiciones
    def cambiar(self, escena, transicion="fundido"):
        foto = self.lienzo.copy()
        self.escena = escena
        sonidos.musica(getattr(escena, "musica", "isla"))
        if transicion:
            dur = {"fundido": 0.28, "ola": 0.75}.get(transicion, 0.3)
            self.transicion = (transicion, foto, 0.0, dur)
            if transicion == "ola":
                sonidos.tocar("ola")

    def sacudir(self, intensidad=8):
        self.sacudida = max(self.sacudida, intensidad)

    def alternar_sonido(self):
        prendido = sonidos.alternar()
        self.progreso.sonido = self.progreso.musica = prendido
        self.progreso.guardar()

    def poner_pantalla_completa(self, activa, guardar=True):
        actual = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN) if pygame.display.get_surface() else False
        if actual != activa:
            try:
                pygame.display.toggle_fullscreen()
            except pygame.error:
                pass
        if guardar:
            self.progreso.pantalla_completa = activa
            self.progreso.guardar()

    def salir(self):
        self.corriendo = False

    def _componer(self, dt):
        destino = self.pantalla
        dx = dy = 0
        if self.sacudida > 0.3:
            dx = random.uniform(-1, 1) * self.sacudida
            dy = random.uniform(-1, 1) * self.sacudida * 0.6
            self.sacudida *= 0.82
        else:
            self.sacudida = 0
        if dx or dy:
            destino.fill(ui.TINTA)
        destino.blit(self.lienzo, (dx, dy))
        if not self.transicion:
            return
        tipo, foto, t, dur = self.transicion
        t += dt
        k = min(1.0, t / dur)
        if tipo == "fundido":
            foto.set_alpha(int(255 * (1 - suave(k))))
            destino.blit(foto, (0, 0))
        elif tipo == "ola":
            # una ola turquesa barre la pantalla: tapa lo viejo y destapa lo nuevo
            w, h = destino.get_size()
            if k < 0.5:
                destino.blit(foto, (0, 0))
                frente = suave(k / 0.5) * (w + 200) - 100      # entra de izquierda a derecha
            else:
                frente = suave((k - 0.5) / 0.5) * (w + 200) - 100  # se va hacia la derecha
            capas = [(126, 210, 220), ui.MAR, ui.MAR_OSC]
            for i, color in enumerate(capas):
                desfase = i * 40
                x_borde = frente - desfase if k < 0.5 else frente + desfase
                pts = [(0 if k < 0.5 else w, 0)]
                for y in range(0, h + 20, 20):
                    pts.append((x_borde + math.sin(y / 40 + t * 8 + i) * 22, y))
                pts.append((0 if k < 0.5 else w, h))
                pygame.draw.polygon(destino, color, pts)
                espuma = pts[1:-1]
                pygame.draw.lines(destino, ui.ESPUMA, False, espuma, 4)
        if k >= 1:
            self.transicion = None
        else:
            self.transicion = (tipo, foto, t, dur)

    # ------------------------------------------------ loop
    def correr(self):
        # Solo para pruebas automáticas: guarda una captura y se cierra.
        captura = os.environ.get("DERIVIA_CAPTURA")
        cuadros = 0
        while self.corriendo:
            cuadros += 1
            if captura and cuadros == 30:
                pygame.image.save(self.pantalla, captura)
                self.corriendo = False
            dt = min(self.reloj.tick(60) / 1000, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.corriendo = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_m and getattr(self.escena, "permite_m", True):
                    self.alternar_sonido()
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self.poner_pantalla_completa(not self.progreso.pantalla_completa)
                else:
                    self.escena.evento(e)
            sonidos.actualizar(dt)
            self.escena.actualizar(dt)
            self.escena.dibujar(self.lienzo)
            self._componer(dt)
            pygame.display.flip()
