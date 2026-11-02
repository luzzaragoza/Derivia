"""El loop principal: ventana a resolución real, eventos, transiciones, sacudidas y sonido."""

import math
import os
import random

import pygame

from . import gato, lienzo, paisaje, pincel, ui
from . import lienzo as dibujo
from .escenas import Menu, NombreGato
from .fx import suave
from .lienzo import ALTO, ANCHO, Lienzo
from .progreso import Progreso
from .sonido import sonidos


def tamaño_inicial():
    """La ventana más grande en 16:9 que entra cómoda en la pantalla."""
    try:
        w, h = pygame.display.get_desktop_sizes()[0]
    except Exception:
        return (ANCHO, ALTO)
    e = min(w * 0.92 / ANCHO, h * 0.86 / ALTO)
    return (int(ANCHO * e), int(ALTO * e))


def limpiar_caches():
    """Al cambiar la resolución hay que volver a dibujar letras, fórmulas, islas y al gato."""
    for cache in (ui._FUENTES, ui._CACHE_BORDE, ui._CACHE_MATE, ui._CACHE_RICO, ui._CACHE_GRAF,
                  paisaje._CACHE, gato._CACHE):
        cache.clear()
    pincel.limpiar()
    try:
        from . import escenas
        escenas._VELO.clear()
    except Exception:
        pass


class App:
    def __init__(self, pantalla):
        self.ventana = pantalla
        self.reloj = pygame.time.Clock()
        self.progreso = Progreso()
        p = self.progreso
        self._ajustar()
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

    # ------------------------------------------------ resolución
    @property
    def pantalla(self):
        return self.ventana

    def _ajustar(self):
        """Calcula la escala según el tamaño real de la ventana y arma el lienzo."""
        self.ventana = pygame.display.get_surface() or self.ventana
        w, h = self.ventana.get_size()
        e = min(w / ANCHO, h / ALTO)
        viejo = lienzo.escala()
        lienzo.poner_escala(e)
        self.dx, self.dy = (w - ANCHO * e) / 2, (h - ALTO * e) / 2
        lienzo.poner_desplazamiento(self.dx, self.dy)
        self.lienzo = Lienzo(ANCHO, ALTO, alfa=False)
        if abs(viejo - e) > 1e-6:
            limpiar_caches()

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
        actual = bool(self.ventana.get_flags() & pygame.FULLSCREEN)
        if actual != activa:
            if activa:
                self.ventana = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                self.ventana = pygame.display.set_mode(tamaño_inicial(), pygame.RESIZABLE)
            self._ajustar()
            self._rearmar()
        if guardar:
            self.progreso.pantalla_completa = activa
            self.progreso.guardar()

    def _rearmar(self):
        """La pantalla actual vuelve a armar sus botones con la resolución nueva."""
        armar = getattr(getattr(self, "escena", None), "armar", None)
        if callable(armar):
            try:
                armar()
            except Exception:
                pass

    def salir(self):
        self.corriendo = False

    def _componer(self, dt):
        pincel.nuevo_cuadro()
        destino = self.ventana
        e = lienzo.escala()
        sx = sy = 0
        if self.sacudida > 0.3:
            sx = random.uniform(-1, 1) * self.sacudida * e
            sy = random.uniform(-1, 1) * self.sacudida * 0.6 * e
            self.sacudida *= 0.82
        else:
            self.sacudida = 0
        if sx or sy or self.dx or self.dy:
            destino.fill((24, 18, 16))
        destino.blit(self.lienzo.sup, (self.dx + sx, self.dy + sy))
        if not self.transicion:
            return
        tipo, foto, t, dur = self.transicion
        t += dt
        k = min(1.0, t / dur)
        zona = pygame.Rect(int(self.dx), int(self.dy), self.lienzo.sup.get_width(),
                           self.lienzo.sup.get_height()).clip(destino.get_rect())
        if zona.width < 1 or zona.height < 1:
            self.transicion = None
            return
        capa = Lienzo(ANCHO, ALTO, sup=destino.subsurface(zona))
        if tipo == "fundido":
            foto.set_alpha(int(255 * (1 - suave(k))))
            capa.blit(foto, (0, 0))
        elif tipo == "ola":
            # una ola turquesa barre la pantalla: tapa lo viejo y destapa lo nuevo
            w, h = ANCHO, ALTO
            if k < 0.5:
                capa.blit(foto, (0, 0))
                frente = suave(k / 0.5) * (w + 200) - 100
            else:
                frente = suave((k - 0.5) / 0.5) * (w + 200) - 100
            for i, color in enumerate([(126, 210, 220), ui.MAR, ui.MAR_OSC]):
                desfase = i * 40
                x_borde = frente - desfase if k < 0.5 else frente + desfase
                pts = [(0 if k < 0.5 else w, 0)]
                for y in range(0, h + 20, 20):
                    pts.append((x_borde + math.sin(y / 40 + t * 8 + i) * 22, y))
                pts.append((0 if k < 0.5 else w, h))
                dibujo.polygon(capa, color, pts)
                dibujo.lines(capa, ui.ESPUMA, False, pts[1:-1], 4)
        self.transicion = None if k >= 1 else (tipo, foto, t, dur)

    # ------------------------------------------------ loop
    def _traducir(self, e):
        """El mouse llega en píxeles reales: se pasa a coordenadas del juego."""
        if e.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and hasattr(e, "pos"):
            datos = dict(e.dict)
            datos["pos"] = lienzo.a_logico(e.pos)
            return pygame.event.Event(e.type, datos)
        return e

    def correr(self):
        # Solo para pruebas automáticas: guarda una captura y se cierra.
        captura = os.environ.get("DERIVIA_CAPTURA")
        cuadros = 0
        while self.corriendo:
            cuadros += 1
            if captura and cuadros == 30:
                pygame.image.save(self.ventana, captura)
                self.corriendo = False
            dt = min(self.reloj.tick(60) / 1000, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.corriendo = False
                elif e.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED):
                    self._ajustar()
                    self._rearmar()
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_m and getattr(self.escena, "permite_m", True):
                    self.alternar_sonido()
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self.poner_pantalla_completa(not self.progreso.pantalla_completa)
                else:
                    self.escena.evento(self._traducir(e))
            sonidos.actualizar(dt)
            self.escena.actualizar(dt)
            self.escena.dibujar(self.lienzo)
            self._componer(dt)
            pygame.display.flip()
