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

# ------------------------------------------------------------ paleta pastel
FONDO = (250, 246, 240)
FONDO_2 = (243, 237, 229)
TARJETA = (255, 255, 255)
TINTA = (52, 48, 72)
SUAVE = (128, 122, 148)
GRIS = (214, 210, 220)
LAVANDA = (200, 186, 240)
LAVANDA_OSC = (112, 88, 196)
MENTA = (186, 230, 208)
MENTA_OSC = (38, 132, 92)
ROSA = (250, 200, 210)
ROSA_OSC = (196, 62, 98)
DURAZNO = (252, 214, 172)
DURAZNO_OSC = (190, 110, 40)
AMARILLO = (252, 226, 130)
AMARILLO_OSC = (214, 160, 20)
CELESTE = (186, 214, 244)


def oscurecer(c, f=0.8):
    return tuple(max(0, int(v * f)) for v in c[:3])


def aclarar(c, f=0.25):
    return tuple(min(255, int(v + (255 - v) * f)) for v in c[:3])


# ------------------------------------------------------------ fuentes
_DIR_FUENTES = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
_FUENTES = {}


def fuente(tam, negrita=False, mono=False):
    clave = (tam, negrita, mono)
    if clave not in _FUENTES:
        nombre = "DejaVuSansMono" if mono else "DejaVuSans"
        if negrita:
            nombre += "-Bold"
        _FUENTES[clave] = pygame.font.Font(os.path.join(_DIR_FUENTES, nombre + ".ttf"), tam)
    return _FUENTES[clave]


def texto(cadena, tam=22, color=TINTA, negrita=False, mono=False):
    return fuente(tam, negrita, mono).render(cadena, True, color)


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
            fu = fuente(tam, neg)
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
        s = rect.move(0, 4)
        pygame.draw.rect(sup, oscurecer(color, 0.86) if color != TARJETA else (226, 220, 214), s, border_radius=radio)
    pygame.draw.rect(sup, color, rect, border_radius=radio)
    if borde:
        pygame.draw.rect(sup, borde, rect, grosor, border_radius=radio)


def corazon(sup, centro, tam, color):
    cx, cy = centro
    r = tam * 0.28
    pygame.draw.circle(sup, color, (int(cx - r), int(cy - r * 0.3)), int(r + 1))
    pygame.draw.circle(sup, color, (int(cx + r), int(cy - r * 0.3)), int(r + 1))
    pygame.draw.polygon(sup, color, [(cx - 2 * r - 0.5, cy - r * 0.05), (cx + 2 * r + 0.5, cy - r * 0.05),
                                     (cx, cy + tam * 0.5)])


def estrella(sup, centro, radio, color, borde=None):
    cx, cy = centro
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = radio if i % 2 == 0 else radio * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    pygame.draw.polygon(sup, color, pts)
    if borde:
        pygame.draw.polygon(sup, borde, pts, 2)


def candado(sup, centro, tam, color=SUAVE):
    cx, cy = centro
    cuerpo = pygame.Rect(0, 0, tam, int(tam * 0.75))
    cuerpo.center = (cx, cy + tam * 0.18)
    pygame.draw.rect(sup, color, cuerpo, border_radius=4)
    arco = pygame.Rect(0, 0, int(tam * 0.64), int(tam * 0.8))
    arco.center = (cx, cuerpo.top)
    pygame.draw.arc(sup, color, arco, 0, math.pi, max(2, tam // 7))


def tilde(sup, centro, tam, color, grosor=4):
    cx, cy = centro
    pygame.draw.lines(sup, color, False, [(cx - tam * 0.45, cy), (cx - tam * 0.1, cy + tam * 0.35),
                                          (cx + tam * 0.5, cy - tam * 0.35)], grosor)


def cruz(sup, centro, tam, color, grosor=4):
    cx, cy = centro
    d = tam * 0.38
    pygame.draw.line(sup, color, (cx - d, cy - d), (cx + d, cy + d), grosor)
    pygame.draw.line(sup, color, (cx - d, cy + d), (cx + d, cy - d), grosor)


# ------------------------------------------------------------ botón
class Boton:
    def __init__(self, rect, contenido, accion, color=LAVANDA, color_texto=TINTA, tam=22,
                 tecla=None, habilitado=True, negrita=True, radio=16, etiqueta_tecla=None):
        self.rect = pygame.Rect(rect)
        self.accion = accion
        self.color = color
        self.color_texto = color_texto
        self.tecla = tecla
        self.habilitado = habilitado
        self.radio = radio
        self.marcado = None          # None | "bien" | "mal"
        self.etiqueta_tecla = etiqueta_tecla
        if isinstance(contenido, pygame.Surface):
            self.sup = contenido
        else:
            if negrita and "$" not in contenido and "**" not in contenido:
                contenido = f"**{contenido}**"
            self.sup = rico(contenido, tam, color_texto, ancho=self.rect.width - 28)
        self.sup = escalar_a(self.sup, self.rect.width - 24)
        if self.sup.get_height() > self.rect.height - 10:
            k = (self.rect.height - 10) / self.sup.get_height()
            self.sup = pygame.transform.smoothscale(
                self.sup, (max(1, int(self.sup.get_width() * k)), max(1, int(self.sup.get_height() * k))))

    def evento(self, e):
        if not self.habilitado:
            return False
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect.collidepoint(e.pos):
            self.accion()
            return True
        if e.type == pygame.KEYDOWN and self.tecla is not None:
            teclas = self.tecla if isinstance(self.tecla, (list, tuple)) else [self.tecla]
            if e.key in teclas:
                self.accion()
                return True
        return False

    def dibujar(self, sup):
        encima = self.habilitado and self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.color
        if self.marcado == "bien":
            color = MENTA
        elif self.marcado == "mal":
            color = ROSA
        elif not self.habilitado:
            color = (236, 232, 238)
        r = self.rect.move(0, -2) if encima else self.rect
        if encima:
            color = aclarar(color, 0.3)
        sombra = r.move(0, 4 if not encima else 6)
        pygame.draw.rect(sup, oscurecer(self.color if self.habilitado else GRIS, 0.8), sombra, border_radius=self.radio)
        pygame.draw.rect(sup, color, r, border_radius=self.radio)
        if self.marcado == "bien":
            pygame.draw.rect(sup, MENTA_OSC, r, 3, border_radius=self.radio)
        elif self.marcado == "mal":
            pygame.draw.rect(sup, ROSA_OSC, r, 3, border_radius=self.radio)
        contenido = self.sup
        if not self.habilitado and self.marcado is None:
            contenido = contenido.copy()
            contenido.set_alpha(110)
        sup.blit(contenido, contenido.get_rect(center=r.center))
        if self.etiqueta_tecla:
            et = texto(self.etiqueta_tecla, 14, SUAVE, negrita=True)
            sup.blit(et, (r.left + 10, r.top + 6))


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
        caja(sup, self.rect, TARJETA, radio=14, sombra=False,
             borde=LAVANDA_OSC if self.habilitado else GRIS, grosor=3)
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
            pygame.draw.line(sup, LAVANDA_OSC, (cx, self.rect.centery - 15), (cx, self.rect.centery + 15), 2)
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
