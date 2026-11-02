"""Lienzo: una superficie que se usa con coordenadas "lógicas" (la pantalla mide siempre
1280×720) pero que por dentro tiene la resolución REAL de tu pantalla.

Así todo el juego sigue pensando en 1280×720, pero se dibuja nítido en una pantalla
Full HD, 2K o 4K (antes se dibujaba chico y después se estiraba: por eso se veía borroso)."""

import math

import pygame

ANCHO, ALTO = 1280, 720
_ESCALA = [1.0]
_DESPLAZAMIENTO = [(0.0, 0.0)]   # bandas negras si la ventana no es 16:9


def poner_desplazamiento(dx, dy):
    _DESPLAZAMIENTO[0] = (dx, dy)


def a_logico(pos):
    dx, dy = _DESPLAZAMIENTO[0]
    e = _ESCALA[0]
    return ((pos[0] - dx) / e, (pos[1] - dy) / e)


def raton():
    return a_logico(pygame.mouse.get_pos())


def escala():
    return _ESCALA[0]


def poner_escala(e):
    _ESCALA[0] = max(0.5, float(e))


def _r(v):
    return int(round(v))


class Lienzo:
    """Imita la parte de pygame.Surface que usa el juego, en coordenadas lógicas."""

    __slots__ = ("sup", "w", "h", "e", "_otras")

    def __init__(self, w, h, alfa=True, sup=None, e=None):
        self.e = e if e is not None else escala()
        self.w, self.h = w, h
        if sup is None:
            # (el -1e-6 evita que un redondeo de la escala agregue un píxel de más)
            tam = (max(1, math.ceil(w * self.e - 1e-6)), max(1, math.ceil(h * self.e - 1e-6)))
            sup = pygame.Surface(tam, pygame.SRCALPHA if alfa else 0)
        self.sup = sup
        self._otras = None

    # ------------------------------------------------ construcción
    @classmethod
    def desde(cls, sup_fisica, e=None):
        """Envuelve una pygame.Surface ya dibujada a resolución real."""
        e = e if e is not None else escala()
        return cls(sup_fisica.get_width() / e, sup_fisica.get_height() / e, sup=sup_fisica, e=e)

    # ------------------------------------------------ medidas (lógicas)
    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    def get_size(self):
        return (self.w, self.h)

    def get_rect(self, **kw):
        r = pygame.Rect(0, 0, _r(self.w), _r(self.h))
        for k, v in kw.items():
            setattr(r, k, v)
        return r

    # ------------------------------------------------ conversión
    def a_fisico(self, x, y):
        return (_r(x * self.e), _r(y * self.e))

    def rect_fisico(self, rect):
        r = pygame.Rect(rect) if not isinstance(rect, pygame.Rect) else rect
        x0, y0 = r.left * self.e, r.top * self.e
        return pygame.Rect(_r(x0), _r(y0), max(1, _r(r.width * self.e)), max(1, _r(r.height * self.e)))

    def _en_escala(self, otra):
        """Si una imagen se hizo con otra escala (por ejemplo, cambiaste el tamaño de la ventana),
        se reescala una vez y se guarda."""
        if abs(otra.e - self.e) < 1e-6:
            return otra.sup
        if otra._otras is None:
            otra._otras = {}
        clave = round(self.e, 4)
        if clave not in otra._otras:
            tam = (max(1, _r(otra.w * self.e)), max(1, _r(otra.h * self.e)))
            otra._otras[clave] = pygame.transform.smoothscale(otra.sup, tam)
        return otra._otras[clave]

    # ------------------------------------------------ dibujar
    def blit(self, fuente, destino, area=None, special_flags=0):
        if isinstance(destino, pygame.Rect):
            x, y = destino.left, destino.top
        else:
            x, y = destino[0], destino[1]
        if isinstance(fuente, Lienzo):
            sup = self._en_escala(fuente)
        else:  # una pygame.Surface "suelta": se la considera hecha a escala 1 y se agranda
            sup = fuente
            if abs(self.e - 1) > 1e-6:
                sup = pygame.transform.smoothscale(fuente, (max(1, _r(fuente.get_width() * self.e)),
                                                            max(1, _r(fuente.get_height() * self.e))))
        if area is not None:
            area = self.rect_fisico(area)
        return self.sup.blit(sup, (_r(x * self.e), _r(y * self.e)), area, special_flags)

    def fill(self, color, rect=None, special_flags=0):
        if rect is not None:
            rect = self.rect_fisico(rect)
        self.sup.fill(color, rect, special_flags)

    def copy(self):
        return Lienzo(self.w, self.h, sup=self.sup.copy(), e=self.e)

    def set_alpha(self, a):
        self.sup.set_alpha(a)

    def get_alpha(self):
        return self.sup.get_alpha()

    def set_clip(self, rect):
        self.sup.set_clip(self.rect_fisico(rect) if rect is not None else None)

    def get_clip(self):
        c = self.sup.get_clip()
        return pygame.Rect(_r(c.left / self.e), _r(c.top / self.e), _r(c.width / self.e), _r(c.height / self.e))

    def convert_alpha(self):
        return self

    def convert(self):
        return self


# ================================================================ dibujo (como pygame.draw, en lógico)

def _color(c):
    return c


def _ancho(sup, w):
    return 0 if not w else max(1, _r(w * sup.e))


def rect(sup, color, rect, width=0, border_radius=0, **kw):
    r = sup.rect_fisico(rect)
    return pygame.draw.rect(sup.sup, color, r, _ancho(sup, width), border_radius=_r(border_radius * sup.e))


def circle(sup, color, center, radius, width=0):
    c = sup.a_fisico(*center)
    rad = max(1, radius * sup.e)
    if width == 0:
        return pygame.draw.aacircle(sup.sup, color, c, rad)
    return pygame.draw.aacircle(sup.sup, color, c, rad, _ancho(sup, width))


def ellipse(sup, color, rect, width=0):
    return pygame.draw.ellipse(sup.sup, color, sup.rect_fisico(rect), _ancho(sup, width))


def polygon(sup, color, points, width=0):
    pts = [(p[0] * sup.e, p[1] * sup.e) for p in points]
    if len(pts) < 3:
        return None
    if width == 0:
        r = pygame.draw.polygon(sup.sup, color, pts)
        pygame.draw.aalines(sup.sup, color, True, pts)   # borde suavizado
        return r
    return pygame.draw.polygon(sup.sup, color, pts, _ancho(sup, width))


def line(sup, color, a, b, width=1):
    a = (a[0] * sup.e, a[1] * sup.e)
    b = (b[0] * sup.e, b[1] * sup.e)
    w = _ancho(sup, width)
    if w <= 1:
        return pygame.draw.aaline(sup.sup, color, a, b)
    r = pygame.draw.line(sup.sup, color, a, b, w)
    # puntas redondeadas: queda mucho más prolijo
    pygame.draw.aacircle(sup.sup, color, (_r(a[0]), _r(a[1])), w / 2 - 0.5)
    pygame.draw.aacircle(sup.sup, color, (_r(b[0]), _r(b[1])), w / 2 - 0.5)
    return r


def lines(sup, color, closed, points, width=1):
    pts = [(p[0] * sup.e, p[1] * sup.e) for p in points]
    if len(pts) < 2:
        return None
    w = _ancho(sup, width)
    if w <= 1:
        return pygame.draw.aalines(sup.sup, color, closed, pts)
    r = pygame.draw.lines(sup.sup, color, closed, pts, w)
    for p in pts:
        pygame.draw.aacircle(sup.sup, color, (_r(p[0]), _r(p[1])), w / 2 - 0.5)
    return r


def arc(sup, color, rect, start, stop, width=1):
    return pygame.draw.arc(sup.sup, color, sup.rect_fisico(rect), start, stop, _ancho(sup, width))


def aaline(sup, color, a, b, width=1):
    return line(sup, color, a, b, width)


def aalines(sup, color, closed, points, width=1):
    return lines(sup, color, closed, points, width)


# ================================================================ transformaciones

def escalar(img, tam):
    """Como pygame.transform.smoothscale, pero tam es lógico."""
    w, h = max(1, tam[0]), max(1, tam[1])
    if isinstance(img, Lienzo):
        fis = (max(1, _r(w * img.e)), max(1, _r(h * img.e)))
        return Lienzo(w, h, sup=pygame.transform.smoothscale(img.sup, fis), e=img.e)
    return pygame.transform.smoothscale(img, (int(w), int(h)))


def rotar(img, angulo, zoom=1.0):
    if isinstance(img, Lienzo):
        s = pygame.transform.rotozoom(img.sup, angulo, zoom)
        return Lienzo.desde(s, img.e)
    return pygame.transform.rotozoom(img, angulo, zoom)
