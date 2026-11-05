"""Pincel: piezas del juego dibujadas con Skia (el motor de gráficos de Chrome y Android).

Skia dibuja con bordes perfectamente suaves, degradés, brillos y sombras difusas. Como en
la computadora es lento para redibujar toda la pantalla 60 veces por segundo, acá cada
pieza se pinta UNA vez (al tamaño real de la pantalla), se guarda, y después pygame solo
la pega, que es rapidísimo.

Si Skia no está instalado, el juego sigue andando con los dibujos simples de antes
(cada función devuelve None y quien la llama usa su versión vieja)."""

import math
import time

import pygame

from .cache import CacheDibujos
from .lienzo import Lienzo, escala

try:
    import skia
    HAY_SKIA = True
except Exception:  # sin Skia: el juego anda igual, con dibujos más simples
    skia = None
    HAY_SKIA = False

_CACHE = CacheDibujos(limite=1500)
_GASTO = [0.0]          # segundos usados este cuadro creando piezas nuevas
_PRESUPUESTO = 0.12     # red de seguridad: si en un cuadro se pasa de esto, se dibuja la versión simple


def nuevo_cuadro():
    _GASTO[0] = 0.0


class siempre:
    """Para dibujos que se guardan (islas, el mapa): ahí sí se usa Skia aunque tarde un poco más."""
    _activo = [0]

    def __enter__(self):
        self._activo[0] += 1

    def __exit__(self, *a):
        self._activo[0] -= 1


# ---------------------------------------------------------------- utilidades
def _c(color, a=255):
    if len(color) == 4:
        a = color[3]
    return skia.Color(int(color[0]), int(color[1]), int(color[2]), int(a))


def _mezcla(c1, c2, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(c1[:3], c2[:3]))


def aclarar(c, f):
    return _mezcla(c, (255, 255, 255), f)


def oscurecer(c, f):
    return tuple(int(v * f) for v in c[:3])


def _pieza(clave, w, h, pintar, margen=0, forzar=False):
    """Crea (o trae de la caché) una pieza de w×h lógicos (+ margen para sombras).
    forzar: se crea aunque este cuadro ya haya gastado su presupuesto (para cosas que se guardan)."""
    if not HAY_SKIA:
        return None
    e = escala()
    clave = clave + (round(e, 4),)
    if clave in _CACHE:
        return _CACHE[clave]
    if _GASTO[0] > _PRESUPUESTO and not forzar and not siempre._activo[0]:
        return None
    t0 = time.perf_counter()
    W, H = max(1, math.ceil((w + 2 * margen) * e)), max(1, math.ceil((h + 2 * margen) * e))
    sup = skia.Surface(W, H)
    cv = sup.getCanvas()
    cv.clear(skia.ColorTRANSPARENT)
    cv.scale(e, e)
    cv.translate(margen, margen)
    pintar(cv)
    arr = sup.makeImageSnapshot().toarray(colorType=skia.kBGRA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    fis = pygame.image.frombuffer(arr.tobytes(), (W, H), "BGRA").copy()
    pieza = Lienzo.desde(fis, e)
    _CACHE[clave] = pieza
    _GASTO[0] += time.perf_counter() - t0
    return pieza


def _paint(color=None, a=255, **kw):
    p = skia.Paint(AntiAlias=True, **kw)
    if color is not None:
        p.setColor(_c(color, a))
    return p


def _lineal(x0, y0, x1, y1, colores, posiciones=None):
    return skia.GradientShader.MakeLinear([(x0, y0), (x1, y1)], [_c(c) for c in colores], posiciones)


def _radial(cx, cy, r, colores, posiciones=None):
    return skia.GradientShader.MakeRadial((cx, cy), r, [_c(c) for c in colores], posiciones)


def _sombra(sigma, a=70):
    return _paint((40, 24, 16), a, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma))


def _rrect(x, y, w, h, r):
    return skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)


# ---------------------------------------------------------------- botones
def boton(w, h, color, radio=16, relieve=6, estado="normal"):
    """estado: normal | encima | apretado | apagado | bien | mal.
    Devuelve la pieza y cuánto margen tiene alrededor (para pegarla en x - margen, y - margen)."""
    m = 12

    def pintar(cv):
        base_c = oscurecer(color, 0.72)
        borde = oscurecer(color, 0.52)
        cara_c = color
        hundido = 0
        if estado == "encima":
            cara_c = aclarar(color, 0.18)
            hundido = -2
        elif estado == "apretado":
            hundido = relieve - 1
        # sombra difusa en el piso
        cv.drawRRect(_rrect(2, relieve + 4, w - 4, h, radio), _sombra(5 if estado != "apretado" else 3, 70))
        # base (el "costado" del botón)
        cv.drawRRect(_rrect(0, relieve, w, h, radio), _paint(borde))
        cv.drawRRect(_rrect(1.5, relieve + 1, w - 3, h - 2.5, radio - 1.5), _paint(base_c))
        # cara con degradé
        y = hundido
        cv.drawRRect(_rrect(0, y, w, h, radio), _paint(borde))
        cara = _paint(Shader=_lineal(0, y, 0, y + h, [aclarar(cara_c, 0.22), cara_c, oscurecer(cara_c, 0.93)],
                                     [0, 0.55, 1]))
        cv.drawRRect(_rrect(2, y + 2, w - 4, h - 4, radio - 2), cara)
        # brillo de arriba (vidrio)
        brillo = _paint(Shader=_lineal(0, y + 4, 0, y + h * 0.5, [(255, 255, 255, 150), (255, 255, 255, 0)]))
        cv.drawRRect(_rrect(7, y + 4, w - 14, h * 0.42, max(2, radio - 6)), brillo)
        # filo de luz
        filo = _paint((255, 255, 255), 90, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5)
        cv.drawRRect(_rrect(3, y + 3, w - 6, h - 6, radio - 3), filo)

    return _pieza(("boton", w, h, tuple(color), radio, relieve, estado), w, h + relieve, pintar, m), m


# ---------------------------------------------------------------- paneles
def panel(w, h, color, borde, radio=18, sombra=True, grosor=3, alto_base=6, brillo=0.5):
    """Tarjeta / pergamino con sombra suave, base y degradé muy sutil."""
    m = 16

    def pintar(cv):
        if sombra:
            cv.drawRRect(_rrect(3, alto_base + 6, w - 6, h, radio), _sombra(9, 60))
        if alto_base:
            cv.drawRRect(_rrect(0, alto_base, w, h, radio), _paint(oscurecer(borde, 0.88)))
        cv.drawRRect(_rrect(0, 0, w, h, radio), _paint(borde))
        cara = _paint(Shader=_lineal(0, 0, 0, h, [aclarar(color, brillo), color, _mezcla(color, borde, 0.06)],
                                     [0, 0.3, 1]))
        cv.drawRRect(_rrect(grosor, grosor, w - 2 * grosor, h - 2 * grosor, max(1, radio - grosor)), cara)
        cv.drawRRect(_rrect(grosor + 2, grosor + 2, w - 2 * grosor - 4, h - 2 * grosor - 4, max(1, radio - grosor - 2)),
                     _paint((255, 255, 255), 70, Style=skia.Paint.kStroke_Style, StrokeWidth=1.5))

    return _pieza(("panel", w, h, tuple(color), tuple(borde), radio, sombra, grosor, alto_base, brillo), w, h + alto_base,
                  pintar, m), m


def globo(w, h, punta, color, borde, grosor=3, radio=20):
    """Globito de diálogo con colita hacia 'punta' (coordenadas relativas al globito)."""
    px, py = punta
    # la colita no se estira de más: como mucho 46 px afuera del globito
    fx = min(max(px, -46), w + 46)
    fy = min(max(py, -46), h + 46)
    px, py = fx, fy
    m = int(max(24, -px, px - w, -py, py - h)) + 20

    def camino():
        p = skia.Path()
        p.addRRect(_rrect(0, 0, w, h, radio))
        cola = skia.Path()
        if px < 0:
            cy = max(radio + 10, min(h - radio - 10, py))
            cola.moveTo(6, cy - 20)
            cola.quadTo(px * 0.4, cy - 6, px, py)
            cola.quadTo(px * 0.2, cy + 14, 6, cy + 20)
        else:
            bx = max(radio + 10, min(w - radio - 40, px + 30))
            base_y = h - 2 if py > h else 2
            cola.moveTo(bx - 20, base_y)
            cola.quadTo(bx - 6, (base_y + py) / 2, px, py)
            cola.quadTo(bx + 6, (base_y + py) / 2, bx + 20, base_y)
        cola.close()
        return skia.Op(p, cola, skia.PathOp.kUnion_PathOp)

    def pintar(cv):
        forma = camino()
        cv.save()
        cv.translate(0, 6)
        cv.drawPath(forma, _sombra(8, 55))
        cv.restore()
        cv.drawPath(forma, _paint(Shader=_lineal(0, 0, 0, h, [aclarar(color, 0.6), color])))
        cv.drawPath(forma, _paint(borde, Style=skia.Paint.kStroke_Style, StrokeWidth=grosor,
                                  StrokeJoin=skia.Paint.kRound_Join))

    return _pieza(("globo", w, h, round(px), round(py), tuple(color), tuple(borde), grosor, radio), w, h,
                  pintar, m), m


def madera(w, h, radio=10, color=(170, 112, 66)):
    """Cartel de madera con vetas curvas, clavitos y sombra."""
    m = 14

    def pintar(cv):
        osc = oscurecer(color, 0.62)
        cv.drawRRect(_rrect(2, 7, w - 4, h, radio), _sombra(6, 70))
        cv.drawRRect(_rrect(0, 5, w, h, radio), _paint(oscurecer(color, 0.55)))
        cv.drawRRect(_rrect(0, 0, w, h, radio), _paint(osc))
        cv.drawRRect(_rrect(2.5, 2.5, w - 5, h - 5, max(1, radio - 2)),
                     _paint(Shader=_lineal(0, 0, 0, h, [aclarar(color, 0.12), color, oscurecer(color, 0.9)])))
        cv.save()
        cv.clipRRect(_rrect(2.5, 2.5, w - 5, h - 5, max(1, radio - 2)), doAntiAlias=True)
        vetas = _paint(oscurecer(color, 0.84), Style=skia.Paint.kStroke_Style, StrokeWidth=1.6)
        n = max(2, int(h // 14))
        for k in range(1, n + 1):
            y = k * h / (n + 1)
            p = skia.Path()
            p.moveTo(-10, y)
            for x in range(0, int(w) + 40, 40):
                p.quadTo(x + 20, y + (3 if (x // 40 + k) % 2 else -3), x + 40, y)
            cv.drawPath(p, vetas)
        # nudos
        for kx, ky in ((0.27, 0.62), (0.71, 0.35)):
            cv.drawOval(skia.Rect.MakeXYWH(w * kx, h * ky, 14, 6), vetas)
        cv.restore()
        brillo = _paint(Shader=_lineal(0, 0, 0, h * 0.5, [(255, 240, 210, 60), (255, 240, 210, 0)]))
        cv.drawRRect(_rrect(4, 4, w - 8, h * 0.45, max(1, radio - 4)), brillo)
        for x in (12, w - 12):
            cv.drawCircle(x, 11, 3.2, _paint(osc))
            cv.drawCircle(x - 0.8, 10.2, 1.2, _paint((240, 220, 190)))

    return _pieza(("madera", w, h, radio, tuple(color)), w, h + 5, pintar, m), m


# ---------------------------------------------------------------- íconos brillantes
def esfera(r, color, borde=(92, 62, 46)):
    """Bolita brillante (los niveles del mapa)."""
    m = 10

    def pintar(cv):
        c = r + 2
        cv.drawCircle(c, c + 6, r, _sombra(4, 70))
        cv.drawCircle(c, c + 4, r + 2, _paint(borde))
        cv.drawCircle(c, c + 3, r, _paint(oscurecer(color, 0.75)))
        cv.drawCircle(c, c, r + 2, _paint(borde))
        cv.drawCircle(c, c, r, _paint(Shader=_radial(c - r * 0.35, c - r * 0.45, r * 1.6,
                                                     [aclarar(color, 0.55), color, oscurecer(color, 0.82)],
                                                     [0, 0.5, 1])))
        cv.drawOval(skia.Rect.MakeXYWH(c - r * 0.6, c - r * 0.78, r * 0.75, r * 0.45),
                    _paint(Shader=_lineal(0, c - r * 0.8, 0, c - r * 0.3, [(255, 255, 255, 190), (255, 255, 255, 0)])))

    return _pieza(("esfera", r, tuple(color), tuple(borde)), 2 * r + 4, 2 * r + 10, pintar, m), m


def corazon(tam, color, borde=(92, 62, 46)):
    m = 6

    def camino(esc=1.0):
        p = skia.Path()
        s = tam * esc
        cx, cy = tam / 2, tam * 0.5
        p.moveTo(cx, cy + s * 0.42)
        p.cubicTo(cx - s * 0.62, cy, cx - s * 0.5, cy - s * 0.48, cx, cy - s * 0.2)
        p.cubicTo(cx + s * 0.5, cy - s * 0.48, cx + s * 0.62, cy, cx, cy + s * 0.42)
        p.close()
        return p

    def pintar(cv):
        cv.save()
        cv.translate(0, 2)
        cv.drawPath(camino(1.08), _sombra(2, 60))
        cv.restore()
        cv.drawPath(camino(1.12), _paint(borde))
        cv.drawPath(camino(1.0), _paint(Shader=_radial(tam * 0.38, tam * 0.3, tam * 0.8,
                                                       [aclarar(color, 0.45), color, oscurecer(color, 0.85)],
                                                       [0, 0.55, 1])))
        cv.drawOval(skia.Rect.MakeXYWH(tam * 0.24, tam * 0.27, tam * 0.2, tam * 0.13), _paint((255, 255, 255), 170))

    return _pieza(("corazon", tam, tuple(color), tuple(borde)), tam, tam, pintar, m), m


def estrella(r, color, borde=(92, 62, 46), puntas=0.5):
    m = 6

    def camino(rr):
        p = skia.Path()
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            k = rr if i % 2 == 0 else rr * puntas
            x, y = r + 2 + k * math.cos(ang), r + 2 + k * math.sin(ang)
            (p.moveTo if i == 0 else p.lineTo)(x, y)
        p.close()
        return p

    def pintar(cv):
        cv.save()
        cv.translate(0, 2)
        cv.drawPath(camino(r), _sombra(2, 55))
        cv.restore()
        if borde:
            cv.drawPath(camino(r), _paint(borde, Style=skia.Paint.kStroke_Style, StrokeWidth=max(2.5, r / 5),
                                          StrokeJoin=skia.Paint.kRound_Join))
        cv.drawPath(camino(r), _paint(Shader=_radial(r * 0.8, r * 0.6, r * 1.4,
                                                     [aclarar(color, 0.5), color, oscurecer(color, 0.85)],
                                                     [0, 0.5, 1])))
        if r > 8:
            cv.drawCircle(r * 0.78, r * 0.62, r * 0.14, _paint((255, 255, 255), 180))

    return _pieza(("estrella", round(r, 1), tuple(color), tuple(borde) if borde else None, puntas),
                  2 * r + 4, 2 * r + 4, pintar, m), m


def moneda(r):
    m = 5

    def pintar(cv):
        c = r + 2
        oro, oro_osc = (255, 206, 84), (214, 146, 22)
        cv.drawCircle(c, c + 2, r, _sombra(2, 60))
        cv.drawCircle(c, c, r + 1.5, _paint(oscurecer(oro_osc, 0.8)))
        cv.drawCircle(c, c, r, _paint(Shader=_radial(c - r * 0.4, c - r * 0.4, r * 1.5,
                                                     [(255, 244, 190), oro, oro_osc], [0, 0.5, 1])))
        cv.drawCircle(c, c, r * 0.68, _paint(oro_osc, 160, Style=skia.Paint.kStroke_Style, StrokeWidth=max(1, r / 8)))
        cv.drawOval(skia.Rect.MakeXYWH(c - r * 0.55, c - r * 0.7, r * 0.5, r * 0.3), _paint((255, 255, 255), 200))

    return _pieza(("moneda", round(r, 1)), 2 * r + 4, 2 * r + 4, pintar, m), m


def brillo_suave(r, color, a=120):
    """Resplandor redondo (para el sol, la luna, luces)."""
    def pintar(cv):
        cv.drawCircle(r, r, r, _paint(Shader=_radial(r, r, r, [tuple(color[:3]) + (a,), tuple(color[:3]) + (0,)])))
    return _pieza(("brillo", r, tuple(color), a), 2 * r, 2 * r, pintar, 0)


# ---------------------------------------------------------------- paisaje
def nube(w, h, semilla, tinte=(255, 255, 255)):
    """Nube esponjosa: bolitas unidas, degradé de arriba (blanco) a abajo (sombreado)."""
    import random
    m = 12

    def pintar(cv):
        rng = random.Random(semilla)
        # (x, y, radio) relativos: x a lo ancho, y y radio a lo alto, así siempre entra
        bolas = [(0.2, 0.62, 0.3), (0.4, 0.45, 0.42), (0.62, 0.4, 0.38), (0.8, 0.6, 0.3), (0.1, 0.72, 0.2),
                 (0.9, 0.74, 0.2)]
        p = skia.Path()
        for bx, by, br in bolas:
            p.addCircle((bx + rng.uniform(-0.03, 0.03)) * w, by * h, br * h)
        p.addRRect(_rrect(0.08 * w, 0.58 * h, 0.84 * w, 0.36 * h, 0.18 * h))
        cv.save()
        cv.translate(0, 5)
        cv.drawPath(p, _paint(oscurecer(tinte, 0.8), 70, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5)))
        cv.restore()
        cv.drawPath(p, _paint(Shader=_lineal(0, h * 0.1, 0, h * 0.9, [tinte, _mezcla(tinte, (190, 214, 236), 0.35)])))

    return _pieza(("nube", w, h, semilla, tuple(tinte)), w, h, pintar, m), m


def _suavizar(pts):
    """Polígono → curva suave (Catmull-Rom cerrado)."""
    p = skia.Path()
    n = len(pts)
    p.moveTo(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    p.close()
    return p


def isla_base(clave, w, h, cx, cy, blob_agua, blob_arena, blob_pasto, pasto, orilla, ancho_total, alto_total):
    """Arena, orilla mojada y pasto, con curvas suaves y degradés."""
    def pintar(cv):
        agua = _suavizar(blob_agua)
        arena = _suavizar(blob_arena)
        verde = _suavizar(blob_pasto)
        cv.drawPath(agua, _paint(orilla, 200, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6)))
        # sombra de la isla sobre el agua
        cv.save()
        cv.translate(0, 10)
        cv.drawPath(arena, _paint((20, 60, 80), 70, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10)))
        cv.restore()
        # espuma
        cv.drawPath(arena, _paint((240, 252, 250), 230, Style=skia.Paint.kStroke_Style, StrokeWidth=10))
        cv.drawPath(arena, _paint((92, 62, 46)))
        cv.drawPath(arena, _paint(Shader=_radial(cx, cy - h * 0.1, max(w, h) * 0.55,
                                                     [(252, 236, 196), (244, 222, 172), (222, 190, 132)],
                                                     [0, 0.7, 1])))
        # arena mojada en el borde
        cv.drawPath(arena, _paint((200, 168, 112), 110, Style=skia.Paint.kStroke_Style, StrokeWidth=7,
                                  MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
        cv.drawPath(arena, _paint((92, 62, 46), Style=skia.Paint.kStroke_Style, StrokeWidth=3))
        # pasto con sombra hacia la arena
        cv.save()
        cv.translate(0, 6)
        cv.drawPath(verde, _paint(oscurecer(pasto, 0.7), 200, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
        cv.restore()
        cv.drawPath(verde, _paint(Shader=_radial(cx - w * 0.1, cy - h * 0.25, max(w, h) * 0.6,
                                                 [aclarar(pasto, 0.25), pasto, oscurecer(pasto, 0.88)], [0, 0.6, 1])))
        cv.drawPath(verde, _paint(oscurecer(pasto, 0.72), Style=skia.Paint.kStroke_Style, StrokeWidth=2.5))

    return _pieza(("isla_base",) + tuple(clave), ancho_total, alto_total, pintar, 0, forzar=True)


def sol(r=58):
    m = 70

    def pintar(cv):
        c = r + 2
        cv.drawCircle(c, c, r + 60, _paint(Shader=_radial(c, c, r + 60, [(255, 236, 160, 150), (255, 236, 160, 0)])))
        cv.drawCircle(c, c, r, _paint(Shader=_radial(c - r * 0.3, c - r * 0.3, r * 1.4,
                                                     [(255, 248, 200), (255, 212, 96), (250, 176, 60)], [0, 0.55, 1])))
        cv.drawCircle(c - r * 0.32, c - r * 0.32, r * 0.22, _paint((255, 255, 240), 170))

    return _pieza(("sol", r), 2 * r + 4, 2 * r + 4, pintar, m), m


def palmera(alto, inclina, esc):
    """Palmera con tronco anillado, hojas curvas con nervadura y cocos brillantes.
    Devuelve (pieza, (ax, ay)): el punto de la pieza que va apoyado en el piso."""
    alto_t = alto * esc
    ancho_hoja = 92 * esc
    lado = abs(alto_t * inclina) + ancho_hoja + 10
    W, H = 2 * lado, alto_t + 70 * esc
    bx, by = lado, H - 14
    borde = (92, 62, 46)

    def pintar(cv):
        pts = [(bx + math.sin(i / 8 * 1.4) * alto_t * inclina, by - i / 8 * alto_t) for i in range(9)]
        # sombrita en el piso
        cv.drawOval(skia.Rect.MakeXYWH(bx - 20 * esc, by - 5 * esc, 40 * esc, 10 * esc), _sombra(3, 60))
        tronco = skia.Path()
        tronco.moveTo(*pts[0])
        for i in range(1, len(pts) - 1, 2):
            tronco.quadTo(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        for i in range(len(pts) - 1):
            g = (12 - i * 0.8) * esc
            seg = skia.Path()
            seg.moveTo(*pts[i])
            seg.lineTo(*pts[i + 1])
            cv.drawPath(seg, _paint(borde, Style=skia.Paint.kStroke_Style, StrokeWidth=g + 4,
                                    StrokeCap=skia.Paint.kRound_Cap))
        for i in range(len(pts) - 1):
            g = (12 - i * 0.8) * esc
            seg = skia.Path()
            seg.moveTo(*pts[i])
            seg.lineTo(*pts[i + 1])
            cv.drawPath(seg, _paint(Shader=_lineal(pts[i][0] - g, 0, pts[i][0] + g, 0,
                                                   [(214, 160, 100), (190, 134, 78), (150, 100, 58)], [0, 0.45, 1]),
                                    Style=skia.Paint.kStroke_Style, StrokeWidth=g, StrokeCap=skia.Paint.kRound_Cap))
            # anillos
            mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
            anillo = skia.Path()
            anillo.moveTo(mx - g * 0.45, my - 1)
            anillo.quadTo(mx, my + 3 * esc, mx + g * 0.45, my - 1)
            cv.drawPath(anillo, _paint((130, 84, 48), 200, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6 * esc))
        cx, cy = pts[-1]
        hojas = (-2.75, -2.15, -1.5, -0.95, -0.35, 0.3)
        orden = sorted(range(len(hojas)), key=lambda k: -abs(hojas[k] + 1.5))
        for k in orden:
            a = hojas[k]
            largo = (74 + 10 * (k % 2)) * esc
            fin = (cx + math.cos(a) * largo, cy + math.sin(a) * largo * 0.55 + largo * 0.38)
            ctrl = (cx + math.cos(a) * largo * 0.55, cy + math.sin(a) * largo * 0.55 - 16 * esc)
            nx, ny = -math.sin(a) * 15 * esc, math.cos(a) * 15 * esc
            hoja = skia.Path()
            hoja.moveTo(cx, cy)
            hoja.quadTo(ctrl[0] + nx, ctrl[1] + ny, fin[0], fin[1])
            hoja.quadTo(ctrl[0] - nx, ctrl[1] - ny, cx, cy)
            hoja.close()
            verde = (112, 190, 96) if k % 2 else (92, 170, 84)
            cv.drawPath(hoja, _paint(Shader=_lineal(cx, cy - 12 * esc, fin[0], fin[1],
                                                    [aclarar(verde, 0.25), verde, oscurecer(verde, 0.8)], [0, 0.5, 1])))
            cv.drawPath(hoja, _paint((40, 92, 50), Style=skia.Paint.kStroke_Style, StrokeWidth=2.2 * esc,
                                     StrokeJoin=skia.Paint.kRound_Join))
            vena = skia.Path()
            vena.moveTo(cx, cy)
            vena.quadTo(ctrl[0], ctrl[1], fin[0], fin[1])
            cv.drawPath(vena, _paint((60, 120, 60), 200, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6 * esc))
        for dx in (-6, 5):
            c = (cx + dx * esc, cy + 7 * esc)
            cv.drawCircle(c[0], c[1], 7 * esc, _paint(borde))
            cv.drawCircle(c[0], c[1], 5.5 * esc, _paint(Shader=_radial(c[0] - 2 * esc, c[1] - 2 * esc, 7 * esc,
                                                                       [(180, 124, 76), (130, 82, 44)])))

    pieza = _pieza(("palmera", round(alto, 1), round(inclina, 3), round(esc, 3)), W, H, pintar, 0, forzar=True)
    return pieza, (bx, by)


def pedestal(w, h, color):
    """Tarima redonda (para que el gato se pruebe la ropa)."""
    m = 14

    def pintar(cv):
        borde = (92, 62, 46)
        alto_tapa = h * 0.72
        cv.drawOval(skia.Rect.MakeXYWH(4, h * 0.3 + 6, w - 8, h * 0.7), _sombra(7, 70))
        lado = skia.Path()
        lado.addOval(skia.Rect.MakeXYWH(0, h - alto_tapa, w, alto_tapa))
        lado.addRect(skia.Rect.MakeXYWH(0, alto_tapa / 2, w, h - alto_tapa))
        lado.setFillType(skia.PathFillType.kWinding)
        cv.drawPath(lado, _paint(borde))
        interior = skia.Path()
        interior.addOval(skia.Rect.MakeXYWH(3, h - alto_tapa, w - 6, alto_tapa - 3))
        interior.addRect(skia.Rect.MakeXYWH(3, alto_tapa / 2, w - 6, h - alto_tapa))
        cv.drawPath(interior, _paint(Shader=_lineal(0, 0, w, 0, [oscurecer(color, 0.7), oscurecer(color, 0.88),
                                                                 oscurecer(color, 0.66)], [0, 0.35, 1])))
        tapa = skia.Rect.MakeXYWH(0, 0, w, alto_tapa)
        cv.drawOval(tapa, _paint(borde))
        cv.drawOval(skia.Rect.MakeXYWH(3, 3, w - 6, alto_tapa - 6),
                    _paint(Shader=_radial(w * 0.42, alto_tapa * 0.35, w * 0.6,
                                          [aclarar(color, 0.35), color, oscurecer(color, 0.9)], [0, 0.6, 1])))
        cv.drawOval(skia.Rect.MakeXYWH(w * 0.12, alto_tapa * 0.16, w * 0.76, alto_tapa * 0.68),
                    _paint(aclarar(color, 0.45), 200, Style=skia.Paint.kStroke_Style, StrokeWidth=3))

    return _pieza(("pedestal", w, h, tuple(color)), w, h, pintar, m), m


# ---------------------------------------------------------------- traductor pygame.draw → Skia
def a_pygame(sup):
    """skia.Surface → pygame.Surface con transparencia."""
    W, H = sup.width(), sup.height()
    arr = sup.makeImageSnapshot().toarray(colorType=skia.kBGRA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType)
    return pygame.image.frombuffer(arr.tobytes(), (W, H), "BGRA").copy()


class HojaSkia:
    """Se hace pasar por la superficie de pygame (solo para 'blit')."""

    def __init__(self, cv, w, h):
        self.cv, self.w, self.h = cv, w, h

    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    def blit(self, fuente, destino, *a, **kw):
        import numpy as np
        w, h = fuente.get_size()
        arr = np.frombuffer(pygame.image.tobytes(fuente, "RGBA"), np.uint8).reshape(h, w, 4).copy()
        img = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)
        x, y = (destino[0], destino[1]) if not isinstance(destino, pygame.Rect) else destino.topleft
        self.cv.drawImage(img, x, y, skia.SamplingOptions(skia.FilterMode.kLinear))


def _rect(r):
    x, y, w, h = tuple(r)[:4]
    return skia.Rect.MakeXYWH(x, y, w, h)


class TrazosSkia:
    """Mismas funciones que pygame.draw (circle, rect, ellipse, arc, polygon, line, lines), pero con Skia:
    todo sale con bordes suaves y respeta la transparencia de los colores."""

    def __init__(self, cv, sombreado=False):
        self.cv = cv
        self.sombreado = sombreado   # rellenos con volumen (para árboles, rocas, hongos...)

    def _relleno(self, color, x, y, w, h):
        if self.sombreado and (len(color) == 3 or color[3] == 255) and w > 6 and h > 6:
            return relleno_sombreado(color, x, y, w, h)
        return self._p(color)

    @staticmethod
    def _p(color, ancho=0):
        p = skia.Paint(AntiAlias=True, Color=_c(color))
        if ancho:
            p.setStyle(skia.Paint.kStroke_Style)
            p.setStrokeWidth(ancho)
            p.setStrokeCap(skia.Paint.kRound_Cap)
            p.setStrokeJoin(skia.Paint.kRound_Join)
        return p

    def circle(self, s, color, centro, radio, width=0):
        if width:
            self.cv.drawCircle(centro[0], centro[1], max(0.5, radio - width / 2), self._p(color, width))
        else:
            self.cv.drawCircle(centro[0], centro[1], radio,
                               self._relleno(color, centro[0] - radio, centro[1] - radio, 2 * radio, 2 * radio))

    def ellipse(self, s, color, rect, width=0):
        r = _rect(rect)
        if width:
            r.inset(width / 2, width / 2)
            self.cv.drawOval(r, self._p(color, width))
        else:
            self.cv.drawOval(r, self._relleno(color, r.x(), r.y(), r.width(), r.height()))

    def rect(self, s, color, rect, width=0, border_radius=0, **kw):
        r = _rect(rect)
        if width:
            r.inset(width / 2, width / 2)
        if border_radius > 0:
            p = self._p(color, width) if width else self._relleno(color, r.x(), r.y(), r.width(), r.height())
            self.cv.drawRRect(skia.RRect.MakeRectXY(r, border_radius, border_radius), p)
        else:
            p = self._p(color, width)
            if width:
                p.setStrokeJoin(skia.Paint.kMiter_Join)
            self.cv.drawRect(r, p)

    def arc(self, s, color, rect, inicio, fin, width=1):
        r = _rect(rect)
        r.inset(width / 2, width / 2)
        self.cv.drawArc(r, -math.degrees(fin), math.degrees(fin - inicio), False, self._p(color, width))

    def polygon(self, s, color, pts, width=0):
        if len(pts) < 3:
            return
        camino = skia.Path()
        camino.addPoly([skia.Point(*p) for p in pts], True)
        if width:
            self.cv.drawPath(camino, self._p(color, width))
        else:
            b = camino.computeTightBounds()
            self.cv.drawPath(camino, self._relleno(color, b.x(), b.y(), b.width(), b.height()))

    def line(self, s, color, a, b, width=1):
        self.cv.drawLine(a[0], a[1], b[0], b[1], self._p(color, max(1, width)))

    def lines(self, s, color, cerrado, pts, width=1):
        camino = skia.Path()
        camino.addPoly([skia.Point(*p) for p in pts], cerrado)
        self.cv.drawPath(camino, self._p(color, max(1, width)))

    aaline = line
    aalines = lines


def relleno_sombreado(color, x, y, w, h):
    """Pintura con volumen: más clara arriba a la izquierda, más oscura abajo."""
    a = color[3] if len(color) == 4 else 255
    cs = [aclarar(color, 0.2) + (a,), tuple(color[:3]) + (a,), oscurecer(color, 0.86) + (a,)]
    sh = _radial(x + w * 0.36, y + h * 0.28, max(w, h) * 0.9, cs, [0, 0.5, 1])
    return skia.Paint(AntiAlias=True, Shader=sh)


class CapaSkia:
    """Hoja transparente en coordenadas lógicas donde se puede dibujar con las funciones de
    siempre (hoja.d.polygon(hoja, ...)) y pegar Lienzos. Al final: terminar() → Lienzo."""

    def __init__(self, w, h, sombreado=True):
        self.e = escala()
        self.w, self.h = w, h
        self.hoja = skia.Surface(max(1, math.ceil(w * self.e)), max(1, math.ceil(h * self.e)))
        self.cv = self.hoja.getCanvas()
        self.cv.clear(skia.ColorTRANSPARENT)
        self.cv.scale(self.e, self.e)
        self.d = TrazosSkia(self.cv, sombreado)

    def get_width(self):
        return self.w

    def get_height(self):
        return self.h

    def blit(self, fuente, destino, *a, **kw):
        import numpy as np
        sup = fuente.sup if isinstance(fuente, Lienzo) else fuente
        w, h = sup.get_size()
        arr = np.frombuffer(pygame.image.tobytes(sup, "RGBA"), np.uint8).reshape(h, w, 4).copy()
        img = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)
        x, y = (destino[0], destino[1]) if not isinstance(destino, pygame.Rect) else destino.topleft
        lw, lh = (fuente.w, fuente.h) if isinstance(fuente, Lienzo) else (w, h)
        self.cv.drawImageRect(img, skia.Rect.MakeXYWH(x, y, lw, lh), skia.SamplingOptions(skia.FilterMode.kLinear))

    def terminar(self):
        return Lienzo.desde(a_pygame(self.hoja), self.e)


def luna(r=52):
    m = 8

    def pintar(cv):
        c = r + 2
        cv.drawCircle(c, c, r, _paint(Shader=_radial(c - r * 0.35, c - r * 0.35, r * 1.5,
                                                     [(255, 254, 240), (240, 238, 216), (206, 204, 188)], [0, 0.55, 1])))
        for dx, dy, rr in ((-16, -10, 10), (14, 12, 7), (10, -20, 5), (-6, 22, 6), (22, -4, 4)):
            x, y = c + dx, c + dy
            cv.drawCircle(x, y, rr, _paint(Shader=_radial(x + rr * 0.3, y + rr * 0.3, rr * 1.2,
                                                          [(232, 230, 212), (204, 200, 182)])))
            cv.drawCircle(x, y, rr, _paint((180, 176, 160), 120, Style=skia.Paint.kStroke_Style, StrokeWidth=1))

    return _pieza(("luna", r), 2 * r + 4, 2 * r + 4, pintar, m), m


def sol_bajo(r=74):
    m = 8

    def pintar(cv):
        c = r + 2
        cv.drawCircle(c, c, r, _paint(Shader=_radial(c - r * 0.3, c - r * 0.35, r * 1.5,
                                                     [(255, 214, 150), (255, 160, 90), (236, 112, 70)], [0, 0.5, 1])))
        cv.drawCircle(c - r * 0.28, c - r * 0.3, r * 0.2, _paint((255, 236, 200), 150))

    return _pieza(("sol_bajo", r), 2 * r + 4, 2 * r + 4, pintar, m), m


def ola(ancho, alto, periodo, amp, color, semilla=0):
    """Tira de mar que se repite cada 'periodo' (para moverla de costado sin cortes):
    cresta ondulada con espuma, agua con degradé y brillitos."""
    import random
    m = 0

    def cresta(x):
        t = x / periodo * math.tau
        return amp + math.sin(t) * amp + math.sin(3 * t + 1.3) * amp * 0.25

    def pintar(cv):
        p = skia.Path()
        p.moveTo(0, alto)
        x = 0.0
        while x <= ancho + 4:
            p.lineTo(x, cresta(x))
            x += 4
        p.lineTo(ancho + 4, alto)
        p.close()
        cv.drawPath(p, _paint(Shader=_lineal(0, 0, 0, min(alto, 260), [aclarar(color, 0.16), color,
                                                                         oscurecer(color, 0.88)], [0, 0.35, 1])))
        # espuma de la cresta: un brillo suave y una línea clara
        borde = skia.Path()
        x = 0.0
        borde.moveTo(0, cresta(0))
        while x <= ancho + 4:
            borde.lineTo(x, cresta(x))
            x += 4
        cv.save()
        cv.clipPath(p, doAntiAlias=True)
        cv.translate(0, 5)
        cv.drawPath(borde, _paint(aclarar(color, 0.5), 110, Style=skia.Paint.kStroke_Style, StrokeWidth=8,
                                  MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3)))
        cv.restore()
        cv.drawPath(borde, _paint(aclarar(color, 0.62), 235, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                                  StrokeCap=skia.Paint.kRound_Cap))
        # brillitos (se repiten con el mismo período)
        rng = random.Random(semilla)
        marcas = [(rng.uniform(0, periodo), rng.uniform(amp * 2 + 14, min(alto - 6, amp * 2 + 90)),
                   rng.uniform(10, 26)) for _ in range(3)]
        brillo = _paint(aclarar(color, 0.45), 150, Style=skia.Paint.kStroke_Style, StrokeWidth=2.5,
                        StrokeCap=skia.Paint.kRound_Cap)
        x0 = 0.0
        while x0 < ancho + periodo:
            for bx, by, bl in marcas:
                if by < alto - 4:
                    cv.drawLine(x0 + bx, by, x0 + bx + bl, by, brillo)
            x0 += periodo

    return _pieza(("ola", ancho, round(alto, 1), periodo, amp, tuple(color), semilla), ancho, alto, pintar, m,
                  forzar=True), m


def pergamino(w, h):
    """Papel de mapa del tesoro: degradé cálido, viñeta suave, manchitas, cuadrícula,
    rosa de los vientos y un caminito punteado con su cruz."""
    import random

    def pintar(cv):
        cv.drawRect(skia.Rect.MakeWH(w, h), _paint(Shader=_lineal(0, 0, 0, h, [(255, 250, 236), (248, 236, 208)])))
        rng = random.Random(7)
        # manchas de papel viejo
        for _ in range(9):
            x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(60, 180)
            cv.drawCircle(x, y, r, _paint(Shader=_radial(x, y, r, [(214, 176, 120, 26), (214, 176, 120, 0)])))
        # cuadrícula muy suave
        linea = _paint((180, 140, 90), 22, Style=skia.Paint.kStroke_Style, StrokeWidth=1)
        for x in range(0, int(w) + 1, 80):
            cv.drawLine(x, 0, x, h, linea)
        for y in range(0, int(h) + 1, 80):
            cv.drawLine(0, y, w, y, linea)
        # rosa de los vientos
        cx, cy = w - 90, h - 90
        tinta = (170, 120, 70)
        for k in range(8):
            a = k * math.tau / 8 - math.pi / 2
            largo = 62 if k % 2 == 0 else 38
            punta = (cx + math.cos(a) * largo, cy + math.sin(a) * largo)
            for lado, alfa in ((0.35, 55), (-0.35, 30)):
                q = (cx + math.cos(a + lado) * 12, cy + math.sin(a + lado) * 12)
                p = skia.Path()
                p.moveTo(*punta)
                p.lineTo(*q)
                p.lineTo(cx, cy)
                p.close()
                cv.drawPath(p, _paint(tinta, alfa))
        for r, a in ((46, 50), (52, 30)):
            cv.drawCircle(cx, cy, r, _paint(tinta, a, Style=skia.Paint.kStroke_Style, StrokeWidth=1.6))
        cv.drawCircle(cx, cy, 4, _paint(tinta, 70))
        # caminito punteado con una cruz
        camino = skia.Path()
        for i in range(41):
            t = i / 40
            x, y = 40 + t * 260, h - 40 - math.sin(t * 5) * 30 - t * 60
            (camino.moveTo if i == 0 else camino.lineTo)(x, y)
        guion = _paint((190, 130, 80), 60, Style=skia.Paint.kStroke_Style, StrokeWidth=3,
                       StrokeCap=skia.Paint.kRound_Cap, PathEffect=skia.DashPathEffect.Make([1, 11], 0))
        cv.drawPath(camino, guion)
        x, y = 300, h - 100 - math.sin(5) * 30
        cruz = _paint((200, 90, 70), 70, Style=skia.Paint.kStroke_Style, StrokeWidth=4, StrokeCap=skia.Paint.kRound_Cap)
        cv.drawLine(x - 9, y - 9, x + 9, y + 9, cruz)
        cv.drawLine(x - 9, y + 9, x + 9, y - 9, cruz)
        # viñeta: bordes un poco tostados
        cv.drawRect(skia.Rect.MakeWH(w, h), _paint(Shader=skia.GradientShader.MakeRadial(
            (w / 2, h / 2), math.hypot(w, h) / 2, [_c((150, 100, 50), 0), _c((150, 100, 50), 0), _c((150, 100, 50), 60)],
            [0, 0.62, 1], skia.TileMode.kClamp, 0, skia.Matrix.Scale(1, h / w * 1.25))))

    return _pieza(("pergamino", w, h), w, h, pintar, 0, forzar=True)


# ---------------------------------------------------------------- controles
def campo(w, h, borde, radio=14):
    """Cuadro donde se escribe: blanco, con sombrita interior arriba (parece hundido)."""
    m = 4

    def pintar(cv):
        cara = _rrect(0, 0, w, h, radio)
        cv.drawRRect(cara, _paint((255, 255, 255)))
        cv.save()
        cv.clipRRect(cara, doAntiAlias=True)
        cv.drawRect(skia.Rect.MakeXYWH(0, 0, w, 16), _paint(Shader=_lineal(0, 0, 0, 16, [(120, 96, 70, 46), (120, 96, 70, 0)])))
        cv.restore()
        cv.drawRRect(_rrect(1.5, 1.5, w - 3, h - 3, radio - 1.5),
                     _paint(borde, Style=skia.Paint.kStroke_Style, StrokeWidth=3))

    return _pieza(("campo", w, h, tuple(borde), radio), w, h, pintar, m), m


def resplandor(w, h, color, radio=18):
    """Halo difuso alrededor de un rectángulo (el cuadro de texto cuando está activo)."""
    m = 16

    def pintar(cv):
        cv.drawRRect(_rrect(-4, -4, w + 8, h + 8, radio + 4),
                     _paint(color, 200, Style=skia.Paint.kStroke_Style, StrokeWidth=6,
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))

    return _pieza(("resplandor", w, h, tuple(color), radio), w, h, pintar, m), m


def pista(w, h, color, borde=(92, 62, 46)):
    """Canaleta hundida (interruptores, deslizadores, barra de tiempo)."""
    m = 4

    def pintar(cv):
        r = h / 2 + 1.5
        cv.drawRRect(_rrect(-3, -3, w + 6, h + 6, r + 1.5), _paint(borde))
        forma = _rrect(0, 0, w, h, h / 2)
        cv.drawRRect(forma, _paint(Shader=_lineal(0, 0, 0, h, [oscurecer(color, 0.86), color, aclarar(color, 0.12)],
                                                  [0, 0.45, 1])))
        cv.save()
        cv.clipRRect(forma, doAntiAlias=True)
        cv.drawRRect(_rrect(0, -h * 0.6, w, h, h / 2), _paint((60, 40, 30), 40, Style=skia.Paint.kStroke_Style,
                                                               StrokeWidth=3, MaskFilter=skia.MaskFilter.MakeBlur(
                                                                   skia.kNormal_BlurStyle, 1.5)))
        cv.restore()

    return _pieza(("pista", w, round(h, 1), tuple(color), tuple(borde)), w, h, pintar, m), m


def relleno(w, h, color):
    """La parte llena de una barra: con volumen y brillo arriba."""
    def pintar(cv):
        forma = _rrect(0, 0, w, h, h / 2)
        cv.drawRRect(forma, _paint(Shader=_lineal(0, 0, 0, h, [aclarar(color, 0.25), color, oscurecer(color, 0.85)],
                                                  [0, 0.5, 1])))
        if h >= 8:
            cv.drawRRect(_rrect(h / 3, 1.5, max(1, w - 2 * h / 3), h * 0.32, h * 0.16), _paint((255, 255, 255), 110))

    return _pieza(("relleno", int(w), round(h, 1), tuple(color)), max(1, int(w)), h, pintar, 0)


def pastilla(w, h, color, borde=(92, 62, 46)):
    """Cartelito redondeado con brillo (PENSÁ / CALCULÁ)."""
    m = 6

    def pintar(cv):
        cv.drawRRect(_rrect(1, 3, w - 2, h, h / 2), _sombra(2.5, 60))
        cv.drawRRect(_rrect(0, 0, w, h, h / 2), _paint(borde))
        cv.drawRRect(_rrect(2, 2, w - 4, h - 4, h / 2 - 2),
                     _paint(Shader=_lineal(0, 2, 0, h - 2, [aclarar(color, 0.22), color, oscurecer(color, 0.88)],
                                           [0, 0.55, 1])))
        cv.drawRRect(_rrect(h / 3, 4, w - 2 * h / 3, h * 0.3, h * 0.15), _paint((255, 255, 255), 90))

    return _pieza(("pastilla", w, h, tuple(color), tuple(borde)), w, h, pintar, m), m
