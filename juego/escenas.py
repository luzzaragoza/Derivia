"""Las pantallas del juego (estilo aventura: islas, mar, madera y pergamino)."""

import math
import random

import pygame

from . import gato as modulo_gato
from . import paisaje, ropa, ui
from .fx import Efectos, Fueguito, rebote, suave
from .gato import Gato
from .mate import (C, ERRORES, ErrorEntrada, casi_igual, diagnosticar, diagnosticar_primitiva, equivalentes,
                   es_primitiva, parsear, tex)
from .mate import x as VAR_X
from .mate import y as VAR_Y
from .mate import z as VAR_Z
from .mundos import MUNDOS, generar, generar_nivel, mundo_por_id
from .sonido import sonidos
from .ui import (ALTO, ANCHO, ARENA, ARENA_OSC, BORDE, CORAL, DURAZNO, GRIS, LAVANDA, LAVANDA_OSC,
                 MADERA, MADERA_OSC, MENTA_OSC, ROSA_OSC, SOL, SOL_OSC, SUAVE, TARJETA, TINTA, Boton, CampoTexto)

CREMA = (255, 248, 230)
FRASES_BIEN = ["¡Bien!", "¡Excelente!", "¡Eso!", "¡Perfecto!", "¡Muy bien!", "¡Genial!", "¡Impecable!", "¡Miau, sí!"]
FRASES_MAL = ["Uy...", "Casi...", "Mmm, no.", "¡Ups!"]
FRASES_INICIO = ["¡Vamos! Yo te acompaño.", "¡A practicar!", "¡Miau! ¿Arrancamos?", "Tranqui, de a un paso."]


def centrar(sup, s, y, x=None):
    r = s.get_rect(midtop=(x if x is not None else ANCHO // 2, y))
    sup.blit(s, r)
    return r


def letrero(sup, rect, texto_s, tam=26):
    """Cartel de madera con un título."""
    rect = pygame.Rect(rect)
    ui.tabla_madera(sup, rect)
    t = ui.texto_borde(texto_s, tam, CREMA, MADERA_OSC, 2)
    sup.blit(t, t.get_rect(center=rect.center))


def dibujar_monedero(sup, monedas, arriba_derecha):
    """Cartelito de madera con las monedas que tenés."""
    t = ui.texto_borde(str(monedas), 24, CREMA, MADERA_OSC, 2)
    r = pygame.Rect(0, 0, t.get_width() + 70, 50)
    r.topright = arriba_derecha
    ui.tabla_madera(sup, r, radio=14)
    ui.moneda(sup, (r.left + 28, r.centery), 15)
    sup.blit(t, t.get_rect(midleft=(r.left + 50, r.centery)))
    return r


def nombre_corto(m):
    return m.nombre.replace("Mundo ", "")


class Escena:
    permite_m = True
    musica = "isla"

    def __init__(self, app):
        self.app = app
        self.botones = []

    def evento(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.atras()
            return True
        for b in list(self.botones):
            if b.evento(e):
                return True
        return False

    def atras(self):
        pass

    def actualizar(self, dt):
        pass

    def dibujar(self, sup):
        pass

    def dibujar_botones(self, sup):
        for b in self.botones:
            b.dibujar(sup)

    def boton_opciones(self, rect):
        icono = pygame.Surface((40, 40), pygame.SRCALPHA)
        ui.engranaje(icono, (20, 20), 32, BORDE)
        return Boton(rect, icono, self.abrir_opciones, ARENA, relieve=4)

    def abrir_opciones(self):
        self.app.cambiar(Opciones(self.app, self), None)

    def armar(self):
        pass


# =============================================================== MENÚ

class Menu(Escena):
    def __init__(self, app):
        super().__init__(app)
        self.cielo = paisaje.Cielo(semilla=2)
        self.mar = paisaje.Mar(470)
        self.gato = Gato(170)
        self.gato.reaccionar("feliz", 1.2)
        self.t = 0.0
        self.armar()

    def armar(self):
        app = self.app
        n = len(app.progreso.cuaderno)
        x, y = 690, 236
        self.botones = [
            Boton((x, y, 400, 74), "¡Jugar!", self.jugar, CORAL, CREMA, tam=34, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER]),
            Boton((x, y + 92, 400, 56), "Tienda del michi", lambda: app.cambiar(Tienda(app), "ola"), (255, 170, 200), tam=24),
            Boton((x, y + 162, 400, 56), f"Cuaderno de errores ({n})", lambda: app.cambiar(Cuaderno(app)), SOL, tam=23),
            Boton((x, y + 232, 400, 56), "Cómo escribir fórmulas", lambda: app.cambiar(Ayuda(app)), LAVANDA, tam=23),
            Boton((x, y + 302, 193, 56), "Opciones", self.abrir_opciones, ARENA, tam=22),
            Boton((x + 207, y + 302, 193, 56), "Salir", app.salir, ARENA, tam=22),
        ]

    def jugar(self):
        self.app.cambiar(Mapa(self.app), "ola")

    def atras(self):
        self.app.salir()

    def evento(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and self.rect_gato.collidepoint(e.pos):
            sonidos.tocar("miau")
            self.gato.reaccionar(random.choice(["feliz", "sorpresa", "festejo"]), 1.2)
            return True
        return super().evento(e)

    rect_gato = pygame.Rect(150, 420, 220, 240)

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.gato.actualizar(dt)
        if self.botones[0].rect.collidepoint(pygame.mouse.get_pos()) and self.gato.animo == "normal":
            self.gato.reaccionar("feliz", 0.8, saltar=False)

    def dibujar(self, sup):
        self.cielo.dibujar(sup)
        self.mar.dibujar(sup)
        paisaje.dibujar_isla(sup, (math.sin(self.t * 0.8) * 2, 470), 520, 230, ui.PASTO, semilla=5, palmeras=2)
        paisaje.dibujar_isla(sup, (1040, 610), 220, 110, ui.PASTO, semilla=9, palmeras=1)
        self.gato.dibujar(sup, (260, 640))
        # título
        titulo = ui.texto_borde("Derivia", 128, SOL, BORDE, 6)
        y = 40 + math.sin(self.t * 1.6) * 6
        sup.blit(titulo, titulo.get_rect(midtop=(430, y)))
        sub = ui.texto_borde("Derivadas e integrales, isla por isla", 26, CREMA, BORDE, 3)
        sup.blit(sub, sub.get_rect(midtop=(430, y + 168)))
        dibujar_monedero(sup, self.app.progreso.monedas, (ANCHO - 24, 24))
        self.dibujar_botones(sup)


# =============================================================== MAPA (camino)

def _catmull(pts, pasos=24):
    if len(pts) < 2:
        return pts
    p = [pts[0]] + pts + [pts[-1]]
    salida = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = (pygame.Vector2(q) for q in p[i - 1:i + 3])
        for k in range(pasos):
            t = k / pasos
            salida.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    salida.append(pygame.Vector2(pts[-1]))
    return salida


class Mapa(Escena):
    def __init__(self, app, mundo_id=None):
        super().__init__(app)
        prog = app.progreso
        if mundo_id is None:
            abiertos = [m.id for m in MUNDOS if prog.mundo_desbloqueado(m.id)]
            mundo_id = abiertos[-1] if abiertos else MUNDOS[0].id
        self.sel = [m.id for m in MUNDOS].index(mundo_id)
        self.cielo = paisaje.Cielo(semilla=4, nubes=5)
        self.mar = paisaje.Mar(215, [(116, 204, 216), (88, 190, 204), ui.MAR, ui.MAR_OSC])
        self.gato = Gato(92)
        self.t = 0.0
        self.desliz = None
        self.hover = None
        self.capas = {}
        self.fx = Efectos()
        self.arranque = None
        self.armar()

    @property
    def mundo(self):
        return MUNDOS[self.sel]

    def atras(self):
        self.app.cambiar(Menu(self.app), "fundido")

    def _nodos(self, m):
        n = len(m.niveles)
        pts = []
        for i in range(n):
            x = 300 + (680 * i / max(1, n - 1))
            y = 470 + 78 * math.sin(i * 1.35 + 0.4)
            pts.append((x, y))
        return pts

    def _actual(self, m):
        """El primer nivel desbloqueado sin aprobar (ahí se sienta el gato)."""
        p = self.app.progreso
        abiertos = [i for i in range(len(m.niveles)) if p.desbloqueado(m.id, i)]
        for i in abiertos:
            if not p.aprobado(m.id, i):
                return i
        return abiertos[-1] if abiertos else None

    def _capa(self, idx):
        """Isla + camino + nodos (lo que no se mueve), cacheado por mundo."""
        if idx in self.capas:
            return self.capas[idx]
        m = MUNDOS[idx]
        p = self.app.progreso
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        pasto = tuple(int(a * 0.55 + b * 0.45) for a, b in zip(ui.PASTO, m.color))
        paisaje.dibujar_isla(s, (100, 205), 1080, 500, pasto, semilla=idx * 7 + 1, palmeras=4, palmeras_borde=True)
        nodos = self._nodos(m)
        curva = _catmull(nodos)
        # camino
        por_tramo = (len(curva) - 1) / max(1, len(nodos) - 1)
        for k in range(0, len(curva) - 1, 3):
            tramo = int(k / por_tramo)
            hecho = p.aprobado(m.id, tramo) and tramo + 1 < len(nodos) and p.desbloqueado(m.id, tramo + 1)
            if hecho:
                pygame.draw.line(s, BORDE, curva[k], curva[min(k + 3, len(curva) - 1)], 14)
            pygame.draw.circle(s, ui.oscurecer(m.color, 0.6) if hecho else (196, 160, 110), curva[k], 7 if hecho else 5)
        for k in range(0, len(curva) - 1, 3):
            tramo = int(k / por_tramo)
            hecho = p.aprobado(m.id, tramo) and tramo + 1 < len(nodos) and p.desbloqueado(m.id, tramo + 1)
            if hecho:
                pygame.draw.line(s, ui.aclarar(m.color, 0.1), curva[k], curva[min(k + 3, len(curva) - 1)], 8)
        # nodos
        for i, (nx, ny) in enumerate(nodos):
            nivel = m.niveles[i]
            abierto = p.desbloqueado(m.id, i)
            r = 38 if nivel.jefe else 30
            if nivel.jefe:
                pygame.draw.line(s, BORDE, (nx + 10, ny - r - 34), (nx + 10, ny - r + 6), 4)
                pygame.draw.polygon(s, BORDE, [(nx + 12, ny - r - 36), (nx + 46, ny - r - 24), (nx + 12, ny - r - 10)])
                pygame.draw.polygon(s, CORAL if abierto else GRIS,
                                    [(nx + 13, ny - r - 32), (nx + 40, ny - r - 24), (nx + 13, ny - r - 15)])
            pygame.draw.circle(s, BORDE, (nx, ny + 6), r + 3)
            pygame.draw.circle(s, BORDE, (nx, ny), r + 3)
            if abierto:
                color = m.color if p.aprobado(m.id, i) else SOL
                pygame.draw.circle(s, ui.oscurecer(color, 0.8), (nx, ny + 5), r)
                pygame.draw.circle(s, color, (nx, ny), r)
                pygame.draw.circle(s, ui.aclarar(color, 0.5), (nx - r * 0.3, ny - r * 0.35), r * 0.22)
                num = "J" if nivel.jefe else str(i + 1)
                t = ui.texto_borde(num, 30 if nivel.jefe else 26, CREMA, BORDE, 3, sombra=False)
                s.blit(t, t.get_rect(center=(nx, ny + 1)))
                est = p.estrellas(m.id, i)
                for k in range(3):
                    ex = nx + (k - 1) * 24
                    ey = ny + r + 16 - (4 if k == 1 else 0)
                    ui.estrella(s, (ex, ey), 11, SOL if k < est else (238, 228, 210), BORDE, brillo=False)
            else:
                pygame.draw.circle(s, (200, 192, 178), (nx, ny), r)
                ui.candado(s, (nx, ny), int(r * 0.8), (150, 140, 126))
        self.capas[idx] = s
        return s

    def armar(self):
        p = self.app.progreso
        m = self.mundo
        self.botones = [Boton((20, 18, 128, 50), "Menú", self.atras, DURAZNO, tam=22),
                        self.boton_opciones((ANCHO - 76, 18, 56, 50))]
        txt = "Volver a bloquear" if p.todo_desbloqueado else "Desbloquear todo"
        self.botones.append(Boton((ANCHO - 290, 18, 200, 50), txt, self.alternar_todo, ARENA, tam=17))
        for d, x in ((-1, ANCHO // 2 - 360), (1, ANCHO // 2 + 310)):
            destino = self.sel + d
            ok = 0 <= destino < len(MUNDOS) and p.mundo_desbloqueado(MUNDOS[destino].id)
            icono = pygame.Surface((30, 30), pygame.SRCALPHA)
            ui.triangulo(icono, (15, 15), 22, CREMA if ok else (230, 222, 210), d)
            self.botones.append(Boton((x, 100, 50, 50), icono, (lambda d=d: self.mover(d)), LAVANDA,
                                      habilitado=ok, tecla=pygame.K_LEFT if d < 0 else pygame.K_RIGHT,
                                      relieve=5, sonido="salto"))
        # fichas de islas abajo
        n = len(MUNDOS)
        x0 = ANCHO // 2 - (n - 1) * 32
        for k, mm in enumerate(MUNDOS):
            abierto = p.mundo_desbloqueado(mm.id)
            icono = ui.texto(nombre_corto(mm), 17, BORDE if abierto else (170, 160, 150), negrita=True)
            b = Boton((x0 + k * 64 - 26, 666, 52, 40), icono, (lambda k=k: self.ir(k)),
                      mm.color if abierto else (220, 214, 204), habilitado=abierto, radio=14, relieve=4,
                      sonido="salto")
            b.ficha = k
            self.botones.append(b)
        self.nodos = self._nodos(m)
        self.gato_nodo = self._actual(m)

    def alternar_todo(self):
        p = self.app.progreso
        p.todo_desbloqueado = not p.todo_desbloqueado
        p.guardar()
        self.capas = {}
        self.armar()

    def mover(self, d):
        self.ir(self.sel + d)

    def ir(self, destino):
        if destino == self.sel or not (0 <= destino < len(MUNDOS)):
            return
        if not self.app.progreso.mundo_desbloqueado(MUNDOS[destino].id):
            return
        direccion = 1 if destino > self.sel else -1
        self.desliz = [0.0, direccion, self.sel]
        self.sel = destino
        self.hover = None
        self.armar()
        self.gato.reaccionar("feliz", 0.8)

    def _nodo_en(self, pos):
        for i, (nx, ny) in enumerate(self.nodos):
            r = 40 if self.mundo.niveles[i].jefe else 32
            if (pos[0] - nx) ** 2 + (pos[1] - ny) ** 2 <= r * r:
                return i
        return None

    def evento(self, e):
        if self.arranque:
            return False
        if super().evento(e):
            return True
        if self.desliz:
            return False
        if e.type == pygame.MOUSEMOTION:
            nuevo = self._nodo_en(e.pos)
            if nuevo is not None and nuevo != self.hover:
                sonidos.tocar("hover")
            self.hover = nuevo
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            i = self._nodo_en(e.pos)
            if i is not None:
                if self.app.progreso.desbloqueado(self.mundo.id, i):
                    self.arrancar(i)
                else:
                    sonidos.tocar("mal", 0.5)
                    self.gato.reaccionar("triste", 0.8)
                return True
        return False

    def arrancar(self, i):
        """El gato salta al nivel, gira y suena la fanfarria; después arranca."""
        nx, ny = self.nodos[i]
        if self.gato_nodo is not None:
            gx, gy = self.nodos[self.gato_nodo]
            desde = (gx - 58, gy + 30)
        else:
            desde = (nx - 58, ny + 30)
        self.arranque = dict(t=0.0, i=i, desde=desde, hasta=(nx, ny - 22), festejo=False, listo=False)
        self.hover = None
        sonidos.tocar("salto")
        sonidos.tocar("inicio")
        sonidos.agachar(1.8)
        self.gato.reaccionar("feliz", 3, saltar=False)

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.gato.actualizar(dt)
        self.fx.actualizar(dt)
        a = self.arranque
        if a:
            a["t"] += dt
            if a["t"] >= 0.42 and not a["festejo"]:
                a["festejo"] = True
                nx, ny = self.nodos[a["i"]]
                self.fx.confeti(nx, ny - 30, 50, 1.1)
                self.fx.chispas(nx, ny, 20, ui.SOL, 320)
                nivel = self.mundo.niveles[a["i"]]
                rotulo = "¡Jefe!" if nivel.jefe else f"¡Nivel {a['i'] + 1}!"
                self.fx.texto(nx, ny - 150, rotulo, SOL, 46, sube=30, dur=1.1)
                self.gato.reaccionar("festejo", 3)
            if a["t"] >= 1.3 and not a["listo"]:
                a["listo"] = True
                self.app.cambiar(Juego(self.app, self.mundo.id, a["i"]), "ola")
        if self.desliz:
            self.desliz[0] += dt / 0.5
            if self.desliz[0] >= 1:
                self.desliz = None

    def _tooltip(self, sup, i):
        m = self.mundo
        nivel = m.niveles[i]
        nx, ny = self.nodos[i]
        abierto = self.app.progreso.desbloqueado(m.id, i)
        w = 330
        titulo = ui.texto(nivel.nombre, 22, TINTA, negrita=True)
        desc = ui.rico(nivel.descripcion, 16, SUAVE, ancho=w - 30)
        etiquetas = ["Opciones" if nivel.modo == "opciones" else "Tipeo"]
        if nivel.tiempo:
            etiquetas.append(f"{int(nivel.tiempo)} s")
        if nivel.jefe:
            etiquetas.append("JEFE")
        pie = "¡Clic para jugar!" if abierto else "Pasá el nivel anterior para abrirlo"
        h = 26 + titulo.get_height() + desc.get_height() + 60
        rect = pygame.Rect(0, 0, w, h)
        rect.midbottom = (nx, ny - 54)
        if rect.top < 160:
            rect.midtop = (nx, ny + 66)
        rect.clamp_ip(pygame.Rect(10, 10, ANCHO - 20, ALTO - 20))
        ui.globo(sup, rect, (nx, ny - 34 if rect.bottom < ny else ny + 40), TARJETA)
        y = rect.top + 12
        sup.blit(titulo, (rect.left + 16, y))
        y += titulo.get_height() + 4
        sup.blit(desc, (rect.left + 16, y))
        y += desc.get_height() + 8
        x = rect.left + 16
        for et in etiquetas:
            t = ui.texto(et, 14, TINTA if et != "JEFE" else CREMA, negrita=True)
            r = pygame.Rect(x, y, t.get_width() + 16, 22)
            pygame.draw.rect(sup, CORAL if et == "JEFE" else ARENA, r, border_radius=11)
            sup.blit(t, t.get_rect(center=r.center))
            x += r.width + 6
        pie_s = ui.texto(pie, 15, ui.CORAL_OSC if abierto else SUAVE, negrita=True)
        sup.blit(pie_s, (rect.left + 16, y + 28))

    def dibujar(self, sup):
        self.cielo.dibujar(sup)
        self.mar.dibujar(sup)
        if self.desliz:
            k = suave(self.desliz[0])
            d = self.desliz[1]
            sup.blit(self._capa(self.desliz[2]), (-d * ANCHO * k, 0))
            sup.blit(self._capa(self.sel), (d * ANCHO * (1 - k), 0))
        else:
            sup.blit(self._capa(self.sel), (0, 0))
            m = self.mundo
            a = self.arranque
            if a:
                nx, ny = self.nodos[a["i"]]
                r = 44 + 10 * abs(math.sin(a["t"] * 9))
                pygame.draw.circle(sup, SOL, (nx, ny), r, 6)
                k = suave(min(1.0, a["t"] / 0.42))
                x = a["desde"][0] + (a["hasta"][0] - a["desde"][0]) * k
                y = a["desde"][1] + (a["hasta"][1] - a["desde"][1]) * k - math.sin(k * math.pi) * 120
                giro = 360 * suave((a["t"] - 0.5) / 0.45) if a["t"] > 0.5 else 0
                self.gato.dibujar(sup, (x, y), angulo=-giro)
            elif self.gato_nodo is not None:
                # anillo que late en el nivel actual
                nx, ny = self.nodos[self.gato_nodo]
                r = (40 if m.niveles[self.gato_nodo].jefe else 32) + 6 + 4 * math.sin(self.t * 4)
                pygame.draw.circle(sup, CREMA, (nx, ny), r, 4)
                self.gato.dibujar(sup, (nx - 58, ny + 30))
            if self.hover is not None:
                nx, ny = self.nodos[self.hover]
                pygame.draw.circle(sup, (255, 255, 255), (nx, ny), 44, 3)
        # cartel del mundo
        m = self.mundo
        tengo, total = self.app.progreso.estrellas_mundo(m.id)
        rect = pygame.Rect(ANCHO // 2 - 290, 86, 580, 80)
        ui.tabla_madera(sup, rect)
        t1 = ui.texto_borde(m.nombre.upper(), 17, SOL, MADERA_OSC, 2)
        t2 = ui.texto_borde(m.tema, 30, CREMA, MADERA_OSC, 3)
        sup.blit(t1, t1.get_rect(midtop=(rect.centerx, rect.top + 8)))
        sup.blit(t2, t2.get_rect(midtop=(rect.centerx, rect.top + 28)))
        ui.estrella(sup, (rect.right - 70, rect.centery), 13, SOL, BORDE)
        st = ui.texto_borde(f"{tengo}/{total}", 17, CREMA, MADERA_OSC, 2)
        sup.blit(st, st.get_rect(midleft=(rect.right - 52, rect.centery)))
        self.dibujar_botones(sup)
        for b in self.botones:
            if getattr(b, "ficha", None) == self.sel:
                pygame.draw.rect(sup, CREMA, b.rect.inflate(10, 12).move(0, 2), 3, border_radius=16)
        if self.hover is not None and not self.desliz and not self.arranque:
            self._tooltip(sup, self.hover)
        self.fx.dibujar(sup)


# =============================================================== JUEGO

TECLADO = [("x²", "^2", 0), ("^", "^", 0), ("()", "()", 1), ("sen", "sen()", 1), ("cos", "cos()", 1),
           ("e^", "e^()", 1), ("ln", "ln()", 1), ("√", "raiz()", 1), ("/", "/", 0), ("·", "*", 0)]

PIE_GATO = (96, ALTO - 8)
BOCA_GATO = (150, ALTO - 120)
X_GLOBO = 196


class Juego(Escena):
    musica = "estudio"

    def __init__(self, app, mundo_id, nivel_idx, practica=None):
        super().__init__(app)
        self.practica = practica is not None
        self.repasos = set()
        if self.practica:
            self.mundo = None
            self.nivel = None
            self.ejercicios = [generar(c["mundo"], c["nivel"], c["gen"], c["semilla"]) for c in practica]
            self.vidas_max = 5
            self.titulo = "Repaso del cuaderno"
            self.color = ui.ROSA
        else:
            self.mundo = mundo_por_id(mundo_id)
            self.nivel = self.mundo.niveles[nivel_idx]
            self.nivel_idx = nivel_idx
            self.ejercicios = generar_nivel(mundo_id, nivel_idx)
            self._meter_repaso()
            self.vidas_max = self.nivel.vidas
            self.titulo = f"{self.mundo.nombre} · {self.nivel.nombre}"
            self.color = self.mundo.color
        self.vidas = self.vidas_max
        self.i = 0
        self.puntos = 0
        self.puntos_vistos = 0.0
        self.racha = 0
        self.errores = 0
        self.pistas_usadas = 0
        self.resultados = []
        self.al_cuaderno = 0
        self.sacados = 0
        self.fx = Efectos()
        self.fuego = Fueguito()
        self.gato = Gato(128)
        self.gato.reaccionar("feliz", 1.0)
        self.charla = random.choice(FRASES_INICIO)
        self.t_charla = 3.5
        self.sacudir = 0
        self.t = 0.0
        self.t_entrada = 0.0
        self.t_moneda = 1.0
        self.t_corazon = 10.0
        self.ultimo_tic = None
        self.campo = CampoTexto((0, 0, 560, 58), al_enter=self.comprobar, al_cambiar=self._previsualizar)
        pygame.key.start_text_input()
        self.empezar_ejercicio()

    @property
    def permite_m(self):
        return not (self.estado == "pregunta" and self.paso.tipo == "expresion")

    # ---------------------------------------------- armado
    def _meter_repaso(self):
        """Mete un ejercicio del cuaderno de errores entre los del nivel."""
        cuaderno = self.app.progreso.cuaderno
        orden = [m.id for m in MUNDOS]
        hasta = orden.index(self.mundo.id)
        candidatos = [c for c in cuaderno if c["clave"]["mundo"] in orden and orden.index(c["clave"]["mundo"]) <= hasta]
        if candidatos and random.random() < 0.7:
            c = random.choice(candidatos)["clave"]
            try:
                ej = generar(c["mundo"], c["nivel"], c["gen"], c["semilla"])
            except Exception:
                return
            pos = random.randint(1, len(self.ejercicios))
            self.ejercicios.insert(pos, ej)
            self.repasos.add(pos)

    @property
    def jefe(self):
        return bool(self.nivel and self.nivel.jefe)

    @property
    def tiempo(self):
        return self.nivel.tiempo if self.nivel else None

    def empezar_ejercicio(self):
        self.ej = self.ejercicios[self.i]
        self.paso_i = 0
        self.fallo_ej = False
        self.pasos_revelados = set()
        self.t_entrada = 0.0
        self.empezar_paso()

    def empezar_paso(self):
        self.paso = self.ej.pasos[self.paso_i]
        self.intentos = 0
        self.pistas_vistas = 0
        self.feedback = None
        self.estado = "pregunta"     # pregunta | bien | revelado | sin_vidas
        self.marcadas = {}
        self.t_marcas = {}
        self.t_paso = 0
        self.auto_t = None
        self.preview = None
        self.ultimo_tic = None
        self.campo.poner("")
        self.armar()

    def _respuesta_tex(self):
        p = self.paso
        if p.esperado is not None:
            return f"${p.prefijo} {p.mostrar or tex(p.esperado)}$"
        for o in p.opciones:
            if o.correcta:
                return f"${o.tex}$" if o.tex else f"**{o.texto}**"
        return ""

    def _teclado(self):
        teclas = list(TECLADO)
        extra = []
        if VAR_Y in self.paso.variables:
            extra.append(("y", "y", 0))
        if VAR_Z in self.paso.variables:
            extra.append(("z", "z", 0))
        if self.paso.chequeo == "primitiva":
            extra.append(("+C", "+C", 0))
        if self.paso.chequeo == "numero":
            extra = [("π", "pi", 0), ("e", "e", 0)]
            teclas = [t for t in teclas if t[0] not in ("sen", "cos", "e^", "ln")]
        return teclas + extra

    def armar(self):
        """Calcula la ubicación de todo según el estado actual."""
        self.botones = [Boton((14, 10, 108, 44), "Salir", self.atras, DURAZNO, tam=19, relieve=4),
                        self.boton_opciones((130, 10, 48, 44))]
        self.capas = []
        if self.ej.grafico:
            self.cx, self.ancho = 480, 860
            g = ui.grafico(self.ej.grafico)
            self.capas.append((g, g.get_rect(topright=(ANCHO - 24, 108))))
        else:
            self.cx, self.ancho = ANCHO // 2, 1100
        cx, ancho = self.cx, self.ancho
        y = 108
        consigna = self.ej.consigna
        if self.i in self.repasos or self.practica:
            consigna = "**Repaso del cuaderno** · " + consigna
        s = ui.rico(consigna, 20, SUAVE, ancho=ancho, color_negrita=ui.CORAL_OSC)
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 4
        f = ui.formula(self.ej.formula, 46)
        s = ui.escalar_a(f.sup, ancho)
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 14
        for k in range(self.paso_i):
            p = self.ej.pasos[k]
            mal = k in self.pasos_revelados
            s = ui.escalar_a(ui.rico(p.resumen, 20, ROSA_OSC if mal else MENTA_OSC, ancho=ancho - 100), ancho - 60)
            r = s.get_rect(midtop=(cx + 16, y))
            self.capas.append((s, r))
            self.capas.append(("cruz" if mal else "tilde", (r.left - 20, r.centery)))
            y += s.get_height() + 6
        if self.paso_i:
            y += 6
        n_pasos = len(self.ej.pasos)
        pregunta = self.paso.pregunta
        if n_pasos > 1:
            pregunta = f"**Paso {self.paso_i + 1} de {n_pasos}.** " + pregunta
        s = ui.rico(pregunta, 24, TINTA, ancho=ancho, color_negrita=LAVANDA_OSC)
        self.capas.append((s, s.get_rect(midtop=(cx, y))))
        y += s.get_height() + 16

        respondiendo = self.estado == "pregunta"
        hay_pista = self.paso.pistas and not self.jefe and self.pistas_vistas < len(self.paso.pistas)
        if self.paso.tipo == "expresion":
            pre = ui.escalar_a(ui.formula(ui.fracciones_grandes(self.paso.prefijo), 30).sup, 380) \
                if self.paso.prefijo else None
            ancho_campo = min(560, ancho - 40 - (pre.get_width() + 14 if pre else 0))
            pw = pre.get_width() + 14 if pre else 0
            x0 = cx - (pw + ancho_campo) // 2
            alto_campo = max(58, pre.get_height() + 6) if pre else 58
            if pre:
                self.capas.append((pre, pre.get_rect(midleft=(x0, y + alto_campo // 2))))
            self.campo.rect = pygame.Rect(x0 + pw, y + (alto_campo - 58) // 2, ancho_campo, 58)
            self.campo.habilitado = respondiendo
            y += alto_campo + 8
            self.y_preview = y
            y += 44
            if respondiendo:
                teclas = self._teclado()
                anchos = [max(46, ui.texto(et, 18, TINTA, negrita=True).get_width() + 22) for et, _, _ in teclas]
                total = sum(anchos) + 8 * (len(anchos) - 1)
                x = cx - total // 2
                for (et, ins, ret), w in zip(teclas, anchos):
                    self.botones.append(Boton((x, y, w, 36), et, (lambda a=ins, b=ret: self.campo.insertar(a, b)),
                                              ARENA, tam=18, radio=10, relieve=4, sonido="tecla"))
                    x += w + 8
                y += 52
                fila = []
                if hay_pista:
                    fila.append(("Pista (−5)", self.pista, SOL, TINTA))
                fila.append(("Comprobar  ↵", self.comprobar, CORAL, CREMA))
                total = len(fila) * 230 + (len(fila) - 1) * 18
                x = cx - total // 2
                for txt, acc, col, ct in fila:
                    self.botones.append(Boton((x, y, 230, 52), txt, acc, col, ct, tam=21,
                                              sonido="pista" if acc == self.pista else None))
                    x += 248
                y += 64
        else:
            ops = self.paso.opciones
            con_texto = any(o.texto for o in ops)
            alto = 62 if con_texto else 84
            w = min(540, (ancho - 18) // 2)
            x0 = cx - (2 * w + 18) // 2
            self.rect_opciones = {}
            for k, o in enumerate(ops):
                fila, col = divmod(k, 2)
                rect = pygame.Rect(x0 + col * (w + 18), y + fila * (alto + 16), w, alto)
                contenido = o.texto if o.texto else ui.formula(ui.fracciones_grandes(o.tex), 28).sup
                b = Boton(rect, contenido, (lambda k=k: self.elegir(k)), TARJETA, tam=21,
                          tecla=[pygame.K_1 + k, pygame.K_KP1 + k], habilitado=respondiendo and k not in self.marcadas,
                          etiqueta_tecla=str(k + 1), sonido=None, relieve=6)
                b.marcado = self.marcadas.get(k)
                b.t_marcado = self.t_marcas.get(k, 0) if hasattr(self, "t_marcas") else 0
                self.rect_opciones[k] = rect
                self.botones.append(b)
            y += ((len(ops) + 1) // 2) * (alto + 16)
            if respondiendo and hay_pista:
                self.botones.append(Boton((cx - 115, y, 230, 46), "Pista (−5)", self.pista, SOL, tam=19,
                                          sonido="pista"))
                y += 58
        # globito del gato: feedback, pista o charla
        self.panel = None
        y += 6
        if self.feedback:
            self.panel = self._panel_feedback(y)
        elif self.pistas_vistas:
            cuerpo = "\n".join(self.paso.pistas[:self.pistas_vistas])
            self.panel = self._panel(y, "Pista", cuerpo, (255, 246, 214), SOL_OSC)
        elif self.charla and self.t_charla > 0:
            self.panel = self._panel(max(y, ALTO - 130), self.charla, "", TARJETA, ui.CORAL_OSC)

    def _panel(self, y, titulo, cuerpo, color, color_titulo, con_boton=False):
        ancho = ANCHO - X_GLOBO - 24
        ancho_txt = ancho - 50 - (210 if con_boton else 0)
        t = ui.texto(titulo, 23, color_titulo, negrita=True)
        c = ui.rico(cuerpo, 19, TINTA, ancho=ancho_txt, color_negrita=color_titulo) if cuerpo else None
        alto = 22 + t.get_height() + (c.get_height() + 8 if c else 0) + 14
        alto = max(alto, 86 if con_boton else 0)
        # el globito va abajo, al lado del gato (pero sin tapar el ejercicio)
        rect = pygame.Rect(X_GLOBO, max(y, ALTO - 16 - alto), ancho, alto)
        if rect.bottom > ALTO - 12:
            rect.bottom = ALTO - 12
        if con_boton:
            b = Boton((rect.right - 206, rect.centery - 28, 184, 54), "Continuar  ↵", self.continuar, LAVANDA,
                      tam=20, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE], sonido="paso")
            self.botones.append(b)
        return dict(rect=rect, color=color, titulo=t, cuerpo=c, borde=color_titulo)

    def _panel_feedback(self, y):
        fb = self.feedback
        if fb["tipo"] == "bien":
            return self._panel(y, fb["titulo"], fb["cuerpo"], (232, 248, 222), MENTA_OSC, con_boton=self.auto_t is None)
        if fb["tipo"] == "info":
            return self._panel(y, fb["titulo"], fb["cuerpo"], TARJETA, SUAVE)
        return self._panel(y, fb["titulo"], fb["cuerpo"], (255, 234, 226), ROSA_OSC,
                           con_boton=self.estado in ("revelado", "sin_vidas"))

    # ---------------------------------------------- acciones
    def atras(self):
        if self.practica:
            self.app.cambiar(Cuaderno(self.app))
        else:
            self.app.cambiar(Mapa(self.app, self.mundo.id), "ola")

    def _previsualizar(self, texto):
        if not texto.strip():
            self.preview = None
            return
        try:
            self.preview = ("ok", tex(self._parsear(texto)))
        except ErrorEntrada as ex:
            self.preview = ("err", str(ex))
        except Exception:
            self.preview = ("err", "No entiendo la fórmula.")
        if self.feedback and self.feedback["tipo"] == "info":
            self.feedback = None
            self.armar()

    def pista(self):
        if self.pistas_vistas < len(self.paso.pistas):
            self.pistas_vistas += 1
            self.pistas_usadas += 1
            self.puntos = max(0, self.puntos - 5)
            self.gato.reaccionar("pensando", 2.5, saltar=False)
            if self.feedback and self.feedback["tipo"] != "bien":
                self.feedback = None
            self.armar()

    def _parsear(self, texto):
        return parsear(texto, self.paso.variables, permitir_c=self.paso.chequeo == "primitiva")

    def comprobar(self):
        if self.estado != "pregunta" or self.paso.tipo != "expresion":
            return
        try:
            r = self._parsear(self.campo.texto)
        except ErrorEntrada as ex:
            self.feedback = dict(tipo="info", titulo="Mmm, no entiendo lo que escribiste",
                                 cuerpo=f"{ex} (Esto no te saca vidas. En el menú está la ayuda para escribir fórmulas.)")
            self.gato.reaccionar("sorpresa", 1.2, saltar=False)
            sonidos.tocar("tic")
            self.armar()
            return
        p = self.paso
        if p.chequeo == "primitiva":
            if es_primitiva(r, p.integrando, p.var or p.variables[0]):
                nota = ""
                if not r.has(C) and p.prefijo.startswith("\\int"):
                    nota = "Ojo: en el parcial no te olvides del $+\\,C$."
                self.acierto(nota)
            else:
                _, titulo, cuerpo = diagnosticar_primitiva(r, p.integrando, p.var or p.variables[0], p.errores)
                self.fallo(titulo, cuerpo)
            return
        if equivalentes(r, p.esperado):
            self.acierto()
        elif p.chequeo == "numero" and casi_igual(r, p.esperado):
            self.acierto(f"Está bien, pero en el parcial dejalo exacto: ${tex(p.esperado)}$.")
        else:
            _, titulo, cuerpo = diagnosticar(r, p.esperado, p.errores, p.original)
            self.fallo(titulo, cuerpo)

    def elegir(self, k):
        if self.estado != "pregunta":
            return
        o = self.paso.opciones[k]
        self.t_marcas = getattr(self, "t_marcas", {})
        self.t_marcas[k] = pygame.time.get_ticks() / 1000
        if o.correcta:
            self.marcadas[k] = "bien"
            self.acierto(origen=self.rect_opciones[k].center)
        else:
            self.marcadas[k] = "mal"
            titulo, cuerpo = ERRORES.get(o.error, ("Todavía no", "Esa no es."))
            self.fallo(titulo, cuerpo)

    def _origen(self):
        if self.paso.tipo == "expresion":
            return self.campo.rect.center
        return (self.cx, 400)

    def acierto(self, nota="", origen=None):
        self.racha += 1
        pts = 10 + 2 * min(self.racha - 1, 5)
        if self.tiempo:
            pts += max(0, int(self.tiempo - self.t_paso))
        self.puntos += pts
        self.estado = "bien"
        self.charla = None
        cuerpo = self.paso.explicacion
        if self.paso.tipo == "expresion" and self.paso.mostrar:
            cuerpo = f"${self.paso.prefijo} {self.paso.mostrar}$\n{cuerpo}"
        if nota:
            cuerpo = f"**{nota}**\n{cuerpo}" if cuerpo else f"**{nota}**"
        self.feedback = dict(tipo="bien", titulo=f"{random.choice(FRASES_BIEN)}   +{pts}", cuerpo=cuerpo)
        if (not self.paso.explicacion and not nota) or self.tiempo:
            self.auto_t = 0.9 if not self.tiempo else 1.6
        self.t_marcas = getattr(self, "t_marcas", {})
        for k, o in enumerate(self.paso.opciones):
            if o.correcta:
                self.marcadas[k] = "bien"
                self.t_marcas.setdefault(k, pygame.time.get_ticks() / 1000)
        # festejo
        ox, oy = origen or self._origen()
        self.fx.confeti(ox, oy, 34 + min(self.racha, 8) * 4, 1.0)
        self.fx.texto(ox, oy - 30, f"+{pts}", ui.SOL, 34)
        for k in range(min(5, 1 + pts // 8)):
            self.fx.volar((ox, oy), self.pos_monedas, self._llego_moneda, dur=0.6, demora=k * 0.08)
        if self.racha >= 3:
            sonidos.tocar("bien_racha")
        else:
            sonidos.tocar("bien")
        if self.racha in (3, 5, 8, 12, 20):
            self.fx.texto(ANCHO // 2, 300, f"¡Racha ×{self.racha}!", ui.CORAL, 52, sube=80, dur=1.4)
            sonidos.tocar("fuego")
            self.gato.reaccionar("festejo", 1.4)
        else:
            self.gato.reaccionar("feliz", 1.2)
        self.armar()

    def _llego_moneda(self):
        self.t_moneda = 0.0
        sonidos.tocar("moneda", 0.5, variar=True)

    def fallo(self, titulo, cuerpo, sin_reintento=False):
        self.vidas -= 1
        self.t_corazon = 0.0
        self.racha = 0
        self.errores += 1
        self.intentos += 1
        self.fallo_ej = True
        self.sacudir = 0.4
        self.charla = None
        self.app.sacudir(7)
        sonidos.tocar("mal")
        self.gato.reaccionar("triste", 1.8)
        titulo = f"{random.choice(FRASES_MAL)} {titulo}"
        if self.vidas <= 0 or sin_reintento or self.intentos >= self.paso.max_intentos:
            self.estado = "sin_vidas" if self.vidas <= 0 else "revelado"
            self.pasos_revelados.add(self.paso_i)
            self.t_marcas = getattr(self, "t_marcas", {})
            for k, o in enumerate(self.paso.opciones):
                if o.correcta:
                    self.marcadas[k] = "bien"
            extra = f"La respuesta era:  {self._respuesta_tex()}"
            if self.paso.explicacion:
                extra += "\n" + self.paso.explicacion
            self.feedback = dict(tipo="mal", titulo=titulo, cuerpo="\n".join(t for t in (cuerpo, extra) if t))
        else:
            self.feedback = dict(tipo="mal", titulo=titulo, cuerpo=cuerpo + "  **¡Probá de nuevo!**")
        self.armar()

    def continuar(self):
        if self.estado == "sin_vidas":
            if self.fallo_ej:
                self.app.progreso.anotar_error(self.ej.clave, self.ej.formula)
                self.al_cuaderno += 1
            self.app.cambiar(FinNivel(self.app, self, gano=False))
            return
        if self.estado not in ("bien", "revelado"):
            return
        self.paso_i += 1
        if self.paso_i < len(self.ej.pasos):
            self.empezar_paso()
        else:
            self.terminar_ejercicio()

    def terminar_ejercicio(self):
        prog = self.app.progreso
        if self.fallo_ej:
            prog.anotar_error(self.ej.clave, self.ej.formula)
            self.al_cuaderno += 1
            self.resultados.append("mal")
        else:
            if prog.en_cuaderno(self.ej.clave) and prog.anotar_acierto(self.ej.clave):
                self.sacados += 1
            self.resultados.append("bien")
        self.i += 1
        if self.i >= len(self.ejercicios):
            self.terminar_nivel()
        else:
            self.empezar_ejercicio()

    def terminar_nivel(self):
        faltas = self.errores + self.pistas_usadas
        estrellas = 3 if faltas == 0 else (2 if faltas <= 2 else 1)
        nuevo_mundo = None
        if not self.practica:
            prog = self.app.progreso
            orden = [m.id for m in MUNDOS]
            pos = orden.index(self.mundo.id)
            era_ultimo = self.nivel_idx == len(self.mundo.niveles) - 1
            ya = prog.aprobado(self.mundo.id, self.nivel_idx)
            prog.registrar(self.mundo.id, self.nivel_idx, estrellas, self.puntos)
            if era_ultimo and not ya and pos + 1 < len(MUNDOS):
                nuevo_mundo = MUNDOS[pos + 1]
        self.app.cambiar(FinNivel(self.app, self, gano=True, estrellas=estrellas, nuevo_mundo=nuevo_mundo))

    # ---------------------------------------------- loop
    @property
    def pos_monedas(self):
        return (ANCHO - 230, 32)

    def evento(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.atras()
            return True
        if self.estado == "pregunta" and self.paso.tipo == "expresion":
            if e.type == pygame.MOUSEBUTTONDOWN and not self.campo.rect.collidepoint(e.pos):
                pass
            elif self.campo.evento(e):
                return True
        if self.estado == "bien" and self.auto_t is not None and e.type == pygame.KEYDOWN and \
                e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            self.continuar()
            return True
        for b in list(self.botones):
            if b.evento(e):
                return True
        return False

    def actualizar(self, dt):
        self.t += dt
        self.t_entrada += dt
        self.t_moneda += dt
        self.t_corazon += dt
        self.campo.actualizar(dt)
        self.sacudir = max(0, self.sacudir - dt)
        self.fx.actualizar(dt)
        self.fuego.actualizar(dt, min(1.0, self.racha / 8))
        self.gato.actualizar(dt)
        self.puntos_vistos += (self.puntos - self.puntos_vistos) * min(1, dt * 6)
        if self.t_charla > 0:
            self.t_charla -= dt
            if self.t_charla <= 0 and not self.feedback:
                self.charla = None
                self.armar()
        if self.estado == "pregunta" and self.tiempo:
            self.t_paso += dt
            quedan = int(self.tiempo - self.t_paso)
            if quedan < 3 and quedan != self.ultimo_tic:
                self.ultimo_tic = quedan
                sonidos.tocar("tic")
            if self.t_paso >= self.tiempo:
                self.fallo("¡Se acabó el tiempo!", "", sin_reintento=True)
        if self.auto_t is not None and self.estado == "bien":
            self.auto_t -= dt
            if self.auto_t <= 0:
                self.auto_t = None
                self.continuar()

    def _dibujar_encabezado(self, sup):
        r = pygame.Rect(-10, -10, ANCHO + 20, 74)
        ui.tabla_madera(sup, r, radio=0)
        t = ui.texto_borde(self.titulo, 24, CREMA, MADERA_OSC, 2)
        sup.blit(t, (192, 32 - t.get_height() // 2))
        x = 192 + t.get_width() + 12
        if self.jefe:
            et = ui.texto_borde("JEFE", 16, CREMA, ui.CORAL_OSC, 2)
            rr = pygame.Rect(x, 18, et.get_width() + 18, 28)
            pygame.draw.rect(sup, CORAL, rr, border_radius=14)
            pygame.draw.rect(sup, BORDE, rr, 2, border_radius=14)
            sup.blit(et, et.get_rect(center=rr.center))
        # vidas
        x = ANCHO - 34
        for k in range(self.vidas_max - 1, -1, -1):
            if k < self.vidas:
                ui.corazon(sup, (x, 30), 28, CORAL)
            else:
                ui.corazon(sup, (x, 30), 28, GRIS, brillo=False)
                if k == self.vidas and self.t_corazon < 0.6:
                    kk = self.t_corazon / 0.6
                    tam = 28 * (1 + kk * 1.2)
                    cap = pygame.Surface((80, 80), pygame.SRCALPHA)
                    ui.corazon(cap, (40, 40), tam, CORAL)
                    cap.set_alpha(int(255 * (1 - kk)))
                    sup.blit(cap, (x - 40, 30 - 40 - kk * 20))
            x -= 38
        # monedas
        mx, my = self.pos_monedas
        bump = 1 + 0.35 * max(0.0, 1 - self.t_moneda / 0.25)
        ui.moneda(sup, (mx, my), 14 * bump)
        pts = ui.texto_borde(str(int(round(self.puntos_vistos))), 24, CREMA, MADERA_OSC, 2)
        sup.blit(pts, pts.get_rect(midleft=(mx + 22, my)))
        # racha con fuego
        if self.racha >= 2:
            fx = mx - 70
            escala = 0.8 + min(self.racha, 10) * 0.08
            self.fuego.dibujar(sup, (fx, 44), escala)
            rt = ui.texto_borde(f"×{self.racha}", 20, SOL, MADERA_OSC, 2)
            sup.blit(rt, rt.get_rect(midleft=(fx + 14, 34)))
        # soga con el progreso
        n = len(self.ejercicios)
        sep = min(30, 600 // max(1, n))
        x0 = ANCHO // 2 - (n - 1) * sep // 2
        pygame.draw.line(sup, MADERA, (x0 - 14, 86), (x0 + (n - 1) * sep + 14, 86), 3)
        for k in range(n):
            c = (x0 + k * sep, 86)
            if k < len(self.resultados):
                bien = self.resultados[k] == "bien"
                pygame.draw.circle(sup, BORDE, c, 10)
                pygame.draw.circle(sup, ui.PASTO if bien else CORAL, c, 8)
            elif k == self.i:
                rr = 10 + 2 * math.sin(self.t * 5)
                pygame.draw.circle(sup, BORDE, c, rr + 2)
                pygame.draw.circle(sup, SOL, c, rr)
            else:
                pygame.draw.circle(sup, ARENA_OSC, c, 7)
                pygame.draw.circle(sup, ARENA, c, 5)
        if self.tiempo:
            restante = max(0.0, 1 - min(self.t_paso, self.tiempo) / self.tiempo)
            rr = pygame.Rect(ANCHO // 2 - 220, 100, 440, 10)
            pygame.draw.rect(sup, BORDE, rr.inflate(4, 4), border_radius=6)
            pygame.draw.rect(sup, (240, 228, 204), rr, border_radius=5)
            col = ui.PASTO if restante > 0.5 else (SOL if restante > 0.25 else CORAL)
            pygame.draw.rect(sup, col, (rr.left, rr.top, int(rr.width * restante), rr.height), border_radius=5)

    def dibujar(self, sup):
        sup.blit(paisaje.pergamino(), (0, 0))
        k = suave(self.t_entrada / 0.35)
        dx = int((1 - k) * 90)
        for s, r in self.capas:
            if s == "tilde":
                ui.tilde(sup, (r[0] + dx, r[1]), 18, MENTA_OSC, 3)
            elif s == "cruz":
                ui.cruz(sup, (r[0] + dx, r[1]), 18, ROSA_OSC, 3)
            else:
                if k < 1:
                    s = s.copy()
                    s.set_alpha(int(255 * k))
                sup.blit(s, r.move(dx, 0))
        if self.paso.tipo == "expresion":
            temblor = int(math.sin(self.sacudir * 50) * 9 * (self.sacudir / 0.4)) if self.sacudir else 0
            orig = self.campo.rect
            self.campo.rect = orig.move(temblor + dx, 0)
            self.campo.dibujar(sup)
            self.campo.rect = orig
            if self.preview and self.estado == "pregunta":
                if self.preview[0] == "ok":
                    et = ui.texto("Leo:", 18, SUAVE, negrita=True)
                    fm = ui.escalar_a(ui.formula(self.preview[1], 26, LAVANDA_OSC).sup, 900)
                    w = et.get_width() + 12 + fm.get_width()
                    x = self.cx - w // 2
                    cy = self.y_preview + 18
                    sup.blit(et, (x, cy - et.get_height() // 2))
                    sup.blit(fm, (x + et.get_width() + 12, cy - fm.get_height() // 2))
                else:
                    centrar(sup, ui.texto(self.preview[1], 18, SUAVE), self.y_preview + 6, self.cx)
        for b in self.botones:
            b.dibujar(sup, dx if b.rect.top > 90 else 0)
        # el gato y su globito
        self.gato.dibujar(sup, PIE_GATO)
        if self.panel:
            p = self.panel
            ui.globo(sup, p["rect"], BOCA_GATO, p["color"], p["borde"], 3)
            sup.blit(p["titulo"], (p["rect"].left + 22, p["rect"].top + 14))
            if p["cuerpo"]:
                sup.blit(p["cuerpo"], (p["rect"].left + 22, p["rect"].top + 22 + p["titulo"].get_height()))
            for b in self.botones:
                if b.rect.colliderect(p["rect"]) and b.rect.top > p["rect"].top:
                    b.dibujar(sup)
        self._dibujar_encabezado(sup)
        self.botones[0].dibujar(sup)
        self.botones[1].dibujar(sup)
        self.fx.dibujar(sup)


# =============================================================== FIN DE NIVEL

class FinNivel(Escena):
    def __init__(self, app, juego, gano, estrellas=0, nuevo_mundo=None):
        super().__init__(app)
        self.j = juego
        self.gano = gano
        self.estrellas = estrellas
        self.nuevo_mundo = nuevo_mundo
        self.t = 0.0
        self.cielo = paisaje.Cielo(semilla=6)
        self.mar = paisaje.Mar(520)
        self.fx = Efectos()
        self.gato = Gato(170)
        self.estrellas_hechas = 0
        self.puntos_vistos = 0
        self.ultimo_tic = 0
        app.progreso.sumar_monedas(juego.puntos)
        sonidos.agachar(2.5)
        if gano:
            self.gato.reaccionar("festejo", 99)
            self.gato.animo_base = "feliz"
            self.fx.lluvia_confeti(ANCHO, 140)
            sonidos.tocar("nivel")
        else:
            self.gato.reaccionar("triste", 99)
            self.gato.animo_base = "triste"
            self.fx.lluvia(ANCHO, 90)
            sonidos.tocar("perder")
        cx, y = ANCHO // 2 + 120, 594
        b = []
        if juego.practica:
            b.append(("Volver al cuaderno", lambda: app.cambiar(Cuaderno(app)), CORAL, CREMA))
        else:
            m, i = juego.mundo, juego.nivel_idx
            if gano:
                if i + 1 < len(m.niveles):
                    b.append(("Siguiente nivel", lambda: app.cambiar(Juego(app, m.id, i + 1), "ola"), CORAL, CREMA))
                elif nuevo_mundo:
                    b.append((f"Ir al {nuevo_mundo.nombre}", lambda: app.cambiar(Mapa(app, nuevo_mundo.id), "ola"),
                              CORAL, CREMA))
                b.append(("Repetir", lambda: app.cambiar(Juego(app, m.id, i), "ola"), LAVANDA, TINTA))
            else:
                b.append(("Reintentar", lambda: app.cambiar(Juego(app, m.id, i), "ola"), CORAL, CREMA))
            b.append(("Mapa", lambda: app.cambiar(Mapa(app, m.id), "ola"), ARENA, TINTA))
        total = len(b) * 230 + (len(b) - 1) * 18
        x = cx - total // 2
        for k, (txt, acc, col, ct) in enumerate(b):
            teclas = [pygame.K_RETURN, pygame.K_KP_ENTER] if k == 0 else None
            self.botones.append(Boton((x, y, 230, 62), txt, acc, col, ct, tam=22, tecla=teclas))
            x += 248

    def atras(self):
        if self.j.practica:
            self.app.cambiar(Cuaderno(self.app))
        else:
            self.app.cambiar(Mapa(self.app, self.j.mundo.id), "ola")

    def _pos_estrella(self, k):
        return (ANCHO // 2 + 120 + (k - 1) * 110, 200 - (16 if k == 1 else 0))

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.fx.actualizar(dt)
        self.gato.actualizar(dt)
        if self.gano and not self.j.practica:
            while self.estrellas_hechas < self.estrellas and self.t > 0.6 + self.estrellas_hechas * 0.45:
                x, y = self._pos_estrella(self.estrellas_hechas)
                self.fx.chispas(x, y, 22, ui.SOL, 300)
                self.fx.confeti(x, y, 25, 0.8)
                sonidos.tocar("estrella")
                self.estrellas_hechas += 1
            if self.nuevo_mundo and self.t > 2.2 and not getattr(self, "_desbloqueo_sonado", False):
                self._desbloqueo_sonado = True
                sonidos.tocar("desbloqueo")
        meta = self.j.puntos
        if self.t > 0.4 and self.puntos_vistos < meta:
            self.puntos_vistos = min(meta, self.puntos_vistos + max(1, meta * dt / 1.2))
            if int(self.puntos_vistos) // 15 != self.ultimo_tic:
                self.ultimo_tic = int(self.puntos_vistos) // 15
                sonidos.tocar("tic", 0.4)

    def dibujar(self, sup):
        self.cielo.dibujar(sup)
        if not self.gano:
            gris = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            gris.fill((60, 70, 90, 70))
            sup.blit(gris, (0, 0))
        self.mar.dibujar(sup)
        paisaje.dibujar_isla(sup, (-20, 545), 400, 190, ui.PASTO, semilla=12, palmeras=1)
        self.gato.dibujar(sup, (170, 680))
        # pergamino central
        j = self.j
        card = pygame.Rect(ANCHO // 2 - 240, 40, 720, 530)
        ui.tarjeta(sup, card, ui.PERGAMINO, 26, ui.ARENA_OSC, 8)
        if self.gano:
            titulo = "¡Repaso terminado!" if j.practica else "¡Nivel superado!"
            t = ui.texto_borde(titulo, 50, SOL, BORDE, 4)
        else:
            t = ui.texto_borde("Te quedaste sin vidas", 44, CORAL, BORDE, 4)
        esc = rebote(min(1, self.t / 0.5))
        t2 = pygame.transform.smoothscale(t, (max(1, int(t.get_width() * esc)), max(1, int(t.get_height() * esc))))
        sup.blit(t2, t2.get_rect(center=(card.centerx, card.top + 64)))
        y = card.top + 110
        if self.gano and not j.practica:
            for k in range(3):
                c = self._pos_estrella(k)
                ui.estrella(sup, c, 44, (236, 226, 204), (200, 184, 160), brillo=False)
                if k < self.estrellas_hechas:
                    edad = self.t - (0.6 + k * 0.45)
                    r = 44 * rebote(min(1, edad / 0.35))
                    ui.estrella(sup, c, r, SOL, BORDE)
            y += 140
            frase = {3: "¡Perfecto! Ni un error ni una pista.", 2: "¡Muy bien! Casi perfecto.",
                     1: "Aprobado. Repetilo para sacar las 3 estrellas."}[self.estrellas]
            centrar(sup, ui.texto(frase, 22, SUAVE, negrita=True), y, card.centerx)
            y += 44
        elif not self.gano:
            centrar(sup, ui.rico("No pasa nada: **así se aprende**. Mirá bien la explicación del error y volvé a intentarlo.",
                                 21, SUAVE, ancho=600, centrado=True, color_negrita=ui.CORAL_OSC), y + 10, card.centerx)
            y += 100
        bien = sum(1 for r in j.resultados if r == "bien")
        datos = [("Monedas", str(int(self.puntos_vistos))), ("Sin errores", f"{bien} de {len(j.ejercicios)}"),
                 ("Errores", str(j.errores)), ("Pistas", str(j.pistas_usadas))]
        for k, (a, b) in enumerate(datos):
            col, fila = k % 2, k // 2
            x = card.centerx - 260 + col * 290
            caja = pygame.Rect(x, y + fila * 70, 250, 60)
            pygame.draw.rect(sup, (250, 236, 206), caja, border_radius=14)
            pygame.draw.rect(sup, ui.ARENA_OSC, caja, 2, border_radius=14)
            sup.blit(ui.texto(a, 16, SUAVE, negrita=True), (caja.left + 14, caja.top + 6))
            sup.blit(ui.texto(b, 24, TINTA, negrita=True), (caja.left + 14, caja.top + 26))
            if a == "Monedas":
                ui.moneda(sup, (caja.right - 26, caja.centery), 14)
        y += 150
        mensajes = []
        if j.puntos:
            mensajes.append(f"Ahora tenés **{self.app.progreso.monedas} monedas** para gastar en la tienda del michi.")
        if self.nuevo_mundo:
            mensajes.append(f"¡Desbloqueaste el **{self.nuevo_mundo.nombre}: {self.nuevo_mundo.tema}**!")
        if j.al_cuaderno:
            mensajes.append(f"{j.al_cuaderno} ejercicio(s) fueron al **cuaderno de errores** para repasar.")
        if j.sacados:
            mensajes.append(f"Sacaste {j.sacados} ejercicio(s) del cuaderno. ¡Ya te salen!")
        for m in mensajes[:2]:
            s = ui.rico(m, 18, TINTA, ancho=660, centrado=True, color_negrita=ui.CORAL_OSC)
            centrar(sup, s, y, card.centerx)
            y += s.get_height() + 2
        self.fx.dibujar(sup)
        self.dibujar_botones(sup)


# =============================================================== CUADERNO

class Cuaderno(Escena):
    MAX = 8

    def __init__(self, app):
        super().__init__(app)
        self.items = list(app.progreso.cuaderno)
        self.gato = Gato(120)
        self.gato.animo_base = "normal" if self.items else "dormido"
        self.gato.animo = self.gato.animo_base
        self.botones = [Boton((24, 22, 128, 50), "Menú", self.atras, DURAZNO, tam=22)]
        if self.items:
            self.botones.append(Boton((ANCHO - 330, 640, 300, 60), f"Practicar ({min(len(self.items), self.MAX)})",
                                      self.practicar, CORAL, CREMA, tam=24, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER]))

    def atras(self):
        self.app.cambiar(Menu(self.app))

    def practicar(self):
        claves = [c["clave"] for c in self.items[:self.MAX]]
        random.shuffle(claves)
        self.app.cambiar(Juego(self.app, None, None, practica=claves), "ola")

    def actualizar(self, dt):
        self.gato.actualizar(dt)

    def dibujar(self, sup):
        sup.blit(paisaje.pergamino(), (0, 0))
        letrero(sup, (ANCHO // 2 - 230, 16, 460, 62), "Cuaderno de errores", 30)
        sup.blit(ui.rico("Los ejercicios en los que te equivocaste. Cada uno sale cuando lo resolvés **2 veces sin errores** "
                         "(acá o cuando te aparece de repaso en un nivel).", 18, SUAVE, ancho=1180, color_negrita=ui.CORAL_OSC),
                 (40, 90))
        if not self.items:
            s = ui.rico("¡Está vacío! Cuando te equivoques en un ejercicio, va a aparecer acá para que lo repases.",
                        24, SUAVE, ancho=700, centrado=True)
            centrar(sup, s, 260)
            self.gato.dibujar(sup, (ANCHO // 2, 520))
        y = 140
        for item in self.items[:self.MAX]:
            r = pygame.Rect(40, y, ANCHO - 80, 50)
            ui.tarjeta(sup, r, TARJETA, 14, ui.ARENA_OSC, 4)
            c = item["clave"]
            try:
                m = mundo_por_id(c["mundo"])
                lugar = f"{m.nombre} · {m.niveles[c['nivel']].nombre}"
            except (KeyError, IndexError):
                lugar = ""
            sup.blit(ui.texto(lugar, 16, SUAVE, negrita=True), (r.left + 18, r.centery - 10))
            f = ui.escalar_a(ui.formula(item["formula"], 24).sup, 620)
            sup.blit(f, f.get_rect(midleft=(r.left + 380, r.centery)))
            for k in range(2):
                ui.estrella(sup, (r.right - 60 + k * 28, r.centery), 11,
                            SOL if k < item["repasos"] else (232, 222, 200), BORDE, brillo=False)
            y += 60
        if len(self.items) > self.MAX:
            sup.blit(ui.texto(f"…y {len(self.items) - self.MAX} más", 18, SUAVE, negrita=True), (40, 660))
        if self.items:
            self.gato.dibujar(sup, (ANCHO - 420, ALTO - 6), 100)
        self.dibujar_botones(sup)


# =============================================================== AYUDA

class Ayuda(Escena):
    FILAS = [
        ("Potencia", "x^3", ["x^3"]),
        ("Multiplicar", "3x   o   3*x", ["3x"]),
        ("Seno y coseno", "sen(x)   cos(x)", ["sen(x)", "cos(x)"]),
        ("Tangente", "tg(x)", ["tg(x)"]),
        ("e a la algo", "e^(2x)", ["e^(2x)"]),
        ("Logaritmo natural", "ln(x)", ["ln(x)"]),
        ("Raíz cuadrada", "raiz(x)", ["raiz(x)"]),
        ("Fracción", "(x+1)/(x^2+1)", ["(x+1)/(x^2+1)"]),
        ("Seno al cuadrado", "sen(x)^2", ["sen(x)^2"]),
        ("Decimales", "0,5x", ["0,5x"]),
        ("Otras variables", "3x^2y + z", ["3x^2y+z"]),
        ("Constante de integración", "x^3/3 + C", ["x^3/3+C"]),
        ("Pi", "8pi/3", ["8pi/3"]),
    ]

    def __init__(self, app):
        super().__init__(app)
        self.botones = [Boton((24, 22, 128, 50), "Menú", self.atras, DURAZNO, tam=22)]
        self.filas = [(nombre, ejemplo, r"\quad ".join(tex(parsear(m, (VAR_X, VAR_Y, VAR_Z), True)) for m in muestras))
                      for nombre, ejemplo, muestras in self.FILAS]
        self.gato = Gato(120)
        self.gato.animo_base = "normal"

    def atras(self):
        self.app.cambiar(Menu(self.app))

    def actualizar(self, dt):
        self.gato.actualizar(dt)

    def dibujar(self, sup):
        sup.blit(paisaje.pergamino(), (0, 0))
        letrero(sup, (ANCHO // 2 - 250, 16, 500, 62), "Cómo escribir fórmulas", 30)
        x1, x2, x3 = 60, 290, 560
        y = 96
        for et, x in [("Para escribir…", x1), ("tipeás", x2), ("y se ve así", x3)]:
            sup.blit(ui.texto(et, 18, SUAVE, negrita=True), (x, y))
        y += 30
        for nombre, ejemplo, vista in self.filas:
            r = pygame.Rect(40, y, 760, 36)
            pygame.draw.rect(sup, TARJETA, r, border_radius=12)
            pygame.draw.rect(sup, ui.ARENA_OSC, r, 2, border_radius=12)
            sup.blit(ui.texto(nombre, 18, TINTA), (x1, y + 8))
            sup.blit(ui.texto(ejemplo, 18, LAVANDA_OSC, mono=True, negrita=True), (x2, y + 8))
            if vista:
                f = ui.escalar_a(ui.formula(vista, 22).sup, 230)
                sup.blit(f, f.get_rect(midleft=(x3, y + 18)))
            y += 40
        consejos = ("**Consejos del gato**\n"
                    "• Usá paréntesis: **e^2x** se lee como $e^2\\cdot x$. Para $e^{2x}$ escribí **e^(2x)**.\n"
                    "• Debajo del cuadro vas a ver «Leo: …» con cómo entendí lo que escribiste.\n"
                    "• No hace falta simplificar: si es la misma función escrita distinto, está bien.\n"
                    "• Si tu teclado escribe â cuando apretás ^, no pasa nada: lo entiendo igual.\n"
                    "• En las integrales podés poner **+ C** o no.\n"
                    "• Equivocarte al tipear **no** te saca vidas.\n"
                    "• Con la tecla **M** prendés o apagás el sonido.")
        cuerpo = ui.rico(consejos, 17, TINTA, ancho=370, color_negrita=ui.CORAL_OSC)
        caja = pygame.Rect(828, 0, 420, cuerpo.get_height() + 36)
        caja.bottom = 560
        ui.globo(sup, caja, (1110, 590), TARJETA)
        sup.blit(cuerpo, (caja.left + 22, caja.top + 18))
        self.gato.dibujar(sup, (1110, ALTO - 12))
        self.dibujar_botones(sup)


# =============================================================== OPCIONES

class Opciones(Escena):
    """Se abre encima de la pantalla en la que estabas (la deja en pausa)."""

    def __init__(self, app, previa):
        super().__init__(app)
        self.previa = previa
        self.musica = getattr(previa, "musica", "isla")
        self.foto = app.lienzo.copy()
        velo = pygame.Surface(self.foto.get_size(), pygame.SRCALPHA)
        velo.fill((40, 30, 40, 140))
        self.foto.blit(velo, (0, 0))
        self.t = 0.0
        p = app.progreso
        self.panel = pygame.Rect(ANCHO // 2 - 300, 96, 600, 540)
        x, y = self.panel.left + 50, self.panel.top + 110
        self.controles = [
            ui.Interruptor((x + 380, y, 110, 40), p.musica, self.poner_musica),
            ui.Deslizador((x + 20, y + 66, 470, 14), p.vol_musica, self.vol_musica),
            ui.Interruptor((x + 380, y + 120, 110, 40), p.sonido, self.poner_efectos),
            ui.Deslizador((x + 20, y + 186, 470, 14), p.vol_efectos, self.vol_efectos),
            ui.Interruptor((x + 380, y + 240, 110, 40), p.pantalla_completa, self.poner_pantalla),
        ]
        self.botones = [Boton((self.panel.centerx - 110, self.panel.bottom - 86, 220, 58), "Listo", self.atras,
                              CORAL, CREMA, tam=24, tecla=[pygame.K_RETURN, pygame.K_KP_ENTER])]
        self._habilitar()

    def _habilitar(self):
        self.controles[1].habilitado = self.app.progreso.musica
        self.controles[3].habilitado = self.app.progreso.sonido

    def poner_musica(self, v):
        self.app.progreso.musica = v
        sonidos.poner_musica(v)
        self.app.progreso.guardar()
        self._habilitar()

    def poner_efectos(self, v):
        self.app.progreso.sonido = v
        sonidos.poner_efectos(v)
        self.app.progreso.guardar()
        self._habilitar()

    def vol_musica(self, v):
        self.app.progreso.vol_musica = v
        sonidos.poner_volumenes(musica=v)
        self.app.progreso.guardar()

    def vol_efectos(self, v):
        self.app.progreso.vol_efectos = v
        sonidos.poner_volumenes(efectos=v)
        self.app.progreso.guardar()

    def poner_pantalla(self, v):
        self.app.poner_pantalla_completa(v)

    def atras(self):
        self.app.cambiar(self.previa, None)

    def evento(self, e):
        for c in self.controles:
            if c.evento(e):
                return True
        return super().evento(e)

    def actualizar(self, dt):
        self.t += dt

    def dibujar(self, sup):
        sup.blit(self.foto, (0, 0))
        k = rebote(min(1.0, self.t / 0.3))
        panel = self.panel.move(0, int((1 - k) * 60))
        ui.tarjeta(sup, panel, ui.PERGAMINO, 26, ui.ARENA_OSC, 8)
        letrero(sup, (panel.centerx - 160, panel.top - 26, 320, 64), "Opciones", 30)
        x, y = panel.left + 50, panel.top + 110
        filas = [("Música", y), ("Efectos de sonido", y + 120), ("Pantalla completa  (F11)", y + 240)]
        for txt, yy in filas:
            sup.blit(ui.texto(txt, 26, TINTA, negrita=True), (x, yy + 4))
        icono_m = pygame.Rect(x + 300, y + 2, 36, 36)
        ui.parlante(sup, (icono_m.centerx, icono_m.centery), 30, SUAVE, self.app.progreso.musica)
        sup.blit(ui.texto("La tecla M silencia todo de una.", 17, SUAVE), (x, y + 300))
        dy = int((1 - k) * 60)
        for c in self.controles:
            c.rect.move_ip(0, dy)
            c.dibujar(sup)
            c.rect.move_ip(0, -dy)
        self.dibujar_botones(sup)


# =============================================================== TIENDA DEL MICHI

class Tienda(Escena):
    def __init__(self, app):
        super().__init__(app)
        self.cielo = paisaje.Cielo(semilla=8, nubes=4)
        self.mar = paisaje.Mar(400)
        self.gato = Gato(250)
        self.gato.reaccionar("feliz", 1.2)
        self.fx = Efectos()
        self.lugar = "cabeza"
        self.sel = None
        self.t = 0.0
        self.mensaje = "¡Elegí algo para probarle!"
        self.armar()

    @property
    def prog(self):
        return self.app.progreso

    def atras(self):
        self.app.cambiar(Menu(self.app), "ola")

    def _puesta(self):
        return dict(self.prog.ropa_puesta)

    def _sincronizar(self):
        modulo_gato.ROPA = tuple(self.prog.ropa_puesta.values())

    def _probando(self):
        puesta = self._puesta()
        if self.sel:
            puesta[ropa.POR_ID[self.sel].lugar] = self.sel
        return tuple(puesta.values())

    def _tarjeta(self, p, w, h):
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        img = modulo_gato.superficie(84, "normal", ropa=(p.id,))
        s.blit(img, img.get_rect(midtop=(w // 2, -8)))
        nombre = ui.escalar_a(ui.texto(p.nombre, 15, TINTA, negrita=True), w - 8)
        s.blit(nombre, nombre.get_rect(midtop=(w // 2, h - 46)))
        if self.prog.ropa_puesta.get(p.lugar) == p.id:
            et = ui.texto("¡Puesto!", 16, MENTA_OSC, negrita=True)
            s.blit(et, et.get_rect(midtop=(w // 2, h - 24)))
        elif p.id in self.prog.ropa_comprada:
            et = ui.texto("Es tuyo", 16, ui.LAVANDA_OSC, negrita=True)
            s.blit(et, et.get_rect(midtop=(w // 2, h - 24)))
        else:
            et = ui.texto(str(p.precio), 17, ui.SOL_OSC if self.prog.monedas >= p.precio else SUAVE, negrita=True)
            ancho = et.get_width() + 24
            x = w // 2 - ancho // 2
            ui.moneda(s, (x + 8, h - 14), 9)
            s.blit(et, (x + 22, h - 24))
        return s

    def armar(self):
        self.botones = [Boton((24, 22, 128, 50), "Menú", self.atras, DURAZNO, tam=22),
                        self.boton_opciones((ANCHO - 76, 22, 56, 50))]
        x0 = 572
        for k, (clave, nombre) in enumerate(ropa.LUGARES):
            self.botones.append(Boton((x0 + k * 134, 112, 124, 46), nombre, (lambda c=clave: self.elegir_lugar(c)),
                                      SOL if clave == self.lugar else ARENA, tam=19, relieve=4, sonido="tecla"))
        items = [p for p in ropa.CATALOGO if p.lugar == self.lugar]
        w, h = 150, 150
        for k, p in enumerate(items):
            fila, col = divmod(k, 4)
            rect = (x0 + col * (w + 14), 182 + fila * (h + 16), w, h)
            puesto = self.prog.ropa_puesta.get(p.lugar) == p.id
            color = (226, 246, 210) if puesto else ((255, 236, 196) if p.id == self.sel else TARJETA)
            b = Boton(rect, self._tarjeta(p, w - 12, h - 12), (lambda pid=p.id: self.tocar(pid)), color,
                      radio=16, relieve=5, sonido="tecla")
            self.botones.append(b)
        # botón de acción debajo del gato
        if self.sel:
            p = ropa.POR_ID[self.sel]
            if p.id not in self.prog.ropa_comprada:
                alcanza = self.prog.monedas >= p.precio
                self.botones.append(Boton((90, 602, 380, 64), f"Comprar · {p.precio}", self.comprar, CORAL, CREMA,
                                          tam=26, habilitado=alcanza, sonido=None))
        if self.prog.ropa_puesta:
            self.botones.append(Boton((180, 676, 200, 38), "Sacarle todo", self.sacar_todo, ARENA, tam=16, relieve=4))

    def elegir_lugar(self, clave):
        self.lugar = clave
        self.armar()

    def tocar(self, pid):
        p = ropa.POR_ID[pid]
        if pid in self.prog.ropa_comprada:
            if self.prog.ropa_puesta.get(p.lugar) == pid:
                self.prog.poner(p.lugar, None)
                self.mensaje = f"Le sacaste: {p.nombre}"
                self.gato.reaccionar("sorpresa", 0.8, saltar=False)
            else:
                self.prog.poner(p.lugar, pid)
                self.mensaje = f"¡Le pusiste: {p.nombre}!"
                self.gato.reaccionar("feliz", 1.0)
                sonidos.tocar("estrella", 0.6)
            self.sel = None
            self._sincronizar()
        else:
            self.sel = pid
            faltan = p.precio - self.prog.monedas
            self.mensaje = (f"Probándose: {p.nombre}" if faltan <= 0
                            else f"Te faltan {faltan} monedas para: {p.nombre}")
            self.gato.reaccionar("sorpresa" if faltan > 0 else "feliz", 0.9, saltar=faltan <= 0)
        self.armar()

    def comprar(self):
        p = ropa.POR_ID[self.sel]
        if self.prog.comprar(p.id, p.precio):
            self.prog.poner(p.lugar, p.id)
            self._sincronizar()
            sonidos.tocar("desbloqueo")
            sonidos.tocar("miau")
            sonidos.agachar(1.2)
            self.fx.confeti(270, 420, 60, 1.2)
            self.fx.chispas(270, 460, 24, ui.SOL, 340)
            self.fx.texto(270, 330, f"−{p.precio}", ui.SOL, 40)
            self.gato.reaccionar("festejo", 2.0)
            self.mensaje = f"¡Compraste: {p.nombre}!"
            self.sel = None
        else:
            sonidos.tocar("mal")
        self.armar()

    def sacar_todo(self):
        for lugar in list(self.prog.ropa_puesta):
            self.prog.poner(lugar, None)
        self.sel = None
        self._sincronizar()
        self.mensaje = "¡Al natural!"
        self.armar()

    def actualizar(self, dt):
        self.t += dt
        self.cielo.actualizar(dt)
        self.mar.actualizar(dt)
        self.gato.actualizar(dt)
        self.fx.actualizar(dt)
        self.gato.ropa = self._probando() if self.sel else None

    def dibujar(self, sup):
        self.cielo.dibujar(sup, sol=False)
        self.mar.dibujar(sup)
        # playa
        pts = [(0, ALTO)] + [(x, 520 + 10 * math.sin(x / 70 + 1)) for x in range(0, 561, 20)] + [(560, ALTO)]
        pygame.draw.polygon(sup, ui.ARENA, pts)
        pygame.draw.lines(sup, ui.ESPUMA, False, pts[1:-1], 5)
        # alfombrita y gato
        pygame.draw.ellipse(sup, BORDE, (120, 528, 300, 70))
        pygame.draw.ellipse(sup, CORAL, (124, 528, 292, 62))
        pygame.draw.ellipse(sup, (255, 170, 150), (150, 538, 240, 42), 4)
        self.gato.dibujar(sup, (270, 566))
        letrero(sup, (ANCHO // 2 - 230, 16, 460, 64), "Tienda del michi", 30)
        dibujar_monedero(sup, self.prog.monedas, (ANCHO - 92, 22))
        # cartel con el mensaje, arriba del gato
        msg = ui.rico(self.mensaje, 20, TINTA, ancho=380, centrado=True)
        caja = pygame.Rect(0, 0, 420, msg.get_height() + 28)
        caja.midtop = (270, 100)
        ui.globo(sup, caja, (330, 200), TARJETA)
        sup.blit(msg, msg.get_rect(center=caja.center))
        # panel de prendas
        panel = pygame.Rect(552, 96, 708, 610)
        ui.tarjeta(sup, panel, ui.PERGAMINO, 24, ui.ARENA_OSC, 6)
        self.dibujar_botones(sup)
        self.fx.dibujar(sup)
