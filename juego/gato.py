"""El gato naranja que acompaña: se dibuja con formas (sin imágenes) y reacciona.

Ánimos: normal, feliz, festejo, triste, pensando, sorpresa, dormido."""

import math
import random

import pygame

from . import lienzo as dibujo
from .lienzo import Lienzo
from .ui import BORDE

NARANJA = (247, 152, 60)
NARANJA_OSC = (214, 112, 34)
CREMA = (255, 236, 206)
ROSA = (255, 158, 170)
ROSA_OREJA = (255, 182, 186)
NEGRO = (52, 36, 32)
ROJO_BOCA = (176, 62, 70)
LAGRIMA = (120, 196, 240)

_CACHE = {}
ROPA = ()          # lo que tiene puesto el gato en todo el juego (ids de juego/ropa.py)
OY = 40            # margen de arriba (para sombreros), en unidades de diseño


class _Lienzo:
    """Lo que necesitan las prendas para dibujarse en el espacio de diseño del gato."""


def _rot(p, centro, ang):
    x, y = p[0] - centro[0], p[1] - centro[1]
    c, s = math.cos(ang), math.sin(ang)
    return (centro[0] + x * c - y * s, centro[1] + x * s + y * c)


def _render(tam, animo, ojos_cerrados, cola_paso, mirar, ropa=()):
    """Dibuja el gato en un espacio de diseño de 200×220.
    Con Skia: directo al tamaño final, bordes suaves y sombreado con volumen.
    Sin Skia: a 2x con pygame y después se achica (queda suavizado)."""
    from . import pincel
    from . import ropa as prendas
    fino = pincel.HAY_SKIA
    K = tam * (1 if fino else 2) / 200
    OX = 30  # margen a los costados para que la cola y los brazos no se corten
    W, H = int((200 + 2 * OX) * K), int((222 + OY) * K)
    G = max(2, int(4 * K)) if not fino else max(1.6, 4 * K)  # grosor del contorno
    if fino:
        hoja = pincel.skia.Surface(max(1, W), max(1, H))
        cv = hoja.getCanvas()
        cv.clear(pincel.skia.ColorTRANSPARENT)
        d = pincel.TrazosSkia(cv)
        s = pincel.HojaSkia(cv, W, H)
    else:
        d = pygame.draw
        s = pygame.Surface((W, H), pygame.SRCALPHA)

    def _g(n):
        return n * K if fino else int(n * K)

    def P(x, y):
        return ((x + OX) * K, (y + OY) * K)

    def R(x, y, w, h):
        if fino:
            return pygame.FRect((x + OX) * K, (y + OY) * K, w * K, h * K)
        return pygame.Rect(int((x + OX) * K), int((y + OY) * K), int(w * K), int(h * K))

    def elipse(rect, color, contorno=True):
        if fino:
            r = pincel.skia.Rect.MakeXYWH(rect.x, rect.y, rect.w, rect.h)
            if contorno:
                cv.drawOval(r, d._p(BORDE, 2 * G))
            cv.drawOval(r, pincel.relleno_sombreado(color, rect.x, rect.y, rect.w, rect.h))
            return
        if contorno:
            d.ellipse(s, BORDE, rect.inflate(G * 2, G * 2))
        d.ellipse(s, color, rect)

    def poligono(pts, color, contorno=True):
        pts = [P(*p) for p in pts]
        if fino:
            camino = pincel.skia.Path()
            camino.addPoly([pincel.skia.Point(*p) for p in pts], True)
            if contorno:
                cv.drawPath(camino, d._p(BORDE, 2 * G))
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            cv.drawPath(camino, pincel.relleno_sombreado(color, min(xs), min(ys), max(xs) - min(xs) + 1,
                                                         max(ys) - min(ys) + 1))
            return
        if contorno:
            d.polygon(s, BORDE, pts, G * 2)
        d.polygon(s, color, pts)

    def trazo(pts, color, ancho, contorno=True):
        """Línea gruesa redondeada (para la cola y los brazos)."""
        pts = [P(*p) for p in pts]
        if fino:
            if contorno:
                d.lines(s, BORDE, False, pts, 2 * (ancho * K + G))
            d.lines(s, color, False, pts, 2 * ancho * K)
            return
        if contorno:
            for p in pts:
                d.circle(s, BORDE, p, ancho * K + G)
            d.lines(s, BORDE, False, pts, int(2 * (ancho * K + G)))
        for p in pts:
            d.circle(s, color, p, ancho * K)
        d.lines(s, color, False, pts, int(2 * ancho * K))

    triste = animo == "triste"
    alegre = animo in ("feliz", "festejo")
    brazos = animo == "festejo"
    lz = _Lienzo()
    lz.s, lz.K, lz.G, lz.P, lz.R, lz.elipse, lz.poligono, lz.trazo = s, K, G, P, R, elipse, poligono, trazo
    lz.d = d
    lz.triste = triste
    prendas.dibujar_capa("espalda", ropa, lz)

    # ---- cola (atrás de todo)
    ang = math.sin(cola_paso / 16 * math.tau) * (0.5 if alegre else 0.25)
    pts = []
    for i in range(14):
        t = i / 13
        x = 140 + 40 * t + 18 * math.sin(t * 2.4 + ang * 2) * t
        y = 190 - 95 * t + 10 * math.sin(t * 3)
        pts.append(_rot((x, y), (140, 190), ang * t))
    trazo(pts, NARANJA, 10)
    for p in pts[-4:]:
        d.circle(s, NARANJA_OSC, P(*p), 10 * K)
    lz.cola = pts
    prendas.dibujar_capa("cola", ropa, lz)
    # ---- cuerpo
    elipse(R(46, 118, 108, 94), NARANJA)
    elipse(R(70, 140, 60, 62), CREMA, contorno=False)
    for x0 in (52, 58):
        d.line(s, NARANJA_OSC, P(x0, 150), P(x0 + 10, 154), _g(4))
    for x0 in (148, 142):
        d.line(s, NARANJA_OSC, P(x0, 150), P(x0 - 10, 154), _g(4))
    # patas de atrás
    elipse(R(52, 196, 38, 20), NARANJA)
    elipse(R(110, 196, 38, 20), NARANJA)
    # ---- patas de adelante: van debajo de la ropa (un vestido las tapa y solo asoman los pies)
    if not brazos:
        for x in (84, 116):
            trazo([(x, 162), (x - (1 if x < 100 else -1), 186), (x, 203)], NARANJA, 9)
    prendas.dibujar_capa("cuerpo", ropa, lz)
    # ---- pies (los brazos levantados se dibujan después de la cabeza)
    if not brazos:
        for x in (84, 116):
            elipse(R(x - 15, 197, 30, 15), CREMA)
            for dx in (-5, 5):
                d.line(s, NARANJA_OSC, P(x + dx, 198), P(x + dx, 203), _g(2.5))
    # ---- orejas
    caida = 0.45 if triste else 0.0
    oreja_i = [(38, 66), (50, 6), (90, 40)]
    oreja_d = [(162, 66), (150, 6), (110, 40)]
    oreja_i = [_rot(p, (64, 52), -caida) for p in oreja_i]
    oreja_d = [_rot(p, (136, 52), caida) for p in oreja_d]
    poligono(oreja_i, NARANJA)
    poligono(oreja_d, NARANJA)
    poligono([_rot(p, (64, 52), -caida) for p in [(50, 54), (55, 22), (78, 42)]], ROSA_OREJA, contorno=False)
    poligono([_rot(p, (136, 52), caida) for p in [(150, 54), (145, 22), (122, 42)]], ROSA_OREJA, contorno=False)
    # ---- cabeza
    elipse(R(28, 30, 144, 112), NARANJA)
    elipse(R(66, 92, 68, 44), CREMA, contorno=False)
    for (x1, y1, x2, y2) in [(100, 34, 100, 50), (86, 38, 89, 52), (114, 38, 111, 52)]:
        d.line(s, NARANJA_OSC, P(x1, y1), P(x2, y2), _g(5))
    for (x1, y1, x2, y2) in [(30, 80, 46, 83), (32, 93, 46, 93), (170, 80, 154, 83), (168, 93, 154, 93)]:
        d.line(s, NARANJA_OSC, P(x1, y1), P(x2, y2), _g(4))
    # cachetes
    for cx in (58, 142):
        if fino:
            d.ellipse(s, ROSA + (150,), R(cx - 13, 99, 26, 14))
            continue
        cachete = pygame.Surface((int(26 * K), int(14 * K)), pygame.SRCALPHA)
        d.ellipse(cachete, ROSA + (150,), cachete.get_rect())
        s.blit(cachete, cachete.get_rect(center=P(cx, 106)))
    # ---- ojos
    mx, my = mirar
    for cx in (74, 126):
        if ojos_cerrados or animo == "dormido":
            r = R(cx - 11, 76, 22, 16)
            d.arc(s, NEGRO, r, math.pi * 1.05, math.pi * 1.95, _g(4))
        elif alegre:
            r = R(cx - 11, 74, 22, 20)
            d.arc(s, NEGRO, r, math.pi * 0.1, math.pi * 0.9, _g(5))
        else:
            grande = animo == "sorpresa"
            w, h = (22, 26) if grande else (18, 24)
            d.ellipse(s, NEGRO, R(cx - w / 2 + mx, 72 + my, w, h))
            d.circle(s, (255, 255, 255), P(cx + 3 + mx, 79 + my), 4.5 * K)
            d.circle(s, (255, 255, 255), P(cx - 3 + mx, 89 + my), 2 * K)
    if triste:
        d.line(s, NEGRO, P(62, 70), P(84, 62), _g(4))
        d.line(s, NEGRO, P(138, 70), P(116, 62), _g(4))
        gota = [P(128, 98), P(124, 108), P(128, 112), P(132, 108)]
        d.polygon(s, LAGRIMA, gota)
        d.circle(s, LAGRIMA, P(128, 108), 4 * K)
    # ---- nariz y boca
    poligono([(93, 96), (107, 96), (100, 103)], ROSA, contorno=False)
    if alegre:
        boca = R(89, 103, 22, 18)
        d.ellipse(s, ROJO_BOCA, boca)
        d.rect(s, CREMA, R(88, 100, 24, 8))
        d.ellipse(s, ROSA, R(94, 112, 12, 8))
    elif triste:
        d.arc(s, NEGRO, R(90, 106, 20, 12), 0.2, math.pi - 0.2, _g(3))
    elif animo in ("sorpresa", "pensando"):
        d.ellipse(s, ROJO_BOCA, R(95, 106, 10, 10 if animo == "sorpresa" else 7))
    else:
        d.arc(s, NEGRO, R(88, 98, 13, 12), math.pi * 1.05, math.pi * 1.95, _g(3))
        d.arc(s, NEGRO, R(99, 98, 13, 12), math.pi * 1.05, math.pi * 1.95, _g(3))
    if brazos:
        trazo([(64, 146), (34, 118), (14, 88)], NARANJA, 9)
        trazo([(136, 146), (166, 118), (186, 88)], NARANJA, 9)
        elipse(R(2, 70, 24, 22), CREMA)
        elipse(R(174, 70, 24, 22), CREMA)
    # bigotes
    for (x1, y1, x2, y2) in [(56, 100, 22, 94), (56, 107, 24, 110), (144, 100, 178, 94), (144, 107, 176, 110)]:
        d.line(s, BORDE, P(x1, y1), P(x2, y2), _g(2))
    for capa in ("cuello", "cara", "cabeza", "mano"):
        prendas.dibujar_capa(capa, ropa, lz)
    if fino:
        return pincel.a_pygame(hoja)
    return pygame.transform.smoothscale(s, (int(W / 2), int(H / 2)))


def superficie(tam, animo="normal", ojos_cerrados=False, cola_paso=0, mirar=(0, 0), ropa=None):
    from .lienzo import Lienzo, escala
    ropa = tuple(sorted(ROPA if ropa is None else ropa))
    e = escala()
    clave = (tam, animo, ojos_cerrados, cola_paso % 16, mirar, ropa, e)
    if clave not in _CACHE:
        if len(_CACHE) > 500:
            _CACHE.clear()
        # se dibuja al tamaño real en la pantalla (tam × escala): queda nítido
        _CACHE[clave] = Lienzo.desde(_render(tam * e, animo, ojos_cerrados, cola_paso % 16, mirar, ropa), e)
    return _CACHE[clave]


class Gato:
    def __init__(self, tam=150):
        self.tam = tam
        self.animo = "normal"
        self.animo_base = "normal"
        self.t = 0.0
        self.t_animo = 0.0
        self.dur_animo = 0.0
        self.prox_parpadeo = random.uniform(1.5, 4)
        self.parpadeando = 0.0
        self.salto = 0.0
        self.t_salto = 10.0
        self.sacude = 0.0
        self.ropa = None        # None = lo que tiene puesto (ROPA); si no, una tupla para probar

    def reaccionar(self, animo, dur=1.6, saltar=None):
        self.animo = animo
        self.t_animo = 0.0
        self.dur_animo = dur
        if saltar or (saltar is None and animo in ("feliz", "festejo")):
            self.t_salto = 0.0
        if animo == "triste":
            self.sacude = 0.4

    def actualizar(self, dt):
        self.t += dt
        self.t_animo += dt
        if self.dur_animo and self.t_animo > self.dur_animo and self.animo != self.animo_base:
            self.animo = self.animo_base
        self.prox_parpadeo -= dt
        if self.prox_parpadeo <= 0:
            self.parpadeando = 0.13
            self.prox_parpadeo = random.uniform(2, 5)
        self.parpadeando = max(0.0, self.parpadeando - dt)
        self.t_salto += dt
        dur_salto = 0.45
        if self.t_salto < dur_salto:
            self.salto = math.sin(self.t_salto / dur_salto * math.pi) * self.tam * 0.25
        elif self.animo == "festejo" and self.t_animo < self.dur_animo:
            self.t_salto = 0.0
        else:
            self.salto = 0.0
        self.sacude = max(0.0, self.sacude - dt)

    def dibujar(self, sup, pie, tam=None, angulo=0.0):
        """pie = (x, y) del medio de las patas. angulo: para girar en el aire."""
        tam = tam or self.tam
        cola = int(self.t * (14 if self.animo in ("feliz", "festejo") else 7))
        mirar = (0, 0)
        if self.animo == "pensando":
            mirar = (3, -4)
        elif self.animo == "normal":
            mirar = (int(round(math.sin(self.t * 0.5) * 2)), 0)
        img = superficie(tam, self.animo, self.parpadeando > 0, cola, mirar, self.ropa)
        respira = 1 + 0.018 * math.sin(self.t * 2.4)
        estirar = 1.0
        if 0 < self.t_salto < 0.45:
            estirar = 1.06
        w = int(img.get_width() * (2 - estirar) * (1 if self.animo != "dormido" else 1.02))
        h = int(img.get_height() * respira * estirar)
        if (w, h) != img.get_size():
            img = dibujo.escalar(img, (w, h))
        dx = math.sin(self.t * 40) * 5 * (self.sacude / 0.4) if self.sacude else 0
        r = img.get_rect(midbottom=(pie[0] + dx, pie[1] - self.salto))
        if angulo:
            centro = r.center
            img = dibujo.rotar(img, angulo, 1.0)
            r = img.get_rect(center=centro)
        # sombra en el piso
        sombra = Lienzo(int(tam * 0.8), int(tam * 0.14))
        alfa = int(70 * (1 - min(1, self.salto / (self.tam * 0.3))))
        dibujo.ellipse(sombra, (60, 40, 30, alfa), sombra.get_rect())
        sup.blit(sombra, sombra.get_rect(center=(pie[0], pie[1] - 2)))
        sup.blit(img, r)
        # extras
        from . import ui
        r = pygame.Rect(r.left, r.top + int(OY * tam / 200), r.width, r.height - int(OY * tam / 200))
        if self.animo == "pensando":
            q = ui.texto_borde("?", int(tam * 0.3), (255, 255, 255), BORDE, 3)
            sup.blit(q, q.get_rect(center=(r.right - tam * 0.05, r.top + math.sin(self.t * 4) * 4)))
        elif self.animo == "dormido":
            for k in range(3):
                fase = (self.t * 0.6 + k / 3) % 1
                zz = ui.texto("z", int(tam * (0.12 + 0.08 * fase)), (255, 255, 255), negrita=True)
                zz.set_alpha(int(255 * (1 - fase)))
                sup.blit(zz, (r.right - tam * 0.15 + fase * tam * 0.2, r.top + tam * 0.1 - fase * tam * 0.4))
        elif self.animo == "festejo":
            for k in range(4):
                a = self.t * 3 + k * math.pi / 2
                ui.destello(sup, (r.centerx + math.cos(a) * tam * 0.6, r.centery - tam * 0.2 + math.sin(a) * tam * 0.35),
                            10 + 5 * math.sin(self.t * 8 + k), (255, 230, 120))
        return r
