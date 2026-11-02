"""Dibujo: colores, fuentes, fórmulas (con matplotlib), texto con fórmulas
adentro, botones y el cuadro donde se tipea."""

import math
import os
import re

import matplotlib
import numpy as np
import pygame

matplotlib.use("Agg")
matplotlib.rcParams["mathtext.fontset"] = "cm"
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.mathtext import MathTextParser  # noqa: E402

ANCHO, ALTO = 1280, 720

# ------------------------------------------------------------ paleta "aventura"
CIELO_ARRIBA = (120, 200, 234)
CIELO_ABAJO = (206, 238, 242)
MAR = (64, 182, 196)
MAR_OSC = (34, 132, 158)
ESPUMA = (228, 250, 246)
ARENA = (246, 226, 182)
ARENA_OSC = (214, 178, 118)
PASTO = (122, 196, 106)
PASTO_OSC = (70, 148, 72)
CORAL = (250, 124, 104)
CORAL_OSC = (206, 78, 64)
SOL = (255, 206, 84)
SOL_OSC = (222, 150, 24)
MADERA = (170, 112, 66)
MADERA_OSC = (110, 68, 38)
NARANJA = (247, 152, 60)
PERGAMINO = (255, 248, 230)
PERGAMINO_2 = (248, 236, 206)
BORDE = (92, 62, 46)            # contorno "ilustrado"

# nombres que usa el resto del juego (significado, no color)
FONDO = (250, 240, 214)
FONDO_2 = (241, 226, 192)
TARJETA = (255, 251, 240)
TINTA = (64, 46, 40)
SUAVE = (140, 112, 92)
GRIS = (206, 196, 180)
LAVANDA = (126, 214, 218)        # acción principal (turquesa)
LAVANDA_OSC = (24, 124, 140)
MENTA = (178, 228, 150)          # bien (verde hoja)
MENTA_OSC = (52, 136, 64)
ROSA = (255, 190, 176)           # mal (coral)
ROSA_OSC = CORAL_OSC
DURAZNO = (253, 214, 160)
DURAZNO_OSC = (200, 118, 40)
AMARILLO = (255, 216, 110)
AMARILLO_OSC = SOL_OSC
CELESTE = (166, 218, 240)


def oscurecer(c, f=0.8):
    return tuple(max(0, int(v * f)) for v in c[:3])


def aclarar(c, f=0.25):
    return tuple(min(255, int(v + (255 - v) * f)) for v in c[:3])


# ------------------------------------------------------------ fuentes
_DIR_FUENTES = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
_FREDOKA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fuentes", "FredokaOne-Regular.ttf")
_FUENTES = {}
_GLIFOS = {}


def fuente(tam, negrita=False, mono=False, dejavu=False):
    """negrita = Fredoka One (títulos, botones, etiquetas); si no, DejaVu Sans (texto largo)."""
    clave = (tam, negrita, mono, dejavu)
    if clave not in _FUENTES:
        if negrita and not mono and not dejavu and os.path.exists(_FREDOKA):
            _FUENTES[clave] = pygame.font.Font(_FREDOKA, int(tam * 1.08))
        else:
            nombre = "DejaVuSansMono" if mono else "DejaVuSans"
            if negrita:
                nombre += "-Bold"
            _FUENTES[clave] = pygame.font.Font(os.path.join(_DIR_FUENTES, nombre + ".ttf"), tam)
    return _FUENTES[clave]


def _fredoka_tiene(cadena):
    """Fredoka One no trae π, √, ∫, flechas, etc.: en ese caso se usa DejaVu."""
    f = fuente(20, True)
    for ch in set(cadena):
        if ch not in _GLIFOS:
            if ch.isspace() or ord(ch) < 0x250:
                _GLIFOS[ch] = True
            else:
                nada = pygame.image.tobytes(f.render("\ue000", True, (0, 0, 0)), "RGBA")
                _GLIFOS[ch] = pygame.image.tobytes(f.render(ch, True, (0, 0, 0)), "RGBA") != nada
        if not _GLIFOS[ch]:
            return False
    return True


def fuente_para(cadena, tam, negrita=False, mono=False):
    if negrita and not mono and not _fredoka_tiene(cadena):
        return fuente(tam, True, dejavu=True)
    return fuente(tam, negrita, mono)


def texto(cadena, tam=22, color=TINTA, negrita=False, mono=False):
    return fuente_para(cadena, tam, negrita, mono).render(cadena, True, color)


_CACHE_BORDE = {}


def texto_borde(cadena, tam, color, color_borde=BORDE, grosor=3, sombra=True):
    """Texto de título con contorno (y sombrita), estilo videojuego."""
    clave = (cadena, tam, color, color_borde, grosor, sombra)
    if clave in _CACHE_BORDE:
        return _CACHE_BORDE[clave]
    f = fuente_para(cadena, tam, True)
    base = f.render(cadena, True, color)
    contorno = f.render(cadena, True, color_borde)
    w, h = base.get_width() + 2 * grosor, base.get_height() + 2 * grosor + (grosor if sombra else 0)
    sup = pygame.Surface((w, h), pygame.SRCALPHA)
    pasos = max(12, grosor * 6)
    if sombra:
        for k in range(pasos):
            a = math.tau * k / pasos
            sup.blit(contorno, (grosor + math.cos(a) * grosor, grosor * 2 + math.sin(a) * grosor))
    for k in range(pasos):
        a = math.tau * k / pasos
        sup.blit(contorno, (grosor + math.cos(a) * grosor, grosor + math.sin(a) * grosor))
    sup.blit(base, (grosor, grosor))
    _CACHE_BORDE[clave] = sup
    return sup


# ------------------------------------------------------------ fórmulas
_PARSER = None
_CACHE_MATE = {}


class Formula:
    """Superficie de una fórmula + cuánto queda debajo de la línea base."""

    def __init__(self, sup, abajo):
        self.sup = sup
        self.abajo = abajo

    @property
    def arriba(self):
        return self.sup.get_height() - self.abajo


_INTEGRAL = re.compile(r"(\\i{1,3}nt(?:_\{(?:[^{}]|\{[^{}]*\})*\}|_[A-Za-z0-9])?"
                       r"(?:\^\{(?:[^{}]|\{[^{}]*\})*\}|\^[A-Za-z0-9])?)\s+(?!\\i{1,3}nt)")


def espaciar_integrales(tex):
    """Un espacito entre el signo integral y lo que se integra."""
    return _INTEGRAL.sub(lambda m: m.group(1) + r"\ ", tex)


def formula(tex, tam=28, color=TINTA):
    """Dibuja LaTeX (sin $). tam ~ altura en píxeles de una letra grande."""
    tex = espaciar_integrales(tex)
    clave = (tex, tam, color)
    if clave in _CACHE_MATE:
        return _CACHE_MATE[clave]
    global _PARSER
    if _PARSER is None:
        _PARSER = MathTextParser("agg")
    try:
        r = _PARSER.parse(f"${tex}$", dpi=72, prop=FontProperties(size=tam))
        alfa = np.asarray(r.image)
        prof = int(round(r.depth))
    except Exception:
        s = texto(tex, int(tam * 0.7), color)
        f = Formula(s, 4)
        _CACHE_MATE[clave] = f
        return f
    h, w = alfa.shape
    sup = pygame.Surface((max(1, w), max(1, h)), pygame.SRCALPHA)
    sup.fill(color + (0,) if len(color) == 3 else color)
    if w and h:
        rgb = pygame.surfarray.pixels3d(sup)
        rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2] = color[0], color[1], color[2]
        del rgb
        a = pygame.surfarray.pixels_alpha(sup)
        a[:, :] = alfa.T
        del a
    f = Formula(sup, prof)
    _CACHE_MATE[clave] = f
    return f


def escalar_a(sup, ancho_max):
    if sup.get_width() <= ancho_max:
        return sup
    k = ancho_max / sup.get_width()
    return pygame.transform.smoothscale(sup, (int(sup.get_width() * k), max(1, int(sup.get_height() * k))))


def fracciones_grandes(tex):
    """\\frac -> \\dfrac: las fracciones chiquitas en una línea de texto no se leen."""
    return re.sub(r"(?<![a-z])\\frac", r"\\dfrac", tex)


# ------------------------------------------------------------ texto con fórmulas
_CACHE_RICO = {}


def _trozos(cadena):
    """Parte 'hola $x^2$ **chau**' en (tipo, contenido, negrita, espacio_antes)."""
    salida = []
    negrita = False
    espacio = False
    for i, parte in enumerate(re.split(r"(\$[^$]+\$)", cadena)):
        if not parte:
            continue
        if parte.startswith("$") and parte.endswith("$") and len(parte) > 1:
            salida.append(("mate", parte[1:-1], negrita, espacio))
            espacio = False
            continue
        for tok in re.split(r"(\s+|\*\*)", parte):
            if tok == "":
                continue
            if tok == "**":
                negrita = not negrita
            elif tok.isspace():
                if "\n" in tok:
                    salida.append(("salto", "", negrita, False))
                    espacio = False
                else:
                    espacio = True
            else:
                salida.append(("texto", tok, negrita, espacio))
                espacio = False
    return salida


def rico(cadena, tam=22, color=TINTA, ancho=900, centrado=False, interlineado=1.25, color_negrita=None):
    """Texto común con fórmulas $...$ y **negritas**, cortado en renglones."""
    clave = (cadena, tam, color, ancho, centrado, interlineado, color_negrita)
    if clave in _CACHE_RICO:
        return _CACHE_RICO[clave]
    f_normal = fuente(tam)
    espacio_px = f_normal.size(" ")[0]
    renglones = [[]]
    x = 0
    for tipo, cont, neg, esp in _trozos(cadena):
        if tipo == "salto":
            renglones.append([])
            x = 0
            continue
        if tipo == "mate":
            fm = formula(fracciones_grandes(cont), int(tam * 1.18), color)
            sup, arriba, abajo = fm.sup, fm.arriba, fm.abajo
        else:
            fu = fuente_para(cont, tam, neg)
            sup = fu.render(cont, True, (color_negrita or color) if neg else color)
            arriba, abajo = fu.get_ascent(), -fu.get_descent()
        sep = espacio_px if (esp and renglones[-1]) else 0
        if renglones[-1] and x + sep + sup.get_width() > ancho:
            renglones.append([])
            x = 0
            sep = 0
        renglones[-1].append((x + sep, sup, arriba, abajo))
        x += sep + sup.get_width()
    # medir
    medidas = []
    for r in renglones:
        arr = max([a for _, _, a, _ in r] + [f_normal.get_ascent()])
        aba = max([b for _, _, _, b in r] + [-f_normal.get_descent()])
        w = (r[-1][0] + r[-1][1].get_width()) if r else 0
        medidas.append((arr, aba, w))
    alto_total = 0
    for (arr, aba, _) in medidas:
        alto_total += max(int((arr + aba) * 1.0), int(tam * interlineado)) + int(tam * (interlineado - 1))
    ancho_total = max([w for _, _, w in medidas] + [1])
    ancho_sup = ancho if centrado else ancho_total
    sup = pygame.Surface((max(1, ancho_sup), max(1, alto_total)), pygame.SRCALPHA)
    y = 0
    for r, (arr, aba, w) in zip(renglones, medidas):
        dx = (ancho_sup - w) // 2 if centrado else 0
        for (px, s, a, _) in r:
            sup.blit(s, (dx + px, y + arr - a))
        y += max(int(arr + aba), int(tam * interlineado)) + int(tam * (interlineado - 1))
    if len(_CACHE_RICO) > 3000:
        _CACHE_RICO.clear()
    _CACHE_RICO[clave] = sup
    return sup


# ------------------------------------------------------------ formas
def caja(sup, rect, color, radio=16, sombra=True, borde=None, grosor=2):
    rect = pygame.Rect(rect)
    if sombra:
        s = rect.move(0, 5)
        pygame.draw.rect(sup, oscurecer(color, 0.78), s, border_radius=radio)
    pygame.draw.rect(sup, color, rect, border_radius=radio)
    if borde:
        pygame.draw.rect(sup, borde, rect, grosor, border_radius=radio)


def tarjeta(sup, rect, color=TARJETA, radio=18, borde=ARENA_OSC, alto_base=6):
    """Tarjeta 'de juego': cara clara, base más oscura abajo y contorno."""
    rect = pygame.Rect(rect)
    base = rect.move(0, alto_base)
    pygame.draw.rect(sup, oscurecer(borde, 0.9), base, border_radius=radio)
    pygame.draw.rect(sup, color, rect, border_radius=radio)
    pygame.draw.rect(sup, borde, rect, 3, border_radius=radio)


def destello(sup, centro, tam, color=(255, 240, 160)):
    """Estrellita de 4 puntas (brillo)."""
    cx, cy = centro
    t = tam / 2
    a = tam / 7
    pygame.draw.polygon(sup, color, [(cx, cy - t), (cx + a, cy - a), (cx + t, cy), (cx + a, cy + a),
                                     (cx, cy + t), (cx - a, cy + a), (cx - t, cy), (cx - a, cy - a)])


def corazon(sup, centro, tam, color, borde=BORDE, brillo=True):
    cx, cy = centro
    r = tam * 0.27

    def forma(c, d=0):
        pygame.draw.circle(sup, c, (int(cx - r), int(cy - r * 0.35)), int(r + 1 + d))
        pygame.draw.circle(sup, c, (int(cx + r), int(cy - r * 0.35)), int(r + 1 + d))
        pygame.draw.polygon(sup, c, [(cx - 2 * r - 0.6 - d, cy - r * 0.15), (cx + 2 * r + 0.6 + d, cy - r * 0.15),
                                     (cx, cy + tam * 0.52 + d * 1.4)])
    if borde:
        forma(borde, 2)
    forma(color)
    if brillo and color != GRIS:
        pygame.draw.circle(sup, aclarar(color, 0.65), (int(cx - r * 1.1), int(cy - r * 0.7)), max(2, int(r * 0.35)))


def estrella(sup, centro, radio, color, borde=None, brillo=True):
    cx, cy = centro
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = radio if i % 2 == 0 else radio * 0.5
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    if borde:
        pygame.draw.polygon(sup, borde, pts, max(2, int(radio / 6)))
    pygame.draw.polygon(sup, color, pts)
    if borde:
        pygame.draw.polygon(sup, borde, pts, max(2, int(radio / 8)))
    if brillo and radio > 8 and color not in (GRIS,):
        pygame.draw.circle(sup, aclarar(color, 0.7), (int(cx - radio * 0.18), int(cy - radio * 0.25)), max(2, int(radio * 0.16)))


def moneda(sup, centro, radio, giro=0.0):
    """Moneda dorada (con giro, para cuando vuela)."""
    cx, cy = centro
    ancho = max(3, int(abs(math.cos(giro)) * radio * 2))
    r = pygame.Rect(0, 0, ancho, int(radio * 2))
    r.center = (int(cx), int(cy))
    pygame.draw.ellipse(sup, SOL_OSC, r.inflate(4, 4))
    pygame.draw.ellipse(sup, SOL, r)
    if ancho > radio:
        pygame.draw.ellipse(sup, aclarar(SOL, 0.4), r.inflate(-radio * 0.7, -radio * 0.7), 2)
        pygame.draw.circle(sup, (255, 250, 220), (int(cx - radio * 0.35), int(cy - radio * 0.4)), max(1, int(radio * 0.2)))


def candado(sup, centro, tam, color=SUAVE):
    cx, cy = centro
    cuerpo = pygame.Rect(0, 0, tam, int(tam * 0.75))
    cuerpo.center = (cx, cy + tam * 0.18)
    arco = pygame.Rect(0, 0, int(tam * 0.64), int(tam * 0.8))
    arco.center = (cx, cuerpo.top)
    pygame.draw.arc(sup, oscurecer(color, 0.8), arco, 0, math.pi, max(3, tam // 6))
    pygame.draw.rect(sup, color, cuerpo, border_radius=5)
    pygame.draw.rect(sup, oscurecer(color, 0.75), cuerpo, 2, border_radius=5)
    pygame.draw.circle(sup, oscurecer(color, 0.6), (int(cx), int(cuerpo.centery - 1)), max(2, tam // 9))


def tilde(sup, centro, tam, color, grosor=4):
    cx, cy = centro
    pygame.draw.lines(sup, color, False, [(cx - tam * 0.45, cy), (cx - tam * 0.1, cy + tam * 0.35),
                                          (cx + tam * 0.5, cy - tam * 0.35)], grosor)


def cruz(sup, centro, tam, color, grosor=4):
    cx, cy = centro
    d = tam * 0.38
    pygame.draw.line(sup, color, (cx - d, cy - d), (cx + d, cy + d), grosor)
    pygame.draw.line(sup, color, (cx - d, cy + d), (cx + d, cy - d), grosor)


def triangulo(sup, centro, tam, color, direccion=1):
    """Flechita hacia la derecha (1) o la izquierda (-1)."""
    cx, cy = centro
    pygame.draw.polygon(sup, color, [(cx - tam * 0.4 * direccion, cy - tam * 0.5),
                                     (cx + tam * 0.5 * direccion, cy), (cx - tam * 0.4 * direccion, cy + tam * 0.5)])


def parlante(sup, centro, tam, color, activo=True):
    cx, cy = centro
    pygame.draw.rect(sup, color, (cx - tam * 0.5, cy - tam * 0.18, tam * 0.3, tam * 0.36), border_radius=2)
    pygame.draw.polygon(sup, color, [(cx - tam * 0.3, cy - tam * 0.18), (cx, cy - tam * 0.45),
                                     (cx, cy + tam * 0.45), (cx - tam * 0.3, cy + tam * 0.18)])
    if activo:
        for k, rr in enumerate((0.25, 0.42)):
            r = pygame.Rect(0, 0, tam * rr * 2, tam * rr * 2)
            r.center = (cx + tam * 0.02, cy)
            pygame.draw.arc(sup, color, r, -0.9, 0.9, 3)
    else:
        cruz(sup, (cx + tam * 0.3, cy), tam * 0.45, color, 3)


def globo(sup, rect, punta, color=TARJETA, borde=BORDE, grosor=3, radio=20):
    """Globito de diálogo con la colita apuntando a 'punta' (la boca del gato)."""
    rect = pygame.Rect(rect)
    px, py = punta
    bx = max(rect.left + radio + 10, min(rect.right - radio - 40, px + 30))
    base_y = rect.bottom - 2 if py > rect.bottom else rect.top + 2
    if px < rect.left:
        # la colita sale por la izquierda
        cy = max(rect.top + radio + 10, min(rect.bottom - radio - 10, py))
        tri = [(rect.left + 2, cy - 14), (rect.left + 2, cy + 14), (px, py)]
    else:
        tri = [(bx - 16, base_y), (bx + 16, base_y), (px, py)]
    pygame.draw.rect(sup, oscurecer(color, 0.85), rect.move(0, 5), border_radius=radio)
    pygame.draw.polygon(sup, borde, tri, grosor * 2)
    pygame.draw.rect(sup, color, rect, border_radius=radio)
    pygame.draw.polygon(sup, color, tri)
    pygame.draw.rect(sup, borde, rect, grosor, border_radius=radio)
    # tapar el borde donde se une la colita
    if px < rect.left:
        pygame.draw.line(sup, color, (rect.left + 1, tri[0][1] + 3), (rect.left + 1, tri[1][1] - 3), grosor + 2)
    else:
        pygame.draw.line(sup, color, (tri[0][0] + 3, base_y - 1), (tri[1][0] - 3, base_y - 1), grosor + 2)


def tabla_madera(sup, rect, radio=10, color=MADERA):
    """Cartel de madera con vetas."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(sup, MADERA_OSC, rect.move(0, 5), border_radius=radio)
    pygame.draw.rect(sup, color, rect, border_radius=radio)
    vetas = oscurecer(color, 0.88)
    n = max(1, rect.height // 18)
    for k in range(1, n + 1):
        y = rect.top + k * rect.height / (n + 1)
        pygame.draw.line(sup, vetas, (rect.left + 14, y), (rect.right - 14, y), 2)
    for x in (rect.left + 12, rect.right - 12):
        pygame.draw.circle(sup, MADERA_OSC, (x, rect.top + 12), 3)
    pygame.draw.rect(sup, MADERA_OSC, rect, 3, border_radius=radio)


# ------------------------------------------------------------ botón
def _ahora():
    return pygame.time.get_ticks() / 1000


class Boton:
    """Botón 'de videojuego': tiene relieve, se levanta con el mouse y se hunde al apretarlo."""

    def __init__(self, rect, contenido, accion, color=LAVANDA, color_texto=TINTA, tam=22,
                 tecla=None, habilitado=True, negrita=True, radio=16, etiqueta_tecla=None,
                 sonido="click", relieve=6):
        self.rect = pygame.Rect(rect)
        self.accion = accion
        self.color = color
        self.color_texto = color_texto
        self.tecla = tecla
        self.habilitado = habilitado
        self.radio = radio
        self.marcado = None          # None | "bien" | "mal"
        self.t_marcado = 0.0
        self.etiqueta_tecla = etiqueta_tecla
        self.sonido = sonido
        self.relieve = relieve
        self.t_apretado = -10.0
        self.encima_antes = False
        if isinstance(contenido, pygame.Surface):
            self.sup = contenido
        else:
            if negrita and "$" not in contenido and "**" not in contenido:
                contenido = f"**{contenido}**"
            self.sup = rico(contenido, tam, color_texto, ancho=self.rect.width - 28, color_negrita=color_texto)
        self.sup = escalar_a(self.sup, self.rect.width - 24)
        if self.sup.get_height() > self.rect.height - 10:
            k = (self.rect.height - 10) / self.sup.get_height()
            self.sup = pygame.transform.smoothscale(
                self.sup, (max(1, int(self.sup.get_width() * k)), max(1, int(self.sup.get_height() * k))))

    def marcar(self, estado):
        self.marcado = estado
        self.t_marcado = _ahora()

    def _activar(self):
        self.t_apretado = _ahora()
        if self.sonido:
            from .sonido import sonidos
            sonidos.tocar(self.sonido)
        self.accion()

    def evento(self, e):
        if not self.habilitado:
            return False
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            self._activar()
            return True
        if e.type == pygame.KEYDOWN and self.tecla is not None:
            teclas = self.tecla if isinstance(self.tecla, (list, tuple)) else [self.tecla]
            if e.key in teclas:
                self._activar()
                return True
        return False

    def dibujar(self, sup, dx=0, dy=0):
        ahora = _ahora()
        rect = self.rect.move(dx, dy)
        encima = self.habilitado and rect.collidepoint(pygame.mouse.get_pos())
        apretado = ahora - self.t_apretado < 0.12
        color = self.color
        borde = oscurecer(self.color, 0.62)
        if self.marcado == "bien":
            color, borde = MENTA, MENTA_OSC
        elif self.marcado == "mal":
            color, borde = ROSA, ROSA_OSC
        elif not self.habilitado:
            color, borde = (232, 224, 210), (200, 188, 170)
        if encima and not apretado:
            color = aclarar(color, 0.25)
        sacudir = 0
        if self.marcado == "mal" and ahora - self.t_marcado < 0.4:
            k = 1 - (ahora - self.t_marcado) / 0.4
            sacudir = int(math.sin((ahora - self.t_marcado) * 60) * 8 * k)
        salto = 0
        if self.marcado == "bien" and ahora - self.t_marcado < 0.35:
            salto = -int(math.sin((ahora - self.t_marcado) / 0.35 * math.pi) * 8)
        relieve = self.relieve
        hundir = relieve - 1 if apretado else (-2 if encima else 0)
        cara = rect.move(sacudir, hundir + salto)
        base = rect.move(sacudir, relieve + salto)
        pygame.draw.rect(sup, borde, base.inflate(4, 4), border_radius=self.radio + 2)
        pygame.draw.rect(sup, oscurecer(color, 0.8), base, border_radius=self.radio)
        pygame.draw.rect(sup, borde, cara.inflate(4, 4), border_radius=self.radio + 2)
        pygame.draw.rect(sup, color, cara, border_radius=self.radio)
        # brillo de arriba
        brillo = pygame.Rect(cara.left + 8, cara.top + 4, cara.width - 16, max(4, cara.height // 5))
        pygame.draw.rect(sup, aclarar(color, 0.45), brillo, border_radius=self.radio // 2 + 2)
        contenido = self.sup
        if not self.habilitado and self.marcado is None:
            contenido = contenido.copy()
            contenido.set_alpha(110)
        sup.blit(contenido, contenido.get_rect(center=(cara.centerx, cara.centery + 1)))
        if self.marcado == "bien":
            pygame.draw.circle(sup, MENTA_OSC, (cara.right - 20, cara.top + 18), 12)
            tilde(sup, (cara.right - 20, cara.top + 18), 13, TARJETA, 3)
        elif self.marcado == "mal":
            pygame.draw.circle(sup, ROSA_OSC, (cara.right - 20, cara.top + 18), 12)
            cruz(sup, (cara.right - 20, cara.top + 18), 15, TARJETA, 3)
        if self.etiqueta_tecla:
            et = texto(self.etiqueta_tecla, 14, oscurecer(color, 0.5), negrita=True)
            sup.blit(et, (cara.left + 12, cara.top + 7))


# ------------------------------------------------------------ cuadro de texto
class CampoTexto:
    def __init__(self, rect, al_enter=None, al_cambiar=None):
        self.rect = pygame.Rect(rect)
        self.texto = ""
        self.cursor = 0
        self.al_enter = al_enter
        self.al_cambiar = al_cambiar
        self.t = 0
        self.desplazamiento = 0
        self.habilitado = True

    def _cambio(self):
        self.t = 0
        if self.al_cambiar:
            self.al_cambiar(self.texto)

    def poner(self, nuevo):
        self.texto = nuevo
        self.cursor = len(nuevo)
        self._cambio()

    def insertar(self, s, retroceso=0):
        self.texto = self.texto[:self.cursor] + s + self.texto[self.cursor:]
        self.cursor += len(s) - retroceso
        self._cambio()

    def evento(self, e):
        if not self.habilitado:
            return False
        if e.type == pygame.TEXTINPUT:
            if len(self.texto) < 120:
                self.insertar(e.text)
                from .sonido import sonidos
                sonidos.tocar("tecla", variar=True)
            return True
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.al_enter:
                    self.al_enter()
                return True
            if e.key == pygame.K_BACKSPACE:
                if self.cursor > 0:
                    self.texto = self.texto[:self.cursor - 1] + self.texto[self.cursor:]
                    self.cursor -= 1
                    self._cambio()
                return True
            if e.key == pygame.K_DELETE:
                self.texto = self.texto[:self.cursor] + self.texto[self.cursor + 1:]
                self._cambio()
                return True
            if e.key == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
                self.t = 0
                return True
            if e.key == pygame.K_RIGHT:
                self.cursor = min(len(self.texto), self.cursor + 1)
                self.t = 0
                return True
            if e.key == pygame.K_HOME:
                self.cursor = 0
                return True
            if e.key == pygame.K_END:
                self.cursor = len(self.texto)
                return True
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            # ubicar el cursor donde hizo clic
            f = fuente(26, mono=True)
            rel = e.pos[0] - self.rect.left - 16 + self.desplazamiento
            mejor = 0
            for i in range(len(self.texto) + 1):
                if f.size(self.texto[:i])[0] <= rel:
                    mejor = i
            self.cursor = mejor
            self.t = 0
            return True
        return False

    def actualizar(self, dt):
        self.t += dt

    def dibujar(self, sup):
        r = self.rect
        pygame.draw.rect(sup, (255, 255, 255), r, border_radius=14)
        pygame.draw.rect(sup, (236, 230, 218), (r.left + 4, r.top + 3, r.width - 8, 6), border_radius=3)
        borde = LAVANDA_OSC if self.habilitado else GRIS
        if self.habilitado:
            brillo = 0.5 + 0.5 * math.sin(self.t * 3)
            pygame.draw.rect(sup, aclarar(LAVANDA, 0.3 + 0.3 * brillo), r.inflate(10, 10), 4, border_radius=18)
        pygame.draw.rect(sup, borde, r, 3, border_radius=14)
        f = fuente(26, mono=True)
        interior = self.rect.inflate(-32, 0)
        ancho_cursor = f.size(self.texto[:self.cursor])[0]
        if ancho_cursor - self.desplazamiento > interior.width - 4:
            self.desplazamiento = ancho_cursor - interior.width + 4
        if ancho_cursor - self.desplazamiento < 0:
            self.desplazamiento = ancho_cursor
        clip = sup.get_clip()
        sup.set_clip(interior)
        if self.texto:
            s = f.render(self.texto, True, TINTA)
            sup.blit(s, (interior.left - self.desplazamiento, self.rect.centery - s.get_height() // 2))
        else:
            s = f.render("escribí acá…", True, GRIS)
            sup.blit(s, (interior.left, self.rect.centery - s.get_height() // 2))
        if self.habilitado and (self.t % 1.0) < 0.6:
            cx = interior.left + ancho_cursor - self.desplazamiento
            pygame.draw.line(sup, LAVANDA_OSC, (cx, self.rect.centery - 15), (cx, self.rect.centery + 15), 3)
        sup.set_clip(clip)


# ------------------------------------------------------------ dibujo de regiones (integrales dobles)
_CACHE_GRAF = {}


def grafico(spec, tam=300):
    """Dibuja la región de integración con matplotlib y la devuelve como superficie."""
    clave = (tuple(sorted((k, str(v)) for k, v in spec.items())), tam)
    if clave in _CACHE_GRAF:
        return _CACHE_GRAF[clave]
    import matplotlib.patches  # noqa: F401
    import sympy as sp
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    from .mate import tex, x

    relleno, borde, tinta = "#d9cdf7", "#7058c4", "#343048"
    fig = Figure(figsize=(tam / 100, tam / 100), dpi=100)
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0.15, 0.15, 0.79, 0.80])
    tipo = spec["tipo"]
    if tipo == "rect":
        a, b, c, d = (float(spec[k]) for k in "abcd")
        ax.add_patch(matplotlib.patches.Rectangle((a, c), b - a, d - c, facecolor=relleno, edgecolor=borde, lw=2))
        m = 0.15 * max(b - a, d - c)
        ax.set_xlim(min(0, a) - m, b + m)
        ax.set_ylim(min(0, c) - m, d + m)
    elif tipo == "I":
        a, b = float(spec["a"]), float(spec["b"])
        xs = np.linspace(a, b, 240)

        def evaluar(g):
            f = sp.lambdify(x, sp.sympify(g), "numpy")
            return np.broadcast_to(np.asarray(f(xs), dtype=float), xs.shape)
        y1, y2 = evaluar(spec["g1"]), evaluar(spec["g2"])
        ax.fill_between(xs, y1, y2, color=relleno, zorder=1)
        ax.plot(xs, y1, color="#26845c", lw=2.2, label=f"$y = {tex(spec['g1'])}$", zorder=2)
        ax.plot(xs, y2, color="#c43e62", lw=2.2, label=f"$y = {tex(spec['g2'])}$", zorder=2)
        for xv in (a, b):
            ax.axvline(xv, color=borde, lw=1, ls="--", zorder=0)
        lo, hi = min(y1.min(), y2.min(), 0), max(y1.max(), y2.max())
        m = 0.15 * max(b - a, hi - lo, 1)
        ax.set_xlim(min(a, 0) - m, b + m)
        ax.set_ylim(lo - m, hi + m * 2.2)
        ax.legend(loc="upper left", fontsize=10, frameon=False)
    elif tipo == "polar":
        r1, r2 = float(spec["r1"]), float(spec["r2"])
        t1, t2 = float(spec["t1"]), float(spec["t2"])
        ts = np.linspace(t1, t2, 240)
        afuera = np.c_[r2 * np.cos(ts), r2 * np.sin(ts)]
        adentro = np.c_[r1 * np.cos(ts[::-1]), r1 * np.sin(ts[::-1])] if r1 > 0 else np.array([[0.0, 0.0]])
        ax.add_patch(matplotlib.patches.Polygon(np.r_[afuera, adentro], closed=True, facecolor=relleno,
                                                edgecolor=borde, lw=2))
        m = r2 * 1.25
        ax.set_xlim(-m, m)
        ax.set_ylim(-m, m)
        ax.set_aspect("equal")
    ax.axhline(0, color=tinta, lw=0.8, zorder=0)
    ax.axvline(0, color=tinta, lw=0.8, zorder=0)
    ax.grid(True, color="#ece6dc", lw=0.8, zorder=0)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(labelsize=9, colors=tinta)
    ax.set_xlabel("x", color=tinta, fontsize=11, labelpad=1)
    ax.set_ylabel("y", color=tinta, fontsize=11, rotation=0, labelpad=8)
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    w, h = canvas.get_width_height()
    img = pygame.image.frombuffer(bytes(canvas.buffer_rgba()), (w, h), "RGBA").copy()
    tarjeta = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
    pygame.draw.rect(tarjeta, (226, 220, 214), tarjeta.get_rect().move(0, 3), border_radius=16)
    pygame.draw.rect(tarjeta, TARJETA, tarjeta.get_rect().inflate(0, -3).move(0, -1), border_radius=16)
    tarjeta.blit(img, (8, 6))
    _CACHE_GRAF[clave] = tarjeta
    return tarjeta
