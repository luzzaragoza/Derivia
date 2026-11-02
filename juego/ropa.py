"""Ropa y accesorios del gato. Cada prenda se dibuja con formas en el espacio de
diseño del gato (200 de ancho; cabeza entre y=30 y y=142, ojos en y≈84, cuello y≈140)."""

import math
from dataclasses import dataclass

import pygame

from .ui import BORDE

LUGARES = [("cabeza", "Cabeza"), ("cara", "Cara"), ("cuello", "Cuello"), ("espalda", "Espalda"), ("cola", "Cola")]

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
        pygame.draw.circle(lz.s, BORDE, lz.P(x, y), (r + 2) * lz.K)
    for x, y in centros:
        pygame.draw.circle(lz.s, color, lz.P(x, y), r * lz.K)


def _linea(lz, a, b, color, ancho):
    pygame.draw.line(lz.s, color, lz.P(*a), lz.P(*b), max(1, int(ancho * lz.K)))


def _flor(lz, cx, cy, r, color, centro=ORO):
    for k in range(5):
        a = k * math.tau / 5 - math.pi / 2
        pygame.draw.circle(lz.s, BORDE, lz.P(cx + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75), (r * 0.62 + 1.5) * lz.K)
    for k in range(5):
        a = k * math.tau / 5 - math.pi / 2
        pygame.draw.circle(lz.s, color, lz.P(cx + math.cos(a) * r * 0.75, cy + math.sin(a) * r * 0.75), r * 0.62 * lz.K)
    pygame.draw.circle(lz.s, centro, lz.P(cx, cy), r * 0.4 * lz.K)


# ------------------------------------------------------------ cabeza
def _corona(lz):
    lz.poligono([(60, 38), (58, 8), (76, 24), (88, -2), (100, 20), (112, -2), (124, 24), (142, 8), (140, 38)], ORO)
    for x, c in ((80, (90, 160, 255)), (100, ROJO), (120, (90, 200, 120))):
        pygame.draw.circle(lz.s, BORDE, lz.P(x, 31), 6 * lz.K)
        pygame.draw.circle(lz.s, c, lz.P(x, 31), 4.5 * lz.K)
    for x, y in ((58, 8), (88, -2), (112, -2), (142, 8)):
        pygame.draw.circle(lz.s, ORO_OSC, lz.P(x, y), 3.5 * lz.K)


def _pirata(lz):
    lz.poligono([(22, 50), (48, 14), (100, 0), (152, 14), (178, 50), (140, 40), (100, 36), (60, 40)], NEGRO)
    _linea(lz, (30, 47), (60, 39), ORO, 3)
    _linea(lz, (60, 39), (100, 35), ORO, 3)
    _linea(lz, (100, 35), (140, 39), ORO, 3)
    _linea(lz, (140, 39), (170, 47), ORO, 3)
    pygame.draw.circle(lz.s, BLANCO, lz.P(100, 18), 8 * lz.K)
    pygame.draw.rect(lz.s, BLANCO, lz.R(95, 21, 10, 7))
    for dx in (-3, 3):
        pygame.draw.circle(lz.s, NEGRO, lz.P(100 + dx, 17), 2.2 * lz.K)
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
    pygame.draw.circle(lz.s, BORDE, lz.P(136, -24), 10 * lz.K)
    pygame.draw.circle(lz.s, ORO, lz.P(136, -24), 8 * lz.K)


def _paja(lz):
    lz.elipse(lz.R(10, 26, 180, 32), (236, 200, 120))
    lz.elipse(lz.R(52, -6, 96, 52), (240, 208, 132))
    pygame.draw.rect(lz.s, (250, 124, 104), lz.R(53, 26, 94, 11))
    _flor(lz, 132, 30, 9, (255, 150, 190))
    for x in range(64, 140, 12):
        _linea(lz, (x, 2), (x + 4, 22), (214, 172, 96), 1.5)


def _birrete(lz):
    lz.elipse(lz.R(64, 16, 72, 30), (52, 56, 92))
    lz.poligono([(30, 16), (100, -8), (170, 16), (100, 38)], (60, 64, 104))
    pygame.draw.circle(lz.s, ORO, lz.P(100, 15), 4 * lz.K)
    _linea(lz, (100, 15), (150, 22), ORO, 3)
    _linea(lz, (150, 22), (154, 50), ORO, 3)
    pygame.draw.rect(lz.s, ORO_OSC, lz.R(149, 48, 10, 14), border_radius=int(2 * lz.K))


def _boina(lz):
    lz.elipse(lz.R(24, 20, 132, 42), (220, 70, 80))
    pygame.draw.ellipse(lz.s, (240, 110, 116), lz.R(42, 26, 70, 14))
    lz.elipse(lz.R(84, 12, 12, 12), (220, 70, 80))


def _rulos(lz):
    centros = []
    for k in range(11):
        a = math.pi + k * math.pi / 10
        centros.append((100 + math.cos(a) * 70, 66 + math.sin(a) * 50))
    centros += [(30, 80), (170, 80), (28, 98), (172, 98), (70, 22), (100, 16), (130, 22), (85, 30), (115, 30)]
    _circulos(lz, centros, 15, (250, 214, 110))
    for x, y in centros[::3]:
        pygame.draw.circle(lz.s, (255, 236, 170), lz.P(x - 4, y - 4), 4 * lz.K)


def _peluca_rosa(lz):
    rosa, rosa_osc = (255, 150, 190), (230, 110, 160)
    K, G = lz.K, lz.G
    formas = [("e", lz.R(12, 50, 38, 104)), ("e", lz.R(150, 50, 38, 104)), ("e", lz.R(22, 14, 156, 70))]
    flequillo = [(46 + k * 18, 60) for k in range(7)]
    for tipo, r in formas:
        pygame.draw.ellipse(lz.s, BORDE, r.inflate(G * 2, G * 2))
    for x, y in flequillo:
        pygame.draw.circle(lz.s, BORDE, lz.P(x, y), 11 * K + G)
    for tipo, r in formas:
        pygame.draw.ellipse(lz.s, rosa, r)
    for x, y in flequillo:
        pygame.draw.circle(lz.s, rosa, lz.P(x, y), 11 * K)
    for x in (60, 90, 120, 140):
        _linea(lz, (x, 24), (x + 8, 44), rosa_osc, 2.5)
    for x in (24, 168):
        _linea(lz, (x, 70), (x + 4, 130), rosa_osc, 2.5)
    _flor(lz, 156, 34, 10, (255, 230, 120), (250, 124, 104))


def _vincha(lz):
    rect = lz.R(34, 18, 132, 90)
    pygame.draw.arc(lz.s, BORDE, rect.inflate(lz.G * 2, lz.G * 2), 0.35, math.pi - 0.35, int(11 * lz.K))
    pygame.draw.arc(lz.s, (250, 124, 104), rect, 0.38, math.pi - 0.38, int(7 * lz.K))
    _flor(lz, 52, 40, 16, (255, 120, 150))


def _lana(lz):
    d = 14
    lz.poligono([(30, 52 + d), (34, 26 + d), (60, 6 + d), (100, 0 + d), (140, 6 + d), (166, 26 + d), (170, 52 + d)],
                (120, 196, 200))
    for x in range(48, 160, 16):
        _linea(lz, (x, 12 + d), (x - 2, 48 + d), (90, 170, 176), 3)
    pygame.draw.rect(lz.s, BORDE, lz.R(26, 40 + d, 148, 22), border_radius=int(10 * lz.K))
    pygame.draw.rect(lz.s, (240, 236, 220), lz.R(29, 42 + d, 142, 17), border_radius=int(9 * lz.K))
    pygame.draw.circle(lz.s, BORDE, lz.P(100, -4 + d), 15 * lz.K)
    pygame.draw.circle(lz.s, (250, 124, 104), lz.P(100, -4 + d), 13 * lz.K)


# ------------------------------------------------------------ cara
def _anteojos(lz):
    for cx in (74, 126):
        pygame.draw.circle(lz.s, BORDE, lz.P(cx, 84), 17 * lz.K, int(4 * lz.K))
    _linea(lz, (91, 82), (109, 82), BORDE, 3.5)
    _linea(lz, (57, 80), (34, 76), BORDE, 3.5)
    _linea(lz, (143, 80), (166, 76), BORDE, 3.5)


def _sol(lz):
    for x in (54, 106):
        pygame.draw.rect(lz.s, BORDE, lz.R(x - 2, 70, 44, 32), border_radius=int(12 * lz.K))
        pygame.draw.rect(lz.s, (44, 42, 70), lz.R(x, 72, 40, 28), border_radius=int(11 * lz.K))
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
        pygame.draw.circle(lz.s, (255, 200, 220), lz.P(cx - 7, 78), 3 * lz.K)
    _linea(lz, (92, 82), (108, 82), BORDE, 3.5)


# ------------------------------------------------------------ cuello
def _parabola(x0, x1, y0, curva, n):
    return [(x0 + (x1 - x0) * k / (n - 1), y0 + curva * (1 - ((2 * k / (n - 1)) - 1) ** 2)) for k in range(n)]


def _cascabel(lz):
    pts = _parabola(62, 138, 134, 10, 12)
    lz.trazo(pts, ROJO, 5)
    lz.elipse(lz.R(91, 142, 18, 18), ORO)
    _linea(lz, (100, 152), (100, 159), ORO_OSC, 2.5)
    pygame.draw.circle(lz.s, (255, 240, 180), lz.P(96, 147), 2.5 * lz.K)


def _monio(lz):
    lz.poligono([(100, 146), (74, 132), (74, 162)], (250, 110, 120))
    lz.poligono([(100, 146), (126, 132), (126, 162)], (250, 110, 120))
    for x, y in ((82, 140), (82, 154), (118, 140), (118, 154)):
        pygame.draw.circle(lz.s, BLANCO, lz.P(x, y), 2.5 * lz.K)
    lz.elipse(lz.R(93, 139, 14, 14), (220, 80, 96))


def _bufanda(lz):
    pts = _parabola(56, 144, 132, 10, 14)
    lz.trazo(pts, (120, 196, 200), 9)
    pygame.draw.rect(lz.s, BORDE, lz.R(108, 138, 24, 56), border_radius=int(4 * lz.K))
    pygame.draw.rect(lz.s, (120, 196, 200), lz.R(110, 140, 20, 52), border_radius=int(3 * lz.K))
    for y in (150, 166, 182):
        pygame.draw.rect(lz.s, (255, 248, 230), lz.R(110, y, 20, 6))
    for x in range(112, 130, 5):
        _linea(lz, (x, 192), (x, 200), (120, 196, 200), 2)
    for x, y in pts[2:-2:3]:
        pygame.draw.circle(lz.s, (255, 248, 230), lz.P(x, y), 3 * lz.K)


def _perlas(lz):
    _circulos(lz, _parabola(64, 136, 136, 14, 11), 5.5, (255, 252, 244))


def _panuelo(lz):
    lz.poligono([(62, 134), (138, 134), (100, 174)], ROJO)
    for x, y in ((84, 142), (100, 150), (116, 142), (100, 162), (92, 154), (108, 154)):
        pygame.draw.circle(lz.s, BLANCO, lz.P(x, y), 2.5 * lz.K)
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
        pygame.draw.circle(lz.s, BORDE, lz.P(100 + lado * 30, 136), 6 * lz.K)
        pygame.draw.circle(lz.s, ORO, lz.P(100 + lado * 30, 136), 4.5 * lz.K)


def _mochila_frente(lz):
    for x0, x1 in ((72, 78), (128, 122)):
        _linea(lz, (x0, 128), (x1, 178), BORDE, 9)
        _linea(lz, (x0, 128), (x1, 178), (92, 160, 82), 6)


def _mochila(lz):
    lz.elipse(lz.R(136, 112, 64, 80), (122, 196, 106))
    pygame.draw.rect(lz.s, BORDE, lz.R(156, 140, 36, 24), border_radius=int(6 * lz.K))
    pygame.draw.rect(lz.s, (92, 160, 82), lz.R(158, 142, 32, 20), border_radius=int(5 * lz.K))
    pygame.draw.circle(lz.s, ORO, lz.P(174, 152), 3.5 * lz.K)


# ------------------------------------------------------------ cola
def _monio_cola(lz):
    x, y = lz.cola[-4]
    lz.poligono([(x, y), (x - 16, y - 12), (x - 16, y + 12)], (255, 150, 190))
    lz.poligono([(x, y), (x + 16, y - 12), (x + 16, y + 12)], (255, 150, 190))
    lz.elipse(lz.R(x - 6, y - 6, 12, 12), (250, 110, 150))


def _cascabel_cola(lz):
    x, y = lz.cola[-6]
    lz.elipse(lz.R(x - 9, y - 4, 18, 18), ORO)
    pygame.draw.circle(lz.s, (255, 240, 180), lz.P(x - 3, y + 1), 2.5 * lz.K)


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
