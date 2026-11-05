"""Paisajes: cielo, nubes, sol, mar con olas, islas con palmeras y el pergamino."""

import math
import random

import numpy as np
import pygame

from . import lienzo as dibujo
from . import pincel, ui
from .cache import CacheDibujos
from .lienzo import Lienzo
from .ui import ALTO, ANCHO

_CACHE = CacheDibujos(limite=400)


def gradiente(w, h, arriba, abajo):
    """Degradé vertical, pintado fila por fila a la resolución real (sin bandas)."""
    lz = Lienzo(w, h, alfa=False)
    H = lz.sup.get_height()
    col = np.linspace(0, 1, H)[:, None]
    filas = (np.array(arriba, float)[None, :] * (1 - col) + np.array(abajo, float)[None, :] * col).astype(np.uint8)
    px = pygame.surfarray.pixels3d(lz.sup)
    px[:, :, :] = filas[None, :, :]
    del px
    return lz


_gradiente = gradiente


def nube(escala=1.0, semilla=0, tinte=None):
    clave = ("nube", round(escala, 2), semilla, tinte)
    if tinte and clave not in _CACHE:
        s = nube(escala, semilla).copy()
        s.fill(tinte + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        _CACHE[clave] = s
    if clave in _CACHE:
        return _CACHE[clave]
    rng = random.Random(semilla)
    w, h = int(220 * escala), int(100 * escala)
    with pincel.siempre():
        pieza, _m = pincel.nube(w, h, semilla) if pincel.HAY_SKIA else (None, 0)
    if pieza is not None:
        _CACHE[clave] = pieza
        return pieza
    s = Lienzo(*((w, h)))
    bolas = [(0.25, 0.62, 0.22), (0.45, 0.45, 0.3), (0.68, 0.55, 0.25), (0.82, 0.68, 0.17), (0.12, 0.72, 0.14)]
    for bx, by, br in bolas:
        bx += rng.uniform(-0.03, 0.03)
        dibujo.circle(s, (214, 234, 244), (bx * w, by * h + 5 * escala), br * w)
    for bx, by, br in bolas:
        dibujo.circle(s, (255, 255, 255), (bx * w, by * h), br * w)
    dibujo.rect(s, (0, 0, 0, 0), (0, h * 0.86, w, h))
    _CACHE[clave] = s
    return s


class Cielo:
    def __init__(self, alto=ALTO, nubes=6, semilla=1, tema=None):
        self.tema = tema or TEMAS["1"]
        self.fondo = _gradiente(ANCHO, alto, self.tema["cielo"][0], self.tema["cielo"][1])
        rng = random.Random(semilla)
        self.estrellas = [(rng.uniform(0, ANCHO), rng.uniform(0, alto * 0.55), rng.uniform(0, 6.28), rng.choice((1, 2, 2, 3)))
                          for _ in range(70)] if self.tema.get("estrellas") else []
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
        for x, y, fase, r in self.estrellas:
            brillo = 0.5 + 0.5 * math.sin(self.t * 2 + fase)
            dibujo.circle(sup, (255, 250, 220), (x, y), r * (0.6 + 0.4 * brillo))
        astro = self.tema.get("astro", "sol")
        if sol and astro == "luna":
            c = (ANCHO - 160, 110)
            _halo(sup, c, 110, (240, 240, 220), 70)
            pieza, m = pincel.luna(52) if pincel.HAY_SKIA else (None, 0)
            if pieza is not None:
                sup.blit(pieza, (c[0] - 54 - m, c[1] - 54 - m))
            else:
                dibujo.circle(sup, (246, 244, 226), c, 52)
                for dx, dy, r in ((-16, -10, 10), (14, 12, 7), (10, -20, 5), (-6, 22, 6)):
                    dibujo.circle(sup, (222, 220, 200), (c[0] + dx, c[1] + dy), r)
            sol = False
        elif sol and astro == "sol_bajo":
            c = (ANCHO - 230, 250)
            _halo(sup, c, 170, (255, 200, 120), 110)
            pieza, m = pincel.sol_bajo(74) if pincel.HAY_SKIA else (None, 0)
            if pieza is not None:
                sup.blit(pieza, (c[0] - 76 - m, c[1] - 76 - m))
            else:
                dibujo.circle(sup, (255, 160, 90), c, 74)
                dibujo.circle(sup, (255, 196, 120), (c[0] - 20, c[1] - 22), 18)
            sol = False
        elif astro == "ninguno":
            sol = False
        if sol:
            sol_c = (ANCHO - 150, 110)
            for k in range(12):
                a = self.t * 0.15 + k * math.tau / 12
                p1 = (sol_c[0] + math.cos(a) * 64, sol_c[1] + math.sin(a) * 64)
                p2 = (sol_c[0] + math.cos(a + 0.12) * 96, sol_c[1] + math.sin(a + 0.12) * 96)
                p3 = (sol_c[0] + math.cos(a - 0.12) * 96, sol_c[1] + math.sin(a - 0.12) * 96)
                dibujo.polygon(sup, (255, 236, 160), [p1, p2, p3])
            pieza, m = pincel.sol(58) if pincel.HAY_SKIA else (None, 0)
            if pieza is not None:
                sup.blit(pieza, (sol_c[0] - 60 - m, sol_c[1] - 60 - m))
            else:
                dibujo.circle(sup, (255, 226, 120), sol_c, 62)
                dibujo.circle(sup, ui.SOL, sol_c, 54)
                dibujo.circle(sup, (255, 240, 180), (sol_c[0] - 18, sol_c[1] - 18), 14)
        tinte = self.tema.get("nubes")
        for x, y, esc, _, sem in self.nubes:
            sup.blit(nube(esc, sem, tinte), (x, y))


def _halo(sup, c, r, color, a):
    pieza = pincel.brillo_suave(r, color, a) if pincel.HAY_SKIA else None
    if pieza is None:
        pieza = _CACHE.get(("halo", r, color, a, dibujo.escala()))
        if pieza is None:
            pieza = Lienzo(2 * r, 2 * r)
            for k in range(6):
                dibujo.circle(pieza, color + (a // 6,), (r, r), r * (1 - k / 7))
            _CACHE[("halo", r, color, a, dibujo.escala())] = pieza
    sup.blit(pieza, (c[0] - r, c[1] - r))


class Mar:
    def __init__(self, y, colores=None):
        self.y = y
        self.t = 0.0
        self.capas = colores or [(126, 210, 220), ui.MAR, ui.MAR_OSC]

    def actualizar(self, dt):
        self.t += dt

    PERIODOS = (420, 300, 360, 260)

    def dibujar(self, sup, desde=0, hasta=ANCHO):
        if pincel.HAY_SKIA and self._dibujar_fino(sup, desde, hasta):
            return
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
            dibujo.polygon(sup, color, pts)
            # espuma
            espuma = [(x, base + math.sin(x / (70 + 15 * k) + fase) * amp + math.sin(x / 31 + fase * 1.7) * 2)
                      for x in range(desde, hasta + 21, 20)]
            if len(espuma) > 1:
                dibujo.lines(sup, ui.aclarar(color, 0.55), False, espuma, 3)


def _mar_fino(self, sup, desde, hasta):
    n = len(self.capas)
    alto = ALTO - self.y
    clip = sup.get_clip()
    if (desde, hasta) != (0, ANCHO):
        sup.set_clip(pygame.Rect(desde, 0, hasta - desde, ALTO))
    try:
        for k, color in enumerate(self.capas):
            base = self.y + k * alto / (n + 0.5)
            amp = 6 + k * 2
            periodo = self.PERIODOS[k % len(self.PERIODOS)]
            with pincel.siempre():
                tira, _m = pincel.ola(ANCHO + periodo, ALTO - base + 2 * amp + 4, periodo, amp, color, k)
            if tira is None:
                return False
            vel = (22 + 10 * k) * (1 if k % 2 == 0 else -1)
            dx = -((self.t * vel) % periodo)
            dy = math.sin(self.t * (0.9 + 0.3 * k) + k) * 2.5
            sup.blit(tira, (dx, base - 2 * amp + dy))
    finally:
        sup.set_clip(clip)
    return True


Mar._dibujar_fino = _mar_fino


def palmera(sup, base, alto=110, inclina=0.25, escala=1.0):
    bx, by = base
    if pincel.HAY_SKIA:
        pieza, (ax, ay) = pincel.palmera(alto, inclina, escala)
        if pieza is not None:
            sup.blit(pieza, (bx - ax, by - ay))
            return
    alto *= escala
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((bx + math.sin(t * 1.4) * alto * inclina, by - t * alto))
    # tronco
    for i in range(len(pts) - 1):
        ancho = (12 - i * 0.8) * escala
        dibujo.line(sup, ui.BORDE, pts[i], pts[i + 1], int(ancho + 4))
    for i in range(len(pts) - 1):
        ancho = (12 - i * 0.8) * escala
        dibujo.line(sup, (196, 140, 82) if i % 2 == 0 else (176, 120, 66), pts[i], pts[i + 1], int(ancho))
    copa = pts[-1]
    # hojas
    for k, ang in enumerate((-2.7, -2.1, -1.4, -0.7, -0.1, 0.5)):
        largo = (70 + 10 * (k % 2)) * escala
        a = ang
        p_fin = (copa[0] + math.cos(a) * largo, copa[1] + math.sin(a) * largo * 0.55 + largo * 0.35)
        medio = (copa[0] + math.cos(a) * largo * 0.5, copa[1] + math.sin(a) * largo * 0.5 - 10 * escala)
        nx, ny = -math.sin(a) * 12 * escala, math.cos(a) * 12 * escala
        hoja = [copa, (medio[0] + nx, medio[1] + ny), p_fin, (medio[0] - nx, medio[1] - ny)]
        dibujo.polygon(sup, ui.BORDE, hoja)
        hoja_in = [copa, (medio[0] + nx * 0.7, medio[1] + ny * 0.7), p_fin, (medio[0] - nx * 0.7, medio[1] - ny * 0.7)]
        dibujo.polygon(sup, ui.PASTO if k % 2 else (100, 176, 90), hoja_in)
        dibujo.line(sup, ui.PASTO_OSC, copa, p_fin, 2)
    for dx in (-6, 5):
        dibujo.circle(sup, ui.BORDE, (copa[0] + dx * escala, copa[1] + 6 * escala), 7 * escala)
        dibujo.circle(sup, (140, 90, 50), (copa[0] + dx * escala, copa[1] + 6 * escala), 5 * escala)


def _blob(cx, cy, rx, ry, rng, puntos=40, rugosidad=0.08):
    fases = [rng.uniform(0, 6.28) for _ in range(3)]
    pts = []
    for i in range(puntos):
        a = math.tau * i / puntos
        r = 1 + rugosidad * (math.sin(a * 3 + fases[0]) + 0.6 * math.sin(a * 5 + fases[1]) + 0.4 * math.sin(a * 2 + fases[2]))
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    return pts


MARGEN_X, MARGEN_Y = 90, 150


def dibujar_isla(sup, pos, w, h, color_pasto=ui.PASTO, semilla=0, palmeras=3, palmeras_borde=False, deco="palmeras",
                 orilla=None, tinte=None):
    """Dibuja la isla con su esquina de arriba a la izquierda en pos (sin contar el margen)."""
    sup.blit(isla(w, h, color_pasto, semilla, palmeras, palmeras_borde, deco, orilla, tinte),
             (pos[0] - MARGEN_X, pos[1] - MARGEN_Y))


def isla_tema(sup, pos, w, h, t, semilla=0, palmeras=3, palmeras_borde=False):
    """Isla con los colores y la decoración de un tema."""
    dibujar_isla(sup, pos, w, h, t["pasto"], semilla, palmeras, palmeras_borde, t["deco"],
                 ui.aclarar(t["mar"][0], 0.15), t.get("tinte"))


def isla(w, h, color_pasto=ui.PASTO, semilla=0, palmeras=3, palmeras_borde=False, deco="palmeras", orilla=None,
         tinte=None):
    """Isla (arena + pasto + palmeras) en una superficie transparente.
    palmeras_borde: las pone en las puntas de atrás (para que no tapen el camino del mapa)."""
    clave = ("isla", w, h, color_pasto, semilla, palmeras, palmeras_borde, deco, orilla, tinte)
    if clave in _CACHE:
        return _CACHE[clave]
    with pincel.siempre():
        _CACHE[clave] = _armar_isla(w, h, color_pasto, semilla, palmeras, palmeras_borde, deco, orilla, tinte)
    return _CACHE[clave]


def _armar_isla(w, h, color_pasto, semilla, palmeras, palmeras_borde, deco, orilla, tinte):
    rng = random.Random(semilla)
    # margen alrededor para que las palmeras no se corten
    s = Lienzo(*((w + 2 * MARGEN_X, h + MARGEN_Y)))
    cx, cy = w / 2 + MARGEN_X, h * 0.55 + MARGEN_Y
    # sombra en el agua y orilla
    agua = _blob(cx, cy + 14, w * 0.49, h * 0.42, rng)
    rng2 = random.Random(semilla)
    arena = _blob(cx, cy, w * 0.47, h * 0.4, rng2)
    pasto = _blob(cx, cy - h * 0.04, w * 0.39, h * 0.3, random.Random(semilla + 1), rugosidad=0.1)
    base = None
    if pincel.HAY_SKIA:
        base = pincel.isla_base((w, h, semilla, tuple(color_pasto), orilla), w, h, cx, cy, agua, arena, pasto,
                                color_pasto, orilla or (90, 196, 206), s.get_width(), s.get_height())
    if base is not None:
        s.blit(base, (0, 0))
    else:
        dibujo.polygon(s, orilla or (90, 196, 206), agua)
        dibujo.polygon(s, ui.BORDE, arena)
        dibujo.polygon(s, ui.ARENA, _blob(cx, cy, w * 0.47 - 3, h * 0.4 - 3, random.Random(semilla)))
        dibujo.polygon(s, ui.oscurecer(color_pasto, 0.75), [(x, y + 6) for x, y in pasto])
        dibujo.polygon(s, color_pasto, pasto)
    final = s
    if pincel.HAY_SKIA:   # lo de arriba de la isla se pinta con Skia en una hoja aparte
        s = pincel.CapaSkia(final.get_width(), final.get_height())
    # matitas
    for _ in range(14):
        x = rng.uniform(cx - w * 0.33, cx + w * 0.33)
        y = rng.uniform(cy - h * 0.25, cy + h * 0.18)
        c = ui.oscurecer(color_pasto, 0.82)
        for dx in (-4, 0, 4):
            _d(s).line(s, c, (x, y), (x + dx * 1.5, y - 9), 2)
    _decorar(s, deco, cx, cy, w, h, rng, color_pasto)
    for k in range(palmeras if deco in ("palmeras", "flores", "rocas") else 0):
        lado = -1 if k % 2 == 0 else 1
        if palmeras_borde:
            x = cx + lado * w * (0.40 + 0.03 * (k // 2))
            y = cy - h * (0.12 + 0.1 * (k // 2))
        else:
            x = cx + lado * w * rng.uniform(0.28, 0.4)
            y = cy + rng.uniform(-h * 0.12, h * 0.08)
        palmera(s, (x, y), rng.uniform(80, 110), inclina=0.25 * lado, escala=rng.uniform(0.75, 0.95))
    if s is not final:
        final.blit(s.terminar(), (0, 0))
        s = final
    if tinte:
        s.fill(tuple(tinte) + (255,), special_flags=pygame.BLEND_RGBA_MULT)
    return s


def pergamino():
    """Fondo de mapa del tesoro para las pantallas de estudio (se calcula una vez)."""
    clave = ("pergamino", Lienzo(1, 1).e)
    if clave in _CACHE:
        return _CACHE[clave]
    if pincel.HAY_SKIA:
        papel = pincel.pergamino(ANCHO, ALTO)
        if papel is not None:
            s = Lienzo(ANCHO, ALTO, alfa=False)
            s.blit(papel, (0, 0))
            arr = pygame.surfarray.pixels3d(s.sup)   # granito de papel, a la resolución real
            ruido = np.random.default_rng(3).normal(0, 2.6, arr.shape[:2] + (1,))
            arr[:] = np.clip(arr.astype(np.int16) + ruido, 0, 255).astype(np.uint8)
            del arr
            _CACHE[clave] = s
            return s
    s = gradiente(ANCHO, ALTO, (255, 249, 233), (247, 234, 204))
    rng = np.random.default_rng(3)
    # manchitas de papel (a la resolución real)
    arr = pygame.surfarray.pixels3d(s.sup)
    ruido = rng.normal(0, 3.2, arr.shape[:2] + (1,))
    arr[:] = np.clip(arr.astype(np.int16) + ruido, 0, 255).astype(np.uint8)
    del arr
    # líneas de latitud y longitud muy suaves
    capa = Lienzo(*((ANCHO, ALTO)))
    for x in range(0, ANCHO, 80):
        dibujo.line(capa, (180, 140, 90, 22), (x, 0), (x, ALTO), 1)
    for y in range(0, ALTO, 80):
        dibujo.line(capa, (180, 140, 90, 22), (0, y), (ANCHO, y), 1)
    # rosa de los vientos en una esquina
    cx, cy = ANCHO - 90, ALTO - 90
    for k in range(8):
        a = k * math.tau / 8 - math.pi / 2
        largo = 62 if k % 2 == 0 else 38
        p = (cx + math.cos(a) * largo, cy + math.sin(a) * largo)
        q1 = (cx + math.cos(a + 0.35) * 12, cy + math.sin(a + 0.35) * 12)
        q2 = (cx + math.cos(a - 0.35) * 12, cy + math.sin(a - 0.35) * 12)
        dibujo.polygon(capa, (170, 120, 70, 40), [p, q1, (cx, cy), q2])
    dibujo.circle(capa, (170, 120, 70, 40), (cx, cy), 46, 2)
    # sendero punteado decorativo
    for i in range(40):
        t = i / 40
        x = 40 + t * 260
        y = ALTO - 40 - math.sin(t * 5) * 30 - t * 60
        dibujo.circle(capa, (190, 130, 80, 40), (x, y), 3)
    s.blit(capa, (0, 0))
    # viñeta en los bordes
    vin = Lienzo(*((ANCHO, ALTO)))
    for k in range(18):
        dibujo.rect(vin, (150, 100, 50, 7), (k * 2, k * 2, ANCHO - k * 4, ALTO - k * 4), 3, border_radius=30)
    s.blit(vin, (0, 0))
    _CACHE[clave] = s
    return s


# ------------------------------------------------------------ temas de las islas
# De más tranquila a más misteriosa (sin pasarse).
TEMAS = {
    "1": dict(nombre="Isla Serena", cielo=((120, 200, 234), (206, 238, 242)), astro="sol",
              mar=[(126, 210, 220), (64, 182, 196), (34, 132, 158)], pasto=(122, 196, 106), deco="palmeras"),
    "2": dict(nombre="Isla Jardín", cielo=((126, 204, 236), (214, 240, 236)), astro="sol",
              mar=[(126, 214, 214), (70, 190, 190), (40, 140, 156)], pasto=(132, 206, 112), deco="flores"),
    "3": dict(nombre="Isla Rocosa", cielo=((140, 196, 226), (228, 236, 230)), astro="sol",
              mar=[(118, 196, 214), (60, 166, 190), (32, 120, 150)], pasto=(146, 186, 100), deco="rocas"),
    "3b": dict(nombre="Isla del Reloj", cielo=((236, 196, 140), (255, 236, 200)), astro="sol",
               mar=[(120, 200, 206), (64, 170, 186), (40, 126, 150)], pasto=(204, 190, 112), deco="cactus"),
    "4": dict(nombre="Isla del Bosque", cielo=((132, 178, 206), (210, 226, 228)), astro="sol",
              mar=[(108, 184, 200), (56, 150, 176), (30, 108, 140)], pasto=(88, 160, 96), deco="pinos",
              nubes=(236, 240, 244)),
    "5": dict(nombre="Isla Cascada", cielo=((156, 172, 226), (236, 214, 232)), astro="sol",
              mar=[(112, 180, 214), (64, 146, 190), (38, 104, 150)], pasto=(100, 172, 130), deco="montaña"),
    "6": dict(nombre="Isla del Atardecer", cielo=((240, 140, 120), (255, 214, 160)), astro="sol_bajo",
              mar=[(110, 170, 196), (70, 136, 176), (44, 98, 140)], pasto=(118, 158, 92), deco="hongos",
              nubes=(255, 214, 200), tinte=(255, 232, 218)),
    "7": dict(nombre="Isla Volcán", cielo=((110, 86, 140), (236, 150, 120)), astro="ninguno",
              mar=[(86, 130, 166), (58, 100, 142), (34, 70, 112)], pasto=(116, 130, 82), deco="volcan",
              nubes=(200, 170, 190), tinte=(232, 206, 210)),
    "8": dict(nombre="Isla Tormenta", cielo=((62, 72, 108), (122, 132, 158)), astro="ninguno",
              mar=[(60, 108, 136), (40, 84, 116), (26, 62, 92)], pasto=(78, 120, 92), deco="tormenta",
              nubes=(150, 156, 176), tinte=(196, 202, 220)),
    "9": dict(nombre="Isla Calavera", cielo=((26, 28, 66), (82, 70, 122)), astro="luna", estrellas=True,
              mar=[(52, 70, 112), (36, 50, 92), (22, 34, 70)], pasto=(86, 100, 92), deco="calavera",
              nubes=(110, 104, 150), tinte=(160, 160, 200)),
}


def tema(mundo_id):
    return TEMAS.get(mundo_id, TEMAS["1"])


def _d(sup):
    """Con qué se dibuja: Skia si la hoja es de Skia, si no las funciones de siempre."""
    return getattr(sup, "d", dibujo)


def _con_borde_poligono(sup, pts, color, grosor=3):
    _d(sup).polygon(sup, ui.BORDE, pts, grosor * 2)
    _d(sup).polygon(sup, color, pts)


def pino(sup, base, alto=120, color=(64, 140, 80)):
    bx, by = base
    _d(sup).rect(sup, ui.BORDE, (bx - 7, by - 24, 14, 26))
    _d(sup).rect(sup, (140, 92, 54), (bx - 5, by - 22, 10, 22))
    for k in range(3):
        ancho = alto * (0.42 - k * 0.09)
        y0 = by - 18 - k * alto * 0.24
        _con_borde_poligono(sup, [(bx - ancho, y0), (bx + ancho, y0), (bx, y0 - alto * 0.42)],
                            ui.oscurecer(color, 1 - k * 0.04) if k else color)


def cactus(sup, base, alto=90):
    bx, by = base
    verde = (110, 176, 96)
    for r in [(bx - 12, by - alto, 24, alto), (bx - 40, by - alto * 0.7, 18, alto * 0.38),
              (bx + 22, by - alto * 0.85, 18, alto * 0.45)]:
        _d(sup).rect(sup, ui.BORDE, pygame.Rect(r).inflate(6, 6), border_radius=12)
    for r in [(bx - 30, by - alto * 0.42, 22, 14), (bx + 10, by - alto * 0.5, 22, 14)]:
        _d(sup).rect(sup, ui.BORDE, pygame.Rect(r).inflate(6, 6), border_radius=6)
    for r in [(bx - 12, by - alto, 24, alto), (bx - 40, by - alto * 0.7, 18, alto * 0.38),
              (bx + 22, by - alto * 0.85, 18, alto * 0.45), (bx - 30, by - alto * 0.42, 22, 14),
              (bx + 10, by - alto * 0.5, 22, 14)]:
        _d(sup).rect(sup, verde, r, border_radius=10)
    _d(sup).circle(sup, (255, 150, 190), (bx, by - alto - 2), 6)


def roca(sup, centro, r, color=(160, 156, 150)):
    cx, cy = centro
    pts = [(cx - r, cy), (cx - r * 0.7, cy - r * 0.7), (cx, cy - r * 0.9), (cx + r * 0.8, cy - r * 0.55), (cx + r, cy)]
    _con_borde_poligono(sup, pts, color)
    _d(sup).line(sup, ui.aclarar(color, 0.35), (cx - r * 0.5, cy - r * 0.55), (cx - r * 0.05, cy - r * 0.75), 3)


def flor(sup, pos, color):
    x, y = pos
    _d(sup).line(sup, (80, 150, 70), (x, y), (x, y + 10), 2)
    for k in range(5):
        a = k * math.tau / 5
        _d(sup).circle(sup, color, (x + math.cos(a) * 5, y + math.sin(a) * 5), 4)
    _d(sup).circle(sup, ui.SOL, (x, y), 3)


def hongo(sup, base, escala=1.0, color=(200, 80, 110)):
    bx, by = base
    tallo = pygame.Rect(0, 0, 18 * escala, 34 * escala)
    tallo.midbottom = (bx, by)
    _d(sup).rect(sup, ui.BORDE, tallo.inflate(6, 6), border_radius=8)
    _d(sup).rect(sup, (250, 236, 210), tallo, border_radius=7)
    rx, ry = 36 * escala, 30 * escala
    base_y = tallo.top + 8 * escala
    cupula = [(bx + math.cos(a) * rx, base_y - math.sin(a) * ry) for a in [k * math.pi / 16 for k in range(17)]]
    _con_borde_poligono(sup, cupula, color)
    for dx, dy, r in ((-16, -10, 6), (10, -18, 5), (22, -6, 4), (-2, -6, 4)):
        _d(sup).circle(sup, (255, 248, 236), (bx + dx * escala, base_y + dy * escala), r * escala)


def montana(sup, base, ancho, alto):
    """Dos picos con nieve, crestas y una cascada que cae a un laguito."""
    bx, by = base
    d = _d(sup)
    # pico de atrás (más chico y más azulado, da profundidad)
    atras = [(bx + ancho * 0.05, by), (bx + ancho * 0.36, by - alto * 0.78), (bx + ancho * 0.62, by)]
    _con_borde_poligono(sup, atras, (168, 172, 196))
    _con_borde_poligono(sup, [(bx + ancho * 0.29, by - alto * 0.62), (bx + ancho * 0.36, by - alto * 0.78),
                              (bx + ancho * 0.43, by - alto * 0.62), (bx + ancho * 0.36, by - alto * 0.66)],
                        (246, 248, 255), 2)
    # pico principal
    frente = [(bx - ancho / 2, by), (bx - ancho * 0.12, by - alto * 0.8), (bx, by - alto), (bx + ancho * 0.1, by - alto * 0.86),
              (bx + ancho * 0.42, by)]
    _con_borde_poligono(sup, frente, (150, 146, 168))
    # lado en sombra
    d.polygon(sup, (126, 120, 146), [(bx, by - alto), (bx + ancho * 0.1, by - alto * 0.86), (bx + ancho * 0.42, by),
                                     (bx + ancho * 0.08, by)])
    # nieve con "goteo"
    nieve = [(bx - ancho * 0.16, by - alto * 0.74), (bx - ancho * 0.12, by - alto * 0.8), (bx, by - alto),
             (bx + ancho * 0.1, by - alto * 0.86), (bx + ancho * 0.15, by - alto * 0.78), (bx + ancho * 0.08, by - alto * 0.72),
             (bx + ancho * 0.03, by - alto * 0.76), (bx - ancho * 0.03, by - alto * 0.68), (bx - ancho * 0.08, by - alto * 0.75)]
    _con_borde_poligono(sup, nieve, (250, 252, 255), 2)
    # crestas de roca
    for (x1, y1, x2, y2) in ((-0.2, 0.55, -0.28, 0.3), (0.16, 0.6, 0.24, 0.32), (-0.05, 0.62, -0.1, 0.4)):
        d.line(sup, (110, 104, 128), (bx + ancho * x1, by - alto * y1), (bx + ancho * x2, by - alto * y2), 3)
    # cascada con espuma abajo
    cx = bx + ancho * 0.02
    d.rect(sup, ui.BORDE, (cx - 10, by - alto * 0.6, 20, alto * 0.6 - 4), border_radius=6)
    d.rect(sup, (150, 210, 240), (cx - 7, by - alto * 0.6 + 2, 14, alto * 0.6 - 8), border_radius=5)
    for k in range(5):
        y = by - alto * 0.55 + k * alto * 0.1
        d.line(sup, (236, 250, 255), (cx - 2 + (k % 2) * 4, y), (cx - 2 + (k % 2) * 4, y + 12), 2)
    d.ellipse(sup, ui.BORDE, (cx - 34, by - 14, 68, 22))
    d.ellipse(sup, (120, 196, 230), (cx - 31, by - 12, 62, 17))
    for dx in (-14, 0, 14):
        d.circle(sup, (248, 252, 255), (cx + dx, by - 10), 6)


def volcan(sup, base, ancho, alto):
    bx, by = base
    _con_borde_poligono(sup, [(bx - ancho / 2, by), (bx - ancho * 0.12, by - alto), (bx + ancho * 0.12, by - alto),
                              (bx + ancho / 2, by)], (134, 96, 80))
    _d(sup).polygon(sup, (250, 120, 60), [(bx - ancho * 0.12, by - alto), (bx + ancho * 0.12, by - alto),
                                              (bx + ancho * 0.05, by - alto * 0.86), (bx - ancho * 0.02, by - alto * 0.9)])
    _d(sup).lines(sup, (250, 150, 70), False, [(bx + ancho * 0.02, by - alto * 0.9), (bx - ancho * 0.04, by - alto * 0.6),
                                                   (bx + ancho * 0.03, by - alto * 0.35)], 6)


def arbol_seco(sup, base, alto=100):
    bx, by = base
    color = (96, 72, 64)
    tronco = [(bx, by), (bx + 4, by - alto * 0.6), (bx - 2, by - alto)]
    _d(sup).lines(sup, ui.BORDE, False, tronco, 12)
    _d(sup).lines(sup, color, False, tronco, 8)
    for (x1, y1, x2, y2) in ((bx + 3, by - alto * 0.55, bx + 34, by - alto * 0.8), (bx + 1, by - alto * 0.75, bx - 30, by - alto * 0.98),
                             (bx + 20, by - alto * 0.68, bx + 30, by - alto * 0.95)):
        _d(sup).line(sup, ui.BORDE, (x1, y1), (x2, y2), 8)
        _d(sup).line(sup, color, (x1, y1), (x2, y2), 4)


def calavera_roca(sup, centro, r):
    cx, cy = centro
    gris = (176, 172, 168)
    _d(sup).circle(sup, ui.BORDE, (cx, cy), r + 3)
    _d(sup).circle(sup, gris, (cx, cy), r)
    mandibula = pygame.Rect(0, 0, r * 1.1, r * 0.7)
    mandibula.midtop = (cx, cy + r * 0.55)
    _d(sup).rect(sup, ui.BORDE, mandibula.inflate(6, 6), border_radius=10)
    _d(sup).rect(sup, gris, mandibula, border_radius=8)
    for dx in (-0.38, 0.38):
        _d(sup).ellipse(sup, (40, 34, 56), (cx + dx * r - r * 0.22, cy - r * 0.1, r * 0.44, r * 0.5))
    _d(sup).polygon(sup, (40, 34, 56), [(cx, cy + r * 0.38), (cx - r * 0.1, cy + r * 0.58), (cx + r * 0.1, cy + r * 0.58)])
    for k in range(-2, 3):
        _d(sup).line(sup, ui.BORDE, (cx + k * r * 0.18, mandibula.top + 4), (cx + k * r * 0.18, mandibula.bottom - 4), 2)


def _decorar(s, deco, cx, cy, w, h, rng, pasto):
    """Decoración de cada isla. Lo grande va atrás (arriba), lo chiquito, desparramado."""
    atras = [(cx - w * 0.42, cy - h * 0.14), (cx + w * 0.42, cy - h * 0.14), (cx - w * 0.3, cy - h * 0.26),
             (cx + w * 0.3, cy - h * 0.26)]
    desparramado = [(rng.uniform(cx - w * 0.36, cx + w * 0.36), rng.uniform(cy - h * 0.2, cy + h * 0.22)) for _ in range(14)]
    if deco == "flores":
        for k, p in enumerate(desparramado):
            flor(s, p, [(255, 150, 190), (255, 230, 120), (255, 255, 255), (250, 124, 104)][k % 4])
    elif deco == "rocas":
        for p in desparramado[:5]:
            roca(s, p, rng.uniform(14, 26))
    elif deco == "cactus":
        for p in atras:
            cactus(s, p, rng.uniform(70, 100))
        for p in desparramado[:4]:
            roca(s, p, rng.uniform(10, 18), (200, 170, 130))
    elif deco in ("pinos", "tormenta"):
        color = (64, 140, 80) if deco == "pinos" else (52, 96, 76)
        for p in atras + [(cx - w * 0.15, cy - h * 0.3), (cx + w * 0.12, cy - h * 0.32)]:
            pino(s, p, rng.uniform(100, 140), color)
        if deco == "tormenta":
            for p in desparramado[:4]:
                roca(s, p, rng.uniform(12, 22), (130, 130, 140))
    elif deco == "montaña":
        montana(s, (cx - w * 0.2, cy - h * 0.2), w * 0.3, h * 0.42)
        for p in atras[1::2]:
            pino(s, p, 110)
    elif deco == "hongos":
        for k, p in enumerate(atras):
            hongo(s, (p[0], p[1] + 10), rng.uniform(0.9, 1.3), [(200, 80, 110), (150, 100, 200)][k % 2])
        for p in desparramado[:6]:
            hongo(s, p, 0.35, (200, 80, 110))
    elif deco == "volcan":
        volcan(s, (cx + w * 0.3, cy - h * 0.18), w * 0.26, h * 0.4)
        for p in desparramado[:5]:
            roca(s, p, rng.uniform(12, 22), (120, 100, 96))
        arbol_seco(s, atras[0], 90)
    elif deco == "calavera":
        calavera_roca(s, (cx + w * 0.36, cy - h * 0.3), 46)
        for p in (atras[0], atras[2], (cx - w * 0.05, cy - h * 0.33)):
            arbol_seco(s, p, rng.uniform(90, 120))
        for p in desparramado[:4]:
            roca(s, p, rng.uniform(10, 18), (120, 120, 130))


def volcan_cima(isla_pos, w, h):
    """Dónde sale el humo del volcán (en coordenadas de pantalla)."""
    cx, cy = isla_pos[0] + w / 2, isla_pos[1] + h * 0.55
    return (cx + w * 0.3, cy - h * 0.18 - h * 0.4)


def niebla():
    """Banda de niebla que se repite de costado (para la Isla Calavera)."""
    if "niebla" in _CACHE:
        return _CACHE["niebla"]
    s = Lienzo(*((ANCHO, 160)))
    rng = random.Random(4)
    for _ in range(26):
        w = rng.uniform(160, 340)
        h = rng.uniform(40, 80)
        x = rng.uniform(-w / 2, ANCHO - w / 2)
        y = rng.uniform(20, 120)
        dibujo.ellipse(s, (210, 210, 240, 26), (x, y, w, h))
    _CACHE["niebla"] = s
    return s
