"""Paisajes: cielo, nubes, sol, mar con olas, islas con palmeras y el pergamino."""

import math
import random

import numpy as np
import pygame

from . import ui
from .ui import ALTO, ANCHO

_CACHE = {}


def _gradiente(w, h, arriba, abajo):
    sup = pygame.Surface((w, h))
    for y in range(h):
        k = y / max(1, h - 1)
        c = [int(a + (b - a) * k) for a, b in zip(arriba, abajo)]
        pygame.draw.line(sup, c, (0, y), (w, y))
    return sup


def nube(escala=1.0, semilla=0):
    clave = ("nube", round(escala, 2), semilla)
    if clave in _CACHE:
        return _CACHE[clave]
    rng = random.Random(semilla)
    w, h = int(220 * escala), int(100 * escala)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    bolas = [(0.25, 0.62, 0.22), (0.45, 0.45, 0.3), (0.68, 0.55, 0.25), (0.82, 0.68, 0.17), (0.12, 0.72, 0.14)]
    for bx, by, br in bolas:
        bx += rng.uniform(-0.03, 0.03)
        pygame.draw.circle(s, (214, 234, 244), (bx * w, by * h + 5 * escala), br * w)
    for bx, by, br in bolas:
        pygame.draw.circle(s, (255, 255, 255), (bx * w, by * h), br * w)
    pygame.draw.rect(s, (0, 0, 0, 0), (0, h * 0.86, w, h))
    _CACHE[clave] = s
    return s


class Cielo:
    def __init__(self, alto=ALTO, nubes=6, semilla=1):
        self.fondo = _gradiente(ANCHO, alto, ui.CIELO_ARRIBA, ui.CIELO_ABAJO)
        rng = random.Random(semilla)
        self.nubes = [[rng.uniform(-200, ANCHO), rng.uniform(20, alto * 0.45), rng.uniform(0.5, 1.1),
                       rng.uniform(6, 18), rng.randint(0, 5)] for _ in range(nubes)]
        self.t = 0.0

    def actualizar(self, dt):
        self.t += dt
        for n in self.nubes:
            n[0] += n[3] * dt
            if n[0] > ANCHO + 40:
                n[0] = -260

    def dibujar(self, sup, sol=True):
        sup.blit(self.fondo, (0, 0))
        if sol:
            sol_c = (ANCHO - 150, 110)
            for k in range(12):
                a = self.t * 0.15 + k * math.tau / 12
                p1 = (sol_c[0] + math.cos(a) * 64, sol_c[1] + math.sin(a) * 64)
                p2 = (sol_c[0] + math.cos(a + 0.12) * 96, sol_c[1] + math.sin(a + 0.12) * 96)
                p3 = (sol_c[0] + math.cos(a - 0.12) * 96, sol_c[1] + math.sin(a - 0.12) * 96)
                pygame.draw.polygon(sup, (255, 236, 160), [p1, p2, p3])
            pygame.draw.circle(sup, (255, 226, 120), sol_c, 62)
            pygame.draw.circle(sup, ui.SOL, sol_c, 54)
            pygame.draw.circle(sup, (255, 240, 180), (sol_c[0] - 18, sol_c[1] - 18), 14)
        for x, y, esc, _, sem in self.nubes:
            sup.blit(nube(esc, sem), (x, y))


class Mar:
    def __init__(self, y, colores=None):
        self.y = y
        self.t = 0.0
        self.capas = colores or [(126, 210, 220), ui.MAR, ui.MAR_OSC]

    def actualizar(self, dt):
        self.t += dt

    def dibujar(self, sup, desde=0, hasta=ANCHO):
        n = len(self.capas)
        alto = ALTO - self.y
        for k, color in enumerate(self.capas):
            base = self.y + k * alto / (n + 0.5)
            amp = 6 + k * 2
            fase = self.t * (0.9 + 0.4 * k) * (1 if k % 2 == 0 else -1)
            pts = [(desde, ALTO)]
            for x in range(desde, hasta + 21, 20):
                yy = base + math.sin(x / (70 + 15 * k) + fase) * amp + math.sin(x / 31 + fase * 1.7) * 2
                pts.append((x, yy))
            pts.append((hasta, ALTO))
            pygame.draw.polygon(sup, color, pts)
            # espuma
            espuma = [(x, base + math.sin(x / (70 + 15 * k) + fase) * amp + math.sin(x / 31 + fase * 1.7) * 2)
                      for x in range(desde, hasta + 21, 20)]
            if len(espuma) > 1:
                pygame.draw.lines(sup, ui.aclarar(color, 0.55), False, espuma, 3)


def palmera(sup, base, alto=110, inclina=0.25, escala=1.0):
    bx, by = base
    alto *= escala
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((bx + math.sin(t * 1.4) * alto * inclina, by - t * alto))
    # tronco
    for i in range(len(pts) - 1):
        ancho = (12 - i * 0.8) * escala
        pygame.draw.line(sup, ui.BORDE, pts[i], pts[i + 1], int(ancho + 4))
    for i in range(len(pts) - 1):
        ancho = (12 - i * 0.8) * escala
        pygame.draw.line(sup, (196, 140, 82) if i % 2 == 0 else (176, 120, 66), pts[i], pts[i + 1], int(ancho))
    copa = pts[-1]
    # hojas
    for k, ang in enumerate((-2.7, -2.1, -1.4, -0.7, -0.1, 0.5)):
        largo = (70 + 10 * (k % 2)) * escala
        a = ang
        p_fin = (copa[0] + math.cos(a) * largo, copa[1] + math.sin(a) * largo * 0.55 + largo * 0.35)
        medio = (copa[0] + math.cos(a) * largo * 0.5, copa[1] + math.sin(a) * largo * 0.5 - 10 * escala)
        nx, ny = -math.sin(a) * 12 * escala, math.cos(a) * 12 * escala
        hoja = [copa, (medio[0] + nx, medio[1] + ny), p_fin, (medio[0] - nx, medio[1] - ny)]
        pygame.draw.polygon(sup, ui.BORDE, hoja)
        hoja_in = [copa, (medio[0] + nx * 0.7, medio[1] + ny * 0.7), p_fin, (medio[0] - nx * 0.7, medio[1] - ny * 0.7)]
        pygame.draw.polygon(sup, ui.PASTO if k % 2 else (100, 176, 90), hoja_in)
        pygame.draw.line(sup, ui.PASTO_OSC, copa, p_fin, 2)
    for dx in (-6, 5):
        pygame.draw.circle(sup, ui.BORDE, (copa[0] + dx * escala, copa[1] + 6 * escala), 7 * escala)
        pygame.draw.circle(sup, (140, 90, 50), (copa[0] + dx * escala, copa[1] + 6 * escala), 5 * escala)


def _blob(cx, cy, rx, ry, rng, puntos=40, rugosidad=0.08):
    fases = [rng.uniform(0, 6.28) for _ in range(3)]
    pts = []
    for i in range(puntos):
        a = math.tau * i / puntos
        r = 1 + rugosidad * (math.sin(a * 3 + fases[0]) + 0.6 * math.sin(a * 5 + fases[1]) + 0.4 * math.sin(a * 2 + fases[2]))
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    return pts


MARGEN_X, MARGEN_Y = 90, 150


def dibujar_isla(sup, pos, w, h, color_pasto=ui.PASTO, semilla=0, palmeras=3, palmeras_borde=False):
    """Dibuja la isla con su esquina de arriba a la izquierda en pos (sin contar el margen)."""
    sup.blit(isla(w, h, color_pasto, semilla, palmeras, palmeras_borde), (pos[0] - MARGEN_X, pos[1] - MARGEN_Y))


def isla(w, h, color_pasto=ui.PASTO, semilla=0, palmeras=3, palmeras_borde=False):
    """Isla (arena + pasto + palmeras) en una superficie transparente.
    palmeras_borde: las pone en las puntas de atrás (para que no tapen el camino del mapa)."""
    clave = ("isla", w, h, color_pasto, semilla, palmeras, palmeras_borde)
    if clave in _CACHE:
        return _CACHE[clave]
    rng = random.Random(semilla)
    # margen alrededor para que las palmeras no se corten
    s = pygame.Surface((w + 2 * MARGEN_X, h + MARGEN_Y), pygame.SRCALPHA)
    cx, cy = w / 2 + MARGEN_X, h * 0.55 + MARGEN_Y
    # sombra en el agua y orilla
    pygame.draw.polygon(s, (90, 196, 206), _blob(cx, cy + 14, w * 0.49, h * 0.42, rng))
    rng2 = random.Random(semilla)
    arena = _blob(cx, cy, w * 0.47, h * 0.4, rng2)
    pygame.draw.polygon(s, ui.BORDE, arena)
    pygame.draw.polygon(s, ui.ARENA, _blob(cx, cy, w * 0.47 - 3, h * 0.4 - 3, random.Random(semilla)))
    pasto = _blob(cx, cy - h * 0.04, w * 0.39, h * 0.3, random.Random(semilla + 1), rugosidad=0.1)
    pygame.draw.polygon(s, ui.oscurecer(color_pasto, 0.75), [(x, y + 6) for x, y in pasto])
    pygame.draw.polygon(s, color_pasto, pasto)
    # matitas
    for _ in range(14):
        x = rng.uniform(cx - w * 0.33, cx + w * 0.33)
        y = rng.uniform(cy - h * 0.25, cy + h * 0.18)
        c = ui.oscurecer(color_pasto, 0.82)
        for dx in (-4, 0, 4):
            pygame.draw.line(s, c, (x, y), (x + dx * 1.5, y - 9), 2)
    for k in range(palmeras):
        lado = -1 if k % 2 == 0 else 1
        if palmeras_borde:
            x = cx + lado * w * (0.40 + 0.03 * (k // 2))
            y = cy - h * (0.12 + 0.1 * (k // 2))
        else:
            x = cx + lado * w * rng.uniform(0.28, 0.4)
            y = cy + rng.uniform(-h * 0.12, h * 0.08)
        palmera(s, (x, y), rng.uniform(80, 110), inclina=0.25 * lado, escala=rng.uniform(0.75, 0.95))
    _CACHE[clave] = s
    return s


def pergamino():
    """Fondo de mapa del tesoro para las pantallas de estudio (se calcula una vez)."""
    if "pergamino" in _CACHE:
        return _CACHE["pergamino"]
    s = _gradiente(ANCHO, ALTO, (255, 249, 233), (247, 234, 204))
    rng = np.random.default_rng(3)
    # manchitas de papel
    arr = pygame.surfarray.pixels3d(s)
    ruido = rng.normal(0, 3.2, (ANCHO, ALTO, 1))
    arr[:] = np.clip(arr.astype(np.int16) + ruido, 0, 255).astype(np.uint8)
    del arr
    # líneas de latitud y longitud muy suaves
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for x in range(0, ANCHO, 80):
        pygame.draw.line(capa, (180, 140, 90, 22), (x, 0), (x, ALTO), 1)
    for y in range(0, ALTO, 80):
        pygame.draw.line(capa, (180, 140, 90, 22), (0, y), (ANCHO, y), 1)
    # rosa de los vientos en una esquina
    cx, cy = ANCHO - 90, ALTO - 90
    for k in range(8):
        a = k * math.tau / 8 - math.pi / 2
        largo = 62 if k % 2 == 0 else 38
        p = (cx + math.cos(a) * largo, cy + math.sin(a) * largo)
        q1 = (cx + math.cos(a + 0.35) * 12, cy + math.sin(a + 0.35) * 12)
        q2 = (cx + math.cos(a - 0.35) * 12, cy + math.sin(a - 0.35) * 12)
        pygame.draw.polygon(capa, (170, 120, 70, 40), [p, q1, (cx, cy), q2])
    pygame.draw.circle(capa, (170, 120, 70, 40), (cx, cy), 46, 2)
    # sendero punteado decorativo
    for i in range(40):
        t = i / 40
        x = 40 + t * 260
        y = ALTO - 40 - math.sin(t * 5) * 30 - t * 60
        pygame.draw.circle(capa, (190, 130, 80, 40), (x, y), 3)
    s.blit(capa, (0, 0))
    # viñeta en los bordes
    vin = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for k in range(18):
        pygame.draw.rect(vin, (150, 100, 50, 7), (k * 2, k * 2, ANCHO - k * 4, ALTO - k * 4), 3, border_radius=30)
    s.blit(vin, (0, 0))
    _CACHE["pergamino"] = s
    return s
