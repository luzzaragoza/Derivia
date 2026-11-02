"""Ropa y accesorios del gato. Cada prenda se dibuja con formas en el espacio de
diseño del gato (200 de ancho; cabeza entre y=30 y y=142, ojos en y≈84, cuello y≈140)."""

import math
from dataclasses import dataclass

import pygame

from .ui import BORDE

LUGARES = [("cabeza", "Cabeza"), ("cara", "Cara"), ("cuello", "Cuello"), ("cuerpo", "Cuerpo"), ("espalda", "Espalda"),
           ("mano", "Mano"), ("cola", "Cola")]

ORO = (255, 206, 84)
ORO_OSC = (214, 150, 30)
ROJO = (222, 66, 70)
BLANCO = (255, 255, 255)
NEGRO = (46, 40, 52)


@dataclass
class Prenda:
    id: str
    nombre: str
    lugar: str
    precio: int
    dibujar: object
    frente: object = None      # parte que va adelante del cuerpo (tiras, broches)


def _circulos(lz, centros, r, color):
    """Varias bolitas con contorno de una sola vez (pelucas, collares)."""
    for x, y in centros:
        lz.d.circle(lz.s, BORDE, lz.P(x, y), (r + 2) * lz.K)
    for x, y in centros:
        lz.d.circle(lz.s, color, lz.P(x, y), r * lz.K)


def _linea(lz, a, b, color, ancho):
    lz.d.line(lz.s, color, lz.P(*a), lz.P(*b), max(1, int(ancho * lz.K)))


def _flor(lz, cx, cy, r, color, centro=ORO):
    for k in range(5):
        a = k * math.tau / 5 - math.pi / 2
        lz.d.circle(lz.s, BORDE, lz.P(cx + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75), (r * 0.62 + 1.5) * lz.K)
    for k in range(5):
        a = k * math.tau / 5 - math.pi / 2
        lz.d.circle(lz.s, color, lz.P(cx + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75), r * 0.62 * lz.K)
    lz.d.circle(lz.s, centro, lz.P(cx, cy), r * 0.4 * lz.K)


# ------------------------------------------------------------ cabeza
def _corona(lz):
    lz.poligono([(60, 38), (58, 8), (76, 24), (88, -2), (100, 20), (112, -2), (124, 24), (142, 8), (140, 38)], ORO)
    for x, c in ((80, (90, 160, 255)), (100, ROJO), (120, (90, 200, 120))):
        lz.d.circle(lz.s, BORDE, lz.P(x, 31), 6 * lz.K)
        lz.d.circle(lz.s, c, lz.P(x, 31), 4.5 * lz.K)
    for x, y in ((58, 8), (88, -2), (112, -2), (142, 8)):
        lz.d.circle(lz.s, ORO_OSC, lz.P(x, y), 3.5 * lz.K)


def _pirata(lz):
    lz.poligono([(22, 50), (48, 14), (100, 0), (152, 14), (178, 50), (140, 40), (100, 36), (60, 40)], NEGRO)
    _linea(lz, (30, 47), (60, 39), ORO, 3)
    _linea(lz, (60, 39), (100, 35), ORO, 3)
    _linea(lz, (100, 35), (140, 39), ORO, 3)
    _linea(lz, (140, 39), (170, 47), ORO, 3)
    lz.d.circle(lz.s, BLANCO, lz.P(100, 18), 8 * lz.K)
    lz.d.rect(lz.s, BLANCO, lz.R(95, 21, 10, 7))
    for dx in (-3, 3):
        lz.d.circle(lz.s, NEGRO, lz.P(100 + dx, 17), 2.2 * lz.K)
    _linea(lz, (88, 30), (112, 22), BLANCO, 2.5)
    _linea(lz, (88, 22), (112, 30), BLANCO, 2.5)


def _fiesta(lz):
    pts = [(98, 40), (150, 34), (136, -22)]
    lz.poligono(pts, (120, 200, 230))
    for k in range(1, 4):
        t = k / 4
        a = (98 + (136 - 98) * t, 40 + (-22 - 40) * t)
        b = (150 + (136 - 150) * t, 34 + (-22 - 34) * t)
        _linea(lz, a, b, (255, 120, 150), 5)
    lz.d.circle(lz.s, BORDE, lz.P(136, -24), 10 * lz.K)
    lz.d.circle(lz.s, ORO, lz.P(136, -24), 8 * lz.K)


def _paja(lz):
    lz.elipse(lz.R(10, 26, 180, 32), (236, 200, 120))
    lz.elipse(lz.R(52, -6, 96, 52), (240, 208, 132))
    lz.d.rect(lz.s, (250, 124, 104), lz.R(53, 26, 94, 11))
    _flor(lz, 132, 30, 9, (255, 150, 190))
    for x in range(64, 140, 12):
        _linea(lz, (x, 2), (x + 4, 22), (214, 172, 96), 1.5)


def _birrete(lz):
    lz.elipse(lz.R(64, 16, 72, 30), (52, 56, 92))
    lz.poligono([(30, 16), (100, -8), (170, 16), (100, 38)], (60, 64, 104))
    lz.d.circle(lz.s, ORO, lz.P(100, 15), 4 * lz.K)
    _linea(lz, (100, 15), (150, 22), ORO, 3)
    _linea(lz, (150, 22), (154, 50), ORO, 3)
    lz.d.rect(lz.s, ORO_OSC, lz.R(149, 48, 10, 14), border_radius=int(2 * lz.K))


def _boina(lz):
    lz.elipse(lz.R(24, 20, 132, 42), (220, 70, 80))
    lz.d.ellipse(lz.s, (240, 110, 116), lz.R(42, 26, 70, 14))
    lz.elipse(lz.R(84, 12, 12, 12), (220, 70, 80))


def _rulos(lz):
    centros = []
    for k in range(11):
        a = math.pi + k * math.pi / 10
        centros.append((100 + math.cos(a) * 70, 66 + math.sin(a) * 50))
    centros += [(30, 80), (170, 80), (28, 98), (172, 98), (70, 22), (100, 16), (130, 22), (85, 30), (115, 30)]
    _circulos(lz, centros, 15, (250, 214, 110))
    for x, y in centros[::3]:
        lz.d.circle(lz.s, (255, 236, 170), lz.P(x - 4, y - 4), 4 * lz.K)


def _peluca_rosa(lz):
    rosa, rosa_osc = (255, 150, 190), (230, 110, 160)
    K, G = lz.K, lz.G
    formas = [("e", lz.R(12, 50, 38, 104)), ("e", lz.R(150, 50, 38, 104)), ("e", lz.R(22, 14, 156, 70))]
    flequillo = [(46 + k * 18, 60) for k in range(7)]
    for tipo, r in formas:
        lz.d.ellipse(lz.s, BORDE, r.inflate(G * 2, G * 2))
    for x, y in flequillo:
        lz.d.circle(lz.s, BORDE, lz.P(x, y), 11 * K + G)
    for tipo, r in formas:
        lz.d.ellipse(lz.s, rosa, r)
    for x, y in flequillo:
        lz.d.circle(lz.s, rosa, lz.P(x, y), 11 * K)
    for x in (60, 90, 120, 140):
        _linea(lz, (x, 24), (x + 8, 44), rosa_osc, 2.5)
    for x in (24, 168):
        _linea(lz, (x, 70), (x + 4, 130), rosa_osc, 2.5)
    _flor(lz, 156, 34, 10, (255, 230, 120), (250, 124, 104))


def _vincha(lz):
    rect = lz.R(34, 18, 132, 90)
    lz.d.arc(lz.s, BORDE, rect.inflate(lz.G * 2, lz.G * 2), 0.35, math.pi - 0.35, int(11 * lz.K))
    lz.d.arc(lz.s, (250, 124, 104), rect, 0.38, math.pi - 0.38, int(7 * lz.K))
    _flor(lz, 52, 40, 16, (255, 120, 150))


def _lana(lz):
    d = 14
    lz.poligono([(30, 52 + d), (34, 26 + d), (60, 6 + d), (100, 0 + d), (140, 6 + d), (166, 26 + d), (170, 52 + d)],
                (120, 196, 200))
    for x in range(48, 160, 16):
        _linea(lz, (x, 12 + d), (x - 2, 48 + d), (90, 170, 176), 3)
    lz.d.rect(lz.s, BORDE, lz.R(26, 40 + d, 148, 22), border_radius=int(10 * lz.K))
    lz.d.rect(lz.s, (240, 236, 220), lz.R(29, 42 + d, 142, 17), border_radius=int(9 * lz.K))
    lz.d.circle(lz.s, BORDE, lz.P(100, -4 + d), 15 * lz.K)
    lz.d.circle(lz.s, (250, 124, 104), lz.P(100, -4 + d), 13 * lz.K)


# ------------------------------------------------------------ cara
def _anteojos(lz):
    for cx in (74, 126):
        lz.d.circle(lz.s, BORDE, lz.P(cx, 84), 17 * lz.K, int(4 * lz.K))
    _linea(lz, (91, 82), (109, 82), BORDE, 3.5)
    _linea(lz, (57, 80), (34, 76), BORDE, 3.5)
    _linea(lz, (143, 80), (166, 76), BORDE, 3.5)


def _sol(lz):
    for x in (54, 106):
        lz.d.rect(lz.s, BORDE, lz.R(x - 2, 70, 44, 32), border_radius=int(12 * lz.K))
        lz.d.rect(lz.s, (44, 42, 70), lz.R(x, 72, 40, 28), border_radius=int(11 * lz.K))
        _linea(lz, (x + 8, 78), (x + 18, 76), (190, 200, 255), 3)
    _linea(lz, (94, 80), (106, 80), BORDE, 4)
    _linea(lz, (52, 80), (32, 76), BORDE, 3.5)
    _linea(lz, (148, 80), (168, 76), BORDE, 3.5)


def _parche(lz):
    _linea(lz, (40, 54), (164, 106), NEGRO, 3.5)
    lz.elipse(lz.R(112, 70, 30, 28), NEGRO)


def _corazones(lz):
    for cx in (74, 126):
        pts = []
        for k in range(30):
            t = k / 30 * math.tau
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
            pts.append((cx + x * 1.05, 84 + y * 1.05))
        lz.poligono(pts, (255, 110, 150))
        lz.d.circle(lz.s, (255, 200, 220), lz.P(cx - 7, 78), 3 * lz.K)
    _linea(lz, (92, 82), (108, 82), BORDE, 3.5)


# ------------------------------------------------------------ cuello
def _parabola(x0, x1, y0, curva, n):
    return [(x0 + (x1 - x0) * k / (n - 1), y0 + curva * (1 - ((2 * k / (n - 1)) - 1) ** 2)) for k in range(n)]


def _cascabel(lz):
    pts = _parabola(62, 138, 134, 10, 12)
    lz.trazo(pts, ROJO, 5)
    lz.elipse(lz.R(91, 142, 18, 18), ORO)
    _linea(lz, (100, 152), (100, 159), ORO_OSC, 2.5)
    lz.d.circle(lz.s, (255, 240, 180), lz.P(96, 147), 2.5 * lz.K)


def _monio(lz):
    lz.poligono([(100, 146), (74, 132), (74, 162)], (250, 110, 120))
    lz.poligono([(100, 146), (126, 132), (126, 162)], (250, 110, 120))
    for x, y in ((82, 140), (82, 154), (118, 140), (118, 154)):
        lz.d.circle(lz.s, BLANCO, lz.P(x, y), 2.5 * lz.K)
    lz.elipse(lz.R(93, 139, 14, 14), (220, 80, 96))


def _bufanda(lz):
    pts = _parabola(56, 144, 132, 10, 14)
    lz.trazo(pts, (120, 196, 200), 9)
    lz.d.rect(lz.s, BORDE, lz.R(108, 138, 24, 56), border_radius=int(4 * lz.K))
    lz.d.rect(lz.s, (120, 196, 200), lz.R(110, 140, 20, 52), border_radius=int(3 * lz.K))
    for y in (150, 166, 182):
        lz.d.rect(lz.s, (255, 248, 230), lz.R(110, y, 20, 6))
    for x in range(112, 130, 5):
        _linea(lz, (x, 192), (x, 200), (120, 196, 200), 2)
    for x, y in pts[2:-2:3]:
        lz.d.circle(lz.s, (255, 248, 230), lz.P(x, y), 3 * lz.K)


def _perlas(lz):
    _circulos(lz, _parabola(64, 136, 136, 14, 11), 5.5, (255, 252, 244))


def _panuelo(lz):
    lz.poligono([(62, 134), (138, 134), (100, 174)], ROJO)
    for x, y in ((84, 142), (100, 150), (116, 142), (100, 162), (92, 154), (108, 154)):
        lz.d.circle(lz.s, BLANCO, lz.P(x, y), 2.5 * lz.K)
    lz.elipse(lz.R(56, 128, 16, 14), ROJO)


def _lei(lz):
    colores = [(250, 124, 104), (255, 214, 102), (255, 150, 190), (255, 255, 255)]
    for k, (x, y) in enumerate(_parabola(56, 144, 134, 18, 10)):
        _flor(lz, x, y, 9, colores[k % 4])


# ------------------------------------------------------------ espalda
def _capa(lz):
    lz.poligono([(52, 118), (148, 118), (198, 220), (2, 220)], (214, 60, 76))
    lz.poligono([(60, 126), (140, 126), (184, 214), (16, 214)], (236, 92, 104), contorno=False)


def _alas(lz):
    for lado in (-1, 1):
        base = (100 + lado * 44, 150)
        pts = [base, (100 + lado * 92, 96), (100 + lado * 104, 118), (100 + lado * 98, 140),
               (100 + lado * 102, 158), (100 + lado * 86, 176), (100 + lado * 60, 172)]
        lz.poligono(pts, (255, 255, 255))
        for k in range(3):
            _linea(lz, (100 + lado * 56, 156), (100 + lado * (82 + 6 * k), 118 + 18 * k), (210, 222, 240), 2.5)


def _capa_frente(lz):
    for lado in (-1, 1):
        lz.poligono([(100 + lado * 30, 132), (100 + lado * 52, 124), (100 + lado * 50, 146)], (214, 60, 76))
        lz.d.circle(lz.s, BORDE, lz.P(100 + lado * 30, 136), 6 * lz.K)
        lz.d.circle(lz.s, ORO, lz.P(100 + lado * 30, 136), 4.5 * lz.K)


def _mochila_frente(lz):
    for x0, x1 in ((72, 78), (128, 122)):
        _linea(lz, (x0, 128), (x1, 178), BORDE, 9)
        _linea(lz, (x0, 128), (x1, 178), (92, 160, 82), 6)


def _mochila(lz):
    lz.elipse(lz.R(136, 112, 64, 80), (122, 196, 106))
    lz.d.rect(lz.s, BORDE, lz.R(156, 140, 36, 24), border_radius=int(6 * lz.K))
    lz.d.rect(lz.s, (92, 160, 82), lz.R(158, 142, 32, 20), border_radius=int(5 * lz.K))
    lz.d.circle(lz.s, ORO, lz.P(174, 152), 3.5 * lz.K)


# ------------------------------------------------------------ cola
def _monio_cola(lz):
    x, y = lz.cola[-4]
    lz.poligono([(x, y), (x - 16, y - 12), (x - 16, y + 12)], (255, 150, 190))
    lz.poligono([(x, y), (x + 16, y - 12), (x + 16, y + 12)], (255, 150, 190))
    lz.elipse(lz.R(x - 6, y - 6, 12, 12), (250, 110, 150))


def _cascabel_cola(lz):
    x, y = lz.cola[-6]
    lz.elipse(lz.R(x - 9, y - 4, 18, 18), ORO)
    lz.d.circle(lz.s, (255, 240, 180), lz.P(x - 3, y + 1), 2.5 * lz.K)


# ------------------------------------------------------------ nuevas: cabeza
ROSA_P, LILA, CELESTE_P, PLATA = (255, 150, 190), (170, 120, 220), (150, 210, 240), (220, 224, 236)


def _tiara(lz):
    pts = [(58, 40), (66, 22), (78, 32), (88, 12), (100, 28), (112, 12), (122, 32), (134, 22), (142, 40)]
    lz.poligono(pts + [(142, 46), (58, 46)], PLATA)
    for x, y, c in ((88, 18, (120, 200, 255)), (100, 34, ROSA_P), (112, 18, (120, 200, 255))):
        lz.d.circle(lz.s, BORDE, lz.P(x, y), 5.5 * lz.K)
        lz.d.circle(lz.s, c, lz.P(x, y), 4 * lz.K)


def _monio_gigante(lz):
    lz.poligono([(128, 30), (98, 4), (96, 50)], ROSA_P)
    lz.poligono([(128, 30), (164, 2), (168, 52)], ROSA_P)
    for x, y in ((108, 22), (154, 24)):
        lz.d.circle(lz.s, BLANCO, lz.P(x, y), 3 * lz.K)
    lz.elipse(lz.R(118, 20, 20, 20), (240, 110, 160))


def _auriculares(lz):
    rect = lz.R(22, 8, 156, 130)
    lz.d.arc(lz.s, BORDE, rect.inflate(lz.G * 2, lz.G * 2), 0.2, math.pi - 0.2, int(12 * lz.K))
    lz.d.arc(lz.s, (80, 80, 96), rect, 0.22, math.pi - 0.22, int(8 * lz.K))
    for x in (14, 162):
        lz.elipse(lz.R(x, 66, 26, 42), (100, 200, 200))
        lz.d.ellipse(lz.s, (60, 150, 160), lz.R(x + 6, 74, 14, 26))


def _gorra(lz):
    lz.poligono([(120, 40), (178, 30), (184, 44), (128, 52)], (250, 124, 104))
    lz.poligono([(34, 52), (40, 22), (72, 6), (110, 4), (140, 16), (156, 46)], (250, 124, 104))
    _linea(lz, (98, 6), (100, 46), (220, 90, 76), 3)
    lz.d.circle(lz.s, BORDE, lz.P(100, 5), 5 * lz.K)


def _casco(lz):
    r = lz.R(6, -4, 188, 168)
    lz.d.ellipse(lz.s, BORDE, r.inflate(lz.G * 2, lz.G * 2), int(12 * lz.K))
    lz.d.ellipse(lz.s, (236, 240, 248), r, int(9 * lz.K))
    lz.d.arc(lz.s, BLANCO, lz.R(28, 12, 80, 70), math.pi * 0.55, math.pi * 0.95, int(5 * lz.K))
    _linea(lz, (150, 2), (166, -26), BORDE, 3)
    lz.d.circle(lz.s, (250, 124, 104), lz.P(166, -28), 6 * lz.K)


def _gorro_chef(lz):
    _circulos(lz, [(64, 10), (88, -2), (112, -2), (136, 10), (76, 22), (124, 22), (100, 12)], 20, BLANCO)
    lz.d.rect(lz.s, BORDE, lz.R(50, 26, 100, 26), border_radius=int(6 * lz.K))
    lz.d.rect(lz.s, BLANCO, lz.R(53, 28, 94, 21), border_radius=int(5 * lz.K))


def _bruja(lz):
    lz.elipse(lz.R(12, 32, 176, 28), (110, 70, 160))
    lz.poligono([(52, 44), (148, 44), (128, 0), (120, -20), (150, -34), (104, -18), (76, 10)], (124, 82, 180))
    lz.d.rect(lz.s, (255, 206, 84), lz.R(56, 30, 88, 12))
    lz.d.rect(lz.s, BORDE, lz.R(92, 28, 16, 16), int(3 * lz.K))
    for x, y in ((80, 10), (116, -6)):
        _estrellita(lz, x, y, 5, (255, 236, 140))


def _estrellita(lz, cx, cy, r, color):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    lz.d.polygon(lz.s, color, [lz.P(*p) for p in pts])


def _corona_flores(lz):
    colores = [ROSA_P, (255, 230, 120), BLANCO, (186, 150, 236)]
    for k in range(7):
        a = math.pi + (k + 0.5) * math.pi / 7
        _flor(lz, 100 + math.cos(a) * 66, 60 + math.sin(a) * 44, 9, colores[k % 4])


def _unicornio(lz):
    lz.poligono([(88, 34), (112, 34), (100, -30)], (255, 236, 170))
    for k, y in enumerate((20, 6, -8)):
        _linea(lz, (90 + k * 3, y + 6), (110 - k * 3, y - 2), (240, 190, 120), 2.5)
    _flor(lz, 72, 36, 8, ROSA_P)
    _flor(lz, 128, 36, 8, (186, 150, 236))


# ------------------------------------------------------------ nuevas: cara
def _anteojos_3d(lz):
    for x, c in ((54, (240, 70, 80)), (106, (70, 150, 240))):
        lz.d.rect(lz.s, BORDE, lz.R(x - 2, 70, 44, 30), border_radius=int(6 * lz.K))
        lz.d.rect(lz.s, BLANCO, lz.R(x, 72, 40, 26), border_radius=int(5 * lz.K))
        lz.d.rect(lz.s, c, lz.R(x + 4, 76, 32, 18), border_radius=int(4 * lz.K))
    _linea(lz, (52, 80), (32, 76), BORDE, 3.5)
    _linea(lz, (148, 80), (168, 76), BORDE, 3.5)


def _brillitos(lz):
    for x, y, r in ((46, 112, 7), (154, 112, 7), (40, 96, 4), (160, 96, 4)):
        _estrellita(lz, x, y, r + 1.5, BORDE)
        _estrellita(lz, x, y, r, (255, 230, 120))
    for x in (60, 140):
        lz.d.circle(lz.s, (255, 120, 160), lz.P(x, 107), 4 * lz.K)


def _antifaz(lz):
    for cx in (74, 126):
        lz.d.ellipse(lz.s, BORDE, lz.R(cx - 21, 68, 42, 34), int(11 * lz.K))
        lz.d.ellipse(lz.s, (150, 80, 200), lz.R(cx - 19, 70, 38, 30), int(7 * lz.K))
    _linea(lz, (93, 82), (107, 82), (150, 80, 200), 7)
    lz.poligono([(55, 80), (34, 70), (40, 90)], (150, 80, 200))
    lz.poligono([(145, 80), (166, 70), (160, 90)], (150, 80, 200))


# ------------------------------------------------------------ nuevas: cuello
def _cadena_oro(lz):
    _circulos(lz, _parabola(62, 138, 134, 14, 13), 4.5, ORO)
    lz.elipse(lz.R(89, 146, 22, 22), ORO)
    _estrellita(lz, 100, 157, 6, (255, 248, 220))


def _collar_corazon(lz):
    for (x1, y1), (x2, y2) in zip(_parabola(66, 134, 134, 12, 9), _parabola(66, 134, 134, 12, 9)[1:]):
        _linea(lz, (x1, y1), (x2, y2), PLATA, 2.5)
    pts = []
    for k in range(24):
        t = k / 24 * math.tau
        pts.append((100 + 8 * math.sin(t) ** 3 * 0.9, 156 - (6.5 * math.cos(t) - 2.5 * math.cos(2 * t) - math.cos(3 * t))))
    lz.poligono(pts, (255, 110, 150))


# ------------------------------------------------------------ cuerpo (va encima de la panza)
def _remera(lz, color, simbolo=None):
    lz.poligono([(52, 128), (78, 120), (100, 128), (122, 120), (148, 128), (156, 160), (144, 166), (146, 200),
                 (54, 200), (56, 166), (44, 160)], color)
    if simbolo:
        t = pygame.font.Font(None, int(44 * lz.K)).render(simbolo, True, BLANCO)
        lz.s.blit(t, t.get_rect(center=lz.P(100, 166)))


def _remera_integral(lz):
    _remera(lz, (64, 182, 196), "f'")


def _buzo(lz):
    _remera(lz, (170, 120, 220))
    lz.d.rect(lz.s, (140, 96, 196), lz.R(74, 172, 52, 20), border_radius=int(6 * lz.K))
    for x in (90, 110):
        _linea(lz, (x, 130), (x, 152), BLANCO, 2.5)


def _vestido(lz):
    lz.poligono([(64, 124), (136, 124), (150, 166), (176, 210), (24, 210), (50, 166)], ROSA_P)
    _circulos(lz, [(30 + k * 20, 210) for k in range(8)], 9, (255, 190, 214))
    lz.d.rect(lz.s, (240, 110, 160), lz.R(58, 156, 84, 10))
    for x, y in ((76, 184), (100, 194), (124, 184), (88, 136), (112, 136)):
        lz.d.circle(lz.s, BLANCO, lz.P(x, y), 3 * lz.K)
    lz.elipse(lz.R(92, 152, 16, 16), (240, 110, 160))


def _tutu(lz):
    for k, color in enumerate(((255, 190, 214), ROSA_P)):
        _circulos(lz, [(38 + j * 18 + k * 9, 178 + k * 8) for j in range(7 - k)], 12, color)


def _delantal(lz):
    lz.poligono([(70, 134), (130, 134), (136, 204), (64, 204)], BLANCO)
    lz.d.rect(lz.s, BORDE, lz.R(84, 168, 32, 20), int(2.5 * lz.K), border_radius=int(4 * lz.K))
    for x0, x1 in ((70, 56), (130, 144)):
        _linea(lz, (x0, 134), (x1, 120), BLANCO, 4)


def _traje_astronauta(lz):
    _remera(lz, (236, 240, 248))
    lz.d.rect(lz.s, BORDE, lz.R(78, 146, 44, 30), border_radius=int(4 * lz.K))
    lz.d.rect(lz.s, (210, 216, 230), lz.R(80, 148, 40, 26), border_radius=int(3 * lz.K))
    for k, c in enumerate(((250, 124, 104), (122, 196, 106), (255, 206, 84))):
        lz.d.circle(lz.s, c, lz.P(88 + k * 12, 161), 4 * lz.K)
    lz.elipse(lz.R(56, 136, 16, 16), (70, 120, 220))


def _overol(lz):
    lz.poligono([(60, 162), (140, 162), (148, 204), (52, 204)], (90, 130, 200))
    lz.d.rect(lz.s, (90, 130, 200), lz.R(76, 140, 48, 26))
    for x0 in (78, 122):
        _linea(lz, (x0, 142), (x0 + (-12 if x0 < 100 else 12), 124), (90, 130, 200), 6)
        lz.d.circle(lz.s, ORO, lz.P(x0, 146), 3.5 * lz.K)


# ------------------------------------------------------------ nuevas: espalda
def _alas_hada(lz):
    for lado in (-1, 1):
        lz.elipse(lz.R(100 + lado * 74 - 32, 80, 64, 80), (160, 220, 250))
        lz.elipse(lz.R(100 + lado * 66 - 22, 148, 44, 50), (255, 180, 216))
        _linea(lz, (100 + lado * 50, 140), (100 + lado * 86, 100), (120, 190, 230), 2.5)


def _jetpack(lz):
    for x in (28, 148):
        lz.d.rect(lz.s, BORDE, lz.R(x - 3, 120, 30, 70), border_radius=int(10 * lz.K))
        lz.d.rect(lz.s, (180, 186, 200), lz.R(x, 122, 24, 66), border_radius=int(9 * lz.K))
        lz.poligono([(x + 2, 190), (x + 22, 190), (x + 12, 214)], (255, 170, 60))
        lz.poligono([(x + 7, 190), (x + 17, 190), (x + 12, 204)], (255, 236, 140), contorno=False)


def _capa_violeta(lz):
    lz.poligono([(52, 118), (148, 118), (198, 220), (2, 220)], (110, 70, 160))
    for x, y in ((24, 196), (176, 196), (40, 160), (162, 164)):
        _estrellita(lz, x, y, 6, (255, 230, 120))


def _capa_violeta_frente(lz):
    for lado in (-1, 1):
        lz.poligono([(100 + lado * 30, 132), (100 + lado * 52, 124), (100 + lado * 50, 146)], (110, 70, 160))
    lz.d.circle(lz.s, BORDE, lz.P(100, 140), 7 * lz.K)
    lz.d.circle(lz.s, ORO, lz.P(100, 140), 5 * lz.K)


# ------------------------------------------------------------ mano (al costado de la pata derecha)
def _varita(lz):
    _linea(lz, (128, 196), (170, 120), BORDE, 6)
    _linea(lz, (128, 196), (170, 120), (120, 80, 60), 3.5)
    _estrellita(lz, 172, 116, 15, BORDE)
    _estrellita(lz, 172, 116, 12, (255, 220, 100))


def _cartera(lz):
    lz.d.arc(lz.s, BORDE, lz.R(140, 140, 40, 46), 0, math.pi, int(4 * lz.K))
    lz.poligono([(134, 164), (186, 164), (180, 206), (140, 206)], ROSA_P)
    lz.d.circle(lz.s, ORO, lz.P(160, 172), 4 * lz.K)


def _globo(lz):
    _linea(lz, (128, 198), (176, 74), BORDE, 1.8)
    lz.elipse(lz.R(160, 18, 40, 52), (250, 90, 100))
    lz.d.ellipse(lz.s, (255, 170, 170), lz.R(168, 26, 10, 14))


def _helado(lz):
    lz.poligono([(134, 170), (164, 170), (149, 210)], (230, 180, 110))
    _circulos(lz, [(142, 160), (156, 160), (149, 146)], 10, (255, 190, 214))
    lz.d.circle(lz.s, ROJO, lz.P(149, 134), 4 * lz.K)


CATALOGO = [
    Prenda("vincha_flor", "Vincha con flor", "cabeza", 80, _vincha),
    Prenda("gorro_fiesta", "Gorrito de fiesta", "cabeza", 120, _fiesta),
    Prenda("boina", "Boina", "cabeza", 150, _boina),
    Prenda("gorro_lana", "Gorro de lana", "cabeza", 180, _lana),
    Prenda("sombrero_paja", "Sombrero de paja", "cabeza", 250, _paja),
    Prenda("gorro_pirata", "Sombrero pirata", "cabeza", 320, _pirata),
    Prenda("peluca_rulos", "Peluca de rulos", "cabeza", 400, _rulos),
    Prenda("peluca_rosa", "Peluca rosa", "cabeza", 450, _peluca_rosa),
    Prenda("birrete", "Birrete de egresada", "cabeza", 700, _birrete),
    Prenda("corona", "Corona", "cabeza", 1000, _corona),
    Prenda("anteojos", "Anteojos de estudiar", "cara", 80, _anteojos),
    Prenda("parche", "Parche pirata", "cara", 150, _parche),
    Prenda("anteojos_sol", "Anteojos de sol", "cara", 220, _sol),
    Prenda("corazones", "Anteojos corazón", "cara", 350, _corazones),
    Prenda("cascabel", "Collar con cascabel", "cuello", 60, _cascabel),
    Prenda("monio", "Moño", "cuello", 100, _monio),
    Prenda("panuelo", "Pañuelo pirata", "cuello", 140, _panuelo),
    Prenda("bufanda", "Bufanda", "cuello", 220, _bufanda),
    Prenda("collar_flores", "Collar de flores", "cuello", 260, _lei),
    Prenda("perlas", "Collar de perlas", "cuello", 500, _perlas),
    Prenda("mochila", "Mochila", "espalda", 200, _mochila, _mochila_frente),
    Prenda("capa", "Capa de superheroína", "espalda", 450, _capa, _capa_frente),
    Prenda("alas", "Alitas", "espalda", 750, _alas),
    Prenda("tiara", "Tiara", "cabeza", 900, _tiara),
    Prenda("monio_gigante", "Moño gigante", "cabeza", 350, _monio_gigante),
    Prenda("auriculares", "Auriculares", "cabeza", 600, _auriculares),
    Prenda("gorra", "Gorra canchera", "cabeza", 300, _gorra),
    Prenda("casco", "Casco espacial", "cabeza", 2000, _casco),
    Prenda("gorro_chef", "Gorro de chef", "cabeza", 700, _gorro_chef),
    Prenda("sombrero_bruja", "Sombrero de bruja", "cabeza", 1200, _bruja),
    Prenda("corona_flores", "Corona de flores", "cabeza", 500, _corona_flores),
    Prenda("unicornio", "Cuerno de unicornio", "cabeza", 1500, _unicornio),
    Prenda("anteojos_3d", "Anteojos 3D", "cara", 400, _anteojos_3d),
    Prenda("brillitos", "Brillitos", "cara", 250, _brillitos),
    Prenda("antifaz", "Antifaz", "cara", 700, _antifaz),
    Prenda("cadena_oro", "Cadena de oro", "cuello", 800, _cadena_oro),
    Prenda("collar_corazon", "Collar de corazón", "cuello", 450, _collar_corazon),
    Prenda("remera", "Remera f′", "cuerpo", 500, _remera_integral),
    Prenda("overol", "Overol", "cuerpo", 600, _overol),
    Prenda("buzo", "Buzo lila", "cuerpo", 700, _buzo),
    Prenda("delantal", "Delantal de chef", "cuerpo", 700, _delantal),
    Prenda("tutu", "Tutú", "cuerpo", 900, _tutu),
    Prenda("vestido", "Vestido rosa", "cuerpo", 1200, _vestido),
    Prenda("traje_astronauta", "Traje espacial", "cuerpo", 2200, _traje_astronauta),
    Prenda("capa_violeta", "Capa de bruja", "espalda", 900, _capa_violeta, _capa_violeta_frente),
    Prenda("alas_hada", "Alas de hada", "espalda", 1400, _alas_hada),
    Prenda("jetpack", "Mochila cohete", "espalda", 1800, _jetpack),
    Prenda("globo", "Globito", "mano", 300, _globo),
    Prenda("helado", "Helado", "mano", 350, _helado),
    Prenda("cartera", "Cartera", "mano", 650, _cartera),
    Prenda("varita", "Varita mágica", "mano", 1000, _varita),
    Prenda("monio_cola", "Moño en la cola", "cola", 90, _monio_cola),
    Prenda("cascabel_cola", "Cascabel en la cola", "cola", 120, _cascabel_cola),
]
POR_ID = {p.id: p for p in CATALOGO}


def dibujar_capa(lugar, ropa, lz):
    for item in ropa:
        p = POR_ID.get(item)
        if p and p.lugar == lugar:
            p.dibujar(lz)
        if p and p.frente and lugar == "cuello":
            p.frente(lz)


@dataclass
class Conjunto:
    id: str
    nombre: str
    piezas: tuple
    precio: int


CONJUNTOS = [
    Conjunto("set_pirata", "Pirata", ("gorro_pirata", "parche", "panuelo"), 520),
    Conjunto("set_super", "Superheroína", ("antifaz", "capa", "remera"), 1400),
    Conjunto("set_chef", "Chef", ("gorro_chef", "delantal", "helado"), 1500),
    Conjunto("set_unicornio", "Unicornio", ("unicornio", "brillitos", "monio_cola"), 1600),
    Conjunto("set_hada", "Hada", ("corona_flores", "alas_hada", "tutu"), 2300),
    Conjunto("set_bruja", "Bruja", ("sombrero_bruja", "capa_violeta", "varita"), 2500),
    Conjunto("set_princesa", "Princesa", ("tiara", "vestido", "varita"), 2600),
    Conjunto("set_astronauta", "Astronauta", ("casco", "traje_astronauta", "jetpack"), 4800),
]
CONJUNTO_POR_ID = {c.id: c for c in CONJUNTOS}
